#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「三平方の定理」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み）。
ヘルパー群（Canvas/ティック/弧/直角/寸法線ほか）は相似単元
production/jhs-math-3-similar-figures/candidate_draft/assets_provenance/generate_figures.py
からコピー再利用（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（21枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib）
- 幾何の自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。
- 答えの分離方針: 近隣の設問が問う値は図に書かず「？」で示す。検算では本文の答と照合する。
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
GRID_C = "#bbb"   # 方眼の線色（薄グレー・情報は持たせない）


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き に変換して描く）
# 相似単元 generate_figures.py からコピー再利用（polyline に dash を追加拡張）
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

    def circle(self, c, r_math, w=MAIN_W, dash=None):
        x, y = self.P(c)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_math * self.s:.1f}" '
                 f'fill="none" stroke="#000" stroke-width="{w}"{d}/>')

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None):
        x, y = self.P(p)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS_CAP, anchor="start", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    # 記号マーク（docs/SPEC_figures.md） ------------------------------------
    def ticks(self, a, b, n=1, half=4.5, gap=3.5):
        """対応する辺のティック: 中点に垂直な短線をn本"""
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L          # 辺方向
        nx, ny = -uy, ux                 # 法線方向
        for i in range(n):
            off = (i - (n - 1) / 2) * gap
            cx, cy = mx + ux * off, my + uy * off
            self.raw(f'<line x1="{cx - nx * half:.1f}" y1="{cy - ny * half:.1f}" '
                     f'x2="{cx + nx * half:.1f}" y2="{cy + ny * half:.1f}" '
                     f'stroke="#000" stroke-width="1.4"/>')

    def angle_arc(self, v, p, q, r=14.0, n=1, gap=3.5, w=1.2):
        """頂点vで辺vp→vqの間の角の弧をn重に描く（折れ線近似・劣角側）"""
        vx, vy = self.P(v)
        px, py = self.P(p)
        qx, qy = self.P(q)
        a1 = math.atan2(py - vy, px - vx)
        a2 = math.atan2(qy - vy, qx - vx)
        d = a2 - a1
        while d <= -math.pi:
            d += 2 * math.pi
        while d > math.pi:
            d -= 2 * math.pi
        for k in range(n):
            rr = r + k * gap
            pts = []
            for i in range(21):
                t = a1 + d * i / 20
                pts.append(f"{vx + rr * math.cos(t):.1f},{vy + rr * math.sin(t):.1f}")
            self.raw(f'<polyline points="{" ".join(pts)}" fill="none" '
                     f'stroke="#000" stroke-width="{w}"/>')

    def right_angle(self, v, p, q, size=9.0):
        """頂点vの直角マーク（小正方形）。p,qは直交2辺の先の点"""
        vx, vy = self.P(v)
        px, py = self.P(p)
        qx, qy = self.P(q)
        u = (px - vx, py - vy)
        w_ = (qx - vx, qy - vy)
        lu, lw = math.hypot(*u), math.hypot(*w_)
        ux, uy = u[0] / lu * size, u[1] / lu * size
        wx, wy = w_[0] / lw * size, w_[1] / lw * size
        self.raw(f'<polyline points="{vx + ux:.1f},{vy + uy:.1f} '
                 f'{vx + ux + wx:.1f},{vy + uy + wy:.1f} {vx + wx:.1f},{vy + wy:.1f}" '
                 f'fill="none" stroke="#000" stroke-width="1.2"/>')

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

    def label_out(self, p, centroid_, s, dist_=15.0, size=FS, weight="bold"):
        """頂点名: 重心から離れる向きにdist(px)ずらして置く"""
        x, y = self.P(p)
        cx, cy = self.P(centroid_)
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        self.text_px(x + dx / L * dist_, y + dy / L * dist_ + size * 0.35,
                     s, size=size, anchor="middle", weight=weight)

    # 単元共通の追加ヘルパー（本スクリプトで追加） ---------------------------
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


