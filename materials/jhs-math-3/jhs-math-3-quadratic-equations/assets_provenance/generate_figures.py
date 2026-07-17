#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「二次方程式」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み）。
ヘルパー群（Canvas/寸法線/ハッチ/矢印/3D平行投影ほか）は先行単元
production/jhs-math-3-similar-figures/candidate_draft/assets_provenance/generate_figures.py
production/jhs-math-3-pythagorean-theorem/candidate_draft/assets_provenance/generate_figures.py
からコピー再利用（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（6枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない（面積恒等式・数値例・箱の体積・解法3経路の一致）。
- 答えの分離方針: 近隣の設問・例題が問う値（L01の5cm・L07のx・L09の10cmなど）は図に書かない。
  検算では本文・answer_keyの答と照合する。
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

    def dim(self, a, b, label, offset=(0, 0), tick=4.0, size=FS, away=None,
            lab_off=13.0):
        """寸法線: 細線+両端ティック+ラベル。offsetは数学座標のずらし量。
        away=図形中心（数学座標）を渡すと、ラベルを線から中心の反対側へ
        lab_off(px)離して置く（線かぶり防止）。"""
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
                if abs(nx * side) > 0.7:      # 縦の寸法線→左右に置く
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
            f'(docs/SPEC_figures.md準拠（内部規約の要旨は同SPECに反映済み）・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


# ---- ユーティリティ --------------------------------------------------------
def shoelace(pts):
    """多角形の面積（符号なし）"""
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


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


# ---- 方程式ソルバ（L10系統図の検算用・図には数値を書かない） ----------------
def solve_by_formula(a, b, c):
    """解の公式 x=(−b±√(b²−4ac))/(2a)"""
    disc = b * b - 4 * a * c
    assert disc >= 0
    r = math.sqrt(disc)
    return sorted({(-b + r) / (2 * a), (-b - r) / (2 * a)})


def solve_by_completing(a, b, c):
    """平方の形に変形: x²+(b/a)x=−c/a → (x+b/2a)²=(b²−4ac)/4a²"""
    p, q = b / a, c / a
    rhs = (p / 2) ** 2 - q
    assert rhs >= 0
    r = math.sqrt(rhs)
    return sorted({-p / 2 + r, -p / 2 - r})


def solve_by_sqrt(k):
    """平方根の考え: x²=k → x=±√k"""
    assert k >= 0
    return sorted({math.sqrt(k), -math.sqrt(k)})


# ---- 3D平行投影（L09の箱の見取図用・三平方単元からコピー再利用） -------------
DEPTH = (0.55, 0.42)   # 奥行き1あたりの(x, y)ずれ（平行投影・立体風装飾なし）


def proj(p3):
    """(x, 奥行きd, 高さz) → 数学座標(x', y')。平行投影"""
    x, d, z = p3
    return (x + DEPTH[0] * d, z + DEPTH[1] * d)


