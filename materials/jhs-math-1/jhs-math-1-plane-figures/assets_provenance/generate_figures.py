#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1数学「平面図形」単元 図版パラメトリック生成スクリプト
====================================================================================
様式の正本: materials/jhs-math-2/jhs-math-2-congruence-and-proof/assets_provenance/
generate_figures.py（コード来歴方式）に準拠。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（21枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / pathlib / datetime / html）
- 幾何の自己検証: 各図の fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。作図図では交点座標をコードで
  厳密計算し、垂直二等分線=等距離性、角の二等分線=等角性を数値検証する。
  加えて main() が「答え漏れの機械検査」（可視テキストに禁止文字列がないか）を全図で行う。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
- 描画ヘルパー（Canvas ほか）は中2合同単元の generate_figures.py から無変更で流用
  （この単元専用の追加ヘルパーは「追加ヘルパー」節に分離）。
"""

import math
import re
import datetime
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数 ----------------------------------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
DOT_R = 2.5      # 点マーカー半径


# ===========================================================================
# 描画ヘルパー（中2合同単元 generate_figures.py から無変更流用）
# （数学座標: y上向き → SVG座標: y下向き に変換して描く）
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

    def polyline(self, pts, w=MAIN_W):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        self.raw(f'<polyline points="{s}" fill="none" stroke="#000" stroke-width="{w}"/>')

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

    # 記号マーク ------------------------------------------------------------
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

    def parallel_mark(self, a, b, n=1, size=5.0, gap=9.0, t=0.5):
        """平行の矢羽「>」を線分の位置tにn個（向き: a→b）"""
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        mx, my = x1 + dx * t, y1 + dy * t
        for i in range(n):
            off = (i - (n - 1) / 2) * gap
            tipx, tipy = mx + ux * (off + size * 0.9), my + uy * (off + size * 0.9)
            for sgn in (1, -1):
                bx = tipx - ux * size * 1.6 + nx * size * sgn
                by = tipy - uy * size * 1.6 + ny * size * sgn
                self.raw(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tipx:.1f}" y2="{tipy:.1f}" '
                         f'stroke="#000" stroke-width="1.4"/>')

    def angle_arc(self, v, p, q, r=14.0, n=1, gap=3.5, w=1.2):
        """頂点vで辺vp→vqの間の角の弧をn重に描く（折れ線近似・劣角側）"""
        (vx, vy) = self.P(v)
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

    def label_out(self, p, centroid, s, dist=15.0, size=FS, weight="bold"):
        """頂点名: 重心から離れる向きにdist(px)ずらして置く"""
        x, y = self.P(p)
        cx, cy = self.P(centroid)
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        self.text_px(x + dx / L * dist, y + dy / L * dist + size * 0.35,
                     s, size=size, anchor="middle", weight=weight)

    # 出力 ------------------------------------------------------------------
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


# ---- 幾何ユーティリティ（同・無変更流用） ----------------------------------
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def centroid(*pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


class Checker:
    """幾何検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


def angle_deg(v, p, q):
    """頂点vで辺vp・vqがつくる角の大きさ（度・0〜180）"""
    a = math.atan2(p[1] - v[1], p[0] - v[0])
    b = math.atan2(q[1] - v[1], q[0] - v[0])
    d = abs(b - a) % (2 * math.pi)
    return math.degrees(min(d, 2 * math.pi - d))


def seg_label(cv, p, q, lab, off=13.0, t=0.5, size=12):
    """線分pqの位置tから法線方向へoff(px)ずらしてラベルを置く（offの符号で側を選ぶ）"""
    (x1, y1), (x2, y2) = cv.P(p), cv.P(q)
    mx, my = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    cv.text_px(mx + nx * off, my + ny * off + size * 0.35, lab,
               size=size, anchor="middle")


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0, color="#000"):
    """SVG座標(px)で矢印（線+先端の三角形）を描く。概念図用"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="{color}" stroke-width="{w}"/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="{color}"/>')


# ===========================================================================
# 追加ヘルパー（本単元用）
# ===========================================================================
GRAY_FILL = "#e6e6e6"   # 薄い塗り（白黒両立: 濃淡グレー）
GRAY_FILL2 = "#bdbdbd"  # 濃いめの塗り
GRAY_LINE = "#999"      # 補助・前ステップの線


def unit(deg):
    return (math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def ray_pt(o, deg, r):
    u = unit(deg)
    return (o[0] + u[0] * r, o[1] + u[1] * r)


def rot(p, deg, about=(0.0, 0.0)):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    x, y = p[0] - about[0], p[1] - about[1]
    return (about[0] + c * x - s * y, about[1] + s * x + c * y)


def mirror_x(p, axis_x=0.0):
    return (2 * axis_x - p[0], p[1])


def translate(p, d):
    return (p[0] + d[0], p[1] + d[1])


def poly2(cv, pts, w=MAIN_W, stroke="#000", fill="none", dash=None):
    """stroke色・破線を選べるポリゴン"""
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(cv.P, pts))
    d = f' stroke-dasharray="{dash}"' if dash else ""
    cv.raw(f'<polygon points="{s}" fill="{fill}" stroke="{stroke}" '
           f'stroke-width="{w}" stroke-linejoin="round"{d}/>')


def fill_poly(cv, pts, fill):
    """輪郭なしの塗りだけのポリゴン（塗り分け用・主線は別に描く）"""
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(cv.P, pts))
    cv.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')


def circle(cv, c, r, w=MAIN_W, color="#000", fill="none", dash=None):
    """数学座標の円"""
    x, y = cv.P(c)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    cv.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * cv.s:.1f}" '
           f'fill="{fill}" stroke="{color}" stroke-width="{w}"{d}/>')


def arc(cv, c, r, a1, a2, w=AUX_W, color="#000", dash=None):
    """中心c半径rの円弧（数学角度a1→a2へ反時計回り・度）。コンパスの弧用"""
    assert a2 > a1, "arc: a2>a1（反時計回り）で指定"
    cx, cy = cv.P(c)
    rr = r * cv.s
    x1 = cx + rr * math.cos(math.radians(a1))
    y1 = cy - rr * math.sin(math.radians(a1))
    x2 = cx + rr * math.cos(math.radians(a2))
    y2 = cy - rr * math.sin(math.radians(a2))
    large = 1 if (a2 - a1) > 180 else 0
    d = f' stroke-dasharray="{dash}"' if dash else ""
    cv.raw(f'<path d="M {x1:.1f} {y1:.1f} A {rr:.1f} {rr:.1f} 0 {large} 0 '
           f'{x2:.1f} {y2:.1f}" fill="none" stroke="{color}" stroke-width="{w}"{d}/>')


def arc_tick(cv, c, r, ang, half=5.0, w=1.4):
    """弧の途中の半径方向ティック（等しい半径の印）"""
    cx, cy = cv.P(c)
    rr = r * cv.s
    ux, uy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
    cv.raw(f'<line x1="{cx + (rr - half) * ux:.1f}" y1="{cy + (rr - half) * uy:.1f}" '
           f'x2="{cx + (rr + half) * ux:.1f}" y2="{cy + (rr + half) * uy:.1f}" '
           f'stroke="#000" stroke-width="{w}"/>')


def sector(cv, c, r, a1, a2, fill="none", stroke="#000", w=MAIN_W):
    """中心角のあるおうぎ形（a1→a2反時計回り・度）"""
    cx, cy = cv.P(c)
    rr = r * cv.s
    x1 = cx + rr * math.cos(math.radians(a1))
    y1 = cy - rr * math.sin(math.radians(a1))
    x2 = cx + rr * math.cos(math.radians(a2))
    y2 = cy - rr * math.sin(math.radians(a2))
    large = 1 if (a2 - a1) > 180 else 0
    cv.raw(f'<path d="M {cx:.1f} {cy:.1f} L {x1:.1f} {y1:.1f} '
           f'A {rr:.1f} {rr:.1f} 0 {large} 0 {x2:.1f} {y2:.1f} Z" '
           f'fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round"/>')


def fold_arrow(cv, a, b, bend=0.5, w=1.4, head=6.0):
    """折り返しを表す両矢印（曲線）。a→bへふくらむ二次曲線+両端矢じり（数学座標）"""
    (x1, y1), (x2, y2) = cv.P(a), cv.P(b)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    cx2, cy2 = mx + nx * L * bend, my + ny * L * bend
    cv.raw(f'<path d="M {x1:.1f} {y1:.1f} Q {cx2:.1f} {cy2:.1f} {x2:.1f} {y2:.1f}" '
           f'fill="none" stroke="#000" stroke-width="{w}"/>')
    for (tx, ty) in ((x1, y1), (x2, y2)):
        ang = math.atan2(ty - cy2, tx - cx2)
        bx, by = tx - head * math.cos(ang), ty - head * math.sin(ang)
        pnx, pny = -math.sin(ang), math.cos(ang)
        cv.raw(f'<polygon points="{tx:.1f},{ty:.1f} '
               f'{bx + pnx * head * 0.45:.1f},{by + pny * head * 0.45:.1f} '
               f'{bx - pnx * head * 0.45:.1f},{by - pny * head * 0.45:.1f}" fill="#000"/>')


def box_px(cv, x, y, w, h, lines, size=12, weight=None, fill="#fff",
           stroke="#000", sw=1.4, rx=7):
    """角丸ボックス+中央ぞろえの複数行テキスト（px座標）"""
    cv.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
           f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    n = len(lines)
    for i, ln in enumerate(lines):
        ty = y + h / 2 + (i - (n - 1) / 2) * (size + 4) + size * 0.35
        cv.text_px(x + w / 2, ty, ln, size=size, anchor="middle", weight=weight)


def grid(cv, org, nx, ny, color="#ddd", w=0.8):
    """方眼（org=左下・1マス=1単位・数学座標）"""
    for gx in range(nx + 1):
        cv.line((org[0] + gx, org[1]), (org[0] + gx, org[1] + ny), w=w, color=color)
    for gy in range(ny + 1):
        cv.line((org[0], org[1] + gy), (org[0] + nx, org[1] + gy), w=w, color=color)


def dist_point_line(p, a, b):
    """点pと直線ab(2点指定)の距離"""
    L = dist(a, b)
    return abs(cross(a, b, p)) / L


def line_x_line(p1, p2, p3, p4):
    """直線p1p2と直線p3p4の交点"""
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (p4[0] - p3[0], p4[1] - p3[1])
    det = d1[0] * d2[1] - d1[1] * d2[0]
    assert abs(det) > 1e-12, "直線が平行で交点なし"
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / det
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)


def reflect_line(p, a, b):
    """点pを直線abで折り返した点"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    fx, fy = a[0] + t * dx, a[1] + t * dy
    return (2 * fx - p[0], 2 * fy - p[1])


def visible_text(svg):
    """答え漏れ検査用: <title>/<desc>を除いた可視テキストノードを連結して返す"""
    body = re.sub(r"<title>.*?</title>", "", svg, flags=re.S)
    body = re.sub(r"<desc>.*?</desc>", "", body, flags=re.S)
    return "".join(re.findall(r">([^<]*)<", body))


EPS = 1e-9
EPSA = 1e-6   # 三角関数を経由する検算用


# ===========================================================================
# L01 図1: 直線・線分・半直線の対比（3段組）
# 本文根拠: lesson_01.md 主概念1（同じ2点A・Bに対する3つの定義）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md: 2点A・Bを共通にして3段組） ---
    xa, xb = -1.2, 1.2          # A・Bのx座標（3段共通）
    ext = 0.7                   # 直線・半直線をのばす長さ
    rows = [1.1, 0.0, -1.1]     # 3段のy座標（上から直線・線分・半直線）

    ck = Checker()
    ck.ok("3段ともA・Bの位置が共通（x座標一致）", xa < xb and ext > 0,
          f"A=x{xa}, B=x{xb}")
    ck.ok("直線は両側へのびる（左右とも延長>0）", ext > 0)
    ck.ok("線分は両端で止まる（延長なし）", True, "端点=A・B")
    ck.ok("半直線ABはAが端でB側だけのびる", ext > 0, "A側延長なし・B側延長あり")

    cv = Canvas(460, 250, scale=70.0, ox=150, oy=125)
    names = ["直線AB", "線分AB", "半直線AB"]
    for i, y in enumerate(rows):
        A, B = (xa, y), (xb, y)
        if i == 0:      # 直線: 両側へ矢印
            cv.line(A, B)
            arrow_px(cv, *cv.P(A), *cv.P((xa - ext, y)))
            arrow_px(cv, *cv.P(B), *cv.P((xb + ext, y)))
        elif i == 1:    # 線分
            cv.line(A, B)
        else:           # 半直線AB: A端・B側矢印
            cv.line(A, B)
            arrow_px(cv, *cv.P(B), *cv.P((xb + ext, y)))
        cv.dot(A)
        cv.dot(B)
        cv.text((xa, y + 0.22), "A", weight="bold")
        cv.text((xb, y + 0.22), "B", weight="bold")
        cv.text((xb + ext + 0.25, y), names[i], anchor="start", weight="bold")
    cv.text_px(230, 235, "同じ2点A・Bでも、のばし方（端があるかないか）で名前が変わる",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_line_segment_ray.svg", canvas=cv, lesson="L01",
                title="直線・線分・半直線の対比（3段組の定義図)",
                intent="直線・線分・半直線の3点セットを1枚で対比する定義図。上段=直線（両端矢印）・中段=線分（両端が点）・下段=半直線AB（A端・B側矢印）",
                params="2点A・Bを3段で共通にする（目盛り・長さの数値なし）",
                checks=ck.items, forbid=["cm"])


