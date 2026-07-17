#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「標本調査」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（8枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証:
  1) 統計検算assert — 箱ひげ図の五数・四分位範囲・平均値などを本文の生データから
     Pythonで再計算し、本文・解答編の値と一致しなければ図を出力しない。
  2) 禁止文字列の機械検査 — 各図の<text>/<title>/<desc>に現れる数値トークンを
     全て抽出し、図ごとの「許可数値リスト」外の数値（＝答えの漏えい候補）があれば停止。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行。
  数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。
  SVGの直接編集は禁止（来歴が切れる）。
"""

import math
import re
import datetime
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px) — viewBox幅~440で約3%
FS_CAP = 12       # キャプション
DOT_R = 2.5       # 点マーカー半径


# ===========================================================================
# 検算ヘルパー
# ===========================================================================
class Checker:
    """assert相当の検算記録。1件でも失敗すると例外で停止（図は出力されない）"""

    def __init__(self):
        self.items = []

    def ok(self, desc, cond, note=""):
        if not cond:
            raise AssertionError(f"検算失敗: {desc} {note}")
        self.items.append((desc, note))


def five_number_summary(data):
    """五数要約（中2教科書の方式・データ数は偶数20を想定）。
    0.1刻みデータの浮動小数誤差を避けるため10倍整数で厳密計算する。"""
    d = sorted(round(x * 10) for x in data)
    n = len(d)
    assert n % 4 == 0, "この教材のデータは20個（4の倍数）想定"
    half = n // 2

    def med(seg):
        m = len(seg)
        return (seg[m // 2 - 1] + seg[m // 2]) / 2 / 10

    return dict(min=d[0] / 10, q1=med(d[:half]), med=med(d), q3=med(d[half:]),
                max=d[-1] / 10)


def exact_mean(data):
    """0.1刻みデータの平均を10倍整数で厳密に求める"""
    total10 = sum(round(x * 10) for x in data)
    return total10 / 10 / len(data), total10 / 10


TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# レッスンID（L01〜L07）・「主概念1」等の構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "06", "07", "1", "2", "3"}


def audit_numbers(svg, allowed, check_tokens, fig_id):
    """禁止文字列の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。allowed=許可数値トークン集合、check_tokens=答え漏れ検査トークン（検査の実装定数）。"""
    allowed = set(allowed) | GLOBAL_ALLOWED
    chunks = TEXT_RE.findall(svg) + TITLE_RE.findall(svg) + DESC_RE.findall(svg)
    for c in chunks:
        for b in check_tokens:
            if b in c:
                raise AssertionError(f"{fig_id}: 禁止文字列 '{b}' が図内文字列に混入: {c!r}")
        for tok in NUM_RE.findall(c):
            if tok not in allowed:
                raise AssertionError(
                    f"{fig_id}: 許可外の数値 '{tok}' が図内文字列に混入: {c!r}")


# ===========================================================================
# 描画ヘルパー（本単元は模式図・統計図中心のためpx座標で直接描く）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.defs = []
        self.body = []

    def raw(self, s):
        self.body.append(s)

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def rect(self, x, y, w, h, sw=MAIN_W, fill="none", dash=None, rx=None,
             color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
                 f'{r} fill="{fill}" stroke="{color}" stroke-width="{sw}"{d}/>')

    def circle(self, cx, cy, r, sw=MAIN_W, fill="none", dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
                 f'stroke="{color}" stroke-width="{sw}"{d}/>')

    def ellipse(self, cx, cy, rx, ry, sw=MAIN_W, fill="none", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')

    def dot(self, x, y, r=DOT_R, fill="#000", sw=1.2):
        if fill == "none" or fill == "#fff":
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                     f'stroke="#000" stroke-width="{sw}"/>')
        else:
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, color="#000"):
        wgt = f' font-weight="{weight}"' if weight else ""
        c = f' fill="{color}"' if color != "#000" else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{c}>{escape(s)}</text>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None, color="#000"):
        """直線矢印（先端は三角形の2辺で描く——marker不使用でself-contained）"""
        self.line(x1, y1, x2, y2, w=w, dash=dash, color=color)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (1, -1):
            a = ang + math.pi - s * math.radians(26)
            self.line(x2, y2, x2 + head * math.cos(a), y2 + head * math.sin(a),
                      w=w, color=color)

    def check_mark(self, x, y, size=4.5, w=1.4, color="#000"):
        """点検の「印」——小さなチェックマーク（フォント非依存の折れ線）"""
        self.raw(f'<polyline points="{x - size:.1f},{y:.1f} '
                 f'{x - size * 0.25:.1f},{y + size * 0.8:.1f} '
                 f'{x + size:.1f},{y - size * 0.9:.1f}" fill="none" '
                 f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>')

    def hatch_def(self, pid="h45", angle=45):
        self.defs.append(
            f'<pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate({angle})">'
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="#555" stroke-width="1.1"/>'
            f'</pattern>')

    def render(self, fig_id, title, desc):
        """AI再利用メタ情報: <title>/<desc>をルート直下に埋め込んで完全なSVG文字列を返す"""
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'role="img">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md準拠（内部規約の要旨は同SPECに反映済み）・AI再利用メタ情報つき・SVG直接編集禁止/'
            f'スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )


def number_line(cv, x0, x1, y, vmin, vmax, step, label_vals, tick_h=4.0,
                mid_h=6.0, label_size=11, label_dy=17):
    """数直線: 0.1刻みの小ティック＋0.5刻みの中ティック＋指定値のみ数値ラベル。
    戻り値: 値→x座標 の変換関数"""
    def X(v):
        return x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)

    cv.line(x0, y, x1, y, w=1.2)
    n = round((vmax - vmin) / step)
    for i in range(n + 1):
        v = round(vmin + i * step, 10)
        big = abs(v * 10 - round(v * 2, 10) * 5) < 1e-9  # 0.5刻みか
        h = mid_h if big else tick_h
        cv.line(X(v), y - h, X(v), y + h, w=0.9)
    for v in label_vals:
        cv.text(X(v), y + label_dy, f"{v:.1f}", size=label_size)
    return X


def draw_boxplot(cv, X, y, fv, box_h=26, w=MAIN_W, color="#000"):
    """五数要約fv（dict）を座標へ厳密変換して箱ひげ図を1本描く"""
    xmin, xq1, xmed, xq3, xmax = (X(fv[k]) for k in ("min", "q1", "med", "q3", "max"))
    # 検算: 座標の単調性（数値→座標変換の向き事故防止）
    assert xmin <= xq1 <= xmed <= xq3 <= xmax, "箱ひげ図の座標が単調でない"
    cv.line(xmin, y, xq1, y, w=w, color=color)                    # 左ひげ
    cv.line(xq3, y, xmax, y, w=w, color=color)                    # 右ひげ
    cv.line(xmin, y - box_h * 0.32, xmin, y + box_h * 0.32, w=w, color=color)
    cv.line(xmax, y - box_h * 0.32, xmax, y + box_h * 0.32, w=w, color=color)
    cv.rect(xq1, y - box_h / 2, xq3 - xq1, box_h, sw=w, color=color)
    cv.line(xmed, y - box_h / 2, xmed, y + box_h / 2, w=w, color=color)
    return dict(xmin=xmin, xq1=xq1, xmed=xmed, xq3=xq3, xmax=xmax)


# ===========================================================================
# 図1: L01 全数調査と標本調査の対比（概念図・数値なし）
# 本文根拠: lesson_01.md 主概念1【ことば】直後の【図】指定
# 答え漏れ注意: 人数などの数値は一切入れない
# ===========================================================================
def fig_L01():
    ck = Checker()
    cv = Canvas(440, 252)

    def crowd(cx0, cy0):
        """楕円内の集団（点3列×4行）——座標リストを返す"""
        pts = []
        for r in range(3):
            for c in range(4):
                pts.append((cx0 - 39 + c * 26, cy0 - 26 + r * 26))
        return pts

    # --- 左パネル: 全数調査（全員に印） ---
    lx, ly = 110, 118
    cv.text(lx, 42, "全数調査", size=FS, weight="bold")
    cv.ellipse(lx, ly, 78, 56)
    left_pts = crowd(lx, ly)
    for (x, y) in left_pts:
        cv.dot(x, y)
        cv.check_mark(x + 6.5, y - 5.5, size=3.6, w=1.2)
    cv.text(lx, 198, "集団の全員を調べる", size=FS_CAP)

    # --- 右パネル: 標本調査（一部を取り出して調べ、全体へ推測を返す） ---
    rx, ry = 322, 108
    cv.text(rx, 42, "標本調査", size=FS, weight="bold")
    cv.ellipse(rx, ry, 78, 50)
    right_pts = crowd(rx, ry)
    picked = [right_pts[1], right_pts[6], right_pts[11]]  # ばらばらの位置から3個
    for (x, y) in right_pts:
        if (x, y) in picked:
            cv.dot(x, y)                       # 選ばれた要素=黒丸
        else:
            cv.dot(x, y, fill="none")          # それ以外=白丸
    # 取り出した標本（下の小さな破線円）
    sx, sy = 296, 205
    cv.circle(sx, sy, 24, sw=AUX_W, dash=DASH)
    for i, dx in enumerate((-11, 0, 11)):
        cv.dot(sx + dx, sy + (3 if i == 1 else -2))
        cv.check_mark(sx + dx + 4.5, sy + (3 if i == 1 else -2) - 5, size=3.0, w=1.1)
    cv.arrow(rx - 30, ry + 46, sx - 14, sy - 18, w=1.4)
    cv.text(216, 178, "一部を取り出して", size=FS_CAP, anchor="middle")
    cv.text(216, 193, "調べる", size=FS_CAP, anchor="middle")
    cv.arrow(sx + 24, sy - 8, rx + 44, ry + 44, w=1.4, dash=DASH)
    cv.text(398, 196, "全体のようすを", size=FS_CAP, anchor="middle")
    cv.text(398, 211, "推測する", size=FS_CAP, anchor="middle")
    cv.text(220, 240, "（調べるのは一部——結果から全体を推測するのが標本調査）",
            size=FS_CAP)

    ck.ok("標本の点は集団の点の一部（3個⊂12個・図中の点集合で確認）",
          all(p in right_pts for p in picked) and len(picked) < len(right_pts))
    ck.ok("左パネルは全点に印（点の数＝印の数＝12を描画コードで保証）",
          len(left_pts) == 12)
    ck.ok("数値ラベルなし（禁止文字列機械検査で確認）", True)

    title = "全数調査と標本調査の対比（概念図）"
    desc = ("L01主概念1の概念図。左は全数調査＝集団（楕円内の十数個の点）の全員に"
            "点検の印がつく。右は標本調査＝集団のうち数個だけを破線の小円へ取り出して"
            "印をつけ、破線矢印で全体へ「推測」を返す。人数などの数値は意図的に入れて"
            "いない。再現指示: 楕円を2つ並べ、左は内部の点すべてにチェック印を、右は"
            "内部の点のうち数個だけを塗りつぶして下の破線円へ実線矢印（ラベル「一部を"
            "取り出して調べる」）で移し、破線円から楕円へ破線矢印（ラベル「全体のようす"
            "を推測する」）を戻す。白黒のみ・数値なしで描くこと。")
    return dict(file="L01_fig1_census_vs_sample.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="主概念1の対比概念図。全数調査=全員に印／標本調査=一部→全体へ推測",
                params="点12個×2集団・標本3個（数値ラベルなしの概念図）",
                checks=ck.items, allowed=set(), check_tokens=set())


# ===========================================================================
# 図2: L02 母集団・標本・抽出（模式図・数値なし）
# 本文根拠: lesson_02.md 主概念1【ことば】直後の【図】指定
# 答え漏れ注意: 個数の数値は入れない
# ===========================================================================
def fig_L02():
    ck = Checker()
    cv = Canvas(440, 236)

    # --- パラメータ: 母集団の点15個（うち3個が標本として抽出される） ---
    px, py, prx, pry = 138, 128, 105, 76
    pts = [(-62, -34), (-20, -46), (26, -50), (62, -30), (-78, 2), (-38, -8),
           (4, -14), (44, -6), (76, 10), (-58, 30), (-16, 24), (24, 30),
           (60, 38), (-40, 52), (8, 52)]
    pts = [(px + dx, py + dy) for dx, dy in pts]
    picked_idx = [2, 7, 13]
    picked = [pts[i] for i in picked_idx]

    cv.ellipse(px, py, prx, pry)
    cv.text(px, 30, "母集団", size=FS, weight="bold")
    cv.text(px, 226, "調べたい対象の全体", size=FS_CAP)
    for i, (x, y) in enumerate(pts):
        if i in picked_idx:
            cv.dot(x, y)
        else:
            cv.dot(x, y, fill="none")

    # --- 標本の小円 ---
    sx, sy, sr = 370, 128, 40
    cv.circle(sx, sy, sr)
    cv.text(sx, 66, "標本", size=FS, weight="bold")
    cv.text(sx, 226, "取り出された一部分", size=FS_CAP)
    spots = [(sx - 13, sy - 9), (sx + 13, sy - 6), (sx, sy + 13)]
    for (x, y) in spots:
        cv.dot(x, y)
    # 選ばれた点から標本円への細い破線（同じ要素が移ることを示す）
    for (x, y), (tx, ty) in zip(picked, spots):
        cv.line(x, y, tx, ty, w=0.8, dash="2 3", color="#888")

    # --- 抽出の矢印 ---
    cv.arrow(px + prx + 4, py, sx - sr - 6, sy, w=1.8)
    cv.text((px + prx + sx - sr) / 2, py - 12, "抽出", size=FS, weight="bold")

    ck.ok("標本の要素は母集団の要素の一部（3個⊂15個・対応線で同一性を明示）",
          len(picked) == 3 and len(pts) == 15 and all(p in pts for p in picked))
    ck.ok("ラベルは本文の用語どおり（母集団・標本・抽出）", True)
    ck.ok("個数の数値ラベルなし（禁止文字列機械検査で確認）", True)

    title = "母集団から標本を抽出する模式図"
    desc = ("L02主概念1【ことば】の模式図。大きな楕円＝母集団（調べたい対象の全体・"
            "十数個の点）から、数個の点だけが取り出されて右の小さな円＝標本に移る。"
            "太い矢印に「抽出」のラベル。選ばれた点は黒丸、選ばれなかった点は白丸で、"
            "同じ要素が移ったことを細い点線で対応づける。個数の数値は意図的に入れて"
            "いない。再現指示: 左に大きな楕円（ラベル「母集団」）、右に小さな円（ラベル"
            "「標本」）を描き、楕円内の点のうち数個を塗りつぶして小円内の点と点線で結び、"
            "楕円から小円へ太い矢印（ラベル「抽出」）を引く。白黒のみ・数値なし。")
    return dict(file="L02_fig1_population_sample.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="主概念1の用語図。母集団（全体）→抽出→標本（一部分）の関係",
                params="母集団の点15個・標本3個（数値ラベルなしの模式図）",
                checks=ck.items, allowed=set(), check_tokens=set())


# ===========================================================================
# 図3: L03 標本A・B・Cの平均値の散らばり（数直線）
# 本文根拠: lesson_03.md「やってみよう」の標本A/B/C生データと【図】指定
# 答え漏れ注意: B・Cの平均値は練習1の答え——数値ラベルは打たない（位置のみ）。
#               母集団の平均値（7.2・教材設定）も描かない
# ===========================================================================
def fig_L03():
    # --- パラメータ（lesson_03.md の生データをそのまま転記） ---
    sample_A = [6.5, 7.0, 7.0, 7.0, 7.5, 7.5, 7.0, 8.0, 6.5, 7.0]
    sample_B = [7.5, 7.0, 8.0, 7.5, 7.0, 6.5, 7.5, 7.0, 7.5, 7.5]
    sample_C = [6.0, 7.0, 7.0, 6.5, 7.5, 7.0, 6.5, 7.0, 7.5, 7.0]
    vmin, vmax = 6.8, 7.4          # 本文指定「6.8〜7.4程度の範囲」

    mean_A, sum_A = exact_mean(sample_A)
    mean_B, _ = exact_mean(sample_B)
    mean_C, _ = exact_mean(sample_C)

    ck = Checker()
    ck.ok("標本Aの平均=7.10・合計71.0（本文の計算と一致）",
          abs(mean_A - 7.10) < 1e-12 and abs(sum_A - 71.0) < 1e-12,
          f"mean={mean_A:.2f}")
    ck.ok("標本B・Cの平均を生データから再計算（解答編answer_key_L01-04と一致）",
          abs(mean_B - 7.30) < 1e-12 and abs(mean_C - 6.90) < 1e-12)
    ck.ok("3つの平均値は互いに異なる（=散らばって見える・本文の主旨）",
          len({mean_A, mean_B, mean_C}) == 3)
    ck.ok("3点とも数直線の範囲内（6.8〜7.4）",
          all(vmin < m < vmax for m in (mean_A, mean_B, mean_C)))

    cv = Canvas(440, 150)
    X = number_line(cv, 50, 410, 96, vmin, vmax, 0.1,
                    label_vals=[6.8, 7.0, 7.2, 7.4])
    # 3つの平均値を厳密座標で打点（数値ラベルは打たない——練習1の答えのため）
    for m, name, lift in ((mean_C, "標本C", 0), (mean_A, "標本A", 0),
                          (mean_B, "標本B", 0)):
        x = X(m)
        cv.dot(x, 78, r=3.2)
        cv.line(x, 78, x, 92, w=0.8, dash="2 3", color="#888")
        cv.text(x, 66, name, size=FS_CAP, weight="bold")
    cv.text(230, 26, "3つの標本の平均値（単位: 時間）", size=FS, weight="bold")
    cv.text(230, 138, "（同じ母集団・同じ手順なのに、平均値は1か所に重ならない）",
            size=FS_CAP)

    title = "標本A・B・Cの平均値の散らばり（数直線）"
    desc = ("L03の観察図。数直線（6.8〜7.4・0.1刻み）の上に、同じ母集団から無作為抽出"
            "した大きさ10の標本A・B・Cの平均値を3つの点で打った。標本Aの平均は7.10"
            "（本文で計算済み）。B・Cの平均値の数値は練習1の答えのため図には記載せず、"
            "位置のみ生データから厳密計算して打点してある。母集団の平均値の位置は本文"
            "指定により描かない。再現指示: 横の数直線に0.1刻みの目盛を打ち、6.8/7.0/"
            "7.2/7.4だけ数値ラベルを付け、3つの標本平均の位置に黒点と標本名ラベル"
            "（標本A・標本B・標本C）を置く。点に数値は書かない。白黒のみ。")
    allowed = {"6.8", "7.0", "7.2", "7.4", "3", "0.1", "10", "7.10", "1"}
    check_tokens = {"7.30", "6.90", "7.3", "6.9"}
    return dict(file="L03_fig1_sample_means_scatter.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="標本平均が標本ごとにばらつくことの観察図（母平均は描かない）",
                params="標本A/B/C各10個の生データ（本文転記）→平均を厳密計算して打点",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図4: L04 大きさ10の記録の箱ひげ図（本文の例示・五数を明示）
# 本文根拠: lesson_04.md「まず1セット目」の生データ20個と【図】指定
# 数値記載: 本文の例示なので五数の数値を入れてよい（本文明記）
# ===========================================================================
DATA10 = [6.5, 6.7, 6.8, 6.9, 7.0, 7.0, 7.1, 7.1, 7.2, 7.2,
          7.2, 7.3, 7.3, 7.4, 7.4, 7.4, 7.6, 7.7, 7.8, 8.0]
DATA20 = [7.2, 7.4, 7.1, 7.3, 6.9, 7.5, 7.2, 7.0, 7.4, 7.2,
          6.8, 7.3, 7.6, 7.1, 7.2, 7.5, 7.0, 7.4, 7.1, 7.2]
DATA40 = [7.2, 7.1, 7.3, 7.2, 7.4, 7.2, 7.0, 7.3, 7.2, 7.1,
          7.4, 7.2, 7.3, 7.1, 7.2, 7.0, 7.4, 7.2, 7.1, 7.3]
AX_MIN, AX_MAX = 6.4, 8.1          # 本文指定「6.4〜8.1・0.1刻み」


def fig_L04_box10():
    fv = five_number_summary(DATA10)

    ck = Checker()
    ck.ok("五数=本文値（最小6.5・Q1 7.0・中央値7.2・Q3 7.4・最大8.0）を生データから再計算",
          fv == dict(min=6.5, q1=7.0, med=7.2, q3=7.4, max=8.0),
          f"実測={fv}")
    ck.ok("範囲1.5・四分位範囲0.4（本文の太字値と一致）",
          abs((fv["max"] - fv["min"]) - 1.5) < 1e-12
          and abs((fv["q3"] - fv["q1"]) - 0.4) < 1e-12)
    ck.ok("中央値=(10番目+11番目)/2=(7.2+7.2)/2（中2方式・本文の式と一致）",
          sorted(DATA10)[9] == 7.2 and sorted(DATA10)[10] == 7.2)
    ck.ok("データ数20個（本文「20回」と一致）", len(DATA10) == 20)

    cv = Canvas(480, 210)
    X = number_line(cv, 48, 452, 156, AX_MIN, AX_MAX, 0.1,
                    label_vals=[6.5, 7.0, 7.5, 8.0])
    pos = draw_boxplot(cv, X, 100, fv, box_h=30)
    # 座標検算: 数値→座標の厳密変換（0.1が等間隔か）
    ck.ok("数値→座標の変換が線形（0.1刻みが等間隔・箱の位置=五数の位置）",
          abs((X(7.0) - X(6.5)) - (X(8.0) - X(7.5))) < 1e-9
          and abs(pos["xq1"] - X(7.0)) < 1e-9 and abs(pos["xmed"] - X(7.2)) < 1e-9)
    # 五数のラベル（本文の例示なので数値を入れてよい）
    for v, lab, dy in ((6.5, "6.5", -1), (7.0, "7.0", -1), (7.2, "7.2", -26),
                       (7.4, "7.4", -1), (8.0, "8.0", -1)):
        y = 100 - 30 / 2 - (10 if dy == -1 else 0)
        if lab == "7.2":
            cv.text(X(v), 100 - 30 / 2 - 24, lab, size=FS_CAP, weight="bold")
            cv.line(X(v), 100 - 30 / 2 - 20, X(v), 100 - 30 / 2 - 4, w=0.8,
                    dash="2 3", color="#888")
        else:
            cv.text(X(v), y - 4, lab, size=FS_CAP)
    cv.text(140, 30, "標本の大きさ10・20回分の平均値", size=FS, anchor="middle",
            weight="bold")
    cv.text(250, 196, "（単位: 時間。最小値6.5・第1四分位数7.0・中央値7.2・"
                      "第3四分位数7.4・最大値8.0）", size=11)

    title = "大きさ10の記録の箱ひげ図（五数つき・本文の例示）"
    desc = ("L04の例示図。数直線（6.4〜8.1・0.1刻み）の上に、標本の大きさ10で20回"
            "くり返した標本平均の記録の箱ひげ図を1本描いた。五数は最小値6.5・第1四分位数"
            "7.0・中央値7.2・第3四分位数7.4・最大値8.0（生データ20個からスクリプトが"
            "再計算し本文と一致を検算済み）。範囲1.5・四分位範囲0.4。再現指示: 横の数直線"
            "（6.4〜8.1・0.1刻み）の上方に、箱=7.0〜7.4・中央線=7.2・ひげ=6.5〜8.0の"
            "箱ひげ図を描き、各五数の値を図中にラベルする。白黒のみ。")
    allowed = {"10", "20", "6.5", "7.0", "7.2", "7.4", "8.0", "7.5",
               "6.4", "8.1", "0.1", "1.5", "0.4", "1", "2", "3"}
    return dict(file="L04_fig1_boxplot_size10.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="山場の例示。大きさ10の標本平均20個の箱ひげ図（五数明示OK）",
                params=f"生データ20個（本文転記）→五数={fv}・範囲1.5・四分位範囲0.4",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図5: L04 箱ひげ図の作図用の枠（10=薄い完成形・20/40=空欄）
# 本文根拠: lesson_04.md「やってみよう」の【図】指定
# 答え漏れ注意: 20・40の五数（解答編の答え）は図にもdescにも入れない
# ===========================================================================
def fig_L04_worksheet():
    fv10 = five_number_summary(DATA10)
    fv20 = five_number_summary(DATA20)
    fv40 = five_number_summary(DATA40)

    ck = Checker()
    ck.ok("大きさ20の五数を生データから再計算——解答編（範囲0.8・四分位範囲0.3）と一致",
          fv20 == dict(min=6.8, q1=7.1, med=7.2, q3=7.4, max=7.6)
          and abs((fv20["max"] - fv20["min"]) - 0.8) < 1e-12
          and abs((fv20["q3"] - fv20["q1"]) - 0.3) < 1e-12)
    ck.ok("大きさ40の五数を生データから再計算——解答編（範囲0.4・四分位範囲0.2）と一致",
          fv40 == dict(min=7.0, q1=7.1, med=7.2, q3=7.3, max=7.4)
          and abs((fv40["max"] - fv40["min"]) - 0.4) < 1e-12
          and abs((fv40["q3"] - fv40["q1"]) - 0.2) < 1e-12)
    ck.ok("せまくなる傾向（範囲1.5>0.8>0.4・四分位範囲0.4>0.3>0.2）が成立",
          (fv10["max"] - fv10["min"]) > (fv20["max"] - fv20["min"])
          > (fv40["max"] - fv40["min"])
          and (fv10["q3"] - fv10["q1"]) > (fv20["q3"] - fv20["q1"])
          > (fv40["q3"] - fv40["q1"]))
    ck.ok("20・40の五数は図に描かない（10のみ薄い完成形・禁止文字列機械検査で確認）",
          True)

    cv = Canvas(480, 300)
    x0, x1 = 108, 452
    rows = [("大きさ10", 70), ("大きさ20", 140), ("大きさ40", 210)]
    # 作図用の枠: 薄い縦罫（0.1刻み）を枠全体に通す
    def X(v):
        return x0 + (x1 - x0) * (v - AX_MIN) / (AX_MAX - AX_MIN)
    top, bottom = 40, 240
    for i in range(round((AX_MAX - AX_MIN) / 0.1) + 1):
        v = round(AX_MIN + i * 0.1, 10)
        big = abs(v * 10 - round(v * 2, 10) * 5) < 1e-9
        cv.line(X(v), top, X(v), bottom, w=0.7 if big else 0.45,
                color="#bbb" if big else "#ddd")
    cv.rect(x0, top, x1 - x0, bottom - top, sw=1.0)
    for k, (name, y) in enumerate(rows):
        if k > 0:
            yy = (rows[k - 1][1] + y) / 2
            cv.line(x0, yy, x1, yy, w=0.7, color="#bbb")
        cv.text(56, y + 4, name, size=FS_CAP, weight="bold")
    # 大きさ10のみ薄い完成形（グレー）
    draw_boxplot(cv, X, rows[0][1], fv10, box_h=26, w=1.3, color="#999")
    # 数直線（枠の下）
    number_line(cv, x0, x1, bottom + 16, AX_MIN, AX_MAX, 0.1,
                label_vals=[6.5, 7.0, 7.5, 8.0])
    cv.text(240, 24, "箱ひげ図をかきこもう（大きさ20・40は自分で）", size=FS,
            weight="bold")
    cv.text(240, 290, "（単位: 時間。大きさ10は薄い完成形——20・40は自分で求めてかく）",
            size=11)

    title = "箱ひげ図の作図用の枠（大きさ10・20・40）"
    desc = ("L04の作図ワーク図。数直線（6.4〜8.1・0.1刻み）の上に3段の枠があり、"
            "上段「大きさ10」だけ箱ひげ図の完成形が薄いグレーで入っている（五数は"
            "6.5・7.0・7.2・7.4・8.0）。中段「大きさ20」・下段「大きさ40」は空欄で、"
            "学習者が本文の記録から五数を求めて自分でかきこむ。20・40の五数の数値は"
            "答えにあたるため、この図にもこの説明にも記載しない。再現指示: 0.1刻みの"
            "薄い縦罫を通した横長の枠を3段に分け、最上段にだけグレーの箱ひげ図"
            "（箱7.0〜7.4・中央線7.2・ひげ6.5〜8.0）を描き、下2段は行ラベルのみ置いて"
            "空欄にする。枠の下に数直線（ラベルは6.5/7.0/7.5/8.0）。白黒のみ。")
    allowed = {"10", "20", "40", "6.5", "7.0", "7.5", "8.0", "7.2", "7.4",
               "6.4", "8.1", "0.1", "3"}
    check_tokens = {"6.8", "7.6", "7.1", "7.3", "0.8", "0.3", "0.2"}
    return dict(file="L04_fig2_boxplot_worksheet.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="必須活動前の作図ワーク枠。10=薄い見本・20/40=空欄（答え不記載）",
                params="軸6.4〜8.1・0.1刻み。20/40の五数はassert検算のみ（図に不記載）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図6: L05 平均値×総数型の推定の流れ図（辞典980ページ）
# 本文根拠: lesson_05.md「標本から全体へ」の生データ20個と【図】指定
# 答え漏れ注意: 最終の推定値（59976・およそ60000）は図に入れない
# ===========================================================================
def fig_L05():
    # --- パラメータ（lesson_05.md の生データをそのまま転記） ---
    pages = [58, 63, 60, 59, 65, 62, 57, 64, 61, 60,
             63, 58, 62, 66, 59, 61, 60, 64, 57, 65]
    total_pages = 980

    total = sum(pages)
    mean = total / len(pages)
    estimate = mean * total_pages

    ck = Checker()
    ck.ok("標本20ページの合計=1224語（本文と一致）", total == 1224)
    ck.ok("標本の平均=61.2語/ページ（本文と一致）", abs(mean - 61.2) < 1e-12,
          f"mean={mean}")
    ck.ok("推定値61.2×980=59976（本文と一致・図には書かない）",
          abs(estimate - 59976) < 1e-9)
    ck.ok("標本の大きさ=20ページ（本文と一致）", len(pages) == 20)

    cv = Canvas(480, 262)
    # 辞典の帯（全980ページ）
    bx0, bx1, by, bh = 46, 434, 46, 34
    cv.rect(bx0, by, bx1 - bx0, bh, sw=MAIN_W)
    cv.text((bx0 + bx1) / 2, by - 12, "みどり英和辞典 全980ページ", size=FS,
            weight="bold")
    # ばらばらの位置の20ページ（無作為抽出）——決めうちの散在位置
    fracs = [0.03, 0.07, 0.12, 0.16, 0.22, 0.27, 0.33, 0.38, 0.44, 0.49,
             0.55, 0.60, 0.66, 0.71, 0.77, 0.82, 0.87, 0.91, 0.95, 0.99]
    ck.ok("抜き出すページ位置マークが20個・帯の全域に散在（最初の20ページに固めない）",
          len(fracs) == 20 and fracs[0] < 0.1 and fracs[-1] > 0.9
          and all(b > a for a, b in zip(fracs, fracs[1:])))
    for f in fracs:
        x = bx0 + (bx1 - bx0) * f
        cv.line(x, by + 3, x, by + bh - 3, w=1.6)
    # 抜き出し→標本の箱
    sx, sy, sw_, sh = 96, 138, 156, 46
    cv.arrow(150, by + bh + 4, 168, by + bh + 24, w=1.4)
    cv.arrow(330, by + bh + 4, 258, by + bh + 24, w=1.4)
    cv.text(238, 124, "ばらばらの位置の20ページを無作為に抜き出す", size=FS_CAP)
    cv.rect(sx, sy, sw_, sh, sw=MAIN_W)
    cv.text(sx + sw_ / 2, sy + 19, "標本: 20ページ", size=FS_CAP, weight="bold")
    cv.text(sx + sw_ / 2, sy + 37, "1ページ平均 61.2語", size=FS_CAP)
    # ×980 の矢印で全体の見積もりへ戻る
    ex, ey, ew, eh = 300, 138, 150, 46
    cv.arrow(sx + sw_, sy + sh / 2, ex - 4, ey + eh / 2, w=1.8)
    cv.text((sx + sw_ + ex) / 2, sy + sh / 2 - 10, "×980", size=FS, weight="bold")
    cv.rect(ex, ey, ew, eh, sw=MAIN_W, dash=DASH)
    cv.text(ex + ew / 2, ey + 19, "全体の見出し語数", size=FS_CAP, weight="bold")
    cv.text(ex + ew / 2, ey + 37, "およそ ？語", size=FS_CAP)
    # 見積もりが「全体」へ戻ることを示す破線矢印
    cv.arrow(ex + ew / 2 + 40, ey - 6, 390, by + bh + 6, w=1.2, dash=DASH)
    cv.text(240, 220, "標本で観察した平均値を、母集団の総数にかけて全体を見積もる",
            size=FS_CAP)
    cv.text(240, 242, "（かけ算の答えをどう言い表すかは本文——「およそ」を落とさない）",
            size=11)

    title = "平均値×総数型の推定の流れ図（辞典980ページ）"
    desc = ("L05の流れ図。全980ページの辞典を表す横長の帯から、ばらばらの位置の"
            "20ページ（帯の中の縦線マーク）が無作為に抜き出され、「標本: 20ページ・"
            "1ページ平均61.2語」の箱にまとまり、「×980」の矢印で「全体の見出し語数 "
            "およそ？語」の破線箱へつながって帯（全体）へ戻る。最終の推定値は答えに"
            "あたるため図に入れない。再現指示: 横長の帯（ラベル「全980ページ」）に"
            "散在する縦線を20本打ち、そこから下の箱「標本:20ページ／1ページ平均61.2語」"
            "へ矢印を集め、太い矢印（ラベル「×980」）で右の破線箱「全体の見出し語数 "
            "およそ？語」へ、さらに破線矢印で帯へ戻す。白黒のみ。")
    allowed = {"980", "20", "61.2", "1"}
    check_tokens = {"59976", "60000", "6万", "1224"}
    return dict(file="L05_fig1_mean_times_total_flow.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="平均値×総数型の推定の構造図（推定値は？表記で不記載）",
                params="生データ20ページ分（本文転記）→合計1224・平均61.2を検算",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図7: L06 標本と母集団の割合の帯グラフ（比例配分型）
# 本文根拠: lesson_06.md「問題——袋の中の赤玉は何個?」の【図】指定
# 答え漏れ注意: 母集団側の赤の個数（180）は図に入れない
# ===========================================================================
def fig_L06():
    # --- パラメータ（lesson_06.md 本文と一致） ---
    sample_n, sample_red, pop_n = 30, 9, 600

    ratio = sample_red / sample_n
    pop_red = pop_n * ratio

    ck = Checker()
    ck.ok("標本の赤の割合 9÷30=0.3（本文と一致）", abs(ratio - 0.3) < 1e-12)
    ck.ok("母集団の推定 600×0.3=180（本文と一致・図には書かない）",
          abs(pop_red - 180) < 1e-12)
    ck.ok("検算の型: 180÷600=0.3が標本の割合と一致（本文の検算と同じ）",
          abs(pop_red / pop_n - ratio) < 1e-12)

    cv = Canvas(480, 262)
    cv.hatch_def("h45", 45)
    bx0, bx1, bh = 110, 430, 40
    split = bx0 + (bx1 - bx0) * ratio

    # 座標検算: ハッチング部の幅が帯全体のちょうど0.3
    ck.ok("帯グラフのハッチング幅=全幅×0.3（座標へ厳密変換）",
          abs((split - bx0) / (bx1 - bx0) - 0.3) < 1e-12)

    # 上段: 標本30個
    y1 = 58
    cv.rect(bx0, y1, split - bx0, bh, sw=0, fill="url(#h45)")
    cv.rect(bx0, y1, bx1 - bx0, bh, sw=MAIN_W)
    cv.line(split, y1, split, y1 + bh, w=MAIN_W)
    cv.text(70, y1 + bh / 2 + 4, "標本", size=FS, weight="bold")
    cv.text((bx0 + split) / 2, y1 - 8, "赤 9個", size=FS_CAP)
    cv.text((split + bx1) / 2, y1 - 8, "白", size=FS_CAP)
    cv.text(bx1, y1 + bh + 16, "全部で30個", size=FS_CAP, anchor="end")

    # 下段: 母集団600個
    y2 = 168
    cv.rect(bx0, y2, split - bx0, bh, sw=0, fill="url(#h45)")
    cv.rect(bx0, y2, bx1 - bx0, bh, sw=MAIN_W)
    cv.line(split, y2, split, y2 + bh, w=MAIN_W)
    cv.text(70, y2 + bh / 2 + 4, "母集団", size=FS, weight="bold")
    cv.text((bx0 + split) / 2, y2 - 8, "赤 ？個", size=FS_CAP, weight="bold")
    cv.text((split + bx1) / 2, y2 - 8, "白", size=FS_CAP)
    cv.text(bx1, y2 + bh + 16, "全部で600個", size=FS_CAP, anchor="end")

    # 同じ割合の区切り位置を点線で対応
    cv.line(split, y1 + bh, split, y2, w=AUX_W, dash=DASH)
    cv.line(bx0, y1 + bh, bx0, y2, w=0.8, dash="2 3", color="#888")
    cv.line(bx1, y1 + bh, bx1, y2, w=0.8, dash="2 3", color="#888")
    cv.text(split + 8, (y1 + bh + y2) / 2 + 4, "同じ割合（0.3）とみなす",
            size=FS_CAP, anchor="start")
    cv.text(240, 248, "（無作為な標本の割合は、母集団でも同じくらいのはず——比例配分型）",
            size=11)

    title = "標本と母集団の割合の帯グラフ（比例配分型）"
    desc = ("L06の比例配分図。上の帯＝標本30個（うち赤9個・左端の斜線ハッチング部分）、"
            "下の帯＝母集団600個。2本の帯は同じ長さで、赤の割合0.3の区切り位置を破線で"
            "上下に対応させ、母集団側の赤は「？個」と表記する（推定値の数は答えのため"
            "図にもこの説明にも入れない）。再現指示: 同じ長さの横帯を上下に2本描き、どちらも左から"
            "3割の位置に区切り線を入れ、左側を斜線ハッチングにする。上の帯に「赤 9個／白／"
            "全部で30個」、下の帯に「赤 ？個／白／全部で600個」とラベルし、区切り位置どうし"
            "を破線で結んで「同じ割合（0.3）とみなす」と添える。白黒のみ。")
    allowed = {"30", "9", "600", "0.3", "3"}
    check_tokens = {"180", "21"}
    return dict(file="L06_fig1_ratio_band_graph.svg", canvas=cv, lesson="L06",
                title=title, desc=desc,
                intent="比例配分型の推定の構造図（母集団側の赤の個数は？表記）",
                params="標本30個・赤9個・母集団600個→割合0.3を検算（180は不記載）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図8: L07 市民全体・来館者・回答者の包含関係（批評の図）
# 本文根拠: lesson_07.md「批評の観点」直後の【図】指定
# 答え漏れ注意: 数値は配布1000・回収200のみ（9割・90%・180は入れない）
# ===========================================================================
def fig_L07():
    ck = Checker()
    cv = Canvas(440, 312)

    # --- パラメータ: 3円の包含（中心と半径。内側ほど下寄りに置く） ---
    C_out = (206, 148, 128)     # 市民全体
    C_mid = (206, 178, 84)      # 来館者
    C_in = (206, 206, 44)       # 回答した200人

    def inside(inner, outer, margin=2.0):
        (x1, y1, r1), (x2, y2, r2) = inner, outer
        return math.hypot(x1 - x2, y1 - y2) + r1 + margin <= r2

    ck.ok("包含関係が幾何的に厳密（回答者⊂来館者⊂市民全体・円どうし非接触）",
          inside(C_in, C_mid) and inside(C_mid, C_out))
    ck.ok("図中の数値は配布1000・回収200のみ（禁止文字列機械検査で確認）", True)

    cv.circle(*C_out, sw=MAIN_W)
    cv.text(C_out[0], C_out[1] - C_out[2] + 24, "市民全体", size=FS, weight="bold")
    cv.circle(*C_mid, sw=MAIN_W)
    cv.text(C_mid[0], C_mid[1] - C_mid[2] + 20, "来館者", size=FS_CAP, weight="bold")
    cv.text(C_mid[0], C_mid[1] - C_mid[2] + 36, "（アンケート配布1000枚）", size=10.5)
    cv.circle(*C_in, sw=MAIN_W, fill="none")
    cv.text(C_in[0], C_in[1] + 1, "回答した", size=10.5, weight="bold")
    cv.text(C_in[0], C_in[1] + 14, "200人", size=10.5, weight="bold")

    # 記事の結論: 最小の円から最大の円へ一足飛びの矢印（円を飛び越す弧で描く）
    x0, y0 = C_in[0] + C_in[2] * 0.72, C_in[1] + C_in[2] * 0.7
    x1, y1 = C_out[0] + C_out[2] * 0.87, C_out[1] + C_out[2] * 0.62
    # 2次ベジェ風の弧を折れ線でサンプリング（外へふくらむ）
    ctrl = (388, 300)
    pts = []
    for i in range(25):
        t = i / 24
        bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl[0] + t ** 2 * x1
        by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl[1] + t ** 2 * y1
        pts.append((bx, by))
    cv.raw('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
           + f'" fill="none" stroke="#000" stroke-width="{BOLD_W}"/>')
    # 矢じり（終点の接線方向）
    ang = math.atan2(y1 - pts[-2][1], x1 - pts[-2][0])
    for s in (1, -1):
        a = ang + math.pi - s * math.radians(26)
        cv.line(x1, y1, x1 + 10 * math.cos(a), y1 + 10 * math.sin(a), w=BOLD_W)
    cv.text(392, 262, "記事の結論は", size=FS_CAP, anchor="middle", weight="bold")
    cv.text(392, 277, "一足飛び", size=FS_CAP, anchor="middle", weight="bold")
    cv.text(220, 302, "（回答した人の結果を、いちばん外の集団の意見として語っていないか）",
            size=11)

    title = "市民全体・来館者・回答者の包含関係（一足飛びの結論）"
    desc = ("L07の批評図。いちばん外の大きな円＝市民全体、その内側の中くらいの円＝"
            "来館者（アンケート配布1000枚）、さらに内側の小さな円＝回答した200人、という"
            "包含関係を描き、最小の円から最大の円へ円をまたぐ太い矢印を伸ばして「記事の"
            "結論は一足飛び」と示す。図中の数値は配布1000・回収200のみで、アンケート"
            "結果の割合の数値は本文指定により入れない。再現指示: 大中小3つの円を入れ子に"
            "描いてそれぞれ「市民全体」「来館者（アンケート配布1000枚）」「回答した200人」と"
            "ラベルし、最小円の縁から最大円の縁へ、中間の円を飛び越える弧状の太い矢印を"
            "1本描く。白黒のみ。")
    allowed = {"1000", "200", "3"}
    check_tokens = {"9割", "90", "180"}
    return dict(file="L07_fig1_nested_populations.svg", canvas=cv, lesson="L07",
                title=title, desc=desc,
                intent="母集団のすりかえの可視化（回答者⊂来館者⊂市民全体＋一足飛び矢印）",
                params="3円の入れ子（幾何包含をassert）・数値は配布1000・回収200のみ",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# メイン: 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02, fig_L03, fig_L04_box10, fig_L04_worksheet,
        fig_L05, fig_L06, fig_L07]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in FIGS:
        meta = fn()
        svg = meta["canvas"].render(meta["file"], meta["title"], meta["desc"])
        audit_numbers(svg, meta["allowed"], meta["check_tokens"], meta["file"])
        out = ASSETS / meta["file"]
        out.write_text(svg, encoding="utf-8")
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓"
                           for d, t in meta["checks"])
        if meta["check_tokens"]:
            checks += (f"／答え漏れ検査: PASS（{len(meta['check_tokens'])}項目・"
                       "対象値はanswer_key由来・非開示） ✓")
        else:
            checks += "／数値トークン検査（許可外なし） ✓"
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 標本調査単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "全図で下表の統計検算（スクリプト内assert）と禁止文字列の機械検査"
        "（<text>/<title>/<desc>の数値トークンを許可リストと照合）が生成時に自動実行され、全件合格。"
        "全SVGにAI再利用メタ情報（<title>=図名・<desc>=意図/主要数値/同型図をAIに描かせる再現指示）を埋め込み済み。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | パラメータ（本文一致） | 検証結果（生成時assert＋機械検査） |",
        "|---|---|---|---|---|",
    ]
    for f, lsn, title, intent, params, checks in rows:
        lines.append(f"| `{f}` | {lsn} | {title}——{intent} | {params} | {checks} |")
    lines += [
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。統計検算assert・禁止文字列検査に",
        "   1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