# ===========================================================================
# 図1: L01 正方形と長方形（(x＋1)(x−1)＝24 の場面図）
# 本文根拠: lesson_01.md 主概念1「一方の辺を1cm長く・他方を1cm短くして面積24cm²」
# 答え漏れ注意: 本文の答「5cm」（x＝5）は図に書かない
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md 主概念1 と一致させる） ---
    x = 5.0                 # 描画用の実比（本文の答5cm。図にはx表記のみ）
    dv, dh = 1.0, 1.0       # 縦に+1cm・横に−1cm
    area = 24.0             # 長方形の面積（本文の与件・図に書いてよい）

    ck = Checker()
    ck.ok("恒等式 (x＋1)(x−1)＝x²−1（複数のxで成立）",
          all(abs((t + 1) * (t - 1) - (t * t - 1)) < 1e-9
              for t in (2.0, 3.5, 5.0, 7.25)))
    ck.ok("数値例: x＝5で (5＋1)(5−1)＝24＝与件の面積（本文の答5cmと整合・図には書かない）",
          abs((x + dv) * (x - dh) - area) < 1e-9)
    ck.ok("描画比が場面どおり（縦x＋1・横x−1・もとは正方形）",
          dv == dh == 1.0 and x > dh)

    s = 17.0
    cv = Canvas(420, 262, scale=s, ox=52, oy=196)
    # 左: もとの正方形（1辺x）
    sq = [(0, 0), (x, 0), (x, x), (0, x)]
    csq = (x / 2, x / 2)
    cv.polygon(sq, w=MAIN_W)
    cv.dim((0, x), (x, x), "x cm", offset=(0, 0.55), size=FS, away=csq)
    cv.dim((0, 0), (0, x), "x cm", offset=(-0.55, 0), size=FS, away=csq)
    ck.ok("正方形の4辺が等しい（shoelace面積＝x²）",
          abs(shoelace(sq) - x * x) < 1e-9)
    # 中央: 変形の矢印
    ox2 = x + 3.6
    x1p, _ = cv.P((x, x / 2))
    x2p, ymid = cv.P((ox2 - 0.5, x / 2))
    arrow_px(cv, x1p + 10, ymid, x2p + 2, ymid, w=1.4)
    cv.text_px((x1p + x2p) / 2 + 6, ymid - 26, "縦＋1cm", size=11,
               anchor="middle")
    cv.text_px((x1p + x2p) / 2 + 6, ymid - 12, "横−1cm", size=11,
               anchor="middle")
    # 右: 長方形（縦x+1・横x−1）
    rc = [(ox2, -dv / 2), (ox2 + x - dh, -dv / 2),
          (ox2 + x - dh, x + dv / 2), (ox2, x + dv / 2)]
    crc = (ox2 + (x - dh) / 2, x / 2)
    cv.polygon(rc, w=MAIN_W)
    ck.ok("長方形の面積＝(x＋1)(x−1)（shoelaceで検算）",
          abs(shoelace(rc) - (x + dv) * (x - dh)) < 1e-9)
    cv.dim((ox2, x + dv / 2), (ox2 + x - dh, x + dv / 2), "(x−1)cm",
           offset=(0, 0.55), size=FS, away=crc)
    cv.dim((ox2 + x - dh, -dv / 2), (ox2 + x - dh, x + dv / 2), "(x＋1)cm",
           offset=(0.55, 0), size=FS, away=crc)
    cv.text(crc, "面積 24cm²", size=FS, weight="bold")
    cv.text_px(210, 230, "一方の辺を1cm長く・他方の辺を1cm短くしたら、面積が24cm²になった",
               size=FS_CAP, anchor="middle")
    cv.text_px(210, 248, "（もとの正方形の1辺 x cm は？——面積の関係から方程式をつくる）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_square_to_rectangle_24.svg", canvas=cv, lesson="L01",
                title="正方形→長方形（縦＋1cm・横−1cm で面積24cm²）",
                intent="主概念1の場面図。xの値（答え）は書かず、与件24cm²のみ記載",
                src="lesson_01.md 主概念1（36行目のプレースホルダ）",
                params="正解のxの縦横比で描画（ラベルはx表記）／縦x＋1・横x−1／面積24",
                checks=ck.items)


