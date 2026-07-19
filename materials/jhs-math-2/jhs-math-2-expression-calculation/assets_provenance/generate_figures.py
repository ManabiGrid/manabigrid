#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2数学「式の計算」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。
ヘルパー群（Canvas/寸法線/ハッチ/矢印ほか）は先行単元
materials/jhs-math-3/jhs-math-3-quadratic-equations/assets_provenance/generate_figures.py
（元は jhs-math-3-similar-figures）からコピー再利用（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（10枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない（係数の計算・代入検算・恒等式・
  トラックの周長差など、本文の数値との一致を検算）。
- 答えの分離方針: 近隣の練習・設問の答（L03練習3(2)の−2a−b・L07練習1の9(a−b)・
  L09練習2の4π/S1の2πaなど）は図に書かない。禁止文字列は main() で機械検査する。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
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
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
DOT_R = 2.5       # 点マーカー半径


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き に変換して描く）
# 先行単元 generate_figures.py からコピー再利用（無変更）
# ===========================================================================
class Canvas:
    def __init__(self, width, height, scale=1.0, ox=0.0, oy=0.0):
        """scale: 数学単位→px、(ox,oy): 数学原点のSVG座標（yはoyから上向きに減る）"""
        self.w, self.h = width, height
        self.s, self.ox, self.oy = scale, ox, oy
        self.defs = []
        self.body = []

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

    def polygon(self, pts, w=MAIN_W, fill="none", dash=None):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="#000" '
                 f'stroke-width="{w}"{d} stroke-linejoin="round"/>')

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

    def circle_open(self, p, r=DOT_R + 1.0):
        """白抜き丸（数直線の「含まない」等ではなく、種類の区別用マーカー）"""
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                 f'stroke="#000" stroke-width="1.4"/>')

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None):
        x, y = self.P(p)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS_CAP, anchor="start", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def dim(self, a, b, label, offset=(0, 0), tick=4.0, size=FS, away=None,
            lab_off=13.0):
        """寸法線: 細線+両端ティック+ラベル。offsetは数学座標のずらし量。"""
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
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if away is None:
                mm = ((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2)
                self.text(mm, label, size=size, dy=(1.15 if ny > 0 else -0.55))
            else:
                ax, ay = self.P(away)
                side = 1.0 if (mx - ax) * nx + (my - ay) * ny >= 0 else -1.0
                lx, ly = mx + nx * side * lab_off, my + ny * side * lab_off
                if abs(nx * side) > 0.7:
                    anchor = "start" if nx * side > 0 else "end"
                else:
                    anchor = "middle"
                self.text_px(lx, ly + size * 0.35, label, size=size,
                             anchor=anchor)

    def add_hatch(self):
        """濃淡+ハッチングの塗り分けパターン（§4）を内蔵defsへ"""
        self.defs.append(
            '<pattern id="h45" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>'
            '<pattern id="h135" width="6" height="6" patternUnits="userSpaceOnUse" '
            'patternTransform="rotate(135)"><line x1="0" y1="0" x2="0" y2="6" '
            'stroke="#555" stroke-width="1.1"/></pattern>')

    # 概念図・系統図用（SVG座標pxで直接描く） --------------------------------
    def rect_px(self, x, y, w, h, sw=MAIN_W, dash=None, fill="#fff", rx=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
                 f'{r} fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')

    def textbox_px(self, x, y, w, h, lines, size=FS, sw=MAIN_W, dash=None,
                   weight_first=None, line_gap=1.35, fill="#fff"):
        """枠+中央ぞろえ複数行テキスト。lines=[行1, 行2, ...]"""
        self.rect_px(x, y, w, h, sw=sw, dash=dash, rx=4, fill=fill)
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


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0, dash=None):
    """SVG座標(px)で矢印（線+先端の三角形）を描く。概念図・系統図用"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="#000" stroke-width="{w}"{d}/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')


class Checker:
    """検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


