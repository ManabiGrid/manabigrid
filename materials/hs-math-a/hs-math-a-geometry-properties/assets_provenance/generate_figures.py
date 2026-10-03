#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高校 数学A「図形の性質」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。描画ヘルパー（Canvas / Frame / Checker / 許可リスト検査 /
禁止文字列検査 / 文字衛生検査 / 陽性対照 / FIGURE_MANIFEST 自動生成）は先行単元
materials/hs-math-i/hs-math-i-trigonometric-ratios/assets_provenance/generate_figures.py
の構造を踏襲し、立体は頂点座標からの斜投影（中1 空間図形と同じ見取図の描法）で描く。
凸多面体の面は頂点座標から支持平面を探して機械的に求め、隠れ線は面の可視判定から決める。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（36枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / unicodedata / xml.etree / itertools）
- 座標の与え方: 本文明示値（辺の長さ・比）をパラメータに書き、数学座標→px の変換関数
  Frame.P を通して描く。検算 assert は数学座標で照合する。
- 幾何の自己検証: 各 fig_* 関数内の Checker が検算項目（外心の等距離・チェバの積・方べきの積・
  オイラーの式など）を検算し、1つでも失敗すると例外で停止して図を出力しない。
- 答えの分離（二重ゲート＋陽性対照）:
  (1) 許可リスト検査——各図が宣言した「使ってよいラベル集合」(allow_texts) と
      生成後 SVG の <text> 全内容が集合として完全一致することを検査する。
  (2) 禁止文字列検査——例題・練習の答え由来の禁止文字列 (check_tokens) が図中テキストに現れないこと、
      および各図の「数字の集合」制約 (digit_rule) を検査する。
  検査器は main() 冒頭の陽性対照（禁止値を仕込んだ合成 SVG で検出できること）で毎回実証する。
- 文字衛生: 絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字を、本スクリプト自身と
  全 SVG・台帳に対して機械検査する。
- 決定性: 乱数を使わない。集合は必ず整列してから出力する。日付は「生成日」行と各 SVG 先頭コメントだけ。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
"""

import datetime
import itertools
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSON_DIR = HERE.parent          # 作業フォルダでも公開側の単元フォルダでも lesson_XX.md はこの階層
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md の規約） --------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅（破線）
DASH = "6 4"      # 破線
DIM_W = 1.0       # 寸法線
DOT_R = 2.5       # 点マーカー半径
RA_SIZE = 11.0    # 直角マークの一辺（px）
ARC_W = 1.2       # 角の弧の線幅
SHADE = "#e6e6e6"  # うすい網かけ
DEG = math.pi / 180.0
SQ2, SQ3, SQ5 = math.sqrt(2), math.sqrt(3), math.sqrt(5)
PHI = (1 + SQ5) / 2


def fs_for(width):
    """基本文字サイズ = viewBox 幅の 3 パーセント（四捨五入）"""
    return round(width * 0.03)


# ===========================================================================
# 幾何ユーティリティ（2次元・数学座標）
# ===========================================================================
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, k):
    return (a[0] * k, a[1] * k)


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def mid(a, b, t=0.5):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def unit(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


def perp(v):
    return (-v[1], v[0])


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


def near_pt(p, q, tol=1e-9):
    return dist(p, q) < tol


def angle_at(v, p, q):
    """頂点 v で辺 vp・vq がつくる角（度・0〜180）"""
    a = math.atan2(p[1] - v[1], p[0] - v[0])
    b = math.atan2(q[1] - v[1], q[0] - v[0])
    d = abs(b - a) % (2 * math.pi)
    return math.degrees(min(d, 2 * math.pi - d))


def line_x(p1, p2, q1, q2):
    """直線 p1p2 と直線 q1q2 の交点（平行なら None）"""
    d1, d2 = sub(p2, p1), sub(q2, q1)
    den = cross(d1, d2)
    if abs(den) < 1e-12:
        return None
    t = cross(sub(q1, p1), d2) / den
    return add(p1, mul(d1, t))


def param_on(p, a, b):
    """点 p（直線 ab 上）の位置パラメータ t（p = a + t(b−a)）"""
    d = sub(b, a)
    return dot(sub(p, a), d) / dot(d, d)


def foot(p, a, b):
    """点 p から直線 ab へ下ろした垂線の足"""
    t = param_on(p, a, b)
    return add(a, mul(sub(b, a), t))


def dist_line(p, a, b):
    return dist(p, foot(p, a, b))


def divide(a, b, m, n, internal=True):
    """線分 ab を m:n に内分（(n·a＋m·b)/(m＋n)）・外分（(−n·a＋m·b)/(m−n)）する点"""
    if internal:
        return ((n * a[0] + m * b[0]) / (m + n), (n * a[1] + m * b[1]) / (m + n))
    return ((-n * a[0] + m * b[0]) / (m - n), (-n * a[1] + m * b[1]) / (m - n))


def circumcenter(a, b, c):
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    ux = ((a[0] ** 2 + a[1] ** 2) * (b[1] - c[1]) + (b[0] ** 2 + b[1] ** 2) * (c[1] - a[1])
          + (c[0] ** 2 + c[1] ** 2) * (a[1] - b[1])) / d
    uy = ((a[0] ** 2 + a[1] ** 2) * (c[0] - b[0]) + (b[0] ** 2 + b[1] ** 2) * (a[0] - c[0])
          + (c[0] ** 2 + c[1] ** 2) * (b[0] - a[0])) / d
    return (ux, uy)


def incenter(a, b, c):
    la, lb, lc = dist(b, c), dist(c, a), dist(a, b)
    s = la + lb + lc
    return ((la * a[0] + lb * b[0] + lc * c[0]) / s, (la * a[1] + lb * b[1] + lc * c[1]) / s)


def centroid(a, b, c):
    return ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3)


def on_circle(p, c, r, tol=1e-9):
    return abs(dist(p, c) - r) < tol


def circle_line(c, r, a, b):
    """円（中心 c 半径 r）と直線 ab の交点を、a から b の向きのパラメータ順に返す"""
    d = sub(b, a)
    f = sub(a, c)
    A = dot(d, d)
    B = 2 * dot(f, d)
    C = dot(f, f) - r * r
    disc = B * B - 4 * A * C
    if disc < 0:
        return []
    s = math.sqrt(disc)
    ts = sorted([(-B - s) / (2 * A), (-B + s) / (2 * A)])
    return [add(a, mul(d, t)) for t in ts]


def circle_circle(c1, r1, c2, r2):
    """2円の交点（2点・無ければ空）"""
    d = dist(c1, c2)
    if d > r1 + r2 + 1e-12 or d < abs(r1 - r2) - 1e-12 or d == 0:
        return []
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h2 = r1 * r1 - a * a
    h = math.sqrt(max(h2, 0.0))
    p = add(c1, mul(unit(sub(c2, c1)), a))
    n = perp(unit(sub(c2, c1)))
    return [add(p, mul(n, h)), add(p, mul(n, -h))]


def same_side(p, q, a, b):
    """p, q が直線 ab について同じ側にあるか"""
    return cross(sub(b, a), sub(p, a)) * cross(sub(b, a), sub(q, a)) > 0


def pt_on_circle(c, r, deg):
    return (c[0] + r * math.cos(deg * DEG), c[1] + r * math.sin(deg * DEG))


def bisector_dir(v, p, q):
    """頂点 v の角 pvq の内角二等分線の向き（単位ベクトル）"""
    return unit(add(unit(sub(p, v)), unit(sub(q, v))))


# ---- 3次元（斜投影） ------------------------------------------------------
def v3(a, b):
    return (b[0] - a[0], b[1] - a[1], b[2] - a[2])


def dot3(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def cross3(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def dist3(a, b):
    return math.sqrt(dot3(v3(a, b), v3(a, b)))


def norm3(u):
    L = math.sqrt(dot3(u, u)) or 1.0
    return (u[0] / L, u[1] / L, u[2] / L)


def add3(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2])


def mean3(ps):
    n = len(ps)
    return (sum(p[0] for p in ps) / n, sum(p[1] for p in ps) / n, sum(p[2] for p in ps) / n)


def rot_z(p, deg):
    c, s = math.cos(deg * DEG), math.sin(deg * DEG)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])


def rot_x(p, deg):
    c, s = math.cos(deg * DEG), math.sin(deg * DEG)
    return (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)


class Oblique:
    """斜投影: x 右・y 奥行き・z 上 → 平面 (X, Y)。X = x + k·y·cos α、Y = z + k·y·sin α。
    投影方向は (−k cos α, 1, −k sin α) なので、面の可視判定は外向き法線と (k cos α, −1, k sin α) の内積で行う"""
    def __init__(self, k=0.5, alpha=30.0):
        self.k, self.alpha = k, alpha
        self.view = (k * math.cos(alpha * DEG), -1.0, k * math.sin(alpha * DEG))

    def P(self, p):
        return (p[0] + self.k * p[1] * math.cos(self.alpha * DEG), p[2] + self.k * p[1] * math.sin(self.alpha * DEG))

    def visible(self, n_out):
        return dot3(n_out, self.view) > 1e-9


def hull_faces(verts, tol=1e-7):
    """凸多面体の面を頂点座標だけから求める（支持平面の探索）。各面は反時計回り（外向き法線）に整列した頂点番号列"""
    cen = mean3(verts)
    found = {}
    for i, j, k in itertools.combinations(range(len(verts)), 3):
        n = cross3(v3(verts[i], verts[j]), v3(verts[i], verts[k]))
        L = math.sqrt(dot3(n, n))
        if L < tol:
            continue
        n = (n[0] / L, n[1] / L, n[2] / L)
        ds = [dot3(n, v3(verts[i], q)) for q in verts]
        if all(d <= tol for d in ds) or all(d >= -tol for d in ds):
            members = tuple(sorted(m for m, d in enumerate(ds) if abs(d) <= tol))
            if members in found:
                continue
            if dot3(n, v3(cen, verts[i])) < 0:
                n = (-n[0], -n[1], -n[2])
            fc = mean3([verts[m] for m in members])
            e1 = norm3(v3(fc, verts[members[0]]))
            e2 = cross3(n, e1)
            order = sorted(members, key=lambda m: math.atan2(dot3(v3(fc, verts[m]), e2), dot3(v3(fc, verts[m]), e1)))
            found[members] = (tuple(order), n)
    return [found[m] for m in sorted(found)]


def solid_edges(faces):
    """面の頂点番号列から辺（頂点番号の組・整列済み）→ 隣接面番号の一覧"""
    edges = {}
    for fi, (order, _) in enumerate(faces):
        for a in range(len(order)):
            e = tuple(sorted((order[a], order[(a + 1) % len(order)])))
            edges.setdefault(e, []).append(fi)
    return [(e, edges[e]) for e in sorted(edges)]


def draw_solid(cv, fr, ob, verts, faces, w=MAIN_W, fill_faces=None):
    """凸多面体を斜投影で描く。可視面に接する辺は実線、どの可視面にも接さない辺は破線。
    fill_faces: 網かけする面番号の集合（可視面のみ）。辺の一覧（整列）を返す"""
    vis = [ob.visible(n) for _, n in faces]
    if fill_faces:
        for fi in sorted(fill_faces):
            if vis[fi]:
                cv.polygon_fill([fr.P(ob.P(verts[m])) for m in faces[fi][0]], SHADE)
    edges = solid_edges(faces)
    for (a, b), fis in edges:
        if any(vis[f] for f in fis):
            seg(cv, fr, ob.P(verts[a]), ob.P(verts[b]), w=w)
        else:
            seg(cv, fr, ob.P(verts[a]), ob.P(verts[b]), w=AUX_W, dash=DASH)
    return edges, vis


# ===========================================================================
# 文字幅推定・数字抽出
# ===========================================================================
def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・記号は個別"""
    special = {"°": 0.45, "′": 0.3, "²": 0.45, "√": 0.8, "−": 0.6, " ": 0.35, ".": 0.3, ",": 0.3,
               "/": 0.4, "(": 0.4, ")": 0.4, "₁": 0.45, "₂": 0.45, "₃": 0.45, "₄": 0.45, "₅": 0.45,
               "₆": 0.45, "₇": 0.45, "ℓ": 0.5, "α": 0.6, "β": 0.6, "∠": 0.9, "△": 0.9, "⊥": 0.9, "∥": 0.7}
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
    out = set()
    for t in texts:
        out.update(re.findall(r"[0-9]+", t))
    return out


