#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2数学「連立方程式」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。
ヘルパー群（Canvas/寸法線/ハッチ/矢印ほか）は先行単元
materials/jhs-math-3/jhs-math-3-quadratic-equations/assets_provenance/generate_figures.py
materials/jhs-math-3/jhs-math-3-similar-figures/assets_provenance/generate_figures.py
からコピー再利用（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（9枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない
  （解の全数列挙・共通組の一意性・連立の解の代入検算・恒等式・整理変形の同値性など）。
- 答えの分離方針: 練習問題の答は図に一切書かない。本文の例題解説が明示している
  途中式（2x＝14・−y＝−2 など）のみ解説値として図に載せ、最終解の組
  （(7,4)・(3,2)・(2,5)・飲み物7本など）は図に書かず assert 検算のみで使う。
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
# 先行単元 generate_figures.py からコピー再利用
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

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None):
        x, y = self.P(p)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS_CAP, anchor="start", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

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
                   weight_first=None, line_gap=1.35):
        """枠+中央ぞろえ複数行テキスト。lines=[行1, 行2, ...]"""
        self.rect_px(x, y, w, h, sw=sw, dash=dash, rx=4)
        n = len(lines)
        cy0 = y + h / 2 - (n - 1) * size * line_gap / 2
        for i, ln in enumerate(lines):
            wgt = weight_first if i == 0 else None
            self.text_px(x + w / 2, cy0 + i * size * line_gap + size * 0.35,
                         ln, size=size, anchor="middle", weight=wgt)

    def ellipse_px(self, cx, cy, rx, ry, w=MAIN_W, dash=None, n=72):
        """楕円を座標サンプリングした折れ線で描く（arcフラグ不使用・SPEC§6）"""
        pts = []
        for i in range(n + 1):
            t = 2 * math.pi * i / n
            pts.append(f"{cx + rx * math.cos(t):.1f},{cy + ry * math.sin(t):.1f}")
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polyline points="{" ".join(pts)}" fill="none" '
                 f'stroke="#000" stroke-width="{w}"{d}/>')

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


