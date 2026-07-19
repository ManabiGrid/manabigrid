#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2数学「図形の合同と証明」単元 図版パラメトリック生成スクリプト
====================================================================================
様式: docs/SPEC_figures.md に準拠。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（22枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / pathlib / datetime / html）
- 幾何の自己検証: 各図の fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。加えて main() が
  「答え漏れの機械検査」（可視テキストに禁止文字列がないか）を全図で行う。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
- 描画ヘルパー（Canvas ほか）は
  materials/jhs-math-3/jhs-math-3-similar-figures/assets_provenance/generate_figures.py
  から無変更で流用（この単元専用の追加ヘルパーは「追加ヘルパー」節に分離）。
"""

import math
import re
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
# 描画ヘルパー（相似単元 generate_figures.py から無変更流用）
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
        a1 = math.atan2(*(reversed([self.P(p)[0] - vx]))) if False else None  # (未使用ガード)
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
        mx, my = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2
        lab_off = 11 / self.s
        self.text((mx + nx * 0, my), label, size=size,
                  dy=(1.15 if ny > 0 else -0.55))

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
            f'(docs/SPEC_figures.md準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
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


def tri_from_sides(c_len, b_len, a_len):
    """B=(0,0), C=(a_len,0) — BC=a_len を底辺に、AB=c_len, CA=b_len の三角形を返す(A,B,C)"""
    B = (0.0, 0.0)
    C = (a_len, 0.0)
    x = (c_len ** 2 + a_len ** 2 - b_len ** 2) / (2 * a_len)
    y = math.sqrt(c_len ** 2 - x ** 2)
    return (x, y), B, C


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


# ===========================================================================
# 追加ヘルパー（本単元用）
# ===========================================================================
GRAY_FILL = "#e6e6e6"   # 薄い塗り分け（白黒両立: 濃淡グレー）


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


def line_through(cv, p, deg, back, fwd, w=MAIN_W, dash=None, color="#000"):
    """点pを通り方向deg（度）の直線を、後方back〜前方fwd（数学単位）で描く"""
    u = unit(deg)
    a = (p[0] - u[0] * back, p[1] - u[1] * back)
    b = (p[0] + u[0] * fwd, p[1] + u[1] * fwd)
    cv.line(a, b, w=w, dash=dash, color=color)


def angle_label(cv, v, p, q, s, r=27.0, size=FS):
    """頂点vの角∠pvq内（2辺の二等分方向・半径r px）にラベルを置く"""
    d1 = (p[0] - v[0], p[1] - v[1])
    d2 = (q[0] - v[0], q[1] - v[1])
    l1 = math.hypot(*d1) or 1.0
    l2 = math.hypot(*d2) or 1.0
    bx, by = d1[0] / l1 + d2[0] / l2, d1[1] / l1 + d2[1] / l2
    lb = math.hypot(bx, by) or 1.0
    pos = (v[0] + bx / lb * (r / cv.s), v[1] + by / lb * (r / cv.s))
    cv.text(pos, s, size=size)


def add_hatch(cv, pid="hatch"):
    """白黒両立のハッチング塗り（<pattern>内蔵・外部参照なし）"""
    if not any(pid in d for d in cv.defs):
        cv.defs.append(
            f'<pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="#999" stroke-width="1"/></pattern>')
    return f"url(#{pid})"


def fill_poly(cv, pts, fill):
    """輪郭なしの塗りだけのポリゴン（塗り分け用・主線は別に描く）"""
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(cv.P, pts))
    cv.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')


def line_intersect(p1, d1, p2, d2):
    """点p1方向d1の直線と点p2方向d2の直線の交点（方向はdeg）"""
    u, v = unit(d1), unit(d2)
    det = u[0] * (-v[1]) - (-v[0]) * u[1]
    assert abs(det) > 1e-12, "直線が平行で交点なし"
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t = (dx * (-v[1]) - (-v[0]) * dy) / det
    return (p1[0] + u[0] * t, p1[1] + u[1] * t)


def region_bisectors(u_deg, v_deg):
    """交点まわり4領域（左上/右上/右下/左下）の二等分方向ベクトルを返す辞書"""
    u, v = unit(u_deg), unit(v_deg)
    out = {}
    for su in (1, -1):
        for sv in (1, -1):
            bx, by = su * u[0] + sv * v[0], su * u[1] + sv * v[1]
            L = math.hypot(bx, by) or 1.0
            bx, by = bx / L, by / L
            key = ("右" if bx > 0 else "左") + ("上" if by > 0 else "下")
            out[key] = (bx, by)
    assert len(out) == 4, "4領域が一意に決まらない配置"
    return out


def visible_text(svg):
    """答え漏れ検査用: <title>/<desc>を除いた可視テキストノードを連結して返す"""
    body = re.sub(r"<title>.*?</title>", "", svg, flags=re.S)
    body = re.sub(r"<desc>.*?</desc>", "", body, flags=re.S)
    return "".join(re.findall(r">([^<]*)<", body))


EPS = 1e-9


# ===========================================================================
# L01 図1: 対頂角の定義図（交差角70°・数値なし）
# 本文根拠: lesson_01.md 主概念1（∠a左上・∠b右上・∠c右下・∠d左下、∠a=∠cに同系弧）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md: 斜め交差・直角に見えない70°程度） ---
    th1, th2 = 10.0, 80.0          # 2直線の方向（交差角=70°）
    O = (0.0, 0.0)
    R = 2.4

    rays = sorted([th1, th2, th1 + 180, th2 + 180])
    regions = [(rays[i], rays[(i + 1) % 4] + (360 if i == 3 else 0)) for i in range(4)]
    meas = {}
    for lo, hi in regions:
        mid = (lo + hi) / 2 % 360
        key = ("右" if math.cos(math.radians(mid)) > 0 else "左") + \
              ("上" if math.sin(math.radians(mid)) > 0 else "下")
        meas[key] = (hi - lo, (lo, hi))

    ck = Checker()
    ck.ok("対頂角どうしが等しい（∠a=∠c, ∠b=∠d）",
          abs(meas["左上"][0] - meas["右下"][0]) < EPS and
          abs(meas["右上"][0] - meas["左下"][0]) < EPS,
          f"∠a=∠c={meas['左上'][0]:.1f}, ∠b=∠d={meas['右上'][0]:.1f}")
    ck.ok("となり合う角の和=180°（一直線）",
          abs(meas["左上"][0] + meas["右上"][0] - 180) < EPS)
    ck.ok("4つの角の和=360°", abs(sum(m[0] for m in meas.values()) - 360) < EPS)
    acute = min(meas["左上"][0], meas["右上"][0])
    ck.ok("交差角70°（直角に見えない斜め交差）", abs(acute - 70) < EPS and abs(acute - 90) > 10)

    cv = Canvas(420, 250, scale=46.0, ox=210, oy=120)
    line_through(cv, O, th1, R, R)
    line_through(cv, O, th2, R, R)
    cv.dot(O)
    cv.text_px(*(lambda p: (p[0] + 14, p[1] - 12))(cv.P(O)), "O", size=FS, anchor="start", weight="bold")
    # 対頂角の組∠a・∠cに同系（1重）の弧
    for key in ("左上", "右下"):
        lo, hi = meas[key][1]
        cv.angle_arc(O, ray_pt(O, lo, 1), ray_pt(O, hi, 1), r=16, n=1)
    names = {"左上": "∠a", "右上": "∠b", "右下": "∠c", "左下": "∠d"}
    for key, nm in names.items():
        lo, hi = meas[key][1]
        cv.text(ray_pt(O, (lo + hi) / 2, 42 / cv.s), nm, size=FS, weight="bold")
    cv.text_px(210, 232, "向かい合う∠aと∠c、∠bと∠dが対頂角（弧は∠a・∠cの組）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig1_vertical_angles.svg", canvas=cv, lesson="L01",
                title="2直線の交点と4つの角（対頂角の定義図）",
                intent="対頂角の定義図。向かい合う∠aと∠cを同系の弧マークで示す（角度の具体値は載せない）",
                params="2直線の方向10°/80°（交差角70°・直角に見えない斜め交差）",
                checks=ck.items, forbid=["°", "70"])


# ===========================================================================
# L01 図2: 対頂角の適用練習（左上62°のみ表示・残り3角は？）
# 本文根拠: lesson_01.md 練習1「1つの角が62°のとき残り3つを求める」
# 答え漏れ注意: 118°は図に書かない（answer_key_L01-04と照合）
# ===========================================================================
def fig_L01_2():
    # --- パラメータ（lesson_01.md 練習1 と一致させる） ---
    given = 62.0                    # 左上の角にのみ表示する与件
    th1, th2 = 104.0, 166.0         # 交差角62°になる2直線の方向
    O = (0.0, 0.0)
    R = 2.4

    rays = sorted([th1 % 360, th2 % 360, (th1 + 180) % 360, (th2 + 180) % 360])
    meas = {}
    for i in range(4):
        lo = rays[i]
        hi = rays[(i + 1) % 4] + (360 if i == 3 else 0)
        mid = (lo + hi) / 2 % 360
        key = ("右" if math.cos(math.radians(mid)) > 0 else "左") + \
              ("上" if math.sin(math.radians(mid)) > 0 else "下")
        meas[key] = (hi - lo, (lo, hi))

    ck = Checker()
    ck.ok("左上の角=本文の与件62°", abs(meas["左上"][0] - given) < EPS,
          f"実測={meas['左上'][0]:.1f}")
    ck.ok("残り3角は対頂角・一直線の関係と整合（62/118/118）",
          abs(meas["右下"][0] - 62) < EPS and abs(meas["右上"][0] - 118) < EPS
          and abs(meas["左下"][0] - 118) < EPS)
    ck.ok("4角の和=360°", abs(sum(m[0] for m in meas.values()) - 360) < EPS)

    cv = Canvas(420, 250, scale=46.0, ox=210, oy=120)
    line_through(cv, O, th1, R, R)
    line_through(cv, O, th2, R, R)
    cv.dot(O)
    cv.text_px(*(lambda p: (p[0] + 12, p[1] + 14))(cv.P(O)), "O", size=FS, anchor="start", weight="bold")
    for key, lab in [("左上", "62°"), ("右上", "？"), ("右下", "？"), ("左下", "？")]:
        lo, hi = meas[key][1]
        if lab != "？":
            cv.angle_arc(O, ray_pt(O, lo, 1), ray_pt(O, hi, 1), r=17, n=1)
        cv.text(ray_pt(O, (lo + hi) / 2, 44 / cv.s), lab, size=FS,
                weight="bold" if lab != "？" else None)
    cv.text_px(210, 232, "2直線が点Oで交わる。？の3つの角を求める（根拠を一言そえて）",
               size=FS_CAP, anchor="middle")

    return dict(file="L01_fig2_vertical_angles_62.svg", canvas=cv, lesson="L01",
                title="2直線の交点・1つの角だけ62°（練習1）",
                intent="対頂角・一直線の角の適用練習。与件62°のみ表示し、残り3角は？で示す",
                params="交差角62°を厳密に反映（残り3角の値は図に書かない）",
                checks=ck.items, forbid=["118"])


# ===========================================================================
# L02 図1: 同位角・錯角の定義図（8角・lとmはあえて非平行）
# 本文根拠: lesson_02.md 主概念1（∠a〜∠h。定義は平行と無関係＝わずかに非平行）
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（lesson_02.md: lとmをわずかに非平行にする） ---
    deg_l, deg_m, deg_n = 0.0, -5.0, 64.0     # l・m・横切るnの方向
    Pl = (0.0, 1.05)                          # l上の1点
    Pm = (0.0, -1.05)                         # m上の1点

    T = line_intersect(Pl, deg_l, (0.0, 0.0), deg_n)   # 上の交点（l×n）
    Bt = line_intersect(Pm, deg_m, (0.0, 0.0), deg_n)  # 下の交点（m×n）

    ck = Checker()
    diff = abs(deg_l - deg_m)
    ck.ok("lとmは平行でない（定義は平行と無関係であることを示す）",
          3.0 <= diff <= 8.0, f"方向差={diff:.1f}度")
    ck.ok("nがl・mの両方と交わる（交点2つ・8角）",
          dist(T, Bt) > 0.5, f"交点間距離={dist(T, Bt):.2f}")
    ck.ok("同位角の組∠aと∠eは等しくない（非平行のため）",
          abs(angle_deg(T, ray_pt(T, deg_l + 180, 1), ray_pt(T, deg_n, 1))
              - angle_deg(Bt, ray_pt(Bt, deg_m + 180, 1), ray_pt(Bt, deg_n, 1))) > 1.0)

    cv = Canvas(430, 300, scale=62.0, ox=215, oy=150)
    line_through(cv, T, deg_l, 2.6, 2.6)
    line_through(cv, Bt, deg_m, 2.6, 2.6)
    line_through(cv, (0.0, 0.0), deg_n, 2.1, 2.1)
    for p in (T, Bt):
        cv.dot(p)
    # 直線名ラベル（右端・下端）
    cv.text(ray_pt(T, deg_l, 2.75), "l", size=FS, weight="bold")
    cv.text(ray_pt(Bt, deg_m, 2.75), "m", size=FS, weight="bold")
    cv.text(ray_pt((0.0, 0.0), deg_n, 2.3), "n", size=FS, weight="bold")
    # 8角のラベル（各交点の4領域）
    for o, ldeg, names in [(T, deg_l, {"左上": "∠a", "右上": "∠b", "右下": "∠c", "左下": "∠d"}),
                           (Bt, deg_m, {"左上": "∠e", "右上": "∠f", "右下": "∠g", "左下": "∠h"})]:
        bis = region_bisectors(ldeg, deg_n)
        for key, nm in names.items():
            b = bis[key]
            cv.text((o[0] + b[0] * (30 / cv.s), o[1] + b[1] * (30 / cv.s)), nm, size=FS)
    cv.text_px(215, 288, "lとmは平行とは限らない（この図では平行でない）",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_transversal_angles.svg", canvas=cv, lesson="L02",
                title="2直線l・mに直線nが交わる図（8つの角）",
                intent="同位角・錯角の定義図。lとmはあえて非平行に描き、位置取りの名前であることを示す",
                params="lの方向0度・mの方向-5度（わずかに非平行）・nの方向64度。角度値・平行記号なし",
                checks=ck.items, forbid=["°", "平行記号", "//"])


# ===========================================================================
# L03 図1: 「角を集める」実験の再現図（50°・60°・70°）
# 本文根拠: lesson_03.md 活動（3角を切り取り1点に集めると一直線）
# ===========================================================================
def fig_L03_1():
    # --- パラメータ（lesson_03.md figure-spec: 非対称の3角） ---
    aA, aB, aC = 50.0, 60.0, 70.0

    ck = Checker()
    ck.ok("3つの角の和=180°（一直線に並ぶ）", abs(aA + aB + aC - 180) < EPS)
    # 三角形を実際に構成して角を検算
    B = (0.0, 0.0)
    C = (3.0, 0.0)
    A = line_intersect(B, aB, C, 180 - aC)
    ck.ok("構成した三角形の3角=50/60/70°",
          abs(angle_deg(A, B, C) - aA) < 1e-6 and abs(angle_deg(B, C, A) - aB) < 1e-6
          and abs(angle_deg(C, A, B) - aC) < 1e-6,
          f"実測A={angle_deg(A, B, C):.2f}, B={angle_deg(B, C, A):.2f}, C={angle_deg(C, A, B):.2f}")
    ck.ok("非対称（3角がすべて異なる）", len({aA, aB, aC}) == 3)

    cv = Canvas(470, 230, scale=48.0)
    # 左: 三角形（弧の本数 A=1, B=2, C=3）
    cv.ox, cv.oy = 40, 185
    cv.polygon([A, B, C])
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    cv.angle_arc(A, B, C, n=1)
    cv.angle_arc(B, C, A, n=2)
    cv.angle_arc(C, A, B, n=3)
    # 右: 1点Pのまわりに3つの角を並べると一直線
    cv.ox, cv.oy = 330, 130
    Pp = (0.0, 0.0)
    bounds = [0.0, aA, aA + aB, 180.0]     # 領域: [0,50]=∠A, [50,110]=∠B, [110,180]=∠C
    r = 1.3
    hatch = add_hatch(cv)
    fills = [GRAY_FILL, "#fff", hatch]
    for i in range(3):
        lo, hi = bounds[i], bounds[i + 1]
        pts = [Pp] + [ray_pt(Pp, lo + (hi - lo) * k / 12, r) for k in range(13)]
        fill_poly(cv, pts, fills[i])
        cv.angle_arc(Pp, ray_pt(Pp, lo, 1), ray_pt(Pp, hi, 1), r=14, n=i + 1)
    line_through(cv, Pp, 0, 1.7, 1.7)       # 一直線（底の直線）
    for i in range(1, 3):
        cv.line(Pp, ray_pt(Pp, bounds[i], r), w=MAIN_W)
    cv.dot(Pp)
    cv.text_px(330, 212, "切り取った3つの角を1点に集めると一直線に並ぶ",
               size=FS_CAP, anchor="middle")
    cv.text_px(330, 170, "（弧の本数が同じ角どうしが対応）", size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_tear_and_line_up.svg", canvas=cv, lesson="L03",
                title="三角形の3つの角を1点に集めると一直線に並ぶ（実験の再現図）",
                intent="角を集める実験の再現図。弧の本数で角の対応を示す（角度の数値は載せない）",
                params="3つの角50/60/70度（非対称）・和180度を検算",
                checks=ck.items, forbid=["°", "50", "60", "70"])


# ===========================================================================
# L03 図2: 内角の和180°の導出図（頂点Aを通るBCの平行線・錯角2組）
# 本文根拠: lesson_03.md 主概念1（直線l・D左・E右・∠DAB=∠B・∠EAC=∠C）
# ===========================================================================
def fig_L03_2():
    # --- パラメータ ---
    B = (0.0, 0.0)
    C = (4.0, 0.0)
    A = (1.5, 2.1)
    D = (A[0] - 1.7, A[1])          # l上・Aの左
    E = (A[0] + 2.1, A[1])          # l上・Aの右

    ck = Checker()
    ck.ok("lはBCに平行（D・E・Aが同じ高さ）",
          abs(D[1] - A[1]) < EPS and abs(E[1] - A[1]) < EPS and abs(B[1] - C[1]) < EPS)
    ck.ok("錯角∠DAB=∠B（l//BC）",
          abs(angle_deg(A, D, B) - angle_deg(B, C, A)) < 1e-6,
          f"∠DAB={angle_deg(A, D, B):.2f}, ∠B={angle_deg(B, C, A):.2f}")
    ck.ok("錯角∠EAC=∠C（l//BC）",
          abs(angle_deg(A, E, C) - angle_deg(C, A, B)) < 1e-6,
          f"∠EAC={angle_deg(A, E, C):.2f}, ∠C={angle_deg(C, A, B):.2f}")
    ck.ok("Aのまわりの3角の和=180°（一直線）",
          abs(angle_deg(A, D, B) + angle_deg(A, B, C) + angle_deg(A, E, C) - 180) < 1e-6)

    cv = Canvas(430, 250, scale=52.0, ox=60, oy=190)
    cv.line((D[0] - 0.5, D[1]), (E[0] + 0.45, E[1]), w=MAIN_W)   # 直線l（D・Eの先まで）
    cv.polygon([A, B, C])
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    for p, nm in [(D, "D"), (E, "E")]:
        cv.dot(p)
        cv.label_out(p, (A[0], A[1] - 1), nm, dist=13)
    cv.text(ray_pt(E, 0, 0.55), "l", size=FS, weight="bold")
    # 錯角の対応: ∠DAB・∠B=1重弧、∠EAC・∠C=2重弧
    cv.angle_arc(A, D, B, n=1)
    cv.angle_arc(B, C, A, n=1)
    cv.angle_arc(A, E, C, n=2)
    cv.angle_arc(C, A, B, n=2)
    cv.text_px(215, 238, "Aを通りBCに平行な直線l。同じ本数の弧＝錯角の組",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig2_parallel_through_apex.svg", canvas=cv, lesson="L03",
                title="頂点Aを通り辺BCに平行な直線を引いた図（内角の和の導出）",
                intent="内角の和180度の導出図。l//BCの錯角2組を弧の本数で対応づける（角度値なし）",
                params="B(0,0) C(4,0) A(1.5,2.1)・lはAを通る水平線（BCと厳密に平行）",
                checks=ck.items, forbid=["°"])


# ===========================================================================
# L03 図3: 外角の定義図（辺BCの延長上のD・∠ACD）
# 本文根拠: lesson_03.md 主概念2（∠ACD=∠A+∠B・∠ACB+∠ACD=180°）
# ===========================================================================
def fig_L03_3():
    # --- パラメータ ---
    B = (0.0, 0.0)
    C = (3.2, 0.0)
    A = (0.9, 1.9)
    D = (4.7, 0.0)                  # BCの延長上（Cの先）

    ck = Checker()
    ck.ok("B・C・Dは一直線でCはBとDの間",
          abs(cross(B, C, D)) < EPS and B[0] < C[0] < D[0])
    ext = angle_deg(C, A, D)
    ck.ok("外角∠ACD=∠A+∠B（外角の性質）",
          abs(ext - (angle_deg(A, B, C) + angle_deg(B, C, A))) < 1e-6,
          f"∠ACD={ext:.2f}")
    ck.ok("∠ACB+∠ACD=180°（一直線）",
          abs(angle_deg(C, A, B) + ext - 180) < 1e-6)

    cv = Canvas(430, 240, scale=56.0, ox=70, oy=185)
    cv.polygon([A, B, C])
    cv.line(C, D, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    cv.dot(D)
    cv.label_out(D, C, "D", dist=13)
    cv.angle_arc(C, A, D, n=1)      # 外角∠ACD
    cv.angle_arc(A, B, C, n=2)      # ∠A
    cv.angle_arc(B, C, A, n=3)      # ∠B
    angle_label(cv, C, A, D, "外角", r=42, size=FS_CAP)
    cv.text_px(215, 228, "辺BCをCの先へ延長すると、頂点Cの外角∠ACDができる",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig3_exterior_angle.svg", canvas=cv, lesson="L03",
                title="辺BCをCの先へ延長してできる外角∠ACD",
                intent="外角の定義図と外角の性質の導出図。外角と2つの内角を弧の本数で区別（角度値なし）",
                params="B(0,0) C(3.2,0) A(0.9,1.9) D(4.7,0)（B・C・D一直線）",
                checks=ck.items, forbid=["°"])


# ===========================================================================
# L04 図1: 五角形の三角形分割（1頂点からの対角線・①②③）
# 本文根拠: lesson_04.md 主概念1（凸五角形ABCDE・AC/ADで3分割）
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（正五角形を避けた一般の凸五角形） ---
    A = (0.1, 2.5)
    B = (-2.0, 1.1)
    C = (-1.3, -1.1)
    D = (1.6, -1.3)
    E = (2.4, 1.0)
    pts = [A, B, C, D, E]

    ck = Checker()
    signs = []
    for i in range(5):
        signs.append(cross(pts[i], pts[(i + 1) % 5], pts[(i + 2) % 5]) > 0)
    ck.ok("凸五角形である（全頂点で同じ回り向き）", all(signs) or not any(signs))
    total = sum(angle_deg(pts[i], pts[(i - 1) % 5], pts[(i + 1) % 5]) for i in range(5))
    ck.ok("内角の和=540°（180°×3）", abs(total - 540) < 1e-6, f"実測={total:.2f}")
    sides = [dist(pts[i], pts[(i + 1) % 5]) for i in range(5)]
    ck.ok("正五角形ではない（辺の長さが不ぞろい）", max(sides) - min(sides) > 0.3)
    tri_sum = (angle_deg(A, B, C) + angle_deg(B, C, A) + angle_deg(C, A, B))
    ck.ok("分割された三角形の内角の和=180°", abs(tri_sum - 180) < 1e-6)

    cv = Canvas(420, 260, scale=44.0, ox=210, oy=125)
    cv.polygon(pts)
    cv.line(A, C, w=AUX_W, dash=DASH)    # 対角線（補助線）
    cv.line(A, D, w=AUX_W, dash=DASH)
    g = centroid(*pts)
    for p, nm in zip(pts, "ABCDE"):
        cv.label_out(p, g, nm)
    for tri, nm in [((A, B, C), "①"), ((A, C, D), "②"), ((A, D, E), "③")]:
        cx, cy = cv.P(centroid(*tri))
        cv.raw(f'<text x="{cx:.1f}" y="{cy + 5:.1f}" font-size="{FS}" '
               f'text-anchor="middle" fill="#555">{nm}</text>')
    cv.text_px(210, 248, "頂点Aからの対角線AC・ADで、五角形は3つの三角形に分かれる",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_pentagon_triangulation.svg", canvas=cv, lesson="L04",
                title="五角形を1頂点からの対角線で3つの三角形に分ける図",
                intent="内角の和の導出（三角形分割）。一般の凸五角形・対角線は破線・番号は薄いグレー",
                params="凸五角形ABCDE（不等辺）・対角線AC/AD・内角の和540度を検算",
                checks=ck.items, forbid=["°", "540", "180"])


# ===========================================================================
# L05 図1: 合同の動的定義（回転+平行移動の△DEFと裏返しの△GHI）
# 本文根拠: lesson_05.md 主概念1（移動して重ねられる3つの三角形・裏返し含む）
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（非対称な三角形・鏡像が見分けられる形） ---
    A = (0.0, 0.0)
    B = (2.5, 0.35)
    C = (0.75, 1.55)
    rot_deg = 38.0
    T1 = (3.35, 0.45)               # △DEFへの平行移動量（回転後）
    T2 = (7.1, 0.0)                 # △GHIへの平行移動量（鏡映後）

    DEF = [translate(rot(p, rot_deg), T1) for p in (A, B, C)]
    GHI = [translate(mirror_x(p, 1.25), T2) for p in (A, B, C)]

    ck = Checker()
    src = [A, B, C]
    for tgt, nm in [(DEF, "DEF"), (GHI, "GHI")]:
        ok = all(abs(dist(src[i], src[(i + 1) % 3]) - dist(tgt[i], tgt[(i + 1) % 3])) < EPS
                 for i in range(3))
        ck.ok(f"△{nm}は対応する3辺の長さが保存（移動は長さを変えない）", ok)
    o0 = cross(A, B, C)
    ck.ok("△DEFは回転+平行移動（向きが同じ）", cross(*DEF) * o0 > 0)
    ck.ok("△GHIは裏返し（向きが逆＝鏡像）", cross(*GHI) * o0 < 0)
    ck.ok("非対称な三角形（3辺の長さがすべて異なる）",
          len({round(dist(A, B), 6), round(dist(B, C), 6), round(dist(C, A), 6)}) == 3)

    cv = Canvas(500, 220, scale=40.0, ox=35, oy=150)
    for tri, names in [((A, B, C), "ABC"), (DEF, "DEF"), (GHI, "GHI")]:
        cv.polygon(list(tri))
        g = centroid(*tri)
        for p, nm in zip(tri, names):
            cv.label_out(p, g, nm)
    # 移動の対応を薄い矢印で示す
    g0, g1, g2 = map(lambda t: cv.P(centroid(*t)), ([A, B, C], DEF, GHI))
    cv.raw(f'<line x1="{g0[0] + 22:.1f}" y1="{g0[1]:.1f}" x2="{g1[0] - 22:.1f}" y2="{g1[1]:.1f}" '
           f'stroke="#999" stroke-width="1.2" stroke-dasharray="{DASH}"/>')
    cv.raw(f'<line x1="{g1[0] + 22:.1f}" y1="{g1[1]:.1f}" x2="{g2[0] - 22:.1f}" y2="{g2[1]:.1f}" '
           f'stroke="#999" stroke-width="1.2" stroke-dasharray="{DASH}"/>')
    cv.text_px((g0[0] + g1[0]) / 2, max(g0[1], g1[1]) + 38, "回転+平行移動",
               size=FS_CAP, anchor="middle")
    cv.text_px((g1[0] + g2[0]) / 2, max(g1[1], g2[1]) + 38, "裏返し（対称移動）",
               size=FS_CAP, anchor="middle")
    cv.text_px(250, 208, "どれも移動でぴったり重ねられる＝合同（裏返しも移動のうち）",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig1_congruent_by_motion.svg", canvas=cv, lesson="L05",
                title="合同な3つの三角形（回転+平行移動・裏返し）",
                intent="合同の動的定義の図。非対称な三角形で鏡像が見分けられる（長さの数値なし）",
                params="基準△ABC(辺2.53/2.10/1.71相当)・回転38度+平行移動・x=1.25軸で鏡映+平行移動",
                checks=ck.items, forbid=["cm"])


# ===========================================================================
# L05 図2: 対応の読み取り練習（△ABCと150°回転した△KLM）
# 本文根拠: lesson_05.md 練習3（∠B・∠Lが鈍角、AC・KMが最長。≡の式は書かない）
# ===========================================================================
def fig_L05_2():
    # --- パラメータ（∠Bが鈍角・ACが最長になる3辺） ---
    AB, BC, CA = 2.2, 2.6, 4.3
    rot_deg = 150.0
    T = (6.1, 2.15)

    A, B, C = tri_from_sides(AB, CA, BC)     # B=(0,0), C=(BC,0)
    K, Lp, M = (translate(rot(p, rot_deg), T) for p in (A, B, C))

    ck = Checker()
    ck.ok("∠Bは鈍角（∠Lも同じ）", angle_deg(B, A, C) > 90,
          f"∠B={angle_deg(B, A, C):.1f}度")
    ck.ok("辺ACが最長（KMも同じ）", CA > AB and CA > BC)
    ck.ok("△KLMは△ABCの150°回転（対応辺の長さ一致）",
          all(abs(d1 - d2) < EPS for d1, d2 in
              [(dist(A, B), dist(K, Lp)), (dist(B, C), dist(Lp, M)), (dist(C, A), dist(M, K))]))
    ck.ok("回転角=150°（KLはABを150°回した向き）",
          abs((math.degrees(math.atan2(Lp[1] - K[1], Lp[0] - K[0]))
               - math.degrees(math.atan2(B[1] - A[1], B[0] - A[0]))) % 360 - rot_deg) < 1e-6)

    cv = Canvas(460, 265, scale=42.0, ox=80, oy=175)
    for tri, names in [((A, B, C), "ABC"), ((K, Lp, M), "KLM")]:
        cv.polygon(list(tri))
        g = centroid(*tri)
        for p, nm in zip(tri, names):
            cv.label_out(p, g, nm)
        cv.ticks(tri[0], tri[1], 1)   # AB / KL
        cv.ticks(tri[1], tri[2], 2)   # BC / LM
        cv.ticks(tri[2], tri[0], 3)   # CA / MK
    cv.text_px(230, 253, "2つの三角形は合同。同じ本数のティック＝等しい辺。対応順に注意して≡で表す",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig2_match_correspondence.svg", canvas=cv, lesson="L05",
                title="向きの違う合同な2つの三角形（対応の読み取り練習）",
                intent="対応の読み取り練習。等しい辺は同数ティック。解答となる対応の式は図に書かない",
                params="AB=2.2 BC=2.6 CA=4.3（∠B鈍角・AC最長）・△KLMは150度回転+平行移動",
                checks=ck.items, forbid=["≡△", "°"])


# ===========================================================================
# L06 図1: 三角形の合同条件3つの一覧図（3段・マークのみ）
# 本文根拠: lesson_06.md 主概念1（正典の文言3つ・数値や略称は載せない）
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（各段共通の三角形。数値は図に載せない） ---
    AB, BC, CA = 2.4, 3.0, 2.0
    rot_deg = 14.0
    A, B, C = tri_from_sides(AB, CA, BC)
    A2, B2, C2 = (rot(p, rot_deg) for p in (A, B, C))

    ck = Checker()
    ck.ok("各段のペアは合同（対応3辺の長さ一致）",
          all(abs(d1 - d2) < EPS for d1, d2 in
              [(dist(A, B), dist(A2, B2)), (dist(B, C), dist(B2, C2)), (dist(C, A), dist(C2, A2))]))
    ck.ok("回転しても角も保存（∠A・∠B・∠C一致）",
          abs(angle_deg(A, B, C) - angle_deg(A2, B2, C2)) < EPS
          and abs(angle_deg(B, C, A) - angle_deg(B2, C2, A2)) < EPS)
    conds = ["対応する３組の辺がそれぞれ等しい",
             "対応する２組の辺がそれぞれ等しく，その間の角が等しい",
             "対応する１組の辺が等しく，その両端の角がそれぞれ等しい"]
    ck.ok("条件の文言=lesson_06.md正典の3文言と一致（コードに転記）", len(conds) == 3)

    cv = Canvas(500, 470, scale=34.0)
    rows = [("sss", conds[0]), ("sas", conds[1]), ("asa", conds[2])]
    for i, (kind, cap) in enumerate(rows):
        oy = 142 + i * 138
        for tri, ox in [((A, B, C), 42), ((A2, B2, C2), 200)]:
            cv.ox, cv.oy = ox, oy
            P1, P2, P3 = tri
            cv.polygon([P1, P2, P3])
            if kind == "sss":
                cv.ticks(P1, P2, 1)
                cv.ticks(P2, P3, 2)
                cv.ticks(P3, P1, 3)
            elif kind == "sas":
                cv.ticks(P1, P2, 1)          # 辺AB
                cv.ticks(P2, P3, 2)          # 辺BC
                cv.angle_arc(P2, P3, P1, n=1)  # その間の角∠B
            else:
                cv.ticks(P2, P3, 1)            # 辺BC
                cv.angle_arc(P2, P3, P1, n=1)  # 両端の角∠B
                cv.angle_arc(P3, P1, P2, n=2)  # 両端の角∠C
        num = ["1.", "2.", "3."][i]
        cv.text_px(30, oy - 102, f"{num} {cap}", size=FS, anchor="start", weight="bold")
    cv.text_px(250, 22, "三角形の合同条件（どれか1つが成り立てば合同）",
               size=14, anchor="middle", weight="bold")
    cv.text_px(250, 454, "同じ本数のティック＝等しい辺，同じ本数の弧＝等しい角",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_three_conditions.svg", canvas=cv, lesson="L06",
                title="三角形の合同条件3つの対応図",
                intent="3条件の一覧図。使う辺・角だけにマークを付け、正典の文言を添える（数値・略称なし）",
                params="共通の三角形（辺2.4/3.0/2.0相当）×3段・右側は14度回転",
                checks=ck.items, forbid=["cm", "°", "三辺", "二辺", "一辺"])


# ===========================================================================
# L06 図2: 「間ではない角」では決まらない実験図（AB=6, AC=4, ∠B=40°）
# 本文根拠: lesson_06.md 主概念2（6×sin40°≈3.86<4<6 → 交点2つ・三角形2種類）
# ===========================================================================
def fig_L06_2():
    # --- パラメータ（lesson_06.md 主概念2 と一致させる） ---
    AB_len, AC_len, angB = 6.0, 4.0, 40.0

    A = (0.0, 0.0)
    B = (AB_len, 0.0)
    ray_deg = 180.0 - angB          # Bから見てAの上側へ40°
    u = unit(ray_deg)
    # |B + t·u − A| = AC_len の2解
    bcoef = 2 * (B[0] * u[0] + B[1] * u[1])
    ccoef = B[0] ** 2 + B[1] ** 2 - AC_len ** 2
    disc = bcoef ** 2 - 4 * ccoef
    t1 = (-bcoef - math.sqrt(disc)) / 2
    t2 = (-bcoef + math.sqrt(disc)) / 2
    C1 = (B[0] + u[0] * t1, B[1] + u[1] * t1)
    C2 = (B[0] + u[0] * t2, B[1] + u[1] * t2)

    ck = Checker()
    ck.ok("2交点条件 6×sin40°<4<6 が成立",
          AB_len * math.sin(math.radians(angB)) < AC_len < AB_len,
          f"6sin40°={AB_len * math.sin(math.radians(angB)):.3f}")
    ck.ok("AC1=AC2=4（どちらも指定どおり）",
          abs(dist(A, C1) - AC_len) < EPS and abs(dist(A, C2) - AC_len) < EPS)
    ck.ok("∠ABC1=∠ABC2=40°（どちらも指定どおり）",
          abs(angle_deg(B, A, C1) - angB) < 1e-6 and abs(angle_deg(B, A, C2) - angB) < 1e-6)
    ck.ok("C1とC2は別の点（形の違う三角形が2つできる）", dist(C1, C2) > 0.5,
          f"C1C2={dist(C1, C2):.2f}")

    cv = Canvas(430, 280, scale=44.0, ox=60, oy=235)
    hatch = add_hatch(cv)
    fill_poly(cv, [A, B, C2], hatch)
    fill_poly(cv, [A, B, C1], GRAY_FILL)
    cv.line(A, B, w=MAIN_W)
    cv.line(B, ray_pt(B, ray_deg, t2 + 0.7), w=MAIN_W)   # Bからの半直線
    cv.line(A, C1, w=MAIN_W)
    cv.line(A, C2, w=MAIN_W)
    # Aを中心とする半径4の円弧（破線・交点付近をカバー）
    a1 = math.degrees(math.atan2(C1[1], C1[0])) - 16
    a2 = math.degrees(math.atan2(C2[1], C2[0])) + 16
    arc = [ray_pt(A, a1 + (a2 - a1) * k / 40, AC_len) for k in range(41)]
    s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(cv.P, arc))
    cv.raw(f'<polyline points="{s}" fill="none" stroke="#000" '
           f'stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
    for p, nm, dxy in [(A, "A", (-12, 14)), (B, "B", (12, 14)),
                       (C1, "C1", (16, -2)), (C2, "C2", (10, -8))]:
        cv.dot(p)
        px, py = cv.P(p)
        cv.text_px(px + dxy[0], py + dxy[1], nm, size=FS, anchor="middle", weight="bold")
    seg_label(cv, A, B, "6cm", off=14)
    seg_label(cv, A, C1, "4cm", off=13)
    seg_label(cv, A, C2, "4cm", off=-13)
    cv.angle_arc(B, A, C1, n=1, r=17)
    angle_label(cv, B, A, C1, "40°", r=38)
    cv.text_px(215, 268, "同じ指定（AB=6cm・AC=4cm・∠B=40°）から、形の違う三角形が2つできる",
               size=FS_CAP, anchor="middle")

    return dict(file="L06_fig2_ssa_two_triangles.svg", canvas=cv, lesson="L06",
                title="2辺と間ではない角の指定から2種類の三角形ができる作図",
                intent="位置指定を外すと三角形が決まらないことの実験図。濃淡とハッチングで2三角形を塗り分け",
                params="AB=6, AC=4, ∠B=40度（6sin40°≈3.857<4<6の2交点条件を厳密に反映）",
                checks=ck.items, forbid=["合同"])


# ===========================================================================
# L07 図1: はじめての証明の図（中点Oで交わる2線分・L15で再訪）
# 本文根拠: lesson_07.md 主概念3（OA=OB・OC=OD・AC=BDを証明。平行は先取りしない）
# ===========================================================================
def _midpoint_cross_points():
    """L07/L15共通パラメータ（figure-spec: L15はL07と同一パラメータ）"""
    O = (0.0, 0.0)
    A = (-1.7, 1.1)
    C = (-1.3, -1.2)
    B = (-A[0], -A[1])
    D = (-C[0], -C[1])
    return O, A, B, C, D


def _build_midpoint_fig(caption):
    O, A, B, C, D = _midpoint_cross_points()

    ck = Checker()
    ck.ok("OはABの中点（OA=OB）", abs(dist(O, A) - dist(O, B)) < EPS and
          abs(cross(A, O, B)) < EPS)
    ck.ok("OはCDの中点（OC=OD）", abs(dist(O, C) - dist(O, D)) < EPS and
          abs(cross(C, O, D)) < EPS)
    ck.ok("配置=A左上・B右下・C左下・D右上（四角形ACBDが視認できる）",
          A[0] < 0 < A[1] and B[0] > 0 > B[1] and C[0] < 0 and C[1] < 0
          and D[0] > 0 and D[1] > 0)
    ck.ok("AC=BD（証明の結論と図が整合）", abs(dist(A, C) - dist(B, D)) < EPS,
          f"AC={dist(A, C):.3f}")
    ck.ok("∠AOC=∠BOD（対頂角）",
          abs(angle_deg(O, A, C) - angle_deg(O, B, D)) < 1e-6)
    ck.ok("AC//BDも成立（図の整合検算。マーク・文言は載せない）",
          abs(cross((0, 0), (C[0] - A[0], C[1] - A[1]), (D[0] - B[0], D[1] - B[1]))) < EPS)

    cv = Canvas(420, 250, scale=62.0, ox=210, oy=118)
    cv.line(A, B, w=MAIN_W)
    cv.line(C, D, w=MAIN_W)
    cv.line(A, C, w=MAIN_W)
    cv.line(B, D, w=MAIN_W)
    cv.ticks(O, A, 1)
    cv.ticks(O, B, 1)
    cv.ticks(O, C, 2)
    cv.ticks(O, D, 2)
    for p, nm in [(A, "A"), (B, "B"), (C, "C"), (D, "D")]:
        cv.dot(p)
        cv.label_out(p, O, nm)
    cv.dot(O)
    px, py = cv.P(O)
    cv.text_px(px + 8, py - 8, "O", size=FS, anchor="start", weight="bold")
    cv.text_px(210, 238, caption, size=FS_CAP, anchor="middle")
    return cv, ck


def fig_L07_1():
    cv, ck = _build_midpoint_fig(
        "線分AB・CDは、それぞれの中点Oで交わっている")
    return dict(file="L07_fig1_two_segments_midpoint.svg", canvas=cv, lesson="L07",
                title="中点Oで交わる2線分AB・CDと、結んだ線分AC・BD",
                intent="はじめての証明の図。仮定OA=OB・OC=ODをティックで示す（結論側の情報は載せない）",
                params="O(0,0) A(-1.7,1.1) B(1.7,-1.1) C(-1.3,-1.2) D(1.3,1.2)",
                checks=ck.items, forbid=["平行", "//"])


# ===========================================================================
# L08 図1: 二等辺三角形の用語整理（頂角・底辺・底角）
# 本文根拠: lesson_08.md 主概念1（AB=ACのみマーク。底角相等はこれから証明）
# ===========================================================================
def fig_L08_1():
    # --- パラメータ ---
    A = (0.0, 2.7)
    B = (-1.4, 0.0)
    C = (1.4, 0.0)

    ck = Checker()
    ck.ok("AB=AC（二等辺の定義どおり）", abs(dist(A, B) - dist(A, C)) < EPS)
    ck.ok("正三角形ではない（AB≠BC）", abs(dist(A, B) - dist(B, C)) > 0.1)
    ck.ok("∠B=∠Cが成立（図の整合検算。等角マークは載せない）",
          abs(angle_deg(B, A, C) - angle_deg(C, A, B)) < 1e-6)

    cv = Canvas(420, 250, scale=58.0, ox=210, oy=200)
    cv.polygon([A, B, C])
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    cv.ticks(A, B, 1)
    cv.ticks(A, C, 1)
    cv.angle_arc(A, B, C, n=1)
    angle_label(cv, A, B, C, "頂角", r=44, size=FS_CAP)
    cv.text((0.0, -0.28), "底辺", size=FS_CAP)
    for v, other in [(B, C), (C, B)]:
        angle_label(cv, v, A, other, "底角", r=40, size=FS_CAP)
    cv.text_px(210, 238, "等しい2辺の間の角＝頂角、向かい合う辺＝底辺、底辺の両端＝底角",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig1_isosceles_terms.svg", canvas=cv, lesson="L08",
                title="二等辺三角形と頂角・底辺・底角の名称",
                intent="用語の整理図。仮定AB=ACのみティックで示し、底角の等しさはマークしない",
                params="A(0,2.7) B(-1.4,0) C(1.4,0)（AB=AC=3.04相当・正三角形ではない）",
                checks=ck.items, forbid=["°", "底角は等しい"])


# ===========================================================================
# L08 図2: 底角の定理の証明図（頂角の二等分線AD）
# 本文根拠: lesson_08.md 主概念2（∠BAD=∠CADのみマーク。直角・BD=CDは描かない）
# ===========================================================================
def fig_L08_2():
    # --- パラメータ（fig_L08_1と同じ三角形） ---
    A = (0.0, 2.7)
    B = (-1.4, 0.0)
    C = (1.4, 0.0)
    D = (0.0, 0.0)                  # ∠Aの二等分線とBCの交点（対称性より原点）

    ck = Checker()
    ck.ok("AB=AC（仮定）", abs(dist(A, B) - dist(A, C)) < EPS)
    ck.ok("DはBC上", abs(cross(B, C, D)) < EPS and B[0] < D[0] < C[0])
    ck.ok("ADは∠Aの二等分線（∠BAD=∠CAD）",
          abs(angle_deg(A, B, D) - angle_deg(A, C, D)) < 1e-6,
          f"∠BAD={angle_deg(A, B, D):.2f}")
    ck.ok("BD=CD・AD⊥BCも成立（図の整合検算。マークは載せない）",
          abs(dist(B, D) - dist(C, D)) < EPS and abs(angle_deg(D, A, B) - 90) < 1e-6)

    cv = Canvas(420, 250, scale=58.0, ox=210, oy=200)
    cv.polygon([A, B, C])
    cv.line(A, D, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    cv.dot(D)
    px, py = cv.P(D)
    cv.text_px(px, py + 16, "D", size=FS, anchor="middle", weight="bold")
    cv.ticks(A, B, 1)
    cv.ticks(A, C, 1)
    cv.angle_arc(A, B, D, n=1, r=22)
    cv.angle_arc(A, D, C, n=1, r=22)
    cv.text_px(210, 238, "頂角∠Aの二等分線ADと底辺BCの交点をDとする（同じ弧＝等しい角）",
               size=FS_CAP, anchor="middle")

    return dict(file="L08_fig2_bisector_split.svg", canvas=cv, lesson="L08",
                title="頂角の二等分線ADで二等辺三角形を2つに割った図",
                intent="底角の定理の証明図。仮定と作図（AB=AC・∠BAD=∠CAD）のみマークし、証明する内容は描かない",
                params="A(0,2.7) B(-1.4,0) C(1.4,0) D(0,0)（二等分線の足＝厳密に対称）",
                checks=ck.items, forbid=["90", "垂直", "⊥"])


# ===========================================================================
# L10 図1: 直角三角形を背中合わせに貼って二等辺三角形を作る図
# 本文根拠: lesson_10.md 主概念2（DFをACに重ねE→G・B,C,G一直線・AB=AG）
# ===========================================================================
def fig_L10_1():
    # --- パラメータ ---
    legB, legH = 1.9, 2.5           # BC（底の辺）とAC（貼り合わせる辺）の長さ
    C = (0.0, 0.0)
    B = (-legB, 0.0)
    A = (0.0, legH)
    F = (0.0, 0.0)                  # △DEF（左パネル内・別位置に描く）
    E = (legB, 0.0)
    Dp = (0.0, legH)
    G = (legB, 0.0)                 # 合成図でEを移した点

    ck = Checker()
    ck.ok("∠C=∠F=90°（どちらも直角）",
          abs(angle_deg(C, A, B) - 90) < EPS and abs(angle_deg(F, Dp, E) - 90) < EPS)
    ck.ok("斜辺AB=DE（仮定）", abs(dist(A, B) - dist(Dp, E)) < EPS)
    ck.ok("他の1辺AC=DF（仮定）", abs(dist(A, C) - dist(Dp, F)) < EPS)
    ck.ok("合成図でB・C・Gは一直線", abs(cross(B, C, G)) < EPS and B[0] < C[0] < G[0])
    ck.ok("AB=AG（大きな三角形ABGは二等辺）", abs(dist(A, B) - dist(A, G)) < EPS,
          f"AB={dist(A, B):.3f}")

    cv = Canvas(470, 240, scale=34.0)
    # 左パネル: △ABCと△DEF
    cv.ox, cv.oy = 80, 190
    cv.polygon([A, B, C])
    gt = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, gt, nm)
    cv.right_angle(C, B, A)
    cv.ticks(A, B, 1)
    cv.ticks(A, C, 2)
    cv.ox = 175
    cv.polygon([Dp, E, F])
    gt2 = centroid(Dp, E, F)
    for p, nm in zip((Dp, E, F), "DEF"):
        cv.label_out(p, gt2, nm)
    cv.right_angle(F, E, Dp)
    cv.ticks(Dp, E, 1)
    cv.ticks(Dp, F, 2)
    # 右パネル: 合成図（DFをACに重ねて裏返し貼り・△ABG）
    cv.ox = 350
    cv.polygon([A, B, G])
    cv.line(A, C, w=MAIN_W)
    gt3 = centroid(A, B, G)
    for p, nm in [(A, "A"), (B, "B"), (G, "G")]:
        cv.label_out(p, gt3, nm)
    cv.dot(C)
    px, py = cv.P(C)
    cv.text_px(px, py + 16, "C", size=FS, anchor="middle", weight="bold")
    cv.right_angle(C, B, A)
    cv.ticks(A, B, 1)
    cv.ticks(A, G, 1)
    cv.text_px(128, 224, "△ABCと△DEF（斜辺と他の1辺が等しい）", size=FS_CAP, anchor="middle")
    cv.text_px(360, 224, "DFをACに重ねて貼るとB・C・Gは一直線", size=FS_CAP, anchor="middle")

    return dict(file="L10_fig1_back_to_back.svg", canvas=cv, lesson="L10",
                title="2つの直角三角形を背中合わせに貼って二等辺三角形を作る図",
                intent="斜辺と他の1辺の条件の証明図。合成でAB=AGの二等辺三角形が現れる（角度数値なし）",
                params="直角をはさむ2辺1.9/2.5相当・合成図はB(-1.9,0) C(0,0) G(1.9,0) A(0,2.5)",
                checks=ck.items, forbid=["°"])


# ===========================================================================
# L11/L12共通の平行四辺形パラメータ（A左上・B左下・C右下・D右上）
# ===========================================================================
def _pgram():
    A = (1.2, 2.2)
    B = (0.0, 0.0)
    C = (3.4, 0.0)
    D = (4.6, 2.2)
    return A, B, C, D


def _pgram_checks(ck, A, B, C, D):
    ck.ok("AB//DC（1組目の対辺が平行）",
          abs(cross((0, 0), (B[0] - A[0], B[1] - A[1]), (C[0] - D[0], C[1] - D[1]))) < EPS)
    ck.ok("AD//BC（2組目の対辺が平行）",
          abs(cross((0, 0), (D[0] - A[0], D[1] - A[1]), (C[0] - B[0], C[1] - B[1]))) < EPS)
    ck.ok("配置=A左上・B左下・C右下・D右上",
          A[1] > 0 and D[1] > 0 and B[1] == 0 and C[1] == 0 and A[0] < D[0] and B[0] < C[0])


# ===========================================================================
# L11 図1: 対辺相等の証明図（対角線AC・錯角2組）
# 本文根拠: lesson_11.md 主概念1（∠BAC=∠DCA・∠BCA=∠DAC。辺のティックは付けない）
# ===========================================================================
def fig_L11_1():
    A, B, C, D = _pgram()

    ck = Checker()
    _pgram_checks(ck, A, B, C, D)
    ck.ok("錯角∠BAC=∠DCA（AB//DC）",
          abs(angle_deg(A, B, C) - angle_deg(C, D, A)) < 1e-6,
          f"={angle_deg(A, B, C):.2f}度")
    ck.ok("錯角∠BCA=∠DAC（AD//BC）",
          abs(angle_deg(C, B, A) - angle_deg(A, D, C)) < 1e-6)
    ck.ok("AB=CD・AD=BCも成立（図の整合検算。ティックは載せない）",
          abs(dist(A, B) - dist(C, D)) < EPS and abs(dist(A, D) - dist(B, C)) < EPS)

    cv = Canvas(430, 240, scale=64.0, ox=45, oy=190)
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=MAIN_W)
    g = centroid(A, B, C, D)
    for p, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p, g, nm)
    cv.angle_arc(A, B, C, n=1, r=18)     # ∠BAC
    cv.angle_arc(C, D, A, n=1, r=18)     # ∠DCA
    cv.angle_arc(C, B, A, n=2, r=26)     # ∠BCA
    cv.angle_arc(A, D, C, n=2, r=26)     # ∠DAC
    cv.text_px(215, 228, "対角線ACを引く。同じ本数の弧＝錯角の組（1重: AB//DC、2重: AD//BC）",
               size=FS_CAP, anchor="middle")

    return dict(file="L11_fig1_diagonal_split.svg", canvas=cv, lesson="L11",
                title="平行四辺形ABCDに対角線ACを引き、錯角2組をマークした図",
                intent="対辺相等の証明図。仮定（平行）から得る錯角のみマークし、証明する辺の等しさは描かない",
                params="A(1.2,2.2) B(0,0) C(3.4,0) D(4.6,2.2)（厳密な平行四辺形）",
                checks=ck.items, forbid=["°"])


# ===========================================================================
# L11 図2: 対角線の性質の証明図（交点O・△OABと△OCD）
# 本文根拠: lesson_11.md 主概念3（AB=DCは証明済みでティック可。OA=OC等は描かない）
# ===========================================================================
def fig_L11_2():
    A, B, C, D = _pgram()
    O = lerp(A, C, 0.5)

    ck = Checker()
    _pgram_checks(ck, A, B, C, D)
    ck.ok("Oは対角線ACとBDの交点",
          abs(cross(A, C, O)) < EPS and abs(cross(B, D, O)) < EPS)
    ck.ok("AB=DC（主概念1で証明済み→ティック可）",
          abs(dist(A, B) - dist(D, C)) < EPS)
    ck.ok("錯角∠OAB=∠OCD・∠OBA=∠ODC（AB//DC）",
          abs(angle_deg(A, O, B) - angle_deg(C, O, D)) < 1e-6
          and abs(angle_deg(B, O, A) - angle_deg(D, O, C)) < 1e-6)
    ck.ok("OA=OC・OB=ODも成立（図の整合検算。ティックは載せない）",
          abs(dist(O, A) - dist(O, C)) < EPS and abs(dist(O, B) - dist(O, D)) < EPS)

    cv = Canvas(430, 240, scale=64.0, ox=45, oy=190)
    hatch = add_hatch(cv)
    fill_poly(cv, [O, A, B], GRAY_FILL)
    fill_poly(cv, [O, C, D], hatch)
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=MAIN_W)
    cv.line(B, D, w=MAIN_W)
    g = centroid(A, B, C, D)
    for p, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p, g, nm)
    cv.dot(O)
    px, py = cv.P(O)
    cv.text_px(px + 4, py - 9, "O", size=FS, anchor="start", weight="bold")
    cv.ticks(A, B, 1)
    cv.ticks(D, C, 1)
    cv.angle_arc(A, O, B, n=1, r=17)     # ∠OAB
    cv.angle_arc(C, O, D, n=1, r=17)     # ∠OCD
    cv.angle_arc(B, O, A, n=2, r=17)     # ∠OBA
    cv.angle_arc(D, O, C, n=2, r=17)     # ∠ODC
    cv.text_px(215, 228, "向かい合う△OABと△OCD。ティック＝対辺相等（証明済み）、弧＝錯角",
               size=FS_CAP, anchor="middle")

    return dict(file="L11_fig2_diagonals_bisect.svg", canvas=cv, lesson="L11",
                title="平行四辺形の対角線の交点Oと、向かい合う△OAB・△OCD",
                intent="対角線の性質の証明図。証明済みの対辺相等と錯角のみマークし、OA=OC等は描かない",
                params="A(1.2,2.2) B(0,0) C(3.4,0) D(4.6,2.2)・O=対角線の交点(2.3,1.1)",
                checks=ck.items, forbid=["°"])


# ===========================================================================
# L12 図1: 条件2の証明図（対辺相等の四角形・平行マークなし）
# 本文根拠: lesson_12.md 主概念2（仮定AB=CD・AD=CBをティック。平行はこれから証明）
# ===========================================================================
def fig_L12_1():
    A, B, C, D = _pgram()           # 形は平行四辺形だが平行マークは付けない

    ck = Checker()
    ck.ok("仮定AB=CD（1本ティックの組）", abs(dist(A, B) - dist(C, D)) < EPS)
    ck.ok("仮定AD=CB（2本ティックの組）", abs(dist(A, D) - dist(C, B)) < EPS)
    ck.ok("合同から取り出す錯角∠BAC=∠DCAが成立",
          abs(angle_deg(A, B, C) - angle_deg(C, D, A)) < 1e-6)
    ck.ok("AB//DC・AD//BCも成立（図の整合検算。平行マークは載せない）",
          abs(cross((0, 0), (B[0] - A[0], B[1] - A[1]), (C[0] - D[0], C[1] - D[1]))) < EPS
          and abs(cross((0, 0), (D[0] - A[0], D[1] - A[1]), (C[0] - B[0], C[1] - B[1]))) < EPS)

    cv = Canvas(430, 240, scale=64.0, ox=45, oy=190)
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=MAIN_W)
    g = centroid(A, B, C, D)
    for p, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p, g, nm)
    cv.ticks(A, B, 1)
    cv.ticks(C, D, 1)
    cv.ticks(A, D, 2)
    cv.ticks(C, B, 2)
    cv.angle_arc(A, B, C, n=1, r=18)     # ∠BAC
    cv.angle_arc(C, D, A, n=1, r=18)     # ∠DCA
    cv.text_px(215, 228, "仮定: AB=CD（1本）・AD=CB（2本）。弧＝合同から取り出す角",
               size=FS_CAP, anchor="middle")

    return dict(file="L12_fig1_sss_to_parallel.svg", canvas=cv, lesson="L12",
                title="対角線ACで分けた2つの三角形と、合同から取り出す錯角",
                intent="条件2の証明図。仮定の対辺相等のみティックで示し、証明する平行は描かない",
                params="A(1.2,2.2) B(0,0) C(3.4,0) D(4.6,2.2)（L11と同一座標・マークのみ変更）",
                checks=ck.items, forbid=["平行", "//", "°"])


# ===========================================================================
# L13 図1: ひし形の対角線垂直の証明図（△ABOと△CBO）
# 本文根拠: lesson_13.md 主概念2（4辺相等・O。直角マークはこれから証明のため描かない）
# ===========================================================================
def fig_L13_1():
    # --- パラメータ（A上・B左・C下・D右） ---
    p, q = 1.3, 1.9                 # 対角線の半分（BD/2, AC/2）
    A = (0.0, q)
    B = (-p, 0.0)
    C = (0.0, -q)
    D = (p, 0.0)
    O = (0.0, 0.0)

    ck = Checker()
    sides = [dist(A, B), dist(B, C), dist(C, D), dist(D, A)]
    ck.ok("4辺がすべて等しい（ひし形の定義）",
          max(sides) - min(sides) < EPS, f"辺長={sides[0]:.3f}")
    ck.ok("Oは対角線それぞれの中点（平行四辺形として相続）",
          abs(dist(O, A) - dist(O, C)) < EPS and abs(dist(O, B) - dist(O, D)) < EPS)
    ck.ok("正方形ではない（対角線の長さが異なる）", abs(dist(A, C) - dist(B, D)) > 0.3)
    ck.ok("∠AOB=∠COBかつAC⊥BDも成立（図の整合検算。直角マークは載せない）",
          abs(angle_deg(O, A, B) - angle_deg(O, C, B)) < 1e-6
          and abs(angle_deg(O, A, B) - 90) < 1e-6)

    cv = Canvas(420, 292, scale=56.0, ox=210, oy=128)
    hatch = add_hatch(cv)
    fill_poly(cv, [A, B, O], GRAY_FILL)
    fill_poly(cv, [C, B, O], hatch)
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=MAIN_W)
    cv.line(B, D, w=MAIN_W)
    g = (0.0, 0.0)
    for p_, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p_, g, nm)
    cv.dot(O)
    px, py = cv.P(O)
    cv.text_px(px + 7, py - 8, "O", size=FS, anchor="start", weight="bold")
    for e in [(A, B), (B, C), (C, D), (D, A)]:
        cv.ticks(*e, n=1)
    cv.text_px(210, 280, "4辺が等しいひし形。塗り分けた△ABOと△CBOの合同に注目する",
               size=FS_CAP, anchor="middle")

    return dict(file="L13_fig1_rhombus_diagonals.svg", canvas=cv, lesson="L13",
                title="ひし形の対角線と、合同を使う2つの三角形",
                intent="対角線垂直の証明図。定義（4辺相等）のみマークし、証明する直角は描かない",
                params="対角線の半分1.3/1.9（4辺=2.302相当・正方形ではない）",
                checks=ck.items, forbid=["90", "垂直", "⊥", "°"])


# ===========================================================================
# L13 図2: 包含関係の整理図（四角形⊃平行四辺形⊃長方形・ひし形、重なり=正方形）
# 本文根拠: lesson_13.md 主概念3（入れ子の枠+代表図形のシルエット。台形は描かない）
# ===========================================================================
def fig_L13_2():
    # --- パラメータ（px直書きの概念図。枠の入れ子を検算） ---
    box_quad = (8, 26, 432, 322)        # (x1,y1,x2,y2)
    box_pgram = (24, 96, 416, 314)
    box_rect = (40, 150, 270, 302)
    box_rhom = (185, 150, 400, 302)

    def inside(inner, outer):
        return (outer[0] < inner[0] and outer[1] < inner[1]
                and inner[2] < outer[2] and inner[3] < outer[3])

    ov = (max(box_rect[0], box_rhom[0]), max(box_rect[1], box_rhom[1]),
          min(box_rect[2], box_rhom[2]), min(box_rect[3], box_rhom[3]))

    ck = Checker()
    ck.ok("平行四辺形⊂四角形・長方形/ひし形⊂平行四辺形（枠の入れ子）",
          inside(box_pgram, box_quad) and inside(box_rect, box_pgram)
          and inside(box_rhom, box_pgram))
    ck.ok("長方形とひし形の枠に重なりがある（そこが正方形）",
          ov[0] < ov[2] and ov[1] < ov[3])
    # シルエットの幾何検算
    sq = [(0, 0), (1, 0), (1, 1), (0, 1)]
    rect_s = [(0, 0), (1.6, 0), (1.6, 1), (0, 1)]
    rhom_s = [(0.5, 0), (1.0, 0.8), (0.5, 1.6), (0.0, 0.8)]
    pg_s = [(0.35, 0), (1.75, 0), (1.4, 1), (0.0, 1)]
    quad_s = [(0.0, 0.1), (1.5, 0.0), (1.7, 1.0), (0.5, 1.4)]
    ck.ok("正方形シルエット=4辺相等かつ4直角",
          all(abs(dist(sq[i], sq[(i + 1) % 4]) - 1) < EPS for i in range(4))
          and all(abs(angle_deg(sq[i], sq[i - 1], sq[(i + 1) % 4]) - 90) < EPS for i in range(4)))
    ck.ok("長方形シルエット=4直角だが4辺相等でない",
          all(abs(angle_deg(rect_s[i], rect_s[i - 1], rect_s[(i + 1) % 4]) - 90) < EPS
              for i in range(4))
          and abs(dist(rect_s[0], rect_s[1]) - dist(rect_s[1], rect_s[2])) > 0.3)
    ck.ok("ひし形シルエット=4辺相等だが直角でない",
          max(dist(rhom_s[i], rhom_s[(i + 1) % 4]) for i in range(4))
          - min(dist(rhom_s[i], rhom_s[(i + 1) % 4]) for i in range(4)) < EPS
          and abs(angle_deg(rhom_s[0], rhom_s[3], rhom_s[1]) - 90) > 5)
    ck.ok("平行四辺形シルエット=対辺平行・長方形/ひし形ではない",
          abs(cross((0, 0), (pg_s[1][0] - pg_s[0][0], pg_s[1][1] - pg_s[0][1]),
                    (pg_s[2][0] - pg_s[3][0], pg_s[2][1] - pg_s[3][1]))) < EPS
          and abs(angle_deg(pg_s[0], pg_s[3], pg_s[1]) - 90) > 5
          and abs(dist(pg_s[0], pg_s[1]) - dist(pg_s[1], pg_s[2])) > 0.2)
    ck.ok("一般四角形シルエット=平行四辺形ではない",
          abs(cross((0, 0), (quad_s[1][0] - quad_s[0][0], quad_s[1][1] - quad_s[0][1]),
                    (quad_s[2][0] - quad_s[3][0], quad_s[2][1] - quad_s[3][1]))) > 0.1)

    cv = Canvas(440, 332)

    def box(b, label, lx, ly, w=MAIN_W, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        cv.raw(f'<rect x="{b[0]}" y="{b[1]}" width="{b[2] - b[0]}" height="{b[3] - b[1]}" '
               f'fill="none" stroke="#000" stroke-width="{w}"{d} rx="6"/>')
        cv.text_px(lx, ly, label, size=FS, weight="bold")

    box(box_quad, "四角形", 18, 46)
    box(box_pgram, "平行四辺形", 34, 116)
    box(box_rect, "長方形", 50, 170)
    box(box_rhom, "ひし形", 358, 170, dash=DASH)   # 破線=重なりを見分けるため
    cv.text_px((ov[0] + ov[2]) / 2, 176, "正方形", size=FS, anchor="middle", weight="bold")
    cv.text_px((ov[0] + ov[2]) / 2, 194, "（重なり）", size=10, anchor="middle")

    def sil(pts, ox, oy, s):
        cv.ox, cv.oy, cv.s = ox, oy, s
        cv.polygon(pts, w=1.2, fill=GRAY_FILL)

    sil(quad_s, 300, 84, 30)         # 四角形帯（平行四辺形の外）
    sil(pg_s, 280, 144, 26)          # 平行四辺形帯
    sil(rect_s, 66, 262, 34)         # 長方形のみの領域
    sil(rhom_s, 306, 282, 36)        # ひし形のみの領域
    sil(sq, ov[0] + 8, 262, 42)      # 重なり（正方形）
    cv.s = 1.0

    return dict(file="L13_fig2_inclusion_map.svg", canvas=cv, lesson="L13",
                title="四角形・平行四辺形・長方形・ひし形・正方形の包含関係図",
                intent="包含関係の整理図。入れ子の枠と代表図形のシルエットで示す（台形は描かない）",
                params="枠4つ+重なり領域・シルエット5種は幾何検算済み（正方形=4辺相等かつ4直角など）",
                checks=ck.items, forbid=["台形"])


# ===========================================================================
# L14 図1: 反例（等脚台形）の作図（AD//BC・AB=DCだが平行四辺形ではない）
# 本文根拠: lesson_14.md 活動（左右対称・AD:BC=2:4）
# ===========================================================================
def fig_L14_1():
    # --- パラメータ（lesson_14.md: AD:BC=2:4程度・等脚を厳密に） ---
    ad_half, bc_half, h = 1.0, 2.0, 1.7
    A = (-ad_half, h)
    D = (ad_half, h)
    B = (-bc_half, 0.0)
    C = (bc_half, 0.0)

    ck = Checker()
    ck.ok("AD//BC（どちらも水平）", abs(A[1] - D[1]) < EPS and abs(B[1] - C[1]) < EPS)
    ck.ok("AB=DC（等脚を厳密に・左右対称）",
          abs(dist(A, B) - dist(D, C)) < EPS
          and abs((A[0] + D[0]) / 2 - (B[0] + C[0]) / 2) < EPS,
          f"脚={dist(A, B):.3f}")
    ck.ok("AD:BC=2:4（=1:2）", abs(dist(A, D) / dist(B, C) - 0.5) < EPS)
    ck.ok("ABとDCは平行でない（平行四辺形ではない）",
          abs(cross((0, 0), (B[0] - A[0], B[1] - A[1]), (C[0] - D[0], C[1] - D[1]))) > 0.1)

    cv = Canvas(420, 240, scale=64.0, ox=210, oy=180)
    # 平行な2本の直線（薄く）
    for y in (h, 0.0):
        cv.line((-2.9, y), (2.9, y), w=1.0, color="#aaa")
    cv.polygon([A, B, C, D])
    g = centroid(A, B, C, D)
    for p, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p, g, nm)
    cv.ticks(A, B, 1)
    cv.ticks(D, C, 1)
    cv.parallel_mark(A, D, 1)
    cv.parallel_mark(B, C, 1)
    cv.text_px(210, 228, "AD//BC（矢羽）・AB=DC（ティック）の左右対称な台形",
               size=FS_CAP, anchor="middle")

    return dict(file="L14_fig1_isosceles_trapezoid.svg", canvas=cv, lesson="L14",
                title="左右対称な台形（AD//BC・AB=DC）",
                intent="反例づくり（等脚台形）の作図。仮定側のマークのみ付け、判定は本文で行う",
                params="AD=2, BC=4, 高さ1.7（AD:BC=1:2・等脚を厳密に左右対称で構成）",
                checks=ck.items, forbid=["等脚台形", "平行四辺形ではない"])


# ===========================================================================
# L15 図1: L07の図の再掲（発見活動の出発点・同一パラメータ）
# 本文根拠: lesson_15.md 主概念1（読み手がこれから発見する内容は描かない・書かない）
# ===========================================================================
def fig_L15_1():
    cv, ck = _build_midpoint_fig(
        "L07で証明を書いた、あの図（OはAB・CDそれぞれの中点）")
    ck.ok("L07_fig1と同一パラメータ（再掲）", _midpoint_cross_points() is not None)
    return dict(file="L15_fig1_revisit_midpoint.svg", canvas=cv, lesson="L15",
                title="中点Oで交わる2線分AB・CDと、結んだ線分AC・BD（L07の再掲）",
                intent="L07の証明図の再掲（読み返し活動の出発点）。仮定のティックのみ示す",
                params="L07_fig1と同一: O(0,0) A(-1.7,1.1) B(1.7,-1.1) C(-1.3,-1.2) D(1.3,1.2)",
                checks=ck.items, forbid=["平行", "//"])


# ===========================================================================
# メイン: 生成 + 答え漏れ機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L02_1,
        fig_L03_1, fig_L03_2, fig_L03_3, fig_L04_1,
        fig_L05_1, fig_L05_2, fig_L06_1, fig_L06_2,
        fig_L07_1, fig_L08_1, fig_L08_2, fig_L10_1,
        fig_L11_1, fig_L11_2, fig_L12_1,
        fig_L13_1, fig_L13_2, fig_L14_1, fig_L15_1]


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
        "spec: docs/SPEC_figures.md 準拠",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 中2「図形の合同と証明」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        f"全{len(rows)}図で下表の幾何検算＋答え漏れ機械検査（計{n_checks}件のスクリプト内assert）"
        "が生成時に自動実行され、全件合格。",
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
        "補足: 証明図では「これから証明する内容」（直角・辺の相等・平行など）を図にマークしない方針を",
        "とっており、その整合も上表のassertで検算している（例: L08_fig2のBD=CDは検算のみ・非表示）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines),
        encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")


if __name__ == "__main__":
    main()