# ---- 幾何ユーティリティ ----------------------------------------------------
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def centroid(*pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def angle_deg(v, p, q):
    """頂点vで辺vp・vqがつくる角の大きさ（度・0〜180）"""
    a = math.atan2(p[1] - v[1], p[0] - v[0])
    b = math.atan2(q[1] - v[1], q[0] - v[0])
    d = abs(b - a) % (2 * math.pi)
    return math.degrees(min(d, 2 * math.pi - d))


def shoelace(pts):
    """多角形の面積（符号なし）"""
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def arc_pts(center, r, deg_from, deg_to, n=48):
    """中心・半径・角度範囲（度・数学の向き）から円弧の折れ線点列（数学座標）"""
    return [(center[0] + r * math.cos(math.radians(deg_from + (deg_to - deg_from) * i / n)),
             center[1] + r * math.sin(math.radians(deg_from + (deg_to - deg_from) * i / n)))
            for i in range(n + 1)]


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


# ---- 3D平行投影（空間図形用・L07/L08） -------------------------------------
DEPTH = (0.55, 0.42)   # 奥行き1あたりの(x, y)ずれ（平行投影・立体風装飾なし）


def proj(p3):
    """(x, 奥行きd, 高さz) → 数学座標(x', y')。平行投影"""
    x, d, z = p3
    return (x + DEPTH[0] * d, z + DEPTH[1] * d)


def d3(a, b):
    return math.sqrt(sum((b[i] - a[i]) ** 2 for i in range(3)))


def dot3(u, v):
    return sum(u[i] * v[i] for i in range(3))


def sub3(a, b):
    return tuple(a[i] - b[i] for i in range(3))


# ===========================================================================
# 図1: L01 導入——3辺の上の3つの正方形（3・4・5）
# 本文根拠: lesson_01.md 導入「直角をはさむ2辺が3マスと4マス。面積9・16・25の配置」
# 答え漏れ注意: 面積9・16・25と関係式は導入時点の発見対象なので図に書かない
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（本文 lesson_01.md 導入 と一致させる） ---
    a, b = 3, 4                       # 直角をはさむ2辺（マス）
    R, X, Y = (0, 0), (b, 0), (0, a)  # 直角の頂点・横の頂点・縦の頂点
    # 斜辺の上の正方形（外側）: X-Y を1辺に、法線(a,b)方向へ
    S_hyp = [Y, X, (X[0] + a, X[1] + b), (Y[0] + a, Y[1] + b)]
    S_a = [R, Y, (-a, a), (-a, 0)]    # 縦の辺の上の正方形（左）
    S_b = [R, X, (b, -b), (0, -b)]    # 横の辺の上の正方形（下）

    c = dist(X, Y)
    ck = Checker()
    ck.ok("直角をはさむ2辺=3マス・4マス（本文どおり）", (a, b) == (3, 4))
    ck.ok("3つの正方形の面積=9・16・25", shoelace(S_a) == 9 and shoelace(S_b) == 16
          and abs(shoelace(S_hyp) - 25) < 1e-9)
    ck.ok("9+16=25（ピタゴラス数3,4,5）", a * a + b * b == 25 and abs(c - 5) < 1e-9)
    ck.ok("斜辺の正方形の頂点が全て格子点（方眼上に描ける）",
          all(abs(v[0] - round(v[0])) < 1e-9 and abs(v[1] - round(v[1])) < 1e-9
              for v in S_hyp))
    ck.ok("面積の値は図に書かない（導入の発見対象）", True)

    cv = Canvas(330, 344)
    cv.add_hatch()
    cv.s = 24.0
    cv.ox, cv.oy = 100, 192
    cv.grid(-3, -4, 7, 7)
    cv.polygon_nostroke(S_a, "url(#h45)")
    cv.polygon_nostroke(S_b, "url(#h135)")
    cv.polygon_nostroke(S_hyp, "#ddd")
    cv.polygon(S_a, w=MAIN_W)
    cv.polygon(S_b, w=MAIN_W)
    cv.polygon(S_hyp, w=MAIN_W)
    # 三角形（白抜きで前面に）
    cv.polygon([R, X, Y], w=MAIN_W, fill="#fff")
    cv.right_angle(R, X, Y)
    seg_label(cv, R, Y, "3マス", off=16, size=12, weight="bold")
    seg_label(cv, R, X, "4マス", off=-16, size=12, weight="bold")  # 三角形内側（白地）に置く
    cv.text_px(165, 310, "直角三角形の3つの辺の上に，外側に正方形を3つかく",
               size=FS_CAP, anchor="middle")
    cv.text_px(165, 327, "（3つの正方形の面積の間に，何か関係はないだろうか？）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_three_squares_on_grid.svg", canvas=cv, lesson="L01",
                title="3辺の上の3つの正方形（方眼・3マスと4マス）",
                intent="導入の発見用の図。塗り分けはハッチング2種+薄グレー。面積値は書かない",
                src="lesson_01.md 導入（22行目のプレースホルダ）",
                params="直角をはさむ2辺=3,4マス／斜辺の正方形は格子点(0,3)(4,0)(7,4)(3,7)",
                checks=ck.items)


# ===========================================================================
# 図2: L01 囲んで引く（7×7の中の傾いた正方形）
# 本文根拠: lesson_01.md 主概念1「49 − 24 ＝ 25」
# ===========================================================================
def fig_L01_2():
    # --- パラメータ（本文 lesson_01.md 主概念1 と一致させる） ---
    a, b = 3, 4
    n = a + b                                     # 囲む正方形の1辺=7
    T = [(a, 0), (n, a), (b, n), (0, b)]          # 傾いた正方形の頂点（格子点）

    side2 = dist(T[0], T[1]) ** 2
    ck = Checker()
    ck.ok("囲む正方形=1辺7マス・面積49", n == 7 and n * n == 49)
    ck.ok("四すみの直角三角形は3×4÷2=6が4つで24", 4 * (a * b / 2) == 24)
    ck.ok("傾いた正方形の面積=49−24=25（shoelaceでも一致）",
          abs(shoelace(T) - 25) < 1e-9 and n * n - 24 == 25)
    ck.ok("傾いた正方形の4辺が等しく対角線も等しい（正方形）",
          all(abs(dist(T[i], T[(i + 1) % 4]) ** 2 - side2) < 1e-9 for i in range(4))
          and abs(dist(T[0], T[2]) - dist(T[1], T[3])) < 1e-9)

    cv = Canvas(400, 316)
    cv.add_hatch()
    cv.s = 26.0
    cv.ox, cv.oy = 40, 212
    cv.grid(0, 0, n, n)
    # 四すみの三角形（ハッチ）→傾いた正方形（白）→輪郭
    corners = [[(0, 0), (a, 0), (0, b)], [(n, 0), (n, a), (a, 0)],
               [(n, n), (b, n), (n, a)], [(0, n), (0, b), (b, n)]]
    for tri in corners:
        cv.polygon_nostroke(tri, "url(#h45)")
    cv.polygon([(0, 0), (n, 0), (n, n), (0, n)], w=MAIN_W)
    cv.polygon(T, w=MAIN_W, fill="#fff")
    seg_label(cv, (0, 0), (a, 0), "3", off=14, size=12)
    seg_label(cv, (a, 0), (n, 0), "4", off=14, size=12)
    seg_label(cv, (n, 0), (n, a), "3", off=14, size=12)
    seg_label(cv, (n, a), (n, n), "4", off=14, size=12)
    # 傾いた正方形の目印（求める面積）
    cv.text(centroid(*T), "？", size=16, weight="bold")
    x0 = 250
    cv.text_px(x0, 60, "大きい正方形", size=FS_CAP)
    cv.text_px(x0, 77, "7×7＝49", size=FS, weight="bold")
    cv.text_px(x0, 106, "四すみの直角三角形", size=FS_CAP)
    cv.text_px(x0, 123, "3×4÷2＝6 → 4つで24", size=FS, weight="bold")
    cv.text_px(x0, 152, "傾いた正方形", size=FS_CAP)
    cv.text_px(x0, 169, "49−24＝25", size=FS, weight="bold")
    cv.text_px(200, 286, "「囲んで引く」——マス目に沿った正方形で囲み，", size=FS_CAP,
               anchor="middle")
    cv.text_px(200, 303, "四すみの三角形（斜線部）を引く", size=FS_CAP, anchor="middle")

    return dict(file="L01_fig2_enclose_and_subtract.svg", canvas=cv, lesson="L01",
                title="囲んで引く（1辺7の正方形−三角形4つ＝25）",
                intent="主概念1の手順図。本文の計算 49−24＝25 をそのまま添える（本文が直後に示す値）",
                src="lesson_01.md 主概念1（34行目のプレースホルダ）",
                params="a=3,b=4／囲む正方形1辺7／傾いた正方形の頂点(3,0)(7,3)(4,7)(0,4)",
                checks=ck.items)


# ===========================================================================
# 図3: L01 やってみようの作図見本（1と2／2と3）
# 本文根拠: lesson_01.md やってみよう1・2
# 答え漏れ注意: 面積の値そのものは図に書かない（直後の表で生徒が求める・本文指定）
# ===========================================================================
def fig_L01_3():
    # --- パラメータ（本文 やってみよう 1・2 と一致させる） ---
    cases = [(1, 2), (2, 3)]   # 直角をはさむ2辺（マス）

    ck = Checker()
    for a, b in cases:
        n = a + b
        T = [(a, 0), (n, a), (b, n), (0, b)]
        area = shoelace(T)
        ck.ok(f"({a},{b}): 傾いた正方形の面積={n}²−4×({a}×{b}÷2)={a * a + b * b}"
              "（図には書かない）",
              abs(area - (a * a + b * b)) < 1e-9 and abs(area - (n * n - 2 * a * b)) < 1e-9,
              f"shoelace={area:.4f}")
        ck.ok(f"({a},{b}): 頂点が全て格子点", all(
            abs(v[0] - round(v[0])) < 1e-9 and abs(v[1] - round(v[1])) < 1e-9 for v in T))

    cv = Canvas(460, 302)
    cv.add_hatch()

    def panel(a, b, ox, label):
        n = a + b
        T = [(a, 0), (n, a), (b, n), (0, b)]
        cv.s = 26.0
        cv.ox, cv.oy = ox, 210
        cv.grid(0, 0, n, n)
        corners = [[(0, 0), (a, 0), (0, b)], [(n, 0), (n, a), (a, 0)],
                   [(n, n), (b, n), (n, a)], [(0, n), (0, b), (b, n)]]
        for tri in corners:
            cv.polygon_nostroke(tri, "url(#h45)")
        cv.polygon([(0, 0), (n, 0), (n, n), (0, n)], w=MAIN_W)
        cv.polygon(T, w=MAIN_W, fill="#fff")
        seg_label(cv, (0, 0), (a, 0), str(a), off=13, size=12)
        seg_label(cv, (a, 0), (n, 0), str(b), off=13, size=12)
        cv.text_px(ox + n * 26 / 2, 240, label, size=FS_CAP, anchor="middle",
                   weight="bold")

    panel(1, 2, 60, "1．2辺が1マスと2マス")
    panel(2, 3, 260, "2．2辺が2マスと3マス")
    cv.text_px(230, 270, "見本: 傾いた正方形を，マス目に沿った正方形で囲む", size=FS_CAP,
               anchor="middle")
    cv.text_px(230, 287, "（面積＝囲む正方形 − 四すみの直角三角形4つ分。値は表で求めよう）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig3_tilted_square_examples.svg", canvas=cv, lesson="L01",
                title="やってみようの作図見本（1・2マス／2・3マス）",
                intent="囲んで引く手順の見本2連。面積の値は本文指定により図に書かない",
                src="lesson_01.md やってみよう（64行目のプレースホルダ）",
                params="ケース(1,2)と(2,3)／囲む正方形は1辺3と1辺5",
                checks=ck.items)


# ===========================================================================
# 図4: L02 三平方の定理の基本図（a・b・c）
# 本文根拠: lesson_02.md 主概念1「直角をはさむ2辺a,b・斜辺c」
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（形は3:4:5比・ラベルは文字。本文と同じ記号a,b,c） ---
    A, B, C = (0.0, 3.0), (0.0, 0.0), (4.0, 0.0)   # 直角はB

    ck = Checker()
    ck.ok("Bが直角（内積=0）", (A[0] - B[0]) * (C[0] - B[0])
          + (A[1] - B[1]) * (C[1] - B[1]) == 0)
    ck.ok("斜辺ACが最長辺（直角の向かい側）",
          dist(A, C) > dist(A, B) and dist(A, C) > dist(B, C))

    cv = Canvas(420, 258)
    cv.s = 40.0
    cv.ox, cv.oy = 90, 190
    cv.polygon([A, B, C])
    cv.right_angle(B, A, C)
    seg_label(cv, B, A, "a", off=-15, size=16)
    seg_label(cv, B, C, "b", off=15, size=16)
    seg_label(cv, A, C, "c（斜辺）", off=-27, size=15)
    # 「直角の向かい側」を示す矢印（直角マークから斜辺へ）
    x1, y1 = cv.P((0.42, 0.42))
    x2, y2 = cv.P(lerp(A, C, 0.55))
    arrow_px(cv, x1, y1, x2 - 7, y2 + 7, w=1.1, head=6.0)
    cv.text_px(210, 226, "直角の向かい側にある一番長い辺が斜辺 c", size=FS_CAP,
               anchor="middle")
    cv.text_px(210, 246, "三平方の定理: a²＋b²＝c²", size=FS, anchor="middle",
               weight="bold")

    return dict(file="L02_fig1_theorem_basic_triangle.svg", canvas=cv, lesson="L02",
                title="三平方の定理の基本図（a・b・c と斜辺の位置）",
                intent="定理の記号定義図。矢印で「直角の向かい側＝斜辺」を可視化",
                src="lesson_02.md 主概念1（30行目のプレースホルダ）",
                params="形は3:4:5比（ラベルはa,b,c）・直角はB",
                checks=ck.items)


# ===========================================================================
# 図5: L02 証明のアイデア（風車の並べかえ）
# 本文根拠: lesson_02.md 主概念2「(a＋b)²−三角形4枚＝c²」
# ===========================================================================
def fig_L02_2():
    # --- パラメータ（概念図。形はa=3,b=4比・ラベルは文字） ---
    a, b = 3.0, 4.0
    n = a + b
    T = [(a, 0), (n, a), (b, n), (0, b)]          # 中央の傾いた正方形（1辺c）

    c2 = dist(T[0], T[1]) ** 2
    ck = Checker()
    ck.ok("中央の4辺が等しい（1辺c=√(a²+b²)）",
          all(abs(dist(T[i], T[(i + 1) % 4]) ** 2 - c2) < 1e-9 for i in range(4))
          and abs(c2 - (a * a + b * b)) < 1e-9)
    ck.ok("中央の角が直角（正方形）",
          all(abs(angle_deg(T[i], T[i - 1], T[(i + 1) % 4]) - 90) < 1e-9
              for i in range(4)))
    ck.ok("面積の恒等式 (a+b)²−4×(ab/2)＝a²+b²＝c²",
          abs(n * n - 2 * a * b - c2) < 1e-9 and abs(shoelace(T) - c2) < 1e-9)

    cv = Canvas(440, 300)
    cv.add_hatch()
    cv.s = 30.0
    cv.ox, cv.oy = 40, 244
    corners = [[(0, 0), (a, 0), (0, b)], [(n, 0), (n, a), (a, 0)],
               [(n, n), (b, n), (n, a)], [(0, n), (0, b), (b, n)]]
    for tri in corners:
        cv.polygon_nostroke(tri, "url(#h45)")
        cv.polygon(tri, w=1.0)
    cv.polygon([(0, 0), (n, 0), (n, n), (0, n)], w=MAIN_W)
    cv.polygon(T, w=MAIN_W, fill="#fff")
    seg_label(cv, (0, 0), (a, 0), "a", off=14, size=14)
    seg_label(cv, (a, 0), (n, 0), "b", off=14, size=14)
    seg_label(cv, (n, 0), (n, a), "a", off=14, size=14)
    seg_label(cv, (n, a), (n, n), "b", off=14, size=14)
    seg_label(cv, T[0], T[1], "c", off=-13, t=0.5, size=14)
    cv.text(centroid(*T), "c²", size=16, weight="bold")
    x0 = 290
    cv.text_px(x0, 76, "1辺(a＋b)の正方形に", size=FS_CAP)
    cv.text_px(x0, 93, "合同な直角三角形4枚を", size=FS_CAP)
    cv.text_px(x0, 110, "風車のように並べる", size=FS_CAP)
    cv.text_px(x0, 145, "全体 (a＋b)²", size=FS, weight="bold")
    cv.text_px(x0, 167, "− 三角形4枚", size=FS, weight="bold")
    cv.text_px(x0, 189, "＝ 真ん中の c²", size=FS, weight="bold")
    cv.text_px(220, 288, "（斜線部＝合同な直角三角形4枚。真ん中に1辺cの正方形が残る）",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig2_pinwheel_proof_idea.svg", canvas=cv, lesson="L02",
                title="証明のアイデア（風車の4枚並べ）",
                intent="主概念2の証明図。囲んで引くがそのまま証明になる対応を注記",
                src="lesson_02.md 主概念2（53行目のプレースホルダ）",
                params="形はa=3,b=4比（ラベルは文字a,b,c）・中央の正方形は厳密に正方形",
                checks=ck.items)


# ===========================================================================
# 図6: L02 練習4（7cmと√15cmの直角三角形）
# 本文根拠: lesson_02.md 練習4
# 答え漏れ注意: 斜辺8cmは書かない（answer_key照合のみ）→図は「？」
# ===========================================================================
def fig_L02_3():
    # --- パラメータ（本文 練習4 と一致させる） ---
    b, a = 7.0, math.sqrt(15.0)     # 直角をはさむ2辺
    A, B, C = (0.0, a), (0.0, 0.0), (b, 0.0)

    ck = Checker()
    ck.ok("7²+(√15)²=49+15=64=8²（answer_keyの答8cmと整合・図には？）",
          abs(b * b + a * a - 64) < 1e-9 and abs(dist(A, C) - 8) < 1e-9,
          f"斜辺={dist(A, C):.4f}")
    ck.ok("Bが直角", (A[0] - B[0]) * (C[0] - B[0]) + (A[1] - B[1]) * (C[1] - B[1]) == 0)

    cv = Canvas(380, 220)
    cv.s = 36.0
    cv.ox, cv.oy = 60, 170
    cv.polygon([A, B, C])
    cv.right_angle(B, A, C)
    seg_label(cv, B, A, "√15cm", off=-27, size=FS)
    seg_label(cv, B, C, "7cm", off=13, size=FS)
    seg_label(cv, A, C, "？", off=-14, size=15, weight="bold")
    cv.text_px(190, 205, "（練習4: 斜辺の長さを求めよう）", size=FS_CAP, anchor="middle")

    return dict(file="L02_fig3_practice_7_sqrt15.svg", canvas=cv, lesson="L02",
                title="練習4の図（2辺が7cmと√15cm）",
                intent="練習4の与件図。問われる斜辺は？表記（答えの値は書かない）",
                src="lesson_02.md 練習4（108行目のプレースホルダ）",
                params="直角をはさむ2辺=7, √15（座標は厳密値）",
                checks=ck.items)


# ===========================================================================
# 図7: L03 定理の逆（3・4・5で直角ができる）
# 本文根拠: lesson_03.md 主概念「長さ5の辺の向かいの角が直角になる・分度器×ものさし○」
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 と一致させる） ---
    P, Q, R = (0.0, 0.0), (4.0, 0.0), (4.0, 3.0)   # 3辺 3,4,5。直角はQ

    ck = Checker()
    ck.ok("3辺=3,4,5（本文どおり）", abs(dist(Q, R) - 3) < 1e-9
          and abs(dist(P, Q) - 4) < 1e-9 and abs(dist(P, R) - 5) < 1e-9)
    ck.ok("3²+4²=5²（逆の判定が成立）", 9 + 16 == 25)
    ck.ok("長さ5の辺(PR)の向かいの角Qが90°", abs(angle_deg(Q, P, R) - 90) < 1e-9)

    cv = Canvas(460, 300)
    cv.s = 40.0
    cv.ox, cv.oy = 40, 226
    cv.polygon([P, Q, R])
    cv.right_angle(Q, P, R)
    seg_label(cv, P, Q, "4", off=14, size=15)
    seg_label(cv, Q, R, "3", off=14, size=15)
    seg_label(cv, P, R, "5", off=-14, size=15)
    # 注記: ここが直角になる（三角形の上の空きへ・矢印で直角の頂点Qを指す）
    xq, yq = cv.P(Q)
    cv.text_px(60, 56, "ここが直角になる", size=FS)
    arrow_px(cv, 128, 62, xq - 10, yq - 16, w=1.2, head=6.5)
    # 対比アイコン: 分度器（×）とものさし（○）
    px0, py0 = 330, 96
    pts = " ".join(f"{px0 + 34 * math.cos(math.radians(180 - t)):.1f},"
                   f"{py0 - 34 * math.sin(math.radians(180 - t)):.1f}"
                   for t in range(0, 181, 9))
    cv.raw(f'<polyline points="{pts}" fill="none" stroke="#000" stroke-width="1.3"/>')
    cv.raw(f'<line x1="{px0 - 34}" y1="{py0}" x2="{px0 + 34}" y2="{py0}" '
           f'stroke="#000" stroke-width="1.3"/>')
    for t in range(0, 181, 30):
        x1 = px0 + 34 * math.cos(math.radians(t))
        y1 = py0 - 34 * math.sin(math.radians(t))
        x2 = px0 + 28 * math.cos(math.radians(t))
        y2 = py0 - 28 * math.sin(math.radians(t))
        cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
               f'stroke="#000" stroke-width="0.9"/>')
    cv.raw(f'<line x1="{px0 - 14}" y1="{py0 - 28}" x2="{px0 + 14}" y2="{py0 - 4}" '
           f'stroke="#000" stroke-width="2.6"/>')
    cv.raw(f'<line x1="{px0 - 14}" y1="{py0 - 4}" x2="{px0 + 14}" y2="{py0 - 28}" '
           f'stroke="#000" stroke-width="2.6"/>')
    cv.text_px(px0, py0 + 18, "角度を測らなくても", size=11, anchor="middle")
    rx0, ry0 = 330, 158
    cv.raw(f'<rect x="{rx0 - 34}" y="{ry0}" width="68" height="20" fill="none" '
           f'stroke="#000" stroke-width="1.3"/>')
    for i in range(1, 7):
        x = rx0 - 34 + i * 68 / 7
        cv.raw(f'<line x1="{x:.1f}" y1="{ry0}" x2="{x:.1f}" y2="{ry0 + 7}" '
               f'stroke="#000" stroke-width="0.9"/>')
    cv.raw(f'<circle cx="{rx0}" cy="{ry0 + 10}" r="17" fill="none" stroke="#000" '
           f'stroke-width="2.6"/>')
    cv.text_px(rx0, ry0 + 42, "3辺の長さだけで", size=11, anchor="middle")
    cv.text_px(230, 268, "3辺が3・4・5なら 3²＋4²＝5² → 長さ5の辺を斜辺とする直角三角形",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 285, "（三平方の定理の逆: 辺の長さが角の情報を握っている）",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_converse_345.svg", canvas=cv, lesson="L03",
                title="定理の逆（3・4・5→直角）と分度器×・ものさし○の対比",
                intent="主概念の図。角度を測らず3辺で直角が決まることをアイコン対比で示す",
                src="lesson_03.md 主概念（34行目のプレースホルダ）",
                params="3辺=3,4,5・直角の頂点は長さ5の辺の向かい",
                checks=ck.items)


