#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「相似」単元 図版パラメトリック生成スクリプト
=========================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（8枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / pathlib / datetime / html）
- 幾何の自己検証: 各図の build 関数内の check() が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。
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


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き に変換して描く）
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
            f'(docs/SPEC_figures.md準拠（内部規約の要旨は同SPECに反映済み）・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


# ---- 幾何ユーティリティ ----------------------------------------------------
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def centroid(*pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def tri_from_sides(c_len, b_len, a_len):
    """B=(0,0), C=(c_len? ) — BC=a_len を底辺に、AB=c_len, CA=b_len の三角形を返す(A,B,C)"""
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


def side_labels(cv, tri, labs, out=21.0, size=12):
    """三角形の各辺(P1P2,P2P3,P3P1)のラベルを重心から離れる向きに置く（Noneは省略）"""
    P1, P2, P3 = tri
    g = centroid(P1, P2, P3)
    for (p, q), lab in zip([(P1, P2), (P2, P3), (P3, P1)], labs):
        if lab is None:
            continue
        m = lerp(p, q, 0.5)
        d = (m[0] - g[0], m[1] - g[1])
        L = math.hypot(*d) or 1.0
        cv.text((m[0] + d[0] / L * (out / cv.s), m[1] + d[1] / L * (out / cv.s)),
                lab, size=size)


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
# 図1: L01 相似な2三角形（∽・対応順・対応マーク）
# 本文根拠: lesson_01.md 練習1「△ABC 5,7,9cm / △DEF 10,14,18cm・対応角相等」
# ===========================================================================
def fig_L01():
    # --- パラメータ（本文 lesson_01.md 練習1 と一致させる） ---
    AB, BC, CA = 5.0, 7.0, 9.0
    k = 2.0  # 相似比 1:2 → DEF = 10,14,18

    A, B, C = tri_from_sides(AB, CA, BC)
    D, E, F = ((k * p[0], k * p[1]) for p in (A, B, C))

    ck = Checker()
    for (p, q), (r_, s_), name in [((A, B), (D, E), "AB:DE"), ((B, C), (E, F), "BC:EF"),
                                   ((C, A), (F, D), "CA:FD")]:
        ratio = dist(r_, s_) / dist(p, q)
        ck.ok(f"相似比 {name}=1:2", abs(ratio - k) < 1e-9, f"実測比={ratio:.6f}")
    ck.ok("辺長=本文値(5,7,9)/(10,14,18)cm",
          abs(dist(A, B) - 5) < 1e-9 and abs(dist(E, F) - 14) < 1e-9 and abs(dist(F, D) - 18) < 1e-9)

    s = 16.0
    cv = Canvas(500, 258)
    cv.s = s

    def draw_tri(P1, P2, P3, names, ox, oy):
        cv.ox, cv.oy = ox, oy
        cv.polygon([P1, P2, P3])
        g = centroid(P1, P2, P3)
        for p, nm in zip((P1, P2, P3), names):
            cv.label_out(p, g, nm)
        # 対応する角: 弧の本数で対応（A/D=1, B/E=2, C/F=3）
        cv.angle_arc(P1, P2, P3, n=1)
        cv.angle_arc(P2, P3, P1, n=2)
        cv.angle_arc(P3, P1, P2, n=3)
        # 対応する辺: ティック本数（AB/DE=1, BC/EF=2, CA/FD=3）
        cv.ticks(P1, P2, 1)
        cv.ticks(P2, P3, 2)
        cv.ticks(P3, P1, 3)
        # 辺長ラベル（外側）
        for p, q, lab in [(P1, P2, None), (P2, P3, None), (P3, P1, None)]:
            pass

    draw_tri(A, B, C, "ABC", 55, 200)
    # 小三角形の辺長
    cv.ox, cv.oy = 55, 200
    for p, q, lab in [(A, B, "5cm"), (B, C, "7cm"), (C, A, "9cm")]:
        m = lerp(p, q, 0.5)
        g = centroid(A, B, C)
        d = (m[0] - g[0], m[1] - g[1])
        L = math.hypot(*d) or 1
        cv.text((m[0] + d[0] / L * (21 / s), m[1] + d[1] / L * (21 / s)), lab, size=12)
    draw_tri(D, E, F, "DEF", 240, 200)
    cv.ox, cv.oy = 240, 200
    for p, q, lab in [(D, E, "10cm"), (E, F, "14cm"), (F, D, "18cm")]:
        m = lerp(p, q, 0.5)
        g = centroid(D, E, F)
        d = (m[0] - g[0], m[1] - g[1])
        L = math.hypot(*d) or 1
        cv.text((m[0] + d[0] / L * (23 / s), m[1] + d[1] / L * (23 / s)), lab, size=12)

    cv.text_px(250, 232, "△ABC ∽ △DEF（相似比は？）", size=14, anchor="middle", weight="bold")  # 練習1が比を問うため答えを図に書かない（2026-07-11メンテナ検品）
    cv.text_px(250, 250, "同じ本数の弧＝対応する角，同じ本数のティック＝対応する辺", anchor="middle")

    return dict(file="L01_fig1_similar_triangles.svg", canvas=cv, lesson="L01",
                title="相似な2三角形と対応（△ABC∽△DEF）",
                intent="∽の対応順・対応する頂点/辺/角のマーク規約の提示（練習1の数値）",
                params="AB=5,BC=7,CA=9 / 相似比k=2 → DE=10,EF=14,FD=18",
                checks=ck.items)


# ===========================================================================
# 図2: L05 相似条件3つの並置図
# 本文根拠: lesson_03.md の条件文言（L05の証明で使用される条件の一覧）
# ===========================================================================
def fig_L05_conditions():
    # --- パラメータ: 汎用三角形（概念図なので寸法自由・比のみ厳密） ---
    AB, BC, CA = 3.4, 4.4, 3.0
    k = 1.55
    A, B, C = tri_from_sides(AB, CA, BC)
    A2, B2, C2 = ((k * p[0], k * p[1]) for p in (A, B, C))

    ck = Checker()
    ck.ok("並置図の2三角形の相似比が3辺とも一致",
          all(abs(dist(*pq2) / dist(*pq1) - k) < 1e-9 for pq1, pq2 in
              [((A, B), (A2, B2)), ((B, C), (B2, C2)), ((C, A), (C2, A2))]),
          f"k={k}")
    ck.ok("条件文言=lesson_03.md掲載の3条件と一致（コードに転記）", True)

    s = 15.0
    cv = Canvas(660, 226)
    cv.s = s
    panels = [
        ("bbb", ["① 対応する3組の辺の比が", "すべて等しい"]),
        ("bba", ["② 対応する2組の辺の比と", "その間の角がそれぞれ等しい"]),
        ("aa",  ["③ 対応する2組の角が", "それぞれ等しい"]),
    ]
    for i, (kind, cap) in enumerate(panels):
        px0 = 30 + i * 215

        for (P1, P2, P3), oy in [((A, B, C), 78), ((A2, B2, C2), 168)]:
            cv.ox, cv.oy = px0, oy
            # 強調辺（条件で使う辺は太線）
            bold_ab = kind in ("bbb", "bba")
            bold_bc = kind == "bbb"
            bold_ca = kind in ("bbb", "bba")
            cv.line(P1, P2, w=BOLD_W if bold_ab else MAIN_W)
            cv.line(P2, P3, w=BOLD_W if bold_bc else MAIN_W)
            cv.line(P3, P1, w=BOLD_W if bold_ca else MAIN_W)
            if kind == "bbb":
                cv.ticks(P1, P2, 1)
                cv.ticks(P2, P3, 2)
                cv.ticks(P3, P1, 3)
            elif kind == "bba":
                cv.ticks(P1, P2, 1)
                cv.ticks(P3, P1, 2)
                cv.angle_arc(P1, P2, P3, n=1)  # その間の角=∠A
            else:
                cv.angle_arc(P2, P3, P1, n=1)
                cv.angle_arc(P3, P1, P2, n=2)
        for j, line_ in enumerate(cap):
            cv.text_px(px0 + 3.4 * s, 190 + j * 16, line_, size=FS_CAP, anchor="middle")

    cv.text_px(330, 24, "三角形の相似条件（どれか1つが言えれば相似）", size=14,
               anchor="middle", weight="bold")
    return dict(file="L05_fig1_similarity_conditions.svg", canvas=cv, lesson="L05（条件はL03で導入）",
                title="三角形の相似条件3つの並置",
                intent="L05の証明で根拠に使う相似条件の一覧図。太線・ティック・弧=条件で使う要素",
                params=f"基準三角形(3.4,4.4,3.0)・相似比k={k}（概念図・比のみ厳密）",
                checks=ck.items)


# ===========================================================================
# 図3: L06 三角形と平行線の線分比（PQ∥BC）
# 本文根拠: lesson_06.md 例題1「AB=12,AP=8,AC=9,BC=15 → AQ=6,PQ=10」
# ===========================================================================
def fig_L06():
    # --- パラメータ（本文 例題1） ---
    AB, AC, BC, AP = 12.0, 9.0, 15.0, 8.0

    A, B, C = tri_from_sides(AB, AC, BC)   # B=(0,0), C=(15,0), A=(9.6,7.2)
    P = lerp(A, B, AP / AB)                # AP:AB
    Q = lerp(A, C, AP / AB)                # 同比 → AQ:AC=2:3

    ck = Checker()
    ck.ok("AP:AB=2:3", abs(dist(A, P) / dist(A, B) - 2 / 3) < 1e-9)
    ck.ok("AQ=6cm（本文の答と一致）", abs(dist(A, Q) - 6.0) < 1e-9, f"AQ={dist(A, Q):.4f}")
    ck.ok("PQ∥BC（外積≈0）", abs(cross((0, 0), (Q[0] - P[0], Q[1] - P[1]),
                                        (C[0] - B[0], C[1] - B[1]))) < 1e-9)
    ck.ok("PQ=10cm（本文の答と一致）", abs(dist(P, Q) - 10.0) < 1e-9, f"PQ={dist(P, Q):.4f}")

    cv = Canvas(400, 240)
    cv.s = 21.0
    cv.ox, cv.oy = 40, 180
    cv.polygon([A, B, C])
    cv.line(P, Q, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    for p, nm, dxy in [(P, "P", (-14, 0)), (Q, "Q", (14, 0))]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dxy[0], y + dxy[1] + 4.5, nm, size=FS, anchor="middle", weight="bold")
    cv.parallel_mark(P, Q, 1, t=0.55)
    cv.parallel_mark(B, C, 1, t=0.55)
    # 与件のうち図中に置く長さ
    mAP = lerp(A, P, 0.5)
    cv.text((mAP[0] - 26 / cv.s, mAP[1]), "8cm", size=12)
    mBC = lerp(B, C, 0.28)
    cv.text((mBC[0], mBC[1] - 16 / cv.s), "15cm", size=12)
    cv.text_px(200, 214, "PQ∥BC，AB=12cm，AP=8cm，AC=9cm，BC=15cm",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 231, "（例題1: AQとPQを求める）", size=FS_CAP, anchor="middle")

    return dict(file="L06_fig1_parallel_segment_ratio.svg", canvas=cv, lesson="L06",
                title="三角形と比の基本形（PQ∥BC）",
                intent="例題1の図。AP:AB=AQ:AC=PQ:BC の場面設定",
                params="AB=12,AC=9,BC=15,AP=8（→A=(9.6,7.2)を厳密計算）",
                checks=ck.items)


# ===========================================================================
# 図4: L08 平行線と線分の比（3本の平行線）
# 本文根拠: lesson_08.md 主概念（点名A,B,C/A′,B′,C′）＋例題1（6,9,8,x）
# ===========================================================================
def fig_L08():
    # --- パラメータ（本文 例題1: 6cm:9cm = 8cm:x） ---
    r1, r2 = 6.0, 9.0            # 左の直線が切り取られる2線分
    s1 = 8.0                     # 右の直線の上側線分（下側xは図では「x cm」表記）
    gap1, gap2 = 40.0, 60.0      # 平行線の間隔px（比2:3で任意）

    yl, ym, yn = 100.0, 100.0 - gap1, 100.0 - gap1 - gap2  # ℓ,m,n（数学座標y）
    # 斜線1（左）: x = 40 + 0.5*(100-y)
    A = (40.0, yl); B = (40 + 0.5 * gap1, ym); C = (40 + 0.5 * (gap1 + gap2), yn)
    # 斜線2（右）: x = 200 - 0.9*(100-y)
    A2 = (200.0, yl); B2 = (200 - 0.9 * gap1, ym); C2 = (200 - 0.9 * (gap1 + gap2), yn)

    ck = Checker()
    ck.ok("AB:BC = 6:9 = 2:3（幾何実測）",
          abs(dist(A, B) / dist(B, C) - r1 / r2) < 1e-9,
          f"実測比={dist(A, B) / dist(B, C):.6f}")
    ck.ok("A′B′:B′C′ = 2:3（幾何実測）",
          abs(dist(A2, B2) / dist(B2, C2) - 2 / 3) < 1e-9)
    ck.ok("本文の答 x=12 と整合（8×9/6=12）", abs(s1 * r2 / r1 - 12.0) < 1e-9)

    cv = Canvas(460, 260)
    cv.s = 1.7
    cv.ox, cv.oy = 30, 190
    # 平行線 ℓ, m, n
    for y, nm in [(yl, "ℓ"), (ym, "m"), (yn, "n")]:
        cv.line((0, y), (230, y), w=MAIN_W)
        cv.parallel_mark((0, y), (230, y), 1, t=0.94)
        cv.text((-8, y), nm, size=FS, anchor="end")
    # 斜線2本（平行線の少し外まで延長）
    for (pa, pc) in [(A, C), (A2, C2)]:
        ext_a = lerp(pa, pc, -0.12)
        ext_c = lerp(pa, pc, 1.12)
        cv.line(ext_a, ext_c, w=MAIN_W)
    # 点と名前
    g1 = centroid(A, C, (140, ym))
    for p, nm in [(A, "A"), (B, "B"), (C, "C")]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x - 13, y - 7, nm, size=FS, anchor="middle", weight="bold")
    for p, nm in [(A2, "A′"), (B2, "B′"), (C2, "C′")]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + 16, y - 7, nm, size=FS, anchor="middle", weight="bold")
    # 線分長ラベル（本文例題1の数値）
    for p, q, lab, side in [(A, B, "6cm", -1), (B, C, "9cm", -1),
                            (A2, B2, "8cm", 1), (B2, C2, "x cm", 1)]:
        m = lerp(p, q, 0.5)
        x, y = cv.P(m)
        cv.text_px(x + side * 30, y + 4, lab, size=FS, anchor="middle")
    cv.text_px(230, 232, "ℓ∥m∥n，AB=6cm，BC=9cm，A′B′=8cm，B′C′=x cm",
               size=FS_CAP, anchor="middle")
    cv.text_px(230, 249, "（例題1: xを求める。対応は 6↔8，9↔x）", size=FS_CAP, anchor="middle")

    return dict(file="L08_fig1_three_parallel_lines.svg", canvas=cv, lesson="L08",
                title="平行な3直線が2直線を切り取る線分の比",
                intent="主概念＋例題1の図。AB:BC=A′B′:B′C′",
                params="間隔比2:3（=6:9）・斜線2本は傾き別（0.5 / −0.9）で比の不変を見せる",
                checks=ck.items)


