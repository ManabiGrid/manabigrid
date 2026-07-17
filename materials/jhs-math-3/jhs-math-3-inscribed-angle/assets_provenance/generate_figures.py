#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中3数学「円周角の定理」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み）。
ヘルパーは similar-figures / pythagorean-theorem の generate_figures.py から流用（元は不変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（34枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / xml.etree）
- 幾何の自己検証: 各 fig_* 内の Checker が角度・配置を assert 検算
  （円周角=中心角÷2・同弧等角・直径→90°・弧の対応・逆の反例配置など）。
  1つでも失敗すると例外で停止して図を出力しない。
- 答えの分離方針: 各図に check_tokens（答え漏れ検査トークン・検査の実装定数）と counts（既出数値の出現回数上限）を持たせ、
  SVG内の全テキストを機械検査する。設問の答えの数値は図に現れない。
- 改修方法（第三者向け）: 各 fig_* 冒頭の「パラメータ」ブロック（円周上の配置角など）を
  変えて再実行する。数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。

配置の座標系: 円は中心O=(0,0)・半径1の数学座標（y上向き）。円周上の点は
C(θ)=（cosθ, sinθ）で「円周上の配置角θ（度・反時計回り・右が0°）」により指定する。
弧XYの中心角 = 配置角の差。円周角はすべて angle_deg() の実測で assert する。
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
FS_CAP = 12      # キャプション
DOT_R = 2.5       # 点マーカー半径
ARC_HL = "#c9c9c9"  # 弧の強調（薄グレー太線・白黒印刷で判読可）


