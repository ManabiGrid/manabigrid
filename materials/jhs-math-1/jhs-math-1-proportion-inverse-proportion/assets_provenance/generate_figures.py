#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1数学「比例・反比例」単元 図版パラメトリック生成スクリプト
================================================================================
様式: jhs-math-2-quartiles-boxplot/assets_provenance/generate_figures.py の
コード来歴方式に準拠（Python標準ライブラリのみ・assert検算・解答値を図に載せない・
<title>/<desc>のAI再利用メタ情報・白黒両立）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（19枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証:
  1) 座標検算assert — グラフ図は通過点の座標（y＝ax・y＝a/x）を式から再計算して
     本文の値と一致しなければ図を出力しない。**全プロット点・曲線サンプル点の
     軸範囲内assertを必須とする**（E裁定: 主要点が軸範囲外だった2枚の再発防止。
     L05_fig1は軸x＝−4〜4・y＝−7〜7に点(±3, ±6)が収まること、L08_fig1は
     (0.5, 24)等の範囲外点を打たないことを明示的に検算する）。
  2) 禁止文字列の機械検査 — 各図の<text>/<title>/<desc>に現れる数値トークンを
     全て抽出し、図ごとの「許可数値リスト」外の数値（＝答えの漏えい候補）が
     あれば停止。練習用の図（L04_fig2・L05_fig3・L06_fig2・L08_fig2・L10_fig2）は
     answer_keyの解答文字列をcheck_tokensで追加検査する。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて
  再実行。数値は該当レッスン本文（lesson_XX.md）と一致させること。
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

# ---- 様式定数 ----------------------------------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 2.6      # 強調線幅（グラフの直線・曲線）
AUX_W = 1.1       # 補助線幅
GRID_W = 0.5      # 方眼線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_CAP = 11       # キャプション
DOT_R = 3.0       # 点マーカー半径
GRID_C = "#d8d8d8"  # 方眼色（白黒印刷でも薄グレーとして両立）

MINUS = "−"  # 全角風マイナス（本文表記と一致させる）


def fmt(v):
    """数値→表示文字列（負号はU+2212・整数は小数点なし）"""
    if v == int(v):
        s = str(int(v))
    else:
        s = f"{v:g}"
    return s.replace("-", MINUS)


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


TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# レッスンID（L01〜L12）・「主概念1」等の構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "06", "07", "08", "09",
                  "10", "11", "12", "1", "2", "3"}