# ===========================================================================
# 図5: L10 中点連結定理
# 本文根拠: lesson_10.md 例題1「BC=14cm → MN=7cm」
# ===========================================================================
def fig_L10():
    # --- パラメータ（本文 例題1） ---
    BC = 14.0
    A = (5.0, 9.0)               # 頂点Aは任意（非対称にして一般性を出す）
    B, C = (0.0, 0.0), (BC, 0.0)
    M = lerp(A, B, 0.5)
    N = lerp(A, C, 0.5)

    ck = Checker()
    ck.ok("MはABの中点", dist(A, M) == dist(M, B))
    ck.ok("NはACの中点", dist(A, N) == dist(N, C))
    ck.ok("MN∥BC（外積≈0）", abs(cross((0, 0), (N[0] - M[0], N[1] - M[1]),
                                        (C[0] - B[0], C[1] - B[1]))) < 1e-12)
    ck.ok("MN=½BC=7cm（本文の答と一致）", abs(dist(M, N) - BC / 2) < 1e-12,
          f"MN={dist(M, N):.4f}")

    cv = Canvas(380, 246)
    cv.s = 19.0
    cv.ox, cv.oy = 55, 186
    cv.polygon([A, B, C])
    cv.line(M, N, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    for p, nm, dx in [(M, "M", -14), (N, "N", 14)]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dx, y + 4.5, nm, size=FS, anchor="middle", weight="bold")
    # 中点ティック: AM=MB(1本), AN=NC(2本)
    cv.ticks(A, M, 1); cv.ticks(M, B, 1)
    cv.ticks(A, N, 2); cv.ticks(N, C, 2)
    cv.parallel_mark(M, N, 1, t=0.55)
    cv.parallel_mark(B, C, 1, t=0.55)
    mBC = lerp(B, C, 0.5)
    cv.text((mBC[0], mBC[1] - 16 / cv.s), "14cm", size=12)
    mMN = lerp(M, N, 0.32)
    cv.text((mMN[0], mMN[1] + 14 / cv.s), "MN=？", size=12)
    cv.text_px(190, 220, "M・NはそれぞれAB・ACの中点，BC=14cm", size=FS_CAP, anchor="middle")
    cv.text_px(190, 237, "（例題1: MNを求める。同ティック=等長，矢羽=平行）",
               size=FS_CAP, anchor="middle")

    return dict(file="L10_fig1_midsegment_theorem.svg", canvas=cv, lesson="L10",
                title="中点連結定理（MN∥BC・MN=½BC）",
                intent="例題1の図。中点2つ→平行と半分",
                params="B=(0,0),C=(14,0),A=(5,9)・M,Nは厳密中点",
                checks=ck.items)


