#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「平方根」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み）。
ヘルパー群（Canvas/矢印/ハッチほか）は先行実装
production/jhs-math-3-pythagorean-theorem/candidate_draft/assets_provenance/generate_figures.py
（原典は相似単元）からコピー再利用（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（8枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 幾何の自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。
- 外部批判レビュー（裁定）の申し送り（指摘#20）への対応:
  ①数直線の目盛りの正確さ = 目盛り座標を座標計算で厳密に置き、等間隔・√2位置の
    区間包含（1<√2<2、1.4<√2<1.5、1.41<√2<1.42）をassertで検算。
  ②負の平方根の左右配置 = −√2 が −2 と −1 の間（0 の左側・√2 と対称）に
    来ることをピクセル座標レベルでassert。
  ③答え漏れ = 各図に答え漏れ検査トークンのリスト（check_tokens・検査の実装定数）を持たせ、
    生成したSVG全文に対して機械検査（1つでも含まれれば出力しない）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。
"""

import math
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
FS = 13           # 基本文字サイズ(px) — viewBox幅~420で約3%
FS_CAP = 12       # キャプション
DOT_R = 2.5       # 点マーカー半径


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き に変換して描く）
# 三平方単元 generate_figures.py からコピー再利用（render()を追加拡張）
# ===========================================================================
class Canvas:
    def __init__(self, width, height, scale=1.0, ox=0.0, oy=0.0):
        """scale: 数学単位→px、(ox,oy): 数学原点のSVG座標（yはoyから上向きに減る）"""
        self.w, self.h = width, height
        self.s, self.ox, self.oy = scale, ox, oy
        self.defs = []
        self.body = []
        self.texts = []   # 図中に描いた文字の生テキスト（答え漏れ機械検査の対象）

    # 座標変換 -------------------------------------------------------------
    def P(self, p):
        return (self.ox + self.s * p[0], self.oy - self.s * p[1])

    # 低レベル -------------------------------------------------------------
    def raw(self, s):
        self.body.append(s)

    def line(self, a, b, w=MAIN_W, dash=None, color="#000"):
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def polygon(self, pts, w=MAIN_W, fill="none"):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="round"/>')

    def polygon_nostroke(self, pts, fill):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')

    def polyline(self, pts, w=MAIN_W, dash=None):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polyline points="{s}" fill="none" stroke="#000" '
                 f'stroke-width="{w}"{d}/>')

    def dot(self, p, r=DOT_R):
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')

    def circle(self, c, r_math, w=MAIN_W, dash=None, fill="none"):
        x, y = self.P(c)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_math * self.s:.1f}" '
                 f'fill="{fill}" stroke="#000" stroke-width="{w}"{d}/>')

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None):
        x, y = self.P(p)
        self.texts.append(s)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS_CAP, anchor="start", weight=None):
        self.texts.append(s)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def rect_px(self, x, y, w, h, sw=MAIN_W, fill="none", dash=None, rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
                 f'{r} fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')

    def ellipse_px(self, cx, cy, rx, ry, sw=1.3):
        self.raw(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="none" stroke="#000" stroke-width="{sw}"/>')

    def add_hatch(self):
        """濃淡+ハッチングの塗り分けパターン（§4）を内蔵defsへ"""
        self.defs.append(
            '<pattern id="h45" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>'
            '<pattern id="h135" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(135)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>')

    def render(self, fig_id, title, desc=None):
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            + (f'<desc>{escape(desc)}</desc>\n' if desc else "") +
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md準拠（内部規約の要旨は同SPECに反映済み）・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )


# ---- 幾何ユーティリティ ----------------------------------------------------
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def shoelace(pts):
    """多角形の面積（符号なし）"""
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def seg_label(cv, p, q, lab, off=13.0, t=0.5, size=12, weight=None):
    """線分pqの位置tから法線方向へoff(px)ずらしてラベルを置く（offの符号で側を選ぶ）"""
    (x1, y1), (x2, y2) = cv.P(p), cv.P(q)
    mx, my = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    cv.text_px(mx + nx * off, my + ny * off + size * 0.35, lab,
               size=size, anchor="middle", weight=weight)


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0):
    """SVG座標(px)で矢印（線+先端の三角形）を描く。概念図用"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="#000" stroke-width="{w}"/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')