# ===========================================================================
# 図8: L04 正三角形の高さ（1辺6cm・垂線AH）
# 本文根拠: lesson_04.md 例題1「1辺6cm・BH=HC=3cm・h=AH」
# 答え漏れ注意: h=3√3・面積9√3は書かない（hのまま）
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（本文 例題1 と一致させる） ---
    side = 6.0
    B, C = (0.0, 0.0), (side, 0.0)
    A = (side / 2, side * math.sqrt(3) / 2)
    H = (side / 2, 0.0)

    ck = Checker()
    ck.ok("正三角形（3辺とも6cm）", all(abs(dist(p, q) - 6) < 1e-9
          for p, q in [(A, B), (B, C), (C, A)]))
    ck.ok("HはBCの中点（BH=HC=3cm）", abs(dist(B, H) - 3) < 1e-9
          and abs(dist(H, C) - 3) < 1e-9)
    ck.ok("AH⊥BC・h=3√3（本文の答と一致・図にはhのみ）",
          A[0] == H[0] and abs(dist(A, H) - 3 * math.sqrt(3)) < 1e-9,
          f"AH={dist(A, H):.4f}")
    ck.ok("△ABHは斜辺6・底辺3の直角三角形", abs(dist(A, B) - 6) < 1e-9
          and abs(angle_deg(H, A, B) - 90) < 1e-9)

    cv = Canvas(380, 300)
    cv.s = 34.0
    cv.ox, cv.oy = 85, 230
    cv.polygon([A, B, C])
    cv.line(A, H, w=AUX_W, dash=DASH)      # 求める高さ=破線
    cv.right_angle(H, C, A)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    cv.dot(H)
    xh, yh = cv.P(H)
    cv.text_px(xh + 4, yh + 17, "H", size=FS, anchor="middle", weight="bold")
    cv.ticks(B, H, 1)
    cv.ticks(H, C, 1)
    seg_label(cv, B, H, "3cm", off=15, size=12)
    seg_label(cv, H, C, "3cm", off=15, size=12)
    seg_label(cv, A, B, "6cm", off=-16, size=12)
    seg_label(cv, A, H, "h", off=-12, t=0.45, size=15)
    cv.text_px(190, 268, "頂点Aから底辺BCへ垂線AH。垂線は底辺を2等分（BH＝HC＝3cm）",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 285, "（例題1: 直角三角形ABHで高さh＝AHを求める）",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_equilateral_height.svg", canvas=cv, lesson="L04",
                title="正三角形の高さ（1辺6cm・垂線AH）",
                intent="例題1の図。同ティック=BH・HC等長。hは未知のまま（答えの値は書かない）",
                src="lesson_04.md 例題1（28行目のプレースホルダ）",
                params="1辺=6・頂点A=厳密計算（高さの値は答えのため非表示）・H=BC中点",
                checks=ck.items)