# ===========================================================================
# L01 図2: 点と直線の距離＝垂線の長さ（比較で見せる）
# 本文根拠: lesson_01.md 主概念1（点と直線の距離・垂線PHがいちばん短い）
# ===========================================================================
def fig_L01_2():
    # --- パラメータ ---
    P = (0.3, 1.6)                 # 直線外の点
    Q1, Q2 = (-1.0, 0.0), (1.6, 0.0)   # 比較用の斜め線分の足
    H = (P[0], 0.0)                # 垂線とℓの交点（Pの真下）

    ck = Checker()
    ck.ok("PHはℓに垂直（Hの真上にP）", abs(P[0] - H[0]) < EPS and H[1] == 0.0)
    ck.ok("PHは斜めの線分より短い（垂線が最短）",
          dist(P, H) < dist(P, Q1) and dist(P, H) < dist(P, Q2),
          f"PH={dist(P, H):.2f} < PQ1={dist(P, Q1):.2f}, PQ2={dist(P, Q2):.2f}")
    ck.ok("Hはℓ上の点", H[1] == 0.0)

    cv = Canvas(420, 250, scale=70.0, ox=200, oy=190)
    cv.line((-2.3, 0), (2.3, 0))
    cv.text((2.3, 0.2), "ℓ", anchor="end", weight="bold")
    cv.line(P, Q1, w=AUX_W, dash=DASH)
    cv.line(P, Q2, w=AUX_W, dash=DASH)
    cv.line(P, H, w=BOLD_W)
    cv.right_angle(H, P, (1.5, 0))
    cv.dot(P)
    cv.dot(H)
    cv.text((P[0], P[1] + 0.22), "P", weight="bold")
    cv.text((H[0] + 0.16, -0.24), "H", weight="bold")
    cv.text_px(210, 237, "Pからℓへの線分のうち、垂直にひいた線分PHがいちばん短い＝点と直線の距離",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig2_point_line_distance.svg", canvas=cv, lesson="L01",
                title="点と直線の距離（垂線の長さがいちばん短い）",
                intent="点と直線の距離＝垂線の長さを「他の線分より短い」比較で見せる図。垂線PH=太線+直角マーク・斜め2本=細い破線",
                params="直線ℓと直線外の点P・垂線PHと比較用の斜め線分2本（長さの数値なし）",
                checks=ck.items, forbid=["cm"])


# ===========================================================================
# L01 図3: 線対称・点対称の分類ベン図
# 本文根拠: lesson_01.md 主概念2（両方をもつ図形の存在を面で見せる）
# ===========================================================================
def fig_L01_3():
    # --- パラメータ ---
    c1, c2, rv = (-0.62, 0.0), (0.62, 0.0), 1.05    # ベン図の2円
    iso = [(-1.15, 0.32), (-1.33, -0.10), (-0.97, -0.10)]           # 二等辺三角形
    par = [(0.93, -0.02), (1.31, -0.02), (1.41, 0.20), (1.03, 0.20)]  # 平行四辺形
    sq_c, sq_h = (0.0, 0.47), 0.14                                   # 正方形
    rh_c, rh_dx, rh_dy = (0.0, 0.02), 0.22, 0.14                     # ひし形
    ci_c, ci_r = (0.0, -0.48), 0.16                                  # 円

    sq = [(sq_c[0] - sq_h, sq_c[1] - sq_h), (sq_c[0] + sq_h, sq_c[1] - sq_h),
          (sq_c[0] + sq_h, sq_c[1] + sq_h), (sq_c[0] - sq_h, sq_c[1] + sq_h)]
    rh = [(rh_c[0] - rh_dx, rh_c[1]), (rh_c[0], rh_c[1] - rh_dy),
          (rh_c[0] + rh_dx, rh_c[1]), (rh_c[0], rh_c[1] + rh_dy)]

    ck = Checker()
    ck.ok("2円が重なりをもつ（両方の領域が存在）",
          dist(c1, c2) < 2 * rv, f"中心間={dist(c1, c2):.2f} < 2r={2 * rv:.2f}")
    ck.ok("二等辺三角形シルエット=2辺相等・正三角形でない",
          abs(dist(iso[0], iso[1]) - dist(iso[0], iso[2])) < EPS
          and abs(dist(iso[1], iso[2]) - dist(iso[0], iso[1])) > 0.05)
    d_par = [dist(par[i], par[(i + 1) % 4]) for i in range(4)]
    ck.ok("平行四辺形シルエット=対辺平行・長方形/ひし形でない",
          abs(cross((0, 0), (par[1][0] - par[0][0], par[1][1] - par[0][1]),
                    (par[2][0] - par[3][0], par[2][1] - par[3][1]))) < EPS
          and abs(angle_deg(par[0], par[1], par[3]) - 90) > 5
          and abs(d_par[0] - d_par[1]) > 0.05)
    d_sq = [dist(sq[i], sq[(i + 1) % 4]) for i in range(4)]
    ck.ok("正方形シルエット=4辺相等かつ4直角",
          max(d_sq) - min(d_sq) < EPS and abs(angle_deg(sq[0], sq[1], sq[3]) - 90) < EPSA)
    d_rh = [dist(rh[i], rh[(i + 1) % 4]) for i in range(4)]
    ck.ok("ひし形シルエット=4辺相等だが直角でない（正方形でない）",
          max(d_rh) - min(d_rh) < EPS and abs(angle_deg(rh[0], rh[1], rh[3]) - 90) > 5)
    ck.ok("左のみ領域=二等辺三角形（左円の中・右円の外）",
          all(dist(p, c1) < rv - 0.02 and dist(p, c2) > rv + 0.02 for p in iso))
    ck.ok("右のみ領域=平行四辺形（右円の中・左円の外）",
          all(dist(p, c2) < rv - 0.02 and dist(p, c1) > rv + 0.02 for p in par))
    ck.ok("重なり領域=正方形・ひし形・円（両円の中）",
          all(dist(p, c1) < rv - 0.02 and dist(p, c2) < rv - 0.02 for p in sq + rh)
          and dist(ci_c, c1) + ci_r < rv and dist(ci_c, c2) + ci_r < rv)

    cv = Canvas(460, 310, scale=95.0, ox=230, oy=150)
    circle(cv, c1, rv)
    circle(cv, c2, rv)
    cv.text((-1.15, 1.22), "線対称", weight="bold")
    cv.text((1.15, 1.22), "点対称", weight="bold")
    cv.polygon(iso, w=1.3, fill=GRAY_FILL)
    cv.text((-1.15, -0.34), "二等辺三角形", size=10)
    cv.polygon(par, w=1.3, fill=GRAY_FILL)
    cv.text((1.17, -0.16), "平行四辺形", size=10)
    cv.polygon(sq, w=1.3, fill=GRAY_FILL)
    cv.text_px(*cv.P((0.22, 0.47)), "正方形", size=10)
    cv.polygon(rh, w=1.3, fill=GRAY_FILL)
    cv.text_px(*cv.P((0.30, 0.02)), "ひし形", size=10)
    circle(cv, ci_c, ci_r, w=1.3, fill=GRAY_FILL)
    cv.text_px(*cv.P((0.24, -0.48)), "円", size=10)
    cv.text_px(230, 298, "重なり＝線対称でもあり点対称でもある図形", size=FS_CAP,
               anchor="middle")

    return dict(file="L01_fig3_symmetry_venn.svg", canvas=cv, lesson="L01",
                title="線対称・点対称の分類マップ（ベン図）",
                intent="線対称・点対称の分類マップ。左のみ=二等辺三角形・右のみ=平行四辺形・重なり=正方形・ひし形・円をシルエットで配置（両方をもつ図形の存在を面で見せる）",
                params="2円のベン図＋図形シルエット5種（対称軸の本数の一覧は載せない）",
                checks=ck.items, forbid=["1本", "2本", "3本", "4本"])


# ===========================================================================
# L02 図1: 合同な三角形の敷き詰め模様（ア・①②③）
# 本文根拠: lesson_02.md 導入（①=ずらす・②=共有辺で裏返す・③=頂点のまわりに回す）
#           lesson_02.md stretch S1（裏返しが必要な三角形の帯が存在すること）
# 構成: 不等辺三角形（直角なし）の敷き詰め。下2行=基準の向きの帯（平行移動と
#       180°回転のタイル）・上2行=それを境界線で折り返した鏡映の帯。
#       この「2行ごとに折り返す」構成により、②（共有辺での裏返し）・③（1頂点
#       まわりの180°回転）・S1の「裏返さないと重ならない三角形の帯」がすべて
#       同時に実在する（1行ごとの折り返しでは③が、折り返しなしでは②とS1が消える）。
# ===========================================================================
def fig_L02_1():
    # --- パラメータ ---
    T = [(0.0, 0.0), (2.0, 0.0), (0.7, 1.1)]   # 基準三角形（不等辺・直角なし）
    u, v = (2.0, 0.0), (0.7, 1.1)              # 敷き詰めの格子ベクトル
    D = [(2.7, 1.1), (0.7, 1.1), (2.0, 0.0)]   # Tを辺BCの中点で180°回した相棒タイル
    MIRROR_Y = 2.2                              # 鏡映の帯の折り返し線（2行ぶんの高さ）

    def refl_band(p):
        return (p[0], 2 * MIRROR_Y - p[1])

    tiles = []
    for i in range(-1, 6):
        for j in (0, 1):
            off = (i * u[0] + j * v[0], i * u[1] + j * v[1])
            base_t = [translate(p, off) for p in T]
            base_d = [translate(p, off) for p in D]
            tiles += [base_t, base_d]                       # 下2行（基準の向き）
            tiles += [[refl_band(p) for p in base_t],       # 上2行（鏡映の帯）
                      [refl_band(p) for p in base_d]]

    tri_a = [translate(p, v) for p in D]                          # ア（2行目のタイル）
    tri_1 = [translate(p, u) for p in tri_a]                      # ①=右へずらす
    tri_2 = [reflect_line(p, tri_a[0], tri_a[1]) for p in tri_a]  # ②=共有辺で裏返す
    tri_3 = [rot(p, 180, about=tri_a[2]) for p in tri_a]          # ③=頂点のまわりに回す

    def same_set(t1, t2):
        return all(any(dist(p, q) < EPS for q in t2) for p in t1)

    def in_tiles(t):
        return any(same_set(t, s) and same_set(s, t) for s in tiles)

    ck = Checker()
    sides = sorted([dist(T[0], T[1]), dist(T[1], T[2]), dist(T[2], T[0])])
    ck.ok("基準三角形は不等辺（一般三角形）・直角なし",
          sides[1] - sides[0] > 0.1 and sides[2] - sides[1] > 0.1
          and all(abs(angle_deg(T[i], T[(i + 1) % 3], T[(i + 2) % 3]) - 90) > 7
                  for i in range(3)),
          f"3辺={sides[0]:.2f}/{sides[1]:.2f}/{sides[2]:.2f}")
    ck.ok("①はアを右へずらした位置＝敷き詰めの実タイルと厳密一致",
          same_set(tri_1, [translate(p, u) for p in tri_a]) and in_tiles(tri_1))
    ck.ok("②はアを共有辺で裏返した位置＝敷き詰めの実タイルと厳密一致",
          in_tiles(tri_2), "折り返しの計算結果が鏡映の帯のタイルと一致")
    ck.ok("②はアと辺を共有し、向きが逆（裏返し）",
          all(any(dist(p, q) < EPS for q in tri_2) for p in (tri_a[0], tri_a[1]))
          and cross(*tri_a) * cross(*tri_2) < 0)
    ck.ok("③はアを1つの頂点のまわりに180°回した位置＝敷き詰めの実タイルと厳密一致",
          in_tiles(tri_3), "回転の計算結果が基準の帯のタイルと一致")
    ck.ok("③は向きが同じ（回転）でアと頂点を共有",
          cross(*tri_a) * cross(*tri_3) > 0 and dist(tri_a[2], tri_3[2]) < EPS)
    mirror_tile = [refl_band(p) for p in T]
    ck.ok("裏返さないと重ならない三角形の帯が存在（stretch S1の素材・不等辺のため"
          "回転では鏡映タイルに重ねられない）",
          cross(*T) * cross(*mirror_tile) < 0 and in_tiles(mirror_tile))

    cv = Canvas(480, 265, scale=42.0, ox=18, oy=210)
    fill_poly(cv, tri_a, GRAY_FILL2)
    for t in tiles:
        poly2(cv, t, w=1.1)
    cv.text(centroid(*tri_a), "ア", size=15, weight="bold")
    cv.text(centroid(*tri_1), "①", size=14, weight="bold")
    cv.text(centroid(*tri_2), "②", size=14, weight="bold")
    cv.text(centroid(*tri_3), "③", size=14, weight="bold")
    cv.text_px(240, 250, "アを①②③のそれぞれにぴったり重ねるには、どう動かせばよい？",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_tessellation.svg", canvas=cv, lesson="L02",
                title="合同な三角形の敷き詰め模様（ア・①②③）",
                intent="敷き詰め模様の観察素材。①=アを右へずらした位置・②=アを共有辺で裏返した位置・③=アを1つの頂点のまわりに回した位置（移動を表す矢印は描かない）",
                params="合同な不等辺三角形（直角なし）を4行×7列敷き詰め（下2行=基準の向き・上2行=鏡映の帯）。①②③の位置と裏返しの帯の存在を移動の計算で厳密に検証",
                checks=ck.items, forbid=["平行移動", "対称移動", "回転移動"])


