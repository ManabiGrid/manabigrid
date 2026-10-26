#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高校数学Ⅱ「いろいろな式」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（白黒とグレーだけ・font-family なし・xmlns と viewBox・
title/desc・白背景・答え非記載・コード来歴）。各図の内容仕様（各 fig_* 関数冒頭のパラメータ
ブロック・Checker の検算項目・台帳の記載）は本文 lesson_XX.md と一致させる。描画ヘルパーと
検査器の組み立て（Canvas・Checker・許可リスト検査・禁止文字列検査・陽性対照・台帳の自動生成）は
先行単元（数学A「場合の数と確率」・数学Ⅰ「数と式」「二次関数」）の generate_figures.py の型を踏襲し、
等角投影の立体・筆算の段組み・点の図・入れ子の枠の部品は本単元向けに書き下ろした。

- 実行: python3 generate_figures.py（この階層を作業フォルダにして実行する）
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（11枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（datetime / fractions / html / itertools / math / pathlib / re /
  unicodedata / xml.etree）
- 決定性: 乱数・時刻に依存しない。日付は SVG 先頭コメントと台帳の generated 行・生成日行だけに現れる。
  台帳に載せる集合は整列してから書く（実行ごとの要素順の揺れを出さない）。
- 自己検証（1つでも落ちると例外で停止し、SVG も台帳も書き出さない）:
  (1) 図ごとの Checker——数学の検算（展開・割り算の各段・恒等式・判別式・相加相乗平均の値・
      三次方程式の解など）と描画の幾何（等角投影の重なり順・ラベルが見える面の上にあること・
      入れ子の包含・点と目盛りの位置）。
  (2) 本文照合——図のパラメータ（式・値・表）が本文 lesson_XX.md にそのまま書かれていることを、
      本文を読んで照合する（本文を直したら、このスクリプトも直すこと）。
  (3) 答えの分離（二重ゲート＋陽性対照）——各図の <text> の文字列集合が、パラメータブロックで
      宣言した許可リストと完全一致すること、練習と stretch の答え由来の禁止文字列が図中テキストと
      title・desc に無いこと、図ごとの数字集合の制約。検査器は main() 冒頭の陽性対照で毎回実証する。
  (4) 配置検査——全要素が viewBox 内・ラベル同士が重ならない・ラベルが線にかからない・
      文字サイズが viewBox 幅の3%以上。
  (5) 文字衛生と公開語彙——絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字と、
      公開側の検疫語彙を、本スクリプト自身と全 SVG・台帳について機械検査する。
  (6) 受け入れ——本文の図参照の集合と生成ファイルの集合の完全一致、alt 文のバイト一致。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの値を変えて再実行する。
  値は該当レッスン本文（lesson_XX.md）と一致させること。SVG の直接編集は禁止（来歴が切れる）。
"""

import datetime
import itertools
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from fractions import Fraction as Fr
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSON_DIR = HERE.parent          # lesson_XX.md はこの階層（公開側の単元フォルダでも同じ）
GENERATED = datetime.date.today().isoformat()
MODEL_LINE = "実行モデル: claude-opus-5-5（親指定・effort max・親が実走記録で照合）"

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------------
W = 640            # 全図共通の viewBox 幅
FS = round(W * 0.03)   # 基本文字サイズ＝viewBox 幅の3%（19px）
MIN_FS = FS        # 文字サイズの下限（assert）
MAIN_W = 1.6       # 主線幅
BOLD_W = 3.2       # 強調線幅
AUX_W = 1.1        # 補助線幅（破線）
DASH = "6 4"       # 破線
THIN_W = 1.0       # 細線（目盛り・区切り）
AXIS_W = 1.2       # 座標軸
DOT_R = 3.2        # 点マーカー半径
DOT_R_END = 3.4    # 数直線の●（数学Ⅰ「数と式」の数直線系と同じ値）
SHADE = "#d9d9d9"  # うすい網かけ
SHADE2 = "#b3b3b3" # 濃い網かけ
SHADE3 = "#efefef" # ごくうすい網かけ
C30 = math.cos(math.radians(30))
# font-family は書かない（docs/SPEC_figures.md §5。書体は閲覧環境に任せる）


# ===========================================================================
# 幾何ユーティリティ（px 座標: x=右・y=下）
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


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


def convex_hull(pts):
    """凸包（単調連鎖法）。頂点を一周の順に返す"""
    P = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
    if len(P) <= 2:
        return P

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and cross(sub(h[-1], h[-2]), sub(p, h[-2])) <= 0:
                h.pop()
            h.append(p)
        return h

    lower = half(P)
    upper = half(list(reversed(P)))
    return lower[:-1] + upper[:-1]


def poly_orient(poly):
    s = 0.0
    for i in range(len(poly)):
        s += cross(poly[i], poly[(i + 1) % len(poly)])
    return 1.0 if s > 0 else -1.0


def in_convex(p, poly, margin=0.0):
    """点 p が凸多角形 poly の内側に margin(px) 以上入っているか"""
    o = poly_orient(poly)
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        L = dist(a, b)
        if L == 0:
            continue
        if o * cross(sub(b, a), sub(p, a)) / L < margin:
            return False
    return True


def rect_poly(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def convex_overlap(A, B, eps=0.5):
    """凸多角形どうしが eps(px) を超えて重なるか（分離軸定理）。辺が接するだけなら False"""
    for poly in (A, B):
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            ax = unit((-(q[1] - p[1]), q[0] - p[0]))
            pa = [dot(v, ax) for v in A]
            pb = [dot(v, ax) for v in B]
            if max(pa) <= min(pb) + eps or max(pb) <= min(pa) + eps:
                return False
    return True


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


def inside_rect(inner, outer):
    """矩形 (x, y, w, h) inner が outer の厳密に内側か"""
    return (outer[0] < inner[0] and inner[0] + inner[2] < outer[0] + outer[2] and
            outer[1] < inner[1] and inner[1] + inner[3] < outer[1] + outer[3])


def disjoint_rect(r1, r2):
    return (r1[0] + r1[2] <= r2[0] or r2[0] + r2[2] <= r1[0] or
            r1[1] + r1[3] <= r2[1] or r2[1] + r2[3] <= r1[1])


def pt_in_rect(p, r):
    return r[0] < p[0] < r[0] + r[2] and r[1] < p[1] < r[1] + r[3]


# ===========================================================================
# 数の表記と多項式（係数リストは低次→高次・厳密な有理数演算）
# ===========================================================================
def fmt(v):
    """数を本文の表記で（負号は U+2212。整数は小数点なし）"""
    v = Fr(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return s.replace("-", "−")


def poly_mul(p, q):
    r = [Fr(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] += Fr(a) * Fr(b)
    return r


def poly_add(p, q):
    n = max(len(p), len(q))
    return [Fr(p[i] if i < len(p) else 0) + Fr(q[i] if i < len(q) else 0) for i in range(n)]


def poly_trim(p):
    p = [Fr(c) for c in p]
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p


def poly_eval(p, x):
    return sum(Fr(c) * Fr(x) ** i for i, c in enumerate(p))


def poly_pow(p, n):
    r = [Fr(1)]
    for _ in range(n):
        r = poly_mul(r, p)
    return r


def poly_term(c, deg, lead):
    """係数 c・次数 deg の項を本文の表記で（先頭の項は＋を付けない・係数1は省く）"""
    c = Fr(c)
    sign = "−" if c < 0 else ("" if lead else "＋")
    a = abs(c)
    var = {0: "", 1: "x", 2: "x²", 3: "x³"}[deg]
    coef = "" if (a == 1 and deg > 0) else fmt(a)
    return sign + coef + var


def school_int_division(N, dv):
    """整数の筆算（小学校の手順）。戻り値: 商の各桁 {桁位置: 数字}・段の並び・余り。
    段は ("prod"|"rem", 値, 右端の桁位置)。桁位置は割られる数の左から 0, 1, 2, …"""
    digits = [int(ch) for ch in str(N)]
    qd, rows = {}, []
    cur, started = 0, False
    for idx, dg in enumerate(digits):
        cur = cur * 10 + dg
        if not started and cur < dv:
            continue
        started = True
        q = cur // dv
        qd[idx] = q
        rows.append(("prod", q * dv, idx))
        cur -= q * dv
        if idx + 1 < len(digits):
            rows.append(("rem", cur * 10 + digits[idx + 1], idx + 1))
        else:
            rows.append(("rem", cur, idx))
    return qd, rows, cur


def school_poly_division(A, B):
    """多項式の筆算。A, B は係数リスト（高次→低次）。戻り値: 商 {次数: 係数}・段の並び・余り。
    段は ("prod"|"rem", {次数: 係数})。rem の段は「引いた結果＋次に下ろした項」"""
    n, m = len(A) - 1, len(B) - 1
    work = {n - i: Fr(c) for i, c in enumerate(A)}
    quot, rows = {}, []
    for d in range(n - m, -1, -1):
        lead = d + m
        c = work.get(lead, Fr(0)) / Fr(B[0])
        quot[d] = c
        prod = {lead - i: c * Fr(B[i]) for i in range(m + 1)}
        rows.append(("prod", prod))
        for k, v in prod.items():
            work[k] = work.get(k, Fr(0)) - v
        low = d - 1 if d > 0 else 0
        rows.append(("rem", {k: work.get(k, Fr(0)) for k in range(lead - 1, low - 1, -1)}))
    rem = {k: work.get(k, Fr(0)) for k in range(m - 1, -1, -1)}
    return quot, rows, rem


def terms_of(dct):
    """{次数: 係数} を次数の高い順の (次数, 表記) の並びにする（係数0の項は書かない）"""
    out, lead = [], True
    for deg in sorted(dct, reverse=True):
        c = dct[deg]
        if c == 0:
            continue
        out.append((deg, poly_term(c, deg, lead)))
        lead = False
    return out


# ===========================================================================
# 文字幅の推定・数字の抽出
# ===========================================================================
_SPECIAL_W = {" ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4, "→": 1.0, "←": 1.0,
              "・": 1.0, "×": 1.0, "÷": 1.0, "〜": 1.0, "−": 1.0, "√": 1.0, "≧": 1.0, "≦": 1.0,
              "=": 0.6, "<": 0.6, ">": 0.6}


def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・あいまい幅 0.7em・記号は個別（大きめに見積もる）"""
    w = 0.0
    for ch in s:
        if ch in _SPECIAL_W:
            w += _SPECIAL_W[ch]
        elif ord(ch) < 128:
            w += 0.6
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 1.0
        else:
            w += 0.7
    return w * size


def digit_runs(texts):
    """ラベル群に含まれる数字の連なり（「4C2=6」→ {"4", "2", "6"}）"""
    out = set()
    for t in texts:
        out.update(re.findall(r"[0-9]+", t))
    return out