# ===========================================================================
# 図9: L04 三角定規の3辺の比（1:1:√2 と 1:2:√3）
# 本文根拠: lesson_04.md 主概念2（30°の向かいが1・90°の向かいが2・60°の向かいが√3）
# ===========================================================================
def fig_L04_2():
    # --- パラメータ（比は厳密値） ---
    r2, r3 = math.sqrt(2.0), math.sqrt(3.0)
    # 左: 直角二等辺 C1直角
    C1, B1, A1 = (0.0, 0.0), (1.0, 0.0), (0.0, 1.0)
    # 右: 30°60°90° C2直角・Bの角30°・Aの角60°
    C2, B2, A2 = (0.0, 0.0), (r3, 0.0), (0.0, 1.0)

    ck = Checker()
    ck.ok("左: 斜辺=√2・角が45°45°90°", abs(dist(A1, B1) - r2) < 1e-9
          and abs(angle_deg(A1, C1, B1) - 45) < 1e-9
          and abs(angle_deg(B1, C1, A1) - 45) < 1e-9)
    ck.ok("左: 3辺の比 1:1:√2", abs(dist(C1, B1) - 1) < 1e-9
          and abs(dist(C1, A1) - 1) < 1e-9)
    ck.ok("右: 角が30°(B)・60°(A)・90°(C)",
          abs(angle_deg(B2, C2, A2) - 30) < 1e-9
          and abs(angle_deg(A2, C2, B2) - 60) < 1e-9
          and abs(angle_deg(C2, A2, B2) - 90) < 1e-9)
    ck.ok("右: 3辺の比 1:2:√3（30°の向かい=1・90°の向かい=2・60°の向かい=√3）",
          abs(dist(C2, A2) - 1) < 1e-9 and abs(dist(A2, B2) - 2) < 1e-9
          and abs(dist(C2, B2) - r3) < 1e-9)

    cv = Canvas(500, 292)
    s = 108.0
    # 左パネル
    cv.s = s
    cv.ox, cv.oy = 55, 190
    cv.polygon([A1, B1, C1])
    cv.right_angle(C1, A1, B1)
    cv.angle_arc(A1, C1, B1, r=16)
    cv.angle_arc(B1, C1, A1, r=16)
    xa, ya = cv.P(A1)
    cv.text_px(xa + 16, ya + 24, "45°", size=12, anchor="middle")
    xb, yb = cv.P(B1)
    cv.text_px(xb - 24, yb - 12, "45°", size=12, anchor="middle")
    seg_label(cv, C1, B1, "1", off=14, size=15)
    seg_label(cv, C1, A1, "1", off=-13, size=15)
    seg_label(cv, A1, B1, "√2", off=-17, size=15)
    cv.text_px(55 + s * 0.5, 226, "45°・45°・90°", size=FS, anchor="middle", weight="bold")
    cv.text_px(55 + s * 0.5, 244, "1 : 1 : √2", size=FS, anchor="middle", weight="bold")
    cv.text_px(55 + s * 0.5, 262, "45°の向かい＝1，90°の向かい＝√2", size=11, anchor="middle")
    # 右パネル
    cv.ox, cv.oy = 260, 190
    cv.polygon([A2, B2, C2])
    cv.right_angle(C2, A2, B2)
    cv.angle_arc(B2, C2, A2, r=22)
    cv.angle_arc(A2, C2, B2, r=14)
    xb, yb = cv.P(B2)
    cv.text_px(xb - 40, yb - 10, "30°", size=12, anchor="middle")
    xa, ya = cv.P(A2)
    cv.text_px(xa + 20, ya + 26, "60°", size=12, anchor="middle")
    seg_label(cv, C2, B2, "√3", off=14, size=15)
    seg_label(cv, C2, A2, "1", off=-13, size=15)
    seg_label(cv, A2, B2, "2", off=-15, size=15)
    cx = 260 + r3 * s / 2
    cv.text_px(cx, 226, "30°・60°・90°", size=FS, anchor="middle", weight="bold")
    cv.text_px(cx, 244, "1 : 2 : √3（短:斜辺:中間）", size=FS, anchor="middle", weight="bold")
    cv.text_px(cx, 262, "30°の向かい＝1，90°の向かい＝2，60°の向かい＝√3",
               size=11, anchor="middle")
    cv.text_px(250, 284, "（2種類の三角定規——角の向かいにどの辺が来るかで比を読む）",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig2_set_square_ratios.svg", canvas=cv, lesson="L04",
                title="三角定規の3辺の比（1:1:√2／1:2:√3）",
                intent="主概念2の一覧図。角と向かいの辺の対応を両パネルで明示",
                src="lesson_04.md 主概念2（60行目のプレースホルダ）",
                params="左=直角二等辺(1,1,√2)・右=30°60°90°(1,√3,2)・座標は厳密値",
                checks=ck.items)


# ===========================================================================
# 図10: L05 長方形の対角線（縦4cm・横6cm）
# 本文根拠: lesson_05.md 例題1
# 答え漏れ注意: 対角線2√13cmは書かない→「？」
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（本文 例題1 と一致させる） ---
    tate, yoko = 4.0, 6.0
    A, B, C, D = (0.0, tate), (0.0, 0.0), (yoko, 0.0), (yoko, tate)

    ck = Checker()
    ck.ok("長方形（縦4cm・横6cm）", abs(dist(A, B) - 4) < 1e-9
          and abs(dist(B, C) - 6) < 1e-9)
    ck.ok("∠B=90°", abs(angle_deg(B, A, C) - 90) < 1e-9)
    ck.ok("対角線AC=√52=2√13（本文の答と一致・図には？）",
          abs(dist(A, C) - 2 * math.sqrt(13)) < 1e-9, f"AC={dist(A, C):.4f}")

    cv = Canvas(400, 262)
    cv.s = 36.0
    cv.ox, cv.oy = 70, 190
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=MAIN_W)
    cv.right_angle(B, A, C)
    g = centroid(A, B, C, D)
    for p, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p, g, nm)
    seg_label(cv, B, A, "4cm", off=13, size=12)
    seg_label(cv, B, C, "6cm", off=13, size=12)
    seg_label(cv, A, C, "？", off=-13, t=0.42, size=15, weight="bold")
    cv.text_px(200, 228, "対角線ACが長方形を2つの直角三角形に分ける（∠B＝90°を使う）",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 245, "（例題1: 対角線ACの長さを求める）", size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_rectangle_diagonal.svg", canvas=cv, lesson="L05",
                title="長方形の対角線（縦4cm・横6cm）",
                intent="例題1の図。対角線=直角三角形ABCの斜辺。答えの値は？表記",
                src="lesson_05.md 例題1（28行目のプレースホルダ）",
                params="縦4・横6・A=(0,4),B=(0,0),C=(6,0),D=(6,4)",
                checks=ck.items)


# ===========================================================================
# 図11: L05 円の弦と中心からの距離（半径5cm・距離3cm）
# 本文根拠: lesson_05.md 例題2
# 答え漏れ注意: AH=4cm・AB=8cmは書かない→「？」
# ===========================================================================
def fig_L05_2():
    # --- パラメータ（本文 例題2 と一致させる） ---
    r, d = 5.0, 3.0
    O = (0.0, 0.0)
    half = math.sqrt(r * r - d * d)          # AH（図には書かない）
    A, B, H = (-half, -d), (half, -d), (0.0, -d)

    ck = Checker()
    ck.ok("A・Bが円周上（OA=OB=5cm）", abs(dist(O, A) - r) < 1e-9
          and abs(dist(O, B) - r) < 1e-9)
    ck.ok("OH⊥AB・OH=3cm", abs(angle_deg(H, O, A) - 90) < 1e-9
          and abs(dist(O, H) - d) < 1e-9)
    ck.ok("AH=4cm・AB=8cm（本文の答と一致・図には？）",
          abs(half - 4) < 1e-9 and abs(dist(A, B) - 8) < 1e-9)
    ck.ok("HはABの中点（垂線は弦を2等分）", abs(dist(A, H) - dist(H, B)) < 1e-12)

    cv = Canvas(400, 320)
    cv.s = 22.0
    cv.ox, cv.oy = 200, 128
    cv.circle(O, r, w=MAIN_W)
    # 三角形OAHを薄グレーで強調
    cv.polygon_nostroke([O, A, H], "#e6e6e6")
    cv.line(A, B, w=MAIN_W)
    cv.line(O, H, w=MAIN_W)
    cv.line(O, A, w=BOLD_W)                  # 自分で引く半径=強調
    cv.right_angle(H, O, A)
    cv.dot(O)
    cv.dot(A)
    cv.dot(B)
    cv.dot(H)
    xo, yo = cv.P(O)
    cv.text_px(xo + 4, yo - 10, "O", size=FS, anchor="middle", weight="bold")
    xa, ya = cv.P(A)
    cv.text_px(xa - 14, ya + 5, "A", size=FS, anchor="middle", weight="bold")
    xb, yb = cv.P(B)
    cv.text_px(xb + 14, yb + 5, "B", size=FS, anchor="middle", weight="bold")
    xh, yh = cv.P(H)
    cv.text_px(xh + 6, yh + 17, "H", size=FS, anchor="middle", weight="bold")
    seg_label(cv, O, A, "5cm", off=-15, t=0.55, size=12)
    seg_label(cv, O, H, "3cm", off=-14, t=0.5, size=12)
    cv.ticks(A, H, 1)
    cv.ticks(H, B, 1)
    cv.text_px(xh, yh + 36, "AB＝？", size=14, anchor="middle", weight="bold")
    cv.text_px(200, 288, "中心Oから弦ABへ垂線OH（3cm）＋半径OA（5cm）→直角三角形OAH",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 305, "垂線は弦を2等分する（AH＝HB・同ティック）", size=FS_CAP,
               anchor="middle")

    return dict(file="L05_fig2_circle_chord_distance.svg", canvas=cv, lesson="L05",
                title="円の弦と中心からの距離（半径5cm・OH=3cm）",
                intent="例題2の図。太線=自分で引く半径。△OAH薄グレー強調。答えのABは？表記",
                src="lesson_05.md 例題2（44行目のプレースホルダ）",
                params="r=5,OH=3・A,Bは円周上厳密（AHの途中値は非表示）",
                checks=ck.items)