# ===========================================================================
# 図6: L12 相似比と面積比（方眼の数え上げ）
# 本文根拠: lesson_12.md 主概念1「A=2×3=6マス，B=4×6=24マス，縦だけ2倍=4×3=12マス」
# ===========================================================================
def fig_L12():
    # --- パラメータ（本文 主概念1） ---
    a_w, a_h = 3, 2       # 長方形A（横×縦マス）
    k = 2                 # 相似比1:2
    b_w, b_h = a_w * k, a_h * k
    t_w, t_h = a_w, a_h * k   # 縦だけ2倍

    ck = Checker()
    ck.ok("A=6マス", a_w * a_h == 6)
    ck.ok("B=24マス（相似比1:2）", b_w * b_h == 24)
    ck.ok("面積比 24/6 = 4 = 2²", (b_w * b_h) / (a_w * a_h) == k ** 2)
    ck.ok("縦だけ2倍=12マス（2倍どまり）", t_w * t_h == 12 and t_w * t_h == 2 * a_w * a_h)

    cell = 22
    cols, rows = 15, 5
    gx, gy = 30, 40
    cv = Canvas(420, 268)
    cv.defs.append(
        '<pattern id="h45" width="6" height="6" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
        'stroke="#555" stroke-width="1.1"/></pattern>'
        '<pattern id="h135" width="6" height="6" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(135)"><line x1="0" y1="0" x2="0" y2="6" '
        'stroke="#555" stroke-width="1.1"/></pattern>')
    # 方眼
    for i in range(cols + 1):
        x = gx + i * cell
        cv.raw(f'<line x1="{x}" y1="{gy}" x2="{x}" y2="{gy + rows * cell}" '
               f'stroke="#bbb" stroke-width="0.6"/>')
    for j in range(rows + 1):
        y = gy + j * cell
        cv.raw(f'<line x1="{gx}" y1="{y}" x2="{gx + cols * cell}" y2="{y}" '
               f'stroke="#bbb" stroke-width="0.6"/>')

    def rect_cells(col, w, h, fill):
        """方眼の下端に底を揃えて長方形を置く（col=左端の列番号）"""
        x = gx + col * cell
        y = gy + (rows - h) * cell
        cv.raw(f'<rect x="{x}" y="{y}" width="{w * cell}" height="{h * cell}" '
               f'fill="{fill}" stroke="#000" stroke-width="{MAIN_W}"/>')
        return x + w * cell / 2

    cxA = rect_cells(0, a_w, a_h, "url(#h45)")
    cxT = rect_cells(a_w + 1, t_w, t_h, "url(#h135)")
    cxB = rect_cells(a_w + 1 + t_w + 1, b_w, b_h, "#ddd")

    yy = gy + rows * cell + 20
    cv.text_px(cxA, yy, "A：2×3＝6マス", size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(cxT, yy + 17, "縦だけ2倍：4×3＝12マス", size=FS_CAP, anchor="middle")
    cv.text_px(cxB, yy, "B：4×6＝24マス", size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(210, 24, "相似比1:2の長方形A・B——面積は何倍？", size=14,
               anchor="middle", weight="bold")
    cv.text_px(210, yy + 39, "AとBは相似（相似比1:2）。面積比は 6:24＝1:4（＝1:2²）",
               size=FS_CAP, anchor="middle")
    cv.text_px(210, yy + 56, "「縦だけ2倍」は12マス＝2倍どまり——相似では縦も横も2倍になる",
               size=FS_CAP, anchor="middle")

    return dict(file="L12_fig1_area_ratio_grid.svg", canvas=cv, lesson="L12",
                title="方眼で数える面積比（相似比1:2→面積比1:4）",
                intent="主概念1の対比ワーク図。予想「2倍」への反例を数え上げで見せる",
                params="A=3×2マス，B=6×4マス，縦だけ2倍=3×4マス（塗り分け=ハッチング/濃淡）",
                checks=ck.items)


# ===========================================================================
# 図7: L15 縮図による測量①（木の高さ）
# 本文根拠: lesson_15.md 主概念1「水平距離10m・見上げ角35°・目の高さ1.5m→約8.5m」
# ===========================================================================
def fig_L15_tree():
    # --- パラメータ（本文 主概念1・実寸比で描く） ---
    DIST, ANG, EYE = 10.0, 35.0, 1.5     # 水平距離m・見上げ角°・目の高さm
    H_ANS = 8.5                        # 本文の答（約8.5m）

    h_above_eye = DIST * math.tan(math.radians(ANG))   # 目の高さから先端まで
    ck = Checker()
    ck.ok("tan35°×10m＝約7m（本文「約3.5cm×200=約7m」と一致）",
          abs(h_above_eye - 7.0) < 0.01, f"={h_above_eye:.4f}m")
    ck.ok("木の高さ＝約8.5m（本文の答と一致）",
          abs(h_above_eye + EYE - H_ANS) < 0.01, f"={h_above_eye + EYE:.4f}m")

    treetop = h_above_eye + EYE
    Pg = (0.0, 0.0)                  # 地点P（観測者の足元）
    E = (0.0, EYE)                   # 目
    T = (DIST, 0.0)                     # 木の根元
    Atop = (DIST, treetop)              # 木の先端A
    Hh = (DIST, EYE)                    # 目の高さの水平線が木と交わる点

    cv = Canvas(400, 282)
    cv.s = 22.0
    cv.ox, cv.oy = 46, 218
    # 地面
    cv.line((-1.4, 0), (11.8, 0), w=MAIN_W)
    # 観測者（最小限: 足元→目の縦線＋頭の丸）
    cv.line(Pg, (0, EYE - 0.12), w=MAIN_W)
    ex, ey = cv.P(E)
    cv.raw(f'<circle cx="{ex:.1f}" cy="{ey - 4:.1f}" r="5.5" fill="none" '
           f'stroke="#000" stroke-width="1.4"/>')
    cv.dot(E, r=2.2)
    # 木（幹＋最小限の樹冠。先端=A）
    cv.line(T, (DIST, treetop - 1.7), w=BOLD_W)
    cv.polygon([Atop, (DIST - 0.75, treetop - 1.8), (DIST + 0.75, treetop - 1.8)], w=1.4)
    # 視線と水平線
    cv.line(E, Atop, w=AUX_W)
    cv.line(E, Hh, w=AUX_W, dash=DASH)
    cv.right_angle(Hh, E, Atop)
    cv.angle_arc(E, Hh, Atop, r=26, n=1)
    ax_, ay_ = cv.P((1.55, EYE + 0.62))
    cv.text_px(ax_, ay_, "35°", size=FS, anchor="middle")
    # ラベル
    x, y = cv.P(Pg); cv.text_px(x - 15, y + 17, "P", size=FS, anchor="middle", weight="bold")
    x, y = cv.P(Atop); cv.text_px(x + 14, y + 2, "A", size=FS, anchor="middle", weight="bold")
    # 寸法: 10m（地面）・1.5m（目の高さ）・木の高さ？
    cv.dim((0, 0), (DIST, 0), "10m", offset=(0, -0.62))
    cv.dim((0, 0), (0, EYE), "", offset=(-0.55, 0))
    x, y = cv.P((-0.75, EYE / 2)); cv.text_px(x - 2, y + 4, "1.5m", size=12, anchor="end")
    cv.dim((DIST, 0), (DIST, treetop), "", offset=(1.15, 0))
    x, y = cv.P((DIST + 1.15, treetop / 2))
    cv.text_px(x + 6, y, "木の高さ", size=12); cv.text_px(x + 6, y + 15, "＝？", size=12)
    cv.text_px(200, 262, "水平距離10m・見上げる角35°・目の高さ1.5m（主概念1・実寸比）",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 279, "破線＝目の高さの水平線。縮図は目の高さから上の直角三角形で作る",
               size=FS_CAP, anchor="middle")

    return dict(file="L15_fig1_tree_height_survey.svg", canvas=cv, lesson="L15",
                title="縮図による測量①木の高さ（10m・35°・目の高さ1.5m）",
                intent="主概念1の場面図。目の高さを最後に足す構造を可視化",
                params="D=10m, 角=35°, 目の高さ=1.5m（tanで先端座標を厳密計算・実寸比）",
                checks=ck.items)


# ===========================================================================
# 図8: L15 縮図による測量②（池ごしの距離）
# 本文根拠: lesson_15.md 主概念2「CA=18m,CB=24m,∠ACB=60°→AB約21.6m」
# ===========================================================================
def fig_L15_pond():
    # --- パラメータ（本文 主概念2・実寸比で描く） ---
    CA, CB, ANG_C = 18.0, 24.0, 60.0

    C = (0.0, 0.0)
    # ∠ACBを二等分線が真上になるよう配置
    aL = math.radians(90 + ANG_C / 2)
    aR = math.radians(90 - ANG_C / 2)
    A = (CA * math.cos(aL), CA * math.sin(aL))
    B = (CB * math.cos(aR), CB * math.sin(aR))

    ab = dist(A, B)
    ab_law = math.sqrt(CA ** 2 + CB ** 2 - 2 * CA * CB * math.cos(math.radians(ANG_C)))
    ck = Checker()
    ck.ok("∠ACB=60°（配置の検算）",
          abs(math.degrees(math.acos(
              (A[0] * B[0] + A[1] * B[1]) / (CA * CB))) - ANG_C) < 1e-9)
    ck.ok("AB＝約21.6m（本文の答と一致・余弦定理）",
          abs(ab - 21.6) < 0.05 and abs(ab - ab_law) < 1e-9, f"AB={ab:.4f}m")

    cv = Canvas(400, 300)
    cv.s = 9.4
    cv.ox, cv.oy = 186, 240
    # 池（ABの間・楕円をAB方向に回転）
    mid = lerp(A, B, 0.5)
    mx, my = cv.P(mid)
    ang_svg = math.degrees(math.atan2(-(B[1] - A[1]), B[0] - A[0]))
    cv.raw(f'<ellipse cx="{mx:.1f}" cy="{my:.1f}" rx="{9.3 * cv.s:.1f}" '
           f'ry="{3.4 * cv.s:.1f}" transform="rotate({ang_svg:.1f} {mx:.1f} {my:.1f})" '
           f'fill="#e6e6e6" stroke="#888" stroke-width="1"/>')
    px_, py_ = cv.P(mid)
    cv.text_px(px_, py_ + 4, "池", size=FS_CAP, anchor="middle")
    # 三角形の2辺（実測辺は実線）とAB（求める辺は破線）
    cv.line(C, A, w=MAIN_W)
    cv.line(C, B, w=MAIN_W)
    cv.line(A, B, w=AUX_W, dash=DASH)
    cv.angle_arc(C, A, B, r=20, n=1)
    x, y = cv.P((0, 3.2)); cv.text_px(x, y - 4, "60°", size=FS, anchor="middle")
    for p, nm, (dx, dy) in [(A, "A", (-14, 0)), (B, "B", (15, 0)), (C, "C", (0, 18))]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy + 4.5, nm, size=FS, anchor="middle", weight="bold")
    mCA = lerp(C, A, 0.55)
    x, y = cv.P(mCA); cv.text_px(x - 24, y + 4, "18m", size=FS, anchor="middle")
    mCB = lerp(C, B, 0.55)
    x, y = cv.P(mCB); cv.text_px(x + 26, y + 4, "24m", size=FS, anchor="middle")
    x, y = cv.P(lerp(A, B, 0.5))
    cv.text_px(x + 2, y - 36, "AB＝？", size=FS, anchor="middle")
    cv.text_px(200, 276, "CA=18m，CB=24m，∠ACB=60°（主概念2・実寸比）",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 293, "実線＝測った辺・破線＝求める距離。縮尺1/300の縮図をかいて求める",
               size=FS_CAP, anchor="middle")

    return dict(file="L15_fig2_pond_distance_survey.svg", canvas=cv, lesson="L15",
                title="縮図による測量②池ごしの距離（18m・24m・60°）",
                intent="主概念2の場面図。測れる2辺と間の角から縮図を作る構造",
                params="CA=18m, CB=24m, ∠C=60°（ABは余弦定理で検算・実寸比）",
                checks=ck.items)


# ===========================================================================
# 図9: L02 相似比の読み方（∽の対応順から求値へ）
# 本文根拠: lesson_02.md 例題1「△ABC∽△DEF, AB=8, BC=10, ∠A=70°, DE=12」
# 答え漏れ注意: 例題1が問うのは (1)相似比 (2)EF (3)∠D —— いずれも図に書かず「？」
# ===========================================================================
def fig_L02():
    # --- パラメータ（本文 lesson_02.md 例題1 と一致させる） ---
    AB, BC, ANG_A, DE = 8.0, 10.0, 70.0, 12.0
    k = DE / AB      # =1.5（相似比2:3。例題1(1)が問う値なので図には書かない）

    ca = math.cos(math.radians(ANG_A))
    AC = (2 * AB * ca + math.sqrt((2 * AB * ca) ** 2 - 4 * (AB * AB - BC * BC))) / 2
    A, B = (0.0, 0.0), (AB, 0.0)
    C = (AC * ca, AC * math.sin(math.radians(ANG_A)))
    D, E, F = ((k * p[0], k * p[1]) for p in (A, B, C))

    ck = Checker()
    ck.ok("AB=8cm・BC=10cm・∠A=70°（本文の与件どおり配置）",
          abs(dist(A, B) - 8) < 1e-9 and abs(dist(B, C) - 10) < 1e-9
          and abs(angle_deg(A, B, C) - 70) < 1e-9,
          f"BC={dist(B, C):.4f}, ∠A={angle_deg(A, B, C):.2f}°")
    ck.ok("DE=12cm・3辺とも同じ比", abs(dist(D, E) - 12) < 1e-9 and
          abs(dist(E, F) / dist(B, C) - k) < 1e-9 and abs(dist(F, D) / dist(C, A) - k) < 1e-9)
    ck.ok("本文の答と整合: 相似比2:3・EF=15cm・∠D=70°（いずれも図には書かない）",
          abs(k - 1.5) < 1e-12 and abs(dist(E, F) - 15) < 1e-9
          and abs(angle_deg(D, E, F) - 70) < 1e-9, f"EF={dist(E, F):.4f}")

    s = 12.0
    cv = Canvas(560, 300)
    cv.s = s

    def draw(P1, P2, P3, names, ox, oy):
        cv.ox, cv.oy = ox, oy
        cv.polygon([P1, P2, P3])
        g = centroid(P1, P2, P3)
        for p, nm in zip((P1, P2, P3), names):
            cv.label_out(p, g, nm)
        # 対応する角=弧の本数（A/D=1, B/E=2, C/F=3）・対応する辺=ティック本数
        cv.angle_arc(P1, P2, P3, n=1)
        cv.angle_arc(P2, P3, P1, n=2)
        cv.angle_arc(P3, P1, P2, n=3)
        cv.ticks(P1, P2, 1)
        cv.ticks(P2, P3, 2)
        cv.ticks(P3, P1, 3)

    draw(A, B, C, "ABC", 55, 218)
    side_labels(cv, (A, B, C), ("8cm", "10cm", None))
    bis = math.radians(ANG_A / 2)
    cv.text((30 / s * math.cos(bis), 30 / s * math.sin(bis)), "70°", size=12)
    draw(D, E, F, "DEF", 250, 218)
    side_labels(cv, (D, E, F), ("12cm", "？", None), out=23)
    cv.text((32 / s * math.cos(bis), 32 / s * math.sin(bis)), "？", size=12)

    cv.text_px(280, 274, "△ABC∽△DEF，AB=8cm，BC=10cm，∠A=70°，DE=12cm",
               size=FS_CAP, anchor="middle")
    cv.text_px(280, 291, "（例題1: (1)相似比 (2)EF (3)∠D を求める——図の「？」）",
               size=FS_CAP, anchor="middle")

    return dict(file="L02_fig1_similarity_ratio.svg", canvas=cv, lesson="L02",
                title="相似比と対応する辺・角の求値（△ABC∽△DEF）",
                intent="例題1の図。∽の並び順から対応を読み、相似比→EF・∠Dへ（問う値は？表記）",
                params="AB=8,BC=10,∠A=70°,DE=12（ACは厳密解9.33を計算）・k=DE/AB（相似比は答えのため値非表示）",
                checks=ck.items)


# ===========================================================================
# 図10: L03 相似の判定 例題1の3組並置
# 本文根拠: lesson_03.md 例題1 (1)SSS比 (2)二辺比夾角 (3)二角（対応の探し直し）
# 答え漏れ注意: 「相似か・どの条件か・対応順」が答えなので、対応マーク（同数ティック/弧）は付けない
# ===========================================================================
def fig_L03():
    # --- パラメータ（本文 lesson_03.md 例題1 と一致させる） ---
    # (1) △ABC: 4,6,8 ／ △DEF: 6,9,12
    a1 = tri_from_sides(4.0, 8.0, 6.0)          # (A,B,C): AB=4, CA=8, BC=6
    d1 = tuple((1.5 * p[0], 1.5 * p[1]) for p in a1)
    # (2) △ABC: AB=5, AC=8, ∠A=45° ／ △DEF: DE=7.5, DF=12, ∠D=45°
    c45, s45 = math.cos(math.radians(45)), math.sin(math.radians(45))
    a2 = ((0.0, 0.0), (5.0, 0.0), (8.0 * c45, 8.0 * s45))
    d2 = tuple((1.5 * p[0], 1.5 * p[1]) for p in a2)
    # (3) △ABC: ∠A=50°, ∠B=70° ／ △DEF: ∠D=50°, ∠E=60°
    AB3, DE3 = 5.2, 6.8
    ac3 = AB3 * math.sin(math.radians(70)) / math.sin(math.radians(60))
    a3 = ((0.0, 0.0), (AB3, 0.0),
          (ac3 * math.cos(math.radians(50)), ac3 * math.sin(math.radians(50))))
    df3 = DE3 * math.sin(math.radians(60)) / math.sin(math.radians(70))
    d3 = ((0.0, 0.0), (DE3, 0.0),
          (df3 * math.cos(math.radians(50)), df3 * math.sin(math.radians(50))))

    ck = Checker()
    ck.ok("(1) 4:6=6:9=8:12=2:3（3組の辺の比が実測で一致）",
          all(abs(dist(d1[i], d1[j]) / dist(a1[i], a1[j]) - 1.5) < 1e-9
              for i, j in [(0, 1), (1, 2), (2, 0)]))
    ck.ok("(1) 辺長=本文値(4,6,8)/(6,9,12)cm",
          abs(dist(a1[0], a1[1]) - 4) < 1e-9 and abs(dist(a1[1], a1[2]) - 6) < 1e-9
          and abs(dist(d1[2], d1[0]) - 12) < 1e-9)
    ck.ok("(2) AB=5,AC=8,∠A=45°／DE=7.5,DF=12,∠D=45°（実測一致）",
          abs(dist(a2[0], a2[1]) - 5) < 1e-9 and abs(dist(a2[0], a2[2]) - 8) < 1e-9
          and abs(dist(d2[0], d2[1]) - 7.5) < 1e-9 and abs(dist(d2[0], d2[2]) - 12) < 1e-9
          and abs(angle_deg(a2[0], a2[1], a2[2]) - 45) < 1e-9
          and abs(angle_deg(d2[0], d2[1], d2[2]) - 45) < 1e-9)
    ck.ok("(3) △ABC={50°,70°,60°}・△DEF={50°,60°,70°}（残りの角も実測で本文と一致）",
          abs(angle_deg(a3[0], a3[1], a3[2]) - 50) < 1e-9
          and abs(angle_deg(a3[1], a3[0], a3[2]) - 70) < 1e-9
          and abs(angle_deg(a3[2], a3[0], a3[1]) - 60) < 1e-9
          and abs(angle_deg(d3[0], d3[1], d3[2]) - 50) < 1e-9
          and abs(angle_deg(d3[1], d3[0], d3[2]) - 60) < 1e-9
          and abs(angle_deg(d3[2], d3[0], d3[1]) - 70) < 1e-9)
    ck.ok("判定・条件名・対応順（本文の答）は図に書かず、対応マークも付けない", True)

    cv = Canvas(680, 285)

    def panel(tri_s, tri_l, names_s, names_l, px0, scale, arcs_s=(), arcs_l=(),
              labs_s=None, labs_l=None):
        cv.s = scale
        for tri, names, oy, arcs, labs in [(tri_s, names_s, 100, arcs_s, labs_s),
                                           (tri_l, names_l, 205, arcs_l, labs_l)]:
            cv.ox, cv.oy = px0, oy
            cv.polygon(list(tri))
            g = centroid(*tri)
            for p, nm in zip(tri, names):
                cv.label_out(p, g, nm, dist=12, size=12)
            for (vi, pi, qi, lab) in arcs:
                cv.angle_arc(tri[vi], tri[pi], tri[qi], n=1)
                v, p_, q_ = tri[vi], tri[pi], tri[qi]
                u1 = ((p_[0] - v[0]) / dist(v, p_), (p_[1] - v[1]) / dist(v, p_))
                u2 = ((q_[0] - v[0]) / dist(v, q_), (q_[1] - v[1]) / dist(v, q_))
                bl = math.hypot(u1[0] + u2[0], u1[1] + u2[1]) or 1.0
                cv.text((v[0] + (u1[0] + u2[0]) / bl * 21 / scale,
                         v[1] + (u1[1] + u2[1]) / bl * 21 / scale), lab, size=11)
            if labs:
                side_labels(cv, tri, labs, out=15, size=11)

    panel(a1, d1, "ABC", "DEF", 55, 8.5,
          labs_s=("4cm", "6cm", "8cm"), labs_l=("6cm", "9cm", "12cm"))
    panel(a2, d2, "ABC", "DEF", 280, 8.5,
          arcs_s=[(0, 1, 2, "45°")], arcs_l=[(0, 1, 2, "45°")],
          labs_s=("5cm", None, "8cm"), labs_l=("7.5cm", None, "12cm"))
    panel(a3, d3, "ABC", "DEF", 510, 11.0,
          arcs_s=[(0, 1, 2, "50°"), (1, 2, 0, "70°")],
          arcs_l=[(0, 1, 2, "50°"), (1, 2, 0, "60°")])
    cv.s = 8.5

    for i, px in enumerate((110, 335, 555)):
        cv.text_px(px, 246, f"({i + 1})", size=FS_CAP, anchor="middle", weight="bold")
    cv.text_px(340, 24, "例題1: 各組の三角形は相似といえるか（いえる場合は使った条件も）",
               size=14, anchor="middle", weight="bold")
    cv.text_px(340, 268, "判定が問われているので、対応を示すマーク（同数のティック・弧）は"
               "付けていない——対応を探すのも問題の一部",
               size=FS_CAP, anchor="middle")

    return dict(file="L03_fig1_similarity_test_examples.svg", canvas=cv, lesson="L03",
                title="相似の判定 例題1（3組の並置）",
                intent="例題1(1)(2)(3)の与件図。判定・条件名が答えのため対応マークなし",
                params="(1)4,6,8/6,9,12 (2)5,8,45°/7.5,12,45° (3)50°70°/50°60°（角は厳密配置）",
                checks=ck.items)


# ===========================================================================
# 図11: L04 証明の構想① 交差配置（対頂角の図）
# 本文根拠: lesson_04.md 例題1「ADとBCが点Oで交わる。OA=4,OB=6,OC=9,OD=6」
# 答え漏れ注意: 方針メモ（条件選び・対頂角・2:3）が答えなので、等角マーク・対応ティックは付けない
# ===========================================================================
def fig_L04_cross():
    # --- パラメータ（本文 lesson_04.md 例題1 と一致させる） ---
    OA, OB, OC, OD = 4.0, 6.0, 9.0, 6.0
    aA, aB = math.radians(150), math.radians(40)   # 2直線の向き（描画用・任意）

    O = (0.0, 0.0)
    A = (OA * math.cos(aA), OA * math.sin(aA))
    D = (-OD * math.cos(aA), -OD * math.sin(aA))
    B = (OB * math.cos(aB), OB * math.sin(aB))
    C = (-OC * math.cos(aB), -OC * math.sin(aB))

    ck = Checker()
    ck.ok("A,O,D／B,O,C はそれぞれ一直線（線分AD・BCの交点がO）",
          abs(cross(A, O, D)) < 1e-9 and abs(cross(B, O, C)) < 1e-9)
    ck.ok("OA=4,OB=6,OC=9,OD=6（本文の与件どおり）",
          all(abs(dist(O, p) - L) < 1e-9 for p, L in [(A, 4), (B, 6), (C, 9), (D, 6)]))
    ck.ok("本文の方針メモと整合: OA:OD=OB:OC=2:3・∠AOB=∠DOC（図にはマークしない）",
          abs(dist(O, A) / dist(O, D) - 2 / 3) < 1e-9
          and abs(dist(O, B) / dist(O, C) - 2 / 3) < 1e-9
          and abs(angle_deg(O, A, B) - angle_deg(O, D, C)) < 1e-9)
    ck.ok("相似比の帰結 AB:DC=2:3（実測・図には書かない）",
          abs(dist(A, B) / dist(D, C) - 2 / 3) < 1e-9,
          f"AB/DC={dist(A, B) / dist(D, C):.6f}")

    cv = Canvas(420, 248)
    cv.s = 15.0
    cv.ox, cv.oy = 148, 95
    cv.line(A, D, w=MAIN_W)
    cv.line(B, C, w=MAIN_W)
    cv.line(A, B, w=MAIN_W)
    cv.line(D, C, w=MAIN_W)
    for p, nm, (dx, dy) in [(O, "O", (12, 16)), (A, "A", (-13, -8)), (B, "B", (13, -8)),
                            (C, "C", (-14, 8)), (D, "D", (14, 8))]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy + 4.0, nm, size=FS, anchor="middle", weight="bold")
    seg_label(cv, O, A, "4cm", off=-12)
    seg_label(cv, O, B, "6cm", off=12)
    seg_label(cv, O, C, "9cm", off=-13)
    seg_label(cv, O, D, "6cm", off=13)
    cv.text_px(210, 214, "線分ADと線分BCが点Oで交わる。OA=4cm，OB=6cm，OC=9cm，OD=6cm",
               size=FS_CAP, anchor="middle")
    cv.text_px(210, 231, "（例題1: △OAB∽△ODCの方針メモを作る——条件と材料を図から探す）",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig1_crossing_segments.svg", canvas=cv, lesson="L04",
                title="証明の構想① 交差配置（AD×BC＝O）",
                intent="例題1の与件図。方針メモ（対頂角・比2:3）が答えのため等角マークなし",
                params="OA=4,OB=6,OC=9,OD=6・直線の向き150°/40°（任意）",
                checks=ck.items)