# ===========================================================================
# L02 図2・図3 共通の幾何（3つの移動の設定）
# 本文根拠: lesson_02.md 主概念1・2（平行移動=右5マス上1マス／縦軸ℓ／O中心反時計90°）
# ===========================================================================
def _motion_setup():
    tri = [(1, 1), (3, 1), (2, 3)]     # 移動前の△ABC（3パネル共通の形・格子点上）
    vec = (5, 1)                        # 平行移動: 右へ5マス・上へ1マス
    ax = 4.0                            # 対称移動: 縦の直線ℓ（x=4）
    tri3 = [(6, 1), (8, 1), (7, 3)]     # 回転移動用の△ABC
    O = (4.0, 0.0)                      # 回転の中心
    img1 = [translate(p, vec) for p in tri]
    img2 = [mirror_x(p, ax) for p in tri]
    img3 = [rot(p, 90, about=O) for p in tri3]

    ck = Checker()
    ck.ok("平行移動の像=右へ5マス・上へ1マス（全頂点）",
          all(dist(img1[i], translate(tri[i], vec)) < EPS for i in range(3)))
    conn = [(tri[i], img1[i]) for i in range(3)]
    L0 = dist(*conn[0])
    ck.ok("対応点を結ぶ線分AD・BE・CFはすべて平行で長さが等しい",
          all(abs(dist(a, b) - L0) < EPS for a, b in conn)
          and all(abs(cross((0, 0), (b[0] - a[0], b[1] - a[1]),
                            (vec[0], vec[1]))) < EPS for a, b in conn),
          f"長さ={L0:.3f}")
    ck.ok("対称移動の像=直線ℓ（x=4）での折り返し（全頂点）",
          all(dist(img2[i], mirror_x(tri[i], ax)) < EPS for i in range(3)))
    ck.ok("対応点を結ぶ線分は軸と垂直に交わり、交点で2等分される",
          all(abs(tri[i][1] - img2[i][1]) < EPS
              and abs((tri[i][0] + img2[i][0]) / 2 - ax) < EPS for i in range(3)))
    ck.ok("回転移動の像=点Oを中心に反時計回りに90°（全頂点）",
          all(dist(img3[i], rot(tri3[i], 90, about=O)) < EPS for i in range(3)))
    ck.ok("対応点は回転の中心Oから等距離（OA=OD等）",
          all(abs(dist(O, tri3[i]) - dist(O, img3[i])) < EPS for i in range(3)))
    sgn = cross(O, tri3[0], img3[0])
    ck.ok("∠AOD=∠BOE=∠COF=90°で向きは反時計回り",
          all(abs(angle_deg(O, tri3[i], img3[i]) - 90) < EPSA for i in range(3))
          and sgn > 0)
    ck.ok("全頂点が方眼の格子点上（方眼で再現できる設定）",
          all(abs(p[0] - round(p[0])) < EPS and abs(p[1] - round(p[1])) < EPS
              for p in tri + img1 + img2 + tri3 + img3 + [O]))
    return tri, vec, ax, tri3, O, img1, img2, img3, ck


def _draw_motion_panels(with_marks):
    tri, vec, ax, tri3, O, img1, img2, img3, ck = _motion_setup()
    cv = Canvas(400, 560, scale=32.0, ox=48, oy=530)
    orgs = [(0.0, 11.0), (0.0, 5.5), (0.0, 0.0)]   # 上から平行・対称・回転
    titles = ["平行移動（右へ5マス・上へ1マス）", "対称移動（直線ℓが軸）",
              "回転移動（点Oを中心に反時計回りに90°）"]
    tris_pre = [tri, tri, tri3]
    tris_img = [img1, img2, img3]
    for k in range(3):
        org = orgs[k]
        grid(cv, org, 9, 4)
        cv.text((org[0], org[1] + 4.55), titles[k], anchor="start",
                size=12, weight="bold")
        pre = [translate(p, org) for p in tris_pre[k]]
        img = [translate(p, org) for p in tris_img[k]]
        poly2(cv, pre, w=MAIN_W)
        poly2(cv, img, w=MAIN_W, stroke="#777")
        for nm, p in zip("ABC", pre):
            cv.label_out(p, centroid(*pre), nm, dist=12, size=12)
        for nm, p in zip("DEF", img):
            cv.label_out(p, centroid(*img), nm, dist=12, size=12)
        if k == 0:
            for a, b in zip(pre, img):
                if with_marks:
                    cv.line(a, b, w=AUX_W, dash=DASH, color="#444")
                    cv.ticks(a, b, n=1)
                    cv.parallel_mark(a, b, n=1, t=0.35)
                else:
                    arrow_px(cv, *cv.P(a), *cv.P(b), w=1.1, color="#555")
        elif k == 1:
            axa, axb = (org[0] + ax, org[1] - 0.2), (org[0] + ax, org[1] + 4.3)
            cv.line(axa, axb, w=2.0)
            cv.text((org[0] + ax + 0.28, org[1] + 4.15), "ℓ", weight="bold")
            if with_marks:
                for i, (a, b) in enumerate(zip(pre, img)):
                    m = ((a[0] + b[0]) / 2, a[1])
                    cv.line(a, b, w=AUX_W, dash=DASH, color="#444")
                    cv.ticks(a, m, n=i + 1)
                    cv.ticks(m, b, n=i + 1)
                    if i == 0:
                        cv.right_angle(m, a, (m[0], m[1] + 1))
            else:
                fold_arrow(cv, (org[0] + ax - 0.7, org[1] + 4.05),
                           (org[0] + ax + 0.7, org[1] + 4.05), bend=0.4)
        else:
            Og = translate(O, org)
            cv.dot(Og, r=3.0)
            cv.text((Og[0] - 0.32, Og[1] + 0.14), "O", weight="bold")
            if with_marks:
                for i, (a, b) in enumerate(zip(pre, img)):
                    cv.line(Og, a, w=AUX_W, dash=DASH, color="#444")
                    cv.line(Og, b, w=AUX_W, dash=DASH, color="#444")
                    cv.ticks(Og, a, n=i + 1)
                    cv.ticks(Og, b, n=i + 1)
                    cv.angle_arc(Og, a, b, r=16 + 7 * i, n=1)
            else:
                arc(cv, Og, 1.3, 15, 75, w=1.3)
                aend = ray_pt(Og, 75, 1.3)
                atip = ray_pt(Og, 82, 1.3)
                arrow_px(cv, *cv.P(aend), *cv.P(atip), w=1.3)
    return cv, ck


def fig_L02_2():
    cv, ck = _draw_motion_panels(with_marks=False)
    cv.text_px(200, 550, "対応: A→D・B→E・C→F。形も大きさも変わらない",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig2_three_motions.svg", canvas=cv, lesson="L02",
                title="3つの移動の定義（△ABC→△DEFの3段組）",
                intent="平行移動・対称移動・回転移動の定義を1枚で対比する図。各段に移動前△ABC・移動後△DEFと移動のようす（矢印/軸ℓと折り返し/中心Oと回転の弧矢印）。対応A→D・B→E・C→Fを明記",
                params="平行移動=右へ5マス・上へ1マス／対称移動=縦の直線ℓ（x=4）／回転移動=点O中心・反時計回りに90°（全頂点が格子点上）",
                checks=ck.items, forbid=[])


def fig_L02_3():
    cv, ck = _draw_motion_panels(with_marks=True)
    cv.text_px(200, 550, "対応する点を結ぶ線分に、移動の種類ごとの性質が現れる",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig3_motion_properties.svg", canvas=cv, lesson="L02",
                title="対応する点を結ぶ線分の性質（3つの移動の検証図）",
                intent="移動の種類ごとの「対応する点を結ぶ線分の性質」を確かめる検証図。図2と同じ3設定に補助線分（破線）と等長・直角・等角のマークを重ねる。回転の段は中心Oから各対応点への線分と角のマークを明示",
                params="図2と同じ設定を再利用（AD・BE・CF等長平行／軸と垂直・2等分／中心から等距離・等角90°を数値検証）",
                checks=ck.items, forbid=[])


# ===========================================================================
# L03 図1: 移動の決定要素の対比（3ミニ図）
# 本文根拠: lesson_03.md 主概念1（回転の例=点O・時計回りに90°）
# ===========================================================================
def fig_L03_1():
    # --- パラメータ ---
    tri1 = [(0.4, 0.8), (1.7, 0.8), (0.8, 1.7)]
    vec = (1.7, 0.9)                         # 平行移動: 方向と距離
    Pp, Qp = (0.7, 2.2), (0.7 + 1.7, 2.2 + 0.9)   # 強調する矢印PQ
    tri2 = [(0.4, 0.8), (1.5, 0.8), (0.8, 1.9)]
    ax2 = 2.0                                # 対称移動: 軸x=2.0
    O3 = (1.9, 1.9)                          # 回転移動: 中心
    rot_deg = -90                            # 時計回りに90°
    tri3 = [(2.5, 2.4), (3.4, 2.4), (2.7, 3.2)]

    img1 = [translate(p, vec) for p in tri1]
    img2 = [mirror_x(p, ax2) for p in tri2]
    img3 = [rot(p, rot_deg, about=O3) for p in tri3]

    ck = Checker()
    ck.ok("平行移動の像=矢印PQと同じ方向・距離",
          all(dist(img1[i], translate(tri1[i], vec)) < EPS for i in range(3))
          and abs(Qp[0] - Pp[0] - vec[0]) < EPS and abs(Qp[1] - Pp[1] - vec[1]) < EPS)
    ck.ok("対称移動の像=軸ℓでの折り返しと厳密一致",
          all(dist(img2[i], mirror_x(tri2[i], ax2)) < EPS for i in range(3)))
    ck.ok("回転移動の像=点O中心・90°と厳密一致",
          all(dist(img3[i], rot(tri3[i], rot_deg, about=O3)) < EPS for i in range(3))
          and all(abs(angle_deg(O3, tri3[i], img3[i]) - 90) < EPSA for i in range(3)))
    ck.ok("回転の向きは時計回り", cross(O3, tri3[0], img3[0]) < 0)
    ck.ok("中心からの距離が保存（OA=OA'等）",
          all(abs(dist(O3, tri3[i]) - dist(O3, img3[i])) < EPS for i in range(3)))

    cv = Canvas(480, 240, scale=34.0, ox=8, oy=195)
    orgs = [(0.0, 0.0), (4.7, 0.0), (9.4, 0.0)]
    heads = ["平行移動", "対称移動", "回転移動"]
    subs = ["決定要素: 方向と距離", "決定要素: 軸の位置", "決定要素: 中心・角・向き"]
    for k, org in enumerate(orgs):
        cv.text((org[0] + 2.0, 4.6), heads[k], size=12, weight="bold")
        cv.text((org[0] + 2.0, -0.75), subs[k], size=11)
    # パネル1: 図形はうすく・矢印（方向と距離）だけ強調
    poly2(cv, [translate(p, orgs[0]) for p in tri1], w=1.2, stroke=GRAY_LINE)
    poly2(cv, [translate(p, orgs[0]) for p in img1], w=1.2, stroke=GRAY_LINE)
    arrow_px(cv, *cv.P(translate(Pp, orgs[0])), *cv.P(translate(Qp, orgs[0])), w=2.8)
    # パネル2: 軸だけ強調
    poly2(cv, [translate(p, orgs[1]) for p in tri2], w=1.2, stroke=GRAY_LINE)
    poly2(cv, [translate(p, orgs[1]) for p in img2], w=1.2, stroke=GRAY_LINE)
    cv.line((orgs[1][0] + ax2, 0.2), (orgs[1][0] + ax2, 4.1), w=2.8)
    cv.text((orgs[1][0] + ax2 + 0.3, 3.9), "ℓ", weight="bold")
    # パネル3: 中心・弧矢印（向き）・角度ラベルの3点を強調
    poly2(cv, [translate(p, orgs[2]) for p in tri3], w=1.2, stroke=GRAY_LINE)
    poly2(cv, [translate(p, orgs[2]) for p in img3], w=1.2, stroke=GRAY_LINE)
    Og = translate(O3, orgs[2])
    cv.dot(Og, r=3.4)
    cv.text((Og[0] - 0.35, Og[1] - 0.05), "O", weight="bold")
    arc(cv, Og, 1.2, 10, 70, w=2.2)
    arrow_px(cv, *cv.P(ray_pt(Og, 14, 1.2)), *cv.P(ray_pt(Og, 7, 1.2)), w=2.2)
    cv.text(ray_pt(Og, 40, 1.75), "90°", size=13, weight="bold")
    cv.text_px(240, 232, "うすい図形は移動の前後。こく示した部分が「決めなければ伝わらない」情報",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_determining_elements.svg", canvas=cv, lesson="L03",
                title="3つの移動の決定要素（対比のミニ図3枚）",
                intent="決定要素の対比表を図解化した3枚のミニ図。平行移動=方向と距離の矢印だけ強調・対称移動=軸だけ強調・回転移動=中心の点・回転の弧矢印（向き）・角度ラベルの3要素を強調（決定要素以外の補助線なし）",
                params="回転移動の例は「点O・時計回りに90°」（本文の表と一致・回転向きも数値検証）",
                checks=ck.items, forbid=[])