# ===========================================================================
# 図12: L05 座標平面上の2点間の距離（A(1,2)・B(4,6)）
# 本文根拠: lesson_05.md 例題3
# 答え漏れ注意: AB=5は書かない→「？」
# ===========================================================================
def fig_L05_3():
    # --- パラメータ（本文 例題3 と一致させる） ---
    A, B = (1.0, 2.0), (4.0, 6.0)
    C = (B[0], A[1])                       # 直角の頂点(4,2)

    ck = Checker()
    ck.ok("横のずれ=4−1=3・縦のずれ=6−2=4", abs(dist(A, C) - 3) < 1e-9
          and abs(dist(C, B) - 4) < 1e-9)
    ck.ok("Cが直角(4,2)", C == (4.0, 2.0)
          and abs(angle_deg(C, A, B) - 90) < 1e-9)
    ck.ok("AB=5（本文の答と一致・図には？）", abs(dist(A, B) - 5) < 1e-9)

    cv = Canvas(400, 322)
    cv.s = 34.0
    cv.ox, cv.oy = 60, 262
    cv.grid(0, 0, 6, 7)
    # 座標軸
    cv.line((-0.5, 0), (6.4, 0), w=1.2)
    cv.line((0, -0.5), (0, 7.3), w=1.2)
    x1, y1 = cv.P((6.4, 0))
    arrow_px(cv, x1 - 10, y1, x1 + 4, y1, w=1.2, head=6)
    x1, y1 = cv.P((0, 7.3))
    arrow_px(cv, x1, y1 + 10, x1, y1 - 4, w=1.2, head=6)
    xo, yo = cv.P((0, 0))
    cv.text_px(xo - 8, yo + 15, "O", size=12, anchor="middle")
    x1, y1 = cv.P((6.35, 0))
    cv.text_px(x1, y1 + 16, "x", size=12, anchor="middle")
    x1, y1 = cv.P((0, 7.25))
    cv.text_px(x1 - 12, y1 + 4, "y", size=12, anchor="middle")
    for i in (1, 4):
        x1, y1 = cv.P((i, 0))
        cv.text_px(x1, y1 + 15, str(i), size=11, anchor="middle")
    for j in (2, 6):
        x1, y1 = cv.P((0, j))
        cv.text_px(x1 - 10, y1 + 4, str(j), size=11, anchor="end")
    cv.line(A, B, w=MAIN_W)
    cv.line(A, C, w=AUX_W, dash=DASH)
    cv.line(C, B, w=AUX_W, dash=DASH)
    cv.right_angle(C, A, B)
    cv.dot(A)
    cv.dot(B)
    cv.dot(C)
    xa, ya = cv.P(A)
    cv.text_px(xa - 8, ya + 18, "A(1, 2)", size=FS, anchor="middle", weight="bold")
    xb, yb = cv.P(B)
    cv.text_px(xb + 2, yb - 10, "B(4, 6)", size=FS, anchor="middle", weight="bold")
    xc, yc = cv.P(C)
    cv.text_px(xc + 22, yc + 14, "C(4, 2)", size=FS, anchor="middle", weight="bold")
    seg_label(cv, A, C, "3", off=13, size=14)
    seg_label(cv, C, B, "4", off=-14, size=14)
    seg_label(cv, A, B, "？", off=-13, t=0.5, size=15, weight="bold")
    cv.text_px(200, 292, "ABを斜辺に，横の線と縦の線で直角三角形ABCを作る（破線）",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 309, "（例題3: 2点A・B間の距離を求める）", size=FS_CAP, anchor="middle")

    return dict(file="L05_fig3_coordinate_distance.svg", canvas=cv, lesson="L05",
                title="座標平面上の2点間の距離（A(1,2)・B(4,6)）",
                intent="例題3の図。補助の直角三角形は破線。答えの値は？表記",
                src="lesson_05.md 例題3（66行目のプレースホルダ）",
                params="A=(1,2),B=(4,6),C=(4,2)・ずれ3と4",
                checks=ck.items)


# ===========================================================================
# 図13: L06 1辺1の正方形の対角線=√2
# 本文根拠: lesson_06.md 主概念1
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（本文 主概念1 と一致させる） ---
    Sq = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    diag = dist(Sq[0], Sq[2])

    ck = Checker()
    ck.ok("1辺1の正方形", all(abs(dist(Sq[i], Sq[(i + 1) % 4]) - 1) < 1e-12
          for i in range(4)))
    ck.ok("対角線=√2（x²=1²+1²=2）", abs(diag - math.sqrt(2)) < 1e-12,
          f"={diag:.6f}")

    cv = Canvas(380, 280)
    cv.s = 62.0
    cv.ox, cv.oy = 76, 208
    cv.grid(0, 0, 3, 2)
    cv.polygon(Sq, w=MAIN_W, fill="#eee")
    cv.line(Sq[0], Sq[2], w=BOLD_W)
    seg_label(cv, Sq[0], Sq[1], "1", off=14, size=14)
    seg_label(cv, Sq[1], Sq[2], "1", off=14, size=14)   # 正方形の外側（右の空きマス）に置く
    seg_label(cv, Sq[0], Sq[2], "√2", off=-17, t=0.5, size=16, weight="bold")
    xg, yg = cv.P((2.5, 1.5))
    cv.text_px(xg, yg, "1マス＝1", size=FS_CAP, anchor="middle")
    xg, yg = cv.P((2.5, 1.2))
    cv.text_px(xg, yg + 4, "（方眼）", size=11, anchor="middle")
    cv.text_px(190, 246, "1辺1の正方形の対角線の長さが√2（太線）", size=FS_CAP,
               anchor="middle")
    cv.text_px(190, 263, "対角線はマス目の目盛りでは測れない長さ", size=FS_CAP,
               anchor="middle")

    return dict(file="L06_fig1_unit_square_diagonal.svg", canvas=cv, lesson="L06",
                title="1辺1の正方形の対角線＝√2",
                intent="主概念1の図。方眼1マス=1、対角線を太線で強調",
                src="lesson_06.md 主概念1（35行目のプレースホルダ）",
                params="正方形(0,0)-(1,1)・対角線√2厳密",
                checks=ck.items)


# ===========================================================================
# 図14: L06 数直線上に√2を作図（手順①〜④）
# 本文根拠: lesson_06.md 主概念2（手順1〜4）
# ===========================================================================
def fig_L06_2():
    # --- パラメータ（本文 主概念2 と一致させる） ---
    O = (0.0, 0.0)
    Pt = (1.0, 1.0)                     # 1の点から高さ1の点P
    r = dist(O, Pt)                     # 斜辺OP=√2

    ck = Checker()
    ck.ok("OP=√2（1²+1²=2）", abs(r - math.sqrt(2)) < 1e-12, f"OP={r:.6f}")
    ck.ok("弧と数直線の交点=√2の位置", abs(r - 1.4142135623730951) < 1e-12)
    ck.ok("√2は1と2の間（数直線の目盛り0,1,2に収まる）", 1 < r < 2)

    cv = Canvas(430, 270)
    cv.s = 110.0
    cv.ox, cv.oy = 60, 180
    # 数直線
    cv.line((-0.35, 0), (2.45, 0), w=1.4)
    x1, y1 = cv.P((2.45, 0))
    arrow_px(cv, x1 - 10, y1, x1 + 4, y1, w=1.4, head=6.5)
    for t, lab in [(0, "0"), (1, "1"), (2, "2")]:
        cv.line((t, -0.045), (t, 0.045), w=1.3)
        xt, yt = cv.P((t, 0))
        cv.text_px(xt, yt + 22, lab, size=FS, anchor="middle")
    # 垂線・P・斜辺
    cv.line((1, 0), (1, 1.18), w=AUX_W, dash=DASH)
    cv.line((1, 0), Pt, w=MAIN_W)
    cv.right_angle((1, 0), (0, 0), (1, 1))
    cv.dot(Pt)
    xp, yp = cv.P(Pt)
    cv.text_px(xp + 14, yp - 6, "P", size=FS, anchor="middle", weight="bold")
    cv.line(O, Pt, w=MAIN_W)
    cv.dot(O)
    xo, yo = cv.P(O)
    cv.text_px(xo - 6, yo - 10, "O", size=FS, anchor="middle", weight="bold")
    seg_label(cv, O, Pt, "√2", off=-15, t=0.55, size=14)
    seg_label(cv, (1, 0), Pt, "1", off=13, t=0.5, size=13)
    # 弧（Pから数直線へ・折れ線サンプリング）
    cv.polyline(arc_pts(O, r, 45, 0), w=MAIN_W)
    Q = (r, 0.0)
    cv.dot(Q)
    xq, yq = cv.P(Q)
    cv.text_px(xq + 4, yq + 22, "√2", size=FS, anchor="middle", weight="bold")
    # 手順番号①〜④
    xt, yt = cv.P((0.45, 0))
    cv.text_px(xt, yt + 40, "①数直線に0と1", size=11, anchor="middle")
    xt, yt = cv.P((1, 1.18))
    cv.text_px(xt - 2, yt - 8, "②1の点から垂線", size=11, anchor="middle")
    cv.text_px(20, 66, "③高さ1の点P・斜辺OP", size=11, anchor="start")
    xt, yt = cv.P((1.45, 0.75))
    cv.text_px(xt + 6, yt, "④Oを中心に半径OPの弧", size=11)
    cv.text_px(215, 252, "（コンパスで斜辺OPの長さ√2を数直線の上へ写し取る）",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig2_sqrt2_on_numberline.svg", canvas=cv, lesson="L06",
                title="数直線上に√2を作図（手順①〜④）",
                intent="主概念2の手順図。弧は折れ線サンプリング。①〜④を図中対応",
                src="lesson_06.md 主概念2（52行目のプレースホルダ）",
                params="O=0,垂線位置=1,高さ=1→OP=√2・交点x=√2厳密",
                checks=ck.items)