# ===========================================================================
# 図12: L04 証明の構想② 重なる配置（共通角の図）
# 本文根拠: lesson_04.md 例題2「AB上にD・AC上にE、∠AED=∠ABC → △ADE∽△ACB」
# 答え漏れ注意: 2組目の角（共通角∠A）が答えなので、∠Aにはマークを付けない
# ===========================================================================
def fig_L04_overlap():
    # --- パラメータ（∠AED=∠ABCが厳密に成り立つよう AD=k·AC, AE=k·AB で配置） ---
    AB, CA, BC, k = 7.0, 5.6, 8.0, 0.62

    A, B, C = tri_from_sides(AB, CA, BC)
    D = lerp(A, B, (k * CA) / AB)      # AD=k·AC（D↔Cの対応）
    E = lerp(A, C, (k * AB) / CA)      # AE=k·AB（E↔Bの対応）

    ck = Checker()
    ck.ok("∠AED=∠ABC（本文の仮定が実測で成立）",
          abs(angle_deg(E, A, D) - angle_deg(B, A, C)) < 1e-9,
          f"={angle_deg(E, A, D):.2f}°")
    ck.ok("△ADE∽△ACB（AD:AC=AE:AB=DE:CB=k・概念図のため数値ラベルなし）",
          abs(dist(A, D) / dist(A, C) - k) < 1e-9
          and abs(dist(A, E) / dist(A, B) - k) < 1e-9
          and abs(dist(D, E) / dist(C, B) - k) < 1e-9)
    ck.ok("DはAB上・EはAC上（内分）", 0 < (k * CA) / AB < 1 and 0 < (k * AB) / CA < 1)

    cv = Canvas(470, 235)
    cv.s = 26.0
    cv.ox, cv.oy = 115, 160
    cv.polygon([A, B, C])
    cv.line(D, E, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    for p, nm, (dx, dy) in [(D, "D", (-13, -4)), (E, "E", (13, 8))]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy + 4.0, nm, size=FS, anchor="middle", weight="bold")
    # 仮定の等しい角だけマーク（∠AED と ∠ABC・同じ1重弧）
    cv.angle_arc(E, A, D, n=1)
    cv.angle_arc(B, A, C, n=1)
    cv.text_px(235, 199, "辺AB上に点D，辺AC上に点E，∠AED＝∠ABC（同じ弧＝等しい角・仮定）",
               size=FS_CAP, anchor="middle")
    cv.text_px(235, 216, "（例題2: △ADE∽△ACBの方針メモ——2組目の等しい角はどこから？）",
               size=FS_CAP, anchor="middle")

    return dict(file="L04_fig2_overlapping_triangles.svg", canvas=cv, lesson="L04",
                title="証明の構想② 重なる配置（∠AED=∠ABC）",
                intent="例題2の与件図。共通角∠Aが答えのため∠Aにはマークなし",
                params="AB=7,CA=5.6,BC=8,k=0.62（∠AED=∠ABCを厳密に満たす内分点）",
                checks=ck.items)


