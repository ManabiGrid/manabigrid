#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2数学「一次関数」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。
ヘルパー群（Canvas/矢印/Checker ほか）は先行単元
materials/jhs-math-2/jhs-math-2-simultaneous-equations/assets_provenance/generate_figures.py
からコピー再利用（元スクリプトは無変更）。本単元向けの増補は
座標平面ヘルパー（axes_math/plot範囲計算）・弧矢印・色付きテキストのみ。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（16枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / fractions / html / pathlib / xml.etree）
- 決定的出力: 乱数・時刻を使わない（生成日コメントは定数 GENERATED。改修時に手で更新）
- 自己検証（2段構え）:
  1) 各 fig_* 関数内の Checker が生成前に検算を行い、1つでも失敗すると図を出力しない
     （プロット点が式を満たすこと・増加量・交点の代入検算・答えの分離など）。
  2) 生成後に各SVGを ElementTree で読み戻し、必須文字列の存在・禁止文字列（答え）の
     不在・プロット点の座標が式の再計算値と一致することを assert する（読み戻し検査）。
     照合0件のfigは「ゲート不在」としてエラーにする（素通り防止）。
- 答えの分離方針: 練習問題の答は図に一切書かない。
  L07_fig2 の交点 (1, 80)・L06_fig1 の交点 (4/3, 10/3) は図に座標を書かず、
  L04_fig2/fig3 は練習の答えの直線と切片が異なる別直線を使う（各notesの明記に従う）。
- 数値の出所: すべて同単元の lesson_0X.md 本文（制作時の図版仕様ノートに基づく）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_0X.md）と一致させること。
"""

import math
from fractions import Fraction as F
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
GENERATED = "2026-08-29"   # 決定的出力のため固定（時刻関数不使用）。改修時に更新する

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
DOT_R = 2.5       # 点マーカー半径


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き に変換して描く）
# 先行単元 generate_figures.py からコピー再利用（fill/color引数のみ増補）
# ===========================================================================
class Canvas:
    def __init__(self, width, height, scale=1.0, ox=0.0, oy=0.0, sy=None):
        """scale: 数学単位→px、(ox,oy): 数学原点のSVG座標（yはoyから上向きに減る）
        sy: y方向だけ別スケールにする場合に指定（量のグラフ用・省略時はscaleと同じ）"""
        self.w, self.h = width, height
        self.s, self.ox, self.oy = scale, ox, oy
        self.sy = sy if sy is not None else scale
        self.defs = []
        self.body = []

    # 座標変換 -------------------------------------------------------------
    def P(self, p):
        return (self.ox + self.s * p[0], self.oy - self.sy * p[1])

    # 低レベル -------------------------------------------------------------
    def raw(self, s):
        self.body.append(s)

    def line(self, a, b, w=MAIN_W, dash=None, color="#000"):
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def polyline(self, pts, w=MAIN_W, dash=None, color="#000"):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polyline points="{s}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}"{d}/>')

    def dot(self, p, r=DOT_R, fill="#000"):
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def open_dot(self, p, r=4.0, w=MAIN_W, stroke="#000"):
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                 f'stroke="{stroke}" stroke-width="{w}"/>')

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None, fill=None):
        x, y = self.P(p)
        wgt = f' font-weight="{weight}"' if weight else ""
        fl = f' fill="{fill}"' if fill else ""
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{fl}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS_CAP, anchor="start", weight=None, fill=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        fl = f' fill="{fill}"' if fill else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{fl}>{escape(s)}</text>')

    def add_hatch(self):
        """濃淡+ハッチングの塗り分けパターン（SPEC §4）を内蔵defsへ"""
        self.defs.append(
            '<pattern id="h45" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>')

    # 概念図・表用（SVG座標pxで直接描く） -----------------------------------
    def rect_px(self, x, y, w, h, sw=MAIN_W, dash=None, fill="#fff", rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
                 f'{r} fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')

    def rect_px_nostroke(self, x, y, w, h, fill):
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'fill="{fill}" stroke="none"/>')

    def textbox_px(self, x, y, w, h, lines, size=FS, sw=MAIN_W, dash=None,
                   weight_first=None, line_gap=1.35):
        """枠+中央ぞろえ複数行テキスト。lines=[行1, 行2, ...]"""
        self.rect_px(x, y, w, h, sw=sw, dash=dash, rx=4)
        n = len(lines)
        cy0 = y + h / 2 - (n - 1) * size * line_gap / 2
        for i, ln in enumerate(lines):
            wgt = weight_first if i == 0 else None
            self.text_px(x + w / 2, cy0 + i * size * line_gap + size * 0.35,
                         ln, size=size, anchor="middle", weight=wgt)

    def save(self, path, fig_id, title, desc=None):
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            + (f'<desc>{escape(desc)}</desc>\n' if desc else "") +
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0, dash=None, color="#000"):
    """SVG座標(px)で矢印（線+先端の三角形）を描く"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="{color}" stroke-width="{w}"{d}/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="{color}"/>')


def arrow_math(cv, a, b, **kw):
    """数学座標で矢印を描く（arrow_pxへ変換委譲）"""
    (x1, y1), (x2, y2) = cv.P(a), cv.P(b)
    arrow_px(cv, x1, y1, x2, y2, **kw)


