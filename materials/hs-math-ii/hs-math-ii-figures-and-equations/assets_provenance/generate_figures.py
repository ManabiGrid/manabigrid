#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高校数学Ⅱ「図形と方程式」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（線は黒・塗りは白黒とグレーと斜線だけ・font-family なし・
xmlns と viewBox・title/desc・白背景・答え非記載・コード来歴）。各図の内容仕様（各 fig_* 関数冒頭の
パラメータブロック・Checker の検算項目・台帳の記載）は本文 lesson_XX.md と一致させる。
描画ヘルパーと検査器の組み立て（Canvas・Checker・許可リスト検査・禁止文字列検査・陽性対照・
台帳の自動生成）は先行単元の generate_figures.py（数学A「場合の数と確率」と数学Ⅱ「いろいろな式」）の
型を踏襲し、座標平面（x と y の目盛りの単位を等しくする Frame）・直線の窓への切り詰め・領域の塗り
（半平面・円の内部と外部・共通部分）・直角と等長の印・寸法線・数直線の部品は本単元向けに書き下ろした。

- 実行: python3 generate_figures.py（この階層を作業フォルダにして実行する）
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（18枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（datetime / fractions / html / math / pathlib / re / unicodedata /
  xml.etree）
- 決定性: 乱数・時刻に依存しない。日付は SVG 先頭コメントと台帳の generated 行・生成日行だけに現れる。
  台帳に載せる集合は整列してから書く（実行ごとの要素順の揺れを出さない）。
- 自己検証（1つでも落ちると例外で停止し、SVG も台帳も書き出さない）:
  (1) 図ごとの Checker——数学の検算（内分点・外分点・距離・垂直条件・点と直線の距離・対称な点・
      接線・軌跡の条件・領域の不等式・線形計画法の頂点の値）と描画の幾何（x と y の単位が等しい・
      直線が窓の端まで届く・塗った部分が不等式を満たす点の集合と一致する・境界線の線種が不等号と
      一致する）。
  (2) 本文照合——図のパラメータ（点の座標・式・比）が本文 lesson_XX.md（図の行を除いた本文）に
      そのまま書かれていることを、本文を読んで照合する（本文を直したら、このスクリプトも直すこと）。
  (3) 答えの分離（二重ゲート＋陽性対照）——各図の <text> の文字列集合がパラメータブロックで宣言した
      許可リストと完全一致すること、練習と stretch の答え由来の禁止文字列が図中テキストと title・desc に
      無いこと、図ごとの数字集合の制約。禁止文字列が許可ラベルの部分文字列になっていないことも確かめる。
      検査器は main() 冒頭の陽性対照で毎回実証する。
  (4) 配置検査——全要素が viewBox 内・ラベル同士が重ならない・ラベルが線にかからない・斜線の上の
      ラベルには白地を敷く・文字サイズが viewBox 幅の3%以上。
  (5) 文字衛生と公開語彙——絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字と、公開側の
      検疫語彙と、読点と鍵括弧の連続を、本スクリプト自身と全 SVG・台帳について機械検査する。
  (6) 受け入れ——本文の図参照の集合と生成ファイルの集合の完全一致、alt 文のバイト一致、連番の順。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの値を変えて再実行する。
  値は該当レッスン本文（lesson_XX.md）と一致させること。SVG の直接編集は禁止（来歴が切れる）。