# ===========================================================================
# 図1: L01 項に分ける——符号ごと切り取り、同類項をまとめる（7a−2−4a＋6）
# 本文根拠: lesson_01.md 主概念1（7a−2−4a＋6 → 項7a・−2・−4a・6 → 3a＋4）
# 答え漏れ注意: 練習の答（4a＋4・2x＋3など）は図に書かない。3a＋4は本文明示の解説値
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md 主概念1 と一致させる） ---
    c1, c0 = (7, -4), (-2, 6)      # 文字aの項の係数 / 数の項

    ck = Checker()
    ck.ok("同類項の係数の和: 7＋(−4)＝3（本文の3aと一致）", sum(c1) == 3)
    ck.ok("数の項の和: −2＋6＝4（本文の4と一致）", sum(c0) == 4)
    ck.ok("代入検算: a＝2で元の式7a−2−4a＋6＝結果3a＋4＝10（本文の型どおり1以外の数）",
          all(c1[0] * a + c0[0] + c1[1] * a + c0[1] == sum(c1) * a + sum(c0)
              for a in (2, 3, -1)) and 7 * 2 - 2 - 4 * 2 + 6 == 10)

    cv = Canvas(440, 250)
    cv.add_hatch()
    # 上段: 元の式と切り取り位置（＋・−の直前に破線のハサミ線）
    cv.text_px(220, 40, "7a − 2 − 4a ＋ 6", size=20, anchor="middle",
               weight="bold")
    for cx in (156, 208, 272):      # 各符号の直前
        cv.raw(f'<line x1="{cx}" y1="20" x2="{cx}" y2="52" stroke="#000" '
               f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    cv.text_px(220, 68, "ハサミを入れるのは、いつも ＋・− の直前（符号ごと切り取る）",
               size=FS_CAP, anchor="middle")
    # 中段: 4つの項の箱（aの項＝斜線ハッチ、数の項＝白）
    terms = [("7a", True), ("−2", False), ("−4a", True), ("＋6", False)]
    bw, bh, gap, x0, by = 76, 40, 22, 32, 92
    for i, (t, is_a) in enumerate(terms):
        bx = x0 + i * (bw + gap)
        if is_a:
            cv.rect_px(bx, by, bw, bh, sw=MAIN_W, rx=4, fill="url(#h45)")
            cv.text_px(bx + bw / 2, by + bh / 2 + 5, t, size=16,
                       anchor="middle", weight="bold")
        else:
            cv.textbox_px(bx, by, bw, bh, [t], size=16, weight_first="bold")
        arrow_px(cv, 156 + (i - 1.5) * 42, 74, bx + bw / 2, by - 4, w=1.1)
    cv.text_px(220, 152, "斜線＝文字の部分が a の項　　白＝数の項", size=FS_CAP,
               anchor="middle")
    # 下段: 同類項どうしをまとめる
    arrow_px(cv, x0 + bw / 2, by + bh + 24, 120, 196, w=1.4)          # 7a
    arrow_px(cv, x0 + 2 * (bw + gap) + bw / 2, by + bh + 24, 140, 196, w=1.4)  # −4a
    arrow_px(cv, x0 + (bw + gap) + bw / 2, by + bh + 24, 296, 196, w=1.4)      # −2
    arrow_px(cv, x0 + 3 * (bw + gap) + bw / 2, by + bh + 24, 316, 196, w=1.4)  # ＋6
    cv.text_px(130, 216, "7a −4a → 3a", size=15, anchor="middle", weight="bold")
    cv.text_px(306, 216, "−2 ＋6 → 4", size=15, anchor="middle", weight="bold")
    cv.text_px(220, 242, "文字の部分が同じ項どうしだけをまとめる → 3a＋4",
               size=FS, anchor="middle", weight="bold")

    return dict(file="L01_fig1_terms_split_and_group.svg", canvas=cv, lesson="L01",
                title="項に分ける（符号ごと切り取り→同類項をまとめて3a＋4）",
                intent="主概念1の可視化。切り取り位置＝符号の直前・同類項の仕分けを図解。"
                       "練習の答は書かない（3a＋4は本文明示の解説値）",
                src="lesson_01.md 主概念1",
                params="式7a−2−4a＋6／aの項7a・−4a→3a／数の項−2・6→4",
                checks=ck.items)


# ===========================================================================
# 図2: L02 同類項の仕分け（5x＋3y−2x＋y → 3x＋4y・xとyはまとめられない）
# 本文根拠: lesson_02.md 主概念3（5x＋3y−2x＋y＝3x＋4y／7xyは別の式）
# 答え漏れ注意: 練習2の答（4x＋7y・4a−5bなど）は図に書かない
# ===========================================================================
def fig_L02():
    # --- パラメータ（本文 lesson_02.md 主概念3 と一致させる） ---
    cx_, cy_ = (5, -2), (3, 1)     # xの項の係数 / yの項の係数

    ck = Checker()
    ck.ok("xの同類項: 5＋(−2)＝3（本文の3xと一致）", sum(cx_) == 3)
    ck.ok("yの同類項: 3＋1＝4（本文の4yと一致）", sum(cy_) == 4)
    ck.ok("代入検算: x＝2、y＝1で元の式＝10＝3x＋4y（本文の検算と同じ値）",
          5 * 2 + 3 * 1 - 2 * 2 + 1 == 10 and 3 * 2 + 4 * 1 == 10)
    ck.ok("7xyは別の式: x＝2、y＝1で7xy＝14≠10（本文の誤答例と一致）",
          7 * 2 * 1 == 14 and 14 != 10)

    cv = Canvas(440, 262)
    cv.add_hatch()
    cv.text_px(220, 34, "5x ＋ 3y − 2x ＋ y", size=20, anchor="middle",
               weight="bold")
    # 中段: 2つのトレイ（x班＝斜線45度、y班＝斜線135度）
    tx, ty_, tw, th = 48, 84, 150, 84
    cv.rect_px(tx, ty_, tw, th, sw=MAIN_W, rx=6, fill="url(#h45)")
    cv.rect_px(242, ty_, tw, th, sw=MAIN_W, rx=6, fill="url(#h135)")
    cv.text_px(tx + tw / 2, ty_ + 24, "文字の部分が x", size=FS_CAP,
               anchor="middle", weight="bold")
    cv.text_px(242 + tw / 2, ty_ + 24, "文字の部分が y", size=FS_CAP,
               anchor="middle", weight="bold")
    cv.text_px(tx + tw / 2, ty_ + 52, "5x　−2x", size=16, anchor="middle",
               weight="bold")
    cv.text_px(242 + tw / 2, ty_ + 52, "3y　＋y", size=16, anchor="middle",
               weight="bold")
    cv.text_px(tx + tw / 2, ty_ + 74, "→ 3x", size=15, anchor="middle")
    cv.text_px(242 + tw / 2, ty_ + 74, "→ 4y", size=15, anchor="middle")
    # 式の各項からトレイへの矢印
    arrow_px(cv, 138, 42, tx + 40, ty_ - 4, w=1.1)        # 5x
    arrow_px(cv, 258, 42, tx + 110, ty_ - 4, w=1.1)       # −2x
    arrow_px(cv, 196, 42, 242 + 40, ty_ - 4, w=1.1)       # 3y
    arrow_px(cv, 306, 42, 242 + 110, ty_ - 4, w=1.1)      # ＋y
    # 下段: まとめられない
    cv.text_px(220, 202, "3x ＋ 4y", size=19, anchor="middle", weight="bold")
    cv.text_px(220, 228, "x と y は文字の部分が違う＝同類項ではない → これ以上まとめられない",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 248, "（7xy とまとめるのは誤り。x＝2、y＝1 の代入がすぐ暴く）",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_like_terms_sorting.svg", canvas=cv, lesson="L02",
                title="同類項の仕分け（5x＋3y−2x＋y→3x＋4y・xとyはまとめられない）",
                intent="主概念3の可視化。x班とy班のトレイ仕分けで「文字の部分が同じ？」を図解。"
                       "練習の答は書かない（3x＋4yは本文明示の解説値）",
                src="lesson_02.md 主概念3",
                params="式5x＋3y−2x＋y／x班5x・−2x→3x／y班3y・y→4y／誤答7xyの注意書き",
                checks=ck.items)


# ===========================================================================
# 図3: L03 分配は「全員に配る」（3(2a−5b)と、−(2x−3y)＝(−1)の分配）
# 本文根拠: lesson_03.md 主概念1（−(2x−3y)＝−2x＋3y）・主概念2（3(2a−5b)＝6a−15b）
# 答え漏れ注意: 練習の答（8a−4b・−2a−bなど）は図に書かない
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md と一致させる） ---
    k = 3
    t1, t2 = 2, -5          # 3(2a−5b)
    m1, m2 = 2, -3          # −(2x−3y)

    ck = Checker()
    ck.ok("分配の係数: 3×2＝6・3×(−5)＝−15（本文の6a−15bと一致）",
          k * t1 == 6 and k * t2 == -15)
    ck.ok("代入検算: a＝2、b＝1で3(2a−5b)＝−3＝6a−15b（複数の値で一致）",
          all(k * (t1 * a + t2 * b) == k * t1 * a + k * t2 * b
              for a, b in ((2, 1), (3, 2), (-1, 4))))
    ck.ok("−1の分配: (−1)×2＝−2・(−1)×(−3)＝＋3（本文の−2x＋3yと一致）",
          -1 * m1 == -2 and -1 * m2 == 3)
    ck.ok("代入検算: x＝2、y＝1で−(2x−3y)＝−1＝−2x＋3y（複数の値で一致）",
          all(-(m1 * x + m2 * y) == -m1 * x - m2 * y
              for x, y in ((2, 1), (3, 2), (-2, 5))))

    cv = Canvas(440, 252)

    def dist_panel(y0, head, a_txt, b_txt, res, note):
        """1段分: 係数→かっこ内2項への曲線矢印と結果"""
        cv.text_px(96, y0, head, size=19, anchor="middle", weight="bold")
        # 係数から各項への矢印（かっこの上をまたぐ弧の代わりに折れ線矢印）
        x_k = 96 - len(head) * 4.6         # 係数のおよその位置
        cv.raw(f'<path d="M {x_k:.0f} {y0 - 18} Q {x_k + 26:.0f} {y0 - 34} '
               f'{x_k + 46:.0f} {y0 - 20}" fill="none" stroke="#000" '
               f'stroke-width="1.2"/>')
        arrow_px(cv, x_k + 44, y0 - 22, x_k + 48, y0 - 18, w=1.2, head=6)
        cv.raw(f'<path d="M {x_k:.0f} {y0 - 18} Q {x_k + 52:.0f} {y0 - 44} '
               f'{x_k + 94:.0f} {y0 - 20}" fill="none" stroke="#000" '
               f'stroke-width="1.2"/>')
        arrow_px(cv, x_k + 92, y0 - 24, x_k + 96, y0 - 18, w=1.2, head=6)
        arrow_px(cv, 178, y0 - 6, 226, y0 - 6, w=1.4)
        cv.text_px(296, y0, res, size=19, anchor="middle", weight="bold")
        cv.text_px(296, y0 + 22, note, size=11, anchor="middle")

    cv.text_px(220, 30, "分配法則——外の数は、かっこの中の全員に配る", size=FS,
               anchor="middle", weight="bold")
    dist_panel(96, "3(2a−5b)", "2a", "−5b", "6a−15b",
               "3×2a と 3×(−5b)——符号ごとかける")
    dist_panel(186, "−(2x−3y)", "2x", "−3y", "−2x＋3y",
               "−は(−1)×のこと。(−1)×(−3y)＝＋3y")
    cv.text_px(220, 240, "事故が起きるのは決まって後半の項。−も、最後の項まで全員に配る",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_distribute_to_all.svg", canvas=cv, lesson="L03",
                title="分配は全員に配る（3(2a−5b)＝6a−15b・−(2x−3y)＝−2x＋3y）",
                intent="主概念1・2の可視化。係数から各項への矢印で「全員に配る」を図解。"
                       "練習の答は書かない（6a−15b・−2x＋3yは本文明示の解説値）",
                src="lesson_03.md 主概念1・主概念2",
                params="上段3(2a−5b)→6a−15b／下段−(2x−3y)＝(−1)の分配→−2x＋3y",
                checks=ck.items)


# ===========================================================================
# 図4: L05 偶数2n・奇数2n＋1の数直線（1本の式が無限個の身分証明書）
# 本文根拠: lesson_05.md 主概念1（偶数2n・奇数2n＋1・nは整数）
# 答え漏れ注意: 練習の答（5n・2n−1・n＋1・3n＋1など）は図に書かない
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（本文 lesson_05.md 主概念1 と一致させる） ---
    n_range = range(0, 5)          # n＝0..4 → 偶数0,2,4,6,8

    ck = Checker()
    evens = [2 * n for n in n_range]
    odds = [2 * n + 1 for n in n_range]
    ck.ok("2nはすべて偶数（n＝0..4で0,2,4,6,8）",
          all(e % 2 == 0 for e in evens), f"{evens}")
    ck.ok("2n＋1はすべて奇数（n＝0..4で1,3,5,7,9）",
          all(o % 2 == 1 for o in odds), f"{odds}")
    ck.ok("偶数どうし・奇数どうしの間隔は2（連続する偶数＝2nと2n＋2の根拠）",
          all(evens[i + 1] - evens[i] == 2 for i in range(len(evens) - 1)))

    cv = Canvas(440, 200, scale=42, ox=32, oy=104)
    # 数直線
    cv.line((-0.3, 0), (9.4, 0), w=MAIN_W)
    arrow_px(cv, *cv.P((9.1, 0)), *(lambda p: (p[0] + 12, p[1]))(cv.P((9.1, 0))),
             w=MAIN_W)
    for v in range(0, 10):
        cv.line((v, -0.08), (v, 0.08), w=1.1)
        cv.text((v, -0.34), str(v), size=FS)
    # 偶数＝黒丸（上側ラベル2n）、奇数＝白抜き丸（下側ラベル2n＋1）
    for e in evens:
        cv.dot((e, 0.30), r=4.0)
    for o in odds:
        cv.circle_open((o, 0.30), r=4.0)
    cv.text((4, 1.05), "●＝偶数 2n　　○＝奇数 2n＋1　（n は整数）", size=FS,
            weight="bold")
    cv.text_px(220, 158, "n に 0、1、2、3……を入れると、●が 0、2、4、6……と全部出てくる",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 178, "1本の式が、無限にある偶数の「製造機」になっている",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_even_odd_number_line.svg", canvas=cv, lesson="L05",
                title="数直線上の偶数2nと奇数2n＋1（nは整数）",
                intent="主概念1の可視化。●＝偶数2n・○＝奇数2n＋1が交互に並び、"
                       "間隔2で無限に続くことを示す。練習の答は書かない",
                src="lesson_05.md 主概念1",
                params="数直線0〜9／偶数0,2,4,6,8＝●／奇数1,3,5,7,9＝○／間隔2をassert",
                checks=ck.items)


# ===========================================================================
# 図5: L05 2けたの数は10a＋b（37＝10×3＋7・「ab」ではない）
# 本文根拠: lesson_05.md 主概念1（10a＋b・37は30＋7であって3×7＝21ではない）
# 答え漏れ注意: 練習2の答（10b＋a）は図に書かない（一般形10a＋bは本文明示の解説値）
# ===========================================================================
def fig_L05_2():
    # --- パラメータ（本文 lesson_05.md 主概念1 と一致させる） ---
    a, b = 3, 7                    # 例の数37

    ck = Checker()
    ck.ok("位の値の分解: 37＝10×3＋7（本文の例と一致）",
          10 * a + b == 37)
    ck.ok("誤答「ab」＝a×b＝21は別の数（本文の注意と一致）",
          a * b == 21 and a * b != 10 * a + b)
    ck.ok("一般形: 10a＋bはa,b＝1..9の全組で2けたの数（10〜99）",
          all(10 <= 10 * p + q <= 99 for p in range(1, 10) for q in range(0, 10)))

    cv = Canvas(440, 226)
    cv.add_hatch()
    # 上段: 具体例 37
    cv.text_px(110, 46, "37", size=26, anchor="middle", weight="bold")
    cv.text_px(110, 68, "十の位 3・一の位 7", size=FS_CAP, anchor="middle")
    arrow_px(cv, 150, 42, 200, 42, w=1.4)
    cv.rect_px(208, 22, 90, 36, sw=MAIN_W, rx=4, fill="url(#h45)")
    cv.text_px(253, 45, "10×3", size=15, anchor="middle", weight="bold")
    cv.text_px(310, 45, "＋", size=15, anchor="middle")
    cv.textbox_px(322, 22, 56, 36, ["7"], size=15, weight_first="bold")
    cv.text_px(293, 78, "＝ 30＋7（3×7＝21 ではない）", size=FS_CAP,
               anchor="middle")
    # 下段: 一般形 10a＋b
    cv.text_px(110, 138, "十の位 a", size=15, anchor="middle", weight="bold")
    cv.text_px(110, 158, "一の位 b", size=15, anchor="middle", weight="bold")
    arrow_px(cv, 158, 144, 200, 144, w=1.4)
    cv.rect_px(208, 124, 90, 36, sw=MAIN_W, rx=4, fill="url(#h45)")
    cv.text_px(253, 147, "10×a", size=15, anchor="middle", weight="bold")
    cv.text_px(310, 147, "＋", size=15, anchor="middle")
    cv.textbox_px(322, 124, 56, 36, ["b"], size=15, weight_first="bold")
    cv.text_px(293, 180, "＝ 10a＋b（「ab」と書くと a×b の意味になる）",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 212, "位の値×個数の和で組み立てる——斜線の箱が「十の位のかたまり」",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig2_place_value_10a_plus_b.svg", canvas=cv,
                lesson="L05",
                title="2けたの数は10a＋b（37＝10×3＋7）",
                intent="主概念1の可視化。具体例37と一般形10a＋bを並置し、"
                       "「ab＝a×b」との違いを注意書き。練習2の答（入れかえた数の式）は書かない",
                src="lesson_05.md 主概念1",
                params="例37＝10×3＋7／一般形10a＋b／誤答例3×7＝21",
                checks=ck.items)


# ===========================================================================
# 図6: L06 式による説明の4ステップ（二つの奇数の和は偶数）
# 本文根拠: lesson_06.md 主概念1（表す→計算・変形→読む→結論）
# 答え漏れ注意: 足場1の答（2n・m＋n）・練習の答は図に書かない
# ===========================================================================
def fig_L06():
    ck = Checker()
    ck.ok("恒等式: (2m＋1)＋(2n＋1)＝2(m＋n＋1)（複数のm,nで成立）",
          all((2 * m + 1) + (2 * n + 1) == 2 * (m + n + 1)
              for m in (-2, 0, 1, 3) for n in (-1, 0, 2, 5)))
    ck.ok("読みの根拠: 2(m＋n＋1)は2×（整数）の形＝偶数（複数のm,nで偶数）",
          all((2 * (m + n + 1)) % 2 == 0 for m in (-2, 0, 3) for n in (-1, 2, 5)))
    ck.ok("本文の導入例と整合: 3＋5＝8・7＋11＝18・23＋9＝32はすべて偶数",
          all(s % 2 == 0 for s in (3 + 5, 7 + 11, 23 + 9)))

    cv = Canvas(440, 344)
    steps = [
        ("ステップ1: 表す", ["m、n を整数とすると", "二つの奇数は 2m＋1、2n＋1"]),
        ("ステップ2: 計算・変形する", ["(2m＋1)＋(2n＋1)", "＝2m＋2n＋2＝2(m＋n＋1)"]),
        ("ステップ3: 読む", ["m＋n＋1 は整数だから", "2×（整数）の形＝偶数"]),
        ("ステップ4: 結論", ["したがって", "二つの奇数の和は偶数になる"]),
    ]
    bw, bh, x0, y0, gap = 300, 58, 70, 26, 16
    for i, (head, lines) in enumerate(steps):
        by = y0 + i * (bh + gap)
        cv.textbox_px(x0, by, bw, bh, [head] + lines, size=12,
                      weight_first="bold")
        if i < 3:
            arrow_px(cv, x0 + bw / 2, by + bh + 2, x0 + bw / 2,
                     by + bh + gap - 2, w=1.6)
    # わきの注記
    cv.text_px(x0 + bw + 8, y0 + 2 * (bh + gap) + bh / 2 - 6, "忘れられ", size=10)
    cv.text_px(x0 + bw + 8, y0 + 2 * (bh + gap) + bh / 2 + 6, "やすい！", size=10)
    cv.text_px(220, 330, "ステップ3を飛ばすと「計算しただけ」で説明にならない",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_four_step_explanation.svg", canvas=cv,
                lesson="L06",
                title="式による説明の4ステップ（二つの奇数の和は偶数）",
                intent="主概念1の流れの可視化。表す→計算・変形→読む→結論を縦に接続。"
                       "足場1・練習の答は書かない（例の式は本文明示の解説）",
                src="lesson_06.md 主概念1",
                params="例＝二つの奇数の和／(2m＋1)＋(2n＋1)＝2(m＋n＋1)／読み＝2×（整数）",
                checks=ck.items)


# ===========================================================================
# 図7: L07 入れかえた数との和（10a＋bと10b＋a→11(a＋b)・例52＋25＝77）
# 本文根拠: lesson_07.md 導入・主概念1
# 答え漏れ注意: 練習1の答（9(a−b)・9a−9b＝差の説明）は図に書かない（和のみ扱う）
# ===========================================================================
def fig_L07():
    # --- パラメータ（本文 lesson_07.md と一致させる） ---
    a, b = 5, 2                    # 例の数52

    ck = Checker()
    ck.ok("例: 52＋25＝77＝11×7（本文の導入と一致）",
          (10 * a + b) + (10 * b + a) == 77 and 77 == 11 * 7)
    ck.ok("a＋b＝7が11×7の7の正体（本文の解説と一致）", a + b == 7)
    ck.ok("恒等式: (10a＋b)＋(10b＋a)＝11(a＋b)（a,b＝1..9の全81組で成立）",
          all((10 * p + q) + (10 * q + p) == 11 * (p + q)
              for p in range(1, 10) for q in range(1, 10)))

    cv = Canvas(440, 262)
    cv.add_hatch()
    # 左: 位の箱の縦並び（もとの数・入れかえた数）
    def num_row(y, ten, one, label):
        cv.rect_px(60, y, 92, 38, sw=MAIN_W, rx=4, fill="url(#h45)")
        cv.text_px(106, y + 24, ten, size=15, anchor="middle", weight="bold")
        cv.textbox_px(160, y, 64, 38, [one], size=15, weight_first="bold")
        cv.text_px(240, y + 24, label, size=FS_CAP)

    cv.text_px(106, 30, "十の位", size=FS_CAP, anchor="middle")
    cv.text_px(192, 30, "一の位", size=FS_CAP, anchor="middle")
    num_row(42, "10×a", "b", "もとの数 10a＋b")
    cv.text_px(142, 112, "↓ 位を入れかえる", size=FS_CAP, anchor="middle")
    num_row(126, "10×b", "a", "入れかえた数 10b＋a")
    # 右下: 和
    cv.text_px(220, 204, "和＝(10a＋b)＋(10b＋a)＝11a＋11b＝11(a＋b)",
               size=15, anchor="middle", weight="bold")
    cv.text_px(220, 230, "a＋b は整数 → 11×（整数）の形＝11の倍数",
               size=FS, anchor="middle")
    cv.text_px(220, 252, "（例: 52＋25＝77＝11×7。a＋b＝5＋2＝7 が「7」の正体）",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig1_digit_swap_sum.svg", canvas=cv, lesson="L07",
                title="入れかえた数との和は11(a＋b)（例52＋25＝77）",
                intent="主概念1の可視化。位の箱の入れかえと和の変形を図解。"
                       "練習1（差の説明）の答は書かない（和のみ・本文明示の解説値）",
                src="lesson_07.md 導入・主概念1",
                params="もとの数10a＋b／入れかえた数10b＋a／和11(a＋b)／例52＋25＝77",
                checks=ck.items)


# ===========================================================================
# 図8: L08 等式の変形（S＝(1/2)ah ⇔ a＝2S/h・公式の向きが変わる）
# 本文根拠: lesson_08.md 導入・主概念1
# 答え漏れ注意: 練習の答（x＝9−3y・y＝4x−7・c＝V/(ab)など）は図に書かない
# ===========================================================================
def fig_L08():
    ck = Checker()
    ck.ok("往復の検算: a＝2S/hをS＝(1/2)ahに戻すと(1/2)×(2S/h)×h＝S（複数の値で成立）",
          all(abs(0.5 * (2 * S / h) * h - S) < 1e-9
              for S in (14.0, 24.0, 7.5) for h in (4.0, 5.0, 2.5)))
    ck.ok("変形の各段: 両辺×2でS→2S＝ah、両辺÷hで2S/h＝a（S＝14,a＝7,h＝4の数値例）",
          abs(0.5 * 7 * 4 - 14) < 1e-9 and abs(2 * 14 - 7 * 4) < 1e-9
          and abs(2 * 14 / 4 - 7) < 1e-9)

    cv = Canvas(440, 264)
    cv.text_px(220, 36, "a について解く", size=FS, anchor="middle",
               weight="bold")
    # 左の箱: 面積を出す向き
    cv.textbox_px(28, 56, 168, 74,
                  ["S＝(1/2)ah", "底辺 a と高さ h から", "面積 S を出す公式"],
                  size=12, weight_first="bold")
    # 右の箱: 底辺を出す向き
    cv.textbox_px(244, 56, 168, 74,
                  ["a＝2S/h", "面積 S と高さ h から", "底辺 a を出す公式"],
                  size=12, weight_first="bold")
    # 変形の向きの矢印
    arrow_px(cv, 200, 93, 240, 93, w=1.6)
    # 手順の段
    cv.text_px(220, 164, "S＝(1/2)ah　→（両辺に2をかける）→　2S＝ah",
               size=FS, anchor="middle")
    cv.text_px(220, 188, "→（両辺を h でわる）→　2S/h＝a", size=FS,
               anchor="middle")
    cv.text_px(220, 218, "使う道具は中1の等式の性質だけ。新しい魔法は何もない",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 240, "検算: a＝2S/h を元の式に戻すと (1/2)×(2S/h)×h＝S ✓",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig1_solve_for_a.svg", canvas=cv, lesson="L08",
                title="等式の変形（S＝(1/2)ah を a について解くと a＝2S/h）",
                intent="主概念1の可視化。同じ等式が「aを出す向き」に生まれ変わる流れと"
                       "手順2段（×2・÷h）。練習の答は書かない（a＝2S/hは本文明示の解説値）",
                src="lesson_08.md 導入・主概念1",
                params="S＝(1/2)ah⇔a＝2S/h／手順＝両辺×2→両辺÷h／往復検算をassert",
                checks=ck.items)


# ===========================================================================
# 図9: L09 トラックの内側・外側レーン（直線d・半径r・レーン幅1m・差は？）
# 本文根拠: lesson_09.md 導入（既存プレースホルダ assets/L09_fig1_track_lanes.svg）
# 答え漏れ注意: 差の値（本文解説2π・練習2の4π・S1の2πa）は図に書かない——「？」で示す
# ===========================================================================
def fig_L09():
    # --- パラメータ（本文 lesson_09.md と一致させる。描画用の具体値） ---
    d = 7.0            # 直線部分の長さ（描画比。ラベルはd m）
    r = 2.2            # 内側レーンの半円の半径（描画比。ラベルはr m）
    w_lane = 1.0       # レーン幅1m（与件・図に書いてよい）

    ck = Checker()
    # 半円を折れ線サンプリングで描く（SPEC§6）。サンプル点が正しく円上にあるか検算
    N = 60
    inner_pts_r, outer_pts_r = [], []
    for i in range(N + 1):
        th = -math.pi / 2 + math.pi * i / N
        inner_pts_r.append((d / 2 + r * math.cos(th), r * math.sin(th)))
        outer_pts_r.append((d / 2 + (r + w_lane) * math.cos(th),
                            (r + w_lane) * math.sin(th)))
    ck.ok("半円のサンプル点が半径r・r＋1の円上にある（右端・各61点）",
          all(abs(math.hypot(x - d / 2, y) - r) < 1e-9 for x, y in inner_pts_r)
          and all(abs(math.hypot(x - d / 2, y) - (r + w_lane)) < 1e-9
                  for x, y in outer_pts_r))
    inner_len = 2 * d + 2 * math.pi * r
    outer_len = 2 * d + 2 * math.pi * (r + w_lane)
    ck.ok("周長の式: 内側2d＋2πr・外側2d＋2π(r＋1)（本文の式と一致）",
          abs(inner_len - (2 * d + 2 * math.pi * r)) < 1e-9
          and abs(outer_len - (2 * d + 2 * math.pi * (r + w_lane))) < 1e-9)
    diff = outer_len - inner_len
    ck.ok("1周の差＝2π×レーン幅で、dにもrにも無関係（本文の結論と整合・図には書かない）",
          abs(diff - 2 * math.pi * w_lane) < 1e-9
          and abs((2 * 99 + 2 * math.pi * (50 + w_lane))
                  - (2 * 99 + 2 * math.pi * 50) - diff) < 1e-9)

    s = 32.0
    cv = Canvas(440, 292, scale=s, ox=220 - s * 0, oy=118)

    def track_ring(rad):
        """直線2本+左右の半円（折れ線近似）を1本の閉曲線で描く"""
        pts = []
        for i in range(N + 1):                    # 右の半円（下→上）
            th = -math.pi / 2 + math.pi * i / N
            pts.append((d / 2 + rad * math.cos(th), rad * math.sin(th)))
        for i in range(N + 1):                    # 左の半円（上→下）
            th = math.pi / 2 + math.pi * i / N
            pts.append((-d / 2 + rad * math.cos(th), rad * math.sin(th)))
        pts.append(pts[0])
        return pts

    cv.polyline(track_ring(r), w=MAIN_W)
    cv.polyline(track_ring(r + w_lane), w=MAIN_W)
    # 直線部分の寸法線（上の直線・内側レーンの内側に置く）
    cv.dim((-d / 2, r), (d / 2, r), "直線部分 d m", offset=(0, -0.7), size=FS,
           away=(0, -5))
    # 半径 r（右の半円の中心から内側の線へ）
    cv.dot((d / 2, 0), r=2.5)
    cv.line((d / 2, 0), (d / 2 + r * math.cos(-0.5), r * math.sin(-0.5)),
            w=AUX_W, dash=DASH)
    cv.text((d / 2 + 0.62 * r, -0.62 * r), "r m", size=FS)
    # レーン幅 1m（右側・内外の線の間）
    cv.dim((d / 2 + r, 0), (d / 2 + r + w_lane, 0), "1m",
           offset=(0, 0), size=12, away=(0, 0), lab_off=15)
    # ラベル（外側レーン名は内外の線の間・下の直線部分の中央）
    cv.text((0, -r - w_lane / 2), "外側のレーン", size=FS_CAP)
    cv.text((0, 0), "内側のレーン", size=FS_CAP)
    cv.text_px(220, 254, "外側のレーンは1周がどれだけ長い？——差は「？」m",
               size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 276, "（長方形の両端に半円。走る線の上で測る。外側の半円の半径は r＋1）",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_track_lanes.svg", canvas=cv, lesson="L09",
                title="両端が半円のトラック（直線d・内側の半径r・レーン幅1m）",
                intent="導入の場面図。求める1周の差は「？」で示し、答えの値は書かない",
                src="lesson_09.md 導入（20行目の既存参照）",
                params="直線d・内側半径r・レーン幅1m／半円は61点の折れ線近似／"
                       "差がd,rに無関係なことはassertのみで検算",
                checks=ck.items)


# ===========================================================================
# 図10: L09 同じ数の二つの顔（2(5n＋2)＋1は奇数でもあり5の倍数でもある）
# 本文根拠: lesson_09.md 主概念2（2(5n＋2)＋1＝10n＋5＝5(2n＋1)）
# 答え漏れ注意: 練習1・3の答（奇数・5の倍数の各判定など）は図に書かない
# ===========================================================================
def fig_L09_2():
    ck = Checker()
    ck.ok("整理: 2(5n＋2)＋1＝10n＋5（複数のnで成立）",
          all(2 * (5 * n + 2) + 1 == 10 * n + 5 for n in (-2, 0, 1, 2, 7)))
    ck.ok("読み①: 2×（整数）＋1の形＝奇数（複数のnで奇数）",
          all((2 * (5 * n + 2) + 1) % 2 == 1 for n in (-2, 0, 1, 2, 7)))
    ck.ok("読み②: 10n＋5＝5(2n＋1)＝5×（整数）の形＝5の倍数（複数のnで5の倍数）",
          all((10 * n + 5) == 5 * (2 * n + 1) and (10 * n + 5) % 5 == 0
              for n in (-2, 0, 1, 2, 7)))
    ck.ok("本文の数値例: n＝2で2(5×2＋2)＋1＝25（奇数かつ5の倍数）",
          2 * (5 * 2 + 2) + 1 == 25 and 25 % 2 == 1 and 25 % 5 == 0)

    cv = Canvas(440, 262)
    # 上段中央: もとの式
    cv.textbox_px(140, 22, 160, 40, ["2(5n＋2)＋1", "（n は整数）"], size=13,
                  weight_first="bold")
    # 左下: 奇数の顔
    cv.textbox_px(28, 130, 180, 66,
                  ["2(5n＋2)＋1 のまま見る", "＝2×（整数）＋1", "→ 奇数"],
                  size=12, weight_first=None)
    # 右下: 5の倍数の顔
    cv.textbox_px(232, 130, 180, 66,
                  ["10n＋5＝5(2n＋1) と変形", "＝5×（整数）", "→ 5の倍数"],
                  size=12, weight_first=None)
    arrow_px(cv, 190, 66, 118, 126, w=1.4)
    arrow_px(cv, 250, 66, 322, 126, w=1.4)
    cv.text_px(120, 100, "そのまま読む", size=11, anchor="middle")
    cv.text_px(322, 100, "変形して読む", size=11, anchor="middle")
    cv.text_px(220, 226, "同じ数が、どの形に整えるかで違う顔を見せる",
               size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 248, "変形の仕方の数だけ、読める事実がある（n＝2 なら 25——たしかに両方 ✓）",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig2_two_faces_of_expression.svg", canvas=cv,
                lesson="L09",
                title="同じ数の二つの顔（2(5n＋2)＋1は奇数でも5の倍数でもある）",
                intent="主概念2の可視化。1つの式から2通りの形へ分岐する読みの図解。"
                       "練習の答は書かない（25は本文明示の解説値）",
                src="lesson_09.md 主概念2",
                params="2(5n＋2)＋1＝10n＋5／読み①2×（整数）＋1／読み②5(2n＋1)／例n＝2で25",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + 答え漏れの機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02, fig_L03, fig_L05_1, fig_L05_2, fig_L06, fig_L07,
        fig_L08, fig_L09, fig_L09_2]

# 答え漏れの禁止文字列（近隣の練習・設問の答。answer_key と照合して選定）
FORBIDDEN = {
    "L01_fig1_terms_split_and_group.svg": ["4a＋4", "2x＋3", "5x＋2", "5x−2"],
    "L02_fig1_like_terms_sorting.svg": ["4x＋7y", "4a−5b", "−3x²＋4x", "5ab−4"],
    "L03_fig1_distribute_to_all.svg": ["8a−4b", "−2a−b", "5a−2b", "2x＋5y"],
    "L05_fig1_even_odd_number_line.svg": ["5n", "2n−1", "3n＋1"],
    "L05_fig2_place_value_10a_plus_b.svg": ["10b＋a"],
    "L06_fig1_four_step_explanation.svg": ["2(m＋n)", "2n＋1、n＋1"],
    "L07_fig1_digit_swap_sum.svg": ["9(a−b)", "9a−9b", "5(n", "9の倍数"],
    "L08_fig1_solve_for_a.svg": ["9−3y", "4x−7", "V/(ab)", "2m−a", "(3−4x)/2"],
    "L09_fig1_track_lanes.svg": ["2π", "4π", "6.28"],
    "L09_fig2_two_faces_of_expression.svg": ["2(m＋n)−1", "5n＋5", "10a＋5"],
}


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


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    n_checks = 0
    for fn in FIGS:
        meta = fn()
        out = ASSETS / meta["file"]
        meta["canvas"].save(out, meta["file"], meta["title"], build_desc(meta))
        # 答え漏れの機械検査（SPEC§5）: 禁止文字列がSVG全文にないこと
        svg_text = out.read_text(encoding="utf-8")
        for bad in FORBIDDEN.get(meta["file"], []):
            assert bad not in svg_text, f"答え漏れ検出: {meta['file']} に「{bad}」"
        meta["checks"].append(
            (f"答え漏れ検査: 禁止文字列{len(FORBIDDEN.get(meta['file'], []))}件が"
             "SVG全文に不在", ""))
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓"
                          for d, t in meta["checks"])
        n_checks += len(meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["src"], meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 式の計算単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。",
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
        "- 近隣の練習・設問の答（L01練習の4a＋4・L03練習の−2a−b・L05練習の5n/2n−1・"
        "L07練習1の9(a−b)・L08練習のy＝(3−4x)/2など・L09の差2π/4π/2πa）は図に書かない。",
        "- 図に載る式・数値はすべて該当レッスン本文が地の文で明示する解説値"
        "（3a＋4・3x＋4y・6a−15b・11(a＋b)・a＝2S/h・25など）に限る。",
        "- L09のトラック図は、求める1周の差を「？」で示し、答えの値（2π）は"
        "図・title・descのいずれにも書かない（assert内でのみ検算）。",
        "- 各図の禁止文字列は main() の FORBIDDEN 表で機械検査し、"
        "1件でも検出されれば生成が停止する。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算assertに1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines),
        encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")


if __name__ == "__main__":
    main()