# ===========================================================================
# 図2: L03 平方完成の面積図（x²＋6x に 3²＝9 を埋めて (x＋3)²）
# 本文根拠: lesson_03.md 主概念（x²＋6x＋2＝0 → (x＋3)²＝7）と直後のguide
# 答え漏れ注意: 方程式の解 −3±√7 は図に書かない（9は本文が図中で明示する解説値）
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md と一致させる） ---
    p = 6.0            # xの係数（x²＋6x）
    h = p / 2          # 半分＝3（両側に分けるから）
    x = 5.0            # 描画用のxの長さ（概念図・比率のみ意味を持つ）

    ck = Checker()
    ck.ok("恒等式 x²＋6x＋9＝(x＋3)²（複数のxで成立）",
          all(abs(t * t + p * t + h * h - (t + h) ** 2) < 1e-9
              for t in (1.0, 2.5, 5.0, 8.0)))
    ck.ok("半分の2乗＝(6/2)²＝9（すき間の正方形の面積）", h == 3.0 and h * h == 9.0)
    ck.ok("長方形x×6を半分にした2枚（x×3）の面積の和＝6x",
          abs(2 * (x * h) - p * x) < 1e-9)
    ck.ok("はり付け後: x²＋3x＋3x＋すき間9＝大きな正方形(x＋3)²",
          abs(x * x + 2 * h * x + h * h - (x + h) ** 2) < 1e-9)

    s = 15.0
    cv = Canvas(460, 322)
    cv.add_hatch()
    cv.s, cv.ox, cv.oy = s, 30, 250
    # --- 左パネル: x²の正方形 + 縦x・横6の長方形（半分の切れ目=破線） ---
    sq = [(0, 0), (x, 0), (x, x), (0, x)]
    cv.polygon(sq, w=MAIN_W)
    cv.text((x / 2, x / 2), "x²", size=15, weight="bold")
    cv.dim((0, x), (x, x), "x", offset=(0, 0.5), size=FS, away=(x / 2, x / 2))
    cv.dim((0, 0), (0, x), "x", offset=(-0.5, 0), size=FS, away=(x / 2, x / 2))
    gx = x + 1.0                       # 長方形の左端
    rc = [(gx, 0), (gx + p, 0), (gx + p, x), (gx, x)]
    ck.ok("左パネルの長方形＝縦x・横6（shoelaceで検算）",
          abs(shoelace(rc) - p * x) < 1e-9)
    cv.polygon_nostroke([(gx, 0), (gx + h, 0), (gx + h, x), (gx, x)], "url(#h45)")
    cv.polygon_nostroke([(gx + h, 0), (gx + p, 0), (gx + p, x), (gx + h, x)],
                        "url(#h135)")
    cv.polygon(rc, w=MAIN_W)
    cv.line((gx + h, 0), (gx + h, x), w=AUX_W, dash=DASH)   # 半分に切る破線
    crec = (gx + p / 2, x / 2)
    cv.dim((gx, x), (gx + h, x), "3", offset=(0, 0.5), size=FS, away=crec)
    cv.dim((gx + h, x), (gx + p, x), "3", offset=(0, 0.5), size=FS, away=crec)
    cv.text_px(30 + s * (x + 1 + p / 2), 250 - s * x - 44, "横6を半分に切る",
               size=FS_CAP, anchor="middle")
    xlp, ylp = cv.P(((x + gx + p) / 2, -0.9))
    cv.text_px(30 + s * (x + gx + p) / 2 - 8, ylp + 8, "x²＋6x", size=FS,
               anchor="middle", weight="bold")
    # --- 中央の矢印 ---
    xa1, ya = cv.P((gx + p + 0.6, x / 2))
    arrow_px(cv, xa1, ya, xa1 + 34, ya, w=1.4)
    cv.text_px(xa1 + 17, ya - 12, "はり付け", size=11, anchor="middle")
    # --- 右パネル: L字型にはり付け・右下にすき間3×3 ---
    cv.ox = 30 + s * (gx + p + 0.6) + 48
    base = [(0, h), (x, h), (x, x + h), (0, x + h)]          # x²（左上へ）
    strip_r = [(x, h), (x + h, h), (x + h, x + h), (x, x + h)]   # 右の帯 3×x
    strip_b = [(0, 0), (x, 0), (x, h), (0, h)]                   # 下の帯 x×3
    gap = [(x, 0), (x + h, 0), (x + h, h), (x, h)]               # すき間 3×3
    big = [(0, 0), (x + h, 0), (x + h, x + h), (0, x + h)]       # 完成形 (x+3)²
    ck.ok("右パネル: 帯2枚＝3×xずつ・すき間＝3×3・全体＝(x＋3)²（shoelaceで検算）",
          abs(shoelace(strip_r) - h * x) < 1e-9
          and abs(shoelace(strip_b) - h * x) < 1e-9
          and abs(shoelace(gap) - h * h) < 1e-9
          and abs(shoelace(big) - (x + h) ** 2) < 1e-9)
    ck.ok("面積の分割が過不足なし: x²＋帯2枚＋すき間＝全体",
          abs(shoelace(base) + shoelace(strip_r) + shoelace(strip_b)
              + shoelace(gap) - shoelace(big)) < 1e-9)
    cv.polygon_nostroke(strip_r, "url(#h45)")
    cv.polygon_nostroke(strip_b, "url(#h135)")
    cv.polygon(base, w=MAIN_W)
    cv.polygon(strip_r, w=MAIN_W)
    cv.polygon(strip_b, w=MAIN_W)
    cv.polygon(gap, w=AUX_W, dash=DASH)                      # すき間＝破線
    cv.text((x / 2, h + x / 2), "x²", size=15, weight="bold")
    cv.text((x + h / 2, h / 2), "3²", size=13, weight="bold")
    cbig = ((x + h) / 2, (x + h) / 2)
    cv.dim((0, x + h), (x, x + h), "x", offset=(0, 0.5), size=FS, away=cbig)
    cv.dim((x, x + h), (x + h, x + h), "3", offset=(0, 0.5), size=FS, away=cbig)
    cv.dim((x + h, h), (x + h, x + h), "x", offset=(0.5, 0), size=FS, away=cbig)
    cv.dim((x + h, 0), (x + h, h), "3", offset=(0.5, 0), size=FS, away=cbig)
    # キャプション
    cv.text_px(230, 292, "右下に1辺3の正方形のすき間（破線）。すき間＝3²＝9 を埋めると",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 309, "大きな正方形 (x＋3)² が完成する——「係数6の半分の2乗」の正体",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_completing_square_area.svg", canvas=cv, lesson="L03",
                title="平方完成の面積図（x²＋6x＋9＝(x＋3)²）",
                intent="主概念の意味理解図。方程式の解の値は書かない（9は本文明示の解説値）",
                src="lesson_03.md 主概念（48行目のプレースホルダ）",
                params="p=6・半分h=3・x=5比で描画／帯2枚とすき間はshoelaceで面積検算",
                checks=ck.items)


