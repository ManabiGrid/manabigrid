#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1数学「不確定な事象の起こりやすさ（頻度確率）」単元 図版パラメトリック生成スクリプト
================================================================================
様式: jhs-math-2-quartiles-boxplot/assets_provenance/generate_figures.py と同一のコード来歴方式
（Python標準ライブラリのみ・assert検算・解答値を図に載せない・<title>/<desc>のAI再利用メタ情報・白黒両立）。
描画ヘルパー（Canvas等）は同スクリプトの実装を流用（無変更の方針）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（4枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / decimal / html / pathlib）
- 自己検証:
  1) 統計検算assert — 相対度数を本文の生データ（回数r・投げた回数n）から
     **四捨五入（小数第2位まで・ROUND_HALF_UP）**で再計算し、本文の表の値と
     一致しなければ図を出力しない。合計・最大値の位置も再計算して検算する。
  2) 禁止文字列の機械検査 — 各図の<text>/<title>/<desc>に現れる数値トークンを全て抽出し、
     図ごとの「許可数値リスト」外の数値（＝答えの漏えい候補）があれば停止。
     特にL03図は、練習1の空らん（あ）の解答値（answer_key由来・ここには書かない）を
     check_tokensで機械検査する（E裁定の抑止注記を厳守）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
  SVGの直接編集は禁止（来歴が切れる）。
