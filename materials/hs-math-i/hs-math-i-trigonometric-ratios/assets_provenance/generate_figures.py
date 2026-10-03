#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高1数学I「図形と計量（三角比）」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。各図の内容仕様（以下「図版仕様」。各 fig_* 関数冒頭のパラメータブロック・
Checker の検算項目・台帳の「逸脱」節に書いた、図の意図・ラベル一覧・検算項目のこと）は
本文 lesson_XX.md と一致させる。描画ヘルパーの書き方（Canvas / Checker / 許可リスト検査 /
禁止文字列検査 / 陽性対照 / FIGURE_MANIFEST 自動生成）は先行単元
materials/hs-math-i/hs-math-i-numbers-and-expressions/assets_provenance/generate_figures.py
を踏襲し、直角三角形・弧・直角マーク・寸法線のヘルパーは
materials/jhs-math-3/jhs-math-3-pythagorean-theorem/assets_provenance/generate_figures.py
の実例に合わせて書き直した（どちらの元スクリプトも無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（14枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / unicodedata / xml.etree / fractions）
- 座標の与え方: 本文明示値（辺の長さ・角）をパラメータに書き、数学座標→px の変換関数
  Frame.P を通して描く（px 直書きをしない）。検算 assert は同じ変換関数で照合する。
- 幾何の自己検証: 各 fig_* 関数内の Checker が図版仕様の検算項目を検算し、
  1つでも失敗すると例外で停止して図を出力しない。
- 答えの分離（二重ゲート＋陽性対照）:
  (1) 許可リスト検査——各図が宣言した「使ってよいラベル集合」(allow_texts) と
      生成後 SVG の <text> 全内容が集合として完全一致することを検査する。
  (2) 禁止文字列検査——図版仕様の禁止文字列 (check_tokens) が図中テキストに現れないこと、
      および各図の「数字の集合」制約 (digit_rule) を検査する。
  検査器は main() 冒頭の陽性対照（禁止値を仕込んだ合成 SVG で検出できること）で毎回実証する。
- 文字衛生: 絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字を、本スクリプト自身と
  全 SVG・台帳に対して機械検査する（公開側の検疫 CI と同じ向き）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。
"""

import math
import datetime
import re
import unicodedata
import xml.etree.ElementTree as ET
from fractions import Fraction as Fr
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSON_DIR = HERE.parent          # candidate_draft/ でも公開側の単元フォルダでも lesson_XX.md はこの階層
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md の規約） --------------------
MAIN_W = 1.6      # 主線幅（三角形の辺・円・軸）
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅（破線）
DASH = "6 4"      # 破線
DIM_W = 1.0       # 寸法線
THIN_W = 1.0      # 細線（半径 R など）
DOT_R = 2.5       # 点マーカー半径
RA_SIZE = 12.0    # 直角マークの一辺（px）
ARC_W = 1.2       # 角の弧の線幅
SHADE2 = "#eee"   # うすい網かけ（川の帯）
DEG = math.pi / 180.0
SQ2, SQ3, SQ6 = math.sqrt(2), math.sqrt(3), math.sqrt(6)


def fs_for(width):
    """基本文字サイズ = viewBox 幅の 3 パーセント（四捨五入）"""
    return round(width * 0.03)


# ===========================================================================
# 幾何ユーティリティ（px でも数学座標でも同じ）
# ===========================================================================
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def mid(a, b, t=0.5):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def unit(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


def angle_at(v, p, q):
    """頂点 v で辺 vp・vq がつくる角（度・0〜180）——px でも数学座標でも同じ値"""
    a = math.atan2(p[1] - v[1], p[0] - v[0])
    b = math.atan2(q[1] - v[1], q[0] - v[0])
    d = abs(b - a) % (2 * math.pi)
    return math.degrees(min(d, 2 * math.pi - d))


def math_deg(v_px, p_px):
    """px 座標で v から p への向きを数学の角（度・反時計回り・x 軸正が 0）で返す"""
    return math.degrees(math.atan2(-(p_px[1] - v_px[1]), p_px[0] - v_px[0])) % 360.0


def in_wedge(v_px, p_px, q_px, pt_px):
    """点 pt が頂点 v・辺 vp・vq の劣角の内側にあるか（px）"""
    return (abs(angle_at(v_px, p_px, pt_px) + angle_at(v_px, pt_px, q_px)
                - angle_at(v_px, p_px, q_px)) < 1e-9)


def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・記号は個別"""
    special = {"°": 0.45, "′": 0.3, "²": 0.45, "√": 0.8, "θ": 0.6, "−": 0.6,
               "Ⅱ": 0.7, " ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4}
    w = 0.0
    for ch in s:
        if ch in special:
            w += special[ch]
        elif ord(ch) < 128:
            w += 0.6
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 1.0
        else:
            w += 0.7
    return w * size


def digit_runs(texts):
    """ラベル群に含まれる数字の連なり（「180°−θ」→ {"180"}）"""
    out = set()
    for t in texts:
        out.update(re.findall(r"[0-9]+", t))
    return out


def show_set(s):
    """集合を整列した文字列にする（台帳に載せる detail 用。set をそのまま f-string に入れると
    要素順がプロセスごとに変わり、台帳の再生成照合が落ちる）"""
    return "{" + ", ".join(sorted(s, key=lambda t: (len(t), t))) + "}"


def no_digits(texts):
    return not any(re.search(r"[0-9]", t) for t in texts)


# ===========================================================================
# 描画ヘルパー（Canvas = px 座標・Frame = 数学座標→px の線形変換）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.body = []
        self.texts = []          # (x0, y0, x1, y1, s) 推定バウンディングボックス
        self.bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

    def _grow(self, x, y, pad=0.0):
        self.bbox[0] = min(self.bbox[0], x - pad)
        self.bbox[1] = min(self.bbox[1], y - pad)
        self.bbox[2] = max(self.bbox[2], x + pad)
        self.bbox[3] = max(self.bbox[3], y + pad)

    def raw(self, s):
        self.body.append(s)

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w); self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="#000" stroke-width="{w}"{d}/>')

    def polyline(self, pts, w=MAIN_W, dash=None, close=False):
        for x, y in pts:
            self._grow(x, y, w)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="none" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="round"{d}/>')

    def polygon_fill(self, pts, fill):
        for x, y in pts:
            self._grow(x, y)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')

    def dot(self, x, y, r=DOT_R):
        self._grow(x, y, r)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')

    def ring(self, x, y, r, w=1.4):
        """白抜きの小円（目の位置・木のてっぺんの輪郭）"""
        self._grow(x, y, r + w)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                 f'stroke="#000" stroke-width="{w}"/>')

    def rect(self, x, y, w, h, fill="none", dash=None, sw=1.4):
        self._grow(x, y, sw); self._grow(x + w, y + h, sw)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size, anchor="middle", weight=None):
        """(x, y) はベースライン。推定バウンディングボックスを記録する"""
        w = est_w(s, size)
        x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        box = (x0, y - 0.8 * size, x0 + w, y + 0.22 * size, s)
        self.texts.append(box)
        self._grow(box[0], box[1]); self._grow(box[2], box[3])
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def layout_checks(self, ck):
        """共通 assert: 全要素が viewBox 内／テキスト同士が重ならない（推定ボックス）"""
        ck.ok("全要素が viewBox 内に収まる（線幅・推定文字幅込み）",
              self.bbox[0] >= 0 and self.bbox[1] >= 0 and
              self.bbox[2] <= self.w and self.bbox[3] <= self.h,
              f"bbox=({self.bbox[0]:.1f},{self.bbox[1]:.1f})-({self.bbox[2]:.1f},{self.bbox[3]:.1f})")
        bad = []
        for i in range(len(self.texts)):
            for j in range(i + 1, len(self.texts)):
                a, b = self.texts[i], self.texts[j]
                if not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]):
                    bad.append((a[4], b[4]))
        ck.ok("ラベル同士が重ならない（推定ボックスの全ペア）", not bad, f"{bad}")

    def svg(self, fig_id, title, desc):
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md 準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + "\n".join(self.body) + "\n</svg>\n"
        )


class Frame:
    """数学座標 (x, y)（y 上向き）→ SVG px: x_px = ox + s*x, y_px = oy − s*y"""
    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def P(self, p):
        return (self.ox + self.s * p[0], self.oy - self.s * p[1])


def seg(cv, fr, a, b, w=MAIN_W, dash=None):
    (x1, y1), (x2, y2) = fr.P(a), fr.P(b)
    cv.line(x1, y1, x2, y2, w=w, dash=dash)


def poly(cv, fr, pts, w=MAIN_W, close=True):
    cv.polyline([fr.P(p) for p in pts], w=w, close=close)


def dot_m(cv, fr, p, r=DOT_R):
    x, y = fr.P(p)
    cv.dot(x, y, r)


def circle_path(cv, fr, c, r, w=MAIN_W, step_deg=2):
    """円（半径 r）の点を step_deg 刻みでサンプリングした閉じた折れ線（arc フラグ不使用）"""
    n = int(round(360 / step_deg))
    pts = [fr.P((c[0] + r * math.cos(i * step_deg * DEG), c[1] + r * math.sin(i * step_deg * DEG)))
           for i in range(n)]
    cv.polyline(pts, w=w, close=True)


def arc_px(cv, cx, cy, r, deg_from, deg_to, n=1, gap=4.0, w=ARC_W):
    """中心 (cx, cy) px・半径 r px・数学の角 deg_from→deg_to（反時計回り）の弧を n 重に描く。
    5° 以下の刻みでサンプリングした折れ線"""
    span = deg_to - deg_from
    k = max(6, int(math.ceil(abs(span) / 5.0)))
    for j in range(n):
        rr = r + j * gap
        pts = [(cx + rr * math.cos((deg_from + span * i / k) * DEG),
                cy - rr * math.sin((deg_from + span * i / k) * DEG)) for i in range(k + 1)]
        cv.polyline(pts, w=w)


def angle_arc(cv, fr, v, p, q, r, n=1):
    """頂点 v で辺 vp→vq の劣角に弧（px 半径 r）を n 重に描く（数学座標で指定）"""
    vx, vy = fr.P(v)
    a1 = math_deg((vx, vy), fr.P(p))
    a2 = math_deg((vx, vy), fr.P(q))
    d = (a2 - a1) % 360.0
    if d > 180.0:
        a1, d = a2, 360.0 - d
    arc_px(cv, vx, vy, r, a1, a1 + d, n=n)


def right_angle(cv, fr, v, p, q, size=RA_SIZE):
    """頂点 v の直角マーク（小さな正方形）。p, q は直交する2辺の先の点（数学座標）。
    投影図では2方向の平行四辺形になる"""
    vx, vy = fr.P(v)
    u = unit(sub(fr.P(p), (vx, vy)))
    w_ = unit(sub(fr.P(q), (vx, vy)))
    cv.polyline([(vx + u[0] * size, vy + u[1] * size),
                 (vx + (u[0] + w_[0]) * size, vy + (u[1] + w_[1]) * size),
                 (vx + w_[0] * size, vy + w_[1] * size)], w=1.2)


def dim_h(cv, x1, x2, y, label, fs, tick=4.0):
    """水平な寸法線: 細実線＋両端ティック。ラベルは線の中央（線を切って置く）"""
    w = est_w(label, fs) + 8
    xm = (x1 + x2) / 2
    cv.line(x1, y, xm - w / 2, y, w=DIM_W)
    cv.line(xm + w / 2, y, x2, y, w=DIM_W)
    for x in (x1, x2):
        cv.line(x, y - tick, x, y + tick, w=DIM_W)
    cv.text(xm, y + fs * 0.35, label, fs)


def dim_v(cv, x, y1, y2, fs, tick=4.0):
    """垂直な寸法線（ラベルは呼び出し側で置く）"""
    cv.line(x, y1, x, y2, w=DIM_W)
    for y in (y1, y2):
        cv.line(x - tick, y, x + tick, y, w=DIM_W)


def bracket_h(cv, x1, x2, y, label, fs, tick=4.0):
    """水平な寸法線（線は切らず、ラベルを線の下に置く——長い式ラベル用）"""
    cv.line(x1, y, x2, y, w=DIM_W)
    for x in (x1, x2):
        cv.line(x, y - tick, x, y + tick, w=DIM_W)
    cv.text((x1 + x2) / 2, y + fs * 1.15, label, fs)


def label_out(cv, fr, p, centroid_, s, fs, dist_=16.0, weight="bold"):
    """頂点名: 重心から離れる向きに dist_ px ずらして図形の外側に置く"""
    x, y = fr.P(p)
    cx, cy = fr.P(centroid_)
    d = unit((x - cx, y - cy))
    cv.text(x + d[0] * dist_, y + d[1] * dist_ + fs * 0.35, s, fs, weight=weight)


def side_label(cv, fr, p, q, away, s, fs, off=14.0, t=0.5, anchor="middle"):
    """線分 pq の位置 t から、点 away と反対側へ法線方向に off px ずらしてラベルを置く"""
    a, b, c = fr.P(p), fr.P(q), fr.P(away)
    m = mid(a, b, t)
    d = unit(sub(b, a))
    n = (-d[1], d[0])
    if dot(n, sub(c, m)) > 0:
        n = (-n[0], -n[1])
    cv.text(m[0] + n[0] * off, m[1] + n[1] * off + fs * 0.35, s, fs, anchor=anchor)
    return (m[0] + n[0] * off, m[1] + n[1] * off)


def label_polar(cv, fr, v, deg, r, s, fs, anchor="middle"):
    """頂点 v から数学の角 deg の向きに r px 離れた位置を中心にラベルを置く。中心 px を返す"""
    vx, vy = fr.P(v)
    x, y = vx + r * math.cos(deg * DEG), vy - r * math.sin(deg * DEG)
    cv.text(x, y + fs * 0.35, s, fs, anchor=anchor)
    return (x, y)


def arrow(cv, x1, y1, x2, y2, w=1.4, head=7.0):
    """px 座標で矢印（線＋先端の三角形）"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.line(x1, y1, bx, by, w=w)
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
           (bx - nx * head * 0.45, by - ny * head * 0.45)]
    cv.polygon_fill(pts, "#000")


def axes(cv, fr, xmin, xmax, ymin, ymax, fs):
    """矢印つきの x 軸・y 軸と軸ラベル x・y・原点ラベル O（左下）。置いたラベルを返す"""
    ox, oy = fr.P((0, 0))
    x0, x1 = fr.P((xmin, 0))[0], fr.P((xmax, 0))[0]
    y0, y1 = fr.P((0, ymin))[1], fr.P((0, ymax))[1]
    arrow(cv, x0, oy, x1, oy, w=MAIN_W, head=9.0)
    arrow(cv, ox, y0, ox, y1, w=MAIN_W, head=9.0)
    cv.text(x1 + 6, oy + fs * 0.35, "x", fs, anchor="start")
    cv.text(ox, y1 - 6, "y", fs)
    cv.text(ox - 8, oy + fs * 1.0, "O", fs, anchor="end")
    return ["x", "y", "O"]


class Checker:
    """幾何検算の記録つき assert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