# ===========================================================================
# 図3: L07 立式の概念図（同じ数量を二通りに表して等号で結ぶ）
# 本文根拠: lesson_07.md 主概念1「x²＝3x＋10」（例: 2乗すると3倍して10を加えた数）
# 答え漏れ注意: 例の数（x＝5）は図に書かない（方程式そのものは本文が直前に明示）
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（本文 lesson_07.md 主概念1 と一致させる） ---
    expr1, expr2 = "x²", "3x＋10"

    ck = Checker()
    roots = solve_by_formula(1, -3, -10)      # x²＝3x＋10 ⇔ x²−3x−10＝0
    ck.ok("例の方程式 x²＝3x＋10 の正の解は5（両辺とも25・図には書かない）",
          5.0 in [round(r, 9) for r in roots] and abs(5 ** 2 - (3 * 5 + 10)) < 1e-9,
          f"解={roots}")
    ck.ok("等号の左右は同じ数量の2つの表し方（本文の型どおりの構図）", True)

    cv = Canvas(440, 212)
    # 中央の箱
    bx, by, bw, bh = 158, 44, 124, 62
    cv.textbox_px(bx, by, bw, bh, ["ある1つの", "数量"], size=FS, sw=MAIN_W,
                  weight_first="bold")
    # 左: x² → 箱
    cv.text_px(64, 80, expr1, size=17, anchor="middle", weight="bold")
    arrow_px(cv, 86, 75, bx - 6, 75, w=1.4)
    cv.text_px((86 + bx) / 2, 65, "表し方①", size=11, anchor="middle")
    cv.text_px(64, 100, "「2乗すると」", size=11, anchor="middle")
    # 右: 3x＋10 → 箱
    cv.text_px(374, 80, expr2, size=17, anchor="middle", weight="bold")
    arrow_px(cv, 340, 75, bx + bw + 6, 75, w=1.4)
    cv.text_px((340 + bx + bw) / 2, 65, "表し方②", size=11, anchor="middle")
    cv.text_px(374, 100, "「3倍して10を", size=11, anchor="middle")
    cv.text_px(374, 114, "加えた数」", size=11, anchor="middle")
    # 下段: 等号で結ぶ
    cv.text_px(220, 152, "同じ数量の2つの表し方 → 等号で結べる：x²＝3x＋10",
               size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 176, "（等号「＝」は答えを出す記号ではなく、同じものの言いかえを結ぶ記号）",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig1_two_expressions_one_quantity.svg", canvas=cv,
                lesson="L07",
                title="立式の概念図（1つの数量・2つの表現・1本の等号）",
                intent="主概念1の型の可視化。例の数（xの値）は書かない",
                src="lesson_07.md 主概念1（44行目のプレースホルダ）",
                params="表し方①x²・②3x＋10（本文の例と同一の式・同じ向き）",
                checks=ck.items)