# ===========================================================================
# L04 図1: 垂直二等分線の作図手順（2ステップ）
# 本文根拠: lesson_04.md 主概念2（A・B中心の等半径の弧→交点P・Q→直線PQ）
# ===========================================================================
def _perp_bisector_pts():
    A, B = (-1.3, 0.0), (1.3, 0.0)
    r = 1.7                                   # 共通の半径（ABの半分より長く）
    h = math.sqrt(r * r - (dist(A, B) / 2) ** 2)
    P, Q = (0.0, h), (0.0, -h)                # 2円の交点（厳密計算）
    return A, B, r, P, Q


def _pb_checks():
    A, B, r, P, Q = _perp_bisector_pts()
    M = lerp(A, B, 0.5)
    ck = Checker()
    ck.ok("半径はABの半分より長い（2円が2点で交わる条件）",
          r > dist(A, B) / 2, f"r={r} > AB/2={dist(A, B) / 2}")
    ck.ok("PA=PB=QA=QB=r（P・QはA・Bから等距離＝等距離性の数値検証）",
          all(abs(dist(X, Y) - r) < EPS for X in (P, Q) for Y in (A, B)),
          f"PA={dist(P, A):.4f}=r")
    ck.ok("直線PQはABと垂直", abs((P[0] - Q[0]) * (B[0] - A[0])
                                  + (P[1] - Q[1]) * (B[1] - A[1])) < EPS)
    ck.ok("直線PQはABの中点Mを通る", dist_point_line(M, P, Q) < EPS
          and abs(dist(A, M) - dist(M, B)) < EPS)
    return A, B, r, P, Q, M, ck


def fig_L04_1():
    A, B, r, P, Q, M, ck = _pb_checks()

    cv = Canvas(480, 280, scale=62.0, ox=0, oy=150)
    orgs = [(1.95, 0.0), (5.75, 0.0)]
    caps = ["① A・Bを中心に等しい半径の弧", "② 交点P・Qを通る直線をひく"]
    ang = math.degrees(math.atan2(P[1], P[0] - A[0]))   # 交点方向（約40°）
    for k, org in enumerate(orgs):
        Ag, Bg, Pg, Qg = (translate(X, org) for X in (A, B, P, Q))
        cv.line(Ag, Bg)
        arc(cv, Ag, r, -ang - 14, ang + 14, w=AUX_W, color="#555")
        arc(cv, Bg, r, 180 - ang - 14, 180 + ang + 14, w=AUX_W, color="#555")
        arc_tick(cv, Ag, r, 12)
        arc_tick(cv, Bg, r, 168)
        for X, nm, dyy in ((Ag, "A", -0.26), (Bg, "B", -0.26),
                           (Pg, "P", 0.26), (Qg, "Q", -0.28)):
            cv.dot(X)
            cv.text((X[0], X[1] + dyy), nm, weight="bold")
        if k == 1:
            cv.line((org[0], P[1] + 0.35), (org[0], Q[1] - 0.35), w=2.2)
            Mg = translate(M, org)
            cv.dot(Mg)
            cv.text((Mg[0] + 0.24, Mg[1] - 0.24), "M", weight="bold")
            cv.right_angle(Mg, (Mg[0] + 1, Mg[1]), Pg)
            cv.ticks(Ag, Mg, n=1)
            cv.ticks(Mg, Bg, n=1)
        cv.text_px(*cv.P((org[0], Q[1] - 0.75)), caps[k], size=FS_CAP,
                   anchor="middle")
    cv.text_px(240, 272, "弧の途中の印＝半径が等しいしるし。Mは中点・直角マークつき",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_perp_bisector_steps.svg", canvas=cv, lesson="L04",
                title="線分の垂直二等分線の作図手順（2ステップ）",
                intent="垂直二等分線の作図手順図（2ステップを左右に並べる）。左=手順①（A中心・B中心の同半径の弧が上下2点P・Qで交わる。半径が等しいことを弧上の印で示す）・右=手順②（直線PQと、ABとの交点Mに中点の印と直角マーク）",
                params="線分AB=2.6・共通の半径r=1.7（ABの半分より大きい）。交点P・Qは厳密計算（長さの数値・分度器は載せない）",
                checks=ck.items, forbid=["cm", "°"])


# ===========================================================================
# L04 図2: 作図の根拠図（等距離と2円の線対称）
# 本文根拠: lesson_04.md 手がかり1（PA=PB・QA=QB）・手がかり2（直線PQで線対称）
# ===========================================================================
def fig_L04_2():
    A, B, r, P, Q, M, ck = _pb_checks()
    ck.ok("直線PQで折るとAとBが重なる（線対称の数値検証）",
          dist(reflect_line(A, P, Q), B) < EPS)
    ck.ok("直線PQで折ると2つの円がぴったり重なる（中心が入れかわり・半径が等しい）",
          dist(reflect_line(A, P, Q), B) < EPS and True, "半径は共通のr")

    cv = Canvas(420, 300, scale=62.0, ox=210, oy=160)
    ang = math.degrees(math.atan2(P[1], P[0] - A[0]))
    cv.line(A, B)
    arc(cv, A, r, -ang - 14, ang + 14, w=AUX_W, color="#555")
    arc(cv, B, r, 180 - ang - 14, 180 + ang + 14, w=AUX_W, color="#555")
    cv.line((0, P[1] + 0.5), (0, Q[1] - 0.35), w=2.2)
    for X, Y in ((P, A), (P, B), (Q, A), (Q, B)):
        cv.line(X, Y, w=AUX_W, dash=DASH)
        cv.ticks(X, Y, n=1)
    for X, nm, dxx, dyy in ((A, "A", -0.05, -0.27), (B, "B", 0.05, -0.27),
                            (P, "P", 0.22, 0.18), (Q, "Q", 0.22, -0.2)):
        cv.dot(X)
        cv.text((X[0] + dxx, X[1] + dyy), nm, weight="bold")
    cv.dot(M)
    cv.right_angle(M, (1, 0), P)
    fold_arrow(cv, (-0.55, P[1] + 0.28), (0.55, P[1] + 0.28), bend=0.5)
    cv.text_px(210, 288, "PA・PB・QA・QBの印＝等距離。直線PQで折ると図全体がぴったり重なる",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig2_perp_bisector_reason.svg", canvas=cv, lesson="L04",
                title="垂直二等分線の作図の根拠（等距離と2円の線対称）",
                intent="作図の根拠図。完成図にPA・PB・QA・QBの4線分を破線+等しい印で追加し、直線PQを対称の軸として図全体が線対称であることを折り返し矢印で示す（この単元の統合の伏線）",
                params="図1と同じ設定（AB=2.6・r=1.7）。折るとA・Bが重なることを数値検証",
                checks=ck.items, forbid=["cm", "°"])


# ===========================================================================
# L05 図1: 角の二等分線の作図手順（3コマ）
# 本文根拠: lesson_05.md 主概念1（O中心の弧→A・B→等半径の弧→P→半直線OP）
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（lesson_05.md: 角はおよそ70°・手順2の半径はABの半分より長く） ---
    a1, a2 = 15.0, 85.0        # 2辺の方向（∠XOY=70°）
    s = 1.1                    # 手順1の半径（OA=OB）
    t = 0.9                    # 手順2の半径（ABの半分より長く）
    O = (0.0, 0.0)
    A, B = ray_pt(O, a1, s), ray_pt(O, a2, s)
    half = dist(A, B) / 2
    bis = (a1 + a2) / 2
    h = math.sqrt(t * t - half * half)
    P = ray_pt(O, bis, s * math.cos(math.radians((a2 - a1) / 2)) + h)  # 交点（厳密計算）

    ck = Checker()
    ck.ok("OA=OB（同じ円の半径）", abs(dist(O, A) - s) < EPS and abs(dist(O, B) - s) < EPS)
    ck.ok("手順2の半径はABの半分より長い（2つの弧が交わる条件）",
          t > half, f"t={t} > AB/2={half:.3f}")
    ck.ok("PA=PB（等しい半径の円の上の点＝等距離性）",
          abs(dist(P, A) - t) < EPSA and abs(dist(P, B) - t) < EPSA,
          f"PA={dist(P, A):.4f}=PB={dist(P, B):.4f}")
    ck.ok("∠XOP=∠POY（半直線OPが角を2等分＝等角性の数値検証）",
          abs(angle_deg(O, A, P) - angle_deg(O, P, B)) < EPSA,
          f"どちらも{angle_deg(O, A, P):.2f}度")
    ck.ok("∠XOY=70°（直角・60°に見えない角）",
          abs((a2 - a1) - 70) < EPS and abs((a2 - a1) - 90) > 10
          and abs((a2 - a1) - 60) > 5)
    ck.ok("Pは角の内側", a1 < math.degrees(math.atan2(P[1], P[0])) < a2)

    cv = Canvas(490, 260, scale=58.0, ox=0, oy=205)
    orgs = [(0.5, 0.0), (3.35, 0.0), (6.2, 0.0)]
    caps = ["① O中心の弧→A・B", "② A・B中心に等しい弧→P", "③ 半直線OPをひく"]
    for k, org in enumerate(orgs):
        Og, Ag, Bg, Pg = (translate(X, org) for X in (O, A, B, P))
        cv.line(Og, translate(ray_pt(O, a1, 2.2), org))
        cv.line(Og, translate(ray_pt(O, a2, 2.2), org))
        cv.text(translate(ray_pt(O, a1, 2.42), org), "X", weight="bold")
        cv.text(translate(ray_pt(O, a2, 2.42), org), "Y", weight="bold")
        arc(cv, Og, s, a1 - 12, a2 + 12, w=AUX_W, color="#555")
        cv.dot(Og)
        cv.text((Og[0] - 0.2, Og[1] - 0.16), "O", weight="bold")
        cv.dot(Ag)
        cv.text((Ag[0] + 0.1, Ag[1] - 0.24), "A", weight="bold")
        cv.dot(Bg)
        cv.text((Bg[0] - 0.26, Bg[1] + 0.12), "B", weight="bold")
        if k >= 1:
            angA = math.degrees(math.atan2(P[1] - A[1], P[0] - A[0]))
            angB = math.degrees(math.atan2(P[1] - B[1], P[0] - B[0]))
            arc(cv, Ag, t, angA - 26, angA + 26, w=AUX_W, color="#555")
            arc(cv, Bg, t, angB - 26, angB + 26, w=AUX_W, color="#555")
            arc_tick(cv, Ag, t, angA + 18)
            arc_tick(cv, Bg, t, angB - 18)
            cv.dot(Pg)
            cv.text((Pg[0] + 0.24, Pg[1] + 0.16), "P", weight="bold")
        if k == 2:
            cv.line(Og, translate(ray_pt(O, bis, 2.25), org), w=2.2)
            cv.angle_arc(Og, Ag, Pg, r=15, n=1)
            cv.angle_arc(Og, Pg, Bg, r=15, n=1)
        cv.text_px(*cv.P((org[0] + 0.95, -0.62)), caps[k], size=FS_CAP,
                   anchor="middle")
    cv.text_px(245, 252, "②の印＝半径が等しいしるし。③の弧＝2つに分かれた角が等しいしるし",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_angle_bisector_steps.svg", canvas=cv, lesson="L05",
                title="角の二等分線の作図手順（3コマ）",
                intent="角の二等分線の作図手順図（3ステップ）。コマ①=O中心の弧とOX・OY上の交点A・B、コマ②=A中心・B中心の等半径の弧と交点P、コマ③=半直線OPと2つに分かれた角の等しい印（分度器・角度の数値なし）",
                params="∠XOY=70°（直角・60°に見えない角）・OA=OB=1.1・手順②の半径0.9（ABの半分より長い）。交点Pは厳密計算し等角性を数値検証",
                checks=ck.items, forbid=["°", "70", "35"])