# ===========================================================================
# L01〜L05
# ===========================================================================
# 図1: L01 §2 角 A を共有する 3-4-5・6-8-10・9-12-15 の重ね描き
def fig_L01_2():
    # --- パラメータ（図版仕様: L01_fig2・lesson_01.md §2） ---
    tri = [(4, 3, 5), (8, 6, 10), (12, 9, 15)]   # (隣辺, 対辺, 斜辺)
    W, H = 640, 440
    fr = Frame(60, 340, 20)                      # A=(60,340) px・倍率 20 px/単位
    dim_ys = [362, 384, 406]
    formula = "3/5=6/10=9/15=0.6"
    fs = fs_for(W)

    ck = Checker()
    A = (0, 0)
    C = [(adj, 0) for adj, _, _ in tri]
    B = [(adj, opp) for adj, opp, _ in tri]
    for (adj, opp, hyp) in tri:
        ck.ok(f"{opp}²＋{adj}²={hyp}²（整数演算）", opp * opp + adj * adj == hyp * hyp)
    ck.ok("B1・B2・B3 が A を通る同一直線上（外積 0・整数演算）",
          cross(sub(B[1], A), sub(B[0], A)) == 0 and cross(sub(B[2], A), sub(B[0], A)) == 0)
    ck.ok("3/5=6/10=9/15=0.6（分数比較）",
          Fr(3, 5) == Fr(6, 10) == Fr(9, 15) == Fr("0.6"))
    ck.ok("各直角: (B−C)·(A−C)=0", all(dot(sub(B[i], C[i]), sub(A, C[i])) == 0 for i in range(3)))
    ck.ok("px 座標は変換関数から: C1=(140,340)・B3=(300,160)",
          fr.P(C[0]) == (140.0, 340.0) and fr.P(B[2]) == (300.0, 160.0))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    for i in (2, 1, 0):
        poly(cv, fr, [A, C[i], B[i]])
        right_angle(cv, fr, C[i], A, B[i])
    angle_arc(cv, fr, A, C[0], B[0], r=26)
    ax, ay = fr.P(A)
    T(ax - 12, ay + fs * 0.9, "A", weight="bold")
    # 対辺（垂直線）の右側
    for i, (_, opp, _) in enumerate(tri):
        cx, cy = fr.P(C[i])
        bx, by = fr.P(B[i])
        T(cx + 10, (cy + by) / 2 + fs * 0.35, str(opp), anchor="start")
    # 斜辺の中点の左上
    for i, (_, _, hyp) in enumerate(tri):
        m = mid(fr.P(A), fr.P(B[i]))
        d = unit(sub(fr.P(B[i]), fr.P(A)))
        n = (d[1], -d[0])            # 左上向きの法線（px）
        T(m[0] + n[0] * 16, m[1] + n[1] * 16 + fs * 0.35, str(hyp))
    # 隣辺の寸法線 3 段
    for (adj, _, _), y in zip(tri, dim_ys):
        labels.append(str(adj))
        dim_h(cv, ax, fr.P((adj, 0))[0], y, str(adj), fs)
    T(ax, 60, formula, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L01_fig2_similar_right_triangles_overlay.svg", "lesson": "L01", "canvas": cv,
            "title": "同じ鋭角をもつ3つの直角三角形の重ね描き——対辺/斜辺 は 0.6 でそろう",
            "desc": "頂点 A を共有する 3-4-5・6-8-10・9-12-15 の直角三角形を、隣辺を水平・対辺を垂直に重ねて描く。斜辺は同一直線上。辺の長さと 3/5=6/10=9/15=0.6 をラベルする。同型図は3組の (隣辺, 対辺, 斜辺) を差し替えて生成する（整数の直角三角形を使う）",
            "alt": "角 A を共有し、頂点 A を重ねてかいた3つの直角三角形——斜辺 5・向かいの辺 3・はさむ辺 4、斜辺 10・向かいの辺 6・はさむ辺 8、斜辺 15・向かいの辺 9・はさむ辺 12。3つは相似で、向かいの辺/斜辺 はどれも 0.6",
            "intent": "同じ鋭角 A をもつ3つの直角三角形を頂点 A で重ね、斜辺が同一直線上に乗ること（相似）と「対辺/斜辺」が 0.6 でそろうことを見せる",
            "src": "lesson_01.md §2（3つの直角三角形の段落の直後）",
            "params": "(隣辺, 対辺, 斜辺)=(4,3,5)・(8,6,10)・(12,9,15)／倍率 20 px／単位・A=(60,340)／寸法線 y=362・384・406／式 3/5=6/10=9/15=0.6",
            "checks": ck.items,
            "check_tokens": ["7", "13", "17", "24", "25", "37", "0.8", "0.75", "°"],
            "digit_rule": ("subset", {"3", "4", "5", "6", "8", "9", "10", "12", "15", "0", "6"}),
            "allow_texts": labels}