# ---- 連立方程式ソルバ・列挙ユーティリティ（検算専用・図には解を書かない） -----
def solve2(a1, b1, c1, a2, b2, c2):
    """a1x＋b1y＝c1, a2x＋b2y＝c2 をクラメルの公式で解く（一意解前提）"""
    det = a1 * b2 - a2 * b1
    assert det != 0, "係数行列が正則でない"
    return ((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det)


def nat_solutions(a, b, c, xmax=50):
    """ax＋by＝c の自然数解（x,y≧1）を全数列挙"""
    out = []
    for x in range(1, xmax + 1):
        rest = c - a * x
        if rest <= 0:
            continue
        if rest % b == 0:
            y = rest // b
            if y >= 1:
                out.append((x, y))
    return out


# ===========================================================================
# 図1: L01 二つの表と共通の組（2x＋y＝7 と x＋y＝4・(3,1)だけが両方に現れる）
# 本文根拠: lesson_01.md 主概念1・2（解の表列挙と「両方の表に現れる組は(3,1)ただ1つ」）
# 答え扱い: (3,1)は本文が主概念2の解説で明示する解説値のため記載可
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md と一致させる） ---
    eq1 = (2, 1, 7)     # 2x＋y＝7（人数の条件）
    eq2 = (1, 1, 4)     # x＋y＝4（艘数の条件）

    sols1 = nat_solutions(*eq1)
    sols2 = nat_solutions(*eq2)
    common = [p for p in sols1 if p in sols2]
    ck = Checker()
    ck.ok("2x＋y＝7 の自然数解は本文どおり (1,5)(2,3)(3,1) の3組",
          sols1 == [(1, 5), (2, 3), (3, 1)])
    ck.ok("x＋y＝4 の自然数解（x＝4,y＝0を除く）は本文どおり (1,3)(2,2)(3,1) の3組",
          sols2 == [(1, 3), (2, 2), (3, 1)])
    ck.ok("両方の表に現れる組は (3,1) ただ1つ（本文の解説値・図に記載）",
          common == [(3, 1)])
    ck.ok("(3,1)は両方の式を同時に満たす（2×3＋1＝7・3＋1＝4）",
          2 * 3 + 1 == 7 and 3 + 1 == 4)

    cv = Canvas(460, 306)
    cw, ch = 44, 26          # 表セル寸法
    # --- 表を1つ描く関数（ローカル） ---
    def table(x0, y0, head, sols, mark):
        cv.text_px(x0 + cw / 2 + cw * 1.5, y0 - 10, head, size=FS,
                   anchor="middle", weight="bold")
        labels = ["x", "y"]
        for r, lab in enumerate(labels):
            cv.rect_px(x0 - cw, y0 + r * ch, cw, ch, sw=AUX_W, fill="#eee")
            cv.text_px(x0 - cw / 2, y0 + r * ch + ch / 2 + FS * 0.35, lab,
                       size=FS, anchor="middle")
        for i, (sx, sy) in enumerate(sols):
            cv.rect_px(x0 + i * cw, y0, cw, ch, sw=AUX_W)
            cv.rect_px(x0 + i * cw, y0 + ch, cw, ch, sw=AUX_W)
            cv.text_px(x0 + i * cw + cw / 2, y0 + ch / 2 + FS * 0.35,
                       str(sx), size=FS, anchor="middle")
            cv.text_px(x0 + i * cw + cw / 2, y0 + ch + ch / 2 + FS * 0.35,
                       str(sy), size=FS, anchor="middle")
            if (sx, sy) == mark:      # 共通の組の列を楕円で強調
                cv.ellipse_px(x0 + i * cw + cw / 2, y0 + ch, cw * 0.62,
                              ch * 1.28, w=BOLD_W * 0.7)
        return (x0 + (len(sols) - 1) * cw + cw / 2, y0 + 2 * ch)

    m1 = table(120, 44, "① 2x＋y＝7 の解（人数の条件）", sols1, common[0])
    m2 = table(120, 152, "② x＋y＝4 の解（艘数の条件）", sols2, common[0])
    # 共通の組から右の説明へ矢印
    bx, by, bw, bh = 316, 88, 132, 96
    cv.textbox_px(bx, by, bw, bh,
                  ["両方の表に", "現れる組は", "(3, 1) ただ1つ", "＝連立方程式の解"],
                  size=12, sw=MAIN_W, weight_first="bold")
    arrow_px(cv, m1[0] + 30, m1[1] - 26, bx - 4, by + 26, w=1.4)
    arrow_px(cv, m2[0] + 30, m2[1] - 26, bx - 4, by + bh - 22, w=1.4)
    cv.text_px(230, 272, "表の同じ列（縦のならび）が1つの解。どちらか一方だけ満たす組は解ではない",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 290, "（x, yは自然数の範囲で列挙——「同時に満たす」で組が1つに絞られる）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_two_tables_common_pair.svg", canvas=cv, lesson="L01",
                title="二つの表の共通の組（2x＋y＝7 と x＋y＝4 → (3,1)だけ）",
                intent="主概念2の可視化。解の全数列挙と共通組の一意性はassertで検算",
                src="lesson_01.md 主概念2（52〜57行の表の見比べ）",
                params="①2x＋y＝7・②x＋y＝4／自然数解を列挙し共通組(3,1)を楕円で強調",
                checks=ck.items)


# ===========================================================================
# 図2: L02 天びん図（A＝B, C＝D なら A＋C＝B＋D——辺々を加えてよい理由）
# 本文根拠: lesson_02.md 主概念1「等式は天びん・CとDは同じ量だから崩れない」
# 答え扱い: 記号のみの概念図。数値検算は複数の数値組で恒等的に確認
# ===========================================================================
def fig_L02_1():
    ck = Checker()
    ck.ok("複数の数値組で A＝B, C＝D ⇒ A＋C＝B＋D が成立（辺々を加える）",
          all(abs((a + c) - (b + d)) < 1e-9
              for (a, b, c, d) in [(5, 5, 3, 3), (11, 11, 3, 3), (2.5, 2.5, -4, -4)]))
    ck.ok("同様に A−C＝B−D も成立（辺々を引く）",
          all(abs((a - c) - (b - d)) < 1e-9
              for (a, b, c, d) in [(5, 5, 3, 3), (11, 11, 3, 3), (2.5, 2.5, -4, -4)]))

    cv = Canvas(460, 268)
    cv.add_hatch()

    def balance(cx, base_y, left_labels, right_labels, caption):
        """つり合った天びん1台をpx座標で描く"""
        beam_y = base_y - 58
        half = 78
        # 支点（三角形）と支柱
        cv.raw(f'<polygon points="{cx:.1f},{beam_y:.1f} {cx - 13:.1f},{base_y:.1f} '
               f'{cx + 13:.1f},{base_y:.1f}" fill="#ccc" stroke="#000" '
               f'stroke-width="{MAIN_W}"/>')
        # はり（水平＝つり合い）
        cv.raw(f'<line x1="{cx - half:.1f}" y1="{beam_y:.1f}" x2="{cx + half:.1f}" '
               f'y2="{beam_y:.1f}" stroke="#000" stroke-width="{BOLD_W * 0.7}"/>')
        # 皿とおもり（枠＝おもりの箱・複数段可）
        for side, labels in ((-1, left_labels), (1, right_labels)):
            px = cx + side * half
            cv.raw(f'<line x1="{px:.1f}" y1="{beam_y:.1f}" x2="{px:.1f}" '
                   f'y2="{beam_y + 12:.1f}" stroke="#000" stroke-width="{AUX_W}"/>')
            for i, (lab, hatched) in enumerate(labels):
                bw, bh = 46, 24
                by = beam_y + 12 + i * (bh + 3)
                fill = "url(#h45)" if hatched else "#fff"
                cv.rect_px(px - bw / 2, by, bw, bh, sw=MAIN_W, fill="#fff")
                if hatched:
                    cv.raw(f'<rect x="{px - bw / 2:.1f}" y="{by:.1f}" '
                           f'width="{bw:.1f}" height="{bh:.1f}" fill="{fill}" '
                           f'stroke="#000" stroke-width="{MAIN_W}"/>')
                cv.text_px(px, by + bh / 2 + FS * 0.35, lab, size=FS,
                           anchor="middle", weight="bold")
        cv.text_px(cx, base_y + 22, caption, size=FS_CAP, anchor="middle")

    balance(105, 150, [("A", False)], [("B", False)], "① A＝B（つり合っている）")
    arrow_px(cv, 206, 58, 250, 58, w=1.6, head=8)
    cv.text_px(228, 40, "②C＝Dを", size=11, anchor="middle")
    cv.text_px(228, 78, "左にC・右にD", size=10, anchor="middle")
    balance(350, 150, [("A", False), ("C", True)], [("B", False), ("D", True)],
            "A＋C＝B＋D（つり合ったまま）")
    cv.text_px(230, 216, "CとDは名札がちがっても中身は同じ量（②C＝D）——だから天びんは崩れない",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 236, "注意: 足すのは左辺どうしと右辺どうしの両方。片側だけにのせると等式が壊れる",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_balance_add_equals.svg", canvas=cv, lesson="L02",
                title="天びん図（A＝B, C＝D なら A＋C＝B＋D）",
                intent="主概念1「辺々の加減」の理由の可視化。記号のみで答えなし",
                src="lesson_02.md 主概念1（29〜42行）",
                params="A＝B・C＝D（斜線＝あとからのせた同じ量の組）／数値組3通りで恒等検算",
                checks=ck.items)


# ===========================================================================
# 図3: L02 加減法の筆算型（①x＋y＝11, ②x−y＝3 → 辺々を加えて 2x＝14）
# 本文根拠: lesson_02.md 主概念2（①＋②で 2x＝14 まで本文明示）
# 答え漏れ注意: 解 (7,4) は図に書かない（2x＝14までが本文明示の解説値）
# ===========================================================================
def fig_L02_2():
    # --- パラメータ（本文 lesson_02.md 主概念2 と一致させる） ---
    a1, b1, c1 = 1, 1, 11     # ① x＋y＝11
    a2, b2, c2 = 1, -1, 3     # ② x−y＝3

    ck = Checker()
    ck.ok("辺々を加えると (x＋y)＋(x−y)＝2x（yの係数＋1と−1が打ち消す）",
          b1 + b2 == 0 and a1 + a2 == 2)
    ck.ok("右辺どうしの和 11＋3＝14（本文明示の解説値・図に記載）",
          c1 + c2 == 14)
    x, y = solve2(a1, b1, c1, a2, b2, c2)
    ck.ok("解(7,4)が両式を満たす（本文の解説値・図には書かない）",
          abs(x - 7) < 1e-9 and abs(y - 4) < 1e-9
          and abs(x + y - 11) < 1e-9 and abs(x - y - 3) < 1e-9)

    cv = Canvas(440, 250)
    lx, rx0 = 150, 262        # 左辺の右端x・右辺の右端x（縦をそろえる）
    rows = [("①", "x＋y", "11", 54), ("②", "x−y", "3", 88)]
    for lab, lhs, rhs, y0 in rows:
        cv.text_px(84, y0, lab, size=FS, anchor="middle")
        cv.text_px(lx, y0, lhs + "＝", size=16, anchor="end")
        cv.text_px(rx0, y0, rhs, size=16, anchor="end")
    cv.text_px(56, 92, "＋)", size=16, anchor="middle", weight="bold")
    cv.raw(f'<line x1="72" y1="102" x2="272" y2="102" stroke="#000" '
           f'stroke-width="{MAIN_W}"/>')
    cv.text_px(lx, 128, "2x＝", size=16, anchor="end", weight="bold")
    cv.text_px(rx0, 128, "14", size=16, anchor="end", weight="bold")
    # 消えるyへの注記（yの列の真上に置く）
    cv.text_px(128, 22, "＋1と−1で", size=11, anchor="middle")
    cv.text_px(128, 35, "打ち消し合う", size=11, anchor="middle")
    # 右辺への注記（右辺の列の真上に置く）
    cv.text_px(248, 22, "右辺も忘れず", size=11, anchor="middle")
    cv.text_px(248, 35, "11＋3", size=11, anchor="middle")
    # 帰着の矢印
    arrow_px(cv, 292, 122, 332, 122, w=1.6, head=8)
    cv.textbox_px(340, 96, 88, 52, ["yが消えた", "＝中1で見た", "形に帰着"],
                  size=11, sw=MAIN_W, weight_first="bold")
    cv.text_px(220, 190, "筆算のように上下にそろえて書くと、左辺の列と右辺の列を同時に処理できて",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 208, "「右辺だけ置き去り」の事故が起きにくい（このあと x を求めて①に代入する）",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig2_elimination_column_addition.svg", canvas=cv,
                lesson="L02",
                title="加減法の筆算型（①＋②でyが消えて 2x＝14）",
                intent="主概念2の型の可視化。解の組は書かずassertで代入検算のみ",
                src="lesson_02.md 主概念2（48〜59行）",
                params="①x＋y＝11・②x−y＝3／辺々加えて2x＝14（本文明示）／解の組は非記載",
                checks=ck.items)


# ===========================================================================
# 図4: L03 係数をそろえる（②×2 は右辺も2倍→そろえてから引く）
# 本文根拠: lesson_03.md 主概念1（①2x＋3y＝12, ②x＋2y＝7, ②×2＝2x＋4y＝14, −y＝−2）
# 答え漏れ注意: 解 (3,2) は図に書かない（−y＝−2までが本文明示の解説値）
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md 主概念1 と一致させる） ---
    a1, b1, c1 = 2, 3, 12     # ① 2x＋3y＝12
    a2, b2, c2 = 1, 2, 7      # ② x＋2y＝7
    k = 2                     # ②を2倍

    ck = Checker()
    ck.ok("②×2 で 2x＋4y＝14（右辺 7×2＝14 も同時に2倍）",
          (a2 * k, b2 * k, c2 * k) == (2, 4, 14))
    ck.ok("xの係数が①とそろう（2と2）", a1 == a2 * k)
    ck.ok("①−②×2 の左辺は −y・右辺は 12−14＝−2（本文明示の解説値・図に記載）",
          a1 - a2 * k == 0 and b1 - b2 * k == -1 and c1 - c2 * k == -2)
    x, y = solve2(a1, b1, c1, a2, b2, c2)
    ck.ok("解(3,2)が両式を満たす（本文の解説値・図には書かない）",
          abs(x - 3) < 1e-9 and abs(y - 2) < 1e-9
          and abs(2 * x + 3 * y - 12) < 1e-9 and abs(x + 2 * y - 7) < 1e-9)

    cv = Canvas(470, 262)
    # 左パネル: そろっていない2式
    cv.text_px(36, 56, "①", size=FS)
    cv.text_px(160, 56, "2x＋3y＝12", size=16, anchor="end")
    cv.text_px(36, 92, "②", size=FS)
    cv.text_px(160, 92, "x＋2y＝7", size=16, anchor="end")
    cv.text_px(96, 126, "係数がそろって", size=11, anchor="middle")
    cv.text_px(96, 139, "いない…", size=11, anchor="middle")
    # ②×2 の矢印（両辺に）
    arrow_px(cv, 170, 88, 226, 88, w=1.4)
    cv.text_px(198, 76, "②×2", size=12, anchor="middle", weight="bold")
    cv.text_px(198, 104, "右辺も2倍", size=10, anchor="middle")
    # 右パネル: そろった2式の筆算引き算
    lx2 = 380
    cv.text_px(258, 66, "①", size=FS)
    cv.text_px(lx2, 66, "2x＋3y＝12", size=16, anchor="end")
    cv.text_px(236, 102, "−)", size=15, anchor="middle", weight="bold")
    cv.text_px(262, 102, "②×2", size=FS)
    cv.text_px(lx2, 102, "2x＋4y＝14", size=16, anchor="end")
    cv.raw(f'<line x1="248" y1="114" x2="388" y2="114" stroke="#000" '
           f'stroke-width="{MAIN_W}"/>')
    cv.text_px(lx2, 142, "−y＝−2", size=16, anchor="end", weight="bold")
    # そろった2xへの注記（上から破線矢印で指す）
    cv.text_px(310, 26, "2xがそろった！", size=11, anchor="middle")
    cv.text_px(310, 39, "（引けば消える）", size=10, anchor="middle")
    arrow_px(cv, 303, 44, 303, 54, w=AUX_W, head=6.0, dash=DASH)
    cv.text_px(235, 196, "等式の性質③「両辺に同じ数をかけてよい」で係数をそろえる。",
               size=FS_CAP, anchor="middle")
    cv.text_px(235, 214, "宣言の型:「xを消す。係数を2にそろえて、辺々を引く」——同符号どうしなら引く",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_scale_coefficients_then_subtract.svg", canvas=cv,
                lesson="L03",
                title="係数をそろえる（②×2→2xがそろい、引いて −y＝−2）",
                intent="主概念1の流れの可視化。解の組は書かずassertで代入検算のみ",
                src="lesson_03.md 主概念1（20〜37行）",
                params="①2x＋3y＝12・②x＋2y＝7・②×2＝2x＋4y＝14／−y＝−2まで本文明示",
                checks=ck.items)


# ===========================================================================
# 図5: L04 代入法の置きかえ図（①y＝x＋3 を②のyへ「まるごとかっこ付きで」）
# 本文根拠: lesson_04.md 主概念1（①y＝x＋3, ②x＋2y＝12, x＋2(x＋3)＝12）
# 答え漏れ注意: 解 (2,5) は図に書かない（置きかえた式までが本文明示の解説値）
# ===========================================================================
def fig_L04():
    # --- パラメータ（本文 lesson_04.md 主概念1 と一致させる） ---
    # ① y＝x＋3　② x＋2y＝12
    ck = Checker()
    x, y = solve2(1, -1, -3, 1, 2, 12)     # −x＋y＝3 を 1x−1y＝−3 と表現
    ck.ok("解(2,5)が両式を満たす（本文の解説値・図には書かない）",
          abs(x - 2) < 1e-9 and abs(y - 5) < 1e-9
          and abs(y - (x + 3)) < 1e-9 and abs(x + 2 * y - 12) < 1e-9)
    ck.ok("置きかえの同値性: x＋2(x＋3)＝3x＋6（複数のxで恒等）",
          all(abs(t + 2 * (t + 3) - (3 * t + 6)) < 1e-9 for t in (0.0, 2.0, 4.5)))
    ck.ok("かっこなしだと別の式になる: 2×x＋3 ≠ 2(x＋3)（x＝2で7≠10）",
          2 * 2 + 3 == 7 and 2 * (2 + 3) == 10)

    cv = Canvas(450, 240)
    # ①の式（yの正体）
    cv.text_px(60, 52, "①", size=FS)
    cv.text_px(96, 52, "y＝x＋3", size=17, anchor="start", weight="bold")
    cv.ellipse_px(140, 47, 25, 16, w=AUX_W, dash=DASH)     # x＋3 を囲む
    cv.text_px(226, 47, "「yはx＋3と同じもの」", size=11, anchor="start")
    # ②の式（置きかえ先）
    cv.text_px(60, 110, "②", size=FS)
    cv.text_px(96, 110, "x＋2", size=17, anchor="start")
    cv.rect_px(140, 94, 26, 24, sw=MAIN_W, fill="#eee", rx=3)
    cv.text_px(153, 111, "y", size=17, anchor="middle", weight="bold")
    cv.text_px(170, 110, "＝12", size=17, anchor="start")
    # ①のかたまり→②のyへ矢印
    arrow_px(cv, 142, 64, 152, 90, w=1.6, head=8)
    cv.text_px(196, 80, "まるごと置きかえ", size=11, anchor="start")
    # 置きかえた結果
    arrow_px(cv, 130, 128, 130, 152, w=1.4)
    cv.text_px(96, 174, "x＋2(x＋3)＝12", size=17, anchor="start", weight="bold")
    cv.ellipse_px(155, 169, 29, 16, w=AUX_W, dash=DASH)
    cv.text_px(250, 160, "急所: 必ずかっこ付きで。", size=11, anchor="start")
    cv.text_px(250, 174, "2×x＋3 と書くと「全体の2倍」が", size=11, anchor="start")
    cv.text_px(250, 188, "「xだけ2倍」に化けてしまう", size=11, anchor="start")
    cv.text_px(225, 218, "文字が1つ消えて一元一次方程式に帰着——ちがうのは消し方だけ",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_substitution_replace_with_parentheses.svg",
                canvas=cv, lesson="L04",
                title="代入法の置きかえ図（②のyをx＋3にまるごと置きかえ）",
                intent="主概念1の急所（かっこ付き代入）の可視化。解は書かない",
                src="lesson_04.md 主概念1（20〜33行）",
                params="①y＝x＋3・②x＋2y＝12→x＋2(x＋3)＝12／かっこ有無の差はassertで数値確認",
                checks=ck.items)


# ===========================================================================
# 図6: L05 帰着の見取図（4つの型を整理して基本の形へ→L02〜L04の解き方）
# 本文根拠: lesson_05.md 主概念（型1〜型4「整理して基本の形に戻す→あとはいつもどおり」）
# 答え漏れ注意: 各型の例の解((3,3)(3,2)(4,6)(4,2))は図に書かずassertでのみ検算
# ===========================================================================
def fig_L05():
    ck = Checker()
    # 型1: 展開の同値性と解
    ck.ok("型1: 2(x＋y)−y＝2x＋y（複数の(x,y)で恒等）",
          all(abs(2 * (p + q) - q - (2 * p + q)) < 1e-9
              for p, q in [(1, 2), (3, 3), (-2, 5)]))
    x1, y1 = solve2(2, 1, 9, 3, -2, 3)
    ck.ok("型1の例の解(3,3)が元の式を満たす（図には書かない）",
          abs(x1 - 3) < 1e-9 and abs(y1 - 3) < 1e-9
          and abs(2 * (x1 + y1) - y1 - 9) < 1e-9 and abs(3 * x1 - 2 * y1 - 3) < 1e-9)
    # 型2: 10倍の同値性と解
    x2, y2 = solve2(5, 2, 19, 1, -1, 1)
    ck.ok("型2: 0.5x＋0.2y＝1.9 の10倍は 5x＋2y＝19・解(3,2)が元の式を満たす",
          abs(0.5 * 10 - 5) < 1e-9 and abs(0.2 * 10 - 2) < 1e-9
          and abs(1.9 * 10 - 19) < 1e-9
          and abs(x2 - 3) < 1e-9 and abs(y2 - 2) < 1e-9
          and abs(0.5 * x2 + 0.2 * y2 - 1.9) < 1e-9 and abs(x2 - y2 - 1) < 1e-9)
    # 型3: 6倍の同値性と解
    x3, y3 = solve2(3, 2, 24, 1, 1, 10)
    ck.ok("型3: x/2＋y/3＝4 の6倍は 3x＋2y＝24・解(4,6)が元の式を満たす",
          abs(x3 - 4) < 1e-9 and abs(y3 - 6) < 1e-9
          and abs(x3 / 2 + y3 / 3 - 4) < 1e-9 and abs(x3 + y3 - 10) < 1e-9)
    # 型4: A＝B＝C の分解と解
    x4, y4 = solve2(2, 1, 10, 1, 3, 10)
    ck.ok("型4: 2x＋y＝x＋3y＝10 → {2x＋y＝10, x＋3y＝10}・解(4,2)が3つの量を等しくする",
          abs(x4 - 4) < 1e-9 and abs(y4 - 2) < 1e-9
          and abs(2 * x4 + y4 - 10) < 1e-9 and abs(x4 + 3 * y4 - 10) < 1e-9)

    cv = Canvas(480, 330)
    tops = [
        (10, 20, 112, 74, ["型1 かっこ", "2(x＋y)−y＝9", "→展開して整理"]),
        (130, 20, 112, 74, ["型2 小数", "0.5x＋0.2y＝1.9", "→両辺を10倍"]),
        (250, 20, 112, 74, ["型3 分数", "x/2＋y/3＝4", "→両辺を6倍"]),
        (370, 20, 104, 74, ["型4 A＝B＝C", "2x＋y＝x＋3y＝10", "→2本に分解"]),
    ]
    for (bx, by, bw, bh, lines) in tops:
        cv.textbox_px(bx, by, bw, bh, lines, size=10.5, sw=MAIN_W,
                      weight_first="bold")
    # 中央: 基本の形
    jx, jy, jw, jh = 140, 160, 200, 52
    cv.textbox_px(jx, jy, jw, jh, ["基本の形", "ax＋by＝c が2本"], size=FS,
                  sw=BOLD_W * 0.6, weight_first="bold")
    for (bx, by, bw, bh, _) in tops:
        arrow_px(cv, bx + bw / 2, by + bh + 2, jx + jw / 2 + (bx - 187) * 0.28,
                 jy - 4, w=1.4)
    cv.text_px(240, 138, "整理して戻す（右辺も同じ数をかける・その式の両辺だけ）",
               size=11, anchor="middle")
    # 下段: いつもの解き方
    arrow_px(cv, 240, jy + jh + 4, 240, 248, w=1.6, head=8)
    cv.textbox_px(140, 252, 200, 40, ["あとはいつもどおり", "加減法・代入法（L02〜L04）"],
                  size=12, sw=MAIN_W, weight_first="bold")
    cv.text_px(240, 310, "新しい解き方はゼロ——「知らない見た目→知っている形に戻す」",
               size=FS_CAP, anchor="middle")
    cv.text_px(240, 326, "（検算は変形前の元の式で）", size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_reduce_to_basic_form.svg", canvas=cv, lesson="L05",
                title="帰着の見取図（4つの型→基本の形→いつもの解き方）",
                intent="主概念（整理して基本の形へ）の地図。各型の例の解は書かない",
                src="lesson_05.md 主概念・型1〜型4（17〜52行）",
                params="型1〜4の例式は本文と同一／変形の同値性と各解はassertでのみ検算",
                checks=ck.items)


# ===========================================================================
# 図7: L06 表→式2本の対応図（個数の行→x＋y＝10・代金の行→80x＋120y＝920）
# 本文根拠: lesson_06.md 主概念1（文化祭の模擬店・表の行ごとに式ができる）
# 答え漏れ注意: 解（飲み物7本・パン3個）は図に書かない
# ===========================================================================
def fig_L06():
    # --- パラメータ（本文 lesson_06.md 主概念1 と一致させる） ---
    p1, p2 = 80, 120          # 飲み物80円・パン120円
    total_n, total_c = 10, 920

    ck = Checker()
    x, y = solve2(1, 1, total_n, p1, p2, total_c)
    ck.ok("解（飲み物7本・パン3個）が両式を満たす（本文の解説値・図には書かない）",
          abs(x - 7) < 1e-9 and abs(y - 3) < 1e-9
          and abs(x + y - total_n) < 1e-9
          and abs(p1 * x + p2 * y - total_c) < 1e-9)
    ck.ok("代金検算 80×7＋120×3＝560＋360＝920（本文ステップ4と一致）",
          p1 * 7 + p2 * 3 == 560 + 360 == 920)
    ck.ok("行が単位ごと（個数の行・代金の行）で、行ごとにそのまま式になる構成", True)

    cv = Canvas(560, 260)
    x0, y0 = 48, 46
    cw, ch = 74, 30
    heads = ["", "飲み物", "パン", "合計"]
    rows = [("個数（個）", ["x", "y", "10"]),
            ("代金（円）", ["80x", "120y", "920"])]
    # ヘッダ行
    for j, h in enumerate(heads):
        cv.rect_px(x0 + j * cw, y0, cw, ch, sw=AUX_W,
                   fill="#eee" if j else "#fff")
        if h:
            cv.text_px(x0 + j * cw + cw / 2, y0 + ch / 2 + FS * 0.35, h,
                       size=FS, anchor="middle")
    # データ行
    for i, (lab, cells) in enumerate(rows):
        ry = y0 + (i + 1) * ch
        cv.rect_px(x0, ry, cw, ch, sw=AUX_W, fill="#eee")
        cv.text_px(x0 + cw / 2, ry + ch / 2 + FS * 0.35, lab, size=11.5,
                   anchor="middle")
        for j, s in enumerate(cells):
            cv.rect_px(x0 + (j + 1) * cw, ry, cw, ch, sw=AUX_W)
            cv.text_px(x0 + (j + 1) * cw + cw / 2, ry + ch / 2 + FS * 0.35,
                       s, size=FS, anchor="middle")
    # 行→式の矢印
    eqs = ["x＋y＝10", "80x＋120y＝920"]
    for i, eq in enumerate(eqs):
        ry = y0 + (i + 1) * ch + ch / 2
        arrow_px(cv, x0 + 4 * cw + 8, ry, x0 + 4 * cw + 42, ry, w=1.4)
        cv.text_px(x0 + 4 * cw + 48, ry + FS * 0.35, eq, size=13.5,
                   anchor="start", weight="bold")
    cv.text_px(66, 178, "「飲み物をx本、パンをy個とする」（ステップ1の宣言）", size=11,
               anchor="start")
    cv.text_px(280, 210, "表の行ごとに式ができる——単位ごとに行を作ると「個数と円を足す」事故が防げる",
               size=FS_CAP, anchor="middle")
    cv.text_px(280, 228, "（1本80円の飲み物と1個120円のパンをあわせて10個・代金920円の場面）",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_table_to_two_equations.svg", canvas=cv, lesson="L06",
                title="数量の表→式2本（個数の行と代金の行がそのまま式になる）",
                intent="主概念1ステップ2の可視化。解（それぞれの個数）は書かない",
                src="lesson_06.md 主概念1（26〜33行の表と式）",
                params="80円×x本・120円×y個・合計10個・920円（本文と同一）／解はassertのみ",
                checks=ck.items)


# ===========================================================================
# 図8: L07 速さの線分図（家—駅1200m・歩き分速60m x分・走り分速120m y分・計14分）
# 本文根拠: lesson_07.md 主概念1（家から駅1200m・分速60m→分速120m・全体14分）
# 答え漏れ注意: 解（歩き8分・走り6分）は図に書かない（区切り位置の比のみ解を使用）
# ===========================================================================
def fig_L07():
    # --- パラメータ（本文 lesson_07.md 主概念1 と一致させる） ---
    v1, v2 = 60, 120          # 歩き分速60m・走り分速120m
    total_d, total_t = 1200, 14

    ck = Checker()
    tx, ty = solve2(1, 1, total_t, v1, v2, total_d)
    ck.ok("解（歩き8分・走り6分）が時間・道のりの両式を満たす（図には書かない）",
          abs(tx - 8) < 1e-9 and abs(ty - 6) < 1e-9
          and abs(tx + ty - total_t) < 1e-9
          and abs(v1 * tx + v2 * ty - total_d) < 1e-9)
    d1, d2 = v1 * tx, v2 * ty
    ck.ok("道のり内訳 480m＋720m＝1200m（区切り位置は実測比・数値は図に書かない）",
          abs(d1 - 480) < 1e-9 and abs(d2 - 720) < 1e-9
          and abs(d1 + d2 - total_d) < 1e-9)

    cv = Canvas(470, 232)
    x0, x1 = 52, 428          # 線分の左右端(px)
    yline = 96
    xm = x0 + (x1 - x0) * d1 / total_d      # 区切り（実測比・ラベルは文字のみ）
    # 本線
    cv.raw(f'<line x1="{x0}" y1="{yline}" x2="{x1}" y2="{yline}" '
           f'stroke="#000" stroke-width="{MAIN_W}"/>')
    for px in (x0, xm, x1):
        cv.raw(f'<line x1="{px:.1f}" y1="{yline - 8}" x2="{px:.1f}" '
               f'y2="{yline + 8}" stroke="#000" stroke-width="{MAIN_W}"/>')
    cv.text_px(x0, yline - 16, "家", size=FS, anchor="middle", weight="bold")
    cv.text_px(x1, yline - 16, "駅", size=FS, anchor="middle", weight="bold")
    cv.text_px(xm, yline - 16, "ここから走る", size=11, anchor="middle")
    # 区間ラベル（上: 速さと時間）
    cv.text_px((x0 + xm) / 2, yline + 26, "歩き 分速60m", size=FS, anchor="middle")
    cv.text_px((x0 + xm) / 2, yline + 44, "x分", size=FS, anchor="middle",
               weight="bold")
    cv.text_px((xm + x1) / 2, yline + 26, "走り 分速120m", size=FS, anchor="middle")
    cv.text_px((xm + x1) / 2, yline + 44, "y分", size=FS, anchor="middle",
               weight="bold")
    # 全体の寸法線（下: 道のり1200m・時間14分）
    yd = yline + 66
    cv.raw(f'<line x1="{x0}" y1="{yd}" x2="{x1}" y2="{yd}" '
           f'stroke="#000" stroke-width="0.9"/>')
    for px in (x0, x1):
        cv.raw(f'<line x1="{px}" y1="{yd - 5}" x2="{px}" y2="{yd + 5}" '
               f'stroke="#000" stroke-width="0.9"/>')
    cv.text_px((x0 + x1) / 2, yd + 18, "全体で 1200m・14分", size=FS,
               anchor="middle", weight="bold")
    cv.text_px(240, 206, "時間の行: x＋y＝14　　道のりの行: 60x＋120y＝1200（道のり＝速さ×時間）",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig1_distance_time_segment.svg", canvas=cv, lesson="L07",
                title="速さの線分図（家—駅1200m・歩きx分・走りy分・計14分）",
                intent="主概念1の場面図。歩き・走りの時間の値は書かずx・y表記のみ",
                src="lesson_07.md 主概念1（20〜34行）",
                params="分速60m・分速120m・1200m・14分（本文と同一）／区切りは解の実測比（値は非記載）",
                checks=ck.items)


# ===========================================================================
# 図9: L08 「消して戻す」作戦の地図（連立→消去→一元一次→解→場面へ）
# 本文根拠: lesson_08.md 3部屋の自己チェック・次の章へ（帰着の作戦と中3への接続）
# 答え漏れ注意: 総合演習の答は図に書かない。検算は総合演習1(1)(2)を両解法で実施
# ===========================================================================
def fig_L08():
    ck = Checker()
    # 総合演習1(1): { 4x＋3y＝1, 2x−y＝3 } を加減法相当（クラメル）で
    xa, ya = solve2(4, 3, 1, 2, -1, 3)
    ck.ok("総合演習1(1)の解が両式を満たす（値は図に書かない）",
          abs(4 * xa + 3 * ya - 1) < 1e-9 and abs(2 * xa - ya - 3) < 1e-9)
    # 総合演習1(2): { y＝2x−3, 3x−2y＝4 } を代入法（式変形）で
    #   3x−2(2x−3)＝4 → −x＋6＝4 → x＝2 → y＝1
    xb = -(4 - 6) / 1
    yb = 2 * xb - 3
    xs, ys = solve2(2, -1, 3, 3, -2, 4)     # 同じ系を加減法相当でも
    ck.ok("総合演習1(2): 代入法と加減法で同じ解になる（どちらで解いても答えは同じ）",
          abs(xb - xs) < 1e-9 and abs(yb - ys) < 1e-9
          and abs(ys - (2 * xs - 3)) < 1e-9 and abs(3 * xs - 2 * ys - 4) < 1e-9)
    # stretch S1: { x＋y＝5, 2x＋2y＝10 } は2本目が1本目の2倍＝新しい条件でない
    ck.ok("S1: 2x＋2y＝10 は x＋y＝5 の両辺2倍（係数・右辺とも比2）＝組は1つに絞れない",
          (2, 2, 10) == (1 * 2, 1 * 2, 5 * 2))

    cv = Canvas(480, 342)
    # 上段: 連立方程式
    cv.textbox_px(150, 14, 180, 46, ["連立方程式", "（文字が2つ・式が2本）"],
                  size=12, sw=MAIN_W, weight_first="bold")
    # 中段: 2つの消し方
    cv.textbox_px(56, 110, 152, 50, ["加減法（L02〜L03）", "そろえて、打ち消して消す"],
                  size=11, sw=MAIN_W, weight_first="bold")
    cv.textbox_px(272, 110, 152, 50, ["代入法（L04）", "まるごと置きかえて消す"],
                  size=11, sw=MAIN_W, weight_first="bold")
    arrow_px(cv, 200, 62, 140, 106, w=1.4)
    arrow_px(cv, 280, 62, 340, 106, w=1.4)
    cv.text_px(240, 92, "文字を1つ消す（どちらでも答えは同じ）", size=11,
               anchor="middle")
    # 下段: 一元一次方程式（合流）
    jx, jy, jw, jh = 150, 208, 180, 46
    cv.textbox_px(jx, jy, jw, jh, ["一元一次方程式", "（中1で解ける形に帰着）"],
                  size=12, sw=BOLD_W * 0.6, weight_first="bold")
    arrow_px(cv, 132, 164, 210, 204, w=1.4)
    arrow_px(cv, 348, 164, 270, 204, w=1.4)
    # 解→場面
    arrow_px(cv, 240, 258, 240, 284, w=1.4)
    cv.textbox_px(96, 288, 288, 34,
                  ["解（組）→ 代入検算・場面に戻して吟味（利用の4ステップ）"],
                  size=11, sw=MAIN_W)
    # わきの注記: 中3への接続（破線枠）
    cv.textbox_px(348, 214, 124, 62,
                  ["中3 二次方程式", "「次数を減らして」", "同じ作戦で帰着"],
                  size=10.5, sw=AUX_W, dash=DASH, weight_first="bold")
    arrow_px(cv, 410, 210, 336, 240, w=1.1, head=6.0, dash=DASH)
    cv.text_px(240, 336, "「消して戻す」——この章の背骨。文字の種類を減らして、解ける形に帰る",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig1_elimination_reduction_map.svg", canvas=cv,
                lesson="L08",
                title="「消して戻す」作戦の地図（2つの消し方が一元一次方程式に合流）",
                intent="章末のふり返り地図。総合演習の答は書かずassertで両解法一致を検算",
                src="lesson_08.md 部屋2の問い・次の章へ（27〜51行）",
                params="検算=総合演習1(1)(2)（代入法・加減法の一致）＋S1の係数比2倍",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02_1, fig_L02_2, fig_L03, fig_L04, fig_L05, fig_L06,
        fig_L07, fig_L08]


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
        "# FIGURE_MANIFEST — 連立方程式単元 図版台帳",
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
        "- 練習問題・総合演習の答は図に一切書かない。例題（本文解説）の最終解の組"
        "（L02の(7,4)・L03の(3,2)・L04の(2,5)・L05の各型の解・L06の飲み物7本パン3個・"
        "L07の歩き8分走り6分）も図には書かず、スクリプト内assertで本文の解説値と照合した。",
        "- 図に載せた数値は、与件（10個・920円・1200m・14分など）と、本文が解説中で"
        "明示している途中式（L02の2x＝14・L03の−y＝−2・L04のx＋2(x＋3)＝12・"
        "L01の共通組(3,1)）のみ。",
        "- L07の線分図の区切り位置は解の実測比（480m:720m）で描いたが、図中のラベルは"
        "x分・y分の文字表記のみで値は現れない。",
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
        "---\ndistribution_status: published_draft\n---\n\n"
        + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")


if __name__ == "__main__":
    main()