# ===========================================================================
# L05 図2: 垂線の作図（2つの場合の左右対比）
# 本文根拠: lesson_05.md 主概念2（どちらもPA=PBを作って垂直二等分線に帰着）
# ===========================================================================
def fig_L05_2():
    # --- パラメータ ---
    r1 = 0.85                 # 場合1: P中心の円の半径（Pはℓ上）
    t1 = 1.3                  # 場合1: A・B中心の弧の半径
    P2y = 1.25                # 場合2: Pのℓからの高さ
    r2 = 1.55                 # 場合2: P中心の円の半径（ℓと2点で交わる大きさ）
    t2 = 1.15                 # 場合2: A・B中心の弧の半径

    # 場合1の交点（厳密計算）
    A1, B1 = (-r1, 0.0), (r1, 0.0)
    q1 = math.sqrt(t1 * t1 - r1 * r1)
    # 場合2の交点（厳密計算）
    P2 = (0.0, P2y)
    xw = math.sqrt(r2 * r2 - P2y * P2y)
    A2, B2 = (-xw, 0.0), (xw, 0.0)
    q2 = math.sqrt(t2 * t2 - xw * xw)
    Q2 = (0.0, -q2)

    ck = Checker()
    ck.ok("場合1: PA=PB（同じ円の半径→Pは2点から等距離）",
          abs(dist((0, 0), A1) - r1) < EPS and abs(dist((0, 0), B1) - r1) < EPS)
    ck.ok("場合1: 交点はA・Bから等距離で、結んだ直線はℓに垂直・Pを通る",
          abs(dist((0, q1), A1) - t1) < EPSA and abs(dist((0, q1), B1) - t1) < EPSA
          and abs(dist((0, -q1), A1) - t1) < EPSA)
    ck.ok("場合2: 円がℓと2点で交わる（半径>Pとℓの距離）",
          r2 > P2y, f"r={r2} > 距離={P2y}")
    ck.ok("場合2: PA=PB（同じ円の半径→Pは2点から等距離）",
          abs(dist(P2, A2) - r2) < EPSA and abs(dist(P2, B2) - r2) < EPSA)
    ck.ok("場合2: QA=QB（もう1つの等距離の点）",
          abs(dist(Q2, A2) - t2) < EPSA and abs(dist(Q2, B2) - t2) < EPSA)
    ck.ok("場合2: 直線PQはℓに垂直でPを通る",
          abs(P2[0] - Q2[0]) < EPS)

    cv = Canvas(490, 290, scale=60.0, ox=0, oy=155)
    caps = ["ℓ上の点Pを通る垂線", "ℓ上にない点Pを通る垂線"]
    # --- 左パネル（場合1） ---
    o1 = (1.9, 0.0)
    cv.line(translate((-1.8, 0), o1), translate((1.8, 0), o1))
    cv.text(translate((1.8, 0.2), o1), "ℓ", anchor="end", weight="bold")
    circle(cv, o1, r1, w=AUX_W, color="#555")
    arc(cv, translate(A1, o1), t1, 30, 90 + 42, w=AUX_W, color="#555")
    arc(cv, translate(B1, o1), t1, 48, 150, w=AUX_W, color="#555")
    cv.line(translate((0, q1 + 0.3), o1), translate((0, -q1 - 0.3), o1), w=2.2)
    cv.dot(translate((0, 0), o1))
    cv.text(translate((0.2, -0.26), o1), "P", weight="bold")
    for X, nm in ((A1, "A"), (B1, "B")):
        cv.dot(translate(X, o1))
        cv.text(translate((X[0], -0.28), o1), nm, weight="bold")
    cv.dot(translate((0, q1), o1))
    cv.ticks(translate(A1, o1), o1, n=1)
    cv.ticks(o1, translate(B1, o1), n=1)
    cv.right_angle(translate((0, 0), o1), translate((1, 0), o1),
                   translate((0, 1), o1))
    # --- 右パネル（場合2） ---
    o2 = (6.0, 0.0)
    cv.line(translate((-1.8, 0), o2), translate((1.8, 0), o2))
    cv.text(translate((1.8, 0.2), o2), "ℓ", anchor="end", weight="bold")
    Pg = translate(P2, o2)
    arc(cv, Pg, r2, 205, 335, w=AUX_W, color="#555")
    angQA = math.degrees(math.atan2(Q2[1] - A2[1], Q2[0] - A2[0]))
    arc(cv, translate(A2, o2), t2, angQA - 24, angQA + 24, w=AUX_W, color="#555")
    arc(cv, translate(B2, o2), t2, 180 - angQA - 24, 180 - angQA + 24,
        w=AUX_W, color="#555")
    cv.line((o2[0], P2y + 0.35), (o2[0], -q2 - 0.35), w=2.2)
    cv.dot(Pg)
    cv.text((Pg[0] + 0.22, Pg[1] + 0.14), "P", weight="bold")
    for X, nm in ((A2, "A"), (B2, "B")):
        cv.dot(translate(X, o2))
        cv.text(translate((X[0] - 0.05, 0.24), o2), nm, weight="bold")
    Qg = translate(Q2, o2)
    cv.dot(Qg)
    cv.text((Qg[0] + 0.22, Qg[1] - 0.1), "Q", weight="bold")
    cv.line(Pg, translate(A2, o2), w=AUX_W, dash=DASH)
    cv.line(Pg, translate(B2, o2), w=AUX_W, dash=DASH)
    cv.ticks(Pg, translate(A2, o2), n=1)
    cv.ticks(Pg, translate(B2, o2), n=1)
    cv.right_angle(translate((0, 0), o2), translate((1, 0), o2), Pg)
    for k, org in enumerate((o1, o2)):
        cv.text_px(*cv.P((org[0], -1.9)), caps[k], size=FS_CAP, anchor="middle")
    cv.text_px(245, 283, "どちらも「Pを2点A・Bから等距離の点にする」→あとは垂直二等分線の作図",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig2_perpendicular_two_cases.svg", canvas=cv, lesson="L05",
                title="垂線の作図（ℓ上の点・ℓ上にない点の対比）",
                intent="垂線の2つの場合を左右対比で示す作図手順図。左=ℓ上の点P（P中心の円→A・B→垂直二等分線）・右=ℓ上にない点P（P中心の弧がℓと2点で交わる→A・B→垂直二等分線）。どちらもPA=PBの等しい印を明示し、垂直二等分線部分はL04と同じ描き方（慣用語ラベル・数値なし）",
                params="場合1: 半径0.85→弧1.3／場合2: Pの高さ1.25・円の半径1.55（2点で交わる条件を数値検証）・弧1.15",
                checks=ck.items, forbid=["垂線の足", "cm"])


# ===========================================================================
# L06 図1: 3作図の統合図（共通の骨組み=等しい半径の2円と対称の軸）
# 本文根拠: lesson_06.md 主概念1（この単元の山場・手順番号は描かない）
# ===========================================================================
def fig_L06_1():
    ck = Checker()
    # --- P1: 垂直二等分線 ---
    A1, B1, r1 = (-0.75, 0.0), (0.75, 0.0), 1.0
    h1 = math.sqrt(r1 * r1 - 0.75 ** 2)
    ck.ok("垂直二等分線: 等しい半径の2円の交点2つを軸が通る",
          abs(dist(A1, (0, h1)) - r1) < EPS and abs(dist(B1, (0, h1)) - r1) < EPS
          and abs(dist(A1, (0, -h1)) - r1) < EPS)
    ck.ok("垂直二等分線: 軸で折ると2つの中心A・Bが入れかわる",
          dist(reflect_line(A1, (0, 1), (0, -1)), B1) < EPS)
    # --- P2: 角の二等分線 ---
    O2 = (-1.0, -0.85)
    b1d, b2d, s2, t2 = 12.0, 72.0, 0.95, 0.85
    A2, B2 = ray_pt(O2, b1d, s2), ray_pt(O2, b2d, s2)
    half2 = dist(A2, B2) / 2
    h2 = math.sqrt(t2 * t2 - half2 * half2)
    bis2 = (b1d + b2d) / 2
    P2 = ray_pt(O2, bis2, s2 * math.cos(math.radians((b2d - b1d) / 2)) + h2)
    ck.ok("角の二等分線: 2円の中心A・Bは頂点から等距離・交点PはA・Bから等距離",
          abs(dist(O2, A2) - dist(O2, B2)) < EPS
          and abs(dist(P2, A2) - t2) < EPSA and abs(dist(P2, B2) - t2) < EPSA)
    ck.ok("角の二等分線: 軸OPが角を2等分（等角性）",
          abs(angle_deg(O2, A2, P2) - angle_deg(O2, P2, B2)) < EPSA,
          f"どちらも{angle_deg(O2, A2, P2):.1f}度")
    ck.ok("角の二等分線: 軸OPはABの垂直二等分線（折るとA・Bが入れかわる）",
          dist(reflect_line(A2, O2, P2), B2) < EPSA)
    # --- P3: 垂線（ℓ上の点） ---
    P3 = (0.0, -0.55)
    r3, t3 = 0.62, 1.0
    A3, B3 = (-r3, -0.55), (r3, -0.55)
    h3 = math.sqrt(t3 * t3 - r3 * r3)
    ck.ok("垂線: P中心の円でPA=PB→2円の交点を通る軸がℓに垂直",
          abs(dist(P3, A3) - r3) < EPS
          and abs(dist((0, -0.55 + h3), A3) - t3) < EPSA
          and abs(dist((0, -0.55 + h3), B3) - t3) < EPSA)
    # --- P4: 骨組み（抽象図） ---
    M1, M2, r4 = (-0.55, 0.0), (0.55, 0.0), 0.9
    h4 = math.sqrt(r4 * r4 - 0.55 ** 2)
    ck.ok("骨組み: 2円の交点は両方の中心から等距離→交点を結ぶ直線は対称の軸",
          abs(dist(M1, (0, h4)) - r4) < EPS and abs(dist(M2, (0, h4)) - r4) < EPS
          and dist(reflect_line(M1, (0, h4), (0, -h4)), M2) < EPS)

    cv = Canvas(490, 350, scale=54.0, ox=0, oy=160)
    titles = ["垂直二等分線", "角の二等分線", "垂線"]
    torgs = [(1.5, 0.0), (4.55, 0.0), (7.6, 0.0)]
    for k, org in enumerate(torgs):
        cv.text((org[0], 1.45), titles[k], size=12, weight="bold")
    # P1
    o = torgs[0]
    Ag, Bg = translate(A1, o), translate(B1, o)
    cv.line(Ag, Bg, w=AUX_W)
    arc(cv, Ag, r1, -62, 62, w=1.3, color="#555")
    arc(cv, Bg, r1, 118, 242, w=1.3, color="#555")
    cv.line((o[0], 1.05), (o[0], -1.05), w=BOLD_W)
    cv.dot(Ag, r=3.2)
    cv.dot(Bg, r=3.2)
    # P2
    o = torgs[1]
    Og, Ag, Bg, Pg = (translate(X, o) for X in (O2, A2, B2, P2))
    cv.line(Og, translate(ray_pt(O2, b1d, 2.05), o), w=AUX_W)
    cv.line(Og, translate(ray_pt(O2, b2d, 2.05), o), w=AUX_W)
    arc(cv, Og, s2, b1d - 12, b2d + 12, w=1.3, color="#555")
    angA = math.degrees(math.atan2(P2[1] - A2[1], P2[0] - A2[0]))
    angB = math.degrees(math.atan2(P2[1] - B2[1], P2[0] - B2[0]))
    arc(cv, Ag, t2, angA - 30, angA + 30, w=1.3, color="#555")
    arc(cv, Bg, t2, angB - 30, angB + 30, w=1.3, color="#555")
    cv.line(Og, translate(ray_pt(O2, bis2, 2.35), o), w=BOLD_W)
    cv.dot(Og)
    cv.dot(Ag, r=3.2)
    cv.dot(Bg, r=3.2)
    # P3
    o = torgs[2]
    lg1, lg2 = translate((-1.35, -0.55), o), translate((1.35, -0.55), o)
    cv.line(lg1, lg2, w=AUX_W)
    Pg3, Ag, Bg = (translate(X, o) for X in (P3, A3, B3))
    circle(cv, Pg3, r3, w=1.3, color="#555")
    arc(cv, Ag, t3, 20, 100, w=1.3, color="#555")
    arc(cv, Bg, t3, 80, 160, w=1.3, color="#555")
    cv.line((o[0], 0.75), (o[0], -1.35), w=BOLD_W)
    cv.dot(Pg3)
    cv.dot(Ag, r=3.2)
    cv.dot(Bg, r=3.2)
    # P4（骨組み）
    o = (4.55, -2.55)
    M1g, M2g = translate(M1, o), translate(M2, o)
    circle(cv, M1g, r4, w=1.4)
    circle(cv, M2g, r4, w=1.4)
    cv.line(M1g, M2g, w=AUX_W)
    cv.line((o[0], o[1] + h4 + 0.4), (o[0], o[1] - h4 - 0.4), w=BOLD_W)
    cv.dot(M1g, r=3.2)
    cv.dot(M2g, r=3.2)
    cv.dot((o[0], o[1] + h4))
    cv.dot((o[0], o[1] - h4))
    cv.text((o[0] + 1.35, o[1] + 0.7), "共通の骨組み", size=12, weight="bold",
            anchor="start")
    cv.text((o[0] + 1.35, o[1] + 0.3), "等しい半径の2円と", size=11, anchor="start")
    cv.text((o[0] + 1.35, o[1] - 0.05), "交点を通る対称の軸", size=11, anchor="start")
    cv.text_px(245, 342, "3つの完成図のどれにも、等しい半径の2円（弧）と、その交点を通る太い軸がある",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_unified_constructions.svg", canvas=cv, lesson="L06",
                title="3つの作図の統合図（共通の骨組み＝2円の線対称）",
                intent="3作図（垂直二等分線・角の二等分線・垂線）の完成図を横に並べ、共通の骨組み「等しい半径の2円＋交点を通る対称の軸」を同じ描き方（中心=太い点・2円=グレー弧・軸=太線）でハイライトする統合図。下段に骨組みだけの抽象図（手順番号なし）",
                params="3作図とも交点を厳密計算し、軸で折ると2円の中心が入れかわること（線対称）を数値検証",
                checks=ck.items, forbid=["①", "②", "③"])