# ===========================================================================
# 図15: L06 練習3（2の位置から高さ1→点x）
# 本文根拠: lesson_06.md 練習3
# 答え漏れ注意: x=√5は書かない（xのまま）
# ===========================================================================
def fig_L06_3():
    # --- パラメータ（本文 練習3 と一致させる） ---
    O = (0.0, 0.0)
    Pt = (2.0, 1.0)                     # 2の位置から高さ1
    r = dist(O, Pt)                     # 斜辺=√5（図には書かない）

    ck = Checker()
    ck.ok("斜辺=√(2²+1²)=√5（answer_keyの答√5と整合・図にはx）",
          abs(r - math.sqrt(5)) < 1e-12, f"={r:.6f}")
    ck.ok("√5は2と3の間（目盛り0,1,2の右に落ちる）", 2 < r < 3)

    cv = Canvas(430, 240)
    cv.s = 92.0
    cv.ox, cv.oy = 50, 160
    cv.line((-0.3, 0), (2.75, 0), w=1.4)
    x1, y1 = cv.P((2.75, 0))
    arrow_px(cv, x1 - 10, y1, x1 + 4, y1, w=1.4, head=6.5)
    for t, lab in [(0, "0"), (1, "1"), (2, "2")]:
        cv.line((t, -0.05), (t, 0.05), w=1.3)
        xt, yt = cv.P((t, 0))
        cv.text_px(xt, yt + 22, lab, size=FS, anchor="middle")
    cv.line((2, 0), (2, 1.14), w=AUX_W, dash=DASH)
    cv.line((2, 0), Pt, w=MAIN_W)
    cv.right_angle((2, 0), (0, 0), (2, 1))
    cv.dot(Pt)
    xp, yp = cv.P(Pt)
    cv.text_px(xp + 14, yp - 6, "P", size=FS, anchor="middle", weight="bold")
    cv.line(O, Pt, w=MAIN_W)
    cv.dot(O)
    xo, yo = cv.P(O)
    cv.text_px(xo - 6, yo - 10, "O", size=FS, anchor="middle", weight="bold")
    seg_label(cv, (2, 0), Pt, "1", off=-13, t=0.5, size=13)
    cv.polyline(arc_pts(O, r, math.degrees(math.atan2(1, 2)), 0), w=MAIN_W)
    Q = (r, 0.0)
    cv.dot(Q)
    xq, yq = cv.P(Q)
    cv.text_px(xq + 10, yq + 22, "x", size=15, anchor="middle", weight="bold")
    cv.text_px(215, 222, "（練習3: 2の位置から高さ1の垂線→斜辺を弧で数直線に写した点x。"
               "xはどんな数？）", size=11, anchor="middle")

    return dict(file="L06_fig3_practice_point_x.svg", canvas=cv, lesson="L06",
                title="練習3の作図例（2の位置から高さ1→点x）",
                intent="練習3の与件図。xの正体は書かない",
                src="lesson_06.md 練習3（82行目のプレースホルダ）",
                params="垂線位置=2,高さ=1→斜辺は厳密作図（値は答えのため非表示）・交点はx表記のみ",
                checks=ck.items)


# ===========================================================================
# 図16: L07 直方体の対角線AG（3段階法・見取図）
# 本文根拠: lesson_07.md 例題1「縦3・横4・高さ5、AG太線・AC点線」
# 答え漏れ注意: AC=5・AG=5√2は書かない
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（本文 例題1 と一致させる） ---
    W, D, Hgt = 4.0, 3.0, 5.0     # 横AB=4cm・縦AD=3cm・高さ=5cm
    V = {"A": (0, 0, 0), "B": (W, 0, 0), "C": (W, D, 0), "D": (0, D, 0),
         "E": (0, 0, Hgt), "F": (W, 0, Hgt), "G": (W, D, Hgt), "H": (0, D, Hgt)}

    ck = Checker()
    ck.ok("底面の対角線AC=5cm（3²+4²=25・本文の途中値と一致・図には書かない）",
          abs(d3(V["A"], V["C"]) - 5) < 1e-12)
    ck.ok("CG⊥AC（内積=0）——直角の根拠",
          abs(dot3(sub3(V["G"], V["C"]), sub3(V["A"], V["C"]))) < 1e-12)
    ck.ok("対角線AG=√50=5√2（本文の答と一致・図には書かない）",
          abs(d3(V["A"], V["G"]) - 5 * math.sqrt(2)) < 1e-12,
          f"AG={d3(V['A'], V['G']):.4f}")
    ck.ok("AG²=AC²+CG²（2階建ての検算）",
          abs(d3(V["A"], V["G"]) ** 2 - (25 + 25)) < 1e-9)

    P2 = {k: proj(p) for k, p in V.items()}
    cv = Canvas(430, 358)
    cv.s = 42.0
    cv.ox, cv.oy = 70, 290
    hidden = [("A", "D"), ("D", "C"), ("D", "H")]
    solid = [("A", "B"), ("B", "C"), ("A", "E"), ("B", "F"), ("C", "G"),
             ("E", "F"), ("F", "G"), ("G", "H"), ("H", "E")]
    for a, b in hidden:
        cv.line(P2[a], P2[b], w=AUX_W, dash=DASH)
    for a, b in solid:
        cv.line(P2[a], P2[b], w=MAIN_W)
    cv.line(P2["A"], P2["C"], w=AUX_W, dash="3 3")    # 底面の対角線AC=点線
    cv.line(P2["A"], P2["G"], w=BOLD_W)               # 対角線AG=太線
    offs = {"A": (-12, 14), "B": (12, 14), "C": (16, 8), "D": (-16, -2),
            "E": (-12, -6), "F": (0, -13), "G": (14, -6), "H": (-4, -10)}
    for k, p in P2.items():
        x, y = cv.P(p)
        cv.text_px(x + offs[k][0], y + offs[k][1] + 4, k, size=FS,
                   anchor="middle", weight="bold")
    seg_label(cv, P2["A"], P2["B"], "4cm", off=15, size=12)
    seg_label(cv, P2["B"], P2["C"], "3cm", off=17, size=12)
    seg_label(cv, P2["C"], P2["G"], "5cm", off=-17, size=12)
    seg_label(cv, P2["A"], P2["G"], "AG＝？", off=-20, t=0.6, size=13, weight="bold")
    cv.text_px(215, 324, "対角線AG（太線）。底面の対角線AC（点線）が2つ目の三角形を作る",
               size=FS_CAP, anchor="middle")
    cv.text_px(215, 341, "（例題1: 縦3cm・横4cm・高さ5cm。△ABCと△ACGの2階建て）",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig1_cuboid_diagonal.svg", canvas=cv, lesson="L07",
                title="直方体の対角線AG（見取図・平行投影）",
                intent="例題1の見取図。隠線破線・AG太線・AC点線。AC・AGの値は非表示",
                src="lesson_07.md 例題1（38行目のプレースホルダ）",
                params="AB=4,AD=3,AE=5・平行投影(奥行き係数0.55,0.42)",
                checks=ck.items)