def show_set(s):
    """集合を整列した文字列にする（台帳に載せる detail 用。要素順の揺れを消す）"""
    return "{" + ", ".join(sorted(s, key=lambda t: (len(t), t))) + "}"


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

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, oid="line", color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w)
        self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')
        self.obstacle(oid, [(x1, y1), (x2, y2)])

    def path(self, pts, w=MAIN_W, dash=None, close=False, fill="none", oid="line", join="round",
             color="#000"):
        """折れ線（close=True なら多角形）。fill を指定すると塗りつぶし＋輪郭"""
        for x, y in pts:
            self._grow(x, y, w / 2.0)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="{fill}" stroke="{color}" '
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

    def rect(self, x, y, w, h, fill="none", sw=1.4, dash=None, oid="line"):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], w=sw, dash=dash, close=True,
                  fill=fill, oid=oid, join="miter")

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, own=(), clear=True):
        """(x, y) はベースライン。推定ボックスを記録する"""
        w = est_w(s, size)
        x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        box = (x0, y - 0.8 * size, x0 + w, y + 0.22 * size)
        self.texts.append((box[0], box[1], box[2], box[3], s, tuple(own), clear))
        self.font_sizes.append(size)
        self._grow(box[0], box[1])
        self._grow(box[2], box[3])
        wgt = f' font-weight="{weight}"' if weight else ""
        self.overlay.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                            f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')
        return box

    def arrow(self, x1, y1, x2, y2, w=1.4, head=8.0, oid="arrow"):
        """px 座標の矢印（線＋先端の三角形）"""
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, w=w, oid=oid)
        nx, ny = -math.sin(ang), math.cos(ang)
        pts = [(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
               (bx - nx * head * 0.45, by - ny * head * 0.45)]
        self.fill_poly(pts, "#000")
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
        ck.ok("ラベルが線（軸・曲線・枠・矢印・点）にかからない", not hits, f"{hits}")
        ck.ok(f"文字サイズがすべて {MIN_FS}px 以上（viewBox 幅の3%）",
              bool(self.font_sizes) and min(self.font_sizes) >= MIN_FS,
              f"min={min(self.font_sizes) if self.font_sizes else None}")

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


class Frame:
    """数学座標（y 上向き）→ px: x_px = ox + sx*x, y_px = oy - sy*y（(ox, oy) は原点の px）"""
    def __init__(self, ox, oy, sx, sy=None):
        self.ox, self.oy, self.sx = ox, oy, sx
        self.sy = sx if sy is None else sy

    def P(self, p):
        return (self.ox + self.sx * float(p[0]), self.oy - self.sy * float(p[1]))


def draw_axes(cv, lb, fr, xr, yr, xlabel="x", ylabel="y", origin="O", x_step=1, y_step=1,
              xnums=(), ynums=(), xticks=True, yticks=True):
    """座標軸: 矢印つき軸線・目盛り・指定した数値ラベル・原点 O（ラベルは lb に登録）"""
    (x0, x1), (y0, y1) = xr, yr
    ax0, ax1 = fr.P((x0, 0)), fr.P((x1, 0))
    cv.arrow(ax0[0], ax0[1], ax1[0] + 10, ax1[1], w=AXIS_W, oid="axis")
    by0, by1 = fr.P((0, y0)), fr.P((0, y1))
    cv.arrow(by0[0], by0[1], by1[0], by1[1] - 10, w=AXIS_W, oid="axis")
    if xlabel:
        lb.put(ax1[0] + 16, ax1[1] + FS * 0.35, xlabel, anchor="start")
    if ylabel:
        lb.put(by1[0] + 9, by1[1] - 6, ylabel, anchor="start")
    if xticks:
        t = math.ceil(x0 / x_step) * x_step
        while t <= x1 + 1e-9:
            if abs(t) > 1e-9:
                px, py = fr.P((t, 0))
                cv.line(px, py - 3.5, px, py + 3.5, w=THIN_W, oid="tick")
            t += x_step
    if yticks:
        t = math.ceil(y0 / y_step) * y_step
        while t <= y1 + 1e-9:
            if abs(t) > 1e-9:
                px, py = fr.P((0, t))
                cv.line(px - 3.5, py, px + 3.5, py, w=THIN_W, oid="tick")
            t += y_step
    for v in xnums:
        px, py = fr.P((v, 0))
        lb.put(px, py + 5 + FS, fmt(v))
    for v in ynums:
        px, py = fr.P((0, v))
        lb.put(px - 7, py + FS * 0.35, fmt(v), anchor="end")
    if origin:
        px, py = fr.P((0, 0))
        lb.put(px - 6, py + 5 + FS, origin, anchor="end")


def curve_pts(fr, f, xa, xb, n=240):
    """y=f(x) を [xa, xb] でサンプリングした px の点列"""
    return [fr.P((xa + (xb - xa) * i / n, f(xa + (xb - xa) * i / n))) for i in range(n + 1)]


def parabola_span(p, q, y_top, xlo, xhi):
    """y=(x−p)²＋q を上端 y_top まで描くときの x の範囲（視野内に切り詰める）"""
    h = math.sqrt(max(0.0, y_top - q))
    return max(xlo, p - h), min(xhi, p + h)


def lesson_text(n):
    """lesson_NN.md の本文（無ければ None）"""
    f = LESSON_DIR / f"lesson_{n:02d}.md"
    return f.read_text(encoding="utf-8") if f.exists() else None


def body_has(ck, n, needles, what):
    """本文 lesson_NN.md に needles（図のパラメータから組み立てた文字列）が全部あることを照合する"""
    t = lesson_text(n)
    if t is None:
        ck.ok(f"本文照合（{what}）: lesson_{n:02d}.md がこの階層に無いため未実施", True)
        return
    miss = [s for s in needles if s not in t]
    ck.ok(f"本文照合（{what}）: lesson_{n:02d}.md に {len(needles)} 件の文字列がそのままある",
          not miss, f"欠落={miss}")


def allow_check(ck, lb, allow):
    got, want = set(lb.items), set(allow)
    ck.ok(f"図中ラベルの集合が、パラメータブロックで宣言した許可リスト（{len(want)}種）と一致",
          got == want, f"余分={sorted(got - want)} 不足={sorted(want - got)}")


# ===== 図の関数はこの下 =====================================================
def put_c(lb, x, y, s, **kw):
    """(x, y) を文字の推定ボックスの中心にして置く"""
    return lb.put(x, y + 0.29 * (kw.pop("size", None) or FS), s, **kw)


# ===========================================================================
# L01: (a＋b)³ の立体分割（等角投影）
# ===========================================================================
def iso_box(org, dims):
    """直方体の見える3面（上面・x の正の側の面・y の正の側の面）と8頂点（3次元座標）"""
    x0, y0, z0 = org
    dx, dy, dz = dims
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz
    top = [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    right = [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]
    left = [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    corners = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    return top, right, left, corners


def boxes_overlap3d(o1, d1, o2, d2):
    """軸に平行な直方体どうしが内部で重なるか"""
    return all(o1[t] < o2[t] + d2[t] and o2[t] < o1[t] + d1[t] for t in range(3))


def fig_L01_1():
    # --- パラメータ（lesson_01.md §2「公式1を立体で見ておこう」の段落） ---
    a, b = Fr(3), Fr(2)            # 描画用の辺の比 a:b=3:2（a, b が正の場合の見取り図。数値の例ではない）
    S = 23.0                       # 1単位の長さ（px）
    gap = Fr(4, 5)                 # 分解図の横のすき間（単位）
    lift = a + b + gap + Fr(1, 2)  # 分解図で上の段を持ち上げる高さ（単位）
    fills = {"a³": "#a6a6a6", "a²b": "#d0d0d0", "ab²": "#ececec", "b³": "#fff"}   # 種類ごとに1色（面ごとの陰影はつけない）
    names = {3: "a³", 2: "a²b", 1: "ab²", 0: "b³"}   # a の長さの辺の本数 → 体積の式
    cube_caption = "1辺 a＋b の立方体"
    count_caption = "a³ が1個・a²b が3個・ab² が3個・b³ が1個"
    allow = ["a", "b", cube_caption, "8個に", "分ける", "a³", "a²b", "ab²", "b³", count_caption]

    L = {0: a, 1: b}
    O = {0: Fr(0), 1: a}
    pieces = []
    for i, j, k in itertools.product((0, 1), repeat=3):
        idx = (i, j, k)
        pieces.append({"idx": idx, "dims": (L[i], L[j], L[k]), "org": (O[i], O[j], O[k]),
                       "exp": (O[i] + gap * i, O[j] + gap * j, O[k] + lift * k),
                       "name": names[idx.count(0)]})
    n = a + b

    ck = Checker()
    vols = [p["dims"][0] * p["dims"][1] * p["dims"][2] for p in pieces]
    ck.ok("8個の直方体の体積の和が立方体の体積 (a＋b)³ に等しい（描画の比 a:b=3:2 で厳密計算）",
          sum(vols) == n ** 3, f"{sum(vols)}={n ** 3}")
    ck.ok("8個は立方体の中で互いに重ならない（切り分けた位置で）",
          not any(boxes_overlap3d(p["org"], p["dims"], q["org"], q["dims"])
                  for p, q in itertools.combinations(pieces, 2)))
    cnt = {s: sum(1 for p in pieces if p["name"] == s) for s in names.values()}
    ck.ok("体積の式ごとの個数が a³:1・a²b:3・ab²:3・b³:1（本文の個数）",
          cnt == {"a³": 1, "a²b": 3, "ab²": 3, "b³": 1}, f"{cnt}")
    ck.ok("各直方体の式は辺の長さの積（a の辺の本数が指数）",
          all(p["dims"][0] * p["dims"][1] * p["dims"][2] ==
              a ** p["idx"].count(0) * b ** p["idx"].count(1) for p in pieces))
    dir_b = sorted(p["dims"].index(b) for p in pieces if p["name"] == "a²b")
    dir_a = sorted(p["dims"].index(a) for p in pieces if p["name"] == "ab²")
    ck.ok("a²b の3個は長さ b の辺がそれぞれ別の軸に1本ずつ（ab² の3個も同様に長さ a の辺が別の軸）",
          dir_b == [0, 1, 2] and dir_a == [0, 1, 2], f"b の軸={dir_b}・a の軸={dir_a}")
    ck.ok("公式1 (a＋b)³=a³＋3a²b＋3ab²＋b³ を整数の組 (a, b)=(1..6, 1..6) の36組で検算",
          all((u + v) ** 3 == u ** 3 + 3 * u * u * v + 3 * u * v * v + v ** 3
              for u in range(1, 7) for v in range(1, 7)))
    ck.ok("分解図は8個が互いに重ならない", not any(
        boxes_overlap3d(p["exp"], p["dims"], q["exp"], q["dims"]) for p, q in itertools.combinations(pieces, 2)))
    ck.ok("持ち上げる高さ＞a＋b＋すき間（上の段が下の段の上面を隠さない十分条件）",
          lift > a + b + gap, f"lift={float(lift)}")
    body_has(ck, 1, ["1辺 a の立方体が1個（体積 a³）", "1辺 b の立方体が1個（b³）",
                     "a・a・b の直方体が3個（合わせて 3a²b）", "a・b・b の直方体が3個（合わせて 3ab²）",
                     "8個の直方体に分かれる", "(a＋b)³ = a³＋3a²b＋3ab²＋b³"], "個数と公式1")

    def iso(p, ox, oy):
        x, y, z = (float(t) for t in p)
        return (ox + (x - y) * C30 * S, oy + (x + y) * 0.5 * S - z * S)

    cube_corners = [(x, y, z) for x in (0, n) for y in (0, n) for z in (0, n)]
    la = [iso(c, 0, 0) for c in cube_corners]
    le = [iso(c, 0, 0) for p in pieces for c in iso_box(p["exp"], p["dims"])[3]]
    ua0, ua1 = min(u for u, _ in la), max(u for u, _ in la)
    va0, va1 = min(v for _, v in la), max(v for _, v in la)
    ue0, ue1 = min(u for u, _ in le), max(u for u, _ in le)
    ve0, ve1 = min(v for _, v in le), max(v for _, v in le)
    ox_a, ox_e = 28 - ua0, 612 - ue1
    oy_e = 16 - ve0
    oy_a = oy_e + (ve0 + ve1) / 2 - (va0 + va1) / 2
    y_cube_cap = oy_a + va1 + 44
    y_count = max(oy_e + ve1, y_cube_cap) + 46
    H = round(y_count + 16)

    cv = Canvas(W, H)
    lb = Labels(cv)

    # 左: 組み立てた立方体（見える3面を、切り分けた8個の面で塗り分ける）
    A = lambda p: iso(p, ox_a, oy_a)
    face_area = {"top": Fr(0), "right": Fr(0), "left": Fr(0)}
    for p in pieces:
        i, j, k = p["idx"]
        top, right, left, _ = iso_box(p["org"], p["dims"])
        dx, dy, dz = p["dims"]
        if k == 1:
            cv.path([A(q) for q in top], w=THIN_W, close=True, fill=fills[p["name"]], oid="cube")
            face_area["top"] += dx * dy
        if i == 1:
            cv.path([A(q) for q in right], w=THIN_W, close=True, fill=fills[p["name"]], oid="cube")
            face_area["right"] += dy * dz
        if j == 1:
            cv.path([A(q) for q in left], w=THIN_W, close=True, fill=fills[p["name"]], oid="cube")
            face_area["left"] += dx * dz
    ck.ok("見える3面が、それぞれ4枚の面でちょうど埋まる（面積の和＝(a＋b)²）",
          all(v == n * n for v in face_area.values()), f"{ {k2: str(v) for k2, v in face_area.items()} }")
    hull_a = convex_hull(la)
    cv.path([(x + ox_a, y + oy_a) for x, y in hull_a], w=MAIN_W, close=True, oid="cube")
    front = A((n, n, n))
    for q in [(0, n, n), (n, 0, n), (n, n, 0)]:
        e = A(q)
        cv.line(front[0], front[1], e[0], e[1], w=MAIN_W, oid="cube")
    # 辺のラベル（左の縦の辺・左下の辺・右下の辺を a と b に分けて書く）
    edges = [((0, n, 0), (0, n, n), (-1.0, 0.0)),
             ((0, n, 0), (n, n, 0), (-0.5, C30)),
             ((n, 0, 0), (n, n, 0), (0.5, C30))]
    ratio_ok = True
    for p0, p1, nrm in edges:
        axis = [t for t in range(3) if p0[t] != p1[t]][0]
        cut = list(p0)
        cut[axis] = a
        P0, P1, Pc = A(p0), A(p1), A(tuple(cut))
        ratio_ok = ratio_ok and near(dist(P0, Pc) / dist(Pc, P1), float(a / b), 1e-9)
        for (q0, q1, s) in ((P0, Pc, "a"), (Pc, P1, "b")):
            mx, my = (q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2
            off = 13.0 if nrm[1] == 0 else 17.0
            put_c(lb, mx + nrm[0] * off, my + nrm[1] * off, s)
    ck.ok("立方体の3本の辺で、切れ目が長さを a:b=3:2 に分ける（px 長さの比）", ratio_ok)
    put_c(lb, ox_a, y_cube_cap - 0.29 * FS, cube_caption)

    # 右: 分解図（上下2段に分け、すき間をあけて並べる）。奥から手前へ描く
    Ex = lambda p: iso(p, ox_e, oy_e)
    order = sorted(pieces, key=lambda p: (sum(p["idx"]), p["idx"]))
    for m, p in enumerate(order):
        top, right, left, corners = iso_box(p["exp"], p["dims"])
        p["top2d"] = [Ex(q) for q in top]
        p["hull"] = convex_hull([Ex(q) for q in corners])
        for face in (right, left, top):
            cv.path([Ex(q) for q in face], w=1.2, close=True, fill=fills[p["name"]], oid=None)
        cv.obstacle(f"piece{m}", p["hull"] + [p["hull"][0]])
    # 持ち上げた上の段と下の段を、左右の輪郭の角で破線の縦線でつなぐ（持ち上げたことの目印）
    guides = []
    for g0, g1 in (((0, n + gap, a), (0, n + gap, a + lift)), ((n + gap, 0, a), (n + gap, 0, a + lift))):
        P0, P1 = Ex(g0), Ex(g1)
        cv.line(P0[0], P0[1], P1[0], P1[1], w=AUX_W, dash=DASH, oid="guide")
        guides.append((P0, P1))
    ck.ok("持ち上げの目印の縦線2本は、分解図の左端・右端（どの直方体の面にもかからない輪郭の外側）にある",
          all(near(P0[0], P1[0]) and (near(P0[0], ox_e + ue0) or near(P0[0], ox_e + ue1)) for P0, P1 in guides))
    pairs, bad = 0, []
    for u_, v_ in itertools.combinations(range(len(order)), 2):
        p, q = order[u_], order[v_]
        if convex_overlap(p["hull"], q["hull"]):
            pairs += 1
            if not all(q["idx"][t] >= p["idx"][t] for t in range(3)):
                bad.append((p["idx"], q["idx"]))
    ck.ok("重なって見える組は、あとに描く方が必ず手前（添え字が各軸で大きい）＝奥から手前への描き順が正しい",
          not bad, f"重なる組={pairs}・違反={bad}")
    hidden = [p["idx"] for m, p in enumerate(order)
              if any(convex_overlap(p["top2d"], q["hull"]) for q in order[m + 1:])]
    ck.ok("8個すべての上面が、あとから描く直方体に隠されない", not hidden, f"{hidden}")
    lab_bad = []
    for m, p in enumerate(order):
        top3d = iso_box(p["exp"], p["dims"])[0]
        cx = sum(Ex(q)[0] for q in top3d) / 4
        cy = sum(Ex(q)[1] for q in top3d) / 4
        box = put_c(lb, cx, cy, p["name"], clear=False)
        corners = rect_poly(box)
        if not all(in_convex(c, p["top2d"], margin=1.5) for c in corners):
            lab_bad.append(p["name"])
    ck.ok("体積の式のラベル8個は、それぞれ自分の直方体の上面の内側に収まる（縁から1.5px以上）",
          not lab_bad, f"{lab_bad}")

    # 中央の矢印と、下の個数の説明
    y_ar = oy_a
    x_ar0, x_ar1 = ox_a + ua1 + 18, ox_e + ue0 - 18
    ck.ok("矢印は立方体と分解図のあいだに収まる", x_ar1 - x_ar0 > 60, f"{x_ar0:.1f}→{x_ar1:.1f}")
    cv.arrow(x_ar0, y_ar, x_ar1, y_ar, w=MAIN_W, head=10.0)
    xm = (x_ar0 + x_ar1) / 2
    put_c(lb, xm, y_ar - 16 - 1.25 * FS, "8個に")
    put_c(lb, xm, y_ar - 16, "分ける")
    put_c(lb, W / 2, y_count - 0.29 * FS, count_caption)
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L01_fig1_cube_expansion_blocks.svg", "lesson": "L01", "canvas": cv,
            "title": "(a＋b)³ の立体分割——1辺 a＋b の立方体を8個の直方体に切り分ける",
            "desc": ("左に1辺 a＋b の立方体（各辺を a と b に分ける切れ目つき・見える3面を切り分けた面で塗り分け）、"
                     "右にその8個の直方体を上下2段に分けてすき間をあけた等角投影の分解図。上面に体積の式 a³・a²b・ab²・b³ を書き、"
                     "下に a³ が1個・a²b が3個・ab² が3個・b³ が1個とまとめる。塗りは式の種類ごとに1色。"
                     "描画の辺の比は a:b=3:2（a, b が正の場合の見取り図）。同型図は辺の比を差し替えて生成する"),
            "alt": "(a＋b)³の立体分割——1辺a＋bの立方体が、1辺aの立方体1個（a³）、1辺bの立方体1個（b³）、a×a×bの直方体3個（3a²b）、a×b×bの直方体3個（3ab²）の8個に分かれる",
            "intent": "公式1の各項を体積として見せる。数学Ⅰ「数と式」の (a＋b)² の面積図を1つ次元を上げた図で、a³ と b³ の2個だけでは立方体が埋まらないことも読み取れる",
            "src": "lesson_01.md §2（公式1を立体で見る段落の直後）",
            "params": "描画の辺の比 a:b=3:2・1単位 23px・分解図のすき間 0.8・上の段の持ち上げ 6.3（単位）／塗り a³ #a6a6a6・a²b #d0d0d0・ab² #ececec・b³ 白",
            "checks": ck.items,
            "check_tokens": ["x³＋12x²＋48x＋64", "27x³−54x²＋36x−8", "8a³＋36a²b＋54ab²＋27b³", "x³−27", "8a³＋1",
                             "x³＋8y³", "(x−5)(x²＋5x＋25)", "4a²−6ab＋9b²", "3(x＋2)(x²−2x＋4)", "x(x＋1)(x²−x＋1)",
                             "x³＋6x²＋12x＋8", "(x−2)(x²＋2x＋4)", "(x−1)(x²＋4x＋7)", "a²＋b²＋c²−ab−bc−ca",
                             "向き", "3通り", "18"],
            "digit_rule": ("subset", {"1", "3", "8"}),
            "allow_texts": allow}


# ===========================================================================
# L02: 4つのかっこから b を2つ選ぶ選び方の対応図
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（lesson_02.md §2「a²b² の項は…」の段落） ---
    n, r = 4, 2
    col_x = [236, 306, 376, 446]     # 4つのかっこの中心 x（px）
    y_num, y_fac = 34, 76            # かっこの番号の行・かっこの行（ベースライン）
    y_row0, pitch = 136, 40          # 選び方の1行目のベースライン・行の間隔
    cell = 30                        # ますの1辺（px）
    x_rowlab, x_prod, x_br = 196, 488, 558
    fac = "(a＋b)"
    caption = "a²b² の係数は 4C2=6"
    allow = ["1", "2", "3", "4", fac, "1と2", "1と3", "1と4", "2と3", "2と4", "3と4", "a", "b", "a²b²",
             "6通り", caption]

    combos = list(itertools.combinations(range(1, n + 1), r))
    ck = Checker()
    ck.ok("b を選ぶ2つのかっこの組は 1と2・1と3・1と4・2と3・2と4・3と4 の順（本文の並び）",
          combos == [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)], f"{combos}")
    ck.ok("組の数 = 4C2 = 6", len(combos) == math.comb(n, r) == 6)
    pats = list(itertools.product("ab", repeat=n))
    ck.ok("4つのかっこから a か b を選ぶ選び方 2⁴=16 通りのうち、b がちょうど2つのものは6通りで、表の6行と一致",
          len(pats) == 16 and sorted(tuple(i + 1 for i, c in enumerate(p) if c == "b") for p in pats
                                     if p.count("b") == r) == combos)
    coef = poly_pow([1, 1], n)                 # (1＋t)⁴ の係数＝(a＋b)⁴ の aⁿ⁻ʳbʳ の係数
    ck.ok("(a＋b)⁴ を分配法則で展開した a²b² の係数が 6（係数の並び 1, 4, 6, 4, 1）",
          coef == [1, 4, 6, 4, 1] and coef[r] == len(combos), f"{[int(c) for c in coef]}")
    body_has(ck, 2, ["1番目と2番目・1番目と3番目・1番目と4番目・2番目と3番目・2番目と4番目・3番目と4番目の 4C2=6 通り",
                     "a²b² の係数は 6 になる"], "組の並びと係数")

    H = y_row0 + pitch * (len(combos) - 1) + 62
    cv = Canvas(W, H)
    lb = Labels(cv)
    for c, x in enumerate(col_x):
        put_c(lb, x, y_num - 0.29 * FS, str(c + 1))
        cv.rect(x - 33, y_fac - 22, 66, 32, sw=1.2)
        lb.put(x, y_fac, fac)
    cv.line(150, y_fac + 24, 548, y_fac + 24, w=THIN_W)
    rows_ok = True
    for i, cmb in enumerate(combos):
        y = y_row0 + i * pitch
        cy = y - 0.29 * FS
        lb.put(x_rowlab, y, f"{cmb[0]}と{cmb[1]}", anchor="end")
        letters = []
        for c, x in enumerate(col_x):
            chosen = (c + 1) in cmb
            letters.append("b" if chosen else "a")
            cv.rect(x - cell / 2, cy - cell / 2, cell, cell, fill=(SHADE if chosen else "#fff"),
                    sw=(1.6 if chosen else 1.0))
            put_c(lb, x, cy, "b" if chosen else "a", weight=("bold" if chosen else None))
        rows_ok = rows_ok and letters.count("a") == n - r and letters.count("b") == r
        lb.put(x_prod, y, "a²b²", anchor="start")
    ck.ok("どの行も a を2つ・b を2つ掛けて a²b² になる（右端のラベルと一致）", rows_ok)
    y0b, y1b = y_row0 - 0.29 * FS - cell / 2 - 2, y_row0 + pitch * (len(combos) - 1) - 0.29 * FS + cell / 2 + 2
    cv.line(x_br, y0b, x_br, y1b, w=1.4)
    cv.line(x_br - 8, y0b, x_br, y0b, w=1.4)
    cv.line(x_br - 8, y1b, x_br, y1b, w=1.4)
    put_c(lb, x_br + 8 + est_w("6通り", FS) / 2, (y0b + y1b) / 2, "6通り")
    put_c(lb, W / 2, H - 24, caption)
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L02_fig1_choose_b_from_factors.svg", "lesson": "L02", "canvas": cv,
            "title": "(a＋b)⁴ の a²b² の項——4つのかっこのうち b を選ぶ2つの組は6通り",
            "desc": ("上に番号1〜4をつけた4つのかっこ (a＋b)。その下に、b を選ぶ2つのかっこに網かけと太字の b を置き、"
                     "残りの2つには a を置いた行を 1と2・1と3・1と4・2と3・2と4・3と4 の順に6行並べ、各行の右に積 a²b² を書く。"
                     "右の括弧で6行をまとめて 6通り、下に a²b² の係数は 4C2=6。同型図はかっこの個数と選ぶ個数を差し替えて生成する"),
            "alt": "4つのかっこ(a＋b)から、bを選ぶ2つに印をつけた6通りの対応図——1と2、1と3、1と4、2と3、2と4、3と4の6行が並び、a²b²の係数4C2=6に対応する",
            "intent": "係数＝選び方の数（二項定理の見方）を、印をつけたますの並びで数えられる形にする。L01 の立方体の3個の直方体と同じ数え方の、かっこ4つの場合",
            "src": "lesson_02.md §2（a²b² の係数を数える段落の直後）",
            "params": "かっこ4つ（中心 x=236・306・376・446）／行 6（1行目のベースライン 136・間隔 40）／ます 30px・b を選んだますは網かけ #d9d9d9",
            "checks": ck.items,
            "check_tokens": ["189", "448", "270", "14641", "161051", "1792", "8x³＋8x", "a=2", "5C3", "5C2",
                             "81x⁴", "24a²b²", "16b⁴", "10x³", "64", "32"],
            "digit_rule": ("subset", {"1", "2", "3", "4", "6"}),
            "allow_texts": allow}


# ===========================================================================
# L03: 158÷12 と (x²＋5x＋8)÷(x＋2) の筆算の並置
# ===========================================================================
def draw_division_bracket(cv, bx, y_top, y_bot):
    """筆算の「)」と上の横線の左端（弧は座標サンプリングした折れ線）"""
    pts = [(bx + 5.0 * math.sin(math.pi * t / 16), y_top + (y_bot - y_top) * t / 16) for t in range(17)]
    cv.path(pts, w=MAIN_W, oid="bracket")


def fig_L03_1():
    # --- パラメータ（lesson_03.md §1〜§2。学習指導要領解説の例の値） ---
    N, dv = 158, 12                  # 整数の割り算
    A, B = [1, 5, 8], [1, 2]         # x²＋5x＋8 を x＋2 で割る（係数は高次→低次）
    rows_y = {"q": 96, "d": 136, "p1": 176, "r1": 214, "p2": 254, "r2": 292}   # 各段のベースライン
    dp = 12.5                        # 整数の1桁の幅（px）
    int_col0 = 154.0                 # 整数の百の位の中心 x
    poly_R = [446.0, 494.0, 530.0]   # 多項式の x²・x・定数項の列の右端 x
    x_mid = 290.0                    # 中央の「商」「余り」の x
    title_i, title_p = "整数：158÷12", "多項式：(x²＋5x＋8)÷(x＋2)"
    allow = [title_i, title_p, "12", "1", "2", "3", "5", "6", "8", "x＋2", "x", "＋3", "x²", "＋5x", "＋8",
             "＋2x", "3x", "＋6", "商", "余り"]

    ck = Checker()
    qd, irows, irem = school_int_division(N, dv)
    q_int = int("".join(str(qd[k]) for k in sorted(qd)))
    ck.ok("158=12×13＋2・0≦余り2<12（整数の割り算の結果）", N == dv * q_int + irem and 0 <= irem < dv and q_int == 13,
          f"商={q_int}・余り={irem}")
    ck.ok("整数の筆算の段: 12（百・十の位）→38→36→2（小学校の手順で計算した段と一致）",
          [(k, v, c) for k, v, c in irows] == [("prod", 12, 1), ("rem", 38, 2), ("prod", 36, 2), ("rem", 2, 2)],
          f"{irows}")
    quot, prows, prem = school_poly_division(A, B)
    ck.ok("多項式の筆算: 商 x＋3・余り 2", quot == {1: 1, 0: 3} and prem == {0: 2}, f"商={quot}・余り={prem}")
    ck.ok("x²＋5x＋8=(x＋2)(x＋3)＋2（右辺を展開して左辺に戻る）",
          poly_add(poly_mul([2, 1], [3, 1]), [2]) == [8, 5, 1])
    ck.ok("余りの次数（0次）<割る式の次数（1次）で筆算が止まる", max(prem) < len(B) - 1 + 1 and len(B) - 1 == 1)
    shown = [[(d, s) for d, s in terms_of(dct)] for _, dct in prows]
    ck.ok("多項式の筆算の段: x²＋2x→3x＋8→3x＋6→2（本文の手順1〜3と同じ式）",
          [[s for _, s in t] for t in shown] == [["x²", "＋2x"], ["3x", "＋8"], ["3x", "＋6"], ["2"]], f"{shown}")
    # 段組みの対応: 多項式の各段に x=10 を入れた値＝整数の同じ段の値×（右端の位）
    corr = []
    for (kind_i, v_i, c_i), (kind_p, dct) in zip(irows, prows):
        pv = sum(c * 10 ** d for d, c in dct.items())
        corr.append(kind_i == kind_p and pv == v_i * 10 ** (2 - c_i))
    ck.ok("同じ段組み: 多項式の各段に x=10 を入れると整数の同じ段の値になる（x²・x・定数項＝百・十・一の位）",
          all(corr) and sum(c * 10 ** (2 - i) for i, c in enumerate(A)) == N and 10 + 2 == dv and 10 + 3 == q_int)
    cols_ok = True
    for (kind_i, v_i, c_i), (kind_p, dct) in zip(irows, prows):
        dcols = [c_i - t for t in range(len(str(v_i)))]
        pcols = [2 - d for d, _ in terms_of(dct)]
        cols_ok = cols_ok and sorted(dcols) == sorted(pcols)
    ck.ok("各段で、整数の数字が入る位の列と、多項式の項が入る次数の列が同じ", cols_ok)
    body_has(ck, 3, ["158=12×13＋2", "x²＋5x＋8=(x＋2)(x＋3)＋2", "x(x＋2)=x²＋2x", "3x＋8", "3(x＋2)=3x＋6",
                     "商は x＋3、余りは 2 である"], "筆算の値と段")

    H = rows_y["r2"] + 26
    cv = Canvas(W, H)
    lb = Labels(cv)
    icol = [int_col0 + dp * t for t in range(3)]

    def put_int(v, right_col, y):
        s = str(v)
        for t, ch in enumerate(reversed(s)):
            lb.put(icol[right_col - t], y, ch)

    # 整数の筆算
    bx_i = icol[0] - dp / 2 - 9
    put_c(lb, (bx_i + icol[2]) / 2 - 16, 44 - 0.29 * FS, title_i)
    lb.put(bx_i - 6, rows_y["d"], str(dv), anchor="end")
    draw_division_bracket(cv, bx_i, rows_y["d"] - 21, rows_y["d"] + 7)
    cv.line(bx_i, rows_y["d"] - 21, icol[2] + 10, rows_y["d"] - 21, w=MAIN_W, oid="bracket")
    for k in sorted(qd):
        lb.put(icol[k], rows_y["q"], str(qd[k]))
    put_int(N, 2, rows_y["d"])
    for (kind, v, c), key in zip(irows, ["p1", "r1", "p2", "r2"]):
        put_int(v, c, rows_y[key])
        if kind == "prod":
            left = icol[c - len(str(v)) + 1] - dp / 2 - 3
            cv.line(left, rows_y[key] + 9, icol[2] + 10, rows_y[key] + 9, w=1.2)
    # 多項式の筆算
    bx_p = poly_R[0] - est_w("x²", FS) - 9
    put_c(lb, 452, 44 - 0.29 * FS, title_p)
    lb.put(bx_p - 6, rows_y["d"], "x＋2", anchor="end")
    draw_division_bracket(cv, bx_p, rows_y["d"] - 21, rows_y["d"] + 7)
    cv.line(bx_p, rows_y["d"] - 21, poly_R[2] + 6, rows_y["d"] - 21, w=MAIN_W, oid="bracket")
    for d, s in terms_of(quot):
        lb.put(poly_R[2 - d], rows_y["q"], s, anchor="end")
    for d, s in terms_of({2 - i: c for i, c in enumerate(A)}):
        lb.put(poly_R[2 - d], rows_y["d"], s, anchor="end")
    for (kind, dct), key in zip(prows, ["p1", "r1", "p2", "r2"]):
        ts = terms_of(dct)
        for d, s in ts:
            lb.put(poly_R[2 - d], rows_y[key], s, anchor="end")
        if kind == "prod":
            dmax = ts[0][0]
            left = poly_R[2 - dmax] - max(est_w(s, FS) for _, s in ts) - 4
            cv.line(left, rows_y[key] + 9, poly_R[2] + 6, rows_y[key] + 9, w=1.2)
    # 中央: 商・余りの段の見出し（左右の筆算を指す）
    for key, s in (("q", "商"), ("r2", "余り")):
        cy = rows_y[key] - 0.29 * FS
        hw = est_w(s, FS) / 2
        put_c(lb, x_mid, cy, s)
        cv.arrow(x_mid - hw - 6, cy, x_mid - hw - 46, cy, w=1.2, head=7.0)
        cv.arrow(x_mid + hw + 6, cy, x_mid + hw + 46, cy, w=1.2, head=7.0)
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L03_fig1_long_division_side_by_side.svg", "lesson": "L03", "canvas": cv,
            "title": "整数の筆算と多項式の筆算の並置——158÷12 と (x²＋5x＋8)÷(x＋2)",
            "desc": ("左に 158÷12 の筆算（商13・段 12→38→36→余り2）、右に x²＋5x＋8 を x＋2 で割る筆算（商 x＋3・段 x²＋2x→3x＋8→3x＋6→余り2）を、"
                     "同じ高さの段にそろえて並べる。多項式の x²・x・定数項の列が整数の百・十・一の位の列に対応する。"
                     "中央に商の段と余りの段の見出し。値は学習指導要領解説の例。同型図は割られる式・割る式の係数と整数を差し替えて生成する"),
            "alt": "整数と多項式の筆算の並置——左に158÷12の筆算（商13・余り2）、右にx²＋5x＋8をx＋2で割る筆算（商x＋3・余り2）が同じ段組みで並ぶ",
            "intent": "多項式の筆算が整数の筆算と同じ手順・同じ段で進むことを見せる。違いは止まる理由（大きさか次数か）だけ、という本文の表への入口",
            "src": "lesson_03.md §2（筆算を並べる段落の直後）",
            "params": "整数 158÷12（1桁 12.5px・百の位の中心 x=154）／多項式 [1, 5, 8]÷[1, 2]（列の右端 x=446・494・530）／段のベースライン 96・136・176・214・254・292",
            "checks": ck.items,
            "check_tokens": ["−7", "x＋4", "3x²＋x＋1", "2x−3", "3x−2", "x²＋x＋1", "2y²", "x²＋x＋2", "b＋1",
                             "x³−3x²＋x＋4", "10", "2x²＋4x＋3", "−2x＋1"],
            "digit_rule": ("subset", {"1", "2", "3", "5", "6", "8", "12", "158"}),
            "allow_texts": allow}