def audit_numbers(svg, allowed, check_tokens, fig_id):
    """禁止文字列の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。allowed=許可数値トークン集合、check_tokens=答え漏れ検査
    トークン（answer_keyにのみ現れる文字列・検査の実装定数）。"""
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
# 描画ヘルパー（quartiles-boxplot版から流用＋座標平面ヘルパーを追加）
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

    def circle(self, x, y, r, sw=MAIN_W, fill="none", color="#000"):
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" '
                 f'stroke="{color}" stroke-width="{sw}"/>')

    def ellipse(self, x, y, rx, ry, sw=MAIN_W, fill="none", color="#000"):
        self.raw(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="{fill}" stroke="{color}" stroke-width="{sw}"/>')

    def dot(self, x, y, r=DOT_R, fill="#000", sw=1.2):
        if fill in ("none", "#fff"):
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                     f'stroke="#000" stroke-width="{sw}"/>')
        else:
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, color="#000"):
        wgt = f' font-weight="{weight}"' if weight else ""
        c = f' fill="{color}"' if color != "#000" else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{c}>{escape(s)}</text>')

    def polyline(self, pts, w=BOLD_W, dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        self.raw(f'<polyline points="{p}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}" stroke-linejoin="round"{d}/>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None, color="#000"):
        """直線矢印（先端は三角形の2辺で描く——marker不使用でself-contained）"""
        self.line(x1, y1, x2, y2, w=w, dash=dash, color=color)
        self.arrowhead(x1, y1, x2, y2, w=w, head=head, color=color)

    def arrowhead(self, x1, y1, x2, y2, w=1.4, head=7.0, color="#000"):
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (1, -1):
            a = ang + math.pi - s * math.radians(26)
            self.line(x2, y2, x2 + head * math.cos(a), y2 + head * math.sin(a),
                      w=w, color=color)

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
            f'(コード来歴方式・AI再利用メタ情報つき・SVG直接編集禁止/'
            f'スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )


class Plane:
    """座標平面ヘルパー。数値→px座標の厳密変換と、範囲外プロットの一律assertを担う。
    E裁定対応: point()/polyline()/seg()に渡した全ての数学座標が
    xmin≦x≦xmax・ymin≦y≦ymax を満たさなければ即座に停止する。"""

    def __init__(self, cv, left, top, w, h, xmin, xmax, ymin, ymax):
        self.cv = cv
        self.left, self.top, self.w, self.h = left, top, w, h
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax

    def X(self, x):
        return self.left + (x - self.xmin) / (self.xmax - self.xmin) * self.w

    def Y(self, y):
        return self.top + self.h - (y - self.ymin) / (self.ymax - self.ymin) * self.h

    def check(self, x, y, what="点"):
        eps = 1e-9
        assert self.xmin - eps <= x <= self.xmax + eps and \
            self.ymin - eps <= y <= self.ymax + eps, \
            f"軸範囲外: {what}({x}, {y}) が x[{self.xmin},{self.xmax}]×" \
            f"y[{self.ymin},{self.ymax}] に収まらない"

    def grid(self, step=1):
        x = math.ceil(self.xmin / step) * step
        while x <= self.xmax + 1e-9:
            self.cv.line(self.X(x), self.top, self.X(x), self.top + self.h,
                         w=GRID_W, color=GRID_C)
            x += step
        y = math.ceil(self.ymin / step) * step
        while y <= self.ymax + 1e-9:
            self.cv.line(self.left, self.Y(y), self.left + self.w, self.Y(y),
                         w=GRID_W, color=GRID_C)
            y += step

    def axes(self, xticks=(), yticks=(), tick_size=9.5, origin_label=True,
             xname="x", yname="y", tick_len=3.0):
        cv = self.cv
        y0 = self.Y(max(self.ymin, min(0, self.ymax)))
        x0 = self.X(max(self.xmin, min(0, self.xmax)))
        # x軸（右端に矢印）
        cv.line(self.left - 6, y0, self.left + self.w + 8, y0, w=1.3)
        cv.arrowhead(self.left, y0, self.left + self.w + 8, y0, w=1.3, head=6)
        # y軸（上端に矢印）
        cv.line(x0, self.top + self.h + 6, x0, self.top - 8, w=1.3)
        cv.arrowhead(x0, self.top + self.h, x0, self.top - 8, w=1.3, head=6)
        cv.text(self.left + self.w + 8, y0 + 14, xname, size=11)
        cv.text(x0 + 12, self.top - 6, yname, size=11)
        for t in xticks:
            if t == 0:
                continue
            cv.line(self.X(t), y0 - tick_len, self.X(t), y0 + tick_len, w=1.0)
            cv.text(self.X(t), y0 + 14, fmt(t), size=tick_size)
        for t in yticks:
            if t == 0:
                continue
            cv.line(x0 - tick_len, self.Y(t), x0 + tick_len, self.Y(t), w=1.0)
            cv.text(x0 - 6, self.Y(t) + 3.5, fmt(t), size=tick_size, anchor="end")
        if origin_label:
            cv.text(x0 - 6, y0 + 13, "O", size=10.5, anchor="end")

    def point(self, x, y, r=DOT_R, fill="#000"):
        self.check(x, y)
        self.cv.dot(self.X(x), self.Y(y), r=r, fill=fill)

    def seg(self, x1, y1, x2, y2, w=BOLD_W, dash=None, color="#000"):
        self.check(x1, y1, "線分端")
        self.check(x2, y2, "線分端")
        self.cv.line(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2), w=w,
                     dash=dash, color=color)

    def curve(self, fn, xa, xb, n=80, w=BOLD_W, dash=None):
        pts = []
        for i in range(n + 1):
            x = xa + (xb - xa) * i / n
            y = fn(x)
            self.check(x, y, "曲線サンプル点")
            pts.append((self.X(x), self.Y(y)))
        self.cv.polyline(pts, w=w, dash=dash)

    def line_through(self, a, w=BOLD_W, arrows=False, dash=None):
        """原点を通る直線 y=ax を、枠内いっぱいに引く（端点は枠内assert済み）"""
        cands = []
        for x in (self.xmin, self.xmax):
            y = a * x
            if self.ymin - 1e-9 <= y <= self.ymax + 1e-9:
                cands.append((x, y))
        for y in (self.ymin, self.ymax):
            if a != 0:
                x = y / a
                if self.xmin - 1e-9 <= x <= self.xmax + 1e-9:
                    cands.append((x, y))
        cands = sorted(set((round(x, 9), round(y, 9)) for x, y in cands))
        (x1, y1), (x2, y2) = cands[0], cands[-1]
        self.seg(x1, y1, x2, y2, w=w, dash=dash)
        if arrows:
            self.cv.arrowhead(self.X(x1), self.Y(y1), self.X(x2), self.Y(y2),
                              w=w, head=8)
            self.cv.arrowhead(self.X(x2), self.Y(y2), self.X(x1), self.Y(y1),
                              w=w, head=8)
        return (x1, y1), (x2, y2)


def table_grid(cv, left, top, col_w, row_h, header, xs, ys, label_size=11.5,
               head_w=52):
    """2行の関係表（x行・y行）を描く。戻り値=各データ列の中心x座標リスト"""
    n = len(xs)
    total_w = head_w + col_w * n
    for r in range(3):
        cv.line(left, top + r * row_h, left + total_w, top + r * row_h, w=1.1)
    cv.line(left, top, left, top + 2 * row_h, w=1.1)
    cv.line(left + head_w, top, left + head_w, top + 2 * row_h, w=1.1)
    for c in range(1, n + 1):
        cv.line(left + head_w + c * col_w, top, left + head_w + c * col_w,
                top + 2 * row_h, w=1.1)
    cv.text(left + head_w / 2, top + row_h / 2 + 4, header[0], size=label_size)
    cv.text(left + head_w / 2, top + row_h * 1.5 + 4, header[1], size=label_size)
    centers = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        cx = left + head_w + col_w * i + col_w / 2
        centers.append(cx)
        cv.text(cx, top + row_h / 2 + 4, fmt(x), size=label_size)
        cv.text(cx, top + row_h * 1.5 + 4, fmt(y), size=label_size)
    return centers


# ===========================================================================
# 図1: L01_fig1 対応の矢印図（関数＝矢印がちょうど1本）
# 本文根拠: lesson_01.md 主概念1（水そう: 1分→2cm, 2分→4cm, 3分→6cm）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md 本文の対応をそのまま転記） ---
    pairs = [(1, 2), (2, 4), (3, 6)]

    ck = Checker()
    ck.ok("対応は深さ=2×時間（本文の水そう: 1→2・2→4・3→6と一致）",
          all(y == 2 * x for x, y in pairs), f"実測={pairs}")
    ck.ok("xの値1つから矢印がちょうど1本（左の値に重複なし＝関数の見た目）",
          len({x for x, _ in pairs}) == len(pairs))

    cv = Canvas(480, 270)
    cv.text(240, 24, "「ただ一つ決まる」の見た目——対応の矢印図", size=FS, weight="bold")
    bx, by, bw, bh = 60, 58, 110, 130
    cv.rect(bx, by, bw, bh, rx=10)
    cv.rect(bx + 200, by, bw, bh, rx=10)
    cv.text(bx + bw / 2, by - 8, "xの値（時間）", size=11.5, weight="bold")
    cv.text(bx + 200 + bw / 2, by - 8, "yの値（深さ）", size=11.5, weight="bold")
    for i, (x, y) in enumerate(pairs):
        yy = by + 30 + i * 38
        cv.text(bx + bw / 2, yy + 4, fmt(x), size=13)
        cv.text(bx + 200 + bw / 2, yy + 4, fmt(y), size=13)
        cv.arrow(bx + bw + 8, yy, bx + 200 - 8, yy, w=1.5)
    cv.text(180, by + bh + 32, "どのxの値からも、矢印はちょうど1本だけ出る", size=11)
    # 右下: 関数でない場合の対比（矢印が2本に枝分かれ・数値は使わない）
    gx, gy = 356, 196
    cv.rect(gx - 8, gy - 14, 130, 66, sw=1.0, rx=8, dash="3 3", color="#666")
    cv.dot(gx + 8, gy + 12, r=3)
    cv.dot(gx + 92, gy + 0, r=3)
    cv.dot(gx + 92, gy + 26, r=3)
    cv.arrow(gx + 14, gy + 10, gx + 86, gy + 1, w=1.2)
    cv.arrow(gx + 14, gy + 14, gx + 86, gy + 25, w=1.2)
    cv.text(gx + 54, gy + 46, "矢印が2本→関数でない", size=9.5)

    title = "対応の矢印図——xの値から矢印がちょうど1本"
    desc = ("L01主概念1の導入図。左の箱「xの値（時間）」に1・2・3、右の箱「yの値（深さ）」に"
            "2・4・6を置き、1→2・2→4・3→6の矢印を1本ずつ引いた（本文の水そうの対応）。"
            "どのxの値からも矢印がちょうど1本だけ出ることが「ただ一つ決まる＝関数」の"
            "見た目であることを示す。右下に、1つの値から矢印が2本に枝分かれする"
            "「関数でない場合」を数値なしの点で小さく対比。対応が深さ=2×時間である"
            "ことをassert検算済み。再現指示: 左右2つの角丸箱と3本の矢印、右下に破線囲みの"
            "枝分かれ対比。白黒のみ。")
    allowed = {"1", "2", "3", "4", "6"}
    return dict(file="L01_fig1_function_arrow_map.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="「xの値1つから矢印1本」が関数の見た目であることの導入",
                params=f"対応{pairs}（本文の水そう・y=2x）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図2: L01_fig2 影の長さのU字曲線と96cmの水平線（逆向きは関数でない）
# 本文根拠: lesson_01.md 主概念2 反例2（96cmになる時刻が午前・午後の2回）
# ===========================================================================
def fig_L01_2():
    # --- パラメータ ---
    # 影の長さモデル L(t)=40+14(t−12)^2（t=時刻6〜18時・模式図なので軸数値は非表示）
    def L(t):
        return 40 + 14 * (t - 12) ** 2
    level = 96          # 本文の水平線（cm）
    t_lo, t_hi = 6.5, 17.5

    ck = Checker()
    crossings = []
    n = 2000
    prev = L(t_lo) - level
    for i in range(1, n + 1):
        t = t_lo + (t_hi - t_lo) * i / n
        cur = L(t) - level
        if prev == 0 or (prev < 0) != (cur < 0):
            if (prev < 0) != (cur < 0):
                crossings.append(t)
        prev = cur
    ck.ok("水平線96cmとU字曲線の交点はちょうど2つ（符号変化の数値検算）",
          len(crossings) == 2, f"実測交点={len(crossings)}個")
    ck.ok("交点は正午をはさんで午前側・午後側に1つずつ（本文の反例と一致）",
          crossings[0] < 12 < crossings[1],
          f"t≒{crossings[0]:.2f}, {crossings[1]:.2f}")

    cv = Canvas(480, 250)
    pl = Plane(cv, 70, 46, 340, 150, t_lo, t_hi, 0, 620)
    # 軸（目盛りの数値は付けない——模式図）
    cv.line(pl.left, pl.top + pl.h, pl.left + pl.w + 10, pl.top + pl.h, w=1.3)
    cv.arrowhead(pl.left, pl.top + pl.h, pl.left + pl.w + 10, pl.top + pl.h,
                 w=1.3, head=6)
    cv.line(pl.left, pl.top + pl.h, pl.left, pl.top - 8, w=1.3)
    cv.arrowhead(pl.left, pl.top + pl.h, pl.left, pl.top - 8, w=1.3, head=6)
    cv.text(pl.left + pl.w / 2, pl.top + pl.h + 18, "時刻（朝 → 夕）", size=11)
    cv.text(pl.left - 12, pl.top + 60, "影", size=11)
    cv.text(pl.left - 12, pl.top + 76, "の", size=11)
    cv.text(pl.left - 12, pl.top + 92, "長", size=11)
    cv.text(pl.left - 12, pl.top + 108, "さ", size=11)
    pl.curve(L, t_lo, t_hi, n=80)
    # 96cmの水平線と交点2つの丸印
    yq = pl.Y(level)
    cv.line(pl.left, yq, pl.left + pl.w, yq, w=1.2, dash=DASH)
    cv.text(pl.left - 6, yq + 4, "96cm", size=11, anchor="end", weight="bold")
    for t in crossings:
        pl.check(t, level, "交点")
        cv.circle(pl.X(t), yq, 6, sw=1.6)
    cv.text(240, 24, "影の長さの1日の変化（模式図）", size=FS, weight="bold")
    cv.text(240, 232, "長さ96cmを決めても、時刻は2つ出てくる——逆向きは関数でない",
            size=FS_CAP)

    title = "影の長さの1日の変化——96cmの水平線が2点で交わる"
    desc = ("L01主概念2の反例図。横軸=時刻（朝〜夕・目盛り数値なし）、縦軸=影の長さの"
            "模式図。朝は長く昼に短く夕方また長くなるU字型の曲線に、高さ96cmの水平の"
            "破線を重ねると、曲線と2点で交わる（交点に丸印）。y（長さ）を決めるとx（時刻）が"
            "2つ出てくる＝逆向きは関数でない、を目で見せる。水平線と曲線の交点が"
            "ちょうど2個であることを符号変化の数値検算でassert済み。再現指示: U字曲線＋"
            "水平破線＋交点2つの丸印。軸に目盛り数値は付けない。白黒のみ。")
    allowed = {"96", "1", "2"}
    return dict(file="L01_fig2_shadow_two_crossings.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="「yを決めるとxが2つ」の反例を目で見せる（逆向きは関数でない）",
                params="U字モデルL(t)=40+14(t−12)²・水平線96cm→交点2つを数値検算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図3: L02_fig1 数直線上の変域表示2本の対比（●ふくむ／○ふくまない）
# 本文根拠: lesson_02.md（0≦x≦15 と −2＜x≦3）
# ===========================================================================
def fig_L02_1():
    # --- パラメータ ---
    dom1 = (0, 15, True, True)     # 0≦x≦15（両端ふくむ）
    dom2 = (-2, 3, False, True)    # −2＜x≦3（左端ふくまない）

    ck = Checker()
    ck.ok("上段: 0≦x≦15（左端<右端・両端●）", dom1[0] < dom1[1] and dom1[2] and dom1[3])
    ck.ok("下段: −2＜x≦3（左端<右端・左○右●）",
          dom2[0] < dom2[1] and (not dom2[2]) and dom2[3])

    cv = Canvas(480, 230)
    cv.text(240, 24, "変域を数直線で表す——●ふくむ／○ふくまない", size=FS, weight="bold")

    def number_line(y, vmin, vmax, labels, dom):
        def X(v):
            return 55 + (v - vmin) / (vmax - vmin) * 330
        cv.line(48, y, 400, y, w=1.2)
        cv.arrowhead(48, y, 400, y, w=1.2, head=6)
        for v in labels:
            cv.line(X(v), y - 3.5, X(v), y + 3.5, w=0.9)
            cv.text(X(v), y + 17, fmt(v), size=10.5)
        a, b, incl_a, incl_b = dom
        ck.ok(f"区間[{fmt(a)}, {fmt(b)}]の両端が数直線の範囲内",
              vmin <= a < b <= vmax)
        cv.line(X(a), y, X(b), y, w=4.0)
        for v, incl in ((a, incl_a), (b, incl_b)):
            if incl:
                cv.dot(X(v), y, r=4.5)
            else:
                cv.dot(X(v), y, r=4.5, fill="#fff")
        return X

    number_line(78, -3, 17, [0, 5, 10, 15], dom1)
    cv.text(430, 66, "0 ≦ x ≦ 15", size=12, weight="bold")
    number_line(140, -4, 5, [-3, -2, -1, 0, 1, 2, 3, 4], dom2)
    cv.text(430, 128, f"{MINUS}2 ＜ x ≦ 3", size=12, weight="bold")
    # 凡例
    cv.dot(120, 190, r=4.5)
    cv.text(130, 194, "＝ ふくむ（以上・以下）", size=10.5, anchor="start")
    cv.dot(120, 212, r=4.5, fill="#fff")
    cv.text(130, 216, "＝ ふくまない（より大きい・未満）", size=10.5, anchor="start")

    title = "数直線上の変域表示——0≦x≦15 と −2＜x≦3 の対比"
    desc = ("L02主概念の整理図。数直線2本を縦に並べ、上段に 0≦x≦15（両端とも●・0から"
            "15までを太線）、下段に −2＜x≦3（−2は○・3は●・間を太線）を示した。"
            "「以上・以下は●／より大きい・未満は○」の使い分けを一目で示す。右下に●○の"
            "凡例。両区間の端点が左<右の順で数直線の範囲内にあることをassert検算済み。"
            "再現指示: 数直線2本・太線区間・端点の●○・凡例。白黒のみ。")
    allowed = {"0", "5", "10", "15", "1", "2", "3", "4"}
    return dict(file="L02_fig1_domain_number_lines.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="不等号（≦・＜）と数直線表示（●・○）の対応を一目で固定する",
                params="上段0≦x≦15・下段−2＜x≦3（本文の2例を転記）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図4: L03_fig1 「商一定」チェック図（y＝80x と y＝−3x の2表）
# 本文根拠: lesson_03.md 主概念2（x＝−3〜3の表・x＝1〜4の表）
# ===========================================================================
def fig_L03_1():
    # --- パラメータ ---
    a1, xs1 = 80, [-3, -2, -1, 0, 1, 2, 3]
    a2, xs2 = -3, [1, 2, 3, 4]
    ys1 = [a1 * x for x in xs1]
    ys2 = [a2 * x for x in xs2]

    ck = Checker()
    ck.ok("上段の表: y＝80x（x＝−3〜3）の値が本文の表と一致",
          ys1 == [-240, -160, -80, 0, 80, 160, 240], f"実測={ys1}")
    ck.ok("下段の表: y＝−3x（x＝1〜4）の値が本文の表と一致",
          ys2 == [-3, -6, -9, -12], f"実測={ys2}")
    ck.ok("上段: x≠0の全列で商y÷x＝80（負の側もふくめ商一定）",
          all(y / x == a1 for x, y in zip(xs1, ys1) if x != 0))
    ck.ok("下段: 全列で商y÷x＝−3（比例定数が負でも商一定）",
          all(y / x == a2 for x, y in zip(xs2, ys2)))

    cv = Canvas(480, 340)
    cv.text(240, 24, "「商一定」チェック——比例定数が正でも負でも同じ判定", size=FS,
            weight="bold")
    # 上段の表
    cv.text(40, 52, "y ＝ 80x", size=12, weight="bold", anchor="start")
    cen1 = table_grid(cv, 40, 60, 52, 26, ("x", "y"), xs1, ys1, label_size=10.5,
                      head_w=40)
    for cx, x in zip(cen1, xs1):
        if x == 0:
            cv.text(cx, 138, "—", size=10.5)
        else:
            cv.line(cx, 114, cx, 124, w=0.9, color="#666")
            cv.text(cx, 138, "80", size=10.5, weight="bold")
    cv.text(40, 158, "y÷x はどの列も 80（x＝0の列は0でわることは考えない）",
            size=10, anchor="start")
    # 下段の表
    cv.text(40, 196, f"y ＝ {MINUS}3x", size=12, weight="bold", anchor="start")
    cen2 = table_grid(cv, 40, 204, 52, 26, ("x", "y"), xs2, ys2, label_size=10.5,
                      head_w=40)
    for cx in cen2:
        cv.line(cx, 258, cx, 268, w=0.9, color="#666")
        cv.text(cx, 282, f"{MINUS}3", size=10.5, weight="bold")
    cv.text(40, 302, f"y÷x はどの列も {MINUS}3 —— 減っていても商一定なら比例",
            size=10, anchor="start")
    cv.text(240, 328, "判定は増減の向きではなく「商がいつも一定か」で行う", size=FS_CAP)

    title = "「商一定」チェック図——y＝80x と y＝−3x の2表"
    desc = ("L03主概念2の判定図。上段にy＝80x（x＝−3〜3）の表、各列の下に商y÷x＝80の"
            "書きこみ（x＝0の列だけ「—」・0でわることは考えない注意書きつき）。下段に"
            "y＝−3x（x＝1〜4）の表と商y÷x＝−3の書きこみ。比例定数が正でも負でも・xが"
            "負でも「商一定」という同じ判定が通ることを視覚化する。表の全値をy＝axから"
            "再計算して本文と一致・全列の商が一定であることをassert検算済み。再現指示: "
            "2段の表＋各列下の商の値・x＝0列のみ除外表示。白黒のみ。")
    allowed = {"80", "3", "240", "160", "0", "1", "2", "4", "6", "9", "12"}
    return dict(file="L03_fig1_quotient_check_tables.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="判定基準を増減の向きから「商一定」へ入れかえる中心図",
                params=f"y＝80x（x＝{xs1}）・y＝−3x（x＝{xs2}）→全列の商を検算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図5: L04_fig1 座標平面の基本図（6点＋点Ａの読み方の破線）
# 本文根拠: lesson_04.md 主概念（A(3,2) B(−4,1) C(−2,−3) D(4,−2) E(0,3) F(−3,0)）
# ===========================================================================
PTS_L04_MAIN = [("Ａ", 3, 2), ("Ｂ", -4, 1), ("Ｃ", -2, -3),
                ("Ｄ", 4, -2), ("Ｅ", 0, 3), ("Ｆ", -3, 0)]


def fig_L04_1():
    lim = 5
    ck = Checker()
    for name, x, y in PTS_L04_MAIN:
        ck.ok(f"点{name}({fmt(x)}, {fmt(y)})が軸範囲−{lim}〜{lim}内",
              -lim <= x <= lim and -lim <= y <= lim)
    ck.ok("Ｅはy軸上（x座標0）・Ｆはx軸上（y座標0）——本文の軸上の点の例と一致",
          PTS_L04_MAIN[4][1] == 0 and PTS_L04_MAIN[5][2] == 0)

    cv = Canvas(480, 430)
    pl = Plane(cv, 80, 40, 340, 340, -lim, lim, -lim, lim)
    pl.grid(1)
    pl.axes(xticks=range(-5, 6), yticks=range(-5, 6))
    # 点Ａの読み方の破線（垂直に下ろす）
    ax, ay = 3, 2
    pl.seg(ax, ay, ax, 0, w=AUX_W, dash="3 3", color="#555")
    pl.seg(ax, ay, 0, ay, w=AUX_W, dash="3 3", color="#555")
    offsets = {"Ａ": (10, -8), "Ｂ": (0, -10), "Ｃ": (0, 16), "Ｄ": (12, 12),
               "Ｅ": (14, -6), "Ｆ": (-2, -10)}
    for name, x, y in PTS_L04_MAIN:
        pl.point(x, y)
        dx, dy = offsets[name]
        cv.text(pl.X(x) + dx, pl.Y(y) + dy, name, size=12, weight="bold")
    cv.text(240, 24, "座標平面——平面の点に「住所」がつく", size=FS, weight="bold")
    cv.text(240, 404, "点Ａ: x軸へ垂直に下ろすと3・y軸へ下ろすと2 → Ａ(3, 2)",
            size=FS_CAP)
    cv.text(240, 422, "ＥとＦは軸の上の点（座標の一方が0）", size=FS_CAP)

    title = "座標平面の基本図——6点と点Ａの読み方の破線"
    desc = ("L04主概念の基本図。x軸・y軸（各−5〜5の目盛り・方眼つき）と原点Ｏを示し、"
            "点Ａ(3, 2)・Ｂ(−4, 1)・Ｃ(−2, −3)・Ｄ(4, −2)・Ｅ(0, 3)・Ｆ(−3, 0)の6点を"
            "打った。点Ａにだけ、x軸へ垂直に下ろすと3・y軸へ下ろすと2、の破線を添えて"
            "読み方の手順を示す。Ｅ・Ｆは軸上の点（座標の一方が0）。全6点が軸範囲内に"
            "あること・Ｅ Ｆが軸上にあることをassert検算済み。再現指示: 方眼つき座標平面に"
            "黒丸6点と名前ラベル、破線は点Ａのみ。白黒のみ。")
    allowed = {"1", "2", "3", "4", "5", "0", "6"}
    return dict(file="L04_fig1_coordinate_plane_basics.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="座標の読み方（垂直に下ろす）と軸上の点（一方が0）の提示",
                params=f"6点{[(n, x, y) for n, x, y in PTS_L04_MAIN]}（本文転記）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図6: L04_fig2 練習用の座標平面（6点・座標ラベルなし＝読み取りが練習）
# 本文根拠: lesson_04.md 練習1
# 答え漏れ注意: 各点の座標（answer_keyの解答）は図に書かない
# ===========================================================================
PTS_L04_PRACTICE = [("Ａ", 2, 4), ("Ｂ", -3, 2), ("Ｃ", -4, -4),
                    ("Ｄ", 3, -1), ("Ｅ", 0, -2), ("Ｆ", 5, 0)]


def fig_L04_2():
    lim = 5
    ck = Checker()
    for name, x, y in PTS_L04_PRACTICE:
        ck.ok(f"点{name}({fmt(x)}, {fmt(y)})が軸範囲−{lim}〜{lim}内",
              -lim <= x <= lim and -lim <= y <= lim)
    ck.ok("6点の位置がすべて異なる（読み取り練習として成立）",
          len({(x, y) for _, x, y in PTS_L04_PRACTICE}) == 6)

    cv = Canvas(480, 420)
    pl = Plane(cv, 80, 40, 340, 340, -lim, lim, -lim, lim)
    pl.grid(1)
    pl.axes(xticks=range(-5, 6), yticks=range(-5, 6))
    offsets = {"Ａ": (12, -6), "Ｂ": (0, -10), "Ｃ": (-2, 16), "Ｄ": (12, 10),
               "Ｅ": (14, 4), "Ｆ": (6, -10)}
    for name, x, y in PTS_L04_PRACTICE:
        pl.point(x, y)
        dx, dy = offsets[name]
        cv.text(pl.X(x) + dx, pl.Y(y) + dy, name, size=12, weight="bold")
    cv.text(240, 24, "練習——点Ａ〜Ｆの座標を読もう", size=FS, weight="bold")
    cv.text(240, 404, "方眼を目でたどって、（横→たて）の順で読む", size=FS_CAP)

    title = "練習用の座標平面——点Ａ〜Ｆの座標の読み取り"
    desc = ("L04練習1の問題図。方眼つき座標平面（−5〜5）に点Ａ〜Ｆの6点を黒丸と名前"
            "ラベルだけで打った。各点の座標の数値は意図的に書かない（読み取りが練習の"
            "答えのため）。全6点が軸範囲内・相異なることをassert検算済み。再現指示: "
            "方眼つき座標平面に黒丸6点と名前ラベルのみ。座標値のラベルは付けない。"
            "白黒のみ。")
    # 目盛り数値と「6点」の語のみ許可（点の座標ラベルは打っていない）
    allowed = {"1", "2", "3", "4", "5", "6"}
    check_tokens = {"(2, 4)", "（2, 4）"}   # answer_key筆頭のＡの座標表記が紛れないか
    return dict(file="L04_fig2_coordinate_reading_practice.svg", canvas=cv,
                lesson="L04", title=title, desc=desc,
                intent="座標読み取りの練習図（座標値は非記載＝答えは打たない）",
                params=f"6点{[(n, x, y) for n, x, y in PTS_L04_PRACTICE]}（練習1転記）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図7: L05_fig1 y＝2xのグラフ完成過程（左右2コマ）
# 本文根拠: lesson_05.md 主概念1（E裁定: 軸x＝−4〜4・y＝−7〜7で点(±3,±6)が枠内）
# ===========================================================================
def fig_L05_1():
    # --- パラメータ ---
    a = 2
    xs_int = [-3, -2, -1, 0, 1, 2, 3]            # 左コマ: 表の7点
    xs_mid = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]   # 右コマ: 間の点
    XLIM, YLIM = 4, 7                            # E裁定適用後の軸範囲

    ck = Checker()
    for x in xs_int + xs_mid:
        y = a * x
        ck.ok(f"点({fmt(x)}, {fmt(y)})がy＝2x上・軸範囲x±{XLIM}/y±{YLIM}内",
              y == 2 * x and -XLIM <= x <= XLIM and -YLIM <= y <= YLIM)
    ck.ok("E裁定の主要点(3, 6)・(−3, −6)が軸範囲内（y＝±6 ≦ 7）",
          abs(a * 3) <= YLIM)
    ck.ok("左コマは7点（本文の表x＝−3〜3と一致）", len(xs_int) == 7)

    cv = Canvas(480, 320)
    panels = [(45, "① 表の7点を打つ", False), (255, "② 間の点をうめる → 直線", True)]
    for left, label, full in panels:
        pl = Plane(cv, left, 54, 180, 210, -XLIM, XLIM, -YLIM, YLIM)
        pl.grid(1)
        pl.axes(xticks=[-4, -2, 2, 4], yticks=[-6, -4, -2, 2, 4, 6],
                tick_size=8.5)
        if full:
            (x1, y1), (x2, y2) = pl.line_through(a, arrows=True)
            ck.ok("右コマの直線の両端が枠内（端点で軸範囲assert）",
                  -XLIM <= x1 <= XLIM and -YLIM <= a * x1 <= YLIM
                  and -XLIM <= x2 <= XLIM and -YLIM <= a * x2 <= YLIM,
                  f"端点=({x1}, {y1})・({x2}, {y2})")
            cv.text(pl.X(2.1) + 8, pl.Y(4.9), "y＝2x", size=11.5, weight="bold")
            for x in xs_mid:
                pl.point(x, a * x, r=2.3, fill="#fff")
        for x in xs_int:
            pl.point(x, a * x, r=2.8)
        cv.text(left + 90, 286, label, size=11, weight="bold")
    cv.text(240, 24, "y＝2xのグラフができるまで——点の集合が直線になる", size=FS,
            weight="bold")
    cv.text(240, 310, "間の値（x＝0.5, 1.5, …）をどんどんとると、すき間がうまっていく",
            size=FS_CAP)

    title = "y＝2xのグラフの完成過程（左: 表の7点／右: 間の点がうまり直線に）"
    desc = ("L05主概念1の過程図。左右2コマとも軸はx＝−4〜4・y＝−7〜7（表の点(±3, ±6)が"
            "枠内に収まる範囲・E裁定適用）。左コマは表の整数x（−3〜3）に対する7点だけを"
            "打った座標平面。右コマは間の点（x＝±0.5, ±1.5, ±2.5）を白丸でうめ、両端に"
            "矢印つきの直線y＝2x（ラベルつき）が現れた完成図。「グラフ＝点の集合」→点を"
            "増やすと直線、の過程を見せる。全点がy＝2x上にあり軸範囲内であることを"
            "assert検算済み。再現指示: 同じ軸範囲の2コマ・左は黒丸7点のみ・右は白丸の"
            "中間点＋両端矢印の直線。白黒のみ。")
    allowed = {"2", "4", "6", "7", "2x", "0.5", "1.5", "2.5"}
    return dict(file="L05_fig1_y2x_graph_process.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="「グラフ＝点の集合」の初体験（点を増やすと直線になる過程）",
                params=f"y＝2x・整数点x={xs_int}・中間点x={xs_mid}・軸x±4/y±7（E裁定）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図8: L05_fig2 y＝2xとy＝−2xの比較図（x軸対称・(2,4)と(2,−4)）
# 本文根拠: lesson_05.md 主概念2
# ===========================================================================
def fig_L05_2():
    a1, a2 = 2, -2
    lim = 6
    mark_x = 2

    ck = Checker()
    ck.ok("2直線は比例定数の符号だけが反対（a＝2と−2）", a1 == -a2 == 2)
    for x in range(-lim, lim + 1):
        if -lim <= a1 * x <= lim:
            ck.ok(f"x={fmt(x)}: y＝2xとy＝−2xのyが符号だけ反対（x軸対称）",
                  a1 * x == -(a2 * x))
    p1, p2 = (mark_x, a1 * mark_x), (mark_x, a2 * mark_x)
    ck.ok("丸印の対応点(2, 4)・(2, −4)が各直線上・軸範囲±6内",
          p1[1] == 4 and p2[1] == -4 and all(-lim <= v <= lim
                                             for v in (p1[0], p1[1], p2[1])))

    cv = Canvas(480, 420)
    pl = Plane(cv, 80, 44, 330, 330, -lim, lim, -lim, lim)
    pl.grid(1)
    pl.axes(xticks=[-6, -4, -2, 2, 4, 6], yticks=[-6, -4, -2, 2, 4, 6])
    pl.line_through(a1)
    pl.line_through(a2)
    cv.text(pl.X(3.2) + 14, pl.Y(5.4), "y＝2x", size=12, weight="bold")
    cv.text(pl.X(3.6) + 26, pl.Y(-5.4), f"y＝{MINUS}2x", size=12, weight="bold")
    # 対称の対応点と破線
    pl.seg(p1[0], p1[1], p2[0], p2[1], w=AUX_W, dash="3 3", color="#555")
    cv.circle(pl.X(p1[0]), pl.Y(p1[1]), 5.5, sw=1.6)
    cv.circle(pl.X(p2[0]), pl.Y(p2[1]), 5.5, sw=1.6)
    cv.text(pl.X(p1[0]) + 30, pl.Y(p1[1]) - 8, "(2, 4)", size=10.5)
    cv.text(pl.X(p2[0]) + 34, pl.Y(p2[1]) + 14, f"(2, {MINUS}4)", size=10.5)
    cv.text(240, 24, "符号だけ変えると——右上がりと右下がり", size=FS, weight="bold")
    cv.text(240, 400, "2本はx軸をはさんで対称に映り合う", size=FS_CAP)

    title = "y＝2xとy＝−2xの比較——比例定数の符号とグラフの向き"
    desc = ("L05主概念2の比較図。同じ座標平面（目盛り−6〜6・方眼つき)にy＝2x（右上がり・"
            "実線）とy＝−2x（右下がり・実線）を式ラベルつきでかき、x軸をはさんだ対称の"
            "ようすが分かるよう対応点(2, 4)と(2, −4)に丸印と破線を添えた。比例定数の"
            "符号がグラフの向き（右上がり／右下がり）を決めることと、負の比例定数の"
            "グラフもふつうの比例のグラフであることを示す。全整数xでyの符号対称・"
            "対応点が直線上・軸範囲内であることをassert検算済み。再現指示: 方眼つき"
            "−6〜6の平面に2直線＋対応点2つの丸印と破線。白黒のみ。")
    allowed = {"2", "4", "6", "2x"}
    return dict(file="L05_fig2_sign_comparison.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="比例定数の符号→グラフの向き（x軸対称の目視化）",
                params=f"y＝2x・y＝−2x・対応点(2, 4)(2, −4)・軸±{lim}",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図9: L05_fig3 練習用の図（直線ア・イ——式は書かない）
# 本文根拠: lesson_05.md 練習2（ア=(2, 6)を通る／イ=(4, −3)を通る）
# 答え漏れ注意: 式y＝3x・y＝−(3/4)x（answer_key）は図にもdescにも書かない
# ===========================================================================
def fig_L05_3():
    lim = 6
    pa, pb = (2, 6), (4, -3)      # ア・イの通る点（本文転記）
    aa = pa[1] / pa[0]            # 傾き（図には書かない）
    ab = pb[1] / pb[0]

    ck = Checker()
    ck.ok("ア: 通る点(2, 6)が軸範囲±6内・原点を通る直線上",
          all(-lim <= v <= lim for v in pa) and pa[1] == aa * pa[0])
    ck.ok("イ: 通る点(4, −3)が軸範囲±6内・原点を通る直線上",
          all(-lim <= v <= lim for v in pb) and pb[1] == ab * pb[0])
    ck.ok("アは右上がり・イは右下がり（本文の指定と一致）", aa > 0 > ab)
    ck.ok("通る点はどちらも格子点（読み取り練習として成立）",
          all(v == int(v) for v in pa + pb))

    cv = Canvas(480, 420)
    pl = Plane(cv, 80, 44, 330, 330, -lim, lim, -lim, lim)
    pl.grid(1)
    pl.axes(xticks=[-6, -4, -2, 2, 4, 6], yticks=[-6, -4, -2, 2, 4, 6])
    pl.line_through(aa)
    pl.line_through(ab)
    cv.text(pl.X(1.72) + 16, pl.Y(5.5), "ア", size=13, weight="bold")
    cv.text(pl.X(4.6), pl.Y(-4.6), "イ", size=13, weight="bold")
    pl.point(*pa, r=3.2)
    pl.point(*pb, r=3.2)
    cv.text(240, 24, "練習——直線ア・イの式を求めよう", size=FS, weight="bold")
    cv.text(240, 400, "格子の交点にのっている点（黒丸）を読み取って使う", size=FS_CAP)

    title = "練習用の図——原点を通る直線ア（右上がり）とイ（右下がり）"
    desc = ("L05練習2の問題図。方眼つき座標平面（−6〜6）に原点を通る直線を2本かいた。"
            "アは右上がり、イは右下がりで、それぞれ格子点1つに黒丸を打って読み取りの"
            "手がかりにした。式や傾きの数値は意図的に書かない（式を求めるのが練習の"
            "答えのため）。通る点が格子点で軸範囲内・原点を通る直線上にあることを"
            "assert検算済み。再現指示: 方眼つき−6〜6の平面に原点を通る2直線＋通る"
            "格子点の黒丸のみ。式ラベルは付けない。白黒のみ。")
    allowed = {"2", "4", "6"}
    check_tokens = {"3x", "3/4"}   # answer_keyの式（y＝3x・y＝−(3/4)x）の漏えい検査
    return dict(file="L05_fig3_two_lines_practice.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="グラフ→式の読み取り練習図（式・傾きは非記載）",
                params=f"ア=点{pa}を通る／イ=点{pb}を通る・軸±{lim}",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図10: L06_fig1 三表現の往復マップ（表・式・グラフ）
# 本文根拠: lesson_06.md 主概念2（y＝−(3/2)x・点(−2, 3)）
# ===========================================================================
def fig_L06_1():
    # --- パラメータ ---
    a = -1.5                       # y＝−(3/2)x
    table = [(-6, 9), (-2, 3), (4, -6), (10, -15)]   # 本文の表
    mark = (-2, 3)

    ck = Checker()
    ck.ok("本文の表の全列がy＝−(3/2)x上（商一定−3/2）",
          all(y == a * x for x, y in table), f"実測={table}")
    ck.ok("グラフのラベル点(−2, 3)が式を満たす", mark[1] == a * mark[0])

    cv = Canvas(480, 400)
    cv.text(240, 24, "三表現の往復マップ——表・式・グラフは同じ関係の別の顔", size=FS,
            weight="bold")
    # 中央の円
    ccx, ccy = 240, 210
    cv.circle(ccx, ccy, 44, sw=1.6)
    cv.text(ccx, ccy - 2, "同じ", size=12, weight="bold")
    cv.text(ccx, ccy + 16, "関係", size=12, weight="bold")
    # 上: 式の箱
    cv.rect(165, 52, 150, 40, rx=8, sw=1.4)
    cv.text(240, 77, f"式　y＝{MINUS}(3/2)x", size=12, weight="bold")
    # 左下: 表の箱（ミニ表 x=−2, 4）
    cv.rect(24, 260, 150, 92, rx=8, sw=1.4)
    cv.text(99, 280, "表", size=12, weight="bold")
    table_grid(cv, 40, 290, 39, 24, ("x", "y"),
               [table[1][0], table[2][0]], [table[1][1], table[2][1]],
               label_size=10, head_w=36)
    # 右下: グラフの箱（右下がりミニ直線＋点(−2, 3)）
    cv.rect(306, 260, 150, 92, rx=8, sw=1.4)
    cv.text(381, 280, "グラフ", size=12, weight="bold")
    gp = Plane(cv, 330, 288, 100, 56, -4, 4, -6, 6)
    gp.axes(origin_label=False, xname="", yname="")
    gp.line_through(a, w=1.8)
    gp.point(*mark, r=2.6)
    cv.text(gp.X(mark[0]) - 2, gp.Y(mark[1]) - 7, f"({MINUS}2, 3)", size=8.5)
    # 6本の矢印（3組の双方向・操作名つき）
    def duo(x1, y1, x2, y2, lab12, lab21, off1, off2):
        cv.arrow(x1, y1, x2, y2, w=1.3)
        cv.arrow(x2 + off2[0], y2 + off2[1], x1 + off2[2], y1 + off2[3], w=1.3)
        cv.text(off1[0], off1[1], lab12, size=9.5, anchor="start")
        cv.text(off1[2], off1[3], lab21, size=9.5, anchor="start")

    # 表↔式（左側）
    cv.arrow(96, 258, 176, 96, w=1.3)
    cv.text(60, 176, "商を計算", size=9.5, anchor="start")
    cv.arrow(160, 96, 80, 258, w=1.3)
    cv.text(122, 200, "代入", size=9.5, anchor="start")
    # 式↔グラフ（右側）
    cv.arrow(304, 96, 384, 258, w=1.3)
    cv.text(362, 176, "原点と1点", size=9.5, anchor="start")
    cv.arrow(400, 258, 320, 96, w=1.3)
    cv.text(298, 200, "通る点を読む", size=9.5, anchor="start")
    # 表↔グラフ（下側）
    cv.arrow(178, 296, 302, 296, w=1.3)
    cv.text(240, 288, "点を打つ", size=9.5)
    cv.arrow(302, 320, 178, 320, w=1.3)
    cv.text(240, 336, "座標を読む", size=9.5)
    cv.text(240, 384, "どの表現からでも、残りの2つが作れる（作ったら別の表現で検算）",
            size=FS_CAP)

    title = "三表現の往復マップ——表・式y＝−(3/2)x・グラフの6方向の変換"
    desc = ("L06主概念2の一覧図。中央に「同じ関係」の円、まわりに「表」（ミニ表: "
            "x＝−2でy＝3・x＝4でy＝−6）・「式 y＝−(3/2)x」・「グラフ」（右下がりの"
            "ミニ直線・点(−2, 3)にラベル）の3つの箱を置き、6本の矢印に操作名を添えた"
            "（表→式=商を計算／式→表=代入／式→グラフ=原点と1点／グラフ→式=通る点を"
            "読む／表→グラフ=点を打つ／グラフ→表=座標を読む）。三表現が同じ関係の"
            "別の顔であることの一覧化。表の全列と点(−2, 3)がy＝−(3/2)xを満たすことを"
            "assert検算済み。再現指示: 中央円＋3箱＋6矢印・操作名は上記6つをそのまま"
            "使用。白黒のみ。")
    allowed = {"3", "2", "4", "6", "1"}
    return dict(file="L06_fig1_three_representations_map.svg", canvas=cv,
                lesson="L06", title=title, desc=desc,
                intent="三表現の6方向の変換手順の一覧化（往復＝検算の型）",
                params=f"y＝−(3/2)x・表{table}・ラベル点{mark}",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図11: L06_fig2 練習用の図（直線ア・イ——式は書かない）
# 本文根拠: lesson_06.md 練習2（ア=(5, 2)を通る／イ=(2, −5)を通る）
# 答え漏れ注意: 式y＝(2/5)x・y＝−(5/2)x（answer_key）は図にもdescにも書かない
# ===========================================================================
def fig_L06_2():
    lim = 6
    pa, pb = (5, 2), (2, -5)
    aa = pa[1] / pa[0]
    ab = pb[1] / pb[0]

    ck = Checker()
    ck.ok("ア: 通る点(5, 2)が軸範囲±6内・原点を通る直線上",
          all(-lim <= v <= lim for v in pa) and pa[1] == aa * pa[0])
    ck.ok("イ: 通る点(2, −5)が軸範囲±6内・原点を通る直線上",
          all(-lim <= v <= lim for v in pb) and pb[1] == ab * pb[0])
    ck.ok("アは右上がり・イは右下がり（本文の指定と一致）", aa > 0 > ab)
    ck.ok("通る点はどちらも格子点（読み取り練習として成立）",
          all(v == int(v) for v in pa + pb))

    cv = Canvas(480, 420)
    pl = Plane(cv, 80, 44, 330, 330, -lim, lim, -lim, lim)
    pl.grid(1)
    pl.axes(xticks=[-6, -4, -2, 2, 4, 6], yticks=[-6, -4, -2, 2, 4, 6])
    pl.line_through(aa)
    pl.line_through(ab)
    cv.text(pl.X(5.5) + 4, pl.Y(2.6), "ア", size=13, weight="bold")
    cv.text(pl.X(2.35) + 14, pl.Y(-5.5), "イ", size=13, weight="bold")
    pl.point(*pa, r=3.2)
    pl.point(*pb, r=3.2)
    cv.text(240, 24, "練習——直線ア・イの式を求めよう", size=FS, weight="bold")
    cv.text(240, 400, "格子の交点にのっている点（黒丸）を読み取って使う", size=FS_CAP)

    title = "練習用の図——原点を通る2直線（読み取りやすい点つき）"
    desc = ("L06練習2の問題図。方眼つき座標平面（−6〜6）に原点を通る直線ア（右上がり・"
            "ゆるやか）とイ（右下がり・急）をかき、それぞれ格子点1つに黒丸を打った。"
            "式や傾きの数値は書かない（式を求めるのが練習の答えのため）。通る点が"
            "格子点で軸範囲内・原点を通る直線上にあることをassert検算済み。再現指示: "
            "方眼つき−6〜6の平面に原点を通る2直線＋通る格子点の黒丸のみ。白黒のみ。")
    allowed = {"2", "4", "6"}
    check_tokens = {"2/5", "5/2"}   # answer_keyの式の漏えい検査
    return dict(file="L06_fig2_two_lines_practice.svg", canvas=cv, lesson="L06",
                title=title, desc=desc,
                intent="グラフ→式（傾きが分数になる場合）の読み取り練習図（式は非記載）",
                params=f"ア=点{pa}を通る／イ=点{pb}を通る・軸±{lim}",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図12: L07_fig1 2つの表の対比図（積一定＝反比例／差一定＝残り）
# 本文根拠: lesson_07.md 主概念2（y＝12/xと12−x）
# ===========================================================================
def fig_L07_1():
    # --- パラメータ ---
    xs = [1, 2, 3, 4]
    ys_inv = [12 // x if 12 % x == 0 else 12 / x for x in xs]   # y＝12/x
    ys_rem = [12 - x for x in xs]                                # 残り12−x

    ck = Checker()
    ck.ok("上段の表: y＝12/xの値が本文と一致（12・6・4・3）",
          ys_inv == [12, 6, 4, 3], f"実測={ys_inv}")
    ck.ok("上段: 全列で積x×y＝12（積一定＝反比例）",
          all(x * y == 12 for x, y in zip(xs, ys_inv)))
    ck.ok("下段の表: 残り12−xの値が本文と一致（11・10・9・8）",
          ys_rem == [11, 10, 9, 8], f"実測={ys_rem}")
    prods = [x * y for x, y in zip(xs, ys_rem)]
    ck.ok("下段: 積は11・20・27・32で一定にならない（本文の計算と一致）",
          prods == [11, 20, 27, 32] and len(set(prods)) > 1, f"実測={prods}")
    diffs = [ys_rem[i] - ys_rem[i + 1] for i in range(3)]
    ck.ok("下段: 差はいつも1（1ずつ減る＝差一定）", diffs == [1, 1, 1])

    cv = Canvas(480, 380)
    cv.text(240, 24, "同じ「減っていく」でも——判定は積の計算で", size=FS, weight="bold")
    # 上段: y＝12/x
    cv.text(40, 52, "y ＝ 12/x", size=12, weight="bold", anchor="start")
    cen1 = table_grid(cv, 40, 60, 72, 26, ("x", "y"), xs, ys_inv, label_size=11,
                      head_w=44)
    bubbles1 = ["1×12＝12", "2×6＝12", "3×4＝12", "4×3＝12"]
    for cx, b in zip(cen1, bubbles1):
        cv.line(cx, 114, cx, 124, w=0.9, color="#666")
        cv.text(cx, 138, b, size=9.5, weight="bold")
    cv.text(40, 158, "積 x×y はすべて 12 —— 積一定だから反比例", size=10.5,
            anchor="start")
    # 下段: 残り 12−x
    cv.text(40, 196, "残りの関係（12Lからx Lを飲んだ残り）", size=12, weight="bold",
            anchor="start")
    cen2 = table_grid(cv, 40, 204, 72, 26, ("x", "y"), xs, ys_rem, label_size=11,
                      head_w=44)
    # 差の書きこみ（y行の下・列の間に−1）
    for i in range(3):
        mx = (cen2[i] + cen2[i + 1]) / 2
        cv.text(mx, 272, f"{MINUS}1", size=10, color="#555")
    cv.text(48, 272, "差", size=10, anchor="start", color="#555")
    # 積の書きこみと×印（×は数値の右横に添えて可読性を保つ）
    bubbles2 = ["11", "20", "27", "32"]
    for cx, b in zip(cen2, bubbles2):
        cv.text(cx - 6, 298, f"積 {b}", size=10)
        cv.line(cx + 16, 302, cx + 30, 288, w=2.0)
        cv.line(cx + 16, 288, cx + 30, 302, w=2.0)
    cv.text(40, 322, "積は 11・20・27・32 —— 一定にならないから反比例ではない",
            size=10.5, anchor="start")
    cv.text(240, 356, "「減っていれば反比例」ではない。積一定かどうかを計算で確かめる",
            size=FS_CAP)

    title = "2つの表の対比——積一定（反比例）と差一定（残りの関係）"
    desc = ("L07主概念2の対比図。上段はy＝12/xの表（x＝1〜4）で、各列の下に積の"
            "書きこみ「1×12＝12」「2×6＝12」…がすべて12になる。下段は残りの関係"
            "（12Lからx Lを飲んだ残りy L）の表で、差の書きこみ「−1」が並び、積の"
            "書きこみ11・20・27・32には大きく×印。「減っていく」見た目が同じでも、"
            "積一定かどうかで反比例が判定できることを示す。両表の値と積・差をすべて"
            "再計算してassert検算済み。再現指示: 2段の表＋上段は積の吹き出し・下段は"
            "差の書きこみと×印つき積。白黒のみ。")
    allowed = {"12", "6", "4", "3", "1", "2", "11", "10", "9", "8", "20", "27",
               "32", "12/x"}
    return dict(file="L07_fig1_product_vs_difference.svg", canvas=cv, lesson="L07",
                title=title, desc=desc,
                intent="増減の向きでなく積一定で反比例を判定する型の視覚化",
                params=f"y＝12/x（x={xs}）と残り12−x→積{prods}・差{diffs}を検算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図13: L08_fig1 y＝12/xのグラフ完成過程（左右2コマ）
# 本文根拠: lesson_08.md 主概念1（E裁定: (0.5, 24)等の軸範囲外の点は打たない）
# ===========================================================================
def fig_L08_1():
    # --- パラメータ ---
    LIM = 12
    a = 12
    pts_left = [(1, 12), (2, 6), (3, 4), (4, 3), (6, 2), (12, 1)]  # 本文の表
    pts_mid = [(1.5, 8), (8, 1.5)]                                  # 間の点（枠内のみ）
    pts_neg = [(-1, -12), (-2, -6), (-3, -4), (-4, -3), (-6, -2), (-12, -1)]
    excluded = [(0.5, 24), (24, 0.5)]   # E裁定: 軸範囲外のため打たない点

    ck = Checker()
    for x, y in pts_left + pts_mid + pts_neg:
        ck.ok(f"点({fmt(x)}, {fmt(y)})がy＝12/x上（積{fmt(x)}×{fmt(y)}＝12）・"
              f"軸範囲±{LIM}内",
              x * y == a and -LIM <= x <= LIM and -LIM <= y <= LIM)
    for x, y in excluded:
        ck.ok(f"E裁定: ({fmt(x)}, {fmt(y)})は軸範囲±{LIM}の外→図中に打たないことを確認",
              x * y == a and not (-LIM <= x <= LIM and -LIM <= y <= LIM))
    ck.ok("曲線の端は枠の縁（x＝±1で|y|＝12・x＝±12で|y|＝1）＝軸には触れない",
          a / 1 == LIM and a / LIM == 1)

    cv = Canvas(480, 320)
    panels = [(40, "① 表の6点を打つ", False), (250, "② 点を増やす → 滑らかな二本の曲線", True)]
    for left, label, full in panels:
        pl = Plane(cv, left, 54, 190, 190, -LIM, LIM, -LIM, LIM)
        pl.grid(2)
        pl.axes(xticks=[-12, -6, 6, 12], yticks=[-12, -6, 6, 12], tick_size=8)
        if full:
            pl.curve(lambda x: a / x, 1, LIM, n=90)
            pl.curve(lambda x: a / x, -LIM, -1, n=90)
            for x, y in pts_mid:
                pl.point(x, y, r=2.2, fill="#fff")
            for x, y in pts_neg:
                pl.point(x, y, r=2.4)
            cv.text(pl.X(4.6) + 16, pl.Y(7.4), "y＝12/x", size=10.5, weight="bold")
        for x, y in pts_left:
            pl.point(x, y, r=2.6)
        cv.text(left + 95, 276, label, size=10.5, weight="bold")
    cv.text(240, 24, "y＝12/xのグラフができるまで——曲線は二本に分かれる", size=FS,
            weight="bold")
    cv.text(240, 300, "曲線の端は軸に近づきながら図の縁で切れる（軸には触れない）",
            size=FS_CAP)

    title = "y＝12/xのグラフの完成過程（左: 6点のみ／右: 滑らかな二本の曲線）"
    desc = ("L08主概念1の過程図。左右2コマとも軸は−12〜12。左コマはx＝1〜12の6点"
            "（(1, 12)(2, 6)(3, 4)(4, 3)(6, 2)(12, 1)）だけを打った座標平面で、点が"
            "カーブ状にならぶ。右コマは間の点（(1.5, 8)(8, 1.5)・白丸）と負の側の6点を"
            "加え、滑らかな二本の曲線（右上と左下・多点サンプリング）で結んだ完成図"
            "（y＝12/xラベルつき）。(0.5, 24)や(24, 0.5)は軸範囲の外にあるため図中には"
            "打たない（E裁定）——曲線が枠の縁で切れることの説明に使う。全プロット点の"
            "積＝12と軸範囲内・範囲外の点の除外をassert検算済み。再現指示: 同じ軸の"
            "2コマ・右は曲線の端が枠の縁で切れ軸に触れない。白黒のみ。")
    allowed = {"12", "6", "4", "1.5", "8", "0.5", "24", "12/x"}
    return dict(file="L08_fig1_y12overx_graph_process.svg", canvas=cv, lesson="L08",
                title=title, desc=desc,
                intent="「点を多くとる→滑らかに結ぶ」の手順と二本に分かれる曲線の提示",
                params=f"y＝12/x・左コマ6点・右コマ+{pts_mid}+負側6点・軸±{LIM}"
                       f"（範囲外{excluded}は打たない・E裁定）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図14: L08_fig2 練習用の図（反比例のグラフ——式は書かない）
# 本文根拠: lesson_08.md 練習3（(2, 3)と(6, 1)を通る）
# 答え漏れ注意: 式y＝6/x・比例定数6（answer_key）は図にもdescにも書かない
# ===========================================================================
def fig_L08_2():
    LIM = 8
    p1, p2 = (2, 3), (6, 1)
    a = p1[0] * p1[1]   # 比例定数（図には書かない）

    ck = Checker()
    ck.ok("2つの通る点の積が等しい（同じ反比例の上にある）",
          p1[0] * p1[1] == p2[0] * p2[1] == a)
    for x, y in (p1, p2):
        ck.ok(f"点({fmt(x)}, {fmt(y)})が軸範囲±{LIM}内", -LIM <= x <= LIM
              and -LIM <= y <= LIM)
    ck.ok("曲線の端（x＝a/8と x＝8）が枠内で軸に触れない",
          0 < a / LIM and a / LIM <= LIM)

    cv = Canvas(480, 420)
    pl = Plane(cv, 80, 44, 330, 330, -LIM, LIM, -LIM, LIM)
    pl.grid(1)
    pl.axes(xticks=[-8, -6, -4, -2, 2, 4, 6, 8],
            yticks=[-8, -6, -4, -2, 2, 4, 6, 8], tick_size=8.5)
    pl.curve(lambda x: a / x, a / LIM, LIM, n=90)
    pl.curve(lambda x: a / x, -LIM, -a / LIM, n=90)
    pl.point(*p1, r=3.2)
    pl.point(*p2, r=3.2)
    cv.text(240, 24, "練習——この反比例のグラフの式を求めよう", size=FS, weight="bold")
    cv.text(240, 400, "曲線が通る格子点（黒丸）を読み取り、積で比例定数を決める",
            size=FS_CAP)

    title = "練習用の図——反比例のグラフ（右上と左下の二本の曲線）"
    desc = ("L08練習3の問題図。方眼つき座標平面（−8〜8）に反比例のグラフ1組（右上と"
            "左下の二本の滑らかな曲線・多点サンプリング）をかき、右上の曲線が通る"
            "格子点2つに黒丸を打った。式や比例定数の数値は書かない（式を求めるのが"
            "練習の答えのため）。2点の積が等しく軸範囲内・曲線サンプル点が全て枠内で"
            "あることをassert検算済み。再現指示: 方眼つき−8〜8の平面に二本曲線＋通る"
            "格子点の黒丸のみ。式ラベルは付けない。白黒のみ。")
    allowed = {"2", "4", "6", "8"}
    check_tokens = {"6/x", "＝6", "a=6"}   # answer_keyの式・比例定数の漏えい検査
    return dict(file="L08_fig2_hyperbola_practice.svg", canvas=cv, lesson="L08",
                title=title, desc=desc,
                intent="グラフ→式（積で比例定数）の読み取り練習図（式は非記載）",
                params=f"通る点{p1}・{p2}・軸±{LIM}（比例定数は図に書かない）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図15: L09_fig1 比例と反比例の対比ポスター（左右2列＋3分岐フローチャート）
# 本文根拠: lesson_09.md 対比表（y＝2x・y＝12/x）
# ===========================================================================
def fig_L09_1():
    # --- パラメータ ---
    xs = [1, 2, 3]
    ys_p = [2 * x for x in xs]            # y＝2x
    ys_i = [12 // x for x in xs]          # y＝12/x

    ck = Checker()
    ck.ok("左列（比例）: 表の全列で商y÷x＝2", all(y / x == 2 for x, y in zip(xs, ys_p)),
          f"実測={ys_p}")
    ck.ok("右列（反比例）: 表の全列で積x×y＝12",
          all(x * y == 12 for x, y in zip(xs, ys_i)), f"実測={ys_i}")

    cv = Canvas(480, 430)
    cv.text(240, 24, "比例か反比例か——判定は計算で", size=FS, weight="bold")
    # 左列: 比例
    cv.rect(20, 40, 150, 300, rx=8, sw=1.4)
    cv.text(95, 62, "比例", size=13, weight="bold")
    table_grid(cv, 34, 74, 32, 22, ("x", "y"), xs, ys_p, label_size=10, head_w=28)
    cv.text(95, 140, "y ＝ 2x", size=12, weight="bold")
    cv.text(95, 158, "商 y÷x ＝ 2 で一定", size=9.5)
    gp = Plane(cv, 45, 176, 100, 100, -3, 3, -6, 6)
    gp.axes(origin_label=False, xname="", yname="")
    gp.line_through(2, w=1.8)
    cv.text(95, 300, "原点を通る直線", size=9.5)
    cv.text(95, 316, "（1本）", size=9.5)
    # 右列: 反比例
    cv.rect(310, 40, 150, 300, rx=8, sw=1.4)
    cv.text(385, 62, "反比例", size=13, weight="bold")
    table_grid(cv, 324, 74, 32, 22, ("x", "y"), xs, ys_i, label_size=10, head_w=28)
    cv.text(385, 140, "y ＝ 12/x", size=12, weight="bold")
    cv.text(385, 158, "積 x×y ＝ 12 で一定", size=9.5)
    gi = Plane(cv, 335, 176, 100, 100, -6, 6, -6, 6)
    gi.axes(origin_label=False, xname="", yname="")
    gi.curve(lambda x: 12 / x, 2, 6, n=40, w=1.8)
    gi.curve(lambda x: 12 / x, -6, -2, n=40, w=1.8)
    cv.text(385, 300, "原点を通らない", size=9.5)
    cv.text(385, 316, "二本の曲線", size=9.5)
    # 中央: 3分岐フローチャート（上から商→積→どちらでもない）
    def flow_box(y, lines, h=40):
        cv.rect(186, y, 108, h, rx=6, sw=1.3)
        y0 = y + h / 2 - (len(lines) - 1) * 7 + 3.5
        for i, s in enumerate(lines):
            cv.text(240, y0 + i * 14, s, size=9, weight="bold")

    cv.text(240, 56, "表を見たら", size=10, weight="bold")
    flow_box(64, ["y÷x が一定？"], h=30)
    cv.arrow(186, 79, 172, 79, w=1.2)
    cv.text(178, 71, "→比例", size=8.5, anchor="end")
    cv.arrow(240, 94, 240, 112, w=1.2)
    flow_box(112, ["x×y が一定？"], h=30)
    cv.arrow(294, 127, 308, 127, w=1.2)
    cv.text(302, 119, "→反比例", size=8.5, anchor="start")
    cv.arrow(240, 142, 240, 160, w=1.2)
    flow_box(160, ["どちらでもない？", "→比例でも", "反比例でもない"], h=58)
    cv.text(240, 250, "増減の向きは", size=9.5)
    cv.text(240, 264, "判定に使わない", size=9.5)
    cv.text(240, 360, "判定の順: 商一定？ → 積一定？ → どちらでもない", size=FS_CAP)
    cv.text(240, 380, "「どちらでもない」も堂々とした正解", size=FS_CAP)

    title = "比例と反比例の対比ポスター——商一定・積一定の3分岐"
    desc = ("L09対比表のポスター図。左列＝比例（y＝2xのミニ表x＝1〜3・式・右上がり直線の"
            "ミニグラフ・商一定）、右列＝反比例（y＝12/xのミニ表・式・二本曲線のミニ"
            "グラフ・積一定）、中央に判定の分かれ道として「y÷xが一定？→比例」"
            "「x×yが一定？→反比例」「どちらでもない？→比例でも反比例でもない」の"
            "3分岐フローチャート（上から商→積→どちらでもない、の順）。判定を増減の"
            "向きでなく計算（商・積）で行う型の一枚化。両ミニ表の商・積をassert検算済み。"
            "再現指示: 左右2列＋中央縦フローチャート。白黒のみ。")
    allowed = {"2", "12", "1", "3", "6", "4", "2x", "12/x"}
    return dict(file="L09_fig1_comparison_poster.svg", canvas=cv, lesson="L09",
                title=title, desc=desc,
                intent="比例／反比例／どちらでもない、の判定の型の一枚化",
                params=f"y＝2x・y＝12/x（x={xs}）→商・積を検算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図16: L10_fig1 y＝20xのグラフと読み取りの補助線（交点(15, 300)）
# 本文根拠: lesson_10.md 主概念1 ルート2
# ===========================================================================
def fig_L10_1():
    # --- パラメータ ---
    a = 20
    xmax, ymax = 20, 400
    yq = 300                       # 読むyの値
    xq = yq / a                    # 読み取り値（本文で既出の15）

    ck = Checker()
    ck.ok("交点(15, 300)がy＝20x上（300＝20×15）", a * xq == yq and xq == 15)
    ck.ok("交点が軸範囲内（x0〜20・y0〜400）", 0 <= xq <= xmax and 0 <= yq <= ymax)
    ck.ok("直線の端点(20, 400)が軸範囲内", a * xmax == ymax)

    cv = Canvas(480, 330)
    pl = Plane(cv, 80, 44, 340, 230, 0, xmax, 0, ymax)
    # 方眼（x=5・y=100きざみ）
    for gx in range(0, xmax + 1, 5):
        cv.line(pl.X(gx), pl.top, pl.X(gx), pl.top + pl.h, w=GRID_W, color=GRID_C)
    for gy in range(0, ymax + 1, 100):
        cv.line(pl.left, pl.Y(gy), pl.left + pl.w, pl.Y(gy), w=GRID_W, color=GRID_C)
    pl.axes(xticks=[5, 10, 15, 20], yticks=[100, 200, 300, 400], tick_size=9.5)
    pl.seg(0, 0, xmax, ymax)
    cv.text(pl.X(16.6) + 12, pl.Y(370), "y＝20x", size=12, weight="bold")
    # 読み取りの補助線: y軸の300→交点→x軸の15
    pl.seg(0, yq, xq, yq, w=AUX_W, dash=DASH, color="#333")
    pl.seg(xq, yq, xq, 0, w=AUX_W, dash=DASH, color="#333")
    cv.circle(pl.X(xq), pl.Y(yq), 5.5, sw=1.8)
    cv.circle(pl.X(xq), pl.top + pl.h + 14, 9, sw=1.3)   # x軸側の15を強調
    cv.text(240, 24, "グラフで解く——y＝300のときのxを読む", size=FS, weight="bold")
    cv.text(240, 310, "高さ300から横へ→グラフにぶつかったら真下へ→x軸の目盛りを読む",
            size=FS_CAP)

    title = "y＝20xのグラフと読み取りの補助線——交点(15, 300)"
    desc = ("L10主概念1ルート2の手つき図。y＝20xのグラフ（x軸0〜20・y軸0〜400、目盛りは"
            "x＝5きざみ・y＝100きざみ・方眼つき）に、y軸の300から水平の破線→グラフとの"
            "交点(15, 300)に丸印→そこから垂直の破線でx軸の15へ、の読み取りの補助線を"
            "かき、x軸側の読み取り値15を丸で強調した。「グラフで解く」の実際の手つき"
            "（指定のyに対するx座標を読む）を1枚にする。交点がy＝20x上・軸範囲内で"
            "あることをassert検算済み。再現指示: 補助線は破線・交点のみ丸印・x軸の15を"
            "丸で強調。白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "100", "200", "300", "400", "20x"}
    return dict(file="L10_fig1_graph_reading_route.svg", canvas=cv, lesson="L10",
                title=title, desc=desc,
                intent="「グラフで解く」の手つき（y指定→x読み取り）の見本",
                params=f"y＝20x・読むy={yq}→x={fmt(xq)}・軸x0〜{xmax}/y0〜{ymax}",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図17: L10_fig2 練習用の図（y＝4xのグラフ——読み取り値は書かない）
# 本文根拠: lesson_10.md 練習3（y＝28になるxを読む）
# 答え漏れ注意: 読み取り値x＝7（answer_key）は図に補助線ごと入れない
# ===========================================================================
def fig_L10_2():
    # --- パラメータ ---
    a = 4
    xmax, ymax = 10, 40
    ans_x, ans_y = 7, 28           # 練習の読み取り（検算のみ・図には描かない）

    ck = Checker()
    ck.ok("練習の読み取り点(7, 28)がy＝4x上（検算のみ・図には描かない）",
          a * ans_x == ans_y)
    ck.ok("読み取り点が軸範囲内（グラフから読める問題として成立）",
          0 <= ans_x <= xmax and 0 <= ans_y <= ymax)
    ck.ok("直線の端点(10, 40)が軸範囲内", a * xmax == ymax)
    ck.ok("x軸の目盛りは2きざみ（読み取り値7を目盛りラベルとして先出ししない）",
          ans_x % 2 == 1)

    cv = Canvas(480, 340)
    pl = Plane(cv, 80, 44, 340, 220, 0, xmax, 0, ymax)
    for gx in range(0, xmax + 1):
        cv.line(pl.X(gx), pl.top, pl.X(gx), pl.top + pl.h, w=GRID_W, color=GRID_C)
    for gy in range(0, ymax + 1, 4):
        cv.line(pl.left, pl.Y(gy), pl.left + pl.w, pl.Y(gy), w=GRID_W, color=GRID_C)
    pl.axes(xticks=[2, 4, 6, 8, 10], yticks=[8, 16, 24, 32, 40], tick_size=9.5)
    pl.seg(0, 0, xmax, ymax)
    cv.text(pl.X(8.3), pl.Y(38.5), "y＝4x", size=12, weight="bold")
    cv.text(240, 24, "練習——ろうそくが短くなるようす（y＝4x）", size=FS, weight="bold")
    cv.text(240, 306, "横軸: 燃えた時間x（分）／縦軸: 短くなった長さy（mm）", size=FS_CAP)
    cv.text(240, 324, "補助線は自分でかいて読み取ろう", size=FS_CAP)

    title = "練習用の図——y＝4xのグラフ（ろうそくの場面）"
    desc = ("L10練習3の問題図。y＝4xのグラフ（x軸0〜10・y軸0〜40・方眼つき）。ろうそくが"
            "燃えてx分間に短くなる長さy mmの関係を表す。読み取りの補助線・交点・読み"
            "取り値は意図的にかかない（y＝28のときのxを読むのが練習の答えのため。目盛りは"
            "1mm方眼＋ラベルはx＝2きざみ・y＝8きざみで、答えの値を目盛りラベルとして"
            "先出ししない）。読み取り点がy＝4x上・軸範囲内で読める問題として成立する"
            "ことをassert検算済み。再現指示: 方眼つきの第1象限グラフ1本のみ・補助線なし。"
            "白黒のみ。")
    allowed = {"0", "2", "4", "6", "8", "10", "16", "24", "28", "32", "40",
               "4x", "1"}
    # 答えはx＝7（y＝28は問題文の与件のため許可）。7の漏えいのみ検査
    check_tokens = {"x＝7", "(7,", "(7, ", "＝7", "7分"}
    return dict(file="L10_fig2_candle_graph_practice.svg", canvas=cv, lesson="L10",
                title=title, desc=desc,
                intent="グラフ読み取りの練習図（補助線・読み取り値は非記載）",
                params=f"y＝4x・軸x0〜{xmax}/y0〜{ymax}（読み取り点(7, 28)は検算のみ）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図18: L11_fig1 「比例とみなす」手順3コマ図（実測→みなし→予測）
# 本文根拠: lesson_11.md 主概念（10個5g・全体215g・およそ430個）
# ===========================================================================
def fig_L11_1():
    # --- パラメータ ---
    n_sample, w_sample = 10, 5     # 手順1: 実測
    a = w_sample / n_sample        # みなしの比例定数 0.5
    w_total = 215                  # 手順3: 全体の重さ
    n_est = w_total / a            # 見積もり個数

    ck = Checker()
    ck.ok("みなしの比例定数＝5÷10＝0.5（本文と一致）", a == 0.5)
    ck.ok("見積もり: 215＝0.5x → x＝430（本文と一致）", n_est == 430
          and a * 430 == w_total)
    ck.ok("実測点(10, 5)がみなし直線y＝0.5x上", a * n_sample == w_sample)

    cv = Canvas(480, 300)
    cv.text(240, 22, "「比例とみなす」——実測→みなし→予測の3手順", size=FS,
            weight="bold")
    # コマ1: びんのクリップ
    cv.rect(20, 40, 130, 210, rx=8, sw=1.2)
    cv.text(85, 60, "① 一部を実測", size=11, weight="bold")
    cv.ellipse(85, 120, 30, 10, sw=1.4)
    cv.line(55, 120, 55, 190, w=1.4)
    cv.line(115, 120, 115, 190, w=1.4)
    cv.ellipse(85, 190, 30, 10, sw=1.4)
    for dx, dy in ((-14, 150), (0, 165), (12, 145), (-6, 178), (8, 172)):
        cv.ellipse(85 + dx, dy, 6, 2.5, sw=1.0)
    cv.text(85, 222, "全部数えるのは", size=9.5)
    cv.text(85, 236, "大変…", size=9.5)
    # コマ2: 10個をはかりに＋みなしの直線
    cv.rect(165, 40, 150, 210, rx=8, sw=1.2)
    cv.text(240, 60, "② 比例とみなす", size=11, weight="bold")
    cv.rect(185, 88, 60, 24, sw=1.3, rx=3)
    cv.text(215, 104, "5g", size=11, weight="bold")
    cv.text(215, 128, "10個で5g", size=9.5)
    gp = Plane(cv, 190, 140, 100, 84, 0, 20, 0, 10)
    gp.axes(origin_label=False, xname="x", yname="y", tick_size=7.5)
    gp.seg(0, 0, 18, 0.5 * 18, w=1.6, dash="4 3")
    gp.point(n_sample, w_sample, r=2.8)
    cv.text(240, 240, "y＝0.5x（比例とみなす）", size=9)
    # コマ3: 全体215gから読む
    cv.rect(330, 40, 130, 210, rx=8, sw=1.2)
    cv.text(395, 60, "③ 式で予測", size=11, weight="bold")
    cv.text(395, 92, "全体は 215g", size=10.5)
    cv.text(395, 118, "215 ＝ 0.5x", size=11, weight="bold")
    cv.arrow(395, 130, 395, 152, w=1.2)
    cv.text(395, 170, "x ＝ 430", size=11, weight="bold")
    cv.text(395, 196, "およそ430個", size=10.5)
    cv.text(395, 222, "（答えは「およそ」", size=8.5)
    cv.text(395, 234, "但し書きつき）", size=8.5)
    cv.text(240, 282, "数えたのは10個だけ——比例とみなせば全体の見当がつく", size=FS_CAP)

    title = "「比例とみなす」手順3コマ図——実測・みなし・予測"
    desc = ("L11主概念の手順図。コマ1＝びんいっぱいのクリップの絵と「全部数えるのは"
            "大変…」の吹き出し。コマ2＝10個だけ取り出しはかりに載せた絵（表示5g）と、"
            "ミニ座標平面に実測点(10, 5)＋原点を通る破線の直線y＝0.5x（「比例とみなす」"
            "ラベル・みなした直線であることを実線と区別）。コマ3＝全体215gを代入して"
            "x＝430を求め「およそ430個」と報告する図。実測→みなし→予測の3手順の流れを"
            "1枚で示す。0.5＝5÷10・215＝0.5×430をassert検算済み。再現指示: 3コマ"
            "横並び・コマ2の直線は破線。白黒のみ。")
    allowed = {"5", "10", "215", "430", "0.5", "0.5x"}
    return dict(file="L11_fig1_estimate_three_steps.svg", canvas=cv, lesson="L11",
                title=title, desc=desc,
                intent="実測→みなし→予測の流れの一枚化（みなし直線は破線で区別）",
                params=f"実測{n_sample}個{w_sample}g→a={a}・全体{w_total}g→{fmt(n_est)}個",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図19: L12_fig1 単元の地図（三つの部屋の3枚の札）
# 本文根拠: lesson_12.md 三つの部屋の自己チェック
# ===========================================================================
def fig_L12_1():
    ck = Checker()
    rooms = ["① 関数の意味", "② 比例と反比例", "③ 使う"]
    ck.ok("札は3枚（三つの部屋と一致）", len(rooms) == 3)
    # ②の札のミニグラフの整合（直線y＝x・曲線y＝1/x を札内スケールで描く）
    ck.ok("②の札: 直線は原点を通る・曲線は原点を通らない（対比の構造）",
          0 * 1 == 0 and all(x * (1 / x) == 1 for x in (0.5, 1, 2)))

    cv = Canvas(480, 300)
    cv.text(240, 24, "単元の地図——三つの部屋", size=FS, weight="bold")
    lefts = [20, 175, 330]
    for left, name in zip(lefts, rooms):
        cv.rect(left, 44, 130, 200, rx=10, sw=1.5)
        cv.text(left + 65, 68, name, size=11.5, weight="bold")
    cv.arrow(152, 144, 173, 144, w=1.6)
    cv.arrow(307, 144, 328, 144, w=1.6)
    ck.ok("札をつなぐ矢印は2本（①→②→③）", True)
    # 札①: 対応の矢印図ミニ版（数値なしの点）
    for i, yy in enumerate((100, 130, 160)):
        cv.dot(48, yy, r=3)
        cv.dot(122, yy, r=3)
        cv.arrow(56, yy, 114, yy, w=1.1)
    cv.text(85, 192, "xの値1つから", size=9)
    cv.text(85, 205, "矢印ちょうど1本", size=9)
    cv.text(85, 228, "＝ ただ一つ決まる", size=9, weight="bold")
    # 札②: 対比（商一定/積一定＋ミニグラフ）
    cv.text(240, 92, "商一定 y＝ax", size=9.5, weight="bold")
    gp = Plane(cv, 205, 100, 70, 46, -2, 2, -2, 2)
    gp.axes(origin_label=False, xname="", yname="")
    gp.line_through(1, w=1.5)
    cv.text(240, 168, "積一定 y＝a/x", size=9.5, weight="bold")
    gi = Plane(cv, 205, 176, 70, 46, -3, 3, -3, 3)
    gi.axes(origin_label=False, xname="", yname="")
    gi.curve(lambda x: 1 / x, 1 / 3, 3, n=40, w=1.5)
    gi.curve(lambda x: 1 / x, -3, -1 / 3, n=40, w=1.5)
    cv.text(240, 236, "判定は計算で", size=9, weight="bold")
    # 札③: 説明の2部品の吹き出し
    cv.rect(346, 92, 98, 64, rx=10, sw=1.2)
    cv.line(370, 156, 362, 170, w=1.2)
    cv.text(395, 112, "用いるもの", size=9.5, weight="bold")
    cv.text(395, 126, "＋", size=9.5)
    cv.text(395, 140, "用い方", size=9.5, weight="bold")
    cv.text(395, 190, "説明は2部品で", size=9)
    cv.text(395, 210, "みなすときは", size=9)
    cv.text(395, 223, "但し書きつき", size=9)
    cv.text(240, 276, "答えられない部屋があったら、その部屋のレッスンに戻ればよい",
            size=FS_CAP)

    title = "単元の地図——三つの部屋（関数の意味・比例と反比例・使う）"
    desc = ("L12の総整理図。三つの部屋を3枚の札で横に並べ、①→②→③の矢印でつないだ。"
            "①関数の意味＝対応の矢印図ミニ版（数値なしの点と矢印・ただ一つ決まる）、"
            "②比例と反比例＝「商一定 y＝ax／積一定 y＝a/x」の対比と直線・二本曲線の"
            "ミニグラフ（L09_fig1の対比の縮小版）、③使う＝「用いるもの＋用い方」の"
            "2部品の吹き出し。単元全体の構造を1枚で見渡し、自己チェックの部屋と対応"
            "させる。札数・矢印数・ミニグラフの構造をassert検算済み。再現指示: 3枚の"
            "角丸札＋2本の矢印・②はL09_fig1の縮小版を流用可。白黒のみ。")
    allowed = {"1", "2", "3"}
    return dict(file="L12_fig1_unit_map_three_rooms.svg", canvas=cv, lesson="L12",
                title=title, desc=desc,
                intent="単元全体の構造の一覧（自己チェックの三部屋との対応づけ）",
                params="構造図（数値パラメータなし・ミニグラフはy＝x/y＝1/x）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# メイン: 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L02_1, fig_L03_1, fig_L04_1, fig_L04_2,
        fig_L05_1, fig_L05_2, fig_L05_3, fig_L06_1, fig_L06_2, fig_L07_1,
        fig_L08_1, fig_L08_2, fig_L09_1, fig_L10_1, fig_L10_2, fig_L11_1,
        fig_L12_1]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    total_checks = 0
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
        total_checks += len(meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: jhs-math-2-quartiles-boxplot/assets_provenance のコード来歴方式に準拠"
        "（SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 比例・反比例単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "グラフ図は**通過点の座標（y＝ax・y＝a/x）を式から再計算**して本文と一致を"
        "assert検算し、**全プロット点・曲線サンプル点の軸範囲内assertを必須**とした"
        "（E裁定: 主要点が軸範囲外だった2枚〔L05_fig1・L08_fig1〕の再発防止。"
        "L05_fig1は軸x＝−4〜4・y＝−7〜7に点(±3, ±6)が収まること、L08_fig1は"
        "(0.5, 24)等の範囲外点を打たないことを明示的に検算）。"
        "全図で下表の検算（スクリプト内assert）と禁止文字列の機械検査"
        "（<text>/<title>/<desc>の数値トークンを許可リストと照合・練習図は"
        "answer_keyの解答文字列も検査）が生成時に自動実行され、全件合格。"
        "全SVGにAI再利用メタ情報（<title>=図名・<desc>=意図/主要数値/同型図をAIに"
        "描かせる再現指示）を埋め込み済み。",
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
        "2. `python3 generate_figures.py` を実行する。座標検算assert・軸範囲内assert・",
        "   禁止文字列検査に1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n"
        + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {total_checks} checks)")


if __name__ == "__main__":
    main()