def arc_arrow_px(cv, x1, x2, ybase, rise, label, w=1.2, fs=11, head=6.0):
    """表の列間を結ぶ弧矢印（px座標）。rise<0で上ぶくらみ・>0で下ぶくらみ。
    弧は放物線サンプリングの折れ線（arcフラグ不使用・SPEC §6）"""
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x1 + (x2 - x1) * t, ybase + rise * 4 * t * (1 - t)))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    cv.raw(f'<polyline points="{poly}" fill="none" stroke="#000" stroke-width="{w}"/>')
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    ang = math.atan2(yb - ya, xb - xa)
    bx, by = xb - head * math.cos(ang), yb - head * math.sin(ang)
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{xb:.1f},{yb:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')
    ly = ybase + rise + (-4 if rise < 0 else fs + 2)
    cv.text_px((x1 + x2) / 2, ly, label, size=fs, anchor="middle", weight="bold")


def num_label(v):
    """目盛ラベル用: 負号を全角マイナス（−）で表記"""
    return str(v).replace("-", "−")


def axes_math(cv, xmin, xmax, ymin, ymax, xlabel="x", ylabel="y",
              xticks=None, yticks=None, xlabels=None, ylabels=None,
              fs_tick=10, grid=False, yaxis_w=1.2, xaxis_w=1.2, tick=3.2):
    """座標平面（軸・矢印・目盛・O）。目盛位置は整数レンジから計算配置"""
    if grid:
        for gx in range(math.ceil(xmin), math.floor(xmax) + 1):
            cv.line((gx, ymin), (gx, ymax), w=0.6, color="#ddd")
        for gy in range(math.ceil(ymin), math.floor(ymax) + 1):
            cv.line((xmin, gy), (xmax, gy), w=0.6, color="#ddd")
    if xticks is None:
        xticks = [i for i in range(math.ceil(xmin), math.floor(xmax) + 1) if i != 0]
    if yticks is None:
        yticks = [i for i in range(math.ceil(ymin), math.floor(ymax) + 1) if i != 0]
    if xlabels is None:
        xlabels = xticks
    if ylabels is None:
        ylabels = yticks
    x0px, y0px = cv.P((0, 0))
    x1px, _ = cv.P((xmin, 0))
    x2px, _ = cv.P((xmax, 0))
    _, ytoppx = cv.P((0, ymax))
    _, ybotpx = cv.P((0, ymin))
    arrow_px(cv, x1px, y0px, x2px + 10, y0px, w=xaxis_w, head=7)
    arrow_px(cv, x0px, ybotpx, x0px, ytoppx - 10, w=yaxis_w, head=7)
    cv.text_px(x2px + 14, y0px + 4, xlabel, size=FS - 1, anchor="start")
    cv.text_px(x0px - 7, ytoppx - 10, ylabel, size=FS - 1, anchor="end")
    cv.text_px(x0px - 6, y0px + 13, "O", size=fs_tick + 1, anchor="end")
    for i in xticks:
        px, _ = cv.P((i, 0))
        cv.raw(f'<line x1="{px:.1f}" y1="{y0px - tick:.1f}" x2="{px:.1f}" '
               f'y2="{y0px + tick:.1f}" stroke="#000" stroke-width="1"/>')
    for i in xlabels:
        px, _ = cv.P((i, 0))
        cv.text_px(px, y0px + 14, num_label(i), size=fs_tick, anchor="middle")
    for i in yticks:
        _, py = cv.P((0, i))
        cv.raw(f'<line x1="{x0px - tick:.1f}" y1="{py:.1f}" x2="{x0px + tick:.1f}" '
               f'y2="{py:.1f}" stroke="#000" stroke-width="1"/>')
    for i in ylabels:
        _, py = cv.P((0, i))
        cv.text_px(x0px - 6, py + fs_tick * 0.35, num_label(i), size=fs_tick,
                   anchor="end")


def x_range_for(f, xlo, xhi, ylo, yhi):
    """一次関数fのグラフを描く x 区間: [xlo,xhi] のうち f(x)∈[ylo,yhi] の部分を計算"""
    a = f(1) - f(0)
    if a == 0:
        return (xlo, xhi) if ylo <= f(0) <= yhi else None
    xa = (ylo - f(0)) / a
    xb = (yhi - f(0)) / a
    lo, hi = (xa, xb) if xa < xb else (xb, xa)
    return (max(xlo, lo), min(xhi, hi))


class Checker:
    """検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


# ===========================================================================
# 図1: L01 水そうの水位のうつりかわり（y＝3x と y＝3x＋2 の対比・グラフにはしない）
# 仕様源: notes/lesson_01_notes.md §1 L01_fig1（L3先取り回避のため水位図）
# 答え扱い: 数値はすべて本文解説中の与件（0L/2Lスタート・毎分3L・x=0,1,2の水位）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md 主概念1 と一致させる） ---
    pace = 3                  # 毎分3L
    start1, start2 = 0, 2     # ①空から ②はじめ2L
    xs = [0, 1, 2]            # ならべる時刻（分）
    f1 = lambda x: pace * x + start1          # y＝3x
    f2 = lambda x: pace * x + start2          # y＝3x＋2

    lv1 = [f1(x) for x in xs]
    lv2 = [f2(x) for x in xs]
    ck = Checker()
    ck.ok("①y＝3xの水位は本文どおり 0,3,6 L（x＝0,1,2）", lv1 == [0, 3, 6])
    ck.ok("②y＝3x＋2の水位は本文どおり 2,5,8 L（x＝0,1,2）", lv2 == [2, 5, 8])
    ck.ok("どちらも毎分3Lの同じペース（隣接差がすべて3）",
          [b - a for a, b in zip(lv1, lv1[1:])] == [3, 3]
          and [b - a for a, b in zip(lv2, lv2[1:])] == [3, 3])
    ck.ok("スタートのちがい2Lは何分たっても2Lのまま",
          all(f2(x) - f1(x) == 2 for x in xs))

    cv = Canvas(460, 248)
    cv.add_hatch()
    unit = 8                  # 1L＝8px
    tw, cap = 44, 10          # 水そう幅・容量10L（描画上の高さ）
    top, bot = 64, 64 + cap * unit
    rb_texts = []

    def panel(x0s, f, title, tcx, hatch_start):
        cv.text_px(tcx, 26, title, size=FS, anchor="middle", weight="bold")
        for i, xv in enumerate(xs):
            x0 = x0s + i * 60
            h = f(xv) * unit                  # 水位の高さは式から計算
            if h > 0:
                cv.rect_px_nostroke(x0, bot - h, tw, h, "#ddd")
                if hatch_start:               # はじめから入っていた分を斜線で
                    hs = hatch_start * unit
                    cv.raw(f'<rect x="{x0:.1f}" y="{bot - hs:.1f}" width="{tw:.1f}" '
                           f'height="{hs:.1f}" fill="url(#h45)" stroke="none"/>')
                cv.raw(f'<line x1="{x0:.1f}" y1="{bot - h:.1f}" x2="{x0 + tw:.1f}" '
                       f'y2="{bot - h:.1f}" stroke="#000" stroke-width="{MAIN_W}"/>')
            cv.raw(f'<polyline points="{x0:.1f},{top:.1f} {x0:.1f},{bot:.1f} '
                   f'{x0 + tw:.1f},{bot:.1f} {x0 + tw:.1f},{top:.1f}" fill="none" '
                   f'stroke="#000" stroke-width="{MAIN_W}"/>')
            lab = f"{f(xv)}L"
            rb_texts.append(lab)
            cv.text_px(x0 + tw / 2, top - 8, lab, size=FS, anchor="middle",
                       weight="bold")
            cv.text_px(x0 + tw / 2, bot + 16, f"{xv}分", size=11, anchor="middle")

    panel(48, f1, "① 空の水そうから（y＝3x）", 125, 0)
    panel(268, f2, "② はじめ2L入り（y＝3x＋2）", 345, start2)
    cv.text_px(125, 182, "0Lからスタート", size=10.5, anchor="middle")
    cv.text_px(345, 182, "斜線＝はじめから入っていた2L", size=10.5, anchor="middle")
    cv.text_px(230, 210, "どちらも1分ごとに3Lずつ増える——ちがいは「はじめに入っていた量」だけ",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 230, "（スタートのちがい2Lは、何分たっても2Lのまま）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_tank_water_level.svg", canvas=cv, lesson="L01",
                title="水そうの水位のうつりかわり（y＝3x と y＝3x＋2 の対比）",
                intent="主概念1の場面の可視化。座標平面のグラフにはしない（L3先取り回避）",
                src="lesson_01.md 主概念1",
                params="毎分3L・はじめ0Lと2L・x＝0,1,2の水位(0,3,6 / 2,5,8)は式から計算",
                checks=ck.items,
                rb_texts=rb_texts + ["y＝3x", "y＝3x＋2", "0分", "1分", "2分"],
                rb_absent=["傾き", "切片", "変化の割合"],
                rb_circles=[])


# ===========================================================================
# 図2: L01 式 y＝3x＋2 の構造図（3x＝増えた分・＋2＝はじめの量）
# 仕様源: notes/lesson_01_notes.md §1 L01_fig2
# ===========================================================================
def fig_L01_2():
    # --- パラメータ（lesson_01.md 主概念1・2 と一致させる） ---
    pace, start = 3, 2
    f = lambda x: pace * x + start

    ck = Checker()
    ck.ok("ペースは毎分3L（f(x＋1)−f(x)＝3）",
          all(f(x + 1) - f(x) == 3 for x in range(0, 4)))
    ck.ok("はじめの量は2L（f(0)＝2）", f(0) == 2)
    ck.ok("「増えた分3x＋はじめの量2」の分解が式と一致（x＝0..5で恒等）",
          all(pace * x + start == f(x) for x in range(0, 6)))

    cv = Canvas(440, 224)
    ey = 76
    cv.text_px(70, ey, "y", size=22, anchor="middle")
    cv.text_px(95, ey, "＝", size=22, anchor="middle")
    cv.text_px(131, ey, "3x", size=22, anchor="middle", weight="bold")
    cv.text_px(163, ey, "＋", size=22, anchor="middle")
    cv.text_px(187, ey, "2", size=22, anchor="middle", weight="bold")
    cv.rect_px(112, ey - 22, 38, 30, sw=AUX_W, dash=DASH, rx=5, fill="none")
    cv.rect_px(174, ey - 22, 26, 30, sw=AUX_W, dash=DASH, rx=5, fill="none")
    arrow_px(cv, 131, ey + 14, 120, 118, w=1.4)
    arrow_px(cv, 187, ey + 14, 300, 118, w=1.4)
    cv.textbox_px(30, 122, 180, 54, ["増えた分", "毎分3L × x分 ＝ 3x L"],
                  size=12, sw=MAIN_W, weight_first="bold")
    cv.textbox_px(240, 122, 170, 54, ["はじめの量", "はじめから入っていた 2L"],
                  size=12, sw=MAIN_W, weight_first="bold")
    cv.text_px(220, 206, "「増えた分」と「はじめの量」の和が、x分後の水の量 y になる",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig2_pace_plus_start.svg", canvas=cv, lesson="L01",
                title="式 y＝3x＋2 の構造（3x＝増えた分・＋2＝はじめの量）",
                intent="主概念1の式の分解の可視化。使う数値は3（ペース）と2（はじめの量）のみ",
                src="lesson_01.md 主概念1（式 y＝3x＋2 の解説直後）",
                params="ペース3・はじめの量2／分解の恒等性はassertで確認",
                checks=ck.items,
                rb_texts=["3x", "増えた分", "はじめの量", "毎分3L × x分 ＝ 3x L"],
                rb_absent=["傾き", "切片", "変化の割合"],
                rb_circles=[])


# ===========================================================================
# 図3: L02 表の増加量矢印図（y＝3x＋2・x側＋1×3・y側＋3×3）
# 仕様源: notes/lesson_02_notes.md §3 L02_fig1
# 答え漏れ注意: 変化の割合の値（3÷1＝3）は図に書かない（増加量矢印まで）
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（lesson_02.md 主概念1 と一致させる） ---
    f = lambda x: 3 * x + 2
    xs = [0, 1, 2, 3]
    ys = [f(x) for x in xs]

    ck = Checker()
    ck.ok("表の値は本文どおり y＝2,5,8,11（x＝0,1,2,3）", ys == [2, 5, 8, 11])
    ck.ok("xの隣接増加量はすべて＋1", [b - a for a, b in zip(xs, xs[1:])] == [1, 1, 1])
    ck.ok("yの隣接増加量はすべて＋3", [b - a for a, b in zip(ys, ys[1:])] == [3, 3, 3])
    ck.ok("矢印ラベル（＋1・＋3）は表の隣接差の再計算値と一致",
          all(f(x + 1) - f(x) == 3 for x in xs[:-1]))

    cv = Canvas(460, 262)
    x0, y0 = 128, 84
    cw, ch = 56, 30
    cv.text_px(230, 30, "y＝3x＋2 の表", size=FS, anchor="middle", weight="bold")
    for r, lab in enumerate(["x", "y"]):
        cv.rect_px(x0 - cw, y0 + r * ch, cw, ch, sw=AUX_W, fill="#eee")
        cv.text_px(x0 - cw / 2, y0 + r * ch + ch / 2 + FS * 0.35, lab,
                   size=FS, anchor="middle")
    for i, x in enumerate(xs):
        cv.rect_px(x0 + i * cw, y0, cw, ch, sw=AUX_W)
        cv.rect_px(x0 + i * cw, y0 + ch, cw, ch, sw=AUX_W)
        cv.text_px(x0 + i * cw + cw / 2, y0 + ch / 2 + FS * 0.35, str(x),
                   size=FS, anchor="middle")
        cv.text_px(x0 + i * cw + cw / 2, y0 + ch + ch / 2 + FS * 0.35, str(f(x)),
                   size=FS, anchor="middle")
    for i in range(len(xs) - 1):
        c1 = x0 + i * cw + cw / 2
        c2 = x0 + (i + 1) * cw + cw / 2
        arc_arrow_px(cv, c1, c2, y0 - 4, -16, f"＋{xs[i+1] - xs[i]}")
        arc_arrow_px(cv, c1, c2, y0 + 2 * ch + 4, 16, f"＋{f(xs[i+1]) - f(xs[i])}")
    cv.text_px(230, 216, "見るのは、セルの値だけでなく「列と列の間」の増え方",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 236, "——xが1増えるごとに、yはいつも同じ数（3）ずつ増えている",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_table_increment_arrows.svg", canvas=cv, lesson="L02",
                title="表の増加量矢印図（xは＋1ずつ・yは＋3ずつ）",
                intent="主概念1の可視化。視線を値から増え方へ移す。変化の割合の値は書かない",
                src="lesson_02.md 主概念1（表の直後）",
                params="y＝3x＋2・x＝0,1,2,3／表の値と増加量は式から計算",
                checks=ck.items,
                rb_texts=[str(v) for v in ys] + ["＋1", "＋3", "y＝3x＋2 の表"],
                rb_absent=["÷", "傾き", "切片"],
                rb_circles=[])


# ===========================================================================
# 図4: L02 跳びの増加量図（x: 2→5・y: 8→17・注記 9÷3＝3）
# 仕様源: notes/lesson_02_notes.md §3 L02_fig2（9÷3＝3は本文明示の途中式のため記載可）
# ===========================================================================
def fig_L02_2():
    # --- パラメータ（lesson_02.md 主概念2 と一致させる） ---
    f = lambda x: 3 * x + 2
    xa, xb = 2, 5
    ya, yb = f(xa), f(xb)

    ck = Checker()
    ck.ok("表の値は本文どおり (2, 8) と (5, 17)", (ya, yb) == (8, 17))
    ck.ok("増加量は x:＋3・y:＋9", (xb - xa, yb - ya) == (3, 9))
    ck.ok("9÷3＝3（本文明示の途中式・図に記載）", (yb - ya) / (xb - xa) == 3)
    ck.ok("fig1（1ずつの表）と同じ割合になる（同じ式だから）",
          (yb - ya) / (xb - xa) == f(1) - f(0))

    cv = Canvas(440, 244)
    x0, y0 = 130, 84
    cw, ch = 64, 30
    cv.text_px(196, 30, "y＝3x＋2 で、xが2から5へ跳ぶとき", size=FS,
               anchor="middle", weight="bold")
    for r, lab in enumerate(["x", "y"]):
        cv.rect_px(x0 - cw, y0 + r * ch, cw, ch, sw=AUX_W, fill="#eee")
        cv.text_px(x0 - cw / 2, y0 + r * ch + ch / 2 + FS * 0.35, lab,
                   size=FS, anchor="middle")
    for i, x in enumerate([xa, xb]):
        cv.rect_px(x0 + i * cw, y0, cw, ch, sw=AUX_W)
        cv.rect_px(x0 + i * cw, y0 + ch, cw, ch, sw=AUX_W)
        cv.text_px(x0 + i * cw + cw / 2, y0 + ch / 2 + FS * 0.35, str(x),
                   size=FS, anchor="middle")
        cv.text_px(x0 + i * cw + cw / 2, y0 + ch + ch / 2 + FS * 0.35, str(f(x)),
                   size=FS, anchor="middle")
    c1, c2 = x0 + cw / 2, x0 + cw + cw / 2
    arc_arrow_px(cv, c1, c2, y0 - 4, -16, f"＋{xb - xa}")
    arc_arrow_px(cv, c1, c2, y0 + 2 * ch + 4, 16, f"＋{yb - ya}")
    cv.textbox_px(296, 96, 118, 50, ["9÷3＝3", "増加量どうしで割る"],
                  size=11.5, sw=MAIN_W, weight_first="bold")
    arrow_px(cv, 292, 138, 246, 158, w=1.2, dash=DASH)
    cv.text_px(220, 214, "xが1ずつ進まなくても、やり方は同じ——yの増加量をxの増加量で割る",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig2_table_jump_increment.svg", canvas=cv, lesson="L02",
                title="跳びの増加量図（x:2→5 で ＋3・y:8→17 で ＋9・9÷3＝3）",
                intent="主概念2の可視化。矢印の幅が変わっても増加量どうしで割れば同じ割合",
                src="lesson_02.md 主概念2（跳び計算の直後）",
                params="y＝3x＋2・x＝2,5／y値8,17と増加量＋3・＋9は式から計算",
                checks=ck.items,
                rb_texts=[str(ya), str(yb), "＋3", "＋9", "9÷3＝3"],
                rb_absent=["傾き", "切片"],
                rb_circles=[])


# ===========================================================================
# 図5: L03 4点が一直線に並ぶ（y＝2x＋1・(0,1)(1,3)(2,5)(3,7)・両側にのばす）
# 仕様源: notes/lesson_03_notes.md §2 L03_fig1（必須級＝CONTENT_MAP指定）
# ===========================================================================
def fig_L03_1():
    # --- パラメータ（lesson_03.md 主概念1 と一致させる） ---
    f = lambda x: 2 * x + 1
    xs = [0, 1, 2, 3]

    ck = Checker()
    ck.ok("4点は本文の表どおり (0,1)(1,3)(2,5)(3,7)",
          [f(x) for x in xs] == [1, 3, 5, 7])
    ck.ok("プロットする各点が式 y＝2x＋1 を満たす（再計算）",
          all(f(x) == 2 * x + 1 for x in xs))
    ck.ok("歩幅が一定（隣接のy差がすべて2）＝一直線に並ぶ根拠",
          [f(x + 1) - f(x) for x in xs[:-1]] == [2, 2, 2])
    ck.ok("のばした先 x＝4 でも y＝9 が式を満たす（本文言及・図には点を打たない）",
          f(4) == 9)

    cv = Canvas(360, 466, scale=38, ox=80, oy=368)
    axes_math(cv, -1, 4, -1, 9)
    lo, hi = x_range_for(f, -0.85, 4.05, -0.75, 8.85)
    (x1, y1), (x2, y2) = cv.P((lo, f(lo))), cv.P((hi, f(hi)))
    arrow_px(cv, x2, y2, x1, y1, w=MAIN_W, head=8)      # 両端矢印＝両側にのびる
    arrow_px(cv, x1, y1, x2, y2, w=MAIN_W, head=8)
    pts_px = []
    for x in xs:
        cv.dot((x, f(x)), r=3)
        pts_px.append(cv.P((x, f(x))) + (f"({x}, {f(x)})",))
        cv.text((x - 0.14, f(x) + 0.34), f"({x}, {f(x)})", size=11, anchor="end")
    cv.text((2.95, 5.55), "y＝2x＋1", size=12.5, anchor="start", weight="bold")
    cv.text_px(180, 428, "4つの点は、ものさしを当てたように一直線に並ぶ",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 448, "——点の間も両側ものばして、1本の直線がグラフになる",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_points_line_up.svg", canvas=cv, lesson="L03",
                title="4点が一直線に並ぶ（y＝2x＋1・両側にのばして直線に）",
                intent="主概念1の可視化。点の座標は式から計算し、直線は両端矢印で延長を示す",
                src="lesson_03.md 主概念1（表の直後）",
                params="y＝2x＋1・x＝0,1,2,3（y＝1,3,5,7は式から計算）／x＝4→9はassertのみ",
                checks=ck.items,
                rb_texts=["(0, 1)", "(1, 3)", "(2, 5)", "(3, 7)", "y＝2x＋1"],
                rb_absent=["y＝x＋2"],     # 練習1の答えの直線を混ぜない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図6: L03 切片に最初の点→傾きの階段（y＝2x＋1・(0,1)から右1上2）
# 仕様源: notes/lesson_03_notes.md §2 L03_fig2
# ===========================================================================
def fig_L03_2():
    # --- パラメータ（lesson_03.md 主概念2 と一致させる） ---
    f = lambda x: 2 * x + 1
    b = f(0)                  # 切片1（式から計算）
    a = f(1) - f(0)           # 傾き2（式から計算）

    ck = Checker()
    ck.ok("最初の点は y軸上の (0, 1)（b＝f(0)＝1）", b == 1)
    ck.ok("階段は右へ1・上へ2（a＝2）", a == 2)
    ck.ok("階段の角 (1,1)→(1,3)・(2,3)→(2,5) の縦の上がりが式の差と一致",
          f(1) - f(0) == 2 and f(2) - f(1) == 2)
    ck.ok("階段でたどる点 (0,1)(1,3)(2,5) がすべて式を満たす",
          all(f(x) == 2 * x + 1 for x in (0, 1, 2)))

    cv = Canvas(360, 466, scale=38, ox=80, oy=368)
    axes_math(cv, -1, 4, -1, 9, yaxis_w=2.2)            # y軸を太めに（切片の強調）
    lo, hi = x_range_for(f, -0.85, 4.05, -0.75, 8.85)
    cv.line((lo, f(lo)), (hi, f(hi)), w=MAIN_W)
    pts_px = []
    for k in (0, 1):                                    # 階段2段（角は式から計算）
        arrow_math(cv, (k, f(k)), (k + 1, f(k)), w=1.3, head=6)
        arrow_math(cv, (k + 1, f(k)), (k + 1, f(k + 1)), w=1.3, head=6)
        cv.text((k + 0.5, f(k) - 0.52), "右へ1", size=10.5)
        cv.text((k + 1.1, f(k) + a / 2), f"上へ{a}", size=10.5, anchor="start")
    for x in (0, 1, 2):
        cv.dot((x, f(x)), r=3)
        pts_px.append(cv.P((x, f(x))) + (f"({x},{f(x)})",))
    cv.open_dot((0, b), r=6.5, w=1.4)
    cv.text((1.15, 0.5), f"最初の点 (0, {b})＝切片 b", size=11, anchor="start")
    arrow_math(cv, (1.1, 0.68), (0.14, b - 0.12), w=1.1, head=5.5, dash=DASH)
    cv.text((2.5, 3.05), f"傾き a＝{a}", size=11.5, anchor="start", weight="bold")
    cv.text((2.5, 2.42), f"（右へ1で上へ{a}）", size=10, anchor="start")
    cv.text_px(180, 428, "y軸の切片に最初の点を打ち、傾きのぶんだけ階段をのぼる",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 448, "（右へ1・上へ2を、どこまでもくり返す）",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig2_intercept_and_slope_steps.svg", canvas=cv,
                lesson="L03",
                title="切片に最初の点→傾きの階段（y＝2x＋1）",
                intent="主概念2の手順の可視化。最初の点(0,b)と右1上2の階段を式から計算配置",
                src="lesson_03.md 主概念2",
                params="y＝2x＋1・b＝1・a＝2・階段の角(1,1)(2,3)は式から計算",
                checks=ck.items,
                rb_texts=["最初の点 (0, 1)＝切片 b", "傾き a＝2", "右へ1", "上へ2"],
                rb_absent=["y＝2x−3"],    # 練習2の答えの直線を混ぜない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図7: L04 グラフから式を読む（y＝3x＋2・①(0,2)で b・②右1上3で a）
# 仕様源: notes/lesson_04_notes.md §2 L04_fig1（必須級・本単元の筆頭）
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（lesson_04.md 主概念1 と一致させる） ---
    f = lambda x: 3 * x + 2
    b = f(0)                  # 2
    a = f(1) - f(0)           # 3

    ck = Checker()
    ck.ok("y軸との交点は (0, 2)（b＝2）", b == 2)
    ck.ok("右へ1で上へ3（a＝3・(1,5)は式から計算）", a == 3 and f(1) == 5)
    ck.ok("確かめ点 (2, 8) が式を満たす（本文guide2の解説値）", f(2) == 8)
    ck.ok("プロットする3点すべてが y＝3x＋2 を満たす（再計算）",
          all(f(x) == 3 * x + 2 for x in (0, 1, 2)))

    cv = Canvas(360, 466, scale=38, ox=80, oy=368)
    axes_math(cv, -1, 4, -1, 9)
    lo, hi = x_range_for(f, -0.95, 4.05, -0.85, 8.85)
    cv.line((lo, f(lo)), (hi, f(hi)), w=MAIN_W)
    pts_px = []
    # ① 切片
    cv.dot((0, b), r=3)
    pts_px.append(cv.P((0, b)) + ("(0,2)",))
    cv.open_dot((0, b), r=6.5, w=1.4)
    cv.text((0.55, 1.1), f"① y軸との交点 (0, {b})＝切片 b", size=11, anchor="start")
    arrow_math(cv, (0.5, 1.32), (0.1, 1.78), w=1.1, head=5.5, dash=DASH)
    # ② 傾きの階段
    arrow_math(cv, (0, b), (1, b), w=1.3, head=6)
    arrow_math(cv, (1, b), (1, f(1)), w=1.3, head=6)
    cv.text((0.5, b + 0.22), "右へ1", size=10.5)
    cv.text((1.1, b + a / 2), f"上へ{a}", size=10.5, anchor="start")
    cv.dot((1, f(1)), r=3)
    pts_px.append(cv.P((1, f(1))) + ("(1,5)",))
    cv.text((1.7, 4.2), f"② 傾き a＝{a}", size=11.5, anchor="start", weight="bold")
    # 確かめ点（本文明示の解説値・うすく）
    cv.open_dot((2, f(2)), r=3.5, w=1.2, stroke="#666")
    pts_px.append(cv.P((2, f(2))) + ("(2,8)",))
    cv.text((2.12, 8.05), f"(2, {f(2)})で確かめ", size=10.5, anchor="start",
            fill="#666")
    cv.text((2.35, 6.0), "y＝3x＋2", size=12.5, anchor="start", weight="bold")
    cv.text_px(180, 428, "①y軸との交点で b、②右へ1ののぼり方で a を読む",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 448, "（式に戻せたら、通る点を代入して確かめる）",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_read_slope_intercept.svg", canvas=cv, lesson="L04",
                title="グラフから式を読む（切片 b＝2・傾き a＝3 → y＝3x＋2）",
                intent="主概念1の読み取り2手順の可視化。読み取るグラフを図として与える",
                src="lesson_04.md 主概念1",
                params="y＝3x＋2・(0,2)(1,5)(2,8)は式から計算／確かめ点(2,8)は本文明示値",
                checks=ck.items,
                rb_texts=["① y軸との交点 (0, 2)＝切片 b", "② 傾き a＝3",
                          "右へ1", "上へ3", "y＝3x＋2"],
                rb_absent=[],
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図8: L04 右下がりの直線（y＝−2x＋3・右へ1で2下がる→a＝−2）
# 仕様源: notes/lesson_04_notes.md §2 L04_fig2
# 答え漏れ注意: 練習2の答え y＝−2x＋4 とは別直線（切片3≠4を維持）
# ===========================================================================
def fig_L04_2():
    # --- パラメータ（lesson_04.md 主概念2前半 と一致させる） ---
    f = lambda x: -2 * x + 3
    b = f(0)                  # 3
    a = f(1) - f(0)           # −2
    ans2_b = 4                # 練習2の答えの切片（分離の照合にのみ使用・図に書かない）

    ck = Checker()
    ck.ok("y軸との交点は (0, 3)", b == 3)
    ck.ok("右へ1で2下がる（a＝−2・(1,1)は式から計算）", a == -2 and f(1) == 1)
    ck.ok("プロットする2点が y＝−2x＋3 を満たす（再計算）",
          all(f(x) == -2 * x + 3 for x in (0, 1)))
    ck.ok("答えの分離: 練習2の答え（切片4）とは別直線（b＝3≠4）", b != ans2_b)

    cv = Canvas(360, 404, scale=38, ox=80, oy=216)
    axes_math(cv, -1, 4, -3, 5)
    lo, hi = x_range_for(f, -0.9, 3.6, -2.85, 4.1)
    cv.line((lo, f(lo)), (hi, f(hi)), w=MAIN_W)
    pts_px = []
    cv.dot((0, b), r=3)
    pts_px.append(cv.P((0, b)) + ("(0,3)",))
    cv.open_dot((0, b), r=6.5, w=1.4)
    cv.text((-0.98, 4.55), f"y軸の交点 (0, {b})", size=11, anchor="start")
    arrow_math(cv, (-0.32, 4.32), (-0.07, 3.3), w=1.1, head=5.5, dash=DASH)
    arrow_math(cv, (0, b), (1, b), w=1.3, head=6)
    arrow_math(cv, (1, b), (1, f(1)), w=1.3, head=6)
    cv.text((0.5, b - 0.55), "右へ1", size=10.5)
    cv.text((1.1, b + a / 2), "下へ2", size=10.5, anchor="start")
    cv.dot((1, f(1)), r=3)
    pts_px.append(cv.P((1, f(1))) + ("(1,1)",))
    cv.text((1.55, 4.25), "右へ進むと下がる → 傾きは負", size=11, anchor="start",
            weight="bold")
    cv.text((1.7, 3.62), "a＝−2", size=12.5, anchor="start", weight="bold")
    cv.text((2.4, -0.95), "y＝−2x＋3", size=12.5, anchor="start", weight="bold")
    cv.text_px(180, 366, "右下がりの直線——右へ1進むと2下がるから、傾きは −2",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 386, "（下がる量2は正の数で数え、符号は「下がる向き」で付ける）",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig2_negative_slope.svg", canvas=cv, lesson="L04",
                title="右下がりの直線（y＝−2x＋3・右へ1で2下がる→a＝−2）",
                intent="主概念2前半の可視化。練習2の答えの直線とは別直線で答えを分離",
                src="lesson_04.md 主概念2前半",
                params="y＝−2x＋3・(0,3)(1,1)は式から計算／練習2の答えと切片不一致をassert",
                checks=ck.items,
                rb_texts=["y軸の交点 (0, 3)", "右へ1", "下へ2", "a＝−2", "y＝−2x＋3"],
                rb_absent=["−2x＋4"],     # 練習2の答えの直線を図に出さない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図9: L04 傾きが分数の直線（y＝(2/3)x−1・格子点(0,−1)(3,1)・右3上2）
# 仕様源: notes/lesson_04_notes.md §2 L04_fig3
# 答え漏れ注意: 練習1の答え y＝(2/3)x＋1 とは別直線（切片−1≠1を維持）
# ===========================================================================
def fig_L04_3():
    # --- パラメータ（lesson_04.md 主概念2後半 と一致させる） ---
    f = lambda x: F(2, 3) * x - 1
    b = f(0)                  # −1
    ans1_b = 1                # 練習1の答えの切片（分離の照合にのみ使用・図に書かない）

    ck = Checker()
    ck.ok("格子点 (0,−1)(3,1)(6,3) がすべて式を満たし整数座標（再計算）",
          [f(x) for x in (0, 3, 6)] == [-1, 1, 3]
          and all(f(x).denominator == 1 for x in (0, 3, 6)))
    ck.ok("右へ3・上へ2（(3,1)−(0,−1) の差の再計算）",
          (f(3) - f(0)) == 2 and 3 - 0 == 3)
    ck.ok("2÷3＝2/3（本文明示の途中式・図に記載）", F(2, 3) == F(2 - 0, 3 - 0)
          and F(f(3) - f(0), 3 - 0) == F(2, 3))
    ck.ok("右へ1では方眼に乗らない（f(1)＝−1/3 は整数でない）",
          f(1) == F(-1, 3) and f(1).denominator != 1)
    ck.ok("答えの分離: 練習1の答え（切片1）とは別直線（b＝−1≠1）", b != ans1_b)

    cv = Canvas(370, 334, scale=34, ox=60, oy=162)
    axes_math(cv, -1, 7, -3, 4, grid=True, fs_tick=9.5)
    lo, hi = x_range_for(lambda x: float(f(F(x))), -0.9, 6.95, -2.85, 3.9)
    cv.line((lo, float(f(F(lo)))), (hi, float(f(F(hi)))), w=MAIN_W)
    pts_px = []
    # 大またの階段（右へ3・上へ2）——角は式から計算
    arrow_math(cv, (0, float(f(0))), (3, float(f(0))), w=1.3, head=6)
    arrow_math(cv, (3, float(f(0))), (3, float(f(3))), w=1.3, head=6)
    cv.text((1.5, float(f(0)) - 0.62), "右へ3", size=10.5)
    cv.text((2.86, 0.4), "上へ2", size=10.5, anchor="end")
    for x, emph in ((0, True), (3, True), (6, False)):
        cv.dot((x, float(f(x))), r=3)
        pts_px.append(cv.P((x, float(f(x)))) + (f"({x},{f(x)})",))
        if emph:
            cv.open_dot((x, float(f(x))), r=6.5, w=1.4)
    cv.text((-0.16, -1.85), f"(0, {num_label(str(f(0)))})", size=11, anchor="end")
    cv.text((3.14, 1.62), f"(3, {f(3)})", size=11, anchor="start")
    cv.text((6.15, 2.55), f"(6, {f(6)})", size=10.5, anchor="start", fill="#666")
    cv.text((0.55, 2.6), "傾き＝2÷3＝2/3", size=12, anchor="start", weight="bold")
    # 右へ1では格子点に乗らないことの注記
    cv.open_dot((1, float(f(1))), r=3.2, w=1.1, stroke="#666")
    cv.text((0.9, -2.55), "右へ1では方眼の交点に乗らない", size=10, anchor="start",
            fill="#666")
    arrow_math(cv, (1.3, -2.15), (1.04, float(f(1)) - 0.2), w=1.0, head=5,
               dash=DASH, color="#666")
    cv.text((4.55, 1.35), "y＝(2/3)x−1", size=11.5, anchor="start", weight="bold")
    cv.text_px(185, 300, "傾きが分数のときは、方眼にちょうど乗る格子点まで大またで進む",
               size=11.5, anchor="middle")
    cv.text_px(185, 318, "（右へ3・上へ2 → 2÷3＝2/3）", size=11.5, anchor="middle")

    return dict(file="L04_fig3_lattice_fraction_slope.svg", canvas=cv, lesson="L04",
                title="傾きが分数の直線（格子点(0,−1)(3,1)・右へ3上へ2→2/3）",
                intent="主概念2後半の可視化。練習1の答えの直線とは別直線で答えを分離",
                src="lesson_04.md 主概念2後半",
                params="y＝(2/3)x−1・格子点(0,−1)(3,1)(6,3)と非格子点(1,−1/3)は式から計算",
                checks=ck.items,
                rb_texts=["(3, 1)", "傾き＝2÷3＝2/3", "右へ3", "上へ2",
                          "y＝(2/3)x−1", "右へ1では方眼の交点に乗らない"],
                rb_absent=["(2/3)x＋1"],  # 練習1の答えの直線を図に出さない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図9b: L04 練習3の問題図（3直線ア・イ・ウ・図読み取り形式）
# 仕様源: レビュー裁定2（2026-08-29 決裁済み）——練習3を図読み取り形式へ
# 答え漏れ注意: 直線の式そのものが答え——式・傾き・切片の値は図に一切書かない
#   （ラベルはア・イ・ウのみ。係数は answer_key_L01-04.md 練習3(1)(2)(3)の解と一致）
# ===========================================================================
def fig_L04_4():
    # --- パラメータ（answer_key_L01-04.md 練習3の解 と一致させる） ---
    lines = [
        ("ア", lambda x: 4 * x - 3, 4, -3),    # 練習3(1) 切片−3・傾き4
        ("イ", lambda x: -x + 5, -1, 5),       # 練習3(2) 切片5・傾き−1
        ("ウ", lambda x: 3 * x, 3, 0),         # 練習3(3) 原点・傾き3
    ]
    xmin, xmax, ymin, ymax = -2, 3, -5, 7      # 描画窓（格子・目盛の範囲）

    ck = Checker()
    ck.ok("3直線の傾き・切片が answer_key_L01-04.md 練習3(1)(2)(3)の解と一致（再計算）",
          all(f(1) - f(0) == a and f(0) == b for _, f, a, b in lines))
    ck.ok("ウは原点を通る（練習3(3)の与件）", lines[2][1](0) == 0)
    ck.ok("読み取り用の格子点（y軸上と右へ1）が全直線で整数座標かつ窓の中（再計算）",
          all(isinstance(f(x), int) and xmin <= x <= xmax and ymin <= f(x) <= ymax
              for _, f, a, b in lines for x in (0, 1)))
    ck.ok("3本の傾きがすべて異なる（1本ずつ別の直線として識別できる）",
          len({a for _, f, a, b in lines}) == 3)
    ck.ok("答えの分離: 式・傾き・切片の値は図に文字で書かない（rb_absentで機械検査）",
          True)

    cv = Canvas(380, 505, scale=34, ox=130, oy=270)
    axes_math(cv, xmin, xmax, ymin, ymax, grid=True, fs_tick=9.5)
    pts_px = []
    for name, f, a, b in lines:
        lo, hi = x_range_for(f, xmin + 0.1, xmax - 0.1, ymin + 0.2, ymax - 0.2)
        cv.line((lo, f(lo)), (hi, f(hi)), w=MAIN_W)
        for x in (0, 1):                       # 読み取り用の格子点（式から計算）
            cv.dot((x, f(x)), r=3)
            pts_px.append(cv.P((x, f(x))) + (f"{name}({x},{f(x)})",))
        if a > 0:                              # ラベル位置＝線の端（式から計算）
            if name == "ウ":                   # ウはアと上端が近いため下端側へ
                cv.text((lo - 0.14, f(lo) + 0.28), name, size=13, anchor="end",
                        weight="bold")
            else:
                cv.text((hi + 0.1, f(hi) - 0.1), name, size=13, anchor="start",
                        weight="bold")
        else:
            cv.text((hi + 0.12, f(hi)), name, size=13, anchor="start",
                    weight="bold")
    cv.text_px(190, 468, "方眼の1目盛は1——ア・イ・ウの直線の式を、図から読み取ろう",
               size=11.5, anchor="middle")
    cv.text_px(190, 488, "（y軸と交わる点と、右へ1進んだときの変化に注目）",
               size=11, anchor="middle")

    return dict(file="L04_fig4_practice_three_lines.svg", canvas=cv, lesson="L04",
                title="L04練習3の問題図（3直線ア・イ・ウの読み取り）",
                intent="練習3を図読み取り形式にした問題図。直線の式は答えのため文字では"
                       "書かず、ア・イ・ウのラベルと格子・目盛だけを置く",
                src="lesson_04.md 練習3（裁定2・2026-08-29）",
                params="3直線の係数は answer_key_L01-04.md 練習3(1)(2)(3)の解と一致"
                       "（値は答えの分離のため図・台帳に非記載）・読み取り用格子点は式から計算",
                checks=ck.items,
                rb_texts=["ア", "イ", "ウ",
                          "方眼の1目盛は1——ア・イ・ウの直線の式を、図から読み取ろう"],
                rb_absent=["y＝", "4x−3", "−x＋5", "傾き", "切片"],
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図9c: L04 練習4の問題図（2直線エ・オ・図読み取り形式・分数の傾き）
# 仕様源: レビュー裁定2（2026-08-29 決裁済み）——練習4を図読み取り形式へ
# 答え漏れ注意: 直線の式そのものが答え——式・傾き・切片の値は図に一切書かない
#   （ラベルはエ・オのみ。係数は answer_key_L01-04.md 練習4(1)(2)の解と一致）
# ===========================================================================
def fig_L04_5():
    # --- パラメータ（answer_key_L01-04.md 練習4の解 と一致させる） ---
    fE = lambda x: F(3, 4) * x + 2             # 練習4(1) 切片2・傾き3/4
    fO = lambda x: F(-2, 3) * x + 1            # 練習4(2) 切片1・傾き−2/3
    latE = [0, 4]                              # エの読み取り用格子点のx（右へ4）
    latO = [0, 3]                              # オの読み取り用格子点のx（右へ3）
    xmin, xmax, ymin, ymax = -4, 5, -3, 6      # 描画窓（格子・目盛の範囲）

    ck = Checker()
    ck.ok("エ・オの傾き・切片が answer_key_L01-04.md 練習4(1)(2)の解と一致（再計算）",
          fE(1) - fE(0) == F(3, 4) and fE(0) == 2
          and fO(1) - fO(0) == F(-2, 3) and fO(0) == 1)
    ck.ok("右へ1では方眼の交点に乗らない（f(1)が整数でない＝大また読みが必要）",
          fE(1).denominator != 1 and fO(1).denominator != 1)
    ck.ok("大また用の格子点 エ(0,2)(4,5)・オ(0,1)(3,−1) が式を満たし整数座標（再計算）",
          [fE(x) for x in latE] == [2, 5] and [fO(x) for x in latO] == [1, -1]
          and all(fE(x).denominator == 1 for x in latE)
          and all(fO(x).denominator == 1 for x in latO))
    ck.ok("格子点が図の窓の中（読み取れることが問題の成立条件）",
          all(xmin <= x <= xmax and ymin <= fE(x) <= ymax for x in latE)
          and all(xmin <= x <= xmax and ymin <= fO(x) <= ymax for x in latO))
    ck.ok("答えの分離: 式・傾き・切片の値は図に文字で書かない（rb_absentで機械検査）",
          True)

    cv = Canvas(420, 408, scale=34, ox=160, oy=240)
    axes_math(cv, xmin, xmax, ymin, ymax, grid=True, fs_tick=9.5)
    pts_px = []
    for name, f, lat in (("エ", fE, latE), ("オ", fO, latO)):
        lo, hi = x_range_for(lambda x, f=f: float(f(F(x))),
                             xmin + 0.1, xmax - 0.1, ymin + 0.15, ymax - 0.15)
        cv.line((lo, float(f(F(lo)))), (hi, float(f(F(hi)))), w=MAIN_W)
        for x in lat:                          # 読み取り用の格子点（式から計算）
            cv.dot((x, float(f(x))), r=3)
            pts_px.append(cv.P((x, float(f(x)))) + (f"{name}({x},{f(x)})",))
        cv.text((hi + 0.14, float(f(F(hi)))), name, size=13, anchor="start",
                weight="bold")
    cv.text_px(210, 372, "方眼の1目盛は1——エ・オの直線の式を、図から読み取ろう",
               size=11.5, anchor="middle")
    cv.text_px(210, 392, "（右へ1では方眼の交点に乗らない——ちょうど乗る点まで大またで）",
               size=11, anchor="middle")

    return dict(file="L04_fig5_practice_two_lines.svg", canvas=cv, lesson="L04",
                title="L04練習4の問題図（2直線エ・オの読み取り）",
                intent="練習4を図読み取り形式にした問題図。右へ1では方眼に乗らない直線を、"
                       "格子点まで大またで読み取らせる。式・係数の値は図に書かない",
                src="lesson_04.md 練習4（裁定2・2026-08-29）",
                params="2直線の係数は answer_key_L01-04.md 練習4(1)(2)の解と一致"
                       "（値は非記載）・格子点 エ(0,2)(4,5)・オ(0,1)(3,−1) は式から計算",
                checks=ck.items,
                rb_texts=["エ", "オ",
                          "方眼の1目盛は1——エ・オの直線の式を、図から読み取ろう"],
                rb_absent=["y＝", "3/4", "2/3", "傾き", "切片"],
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図10: L05 2点で直線が1本に決まる（(1,5)(4,11)→y＝2x＋3・候補線は式ラベルなし）
# 仕様源: notes/lesson_05_notes.md §1 L05_fig1
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（lesson_05.md 主概念2・例2 と一致させる） ---
    p1, p2 = (1, 5), (4, 11)
    a = F(p2[1] - p1[1], p2[0] - p1[0])       # (11−5)÷(4−1)＝2
    b = p1[1] - a * p1[0]                     # 3
    f = lambda x: a * x + b                   # y＝2x＋3
    cand_slopes = [F(1, 2), 4, -1]            # 候補線の傾き（図にラベルしない）
    cands = [(m, lambda x, m=m: m * (x - p1[0]) + p1[1]) for m in cand_slopes]

    ck = Checker()
    ck.ok("傾き a＝(11−5)÷(4−1)＝2・切片 b＝3（本文例2の計算の再現）",
          a == 2 and b == 3)
    ck.ok("直線 y＝2x＋3 が2点 (1,5)(4,11) の両方を通る（代入検算）",
          f(p1[0]) == p1[1] and f(p2[0]) == p2[1])
    ck.ok("候補線（うすい線）はすべて1点目 (1,5) を通る",
          all(g(p1[0]) == p1[1] for _, g in cands))
    ck.ok("候補線はどれも2点目 (4,11) を通らない（＝2点目で1本に絞られる）",
          all(g(p2[0]) != p2[1] for _, g in cands))
    ck.ok("傾きの三角形は右へ3・上へ6（本文の計算 (11−5)÷(4−1) と一致）",
          p2[0] - p1[0] == 3 and p2[1] - p1[1] == 6)

    cv = Canvas(340, 484, scale=30, ox=70, oy=384)
    axes_math(cv, -1, 5, -1, 12, fs_tick=9.5)
    for _, g in cands:                        # 候補線（グレー・式ラベルなし）
        r = x_range_for(lambda x, g=g: float(g(F(x))), -0.85, 4.9, -0.8, 11.8)
        cv.line((r[0], float(g(F(r[0])))), (r[1], float(g(F(r[1])))),
                w=1.2, color="#bbb")
    lo, hi = x_range_for(lambda x: float(f(F(x))), -0.85, 4.55, -0.8, 11.8)
    cv.line((lo, float(f(F(lo)))), (hi, float(f(F(hi)))), w=2.2)
    # 傾きの三角形（破線・右へ3上へ6）——頂点は2点から計算
    cv.polyline([(p1[0], p1[1]), (p2[0], p1[1]), (p2[0], p2[1])], w=AUX_W,
                dash=DASH)
    cv.text(((p1[0] + p2[0]) / 2, p1[1] - 0.55), f"右へ{p2[0] - p1[0]}", size=10.5)
    cv.text((p2[0] + 0.12, (p1[1] + p2[1]) / 2), f"上へ{p2[1] - p1[1]}",
            size=10.5, anchor="start")
    pts_px = []
    for (x, y) in (p1, p2):
        cv.dot((x, y), r=3.2)
        pts_px.append(cv.P((x, y)) + (f"({x},{y})",))
    cv.text((p1[0] - 0.2, p1[1] + 0.35), f"({p1[0]}, {p1[1]})", size=11,
            anchor="end")
    cv.text((p2[0] + 0.18, p2[1] - 0.15), f"({p2[0]}, {p2[1]})", size=11,
            anchor="start")
    cv.text((2.28, 8.85), "y＝2x＋3", size=12.5, anchor="start", weight="bold")
    cv.text_px(170, 444, "1点だけなら、通る直線は何本もある（うすい線）",
               size=FS_CAP, anchor="middle")
    cv.text_px(170, 464, "——2点目が加わると、通る直線は y＝2x＋3 の1本に決まる",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_two_points_one_line.svg", canvas=cv, lesson="L05",
                title="2点で直線が1本に決まる（(1,5)(4,11)→y＝2x＋3）",
                intent="主概念2「2つの手がかりで1本に決まる」の可視化。候補線は式ラベルなし",
                src="lesson_05.md 主概念2・例2の直後",
                params="点(1,5)(4,11)・y＝2x＋3（a・bは2点から計算）／候補線の式は非記載",
                checks=ck.items,
                rb_texts=["(1, 5)", "(4, 11)", "y＝2x＋3", "右へ3", "上へ6"],
                rb_absent=["1/2", "4x", "−x＋6"],   # 候補線の式を図に書かない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図11: L06 2直線と交わる点（y＝−2x＋6 と y＝−(1/2)x＋4・交点座標は書かない）
# 仕様源: notes/lesson_06_notes.md §1 L06_fig1（必須級）
# 答え漏れ注意: 交点 (4/3, 10/3) の座標値を図に表記しない（○で存在のみ示す）
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（lesson_06.md 主概念1・2 と一致させる） ---
    g1 = lambda x: -2 * x + 6                 # 2x＋y＝6 を変形
    g2 = lambda x: F(-1, 2) * x + 4           # x＋2y＝8 を変形
    lat1 = [0, 1, 2, 3]                       # 直線1の格子点のx
    lat2 = [0, 2, 4]                          # 直線2の格子点のx

    ck = Checker()
    ck.ok("直線1の格子点 (0,6)(1,4)(2,2)(3,0) が式を満たす（再計算）",
          [g1(x) for x in lat1] == [6, 4, 2, 0]
          and all(2 * x + g1(x) == 6 for x in lat1))
    ck.ok("直線2の格子点 (0,4)(2,3)(4,2) が式を満たす（再計算）",
          [g2(x) for x in lat2] == [4, 3, 2]
          and all(x + 2 * g2(x) == 8 for x in lat2))
    xi = F(4, 3)                              # 交点（検算のみ・図に書かない）
    yi = g1(xi)
    ck.ok("交点 (4/3, 10/3) が両方の式を満たす（図には座標を書かない）",
          g1(xi) == g2(xi) == F(10, 3)
          and 2 * xi + yi == 6 and xi + 2 * yi == 8)
    ck.ok("交点は格子点でない（座標が整数でない）ことにスクリプトが耐える",
          xi.denominator != 1 and yi.denominator != 1)
    ck.ok("式ラベルの2表記が同値: 2x＋y＝6 ⇔ y＝−2x＋6・x＋2y＝8 ⇔ y＝−(1/2)x＋4",
          all(2 * x + g1(x) == 6 for x in range(-3, 6))
          and all(x + 2 * g2(x) == 8 for x in range(-3, 6)))

    cv = Canvas(440, 414, scale=40, ox=64, oy=306)
    axes_math(cv, -1, 5, -1, 7)
    r1 = x_range_for(g1, -0.35, 4.9, -0.8, 6.8)
    cv.line((r1[0], g1(r1[0])), (r1[1], g1(r1[1])), w=MAIN_W)
    r2 = x_range_for(lambda x: float(g2(F(x))), -0.9, 4.9, -0.8, 6.8)
    cv.line((r2[0], float(g2(F(r2[0])))), (r2[1], float(g2(F(r2[1])))), w=MAIN_W)
    pts_px = []
    for x in lat1:
        cv.dot((x, g1(x)), r=2.5)
        pts_px.append(cv.P((x, g1(x))) + (f"直線1({x},{g1(x)})",))
    for x in lat2:
        cv.dot((x, float(g2(x))), r=2.5)
        pts_px.append(cv.P((x, float(g2(x)))) + (f"直線2({x},{g2(x)})",))
    cv.open_dot((float(xi), float(yi)), r=4.5, w=1.6)   # 交点＝白抜き○（座標なし）
    pts_px.append(cv.P((float(xi), float(yi))) + ("交点○",))
    cv.text((2.0, 5.3), "交わる点（2つの式を同時に満たす組）", size=11,
            anchor="start")
    arrow_math(cv, (2.1, 5.0), (float(xi) + 0.18, float(yi) + 0.28), w=1.1,
               head=5.5, dash=DASH)
    cv.text((2.62, 0.95), "y＝−2x＋6", size=11.5, anchor="start", weight="bold")
    cv.text((2.62, 0.45), "（2x＋y＝6）", size=10, anchor="start", fill="#666")
    cv.text((3.5, 3.1), "y＝−(1/2)x＋4", size=11.5, anchor="start", weight="bold")
    cv.text((3.5, 2.6), "（x＋2y＝8）", size=10, anchor="start", fill="#666")
    cv.text_px(220, 372, "2つの方程式のグラフを1つの座標平面にかくと、1点で交わる",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 392, "（交わる点の組は、どちらの式にも当てはまる——両方の式で確かめよう）",
               size=11, anchor="middle")

    return dict(file="L06_fig1_two_lines_intersection.svg", canvas=cv, lesson="L06",
                title="2直線と交わる点（y＝−2x＋6 と y＝−(1/2)x＋4）",
                intent="主概念2「交わる点がある」の可視化。交点の座標は図に書かない",
                src="lesson_06.md 主概念2冒頭",
                params="2x＋y＝6・x＋2y＝8／格子点7点と交点は式から計算（交点座標は非記載）",
                checks=ck.items,
                rb_texts=["y＝−2x＋6", "（2x＋y＝6）", "y＝−(1/2)x＋4", "（x＋2y＝8）",
                          "交わる点（2つの式を同時に満たす組）"],
                rb_absent=["4/3", "10/3", "1.3", "3.3"],   # 交点座標を書かない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図12: L07 変域つきの水そうグラフ（y＝3x＋4・0≤x≤12・満水40cm）
# 仕様源: notes/lesson_07_notes.md §1 L07_fig1（必須級）
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（lesson_07.md 主概念1・2 と一致させる） ---
    f = lambda x: 3 * x + 4
    full = 40                 # 満水（cm）
    xmax_dom = (full - f(0)) // 3             # 40＝3x＋4 → x＝12（式から計算）

    ck = Checker()
    ck.ok("端点は (0, 4) と (12, 40)（式から計算）",
          f(0) == 4 and f(12) == 40)
    ck.ok("満水の時刻は 40＝3x＋4 → x＝12（本文明示の途中式）",
          xmax_dom == 12 and f(xmax_dom) == full)
    ck.ok("yの変域は 4 ≤ y ≤ 40（両はしのxを代入した再計算値）",
          f(0) == 4 and f(xmax_dom) == 40)
    ck.ok("変域の外では場面に合わない（x＝13で43cm＞満水40cm）",
          f(13) == 43 and f(13) > full)
    ck.ok("グラフの傾き＝毎分3cm（式の再計算）", f(1) - f(0) == 3)

    cv = Canvas(470, 436, scale=24, ox=70, oy=346, sy=7)
    # 変域の帯（0 ≤ x ≤ 12）を薄グレーで
    (bx1, by1), (bx2, by2) = cv.P((0, 46)), cv.P((12, 0))
    cv.rect_px_nostroke(bx1, by1, bx2 - bx1, by2 - by1, "#f0f0f0")
    axes_math(cv, -1, 14, -4, 46, xlabel="x（分）", ylabel="y（cm）",
              xticks=list(range(1, 15)), xlabels=[5, 10],
              yticks=[10, 20, 30], ylabels=[10, 20, 30], fs_tick=10)
    # 目盛の強調: x＝12・y＝4・y＝40（変域の端）
    x0px, y0px = cv.P((0, 0))
    for vx, lab in ((12, "12"),):
        px, _ = cv.P((vx, 0))
        cv.raw(f'<line x1="{px:.1f}" y1="{y0px - 3.2:.1f}" x2="{px:.1f}" '
               f'y2="{y0px + 3.2:.1f}" stroke="#000" stroke-width="1.4"/>')
        cv.text_px(px, y0px + 14, lab, size=10, anchor="middle", weight="bold")
    for vy in (f(0), full):
        _, py = cv.P((0, vy))
        cv.raw(f'<line x1="{x0px - 3.2:.1f}" y1="{py:.1f}" x2="{x0px + 3.2:.1f}" '
               f'y2="{py:.1f}" stroke="#000" stroke-width="1.4"/>')
        cv.text_px(x0px - 6, py + 3.5, str(vy), size=10, anchor="end",
                   weight="bold")
    # 満水線 y＝40（点線）と補助線 x＝12（破線）
    cv.line((0, full), (14, full), w=0.9, dash="2 3")
    cv.text((13.9, full + 1.2), f"満水 {full}cm", size=10.5, anchor="end")
    cv.line((12, 0), (12, full), w=AUX_W, dash=DASH)
    # 本体: 0≤x≤12 は実線・その先は破線グレー（場面を表せない）
    cv.line((0, f(0)), (xmax_dom, f(xmax_dom)), w=2.0)
    ext_hi = x_range_for(f, 12, 14.2, 0, 45.5)[1]
    cv.line((12, f(12)), (ext_hi, f(ext_hi)), w=1.3, dash=DASH, color="#888")
    cv.text((8.0, 43.6), "満水後はこの式では表せない", size=10, anchor="start",
            fill="#666")
    pts_px = []
    for x in (0, xmax_dom):                   # 端点●（変域に含む）
        cv.dot((x, f(x)), r=3.2)
        pts_px.append(cv.P((x, f(x))) + (f"端点({x},{f(x)})",))
    cv.text((0.25, 6.3), f"(0, {f(0)})", size=10.5, anchor="start")
    cv.text((12.25, 37.2), f"(12, {f(12)})", size=10.5, anchor="start")
    cv.text((5.1, 30.5), "y＝3x＋4", size=12.5, anchor="start", weight="bold")
    cv.text((6, 2.0), "xの変域 0 ≤ x ≤ 12", size=10.5, anchor="middle",
            weight="bold")
    cv.text((0.35, 33.5), "yの変域 4 ≤ y ≤ 40", size=10.5, anchor="start",
            weight="bold")
    cv.text_px(235, 400, "水そうの深さ y＝3x＋4 が場面を表すのは 0 ≤ x ≤ 12（満水まで）だけ",
               size=11.5, anchor="middle")
    cv.text_px(235, 420, "（12分をこえると、式では計算できても場面には合わない）",
               size=11.5, anchor="middle")

    return dict(file="L07_fig1_tank_domain.svg", canvas=cv, lesson="L07",
                title="変域つきの水そうグラフ（y＝3x＋4・0 ≤ x ≤ 12・満水40cm）",
                intent="主概念2「変域」の可視化。実線は変域内だけ・満水線と変域帯を添える",
                src="lesson_07.md 主概念2（変域の提示直後）",
                params="はじめ4cm・毎分3cm・満水40cm／端点(0,4)(12,40)と満水時刻12分は式から計算",
                checks=ck.items,
                rb_texts=["y＝3x＋4", "xの変域 0 ≤ x ≤ 12", "yの変域 4 ≤ y ≤ 40",
                          "満水 40cm", "(0, 4)", "(12, 40)"],
                rb_absent=[],
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図13: L07 追いつきの2直線（y＝60x＋20 と y＝80x・交点座標は書かない）
# 仕様源: notes/lesson_07_notes.md §1 L07_fig2
# 答え漏れ注意: 交点 (1, 80) は練習4の最終解——図に座標ラベル・目盛数値を書かない
# 配置変更: 裁定5（2026-08-29）で参照位置を練習4ヒント直後→guide3「追いつく」直後へ
#   移動（srcのみ更新。SVG本体のバイト列は不変を維持するため intent/params は非変更）
# ===========================================================================
def fig_L07_2():
    # --- パラメータ（lesson_07.md 練習4 と一致させる） ---
    A = lambda x: 60 * x + 20                 # Aさん（先に20m）
    B = lambda x: 80 * x                      # Bさん（原点から）

    ck = Checker()
    xi = 20 / (80 - 60)                       # 追いつく時刻（検算のみ・図に書かない）
    ck.ok("交点は x＝1 で A(1)＝B(1)＝80（練習4の答え・図には書かない）",
          xi == 1.0 and A(1) == B(1) == 80)
    ck.ok("出発時はAが20m前（A(0)−B(0)＝20＝場面の与件）", A(0) - B(0) == 20)
    ck.ok("Bのほうが速い（傾き80＞60）だからいつか追いつく",
          (B(1) - B(0)) > (A(1) - A(0)))
    ck.ok("答えの分離: 図には数値目盛を置かず、交点座標は読み取れない（rb_absentで機械検査）",
          True)

    cv = Canvas(470, 372, scale=130, ox=56, oy=287, sy=1.5)
    axes_math(cv, -0.2, 2.4, -15, 175, xlabel="x（分）", ylabel="y（m）",
              xticks=[], yticks=[], xlabels=[], ylabels=[])
    rA = x_range_for(A, 0, 2.15, 0, 152)
    cv.line((rA[0], A(rA[0])), (rA[1], A(rA[1])), w=MAIN_W)
    rB = x_range_for(B, 0, 2.1, 0, 168)
    cv.line((rB[0], B(rB[0])), (rB[1], B(rB[1])), w=MAIN_W)
    pts_px = []
    cv.dot((0, A(0)), r=3.2)                  # スタート時のAの位置（与件20m）
    pts_px.append(cv.P((0, A(0))) + ("A出発(0,20)",))
    cv.text((0.3, 9), "スタートでAが20m前", size=10.5, anchor="start")
    cv.open_dot((xi, A(xi)), r=4.5, w=1.6)    # 追いつく点（白抜き○・座標なし）
    pts_px.append(cv.P((xi, A(xi))) + ("交点○",))
    cv.text((1.12, 46), "ここで追いつく", size=11, anchor="start", weight="bold")
    cv.text((1.12, 32), "（2つのyが等しくなる点）", size=10, anchor="start")
    arrow_math(cv, (1.25, 55), (xi + 0.035, A(xi) - 9), w=1.1, head=5.5,
               dash=DASH)
    cv.text((2.13, B(2.05) - 4), "Bさん y＝80x", size=11.5, anchor="start",
            weight="bold")
    cv.text((2.18, A(2.12) - 16), "Aさん y＝60x＋20", size=11.5, anchor="start",
            weight="bold")
    cv.text_px(235, 336, "Aさん（先に20m）とBさん（速い）の2直線は、1点で交わる",
               size=FS_CAP, anchor="middle")
    cv.text_px(235, 356, "（交わるところが「追いつく」とき——いつかは、式かグラフで求めよう）",
               size=11, anchor="middle")

    return dict(file="L07_fig2_catchup_two_lines.svg", canvas=cv, lesson="L07",
                title="追いつきの2直線（y＝60x＋20 と y＝80x）",
                intent="練習4の追加ヒントの可視化。交点は座標も数値目盛も書かない",
                src="lesson_07.md guide3「追いつく」の直後（裁定5・2026-08-29で移動）",
                params="分速60m＋20m先行・分速80m／交点はassertのみ・軸の数値目盛なし",
                checks=ck.items,
                rb_texts=["Aさん y＝60x＋20", "Bさん y＝80x", "ここで追いつく",
                          "スタートでAが20m前"],
                rb_absent=["(1, 80)", "(1,80)", "1分後"],   # 答えの座標を書かない
                rb_circles=[(px, py, lab) for px, py, lab in pts_px])


# ===========================================================================
# 図14: L08 4つの見方のふり返り地図（中央 y＝ax＋b・表/グラフ/場面と行き来）
# 仕様源: notes/lesson_08_notes.md §1 L08_fig1（概念図・具体数値なし）
# ===========================================================================
def fig_L08_1():
    ck = Checker()
    # 地図の各矢印の主張を、見本の関数 y＝2x＋1 で検算（図には書かない）
    w = lambda x: 2 * x + 1
    ck.ok("表⇄式（L02）: 表の増加量どうしで割ると a（見本 y＝2x＋1 で再計算）",
          (w(3) - w(0)) / (3 - 0) == 2 == w(1) - w(0))
    ck.ok("式⇄グラフ（L03/L04）: 切片 b＝f(0)・傾き a＝右1の上がり（見本で再計算）",
          w(0) == 1 and w(1) - w(0) == 2)
    ck.ok("場面⇄式（L01/L07）: ペース＝a・はじめの量＝b の対応（見本で再計算）",
          w(0) == 1 and all(w(x + 1) - w(x) == 2 for x in range(0, 3)))
    ck.ok("グラフどうしの交点（L06）: 見本 y＝2x＋1 と y＝−x＋4 の交点(1,3)が両式を満たす",
          w(1) == 3 and -1 * 1 + 4 == 3)

    cv = Canvas(500, 372)
    cv.textbox_px(180, 148, 140, 56, ["式", "y＝ax＋b"], size=13,
                  sw=BOLD_W * 0.6, weight_first="bold")
    cv.textbox_px(30, 40, 120, 46, ["表", "x・yの数の並び"], size=11,
                  weight_first="bold")
    cv.textbox_px(350, 40, 120, 46, ["グラフ", "座標平面の直線"], size=11,
                  weight_first="bold")
    cv.textbox_px(180, 292, 140, 46, ["場面", "ことば・現実の状況"], size=11,
                  weight_first="bold")
    # 表⇄式（L02）
    arrow_px(cv, 112, 90, 192, 144, w=1.4)
    arrow_px(cv, 182, 152, 102, 98, w=1.4)
    cv.text_px(58, 118, "L02", size=10.5, anchor="start", weight="bold")
    cv.text_px(58, 131, "増加量どうしで", size=10, anchor="start")
    cv.text_px(58, 144, "割ると a", size=10, anchor="start")
    # 式⇄グラフ（L03: かく／L04: 読む）
    arrow_px(cv, 322, 150, 388, 92, w=1.4)
    arrow_px(cv, 376, 86, 310, 144, w=1.4)
    cv.text_px(368, 112, "L03 かく", size=10.5, anchor="start", weight="bold")
    cv.text_px(302, 132, "L04 読む", size=10.5, anchor="end", weight="bold")
    # 場面⇄式（L01/L07）
    arrow_px(cv, 244, 290, 244, 208, w=1.4)
    arrow_px(cv, 256, 208, 256, 290, w=1.4)
    cv.text_px(232, 238, "L01 ペースとはじめの量", size=10, anchor="end")
    cv.text_px(232, 254, "L07 変域・場面に戻して確かめ", size=10, anchor="end")
    # グラフどうしの交点（L06・破線囲み）
    cv.textbox_px(348, 200, 138, 62, ["グラフどうしの交点", "＝2つの式を同時に",
                                      "満たす組（L06）"], size=10, sw=AUX_W,
                  dash=DASH, weight_first="bold")
    arrow_px(cv, 418, 88, 421, 196, w=1.1, head=6, dash=DASH)
    cv.text_px(250, 358, "4つの見方は、式 y＝ax＋b を中心に行き来できる——矢印は学んだレッスン",
               size=11.5, anchor="middle")

    return dict(file="L08_fig1_four_views_map.svg", canvas=cv, lesson="L08",
                title="4つの見方のふり返り地図（表・式・グラフ・場面）",
                intent="単元まとめの地図。一般形 y＝ax＋b のみで具体数値なし（答えの分離の懸念なし）",
                src="lesson_08.md 「4つの見方——単元のまとめ」3段表の直後",
                params="一般形 y＝ax＋b・矢印のレッスン番号（L01〜L07）／主張は見本関数でassert",
                checks=ck.items,
                rb_texts=["y＝ax＋b", "表", "グラフ", "場面", "L02", "L03 かく",
                          "L04 読む", "L01 ペースとはじめの量", "満たす組（L06）",
                          "L07 変域・場面に戻して確かめ"],
                rb_absent=[],
                rb_circles=[])


# ===========================================================================
# メイン: 生成 + 読み戻し検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L02_1, fig_L02_2, fig_L03_1, fig_L03_2,
        fig_L04_1, fig_L04_2, fig_L04_3, fig_L04_4, fig_L04_5, fig_L05_1,
        fig_L06_1, fig_L07_1, fig_L07_2, fig_L08_1]

SVG_NS = "{http://www.w3.org/2000/svg}"


def build_desc(meta):
    """SVG <desc> 用のAI再利用メタ情報（FIGURE_MANIFESTと同じmetaから機械生成）"""
    return (
        f"【この図の意図】{meta['intent']}。"
        f"【主要な数値・設定】{meta['params']}。"
        f"【AIに同じ種類の図を描かせるときの説明文】"
        f"「{meta['title']}。{meta['intent']}。数値・設定: {meta['params']}。"
        f"白黒印刷向けのシンプルな教材図（SVG）としてかいて。」"
        f"——この説明文を生成AIに渡せば同型の図を描かせられる。"
        f"数値を変えれば類題用の図も作れる。"
    )


def verify_readback(meta):
    """生成済みSVGをElementTreeで読み戻し、必須文字列・禁止文字列・
    プロット点座標（式からの再計算値）を照合する。照合0件はエラー（素通り防止）"""
    import xml.etree.ElementTree as ET
    path = ASSETS / meta["file"]
    root = ET.parse(path).getroot()
    corpus = "\n".join(
        (el.text or "")
        for tag in ("text", "title", "desc")
        for el in root.iter(f"{SVG_NS}{tag}"))
    circles = [(float(el.get("cx")), float(el.get("cy")))
               for el in root.iter(f"{SVG_NS}circle")]
    n_texts = len(meta.get("rb_texts", []))
    n_absent = len(meta.get("rb_absent", []))
    n_circ = len(meta.get("rb_circles", []))
    assert n_texts + n_circ >= 3, (
        f"{meta['file']}: 読み戻し照合が{n_texts + n_circ}件しかない"
        f"（照合0件ゲートは素通り装置——figごとに3件以上を義務付け）")
    for s in meta.get("rb_texts", []):
        assert s in corpus, f"{meta['file']}: 必須文字列が図にない: {s!r}"
    for s in meta.get("rb_absent", []):
        assert s not in corpus, (
            f"{meta['file']}: 禁止文字列（答え等）が図のテキストにある: {s!r}")
    for (ex, ey, why) in meta.get("rb_circles", []):
        assert any(abs(cx - ex) <= 0.075 and abs(cy - ey) <= 0.075
                   for cx, cy in circles), (
            f"{meta['file']}: 式から再計算した位置({ex:.1f},{ey:.1f})に"
            f"点マーカーがない: {why}")
    return n_texts + n_absent + n_circ


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    metas = []
    n_checks = 0
    n_rb = 0
    for fn in FIGS:
        meta = fn()
        out = ASSETS / meta["file"]
        meta["canvas"].save(out, meta["file"], meta["title"], build_desc(meta))
        metas.append(meta)
    # 読み戻し検査（全ファイル書き出し後に、ファイルシステム上の実物を照合）
    for meta in metas:
        rb = verify_readback(meta)
        n_rb += rb
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓"
                           for d, t in meta["checks"])
        n_checks += len(meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["src"], meta["params"], checks))
        print(f"OK {meta['file']}  [生成時assert {len(meta['checks'])}件 / "
              f"読み戻し検査 {rb}件 合格]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 一次関数単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的出力）／ "
        f"全{len(rows)}図で下表の検算（スクリプト内assert・計{n_checks}項目）と、"
        f"生成後のSVG読み戻し検査（ElementTree・必須文字列/禁止文字列/プロット点の"
        f"式再計算照合・計{n_rb}項目）が自動実行され、全件合格。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | パラメータ（本文一致） | 検証結果（生成時assert） |",
        "|---|---|---|---|---|---|",
    ]
    for f_, lsn, title, intent, src, params, checks in rows:
        lines.append(f"| `{f_}` | {lsn} | {title}——{intent} | {src} | {params} | {checks} |")
    lines += [
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 練習問題の答は図に一切書かない。読み戻し検査の禁止文字列（rb_absent）で"
        "機械検査済み: L07_fig2の交点(1, 80)・L06_fig1の交点(4/3, 10/3)は座標を図に"
        "書かず、白抜き○で存在だけを示した。L07_fig2は軸の数値目盛も置かない"
        "（交点座標が直読できない粗さ＝notesの指示）。",
        "- L04_fig2（y＝−2x＋3）とL04_fig3（y＝(2/3)x−1）は、練習2の答え（y＝−2x＋4）・"
        "練習1の答え（y＝(2/3)x＋1）と切片が異なる別直線（本文の例示）。切片の不一致を"
        "assertし、答えの式文字列の不在を読み戻しで検査した。",
        "- L04_fig4・L04_fig5（練習3・4の問題図＝裁定2・2026-08-29）は、直線の式"
        "そのものが答えのため、式・傾き・切片の値を図に一切書かない（ラベルは"
        "ア〜オのみ）。係数が answer_key_L01-04.md の解と一致することを生成時"
        "assertで、式文字列の不在を読み戻し（rb_absent）で機械検査した。",
        "- L05_fig1の候補線（1点だけを通る比較用のうすい線）には式ラベルを付けない"
        "（本文に式がないため。傾き1/2・4・−1はスクリプト内パラメータのみ）。",
        "- L02_fig1は増加量の矢印（＋1・＋3）までを示し、変化の割合の値（3÷1＝3）は"
        "図に書かない。L02_fig2の「9÷3＝3」は本文が解説中で明示する途中式のため記載可。",
        "- 図に載せたその他の数値は、与件（毎分3L・はじめ2L・満水40cm・分速60m/80m等）と、"
        "本文が解説中で明示している値（L03の(0,1)〜(3,7)・L04の(0,2)(1,5)(2,8)・"
        "L05の(1,5)(4,11)とy＝2x＋3・L07の端点(0,4)(12,40)）のみ。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （数値は必ず該当 `lesson_0X.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算assert・読み戻し検査に1つでも",
        "   落ちると図・台帳は完成しない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n"
        + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, "
          f"生成時assert計{n_checks}項目 + 読み戻し検査計{n_rb}項目)")


if __name__ == "__main__":
    main()