# ===========================================================================
# L05: 恒等式と方程式——グラフが重なる／交点だけ
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（lesson_05.md §1 の (ア) と例題1(2)） ---
    S = 40.0                                   # 1単位の px（両パネル共通）
    xr_l, xr_r, yr = (-3.6, 1.6), (-2.2, 3.4), (-0.9, 5.6)
    y_top = 5.35                               # 曲線を描く上端の y
    x_l0, x_r0, y_plot_top = 54.0, 368.0, 72.0 # 左右パネルの左端 px・y=5.6 の px
    f1 = lambda x: (x + 1) ** 2                # y=(x＋1)²
    f2 = lambda x: x * x + 2 * x + 1           # y=x²＋2x＋1
    g = lambda x: x * x - x                    # y=x²−x
    c_line = 2                                 # y=2
    title_l, title_r = "恒等式：2つのグラフが重なる", "方程式：2点でだけ交わる"
    lab1, lab2, lab3, lab4 = "y=(x＋1)²", "y=x²＋2x＋1", "y=x²−x", "y=2"
    allow = [title_l, title_r, "x", "y", "O", lab1, lab2, lab3, lab4, "−1", "2"]

    ck = Checker()
    ck.ok("(x＋1)² を展開すると x²＋2x＋1（係数の並びが一致）", poly_mul([1, 1], [1, 1]) == [1, 2, 1])
    ck.ok("(x＋1)² と x²＋2x＋1 は x=−10〜10 の21個の整数で値が一致（厳密計算）",
          all(f1(Fr(t)) == f2(Fr(t)) for t in range(-10, 11)))
    roots = sorted(t for t in range(-10, 11) if g(t) == c_line)
    ck.ok("x²−x=2 は x²−x−2=(x−2)(x＋1)=0 で、解は x=−1, 2 の2つだけ（判別式 9>0）",
          poly_mul([-2, 1], [1, 1]) == [-2, -1, 1] and roots == [-1, 2] and (-1) ** 2 - 4 * 1 * (-2) == 9)
    body_has(ck, 5, ["(ア) (x＋1)²=x²＋2x＋1", "x²−x=2", "x=2, −1 のときだけ成り立つ", "2つのグラフは完全に重なる",
                     "2つのグラフが交わる点の x 座標だけが解になる"], "式と解")

    frL = Frame(x_l0 - xr_l[0] * S, y_plot_top + yr[1] * S, S)
    frR = Frame(x_r0 - xr_r[0] * S, y_plot_top + yr[1] * S, S)
    H = round(frL.oy - yr[0] * S + 96)
    cv = Canvas(W, H)
    lb = Labels(cv)
    lx_c = x_l0 + (xr_l[1] - xr_l[0]) * S / 2
    rx_c = x_r0 + (xr_r[1] - xr_r[0]) * S / 2
    put_c(lb, lx_c, 40 - 0.29 * FS, title_l, weight="bold")
    put_c(lb, rx_c, 40 - 0.29 * FS, title_r, weight="bold")
    # 左: 2つのグラフ（太いグレーの線と、その上の黒い破線）
    draw_axes(cv, lb, frL, xr_l, yr)
    xa, xb = parabola_span(-1, 0, y_top, *xr_l)
    p1 = curve_pts(frL, f1, xa, xb)
    p2 = curve_pts(frL, f2, xa, xb)
    ck.ok("左のパネルの2本の曲線は、描く点列（241点）が座標まで完全に同じ",
          [f"{x:.3f},{y:.3f}" for x, y in p1] == [f"{x:.3f},{y:.3f}" for x, y in p2])
    cv.path(p1, w=7.0, color=SHADE2, oid="curve")
    cv.path(p2, w=MAIN_W, dash=DASH, oid="curve")
    yl1 = frL.oy - yr[0] * S + 40
    yl2 = yl1 + 30
    cv.line(x_l0 + 14, yl1, x_l0 + 54, yl1, w=7.0, color=SHADE2, oid="legend")
    cv.line(x_l0 + 14, yl2, x_l0 + 54, yl2, w=MAIN_W, dash=DASH, oid="legend")
    put_c(lb, x_l0 + 64 + est_w(lab1, FS) / 2, yl1, lab1)
    put_c(lb, x_l0 + 64 + est_w(lab2, FS) / 2, yl2, lab2)
    # 右: 放物線と直線、交点2つ
    draw_axes(cv, lb, frR, xr_r, yr, xnums=(-1, 2))
    xa, xb = parabola_span(0.5, -0.25, y_top, *xr_r)
    cv.path(curve_pts(frR, g, xa, xb), w=MAIN_W, oid="curve")
    L0, L1 = frR.P((xr_r[0], c_line)), frR.P((xr_r[1], c_line))
    cv.line(L0[0], L0[1], L1[0], L1[1], w=MAIN_W, oid="curve")
    for rt in roots:
        P = frR.P((rt, c_line))
        Q = frR.P((rt, 0))
        cv.line(P[0], P[1], Q[0], Q[1] - 4, w=AUX_W, dash=DASH, oid="guide")
        cv.dot(P[0], P[1], r=DOT_R + 0.8)
    ck.ok("交点の点は (−1, 2) と (2, 2) の位置（放物線と直線の両方の上）",
          all(near(g(rt), c_line) and xr_r[0] < rt < xr_r[1] for rt in roots))
    P = frR.P((0.25, 4.62))
    lb.put(P[0], P[1], lab3, anchor="start")
    P = frR.P((xr_r[1], c_line))
    lb.put(P[0], P[1] - 8, lab4, anchor="end")
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L05_fig1_identity_vs_equation.svg", "lesson": "L05", "canvas": cv,
            "title": "恒等式と方程式——y=(x＋1)² と y=x²＋2x＋1 は重なり、y=x²−x と y=2 は2点でだけ交わる",
            "desc": ("2つの座標平面を横に並べる。左は y=(x＋1)²（太いグレーの線）と y=x²＋2x＋1（黒い破線）で、2本が同じ放物線の上に重なる。"
                     "右は y=x²−x と y=2 で、交点 (−1, 2)・(2, 2) に点を打ち、x 軸へ破線を下ろして −1 と 2 を書く。"
                     "同型図は左の2つの式（展開の前と後）と、右の2つの式を差し替えて生成する"),
            "alt": "恒等式と方程式の違い——左のパネルではy=(x＋1)²とy=x²＋2x＋1のグラフが完全に重なり、右のパネルではy=x²−xとy=2のグラフがx=−1とx=2の2点でだけ交わる",
            "intent": "「いつでも成り立つ」と「ある x で成り立つ」の違いを、グラフが重なるか交点だけかで見せる。1つの値で成り立っても恒等式とは言えないことへの伏線",
            "src": "lesson_05.md §1（例題1のあと、グラフで見る段落の直後）",
            "params": "1単位 40px・左 x=−3.6〜1.6・右 x=−2.2〜3.4・y=−0.9〜5.6／曲線は y=5.35 まで（241点の折れ線）／左の2本は太さ7のグレーと黒の破線",
            "checks": ck.items,
            "check_tokens": ["x=0", "a=2", "c=−2", "c=3", "x−3", "−3x＋11", "x=−2", "y=3", "1/2", "−1/2", "x²＋4"],
            "digit_rule": ("subset", {"1", "2"}),
            "allow_texts": allow}


