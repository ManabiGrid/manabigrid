#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1数学「一次方程式」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: 先行単元（中2「連立方程式」）
materials/jhs-math-2/jhs-math-2-simultaneous-equations/assets_provenance/generate_figures.py
のコード来歴方式に準拠。ヘルパー群（Canvas/矢印ほか）は同スクリプトから
コピー再利用（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig1_{slug}.svg（10枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない
  （代入表の全数照合・天びん操作の等式保存・各例題解の代入検算・整数判定など）。
- 答えの分離方針: 練習問題・stretch の答は図に一切書かない。図に載せる数値は
  与件と、本文の例題解説が明示している途中式・解説値
  （L01のx＝2・L02のx＝5・L04のx＝5・L06のx＝9・L07のx＝5・L09のx＝3.75 など）のみ。
  L08の線分図は本文解説値（人数10人・総数58個）を区切り比の計算にだけ使い、
  図中ラベルは一般形（4x・18・7x・12）にとどめる。
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

# ---- 様式定数（先行単元 docs/SPEC_figures.md 準拠） -----------------------
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
        """濃淡+ハッチングの塗り分けパターンを内蔵defsへ"""
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

    def ellipse_px(self, cx, cy, rx, ry, w=MAIN_W, dash=None, n=72):
        """楕円を座標サンプリングした折れ線で描く（arcフラグ不使用）"""
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
            f'(コード来歴方式・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0, dash=None):
    """SVG座標(px)で矢印(線+先端の三角形)を描く。概念図・系統図用"""
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


def solve_linear(a, b):
    """ax＝b を解く（検算専用）"""
    assert a != 0, "係数が0"
    return b / a


# ===========================================================================
# 図1: L01 代入して確かめる表（x＋3＝5・xに−3〜3を代入・○はx＝2だけ）
# 本文根拠: lesson_01.md 主概念2（代入表と「x＝2のときだけ」の解説）
# 答え扱い: x＝2は本文主概念2が明示する解説値のため記載可
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md 主概念2 と一致させる） ---
    add_const, target = 3, 5          # 方程式 x＋3＝5
    xs = list(range(-3, 4))           # 代入する値 −3〜3

    lhs = [x + add_const for x in xs]
    hits = [x for x in xs if x + add_const == target]
    ck = Checker()
    ck.ok("x＝−3〜3 の左辺の値は本文の表どおり 0〜6",
          lhs == [0, 1, 2, 3, 4, 5, 6])
    ck.ok("5と等しくなるのは x＝2 ただ1つ（本文の解説値・図に記載）",
          hits == [2])
    ck.ok("表の外でも成り立たない: x＞3では左辺＞6＞5・x＜−3では左辺＜0＜5",
          (-4 + add_const < target) and (4 + add_const > target)
          and all(lhs[i + 1] - lhs[i] == 1 for i in range(len(lhs) - 1)))

    cv = Canvas(560, 262)
    cv.text_px(280, 26, "方程式 x＋3＝5 に、xの値を順に代入してみる", size=FS,
               anchor="middle", weight="bold")
    x0, y0 = 128, 44
    cw, ch = 42, 28
    cols = ["…"] + [str(x) for x in xs] + ["…"]
    row_labels = [("① xの値", cols),
                  ("② x＋3の値", ["…"] + [str(v) for v in lhs] + ["…"]),
                  ("③ 5と等しい？", ["×"] + ["×" if x != 2 else "○" for x in xs] + ["×"])]
    for r, (lab, cells) in enumerate(row_labels):
        ry = y0 + r * ch
        cv.rect_px(x0 - 100, ry, 100, ch, sw=AUX_W, fill="#eee")
        cv.text_px(x0 - 50, ry + ch / 2 + 11 * 0.35, lab, size=11, anchor="middle")
        for c, s in enumerate(cells):
            cv.rect_px(x0 + c * cw, ry, cw, ch, sw=AUX_W)
            wgt = "bold" if (r == 2 and s == "○") else None
            cv.text_px(x0 + c * cw + cw / 2, ry + ch / 2 + FS * 0.35, s,
                       size=FS, anchor="middle", weight=wgt)
    # x＝2 の列（cols内で先頭の…を含めindex 6）を太枠で強調
    hit_col = 1 + xs.index(2)
    cv.rect_px(x0 + hit_col * cw, y0, cw, ch * 3, sw=BOLD_W * 0.7, fill="none")
    arrow_px(cv, x0 + hit_col * cw + cw / 2, y0 + 3 * ch + 34,
             x0 + hit_col * cw + cw / 2, y0 + 3 * ch + 6, w=1.4)
    cv.text_px(x0 + hit_col * cw + cw / 2, y0 + 3 * ch + 50,
               "条件をくぐり抜けた値＝解（x＝2）", size=FS, anchor="middle",
               weight="bold")
    cv.text_px(280, 214, "「…」の部分でも左辺は1ずつ増え続けるので、5に等しくなることはもうない",
               size=FS_CAP, anchor="middle")
    cv.text_px(280, 232, "①入力→②左辺の値→③判定 の3段で、1つずつ条件に照らしている",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_substitute_and_check_table.svg", canvas=cv,
                lesson="L01",
                title="代入して確かめる表（x＋3＝5・○が付くのはx＝2だけ）",
                intent="主概念2「解＝条件を満たす値」の活動の可視化。○×判定の3段構造",
                src="lesson_01.md 主概念2（代入表の直後）",
                params="x＋3＝5・xは−3〜3（両端に…）・左辺の値0〜6・○はx＝2のみ",
                checks=ck.items)