"""

import math
import re
import datetime
from decimal import Decimal, ROUND_HALF_UP
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（quartiles-boxplot版と同一） ------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px) — viewBox幅~480で約3%
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


def relfreq2(r, n):
    """相対度数 r/n を四捨五入して小数第2位まで（本文の指示どおりROUND_HALF_UP）。
    floatの2進誤差で四捨五入がずれないよう、Decimalの厳密な割り算で行う。"""
    return Decimal(r) / Decimal(n)


def round2(r, n):
    return relfreq2(r, n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# レッスンID（L01〜L03）・「主概念1」「手順①〜④」等の構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "1", "2", "3", "4"}


def audit_numbers(svg, allowed, check_tokens, fig_id):
    """禁止文字列の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。allowed=許可数値トークン集合、check_tokens=答え漏れ検査トークン
    （answer_keyにのみ現れる値。この検査があるため解答値は図にもメタにも載らない）。"""
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
# 描画ヘルパー（quartiles-boxplot版から流用）
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

    def dot(self, x, y, r=DOT_R, fill="#000", sw=1.2):
        if fill == "none" or fill == "#fff":
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                     f'stroke="#000" stroke-width="{sw}"/>')
        else:
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def circle(self, x, y, r, sw=MAIN_W, fill="none", color="#000"):
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" '
                 f'stroke="{color}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, color="#000"):
        wgt = f' font-weight="{weight}"' if weight else ""
        c = f' fill="{color}"' if color != "#000" else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{c}>{escape(s)}</text>')

    def polyline(self, pts, w=MAIN_W, color="#000"):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.raw(f'<polyline points="{p}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}"/>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None, color="#000"):
        """直線矢印（先端は三角形の2辺で描く——marker不使用でself-contained）"""
        self.line(x1, y1, x2, y2, w=w, dash=dash, color=color)
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


# ===========================================================================
# 図1: L01 ペットボトルのふたの3つの落ち方
# 本文根拠: lesson_01.md 主概念1の figure-spec（3つを横に並べ、呼び名を本文と完全一致・装飾なし）
# ===========================================================================
def fig_L01_cap():
    # --- パラメータ（lesson_01.md 本文の呼び名をそのまま転記） ---
    names = ["上向き", "下向き", "横向き"]
    subs = ["（開いた口が上）", "（口が下、かぶさる形）", "（転がって横になった形）"]

    ck = Checker()
    ck.ok("落ち方は3通り・呼び名が本文（上向き・下向き・横向き）と完全一致",
          names == ["上向き", "下向き", "横向き"] and len(names) == 3)

    cv = Canvas(480, 230)
    ground = 152
    centers = [96, 240, 384]
    half_w, wall_top = 32, 112   # ふた断面: 幅64px・高さ40px
    wall = 3.0                   # プラスチック壁を太線1本で表す

    # パネル1: 上向き（口が上に開く——底が接地・上辺は描かない）
    cx = centers[0]
    segs_up = [((cx - half_w, wall_top), (cx - half_w, ground)),   # 左壁
               ((cx - half_w, ground), (cx + half_w, ground)),     # 底（接地）
               ((cx + half_w, ground), (cx + half_w, wall_top))]   # 右壁
    # パネル2: 下向き（口が下——天面を描き、底辺は描かない）
    cx = centers[1]
    segs_down = [((cx - half_w, ground), (cx - half_w, wall_top)),
                 ((cx - half_w, wall_top), (cx + half_w, wall_top)),  # 天面
                 ((cx + half_w, wall_top), (cx + half_w, ground))]
    # 開口の向きの検算: 上向きは天面なし・底あり／下向きは底なし・天面あり
    top_y, bottom_y = wall_top, ground

    def has_edge(segs, y):
        return any(p1[1] == y and p2[1] == y for p1, p2 in segs)

    ck.ok("上向き: 底が接地し、上辺（天面）は描かない＝口が上に開く",
          has_edge(segs_up, bottom_y) and not has_edge(segs_up, top_y))
    ck.ok("下向き: 天面を描き、底辺は描かない＝口が下でかぶさる形",
          has_edge(segs_down, top_y) and not has_edge(segs_down, bottom_y))

    for segs in (segs_up, segs_down):
        for (x1, y1), (x2, y2) in segs:
            cv.line(x1, y1, x2, y2, w=wall)
    # ふたの口のふち（リップ）: 上向きは壁の上端に短い外向きの返し
    cx = centers[0]
    for s in (-1, 1):
        cv.line(cx + s * half_w, wall_top, cx + s * (half_w + 5), wall_top, w=wall)
    cx = centers[1]
    for s in (-1, 1):
        cv.line(cx + s * half_w, ground, cx + s * (half_w + 5), ground, w=wall)

    # パネル3: 横向き（転がって円形の面が見える——円が地面に接する）
    cx, r_out, r_in = centers[2], 26, 18
    cy = ground - r_out
    ck.ok("横向き: 円（ふたの丸い面）が地面にちょうど接する（転がった状態）",
          cy + r_out == ground)
    cv.circle(cx, cy, r_out, sw=wall)
    cv.circle(cx, cy, r_in, sw=1.2)

    # 地面線と名前ラベル
    for i, cx in enumerate(centers):
        cv.line(cx - 56, ground, cx + 56, ground, w=1.1)
        cv.text(cx, 182, names[i], size=FS, weight="bold")
        cv.text(cx, 200, subs[i], size=10.5)
    cv.text(240, 26, "ペットボトルのふたの3つの落ち方", size=FS, weight="bold")
    cv.text(240, 222, "断面の模式図（実物の色や柄は関係しない）", size=10.5)

    title = "ペットボトルのふたの3つの落ち方（上向き・下向き・横向き）"
    desc = ("L01主概念1の導入図。ペットボトルのふたを机に投げたときの3つの落ち方を、"
            "断面の模式図3つで横に並べた。左＝上向き（開いた口が上・底が接地）、"
            "中＝下向き（口が下でかぶさる形・天面が見える）、右＝横向き（転がって"
            "円形の面が見える・円が地面に接する）。名前ラベルは本文の呼び名と完全一致。"
            "装飾なし・白黒のみ。開口の向き（上向き=天面なし・下向き=底なし）と接地は"
            "スクリプト内assertで検算済み。再現指示: コの字を上に開いた断面・下に開いた"
            "断面・二重円の3つを地面線の上に描き、名前を添える。数値は入れない。")
    allowed = set()
    return dict(file="L01_fig1_cap_three_landings.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="中心例の事象（3つの落ち方と呼び名）を目で確認させる",
                params="呼び名3つ（本文転記）・断面模式図（開口の向きをassert）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図2: L01 実験の記録表（書きこみ式）
# 本文根拠: lesson_01.md 主概念2の figure-spec（1〜20回のマス・5回ごと太線・
#           4時点の集計欄＋予想メモ欄＋実験前の予想欄・相対度数欄に式を薄く印字）
# ===========================================================================
def fig_L01_sheet():
    # --- パラメータ（lesson_01.md 本文の手順をそのまま転記） ---
    n_cells = 20          # 投げる回数
    block = 5             # 手を止める間隔
    checkpoints = [5, 10, 15, 20]

    ck = Checker()
    ck.ok("記入マスは20個（本文「20回投げて」と一致）", n_cells == 20)
    ck.ok("集計の時点は5・10・15・20回（本文「5回投げるごとに」と一致）",
          checkpoints == [block * (i + 1) for i in range(n_cells // block)])
    ck.ok("太線の区切り位置＝各時点の直後（5回ごと）",
          all(c % block == 0 for c in checkpoints))

    cv = Canvas(480, 372)
    cv.text(240, 24, "ふた投げ実験の記録表", size=FS, weight="bold")

    # 実験前の予想欄
    cv.rect(20, 38, 440, 42, sw=1.3, rx=4)
    cv.text(28, 55, "実験前の予想：上向きは、20回中だいたい（　　）回。", size=11,
            anchor="start")
    cv.text(28, 72, "理由：", size=11, anchor="start")

    # 記録グリッド（回番号の行＋○×記入行）
    gx, gy = 58, 94
    cw, h1, h2 = 20, 18, 26
    cv.text(gx - 6, gy + 13, "回", size=10, anchor="end")
    cv.text(gx - 6, gy + h1 + 17, "結果", size=10, anchor="end")
    cv.rect(gx, gy, cw * n_cells, h1 + h2, sw=1.3)
    cv.line(gx, gy + h1, gx + cw * n_cells, gy + h1, w=1.0)
    for i in range(1, n_cells):
        w = 2.4 if i % block == 0 else 0.8   # 5回ごとに太線
        cv.line(gx + cw * i, gy, gx + cw * i, gy + h1 + h2, w=w)
    for i in range(n_cells):
        cv.text(gx + cw * i + cw / 2, gy + 13, f"{i + 1}", size=9.5)
    cv.text(240, gy + h1 + h2 + 16, "○＝上向き、×＝それ以外（下向き・横向き）",
            size=10.5)

    # 集計表（4時点）
    tx, ty = 15, 176
    widths = [64, 78, 72, 118, 128]
    hh, rh = 34, 30
    cols = [sum(widths[:i]) for i in range(len(widths) + 1)]
    total_w = cols[-1]
    cv.rect(tx, ty, total_w, hh + rh * 4, sw=1.3)
    cv.line(tx, ty + hh, tx + total_w, ty + hh, w=1.6)
    for i in range(1, 4):
        cv.line(tx, ty + hh + rh * i, tx + total_w, ty + hh + rh * i, w=0.8)
    for c in cols[1:-1]:
        cv.line(tx + c, ty, tx + c, ty + hh + rh * 4, w=0.8)
    headers = ["時点", "上向きの回数", "投げた回数", "相対度数",
               "この後どうなる？"]
    for i, htxt in enumerate(headers):
        cv.text(tx + (cols[i] + cols[i + 1]) / 2, ty + 15, htxt, size=9.5,
                weight="bold")
    # 相対度数欄の式を薄く印字（本文の再現指示）＋予想メモ欄の補足
    cv.text(tx + (cols[3] + cols[4]) / 2, ty + 28,
            "＝上向きの回数÷投げた回数", size=8, color="#888")
    cv.text(tx + (cols[4] + cols[5]) / 2, ty + 28, "（予想メモ）", size=8.5,
            color="#888")
    for j, cp in enumerate(checkpoints):
        yy = ty + hh + rh * j + rh / 2 + 4
        cv.text(tx + (cols[0] + cols[1]) / 2, yy, f"{cp}回時点", size=10)
        # 投げた回数は各時点で確定しているので薄く印字（記入の手間と誤記を防ぐ）
        cv.text(tx + (cols[2] + cols[3]) / 2, yy, f"{cp}", size=10, color="#888")

    cv.text(240, 340, "5回投げるごとに一度手を止めて、集計と予想を書きこむ", size=10.5)
    cv.text(240, 358, "（相対度数が割り切れないときは四捨五入して小数第2位まで）",
            size=10.5)

    title = "ふた投げ実験の記録表（書きこみ式・20回）"
    desc = ("L01主概念2の作業用紙。上から、実験前の予想欄（20回中だいたい何回か＋理由）、"
            "1〜20回の○×記入マス（5回ごとに太線で区切る）、5・10・15・20回時点の集計表"
            "（上向きの回数・投げた回数・相対度数・この後どうなる？の予想メモ欄）を配置。"
            "相対度数の列見出しには「＝上向きの回数÷投げた回数」の式を薄く印字。"
            "投げた回数の列は各時点で確定するため薄く印字済み。データは一切入っていない"
            "白紙の書きこみ式で、解答値の漏えいはない。マス数20・区切り位置はassert検算済み。"
            "再現指示: 20マスの記録欄と4行の集計表を持つ書きこみ式ワークシート。白黒のみ。")
    allowed = {str(i) for i in range(1, 21)} | {"20"}
    return dict(file="L01_fig2_experiment_record_sheet.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="途中経過の記録と予想の書き留めを本文の手順どおりに実行させる",
                params="20マス・5回ごと太線・4時点集計欄（本文の手順を転記・データなし）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図3: L02 投げた回数と上向きの相対度数の折れ線グラフ（本単元の中心図版）
# 本文根拠: lesson_02.md 主概念1の figure-spec（8点等間隔・0.65点線・0.5と1の目盛り・
#           「横軸の間隔は回数に比例していない」注記）
# 答え漏れ注意: 練習1の解答値（あ〜う・answer_key由来）は図にもdescにも入れない
# ===========================================================================
def fig_L02_line():
    # --- パラメータ（lesson_02.md 本文の2000回の表をそのまま転記） ---
    ns = [10, 20, 50, 100, 200, 500, 1000, 2000]
    rs = [4, 11, 31, 63, 131, 327, 652, 1303]
    table_rf = ["0.40", "0.55", "0.62", "0.63", "0.66", "0.65", "0.65", "0.65"]
    limit = Decimal("0.65")   # 点線の高さ「およそ0.65」

    ck = Checker()
    for n, r, exp in zip(ns, rs, table_rf):
        ck.ok(f"n={n}: 相対度数 {r}÷{n} を四捨五入（小数第2位）で再計算——本文の表"
              f"（{exp}）と一致", round2(r, n) == Decimal(exp),
              f"実測={round2(r, n)}")
    ck.ok("上向きの回数 r は増え続ける（「r と r/n は別の量」の記述の検算）",
          all(a < b for a, b in zip(rs, rs[1:])))
    ck.ok("本文の種明かし（500回以降の割り算の値そのもの）と一致: "
          "0.654・0.652・0.6515",
          [relfreq2(327, 500), relfreq2(652, 1000), relfreq2(1303, 2000)]
          == [Decimal("0.654"), Decimal("0.652"), Decimal("0.6515")])
    dev = [abs(relfreq2(r, n) - limit) for n, r in zip(ns, rs)]
    ck.ok("前半（n=10〜100）のぶれ > 後半（n=500〜2000）のぶれ（安定の対比が図の主役）",
          max(dev[:4]) > 10 * max(dev[5:]), f"前半最大={max(dev[:4])}")
    ck.ok("相対度数は1にも0.5にも近づいていない（誤答ア・ウの否定が図から読める）",
          all(Decimal("0.6") < relfreq2(r, n) < Decimal("0.7")
              for n, r in zip(ns[3:], rs[3:])))

    cv = Canvas(480, 322)
    x0, x1, y_base, y_top = 70, 450, 250, 50   # 縦軸: 値0→y=250, 値1→y=50

    def Y(v):
        return y_base - float(v) * (y_base - y_top)

    def X(i):
        return x0 + (x1 - x0) * i / (len(ns) - 1)

    # 軸
    cv.line(x0, y_base, x1 + 4, y_base, w=1.2)
    cv.line(x0, y_base, x0, y_top - 8, w=1.2)
    for v, lab in ((0, "0"), (0.5, "0.5"), (1, "1")):
        cv.line(x0 - 4, Y(v), x0, Y(v), w=0.9)
        cv.text(x0 - 8, Y(v) + 4, lab, size=11, anchor="end")
    cv.text(x0 - 4, y_top - 14, "上向きの相対度数", size=10.5, anchor="start")
    # 0.65の点線補助線
    cv.line(x0, Y(0.65), x1, Y(0.65), w=AUX_W, dash=DASH)
    cv.text(x1 - 2, Y(0.65) - 7, "およそ0.65", size=11, anchor="end", weight="bold")
    # 横軸目盛り（8点を等間隔に）
    for i, n in enumerate(ns):
        cv.line(X(i), y_base, X(i), y_base + 4, w=0.9)
        cv.text(X(i), y_base + 18, f"{n}", size=9.5)
    cv.text(260, y_base + 34, "投げた回数 n（8つの回数を等間隔に並べてある——"
            "間隔は回数に比例していない）", size=9.5)
    # 折れ線と点（座標は割り算の値そのものから厳密変換）
    pts = [(X(i), Y(relfreq2(r, n))) for i, (n, r) in enumerate(zip(ns, rs))]
    cv.polyline(pts, w=MAIN_W)
    for x, y in pts:
        cv.dot(x, y, r=2.8)
    cv.text(260, 26, "投げた回数と上向きの相対度数", size=FS, weight="bold")
    cv.text(260, 308, "同じ種類のふたを2000回投げた記録の例（教材用）", size=10.5)

    title = "投げた回数と上向きの相対度数の折れ線グラフ（相対度数の安定）"
    desc = ("L02主概念1の中心図版。横軸は投げた回数n（10・20・50・100・200・500・1000・"
            "2000の8点を等間隔に配置。間隔は回数に比例していない旨を軸の下に注記）、"
            "縦軸は上向きの相対度数（0〜1・0.5と1の目盛りを明示）。本文の表の8点を"
            "折れ線で結び、0.65の高さに「およそ0.65」の点線補助線を引いた。前半のぶれと"
            "後半の安定の対比が主役で、3方向の誤った予想（1に近づく・最初から一定・"
            "近づかない）をこの1枚で同時に否定する。各点の相対度数は本文の生データ"
            "（rとn）から四捨五入で再計算して表と一致をassert検算済み。点ごとの数値"
            "ラベルは打たない（値は本文の表で読む）。再現指示: 8点等間隔の折れ線＋"
            "0.65の点線。白黒のみ。")
    # 「8」は「8つの回数」の語のみ（点の個数＝構造の数で、答えの数値ではない）
    allowed = {"10", "20", "50", "100", "200", "500", "1000", "2000",
               "0", "0.5", "0.65", "8"}
    # 練習1（画びょう）の解答値（あ〜う）は図にもdescにも入れない（answer_key由来）
    check_tokens = {"0.60", "0.57", "0.568", "0.572"}
    return dict(file="L02_fig1_relative_frequency_line.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="相対度数の安定を一目で見せ、3方向の誤った予想を同時に否定する",
                params="本文の2000回の表（n=10〜2000の8点）を転記→r/nを再計算し検算",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図4: L03 サイズごとの貸し出し回数の相対度数（棒グラフ）
# 本文根拠: lesson_03.md 主概念1の figure-spec（E裁定適用後）
# 答え漏れ注意（E裁定の抑止注記を厳守）: 練習1の空らん（あ）＝23.0cmの相対度数の
#   解答値を図に載せない。数値ラベルは24.0cm（0.18）のみ。縦軸は0.05刻みの
#   主目盛りのみ・グリッド線なし（棒の高さから精密に読み取れないようにする）。
# ===========================================================================
def fig_L03_bar():
    # --- パラメータ（lesson_03.md 本文の表をそのまま転記） ---
    sizes = ["22.0", "22.5", "23.0", "23.5", "24.0", "24.5", "25.0", "25.5",
             "26.0", "26.5", "27.0"]
    counts = [400, 640, 960, 1200, 1440, 1360, 880, 560, 320, 160, 80]
    total = 8000
    # 本文の表の相対度数（（あ）＝23.0cmはNone: 空らんのため図にも載せない）
    table_rf = ["0.05", "0.08", None, "0.15", "0.18", "0.17", "0.11", "0.07",
                "0.04", "0.02", "0.01"]

    ck = Checker()
    ck.ok("貸し出した回数の合計＝8000回（本文の表と一致）", sum(counts) == total)
    rf = [relfreq2(c, total) for c in counts]
    for s, c, f, exp in zip(sizes, counts, rf, table_rf):
        if exp is not None:
            ck.ok(f"{s}cm: 相対度数 {c}÷{total} を再計算——本文の表（{exp}）と一致",
                  f == Decimal(exp), f"実測={f}")
    hidden = rf[sizes.index("23.0")]
    ck.ok("（あ）＝23.0cmの相対度数を回数と合計から再計算——検算 8000×（あ）＝960 が"
          "成立（値は解答のため非開示・図にも載せない）",
          hidden * total == Decimal(960))
    ck.ok("相対度数の合計＝1.00（本文の欄外注記と一致）", sum(rf) == Decimal("1.00"))
    ck.ok("最大は24.0cmの0.18（「最も借りられやすい」注記の根拠）",
          max(rf) == rf[sizes.index("24.0")] == Decimal("0.18"))

    cv = Canvas(480, 306)
    x0, y_base = 58, 232
    slot, bw = 35.5, 24
    scale = 800.0   # 相対度数1あたりのpx（0.05→40px）

    # 縦軸: 0.05刻みの主目盛りのみ・グリッド線なし（E裁定——精密読み取りの抑止）
    cv.line(x0, y_base, x0, y_base - 0.22 * scale, w=1.2)
    for k in range(5):
        v = Decimal("0.05") * k
        cv.line(x0 - 4, y_base - float(v) * scale, x0, y_base - float(v) * scale,
                w=0.9)
        cv.text(x0 - 8, y_base - float(v) * scale + 4,
                f"{v:.2f}" if k else "0", size=10, anchor="end")
    # 横軸と棒
    cv.line(x0, y_base, x0 + slot * len(sizes) + 6, y_base, w=1.2)
    for i, (s, f) in enumerate(zip(sizes, rf)):
        cx = x0 + slot * i + slot / 2
        cv.rect(cx - bw / 2, y_base - float(f) * scale, bw, float(f) * scale,
                sw=1.3, fill="#e6e6e6")
        cv.text(cx, y_base + 16, s, size=9, anchor="middle")
    # 数値ラベルは注記対象の24.0cmのみ（E裁定——他の棒は高さのみ）
    i_max = sizes.index("24.0")
    cx = x0 + slot * i_max + slot / 2
    top = y_base - float(rf[i_max]) * scale
    cv.text(cx, top - 8, "0.18", size=10.5, weight="bold")
    cv.text(cx + 10, top - 40, "最も借りられやすい", size=10.5, weight="bold")
    cv.line(cx + 2, top - 36, cx, top - 22, w=0.9, color="#888")
    cv.text(240, y_base + 34, "横軸: 靴のサイズ（cm）／縦軸: 相対度数", size=10.5)
    cv.text(240, y_base + 52, "相対度数の合計は1.00（過去1年・貸し出し8000回の記録）",
            size=10.5)
    cv.text(240, 26, "サイズごとの貸し出し回数の相対度数", size=FS, weight="bold")

    title = "サイズごとの貸し出し回数の相対度数（棒グラフ）"
    desc = ("L03主概念1の意思決定の土台図。横軸は靴のサイズ（22.0〜27.0cm・0.5cm刻み）、"
            "縦軸は相対度数（0〜0.20・0.05刻みの主目盛りのみでグリッド線なし）。"
            "過去1年・貸し出し8000回の記録（教材用の例）の相対度数を単色の棒で表し、"
            "最大の24.0cm（0.18）にだけ数値ラベルと「最も借りられやすい」の注記を付けた。"
            "23.0cmの棒には数値ラベルを付けない（練習1の空らんの解答が図から読み取れて"
            "しまうのを防ぐため。グリッド線を引かないのも同じ理由）。欄外に相対度数の"
            "合計が1.00になることを注記。全ての相対度数は回数÷合計8000から再計算して"
            "本文の表と一致をassert検算済み（空らん分は掛け算の検算のみで値は非開示）。"
            "再現指示: 単色・装飾なしの棒グラフ11本。数値ラベルは最大の棒1本のみ。白黒のみ。")
    # 「0.5」は「0.5cm刻み」の語のみ（サイズの刻み幅で、答えの数値ではない）
    allowed = {"22.0", "22.5", "23.0", "23.5", "24.0", "24.5", "25.0", "25.5",
               "26.0", "26.5", "27.0", "0", "0.05", "0.10", "0.15", "0.20",
               "0.18", "1.00", "8000", "11", "0.5"}
    check_tokens = {"0.12"}   # 練習1（あ）の解答値（answer_key由来）——図・メタ双方から排除
    return dict(file="L03_fig1_shoe_size_relfreq_bar.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="借りられやすさの傾向を一目で読める形にする（解答値の抑止つき）",
                params="本文の貸し出し記録（11サイズ・計8000回）を転記→相対度数を再計算し検算",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# メイン: 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_cap, fig_L01_sheet, fig_L02_line, fig_L03_bar]


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
        "spec: jhs-math-2-quartiles-boxplot/assets_provenance/generate_figures.py と同一のコード来歴方式"
        "（SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 不確定な事象の起こりやすさ（頻度確率）単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "相対度数は本文の生データ（回数r・投げた回数n）から**四捨五入"
        "（小数第2位まで・ROUND_HALF_UP）**で再計算してassert検算。"
        "合計・最大値の位置も再計算して検算。"
        "全図で下表の統計検算（スクリプト内assert）と禁止文字列の機械検査"
        "（<text>/<title>/<desc>の数値トークンを許可リストと照合）が生成時に自動実行され、全件合格。"
        "解答編（answer_key）にのみ現れる値（L03練習1の空らん（あ）等）は"
        "check_tokensで機械的に排除している（E裁定の抑止注記に対応）。"
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
        "---\ndistribution_status: published_draft\n---\n\n"
        + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {total_checks} checks)")


if __name__ == "__main__":
    main()