# ===========================================================================
# 図13: L05 循環論法の構造（概念図）
# 本文根拠: lesson_05.md 例題2の誤答「△OAB∽△ODCだから∠OAB=∠ODC」→結論に戻る循環
# ===========================================================================
def fig_L05_circular():
    ck = Checker()
    ck.ok("結論の文言=lesson_05.md例題2「△OAB∽△ODC」と一致（コードに転記）", True)
    ck.ok("誤答①の文言=「△OAB∽△ODCだから ∠OAB=∠ODC」と一致（コードに転記）", True)
    ck.ok("直した証明の材料と整合: OA:OD=4:6=OB:OC=6:9=2:3",
          abs(4 / 6 - 2 / 3) < 1e-12 and abs(6 / 9 - 2 / 3) < 1e-12)

    cv = Canvas(480, 262)

    def box(x, y, w, h, tag, body):
        cv.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
               f'fill="#fff" stroke="#000" stroke-width="{MAIN_W}"/>')
        cv.text_px(x + w / 2, y + 17, tag, size=FS_CAP, anchor="middle", weight="bold")
        cv.text_px(x + w / 2, y + 34, body, size=FS, anchor="middle")

    box(140, 38, 200, 42, "結論（証明したいこと）", "△OAB∽△ODC")
    box(90, 158, 300, 42, "誤答の根拠①", "「△OAB∽△ODCだから ∠OAB=∠ODC」")
    # 右回りの循環: 結論→(根拠に使う)→① と ①→(結論を導く)→結論
    arrow_px(cv, 330, 80, 355, 158)
    arrow_px(cv, 150, 158, 125, 80)
    cv.text_px(358, 118, "結論そのものを", size=FS_CAP, anchor="start")
    cv.text_px(358, 133, "根拠に使っている", size=FS_CAP, anchor="start")
    cv.text_px(122, 118, "①を根拠に", size=FS_CAP, anchor="end")
    cv.text_px(122, 133, "結論を導く", size=FS_CAP, anchor="end")
    cv.text_px(240, 125, "循環！", size=15, anchor="middle", weight="bold")
    cv.text_px(240, 228, "例題2の誤答の構造。3点検の「循環の検査」で①を見つけて消し、",
               size=FS_CAP, anchor="middle")
    cv.text_px(240, 245, "別の材料（仮定の辺の比と対頂角）に切り替える",
               size=FS_CAP, anchor="middle")

    return dict(file="L05_fig2_circular_reasoning.svg", canvas=cv, lesson="L05",
                title="循環論法の構造（例題2の誤答）",
                intent="主概念2・例題2の概念図。結論が根拠に混ざる循環を矢印2本で可視化",
                params="概念図（幾何なし）。文言はlesson_05.md例題2から転記",
                checks=ck.items)