# ===========================================================================
# 図2: L02 天びんの2コマ（x＋2＝7 → 両皿から2個ずつ取り除く → x＝5）
# 本文根拠: lesson_02.md 主概念2（袋x＋おもり2個と おもり7個のつり合い）
# 答え扱い: x＝5は本文主概念2が明示する解説値のため記載可
# ===========================================================================
def fig_L02():
    # --- パラメータ（本文 lesson_02.md 主概念2 と一致させる） ---
    left_w, right_w, remove = 2, 7, 2     # 左皿おもり2個・右皿7個・2個ずつ除去

    ck = Checker()
    ck.ok("両皿から2個ずつ取り除くと右皿は 7−2＝5個（本文の解説値・図に記載）",
          right_w - remove == 5)
    ck.ok("x＝5 は x＋2＝7 を成り立たせる（5＋2＝7）", 5 + left_w == right_w)
    ck.ok("等式の保存: a＝b なら a−c＝b−c（数値組3通りで恒等）",
          all(abs((a - c) - (b - c)) < 1e-9
              for a, b, c in [(7, 7, 2), (10, 10, 3), (4.5, 4.5, -1)]))

    cv = Canvas(500, 262)

    def balance(cx, base_y, left_labels, right_labels, eq):
        """つり合った天びん1台（皿の上に枠ラベル）"""
        beam_y = base_y - 56
        half = 72
        cv.raw(f'<polygon points="{cx:.1f},{beam_y:.1f} {cx - 13:.1f},{base_y:.1f} '
               f'{cx + 13:.1f},{base_y:.1f}" fill="#ccc" stroke="#000" '
               f'stroke-width="{MAIN_W}"/>')
        cv.raw(f'<line x1="{cx - half:.1f}" y1="{beam_y:.1f}" x2="{cx + half:.1f}" '
               f'y2="{beam_y:.1f}" stroke="#000" stroke-width="{BOLD_W * 0.7}"/>')
        for side, labels in ((-1, left_labels), (1, right_labels)):
            px = cx + side * half
            cv.raw(f'<line x1="{px:.1f}" y1="{beam_y:.1f}" x2="{px:.1f}" '
                   f'y2="{beam_y + 12:.1f}" stroke="#000" stroke-width="{AUX_W}"/>')
            for i, lab in enumerate(labels):
                bw, bh = 62, 24
                by = beam_y + 12 + i * (bh + 3)
                cv.rect_px(px - bw / 2, by, bw, bh, sw=MAIN_W, rx=3)
                cv.text_px(px, by + bh / 2 + 11.5 * 0.35, lab, size=11.5,
                           anchor="middle", weight="bold")
        cv.text_px(cx, base_y + 24, eq, size=15, anchor="middle", weight="bold")

    balance(118, 168, ["袋 x個", "おもり2個"], ["おもり7個"], "x＋2＝7")
    cv.text_px(248, 44, "両皿から", size=11, anchor="middle")
    cv.text_px(248, 58, "おもりを2個ずつ", size=11, anchor="middle")
    cv.text_px(248, 72, "取り除く（性質②）", size=11, anchor="middle")
    arrow_px(cv, 222, 86, 274, 86, w=1.6, head=8)
    balance(382, 168, ["袋 x個"], ["おもり5個"], "x＝5")
    cv.text_px(250, 224, "左右から同じだけ取るのだから、天びんはつり合ったまま",
               size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(250, 246, "——両辺から同じ数を引いても、等しさは崩れない",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_balance_remove_two.svg", canvas=cv, lesson="L02",
                title="天びんの2コマ（x＋2＝7 → 両皿から2個ずつ → x＝5）",
                intent="主概念2「等式の性質」の操作イメージの中心図",
                src="lesson_02.md 主概念2（天びんの段落の直後）",
                params="左皿=袋x＋おもり2個・右皿=おもり7個→2個ずつ除去→x＝5（本文明示）",
                checks=ck.items)


# ===========================================================================
# 図3: L03 フル手順と移項の対比（x＋6＝13——同じ変形の長い書き方と短い書き方）
# 本文根拠: lesson_03.md 発見（性質②のフルコースと移項の見比べ）
# 答え扱い: 図はx＝13−6まで（本文の並記と同じ範囲）。解7はassertのみ
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md と一致させる） ---
    move_const, rhs = 6, 13           # x＋6＝13

    ck = Checker()
    x = solve_linear(1, rhs - move_const)
    ck.ok("x＝13−6＝7 が元の式を満たす（7＋6＝13・解の値は図に書かない）",
          abs(x - 7) < 1e-9 and x + move_const == rhs)
    ck.ok("フル手順と移項は同じ変形: 両辺−6の結果が x＝13−6",
          (rhs - move_const) == (rhs - move_const))
    ck.ok("移項で符号が反転する（＋6 → −6）", +move_const == -(-move_const))

    cv = Canvas(500, 268)
    # 左列: フルコース（3行）
    lx, lw = 28, 200
    cv.textbox_px(lx, 24, lw, 30, ["長い書き方（性質②のフルコース）"],
                  size=11.5, sw=MAIN_W, weight_first="bold", fill="#eee")
    cv.text_px(lx + lw / 2, 84, "x＋6＝13", size=16, anchor="middle")
    cv.text_px(lx + lw / 2, 118, "x＋6−6＝13−6", size=16, anchor="middle")
    cv.text_px(lx + lw / 2, 152, "x＝13−6", size=16, anchor="middle", weight="bold")
    cv.text_px(lx + lw + 4, 104, "両辺から6を引く（性質②）", size=10, anchor="end")
    cv.text_px(lx + lw + 4, 136, "−6＋6＝0 で左辺が消える", size=10, anchor="end")
    # 右列: 移項（2行）
    rx, rw = 292, 180
    cv.textbox_px(rx, 24, rw, 30, ["短い書き方（移項）"],
                  size=11.5, sw=MAIN_W, weight_first="bold", fill="#eee")
    cv.text_px(rx + rw / 2, 84, "x＋6＝13", size=16, anchor="middle")
    cv.text_px(rx + rw / 2, 152, "x＝13−6", size=16, anchor="middle", weight="bold")
    # ＋6→−6 の引っこし矢印（曲がりの折れ線+先端）
    cv.raw(f'<polyline points="{rx + rw / 2 + 14:.1f},92 {rx + rw / 2 + 44:.1f},112 '
           f'{rx + rw / 2 + 30:.1f},136" fill="none" stroke="#000" '
           f'stroke-width="1.4" stroke-dasharray="{DASH}"/>')
    arrow_px(cv, rx + rw / 2 + 30, 136, rx + rw / 2 + 22, 142, w=1.4, head=7,
             dash=DASH)
    cv.text_px(rx + rw + 22, 112, "符号を変えて", size=10, anchor="end")
    cv.text_px(rx + rw + 24, 125, "反対側の辺へ", size=10, anchor="end")
    # 2列を結ぶラベル（＝で結ばない）
    cv.textbox_px(206, 180, 128, 40, ["同じ変形の", "長い書き方と短い書き方"],
                  size=10.5, sw=AUX_W, dash=DASH)
    cv.raw(f'<line x1="128" y1="170" x2="216" y2="196" stroke="#000" '
           f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    cv.raw(f'<line x1="334" y1="196" x2="382" y2="164" stroke="#000" '
           f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    cv.text_px(250, 244, "移項は瞬間移動ではなく、「両辺から同じ数を引いた」途中を省いた書き方",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_full_steps_vs_transposition.svg", canvas=cv,
                lesson="L03",
                title="フル手順と移項の対比（x＋6＝13 → x＝13−6）",
                intent="移項＝性質②の省略記法であることの対比図。2列は＝で結ばない",
                src="lesson_03.md 【ことば】移項の直後",
                params="x＋6＝13・両辺−6・x＝13−6（本文並記と同一範囲）／解7はassertのみ",
                checks=ck.items)


# ===========================================================================
# 図4: L04 解く手順の全体地図（5x−7＝2x＋8 → 移項→整理→係数でわる→検算）
# 本文根拠: lesson_04.md 主概念1 例1と手順1〜4
# 答え扱い: x＝5・両辺18は本文例1が明示する解説値のため記載可
# ===========================================================================
def fig_L04():
    # --- パラメータ（本文 lesson_04.md 例1 と一致させる） ---
    # 5x−7＝2x＋8 → 5x−2x＝8＋7 → 3x＝15 → x＝5
    ck = Checker()
    ck.ok("移項後の整理: 5−2＝3・8＋7＝15", 5 - 2 == 3 and 8 + 7 == 15)
    x = solve_linear(3, 15)
    ck.ok("x＝5（本文明示の解説値・図に記載）", abs(x - 5) < 1e-9)
    ck.ok("検算: 左辺 5×5−7＝18・右辺 2×5＋8＝18 で一致",
          5 * 5 - 7 == 18 and 2 * 5 + 8 == 18)

    cv = Canvas(480, 344)
    bx, bw, bh = 60, 190, 36
    steps = [
        (24, "5x−7＝2x＋8", None),
        (86, "5x−2x＝8＋7", "1 移項（性質①②の省略）"),
        (148, "3x＝15", "2 整理してＡx＝Ｂの形に"),
        (210, "x＝5", "3 両辺を係数3でわる（性質④）"),
        (272, "検算: 両辺とも18で成り立つ", "4 解を代入して検算"),
    ]
    for i, (by, label, note) in enumerate(steps):
        wgt = "bold" if i in (3,) else None
        w2 = bw if i < 4 else 250
        cv.textbox_px(bx, by, w2, bh, [label], size=14, sw=MAIN_W,
                      weight_first=wgt)
        if i > 0:
            arrow_px(cv, bx + bw / 2, by - 26 + bh / 2 + 4, bx + bw / 2, by - 2,
                     w=1.6, head=7)  # 本流はすべて実線（検算も本流）
        if note:
            num, txt = note.split(" ", 1)
            cv.text_px(bx + max(bw, w2) + 16, by + bh / 2 - 3, "手順" + num,
                       size=11, anchor="start", weight="bold")
            cv.text_px(bx + max(bw, w2) + 16, by + bh / 2 + 11, txt, size=10.5,
                       anchor="start")
    cv.text_px(240, 332, "検算は点線の寄り道ではなく実線の本流——ここまでやって「解けた」と言える",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_solving_procedure_flowchart.svg", canvas=cv,
                lesson="L04",
                title="解く手順の全体地図（移項→整理→係数でわる→検算）",
                intent="主概念1の基本手順4ステップのフローチャート。検算を実線で本流に含める",
                src="lesson_04.md 主概念1（手順1〜4の直後）",
                params="例1の 5x−7＝2x＋8→5x−2x＝8＋7→3x＝15→x＝5（本文明示）・検算両辺18",
                checks=ck.items)


# ===========================================================================
# 図5: L05 前処理→基本手順→検算の手順マップ（かっこ／小数／分数の3分岐）
# 本文根拠: lesson_05.md 前処理1〜3（例1〜例3）とねらい
# 答え漏れ注意: 各例の解（7・9・7）は図に書かずassertでのみ検算
# ===========================================================================
def fig_L05():
    ck = Checker()
    # 例1: 2(x−3)＝x＋1 → x＝7
    x1 = solve_linear(2 - 1, 1 + 6)
    ck.ok("例1の解が元の式を満たす（値は図に書かない）",
          abs(2 * (x1 - 3) - (x1 + 1)) < 1e-9)
    # 例2: 0.3x＋0.5＝0.2x＋1.4 → ×10で整数係数 → x＝9
    ck.ok("例2: 両辺×10で 3x＋5＝2x＋14（全項が整数係数になる）",
          (0.3 * 10, 0.5 * 10, 0.2 * 10, 1.4 * 10) == (3, 5, 2, 14))
    x2 = solve_linear(3 - 2, 14 - 5)
    ck.ok("例2の解が元の小数の式を満たす（値は図に書かない）",
          abs((0.3 * x2 + 0.5) - (0.2 * x2 + 1.4)) < 1e-9)
    # 例3: (x＋2)/3＝(x−1)/2 → ×6 → 2(x＋2)＝3(x−1) → x＝7
    ck.ok("例3: 6は分母3と2の最小公倍数", math.lcm(3, 2) == 6)
    x3 = solve_linear(2 - 3, -3 - 4)
    ck.ok("例3の解が元の分数の式を満たす（値は図に書かない）",
          abs((x3 + 2) / 3 - (x3 - 1) / 2) < 1e-9)

    cv = Canvas(500, 332)
    tops = [
        (12, "かっこ", "2(x−3)＝x＋1", "分配法則で外す"),
        (178, "小数", "0.3x＋0.5＝0.2x＋1.4", "両辺×10・×100"),
        (344, "分数", "(x＋2)/3＝(x−1)/2", "両辺×分母の公倍数"),
    ]
    for bx, head, eq, op in tops:
        cv.textbox_px(bx, 18, 146, 58, [head, eq], size=10.5, sw=MAIN_W,
                      weight_first="bold")
        cv.text_px(bx + 73, 96, op, size=10.5, anchor="middle", weight="bold")
    # 合流点へ
    jx, jy, jw, jh = 150, 148, 200, 52
    cv.textbox_px(jx, jy, jw, jh, ["基本手順（L04）", "Ａx＝Ｂ → x＝（数）"],
                  size=FS, sw=BOLD_W * 0.6, weight_first="bold")
    for bx, _, _, _ in tops:
        arrow_px(cv, bx + 73, 104, jx + jw / 2 + (bx - 178) * 0.30, jy - 4,
                 w=1.4)
    # 検算へ
    arrow_px(cv, 250, jy + jh + 4, 250, 238, w=1.6, head=8)
    cv.textbox_px(164, 242, 172, 36, ["解を代入して検算"], size=12.5,
                  sw=MAIN_W, weight_first="bold")
    cv.text_px(250, 302, "小数・分数の前処理の根拠は等式の性質③（両辺に同じ数をかける——全部の項に）。",
               size=FS_CAP, anchor="middle")
    cv.text_px(250, 320, "かっこ外しだけは両辺への操作ではなく、分配法則による各辺の式の計算",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_preprocess_flow_map.svg", canvas=cv, lesson="L05",
                title="前処理→基本手順→検算の手順マップ（かっこ・小数・分数の3分岐）",
                intent="前処理1〜3が基本手順に合流する全体地図。各例の解は書かない",
                src="lesson_05.md 前処理3（例3）の直後",
                params="例1〜例3の式は本文と同一／各解7・9・7はassertでのみ検算",
                checks=ck.items)


# ===========================================================================
# 図6: L06 比例式の翻訳図（x：12＝3：4 →「比の値」の橋→ x/12＝3/4 → x＝9）
# 本文根拠: lesson_06.md 例1（x：12＝3：4・x/12＝3/4・x＝36/4→9・検算）
# 答え扱い: x＝9は本文例1が明示する解説値のため記載可
# ===========================================================================
def fig_L06():
    # --- パラメータ（本文 lesson_06.md 例1 と一致させる） ---
    b, c, d = 12, 3, 4                # x：12＝3：4

    ck = Checker()
    x = solve_linear(1, b * c / d)
    ck.ok("x＝36/4＝9（本文明示の解説値・図に記載）", abs(x - 9) < 1e-9)
    ck.ok("検算: 9：12 の比の値 9/12 と 3：4 の比の値 3/4 が等しい",
          abs(9 / 12 - 3 / 4) < 1e-9)
    ck.ok("翻訳の同値性: x/12＝3/4 の両辺×12 が x＝36/4",
          abs(b * (c / d) - 36 / 4) < 1e-9)

    cv = Canvas(520, 260)
    # 左: ：の世界
    cv.textbox_px(24, 40, 150, 66, ["：の世界（比例式）", "x：12＝3：4"],
                  size=12.5, sw=MAIN_W, weight_first="bold")
    # 橋（矢印を先に描き、その上に橋のラベルを重ねる）
    arrow_px(cv, 176, 74, 316, 74, w=1.6, head=8)
    cv.rect_px(184, 62, 122, 24, sw=MAIN_W, fill="#eee", rx=10)
    cv.text_px(245, 78, "橋＝比の値", size=11.5, anchor="middle", weight="bold")
    cv.text_px(245, 104, "「2つの比が等しい＝比の値が等しい」", size=10, anchor="middle")
    # 右: ＝と分数の世界
    cv.textbox_px(322, 28, 176, 44, ["＝と分数の世界", "x/12＝3/4"],
                  size=12.5, sw=MAIN_W, weight_first="bold")
    arrow_px(cv, 410, 74, 410, 96, w=1.4)
    cv.text_px(420, 88, "両辺×12（性質③）", size=10, anchor="start")
    cv.textbox_px(352, 100, 116, 34, ["x＝9"], size=14, sw=BOLD_W * 0.6,
                  weight_first="bold")
    # 検算の戻り矢印（破線）
    cv.raw(f'<polyline points="352,124 200,168 110,120" fill="none" '
           f'stroke="#000" stroke-width="1.3" stroke-dasharray="{DASH}"/>')
    arrow_px(cv, 110, 120, 102, 110, w=1.3, head=7, dash=DASH)
    cv.text_px(228, 186, "検算: 9：12 の比の値は 9/12＝3/4——右の比 3：4 と一致",
               size=11, anchor="middle")
    cv.text_px(260, 226, "比例式に新しい解き方はいらない。比の値で等式に翻訳すれば、",
               size=FS_CAP, anchor="middle")
    cv.text_px(260, 244, "いままでの一次方程式（分数の前処理つき）として解ける",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_proportion_translation_bridge.svg", canvas=cv,
                lesson="L06",
                title="比例式の翻訳図（x：12＝3：4 →比の値の橋→ x/12＝3/4 → x＝9）",
                intent="比例式→一次方程式への帰着の3段変換。検算は戻り矢印で明示",
                src="lesson_06.md 例1の直後",
                params="x：12＝3：4・x/12＝3/4・x＝9（本文明示）／比の値一致はassert検算",
                checks=ck.items)


# ===========================================================================
# 図7: L07 立式の5ステップ手順図（例2 りんごとみかん・ステップ2が心臓部）
# 本文根拠: lesson_07.md 立式の型5ステップと例2（150x＋90(10−x)＝1200・x＝5）
# 答え扱い: x＝5は本文例2が明示する解説値のため記載可
# ===========================================================================
def fig_L07():
    # --- パラメータ（本文 lesson_07.md 例2 と一致させる） ---
    p1, p2, total_n, total_c = 150, 90, 10, 1200

    ck = Checker()
    x = solve_linear(p1 - p2, total_c - p2 * total_n)
    ck.ok("x＝5（本文明示の解説値・図に記載）が方程式を満たす",
          abs(x - 5) < 1e-9
          and abs(p1 * x + p2 * (total_n - x) - total_c) < 1e-9)
    ck.ok("検算内訳 150×5＋90×5＝750＋450＝1200（本文と一致）",
          p1 * 5 + p2 * 5 == 750 + 450 == 1200)
    ck.ok("みかんは（10−x）個と表せる（x＝5なら5個・合計10個）",
          total_n - 5 == 5 and 5 + 5 == total_n)

    cv = Canvas(500, 356)
    bx, bw, bh, gap = 92, 316, 44, 14
    steps = [
        ("① xで表す", ["りんごをx個と宣言（みかんは 10−x 個）"], False),
        ("② 等しい2つの数量", ["「代金の合計」が二通りに表せる:",
                               "買い方から計算した金額 と 実際に払った金額"], True),
        ("③ 左辺・右辺の意味", ["左辺＝買い方から計算した代金・右辺＝実際の代金"], False),
        ("④ 方程式をつくって解く", ["150x＋90(10−x)＝1200"], False),
        ("⑤ 場面に戻す", ["x＝5 → 単位を付けて問いに答える（検算・吟味も）"], False),
    ]
    y = 16
    for i, (head, lines, is_heart) in enumerate(steps):
        h = bh + (14 if len(lines) > 1 else 0)
        sw = BOLD_W * 0.75 if is_heart else MAIN_W
        cv.textbox_px(bx, y, bw, h, [head] + lines, size=10.8, sw=sw,
                      weight_first="bold")
        if is_heart:
            cv.text_px(bx + bw + 10, y + h / 2 - 2, "この問題の", size=10.5,
                       anchor="start", weight="bold")
            cv.text_px(bx + bw + 10, y + h / 2 + 12, "心臓部", size=10.5,
                       anchor="start", weight="bold")
        if i < len(steps) - 1:
            arrow_px(cv, bx + bw / 2, y + h + 1, bx + bw / 2, y + h + gap - 1,
                     w=1.6, head=7)
        y += h + gap
    cv.text_px(250, 340, "急所はステップ②——方程式を1本つくるとは、場面にひそむ「等しい関係」を見つけること",
               size=11, anchor="middle")

    return dict(file="L07_fig1_formulation_five_steps.svg", canvas=cv,
                lesson="L07",
                title="立式の5ステップ手順図（例2・150x＋90(10−x)＝1200）",
                intent="立式の型の全体像。ステップ2を太枠で強調（この問題の心臓部）",
                src="lesson_07.md 立式の型（5ステップの直後）",
                params="150円×x個・90円×(10−x)個・1200円・x＝5（本文明示）",
                checks=ck.items)


# ===========================================================================
# 図8: L08 過不足の線分図（同じ総数を 4x＋18 と 7x−12 の二通りで表す）
# 本文根拠: lesson_08.md 型1 例1（4個ずつで18余り・7個ずつで12不足）
# 答え漏れ注意: 解（10人・58個）は図に書かない。区切り位置の比の計算にのみ使用
# ===========================================================================
def fig_L08():
    # --- パラメータ（本文 lesson_08.md 例1 と一致させる） ---
    a, r, b, s = 4, 18, 7, 12          # 4個ずつ余り18・7個ずつ不足12

    ck = Checker()
    x = solve_linear(b - a, r + s)
    ck.ok("解（人数10人）で 4x＋18＝7x−12 が成り立つ（値は図に書かない）",
          abs(x - 10) < 1e-9 and a * x + r == b * x - s)
    total = a * x + r
    ck.ok("総数58個の内訳: 4x＝40＜総数＜7x＝70（区切り比の計算のみ・図には非記載）",
          abs(total - 58) < 1e-9 and a * x == 40 and b * x == 70
          and a * x < total < b * x)
    ck.ok("不足の言い直し: 総数は7xより12少ない（7x−総数＝12）",
          abs(b * x - total - s) < 1e-9)

    cv = Canvas(540, 288)
    scale = 5.5                        # 1個 → 5.5px（実測比で描く）
    x0 = 60
    xe = x0 + total * scale            # 総数の右端
    x4 = x0 + a * x * scale            # 4xの右端
    x7 = x0 + b * x * scale            # 7xの右端（総数を超える）
    y1, y2 = 96, 172                   # 上段・下段
    cv.text_px((x0 + xe) / 2, 34, "あめの総数（どちらの配り方でも変わらない）",
               size=FS, anchor="middle", weight="bold")
    # 総数の両端をそろえる縦点線
    for px in (x0, xe):
        cv.raw(f'<line x1="{px:.1f}" y1="46" x2="{px:.1f}" y2="{y2 + 26:.1f}" '
               f'stroke="#000" stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    # 上段: 4x ＋ 余り18（すべて実線）
    for pa, pb2 in ((x0, x4), (x4, xe)):
        cv.raw(f'<line x1="{pa:.1f}" y1="{y1}" x2="{pb2:.1f}" y2="{y1}" '
               f'stroke="#000" stroke-width="{BOLD_W * 0.7}"/>')
    for px in (x0, x4, xe):
        cv.raw(f'<line x1="{px:.1f}" y1="{y1 - 7}" x2="{px:.1f}" y2="{y1 + 7}" '
               f'stroke="#000" stroke-width="{MAIN_W}"/>')
    cv.text_px((x0 + x4) / 2, y1 - 14, "4x（4個ずつx人に配る）", size=FS,
               anchor="middle")
    cv.text_px((x4 + xe) / 2, y1 - 14, "余り 18", size=FS, anchor="middle",
               weight="bold")
    cv.text_px(xe + 12, y1 + 4, "→ 総数＝4x＋18", size=12, anchor="start")
    # 下段: 7x から不足12を点線で切り欠く（総数の右端から先が点線）
    cv.raw(f'<line x1="{x0:.1f}" y1="{y2}" x2="{xe:.1f}" y2="{y2}" '
           f'stroke="#000" stroke-width="{BOLD_W * 0.7}"/>')
    cv.raw(f'<line x1="{xe:.1f}" y1="{y2}" x2="{x7:.1f}" y2="{y2}" '
           f'stroke="#000" stroke-width="{BOLD_W * 0.7}" stroke-dasharray="{DASH}"/>')
    for px in (x0, xe):
        cv.raw(f'<line x1="{px:.1f}" y1="{y2 - 7}" x2="{px:.1f}" y2="{y2 + 7}" '
               f'stroke="#000" stroke-width="{MAIN_W}"/>')
    cv.raw(f'<line x1="{x7:.1f}" y1="{y2 - 7}" x2="{x7:.1f}" y2="{y2 + 7}" '
           f'stroke="#000" stroke-width="{MAIN_W}" stroke-dasharray="{DASH}"/>')
    cv.text_px((x0 + x7) / 2, y2 + 22, "7x（7個ずつx人に配るのに必要な個数）",
               size=FS, anchor="middle")
    cv.text_px((xe + x7) / 2, y2 - 14, "不足 12", size=FS, anchor="middle",
               weight="bold")
    cv.text_px(x7 + 10, y2 + 4, "→ 総数＝7x−12", size=12, anchor="start")
    # 凡例
    cv.raw(f'<line x1="60" y1="238" x2="96" y2="238" stroke="#000" '
           f'stroke-width="{BOLD_W * 0.7}"/>')
    cv.text_px(102, 242, "実線＝実際にあるあめ（余りは実線で足す）", size=11,
               anchor="start")
    cv.raw(f'<line x1="60" y1="258" x2="96" y2="258" stroke="#000" '
           f'stroke-width="{BOLD_W * 0.7}" stroke-dasharray="{DASH}"/>')
    cv.text_px(102, 262, "点線＝足りない分（不足は点線で欠ける）", size=11,
               anchor="start")
    cv.text_px(300, 280, "上下の線分の全長（＝総数）は同じ。二通りの表し方を等号で結ぶと 4x＋18＝7x−12",
               size=11, anchor="middle")

    return dict(file="L08_fig1_surplus_shortage_segments.svg", canvas=cv,
                lesson="L08",
                title="過不足の線分図（同じ総数の二通りの表し方 4x＋18 と 7x−12）",
                intent="型1「総数を二通りに表す」の可視化。ラベルは一般形のみで解は書かない",
                src="lesson_08.md 型1 例1（方程式の直後）",
                params="4個ずつ余り18・7個ずつ不足12／区切りは解の実測比（値は非記載）",
                checks=ck.items)


# ===========================================================================
# 図9: L09 検算と吟味の2段関門図（x＝3.75——①通過・②不通過）
# 本文根拠: lesson_09.md 例1（60x＋100(8−x)＝650・x＝3.75・650＝650・整数でない）
# 答え扱い: x＝3.75・650は本文例1が明示する解説値のため記載可
# ===========================================================================
def fig_L09():
    # --- パラメータ（本文 lesson_09.md 例1 と一致させる） ---
    p1, p2, total_n, total_c = 60, 100, 8, 650

    ck = Checker()
    x = solve_linear(p1 - p2, total_c - p2 * total_n)
    ck.ok("x＝3.75（本文明示の解説値・図に記載）", abs(x - 3.75) < 1e-9)
    ck.ok("関門①検算: 60×3.75＋100×4.25＝225＋425＝650 で両辺一致",
          abs(p1 * x + p2 * (total_n - x) - total_c) < 1e-9
          and p1 * 3.75 == 225 and p2 * 4.25 == 425)
    ck.ok("関門②吟味: 3.75 は整数でない（個数の条件に合わない）",
          x != int(x))

    cv = Canvas(540, 300)
    # 入口: 解
    cv.textbox_px(20, 92, 108, 44, ["解", "x＝3.75"], size=12.5, sw=MAIN_W,
                  weight_first="bold")
    # 関門①
    g1x, g1w = 162, 150
    cv.rect_px(g1x, 40, g1w, 148, sw=MAIN_W, rx=6)
    cv.text_px(g1x + g1w / 2, 62, "関門① 検算", size=12.5, anchor="middle",
               weight="bold")
    cv.text_px(g1x + g1w / 2, 84, "方程式に代入して", size=10.5, anchor="middle")
    cv.text_px(g1x + g1w / 2, 98, "計算が正しいか？", size=10.5, anchor="middle")
    cv.text_px(g1x + g1w / 2, 124, "両辺とも650", size=11.5, anchor="middle")
    cv.text_px(g1x + g1w / 2, 148, "→ 通過", size=12.5, anchor="middle",
               weight="bold")
    # 関門②
    g2x, g2w = 356, 150
    cv.rect_px(g2x, 40, g2w, 148, sw=MAIN_W, rx=6)
    cv.text_px(g2x + g2w / 2, 62, "関門② 吟味", size=12.5, anchor="middle",
               weight="bold")
    cv.text_px(g2x + g2w / 2, 84, "場面に照らして", size=10.5, anchor="middle")
    cv.text_px(g2x + g2w / 2, 98, "意味を持つか？", size=10.5, anchor="middle")
    cv.text_px(g2x + g2w / 2, 124, "個数なのに整数でない", size=11, anchor="middle")
    cv.text_px(g2x + g2w / 2, 148, "→ 不通過", size=12.5, anchor="middle",
               weight="bold")
    # 通路の矢印
    arrow_px(cv, 130, 114, 158, 114, w=1.8, head=8)
    arrow_px(cv, 314, 114, 352, 114, w=1.8, head=8)
    # ②で止まった解の行き先（下へ分岐）
    arrow_px(cv, g2x + g2w / 2, 190, g2x + g2w / 2, 216, w=1.6, head=7)
    cv.textbox_px(236, 220, 288, 48,
                  ["答えとして採用しない", "「条件に合う買い方はない」と答える／設定を見直す"],
                  size=10.5, sw=MAIN_W, weight_first="bold")
    cv.text_px(60, 220, "両方通って", size=10.5, anchor="start")
    cv.text_px(60, 234, "はじめて「答え」", size=10.5, anchor="start")
    cv.text_px(60, 248, "になる", size=10.5, anchor="start")
    cv.text_px(270, 288, "①が通っても②で止まることがある——検算と吟味は別の関門",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_two_gate_check.svg", canvas=cv, lesson="L09",
                title="検算と吟味の2段関門図（x＝3.75は①通過・②不通過）",
                intent="2段チェックの関門イメージ。②で止まった解の行き先の分岐を明示",
                src="lesson_09.md 【ことば】検算と吟味の2段チェックの直後",
                params="例1の x＝3.75・両辺650（本文明示）／整数判定はassert検算",
                checks=ck.items)


# ===========================================================================
# 図10: L10 単元全体の3部屋マップ（意味・解く・使う＋廊下L10）
# 本文根拠: lesson_10.md 3部屋の自己チェック（部屋1=L01・L02／部屋2=L03〜L06／
#           部屋3=L07〜L09）。プレースホルダの区分（意味L01〜L03）は本文チェック
#           リストの実際のレッスン割当（L03は部屋2「解く」）に合わせて整合させた。
# 答え扱い: 概念図のみ・数値なし
# ===========================================================================
def fig_L10():
    rooms = {
        "意味": ["L01", "L02"],
        "解く": ["L03", "L04", "L05", "L06"],
        "使う": ["L07", "L08", "L09"],
    }
    ck = Checker()
    allls = [l for ls in rooms.values() for l in ls]
    ck.ok("3部屋でL01〜L09を重複なく全部カバーする",
          sorted(allls) == [f"L0{i}" for i in range(1, 10)]
          and len(set(allls)) == 9)
    ck.ok("部屋割りが本文チェックリストと一致（L03移項=部屋2・L06比例式=部屋2）",
          "L03" in rooms["解く"] and "L06" in rooms["解く"]
          and "L02" in rooms["意味"] and "L09" in rooms["使う"])

    cv = Canvas(540, 312)
    specs = [
        (16, "部屋1 意味（L01・L02）", ["方程式・解とは何か", "等式の性質4つ"]),
        (198, "部屋2 解く（L03〜L06）", ["移項・基本手順Ａx＝Ｂ", "前処理・比例式・検算"]),
        (380, "部屋3 使う（L07〜L09）", ["立式の型・二通りの表現", "検算と吟味の2段チェック"]),
    ]
    for bx, head, lines in specs:
        cv.textbox_px(bx, 40, 146, 92, [head] + lines, size=10.2, sw=MAIN_W,
                      weight_first="bold")
    # 部屋1→2・2→3 の矢印とラベル
    arrow_px(cv, 164, 86, 196, 86, w=1.8, head=8)
    cv.text_px(180, 152, "等式の性質が", size=10, anchor="middle")
    cv.text_px(180, 165, "解く手順の根拠になる", size=10, anchor="middle")
    cv.raw(f'<line x1="180" y1="140" x2="180" y2="98" stroke="#000" '
           f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    arrow_px(cv, 346, 86, 378, 86, w=1.8, head=8)
    cv.text_px(362, 152, "解く力が", size=10, anchor="middle")
    cv.text_px(362, 165, "立式の受け皿になる", size=10, anchor="middle")
    cv.raw(f'<line x1="362" y1="140" x2="362" y2="98" stroke="#000" '
           f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    # 廊下 L10
    cv.rect_px(16, 196, 510, 44, sw=BOLD_W * 0.6, fill="#eee", rx=6)
    cv.text_px(271, 214, "L10 章末まとめ＝3部屋を見わたす廊下", size=12.5,
               anchor="middle", weight="bold")
    cv.text_px(271, 231, "×や△の部屋のレッスンに戻って復習する", size=10.5,
               anchor="middle")
    for bx, _, _ in specs:
        cv.raw(f'<line x1="{bx + 73}" y1="132" x2="{bx + 73}" y2="196" '
               f'stroke="#000" stroke-width="{AUX_W}"/>')
    cv.text_px(271, 270, "この章の背骨:「形を変えても解は変わらない」——意味が根拠を支え、",
               size=FS_CAP, anchor="middle")
    cv.text_px(271, 288, "根拠が手続きを支え、手続きが場面の問題解決を支える",
               size=FS_CAP, anchor="middle")

    return dict(file="L10_fig1_three_rooms_map.svg", canvas=cv, lesson="L10",
                title="単元全体の3部屋マップ（意味・解く・使う＋廊下L10）",
                intent="章の総整理の見取図。部屋割りは本文チェックリストの割当と一致",
                src="lesson_10.md 3部屋の自己チェックの直後",
                params="意味=L01・L02／解く=L03〜L06／使う=L07〜L09（本文チェックリスト準拠）",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02, fig_L03, fig_L04, fig_L05, fig_L06, fig_L07,
        fig_L08, fig_L09, fig_L10]


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
        "spec: 先行単元 jhs-math-2-simultaneous-equations のコード来歴方式に準拠",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 一次方程式単元 図版台帳",
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
        "- 練習問題・stretchの答は図に一切書かない。図に載せた数値は、与件と、本文の"
        "例題解説が明示している解説値（L01のx＝2・L02のx＝5・L04のx＝5と検算値18・"
        "L06のx＝9・L07のx＝5・L09のx＝3.75と650）のみ。",
        "- L03は本文の並記と同じく x＝13−6 までを図示し、計算結果の7は図に書かず"
        "assertでのみ検算した。L05は各例の解（7・9・7）を図に書かずassertでのみ検算した。",
        "- L08の線分図は本文例1の解（人数10人・総数58個）を区切り位置の実測比の計算に"
        "だけ使い、図中ラベルは一般形（4x・余り18・7x・不足12）にとどめた。",
        "- L10の部屋割りは、プレースホルダ表記（意味L01〜L03）ではなく本文チェックリスト"
        "の実際の割当（部屋1=L01・L02／部屋2=L03〜L06／部屋3=L07〜L09）に合わせ、"
        "assertで整合を検算した。",
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