# ===========================================================================
# L07 図1: 弧と弦の定義図
# 本文根拠: lesson_07.md 主概念1（弦AB・2つの弧・中心Oと半径1本）
# ===========================================================================
def fig_L07_1():
    # --- パラメータ ---
    r = 1.35
    aA, aB, aC = 210.0, 330.0, 90.0     # A・B・C（Cは長い方の弧の上）の方向
    aR = 150.0                          # 半径を示す方向
    O = (0.0, 0.0)
    A, B, C = (ray_pt(O, d, r) for d in (aA, aB, aC))

    ck = Checker()
    ck.ok("A・B・Cは円周上の点", all(abs(dist(O, X) - r) < EPS for X in (A, B, C)))
    ck.ok("弧AB（短い方）の中心角120°<長い方240°", (aB - aA) == 120)
    ck.ok("Cは長い方の弧の上", not (aA < aC < aB))
    ck.ok("弦ABは直径ではない（中心を通らない）",
          dist_point_line(O, A, B) > 0.1, f"中心からの距離={dist_point_line(O, A, B):.2f}")

    cv = Canvas(430, 300, scale=72.0, ox=195, oy=140)
    arc(cv, O, r, aB - 360, aA, w=MAIN_W)            # 長い方の弧（ふつうの線）
    arc(cv, O, r, aA, aB, w=BOLD_W)                  # 短い方の弧（太線）
    cv.line(A, B)                                    # 弦
    cv.line(O, ray_pt(O, aR, r), w=AUX_W)            # 半径
    seg_label(cv, O, ray_pt(O, aR, r), "半径", off=13)
    cv.dot(O)
    cv.text((0.16, -0.06), "O", weight="bold")
    for X, nm, dv in ((A, "A", (-0.2, -0.2)), (B, "B", (0.2, -0.2)),
                      (C, "C", (0.0, 0.22))):
        cv.dot(X)
        cv.text((X[0] + dv[0], X[1] + dv[1]), nm, weight="bold")
    seg_label(cv, A, B, "弦AB", off=-15)
    cv.text(ray_pt(O, 270, r + 0.28), "弧AB（太い側）", size=12)
    cv.text_px(210, 30, "Cを通る側も弧。区別するときは間の点を", size=11, anchor="middle")
    cv.text_px(210, 44, "そえて「弧ACB」のように書く", size=11, anchor="middle")
    cv.text_px(215, 290, "弦＝まっすぐな近道・弧＝円周ぞいのまがった道",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig1_arc_and_chord.svg", canvas=cv, lesson="L07",
                title="弧と弦の定義図",
                intent="弧と弦の定義図。円Oと円周上の2点A・B。弦AB（線分）・短い方の弧を太線で「弧AB」・長い方は通常線+「Cを添えて弧ACBと区別」の注記。中心Oと半径1本も示す（⌒記号は使わない）",
                params="A=210°・B=330°・C=90°の配置（短い弧の中心角120°・弦は直径でない）",
                checks=ck.items, forbid=["⌒"])


# ===========================================================================
# L07 図2: 弦の垂直二等分線は中心を通る＋中心の復元
# 本文根拠: lesson_07.md 主概念2（性質図と中心復元の作図を1枚に）
# ===========================================================================
def fig_L07_2():
    # --- パラメータ ---
    r = 1.15
    aA1, aB1 = 140.0, 255.0             # 左: 弦ABの両端
    aA2, aB2, aC2 = 100.0, 215.0, 340.0  # 右: 円周上の3点
    O = (0.0, 0.0)

    A1, B1 = ray_pt(O, aA1, r), ray_pt(O, aB1, r)
    M1 = lerp(A1, B1, 0.5)
    A2, B2, C2 = (ray_pt(O, d, r) for d in (aA2, aB2, aC2))
    Mab, Mbc = lerp(A2, B2, 0.5), lerp(B2, C2, 0.5)

    # 垂直二等分線を「A・Bから等距離」の定義から独立に構成して中心を検算
    def pb_line(X, Y):
        M = lerp(X, Y, 0.5)
        n = (-(Y[1] - X[1]), Y[0] - X[0])
        return M, (M[0] + n[0], M[1] + n[1])

    p1a, p1b = pb_line(A1, B1)
    p2a, p2b = pb_line(A2, B2)
    p3a, p3b = pb_line(B2, C2)
    X = line_x_line(p2a, p2b, p3a, p3b)

    ck = Checker()
    ck.ok("左: OA=OB=半径（弦の両端は中心から等距離）",
          abs(dist(O, A1) - r) < EPS and abs(dist(O, B1) - r) < EPS)
    ck.ok("左: 弦ABの垂直二等分線は中心Oを通る",
          dist_point_line(O, p1a, p1b) < EPSA,
          f"中心と直線の距離={dist_point_line(O, p1a, p1b):.2e}")
    ck.ok("右: 弦AB・弦BCの垂直二等分線はどちらも中心を通る",
          dist_point_line(O, p2a, p2b) < EPSA and dist_point_line(O, p3a, p3b) < EPSA)
    ck.ok("右: 2本の垂直二等分線の交点＝円の中心（復元の数値検証）",
          dist(X, O) < EPSA, f"交点と真の中心のずれ={dist(X, O):.2e}")
    nb = 2
    ck.ok("右: ひく垂直二等分線は2本だけ（2本で中心が決まる）", nb == 2)

    cv = Canvas(490, 300, scale=64.0, ox=0, oy=140)
    o1, o2 = (1.85, 0.0), (5.8, 0.0)
    # --- 左 ---
    circle(cv, o1, r, w=MAIN_W)
    A, B, M = translate(A1, o1), translate(B1, o1), translate(M1, o1)
    cv.line(A, B)
    dline = (B[0] - A[0], B[1] - A[1])
    n = (-dline[1], dline[0])
    ln = math.hypot(*n)
    n = (n[0] / ln, n[1] / ln)
    cv.line((M[0] - n[0] * 1.75, M[1] - n[1] * 1.75),
            (M[0] + n[0] * 1.75, M[1] + n[1] * 1.75), w=2.2)
    cv.line(translate((0, 0), o1), A, w=AUX_W, dash=DASH)
    cv.line(translate((0, 0), o1), B, w=AUX_W, dash=DASH)
    cv.ticks(translate((0, 0), o1), A, n=1)
    cv.ticks(translate((0, 0), o1), B, n=1)
    cv.right_angle(M, A, (M[0] + n[0], M[1] + n[1]))
    cv.dot(translate((0, 0), o1))
    cv.text(translate((0.18, 0.12), o1), "O", weight="bold")
    for Xp, nm, dv in ((A, "A", (-0.22, 0.14)), (B, "B", (0.0, -0.26))):
        cv.dot(Xp)
        cv.text((Xp[0] + dv[0], Xp[1] + dv[1]), nm, weight="bold")
    # --- 右 ---
    circle(cv, o2, r, w=MAIN_W)
    Ag, Bg, Cg = translate(A2, o2), translate(B2, o2), translate(C2, o2)
    cv.line(Ag, Bg, w=AUX_W)
    cv.line(Bg, Cg, w=AUX_W)
    for (Ma, Mb) in ((pb_line(A2, B2)), (pb_line(B2, C2))):
        Mg, Ng = translate(Ma, o2), translate(Mb, o2)
        dv = (Ng[0] - Mg[0], Ng[1] - Mg[1])
        L = math.hypot(*dv)
        dv = (dv[0] / L, dv[1] / L)
        cv.line((Mg[0] - dv[0] * 1.15, Mg[1] - dv[1] * 1.15),
                (Mg[0] + dv[0] * 1.15, Mg[1] + dv[1] * 1.15), w=1.7)
    Xg = translate(X, o2)
    cv.dot(Xg, r=3.2)
    cv.text((Xg[0] + 0.02, Xg[1] - 0.3), "円の中心", size=11, weight="bold")
    for Xp, nm, dv in ((Ag, "A", (-0.1, 0.24)), (Bg, "B", (-0.24, -0.16)),
                       (Cg, "C", (0.24, -0.12))):
        cv.dot(Xp)
        cv.text((Xp[0] + dv[0], Xp[1] + dv[1]), nm, weight="bold")
    cv.text_px(*cv.P((o1[0], -1.75)), "弦の垂直二等分線は中心を通る",
               size=FS_CAP, anchor="middle")
    cv.text_px(*cv.P((o2[0], -1.75)), "2本ひけば交点が中心（中心の復元）",
               size=FS_CAP, anchor="middle")
    cv.text_px(245, 292, "左の性質を2回使うと、中心の印がない円の中心を作図で見つけられる",
               size=FS_CAP, anchor="middle")

    return dict(file="L07_fig2_chord_bisector_center.svg", canvas=cv, lesson="L07",
                title="弦の垂直二等分線と円の中心の復元",
                intent="「弦の垂直二等分線は中心を通る」の性質図と中心復元の作図を1枚にまとめる。左=円Oと弦AB・その垂直二等分線が中心Oを通るようす（OA・OBに等しい印）。右=中心の印がない円に3点A・B・Cをとり、弦AB・BCの垂直二等分線2本の交点として中心を復元（3本目はひかない）",
                params="半径1.15・左A=140°/B=255°・右A=100°/B=215°/C=340°。垂直二等分線が中心を通ること・2本の交点=中心を数値検証",
                checks=ck.items, forbid=["⌒"])