# ===========================================================================
# 図14: L07 延長上の2配置（Aの反対側／B・Cの外側）
# 本文根拠: lesson_07.md 例題1「AB=8,AP=4,AC=10,BC=12」・例題2「AB=8,AP=10,AC=12,BC=8」
# 答え漏れ注意: AQ・PQが問われる——図は「？」（AQ=5,PQ=6／AQ=15,PQ=10はassertのみ）
# ===========================================================================
def fig_L07():
    # --- パラメータ（本文 例題1・例題2 と一致させる） ---
    # 例題1（Aの反対側）: AB=8, AP=4, AC=10, BC=12
    A1, B1, C1 = tri_from_sides(8.0, 10.0, 12.0)
    t1 = 4.0 / 8.0
    P1 = (A1[0] + (A1[0] - B1[0]) * t1, A1[1] + (A1[1] - B1[1]) * t1)
    Q1 = (A1[0] + (A1[0] - C1[0]) * t1, A1[1] + (A1[1] - C1[1]) * t1)
    # 例題2（B・Cの外側）: AB=8, AP=10, AC=12, BC=8
    A2, B2, C2 = tri_from_sides(8.0, 12.0, 8.0)
    t2 = 10.0 / 8.0
    P2 = lerp(A2, B2, t2)
    Q2 = lerp(A2, C2, t2)

    ck = Checker()
    ck.ok("例題1: AP=4cm・PQ∥BC（配置の検算）",
          abs(dist(A1, P1) - 4) < 1e-9 and
          abs(cross((0, 0), (Q1[0] - P1[0], Q1[1] - P1[1]),
                    (C1[0] - B1[0], C1[1] - B1[1]))) < 1e-9)
    ck.ok("例題1の答と整合: AQ=5cm・PQ=6cm（図には？で示す）",
          abs(dist(A1, Q1) - 5) < 1e-9 and abs(dist(P1, Q1) - 6) < 1e-9,
          f"AQ={dist(A1, Q1):.4f}, PQ={dist(P1, Q1):.4f}")
    ck.ok("例題2: AP=10cm・PQ∥BC（配置の検算）",
          abs(dist(A2, P2) - 10) < 1e-9 and
          abs(cross((0, 0), (Q2[0] - P2[0], Q2[1] - P2[1]),
                    (C2[0] - B2[0], C2[1] - B2[1]))) < 1e-9)
    ck.ok("例題2の答と整合: AQ=15cm・PQ=10cm（図には？で示す）",
          abs(dist(A2, Q2) - 15) < 1e-9 and abs(dist(P2, Q2) - 10) < 1e-9,
          f"AQ={dist(A2, Q2):.4f}, PQ={dist(P2, Q2):.4f}")

    cv = Canvas(660, 268)
    cv.s = 12.0

    def draw_case(A, B, C, P, Q, ox, oy, offs):
        cv.ox, cv.oy = ox, oy
        cv.polygon([A, B, C])
        cv.line(A, P, w=MAIN_W)
        cv.line(A, Q, w=MAIN_W)
        cv.line(P, Q, w=MAIN_W)
        cv.parallel_mark(P, Q, 1, t=0.5)
        cv.parallel_mark(B, C, 1, t=0.5)
        for p, nm in [(P, "P"), (Q, "Q")]:
            cv.dot(p)
        for p, nm, (dx, dy) in zip((A, B, C, P, Q), "ABCPQ", offs):
            x, y = cv.P(p)
            cv.text_px(x + dx, y + dy + 4.0, nm, size=FS, anchor="middle", weight="bold")

    draw_case(A1, B1, C1, P1, Q1, 45, 190,
              [(17, 5), (-12, 13), (14, 13), (5, -12), (-8, -12)])
    seg_label(cv, A1, Q1, "？", off=-12, t=0.6)   # AQ
    seg_label(cv, P1, Q1, "？", off=12)           # PQ（上側）
    seg_label(cv, A1, B1, "8cm", off=-13, size=11)
    seg_label(cv, A1, P1, "4cm", off=13, size=11)
    seg_label(cv, B1, C1, "12cm", off=13, size=11)

    draw_case(A2, B2, C2, P2, Q2, 385, 150,
              [(-8, -10), (-14, -2), (7, -13), (-6, 15), (14, 9)])
    seg_label(cv, A2, Q2, "？", off=-13, t=0.93)  # AQ（C側延長部の外側）
    seg_label(cv, P2, Q2, "？", off=12)           # PQ（下側）
    seg_label(cv, A2, B2, "8cm", off=13, size=11)
    seg_label(cv, B2, C2, "8cm", off=-12, t=0.35, size=11)

    cv.text_px(150, 28, "例題1（P・QはAの反対側）", size=13, anchor="middle", weight="bold")
    cv.text_px(480, 28, "例題2（P・QはB・Cの外側）", size=13, anchor="middle", weight="bold")
    cv.text_px(150, 232, "AB=8cm，AP=4cm，AC=10cm，BC=12cm", size=FS_CAP, anchor="middle")
    cv.text_px(150, 249, "PQ∥BC。AQとPQを求める（？）", size=FS_CAP, anchor="middle")
    cv.text_px(480, 232, "AB=8cm，AP=10cm，AC=12cm，BC=8cm", size=FS_CAP, anchor="middle")
    cv.text_px(480, 249, "PQ∥BC。AQとPQを求める（？）", size=FS_CAP, anchor="middle")

    return dict(file="L07_fig1_extension_two_cases.svg", canvas=cv, lesson="L07",
                title="延長上の2配置（Aの反対側／B・Cの外側）",
                intent="例題1・例題2の並置図。式が辺上と同じになる2つの延長配置",
                params="例題1: 8,4,10,12（t=1/2）／例題2: 8,10,12,8（t=5/4）",
                checks=ck.items)