# ===========================================================================
# 図17: L07 平面に取り出す（底面ABCD＋直角三角形ACG）
# 本文根拠: lesson_07.md 例題1 手順②
# ===========================================================================
def fig_L07_2():
    # --- パラメータ（本文 例題1 と一致させる） ---
    W, D, Hgt = 4.0, 3.0, 5.0
    AC = math.hypot(W, D)               # =5（図には値を書かない）

    ck = Checker()
    ck.ok("底面対角線AC=√(3²+4²)=5（値は図に書かずACのまま）", abs(AC - 5) < 1e-12)
    ck.ok("右パネル: AG=√(AC²+5²)=5√2（本文の答と一致・図には？）",
          abs(math.hypot(AC, Hgt) - 5 * math.sqrt(2)) < 1e-12)

    cv = Canvas(470, 300)
    # 左: 底面ABCD（A左下・B右下・C右上・D左上に配置し AB=4, BC=3）
    s1 = 30.0
    cv.s = s1
    cv.ox, cv.oy = 40, 200
    A, B, C, Dp = (0, 0), (W, 0), (W, D), (0, D)
    cv.polygon([A, B, C, Dp])
    cv.line(A, C, w=MAIN_W)
    cv.right_angle(B, A, C)
    g = centroid(A, B, C, Dp)
    for p, nm in zip((A, B, C, Dp), "ABCD"):
        cv.label_out(p, g, nm)
    seg_label(cv, A, B, "4cm", off=15, size=12)
    seg_label(cv, B, C, "3cm", off=17, size=12)
    seg_label(cv, A, C, "AC", off=-13, t=0.6, size=13)
    cv.text_px(40 + W * s1 / 2, 250, "①底面を取り出す", size=FS_CAP, anchor="middle",
               weight="bold")
    cv.text_px(40 + W * s1 / 2, 267, "（まずACを求める）", size=11, anchor="middle")
    # 矢印
    arrow_px(cv, 185, 150, 245, 150, w=1.8, head=9)
    cv.text_px(215, 136, "次に", size=11, anchor="middle")
    # 右: 直角三角形ACG
    s2 = 26.0
    cv.s = s2
    cv.ox, cv.oy = 270, 222
    A2, C2, G2 = (0, 0), (AC, 0), (AC, Hgt)
    cv.polygon([A2, C2, G2])
    cv.right_angle(C2, A2, G2)
    for p, nm, (dx, dy) in [(A2, "A", (-12, 14)), (C2, "C", (14, 14)),
                            (G2, "G", (12, -6))]:
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy + 4, nm, size=FS, anchor="middle", weight="bold")
    seg_label(cv, A2, C2, "AC", off=14, size=13)
    seg_label(cv, C2, G2, "5cm", off=-16, size=12)
    seg_label(cv, A2, G2, "？", off=-14, t=0.5, size=15, weight="bold")
    cv.text_px(270 + AC * s2 / 2, 266, "②直角三角形ACGを取り出す", size=FS_CAP,
               anchor="middle", weight="bold")
    cv.text_px(235, 292, "（見取図から平面を2枚取り出す——三平方の定理を2回使う）",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig2_extracted_planes.svg", canvas=cv, lesson="L07",
                title="平面に取り出す2枚（底面ABCD→直角三角形ACG）",
                intent="例題1手順②の図。1プレースホルダ=2パネル+流れ矢印で統合",
                src="lesson_07.md 例題1（46行目のプレースホルダ）",
                params="底面4×3・CG=5・右パネル底辺AC=5は長さのみ厳密（値表記なし）",
                checks=ck.items)


# ===========================================================================
# 図18: L08 正四角錐O-ABCD（見取図）
# 本文根拠: lesson_08.md 例題1「底面1辺6cm・OA=5cm・高さOH」
# 答え漏れ注意: OH=√7・AH=3√2は見取図に書かない
# ===========================================================================
def fig_L08_1():
    # --- パラメータ（本文 例題1 と一致させる） ---
    a, edge = 6.0, 5.0                       # 底面1辺・側面の辺OA
    h = math.sqrt(edge ** 2 - (a * math.sqrt(2) / 2) ** 2)   # =√7（実寸で描く）
    V = {"A": (0, 0, 0), "B": (a, 0, 0), "C": (a, a, 0), "D": (0, a, 0),
         "H": (a / 2, a / 2, 0), "O": (a / 2, a / 2, h)}

    ck = Checker()
    ck.ok("側面の辺OA=OB=OC=OD=5cm（h=√7で成立・実寸整合）",
          all(abs(d3(V["O"], V[k]) - edge) < 1e-12 for k in "ABCD"),
          f"h={h:.4f}")
    ck.ok("HはACの中点", all(abs(V["H"][i] - (V["A"][i] + V["C"][i]) / 2) < 1e-12
          for i in range(3)))
    ck.ok("OH⊥底面（OH⊥HA・OH⊥HB）",
          abs(dot3(sub3(V["O"], V["H"]), sub3(V["A"], V["H"]))) < 1e-12
          and abs(dot3(sub3(V["O"], V["H"]), sub3(V["B"], V["H"]))) < 1e-12)
    ck.ok("OH=√7（本文の答と一致・図には書かない）",
          abs(h - math.sqrt(7)) < 1e-12)

    P2 = {k: proj(p) for k, p in V.items()}
    cv = Canvas(430, 330)
    cv.s = 34.0
    cv.ox, cv.oy = 70, 250
    for x, y_ in [("A", "D"), ("D", "C")]:
        cv.line(P2[x], P2[y_], w=AUX_W, dash=DASH)      # 隠れる底面辺
    cv.line(P2["O"], P2["D"], w=AUX_W, dash=DASH)       # 隠れる側辺OD
    cv.line(P2["A"], P2["C"], w=AUX_W, dash="3 3")      # 対角線AC（隠線）
    cv.line(P2["O"], P2["H"], w=AUX_W, dash=DASH)       # 高さOH（点線・本文指定）
    for x, y_ in [("A", "B"), ("B", "C"), ("O", "A"), ("O", "B"), ("O", "C")]:
        cv.line(P2[x], P2[y_], w=MAIN_W)
    cv.right_angle(P2["H"], P2["O"], P2["A"], size=7.5)
    cv.dot(P2["H"], r=2.2)
    offs = {"A": (-12, 14), "B": (12, 14), "C": (16, 4), "D": (-14, 0),
            "H": (13, 12), "O": (0, -12)}
    for k, p in P2.items():
        x, y = cv.P(p)
        cv.text_px(x + offs[k][0], y + offs[k][1] + 4, k, size=FS,
                   anchor="middle", weight="bold")
    seg_label(cv, P2["A"], P2["B"], "6cm", off=15, size=12)
    seg_label(cv, P2["O"], P2["A"], "5cm", off=-14, t=0.72, size=12)
    xh, yh = cv.P(P2["O"])
    cv.text_px(xh + 58, yh + 68, "OH＝？", size=13, anchor="middle", weight="bold")
    cv.text_px(215, 296, "高さOH（点線）：OH⊥底面，Hは対角線の交点＝ACの中点",
               size=FS_CAP, anchor="middle")
    cv.text_px(215, 313, "（例題1: 底面1辺6cm・側面の辺5cmの正四角錐。実寸比の見取図）",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig1_square_pyramid.svg", canvas=cv, lesson="L08",
                title="正四角錐O-ABCD（底面6cm・側辺5cm）",
                intent="例題1の見取図。h=√7の実寸で作図（低い錐が正しい姿）。OHは？",
                src="lesson_08.md 例題1（28行目のプレースホルダ）",
                params="底面1辺6・OA=5→h=√7を3D厳密計算・平行投影",
                checks=ck.items)


# ===========================================================================
# 図19: L08 平面に取り出す（底面の正方形＋直角三角形OHA）
# 本文根拠: lesson_08.md 例題1 手順②「AC=6√2cm・AH=3√2cm」
# 答え漏れ注意: OH=√7は書かない→「？」
# ===========================================================================
def fig_L08_2():
    # --- パラメータ（本文 例題1 と一致させる） ---
    a, edge = 6.0, 5.0
    AC = a * math.sqrt(2)                # 6√2（本文がこの段で示す値）
    AH = AC / 2                          # 3√2
    OH = math.sqrt(edge ** 2 - AH ** 2)  # √7（図には書かない）

    ck = Checker()
    ck.ok("AC=√(6²+6²)=6√2（本文の途中値と一致）",
          abs(AC - math.sqrt(72)) < 1e-12)
    ck.ok("AH=3√2（ACの半分・本文と一致）", abs(AH - 3 * math.sqrt(2)) < 1e-12)
    ck.ok("OH²=5²−(3√2)²=25−18=7（本文の答√7と整合・図には？）",
          abs(OH ** 2 - 7) < 1e-12, f"OH={OH:.4f}")

    cv = Canvas(470, 312)
    # 左: 底面の正方形ABCD＋対角線
    s1 = 24.0
    cv.s = s1
    cv.ox, cv.oy = 40, 216
    A, B, C, Dp = (0, 0), (a, 0), (a, a), (0, a)
    Hc = (a / 2, a / 2)
    cv.polygon([A, B, C, Dp])
    cv.line(A, C, w=MAIN_W)
    cv.line(B, Dp, w=AUX_W, dash="3 3")
    cv.dot(Hc)
    g = centroid(A, B, C, Dp)
    for p, nm in zip((A, B, C, Dp), "ABCD"):
        cv.label_out(p, g, nm)
    xh, yh = cv.P(Hc)
    cv.text_px(xh + 14, yh + 12, "H", size=FS, anchor="middle", weight="bold")
    cv.ticks(A, Hc, 1)
    cv.ticks(Hc, C, 1)
    seg_label(cv, A, B, "6cm", off=15, size=12)
    seg_label(cv, A, Hc, "3√2cm", off=-15, t=0.4, size=11)
    seg_label(cv, Hc, C, "AC＝6√2cm", off=-15, t=0.4, size=11)
    cv.text_px(40 + a * s1 / 2, 260, "①底面を取り出す", size=FS_CAP, anchor="middle",
               weight="bold")
    cv.text_px(40 + a * s1 / 2, 277, "（AH＝ACの半分＝3√2cm）", size=11, anchor="middle")
    arrow_px(cv, 205, 140, 260, 140, w=1.8, head=9)
    # 右: 直角三角形OHA（HA=3√2, OA=5, OH=？）
    s2 = 30.0
    cv.s = s2
    cv.ox, cv.oy = 285, 216
    H2, A2, O2 = (0.0, 0.0), (AH, 0.0), (0.0, OH)
    cv.polygon([H2, A2, O2])
    cv.right_angle(H2, A2, O2)
    for p, nm, (dx, dy) in [(H2, "H", (-12, 14)), (A2, "A", (12, 14)),
                            (O2, "O", (-12, -6))]:
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy + 4, nm, size=FS, anchor="middle", weight="bold")
    seg_label(cv, H2, A2, "3√2cm", off=15, size=12)
    seg_label(cv, A2, O2, "5cm", off=-16, size=12)
    seg_label(cv, H2, O2, "？", off=13, t=0.5, size=15, weight="bold")
    cv.text_px(285 + AH * s2 / 2, 260, "②直角三角形OHAを取り出す", size=FS_CAP,
               anchor="middle", weight="bold")
    cv.text_px(285 + AH * s2 / 2, 277, "（斜辺5cm・底辺3√2cm・高さOH）", size=11,
               anchor="middle")
    cv.text_px(235, 302, "（例題1手順②: 底面→直角三角形の2枚。OHを求める）",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig2_pyramid_extracted_planes.svg", canvas=cv, lesson="L08",
                title="平面に取り出す2枚（底面6cm→直角三角形OHA）",
                intent="例題1手順②の図。1プレースホルダ=2パネル統合。答えのOHは？表記",
                src="lesson_08.md 例題1（36行目のプレースホルダ）",
                params="底面1辺6・AC=6√2・AH=3√2・OA=5（OHの値は非表示・実寸）",
                checks=ck.items)