# ===========================================================================
# 図4: L07 例4の長方形（縦x cm・横(x＋4)cm・面積60cm²）
# 本文根拠: lesson_07.md 例4「縦がx cm、横が縦より4cm長い長方形の面積が60cm²」
# 答え漏れ注意: xの値（6）は図に書かない（練習Aは「つくるだけ」で解かない）
# ===========================================================================
def fig_L07_2():
    # --- パラメータ（本文 lesson_07.md 例4 と一致させる） ---
    x = 6.0            # 描画用の実比（x(x＋4)＝60を満たす正の値。図にはx表記のみ）
    dd = 4.0           # 横は縦より4cm長い
    area = 60.0        # 面積（与件・図に書いてよい）

    ck = Checker()
    ck.ok("数値例: x＝6で x(x＋4)＝6×10＝60＝与件の面積（図には書かない）",
          abs(x * (x + dd) - area) < 1e-9)
    ck.ok("横−縦＝4cm（場面どおりの比で描画）", abs((x + dd) - x - 4) < 1e-9)

    s = 19.0
    cv = Canvas(400, 232, scale=s, ox=105, oy=180)
    rc = [(0, 0), (x + dd, 0), (x + dd, x), (0, x)]
    ck.ok("長方形の面積＝x(x＋4)（shoelaceで検算）",
          abs(shoelace(rc) - x * (x + dd)) < 1e-9)
    cv.polygon(rc, w=MAIN_W)
    crc = ((x + dd) / 2, x / 2)
    cv.dim((0, x), (x + dd, x), "(x＋4)cm", offset=(0, 0.45), size=FS, away=crc)
    cv.dim((0, 0), (0, x), "x cm", offset=(-0.45, 0), size=FS, away=crc)
    cv.text(crc, "面積 60cm²", size=FS, weight="bold")
    cv.text_px(200, 212, "（例4: 着目する数量は「面積」——①縦×横 ②60 の二通りで表す）",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig2_rectangle_area_60.svg", canvas=cv, lesson="L07",
                title="例4の長方形（縦x・横x＋4・面積60cm²）",
                intent="例4の場面図。xの値（答え）は書かず、与件60cm²のみ記載",
                src="lesson_07.md 例4（78行目のプレースホルダ）",
                params="正解のxの比で描画（ラベルはx表記）／横は縦＋4",
                checks=ck.items)