# ===========================================================================
# L07: y=(x−2)²＋3 は x 軸より上——実数の平方は 0 以上
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（lesson_07.md §2 例題2） ---
    p, q = 2, 3                                 # y=(x−p)²＋q の頂点 (p, q)
    xr, yr = (-1.2, 5.4), (-0.9, 8.4)
    sx, sy = 48.0, 38.0
    x_left, y_plot_top = 60.0, 30.0             # x=−1.2 の px・y=8.4 の px
    y_top = 8.1                                 # 曲線を描く上端の y
    f = lambda x: (x - p) ** 2 + q
    lab_curve, lab_vertex = "y=(x−2)²＋3", "頂点 (2, 3)"
    caption = "(x−2)²≧0 だから y≧3>0"
    allow = ["x", "y", "O", lab_curve, lab_vertex, "2", "3", caption]

    ck = Checker()
    ck.ok("(x−2)²＋3 を展開すると x²−4x＋7", poly_add(poly_mul([-2, 1], [-2, 1]), [3]) == [7, -4, 1])
    vals = [f(Fr(t, 10)) for t in range(-12, 55)]
    ck.ok("x=−1.2〜5.4（0.1刻み）で y≧3、y=3 は x=2 のときだけ",
          min(vals) == q and [Fr(t, 10) for t in range(-12, 55) if f(Fr(t, 10)) == q] == [p])
    ck.ok("x²−4x＋7=0 の判別式 16−28=−12<0（x 軸と共有点をもたない）", (-4) ** 2 - 4 * 1 * 7 == -12)
    body_has(ck, 7, ["x²−4x＋7=(x−2)²＋3", "頂点が (2, 3) の下に凸の放物線", "(x−2)²≧0。よって (x−2)²＋3≧3>0"],
             "式と頂点")

    fr = Frame(x_left - xr[0] * sx, y_plot_top + yr[1] * sy, sx, sy)
    H = round(fr.oy - yr[0] * sy + 76)
    cv = Canvas(W, H)
    lb = Labels(cv)
    draw_axes(cv, lb, fr, xr, yr, xnums=(p,), ynums=(q,))
    A0, A1 = fr.P((0, q)), fr.P((xr[1], q))
    cv.line(A0[0] + 4, A0[1], A1[0], A1[1], w=AUX_W, dash=DASH, oid="guide")
    V, V0 = fr.P((p, q)), fr.P((p, 0))
    cv.line(V[0], V[1], V0[0], V0[1] - 4, w=AUX_W, dash=DASH, oid="guide")
    xa, xb = parabola_span(p, q, y_top, *xr)
    pts = curve_pts(fr, f, xa, xb)
    ck.ok("描いた曲線の点はすべて x 軸より上（y≧3 の高さ以上の px）", all(py <= V[1] + 1e-9 for _, py in pts))
    cv.path(pts, w=MAIN_W, oid="curve")
    cv.dot(V[0], V[1], r=DOT_R + 0.6)
    P = fr.P((4.42, 7.55))
    lb.put(P[0], P[1], lab_curve, anchor="start")
    P = fr.P((2.24, 2.02))
    lb.put(P[0], P[1], lab_vertex, anchor="start")
    put_c(lb, W / 2, H - 22, caption)
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L07_fig1_square_nonnegative.svg", "lesson": "L07", "canvas": cv,
            "title": "y=(x−2)²＋3 のグラフ——頂点 (2, 3)・x 軸と共有点をもたない",
            "desc": ("座標平面に、頂点 (2, 3) の下に凸の放物線 y=(x−2)²＋3 を描く。頂点から x 軸・y 軸へ破線を引き、y=3 の高さの破線を右へのばす。"
                     "放物線はこの破線より下に行かず、x 軸とは交わらない。下に「(x−2)²≧0 だから y≧3>0」。"
                     "同型図は頂点 (p, q)（q>0）を差し替えて生成する"),
            "alt": "y=(x−2)²＋3のグラフ——頂点(2, 3)の下に凸の放物線がx軸より上にあり、x軸と共有点をもたない。(x−2)²≧0 だから y≧3>0 であることを示す",
            "intent": "平方完成した式の (…)²≧0 が、グラフでは「頂点の高さより下に行かない」に当たることを見せる（数学Ⅰ「二次関数」の描き方）",
            "src": "lesson_07.md §2（例題2のあと、グラフの見え方の段落の直後）",
            "params": "頂点 (2, 3)・x=−1.2〜5.4・y=−0.9〜8.4（1単位 横 48px・縦 38px）・曲線は y=8.1 まで",
            "checks": ck.items,
            "check_tokens": ["(x＋3)²＋1", "b=2a", "x=y=1", "x=y", "a=b=0", "a=b=c", "17", "8"],
            "digit_rule": ("subset", {"0", "2", "3"}),
            "allow_texts": allow}