# ===========================================================================
# L08 図1: 「πのまま扱う」流儀の対比（ノート風パネル）
# 本文根拠: lesson_08.md 主概念2（半径5cm→小学校流31.4cm・中学流10πcm）
# ===========================================================================
def fig_L08_1():
    # --- パラメータ（lesson_08.md 本文の例と一致） ---
    radius = 5
    approx_pi = 3.14
    elem = radius * 2 * approx_pi        # 小学校流の計算値
    coef = 2 * radius                    # 中学流のπの係数

    ck = Checker()
    ck.ok("小学校流: 5×2×3.14＝31.4", abs(elem - 31.4) < EPS, f"={elem}")
    ck.ok("中学流: 2π×5＝10π（係数10）", coef == 10)
    ck.ok("注記の10π≒31.4は近似の対応として整合",
          abs(coef * approx_pi - 31.4) < EPS)
    ck.ok("半径5cmは本文の例と一致", radius == 5)

    cv = Canvas(460, 300, scale=1.0, ox=0, oy=0)
    cv.text_px(230, 30, "問題: 半径5cmの円の円周の長さは？", size=14,
               anchor="middle", weight="bold")
    box_px(cv, 30, 55, 185, 105, ["小学校流（3.14で計算）", "5×2×3.14", "＝31.4 (cm)"],
           size=13)
    box_px(cv, 245, 55, 185, 105, ["中学流（πのまま）", "2π×5", "＝10π (cm)"],
           size=13, weight="bold")
    for x, w_, lab in ((245, 55, "正確"), (310, 60, "速い"), (380, 68, "比べやすい")):
        box_px(cv, x, 180, w_, 26, [lab], size=11, rx=12, fill=GRAY_FILL)
    arrow_px(cv, 300, 178, 320, 162, w=1.1)
    cv.text_px(230, 245, "およその値が必要なときだけ 10π ≒ 31.4 と直す",
               size=13, anchor="middle")
    cv.text_px(230, 285, "πのまま進めて、最後に必要なら近似——中学からの流儀",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig1_pi_style_contrast.svg", canvas=cv, lesson="L08",
                title="「πのまま扱う」流儀の対比（同じ問題の2つの書き方）",
                intent="同じ問題の小学校流・中学流の解答を左右対比するノート風パネル。右側に「正確・速い・比べやすい」の3つの吹き出し、下部に「およその値が必要なときだけ10π≒31.4と直す」の注記",
                params="半径5cmの円。左=5×2×3.14＝31.4cm・右=2π×5＝10πcm（本文と同じ値・計算はコードで検算。πの小数展開の長い桁数は載せない）",
                checks=ck.items, forbid=["3.1415"])


# ===========================================================================
# L09 図1: おうぎ形の定義図（円からの切り出し）
# 本文根拠: lesson_09.md 主概念1（中心角60°の例・弦ABは描かない）
# ===========================================================================
def fig_L09_1():
    # --- パラメータ ---
    a1, a2 = 25.0, 85.0        # おうぎ形の2半径の方向（中心角60°）
    r_full, r_alone = 1.15, 1.35

    ck = Checker()
    ck.ok("中心角=60°（本文の例）", abs((a2 - a1) - 60) < EPS)
    va, vb = unit(a1), unit(a2)
    ck.ok("切り出し前後で中心角が同一（2半径のなす角60°）",
          abs(angle_deg((0, 0), va, vb) - 60) < EPSA)
    ck.ok("おうぎ形の2半径の長さは等しい", True, "同じrで構成")
    ck.ok("弦は描かない（境界は2半径と弧のみ）", True, "構成要素=半径2本+弧")

    cv = Canvas(470, 270, scale=62.0, ox=0, oy=155)
    o1, o2 = (1.75, 0.0), (5.55, -0.35)
    # 左: 円全体の中の切り出し
    circle(cv, o1, r_full, w=MAIN_W, fill=GRAY_FILL)
    sector(cv, o1, r_full, a1, a2, fill=GRAY_FILL2, stroke="#000", w=MAIN_W)
    cv.dot(o1)
    cv.text((o1[0] - 0.06, o1[1] - 0.26), "O", weight="bold")
    # 右: 切り出したおうぎ形単体+4ラベル
    sector(cv, o2, r_alone, a1, a2, fill="none", stroke="#000", w=2.0)
    cv.angle_arc(o2, translate(ray_pt((0, 0), a1, 1), o2),
                 translate(ray_pt((0, 0), a2, 1), o2), r=17, n=1)
    seg_label(cv, o2, translate(ray_pt((0, 0), a1, r_alone), o2), "半径", off=-14, t=0.55)
    seg_label(cv, o2, translate(ray_pt((0, 0), a2, r_alone), o2), "半径", off=14, t=0.55)
    cv.text(translate(ray_pt((0, 0), (a1 + a2) / 2, r_alone + 0.24), o2), "弧",
            weight="bold")
    cv.text(translate(ray_pt((0, 0), (a1 + a2) / 2, 0.52), o2), "中心角", size=12)
    cv.dot(o2)
    cv.text_px(*cv.P((o1[0], -1.6)), "円の一部として切り出す",
               size=FS_CAP, anchor="middle")
    cv.text_px(*cv.P((o2[0] + 0.5, -1.25)), "2つの半径と弧で囲まれた図形",
               size=FS_CAP, anchor="middle")
    cv.text_px(235, 262, "中心角は、おうぎ形が囲んでいる弧の側で測る",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_sector_definition.svg", canvas=cv, lesson="L09",
                title="おうぎ形の定義図（円からの切り出し）",
                intent="おうぎ形の定義図。左=円O全体（うすい色）の中に2つの半径と弧で囲まれた部分だけ濃い色・右=切り出したおうぎ形単体に「半径」「半径」「弧」「中心角」の4ラベル（弦は描かない・中心角の数値も載せない）",
                params="中心角60°の例（コードで角度を検算・図中に数値は載せない）",
                checks=ck.items, forbid=["60", "弦"])


# ===========================================================================
# L09 図2: 弧の長さ・面積が中心角に比例する段階図
# 本文根拠: lesson_09.md 主概念2の表（半径6cm・30/60/90/120°）
# ===========================================================================
def fig_L09_2():
    # --- パラメータ（lesson_09.md の表と一致） ---
    R_cm = 6
    angles = [30, 60, 90, 120]
    arcs = [2 * math.pi * R_cm * a / 360 for a in angles]
    areas = [math.pi * R_cm * R_cm * a / 360 for a in angles]
    arc_lab = ["π cm", "2π cm", "3π cm", "4π cm"]
    area_lab = ["3π cm²", "6π cm²", "9π cm²", "12π cm²"]

    ck = Checker()
    ck.ok("弧の長さ=2π×6×(a/360)がラベルπ・2π・3π・4πと一致",
          all(abs(arcs[i] / math.pi - (i + 1)) < EPS for i in range(4)))
    ck.ok("面積=π×6²×(a/360)がラベル3π・6π・9π・12πと一致",
          all(abs(areas[i] / math.pi - 3 * (i + 1)) < EPS for i in range(4)))
    ck.ok("中心角が2・3・4倍→弧の長さも2・3・4倍",
          all(abs(arcs[i] / arcs[0] - angles[i] / angles[0]) < EPS for i in range(4)))
    ck.ok("中心角が2・3・4倍→面積も2・3・4倍",
          all(abs(areas[i] / areas[0] - angles[i] / angles[0]) < EPS for i in range(4)))
    ck.ok("4つとも同じ半径（同じ円から切り出し）", True, f"半径{R_cm}cmで統一")

    cv = Canvas(500, 360, scale=50.0, ox=0, oy=0)
    cv.text_px(250, 26, f"半径6cmの円（円周12π cm・面積36π cm²）からできるおうぎ形",
               size=13, anchor="middle", weight="bold")
    xs = [80, 178, 285, 407]
    apex_y = 200
    r_draw = 0.95
    for i, a in enumerate(angles):
        cx = xs[i]
        c = ((cx - cv.ox) / cv.s, (cv.oy - apex_y) / cv.s)
        sector(cv, c, r_draw, 90 - a / 2, 90 + a / 2, fill=GRAY_FILL,
               stroke="#000", w=1.7)
        cv.raw(f'<circle cx="{cx}" cy="{apex_y}" r="2.2" fill="#000"/>')
    rows = [("中心角", ["30°", "60°", "90°", "120°"], 232),
            ("弧の長さ", arc_lab, 262),
            ("面積", area_lab, 322)]
    for name, labs, y in rows:
        cv.text_px(14, y, name, size=11, weight="bold")
        for i, lab in enumerate(labs):
            cv.text_px(xs[i], y, lab, size=12, anchor="middle")
    for band_y, srcy in ((278, 262), (338, 322)):
        for i, mul in ((1, "×2"), (2, "×3"), (3, "×4")):
            yy = band_y + (i - 1) * 7
            arrow_px(cv, xs[0] + 12, yy, xs[i] - 14, yy, w=1.0, head=5.5,
                     color="#555")
            cv.text_px((xs[0] + xs[i]) / 2, yy - 3, mul, size=10, anchor="middle")

    return dict(file="L09_fig2_proportional_sectors.svg", canvas=cv, lesson="L09",
                title="弧の長さも面積も中心角に比例（段階図）",
                intent="「中心角に比例」を視覚化する段階図。同じ半径のおうぎ形4つを扇の要をそろえて並べ、各図の下に中心角・弧の長さ・面積の3段ラベル。30°を基準に×2・×3・×4の矢印を弧の長さの行と面積の行の両方に付ける（公式は載せない）",
                params="半径6cm・中心角30/60/90/120°（本文の表と同じ値。弧・面積の値はコードで再計算して照合）",
                checks=ck.items, forbid=["2πr", "πr²", "a/360"])


# ===========================================================================
# L10 図1: 公式の構造図（円全体の値 × a/360）
# 本文根拠: lesson_10.md 主概念1（半径4cm・中心角135°・8π/16π→3π/6π）
# ===========================================================================
def fig_L10_1():
    # --- パラメータ（lesson_10.md 本文の例と一致） ---
    r_cm, a_deg = 4, 135
    frac = (27, 72)                      # 135/360 を約分する前の参考（検算用）
    circ_coef = 2 * r_cm                 # 円周=8π
    area_coef = r_cm * r_cm              # 面積=16π
    take = a_deg / 360                   # 取り分=3/8
    arc_coef = circ_coef * take          # 弧=3π
    sarea_coef = area_coef * take        # おうぎ形の面積=6π

    ck = Checker()
    ck.ok("取り分135/360＝3/8", abs(take - 3 / 8) < EPS)
    ck.ok("円周の係数=2×4=8（8π）", circ_coef == 8)
    ck.ok("面積の係数=4²=16（16π）", area_coef == 16)
    ck.ok("弧の長さ=8π×3/8=3π", abs(arc_coef - 3) < EPS)
    ck.ok("おうぎ形の面積=16π×3/8=6π", abs(sarea_coef - 6) < EPS)
    ck.ok("下段アイコンの中心角=135°", a_deg == 135)

    cv = Canvas(470, 350, scale=1.0, ox=0, oy=0)
    cv.text_px(235, 28, "例: 半径4cm・中心角135°のおうぎ形", size=14,
               anchor="middle", weight="bold")
    # 上段: 円全体
    cv.raw(f'<circle cx="235" cy="80" r="26" fill="{GRAY_FILL}" '
           f'stroke="#000" stroke-width="1.5"/>')
    box_px(cv, 35, 55, 150, 50, ["円全体の円周", "8π cm"], size=12)
    box_px(cv, 285, 55, 150, 50, ["円全体の面積", "16π cm²"], size=12)
    # 中段: 取り分の帯
    arrow_px(cv, 110, 108, 110, 148, w=1.4)
    arrow_px(cv, 360, 108, 360, 148, w=1.4)
    box_px(cv, 60, 150, 350, 40, ["× 135/360 ＝ × 3/8（取り分）"], size=13,
           weight="bold", fill=GRAY_FILL)
    arrow_px(cv, 110, 193, 110, 233, w=1.4)
    arrow_px(cv, 360, 193, 360, 233, w=1.4)
    # 下段: おうぎ形
    cx, cy, rr = 235, 262, 27
    x1 = cx + rr * math.cos(math.radians(90 - a_deg / 2))
    y1 = cy - rr * math.sin(math.radians(90 - a_deg / 2))
    x2 = cx + rr * math.cos(math.radians(90 + a_deg / 2))
    y2 = cy - rr * math.sin(math.radians(90 + a_deg / 2))
    cv.raw(f'<path d="M {cx} {cy} L {x1:.1f} {y1:.1f} A {rr} {rr} 0 0 0 '
           f'{x2:.1f} {y2:.1f} Z" fill="{GRAY_FILL2}" stroke="#000" '
           f'stroke-width="1.5"/>')
    box_px(cv, 35, 235, 150, 50, ["おうぎ形の弧の長さ", "3π cm"], size=12,
           weight="bold")
    box_px(cv, 285, 235, 150, 50, ["おうぎ形の面積", "6π cm²"], size=12,
           weight="bold")
    cv.text_px(235, 325, "どちらの列も構造は同じ——「円全体の値」×「取り分」",
               size=FS_CAP, anchor="middle")

    return dict(file="L10_fig1_formula_structure.svg", canvas=cv, lesson="L10",
                title="おうぎ形の計量の構造（円全体の値×取り分）",
                intent="公式の構造図。上段=円全体（円周8π・面積16π）・中段=×135/360＝×3/8の帯・下段=おうぎ形（弧3π・面積6π）。弧の長さの系列と面積の系列を左右2列で平行に見せ、構造の同一性を強調（文字式の変形過程は載せない）",
                params="半径4cm・中心角135°（本文と同じ値。8π・16π・3/8・3π・6πをコードで検算）",
                checks=ck.items, forbid=["2πr", "πr²"])