"""

import datetime
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
MAIN_W = 1.6       # 主線幅（図形の辺・直線・円・境界線）
BOLD_W = 3.2       # 強調線幅
AUX_W = 1.1        # 補助線幅（破線）
DASH = "6 4"       # 破線（補助線と「境界線を含まない」境界線で共通）
THIN_W = 1.0       # 細線（目盛り・印・寸法線）
AXIS_W = 1.2       # 座標軸
DOT_R = 3.0        # 点マーカー半径
DOT_R_END = 3.4    # 数直線の●（数学Ⅰ「数と式」の数直線系と同じ値）
MARK = 9.0         # 直角の印の一辺（px）
PLATE_PAD = 2.0    # 斜線の上に置くラベルの白地の余白（px）
SHADE = "#d9d9d9"  # うすい網かけ
SHADE2 = "#b3b3b3" # 濃い網かけ
SHADE3 = "#efefef" # ごくうすい網かけ
HATCH_GAP = 8      # 斜線の間隔（px）
# font-family は書かない（docs/SPEC_figures.md §5。書体は閲覧環境に任せる）

ALT_RE = re.compile(r"!\[(.*?)\]\(assets/([^)]+)\)")


# ===========================================================================
# 幾何ユーティリティ（数学座標でも px 座標でも使う）
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


def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


def near_pt(p, q, tol=1e-9):
    return dist(p, q) < tol


def rot90(v):
    """数学座標で原点のまわりに左回りに 90° 回す"""
    return (-v[1], v[0])


def px_dir(v):
    """数学座標の向き（y 上向き）を px の単位ベクトル（y 下向き）に"""
    return unit((v[0], -v[1]))


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


def boxes_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def point_in_poly(p, poly):
    """偶奇規則による点の内外判定（境界の近くの点は検査側で除いてから使う）"""
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xin > x:
                inside = not inside
    return inside


def in_region(p, polys):
    """複数の多角形を偶奇規則で重ねた領域（外枠＋穴）の内外。SVG の fill-rule="evenodd" と同じ規則"""
    return sum(1 for poly in polys if point_in_poly(p, poly)) % 2 == 1


def clip_halfplane(poly, L):
    """多角形を半平面 ax＋by＋c≧0 で切り取る（Sutherland–Hodgman）。L=(a, b, c)"""
    a, b, c = L
    out = []
    n = len(poly)
    for i in range(n):
        P, Q = poly[i], poly[(i + 1) % n]
        fp = a * P[0] + b * P[1] + c
        fq = a * Q[0] + b * Q[1] + c
        if fp >= 0:
            out.append(P)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
    return out


def circle_pts(c, r, n=180):
    """円（数学座標）を n 等分した閉じた折れ線の頂点（arc フラグは使わない）"""
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def rect_pts(win):
    (x0, x1), (y0, y1) = win
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def line_val(L, p):
    return L[0] * p[0] + L[1] * p[1] + L[2]


def line_in_window(L, win):
    """直線 ax＋by＋c=0 と窓 [x0, x1]×[y0, y1] の共通部分（線分の両端）。交わらなければ None"""
    a, b, c = L
    (x0, x1), (y0, y1) = win
    pts = []
    if b != 0:
        for x in (x0, x1):
            y = -(a * x + c) / b
            if y0 - 1e-9 <= y <= y1 + 1e-9:
                pts.append((x, y))
    if a != 0:
        for y in (y0, y1):
            x = -(b * y + c) / a
            if x0 - 1e-9 <= x <= x1 + 1e-9:
                pts.append((x, y))
    uniq = []
    for p in pts:
        if all(dist(p, q) > 1e-9 for q in uniq):
            uniq.append(p)
    if len(uniq) < 2:
        return None
    d = (b, -a)
    uniq.sort(key=lambda p: dot(p, d))
    return uniq[0], uniq[-1]


def on_window_edge(p, win, tol=1e-9):
    (x0, x1), (y0, y1) = win
    return near(p[0], x0, tol) or near(p[0], x1, tol) or near(p[1], y0, tol) or near(p[1], y1, tol)


def dist_point_line(p, L):
    return abs(line_val(L, p)) / math.hypot(L[0], L[1])


def foot_on_line(p, L):
    a, b, _ = L
    t = line_val(L, p) / (a * a + b * b)
    return (p[0] - a * t, p[1] - b * t)


def reflect_on_line(p, L):
    a, b, _ = L
    t = line_val(L, p) / (a * a + b * b)
    return (p[0] - 2 * a * t, p[1] - 2 * b * t)


def dist_to_window_edge(p, win):
    (x0, x1), (y0, y1) = win
    return min(abs(p[0] - x0), abs(p[0] - x1), abs(p[1] - y0), abs(p[1] - y1))


# ===========================================================================
# 数の表記・文字幅の推定・数字の抽出
# ===========================================================================
def fmt(v):
    """数を本文の表記で（負号は U+2212。整数は小数点なし・分数は a/b）。int か Fraction を渡す"""
    v = Fr(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return s.replace("-", "−")


def pt_label(name, x, y):
    """点のラベル「A(−3, 1)」（本文の書き方: コンマの後に半角空白）"""
    return f"{name}({fmt(x)}, {fmt(y)})"


_SPECIAL_W = {" ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4, ":": 0.35, "°": 0.45,
              "→": 1.0, "←": 1.0, "・": 1.0, "×": 1.0, "〜": 1.0, "−": 1.0, "√": 1.0, "≧": 1.0, "≦": 1.0,
              "=": 0.6, "<": 0.6, ">": 0.6, "′": 0.5, "₁": 0.6, "₂": 0.6}


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
    """ラベル群に含まれる数字の連なり（「A(−3, 1)」→ {"3", "1"}）。上付き・下付きの数字は数えない"""
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
        self.defs = []           # 斜線の <pattern>
        self.texts = []          # dict(box, s, own, plate)
        self.obstacles = []      # (oid, [pts...])  ラベルがかかってはいけない線
        self.textured = []       # 斜線の塗り（px の多角形の組・偶奇規則）。この上のラベルには白地が要る
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

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, oid="line"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w)
        self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="#000" stroke-width="{w}"{d}/>')
        self.obstacle(oid, [(x1, y1), (x2, y2)])

    def path(self, pts, w=MAIN_W, dash=None, close=False, fill="none", oid="line", join="round"):
        """折れ線（close=True なら多角形）。fill を指定すると塗りつぶし＋輪郭"""
        for x, y in pts:
            self._grow(x, y, w / 2.0)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="{fill}" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="{join}"{d}/>')
        self.obstacle(oid, list(pts) + ([pts[0]] if close else []))

    def fill_region(self, polys, fill, textured=True):
        """塗り（輪郭なし）。polys は px の多角形の組で、偶奇規則（外枠＋穴）で重ねる"""
        parts = []
        for poly in polys:
            for x, y in poly:
                self._grow(x, y)
            parts.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in poly) + " Z")
        rule = ' fill-rule="evenodd"' if len(polys) > 1 else ""
        self.raw(f'<path d="{" ".join(parts)}" fill="{fill}" stroke="none"{rule}/>')
        if textured:
            self.textured.append([list(p) for p in polys])

    def pattern(self, pid, angle, gap=HATCH_GAP, sw=1.0):
        """斜線の塗り（<defs><pattern> で内蔵・ファイル内で完結）。angle は SVG の回転角（度）"""
        if not any(f'id="{pid}"' in d for d in self.defs):
            self.defs.append(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}" '
                             f'patternTransform="rotate({angle})">'
                             f'<line x1="{gap / 2}" y1="0" x2="{gap / 2}" y2="{gap}" stroke="#000" '
                             f'stroke-width="{sw}"/></pattern>')
        return f"url(#{pid})"

    def dot(self, x, y, r=DOT_R, oid="dot"):
        self._grow(x, y, r)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')
        self.obstacle(oid, [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r), (x - r, y - r)])

    def rect(self, x, y, w, h, fill="none", sw=1.4, dash=None, oid="line"):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], w=sw, dash=dash, close=True,
                  fill=fill, oid=oid, join="miter")

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, own=(), plate=False):
        """(x, y) はベースライン。推定ボックスを記録する。plate=True なら白地を先に敷く"""
        w = est_w(s, size)
        x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        box = (x0, y - 0.8 * size, x0 + w, y + 0.22 * size)
        e = PLATE_PAD if plate else 0.0
        self.texts.append({"box": box, "s": s, "own": tuple(own), "plate": plate})
        self.font_sizes.append(size)
        self._grow(box[0] - e, box[1] - e)
        self._grow(box[2] + e, box[3] + e)
        if plate:
            self.overlay.append(f'<rect x="{box[0] - e:.1f}" y="{box[1] - e:.1f}" width="{box[2] - box[0] + 2 * e:.1f}" '
                                f'height="{box[3] - box[1] + 2 * e:.1f}" fill="#fff" stroke="none"/>')
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
        self.fill_region([pts], "#000", textured=False)
        self.obstacle(oid, pts + [pts[0]])

    def layout_checks(self, ck, pad=1.0):
        """共通 assert: viewBox 内／ラベル同士が重ならない／ラベルが線にかからない／斜線の上は白地／文字サイズ"""
        ck.ok("全要素が viewBox 内に収まる（線幅・推定文字幅・白地込み）",
              self.bbox[0] >= 0 and self.bbox[1] >= 0 and self.bbox[2] <= self.w and self.bbox[3] <= self.h,
              f"bbox=({self.bbox[0]:.1f},{self.bbox[1]:.1f})-({self.bbox[2]:.1f},{self.bbox[3]:.1f})")
        boxes = []
        for t in self.texts:
            x0, y0, x1, y1 = t["box"]
            e = PLATE_PAD if t["plate"] else 0.0
            boxes.append((x0 - e, y0 - e, x1 + e, y1 + e))
        bad = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if boxes_overlap(boxes[i], boxes[j]):
                    bad.append((self.texts[i]["s"], self.texts[j]["s"]))
        ck.ok("ラベル同士が重ならない（推定ボックスの全ペア・白地込み）", not bad, f"{bad}")
        hits = []
        for t, bx in zip(self.texts, boxes):
            r = (bx[0] - pad, bx[1] - pad, bx[2] + pad, bx[3] + pad)
            for oid, pts in self.obstacles:
                if oid in t["own"]:
                    continue
                if any(seg_intersects_rect(a, b, r) for a, b in zip(pts, pts[1:])):
                    hits.append((t["s"], oid))
                    break
        ck.ok("ラベルが線（軸・目盛り・直線・円・枠・矢印・点・印）にかからない", not hits, f"{hits}")
        need = []
        for t in self.texts:
            if t["plate"]:
                continue
            x0, y0, x1, y1 = t["box"]
            samples = [(x0 + (x1 - x0) * i / 4, y0 + (y1 - y0) * j / 2) for i in range(5) for j in range(3)]
            if any(in_region(s, polys) for polys in self.textured for s in samples):
                need.append(t["s"])
        ck.ok("斜線の塗りの上に置いたラベルには白地を敷いている", not need, f"{need}")
        ck.ok(f"文字サイズがすべて {MIN_FS}px 以上（viewBox 幅の3%）",
              bool(self.font_sizes) and min(self.font_sizes) >= MIN_FS,
              f"min={min(self.font_sizes) if self.font_sizes else None}")

    def svg(self, fig_id, title, desc):
        defs = f"<defs>{''.join(self.defs)}</defs>\n" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md 準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + ("\n" if self.body else "")
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

    def c(self, x, y, s, size=None, **kw):
        """(x, y) を推定ボックスの中心にして置く"""
        sz = size or self.fs
        return self.put(x, y + 0.29 * sz, s, size=sz, **kw)

    def at(self, p, ang, d, s, **kw):
        """点 p（px）から、画面上の角 ang（度・右が 0・上が 90）の向きに d px 離れた所を中心にして置く"""
        a = math.radians(ang)
        return self.c(p[0] + d * math.cos(a), p[1] - d * math.sin(a), s, **kw)


class Frame:
    """数学座標（y 上向き）→ px。x と y の目盛りの単位は等しい（1つの s だけを持つ）。
    窓 win=((x0, x1), (y0, y1)) の左上を px の (left, top) に置く"""
    def __init__(self, left, top, win, s):
        (x0, x1), (y0, y1) = win
        self.win, self.s = win, s
        self.ox = left - s * x0
        self.oy = top + s * y1

    def P(self, p):
        return (self.ox + self.s * p[0], self.oy - self.s * p[1])

    def Ps(self, pts):
        return [self.P(p) for p in pts]

    def unit_px(self):
        o, ex, ey = self.P((0, 0)), self.P((1, 0)), self.P((0, 1))
        return dist(o, ex), dist(o, ey)


def equal_units(ck, *frames):
    """x と y の目盛りの単位が等しい（本文 L04 の対照表・x 軸と y 軸で同じ単位にする）"""
    u = [f.unit_px() for f in frames]
    ck.ok("x 軸と y 軸の目盛りの単位が等しい（1 目盛りの px が縦横で同じ）",
          all(near(a, b) for a, b in u) and all(near(u[0][0], a) for a, _ in u),
          "・".join(f"{a:.1f}px" for a, _ in u))


def draw_axes(cv, lb, fr, xr=None, yr=None, ticks=True, xlabel="x", ylabel="y", origin="O",
              origin_ang=225.0, origin_d=17.0, plate=False):
    """座標軸（矢印つき）・目盛り（整数ごと）・x と y の文字・原点 O（ラベルは lb に登録）。
    plate=True なら O と y の文字に白地を敷く（斜線の塗りの上に来るため）"""
    (wx0, wx1), (wy0, wy1) = fr.win
    x0, x1 = xr if xr else (wx0, wx1)
    y0, y1 = yr if yr else (wy0, wy1)
    a0, a1 = fr.P((x0, 0)), fr.P((x1, 0))
    cv.arrow(a0[0], a0[1], a1[0], a1[1], w=AXIS_W, oid="axis")
    b0, b1 = fr.P((0, y0)), fr.P((0, y1))
    cv.arrow(b0[0], b0[1], b1[0], b1[1], w=AXIS_W, oid="axis")
    if ticks:
        for k in range(math.ceil(x0), math.floor(x1) + 1):
            if k != 0 and x0 + 0.2 < k < x1 - 0.35:
                p = fr.P((k, 0))
                cv.line(p[0], p[1] - 3.5, p[0], p[1] + 3.5, w=THIN_W, oid="tick")
        for k in range(math.ceil(y0), math.floor(y1) + 1):
            if k != 0 and y0 + 0.2 < k < y1 - 0.35:
                p = fr.P((0, k))
                cv.line(p[0] - 3.5, p[1], p[0] + 3.5, p[1], w=THIN_W, oid="tick")
    if xlabel:
        lb.put(a1[0] + 7, a1[1] + 0.35 * FS, xlabel, anchor="start")
    if ylabel:
        lb.put(b1[0] + 8 + (2 if plate else 0), b1[1] + 11 + (3 if plate else 0), ylabel, anchor="start", plate=plate)
    if origin:
        lb.at(fr.P((0, 0)), origin_ang, origin_d, origin, plate=plate)


def right_mark(cv, V, u1, u2, k=MARK, oid="mark"):
    """頂点 V（px）で、px の単位ベクトル u1・u2 の間に直角の印（小さな正方形の2辺）"""
    a = (V[0] + k * u1[0], V[1] + k * u1[1])
    b = (a[0] + k * u2[0], a[1] + k * u2[1])
    c = (V[0] + k * u2[0], V[1] + k * u2[1])
    cv.path([a, b, c], w=THIN_W, oid=oid)


def equal_ticks(cv, p, q, n=1, size=6.0, gap=4.0, oid="mark"):
    """線分 pq（px）の中点に、長さが等しいことの印（線分に交わる短い線 n 本）"""
    m = mid(p, q)
    d = unit(sub(q, p))
    nr = (-d[1], d[0])
    for i in range(n):
        off = (i - (n - 1) / 2) * gap
        c = (m[0] + d[0] * off, m[1] + d[1] * off)
        cv.line(c[0] - nr[0] * size, c[1] - nr[1] * size, c[0] + nr[0] * size, c[1] + nr[1] * size,
                w=THIN_W, oid=oid)


def dim_line(cv, p, q, tick=5.0, oid="dim"):
    """寸法線（細実線＋両端のティック）。p, q は px"""
    cv.line(p[0], p[1], q[0], q[1], w=THIN_W, oid=oid)
    d = unit(sub(q, p))
    nr = (-d[1], d[0])
    for e in (p, q):
        cv.line(e[0] - nr[0] * tick, e[1] - nr[1] * tick, e[0] + nr[0] * tick, e[1] + nr[1] * tick,
                w=THIN_W, oid=oid)


def arc_arrow(cv, fr, center, r, a0, a1, head=8.0, oid="arc"):
    """中心 center・半径 r（数学座標）の円弧を角 a0→a1（度・左回り）で折れ線に描き、終端に矢じり"""
    n = max(8, int(abs(a1 - a0) / 2))
    pts = [fr.P((center[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 center[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))) for i in range(n + 1)]
    cv.path(pts[:-1], w=THIN_W, oid=oid)
    tip, prev = pts[-1], pts[-2]
    ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
    bx, by = tip[0] - head * math.cos(ang), tip[1] - head * math.sin(ang)
    nx, ny = -math.sin(ang), math.cos(ang)
    tri = [tip, (bx + nx * head * 0.45, by + ny * head * 0.45), (bx - nx * head * 0.45, by - ny * head * 0.45)]
    cv.fill_region([tri], "#000", textured=False)
    cv.obstacle(oid, tri + [tri[0]])
    return pts


def draw_line_in_window(cv, fr, L, win=None, w=MAIN_W, dash=None, oid="line"):
    """直線 ax＋by＋c=0 を窓の端から端まで描く（両端は窓の辺の上）。数学座標の両端を返す"""
    seg = line_in_window(L, win or fr.win)
    assert seg is not None, f"直線 {L} が窓と交わらない"
    p, q = fr.P(seg[0]), fr.P(seg[1])
    cv.line(p[0], p[1], q[0], q[1], w=w, dash=dash, oid=oid)
    return seg


def draw_circle(cv, fr, c, r, w=MAIN_W, dash=None, oid="circle"):
    pts = fr.Ps(circle_pts(c, r))
    cv.path(pts, w=w, dash=dash, close=True, oid=oid)


# ===========================================================================
# 本文の読み取り・許可リスト・禁止文字列・領域の検査
# ===========================================================================
def lesson_text(n):
    """lesson_NN.md の全文（無ければ None）"""
    f = LESSON_DIR / f"lesson_{n:02d}.md"
    return f.read_text(encoding="utf-8") if f.exists() else None


def lesson_body(n):
    """lesson_NN.md から図の行（![alt](assets/…)）を除いた本文（alt だけにある値で照合しないため）"""
    t = lesson_text(n)
    if t is None:
        return None
    return "\n".join(line for line in t.splitlines() if not ALT_RE.search(line))


def body_has(ck, n, needles, what):
    """本文（図の行を除く）に needles（図のパラメータから組み立てた文字列）が全部あることを照合する"""
    t = lesson_body(n)
    if t is None:
        ck.ok(f"本文照合（{what}）: lesson_{n:02d}.md がこの階層に無いため未実施", True)
        return
    miss = [s for s in needles if s not in t]
    ck.ok(f"本文照合（{what}）: lesson_{n:02d}.md の本文（図の行を除く）に {len(needles)} 件の文字列がそのままある",
          not miss, f"欠落={miss}")


def allow_check(ck, lb, allow):
    got, want = set(lb.items), set(allow)
    ck.ok(f"図中ラベルの集合が、パラメータブロックで宣言した許可リスト（{len(want)}種）と一致",
          got == want, f"余分={sorted(got - want)} 不足={sorted(want - got)}")


def ban_consistency(ck, allow, bans):
    clash = sorted({b for b in bans for s in allow if b in s})
    ck.ok(f"禁止文字列（{len(bans)}件）はどれも許可ラベルの部分文字列でない（答え漏れ検査が図の正しいラベルを誤検出しない）",
          not clash, "" if not clash else f"{clash}")


def region_check(ck, what, polys, pred, bdist, win, step=0.25, margin=0.1):
    """塗った部分（数学座標の多角形の組・偶奇規則）と、不等式 pred を満たす点の集合の一致を、
    窓の中の格子点（格子は窓の辺からずらす）で調べる。境界から margin 以内の点は除く"""
    (x0, x1), (y0, y1) = win
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    n_ok = n_skip = 0
    bad = []
    for i in range(nx):
        for j in range(ny):
            p = (x0 + (i + 0.5) * step, y0 + (j + 0.5) * step)
            if bdist(p) < margin or dist_to_window_edge(p, win) < margin:
                n_skip += 1
                continue
            if in_region(p, polys) != bool(pred(p)):
                bad.append((round(p[0], 3), round(p[1], 3)))
            else:
                n_ok += 1
    ck.ok(f"塗った部分＝{what}（窓の中の格子点 {n_ok} 点で一致・境界の近くの {n_skip} 点は除く）",
          not bad and n_ok > 100, f"{bad[:3]}")


def boundary_style_check(ck, what, strict, dash):
    ck.ok(f"境界線の線種が不等号と一致（{what}: {'< か > なので破線' if strict else '≦ か ≧ なので実線'}）",
          (dash is not None) == strict, f"dash={dash}")


# ===== 図の関数はこの下 =====================================================
# ===========================================================================
# L01: 数直線上の内分点・外分点
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md 例題2・例題3・例題4） ---
    a, b = -2, 8                                   # A(a)、B(b)
    divs = [("P", "内", 3, 2), ("Q", "外", 3, 1), ("R", "外", 1, 3)]
    lo, hi = -9, 15                                # 目盛りの範囲（1 ごと）
    UNIT, X_LO, Y, H = 23.0, 44.0, 64.0, 116       # 1目盛りの px・lo の px・数直線の高さ・viewBox の高さ
    xp = lambda v: X_LO + (v - lo) * UNIT

    ck = Checker()
    vals = {}
    for name, kind, m, n in divs:
        vals[name] = Fr(n * a + m * b, m + n) if kind == "内" else Fr(-n * a + m * b, m - n)
    ck.ok("内分点 P=(2×(−2)＋3×8)/(3＋2)=4", vals["P"] == 4)
    ck.ok("外分点 Q=(−1×(−2)＋3×8)/(3−1)=13", vals["Q"] == 13)
    ck.ok("外分点 R=(−3×(−2)＋1×8)/(1−3)=−7 で、分母を正にした (3×(−2)−1×8)/(3−1) と同じ値",
          vals["R"] == -7 and Fr(3 * a - 1 * b, 3 - 1) == -7)
    for name, kind, m, n in divs:
        v = vals[name]
        la, lb_ = abs(v - a), abs(b - v)
        ck.ok(f"{name} の検算: A{name}:{name}B={fmt(la)}:{fmt(lb_)}={m}:{n}", la * n == lb_ * m)
    ck.ok("内分点 P は A と B の間にある", a < vals["P"] < b)
    ck.ok("外分点は比の数が小さい方の端の外側（Q は 3>1 で B の外側・R は 1<3 で A の外側）",
          vals["Q"] > b and vals["R"] < a)
    ck.ok("目盛りの範囲が5点を含み、両端に1目盛り以上の余白がある",
          lo + 1 <= min(vals["R"], a) and max(vals["Q"], b) <= hi - 1)
    ck.ok("●の半径は数学Ⅰ「数と式」の数直線系と同じ 3.4px（描き方の統一）", DOT_R_END == 3.4)
    body_has(ck, 1, ["2点 A(−2)、B(8) について、線分 AB を 3:2 に内分する点 P の座標を求めよ",
                     "p=(2×(−2)＋3×8)/(3＋2)=(−4＋24)/5=20/5=**4**",
                     "2点 A(−2)、B(8) について、線分 AB を 3:1 に外分する点 Q の座標を求めよ",
                     "q=(−1×(−2)＋3×8)/(3−1)=(2＋24)/2=26/2=**13**",
                     "2点 A(−2)、B(8) について、線分 AB を 1:3 に外分する点 R の座標を求めよ",
                     "r=(3×(−2)−1×8)/(3−1)=(−6−8)/2=−14/2=**−7**"], "例題2〜例題4 の点・比・答え")

    cv = Canvas(W, H)
    lb = Labels(cv)
    cv.arrow(xp(0), Y, xp(hi) + 14, Y, w=AXIS_W, oid="axis")
    cv.arrow(xp(0), Y, xp(lo) - 14, Y, w=AXIS_W, oid="axis")
    for v in range(lo, hi + 1):
        cv.line(xp(v), Y - 4, xp(v), Y + 4, w=THIN_W, oid="tick")
    cv.line(xp(a), Y, xp(b), Y, w=BOLD_W, oid="seg")          # 線分 AB
    pts = [("A", Fr(a)), ("B", Fr(b))] + [(nm, vals[nm]) for nm, _, _, _ in divs]
    for nm, v in pts:
        cv.dot(xp(v), Y, r=DOT_R_END)
        lb.put(xp(v), Y - 15, f"{nm}({fmt(v)})")
    lb.put(xp(0), Y + 28, "0")
    caps = []
    for nm, kind, m, n in divs:
        cap = f"{m}:{n} の{kind}分点"
        caps.append(cap)
        lb.put(xp(vals[nm]), Y + 28, cap)
    allow = [f"{nm}({fmt(v)})" for nm, v in pts] + ["0"] + caps
    ck.ok("点のラベルの座標は、式で計算した値を書いたもの（P(4)・Q(13)・R(−7)）",
          allow[2:5] == ["P(4)", "Q(13)", "R(−7)"])
    allow_check(ck, lb, allow)
    bans = ["−11", "19", "2:1", "4:1", "5:3", "A(2)", "B(5)", "Q(8)", "(9)", "(−1)"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L01_fig1_number_line_division_points.svg", "lesson": "L01", "canvas": cv,
            "title": "数直線上の内分点と外分点——A(−2)、B(8) の 3:2 の内分点 P(4)・3:1 の外分点 Q(13)・1:3 の外分点 R(−7)",
            "desc": ("−9〜15 の目盛りの数直線に線分 AB（A(−2)、B(8)）を太線で示し、3:2 の内分点 P(4) を A と B の間に、"
                     "3:1 の外分点 Q(13) を B の外側に、1:3 の外分点 R(−7) を A の外側に●で打つ。点の名と座標を上に、"
                     "比と内分点・外分点の別を下に書く。●の描き方は数学Ⅰ「数と式」の数直線と同じ。"
                     "同型図は A と B の座標と比 m:n を差し替えて生成する（内分点は (na＋mb)/(m＋n)、外分点は (−na＋mb)/(m−n) で計算する）"),
            "alt": "数直線上に A(−2)、B(8) をとり、3:2 の内分点 P(4)、3:1 の外分点 Q(13)、1:3 の外分点 R(−7) の位置を目盛りで示した図。内分点は A と B の間に、外分点は比の数が小さい方の端の外側にある",
            "intent": "内分点と外分点を同じ「比に分ける点」として1本の数直線に並べ、内分点は線分の内側に、外分点は比の数が小さい方の端の外側に出ることを目盛りで見せる",
            "src": "lesson_01.md §3（例題4の解答の直後）",
            "params": "A(−2)・B(8)／P は 3:2 の内分・Q は 3:1 の外分・R は 1:3 の外分（座標は式から計算）／数直線 −9〜15（1目盛り 23px）／線分 AB は太線 3.2px／●半径 3.4px",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2", "3", "4", "7", "8", "13"}), "allow_texts": allow}


# ===========================================================================
# L02: 2点間の距離の直角三角形・平面上の内分点を軸へ落とす図
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（lesson_02.md §1。文字だけの図なので、点の位置は描く値） ---
    A, B = (1.6, 1.3), (6.0, 4.3)          # 描く位置（x₂>x₁・y₂>y₁ になる位置。図に数値は書かない）
    C = (B[0], A[1])                       # 直角の頂点 C(x₂, y₁)
    win, s = ((-0.7, 7.3), (-0.7, 5.2)), 62.0
    left, top = 60.0, 16.0
    labA, labB, labC = "A(x₁, y₁)", "B(x₂, y₂)", "C(x₂, y₁)"
    lab_h, lab_v = "x₂−x₁", "y₂−y₁"
    allow = [labA, labB, labC, lab_h, lab_v, "x₁", "x₂", "y₁", "y₂", "x", "y", "O"]

    ck = Checker()
    ck.ok("C の x 座標は B と同じ・y 座標は A と同じ（C(x₂, y₁)）", C == (B[0], A[1]))
    ck.ok("AC は x 軸に平行・CB は y 軸に平行で、角 C は直角（内積 0）",
          near(A[1], C[1]) and near(B[0], C[0]) and near(dot(sub(A, C), sub(B, C)), 0.0))
    ck.ok("三平方の定理: AB²=AC²＋CB²（描いた長さで）",
          near(dist(A, B) ** 2, dist(A, C) ** 2 + dist(C, B) ** 2), f"{dist(A, B) ** 2:.4f}")
    ck.ok("x₂>x₁・y₂>y₁ の位置なので、辺のラベル x₂−x₁・y₂−y₁ はそのまま長さ", B[0] > A[0] and B[1] > A[1])
    body_has(ck, 2, ["点 C(x₂, y₁) をとると、AC は x 軸に平行で長さ |x₂−x₁|、BC は y 軸に平行で長さ |y₂−y₁| であり、角 C は直角である",
                     "AB² = (x₂−x₁)²＋(y₂−y₁)²"], "C の座標と三平方の定理の式")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 34)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr, ticks=False)
    pA, pB, pC = fr.P(A), fr.P(B), fr.P(C)
    for p, q in [(A, (A[0], 0)), (A, (0, A[1])), (C, (C[0], 0)), (B, (0, B[1]))]:
        P1, Q1 = fr.P(p), fr.P(q)
        cv.line(P1[0], P1[1], Q1[0], Q1[1], w=AUX_W, dash=DASH, oid="guide")
    cv.path([pA, pC, pB], w=MAIN_W, close=True, oid="tri")
    right_mark(cv, pC, px_dir((-1, 0)), px_dir((0, 1)))
    for p in (pA, pB, pC):
        cv.dot(p[0], p[1])
    o = fr.P((0, 0))
    lb.at(pA, 155, 44, labA)
    lb.put(pB[0] + 9, pB[1] + 6, labB, anchor="start")
    lb.put(pC[0] + 9, pC[1] + 22, labC, anchor="start")
    lb.c((pA[0] + pC[0]) / 2, pC[1] + 17, lab_h)
    lb.put(pC[0] + 9, (pB[1] + pC[1]) / 2 + 0.29 * FS, lab_v, anchor="start")
    lb.c(pA[0], o[1] + 17, "x₁")
    lb.c(pC[0], o[1] + 17, "x₂")
    lb.c(o[0] - 17, pA[1], "y₁")
    lb.c(o[0] - 17, pB[1], "y₂")
    allow_check(ck, lb, allow)
    bans = ["2√13", "(0, 4)", "(1, 9/2)", "(−24, −8)", "(26, 17)", "(5, −8)", "(6, 9)", "(0, −4)", "x²＋y²=9", "5√2"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L02_fig1_distance_right_triangle.svg", "lesson": "L02", "canvas": cv,
            "title": "2点間の距離の公式を導く直角三角形——AB を斜辺とし C(x₂, y₁) を直角の頂点とする",
            "desc": ("座標平面に A(x₁, y₁)、B(x₂, y₂) と C(x₂, y₁) をとり、線分 AB を斜辺とする直角三角形を描く。"
                     "横の辺 AC に x₂−x₁、縦の辺 CB に y₂−y₁ のラベルを付け、C に直角の印。A と B から軸へ破線を下ろし、"
                     "軸の上に x₁・x₂・y₁・y₂ を書く。数値は書かない（文字だけの図）。同型図は A と B の描く位置を差し替えて生成する"),
            "alt": "2点 A(x₁, y₁)、B(x₂, y₂) を結ぶ線分を斜辺とし、点 C(x₂, y₁) を直角の頂点とする直角三角形。横の辺に x₂−x₁、縦の辺に y₂−y₁ のラベルがある",
            "intent": "中3の「直角三角形を見つける」を文字の座標で行い、横と縦の辺の長さが座標の差になることを見せて、三平方の定理から距離の公式へつなぐ",
            "src": "lesson_02.md §1（距離の公式を導いた直後）",
            "params": "描く位置 A(1.6, 1.3)・B(6.0, 4.3)（x₂>x₁・y₂>y₁ となる位置。図に数値は書かない）／C は B の x 座標と A の y 座標／1目盛り 62px（縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("none", set()), "allow_texts": allow}


def fig_L02_2():
    # --- パラメータ（lesson_02.md §2 例題4 (1)） ---
    A, B = (-3, 1), (5, 5)
    m, n = 3, 1
    P = (Fr(n * A[0] + m * B[0], m + n), Fr(n * A[1] + m * B[1], m + n))
    win, s = ((-4.6, 6.4), (-2.3, 5.9)), 44.0
    left, top = 64.0, 18.0
    dim_y, dim_x = -1.05, -1.05          # x 軸の下の寸法線の高さ・y 軸の左の寸法線の位置
    labA, labB, labP = pt_label("A", *A), pt_label("B", *B), pt_label("P", *P)
    allow = [labA, labB, labP, "A′", "P′", "B′", str(m), str(n), "x", "y", "O"]

    ck = Checker()
    ck.ok("P=((1×(−3)＋3×5)/(3＋1), (1×1＋3×5)/(3＋1))=(3, 4)", P == (3, 4))
    AP2 = (P[0] - A[0]) ** 2 + (P[1] - A[1]) ** 2
    PB2 = (B[0] - P[0]) ** 2 + (B[1] - P[1]) ** 2
    ck.ok("AP:PB=3:1（AP²=45・PB²=5 で AP²=9PB²・AP=3√5・PB=√5）", AP2 == 45 and PB2 == 5 and AP2 == 9 * PB2)
    ck.ok("x 軸上: A′P′:P′B′=(3−(−3)):(5−3)=6:2=3:1", (P[0] - A[0]) * n == (B[0] - P[0]) * m)
    ck.ok("y 軸上: (4−1):(5−4)=3:1", (P[1] - A[1]) * n == (B[1] - P[1]) * m)
    body_has(ck, 2, ["2点 A(−3, 1)、B(5, 5) について、次の点の座標を求めよ", "よって **P(3, 4)**",
                     "A′P′:P′B′=AP:PB=m:n"], "例題4 の2点と答え・平行線と線分の比")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 14)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr, xr=(-4.4, 6.3), yr=(-0.6, 5.8))
    pA, pB, pP = fr.P(A), fr.P(B), fr.P(P)
    o = fr.P((0, 0))
    for q in (A, P, B):
        for r in ((q[0], 0), (0, q[1])):
            P1, Q1 = fr.P(q), fr.P(r)
            cv.line(P1[0], P1[1], Q1[0], Q1[1], w=AUX_W, dash=DASH, oid="guide")
    cv.line(pA[0], pA[1], pB[0], pB[1], w=MAIN_W, oid="seg")
    for p in (pA, pB, pP):
        cv.dot(p[0], p[1])
    feet_x = [fr.P((q[0], 0)) for q in (A, P, B)]
    feet_y = [fr.P((0, q[1])) for q in (A, P, B)]
    for f in feet_x + feet_y:
        cv.dot(f[0], f[1], r=2.4)
    # 寸法線（x 軸の下・y 軸の左）と引き出し線
    dy = fr.P((0, dim_y))[1]
    for f in feet_x:
        cv.line(f[0], o[1] + 8, f[0], dy + 7, w=THIN_W, oid="ext")
    dim_line(cv, (feet_x[0][0], dy), (feet_x[1][0], dy))
    dim_line(cv, (feet_x[1][0], dy), (feet_x[2][0], dy))
    dx = fr.P((dim_x, 0))[0]
    for f in feet_y[1:]:
        cv.line(o[0] - 8, f[1], dx - 7, f[1], w=THIN_W, oid="ext")
    dim_line(cv, (dx, feet_y[0][1]), (dx, feet_y[1][1]))
    dim_line(cv, (dx, feet_y[1][1]), (dx, feet_y[2][1]))
    # ラベル
    lb.put(pA[0] - 9, pA[1] + 6, labA, anchor="end")
    lb.put(pB[0] + 9, pB[1] + 6, labB, anchor="start")
    lb.put(pP[0] + 9, pP[1] + 21, labP, anchor="start")
    for f, nm in zip(feet_x, ["A′", "P′", "B′"]):
        lb.put(f[0] - 5, o[1] - 8, nm, anchor="end")
    lb.c((feet_x[0][0] + feet_x[1][0]) / 2, dy + 17, str(m))
    lb.c((feet_x[1][0] + feet_x[2][0]) / 2, dy + 17, str(n))
    lb.c(dx - 13, (feet_y[0][1] + feet_y[1][1]) / 2, str(m))
    lb.c(dx - 13, (feet_y[1][1] + feet_y[2][1]) / 2, str(n))
    nrm = px_dir((1, -2))                      # 線分 AB の右下側の法線
    q1 = fr.P((A[0] + 0.62 * (P[0] - A[0]), A[1] + 0.62 * (P[1] - A[1])))
    q2 = fr.P(((P[0] + B[0]) / 2, (P[1] + B[1]) / 2))
    lb.c(q1[0] + 16 * nrm[0], q1[1] + 16 * nrm[1], str(m))
    lb.c(q2[0] + 16 * nrm[0], q2[1] + 16 * nrm[1], str(n))
    allow_check(ck, lb, allow)
    bans = ["(0, 4)", "(1, 9/2)", "(−24, −8)", "(26, 17)", "(5, −8)", "(6, 9)", "(0, −4)", "2√13",
            "Q(9, 7)", "M(1, 3)", "3√5", "(3, 3)"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L02_fig2_plane_division_point_projection.svg", "lesson": "L02", "canvas": cv,
            "title": "平面上の内分点を軸へ落とす——A(−3, 1)、B(5, 5) を 3:1 に内分する点 P(3, 4)",
            "desc": ("座標平面に A(−3, 1)、B(5, 5) と、線分 AB を 3:1 に内分する点 P(3, 4) を打ち、3点から x 軸と y 軸へ破線の垂線を下ろす。"
                     "x 軸上の足 A′、P′、B′ の間と、y 軸上の足の間に、寸法線で 3 と 1 の比を書く（線分 AB の上にも 3 と 1）。"
                     "1目盛りは縦横とも同じ長さ。同型図は A、B と比 m:n を差し替えて生成する（P は内分点の式で計算）"),
            "alt": "2点 A(−3, 1)、B(5, 5) と、線分 AB を 3:1 に内分する点 P(3, 4) から x 軸と y 軸に破線の垂線を下ろし、x 軸上と y 軸上でもそれぞれ 3:1 の内分になっていることを示す対応図",
            "intent": "平面上の内分点を「x 座標と y 座標のそれぞれで数直線の内分」に分ける見方（L01 の式を2回使う根拠）を、平行な垂線と寸法線で見せる",
            "src": "lesson_02.md §2（内分点・外分点の公式の直後・例題4の前）",
            "params": "A(−3, 1)・B(5, 5)・m:n=3:1／P=((1×(−3)＋3×5)/4, (1×1＋3×5)/4)=(3, 4)／窓 x −4.6〜6.4・y −2.3〜5.9（1目盛り 44px・縦横共通）／寸法線は x 軸の下 1.05・y 軸の左 1.05",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"1", "3", "4", "5"}), "allow_texts": allow}


# ===========================================================================
# L03: 同じ三角形に2通りの座標軸
# ===========================================================================
def fig_L03_1():
    # --- パラメータ（lesson_03.md §1 置き方1・置き方2。文字だけの図なので c と A の位置は描く値） ---
    c = 2.0                                  # 描く値の c（BM=MC=c）
    A_rel = (0.9, 2.3)                       # 中点 M から見た A の位置（描く値）
    s = 46.0
    heads = ["置き方1", "置き方2"]
    P1 = {"B": (0.0, 0.0), "C": (2 * c, 0.0), "M": (c, 0.0), "A": (c + A_rel[0], A_rel[1])}
    P2 = {"M": (0.0, 0.0), "B": (-c, 0.0), "C": (c, 0.0), "A": A_rel}
    L1 = {"B": "B(0, 0)", "C": "C(2c, 0)", "M": "M(c, 0)", "A": "A(a, b)"}
    L2 = {"M": "M(0, 0)", "B": "B(−c, 0)", "C": "C(c, 0)", "A": "A(a, b)"}
    wins = [((-0.9, 5.3), (-0.3, 3.4)), ((-3.1, 3.1), (-0.3, 3.4))]
    lefts, top = [20.0, 335.0], 40.0
    allow = heads + sorted(set(L1.values()) | set(L2.values())) + ["x", "y"]

    ck = Checker()
    for Pn, nm in ((P1, "置き方1"), (P2, "置き方2")):
        ck.ok(f"{nm}: M は辺 BC の中点", near_pt(Pn["M"], mid(Pn["B"], Pn["C"])))
    ck.ok("置き方1: B が原点で C は x 軸の正の向き（C(2c, 0)・M(c, 0)）",
          P1["B"] == (0.0, 0.0) and P1["C"] == (2 * c, 0.0) and P1["M"] == (c, 0.0))
    ck.ok("置き方2: M が原点で B(−c, 0)・C(c, 0)（対称な形）", P2["M"] == (0.0, 0.0) and P2["B"] == (-c, 0.0) and P2["C"] == (c, 0.0))
    sides = lambda Pn: sorted(round(dist(Pn[u], Pn[v]), 9) for u, v in (("A", "B"), ("B", "C"), ("C", "A")))
    ck.ok("2つのパネルは同じ三角形（3辺の長さが一致）", sides(P1) == sides(P2), f"{sides(P1)}")
    a1, a2, bb = P1["A"][0], P2["A"][0], A_rel[1]
    e1 = 2 * a1 ** 2 - 4 * a1 * c + 4 * c ** 2 + 2 * bb ** 2
    e2 = 2 * a2 ** 2 + 2 * c ** 2 + 2 * bb ** 2
    real = dist(P1["A"], P1["B"]) ** 2 + dist(P1["A"], P1["C"]) ** 2
    ck.ok("本文の2つの式（置き方1: 2a²−4ac＋4c²＋2b²・置き方2: 2a²＋2c²＋2b²）が、描いた三角形の AB²＋AC² と一致",
          near(e1, real) and near(e2, real), f"{real:.4f}")
    body_has(ck, 3, ["B(0, 0)、C(2c, 0)（c>0）、A(a, b) とおくと、M(c, 0) である",
                     "M(0, 0)、B(−c, 0)、C(c, 0)（c>0）、A(a, b) とおく"], "置き方1・置き方2 の座標")

    fr1 = Frame(lefts[0], top, wins[0], s)
    fr2 = Frame(lefts[1], top, wins[1], s)
    H = round(top + (wins[0][1][1] - wins[0][1][0]) * s + 30)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr1, fr2)
    for fr, Pn, Ln, head, win in ((fr1, P1, L1, heads[0], wins[0]), (fr2, P2, L2, heads[1], wins[1])):
        draw_axes(cv, lb, fr, yr=(0.0, 3.3), ticks=False, origin=None)
        pts = {k: fr.P(v) for k, v in Pn.items()}
        cv.path([pts["A"], pts["B"], pts["C"]], w=MAIN_W, close=True, oid="tri")
        for k in ("A", "B", "C", "M"):
            cv.dot(pts[k][0], pts[k][1])
        for k in ("B", "M", "C"):
            lb.c(pts[k][0], pts[k][1] + 17, Ln[k])
        lb.c(pts["A"][0], pts["A"][1] - 17, Ln["A"])
        cx = (fr.P((win[0][0], 0))[0] + fr.P((win[0][1], 0))[0]) / 2
        lb.c(cx, 22, head, weight="bold")
    allow_check(ck, lb, allow)
    bans = ["52", "32", "17", "(−3, 0)", "(3, 0)", "A(1, 4)", "(a＋b, c)", "(s, t)", "AB²＋AC²"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L03_fig1_axis_placement_two_panels.svg", "lesson": "L03", "canvas": cv,
            "title": "座標軸の置き方を2通り——同じ三角形 ABC で、B を原点にする置き方1と中点 M を原点にする置き方2",
            "desc": ("同じ三角形 ABC（M は辺 BC の中点）を2つのパネルに描く。左は B を原点・辺 BC を x 軸の正の向きに置き、B(0, 0)・C(2c, 0)・M(c, 0)・A(a, b)。"
                     "右は M を原点・辺 BC を x 軸に置き、M(0, 0)・B(−c, 0)・C(c, 0)・A(a, b)。2つのパネルは同じ縮尺で、三角形の形と大きさは同じ。"
                     "文字だけの図（数値なし）。同型図は描く値（c と A の位置）を差し替えて生成する"),
            "alt": "同じ三角形 ABC に2通りの座標軸を置いた2つの図。左は頂点 B を原点、辺 BC を x 軸に置き、B(0, 0)、C(2c, 0)、A(a, b)、M(c, 0)。右は中点 M を原点に置き、M(0, 0)、B(−c, 0)、C(c, 0)、A(a, b)",
            "intent": "座標軸は自分で置くもので、置き方で計算の量が変わることを、同じ三角形に2通りの軸を当てて見せる（中線定理の証明で置き方2を使う準備）",
            "src": "lesson_03.md §1（置き方1・置き方2を示した直後）",
            "params": "描く値 c=2・M から見た A の位置 (0.9, 2.3)（図に数値は書かない）／2パネルとも1目盛り 46px（縦横共通）／y 軸は x 軸から上だけを描く（原点にある点のラベルを軸で切らないため）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2"}), "allow_texts": allow}


# ===========================================================================
# L04: 一次関数のグラフと、関数のグラフでない直線 x=2
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（lesson_04.md §2。y=(1/2)x＋1 は並べて描く一次関数の例） ---
    slope, icpt, k = Fr(1, 2), 1, 2
    Lf = (float(slope), -1.0, float(icpt))       # (1/2)x−y＋1=0
    Lv = (1.0, 0.0, -float(k))                   # x−2=0
    win, s = ((-3.2, 7.4), (-2.8, 4.8)), 46.0
    left, top = 50.0, 18.0
    lab_f, lab_v, lab_note = "y=(1/2)x＋1", f"x={k}", "関数のグラフでない直線"
    allow = [lab_f, lab_v, lab_note, str(k), str(icpt), "x", "y", "O"]

    ck = Checker()
    ck.ok("y=(1/2)x＋1 は (0, 1) と (2, 2) を通る（傾き 1/2・y 軸との交点 1）",
          near(line_val(Lf, (0, 1)), 0) and near(line_val(Lf, (2, 2)), 0))
    pts_v = [(2, 0), (2, 1), (2, -3), (2, 5)]
    ck.ok("本文の4点 (2, 0)、(2, 1)、(2, −3)、(2, 5) はどれも x=2 の上にあり、y は4通り（x=2 に対して y が1つに決まらない）",
          all(near(line_val(Lv, p), 0) for p in pts_v) and len({p[1] for p in pts_v}) == 4)
    body_has(ck, 4, ["点 (2, 0)、(2, 1)、(2, −3)、(2, 5) はすべて x 座標が 2 で、y 座標は何でもよい",
                     "点 (2, 0) を通り y 軸に平行な直線である",
                     "x=2 に対して y の値が1つに決まらないので、一次関数のグラフではない"], "x=2 の点と、関数のグラフでない理由")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 18)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr)
    sf = draw_line_in_window(cv, fr, Lf, oid="line")
    sv = draw_line_in_window(cv, fr, Lv, oid="line")
    ck.ok("2本とも窓の端から端まで描く（両端が窓の辺の上）",
          all(on_window_edge(p, win) for p in (*sf, *sv)))
    ck.ok("x=2 は縦の直線（両端の x が等しい）", near(sv[0][0], k) and near(sv[1][0], k))
    o = fr.P((0, 0))
    lb.c(*fr.P((5.95, 2.78)), lab_f)
    lb.put(fr.P((2.18, 0))[0], fr.P((0, 4.28))[1], lab_v, anchor="start")
    lb.put(fr.P((2.22, 0))[0], fr.P((0, -1.72))[1], lab_note, anchor="start")
    lb.put(fr.P((k, 0))[0] - 5, o[1] + 20, str(k), anchor="end")
    lb.put(o[0] - 6, fr.P((0, icpt))[1] - 4, str(icpt), anchor="end")
    allow_check(ck, lb, allow)
    bans = ["y=−2x＋6", "y=(1/3)x＋3", "y=−2", "x=5", "y=2x−3", "y=−2x＋2", "x=3", "(1/2)x−2", "x＋2y−6=0",
            "x=−4", "y=2", "k=5", "a=3", "y=3x＋1", "傾きが無限大"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L04_fig1_line_vs_function_graph.svg", "lesson": "L04", "canvas": cv,
            "title": "y 軸に平行な直線 x=2 は関数のグラフでない直線——一次関数のグラフ y=(1/2)x＋1 と並べる",
            "desc": ("同じ座標平面（1目盛りは縦横とも同じ長さ）に、一次関数のグラフである直線 y=(1/2)x＋1 と、点 (2, 0) を通り y 軸に平行な直線 x=2 を描く。"
                     "x=2 のそばに「関数のグラフでない直線」と書く。どちらの直線も窓の端から端まで描く。目盛りの数字は 2 と 1 だけ。"
                     "同型図は傾き・切片と k を差し替えて生成する"),
            "alt": "同じ座標平面に、一次関数のグラフである直線 y=(1/2)x＋1 と、関数のグラフではない直線 x=2 を並べて描いた図。x=2 には「関数のグラフでない直線」のラベルがある",
            "intent": "直線を「方程式を満たす点の集合」と見ると、関数のグラフにならない直線 x=k も直線の仲間に入ることを、一次関数のグラフと並べて見せる",
            "src": "lesson_04.md §2（x=2 が一次関数のグラフでないことを述べた直後）",
            "params": "直線 y=(1/2)x＋1（並べて描く一次関数の例）と x=2／窓 x −3.2〜7.4・y −2.8〜4.8（1目盛り 46px・縦横共通）／目盛りの数字は 2 と 1 だけ",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"1", "2"}), "allow_texts": allow}


# ===========================================================================
# L05: 垂直条件を直角三角形の回転で見る
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（lesson_05.md §2。傾き m は文字だけで示すので、描く値を固定する） ---
    m = 1.5                                  # 描く値の傾き（図に数値は書かない）
    O, A, Pp = (0.0, 0.0), (1.0, 0.0), (1.0, m)
    A2, Q = rot90(A), rot90(Pp)              # 90° 回した後: A′(0, 1)・Q(−m, 1)
    L1, L2 = (m, -1.0, 0.0), (1.0, m, 0.0)   # y=mx と、OQ を通る直線 x＋my=0
    win, s = ((-2.35, 1.95), (-0.6, 2.4)), 96.0
    left, top = 118.0, 22.0
    labP, labQ, lab90 = "P(1, m)", "Q(−m, 1)", "90°"
    allow = [labP, labQ, lab90, "1", "m", "x", "y", "O"]

    ck = Checker()
    ck.ok("90° 回した後の頂点は A′(0, 1)・Q(−m, 1)（横と縦が入れ替わり、向きが1つ反転する）",
          near_pt(A2, (0.0, 1.0)) and near_pt(Q, (-m, 1.0)))
    ck.ok("OP と OQ は垂直（内積 0）", near(dot(Pp, Q), 0.0))
    ck.ok("回した直角三角形は元と合同（OA=OA′=1・AP=A′Q=m）",
          near(dist(O, A), 1) and near(dist(O, A2), 1) and near(dist(A, Pp), m) and near(dist(A2, Q), m))
    ck.ok("OQ の傾きは 1/(−m) で、傾き m との積は −1（本文の結論。図には書かない）", near(m * (Q[1] / Q[0]), -1.0))
    ck.ok("Q は直線 x＋my=0 の上（OQ を窓の端まで描く直線）", near(line_val(L2, Q), 0.0))
    body_has(ck, 5, ["直線 y=m₁x は、原点 O と点 P(1, m₁) を通る", "横 1、縦 m₁ の直角三角形 OAP（A(1, 0)）を考える",
                     "P の行き先は点 Q(−m₁, 1) である"], "P・A・Q の座標（本文の m₁ を図では m と書く）")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 12)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    pO, pA, pP, pA2, pQ = fr.P(O), fr.P(A), fr.P(Pp), fr.P(A2), fr.P(Q)
    cv.path([pO, pA, pP], w=MAIN_W, close=True, fill=SHADE3, oid="tri")
    cv.path([pO, pA2, pQ], w=MAIN_W, close=True, fill=SHADE, oid="tri")
    draw_axes(cv, lb, fr, ticks=False, origin_ang=208, origin_d=26)
    s1 = draw_line_in_window(cv, fr, L1)
    s2 = draw_line_in_window(cv, fr, L2)
    ck.ok("2本の直線を窓の端から端まで描く", all(on_window_edge(p, win) for p in (*s1, *s2)))
    right_mark(cv, pA, px_dir((-1, 0)), px_dir((0, 1)))
    right_mark(cv, pA2, px_dir((0, -1)), px_dir((-1, 0)))
    right_mark(cv, pO, px_dir(Pp), px_dir(Q))
    for p in (pP, pQ):
        cv.dot(p[0], p[1])
    r = math.hypot(*Pp)
    tP, tQ = math.degrees(math.atan2(Pp[1], Pp[0])), math.degrees(math.atan2(Q[1], Q[0]))
    ck.ok("弧の矢印は P の向きから Q の向きまで 90°", near(tQ - tP, 90.0), f"{tQ - tP:.6f}")
    arc_arrow(cv, fr, O, r, tP + 5, tQ - 5)
    lb.put(pP[0] + 9, pP[1] + 17, labP, anchor="start")
    lb.put(pQ[0] - 9, pQ[1] + 23, labQ, anchor="end")
    lb.c(fr.P((0.5, 0))[0], pO[1] + 16, "1")
    lb.c(pA[0] + 13, fr.P((1, m / 2))[1], "m")
    lb.c(pO[0] + 13, fr.P((0, 0.5))[1], "1")
    lb.c(fr.P((-m / 2, 1))[0], pA2[1] - 14, "m")
    lb.at(pO, (tP + tQ) / 2, (r + 0.24) * s, lab90)
    allow_check(ck, lb, allow)
    bans = ["−1", "−1/m", "m₁m₂", "y=2x＋4", "x＋2y−3=0", "y=−4", "(1, 2)", "y=−2x＋7", "a=2/5", "y=x＋2", "H(0, 2)", "2/3"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L05_fig1_perpendicular_slope_rotation.svg", "lesson": "L05", "canvas": cv,
            "title": "垂直条件を直角三角形の回転で見る——横1・縦 m の直角三角形を原点のまわりに 90° 回すと、横 m・縦 1 になる",
            "desc": ("原点 O を通る傾き m の直線と、横1・縦 m の直角三角形 OAP（P(1, m)）をうすい網かけで描き、それを原点のまわりに左回りに 90° 回した"
                     "直角三角形（頂点 Q(−m, 1)）を濃い網かけで重ねる。直線 OQ も窓の端まで描き、O で OP と OQ が垂直であることを直角の印で示す。"
                     "P から Q へ 90° の弧の矢印。本文の m₁ を図では m と書く。文字だけの図（傾きの値も積の値も書かない）。同型図は描く値 m を差し替えて生成する"),
            "alt": "原点を通り傾き m の直線と、横1・縦 m の直角三角形。この直角三角形を原点のまわりに 90° 回した直角三角形が重ねて描かれ、回した後の頂点 (−m, 1) を通る直線が元の直線と垂直になる様子を示す図",
            "intent": "垂直条件を暗記でなく、横と縦が入れ替わって向きが1つ反転する回転の結果として読めるようにする（積の値は本文が言う）",
            "src": "lesson_05.md §2（Q(−m₁, 1) を求めた直後）",
            "params": "描く値 m=1.5（図に数値は書かない）／O・A(1, 0)・P(1, m) と、90° 回した A′(0, 1)・Q(−m, 1)／1目盛り 96px（縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"1", "90"}), "allow_texts": allow}


# ===========================================================================
# L06: 点と直線の距離（垂線の足）・直線に関して対称な点
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（lesson_06.md §1 例題1） ---
    Pt = (5, 1)
    L = (2, -1, 1)                        # 2x−y＋1=0
    win, s = ((-1.8, 6.6), (-1.6, 5.8)), 48.0
    left, top = 110.0, 18.0
    Hf = foot_on_line(Pt, L)
    labP, labH, labd, labL = pt_label("P", *Pt), "H(1, 3)", "2√5", "2x−y＋1=0"
    allow = [labP, labH, labd, labL, "x", "y", "O"]

    ck = Checker()
    ck.ok("垂線の足 H=(1, 3)（点と直線の式から計算した値と本文の値が一致）", near_pt(Hf, (1, 3)))
    ck.ok("H は直線 2x−y＋1=0 の上", near(line_val(L, Hf), 0))
    ck.ok("PH は直線に垂直（直線の向き (1, 2) との内積 0）", near(dot(sub(Pt, Hf), (1, 2)), 0))
    ck.ok("PH=√20=2√5（距離の公式）", near(dist(Pt, Hf), 2 * math.sqrt(5)))
    ck.ok("公式（2×5−1×1＋1 の絶対値を √(2²＋(−1)²) で割る）=10/√5=2√5 と一致", near(dist_point_line(Pt, L), 2 * math.sqrt(5)))
    body_has(ck, 6, ["点 P(5, 1) と直線 l: 2x−y＋1=0 の距離を求めよ", "よって垂線の足は H(1, 3)", "=√20=**2√5**"],
             "例題1 の点・直線・足・距離")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 16)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr)
    seg = draw_line_in_window(cv, fr, L)
    ck.ok("直線を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
    pP, pH = fr.P(Pt), fr.P(Hf)
    cv.line(pP[0], pP[1], pH[0], pH[1], w=MAIN_W, oid="perp")
    right_mark(cv, pH, px_dir(sub(Pt, Hf)), px_dir((1, 2)))
    for p in (pP, pH):
        cv.dot(p[0], p[1])
    lb.put(pP[0] + 9, pP[1] + 6, labP, anchor="start")
    lb.c(pH[0] + 56, pH[1] - 26, labH)
    nrm = px_dir((1, 2))
    mm = mid(pP, pH)
    lb.c(mm[0] + 22 * nrm[0], mm[1] + 22 * nrm[1], labd)
    lb.put(fr.P((2.35, 0))[0], fr.P((0, 5.2))[1] + 0.29 * FS, labL, anchor="start")
    allow_check(ck, lb, allow)
    bans = ["√17", "15/2", "(0, 5)", "(−1, 1)", "k=4", "−26", "(4, 0)", "(2, 2)", "15√17/17", "6√5/5", "k=3", "d="]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L06_fig1_point_line_distance_foot.svg", "lesson": "L06", "canvas": cv,
            "title": "点と直線の距離——点 P(5, 1) から直線 2x−y＋1=0 に下ろした垂線の足 H(1, 3) と距離 2√5",
            "desc": ("座標平面（1目盛りは縦横とも同じ長さ）に直線 2x−y＋1=0 を窓の端から端まで描き、点 P(5, 1) から下ろした垂線 PH（H(1, 3)）を実線で描く。"
                     "H に直角の印、PH の中ほどに距離 2√5 を書く（例題1の解答で求めた値）。同型図は点と直線の係数を差し替えて生成する（足は式で計算）"),
            "alt": "点 P(5, 1) と直線 2x−y＋1=0、P から直線に下ろした垂線の足 H(1, 3)、直角の印と距離 2√5 のラベルを示す図",
            "intent": "点と直線の距離を「垂線の足までの長さ」として見せ、素朴解法（垂直な直線と交点）と公式が同じ長さを求めていることの足場にする",
            "src": "lesson_06.md §1（例題1の解答の直後）",
            "params": "P(5, 1)・直線 2x−y＋1=0／足 H は P−((2×5−1＋1)/5)(2, −1)=(1, 3)／窓 x −1.8〜6.6・y −1.6〜5.8（1目盛り 48px・縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2", "3", "5"}), "allow_texts": allow}


def fig_L06_2():
    # --- パラメータ（lesson_06.md §4 例題4） ---
    A = (3, 2)
    L = (1, 1, -1)                         # x＋y−1=0
    win, s = ((-2.6, 4.8), (-3.2, 3.8)), 48.0
    left, top = 120.0, 18.0
    B = reflect_on_line(A, L)
    M = mid(A, B)
    labA, labB, labM, labL = pt_label("A", *A), "B(−1, −2)", "(1, 0)", "x＋y−1=0"
    allow = [labA, labB, labM, labL, "x", "y", "O"]

    ck = Checker()
    ck.ok("直線に関して A と対称な点は B(−1, −2)（式で計算した値と本文の値が一致）", near_pt(B, (-1, -2)))
    ck.ok("(i) 線分 AB の中点 (1, 0) は直線の上（1＋0−1=0）", near_pt(M, (1, 0)) and near(line_val(L, M), 0))
    ck.ok("(ii) AB の傾き 1 と直線の傾き −1 の積は −1（垂直）", near(dot(sub(B, A), (1, -1)), 0))
    ck.ok("AM=MB（(1, 0) は線分 AB の中点）", near(dist(A, M), dist(M, B)))
    body_has(ck, 6, ["点 A(3, 2) と直線 l: x＋y−1=0 に関して対称な点 B の座標を求めよ", "よって **B(−1, −2)** である",
                     "中点は ((3−1)/2, (2−2)/2)=(1, 0) で、1＋0−1=0 を満たす"], "例題4 の点・直線・答え・中点")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 16)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr)
    seg = draw_line_in_window(cv, fr, L)
    ck.ok("直線を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
    pA, pB, pM = fr.P(A), fr.P(B), fr.P(M)
    cv.line(pA[0], pA[1], pB[0], pB[1], w=AUX_W, dash=DASH, oid="seg")
    right_mark(cv, pM, px_dir(sub(A, M)), px_dir((-1, 1)))
    for p in (pA, pB, pM):
        cv.dot(p[0], p[1])
    lb.put(pA[0] + 9, pA[1] + 6, labA, anchor="start")
    lb.put(pB[0] - 9, pB[1] + 6, labB, anchor="end")
    lb.c(pM[0], pM[1] + 40, labM)
    lb.put(fr.P((3.9, 0))[0], fr.P((0, -2.6))[1] + 0.29 * FS, labL, anchor="start")
    allow_check(ck, lb, allow)
    bans = ["(0, 5)", "(−1, 1)", "p＋q＋3=0", "q=p−1", "(2, 3)", "(1, 2)", "15√17/17", "15/2"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L06_fig2_reflection_across_line.svg", "lesson": "L06", "canvas": cv,
            "title": "直線に関して対称な点——A(3, 2) と直線 x＋y−1=0 に関して対称な点 B(−1, −2)・中点 (1, 0) は直線の上",
            "desc": ("座標平面（1目盛りは縦横とも同じ長さ）に直線 x＋y−1=0 を窓の端から端まで描き、A(3, 2) と対称な点 B(−1, −2) を結ぶ線分を破線で描く。"
                     "中点 (1, 0) に直角の印。同型図は点と直線の係数を差し替えて生成する（対称な点は式で計算）"),
            "alt": "点 A(3, 2) と直線 x＋y−1=0 と、直線に関して A と対称な点 B(−1, −2)。線分 AB の中点 (1, 0) が直線上にあり、AB と直線が直角で交わる印を示す図",
            "intent": "対称な点の2条件（中点が直線上・結ぶ線分が直線に垂直）を、中1の「対称の軸は垂直二等分線」と同じ形で見せる",
            "src": "lesson_06.md §4（例題4の解答の直後）",
            "params": "A(3, 2)・直線 x＋y−1=0／B は A−2((3＋2−1)/2)(1, 1)=(−1, −2)／窓 x −2.6〜4.8・y −3.2〜3.8（1目盛り 48px・縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2", "3"}), "allow_texts": allow}


# ===========================================================================
# L07: 円の方程式（中心と半径）
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（lesson_07.md §1。文字だけの図なので、中心・半径・P の位置は描く値） ---
    C, r, ang = (3.2, 2.3), 1.9, 35.0
    Pp = (C[0] + r * math.cos(math.radians(ang)), C[1] + r * math.sin(math.radians(ang)))
    win, s = ((-0.6, 6.4), (-0.6, 5.0)), 56.0
    left, top = 110.0, 18.0
    labC, labP, labr = "C(a, b)", "P(x, y)", "r"
    allow = [labC, labP, labr, "x", "y", "O"]

    ck = Checker()
    ck.ok("CP=r（P は円周上）", near(dist(C, Pp), r))
    ck.ok("P の座標が (x−a)²＋(y−b)²=r² を満たす（描く値で）", near((Pp[0] - C[0]) ** 2 + (Pp[1] - C[1]) ** 2, r * r))
    (x0, x1), (y0, y1) = win
    ck.ok("円は窓の内側（第1象限）に収まる", x0 < 0 < C[0] - r and C[0] + r < x1 and 0 < C[1] - r and C[1] + r < y1)
    body_has(ck, 7, ["点 C(a, b) を中心とし、半径が r（r>0）の円を考える",
                     "点 P(x, y) がこの円の周上にあるとは、**P と C の距離が r に等しい**ということである"], "中心・半径・周上の点")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 16)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr, ticks=False)
    draw_circle(cv, fr, C, r)
    pC, pP = fr.P(C), fr.P(Pp)
    cv.line(pC[0], pC[1], pP[0], pP[1], w=MAIN_W, oid="radius")
    for p in (pC, pP):
        cv.dot(p[0], p[1])
    lb.c(pC[0], pC[1] + 26, labC)
    lb.put(pP[0] + 9, pP[1] - 6, labP, anchor="start")
    nrm = px_dir(rot90((math.cos(math.radians(ang)), math.sin(math.radians(ang)))))
    mm = mid(pC, pP)
    lb.c(mm[0] + 15 * nrm[0], mm[1] + 15 * nrm[1], labr)
    allow_check(ck, lb, allow)
    bans = ["(x−3)²＋(y＋2)²=16", "x²＋y²=7", "(x＋1)²＋(y−4)²=25", "(x−1)²＋(y−4)²=25", "(4, −3)", "(−2, 1)",
            "(0, 3)", "k<5", "√5", "(2, 2)", "(x−2)²＋(y＋1)²=9"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L07_fig1_circle_center_radius.svg", "lesson": "L07", "canvas": cv,
            "title": "円の方程式——中心 C(a, b)・半径 r の円と周上の点 P(x, y)（CP=r）",
            "desc": ("座標平面に中心 C(a, b)、半径 r の円を描き、周上の点 P(x, y) と中心を結ぶ線分 CP に r のラベルを付ける。"
                     "文字だけの図（数値なし）。1目盛りは縦横とも同じ長さ。同型図は中心・半径・P の位置（描く値）を差し替えて生成する"),
            "alt": "中心 C(a, b)、半径 r の円と、その周上の点 P(x, y)。C と P を結ぶ線分の長さが r であることを示す",
            "intent": "円を「定点 C からの距離が r の点の集合」と見て、距離の公式から (x−a)²＋(y−b)²=r² を導く出発点にする",
            "src": "lesson_07.md §1（円の方程式を導いた直後）",
            "params": "描く値 中心 (3.2, 2.3)・半径 1.9・P は中心から 35° の向き（図に数値は書かない）／1目盛り 56px（縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("none", set()), "allow_texts": allow}


# ===========================================================================
# L08: 円と直線の位置関係の3つの場合
# ===========================================================================
def fig_L08_1():
    # --- パラメータ（lesson_08.md §3。d と r は文字だけで示すので、長さは描く値） ---
    r = 56.0
    ds = [0.5 * r, r, 1.4 * r]
    heads = ["d<r", "d=r", "d>r"]
    caps = ["共有点 2個", "共有点 1個", "共有点 0個"]
    PW, gap, x_first, cy, H = 200.0, 10.0, 15.0, 104.0, 236
    rad_ang = 140.0                          # 半径を引く向き（画面の角）
    allow = heads + caps + ["d", "r", "O"]

    ck = Checker()
    counts = [2 if d < r else (1 if near(d, r) else 0) for d in ds]
    ck.ok("共有点の個数は r²−d² の符号で 2・1・0（正・0・負）", counts == [2, 1, 0])
    ck.ok("パネルの見出しの大小関係が d と r の値と一致",
          [("<" if d < r and not near(d, r) else ("=" if near(d, r) else ">")) for d in ds] == [h[1] for h in heads])
    ck.ok("下の文の個数が共有点の個数と一致", [int(re.search(r"([0-9])個", c).group(1)) for c in caps] == counts)
    body_has(ck, 8, ["d が半径 r より小さければ直線は円の内側を通るので共有点は2個、d=r なら直線は円にちょうど触れて共有点は1個、d>r なら離れていて0個である"],
             "d と r の大小と共有点の個数")

    cv = Canvas(W, H)
    lb = Labels(cv)
    n_dots = []
    for i, (d, head, cap) in enumerate(zip(ds, heads, caps)):
        x_off = x_first + i * (PW + gap)
        cx = x_off + PW / 2
        cv.path(circle_pts((cx, cy), r), w=MAIN_W, close=True, oid="circle")
        ly = cy + d
        cv.line(x_off + 8, ly, x_off + PW - 8, ly, w=MAIN_W, oid="line")
        cv.line(cx, cy, cx, ly, w=AUX_W, dash=DASH, oid="perp")
        right_mark(cv, (cx, ly), (0.0, -1.0), (-1.0, 0.0))
        cv.dot(cx, cy)
        a = math.radians(rad_ang)
        re_ = (cx + r * math.cos(a), cy - r * math.sin(a))
        cv.line(cx, cy, re_[0], re_[1], w=MAIN_W, oid="radius")
        pts = []
        if r * r - d * d > 1e-9:
            h = math.sqrt(r * r - d * d)
            pts = [(cx - h, ly), (cx + h, ly)]
        elif near(r * r - d * d, 0.0):
            pts = [(cx, ly)]
        for p in pts:
            ck.ok(f"{head}: 共有点は円の上と直線の上の両方にある", near(dist(p, (cx, cy)), r) and near(p[1], ly))
            cv.dot(p[0], p[1])
        n_dots.append(len(pts))
        ck.ok(f"{head}: 垂線の足は中心から直線へ最も近い点（中心と直線の距離＝d）", near(ly - cy, d))
        lb.c(cx, 24, head, weight="bold")
        lb.c(cx + 12, cy - 10, "O")
        lb.c(cx + 12, cy + d / 2, "d")
        nr = (math.sin(a), math.cos(a))
        lb.c((cx + re_[0]) / 2 + 15 * nr[0], (cy + re_[1]) / 2 + 15 * nr[1], "r")
        lb.c(cx, H - 22, cap)
    ck.ok("●で打った共有点の数が 2・1・0", n_dots == counts)
    allow_check(ck, lb, allow)
    bans = ["k=±5", "3√2", "2√7", "r=2", "r≧2", "±2√2", "√7", "√5", "8"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L08_fig1_circle_line_three_cases.svg", "lesson": "L08", "canvas": cv,
            "title": "円と直線の位置関係の3つの場合——中心と直線の距離 d と半径 r を比べる（d<r・d=r・d>r）",
            "desc": ("3つのパネルに同じ半径 r の円と直線を描き、中心 O から直線へ下ろした垂線（破線・長さ d）と、別の向きの半径（長さ r）を示す。"
                     "左は d<r で2点で交わる（共有点 2個）、中は d=r で1点で接する（共有点 1個）、右は d>r で共有点がない（共有点 0個）。"
                     "共有点には●。文字だけの図（d と r の値は書かない）。同型図は d の値を差し替えて生成する"),
            "alt": "円と直線の位置関係の3つの場合。左から、中心と直線の距離 d が半径 r より小さく2点で交わる場合、d=r で1点で接する場合、d>r で共有点がない場合。各パネルに中心から直線へ下ろした垂線の長さ d と半径 r を示す",
            "intent": "共有点の個数を、方程式の実数解の個数（判別式）とは別に、中心と直線の距離 d と半径 r の大小（方法②）で読めるようにする",
            "src": "lesson_08.md §3（方法②の説明の直後）",
            "params": "描く値 半径 56px・d は 28px・56px・78.4px（0.5r・r・1.4r）／直線は水平・中心は各パネルの中央（高さ 104px）／半径は 140° の向きに引く",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2"}), "allow_texts": allow}


# ===========================================================================
# L09: 円の接線は半径に垂直
# ===========================================================================
def fig_L09_1():
    # --- パラメータ（lesson_09.md §2 例題1） ---
    r2 = 25
    Pt = (3, -4)
    T = (Pt[0], Pt[1], -r2)                  # x₁x＋y₁y=r² → 3x−4y−25=0
    win, s = ((-6.6, 9.3), (-7.6, 6.4)), 28.0
    left, top = 70.0, 18.0
    labP, labT, labC = pt_label("P", *Pt), "3x−4y=25", "x²＋y²=25"
    allow = [labP, labT, labC, "x", "y", "O"]

    ck = Checker()
    r = math.sqrt(r2)
    ck.ok("P(3, −4) は円 x²＋y²=25 の上（9＋16=25）", Pt[0] ** 2 + Pt[1] ** 2 == r2)
    ck.ok("接線 3x−4y=25 は P を通る（9＋16=25）", line_val(T, Pt) == 0)
    ck.ok("半径 OP と接線は垂直（OP と接線の向き (4, 3) の内積 0）", dot(Pt, (4, 3)) == 0)
    ck.ok("原点と接線の距離（−25 の絶対値を √(9＋16) で割る）=5 は半径に等しい", near(dist_point_line((0, 0), T), r))
    ck.ok("OP の傾き −4/3 と接線の傾き 3/4 の積は −1", Fr(Pt[1], Pt[0]) * Fr(3, 4) == -1)
    body_has(ck, 9, ["円 x²＋y²=25 上の点 P(3, −4) における接線の方程式を求めよ", "3x−4y=25"], "例題1 の円・接点・接線")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 16)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr)
    draw_circle(cv, fr, (0, 0), r)
    seg = draw_line_in_window(cv, fr, T)
    ck.ok("接線を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
    pO, pP = fr.P((0, 0)), fr.P(Pt)
    cv.line(pO[0], pO[1], pP[0], pP[1], w=MAIN_W, oid="radius")
    right_mark(cv, pP, px_dir((-Pt[0], -Pt[1])), px_dir((4, 3)))
    for p in (pO, pP):
        cv.dot(p[0], p[1])
    out = px_dir(Pt)
    lb.c(pP[0] + 40 * out[0], pP[1] + 40 * out[1], labP)
    lb.c(*fr.P((-4.4, 4.95)), labC)
    lb.c(*fr.P((7.6, -2.55)), labT)
    allow_check(ck, lb, allow)
    bans = ["2x−3y=13", "y=−4", "x=−3", "(1, −2)", "3x＋y=10", "−x＋3y=10", "(3, 1)", "(−1, 3)", "4x＋3y−15=0", "x=3",
            "(3, 4)", "(5, 0)", "2x＋y−10=0", "4x−3y−10=0", "x＋2y=5", "2x−y=5"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L09_fig1_tangent_perpendicular_radius.svg", "lesson": "L09", "canvas": cv,
            "title": "円の接線は接点を通る半径に垂直——円 x²＋y²=25 上の点 P(3, −4) における接線 3x−4y=25",
            "desc": ("座標平面（1目盛りは縦横とも同じ長さ）に円 x²＋y²=25 と、周上の点 P(3, −4) における接線 3x−4y=25 を窓の端から端まで描く。"
                     "中心 O と P を結ぶ半径と接線が垂直であることを P の直角の印で示す。同型図は半径と接点を差し替えて生成する（接線は x₁x＋y₁y=r² で計算）"),
            "alt": "円 x²＋y²=25 と、その周上の点 P(3, −4) における接線 3x−4y=25。中心 O と P を結ぶ半径に、接線が垂直であることを直角の印で示す",
            "intent": "接線の方程式を「接点を通る半径に垂直」という中学の円の性質から導く出発点にし、公式 x₁x＋y₁y=r² の理由を図で押さえる",
            "src": "lesson_09.md §2（例題1の解答の直後）",
            "params": "円 x²＋y²=25（半径 5）・接点 P(3, −4)・接線 3x−4y=25／窓 x −6.6〜9.3・y −7.6〜6.4（1目盛り 28px・縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"3", "4", "25"}), "allow_texts": allow}


# ===========================================================================
# L10: 軌跡（2点から等距離の点・距離の比が一定の点）
# ===========================================================================
def fig_L10_1():
    # --- パラメータ（lesson_10.md §2 例題1） ---
    A, B = (1, 2), (5, 4)
    L = (2, 1, -9)                           # 2x＋y−9=0
    ts = [-1.0, -0.5, 0.0, 0.5, 1.0]         # 中点から直線に沿って打つ点（x の差）
    Pn = (2, 5)                              # PA=PB を破線で示す点
    win, s = ((-1.0, 7.2), (-0.9, 6.4)), 50.0
    left, top = 100.0, 18.0
    M = mid(A, B)
    dots = [(M[0] + t, M[1] - 2 * t) for t in ts]
    labA, labB, labM, labL = pt_label("A", *A), pt_label("B", *B), "(3, 3)", "2x＋y−9=0"
    allow = [labA, labB, labM, labL, "P", "x", "y", "O"]

    ck = Checker()
    ck.ok("打った5点はどれも A と B から等しい距離（AP²=BP²）",
          all(near(dist(p, A) ** 2, dist(p, B) ** 2) for p in dots))
    ck.ok("打った5点はどれも直線 2x＋y−9=0 の上", all(near(line_val(L, p), 0) for p in dots))
    grid = [(x, y) for x in (-2, 0, 3, 7) for y in (-1, 2, 5)]
    ck.ok("AP²−BP² を整理すると 4(2x＋y−9)（本文の 8x＋4y−36=0 と同じ式・12点で確かめる）",
          all(near(dist(p, A) ** 2 - dist(p, B) ** 2, 4 * line_val(L, p)) for p in grid))
    ck.ok("中点 (3, 3) は直線の上で、AB（傾き 1/2）と直線（傾き −2）は垂直＝垂直二等分線",
          M == (3.0, 3.0) and near(line_val(L, M), 0) and near(dot(sub(B, A), (1, -2)), 0))
    ck.ok("P(2, 5) は5点のうちの1つで、PA=PB=√10", Pn in dots and near(dist(Pn, A), math.sqrt(10)) and near(dist(Pn, B), math.sqrt(10)))
    body_has(ck, 10, ["2点 A(1, 2)、B(5, 4) から等しい距離にある点 P の軌跡を求めよ", "よって、求める軌跡は**直線 2x＋y−9=0** である",
                      "線分 AB の中点 (3, 3) はこの直線上にある"], "例題1 の2点・軌跡・中点")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 16)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    draw_axes(cv, lb, fr)
    seg = draw_line_in_window(cv, fr, L)
    ck.ok("直線を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
    pA, pB, pM, pP = fr.P(A), fr.P(B), fr.P(M), fr.P(Pn)
    cv.line(pA[0], pA[1], pB[0], pB[1], w=MAIN_W, oid="seg")
    cv.line(pP[0], pP[1], pA[0], pA[1], w=AUX_W, dash=DASH, oid="guide")
    cv.line(pP[0], pP[1], pB[0], pB[1], w=AUX_W, dash=DASH, oid="guide")
    equal_ticks(cv, pP, pA)
    equal_ticks(cv, pP, pB)
    equal_ticks(cv, pA, pM, n=2)
    equal_ticks(cv, pM, pB, n=2)
    right_mark(cv, pM, px_dir(sub(B, A)), px_dir((-1, 2)))
    for p in [pA, pB] + [fr.P(q) for q in dots]:
        cv.dot(p[0], p[1])
    lb.c(pA[0], pA[1] + 25, labA)
    lb.put(pB[0] + 9, pB[1] + 6, labB, anchor="start")
    lb.at(pP, 49, 17, "P")
    lb.at(pM, -15, 42, labM)
    lb.put(fr.P((1.78, 0))[0], fr.P((0, 6.0))[1] + 0.29 * FS, labL, anchor="start")
    allow_check(ck, lb, allow)
    bans = ["3x＋y−5=0", "(x＋2)²＋y²=16", "x=3", "x²＋y²=4", "(x−2)²＋(y−1)²=9/4", "3/2", "x−3y=0", "3x＋y=0",
            "√10", "(0, 5)", "(0, 2)", "(0, −2)"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L10_fig1_equidistant_perpendicular_bisector.svg", "lesson": "L10", "canvas": cv,
            "title": "2点から等しい距離にある点の軌跡——A(1, 2)、B(5, 4) から等距離の点は直線 2x＋y−9=0（線分 AB の垂直二等分線）の上に並ぶ",
            "desc": ("座標平面（1目盛りは縦横とも同じ長さ）に A(1, 2)、B(5, 4) と線分 AB を描き、A と B から等しい距離にある点を5つ●で打つ。"
                     "5点は直線 2x＋y−9=0 の上に並ぶ。そのうちの1点 P から A と B へ破線を引き、長さが等しい印を付ける。"
                     "中点 (3, 3) で AB と直線が直角に交わる印と、中点の両側が等しい印。中1の作図の弧は描かない。同型図は A と B を差し替えて生成する"),
            "alt": "2点 A(1, 2)、B(5, 4) から等しい距離にある点をいくつか打つと、それらが直線 2x＋y−9=0 の上に並ぶ。この直線は線分 AB の垂直二等分線である",
            "intent": "軌跡を「条件を満たす点の集合」として、条件を満たす点をいくつか打つと1本の直線に並ぶことを見せ、4段の型で得た 2x＋y−9=0 が中1の垂直二等分線と同じ図形であることを確かめる",
            "src": "lesson_10.md §2（例題1の検算の直後）",
            "params": "A(1, 2)・B(5, 4)／等距離の点 (2, 5)・(2.5, 4)・(3, 3)・(3.5, 2)・(4, 1)（中点から直線に沿って打つ）／P(2, 5)／窓 x −1.0〜7.2・y −0.9〜6.4（1目盛り 50px・縦横共通）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2", "3", "4", "5", "9"}), "allow_texts": allow}


def fig_L10_2():
    # --- パラメータ（lesson_10.md §3 例題2 と、比を 1:2 に変えた例） ---
    A, B = (-2, 0), (1, 0)
    cases = [((2, 1), (2, -2)), ((1, 2), (-3, -2))]      # (比 AP:BP、円の上の例の点 P)
    wins = [((-3.2, 4.4), (-2.7, 2.7)), ((-5.6, 2.1), (-2.7, 2.7))]
    s = 38.0
    lefts, top = [10.0, 322.0], 40.0
    labA, labB = pt_label("A", *A), pt_label("B", *B)
    heads = [f"AP:BP={m}:{n}" for (m, n), _ in cases]

    ck = Checker()
    circles = []
    for (m, n), P0 in cases:
        k2 = Fr(m * m, n * n)
        cx = (k2 * B[0] - A[0]) / (k2 - 1)
        rad = Fr(m, n) * abs(B[0] - A[0]) / abs(k2 - 1)
        circles.append((cx, rad))
        grid = [(Fr(x), Fr(y)) for x in (-5, -1, 0, 2, 4) for y in (-3, 0, 1, 3)]
        ck.ok(f"AP²−{fmt(k2)}BP² は (1−{fmt(k2)})((x−{fmt(cx)})²＋y²−{fmt(rad * rad)}) に等しい（中心 ({fmt(cx)}, 0)・半径 {fmt(rad)} の円・20点で厳密に確かめる）",
              all((p[0] - A[0]) ** 2 + p[1] ** 2 - k2 * ((p[0] - B[0]) ** 2 + p[1] ** 2)
                  == (1 - k2) * ((p[0] - cx) ** 2 + p[1] ** 2 - rad * rad) for p in grid))
        ok_all = True
        for i in range(72):
            t = 2 * math.pi * i / 72
            q = (float(cx) + float(rad) * math.cos(t), float(rad) * math.sin(t))
            ok_all = ok_all and near(dist(q, A) * n, dist(q, B) * m, 1e-9)
        ck.ok(f"AP:BP={m}:{n}: 円の上の72点すべてで AP:BP={m}:{n}", ok_all)
        ck.ok(f"AP:BP={m}:{n}: 例の点 P({fmt(P0[0])}, {fmt(P0[1])}) は円の上で AP:BP={m}:{n}",
              near((P0[0] - cx) ** 2 + P0[1] ** 2, rad ** 2) and near(dist(P0, A) * n, dist(P0, B) * m))
        near_pt_name = "B" if m > n else "A"
        inside = lambda q: (q[0] - cx) ** 2 + q[1] ** 2 < rad ** 2
        ck.ok(f"AP:BP={m}:{n}: 近い方の点 {near_pt_name} は円の内側、もう一方は外側",
              (inside(B) and not inside(A)) if m > n else (inside(A) and not inside(B)))
    ck.ok("本文の値と一致: 左は中心 (2, 0)・半径 2、右は中心 (−3, 0)・半径 2", circles == [(2, 2), (-3, 2)])
    caps = [f"中心 ({fmt(c)}, 0)、半径 {fmt(r)}" for c, r in circles]
    allow = heads + caps + [labA, labB, "P", "x", "y", "O"]
    body_has(ck, 10, ["2点 A(−2, 0)、B(1, 0) からの距離の比が AP:BP=2:1 である点 P の軌跡を求めよ",
                      "よって、求める軌跡は**中心 (2, 0)、半径 2 の円**である", "つまり中心 (−3, 0)、半径 2 の円になる"],
             "例題2 の2点・比・軌跡と、比を 1:2 に変えた円")

    frs = [Frame(lefts[i], top, wins[i], s) for i in range(2)]
    H = round(top + (wins[0][1][1] - wins[0][1][0]) * s + 44)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, *frs)
    for i, (fr, win, ((m, n), P0), (cx, rad)) in enumerate(zip(frs, wins, cases, circles)):
        draw_axes(cv, lb, fr, origin_ang=135)
        draw_circle(cv, fr, (float(cx), 0.0), float(rad))
        pA, pB, pP = fr.P(A), fr.P(B), fr.P(P0)
        cv.line(pP[0], pP[1], pA[0], pA[1], w=AUX_W, dash=DASH, oid="guide")
        cv.line(pP[0], pP[1], pB[0], pB[1], w=AUX_W, dash=DASH, oid="guide")
        for p in (pA, pB, pP):
            cv.dot(p[0], p[1])
        if m > n:
            lb.c(pA[0], pA[1] - 20, labA)
            lb.put(pB[0] + 4, pB[1] - 12, labB, anchor="start")
        else:
            lb.put(pA[0] - 4, pA[1] - 12, labA, anchor="end")
            lb.c(pB[0], pB[1] - 20, labB)
        lb.c(pP[0], pP[1] + 17, "P")
        cxp = (fr.P((win[0][0], 0))[0] + fr.P((win[0][1], 0))[0]) / 2
        lb.c(cxp, 22, heads[i], weight="bold")
        lb.c(cxp, H - 22, caps[i])
    allow_check(ck, lb, allow)
    bans = ["半径 4", "中心 (−2, 0)", "(x＋2)²＋y²=16", "x=3", "3/2", "(2, 1)", "9/4", "アポロ" + "ニウス", "(x−2)²＋(y−1)²",
            "x−3y=0", "3x＋y=0"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L10_fig2_distance_ratio_locus_circle.svg", "lesson": "L10", "canvas": cv,
            "title": "距離の比が一定（比は正で 1:1 でない）の点の軌跡は円——A(−2, 0)、B(1, 0) で AP:BP=2:1 なら中心 (2, 0)・半径 2、1:2 なら中心 (−3, 0)・半径 2",
            "desc": ("2つのパネルに同じ2点 A(−2, 0)、B(1, 0) をとり、左に AP:BP=2:1 の点の軌跡（中心 (2, 0)、半径 2 の円）、右に AP:BP=1:2 の点の軌跡"
                     "（中心 (−3, 0)、半径 2 の円）を描く。各円の上の1点 P から A と B へ破線を引き、比の条件を満たす点の例を示す。円は近い方の点の側にできる。"
                     "1目盛りは縦横とも同じ長さで、2つのパネルは同じ縮尺。同型図は比を差し替えて生成する（中心と半径は式で計算）"),
            "alt": "2点 A(−2, 0)、B(1, 0) からの距離の比が一定の点の軌跡を2つ並べた図。左は AP:BP=2:1 で中心 (2, 0)、半径 2 の円、右は AP:BP=1:2 で中心 (−3, 0)、半径 2 の円。近い方の点の側に円ができる",
            "intent": "条件（比）を変えると軌跡がどう動くかを2つ並べて見せ、コンピュータで点を動かして観察する活動の代わりにする（比を 1:1 や 3:1 に変えたらどうなるかは本文の自問）",
            "src": "lesson_10.md §3（比を 1:2 に変えた円を述べた直後）",
            "params": "A(−2, 0)・B(1, 0)／左 AP:BP=2:1 → 中心 (2, 0)・半径 2・例の点 P(2, −2)／右 AP:BP=1:2 → 中心 (−3, 0)・半径 2・例の点 P(−3, −2)／1目盛り 38px（縦横共通・2パネル同じ）",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2", "3"}), "allow_texts": allow}


# ===========================================================================
# L11: 不等式の表す領域（直線を境界線とする・円を境界線とする）
# ===========================================================================
def fig_L11_1():
    # --- パラメータ（lesson_11.md §2 例題1・例題2） ---
    panels = [
        {"head": "y>2x−1", "L": (-2, 1, 1), "strict": True, "bound": "y=2x−1", "cap": "境界線を含まない",
         "pred": lambda p: p[1] > 2 * p[0] - 1, "win": ((-2.8, 3.4), (-2.6, 3.4)), "blab": (2.95, 2.56)},
        {"head": "3x＋2y−6≦0", "L": (-3, -2, 6), "strict": False, "bound": "3x＋2y−6=0", "cap": "境界線を含む",
         "pred": lambda p: 3 * p[0] + 2 * p[1] - 6 <= 0, "win": ((-1.8, 4.3), (-1.8, 4.2)), "blab": (2.6, 2.9)},
    ]
    s, lefts, top = 44.0, [10.0, 325.0], 40.0
    allow = [q["head"] for q in panels] + [q["bound"] for q in panels] + [q["cap"] for q in panels] + ["x", "y", "O"]

    ck = Checker()
    ck.ok("左: 原点を代入すると 0>2×0−1 すなわち 0>−1 で成り立つ", panels[0]["pred"]((0, 0)))
    ck.ok("右: 原点を代入すると −6≦0 で成り立つ", panels[1]["pred"]((0, 0)))
    body_has(ck, 11, ["不等式 y>2x−1 の表す領域を図示せよ",
                      "不等号が > なので境界線上の点は領域に含まれない。含まれないことを表すために、境界線は破線で描く",
                      "原点 (0, 0) を入れると 0>2×0−1、すなわち 0>−1 で成り立つ",
                      "不等式 3x＋2y−6≦0 の表す領域を図示せよ", "含まれることを表すために実線で描く",
                      "原点 (0, 0) を代入すると −6≦0 で成り立つ"], "例題1・例題2 の不等式・線種・代入した点")

    frs = [Frame(lefts[i], top, panels[i]["win"], s) for i in range(2)]
    H = round(top + 6.0 * s + 46)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, *frs)
    hatch = cv.pattern("hatchA", 45)
    for q, fr in zip(panels, frs):
        win, L = q["win"], q["L"]
        ck.ok(f"{q['head']}: 窓の高さは 6 目盛り（2つのパネルの上下をそろえる）", near(win[1][1] - win[1][0], 6.0))
        poly = clip_halfplane(rect_pts(win), L)
        cv.fill_region([fr.Ps(poly)], hatch)
        region_check(ck, f"{q['head']} を満たす点の集合", [poly], q["pred"],
                     lambda p, L=L: dist_point_line(p, L), win)
        ck.ok(f"{q['head']}: 代入した原点は斜線の部分の中", in_region((0.0, 0.0), [poly]))
        dash = DASH if q["strict"] else None
        boundary_style_check(ck, q["head"], q["strict"], dash)
        seg = draw_line_in_window(cv, fr, L, w=MAIN_W, dash=dash, oid="boundary")
        ck.ok(f"{q['head']}: 境界線を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
        draw_axes(cv, lb, fr, origin_d=21, plate=True)
        o = fr.P((0, 0))
        cv.dot(o[0], o[1], r=DOT_R_END)
        lb.c(*fr.P(q["blab"]), q["bound"])
        cxp = (fr.P((win[0][0], 0))[0] + fr.P((win[0][1], 0))[0]) / 2
        lb.c(cxp, 22, q["head"], weight="bold")
        lb.c(cxp, H - 20, q["cap"])
    allow_check(ck, lb, allow)
    bans = ["(x−2)²＋(y＋1)²<5", "x−y＋2≧0", "(x−3)²＋(y＋1)²>16", "y>3", "x²＋y²≦4", "y≧−2x＋3", "3x−2y<6", "x≦2",
            "y>−1", "x−y>1", "下側"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L11_fig1_half_plane_solid_dashed.svg", "lesson": "L11", "canvas": cv,
            "title": "直線を境界線とする領域——y>2x−1 は破線の上側、3x＋2y−6≦0 は実線の原点側（どちらも原点を代入して側を決める）",
            "desc": ("2つのパネルに、左は不等式 y>2x−1 の表す領域（境界線 y=2x−1 を破線で描き、原点を含む上側に斜線）、右は不等式 3x＋2y−6≦0 の表す領域"
                     "（境界線 3x＋2y−6=0 を実線で描き、原点を含む側に斜線）を描く。代入した原点に●。下に境界線を含むかどうかを書く。"
                     "斜線は角度と間隔を固定し、境界線を含むかどうかは線種で表す（色に頼らない）。1目盛りは縦横とも同じ長さ。"
                     "同型図は不等式の係数と不等号を差し替えて生成する"),
            "alt": "直線を境界線とする領域の2つの例。左は y>2x−1 の表す領域で、境界線を破線で描き、代入した原点に印をつけて、原点を含む上側に斜線を引く。右は 3x＋2y−6≦0 の表す領域で、境界線を実線で描き、原点を含む側に斜線を引く",
            "intent": "領域の図示の3段（境界線を描く→点を1つ代入→成り立つ側を塗る）と、境界線を含むかどうかの書き分け（不等号・線種・答えの文）を1枚で見せる",
            "src": "lesson_11.md §2（例題2の答えの直後）",
            "params": "左 y>2x−1（破線・窓 x −2.8〜3.4・y −2.6〜3.4）／右 3x＋2y−6≦0（実線・窓 x −1.8〜4.3・y −1.8〜4.2）／1目盛り 44px（縦横共通）／斜線 45°・間隔 8px",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "1", "2", "3", "6"}), "allow_texts": allow}


def fig_L11_2():
    # --- パラメータ（lesson_11.md §3 例題5） ---
    panels = [
        {"head": "(x−1)²＋(y−2)²<9", "c": (1, 2), "r": 3, "strict": True, "inside": True, "cap": "境界線を含まない",
         "pred": lambda p: (p[0] - 1) ** 2 + (p[1] - 2) ** 2 < 9,
         "win": ((-2.7, 4.8), (-1.6, 5.6)), "o_ang": 135},
        {"head": "x²＋y²≧4", "c": (0, 0), "r": 2, "strict": False, "inside": False, "cap": "境界線を含む",
         "pred": lambda p: p[0] ** 2 + p[1] ** 2 >= 4,
         "win": ((-3.6, 3.8), (-3.4, 3.8)), "o_ang": 225},
    ]
    s, lefts, top = 36.0, [12.0, 330.0], 40.0
    lab_c = pt_label("", 1, 2)
    allow = [q["head"] for q in panels] + [q["cap"] for q in panels] + [lab_c, "x", "y", "O"]

    ck = Checker()
    ck.ok("左: 中心 (1, 2) を代入すると 0<9 で成り立つので内部", panels[0]["pred"](panels[0]["c"]))
    ck.ok("右: 中心 (0, 0) を代入すると 0≧4 は成り立たないので外部", not panels[1]["pred"](panels[1]["c"]))
    body_has(ck, 11, ["(x−1)²＋(y−2)²<9", "x²＋y²≧4", "（中心 (1, 2)、半径 3）で、不等号が < なので破線",
                      "中心 (0, 0) を代入すると 0≧4 で成り立たないから、中心を含まない側、つまり**円の外部**が領域である"],
             "例題5 の不等式・中心と半径・内部と外部")

    frs = [Frame(lefts[i], top, panels[i]["win"], s) for i in range(2)]
    H = round(top + 7.2 * s + 46)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, *frs)
    hatch = cv.pattern("hatchA", 45)
    for q, fr in zip(panels, frs):
        win, c, r = q["win"], q["c"], q["r"]
        ck.ok(f"{q['head']}: 窓の高さは 7.2 目盛り（2つのパネルの上下をそろえる）", near(win[1][1] - win[1][0], 7.2))
        disk = circle_pts(c, r)
        polys = [disk] if q["inside"] else [rect_pts(win), disk]
        (x0, x1), (y0, y1) = win
        ck.ok(f"{q['head']}: 円は窓の内側に収まる", x0 < c[0] - r and c[0] + r < x1 and y0 < c[1] - r and c[1] + r < y1)
        cv.fill_region([fr.Ps(pl) for pl in polys], hatch)
        region_check(ck, f"{q['head']} を満たす点の集合（窓の中）", polys, q["pred"],
                     lambda p, c=c, r=r: abs(dist(p, c) - r), win, step=0.2)
        dash = DASH if q["strict"] else None
        boundary_style_check(ck, q["head"], q["strict"], dash)
        draw_circle(cv, fr, c, r, dash=dash, oid="boundary")
        draw_axes(cv, lb, fr, origin_ang=q["o_ang"], origin_d=21, plate=True)
        if q["inside"]:
            pc = fr.P(c)
            cv.dot(pc[0], pc[1], r=DOT_R_END)
            ck.ok(f"{q['head']}: 代入した中心は斜線の部分の中", in_region(c, polys))
            lb.put(pc[0] + 9, pc[1] + 6, lab_c, anchor="start", plate=True)
        else:
            ck.ok(f"{q['head']}: 代入した中心は斜線の部分の外", not in_region(c, polys))
        cxp = (fr.P((win[0][0], 0))[0] + fr.P((win[0][1], 0))[0]) / 2
        lb.c(cxp, 22, q["head"], weight="bold")
        lb.c(cxp, H - 20, q["cap"])
    allow_check(ck, lb, allow)
    bans = ["(x−2)²＋(y＋1)²<5", "√5", "x²＋y²≦4", "(x−3)²＋(y＋1)²>16", "(2, −1)", "(x＋1)²＋(y−2)²≦4", "x²＋y²>9", "(−1, 2)"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L11_fig2_circle_interior_exterior.svg", "lesson": "L11", "canvas": cv,
            "title": "円を境界線とする領域——(x−1)²＋(y−2)²<9 は破線の円の内部、x²＋y²≧4 は実線の円の外部",
            "desc": ("2つのパネルに、左は不等式 (x−1)²＋(y−2)²<9 の表す領域（中心 (1, 2)・半径 3 の円を破線で描き、内部に斜線）、右は不等式 x²＋y²≧4 の表す領域"
                     "（半径 2 の円を実線で描き、窓の中の外部に斜線）を描く。左は代入した中心 (1, 2) に●。下に境界線を含むかどうかを書く。"
                     "1目盛りは縦横とも同じ長さ。同型図は中心・半径と不等号を差し替えて生成する"),
            "alt": "円を境界線とする領域の2つの例。左は (x−1)²＋(y−2)²<9 の表す領域で、円を破線で描き内部に斜線。右は x²＋y²≧4 の表す領域で、円を実線で描き外部に斜線",
            "intent": "円を境界線とする領域も、境界線を描いて中心を代入すれば内部か外部かが決まることと、境界線を含むかどうかの線種の書き分けを見せる",
            "src": "lesson_11.md §3（例題5の答えの直後）",
            "params": "左 (x−1)²＋(y−2)²<9（中心 (1, 2)・半径 3・破線・窓 x −2.7〜4.8・y −1.6〜5.6）／右 x²＋y²≧4（半径 2・実線・窓 x −3.6〜3.8・y −3.4〜3.8）／1目盛り 36px（縦横共通）／円は 2° ごとの折れ線／斜線 45°・間隔 8px",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"1", "2", "4", "9"}), "allow_texts": allow}


# ===========================================================================
# L12: 連立不等式の領域（共通部分）・線形計画法
# ===========================================================================
def fig_L12_1():
    # --- パラメータ（lesson_12.md §1 例題2） ---
    r = 4                                   # x²＋y²≦16
    L = (-1, 1, 2)                          # y≧x−2 ⇔ −x＋y＋2≧0
    win, s = ((-5.4, 5.8), (-5.4, 5.6)), 34.0
    left, top = 110.0, 18.0
    labC, labL = "x²＋y²=16", "y=x−2"
    cap = "濃く示した部分が共通部分（境界線を含む）"
    allow = [labC, labL, cap, "x", "y", "O"]

    ck = Checker()
    inA = lambda p: p[0] ** 2 + p[1] ** 2 <= r * r
    inB = lambda p: p[1] >= p[0] - 2
    ck.ok("本文の検算: (0, 3) は 9≦16・3≧−2 で共通部分に入り、(3, −1) は 10≦16 だが −1≧1 が成り立たず入らない",
          inA((0, 3)) and inB((0, 3)) and inA((3, -1)) and not inB((3, -1)))
    body_has(ck, 12, ["連立不等式 x²＋y²≦16、y≧x−2 の表す領域を図示せよ",
                      "共通部分は、円の内部と周のうち、直線 y=x−2 の上側にある部分（境界線を含む）である"], "例題2 の連立不等式と答え")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 46)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    disk = circle_pts((0, 0), r)
    halfp = clip_halfplane(rect_pts(win), L)
    inter = clip_halfplane(disk, L)
    cv.fill_region([fr.Ps(inter)], SHADE)
    cv.fill_region([fr.Ps(disk)], cv.pattern("hatchA", 45))
    cv.fill_region([fr.Ps(halfp)], cv.pattern("hatchB", -45))
    bd_c = lambda p: abs(math.hypot(p[0], p[1]) - r)
    bd_l = lambda p: dist_point_line(p, L)
    region_check(ck, "x²＋y²≦16 を満たす点の集合（右上がりの斜線）", [disk], inA, bd_c, win)
    region_check(ck, "y≧x−2 を満たす点の集合（右下がりの斜線）", [halfp], inB, bd_l, win)
    region_check(ck, "両方を満たす点の集合（灰色の共通部分）", [inter], lambda p: inA(p) and inB(p),
                 lambda p: min(bd_c(p), bd_l(p)), win)
    ck.ok("本文の検算の点が塗りでも同じに分かれる（(0, 3) は灰色の中・(3, −1) は円の斜線の中で灰色の外）",
          in_region((0, 3), [inter]) and in_region((3, -1), [disk]) and not in_region((3, -1), [inter]))
    boundary_style_check(ck, "x²＋y²≦16", False, None)
    boundary_style_check(ck, "y≧x−2", False, None)
    draw_circle(cv, fr, (0, 0), r, oid="boundary")
    seg = draw_line_in_window(cv, fr, L, oid="boundary")
    ck.ok("直線 y=x−2 を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
    draw_axes(cv, lb, fr, origin_d=21, plate=True)
    lb.c(*fr.P((3.9, -4.62)), labC)
    lb.c(*fr.P((5.0, 1.55)), labL)
    lb.c(fr.P((0, 0))[0], H - 20, cap)
    allow_check(ck, lb, allow)
    bans = ["(3, 2)", "(−1, −3)", "(4, 1)", "(2, −1)", "(2/3, 5/3)", "(6, 0)", "(2, 4)", "(0, 7/2)", "x²＋y²<9", "x−y−1<0"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L12_fig1_system_common_region.svg", "lesson": "L12", "canvas": cv,
            "title": "連立不等式の表す領域は共通部分——x²＋y²≦16 と y≧x−2 の斜線の重なり（どちらの境界線も実線）",
            "desc": ("座標平面（1目盛りは縦横とも同じ長さ）に円 x²＋y²=16 と直線 y=x−2 を実線で描き、円の内部と周に右上がりの斜線、直線の上側に右下がりの斜線を引く。"
                     "両方の斜線が重なる共通部分だけを灰色で濃く示す。下に「濃く示した部分が共通部分（境界線を含む）」と書く。"
                     "同型図は円の半径と直線の係数を差し替えて生成する"),
            "alt": "連立不等式 x²＋y²≦16、y≧x−2 の表す領域。円 x²＋y²=16 の内部と、直線 y=x−2 の上側の部分に、それぞれ向きの違う斜線を引き、両方が重なる共通部分だけを濃く示す。境界線はどちらも実線",
            "intent": "連立不等式の表す領域を、各不等式の領域を描いてから共通部分をとる手順として見せ、境界線が直線と円の混在でも同じ3段で進むことを示す",
            "src": "lesson_12.md §1（例題2の答えの直後）",
            "params": "x²＋y²≦16（半径 4・実線）と y≧x−2（実線）／窓 x −5.4〜5.8・y −5.4〜5.6（1目盛り 34px・縦横共通）／斜線 45° と −45°・間隔 8px／共通部分は灰色 #d9d9d9",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"2", "16"}), "allow_texts": allow}


def fig_L12_2():
    # --- パラメータ（lesson_12.md §3 例題4。高等学校学習指導要領解説 数学編（平成30年告示）の線形計画法の例） ---
    cons = [(1, 2, 200), (3, 1, 400)]        # x＋2y≦200（原料 a）・3x＋y≦400（原料 b）
    profit = (2000, 1000)                    # P=2000x＋1000y
    P_lines = [100000, 200000, 280000]       # 平行に描く3本（値を図に書くのは本文が示した 280000 だけ）
    win, s = ((-40.0, 168.0), (-6.0, 150.0)), 2.5
    left, top = 50.0, 20.0
    cap = "破線は直線 2000x＋1000y=P（P の値を変えた3本）"

    ck = Checker()

    def meet(l1, l2):
        (a1, b1, c1), (a2, b2, c2) = l1, l2
        det = a1 * b2 - a2 * b1
        return (Fr(c1 * b2 - c2 * b1, det), Fr(a1 * c2 - a2 * c1, det))
    V = [(Fr(0), Fr(0)), meet((3, 1, 400), (0, 1, 0)), meet(cons[0], cons[1]), meet((1, 2, 200), (1, 0, 0))]
    ck.ok("頂点は (0, 0)・(400/3, 0)・(120, 40)・(0, 100)（x＋2y=200 と 3x＋y=400 の交点は (120, 40)）",
          V == [(0, 0), (Fr(400, 3), 0), (120, 40), (0, 100)])
    vals = [profit[0] * x + profit[1] * y for x, y in V]
    ck.ok("頂点での P は 0・800000/3（約 266667）・280000・100000 で、最大は (120, 40) の 280000 だけ",
          vals == [0, Fr(800000, 3), 280000, 100000] and max(vals) == 280000 and vals.count(280000) == 1)
    ck.ok("傾きの比較: 辺 3x＋y=400 の −3 < 直線 2000x＋1000y=P の −2 < 辺 x＋2y=200 の −1/2", Fr(-3) < Fr(-2) < Fr(-1, 2))
    ck.ok("いちばん上の P=280000 の直線は頂点 (120, 40) を通る（2000×120＋1000×40−280000=0）",
          P_lines[-1] == vals[2] and profit[0] * 120 + profit[1] * 40 - P_lines[-1] == 0)
    ck.ok("P=100000 の直線は頂点 (0, 100) を通る（本文の検算の値）", profit[0] * 0 + profit[1] * 100 == P_lines[0])
    ck.ok("下の2本は領域を横切る（頂点の値が直線の両側にある）",
          all(min(vals) <= Pv < max(vals) for Pv in P_lines[:-1]))
    ck.ok("A を 120 個・B を 40 個作ると原料 a は 120＋80=200 kg・原料 b は 360＋40=400 kg（どちらも使い切る）",
          120 + 2 * 40 == 200 and 3 * 120 + 40 == 400)
    body_has(ck, 12, ["4点 (0, 0)、(400/3, 0)、(120, 40)、(0, 100) を頂点とする四角形の内部と周である",
                      "このとき P=2000×120＋1000×40=280000", "x＋2y≦200、3x＋y≦400",
                      "高等学校学習指導要領解説 数学編（平成30年告示）が線形計画法の例として挙げているものである"],
             "例題4 の頂点・最大値・条件・出典")

    fr = Frame(left, top, win, s)
    H = round(top + (win[1][1] - win[1][0]) * s + 68)
    cv = Canvas(W, H)
    lb = Labels(cv)
    equal_units(ck, fr)
    poly = [(float(x), float(y)) for x, y in V]
    cv.fill_region([fr.Ps(poly)], SHADE, textured=False)
    feas = lambda p: p[0] >= 0 and p[1] >= 0 and p[0] + 2 * p[1] <= 200 and 3 * p[0] + p[1] <= 400
    bd = lambda p: min(abs(p[0]), abs(p[1]), dist_point_line(p, (1, 2, -200)), dist_point_line(p, (3, 1, -400)))
    region_check(ck, "4つの不等式を満たす点の集合（灰色の四角形）", [poly], feas, bd, win, step=2.0, margin=0.8)
    for a, b, c in cons:
        seg = draw_line_in_window(cv, fr, (a, b, -c), oid="boundary")
        ck.ok(f"境界の直線 {a if a != 1 else ''}x＋{b if b != 1 else ''}y={c} を窓の端から端まで描く", all(on_window_edge(p, win) for p in seg))
    for Pv in P_lines:
        seg = draw_line_in_window(cv, fr, (profit[0], profit[1], -Pv), w=AUX_W, dash=DASH, oid="pline")
        ck.ok(f"直線 2000x＋1000y={Pv} を窓の端から端まで破線で描き、描いた線分の傾きは −2（3本は平行）",
              all(on_window_edge(p, win) for p in seg) and near((seg[1][1] - seg[0][1]) / (seg[1][0] - seg[0][0]), -2.0))
    draw_axes(cv, lb, fr, ticks=False)
    pv = {k: fr.P((float(x), float(y))) for k, (x, y) in zip(("O", "X", "M", "Y"), V)}
    for k in ("X", "Y"):
        cv.dot(pv[k][0], pv[k][1])
    cv.dot(pv["M"][0], pv["M"][1], r=4.6)
    labX, labY, labM, labP = f"({fmt(V[1][0])}, 0)", f"(0, {fmt(V[3][1])})", pt_label("", *V[2]), f"P={vals[2]}"
    lb.c(pv["X"][0], pv["X"][1] + 29, labX)
    lb.at(pv["Y"], 205, 45, labY)
    lb.c(pv["M"][0] + 52, pv["M"][1] - 22, labM)
    lb.c(pv["M"][0] + 52, pv["M"][1] - 46, labP)
    lb.c(W / 2, H - 20, cap)
    allow = [labX, labY, labM, labP, cap, "x", "y", "O"]
    ck.ok("ラベルの座標と P の値は、連立方程式と P の式で計算した値を書いたもの", [labX, labY, labM, labP] == ["(400/3, 0)", "(0, 100)", "(120, 40)", "P=280000"])
    allow_check(ck, lb, allow)
    bans = ["(3, 2)", "(4, 0)", "(0, 7/2)", "(4, 4)", "(6, 0)", "(0, 8)", "1800", "1600", "63/4", "(7/4, 7/4)", "14/5",
            "266667", "200000", "100000"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L12_fig2_linear_programming_parallel_lines.svg", "lesson": "L12", "canvas": cv,
            "title": "線形計画法——製品 A を x 個・B を y 個作る条件の領域と、平行に動かした3本の直線 2000x＋1000y=P（最大は頂点 (120, 40) で P=280000）",
            "desc": ("4点 (0, 0)、(400/3, 0)、(120, 40)、(0, 100) を頂点とする四角形（x≧0・y≧0・x＋2y≦200・3x＋y≦400 の共通部分）を灰色で塗り、"
                     "境界の直線 x＋2y=200・3x＋y=400 を実線で描く。直線 2000x＋1000y=P を P の値を変えて3本、破線で平行に描く（いちばん上は頂点 (120, 40) を通る"
                     " P=280000 の直線）。(120, 40) に大きい●。設定と数値は高等学校学習指導要領解説 数学編（平成30年告示）の線形計画法の例（本文の例題4に出典を併記）。"
                     "1目盛りは縦横とも同じ長さ。同型図は条件の係数と利益の係数を差し替えて生成する（頂点は連立方程式で計算）"),
            "alt": "製品 A を x 個、B を y 個作る条件の表す領域（4点 (0, 0)、(400/3, 0)、(120, 40)、(0, 100) を頂点とする四角形）と、直線 2000x＋1000y=P を P の値を変えて3本平行に描いた図。利益が最大になる頂点 (120, 40) に印をつけ、そこでの P=280000 を示す",
            "intent": "1次式の値 P を「直線の位置を決めるつまみ」として、P を大きくすると直線が平行に上へ動き、領域から離れる直前に触れる頂点で最大になることを3本の平行線で見せる（コンピュータで直線を動かす活動の代わり）",
            "src": "lesson_12.md §3（例題4で P=280000 を求めた直後）",
            "params": "x≧0・y≧0・x＋2y≦200・3x＋y≦400／頂点は連立方程式で (0, 0)・(400/3, 0)・(120, 40)・(0, 100)／P=100000・200000・280000 の3本（図に値を書くのは本文が示した P=280000 だけ）／窓 x −40〜168・y −6〜150（1 あたり 2.5px・縦横共通）／出典 高等学校学習指導要領解説 数学編（平成30年告示）の例",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("subset", {"0", "3", "40", "100", "120", "400", "1000", "2000", "280000"}), "allow_texts": allow}


# ===========================================================================
# L13: 単元の地図
# ===========================================================================
def fig_L13_1():
    # --- パラメータ（lesson_13.md §1） ---
    blocks = [("点と直線", 1, 6), ("円", 7, 9), ("軌跡と領域", 10, 12)]
    top_lab = "まとめ（L13）"
    spine = "図形を、条件を満たす点の集合として見る"
    H = 300
    bw, bh, gapx, x0, y0 = 176.0, 80.0, 30.0, 26.0, 116.0     # 3つの枠の幅・高さ・間隔・左端・上端
    band = (12.0, 172.0, W - 24.0, 72.0)                        # 帯（x, y, 幅, 高さ）
    tb = (210.0, 18.0, 220.0, 46.0)                             # まとめの枠
    rng = [f"L{a:02d}〜L{b:02d}" for _, a, b in blocks]
    allow = [t for t, _, _ in blocks] + rng + [top_lab, spine]

    ck = Checker()
    ck.ok("3つのまとまりのレッスン番号が L01 から L12 まで途切れなく昇順（L01〜L06・L07〜L09・L10〜L12）",
          [a for _, a, _ in blocks] == [1, 7, 10] and [b for _, _, b in blocks] == [6, 9, 12]
          and all(blocks[i][2] + 1 == blocks[i + 1][1] for i in range(2)))
    xs = [x0 + i * (bw + gapx) for i in range(3)]
    ck.ok("3つの枠は左から順に同じ幅・同じ間隔で並び、左右の余白が等しい",
          near(xs[0], W - (xs[2] + bw)) and all(near(xs[i + 1] - xs[i], bw + gapx) for i in range(2)))
    ck.ok("帯は3つの枠の全体を左右に貫く（帯の左端＜最初の枠・最後の枠＜帯の右端）",
          band[0] < xs[0] and xs[2] + bw < band[0] + band[2])
    ck.ok("帯は3つの枠のどれとも上下に重なる（枠の下の部分を通る）", band[1] < y0 + bh and y0 < band[1])
    ck.ok("まとめの枠は3つの枠より上で、左右の中央", tb[1] + tb[3] < y0 and near(tb[0] + tb[2] / 2, W / 2))
    body_has(ck, 13, ["点と直線（L01〜L06）、円（L07〜L09）、軌跡と領域（L10〜L12）の3つのまとまりでできていた",
                      "この見方が、単元全体を貫く背骨である"], "3つのまとまりと背骨")

    cv = Canvas(W, H)
    lb = Labels(cv)
    cv.fill_region([[(band[0], band[1]), (band[0] + band[2], band[1]), (band[0] + band[2], band[1] + band[3]),
                     (band[0], band[1] + band[3])]], SHADE, textured=False)
    cv.rect(*tb, fill="#fff", sw=BOLD_W, oid="box")
    lb.c(tb[0] + tb[2] / 2, tb[1] + tb[3] / 2, top_lab, weight="bold")
    yb = tb[1] + tb[3] + 26
    cv.line(W / 2, tb[1] + tb[3], W / 2, yb, w=THIN_W, oid="tree")
    cv.line(xs[0] + bw / 2, yb, xs[2] + bw / 2, yb, w=THIN_W, oid="tree")
    for i, ((t, a, b), r_) in enumerate(zip(blocks, rng)):
        cx = xs[i] + bw / 2
        cv.line(cx, yb, cx, y0, w=THIN_W, oid="tree")
        cv.rect(xs[i], y0, bw, bh, fill="#fff", sw=MAIN_W, oid="box")
        lb.c(cx, y0 + 26, t, weight="bold")
        lb.c(cx, y0 + 54, r_)
        if i < 2:
            cv.arrow(xs[i] + bw + 3, y0 + 26, xs[i + 1] - 3, y0 + 26, w=MAIN_W, head=8.0)
    lb.c(W / 2, band[1] + band[3] - 22, spine, weight="bold")
    allow_check(ck, lb, allow)
    bans = ["2√5", "x＋2y−1=0", "x=−2", "(4, −1)", "y=3", "3＋3√2", "(−5√2/2, 5√2/2)", "5√2", "3x＋4y=25", "4x＋3y＋25=0"]
    ban_consistency(ck, allow, bans)
    cv.layout_checks(ck)

    return {"file": "L13_fig1_unit_map.svg", "lesson": "L13", "canvas": cv,
            "title": "単元の地図——点と直線（L01〜L06）・円（L07〜L09）・軌跡と領域（L10〜L12）を「図形を、条件を満たす点の集合として見る」の帯が貫く",
            "desc": ("左から順に3つの枠（点と直線 L01〜L06・円 L07〜L09・軌跡と領域 L10〜L12）を矢印でつなぎ、3つの枠の下の部分を灰色の帯が左右に貫く。"
                     "帯には「図形を、条件を満たす点の集合として見る」と書く。上にまとめ（L13）の枠を置き、3つの枠へ線で結ぶ（全体を見わたす位置）。"
                     "数字はレッスン番号だけ。同型図は枠と帯の文字を差し替えて生成する"),
            "alt": "単元の地図。点と直線（L01〜L06）、円（L07〜L09）、軌跡と領域（L10〜L12）の3つのまとまりが順に並び、その全体を「図形を、条件を満たす点の集合として見る」という1本の帯が貫いている。まとめの L13 は全体を見わたす位置にある",
            "intent": "総括回の1枚地図。3つのまとまりが1本の背骨（点の集合として見る）でつながっていることと、まとめの回が全体を見わたす位置にあることを見せる",
            "src": "lesson_13.md §1（冒頭の段落の直後）",
            "params": "枠 176×80・間隔 30・左端 26・上端 116／帯 (12, 172) 幅 616・高さ 72（灰色 #d9d9d9）／まとめの枠 (210, 18) 220×46・太枠",
            "checks": ck.items, "check_tokens": bans,
            "digit_rule": ("strip", []), "allow_texts": allow}


# ===========================================================================
# main: 陽性対照 → 生成（2回・一致）→ 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L02_1, fig_L02_2, fig_L03_1, fig_L04_1, fig_L05_1, fig_L06_1, fig_L06_2, fig_L07_1,
        fig_L08_1, fig_L09_1, fig_L10_1, fig_L10_2, fig_L11_1, fig_L11_2, fig_L12_1, fig_L12_2, fig_L13_1]

TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
COLOR_RE = re.compile(r'(fill|stroke)="([^"]+)"')
FONT_RE = re.compile(r'font-size="([0-9.]+)"')
NAME_RE = re.compile(r"L(\d\d)_fig(\d+)_[a-z0-9_]+\.svg")
_DASHES = "-‐‑‒–—―−ー－" + "・･·./:_" + " " + " " + "\t" + "•‣∙"


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


def color_problem(src):
    """線は黒だけ・塗りは白黒とグレーと、ファイル内で定義した斜線の pattern だけ。問題の並び（空なら合格）"""
    bad = []
    for kind, c in COLOR_RE.findall(src):
        if kind == "stroke":
            if c not in ("#000", "none"):
                bad.append(f"stroke={c}")
        else:
            m = re.fullmatch(r"url\(#([A-Za-z0-9_-]+)\)", c)
            if m:
                if f'<pattern id="{m.group(1)}"' not in src:
                    bad.append(f"fill={c}（未定義）")
            elif not is_gray(c):
                bad.append(f"fill={c}")
    return bad


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


def comma_bracket_hits(s):
    """読点と鍵括弧の連続（読点の直後の開き括弧・閉じ括弧の直後の読点）の出現位置"""
    pat = "、" + "「" + "|" + "」" + "、"          # このファイル自身が当たらないように連結で書く
    return [m.start() for m in re.finditer(pat, s)]


def _vocab_words():
    """公開側の検疫語彙と工場の非出荷ファイル名（このファイル自身が当たらないように連結で崩して書く）"""
    return ["candidate" + "_draft", "RESEARCH" + "_RAW", "RESEARCH" + "_BRIEF", "CONTENT" + "_MAP", "_no" + "tes/",
            "_q" + "a/", "PRODUCTION" + "_ORDER", "Q" + "A_", "FIX" + "_LOG", "INTER" + "NAL", "内部" + "用",
            "/" + "Users" + "/", "MERGE" + "_LOG", "run" + "_id", "source" + "_package",
            "public" + "_release_ready", "student" + "_distribution_ready", "external" + "_upload_ready",
            "sale" + "_ready", "canonical" + "_status", "オー" + "ナー", "監" + "督", "改稿" + "キュー",
            "低" + "知識", "体系" + "数学", "チャート" + "式"]


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
              '<text x="1" y="1">P(3, 4)</text><text x="2" y="2">y&gt;2x−1</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["P(3, 4)", "y>2x−1"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["(3, 4)"]) == ["(3, 4)"], "陽性対照失敗: 禁止文字列を検出できない"
    assert ban_hits(ts, ["(3, 3)"]) == [], "陰性対照失敗: 存在しない文字列を誤検出"
    assert digit_runs(ts) == {"3", "4", "2", "1"}, "数字抽出が壊れている"
    assert digit_problem(["x=7"], ("subset", {"2", "3"})) is not None, "陽性対照失敗: 許可外の数字を見逃す"
    assert digit_problem(["L01〜L06"], ("strip", [])) is None and digit_problem(["L13 と 7"], ("strip", [])), \
        "数字の規則 strip の対照が壊れている"
    assert digit_problem(["A(x₁, y₁)"], ("none", set())) is None and digit_problem(["x=2"], ("none", set())), \
        "数字の規則 none の対照が壊れている（下付きの数字は数えない・半角の数字は数える）"
    probes = ["a" + chr(0x200B) + "b", "e" + chr(0x0301), chr(0x2713) + chr(0xFE0F), chr(0xFF21) + chr(0xFF11),
              chr(0x1F600), "x" + chr(0x7), "キ" + chr(0xFF9E)]
    for probe in probes:
        try:
            char_hygiene(probe, "陽性対照")
        except AssertionError:
            continue
        raise AssertionError(f"文字衛生の陽性対照失敗: {probe!r} を検出できない")
    char_hygiene("x²＋y²≦16・(x−1)²・√5・A′・x₁・≧・〜・→・°・（L13）", "陰性対照")
    for probe in ["candidate" + "_draft/x", "D" + "−" + "3", "D" + "・" + "7", chr(0xFF24) + "-" + "1", "監" + "督",
                  "/" + "Users" + "/x", "run" + "_id", "D" + "1" + "2", "H" + "R" + "3"]:
        assert vocab_hits(probe), f"公開語彙の陽性対照失敗: {probe!r} を検出できない"
    for neg in ["d<r・d=r・d>r", "H(1, 3)", "まとめ（L13）", "y=x−2", "B(−1, −2)", "実行モデル: claude-opus-5-5"]:
        assert not vocab_hits(neg), f"公開語彙の陰性対照失敗: {neg!r} を誤検出 {vocab_hits(neg)}"
    assert (comma_bracket_hits("甲" + "、" + "「" + "乙」") and comma_bracket_hits("「乙」" + "、" + "丙")
            and not comma_bracket_hits("甲の「乙」と丙")), \
        "読点と鍵括弧の連続の検査の対照が壊れている"
    fake = "本文 ![甲](assets/L01_fig1_x.svg) と ![乙(1)](assets/L02_fig1_y.svg)"
    refs = {name: alt for alt, name in ALT_RE.findall(fake)}
    assert refs == {"L01_fig1_x.svg": "甲", "L02_fig1_y.svg": "乙(1)"}, f"参照の抽出が壊れている: {refs}"
    assert ref_diff(set(refs), {"L01_fig1_x.svg"}) == (["L02_fig1_y.svg"], []), "陽性対照失敗: 参照と生成の差を検出できない"
    assert ref_diff(set(refs), set(refs)) == ([], []), "陰性対照失敗: 一致を差ありと判定"
    assert is_gray("#d9d9d9") and is_gray("#fff") and not is_gray("#ff0000"), "グレー判定の対照が壊れている"
    good = '<pattern id="h"></pattern><path fill="url(#h)" stroke="none"/><line stroke="#000"/>'
    assert not color_problem(good), "色の検査の陰性対照が壊れている"
    assert color_problem('<line stroke="#777777"/>') and color_problem('<path fill="url(#zz)"/>'), \
        "色の検査の陽性対照失敗: 黒以外の線・未定義の斜線を見逃す"
    ring = [[(0, 0), (4, 0), (4, 4), (0, 4)], [(1, 1), (3, 1), (3, 3), (1, 3)]]
    assert in_region((0.5, 0.5), ring) and not in_region((2, 2), ring), "偶奇規則の内外判定が壊れている"
    half = clip_halfplane([(0, 0), (4, 0), (4, 4), (0, 4)], (-1, 0, 2))
    assert in_region((1, 1), [half]) and not in_region((3, 1), [half]), "半平面の切り取りが壊れている"
    probe = Checker()
    try:
        region_check(probe, "陽性対照", [half], lambda p: p[0] > 2, lambda p: abs(p[0] - 2), ((0, 4), (0, 4)))
    except AssertionError:
        pass
    else:
        raise AssertionError("陽性対照失敗: 塗った側と不等式の側の食い違いを検出できない")
    region_check(Checker(), "陰性対照", [half], lambda p: p[0] < 2, lambda p: abs(p[0] - 2), ((0, 4), (0, 4)))
    for bad_call in (lambda: boundary_style_check(Checker(), "陽性対照", True, None),
                     lambda: ban_consistency(Checker(), ["P(3, 4)"], ["(3, 4)"])):
        try:
            bad_call()
        except AssertionError:
            continue
        raise AssertionError("陽性対照失敗: 線種の食い違い・禁止文字列と許可ラベルの衝突を検出できない")


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
    cp = color_problem(src)
    assert not cp, f"{name}: 線は黒だけ・塗りは白黒とグレーと斜線だけ、に反する {cp}"
    sizes = [float(v) for v in FONT_RE.findall(src)]
    assert sizes and min(sizes) >= MIN_FS, f"{name}: 文字サイズの下限 {MIN_FS} を下回る"
    char_hygiene(src, name)
    vh = vocab_hits(src)
    assert not vh, f"{name}: 公開語彙の検疫に当たる {vh}"
    cb = comma_bracket_hits(src)
    assert not cb, f"{name}: 読点と鍵括弧の連続 {cb[:3]}"
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
    cb = comma_bracket_hits(own)
    assert not cb, f"generate_figures.py: 読点と鍵括弧の連続 {cb[:3]}"
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
        for key in ("title", "desc", "intent", "src", "params"):
            assert not comma_bracket_hits(meta[key]), f"{meta['file']}: {key} に読点と鍵括弧の連続"
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
                swapped.append(les)
        assert not swapped, f"連番の順が本文での登場順と違う: {swapped}"
        accept.append("連番の順: どのレッスンでも本文での登場順と一致（docs/SPEC_figures.md §3）")
    for line in accept:
        print("ACCEPT", line)
    manifest = build_manifest(rows, n_checks, total_bytes, n_texts, accept)   # 台帳の検査もここで済ませる
    for out, svg in pending:                                                   # 全部通ってから書く
        out.write_text(svg, encoding="utf-8")
    (HERE / "FIGURE_MANIFEST.md").write_text(manifest, encoding="utf-8")
    n_tokens = sum(len(m.get("check_tokens", [])) for m in rows)
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks, {n_tokens} ban-tokens, "
          f"{len(manifest.splitlines())} lines)")
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
        "# FIGURE_MANIFEST — 数学Ⅱ「図形と方程式」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的・乱数不使用）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト・図中ラベル {n_texts} 個。下表の検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。検算は数学（内分点・外分点・距離・垂直条件・点と直線の距離・対称な点・接線・軌跡の条件・"
        "領域の不等式・線形計画法の頂点の値）、本文照合（図のパラメータの点・式・比が本文 lesson_XX.md の図の行を除いた本文にそのままあること）、"
        "描画の幾何（x と y の目盛りの単位が等しい・直線が窓の端まで届く・塗った部分と不等式を満たす点の集合が格子点で一致する・"
        "境界線の線種が不等号と一致する）、配置（viewBox 内・ラベル同士が重ならない・ラベルが線にかからない・斜線の上のラベルには白地・"
        "文字サイズが viewBox 幅の3%以上）の4種。加えて全SVGに XML整形式・xmlns/viewBox・width/height なし・外部参照なし・"
        "`<title>`/`<desc>`・白背景・線は黒だけで塗りは白黒とグレーと斜線だけ・フォント指定なし の技術検査と、文字衛生検査"
        "（絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字の不在）と、公開語彙の検疫と、読点と鍵括弧の連続の検査と、"
        "答え漏れ検査を実施。答え漏れ検査は二重ゲート: (1)図中の全ラベルを、各図のパラメータブロックで宣言した許可リスト"
        "（本文が図の前後で明示している語と値のみ）と集合として完全一致で照合、"
        f"(2)禁止文字列（練習・stretch の答え由来・計{n_tokens}項目・対象値は非開示）が図中テキストと title・desc に無いことと、"
        "図ごとの数字集合の制約。禁止文字列が許可ラベルの部分文字列になっていないことも図ごとに確かめる。検査器は生成前の陽性対照"
        "（禁止値・禁止文字・検疫語彙・参照の差・塗りの食い違い・線種の食い違いを仕込んだ合成入力での検出）で毎回実証している。PASS。／ "
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
        f"白背景 rect あり・線は黒だけ・塗りは白黒とグレーとファイル内の斜線だけ・font-family なし・文字サイズ {MIN_FS}px 以上"
        f"（{len(rows)} 枚全件・スクリプトの技術検査で assert）",
        f"- 各図の assert が生成時に全件通過（計 {n_checks} 項目・上表）",
        "- 答え漏れ検査: `<text>` の文字列集合が各図の許可リストと完全一致・禁止文字列 0 件（図中テキスト・title・desc）・数字集合の制約を満たす（全図 assert）",
        "- 文字衛生・公開語彙・読点と鍵括弧の連続: 本スクリプト・全SVG・本台帳で 0 件（assert）",
        "- 決定性: 乱数不使用。同一プロセス内で各図を2回生成してバイト一致を assert。別プロセスでの再実行の一致は、"
        "出荷時に全SVGと本台帳を2回生成して照合する（生成日は日付のみなので同日なら一致。"
        "台帳に載せる集合は整列して書くので、実行ごとの要素順の差は出ない）",
        "",
        "## 描き方の約束（この単元の図に共通）",
        "",
        "- 座標平面は x 軸と y 軸の目盛りの単位を等しく描く（1目盛りの px が縦横で同じ・全図 assert）。直線は窓の端から端まで描き、線分は端点に●を打つ。",
        "- 領域は斜線（角度 45° か −45°・間隔 8px・ファイル内の pattern）で塗り、境界線を含むかどうかは線種（含む＝実線・含まない＝破線）で表す。色に意味を持たせない。連立不等式の共通部分だけは斜線の下に灰色を敷いて濃く示す。",
        "- 線形計画法の図（L12_fig2）の平行な3本の直線は補助線なので破線で描く（境界線ではない）。領域の境界線はすべて実線。",
        "- 数直線（L01_fig1）の●は数学Ⅰ「数と式」の数直線と同じ半径 3.4px。",
        "- 文字だけの図（L02_fig1・L03_fig1・L05_fig1・L07_fig1・L08_fig1）の点の位置や長さは描く値で、図に数値は書かない。描く値は台帳のパラメータ欄に記録した。",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値・式は、いずれも本文（例題の与件・図の直前に解答で示した値・図の前後の明示値）のみ。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- 例題の解答で求めた値（L01 の P(4)・Q(13)・R(−7)、L06 の H(1, 3)・2√5・B(−1, −2)、L10 の円の中心と半径、L12 の (120, 40) と P=280000）は、本文が図の直前に解答として示している。"
        "L02_fig2 の P(3, 4) だけは図の直後の例題4 (1) の解答で示す値（図は公式の直後・例題4の前に置かれている）。",
        "- 練習・stretch の答えと同じ文字列になる値が本文明示値として図に入る場合がある（L06_fig1 の 2√5 は例題1の距離で、練習の問2の距離と同じ値）。これは練習の答えの転記ではない。禁止文字列検査には、本文明示値と一致しない答え（座標・式・分数・根号の値）を登録している。",
        "- L05_fig1 には垂直条件の「積」の値を書かない（本文が図の後で言う）。L10_fig2 の title・desc には軌跡の円の名称を書かない（禁止文字列に登録）。",
        "- L12_fig2 の3本のうち、値を書くのは本文が示した P=280000 だけ（下の2本の P は描く値で、台帳のパラメータ欄だけに記録）。",
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
    cb = comma_bracket_hits(text)
    assert not cb, f"FIGURE_MANIFEST.md: 読点と鍵括弧の連続 {cb[:3]}"
    assert text.splitlines()[:4] == ["---", "distribution_status: published_draft", "---", ""] and text.splitlines()[4] == MODEL_LINE, \
        "FIGURE_MANIFEST.md: frontmatter は distribution_status の1行だけ・その直後に実行モデルの行"
    return text


if __name__ == "__main__":
    main()