# 図2: L01 §3 辺の呼び名（数値なし）
def fig_L01_1():
    # --- パラメータ（図版仕様: L01_fig1・lesson_01.md §3） ---
    W, H = 480, 320
    fr = Frame(60, 270, 1)                       # px 単位の枠（4:3:5 の形・角の数値は書かない）
    A, C, B = (0, 0), (320, 0), (320, 240)
    fs = fs_for(W)

    ck = Checker()
    ck.ok("直角は C: (B−C)·(A−C)=0", dot(sub(B, C), sub(A, C)) == 0)
    ck.ok("斜辺 AB が最長", dist(A, B) > dist(A, C) and dist(A, B) > dist(B, C))
    ck.ok("B は C の真上（px で B.y < C.y）", fr.P(B)[1] < fr.P(C)[1] and fr.P(B)[0] == fr.P(C)[0])
    ck.ok("px 座標: A=(60,270)・C=(380,270)・B=(380,30)",
          fr.P(A) == (60.0, 270.0) and fr.P(C) == (380.0, 270.0) and fr.P(B) == (380.0, 30.0))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    poly(cv, fr, [A, C, B])
    right_angle(cv, fr, C, A, B)
    angle_arc(cv, fr, A, C, B, r=26)
    G = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
    for p, s in ((A, "A"), (B, "B"), (C, "C")):
        labels.append(s)
        label_out(cv, fr, p, G, s, fs, dist_=18)
    m = mid(fr.P(A), fr.P(B))
    d = unit(sub(fr.P(B), fr.P(A)))
    n = (d[1], -d[0])
    T(m[0] + n[0] * 18, m[1] + n[1] * 18 + fs * 0.35, "斜辺")
    bc = mid(fr.P(B), fr.P(C))
    T(bc[0] + 12, bc[1] + fs * 0.35, "対辺", anchor="start")
    ac = mid(fr.P(A), fr.P(C))
    T(ac[0], ac[1] + 22 + fs * 0.35, "隣辺")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L01_fig1_right_triangle_side_names.svg", "lesson": "L01", "canvas": cv,
            "title": "直角三角形 ABC の辺の呼び名（角 A に注目）——斜辺・対辺・隣辺",
            "desc": "∠C=90° の直角三角形を A 左下・C 右下・B 右上の向きで描き、AB を斜辺、BC を対辺、AC を隣辺とラベルする。数値は入れない。同型図は注目する角（A または B）とラベルの向きを差し替えて生成する",
            "alt": "直角三角形 ABC（∠C=90°）と角 A に注目したときの辺の呼び名——直角の向かいの AB が斜辺、角 A の向かいの BC が対辺、角 A をはさむ AC が隣辺",
            "intent": "角 A に注目したときの斜辺・対辺・隣辺の呼び名を辺のそばに書く定義図（数値なし・定義の向きの基準）",
            "src": "lesson_01.md §3（辺の呼び名の箇条書きの直後）",
            "params": "A=(60,270)・C=(380,270)・B=(380,30)（4:3:5 の形・角の数値は書かない）／ラベルは A・B・C・斜辺・対辺・隣辺のみ",
            "checks": ck.items,
            "check_tokens": ["13", "5", "12", "7", "24", "25", "8", "15", "17", "37", "0.6"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# 図3: L02 §2 例題2 仰角による木の高さの測量（実寸比）
def fig_L02_1():
    # --- パラメータ（図版仕様: L02_fig1・lesson_02.md §2 例題2） ---
    horiz, elev_deg, eye_h = 20.0, 32.0, 1.5     # 水平距離 m・仰角 °・目の高さ m
    W, H = 640, 400
    fr = Frame(80, 360, 16)                      # 地面 y=360・観測者の足元 x=80・16 px/m
    fs = fs_for(W)

    h = horiz * math.tan(elev_deg * DEG)
    foot, E = (0.0, 0.0), (0.0, eye_h)
    root, F, T_ = (horiz, 0.0), (horiz, eye_h), (horiz, eye_h + h)

    ck = Checker()
    ck.ok("h=20×tan 32° について |h−12.498|<0.001", abs(h - 12.498) < 0.001, f"h={h:.4f}")
    ck.ok("T の y 座標が変換関数 y_px(1.5＋h) と一致", fr.P(T_)[1] == fr.P((horiz, eye_h + h))[1])
    ck.ok("直角は F: (T−F)·(E−F)=0", dot(sub(T_, F), sub(E, F)) == 0)
    ck.ok("|FT|/|EF|=tan 32°（相対誤差 1e-9）",
          abs(dist(F, T_) / dist(E, F) / math.tan(elev_deg * DEG) - 1) < 1e-9)
    ck.ok("ET の傾き角（atan2）が 32°（1e-9）",
          near(math.degrees(math.atan2(T_[1] - E[1], T_[0] - E[0])), elev_deg))
    ck.ok("木の幹の上端が T と一致（幹は根元から T まで）", fr.P(T_) == fr.P((horiz, eye_h + h)))
    ck.ok("木の高さ h＋1.5≒14.0 m（答えは図に書かない）", abs((h + eye_h) - 14.0) < 0.01)
    ck.ok("実寸比: 水平・垂直とも 16 px/m", fr.s == 16)

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    gx0, gx1 = 30, 610
    cv.line(gx0, fr.P(foot)[1], gx1, fr.P(foot)[1], w=MAIN_W)      # 地面
    seg(cv, fr, foot, E)                                            # 観測者（輪郭のみ）
    ex, ey = fr.P(E)
    cv.ring(ex, ey, 4.0)
    seg(cv, fr, root, F)                                            # 木の幹（根元〜F）
    seg(cv, fr, F, T_, w=BOLD_W)                                    # FT（強調）
    tx, ty = fr.P(T_)
    cv.ring(tx, ty, 6.0)
    seg(cv, fr, E, F, w=AUX_W, dash=DASH)                           # 目の高さの水平線
    seg(cv, fr, E, T_)                                              # 視線
    dot_m(cv, fr, F)
    right_angle(cv, fr, F, E, T_)
    arc_px(cv, ex, ey, 40, 0, elev_deg)
    c = label_polar(cv, fr, E, elev_deg / 2, 75, f"{int(elev_deg)}°", fs)
    labels.append(f"{int(elev_deg)}°")
    ck.ok("仰角ラベルが角の内側（視線と水平線の間）にある", in_wedge(fr.P(E), fr.P(F), fr.P(T_), c))
    fx, fy = fr.P(F)
    gy = fr.P(foot)[1]
    labels.append(f"{int(horiz)} m")
    dim_h(cv, ex, fx, gy + 24, f"{int(horiz)} m", fs)
    dim_v(cv, ex - 28, ey, gy, fs)
    T(ex - 40, ey - 12, f"{eye_h} m")
    T(tx + 14, (ty + fy) / 2 + fs * 0.35, "？", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L02_fig1_elevation_angle_tree_height.svg", "lesson": "L02", "canvas": cv,
            "title": "仰角による木の高さの測量（水平距離 20 m・仰角 32°・目の高さ 1.5 m）",
            "desc": "観測者の目の位置から木のてっぺんまでの視線と、目の高さの水平線、木の幹で直角三角形をつくる。実寸比（1 m=16 px）。三角比で求める対辺（木のうち目の高さより上の部分）を太線と？で示す。木の高さはこれに目の高さを足した値で、答えの数値は書かない。同型図は水平距離・仰角・目の高さの3値を差し替えて生成する（俯角の図は水平線を上に置き、角を下向きにとる）",
            "alt": "木の高さの測量——目の位置から木の根元の真上（目の高さの点）までの水平距離 20 m、てっぺんを見上げる仰角 32°、目の高さ 1.5 m の直角三角形",
            "intent": "測量の設定を実寸比で見せ、目の位置・てっぺん・目の高さの点でできる直角三角形と、目の高さ 1.5 m を足す必要を図で示す",
            "src": "lesson_02.md §2 例題2（問題文の直後・解答の前）",
            "params": "水平距離 20 m・仰角 32°・目の高さ 1.5 m／16 px/m／h=20 tan 32°（≒12.498）は math.tan で計算・答え（14.0 m）は書かない",
            "checks": ck.items,
            "check_tokens": ["14", "12.5", "12.498", "0.6249", "25", "40°", "1.6", "22.6", "21",
                             "36", "15°", "134", "45", "28°", "84.6"],
            "digit_rule": ("subset", {"20", "32", "1", "5"}),
            "allow_texts": labels}


# 図4: L03 §2 斜辺 1 の直角三角形——対辺 sin A・隣辺 cos A
def fig_L03_1():
    # --- パラメータ（図版仕様: L03_fig1・lesson_03.md §2） ---
    ang = 35.0                                   # 角 A（描画用・値は書かない）
    W, H = 480, 320
    fr = Frame(60, 270, 300)                     # 斜辺 1 ↔ 300 px
    fs = fs_for(W)

    A = (0.0, 0.0)
    C = (math.cos(ang * DEG), 0.0)
    B = (math.cos(ang * DEG), math.sin(ang * DEG))

    ck = Checker()
    ck.ok("|BC|/|AB|=sin 35°・|AC|/|AB|=cos 35°（1e-9）",
          near(dist(B, C) / dist(A, B), math.sin(ang * DEG)) and
          near(dist(A, C) / dist(A, B), math.cos(ang * DEG)))
    ck.ok("直角は C: (B−C)·(A−C)=0", dot(sub(B, C), sub(A, C)) == 0)
    ck.ok("|AB|=300 px", near(dist(fr.P(A), fr.P(B)), 300.0))
    ck.ok("sin²35°＋cos²35°=1（1e-12）",
          near(math.sin(ang * DEG) ** 2 + math.cos(ang * DEG) ** 2, 1.0, 1e-12))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    poly(cv, fr, [A, C, B])
    right_angle(cv, fr, C, A, B)
    angle_arc(cv, fr, A, C, B, r=26)
    G = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
    for p, s in ((A, "A"), (B, "B"), (C, "C")):
        labels.append(s)
        label_out(cv, fr, p, G, s, fs, dist_=18)
    m = mid(fr.P(A), fr.P(B))
    d = unit(sub(fr.P(B), fr.P(A)))
    n = (d[1], -d[0])
    T(m[0] + n[0] * 16, m[1] + n[1] * 16 + fs * 0.35, "1")
    bc = mid(fr.P(B), fr.P(C))
    T(bc[0] + 12, bc[1] + fs * 0.35, "sin A", anchor="start")
    ac = mid(fr.P(A), fr.P(C))
    T(ac[0], ac[1] + 22 + fs * 0.35, "cos A")
    ck.ok("ラベルから「1」を除くと数字が残らない", no_digits([t for t in labels if t != "1"]))
    cv.layout_checks(ck)

    return {"file": "L03_fig1_unit_hypotenuse_sin_cos.svg", "lesson": "L03", "canvas": cv,
            "title": "斜辺 1 の直角三角形——対辺が sin A、隣辺が cos A",
            "desc": "A 左下・C 右下（直角）・B 右上の直角三角形。斜辺に 1、対辺に sin A、隣辺に cos A をラベルし、三平方の定理から sin²A＋cos²A=1 を読ませる。角 A は 35° で描くが値は書かない。同型図は角 A の大きさを差し替えて生成する",
            "alt": "斜辺の長さを 1 にした直角三角形——角 A の対辺の長さが sin A、隣辺の長さが cos A になる",
            "intent": "斜辺 1 の直角三角形に 1・sin A・cos A を辺の長さとして書き込み、sin²A＋cos²A=1 を図から読めるようにする",
            "src": "lesson_03.md §2（「斜辺 AB の長さを 1 にすると」の段落の直後）",
            "params": "斜辺 1 ↔ 300 px・A=(60,270)・角 A=35°（math.cos/sin から計算・値は書かない）／ラベルは A・B・C・1・sin A・cos A",
            "checks": ck.items,
            "check_tokens": ["3/5", "4/5", "5/13", "12/13", "√7", "√13", "0.28", "0.96", "16", "35", "°"],
            "digit_rule": ("subset", {"1"}),
            "allow_texts": labels}


# 図5: L04 §2 半径 r の円周上の点 P(x, y) と直角三角形 OPH——鋭角と鈍角の2パネル
def fig_L04_1():
    # --- パラメータ（図版仕様: L04_fig1・lesson_04.md §2） ---
    th_acute, th_obtuse = 50.0, 130.0            # 描画用の角（値は書かない・補角の組）
    r_px = 140
    W, H = 800, 420
    fs = 20                                      # 2.5%: 24 だと P(x, y) の左右ラベルが境界で接する（台帳に記録）
    panels = [(Frame(200, 230, r_px), th_acute, "鋭角の場合"),
              (Frame(600, 230, r_px), th_obtuse, "鈍角の場合")]

    ck = Checker()
    Ps = []
    for fr, th, _ in panels:
        P = (math.cos(th * DEG), math.sin(th * DEG))
        Hh = (P[0], 0.0)
        O = (0.0, 0.0)
        Ps.append((fr, th, P, Hh, O))
    (frL, thL, PL, HL, OL), (frR, thR, PR, HR, OR) = Ps
    ck.ok("左右とも |OP|=140 px（1e-9）",
          near(dist(frL.P(OL), frL.P(PL)), r_px) and near(dist(frR.P(OR), frR.P(PR)), r_px))
    ck.ok("左 P.x>O.x（鋭角）・右 P.x<O.x（鈍角）",
          frL.P(PL)[0] > frL.P(OL)[0] and frR.P(PR)[0] < frR.P(OR)[0])
    ck.ok("左右の P の y 座標が等しい（50° と 130° は補角で sin が等しい・1e-9）",
          near(frL.P(PL)[1], frR.P(PR)[1]))
    ck.ok("左: (P−H)·(O−H)=0", dot(sub(PL, HL), sub(OL, HL)) == 0)
    ck.ok("角 θ を atan2 で測ると 50°・130°（1e-9）",
          near(math.degrees(math.atan2(PL[1], PL[0])), thL) and
          near(math.degrees(math.atan2(PR[1], PR[0])), thR))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    for (fr, th, P, Hh, O), (_, _, cap) in zip(Ps, panels):
        labels.extend(axes(cv, fr, -1.25, 1.22, -1.07, 1.22, fs))
        circle_path(cv, fr, O, 1.0)
        seg(cv, fr, O, P)
        acute = th < 90
        seg(cv, fr, P, Hh, w=MAIN_W if acute else AUX_W, dash=None if acute else DASH)
        dot_m(cv, fr, P)
        ox, oy = fr.P(O)
        arc_px(cv, ox, oy, 30, 0, th)
        px, py = fr.P(P)
        if acute:
            T(px + 6, py - 10, "P(x, y)", anchor="start")
            right_angle(cv, fr, Hh, O, P)
            dot_m(cv, fr, Hh)
            hx, hy = fr.P(Hh)
            T(hx, hy + fs * 1.2, "H")
            T((ox + hx) / 2, hy + fs * 1.2, "x")
            T(hx + 10, (py + hy) / 2 + fs * 0.35, "y", anchor="start")
        else:
            T(px - 6, py - 10, "P(x, y)", anchor="end")
        c = label_polar(cv, fr, O, th / 2, 48, "θ", fs)
        labels.append("θ")
        ck.ok(f"θ ラベルが角の内側（{cap}）", in_wedge((ox, oy), (ox + 10, oy), (px, py), c))
        side_label(cv, fr, O, P, Hh, "r", fs, off=14)
        labels.append("r")
        T(ox, 408, cap)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L04_fig1_circle_point_acute_obtuse.svg", "lesson": "L04", "canvas": cv,
            "title": "座標平面上の点 P(x, y) による三角比の言い直し——鋭角と鈍角の2パネル",
            "desc": "原点中心・半径 r の円周上の点 P と、P から x 軸へ下ろした垂線でできる直角三角形 OPH を左パネルに、y 軸の左側にある P（鈍角）を右パネルに描く。同型図は θ（左は鋭角・右はその補角）と r を差し替えて生成する",
            "alt": "座標平面で三角比を言い直す2パネル——左は鋭角 θ: 原点 O を中心とする半径 r の円周上の点 P(x, y) と、P から x 軸に下ろした垂線の足 H でできる直角三角形 OPH。右は鈍角 θ: 点 P(x, y) が y 軸の左側（x<0）にあり、OP と x 軸の正の向きのなす角が θ",
            "intent": "三角比を座標で言い直す図。左（鋭角）で直角三角形 OPH が見え、右（鈍角）で同じ式が P の座標（x<0）から読めることを同じ配置で対比する",
            "src": "lesson_04.md §2（「まず θ が鋭角の場合を考える」の直後）",
            "params": "2パネル各 400 幅・O=(200,230)/(600,230)・r=140 px／描画角 θ=50°・130°（値は書かない）／垂線は左 実線・右 破線／ラベルは O・P(x, y)・H・θ・r・x・y・見出し2つ",
            "checks": ck.items,
            "check_tokens": ["120", "135", "130", "50", "−3", "4", "5", "13", "12", "−8", "6",
                             "10", "150", "√3"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# 図6: L04 §4 単位円上の 0°・90°・180° の点
def fig_L04_2():
    # --- パラメータ（図版仕様: L04_fig2・lesson_04.md §4） ---
    angs = [0, 90, 180]
    W, H = 480, 400
    fr = Frame(240, 230, 150)                    # O=(240,230)・150 px/単位
    r_arc90, r_arc180 = 30, 64                   # 180° の弧は 90° の弧と半径を変える（仕様 44→64・台帳に記録）
    fs = fs_for(W)

    pts = [(math.cos(a * DEG), math.sin(a * DEG)) for a in angs]
    expect = [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)]
    ck = Checker()
    ck.ok("3 点が (cos θ, sin θ)=(1,0)(0,1)(−1,0) に一致（1e-12）",
          all(near(p[0], e[0], 1e-12) and near(p[1], e[1], 1e-12) for p, e in zip(pts, expect)))
    ck.ok("3 点がそれぞれ円周上（距離 1・1e-12）", all(near(math.hypot(*p), 1.0, 1e-12) for p in pts))
    ck.ok("点の px が変換関数と一致: (1,0)→(390,230)・(0,1)→(240,80)・(−1,0)→(90,230)",
          all(near(fr.P(p)[0], e[0], 1e-9) and near(fr.P(p)[1], e[1], 1e-9)
              for p, e in zip(pts, [(390, 230), (240, 80), (90, 230)])))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    labels.extend(axes(cv, fr, -1.4, 1.45, -1.05, 1.2, fs))
    circle_path(cv, fr, (0, 0), 1.0)
    ox, oy = fr.P((0, 0))
    for p in pts:
        dot_m(cv, fr, p)
    x1, y1 = fr.P(pts[0])
    T(x1 + 8, y1 + 22, "(1, 0)", anchor="start")
    T(x1 + 8, y1 - 8, "0°", anchor="start")
    x2, y2 = fr.P(pts[1])
    T(x2 + 8, y2 - 6, "(0, 1)", anchor="start")
    x3, y3 = fr.P(pts[2])
    T(x3 - 8, y3 + 22, "(−1, 0)", anchor="end")
    arc_px(cv, ox, oy, r_arc90, 0, 90)
    c90 = label_polar(cv, fr, (0, 0), 45, 44, "90°", fs)
    labels.append("90°")
    arc_px(cv, ox, oy, r_arc180, 0, 180)
    c180 = label_polar(cv, fr, (0, 0), 120, 80, "180°", fs)
    labels.append("180°")
    ck.ok("90° ラベルが第1象限（角の内側）・180° ラベルが上半分（角の内側）",
          in_wedge((ox, oy), (ox + 10, oy), (x2, y2), c90) and c180[1] < oy and
          in_wedge((ox, oy), (ox + 10, oy), (x3, y3), c180))
    T((ox + x1) / 2, oy + 18 + fs * 0.35, "1")
    ck.ok("ラベルの数字の集合が {0,1,8,9} の部分集合",
          set("".join(digit_runs(labels))) <= {"0", "1", "8", "9"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L04_fig2_circle_points_0_90_180.svg", "lesson": "L04", "canvas": cv,
            "title": "単位円上の 0°・90°・180° に対応する点",
            "desc": "原点中心・半径 1 の円に、x 軸正の向きから測った角 0°・90°・180° の点 (1, 0)・(0, 1)・(−1, 0) を描き、座標と角をラベルする。同型図は角の集合を差し替えて生成する（30°・45°・60° の点を加える等）",
            "alt": "半径 1 の円（単位円）上の 0°・90°・180° に対応する点——(1, 0)・(0, 1)・(−1, 0)",
            "intent": "単位円上で 0°・90°・180° に対応する点が (1, 0)・(0, 1)・(−1, 0) であることを座標と角の両方のラベルで示す（本文の表の根拠）",
            "src": "lesson_04.md §4（「それぞれの角に対応する点 P を読む」の直後）",
            "params": "O=(240,230)・150 px/単位／点は math.cos/sin から計算／90° の弧 r=30・180° の弧 r=64／ラベルは O・x・y・(1, 0)・(0, 1)・(−1, 0)・0°・90°・180°・1",
            "checks": ck.items,
            "check_tokens": ["120", "135", "150", "110", "155", "130", "√", "−3", "−8", "−1/2", "√3/2"],
            "digit_rule": ("chars", {"0", "1", "8", "9"}),
            "allow_texts": labels}


# 図7: L05 §1 θ と 180°−θ の点の y 軸対称
def fig_L05_1():
    # --- パラメータ（図版仕様: L05_fig1・lesson_05.md §1） ---
    th = 40.0                                    # 描画用の角（値は書かない）
    W, H = 480, 400
    fr = Frame(240, 230, 150)
    fs = fs_for(W)

    O = (0.0, 0.0)
    P = (math.cos(th * DEG), math.sin(th * DEG))
    Q = (-math.cos(th * DEG), math.sin(th * DEG))
    ck = Checker()
    ck.ok("Q.x=2×O.x−P.x かつ Q.y=P.y（px・1e-9）",
          near(fr.P(Q)[0], 2 * fr.P(O)[0] - fr.P(P)[0]) and near(fr.P(Q)[1], fr.P(P)[1]))
    ck.ok("|OP|=|OQ|=150 px", near(dist(fr.P(O), fr.P(P)), 150) and near(dist(fr.P(O), fr.P(Q)), 150))
    ck.ok("atan2 で測った OQ の角が 180°−（OP の角）（1e-9）",
          near(math.degrees(math.atan2(Q[1], Q[0])), 180 - math.degrees(math.atan2(P[1], P[0]))))
    ck.ok("P.x>O.x・Q.x<O.x", fr.P(P)[0] > fr.P(O)[0] and fr.P(Q)[0] < fr.P(O)[0])

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    labels.extend(axes(cv, fr, -1.4, 1.45, -1.05, 1.2, fs))
    circle_path(cv, fr, O, 1.0)
    seg(cv, fr, O, P)
    seg(cv, fr, O, Q)
    seg(cv, fr, P, Q, w=AUX_W, dash=DASH)
    seg(cv, fr, P, (P[0], 0), w=AUX_W, dash=DASH)
    seg(cv, fr, Q, (Q[0], 0), w=AUX_W, dash=DASH)
    dot_m(cv, fr, P)
    dot_m(cv, fr, Q)
    ox, oy = fr.P(O)
    px, py = fr.P(P)
    qx, qy = fr.P(Q)
    T(px + 6, py - 6, "P(x, y)", anchor="start")
    T(qx - 6, qy - 6, "Q(−x, y)", anchor="end")
    arc_px(cv, ox, oy, 30, 0, th)
    arc_px(cv, ox, oy, 44, 0, 180 - th)
    c1 = label_polar(cv, fr, O, th / 2 - 2, 50, "θ", fs)
    labels.append("θ")
    c2 = label_polar(cv, fr, O, 95, 72, "180°−θ", fs, anchor="end")
    labels.append("180°−θ")
    ck.ok("θ ラベルが角 θ の内側・180°−θ ラベルが角 180°−θ の内側",
          in_wedge((ox, oy), (ox + 10, oy), (px, py), c1) and
          in_wedge((ox, oy), (ox + 10, oy), (qx, qy), c2))
    ck.ok("ラベルの数字の集合が {0,1,8} の部分集合",
          set("".join(digit_runs(labels))) <= {"0", "1", "8"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L05_fig1_supplementary_angle_symmetry.svg", "lesson": "L05", "canvas": cv,
            "title": "θ と 180°−θ に対応する単位円上の点の y 軸対称",
            "desc": "原点中心・半径 1 の円に、角 θ の点 P(x, y) と角 180°−θ の点 Q(−x, y) を描き、水平な破線と垂線で y 座標が等しく x 座標の符号が逆であることを見せる。θ=40° で描くが値は書かない。同型図は θ を差し替えて生成する（90°−θ の対称は y=x について折り返す別図）",
            "alt": "単位円上で θ に対応する点 P(x, y) と 180°−θ に対応する点 Q(−x, y)——2点は y 軸について対称で、y 座標が等しく x 座標の符号が逆",
            "intent": "θ の点 P(x, y) と 180°−θ の点 Q(−x, y) が y 軸について対称であることを、水平な破線と2本の垂線で見せる（sin(180°−θ)=sin θ・cos(180°−θ)=−cos θ の根拠）",
            "src": "lesson_05.md §1（「Q の座標は (−x, y) である」の段落の直後）",
            "params": "O=(240,230)・150 px/単位・描画角 θ=40°（値は書かない）／弧 θ r=30・180°−θ r=44／ラベルは O・x・y・P(x, y)・Q(−x, y)・θ・180°−θ",
            "checks": ck.items,
            "check_tokens": ["140", "40", "120", "60", "125", "55", "172", "24", "156", "73", "107", "√"],
            "digit_rule": ("chars", {"0", "1", "8"}),
            "allow_texts": labels}


# ===========================================================================
# L06〜L09
# ===========================================================================
# 図8: L06 §3 外接円と正弦定理の導出——直径 BD と直角三角形 BCD（鋭角・鈍角の2パネル）
def fig_L06_1():
    # --- パラメータ（図版仕様: L06_fig1・lesson_06.md §3） ---
    R = 100                                      # 外接円の半径 px
    angB, angC, angD = 200.0, 340.0, 20.0        # 円周上の位置（数学の角・度）。D は B の対心点
    W, H = 640, 340
    fs = fs_for(W)
    panels = [(Frame(150, 170, R), 100.0, "A が鋭角のとき", "∠BDC=A", 2),
              (Frame(490, 170, R), 270.0, "A が鈍角のとき", "∠BDC=180°−A", 1)]

    def on_circle(deg):
        return (math.cos(deg * DEG), math.sin(deg * DEG))

    O = (0.0, 0.0)
    B, C, D = on_circle(angB), on_circle(angC), on_circle(angD)
    ck = Checker()
    cv = Canvas(W, H)
    labels = []
    for fr, angA, heading, caption, n_arc in panels:
        A = on_circle(angA)
        tag = "鋭角" if angA < 180 else "鈍角"
        ck.ok(f"[{tag}] |OA|=|OB|=|OC|=|OD|=100 px（1e-6）",
              all(abs(dist(fr.P(O), fr.P(X)) - R) < 1e-6 for X in (A, B, C, D)))
        ck.ok(f"[{tag}] D=−B（O について対称）・B・O・D が一直線",
              near(D[0], -B[0]) and near(D[1], -B[1]) and near(cross(sub(B, O), sub(D, O)), 0))
        ck.ok(f"[{tag}] (B−C)·(D−C)=0（∠BCD=90°）",
              near(dot(sub(B, C), sub(D, C)), 0) and near(angle_at(C, B, D), 90))
        sA = cross(sub(C, B), sub(A, B))
        sD = cross(sub(C, B), sub(D, B))
        if angA < 180:
            ck.ok("[鋭角] A と D が直線 BC について同じ側（外積の符号が一致）", sA * sD > 0)
            ck.ok("[鋭角] ∠BAC=∠BDC（1e-6°）", abs(angle_at(A, B, C) - angle_at(D, B, C)) < 1e-6,
                  f"∠A={angle_at(A, B, C):.3f}°")
        else:
            ck.ok("[鈍角] A と D が直線 BC について反対側", sA * sD < 0)
            ck.ok("[鈍角] ∠BAC＋∠BDC=180°（1e-6°）",
                  abs(angle_at(A, B, C) + angle_at(D, B, C) - 180) < 1e-6,
                  f"∠A={angle_at(A, B, C):.3f}°")

        def T(x, y, s, **kw):
            labels.append(s)
            cv.text(x, y, s, fs, **kw)

        circle_path(cv, fr, O, 1.0)
        poly(cv, fr, [A, B, C])
        seg(cv, fr, B, D, w=AUX_W, dash=DASH)
        seg(cv, fr, C, D)
        seg(cv, fr, O, A, w=THIN_W)
        right_angle(cv, fr, C, B, D)
        angle_arc(cv, fr, A, B, C, r=22, n=n_arc)
        angle_arc(cv, fr, D, B, C, r=22, n=2)   # ∠BDC は左右とも 2重。∠A（n_arc）は ∠BDC と等しい左だけ 2重
        for p, s in ((A, "A"), (B, "B"), (C, "C"), (D, "D")):
            labels.append(s)
            label_out(cv, fr, p, O, s, fs, dist_=16)
        ox, oy = fr.P(O)
        T(ox - 10, oy + 20, "O", anchor="end")
        side_label(cv, fr, O, A, B, "R", fs, off=13)
        labels.append("R")
        ax_, ay_ = fr.P((0.35, -0.17))            # 弦 BC の中点付近（円の内側・鈍角パネルの A ラベルと衝突しないため）
        T(ax_, ay_ + fs * 0.35, "a")
        T(ox, 30, heading)
        T(ox, 320, caption)
    ck.ok("ラベルに含まれる数字は「180」のみ", digit_runs(labels) == {"180"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L06_fig1_circumcircle_sine_rule.svg", "lesson": "L06", "canvas": cv,
            "title": "外接円と正弦定理の導出——直径 BD を引いてできる直角三角形 BCD（鋭角と鈍角の2パネル）",
            "desc": "三角形 ABC の外接円（中心 O・半径 R）に頂点 B を通る直径 BD を引く。左は A が鋭角で、D は直線 BC について A と同じ側にあり、円周角の定理から ∠BDC=A。右は A が鈍角で、D は反対側にあり ∠BDC=180°−A。どちらも直角三角形 BCD で sin ∠BDC=a/(2R) となり、sin A=a/(2R) が成り立つ。同型の図を描くときは、B を通る直径のもう一方の端を D にとることと、∠BCD の直角マークを保つ。",
            "alt": "外接円と正弦定理——左パネル: 鋭角 A の三角形 ABC とその外接円（中心 O・半径 R）に、頂点 B を通る直径 BD を引き、直角三角形 BCD（∠BCD=90°）で ∠BDC が角 A と等しいことを示す。右パネル: 鈍角 A の場合で、D は直線 BC について A と反対側にあり ∠BDC=180°−A となる。どちらも sin A=a/(2R)",
            "intent": "正弦定理の導出「B を通る直径 BD を引くと直角三角形 BCD で ∠BDC が A（鋭角）または 180°−A（鈍角）になる」を2パネルで見せ、どちらも sin A=a/(2R) に落ちることを示す",
            "src": "lesson_06.md §3（鋭角の場合の導出の直後・「A が 90° のとき」の前）",
            "params": "R=100 px・O=(150,170)/(490,170)／円周上の位置 B=200°・C=340°・D=20°・A=100°（左）/270°（右）／角の弧の本数: ∠BDC は左右とも 2重・∠A は左 2重（∠BDC と等しい）・右 1重（∠BDC=180°−A で等しくない）／数字は 180 のみ",
            "checks": ck.items,
            "check_tokens": ["4√2", "15.0", "7.8", "6√2", "9.0", "9.8", "3√2", "5.8", "10.2", "6.8"],
            "digit_rule": ("subset", {"180"}),
            "deviations": ["当初の図版仕様「∠A と ∠BDC に同じ色の小さい角の弧」→ 白黒規約により色を使わず、"
                           "角の関係を弧の本数で示した（∠BDC は左右とも 2重。∠A は、∠BDC と等しい左パネルでは 2重、∠BDC=180°−A で等しくない右パネルでは 1重）",
                           "ラベル a は仕様の「弦 BC の中点付近・円の外側」でなく円の内側（弦 BC の上）に置いた"
                           "（右パネルで円の外側に置くと A のラベルと重なる）"],
            "allow_texts": labels}


# 図9: L07 §2 垂線 CH と余弦定理の導出（鋭角・鈍角の2パネル）
def fig_L07_1():
    # --- パラメータ（図版仕様: L07_fig1・lesson_07.md §1 活動1／§2 例題1） ---
    bL, cL, AL, aL = 5.0, 8.0, 60.0, 7.0         # 左: b=5・c=8・A=60°（a=7）
    bR, cR, AR, aR = 7.0, 8.0, 120.0, 13.0       # 右: b=7・c=8・A=120°（a=13）
    W, H = 720, 350
    fs, fs2 = 20, 17                             # 文字・式ラベル（2.8%・2.4%）
    panels = [(Frame(40, 250, 32), bL, cL, AL, aL, "A が鋭角のとき"),
              (Frame(510, 250, 20), bR, cR, AR, aR, "A が鈍角のとき")]

    ck = Checker()
    cv = Canvas(W, H)
    labels = []
    for fr, b, c, Adeg, a, heading in panels:
        A = (0.0, 0.0)
        B = (c, 0.0)
        C = (b * math.cos(Adeg * DEG), b * math.sin(Adeg * DEG))
        Hh = (C[0], 0.0)
        tag = "鋭角" if Adeg < 90 else "鈍角"
        ck.ok(f"[{tag}] H.y=A.y=B.y かつ C.x=H.x（CH⊥AB）", Hh[1] == A[1] == B[1] and C[0] == Hh[0])
        if Adeg < 90:
            ck.ok("[鋭角] A.x<H.x<B.x（H が辺 AB の内側）", A[0] < Hh[0] < B[0])
            ck.ok("[鋭角] CH²＋BH²=a²・a=7（|BC| との誤差 1e-6）",
                  abs(dist(C, Hh) ** 2 + dist(B, Hh) ** 2 - a * a) < 1e-6 and abs(dist(B, C) - a) < 1e-6)
            ck.ok("[鋭角] AH=b cos 60°=2.5・CH=5 sin 60°",
                  near(dist(A, Hh), 2.5) and near(dist(C, Hh), b * math.sin(Adeg * DEG)))
        else:
            ck.ok("[鈍角] H.x<A.x（H が辺 BA の A 側の延長上）", Hh[0] < A[0])
            ck.ok("[鈍角] CH²＋BH²=a²・a=13（|BC| との誤差 1e-6）",
                  abs(dist(C, Hh) ** 2 + dist(B, Hh) ** 2 - a * a) < 1e-6 and abs(dist(B, C) - a) < 1e-6)
            ck.ok("[鈍角] AH=−b cos 120°=3.5・CH=7 sin 120°",
                  near(dist(A, Hh), 3.5) and near(dist(C, Hh), b * math.sin(Adeg * DEG)))

        def T(x, y, s, size=fs, **kw):
            labels.append(s)
            cv.text(x, y, s, size, **kw)

        ax, ay = fr.P(A)
        bx, by = fr.P(B)
        cx, cy = fr.P(C)
        hx, hy = fr.P(Hh)
        poly(cv, fr, [A, B, C])
        seg(cv, fr, C, Hh, w=AUX_W, dash=DASH)
        T(ax, ay + 22, "A")
        T(bx, by + 22, "B")
        T(hx, hy + 22, "H")
        T(cx, cy - 12, "C")
        side_label(cv, fr, A, C, B, "b", fs, off=14)
        side_label(cv, fr, B, C, A, "a", fs, off=14, t=0.3)   # B 寄り（中点だと CH=b sin A の式ラベルと重なる）
        labels.extend(["b", "a"])
        m = mid((ax, ay), (bx, by))
        T(m[0], m[1] - 8, "c")
        if Adeg < 90:
            right_angle(cv, fr, Hh, C, B)
            T(hx + 8, hy - 36 + fs2 * 0.35, "CH=b sin A", size=fs2, anchor="start")   # CH の中点の高さだと辺 BC が文字にかかる
            labels.extend(["AH=b cos A", "BH=c−b cos A"])
            bracket_h(cv, ax, hx, 284, "AH=b cos A", fs2)
            bracket_h(cv, hx, bx, 284, "BH=c−b cos A", fs2)
        else:
            seg(cv, fr, A, Hh, w=AUX_W, dash=DASH)       # 辺 BA の A 側への延長
            right_angle(cv, fr, Hh, C, A)
            angle_arc(cv, fr, A, Hh, C, r=26)
            lab = "180°−A"
            cx_l = hx - 6 - est_w(lab, fs2) / 2
            T(hx - 6, 228 + fs2 * 0.35, lab, size=fs2, anchor="end")
            ck.ok("[鈍角] 180°−A のラベルが角の内側（延長線と AC の間）",
                  in_wedge((ax, ay), (hx, hy), (cx, cy), (cx_l, 228)))
            T(hx - 8, 195 + fs2 * 0.35, "CH=b sin A", size=fs2, anchor="end")
            labels.extend(["AH=b cos(180°−A)", "BH=c＋AH"])
            bracket_h(cv, hx, ax, 284, "AH=b cos(180°−A)", fs2)
            bracket_h(cv, hx, bx, 316, "BH=c＋AH", fs2)
        T((min(ax, hx) + bx) / 2, 30, heading)
    ck.ok("ラベルに含まれる数字は「180」のみ", digit_runs(labels) == {"180"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L07_fig1_perpendicular_cosine_rule.svg", "lesson": "L07", "canvas": cv,
            "title": "垂線と余弦定理の導出——C から AB に下ろした垂線 CH（鋭角と鈍角の2パネル）",
            "desc": "三角形 ABC で頂点 C から直線 AB に垂線 CH を下ろす。左は A が鋭角で、H が辺 AB 上にあり、AH=b cos A・CH=b sin A・BH=c−b cos A。右は A が鈍角で、H が辺 BA を A の側に延長した直線上にあり、AH=b cos(180°−A)・CH=b sin A・BH=c＋AH。どちらも直角三角形 BCH で a²=CH²＋BH² となり、整理すると a²=b²＋c²−2bc cos A。同型の図を描くときは、H の位置（内側／延長上）と直角マークを保つ。",
            "alt": "垂線と余弦定理——左パネル: 鋭角 A の三角形 ABC で、C から AB に下ろした垂線の足 H が辺 AB 上にあり、AH=b cos A・CH=b sin A・BH=c−b cos A。右パネル: 鈍角 A の場合で、H は辺 BA を A の側に延長した直線上にあり、AH=b cos(180°−A)・CH=b sin A・BH=c＋AH。どちらも a²=CH²＋BH²",
            "intent": "余弦定理の導出を、H が辺 AB の内側に落ちる鋭角と、辺 BA の延長上に落ちる鈍角で対比し、鈍角でも BH=c−b cos A の同じ式になることを見せる",
            "src": "lesson_07.md §2（鈍角の場合の説明の直後・「頂点 A について言えたことは」の前）",
            "params": "左 b=5・c=8・A=60°（a=7・32 px/単位・A=(40,250)）／右 b=7・c=8・A=120°（a=13・20 px/単位・A=(510,250)）／数値ラベルなし（数字は 180 のみ）／式ラベル 17 px",
            "checks": ck.items,
            "check_tokens": ["√21", "19", "5.4", "60°", "30°", "√19", "7"],
            "digit_rule": ("subset", {"180"}),
            "deviations": ["viewBox を仕様の 680×300 から 720×350 に拡張（式ラベル 4 本を辺の下 2 段に置く余白）",
                           "文字サイズ 20 px・式ラベル 17 px（幅の 2.8%・2.4%。3% にすると式ラベル同士が重なる）"],
            "allow_texts": labels}


# 図10: L08 §3 例題4 2辺と1つの対角で三角形が2つできる図
def fig_L08_1():
    # --- パラメータ（図版仕様: L08_fig1・lesson_08.md §3 例題4） ---
    a, b, Adeg = 2.0, 2 * SQ2, 30.0              # a=CB=2・b=AC=2√2・A=30°
    W, H = 560, 440
    fr = Frame(40, 360, 100)                     # 単位長 1=100 px・A=(40,360)
    fs, fs_ang = 17, 14                          # 文字・角ラベル（3.0%・2.5%）

    A = (0.0, 0.0)
    C = (b * math.cos(Adeg * DEG), b * math.sin(Adeg * DEG))
    Hh = (C[0], 0.0)
    half = math.sqrt(a * a - C[1] ** 2)           # 円と直線 AB の交点の H からの距離
    B = (C[0] + half, 0.0)
    Bp = (C[0] - half, 0.0)

    ck = Checker()
    ck.ok("|CB|=|CB′|=2（1e-9）", near(dist(C, B), a) and near(dist(C, Bp), a))
    ck.ok("B・B′・H・A が同一直線 y=0 上", B[1] == Bp[1] == Hh[1] == A[1] == 0.0)
    ck.ok("|CH|=√2 で √2<2<2√2（交点が2つある条件）",
          near(dist(C, Hh), SQ2) and SQ2 < a < b)
    ck.ok("A.x<B′.x<H.x<B.x", A[0] < Bp[0] < Hh[0] < B[0])
    ck.ok("∠ABC=45°・∠AB′C=135°（1e-6°）",
          abs(angle_at(B, A, C) - 45) < 1e-6 and abs(angle_at(Bp, A, C) - 135) < 1e-6)
    ck.ok("|AB|=√6＋√2・|AB′|=√6−√2（1e-9）",
          near(dist(A, B), SQ6 + SQ2) and near(dist(A, Bp), SQ6 - SQ2))
    ck.ok("C=(√6, √2)・H=(√6, 0)（1e-9）", near(C[0], SQ6) and near(C[1], SQ2))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, size=fs, **kw):
        labels.append(s)
        cv.text(x, y, s, size, **kw)

    seg(cv, fr, (-0.2, 0.0), (4.4, 0.0))          # 直線 AB（矢じりなし）
    circle_path(cv, fr, C, a, w=THIN_W)
    seg(cv, fr, A, C)
    seg(cv, fr, C, B)
    seg(cv, fr, C, Bp)
    seg(cv, fr, C, Hh, w=AUX_W, dash=DASH)
    right_angle(cv, fr, Hh, C, B)
    for p in (B, Bp, C, Hh):
        dot_m(cv, fr, p)
    ax, ay = fr.P(A)
    bx, by = fr.P(B)
    px, py = fr.P(Bp)
    cx, cy = fr.P(C)
    hx, hy = fr.P(Hh)
    T(ax, ay + 22, "A")
    T(px, py + 22, "B′")
    T(hx, hy + 22, "H")
    T(bx, by + 22, "B")
    T(cx, cy - 12, "C")
    angle_arc(cv, fr, A, B, C, r=26)
    angle_arc(cv, fr, B, A, C, r=22)
    angle_arc(cv, fr, Bp, A, C, r=22)
    cA = label_polar(cv, fr, A, 15, 76, "30°", fs_ang)
    cB = label_polar(cv, fr, B, 160, 52, "45°", fs_ang)
    cBp = label_polar(cv, fr, Bp, 100, 38, "135°", fs_ang)   # 95°/34 px だと 30° のラベル箱と 0.2 px 接する
    labels.extend(["30°", "45°", "135°"])
    ck.ok("角ラベル 30°・45°・135° がそれぞれの角の内側",
          in_wedge((ax, ay), (bx, by), (cx, cy), cA) and
          in_wedge((bx, by), (ax, ay), (cx, cy), cB) and
          in_wedge((px, py), (ax, ay), (cx, cy), cBp))
    side_label(cv, fr, A, C, B, "2√2", fs, off=16)
    side_label(cv, fr, C, Bp, Hh, "2", fs, off=14)
    side_label(cv, fr, C, B, Hh, "2", fs, off=14)
    labels.extend(["2√2", "2", "2"])
    T(hx + 8, (cy + hy) / 2 + fs * 0.35, "√2", anchor="start")
    ck.ok("ラベルの数字の連なりが {2, 30, 45, 135} のみ",
          digit_runs(labels) == {"2", "30", "45", "135"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L08_fig1_two_triangles_ssa.svg", "lesson": "L08", "canvas": cv,
            "title": "2辺と1つの対角で三角形が2つできる図——a=2・b=2√2・A=30°",
            "desc": "角 A=30° の一方の辺上に A から 2√2 の点 C をとり、C を中心とする半径 2 の円を描くと、もう一方の辺（直線 AB）と2点 B・B′ で交わる。C から直線 AB への垂線 CH の長さ √2 が半径 2 より短いため交点が2つある。△ABC は B=45°、△AB′C は B′=135°。同型の図を描くときは、垂線の長さ・半径・もう1辺の長さの大小（√2<2<2√2）を保つ。",
            "alt": "2辺と1つの対角で三角形が2つできる図——角 A=30° の2辺のうち一方の上に、A から 2√2 の距離に頂点 C をとり、C を中心とする半径 2 の円がもう一方の辺と2点 B・B′ で交わる。C から辺 AB へ下ろした垂線の長さ √2 が円の半径 2 より短いため交点が2つある。△ABC は角 B=45°、△AB′C は角 B′=135°",
            "intent": "「2辺と1つの対角」で三角形が2つできる理由を、C を中心とする半径 a の円と角 A のもう一方の辺との交点2つとして見せる（垂線 √2 が半径 2 より短いことが根拠）",
            "src": "lesson_08.md §3 例題4（2組の答えをまとめた段落の直後・「図で確かめる」の前）",
            "params": "a=2・b=2√2・A=30°／単位長 1=100 px・A=(40,360)（仕様の viewBox 320 高では円が上にはみ出すため 440 高に拡張）／辺 AB・AB′ にラベルを付けない／角ラベル 14 px",
            "checks": ck.items,
            "check_tokens": ["√6", "60°", "120°", "√3", "8", "3.9", "1.0", "√6＋√2", "√6−√2"],   # S1 の 4 は「45°」に部分一致するため数字集合の検査で担保
            "digit_rule": ("subset", {"2", "30", "45", "135"}),
            "deviations": ["viewBox を仕様の 560×320 から 560×440 に拡張（C を中心とする半径 2 の円が上にはみ出す）",
                           "文字サイズ 17 px・角ラベル 14 px（幅の 3.0%・2.5%。角ラベルは弧の内側に収めるため小さくした）"],
            "allow_texts": labels}


# 図11: L09 §1 面積公式の高さ AH=b sin C（鋭角・鈍角の2パネル）
def fig_L09_1():
    # --- パラメータ（図版仕様: L09_fig1・lesson_09.md §1 例題1(1)(2)） ---
    aL, bL, CL = 6.0, 5.0, 60.0                  # 左: a=6・b=5・C=60°
    aR, bR, CR = 4.0, 3.0, 150.0                 # 右: a=4・b=3・C=150°
    W, H = 720, 320
    fs, fs2, fs_ang = 20, 17, 14
    panels = [(Frame(40, 250, 32), aL, bL, CL, "6", "5", "5√3/2", "60°", "C が鋭角のとき"),
              (Frame(300, 250, 56), aR, bR, CR, "4", "3", "3/2", "150°", "C が鈍角のとき")]

    ck = Checker()
    cv = Canvas(W, H)
    labels = []
    for fr, a, b, Cdeg, la, lb, lh, lang, heading in panels:
        B = (0.0, 0.0)
        C = (a, 0.0)
        A = (C[0] + b * math.cos((180 - Cdeg) * DEG), C[1] + b * math.sin((180 - Cdeg) * DEG))
        Hh = (A[0], 0.0)
        tag = "鋭角" if Cdeg < 90 else "鈍角"
        ck.ok(f"[{tag}] H.y=B.y=C.y かつ A.x=H.x（AH⊥BC）", Hh[1] == B[1] == C[1] and A[0] == Hh[0])
        ck.ok(f"[{tag}] |CA|=b={b:g}・|BC|=a={a:g}（1e-9）", near(dist(C, A), b) and near(dist(B, C), a))
        ck.ok(f"[{tag}] 角 C={Cdeg:g}°（座標から・1e-9）", near(angle_at(C, B, A), Cdeg))
        if Cdeg < 90:
            ck.ok("[鋭角] B.x<H.x<C.x（H が辺 BC の内側）", B[0] < Hh[0] < C[0])
            ck.ok("[鋭角] |AH|=5 sin 60°=5√3/2（1e-9）", near(dist(A, Hh), 5 * SQ3 / 2))
            ck.ok("[鋭角] (1/2)×6×|AH|=15√3/2（例題1(1) の答えと一致）",
                  near(0.5 * a * dist(A, Hh), 15 * SQ3 / 2))
        else:
            ck.ok("[鈍角] H.x>C.x（H が辺 BC の C 側の延長上）", Hh[0] > C[0])
            ck.ok("[鈍角] |AH|=3 sin 150°=3/2（1e-9）", near(dist(A, Hh), 1.5))
            ck.ok("[鈍角] (1/2)×4×|AH|=3（例題1(2) の答えと一致）", near(0.5 * a * dist(A, Hh), 3.0))

        def T(x, y, s, size=fs, **kw):
            labels.append(s)
            cv.text(x, y, s, size, **kw)

        ax, ay = fr.P(A)
        bx, by = fr.P(B)
        cx, cy = fr.P(C)
        hx, hy = fr.P(Hh)
        poly(cv, fr, [A, B, C])
        seg(cv, fr, A, Hh, w=AUX_W, dash=DASH)
        right_angle(cv, fr, Hh, A, C if Cdeg >= 90 else B)
        T(ax, ay - 12, "A")
        T(bx, by + 22, "B")
        T(cx, cy + 22, "C")
        T(hx, hy + 22, "H")
        labels.append(la)
        dim_h(cv, bx, cx, 286, la, fs)
        angle_arc(cv, fr, C, B, A, r=24)
        if Cdeg < 90:
            cL_ = label_polar(cv, fr, C, 150, 44, lang, fs_ang)
            labels.append(lang)
            ck.ok("[鋭角] 60° のラベルが角 C の内側", in_wedge((cx, cy), (bx, by), (ax, ay), cL_))
            side_label(cv, fr, C, A, B, lb, fs, off=14)
            labels.append(lb)
            T(hx - 8, 215 + fs2 * 0.35, lh, size=fs2, anchor="end")
        else:
            seg(cv, fr, C, Hh, w=AUX_W, dash=DASH)       # 辺 BC の C 側への延長
            cR_ = label_polar(cv, fr, C, 105, 36, lang, fs_ang)
            labels.append(lang)
            ck.ok("[鈍角] 150° のラベルが角 C の内側", in_wedge((cx, cy), (bx, by), (ax, ay), cR_))
            angle_arc(cv, fr, C, Hh, A, r=32)
            cE = label_polar(cv, fr, C, 15, 80, "180°−C", fs_ang)
            labels.append("180°−C")
            ck.ok("[鈍角] 180°−C のラベルが延長線と CA の間", in_wedge((cx, cy), (hx, hy), (ax, ay), cE))
            side_label(cv, fr, C, A, Hh, lb, fs, off=14)
            labels.append(lb)
            T(hx + 8, (ay + hy) / 2 + fs2 * 0.35, lh, size=fs2, anchor="start")
        T((bx + max(cx, hx)) / 2, 30, heading)
    ck.ok("ラベルの数字の連なりが {6,5,3,2,60,4,150,180} の部分集合",
          digit_runs(labels) <= {"6", "5", "3", "2", "60", "4", "150", "180"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L09_fig1_height_b_sin_C.svg", "lesson": "L09", "canvas": cv,
            "title": "三角形の面積公式の高さ——A から BC に下ろした垂線 AH=b sin C（鋭角と鈍角の2パネル）",
            "desc": "辺 BC を底辺にとり、頂点 A から直線 BC に垂線 AH を下ろす。左は C が鋭角（a=6・b=5・C=60°）で H は辺 BC 上にあり AH=b sin C=5√3/2。右は C が鈍角（a=4・b=3・C=150°）で H は辺 BC の C 側の延長上にあり、AH=b sin(180°−C)=b sin C=3/2。どちらも S=(1/2)×a×AH=(1/2)ab sin C。同型の図を描くときは、H の位置（内側／延長上）と直角マークを保つ。",
            "alt": "面積公式の高さ——左パネル: 鋭角 C の三角形 ABC（a=6、b=5、C=60°）で、A から辺 BC に下ろした垂線 AH の長さが b sin C=5√3/2 であることを示す。右パネル: 鈍角 C の三角形（a=4、b=3、C=150°）で、垂線の足 H が辺 BC の C 側の延長上にあり、AH=b sin(180°−C)=b sin C=3/2 となる。どちらも S=(1/2)ab sin C",
            "intent": "面積公式の高さ AH=b sin C を、C が鋭角（H が辺 BC の内側）と鈍角（H が延長上・AH=b sin(180°−C)=b sin C）の2パネルで見せる（例題1(1)(2) の数値）",
            "src": "lesson_09.md §1（鈍角の場合の説明の直後・「頂点の選び方を変えても」の前）",
            "params": "左 a=6・b=5・C=60°（32 px/単位・B=(40,250)）／右 a=4・b=3・C=150°（56 px/単位・B=(300,250)。仕様の 40 px では鈍角側の角ラベルが入らないため拡大）／ラベルは 6・5・5√3/2・60°・4・3・3/2・150°・180°−C と頂点名・見出し",
            "checks": ck.items,
            "check_tokens": ["15√2/2", "14.2", "2√14", "120°", "14√3", "12√3", "55√3/4"],
            "digit_rule": ("subset", {"6", "5", "3", "2", "60", "4", "150", "180"}),
            "deviations": ["右パネルの倍率を仕様の 40 px/単位から 56 px/単位に拡大し、B を (300,250) に置いた"
                           "（40 px では鈍角側の角ラベル 150°・180°−C が弧の内側に入らない）。viewBox は 680×300→720×320",
                           "文字サイズ 20 px・式ラベル 17 px・角ラベル 14 px（幅の 2.8%・2.4%・1.9%）"],
            "allow_texts": labels}


# ===========================================================================
# L10〜L12
# ===========================================================================
# 図12: L10 §2 例題1 川をはさんだ2地点間の距離——与件図（実寸比）
def fig_L10_1():
    # --- パラメータ（図版仕様: L10_fig1・lesson_10.md §2 例題1） ---
    AB, angA, angB = 60.0, 45.0, 75.0            # AB=60 m・∠PAB=45°・∠PBA=75°
    W, H = 560, 400
    fr = Frame(100, 330, 5)                      # 5 px/m（等方・実寸比）・A=(100,330)
    fs = fs_for(W)
    band_x0, band_x1 = 20, 540                   # 川の帯の左右端 px

    angP = 180.0 - angA - angB
    PA = AB * math.sin(angB * DEG) / math.sin(angP * DEG)
    A = (0.0, 0.0)
    B = (AB, 0.0)
    P = (PA * math.cos(angA * DEG), PA * math.sin(angA * DEG))
    F = (P[0], 0.0)                              # P から直線 AB へ下ろした垂線の足

    ck = Checker()
    ck.ok("45＋75＋60=180（整数演算）", int(angA) + int(angB) + int(angP) == 180)
    ck.ok("座標から測った ∠PAB=45°・∠PBA=75°・∠APB=60°（1e-9）",
          near(angle_at(A, B, P), angA) and near(angle_at(B, A, P), angB) and near(angle_at(P, A, B), angP))
    ck.ok("|PB|=20√6（1e-9）", near(dist(P, B), 20 * SQ6), f"|PB|≒{dist(P, B):.6f}")
    ck.ok("|PA|=60 sin 75°/sin 60°（1e-9）", near(dist(P, A), 60 * math.sin(75 * DEG) / math.sin(60 * DEG)))
    ck.ok("垂線の足 F の x 座標が 0<x<60（両底角が鋭角で足は AB の内部）", 0 < F[0] < AB)
    ck.ok("|PF|=|PB| sin 75°（1e-9）・(P−F)·(B−A)=0", near(dist(P, F), dist(P, B) * math.sin(75 * DEG))
          and near(dot(sub(P, F), sub(B, A)), 0))
    ck.ok("等方スケール: 図上の 川幅/AB が実寸比と一致（1e-9）",
          near(dist(fr.P(P), fr.P(F)) / dist(fr.P(A), fr.P(B)), dist(P, F) / AB))
    ck.ok("川幅≒47.3 m（答えは図に書かない）", abs(dist(P, F) - 47.3) < 0.05, f"{dist(P, F):.3f}")

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    ax, ay = fr.P(A)
    bx, by = fr.P(B)
    px, py = fr.P(P)
    fx, fy = fr.P(F)
    cv.polygon_fill([(band_x0, py), (band_x1, py), (band_x1, ay), (band_x0, ay)], SHADE2)   # 川（帯）
    cv.line(band_x0, py, band_x1, py, w=MAIN_W)                                              # 向こう岸
    cv.line(band_x0, ay, band_x1, ay, w=MAIN_W)                                              # こちら岸
    ck.ok("川の帯の上下端が向こう岸の P と こちら岸の AB を通る（帯の高さが川幅）",
          near(py, fr.P(P)[1]) and near(ay, fr.P(A)[1]) and by == ay)
    poly(cv, fr, [A, B, P])
    seg(cv, fr, P, F, w=AUX_W, dash=DASH)
    right_angle(cv, fr, F, P, B)
    for p in (A, B, P, F):
        dot_m(cv, fr, p)
    T(ax, ay + 22, "A")
    T(bx, by + 22, "B")
    T(px, py - 12, "P")
    angle_arc(cv, fr, A, B, P, r=28)
    angle_arc(cv, fr, B, A, P, r=28)
    angle_arc(cv, fr, P, A, B, r=24)
    cA = label_polar(cv, fr, A, angA / 2, 58, "45°", fs)
    cB = label_polar(cv, fr, B, 180 - angB / 2, 56, "75°", fs)
    cP = label_polar(cv, fr, P, 255, 52, "60°", fs)
    labels.extend(["45°", "75°", "60°"])
    ck.ok("角ラベル 45°・75°・60° がそれぞれの角の内側",
          in_wedge((ax, ay), (bx, by), (px, py), cA) and in_wedge((bx, by), (ax, ay), (px, py), cB)
          and in_wedge((px, py), (ax, ay), (bx, by), cP))
    labels.append("60 m")
    dim_h(cv, ax, bx, ay + 42, "60 m", fs)
    T(fx - 8, (py + fy) / 2 + fs * 0.35, "川幅", anchor="end")
    ck.ok("ラベルの数字の連なりが {60, 45, 75} のみ", digit_runs(labels) == {"60", "45", "75"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L10_fig1_river_two_points.svg", "lesson": "L10", "canvas": cv,
            "title": "川をはさんだ2地点間の距離の測量図——AB=60 m・∠PAB=45°・∠PBA=75°（解く前の与件図）",
            "desc": "こちら岸の2地点 A・B（AB=60 m）と向こう岸の杭 P で三角形 PAB をつくり、分かっている辺 AB と両端の角 45°・75°、残りの角 60° を書き込む。P から直線 AB へ下ろした垂線（破線）が川幅で、その足は AB の内部にある。実寸比（1 m=5 px）。求める PB・PA・川幅の値は書かない。同型の図を描くときは AB・2つの角を差し替え、残りの角は 180° から引いて出す（両底角が鋭角なら垂線の足は AB の内部）",
            "alt": "川をはさんだ2地点間の距離の測量図——こちら岸の A と B（AB=60 m）、向こう岸の杭 P。∠PAB=45°、∠PBA=75°、残りの ∠APB=60°。P から直線 AB へ下ろした垂線が川幅",
            "intent": "「三角形を見つける」段階1の見本——場面（川・こちら岸の2地点・向こう岸の杭）を、求めたい量を辺にもつ三角形 PAB として図にし、分かっている量と求めたい量（垂線が川幅）を書き込んだ状態を示す",
            "src": "lesson_10.md §2 例題1 の直後（「段階1。図をかく。」の段落の次）",
            "params": "AB=60・∠PAB=45°・∠PBA=75°（∠APB=60° は 180° から計算）／PA=60 sin 75°/sin 60°・P=(PA cos 45°, PA sin 45°)／5 px/m 等方・A=(100,330)／川の帯は P の高さから AB まで（薄い網かけ）／ラベルは A・B・P・60 m・45°・75°・60°・川幅",
            "checks": ck.items,
            "check_tokens": ["20√6", "49.0", "66.9", "47.3", "48.98", "56.2", "54.64", "40", "30°", "1.6",
                             "122.5", "136.6", "100√3", "120√3", "16√2/3", "√10/10", "70", "41.0", "48.9"],
            "digit_rule": ("subset", {"60", "45", "75"}),
            "deviations": ["川の帯の「淡い塗り」は白黒規約に従い薄い網かけ（#eee）で描いた（色は使わない）"],
            "allow_texts": labels}


def _v3(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot3(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _cross3(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _dist3(a, b):
    return math.sqrt(_dot3(_v3(a, b), _v3(a, b)))


# 図13: L11 §3 例題3 正四面体の高さ——空間図と底面の平面図（2パネル）
def fig_L11_1():
    # --- パラメータ（図版仕様: L11_fig1・lesson_11.md §3 例題3） ---
    edge = 6.0                                   # 1辺 6
    k, alpha = 0.7, 30.0                         # 左パネルの斜投影: 奥行き y を倍率 k・角 alpha で描く
    W, H = 720, 340
    fs = fs_for(W)
    frL = Frame(40, 290, 36)                     # 左（空間図）36 px/単位
    frR = Frame(420, 290, 36)                    # 右（底面の平面図）36 px/単位

    # 3次元座標（底面 BCD を z=0 に置く）。添字 s は空間座標・v は投影後の描画座標
    Bs, Cs, Ds = (0.0, 0.0, 0.0), (edge, 0.0, 0.0), (edge / 2, edge * SQ3 / 2, 0.0)
    Ns = ((Bs[0] + Cs[0]) / 2, (Bs[1] + Cs[1]) / 2, 0.0)
    Hs = ((Bs[0] + Cs[0] + Ds[0]) / 3, (Bs[1] + Cs[1] + Ds[1]) / 3, 0.0)
    As = (Hs[0], Hs[1], edge * math.sqrt(2.0 / 3.0))

    ck = Checker()
    ck.ok("H は正三角形 BCD の中心 (3, √3)（3つの頂点の座標の平均・1e-9）", near(Hs[0], 3.0) and near(Hs[1], SQ3))
    ck.ok("|HB|=|HC|=|HD|=2√3（1e-9）", all(near(_dist3(Hs, X), 2 * SQ3) for X in (Bs, Cs, Ds)))
    ck.ok("|HN|=√3・|BN|=3・BN²＋HN²=BH²=12（1e-9）",
          near(_dist3(Hs, Ns), SQ3) and near(_dist3(Bs, Ns), 3.0)
          and near(_dist3(Bs, Ns) ** 2 + _dist3(Hs, Ns) ** 2, 12.0) and near(_dist3(Bs, Hs) ** 2, 12.0))
    ck.ok("∠HBN=30°（座標から・1e-9）・HN⊥BC",
          near(angle_at(Bs[:2], Ns[:2], Hs[:2]), 30.0) and near(_dot3(_v3(Hs, Ns), _v3(Cs, Bs)), 0))
    ck.ok("A=(3, √3, 2√6) で |AB|=|AC|=|AD|=6（1e-9）",
          near(As[2], 2 * SQ6) and all(near(_dist3(As, X), edge) for X in (Bs, Cs, Ds)))
    ck.ok("|AH|=2√6・AH⊥底面（AH·BC=AH·BD=0）・∠AHB=90°",
          near(_dist3(As, Hs), 2 * SQ6) and near(_dot3(_v3(As, Hs), _v3(Cs, Bs)), 0)
          and near(_dot3(_v3(As, Hs), _v3(Ds, Bs)), 0) and near(_dot3(_v3(As, Hs), _v3(Bs, Hs)), 0))
    ck.ok("例題3の答え（高さ 2√6・体積 18√2）と一致（図には書かない）",
          near((1.0 / 3.0) * (0.5 * edge * edge * math.sin(60 * DEG)) * _dist3(As, Hs), 18 * SQ2))

    def proj(p):
        """斜投影: (x, y, z) → (x＋k y cos α, z＋k y sin α)（z 軸は図の鉛直のまま）"""
        return (p[0] + k * p[1] * math.cos(alpha * DEG), p[2] + k * p[1] * math.sin(alpha * DEG))

    Av, Bv, Cv, Dv, Hv, Nv = (proj(X) for X in (As, Bs, Cs, Ds, Hs, Ns))
    ck.ok("投影で AH が鉛直（A と H の x が一致）", near(Av[0], Hv[0]))
    # 見える面・隠れる辺の判定: 投影方向 (−k cos α, 1, −k sin α) の逆向きが視点側
    viewer = (k * math.cos(alpha * DEG), -1.0, k * math.sin(alpha * DEG))
    verts = {"A": As, "B": Bs, "C": Cs, "D": Ds}
    G = tuple(sum(v[i] for v in verts.values()) / 4 for i in range(3))
    faces = [("A", "B", "C"), ("A", "C", "D"), ("A", "B", "D"), ("B", "C", "D")]
    visible = {}
    for f in faces:
        p0, p1, p2 = (verts[n] for n in f)
        nrm = _cross3(_v3(p1, p0), _v3(p2, p0))
        cen = tuple((p0[i] + p1[i] + p2[i]) / 3 for i in range(3))
        if _dot3(nrm, _v3(cen, G)) < 0:
            nrm = (-nrm[0], -nrm[1], -nrm[2])
        visible[f] = _dot3(nrm, viewer) > 0
    edges = [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("C", "D"), ("B", "D")]
    hidden = {e for e in edges if not any(visible[f] for f in faces if e[0] in f and e[1] in f)}
    ck.ok("隠れる辺は BD だけ（面の向きと視点から判定）", hidden == {("B", "D")}, f"hidden={sorted(hidden)}")
    ck.ok("ラベル 6 を付ける辺 AB の投影前の長さが 6", near(_dist3(As, Bs), edge))

    # 右パネル（底面の平面図）は当初の図版仕様の座標例そのもの
    Bp, Cp, Dp = (0.0, 0.0), (edge, 0.0), (edge / 2, edge * SQ3 / 2)
    Hp, Np = (edge / 2, edge * SQ3 / 6), (edge / 2, 0.0)
    ck.ok("平面図: H=(3, √3)・N=(3, 0)・∠BNH=90°・∠HBN=30°",
          near(Hp[1], SQ3) and near(dot(sub(Bp, Np), sub(Hp, Np)), 0) and near(angle_at(Bp, Np, Hp), 30.0))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    # 左パネル: 空間図
    poly(cv, frL, [Av, Bv, Cv])
    seg(cv, frL, Av, Dv)
    seg(cv, frL, Cv, Dv)
    seg(cv, frL, Bv, Dv, w=AUX_W, dash=DASH)      # 背面の辺
    seg(cv, frL, Av, Hv, w=AUX_W, dash=DASH)      # 高さ（内部）
    seg(cv, frL, Bv, Hv, w=THIN_W)
    seg(cv, frL, Hv, Nv, w=THIN_W)
    right_angle(cv, frL, Hv, Av, Bv)
    dot_m(cv, frL, Hv)
    dot_m(cv, frL, Nv)
    ax, ay = frL.P(Av)
    bx, by = frL.P(Bv)
    cx, cy = frL.P(Cv)
    dx, dy = frL.P(Dv)
    hx, hy = frL.P(Hv)
    nx, ny = frL.P(Nv)
    T(ax, ay - 12, "A")
    T(bx - 6, by + 20, "B", anchor="end")
    T(cx + 6, cy + 20, "C", anchor="start")
    T(dx + 10, dy + 6, "D", anchor="start")
    T(hx + 8, hy + 7, "H", anchor="start")
    T(nx, ny + 22, "N")
    side_label(cv, frL, Av, Bv, Cv, "6", fs, off=16)
    labels.append("6")
    T((bx + cx) / 2, 30, "空間図")
    # 右パネル: 底面 BCD を真上から見た図
    poly(cv, frR, [Bp, Cp, Dp])
    seg(cv, frR, Bp, Hp)
    seg(cv, frR, Hp, Np)
    right_angle(cv, frR, Np, Bp, Hp)
    dot_m(cv, frR, Hp)
    dot_m(cv, frR, Np)
    angle_arc(cv, frR, Bp, Np, Hp, r=30)
    rbx, rby = frR.P(Bp)
    rcx, rcy = frR.P(Cp)
    rdx, rdy = frR.P(Dp)
    rhx, rhy = frR.P(Hp)
    rnx, rny = frR.P(Np)
    T(rbx - 6, rby + 20, "B", anchor="end")
    T(rcx + 6, rcy + 20, "C", anchor="start")
    T(rdx, rdy - 12, "D")
    T(rhx + 10, rhy + 7, "H", anchor="start")
    T(rnx, rny + 22, "N")
    c30 = label_polar(cv, frR, Bp, 15, 56, "30°", fs)
    labels.append("30°")
    ck.ok("30° のラベルが角 HBN の内側", in_wedge((rbx, rby), (rnx, rny), (rhx, rhy), c30))
    T((rbx + rnx) / 2, rny + 22, "3")
    T((rbx + rcx) / 2, 30, "底面 BCD を真上から見た図")
    ck.ok("ラベルの数字の連なりが {6, 3, 30} のみ", digit_runs(labels) == {"6", "3", "30"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L11_fig1_tetrahedron_height.svg", "lesson": "L11", "canvas": cv,
            "title": "正四面体の高さ——空間図（垂線 AH）と底面 BCD の平面図（直角三角形 BNH）の2パネル",
            "desc": "左は 1辺 6 の正四面体 ABCD の斜投影図で、頂点 A から底面 BCD に下ろした垂線 AH（破線）とその足 H、BC の中点 N、線分 BH・HN を描く（背面の辺 BD は破線）。右は底面 BCD を真上から見た正三角形で、中心 H・中点 N・線分 BH・HN を入れ、∠BNH の直角マークと ∠HBN=30°、BN=3 をラベルする。BH・AH・体積の値は書かない。同型の図を描くときは、H を底面の正三角形の中心（3つの頂点から等しい距離の点）にとり、AH が鉛直に見える投影を使い、隠れる辺を破線にする",
            "alt": "正四面体の高さ——1辺 6 の正四面体 ABCD で、頂点 A から底面 BCD に下ろした垂線の足 H は底面の正三角形の中心。BC の中点を N とすると、△BNH は ∠BNH=90°、∠HBN=30°、BN=3 の直角三角形で、△ABH は ∠AHB=90° の直角三角形",
            "intent": "「平面を1枚取り出す」の見本——空間図（正四面体と高さ AH）と、取り出した平面図（底面 BCD を真上から見た図に H・N を入れたもの）を並べ、BH を出すための直角三角形 BNH が底面の中にあることを示す",
            "src": "lesson_11.md §3 例題3 の「垂線の足 H の位置」の段落の直後（「BH の長さは、……」の段落の前）",
            "params": "1辺 6／3次元座標 B=(0,0,0)・C=(6,0,0)・D=(3,3√3,0)・H=(3,√3,0)・N=(3,0,0)・A=(3,√3,2√6)／左: 斜投影 k=0.7・α=30°・36 px/単位・B=(40,290)／右: 平面図 36 px/単位・B=(420,290)／ラベルは A・B・C・D・H・N・6（辺 AB）・3（BN）・30°・見出し2つ",
            "checks": ck.items,
            "check_tokens": ["2√3", "2√6", "√3", "18√2", "9√3", "36", "12", "24", "2√19", "2√7", "3/2",
                             "√3/3", "3√3", "16√2/3", "4√6/3", "4√3", "√6", "9/4"],
            "digit_rule": ("subset", {"6", "3", "30"}),
            "deviations": ["当初の図版仕様のラベル一覧にないパネル見出し「空間図」「底面 BCD を真上から見た図」を加えた（右パネルが何の図かを示すため。数値は含まない）",
                           "ラベル 6 は辺 AB に付けた（辺 BC の中点 N のラベルと重なるため）"],
            "allow_texts": labels}


def _disjoint(a, b):
    return a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1]


def _on_edge(p, box, side):
    """点 p が矩形 box=(x, y, w, h) の指定した辺（left/right/top/bottom）の上にあるか"""
    x, y, w, h = box
    if side == "left":
        return near(p[0], x) and y <= p[1] <= y + h
    if side == "right":
        return near(p[0], x + w) and y <= p[1] <= y + h
    if side == "top":
        return near(p[1], y) and x <= p[0] <= x + w
    return near(p[1], y + h) and x <= p[0] <= x + w


# 図14: L12 §1 単元マップ——定義→拡張→定理→活用の4段と入出力
def fig_L12_1():
    # --- パラメータ（図版仕様: L12_fig1・lesson_12.md §1 の4段の箇条書き） ---
    W, H = 1020, 340
    Y0 = 60                                      # 中段の箱の上端 y
    fs_t, fs_s = 15, 12.5                        # 箱の見出し・副題と矢印ラベル
    stages = [("定義", (1, 3), ["sin・cos・tan", "相互関係・表"]),
              ("拡張", (4, 5), ["0°〜180°", "座標で定め直す・180°−θ"]),
              ("定理", (6, 9), ["正弦定理・余弦定理", "決定条件・面積"]),
              ("活用", (10, 11), ["4段階の手順", "平面図形・空間図形"])]
    boxes = [(40 + 210 * i, Y0, 160, 90) for i in range(4)]
    mid_labels = [("鈍角でも使いたいので", "座標で定め直す"),
                  ("拡張した三角比で", "定理を導く"),
                  ("決定条件で定理を選んで", "計量する")]
    out_boxes = [(870, Y0 - 30, 136, 44, "数学Ⅱ「三角関数」"), (870, Y0 + 80, 136, 44, "数学A「図形の性質」")]
    ylow = Y0 + 215                              # 下段の箱の上端 y
    low_boxes = [(60, ylow, 120, 48, "相似"), (265, ylow, 130, 48, "三平方の定理"), (475, ylow, 130, 48, "円周角の定理")]
    entry_label = ("相似で比が", "角だけで決まる")
    ymid = boxes[0][1] + boxes[0][3] / 2
    mid_arrows = [((boxes[i][0] + boxes[i][2], ymid), (boxes[i + 1][0], ymid)) for i in range(3)]
    right_arrows = [((boxes[3][0] + boxes[3][2], Y0 + 30.0), (out_boxes[0][0], Y0 - 8.0)),
                    ((boxes[3][0] + boxes[3][2], Y0 + 62.0), (out_boxes[1][0], Y0 + 102.0))]
    ybot = boxes[0][1] + boxes[0][3]
    low_arrows = [(0, ((120.0, ylow), (120.0, ybot)), 0),         # 相似 → 定義
                  (1, ((315.0, ylow), (170.0, ybot)), 0),         # 三平方の定理 → 定義（相互関係）
                  (1, ((345.0, ylow), (490.0, ybot)), 2),         # 三平方の定理 → 定理（余弦定理）
                  (2, ((540.0, ylow), (540.0, ybot)), 2)]         # 円周角の定理 → 定理（正弦定理）

    ck = Checker()
    rng = [r for _, r, _ in stages]
    covered = sorted(n for a, b in rng for n in range(a, b + 1))
    ck.ok("箱が4つ・レッスン番号 L01〜L11 を連続・重複なしに覆い L12 を含まない",
          len(stages) == 4 and covered == list(range(1, 12)) and all(rng[i][1] + 1 == rng[i + 1][0] for i in range(3)))
    allb = boxes + [b[:4] for b in out_boxes] + [b[:4] for b in low_boxes]
    ck.ok("箱 9 個が互いに重ならない", all(_disjoint(allb[i], allb[j]) for i in range(len(allb)) for j in range(i + 1, len(allb))))
    ck.ok("中段の矢印 3 本が隣接する箱の右辺から左辺へ同じ高さで結ぶ",
          len(mid_arrows) == 3 and all(_on_edge(p1, boxes[i], "right") and _on_edge(p2, boxes[i + 1], "left") and p1[1] == p2[1]
                                       for i, (p1, p2) in enumerate(mid_arrows)))
    ck.ok("下段からの矢印 4 本（相似1・三平方2・円周角1）が下段の箱の上辺から中段の箱の下辺へ",
          len(low_arrows) == 4 and [s for s, _, _ in low_arrows].count(0) == 1 and [s for s, _, _ in low_arrows].count(1) == 2
          and [s for s, _, _ in low_arrows].count(2) == 1
          and all(_on_edge(p1, low_boxes[s][:4], "top") and _on_edge(p2, boxes[t], "bottom") for s, (p1, p2), t in low_arrows))
    ck.ok("下段からの矢印の行き先は 定義 2 本（相似・三平方）・定理 2 本（三平方・円周角）",
          [t for _, _, t in low_arrows].count(0) == 2 and [t for _, _, t in low_arrows].count(2) == 2)
    ck.ok("右端から出る矢印 2 本が 活用 の右辺から出て 数学Ⅱ・数学A の箱の左辺に届く",
          len(right_arrows) == 2 and all(_on_edge(p1, boxes[3], "right") and _on_edge(p2, out_boxes[j][:4], "left")
                                         for j, (p1, p2) in enumerate(right_arrows)))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, size, **kw):
        labels.append(s)
        cv.text(x, y, s, size, **kw)

    in_box = []
    for (name, (a, b), subs), (x, y, w, h) in zip(stages, boxes):
        cv.rect(x, y, w, h, sw=MAIN_W)
        head = f"{name} L{a:02d}〜L{b:02d}"
        T(x + w / 2, y + 26, head, fs_t, weight="bold")
        T(x + w / 2, y + 52, subs[0], fs_s)
        T(x + w / 2, y + 72, subs[1], fs_s)
        in_box += [(head, fs_t, w), (subs[0], fs_s, w), (subs[1], fs_s, w)]
    for (x, y, w, h, s) in out_boxes:
        cv.rect(x, y, w, h, dash=DASH, sw=1.4)
        T(x + w / 2, y + 27, s, fs_s)
        in_box.append((s, fs_s, w))
    for (x, y, w, h, s) in low_boxes:
        cv.rect(x, y, w, h, sw=1.4)
        T(x + w / 2, y + 29, s, fs_s)
        in_box.append((s, fs_s, w))
    ck.ok("箱の中の全テキストの推定幅が箱幅−8 px 未満", all(est_w(s, sz) < w - 8 for s, sz, w in in_box),
          f"{[(s, round(est_w(s, sz)), w) for s, sz, w in in_box if est_w(s, sz) >= w - 8]}")
    for (p1, p2), (l1, l2) in zip(mid_arrows, mid_labels):
        arrow(cv, p1[0], p1[1], p2[0], p2[1], w=1.4)
        xm = (p1[0] + p2[0]) / 2
        T(xm, Y0 - 20, l1, fs_s)
        T(xm, Y0 - 4, l2, fs_s)
    for _, (p1, p2), _ in low_arrows:
        arrow(cv, p1[0], p1[1], p2[0], p2[1], w=1.4)
    for (p1, p2) in right_arrows:
        arrow(cv, p1[0], p1[1], p2[0], p2[1], w=1.4)
    T(112, Y0 + 142, entry_label[0], fs_s, anchor="end")
    T(112, Y0 + 160, entry_label[1], fs_s, anchor="end")
    T(40, ylow - 13, "中学3年", fs_s, anchor="start")
    strip_tokens = {"0°〜180°", "180°−θ", "中学3年", "4段階"}
    rest = "\n".join(labels)
    for tok in strip_tokens:
        rest = rest.replace(tok, "")
    rest = re.sub(r"L\d\d", "", rest)
    ck.ok("数字はレッスン番号・0°〜180°・180°−θ・中学3年・4段階 以外に出ない", not re.search(r"[0-9]", rest), repr(rest))
    cv.layout_checks(ck)

    return {"file": "L12_fig1_unit_map.svg", "lesson": "L12", "canvas": cv,
            "title": "単元マップ——定義・拡張・定理・活用の4段と、中学3年からの入力・数学Ⅱ／数学Aへの出力",
            "desc": "中段に 定義（L01〜L03）・拡張（L04〜L05）・定理（L06〜L09）・活用（L10〜L11）の4つの箱を左から右へ並べ、隣どうしを右向きの矢印3本で結ぶ（矢印の上に、段を進む理由の短い句）。下段の 中学3年 の箱（相似・三平方の定理・円周角の定理）から上向きの矢印4本が中段へ入り（相似→定義に「相似で比が角だけで決まる」の句を添える）、右端の 活用 から破線の箱 数学Ⅱ「三角関数」・数学A「図形の性質」へ矢印2本がのびる。式や例題の数値は書かない。同型の図を描くときは、レッスン番号の範囲が連続で重複しないこと、矢印の本数（3・4・2）を保つ",
            "alt": "単元マップ——定義（L01〜L03）・拡張（L04〜L05）・定理（L06〜L09）・活用（L10〜L11）の4段が左から右へ矢印で結ばれ（相似で比が角だけで決まる→鈍角でも使いたいので座標で定め直す→拡張した三角比で定理を導く→決定条件で定理を選んで計量する）、下から中学3年の相似・三平方の定理・円周角の定理が流れ込み、右端から数学Ⅱ「三角関数」と数学A「図形の性質」へ矢印がのびる",
            "intent": "定義→拡張→定理→活用の4段を1枚の地図にし、段どうしをつなぐ矢印の意味、中学からの入力、数学Ⅱ・数学Aへの出力を示す",
            "src": "lesson_12.md §1 の4段の箇条書きの直後（「4段は、前の段が次の段を支えている。」の段落の前）",
            "params": "中段の箱 4（各 160×90・間隔 50）／矢印 中段 3・下段 4・右端 2／文字は箱の見出し 15 px・副題と矢印ラベル 12.5 px／数字はレッスン番号・0°〜180°・180°−θ・中学3年・4段階 のみ",
            "checks": ck.items,
            "check_tokens": ["2R", "a²", "sin A=", "1/2", "√", "例題"],
            "digit_rule": ("strip", {"0°〜180°", "180°−θ", "中学3年", "4段階"}),
            "deviations": ["文字サイズ 15 px・12.5 px（幅 1020 の 1.5%・1.2%）。3% にすると箱名・矢印ラベルが収まらない（先行単元の単元マップと同じ扱い）",
                           "「相似で比が角だけで決まる」の句は、当初の図版仕様が許す「定義の左に入る入力」として、下段の 相似→定義 の矢印の横に置いた（左端に別の入力矢印を足していない）",
                           "「中学3年」「4段階」は本文の表記どおり算用数字を使った（数字の走査ではこの2語を宣言して除外）"],
            "allow_texts": labels}


# 関数側に deviations を持たない図で仕様から変えた点。台帳の「逸脱」節に載せる
EXTRA_DEVIATIONS = {
    "L04_fig1_circle_point_acute_obtuse.svg": ["文字サイズ 20 px（幅 800 の 2.5%）。24 px だと P(x, y) の左右ラベルが境界で接する"],
    "L04_fig2_circle_points_0_90_180.svg": ["180° の弧の半径を仕様の 44 px から 64 px にした（90° の弧と離して読み分けやすくする）"],
}


# ===========================================================================
# main: 陽性対照 → 生成 → 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_2, fig_L01_1, fig_L02_1, fig_L03_1, fig_L04_1, fig_L04_2, fig_L05_1,
        fig_L06_1, fig_L07_1, fig_L08_1, fig_L09_1, fig_L10_1, fig_L11_1, fig_L12_1]

TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
ALT_RE = re.compile(r"!\[(.*?)\]\(assets/([^)]+)\)")


def svg_texts(src):
    return [unescape(m) for m in TEXT_RE.findall(src)]


def ban_hits(texts, bans):
    joined = "\n".join(texts)
    return [b for b in bans if b in joined]


def char_hygiene(s, where):
    """絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字を拒否する（公開側の検疫と同じ向き）"""
    bad = []
    for i, ch in enumerate(s):
        o = ord(ch)
        cat = unicodedata.category(ch)
        if ch in "\n\t":
            continue
        if cat in ("Cf", "Mn", "Me", "Cc", "Co", "Cn"):
            bad.append((i, hex(o), "invisible/combining"))
        elif 0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF:
            bad.append((i, hex(o), "variation selector"))
        elif 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF:
            bad.append((i, hex(o), "emoji/dingbat"))
        elif 0xFF10 <= o <= 0xFF19 or 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A:
            bad.append((i, hex(o), "fullwidth alphanumeric"))
    assert not bad, f"{where}: 禁止文字 {bad[:5]}"


def gate_self_test():
    """答え漏れ検査器と文字衛生検査器の陽性対照"""
    sample = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
              '<text x="1" y="1">14.0</text><text x="2" y="2">x&lt;0</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["14.0", "x<0"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["14"]) == ["14"], "陽性対照失敗: 禁止値 14 を検出できない"
    assert ban_hits(ts, ["12.5"]) == [], "陰性対照失敗: 存在しない値を誤検出"
    assert digit_runs(ts) == {"14", "0"}, "数字抽出が壊れている"
    probes = ["a" + chr(0x200B) + "b", "e" + chr(0x0301), chr(0x2713) + chr(0xFE0F),
              chr(0xFF21) + chr(0xFF11), chr(0x1F600)]
    for probe in probes:
        try:
            char_hygiene(probe, "陽性対照")
        except AssertionError:
            continue
        raise AssertionError(f"文字衛生の陽性対照失敗: {probe!r} を検出できない")
    char_hygiene("sin θ・√2・²・°・−・′・∠・△・＋・Ⅱ・〜・→", "陰性対照")


def svg_tech_checks(src, meta):
    """生成した SVG 文字列を、ファイルへ書く前に検査する（落ちれば例外で停止し、何も出力しない）"""
    path = Path(meta["file"])
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag, f"{path.name}: viewBox がない"
    assert " width=" not in root_tag and " height=" not in root_tag, f"{path.name}: ルートに width/height を書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, f"{path.name}: 外部参照の疑い"
    assert "font-family" not in src, f"{path.name}: フォント指定は書かない"
    assert "<title>" in src and "<desc>" in src, f"{path.name}: title/desc がない"
    assert '<rect x="0" y="0"' in src and 'fill="#fff"' in src, f"{path.name}: 白背景がない"
    char_hygiene(src, path.name)
    texts = svg_texts(src)
    allow = set(meta["allow_texts"])
    got = set(texts)
    assert got == allow, f"{path.name}: ラベル集合が許可リストと不一致 余分={got - allow} 不足={allow - got}"
    hits = ban_hits(texts, meta.get("check_tokens", []))
    assert not hits, f"{path.name}: 禁止文字列が図中テキストにある: {hits}"
    kind, allowed = meta["digit_rule"]
    runs = digit_runs(texts)
    if kind == "none":
        assert not runs, f"{path.name}: 数字が図中にある: {runs}"
    elif kind == "subset":
        assert runs <= allowed, f"{path.name}: 許可外の数字 {runs - allowed}"
    elif kind == "chars":
        assert set("".join(runs)) <= allowed, f"{path.name}: 許可外の数字文字 {set(''.join(runs)) - allowed}"
    elif kind == "strip":
        rest = "\n".join(texts)
        for tok in allowed:
            rest = rest.replace(tok, "")
        rest = re.sub(r"L\d\d", "", rest)
        assert not re.search(r"[0-9]", rest), f"{path.name}: 宣言外の数字が残る: {rest!r}"
    return len(texts)


def lesson_refs():
    """本文の ![alt](assets/FILE) を実測（ファイル名→alt）。lesson_XX.md が無ければ None"""
    files = sorted(LESSON_DIR.glob("lesson_*.md"))
    if not files:
        return None
    refs = {}
    for f in files:
        for alt, name in ALT_RE.findall(f.read_text(encoding="utf-8")):
            refs[name] = (alt, f.name)
    return refs


def main():
    gate_self_test()
    char_hygiene(Path(__file__).read_text(encoding="utf-8"), "generate_figures.py")
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    pending = []                          # 全図の検査が通ってからまとめて書く
    n_checks = 0
    total_bytes = 0
    for fn in FIGS:
        meta = fn()
        svg1 = meta["canvas"].svg(meta["file"], meta["title"], meta["desc"])
        meta2 = fn()
        svg2 = meta2["canvas"].svg(meta2["file"], meta2["title"], meta2["desc"])
        assert svg1 == svg2, f"{meta['file']}: 同一プロセス内の2回生成が一致しない"
        svg_tech_checks(svg1, meta)          # 書く前に検査（落ちればここで停止し、図は出力されない）
        n_checks += len(meta["checks"])
        total_bytes += len(svg1.encode("utf-8"))
        rows.append(meta)
        pending.append((ASSETS / meta["file"], svg1))
        print(f"OK {meta['file']}  [{len(meta['checks'])} checks passed]")

    # 受け入れ検査（図版仕様の受け入れ項目）: ファイル名の一致・alt の一致
    refs = lesson_refs()
    accept = []
    if refs is None:
        accept.append("本文 lesson_XX.md がこの階層に無いため、参照名・alt の照合は未実施")
    else:
        mine = {m["file"] for m in rows}
        theirs = set(refs)
        if mine == theirs:
            accept.append(f"本文の図参照 {len(theirs)} 件と生成ファイル {len(mine)} 件が完全一致（差集合 空）")
        else:
            accept.append(f"参照と生成の差: 本文のみ={sorted(theirs - mine)} 生成のみ={sorted(mine - theirs)}")
        for m in rows:
            if m["file"] in refs:
                alt, src = refs[m["file"]]
                assert alt == m["alt"], f"{m['file']}: alt が本文（{src}）と不一致\n本文: {alt}\n仕様: {m['alt']}"
        accept.append("alt 文: 生成した全図で本文の alt とバイト単位で一致（assert）")
    for line in accept:
        print("ACCEPT", line)
    # ここまでの検査（幾何 assert・技術検査・答え漏れ検査・alt 照合）が全部通った後にだけ書き出す
    for out, svg in pending:
        out.write_text(svg, encoding="utf-8")
    write_manifest(rows, n_checks, total_bytes, accept)
    print(f"TOTAL {len(rows)} figures, {total_bytes} bytes, {n_checks} checks")
    return rows, n_checks, total_bytes, accept


def write_manifest(rows, n_checks, total_bytes, accept):
    """FIGURE_MANIFEST.md（図版台帳）を生成する。手編集禁止——スクリプトを直して再実行"""
    n_tokens = sum(len(m.get("check_tokens", [])) for m in rows)
    head = ["---", "distribution_status: published_draft", "---", "", "<!--",
            f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
            "spec: docs/SPEC_figures.md 準拠",
            "license: CC-BY-4.0", "-->", ""]
    lines = head + [
        "# FIGURE_MANIFEST — 数Ⅰ 図形と計量（三角比）単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト。下表の数学検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。加えて全SVGに XML整形式・viewBox・width/height なし・self-contained・"
        "`<title>`/`<desc>`・白背景・フォント指定なし の技術検査と、文字衛生検査"
        "（絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字の不在）と、答え漏れ検査を実施。"
        "答え漏れ検査は二重ゲート: (1)図中の全ラベルを許可リスト（本文が図の前後で明示している値のみ）と"
        f"集合として完全一致で照合、(2)禁止文字列（練習・例題の答え由来・計{n_tokens}項目・対象値は非開示）の"
        "不在検査と、図ごとの数字集合の制約。検査器自体は生成前の陽性対照（禁止値・禁止文字を仕込んだ合成入力での検出）で"
        "毎回実証している。PASS。／ AI再利用メタ情報として全SVGに `<title>`/`<desc>`"
        "（意図・主要数値・同型図を描かせる説明文）を標準装備。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | alt（本文と同一） | パラメータ（本文一致） | 検証結果（生成時 assert） |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} 合格" for d, t in m["checks"])
        lines.append(f"| `{m['file']}` | {m['lesson']} | {m['title']}——{m['intent']} | "
                     f"{m['src']} | {m['alt']} | {m['params']} | {checks} |")
    lines += ["", "## 受け入れ検査（図版仕様の受け入れ項目）の結果", ""]
    for line in accept:
        lines.append(f"- {line}")
    lines += [
        f"- 各SVG: XML整形式・xmlns と viewBox あり・width/height なし・外部参照なし・`<title>`/`<desc>` あり・"
        f"白背景 rect あり・font-family なし（{len(rows)} 枚全件・スクリプトの技術検査で assert）",
        f"- 各図の assert が生成時に全件通過（計 {n_checks} 項目・上表）",
        "- 答え漏れ検査: `<text>` の文字列集合が各図の許可集合と完全一致・禁止文字列 0 件・数字集合の制約を満たす（全図 assert）",
        "- 決定性: 同一プロセス内で各図を2回生成してバイト一致を assert。別プロセスでの再実行の一致は、"
        "出荷時に全SVGと本台帳の sha256 を2回とって照合する（生成日は日付のみなので同日なら一致。"
        "台帳に載せる集合は整列して書くので、実行ごとの要素順の差は出ない）",
        "- 図数の照合: 本文の図参照と生成ファイルの差集合が空（上の1行目）",
        "",
        "## 逸脱（docs/SPEC_figures.md・当初の図版仕様からの差）",
        "",
    ]
    n_dev = 0
    for m in rows:
        devs = list(m.get("deviations", [])) + EXTRA_DEVIATIONS.get(m["file"], [])
        for d in devs:
            lines.append(f"- `{m['file']}`: {d}")
            n_dev += 1
    lines += [
        "- 共通: 当初の図版仕様の色による対応づけ（同じ色の弧など）は白黒規約により使わず、線幅・破線・弧の本数で置き換えた。"
        "当初の図版仕様の px 座標は目安として扱い、変換関数 Frame.P から出した座標を用いた（幾何の包含関係と assert 条件は変えていない）",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値は、いずれも本文（例題の与件・図の前後の明示値）のみ。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- L06_fig1・L07_fig1 は一般の三角形として描き、数字は「180」のみ。L08_fig1 は例題4の解説の後に置く確認図で、与件 2・2√2・30° と、本文が図の直前で答えとして示す角 B の 45°・135° を載せる（例題4の答えのうち、角 B だけは図にある）。辺 AB・AB′ の長さ（例題4の答えの辺 c）にはラベルを付けない。",
        "- L09_fig1 の「6」は例題1(1) の辺 BC の長さで、練習 問1(1) の答え 6 と同じ文字列になる（当初の図版仕様の注記どおり辺に添える。気になる場合は左パネルの辺ラベル 6 を落とせる）。",
        "- L10_fig1 は解く前の図で、例題1の与件 60 m・45°・75° と、本文が図の直後に 180° から引いて出す残りの角 60° を書き、PB・PA・川幅の値は書かない。L11_fig1 は例題3の与件の 1辺 6 と、本文が図の直後に理由をつけて導く BN=3・∠HBN=30° のみで、BH・AH・体積は書かない。L12_fig1 は式・数値を書かない（レッスン番号と本文表記の 0°〜180°・180°−θ・中学3年・4段階 のみ）。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する（数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算 assert・技術検査・答え漏れ検査・alt 照合に1つでも落ちると、SVG も本ファイルも書き出されない（既存の出力は前回のまま残る）。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    text = "\n".join(lines)
    char_hygiene(text, "FIGURE_MANIFEST.md")
    (HERE / "FIGURE_MANIFEST.md").write_text(text, encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks, {n_tokens} ban-tokens, {n_dev} deviations)")


if __name__ == "__main__":
    main()