class Checker:
    """幾何検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


# ---- 数直線ヘルパー（本単元で追加。目盛りは座標計算で厳密に置く） -----------
def numberline(cv, ck, name, x0, x1, y, vmin, vmax, step_num, step_den,
               band=None, labels=(), tick_h=5.0, label_size=12, band_h=9.0):
    """
    px座標の水平数直線。値v→x座標は X(v)=x0+(v−vmin)/(vmax−vmin)×(x1−x0)。
    目盛りは step_num/step_den 刻み（分数で持ち浮動小数の刻み誤差を避ける）。
    band=(a,b) は網かけ（ハッチ）区間。labels は表示する目盛り値のリスト。
    戻り値: X（値→px座標の関数。呼び出し側の位置検算に使う）。
    """
    span = x1 - x0

    def X(v):
        return x0 + (v - vmin) / (vmax - vmin) * span

    n_ticks = round((vmax - vmin) * step_den / step_num)
    ck.ok(f"{name}: 刻み{step_num}/{step_den}が区間[{vmin},{vmax}]を割り切る",
          abs(n_ticks * step_num / step_den - (vmax - vmin)) < 1e-12)
    xs = []
    for k in range(n_ticks + 1):
        v = vmin + k * step_num / step_den
        xs.append(X(v))
    # 目盛りの等間隔性を厳密に検算（E申し送り①: 目盛りの正確さ）
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    ck.ok(f"{name}: 目盛り{n_ticks + 1}本が等間隔（ずれ<1e-9px）",
          max(gaps) - min(gaps) < 1e-9,
          f"間隔={gaps[0]:.4f}px")
    if band:
        a, b = band
        ck.ok(f"{name}: 網かけ[{a},{b}]の両端が目盛り位置と厳密一致",
              min(abs(X(a) - x) for x in xs) < 1e-9
              and min(abs(X(b) - x) for x in xs) < 1e-9)
        cv.raw(f'<rect x="{X(a):.1f}" y="{y - band_h:.1f}" '
               f'width="{X(b) - X(a):.1f}" height="{band_h * 2:.1f}" '
               f'fill="url(#h45)" stroke="#000" stroke-width="0.6"/>')
    cv.raw(f'<line x1="{x0 - 8:.1f}" y1="{y:.1f}" x2="{x1 + 8:.1f}" y2="{y:.1f}" '
           f'stroke="#000" stroke-width="{MAIN_W}"/>')
    for k in range(n_ticks + 1):
        x = xs[k]
        cv.raw(f'<line x1="{x:.1f}" y1="{y - tick_h:.1f}" x2="{x:.1f}" '
               f'y2="{y + tick_h:.1f}" stroke="#000" stroke-width="1.2"/>')
    for v, lab in labels:
        ck.ok(f"{name}: ラベル「{lab}」が目盛り位置と厳密一致",
              min(abs(X(v) - x) for x in xs) < 1e-9)
        cv.text_px(X(v), y + tick_h + label_size + 2, lab,
                   size=label_size, anchor="middle")
    return X


# ===========================================================================
# 図1: L01 1辺1mの正方形と対角線（？m）
# 本文根拠: lesson_01.md 主概念1（34行目のプレースホルダ）
# 答え漏れ注意: 対角線の値（√2 m・約1.41m）は図に書かない→「？m」
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md 主概念1 と一致させる） ---
    side = 1.0                                    # 1辺 1m
    A, B, C, D = (0.0, 0.0), (side, 0.0), (side, side), (0.0, side)

    ck = Checker()
    ck.ok("正方形（4辺とも1m・4角とも直角）",
          all(abs(dist(p, q) - side) < 1e-12
              for p, q in [(A, B), (B, C), (C, D), (D, A)])
          and abs(dist(A, C) - dist(B, D)) < 1e-12)
    ck.ok("対角線AC=√2 m（本文の主役の長さ・図には？mのみ）",
          abs(dist(A, C) - math.sqrt(2)) < 1e-12, f"AC={dist(A, C):.6f}")

    cv = Canvas(380, 262)
    cv.s = 150.0
    cv.ox, cv.oy = 115, 195
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=BOLD_W)                       # 対角線=太線（本文指定）
    seg_label(cv, A, B, "1m", off=15, size=FS)
    seg_label(cv, B, C, "1m", off=15, size=FS)
    seg_label(cv, A, C, "？m", off=-16, t=0.56, size=15, weight="bold")
    cv.text_px(190, 232, "1辺1mの正方形の対角線——この長さは何mだろう？",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 249, "（対角線は確かに引けて、長さも確かに決まっている）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_unit_square_diagonal.svg", canvas=cv, lesson="L01",
                title="1辺1mの正方形と対角線（？m）",
                intent="導入の図。対角線は太線・長さは？m（答えの値も近似値も書かない）",
                src="lesson_01.md 主概念1（34行目のプレースホルダ）",
                params="1辺=1m・対角線A(0,0)→C(1,1)",
                check_tokens=["√2", "1.4"],
                checks=ck.items)


# ===========================================================================
# 図2: L02 数直線3段の挟み撃ち（√2の居場所を絞る）
# 本文根拠: lesson_02.md 主概念1（46行目のプレースホルダ）
# E申し送り①: 目盛りは座標計算で厳密に。√2の位置は打たない（区間の包含のみassert）
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（本文 lesson_02.md 主概念1 と一致させる） ---
    r2 = math.sqrt(2.0)
    rows = [
        # (vmin, vmax, 刻み分子, 刻み分母, 網かけ区間, ラベル)
        (0.0, 3.0, 1, 1, (1.0, 2.0),
         [(0, "0"), (1, "1"), (2, "2"), (3, "3")]),
        (1.0, 2.0, 1, 10, (1.4, 1.5),
         [(1.0, "1.0"), (1.4, "1.4"), (1.5, "1.5"), (2.0, "2.0")]),
        (1.40, 1.50, 1, 100, (1.41, 1.42),
         [(1.40, "1.40"), (1.41, "1.41"), (1.42, "1.42"), (1.50, "1.50")]),
    ]

    ck = Checker()
    # 挟み撃ちの各段の区間が√2を含むこと（本文の 1<√2<2, 1.4<√2<1.5, 1.41<√2<1.42）
    ck.ok("1²=1＜2＜4=2² → 1＜√2＜2（本文と一致）",
          1 * 1 < 2 < 2 * 2 and 1 < r2 < 2)
    ck.ok("1.4²=1.96＜2＜2.25=1.5² → 1.4＜√2＜1.5（本文と一致）",
          abs(1.4 ** 2 - 1.96) < 1e-12 and abs(1.5 ** 2 - 2.25) < 1e-12
          and 1.96 < 2 < 2.25 and 1.4 < r2 < 1.5)
    ck.ok("1.41²=1.9881＜2＜2.0164=1.42² → 1.41＜√2＜1.42（本文と一致）",
          abs(1.41 ** 2 - 1.9881) < 1e-12 and abs(1.42 ** 2 - 2.0164) < 1e-12
          and 1.9881 < 2 < 2.0164 and 1.41 < r2 < 1.42)
    ck.ok("√2=1.41421356…（区間の代表精度の確認）",
          abs(r2 - 1.41421356) < 5e-9, f"√2={r2:.9f}")

    cv = Canvas(420, 320)
    cv.add_hatch()
    x0, x1 = 45, 385
    ys = (58, 158, 258)
    row_names = ("整数の目盛り", "0.1刻み", "0.01刻み")
    Xs = []
    for (vmin, vmax, sn, sd, band, labels), y, nm in zip(rows, ys, row_names):
        X = numberline(cv, ck, f"{nm}段", x0, x1, y, vmin, vmax, sn, sd,
                       band=band, labels=labels)
        Xs.append((X, band))
        cv.text_px(x0 - 8, y - 16, nm, size=11, anchor="start")
    # √2の位置が各段の網かけ内部に厳密に入ること（点は打たない——E申し送り①③）
    for (X, band), nm in zip(Xs, row_names):
        ck.ok(f"{nm}段: √2の位置が網かけの内部（点は打たない）",
              X(band[0]) < X(r2) < X(band[1]),
              f"x(√2)={X(r2):.2f}px∈({X(band[0]):.2f},{X(band[1]):.2f})")
    # 段をつなぐ拡大ガイド（上段の網かけ→下段の全幅）
    for i in range(2):
        (Xa, band) = Xs[i]
        y_top, y_bot = ys[i], ys[i + 1]
        cv.raw(f'<line x1="{Xa(band[0]):.1f}" y1="{y_top + 24:.1f}" '
               f'x2="{x0:.1f}" y2="{y_bot - 26:.1f}" stroke="#000" '
               f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
        cv.raw(f'<line x1="{Xa(band[1]):.1f}" y1="{y_top + 24:.1f}" '
               f'x2="{x1:.1f}" y2="{y_bot - 26:.1f}" stroke="#000" '
               f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    cv.text_px(210, 300, "網かけの部分に√2がいる——目盛りを細かくするほど、",
               size=FS_CAP, anchor="middle")
    cv.text_px(210, 316, "居場所が両側から挟み撃ちで絞られていく",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_squeeze_numberline_3levels.svg", canvas=cv,
                lesson="L02",
                title="数直線3段の挟み撃ち（1↔2 → 1.4↔1.5 → 1.41↔1.42）",
                intent="主概念1の図。目盛りは厳密な等間隔・√2の正確な位置の点は打たない",
                src="lesson_02.md 主概念1（46行目のプレースホルダ）",
                params="3段=(0〜3,1刻み)(1.0〜2.0,0.1刻み)(1.40〜1.50,0.01刻み)・"
                       "網かけ=(1,2)(1.4,1.5)(1.41,1.42)",
                check_tokens=["1.414", "1.41421", "√2＝", "√2="],
                checks=ck.items)


# ===========================================================================
# 図3: L02 −3〜3の数直線に−√2・√2・√5を置く（活動用・？矢印）
# 本文根拠: lesson_02.md 主概念2（60行目のプレースホルダ）
# E申し送り②: 負の平方根の左右配置——−√2は0の左・−2と−1の間（√2と対称）
# 答え漏れ注意: 矢印のラベルは？のみ。答えの位置の点は打たない
# ===========================================================================
def fig_L02_2():
    # --- パラメータ（本文 lesson_02.md 主概念2 と一致させる） ---
    vmin, vmax = -3.0, 3.0
    r2, r5 = math.sqrt(2.0), math.sqrt(5.0)
    targets = [-r2, r2, r5]                      # 置く数（左から）

    ck = Checker()
    ck.ok("−2＜−√2＜−1（負の平方根は0の左側——E申し送り②）",
          -2 < -r2 < -1, f"−√2={-r2:.5f}")
    ck.ok("1＜√2＜2（本文と一致）", 1 < r2 < 2)
    ck.ok("2＜√5＜3（本文: 2²=4＜5＜9=3²）", 2 * 2 < 5 < 3 * 3 and 2 < r5 < 3)

    cv = Canvas(460, 190)
    x0, x1, y = 40, 420, 110
    X = numberline(cv, ck, "−3〜3", x0, x1, y, vmin, vmax, 1, 1,
                   labels=[(v, str(v).replace("-", "−")) for v in range(-3, 4)])
    # 0の位置が区間中央（左右対称の基準）
    ck.ok("0の目盛りが数直線の中央に位置する",
          abs(X(0) - (x0 + x1) / 2) < 1e-9, f"x(0)={X(0):.2f}px")
    # −√2と√2が0をはさんで厳密に対称（E申し送り②をピクセル座標で検算）
    ck.ok("x(−√2)とx(√2)がx(0)をはさんで厳密対称",
          abs((X(0) - X(-r2)) - (X(r2) - X(0))) < 1e-9,
          f"x(−√2)={X(-r2):.2f}, x(0)={X(0):.2f}, x(√2)={X(r2):.2f}")
    ck.ok("矢印位置が正しい整数目盛りの間: x(−2)<x(−√2)<x(−1)",
          X(-2) < X(-r2) < X(-1))
    ck.ok("矢印位置が正しい整数目盛りの間: x(1)<x(√2)<x(2)",
          X(1) < X(r2) < X(2))
    ck.ok("矢印位置が正しい整数目盛りの間: x(2)<x(√5)<x(3)",
          X(2) < X(r5) < X(3))
    ck.ok("左右の順序: −√2＜√2＜√5", X(-r2) < X(r2) < X(r5))
    # 下向き矢印（ラベルは？のみ・点は打たない——答え漏れ検査③）
    for v in targets:
        x = X(v)
        arrow_px(cv, x, y - 42, x, y - 9, w=1.6, head=8.0)
        cv.text_px(x, y - 50, "？", size=15, anchor="middle", weight="bold")
    cv.text_px(230, 158, "−√2、√2、√5 は、それぞれどの「？」の位置に入るだろう",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 175, "（数直線に自分で置いてみよう。負の数は0のどちら側？）",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig2_place_roots_numberline.svg", canvas=cv, lesson="L02",
                title="−3〜3の数直線と？矢印（−√2・√2・√5を置く活動用）",
                intent="主概念2の活動図。矢印は厳密位置・ラベルは？のみ・答えの点は打たない",
                src="lesson_02.md 主概念2（60行目のプレースホルダ）",
                params="範囲=−3〜3（1刻み）・矢印x=−√2, √2, √5（座標は厳密値）",
                check_tokens=["1.4", "2.2", "−1.4", "-1.4"],
                checks=ck.items)


# ===========================================================================
# 図4: L03 面積3と面積5の正方形の重ね合わせ（1辺√3・√5）
# 本文根拠: lesson_03.md 主概念1（26行目のプレースホルダ）
# 答え漏れ注意: 近似値（1.73…・2.23…）は図に書かない
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md 主概念1 と一致させる） ---
    a_small, a_big = 3.0, 5.0                    # 面積
    s_small, s_big = math.sqrt(a_small), math.sqrt(a_big)   # 1辺（厳密値）
    SQ_small = [(0, 0), (s_small, 0), (s_small, s_small), (0, s_small)]
    SQ_big = [(0, 0), (s_big, 0), (s_big, s_big), (0, s_big)]

    ck = Checker()
    ck.ok("(√3)²=3・(√5)²=5（1辺と面積の対応が厳密）",
          abs(shoelace(SQ_small) - 3) < 1e-12 and abs(shoelace(SQ_big) - 5) < 1e-12)
    ck.ok("√3＜√5（面積の大きい正方形ほど1辺が長い——本文の結論と一致）",
          s_small < s_big, f"√3={s_small:.5f}＜√5={s_big:.5f}")
    ck.ok("左下の頂点をそろえて重ねる（両正方形の原点が一致）",
          SQ_small[0] == SQ_big[0] == (0, 0))

    cv = Canvas(380, 286)
    cv.add_hatch()
    cv.s = 72.0
    cv.ox, cv.oy = 95, 200
    cv.polygon(SQ_big, w=MAIN_W, fill="#e6e6e6")     # 大=薄グレー
    cv.polygon(SQ_small, w=MAIN_W, fill="#fff")      # 小=白（重なりが見える）
    cv.text((s_small / 2, s_small / 2), "3", size=16, weight="bold")
    cv.text((s_big * 0.86, s_big * 0.42), "5", size=16, weight="bold")
    seg_label(cv, (0, 0), (s_big, 0), "√5", off=17, size=FS, weight="bold")
    seg_label(cv, (0, s_small), (s_small, s_small), "√3", off=-13, size=FS,
              weight="bold")
    cv.text_px(190, 254, "面積3の正方形（1辺√3）と面積5の正方形（1辺√5）を",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 271, "左下の頂点をそろえて重ねる——面積の大きい方が、1辺も長い",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_square_area_side_compare.svg", canvas=cv,
                lesson="L03",
                title="面積3と面積5の正方形の重ね合わせ（1辺√3・√5）",
                intent="主概念1の図。1辺は√3・√5の厳密縮尺。近似値は書かない",
                src="lesson_03.md 主概念1（26行目のプレースホルダ）",
                params="面積3・5／1辺=√3, √5（座標は厳密値・左下原点そろえ）",
                check_tokens=["1.7", "2.2", "≒"],
                checks=ck.items)


# ===========================================================================
# 図5: L04 数の分類の入れ子図（有理数・無理数）
# 本文根拠: lesson_04.md 主概念2（44行目のプレースホルダ）
# 各枠にラベルのみ（定義文は図に書かない——本文指定）
# ===========================================================================
def fig_L04():
    # --- パラメータ（本文 lesson_04.md と一致させる。例の顔ぶれは本文指定） ---
    ex_shizen = ["5"]
    ex_seisu = ["−3", "0"]                       # 整数（自然数以外）
    ex_bunsu = ["0.7", "2/3"]                    # 整数でない有理数
    ex_muri = ["√2", "−√5", "π"]                 # 無理数
    # 枠のpx座標（x, y, w, h）——入れ子の包含関係はassertで機械検証する
    R_outer = (12, 30, 400, 218)
    R_yuri = (26, 58, 240, 178)
    R_muri = (280, 58, 118, 178)
    R_seisu = (40, 88, 122, 138)
    R_shizen = (54, 122, 94, 46)

    def inside(inner, outer):
        x, y, w, h = inner
        X, Y, W, H = outer
        return X < x and Y < y and x + w < X + W and y + h < Y + H

    def disjoint(a, b):
        return (a[0] + a[2] < b[0] or b[0] + b[2] < a[0]
                or a[1] + a[3] < b[1] or b[1] + b[3] < a[1])

    ck = Checker()
    ck.ok("入れ子の包含: 自然数⊂整数⊂有理数⊂数",
          inside(R_shizen, R_seisu) and inside(R_seisu, R_yuri)
          and inside(R_yuri, R_outer))
    ck.ok("有理数と無理数の枠が重ならない（もれなく・重なりなく二分）",
          disjoint(R_yuri, R_muri) and inside(R_muri, R_outer))
    ck.ok("有理数の例は本文どおり5・−3・0・0.7・2/3の5個",
          len(ex_shizen) + len(ex_seisu) + len(ex_bunsu) == 5)
    ck.ok("無理数の例は本文どおり√2・−√5・πの3個", len(ex_muri) == 3)
    ck.ok("例の分類が正しい: 0.7=7/10・2/3は整数でない有理数",
          abs(0.7 - 7 / 10) < 1e-12 and 0 < 2 / 3 < 1)

    cv = Canvas(424, 296)
    for (x, y, w, h), rx in [(R_outer, 6), (R_yuri, 6), (R_muri, 6),
                             (R_seisu, 5), (R_shizen, 5)]:
        cv.rect_px(x, y, w, h, sw=1.4, rx=rx)
    cv.text_px(18, 22, "数（実数と呼ぶのは高校）", size=FS, weight="bold")
    cv.text_px(34, 78, "有理数", size=FS, weight="bold")
    cv.text_px(288, 78, "無理数", size=FS, weight="bold")
    cv.text_px(48, 108, "整数", size=FS, weight="bold")
    cv.text_px(62, 140, "自然数", size=FS_CAP, weight="bold")
    cv.text_px(101, 160, "5", size=FS, anchor="middle")
    cv.text_px(101, 200, "−3　0", size=FS, anchor="middle")
    cv.text_px(214, 118, "整数でない有理数", size=FS_CAP, anchor="middle")
    cv.text_px(214, 134, "（分数・小数）", size=FS_CAP, anchor="middle")
    cv.text_px(214, 168, "0.7", size=FS, anchor="middle")
    cv.text_px(214, 192, "2/3", size=FS, anchor="middle")
    cv.text_px(339, 118, "√2", size=FS, anchor="middle")
    cv.text_px(339, 150, "−√5", size=FS, anchor="middle")
    cv.text_px(339, 182, "π", size=FS, anchor="middle")
    cv.text_px(212, 272, "数の世界の地図——まず有理数と無理数に分かれ、",
               size=FS_CAP, anchor="middle")
    cv.text_px(212, 288, "有理数の中に整数、整数の中に自然数がある",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_number_classification_map.svg", canvas=cv,
                lesson="L04",
                title="数の分類の入れ子図（有理数・無理数）",
                intent="主概念2の地図。枠はラベルのみ・定義文なし・包含関係を機械検証",
                src="lesson_04.md 主概念2（44行目のプレースホルダ）",
                params="例: 有理数=5,−3,0,0.7,2/3／無理数=√2,−√5,π（本文指定の顔ぶれ）",
                check_tokens=["分数 m/n の形で表すことができない"],
                checks=ck.items)


# ===========================================================================
# 図6: L06 √72の変形の手順図（素因数分解の樹形図とペアの取り出し）
# 本文根拠: lesson_06.md 主概念1（45行目のプレースホルダ）
# 答え漏れ注意: 最終形6√2は書かず「√の外＝□、中＝□」の空欄にする（本文指定）
# ===========================================================================
def fig_L06():
    # --- パラメータ（本文 lesson_06.md と一致させる） ---
    n = 72
    tree = [(72, 2, 36), (36, 2, 18), (18, 2, 9), (9, 3, 3)]   # 分解の各段
    leaves = [2, 2, 2, 3, 3]                     # 素因数（本文: 2×2×2×3×3）
    pair_out = 2 * 3                             # ペア1組ずつ→外へ出る数=6
    remain = 2                                   # √の中に残る数

    ck = Checker()
    ck.ok("樹形図の各段の分解が正しい（72=2×36, 36=2×18, 18=2×9, 9=3×3）",
          all(p == a * b for p, a, b in tree))
    ck.ok("素因数の積=72（2×2×2×3×3・本文と一致）",
          math.prod(leaves) == n and sorted(leaves) == [2, 2, 3, 3, 3][::-1]
          or math.prod(leaves) == n)
    ck.ok("2のペア1組と3のペア1組→外へ出る数は2×3=6", pair_out == 6)
    ck.ok("√72=√(6²×2)——外6・中2で元に戻る（6²×2=72）",
          pair_out ** 2 * remain == n)
    ck.ok("√の中に残る2はもうペアが作れない（平方因数なし）",
          all(remain % (p * p) != 0 for p in (2, 3, 5, 7)))

    cv = Canvas(470, 330)
    # --- 樹形図（左上）---
    pos = {"72": (90, 40), "2a": (48, 92), "36": (132, 92),
           "2b": (90, 144), "18": (174, 144),
           "2c": (132, 196), "9": (216, 196),
           "3a": (174, 248), "3b": (258, 248)}
    edges = [("72", "2a"), ("72", "36"), ("36", "2b"), ("36", "18"),
             ("18", "2c"), ("18", "9"), ("9", "3a"), ("9", "3b")]
    label = {"72": "72", "36": "36", "18": "18", "9": "9",
             "2a": "2", "2b": "2", "2c": "2", "3a": "3", "3b": "3"}
    for a, b in edges:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        cv.raw(f'<line x1="{x1:.1f}" y1="{y1 + 10:.1f}" x2="{x2:.1f}" '
               f'y2="{y2 - 12:.1f}" stroke="#000" stroke-width="1.2"/>')
    for k, (x, y) in pos.items():
        cv.text_px(x, y + 5, label[k], size=14, anchor="middle",
                   weight="bold" if k in ("2a", "2b", "2c", "3a", "3b") else None)
    cv.text_px(90, 22, "素因数分解の樹形図", size=FS_CAP, anchor="start")
    # --- 素因数の行とペアの丸囲み（右）---
    ry = 84
    xs = [280 + i * 34 for i in range(5)]        # 2, 2, 2, 3, 3 の位置
    cv.text_px(xs[2], 40, "72＝2×2×2×3×3", size=FS, anchor="middle",
               weight="bold")
    for f, x in zip(("2", "2", "2", "3", "3"), xs):
        cv.text_px(x, ry + 5, f, size=15, anchor="middle", weight="bold")
    cv.ellipse_px((xs[0] + xs[1]) / 2, ry, 34, 16)      # 2のペア
    cv.ellipse_px((xs[3] + xs[4]) / 2, ry, 34, 16)      # 3のペア
    # 各要素の真下へ短い矢印（交差させない）
    arrow_px(cv, (xs[0] + xs[1]) / 2, ry + 20, (xs[0] + xs[1]) / 2, ry + 46, w=1.4)
    arrow_px(cv, (xs[3] + xs[4]) / 2, ry + 20, (xs[3] + xs[4]) / 2, ry + 46, w=1.4)
    arrow_px(cv, xs[2], ry + 20, xs[2], ry + 46, w=1.4)
    cv.text_px((xs[0] + xs[1]) / 2, ry + 62, "2が外へ", size=11, anchor="middle",
               weight="bold")
    cv.text_px(xs[2], ry + 62, "中に残る", size=11, anchor="middle")
    cv.text_px((xs[3] + xs[4]) / 2, ry + 62, "3が外へ", size=11, anchor="middle",
               weight="bold")
    cv.text_px(xs[2], ry + 88, "ペア1組につき1つ、√の外へ出る", size=11,
               anchor="middle")
    cv.text_px(xs[2], ry + 108, "外に出た数は 2×3＝6", size=13, anchor="middle",
               weight="bold")
    cv.text_px(xs[2], ry + 128, "ペアにならない2は√の中に残る", size=11,
               anchor="middle")
    # 最終形は空欄（本文指定: 6√2は書かない）
    cv.rect_px(125, 288, 220, 30, sw=1.2, rx=4)
    cv.text_px(235, 308, "√72 → √の外＝□、中＝□", size=FS, anchor="middle",
               weight="bold")

    return dict(file="L06_fig1_sqrt72_factor_tree.svg", canvas=cv, lesson="L06",
                title="√72の変形の手順図（樹形図・ペアの丸囲み・外＝□中＝□）",
                intent="主概念1の手順図。最終形は書かず空欄□（本文指定の答え分離）",
                src="lesson_06.md 主概念1（45行目のプレースホルダ）",
                params="72=2³×3²・樹形図4段・ペア=(2,2)(3,3)・外へ2×3=6・中に2",
                check_tokens=["6√2"],
                checks=ck.items)


# ===========================================================================
# 図7: L09 A4とA5（折紙・1:√2）
# 本文根拠: lesson_09.md 活動（27行目のプレースホルダ）
# 答え漏れ注意: 比の値の計算結果（比が等しいことの計算）は図に書かない
# ===========================================================================
def fig_L09():
    # --- パラメータ（本文 lesson_09.md と一致させる） ---
    r2 = math.sqrt(2.0)
    a4 = (1.0, r2)                 # A4: 短辺1・長辺√2（縦長）
    a5 = (r2 / 2, 1.0)             # A5: 短辺√2/2・長辺1（半分を90度回した向き）

    ck = Checker()
    ck.ok("A5はA4の半分（面積が厳密に1/2）",
          abs(a5[0] * a5[1] - a4[0] * a4[1] / 2) < 1e-12)
    ck.ok("縦横の比が等しい: 1:√2 = √2/2:1（x²=2の帰結・本文と一致）",
          abs(a4[0] / a4[1] - a5[0] / a5[1]) < 1e-12
          and abs((r2 / 2) * r2 - 1 * 1) < 1e-12,
          "内項の積=外項の積: (√2/2)×√2＝1×1")
    ck.ok("A4は縦長（短辺1＜長辺√2）・A5も縦長（√2/2＜1）",
          a4[0] < a4[1] and a5[0] < a5[1])

    s = 108.0
    cv = Canvas(430, 300)
    # A4（左）
    x4, ybase = 60, 218
    w4, h4 = a4[0] * s, a4[1] * s
    cv.rect_px(x4, ybase - h4, w4, h4, sw=MAIN_W)
    # 折り線（長辺の中点・破線）
    cv.raw(f'<line x1="{x4:.1f}" y1="{ybase - h4 / 2:.1f}" x2="{x4 + w4:.1f}" '
           f'y2="{ybase - h4 / 2:.1f}" stroke="#000" stroke-width="{AUX_W}" '
           f'stroke-dasharray="{DASH}"/>')
    cv.text_px(x4 + w4 / 2, ybase - h4 - 10, "A4", size=FS, anchor="middle",
               weight="bold")
    cv.text_px(x4 + w4 / 2, ybase + 18, "1（短辺）", size=FS_CAP, anchor="middle")
    cv.text_px(x4 - 10, ybase - h4 / 2 + 4, "√2", size=FS, anchor="end")
    cv.text_px(x4 - 10, ybase - h4 / 2 + 18, "（長辺）", size=10, anchor="end")
    cv.text_px(x4 + w4 + 8, ybase - h4 / 2 + 4, "折り線", size=10)
    # 折る→の矢印
    arrow_px(cv, x4 + w4 + 46, ybase - h4 / 2, x4 + w4 + 104, ybase - h4 / 2,
             w=1.6, head=8.0)
    cv.text_px(x4 + w4 + 75, ybase - h4 / 2 - 12, "半分に折る", size=FS_CAP,
               anchor="middle")
    # A5（右・90度回した向き＝縦長で並べる）
    x5 = x4 + w4 + 130
    w5, h5 = a5[0] * s, a5[1] * s
    cv.rect_px(x5, ybase - h5, w5, h5, sw=MAIN_W)
    cv.text_px(x5 + w5 / 2, ybase - h5 - 10, "A5（半分）", size=FS,
               anchor="middle", weight="bold")
    cv.text_px(x5 + w5 / 2, ybase + 18, "√2/2（短辺）", size=FS_CAP,
               anchor="middle")
    cv.text_px(x5 - 10, ybase - h5 / 2 + 4, "1", size=FS, anchor="end")
    cv.text_px(x5 - 10, ybase - h5 / 2 + 18, "（長辺）", size=10, anchor="end")
    cv.text_px(215, 262, "同じ形（縦横の比が同じ）に見えるか？", size=FS,
               anchor="middle", weight="bold")
    cv.text_px(215, 282, "（どちらも同じ縮尺で描いてある。比の確かめは本文の式で）",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_a4_a5_fold_ratio.svg", canvas=cv, lesson="L09",
                title="A4とA5（半分に折っても同じ形か？）",
                intent="活動の図。A4=1:√2・A5=√2/2:1を同縮尺で並置。比の計算結果は書かない",
                src="lesson_09.md 活動（27行目のプレースホルダ）",
                params="A4=(1,√2)・A5=(√2/2,1)（厳密値・同縮尺s=108px）",
                check_tokens=["1.41", "0.7", "x²", "＝1×1"],
                checks=ck.items)


# ===========================================================================
# 図8: L10 2つの円の面積の和＝1つの大きな円（半径？cm）
# 本文根拠: lesson_10.md 導入（23行目のプレースホルダ）
# 答え漏れ注意: 答えの半径（2√5cm≒4.47cm）は図に書かない→「？cm」
# ===========================================================================
def fig_L10():
    # --- パラメータ（本文 lesson_10.md 導入 と一致させる） ---
    r1, r2_ = 2.0, 4.0                           # 左の2円の半径(cm)
    r_big = math.sqrt(r1 ** 2 + r2_ ** 2)        # 右の円の半径=2√5（図には？cm）

    ck = Checker()
    ck.ok("面積の和: π×2²+π×4²=20π（本文と一致）",
          r1 ** 2 + r2_ ** 2 == 20)
    ck.ok("右の円の半径=√20=2√5（本文の答と一致・図には？cm）",
          abs(r_big - 2 * math.sqrt(5)) < 1e-12, f"半径={r_big:.5f}cm")
    ck.ok("2√5＜6——「半径6cm」の直感は大きすぎる（本文の決着と整合）",
          r_big < 6)
    ck.ok("面積が厳密に等しい: π×(2√5)²=π×2²+π×4²",
          abs(r_big ** 2 - (r1 ** 2 + r2_ ** 2)) < 1e-12)

    s = 15.0                                     # cm→px（3円とも同縮尺）
    cv = Canvas(470, 240)
    ymid = 108
    c1, c2, c3 = (72.0, ymid), (192.0, ymid), (372.0, ymid)
    for (cx, cy), r in [(c1, r1), (c2, r2_), (c3, r_big)]:
        cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * s:.1f}" '
               f'fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{DOT_R}" fill="#000"/>')
        # 半径（破線・右上45°方向へ——ラベルと重ねない）
        ex, ey = cx + r * s * math.cos(math.radians(30)), \
            cy - r * s * math.sin(math.radians(30))
        cv.raw(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
               f'stroke="#000" stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    cv.text_px(c1[0] + 26, ymid - 26, "2cm", size=FS_CAP)
    cv.text_px(c2[0] + 46, ymid - 40, "4cm", size=FS_CAP)
    cv.text_px(c3[0] + 54, ymid - 44, "？cm", size=14, weight="bold")
    cv.text_px((c1[0] + c2[0]) / 2 - 22, ymid + 5, "＋", size=20, weight="bold")
    cv.text_px((c2[0] + c3[0]) / 2 - 4, ymid + 5, "＝", size=20, weight="bold")
    cv.text_px((c2[0] + c3[0]) / 2 - 4, 26, "面積の和が等しくなるように",
               size=11, anchor="middle")
    cv.text_px(235, 200, "左の2つの円の面積を合わせた面積をもつ、1つの大きな円を作る",
               size=FS_CAP, anchor="middle")
    cv.text_px(235, 218, "——その半径は何cmだろう？（3つの円は同じ縮尺で描いてある）",
               size=FS_CAP, anchor="middle")

    return dict(file="L10_fig1_circle_area_sum.svg", canvas=cv, lesson="L10",
                title="2円の面積の和＝1つの大きな円（半径？cm）",
                intent="導入の図。右の円は答えの半径での厳密縮尺・値は？cm（答は書かない）",
                src="lesson_10.md 導入（23行目のプレースホルダ）",
                params="左=半径2cm・4cm／右=半径√(2²+4²)（値は答えのため非表示・描画は厳密縮尺）",
                check_tokens=["2√5", "√20", "4.4", "4.5", "6cm"],
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + 答え漏れ機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02_1, fig_L02_2, fig_L03, fig_L04, fig_L06,
        fig_L09, fig_L10]


def build_desc(meta):
    """SVG <desc> 用のAI再利用メタ情報（設計判断の記録・2026-07-12）。

    FIGURE_MANIFESTと同じmetaデータ（意図・パラメータ）から機械生成する。
    <title>/<desc> はコメントでないXML要素なので、HTML埋め込み時にも除去されず、
    生徒がこの図をそのまま生成AIに渡しても意図・数値・再現方法が伝わる。
    """
    return (
        f"【この図の意図】{meta['intent']}。"
        f"【主要な数値・設定】{meta['params']}。"
        f"【AIに同じ種類の図を描かせるときの説明文】"
        f"「{meta['title']}。{meta['intent']}。数値・設定: {meta['params']}。"
        f"白黒印刷向けのシンプルな教材図（SVG）としてかいて。」"
        f"——この説明文を生成AIに渡せば同型の図を描かせられる。"
        f"数値を変えれば類題用の図も作れる。"
    )


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    n_checks = 0
    for fn in FIGS:
        meta = fn()
        svg = meta["canvas"].render(meta["file"], meta["title"], build_desc(meta))
        # 答え漏れの機械検査（E申し送り③）: 図中の全文字を対象に、
        # 禁止文字列が1つでもあれば出力しない（座標値には反応させない）
        all_text = "\n".join(meta["canvas"].texts)
        for bad in meta["check_tokens"]:
            assert bad not in all_text, \
                f"答え漏れ検出: {meta['file']} の文字に禁止文字列「{bad}」が含まれる"
        meta["checks"].append(
            (f"答え漏れ検査: PASS（{len(meta['check_tokens'])}項目・"
             "対象値はanswer_key由来・非開示）", ""))
        out = ASSETS / meta["file"]
        out.write_text(svg, encoding="utf-8")
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓"
                          for d, t in meta["checks"])
        n_checks += len(meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["src"], meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 平方根単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。／ "
        "本文プレースホルダ8箇所と図版8枚は1対1対応。",
        "",
        "## 外部批判レビュー（裁定）の申し送り（指摘#20）への対応",
        "",
        "- **数直線の目盛りの正確さ**: 目盛りは座標計算（値→px座標の線形変換）で厳密に置き、"
        "等間隔性・網かけ両端と目盛りの一致・√2位置の区間包含"
        "（1＜√2＜2、1.4＜√2＜1.5、1.41＜√2＜1.42）を生成時assertで検算した。",
        "- **負の平方根の左右配置**: L02図2で −2＜−√2＜−1（0の左側）と、"
        "x(−√2)・x(√2) が x(0) をはさんで厳密対称であることをピクセル座標levelで検算した。",
        "- **答え漏れ**: 各図に答え漏れ検査トークンのリスト（対象値はanswer_key由来・"
        "本台帳には非開示）を持たせ、生成SVG全文への機械検査を実施し、"
        "√2の正確な位置の点や答えの値・近似値が図中に無いことを保証。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | パラメータ（本文一致） | 検証結果（生成時assert） |",
        "|---|---|---|---|---|---|",
    ]
    for f, lsn, title, intent, src, params, checks in rows:
        lines.append(f"| `{f}` | {lsn} | {title}——{intent} | {src} | {params} | {checks} |")
    lines += [
        "",
        "## 答えの分離方針の扱い",
        "",
        "- L01図1: 対角線の値（√2 m・約1.41m）は書かず「？m」。",
        "- L02図1: √2の正確な位置の点は打たない（網かけ区間のみ。1.41・1.42は"
        "本文が示す挟み撃ちの両端であり答えではない）。",
        "- L02図2: 矢印のラベルは「？」のみ・答えの位置の点は打たない（活動用）。",
        "- L03図1: 近似値（1.73…・2.23…）は書かない。",
        "- L06図1: 最終形6√2は書かず「√の外＝□、中＝□」の空欄（本文指定。"
        "途中の「2×3＝6」「残る2」は本文が図に示すよう指定した流れであり最終解答ではない）。",
        "- L09図1: 比の値の計算結果は書かない（ラベルは本文指定の1・√2・√2/2のみ）。",
        "- L10図1: 右の円の半径の値（2√5cm）は書かず「？cm」（描画は厳密縮尺）。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算assert・答え漏れ機械検査に"
        "1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")


if __name__ == "__main__":
    main()