# ===========================================================================
# L08: x＞0 での x・1/x・x＋1/x の値の点の図／絶対値＝距離の数直線
# ===========================================================================
def mk_square(cv, x, y, h=5.5):
    cv.path([(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)], w=1.4, close=True,
            fill="#fff", oid="marker", join="miter")


def mk_tri(cv, x, y, r=7.0):
    cv.path([(x, y - r), (x + r * C30, y + r / 2), (x - r * C30, y + r / 2)], w=1.4, close=True,
            fill="#fff", oid="marker", join="miter")


def mk_dot(cv, x, y, r=5.5):
    cv.dot(x, y, r=r, oid="marker")


def fig_L08_1():
    # --- パラメータ（lesson_08.md §4 の表） ---
    xs = [Fr(1, 4), Fr(1, 2), Fr(1), Fr(2), Fr(4)]
    y0_px, x0_px = 344.0, 96.0                   # 値 0 の高さ・縦軸の位置（px）
    cats = [164.0 + 86.0 * i for i in range(5)]  # 表の x を等間隔に置く（px）
    sy = 62.0                                    # 値 1 あたりの px
    legend_y = 34.0
    note = "横は x の値を等間隔に並べた（点どうしを曲線で結ばない）"
    allow = ["x", "1/x", "x＋1/x", "値", "0", "1", "2", "3", "4", "1/4", "1/2", note]

    inv = [1 / x for x in xs]
    sums = [x + 1 / x for x in xs]
    ck = Checker()
    ck.ok("x＋1/x の値が 17/4・5/2・2・5/2・17/4（厳密計算）",
          sums == [Fr(17, 4), Fr(5, 2), Fr(2), Fr(5, 2), Fr(17, 4)], f"{[fmt(s) for s in sums]}")
    ck.ok("表の中で x＋1/x が最も小さいのは x=1 のときの 2 だけ", min(sums) == 2 and sums.count(2) == 1 and xs[sums.index(2)] == 1)
    ck.ok("どの x でも x＋1/x≧2（相加・相乗平均の関係の数値の確かめ）で、等号は x=1 のときだけ",
          all(s >= 2 for s in sums) and all((s == 2) == (x == 1) for x, s in zip(xs, sums)))
    ck.ok("x の並びは 2 倍ずつ（等間隔に並べると x と 1/x が左右対称になる）",
          all(xs[i + 1] == 2 * xs[i] for i in range(4)) and all(xs[i] * xs[4 - i] == 1 for i in range(5))
          and all(sums[i] == sums[4 - i] for i in range(5)))
    rows = ["| x | " + " | ".join(fmt(v) for v in xs) + " |",
            "| 1/x | " + " | ".join(fmt(v) for v in inv) + " |",
            "| x＋1/x | " + " | ".join(fmt(v) for v in sums) + " |"]
    body_has(ck, 8, rows + ["表の中では x=1 のときの 2 が最も小さい"], "表の3行")

    H = 418
    cv = Canvas(W, H)
    lb = Labels(cv)
    Y = lambda v: y0_px - sy * float(v)
    cv.arrow(x0_px, y0_px, 572.0, y0_px, w=AXIS_W, oid="axis")
    cv.arrow(x0_px, y0_px, x0_px, Y(4.7) - 10, w=AXIS_W, oid="axis")
    lb.put(580.0, y0_px + FS * 0.35, "x", anchor="start")
    lb.put(x0_px + 9, Y(4.7) - 6, "値", anchor="start")
    for i, cx in enumerate(cats):
        cv.line(cx, y0_px - 3.5, cx, y0_px + 3.5, w=THIN_W, oid="tick")
        lb.put(cx, y0_px + 5 + FS, fmt(xs[i]))
    for v in range(0, 5):
        if v:
            cv.line(x0_px - 3.5, Y(v), x0_px + 3.5, Y(v), w=THIN_W, oid="tick")
        lb.put(x0_px - 7, Y(v) + FS * 0.35, str(v), anchor="end")
    cv.line(x0_px + 4, Y(2), 556.0, Y(2), w=AUX_W, dash=DASH, oid="guide")
    pos = {"x": [], "1/x": [], "x＋1/x": []}
    for i, cx in enumerate(cats):
        mk_square(cv, cx, Y(xs[i]))
        pos["x"].append((cx, Y(xs[i])))
    for i, cx in enumerate(cats):
        mk_tri(cv, cx, Y(inv[i]))
        pos["1/x"].append((cx, Y(inv[i])))
    for i, cx in enumerate(cats):
        mk_dot(cv, cx, Y(sums[i]))
        pos["x＋1/x"].append((cx, Y(sums[i])))
    ck.ok("点の高さは値に比例（値 0 の高さから 1 あたり 62px）・横は5つの x を 86px 間隔",
          all(near(pos[k][i][1], y0_px - sy * float(v)) for k, vs in (("x", xs), ("1/x", inv), ("x＋1/x", sums))
              for i, v in enumerate(vs)) and all(near(cats[i + 1] - cats[i], 86.0) for i in range(4)))
    ck.ok("点どうしを線で結んでいない（図の中に折れ線を1本も描かない）", not any("<polyline" in s for s in cv.body))
    close = []
    for i in range(5):
        for k1, k2 in (("x", "1/x"), ("x", "x＋1/x"), ("1/x", "x＋1/x")):
            d = dist(pos[k1][i], pos[k2][i])
            if d < 14.0:
                close.append((fmt(xs[i]), k1, k2, round(d, 1)))
    ck.ok("印が重なるのは x=1 の x と 1/x（どちらも値 1）だけで、ほかの印は 14px 以上離れる",
          close == [("1", "x", "1/x", 0.0)], f"{close}")
    # 凡例
    items = [("x", mk_square, 330.0), ("1/x", mk_tri, 392.0), ("x＋1/x", mk_dot, 474.0)]
    for s, fn, x in items:
        fn(cv, x, legend_y)
        put_c(lb, x + 12 + est_w(s, FS) / 2, legend_y, s)
    put_c(lb, W / 2, H - 22, note)
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L08_fig1_am_gm_values.svg", "lesson": "L08", "canvas": cv,
            "title": "x>0 での x・1/x・x＋1/x の値の点の図——x＋1/x は x=1 のとき最も低く 2",
            "desc": ("横に表の x の値 1/4・1/2・1・2・4 を等間隔に並べ、縦に値をとって、x を白い四角、1/x を白い三角、"
                     "x＋1/x を黒い丸で打つ（点は結ばない）。値 2 の高さに破線。黒い丸は x=1 のときの 2 が最も低く、左右対称に並ぶ。"
                     "x=1 では四角と三角が同じ値 1 で重なる。同型図は表の x の並びを差し替えて生成する"),
            "alt": "x>0のときのx、1/x、x＋1/xの値を、x=1/4, 1/2, 1, 2, 4で点として並べた図——x＋1/xの点はx=1のときに最も低く、その値は2（点どうしを曲線で結ばない）",
            "intent": "表の値だけで「x=1 で最も小さい」が見えるようにし、相加・相乗平均の関係での証明につなぐ。曲線を引かず分数関数の名も出さない（数学Ⅲの内容に立ち入らない）",
            "src": "lesson_08.md §4（値の表の直後）",
            "params": "x=1/4・1/2・1・2・4（横 86px 間隔・等間隔）／縦 1 あたり 62px・値 0 の高さ 344px／印 四角 11px・三角 外接円 7px・丸 半径 5.5px",
            "checks": ck.items,
            "check_tokens": ["9/x", "8/x", "4/x", "16", "x=3", "最小値", "ab=2", "6", "8", "9"],
            "digit_rule": ("subset", {"0", "1", "2", "3", "4"}),
            "allow_texts": allow}


def fig_L08_2():
    # --- パラメータ（lesson_08.md §1「たとえば a=−3 なら、−a=3 で、|a|=3」） ---
    a_val = -3
    UNIT, Y, Y_AR = 50.0, 104.0, 64.0            # 1目盛りの px・数直線の高さ・距離の矢印の高さ
    x_px = lambda v: 320.0 + v * UNIT
    lab_a, lab_na, lab_d = "a=−3", "−a=3", "距離3"
    allow = [lab_a, "0", lab_na, lab_d]

    ck = Checker()
    ck.ok("a=−3 のとき −a=3 で、a と −a の絶対値はどちらも 3", -a_val == 3 and abs(a_val) == abs(-a_val) == 3)
    ck.ok("2点は原点から等距離（3×目盛り）で、原点について対称",
          near(x_px(0) - x_px(a_val), 3 * UNIT) and near(x_px(-a_val) - x_px(0), 3 * UNIT)
          and near(x_px(a_val) + x_px(-a_val), 2 * x_px(0)))
    ck.ok("●の半径は数学Ⅰ「数と式」の数直線系と同じ 3.4px（描き方の統一）", DOT_R_END == 3.4)
    body_has(ck, 8, ["たとえば a=−3 なら、−a=3 で、|a|=3", "どちらも原点からの距離は |a| である"], "値と距離")

    H = 152
    cv = Canvas(W, H)
    lb = Labels(cv)
    cv.arrow(x_px(0), Y, x_px(5) + 26, Y, w=1.2, oid="axis")
    cv.arrow(x_px(0), Y, x_px(-5) - 26, Y, w=1.2, oid="axis")
    for v in range(-5, 6):
        cv.line(x_px(v), Y - 4, x_px(v), Y + 4, w=THIN_W, oid="tick")
    cv.dot(x_px(a_val), Y, r=DOT_R_END)
    cv.dot(x_px(-a_val), Y, r=DOT_R_END)
    lb.put(x_px(a_val), Y + 30, lab_a)
    lb.put(x_px(0), Y + 30, "0")
    lb.put(x_px(-a_val), Y + 30, lab_na)
    cv.arrow(x_px(0), Y_AR, x_px(a_val), Y_AR, w=1.3)
    cv.arrow(x_px(0), Y_AR, x_px(-a_val), Y_AR, w=1.3)
    ck.ok("距離の矢印2本の長さが等しい", near(abs(x_px(a_val) - x_px(0)), abs(x_px(-a_val) - x_px(0))))
    for v in (a_val, 0, -a_val):
        cv.line(x_px(v), Y_AR, x_px(v), Y - 7, w=AUX_W, dash=DASH, oid="guide")
    lb.put(x_px(a_val / 2), Y_AR - 10, lab_d, weight="bold")
    lb.put(x_px(-a_val / 2), Y_AR - 10, lab_d, weight="bold")
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L08_fig2_abs_distance_number_line.svg", "lesson": "L08", "canvas": cv,
            "title": "絶対値は数直線上の距離——a=−3 と −a=3 はどちらも原点から距離3",
            "desc": ("−5〜5 の目盛りの数直線に、a=−3 と −a=3 の2点を●で打ち、原点 0 から左右へ同じ長さの矢印と「距離3」を書く。"
                     "2点は原点について対称。●の描き方は数学Ⅰ「数と式」の数直線と同じ。同型図は a の値を差し替えて生成する"),
            "alt": "絶対値は数直線上の距離——a=−3と−a=3が原点0について対称な位置にあり、どちらも原点からの距離が3であることを示す数直線",
            "intent": "絶対値を「原点からの距離」として読み直し、a と −a の距離が同じであることから絶対値の性質を導く入口にする",
            "src": "lesson_08.md §1（a=−3 の例の直後）",
            "params": "数直線 −5〜5（1目盛り 50px・原点 x=320）／●半径 3.4px／距離の矢印の高さ 64px・数直線の高さ 104px",
            "checks": ck.items,
            "check_tokens": ["6", "8", "9", "16", "ab≦0"],
            "digit_rule": ("subset", {"0", "3"}),
            "allow_texts": allow}


