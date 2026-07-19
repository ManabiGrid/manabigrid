#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1数学「文字と式」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: 先行単元 materials/jhs-math-2/jhs-math-2-expression-calculation/assets_provenance/
generate_figures.py（docs/SPEC_figures.md 準拠）と同一のコード来歴方式。
ヘルパー群（Canvas/寸法線/ハッチ/矢印ほか）は同スクリプトからコピー再利用（元は無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（15枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない（周長・分配・代入検算・
  碁石の数え方3通りの一致など、本文の数値との一致を検算）。
- 答えの分離方針: 近隣の練習・stretchの答（L02練習の7x/3ab・L05練習の0.6a/0.7y・
  L09練習のx≧40・L11練習の5x＋4・L12練習の6x＋3など）は図に書かない。
  禁止文字列は main() で機械検査する。図に載る式・数値は該当レッスン本文が
  地の文で明示する解説値に限る。
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
        """白抜き丸（含まない・種類の区別用マーカー）"""
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
# 図1: L01 正方形のまわりの長さ——変わる数の席に文字aを置く
# 本文根拠: lesson_01.md 主概念1（1×4＝4・2×4＝8・3×4＝12 → a×4）
# 答え漏れ注意: 練習の答（x×6・a×3など）は図に書かない
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md 主概念1 と一致させる） ---
    sides = (1, 2, 3)              # 1辺 1cm・2cm・3cm

    ck = Checker()
    ck.ok("まわりの長さ: 1×4＝4・2×4＝8・3×4＝12（本文の値と一致）",
          [s * 4 for s in sides] == [4, 8, 12])
    ck.ok("どの1辺でも×4は共通（a×4がすべての場合を引き受ける根拠）",
          all(4 * s == s + s + s + s for s in (1, 2, 3, 10, 1.5, 100)))

    cv = Canvas(440, 252)
    cv.text_px(220, 32, "1辺の長さが変わっても、「×4」の部分はいつも同じ",
               size=FS, anchor="middle", weight="bold")
    u = 20.0                       # 1cm → 20px
    y_base = 140.0
    xs = (44, 100, 176)
    for s, x0 in zip(sides, xs):
        w = s * u
        cv.rect_px(x0, y_base - w, w, w, sw=MAIN_W)
        cv.text_px(x0 + w / 2, y_base + 18, f"{s}cm", size=FS_CAP,
                   anchor="middle")
        cv.text_px(x0 + w / 2, y_base + 40, f"{s}×4＝{s * 4}", size=FS,
                   anchor="middle")
    cv.text_px(270, 108, "…", size=18, anchor="middle")
    wa = 58.0
    cv.rect_px(300, y_base - wa, wa, wa, sw=MAIN_W, dash=DASH)
    cv.text_px(300 + wa / 2, y_base + 18, "a cm", size=FS_CAP,
               anchor="middle", weight="bold")
    cv.text_px(300 + wa / 2, y_base + 40, "a×4", size=15, anchor="middle",
               weight="bold")
    cv.text_px(220, 216, "変わる数の席に文字 a を置く——1本の式が、すべての場合を引き受ける",
               size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(220, 238, "（a は正方形の1辺の長さ。0 より大きい数が入る）",
               size=11, anchor="middle")

    return dict(file="L01_fig1_square_perimeter_letter.svg", canvas=cv,
                lesson="L01",
                title="正方形のまわりの長さ——変わる数の席に文字aを置く（1×4・2×4・3×4→a×4）",
                intent="主概念1の可視化。1辺1・2・3cmの正方形と式を並べ、変わる数の席に"
                       "aを置くとa×4になることを図解。近隣の練習の答は書かない",
                src="lesson_01.md 主概念1",
                params="1辺1・2・3cm／まわりの長さ4・8・12／一般形a×4",
                checks=ck.items)


# ===========================================================================
# 図2: L02 積の表し方——×を省く約束の一覧（a×4→4a・b×a→ab・1×a→a・(−1)×a→−a）
# 本文根拠: lesson_02.md 主概念1（積の表し方の約束1〜3）
# 答え漏れ注意: 練習1の答（7x・3ab・−y・0.1x・5(a＋b)）は図に書かない
# ===========================================================================
def fig_L02_1():
    ck = Checker()
    ck.ok("4a＝a×4（複数のaで一致）",
          all(4 * a == a * 4 for a in (2, 3, -1, 0.5)))
    ck.ok("ab＝b×a（積の交換・複数の値で一致）",
          all(a * b == b * a for a in (2, 3) for b in (5, -1)))
    ck.ok("1×a＝a・(−1)×a＝−a（1は書かない・複数のaで一致）",
          all(1 * a == a and (-1) * a == -a for a in (2, 7, -3)))

    cv = Canvas(440, 262)
    cv.text_px(220, 32, "積の表し方——×を省く約束", size=FS, anchor="middle",
               weight="bold")
    rows = [
        ("a×4", "4a", "×をはぶき、数を文字の前に"),
        ("b×a", "ab", "ふつうアルファベット順に"),
        ("1×a", "a", "1は書かない"),
        ("(−1)×a", "−a", "−1の1も書かない（−は残る）"),
    ]
    for i, (left, right, note) in enumerate(rows):
        y = 72 + i * 45
        cv.text_px(96, y, left, size=17, anchor="middle")
        arrow_px(cv, 148, y - 5, 196, y - 5, w=1.4)
        cv.text_px(232, y, right, size=17, anchor="middle", weight="bold")
        cv.text_px(272, y, note, size=11, anchor="start")
    cv.text_px(220, 248, "省けるのはかけ算の×だけ。a＋4 の＋は省けない",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_product_notation_rules.svg", canvas=cv,
                lesson="L02",
                title="積の表し方の約束（a×4→4a・b×a→ab・1×a→a・(−1)×a→−a）",
                intent="主概念1の可視化。4つの書き替えを対応矢印で並べ、「省く×・前に出る数・"
                       "消える1」の3点を図解。練習1の答は書かない",
                src="lesson_02.md 主概念1",
                params="a×4→4a／b×a→ab／1×a→a／(−1)×a→−a（係数4・1・−1）",
                checks=ck.items)


# ===========================================================================
# 図3: L02 商の表し方——a÷5はa/5（誤り例5/aとの代入対比）
# 本文根拠: lesson_02.md 主概念2（a÷5→a/5・a＝10で2と0.5に分かれる）
# 答え漏れ注意: 練習2・4の答（x/9・7/a・(x−2)/3・m/6）は図に書かない
# ===========================================================================
def fig_L02_2():
    # --- パラメータ（本文 lesson_02.md 主概念2 と一致させる） ---
    a_test = 10                    # 検算に使う値

    ck = Checker()
    ck.ok("a÷5＝a/5: a＝10で10÷5＝2（本文の検算と一致）",
          a_test / 5 == 2)
    ck.ok("誤り例5/a: a＝10で5/10＝0.5（本文の値と一致・2と不一致）",
          5 / a_test == 0.5 and 5 / a_test != a_test / 5)
    ck.ok("上下の並びで値が変わる（複数のaで a/5≠5/a）",
          all(a / 5 != 5 / a for a in (10, 2, 50)))

    def fraction(cv, x, y, top, bottom, bold=False):
        w = "bold" if bold else None
        cv.text_px(x, y - 10, top, size=17, anchor="middle", weight=w)
        cv.raw(f'<line x1="{x - 16}" y1="{y}" x2="{x + 16}" y2="{y}" '
               f'stroke="#000" stroke-width="1.6"/>')
        cv.text_px(x, y + 22, bottom, size=17, anchor="middle", weight=w)

    cv = Canvas(440, 272)
    # 左: 正しい変換
    cv.text_px(110, 50, "a÷5", size=18, anchor="middle", weight="bold")
    arrow_px(cv, 110, 62, 110, 92, w=1.4)
    fraction(cv, 110, 122, "a", "5", bold=True)
    cv.text_px(140, 116, "分子＝わられる数", size=11, anchor="start")
    cv.text_px(140, 142, "分母＝わる数", size=11, anchor="start")
    # 右: 誤り例
    cv.text_px(330, 50, "誤り例（上下があべこべ）", size=11, anchor="middle")
    fraction(cv, 330, 122, "5", "a")
    cv.raw('<line x1="306" y1="146" x2="354" y2="98" stroke="#000" '
           'stroke-width="2.2"/>')
    # 下: 代入による点検
    cv.text_px(220, 196, "検算: a＝10 のとき　a÷5＝10÷5＝2", size=FS,
               anchor="middle")
    cv.text_px(220, 220, "a/5＝10/5＝2 で一致 ✓　　5/a＝5/10＝0.5 で不一致 ✗",
               size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 250, "上下の並びは、具体的な数を入れれば自分で点検できる",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig2_quotient_fraction_check.svg", canvas=cv,
                lesson="L02",
                title="商の表し方（a÷5→a/5・誤り例5/aは代入で見分ける）",
                intent="主概念2の可視化。分数の上下の並びと、a＝10の代入で2と0.5に"
                       "分かれる対比を図解。練習2・4の答は書かない",
                src="lesson_02.md 主概念2",
                params="a÷5→a/5／誤り例5/a／検算a＝10で商2・誤0.5",
                checks=ck.items)


# ===========================================================================
# 図4: L03 指数＝同じ文字の個数（a×a×a×b×b→a³b²）
# 本文根拠: lesson_03.md 主概念（a×a→a²・a×a×b→a²b の延長）
# 答え漏れ注意: 練習の答（5a³・ab²・x²−7yなど）は図に書かない
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md と一致させる） ---
    na, nb = 3, 2                  # aの個数・bの個数

    ck = Checker()
    ck.ok("代入検算: a＝2、b＝3で a×a×a×b×b＝72＝a³b²（複数の組で一致）",
          all(a * a * a * b * b == (a ** na) * (b ** nb)
              for a, b in ((2, 3), (3, 2), (-1, 5))) and 2 * 2 * 2 * 3 * 3 == 72)
    ck.ok("指数はaが3個・bが2個の個数（パラメータと一致）",
          na == 3 and nb == 2)

    cv = Canvas(440, 240)
    cv.text_px(220, 32, "指数は「同じ文字を何個かけたか」の個数", size=FS,
               anchor="middle", weight="bold")
    cv.text_px(148, 76, "a×a×a", size=19, anchor="middle", weight="bold")
    cv.text_px(206, 76, "×", size=15, anchor="middle")
    cv.text_px(258, 76, "b×b", size=19, anchor="middle", weight="bold")
    cv.rect_px(102, 56, 92, 30, sw=AUX_W, dash=DASH, rx=8, fill="none")
    cv.rect_px(222, 56, 72, 30, sw=AUX_W, dash=DASH, rx=8, fill="none")
    arrow_px(cv, 148, 92, 148, 116, w=1.2)
    arrow_px(cv, 258, 92, 258, 116, w=1.2)
    cv.text_px(148, 134, "a が3個", size=FS_CAP, anchor="middle")
    cv.text_px(258, 134, "b が2個", size=FS_CAP, anchor="middle")
    cv.text_px(148, 158, "→ a³", size=16, anchor="middle", weight="bold")
    cv.text_px(258, 158, "→ b²", size=16, anchor="middle", weight="bold")
    cv.text_px(220, 196, "a×a×a×b×b ＝ a³b²", size=17, anchor="middle",
               weight="bold")
    cv.text_px(220, 222, "同じ文字のグループごとに個数を数えて、指数に記録する",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_exponent_grouping.svg", canvas=cv, lesson="L03",
                title="指数＝同じ文字の個数（a×a×a×b×b→a³b²）",
                intent="主概念の可視化。同じ文字のグループに丸で仕分けし、個数を指数へ"
                       "記録する流れを図解。練習の答は書かない",
                src="lesson_03.md 主概念",
                params="a×a×a×b×b／aが3個→a³・bが2個→b²／結果a³b²",
                checks=ck.items)


# ===========================================================================
# 図5: L04 言葉の式を橋にする三段変換（代金＝1個の値段×個数→a×5→5a円）
# 本文根拠: lesson_04.md 主概念1（1個a円のパン5個・a＝100で500円の検算）
# 答え漏れ注意: 練習の答（4x円・3t・(3a＋2b)円・(500−2y)円・x/7）は図に書かない
# ===========================================================================
def fig_L04():
    # --- パラメータ（本文 lesson_04.md 主概念1 と一致させる） ---
    n_pan = 5                      # パンの個数
    a_test = 100                   # 検算に使う1個の値段

    ck = Checker()
    ck.ok("検算: a＝100で5×100＝500円（本文の検算と一致）",
          n_pan * a_test == 500)
    ck.ok("a×5＝5a（書き順の約束・複数のaで一致）",
          all(a * n_pan == n_pan * a for a in (100, 80, 120)))

    cv = Canvas(440, 268)
    cv.text_px(220, 26, "言葉の式を橋にする", size=FS, anchor="middle",
               weight="bold")
    # 段1: 言葉の式
    cv.textbox_px(36, 40, 78, 32, ["代金"], size=FS)
    cv.text_px(128, 61, "＝", size=15, anchor="middle")
    cv.textbox_px(146, 40, 110, 32, ["1個の値段"], size=FS)
    cv.text_px(272, 61, "×", size=15, anchor="middle")
    cv.textbox_px(290, 40, 78, 32, ["個数"], size=FS)
    # 段2: 席に入れる
    arrow_px(cv, 201, 78, 201, 102, w=1.2)
    arrow_px(cv, 329, 78, 329, 102, w=1.2)
    cv.text_px(120, 126, "席に入れる →", size=11, anchor="middle")
    cv.textbox_px(146, 106, 110, 32, ["a"], size=16, dash=DASH,
                  weight_first="bold")
    cv.text_px(272, 127, "×", size=15, anchor="middle")
    cv.textbox_px(290, 106, 78, 32, ["5"], size=16, dash=DASH,
                  weight_first="bold")
    # 段3: 約束どおりに書く
    arrow_px(cv, 240, 144, 240, 168, w=1.4)
    cv.text_px(220, 192, "a×5　→（約束どおりに書く）→　5a（円）", size=16,
               anchor="middle", weight="bold")
    cv.text_px(220, 226, "①言葉の式 ②席に文字と数を入れる ③約束どおりに書く",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 248, "検算: a＝100 なら 5×100＝500円——場面の常識と一致 ✓",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_word_formula_bridge.svg", canvas=cv,
                lesson="L04",
                title="言葉の式を橋にする三段変換（代金＝1個の値段×個数→a×5→5a円）",
                intent="主概念1の可視化。言葉の式の席にaと5が入り、約束どおり5a（円）に"
                       "なる流れを図解。練習の答は書かない",
                src="lesson_04.md 主概念1",
                params="代金＝1個の値段×個数／席にaと5／a×5→5a（円）／検算a＝100で500円",
                checks=ck.items)


# ===========================================================================
# 図6: L05 割合はテープ図で基準量を固定する（x円の3/4）
# 本文根拠: lesson_05.md 主概念1（(3/4)x・検算x＝1000で750円）
# 答え漏れ注意: 練習1の答（(2/5)x・0.6a・0.7y・0.15b）は図に書かない
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（本文 lesson_05.md 主概念1 と一致させる） ---
    num, den = 3, 4                # 割合 3/4
    x_test = 1000                  # 検算に使う値

    ck = Checker()
    ck.ok("検算: x＝1000で(3/4)×1000＝750円（本文の検算と一致）",
          num / den * x_test == 750)
    ck.ok("比べる量は基準量より小さい（3/4倍で増えない・本文の注意と整合）",
          num / den * x_test < x_test)
    ck.ok("テープ図の印の位置＝全体の3/4（描画パラメータの整合）",
          abs(240 / 320 - num / den) < 1e-9)

    cv = Canvas(440, 258)
    cv.add_hatch()
    cv.text_px(220, 40, "x 円（基準量＝もとにする量）", size=FS,
               anchor="middle", weight="bold")
    # テープ図: 全体320px・3/4の位置に印
    cv.rect_px(60, 52, 320, 36, sw=MAIN_W)
    cv.rect_px(60, 52, 240, 36, sw=AUX_W, fill="url(#h45)")
    cv.raw('<line x1="300" y1="44" x2="300" y2="96" stroke="#000" '
           f'stroke-width="{BOLD_W}"/>')
    cv.text_px(180, 112, "x円の3/4（斜線の部分）", size=FS_CAP,
               anchor="middle", weight="bold")
    cv.text_px(340, 112, "全体の3/4の位置", size=10, anchor="middle")
    # 言葉の式との対応
    cv.text_px(220, 156, "比べる量 ＝ 基準量 × 割合", size=15, anchor="middle",
               weight="bold")
    cv.text_px(220, 180, "（x円の3/4） ＝ 　x　 × 3/4", size=FS,
               anchor="middle")
    cv.text_px(220, 214, "「〜の」の直前にある量＝基準量を、先に絵で固定してから式へ",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 238, "検算: x＝1000 なら (3/4)×1000＝750円——1000円の4分の3と一致 ✓",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_tape_ratio_base.svg", canvas=cv, lesson="L05",
                title="割合のテープ図（x円の3/4・基準量を固定してから式へ)",
                intent="主概念1の可視化。x円のテープ全体を基準量とし、3/4の位置の印と"
                       "言葉の式の対応を図解。練習1の答は書かない",
                src="lesson_05.md 主概念1",
                params="割合3/4／テープ全体＝基準量x円／検算x＝1000→750円",
                checks=ck.items)


# ===========================================================================
# 図7: L05 「配って残る」の構造分解（a本から3本×5人分を配る→a−15本）
# 本文根拠: lesson_05.md 主概念3（3×5＝15・残りa−15・検算a＝20で5本）
# 答え漏れ注意: 練習3の答（(a−14)個・(1000−6x)円）・練習4の答0.25yは図に書かない
# ===========================================================================
def fig_L05_2():
    # --- パラメータ（本文 lesson_05.md 主概念3 と一致させる） ---
    per, people = 3, 5             # 3本ずつ×5人

    ck = Checker()
    ck.ok("配った本数: 3×5＝15本（本文の値と一致）", per * people == 15)
    ck.ok("検算: a＝20で残り20−15＝5本（本文の検算と一致）",
          20 - per * people == 5)
    ck.ok("残り＝はじめ−配った分（複数のaで構造が成立）",
          all(a - per * people == a - 15 for a in (20, 30, 16)))

    cv = Canvas(440, 250)
    cv.add_hatch()
    cv.text_px(220, 28, "配って残る＝はじめ − 配った分", size=FS,
               anchor="middle", weight="bold")
    # 左: はじめの束
    cv.rect_px(36, 48, 110, 84, sw=MAIN_W, rx=6)
    for i in range(6):
        cv.raw(f'<line x1="{52 + i * 13}" y1="60" x2="{52 + i * 13}" y2="104" '
               f'stroke="#000" stroke-width="{AUX_W}"/>')
    cv.text_px(91, 122, "はじめ a 本", size=FS_CAP, anchor="middle",
               weight="bold")
    # 中央: 配る矢印
    arrow_px(cv, 152, 88, 192, 68, w=1.4)
    cv.text_px(172, 52, "5人に3本ずつ配る", size=11, anchor="middle")
    # 右: 5人分の3本
    for i in range(people):
        bx = 200 + i * 46
        cv.rect_px(bx, 60, 38, 34, sw=AUX_W, rx=4, fill="url(#h45)")
        cv.text_px(bx + 19, 82, "3本", size=11, anchor="middle")
    cv.text_px(314, 116, "配った分 3×5＝15（本）", size=FS_CAP,
               anchor="middle", weight="bold")
    # 下: 残り
    arrow_px(cv, 220, 138, 220, 162, w=1.4)
    cv.text_px(220, 188, "残り ＝ a − 15（本）", size=17, anchor="middle",
               weight="bold")
    cv.text_px(220, 222, "検算: a＝20 なら 20−15＝5本——場面と一致 ✓",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig2_distribute_and_remain.svg", canvas=cv,
                lesson="L05",
                title="「配って残る」の構造分解（a本から3本×5人＝15本→残りa−15本）",
                intent="主概念3の可視化。はじめの束と配った分の2部品に分解する構造を図解。"
                       "練習3の答は書かない",
                src="lesson_05.md 主概念3",
                params="3本×5人＝15本／残りa−15本／検算a＝20で5本",
                checks=ck.items)


# ===========================================================================
# 図8: L06 かっこ付き代入の型（2x＋7のxの席に(−3)がはまる→値1）
# 本文根拠: lesson_06.md 主概念2（2×(−3)＋7＝−6＋7＝1・誤りは13）
# 答え漏れ注意: 練習2・4・5の答（(−2)²・−(−2)・4−(−5)の計算など）は図に書かない
# ===========================================================================
def fig_L06():
    # --- パラメータ（本文 lesson_06.md 主概念2 と一致させる） ---
    xv = -3                        # 代入する値

    ck = Checker()
    ck.ok("かっこ付き代入: 2×(−3)＋7＝1（本文の値と一致）",
          2 * xv + 7 == 1)
    ck.ok("途中式: 2×(−3)＝−6・−6＋7＝1（本文の途中式と一致）",
          2 * xv == -6 and -6 + 7 == 1)
    ck.ok("符号を落とす誤り: 2×3＋7＝13≠1（本文の事故例と一致）",
          2 * 3 + 7 == 13 and 13 != 1)

    cv = Canvas(440, 268)
    # 上段: (−3)のブロックが席に落ちる
    cv.textbox_px(166, 10, 56, 28, ["(−3)"], size=15, weight_first="bold")
    cv.text_px(236, 24, "かっこごと席に入れる", size=11, anchor="start")
    arrow_px(cv, 194, 42, 194, 58, w=1.4)
    cv.text_px(148, 84, "2×", size=18, anchor="middle", weight="bold")
    cv.rect_px(170, 62, 48, 30, sw=MAIN_W, dash=DASH, rx=4)
    cv.text_px(246, 84, "＋7", size=18, anchor="middle", weight="bold")
    cv.text_px(194, 110, "x の席（空欄）", size=10, anchor="middle")
    # 下段: 計算の流れ
    cv.text_px(220, 148, "2×(−3)＋7", size=17, anchor="middle", weight="bold")
    arrow_px(cv, 220, 158, 220, 172, w=1.2)
    cv.text_px(220, 190, "＝ −6＋7", size=15, anchor="middle")
    arrow_px(cv, 220, 198, 220, 212, w=1.2)
    cv.text_px(220, 230, "＝ 1", size=17, anchor="middle", weight="bold")
    cv.text_px(220, 256, "負の数は「かっこ付きで席に着く」——符号の置き忘れを防ぐ型",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_substitute_with_parentheses.svg", canvas=cv,
                lesson="L06",
                title="かっこ付き代入の型（2x＋7のxの席に(−3)→2×(−3)＋7＝−6＋7＝1）",
                intent="主概念2の可視化。xの席に(−3)がかっこごとはまり、計算が流れる型を"
                       "図解。練習の答は書かない（1は本文明示の解説値）",
                src="lesson_06.md 主概念2",
                params="式2x＋7／x＝−3／2×(−3)＋7＝−6＋7＝1",
                checks=ck.items)


# ===========================================================================
# 図9: L07 式→場面の翻訳（4b−3＝袋4つ分のあめ−食べた3個）
# 本文根拠: lesson_07.md 主概念2（4bが買った総数・−3が食べた分）
# 答え漏れ注意: 練習4・5の答（(10b−100)円・(1000−80)xの値など）は図に書かない
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（本文 lesson_07.md 主概念2 と一致させる） ---
    bags, eaten = 4, 3             # 袋4つ・食べた3個

    ck = Checker()
    ck.ok("構造: 4b−3＝b＋b＋b＋b−3（袋4つ分から3個引く・複数のbで一致）",
          all(bags * b - eaten == b + b + b + b - 3 for b in (5, 10, 8)))
    ck.ok("部品の個数: 袋4つ・食べた3個（パラメータと一致）",
          bags == 4 and eaten == 3)

    cv = Canvas(440, 276)
    cv.add_hatch()
    # 上段: 式を部品に色分け
    cv.rect_px(150, 24, 60, 34, sw=MAIN_W, rx=4, fill="url(#h45)")
    cv.text_px(180, 46, "4b", size=17, anchor="middle", weight="bold")
    cv.textbox_px(230, 24, 60, 34, ["−3"], size=17, weight_first="bold")
    # 矢印で場面へ
    arrow_px(cv, 180, 64, 116, 98, w=1.2)
    arrow_px(cv, 260, 64, 330, 98, w=1.2)
    # 左下: 袋4つ
    for i in range(bags):
        bx = 40 + i * 46
        cv.rect_px(bx, 104, 38, 44, sw=MAIN_W, rx=8, fill="url(#h45)")
        cv.text_px(bx + 19, 130, "b個", size=11, anchor="middle")
    cv.text_px(129, 168, "袋4つ分のあめ＝4b個", size=FS_CAP, anchor="middle",
               weight="bold")
    # 右下: 食べた3個
    for i in range(eaten):
        cx = 306 + i * 26
        cv.raw(f'<circle cx="{cx}" cy="126" r="8" fill="#fff" stroke="#000" '
               'stroke-width="1.4"/>')
    cv.raw('<line x1="292" y1="142" x2="372" y2="110" stroke="#000" '
           'stroke-width="2.0"/>')
    cv.text_px(332, 168, "食べた3個を除く＝−3", size=FS_CAP, anchor="middle",
               weight="bold")
    # 下段: 全体の読み
    cv.text_px(220, 212, "4b−3 ＝ 残っているあめの個数", size=16,
               anchor="middle", weight="bold")
    cv.text_px(220, 240, "①部品が場面の何か ②演算がどんな操作か ③全体を1文の日本語に",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 262, "（式→場面の逆向きの翻訳。部品ごとに場面の言葉へ戻す）",
               size=11, anchor="middle")

    return dict(file="L07_fig1_expression_to_scene.svg", canvas=cv,
                lesson="L07",
                title="式→場面の翻訳（4b−3＝袋4つ分のあめから食べた3個を除いた残り）",
                intent="主概念2の可視化。4bと−3の部品を場面の絵に対応させる構造読みを図解。"
                       "練習の答は書かない",
                src="lesson_07.md 主概念2",
                params="袋4つ×b個＝4b／食べた3個＝−3／全体＝残っているあめの個数",
                checks=ck.items)


# ===========================================================================
# 図10: L07 碁石の数え方3通り（1辺n個・例n＝5の正方形の外側）
# 本文根拠: lesson_07.md「数え方が違えば、式も違う」（4(n−1)・4n−4・2n＋2(n−2)）
# 答え漏れ注意: L11 S1・L12練習5の答（2n−4への展開・3nなど）は図に書かない
# ===========================================================================
def fig_L07_2():
    # --- パラメータ（本文 lesson_07.md と一致させる） ---
    n = 5                          # 1辺の碁石の個数（例）

    boundary = [(i, j) for i in range(n) for j in range(n)
                if i in (0, n - 1) or j in (0, n - 1)]
    ck = Checker()
    ck.ok("外側の碁石の総数＝16個（n＝5・本文の値と一致）",
          len(boundary) == 16)
    ck.ok("3通りの式が一致: 4(n−1)＝4n−4＝2n＋2(n−2)＝16（n＝5）",
          4 * (n - 1) == 16 and 4 * n - 4 == 16 and 2 * n + 2 * (n - 2) == 16)
    ck.ok("どのnでも3式は一致（n＝2..10で全数検査）",
          all(4 * (m - 1) == 4 * m - 4 == 2 * m + 2 * (m - 2)
              for m in range(2, 11)))
    # ①の4グループ（各n−1個）が外側全体をちょうど覆うことの検査
    gA = [(i, 0) for i in range(n - 1)]              # 上辺（右端の角を除く）
    gB = [(n - 1, j) for j in range(n - 1)]          # 右辺（下端の角を除く)
    gC = [(i, n - 1) for i in range(n - 1, 0, -1)]   # 下辺（左端の角を除く）
    gD = [(0, j) for j in range(n - 1, 0, -1)]       # 左辺（上端の角を除く)
    groups = gA + gB + gC + gD
    ck.ok("①の4グループ（各4個）が重複なく外側16個をちょうど覆う",
          len(groups) == 16 and set(groups) == set(boundary)
          and len(set(groups)) == len(groups))

    cv = Canvas(440, 300)
    cv.text_px(220, 26, "1辺 n 個（例: n＝5）の碁石——3通りの数え方", size=FS,
               anchor="middle", weight="bold")
    u = 22.0
    origins = (48, 196, 344)
    y0 = 56.0

    def stone(px, py, filled):
        if filled:
            cv.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#000"/>')
        else:
            cv.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#fff" '
                   'stroke="#000" stroke-width="1.3"/>')

    # パネル①: (n−1)個×4組（黒/白で組を交互に・組を破線枠で囲む）
    ox = origins[0]
    for (i, j) in boundary:
        filled = (i, j) in gA or (i, j) in gC
        stone(ox + i * u, y0 + j * u, filled)
    for pts in (gA, gB, gC, gD):
        xs_ = [ox + p[0] * u for p in pts]
        ys_ = [y0 + p[1] * u for p in pts]
        cv.rect_px(min(xs_) - 9, min(ys_) - 9,
                   max(xs_) - min(xs_) + 18, max(ys_) - min(ys_) + 18,
                   sw=AUX_W, dash=DASH, rx=8, fill="none")
    cv.text_px(ox + 2 * u, y0 + 4 * u + 28, "① (n−1)個×4組", size=10,
               anchor="middle", weight="bold")

    # パネル②: 4辺×n個から二重の角4個を引く（角に二重丸）
    ox = origins[1]
    for (i, j) in boundary:
        stone(ox + i * u, y0 + j * u, True)
        if i in (0, n - 1) and j in (0, n - 1):
            cv.raw(f'<circle cx="{ox + i * u:.1f}" cy="{y0 + j * u:.1f}" '
                   'r="8" fill="none" stroke="#000" stroke-width="1.3"/>')
    cv.text_px(ox + 2 * u, y0 + 4 * u + 28, "② 4辺×n個−二重の角4個",
               size=10, anchor="middle", weight="bold")

    # パネル③: 上下2辺はn個ずつ（黒）・左右は角を除く(n−2)個ずつ（白）
    ox = origins[2]
    for (i, j) in boundary:
        filled = j in (0, n - 1)
        stone(ox + i * u, y0 + j * u, filled)
    cv.text_px(436, y0 + 4 * u + 28, "③ 上下n個・左右(n−2)個",
               size=10, anchor="end", weight="bold")

    cv.text_px(220, 244, "どの数え方でも合計は同じ（n＝5 なら16個）",
               size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 266, "●・○・破線の枠は数え方のグループ分け（石の種類の違いではない）。",
               size=11, anchor="middle")
    cv.text_px(220, 284, "数え方の違いが、そのまま式の形の違いになる",
               size=11, anchor="middle")

    return dict(file="L07_fig2_stones_three_countings.svg", canvas=cv,
                lesson="L07",
                title="碁石の数え方3通り（1辺n個・例n＝5で外側16個）",
                intent="「数え方が違えば式も違う」の可視化。同じ16個を3通りの色分けで"
                       "数える図3枚。式の展開・S1の答は書かない",
                src="lesson_07.md 数え方が違えば、式も違う",
                params="n＝5／外側16個／①(n−1)個×4組 ②4辺×n個−角4個 ③上下n個・左右(n−2)個",
                checks=ck.items)


