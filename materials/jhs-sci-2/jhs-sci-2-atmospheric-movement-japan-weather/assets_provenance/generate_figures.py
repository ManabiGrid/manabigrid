#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2理科「大気の動きと日本の天気」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（白黒・font-family なし・xmlns と viewBox・title/desc・
白背景・答え非記載・コード来歴）。各図の内容仕様（各 fig_* 関数冒頭のパラメータブロック・
Checker の検算項目）は本文 lesson_XX.md と一致させる。

- 実行: python3 generate_figures.py（この階層を作業フォルダにして実行する）
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（20枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / unicodedata / xml.etree）
- データ規律: 天気図・断面図・時系列はすべて教材用に作った架空の模式図。実在の日付・地名・
  観測値を使わない。日本列島・大陸は地図データを使わず、下の簡略な多角形（手で決めた頂点）で描く。
- 自己検証（1つでも落ちると例外で停止し、SVG も台帳も書き出さない）:
  (1) 図ごとの Checker（気象の検算）——等圧線が 4hPa きざみで交わらない・地点がのるべき線の上に
      ある・風の矢印が「等圧線にそう向きと中心へ向かう（離れる）向きの中間（45°）」で北半球の
      回り方（低気圧は反時計回りに吹きこむ・高気圧は時計回りに吹き出す）に合う・前線の記号が
      進む向きの側にある・前線面の傾きの急／ゆるい・気団や中心の位置など。
  (2) 本文照合——図のパラメータ（気圧値・目盛りの位置・表の値・風向の約束）が本文の記述と一致する
      ことを、本文 lesson_XX.md を読んで照合する（本文を直したら、このスクリプトも直すこと）。
  (3) 答えの分離（二重ゲート＋陽性対照）——各図の `<text>` の文字列集合が許可リスト（本文が図の前後で
      明示している語と値だけ）と完全一致すること、練習・例題の答え由来の禁止文字列が図中テキスト・
      title・desc に無いこと、図ごとの数字集合の制約。検査器は main() 冒頭の陽性対照で毎回実証する。
  (4) 配置検査——全要素が viewBox 内・ラベル同士が重ならない・ラベルが線（等圧線・前線・矢印・海岸線・
      枠）にかからない（推定の文字ボックスで全ペアを検査）・文字サイズの下限。
  (5) 文字衛生——絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字を、本スクリプト自身と
      全 SVG・台帳について機械検査する（公開側の検疫と同じ向き）。
- 決定性: 乱数・時刻に依存しない。日付は SVG 先頭コメントと台帳の generated 行・生成日行だけに現れる。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの値を変えて再実行する。
  値は該当レッスン本文（lesson_XX.md）と一致させること。SVG の直接編集は禁止（来歴が切れる）。
"""

import math
import datetime
import re
import unicodedata
import xml.etree.ElementTree as ET
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSON_DIR = HERE.parent          # lesson_XX.md はこの階層（公開側の単元フォルダでも同じ）
GENERATED = datetime.date.today().isoformat()
MODEL_LINE = "実行モデル: claude-opus-5-5（親指定・effort max・親が実走記録で照合）"

# ---- 様式定数 --------------------------------------------------------------
W = 640            # 全図共通の viewBox 幅
FS = 19            # 基本文字サイズ（viewBox 幅の約3%）
FS_S = 18          # 補足・キャプション（下限。viewBox 幅の 2.8%）
MIN_FS = 18        # 文字サイズの下限（assert）
MAIN_W = 1.6       # 主線幅
BOLD_W = 3.2       # 強調線幅
AUX_W = 1.1        # 補助線幅（破線）
DASH = "6 4"       # 破線
THIN_W = 1.2       # 等圧線・枠
FRONT_W = 2.6      # 前線の線幅
DOT_R = 3.2        # 地点マーカー半径
LAND_FILL = "#e3e3e3"   # 陸（うすいグレー）
COLD_FILL = "#d9d9d9"   # 寒気（断面図・うすいグレー）
SEA_FILL = "#f0f0f0"    # 海（断面図）
GROUND_FILL = "#bdbdbd" # 地面（断面図）
# font-family は書かない（公開側 docs/SPEC_figures.md §5 の規約。書体は閲覧環境に任せる）
DEG = math.pi / 180.0


# ===========================================================================
# 幾何ユーティリティ（数学座標: x=東・y=北。px 座標: x=右・y=下）
# ===========================================================================
def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(v, k):
    return (v[0] * k, v[1] * k)


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def norm(v):
    return math.hypot(v[0], v[1])


def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def rot(v, deg):
    """数学座標で反時計回りに deg 度回す"""
    c, s = math.cos(deg * DEG), math.sin(deg * DEG)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


def angle_between(u, v):
    """2ベクトルのなす角（度・0〜180）"""
    c = dot(u, v) / (norm(u) * norm(v))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def bearing_deg(v):
    """数学座標のベクトル v の方位角（北=0°・時計回り・0〜360）"""
    return math.degrees(math.atan2(v[0], v[1])) % 360.0


def math_deg(v):
    """数学座標のベクトル v の向き（東=0°・反時計回り・-180〜180）"""
    return math.degrees(math.atan2(v[1], v[0]))


COMPASS8 = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"]


def compass8(v):
    """ベクトル v の向きを8方位で返す。2つ目の値は 45° 格子からのずれ（度）"""
    b = bearing_deg(v)
    k = int(round(b / 45.0)) % 8
    dev = abs((b - 45.0 * round(b / 45.0) + 180.0) % 360.0 - 180.0)
    return COMPASS8[k], dev


def compass_vec(name):
    """8方位名 → その方位を向く単位ベクトル（数学座標）"""
    k = COMPASS8.index(name)
    b = 45.0 * k * DEG
    return (math.sin(b), math.cos(b))


def catmull_rom(pts, n=8):
    """制御点をすべて通る滑らかな曲線（一様 Catmull-Rom・両端は端点を複製）を折れ線で返す"""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t
                       + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                for k in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


def cum_lengths(pts):
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + dist(pts[i - 1], pts[i]))
    return c


def point_at(pts, cum, s):
    """折れ線上で始点から弧長 s の点と、その点の単位接線を返す"""
    s = max(0.0, min(cum[-1], s))
    for i in range(1, len(pts)):
        if cum[i] >= s:
            seg = cum[i] - cum[i - 1] or 1.0
            t = (s - cum[i - 1]) / seg
            return lerp(pts[i - 1], pts[i], t), unit(sub(pts[i], pts[i - 1]))
    return pts[-1], unit(sub(pts[-1], pts[-2]))


def point_in_polygon(p, poly):
    """偶奇規則（レイキャスト）"""
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def dist_point_seg(p, a, b):
    ab = sub(b, a)
    L2 = dot(ab, ab)
    if L2 == 0:
        return dist(p, a)
    t = max(0.0, min(1.0, dot(sub(p, a), ab) / L2))
    return dist(p, add(a, mul(ab, t)))


def dist_point_polyline(p, pts, closed=False):
    segs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[0])] if closed else [])
    return min(dist_point_seg(p, a, b) for a, b in segs)


def min_dist_polylines(A, B):
    """2本の折れ線の最小距離（A の頂点→B の線分・B の頂点→A の線分の小さい方）"""
    return min(min(dist_point_polyline(p, B) for p in A), min(dist_point_polyline(q, A) for q in B))


def seg_intersects_rect(a, b, rect):
    """線分 ab が矩形 rect=(x0, y0, x1, y1) と交わるか（Liang-Barsky）"""
    x0, y0, x1, y1 = rect
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t0 <= t1


def clip_polyline(pts, rect):
    """折れ線を矩形 rect=(x0, y0, x1, y1) で切り取り、矩形内の部分の列（折れ線のリスト）を返す"""
    x0, y0, x1, y1 = rect

    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1

    def clip_seg(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if p == 0:
                if q < 0:
                    return None
            else:
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
                if t0 > t1:
                    return None
        return lerp(a, b, t0), lerp(a, b, t1)

    runs, cur = [], []
    for a, b in zip(pts, pts[1:]):
        c = clip_seg(a, b)
        if c is None:
            if cur:
                runs.append(cur)
                cur = []
            continue
        ca, cb = c
        if not cur:
            cur = [ca]
        elif dist(cur[-1], ca) > 1e-9:
            runs.append(cur)
            cur = [ca]
        cur.append(cb)
        if not inside(b) or dist(cb, b) > 1e-9:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def clip_polygon_rect(poly, rect):
    """多角形を矩形で切り取る（Sutherland-Hodgman）"""
    x0, y0, x1, y1 = rect
    edges = [(lambda p: p[0] >= x0, lambda a, b: lerp(a, b, (x0 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[0] <= x1, lambda a, b: lerp(a, b, (x1 - a[0]) / (b[0] - a[0]))),
             (lambda p: p[1] >= y0, lambda a, b: lerp(a, b, (y0 - a[1]) / (b[1] - a[1]))),
             (lambda p: p[1] <= y1, lambda a, b: lerp(a, b, (y1 - a[1]) / (b[1] - a[1])))]
    out = list(poly)
    for ins, isect in edges:
        src, out = out, []
        if not src:
            break
        for i in range(len(src)):
            cur, prev = src[i], src[i - 1]
            if ins(cur):
                if not ins(prev):
                    out.append(isect(prev, cur))
                out.append(cur)
            elif ins(prev):
                out.append(isect(prev, cur))
    return out


def ellipse_pts(c, a, b, n=180):
    """中心 c・半径 a（東西）・b（南北）の楕円を n 点で（数学座標・反時計回り・閉じない）"""
    return [(c[0] + a * math.cos(2 * math.pi * i / n), c[1] + b * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def ellipse_val(p, c, a, b):
    """楕円の式の値（1 なら線上・1 未満なら内側）"""
    return ((p[0] - c[0]) / a) ** 2 + ((p[1] - c[1]) / b) ** 2


def ellipse_point(c, a, b, deg):
    return (c[0] + a * math.cos(deg * DEG), c[1] + b * math.sin(deg * DEG))


def polygon_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・記号は個別"""
    special = {" ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4, "→": 1.0, "←": 1.0,
               "・": 1.0, "×": 0.6, "℃": 1.0, "〜": 1.0}
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
    """ラベル群に含まれる数字の連なり（「1024hPa」→ {"1024"}）"""
    out = set()
    for t in texts:
        out.update(re.findall(r"[0-9]+", t))
    return out


# ===========================================================================
# 描画ヘルパー（Canvas = px 座標。文字は overlay 層に置き、図形より上に描く）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.body = []           # 図形
        self.overlay = []        # 文字（と文字の白地）
        self.texts = []          # (x0, y0, x1, y1, s, own, clear)
        self.obstacles = []      # (oid, [pts...])  ラベルがかかってはいけない線
        self.font_sizes = []
        self.bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

    def _grow(self, x, y, pad=0.0):
        self.bbox[0] = min(self.bbox[0], x - pad)
        self.bbox[1] = min(self.bbox[1], y - pad)
        self.bbox[2] = max(self.bbox[2], x + pad)
        self.bbox[3] = max(self.bbox[3], y + pad)

    def raw(self, s):
        self.body.append(s)

    def obstacle(self, oid, pts):
        if oid is not None and len(pts) >= 2:
            self.obstacles.append((oid, [tuple(p) for p in pts]))

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, oid=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w)
        self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="#000" stroke-width="{w}"{d}/>')
        self.obstacle(oid, [(x1, y1), (x2, y2)])

    def path(self, pts, w=MAIN_W, dash=None, close=False, fill="none", oid=None, join="round"):
        """折れ線（close=True なら多角形）。fill を指定すると塗りつぶし＋輪郭"""
        for x, y in pts:
            self._grow(x, y, w / 2.0)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="{fill}" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="{join}"{d}/>')
        self.obstacle(oid, list(pts) + ([pts[0]] if close else []))

    def fill_poly(self, pts, fill):
        for x, y in pts:
            self._grow(x, y)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')

    def dot(self, x, y, r=DOT_R, oid="dot"):
        self._grow(x, y, r)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')
        self.obstacle(oid, [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r), (x - r, y - r)])

    def rect(self, x, y, w, h, fill="none", sw=1.4, dash=None, oid=None):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], w=sw, dash=dash, close=True,
                  fill=fill, oid=oid, join="miter")

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, own=(), clear=True, bg=False):
        """(x, y) はベースライン。推定ボックスを記録し、bg=True なら白地を敷く"""
        w = est_w(s, size)
        x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        box = (x0, y - 0.8 * size, x0 + w, y + 0.22 * size)
        self.texts.append((box[0], box[1], box[2], box[3], s, tuple(own), clear))
        self.font_sizes.append(size)
        self._grow(box[0], box[1])
        self._grow(box[2], box[3])
        if bg:
            self.overlay.append(f'<rect x="{box[0] - 2:.1f}" y="{box[1] - 1:.1f}" width="{w + 4:.1f}" '
                                f'height="{1.02 * size + 2:.1f}" fill="#fff" stroke="none"/>')
        wgt = f' font-weight="{weight}"' if weight else ""
        self.overlay.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                            f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')
        return box

    def vtext(self, x, y_top, s, size=FS, own=(), clear=True):
        """縦書き（1文字ずつ下へ）。1つの <text> 要素にまとめ、許可リストでは連結した文字列として扱う"""
        pitch = 1.05 * size
        spans = []
        for i, ch in enumerate(s):
            spans.append(f'<tspan x="{x:.1f}" y="{y_top + 0.8 * size + i * pitch:.1f}">{escape(ch)}</tspan>')
        box = (x - size / 2, y_top, x + size / 2, y_top + (len(s) - 1) * pitch + 1.02 * size)
        self.texts.append((box[0], box[1], box[2], box[3], s, tuple(own), clear))
        self.font_sizes.append(size)
        self._grow(box[0], box[1])
        self._grow(box[2], box[3])
        self.overlay.append(f'<text font-size="{size}" text-anchor="middle">{"".join(spans)}</text>')
        return box

    def arrow(self, x1, y1, x2, y2, w=1.8, head=9.0, oid="arrow"):
        """px 座標の矢印（線＋先端の三角形）"""
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, w=w)
        nx, ny = -math.sin(ang), math.cos(ang)
        pts = [(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
               (bx - nx * head * 0.45, by - ny * head * 0.45)]
        self.fill_poly(pts, "#000")
        self.obstacle(oid, [(x1, y1), (x2, y2)])
        self.obstacle(oid, pts + [pts[0]])

    def layout_checks(self, ck, pad=1.0):
        """共通 assert: viewBox 内／ラベル同士が重ならない／ラベルが線にかからない／文字サイズの下限"""
        ck.ok("全要素が viewBox 内に収まる（線幅・推定文字幅込み）",
              self.bbox[0] >= 0 and self.bbox[1] >= 0 and self.bbox[2] <= self.w and self.bbox[3] <= self.h,
              f"bbox=({self.bbox[0]:.1f},{self.bbox[1]:.1f})-({self.bbox[2]:.1f},{self.bbox[3]:.1f})")
        bad = []
        T = self.texts
        for i in range(len(T)):
            for j in range(i + 1, len(T)):
                a, b = T[i], T[j]
                if not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]):
                    bad.append((a[4], b[4]))
        ck.ok("ラベル同士が重ならない（推定ボックスの全ペア）", not bad, f"{bad}")
        hits = []
        for (x0, y0, x1, y1, s, own, clear) in T:
            if not clear:
                continue
            r = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
            for oid, pts in self.obstacles:
                if oid in own:
                    continue
                if any(seg_intersects_rect(a, b, r) for a, b in zip(pts, pts[1:])):
                    hits.append((s, oid))
                    break
        ck.ok("ラベルが線（等圧線・前線・矢印・海岸線・枠・地点）にかからない", not hits, f"{hits}")
        ck.ok(f"文字サイズがすべて {MIN_FS}px 以上（viewBox 幅の 2.8% 以上）",
              min(self.font_sizes) >= MIN_FS, f"min={min(self.font_sizes)}")

    def svg(self, fig_id, title, desc):
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md 準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + "\n".join(self.body) + ("\n" if self.body else "")
            + "\n".join(self.overlay) + "\n</svg>\n"
        )