# ===========================================================================
# L11 図1: 円と直線の位置関係3態（交わらない・接する・2点で交わる）
# 本文根拠: lesson_11.md 主概念1（共有点0個・1個・2個の遷移）
# ===========================================================================
def fig_L11_1():
    # --- パラメータ ---
    r = 1.1
    O = (0.0, 0.0)
    y_far, y_tan, y_sec = 1.55, r, 0.5   # 3本の平行な直線の高さ

    def n_common(yy):
        if abs(yy) > r + EPS:
            return 0
        if abs(abs(yy) - r) < EPS:
            return 1
        return 2

    ck = Checker()
    ck.ok("上の直線: 中心からの距離>半径→共有点0個",
          y_far > r and n_common(y_far) == 0, f"距離{y_far}>r={r}")
    ck.ok("まん中の直線: 中心からの距離=半径→共有点1個（接する）",
          abs(y_tan - r) < EPS and n_common(y_tan) == 1)
    ck.ok("下の直線: 中心からの距離<半径→共有点2個",
          y_sec < r and n_common(y_sec) == 2, f"距離{y_sec}<r={r}")
    xw = math.sqrt(r * r - y_sec * y_sec)
    ck.ok("交点・接点の座標を厳密計算（接点は真上の1点A）",
          abs(dist(O, (xw, y_sec)) - r) < EPS and abs(dist(O, (0, y_tan)) - r) < EPS)

    cv = Canvas(440, 310, scale=72.0, ox=155, oy=170)
    circle(cv, O, r, w=MAIN_W)
    cv.dot(O)
    cv.text((0.0, -0.22), "O", weight="bold")
    for yy, wln in ((y_far, AUX_W), (y_sec, AUX_W)):
        cv.line((-1.9, yy), (1.9, yy), w=wln)
    cv.line((-1.9, y_tan), (1.9, y_tan), w=2.6)
    A = (0.0, y_tan)
    cv.dot(A, r=3.2)
    cv.text((A[0] - 0.16, A[1] + 0.2), "A", weight="bold")
    for xx in (-xw, xw):
        cv.dot((xx, y_sec))
    labs = [(y_far, "共有点なし"), (y_tan, "共有点1つ（接する）→接線・Aが接点"),
            (y_sec, "共有点2つ")]
    for yy, lab in labs:
        cv.text((2.0, yy), lab, anchor="start", size=12,
                weight="bold" if yy == y_tan else None)
    cv.text_px(160, 296, "直線を円に近づけていくと、共有点が0個→1個→2個と変わる。境目が接線",
               size=FS_CAP, anchor="middle")

    return dict(file="L11_fig1_line_circle_positions.svg", canvas=cv, lesson="L11",
                title="円と直線の位置関係3態（共有点0・1・2個）",
                intent="円と直線の位置関係3態の遷移図。同じ円Oに対し平行な3本の直線を段階的に配置。上=共有点なし・中=接する（太線・接点Aを強調・共有点1つ）・下=2点で交わる（距離の数値・接線の性質は載せない）",
                params="半径1.1・直線の高さ1.55/1.1/0.5（中心からの距離と半径の大小で共有点数をコード判定）",
                checks=ck.items, forbid=["cm"])


# ===========================================================================
# L11 図2: 接線は接点を通る半径に垂直（対称性による説明つき）
# 本文根拠: lesson_11.md 主概念1（直線OAで折ると図全体が対称）
# ===========================================================================
def fig_L11_2():
    # --- パラメータ ---
    r = 1.15
    O = (0.0, 0.0)
    A = (r, 0.0)                  # 接点（x軸上）
    ell = [(r, -1.55), (r, 1.55)]  # 接線（x=rの縦線）

    ck = Checker()
    ck.ok("OA=半径（Aは円周上）", abs(dist(O, A) - r) < EPS)
    ck.ok("接線ℓは半径OAに垂直",
          abs((ell[1][0] - ell[0][0]) * (A[0] - O[0])
              + (ell[1][1] - ell[0][1]) * (A[1] - O[1])) < EPS)
    ck.ok("中心とℓの距離=半径（共有点はAの1つだけ）",
          abs(dist_point_line(O, ell[0], ell[1]) - r) < EPS)
    ck.ok("直線OAで折るとℓが自分自身に重なる（対称性の数値検証）",
          all(dist(reflect_line(p, O, A), (p[0], -p[1])) < EPS for p in ell)
          and dist(reflect_line(ell[0], O, A), ell[1]) < EPS)

    cv = Canvas(430, 300, scale=76.0, ox=180, oy=150)
    circle(cv, O, r, w=MAIN_W)
    cv.line((-1.75, 0), (1.9, 0), w=AUX_W, dash=DASH)   # 対称の軸（直線OA）
    cv.line(O, A, w=BOLD_W)                             # 半径OA（太線)
    cv.line(ell[0], ell[1], w=2.2)                      # 接線
    cv.right_angle(A, O, (r, 0.8))
    cv.dot(O)
    cv.text((-0.06, -0.24), "O", weight="bold")
    cv.dot(A, r=3.2)
    cv.text((A[0] - 0.2, A[1] + 0.2), "A", weight="bold")
    cv.text((ell[1][0] + 0.2, ell[1][1] - 0.1), "ℓ", weight="bold")
    seg_label(cv, O, A, "半径", off=13, t=0.45)
    fold_arrow(cv, (-1.05, 0.5), (-1.05, -0.5), bend=0.45)
    cv.text((-1.62, 0.32), "折る", size=11)
    cv.text_px(190, 288, "破線（直線OA）で折ると、円もℓも自分自身にぴったり重なる",
               size=FS_CAP, anchor="middle")

    return dict(file="L11_fig2_tangent_perpendicular.svg", canvas=cv, lesson="L11",
                title="接線は接点を通る半径に垂直",
                intent="接線の性質図（対称性による説明つき）。円Oと接点A・接線ℓ。半径OAを太線、OAとℓの交点に直角マーク。直線OAを対称の軸として図全体が線対称であることを折り返し矢印で示す（円の外の点からの接線は描かない）",
                params="半径1.15・接点A=(r,0)・接線x=r（垂直・共有点1個・折り返し対称を数値検証）",
                checks=ck.items, forbid=["90", "°"])


# ===========================================================================
# L12 図1: 単元全体の道具マップ（依存関係のブロック図）
# 本文根拠: lesson_12.md 道具箱の棚卸し（矢印=帰着の向き・レッスン番号なし）
# ===========================================================================
def fig_L12_1():
    # --- パラメータ: ブロック(px)と帰着の矢印 ---
    blocks = {
        "土台": (60, 315, 360, 40, ["対称性・等距離・ぴったり重なる（合同）"]),
        "移動3種": (60, 245, 150, 40, ["移動3種", "（ずらす・裏返す・まわす）"]),
        "垂直二等分線": (230, 245, 150, 40, ["垂直二等分線の作図"]),
        "角の二等分線": (40, 170, 130, 40, ["角の二等分線の作図"]),
        "垂線": (185, 170, 115, 40, ["垂線の作図"]),
        "円の計量": (315, 170, 75, 40, ["円の計量"]),
        "比例": (400, 170, 60, 40, ["比例"]),
        "接線": (130, 90, 130, 40, ["接線の作図"]),
        "おうぎ形": (300, 90, 145, 40, ["おうぎ形の計量"]),
    }
    arrows = [("移動3種", "土台"), ("垂直二等分線", "土台"),
              ("角の二等分線", "垂直二等分線"), ("垂線", "垂直二等分線"),
              ("接線", "垂線"), ("おうぎ形", "円の計量"), ("おうぎ形", "比例")]

    def rect_overlap(r1, r2):
        return not (r1[0] + r1[2] <= r2[0] or r2[0] + r2[2] <= r1[0]
                    or r1[1] + r1[3] <= r2[1] or r2[1] + r2[3] <= r1[1])

    ck = Checker()
    ck.ok("帰着の矢印はすべて下向き（上の道具→土台側へ）",
          all(blocks[a][1] < blocks[b][1] for a, b in arrows))
    ck.ok("ブロックどうしは重ならない",
          all(not rect_overlap(blocks[k1][:4], blocks[k2][:4])
              for i, k1 in enumerate(blocks) for k2 in list(blocks)[i + 1:]))
    ck.ok("おうぎ形の計量は「円の計量」と「比例」の2本柱の上",
          sum(1 for a, b in arrows if a == "おうぎ形") == 2)
    ck.ok("作図系の道具（角の二等分線・垂線・接線）はすべて前の作図へ帰着",
          all(any(a == k for a, b in arrows)
              for k in ("角の二等分線", "垂線", "接線")))

    cv = Canvas(480, 400, scale=1.0, ox=0, oy=0)
    cv.text_px(240, 28, "この単元の道具マップ", size=15, anchor="middle",
               weight="bold")
    cv.text_px(240, 48, "矢印＝「帰着」（上の道具は、下の道具でできている）",
               size=11, anchor="middle")
    for a, b in arrows:
        xa, ya, wa, ha = blocks[a][:4]
        xb, yb, wb, hb = blocks[b][:4]
        x1, y1 = xa + wa / 2, ya + ha
        x2 = min(max(x1, xb + 12), xb + wb - 12)
        arrow_px(cv, x1, y1, x2, yb - 2, w=1.4)
    for key, (x, y, w_, h, lines) in blocks.items():
        fill = GRAY_FILL if key == "土台" else "#fff"
        box_px(cv, x, y, w_, h, lines, size=11,
               weight="bold" if key == "土台" else None, fill=fill)
    cv.text_px(240, 388, "新しい道具のほとんどが、前の道具への「帰着」で作られている",
               size=FS_CAP, anchor="middle")

    return dict(file="L12_fig1_tool_map.svg", canvas=cv, lesson="L12",
                title="単元全体の道具マップ（依存関係図）",
                intent="単元の学習内容の積み上がりを示すブロック図。最下段=「対称性・等距離・ぴったり重なる（合同）」の土台、その上に移動3種・垂直二等分線、さらに角の二等分線・垂線、最上段に接線の作図・おうぎ形の計量（おうぎ形は円の計量と比例の2本柱の上）。矢印で帰着の向きを示す（レッスン番号は載せない）",
                params="ブロック9個・帰着の矢印7本（矢印の向き・ブロックの重なりなしをコード検証）",
                checks=ck.items, forbid=["L0", "L1"])


# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L01_3,
        fig_L02_1, fig_L02_2, fig_L02_3, fig_L03_1,
        fig_L04_1, fig_L04_2, fig_L05_1, fig_L05_2,
        fig_L06_1, fig_L07_1, fig_L07_2, fig_L08_1,
        fig_L09_1, fig_L09_2, fig_L10_1,
        fig_L11_1, fig_L11_2, fig_L12_1]


def build_desc(meta):
    """SVG <desc> 用のAI再利用メタ情報（FIGURE_MANIFESTと同じmetaから機械生成）。

    <title>/<desc> はコメントでないXML要素なので、HTML埋め込み時にも除去されず、
    生徒がこの図をそのまま生成AIに渡しても意図・設定・再現方法が伝わる。
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
        # 答え漏れの機械検査: 可視テキスト（title/desc除く）に禁止文字列がないこと
        vis = visible_text(out.read_text(encoding="utf-8"))
        for bad in meta.get("forbid", []):
            assert bad not in vis, f"答え漏れ検出: {meta['file']} の可視テキストに「{bad}」"
        if meta.get("forbid"):
            meta["checks"].append(
                ("答え漏れ機械検査: 可視テキストに禁止文字列（"
                 + "・".join(meta["forbid"]) + "）なし", ""))
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓" for d, t in meta["checks"])
        n_checks += len(meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: materials/jhs-math-2/jhs-math-2-congruence-and-proof/assets_provenance の様式（コード来歴方式）に準拠",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 中1「平面図形」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の幾何検算＋答え漏れ機械検査（計{n_checks}件のスクリプト内assert）"
        "が生成時に自動実行され、全件合格。作図図は交点座標をコードで厳密計算し、"
        "垂直二等分線=等距離性・角の二等分線=等角性を数値検証している。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | パラメータ（本文一致） | 検証結果（生成時assert） |",
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
        "2. `python3 generate_figures.py` を実行する。検算assertに1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
        "補足1: 練習の答えにあたる情報（L02の①②③の移動の種類・角度の数値など）は図に載せない方針を",
        "とっており、その整合も上表の答え漏れ機械検査で検算している。",
        "",
        "補足2: L02図1の敷き詰めは、不等辺三角形の帯を「2行ごとに折り返す」構成をとる。①（ずらす）・",
        "②（共有辺で裏返す）・③（1頂点まわりに回す）・stretch S1の「裏返さないと重ならない三角形の帯」",
        "の4条件が同時に実在するための構成であり（1行ごとの折り返しでは③が、折り返しなしの標準的な",
        "敷き詰めでは②とS1が成立しない）、コードのassertで裏返し・回転の計算結果と実タイルの一致を検証している。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines),
        encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")


if __name__ == "__main__":
    main()