def show_set(s):
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
        self.texts = []
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
        self._grow(x, y, r + w)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" stroke="#000" stroke-width="{w}"/>')

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
        ck.ok("全要素が viewBox 内に収まる（線幅・推定文字幅込み）",
              self.bbox[0] >= 0 and self.bbox[1] >= 0 and self.bbox[2] <= self.w and self.bbox[3] <= self.h,
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


def poly(cv, fr, pts, w=MAIN_W, close=True, dash=None):
    cv.polyline([fr.P(p) for p in pts], w=w, close=close, dash=dash)


def fill_poly(cv, fr, pts, fill=SHADE):
    cv.polygon_fill([fr.P(p) for p in pts], fill)


def dot_m(cv, fr, p, r=DOT_R):
    x, y = fr.P(p)
    cv.dot(x, y, r)


def circle_path(cv, fr, c, r, w=MAIN_W, step_deg=2, dash=None):
    """円の点を step_deg 刻みでサンプリングした閉じた折れ線（arc フラグ不使用）"""
    n = int(round(360 / step_deg))
    pts = [fr.P((c[0] + r * math.cos(i * step_deg * DEG), c[1] + r * math.sin(i * step_deg * DEG))) for i in range(n)]
    cv.polyline(pts, w=w, close=True, dash=dash)


def arc_m(cv, fr, c, r, deg_from, deg_to, w=MAIN_W, dash=None, step=2):
    """数学座標の円弧（反時計回り deg_from→deg_to）を折れ線で描く"""
    span = (deg_to - deg_from) % 360.0 or 360.0
    k = max(6, int(math.ceil(span / step)))
    pts = [fr.P(pt_on_circle(c, r, deg_from + span * i / k)) for i in range(k + 1)]
    cv.polyline(pts, w=w, dash=dash)


def math_deg(v_px, p_px):
    """px 座標で v から p への向きを数学の角（度・反時計回り）で返す"""
    return math.degrees(math.atan2(-(p_px[1] - v_px[1]), p_px[0] - v_px[0])) % 360.0


def arc_px(cv, cx, cy, r, deg_from, deg_to, n=1, gap=4.0, w=ARC_W):
    span = deg_to - deg_from
    k = max(6, int(math.ceil(abs(span) / 5.0)))
    for j in range(n):
        rr = r + j * gap
        pts = [(cx + rr * math.cos((deg_from + span * i / k) * DEG),
                cy - rr * math.sin((deg_from + span * i / k) * DEG)) for i in range(k + 1)]
        cv.polyline(pts, w=w)


def angle_arc(cv, fr, v, p, q, r, n=1):
    """頂点 v で辺 vp→vq の劣角に弧（px 半径 r）を n 重に描く。弧の中央の px 位置を返す"""
    vx, vy = fr.P(v)
    a1 = math_deg((vx, vy), fr.P(p))
    a2 = math_deg((vx, vy), fr.P(q))
    d = (a2 - a1) % 360.0
    if d > 180.0:
        a1, d = a2, 360.0 - d
    arc_px(cv, vx, vy, r, a1, a1 + d, n=n)
    am = (a1 + d / 2) * DEG
    return (vx + r * math.cos(am), vy - r * math.sin(am))


def right_angle(cv, fr, v, p, q, size=RA_SIZE):
    """頂点 v の直角マーク。p, q は直交する2辺の先の点（数学座標）"""
    vx, vy = fr.P(v)
    u = unit(sub(fr.P(p), (vx, vy)))
    w_ = unit(sub(fr.P(q), (vx, vy)))
    cv.polyline([(vx + u[0] * size, vy + u[1] * size),
                 (vx + (u[0] + w_[0]) * size, vy + (u[1] + w_[1]) * size),
                 (vx + w_[0] * size, vy + w_[1] * size)], w=1.2)


def tick(cv, fr, a, b, n=1, t=0.5, size=5.0, gap=4.0):
    """線分 ab の位置 t に、辺と交差する短い線（対応する辺のしるし）を n 本"""
    A, B = fr.P(a), fr.P(b)
    d = unit(sub(B, A))
    nv = perp(d)
    m = mid(A, B, t)
    for j in range(n):
        off = (j - (n - 1) / 2) * gap
        c = (m[0] + d[0] * off, m[1] + d[1] * off)
        cv.line(c[0] - nv[0] * size, c[1] - nv[1] * size, c[0] + nv[0] * size, c[1] + nv[1] * size, w=1.2)


def par_mark(cv, fr, a, b, n=1, t=0.5, size=6.0, gap=5.0):
    """線分 ab の位置 t に、a→b の向きの矢羽（平行のしるし）を n 個"""
    A, B = fr.P(a), fr.P(b)
    d = unit(sub(B, A))
    nv = perp(d)
    m = mid(A, B, t)
    for j in range(n):
        off = (j - (n - 1) / 2) * gap
        c = (m[0] + d[0] * off, m[1] + d[1] * off)
        cv.polyline([(c[0] - d[0] * size + nv[0] * size, c[1] - d[1] * size + nv[1] * size), c,
                     (c[0] - d[0] * size - nv[0] * size, c[1] - d[1] * size - nv[1] * size)], w=1.2)


def label_out(cv, fr, p, centroid_, s, fs, dist_=16.0, weight="bold"):
    """頂点名: 重心から離れる向きに dist_ px ずらして図形の外側に置く"""
    x, y = fr.P(p)
    cx, cy = fr.P(centroid_)
    d = unit((x - cx, y - cy))
    cv.text(x + d[0] * dist_, y + d[1] * dist_ + fs * 0.35, s, fs, weight=weight)


def label_dir(cv, fr, p, deg, r, s, fs, anchor="middle", weight=None):
    """点 p から数学の角 deg の向きに r px 離れた位置を中心にラベルを置く"""
    x, y = fr.P(p)
    cv.text(x + r * math.cos(deg * DEG), y - r * math.sin(deg * DEG) + fs * 0.35, s, fs, anchor=anchor, weight=weight)


def side_label(cv, fr, p, q, away, s, fs, off=14.0, t=0.5, anchor="middle"):
    """線分 pq の位置 t から、点 away と反対側へ法線方向に off px ずらしてラベルを置く"""
    a, b, c = fr.P(p), fr.P(q), fr.P(away)
    m = mid(a, b, t)
    d = unit(sub(b, a))
    n = (-d[1], d[0])
    if dot(n, sub(c, m)) > 0:
        n = (-n[0], -n[1])
    cv.text(m[0] + n[0] * off, m[1] + n[1] * off + fs * 0.35, s, fs, anchor=anchor)


def arrow(cv, x1, y1, x2, y2, w=1.4, head=7.0):
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.line(x1, y1, bx, by, w=w)
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.polygon_fill([(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
                     (bx - nx * head * 0.45, by - ny * head * 0.45)], "#000")


def caption(cv, x, y, s, fs, labels, anchor="middle", weight=None):
    labels.append(s)
    cv.text(x, y, s, fs, anchor=anchor, weight=weight)


class Checker:
    """幾何検算の記録つき assert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


def T_factory(cv, labels, fs):
    def T(x, y, s, size=None, **kw):
        labels.append(s)
        cv.text(x, y, s, size or fs, **kw)
    return T


# 内分・外分の共通パラメータ（L01_fig1 と L10_fig1 で同じ点を使う）
DIV_A, DIV_B, DIV_M, DIV_N = (0.0, 0.0), (6.0, 0.0), 2, 1


# ===========================================================================
# L01 三角形（内分・外分／角の二等分線と比）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md §2 内分・外分の3状態） ---
    A, B, m, n = DIV_A, DIV_B, DIV_M, DIV_N        # AB を 2:1 に内分／2:1 に外分／1:2 に外分
    W, H = 640, 300
    s = 24.0                                       # px/単位
    rows = [("P", m, n, True, "2:1に内分"), ("Q", m, n, False, "2:1に外分"), ("R", n, m, False, "1:2に外分")]
    ys = [70, 150, 230]                            # 3段の px 高さ（上から内分・外分B側・外分A側）
    x0 = 200                                       # A の px x（R=−6 が x=56 px・Q=12 が x=488 px）
    fs = fs_for(W)

    ck = Checker()
    P = divide(A, B, m, n, True)
    Q = divide(A, B, m, n, False)
    R = divide(A, B, n, m, False)
    ck.ok("P=(nA＋mB)/(m＋n)=(4,0)・AP:PB=2:1", near_pt(P, (4.0, 0.0)) and near(dist(A, P) / dist(P, B), 2.0))
    ck.ok("Q=(−nA＋mB)/(m−n)=(12,0)・AQ:QB=2:1・Q は B の側の延長上",
          near_pt(Q, (12.0, 0.0)) and near(dist(A, Q) / dist(Q, B), 2.0) and param_on(Q, A, B) > 1)
    ck.ok("R=(−mA＋nB)/(n−m)=(−6,0)・AR:RB=1:2・R は A の側の延長上",
          near_pt(R, (-6.0, 0.0)) and near(dist(A, R) / dist(R, B), 0.5) and param_on(R, A, B) < 0)
    ck.ok("内分は AP＋PB=AB・外分は AQ−QB=AB・RB−AR=AB",
          near(dist(A, P) + dist(P, B), dist(A, B)) and near(dist(A, Q) - dist(Q, B), dist(A, B))
          and near(dist(R, B) - dist(A, R), dist(A, B)))

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    pts = {"P": P, "Q": Q, "R": R}
    for (name, _, _, internal, cap), y in zip(rows, ys):
        fr = Frame(x0, y, s)
        X = pts[name]
        lo = min(A[0], B[0], X[0]) - 0.6
        hi = max(A[0], B[0], X[0]) + 0.6
        seg(cv, fr, (lo, 0), (hi, 0), w=AUX_W, dash=DASH)
        seg(cv, fr, A, B, w=BOLD_W)
        for p, lab in ((A, "A"), (B, "B"), (X, name)):
            dot_m(cv, fr, p)
            labels.append(lab)
            label_dir(cv, fr, p, 90, 16, lab, fs, weight="bold")
        # 比のしるし: 長い方（m 側）に2本・短い方（n 側）に1本のティックはつけず、区間の下に矢印と比を書く
        ya = y + 18
        a_px, x_px, b_px = fr.P(A), fr.P(X), fr.P(B)
        for (u, v) in ((a_px, x_px), (x_px, b_px)):
            arrow(cv, u[0], ya, v[0], ya, w=1.1, head=6.0)
            arrow(cv, v[0], ya, u[0], ya, w=1.1, head=6.0)
        T(530, y + fs * 0.35, cap, anchor="start")
    ck.ok("図中の数字は比 2・1 のみ", digit_runs(labels) <= {"1", "2"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L01_fig1_internal_external_division.svg", "lesson": "L01", "canvas": cv,
            "title": "線分 AB の内分点 P（2:1）・外分点 Q（2:1・B の側）・外分点 R（1:2・A の側）の3状態",
            "desc": "同じ線分 AB を3段に描き、上段に 2:1 の内分点 P、中段に 2:1 の外分点 Q（B を越えた側）、下段に 1:2 の外分点 R（A の手前側）を置く。各段の下に A→分点・分点→B の2区間を両矢印で示す。長さの数値は書かない。同型図は m:n と A, B の座標を差し替えて生成する",
            "alt": "線分ABを2:1に内分する点P、2:1に外分する点Q（Bの側の延長上）、1:2に外分する点R（Aの側の延長上）の3状態",
            "intent": "内分・外分の定義（AP:PB=m:n・AQ:QB=m:n）と、外分点が m>n なら B の側・m<n なら A の側に来ることを3状態で見せる",
            "src": "lesson_01.md §2（外分点の側の箇条書きの直後・例題1の前）",
            "params": "A=(0,0)・B=(6,0)・24 px/単位／P=2:1 内分・Q=2:1 外分・R=1:2 外分／ラベルは A・B・P・Q・R と 2:1に内分・2:1に外分・1:2に外分",
            "checks": ck.items,
            "check_tokens": ["AP=4", "PB=2", "AQ=12", "QB=6", "AR=6", "RB=12", "=6", "12"],
            "digit_rule": ("subset", {"1", "2"}),
            "allow_texts": labels}


def _tri_from_sides(ab, ac, bc):
    """B=(0,0)・C=(bc,0) とし、AB=ab・AC=ac となる A（上側）を返す"""
    x = (ab * ab - ac * ac + bc * bc) / (2 * bc)
    y = math.sqrt(ab * ab - x * x)
    return (x, y)


def fig_L01_2():
    # --- パラメータ（lesson_01.md §3 定理1の証明図・例題2の与件 AB=6・AC=4・BC=5） ---
    AB, AC, BC = 6.0, 4.0, 5.0
    W, H = 640, 420
    fr = Frame(130, 360, 40)                       # B=(130,360) px・40 px/単位
    fs = fs_for(W)

    B, C = (0.0, 0.0), (BC, 0.0)
    A = _tri_from_sides(AB, AC, BC)
    # 二等分線 AD（D は BC 上）と、C を通り AD に平行な直線と BA の延長（A の側）との交点 E
    D = line_x(A, add(A, bisector_dir(A, B, C)), B, C)
    E = line_x(C, add(C, sub(D, A)), B, A)

    ck = Checker()
    ck.ok("AB=6・AC=4・BC=5（座標から・1e-9）", near(dist(A, B), AB) and near(dist(A, C), AC) and near(dist(B, C), BC))
    ck.ok("D は辺 BC 上（0<t<1）", 0 < param_on(D, B, C) < 1)
    ck.ok("BD:DC=AB:AC（数値照合・1e-9）", near(dist(B, D) / dist(D, C), AB / AC))
    ck.ok("∠BAD=∠DAC（二等分・1e-9）", near(angle_at(A, B, D), angle_at(A, D, C)))
    ck.ok("EC∥AD（外積 0）", near(cross(sub(E, C), sub(D, A)), 0.0))
    ck.ok("E は BA を A の側に延長した直線上（t>1）", param_on(E, B, A) > 1)
    ck.ok("AE=AC（二等辺・1e-9）", near(dist(A, E), AC))
    ck.ok("∠AEC=∠ACE（1e-9）", near(angle_at(E, A, C), angle_at(C, A, E)))

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    poly(cv, fr, [A, B, C])
    seg(cv, fr, A, D)
    seg(cv, fr, A, E, w=AUX_W, dash=DASH)
    seg(cv, fr, C, E, w=AUX_W, dash=DASH)
    par_mark(cv, fr, A, D, n=1, t=0.55)
    par_mark(cv, fr, E, C, n=1, t=0.5)
    angle_arc(cv, fr, A, B, D, r=22, n=1)
    angle_arc(cv, fr, A, D, C, r=22, n=1)
    angle_arc(cv, fr, E, A, C, r=22, n=2)
    angle_arc(cv, fr, C, A, E, r=22, n=2)
    for p in (A, B, C, D, E):
        dot_m(cv, fr, p)
    G = centroid(A, B, C)
    label_out(cv, fr, B, G, "B", fs, dist_=18)
    label_out(cv, fr, C, G, "C", fs, dist_=18)
    label_dir(cv, fr, A, 0, 20, "A", fs, weight="bold")
    label_dir(cv, fr, D, 270, 18, "D", fs, weight="bold")
    label_dir(cv, fr, E, 90, 18, "E", fs, weight="bold")
    for p, lab in ((A, "A"), (B, "B"), (C, "C"), (D, "D"), (E, "E")):
        labels.append(lab)
    ck.ok("図中ラベルに数字を含まない（BD・DC の値は書かない）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L01_fig2_bisector_ratio_interior.svg", "lesson": "L01", "canvas": cv,
            "title": "内角の二等分線と辺の比——△ABC の ∠A の二等分線 AD と、C を通り AD に平行な補助線 CE",
            "desc": "AB=6・AC=4・BC=5 の △ABC（B 左下・C 右下・A 上）に ∠A の二等分線 AD を引き、C を通り AD に平行な補助線を破線で引いて、BA を A の側に延長した直線との交点 E を置く。∠BAD・∠DAC に1重の弧、∠AEC・∠ACE に2重の弧、AD と EC に矢羽。長さの数値は書かない（BD・DC は例題2の答え）。同型図は3辺の長さを差し替えて生成する",
            "alt": "△ABCの∠Aの二等分線ADと、Cを通りADに平行な補助線——BD:DC=AB:ACが平行線と比で読める",
            "intent": "定理1の証明の補助線（C を通り AD に平行）と、それが作る二等辺三角形 ACE（AE=AC）を見せ、BD:DC=BA:AE=AB:AC の読み取りを支える",
            "src": "lesson_01.md §3（定理1の穴埋め証明の直後）",
            "params": "AB=6・AC=4・BC=5（例題2の与件）／B=(0,0)・C=(5,0)・A は座標計算／D=二等分線と BC の交点・E=C を通り AD に平行な直線と直線 BA の交点／40 px/単位／ラベルは A〜E のみ",
            "checks": ck.items,
            "check_tokens": ["BD=3", "DC=2", "3:2", "6:4"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L01_3():
    # --- パラメータ（lesson_01.md §4 定理2の証明図・例題3の与件 AB=6・AC=4・BC=5） ---
    AB, AC, BC = 6.0, 4.0, 5.0
    W, H = 640, 360
    fr = Frame(60, 280, 36)                        # B=(60,280) px・36 px/単位（E まで x=15 で 600 px）
    fs = fs_for(W)

    B, C = (0.0, 0.0), (BC, 0.0)
    A = _tri_from_sides(AB, AC, BC)
    X = add(A, mul(unit(sub(A, B)), 2.2))          # BA を A の側に延長した半直線上の点
    ext_dir = bisector_dir(A, X, C)                # 外角 ∠CAX の二等分線の向き
    E = line_x(A, add(A, ext_dir), B, C)
    F = line_x(C, add(C, ext_dir), A, B)           # C を通り AE に平行な直線と辺 AB の交点

    ck = Checker()
    ck.ok("AB=6・AC=4・BC=5（座標から・1e-9）", near(dist(A, B), AB) and near(dist(A, C), AC) and near(dist(B, C), BC))
    ck.ok("∠XAE=∠EAC（外角の二等分・1e-9）", near(angle_at(A, X, E), angle_at(A, E, C)))
    ck.ok("E は辺 BC を C の側に延長した直線上（t>1）", param_on(E, B, C) > 1)
    ck.ok("BE:EC=AB:AC（数値照合・1e-9）", near(dist(B, E) / dist(E, C), AB / AC))
    ck.ok("BE−EC=BC（外分・1e-9）", near(dist(B, E) - dist(E, C), BC))
    ck.ok("FC∥AE（外積 0）・F は辺 AB 上", near(cross(sub(F, C), ext_dir), 0.0) and 0 < param_on(F, A, B) < 1)
    ck.ok("AF=AC（二等辺・1e-9）・∠AFC=∠ACF", near(dist(A, F), AC) and near(angle_at(F, A, C), angle_at(C, A, F)))

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    poly(cv, fr, [A, B, C])
    seg(cv, fr, C, E, w=AUX_W, dash=DASH)          # BC の延長
    seg(cv, fr, A, X, w=AUX_W, dash=DASH)          # BA の延長
    seg(cv, fr, A, E)                              # 外角の二等分線
    seg(cv, fr, C, F, w=AUX_W, dash=DASH)          # 補助線
    par_mark(cv, fr, A, E, n=1, t=0.5)
    par_mark(cv, fr, F, C, n=1, t=0.5)
    angle_arc(cv, fr, A, X, E, r=22, n=1)
    angle_arc(cv, fr, A, E, C, r=22, n=1)
    angle_arc(cv, fr, F, A, C, r=20, n=2)
    angle_arc(cv, fr, C, A, F, r=20, n=2)
    for p in (A, B, C, E, F, X):
        dot_m(cv, fr, p)
    G = centroid(A, B, C)
    label_out(cv, fr, B, G, "B", fs, dist_=18)
    label_dir(cv, fr, C, 270, 18, "C", fs, weight="bold")
    label_dir(cv, fr, A, 180, 18, "A", fs, weight="bold")
    label_dir(cv, fr, E, 270, 18, "E", fs, weight="bold")
    label_dir(cv, fr, F, 200, 18, "F", fs, weight="bold")
    label_dir(cv, fr, X, 90, 18, "X", fs, weight="bold")
    for lab in ("A", "B", "C", "E", "F", "X"):
        labels.append(lab)
    ck.ok("図中ラベルに数字を含まない（BE・EC・DE の値は書かない）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L01_fig3_bisector_ratio_exterior.svg", "lesson": "L01", "canvas": cv,
            "title": "外角の二等分線と辺の比——△ABC の ∠A の外角 ∠CAX の二等分線 AE と、C を通り AE に平行な補助線 CF",
            "desc": "AB=6・AC=4・BC=5 の △ABC で、BA を A の側に延長した半直線上に X をとり、外角 ∠CAX の二等分線が直線 BC（C の側の延長）と交わる点を E とする。C を通り AE に平行な破線を引き、辺 AB との交点を F とする。∠XAE・∠EAC に1重の弧、∠AFC・∠ACF に2重の弧、AE と FC に矢羽。長さの数値は書かない（BE・EC は例題3の答え）。同型図は AB>AC を保って3辺を差し替える",
            "alt": "△ABCの∠Aの外角の二等分線AEと、Cを通りAEに平行な補助線——BE:EC=AB:ACでEは辺BCの延長上",
            "intent": "定理2の証明の補助線（C を通り AE に平行）と二等辺三角形 AFC（AF=AC）を見せ、E が辺 BC を AB:AC に外分する（C の側の延長上）ことを図で確かめる",
            "src": "lesson_01.md §4（定理2の穴埋め証明の直後）",
            "params": "AB=6・AC=4・BC=5（例題3の与件）／B=(0,0)・C=(5,0)・A は座標計算／E=外角の二等分線と直線 BC の交点（x=15）・F=C を通り AE に平行な直線と辺 AB の交点／36 px/単位／ラベルは A・B・C・E・F・X のみ",
            "checks": ck.items,
            "check_tokens": ["BE=15", "EC=10", "DE=12", "15", "10", "12"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# ===========================================================================
# L02 外心・内心／L03 重心・3心
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（lesson_02.md §2 外心と外接円） ---
    A, B, C = (1.6, 4.4), (0.0, 0.0), (6.0, 0.0)   # 鋭角三角形
    W, H = 640, 460
    fr = Frame(150, 330, 44)
    fs = fs_for(W)

    O = circumcenter(A, B, C)
    R = dist(O, A)
    ck = Checker()
    ck.ok("すべての角が鋭角（外心が内部に来る設定）", all(angle_at(v, p, q) < 90 for v, p, q in ((A, B, C), (B, C, A), (C, A, B))))
    ck.ok("OA=OB=OC（1e-9）", near(dist(O, B), R) and near(dist(O, C), R))
    for p, q, name in ((A, B, "AB"), (B, C, "BC"), (C, A, "CA")):
        m = mid(p, q)
        ck.ok(f"O は辺 {name} の垂直二等分線上（OM⊥{name}・1e-9）", near(dot(sub(O, m), sub(q, p)), 0.0))
    ck.ok("O は三角形の内部（3辺について重心と同じ側）",
          all(same_side(O, centroid(A, B, C), p, q) for p, q in ((A, B), (B, C), (C, A))))

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, O, R)
    poly(cv, fr, [A, B, C])
    for p, q, k in ((A, B, 1), (B, C, 2), (C, A, 3)):
        n = perp(unit(sub(q, p)))
        seg(cv, fr, add(O, mul(n, R * 1.12)), add(O, mul(n, -R * 1.12)), w=AUX_W, dash=DASH)
        m = mid(p, q)
        right_angle(cv, fr, m, q, add(m, perp(sub(q, p))), size=9)
        tick(cv, fr, p, m, n=k)
        tick(cv, fr, m, q, n=k)
    for p in (A, B, C, O):
        dot_m(cv, fr, p)
    G = centroid(A, B, C)
    for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 315), (O, "O", 0)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 18, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L02_fig1_circumcenter.svg", "lesson": "L02", "canvas": cv,
            "title": "外心 O——△ABC の3辺の垂直二等分線が1点で交わり、O を中心に3頂点を通る円（外接円）がかける",
            "desc": "鋭角三角形 ABC（B 左下・C 右下・A 上）に、3辺の垂直二等分線を破線で引く（中点に直角マーク・等しい2区間に辺ごとのティック 1・2・3 本）。3本は1点 O で交わり、O を中心とし OA を半径とする円が A・B・C を通る。数値は書かない。同型図は3頂点の座標を差し替えて生成する（鈍角にすると O は外部に出る）",
            "alt": "△ABCの3辺の垂直二等分線が1点Oで交わり、Oを中心にA・B・Cを通る円がかける",
            "intent": "外心の定義（3辺の垂直二等分線の交点）と、OA=OB=OC から外接円がかけることを1枚で見せる",
            "src": "lesson_02.md §2（穴埋め証明の直後・外心と外接円の定義文の直後）",
            "params": "A=(1.6,4.4)・B=(0,0)・C=(6,0)／O は座標計算（円の中心）／44 px/単位／ラベルは A・B・C・O のみ",
            "checks": ck.items,
            "check_tokens": ["65", "55", "60", "130", "30"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L02_2():
    # --- パラメータ（lesson_02.md §3 外心の位置3状態） ---
    tris = [("鋭角三角形", ((1.2, 3.2), (0.0, 0.0), (4.0, 0.0))),
            ("直角三角形", ((0.0, 3.0), (0.0, 0.0), (4.0, 0.0))),
            ("鈍角三角形", ((3.0, 1.0), (0.0, 0.0), (4.0, 0.0)))]
    W, H = 960, 400
    fs = 17                                       # 3パネルのため幅の 3% より小さい（逸脱として記録）
    frames = [Frame(70 + 320 * i, 240, 36) for i in range(3)]

    ck = Checker()
    kinds = []
    for (name, (A, B, C)), fr in zip(tris, frames):
        angs = [angle_at(A, B, C), angle_at(B, C, A), angle_at(C, A, B)]
        mx = max(angs)
        kind = "鋭角" if mx < 90 - 1e-9 else ("直角" if near(mx, 90) else "鈍角")
        kinds.append(kind)
        ck.ok(f"{name}: 最大角の種類が名前と一致", name.startswith(kind), f"角={[round(a, 3) for a in angs]}")
    A, B, C = tris[1][1]
    O = circumcenter(A, B, C)
    ck.ok("直角三角形の外心＝斜辺 AC の中点（1e-9）", near_pt(O, mid(A, C)))
    A, B, C = tris[0][1]
    O = circumcenter(A, B, C)
    ck.ok("鋭角三角形の外心は内部", all(same_side(O, centroid(A, B, C), p, q) for p, q in ((A, B), (B, C), (C, A))))
    A, B, C = tris[2][1]
    O = circumcenter(A, B, C)
    ck.ok("鈍角三角形の外心は外部", not all(same_side(O, centroid(A, B, C), p, q) for p, q in ((A, B), (B, C), (C, A))))

    cv = Canvas(W, H)
    labels = []
    for (name, (A, B, C)), fr in zip(tris, frames):
        O = circumcenter(A, B, C)
        R = dist(O, A)
        circle_path(cv, fr, O, R, w=AUX_W)
        poly(cv, fr, [A, B, C])
        if name.startswith("直角"):
            right_angle(cv, fr, B, A, C)
        for p in (A, B, C, O):
            dot_m(cv, fr, p)
        for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 315)):
            labels.append(lab)
            label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
        labels.append("O")
        label_dir(cv, fr, O, 0 if not name.startswith("鈍角") else 270, 16, "O", fs, weight="bold")
        caption(cv, fr.P((2.0, 0))[0], 378, name, fs, labels)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L02_fig2_circumcenter_position.svg", "lesson": "L02", "canvas": cv,
            "title": "外心の位置の3状態——鋭角三角形では内部・直角三角形では斜辺の中点・鈍角三角形では外部",
            "desc": "左から 鋭角三角形（A=(1.2,3.2)）・直角三角形（∠B=90°・斜辺 AC）・鈍角三角形（A=(3,1)）を同じ底辺 BC=4 で並べ、各三角形の外接円を細線で、外心 O を点で示す。直角三角形では O が斜辺 AC の中点に重なる。数値は書かない。同型図は頂点 A の座標を差し替えて生成する",
            "alt": "外心の位置の3状態——鋭角三角形では内部、直角三角形では斜辺の中点、鈍角三角形では外部",
            "intent": "外心の位置が角の種類で決まることを、同じ底辺で頂点を動かした3状態で観察させる",
            "src": "lesson_02.md §3（見出しの直後・3状態の箇条書きの前）",
            "params": "底辺 B=(0,0)・C=(4,0) 共通／A=(1.2,3.2)・(0,3)・(3,1)／36 px/単位・3パネル各 320 px／ラベルは A・B・C・O と パネル名",
            "checks": ck.items,
            "check_tokens": ["90°", "180"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 960 の 1.8%）。3パネル並置のため"],
            "allow_texts": labels}


def fig_L02_3():
    # --- パラメータ（lesson_02.md §4 内心と内接円） ---
    A, B, C = (2.0, 4.6), (0.0, 0.0), (6.4, 0.0)
    W, H = 640, 420
    fr = Frame(120, 340, 46)
    fs = fs_for(W)

    I = incenter(A, B, C)
    r = dist_line(I, B, C)
    feet = [foot(I, p, q) for p, q in ((A, B), (B, C), (C, A))]
    ck = Checker()
    ck.ok("I から3辺までの距離が等しい（1e-9）", all(near(dist_line(I, p, q), r) for p, q in ((A, B), (B, C), (C, A))))
    for v, p, q, name in ((A, B, C, "A"), (B, C, A, "B"), (C, A, B, "C")):
        ck.ok(f"I は ∠{name} の二等分線上（∠{name}I の両側の角が等しい・1e-9）", near(angle_at(v, p, I), angle_at(v, I, q)))
    ck.ok("垂線の足が3辺の内部（0<t<1）", all(0 < param_on(f, p, q) < 1 for f, (p, q) in zip(feet, ((A, B), (B, C), (C, A)))))
    ck.ok("I は三角形の内部", all(same_side(I, centroid(A, B, C), p, q) for p, q in ((A, B), (B, C), (C, A))))

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, I, r)
    poly(cv, fr, [A, B, C])
    for v, p, q, n in ((A, B, C, 3), (B, C, A, 2), (C, A, B, 1)):   # 弧の本数は頂点ごと（A 3重・B 2重・C 1重）
        far = line_x(v, I, p, q)
        seg(cv, fr, v, far, w=AUX_W, dash=DASH)
        angle_arc(cv, fr, v, p, I, r=20, n=n)
        angle_arc(cv, fr, v, I, q, r=20 + 6 * n, n=n)
    for f, (p, q) in zip(feet, ((A, B), (B, C), (C, A))):
        seg(cv, fr, I, f, w=DIM_W)
        right_angle(cv, fr, f, q, I, size=8)
    for p in (A, B, C, I):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 315), (I, "I", 90)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 16, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L02_fig3_incenter.svg", "lesson": "L02", "canvas": cv,
            "title": "内心 I——△ABC の3つの内角の二等分線が1点で交わり、I を中心に3辺に接する円（内接円）がかける",
            "desc": "△ABC（B 左下・C 右下・A 上）に3つの内角の二等分線を破線で引き（各頂点の2つの半角に同じ本数の弧——A は3重・B は2重・C は1重）、交点 I から3辺へ下ろした垂線（直角マーク）を細線で描く。I を中心とし、垂線の長さを半径とする円が3辺に接する。数値は書かない。同型図は3頂点の座標を差し替えて生成する",
            "alt": "△ABCの3つの内角の二等分線が1点Iで交わり、Iを中心に3辺に接する円がかける",
            "intent": "内心の定義（3つの内角の二等分線の交点）と、3辺から等距離であることから内接円がかけることを1枚で見せる",
            "src": "lesson_02.md §4（穴埋め証明の直後・内心と内接円の定義文の直後）",
            "params": "A=(2,4.6)・B=(0,0)・C=(6.4,0)／I は座標計算（辺の長さの重み付き平均）／46 px/単位／ラベルは A・B・C・I のみ",
            "checks": ck.items,
            "check_tokens": ["70", "125", "55", "90"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L03_1():
    # --- パラメータ（lesson_03.md §2 重心と 2:1） ---
    A, B, C = (2.2, 4.6), (0.0, 0.0), (6.4, 0.0)
    W, H = 640, 420
    fr = Frame(120, 340, 46)
    fs = fs_for(W)

    L, M, N = mid(B, C), mid(C, A), mid(A, B)
    G = centroid(A, B, C)
    ck = Checker()
    ck.ok("G＝3頂点の座標の平均（1e-9）", near_pt(G, ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)))
    ck.ok("G は3本の中線 AL・BM・CN の上", all(near(cross(sub(G, v), sub(m, v)), 0.0) for v, m in ((A, L), (B, M), (C, N))))
    ck.ok("AG:GL=BG:GM=CG:GN=2:1（1e-9）", all(near(dist(v, G) / dist(G, m), 2.0) for v, m in ((A, L), (B, M), (C, N))))
    ck.ok("中点連結定理 NM∥BC・NM=BC/2（1e-9）", near(cross(sub(M, N), sub(C, B)), 0.0) and near(dist(N, M), dist(B, C) / 2))
    ck.ok("△GNM∽△GCB の相似比 1:2（GM:GB=GN:GC=1:2）", near(dist(G, M) / dist(G, B), 0.5) and near(dist(G, N) / dist(G, C), 0.5))

    cv = Canvas(W, H)
    labels = []
    poly(cv, fr, [A, B, C])
    for v, m in ((A, L), (B, M), (C, N)):
        seg(cv, fr, v, m)
    seg(cv, fr, N, M, w=AUX_W, dash=DASH)
    par_mark(cv, fr, N, M, n=1)
    par_mark(cv, fr, B, C, n=1, t=0.88)
    for p, q, m, k in ((A, B, N, 1), (B, C, L, 2), (C, A, M, 3)):
        tick(cv, fr, p, m, n=k)
        tick(cv, fr, m, q, n=k)
    for p in (A, B, C, L, M, N, G):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 315), (L, "L", 270), (M, "M", 20), (N, "N", 160), (G, "G", 335)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない（AG・GL の値は書かない）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L03_fig1_centroid.svg", "lesson": "L03", "canvas": cv,
            "title": "重心 G——△ABC の3本の中線 AL・BM・CN が1点で交わり、各中線を頂点側から 2:1 に分ける",
            "desc": "△ABC（B 左下・C 右下・A 上）の辺 BC・CA・AB の中点 L・M・N と3本の中線を描き、交点 G を置く。中点連結の線分 NM を破線で引き、NM と BC に矢羽（平行）、等しい半分ずつにティック（AB は1本・BC は2本・CA は3本）。長さの数値は書かない。同型図は3頂点の座標を差し替えて生成する",
            "alt": "△ABCの3本の中線が1点Gで交わり、各中線を頂点側から2:1に分ける——中点連結定理NM∥BC、NM=BC/2が相似比1:2をつくる",
            "intent": "重心の定義（3本の中線の交点）と、証明の芯である △GNM∽△GCB（相似比 1:2）の形を1枚で見せる",
            "src": "lesson_03.md §2（穴埋め証明の直後・重心の定義文の直後）",
            "params": "A=(2.2,4.6)・B=(0,0)・C=(6.4,0)／L・M・N は中点・G は座標の平均／46 px/単位／ラベルは A・B・C・L・M・N・G のみ",
            "checks": ck.items,
            "check_tokens": ["AG=6", "GL=3", "BG=4", "BM=6"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L03_2():
    # --- パラメータ（lesson_03.md §4 3心の比較 2パネル） ---
    gen = ((1.3, 3.9), (0.0, 0.0), (5.0, 0.0))     # 一般の三角形
    side = 4.4
    equi = ((side / 2, side * SQ3 / 2), (0.0, 0.0), (side, 0.0))   # 正三角形
    W, H = 640, 330
    fs = 17                                       # 2パネルのため幅の 3% より小さい（逸脱として記録）
    frL, frR = Frame(50, 250, 44), Frame(370, 250, 44)

    ck = Checker()
    A, B, C = gen
    O, I, G = circumcenter(A, B, C), incenter(A, B, C), centroid(A, B, C)
    ck.ok("一般の三角形では O・I・G が互いに異なる（距離>0.05）", dist(O, I) > 0.05 and dist(I, G) > 0.05 and dist(G, O) > 0.05)
    A2, B2, C2 = equi
    ck.ok("正三角形（3辺相等・1e-9）", near(dist(A2, B2), side) and near(dist(B2, C2), side) and near(dist(C2, A2), side))
    O2, I2, G2 = circumcenter(A2, B2, C2), incenter(A2, B2, C2), centroid(A2, B2, C2)
    ck.ok("正三角形では外心・内心・重心が一致（1e-9）", near_pt(O2, I2) and near_pt(I2, G2))

    cv = Canvas(W, H)
    labels = []
    for fr, (A, B, C), name in ((frL, gen, "一般の三角形"), (frR, equi, "正三角形")):
        O, I, G = circumcenter(A, B, C), incenter(A, B, C), centroid(A, B, C)
        circle_path(cv, fr, O, dist(O, A), w=AUX_W, dash=DASH)
        circle_path(cv, fr, I, dist_line(I, B, C), w=AUX_W, dash=DASH)
        poly(cv, fr, [A, B, C])
        for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 315)):
            dot_m(cv, fr, p)
            labels.append(lab)
            label_dir(cv, fr, p, deg, 16, lab, fs, weight="bold")
        if name == "正三角形":
            dot_m(cv, fr, G)
            labels.append("O=I=G")
            label_dir(cv, fr, G, 0, 16, "O=I=G", fs, anchor="start", weight="bold")
        else:
            for p, lab, deg in ((O, "O", 300), (I, "I", 180), (G, "G", 60)):
                dot_m(cv, fr, p)
                labels.append(lab)
                label_dir(cv, fr, p, deg, 15, lab, fs, weight="bold")
        caption(cv, fr.P(((B[0] + C[0]) / 2, 0))[0], 300, name, fs, labels)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L03_fig2_three_centers.svg", "lesson": "L03", "canvas": cv,
            "title": "3心の比較——一般の三角形では外心 O・内心 I・重心 G が別の点、正三角形では1点に重なる（2パネル）",
            "desc": "左パネルは一般の三角形 ABC に外心 O・内心 I・重心 G を別々の点として置き、外接円と内接円を破線で添える。右パネルは正三角形 ABC で3点が1点（O=I=G）に重なる。数値は書かない。同型図は左の頂点座標を差し替えて生成する（二等辺にすると3点が対称軸上に並ぶ）",
            "alt": "一般の三角形では外心・内心・重心が別の点だが、正三角形では1点に重なる（2パネル）",
            "intent": "3心を「何の交点か」で区別したうえで、正三角形で一致することを2パネルの対比で見せる",
            "src": "lesson_03.md §4（3心の表の直後・正三角形の段落の直後）",
            "params": "左: A=(1.3,3.9)・B=(0,0)・C=(5,0)／右: 1辺 4.4 の正三角形／O・I・G は座標計算／44 px/単位・2パネル／ラベルは A・B・C・O・I・G・O=I=G と パネル名",
            "checks": ck.items,
            "check_tokens": ["2:1", "6等分"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 640 の 2.7%）。2パネル並置のため"],
            "allow_texts": labels}


# ===========================================================================
# L04 チェバ・メネラウス／L05 三角形の成立条件・辺と角の大小
# ===========================================================================
def _ceva_product(A, B, C, P, Q, R):
    """(BP/PC)(CQ/QA)(AR/RB)——長さは正の数として計算"""
    return (dist(B, P) / dist(P, C)) * (dist(C, Q) / dist(Q, A)) * (dist(A, R) / dist(R, B))


def _seg_status(X, p, q):
    t = param_on(X, p, q)
    return "辺上" if 0 < t < 1 else "延長上"


def fig_L04_1():
    # --- パラメータ（lesson_04.md §2 チェバの定理・O が内部） ---
    A, B, C = (2.4, 4.6), (0.0, 0.0), (6.4, 0.0)
    O = (2.9, 1.5)                                 # 三角形の内部の点
    W, H = 640, 420
    fr = Frame(120, 340, 46)
    fs = fs_for(W)

    P = line_x(A, O, B, C)
    Q = line_x(B, O, C, A)
    R = line_x(C, O, A, B)
    ck = Checker()
    ck.ok("O は三角形の内部", all(same_side(O, centroid(A, B, C), p, q) for p, q in ((A, B), (B, C), (C, A))))
    ck.ok("P・Q・R がそれぞれ辺 BC・CA・AB 上（0<t<1）",
          all(0 < param_on(X, p, q) < 1 for X, p, q in ((P, B, C), (Q, C, A), (R, A, B))))
    ck.ok("(BP/PC)(CQ/QA)(AR/RB)=1（1e-9）", near(_ceva_product(A, B, C, P, Q, R), 1.0),
          f"積={_ceva_product(A, B, C, P, Q, R):.12f}")

    cv = Canvas(W, H)
    labels = []
    poly(cv, fr, [A, B, C])
    for v, X in ((A, P), (B, Q), (C, R)):
        seg(cv, fr, v, X)
    for p in (A, B, C, O, P, Q, R):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 315), (O, "O", 300), (P, "P", 270), (Q, "Q", 20), (R, "R", 160)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L04_fig1_ceva_inside.svg", "lesson": "L04", "canvas": cv,
            "title": "チェバの定理——△ABC の内部の点 O を通る3直線 AP・BQ・CR と辺上の3点 P・Q・R",
            "desc": "△ABC（B 左下・C 右下・A 上）の内部に点 O をとり、AO・BO・CO の延長が向かい合う辺 BC・CA・AB と交わる点を P・Q・R とする。3点とも辺上にある基本形。数値は書かない（比は例題の答え）。同型図は O の座標を差し替えて生成する",
            "alt": "△ABCの内部の点Oを通る3直線AP・BQ・CRと辺上の3点P・Q・R——(BP/PC)(CQ/QA)(AR/RB)=1",
            "intent": "チェバの定理の基本形（O が内部・3点が辺上）と、一周の型 B→P→C→Q→A→R→B の読み取りの土台",
            "src": "lesson_04.md §2（定理6の式の直後・穴埋め証明の前）",
            "params": "A=(2.4,4.6)・B=(0,0)・C=(6.4,0)・O=(2.9,1.5)／P・Q・R は直線の交点として座標計算／46 px/単位／ラベルは A・B・C・O・P・Q・R のみ",
            "checks": ck.items,
            "check_tokens": ["2:1", "3:2", "1:3", "2/1"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L04_2():
    # --- パラメータ（lesson_04.md §3 チェバの定理・O が外部） ---
    A, B, C = (2.0, 4.0), (0.0, 0.0), (6.0, 0.0)
    O = (2.5, 5.5)                                 # A の上方（三角形の外部）
    W, H = 640, 440
    fr = Frame(120, 380, 46)
    fs = fs_for(W)

    P = line_x(A, O, B, C)
    Q = line_x(B, O, C, A)
    R = line_x(C, O, A, B)
    ck = Checker()
    ck.ok("O は三角形の外部", not all(same_side(O, centroid(A, B, C), p, q) for p, q in ((A, B), (B, C), (C, A))))
    st = [_seg_status(P, B, C), _seg_status(Q, C, A), _seg_status(R, A, B)]
    ck.ok("P は辺 BC 上・Q と R は辺の延長上（延長上が2点）", st == ["辺上", "延長上", "延長上"], f"{st}")
    ck.ok("(BP/PC)(CQ/QA)(AR/RB)=1（1e-9）", near(_ceva_product(A, B, C, P, Q, R), 1.0),
          f"積={_ceva_product(A, B, C, P, Q, R):.12f}")

    cv = Canvas(W, H)
    labels = []
    poly(cv, fr, [A, B, C])
    seg(cv, fr, A, Q, w=AUX_W, dash=DASH)          # CA の延長
    seg(cv, fr, A, R, w=AUX_W, dash=DASH)          # BA の延長
    seg(cv, fr, O, P)
    seg(cv, fr, B, O)
    seg(cv, fr, C, O)
    for p in (A, B, C, O, P, Q, R):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 180), (B, "B", 225), (C, "C", 315), (O, "O", 90), (P, "P", 270), (Q, "Q", 0), (R, "R", 180)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L04_fig2_ceva_extended.svg", "lesson": "L04", "canvas": cv,
            "title": "チェバの定理（O が外部）——P は辺 BC 上、Q・R は辺 CA・AB を A の側に延長した直線上",
            "desc": "△ABC の外部（A の上方）に点 O をとり、直線 AO・BO・CO と直線 BC・CA・AB の交点を P・Q・R とする。P は辺上、Q・R は辺の延長上（破線）に来るが、長さを正の数として (BP/PC)(CQ/QA)(AR/RB)=1 は保たれる。数値は書かない。同型図は O の座標を差し替えて生成する",
            "alt": "Oが△ABCの外部にあるチェバの定理——P・Q・Rのうち2点が辺の延長上にあっても(BP/PC)(CQ/QA)(AR/RB)=1",
            "intent": "点が辺の延長上に来る場合でも式が同じであることを図で確かめ、「比を求める」と「側を決める」を分ける練習の土台にする",
            "src": "lesson_04.md §3（見出しの直後・「このときも同じ式が成り立つ」の前）",
            "params": "A=(2,4)・B=(0,0)・C=(6,0)・O=(2.5,5.5)／P・Q・R は直線の交点として座標計算／46 px/単位／ラベルは A・B・C・O・P・Q・R のみ",
            "checks": ck.items,
            "check_tokens": ["2:3", "3:2", "2:1"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L04_3():
    # --- パラメータ（lesson_04.md §4 メネラウスの定理・直線が三角形を横切る） ---
    A, B, C = (2.0, 4.4), (0.0, 0.0), (6.0, 0.0)
    R = divide(A, B, 1, 1)                         # 辺 AB の中点
    Q = divide(C, A, 1, 2)                         # CQ:QA=1:2（例題3の設定）
    W, H = 640, 400
    fr = Frame(70, 330, 40)
    fs = fs_for(W)

    P = line_x(Q, R, B, C)
    ck = Checker()
    st = [_seg_status(P, B, C), _seg_status(Q, C, A), _seg_status(R, A, B)]
    ck.ok("Q・R は辺上・P は辺 BC の延長上（C の側・t>1）", st == ["延長上", "辺上", "辺上"] and param_on(P, B, C) > 1, f"{st}")
    ck.ok("P・Q・R は同一直線上（外積 0）", near(cross(sub(Q, P), sub(R, P)), 0.0))
    ck.ok("(BP/PC)(CQ/QA)(AR/RB)=1（1e-9）", near(_ceva_product(A, B, C, P, Q, R), 1.0),
          f"積={_ceva_product(A, B, C, P, Q, R):.12f}")

    cv = Canvas(W, H)
    labels = []
    poly(cv, fr, [A, B, C])
    seg(cv, fr, C, P, w=AUX_W, dash=DASH)          # BC の延長
    ext1 = add(R, mul(unit(sub(R, P)), 1.2))
    ext2 = add(P, mul(unit(sub(P, R)), 0.9))
    seg(cv, fr, ext1, ext2)                        # 直線 ℓ
    for p in (A, B, C, P, Q, R):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 90), (B, "B", 225), (C, "C", 270), (P, "P", 270), (Q, "Q", 30), (R, "R", 160)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
    labels.append("ℓ")
    label_dir(cv, fr, ext1, 90, 14, "ℓ", fs)
    ck.ok("図中ラベルに数字を含まない（比 2:1 は書かない）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L04_fig3_menelaus_inside.svg", "lesson": "L04", "canvas": cv,
            "title": "メネラウスの定理——△ABC の2辺 AB・CA と辺 BC の延長を横切る直線 ℓ 上の3点 R・Q・P",
            "desc": "△ABC（B 左下・C 右下・A 上）で、辺 AB の中点 R と辺 CA を CQ:QA=1:2 に分ける点 Q を通る直線 ℓ が、辺 BC を C の側に延長した直線（破線）と交わる点を P とする。Q・R は辺上、P は延長上。数値は書かない。同型図は Q・R の位置を差し替えて生成する",
            "alt": "△ABCの2辺と1辺の延長を横切る直線ℓ上の3点P・Q・R——(BP/PC)(CQ/QA)(AR/RB)=1",
            "intent": "メネラウスの定理の基本形（直線が三角形を横切り、2点が辺上・1点が延長上）と一周の型の読み取り",
            "src": "lesson_04.md §4（定理7の式と「一周の型で書ける」の直後・穴埋め証明の前）",
            "params": "A=(2,4.4)・B=(0,0)・C=(6,0)／R=AB の中点・Q=CA を 1:2 に内分（C 側から）・P=直線 QR と直線 BC の交点／40 px/単位／ラベルは A・B・C・P・Q・R・ℓ のみ",
            "checks": ck.items,
            "check_tokens": ["2:1", "1:2", "1:1"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L04_4():
    # --- パラメータ（lesson_04.md §4 メネラウスの定理・直線が三角形を横切らない） ---
    A, B, C = (2.0, 4.0), (0.0, 0.0), (5.0, 0.0)
    L1, L2 = (1.0, 5.4), (7.6, -0.5)               # 直線 ℓ の2点（A の上・C の右を通り、3辺の延長と交わる）
    W, H = 640, 400
    fr = Frame(90, 320, 40)
    fs = fs_for(W)

    P = line_x(L1, L2, B, C)
    Q = line_x(L1, L2, C, A)
    R = line_x(L1, L2, A, B)
    ck = Checker()
    st = [_seg_status(P, B, C), _seg_status(Q, C, A), _seg_status(R, A, B)]
    ck.ok("P・Q・R の3点すべてが辺の延長上", st == ["延長上", "延長上", "延長上"], f"{st}")
    ck.ok("直線 ℓ は三角形の内部を通らない（3頂点が ℓ の同じ側）",
          same_side(A, B, L1, L2) and same_side(B, C, L1, L2))
    ck.ok("(BP/PC)(CQ/QA)(AR/RB)=1（1e-9）", near(_ceva_product(A, B, C, P, Q, R), 1.0),
          f"積={_ceva_product(A, B, C, P, Q, R):.12f}")

    cv = Canvas(W, H)
    labels = []
    poly(cv, fr, [A, B, C])
    seg(cv, fr, C, P, w=AUX_W, dash=DASH)
    seg(cv, fr, A, Q, w=AUX_W, dash=DASH)
    seg(cv, fr, A, R, w=AUX_W, dash=DASH)
    seg(cv, fr, L1, L2)
    for p in (A, B, C, P, Q, R):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 200), (B, "B", 225), (C, "C", 270), (P, "P", 270), (Q, "Q", 180), (R, "R", 20)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
    labels.append("ℓ")
    label_dir(cv, fr, L1, 90, 14, "ℓ", fs)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L04_fig4_menelaus_extended.svg", "lesson": "L04", "canvas": cv,
            "title": "メネラウスの定理（三角形を横切らない直線）——P・Q・R の3点がすべて辺の延長上",
            "desc": "△ABC の外側を通る直線 ℓ が、辺 BC・CA・AB をそれぞれ延長した直線（破線）と交わる点を P・Q・R とする。3点とも延長上にあるが (BP/PC)(CQ/QA)(AR/RB)=1 は同じ。数値は書かない。同型図は ℓ の2点を差し替えて生成する（ℓ が三角形を横切らない範囲で）",
            "alt": "△ABCを横切らない直線ℓ——P・Q・Rの3点がすべて辺の延長上にあっても同じ式が成り立つ",
            "intent": "直線が三角形を横切らない場合でも式の形が変わらないことを図で確かめる",
            "src": "lesson_04.md §4（例題3の直後・「直線 ℓ が三角形を横切らないとき」の段落の直後）",
            "params": "A=(2,4)・B=(0,0)・C=(5,0)・ℓ は (1,5.4)−(7.6,−0.5)／P・Q・R は直線の交点として座標計算／40 px/単位／ラベルは A・B・C・P・Q・R・ℓ のみ",
            "checks": ck.items,
            "check_tokens": ["2:1", "1:2"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L05_1():
    # --- パラメータ（lesson_05.md §1 3本の棒を組む3状態） ---
    cases = [((3, 4, 5), "成立"), ((2, 3, 5), "一直線"), ((2, 3, 7), "不成立")]
    W, H = 960, 300
    fs = 17                                       # 3パネルのため幅の 3% より小さい（逸脱として記録）
    frames = [Frame(60 + 320 * i, 200, 30) for i in range(3)]

    ck = Checker()
    for (a, b, c), name in cases:
        holds = a < b + c and b < c + a and c < a + b
        degenerate = (a + b == c) or (b + c == a) or (c + a == b)
        expect = "成立" if holds else ("一直線" if degenerate else "不成立")
        ck.ok(f"{a}・{b}・{c}: 2辺の和と残りの辺の大小から {expect}", expect == name)

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    for ((a, b, c), name), fr in zip(cases, frames):
        # 最長の棒 c を底辺に置き、左端に a・右端に b を蝶番でつなぐ
        B, C = (0.0, 0.0), (float(c), 0.0)
        if name == "成立":
            A = _tri_from_sides(a, b, c)            # AB=a・AC=b
            ck.ok(f"成立: 3辺 {a}・{b}・{c} の三角形が閉じる（座標から・1e-9）",
                  near(dist(A, B), a) and near(dist(A, C), b))
            poly(cv, fr, [A, B, C], w=BOLD_W)
            side_label(cv, fr, B, A, C, str(a), fs, off=16)
            side_label(cv, fr, A, C, B, str(b), fs, off=16)
            side_label(cv, fr, B, C, A, str(c), fs, off=16)
            labels += [str(a), str(b), str(c)]
        elif name == "一直線":
            J = (float(a), 0.0)                    # a＋b=c: 2本が底辺の上で一直線につぶれる
            ck.ok(f"一直線: {a}＋{b}={c}（棒が一直線）", a + b == c)
            seg(cv, fr, B, C, w=BOLD_W)
            up = 0.35
            seg(cv, fr, (B[0], up), (J[0], up), w=BOLD_W)
            seg(cv, fr, (J[0], up), (C[0], up), w=BOLD_W)
            dot_m(cv, fr, (J[0], up))
            T(*fr.P(((B[0] + J[0]) / 2, up + 0.55)), str(a))
            T(*fr.P(((J[0] + C[0]) / 2, up + 0.55)), str(b))
            side_label(cv, fr, B, C, (c / 2, 1.0), str(c), fs, off=16)
            labels.append(str(c))
        else:
            # 2本を底辺の両端から内側へ倒しても届かない: 角度 55° で立てて先端の隙間を見せる
            th = 55.0
            E1 = (a * math.cos(th * DEG), a * math.sin(th * DEG))
            E2 = (c - b * math.cos(th * DEG), b * math.sin(th * DEG))
            ck.ok(f"不成立: {a}＋{b}<{c}（届かない）", a + b < c)
            ck.ok("不成立パネルの2本の先端に隙間がある（底辺方向の距離>0）", E2[0] - E1[0] > 0)
            seg(cv, fr, B, C, w=BOLD_W)
            seg(cv, fr, B, E1, w=BOLD_W)
            seg(cv, fr, C, E2, w=BOLD_W)
            side_label(cv, fr, B, E1, C, str(a), fs, off=16)
            side_label(cv, fr, C, E2, B, str(b), fs, off=16)
            side_label(cv, fr, B, C, (c / 2, 1.0), str(c), fs, off=16)
            labels += [str(a), str(b), str(c)]
        for p in (B, C):
            dot_m(cv, fr, p)
        T(fr.P((c / 2, 0))[0], 275, name)
    ck.ok("図中の数字は本文の棒の長さ 2・3・4・5・7 のみ", digit_runs(labels) <= {"2", "3", "4", "5", "7"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L05_fig1_triangle_inequality.svg", "lesson": "L05", "canvas": cv,
            "title": "3本の棒を組む3状態——3・4・5 は三角形を組める（成立）・2・3・5 は一直線につぶれる（一直線）・2・3・7 は届かない（不成立）",
            "desc": "左: 長さ 3・4・5 の棒が三角形を閉じる。中: 2・3・5 では短い2本を並べるとちょうど 5 になり一直線につぶれる。右: 2・3・7 では両端から立てた2本の先端が届かず隙間が残る。長さは本文の与件のみ。同型図は3組の長さを差し替えて生成する（成立・一直線・不成立の判定は自動）",
            "alt": "長さ3・4・5の棒は三角形を組める（成立）、2・3・5は一直線につぶれる（一直線）、2・3・7は届かない（不成立）の3状態",
            "intent": "三角形の成立条件「2辺の和＞残りの辺」を、棒が届くか届かないかの3状態で見せる",
            "src": "lesson_05.md §1（3本の棒の段落の直後・§2 の前）",
            "params": "(3,4,5)・(2,3,5)・(2,3,7)／最長の棒を底辺・30 px/単位・3パネル各 320 px／ラベルは 棒の長さと 成立・一直線・不成立",
            "checks": ck.items,
            "check_tokens": ["1<x", "x<9", "6", "8"],
            "digit_rule": ("subset", {"2", "3", "4", "5", "7"}),
            "deviations": ["文字サイズ 17 px（幅 960 の 1.8%）。3パネル並置のため"],
            "allow_texts": labels}


def fig_L05_2():
    # --- パラメータ（lesson_05.md §3 辺の大小と対角の大小） ---
    AB, BC, CA = 7.0, 5.0, 4.0                      # AB 最大・CA 最小
    W, H = 640, 380
    fr = Frame(70, 300, 60)
    fs = fs_for(W)

    B = (0.0, 0.0)
    A = (AB, 0.0)
    # C は BC=5・CA=4 を満たす上側の点
    x = (BC * BC - CA * CA + AB * AB) / (2 * AB)
    C = (x, math.sqrt(BC * BC - x * x))
    ck = Checker()
    ck.ok("AB=7・BC=5・CA=4（座標から・1e-9）", near(dist(A, B), AB) and near(dist(B, C), BC) and near(dist(C, A), CA))
    angA, angB, angC = angle_at(A, B, C), angle_at(B, C, A), angle_at(C, A, B)
    ck.ok("最大辺 AB の対角 ∠C が最大", angC > angA and angC > angB, f"∠A={angA:.2f} ∠B={angB:.2f} ∠C={angC:.2f}")
    ck.ok("最小辺 CA の対角 ∠B が最小", angB < angA and angB < angC)
    ck.ok("辺の順 AB>BC>CA と角の順 ∠C>∠A>∠B が同じ向き", (AB > BC > CA) and (angC > angA > angB))

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    poly(cv, fr, [A, B, C])
    seg(cv, fr, A, B, w=BOLD_W)
    angle_arc(cv, fr, C, A, B, r=22, n=3)
    angle_arc(cv, fr, A, B, C, r=26, n=2)
    angle_arc(cv, fr, B, C, A, r=30, n=1)
    for p in (A, B, C):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 315), (B, "B", 225), (C, "C", 90)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 18, lab, fs, weight="bold")
    side_label(cv, fr, B, A, C, "最大辺", fs, off=20)
    side_label(cv, fr, C, A, B, "最小辺", fs, off=22)
    labels += ["最大辺", "最小辺"]
    label_dir(cv, fr, C, 270, 62, "最大角", fs)
    label_dir(cv, fr, B, 20, 78, "最小角", fs)
    labels += ["最大角", "最小角"]
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L05_fig2_side_angle_order.svg", "lesson": "L05", "canvas": cv,
            "title": "辺の大小と対角の大小——最大辺 AB に向かい合う ∠C が最大、最小辺 CA に向かい合う ∠B が最小",
            "desc": "AB=7・BC=5・CA=4 の △ABC（B 左下・A 右下・C 上）で、最大辺 AB を太線にし、角の弧の本数で大小の順（∠C 3重・∠A 2重・∠B 1重）を示す。辺と角の数値は書かない。同型図は3辺の長さを差し替えて生成する（最大・最小の判定は自動）",
            "alt": "△ABCで最も長い辺ABに向かい合う∠Cが最も大きく、最も短い辺に向かい合う角が最も小さい",
            "intent": "「大きい辺の向かいに大きい角」の対応を、辺の太さと弧の本数の対応で見せる",
            "src": "lesson_05.md §3（定理9の式と「向かい合う」の説明の直後）",
            "params": "AB=7・BC=5・CA=4（比のみ・数値は図に書かない）／B=(0,0)・A=(7,0)・C は座標計算／60 px/単位／ラベルは A・B・C・最大辺・最小辺・最大角・最小角",
            "checks": ck.items,
            "check_tokens": ["7", "5", "4"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# ===========================================================================
# L06 円に内接する四角形・星形七角形／L07 接線の長さ・接弦
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（lesson_06.md §2 内接四角形の対角と外角） ---
    O, r = (0.0, 0.0), 3.0
    degs = {"A": 110.0, "B": 200.0, "C": 310.0, "D": 20.0}   # 反時計回りに A→B→C→D
    W, H = 640, 440
    fr = Frame(300, 230, 52)
    fs = fs_for(W)

    A, B, C, D = (pt_on_circle(O, r, degs[k]) for k in "ABCD")
    E = add(C, mul(unit(sub(C, B)), 1.6))          # 辺 BC を C の側に延長した点
    ck = Checker()
    ck.ok("A・B・C・D は円周上（1e-9）", all(on_circle(p, O, r) for p in (A, B, C, D)))
    ck.ok("四角形 ABCD は凸で頂点が反時計回り", all(cross(sub(q, p), sub(s, q)) > 0 for p, q, s in ((A, B, C), (B, C, D), (C, D, A), (D, A, B))))
    angA, angC = angle_at(A, D, B), angle_at(C, B, D)
    ck.ok("対角の和 ∠A＋∠C=180°（1e-9）", near(angA + angC, 180.0), f"∠A={angA:.4f} ∠C={angC:.4f}")
    ck.ok("外角 ∠DCE＝内対角 ∠A（1e-9）", near(angle_at(C, D, E), angA))
    ck.ok("E は直線 BC 上で C の先（t>1）", near(cross(sub(E, B), sub(C, B)), 0.0) and param_on(E, B, C) > 1)

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, O, r)
    poly(cv, fr, [A, B, C, D])
    seg(cv, fr, C, E, w=AUX_W, dash=DASH)
    angle_arc(cv, fr, A, D, B, r=22, n=1)
    angle_arc(cv, fr, C, B, D, r=22, n=2)
    angle_arc(cv, fr, C, D, E, r=30, n=1)
    for p in (A, B, C, D, E, O):
        dot_m(cv, fr, p)
    for k, lab in (("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")):
        p = pt_on_circle(O, r, degs[k])
        labels.append(lab)
        label_dir(cv, fr, p, degs[k], 18, lab, fs, weight="bold")
    labels += ["E", "O"]
    label_dir(cv, fr, E, 300, 16, "E", fs, weight="bold")
    label_dir(cv, fr, O, 90, 14, "O", fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない（角度の値は書かない）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L06_fig1_cyclic_quadrilateral.svg", "lesson": "L06", "canvas": cv,
            "title": "円に内接する四角形 ABCD——対角 ∠A と ∠C（和が 180°）と、辺 BC の延長上の点 E がつくる外角 ∠DCE（＝∠A）",
            "desc": "中心 O の円に四角形 ABCD を反時計回りに内接させ（A 左上・B 左下・C 右下・D 右上）、∠A に1重の弧、∠C に2重の弧を付ける。辺 BC を C の側に延長した破線上の点 E をとり、外角 ∠DCE に ∠A と同じ1重の弧を付ける。角度の数値は書かない。同型図は4点の角度位置を差し替えて生成する",
            "alt": "円に内接する四角形 ABCD——対角 ∠A と ∠C は弧 BCD と弧 BAD に対する円周角で、2つの弧を合わせると円周全体になる。辺 BC の延長上の点 E について、外角 ∠DCE は内対角 ∠A に等しい",
            "intent": "内接四角形の2つの性質（対角の和 180°・外角＝内対角）を1枚で見せ、∠A と ∠C がそれぞれどの弧に対する円周角かを読ませる",
            "src": "lesson_06.md §2（性質 (1)(2) の直後・穴埋め証明の前）",
            "params": "円 O=(0,0)・半径 3／A=110°・B=200°・C=310°・D=20° の位置／E=BC の延長上 1.6／52 px/単位／ラベルは A・B・C・D・E・O のみ",
            "checks": ck.items,
            "check_tokens": ["180", "112", "68", "100", "80"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L06_2():
    # --- パラメータ（lesson_06.md §3 内接する条件（逆）の証明図） ---
    O, r = (0.0, 0.0), 3.0
    degs = {"A": 130.0, "B": 210.0, "C": 320.0, "D": 40.0, "C′": 285.0}
    W, H = 640, 440
    fr = Frame(300, 230, 52)
    fs = fs_for(W)

    A, B, C, D, C2 = (pt_on_circle(O, r, degs[k]) for k in ("A", "B", "C", "D", "C′"))
    ck = Checker()
    ck.ok("3点 A・B・D を通る円の中心＝O・半径 3（1e-9）", near_pt(circumcenter(A, B, D), O) and near(dist(O, A), r))
    ck.ok("∠A＋∠C=180°（C はこの円周上・1e-9）", near(angle_at(A, D, B) + angle_at(C, B, D), 180.0))
    ck.ok("C′ は円周上で、直線 BD について C と同じ側", on_circle(C2, O, r) and same_side(C, C2, B, D))
    ck.ok("∠BC′D=∠BCD（同じ弧 BD に対する円周角・1e-9）", near(angle_at(C2, B, D), angle_at(C, B, D)))
    ck.ok("C と C′ は異なる点（距離>0.5）", dist(C, C2) > 0.5)

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, O, r, w=AUX_W)
    poly(cv, fr, [A, B, C, D])
    seg(cv, fr, B, D, w=AUX_W, dash=DASH)
    seg(cv, fr, B, C2, w=AUX_W, dash=DASH)
    seg(cv, fr, D, C2, w=AUX_W, dash=DASH)
    angle_arc(cv, fr, C, B, D, r=22, n=1)
    angle_arc(cv, fr, C2, B, D, r=22, n=1)
    angle_arc(cv, fr, A, D, B, r=22, n=2)
    for p in (A, B, C, D, C2):
        dot_m(cv, fr, p)
    for k, lab in (("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("C′", "C′")):
        p = pt_on_circle(O, r, degs[k])
        labels.append(lab)
        label_dir(cv, fr, p, degs[k], 20, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L06_fig2_cyclic_converse.svg", "lesson": "L06", "canvas": cv,
            "title": "四角形が円に内接する条件（逆）の証明図——3点 A・B・D を通る円と、直線 BD について C と同じ側の円周上の点 C′",
            "desc": "∠A＋∠C=180° の四角形 ABCD（実線）に対し、3点 A・B・D を通る円を細線でかき、対角線 BD を破線で引く。円周上で直線 BD について C と同じ側に C′ をとり、BC′・DC′ を破線で結ぶ。∠BCD と ∠BC′D に同じ1重の弧、∠A に2重の弧。数値は書かない。同型図は5点の角度位置を差し替えて生成する",
            "alt": "四角形 ABCD で ∠A＋∠C=180° のとき——3点 A、B、D を通る円をかき、その円周上で直線 BD について C と同じ側に点 C′ をとると、∠BC′D=∠BCD となるので、円周角の定理の逆から C は円周上にある",
            "intent": "逆の証明の段取り（3点で円を決める→同じ側に C′ をとる→角が等しい→円周角の定理の逆）を図で追えるようにする",
            "src": "lesson_06.md §3（内接する条件 (1)(2) の直後・穴埋め証明の前）",
            "params": "円 O=(0,0)・半径 3／A=130°・B=210°・C=320°・D=40°・C′=285° の位置／52 px/単位／ラベルは A・B・C・C′・D のみ",
            "checks": ck.items,
            "check_tokens": ["180", "112", "68"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L06_3():
    # --- パラメータ（lesson_06.md §5 練習の後 星形七角形・1つおきに結ぶ） ---
    O, r = (0.0, 0.0), 3.0
    n, step = 7, 2                                 # 7点を 2 つ先（1つおき）へ結ぶ
    W, H = 640, 440
    fr = Frame(320, 230, 56)
    fs = fs_for(W)

    pts = [pt_on_circle(O, r, 90.0 + 360.0 * i / n) for i in range(n)]
    order = [(step * i) % n for i in range(n)]     # A₁→A₃→A₅→A₇→A₂→A₄→A₆→A₁
    ck = Checker()
    ck.ok("結び順 A₁→A₃→A₅→A₇→A₂→A₄→A₆ が7点を1度ずつ通る", sorted(order) == list(range(n)) and order == [0, 2, 4, 6, 1, 3, 5])
    tips = []
    for i in range(n):
        v = pts[order[i]]
        p, q = pts[order[i - 1]], pts[order[(i + 1) % n]]
        tips.append(angle_at(v, p, q))
    expect = 180.0 * (n - 2 * step) / n            # 先端の角＝角の内側の弧（(n−2·step) 区間）に対する円周角
    ck.ok("各先端の角＝内側の弧（3区間）に対する円周角＝3×180°/7（1e-9）", all(near(t, expect) for t in tips), f"角={tips[0]:.4f}")
    ck.ok("先端の角の和＝7×(3×180°/7)（1e-9・値は図に書かない）", near(sum(tips), n * expect))

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, O, r, w=AUX_W)
    cv.polyline([fr.P(pts[k]) for k in order], w=MAIN_W, close=True)
    for i in range(n):
        dot_m(cv, fr, pts[i])
        lab = "A" + "₁₂₃₄₅₆₇"[i]
        labels.append(lab)
        label_dir(cv, fr, pts[i], 90.0 + 360.0 * i / n, 20, lab, fs, weight="bold")
    angle_arc(cv, fr, pts[0], pts[order[-1]], pts[order[1]], r=24, n=1)
    ck.ok("図中ラベルに算用数字を含まない（添字は下付き文字）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L06_fig3_star_heptagon.svg", "lesson": "L06", "canvas": cv,
            "title": "星形七角形——円周上の7点 A₁〜A₇ を1つおきに結んだ図（先端 A₁ の角に弧）",
            "desc": "半径 3 の円周上に A₁（真上）から反時計回りに等間隔で7点をとり、A₁→A₃→A₅→A₇→A₂→A₄→A₆→A₁ と結ぶ。先端 A₁ の角に1重の弧を付ける。角の値・和は書かない。同型図は点の数 n と結ぶ間隔 step を差し替えて生成する（2つおきなら step=3）",
            "alt": "星形七角形——円周上の7点を1つおきに結んだ図。各先端の角は、その角の内側にある弧に対する円周角である",
            "intent": "先端の角を「内側の弧に対する円周角」と見る見方を支える図（stretch S1 の素材）",
            "src": "lesson_06.md §5 練習の後（区切り線の後の星形七角形の段落の直後・stretch の前）",
            "params": "円 O=(0,0)・半径 3／7点は 90°＋360°k/7 の位置／結び順 step=2／56 px/単位／ラベルは A₁〜A₇ のみ",
            "checks": ck.items,
            "check_tokens": ["540", "180", "360"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L07_1():
    # --- パラメータ（lesson_07.md §2 接線の長さ） ---
    O, r = (0.0, 0.0), 2.0
    P = (5.2, 0.0)
    W, H = 640, 360
    fr = Frame(140, 180, 60)
    fs = fs_for(W)

    M = mid(O, P)
    A, B = circle_circle(O, r, M, dist(M, O))       # OP を直径とする円との交点＝接点
    if A[1] < B[1]:
        A, B = B, A                                # A を上側にする
    ck = Checker()
    ck.ok("A・B は円 O の周上（1e-9）", on_circle(A, O, r) and on_circle(B, O, r))
    ck.ok("OA⊥PA・OB⊥PB（内積 0・1e-9）", near(dot(sub(A, O), sub(A, P)), 0.0) and near(dot(sub(B, O), sub(B, P)), 0.0))
    ck.ok("PA=PB（1e-9）", near(dist(P, A), dist(P, B)))
    ck.ok("△OAP≡△OBP（3辺が等しい・1e-9）", near(dist(O, A), dist(O, B)) and near(dist(A, P), dist(B, P)))

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, O, r)
    seg(cv, fr, P, A)
    seg(cv, fr, P, B)
    seg(cv, fr, O, A, w=AUX_W)
    seg(cv, fr, O, B, w=AUX_W)
    seg(cv, fr, O, P, w=AUX_W, dash=DASH)
    right_angle(cv, fr, A, O, P)
    right_angle(cv, fr, B, O, P)
    tick(cv, fr, O, A, n=1)
    tick(cv, fr, O, B, n=1)
    tick(cv, fr, P, A, n=2)
    tick(cv, fr, P, B, n=2)
    for p in (O, P, A, B):
        dot_m(cv, fr, p)
    for p, lab, deg in ((O, "O", 180), (P, "P", 0), (A, "A", 90), (B, "B", 270)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 18, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L07_fig1_tangent_lengths.svg", "lesson": "L07", "canvas": cv,
            "title": "接線の長さ——円 O の外の点 P から引いた2本の接線 PA・PB と、直角三角形 OAP・OBP",
            "desc": "半径 2 の円 O と、中心から 5.2 離れた外部の点 P。接点 A（上）・B（下）を OP を直径とする円との交点として座標計算し、接線 PA・PB、半径 OA・OB（細線・ティック1本）、OP（破線）を描く。A・B に直角マーク、PA・PB にティック2本。数値は書かない。同型図は半径と P の位置を差し替えて生成する",
            "alt": "円 O の外の点 P から引いた2本の接線——接点 A、B について OA⊥PA、OB⊥PB で、直角三角形 OAP と OBP は斜辺 OP を共有し OA=OB だから合同。よって PA=PB",
            "intent": "接線⊥半径から2つの直角三角形の合同（斜辺と他の1辺）を読み、PA=PB に至る証明の図",
            "src": "lesson_07.md §2（接線の長さの性質の直後・穴埋め証明の前）",
            "params": "円 O=(0,0)・半径 2・P=(5.2,0)／接点は OP を直径とする円との交点／60 px/単位／ラベルは O・P・A・B のみ",
            "checks": ck.items,
            "check_tokens": ["90", "AF=3", "BD=6", "CE=4"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L07_2():
    # --- パラメータ（lesson_07.md §3 接線と弦のなす角・3つの場合） ---
    O, r = (0.0, 0.0), 1.6
    cases = [("(i) 直角", 90.0, 180.0), ("(ii) 鋭角", 30.0, 150.0), ("(iii) 鈍角", 120.0, 195.0)]   # (名前, B の角度, C の角度)
    W, H = 960, 330
    fs = 17                                       # 3パネルのため幅の 3% より小さい（逸脱として記録）
    frames = [Frame(160 + 320 * i, 150, 52) for i in range(3)]
    A = pt_on_circle(O, r, 270.0)                  # 接点（真下）
    T = (A[0] + 1.5, A[1])                         # 接線上の点（右）

    ck = Checker()
    for (name, bdeg, cdeg), fr in zip(cases, frames):
        B, C = pt_on_circle(O, r, bdeg), pt_on_circle(O, r, cdeg)
        tab, acb = angle_at(A, T, B), angle_at(C, A, B)
        ck.ok(f"{name}: 接線 AT⊥半径 OA（内積 0）", near(dot(sub(T, A), sub(O, A)), 0.0))
        ck.ok(f"{name}: C は角 TAB の内側の弧の反対側（直線 AB について T と反対側）", not same_side(C, T, A, B))
        ck.ok(f"{name}: ∠TAB=∠ACB（1e-9）", near(tab, acb), f"∠TAB={tab:.4f} ∠ACB={acb:.4f}")
        kind = "直角" if near(tab, 90.0) else ("鋭角" if tab < 90 else "鈍角")
        ck.ok(f"{name}: 角の種類が名前と一致", name.endswith(kind))
        if kind == "直角":
            ck.ok("(i): AB は直径（O が AB 上・1e-9）", near(cross(sub(B, A), sub(O, A)), 0.0))

    cv = Canvas(W, H)
    labels = []
    for (name, bdeg, cdeg), fr in zip(cases, frames):
        B, C = pt_on_circle(O, r, bdeg), pt_on_circle(O, r, cdeg)
        circle_path(cv, fr, O, r)
        seg(cv, fr, (A[0] - 1.9, A[1]), T)         # 接線
        seg(cv, fr, A, B)
        seg(cv, fr, C, A, w=AUX_W)
        seg(cv, fr, C, B, w=AUX_W)
        if name.startswith("(i)"):
            right_angle(cv, fr, A, T, B)
            right_angle(cv, fr, C, A, B)
        else:
            angle_arc(cv, fr, A, T, B, r=20, n=1)
            angle_arc(cv, fr, C, A, B, r=20, n=1)
        for p in (A, B, C, T):
            dot_m(cv, fr, p)
        for p, lab, deg in ((A, "A", 270), (B, "B", bdeg), (C, "C", cdeg), (T, "T", 315)):
            labels.append(lab)
            label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
        caption(cv, fr.P(O)[0], 312, name, fs, labels)
    ck.ok("図中の数字はない（パネル番号はローマ数字）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L07_fig2_tangent_chord_angle.svg", "lesson": "L07", "canvas": cv,
            "title": "接線と弦のなす角の3つの場合——(i) ∠TAB が直角（AB は直径）・(ii) 鋭角・(iii) 鈍角。いずれも ∠TAB=∠ACB",
            "desc": "半径 1.6 の円の真下の点 A における接線（水平・T は右）と弦 AB を、B の位置を 90°（直径）・30°（鋭角）・120°（鈍角）に変えた3パネル。C は角 TAB の内側の弧の反対側の円周上にとり、∠TAB と ∠ACB に同じ1重の弧（(i) は両方に直角マーク）。角度の数値は書かない。同型図は B・C の角度位置を差し替えて生成する",
            "alt": "接線と弦のなす角の3つの場合——(i) ∠TAB=90°（AB は直径） (ii) ∠TAB が鋭角 (iii) ∠TAB が鈍角。どの場合も ∠TAB は角の内側の弧 AB に対する円周角 ∠ACB に等しい",
            "intent": "接弦定理の3つの場合分けを同じ配置で並べ、どの場合も「角の内側の弧に対する円周角」と等しいことを読ませる",
            "src": "lesson_07.md §3（性質の文と「3つの場合に分けて確かめる」の直後）",
            "params": "円 O=(0,0)・半径 1.6・A=270°・T=A の右 1.5／B=90°・30°・120°、C=180°・150°・195°／52 px/単位・3パネル各 320 px／ラベルは A・B・C・T と パネル名",
            "checks": ck.items,
            "check_tokens": ["90°", "180"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 960 の 1.8%）。3パネル並置のため"],
            "allow_texts": labels}


# ===========================================================================
# L08 方べきの定理／L09 2円／L10 作図
# ===========================================================================
def _secant(O, r, P, direction):
    """P を通り direction 向きの直線と円の2交点を、P から近い順に返す"""
    pts = circle_line(O, r, P, add(P, direction))
    return sorted(pts, key=lambda X: dist(P, X))


def fig_L08_1():
    # --- パラメータ（lesson_08.md §2 方べきの定理の3つの形） ---
    O, r = (0.0, 0.0), 1.6
    W, H = 960, 330
    fs = 17                                       # 3パネルのため幅の 3% より小さい（逸脱として記録）
    frames = [Frame(160 + 320 * i, 150, 44) for i in range(3)]
    P_in, d1_in, d2_in = (0.45, 0.3), (1.0, 0.4), (-0.35, 1.0)
    P_out, d1_out, d2_out = (-3.4, 0.0), (1.0, 0.34), (1.0, -0.36)

    ck = Checker()
    panels = []
    # (i) 内部
    A, B = _secant(O, r, P_in, d1_in)
    C, D = _secant(O, r, P_in, d2_in)
    ck.ok("(i): P は円の内部", dist(P_in, O) < r)
    ck.ok("(i): PA×PB=PC×PD（1e-9）", near(dist(P_in, A) * dist(P_in, B), dist(P_in, C) * dist(P_in, D)),
          f"{dist(P_in, A) * dist(P_in, B):.6f}")
    panels.append(("(i) 内部", P_in, [("A", A), ("B", B), ("C", C), ("D", D)], [(A, B), (C, D)]))
    # (ii) 外部・2本の割線
    A, B = _secant(O, r, P_out, d1_out)
    C, D = _secant(O, r, P_out, d2_out)
    ck.ok("(ii): P は円の外部・P—A—B、P—C—D の順", dist(P_out, O) > r and dist(P_out, A) < dist(P_out, B) and dist(P_out, C) < dist(P_out, D))
    ck.ok("(ii): PA×PB=PC×PD（1e-9）", near(dist(P_out, A) * dist(P_out, B), dist(P_out, C) * dist(P_out, D)))
    panels.append(("(ii) 外部", P_out, [("A", A), ("B", B), ("C", C), ("D", D)], [(P_out, B), (P_out, D)]))
    # (iii) 外部・割線と接線
    A, B = _secant(O, r, P_out, d2_out)
    M = mid(O, P_out)
    T1, T2 = circle_circle(O, r, M, dist(M, O))
    T = T1 if T1[1] > T2[1] else T2                # 上側の接点
    ck.ok("(iii): T は接点（OT⊥PT・内積 0）", on_circle(T, O, r) and near(dot(sub(T, O), sub(T, P_out)), 0.0))
    ck.ok("(iii): PA×PB=PT²（1e-9）", near(dist(P_out, A) * dist(P_out, B), dist(P_out, T) ** 2))
    panels.append(("(iii) 接線", P_out, [("A", A), ("B", B), ("T", T)], [(P_out, B), (P_out, T)]))

    cv = Canvas(W, H)
    labels = []
    for (name, P, named, segs), fr in zip(panels, frames):
        circle_path(cv, fr, O, r)
        for a, b in segs:
            seg(cv, fr, a, b)
        dot_m(cv, fr, P)
        labels.append("P")
        label_dir(cv, fr, P, 270 if name.startswith("(i)") else 180, 16, "P", fs, weight="bold")
        for lab, X in named:
            dot_m(cv, fr, X)
            labels.append(lab)
            deg = math.degrees(math.atan2(X[1] - O[1], X[0] - O[0]))
            label_dir(cv, fr, X, deg, 17, lab, fs, weight="bold")
        caption(cv, fr.P(O)[0], 312, name, fs, labels)
    ck.ok("図中の数字はない（パネル番号はローマ数字）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L08_fig1_power_of_point.svg", "lesson": "L08", "canvas": cv,
            "title": "方べきの定理の3つの形——(i) P が内部（2弦の交点）・(ii) P が外部（2本の割線）・(iii) P が外部で一方が接線",
            "desc": "半径 1.6 の同じ円を3パネルに描く。(i) 内部の点 P=(0.45,0.3) を通る2本の弦 AB・CD。(ii) 外部の点 P=(−3.4,0) から2本の割線を引き、近い順に A・B と C・D。(iii) 同じ P から割線 PAB と接線 PT（接点 T は OP を直径とする円との交点）。長さの数値は書かない。同型図は P と直線の向きを差し替えて生成する",
            "alt": "方べきの定理の3つの形——(i) P が円の内部（2つの弦の交点） (ii) P が円の外部（2本の割線） (iii) P が円の外部で一方が接線。どの形でも、P から測った2つの交点までの長さの積が等しい",
            "intent": "3つの形を「P を通る2直線が円と交わる（接する）」の1本の式で見る土台の図",
            "src": "lesson_08.md §2（定理の式の直後・(i) の穴埋め証明の前）",
            "params": "円 O=(0,0)・半径 1.6／(i) P=(0.45,0.3)・向き (1,0.4)・(−0.35,1)／(ii)(iii) P=(−3.4,0)・向き (1,0.34)・(1,−0.36)／44 px/単位・3パネル各 320 px／ラベルは P・A・B・C・D・T と パネル名",
            "checks": ck.items,
            "check_tokens": ["12", "PT=", "=6"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 960 の 1.8%）。3パネル並置のため"],
            "allow_texts": labels}


def fig_L08_2():
    # --- パラメータ（lesson_08.md §3 方べきの定理の逆・P が内部／外部の2パネル） ---
    O, r = (0.0, 0.0), 1.7
    W, H = 640, 330
    fs = 17                                       # 2パネルのため幅の 3% より小さい（逸脱として記録）
    frL, frR = Frame(150, 150, 44), Frame(490, 150, 44)
    P_in, d1_in, d2_in = (0.35, 0.25), (1.0, 0.55), (-0.45, 1.0)
    P_out, d1_out, d2_out = (-3.4, 0.0), (1.0, 0.36), (1.0, -0.3)

    ck = Checker()
    A, B = _secant(O, r, P_in, d1_in)
    C, D = _secant(O, r, P_in, d2_in)
    ck.ok("内部: PA×PB=PC×PD かつ4点が同一円周上（1e-9）",
          near(dist(P_in, A) * dist(P_in, B), dist(P_in, C) * dist(P_in, D)) and all(on_circle(X, O, r) for X in (A, B, C, D)))
    ck.ok("内部: △PAC∽△PDB（PA:PD=PC:PB・対頂角）", near(dist(P_in, A) / dist(P_in, D), dist(P_in, C) / dist(P_in, B))
          and near(angle_at(P_in, A, C), angle_at(P_in, D, B)))
    ck.ok("内部: ∠PAC=∠PDB（1e-9）", near(angle_at(A, P_in, C), angle_at(D, P_in, B)))
    inner = (A, B, C, D)
    A2, B2 = _secant(O, r, P_out, d1_out)
    C2, Dq = _secant(O, r, P_out, d2_out)
    ck.ok("外部: PA×PB=PC×PD かつ4点が同一円周上（1e-9）",
          near(dist(P_out, A2) * dist(P_out, B2), dist(P_out, C2) * dist(P_out, Dq)) and all(on_circle(X, O, r) for X in (A2, B2, C2, Dq)))
    ck.ok("外部: ∠PAC=∠PDB（外角＝内対角・1e-9）", near(angle_at(A2, P_out, C2), angle_at(Dq, P_out, B2)))

    cv = Canvas(W, H)
    labels = []
    for fr, P, (A, B, C, D), name in ((frL, P_in, inner, "P が内部"), (frR, P_out, (A2, B2, C2, Dq), "P が外部")):
        fill_poly(cv, fr, [P, A, C])
        circle_path(cv, fr, O, r, w=AUX_W, dash=DASH)
        if name.endswith("内部"):
            seg(cv, fr, A, B); seg(cv, fr, C, D)
        else:
            seg(cv, fr, P, B); seg(cv, fr, P, D)
        seg(cv, fr, A, C); seg(cv, fr, D, B)
        angle_arc(cv, fr, A, P, C, r=16, n=1)
        angle_arc(cv, fr, D, P, B, r=16, n=1)
        dot_m(cv, fr, P)
        labels.append("P")
        label_dir(cv, fr, P, 270 if name.endswith("内部") else 180, 16, "P", fs, weight="bold")
        for lab, X in (("A", A), ("B", B), ("C", C), ("D", D)):
            dot_m(cv, fr, X)
            labels.append(lab)
            deg = math.degrees(math.atan2(X[1] - O[1], X[0] - O[0]))
            label_dir(cv, fr, X, deg, 17, lab, fs, weight="bold")
        caption(cv, fr.P(O)[0], 312, name, fs, labels)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L08_fig2_power_converse.svg", "lesson": "L08", "canvas": cv,
            "title": "方べきの定理の逆——PA×PB=PC×PD から △PAC∽△PDB を作り、∠PAC=∠PDB で4点が同一円周上と示す（P が内部・外部の2パネル）",
            "desc": "左: 2線分 AB・CD が内部の点 P で交わる形。右: P が外部で P—A—B・P—C—D の順。どちらも △PAC を網かけし、AC・DB を結び、∠PAC と ∠PDB に同じ1重の弧を付ける。結論の円（4点を通る）は破線で添える。数値は書かない。同型図は P と直線の向きを差し替えて生成する",
            "alt": "方べきの定理の逆——PA×PB=PC×PD から △PAC∽△PDB（2組の辺の比とその間の角）が導かれ、∠PAC=∠PDB。P が内部なら円周角の定理の逆、外部なら「外角=内対角」により4点は同一円周上にある",
            "intent": "逆の証明で使う相似な2つの三角形と、等しい2つの角を、内部・外部の両方で同じ配置で見せる",
            "src": "lesson_08.md §3（逆の主張の直後・証明の前）",
            "params": "円 O=(0,0)・半径 1.7／左 P=(0.35,0.25)・向き (1,0.55)・(−0.45,1)／右 P=(−3.4,0)・向き (1,0.36)・(1,−0.3)／44 px/単位・2パネル／ラベルは P・A・B・C・D と パネル名",
            "checks": ck.items,
            "check_tokens": ["12", "=6"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 640 の 2.7%）。2パネル並置のため"],
            "allow_texts": labels}


def fig_L09_1():
    # --- パラメータ（lesson_09.md §2 2円の位置関係5分類） ---
    r, r2 = 1.6, 1.0
    cases = [("(1) 互いに外部", 3.3), ("(2) 外接", r + r2), ("(3) 2点で交わる", 1.8), ("(4) 内接", r - r2), ("(5) 一方が内部", 0.3)]
    W, H = 960, 250
    fs = 15                                       # 5パネルのため幅の 3% より小さい（逸脱として記録）
    frames = [Frame(60 + 192 * i, 110, 26) for i in range(5)]

    ck = Checker()
    for name, d in cases:
        if d > r + r2 + 1e-12:
            kind = "互いに外部"
        elif near(d, r + r2):
            kind = "外接"
        elif d > r - r2 + 1e-12:
            kind = "2点で交わる"
        elif near(d, r - r2):
            kind = "内接"
        else:
            kind = "一方が内部"
        ck.ok(f"{name}: d={d:.2f} と r＋r′={r + r2:.2f}・r−r′={r - r2:.2f} の大小から「{kind}」", name.endswith(kind))
        n_common = len(circle_circle((0.0, 0.0), r, (d, 0.0), r2)) if not (near(d, r + r2) or near(d, r - r2)) else 1
        expect = {"互いに外部": 0, "外接": 1, "2点で交わる": 2, "内接": 1, "一方が内部": 0}[kind]
        ck.ok(f"{name}: 共有点の個数 {expect}", n_common == expect)

    cv = Canvas(W, H)
    labels = []
    for (name, d), fr in zip(cases, frames):
        O, O2 = (0.0, 0.0), (d, 0.0)
        circle_path(cv, fr, O, r)
        circle_path(cv, fr, O2, r2)
        dot_m(cv, fr, O); dot_m(cv, fr, O2)
        labels += ["O", "O′"]
        label_dir(cv, fr, O, 270, 14, "O", fs, weight="bold")
        label_dir(cv, fr, O2, 90 if d < 1.0 else 270, 14, "O′", fs, weight="bold")
        caption(cv, fr.P((d / 2, 0))[0], 232, name, fs, labels)
    ck.ok("図中の数字は分類番号 1〜5 と「2点」のみ", digit_runs(labels) <= {"1", "2", "3", "4", "5"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L09_fig1_two_circles.svg", "lesson": "L09", "canvas": cv,
            "title": "2つの円の位置関係5分類——中心間の距離 d を小さくしていくと 外部→外接→2点で交わる→内接→一方が内部 と移る",
            "desc": "半径 r=1.6 の円 O と半径 r′=1 の円 O′ を、d=3.3・2.6・1.8・0.6・0.3 の5パネルに描く。境目の値 d=r＋r′（外接）・d=r−r′（内接）を含む。長さの数値は書かない。同型図は r・r′・d の組を差し替えて生成する（分類は自動判定）",
            "alt": "2つの円の位置関係——中心間の距離 d を大きい方から小さくしていくと、(1) 互いに外部 (2) 外接 (3) 2点で交わる (4) 内接 (5) 一方が他方の内部、の順に移り変わる",
            "intent": "d と r＋r′・r−r′ の大小で5分類が決まることを、同じ2円の距離だけを変えた並びで観察させる",
            "src": "lesson_09.md §2（「次の順に変わる」の直後・分類表の前）",
            "params": "r=1.6・r′=1／d=3.3・2.6・1.8・0.6・0.3／26 px/単位・5パネル各 192 px／ラベルは O・O′ と 分類名",
            "checks": ck.items,
            "check_tokens": ["11", "3<d"],
            "digit_rule": ("subset", {"1", "2", "3", "4", "5"}),
            "deviations": ["文字サイズ 15 px（幅 960 の 1.6%）。5パネル並置のため"],
            "allow_texts": labels}


def fig_L09_2():
    # --- パラメータ（lesson_09.md §3 共通接線の長さ・外接線と内接線） ---
    r, r2, d = 2.0, 1.2, 5.0
    W, H = 640, 330
    fs = 17                                       # 2パネルのため幅の 3% より小さい（逸脱として記録）
    frL, frR = Frame(95, 175, 32), Frame(415, 175, 32)
    O, O2 = (0.0, 0.0), (d, 0.0)

    ck = Checker()
    # 共通外接線: 法線 n が n·O′=r−r′
    nx = (r - r2) / d
    n_ext = (nx, math.sqrt(1 - nx * nx))
    A_e, B_e = mul(n_ext, r), add(O2, mul(n_ext, r2))
    H_e = foot(O2, O, A_e)
    ck.ok("外接線: OA⊥AB・O′B⊥AB（内積 0）", near(dot(sub(B_e, A_e), sub(A_e, O)), 0.0) and near(dot(sub(B_e, A_e), sub(B_e, O2)), 0.0))
    ck.ok("外接線: OH=r−r′・O′H=AB（1e-9）", near(dist(O, H_e), r - r2) and near(dist(O2, H_e), dist(A_e, B_e)))
    ck.ok("外接線: AB²=d²−(r−r′)²（1e-9）", near(dist(A_e, B_e) ** 2, d * d - (r - r2) ** 2))
    # 共通内接線: 法線 n が n·O′=r＋r′、B は O′ から −n 側
    nx = (r + r2) / d
    n_int = (nx, math.sqrt(1 - nx * nx))
    A_i, B_i = mul(n_int, r), add(O2, mul(n_int, -r2))
    H_i = add(O2, mul(n_int, -(r + r2)))         # O′B を B の側に延長した直線上
    ck.ok("内接線: OA⊥AB・O′B⊥AB（内積 0）", near(dot(sub(B_i, A_i), sub(A_i, O)), 0.0) and near(dot(sub(B_i, A_i), sub(B_i, O2)), 0.0))
    ck.ok("内接線: H は O′B の延長上・OABH は長方形・O′H=r＋r′（1e-9）",
          near(cross(sub(H_i, O2), sub(B_i, O2)), 0.0) and near_pt(sub(H_i, O), sub(B_i, A_i)) and near(dist(O2, H_i), r + r2))
    ck.ok("内接線: AB²=d²−(r＋r′)²（1e-9）", near(dist(A_i, B_i) ** 2, d * d - (r + r2) ** 2))

    cv = Canvas(W, H)
    labels = []
    for fr, (A, B, Hh), name, ext in ((frL, (A_e, B_e, H_e), "共通外接線", True), (frR, (A_i, B_i, H_i), "共通内接線", False)):
        circle_path(cv, fr, O, r)
        circle_path(cv, fr, O2, r2)
        tl = add(A, mul(unit(sub(B, A)), -0.8))
        tr = add(B, mul(unit(sub(B, A)), 0.8))
        seg(cv, fr, tl, tr)                        # 共通接線
        seg(cv, fr, O, A, w=AUX_W)
        seg(cv, fr, O2, B, w=AUX_W)
        seg(cv, fr, O, O2, w=AUX_W, dash=DASH)
        if ext:
            seg(cv, fr, O2, Hh, w=AUX_W, dash=DASH)
            right_angle(cv, fr, Hh, O, O2, size=9)
        else:
            seg(cv, fr, B, Hh, w=AUX_W, dash=DASH)
            seg(cv, fr, O, Hh, w=AUX_W, dash=DASH)
            right_angle(cv, fr, Hh, O, O2, size=9)
        right_angle(cv, fr, A, O, B, size=9)
        right_angle(cv, fr, B, O2, A, size=9)
        for p in (O, O2, A, B, Hh):
            dot_m(cv, fr, p)
        for p, lab, deg in ((O, "O", 270), (O2, "O′", 270 if ext else 45), (A, "A", 90 if ext else 120), (B, "B", 90 if ext else 300), (Hh, "H", 225 if ext else 300)):
            labels.append(lab)
            label_dir(cv, fr, p, deg, 16, lab, fs, weight="bold")
        side_label(cv, fr, O, A, O2, "r", fs, off=12, t=0.7 if ext else 0.5)
        side_label(cv, fr, O2, B, O, "r′", fs, off=12, t=0.5)
        labels += ["r", "r′"]
        caption(cv, fr.P((d / 2, 0))[0], 312, name, fs, labels)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L09_fig2_common_tangents.svg", "lesson": "L09", "canvas": cv,
            "title": "共通接線の長さ——左: 共通外接線（O′ から OA に垂線 O′H・OH=r−r′）、右: 共通内接線（O′B の延長へ O から垂線 OH・O′H=r＋r′）",
            "desc": "半径 r=2 の円 O と半径 r′=1.2 の円 O′（中心間 5）。左パネルは共通外接線 AB と、O′ から OA へ下ろした垂線の足 H（直角三角形 OO′H）。右パネルは共通内接線 AB と、O′B を B の側に延長した直線へ O から下ろした垂線の足 H（長方形 OABH）。半径に r・r′ のラベル。長さの数値は書かない。同型図は r・r′・d を差し替えて生成する",
            "alt": "共通接線の長さ——左: 共通外接線。O′ から OA に垂線 O′H を下ろすと直角三角形 OO′H ができ、OH=r−r′、O′H=AB。右: 共通内接線。O′B を B の側に延長した直線に O から垂線 OH を下ろすと直角三角形 OO′H ができ、OH=AB、O′H=r＋r′",
            "intent": "共通接線の長さを三平方の定理で求めるための直角三角形（OO′H）を、外接線・内接線の両方で見せる",
            "src": "lesson_09.md §3（共通接線の長さの定義の直後・公式の導出の前）",
            "params": "r=2・r′=1.2・d=5／接点は法線ベクトルの条件 n·OO′=r∓r′ から座標計算／32 px/単位・2パネル／ラベルは O・O′・A・B・H・r・r′ と パネル名",
            "checks": ck.items,
            "check_tokens": ["24", "√", "=4"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 640 の 2.7%）。2パネル並置のため"],
            "allow_texts": labels}


def fig_L10_1():
    # --- パラメータ（lesson_10.md §2 内分点・外分点の作図） ---
    A, B, m, n = DIV_A, DIV_B, DIV_M, DIV_N        # L01_fig1 と同じ線分・同じ比 2:1
    u = 1.3                                        # 単位の長さ
    ldeg = 38.0                                    # 直線 ℓ の向き
    W, H = 640, 400
    fr = Frame(70, 220, 36)
    fs = fs_for(W)

    e = (math.cos(ldeg * DEG), math.sin(ldeg * DEG))
    C = add(A, mul(e, u * m))                      # ℓ 上・AC=単位×m
    D = add(B, mul(e, -u * n))                     # k 上・直線 AB について C と反対側・BD=単位×n
    Dq = add(B, mul(e, u * n))                     # k 上・C と同じ側
    P = line_x(C, D, A, B)
    Q = line_x(C, Dq, A, B)
    ck = Checker()
    ck.ok("AC∥BD（ℓ∥k）・AC:BD=m:n=2:1", near(cross(sub(C, A), sub(D, B)), 0.0) and near(dist(A, C) / dist(B, D), m / n))
    ck.ok("D は直線 AB について C と反対側・D′ は同じ側", not same_side(C, D, A, B) and same_side(C, Dq, A, B))
    ck.ok("P は AB を 2:1 に内分（L01_fig1 の P と一致・1e-9）", near_pt(P, divide(A, B, m, n, True)) and 0 < param_on(P, A, B) < 1)
    ck.ok("Q は AB を 2:1 に外分（L01_fig1 の Q と一致・B の側・1e-9）", near_pt(Q, divide(A, B, m, n, False)) and param_on(Q, A, B) > 1)
    ck.ok("△PAC∽△PBD（AP:PB=AC:BD）", near(dist(A, P) / dist(P, B), dist(A, C) / dist(B, D)))

    cv = Canvas(W, H)
    labels = []
    seg(cv, fr, add(A, mul(e, -0.6)), add(A, mul(e, 3.6)), w=AUX_W)       # ℓ
    seg(cv, fr, add(B, mul(e, -2.2)), add(B, mul(e, 2.2)), w=AUX_W)       # k
    seg(cv, fr, add(A, (-0.5, 0)), add(Q, (0.6, 0)), w=AUX_W, dash=DASH)  # 直線 AB
    seg(cv, fr, A, B, w=BOLD_W)
    seg(cv, fr, C, D)
    seg(cv, fr, C, Q)
    par_mark(cv, fr, A, C, n=1, t=0.5)
    par_mark(cv, fr, D, Dq, n=1, t=0.8)
    for p in (A, B, C, D, Dq, P, Q):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 250), (B, "B", 300), (C, "C", 150), (D, "D", 0), (Dq, "D′", 0), (P, "P", 270), (Q, "Q", 270)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 17, lab, fs, weight="bold")
    labels += ["ℓ", "k"]
    label_dir(cv, fr, add(A, mul(e, 3.6)), 90, 14, "ℓ", fs)
    label_dir(cv, fr, add(B, mul(e, 2.2)), 90, 14, "k", fs)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L10_fig1_construct_division.svg", "lesson": "L10", "canvas": cv,
            "title": "内分点・外分点の作図——A を通る直線 ℓ と B を通る平行線 k に、AC=（単位）×m・BD=（単位）×n をとり、直線 CD・CD′ と AB の交点 P・Q",
            "desc": "線分 AB（太線）に対し、A を通る直線 ℓ（38°）と B を通り ℓ に平行な直線 k を引く。ℓ 上に AC（単位の 2 倍）、k 上に BD（単位の 1 倍・AB について C と反対側）と BD′（同じ側）をとる。直線 CD と AB の交点 P が 2:1 の内分点、直線 CD′ と AB の交点 Q が 2:1 の外分点（B の側）。数値は書かない。同型図は比 m:n と ℓ の向きを差し替えて生成する",
            "alt": "内分点・外分点の作図——A を通る直線 ℓ と、B を通り ℓ に平行な直線 k を引く。ℓ 上に AC=m（単位の長さの m 倍）、k 上に BD=n をとる。D を直線 AB について C と反対側にとれば直線 CD は AB を m:n に内分する点 P で、同じ側にとれば m:n に外分する点 Q で交わる",
            "intent": "平行線で相似な三角形を作って比を移す作図の手順と、D の側で内分・外分が切り替わることを1枚で見せる",
            "src": "lesson_10.md §2（作図の方針の直後・手順の箇条書きの前）",
            "params": "A=(0,0)・B=(6,0)・m:n=2:1（L01_fig1 と同一）・単位 1.3・ℓ の向き 38°／P・Q は直線の交点として座標計算／36 px/単位／ラベルは A・B・C・D・D′・P・Q・ℓ・k",
            "checks": ck.items,
            "check_tokens": ["2:1", "12", "=4"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L10_2():
    # --- パラメータ（lesson_10.md §3 √a の作図） ---
    a = 3.0                                        # 図では a=3 の比で描くが、ラベルは 1・a・√a（例題2の答え √3 は書かない）
    W, H = 640, 330
    fr = Frame(100, 270, 110)
    fs = fs_for(W)

    A, C, B = (0.0, 0.0), (1.0, 0.0), (1.0 + a, 0.0)
    M = mid(A, B)
    R = dist(A, B) / 2
    D = (C[0], math.sqrt(1.0 * a))
    ck = Checker()
    ck.ok("A・C・B はこの順に一直線上・AC=1・CB=a", near(dist(A, C), 1.0) and near(dist(C, B), a) and 0 < param_on(C, A, B) < 1)
    ck.ok("D は AB を直径とする円の周上（1e-9）", on_circle(D, M, R))
    ck.ok("CD⊥AB（内積 0）", near(dot(sub(D, C), sub(B, A)), 0.0))
    ck.ok("CD²=AC×CB=a（1e-9）", near(dist(C, D) ** 2, dist(A, C) * dist(C, B)) and near(dist(C, D) ** 2, a))
    ck.ok("∠ADB=90°（直径に対する円周角・1e-9）", near(angle_at(D, A, B), 90.0))

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    arc_m(cv, fr, M, R, 0.0, 180.0)
    seg(cv, fr, A, B)
    seg(cv, fr, C, D)
    seg(cv, fr, A, D, w=AUX_W, dash=DASH)
    seg(cv, fr, B, D, w=AUX_W, dash=DASH)
    right_angle(cv, fr, C, B, D)
    right_angle(cv, fr, D, A, B)
    for p in (A, C, B, D):
        dot_m(cv, fr, p)
    for p, lab, deg in ((A, "A", 270), (C, "C", 270), (B, "B", 270), (D, "D", 90)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 18, lab, fs, weight="bold")
    T(*fr.P((0.5, -0.42)), "1")
    T(*fr.P((1.0 + a / 2, -0.42)), "a")
    T(fr.P((1.0, math.sqrt(a) / 2))[0] + 22, fr.P((1.0, math.sqrt(a) / 2))[1] + fs * 0.35, "√a", anchor="start")
    ck.ok("図中の数字は 1 のみ（CD の値は √a と書く）", digit_runs(labels) == {"1"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L10_fig2_construct_sqrt.svg", "lesson": "L10", "canvas": cv,
            "title": "√a の長さの作図——AC=1・CB=a を並べた AB を直径とする半円と、C で AB に垂直な直線の交点 D（CD=√a）",
            "desc": "直線上に A・C・B をこの順にとり（AC=1・CB=a、図は a=3 の比）、AB を直径とする半円をかく。C で AB に垂直な直線と半円の交点 D をとり、AD・BD を破線で結ぶ（∠ADB は直角）。ラベルは 1・a・√a のみ。同型図は a を差し替えて生成する",
            "alt": "√a の作図——AC=1、CB=a をこの順に並べた線分 AB を直径とする半円をかき、C で AB に垂直な直線を引いて半円との交点を D とする。CD²=AC×CB=a",
            "intent": "方べきの定理（または相似）で CD²=1×a となる作図の形を見せる",
            "src": "lesson_10.md §3（√a の作図の手順の直後・根拠の前）",
            "params": "A=(0,0)・C=(1,0)・B=(1＋a,0)・a=3（比のみ）／D=(1,√a)／110 px/単位／ラベルは A，B，C，D と 1，a，√a",
            "checks": ck.items,
            "check_tokens": ["√3", "3", "4"],
            "digit_rule": ("subset", {"1"}),
            "allow_texts": labels}


def fig_L10_3():
    # --- パラメータ（lesson_10.md §4 円外の点からの接線の作図） ---
    O, r = (0.0, 0.0), 1.8
    P = (5.0, 0.0)
    W, H = 640, 360
    fr = Frame(130, 180, 60)
    fs = fs_for(W)

    M = mid(O, P)
    Q, Q2 = circle_circle(O, r, M, dist(M, O))
    if Q[1] < Q2[1]:
        Q, Q2 = Q2, Q
    ck = Checker()
    ck.ok("M は OP の中点・円 M は O と P を通る（1e-9）", near_pt(M, ((O[0] + P[0]) / 2, 0.0)) and near(dist(M, O), dist(M, P)))
    ck.ok("Q・Q′ は円 O と円 M の両方の周上（1e-9）", all(on_circle(X, O, r) and on_circle(X, M, dist(M, O)) for X in (Q, Q2)))
    ck.ok("∠OQP=∠OQ′P=90°（1e-9）", near(angle_at(Q, O, P), 90.0) and near(angle_at(Q2, O, P), 90.0))
    ck.ok("PQ⊥OQ・PQ′⊥OQ′（接線⊥半径・内積 0）", near(dot(sub(P, Q), sub(O, Q)), 0.0) and near(dot(sub(P, Q2), sub(O, Q2)), 0.0))
    ck.ok("2円の共有点はちょうど2個（接線は2本で全部）", len(circle_circle(O, r, M, dist(M, O))) == 2)

    cv = Canvas(W, H)
    labels = []
    circle_path(cv, fr, O, r)
    circle_path(cv, fr, M, dist(M, O), w=AUX_W, dash=DASH)
    seg(cv, fr, O, P, w=AUX_W)
    seg(cv, fr, P, Q); seg(cv, fr, P, Q2)
    seg(cv, fr, O, Q, w=AUX_W); seg(cv, fr, O, Q2, w=AUX_W)
    right_angle(cv, fr, Q, O, P)
    right_angle(cv, fr, Q2, O, P)
    for p in (O, P, M, Q, Q2):
        dot_m(cv, fr, p)
    for p, lab, deg in ((O, "O", 180), (P, "P", 0), (M, "M", 270), (Q, "Q", 90), (Q2, "Q′", 270)):
        labels.append(lab)
        label_dir(cv, fr, p, deg, 18, lab, fs, weight="bold")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L10_fig3_construct_tangent.svg", "lesson": "L10", "canvas": cv,
            "title": "円外の点 P からの接線の作図——OP を直径とする円（破線）と円 O の交点 Q・Q′ が接点、接線は PQ・PQ′ の2本",
            "desc": "半径 1.8 の円 O と外部の点 P=(5,0)。OP の中点 M を中心とし OP を直径とする円を破線でかき、円 O との交点 Q（上）・Q′（下）をとる。PQ・PQ′ が接線で、Q・Q′ に直角マーク。数値は書かない。同型図は半径と P の位置を差し替えて生成する",
            "alt": "円外の点 P からの接線の作図——OP を直径とする円と円 O の2つの交点 Q、Q′ について、∠OQP=∠OQ′P=90° だから PQ、PQ′ は接線。接点は OP を直径とする円周上にしかないので、接線はこの2本で全部",
            "intent": "作図の根拠（直径に対する円周角）と検証②「他に無いか」（2円の共有点は2個）を1枚で見せる",
            "src": "lesson_10.md §4（作図の手順 1〜3 の直後・根拠の前）",
            "params": "円 O=(0,0)・半径 1.8・P=(5,0)・M=(2.5,0)／Q・Q′ は2円の交点として座標計算／60 px/単位／ラベルは O・P・M・Q・Q′ のみ",
            "checks": ck.items,
            "check_tokens": ["90", "180"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# ===========================================================================
# L11 空間の位置関係／L12 垂線の足・直方体の切断・中点切断
# ===========================================================================
def _cuboid(w, dep, h):
    """直方体 ABCD-EFGH: ABCD が上面・EFGH が下面（A の真下が E）・ABFE が手前の面"""
    E, F, G, Hh = (0.0, 0.0, 0.0), (w, 0.0, 0.0), (w, dep, 0.0), (0.0, dep, 0.0)
    A, B, C, D = (0.0, 0.0, h), (w, 0.0, h), (w, dep, h), (0.0, dep, h)
    return {"A": A, "B": B, "C": C, "D": D, "E": E, "F": F, "G": G, "H": Hh}


def _pair_relation(p, q, r, s):
    """空間の2直線 pq・rs の関係: 交わる／平行／ねじれの位置"""
    u, v = v3(p, q), v3(r, s)
    if math.sqrt(dot3(cross3(u, v), cross3(u, v))) < 1e-9:
        return "平行"
    n = cross3(u, v)
    if abs(dot3(n, v3(p, r))) < 1e-9:
        return "交わる"
    return "ねじれの位置"


def _label3(cv, fr, ob, p, deg, r, s, fs, labels, weight="bold", anchor="middle"):
    labels.append(s)
    label_dir(cv, fr, ob.P(p), deg, r, s, fs, weight=weight, anchor=anchor)


def fig_L11_1():
    # --- パラメータ（lesson_11.md §2 直方体の辺で2直線の3分類・例題1） ---
    w, dep, h = 4.0, 2.6, 2.6
    W, H = 640, 340
    fs = 17                                       # 立体＋一覧のため幅の 3% より小さい（逸脱として記録）
    fr = Frame(50, 290, 44)
    ob = Oblique(0.5, 30.0)
    V = _cuboid(w, dep, h)
    lists = {"交わる": ["AD", "BC", "AE", "BF"], "平行": ["DC", "EF", "HG"], "ねじれの位置": ["DH", "CG", "EH", "FG"]}

    verts = [V[k] for k in "ABCDEFGH"]
    faces = hull_faces(verts)
    edges = solid_edges(faces)
    ck = Checker()
    ck.ok("直方体: 頂点 8・辺 12・面 6", len(verts) == 8 and len(edges) == 12 and len(faces) == 6)
    names = "ABCDEFGH"
    got = {"交わる": [], "平行": [], "ねじれの位置": []}
    for (a, b), _ in edges:
        e = names[a] + names[b]
        if e == "AB":
            continue
        got[_pair_relation(V["A"], V["B"], V[names[a]], V[names[b]])].append(e)
    norm = lambda lst: sorted("".join(sorted(x)) for x in lst)
    for k in lists:
        ck.ok(f"AB と{k}辺＝{'・'.join(lists[k])}（座標から判定）", norm(got[k]) == norm(lists[k]), f"{got[k]}")
    ck.ok("DC∥AB・DC⊥CG（内積 0）→ AB と CG のなす角＝∠DCG=90°",
          _pair_relation(V["A"], V["B"], V["D"], V["C"]) == "平行" and near(dot3(v3(V["C"], V["D"]), v3(V["C"], V["G"])), 0.0))

    cv = Canvas(W, H)
    labels = []
    draw_solid(cv, fr, ob, verts, faces)
    seg(cv, fr, ob.P(V["A"]), ob.P(V["B"]), w=BOLD_W)
    right_angle(cv, fr, ob.P(V["C"]), ob.P(V["D"]), ob.P(V["G"]))
    for k in names:
        dot_m(cv, fr, ob.P(V[k]))
    degs = {"A": 200, "B": 340, "C": 20, "D": 160, "E": 200, "F": 340, "G": 20, "H": 160}
    for k in names:
        _label3(cv, fr, ob, V[k], degs[k], 16, k, fs, labels)
    T = T_factory(cv, labels, fs)
    x0 = 330
    T(x0, 120, "辺 AB と", anchor="start", weight="bold")
    T(x0, 160, "交わる: " + ", ".join(lists["交わる"]), anchor="start")
    T(x0, 200, "平行: " + ", ".join(lists["平行"]), anchor="start")
    T(x0, 240, "ねじれの位置: " + ", ".join(lists["ねじれの位置"]), anchor="start")
    T(x0, 280, "なす角: ∠DCG", anchor="start")
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L11_fig1_lines_in_cuboid.svg", "lesson": "L11", "canvas": cv,
            "title": "直方体 ABCD-EFGH の辺で見る2直線の3分類——辺 AB と交わる辺・平行な辺・ねじれの位置にある辺、なす角は ∠DCG",
            "desc": "直方体 ABCD-EFGH（上面 ABCD・手前の面 ABFE・幅 4・奥行き 2.6・高さ 2.6）を斜投影で描き、辺 AB を太線、隠れた辺を破線にする。頂点 C に ∠DCG の直角マーク。右に、AB と交わる辺・平行な辺・ねじれの位置にある辺の一覧（座標から機械判定した結果と一致）。同型図は寸法を差し替えて生成する",
            "alt": "直方体 ABCD-EFGH の辺で見る2直線の3分類——辺 AB と、交わる辺（AD・BC・AE・BF）、平行な辺（DC・EF・HG）、ねじれの位置にある辺（DH・CG・EH・FG）。ねじれの位置にある辺 CG と AB のなす角は、AB と平行な辺 DC を通して ∠DCG=90° と測れる",
            "intent": "「交わらない2直線」に平行とねじれの位置の2種類があること、ねじれの位置の2直線のなす角を平行な辺へ移して測ることを1枚で見せる",
            "src": "lesson_11.md §2（2直線のなす角の段落の直後・例題1の前）",
            "params": "幅 4・奥行き 2.6・高さ 2.6／斜投影 k=0.5・α=30°／44 px/単位／ラベルは A〜H と一覧文（交わる・平行・ねじれの位置・なす角: ∠DCG）",
            "checks": ck.items,
            "check_tokens": ["90°", "12"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 640 の 2.7%）。立体と一覧の並置のため", "面の可視判定と隠れ線は頂点座標から機械的に決めた（ABFE・ABCD・BCGF が可視）"],
            "allow_texts": labels}


def _plane_quad(cv, fr, ob, corners, w=MAIN_W, fill=None):
    pts = [fr.P(ob.P(c)) for c in corners]
    if fill:
        cv.polygon_fill(pts, fill)
    cv.polyline(pts, w=w, close=True)


def fig_L11_2():
    # --- パラメータ（lesson_11.md §3 直線と平面の垂直の定義） ---
    W, H = 640, 360
    fs = fs_for(W)
    fr = Frame(320, 250, 60)
    ob = Oblique(0.5, 30.0)
    corners = [(-2.6, -1.6, 0.0), (2.6, -1.6, 0.0), (2.6, 1.6, 0.0), (-2.6, 1.6, 0.0)]
    O = (0.0, 0.0, 0.0)
    m = ((-1.9, 0.0, 0.0), (1.9, 0.0, 0.0))
    n = ((0.0, -1.25, 0.0), (0.0, 1.25, 0.0))
    k = ((-1.5, -1.0, 0.0), (1.5, 1.0, 0.0))       # α 上の O を通る別の直線（結論の例・破線）
    l_dir = (0.0, 0.0, 1.0)
    ell = ((0.0, 0.0, -0.7), (0.0, 0.0, 2.4))

    ck = Checker()
    nrm = cross3(v3(*m), v3(*n))
    ck.ok("m・n は α 上で O で交わり平行でない（外積≠0）", math.sqrt(dot3(nrm, nrm)) > 1e-9 and all(p[2] == 0 for p in m + n))
    ck.ok("ℓ⊥m・ℓ⊥n（内積 0）", near(dot3(l_dir, v3(*m)), 0.0) and near(dot3(l_dir, v3(*n)), 0.0))
    ck.ok("ℓ は α の法線と平行→α 上の O を通る別の直線 k とも垂直（内積 0）",
          math.sqrt(dot3(cross3(l_dir, norm3(nrm)), cross3(l_dir, norm3(nrm)))) < 1e-9 and near(dot3(l_dir, v3(*k)), 0.0))

    cv = Canvas(W, H)
    labels = []
    _plane_quad(cv, fr, ob, corners, fill=SHADE)
    seg(cv, fr, ob.P(m[0]), ob.P(m[1]))
    seg(cv, fr, ob.P(n[0]), ob.P(n[1]))
    seg(cv, fr, ob.P(k[0]), ob.P(k[1]), w=AUX_W, dash=DASH)
    seg(cv, fr, ob.P(O), ob.P(ell[1]))
    seg(cv, fr, ob.P(ell[0]), ob.P(O), w=AUX_W, dash=DASH)
    right_angle(cv, fr, ob.P(O), ob.P(ell[1]), ob.P(m[1]))
    right_angle(cv, fr, ob.P(O), ob.P(ell[1]), ob.P(n[1]))
    dot_m(cv, fr, ob.P(O))
    _label3(cv, fr, ob, O, 300, 16, "O", fs, labels)
    _label3(cv, fr, ob, ell[1], 90, 14, "ℓ", fs, labels, weight=None)
    _label3(cv, fr, ob, m[1], 0, 14, "m", fs, labels, weight=None)
    _label3(cv, fr, ob, n[1], 60, 14, "n", fs, labels, weight=None)
    _label3(cv, fr, ob, corners[3], 300, 22, "α", fs, labels, weight=None)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L11_fig2_line_perp_plane.svg", "lesson": "L11", "canvas": cv,
            "title": "直線と平面の垂直の判定法——ℓ が α 上の交わる2直線 m・n に垂直なら、α 上の O を通るどの直線とも垂直（ℓ⊥α）",
            "desc": "平面 α を網かけの平行四辺形（斜投影）で描き、その上の点 O で交わる2直線 m（左右）・n（奥行き）と、O を通る鉛直な直線 ℓ を描く（α より下は破線）。O に ℓ と m・ℓ と n の直角マーク。α 上の O を通る別の直線を破線で添える。数値は書かない。同型図は平面の大きさと直線の向きを差し替えて生成する",
            "alt": "直線と平面の垂直の判定法——直線 ℓ が平面 α と点 O で交わり、α 上の O を通る交わる2直線 m・n に垂直なら、ℓ は α 上の O を通るどの直線とも垂直になる（ℓ⊥α）",
            "intent": "「交わる2本に垂直なら平面に垂直」の判定条件を、平面上の別の直線とも垂直になる結論とともに図で示す",
            "src": "lesson_11.md §3（判定条件の太字文と「交わる」の条件の説明の直後）",
            "params": "α: (±2.6, ±1.6, 0)／m: x 軸方向・n: y 軸方向・ℓ: z 軸方向／斜投影 k=0.5・α=30°／60 px/単位／ラベルは O・ℓ・m・n・α のみ",
            "checks": ck.items,
            "check_tokens": ["90"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L11_3():
    # --- パラメータ（lesson_11.md §4 2平面のなす角・垂直の2パネル） ---
    W, H = 640, 330
    fs = 17                                       # 2パネルのため幅の 3% より小さい（逸脱として記録）
    frames = [Frame(150, 240, 42), Frame(470, 240, 42)]
    thetas = [60.0, 90.0]
    ob = Oblique(0.6, 38.0)
    L = 2.0                                        # 交線 ℓ の半長
    ext = 2.0                                      # 平面の奥行き

    ck = Checker()
    cv = Canvas(W, H)
    labels = []
    for th, fr, name in zip(thetas, frames, ("なす角", "α⊥β")):
        O = (0.0, 0.0, 0.0)
        ell = ((-L, 0.0, 0.0), (L, 0.0, 0.0))
        u_b = (0.0, math.cos(th * DEG), math.sin(th * DEG))      # β 上で ℓ に垂直な向き
        alpha = [(-L, -ext, 0.0), (L, -ext, 0.0), (L, ext, 0.0), (-L, ext, 0.0)]
        beta = [(-L, 0.0, 0.0), (L, 0.0, 0.0), add3((L, 0.0, 0.0), u_b, ext), add3((-L, 0.0, 0.0), u_b, ext)]
        m_end = (0.0, 1.6, 0.0)
        n_end = add3(O, u_b, 1.6)
        ck.ok(f"θ={th:.0f}°: m⊥ℓ・n⊥ℓ（内積 0）", near(dot3(v3(O, m_end), v3(*ell)), 0.0) and near(dot3(v3(O, n_end), v3(*ell)), 0.0))
        ang = math.degrees(math.acos(dot3(norm3(v3(O, m_end)), norm3(v3(O, n_end)))))
        n_a, n_b = (0.0, 0.0, 1.0), norm3(cross3(v3(*ell), u_b))
        ang_n = math.degrees(math.acos(abs(dot3(n_a, n_b))))
        ck.ok(f"θ={th:.0f}°: m と n のなす角＝法線のなす角＝θ（1e-9）", near(ang, th) and near(ang_n, th), f"{ang:.4f} {ang_n:.4f}")
        _plane_quad(cv, fr, ob, alpha, fill=SHADE)
        _plane_quad(cv, fr, ob, beta)
        seg(cv, fr, ob.P(ell[0]), ob.P(ell[1]), w=BOLD_W)
        seg(cv, fr, ob.P(O), ob.P(m_end))
        seg(cv, fr, ob.P(O), ob.P(n_end))
        if near(th, 90.0):
            right_angle(cv, fr, ob.P(O), ob.P(m_end), ob.P(n_end))
        else:
            angle_arc(cv, fr, ob.P(O), ob.P(m_end), ob.P(n_end), r=18, n=1)
        dot_m(cv, fr, ob.P(O))
        _label3(cv, fr, ob, O, 300, 16, "O", fs, labels)
        _label3(cv, fr, ob, ell[1], 0, 14, "ℓ", fs, labels, weight=None)
        _label3(cv, fr, ob, m_end, 0, 14, "m", fs, labels, weight=None)
        _label3(cv, fr, ob, n_end, 90 if near(th, 90.0) else 150, 14, "n", fs, labels, weight=None)
        _label3(cv, fr, ob, alpha[0], 250, 18, "α", fs, labels, weight=None)
        _label3(cv, fr, ob, beta[3], 100, 18, "β", fs, labels, weight=None)
        caption(cv, fr.P(ob.P(O))[0], 312, name, fs, labels)
    ck.ok("右パネルは θ=90°（α⊥β）", near(thetas[1], 90.0))
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L11_fig3_dihedral_angle.svg", "lesson": "L11", "canvas": cv,
            "title": "2平面のなす角——交線 ℓ 上の点 O から α 上に ℓ⊥m、β 上に ℓ⊥n を引いたときの m と n のなす角（左: 一般・右: 90° で α⊥β）",
            "desc": "水平な平面 α（網かけ）と、交線 ℓ（太線）を共有して傾いた平面 β を斜投影で描く。O から α 上に ℓ に垂直な m、β 上に ℓ に垂直な n を引き、左パネルは m・n の間に弧（傾き 60°）、右パネルは直角マーク（傾き 90°・α⊥β）。角度の数値は書かない。同型図は β の傾きを差し替えて生成する",
            "alt": "2平面のなす角——交線 ℓ 上の点 O から、α 上に ℓ⊥m、β 上に ℓ⊥n となる直線を引いたときの m と n のなす角。なす角が 90° のとき α⊥β。左パネルが一般の場合、右パネルがなす角 90° で α⊥β の場合",
            "intent": "2平面のなす角の決め方（交線に垂直な2直線のなす角）と、垂直の定義を2パネルで見せる",
            "src": "lesson_11.md §4（なす角の定義文の直後・「2平面が垂直であることは」の前）",
            "params": "ℓ: x 軸方向（半長 2）・α: z=0・β: ℓ を含み y 軸から 60°／90° 傾く／m・n の長さ 1.6／斜投影 k=0.6・α=38°／42 px/単位・2パネル／ラベルは O・ℓ・m・n・α・β と パネル名",
            "checks": ck.items,
            "check_tokens": ["90°", "60"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 17 px（幅 640 の 2.7%）。2パネル並置のため"],
            "allow_texts": labels}


def _regular_tetra(a, rot=-25.0):
    """1辺 a の正四面体 A（上）・B・C・D（底面 z=0）。見取図で BD だけが隠れるように z 軸まわりに回す"""
    B, C, D = (0.0, 0.0, 0.0), (a, 0.0, 0.0), (a / 2, a * SQ3 / 2, 0.0)
    Hh = (a / 2, a * SQ3 / 6, 0.0)
    A = (Hh[0], Hh[1], a * math.sqrt(2.0 / 3.0))
    c = (a / 2, a * SQ3 / 6, 0.0)
    out = {}
    for k, p in (("A", A), ("B", B), ("C", C), ("D", D), ("H", Hh)):
        q = rot_z(v3(c, p), rot)
        out[k] = (q[0] + c[0], q[1] + c[1], q[2] + c[2])
    return out


def fig_L12_1():
    # --- パラメータ（lesson_12.md §2 正四面体の垂線の足） ---
    a = 4.0
    W, H = 640, 400
    fs = fs_for(W)
    fr = Frame(140, 330, 56)
    ob = Oblique(0.5, 30.0)
    V = _regular_tetra(a)
    A, B, C, D, Hh = (V[k] for k in "ABCDH")

    ck = Checker()
    ck.ok("6辺がすべて等しい（正四面体・1e-9）", all(near(dist3(p, q), a) for p, q in ((A, B), (A, C), (A, D), (B, C), (C, D), (D, B))))
    ck.ok("AH⊥平面 BCD（AH·BC=0・AH·BD=0）", near(dot3(v3(Hh, A), v3(B, C)), 0.0) and near(dot3(v3(Hh, A), v3(B, D)), 0.0))
    ck.ok("H＝底面 BCD の3頂点の座標の平均（重心・1e-9）", dist3(Hh, mean3([B, C, D])) < 1e-9)
    ck.ok("HB=HC=HD（外心・1e-9）", near(dist3(Hh, B), dist3(Hh, C)) and near(dist3(Hh, C), dist3(Hh, D)))
    ck.ok("△ABH≡△ACH≡△ADH（AB=AC=AD・AH 共通・∠AHB=∠AHC=∠AHD=90°）",
          all(near(dot3(v3(Hh, A), v3(Hh, X)), 0.0) for X in (B, C, D)))
    verts = [A, B, C, D]
    faces = hull_faces(verts)
    vis = [ob.visible(n) for _, n in faces]
    ck.ok("見取図: 可視面は2つ（隠れる辺は BD だけ）", sum(vis) == 2)

    cv = Canvas(W, H)
    labels = []
    edges, vis = draw_solid(cv, fr, ob, verts, faces)
    hidden = [(a_, b_) for (a_, b_), fis in edges if not any(vis[f] for f in fis)]
    ck.ok("隠れ線＝辺 BD（頂点番号 1-3）", hidden == [(1, 3)], f"{hidden}")
    seg(cv, fr, ob.P(A), ob.P(Hh), w=AUX_W, dash=DASH)
    for X in (B, C, D):
        seg(cv, fr, ob.P(Hh), ob.P(X), w=AUX_W, dash=DASH)
    right_angle(cv, fr, ob.P(Hh), ob.P(A), ob.P(C), size=9)
    for X in (A, B, C, D, Hh):
        dot_m(cv, fr, ob.P(X))
    for k, deg in (("A", 90), ("B", 200), ("C", 320), ("D", 20), ("H", 270)):
        _label3(cv, fr, ob, V[k], deg, 16, k, fs, labels)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L12_fig1_tetra_foot.svg", "lesson": "L12", "canvas": cv,
            "title": "正四面体 ABCD の頂点 A から底面 BCD に下ろした垂線 AH——足 H は底面の外心＝重心",
            "desc": "1辺 4 の正四面体（底面 BCD を水平・A を上）を斜投影で描き、隠れる辺 BD を破線にする。A から底面へ下ろした垂線 AH と、H から B・C・D へ結ぶ線分を破線で描き、H に直角マーク。数値は書かない。同型図は辺の長さと回転角を差し替えて生成する",
            "alt": "正四面体 ABCD の頂点 A から底面 BCD に下ろした垂線 AH——3つの直角三角形 ABH・ACH・ADH が合同になり、HB=HC=HD。足 H は正三角形 BCD の外心であり、重心と一致する",
            "intent": "直線と平面の垂直の定義→3つの直角三角形の合同→外心→（正三角形なので）重心、の4歩を追う図",
            "src": "lesson_12.md §2（正四面体の定義と「H は底面 BCD のどこにあるだろうか」の直後）",
            "params": "1辺 4・底面 z=0・z 軸まわりに −25° 回転／斜投影 k=0.5・α=30°／56 px/単位／ラベルは A・B・C・D・H のみ",
            "checks": ck.items,
            "check_tokens": ["90", "√6"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def fig_L12_2():
    # --- パラメータ（lesson_12.md §3 直方体の切断→四面体 ABDE・例題3の与件 AB=AD=2・AE=1） ---
    w, dep, h = 2.0, 2.0, 1.0
    W, H = 640, 380
    fs = fs_for(W)
    fr = Frame(170, 310, 90)
    ob = Oblique(0.5, 30.0)
    V = _cuboid(w, dep, h)
    A, B, D, E = V["A"], V["B"], V["D"], V["E"]
    M = mean3([B, D])

    ck = Checker()
    ck.ok("AB=AD=2・AE=1（座標から）", near(dist3(A, B), 2.0) and near(dist3(A, D), 2.0) and near(dist3(A, E), 1.0))
    ck.ok("∠BAD=∠BAE=∠DAE=90°（内積 0）", all(near(dot3(v3(A, p), v3(A, q)), 0.0) for p, q in ((B, D), (B, E), (D, E))))
    ck.ok("切り口 △BDE の3辺: BD=2√2・BE=DE=√5（三平方・1e-9・値は図に書かない）",
          near(dist3(B, D), 2 * SQ2) and near(dist3(B, E), SQ5) and near(dist3(D, E), SQ5))
    ck.ok("AM⊥BD・EM⊥BD（M は BD の中点・内積 0）", near(dot3(v3(M, A), v3(B, D)), 0.0) and near(dot3(v3(M, E), v3(B, D)), 0.0))
    ck.ok("BD⊥平面 AEM（BD·AE=0・BD·AM=0）", near(dot3(v3(B, D), v3(A, E)), 0.0) and near(dot3(v3(B, D), v3(A, M)), 0.0))
    verts = [V[k] for k in "ABCDEFGH"]
    faces = hull_faces(verts)

    cv = Canvas(W, H)
    labels = []
    edges, vis = draw_solid(cv, fr, ob, verts, faces)
    names = "ABCDEFGH"

    def on_visible_face(p, q):
        for (order, _), v in zip(faces, vis):
            if names.index(p) in order and names.index(q) in order:
                return v
        return False

    for p, q in (("B", "D"), ("B", "E"), ("D", "E")):
        if on_visible_face(p, q):
            seg(cv, fr, ob.P(V[p]), ob.P(V[q]), w=BOLD_W)
        else:
            seg(cv, fr, ob.P(V[p]), ob.P(V[q]), w=BOLD_W, dash=DASH)
    ck.ok("BD・BE は可視面上（実線）・DE は隠れた面上（破線）",
          on_visible_face("B", "D") and on_visible_face("B", "E") and not on_visible_face("D", "E"))
    seg(cv, fr, ob.P(A), ob.P(M), w=AUX_W)
    seg(cv, fr, ob.P(E), ob.P(M), w=AUX_W, dash=DASH)
    right_angle(cv, fr, ob.P(M), ob.P(A), ob.P(B), size=8)
    right_angle(cv, fr, ob.P(M), ob.P(E), ob.P(D), size=8)
    for k in names:
        dot_m(cv, fr, ob.P(V[k]))
    dot_m(cv, fr, ob.P(M))
    degs = {"A": 180, "B": 300, "C": 20, "D": 120, "E": 200, "F": 320, "G": 20, "H": 160}
    for k in names:
        _label3(cv, fr, ob, V[k], degs[k], 16, k, fs, labels)
    _label3(cv, fr, ob, M, 60, 16, "M", fs, labels)
    T = T_factory(cv, labels, fs)
    xef, yef = fr.P(ob.P((1.0, 0.0, 0.0)))
    T(xef, yef + 24, "2")                                  # AB の長さは下の辺 EF（=AB）の外側に置く（手前の面の内側は BE・EM・DE が通り、切り口の辺の長さと読めるため）
    xad, yad = fr.P(ob.P((0.0, 1.0, h)))
    T(xad - 14, yad - 6, "2", anchor="end")                # AD（左上の辺の外側）
    xae, yae = fr.P(ob.P((0.0, 0.0, 0.5)))
    T(xae - 12, yae + fs * 0.35, "1", anchor="end")        # AE（左の辺の外側）
    ck.ok("図中の数字は与件 2・2・1 のみ（切り口の辺長は書かない）", digit_runs(labels) == {"2", "1"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L12_fig2_cuboid_cut_tetra.svg", "lesson": "L12", "canvas": cv,
            "title": "直方体 ABCD-EFGH（AB=AD=2・AE=1）を3頂点 B・D・E を通る平面で切った四面体 ABDE——切り口 △BDE と、BD の中点 M・AM⊥BD・EM⊥BD",
            "desc": "AB=AD=2・AE=1 の直方体を斜投影で描き（隠れた辺は破線）、切り口 △BDE の3辺を太線で描く（BD・BE は可視面上で実線、DE は隠れた面上で破線）。BD の中点 M と A・E を結び（EM は破線）、M に直角マーク。与件の 2・2・1 だけを書く（AB の 2 は等しい下の辺 EF の外側に置く。辺長の答えは書かない）。同型図は寸法を差し替えて生成する",
            "alt": "直方体 ABCD-EFGH（AB=AD=2・AE=1）を3頂点 B・D・E を通る平面で切ってできる四面体 ABDE——切り口 △BDE の3辺は面の対角線で、BD=2√2・BE=DE=√5。BD の中点 M について AM⊥BD・EM⊥BD となり、BD⊥平面 AEM",
            "intent": "「見るべき平面を切り出す」型の題材——切り口の三角形と、BD⊥平面 AEM の根拠となる2本の垂線を見せる",
            "src": "lesson_12.md §3（四面体 ABDE の説明の直後・例題3の前）",
            "params": "AB=AD=2・AE=1（例題3の与件）／M=BD の中点／斜投影 k=0.5・α=30°／90 px/単位／ラベルは A〜H・M・2・2・1",
            "checks": ck.items,
            "check_tokens": ["2√2", "√5", "√6", "√30", "4/3", "2/3"],
            "digit_rule": ("subset", {"1", "2"}),
            "allow_texts": labels}


def fig_L12_3():
    # --- パラメータ（lesson_12.md §4 正四面体の各辺の中点を通る平面で切る→八面体） ---
    a = 4.0
    W, H = 640, 400
    fs = fs_for(W)
    fr = Frame(140, 330, 56)
    ob = Oblique(0.5, 30.0)
    V = _regular_tetra(a)
    A, B, C, D = (V[k] for k in "ABCD")
    tet = [A, B, C, D]
    mids = [mean3([tet[i], tet[j]]) for i, j in itertools.combinations(range(4), 2)]

    ck = Checker()
    faces = hull_faces(mids)
    edges = solid_edges(faces)
    ck.ok("中点6個を頂点とする凸多面体: 面 8・辺 12・頂点 6", len(faces) == 8 and len(edges) == 12 and len(mids) == 6)
    ck.ok("v−e＋f=2", len(mids) - len(edges) + len(faces) == 2)
    ck.ok("8面すべてが1辺 a/2 の正三角形（1e-9）",
          all(len(o) == 3 and all(near(dist3(mids[o[i]], mids[o[(i + 1) % 3]]), a / 2) for i in range(3)) for o, _ in faces))
    ck.ok("切り落とす小四面体の辺（中点どうしの距離）は a/2（中点連結定理・1e-9）",
          all(near(dist3(mean3([X, Y]), mean3([X, Z])), a / 2) for X, Y, Z in ((A, B, C), (B, C, D), (C, D, A), (D, A, B))))

    cv = Canvas(W, H)
    labels = []
    tfaces = hull_faces(tet)
    for (p, q), _ in solid_edges(tfaces):
        seg(cv, fr, ob.P(tet[p]), ob.P(tet[q]), w=0.9, dash="2 3")   # もとの正四面体は点線
    draw_solid(cv, fr, ob, mids, faces, w=MAIN_W)
    for X in mids:
        dot_m(cv, fr, ob.P(X))
    for k, deg in (("A", 90), ("B", 200), ("C", 320), ("D", 20)):
        _label3(cv, fr, ob, V[k], deg, 16, k, fs, labels)
    ck.ok("図中ラベルに数字を含まない（面・辺・頂点の個数は書かない）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L12_fig3_tetra_midpoint_cut.svg", "lesson": "L12", "canvas": cv,
            "title": "正四面体 ABCD の各辺の中点を通る4枚の平面で4つの角を切り落としてできる立体（正三角形 8 枚・辺 12・頂点 6）",
            "desc": "1辺 4 の正四面体（細い点線）の6本の辺の中点を頂点とする立体を実線で描く（可視面に接する辺は実線・それ以外は破線）。面は頂点座標からの支持平面探索で求め、8枚とも1辺 2 の正三角形であることを検算する。個数の数値は書かない。同型図は辺の長さと回転角を差し替えて生成する",
            "alt": "正四面体の各辺の中点を通る4枚の平面で4つの角を切り落としてできる立体——面は正三角形8枚、辺は12本、頂点はもとの辺の中点6個。8枚の面は、もとの面の中央に残る三角形4枚と切り口の三角形4枚",
            "intent": "L13 の数え上げ（面 8・辺 12・頂点 6）の題材を、もとの正四面体との位置関係が見える形で示す",
            "src": "lesson_12.md §4（切り落としの説明の直後・「この立体の面・辺・頂点の数を数えると」の前）",
            "params": "1辺 4 の正四面体（L12_fig1 と同じ座標）の6中点／斜投影 k=0.5・α=30°／56 px/単位／ラベルは A・B・C・D のみ",
            "checks": ck.items,
            "check_tokens": ["8", "12", "6", "1/2", "1/8"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# ===========================================================================
# L13 正多面体・角を切った立方体／L14 単元マップ・三角錐
# ===========================================================================
def _platonic():
    """正多面体5種の頂点座標（見取図用に z 軸まわりに少し回す）。(名前, 頂点, 面の形の辺数, 1頂点に集まる面数)"""
    t = _regular_tetra(2.0)
    tetra = [t[k] for k in "ABCD"]
    cube = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    octa = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    ico = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            ico += [(0, s1, s2 * PHI), (s1, s2 * PHI, 0), (s2 * PHI, 0, s1)]
    dode = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            dode += [(0, s1 / PHI, s2 * PHI), (s1 / PHI, s2 * PHI, 0), (s2 * PHI, 0, s1 / PHI)]
    return [("正四面体", tetra, 3, 3, 0.0), ("正六面体", cube, 4, 3, -20.0), ("正八面体", octa, 3, 4, -20.0),
            ("正十二面体", dode, 5, 3, 12.0), ("正二十面体", ico, 3, 5, 12.0)]


def fig_L13_1():
    # --- パラメータ（lesson_13.md §2 正多面体5種） ---
    W, H = 960, 280
    fs = 16                                       # 5パネルのため幅の 3% より小さい（逸脱として記録）
    ob = Oblique(0.5, 30.0)
    expected = {"正四面体": (4, 6, 4), "正六面体": (8, 12, 6), "正八面体": (6, 12, 8), "正十二面体": (20, 30, 12), "正二十面体": (12, 30, 20)}
    panel_w = 192

    ck = Checker()
    cv = Canvas(W, H)
    labels = []
    for i, (name, verts0, ngon, deg, rot) in enumerate(_platonic()):
        cen = mean3(verts0)
        verts = [add3(rot_z(v3(cen, p), rot), cen) for p in verts0]
        faces = hull_faces(verts)
        edges = solid_edges(faces)
        v, e, f = len(verts), len(edges), len(faces)
        ck.ok(f"{name}: 頂点 {v}・辺 {e}・面 {f}（座標からの面探索）", (v, e, f) == expected[name])
        ck.ok(f"{name}: v−e＋f=2", v - e + f == 2)
        edge_len = dist3(verts[edges[0][0][0]], verts[edges[0][0][1]])
        ck.ok(f"{name}: 全ての面が正{ngon}角形（辺数・辺長 1e-9）",
              all(len(o) == ngon and all(near(dist3(verts[o[j]], verts[o[(j + 1) % ngon]]), edge_len) for j in range(ngon)) for o, _ in faces))
        degs = [sum(1 for o, _ in faces if m in o) for m in range(v)]
        ck.ok(f"{name}: どの頂点にも {deg} 面が集まる", all(d == deg for d in degs))
        # パネル内に収める倍率（投影後の広がりから）
        pr = [ob.P(p) for p in verts]
        xs, ys = [q[0] for q in pr], [q[1] for q in pr]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        scale = 120.0 / span
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        fr = Frame(96 + panel_w * i - scale * cx, 130 + scale * cy, scale)
        draw_solid(cv, fr, ob, verts, faces)
        caption(cv, 96 + panel_w * i, 255, name, fs, labels)
    ck.ok("図中ラベルに算用数字を含まない（名前は漢数字）", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L13_fig1_platonic_solids.svg", "lesson": "L13", "canvas": cv,
            "title": "正多面体5種の見取図——正四面体・正六面体・正八面体・正十二面体・正二十面体（斜投影・隠れた辺は破線）",
            "desc": "5つの正多面体を頂点座標（正四面体は L12 と同じ・立方体は (±1,±1,±1)・正八面体は軸上の6点・正十二面体と正二十面体は黄金比の座標）から描く。面は頂点座標からの支持平面探索で求め、頂点・辺・面の数と v−e＋f=2、面の形、1頂点に集まる面の数を検算する。個数の数値は書かない。同型図は回転角と倍率を差し替えて生成する",
            "alt": "正多面体5種の見取図——正四面体（正三角形4面・1頂点に3面）・正六面体（正方形6面・3面）・正八面体（正三角形8面・4面）・正十二面体（正五角形12面・3面）・正二十面体（正三角形20面・5面）",
            "intent": "5種の正多面体を同じ描法で並べ、面の形と1頂点に集まる面の数で区別する表の隣に置く",
            "src": "lesson_13.md §2（正多面体の定義の直後・5種の表の前）",
            "params": "頂点座標表（本文どおり5種）／z 軸まわりの回転 0°・−20°・−20°・12°・12°／斜投影 k=0.5・α=30°／各パネル 192 px・投影幅 120 px に正規化／ラベルは5種の名前のみ",
            "checks": ck.items,
            "check_tokens": ["12", "20", "30"],
            "digit_rule": ("none", set()),
            "deviations": ["文字サイズ 16 px（幅 960 の 1.7%）。5パネル並置のため"],
            "allow_texts": labels}


def fig_L13_2():
    # --- パラメータ（lesson_13.md §4 角を1つ切った立方体） ---
    t = 0.45                                       # 切り落とす頂点から3辺に沿って測った切り位置
    W, H = 640, 400
    fs = fs_for(W)
    fr = Frame(200, 330, 150)
    ob = Oblique(0.5, 30.0)
    cube = [(x, y, z) for x in (0.0, 1.0) for y in (0.0, 1.0) for z in (0.0, 1.0)]
    corner = (1.0, 0.0, 1.0)                       # 手前・右・上の頂点（見取図で見える角）
    verts = [p for p in cube if p != corner] + [(1.0 - t, 0.0, 1.0), (1.0, t, 1.0), (1.0, 0.0, 1.0 - t)]

    faces = hull_faces(verts)
    edges = solid_edges(faces)
    v, e, f = len(verts), len(edges), len(faces)
    ck = Checker()
    ck.ok("頂点 v=8−1＋3=10（値は図に書かない）", v == 10)
    ck.ok("辺 e=12＋3=15", e == 15)
    ck.ok("面 f=6＋1=7", f == 7)
    ck.ok("v−e＋f=2", v - e + f == 2)
    sizes = sorted(len(o) for o, _ in faces)
    ck.ok("面の内訳: 三角形 1・四角形 3・五角形 3", sizes == [3, 4, 4, 4, 5, 5, 5])
    cut = [i for i, (o, _) in enumerate(faces) if len(o) == 3][0]
    ck.ok("切り口の三角形は見取図で可視", ob.visible(faces[cut][1]))

    cv = Canvas(W, H)
    labels = []
    draw_solid(cv, fr, ob, verts, faces, fill_faces={cut})
    for X in verts:
        dot_m(cv, fr, ob.P(X))
    fc = mean3([verts[m] for m in faces[cut][0]])
    labels.append("切り口")
    label_dir(cv, fr, ob.P(fc), 20, 60, "切り口", fs)
    ck.ok("図中ラベルに数字を含まない", no_digits(labels))
    cv.layout_checks(ck)

    return {"file": "L13_fig2_truncated_cube_count.svg", "lesson": "L13", "canvas": cv,
            "title": "立方体の1つの角を、その頂点から出る3辺の途中を通る平面で切り落とした立体（切り口は網かけの三角形）",
            "desc": "1辺 1 の立方体の手前・右・上の頂点を、3辺上の t=0.45 の点を通る平面で切り落とす。残る7頂点と新しい3頂点から面を支持平面探索で求め（三角形 1・四角形 3・五角形 3）、可視面に接する辺を実線・それ以外を破線で描く。切り口を網かけし「切り口」とだけ書く（v・e・f の値は書かない）。同型図は t と切る頂点を差し替えて生成する",
            "alt": "立方体の1つの角を、その頂点から出る3辺の途中を通る平面で切り落とした立体——頂点は 8−1＋3=10、辺は 12＋3=15、面は 6＋1=7 で、v−e＋f=10−15＋7=2",
            "intent": "「頂点が1つ消えて3つ増える・辺が3本増える・面が1つ増える」数え上げの対象を、隠れ線つきの見取図で示す",
            "src": "lesson_13.md §4（「立方体の1つの頂点を…切り落としてみる」の直後・例題2の前）",
            "params": "1辺 1 の立方体・切る頂点 (1,0,1)・切り位置 t=0.45／斜投影 k=0.5・α=30°／150 px/単位／ラベルは 切り口 のみ",
            "checks": ck.items,
            "check_tokens": ["10", "15", "7", "2"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


def _disjoint(a, b):
    return a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1]


def fig_L14_1():
    # --- パラメータ（lesson_14.md §1 定理カード地図） ---
    W, H = 900, 470
    fs_h, fs_c, fs_s = 16, 13, 12                  # 見出し・カード名・中学の結果（幅の 3% より小さい・逸脱として記録）
    groups = [
        ("三角形 L01〜L05", 40, [("角の二等分線と辺の比 (L01)", "平行線と比・二等辺三角形"),
                               ("外心・内心・重心 (L02・L03)", "垂直二等分線・中点連結定理"),
                               ("チェバ・メネラウス (L04)", "面積比・平行線と比・相似"),
                               ("成立条件・辺と角の大小 (L05)", "三角形の内角・外角")]),
        ("円 L06〜L09", 170, [("円に内接する四角形 (L06)", "円周角の定理とその逆"),
                             ("接線の長さ・接弦 (L07)", "接線⊥半径・直角三角形の合同"),
                             ("方べきの定理 (L08)", "円周角の定理・相似"),
                             ("2円の位置関係・共通接線 (L09)", "三平方の定理")]),
        ("空間 L11〜L13", 300, [("直線と平面の垂直 (L11・L12)", "空間の位置関係・合同"),
                               ("正多面体・v−e＋f=2 (L13)", "正多角形の内角・面・辺・頂点")]),
    ]
    card_w, card_h, gap, x0 = 200, 72, 12, 40
    construct = (x0 + 2 * (card_w + gap), 300, 2 * card_w + gap, 72, "作図 L10", "カード1・7を「かく」→ 全て条件に適するか・他に無いか")
    legend = "各カード: 名前・図・一言の理由・使う中学の結果 の4項目（表は本文）"

    ck = Checker()
    cards = []
    for gname, gy, items in groups:
        for j, (name, base) in enumerate(items):
            cards.append((x0 + j * (card_w + gap), gy + 24, card_w, card_h, name, base))
    ck.ok("カードは 10 枚（本文の表と同数）", len(cards) == 10)
    lessons = set()
    for c in cards:
        lessons.update(re.findall(r"L\d\d", c[4]))
    lessons.update(re.findall(r"L\d\d", construct[4]))
    ck.ok("カードと作図の箱でレッスン L01〜L13 を漏れなく覆う", lessons == {f"L{i:02d}" for i in range(1, 14)}, f"{sorted(lessons)}")
    boxes = [c[:4] for c in cards] + [construct[:4]]
    ck.ok("箱 11 個が互いに重ならない", all(_disjoint(boxes[i], boxes[j]) for i in range(len(boxes)) for j in range(i + 1, len(boxes))))
    ck.ok("カード名・中学の結果の推定幅がカード幅−8 px 未満",
          all(est_w(c[4], fs_c) < card_w - 8 and est_w(c[5], fs_s) < card_w - 8 for c in cards),
          f"{[(c[4], round(est_w(c[4], fs_c))) for c in cards if est_w(c[4], fs_c) >= card_w - 8]}")

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs_c)
    for gname, gy, items in groups:
        T(x0, gy + 14, gname, fs_h, anchor="start", weight="bold")
    for (x, y, w, h, name, base) in cards:
        cv.rect(x, y, w, h, sw=MAIN_W)
        T(x + w / 2, y + 28, name, fs_c, weight="bold")
        T(x + w / 2, y + 54, base, fs_s)
    x, y, w, h, gname, note = construct
    cv.rect(x, y, w, h, dash=DASH, sw=1.4)
    T(x + w / 2, y + 28, gname, fs_c, weight="bold")
    T(x + w / 2, y + 54, note, fs_s)
    T(x0, 440, legend, fs_s, anchor="start")
    allowed = {f"{i:02d}" for i in range(1, 14)} | {"1", "2", "4", "7"}
    ck.ok("数字はレッスン番号（01〜13）と 2円・v−e＋f=2・カード1・7・4項目 のみ", digit_runs(labels) <= allowed, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L14_fig1_unit_map.svg", "lesson": "L14", "canvas": cv,
            "title": "単元の定理カード地図——三角形（L01〜L05）・円（L06〜L09）・作図（L10）・空間（L11〜L13）の10枚のカード",
            "desc": "3段のカード列（三角形 4 枚・円 4 枚・空間 2 枚）と破線の作図の箱を並べ、各カードに定理の名前（レッスン番号）と「使う中学の結果」を書く。4項目のうち図と一言の理由は本文の表に置き、図には名前と中学の結果だけを載せる。同型図はカードの文言を差し替えて生成する（レッスン番号の網羅と箱の非重複を検算）",
            "alt": "単元の定理カード地図——三角形の節（L01〜L05）・円の節（L06〜L09）・作図（L10）・空間（L11〜L13）の各定理を、名前と使う中学の結果の2項目で1枚に配置した図（図と一言の理由は本文の表に置く）",
            "intent": "14レッスンの定理を1枚の地図に再配置し、「使う中学の結果」の列から逆向きに読む練習の土台にする",
            "src": "lesson_14.md §1（カードの4項目の説明の直後・表の前）",
            "params": "カード 10 枚（200×72・間隔 12）・作図の箱 1（破線）／文字 16・13・12 px／レッスン番号 L01〜L13 を網羅",
            "checks": ck.items,
            "check_tokens": ["3√5", "2√5", "2√2", "2√6"],
            "digit_rule": ("subset", {"01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "1", "2", "4", "7"}),
            "deviations": ["文字サイズ 16・13・12 px（幅 900 の 1.8%・1.4%・1.3%）。10 枚のカードを1枚に収めるため", "4項目のうち「図」と「一言の理由」はカードに載せず本文の表に委ねた（1枚に収めるため）"],
            "allow_texts": labels}


def fig_L14_2():
    # --- パラメータ（lesson_14.md §2 例題1の三角錐 PABC と切り出した平面 ABC・与件 AB=6・AC=3・PA=4・∠BAC=90°） ---
    AB, AC, PA = 6.0, 3.0, 4.0
    W, H = 640, 390
    fs = 17                                       # 2パネルのため幅の 3% より小さい（逸脱として記録）
    ob = Oblique(0.7, 40.0)
    frL, frR = Frame(70, 300, 27), Frame(390, 290, 30)

    A3, B3, C3, P3 = (0.0, 0.0, 0.0), (AB, 0.0, 0.0), (0.0, AC, 0.0), (0.0, 0.0, PA)
    A, B, C = (0.0, 0.0), (AB, 0.0), (0.0, AC)
    D = divide(B, C, AB, AC, True)                 # BD:DC=AB:AC（角の二等分線と辺の比）
    Oc = mid(B, C)                                 # ∠A=90° なので外接円の中心は BC の中点
    R = dist(Oc, B)
    E = [X for X in circle_line(Oc, R, A, D) if dist(X, A) > 1e-9][0]
    ck = Checker()
    ck.ok("PA⊥AB・PA⊥AC（内積 0）→ PA⊥平面 ABC", near(dot3(v3(A3, P3), v3(A3, B3)), 0.0) and near(dot3(v3(A3, P3), v3(A3, C3)), 0.0))
    ck.ok("∠BAC=90°・AB=6・AC=3・PA=4", near(angle_at(A, B, C), 90.0) and near(dist(A, B), AB) and near(dist(A, C), AC) and near(dist3(A3, P3), PA))
    ck.ok("AD は ∠BAC の二等分線（∠BAD=∠DAC・1e-9）", near(angle_at(A, B, D), angle_at(A, D, C)))
    ck.ok("BD:DC=AB:AC=2:1（1e-9・値は図に書かない）", near(dist(B, D) / dist(D, C), 2.0))
    ck.ok("E は3点 A・B・C を通る円の周上・AD の延長上（t>1）", on_circle(E, Oc, R) and param_on(E, A, D) > 1)
    ck.ok("AD²=AB×AC−BD×DC（方べき・1e-9）", near(dist(A, D) ** 2, AB * AC - dist(B, D) * dist(D, C)))
    ck.ok("AB×AC=AD×AE・BD×DC=DA×DE（1e-9）", near(AB * AC, dist(A, D) * dist(A, E)) and near(dist(B, D) * dist(D, C), dist(D, A) * dist(D, E)))
    ck.ok("∠BEC=90°（BC が直径・1e-9）", near(angle_at(E, B, C), 90.0))

    cv = Canvas(W, H)
    labels = []
    T = T_factory(cv, labels, fs)
    # 左: 三角錐（底面の円は投影して破線）
    Dz, E3 = (D[0], D[1], 0.0), (E[0], E[1], 0.0)
    circ = [ob.P((Oc[0] + R * math.cos(k * 4 * DEG), Oc[1] + R * math.sin(k * 4 * DEG), 0.0)) for k in range(90)]
    cv.polyline([frL.P(q) for q in circ], w=AUX_W, dash=DASH, close=True)
    verts3 = [A3, B3, C3, P3]
    faces3 = hull_faces(verts3)
    edges3, vis3 = draw_solid(cv, frL, ob, verts3, faces3)
    hidden3 = [(a_, b_) for (a_, b_), fis in edges3 if not any(vis3[f] for f in fis)]
    ck.ok("見取図: 可視面は PAB だけ・隠れた辺 AC・BC・PC（頂点番号 0-2・1-2・2-3）は破線", sum(vis3) == 1 and hidden3 == [(0, 2), (1, 2), (2, 3)], f"{hidden3}")
    seg(cv, frL, ob.P(A3), ob.P(Dz), w=AUX_W)
    seg(cv, frL, ob.P(Dz), ob.P(E3), w=AUX_W, dash=DASH)
    seg(cv, frL, ob.P(P3), ob.P(Dz), w=AUX_W, dash=DASH)
    right_angle(cv, frL, ob.P(A3), ob.P(B3), ob.P(C3), size=9)
    right_angle(cv, frL, ob.P(A3), ob.P(P3), ob.P(B3), size=9)
    for X in (A3, B3, C3, P3, Dz, E3):
        dot_m(cv, frL, ob.P(X))
    for X, lab, deg in ((A3, "A", 225), (B3, "B", 300), (C3, "C", 60), (P3, "P", 90), (Dz, "D", 320), (E3, "E", 40)):
        _label3(cv, frL, ob, X, deg, 16, lab, fs, labels)
    xab, yab = frL.P(ob.P((AB / 2, 0.0, 0.0)))
    T(xab, yab + 22, "6")
    xac, yac = frL.P(ob.P((0.0, AC * 0.75, 0.0)))
    T(xac - 8, yac - 6, "3", anchor="end")
    xpa, ypa = frL.P(ob.P((0.0, 0.0, PA / 2)))
    T(xpa - 12, ypa + fs * 0.35, "4", anchor="end")
    # 右: 切り出した平面 ABC
    circle_path(cv, frR, Oc, R, w=AUX_W)
    poly(cv, frR, [A, B, C])
    seg(cv, frR, A, D)
    seg(cv, frR, D, E, w=AUX_W, dash=DASH)
    seg(cv, frR, B, E, w=AUX_W, dash=DASH)
    seg(cv, frR, C, E, w=AUX_W, dash=DASH)
    right_angle(cv, frR, A, B, C, size=9)
    angle_arc(cv, frR, A, B, D, r=24, n=1)
    angle_arc(cv, frR, A, D, C, r=24, n=1)
    for X in (A, B, C, D, E):
        dot_m(cv, frR, X)
    for X, lab, deg in ((A, "A", 225), (B, "B", 315), (C, "C", 135), (D, "D", 330), (E, "E", 45)):
        labels.append(lab)
        label_dir(cv, frR, X, deg, 16, lab, fs, weight="bold")
    side_label(cv, frR, A, B, C, "6", fs, off=16)
    side_label(cv, frR, A, C, B, "3", fs, off=16)
    labels += ["6", "3"]
    caption(cv, 190, 372, "三角錐 PABC", fs, labels)
    caption(cv, 480, 372, "切り出した平面 ABC", fs, labels)
    ck.ok("図中の数字は与件 6・3・4 のみ（BC・BD・AD・PD・体積は書かない）", digit_runs(labels) == {"6", "3", "4"}, show_set(digit_runs(labels)))
    cv.layout_checks(ck)

    return {"file": "L14_fig2_tetra_slice.svg", "lesson": "L14", "canvas": cv,
            "title": "三角錐 PABC（PA⊥平面 ABC・∠BAC=90°・AB=6・AC=3・PA=4）と、切り出した平面 ABC 上の図（外接円・二等分線 AD・その延長と円の交点 E）",
            "desc": "左: A を原点、AB を x 軸、AC を奥行き、PA を高さにとった三角錐を斜投影で描き（可視面 PAB に接する辺 AB・PA・PB は実線、隠れた辺 AC・BC・PC は破線）、底面の3点を通る円を破線、AD を細線、DE・PD を破線で添える（A に2つの直角マーク）。右: 平面 ABC を描き直した図——直角三角形 ABC とその外接円（中心は BC の中点）、∠A の二等分線 AD（2つの半角に弧）、延長と円の交点 E、BE・CE を破線。与件 6・3・4 だけを書く。同型図は AB・AC・PA を差し替えて生成する",
            "alt": "自作の三角錐 PABC（PA⊥平面 ABC・∠BAC=90°・AB=6・AC=3・PA=4）と、切り出した平面 ABC——3点 A・B・C を通る円、∠BAC の二等分線 AD、その延長と円の交点 E。左パネルが三角錐、右パネルが切り出した平面上の図",
            "intent": "「見るべき平面を切り出す→平面の定理→空間へ戻す」の総合演習で、切り出した平面を描き直す動作そのものを見せる",
            "src": "lesson_14.md §2（例題1の問題文 (1)〜(7) の直後・解答の前）",
            "params": "AB=6・AC=3・PA=4（例題1の与件）／D=BC を AB:AC に内分・E=AD の延長と外接円の交点（座標計算）／斜投影 k=0.7・α=40°（左）／27・30 px/単位・2パネル／ラベルは P・A・B・C・D・E・6・3・4 と パネル名",
            "checks": ck.items,
            "check_tokens": ["3√5", "2√5", "√5", "2√2", "2√6", "12", "90°", "9√2"],
            "digit_rule": ("subset", {"6", "3", "4"}),
            "deviations": ["文字サイズ 17 px（幅 640 の 2.7%）。2パネル並置のため"],
            "allow_texts": labels}


# ===========================================================================
# main: 陽性対照 → 生成 → 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L01_3, fig_L02_1, fig_L02_2, fig_L02_3, fig_L03_1, fig_L03_2, fig_L04_1,
        fig_L04_2, fig_L04_3, fig_L04_4, fig_L05_1, fig_L05_2, fig_L06_1, fig_L06_2, fig_L06_3, fig_L07_1,
        fig_L07_2, fig_L08_1, fig_L08_2, fig_L09_1, fig_L09_2, fig_L10_1, fig_L10_2, fig_L10_3, fig_L11_1,
        fig_L11_2, fig_L11_3, fig_L12_1, fig_L12_2, fig_L12_3, fig_L13_1, fig_L13_2, fig_L14_1, fig_L14_2]

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
    """答え漏れ検査器・文字衛生検査器・面探索器の陽性対照"""
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
    char_hygiene("√2・²・°・−・′・∠・△・＋・〜・→・ℓ・α・β・A₁・⊥・∥", "陰性対照")
    # 面探索器: 立方体から 6 面・12 辺・8 頂点が出ること（オイラーの式の検算器の対照）
    cube = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    faces = hull_faces(cube)
    edges = solid_edges(faces)
    assert len(faces) == 6 and len(edges) == 12 and all(len(o) == 4 for o, _ in faces), "面探索器の対照失敗（立方体）"
    assert len(cube) - len(edges) + len(faces) == 2
    # 可視判定の対照: 手前の面（法線 (0,−1,0)）は見え、奥の面（(0,1,0)）は見えない
    ob = Oblique()
    assert ob.visible((0, -1, 0)) and not ob.visible((0, 1, 0)), "可視判定の対照失敗"


def svg_tech_checks(src, meta):
    """生成した SVG 文字列を、ファイルへ書く前に検査する"""
    path = Path(meta["file"])
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert 'xmlns="http://www.w3.org/2000/svg"' in root_tag and "viewBox=" in root_tag, f"{path.name}: xmlns/viewBox がない"
    assert " width=" not in root_tag and " height=" not in root_tag, f"{path.name}: ルートに width/height を書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, f"{path.name}: 外部参照の疑い"
    assert "font-family" not in src, f"{path.name}: フォント指定は書かない（docs/SPEC_figures.md §5）"
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
    pending = []
    n_checks = 0
    total_bytes = 0
    for fn in FIGS:
        meta = fn()
        svg1 = meta["canvas"].svg(meta["file"], meta["title"], meta["desc"])
        meta2 = fn()
        svg2 = meta2["canvas"].svg(meta2["file"], meta2["title"], meta2["desc"])
        assert svg1 == svg2, f"{meta['file']}: 同一プロセス内の2回生成が一致しない"
        svg_tech_checks(svg1, meta)
        n_checks += len(meta["checks"])
        total_bytes += len(svg1.encode("utf-8"))
        rows.append(meta)
        pending.append((ASSETS / meta["file"], svg1))
        print(f"OK {meta['file']}  [{len(meta['checks'])} checks passed]")

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
        "# FIGURE_MANIFEST — 数学A 図形の性質 単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト。下表の数学検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。加えて全SVGに XML整形式・xmlns/viewBox・width/height なし・self-contained・"
        "`<title>`/`<desc>`・白背景・フォント指定なし の技術検査と、文字衛生検査"
        "（絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字の不在）と、答え漏れ検査を実施。"
        "答え漏れ検査は二重ゲート: (1)図中の全ラベルを許可リスト（本文が図の前後で明示している値のみ）と"
        f"集合として完全一致で照合、(2)禁止文字列（例題・練習の答え由来・計{n_tokens}項目・対象値は非開示）の"
        "不在検査と、図ごとの数字集合の制約。検査器自体は生成前の陽性対照（禁止値・禁止文字を仕込んだ合成入力での検出・"
        "立方体からの面探索と可視判定）で毎回実証している。PASS。／ AI再利用メタ情報として全SVGに `<title>`/`<desc>`"
        "（意図・主要数値・同型図を描かせる説明文）を標準装備。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | alt（本文と同一） | パラメータ（本文一致） | 検証結果（生成時 assert） |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} 合格" for d, t in m["checks"])
        lines.append(f"| `{m['file']}` | {m['lesson']} | {m['title']}——{m['intent']} | "
                     f"{m['src']} | {m['alt']} | {m['params']} | {checks} |")
    lines += ["", "## 受け入れ検査の結果", ""]
    for line in accept:
        lines.append(f"- {line}")
    lines += [
        f"- 各SVG: XML整形式・xmlns と viewBox あり・width/height なし・外部参照なし・`<title>`/`<desc>` あり・"
        f"白背景 rect あり・font-family なし（{len(rows)} 枚全件・スクリプトの技術検査で assert）",
        f"- 各図の assert が生成時に全件通過（計 {n_checks} 項目・上表）",
        "- 答え漏れ検査: `<text>` の文字列集合が各図の許可集合と完全一致・禁止文字列 0 件・数字集合の制約を満たす（全図 assert）",
        "- 決定性: 乱数不使用・集合は整列して出力・同一プロセス内で各図を2回生成してバイト一致を assert。"
        "別プロセスでの再実行は、生成日（日付のみ）を除いて全SVGと本台帳がバイト一致する",
        "- 図数の照合: 本文の図参照と生成ファイルの差集合が空（上の1行目）",
        "- 立体図: 面は頂点座標からの支持平面探索で機械的に求め、可視面に接する辺を実線・それ以外を破線で描く"
        "（隠れ線の判定を手で書かない）。v−e＋f=2 は求めた面・辺・頂点の個数で検算",
        "",
        "## 逸脱（docs/SPEC_figures.md からの差）",
        "",
    ]
    n_dev = 0
    for m in rows:
        for d in m.get("deviations", []):
            lines.append(f"- `{m['file']}`: {d}")
            n_dev += 1
    lines += [
        "- 共通: 色による対応づけは白黒規約により使わず、線幅・破線・弧の本数・ティック・矢羽で置き換えた。"
        "多パネル図（3状態・5分類・2パネル）は文字サイズを幅の 3% より小さくした（各図の逸脱行に記載）",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値は、いずれも本文（例題の与件・図の前後の明示値）のみ。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- 例題の答えにあたる長さ・角度・個数（L01 の分点の長さ、L12_fig2 の切り口の辺長、L13_fig2 の v・e・f、L14_fig2 の BC・AD・PD など）は図に書かず、禁止文字列として不在を検査した。この分離の対象は図中の文字（SVG の text）だけで、alt 文は本文の一部（本文と同一・例題の解答が続く位置）として対象外。数値でない答えの例外は L11_fig1 の凡例（辺 AB と交わる・平行・ねじれの位置にある辺の一覧＝例題1(1) の答え）で、分類の一覧を先に見せてから例題で言わせる設計として許可リストに載せている。",
        "- 練習問題の図は作らない（与件は本文で言葉により完全記述する方針）。",
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