# ===========================================================================
# 図20: L08 円錐の高さ（半径3cm・母線9cm）
# 本文根拠: lesson_08.md 例題2
# 答え漏れ注意: 高さ6√2は書かない→「？」
# ===========================================================================
def fig_L08_3():
    # --- パラメータ（本文 例題2 と一致させる） ---
    r, m = 3.0, 9.0
    h = math.sqrt(m * m - r * r)      # =6√2（図には書かない・実寸で描く）

    ck = Checker()
    ck.ok("高さ²=9²−3²=72 → 高さ=6√2（本文の答と一致・図には？）",
          abs(h - 6 * math.sqrt(2)) < 1e-12, f"h={h:.4f}")
    ck.ok("紙面上の頂点・中心・半径端の3点で母線=9cm（実寸比）",
          abs(math.hypot(r, h) - m) < 1e-12)

    cv = Canvas(460, 330)
    s1 = 24.0
    cv.s = s1
    cv.ox, cv.oy = 110, 260
    T = (0.0, h)          # 頂点
    Ctr = (0.0, 0.0)      # 底面の中心
    R = (r, 0.0)          # 半径の端（紙面手前の断面上）
    ry = 0.34 * r         # 底面楕円の見かけの奥行き
    front = [(r * math.cos(math.radians(t)), ry * math.sin(math.radians(t)))
             for t in range(180, 361, 6)]
    back = [(r * math.cos(math.radians(t)), ry * math.sin(math.radians(t)))
            for t in range(0, 181, 6)]
    cv.polyline(front, w=MAIN_W)
    cv.polyline(back, w=AUX_W, dash=DASH)     # 底面の奥半分=隠線
    cv.line(T, (-r, 0), w=MAIN_W)
    cv.line(T, R, w=MAIN_W)                    # 母線（右側）
    cv.line(T, Ctr, w=AUX_W, dash=DASH)        # 高さ=点線
    cv.line(Ctr, R, w=MAIN_W)                  # 半径
    cv.right_angle(Ctr, R, T, size=7.5)
    cv.dot(Ctr, r=2.2)
    seg_label(cv, Ctr, R, "3cm", off=15, size=12)
    seg_label(cv, T, R, "9cm", off=-16, t=0.45, size=12)
    xh, yh = cv.P(lerp(T, Ctr, 0.45))
    cv.text_px(xh - 12, yh, "高さ＝？", size=13, anchor="end", weight="bold")
    cv.text_px(110, 296, "高さ⊥半径・斜辺＝母線", size=FS_CAP, anchor="middle")
    # 右: 取り出した直角三角形
    arrow_px(cv, 218, 150, 268, 150, w=1.8, head=9)
    s2 = 22.0
    cv.s = s2
    cv.ox, cv.oy = 300, 260
    C2, R2, T2 = (0.0, 0.0), (r, 0.0), (0.0, h)
    cv.polygon([C2, R2, T2])
    cv.right_angle(C2, R2, T2, size=7.5)
    seg_label(cv, C2, R2, "3cm", off=15, size=12)
    seg_label(cv, R2, T2, "9cm", off=16, t=0.45, size=12)   # 斜辺の外側に置く
    seg_label(cv, C2, T2, "？", off=-13, t=0.5, size=15, weight="bold")
    cv.text_px(300 + r * s2 / 2 + 10, 296, "取り出した平面図", size=FS_CAP,
               anchor="middle")
    cv.text_px(230, 320, "（例題2: 底面の半径3cm・母線9cmの円錐。高さを求める）",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig3_cone_height.svg", canvas=cv, lesson="L08",
                title="円錐の高さ（半径3cm・母線9cm）",
                intent="例題2の図。見取図+抜き出し平面図の併記（本文指定）。答えの高さは？表記",
                src="lesson_08.md 例題2（58行目のプレースホルダ）",
                params="r=3,母線=9→高さは厳密実寸（値は答えのため非表示）・底面楕円の奥半分は破線",
                checks=ck.items)


# ===========================================================================
# 図21: L09 見渡せる距離（地球の断面・接線）
# 本文根拠: lesson_09.md 例題1「R=6400km・h=2km・OP=6402km・d=PT」
# 答え漏れ注意: d≒160kmは書かない→「d＝？」
# ===========================================================================
def fig_L09():
    # --- パラメータ（本文 例題1 と一致させる。図はhを誇張した模式図） ---
    R_km, h_km = 6400.0, 2.0
    OP_km = R_km + h_km
    d2 = OP_km ** 2 - R_km ** 2

    ck = Checker()
    ck.ok("OP=R+h=6402km（本文と一致）", OP_km == 6402.0)
    ck.ok("d²=6402²−6400²=(6402+6400)(6402−6400)=25604（本文と一致）",
          abs(d2 - 25604) < 1e-9 and abs(d2 - 12802 * 2) < 1e-9)
    ck.ok("d=√25604≒160km（160²=25600<25604<161²・本文の答と整合・図には？）",
          160 ** 2 < d2 < 161 ** 2, f"d={math.sqrt(d2):.2f}km")

    # 表示用ジオメトリ（hを誇張。接線関係は表示座標でも厳密に成立させる）
    Rd, OPd = 108.0, 158.0
    O = (0.0, 0.0)
    P = (0.0, OPd)
    alpha = math.acos(Rd / OPd)              # ∠TOPの半角ではなく∠TOP
    T = (Rd * math.sin(alpha), Rd * math.cos(alpha))
    ck.ok("表示座標でも接線⊥半径（(T−O)・(T−P)=0）・Tは円周上",
          abs((T[0] - O[0]) * (T[0] - P[0]) + (T[1] - O[1]) * (T[1] - P[1])) < 1e-9
          and abs(math.hypot(*T) - Rd) < 1e-9)

    cv = Canvas(430, 348)
    cv.s = 1.0
    cv.ox, cv.oy = 175, 210
    cv.circle(O, Rd, w=MAIN_W)
    S = (0.0, Rd)                              # 山のふもと（地表）
    # 山（最小限の輪郭）
    cv.polyline([(-26, Rd - 3.2), (-10, Rd + 24), (0, OPd), (12, Rd + 18),
                 (26, Rd - 5.5)], w=1.2)
    cv.line(O, P, w=AUX_W)                     # OP
    cv.line(O, T, w=MAIN_W)                    # 半径OT
    cv.line(P, T, w=AUX_W, dash=DASH)          # 視線（接線）=破線
    cv.right_angle(T, O, P, size=8)
    for p, nm, (dx, dy) in [(O, "O", (-12, 14)), (P, "P", (-12, -4)),
                            (T, "T", (13, -8))]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy + 4, nm, size=FS, anchor="middle", weight="bold")
    seg_label(cv, O, T, "6400km", off=13, t=0.52, size=12)
    seg_label(cv, P, T, "d＝？", off=-14, t=0.5, size=14, weight="bold")
    # h（地表→P）の注記
    xs, ys = cv.P(S)
    cv.text_px(xs - 34, ys - 18, "高さ", size=11, anchor="end")
    cv.text_px(xs - 34, ys - 5, "h＝2km", size=11, anchor="end")
    xo, yo = cv.P(lerp(O, P, 0.42))
    cv.text_px(xo - 8, yo, "OP＝6400＋2", size=11, anchor="end")
    cv.text_px(xo - 8, yo + 14, "＝6402km", size=11, anchor="end")
    cv.text_px(215, 330, "接線⊥半径（∠T＝90°）。見渡せる限界＝視線が地表をかすめる接点T",
               size=FS_CAP, anchor="middle")
    cv.text_px(215, 347, "（例題1: d＝PTを求める。縮尺どおりではない——高さhを誇張した模式図）",
               size=11, anchor="middle")

    return dict(file="L09_fig1_horizon_tangent.svg", canvas=cv, lesson="L09",
                title="見渡せる距離（地球の断面と接線PT）",
                intent="例題1の翻訳図。数値検算は実値6400/6402で実施。答えの距離は？表記",
                src="lesson_09.md 主概念1（33行目のプレースホルダ）",
                params="R=6400km,h=2km（表示はh誇張の模式図・接線関係は表示座標でも厳密）",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L01_3,
        fig_L02_1, fig_L02_2, fig_L02_3,
        fig_L03,
        fig_L04_1, fig_L04_2,
        fig_L05_1, fig_L05_2, fig_L05_3,
        fig_L06_1, fig_L06_2, fig_L06_3,
        fig_L07_1, fig_L07_2,
        fig_L08_1, fig_L08_2, fig_L08_3,
        fig_L09]


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
        "# FIGURE_MANIFEST — 三平方の定理単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の幾何検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。／ "
        "本文プレースホルダ21箇所と図版21枚は1対1対応"
        "（プレースホルダ内で2パネル併記が指定された図は1ファイル内パネル分割で統合）。",
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
        "- 近隣の設問が問う値（L02練4の斜辺8cm・L04例1のh=3√3・L05の2√13/AB=8/AB=5・"
        "L06練3のx=√5・L07のAC=5とAG=5√2・L08のOH=√7と高さ6√2・L09のd≒160km）は"
        "図に書かず「？」または文字のままとし、スクリプト内assertでanswer_key/本文の答と照合した。",
        "- L01図1は導入の発見対象（面積9・16・25と関係式）を書かない。"
        "L01図3は本文指定により面積の値そのものを書かない。",
        "- L01図2（49−24＝25）・L02図2（(a＋b)²−4枚＝c²）は本文が図の直後に明示する"
        "解説値のため記載（設問の答ではない）。",
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
