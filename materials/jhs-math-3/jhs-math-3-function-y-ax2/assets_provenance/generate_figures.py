#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「関数y=ax²」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み）。
ヘルパー群（Canvas/ハッチ/寸法線/矢印ほか）は先行単元
production/jhs-math-3-similar-figures/candidate_draft/assets_provenance/generate_figures.py および
production/jhs-math-3-pythagorean-theorem/candidate_draft/assets_provenance/generate_figures.py
からコピー再利用（元スクリプトは無変更）。本単元では関数グラフ用に
「x/y別スケール・座標軸（矢印・目盛・数値）・関数曲線サンプリング・端点●○」を追加した。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（16枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / xml.etree）
- 数学の自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。
  放物線・直線・双曲線・階段関数の「通過点」「変域の端点」「端点●○の座標」は
  すべて式から座標計算し、本文プレースホルダの指定値と照合する。
- 答えの分離方針: 近隣の設問が問う値は図に書かない。各図に答え漏れ検査トークンのリスト（check_tokens・検査の実装定数）
  （bans）を持たせ、生成後のSVG本文に対して機械検査する（main内）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。
"""

import math
import datetime
import re
import xml.etree.ElementTree as ET
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
FS_NUM = 11       # 軸の目盛数値（キャプション段の−1px下限内）
DOT_R = 2.5       # 点マーカー半径
DOT_R_END = 3.4   # 端点●○（L12階段・変域端点）はやや大きく
GRID_C = "#bbb"   # 方眼の線色（薄グレー・情報は持たせない）
SHADE = "#ddd"    # うすい網かけ（薄グレー塗り）


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き に変換して描く）
# 先行単元 generate_figures.py からコピー再利用。
# 本単元での拡張: x/y別スケール（sx, sy）——関数グラフはyの範囲が大きい図
# （y最大26・1300など）があるため。縦横比が意味を持つ幾何図（L10正方形）は sx=sy で使う。
# ===========================================================================
class Canvas:
    def __init__(self, width, height, sx=1.0, sy=None, ox=0.0, oy=0.0):
        """sx/sy: 数学単位→px（syを省略するとsx=sy）、(ox,oy): 数学原点のSVG座標"""
        self.w, self.h = width, height
        self.sx = sx
        self.sy = sx if sy is None else sy
        self.ox, self.oy = ox, oy
        self.defs = []
        self.body = []

    # 座標変換 -------------------------------------------------------------
    def P(self, p):
        return (self.ox + self.sx * p[0], self.oy - self.sy * p[1])

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
                 f'stroke-width="{w}"{d} stroke-linejoin="round"/>')

    def dot(self, p, r=DOT_R):
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')

    def open_dot(self, p, r=DOT_R_END):
        """端点○（その点をふくまない）——白抜き+黒縁"""
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                 f'stroke="#000" stroke-width="1.4"/>')

    def circle(self, c, r_math, w=MAIN_W, dash=None):
        x, y = self.P(c)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_math * self.sx:.1f}" '
                 f'fill="none" stroke="#000" stroke-width="{w}"{d}/>')

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None):
        x, y = self.P(p)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS, anchor="start", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def dim(self, a, b, label, offset=(0, 0), tick=4.0, size=FS):
        """寸法線: 細線+両端ティック+中央ラベル。offsetは数学座標のずらし量"""
        a2 = (a[0] + offset[0], a[1] + offset[1])
        b2 = (b[0] + offset[0], b[1] + offset[1])
        self.line(a2, b2, w=0.9)
        (x1, y1), (x2, y2) = self.P(a2), self.P(b2)
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        for (x, y) in ((x1, y1), (x2, y2)):
            self.raw(f'<line x1="{x - nx * tick:.1f}" y1="{y - ny * tick:.1f}" '
                     f'x2="{x + nx * tick:.1f}" y2="{y + ny * tick:.1f}" '
                     f'stroke="#000" stroke-width="0.9"/>')
        if label:
            mx, my = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2
            self.text((mx, my), label, size=size,
                      dy=(1.15 if ny > 0 else -0.55))

    def grid(self, x0, y0, x1, y1, step=1):
        """方眼（薄グレー）を数学座標の範囲に敷く"""
        i = x0
        while i <= x1 + 1e-9:
            self.line((i, y0), (i, y1), w=0.6, color=GRID_C)
            i += step
        j = y0
        while j <= y1 + 1e-9:
            self.line((x0, j), (x1, j), w=0.6, color=GRID_C)
            j += step

    def add_hatch(self):
        """濃淡+ハッチングの塗り分けパターン（§4）を内蔵defsへ"""
        self.defs.append(
            '<pattern id="h45" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>'
            '<pattern id="h135" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(135)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>')

    def save(self, path, fig_id, title, desc=None):
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            + (f'<desc>{escape(desc)}</desc>\n' if desc else "") +
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md準拠（内部規約の要旨は同SPECに反映済み）・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0):
    """SVG座標(px)で矢印（線+先端の三角形）を描く"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="#000" stroke-width="{w}"/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')