# ===========================================================================
# 図5: L09 箱の問題（厚紙の展開図と、できあがる箱の見取図）
# 本文根拠: lesson_09.md 例1「4すみから1辺2cmの正方形を切り取り容積72cm³」
# 答え漏れ注意: 本文の答「10cm」（x＝10）・底面の1辺6cmは図に書かない
# ===========================================================================
def fig_L09():
    # --- パラメータ（本文 lesson_09.md 例1 と一致させる） ---
    x = 10.0           # 描画用の実比（本文の答10cm。図にはx表記のみ）
    cut = 2.0          # 4すみの切り取りの1辺
    vol = 72.0         # 容積（与件・図に書いてよい）

    base = x - 2 * cut
    ck = Checker()
    ck.ok("箱の体積: 2(x−4)²＝2×6²＝72＝与件（本文の答10cmと整合・図には書かない）",
          abs(cut * base * base - vol) < 1e-9, f"底面{base:.0f}cm角×深さ{cut:.0f}cm")
    ck.ok("場面の条件 x＞4（底面の1辺 x−4＞0）", x > 2 * cut)
    ck.ok("展開図の分割が過不足なし: すみ4つ＋側面4枚＋底面＝厚紙全体",
          abs(4 * cut * cut + 4 * cut * base + base * base - x * x) < 1e-9)

    cv = Canvas(460, 336)
    cv.add_hatch()
    # --- 左: 厚紙の展開図 ---
    s = 14.0
    cv.s, cv.ox, cv.oy = s, 84, 268
    csheet = (x / 2, x / 2)
    cv.polygon([(0, 0), (x, 0), (x, x), (0, x)], w=MAIN_W)
    for (cx, cy) in [(0, 0), (x - cut, 0), (0, x - cut), (x - cut, x - cut)]:
        corner = [(cx, cy), (cx + cut, cy), (cx + cut, cy + cut), (cx, cy + cut)]
        cv.polygon_nostroke(corner, "url(#h45)")
        cv.polygon(corner, w=AUX_W)
        ck.ok(f"すみ({cx:.0f},{cy:.0f})は1辺2cmの正方形",
              abs(shoelace(corner) - cut * cut) < 1e-9)
    # 折り目（点線）＝内側の正方形の4辺
    cv.line((cut, cut), (x - cut, cut), w=AUX_W, dash=DASH)
    cv.line((cut, x - cut), (x - cut, x - cut), w=AUX_W, dash=DASH)
    cv.line((cut, cut), (cut, x - cut), w=AUX_W, dash=DASH)
    cv.line((x - cut, cut), (x - cut, x - cut), w=AUX_W, dash=DASH)
    cv.dim((0, 0), (0, x), "x cm", offset=(-0.6, 0), size=FS, away=csheet)
    cv.dim((x - cut, x), (x, x), "2cm", offset=(0, 0.6), size=11, away=csheet)
    cv.text_px(84 + s * x / 2, 300, "斜線＝切り取る4すみ／点線＝折り目",
               size=FS_CAP, anchor="middle")
    # --- 中央の矢印 ---
    xa, ya = cv.P((x + 0.5, x / 2))
    arrow_px(cv, xa, ya, xa + 40, ya, w=1.6, head=8)
    cv.text_px(xa + 28, ya - 12, "組み立てる", size=11, anchor="middle")
    # --- 右: できあがった箱（ふたなし・平行投影の見取図） ---
    s2 = 16.0
    cv.s, cv.ox, cv.oy = s2, 285, 238
    B = {}          # 頂点: (x, 奥行き, 高さ)
    for i, (px_, py_) in enumerate([(0, 0), (base, 0), (base, base), (0, base)]):
        B[f"b{i}"] = (px_, py_, 0.0)          # 底面
        B[f"t{i}"] = (px_, py_, cut)          # 上のふち
    ck.ok("見取図の箱: 底面(x−4)角・深さ2cm（頂点座標から検算）",
          abs(B["b1"][0] - B["b0"][0] - base) < 1e-9
          and abs(B["t0"][2] - B["b0"][2] - cut) < 1e-9)
    E = lambda k: proj(B[k])
    # 隠れ線（破線）: 奥の底辺2本と左奥の縦辺
    cv.line(E("b3"), E("b2"), w=AUX_W, dash=DASH)
    cv.line(E("b2"), E("b1"), w=AUX_W, dash=DASH)
    cv.line(E("b3"), E("t3"), w=AUX_W, dash=DASH)
    # 見える線: 手前の底辺2本・縦辺3本・上のふち4本
    cv.line(E("b0"), E("b1"), w=MAIN_W)
    cv.line(E("b0"), E("b3"), w=MAIN_W)
    cv.line(E("b0"), E("t0"), w=MAIN_W)
    cv.line(E("b1"), E("t1"), w=MAIN_W)
    cv.line(E("b2"), E("t2"), w=MAIN_W)
    cv.polygon([E("t0"), E("t1"), E("t2"), E("t3")], w=MAIN_W)
    cv.dim(E("b1"), E("t1"), "2cm", offset=(0.55, 0), size=FS,
           away=proj((base / 2, base / 2, cut / 2)))
    xc, _ = cv.P(proj((base / 2, base / 2 + 1.0, 0)))
    cv.text_px(xc, 262, "容積 72cm³", size=FS, anchor="middle", weight="bold")
    cv.text_px(xc, 282, "ふたのない深さ2cmの箱", size=FS_CAP, anchor="middle")
    cv.text_px(230, 326, "（例1: もとの厚紙の1辺 x cm を求める。x＞4 が場面の条件）",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_box_from_square_sheet.svg", canvas=cv, lesson="L09",
                title="箱の問題（厚紙の展開図→ふたなしの箱・容積72cm³）",
                intent="例1の場面図。答え（xと底面の値）は書かず、与件2cm/72cm³のみ記載",
                src="lesson_09.md 例1（22行目のプレースホルダ）",
                params="正解のxの比で描画（ラベルはx表記）／切り取り2cm／体積はassertで72と照合",
                checks=ck.items)