# ===========================================================================
# L09: 数の範囲の入れ子（数学Ⅰ「数と式」L05 の実数の地図の外側に、複素数の枠を1つ足す）
# ===========================================================================
def fig_L09_1():
    # --- パラメータ（lesson_09.md §0 の表と §2 の段落） ---
    boxes = [("複素数", (18, 24, 604, 322), "#e6e6e6", 1.6),
             ("実数", (36, 66, 440, 262), "#fff", 1.6),
             ("有理数", (54, 108, 278, 202), "#fff", 1.3),
             ("無理数", (348, 108, 112, 202), "#fff", 1.3),
             ("整数", (70, 156, 204, 138), "#fff", 1.1),
             ("自然数", (86, 204, 122, 74), "#fff", 1.1)]
    parent = {"実数": "複素数", "有理数": "実数", "無理数": "実数", "整数": "有理数", "自然数": "整数"}
    imag = "虚数"
    allow = [b[0] for b in boxes] + [imag]

    R = {name: r for name, r, _, _ in boxes}
    ck = Checker()
    ck.ok("入れ子の包含: 自然数⊂整数⊂有理数⊂実数⊂複素数（枠の座標で検査）",
          all(inside_rect(R[c], R[p]) for c, p in parent.items() if c != "無理数"))
    ck.ok("無理数の枠は実数の枠の中にあり、有理数の枠と交わらない",
          inside_rect(R["無理数"], R["実数"]) and disjoint_rect(R["無理数"], R["有理数"]))
    ck.ok("表の例の分類: −3 は整数で自然数でない・2/3 は有理数で整数でない・√2 は有理数でない・i は実数でない（i²=−1）",
          (-3) < 1 and Fr(2, 3).denominator != 1 and math.isqrt(2) ** 2 != 2 and (1j) ** 2 == complex(-1, 0))
    body_has(ck, 9, ["| x＋5=2 | 自然数の解はない | 整数（負の数を含む） | x=−3 |",
                     "| 3x=2 | 整数の解はない | 有理数（分数を含む） | x=2/3 |",
                     "| x²=2 | 有理数の解はない | 実数（無理数を含む） | x=±√2 |",
                     "| x²=−1 | 実数の解はない | ？ | ？ |",
                     "実数の地図の外側に、もう1枠を足した形になる", "b≠0 のとき、a＋bi を**虚数**という"],
             "数の範囲の表と虚数の定義")

    H = 364
    cv = Canvas(W, H)
    lb = Labels(cv)
    for name, (x, y, w, h), fill, sw in boxes:
        cv.rect(x, y, w, h, fill=fill, sw=sw, oid="frame")
    lab_ok = True
    for name, (x, y, w, h), _, _ in boxes:
        box = lb.put(x + 12, y + 30, name, anchor="start", weight="bold")
        r = (box[0], box[1], box[2] - box[0], box[3] - box[1])
        kids = [R[c] for c, p in parent.items() if p == name]
        lab_ok = lab_ok and inside_rect(r, (x, y, w, h)) and all(disjoint_rect(r, k) for k in kids)
    ck.ok("枠の名前は、それぞれ自分の枠の内側で、内側の枠とは重ならない位置にある", lab_ok)
    rx = R["実数"][0] + R["実数"][2]
    cx = (rx + R["複素数"][0] + R["複素数"][2]) / 2
    box = put_c(lb, cx, R["複素数"][1] + R["複素数"][3] / 2, imag, weight="bold")
    r = (box[0], box[1], box[2] - box[0], box[3] - box[1])
    ck.ok("「虚数」は複素数の枠の中で、実数の枠の外側（網かけの部分）にある",
          inside_rect(r, R["複素数"]) and disjoint_rect(r, R["実数"]))
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L09_fig1_number_system_nested.svg", "lesson": "L09", "canvas": cv,
            "title": "数の範囲の入れ子——実数の地図の外側に複素数の枠を足す",
            "desc": ("入れ子の枠の図。いちばん外側の複素数の枠（網かけ）の中に実数の枠（白）があり、実数の枠の中に有理数と無理数の枠、"
                     "有理数の中に整数、整数の中に自然数の枠がある。複素数の枠のうち実数の枠の外側の網かけの部分に「虚数」。"
                     "集合の記号は使わず、枠の名前だけ。同型図は枠の名前と入れ子の段数を差し替えて生成する"),
            "alt": "数の範囲の入れ子——自然数の枠を整数・有理数の枠が順に囲み、有理数と無理数を合わせた実数の枠を、いちばん外側の複素数の枠が囲む。複素数の枠の中で、実数の枠の外側にあたる部分が虚数である",
            "intent": "数学Ⅰ「数と式」L05 の実数の地図に1枠を足すだけで複素数の位置が決まることを見せて「実数も複素数の仲間」「虚数＝実数でない複素数」を枠の関係で読ませる",
            "src": "lesson_09.md §2（複素数・虚数・純虚数の定義の直後）",
            "params": "枠（x, y, 幅, 高さ）: 複素数 (18, 24, 604, 322)・実数 (36, 66, 440, 262)・有理数 (54, 108, 278, 202)・無理数 (348, 108, 112, 202)・整数 (70, 156, 204, 138)・自然数 (86, 204, 122, 74)／複素数の枠の網かけ #e6e6e6",
            "checks": ck.items,
            "check_tokens": ["7i", "10", "±√7 i", "(2/3)i", "2＋2i", "−3＋4i", "10＋5i", "−3−4i", "13", "1−2i",
                             "8/5", "純虚数"],
            "digit_rule": ("none", set()),
            "allow_texts": allow}


# ===========================================================================
# L10: 判別式と放物線——D>0・D=0・D<0 の3パネル（数学Ⅰ「二次関数」L09 の3態の描き方）
# ===========================================================================
def fig_L10_1():
    # --- パラメータ（lesson_10.md §4 の表: y=x²−2x＋c の c を −3, 1, 3 と変える） ---
    cs = [-3, 1, 3]
    xr, yr = (-2.2, 4.2), (-4.8, 6.2)
    PW, gap, x_first, pad = 196.0, 12.0, 14.0, 18.0   # パネル幅・間隔・左端・パネル内の余白（px）
    y_plot_top, sy = 56.0, 20.0                        # y=6.2 の px・縦 1 あたりの px
    y_top = 6.0                                        # 曲線を描く上端の y
    sx = (PW - 2 * pad) / (xr[1] - xr[0])
    heads = ["D>0", "D=0", "D<0"]
    eqs = ["y=x²−2x−3", "y=x²−2x＋1", "y=x²−2x＋3"]
    verdicts = ["2点で交わる", "1点で接する", "共有点をもたない"]
    lab_v = "頂点 (1, 2)"
    xnums = [(), (1,), ()]                             # 中央は接点の真下に 1
    root_labs = [((-1, "end"), (3, "start")), (), ()]  # 左は曲線の外側（−1 の左下・3 の右下）に書く
    allow = heads + eqs + verdicts + [lab_v, "x", "y", "−1", "3", "1"]

    ck = Checker()
    discs = [(-2) ** 2 - 4 * 1 * c for c in cs]
    ck.ok("判別式 D=4−4c が 16・0・−8（符号 正・0・負 がパネルの見出しと一致）",
          discs == [16, 0, -8] and [(d > 0) - (d < 0) for d in discs] == [1, 0, -1])
    roots = [sorted(t for t in range(-10, 11) if t * t - 2 * t + c == 0) for c in cs]
    ck.ok("x 軸との共有点: c=−3 は x=−1, 3・c=1 は x=1 だけ・c=3 は無し（整数の探索と判別式で一致）",
          roots == [[-1, 3], [1], []])
    ck.ok("x²−2x＋1=(x−1)²（c=1 の共有点は接点）・x²−2x−3=(x＋1)(x−3)",
          poly_mul([-1, 1], [-1, 1]) == [1, -2, 1] and poly_mul([1, 1], [-3, 1]) == [-3, -2, 1])
    ck.ok("頂点はどれも x=1 で、y 座標 c−1 が −4・0・2（x²−2x＋3 の最小値 2>0）", [c - 1 for c in cs] == [-4, 0, 2])
    ck.ok("数式ラベルがパラメータの c から組み立てた式と一致",
          eqs == ["y=x²−2x" + ("−" if c < 0 else "＋") + str(abs(c)) for c in cs])
    body_has(ck, 10, ["| −3 | 16 | (1, −4) | 2個 | x=−1, 3（異なる2つの実数解） |",
                      "| 1 | 0 | (1, 0) | 1個（接する） | x=1（重解） |",
                      "| 3 | −8 | (1, 2) | 0個 | x=1±√2 i（異なる2つの虚数解） |"], "§4 の表の3行")

    oy = y_plot_top + yr[1] * sy
    y_eq = oy - yr[0] * sy + 30
    H = round(y_eq + 50)
    cv = Canvas(W, H)
    lb = Labels(cv)
    for i, c in enumerate(cs):
        x_off = x_first + i * (PW + gap)
        fr = Frame(x_off + pad - xr[0] * sx, oy, sx, sy)
        draw_axes(cv, lb, fr, xr, yr, origin=None, xnums=xnums[i])
        f = (lambda cc: (lambda x: x * x - 2 * x + cc))(c)
        xa, xb = parabola_span(1, c - 1, y_top, *xr)
        pts = curve_pts(fr, f, xa, xb)
        cv.path(pts, w=MAIN_W, oid="curve")
        for rt in roots[i]:
            P = fr.P((rt, 0))
            cv.dot(P[0], P[1], r=DOT_R + 0.6)
        for v, anc in root_labs[i]:
            P = fr.P((v, 0))
            lb.put(P[0] + (-5 if anc == "end" else 5), P[1] + 5 + FS, fmt(v), anchor=anc)
        if not roots[i]:
            V = fr.P((1, c - 1))
            cv.dot(V[0], V[1], r=DOT_R + 0.6)
            ck.ok("共有点をもたないパネルでは、曲線の点がすべて x 軸より上", all(py < fr.oy for _, py in pts))
            P = fr.P((1.25, 0.95))
            lb.put(P[0], P[1], lab_v, anchor="start")
        cxp = x_off + PW / 2
        put_c(lb, cxp, 26 - 0.29 * FS, heads[i], weight="bold")
        lb.put(cxp, y_eq, eqs[i])
        lb.put(cxp, y_eq + 28, verdicts[i])
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L10_fig1_discriminant_three_cases.svg", "lesson": "L10", "canvas": cv,
            "title": "判別式と放物線——D>0 は2点で交わり、D=0 は1点で接し、D<0 は共有点をもたない",
            "desc": ("同じ目盛りの座標平面を3つ横に並べ、y=x²−2x−3・y=x²−2x＋1・y=x²−2x＋3 を描く（本文の表の c=−3, 1, 3）。"
                     "左は D>0 で x 軸と x=−1, 3 の2点で交わる、中央は D=0 で x=1 の1点で接する、右は D<0 で頂点 (1, 2) が x 軸より上。"
                     "数学Ⅰ「二次関数」の3態の図と同じ描き方。同型図は c の値を差し替えて生成する"),
            "alt": "判別式と放物線——y=x²−2x−3、y=x²−2x＋1、y=x²−2x＋3 の3つの放物線を3つのパネルに並べた図。左は D>0 で x 軸と x=−1, 3 の2点で交わり、中央は D=0 で x=1 の1点で接し、右は D<0 で頂点 (1, 2) が x 軸より上にあって共有点をもたない",
            "intent": "解の種類（判別式の符号）と、数学Ⅰで調べた x 軸との共有点の個数を1枚で結びつける。D<0 でグラフが浮いていても虚数解が2つあることは本文で補う",
            "src": "lesson_10.md §4（c を −3, 1, 3 と変えた表の直後）",
            "params": "c=−3, 1, 3／各パネル x=−2.2〜4.2・y=−4.8〜6.2（横 1 あたり 25px・縦 20px の共通目盛り）／パネル幅 196px・間隔 12px",
            "checks": ck.items,
            "check_tokens": ["2±3i", "(1±i)/2", "√3 i", "(−2±√2 i)/3", "c<9", "c=9", "c>9", "√5", "4(k−3)(k＋2)",
                             "−2<k<3", "x=−3", "k=3", "k=−2", "−20", "13", "9"],
            "digit_rule": ("subset", {"0", "1", "2", "3"}),
            "allow_texts": allow}


# ===========================================================================
# L15: 直方体の箱の見取り図（斜投影）
# ===========================================================================
def fig_L15_1():
    # --- パラメータ（lesson_15.md §1 例題1。学習指導要領解説の例） ---
    vol = 350
    x_draw = 6                     # 見取り図の辺の比に使う高さ（答えの寸法とは違う値にして比から答えが読めないようにする）
    S = 26.0                       # 1単位の px
    depth_k = 0.5                  # 斜投影の奥行きの縮み（45°方向）
    x0, y0 = 150.0, 262.0          # 手前の面の左下の px
    lab_h, lab_d, lab_w, lab_v = "高さ x cm", "縦 (x−2) cm", "横 (x＋3) cm", "容積 350cm³"
    allow = [lab_h, lab_d, lab_w, lab_v]

    ck = Checker()
    P3 = poly_add(poly_mul(poly_mul([0, 1], [-2, 1]), [3, 1]), [-vol])      # x(x−2)(x＋3)−350
    ck.ok("x(x−2)(x＋3)=350 を整理すると x³＋x²−6x−350=0（本文の式）", P3 == [-350, -6, 1, 1])
    divs = [d for d in range(1, vol + 1) if vol % d == 0]
    real_roots = [d for d in divs if poly_eval(P3, d) == 0]
    ck.ok("三次方程式の実数解は1つだけ（350 の約数で1つ見つかり、残りの二次式の判別式が負）",
          len(real_roots) == 1 and 8 * 8 - 4 * 50 < 0 and
          poly_mul([-real_roots[0], 1], [50, 8, 1]) == P3)
    ck.ok("見取り図の辺の比は答えの寸法と別（描画用の高さ ≠ 解）で、辺の長さから答えが読めない",
          x_draw != real_roots[0] and x_draw > 2)
    Lw, Lh, Ld = (x_draw + 3) * S, x_draw * S, (x_draw - 2) * S * depth_k
    ck.ok("描いた辺の長さの順は 横 (x＋3)>高さ x>縦 (x−2)（x>2 ならいつも成り立つ順）",
          Lw > Lh > (x_draw - 2) * S)
    body_has(ck, 15, ["縦は (x−2) cm、横は (x＋3) cm", "容積を 350cm³", "x³＋x²−6x−350=0"], "辺と容積")

    dx = dy = Ld * math.cos(math.radians(45))
    fl, fr_, tr, tl = (x0, y0), (x0 + Lw, y0), (x0 + Lw, y0 - Lh), (x0, y0 - Lh)
    bl, br, btr, btl = (x0 + dx, y0 - dy), (x0 + Lw + dx, y0 - dy), (x0 + Lw + dx, y0 - Lh - dy), (x0 + dx, y0 - Lh - dy)
    H = 318
    cv = Canvas(W, H)
    lb = Labels(cv)
    visible = [(fl, fr_), (fr_, tr), (tr, tl), (tl, fl), (tl, btl), (btl, btr), (btr, tr), (fr_, br), (br, btr)]
    hidden = [(fl, bl), (bl, br), (bl, btl)]
    for p, q in visible:
        cv.line(p[0], p[1], q[0], q[1], w=MAIN_W, oid="box")
    for p, q in hidden:
        cv.line(p[0], p[1], q[0], q[1], w=AUX_W, dash=DASH, oid="box")
    ck.ok("見える辺9本は実線、かくれた辺3本（奥の左下の頂点に集まる辺）は破線", len(visible) == 9 and len(hidden) == 3
          and all(bl in e for e in hidden))
    lb.put(x0 - 12, y0 - Lh / 2 + FS * 0.35, lab_h, anchor="end")
    lb.put(x0 + Lw / 2, y0 + 30, lab_w)
    mx, my = (fr_[0] + br[0]) / 2, (fr_[1] + br[1]) / 2
    lb.put(mx + 14, my + 20, lab_d, anchor="start")
    lb.put(btr[0] + 20, btr[1] + 26, lab_v, anchor="start")
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L15_fig1_box_dimensions.svg", "lesson": "L15", "canvas": cv,
            "title": "直方体の箱の見取り図——高さ x cm・縦 (x−2) cm・横 (x＋3) cm・容積 350cm³",
            "desc": ("斜投影の見取り図（奥行きは 45° 方向に半分の長さ・かくれた辺は破線）。手前の面の左の辺に「高さ x cm」・下の辺に「横 (x＋3) cm」・"
                     "右下の奥へのびる辺に「縦 (x−2) cm」・右上に「容積 350cm³」。辺の長さの比は描画用で、寸法の答えは図に書かない。"
                     "同型図は3辺の式と容積を差し替えて生成する"),
            "alt": "直方体の箱の見取り図——高さが x cm、縦が (x−2) cm、横が (x＋3) cm の直方体で、容積が 350cm³ であることが書き添えられている",
            "intent": "立式の前に、どの辺が x・x−2・x＋3 かを1枚で確かめる。答えの寸法（辺の長さの比も含む）は図に入れない",
            "src": "lesson_15.md §1（高さを x cm とおく段落の直後）",
            "params": "描画用の高さ 6（辺の比 横 9：高さ 6：縦 4・1単位 26px）／奥行きの縮み 1/2・45°／手前の面の左下 (150, 262)",
            "checks": ck.items,
            "check_tokens": ["7cm", "5cm", "10cm", "x=7", "343", "(x−7)", "x²＋8x＋50", "√34", "8cm", "x=5", "x=1",
                             "(11−√21)/2", "0<x<6", "16−x", "10−x", "√15"],
            "digit_rule": ("subset", {"2", "3", "350"}),
            "allow_texts": allow}