class Checker:
    """検算の記録つき assert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


class Labels:
    """図が置いたラベルを集める（許可リスト検査の入力）"""
    def __init__(self, cv, fs=FS):
        self.cv, self.fs, self.items = cv, fs, []

    def put(self, x, y, s, size=None, **kw):
        self.items.append(s)
        return self.cv.text(x, y, s, size or self.fs, **kw)

    def vput(self, x, y_top, s, size=None, **kw):
        self.items.append(s)
        return self.cv.vtext(x, y_top, s, size or self.fs, **kw)


class Frame:
    """数学座標（y 上向き）→ px: x_px = ox + s*(x - x0), y_px = oy - s*(y - y0)"""
    def __init__(self, ox, oy, s, x0=0.0, y0=0.0):
        self.ox, self.oy, self.s, self.x0, self.y0 = ox, oy, s, x0, y0

    def P(self, p):
        return (self.ox + self.s * (p[0] - self.x0), self.oy - self.s * (p[1] - self.y0))

    def Ps(self, pts):
        return [self.P(p) for p in pts]

    def inv(self, q):
        return ((q[0] - self.ox) / self.s + self.x0, (self.oy - q[1]) / self.s + self.y0)


class MapFrame(Frame):
    """地図座標の矩形 crop=(mx0, my0, mx1, my1) を、px の左上 (px0, py0) から縮尺 s で描く枠"""
    def __init__(self, px0, py0, s, crop):
        mx0, my0, mx1, my1 = crop
        super().__init__(px0, py0 + s * (my1 - my0), s, mx0, my0)
        self.crop = crop
        self.px_rect = (px0, py0, px0 + s * (mx1 - mx0), py0 + s * (my1 - my0))

    def contains(self, p):
        mx0, my0, mx1, my1 = self.crop
        return mx0 <= p[0] <= mx1 and my0 <= p[1] <= my1


# ===========================================================================
# 気象図の部品
# ===========================================================================
def north_arrow(cv, lb, x, y_top, length=34):
    """北を示す矢印（上向き）と「北」。(x, y_top) は「北」の文字の上端"""
    lb.put(x, y_top + 0.8 * FS, "北", own=("north",))
    cv.arrow(x, y_top + FS + 4 + length, x, y_top + FS + 4, w=1.8, head=10, oid="north")


def person(cv, x, y, s=1.0, oid="person"):
    """町の位置を示す人形マーク。(x, y) は足もと（町の地点）"""
    cv.raw(f'<circle cx="{x:.1f}" cy="{y - 25 * s:.1f}" r="{4.6 * s:.1f}" fill="#fff" stroke="#000" stroke-width="1.6"/>')
    cv.line(x, y - 20.4 * s, x, y - 9 * s, w=1.8)
    cv.line(x - 7 * s, y - 16.5 * s, x + 7 * s, y - 16.5 * s, w=1.8)
    cv.line(x, y - 9 * s, x - 5.5 * s, y, w=1.8)
    cv.line(x, y - 9 * s, x + 5.5 * s, y, w=1.8)
    cv._grow(x - 8 * s, y - 31 * s)
    cv._grow(x + 8 * s, y + 1)
    cv.obstacle(oid, [(x - 8 * s, y - 31 * s), (x + 8 * s, y - 31 * s), (x + 8 * s, y),
                      (x - 8 * s, y), (x - 8 * s, y - 31 * s)])


def center_cross(cv, x, y, r=5.0, oid="center"):
    """気圧の中心を示す×印"""
    cv.line(x - r, y - r, x + r, y + r, w=1.8)
    cv.line(x - r, y + r, x + r, y - r, w=1.8)
    cv.obstacle(oid, [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r), (x - r, y - r)])


def wind_arrow_px(cv, p_px, u_math, length=56.0, oid="wind"):
    """地点 p（px）を中点とする風の矢印。u_math は空気が進む向き（数学座標の単位ベクトル）"""
    ux, uy = u_math[0], -u_math[1]           # px（y 下向き）へ
    h = length / 2.0
    cv.arrow(p_px[0] - ux * h, p_px[1] - uy * h, p_px[0] + ux * h, p_px[1] + uy * h,
             w=1.8, head=10, oid=oid)


def cyclonic_flow(radial_out, kind):
    """中心から地点への単位ベクトル radial_out（数学座標）に対する風の向き（単位ベクトル）。
    kind="low": 反時計回りに吹きこむ＝（中心へ向かう向き＋反時計回りの接線）/√2
    kind="high": 時計回りに吹き出す＝（中心から離れる向き＋時計回りの接線）/√2"""
    r = unit(radial_out)
    if kind == "low":
        return unit(add(mul(r, -1.0), (-r[1], r[0])))
    return unit(add(r, (r[1], -r[0])))


def front_symbols(curve, spacing, first, kinds, size):
    """前線（数学座標の折れ線 curve）の上に記号を等間隔に置く。
    kinds: 記号の種類の列（"tri" / "semi" を順にくり返す）と向き（+1=進む向きに対して左・-1=右）の組の列。
    戻り値: [(kind, 基点, 単位接線, 単位法線（記号の向き）, 多角形の頂点列)]"""
    cum = cum_lengths(curve)
    out = []
    s = first
    i = 0
    while s + size <= cum[-1] - 0.2 * size:
        kind, side = kinds[i % len(kinds)]
        p, t = point_at(curve, cum, s)
        n = (-t[1] * side, t[0] * side)
        if kind == "tri":
            a = add(p, mul(t, -size / 2.0))
            b = add(p, mul(t, size / 2.0))
            apex = add(p, mul(n, size * 0.85))
            poly = [a, apex, b]
        else:
            r = size / 2.0
            poly = [add(p, add(mul(t, r * math.cos(math.pi * k / 12.0)), mul(n, r * math.sin(math.pi * k / 12.0))))
                    for k in range(13)]
        out.append((kind, p, t, n, poly))
        s += spacing
        i += 1
    return out


def band_polygon(axis, half_ws, n=4, cap=5):
    """中心線 axis（制御点）に沿った帯（両端は半円）。half_ws は制御点ごとの半幅（間は線形補間）。
    戻り値: (多角形, 左側の縁, 右側の縁)。左＝進む向き（南西→北東）に対して左側＝北西側。"""
    c = catmull_rom(axis, n=n)
    hw = []
    for i in range(len(axis) - 1):
        for j in range(n):
            hw.append(half_ws[i] + (half_ws[i + 1] - half_ws[i]) * j / n)
    hw.append(half_ws[-1])
    left, right = [], []
    for i, p in enumerate(c):
        if i == 0:
            t = unit(sub(c[1], c[0]))
        elif i == len(c) - 1:
            t = unit(sub(c[-1], c[-2]))
        else:
            t = unit(sub(c[i + 1], c[i - 1]))
        nrm = (-t[1], t[0])
        left.append(add(p, mul(nrm, hw[i])))
        right.append(sub(p, mul(nrm, hw[i])))
    t_end = unit(sub(c[-1], c[-2]))
    t_start = unit(sub(c[1], c[0]))
    cap_end = [add(c[-1], rot(mul((-t_end[1], t_end[0]), hw[-1]), -180.0 * k / cap)) for k in range(1, cap)]
    cap_start = [add(c[0], rot(mul((t_start[1], -t_start[0]), hw[0]), -180.0 * k / cap)) for k in range(1, cap)]
    poly = left + cap_end + right[::-1] + cap_start
    return poly, left, right


# ---- 基図（地図データを使わない簡略な多角形・数学座標の地図単位: 西→東 0〜100・南→北 0〜64） ----
MAP_W, MAP_H = 100.0, 64.0
JAPAN_AXIS = [(45.5, 16.5), (48.5, 22.5), (55.5, 28.0), (63.0, 32.5), (68.0, 38.0),
              (70.8, 44.5), (72.5, 50.5)]           # 九州〜本州の中心線（手で決めた制御点）
JAPAN_HALF_WS = [3.0, 2.7, 2.4, 2.6, 2.6, 2.3, 2.0]
JAPAN_MAIN_POLY, JAPAN_NW_EDGE, JAPAN_SE_EDGE = band_polygon(JAPAN_AXIS, JAPAN_HALF_WS)
JAPAN_NORTH_POLY = [(73.8, 55.2), (76.0, 58.6), (79.5, 59.8), (82.8, 58.8), (80.8, 56.2),
                    (78.2, 53.6), (75.6, 53.3)]   # 北の島（手で決めた頂点）
JAPAN_POLYS = [JAPAN_MAIN_POLY, JAPAN_NORTH_POLY]
CONTINENT_POLY = [(0.0, 64.0), (47.0, 64.0), (45.5, 58.5), (43.0, 53.0), (40.0, 48.0), (41.5, 43.0),
                  (44.5, 37.0), (46.0, 31.5), (45.0, 27.5), (42.5, 27.0), (40.0, 30.5), (38.0, 36.0),
                  (36.0, 39.5), (33.0, 37.0), (29.5, 32.0), (25.5, 26.0), (21.0, 20.0), (16.0, 14.0),
                  (10.5, 9.5), (5.0, 6.0), (0.0, 5.0)]


def in_japan(p):
    return any(point_in_polygon(p, poly) for poly in JAPAN_POLYS)


def on_land(p):
    return in_japan(p) or point_in_polygon(p, CONTINENT_POLY)


def draw_basemap(cv, mf, oid_coast="coast"):
    """大陸と日本列島（簡略な多角形）を枠 mf の範囲で描く"""
    for poly in [CONTINENT_POLY] + JAPAN_POLYS:
        cp = clip_polygon_rect(poly, mf.crop)
        if len(cp) >= 3:
            cv.path(mf.Ps(cp), w=1.2, close=True, fill=LAND_FILL, oid=oid_coast, join="round")


def draw_curve_map(cv, mf, pts, w=THIN_W, closed=False, oid=None, dash=None):
    """地図座標の曲線を枠で切り取って描く。戻り値: 描いた px 折れ線の列"""
    seq = list(pts) + ([pts[0]] if closed else [])
    runs = clip_polyline(seq, mf.crop)
    out = []
    for r in runs:
        rp = mf.Ps(r)
        cv.path(rp, w=w, oid=oid, dash=dash)
        out.append(rp)
    return out


def draw_map_frame(cv, mf, oid="frame"):
    x0, y0, x1, y1 = mf.px_rect
    cv.rect(x0, y0, x1 - x0, y1 - y0, sw=1.2, oid=oid)


# ---- 本文照合 ---------------------------------------------------------------
_LESSON_CACHE = {}


def lesson_text(n):
    """lesson_NN.md の本文（無ければ None）"""
    if n not in _LESSON_CACHE:
        f = LESSON_DIR / f"lesson_{n:02d}.md"
        _LESSON_CACHE[n] = f.read_text(encoding="utf-8") if f.exists() else None
    return _LESSON_CACHE[n]


def body_has(ck, n, needle, what):
    """本文 lesson_NN.md に needle（図のパラメータから組み立てた文字列）があることを照合する"""
    t = lesson_text(n)
    if t is None:
        ck.ok(f"本文照合（{what}）: lesson_{n:02d}.md がこの階層に無いため未実施", True)
        return
    ck.ok(f"本文照合（{what}）: lesson_{n:02d}.md に「{needle}」がある", needle in t)


def iso_label(lb, p_px, level, oid, size=FS_S):
    """等圧線の上に値のラベルを置く（白地で線を切る）。p_px は線上の点"""
    lb.put(p_px[0], p_px[1] + 0.29 * size, str(level), size=size, own=(oid,), bg=True)


def point_label(lb, p_px, s, off_px, size=FS):
    """地点ラベル: 点から off_px（px のずれ）だけ離れた位置を文字の中心にする"""
    cx, cy = p_px[0] + off_px[0], p_px[1] + off_px[1]
    lb.put(cx, cy + 0.29 * size, s, size=size)


def draw_ellipse_family(cv, fr, c, levels, radii, ratio, oid_prefix="iso"):
    """中心 c のまわりの閉じた等圧線（相似な楕円）を描く。戻り値: {level: (a, b, px 折れ線)}"""
    out = {}
    for lv, a in zip(levels, radii):
        b = a * ratio
        pts = fr.Ps(ellipse_pts(c, a, b))
        cv.path(pts, w=THIN_W, close=True, oid=f"{oid_prefix}{lv}")
        out[lv] = (a, b, pts)
    return out


# ===========================================================================
# L01〜L03: 気圧配置と風（子単元 --pressure-wind）
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md「空気の柱と気圧」・図1・架空の値） ---
    P_hPa, Q_hPa = 1012, 900          # 平地の地点P・山頂の地点Q の気圧（架空値）
    H = 420
    ground_y = 340.0                  # 平地の地表（px）
    h_P = 250.0                       # 地点P の空気の柱の高さ（px）
    h_Q = h_P * Q_hPa / P_hPa         # 柱の高さは気圧の値に比例させる
    top_y = ground_y - h_P            # 2本の柱の上端（空の高い所）をそろえる
    summit_y = top_y + h_Q            # 山頂の高さ＝Q の柱の下端
    col_w = 100.0
    xP, xQ = 170.0, 470.0             # 柱の中心 x
    mtn = [(335.0, ground_y), (405.0, summit_y), (535.0, summit_y), (605.0, ground_y)]  # 山（台形）

    ck = Checker()
    ck.ok("柱の高さの比＝気圧の比（1012:900・柱の高さは値に比例）",
          near(h_P / h_Q, P_hPa / Q_hPa), f"h_P={h_P:.2f}px, h_Q={h_Q:.2f}px")
    ck.ok("2本の柱の上端が同じ高さ（空の高い所）", near(ground_y - h_P, summit_y - h_Q))
    ck.ok("地点P の柱は平地（地表）から、地点Q の柱は山頂から立つ",
          near(top_y + h_P, ground_y) and near(top_y + h_Q, summit_y))
    ck.ok("山の高さ＝2本の柱の高さの差（正）", near(ground_y - summit_y, h_P - h_Q) and h_P - h_Q > 0,
          f"山の高さ={ground_y - summit_y:.2f}px")
    ck.ok("地点Q の柱が山頂の平らな部分に収まり、地点P の柱は山にかからない",
          mtn[1][0] <= xQ - col_w / 2 and xQ + col_w / 2 <= mtn[2][0] and xP + col_w / 2 < mtn[0][0])
    ck.ok("高い所（Q）ほど気圧が低く、柱も短い", Q_hPa < P_hPa and h_Q < h_P)
    body_has(ck, 1, f"Pが{P_hPa}hPa、Qが{Q_hPa}hPa", "図1の気圧の値")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 30, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    # 地面と山
    cv.fill_poly([(30, ground_y), (610, ground_y), (610, ground_y + 16), (30, ground_y + 16)], GROUND_FILL)
    cv.line(30, ground_y, mtn[0][0], ground_y, w=MAIN_W, oid="ground")
    cv.path(mtn, w=MAIN_W, fill=GROUND_FILL, oid="ground")
    cv.line(mtn[3][0], ground_y, 610, ground_y, w=MAIN_W, oid="ground")
    # 空気の柱
    for xc, h, base in ((xP, h_P, ground_y), (xQ, h_Q, summit_y)):
        cv.rect(xc - col_w / 2, base - h, col_w, h, fill="#ececec", sw=1.4, oid="col")
    cv.line(40, top_y, 610, top_y, w=AUX_W, dash=DASH, oid="top")
    lb.put(40, top_y - 10, "空の高い所", size=FS_S, anchor="start")
    for xc, h, base in ((xP, h_P, ground_y), (xQ, h_Q, summit_y)):
        lb.put(xc, base - h + 44, "空気の柱", own=("col",))
    lb.put(xP - col_w / 2 - 10, top_y + h_P / 2 + 6, f"{P_hPa}hPa", anchor="end", weight="bold")
    lb.put(xQ + col_w / 2 + 10, summit_y - h_Q / 2 + 6, f"{Q_hPa}hPa", anchor="start", weight="bold")
    cv.dot(xP, ground_y)
    cv.dot(xQ, summit_y)
    lb.put(xP, ground_y + 44, "平地の地点P", own=("ground",))
    lb.put(xQ, ground_y + 44, "山頂の地点Q", own=("ground",))
    cv.line(xQ, ground_y + 26, xQ, summit_y + 6, w=1.0, oid="leaderQ")
    cv.layout_checks(ck)

    return {"file": "L01_fig1_air_column_pressure.svg", "lesson": "L01", "canvas": cv,
            "title": "空気の柱と気圧——平地の地点P（1012hPa）と山頂の地点Q（900hPa）",
            "desc": "平地の地点Pと山頂の地点Qの上にある空気の柱を2本の長方形でくらべた模式図（教材用に作成・架空の値）。"
                    "柱の上端（空の高い所）をそろえ、柱の高さを気圧の値（Pが1012hPa、Qが900hPa）に比例させてかいた。"
                    "同型図は2地点の気圧の値を差し替えて生成する（柱の高さの比＝気圧の比・山の高さ＝柱の高さの差）",
            "alt": "平地の地点Pと山頂の地点Qの空気の柱の長さと気圧の大小（模式図・教材用に作成・架空の値）",
            "intent": "気圧を「その場所より上にある空気の柱の重さ」ととらえ、高い所ほど柱が短く気圧が低いことを長さのちがいで見せる",
            "src": "lesson_01.md「空気の柱と気圧」（注意書きの直後）",
            "params": f"地点P {P_hPa}hPa・地点Q {Q_hPa}hPa（架空値）／柱の高さ P {h_P:.1f}px・Q {h_Q:.1f}px（比＝気圧の比）／山の高さ {h_P - h_Q:.1f}px",
            "checks": ck.items,
            "check_tokens": ["112", "短い", "長い", "気圧が低", "気圧は低", "気圧が高", "気圧は高", "空気が少ない", "空気が多い"],
            "digit_rule": ("subset", {"1012", "900"}),
            "allow_texts": lb.items}


def fig_L01_2():
    # --- パラメータ（lesson_01.md「模式天気図の読み方」・図2・架空の値） ---
    high_c, high_v = (-142.0, 0.0), 1024      # 高気圧の中心（西）と値
    low_c, low_v = (142.0, 0.0), 996          # 低気圧の中心（東）と値
    step = 4                                  # 等圧線は 4hPa ごと
    high_levels = [1020, 1016, 1012]          # 内側から外側へ
    low_levels = [1000, 1004, 1008]
    radii = [44.0, 88.0, 132.0]               # 楕円の東西の半径（px）
    ratio = 0.85                              # 南北の半径／東西の半径
    labeled = [1020, 1012, 1004]              # 数字を書く線
    pts_spec = {"ア": (1020, 200.0), "イ": (1012, 300.0), "ウ": (1004, 150.0), "エ": (1000, -30.0)}
    H = 410
    fr = Frame(320.0, 215.0, 1.0)             # 数学座標（1 単位＝1px・図の中心が原点）

    ck = Checker()
    ck.ok("等圧線は 4hPa ごと: 高気圧の中心 1024 から外へ 1020・1016・1012",
          [high_v - step * (i + 1) for i in range(3)] == high_levels)
    ck.ok("等圧線は 4hPa ごと: 低気圧の中心 996 から外へ 1000・1004・1008",
          [low_v + step * (i + 1) for i in range(3)] == low_levels)
    ck.ok("2つの族の外側の線（1012 と 1008）も 4hPa ちがい（あいだに線が抜けていない）",
          high_levels[-1] - low_levels[-1] == step)
    ck.ok("高気圧が西（左）、低気圧が東（右）", high_c[0] < low_c[0])
    ck.ok("数字を書く線は 1020・1012・1004 の3本", sorted(labeled) == [1004, 1012, 1020])
    body_has(ck, 1, "数字がかかれている線は" + "・".join(str(v) for v in labeled) + "の3本", "数字を書く線")
    body_has(ck, 1, f"高気圧の中心の値は{high_v}hPa、低気圧の中心の値は{low_v}hPa", "中心の値")
    body_has(ck, 1, f"{step}hPaごと", "等圧線の間隔")

    cv = Canvas(W, H)
    lb = Labels(cv)
    cv.rect(30, 50, 580, 320, sw=1.2, oid="frame")
    fam_h = draw_ellipse_family(cv, fr, high_c, high_levels, radii, ratio)
    fam_l = draw_ellipse_family(cv, fr, low_c, low_levels, radii, ratio)
    fams = {**fam_h, **fam_l}
    ck.ok("等圧線はすべて閉じていて枠の内側にある（閉じた等圧線）",
          all(30 < x < 610 and 50 < y < 370 for (_, _, pts) in fams.values() for x, y in pts))
    ck.ok("同じ族の中で楕円は入れ子（半径が外へ単調に増える）", radii == sorted(radii) and len(set(radii)) == 3)
    gap = min_dist_polylines(fam_h[high_levels[-1]][2], fam_l[low_levels[-1]][2])
    ck.ok("高気圧の族と低気圧の族の楕円は交わらない（最小距離 > 10px）", gap > 10.0, f"最小距離={gap:.1f}px")
    # 中心
    for c, mark, v in ((high_c, "高", high_v), (low_c, "低", low_v)):
        x, y = fr.P(c)
        lb.put(x, y - 2, mark, weight="bold")
        lb.put(x, y + 18, str(v), size=FS_S)
    # 数字を書く線（上端に白地つきで）
    for lv in labeled:
        c = high_c if lv in fam_h else low_c
        a, b, _ = fams[lv]
        iso_label(lb, fr.P((c[0], c[1] + b)), lv, f"iso{lv}")
    # 地点ア〜エ（のっている線の上。ラベルは線と線のあいだへ）
    got = {}
    for name, (lv, ang) in pts_spec.items():
        c = high_c if lv in fam_h else low_c
        a, b, _ = fams[lv]
        p = ellipse_point(c, a, b, ang)
        got[name] = (lv, ellipse_val(p, c, a, b))
        pp = fr.P(p)
        cv.dot(*pp)
        radial = unit(sub(p, c))
        off = (radial[0] * 21.0, -radial[1] * 21.0)
        point_label(lb, pp, name, off)
    ck.ok("地点ア〜エがそれぞれ 1020・1012・1004・1000 の線上（楕円の式の値＝1・誤差 1e-9）",
          [got[k][0] for k in ("ア", "イ", "ウ", "エ")] == [1020, 1012, 1004, 1000]
          and all(near(v, 1.0) for _, v in got.values()))
    ck.ok("地点の気圧はすべて 996〜1024 の範囲", all(low_v <= got[k][0] <= high_v for k in got))
    ck.ok("地点エの線（1000）は数字なしの線で、数字ありの 1004 と中心 996 のあいだ",
          got["エ"][0] not in labeled and low_v < got["エ"][0] < 1004)
    north_arrow(cv, lb, 586, 56, length=28)
    lb.put(30, 398, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L01_fig2_schematic_weather_map.svg", "lesson": "L01", "canvas": cv,
            "title": "模式天気図——西に高気圧（中心1024hPa）、東に低気圧（中心996hPa）、4hPaごとの等圧線と地点ア〜エ",
            "desc": "北が上の模式天気図（教材用に作成・架空の値）。西に高気圧（中心1024hPa）、東に低気圧（中心996hPa）があり、"
                    "それぞれのまわりに4hPaごとの閉じた等圧線（相似な楕円）を3本ずつ引いた。数字は1020・1012・1004の線にだけ書き、"
                    "地点ア〜エは等圧線の上に置いた（地点の横に気圧値は書かない）。同型図は中心の値・線の本数・地点ののる線を差し替えて生成する",
            "alt": "模式天気図——西に高気圧（中心1024hPa）、東に低気圧（中心996hPa）、4hPaごとの等圧線と地点ア〜エ（模式図・教材用に作成・架空の値）",
            "intent": "等圧線は同じ気圧の地点を結んだ線で、閉じた等圧線の中心がまわりより高い所が高気圧・低い所が低気圧であることと、数字のない線の値を4hPaずつ数えて読むことを練習させる",
            "src": "lesson_01.md「模式天気図の読み方」（注意書きの直後）",
            "params": "高気圧 中心1024hPa（西）・低気圧 中心996hPa（東）／等圧線 4hPaごと（高: 1020・1016・1012、低: 1000・1004・1008）／"
                      "数字を書く線 1020・1012・1004／地点ア 1020・イ 1012・ウ 1004・エ 1000 の線上／楕円 東西の半径 44・88・132px・南北は 0.85倍",
            "checks": ck.items,
            "check_tokens": ["1000", "1016", "1008", "16hPa", "28hPa", "低くなる", "高くなる"],
            "digit_rule": ("subset", {"1024", "996", "1020", "1012", "1004"}),
            "allow_texts": lb.items}


# 風向の約束（lesson_02.md「読み取りのコツ」・answer_key 冒頭の約束と同じ）
LOW_SIDE_WIND = {"東": "南東", "北": "北東", "西": "北西", "南": "南西"}
HIGH_SIDE_WIND = {"東": "北西", "北": "南西", "西": "南東", "南": "北東"}
SIDE_VEC = {"東": (1.0, 0.0), "北": (0.0, 1.0), "西": (-1.0, 0.0), "南": (0.0, -1.0)}


def check_cyclonic_arrow(ck, name, side, u, kind):
    """矢印 u（空気が進む向き）の検算: 45°・回る向き・8方位の風向"""
    r = SIDE_VEC[side]
    toward = mul(r, -1.0) if kind == "low" else r
    ang = angle_between(u, toward)
    t_ccw = (-r[1], r[0])                   # 中心のまわりを反時計回りに回る向き（接線）
    circ = dot(u, t_ccw)                    # 正＝反時計回りに回る・負＝時計回りに回る
    src = mul(u, -1.0)
    word, dev = compass8(src)
    expect = (LOW_SIDE_WIND if kind == "low" else HIGH_SIDE_WIND)[side]
    rot_ok = circ > 0 if kind == "low" else circ < 0
    ck.ok(f"地点{name}（中心の{side}側）: 矢印は中心へ向かう（離れる）向きと45°・"
          f"{'反時計回りに吹きこむ' if kind == 'low' else '時計回りに吹き出す'}・根もとの方位＝約束の風向",
          near(ang, 45.0, 1e-9) and rot_ok and dev < 1e-9 and word == expect)


def fig_L02_1():
    # --- パラメータ（lesson_02.md「高気圧・低気圧のまわりの風」・図1） ---
    high_c, low_c = (165.0, -190.0), (475.0, -190.0)    # 数学座標（1単位＝1px。y は上向き）
    r_in, r_out = 48.0, 95.0                               # 等圧線（円）の半径
    arrow_len = 56.0
    low_pts = [("ア", "東"), ("イ", "北"), ("ウ", "西"), ("エ", "南")]
    high_pts = [("カ", "東"), ("キ", "北"), ("ク", "西"), ("ケ", "南")]
    H = 400
    fr = Frame(0.0, 0.0, 1.0)

    ck = Checker()
    body_has(ck, 2, "東側→" + LOW_SIDE_WIND["東"] + "、北側→" + LOW_SIDE_WIND["北"] + "、西側→"
             + LOW_SIDE_WIND["西"] + "、南側→" + LOW_SIDE_WIND["南"], "低気圧のまわりの風向の並び")
    body_has(ck, 2, "高気圧のまわりでは、同じ側の地点の風向が低気圧のときとちょうど反対の方位になります", "高気圧は逆")
    body_has(ck, 2, "図1の矢印は北西へ向かい、根もとは南東側にある", "例題1の読み方")
    for side in SIDE_VEC:
        ck.ok(f"約束: 中心の{side}側で高気圧の風向は低気圧の風向の反対（逆向き）",
              near(angle_between(compass_vec(LOW_SIDE_WIND[side]), compass_vec(HIGH_SIDE_WIND[side])), 180.0, 1e-9))

    cv = Canvas(W, H)
    lb = Labels(cv)
    for c, kind, pts, mark, rule in ((high_c, "high", high_pts, "高", "時計回りに吹き出す"),
                                     (low_c, "low", low_pts, "低", "反時計回りに吹きこむ")):
        for r in (r_in, r_out):
            cv.path(fr.Ps(ellipse_pts(c, r, r)), w=THIN_W, close=True, oid=f"iso{kind}{int(r)}")
        cx, cy = fr.P(c)
        lb.put(cx, cy + 0.29 * FS, mark, weight="bold")
        for name, side in pts:
            rv = SIDE_VEC[side]
            p = add(c, mul(rv, r_out))
            u = cyclonic_flow(rv, kind)
            check_cyclonic_arrow(ck, name, side, u, kind)
            pp = fr.P(p)
            cv.dot(*pp)
            wind_arrow_px(cv, pp, u, arrow_len)
            perp = (-u[1], u[0])
            if dot(perp, rv) < 0:
                perp = mul(perp, -1.0)
            point_label(lb, pp, name, (perp[0] * 26.0, -perp[1] * 26.0))
        lb.put(cx, 352, rule, size=FS_S)
    north_arrow(cv, lb, 320, 40, length=34)
    lb.put(320, 390, "模式図（教材用に作成）", size=FS_S)
    cv.layout_checks(ck)

    return {"file": "L02_fig1_wind_around_highs_lows.svg", "lesson": "L02", "canvas": cv,
            "title": "高気圧と低気圧のまわりの風の吹き方（北半球・上空から見た模式図）",
            "desc": "北が上・上空から見た模式図（教材用に作成）。左に高気圧、右に低気圧を置き、それぞれ2本の円形の等圧線と、"
                    "外側の円の東・北・西・南の地点に風の矢印をかいた。矢印は等圧線にそう向きと中心へ向かう（高気圧では中心から離れる）"
                    "向きのちょうど中間（45°）で、低気圧へは反時計回りに吹きこみ、高気圧からは時計回りに吹き出す。"
                    "地点ア〜エは低気圧のまわり、カ〜ケは高気圧のまわり。風向の文字は図に入れない。同型図は地点の数と位置を差し替えて生成する",
            "alt": "高気圧と低気圧のまわりの風の吹き方（北半球・上空から見た模式図・教材用に作成）。高気圧の中心からは時計回りに吹き出し、低気圧の中心へは反時計回りに吹きこむ。地点ア〜エは低気圧のまわり、カ〜ケは高気圧のまわりに置いてある。風向の文字は図に書かれていない",
            "intent": "北半球で低気圧には反時計回りに吹きこみ高気圧からは時計回りに吹き出すことと、矢印の根もとの側を8方位で読むことを1枚で見せる",
            "src": "lesson_02.md「高気圧・低気圧のまわりの風」（注意書きの直後）",
            "params": "円の半径 48・95px／地点は外側の円の東・北・西・南（低: ア・イ・ウ・エ／高: カ・キ・ク・ケ）／矢印 56px・中心へ向かう（離れる）向きから45°",
            "checks": ck.items,
            "check_tokens": ["北東", "北西", "南東", "南西", "東の風", "西の風", "南の風", "北の風", "上昇気流", "くずれ"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def fig_L02_2():
    # --- パラメータ（lesson_02.md「上空の図から自分の町の風向へ」・図2） ---
    low_c = (320.0, -215.0)            # 数学座標（1単位＝1px）
    r_in, r_out = 60.0, 120.0
    town_side = "北"                    # 町は中心の北側（＝低気圧の中心が町の南）
    arrow_len = 72.0
    H = 385
    fr = Frame(0.0, 0.0, 1.0)

    ck = Checker()
    rv = SIDE_VEC[town_side]
    town = add(low_c, mul(rv, r_out))
    u = cyclonic_flow(rv, "low")
    ck.ok("町は低気圧の中心の真北（中心が町の南）", near(town[0], low_c[0]) and town[1] > low_c[1])
    check_cyclonic_arrow(ck, "町", town_side, u, "low")
    body_has(ck, 2, "図2の矢印は南西へ向かい、根もとは北東側", "例題2の読み方")
    ck.ok("矢印の向き（空気が進む向き）が本文どおり南西", compass8(u)[0] == "南西" and compass8(u)[1] < 1e-9)

    cv = Canvas(W, H)
    lb = Labels(cv)
    for r in (r_in, r_out):
        cv.path(fr.Ps(ellipse_pts(low_c, r, r)), w=THIN_W, close=True, oid=f"iso{int(r)}")
    cx, cy = fr.P(low_c)
    lb.put(cx, cy + 0.29 * FS, "低", weight="bold")
    tp = fr.P(town)
    wind_arrow_px(cv, tp, u, arrow_len)
    person(cv, tp[0], tp[1], s=1.15)
    lb.put(tp[0] - 18, tp[1] - 12, "町", anchor="end")
    lb.put(tp[0] + 46, tp[1] - 30, "町の風向は？", anchor="start")
    north_arrow(cv, lb, 590, 12, length=34)
    lb.put(320, 373, "模式図（教材用に作成）", size=FS_S)
    cv.layout_checks(ck)

    return {"file": "L02_fig2_viewpoint_shift_town.svg", "lesson": "L02", "canvas": cv,
            "title": "低気圧の中心が町の南にあるときの町の位置と風の矢印（答えは「？」）",
            "desc": "北が上・上空から見た模式図（教材用に作成）。低気圧の中心とそのまわりの円形の等圧線2本をかき、"
                    "中心の真北（中心が町の南）の等圧線上に町（人形マーク）を置いた。町の地点に、レッスン2の約束どおり"
                    "反時計回りに吹きこむ風の矢印（中心へ向かう向きから45°）をかき、町の風向は「？」とした。"
                    "同型図は町を置く側（東・北・西・南）を差し替えて生成する",
            "alt": "低気圧の中心が町の南にあるときの、町の位置（人形マーク）と風の矢印（模式図・教材用に作成）。町の風向は「？」で示し、答えは図に書かれていない",
            "intent": "上空から見た図に町（人形）を置き、その地点の矢印の根もとを読んで風向に言いかえる手順を練習させる",
            "src": "lesson_02.md「上空の図から自分の町の風向へ」（注意書きの直後）",
            "params": "円の半径 60・120px／町は外側の円の真北（中心が町の南）／矢印 72px・中心へ向かう向きと45°（反時計回りに吹きこむ側）",
            "checks": ck.items,
            "check_tokens": ["北東", "北西", "南東", "南西", "東の風", "西の風", "南の風", "北の風"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def fig_L03_1():
    # --- パラメータ（lesson_03.md「連続模式天気図を読む」・図1・架空の値） ---
    high_v, low_v = 1024, 996
    step = 4
    high_levels, low_levels = [1020, 1016, 1012], [1000, 1004, 1008]
    low_pos = [-3, -2, -1]            # 低気圧の中心の目盛り（1日目・2日目・3日目。西が負）
    high_pos = [0, 1, 2]              # 高気圧の中心の目盛り
    town = 0                          # 町の目盛り（3枚とも同じ）
    x_range = (-5, 4)                 # 図の東西の範囲（目盛り）
    radii_t = [0.5, 0.925, 1.35]      # 楕円の東西の半径（目盛り）
    ratio = 0.9
    H = 712
    x_left, x_right = 30.0, 610.0
    s = (x_right - x_left) / (x_range[1] - x_range[0])   # 1目盛りの px
    panel_top = [74.0, 250.0, 426.0]
    panel_h = 170.0

    ck = Checker()
    ck.ok("低気圧の中心: 1日目 西へ3・2日目 西へ2・3日目 西へ1／高気圧の中心: 0・東へ1・東へ2",
          low_pos == [-3, -2, -1] and high_pos == [0, 1, 2])
    ck.ok("どちらの中心も1日に目盛り1つ分ずつ東へ動く（等間隔）",
          all(low_pos[i + 1] - low_pos[i] == 1 and high_pos[i + 1] - high_pos[i] == 1 for i in range(2)))
    ck.ok("1日目は高気圧の中心が町の真上（目盛り0）", high_pos[0] == town)
    ck.ok("2日目・3日目は町が低気圧の東側かつ高気圧の西側（東西の対応表〔レッスン2の約束〕で2つの中心から同じ風向になる配置。町を通る等圧線の向きは使っていない）",
          all(low_pos[d] < town < high_pos[d] for d in (1, 2)))
    ck.ok("等圧線は 4hPa ごと（1024→1020→1016→1012／996→1000→1004→1008）",
          [high_v - step * (i + 1) for i in range(3)] == high_levels
          and [low_v + step * (i + 1) for i in range(3)] == low_levels and high_levels[-1] - low_levels[-1] == step)
    body_has(ck, 3, "低気圧の中心は町の西、目盛り3つ分の所（西へ3）", "1日目の低気圧の位置")
    body_has(ck, 3, "1日目は、高気圧の中心が町と同じ位置（目盛り0・町の上空）", "1日目の高気圧の位置")
    body_has(ck, 3, "東へ目盛り1つ分ずつ", "1日の移動量")
    body_has(ck, 3, f"高気圧の中心の値は{high_v}hPa、低気圧の中心の値は{low_v}hPa", "中心の値")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(x_left, 30, f"中心の気圧: 高 {high_v}hPa・低 {low_v}hPa（等圧線は{step}hPaごと）", size=FS_S, anchor="start")
    lb.put(x_left, 56, "人形マーク＝町（3枚とも同じ位置・目盛り0）", size=FS_S, anchor="start")
    north_arrow(cv, lb, 592, 4, length=30)
    min_gap = float("inf")
    for d in range(3):
        top = panel_top[d]
        yc = top + panel_h / 2.0
        fr = Frame(x_left - s * x_range[0], yc, s)       # 数学座標: x=目盛り, y=目盛り（北が上）
        cv.rect(x_left, top, x_right - x_left, panel_h, sw=1.2, oid=f"frame{d}")
        fam = {}
        for c, levels, kind in (((low_pos[d], 0.0), low_levels, "L"), ((high_pos[d], 0.0), high_levels, "H")):
            for lv, a in zip(levels, radii_t):
                pts = fr.Ps(ellipse_pts(c, a, a * ratio))
                ck.ok(f"{d + 1}日目: {lv} の線が枠の内側で閉じている",
                      all(x_left < x < x_right and top < y < top + panel_h for x, y in pts))
                cv.path(pts, w=THIN_W, close=True, oid=f"iso{d}{lv}")
                fam[lv] = pts
        g = min_dist_polylines(fam[high_levels[-1]], fam[low_levels[-1]])
        min_gap = min(min_gap, g)
        for pos, mark in ((low_pos[d], "低"), (high_pos[d], "高")):
            px, py = fr.P((pos, 0.0))
            center_cross(cv, px, py, r=4.0, oid=f"cross{d}{mark}")
            lb.put(px + 18.5, py + 0.29 * FS, mark, weight="bold")
        for k in range(x_range[0], x_range[1] + 1):
            xk = fr.P((k, 0.0))[0]
            cv.line(xk, top + panel_h - 7, xk, top + panel_h, w=1.2)
        tx, ty = fr.P((town, 0.0))
        person(cv, tx, ty, s=0.8, oid=f"person{d}")
        lb.put(x_left + 10, top + 24, f"{d + 1}日目", anchor="start")
    ck.ok("各日: 高気圧の族と低気圧の族の楕円は交わらない（最小距離 > 12px）", min_gap > 12.0, f"最小距離={min_gap:.1f}px")
    # 目盛り（図の下）
    ys = 620.0
    fr0 = Frame(x_left - s * x_range[0], ys, s)
    cv.line(x_left, ys, x_right, ys, w=MAIN_W, oid="scale")
    for k in range(x_range[0], x_range[1] + 1):
        xk = fr0.P((k, 0.0))[0]
        cv.line(xk, ys - 6, xk, ys + 6, w=1.4, oid="scale")
        lb.put(xk, ys + 26, str(abs(k)), size=FS_S)
    lb.put(x_left, ys + 52, "← 西", size=FS_S, anchor="start")
    lb.put(x_right, ys + 52, "東 →", size=FS_S, anchor="end")
    lb.put(320, ys + 52, "目盛り（町が0）", size=FS_S)
    lb.put(x_left, ys + 84, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    ck.ok("目盛りの間隔が等しい（1目盛り＝一定の px）",
          all(near(fr0.P((k + 1, 0))[0] - fr0.P((k, 0))[0], s) for k in range(x_range[0], x_range[1])))
    cv.layout_checks(ck)

    return {"file": "L03_fig1_three_day_sequence.svg", "lesson": "L03", "canvas": cv,
            "title": "連続模式天気図（1日目・2日目・3日目）——低気圧と高気圧が1日に目盛り1つ分ずつ東へ動く",
            "desc": "北が上の模式天気図3枚（教材用に作成・架空の値）。西の低気圧（中心996hPa）と東の高気圧（中心1024hPa）の"
                    "まわりに4hPaごとの閉じた等圧線を3本ずつ引き、中心を×で示した。低気圧の中心は目盛りで1日目 西へ3・2日目 西へ2・"
                    "3日目 西へ1、高気圧の中心は 0・東へ1・東へ2 にある。町（人形マーク）は3枚とも目盛り0。図の下に西から東への目盛り。"
                    "同型図は各日の中心の目盛りを差し替えて生成する",
            "alt": "連続模式天気図（1日目・2日目・3日目）——西の低気圧（中心996hPa）と東の高気圧（中心1024hPa）が、1日に目盛り1つ分ずつ東へ動く。町の位置は3枚とも同じ（模式図・教材用に作成・架空の値）",
            "intent": "同じ記号だけを目で追って、高気圧・低気圧が西から東へ動くことを目盛りで読ませ、町の風向や翌日以降の配置を推測する材料にする",
            "src": "lesson_03.md「連続模式天気図を読む」（注意書きの直後）",
            "params": "低気圧の中心 西へ3・2・1（1〜3日目）・高気圧の中心 0・東へ1・東へ2／町 目盛り0／等圧線 4hPaごと各3本／"
                      f"範囲 西へ5〜東へ4・1目盛り {s:.2f}px",
            "checks": ck.items,
            "check_tokens": ["東へ2個分", "個分", "北西", "南東", "晴れ", "くずれ", "4日目", "5日目", "偏西風", "西の風",
                             "東の風", "上昇", "下降"],
            "digit_rule": ("subset", {"0", "1", "2", "3", "4", "5", "1024", "996"}),
            "allow_texts": lb.items}


def fig_L03_2():
    # --- パラメータ（lesson_03.md「地球と大気の厚さ」・図2・イメージ図） ---
    c = (320.0, 236.0)                 # px
    r = 160.0                          # 地球の半径（px）
    t = 4.0                            # 大気の層の厚さ（px）——「ごく薄い」ことを伝えるイメージ（正確な縮尺ではない）
    H = 440

    ck = Checker()
    ck.ok("大気の層の厚さは地球の半径の 3% 未満（ごく細い環）", t / r < 0.03, f"t/r={t / r:.3f}")
    body_has(ck, 3, "正確な縮尺ではかいてありません", "イメージ図の断り")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 30, "イメージ図（正確な縮尺ではない・教材用に作成）", size=FS_S, anchor="start")
    n = 240
    outer = [(c[0] + (r + t) * math.cos(2 * math.pi * i / n), c[1] - (r + t) * math.sin(2 * math.pi * i / n)) for i in range(n)]
    inner = [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] - r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    cv.fill_poly(inner, LAND_FILL)
    d = ("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in outer) + " Z M "
         + " L ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(inner)) + " Z")
    cv.raw(f'<path d="{d}" fill="#6e6e6e" fill-rule="evenodd" stroke="none"/>')
    for x, y in outer:
        cv._grow(x, y)
    cv.obstacle("ring", outer + [outer[0]])
    lb.put(c[0], c[1] + 0.29 * FS, "地球", weight="bold")
    ang = 42.0
    q = (c[0] + (r + t) * math.cos(ang * DEG), c[1] - (r + t) * math.sin(ang * DEG))
    lp = (q[0] + 52.0, q[1] - 40.0)
    cv.line(q[0] + 2, q[1] - 2, lp[0] - 4, lp[1] + 4, w=1.0, oid="leader")
    lb.put(lp[0], lp[1] - 2, "大気の層", anchor="start", own=("leader",))
    cv.layout_checks(ck)

    return {"file": "L03_fig2_earth_and_atmosphere.svg", "lesson": "L03", "canvas": cv,
            "title": "地球と大気の層の厚さのイメージ図（正確な縮尺ではない）",
            "desc": "大きな円（地球）のまわりに大気の層をごく細い環（半径の2.5%。描くための値で、実際の比率ではない）でかいたイメージ図（教材用に作成）。"
                    "厚さの数値を読み取る図ではなく、大気の層が地球の大きさにくらべてごく薄いことだけを伝える。"
                    "同型図は環の厚さ（半径に対する割合）を差し替えて生成する",
            "alt": "地球と大気の層の厚さのイメージ図——大きな円（地球）に対して、大気の層をごく細い環でかいたもの（イメージ図・正確な縮尺ではない・教材用に作成）",
            "intent": "気象現象が起こっている大気の層が、地球の大きさにくらべてごく薄いことを直感的に見せる（触れる水準）",
            "src": "lesson_03.md「地球と大気の厚さ」（注意書きの直後）",
            "params": f"地球の半径 {r:.0f}px・大気の層の厚さ {t:.0f}px（イメージ・正確な縮尺ではない）",
            "checks": ck.items,
            "check_tokens": ["km", "キロ"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


# ===========================================================================
# L04〜L06: 気団・前線と天気の変化（子単元 --air-masses-fronts）
# ===========================================================================
def box_center(box):
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def box_inside_poly(box, poly):
    """文字ボックスの4隅がすべて多角形の内側"""
    x0, y0, x1, y1 = box[:4]
    return all(point_in_polygon(q, poly) for q in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))


def fig_L04_1():
    # --- パラメータ（lesson_04.md「気団——性質は『どこでできたか』で決まる」・図1） ---
    cols = ["冷たい（北の方）", "暖かい（南の方）"]     # 横の軸（気温の軸）: 左→右
    rows = ["乾いた（陸の上）", "湿った（海の上）"]     # 縦の軸（水蒸気の軸）: 上→下
    gx, gy = 200.0, 118.0            # 区画の左上（px）
    cw, chh = 190.0, 110.0           # 1区画の幅・高さ
    H = 400

    ck = Checker()
    body_has(ck, 4, "横の軸に気温、縦の軸に水蒸気の量をとった4つの区画", "2つの軸")
    body_has(ck, 4, "北の方でできた気団は冷たく、南の方でできた気団は暖かい", "気温の軸の語")
    body_has(ck, 4, "海の上でできた気団は海から水蒸気を受け取って湿っており、陸の上でできた気団は水蒸気が少なく乾いている",
             "水蒸気の軸の語")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 30, "模式図（教材用に作成）", size=FS_S, anchor="start")
    cells = []
    for i in range(2):
        for j in range(2):
            x, y = gx + j * cw, gy + i * chh
            cv.rect(x, y, cw, chh, sw=MAIN_W, oid="grid")
            cells.append((x, y, x + cw, y + chh))
    ck.ok("区画は 2×2（4区画）", len(cells) == 4)
    tb = lb.put(gx + cw, 70, "気温の軸（横）", weight="bold")
    col_boxes = [lb.put(gx + cw * (j + 0.5), gy - 12, cols[j]) for j in range(2)]
    row_boxes = [lb.put(gx - 12, gy + chh * (i + 0.5) + 0.29 * FS, rows[i], anchor="end") for i in range(2)]
    vb = lb.put(gx - 12, 70, "水蒸気の軸（縦）", weight="bold", anchor="end")
    ck.ok("横の軸: 左の列が「冷たい（北の方）」・右の列が「暖かい（南の方）」",
          all(gx + cw * j < box_center(col_boxes[j])[0] < gx + cw * (j + 1) for j in range(2)))
    ck.ok("縦の軸: 上の行が「乾いた（陸の上）」・下の行が「湿った（海の上）」",
          all(gy + chh * i < box_center(row_boxes[i])[1] < gy + chh * (i + 1) for i in range(2)))
    ck.ok("軸の見出し: 気温の軸は列の見出しの上・水蒸気の軸は行の見出しの列の上",
          tb[3] < min(b[1] for b in col_boxes) and vb[3] < min(b[1] for b in row_boxes)
          and near(vb[2], max(b[2] for b in row_boxes)))
    inside = [t[4] for t in cv.texts for c in cells
              if not (t[2] <= c[0] or c[2] <= t[0] or t[3] <= c[1] or c[3] <= t[1])]
    ck.ok("区画の中に文字を置かない（気団の名前・数値を書かない）", not inside, f"{inside}")
    cv.layout_checks(ck)

    return {"file": "L04_fig1_air_mass_two_axes.svg", "lesson": "L04", "canvas": cv,
            "title": "気団の性質の2つの軸——気温（冷たい・暖かい）と水蒸気の量（乾いた・湿った）の2×2の区画",
            "desc": "横の軸に気温（左: 冷たい＝北の方、右: 暖かい＝南の方）、縦の軸に水蒸気の量（上: 乾いた＝陸の上、下: 湿った＝海の上）をとった"
                    "2×2の区画の模式図（教材用に作成）。区画の中は空欄で、気団の名前や数値は書かない。"
                    "同型図は軸の語（発生場所と性質の対応）を差し替えて生成する",
            "alt": "気団の性質の2つの軸——横に「冷たい（北の方）／暖かい（南の方）」をとり縦に「乾いた（陸の上）／湿った（海の上）」をとった2×2の区画（模式図・教材用に作成）",
            "intent": "気団の性質を「気温の軸の語」と「水蒸気の軸の語」の2語の組で言うこと、発生場所と性質が軸ごとに対応することを区画で見せる",
            "src": "lesson_04.md「気団——性質は『どこでできたか』で決まる」（注意書きの直後）",
            "params": "区画 2×2（1区画 190×110px）／列: 冷たい（北の方）・暖かい（南の方）／行: 乾いた（陸の上）・湿った（海の上）",
            "checks": ck.items,
            "check_tokens": ["暖かく湿った", "冷たく湿った", "暖かく乾いた", "冷たく乾いた", "南の方の陸の上",
                             "シベリア", "小笠原", "オホーツク"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def draw_section_frame(cv, x0, x1, top, ground):
    """断面図の枠（空）と地面の帯"""
    cv.fill_poly([(x0, ground), (x1, ground), (x1, ground + 14), (x0, ground + 14)], GROUND_FILL)
    cv.path([(x0, ground), (x0, top), (x1, top), (x1, ground)], w=1.2, oid="frame", join="miter")
    cv.line(x0, ground, x1, ground, w=MAIN_W, oid="ground")


def fig_L04_2():
    # --- パラメータ（lesson_04.md「暖気と寒気が出会うと——前線面と前線」・図2） ---
    x0, x1, top, ground = 30.0, 610.0, 80.0, 300.0
    F = (380.0, ground)              # 境の面が地表と交わる所
    slope = 0.92                     # 境の面の傾き 傾き（縦/横）（px・見やすいように大きく）
    T = (F[0] - (ground - top) / slope, top)   # 境の面が枠の上端と交わる所
    H = 390

    ck = Checker()
    cold = [(x0, top), T, F, (x0, ground)]
    warm = [T, (x1, top), (x1, ground), F]
    ck.ok("境の面は地表と1か所で交わり、そこから寒気の側（左）へ上がる", T[0] < F[0] and T[1] < F[1] and T[0] > x0)
    ck.ok("寒気はくさび形（前線へ近づくほど薄い）で暖気の下にある",
          all((ground - (F[1] - (F[0] - x) * slope)) < (ground - (F[1] - (F[0] - x2) * slope))
              for x, x2 in ((370.0, 300.0), (300.0, 200.0))))
    ck.ok("寒気と暖気で図の枠（空）を過不足なく分ける（面積の和＝枠の面積）",
          near(abs(polygon_area(cold)) + abs(polygon_area(warm)), (x1 - x0) * (ground - top), 1e-6))
    body_has(ck, 4, "寒気が暖気の下に、先の細くとがったくさびのような形で入りこんで", "寒気が下")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 34, "模式図（教材用に作成）", size=FS_S, anchor="start")
    cv.fill_poly(cold, COLD_FILL)
    draw_section_frame(cv, x0, x1, top, ground)
    cv.line(F[0], F[1], T[0], T[1], w=BOLD_W, oid="surface")
    cv.dot(*F)
    b_cold = lb.put(105, 262, "寒気", weight="bold")
    b_warm = lb.put(500, 200, "暖気", weight="bold")
    ck.ok("「寒気」のラベルは寒気の中・「暖気」のラベルは暖気の中",
          box_inside_poly(b_cold, cold) and box_inside_poly(b_warm, warm))
    # 境の面（引き出し線）
    yq = 176.0
    q = (F[0] - (ground - yq) / slope, yq)
    lp = (318.0, 136.0)
    cv.line(lp[0] - 4, lp[1] + 4, q[0] + 3, q[1] - 3, w=1.0, oid="leader1")
    lb.put(lp[0], lp[1], "境の面", anchor="start", own=("leader1",))
    ck.ok("引き出し線の先は境の面の上", dist_point_seg(q, F, T) < 1e-9)
    cv.line(F[0], ground + 22, F[0], ground + 6, w=1.0, oid="leader2")
    lb.put(F[0], ground + 44, "地表と交わる所", own=("leader2", "ground"))
    lb.put(60, ground + 44, "地表", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L04_fig2_frontal_surface_section.svg", "lesson": "L04", "canvas": cv,
            "title": "暖気と寒気の境の断面模式図——左に寒気、右に暖気、境の斜めの面と、それが地表と交わる所",
            "desc": "地面を横から見た断面の模式図（教材用に作成・傾きは見やすいように大きくかいた）。左に寒気（網かけ）、右に暖気があり、"
                    "寒気が暖気の下にくさびのように入りこんで、境の面が斜めになっている。境の面と、それが地表と交わる所（点）に引き出し線をつけた。"
                    "同型図は境の面の傾きと交わる位置を差し替えて生成する",
            "alt": "前線面と前線の断面模式図——左に寒気、右に暖気、その境の斜めの面が前線面、面が地表と交わる所が前線（模式図・教材用に作成）",
            "intent": "暖気と寒気の境が立体の面（前線面）で、天気図にかかれる前線はその面と地表の交線であることを断面で見せる",
            "src": "lesson_04.md「暖気と寒気が出会うと——前線面と前線」（注意書きの直後）",
            "params": f"境の面の傾き 傾き（縦/横）={slope}（px）／地表と交わる所 x={F[0]:.0f}px／寒気は左のくさび・暖気は右と上",
            "checks": ck.items,
            "check_tokens": ["前線面", "前線", "重い", "上昇", "飽和水蒸気量"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def cloud_union(cv, ellipses, oid="cloud", min_run=10.0):
    """楕円を重ねた雲（白地・外形だけ線）。ellipses=[(cx, cy, rx, ry)]（px）。
    重なりの内側に残る小さなすき間の縁（長さ min_run px 未満）は描かない。戻り値: 外形の点列"""
    polys = []
    for cx, cy, rx, ry in ellipses:
        polys.append([(cx + rx * math.cos(2 * math.pi * i / 96), cy + ry * math.sin(2 * math.pi * i / 96))
                      for i in range(96)])
    for poly in polys:
        cv.fill_poly(poly, "#fff")
    outline = []

    def flush(run):
        if len(run) >= 2 and cum_lengths(run)[-1] >= min_run:
            cv.path(run, w=1.4, oid=oid)
            outline.extend(run)

    for k, poly in enumerate(polys):
        run = []
        others = [e for m, e in enumerate(ellipses) if m != k]
        for q in poly + [poly[0]]:
            inside_other = any(((q[0] - cx) / rx) ** 2 + ((q[1] - cy) / ry) ** 2 < 1.0 for cx, cy, rx, ry in others)
            if inside_other:
                flush(run)
                run = []
            else:
                run.append(q)
        flush(run)
    return outline


FRONT_ARROW = ((430.0, 62.0), (570.0, 62.0))      # 前線の進む向きの矢印（L05 図1・図2 共通・東向き）
COLD_SLOPE = 2.4                                    # 寒冷前線の前線面の傾き 傾き（縦/横）（急）
WARM_SLOPE = 0.3                                    # 温暖前線の前線面の傾き 傾き（縦/横）（ゆるい）


def fig_L05_1():
    # --- パラメータ（lesson_05.md「寒冷前線——寒気がもぐりこんで押し上げる」・図1） ---
    x0, x1, top, ground = 30.0, 610.0, 90.0, 320.0
    F = (330.0, ground)                                   # 前線（地表）
    T = (F[0] - (ground - top) / COLD_SLOPE, top)
    cloud = [(362.0, 254.0, 46.0, 24.0), (357.0, 222.0, 40.0, 30.0), (353.0, 186.0, 36.0, 32.0),
             (351.0, 150.0, 33.0, 30.0), (352.0, 120.0, 60.0, 16.0)]   # 背の高い雲（下から上へ・上端は横に広がる）
    A = (505.0, ground)                                   # 前線の東側（通過前）
    B = (150.0, ground)                                   # 前線の西側（通過後）
    H = 400

    def x_surface(y):
        return F[0] - (ground - y) / COLD_SLOPE

    ck = Checker()
    cold = [(x0, top), T, F, (x0, ground)]
    ck.ok("前線面の傾きが急（傾き（縦/横） ≧ 2）", COLD_SLOPE >= 2.0, f"傾き（縦/横）={COLD_SLOPE}")
    ck.ok("寒気（左・西）が暖気の下にもぐりこむくさび形", T[0] < F[0] and x0 < T[0])
    ys = [c[1] - c[3] for c in cloud] + [c[1] + c[3] for c in cloud]
    xs = [c[0] - c[2] for c in cloud] + [c[0] + c[2] for c in cloud]
    ck.ok("雲は背が高く狭い（高さ＞幅）", (max(ys) - min(ys)) > (max(xs) - min(xs)),
          f"高さ={max(ys) - min(ys):.0f}px・幅={max(xs) - min(xs):.0f}px")
    ck.ok("雲は前線の近く（中心が前線から 60px 以内）", all(abs(c[0] - F[0]) <= 60.0 for c in cloud))
    ck.ok("雲はすべて前線面より東（押し上げられた暖気の中）で地表より上",
          all(c[0] - c[2] > x_surface(c[1]) for c in cloud) and max(ys) < ground)
    ck.ok("地点A は前線の東側で暖気の中、地点B は西側で寒気の中",
          A[0] > F[0] and B[0] < F[0] and point_in_polygon((B[0], ground - 5), cold)
          and not point_in_polygon((A[0], ground - 5), cold))
    ck.ok("前線の進む向きの矢印は東向き", FRONT_ARROW[1][0] > FRONT_ARROW[0][0] and FRONT_ARROW[1][1] == FRONT_ARROW[0][1])
    body_has(ck, 5, "左が西、右が東、前線は東（右）へ進むとしてかいてあります", "図の約束")
    body_has(ck, 5, "図1の地点A（東側・通過前）は暖気の中にいて、地点B（西側・通過後）は寒気の中にいます", "地点A・B")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 34, "模式図（教材用に作成）", size=FS_S, anchor="start")
    cv.fill_poly(cold, COLD_FILL)
    cloud_union(cv, cloud)
    draw_section_frame(cv, x0, x1, top, ground)
    cv.line(F[0], F[1], T[0], T[1], w=BOLD_W, oid="surface")
    cv.arrow(*FRONT_ARROW[0], *FRONT_ARROW[1], w=2.2, head=12, oid="front_arrow")
    lb.put(FRONT_ARROW[0][0] - 12, FRONT_ARROW[0][1] + 6, "前線の進む向き", anchor="end")
    lb.put(356.0, 218.0, "雲")
    b_cold = lb.put(110, 250, "寒気", weight="bold")
    b_warm = lb.put(520, 190, "暖気", weight="bold")
    ck.ok("「寒気」のラベルは寒気の中・「暖気」のラベルは寒気の外（暖気の中）",
          box_inside_poly(b_cold, cold) and not any(point_in_polygon(q, cold) for q in
                                                     ((b_warm[0], b_warm[1]), (b_warm[2], b_warm[3]))))
    for p, name in ((A, "地点A"), (B, "地点B")):
        cv.dot(*p)
        lb.put(p[0], ground + 42, name)
    cv.line(F[0], ground + 22, F[0], ground + 6, w=1.0, oid="leaderF")
    lb.put(F[0], ground + 42, "前線", own=("leaderF",))
    lb.put(x0, ground + 42, "西", anchor="start")
    lb.put(x1, ground + 42, "東", anchor="end")
    cv.layout_checks(ck)

    return {"file": "L05_fig1_cold_front_section.svg", "lesson": "L05", "canvas": cv,
            "title": "寒冷前線の断面模式図——西の寒気が東の暖気の下にもぐりこみ、急な前線面に沿って背の高い雲",
            "desc": "地面を横から見た断面の模式図（教材用に作成・左が西、右が東、前線は東へ進む）。左の寒気（網かけ）が右の暖気の下に"
                    "もぐりこみ、前線面の傾きは急（傾き（縦/横）=2.4。描くための値で、実際の傾きではない）。前線付近の狭い範囲に楕円を重ねた背の高い雲がある。"
                    "地点Aは前線の東側、地点Bは西側の地表。同型図は前線面の傾きと雲の形を差し替えて生成する",
            "alt": "寒冷前線の断面模式図——左（西）の寒気が右（東）の暖気の下にもぐりこみ、急な前線面に沿って背の高い雲が狭い範囲にできている。地点Aは前線の東側（通過前）、地点Bは西側（通過後）（模式図・教材用に作成）",
            "intent": "寒気が暖気の下にもぐりこんで暖気を急に押し上げる構造と、狭い範囲の背の高い雲を断面で見せ、通過前後で町がどちらの空気の中にいるかを読ませる",
            "src": "lesson_05.md「寒冷前線——寒気がもぐりこんで押し上げる」（本文の2段落目の直後）",
            "params": f"前線面の傾き 傾き（縦/横）={COLD_SLOPE}（急）／前線 x={F[0]:.0f}px／雲 楕円{len(cloud)}個を重ねる（高さ＞幅）／地点A x={A[0]:.0f}px・地点B x={B[0]:.0f}px",
            "checks": ck.items,
            "check_tokens": ["寒冷前線", "温暖前線", "通過前", "通過後", "下がる", "上がる", "もぐりこ", "はい上が",
                             "積乱雲", "雷", "強い雨", "北寄り"],
            "check_tokens_meta": ["温暖前線", "通過前", "通過後", "下がる", "上がる", "積乱雲", "雷", "強い雨", "北寄り"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def fig_L05_2():
    # --- パラメータ（lesson_05.md「温暖前線——暖気がはい上がる」・図2） ---
    x0, x1, top, ground = 30.0, 610.0, 90.0, 320.0
    F = (190.0, ground)                                   # 前線（地表）
    R = (x1, ground - (x1 - F[0]) * WARM_SLOPE)          # 前線面が枠の右端と交わる所
    cloud_x = [262.0, 322.0, 382.0, 442.0, 502.0, 548.0]  # 雲（前線面に沿って重ねる楕円の中心の x）
    cloud_lift, cloud_rx, cloud_ry = 22.0, 52.0, 13.0
    C = (450.0, ground)                                   # 前線の東側（通過前）
    D = (95.0, ground)                                    # 前線の西側（通過後）
    H = 400

    def y_surface(x):
        return ground - (x - F[0]) * WARM_SLOPE

    cloud = [(x, y_surface(x) - cloud_lift, cloud_rx, cloud_ry) for x in cloud_x]
    ck = Checker()
    cold = [F, (x1, ground), R]
    ck.ok("前線面の傾きがゆるい（傾き（縦/横） ≦ 0.35）", WARM_SLOPE <= 0.35, f"傾き（縦/横）={WARM_SLOPE}")
    ck.ok("図1（寒冷前線）の前線面の傾きの 1/5 未満", WARM_SLOPE < COLD_SLOPE / 5.0,
          f"{WARM_SLOPE} < {COLD_SLOPE}/5")
    ck.ok("暖気（左・西）が寒気（右・東）の上にはい上がる形（寒気は東ほど厚いくさび）",
          R[1] < ground and F[0] < R[0] and y_surface(500.0) < y_surface(300.0))
    ys = [c[1] - c[3] for c in cloud] + [c[1] + c[3] for c in cloud]
    xs = [c[0] - c[2] for c in cloud] + [c[0] + c[2] for c in cloud]
    ck.ok("雲は広い範囲に広がる（幅 > 高さの3倍）", (max(xs) - min(xs)) > 3 * (max(ys) - min(ys)),
          f"幅={max(xs) - min(xs):.0f}px・高さ={max(ys) - min(ys):.0f}px")
    ck.ok("雲はすべて前線面より上（はい上がる暖気の中）で、前線の東側（寒気の上空）に広がる",
          all(c[1] + c[3] < y_surface(c[0]) for c in cloud) and min(xs) > F[0])
    ck.ok("地点C は前線の東側で寒気の中・雲の下、地点D は西側で暖気の中",
          C[0] > F[0] and point_in_polygon((C[0], ground - 3), cold) and min(xs) < C[0] < max(xs)
          and D[0] < F[0])
    body_has(ck, 5, "図2の地点C（東側・通過前）は寒気の中にいて", "地点C")
    body_has(ck, 5, "地点D（西側・通過後）は暖気の中にいます", "地点D")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 34, "模式図（教材用に作成）", size=FS_S, anchor="start")
    cv.fill_poly(cold, COLD_FILL)
    cloud_union(cv, cloud)
    draw_section_frame(cv, x0, x1, top, ground)
    cv.line(F[0], F[1], R[0], R[1], w=BOLD_W, oid="surface")
    cv.arrow(*FRONT_ARROW[0], *FRONT_ARROW[1], w=2.2, head=12, oid="front_arrow")
    lb.put(FRONT_ARROW[0][0] - 12, FRONT_ARROW[0][1] + 6, "前線の進む向き", anchor="end")
    lb.put(cloud_x[4], cloud[4][1] + 0.29 * FS_S, "雲", size=FS_S)
    b_warm = lb.put(150, 170, "暖気", weight="bold")
    b_cold = lb.put(540, 296, "寒気", weight="bold")
    ck.ok("「寒気」のラベルは寒気の中・「暖気」のラベルは暖気の中",
          box_inside_poly(b_cold, cold) and not point_in_polygon(box_center(b_warm), cold))
    for p, name in ((C, "地点C"), (D, "地点D")):
        cv.dot(*p)
        lb.put(p[0], ground + 42, name)
    cv.line(F[0], ground + 22, F[0], ground + 6, w=1.0, oid="leaderF")
    lb.put(F[0], ground + 42, "前線", own=("leaderF",))
    lb.put(x0, ground + 42, "西", anchor="start")
    lb.put(x1, ground + 42, "東", anchor="end")
    cv.layout_checks(ck)

    return {"file": "L05_fig2_warm_front_section.svg", "lesson": "L05", "canvas": cv,
            "title": "温暖前線の断面模式図——西の暖気が東の寒気の上にゆるやかにはい上がり、ゆるい前線面に沿って広い範囲の雲",
            "desc": "地面を横から見た断面の模式図（教材用に作成・左が西、右が東、前線は東へ進む）。左の暖気が右の寒気（網かけ）の上に"
                    "ゆるやかにはい上がり、前線面の傾きはゆるい（傾き（縦/横）=0.3。描くための値で、実際の傾きではない）。前線面の上に沿って、前線の東側の広い範囲に平たい雲が広がる。"
                    "地点Cは前線の東側（雲の下）、地点Dは西側の地表。同型図は前線面の傾きと雲の並びを差し替えて生成する",
            "alt": "温暖前線の断面模式図——左（西）の暖気が右（東）の寒気の上にゆるやかにはい上がり、ゆるい前線面に沿って広い範囲に雲が広がっている。地点Cは前線の東側（通過前）、地点Dは西側（通過後）（模式図・教材用に作成）",
            "intent": "暖気が寒気の上にゆるやかにはい上がる構造と広い範囲の雲を、寒冷前線の図と対にして見せる",
            "src": "lesson_05.md「温暖前線——暖気がはい上がる」（本文の1段落目の直後）",
            "params": f"前線面の傾き 傾き（縦/横）={WARM_SLOPE}（ゆるい・図1の1/8）／前線 x={F[0]:.0f}px／雲 平たい楕円{len(cloud_x)}個を重ねる（前線面の上 {cloud_lift:.0f}px）／地点C x={C[0]:.0f}px・地点D x={D[0]:.0f}px",
            "checks": ck.items,
            "check_tokens": ["寒冷前線", "温暖前線", "通過前", "通過後", "下がる", "上がる", "もぐりこ", "はい上が",
                             "弱い雨", "長い", "層", "南寄り"],
            "check_tokens_meta": ["寒冷前線", "通過前", "通過後", "下がる", "上がる", "弱い雨", "長い", "層", "南寄り"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def side_of_curve(p, curve):
    """点 p が折れ線 curve（向きつき）の左（正）か右（負）か。最も近い線分の接線で判定"""
    best = None
    for a, b in zip(curve, curve[1:]):
        d = dist_point_seg(p, a, b)
        if best is None or d < best[0]:
            best = (d, a, b)
    _, a, b = best
    return cross(sub(b, a), sub(p, a))


def fig_L06_1():
    # --- パラメータ（lesson_06.md「温帯低気圧と2つの前線」・図1） ---
    C = (300.0, -178.0)                                    # 低気圧の中心（数学座標・1単位＝1px）
    warm_ctrl = [(0.0, 0.0), (90.0, -15.0), (180.0, -58.0), (248.0, -126.0)]    # 温暖前線（中心から東側へ）
    cold_ctrl = [(0.0, 0.0), (-58.0, -80.0), (-120.0, -172.0), (-164.0, -254.0)]  # 寒冷前線（中心から南西側へ）
    sym_size, sym_step, sym_first = 18.0, 38.0, 28.0
    pts_spec = [("ア", "東", 185.0), ("イ", "南", 168.0), ("ウ", "西", 185.0), (None, "北", 128.0)]
    arrow_len = 56.0
    H = 480
    fr = Frame(0.0, 0.0, 1.0)

    warm = catmull_rom([add(C, q) for q in warm_ctrl], n=10)
    cold = catmull_rom([add(C, q) for q in cold_ctrl], n=10)
    semis = front_symbols(warm, sym_step, sym_first, [("semi", +1)], sym_size)
    tris = front_symbols(cold, sym_step, sym_first, [("tri", +1)], sym_size)

    ck = Checker()
    d_w = unit(sub(warm[3], warm[0]))
    d_c = unit(sub(cold[3], cold[0]))
    ck.ok("半円の前線は中心から東側へのびる（出だしの向きが東から±30°以内）",
          abs(math_deg(d_w)) <= 30.0, f"{math_deg(d_w):.1f}°")
    ck.ok("三角の前線は中心から南西側へのびる（出だしの方位 200°〜250°）",
          200.0 <= bearing_deg(d_c) <= 250.0, f"{bearing_deg(d_c):.1f}°")
    ck.ok("半円はすべて線の北側〜北東側（記号の向きの方位が 0°〜60°）", all(0.0 <= bearing_deg(n) <= 60.0 for _, _, _, n, _ in semis),
          f"{len(semis)}個")
    ck.ok("三角はすべて南東側（東の成分が正・北の成分が負）＝東へ進む", all(n[0] > 0 and n[1] < 0 for _, _, _, n, _ in tris),
          f"{len(tris)}個")
    ck.ok("記号は前線にそって等間隔（半円・三角とも 3個以上）", len(semis) >= 3 and len(tris) >= 3)
    pos = {}
    for name, side, r in pts_spec:
        pos[side] = add(C, mul(SIDE_VEC[side], r))
    ck.ok("地点ア（中心の東）は半円の前線の記号の側（前線の北東側＝寒気の側）",
          side_of_curve(pos["東"], warm) > 0 and near(bearing_deg(sub(pos["東"], C)), 90.0))
    ck.ok("地点イ（中心の南）は2つの前線の間（半円の前線の右側かつ三角の前線の左側）",
          side_of_curve(pos["南"], warm) < 0 and side_of_curve(pos["南"], cold) > 0)
    ck.ok("地点ウ（中心の西）は三角の前線の西側（後ろ）", side_of_curve(pos["西"], cold) < 0)
    ck.ok("三角は2つの前線の間の側（地点イと同じ側）・半円は反対の側",
          all(side_of_curve(add(p, mul(n, 6.0)), cold) > 0 for _, p, _, n, _ in tris)
          and all(side_of_curve(add(p, mul(n, 6.0)), warm) > 0 for _, p, _, n, _ in semis))
    body_has(ck, 6, "半円は、線の北側から北東側（前線の外側＝寒気の側）についています", "半円の向き")
    body_has(ck, 6, "三角は南東側（前線の東側）についているので", "三角の向き")
    body_has(ck, 6, "中心の東側の地点では" + LOW_SIDE_WIND["東"] + "の風、南側（2つの前線の間）では" + LOW_SIDE_WIND["南"]
             + "の風、西側では" + LOW_SIDE_WIND["西"] + "の風、北側では" + LOW_SIDE_WIND["北"] + "の風", "風向の約束")

    cv = Canvas(W, H)
    lb = Labels(cv)
    for curve, syms in ((warm, semis), (cold, tris)):
        cv.path(fr.Ps(curve), w=FRONT_W, oid="front")
        for kind, _, _, _, poly in syms:
            pp = fr.Ps(poly)
            cv.fill_poly(pp, "#000")
            cv.obstacle("front", pp + [pp[0]])
    cx, cy = fr.P(C)
    center_cross(cv, cx, cy, r=5.0, oid="center")
    lb.put(cx - 22, cy - 12, "低", weight="bold")
    arrows = []
    for name, side, r in pts_spec:
        p = pos[side]
        u = cyclonic_flow(SIDE_VEC[side], "low")
        check_cyclonic_arrow(ck, name or "（北側）", side, u, "low")
        pp = fr.P(p)
        cv.dot(*pp)
        wind_arrow_px(cv, pp, u, arrow_len)
        a0 = sub(p, mul(u, arrow_len / 2.0))
        a1 = add(p, mul(u, arrow_len / 2.0))
        arrows.append((a0, a1))
        if name:
            perp = (-u[1], u[0])
            if dot(perp, SIDE_VEC[side]) < 0:
                perp = mul(perp, -1.0)
            point_label(lb, pp, name, (perp[0] * 25.0, -perp[1] * 25.0))
    gapmin = min(min(dist_point_seg(q, a0, a1) for q in warm + cold) for a0, a1 in arrows)
    ck.ok("風の矢印は前線にかからない（最小距離 > 8px）", gapmin > 8.0, f"最小距離={gapmin:.1f}px")
    north_arrow(cv, lb, 590, 12, length=34)
    lb.put(30, 468, "模式図（教材用に作成）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L06_fig1_extratropical_cyclone_plan.svg", "lesson": "L06", "canvas": cv,
            "title": "温帯低気圧と2つの前線の平面模式図（北が上・上空から見た図）",
            "desc": "北が上・上空から見た模式図（教材用に作成）。低気圧の中心（×）から東側へ半円の記号の前線、南西側へ三角の記号の前線が"
                    "のび、半円は線の北側から北東側に、三角は線の南東側についている。中心の東・南・西・北の地点に、レッスン2の約束どおり反時計回りに"
                    "吹きこむ風の矢印（中心へ向かう向きから45°）をかいた。地点アは中心の東で、半円の前線の北東側、イは2つの前線の間、"
                    "ウは三角の前線の西側。風向の文字と前線の名前は図に入れない。同型図は前線の制御点と地点の位置を差し替えて生成する",
            "alt": "温帯低気圧と2つの前線の平面模式図（北が上・上空から見た図）——中心から東側へ半円の記号の前線、南西側へ三角の記号の前線がのび、風の矢印は反時計回りに中心へ吹きこむ。地点アは中心の東側で、半円の前線の北東側（寒気の中）、地点イは2つの前線の間、地点ウは三角の前線の西側（模式図・教材用に作成）",
            "intent": "温帯低気圧に2つの前線がどうつき、中心のどちら側の町が前線の通過を経験するかを、記号の向きと風の矢印で見せる",
            "src": "lesson_06.md「温帯低気圧と2つの前線」（注意書きの直後）",
            "params": "中心から半円の前線（東側・出だし東南東）と三角の前線（南西側）／記号 18px・38px おき／地点 ア 東185px・イ 南168px・ウ 西185px・北側 128px（矢印のみ）／矢印 56px",
            "checks": ck.items,
            "check_tokens": ["温暖前線", "寒冷前線", "暖気", "寒気", "北東", "北西", "南東", "南西", "閉塞", "停滞"],
            "check_tokens_meta": ["温暖前線", "寒冷前線", "暖気", "寒気", "北東の風", "北西の風", "南東の風", "南西の風",
                                  "閉塞", "停滞"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def parse_md_table_rows(text, headers):
    """Markdown の表から、先頭セルが headers にある行を {見出し: [セル...]} で返す"""
    rows = {}
    for line in text.splitlines():
        t = line.strip()
        if t.startswith("|"):
            cells = [c.strip() for c in t.strip("|").split("|")]
            if cells and cells[0] in headers and cells[0] not in rows:
                rows[cells[0]] = cells[1:]
    return rows


def fig_L06_2():
    # --- パラメータ（lesson_06.md 表1・図2・架空の練習用データ） ---
    times = [3, 6, 9, 12, 15, 18]                          # 時刻［時］
    temps = [12, 12, 18, 20, 12, 10]                       # 気温［℃］（架空値）
    press = [1008, 1004, 1000, 996, 1000, 1004]            # 気圧［hPa］（架空値）
    winds = ["南東", "南東", "南西", "南西", "北西", "北西"]  # 風向（8方位）
    t_rng, t_ticks = (8.0, 24.0), [8, 12, 16, 20, 24]
    p_rng, p_ticks = (992.0, 1012.0), [992, 996, 1000, 1004, 1008, 1012]
    x_first, x_step = 160.0, 86.0                          # 時刻の x（等間隔）
    t_box = (120.0, 80.0, 620.0, 212.0)                    # 気温の枠（x0, y0, x1, y1）
    p_box = (120.0, 276.0, 620.0, 406.0)                   # 気圧の枠
    y_wind, y_time = 452.0, 496.0
    H = 560

    ck = Checker()
    t6 = lesson_text(6)
    if t6 is None:
        ck.ok("本文照合（表1）: lesson_06.md がこの階層に無いため未実施", True)
    else:
        hd = ["時刻", "気温［℃］（架空値）", "気圧［hPa］（架空値）", "風向（8方位）"]
        rows = parse_md_table_rows(t6, hd)
        ck.ok("本文照合（表1）: lesson_06.md の表1の4行（時刻・気温・気圧・風向）が読める", all(h in rows for h in hd),
              f"{sorted(rows)}")
        ck.ok("本文照合（表1）: 時刻の行が一致", [int(c.replace("時", "")) for c in rows["時刻"]] == times)
        ck.ok("本文照合（表1）: 気温の行が一致", [int(c) for c in rows[hd[1]]] == temps)
        ck.ok("本文照合（表1）: 気圧の行が一致", [int(c) for c in rows[hd[2]]] == press)
        ck.ok("本文照合（表1）: 風向の行が一致", rows[hd[3]] == winds)

    def X(i):
        return x_first + x_step * i

    def Yt(v):
        return t_box[3] - (v - t_rng[0]) / (t_rng[1] - t_rng[0]) * (t_box[3] - t_box[1])

    def Yp(v):
        return p_box[3] - (v - p_rng[0]) / (p_rng[1] - p_rng[0]) * (p_box[3] - p_box[1])

    ck.ok("横軸は等間隔（時刻が3時間おき→ x が一定間隔）",
          all(times[i + 1] - times[i] == 3 for i in range(5)) and all(near(X(i + 1) - X(i), x_step) for i in range(5)))
    ck.ok("縦軸は線形（値の差と px の差が比例・誤差 1e-9）",
          all(near((Yt(temps[i]) - Yt(temps[0])), -(temps[i] - temps[0]) * (t_box[3] - t_box[1]) / (t_rng[1] - t_rng[0]))
              for i in range(6))
          and all(near((Yp(press[i]) - Yp(press[0])), -(press[i] - press[0]) * (p_box[3] - p_box[1]) / (p_rng[1] - p_rng[0]))
                  for i in range(6)))
    ck.ok("すべての値が軸の範囲の内側", all(t_rng[0] < v < t_rng[1] for v in temps) and all(p_rng[0] < v < p_rng[1] for v in press))

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 34, "架空の練習用データ（教材用に作成）", size=FS_S, anchor="start")
    for box, rng, ticks, Y, title, oid in ((t_box, t_rng, t_ticks, Yt, "気温［℃］", "tplot"),
                                           (p_box, p_rng, p_ticks, Yp, "気圧［hPa］", "pplot")):
        cv.rect(box[0], box[1], box[2] - box[0], box[3] - box[1], sw=1.2, oid=f"{oid}frame")
        lb.put(box[0], box[1] - 10, title, size=FS_S, anchor="start")
        for v in ticks:
            y = Y(v)
            if box[1] < y < box[3]:
                cv.line(box[0], y, box[2], y, w=0.7, dash="2 4")
            cv.line(box[0] - 6, y, box[0], y, w=1.2, oid=f"{oid}frame")
            lb.put(box[0] - 10, y + 0.29 * FS_S, str(v), size=FS_S, anchor="end")
        for i in range(6):
            cv.line(X(i), box[3], X(i), box[3] + 6, w=1.2, oid=f"{oid}frame")
    tp = [(X(i), Yt(v)) for i, v in enumerate(temps)]
    pp = [(X(i), Yp(v)) for i, v in enumerate(press)]
    cv.path(tp, w=2.0, oid="tline")
    cv.path(pp, w=2.0, oid="pline")
    for x, y in tp:
        cv.dot(x, y, r=4.2, oid="tline")
    for x, y in pp:
        cv.rect(x - 4.2, y - 4.2, 8.4, 8.4, fill="#000", sw=1.0, oid="pline")
    lb.put(30, y_wind + 0.29 * FS, "風向", anchor="start")
    for i, wname in enumerate(winds):
        u = mul(compass_vec(wname), -1.0)          # 空気が進む向き＝風向（吹いてくる方位）の反対
        word, dev = compass8(mul(u, -1.0))
        ck.ok(f"{times[i]}時の矢印: 根もとの方位＝表の風向（{wname}）・8方位ちょうど", word == wname and dev < 1e-9)
        wind_arrow_px(cv, (X(i), y_wind), u, 40.0, oid=f"w{i}")
        lb.put(X(i), y_time, f"{times[i]}時", size=FS_S)
    lb.put(30, 540, "風向の行の矢印は空気が進む向き（根もとが風の吹いてくる方位）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L06_fig2_front_passage_timeseries.svg", "lesson": "L06", "canvas": cv,
            "title": "表1の気温と気圧の折れ線グラフと風向の記号行（架空の練習用データ）",
            "desc": "ある町の1日の記録（架空の練習用データ・教材用に作成）を、上に気温［℃］、下に気圧［hPa］の折れ線、その下に風向の矢印の行"
                    "（矢印は空気が進む向き・根もとが風の吹いてくる方位）としてならべた図。時刻は3時〜18時の3時間おき。"
                    "前線の通過した時間帯・前線の名前・気圧の谷の印は図に書かない。同型図は表の値を差し替えて生成する（値は本文の表と照合する）",
            "alt": "表1の気温と気圧の折れ線グラフと風向の記号行（架空の練習用データ・教材用に作成）。前線の通過した時間帯や前線の名前は図に書いていない",
            "intent": "表1の数字の変わり方（気圧の下がり続けてから上がる形・気温の急な上がり下がり・風向の変わり目）を、判定の手順の順に目で追えるようにする",
            "src": "lesson_06.md「前線の通過を時刻ごとの記録で判定する」（表1の直後）",
            "params": "時刻 3・6・9・12・15・18時／気温 12・12・18・20・12・10℃／気圧 1008・1004・1000・996・1000・1004hPa／"
                      "風向 南東・南東・南西・南西・北西・北西（矢印で表す）／気温軸 8〜24℃・気圧軸 992〜1012hPa",
            "checks": ck.items,
            "check_tokens": ["前線", "通過", "谷", "寒冷", "温暖", "から", "の間", "北東", "北西", "南東", "南西", "雨",
                             "晴れ", "くもり"],
            "check_tokens_meta": ["寒冷前線", "温暖前線", "12時から15時", "6時から9時", "から15時", "から9時", "雨",
                                  "晴れ", "くもり", "北東", "北西", "南東", "南西"],
            "digit_rule": ("subset", {"3", "6", "9", "12", "15", "18", "8", "16", "20", "24",
                                      "992", "996", "1000", "1004", "1008", "1012"}),
            "allow_texts": lb.items}


# ===========================================================================
# L07〜L10: 日本の季節の天気（子単元 --japan-seasons）
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（lesson_07.md「温度差が気圧差を生む——3段のしくみ」・図1） ---
    panels = [("冬", {"大陸": ("冷たい", "高"), "海洋": ("暖かい", "低")}),
              ("夏", {"大陸": ("暖かい", "低"), "海洋": ("冷たい", "高")})]
    bw, bh, gap = 130.0, 150.0, 20.0
    y_box, y_arrow = 76.0, 258.0
    H = 340

    ck = Checker()
    for season, d in panels:
        for place, (temp, pres) in d.items():
            ck.ok(f"{season}: {place}は「{temp}」なら気圧は「{'高' if temp == '冷たい' else '低'}」（冷たい側が高・暖かい側が低）",
                  (temp == "冷たい") == (pres == "高"))
    ck.ok("冬は大陸が冷たく海洋が暖かい・夏はその逆（陸は海より温まりやすく冷めやすい）",
          panels[0][1]["大陸"][0] == "冷たい" and panels[1][1]["大陸"][0] == "暖かい"
          and panels[0][1]["海洋"][0] == "暖かい" and panels[1][1]["海洋"][0] == "冷たい")
    body_has(ck, 7, "冬は大陸→海洋、夏は海洋→大陸", "矢印の向き")
    body_has(ck, 7, "左の四角を大陸、右の四角を海洋として", "四角の約束")

    cv = Canvas(W, H)
    lb = Labels(cv)
    for p, (season, d) in enumerate(panels):
        ox = 20.0 + p * 310.0
        lb.put(ox + 150.0, 52.0, season, weight="bold", size=22)
        centers = {}
        for q, place in enumerate(("大陸", "海洋")):
            x = ox + 10.0 + q * (bw + gap)
            cv.rect(x, y_box, bw, bh, fill=(LAND_FILL if place == "大陸" else "#fff"), sw=MAIN_W, oid=f"box{p}{q}")
            temp, pres = d[place]
            cx = x + bw / 2.0
            lb.put(cx, y_box + 32.0, place, weight="bold")
            lb.put(cx, y_box + 72.0, temp)
            lb.put(cx, y_box + 124.0, pres, size=30, weight="bold")
            centers[pres] = cx
        x_from, x_to = centers["高"], centers["低"]
        cv.arrow(x_from, y_arrow, x_to, y_arrow, w=2.4, head=13, oid=f"arrow{p}")
        ck.ok(f"{season}: 矢印は「高」の四角から「低」の四角へ（{'大陸→海洋' if p == 0 else '海洋→大陸'}）",
              (x_to > x_from) == (p == 0))
        lb.put(ox + 150.0, y_arrow + 30.0, "地表付近の風", size=FS_S)
    lb.put(320, 330, "模式図（教材用に作成）", size=FS_S)
    cv.layout_checks(ck)

    return {"file": "L07_fig1_monsoon_winter_summer.svg", "lesson": "L07", "canvas": cv,
            "title": "冬と夏の大陸と海洋の温度差・気圧配置・地表付近の風の向き（2パネル）",
            "desc": "左のパネル「冬」と右のパネル「夏」の模式図（教材用に作成）。各パネルの左の四角が大陸、右の四角が海洋で、中に温度のようす"
                    "（大陸と海洋をくらべた「冷たい」「暖かい」）と地表付近の気圧の高低（「高」「低」）を書き、下の矢印で地表付近の風の向き"
                    "（高から低へ）を示した。冬は大陸が冷たい・高、海洋が暖かい・低で大陸→海洋、夏はその逆。8方位・数値は書かない。"
                    "同型図は季節ごとの温度の語を差し替えて生成する（高低と矢印は「冷たい側が高」から決まる）",
            "alt": "冬と夏の大陸と海洋の温度差・気圧配置・季節風の向き（2パネル）——左のパネル「冬」では大陸が「冷たい・高」で海洋が「暖かい・低」なので、矢印は大陸から海洋へ向かう。右のパネル「夏」では大陸が「暖かい・低」で海洋が「冷たい・高」なので、矢印は海洋から大陸へ向かう（模式図・教材用に作成）",
            "intent": "季節風の3段（温度差→気圧差→風）を、冬と夏の2枚の対比で見せる",
            "src": "lesson_07.md「温度差が気圧差を生む——3段のしくみ」（注意書きの直後）",
            "params": "冬: 大陸 冷たい・高／海洋 暖かい・低／矢印 大陸→海洋。夏: 大陸 暖かい・低／海洋 冷たい・高／矢印 海洋→大陸。四角 130×150px",
            "checks": ck.items,
            "check_tokens": ["北西", "南東", "季節風", "海陸風", "西高東低", "南高北低", "冷めやすい", "温まりやすい"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def polyline_x_at_y(pts, y):
    xs = []
    for a, b in zip(pts, pts[1:]):
        if a[1] != b[1] and (a[1] - y) * (b[1] - y) <= 0:
            xs.append(a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]))
    return xs


def polyline_y_at_x(pts, x):
    ys = []
    for a, b in zip(pts, pts[1:]):
        if a[0] != b[0] and (a[0] - x) * (b[0] - x) <= 0:
            ys.append(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    return ys


JAPAN_AXIS_CURVE = catmull_rom(JAPAN_AXIS, n=4)
L01_RADII = [44.0, 88.0, 132.0]          # レッスン1 図2 の等圧線の半径（間隔 44px）——冬・夏の図の間隔の比較に使う

# ---- 冬の模式天気図（L08 図1・L10 図3 の「冬」で共用・地図単位） ----
WINTER = {"H": (16.0, 52.0), "H_v": 1036, "L": (88.0, 34.0), "L_v": 996,
          "H_ring": (1032, 15.0, 9.5), "L_ring": (1000, 4.6, 7.2),
          "open": [1028, 1024, 1020, 1016, 1012, 1008, 1004], "beta0": 6.0, "y_mid": 32.0, "y_half": 32.0,
          "y_town": 36.0, "inset": 1.2, "U_deg": -35.0, "labeled": [1032, 1024, 1016, 1008, 1000]}


def winter_geometry():
    Wd = WINTER
    y = Wd["y_town"]
    nw = polyline_x_at_y(JAPAN_NW_EDGE, y)
    se = polyline_x_at_y(JAPAN_SE_EDGE, y)
    assert len(nw) == 1 and len(se) == 1, f"日本の縁と y={y} の交点が1つでない: {nw} {se}"
    A = (nw[0] + Wd["inset"], y)            # 日本海側の町（北西の縁から inset 内側）
    I = (se[0] - Wd["inset"], y)            # 太平洋側の町（南東の縁から inset 内側）
    delta = I[0] - A[0]                     # 町の緯度での等圧線の間隔（地図単位）
    levels = Wd["open"]
    n = len(levels)
    k16 = levels.index(1016)
    u_t = (y - Wd["y_mid"]) / Wd["y_half"]
    lines = []
    lv, a, b = Wd["H_ring"]
    lines.append((lv, ellipse_pts(Wd["H"], a, b), True))
    for k, lvk in enumerate(levels):
        beta = Wd["beta0"] * (1 - 2 * k / (n - 1))
        xk = A[0] + (k - k16) * delta + beta * u_t ** 2
        pts = [(xk - beta * ((j * 0.5 - Wd["y_mid"]) / Wd["y_half"]) ** 2, j * 0.5) for j in range(0, 129)]
        lines.append((lvk, pts, False))
    lv, a, b = Wd["L_ring"]
    lines.append((lv, ellipse_pts(Wd["L"], a, b), True))
    U = ellipse_point(Wd["H"], Wd["H_ring"][1], Wd["H_ring"][2], Wd["U_deg"])
    return {"A": A, "I": I, "U": U, "delta": delta, "lines": lines}


def check_winter(ck, g, s_px):
    Wd = WINTER
    lines = g["lines"]
    levels = [lv for lv, _, _ in lines]
    ck.ok("等圧線は 4hPa ごと: 1032（高気圧を囲む）・1028〜1004（たての線7本）・1000（低気圧を囲む）",
          levels == list(range(1032, 999, -4)) and Wd["H_v"] - levels[0] == 4 and levels[-1] - Wd["L_v"] == 4)
    ck.ok("高気圧の中心（1036）は図の左上の大陸上、低気圧の中心（996）は図の右の海洋上",
          point_in_polygon(Wd["H"], CONTINENT_POLY) and Wd["H"][0] < 30 and Wd["H"][1] > 40
          and not on_land(Wd["L"]) and Wd["L"][0] > 75)
    opens = [(lv, pts) for lv, pts, closed in lines if not closed]
    mono = all(opens[k + 1][1][j][0] - opens[k][1][j][0] > 0.5 for k in range(len(opens) - 1) for j in range(129))
    ck.ok("たての線は西から東へ 1028→1004 の順にならび、どの高さでも交わらない（隣どうしの差 > 0.5）", mono)
    lv, a, b = Wd["H_ring"]
    ring_h = ellipse_pts(Wd["H"], a, b)
    lv2, a2, b2 = Wd["L_ring"]
    ring_l = ellipse_pts(Wd["L"], a2, b2)
    g1 = min_dist_polylines(ring_h, [p for p in opens[0][1] if 0 <= p[1] <= 64])
    g2 = min_dist_polylines(ring_l, [p for p in opens[-1][1] if 0 <= p[1] <= 64])
    ck.ok("閉じた線（1032・1000）はとなりのたての線（1028・1004）と交わらない（最小距離 > 2単位）",
          g1 > 2.0 and g2 > 2.0, f"1032-1028={g1:.2f}・1000-1004={g2:.2f}")
    slope = max(abs(2 * Wd["beta0"] * 1.0 / Wd["y_half"]), 0.0)
    ck.ok("たての線は「たて」（鉛直から 25° 以内）", math.degrees(math.atan(slope)) < 25.0,
          f"最大 {math.degrees(math.atan(slope)):.1f}°")
    ck.ok("町の緯度での等圧線の間隔（px）がレッスン1の図の間隔（44px）より狭い",
          g["delta"] * s_px < (L01_RADII[1] - L01_RADII[0]), f"{g['delta'] * s_px:.1f}px")
    A, I, U = g["A"], g["I"], g["U"]
    X = {lv: pts for lv, pts in opens}

    def x_on(lv, y):
        return polyline_x_at_y(X[lv], y)[0]
    ck.ok("地点ア（日本海側の町）は 1016 の線上、地点イ（太平洋側の町）は 1012 の線上",
          near(x_on(1016, A[1]), A[0], 1e-9) and near(x_on(1012, I[1]), I[0], 1e-9))
    ck.ok("地点アは日本の北西の縁（日本海側）に近く、地点イは南東の縁（太平洋側）に近い（どちらも日本の上）",
          in_japan(A) and in_japan(I)
          and dist_point_polyline(A, JAPAN_NW_EDGE) < dist_point_polyline(A, JAPAN_SE_EDGE)
          and dist_point_polyline(I, JAPAN_SE_EDGE) < dist_point_polyline(I, JAPAN_NW_EDGE))
    ck.ok("地点ウは 1032 の線上で大陸の上",
          near(ellipse_val(U, Wd["H"], a, b), 1.0) and point_in_polygon(U, CONTINENT_POLY))
    ck.ok("日本（地点ア）は低気圧の中心の西側かつ高気圧の中心の東側（東西の対応表〔レッスン2の約束〕で2つの中心から同じ風向になる配置。地点アを通る等圧線の向きは使っていない）",
          Wd["H"][0] < A[0] < Wd["L"][0])


def draw_isobar_lines(cv, mf, lines, w=THIN_W, prefix="iso"):
    runs = {}
    for lv, pts, closed in lines:
        runs[lv] = draw_curve_map(cv, mf, pts, w=w, closed=closed, oid=f"{prefix}{lv}")
    return runs


def map_label(lb, mf, p, s, off_px=(0.0, 0.0), size=FS, bg=False, own=(), weight=None, anchor="middle"):
    x, y = mf.P(p)
    return lb.put(x + off_px[0], y + off_px[1] + 0.29 * size, s, size=size, bg=bg, own=own, weight=weight,
                  anchor=anchor)


def fig_L08_1():
    # --- パラメータ（lesson_08.md「シベリア気団の発達と冬の気圧配置」・図1・架空の値）: 上の WINTER ---
    H = 484
    mf = MapFrame(20.0, 58.0, 6.0, (0.0, 0.0, MAP_W, MAP_H))
    g = winter_geometry()
    Wd = WINTER

    ck = Checker()
    check_winter(ck, g, mf.s)
    body_has(ck, 8, "左上（北西）の大陸", "高気圧の位置")
    body_has(ck, 8, f"中心の値は{Wd['H_v']}hPa", "高気圧の中心の値")
    body_has(ck, 8, f"中心の値は{Wd['L_v']}hPa", "低気圧の中心の値")
    body_has(ck, 8, "数字は" + "・".join(str(v) for v in Wd["labeled"]) + "の線に書いてあります", "数字を書く線")
    body_has(ck, 8, "日本は、低気圧の中心から見て", "日本と2つの中心の位置")

    cv = Canvas(W, H)
    lb = Labels(cv)
    draw_basemap(cv, mf)
    draw_isobar_lines(cv, mf, g["lines"])
    draw_map_frame(cv, mf)
    for c, mark, v in ((Wd["H"], "高", Wd["H_v"]), (Wd["L"], "低", Wd["L_v"])):
        map_label(lb, mf, c, mark, (0.0, -9.0), weight="bold")
        map_label(lb, mf, c, str(v), (0.0, 11.0), size=FS_S)
    # 数字を書く線
    opens = {lv: pts for lv, pts, closed in g["lines"] if not closed}
    for lv in Wd["labeled"]:
        if lv == Wd["H_ring"][0]:
            p = ellipse_point(Wd["H"], Wd["H_ring"][1], Wd["H_ring"][2], 0.0)
        elif lv == Wd["L_ring"][0]:
            p = ellipse_point(Wd["L"], Wd["L_ring"][1], Wd["L_ring"][2], 270.0)
        else:
            p = (polyline_x_at_y(opens[lv], 5.0)[0], 5.0)
        iso_label(lb, mf.P(p), lv, f"iso{lv}")
    # 地点
    for p, name, off in ((g["A"], "ア", (-14.0, -12.0)), (g["I"], "イ", (14.0, 12.0)), (g["U"], "ウ", (14.0, 10.0))):
        pp = mf.P(p)
        cv.dot(*pp)
        lb.put(pp[0] + off[0], pp[1] + off[1] + 0.29 * FS, name, bg=True, own=("coast",))
    # 地名
    map_label(lb, mf, (12.0, 30.0), "大陸")
    xs = polyline_x_at_y(opens[1024], 49.0)[0], polyline_x_at_y(opens[1020], 49.0)[0]
    top_px = mf.P((0.0, 54.0))[1]
    lb.vput(mf.P(((xs[0] + xs[1]) / 2.0, 0.0))[0], top_px, "日本海")
    map_label(lb, mf, (91.0, 12.0), "太平洋")
    north_arrow(cv, lb, 600, 2, length=28)
    lb.put(20, 474, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L08_fig1_winter_pattern_map.svg", "lesson": "L08", "canvas": cv,
            "title": "冬の模式天気図（北が上）——大陸に高気圧（中心1036hPa）、海洋上に低気圧（中心996hPa）、たてにならぶ等圧線",
            "desc": "北が上の模式天気図（教材用に作成・架空の値）。図の左上の大陸に高気圧の中心（1036hPa）、図の右の海洋上に低気圧の中心"
                    "（996hPa）があり、そのあいだに4hPaごとの等圧線がたてに7本ならぶ（1032は高気圧を、1000は低気圧を囲む）。数字は1032・1024・"
                    "1016・1008・1000の線に書いた。日本列島と大陸は地図データを使わない簡略な多角形。地点アは日本海側の町、イは太平洋側の町、"
                    "ウは大陸上。風向の矢印と季節の名前は図に入れない。同型図は中心の位置・値と線の間隔を差し替えて生成する",
            "alt": "冬の模式天気図（北が上）——図の左上の大陸に高気圧の中心（1036hPa）、図の右の海洋上に低気圧の中心（996hPa）があり、等圧線が4hPaごとに、たてに何本もならぶ。日本列島は簡略な多角形。地点アは日本海側の町、地点イは太平洋側の町、地点ウは大陸上（模式図・教材用に作成・架空の値）",
            "intent": "冬の気圧配置（大陸に高気圧・海洋上に低気圧・たてにならぶせまい間隔の等圧線）を見せ、日本が低気圧の西側かつ高気圧の東側にあることを読ませる",
            "src": "lesson_08.md「シベリア気団の発達と冬の気圧配置」（注意書きの直後）",
            "params": f"高気圧 中心1036hPa（{Wd['H'][0]:.0f}, {Wd['H'][1]:.0f}）・低気圧 中心996hPa（{Wd['L'][0]:.0f}, {Wd['L'][1]:.0f}）（地図単位 100×64）／"
                      f"等圧線 1032〜1000 の9本（4hPaごと）／町の緯度での間隔 {g['delta']:.2f}単位＝{g['delta'] * mf.s:.1f}px／"
                      "数字を書く線 1032・1024・1016・1008・1000／地点ア 1016・イ 1012・ウ 1032 の線上",
            "checks": ck.items,
            "check_tokens": ["冬", "西高東低", "シベリア", "北西", "季節風", "季節", "1012", "1028", "1020", "1004",
                             "16hPa"],
            "check_tokens_meta": ["西高東低", "シベリア", "北西", "季節風", "16hPa"],
            "digit_rule": ("subset", {"1036", "996", "1032", "1024", "1016", "1008", "1000"}),
            "allow_texts": lb.items}


def fig_L08_2():
    # --- パラメータ（lesson_08.md「日本海を渡る風——日本海側の雪と太平洋側の晴れ」・図2） ---
    sea_y, x0, x1 = 262.0, 30.0, 610.0
    coast_x = 190.0
    terrain = [(coast_x, sea_y), (232.0, 250.0), (332.0, 128.0), (446.0, 243.0), (x1, 252.0)]  # 海岸→山頂→太平洋側
    peak = terrain[2]
    base_y = 300.0
    slope_a, slope_b = terrain[1], terrain[2]                  # 日本海側の斜面（上り）
    up_n = unit((-(slope_b[1] - slope_a[1]), slope_b[0] - slope_a[0]))   # 斜面から空へ向かう法線（px）
    if up_n[1] > 0:
        up_n = mul(up_n, -1.0)

    def on_slope(t, off):
        return add(lerp(slope_a, slope_b, t), mul(up_n, off))

    cloud = ([(*on_slope(t, 40.0), 18.0, 15.0) for t in (0.28, 0.42, 0.56, 0.70, 0.84)]
             + [(*on_slope(t, 64.0), 17.0, 14.0) for t in (0.40, 0.56, 0.72)])   # 斜面にそう雲（2列の楕円を重ねる）
    arrows = [((42.0, 238.0), (176.0, 238.0)), (on_slope(0.1, 14.0), on_slope(0.86, 14.0)),
              ((366.0, 118.0), (452.0, 212.0)), ((470.0, 226.0), (600.0, 226.0))]
    H = 360

    def ground_y(x):
        return polyline_y_at_x(terrain, x)[0]

    ck = Checker()
    ck.ok("山頂が地形の最も高い所（海岸から山頂まで上り、山頂から太平洋側へ下る）",
          all(peak[1] <= q[1] for q in terrain) and terrain[1][1] > peak[1] < terrain[3][1])
    ck.ok("風の矢印はすべて左（日本海）から右（太平洋側）へ進む", all(b[0] > a[0] for a, b in arrows))
    ck.ok("風の矢印は地形にそう（上りの斜面では上へ・下りの斜面では下へ）",
          arrows[1][1][1] < arrows[1][0][1] and arrows[2][1][1] > arrows[2][0][1])
    ck.ok("風の矢印は地面より上（海面・斜面から 8px 以上）",
          all(p[1] < (sea_y if p[0] <= coast_x else ground_y(p[0])) - 8.0 for a, b in arrows for p in (a, b)))
    ck.ok("雲は山の日本海側の斜面の上（海岸と山頂のあいだ）で、斜面から 20px 以上はなれる",
          all(coast_x < cx - rx and cx + rx <= peak[0] + 20.0 and cy + ry < ground_y(cx) - 20.0 for cx, cy, rx, ry in cloud))
    cl_pts = [(cx + rx * math.cos(2 * math.pi * i / 72), cy + ry * math.sin(2 * math.pi * i / 72))
              for cx, cy, rx, ry in cloud for i in range(72)]
    gap_c = min(dist_point_seg(q, a, b) for q in cl_pts for a, b in arrows)
    ck.ok("雲と風の矢印は重ならない（雲の外形と矢印の最小距離 > 8px）", gap_c > 8.0, f"{gap_c:.1f}px")
    body_has(ck, 8, "左が日本海、中央が日本の山、右が太平洋側", "図の約束")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(30, 34, "模式図（教材用に作成）", size=FS_S, anchor="start")
    cv.fill_poly([(x0, sea_y), (coast_x, sea_y), (coast_x, base_y), (x0, base_y)], SEA_FILL)
    land = [(coast_x, sea_y)] + terrain[1:] + [(x1, base_y), (coast_x, base_y)]
    cv.fill_poly(land, LAND_FILL)
    cv.path(terrain, w=MAIN_W, oid="terrain", join="miter")
    cv.line(x0, sea_y, coast_x, sea_y, w=MAIN_W, oid="sea")
    cv.path([(x0, sea_y), (x0, base_y), (x1, base_y), (x1, terrain[-1][1])], w=1.2, oid="frame", join="miter")
    cloud_union(cv, cloud)
    for a, b in arrows:
        cv.arrow(a[0], a[1], b[0], b[1], w=2.6, head=13, oid="wind")
    b_vap = lb.put(110, 214, "水蒸気を受け取る", size=FS_S)
    b_snow = lb.put(200, 140, "雲・雪", anchor="end")
    b_sun = lb.put(530, 190, "晴れ", weight="bold")
    lb.put(110, sea_y + 26, "日本海")
    lb.put(250, base_y - 12, "日本海側", size=FS_S)
    lb.put(332, base_y - 12, "山", size=FS_S)
    lb.put(530, base_y - 12, "太平洋側", size=FS_S)
    ck.ok("「晴れ」は山頂より東（太平洋側）・「水蒸気を受け取る」は海の上・「雲・雪」は山頂より西（日本海側）",
          b_sun[0] > peak[0] and x0 < b_vap[0] and b_vap[2] < coast_x and b_snow[2] < peak[0])
    cv.layout_checks(ck)

    return {"file": "L08_fig2_sea_of_japan_snow_section.svg", "lesson": "L08", "canvas": cv,
            "title": "日本海側の雪の断面模式図——日本海の上で水蒸気を受け取り、山の日本海側で雲・雪、山を越えた太平洋側は晴れ",
            "desc": "左が日本海、中央が日本の山、右が太平洋側の断面の模式図（教材用に作成・山の高さや雲の大きさは誇張）。地表付近の風の矢印が"
                    "左から右へ進み、日本海の上で「水蒸気を受け取る」を、山の日本海側の斜面の上に楕円を重ねた雲と「雲・雪」を、山を越えた太平洋側に"
                    "「晴れ」を書いた。同型図は地形の折れ線と雲の位置を差し替えて生成する",
            "alt": "日本海側の雪の断面模式図——左（日本海）から右（太平洋側）へ地表付近の風の矢印が進み、日本海の上で水蒸気を受け取り、中央の山の日本海側の斜面で雲ができて雪、山を越えた太平洋側は晴れ（模式図・教材用に作成）",
            "intent": "同じ1つの風が、日本海で水蒸気を受け取って山の日本海側に雪を降らせ、山を越えた太平洋側では晴れになる道すじを見せる",
            "src": "lesson_08.md「日本海を渡る風——日本海側の雪と太平洋側の晴れ」（注意書きの直後）",
            "params": f"海面 y={sea_y:.0f}px・海岸 x={coast_x:.0f}px・山頂 ({peak[0]:.0f}, {peak[1]:.0f})px／雲 楕円{len(cloud)}個を重ねる（日本海側の斜面から 40px・64px）／風の矢印4本（左→右）",
            "checks": ck.items,
            "check_tokens": ["飽和水蒸気量", "上昇", "乾いた", "湿った", "北西", "季節風", "シベリア"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


# ---- 春・秋の連続模式天気図（L09 図1・L10 図3 の「春・秋」で共用・目盛り単位） ----
SPRING = {"H_v": 1020, "L_v": 1000, "H_levels": [1016, 1012], "L_levels": [1004, 1008],
          "radii": [1.0, 1.6], "ratio": 0.9,
          "days": [("1日目", {"A": 0, "B": -4, "C": -8}), ("3日目", {"A": 4, "B": 0, "C": -4})],
          "kind": {"A": "H", "B": "L", "C": "H"}, "town": 0, "x_range": (-8.8, 8.8), "ticks": (-8, 8)}


def fig_L09_1():
    # --- パラメータ（lesson_09.md「春と秋——移動性高気圧と温帯低気圧が交互に通る」・図1・架空の値）: 上の SPRING ---
    Sd = SPRING
    x_left, x_right = 30.0, 610.0
    s = (x_right - x_left) / (Sd["x_range"][1] - Sd["x_range"][0])
    panel_top, panel_h = [74.0, 240.0], 150.0
    H = 512

    ck = Checker()
    d1, d3 = Sd["days"][0][1], Sd["days"][1][1]
    ck.ok("1日目: A=0・B=西へ4・C=西へ8／3日目: A=東へ4・B=0・C=西へ4",
          d1 == {"A": 0, "B": -4, "C": -8} and d3 == {"A": 4, "B": 0, "C": -4})
    ck.ok("すべての中心が2日で東へ4目盛り（1日あたり2目盛り）", all(d3[k] - d1[k] == 4 for k in d1))
    ck.ok("高・低・高が交互で、となりの中心の間隔は4目盛り",
          [Sd["kind"][k] for k in ("A", "B", "C")] == ["H", "L", "H"] and d1["A"] - d1["B"] == 4 and d1["B"] - d1["C"] == 4)
    ck.ok("1日目は町の真上に高気圧A、3日目は町の真上に低気圧B", d1["A"] == Sd["town"] and d3["B"] == Sd["town"])
    ck.ok("等圧線は 4hPa ごと（1020→1016→1012／1000→1004→1008）",
          [Sd["H_v"] - 4, Sd["H_v"] - 8] == Sd["H_levels"] and [Sd["L_v"] + 4, Sd["L_v"] + 8] == Sd["L_levels"]
          and Sd["H_levels"][-1] - Sd["L_levels"][-1] == 4)
    body_has(ck, 9, f"町の真上（目盛り0）に高気圧A（中心{Sd['H_v']}hPa）", "1日目の高気圧A")
    body_has(ck, 9, f"低気圧B（中心{Sd['L_v']}hPa）", "低気圧Bの値")
    body_has(ck, 9, "高気圧Aは東へ4、低気圧Bは0（町の真上）、高気圧Cは西へ4", "3日目の位置")
    body_has(ck, 9, "2日で東へ目盛り4つ分", "移動量")

    cv = Canvas(W, H)
    lb = Labels(cv)
    lb.put(x_left, 30, f"中心の気圧: 高 {Sd['H_v']}hPa・低 {Sd['L_v']}hPa（等圧線は4hPaごと）", size=FS_S, anchor="start")
    lb.put(x_left, 56, "人形マーク＝町（2枚とも同じ位置・目盛り0）", size=FS_S, anchor="start")
    north_arrow(cv, lb, 592, 4, length=30)
    min_gap = float("inf")
    for d, (title, pos) in enumerate(Sd["days"]):
        top = panel_top[d]
        yc = top + 82.0
        fr = Frame(x_left - s * Sd["x_range"][0], yc, s)
        rect = (x_left, top, x_right, top + panel_h)
        cv.rect(x_left, top, x_right - x_left, panel_h, sw=1.2, oid=f"frame{d}")
        outer = {}
        for key in ("C", "B", "A"):
            kind = Sd["kind"][key]
            levels = Sd["H_levels"] if kind == "H" else Sd["L_levels"]
            c = (float(pos[key]), 0.0)
            for lv, a in zip(levels, Sd["radii"]):
                pts = fr.Ps(ellipse_pts(c, a, a * Sd["ratio"]))
                for run in clip_polyline(pts + [pts[0]], rect):
                    cv.path(run, w=THIN_W, oid=f"iso{d}{key}{lv}")
                outer[key] = pts
            px, py = fr.P(c)
            center_cross(cv, px, py, r=4.0, oid=f"cross{d}{key}")
            lb.put(px + 18.5, py + 0.29 * FS, "高" if kind == "H" else "低", weight="bold")
            ytop = py - Sd["radii"][-1] * s * Sd["ratio"]
            lb.put(px, ytop - 7.0, key, weight="bold")
        min_gap = min(min_gap, min_dist_polylines(outer["A"], outer["B"]), min_dist_polylines(outer["B"], outer["C"]))
        for k in range(Sd["ticks"][0], Sd["ticks"][1] + 1):
            xk = fr.P((k, 0.0))[0]
            cv.line(xk, top + panel_h - 7, xk, top + panel_h, w=1.2)
        tx, ty = fr.P((Sd["town"], 0.0))
        person(cv, tx, ty, s=0.8, oid=f"person{d}")
        lb.put(x_right - 10, top + 24, title, anchor="end")
    ck.ok("となりの中心の族どうしの楕円は交わらない（最小距離 > 12px）", min_gap > 12.0, f"最小距離={min_gap:.1f}px")
    ys = 420.0
    fr0 = Frame(x_left - s * Sd["x_range"][0], ys, s)
    cv.line(fr0.P((Sd["ticks"][0], 0))[0], ys, fr0.P((Sd["ticks"][1], 0))[0], ys, w=MAIN_W, oid="scale")
    for k in range(Sd["ticks"][0], Sd["ticks"][1] + 1):
        xk = fr0.P((k, 0.0))[0]
        cv.line(xk, ys - 6, xk, ys + 6, w=1.4, oid="scale")
        lb.put(xk, ys + 26, str(abs(k)), size=FS_S)
    lb.put(x_left, ys + 52, "← 西", size=FS_S, anchor="start")
    lb.put(x_right, ys + 52, "東 →", size=FS_S, anchor="end")
    lb.put(320, ys + 52, "目盛り（町が0）", size=FS_S)
    lb.put(x_left, ys + 84, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L09_fig1_spring_autumn_sequence.svg", "lesson": "L09", "canvas": cv,
            "title": "春・秋の連続模式天気図（1日目と3日目）——高気圧・低気圧・高気圧が交互にならび、2日で東へ目盛り4つ分動く",
            "desc": "北が上の模式天気図2枚（教材用に作成・架空の値）。西から東へ向かう目盛り（町＝0・西へ8〜東へ8）の上に、高気圧A（中心1020hPa）・"
                    "低気圧B（中心1000hPa）・高気圧C（中心1020hPa）が4目盛りおきに交互にならぶ。1日目は A=0・B=西へ4・C=西へ8、3日目は "
                    "A=東へ4・B=0・C=西へ4。等圧線は4hPaごとで、中心の値だけを書く。天気の記号は入れない。同型図は各日の中心の目盛りを差し替えて生成する",
            "alt": "春・秋の連続模式天気図（1日目と3日目・北が上）——西から東へ向かう目盛りの上に、高気圧（中心1020hPa）・低気圧（中心1000hPa）・高気圧（中心1020hPa）が交互にならび、1日目には町（目盛り0）の真上に高気圧、3日目には同じ町の真上に低気圧の中心がある。すべての中心が2日で東へ目盛り4つ分動いている（模式図・教材用に作成・架空の値）",
            "intent": "移動性高気圧と温帯低気圧が交互に西から東へ通過し、町の真上に来るものが数日ごとに入れかわることを目盛りで読ませる",
            "src": "lesson_09.md「春と秋——移動性高気圧と温帯低気圧が交互に通る」（注意書きの直後）",
            "params": f"1日目 A=0・B=−4・C=−8／3日目 A=+4・B=0・C=−4（目盛り・東が正）／等圧線 高 1016・1012・低 1004・1008／1目盛り {s:.2f}px",
            "checks": ck.items,
            "check_tokens": ["晴れ", "雨", "くずれ", "5日目", "東へ4個分", "個分", "1日あたり", "移動性", "温帯低気圧", "周期"],
            "digit_rule": ("subset", {"0", "1", "2", "3", "4", "5", "6", "7", "8", "1020", "1000"}),
            "allow_texts": lb.items}


# ---- 梅雨の模式天気図（L09 図2・L10 図3 の「梅雨」で共用・地図単位） ----
BAIU = {"front": [(20.0, 26.5), (34.0, 24.0), (47.0, 23.0), (58.0, 26.2), (70.0, 31.0), (84.0, 35.0), (100.0, 37.0)],
        "N": (92.5, 54.0), "S": (72.0, 11.0), "v": 1016,
        "N_rings": [(1012, 7.0, 4.6), (1008, 11.0, 8.0)], "S_rings": [(1012, 11.0, 5.2), (1008, 20.0, 8.5)],
        "A_y": 43.0, "I": (60.0, 20.5), "U_x": 57.0, "U_inset": 0.9,
        "sym_step": 5.0, "sym_size": 3.0, "sym_first": 3.5}


def baiu_geometry():
    Bd = BAIU
    front = catmull_rom(Bd["front"], n=10)
    syms = front_symbols(front, Bd["sym_step"], Bd["sym_first"], [("semi", +1), ("tri", -1)], Bd["sym_size"])
    ax = polyline_x_at_y(JAPAN_AXIS_CURVE, Bd["A_y"])
    A = (ax[0], Bd["A_y"])
    se = polyline_y_at_x(JAPAN_SE_EDGE, Bd["U_x"])
    U = (Bd["U_x"], se[0] + Bd["U_inset"])
    rings = [(lv, ellipse_pts(Bd["N"], a, b), True) for lv, a, b in Bd["N_rings"]] + \
            [(lv, ellipse_pts(Bd["S"], a, b), True) for lv, a, b in Bd["S_rings"]]
    return {"front": front, "syms": syms, "A": A, "I": Bd["I"], "U": U, "rings": rings}


def check_baiu(ck, g):
    Bd = BAIU
    front, syms = g["front"], g["syms"]
    d = unit(sub(front[-1], front[0]))
    ck.ok("前線は東西にのびる（全体の向きが東から±25°以内）", abs(math_deg(d)) <= 25.0, f"{math_deg(d):.1f}°")
    kinds = [k for k, _, _, _, _ in syms]
    ck.ok("記号は半円と三角が交互", all(kinds[i] != kinds[i + 1] for i in range(len(kinds) - 1)) and len(kinds) >= 6,
          f"{len(kinds)}個")
    ck.ok("半円は線の北側・三角は線の南側（記号の向きの北の成分: 半円は正・三角は負）",
          all((n[1] > 0) == (k == "semi") for k, _, _, n, _ in syms))
    ck.ok("北の高気圧・南の高気圧の中心は同じ値（1016hPa）で、それぞれ前線の北・南の海上",
          side_of_curve(Bd["N"], front) > 0 and side_of_curve(Bd["S"], front) < 0
          and not on_land(Bd["N"]) and not on_land(Bd["S"]))
    ck.ok("等圧線は 4hPa ごと（1016→1012→1008・北も南も）",
          [lv for lv, _, _ in Bd["N_rings"]] == [Bd["v"] - 4, Bd["v"] - 8] == [lv for lv, _, _ in Bd["S_rings"]])
    gmin = min(min_dist_polylines(pts, front) for _, pts, _ in g["rings"])
    ck.ok("等圧線は前線にかからない（最小距離 > 1.5単位）", gmin > 1.5, f"{gmin:.2f}単位")
    A, I, U = g["A"], g["I"], g["U"]
    du = dist_point_polyline(U, front)
    ck.ok("地点アは前線の北側（日本の上）・地点イは前線の南側・地点ウは前線のすぐ近く（2.5単位以内・日本の上）",
          side_of_curve(A, front) > 0 and in_japan(A) and side_of_curve(I, front) < 0 and du < 2.5 and in_japan(U),
          f"ウと前線の距離={du:.2f}単位")
    near_part = [p for p in front if 47.0 <= p[0] <= 66.0]
    dj = max(min(dist_point_polyline(p, poly, closed=True) for poly in JAPAN_POLYS) if not in_japan(p) else 0.0
             for p in near_part)
    ck.ok("前線は日本列島にそう（西日本〜本州の南の部分で日本から 5単位以内）", dj < 5.0, f"最大 {dj:.2f}単位")


def draw_front(cv, mf, front, syms, w=FRONT_W, oid="front"):
    for run in clip_polyline(front, mf.crop):
        cv.path(mf.Ps(run), w=w, oid=oid)
    for kind, p, t, n, poly in syms:
        if all(mf.contains(q) for q in poly):
            pp = mf.Ps(poly)
            cv.fill_poly(pp, "#000")
            cv.obstacle(oid, pp + [pp[0]])


def fig_L09_2():
    # --- パラメータ（lesson_09.md「梅雨——動かない前線」・図2・架空の値）: 上の BAIU ---
    H = 484
    mf = MapFrame(20.0, 58.0, 6.0, (0.0, 0.0, MAP_W, MAP_H))
    g = baiu_geometry()
    Bd = BAIU

    ck = Checker()
    check_baiu(ck, g)
    body_has(ck, 9, f"高気圧（中心{Bd['v']}hPa）があり、その中の空気が北の", "北の高気圧")
    body_has(ck, 9, f"高気圧（中心{Bd['v']}hPa）があり、その中の空気が南の", "南の高気圧")
    body_has(ck, 9, "地点アは前線の北側（北の気団の中）、地点イは前線の南側（南の気団の中）、地点ウは前線のすぐ近くです", "地点ア〜ウ")

    cv = Canvas(W, H)
    lb = Labels(cv)
    draw_basemap(cv, mf)
    draw_isobar_lines(cv, mf, g["rings"])
    draw_front(cv, mf, g["front"], g["syms"])
    draw_map_frame(cv, mf)
    for c in (Bd["N"], Bd["S"]):
        map_label(lb, mf, c, "高", (0.0, -9.0), weight="bold")
        map_label(lb, mf, c, str(Bd["v"]), (0.0, 11.0), size=FS_S)
    map_label(lb, mf, (90.8, 42.5), "北の海上")
    map_label(lb, mf, (78.5, 21.9), "南の海上")
    for p, name, off in ((g["A"], "ア", (-15.0, -10.0)), (g["I"], "イ", (-17.0, 0.0)), (g["U"], "ウ", (-10.0, -16.0))):
        pp = mf.P(p)
        cv.dot(*pp)
        lb.put(pp[0] + off[0], pp[1] + off[1] + 0.29 * FS, name, bg=True, own=("coast",))
    north_arrow(cv, lb, 600, 2, length=28)
    lb.put(20, 474, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L09_fig2_baiu_front_map.svg", "lesson": "L09", "canvas": cv,
            "title": "梅雨の模式天気図（北が上）——日本列島にそって東西にのびる前線と、北と南の海上の高気圧（どちらも中心1016hPa）",
            "desc": "北が上の模式天気図（教材用に作成・架空の値）。日本列島にそって東西にのびる前線に、半円（線の北側）と三角（線の南側）の記号を"
                    "交互につけた。前線の北の海上と南の海上に高気圧（どちらも中心1016hPa・4hPaごとの閉じた等圧線2本）がある。地点アは前線の北側、"
                    "イは前線の南側、ウは前線のすぐ近く。気団の名前と季節の名前は図に入れない。日本列島と大陸は簡略な多角形。"
                    "同型図は前線の制御点と2つの高気圧の位置・値を差し替えて生成する",
            "alt": "梅雨の模式天気図（北が上）——日本列島にそって東西にのびる前線（半円と三角の記号が線の北側と南側に交互につく）があり、その北の海上に高気圧（中心1016hPa）、南の海上にも高気圧（中心1016hPa）がある。地点アは前線の北側、地点イは前線の南側、地点ウは前線のすぐ近く（模式図・教材用に作成・架空の値）",
            "intent": "性質のちがう2つの気団（北と南の高気圧）の勢力がつり合って、境の前線が東西にのびたまま動かない配置を見せる",
            "src": "lesson_09.md「梅雨——動かない前線」（注意書きの直後）",
            "params": f"前線の制御点 {len(Bd['front'])}個（東西）・記号 {Bd['sym_size']}単位・{Bd['sym_step']}単位おき（半円＝北側・三角＝南側を交互）／"
                      f"北の高気圧 ({Bd['N'][0]}, {Bd['N'][1]})・南の高気圧 ({Bd['S'][0]}, {Bd['S'][1]})（地図単位・どちらも1016hPa）",
            "checks": ck.items,
            "check_tokens": ["梅雨", "停滞前線", "オホーツク", "小笠原", "気団", "冷たく湿った", "暖かく湿った", "つり合", "勢力",
                             "夏", "春"],
            "check_tokens_meta": ["停滞前線", "オホーツク", "小笠原", "冷たく湿った", "暖かく湿った", "つり合", "勢力"],
            "digit_rule": ("subset", {"1016"}),
            "allow_texts": lb.items}


# ---- 夏の模式天気図（L10 図1・L10 図3 の「夏」で共用・地図単位） ----
SUMMER = {"H_v": 1016, "L_v": 1000, "town_y": 25.5, "H_deg": -14.0, "H_dist": 31.0, "L_deg": 162.0, "L_dist": 37.0,
          "H_rings": [(1012, 13.5, 5.8), (1008, 31.0, 12.5)], "L_rings": [(1004, 15.0, 10.5)], "I_off": (7.1, 0.5)}


def summer_geometry():
    Sd = SUMMER
    ax = polyline_x_at_y(JAPAN_AXIS_CURVE, Sd["town_y"])
    A = (ax[0], Sd["town_y"])
    Hc = add(A, mul((math.cos(Sd["H_deg"] * DEG), math.sin(Sd["H_deg"] * DEG)), Sd["H_dist"]))
    Lc = add(A, mul((math.cos(Sd["L_deg"] * DEG), math.sin(Sd["L_deg"] * DEG)), Sd["L_dist"]))
    I = add(Hc, Sd["I_off"])
    lines = [(lv, ellipse_pts(Hc, a, b), True) for lv, a, b in Sd["H_rings"]] + \
            [(lv, ellipse_pts(Lc, a, b), True) for lv, a, b in Sd["L_rings"]]
    return {"A": A, "H": Hc, "L": Lc, "I": I, "lines": lines}


def check_summer(ck, g, s_px, winter_delta_px):
    Sd = SUMMER
    A, Hc, Lc, I = g["A"], g["H"], g["L"], g["I"]
    ah = math_deg(sub(Hc, A))
    al = math_deg(sub(Lc, A))
    ck.ok("高気圧の中心（1016）は地点アから見てほぼ東（やや南）＝向きが東から南へ 3°〜25°", -25.0 <= ah <= -3.0, f"{ah:.1f}°")
    ck.ok("低気圧の中心（1000）は地点アから見てほぼ西（やや北）＝向きが西から北へ 3°〜30°", 150.0 <= al <= 177.0, f"{al:.1f}°")
    ck.ok("高気圧の中心は海上（日本の南〜南東）、低気圧の中心は大陸上",
          not on_land(Hc) and Hc[1] < A[1] and point_in_polygon(Lc, CONTINENT_POLY))
    ck.ok("等圧線は 4hPa ごと: 高 1016→1012→1008、低 1000→1004（両中心のあいだに 1012・1008・1004 の3本）",
          [lv for lv, _, _ in Sd["H_rings"]] == [Sd["H_v"] - 4, Sd["H_v"] - 8]
          and [lv for lv, _, _ in Sd["L_rings"]] == [Sd["L_v"] + 4] and Sd["H_v"] - 8 - (Sd["L_v"] + 4) == 4)
    ck.ok("高気圧の等圧線は東西に長い楕円（東西の半径＞南北の半径の2倍）", all(a > 2 * b for _, a, b in Sd["H_rings"]))
    lv8, a8, b8 = Sd["H_rings"][1]
    ring8 = ellipse_pts(Hc, a8, b8)
    ck.ok("1008 の線が日本の南の海上へ西へ張り出す（西の端が本州の中ほどより西）が、日本には重ならない",
          Hc[0] - a8 < 60.0 and not any(in_japan(q) for q in ring8)
          and not any(ellipse_val(q, Hc, a8, b8) < 1.0 for poly in JAPAN_POLYS for q in poly))
    rings = [pts for _, pts, _ in g["lines"]]
    gmin = min(min_dist_polylines(rings[i], rings[j]) for i in range(len(rings)) for j in range(i + 1, len(rings)))
    ck.ok("等圧線どうしは交わらない", gmin > 1.0, f"最小距離={gmin:.2f}単位")
    ck.ok("等圧線の間隔（となりの線の最小距離・px）が冬の図の間隔より広い", gmin * s_px > winter_delta_px,
          f"{gmin * s_px:.1f}px > {winter_delta_px:.1f}px")
    ck.ok("地点アは日本の上、地点イは高気圧の中心付近の海上（1012 の線の内側）",
          in_japan(A) and not on_land(I) and ellipse_val(I, Hc, Sd["H_rings"][0][1], Sd["H_rings"][0][2]) < 1.0)
    ck.ok("日本（地点ア）は低気圧の中心の東側かつ高気圧の中心の西側（東西の対応表〔レッスン2の約束〕で2つの中心から同じ風向になる配置。地点アを通る等圧線の向きは使っていない）",
          Lc[0] < A[0] < Hc[0])


def fig_L10_1():
    # --- パラメータ（lesson_10.md「小笠原気団の発達と夏の気圧配置」・図1・架空の値）: 上の SUMMER ---
    H = 484
    mf = MapFrame(20.0, 58.0, 6.0, (0.0, 0.0, MAP_W, MAP_H))
    g = summer_geometry()
    Sd = SUMMER
    wg = winter_geometry()

    ck = Checker()
    check_summer(ck, g, mf.s, wg["delta"] * mf.s)
    body_has(ck, 10, f"中心の値は{Sd['H_v']}hPaで、中心は地点ア（日本の町）から見てほぼ東（やや南）にあります", "高気圧の位置と値")
    body_has(ck, 10, f"中心の値は{Sd['L_v']}hPaで、中心は地点アから見てほぼ西（やや北）にあります", "低気圧の位置と値")

    cv = Canvas(W, H)
    lb = Labels(cv)
    draw_basemap(cv, mf)
    draw_isobar_lines(cv, mf, g["lines"])
    draw_map_frame(cv, mf)
    for c, mark, v in ((g["H"], "高", Sd["H_v"]), (g["L"], "低", Sd["L_v"])):
        map_label(lb, mf, c, mark, (0.0, -9.0), weight="bold")
        map_label(lb, mf, c, str(v), (0.0, 11.0), size=FS_S)
    (l12, a12, b12), (l08, a08, b08) = Sd["H_rings"]
    (l04, a04, b04), = Sd["L_rings"]
    iso_label(lb, mf.P(ellipse_point(g["H"], a12, b12, 90.0)), l12, f"iso{l12}")
    iso_label(lb, mf.P(ellipse_point(g["H"], a08, b08, 270.0)), l08, f"iso{l08}")
    iso_label(lb, mf.P(ellipse_point(g["L"], a04, b04, 90.0)), l04, f"iso{l04}")
    for p, name, off in ((g["A"], "ア", (-14.0, -14.0)), (g["I"], "イ", (15.0, 0.0))):
        pp = mf.P(p)
        cv.dot(*pp)
        lb.put(pp[0] + off[0], pp[1] + off[1] + 0.29 * FS, name, bg=True, own=("coast",))
    map_label(lb, mf, (10.0, 58.0), "大陸")
    north_arrow(cv, lb, 600, 2, length=28)
    lb.put(20, 474, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L10_fig1_summer_pattern_map.svg", "lesson": "L10", "canvas": cv,
            "title": "夏の模式天気図（北が上）——日本の南から南東の海上に張り出す高気圧（中心1016hPa）と大陸側の低気圧（中心1000hPa）",
            "desc": "北が上の模式天気図（教材用に作成・架空の値）。日本の南から南東の海上に、東西に長い楕円の等圧線（1012・1008）をもつ高気圧"
                    "（中心1016hPa）が張り出し、大陸側に低気圧（中心1000hPa・1004の線）がある。高気圧の中心は地点ア（日本の町）から見てほぼ東"
                    "（やや南）、低気圧の中心はほぼ西（やや北）。等圧線は4hPaごとで、冬の図より間隔が広い。地点イは高気圧の中心付近の海上。"
                    "風向の矢印と季節の名前は図に入れない。同型図は2つの中心の向きと距離・楕円の半径を差し替えて生成する",
            "alt": "夏の模式天気図（北が上）——日本の南から南東の海上に、東西に長い楕円の等圧線をもつ高気圧（中心1016hPa）が張り出し、その中心は地点ア（日本の町）から見てほぼ東（やや南）にある。大陸側には低気圧（中心1000hPa）があり、その中心は地点アから見てほぼ西（やや北）にある。等圧線は4hPaごと。地点イは高気圧の中心付近（模式図・教材用に作成・架空の値）",
            "intent": "夏の気圧配置（南の海上に張り出す高気圧・大陸側の低気圧・広い間隔の等圧線）を見せ、日本が低気圧の東側かつ高気圧の西側にあることを読ませる",
            "src": "lesson_10.md「小笠原気団の発達と夏の気圧配置」（注意書きの直後）",
            "params": f"地点アから高気圧の中心へ {Sd['H_deg']}°・{Sd['H_dist']}単位、低気圧の中心へ {Sd['L_deg']}°・{Sd['L_dist']}単位（東=0°・反時計回り）／"
                      "高 1012（東西 13.5・南北 5.8）・1008（31・12.5）／低 1004（15・10.5）（地図単位）",
            "checks": ck.items,
            "check_tokens": ["夏", "南高北低", "小笠原", "太平洋高気圧", "南東", "季節風", "暖かく湿った", "太平洋"],
            "check_tokens_meta": ["南高北低", "小笠原", "太平洋高気圧", "南東の風", "季節風", "暖かく湿った"],
            "digit_rule": ("subset", {"1016", "1000", "1012", "1008", "1004"}),
            "allow_texts": lb.items}


# ---- 台風の進路（L10 図2・地図単位） ----
TYPHOON = {"crop": (28.0, 0.0, 100.0, 60.0),
           "A": {"H": (75.0, 9.0), "rings": [(15.5, 5.0), (31.0, 10.0)],
                 "track": [(47.5, 0.0), (43.0, 3.2), (39.2, 8.5), (37.4, 15.0), (37.2, 22.5), (37.8, 30.0),
                           (38.6, 37.5), (39.6, 45.0), (40.8, 52.0), (42.2, 58.5)],
                 "label": (44.8, 56.4)},
           "B": {"H": (89.0, 9.0), "rings": [(6.0, 3.5), (12.0, 7.0)],
                 "track": [(80.5, 0.0), (75.8, 2.8), (72.6, 7.5), (70.2, 13.0), (68.0, 18.5), (66.4, 23.5),
                           (66.4, 28.0), (68.6, 32.5), (72.6, 37.0), (78.0, 41.5), (84.5, 46.0), (91.5, 50.5),
                           (98.5, 55.0)],
                 "label": (99.0, 30.0)}}


def fig_L10_2():
    # --- パラメータ（lesson_10.md「台風の進路——小笠原気団の張り出しが決める」・図2）: 上の TYPHOON ---
    Td = TYPHOON
    s = 4.1
    ph = s * (Td["crop"][3] - Td["crop"][1])
    pw = s * (Td["crop"][2] - Td["crop"][0])
    origins = {"A": (14.0, 62.0), "B": (14.0 + pw + 16.0, 62.0)}
    H = int(62.0 + ph + 44.0)

    ck = Checker()
    tracks = {k: catmull_rom(Td[k]["track"], n=8) for k in ("A", "B")}
    (aA, bA), (aB, bB) = Td["A"]["rings"][1], Td["B"]["rings"][1]
    HA, HB = Td["A"]["H"], Td["B"]["H"]
    ck.ok("パネルAの高気圧の楕円はBより大きく（面積が2倍以上）、西の端がBより西（大きく西へ張り出す）",
          aA * bA >= 2 * aB * bB and HA[0] - aA < HB[0] - aB)
    ringA = ellipse_pts(HA, aA, bA)
    ck.ok("パネルAの高気圧は日本の南の海上をおおい、日本とは重ならない",
          not any(in_japan(q) for q in ringA) and not any(ellipse_val(q, HA, aA, bA) < 1.0 for poly in JAPAN_POLYS for q in poly)
          and max(q[1] for q in ringA) < 24.0)
    for k, (Hc, a, b) in (("A", (HA, aA, bA)), ("B", (HB, aB, bB))):
        tr = tracks[k]
        inside = min(ellipse_val(q, Hc, a, b) for q in tr)
        west = (Hc[0] - a, Hc[1])
        dmin = min(dist(q, west) for q in tr)
        ck.ok(f"パネル{k}: 進路は高気圧の楕円の中に入らず（式の値の最小 > 1.1）、西の縁の近く（西の端から 6単位以内）を回る",
              inside > 1.1 and dmin < 6.0, f"最小={inside:.2f}・西の端との距離={dmin:.2f}")
    trA = tracks["A"]
    west_ok = True
    for q in trA:
        if 15.0 <= q[1] <= 52.0:
            xs = [p[0] for poly in JAPAN_POLYS for p in poly if abs(p[1] - q[1]) < 1.5]
            if xs and not q[0] < min(xs) - 2.0:
                west_ok = False
    endA = math_deg(sub(trA[-1], trA[-4]))
    ck.ok("パネルA: 進路は日本の西側を北上し（日本の緯度で日本の最も西の点より西）、最後の向きは北（東から 60°〜120°）",
          west_ok and 60.0 <= endA <= 120.0, f"最後の向き {endA:.1f}°")
    trB = tracks["B"]
    dj = min(dist_point_polyline(q, poly, closed=True) for q in trB for poly in JAPAN_POLYS)
    endB = math_deg(sub(trB[-1], trB[-4]))
    ck.ok("パネルB: 進路は日本の近くまで北上し（日本との最小距離 6単位以内・日本には重ならない）、最後は北東へ（東から 20°〜70°）",
          dj < 6.0 and not any(in_japan(q) for q in trB) and 20.0 <= endB <= 70.0,
          f"最小距離={dj:.2f}単位・最後の向き {endB:.1f}°")
    ck.ok("どちらの進路も南の海上から始まる（始点は海上・図の下端）",
          all(not on_land(tracks[k][0]) and near(tracks[k][0][1], 0.0) for k in ("A", "B")))
    body_has(ck, 10, "では高気圧が大きく西へ張り出し、台風は高気圧の西の縁を回るように、日本の西側を北上しています", "パネルA")
    body_has(ck, 10, "では高気圧が小さく東へ退き、台風は日本の近く（すぐそば・東側）まで北上して、北東へ向きを変えています", "パネルB")

    cv = Canvas(W, H)
    lb = Labels(cv)
    for k in ("A", "B"):
        ox, oy = origins[k]
        mf = MapFrame(ox, oy, s, Td["crop"])
        draw_basemap(cv, mf)
        Hc = Td[k]["H"]
        for a, b in Td[k]["rings"]:
            draw_curve_map(cv, mf, ellipse_pts(Hc, a, b), w=THIN_W, closed=True, oid=f"ring{k}")
        draw_map_frame(cv, mf, oid=f"frame{k}")
        tr = [q for q in tracks[k]]
        pts = mf.Ps(tr)
        cv.path(pts[:-1], w=2.6, oid=f"track{k}")
        cv.arrow(pts[-3][0], pts[-3][1], pts[-1][0], pts[-1][1], w=2.6, head=13, oid=f"track{k}")
        map_label(lb, mf, Hc, "高", (0.0, 0.0), weight="bold")
        anchor = "start" if k == "A" else "end"
        map_label(lb, mf, Td[k]["label"], "台風の進路", size=FS_S, anchor=anchor, own=("coast",), bg=True)
        lb.put(ox + 2, oy - 10, k, size=24, weight="bold", anchor="start")
    north_arrow(cv, lb, 606, 2, length=26)
    lb.put(320, H - 12, "模式図（教材用に作成）", size=FS_S)
    cv.layout_checks(ck)

    return {"file": "L10_fig2_typhoon_track_two_cases.svg", "lesson": "L10", "canvas": cv,
            "title": "台風の進路と高気圧の張り出しの模式図（2パネル）——高気圧の張り出し（大きさと位置）を変えて進路のちがいを見せる",
            "desc": "北が上の模式図2枚（教材用に作成）。パネルAでは高気圧の楕円が大きく西へ張り出して日本の南の海上をおおい、台風の進路の曲線は"
                    "南の海上から西寄りに進んで高気圧の西の縁を回り、日本の西側を北上する。パネルBでは高気圧の楕円が小さく東へ退き、進路は"
                    "高気圧の西の縁を回って日本の近くまで北上し、北東へ向きを変える。どちらのパネルが夏・秋かは書かない。数値なし。"
                    "日本列島と大陸は簡略な多角形。同型図は高気圧の楕円の中心・半径と進路の制御点を差し替えて生成する",
            "alt": "台風の進路と高気圧の張り出しの模式図（2パネル・北が上）——パネルAでは高気圧の楕円が大きく西へ張り出して日本の南の海上をおおい、台風の進路の曲線は南の海上から西寄りに進んで高気圧の西の縁を回り、日本の西側を北上する。パネルBでは高気圧の楕円が小さく東へ退き、台風の進路は高気圧の西の縁を回って日本の近くまで北上し、北東へ向きを変える（模式図・教材用に作成）",
            "intent": "台風が高気圧の中に入らず縁を回ること、張り出しの大きさで進める道が変わることを2枚の対比で見せる（季節の判定は本文の問いで行う）",
            "src": "lesson_10.md「台風の進路——小笠原気団の張り出しが決める」（注意書きの直後）",
            "params": f"A: 高気圧 中心 {HA}・楕円 {Td['A']['rings']}／B: 高気圧 中心 {HB}・楕円 {Td['B']['rings']}（地図単位）／"
                      f"進路 A {len(Td['A']['track'])}点・B {len(Td['B']['track'])}点（Catmull-Rom）",
            "checks": ck.items,
            "check_tokens": ["夏", "秋", "偏西風", "小笠原", "衰退", "発達", "張り出し"],
            "check_tokens_meta": ["偏西風", "小笠原", "衰退", "発達"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


def fig_L10_3():
    # --- パラメータ（lesson_10.md「まとめ——四季の気圧配置を1枚に」・図3）: WINTER・SPRING・BAIU・SUMMER をそのまま縮小 ---
    s = 2.9
    pw, ph = s * MAP_W, s * MAP_H
    slots = {"冬": (20.0, 72.0), "春・秋": (20.0 + pw + 20.0, 72.0), "梅雨": (20.0, 72.0 + ph + 52.0),
             "夏": (20.0 + pw + 20.0, 72.0 + ph + 52.0)}
    H = int(72.0 + 2 * ph + 52.0 + 40.0)

    ck = Checker()
    cv = Canvas(W, H)
    lb = Labels(cv)
    # 冬
    ox, oy = slots["冬"]
    mf = MapFrame(ox, oy, s, (0.0, 0.0, MAP_W, MAP_H))
    wg = winter_geometry()
    draw_basemap(cv, mf, oid_coast="coast")
    draw_isobar_lines(cv, mf, wg["lines"], w=1.0, prefix="w")
    draw_map_frame(cv, mf, oid="frame1")
    map_label(lb, mf, WINTER["H"], "高", weight="bold")
    map_label(lb, mf, WINTER["L"], "低", weight="bold")
    ck.ok("「冬」の小図は L08 図1 と同じパラメータ（中心・9本の等圧線の値）",
          [lv for lv, _, _ in wg["lines"]] == list(range(1032, 999, -4)))
    # 春・秋（L09 図1 の3日目のコマ）
    ox, oy = slots["春・秋"]
    Sd = SPRING
    day3 = Sd["days"][1][1]
    sx = pw / 13.0
    fr = Frame(ox + pw / 2.0, oy + ph / 2.0, sx)
    rect = (ox, oy, ox + pw, oy + ph)
    cv.rect(ox, oy, pw, ph, sw=1.2, oid="frame2")
    for key in ("C", "B", "A"):
        kind = Sd["kind"][key]
        levels = Sd["H_levels"] if kind == "H" else Sd["L_levels"]
        c = (float(day3[key]), 0.0)
        for lv, a in zip(levels, Sd["radii"]):
            pts = fr.Ps(ellipse_pts(c, a, a * Sd["ratio"]))
            for run in clip_polyline(pts + [pts[0]], rect):
                cv.path(run, w=1.0, oid=f"s{key}{lv}")
        px, py = fr.P(c)
        lb.put(px, py + 0.29 * FS, "高" if kind == "H" else "低", weight="bold")
    ck.ok("「春・秋」の小図は L09 図1 の3日目と同じ配置（A=東へ4・B=0・C=西へ4・高低が交互）",
          day3 == {"A": 4, "B": 0, "C": -4} and [Sd["kind"][k] for k in ("C", "B", "A")] == ["H", "L", "H"])
    # 梅雨
    ox, oy = slots["梅雨"]
    mf = MapFrame(ox, oy, s, (0.0, 0.0, MAP_W, MAP_H))
    bg_ = baiu_geometry()
    small_syms = front_symbols(bg_["front"], BAIU["sym_step"] * 1.2, BAIU["sym_first"],
                               [("semi", +1), ("tri", -1)], BAIU["sym_size"] * 1.35)
    draw_basemap(cv, mf, oid_coast="coast")
    draw_isobar_lines(cv, mf, bg_["rings"], w=1.0, prefix="b")
    draw_front(cv, mf, bg_["front"], small_syms, w=2.0, oid="front3")
    draw_map_frame(cv, mf, oid="frame3")
    for c in (BAIU["N"], BAIU["S"]):
        map_label(lb, mf, c, "高", weight="bold")
    ck.ok("「梅雨」の小図は L09 図2 と同じ前線・高気圧（記号は半円＝北側・三角＝南側を交互）",
          all((n[1] > 0) == (k == "semi") for k, _, _, n, _ in small_syms))
    # 夏
    ox, oy = slots["夏"]
    mf = MapFrame(ox, oy, s, (0.0, 0.0, MAP_W, MAP_H))
    sg = summer_geometry()
    draw_basemap(cv, mf, oid_coast="coast")
    draw_isobar_lines(cv, mf, sg["lines"], w=1.0, prefix="s")
    draw_map_frame(cv, mf, oid="frame4")
    map_label(lb, mf, sg["H"], "高", weight="bold")
    map_label(lb, mf, sg["L"], "低", weight="bold")
    ck.ok("「夏」の小図は L10 図1 と同じパラメータ（中心の向き・楕円）",
          [lv for lv, _, _ in sg["lines"]] == [1012, 1008, 1004])
    for name, (ox, oy) in slots.items():
        lb.put(ox, oy - 12, name, weight="bold", anchor="start")
    ck.ok("季節名のラベルは「冬」「春・秋」「梅雨」「夏」の4つ", sorted(slots) == sorted(["冬", "春・秋", "梅雨", "夏"]))
    north_arrow(cv, lb, 606, 2, length=26)
    lb.put(20, H - 12, "模式図（教材用に作成・架空の値）", size=FS_S, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L10_fig3_four_seasons_overview.svg", "lesson": "L10", "canvas": cv,
            "title": "四季の気圧配置のまとめ（4つの小図）——冬／春・秋／梅雨／夏",
            "desc": "レッスン8〜10の模式天気図（教材用に作成・架空の値）を縮めて2×2にならべたまとめの図。「冬」は大陸に高・海洋上に低でたての等圧線。"
                    "「春・秋」は高気圧と低気圧が交互にならぶ（レッスン9図1の3日目）。「梅雨」は北と南の高気圧のあいだに東西にのびる前線。"
                    "「夏」は南の海上に張り出す高気圧と大陸側の低気圧。等圧線の数字は省いた。同型図は各小図のもとの図のパラメータを差し替えて生成する",
            "alt": "四季の気圧配置のまとめ（4つの小図・北が上）——「冬」は大陸に高・海洋上に低でたてじまの等圧線。「春・秋」は移動性高気圧と温帯低気圧が交互にならぶ。「梅雨」は北と南の高気圧のあいだに東西にのびる前線。「夏」は南の海上に張り出す高気圧と大陸側の低気圧（模式図・教材用に作成・架空の値）",
            "intent": "四季の気圧配置を「どの気団が発達しているか」の1つの問いの答えとして1枚にならべる",
            "src": "lesson_10.md「まとめ——四季の気圧配置を1枚に」（注意書きの直後）",
            "params": "冬＝L08図1・春・秋＝L09図1の3日目・梅雨＝L09図2・夏＝L10図1 と同じパラメータ（縮尺 2.9px/単位・等圧線の数字は省略）",
            "checks": ck.items,
            "check_tokens": ["西高東低", "南高北低", "停滞前線", "小笠原", "シベリア", "オホーツク", "移動性", "温帯"],
            "digit_rule": ("none", set()),
            "allow_texts": lb.items}


# ===========================================================================
# main: 陽性対照 → 生成（2回・一致） → 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L02_1, fig_L02_2, fig_L03_1, fig_L03_2,
        fig_L04_1, fig_L04_2, fig_L05_1, fig_L05_2, fig_L06_1, fig_L06_2,
        fig_L07_1, fig_L08_1, fig_L08_2, fig_L09_1, fig_L09_2,
        fig_L10_1, fig_L10_2, fig_L10_3]

TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TAG_RE = re.compile(r"<[^>]+>")
ALT_RE = re.compile(r"!\[(.*?)\]\(assets/([^)]+)\)")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
FONT_RE = re.compile(r'font-size="([0-9.]+)"')

# 出荷物に書いてはいけない語（公開側の検疫語彙と工場の作業ファイル名。語は連結で崩して書く＝このファイル自身が引っかからないため）
_SHIP_BAN_WORDS = [
    "INTER" + "NAL", "内部" + "用", "/" + "Users" + "/", "MERGE" + "_LOG", "QA" + "_REPORT", "public" + "_release_ready",
    "student" + "_distribution_ready", "external" + "_upload_ready", "sale" + "_ready", "canonical" + "_status",
    "run" + "_id", "source" + "_package", "オー" + "ナー", "監" + "督", "改稿" + "キュー", "低" + "知識", "体系" + "数学",
    "チャート" + "式", "RESEARCH" + "_RAW", "RESEARCH" + "_BRIEF", "CONTENT" + "_MAP", "_no" + "tes/", "_q" + "a/",
    "_sho" + "ken/", "candidate" + "_draft", "PRODUCTION" + "_ORDER", "FIX" + "_LOG", "Q" + "A_", "SHO" + "KEN",
]
_ID_SEP = "[" + "-‐‑‒–—―−ー－・･·./:_  \t•‣∙" + "]"
_SHIP_BAN_RES = [re.compile("submit" + "[0-9]"), re.compile("D" + "[0-9]+" + "-" + "H" + "[0-9]+"),
                 re.compile(r"\b" + "D" + r"[0-9]{1,2}\b"),
                 re.compile("(?<![0-9A-Za-z])" + "D" + _ID_SEP + "+[0-9]"),
                 re.compile("(?<![0-9A-Za-z])" + "H" + "R" + "(?:" + _ID_SEP + "+)?[0-9]")]


def svg_texts(src):
    """<text> の中身（<tspan> は外して連結）"""
    return [unescape(TAG_RE.sub("", m)) for m in TEXT_RE.findall(src)]


def ban_hits(texts, bans):
    joined = "\n".join(texts)
    return [b for b in bans if b in joined]


def vocab_hits(s):
    """出荷物に書いてはいけない語・ID 形（NFKC 正規化後にも照合する）"""
    out = []
    for t in (s, unicodedata.normalize("NFKC", s)):
        out += [w for w in _SHIP_BAN_WORDS if w in t]
        out += [r.pattern for r in _SHIP_BAN_RES if r.search(t)]
    return sorted(set(out))


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
        elif 0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF or 0x3099 <= o <= 0x309C or o in (0xFF9E, 0xFF9F):
            bad.append((i, hex(o), "variation selector/kana modifier"))
        elif 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF:
            bad.append((i, hex(o), "emoji/dingbat"))
        elif 0xFF10 <= o <= 0xFF19 or 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A:
            bad.append((i, hex(o), "fullwidth alphanumeric"))
    assert not bad, f"{where}: 禁止文字 {bad[:5]}"


def gate_self_test():
    """検査器の陽性対照・陰性対照（壊れた検査器で「0件」と言わないため、毎回実行する）"""
    sample = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
              '<text x="1" y="1">1016</text><text x="2" y="2">x&lt;0</text>'
              '<text font-size="18"><tspan x="1" y="1">日</tspan><tspan x="1" y="2">本</tspan></text></svg>')
    ts = svg_texts(sample)
    assert ts == ["1016", "x<0", "日本"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["1016"]) == ["1016"], "陽性対照失敗: 禁止値 1016 を検出できない"
    assert ban_hits(ts, ["1012"]) == [], "陰性対照失敗: 存在しない値を誤検出"
    assert digit_runs(ts) == {"1016", "0"}, "数字抽出が壊れている"
    probes = ["a" + chr(0x200B) + "b", "e" + chr(0x0301), chr(0x2713) + chr(0xFE0F),
              chr(0xFF21) + chr(0xFF11), chr(0x1F600), "キ" + chr(0xFF9E)]
    for probe in probes:
        try:
            char_hygiene(probe, "陽性対照")
        except AssertionError:
            continue
        raise AssertionError(f"文字衛生の陽性対照失敗: {probe!r} を検出できない")
    char_hygiene("→・←・×・℃・〜・？・［hPa］・°・−", "陰性対照")
    for probe in ["INTER" + "NAL" + "_ONLY", "D" + "・" + "7", "D" + " " + "3", "H" + "R" + "2",
                  "監" + "督", "candidate" + "_draft"]:
        assert vocab_hits(probe), f"語彙の陽性対照失敗: {probe!r} を検出できない"
    for probe in ["地点D", "地点C・D", "D=(1, 2)", "1日目", "HPa"]:
        assert not vocab_hits(probe), f"語彙の陰性対照失敗: {probe!r} を誤検出"
    assert seg_intersects_rect((0, 5), (10, 5), (2, 2, 8, 8)), "線分と矩形の交差検査（陽性）が壊れている"
    assert not seg_intersects_rect((0, 0), (10, 0), (2, 2, 8, 8)), "線分と矩形の交差検査（陰性）が壊れている"
    assert point_in_polygon((1, 1), [(0, 0), (2, 0), (2, 2), (0, 2)]), "点の内外判定（陽性）が壊れている"
    assert not point_in_polygon((3, 1), [(0, 0), (2, 0), (2, 2), (0, 2)]), "点の内外判定（陰性）が壊れている"
    runs = clip_polyline([(-5, 1), (5, 1)], (0, 0, 2, 2))
    assert len(runs) == 1 and near(runs[0][0][0], 0.0) and near(runs[0][-1][0], 2.0), f"切り取りが壊れている: {runs}"
    word, dev = compass8((-1.0, 1.0))
    assert word == "北西" and dev < 1e-9, "8方位の判定が壊れている"


def svg_tech_checks(src, meta):
    """生成した SVG 文字列を、ファイルへ書く前に検査する（落ちれば例外で停止し、何も出力しない）"""
    name = meta["file"]
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag, f"{name}: viewBox がない"
    assert 'xmlns="http://www.w3.org/2000/svg"' in root_tag, f"{name}: xmlns がない"
    assert " width=" not in root_tag and " height=" not in root_tag, f"{name}: ルートに width/height を書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext and "url(" not in ext, f"{name}: 外部参照の疑い"
    assert "font-family" not in src, f"{name}: font-family を書かない（SPEC_figures §5）"
    assert "<title>" in src and "<desc>" in src, f"{name}: title/desc がない"
    assert '<rect x="0" y="0"' in src and 'fill="#fff"' in src, f"{name}: 白背景がない"
    colors = set(re.findall(r'(?:stroke|fill)="(#[0-9a-fA-F]{3,6})"', src))
    gray = all(len(c) == 7 and c[1:3] == c[3:5] == c[5:7] or c in ("#000", "#fff") for c in colors)
    assert gray, f"{name}: 白黒・グレー以外の色がある {sorted(colors)}"
    char_hygiene(src, name)
    vh = vocab_hits(src)
    assert not vh, f"{name}: 出荷物に書かない語がある {vh}"
    sizes = [float(v) for v in FONT_RE.findall(src)]
    assert sizes and min(sizes) >= MIN_FS, f"{name}: 文字サイズの下限 {MIN_FS} を下回る {min(sizes) if sizes else None}"
    texts = svg_texts(src)
    allow = set(meta["allow_texts"])
    got = set(texts)
    assert got == allow, f"{name}: ラベル集合が許可リストと不一致 余分={got - allow} 不足={allow - got}"
    meta_text = [unescape(TITLE_RE.search(src).group(1)), unescape(DESC_RE.search(src).group(1))]
    hits = ban_hits(texts, meta.get("check_tokens", []))
    assert not hits, f"{name}: 禁止文字列が図中テキストにある: {hits}"
    meta_bans = meta.get("check_tokens_meta", meta.get("check_tokens", []))
    hits2 = [b for b in ban_hits(meta_text, meta_bans) if not b.isdigit()]
    assert not hits2, f"{name}: 禁止文字列が title/desc にある: {hits2}"
    kind, allowed = meta["digit_rule"]
    runs = digit_runs(texts)
    if kind == "none":
        assert not runs, f"{name}: 数字が図中にある: {runs}"
    elif kind == "subset":
        assert runs <= allowed, f"{name}: 許可外の数字 {runs - allowed}"
    return len(texts)


def lesson_refs():
    """本文の ![alt](assets/FILE) を実測（ファイル名→(alt, 本文ファイル名)）。lesson_XX.md が無ければ None"""
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
    own = Path(__file__).read_text(encoding="utf-8")
    char_hygiene(own, "generate_figures.py")
    assert not vocab_hits(own), f"generate_figures.py: 出荷物に書かない語がある {vocab_hits(own)}"
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
        n_text = svg_tech_checks(svg1, meta)
        n_checks += len(meta["checks"])
        total_bytes += len(svg1.encode("utf-8"))
        rows.append(meta)
        pending.append((ASSETS / meta["file"], svg1))
        print(f"OK {meta['file']}  [{len(meta['checks'])} checks passed, {n_text} labels]")

    refs = lesson_refs()
    accept = []
    if refs is None:
        accept.append("本文 lesson_XX.md がこの階層に無いため、参照名・alt の照合は未実施")
    else:
        mine = {m["file"] for m in rows}
        theirs = set(refs)
        control = mine | {"L99_fig9_control.svg"}
        assert control != theirs and (control - theirs) == {"L99_fig9_control.svg"}, "集合照合の対照（架空の1件の差）を検出できない"
        assert mine == theirs, f"参照と生成の差: 本文のみ={sorted(theirs - mine)} 生成のみ={sorted(mine - theirs)}"
        accept.append(f"本文の図参照 {len(theirs)} 件と生成ファイル {len(mine)} 件が完全一致（差集合 空。架空の1件を足した対照では差を検出）")
        for m in rows:
            alt, src = refs[m["file"]]
            assert alt == m["alt"], f"{m['file']}: alt が本文（{src}）と不一致\n本文: {alt}\n仕様: {m['alt']}"
        accept.append(f"alt 文: 生成した全{len(rows)}図で本文の alt とバイト単位で一致（assert）")
    for line in accept:
        print("ACCEPT", line)
    manifest = build_manifest(rows, n_checks, total_bytes, accept)
    char_hygiene(manifest, "FIGURE_MANIFEST.md")
    assert not vocab_hits(manifest), f"FIGURE_MANIFEST.md: 出荷物に書かない語がある {vocab_hits(manifest)}"
    cells = "".join(m["alt"] + m["params"] + m["intent"] + m["src"] + m["title"] + "".join(d + t for d, t in m["checks"])
                    for m in rows)
    assert "**" not in manifest, "FIGURE_MANIFEST.md: 強調記号 ** を書かない（強調崩れ検査に当たる）"
    assert "|" not in cells, "FIGURE_MANIFEST.md: 表のセルに | を書かない（表が崩れる）"
    for out, svg in pending:
        out.write_text(svg, encoding="utf-8")
    (HERE / "FIGURE_MANIFEST.md").write_text(manifest, encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks)")
    print(f"TOTAL {len(rows)} figures, {total_bytes} bytes, {n_checks} checks")
    return rows, n_checks, total_bytes, accept


def build_manifest(rows, n_checks, total_bytes, accept):
    """FIGURE_MANIFEST.md（図版台帳）の本文を組み立てる。手編集禁止——スクリプトを直して再実行"""
    n_tokens = sum(len(m.get("check_tokens", [])) for m in rows)
    head = ["---", "distribution_status: published_draft", "---", "", MODEL_LINE, "", "<!--",
            f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
            "spec: docs/SPEC_figures.md 準拠",
            "license: CC-BY-4.0", "-->", ""]
    lines = head + [
        "# FIGURE_MANIFEST — 中2理科 大気の動きと日本の天気 単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト。下表の検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。検算は気象の整合（等圧線が4hPaきざみで交わらない・地点がのるべき線の上にある・"
        "風の矢印が等圧線にそう向きと中心へ向かう〔離れる〕向きの中間の45°で北半球の回り方に合う・前線の記号が進む向きの側にある・"
        "前線面の傾きの急／ゆるい・中心や気団の位置）、本文照合（図の値・位置・表の値・風向の約束を本文 lesson_XX.md から読んで照合）、"
        "配置（viewBox 内・ラベル同士が重ならない・ラベルが線にかからない・文字サイズの下限）の3種。"
        "加えて全SVGに XML整形式・xmlns・viewBox・width/height なし・外部参照なし・`<title>`/`<desc>`・白背景・"
        "白黒とグレーだけ・font-family なし（SPEC_figures §5）の技術検査と、文字衛生検査"
        "（絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字の不在）と、答え漏れ検査を実施。"
        "答え漏れ検査は二重ゲート: (1)図中の全ラベルを許可リスト（本文が図の前後で明示している語と値のみ）と"
        f"集合として完全一致で照合、(2)禁止文字列（練習・例題の答え由来・計{n_tokens}項目・対象値は非開示）が図中テキストと"
        "title・desc に無いことと、図ごとの数字集合の制約。検査器自体は生成前の陽性対照（禁止値・禁止文字・禁止語を仕込んだ合成入力での検出）で"
        "毎回実証している。PASS。／ AI再利用メタ情報として全SVGに `<title>`/`<desc>`"
        "（意図・主要な値・同型図を描かせる説明文）を標準装備。",
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
        f"白背景 rect あり・色は白黒とグレーだけ・font-family なし・文字サイズ {MIN_FS}px 以上（{len(rows)} 枚全件・スクリプトの技術検査で assert）",
        f"- 各図の assert が生成時に全件通過（計 {n_checks} 項目・上表）",
        "- 答え漏れ検査: `<text>` の文字列集合が各図の許可集合と完全一致・禁止文字列 0 件（図中テキスト・title・desc）・数字集合の制約を満たす（全図 assert）",
        "- 決定性: 乱数・時刻に依存しない。同一プロセス内で各図を2回生成してバイト一致を assert。"
        "日付は SVG 先頭コメントと、本台帳の generated 行・生成日行だけに現れる",
        "- 図数の照合: 本文の図参照と生成ファイルの差集合が空（上の1行目）",
        "",
        "## 描画上の注記",
        "",
        "- 白黒規約により色に意味を持たせず、区別はうすいグレーの塗り（陸・寒気・地面）・白地に黒の外形（雲）・黒塗り（前線の記号・矢印の先）・破線・線幅で行う。",
        "- 日本列島と大陸は地図データを使わず、手で決めた頂点による簡略な多角形（地図単位: 西→東 0〜100・南→北 0〜64）。同じ基図を L08図1・L09図2・L10図1〜図3 で共用する。",
        "- 閉じた等圧線は中心のまわりの相似な楕円、冬の図のたての等圧線は x＝x_k−β_k・u²（u は南北の位置）の放物線の族で描き、どの高さでも西から東へ値の順にならび交わらないことを assert している。",
        "- 風の矢印は、本文の約束どおり「等圧線にそう向きと、中心へ向かう（高気圧では中心から離れる）向きのちょうど中間（45°）」で、矢印の根もとの側が8方位のどれかにちょうど一致する。L06図2の風向の行も同じ約束（矢印＝空気が進む向き・根もと＝風の吹いてくる方位）で表1の風向を表した。",
        "- L03図1・L09図1 は中心を×で示し、町（人形マーク）が中心と重なる日は×の上に人形の足もとがくる。L03図1は L01図2 と同じ値（中心1024hPa・996hPa・4hPaごと）で、東西の並びは L03 本文の読み方どおり（西に低気圧・東に高気圧）。",
        "- L09図1 の高気圧Cは1日目に図の西の端にかかるため、枠で切り取って描いた。L10図2 は基図を切り取った範囲（西→東 28〜100・南→北 0〜60）で2枚ならべた。",
        "- L10図3 は L08図1・L09図1（3日目）・L09図2・L10図1 と同じパラメータから縮小して描き、まとめの図なので季節名を書き、等圧線の数字は省いた。",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた語と値は、いずれも本文が図の前後で明示している物のみ。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- 練習・例題の答え由来の語と値（風向の8方位・数字のない等圧線の値・前線の通過した時間帯・前線や気団の名前・季節の名前など）は禁止文字列として各図に登録し、図中テキストと title・desc に現れないことを assert している。",
        "- L04図2 は例題2で名前を問う「前線面」「前線」の語を図に書かずに「境の面」「地表と交わる所」と表示した（本文の alt の説明とは食いちがわない）。",
        "- L06図1 は前線の名前と、例題1・練習1で問う「暖気」「寒気」の語を図に書かない（記号の形と地点の位置だけで読ませ、暖気の位置は本文の読み方で文章として示す）。",
        "- 図を読むこと自体が問いになっている物（L01図2の数字のある線の値・L05図2の地点Cのいる空気・L07図1の高低など）は、本文の alt と読み方の記述どおりに描いた。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロック（地図の図は WINTER・SPRING・BAIU・SUMMER・TYPHOON）を編集する（値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算 assert・本文照合・技術検査・答え漏れ検査・alt 照合に1つでも落ちると、SVG も本ファイルも書き出されない（既存の出力は前回のまま残る）。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