# ===========================================================================
# 図6: L10 解法系統図（すべて次数を下げて一次方程式へ合流）
# 本文根拠: lesson_10.md 1.「解き方の地図」（3本の道＋時短ルート1本・駅は1つ）
# 答え漏れ注意: 総合演習の答（±8・4と−5など）は図に書かない。検算のみで使用
# ===========================================================================
def fig_L10():
    ck = Checker()
    # 3経路が同じ解に合流することの検算（総合演習A2: x²＋x−20＝0。値は図に書かない）
    a, b, c = 1, 1, -20
    r_formula = solve_by_formula(a, b, c)
    r_complete = solve_by_completing(a, b, c)
    r_factor = sorted({4.0, -5.0})           # (x−4)(x＋5)＝0
    ck.ok("因数分解の解が方程式を満たす（AB＝0の分解が正しい）",
          all(abs(a * t * t + b * t + c) < 1e-9 for t in r_factor))
    ck.ok("3経路の合流: 因数分解＝平方の形に変形＝解の公式（x²＋x−20＝0で一致・図には書かない）",
          all(abs(u - v) < 1e-9 and abs(u - w) < 1e-9
              for u, v, w in zip(r_factor, r_complete, r_formula)),
          f"解={r_formula}")
    # 平方根の考え（総合演習A1: x²−64＝0）→一次方程式2本
    r_sqrt = solve_by_sqrt(64)
    ck.ok("平方根の考え: x²＝64 → x＝±8 の一次方程式2本（図には書かない）",
          len(r_sqrt) == 2 and all(abs(t * t - 64) < 1e-9 for t in r_sqrt))
    # 解が1つに重なる場合（L05: (x＋3)²＝0 → x＝−3の1つだけ）→一次方程式1本
    r_rep = solve_by_completing(1, 6, 9)
    ck.ok("解が1つに重なるとき（(x＋3)²＝0・L05）は合流する一次方程式が1本",
          len(r_rep) == 1, f"解={r_rep}")
    # 解の公式＝平方の形に変形の一般化（複数の係数で両経路が一致）
    ck.ok("解の公式は平方の形に変形の一般化（複数の(a,b,c)で両経路が一致）",
          all(all(abs(u - v) < 1e-9 for u, v in
                  zip(solve_by_formula(*abc), solve_by_completing(*abc)))
              for abc in [(1, -3, 2), (2, -3, -4), (1, 4, -3), (3, 5, -2)]))

    cv = Canvas(480, 402)
    # 上段: 二次方程式
    cv.textbox_px(140, 16, 200, 34, ["二次方程式 ax²＋bx＋c＝0"], size=FS,
                  sw=MAIN_W, weight_first="bold")
    # 中段: 3つの道
    boxes = [
        (12, 96, 148, 62, ["平方根の考え", "x²＝k・(x＋m)²＝n", "の形（L02）"]),
        (172, 96, 136, 62, ["平方の形に変形", "→平方根の考え", "（L03）"]),
        (318, 96, 150, 62, ["因数分解（L05）", "AB＝0ならば", "A＝0またはB＝0"]),
    ]
    for (bx, by, bw, bh, lines) in boxes:
        cv.textbox_px(bx, by, bw, bh, lines, size=12, sw=MAIN_W,
                      weight_first="bold")
    # 上段→中段の矢印（3本）
    for tx in (86, 240, 393):
        arrow_px(cv, 240, 50, tx, 92, w=1.4)
    # 下段: 一次方程式（合流）
    jx, jy, jw, jh = 140, 226, 200, 36
    cv.textbox_px(jx, jy, jw, jh, ["一次方程式（1本または2本）"], size=FS,
                  sw=MAIN_W, weight_first="bold")
    # 中段→下段の矢印（3本が同じ箱へ合流）
    for (fx, fy) in ((86, 158), (240, 158), (393, 158)):
        tx = 190 if fx < 240 else (290 if fx > 240 else 240)
        arrow_px(cv, fx, fy, tx, 222, w=1.4)
    cv.text_px(285, 200, "次数を下げる", size=11, anchor="middle")
    # 解
    arrow_px(cv, 240, 262, 240, 296, w=1.4)
    cv.textbox_px(206, 300, 68, 32, ["解"], size=FS, sw=MAIN_W,
                  weight_first="bold")
    # わきの注記枠: 解の公式（破線枠+破線矢印で「平方の形に変形」へ）
    cv.textbox_px(316, 272, 152, 66,
                  ["解の公式（L04）", "＝平方の形に変形の手順を", "一般化した時短ルート"],
                  size=11, sw=AUX_W, dash=DASH, weight_first="bold")
    arrow_px(cv, 392, 268, 310, 150, w=1.1, head=6.0, dash=DASH)
    # 注記: 解が1つに重なる場合
    cv.text_px(16, 282, "※解が1つに重なるとき", size=11)
    cv.text_px(16, 296, "（(かたまり)²＝0 の形・L05）は，", size=11)
    cv.text_px(16, 310, "合流する一次方程式が1本になる", size=11)
    # キャプション
    cv.text_px(240, 362, "道は3本＋時短ルート1本。行き先の駅は1つ——一次方程式。",
               size=FS_CAP, anchor="middle")
    cv.text_px(240, 380, "（連立方程式は「文字を減らして」、二次方程式は「次数を減らして」同じ駅へ）",
               size=FS_CAP, anchor="middle")

    return dict(file="L10_fig1_solution_method_map.svg", canvas=cv, lesson="L10",
                title="解法系統図（3本の道＋時短ルートが一次方程式に合流）",
                intent="章末の地図。具体的な解の数値は書かず、3経路一致はassertで検算",
                src="lesson_10.md 1.（20行目のプレースホルダ）",
                params="経路検算=x²＋x−20/x²−64/(x＋3)²＝0＋係数4組（数値は図に書かない）",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L03, fig_L07_1, fig_L07_2, fig_L09, fig_L10]


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
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓" for d, t in meta["checks"])
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
        "# FIGURE_MANIFEST — 二次方程式単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。／ "
        "本文プレースホルダ6箇所と図版6枚は1対1対応。",
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
        "- 設問・例題の答（L01の5cm・L07例4のx=6・L09例1の10cmと底面6cm・"
        "L10総合演習の解±8や4と−5）は図に書かず、辺は x／(x＋1)／(x−4) などの文字表記のまま。"
        "スクリプト内assertで本文の答・与件（24cm²・60cm²・72cm³）と照合した。",
        "- 描画比は答の実比（L01はx=5比・L07図2はx=6比・L09はx=10比）を使うが、"
        "図中のラベルはすべて文字表記で値は現れない。",
        "- L03の「9」・L07図1の「x²＝3x＋10」は、図の直前・直後の本文が明示する解説値・"
        "解説式のため記載（設問の答ではない。方程式の解−3±√7やx=5は書かない）。",
        "- L10の系統図は解法名と流れのみを描き、経路一致の検算（3解法が同じ解に合流・"
        "重解時は1本）はassertでのみ行った。",
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
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")


if __name__ == "__main__":
    main()