# ===========================================================================
# L16: 単元の地図——4つのまとまりと1本の背骨
# ===========================================================================
def fig_L16_1():
    # --- パラメータ（lesson_16.md §1 の表） ---
    blocks = [(["多項式の", "計算"], "L01〜L04"), (["恒等式と", "証明"], "L05〜L08"),
              (["複素数と", "二次方程式"], "L09〜L12"), (["因数定理と", "高次方程式"], "L13〜L15")]
    spine = "式をひとまとまりの対象として見る"
    top_label = "まとめ（L16）"
    bw, bgap, bx0 = 134.0, 14.0, 14.0             # まとまりの枠の幅・間隔・左端
    by0, bh = 92.0, 146.0                         # 枠の上端・高さ
    band_y0, band_y1 = 192.0, 228.0               # 帯（背骨）の上下
    band_x0, band_x1, tip = 4.0, 598.0, 632.0     # 帯の左端・矢じりの付け根・先端
    top_box = (228.0, 16.0, 150.0, 40.0)          # まとめの枠
    allow = [top_label, spine] + [s for names, _ in blocks for s in names] + [rng for _, rng in blocks]

    ck = Checker()
    nums = []
    for _, rng in blocks:
        a0, a1 = (int(t) for t in re.findall(r"L(\d\d)", rng))
        nums.append((a0, a1))
    ck.ok("4つのまとまりのレッスン番号が L01 から L15 まで途切れず・重ならずに昇順",
          [n for a0, a1 in nums for n in range(a0, a1 + 1)] == list(range(1, 16)))
    ck.ok("まとめ L16 はどのまとまりにも入らない", all(not (a0 <= 16 <= a1) for a0, a1 in nums)
          and re.findall(r"L(\d\d)", top_label) == ["16"])
    body_has(ck, 16, ["| " + "".join(names) + " | " + rng + " |" for names, rng in blocks] +
             ["式をひとまとまりの対象として見る", "4つのまとまりを貫く背骨"], "§1 の表と背骨")

    H = round(by0 + bh + 18)
    cv = Canvas(W, H)
    lb = Labels(cv)
    xs = [bx0 + i * (bw + bgap) for i in range(4)]
    centers = [x + bw / 2 for x in xs]
    tb_cx = top_box[0] + top_box[2] / 2
    ck.ok("まとめの枠は4つのまとまりの真上の中央（中心の x が左右のまとまりの中心の平均）",
          near(tb_cx, (centers[0] + centers[-1]) / 2))
    cv.rect(*top_box, fill=SHADE3, sw=BOLD_W)
    put_c(lb, tb_cx, top_box[1] + top_box[3] / 2, top_label, weight="bold")
    y_br = top_box[1] + top_box[3] + 18
    cv.line(tb_cx, top_box[1] + top_box[3], tb_cx, y_br, w=1.2)
    cv.line(centers[0], y_br, centers[-1], y_br, w=1.2)
    for c in centers:
        cv.line(c, y_br, c, by0, w=1.2)
    for (names, rng), x in zip(blocks, xs):
        # 枠は帯の上と下の2つに分けて描く（帯の中を縦の線が通らない）
        cv.path([(x, band_y0), (x, by0), (x + bw, by0), (x + bw, band_y0)], w=MAIN_W, oid="block", join="miter")
        cv.path([(x, band_y1), (x, by0 + bh), (x + bw, by0 + bh), (x + bw, band_y1)], w=MAIN_W, oid="block",
                join="miter")
        put_c(lb, x + bw / 2, by0 + 26, names[0], weight="bold")
        put_c(lb, x + bw / 2, by0 + 52, names[1], weight="bold")
        put_c(lb, x + bw / 2, by0 + 80, rng)
    band = [(band_x0, band_y0), (band_x1, band_y0), (band_x1, band_y0 - 10), (tip, (band_y0 + band_y1) / 2),
            (band_x1, band_y1 + 10), (band_x1, band_y1), (band_x0, band_y1)]
    cv.path(band, w=1.4, close=True, fill=SHADE, oid="band", join="miter")
    ck.ok("帯は4つのまとまりの枠をすべて左右に貫く（帯の範囲が各枠の左端〜右端を含み、帯の高さが枠の中）",
          all(band_x0 < x and x + bw < band_x1 and by0 < band_y0 and band_y1 < by0 + bh for x in xs))
    put_c(lb, (band_x0 + band_x1) / 2, (band_y0 + band_y1) / 2, spine, weight="bold")
    allow_check(ck, lb, allow)
    cv.layout_checks(ck)

    return {"file": "L16_fig1_unit_map.svg", "lesson": "L16", "canvas": cv,
            "title": "単元の地図——4つのまとまりを「式をひとまとまりの対象として見る」の帯が貫く",
            "desc": ("横に4つの枠（多項式の計算 L01〜L04・恒等式と証明 L05〜L08・複素数と二次方程式 L09〜L12・因数定理と高次方程式 L13〜L15）を並べ、"
                     "その下の部分を、左から右へ1本の網かけの帯（矢じりつき）が貫く。帯に「式をひとまとまりの対象として見る」。"
                     "上の中央に太枠の「まとめ（L16）」を置き、4つの枠へ線でつなぐ。数字はレッスン番号だけ。同型図はまとまりの名前と番号を差し替えて生成する"),
            "alt": "単元の地図——多項式の計算（L01〜L04）、恒等式と証明（L05〜L08）、複素数と二次方程式（L09〜L12）、因数定理と高次方程式（L13〜L15）の4つのまとまりが順に並び、それらを「式をひとまとまりの対象として見る」という1本の帯が貫いている。まとめの L16 は、その全体を見わたす位置に置かれている",
            "intent": "総括回の1枚地図。4つのまとまりの順序と、それらを通す1つの見方（背骨）を同時に見せる。新しい概念・用語は図にも入れない",
            "src": "lesson_16.md §1（冒頭の段落の直後）",
            "params": "まとまり4つ（枠 134×146px・間隔 14px・左端 14px）／帯の高さ 192〜228px・左端 4px・矢じりの先 632px／まとめの枠 (228, 16, 150, 40)",
            "checks": ck.items,
            "check_tokens": ["(3x−2y)(9x²＋6xy＋4y²)", "x³−x²＋x＋5", "最小値", "k>4", "−20", "2±√3 i", "a=−1",
                             "1±2i", "x³＋6x²＋12x＋8", "x=0, −2", "8＋2a＋b=0", "p²−4q=0", "q<0", "2x²＋x＋4"],
            "digit_rule": ("strip", []),
            "allow_texts": allow}


# ===========================================================================
# main: 陽性対照 → 生成（2回・一致）→ 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L02_1, fig_L03_1, fig_L05_1, fig_L07_1, fig_L08_1, fig_L08_2, fig_L09_1, fig_L10_1,
        fig_L15_1, fig_L16_1]

TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
ALT_RE = re.compile(r"!\[(.*?)\]\(assets/([^)]+)\)")
COLOR_RE = re.compile(r'(?:fill|stroke)="([^"]+)"')
FONT_RE = re.compile(r'font-size="([0-9.]+)"')
NAME_RE = re.compile(r"L(\d\d)_fig(\d+)_[a-z0-9_]+\.svg")
_DASHES = "-‐‑‒–—―−ー－" + "・･·./:_" + " " + " " + "\t" + "•‣∙"


def svg_texts(src):
    return [unescape(m) for m in TEXT_RE.findall(src)]


def ban_hits(texts, bans):
    joined = "\n".join(texts)
    return [b for b in bans if b in joined]


def digit_problem(texts, rule):
    """図ごとの数字集合の制約。問題が無ければ None"""
    kind, allowed = rule
    runs = digit_runs(texts)
    if kind == "none":
        return None if not runs else f"数字が図中にある: {show_set(runs)}"
    if kind == "subset":
        extra = runs - set(allowed)
        return None if not extra else f"許可外の数字: {show_set(extra)}"
    if kind == "strip":
        rest = "\n".join(texts)
        for tok in allowed:
            rest = rest.replace(tok, "")
        rest = re.sub(r"L\d\d", "", rest)
        return None if not re.search(r"[0-9]", rest) else f"宣言外の数字が残る: {rest!r}"
    return f"未知の規則: {kind}"


def is_gray(c):
    c = c.lower()
    return c == "none" or bool(re.fullmatch(r"#([0-9a-f])\1\1", c) or re.fullmatch(r"#([0-9a-f]{2})\1\1", c))


def char_hygiene(s, where):
    """絵文字・結合文字・異体字セレクタ・不可視文字・制御文字・全角英数字を拒否する（公開側の検疫と同じ向き）"""
    bad = []
    for i, ch in enumerate(s):
        o = ord(ch)
        cat = unicodedata.category(ch)
        if ch in "\n\t":
            continue
        if cat in ("Cf", "Mn", "Me", "Cc", "Co", "Cn"):
            bad.append((i, hex(o), "invisible/combining/control"))
        elif 0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF or 0x3099 <= o <= 0x309C or o in (0xFF9E, 0xFF9F):
            bad.append((i, hex(o), "variation selector/sound mark"))
        elif 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF:
            bad.append((i, hex(o), "emoji/dingbat"))
        elif 0xFF10 <= o <= 0xFF19 or 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A:
            bad.append((i, hex(o), "fullwidth alphanumeric"))
    assert not bad, f"{where}: 禁止文字 {bad[:5]}"


def _vocab_words():
    """公開側の検疫語彙（.github/workflows/quarantine.yml と同じ語。このファイル自身が当たらないように連結で崩して書く）"""
    return ["INTER" + "NAL", "内部" + "用", "/" + "Users" + "/", "MERGE" + "_LOG", "QA" + "_REPORT",
            "run" + "_id", "source" + "_package",
            "public" + "_release_ready", "student" + "_distribution_ready", "external" + "_upload_ready",
            "sale" + "_ready", "canonical" + "_status", "オー" + "ナー", "監" + "督", "改稿" + "キュー"]


def _vocab_res():
    sep = "[" + re.escape(_DASHES) + "]+"
    return [re.compile("submit" + "[0-9]"), re.compile("D" + "[0-9]+" + "-" + "H" + "[0-9]+"),
            re.compile(r"\b" + "D" + r"[0-9]{1,2}\b"),
            re.compile("(?<![0-9A-Za-z])" + "D" + sep + "[0-9]"),
            re.compile("(?<![0-9A-Za-z])" + "H" + "R" + "(?:" + sep + ")?[0-9]")]


def vocab_hits(s):
    """NFKC 正規化した各行に、検疫語彙・内部 ID 形が現れるか（現れた語・パターンの並び）"""
    out = []
    for line in unicodedata.normalize("NFKC", s).splitlines():
        out += [w for w in _vocab_words() if w in line]
        out += [r.pattern for r in _vocab_res() if r.search(line)]
    return out


def ref_diff(theirs, mine):
    return sorted(theirs - mine), sorted(mine - theirs)