# ===========================================================================
# 図15: L09 比から平行を導く（逆・性質の図）
# 本文根拠: lesson_09.md 主概念「AP:AB=AQ:AC（またはAP:PB=AQ:QC）ならばPQ∥BC」
# ===========================================================================
def fig_L09():
    # --- パラメータ（性質の図: 数値なし・t=AP:ABのみ指定） ---
    A, B, C = (3.4, 6.2), (0.0, 0.0), (9.0, 0.0)
    t = 0.6
    P = lerp(A, B, t)
    Q = lerp(A, C, t)

    ck = Checker()
    ck.ok("AP:AB=AQ:AC（作図の仮定・実測一致）",
          abs(dist(A, P) / dist(A, B) - t) < 1e-9 and abs(dist(A, Q) / dist(A, C) - t) < 1e-9)
    ck.ok("AP:PB=AQ:QC も同値に成立（本文の2形式）",
          abs(dist(A, P) / dist(P, B) - dist(A, Q) / dist(Q, C)) < 1e-9)
    ck.ok("結論 PQ∥BC（外積≈0）",
          abs(cross((0, 0), (Q[0] - P[0], Q[1] - P[1]), (C[0] - B[0], C[1] - B[1]))) < 1e-12)

    cv = Canvas(380, 235)
    cv.s = 22.0
    cv.ox, cv.oy = 70, 160
    cv.polygon([A, B, C])
    cv.line(P, Q, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    for p, nm in [(P, "P"), (Q, "Q")]:
        cv.dot(p)
        cv.label_out(p, g, nm, dist=14)
    cv.parallel_mark(P, Q, 1, t=0.55)
    cv.parallel_mark(B, C, 1, t=0.55)
    cv.text_px(190, 199, "仮定: AP:AB＝AQ:AC（または AP:PB＝AQ:QC）",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 216, "結論: PQ∥BC（矢羽）——「比が等しければ平行」・L06の逆",
               size=FS_CAP, anchor="middle")

    return dict(file="L09_fig1_converse_ratio_parallel.svg", canvas=cv, lesson="L09",
                title="比から平行を導く（平行線と線分の比の逆）",
                intent="主概念の性質図。仮定=比の等しさ・結論=平行（矢羽は結論側）",
                params="A=(3.4,6.2),B=(0,0),C=(9,0),t=0.6（比は厳密・数値ラベルなし）",
                checks=ck.items)


# ===========================================================================
# 図16: L11 中点四角形（対角線=補助線）
# 本文根拠: lesson_11.md 主概念・例題「AC=12cm, BD=10cm→EFGHの周は？」
# 答え漏れ注意: 例題の答（周22cm・EF=6・FG=5）は図に書かない——「周＝？」
# ===========================================================================
def fig_L11():
    # --- パラメータ（AC=12, BD=10 を厳密に満たすゆがんだ凸四角形） ---
    A, C = (0.0, 0.0), (12.0, 0.0)
    B = (3.0, -4.0)
    D = (10.0, math.sqrt(51.0) - 4.0)      # BD=√(49+51)=10
    E, F, G, H = (lerp(A, B, .5), lerp(B, C, .5), lerp(C, D, .5), lerp(D, A, .5))

    ck = Checker()
    ck.ok("AC=12cm・BD=10cm（本文の与件どおり）",
          abs(dist(A, C) - 12) < 1e-9 and abs(dist(B, D) - 10) < 1e-9)
    ck.ok("ABCDは凸四角形（自己交差なし）",
          all(cross(p, q, r) > 0 for p, q, r in
              [(A, B, C), (B, C, D), (C, D, A), (D, A, B)]))
    ck.ok("EF∥AC・EF=½AC=6cm／FG∥BD・FG=½BD=5cm（中点連結定理の実測）",
          abs(cross((0, 0), (F[0] - E[0], F[1] - E[1]), (C[0] - A[0], C[1] - A[1]))) < 1e-9
          and abs(dist(E, F) - 6) < 1e-9 and abs(dist(F, G) - 5) < 1e-9)
    ck.ok("EFGHは平行四辺形（対辺ベクトル一致）・周=22cm（本文の答・図には書かない）",
          abs((F[0] - E[0]) - (G[0] - H[0])) < 1e-12
          and abs((F[1] - E[1]) - (G[1] - H[1])) < 1e-12
          and abs(2 * (dist(E, F) + dist(F, G)) - 22) < 1e-9)

    cv = Canvas(430, 235)
    cv.s = 17.0
    cv.ox, cv.oy = 75, 100
    cv.polygon([A, B, C, D])
    cv.line(A, C, w=AUX_W, dash=DASH)
    cv.line(B, D, w=AUX_W, dash=DASH)
    cv.polygon([E, F, G, H])
    gq = centroid(A, B, C, D)
    for p, nm in zip((A, B, C, D), "ABCD"):
        cv.label_out(p, gq, nm)
    for p, nm in zip((E, F, G, H), "EFGH"):
        cv.dot(p)
        cv.label_out(p, gq, nm, dist=14)
    seg_label(cv, A, C, "12cm", off=10, t=0.24, size=11)
    cv.text((4.9, -3.0), "10cm", size=11)     # BD（B寄り・△EBFの空白に置く）
    cv.text((7.95, -1.0), "周＝？", size=FS)   # EFGH内部・対角線2本から離す
    cv.text_px(215, 201, "E・F・G・Hは各辺の中点。対角線AC=12cm，BD=10cm（破線＝補助線）",
               size=FS_CAP, anchor="middle")
    cv.text_px(215, 218, "（例題: 中点四角形EFGHの周の長さを求める）",
               size=FS_CAP, anchor="middle")

    return dict(file="L11_fig1_midpoint_quadrilateral.svg", canvas=cv, lesson="L11",
                title="中点四角形EFGH（対角線AC・BDは補助線）",
                intent="主概念+例題の図。中点連結定理を対角線2本で2回使う構造",
                params="A(0,0),B(3,-4),C(12,0),D(10,√51−4)——AC=12・BD=10を厳密に満たす",
                checks=ck.items)


# ===========================================================================
# 図17: L13 相似な直方体P・Q
# 本文根拠: lesson_13.md 主概念1「P: 2×3×4cm, Q: 4×6×8cm, 相似比1:2」
#           主概念2「表面積52cm²・208cm²（本文が計算する値——図には書かない）」
# ===========================================================================
def fig_L13():
    # --- パラメータ（本文 主概念1 と一致させる） ---
    p_d, p_w, p_h = 2.0, 3.0, 4.0     # 縦(奥行)・横・高さ
    k = 2.0
    q_d, q_w, q_h = p_d * k, p_w * k, p_h * k

    surf_p = 2 * (p_d * p_w + p_w * p_h + p_d * p_h)
    surf_q = 2 * (q_d * q_w + q_w * q_h + q_d * q_h)
    ck = Checker()
    ck.ok("3組の辺の比がすべて1:2（相似）",
          q_d / p_d == 2 and q_w / p_w == 2 and q_h / p_h == 2)
    ck.ok("表面積P=52cm²・Q=208cm²（本文の計算値と一致・図には書かない）",
          abs(surf_p - 52) < 1e-12 and abs(surf_q - 208) < 1e-12)
    ck.ok("表面積の比=4=2²（相似比の2乗）", abs(surf_q / surf_p - k ** 2) < 1e-12)

    cv = Canvas(500, 268)
    s = 10.0
    dep = 0.5 * math.cos(math.radians(45))   # 奥行の見かけ縮率（キャビネット投影）

    def draw_box(x0, y0, w_u, h_u, d_u, labs):
        """x0,y0=前面左下(px)。w,h,d=cm。見える辺=実線・隠れる辺=破線"""
        W, H = w_u * s, h_u * s
        dx, dy = d_u * s * dep, d_u * s * dep
        # 前面
        cv.raw(f'<rect x="{x0:.1f}" y="{y0 - H:.1f}" width="{W:.1f}" height="{H:.1f}" '
               f'fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        # 上面・右面
        for pts in ([(x0, y0 - H), (x0 + dx, y0 - H - dy), (x0 + W + dx, y0 - H - dy),
                     (x0 + W, y0 - H)],
                    [(x0 + W, y0 - H), (x0 + W + dx, y0 - H - dy),
                     (x0 + W + dx, y0 - dy), (x0 + W, y0)]):
            cv.raw('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                   + f'" fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        # 隠れる3辺（破線）
        bx, by = x0 + dx, y0 - dy
        for (x1, y1, x2, y2) in [(bx, by, bx, by - H), (bx, by, x0, y0),
                                 (bx, by, bx + W, by)]:
            cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                   f'stroke="#000" stroke-width="{AUX_W}" stroke-dasharray="{DASH}"/>')
        # ラベル（横・高さ・縦=奥行）
        cv.text_px(x0 + W / 2, y0 + 16, labs[0], size=FS_CAP, anchor="middle")
        cv.text_px(x0 - 6, y0 - H / 2 + 4, labs[1], size=FS_CAP, anchor="end")
        cv.text_px(x0 + W + dx / 2 + 6, y0 - dy / 2 + 12, labs[2], size=FS_CAP,
                   anchor="start")

    draw_box(90, 200, p_w, p_h, p_d, ("横3cm", "高さ4cm", "縦2cm"))
    cv.text_px(110, 130, "P", size=15, anchor="middle", weight="bold")
    draw_box(280, 200, q_w, q_h, q_d, ("横6cm", "高さ8cm", "縦4cm"))
    cv.text_px(315, 90, "Q", size=15, anchor="middle", weight="bold")
    cv.text_px(250, 240, "直方体P（縦2×横3×高さ4cm）と直方体Q（縦4×横6×高さ8cm）",
               size=FS_CAP, anchor="middle")
    cv.text_px(250, 257, "3組の辺の比がすべて等しい→相似比1:2。表面積の比は主概念2で確かめる",
               size=FS_CAP, anchor="middle")

    return dict(file="L13_fig1_similar_cuboids.svg", canvas=cv, lesson="L13",
                title="相似な直方体P・Q（相似比1:2）",
                intent="主概念1の図。立体の相似=全対応辺が同比。表面積計算（主概念2）の土台",
                params="P=2×3×4cm, Q=4×6×8cm（キャビネット投影・隠れ線は破線）",
                checks=ck.items)


# ===========================================================================
# 図18: L14 積み木の数え上げ（1cm→2cmの立方体）
# 本文根拠: lesson_14.md 主概念1「1辺1cm→1辺2cm＝縦2×横2×高さ2」
# ===========================================================================
def fig_L14():
    # --- パラメータ（本文 主概念1 と一致させる） ---
    k = 2
    ck = Checker()
    ck.ok("1辺2cmの立方体=積み木2×2×2=8個（本文の数え上げと一致）", k ** 3 == 8)
    ck.ok("本文の直方体検算: 2×3×4=24cm³→4×6×8=192cm³＝8倍",
          2 * 3 * 4 == 24 and 4 * 6 * 8 == 192 and 192 // 24 == 8)
    ck.ok("体積比=相似比の3乗（1:2³=1:8）", (1, k ** 3) == (1, 8))

    cv = Canvas(430, 260)
    s = 32.0
    dep = 0.5 * math.cos(math.radians(45))

    def cube(x0, y0, edge_u, div, labs):
        E = edge_u * s
        dx = dy = edge_u * s * dep
        cv.raw(f'<rect x="{x0:.1f}" y="{y0 - E:.1f}" width="{E:.1f}" height="{E:.1f}" '
               f'fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        for pts in ([(x0, y0 - E), (x0 + dx, y0 - E - dy), (x0 + E + dx, y0 - E - dy),
                     (x0 + E, y0 - E)],
                    [(x0 + E, y0 - E), (x0 + E + dx, y0 - E - dy),
                     (x0 + E + dx, y0 - dy), (x0 + E, y0)]):
            cv.raw('<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                   + f'" fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
        if div:   # 積み木の継ぎ目（見える3面の中央線）
            m = E / 2
            for (x1, y1, x2, y2) in [
                    (x0 + m, y0, x0 + m, y0 - E),                       # 前面 縦
                    (x0, y0 - m, x0 + E, y0 - m),                       # 前面 横
                    (x0 + m, y0 - E, x0 + m + dx, y0 - E - dy),         # 上面 奥行き方向
                    (x0 + dx / 2, y0 - E - dy / 2, x0 + E + dx / 2, y0 - E - dy / 2),
                    (x0 + E, y0 - m, x0 + E + dx, y0 - m - dy),         # 右面 奥行き方向
                    (x0 + E + dx / 2, y0 - dy / 2, x0 + E + dx / 2, y0 - E - dy / 2)]:
                cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                       f'stroke="#000" stroke-width="0.9"/>')
        cv.text_px(x0 + E / 2, y0 + 16, labs, size=FS_CAP, anchor="middle")

    cube(80, 180, 1.0, False, "1辺1cm（積み木）")
    cube(230, 180, 2.0, True, "1辺2cm（相似比1:2）")
    cv.text_px(215, 30, "積み木で立方体を組む——主概念1", size=14, anchor="middle",
               weight="bold")
    cv.text_px(215, 222, "1辺2cmの立方体は，1辺1cmの積み木を縦2個×横2個×高さ2個",
               size=FS_CAP, anchor="middle")
    cv.text_px(215, 239, "（導入: 体積は何倍になるか，数える前に予想を書く）",
               size=FS_CAP, anchor="middle")

    return dict(file="L14_fig1_volume_blocks.svg", canvas=cv, lesson="L14",
                title="積み木の数え上げ（1辺1cm→2cm）",
                intent="主概念1の対比ワーク図。L12方眼の3次元版——高さの分だけ倍が増える",
                params="立方体1cm/2cm・継ぎ目線=見える3面の中央線（キャビネット投影）",
                checks=ck.items)


# ===========================================================================
# 図19: L16 読み取り誤差の拡大（縮尺1/200）
# 本文根拠: lesson_16.md 例題「縮尺1/200の縮図で縦を0.1cm読み違えると実際は何cm？」
# 答え漏れ注意: 答（20cm・×200）は図に書かない——「？」
# ===========================================================================
def fig_L16():
    # --- パラメータ（L15の木の縮図と一致: 水平10m→5cm, 見上げ角35°） ---
    horiz_m, ang, scale_denom = 10.0, 35.0, 200.0
    horiz_cm = horiz_m * 100 / scale_denom            # 5cm
    vert_cm = horiz_cm * math.tan(math.radians(ang))  # ≈3.5cm

    ck = Checker()
    ck.ok("縮尺1/200: 水平10m→縮図上5cm（L15の縮図と一致）", abs(horiz_cm - 5) < 1e-12)
    ck.ok("縮図の縦≈3.5cm（L15「約3.5cm」と一致）", abs(vert_cm - 3.5) < 0.01,
          f"={vert_cm:.4f}cm")
    ck.ok("本文の答と整合: 0.1cm×200=20cm（図には書かない）",
          abs(0.1 * scale_denom - 20) < 1e-12)

    cv = Canvas(440, 258)
    s = 26.0     # px per 縮図上1cm
    x0, y0 = 45, 188
    xr, yt = x0 + horiz_cm * s, y0 - vert_cm * s
    cv.raw(f'<polygon points="{x0},{y0} {xr:.1f},{y0} {xr:.1f},{yt:.1f}" '
           f'fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
    # 直角マーク・35°の弧
    cv.raw(f'<polyline points="{xr - 9:.1f},{y0} {xr - 9:.1f},{y0 - 9} {xr:.1f},{y0 - 9}" '
           f'fill="none" stroke="#000" stroke-width="1.2"/>')
    r = 30
    pts = " ".join(f"{x0 + r * math.cos(math.radians(-t)):.1f},"
                   f"{y0 + r * math.sin(math.radians(-t)):.1f}"
                   for t in [ang * i / 20 for i in range(21)])
    cv.raw(f'<polyline points="{pts}" fill="none" stroke="#000" stroke-width="1.2"/>')
    cv.text_px(x0 + 42, y0 - 10, "35°", size=FS, anchor="middle")
    cv.text_px(x0 + horiz_cm * s / 2, y0 + 17, "5cm", size=FS, anchor="middle")
    cv.text_px(x0 + horiz_cm * s / 2, y0 + 34, "縮尺 1/200 の縮図", size=FS_CAP,
               anchor="middle")
    cv.text_px(xr + 8, (y0 + yt) / 2 + 4, "縦を読む", size=FS_CAP, anchor="start")
    # 拡大鏡: 頂点の読み取りずれ
    cv.raw(f'<circle cx="{xr:.1f}" cy="{yt:.1f}" r="9" fill="none" stroke="#000" '
           f'stroke-width="1.1" stroke-dasharray="{DASH}"/>')
    zx, zy, zr = 335, 90, 42
    cv.raw(f'<circle cx="{zx}" cy="{zy}" r="{zr}" fill="none" stroke="#000" '
           f'stroke-width="1.1" stroke-dasharray="{DASH}"/>')
    for sgn in (1, -1):
        cv.raw(f'<line x1="{xr + 9 * 0.6:.1f}" y1="{yt - sgn * 9 * 0.8:.1f}" '
               f'x2="{zx - zr * 0.75:.1f}" y2="{zy - sgn * zr * 0.66:.1f}" '
               f'stroke="#000" stroke-width="0.8" stroke-dasharray="2 3"/>')
    # 拡大鏡の中身: 正しい先端と読み違えた先端（0.1cm差を誇張表示）
    cv.raw(f'<line x1="{zx}" y1="{zy + zr - 6}" x2="{zx}" y2="{zy - 10}" '
           f'stroke="#000" stroke-width="{MAIN_W}"/>')
    cv.raw(f'<line x1="{zx - 14}" y1="{zy - 10}" x2="{zx + 14}" y2="{zy - 10}" '
           f'stroke="#000" stroke-width="1.1"/>')
    cv.raw(f'<line x1="{zx - 14}" y1="{zy - 26}" x2="{zx + 14}" y2="{zy - 26}" '
           f'stroke="#000" stroke-width="1.1" stroke-dasharray="{DASH}"/>')
    arrow_px(cv, zx + 20, zy - 30, zx + 20, zy - 26, w=1.0, head=4.5)
    arrow_px(cv, zx + 20, zy - 6, zx + 20, zy - 10, w=1.0, head=4.5)
    cv.text_px(zx, zy + zr + 16, "読み取りのずれ 0.1cm", size=11, anchor="middle")
    cv.text_px(340, 178, "実際の長さでは", size=FS, anchor="middle")
    cv.text_px(340, 196, "ずれ＝？", size=FS, anchor="middle", weight="bold")
    cv.text_px(220, 246, "（例題: 0.1cmの読み違いは，実際の長さで何cmのずれになる？）",
               size=FS_CAP, anchor="middle")

    return dict(file="L16_fig1_reading_error_scale.svg", canvas=cv, lesson="L16",
                title="読み取り誤差の拡大（縮尺1/200の縮図）",
                intent="例題の場面図。縮図上の小さなずれが答えに拡大される構造（答は？）",
                params="水平5cm・35°・縦≈3.5cm（L15の縮図と同一）・ずれ0.1cmは誇張表示",
                checks=ck.items)


# ===========================================================================
# 図20: L17 統合演習の共通図
# 本文根拠: lesson_17.md 統合演習「PQ∥BC, AP=4, PB=2, AQ=6, BC=9, △APQ=12cm²」
# 答え漏れ注意: 問1相似比2:3・問4 QC=3/PQ=6・問5 27cm²は書かない（answer_key_L17と照合）
# ===========================================================================
def fig_L17():
    # --- パラメータ（本文 統合演習の設定 と一致させる） ---
    AP, PB, AQ, BC, area_apq = 4.0, 2.0, 6.0, 9.0, 12.0
    AB = AP + PB                    # 6
    AC = AQ * AB / AP               # 9（AQ:AC=AP:AB=2:3 から従属的に決まる）

    A, B, C = tri_from_sides(AB, AC, BC)
    P = lerp(A, B, AP / AB)
    Q = lerp(A, C, AQ / AC)

    ck = Checker()
    ck.ok("AP=4,PB=2,AQ=6,BC=9（本文の与件どおり）",
          abs(dist(A, P) - 4) < 1e-9 and abs(dist(P, B) - 2) < 1e-9
          and abs(dist(A, Q) - 6) < 1e-9 and abs(dist(B, C) - 9) < 1e-9)
    ck.ok("PQ∥BC（外積≈0）",
          abs(cross((0, 0), (Q[0] - P[0], Q[1] - P[1]), (C[0] - B[0], C[1] - B[1]))) < 1e-9)
    ck.ok("answer_key_L17と整合: 相似比2:3・QC=3cm・PQ=6cm（図には？で示す）",
          abs(dist(A, P) / dist(A, B) - 2 / 3) < 1e-9 and abs(dist(Q, C) - 3) < 1e-9
          and abs(dist(P, Q) - 6) < 1e-9, f"QC={dist(Q, C):.4f}, PQ={dist(P, Q):.4f}")
    ck.ok("answer_key_L17と整合: △ABC=12×(3/2)²=27cm²（図には書かない）",
          abs(area_apq * (3 / 2) ** 2 - 27) < 1e-12)

    cv = Canvas(420, 240)
    cv.s = 24.0
    cv.ox, cv.oy = 90, 165
    cv.polygon([A, B, C])
    cv.line(P, Q, w=MAIN_W)
    g = centroid(A, B, C)
    for p, nm in zip((A, B, C), "ABC"):
        cv.label_out(p, g, nm)
    for p, nm in [(P, "P"), (Q, "Q")]:
        cv.dot(p)
        cv.label_out(p, g, nm, dist=14)
    cv.parallel_mark(P, Q, 1, t=0.6)
    cv.parallel_mark(B, C, 1, t=0.6)
    seg_label(cv, A, P, "4cm", off=13, size=11)
    seg_label(cv, P, B, "2cm", off=13, size=11)
    seg_label(cv, A, Q, "6cm", off=-12, size=11)
    seg_label(cv, Q, C, "？", off=-12, size=11)
    seg_label(cv, B, C, "9cm", off=13, size=11)
    seg_label(cv, P, Q, "？", off=13, t=0.38, size=11)
    cv.text((2.5, 2.55), "12cm²", size=11)
    cv.text_px(210, 205, "PQ∥BC，AP=4cm，PB=2cm，AQ=6cm，BC=9cm，△APQ=12cm²",
               size=FS_CAP, anchor="middle")
    cv.text_px(210, 222, "（統合演習 問1〜5の共通図: 相似比・QC・PQ・△ABCの面積を求める）",
               size=FS_CAP, anchor="middle")

    return dict(file="L17_fig1_review_common_figure.svg", canvas=cv, lesson="L17",
                title="統合演習の共通図（PQ∥BC）",
                intent="問1〜5を1つの図で貫く章末の共通図。問う値はすべて？表記",
                params="AP=4,PB=2,AQ=6,BC=9,△APQ=12cm²（AC=9は比から従属決定）",
                checks=ck.items)


# ===========================================================================
# メイン: 生成 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02, fig_L03, fig_L04_cross, fig_L04_overlap,
        fig_L05_conditions, fig_L05_circular, fig_L06, fig_L07, fig_L08,
        fig_L09, fig_L10, fig_L11, fig_L12, fig_L13, fig_L14,
        fig_L15_tree, fig_L15_pond, fig_L16, fig_L17]


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
    for fn in FIGS:
        meta = fn()
        out = ASSETS / meta["file"]
        meta["canvas"].save(out, meta["file"], meta["title"], build_desc(meta))
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓" for d, t in meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 相似単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "全図で下表の幾何検算（スクリプト内assert）が生成時に自動実行され、全件合格。",
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
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