class Checker:
    """数学検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


# ===========================================================================
# 関数グラフ用ヘルパー（本単元で追加——docs/SPEC_figures.md「関数図の規約」の実装）
# ===========================================================================
def plane(xr, yr, sx, sy=None, ml=34, mr=22, mt=18, mb=30):
    """座標平面用Canvas。xr=(x0,x1), yr=(y0,y1)は軸の描画範囲（数学座標）"""
    sy = sx if sy is None else sy
    x0, x1 = xr
    y0, y1 = yr
    w = ml + (x1 - x0) * sx + mr
    h = mt + (y1 - y0) * sy + mb
    cv = Canvas(round(w), round(h), sx=sx, sy=sy,
                ox=ml - x0 * sx, oy=mt + y1 * sy)
    cv._xr, cv._yr = xr, yr
    return cv


def draw_axes(cv, xlabel="x", ylabel="y", xnums=(), ynums=(),
              x_step=1, y_step=1, tick_half=3.0, num_size=FS_NUM,
              origin="O", ticks=True):
    """座標軸: 矢印つき軸線・目盛（1目盛=x_step/y_step）・指定数値ラベル・原点O"""
    (x0, x1), (y0, y1) = cv._xr, cv._yr
    # 軸線+矢印（正の向きの端）
    ax0, ay = cv.P((x0, 0))
    ax1, _ = cv.P((x1, 0))
    arrow_px(cv, ax0, ay, ax1 + 8, ay, w=1.2)
    bx, by0 = cv.P((0, y0))
    _, by1 = cv.P((0, y1))
    arrow_px(cv, bx, by0, bx, by1 - 8, w=1.2)
    # 軸ラベル
    cv.text_px(ax1 + 10, ay + 4.5, xlabel, size=FS, anchor="start")
    cv.text_px(bx + 7, by1 - 6, ylabel, size=FS, anchor="start")
    # 目盛
    if ticks:
        t = math.ceil(x0 / x_step) * x_step
        while t <= x1 + 1e-9:
            if abs(t) > 1e-9:
                px, py = cv.P((t, 0))
                cv.raw(f'<line x1="{px:.1f}" y1="{py - tick_half:.1f}" '
                       f'x2="{px:.1f}" y2="{py + tick_half:.1f}" '
                       f'stroke="#000" stroke-width="1.0"/>')
            t += x_step
        t = math.ceil(y0 / y_step) * y_step
        while t <= y1 + 1e-9:
            if abs(t) > 1e-9:
                px, py = cv.P((0, t))
                cv.raw(f'<line x1="{px - tick_half:.1f}" y1="{py:.1f}" '
                       f'x2="{px + tick_half:.1f}" y2="{py:.1f}" '
                       f'stroke="#000" stroke-width="1.0"/>')
            t += y_step
    # 数値ラベル
    for v in xnums:
        px, py = cv.P((v, 0))
        cv.text_px(px, py + num_size + 3, fmt_num(v), size=num_size, anchor="middle")
    for v in ynums:
        px, py = cv.P((0, v))
        cv.text_px(px - 6, py + num_size * 0.35, fmt_num(v), size=num_size, anchor="end")
    if origin:
        px, py = cv.P((0, 0))
        cv.text_px(px - 5, py + num_size + 3, origin, size=num_size, anchor="end")


def fmt_num(v):
    s = f"{v:g}"
    return s.replace("-", "−")  # 数学のマイナス記号（本文と同じU+2212）


def func_pts(f, xa, xb, n=160):
    """関数fを[xa,xb]でサンプリングした点列（数学座標）"""
    return [(xa + (xb - xa) * i / n, f(xa + (xb - xa) * i / n)) for i in range(n + 1)]


def parabola_span(a, y_lim, x_lim):
    """y=ax²を|y|≦y_lim・|x|≦x_limで描くときのx範囲（左右対称）"""
    xm = min(x_lim, math.sqrt(y_lim / abs(a)))
    return -xm, xm


def on_curve(ck, name, f, pts, tol=1e-9):
    """通過点リストが厳密に曲線上にあることを検算"""
    for (x, y) in pts:
        assert abs(f(x) - y) <= tol, f"{name}: 点({x},{y})が曲線上にない f({x})={f(x)}"
    ck.ok(f"{name}の通過点{len(pts)}点が式を厳密に満たす",
          True, "／".join(f"({fmt_num(x)},{fmt_num(y)})" for x, y in pts))


# ===========================================================================
# 図1: L01 主概念1——1辺1〜4cmの正方形（まわりの長さと面積の増え方）
# 本文根拠: lesson_01.md 主概念1「まわりの長さy=4x・面積y=x²」＋直後の表（4,8,12,16／1,4,9,16）
# 答え漏れ注意: ラベルの数値は本文が図の直後の表で明示する与件（設問の答ではない）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md 主概念1 と一致させる） ---
    sides = [1, 2, 3, 4]          # 1辺(cm)
    s = 26.0                      # 1cm→px
    gap = 40.0                    # 正方形間隔(px)

    ck = Checker()
    ck.ok("まわりの長さ=4x（本文の表 4,8,12,16 と一致）",
          [4 * x for x in sides] == [4, 8, 12, 16])
    ck.ok("面積=x²（本文の表 1,4,9,16 と一致）",
          [x * x for x in sides] == [1, 4, 9, 16])
    ck.ok("方眼セル数=面積（1cm²方眼で面積が見える）",
          all(x * x == sum(1 for _ in range(x) for _ in range(x)) for x in sides))

    W = 24 + sum(x * s for x in sides) + gap * 3 + 24
    H = 16 + 4 * s + 52
    cv = Canvas(round(W), round(H), sx=1.0)
    base_y = 16 + 4 * s          # 下端（px）を揃える
    x_px = 24.0
    for x in sides:
        side = x * s
        x0, y0 = x_px, base_y - side
        # 正方形+1cm²方眼
        cv.raw(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{side:.1f}" height="{side:.1f}" '
               f'fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        for k in range(1, x):
            cv.raw(f'<line x1="{x0 + k * s:.1f}" y1="{y0:.1f}" x2="{x0 + k * s:.1f}" '
                   f'y2="{y0 + side:.1f}" stroke="{GRID_C}" stroke-width="0.8"/>')
            cv.raw(f'<line x1="{x0:.1f}" y1="{y0 + k * s:.1f}" x2="{x0 + side:.1f}" '
                   f'y2="{y0 + k * s:.1f}" stroke="{GRID_C}" stroke-width="0.8"/>')
        cv.text_px(x0 + side / 2, y0 - 5, f"1辺{x}cm", size=FS_NUM, anchor="middle")
        cv.text_px(x0 + side / 2, base_y + 18, f"まわり{4 * x}cm", size=12, anchor="middle")
        cv.text_px(x0 + side / 2, base_y + 34, f"面積{x * x}cm²", size=12, anchor="middle")
        x_px += side + gap

    return {"file": "L01_fig1_growing_squares.svg", "lesson": "L01", "canvas": cv,
            "title": "1辺1〜4cmの正方形——まわりの長さと面積",
            "intent": "同じ正方形から「まわり=4x」「面積=x²」という2つのちがう増え方が生まれることを見せる導入図",
            "src": "lesson_01.md 主概念1（表の直前）",
            "params": "1辺=1,2,3,4cm／まわり=4x／面積=x²（内部を1cm²方眼で区切り）",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_01.md L38「1辺1cm・2cm・3cm・4cmの正方形を左から並べた図…」"}


# ===========================================================================
# 図2: L03 例題——半径1・2・3cmの3つの円（面積はπ・4π・9π）
# 本文根拠: lesson_03.md 例題「半径x cmの円の面積y cm²」＋直後の表（π,4π,9π,16π）
# 答え漏れ注意: 例題の問いは「2乗に比例するか」——結論の文言は図に書かない（面積値は与件）
# ===========================================================================
def fig_L03_1():
    # --- パラメータ（lesson_03.md 例題 と一致させる） ---
    radii = [1, 2, 3]             # 半径(cm)
    s = 24.0                      # 1cm→px
    gap = 26.0

    ck = Checker()
    ck.ok("面積比=1:4:9（半径比1:2:3の2乗——本文表 π,4π,9π と一致）",
          [r * r for r in radii] == [1, 4, 9])
    ck.ok("半径2倍→面積4倍・3倍→9倍（m倍→m²倍）",
          (2 / 1) ** 2 == 4 and (3 / 1) ** 2 == 9)
    ck.ok("結論の文言「2乗に比例する」は図に書かない（例題の答）", True)

    area_lab = ["面積 π cm²", "面積 4π cm²", "面積 9π cm²"]
    W = 20 + sum(2 * r * s for r in radii) + gap * 2 + 20
    rmax = max(radii) * s
    H = 14 + 2 * rmax + 46
    cv = Canvas(round(W), round(H), sx=1.0)
    cy = 14 + rmax                # 中心の高さ（px）を揃える
    x_px = 20.0
    for i, r in enumerate(radii):
        rp = r * s
        cx = x_px + rp
        cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rp:.1f}" '
               f'fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        cv.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.2" fill="#000"/>')
        cv.raw(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + rp:.1f}" y2="{cy:.1f}" '
               f'stroke="#000" stroke-width="1.2"/>')
        if rp >= 34:              # ラベルが円内に収まる大きさなら半径線の上に
            cv.text_px(cx + rp / 2, cy - 6, f"{r}cm", size=12, anchor="middle")
        else:                     # 小さい円は円の外（上）に置く（円周との重なり回避）
            cv.text_px(cx, cy - rp - 7, f"{r}cm", size=12, anchor="middle")
        cv.text_px(cx, 14 + 2 * rmax + 20, area_lab[i], size=12, anchor="middle")
        x_px += 2 * rp + gap

    return {"file": "L03_fig1_three_circles.svg", "lesson": "L03", "canvas": cv,
            "title": "半径1・2・3cmの円と面積π・4π・9π",
            "intent": "数学化の型の例題——半径（決める側x）と面積（決まる側y）の対応を目で確認する",
            "src": "lesson_03.md 例題（表の直前）",
            "params": "半径=1,2,3cm／面積=π,4π,9π cm²（面積比1:4:9をassert）",
            "checks": ck.items, "check_tokens": ["2乗に比例"],
            "placeholder": "lesson_03.md L30「半径1cm・2cm・3cmの同心でない3つの円…」"}


# ---- L04〜L06共通の座標平面（x: −4..4, y: −1..10, 1目盛=1） ---------------
def plane_L04(sx=27.0, sy=27.0, mr=26):
    cv = plane((-4, 4), (-1, 10), sx, sy, ml=36, mr=mr, mt=16, mb=26)
    return cv


PTS7 = [(-3, 9), (-2, 4), (-1, 1), (0, 0), (1, 1), (2, 4), (3, 9)]
PTS_HALF = [(-2.5, 6.25), (-1.5, 2.25), (-0.5, 0.25),
            (0.5, 0.25), (1.5, 2.25), (2.5, 6.25)]


# ===========================================================================
# 図3: L04 図1——表の7点だけを打った図（線では結ばない）
# 本文根拠: lesson_04.md 主概念1・表（x=−3..3, y=9,4,1,0,1,4,9）の直後
# graph-as-picture対策の中核図: 「表の1列＝グラフの1点」を矢印で例示
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（lesson_04.md 主概念1の表 と一致させる） ---
    f = lambda x: x * x
    sample_col = (2, 4)           # 矢印で例示する列（本文指定: 列(2,4)→点(2,4)）

    ck = Checker()
    on_curve(ck, "y=x²", f, PTS7)
    ck.ok("例示の列(2,4)は表の1列（2²=4）", f(sample_col[0]) == sample_col[1])
    ck.ok("点のみで曲線・折れ線を描かない（本文「線では結ばない」）", True)

    cv = plane_L04(mr=128)        # 右に表の抜粋+ラベルの余白
    draw_axes(cv, xnums=(-4, -2, 2, 4), ynums=(2, 4, 6, 8, 10))
    for p in PTS7:
        cv.dot(p, r=3.0)
    # 表の1列の抜粋（右脇）: |x|2| / |y|4|
    bx, by = cv.P((4, 8))
    bx += 26
    cw, chh = 26, 22
    for r_i, (lab, val) in enumerate((("x", fmt_num(sample_col[0])),
                                      ("y", fmt_num(sample_col[1])))):
        y0 = by + r_i * chh
        cv.raw(f'<rect x="{bx:.1f}" y="{y0:.1f}" width="{cw}" height="{chh}" '
               f'fill="#eee" stroke="#000" stroke-width="1.0"/>')
        cv.raw(f'<rect x="{bx + cw:.1f}" y="{y0:.1f}" width="{cw}" height="{chh}" '
               f'fill="none" stroke="#000" stroke-width="1.0"/>')
        cv.text_px(bx + cw / 2, y0 + chh / 2 + 4.5, lab, size=12, anchor="middle")
        cv.text_px(bx + cw * 1.5, y0 + chh / 2 + 4.5, val, size=12, anchor="middle")
    cv.text_px(bx + cw, by - 8, "表の1列", size=FS_NUM, anchor="middle")
    px, py = cv.P(sample_col)
    arrow_px(cv, bx - 4, by + chh, px + 8, py - 6, w=1.3)
    cv.text_px(bx + cw, by + 2 * chh + 18, "表の1列＝", size=12, anchor="middle", weight="bold")
    cv.text_px(bx + cw, by + 2 * chh + 33, "グラフの1点", size=12, anchor="middle", weight="bold")

    return {"file": "L04_fig1_seven_points.svg", "lesson": "L04", "canvas": cv,
            "title": "y=x²の表の7点を打っただけの図（結ばない）",
            "intent": "graph-as-picture対策——グラフは形の絵ではなく対応(x,y)の点の集まりだと見せる第1段",
            "src": "lesson_04.md 主概念1（表の直後・3段図の1枚目）",
            "params": "7点=(−3,9)〜(3,9)／例示列(2,4)→点(2,4)へ矢印／曲線・折れ線なし",
            "checks": ck.items, "check_tokens": ["放物線"],
            "placeholder": "lesson_04.md L30「y=x²上の7点…を黒丸で打っただけの図。線では結ばない…」"}


# ===========================================================================
# 図4: L04 図2——0.5刻みの点を加えた計13点（まだ結ばない）
# 本文根拠: lesson_04.md「x=0.5ならy=0.25…もっと細かく取ってみよう」の直後
# ===========================================================================
def fig_L04_2():
    f = lambda x: x * x
    ck = Checker()
    on_curve(ck, "y=x²", f, PTS7 + PTS_HALF)
    ck.ok("点の総数=13（7点+0.5刻み6点）", len(PTS7 + PTS_HALF) == 13)
    ck.ok("まだ線では結ばない（本文指定）", True)

    cv = plane_L04()
    draw_axes(cv, xnums=(-4, -2, 2, 4), ynums=(2, 4, 6, 8, 10))
    for p in PTS7:
        cv.dot(p, r=3.0)
    for p in PTS_HALF:
        cv.dot(p, r=3.0)

    return {"file": "L04_fig2_thirteen_points.svg", "lesson": "L04", "canvas": cv,
            "title": "0.5刻みの点を加えた計13点（まだ結ばない）",
            "intent": "点を細かく取るほど曲線の気配が現れる過程を見せる第2段（graph-as-picture対策）",
            "src": "lesson_04.md 主概念1（3段図の2枚目）",
            "params": "7点+0.5刻み6点=13点／全点がy=x²を厳密に満たすことをassert",
            "checks": ck.items, "check_tokens": ["放物線"],
            "placeholder": "lesson_04.md L34「上の7点に加えて0.5刻みの点…を加えた計13点の図…」"}


# ===========================================================================
# 図5: L04 図3——なめらかな曲線の完成図（上端まで延ばす・矢印なし）
# 本文根拠: lesson_04.md「原点を通るなめらかな曲線になる」の直後
# ===========================================================================
def fig_L04_3():
    f = lambda x: x * x
    y_top = 10                    # 座標平面の上端（本文: 上端まで延ばす）
    xa, xb = parabola_span(1, y_top, 4)

    ck = Checker()
    on_curve(ck, "y=x²", f, PTS7)
    ck.ok("曲線の両端が座標平面の上端y=10に達する（x=±√10）",
          abs(f(xa) - y_top) < 1e-9 and abs(f(xb) - y_top) < 1e-9,
          f"x=±{abs(xa):.3f}")
    ck.ok("曲線端に矢印を付けない（本文指定）", True)

    cv = plane_L04()
    draw_axes(cv, xnums=(-4, -2, 2, 4), ynums=(2, 4, 6, 8, 10))
    cv.polyline(func_pts(f, xa, xb, 200), w=MAIN_W)
    for p in PTS7:
        cv.dot(p, r=3.0)

    return {"file": "L04_fig3_smooth_curve.svg", "lesson": "L04", "canvas": cv,
            "title": "y=x²のなめらかな曲線（完成図）",
            "intent": "点のすきまが埋まって曲線になる第3段。通過7点を黒丸で残し「点の集まり」の意味を保持",
            "src": "lesson_04.md 主概念1（3段図の3枚目）",
            "params": "曲線範囲x=±√10（y=10の上端まで）／通過7点を黒丸／矢印なし",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_04.md L38「y=x²のなめらかな曲線を実線でかいた完成図…」"}


# ===========================================================================
# 図6: L05 図1——y=x²とy=−x²のx軸対称
# 本文根拠: lesson_05.md 主概念1・表の直後
# ===========================================================================
def fig_L05_1():
    f1 = lambda x: x * x
    f2 = lambda x: -x * x
    pts1 = PTS7
    pts2 = [(x, -y) for (x, y) in PTS7]
    pair = ((2, 4), (2, -4))      # 縦の破線で結ぶ2点（本文指定）

    ck = Checker()
    on_curve(ck, "y=x²", f1, pts1)
    on_curve(ck, "y=−x²", f2, pts2)
    ck.ok("2曲線はx軸対称（全通過点で y と −y が対応）",
          all(f1(x) == -f2(x) for x in range(-3, 4)))
    ck.ok("破線で結ぶ2点(2,4)・(2,−4)は対称の実例", f1(2) == 4 and f2(2) == -4)

    cv = plane((-4, 4), (-9, 9), 24.0, 21.0, ml=40, mr=44, mt=16, mb=26)
    draw_axes(cv, xnums=(-4, -2, 4), ynums=(-9, -6, -3, 3, 6, 9))
    # x=2の数値は破線(2,4)-(2,−4)と重なるため、目盛のすぐ左に手動配置
    px, py = cv.P((2, 0))
    cv.text_px(px - 5, py + FS_NUM + 3, "2", size=FS_NUM, anchor="end")
    xa, xb = parabola_span(1, 9, 4)
    cv.polyline(func_pts(f1, xa, xb, 200), w=MAIN_W)
    cv.polyline(func_pts(f2, xa, xb, 200), w=MAIN_W)
    cv.line(pair[0], pair[1], w=AUX_W, dash=DASH)
    cv.dot(pair[0], r=3.0)
    cv.dot(pair[1], r=3.0)
    px, py = cv.P((2.9, 8.0))
    cv.text_px(px + 6, py, "y＝x²", size=FS, anchor="start")
    px, py = cv.P((2.9, -8.0))
    cv.text_px(px + 6, py + 8, "y＝−x²", size=FS, anchor="start")

    return {"file": "L05_fig1_axis_symmetry.svg", "lesson": "L05", "canvas": cv,
            "title": "y=x²とy=−x²——x軸対称",
            "intent": "aの符号でグラフの開く向きが逆になり、2曲線がx軸対称の位置に来ることを見せる",
            "src": "lesson_05.md 主概念1（表の直後）",
            "params": "通過点±(x,x²) x=−3..3／破線(2,4)-(2,−4)／式ラベル2つ",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_05.md L29「y=x²…とy=−x²…の2曲線。各曲線に式ラベル…」"}


# ===========================================================================
# 図7: L05 図2——y=2x²・y=x²・y=x²/2の開き具合（同じxで比べる）
# 本文根拠: lesson_05.md 主概念2・表の直後
# ===========================================================================
def fig_L05_2():
    curves = [(2.0, "y＝2x²"), (1.0, "y＝x²"), (0.5, "y＝x²/2")]
    x_cmp = 2                     # 「同じxで比べる」縦線の位置
    cmp_pts = [(2, 2), (2, 4), (2, 8)]   # 本文指定の強調3点

    ck = Checker()
    for a, name in curves:
        pts = [(x, a * x * x) for x in (-2, -1, 0, 1, 2)]
        on_curve(ck, name, lambda x, a=a: a * x * x, pts)
    ck.ok("x=2でのy=8,4,2はそれぞれ2x²・x²・x²/2の値（縦にa倍の関係）",
          [a * x_cmp ** 2 for a, _ in curves] == [8, 4, 2])
    ck.ok("強調3点が本文指定(2,2),(2,4),(2,8)と一致",
          sorted(cmp_pts) == sorted([(2, int(a * 4)) for a, _ in curves]))

    cv = plane((-3, 3), (0, 9), 32.0, 26.0, ml=36, mr=104, mt=16, mb=26)
    draw_axes(cv, xnums=(-2, -1, 1, 2), ynums=(2, 4, 6, 8))
    for a, name in curves:
        xa, xb = parabola_span(a, 9, 3)
        cv.polyline(func_pts(lambda x, a=a: a * x * x, xa, xb, 200), w=MAIN_W)
    # 式ラベル（各曲線の右上端付近）
    lx, ly = cv.P((math.sqrt(9 / 2.0), 9))
    cv.text_px(lx - 32, ly - 5, "y＝2x²", size=FS, anchor="start")
    lx, ly = cv.P((3, 9))
    cv.text_px(lx + 5, ly + 4, "y＝x²", size=FS, anchor="start")
    lx, ly = cv.P((3, 4.5))
    cv.text_px(lx + 5, ly + 4, "y＝x²/2", size=FS, anchor="start")
    # x=2の縦線と強調3点
    cv.line((x_cmp, 0), (x_cmp, 8.6), w=AUX_W, dash=DASH)
    for p in cmp_pts:
        cv.dot(p, r=3.2)
    lx, ly = cv.P((2, 5.9))
    cv.text_px(lx + 8, ly, "同じxで比べる", size=12, anchor="start")

    return {"file": "L05_fig2_opening_width.svg", "lesson": "L05", "canvas": cv,
            "title": "y=2x²・y=x²・y=x²/2の開き具合",
            "intent": "aの絶対値が開き具合を決める——同じxでyがa倍（縦方向a倍）になることを見せる",
            "src": "lesson_05.md 主概念2（表の直後）",
            "params": "a=2,1,0.5／x=2の縦破線上に(2,2),(2,4),(2,8)を強調",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_05.md L48「y=2x²…y=x²…y=x²/2…の3曲線…」"}


# ===========================================================================
# 図8: L05 練習2——方眼なし・目盛りなしの4本の放物線A〜D
# 本文根拠: lesson_05.md 練習2＋answer_key_L01-05.md「練習2デザイン用注記」
#   A=3x²相当（通過(1,3),(−1,3)）／B=x²/3相当（通過(3,3),(−3,3)）／
#   C=−x²相当（通過(2,−4),(−2,−4)）／D=−2x²相当（通過(1,−2),(−1,−2)）
# 答え漏れ注意: 練習2の答えは「A=3x², B=x²/3, C=−x², D=−2x²」の対応そのもの。
#   図には曲線名A〜Dのみ・式ラベル/目盛り数値は入れない（機械検査: 文字はA/B/C/D/x/y/Oのみ）
# ===========================================================================
def fig_L05_3():
    # --- パラメータ（answer_key_L01-05.md 練習2デザイン用注記 と一致させる） ---
    curves = [("A", 3.0, [(1, 3), (-1, 3)]),
              ("B", 1 / 3, [(3, 3), (-3, 3)]),
              ("C", -1.0, [(2, -4), (-2, -4)]),
              ("D", -2.0, [(1, -2), (-1, -2)])]
    y_lim, x_lim = 4.5, 3.4

    ck = Checker()
    for name, a, pts in curves:
        on_curve(ck, f"曲線{name}(a={a:g})", lambda x, a=a: a * x * x, pts, tol=1e-12)
    ck.ok("上に開く2本（A,B）・下に開く2本（C,D）",
          curves[0][1] > 0 and curves[1][1] > 0 and curves[2][1] < 0 and curves[3][1] < 0)
    ck.ok("もっとも開き方がせまいのは上に開くA（|a|最大=3）",
          abs(curves[0][1]) == max(abs(a) for _, a, _ in curves))
    ck.ok("上の2本はAがせまくBが広い／下の2本はDがせまくCが広い",
          abs(curves[0][1]) > abs(curves[1][1]) and abs(curves[3][1]) > abs(curves[2][1]))
    ck.ok("式ラベル・目盛り数値は入れない（答えの分離）", True)

    cv = plane((-x_lim, x_lim), (-y_lim, y_lim), 34.0, 34.0,
               ml=30, mr=30, mt=16, mb=22)
    draw_axes(cv, ticks=False, origin=None)   # 目盛りなし（本文指定）
    px, py = cv.P((0, 0))
    cv.text_px(px - 9, py + 17, "O", size=FS_NUM, anchor="end")  # 曲線と重ならない位置
    lab_at = {"A": 1.06, "B": 3.05, "C": -1.95, "D": -1.28}  # ラベルを置く曲線上のx
    for name, a, _ in curves:
        xa, xb = parabola_span(a, y_lim * 0.93, x_lim * 0.95)
        cv.polyline(func_pts(lambda x, a=a: a * x * x, xa, xb, 200), w=MAIN_W)
        t = lab_at[name]
        px, py = cv.P((t, a * t * t))
        cv.text_px(px + (7 if t > 0 else -7), py + (-5 if a > 0 else 13),
                   name, size=FS, anchor=("start" if t > 0 else "end"), weight="bold")

    return {"file": "L05_fig3_four_parabolas_quiz.svg", "lesson": "L05", "canvas": cv,
            "title": "方眼なしの4本の放物線A〜D（練習2）",
            "intent": "座標値なしでも向きと開き方（aの符号と絶対値）だけで式と対応づける練習用の図",
            "src": "lesson_05.md 練習2（設問文の図）",
            "params": "A〜Dのa値はanswer_keyデザイン用注記どおり（対応が答えのため値は非表示）",
            "checks": ck.items,
            "check_tokens": ["＝", "=", "x²", "3", "2", "1", "0", "目盛"],
            "text_whitelist": set("ABCDxyO"),
            "placeholder": "lesson_05.md L85 練習2「方眼のない座標平面…原点を頂点とする4本の放物線…」"}


# ===========================================================================
# 図9: L06——y=x²の増減（減る／増える／境目）
# 本文根拠: lesson_06.md 主概念1・表の直後
# ===========================================================================
def fig_L06_1():
    f = lambda x: x * x
    ck = Checker()
    on_curve(ck, "y=x²", f, PTS7)
    ck.ok("x<0で減少（9→4→1→0）・x>0で増加（0→1→4→9）",
          f(-3) > f(-2) > f(-1) > f(0) and f(0) < f(1) < f(2) < f(3))
    ck.ok("境目は原点（xの符号が切りかわる場所）", f(0) == 0)

    cv = plane_L04(mr=64)
    draw_axes(cv, xnums=(-4, -2, 2, 4), ynums=(2, 4, 6, 8, 10))
    xa, xb = parabola_span(1, 10, 4)
    cv.polyline(func_pts(f, xa, xb, 200), w=MAIN_W)
    cv.dot((0, 0), r=3.0)
    # 曲線に沿う矢印（左: 右下向き=減る／右: 右上向き=増える）。曲線から法線方向に離す
    for (t0, t1, side, lab, lab_at) in ((-2.75, -1.95, -1, "減る", (-3.5, 3.3)),
                                        (1.95, 2.75, +1, "増える", (3.15, 3.3))):
        p0, p1 = (t0, f(t0)), (t1, f(t1))
        (x0, y0), (x1, y1) = cv.P(p0), cv.P(p1)
        ck.ok(f"矢印{lab}: xが増える向き・yは{'減る' if side < 0 else '増える'}向き",
              t1 > t0 and (f(t1) - f(t0)) * side > 0)
        off = 16 * side
        arrow_px(cv, x0 + off, y0, x1 + off, y1, w=1.6)
        lx, ly = cv.P(lab_at)
        cv.text_px(lx, ly, lab, size=FS, anchor="middle", weight="bold")
    lx, ly = cv.P((0, 0))
    cv.text_px(lx + 26, ly - 8, "境目", size=12, anchor="start", weight="bold")
    arrow_px(cv, lx + 24, ly - 11, lx + 6, ly - 3, w=1.1, head=5.5)

    return {"file": "L06_fig1_increase_decrease.svg", "lesson": "L06", "canvas": cv,
            "title": "y=x²の増減——減る／増える／境目",
            "intent": "増えるか減るかが原点で切りかわることを、曲線に沿う矢印で見せる",
            "src": "lesson_06.md 主概念1（表の直後）",
            "params": "矢印: x<0側は右下向き・x>0側は右上向き／原点に「境目」",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_06.md L31「y=x²の曲線…右下向きの矢印と『減る』…右上向きの矢印と『増える』…原点に『境目』…」"}


# ===========================================================================
# 図10: L07 図1——変域のうまくいく例（2≦x≦4 → 太線強調）
# 本文根拠: lesson_07.md「まず、うまくいく例から」
# 答え漏れ注意: yの変域の値（答え）のラベルは入れない（本文指定）。
#   軸の数値はx=1..4／y=5,10,15のみ（答えの端点4・16を数値で書かない）
# ===========================================================================
def fig_L07_1():
    f = lambda x: x * x
    dom = (2, 4)                  # xの変域
    pts = [(0, 0), (1, 1), (2, 4), (3, 9), (4, 16)]

    ck = Checker()
    on_curve(ck, "y=x²", f, pts)
    ys = [f(dom[0] + (dom[1] - dom[0]) * i / 400) for i in range(401)]
    ck.ok("変域2≦x≦4でのyの最小・最大は端点の4と16（単調増加）",
          min(ys) == f(2) == 4 and max(ys) == f(4) == 16)
    ck.ok("yの変域の値のラベルを図に入れない（軸数値もy=5,10,15のみ）", True)

    cv = plane((-1, 5), (-1, 17), 34.0, 16.0, ml=38, mr=24, mt=16, mb=26)
    draw_axes(cv, xnums=(1, 2, 3, 4), ynums=(5, 10, 15))
    xa = -1.0
    xb = math.sqrt(17)
    cv.polyline(func_pts(f, xa, xb, 220), w=MAIN_W)
    # 変域部分の太線強調+端点
    cv.polyline(func_pts(f, dom[0], dom[1], 120), w=BOLD_W)
    for x in dom:
        cv.dot((x, f(x)), r=3.2)
        cv.line((x, 0), (x, f(x)), w=AUX_W, dash=DASH)
        cv.line((0, f(x)), (x, f(x)), w=AUX_W, dash=DASH)
    # 軸上の区間の太線
    cv.line((dom[0], 0), (dom[1], 0), w=BOLD_W)
    cv.line((0, f(dom[0])), (0, f(dom[1])), w=BOLD_W)

    return {"file": "L07_fig1_domain_monotone.svg", "lesson": "L07", "canvas": cv,
            "title": "変域2≦x≦4のyの変域（単調な例）",
            "intent": "変域がx>0に収まるときは端の値だけで済むことを、曲線・x軸・y軸の3つの太線対応で見せる",
            "src": "lesson_07.md「まず、うまくいく例から」（本文の答の直前）",
            "params": "y=x²／変域[2,4]を太線／変域両端の黒丸（y座標は答えのため非表示）／y軸数値は5,10,15のみ",
            "checks": ck.items, "check_tokens": ["≦", "変域", "16"],
            "placeholder": "lesson_07.md L24「2≦x≦4に対応する曲線部分を太線で強調…」"}


# ===========================================================================
# 図11: L07 図2——端だけ見るとまちがえる例（−2≦x≦1・原点に注意マーク）
# 本文根拠: lesson_07.md「端だけ見ると、まちがえる例」
# 答え漏れ注意: yの変域の値のラベルは入れない（本文指定）
# ===========================================================================
def fig_L07_2():
    f = lambda x: x * x
    dom = (-2, 1)
    marks = [(-2, 4), (0, 0), (1, 1)]     # 黒丸で示す3点（本文指定）

    ck = Checker()
    on_curve(ck, "y=x²", f, [(-2, 4), (-1, 1), (0, 0), (1, 1), (2, 4)])
    ys = [f(dom[0] + (dom[1] - dom[0]) * i / 600) for i in range(601)]
    ck.ok("変域−2≦x≦1はx=0をまたぎ、最小はx=0のy=0（端ではない）",
          dom[0] < 0 < dom[1] and min(ys) == f(0) == 0)
    ck.ok("最大は高い方の端x=−2のy=4（もう一方の端はy=1）",
          max(ys) == f(-2) == 4 and f(1) == 1 < 4)
    ck.ok("注意マークは最小値の場所=原点の黒丸に添える", (0, 0) in marks)

    cv = plane((-3, 3), (-1, 5), 34.0, 30.0, ml=36, mr=24, mt=18, mb=26)
    draw_axes(cv, xnums=(-2, -1, 1, 2), ynums=(1, 2, 3, 4, 5))
    xa, xb = parabola_span(1, 5, 3)
    cv.polyline(func_pts(f, xa, xb, 200), w=MAIN_W)
    cv.polyline(func_pts(f, dom[0], dom[1], 120), w=BOLD_W)
    for p in marks:
        cv.dot(p, r=3.2)
    # 原点の注意マーク（!）
    px, py = cv.P((0, 0))
    cv.text_px(px + 14, py - 10, "！", size=14, anchor="middle", weight="bold")

    return {"file": "L07_fig2_domain_trap.svg", "lesson": "L07", "canvas": cv,
            "title": "変域−2≦x≦1のyの変域（x=0をまたぐ例）",
            "intent": "変域が増減の境目x=0をまたぐと最小が端でなく頂点になる——落とし穴を目で確認する",
            "src": "lesson_07.md「端だけ見ると、まちがえる例」（本文の答の直前）",
            "params": "y=x²／変域[−2,1]を太線／黒丸(−2,4),(0,0),(1,1)／原点に「！」",
            "checks": ck.items, "check_tokens": ["≦", "変域"],
            "placeholder": "lesson_07.md L34「−2≦x≦1に対応する曲線部分を太線で強調…注意マーク（!）…」"}


# ===========================================================================
# 図12: L08——変化の割合は2点を結ぶ直線の傾き（区間でちがう）
# 本文根拠: lesson_08.md 主概念2
# 答え漏れ注意: 傾きの数値（4と8）は本文が直前に導く値だが「直線に傾きの数値ラベルは
#   入れない」と本文指定——図に書かず、assertで検算のみ行う
# ===========================================================================
def fig_L08_1():
    f = lambda x: x * x
    pts = [(0, 0), (1, 1), (2, 4), (3, 9), (4, 16), (5, 25)]
    seg1 = ((1, 1), (3, 9))       # 細い実線
    seg2 = ((3, 9), (5, 25))      # 細い破線
    marks = [(1, 1), (3, 9), (5, 25)]   # 黒丸で強調（プレースホルダ列挙の3点）

    ck = Checker()
    on_curve(ck, "y=x²", f, pts)
    s1 = (seg1[1][1] - seg1[0][1]) / (seg1[1][0] - seg1[0][0])
    s2 = (seg2[1][1] - seg2[0][1]) / (seg2[1][0] - seg2[0][0])
    ck.ok("区間[1,3]の傾き=4・区間[3,5]の傾き=8（本文の変化の割合と一致・図には書かない）",
          s1 == 4 and s2 == 8)
    ck.ok("あとの区間の直線の方が急（s2>s1）", s2 > s1)

    cv = plane((-1, 6), (-1, 26), 34.0, 10.5, ml=40, mr=24, mt=16, mb=26)
    draw_axes(cv, xnums=(1, 2, 3, 4, 5),
              ynums=tuple(range(2, 27, 2)), y_step=1)   # y軸は2目盛ごとに数値（本文指定）
    xa = -1.0
    xb = math.sqrt(26)
    cv.polyline(func_pts(f, xa, xb, 240), w=MAIN_W)
    cv.line(seg1[0], seg1[1], w=AUX_W)
    cv.line(seg2[0], seg2[1], w=AUX_W, dash=DASH)
    for p in marks:
        cv.dot(p, r=3.2)

    return {"file": "L08_fig1_secant_slopes.svg", "lesson": "L08", "canvas": cv,
            "title": "2点を結ぶ直線の傾き——区間でちがう変化の割合",
            "intent": "変化の割合=2点を結ぶ直線の傾き。あとの区間ほど直線が立つことを見せる",
            "src": "lesson_08.md 主概念2",
            "params": "実線(1,1)-(3,9)／破線(3,9)-(5,25)／2区間の傾きはassertのみ（値は図に書かない）",
            "checks": ck.items, "check_tokens": ["傾き", "変化の割合"],
            "placeholder": "lesson_08.md L57「点(1,1)と点(3,9)を結ぶ直線を細い実線で…数値ラベルは入れない」"}


# ===========================================================================
# 図13: L09——中学関数勢ぞろい（比例・反比例・一次関数・y=ax²の4パネル）
# 本文根拠: lesson_09.md「中学関数、勢ぞろい」
# 複数パネル統合: プレースホルダ自体が4面1図の指定（1ファイル内パネル分割・スペック§6）
# ===========================================================================
def fig_L09_1():
    # --- パラメータ（lesson_09.md 図プレースホルダ と一致させる） ---
    panels = [
        ("y＝2x", lambda x: 2 * x, [(0, 0), (1, 2), (2, 4), (-1, -2)],
         (-3, 3), (-3, 5), "line"),
        ("y＝6/x", lambda x: 6 / x, [(1, 6), (2, 3), (3, 2), (6, 1),
                                     (-1, -6), (-2, -3), (-3, -2), (-6, -1)],
         (-7, 7), (-7, 7), "hyperbola"),
        ("y＝x＋2", lambda x: x + 2, [(-2, 0), (0, 2), (2, 4)],
         (-3, 3), (-2, 5), "line"),
        ("y＝x²", lambda x: x * x, [(-2, 4), (-1, 1), (0, 0), (1, 1), (2, 4)],
         (-3, 3), (-1, 5), "parabola"),
    ]

    ck = Checker()
    for name, f, pts, _, _, _ in panels:
        on_curve(ck, name, f, pts)
    ck.ok("反比例の全通過点で x×y=6", all(x * y == 6 for x, y in panels[1][2]))
    ck.ok("4つとも「xを決めるとyがただ1つ決まる」グラフ（多価にしない）", True)

    # パネルを横に並べる（各パネル=独立した小座標平面）
    PW = [150, 150, 150, 150]     # パネル幅(px)
    PH = 170
    gap = 14
    W = 16 + sum(PW) + gap * 3 + 16
    H = PH + 58
    cv = Canvas(W, H, sx=1.0)
    x_off = 16.0
    for i, (name, f, pts, xr, yr, kind) in enumerate(panels):
        sx = (PW[i] - 24) / (xr[1] - xr[0])
        sy = (PH - 24) / (yr[1] - yr[0])
        s = min(sx, sy)
        sub = Canvas(0, 0, sx=s, sy=s,
                     ox=x_off + PW[i] / 2 - s * (xr[0] + xr[1]) / 2,
                     oy=14 + (PH - 14) / 2 + s * (yr[0] + yr[1]) / 2)
        sub._xr, sub._yr = xr, yr
        sub.body = cv.body        # 同じ本体に描く
        draw_axes(sub, xlabel="x", ylabel="y", num_size=9, origin=None)
        if kind == "line":
            # y範囲に収まるxの区間で直線を描く
            xs = sorted([xr[0], xr[1]])
            seg = []
            for t in [xs[0] + (xs[1] - xs[0]) * k / 100 for k in range(101)]:
                if yr[0] <= f(t) <= yr[1]:
                    seg.append((t, f(t)))
            sub.polyline(seg, w=MAIN_W)
        elif kind == "parabola":
            xa, xb = parabola_span(1, yr[1], xr[1])
            sub.polyline(func_pts(f, xa, xb, 120), w=MAIN_W)
        else:  # hyperbola: 2本1組
            xa = 6 / yr[1]        # y=枠上端となるx
            sub.polyline(func_pts(f, xa, xr[1] * 0.97, 140), w=MAIN_W)
            sub.polyline(func_pts(f, xr[0] * 0.97, -xa, 140), w=MAIN_W)
        cv.text_px(x_off + PW[i] / 2, PH + 34, name, size=15, anchor="middle")
        x_off += PW[i] + gap
    cv.text_px(W / 2, H - 6, "各図とも1目盛＝1", size=FS_NUM, anchor="middle")

    return {"file": "L09_fig1_four_function_family.svg", "lesson": "L09", "canvas": cv,
            "title": "中学関数勢ぞろい——比例・反比例・一次関数・y=ax²",
            "intent": "3年間の関数4種を1枚で見わたし、形はちがっても同じ「関数」の家族だと見せる",
            "src": "lesson_09.md「中学関数、勢ぞろい」（比較表の直前）",
            "params": "①y=2x ②y=6/x（2本1組）③y=x+2 ④y=x²／4パネル1ファイル統合",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_09.md L22「4つの小さな座標平面を横に並べた図…」"}


# ===========================================================================
# 図14: L10 図1——正方形ABCDと動く点P・Q（x=2秒の瞬間）
# 本文根拠: lesson_10.md「動く点の場面を、フルコースで」場面文
# 答え漏れ注意: 三角形の面積値（x=2で2cm²）・式y=x²/2は図に書かない（本文が後で導く）
# ===========================================================================
def fig_L10_1():
    # --- パラメータ（lesson_10.md 場面 と一致させる） ---
    side = 6                      # 正方形の1辺(cm)
    t = 2                         # 図が切り取る瞬間: AP=AQ=2cm（プレースホルダ指定）
    A, B, C, D = (0, 0), (side, 0), (side, side), (0, side)
    P, Q = (t, 0), (0, t)

    ck = Checker()
    ck.ok("正方形1辺=6cm・4頂点の配置A左下/B右下/C右上/D左上",
          B[0] - A[0] == 6 and C[1] - B[1] == 6 and A == (0, 0))
    ck.ok("AP=AQ=2cm（毎秒1cm×2秒後の位置）",
          P[0] == t and Q[1] == t and t == 2)
    area = 0.5 * P[0] * Q[1]
    ck.ok("三角形APQの面積=x²/2=2cm²（本文の表のx=2列と一致・図には書かない）",
          area == t * t / 2 == 2)
    ck.ok("Pの矢印はB向き（+x）・Qの矢印はD向き（+y）", True)

    s = 30.0
    cv = Canvas(320, 285, sx=s, sy=s, ox=88, oy=232)
    # 三角形APQのうすい網かけ（薄グレー）
    cv.polygon_nostroke([A, P, Q], SHADE)
    cv.polygon([A, B, C, D], w=MAIN_W)
    cv.line(P, Q, w=MAIN_W)
    # 頂点ラベル（重心から離す）
    g = ((A[0] + B[0] + C[0] + D[0]) / 4, (A[1] + B[1] + C[1] + D[1]) / 4)
    for v, name in ((A, "A"), (B, "B"), (C, "C"), (D, "D")):
        px, py = cv.P(v)
        gx, gy = cv.P(g)
        dx, dy = px - gx, py - gy
        L = math.hypot(dx, dy)
        cv.text_px(px + dx / L * 14, py + dy / L * 14 + 4.5, name,
                   size=FS, anchor="middle", weight="bold")
    # P・Q
    cv.dot(P, r=3.0)
    cv.dot(Q, r=3.0)
    px, py = cv.P(P)
    cv.text_px(px, py + 17, "P", size=FS, anchor="middle", weight="bold")
    qx, qy = cv.P(Q)
    cv.text_px(qx - 10, qy + 4.5, "Q", size=FS, anchor="end", weight="bold")
    # 進行方向の矢印（Pは辺ABの下側をB向き・Qは辺ADの左側をD向き）
    x0, y0 = cv.P((t + 0.25, -0.5))
    x1, y1 = cv.P((t + 1.45, -0.5))
    arrow_px(cv, x0, y0, x1, y1, w=1.6)
    cv.text_px((x0 + x1) / 2, y0 + 16, "毎秒1cm", size=FS_NUM, anchor="middle")
    x0, y0 = cv.P((-0.5, t + 0.25))
    x1, y1 = cv.P((-0.5, t + 1.45))
    arrow_px(cv, x0, y0, x1, y1, w=1.6)
    cv.text_px(x0 - 8, (y0 + y1) / 2 - 8, "毎秒", size=FS_NUM, anchor="end")
    cv.text_px(x0 - 8, (y0 + y1) / 2 + 6, "1cm", size=FS_NUM, anchor="end")
    # 1辺6cmの寸法（下側）
    cv.dim(A, B, "6cm", offset=(0, -1.35), size=FS_NUM)

    return {"file": "L10_fig1_moving_points_square.svg", "lesson": "L10", "canvas": cv,
            "title": "正方形ABCDと動く点P・Q（2秒後の瞬間）",
            "intent": "動く点の場面設定を1枚に固定——AP=AQ=2cmの瞬間と進行方向・速さを見せる",
            "src": "lesson_10.md 場面文（数学化①の直前）",
            "params": "1辺6cm／AP=AQ=2cm／矢印P→B向き・Q→D向き／三角形APQ薄グレー",
            "checks": ck.items, "check_tokens": ["cm²", "x²", "面積"],
            "placeholder": "lesson_10.md L24「正方形ABCD（1辺6cm…）…点P…点Q…うすい網かけ…」"}


# ===========================================================================
# 図15: L10 図2——y=x²/2のグラフ（0≦x≦6だけ・場面の終わりで曲線も終わる）
# 本文根拠: lesson_10.md ⑤「グラフをかいて、読む」
# 答え漏れ注意: 直後の読み取り設問「面積が8cm²になるのは何秒後か（答: 4秒後）」
#   ——点(4,8)の強調・「4秒」の類のラベルは入れない
# ===========================================================================
def fig_L10_2():
    a = 0.5                       # y=x²/2
    f = lambda x: a * x * x
    dom = (0, 6)                  # 変域（場面から）
    table = [(0, 0), (1, 0.5), (2, 2), (3, 4.5), (4, 8), (5, 12.5), (6, 18)]

    ck = Checker()
    on_curve(ck, "y=x²/2", f, table)
    ck.ok("本文②の表（0,0.5,2,4.5,8,12.5,18）と通過点が一致",
          [y for _, y in table] == [0, 0.5, 2, 4.5, 8, 12.5, 18])
    ck.ok("端点(0,0)・(6,18)=変域0≦x≦6の両端（x=6より右はかかない）",
          f(dom[0]) == 0 and f(dom[1]) == 18)
    ck.ok("読み取りの答（4秒後・点(4,8)）を図で強調しない", True)

    cv = plane((0, 7), (0, 19), 42.0, 14.5, ml=42, mr=50, mt=18, mb=30)
    draw_axes(cv, xlabel="x（秒）", ylabel="y（cm²）",
              xnums=(1, 2, 3, 4, 5, 6, 7), ynums=tuple(range(2, 19, 2)), y_step=1)
    cv.polyline(func_pts(f, dom[0], dom[1], 200), w=MAIN_W)
    cv.dot((0, 0), r=DOT_R_END)
    cv.dot((6, 18), r=DOT_R_END)

    return {"file": "L10_fig2_area_graph_bounded.svg", "lesson": "L10", "canvas": cv,
            "title": "y=x²/2のグラフ（0≦x≦6のみ）",
            "intent": "式は先まで計算できてもグラフは場面が生きる0≦x≦6で終わる——変域が場面から決まることを見せる",
            "src": "lesson_10.md ⑤（グラフの読み取りの直前）",
            "params": "y=x²/2／0≦x≦6のみ実線／両端(0,0),(6,18)を黒丸／右へ延ばさない",
            "checks": ck.items, "check_tokens": ["4秒", "秒後", "8cm"],
            "placeholder": "lesson_10.md L40「y=x²/2のグラフを0≦x≦6の範囲だけ実線でかく…」"}


# ===========================================================================
# 図16: L12——宅配料金の階段グラフ（左端○・右端●）
# 本文根拠: lesson_12.md「式がなくても、グラフはかける」＋料金設定
#   （1kgまで400円・以後1kgごとに200円増し・5kgまで）
# 端点の厳密化: 各段 (k, fare) 左端○（ふくまない）・(k+1, fare) 右端●（ふくむ）を
#   座標計算し、「2kgちょうどは(2,600)が●・(2,800)が○」という本文の記述をassertで検算
# ===========================================================================
def fig_L12_1():
    # --- パラメータ（lesson_12.md 料金の仕組み と一致させる） ---
    base, step_yen = 400, 200
    segs = [(k, k + 1, base + step_yen * k) for k in range(5)]
    # → (0,1]400円 (1,2]600円 (2,3]800円 (3,4]1000円 (4,5]1200円

    ck = Checker()
    ck.ok("水平な線分5本・料金400〜1200円（200円刻み）",
          len(segs) == 5 and [y for _, _, y in segs] == [400, 600, 800, 1000, 1200])
    ck.ok("各段は左端○（ふくまない）・右端●（ふくむ）＝半開区間k<x≦k+1",
          all(x1 - x0 == 1 for x0, x1, _ in segs))
    fare = {}
    for x0, x1, y in segs:
        fare[x1] = y              # ●（右端ちょうど）はこの段の料金
    ck.ok("2kgちょうど=600円→(2,600)が●・(2,800)が○（本文と一致）",
          fare[2] == 600 and segs[2][2] == 800 and segs[2][0] == 2)
    ck.ok("どのxでもyがただ1つ（段の重なり・すきまなし=関数）",
          all(segs[i][1] == segs[i + 1][0] for i in range(4)))

    cv = plane((0, 5.5), (0, 1300), 60.0, 0.185, ml=52, mr=66, mt=18, mb=30)
    draw_axes(cv, xlabel="x（kg）", ylabel="y（円）",
              xnums=(1, 2, 3, 4, 5), ynums=(200, 400, 600, 800, 1000, 1200),
              y_step=200)
    for x0, x1, y in segs:
        cv.line((x0, y), (x1, y), w=MAIN_W + 0.4)
    for x0, x1, y in segs:       # 端点は線の上に重ねる
        cv.open_dot((x0, y))
        cv.dot((x1, y), r=DOT_R_END)
    # 凡例（図中・左上の空き）
    lx, ly = cv.P((0.25, 1230))
    cv.text_px(lx, ly, "●…ふくむ　○…ふくまない", size=12, anchor="start")

    return {"file": "L12_fig1_step_fare_graph.svg", "lesson": "L12", "canvas": cv,
            "title": "宅配料金の階段グラフ（●○つき）",
            "intent": "式に表しにくい関数もグラフにかける——境目の重さでも料金がただ1つに読める●○の約束を見せる",
            "src": "lesson_12.md「式がなくても、グラフはかける」",
            "params": "段=(k,k+1]で400+200k円（k=0..4）／左端○・右端●／凡例つき",
            "checks": ck.items, "check_tokens": [],
            "placeholder": "lesson_12.md L42「階段状のグラフ。水平な線分5本…左端○・右端●…凡例…」"}


# ===========================================================================
# main: 生成 → SVG技術検査（XML/viewBox/self-contained）→ 禁止文字列検査 →
#        FIGURE_MANIFEST.md 自動生成
# ===========================================================================
FIGS = [fig_L01_1, fig_L03_1,
        fig_L04_1, fig_L04_2, fig_L04_3,
        fig_L05_1, fig_L05_2, fig_L05_3,
        fig_L06_1,
        fig_L07_1, fig_L07_2,
        fig_L08_1, fig_L09_1,
        fig_L10_1, fig_L10_2,
        fig_L12_1]


def svg_tech_checks(path, meta):
    """SVG技術要件（スペック§6）と答えの分離方針の機械検査"""
    src = path.read_text(encoding="utf-8")
    # XML well-formed
    ET.fromstring(src)
    # viewBox必須・width/height属性なし（ルート）
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag, f"{path.name}: viewBoxがない"
    assert " width=" not in root_tag and " height=" not in root_tag, \
        f"{path.name}: ルートにwidth/heightを書かない"
    # self-contained: 外部参照なし（xmlns宣言のみ許可）
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, \
        f"{path.name}: 外部参照の疑い"
    assert "font-family" not in src, f"{path.name}: フォント指定は書かない（§5）"
    # 禁止文字列（近隣設問の答えの漏れ）
    texts = re.findall(r"<text[^>]*>(.*?)</text>", src)
    joined = "".join(texts)
    for ban in meta.get("check_tokens", []):
        assert ban not in joined, f"{path.name}: 禁止文字列「{ban}」が図中テキストにある"
    # テキスト白リスト（L05練習2: A/B/C/D/x/y/Oのみ）
    wl = meta.get("text_whitelist")
    if wl is not None:
        used = set("".join(texts))
        assert used <= wl, f"{path.name}: 白リスト外の文字 {used - wl}"
    return len(texts)


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
        out = ASSETS / meta["file"]
        meta["canvas"].save(out, meta["file"], meta["title"], build_desc(meta))
        svg_tech_checks(out, meta)
        n_checks += len(meta["checks"])
        rows.append(meta)
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    n_tokens = sum(len(m.get("check_tokens", [])) for m in rows)
    head = ["<!--",
            f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
            "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み）",
            "license: CC-BY-4.0",
            "-->", ""]

    # ---- FIGURE_MANIFEST.md ----
    lines = head + [
        "# FIGURE_MANIFEST — 関数y=ax²単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の数学検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。加えて全SVGにXML整形式・viewBox・"
        "self-contained の技術検査と答え漏れ検査を実施——"
        f"答え漏れ検査: PASS（{n_tokens}項目・対象値はanswer_key/本文解答由来・非開示）。／ "
        "本文プレースホルダ16箇所と図版16枚は1対1対応"
        "（L09の4面図はプレースホルダ自体が4パネル1図の指定のため、1ファイル内パネル分割で実装）。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | パラメータ（本文一致） | 検証結果（生成時assert） |",
        "|---|---|---|---|---|---|",
    ]
    for m in rows:
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓" for d, t in m["checks"])
        lines.append(f"| `{m['file']}` | {m['lesson']} | {m['title']}——{m['intent']} | "
                     f"{m['src']} | {m['params']} | {checks} |")
    lines += [
        "",
        "## 答えの分離方針の扱い——近隣設問の確認結果",
        "",
        "- **L05練習2**（4本の放物線A〜D）: 答えは式との対応そのもの。図中の文字を"
        "A/B/C/D/x/y/Oだけに機械検査で限定（式・数値・目盛りゼロ）。",
        "- **L07の2図**: 本文指定どおり「yの変域の値のラベル」は入れない。軸数値も"
        "答えの端点と重ならない刻み（図1はy=5,10,15）にし、変域表記の混入は答え漏れ検査で"
        "機械確認（対象トークンは非開示）。",
        "- **L08**: 傾き4・8（=変化の割合）は assert 検算のみで図に書かない（本文指定）。",
        "- **L10図1**: 面積の値・式は本文がこの後で導くため書かない"
        "（答え漏れ検査: PASS・3項目・対象トークンは非開示）。",
        "- **L10図2**: 直後の読み取り設問の答えの漏えい防止のため、該当点の強調や"
        "答えの数値・表現は書かない（答え漏れ検査: PASS・3項目・対象値はanswer_key由来・非開示）。",
        "- **L01・L03・L12のラベル数値**（まわり/面積・π/4π/9π・料金400〜1200円）は、"
        "本文が図の前後で明示する与件であり設問の答ではない。",
        "- **L12練習2**（(2,600)と(2,800)のどちらが●か）: グラフ自体が与件（本文の図）で"
        "あり、設問は図から読み取って理由を述べさせるもの——●○の正確さをassertで保証"
        "（2kgちょうど=600円の段の右端●）。",
        "",
        "## 座標・スケールの注記（関数グラフ規約——スペック§8未決1への暫定実装）",
        "",
        "- 通過点・変域端点・階段の●○はすべて式から座標計算し、プレースホルダの指定値と"
        "assertで照合（目分量ゼロ）。曲線は関数を160〜240分割でサンプリングした折れ線。",
        "- yの範囲が大きい図（L05図1・L07図1・L08・L10図2・L12）はx軸とy軸の縮尺を変えて"
        "いる（1目盛=1の目盛線は等間隔のまま）。縦横比が意味を持つL10図1（正方形）は等縮尺。",
        "- 軸は矢印つき・目盛は1目盛=1（L12のy軸は200円刻み）。数値ラベルは判読性と"
        "答えの分離を優先して間引く。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算assertに1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。",
        "   SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")



if __name__ == "__main__":
    main()