def gate_self_test():
    """検査器の陽性対照・陰性対照（検査器が噛むことを毎回実証する）"""
    sample = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
              '<text x="1" y="1">4C2=6</text><text x="2" y="2">x&lt;0</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["4C2=6", "x<0"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["4C2=6"]) == ["4C2=6"], "陽性対照失敗: 禁止文字列を検出できない"
    assert ban_hits(ts, ["5C3"]) == [], "陰性対照失敗: 存在しない文字列を誤検出"
    assert digit_runs(ts) == {"4", "2", "6", "0"}, "数字抽出が壊れている"
    assert digit_problem(["x=7"], ("subset", {"2", "3"})) is not None, "陽性対照失敗: 許可外の数字を見逃す"
    assert digit_problem(["L13〜L15"], ("strip", [])) is None and digit_problem(["L13 と 7"], ("strip", [])), \
        "数字の規則 strip の対照が壊れている"
    assert digit_problem(["虚数"], ("none", set())) is None and digit_problem(["2i"], ("none", set())), \
        "数字の規則 none の対照が壊れている"
    probes = ["a" + chr(0x200B) + "b", "e" + chr(0x0301), chr(0x2713) + chr(0xFE0F), chr(0xFF21) + chr(0xFF11),
              chr(0x1F600), "x" + chr(0x7), "キ" + chr(0xFF9E)]
    for probe in probes:
        try:
            char_hygiene(probe, "陽性対照")
        except AssertionError:
            continue
        raise AssertionError(f"文字衛生の陽性対照失敗: {probe!r} を検出できない")
    char_hygiene("x²＋5x＋8・(x−2)²≧0・√2・a³b・〜・→・÷・×・□△●・（L16）", "陰性対照")
    for probe in ["QA" + "_REPORT/x", "D" + "−" + "3", "D" + "・" + "7", chr(0xFF24) + "-" + "1", "監" + "督",
                  "/" + "Users" + "/x", "run" + "_id", "D" + "1" + "2", "H" + "R" + "3"]:
        assert vocab_hits(probe), f"公開語彙の陽性対照失敗: {probe!r} を検出できない"
    for neg in ["D>0・D=0・D<0", "判別式 D=4−4c", "まとめ（L16）", "y=x²−2x＋3", "実行モデル: claude-opus-5-5"]:
        assert not vocab_hits(neg), f"公開語彙の陰性対照失敗: {neg!r} を誤検出 {vocab_hits(neg)}"
    fake = "本文 ![甲](assets/L01_fig1_x.svg) と ![乙(1)](assets/L02_fig1_y.svg)"
    refs = {name: alt for alt, name in ALT_RE.findall(fake)}
    assert refs == {"L01_fig1_x.svg": "甲", "L02_fig1_y.svg": "乙(1)"}, f"参照の抽出が壊れている: {refs}"
    assert ref_diff(set(refs), {"L01_fig1_x.svg"}) == (["L02_fig1_y.svg"], []), "陽性対照失敗: 参照と生成の差を検出できない"
    assert ref_diff(set(refs), set(refs)) == ([], []), "陰性対照失敗: 一致を差ありと判定"
    assert is_gray("#d0d0d0") and is_gray("#fff") and not is_gray("#ff0000"), "グレー判定の対照が壊れている"


def svg_tech_checks(src, meta):
    """生成した SVG 文字列を、ファイルへ書く前に検査する（落ちれば例外で停止し、何も出力しない）"""
    name = meta["file"]
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag and 'xmlns="http://www.w3.org/2000/svg"' in root_tag, f"{name}: xmlns/viewBox がない"
    assert " width=" not in root_tag and " height=" not in root_tag, f"{name}: ルートに width/height を書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, f"{name}: 外部参照の疑い"
    assert "font-family" not in src, f"{name}: フォント指定は書かない（docs/SPEC_figures.md §5）"
    assert "<title>" in src and "<desc>" in src, f"{name}: title/desc がない"
    assert '<rect x="0" y="0"' in src and 'fill="#fff"' in src, f"{name}: 白背景がない"
    for pid in re.findall(r"url\(#([^)]+)\)", src):
        assert f'id="{pid}"' in src, f"{name}: 未定義の参照 #{pid}"
    colors = set(COLOR_RE.findall(src))
    assert all(is_gray(c) for c in colors), f"{name}: 白黒とグレー以外の色 {sorted(c for c in colors if not is_gray(c))}"
    sizes = [float(v) for v in FONT_RE.findall(src)]
    assert sizes and min(sizes) >= MIN_FS, f"{name}: 文字サイズの下限 {MIN_FS} を下回る"
    char_hygiene(src, name)
    vh = vocab_hits(src)
    assert not vh, f"{name}: 公開語彙の検疫に当たる {vh}"
    texts = svg_texts(src)
    got, allow = set(texts), set(meta["allow_texts"])
    assert got == allow, f"{name}: ラベル集合が許可リストと不一致 余分={sorted(got - allow)} 不足={sorted(allow - got)}"
    hits = ban_hits(texts + [meta["title"], meta["desc"]], meta.get("check_tokens", []))
    assert not hits, f"{name}: 禁止文字列が図中テキスト・title・desc にある: {hits}"
    prob = digit_problem(texts, meta["digit_rule"])
    assert prob is None, f"{name}: {prob}"
    return len(texts)


def lesson_refs():
    """本文の ![alt](assets/FILE) を実測（ファイル名→(alt, 本文ファイル名, 行番号)）。lesson_XX.md が無ければ None"""
    files = sorted(LESSON_DIR.glob("lesson_*.md"))
    if not files:
        return None
    refs = {}
    for f in files:
        for ln, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for alt, name in ALT_RE.findall(line):
                assert name not in refs, f"同じ図が2か所から参照されている: {name}"
                refs[name] = (alt, f.name, ln)
    return refs


def main():
    gate_self_test()
    own = Path(__file__).read_text(encoding="utf-8")
    char_hygiene(own, "generate_figures.py")
    vh = vocab_hits(own)
    assert not vh, f"generate_figures.py: 公開語彙の検疫に当たる {vh}"
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows, pending = [], []                # 全図の検査が通ってからまとめて書く
    n_checks = total_bytes = n_texts = 0
    for fn in FIGS:
        meta = fn()
        svg1 = meta["canvas"].svg(meta["file"], meta["title"], meta["desc"])
        meta2 = fn()
        svg2 = meta2["canvas"].svg(meta2["file"], meta2["title"], meta2["desc"])
        assert svg1 == svg2, f"{meta['file']}: 同一プロセス内の2回生成が一致しない"
        m = NAME_RE.fullmatch(meta["file"])
        assert m and f"L{m.group(1)}" == meta["lesson"], f"{meta['file']}: ファイル名が L{{NN}}_fig{{n}}_slug.svg でない"
        n_texts += svg_tech_checks(svg1, meta)
        n_checks += len(meta["checks"])
        total_bytes += len(svg1.encode("utf-8"))
        rows.append(meta)
        pending.append((ASSETS / meta["file"], svg1))
        print(f"OK {meta['file']}  [{len(meta['checks'])} checks passed]")
    assert len({m["file"] for m in rows}) == len(rows), "ファイル名が重複している"

    # 受け入れ検査: 参照と生成の集合・alt の一致・本文での登場順
    refs = lesson_refs()
    accept = []
    if refs is None:
        accept.append("本文 lesson_XX.md がこの階層に無いため、参照名・alt の照合は未実施")
    else:
        only_theirs, only_mine = ref_diff(set(refs), {m["file"] for m in rows})
        assert not only_theirs and not only_mine, f"参照と生成の差: 本文のみ={only_theirs} 生成のみ={only_mine}"
        accept.append(f"本文の図参照 {len(refs)} 件と生成ファイル {len(rows)} 件が完全一致（差集合 空・検査器は陽性対照で実証）")
        for m in rows:
            alt, src, _ = refs[m["file"]]
            assert src == f"lesson_{m['lesson'][1:]}.md", f"{m['file']}: 参照している本文が {src}"
            assert alt == m["alt"], f"{m['file']}: alt が本文（{src}）と不一致\n本文: {alt}\n仕様: {m['alt']}"
        accept.append("alt 文: 生成した全図で本文の alt とバイト単位で一致（assert）")
        swapped = []
        for les in sorted({m["lesson"] for m in rows}):
            mine = sorted((int(NAME_RE.fullmatch(m["file"]).group(2)), refs[m["file"]][2], m["file"])
                          for m in rows if m["lesson"] == les)
            if [ln for _, ln, _ in mine] != sorted(ln for _, ln, _ in mine):
                swapped.append(f"{les}（本文では " + "→".join(f for _, _, f in sorted(mine, key=lambda t: t[1])) + " の順）")
        if swapped:
            accept.append("連番の順（docs/SPEC_figures.md §3 はレッスン内の登場順）: 本文での登場順と連番が逆の図がある——"
                          + "・".join(swapped) + "。図の名前は単元の構成案の番号のまま。改名するときは本文と指導ノートの参照も同時に直す")
        else:
            accept.append("連番の順: どのレッスンでも本文での登場順と一致（docs/SPEC_figures.md §3）")
    for line in accept:
        print("ACCEPT", line)
    manifest = build_manifest(rows, n_checks, total_bytes, n_texts, accept)   # 台帳の検査もここで済ませる
    for out, svg in pending:                                                   # 全部通ってから書く
        out.write_text(svg, encoding="utf-8")
    (HERE / "FIGURE_MANIFEST.md").write_text(manifest, encoding="utf-8")
    n_tokens = sum(len(m.get("check_tokens", [])) for m in rows)
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks, {n_tokens} ban-tokens)")
    print(f"TOTAL {len(rows)} figures, {total_bytes} bytes, {n_checks} checks, {n_texts} labels")
    return rows, n_checks, total_bytes, accept


def build_manifest(rows, n_checks, total_bytes, n_texts, accept):
    """FIGURE_MANIFEST.md（図版台帳）の本文を組み立てて検査する。手編集禁止——スクリプトを直して再実行"""
    n_tokens = sum(len(m.get("check_tokens", [])) for m in rows)
    head = ["---", "distribution_status: published_draft", "---", "", MODEL_LINE, "", "<!--",
            f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
            "spec: docs/SPEC_figures.md 準拠",
            "license: CC-BY-4.0", "-->", ""]
    lines = head + [
        "# FIGURE_MANIFEST — 数学Ⅱ「いろいろな式」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的・乱数不使用）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト・図中ラベル {n_texts} 個。下表の検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。検算は数学（展開・筆算の各段・恒等式・判別式・値の表・三次方程式）、"
        "本文照合（図のパラメータの式・値・表の行が本文 lesson_XX.md にそのままあること）、"
        "描画の幾何（等角投影の描き順と上面の見え方・入れ子の包含・点と目盛りの位置）、"
        "配置（viewBox 内・ラベル同士が重ならない・ラベルが線にかからない・文字サイズが viewBox 幅の3%以上）の4種。"
        "加えて全SVGに XML整形式・xmlns/viewBox・width/height なし・外部参照なし・`<title>`/`<desc>`・白背景・"
        "色は白黒とグレーだけ・フォント指定なし の技術検査と、文字衛生検査（絵文字・結合文字・異体字セレクタ・"
        "不可視文字・全角英数字の不在）と、公開語彙の検疫と、答え漏れ検査を実施。答え漏れ検査は二重ゲート: "
        "(1)図中の全ラベルを、各図のパラメータブロックで宣言した許可リスト（本文が図の前後で明示している語と値のみ）と"
        f"集合として完全一致で照合、(2)禁止文字列（練習・stretch の答え由来・計{n_tokens}項目・対象値は非開示）が"
        "図中テキストと title・desc に無いことと、図ごとの数字集合の制約。検査器は生成前の陽性対照"
        "（禁止値・禁止文字・検疫語彙・参照の差を仕込んだ合成入力での検出）で毎回実証している。PASS。／ "
        "AI再利用メタ情報として全SVGに `<title>`/`<desc>`（意図・主要な値・同型図を描かせる説明文）を標準装備。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | alt（本文と同一） | パラメータ（本文一致） | 検証結果（生成時 assert） |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} 合格" for d, t in m["checks"])
        cells = [f"`{m['file']}`", m["lesson"], f"{m['title']}——{m['intent']}", m["src"], m["alt"], m["params"], checks]
        for c in cells:
            assert "|" not in c and "\n" not in c, f"{m['file']}: 台帳の表のセルに | か改行がある: {c[:60]}"
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## 受け入れ検査の結果", ""]
    for line in accept:
        lines.append(f"- {line}")
    lines += [
        f"- 各SVG: XML整形式・xmlns と viewBox あり・width/height なし・外部参照なし・`<title>`/`<desc>` あり・"
        f"白背景 rect あり・色は白黒とグレーだけ・font-family なし・文字サイズ {MIN_FS}px 以上（{len(rows)} 枚全件・スクリプトの技術検査で assert）",
        f"- 各図の assert が生成時に全件通過（計 {n_checks} 項目・上表）",
        "- 答え漏れ検査: `<text>` の文字列集合が各図の許可リストと完全一致・禁止文字列 0 件（図中テキスト・title・desc）・数字集合の制約を満たす（全図 assert）",
        "- 文字衛生・公開語彙: 本スクリプト・全SVG・本台帳で禁止文字 0 件・検疫語彙 0 件（assert）",
        "- 決定性: 乱数不使用。同一プロセス内で各図を2回生成してバイト一致を assert。別プロセスでの再実行の一致は、"
        "出荷時に全SVGと本台帳を2回生成して照合する（生成日は日付のみなので同日なら一致。"
        "台帳に載せる集合は整列して書くので、実行ごとの要素順の差は出ない）",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値・式は、いずれも本文（例題の与件・図の前後の明示値・表の値）のみ。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- L01_fig1 の辺の比 a:b=3:2 は、a, b が正の場合の見取り図のための固定比で、数値の例ではない（図に数値は書かない）。係数3の理由の説明（練習で問う）は図に書かない。",
        "- L03_fig1 の整数の筆算の途中の段（12・38・36）は、158÷12 の筆算そのものの段で、練習の答えではない。多項式の段（x²＋2x・3x＋8・3x＋6）は本文の手順1〜3に明示。"
        "両者が同じ段組み（x=10 を入れると整数の段になる）であることを assert で確かめている。",
        "- L08_fig1 の横の目盛りは表の x（1/4・1/2・1・2・4）を等間隔に並べたもの（図中に明記）。点どうしを結ばず、関数の名も出さない。",
        "- L15_fig1 の見取り図は、答えと別の描画用の高さ（辺の比 9：6：4）で描き、辺の長さの比から寸法の答えが読めないようにしている（assert）。",
        "- L09_fig1 は数の範囲の名前のみ（数値なし）。L16_fig1 の数字はレッスン番号（L01〜L16）のみ。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する（値は必ず該当 `lesson_XX.md` 本文と一致させる。本文照合の assert が不一致を止める）。",
        "2. この階層を作業フォルダにして `python3 generate_figures.py` を実行する。検算 assert・技術検査・答え漏れ検査・公開語彙の検疫・alt 照合に1つでも落ちると、SVG も本ファイルも書き出されない（既存の出力は前回のまま残る）。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    text = "\n".join(lines)
    char_hygiene(text, "FIGURE_MANIFEST.md")
    vh = vocab_hits(text)
    assert not vh, f"FIGURE_MANIFEST.md: 公開語彙の検疫に当たる {vh}"
    assert "**" not in text, "FIGURE_MANIFEST.md: 強調記号 ** を書かない（公開側の強調崩れ検査の対象を作らない）"
    return text


if __name__ == "__main__":
    main()