# ===========================================================================
# 図11: L08 天びんの図（3＋5と6＋2がつり合う——＝は関係の宣言）
# 本文根拠: lesson_08.md 主概念1（3＋5＝6＋2も堂々と正しい等式）
# 答え漏れ注意: 練習の答（8x＝640・y/5＝7・4a＝b・a−b＝2）は図に書かない
# ===========================================================================
def fig_L08():
    # --- パラメータ（本文 lesson_08.md 主概念1 と一致させる） ---
    left = (3, 5)
    right = (6, 2)

    ck = Checker()
    ck.ok("左の皿: 3＋5＝8（本文の値と一致）", sum(left) == 8)
    ck.ok("右の皿: 6＋2＝8（本文の値と一致）", sum(right) == 8)
    ck.ok("両辺が等しい（つり合いの根拠）", sum(left) == sum(right))

    cv = Canvas(440, 240)
    cv.text_px(220, 32, "＝は「左右がつり合っている」という宣言", size=FS,
               anchor="middle", weight="bold")
    # 天びん: はり・支点・皿
    cv.raw('<line x1="100" y1="104" x2="340" y2="104" stroke="#000" '
           f'stroke-width="{BOLD_W}"/>')
    cv.raw('<polygon points="220,104 202,150 238,150" fill="none" '
           f'stroke="#000" stroke-width="{MAIN_W}"/>')
    cv.raw('<line x1="180" y1="150" x2="260" y2="150" stroke="#000" '
           f'stroke-width="{MAIN_W}"/>')
    for bx, expr in ((100, "3＋5"), (340, "6＋2")):
        cv.raw(f'<line x1="{bx}" y1="104" x2="{bx - 22}" y2="{136}" '
               f'stroke="#000" stroke-width="{AUX_W}"/>')
        cv.raw(f'<line x1="{bx}" y1="104" x2="{bx + 22}" y2="{136}" '
               f'stroke="#000" stroke-width="{AUX_W}"/>')
        cv.rect_px(bx - 30, 136, 60, 30, sw=MAIN_W, rx=4)
        cv.text_px(bx, 156, expr, size=15, anchor="middle", weight="bold")
    cv.text_px(100, 186, "左辺", size=11, anchor="middle")
    cv.text_px(340, 186, "右辺", size=11, anchor="middle")
    cv.text_px(220, 208, "3＋5＝6＋2 —— どちらの皿も同じ重さ（どちらも8）",
               size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(220, 228, "右側が「答え」になっていなくてもよい", size=11,
               anchor="middle")

    return dict(file="L08_fig1_balance_equality.svg", canvas=cv, lesson="L08",
                title="天びんの図（3＋5と6＋2がつり合う——＝は関係の宣言）",
                intent="主概念1の可視化。等号を左右のつり合いとして読む関係的読みを図解。"
                       "練習の答は書かない",
                src="lesson_08.md 主概念1",
                params="左の皿3＋5／右の皿6＋2／両辺とも8でつり合う",
                checks=ck.items)


# ===========================================================================
# 図12: L09 境界の数100の含む/含まない（4本の数直線）
# 本文根拠: lesson_09.md 主概念1（以上・以下＝含む／より大きい・未満＝含まない）
# 答え漏れ注意: 練習の答（x≧40・6a＜700・2y＋150≦500・b＜20・x≦12）は図に書かない
# ===========================================================================
def fig_L09():
    # --- パラメータ（本文 lesson_09.md 主概念1 と一致させる） ---
    b = 100                        # 境界の数

    ck = Checker()
    ck.ok("以上・以下は境界を含む: 100≧100・100≦100は成り立つ",
          (b >= b) is True and (b <= b) is True)
    ck.ok("より大きい・未満は境界を含まない: 100＞100・100＜100は成り立たない",
          (b > b) is False and (b < b) is False)
    ck.ok("101は「より大きい」に入り、99は「未満」に入る（向きの検算）",
          (101 > b) is True and (99 < b) is True)

    cv = Canvas(440, 300)
    cv.text_px(220, 26, "境界の数 100 を「含む」か「含まない」か", size=FS,
               anchor="middle", weight="bold")
    rows = [
        ("100以上　x≧100", True, +1, "含む ●"),
        ("100以下　x≦100", True, -1, "含む ●"),
        ("100より大きい　x＞100", False, +1, "含まない ○"),
        ("100未満　x＜100", False, -1, "含まない ○"),
    ]
    x0, x1, xb = 196, 416, 300     # 数直線の左端・右端・境界100の位置
    for k, (label, inc, direc, note) in enumerate(rows):
        y = 62 + k * 56
        cv.text_px(16, y - 2, label, size=12, anchor="start")
        cv.text_px(16, y + 16, note, size=10, anchor="start")
        cv.raw(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#000" '
               f'stroke-width="{AUX_W}"/>')
        arrow_px(cv, x1 - 8, y, x1, y, w=AUX_W, head=6)
        cv.raw(f'<line x1="{xb}" y1="{y - 5}" x2="{xb}" y2="{y + 5}" '
               f'stroke="#000" stroke-width="{AUX_W}"/>')
        cv.text_px(xb, y + 22, "100", size=11, anchor="middle")
        # 範囲の太線
        end = x1 - 14 if direc > 0 else x0 + 6
        cv.raw(f'<line x1="{xb}" y1="{y}" x2="{end}" y2="{y}" stroke="#000" '
               f'stroke-width="{BOLD_W}"/>')
        arrow_px(cv, (xb + end) / 2, y, end, y, w=BOLD_W, head=9)
        # 境界のマーカー（含む＝●・含まない＝○）
        if inc:
            cv.raw(f'<circle cx="{xb}" cy="{y}" r="5.5" fill="#000"/>')
        else:
            cv.raw(f'<circle cx="{xb}" cy="{y}" r="5.5" fill="#fff" '
                   'stroke="#000" stroke-width="1.6"/>')
    cv.text_px(220, 288, "「以上・以下」＝●で境界を含む、「より大きい・未満」＝○で含まない",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_boundary_number_lines.svg", canvas=cv,
                lesson="L09",
                title="境界の数100の含む/含まない（≧・≦は●、＞・＜は○の4本の数直線）",
                intent="主概念1の可視化。境界100を含む（●）か含まない（○）かを4本の"
                       "数直線で対比。練習の答は書かない",
                src="lesson_09.md 主概念1",
                params="境界100／x≧100・x≦100＝●含む／x＞100・x＜100＝○含まない",
                checks=ck.items)


# ===========================================================================
# 図13: L10 符号ごと切り取る（2x−3と5−4x＋1を項のカードへ）
# 本文根拠: lesson_10.md 主概念1（2x−3＝2x＋(−3)・項は5、−4x、＋1）
# 答え漏れ注意: 練習の答（−x、4、−3xの列挙・係数1/3など）は図に書かない
# ===========================================================================
def fig_L10():
    ck = Checker()
    ck.ok("読み替え: 2x−3＝2x＋(−3)（複数のxで一致）",
          all(2 * x - 3 == 2 * x + (-3) for x in (2, 5, -1)))
    ck.ok("分解の再構成: 5−4x＋1＝5＋(−4x)＋(＋1)（複数のxで一致）",
          all(5 - 4 * x + 1 == 5 + (-4 * x) + 1 for x in (2, 5, -1)))
    ck.ok("項の個数: 2x−3は2個・5−4x＋1は3個（本文の主要数値と一致）",
          len(["2x", "−3"]) == 2 and len(["5", "−4x", "＋1"]) == 3)

    cv = Canvas(440, 262)
    cv.add_hatch()
    cv.text_px(220, 28, "ハサミを入れるのは、いつも ＋・− の直前", size=FS,
               anchor="middle", weight="bold")
    # 行1: 2x−3
    cv.text_px(80, 66, "2x − 3", size=18, anchor="middle", weight="bold")
    cv.raw(f'<line x1="86" y1="46" x2="86" y2="78" stroke="#000" '
           f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    arrow_px(cv, 138, 60, 180, 60, w=1.4)
    cv.rect_px(192, 44, 54, 32, sw=MAIN_W, rx=4, fill="url(#h45)")
    cv.text_px(219, 65, "2x", size=15, anchor="middle", weight="bold")
    cv.textbox_px(258, 44, 54, 32, ["−3"], size=15, weight_first="bold")
    cv.text_px(330, 65, "項は2つ", size=11, anchor="start")
    # 行2: 5−4x＋1
    cv.text_px(88, 140, "5 − 4x ＋ 1", size=18, anchor="middle", weight="bold")
    for cx in (66, 122):
        cv.raw(f'<line x1="{cx}" y1="120" x2="{cx}" y2="152" stroke="#000" '
               f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    arrow_px(cv, 152, 134, 180, 134, w=1.4)
    cv.textbox_px(192, 118, 44, 32, ["5"], size=15, weight_first="bold")
    cv.rect_px(246, 118, 58, 32, sw=MAIN_W, rx=4, fill="url(#h45)")
    cv.text_px(275, 139, "−4x", size=15, anchor="middle", weight="bold")
    cv.textbox_px(314, 118, 44, 32, ["＋1"], size=15, weight_first="bold")
    cv.text_px(372, 139, "項は3つ", size=11, anchor="start")
    # 下段
    cv.text_px(220, 188, "2x−3 ＝ 2x＋(−3)——＋で結ばれた一つひとつの部品が項",
               size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 214, "−は「ひき算の記号」ではなく、項の一部として符号ごと切り取る",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 240, "斜線＝文字の項　白＝数の項", size=11, anchor="middle")

    return dict(file="L10_fig1_terms_cut_by_sign.svg", canvas=cv, lesson="L10",
                title="符号ごと切り取る（2x−3→2x・−3／5−4x＋1→5・−4x・＋1）",
                intent="主概念1の可視化。＋・−の直前の切り取り位置と符号ごとの項カードを"
                       "図解。練習の答は書かない",
                src="lesson_10.md 主概念1",
                params="2x−3→項2個（2x・−3）／5−4x＋1→項3個（5・−4x・＋1）",
                checks=ck.items)


# ===========================================================================
# 図14: L11 3手順の流れ図（4x−1−2x＋5→分解→仕分け→2x＋4）
# 本文根拠: lesson_11.md 主概念1（(4x−2x)＋(−1＋5)＝2x＋4）
# 答え漏れ注意: 練習の答（5x＋4・4a＋5・3x−2・4x＋6など）は図に書かない
# ===========================================================================
def fig_L11():
    # --- パラメータ（本文 lesson_11.md 主概念1 と一致させる） ---
    cx_, c0 = (4, -2), (-1, 5)     # xの項の係数 / 数の項

    ck = Checker()
    ck.ok("文字の項: 4x−2x→2x（係数4＋(−2)＝2・本文と一致）", sum(cx_) == 2)
    ck.ok("数の項: −1＋5＝4（本文と一致）", sum(c0) == 4)
    ck.ok("代入検算: x＝10で元の式4x−1−2x＋5＝24＝2x＋4（複数の値で一致）",
          all(cx_[0] * x + c0[0] + cx_[1] * x + c0[1]
              == sum(cx_) * x + sum(c0) for x in (10, 2, -3))
          and 4 * 10 - 1 - 2 * 10 + 5 == 24)

    cv = Canvas(440, 316)
    cv.add_hatch()
    # 上段: 元の式と切り取り位置
    cv.text_px(220, 38, "4x − 1 − 2x ＋ 5", size=19, anchor="middle",
               weight="bold")
    for cxp in (176, 224, 286):
        cv.raw(f'<line x1="{cxp}" y1="18" x2="{cxp}" y2="50" stroke="#000" '
               f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    # 中段: 4つの項カード
    terms = [("4x", True), ("−1", False), ("−2x", True), ("＋5", False)]
    bw, bh, gap, x0, by = 70, 34, 22, 38, 72
    for i, (t, is_x) in enumerate(terms):
        bx = x0 + i * (bw + gap)
        if is_x:
            cv.rect_px(bx, by, bw, bh, sw=MAIN_W, rx=4, fill="url(#h45)")
            cv.text_px(bx + bw / 2, by + bh / 2 + 5, t, size=15,
                       anchor="middle", weight="bold")
        else:
            cv.textbox_px(bx, by, bw, bh, [t], size=15, weight_first="bold")
    cv.text_px(220, 128, "①符号ごと項に分解（斜線＝文字の項・白＝数の項）",
               size=11, anchor="middle")
    # 下段: 仕分けの箱
    arrow_px(cv, x0 + bw / 2, by + bh + 26, 110, 168, w=1.4)          # 4x
    arrow_px(cv, x0 + 2 * (bw + gap) + bw / 2, by + bh + 26, 146, 168, w=1.4)  # −2x
    arrow_px(cv, x0 + (bw + gap) + bw / 2, by + bh + 26, 294, 168, w=1.4)      # −1
    arrow_px(cv, x0 + 3 * (bw + gap) + bw / 2, by + bh + 26, 330, 168, w=1.4)  # ＋5
    cv.rect_px(48, 172, 160, 66, sw=MAIN_W, rx=6, fill="url(#h45)")
    cv.text_px(128, 192, "文字の項", size=FS_CAP, anchor="middle",
               weight="bold")
    cv.text_px(128, 214, "4x　−2x　→ 2x", size=14, anchor="middle",
               weight="bold")
    cv.rect_px(232, 172, 160, 66, sw=MAIN_W, rx=6)
    cv.text_px(312, 192, "数の項", size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(312, 214, "−1　＋5　→ ＋4", size=14, anchor="middle",
               weight="bold")
    cv.text_px(220, 258, "②文字の項・数の項に仕分け ③それぞれまとめる",
               size=11, anchor="middle")
    cv.text_px(220, 286, "4x−1−2x＋5 ＝ 2x＋4", size=17, anchor="middle",
               weight="bold")
    cv.text_px(220, 308, "文字の項と数の項は、種類が違うのでこれ以上まとめられない",
               size=11, anchor="middle")

    return dict(file="L11_fig1_sort_and_combine_flow.svg", canvas=cv,
                lesson="L11",
                title="3手順の流れ図（4x−1−2x＋5→符号ごと分解→仕分け→2x＋4）",
                intent="主概念1の可視化。①分解②仕分け③まとめるの3手順を項カードと箱で"
                       "図解。練習の答は書かない（2x＋4は本文明示の解説値）",
                src="lesson_11.md 主概念1",
                params="式4x−1−2x＋5／文字の項4x・−2x→2x／数の項−1・＋5→＋4／結果2x＋4",
                checks=ck.items)


# ===========================================================================
# 図15: L12 分配の矢印図（2(3x＋4)→6x＋8——全員に配る）
# 本文根拠: lesson_12.md 主概念1（2×3x＝6x・2×4＝8・x＝10で68の検算）
# 答え漏れ注意: 練習の答（6x＋3・−8x＋6・8x＋3・5x−5など）は図に書かない
# ===========================================================================
def fig_L12():
    # --- パラメータ（本文 lesson_12.md 主概念1 と一致させる） ---
    k = 2
    t1, t0 = 3, 4                  # かっこの中 3x＋4

    ck = Checker()
    ck.ok("分配の係数: 2×3＝6・2×4＝8（本文の6x＋8と一致）",
          k * t1 == 6 and k * t0 == 8)
    ck.ok("代入検算: x＝10で2(3x＋4)＝68＝6x＋8（本文の検算と一致）",
          k * (t1 * 10 + t0) == 68 and 6 * 10 + 8 == 68)
    ck.ok("配り忘れの誤り: 6x＋4はx＝10で64≠68（本文の事故例と一致）",
          6 * 10 + 4 == 64 and 64 != 68)

    cv = Canvas(440, 248)
    cv.text_px(220, 32, "数×一次式——かっこの中の全員に配る", size=FS,
               anchor="middle", weight="bold")
    # 式と分配の弧矢印（係数2から3xと＋4のそれぞれへ）
    cv.text_px(120, 108, "2(3x＋4)", size=20, anchor="middle", weight="bold")
    xk = 84                        # 係数2のおよその位置
    cv.raw(f'<path d="M {xk} 88 Q {xk + 30} 66 {xk + 48} 86" fill="none" '
           'stroke="#000" stroke-width="1.2"/>')
    arrow_px(cv, xk + 46, 82, xk + 50, 88, w=1.2, head=6)
    cv.raw(f'<path d="M {xk} 88 Q {xk + 56} 52 {xk + 92} 86" fill="none" '
           'stroke="#000" stroke-width="1.2"/>')
    arrow_px(cv, xk + 90, 80, xk + 94, 88, w=1.2, head=6)
    arrow_px(cv, 196, 102, 248, 102, w=1.6)
    cv.text_px(310, 108, "6x＋8", size=20, anchor="middle", weight="bold")
    cv.text_px(220, 148, "2×3x＝6x　　2×4＝8", size=FS, anchor="middle")
    cv.text_px(220, 182, "矢印の本数＝かっこの中の項の数。先頭だけに配る事故を矢印で防ぐ",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 208, "検算: x＝10 なら元の式は 2×34＝68、6x＋8 も 68 で一致 ✓",
               size=FS_CAP, anchor="middle")
    cv.text_px(220, 232, "（(3x＋4)＋(3x＋4)、つまり「(3x＋4)の2個分」と数えても同じ）",
               size=11, anchor="middle")

    return dict(file="L12_fig1_distribute_arrows.svg", canvas=cv, lesson="L12",
                title="分配の矢印図（2(3x＋4)→6x＋8——全員に配る）",
                intent="主概念1の可視化。係数2からかっこの中の各項への矢印で「全員に配る」を"
                       "図解。練習の答は書かない（6x＋8は本文明示の解説値）",
                src="lesson_12.md 主概念1",
                params="2(3x＋4)／2×3x＝6x・2×4＝8／結果6x＋8／検算x＝10で68",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + 答え漏れの機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02_1, fig_L02_2, fig_L03, fig_L04, fig_L05_1,
        fig_L05_2, fig_L06, fig_L07_1, fig_L07_2, fig_L08, fig_L09,
        fig_L10, fig_L11, fig_L12]

# 答え漏れの禁止文字列（近隣の練習・stretchの答。answer_key と照合して選定。
# 数字だけの文字列は座標と衝突するため使わず、式の形で指定する）
FORBIDDEN = {
    "L01_fig1_square_perimeter_letter.svg": ["x×6", "a×3"],
    "L02_fig1_product_notation_rules.svg": ["7x", "3ab", "0.1x", "5(a＋b)",
                                            "−y"],
    "L02_fig2_quotient_fraction_check.svg": ["x/9", "7/a", "(x−2)/3", "m/6"],
    "L03_fig1_exponent_grouping.svg": ["5a³", "ab²", "x²−7y", "x²＋x"],
    "L04_fig1_word_formula_bridge.svg": ["4x（円）", "3t", "(3a＋2b)",
                                         "(500−2y)", "x/7"],
    "L05_fig1_tape_ratio_base.svg": ["(2/5)x", "0.6a", "0.7y", "0.15b",
                                     "0.4x"],
    "L05_fig2_distribute_and_remain.svg": ["a−14", "1000−6x", "0.25y"],
    "L06_fig1_substitute_with_parentheses.svg": ["(−2)²", "−(−2)", "4−(−5)",
                                                 "4×(1/2)"],
    "L07_fig1_expression_to_scene.svg": ["10b−100", "(1000−80)x"],
    "L07_fig2_stones_three_countings.svg": ["2n−4", "3n", "n−1、n、n＋1"],
    "L08_fig1_balance_equality.svg": ["8x＝640", "y/5＝7", "4a＝b", "a−b＝2"],
    "L09_fig1_boundary_number_lines.svg": ["x≧40", "6a＜700", "2y＋150≦500",
                                           "b＜20", "x≦12"],
    "L10_fig1_terms_cut_by_sign.svg": ["−x、4、−3x", "4a と −7", "(1/3)×x"],
    "L11_fig1_sort_and_combine_flow.svg": ["5x＋4", "4a＋5", "3x−2", "5x＋6",
                                           "2a＋3", "−3x−4", "4x＋6", "8x"],
    "L12_fig1_distribute_arrows.svg": ["6x＋3", "−8x＋6", "4x−3", "−3x−1",
                                       "8x＋3", "2x＋6", "5x−5", "3x＋23"],
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
        "spec: docs/SPEC_figures.md 準拠（先行単元 jhs-math-2-expression-calculation と同様式）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 文字と式単元 図版台帳",
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
        "- 近隣の練習・stretchの答（L01練習のx×6/a×3・L02練習の7x/3ab/m/6・"
        "L05練習の0.6a/0.7y/(a−14)個・L08練習の8x＝640・L09練習のx≧40・"
        "L11練習の5x＋4/4x＋6・L12練習の6x＋3/8x＋3など）は図に書かない。",
        "- 図に載る式・数値はすべて該当レッスン本文が地の文で明示する解説値"
        "（a×4・4a・a³b²・5a（円）・750円・a−15・値1・2x＋4・6x＋8など）に限る。",
        "- L07の碁石図は、3通りの数え方のグループ分けだけを示し、"
        "式の展開結果（L11 S1・L12練習5で扱う内容）は図・title・descのいずれにも書かない。",
        "- 各図の禁止文字列は main() の FORBIDDEN 表で機械検査し、"
        "1件でも検出されれば生成が停止する（数字だけの文字列は座標と衝突するため、"
        "式の形で指定している）。",
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