# ===========================================================================
# 描画ヘルパー（数学座標: y上向き → SVG座標: y下向き）
# ===========================================================================
class Canvas:
    def __init__(self, width, height, scale=1.0, ox=0.0, oy=0.0):
        self.w, self.h = width, height
        self.s, self.ox, self.oy = scale, ox, oy
        self.defs = []
        self.body = []
        self.texts = []   # 禁止文字列検査用: 図中に置いた全テキスト

    def P(self, p):
        return (self.ox + self.s * p[0], self.oy - self.s * p[1])

    def raw(self, s):
        self.body.append(s)

    def line(self, a, b, w=MAIN_W, dash=None, color="#000"):
        (x1, y1), (x2, y2) = self.P(a), self.P(b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def polygon(self, pts, w=MAIN_W, fill="none", color="#000"):
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(self.P, pts))
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="{color}" '
                 f'stroke-width="{w}" stroke-linejoin="round"/>')

    def dot(self, p, r=DOT_R):
        x, y = self.P(p)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')

    def text(self, p, s, size=FS, anchor="middle", dy=0.35, weight=None):
        x, y = self.P(p)
        wgt = f' font-weight="{weight}"' if weight else ""
        self.texts.append(s)
        self.raw(f'<text x="{x:.1f}" y="{y + size * dy:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def text_px(self, x, y, s, size=FS_CAP, anchor="start", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.texts.append(s)
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def circle(self, c, r, w=MAIN_W, dash=None, color="#000"):
        x, y = self.P(c)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * self.s:.1f}" fill="none" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def arc(self, c, r, a1, a2, w=MAIN_W, color="#000", dash=None, cap="round"):
        """中心c半径rの円弧を配置角a1→a2（度・反時計回り）へ折れ線サンプリングで描く"""
        if a2 < a1:
            a2 += 360.0
        n = max(12, int((a2 - a1) / 4))
        pts = []
        for i in range(n + 1):
            t = math.radians(a1 + (a2 - a1) * i / n)
            pts.append(self.P((c[0] + r * math.cos(t), c[1] + r * math.sin(t))))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        ps = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.raw(f'<polyline points="{ps}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}" stroke-linecap="{cap}"{d}/>')

    def angle_arc(self, v, p, q, r=14.0, n=1, gap=3.5, w=1.2):
        """頂点vで辺vp→vqの間（劣角側）の弧をn重に描く（等角対応=弧の本数）"""
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

    def right_angle(self, v, p, q, size=8.0):
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
def C(deg, r=1.0):
    """円周上の配置角deg（度）→ 単位円上の座標"""
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def cross2(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def angle_deg(v, p, q):
    """頂点vで辺vp・vqがつくる角（度・0〜180）——全assertの実測器"""
    a = math.atan2(p[1] - v[1], p[0] - v[0])
    b = math.atan2(q[1] - v[1], q[0] - v[0])
    d = abs(b - a) % (2 * math.pi)
    return math.degrees(min(d, 2 * math.pi - d))


def line_int(p1, p2, p3, p4):
    """直線p1p2と直線p3p4の交点"""
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (p4[0] - p3[0], p4[1] - p3[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)


def inside_angle(v, p, q, x):
    """点xが角pvq（180°未満）の内部にあるか: vp→vx→vqの回転向きがすべて一致"""
    c = cross2(v, p, q)
    return cross2(v, p, x) * c > 0 and cross2(v, x, q) * c > 0


def same_side(a, b, p, q):
    """p,qが直線abの同じ側にあるか"""
    return cross2(a, b, p) * cross2(a, b, q) > 0


class Checker:
    """幾何検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))

    def ang(self, desc, v, p, q, expect, tol=1e-9):
        got = angle_deg(v, p, q)
        self.ok(desc, abs(got - expect) < tol, f"実測={got:.4f}°")


# ---- 円図の共通部品 --------------------------------------------------------
O = (0.0, 0.0)


def vertex_label(cv, p, name, dist_px=15, size=FS):
    """頂点名を中心(0,0)から離れる向きに置く"""
    x, y = cv.P(p)
    cx, cy = cv.P(O)
    dx, dy = x - cx, y - cy
    L = math.hypot(dx, dy) or 1.0
    cv.text_px(x + dx / L * dist_px, y + dy / L * dist_px + size * 0.35,
               name, size=size, anchor="middle", weight="bold")


def o_label(cv, dir_deg=225, dist_px=13):
    """中心Oのドットとラベル（dir_deg方向へ逃がす）"""
    cv.dot(O)
    x, y = cv.P(O)
    a = math.radians(dir_deg)
    cv.text_px(x + math.cos(a) * dist_px, y - math.sin(a) * dist_px + FS * 0.35,
               "O", size=FS, anchor="middle", weight="bold")


def ang_label(cv, v, p, q, s, r_px=28, size=FS, weight=None):
    """角pvqの二等分線方向へr_pxずらしてラベルを置く"""
    u1 = (p[0] - v[0], p[1] - v[1])
    u2 = (q[0] - v[0], q[1] - v[1])
    l1, l2 = math.hypot(*u1), math.hypot(*u2)
    bx, by = u1[0] / l1 + u2[0] / l2, u1[1] / l1 + u2[1] / l2
    L = math.hypot(bx, by) or 1.0
    cv.text((v[0] + bx / L * (r_px / cv.s), v[1] + by / L * (r_px / cv.s)),
            s, size=size, weight=weight)


def arc_ticks(cv, deg, n=1, half_px=6, gap_deg=5, r=1.0):
    """弧の等長対応マーク: 配置角degの位置で弧を横切る短い放射線をn本"""
    for i in range(n):
        d = deg + (i - (n - 1) / 2) * gap_deg
        a = math.radians(d)
        rin = r - half_px / cv.s
        rout = r + half_px / cv.s
        cv.line((rin * math.cos(a), rin * math.sin(a)),
                (rout * math.cos(a), rout * math.sin(a)), w=1.4)


def arrow_px(cv, x1, y1, x2, y2, w=1.2, head=6.0):
    """SVG座標(px)で矢印。概念図の対応表示用"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="#000" stroke-width="{w}"/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')


# ===========================================================================
# L01 円のふしぎ
# ===========================================================================
def fig_L01_1():
    """L01図1（本文36行目）: 円周角・中心角の定義図。弧ABの強調が生命線"""
    # --- パラメータ（lesson_01.md 主概念1: 下側弧ABの中心角100°の位置・数値は書かない） ---
    aA, aB, aP = 220.0, 320.0, 100.0
    A, B, P = C(aA), C(aB), C(aP)

    ck = Checker()
    ck.ang("中心角∠AOB=100°の位置に配置", O, A, B, 100.0)
    ck.ang("円周角∠APB=中心角÷2=50°", P, A, B, 50.0)
    ck.ok("Pは弧AB（下側）の上にない", not (aA < aP < aB))

    cv = Canvas(360, 332)
    cv.s, cv.ox, cv.oy = 100, 180, 138
    cv.arc(O, 1.0, aA, aB, w=8, color=ARC_HL)   # 弧ABの強調（薄グレー太線）
    cv.circle(O, 1.0)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    cv.line(P, A, w=MAIN_W)
    cv.line(P, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (P, "P")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=180, dist_px=14)
    cv.angle_arc(P, A, B, n=1)
    cv.angle_arc(O, A, B, n=1, r=17)
    ang_label(cv, P, A, B, "円周角", r_px=44, size=FS_CAP)
    ang_label(cv, O, A, B, "中心角", r_px=40, size=FS_CAP)
    mid = C(270, 1.0)
    x, y = cv.P(mid)
    cv.text_px(x, y + 24, "弧AB", size=FS, anchor="middle", weight="bold")
    arrow_px(cv, x, y + 12, x, y + 3, w=1.2)
    cv.text_px(180, 296, "∠APB＝弧ABに対する円周角，∠AOB＝弧ABに対する中心角",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 314, "（Pは弧ABの上にはとらない。角は「どの弧に対するか」とセット）",
               size=FS_CAP, anchor="middle")
    return dict(file="L01_fig1_inscribed_central_definition.svg", canvas=cv, lesson="L01",
                title="円周角と中心角の定義（弧ABの強調つき）",
                intent="主概念1の定義図。弧AB（下側・グレー強調）と円周角・中心角の対応づけ",
                params="円周上の配置(度): A220・B320・P100。数値ラベルなし",
                checks=ck.items, check_tokens=["50°", "100°"])


def fig_L01_2():
    """L01図2（本文66行目）: 実験——Pを動かしても円周角は変わらない"""
    # --- パラメータ（lesson_01.md 主概念2: 中心角100°・P/P′/P″の3点） ---
    aA, aB = 220.0, 320.0
    aPs = [150.0, 105.0, 60.0]
    A, B = C(aA), C(aB)
    Ps = [C(a) for a in aPs]

    ck = Checker()
    ck.ang("中心角∠AOB=100°", O, A, B, 100.0)
    for (nm, p) in zip(["P", "P′", "P″"], Ps):
        ck.ang(f"円周角∠A{nm}B=50°（どこでも中心角の半分）", p, A, B, 50.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 100, 180, 136
    cv.arc(O, 1.0, aA, aB, w=8, color=ARC_HL)
    cv.circle(O, 1.0)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    for p in Ps:
        cv.line(p, A, w=AUX_W)
        cv.line(p, B, w=AUX_W)
        cv.angle_arc(p, A, B, n=1)
    for p, nm in [(A, "A"), (B, "B")] + list(zip(Ps, ["P", "P′", "P″"])):
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=270, dist_px=26)
    cv.angle_arc(O, A, B, n=1, r=15)
    mid = C(270, 1.0)
    x, y = cv.P(mid)
    cv.text_px(x, y + 24, "弧AB", size=FS, anchor="middle", weight="bold")
    cv.text_px(180, 294, "中心角∠AOBを固定し，Pを円周に沿って動かして∠APBを測る",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（P・P′・P″の3か所——それぞれの角はどうなる？）",
               size=FS_CAP, anchor="middle")
    return dict(file="L01_fig2_experiment_moving_point.svg", canvas=cv, lesson="L01",
                title="実験——点Pを動かして円周角を測る",
                intent="主概念2の実験図。同一弧ABへの3つの円周角（どこでも等しいことを測る）",
                params="円周上の配置(度): A220・B320・P150/105/60。角度数値なし",
                checks=ck.items, check_tokens=["50°", "100°"])


def fig_L01_3():
    """L01図3（本文99行目・練習1）: 弧ABに対する円周角をすべて挙げる"""
    # --- パラメータ（lesson_01.md 練習1: 中心角70°・P/Q。70°のみ図に記す） ---
    aA, aB, aP, aQ = 235.0, 305.0, 110.0, 40.0
    A, B, P, Q = C(aA), C(aB), C(aP), C(aQ)

    ck = Checker()
    ck.ang("中心角∠AOB=70°（図に記す唯一の数値）", O, A, B, 70.0)
    ck.ang("∠APB=35°（答え——図に書かない）", P, A, B, 35.0)
    ck.ang("∠AQB=35°（答え——図に書かない）", Q, A, B, 35.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 100, 180, 136
    cv.arc(O, 1.0, aA, aB, w=8, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (A, B):
        cv.line(O, p, w=MAIN_W)
    for p in (P, Q):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (Q, "Q")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=170, dist_px=14)
    cv.angle_arc(O, A, B, n=1, r=15)
    ang_label(cv, O, A, B, "70°", r_px=30)
    cv.text_px(180, 294, "弧AB（下側・グレー）に対する円周角はどれか，すべて挙げる",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（中心角∠AOB＝70°。円周角の数値はまだ求めない）",
               size=FS_CAP, anchor="middle")
    return dict(file="L01_fig3_practice_find_inscribed.svg", canvas=cv, lesson="L01 練習1",
                title="弧ABに対する円周角を全部見つける（中心角70°）",
                intent="練習1の図。OA・OB・PA・PB・QA・QBを全部引き対応づけを問う",
                params="円周上の配置(度): A235・B305（中心角70°は与件）・P110・Q40",
                checks=ck.items, check_tokens=["35°"], counts={"70°": 2})


# ===========================================================================
# L02 円周角の定理
# ===========================================================================
def fig_L02_1():
    """L02図1（本文29行目）: 定理の全体図——弧→中心角→円周角の対応"""
    # --- パラメータ（lesson_02.md 主概念1: 弧AB中心角100°・P/Q。100°のみ記す） ---
    aA, aB, aP, aQ = 220.0, 320.0, 95.0, 148.0
    A, B, P, Q = C(aA), C(aB), C(aP), C(aQ)

    ck = Checker()
    ck.ang("中心角∠AOB=100°", O, A, B, 100.0)
    ck.ang("∠APB=50°=100°÷2（数値は図に書かない）", P, A, B, 50.0)
    ck.ang("∠AQB=50°（同じ弧→等しい）", Q, A, B, 50.0)
    ck.ok("∠APB=∠AQB（定理(2)）",
          abs(angle_deg(P, A, B) - angle_deg(Q, A, B)) < 1e-9)

    cv = Canvas(380, 352)
    cv.s, cv.ox, cv.oy = 102, 190, 142
    cv.arc(O, 1.0, aA, aB, w=8, color=ARC_HL)
    cv.circle(O, 1.0)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    for p in (P, Q):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (Q, "Q")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=175, dist_px=14)
    cv.angle_arc(O, A, B, n=1, r=15)
    ang_label(cv, O, A, B, "100°", r_px=32)
    cv.text((0.0, -0.64), "中心角", size=FS_CAP)
    mid = C(270, 1.0)
    x, y = cv.P(mid)
    cv.text_px(x, y + 26, "弧AB", size=FS, anchor="middle", weight="bold")
    # 対応の矢印: 弧→中心角→円周角（P・Q）
    arrow_px(cv, x, y + 14, x, y + 4, w=1.2)
    ox_, oy_ = cv.P(O)
    px_, py_ = cv.P(P)
    qx_, qy_ = cv.P(Q)
    arrow_px(cv, ox_ - 8, oy_ - 26, px_ + 4, py_ + 30, w=1.2)
    arrow_px(cv, ox_ - 14, oy_ - 20, qx_ + 16, qy_ + 24, w=1.2)
    cv.text_px(190, 316, "弧AB→中心角∠AOB→円周角∠APB・∠AQB の順に対応づける",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 334, "（定理(1) 円周角＝中心角×1/2 ／ 定理(2) 同じ弧なら円周角は等しい）",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig1_theorem_overview.svg", canvas=cv, lesson="L02",
                title="円周角の定理の全体図（弧→中心角→円周角）",
                intent="主概念1の定理図。塗り弧と2つの円周角・中心角100°の対応を矢印で示す",
                params="A=220°,B=320°（中心角100°）,P=95°,Q=148°",
                checks=ck.items, check_tokens=["50°"], counts={"100°": 1})


def fig_L02_2():
    """L02図2（本文50行目・例題1）: 中心角80°→円周角x"""
    # --- パラメータ（lesson_02.md 例題1: 弧BC中心角80°・答え40°は書かない） ---
    aB, aC, aA = 230.0, 310.0, 95.0
    B, Cp, A = C(aB), C(aC), C(aA)

    ck = Checker()
    ck.ang("中心角∠BOC=80°", O, B, Cp, 80.0)
    ck.ang("x=∠BAC=40°=80°÷2（答え——図に書かない）", A, B, Cp, 40.0)

    cv = Canvas(340, 322)
    cv.s, cv.ox, cv.oy = 96, 170, 132
    cv.arc(O, 1.0, aB, aC, w=8, color=ARC_HL)
    cv.circle(O, 1.0)
    cv.line(O, B, w=MAIN_W)
    cv.line(O, Cp, w=MAIN_W)
    cv.line(A, B, w=MAIN_W)
    cv.line(A, Cp, w=MAIN_W)
    for p, nm in [(B, "B"), (Cp, "C"), (A, "A")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=170, dist_px=14)
    cv.angle_arc(O, B, Cp, n=1, r=15)
    ang_label(cv, O, B, Cp, "80°", r_px=30)
    cv.angle_arc(A, B, Cp, n=1)
    ang_label(cv, A, B, Cp, "x", r_px=28)
    cv.text_px(170, 288, "弧BC（グレー）に対する中心角80°→ 円周角∠BAC＝x",
               size=FS_CAP, anchor="middle")
    cv.text_px(170, 306, "（例題1: 頂点Aを含まない側の弧を塗ってから定理(1)）",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig2_example_central_to_inscribed.svg", canvas=cv, lesson="L02 例題1",
                title="中心角から円周角へ（80°→x）",
                intent="例題1の図。塗り弧BC・中心角80°・求める円周角x",
                params="B=230°,C=310°（中心角80°）,A=95°",
                checks=ck.items, check_tokens=["40°"], counts={"80°": 2})


def fig_L02_3():
    """L02図3（本文66行目・例題3）: 同じ弧の円周角どうし 64°→x"""
    # --- パラメータ（lesson_02.md 例題3: ∠APB=64°→弧AB中心角128°の位置） ---
    aA, aB, aP, aQ = 206.0, 334.0, 110.0, 58.0
    A, B, P, Q = C(aA), C(aB), C(aP), C(aQ)

    ck = Checker()
    ck.ang("∠APB=64°（与件）", P, A, B, 64.0)
    ck.ang("x=∠AQB=64°（同じ弧AB→等しい）", Q, A, B, 64.0)
    ck.ang("弧ABの中心角=128°=2×64°", O, A, B, 128.0)
    ck.ok("P・Qは弧ABと反対側・同じ側", aB - 360 < aQ < aA and aB - 360 < aP < aA)

    cv = Canvas(340, 322)
    cv.s, cv.ox, cv.oy = 96, 170, 132
    cv.arc(O, 1.0, aA, aB, w=8, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (P, Q):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (Q, "Q")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    ang_label(cv, P, A, B, "64°", r_px=30)
    ang_label(cv, Q, A, B, "x", r_px=30)
    cv.text_px(170, 288, "∠APBと∠AQBは，どちらも弧AB（グレー）に対する円周角",
               size=FS_CAP, anchor="middle")
    cv.text_px(170, 306, "（例題3: 中心角が図になくても定理(2)で直接つなぐ）",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig3_example_same_arc.svg", canvas=cv, lesson="L02 例題3",
                title="円周角どうしをつなぐ（64°→x）",
                intent="例題3の図。同一弧ABへの2円周角（弧の強調と1重弧マークで対応）",
                params="A=206°,B=334°（中心角128°）,P=110°,Q=58°",
                checks=ck.items, counts={"64°": 1})


def fig_L02_4():
    """L02図4（本文79行目・例題4）: 円周角2組の図"""
    # --- パラメータ（lesson_02.md 例題4: ∠BAC=30°→弧BC=60°, ∠ACD=45°→弧AD=90°） ---
    aA, aB, aC, aD = 140.0, 200.0, 260.0, 50.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)

    ck = Checker()
    ck.ang("∠BAC=30°（与件）→弧BC=60°", A, B, Cp, 30.0)
    ck.ang("弧BC中心角=60°", O, B, Cp, 60.0)
    ck.ang("∠ACD=45°（与件）→弧AD=90°", Cp, A, D, 45.0)
    ck.ang("弧AD中心角=90°", O, A, D, 90.0)
    ck.ang("∠BDC=30°（答え——図に書かない）", D, B, Cp, 30.0)
    ck.ang("∠ABD=45°（答え——図に書かない）", B, A, D, 45.0)

    cv = Canvas(360, 344)
    cv.s, cv.ox, cv.oy = 98, 180, 138
    cv.arc(O, 1.0, aB, aC, w=8, color=ARC_HL)               # 弧BC
    cv.arc(O, 1.0, aD, aA, w=4, color="#8f8f8f")            # 弧AD（塗り分け=太さ違い）
    cv.circle(O, 1.0)
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.angle_arc(A, B, Cp, n=1)
    cv.angle_arc(D, B, Cp, n=1)      # 同じ弧BC→同じ1重弧
    cv.angle_arc(Cp, A, D, n=2)
    cv.angle_arc(B, A, D, n=2)       # 同じ弧AD→同じ2重弧
    ang_label(cv, A, B, Cp, "30°", r_px=44)
    ang_label(cv, Cp, A, D, "45°", r_px=32)
    ang_label(cv, D, B, Cp, "？", r_px=32)
    ang_label(cv, B, A, D, "？", r_px=32)
    cv.text_px(180, 310, "∠BAC＝30°・∠ACD＝45°から，∠BDC・∠ABD（？）を求める",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 328, "（例題4: 1つの角につき1回塗る。同じ弧マーク＝同じ本数の角弧）",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig4_example_two_pairs.svg", canvas=cv, lesson="L02 例題4",
                title="1つの図に円周角が2組（30°と45°）",
                intent="例題4の図。弧BC/弧ADを塗り分け・等角は弧の本数（1重/2重）で対応",
                params="A=140°,B=200°,C=260°,D=50°（弧BC=60°・弧AD=90°）",
                checks=ck.items, counts={"30°": 2, "45°": 2})


def fig_L02_5():
    """L02図5（本文109・110・114行目 練習3・4・5の3パネル統合）"""
    ck = Checker()
    cv = Canvas(660, 300)
    cv.s = 70

    # --- パネル1（練習3）: ∠APB=41°→∠AQB=x ---
    aA, aB, aP, aQ = 229.0, 311.0, 108.0, 55.0
    A, B, P, Q = C(aA), C(aB), C(aP), C(aQ)
    ck.ang("練習3: ∠APB=41°（与件）", P, A, B, 41.0)
    ck.ang("練習3: x=∠AQB=41°（答え——図に書かない・同弧）", Q, A, B, 41.0)
    ck.ang("練習3: 弧AB中心角=82°=2×41°", O, A, B, 82.0)
    cv.ox, cv.oy = 112, 108
    cv.arc(O, 1.0, aA, aB, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (P, Q):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1, r=11)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (Q, "Q")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    ang_label(cv, P, A, B, "41°", r_px=38, size=FS_CAP)
    ang_label(cv, Q, A, B, "x", r_px=24, size=FS_CAP)
    cv.text_px(112, 216, "練習3", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル2（練習4）: ∠ACB=63°→∠ADB=x ---
    aA, aB, aC, aD = 207.0, 333.0, 112.0, 62.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    ck.ang("練習4: ∠ACB=63°（与件）", Cp, A, B, 63.0)
    ck.ang("練習4: x=∠ADB=63°（答え——図に書かない・同弧）", D, A, B, 63.0)
    ck.ang("練習4: 弧AB中心角=126°=2×63°", O, A, B, 126.0)
    cv.ox, cv.oy = 330, 108
    cv.arc(O, 1.0, aA, aB, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (Cp, D):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1, r=11)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    ang_label(cv, Cp, A, B, "63°", r_px=24, size=FS_CAP)
    ang_label(cv, D, A, B, "x", r_px=24, size=FS_CAP)
    cv.text_px(330, 216, "練習4", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル3（練習5）: OA=OB・∠OAB=25°→∠APB=x（中心角130°経由） ---
    aA, aB, aP = 205.0, 335.0, 90.0
    A, B, P = C(aA), C(aB), C(aP)
    ck.ang("練習5: ∠OAB=25°（与件・二等辺の底角）", A, O, B, 25.0)
    ck.ang("練習5: 中心角∠AOB=130°（途中の答え——図に書かない）", O, A, B, 130.0)
    ck.ang("練習5: x=∠APB=65°（答え——図に書かない）", P, A, B, 65.0)
    ck.ok("練習5: OA=OB（半径）", abs(dist(O, A) - dist(O, B)) < 1e-12)
    cv.ox, cv.oy = 548, 108
    cv.arc(O, 1.0, aA, aB, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    cv.line(P, A, w=MAIN_W)
    cv.line(P, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (P, "P")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=90, dist_px=13)
    cv.angle_arc(A, O, B, n=1, r=11)
    ang_label(cv, A, O, B, "25°", r_px=40, size=FS_CAP)
    cv.angle_arc(P, A, B, n=1, r=11)
    ang_label(cv, P, A, B, "x", r_px=24, size=FS_CAP)
    cv.text_px(548, 216, "練習5（OA＝OB）", size=FS_CAP, anchor="middle", weight="bold")

    cv.text_px(330, 252, "練習3・4: 同じ弧（グレー）に対する円周角の組を見つけて定理(2)",
               size=FS_CAP, anchor="middle")
    cv.text_px(330, 270, "練習5: 二等辺三角形OABから中心角を先に求めて定理(1)",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig5_practice_3_4_5.svg", canvas=cv, lesson="L02 練習3〜5",
                title="練習3・4・5（3パネル統合）",
                intent="同弧等角2題＋半径二等辺経由1題。塗り弧と1重弧マークで対応",
                params="P3: 中心角82°／P4: 中心角126°／P5: ∠OAB=25°（中心角は導出値のため非表示）",
                checks=ck.items, check_tokens=["65°", "130°"],
                counts={"41°": 1, "63°": 1, "25°": 1})


def fig_L02_6():
    """L02図6（本文115・116行目 練習6・7の2パネル統合）"""
    ck = Checker()
    cv = Canvas(560, 330)
    cv.s = 88

    # --- パネル1（練習6）: ∠BAC=30°・∠ACD=28°→x・y ---
    aA, aB, aC, aD = 140.0, 200.0, 260.0, 84.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    ck.ang("練習6: ∠BAC=30°（与件）→弧BC=60°", A, B, Cp, 30.0)
    ck.ang("練習6: ∠ACD=28°（与件）→弧AD=56°", Cp, A, D, 28.0)
    ck.ang("練習6: x=∠BDC=30°（答え——出現1回に固定）", D, B, Cp, 30.0)
    ck.ang("練習6: y=∠ABD=28°（答え——出現1回に固定）", B, A, D, 28.0)
    cv.ox, cv.oy = 140, 128
    cv.arc(O, 1.0, aB, aC, w=6, color=ARC_HL)
    cv.arc(O, 1.0, aD, aA, w=3.4, color="#8f8f8f")
    cv.circle(O, 1.0)
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    cv.angle_arc(A, B, Cp, n=1, r=12)
    cv.angle_arc(D, B, Cp, n=1, r=12)
    cv.angle_arc(Cp, A, D, n=2, r=12)
    cv.angle_arc(B, A, D, n=2, r=12)
    ang_label(cv, A, B, Cp, "30°", r_px=40, size=FS_CAP)
    ang_label(cv, Cp, A, D, "28°", r_px=29, size=FS_CAP)
    ang_label(cv, D, B, Cp, "x", r_px=28, size=FS_CAP)
    ang_label(cv, B, A, D, "y", r_px=28, size=FS_CAP)
    cv.text_px(140, 258, "練習6", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル2（練習7）: 中心角110°・130°→残りの中心角と△ABCの内角 ---
    aA, aB, aC = 145.0, 35.0, 265.0
    A, B, Cp = C(aA), C(aB), C(aC)
    ck.ang("練習7: 中心角∠AOB=110°（与件・Cを含まない弧AB）", O, A, B, 110.0)
    ck.ang("練習7: 中心角∠BOC=130°（与件・Aを含まない弧BC）", O, B, Cp, 130.0)
    ck.ang("練習7: 中心角∠AOC=120°（答え——図に書かない）", O, A, Cp, 120.0)
    ck.ang("練習7: ∠BAC=65°（答え=130°÷2）", A, B, Cp, 65.0)
    ck.ang("練習7: ∠ABC=60°（答え=120°÷2）", B, A, Cp, 60.0)
    ck.ang("練習7: ∠BCA=55°（答え=110°÷2）", Cp, A, B, 55.0)
    ck.ok("練習7: 内角の和=180°",
          abs(angle_deg(A, B, Cp) + angle_deg(B, A, Cp) + angle_deg(Cp, A, B) - 180) < 1e-9)
    cv.ox, cv.oy = 415, 128
    cv.circle(O, 1.0)
    cv.polygon([A, B, Cp], w=MAIN_W)
    for p in (A, B, Cp):
        cv.line(O, p, w=AUX_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=205, dist_px=20)
    cv.angle_arc(O, A, B, n=1, r=12)
    cv.angle_arc(O, B, Cp, n=2, r=12)
    ang_label(cv, O, A, B, "110°", r_px=30, size=FS_CAP)
    ang_label(cv, O, B, Cp, "130°", r_px=32, size=FS_CAP)
    cv.text_px(415, 258, "練習7", size=FS_CAP, anchor="middle", weight="bold")

    cv.text_px(280, 288, "練習6: 例題4と同じ型（1つの角につき1回塗る）",
               size=FS_CAP, anchor="middle")
    cv.text_px(280, 306, "練習7: 中心角110°・130°から残りの中心角と△ABCの内角を求める",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig6_practice_6_7.svg", canvas=cv, lesson="L02 練習6・7",
                title="練習6・7（2パネル統合）",
                intent="円周角2組の型＋中心角3分割から内角。答えの角度は図に置かない",
                params="P6: 弧BC/ADの作図値は答え直結のため非表示／P7: 与件の中心角110°・130°から残り1つを求める構図（値は非表示）",
                checks=ck.items, check_tokens=["120°", "65°", "60°", "55°"],
                counts={"30°": 1, "28°": 1, "110°": 2, "130°": 2})


def fig_L02_7():
    """L02図7（本文 練習9・鈍角ケース）: 中心角216°（大回り）と144°の取り違え防止"""
    # --- パラメータ（lesson_02.md 練習9: 弧BC（Aを含まない側）中心角216°。答え108°・誤答72°は書かない） ---
    aA, aB, aC = 90.0, 162.0, 18.0
    A, B, Cp = C(aA), C(aB), C(aC)

    ck = Checker()
    ck.ang("Aを含む側の弧BCの中心角=144°", O, B, Cp, 144.0)
    ck.ok("Aを含まない側の弧BC（大回り）の中心角=216°=360°−144°",
          abs((360.0 - angle_deg(O, B, Cp)) - 216.0) < 1e-9,
          f"実測={360.0 - angle_deg(O, B, Cp):.4f}°")
    ck.ang("x=∠BAC=108°=216°÷2（答え——図に書かない）", A, B, Cp, 108.0)
    ck.ok("∠BACは鈍角（90°超）", angle_deg(A, B, Cp) > 90.0,
          f"実測={angle_deg(A, B, Cp):.4f}°")
    ck.ok("Aは144°側の弧の上（C=18°＜A=90°＜B=162°）", aC < aA < aB)
    ck.ok("両側の円周角の和: 216°÷2＋144°÷2＝180°",
          abs(216.0 / 2 + 144.0 / 2 - 180.0) < 1e-9)

    cv = Canvas(340, 340)
    cv.s, cv.ox, cv.oy = 96, 170, 132
    cv.arc(O, 1.0, aB, aC + 360.0, w=8, color=ARC_HL)  # Aを含まない側（大回り216°）を塗る
    cv.circle(O, 1.0)
    cv.line(O, B, w=MAIN_W)
    cv.line(O, Cp, w=MAIN_W)
    cv.line(A, B, w=MAIN_W)
    cv.line(A, Cp, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=90, dist_px=12)
    # 大回りの中心角216°（塗った弧側・実線の角弧）
    cv.arc(O, 17.0 / cv.s, aB, aC + 360.0, w=1.2)
    cv.text((0.0, -34.0 / cv.s), "216°")
    # 残りの弧に対する中心角144°（Aの側・破線の角弧）
    cv.arc(O, 26.0 / cv.s, aC, aB, w=1.2, dash=DASH)
    cv.text((0.0, 44.0 / cv.s), "144°")
    cv.angle_arc(A, B, Cp, n=1)
    ang_label(cv, A, B, Cp, "x", r_px=26)
    cv.text_px(170, 306, "弧BC（グレー・Aを含まない側）の中心角は大回りの216°",
               size=FS_CAP, anchor="middle")
    cv.text_px(170, 324, "（練習9: 144°はAを含む側の弧に対する中心角）",
               size=FS_CAP, anchor="middle")
    return dict(file="L02_fig7_practice_obtuse_inscribed.svg", canvas=cv, lesson="L02 練習9",
                title="円周角と2つの弧（中心角144°と216°）",
                intent="練習9の図。2つの弧の中心角144°と216°を両方示す。どちらが∠BACに対応するかは本文の練習で考える",
                params="A=90°,B=162°,C=18°（2つの弧BCの中心角は144°と216°）",
                checks=ck.items, check_tokens=["108°", "72°"],
                counts={"216°": 2, "144°": 2})


# ===========================================================================
# L03 直径と円周角
# ===========================================================================
def fig_L03_1():
    """L03図1（本文30行目）: 直径AB→円周角は？（中心角180°が見える構図）"""
    # --- パラメータ（lesson_03.md 主概念1: 直角の印も数値も付けない） ---
    aA, aB, aP, aP2 = 180.0, 0.0, 115.0, 55.0
    A, B, P, P2 = C(aA), C(aB), C(aP), C(aP2)

    ck = Checker()
    ck.ok("ABは直径（A・O・Bが一直線）", abs(cross2(A, B, O)) < 1e-12)
    ck.ang("弧ABの中心角=180°", O, A, B, 180.0)
    ck.ang("∠APB=90°=180°÷2（印も数値も図に付けない）", P, A, B, 90.0)
    ck.ang("∠AP′B=90°（同上）", P2, A, B, 90.0)

    cv = Canvas(360, 314)
    cv.s, cv.ox, cv.oy = 100, 180, 140
    cv.circle(O, 1.0)
    cv.line(A, B, w=MAIN_W)          # 直径（A-O-Bの直線）
    for p in (P, P2):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (P2, "P′")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=250, dist_px=13)
    cv.text_px(180, 278, "ABは円Oの直径（A・O・Bは一直線）",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 296, "（半円の弧に対する円周角∠APB・∠AP′Bの大きさは？）",
               size=FS_CAP, anchor="middle")
    return dict(file="L03_fig1_diameter_semicircle.svg", canvas=cv, lesson="L03",
                title="半円の弧に対する円周角（直径ABとP・P′）",
                intent="主概念1の導入図。中心角が「直線AOB」として見える構図（値は図に置かない）",
                params="円周上の配置(度): A180・B0（直径）・P115・P′55。印・数値なし",
                checks=ck.items, check_tokens=["90°", "180°"])


def fig_L03_2():
    """L03図2（本文36行目・例題1）: 直径BC・∠ABC=32°"""
    # --- パラメータ（lesson_03.md 例題1: ∠ABC=32°→弧AC=64°の位置） ---
    aB, aC, aA = 180.0, 0.0, 64.0
    B, Cp, A = C(aB), C(aC), C(aA)

    ck = Checker()
    ck.ok("BCは直径", abs(cross2(B, Cp, O)) < 1e-12)
    ck.ang("∠ABC=32°（与件）", B, A, Cp, 32.0)
    ck.ang("∠BAC=90°（半円の弧——答え側・図に書かない）", A, B, Cp, 90.0)
    ck.ang("∠ACB=58°（答え——図に書かない）", Cp, A, B, 58.0)

    cv = Canvas(340, 300)
    cv.s, cv.ox, cv.oy = 96, 170, 134
    cv.circle(O, 1.0)
    cv.polygon([A, B, Cp], w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=250, dist_px=13)
    cv.angle_arc(B, A, Cp, n=1)
    ang_label(cv, B, A, Cp, "32°", r_px=30)
    cv.text_px(170, 266, "BCは円Oの直径——∠BACと∠ACBを求める",
               size=FS_CAP, anchor="middle")
    cv.text_px(170, 284, "（例題1: 直径を見たら，どこかに隠れている角を疑う）",
               size=FS_CAP, anchor="middle")
    return dict(file="L03_fig2_example_diameter_triangle.svg", canvas=cv, lesson="L03 例題1",
                title="直径がつくる三角形（∠ABC=32°）",
                intent="例題1の図。直径BC上の△ABC・与件32°のみ記載",
                params="B=180°,C=0°（直径）,A=64°（弧AC=64°）",
                checks=ck.items, check_tokens=["90°", "58°"], counts={"32°": 1})


def fig_L03_3():
    """L03図3（本文63行目・例題2）: 三角定規の直角2回で中心を見つける"""
    # --- パラメータ（lesson_03.md 例題2: ∠APB=∠A′P′B′=90°→AB・A′B′は直径） ---
    aA, aB, aP = 230.0, 50.0, 130.0        # AB=直径1本目
    aA2, aB2, aP2 = 170.0, 350.0, 282.0    # A′B′=直径2本目
    A, B, P = C(aA), C(aB), C(aP)
    A2, B2, P2 = C(aA2), C(aB2), C(aP2)

    ck = Checker()
    ck.ang("∠APB=90°（直角の印のみ記す）", P, A, B, 90.0)
    ck.ang("∠A′P′B′=90°（直角の印のみ記す）", P2, A2, B2, 90.0)
    ck.ok("ABは中心を通る（円周角90°→直径）", abs(cross2(A, B, O)) < 1e-9)
    ck.ok("A′B′も中心を通る", abs(cross2(A2, B2, O)) < 1e-9)
    xI = line_int(A, B, A2, B2)
    ck.ok("2本の交点=中心O", dist(xI, O) < 1e-9, f"交点=({xI[0]:.2e},{xI[1]:.2e})")

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 100, 180, 142
    cv.circle(O, 1.0)
    # 三角定規（Pに直角の頂点を当てた輪郭・グレー）
    tP1 = lerp(P, A, 0.42)
    tP2 = lerp(P, B, 0.34)
    cv.polygon([P, tP1, tP2], w=1.1, color="#888")
    cv.line(P, A, w=MAIN_W)
    cv.line(P, B, w=MAIN_W)
    cv.line(A, B, w=BOLD_W)     # 見つかった弦（直径）は強調
    cv.line(P2, A2, w=AUX_W, dash=DASH)
    cv.line(P2, B2, w=AUX_W, dash=DASH)
    cv.line(A2, B2, w=BOLD_W)
    cv.right_angle(P, A, B)
    cv.right_angle(P2, A2, B2)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (A2, "A′"), (B2, "B′"), (P2, "P′")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.dot(O)
    x, y = cv.P(O)
    cv.text_px(x + 20, y + 24, "中心O", size=FS, anchor="start", weight="bold")
    cv.text_px(180, 294, "直角を円周上に当て，2辺と円周の交点を結ぶ——を2回",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（2本の線分の交点が中心O。三角定規の輪郭はグレー）",
               size=FS_CAP, anchor="middle")
    return dict(file="L03_fig3_find_center_right_angle.svg", canvas=cv, lesson="L03 例題2",
                title="三角定規の直角で円の中心を見つける",
                intent="例題2の手順図。90°の円周角→弦は直径→2本の交点=中心",
                params="AB: A=230°,B=50°／A′B′: A′=170°,B′=350°／P=130°,P′=282°",
                checks=ck.items, check_tokens=["°"])


def fig_L03_4():
    """L03図4（本文85・86行目 練習1・2の2パネル統合）"""
    ck = Checker()
    cv = Canvas(560, 300)
    cv.s = 88

    # --- パネル1（練習1）: 直径AB・∠CAB=41° ---
    aA, aB, aC = 180.0, 0.0, 82.0
    A, B, Cp = C(aA), C(aB), C(aC)
    ck.ok("練習1: ABは直径", abs(cross2(A, B, O)) < 1e-12)
    ck.ang("練習1: ∠CAB=41°（与件）", A, Cp, B, 41.0)
    ck.ang("練習1: ∠ACB=90°（答え——図は？のみ）", Cp, A, B, 90.0)
    ck.ang("練習1: ∠CBA=49°（答え——図は？のみ）", B, Cp, A, 49.0)
    cv.ox, cv.oy = 140, 122
    cv.circle(O, 1.0)
    cv.polygon([A, B, Cp], w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=250, dist_px=12)
    cv.angle_arc(A, Cp, B, n=1, r=12)
    ang_label(cv, A, Cp, B, "41°", r_px=27, size=FS_CAP)
    ang_label(cv, Cp, A, B, "？", r_px=24, size=FS_CAP)
    ang_label(cv, B, Cp, A, "？", r_px=24, size=FS_CAP)
    cv.text_px(140, 240, "練習1（ABは直径）", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル2（練習2）: 直径AB・∠DAB=35°・Dは右寄り ---
    aD = 70.0
    D = C(aD)
    ck.ok("練習2: ABは直径", abs(cross2(A, B, O)) < 1e-12)
    ck.ang("練習2: ∠DAB=35°（与件）", A, D, B, 35.0)
    ck.ang("練習2: ∠ADB=90°（答え——図は？のみ）", D, A, B, 90.0)
    ck.ang("練習2: ∠DBA=55°（答え——図は？のみ）", B, D, A, 55.0)
    cv.ox, cv.oy = 415, 122
    cv.circle(O, 1.0)
    cv.line(A, B, w=MAIN_W)
    cv.line(D, A, w=MAIN_W)
    cv.line(D, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=250, dist_px=12)
    cv.angle_arc(A, D, B, n=1, r=12)
    ang_label(cv, A, D, B, "35°", r_px=27, size=FS_CAP)
    ang_label(cv, D, A, B, "？", r_px=24, size=FS_CAP)
    ang_label(cv, B, D, A, "？", r_px=24, size=FS_CAP)
    cv.text_px(415, 240, "練習2（ABは直径）", size=FS_CAP, anchor="middle", weight="bold")

    cv.text_px(280, 270, "直径がつくる三角形——？の角を求め，内角の和で検算する",
               size=FS_CAP, anchor="middle")
    return dict(file="L03_fig4_practice_1_2.svg", canvas=cv, lesson="L03 練習1・2",
                title="練習1・2（2パネル統合・直径と三角形）",
                intent="半円の弧に対する円周角の定理を使う基本2題。与件の角のみ記載・答えは？",
                params="P1: ∠CAB=41°（C=82°）／P2: ∠DAB=35°（D=70°・右寄り）",
                checks=ck.items, check_tokens=["90°", "49°", "55°"],
                counts={"41°": 1, "35°": 1})


def fig_L03_5():
    """L03図5（本文87行目・練習3）: 3本の弦のうち直径はどれか"""
    # --- パラメータ（lesson_03.md 練習3: TUのみ中心を通る・∠TVU=90°の印のみ） ---
    aT, aU, aV = 210.0, 30.0, 120.0
    aP, aQ = 150.0, 250.0
    aR, aS = 300.0, 20.0
    T, U, V = C(aT), C(aU), C(aV)
    P, Q = C(aP), C(aQ)
    R, S = C(aR), C(aS)

    def chord_dist(p, q):
        return abs(cross2(p, q, O)) / dist(p, q)

    ck = Checker()
    ck.ang("∠TVU=90°（直角の印のみ）", V, T, U, 90.0)
    ck.ok("TUは中心を通る（円周角90°の弦）", chord_dist(T, U) < 1e-12)
    ck.ok("PQは中心を通らない", chord_dist(P, Q) > 0.15,
          f"中心との距離={chord_dist(P, Q):.3f}")
    ck.ok("RSは中心を通らない", chord_dist(R, S) > 0.15,
          f"中心との距離={chord_dist(R, S):.3f}")

    cv = Canvas(360, 318)
    cv.s, cv.ox, cv.oy = 100, 180, 138
    cv.circle(O, 1.0)   # 中心の印なし
    cv.line(T, U, w=MAIN_W)
    cv.line(P, Q, w=MAIN_W)
    cv.line(R, S, w=MAIN_W)
    cv.line(V, T, w=AUX_W, dash=DASH)
    cv.line(V, U, w=AUX_W, dash=DASH)
    cv.right_angle(V, T, U)
    for p, nm in [(T, "T"), (U, "U"), (V, "V"), (P, "P"), (Q, "Q"), (R, "R"), (S, "S")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    cv.text_px(180, 282, "円周上の点Vから見た∠TVUは直角（印）",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 300, "（弦TU・PQ・RSのうち，この円の直径といえるものはどれ？）",
               size=FS_CAP, anchor="middle")
    return dict(file="L03_fig5_practice_which_diameter.svg", canvas=cv, lesson="L03 練習3",
                title="3本の弦——直径といえるのはどれか",
                intent="練習3の図。90°の円周角の弦だけが中心を通る（中心の印は描かない）",
                params="TU: T=210°,U=30°（対心）,V=120°／PQ: 150°/250°／RS: 300°/20°",
                checks=ck.items, check_tokens=["°"])


# ===========================================================================
# L04 証明のよさ
# ===========================================================================
def fig_L04_1():
    """L04図1（本文38行目）: 証明の図——直径PQで角をa・bに分ける"""
    # --- パラメータ（lesson_04.md 主概念2: a=25°・b=30°の位置関係・文字のみ記す） ---
    aP, aA, aB = 90.0, 220.0, 330.0
    P, A, B = C(aP), C(aA), C(aB)
    Q = C(aP - 180.0)

    ck = Checker()
    ck.ok("PQは直径（P・O・Qが一直線）", abs(cross2(P, Q, O)) < 1e-12)
    ck.ang("a=∠APQ=25°の位置", P, A, Q, 25.0)
    ck.ang("b=∠QPB=30°の位置", P, Q, B, 30.0)
    ck.ang("∠AOQ=2a=50°（外角）", O, A, Q, 50.0)
    ck.ang("∠QOB=2b=60°（外角）", O, Q, B, 60.0)
    ck.ang("∠APB=a+b=55°", P, A, B, 55.0)
    ck.ang("∠AOB=2(a+b)=110°=2×∠APB", O, A, B, 110.0)
    ck.ok("中心Oは∠APBの内部（本文の場合分けどおり）", inside_angle(P, A, B, O))

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 100, 180, 132
    cv.circle(O, 1.0)
    cv.line(P, Q, w=AUX_W, dash=DASH)   # 作戦の補助線=直径PQ
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    cv.line(P, A, w=MAIN_W)
    cv.line(P, B, w=MAIN_W)
    for p, nm in [(P, "P"), (A, "A"), (B, "B"), (Q, "Q")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=0, dist_px=14)
    cv.angle_arc(P, A, Q, n=1)
    cv.angle_arc(P, Q, B, n=2)
    ang_label(cv, P, A, Q, "a", r_px=28)
    ang_label(cv, P, Q, B, "b", r_px=28)
    cv.text_px(180, 294, "作戦: Pから中心Oを通る直径PQ（破線）を引き，角をaとbに分ける",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（OP＝OA＝OB＝半径→二等辺三角形が2つ現れる）",
               size=FS_CAP, anchor="middle")
    return dict(file="L04_fig1_proof_diameter_split.svg", canvas=cv, lesson="L04",
                title="証明の図（直径PQでa・bに分割）",
                intent="主概念2の証明図。補助線PQは破線・角はa/bの文字のみ",
                params="P=90°,A=220°,B=330°（a=25°・b=30°の位置関係）",
                checks=ck.items, check_tokens=["°"])


def fig_L04_2():
    """L04図2（本文90行目・stretch S1）: 場合分け(1)(2)の2パネル"""
    ck = Checker()
    cv = Canvas(560, 300)
    cv.s = 88

    # --- パネル1: 中心Oが辺PA上（PAが直径） ---
    aP, aA, aB = 180.0, 0.0, 60.0
    P, A, B = C(aP), C(aA), C(aB)
    ck.ok("(1) PAは直径（Oが辺PA上）", abs(cross2(P, A, O)) < 1e-12)
    ck.ang("(1) ∠APB=30°の位置（数値は書かない）", P, A, B, 30.0)
    ck.ang("(1) ∠AOB=60°=2×∠APB", O, A, B, 60.0)
    cv.ox, cv.oy = 140, 122
    cv.circle(O, 1.0)
    cv.line(P, A, w=MAIN_W)
    cv.line(P, B, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    for p, nm in [(P, "P"), (A, "A"), (B, "B")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=250, dist_px=12)
    cv.text_px(140, 240, "(1) PAが直径（Oが辺PA上）", size=FS_CAP,
               anchor="middle", weight="bold")

    # --- パネル2: 中心Oが∠APBの外部（∠AOB=70°・∠APB=35°の位置関係） ---
    aA2, aB2, aP2 = 240.0, 310.0, 40.0
    A2, B2, P2 = C(aA2), C(aB2), C(aP2)
    ck.ang("(2) 中心角∠AOB=70°の位置（数値は書かない）", O, A2, B2, 70.0)
    ck.ang("(2) ∠APB=35°=70°÷2", P2, A2, B2, 35.0)
    ck.ok("(2) 中心Oは∠APBの外部", not inside_angle(P2, A2, B2, O))
    cv.ox, cv.oy = 415, 122
    cv.circle(O, 1.0)
    cv.line(O, A2, w=MAIN_W)
    cv.line(O, B2, w=MAIN_W)
    cv.line(P2, A2, w=MAIN_W)
    cv.line(P2, B2, w=MAIN_W)
    for p, nm in [(P2, "P"), (A2, "A"), (B2, "B")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=155, dist_px=13)
    cv.text_px(415, 240, "(2) Oが∠APBの外部（A・Bが近い）", size=FS_CAP,
               anchor="middle", weight="bold")

    cv.text_px(280, 270, "stretch S1: 配置が変わると証明の式の組み立てはどう変わる？",
               size=FS_CAP, anchor="middle")
    return dict(file="L04_fig2_stretch_case_split.svg", canvas=cv, lesson="L04 stretch S1",
                title="場合分け(1)辺上・(2)外部（2パネル統合）",
                intent="stretchの図。中心の位置3通りのうち残り2つ。数値なし",
                params="(1) P=180°,A=0°,B=60°／(2) A=240°,B=310°（中心角70°）,P=40°",
                checks=ck.items, check_tokens=["°"])


# ===========================================================================
# L05 円周角の定理の逆
# ===========================================================================
def fig_L05_1():
    """L05図1（本文30行目）: 逆の定理図——等角2つで円が浮かぶ"""
    # --- パラメータ（lesson_05.md 主概念1: ∠APB=∠AQB=50°・円は破線） ---
    aA, aB, aP, aQ = 220.0, 320.0, 90.0, 143.0
    A, B, P, Q = C(aA), C(aB), C(aP), C(aQ)

    ck = Checker()
    ck.ang("∠APB=50°（与件）", P, A, B, 50.0)
    ck.ang("∠AQB=50°（与件）", Q, A, B, 50.0)
    ck.ok("P・Qは直線ABの同じ側（上側）", same_side(A, B, P, Q))
    ck.ok("4点は単位円上（判定の結論=破線の円）",
          all(abs(dist(O, p) - 1) < 1e-12 for p in (A, B, P, Q)))

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 96, 180, 132
    cv.circle(O, 1.0, w=AUX_W, dash=DASH)   # 出現する円は破線
    ext1, ext2 = lerp(A, B, -0.3), lerp(A, B, 1.3)
    cv.line(ext1, ext2, w=MAIN_W)           # 直線AB
    for p in (P, Q):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1)
    for p, nm in [(A, "A"), (B, "B"), (P, "P"), (Q, "Q")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    ang_label(cv, P, A, B, "50°", r_px=30)
    ang_label(cv, Q, A, B, "50°", r_px=30)
    cv.text_px(180, 294, "P・Qは直線ABの同じ側で，ABを同じ50°で見ている",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（→4点A・B・P・Qは一つの円周上にある＝破線の円が出現する）",
               size=FS_CAP, anchor="middle")
    return dict(file="L05_fig1_converse_theorem.svg", canvas=cv, lesson="L05",
                title="円周角の定理の逆（同じ側＋等角→円）",
                intent="主概念1の定理図。まだ無い円を破線で出現させる",
                params="A=220°,B=320°,P=90°,Q=143°（すべて50°を張る単位円上）",
                checks=ck.items, counts={"50°": 3})


def fig_L05_2():
    """L05図2（本文38行目）: 反例——「同じ側」を落とすと壊れる"""
    # --- パラメータ（lesson_05.md 主概念2: 下側のQ′は円に乗らない・反対側の円周角は130°） ---
    aA, aB, aP = 220.0, 320.0, 90.0
    A, B, P = C(aA), C(aB), C(aP)
    # Q′= Pを直線ABで折り返した点（下側で∠AQ′B=50°を張るが，円の外）
    yAB = A[1]
    Q2 = (P[0], 2 * yAB - P[1])

    ck = Checker()
    ck.ang("∠APB=50°（上側・円周上）", P, A, B, 50.0)
    ck.ang("∠AQ′B=50°（下側でも50°は張れる）", Q2, A, B, 50.0)
    ck.ok("Q′は直線ABについてPと反対側", not same_side(A, B, P, Q2))
    ck.ok("Q′はA・B・Pを通る円の上にない（外側）", dist(O, Q2) > 1.2,
          f"|OQ′|={dist(O, Q2):.3f}")
    ck.ok("もし円上ならPを含む側の弧ABに対する円周角=(360°-100°)÷2=130°≠50°",
          abs((360 - angle_deg(O, A, B)) / 2 - 130) < 1e-9)

    cv = Canvas(360, 420)
    cv.s, cv.ox, cv.oy = 88, 180, 120
    cv.circle(O, 1.0)                        # A・B・Pを通る円は実線
    ext1, ext2 = lerp(A, B, -0.35), lerp(A, B, 1.35)
    cv.line(ext1, ext2, w=MAIN_W)
    for p in (P, Q2):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1)
    for p, nm in [(A, "A"), (B, "B"), (P, "P")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.dot(Q2)
    x, y = cv.P(Q2)
    cv.text_px(x, y + 22, "Q′", size=FS, anchor="middle", weight="bold")
    ang_label(cv, P, A, B, "50°", r_px=30)
    ang_label(cv, Q2, A, B, "50°", r_px=32)
    cv.text_px(180, 384, "Q′は直線ABの反対側——同じ50°でも，A・B・Pの円には乗らない",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 402, "（「同じ側」の条件を落とすと定理は壊れる）",
               size=FS_CAP, anchor="middle")
    return dict(file="L05_fig2_counterexample_opposite_side.svg", canvas=cv, lesson="L05",
                title="反例——反対側のQ′は円に乗らない",
                intent="主概念2の反例図。Q′が円の外にあることがはっきり分かる配置",
                params="A=220°,B=320°,P=90°,Q′=Pの直線AB折り返し（|OQ′|≈2.29）",
                checks=ck.items, check_tokens=["130°"], counts={"50°": 3})


def fig_L05_3():
    """L05図3（本文46行目・例題1）: 四角形で判定（40°・40°）"""
    # --- パラメータ（lesson_05.md 例題1・例題2連続: 弧AB=80°・弧DC=50°の共円配置） ---
    aA, aB, aC, aD = 230.0, 310.0, 65.0, 115.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)

    ck = Checker()
    ck.ang("∠ACB=40°（与件）", Cp, A, B, 40.0)
    ck.ang("∠ADB=40°（与件）", D, A, B, 40.0)
    ck.ok("C・Dは直線ABの同じ側（上側）", same_side(A, B, Cp, D))
    ck.ang("例題2整合: ∠DAC=25°（続きの与件——この図には書かない）", A, D, Cp, 25.0)
    ck.ang("例題2整合: ∠DBC=25°（続きの答え——図に書かない）", B, D, Cp, 25.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 98, 180, 134
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.angle_arc(Cp, A, B, n=1)
    cv.angle_arc(D, A, B, n=1)
    ang_label(cv, Cp, A, B, "40°", r_px=34)
    ang_label(cv, D, A, B, "40°", r_px=34)
    cv.text_px(180, 294, "∠ACB＝∠ADB。C・Dは直線ABの同じ側にある",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（例題1: 4点は一つの円周上にあるといえるか。円は描かない）",
               size=FS_CAP, anchor="middle")
    return dict(file="L05_fig3_example_judge_concyclic.svg", canvas=cv, lesson="L05 例題1・2",
                title="一つの円周上にあるか判定する（40°・40°）",
                intent="例題1の図（例題2の設定とも幾何整合）。円は描かない",
                params="円周上の配置(度): A230・B310・C65・D115（弧AB=80°・弧DCの値は答え直結のため非表示）",
                checks=ck.items, check_tokens=["25°", "50°"], counts={"40°": 2})


def fig_L05_4():
    """L05図4（本文80〜82行目 練習1(ア)(イ)(ウ)の3パネル統合）"""
    ck = Checker()
    cv = Canvas(660, 296)
    cv.s = 62

    def draw_panel(ox, A, B, Cp, D, labC, labD, capt, dashedD=False):
        cv.ox, cv.oy = ox, 118
        ext1, ext2 = lerp(A, B, -0.3), lerp(A, B, 1.3)
        cv.line(ext1, ext2, w=MAIN_W)
        for p in (Cp, D):
            cv.line(p, A, w=MAIN_W)
            cv.line(p, B, w=MAIN_W)
            cv.angle_arc(p, A, B, n=1, r=10)
        for p, nm, dy in [(A, "A", 16), (B, "B", 16)]:
            cv.dot(p)
            x, y = cv.P(p)
            cv.text_px(x - 4, y + dy, nm, size=FS_CAP, anchor="middle", weight="bold")
        for p, nm in [(Cp, "C"), (D, "D")]:
            cv.dot(p)
            x, y = cv.P(p)
            up = -8 if p[1] > A[1] else 20
            cv.text_px(x, y + up, nm, size=FS_CAP, anchor="middle", weight="bold")
        ang_label(cv, Cp, A, B, labC, r_px=23, size=11)
        ang_label(cv, D, A, B, labD, r_px=23, size=11)
        cv.text_px(ox, 258, capt, size=FS_CAP, anchor="middle", weight="bold")

    # (ア) 同じ側・50°＝50°
    A, B = C(220.0), C(320.0)
    Ca, Da = C(95.0), C(145.0)
    ck.ang("(ア) ∠ACB=50°", Ca, A, B, 50.0)
    ck.ang("(ア) ∠ADB=50°", Da, A, B, 50.0)
    ck.ok("(ア) C・Dは同じ側", same_side(A, B, Ca, Da))
    draw_panel(112, A, B, Ca, Da, "50°", "50°", "(ア) 同じ側")

    # (イ) 同じ側・48°≠50°: Cは48°の見込み円上にとる
    R48 = dist(A, B) / (2 * math.sin(math.radians(48)))
    cy48 = A[1] + math.sqrt(R48 ** 2 - (dist(A, B) / 2) ** 2)
    Cb = (R48 * math.cos(math.radians(70)), cy48 + R48 * math.sin(math.radians(70)))
    Db = C(140.0)
    ck.ang("(イ) ∠ACB=48°（Dの50°と等しくない）", Cb, A, B, 48.0)
    ck.ang("(イ) ∠ADB=50°", Db, A, B, 50.0)
    ck.ok("(イ) C・Dは同じ側", same_side(A, B, Cb, Db))
    draw_panel(330, A, B, Cb, Db, "48°", "50°", "(イ) 同じ側・角がちがう")

    # (ウ) 反対側・50°＝50°: Dは上側の点（配置角150°）の直線AB折り返し
    Cc = C(90.0)
    Dc = (C(150.0)[0], 2 * A[1] - C(150.0)[1])
    ck.ang("(ウ) ∠ACB=50°", Cc, A, B, 50.0)
    ck.ang("(ウ) ∠ADB=50°", Dc, A, B, 50.0)
    ck.ok("(ウ) C・Dは反対側", not same_side(A, B, Cc, Dc))
    draw_panel(548, A, B, Cc, Dc, "50°", "50°", "(ウ) 反対側")

    cv.text_px(330, 284, "練習1: それぞれ，4点A・B・C・Dは一つの円周上にあるといえるか",
               size=FS_CAP, anchor="middle")
    return dict(file="L05_fig4_practice_three_cases.svg", canvas=cv, lesson="L05 練習1",
                title="練習1（ア）（イ）（ウ）の3パネル",
                intent="逆の条件2つ（同じ側・等角）の判定練習。円は描かない",
                params="(ア)50°/50°同側／(イ)48°/50°同側／(ウ)50°/50°反対側",
                checks=ck.items, counts={"50°": 5, "48°": 1})


def fig_L05_5():
    """L05図5（本文83行目・練習2）: 四角形で判定→等角の収穫（35°・35°・28°）"""
    # --- パラメータ（lesson_05.md 練習2: 弧BC=70°・弧AD=56°の共円配置） ---
    aA, aB, aC, aD = 230.0, 310.0, 20.0, 174.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)

    ck = Checker()
    ck.ang("∠BAC=35°（与件）", A, B, Cp, 35.0)
    ck.ang("∠BDC=35°（与件）", D, B, Cp, 35.0)
    ck.ang("∠ABD=28°（与件）", B, A, D, 28.0)
    ck.ok("A・Dは直線BCの同じ側（判定に使う2点）", same_side(B, Cp, A, D))
    ck.ang("∠ACD=28°（(2)の答え——図に書かない・同弧AD）", Cp, A, D, 28.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 98, 180, 138
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.angle_arc(A, B, Cp, n=1)
    cv.angle_arc(D, B, Cp, n=1)
    cv.angle_arc(B, A, D, n=2)
    ang_label(cv, A, B, Cp, "35°", r_px=34, size=FS_CAP)
    ang_label(cv, D, B, Cp, "35°", r_px=34, size=FS_CAP)
    ang_label(cv, B, A, D, "28°", r_px=42, size=FS_CAP)
    cv.text_px(180, 294, "∠BAC＝∠BDC（線分BCを見込む2つの角）——円は描かない",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（練習2: (1)一つの円周上にあるといえる理由 (2)∠ACDを求める）",
               size=FS_CAP, anchor="middle")
    return dict(file="L05_fig5_practice_judge_harvest.svg", canvas=cv, lesson="L05 練習2",
                title="判定→等角の収穫（35°・35°・28°）",
                intent="練習2の図。2段コンボ（逆で円→定理(2)で収穫）の判定素材",
                params="A=230°,B=310°,C=20°,D=174°（弧BC=70°・弧AD=56°）",
                checks=ck.items, counts={"35°": 2, "28°": 1})


# ===========================================================================
# L06 接線の作図
# ===========================================================================
def fig_L06_1():
    """L06図1（本文30行目）: 課題の図——円Oと外部の点P（接線はまだ描かない）"""
    # --- パラメータ（lesson_06.md 主概念1: OP=半径の約2.5倍・P右やや上） ---
    k, p_dir = 2.5, 20.0
    P = C(p_dir, k)

    ck = Checker()
    ck.ok("OP=半径の2.5倍", abs(dist(O, P) - k) < 1e-12, f"|OP|={dist(O, P):.2f}")
    ck.ok("Pは円Oの外部", dist(O, P) > 1.0)

    cv = Canvas(380, 260)
    cv.s, cv.ox, cv.oy = 76, 95, 122
    cv.circle(O, 1.0)
    o_label(cv, dir_deg=250, dist_px=13)
    cv.dot(P)
    x, y = cv.P(P)
    cv.text_px(x + 14, y + 4, "P", size=FS, anchor="middle", weight="bold")
    cv.text_px(190, 216, "円Oと，その外部の点P——Pを通る円Oの接線を引きたい",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 234, "（接点の位置はまだ分からない。どう作図する？）",
               size=FS_CAP, anchor="middle")
    return dict(file="L06_fig1_tangent_problem_setup.svg", canvas=cv, lesson="L06",
                title="課題——円外の点Pから接線を引く（接線は未記入）",
                intent="主概念1の課題提示図。円Oと点Pのみ",
                params="半径1・OP=2.5（方向20°）",
                checks=ck.items, check_tokens=["°"])


def fig_L06_2():
    """L06図2（本文44行目）: 接線の作図の完成図"""
    # --- パラメータ（lesson_06.md 手順①〜④: OP=半径の2.5倍） ---
    k = 2.5
    P = (k, 0.0)
    M = (k / 2, 0.0)
    # 円O(r=1)と円M(r=k/2)の交点A・B（厳密解）
    ax = 1.0 / k
    ay = math.sqrt(1 - ax * ax)
    A, B = (ax, ay), (ax, -ay)

    ck = Checker()
    ck.ok("MはOPの中点", abs(dist(O, M) - dist(M, P)) < 1e-12)
    ck.ok("A・Bは円O上", abs(dist(O, A) - 1) < 1e-12 and abs(dist(O, B) - 1) < 1e-12)
    ck.ok("A・BはOPを直径とする円（円M）上",
          abs(dist(M, A) - k / 2) < 1e-12 and abs(dist(M, B) - k / 2) < 1e-12)
    ck.ang("∠OAP=90°（半円の弧に対する円周角→接線⊥半径）", A, O, P, 90.0)
    ck.ang("∠OBP=90°（同上）", B, O, P, 90.0)

    cv = Canvas(400, 330)
    cv.s, cv.ox, cv.oy = 80, 92, 138
    cv.circle(M, k / 2, w=AUX_W, dash=DASH)   # 手順②の円（破線）
    cv.circle(O, 1.0)
    cv.line(O, P, w=AUX_W)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    cv.line(lerp(P, A, 1.25), P, w=MAIN_W)    # 接線PA（Aの先まで）
    cv.line(lerp(P, B, 1.25), P, w=MAIN_W)    # 接線PB
    cv.right_angle(A, O, P)
    cv.right_angle(B, O, P)
    for p, nm, (dx, dy) in [(A, "A", (-4, -12)), (B, "B", (-4, 20)),
                            (P, "P", (16, 4)), (M, "M", (2, 20))]:
        cv.dot(p)
        x, y = cv.P(p)
        cv.text_px(x + dx, y + dy, nm, size=FS, anchor="middle", weight="bold")
    o_label(cv, dir_deg=200, dist_px=14)
    cv.text_px(200, 296, "OPの中点Mを中心に，OPを直径とする円（破線）をかく",
               size=FS_CAP, anchor="middle")
    cv.text_px(200, 314, "（円Oとの交点A・Bが接点。直線PA・PBが求める接線）",
               size=FS_CAP, anchor="middle")
    return dict(file="L06_fig2_tangent_construction.svg", canvas=cv, lesson="L06",
                title="接線の作図の完成図（OP=半径の2.5倍）",
                intent="手順①〜④の完成図。補助円は破線・直角の印のみ（数値なし）",
                params="半径1・OP=2.5・接点A,B=(0.4,±√0.84)（2円の交点の厳密解）",
                checks=ck.items, check_tokens=["°"])


def fig_L06_3():
    """L06図3（本文59行目）: さしがね型——丸太の直径を測る"""
    # --- パラメータ（lesson_06.md 主概念2: 頂点の角90°・CDは中心を通る） ---
    aV, aC, aD = 130.0, 220.0, 40.0
    V, Cp, D = C(aV), C(aC), C(aD)

    ck = Checker()
    ck.ang("さしがねの角=90°（直角の印のみ）", V, Cp, D, 90.0)
    ck.ok("CDは中心を通る配置（90°の円周角の弦）", abs(cross2(Cp, D, O)) < 1e-9)
    ck.ok("C・Dは円周上", abs(dist(O, Cp) - 1) < 1e-12 and abs(dist(O, D) - 1) < 1e-12)

    cv = Canvas(380, 330)
    cv.s, cv.ox, cv.oy = 96, 190, 136
    cv.circle(O, 1.0)   # 丸太の断面（中心の印なし）
    # さしがね（L字型・角の外側に沿わせたグレーの太帯）
    offs = []
    for target in (Cp, D):
        L_ = dist(V, target)
        u = ((target[0] - V[0]) / L_, (target[1] - V[1]) / L_)
        n = (-u[1], u[0])
        if (V[0] - O[0]) * n[0] + (V[1] - O[1]) * n[1] < 0:   # 外向き（Oと反対）へ
            n = (-n[0], -n[1])
        offs.append((u, n))
    (u1, n1), (u2, n2) = offs
    w_ = 0.07
    p1 = (V[0] + u1[0] * 1.3 + n1[0] * w_, V[1] + u1[1] * 1.3 + n1[1] * w_)
    pc = (V[0] + (n1[0] + n2[0]) * w_, V[1] + (n1[1] + n2[1]) * w_)
    p2 = (V[0] + u2[0] * 1.45 + n2[0] * w_, V[1] + u2[1] * 1.45 + n2[1] * w_)
    pts_px = " ".join(f"{x:.1f},{y:.1f}" for x, y in map(cv.P, [p1, pc, p2]))
    cv.raw(f'<polyline points="{pts_px}" fill="none" stroke="#aaa" '
           f'stroke-width="8" stroke-linejoin="round"/>')
    cv.line(V, Cp, w=AUX_W, dash=DASH)
    cv.line(V, D, w=AUX_W, dash=DASH)
    cv.line(Cp, D, w=BOLD_W)   # 測る弦CD
    cv.right_angle(V, Cp, D)
    for p, nm in [(Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.dot(V)
    x, y = cv.P(V)
    cv.text_px(x - 8, y - 12, "さしがね（直角）", size=FS_CAP, anchor="end")
    cv.text_px(190, 296, "丸太の断面。直角の頂点を円周上に当て，交点C・Dを結ぶ",
               size=FS_CAP, anchor="middle")
    cv.text_px(190, 314, "（中心の印はない——それでもCDを測ればよい理由は？）",
               size=FS_CAP, anchor="middle")
    return dict(file="L06_fig3_carpenter_square_log.svg", canvas=cv, lesson="L06",
                title="さしがね型——丸太の直径の見積もり",
                intent="主概念2の活用図。90°の円周角の弦CD（中心の印なし・太線）",
                params="V=130°,C=220°,D=40°（C・Dは対心＝CDは中心を通る）",
                checks=ck.items, check_tokens=["°"])


# ===========================================================================
# L07 総合演習
# ===========================================================================
def fig_L07_1():
    """L07図1（本文34行目・例題1）: 弦の交点のまわりの角（40°・48°→x）"""
    # --- パラメータ（lesson_07.md 例題1: ∠ADB=40°→弧AB=80°, ∠DBC=48°→弧DC=96°） ---
    aA, aB, aC, aD = 125.0, 205.0, 320.0, 56.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    E = line_int(A, Cp, B, D)

    ck = Checker()
    ck.ang("∠ADB=40°（与件）→弧AB=80°", D, A, B, 40.0)
    ck.ang("弧AB中心角=80°", O, A, B, 80.0)
    ck.ang("∠DBC=48°（与件）→弧DC=96°", B, D, Cp, 48.0)
    ck.ang("∠ACB=40°（同弧AB——解答の途中・図に書かない）", Cp, A, B, 40.0)
    ck.ang("x=∠AEB=88°=40°+48°（答え——図に書かない）", E, A, B, 88.0)
    ck.ok("Eは円の内部", dist(O, E) < 1.0, f"|OE|={dist(O, E):.3f}")

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 98, 180, 136
    cv.circle(O, 1.0)
    cv.line(A, Cp, w=MAIN_W)
    cv.line(B, D, w=MAIN_W)
    cv.line(A, D, w=MAIN_W)
    cv.line(B, Cp, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.dot(E)
    x, y = cv.P(E)
    cv.text_px(x + 4, y + 18, "E", size=FS, anchor="middle", weight="bold")
    cv.angle_arc(D, A, B, n=1)
    cv.angle_arc(B, D, Cp, n=2)
    cv.angle_arc(E, A, B, n=1, r=11)
    ang_label(cv, D, A, B, "40°", r_px=30)
    ang_label(cv, B, D, Cp, "48°", r_px=30)
    ang_label(cv, E, A, B, "x", r_px=24)
    cv.text_px(180, 294, "弦ACとBDが円の内部の点Eで交わる——∠AEB＝x",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（例題1: 円周角の定理＋三角形の外角の合わせ技）",
               size=FS_CAP, anchor="middle")
    return dict(file="L07_fig1_example_chord_intersection.svg", canvas=cv, lesson="L07 例題1",
                title="弦の交点のまわりの角（40°・48°→x）",
                intent="例題1の図。与件2つとxのみ・解答の値（与件の角の和）は書かない",
                params="A=125°,B=205°,C=320°,D=56°（弧AB=80°・弧DC=96°）",
                checks=ck.items, check_tokens=["88°"], counts={"40°": 1, "48°": 1})


def fig_L07_2():
    """L07図2（本文47行目・例題2）: 等しい弧には等しい円周角（27°→x）"""
    # --- パラメータ（lesson_07.md 例題2: 弧BC=弧CD（各54°）・∠BAC=27°） ---
    aA, aB, aC, aD = 120.0, 270.0, 324.0, 18.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)

    ck = Checker()
    ck.ang("弧BC中心角=54°", O, B, Cp, 54.0)
    ck.ang("弧CD中心角=54°（弧BC=弧CD）", O, Cp, D, 54.0)
    ck.ang("∠BAC=27°（与件）", A, B, Cp, 27.0)
    ck.ang("x=∠CAD=27°（答え——図に書かない）", A, Cp, D, 27.0)
    ck.ang("∠BAD=54°（2つ分の確認）", A, B, D, 54.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 98, 180, 136
    cv.arc(O, 1.0, aB, aC, w=6, color=ARC_HL)
    cv.arc(O, 1.0, aC, aD + 360.0, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (B, Cp, D):
        cv.line(A, p, w=MAIN_W)
    arc_ticks(cv, (aB + aC) / 2, n=1)                    # 弧BCの等号マーク
    arc_ticks(cv, (aC + aD + 360.0) / 2, n=1)            # 弧CDの等号マーク
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=90, dist_px=13)
    cv.angle_arc(A, B, Cp, n=1, r=13)
    cv.angle_arc(A, Cp, D, n=1, r=18)
    ang_label(cv, A, B, Cp, "27°", r_px=54)
    ang_label(cv, A, Cp, D, "x", r_px=80)
    cv.text_px(180, 294, "弧BCと弧CDの長さが等しい（同じ印）——∠CAD＝x",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（例題2: 等しい弧→等しい中心角→円周角も等しい）",
               size=FS_CAP, anchor="middle")
    return dict(file="L07_fig2_example_equal_arcs.svg", canvas=cv, lesson="L07 例題2",
                title="等しい弧に等しい円周角（27°→x）",
                intent="例題2の図。等弧マーク（弧を横切る短線）で弧BC=弧CDを表示",
                params="A=120°,B=270°,C=324°,D=18°（弧BC=弧CD=54°）",
                checks=ck.items, counts={"27°": 1})


def fig_L07_3():
    """L07図3（本文62行目・例題3）: 逆で円を出してから収穫（52°・52°・31°→x）"""
    # --- パラメータ（lesson_07.md 例題3: 弧BC=104°・弧AD=62°の共円配置・円は描かない） ---
    aA, aB, aC, aD = 230.0, 310.0, 54.0, 168.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)

    ck = Checker()
    ck.ang("∠BAC=52°（与件）", A, B, Cp, 52.0)
    ck.ang("∠BDC=52°（与件）", D, B, Cp, 52.0)
    ck.ang("∠ACD=31°（与件）", Cp, A, D, 31.0)
    ck.ok("A・Dは直線BCの同じ側（逆の条件）", same_side(B, Cp, A, D))
    ck.ang("x=∠ABD=31°（答え——出現1回に固定・同弧AD）", B, A, D, 31.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 98, 180, 138
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.angle_arc(A, B, Cp, n=1)
    cv.angle_arc(D, B, Cp, n=1)
    cv.angle_arc(Cp, A, D, n=2)
    ang_label(cv, A, B, Cp, "52°", r_px=30, size=FS_CAP)
    ang_label(cv, D, B, Cp, "52°", r_px=30, size=FS_CAP)
    ang_label(cv, Cp, A, D, "31°", r_px=32, size=FS_CAP)
    ang_label(cv, B, A, D, "x", r_px=30)
    cv.text_px(180, 294, "∠BAC＝∠BDC——まず円を出現させ，次に∠ABD＝xを収穫する",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（例題3: 円は描かれていない。2段コンボの型）",
               size=FS_CAP, anchor="middle")
    return dict(file="L07_fig3_example_converse_harvest.svg", canvas=cv, lesson="L07 例題3",
                title="逆→収穫の2段コンボ（52°・52°・31°→x）",
                intent="例題3の図。円なし四角形＋対角線・答えの値は図に置かない（与件の表示回数は機械検査で固定）",
                params="A=230°,B=310°,C=54°,D=168°（弧BC=104°・弧AD=62°）",
                checks=ck.items, counts={"52°": 2, "31°": 1})


def fig_L07_4():
    """L07図4（本文85〜88行目 練習1〜4の4パネル統合・2×2）"""
    ck = Checker()
    cv = Canvas(560, 600)
    cv.s = 88

    # --- パネル1（練習1）: 交点の角 36°・44°→x ---
    aA, aB, aC, aD = 125.0, 197.0, 320.0, 48.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    E = line_int(A, Cp, B, D)
    ck.ang("練習1: ∠ADB=36°（与件）", D, A, B, 36.0)
    ck.ang("練習1: ∠DBC=44°（与件）", B, D, Cp, 44.0)
    ck.ang("練習1: x=∠AEB=80°（答え——図に書かない）", E, A, B, 80.0)
    ck.ok("練習1: Eは円の内部", dist(O, E) < 1.0)
    cv.ox, cv.oy = 140, 128
    cv.circle(O, 1.0)
    for p, q in [(A, Cp), (B, D), (A, D), (B, Cp)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    cv.dot(E)
    x, y = cv.P(E)
    cv.text_px(x + 4, y + 17, "E", size=FS_CAP, anchor="middle", weight="bold")
    cv.angle_arc(D, A, B, n=1, r=12)
    cv.angle_arc(B, D, Cp, n=2, r=12)
    ang_label(cv, D, A, B, "36°", r_px=27, size=FS_CAP)
    ang_label(cv, B, D, Cp, "44°", r_px=27, size=FS_CAP)
    ang_label(cv, E, A, B, "x", r_px=21, size=FS_CAP)
    cv.text_px(140, 254, "練習1", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル2（練習2）: 等しい弧 24°→x=∠BAD ---
    aA, aB, aC, aD = 120.0, 270.0, 318.0, 6.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    ck.ang("練習2: 弧BC=弧CD（中心角48°ずつ）", O, B, Cp, 48.0)
    ck.ang("練習2: 弧CD中心角=48°", O, Cp, D, 48.0)
    ck.ang("練習2: ∠BAC=24°（与件）", A, B, Cp, 24.0)
    ck.ang("練習2: x=∠BAD=48°（答え——図に書かない）", A, B, D, 48.0)
    cv.ox, cv.oy = 415, 128
    cv.arc(O, 1.0, aB, aC, w=6, color=ARC_HL)
    cv.arc(O, 1.0, aC, aD + 360.0, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (B, Cp, D):
        cv.line(A, p, w=MAIN_W)
    arc_ticks(cv, (aB + aC) / 2, n=1)
    arc_ticks(cv, (aC + aD + 360.0) / 2, n=1)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=90, dist_px=12)
    cv.angle_arc(A, B, Cp, n=1, r=12)
    cv.angle_arc(A, B, D, n=1, r=19)
    ang_label(cv, A, B, Cp, "24°", r_px=46, size=FS_CAP)
    ang_label(cv, A, B, D, "x", r_px=56, size=FS_CAP)
    cv.text_px(415, 254, "練習2（弧BC＝弧CD）", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル3（練習3）: OA=OB・∠OAB=28°→∠ACB=x ---
    aA, aB, aC = 208.0, 332.0, 90.0
    A, B, Cp = C(aA), C(aB), C(aC)
    ck.ang("練習3: ∠OAB=28°（与件・二等辺の底角）", A, O, B, 28.0)
    ck.ang("練習3: 中心角∠AOB=124°（途中の答え——図に書かない）", O, A, B, 124.0)
    ck.ang("練習3: x=∠ACB=62°（答え——図に書かない）", Cp, A, B, 62.0)
    cv.ox, cv.oy = 140, 420
    cv.arc(O, 1.0, aA, aB, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    cv.line(Cp, A, w=MAIN_W)
    cv.line(Cp, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=45, dist_px=13)
    cv.angle_arc(A, O, B, n=1, r=12)
    cv.angle_arc(Cp, A, B, n=1, r=12)
    ang_label(cv, A, O, B, "28°", r_px=40, size=FS_CAP)
    ang_label(cv, Cp, A, B, "x", r_px=24, size=FS_CAP)
    cv.text_px(140, 546, "練習3（OA＝OB）", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル4（練習4）: 逆→収穫 65°・65°・18°→x（弧AB=130°・弧DC=36°） ---
    aA, aB, aC, aD = 205.0, 335.0, 62.0, 98.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    ck.ang("練習4: ∠ACB=65°（与件）", Cp, A, B, 65.0)
    ck.ang("練習4: ∠ADB=65°（与件）", D, A, B, 65.0)
    ck.ang("練習4: ∠DAC=18°（与件）", A, D, Cp, 18.0)
    ck.ok("練習4: C・Dは直線ABの同じ側", same_side(A, B, Cp, D))
    ck.ang("練習4: x=∠DBC=18°（答え——出現1回に固定・同弧DC）", B, D, Cp, 18.0)
    cv.ox, cv.oy = 415, 420
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    cv.angle_arc(Cp, A, B, n=1, r=12)
    cv.angle_arc(D, A, B, n=1, r=12)
    cv.angle_arc(A, D, Cp, n=2, r=12)
    ang_label(cv, Cp, A, B, "65°", r_px=30, size=FS_CAP)
    ang_label(cv, D, A, B, "65°", r_px=30, size=FS_CAP)
    ang_label(cv, A, D, Cp, "18°", r_px=44, size=FS_CAP)
    ang_label(cv, B, D, Cp, "x", r_px=40, size=FS_CAP)
    cv.text_px(415, 546, "練習4（円は描かれていない）", size=FS_CAP,
               anchor="middle", weight="bold")

    cv.text_px(280, 578, "練習1〜4: どの道具（定理(1)(2)・外角・等しい弧・逆）が使える形かを読み取る",
               size=FS_CAP, anchor="middle")
    return dict(file="L07_fig4_practice_1_to_4.svg", canvas=cv, lesson="L07 練習1〜4",
                title="練習1〜4（2×2の4パネル統合）",
                intent="総合演習の練習4題。答えの角度・途中の中心角は図に置かない",
                params="P1: 弧AB=72°/弧DC=88°／P2: 等弧（作図値は答え直結のため非表示）×2／P3: ∠OAB=28°／P4: 弧AB=130°/弧DC=36°",
                checks=ck.items, check_tokens=["80°", "48°", "62°", "124°"],
                counts={"36°": 1, "44°": 1, "24°": 1, "28°": 1, "65°": 2, "18°": 1})


def fig_L07_5():
    """L07図5（本文93行目・stretch S1）: 円周角×相似の証明図（数値なし）"""
    # --- パラメータ（lesson_07.md stretch: 例題1と同型・記号のみ） ---
    aA, aB, aC, aD = 125.0, 205.0, 320.0, 56.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    E = line_int(A, Cp, B, D)

    ck = Checker()
    ck.ok("Eは円の内部（弦AC・BDの交点）", dist(O, E) < 1.0)
    ck.ang("∠AED=∠BEC（対頂角——証明の材料①）", E, A, D,
           angle_deg(E, B, Cp))
    ck.ok("∠DAC=∠CBD（同弧DC——証明の材料②）",
          abs(angle_deg(A, D, Cp) - angle_deg(B, Cp, D)) < 1e-9,
          f"ともに{angle_deg(A, D, Cp):.1f}°")

    cv = Canvas(360, 318)
    cv.s, cv.ox, cv.oy = 98, 180, 136
    cv.circle(O, 1.0)
    for p, q in [(A, Cp), (B, D), (A, D), (B, Cp)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    cv.dot(E)
    x, y = cv.P(E)
    cv.text_px(x + 4, y + 18, "E", size=FS, anchor="middle", weight="bold")
    cv.text_px(180, 282, "弦ACとBDが円の内部の点Eで交わる",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 300, "（stretch: △AED∽△BECを証明する——等しい角の組を2つ探す）",
               size=FS_CAP, anchor="middle")
    return dict(file="L07_fig5_stretch_similar_triangles.svg", canvas=cv,
                lesson="L07 stretch S1",
                title="円周角×相似の証明図（記号のみ）",
                intent="stretchの図。角度数値なし・証明対象の2三角形が見える構図",
                params="A=125°,B=205°,C=320°,D=56°（例題1と同型）",
                checks=ck.items, check_tokens=["°"])


# ===========================================================================
# L08 章末まとめ
# ===========================================================================
def fig_L08_1():
    """L08図1（本文41行目・例題1）: 道具を乗り継ぐ（直径AB・∠DBA=34°）"""
    # --- パラメータ（lesson_08.md 例題1: 弧AC=40°・弧CD=28°・弧DB=112°） ---
    aA, aB = 180.0, 0.0
    aC, aD = 140.0, 112.0     # A側から40°・さらに28°（残りDB=112°）
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)

    ck = Checker()
    ck.ok("ABは直径", abs(cross2(A, B, O)) < 1e-12)
    ck.ang("弧AC中心角=40°", O, A, Cp, 40.0)
    ck.ang("弧CD中心角=28°", O, Cp, D, 28.0)
    ck.ang("弧DB中心角=112°", O, D, B, 112.0)
    ck.ang("∠DBA=34°（与件・弧ADの半分=68°÷2）", B, D, A, 34.0)
    ck.ang("(1) ∠ADB=90°（答え——図に書かない）", D, A, B, 90.0)
    ck.ang("(2) ∠DAB=56°（答え——図に書かない）", A, D, B, 56.0)
    ck.ang("(3) ∠DCB=56°（答え——図に書かない・同弧DB）", Cp, D, B, 56.0)

    cv = Canvas(360, 330)
    cv.s, cv.ox, cv.oy = 98, 180, 136
    cv.circle(O, 1.0)
    cv.line(A, B, w=MAIN_W)   # 直径
    for p, q in [(A, D), (B, D), (Cp, D), (Cp, B)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=250, dist_px=13)
    cv.angle_arc(B, D, A, n=1)
    ang_label(cv, B, D, A, "34°", r_px=32)
    cv.text_px(180, 294, "ABは円Oの直径——(1)∠ADB (2)∠DAB (3)∠DCB を順に求める",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 312, "（例題1: 半円の弧→内角の和→同じ弧，と道具を乗り継ぐ）",
               size=FS_CAP, anchor="middle")
    return dict(file="L08_fig1_example_tool_relay.svg", canvas=cv, lesson="L08 例題1",
                title="道具を乗り継ぐ（直径AB・∠DBA=34°）",
                intent="例題1の図。与件34°のみ・弧AC/CD/DBの配置は本文指定どおり",
                params="A=180°,B=0°,C=140°,D=112°（弧AC=40°・弧CD=28°・弧DB=112°）",
                checks=ck.items, check_tokens=["90°", "56°"], counts={"34°": 1})


def fig_L08_2():
    """L08図2（本文82〜84行目 練習2・3・4の3パネル統合）"""
    ck = Checker()
    cv = Canvas(660, 300)
    cv.s = 70

    # --- パネル1（練習2）: 同弧等角 57°→x ---
    aA, aB, aC, aD = 213.0, 327.0, 115.0, 65.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    ck.ang("練習2: ∠ACB=57°（与件）", Cp, A, B, 57.0)
    ck.ang("練習2: x=∠ADB=57°（答え——出現1回に固定・同弧AB）", D, A, B, 57.0)
    ck.ang("練習2: 弧AB中心角=114°=2×57°", O, A, B, 114.0)
    cv.ox, cv.oy = 112, 108
    cv.arc(O, 1.0, aA, aB, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    for p in (Cp, D):
        cv.line(p, A, w=MAIN_W)
        cv.line(p, B, w=MAIN_W)
        cv.angle_arc(p, A, B, n=1, r=11)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    ang_label(cv, Cp, A, B, "57°", r_px=24, size=FS_CAP)
    ang_label(cv, D, A, B, "x", r_px=24, size=FS_CAP)
    cv.text_px(112, 216, "練習2", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル2（練習3）: 直径AB・∠CAB=37° ---
    aA, aB, aC = 180.0, 0.0, 74.0
    A, B, Cp = C(aA), C(aB), C(aC)
    ck.ok("練習3: ABは直径", abs(cross2(A, B, O)) < 1e-12)
    ck.ang("練習3: ∠CAB=37°（与件）", A, Cp, B, 37.0)
    ck.ang("練習3: ∠ACB=90°（答え——図は？のみ）", Cp, A, B, 90.0)
    ck.ang("練習3: ∠CBA=53°（答え——図は？のみ）", B, Cp, A, 53.0)
    cv.ox, cv.oy = 330, 108
    cv.circle(O, 1.0)
    cv.polygon([A, B, Cp], w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=250, dist_px=12)
    cv.angle_arc(A, Cp, B, n=1, r=11)
    ang_label(cv, A, Cp, B, "37°", r_px=24, size=FS_CAP)
    ang_label(cv, Cp, A, B, "？", r_px=21, size=FS_CAP)
    ang_label(cv, B, Cp, A, "？", r_px=21, size=FS_CAP)
    cv.text_px(330, 216, "練習3（ABは直径）", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル3（練習4）: OA=OB・∠OAB=31°→∠APB=x ---
    aA, aB, aP = 211.0, 329.0, 90.0
    A, B, P = C(aA), C(aB), C(aP)
    ck.ang("練習4: ∠OAB=31°（与件・二等辺の底角）", A, O, B, 31.0)
    ck.ang("練習4: 中心角∠AOB=118°（途中の答え——図に書かない）", O, A, B, 118.0)
    ck.ang("練習4: x=∠APB=59°（答え——図に書かない）", P, A, B, 59.0)
    cv.ox, cv.oy = 548, 108
    cv.arc(O, 1.0, aA, aB, w=6, color=ARC_HL)
    cv.circle(O, 1.0)
    cv.line(O, A, w=MAIN_W)
    cv.line(O, B, w=MAIN_W)
    cv.line(P, A, w=MAIN_W)
    cv.line(P, B, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (P, "P")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    o_label(cv, dir_deg=90, dist_px=13)
    cv.angle_arc(A, O, B, n=1, r=11)
    cv.angle_arc(P, A, B, n=1, r=11)
    ang_label(cv, A, O, B, "31°", r_px=40, size=FS_CAP)
    ang_label(cv, P, A, B, "x", r_px=24, size=FS_CAP)
    cv.text_px(548, 216, "練習4（OA＝OB）", size=FS_CAP, anchor="middle", weight="bold")

    cv.text_px(330, 252, "章末の混合練習——どの道具を使うかは自分で選ぶ",
               size=FS_CAP, anchor="middle")
    cv.text_px(330, 270, "（練習2: 同じ弧／練習3: 直径／練習4: 半径の二等辺三角形から）",
               size=FS_CAP, anchor="middle")
    return dict(file="L08_fig2_practice_2_3_4.svg", canvas=cv, lesson="L08 練習2〜4",
                title="練習2・3・4（3パネル統合）",
                intent="章末混合練習の基本3題。答え・途中の中心角は図に置かない",
                params="P2: 弧AB=114°／P3: ∠CAB=37°（C=74°）／P4: ∠OAB=31°（中心角は導出値のため非表示）",
                checks=ck.items, check_tokens=["90°", "53°", "59°", "118°"],
                counts={"57°": 1, "37°": 1, "31°": 1})


def fig_L08_3():
    """L08図3（本文85・86行目 練習5・6の2パネル統合）"""
    ck = Checker()
    cv = Canvas(560, 330)
    cv.s = 88

    # --- パネル1（練習5）: 交点の角 42°・39°→x ---
    aA, aB, aC, aD = 125.0, 209.0, 320.0, 38.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    E = line_int(A, Cp, B, D)
    ck.ang("練習5: ∠ADB=42°（与件）", D, A, B, 42.0)
    ck.ang("練習5: ∠DBC=39°（与件）", B, D, Cp, 39.0)
    ck.ang("練習5: x=∠AEB=81°（答え——図に書かない）", E, A, B, 81.0)
    ck.ok("練習5: Eは円の内部", dist(O, E) < 1.0)
    cv.ox, cv.oy = 140, 128
    cv.circle(O, 1.0)
    for p, q in [(A, Cp), (B, D), (A, D), (B, Cp)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    cv.dot(E)
    x, y = cv.P(E)
    cv.text_px(x + 4, y + 17, "E", size=FS_CAP, anchor="middle", weight="bold")
    cv.angle_arc(D, A, B, n=1, r=12)
    cv.angle_arc(B, D, Cp, n=2, r=12)
    ang_label(cv, D, A, B, "42°", r_px=27, size=FS_CAP)
    ang_label(cv, B, D, Cp, "39°", r_px=27, size=FS_CAP)
    ang_label(cv, E, A, B, "x", r_px=21, size=FS_CAP)
    cv.text_px(140, 258, "練習5", size=FS_CAP, anchor="middle", weight="bold")

    # --- パネル2（練習6）: 逆→収穫 58°・58°・21°→x（弧AB=116°・弧DC=42°） ---
    aA, aB, aC, aD = 212.0, 328.0, 60.0, 102.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    ck.ang("練習6: ∠ACB=58°（与件）", Cp, A, B, 58.0)
    ck.ang("練習6: ∠ADB=58°（与件）", D, A, B, 58.0)
    ck.ang("練習6: ∠DAC=21°（与件）", A, D, Cp, 21.0)
    ck.ok("練習6: C・Dは直線ABの同じ側", same_side(A, B, Cp, D))
    ck.ang("練習6: x=∠DBC=21°（答え——出現1回に固定・同弧DC）", B, D, Cp, 21.0)
    cv.ox, cv.oy = 415, 128
    for p, q in [(A, B), (B, Cp), (Cp, D), (D, A), (A, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm, dist_px=13)
    cv.angle_arc(Cp, A, B, n=1, r=12)
    cv.angle_arc(D, A, B, n=1, r=12)
    cv.angle_arc(A, D, Cp, n=2, r=12)
    ang_label(cv, Cp, A, B, "58°", r_px=30, size=FS_CAP)
    ang_label(cv, D, A, B, "58°", r_px=30, size=FS_CAP)
    ang_label(cv, A, D, Cp, "21°", r_px=44, size=FS_CAP)
    ang_label(cv, B, D, Cp, "x", r_px=40, size=FS_CAP)
    cv.text_px(415, 258, "練習6（円は描かれていない）", size=FS_CAP,
               anchor="middle", weight="bold")

    cv.text_px(280, 288, "練習5: 円周角＋外角の合わせ技／練習6: 逆で円を出してから収穫",
               size=FS_CAP, anchor="middle")
    cv.text_px(280, 306, "（使った定理を順番に言えるかも点検する）",
               size=FS_CAP, anchor="middle")
    return dict(file="L08_fig3_practice_5_6.svg", canvas=cv, lesson="L08 練習5・6",
                title="練習5・6（2パネル統合）",
                intent="章末混合練習の応用2題。答えの角度は図に置かない",
                params="P5: 弧AB=84°/弧DC=78°／P6: 弧AB=116°/弧DC=42°",
                checks=ck.items, check_tokens=["81°"],
                counts={"42°": 1, "39°": 1, "58°": 2, "21°": 1})


def fig_L08_4():
    """L08図4（本文92行目・stretch S1）: 直径×相似の融合証明図（数値なし）"""
    # --- パラメータ（lesson_08.md stretch: 弧AC=50°・弧CD=40°・弧DB=90°） ---
    aA, aB = 180.0, 0.0
    aC, aD = 130.0, 90.0
    A, B, Cp, D = C(aA), C(aB), C(aC), C(aD)
    E = line_int(A, D, B, Cp)

    ck = Checker()
    ck.ok("ABは直径", abs(cross2(A, B, O)) < 1e-12)
    ck.ang("弧AC中心角=50°", O, A, Cp, 50.0)
    ck.ang("弧CD中心角=40°", O, Cp, D, 40.0)
    ck.ang("弧DB中心角=90°", O, D, B, 90.0)
    ck.ang("∠ACB=90°（直径——証明の材料・図に書かない）", Cp, A, B, 90.0)
    ck.ang("∠ADB=90°（直径——証明の材料・図に書かない）", D, A, B, 90.0)
    ck.ok("∠DAC=∠CBD（同弧CD=40°の半分どうし）",
          abs(angle_deg(A, D, Cp) - 20.0) < 1e-9
          and abs(angle_deg(B, Cp, D) - 20.0) < 1e-9)
    ck.ok("Eは円の内部（弦AD・BCの交点）", dist(O, E) < 1.0)

    cv = Canvas(360, 318)
    cv.s, cv.ox, cv.oy = 98, 180, 136
    cv.circle(O, 1.0)
    cv.line(A, B, w=MAIN_W)   # 直径
    for p, q in [(A, Cp), (A, D), (B, Cp), (B, D)]:
        cv.line(p, q, w=MAIN_W)
    for p, nm in [(A, "A"), (B, "B"), (Cp, "C"), (D, "D")]:
        cv.dot(p)
        vertex_label(cv, p, nm)
    o_label(cv, dir_deg=250, dist_px=13)
    cv.dot(E)
    x, y = cv.P(E)
    cv.text_px(x + 12, y + 12, "E", size=FS, anchor="middle", weight="bold")
    cv.text_px(180, 282, "ABは円Oの直径。弦ADとBCが円の内部の点Eで交わる",
               size=FS_CAP, anchor="middle")
    cv.text_px(180, 300, "（stretch: △EAC∽△EBDを証明する——直径が供給する角を探す）",
               size=FS_CAP, anchor="middle")
    return dict(file="L08_fig4_stretch_diameter_similar.svg", canvas=cv,
                lesson="L08 stretch S1",
                title="直径×相似の融合証明図（記号のみ）",
                intent="stretchの図。弧AC=50°/CD=40°/DB=90°の本文指定配置・数値なし",
                params="A=180°,B=0°,C=130°,D=90°",
                checks=ck.items, check_tokens=["°"])


FIGS = [fig_L01_1, fig_L01_2, fig_L01_3,
        fig_L02_1, fig_L02_2, fig_L02_3, fig_L02_4, fig_L02_5, fig_L02_6, fig_L02_7,
        fig_L03_1, fig_L03_2, fig_L03_3, fig_L03_4, fig_L03_5,
        fig_L04_1, fig_L04_2,
        fig_L05_1, fig_L05_2, fig_L05_3, fig_L05_4, fig_L05_5,
        fig_L06_1, fig_L06_2, fig_L06_3,
        fig_L07_1, fig_L07_2, fig_L07_3, fig_L07_4, fig_L07_5,
        fig_L08_1, fig_L08_2, fig_L08_3, fig_L08_4]


# 図版配置対応表（2026-07-16統合・設計判断の記録）。
# 本文プレースホルダの改廃時はこの表も更新すること。
PLACEMENT_SECTION = [
    '## 図版配置対応表（プレースホルダ→ファイル/パネル）',
    '',
    '本文の【図: …】プレースホルダ**46箇所**と、`assets/` の図版**34枚**（SVG）の対応表（2026-07-16統合転記。以後は本表を正とする）。',
    '練習問題などの連続コマは**1ファイル内の複数パネルへ統合**した（統合列にパネル名を明記）。',
    '行番号は 2026-07-12 時点の `lesson_XX.md` の実測（行がずれた場合はプレースホルダ冒頭の文字列一致で照合すること）。',
    '',
    '| # | レッスン | 行 | プレースホルダ（冒頭） | 図版ファイル | 統合（パネル） | 参照記法 |',
    '|---|---|---|---|---|---|---|',
    '| 1 | lesson_01.md | 36 | 【図: 円O。円周上に点A（左下）・B（右下）…中心角∠AOB＝100°… | `L01_fig1_inscribed_central_definition.svg` | 単独 | `![円周角と中心角の定義](assets/L01_fig1_inscribed_central_definition.svg)` |',
    '| 2 | lesson_01.md | 66 | 【図: 実験のようす。円O・中心角∠AOB＝100°… | `L01_fig2_experiment_moving_point.svg` | 単独 | `![実験——点Pを動かす](assets/L01_fig2_experiment_moving_point.svg)` |',
    '| 3 | lesson_01.md | 99 | 1. 【図: 円O。円周上にA（左下）・B（右下）・P（上）・Q（右上）…70°… | `L01_fig3_practice_find_inscribed.svg` | 単独 | `![練習1の図](assets/L01_fig3_practice_find_inscribed.svg)`（設問文中の【図:…】部分のみ置換） |',
    '| 4 | lesson_02.md | 29 | 【図: 円O。下側の弧AB（中心角∠AOB＝100°）に色を塗る… | `L02_fig1_theorem_overview.svg` | 単独 | `![円周角の定理の全体図](assets/L02_fig1_theorem_overview.svg)` |',
    '| 5 | lesson_02.md | 50 | 【図: 円O。下側の弧BC（中心角∠BOC＝80°…）… | `L02_fig2_example_central_to_inscribed.svg` | 単独 | `![例題1の図](assets/L02_fig2_example_central_to_inscribed.svg)` |',
    '| 6 | lesson_02.md | 68 | 【図: 円。円周上に4点A・B・P・Q…∠APB＝64°… | `L02_fig3_example_same_arc.svg` | 単独 | `![例題3の図](assets/L02_fig3_example_same_arc.svg)` |',
    '| 7 | lesson_02.md | 81 | 【図: 円。円周上に4点A・B・C・D…∠BAC＝30°・∠ACD＝45°… | `L02_fig4_example_two_pairs.svg` | 単独 | `![例題4の図](assets/L02_fig4_example_two_pairs.svg)` |',
    '| 8 | lesson_02.md | 111 | 3. 【図: 円。円周上にA・B・P・Q…∠APB＝41°… | `L02_fig5_practice_3_4_5.svg` | パネル「練習3」 | `![練習3〜5の図](assets/L02_fig5_practice_3_4_5.svg)`（練習3の設問直前に1回だけ挿入） |',
    '| 9 | lesson_02.md | 112 | 4. 【図: 円。円周上にA・B・C・D…∠ACB＝63°… | `L02_fig5_practice_3_4_5.svg` | パネル「練習4」 | （#8と同一ファイル。図参照は重複させない） |',
    '| 10 | lesson_02.md | 116 | 5. 【図: 円O。半径OA・OBを引き、∠OAB＝25°… | `L02_fig5_practice_3_4_5.svg` | パネル「練習5」 | （#8と同一ファイル） |',
    '| 11 | lesson_02.md | 117 | 6. 【図: 円。円周上に4点A・B・C・D。∠BAC＝30°・∠ACD＝28°… | `L02_fig6_practice_6_7.svg` | パネル「練習6」 | `![練習6・7の図](assets/L02_fig6_practice_6_7.svg)`（練習6の設問直前に1回だけ挿入） |',
    '| 12 | lesson_02.md | 118 | 7. 【図: 円O。円周上に3点A・B・C…110°…130°… | `L02_fig6_practice_6_7.svg` | パネル「練習7」 | （#11と同一ファイル） |',
    '| 13 | lesson_03.md | 30 | 【図: 円O。水平な直径AB。円周上の上側に点P・P′… | `L03_fig1_diameter_semicircle.svg` | 単独 | `![半円の弧に対する円周角](assets/L03_fig1_diameter_semicircle.svg)` |',
    '| 14 | lesson_03.md | 36 | 【図: 円O。直径BC（水平）。…∠ABC＝32°… | `L03_fig2_example_diameter_triangle.svg` | 単独 | `![例題1の図](assets/L03_fig2_example_diameter_triangle.svg)` |',
    '| 15 | lesson_03.md | 63 | 【図: 円形の紙。円周上の点Pに直角の頂点を当てた三角定規… | `L03_fig3_find_center_right_angle.svg` | 単独 | `![円の中心を見つける](assets/L03_fig3_find_center_right_angle.svg)` |',
    '| 16 | lesson_03.md | 85 | 1. 【図: 円O。直径AB（水平）。…∠CAB＝41°… | `L03_fig4_practice_1_2.svg` | パネル「練習1」 | `![練習1・2の図](assets/L03_fig4_practice_1_2.svg)`（練習1の設問直前に1回だけ挿入） |',
    '| 17 | lesson_03.md | 86 | 2. 【図: 円O。直径AB。…∠DAB＝35°… | `L03_fig4_practice_1_2.svg` | パネル「練習2」 | （#16と同一ファイル） |',
    '| 18 | lesson_03.md | 87 | 3. 【図: 円（中心の印なし）。3本の弦PQ・RS・TU… | `L03_fig5_practice_which_diameter.svg` | 単独 | `![練習3の図](assets/L03_fig5_practice_which_diameter.svg)`（設問文中の【図:…】部分のみ置換） |',
    '| 19 | lesson_04.md | 38 | 【図: 円O。上側の円周上に点P…直径PQ…∠APQ＝a・∠QPB＝b… | `L04_fig1_proof_diameter_split.svg` | 単独 | `![証明の図](assets/L04_fig1_proof_diameter_split.svg)` |',
    '| 20 | lesson_04.md | 90 | 【図: (1)用: 円O・PAが直径… (2)用: 円O・…Oが∠APBの外側… | `L04_fig2_stretch_case_split.svg` | 2パネル（(1)/(2)）を1ファイルに統合 | `![場合分け(1)(2)の図](assets/L04_fig2_stretch_case_split.svg)` |',
    '| 21 | lesson_05.md | 30 | 【図: 直線AB（水平…）。ABの上側に2点P・Q。∠APB＝∠AQB＝50°… | `L05_fig1_converse_theorem.svg` | 単独 | `![円周角の定理の逆](assets/L05_fig1_converse_theorem.svg)` |',
    '| 22 | lesson_05.md | 38 | 【図: 直線AB（水平）。ABの上側に点P…下側に点Q′… | `L05_fig2_counterexample_opposite_side.svg` | 単独 | `![反対側の反例](assets/L05_fig2_counterexample_opposite_side.svg)` |',
    '| 23 | lesson_05.md | 46 | 【図: 四角形ABCD（円は描かない）。…∠ACB＝40°・∠ADB＝40°… | `L05_fig3_example_judge_concyclic.svg` | 単独（例題1・2共通図） | `![例題1の図](assets/L05_fig3_example_judge_concyclic.svg)` |',
    '| 24 | lesson_05.md | 80 | (ア) 【図: 直線ABの同じ側（上側）にC・D。∠ACB＝50°・∠ADB＝50°… | `L05_fig4_practice_three_cases.svg` | パネル「(ア)」 | `![練習1(ア)(イ)(ウ)の図](assets/L05_fig4_practice_three_cases.svg)`（練習1の設問直前に1回だけ挿入） |',
    '| 25 | lesson_05.md | 81 | (イ) 【図: 直線ABの同じ側（上側）にC・D。∠ACB＝48°・∠ADB＝50°… | `L05_fig4_practice_three_cases.svg` | パネル「(イ)」 | （#24と同一ファイル） |',
    '| 26 | lesson_05.md | 82 | (ウ) 【図: 直線ABをはさんでCは上側・Dは下側。… | `L05_fig4_practice_three_cases.svg` | パネル「(ウ)」 | （#24と同一ファイル） |',
    '| 27 | lesson_05.md | 83 | 2. 【図: 四角形ABCD…∠BAC＝35°・∠BDC＝35°・∠ABD＝28°… | `L05_fig5_practice_judge_harvest.svg` | 単独 | `![練習2の図](assets/L05_fig5_practice_judge_harvest.svg)`（設問文中の【図:…】部分のみ置換） |',
    '| 28 | lesson_06.md | 30 | 【図: 円O（中央）と、円の外（右側やや上）の点P。… | `L06_fig1_tangent_problem_setup.svg` | 単独 | `![課題の図](assets/L06_fig1_tangent_problem_setup.svg)` |',
    '| 29 | lesson_06.md | 44 | 【図: 円O・外部の点P・OPの中点M…交点A（上）とB（下）… | `L06_fig2_tangent_construction.svg` | 単独 | `![接線の作図の完成図](assets/L06_fig2_tangent_construction.svg)` |',
    '| 30 | lesson_06.md | 59 | 【図: 円形の断面（丸太のイメージ…）。…さしがね（L字型）… | `L06_fig3_carpenter_square_log.svg` | 単独 | `![さしがねで直径を測る](assets/L06_fig3_carpenter_square_log.svg)` |',
    '| 31 | lesson_07.md | 34 | 【図: 円。円周上に4点A・B・C・D…∠ADB＝40°・∠DBC＝48°… | `L07_fig1_example_chord_intersection.svg` | 単独 | `![例題1の図](assets/L07_fig1_example_chord_intersection.svg)` |',
    '| 32 | lesson_07.md | 47 | 【図: 円O。…弧BCと弧CDの長さが等しい…∠BAC＝27°… | `L07_fig2_example_equal_arcs.svg` | 単独 | `![例題2の図](assets/L07_fig2_example_equal_arcs.svg)` |',
    '| 33 | lesson_07.md | 62 | 【図: 四角形ABCD…∠BAC＝52°・∠BDC＝52°・∠ACD＝31°… | `L07_fig3_example_converse_harvest.svg` | 単独 | `![例題3の図](assets/L07_fig3_example_converse_harvest.svg)` |',
    '| 34 | lesson_07.md | 85 | 1. 【図: 円。…∠ADB＝36°・∠DBC＝44°… | `L07_fig4_practice_1_to_4.svg` | パネル「練習1」 | `![練習1〜4の図](assets/L07_fig4_practice_1_to_4.svg)`（練習1の設問直前に1回だけ挿入） |',
    '| 35 | lesson_07.md | 86 | 2. 【図: 円O。…弧BC＝弧CD…∠BAC＝24°… | `L07_fig4_practice_1_to_4.svg` | パネル「練習2」 | （#34と同一ファイル） |',
    '| 36 | lesson_07.md | 87 | 3. 【図: 円O。半径OA・OB。…∠OAB＝28°… | `L07_fig4_practice_1_to_4.svg` | パネル「練習3」 | （#34と同一ファイル） |',
    '| 37 | lesson_07.md | 88 | 4. 【図: 四角形ABCD…∠ACB＝65°・∠ADB＝65°・∠DAC＝18°… | `L07_fig4_practice_1_to_4.svg` | パネル「練習4」 | （#34と同一ファイル） |',
    '| 38 | lesson_07.md | 93 | 【図: 円。円周上に4点A・B・C・D…記号のみで角度の数値なし】 | `L07_fig5_stretch_similar_triangles.svg` | 単独 | `![stretchの図](assets/L07_fig5_stretch_similar_triangles.svg)` |',
    '| 39 | lesson_08.md | 41 | 【図: 円O。水平な直径AB…弧AC＝40°・弧CD＝28°・弧DB＝112°…∠DBA＝34°… | `L08_fig1_example_tool_relay.svg` | 単独 | `![例題1の図](assets/L08_fig1_example_tool_relay.svg)` |',
    '| 40 | lesson_08.md | 82 | 2. 【図: 円。…∠ACB＝57°… | `L08_fig2_practice_2_3_4.svg` | パネル「練習2」 | `![練習2〜4の図](assets/L08_fig2_practice_2_3_4.svg)`（練習2の設問直前に1回だけ挿入） |',
    '| 41 | lesson_08.md | 83 | 3. 【図: 円O。水平な直径AB。…∠CAB＝37°… | `L08_fig2_practice_2_3_4.svg` | パネル「練習3」 | （#40と同一ファイル） |',
    '| 42 | lesson_08.md | 84 | 4. 【図: 円O。半径OA・OB。∠OAB＝31°… | `L08_fig2_practice_2_3_4.svg` | パネル「練習4」 | （#40と同一ファイル） |',
    '| 43 | lesson_08.md | 85 | 5. 【図: 円。…∠ADB＝42°・∠DBC＝39°… | `L08_fig3_practice_5_6.svg` | パネル「練習5」 | `![練習5・6の図](assets/L08_fig3_practice_5_6.svg)`（練習5の設問直前に1回だけ挿入） |',
    '| 44 | lesson_08.md | 86 | 6. 【図: 四角形ABCD…∠ACB＝58°・∠ADB＝58°・∠DAC＝21°… | `L08_fig3_practice_5_6.svg` | パネル「練習6」 | （#43と同一ファイル） |',
    '| 45 | lesson_08.md | 92 | 【図: 円O。水平な直径AB…弧AC＝50°・弧CD＝40°・弧DB＝90°… | `L08_fig4_stretch_diameter_similar.svg` | 単独 | `![stretchの図](assets/L08_fig4_stretch_diameter_similar.svg)` |',
    '| 46 | lesson_02.md | 120 | 9. 【図: 円O。円周上に3点A（上）・B（左上）・C（右上）。…中心角216°…144°… | `L02_fig7_practice_obtuse_inscribed.svg` | 単独 | `![練習9の図](assets/L02_fig7_practice_obtuse_inscribed.svg)`（設問文中の【図:…】部分のみ置換）※2026-07-12の外部批判レビュー（裁定）による改稿（鈍角ケース追加）で追加。既存行の番号を保つため末尾に追記 |',
    '',
    '### 補足',
    '',
    '- **充足率: 46/46**（プレースホルダ全件に対応図あり）。ファイル数は統合により34枚（統合は8ファイル21プレースホルダ分: L02×2・L03×1・L04×1・L05×1・L07×1・L08×2）。',
    '- 統合パネル図（#8〜12, #16〜17, #24〜26, #34〜37, #40〜44）は、**最初の設問の直前に1回だけ**図参照を挿入し、各設問文の【図:…】は削除する（パネル見出し「練習N」「(ア)」等が図内にあるため対応が取れる）。#20（L04 stretch）は1プレースホルダが最初から(1)(2)両方を指すため1ファイルで完結。',
    '- 答えの分離方針: 各設問の答えは図に記載していない。生成スクリプトが禁止文字列・出現回数の機械検査を行い、全34枚で合格（詳細は上表「答え漏れ検査」列）。',
    '',
]


# ===========================================================================
# メイン: 生成 + 禁止文字列検査 + XML検査 + マニフェスト自動出力
# ===========================================================================
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
    import re
    import xml.etree.ElementTree as ET

    def hits(key, joined):
        """数値つき文字列は桁境界で数える（「130°」の中の「30°」を誤検出しない）"""
        if key and key[0].isdigit():
            return len(re.findall(r"(?<![0-9])" + re.escape(key), joined))
        return joined.count(key)

    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in FIGS:
        meta = fn()
        cv = meta["canvas"]
        joined = "\n".join(cv.texts)
        # --- 答えの分離方針: 禁止文字列の機械検査 ---
        for bad in meta.get("check_tokens", []):
            assert hits(bad, joined) == 0, \
                f"答え漏れ検出: {meta['file']} に禁止文字列「{bad}」"
        for key, n_expect in meta.get("counts", {}).items():
            n = hits(key, joined)
            assert n == n_expect, \
                f"答え漏れ疑い: {meta['file']} 「{key}」出現{n}回（許容{n_expect}回）"
        out = ASSETS / meta["file"]
        cv.save(out, meta["file"], meta["title"], build_desc(meta))
        ET.parse(out)  # XML整形式検査（パース失敗で停止）
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓" for d, t in meta["checks"])
        n_guard = len(meta.get("check_tokens", []))
        cnt = "・".join(f"{k}×{v}" for k, v in meta.get("counts", {}).items())
        guard_txt = (f"答え漏れ検査: PASS（{n_guard}項目・対象値はanswer_key由来・非開示）"
                     if n_guard else "")
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks,
                     guard_txt +
                     ("／" if guard_txt and cnt else "") +
                     (f"回数固定（既出数値）:{cnt}" if cnt else "") or "—"))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 円周角の定理単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）。",
        "",
        "- 全図で下表の幾何検算（スクリプト内assert）が生成時に自動実行され、全件合格。",
        "- 全図でSVG内テキストの**答え漏れ機械検査**（禁止文字列・既出数値の出現回数固定）を実施し、全件合格。",
        "- 本文46箇所の【図】プレースホルダを34ファイルに統合（練習の連続コマは1ファイル内の複数パネル）。",
        "  プレースホルダ→ファイル/パネルの対応は本MANIFEST内の対応表（後掲「図版配置対応表」）を正とする。",
        "",
        "| ファイル | 対象 | 図の意図 | パラメータ（本文一致） | 検証結果（生成時assert） | 答え漏れ検査 |",
        "|---|---|---|---|---|---|",
    ]
    for f, lsn, title, intent, params, checks, guard in rows:
        lines.append(f"| `{f}` | {lsn} | {title}——{intent} | {params} | {checks} | {guard} |")
    lines += [
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （円周上の配置角・角度は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。幾何assert・答え漏れ検査に1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    lines += PLACEMENT_SECTION
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
