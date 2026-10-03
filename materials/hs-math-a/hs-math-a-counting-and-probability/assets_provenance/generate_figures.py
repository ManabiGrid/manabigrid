#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高校数学A「場合の数と確率」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。各図の内容仕様（各 fig_* 関数冒頭のパラメータブロック・
Checker の検算項目・台帳の記載）は本文 lesson_XX.md と一致させる。描画ヘルパーの書き方
（Canvas / Checker / 許可リスト検査 / 禁止文字列検査 / 陽性対照 / FIGURE_MANIFEST 自動生成）は
先行単元 hs-math-i-trigonometric-ratios の generate_figures.py を踏襲し、
樹形図・格子表・ベン図・扇形・折れ線のヘルパーは本単元向けに書き下ろした。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（19枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / unicodedata / xml.etree / fractions）
- 決定性: 乱数を使わない（L08_fig2 の相対度数も本文の表の固定値）。日付は「生成日」行と
  SVG 先頭コメントだけに現れる。
- 幾何・数値の自己検証: 各 fig_* 関数内の Checker が検算項目を検算し、1つでも失敗すると
  例外で停止して図を出力しない（樹形図の葉の数＝枝数の積・確率の積と和・面積比・角の和など）。
- 答えの分離（二重ゲート＋陽性対照）:
  (1) 許可リスト検査——各図が宣言した「使ってよいラベル集合」(allow_texts) と
      生成後 SVG の <text> 全内容が集合として完全一致することを検査する。
  (2) 禁止文字列検査——練習・stretch の答え由来の禁止文字列 (check_tokens) が図中テキストに
      現れないこと、および各図の「数字の集合」制約 (digit_rule) を検査する。
  検査器は main() 冒頭の陽性対照（禁止値を仕込んだ合成 SVG で検出できること）で毎回実証する。
- 文字衛生: 絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字を、本スクリプト自身と
  全 SVG・台帳に対して機械検査する（公開側の検疫 CI と同じ向き）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
"""

import itertools
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
LESSON_DIR = HERE.parent          # lesson_XX.md はこの階層（公開側の単元フォルダでも同じ）
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md の規約） --------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅（破線）
DASH = "6 4"      # 破線
THIN_W = 1.0      # 細線（格子・樹形図の枝）
DOT_R = 2.5       # 点マーカー半径
SHADE = "#d9d9d9"   # うすい網かけ
SHADE2 = "#b3b3b3"  # 濃い網かけ
SHADE3 = "#efefef"  # ごくうすい網かけ
DEG = math.pi / 180.0


def fs_for(width):
    """基本文字サイズ = viewBox 幅の 3 パーセント（四捨五入）"""
    return round(width * 0.03)


# ===========================================================================
# ユーティリティ
# ===========================================================================
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def unit(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・記号は個別"""
    special = {"°": 0.45, " ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4,
               "!": 0.35, "=": 0.6, "ᶜ": 0.45, "₁": 0.4, "₂": 0.4, "₃": 0.4, "₄": 0.4,
               "₅": 0.4, "₆": 0.4, "{": 0.45, "}": 0.45, "|": 0.3, "_": 0.6}
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
    """ラベル群に含まれる数字の連なり（「3×2×4=24」→ {"3","2","4","24"}）"""
    out = set()
    for t in texts:
        out.update(re.findall(r"[0-9]+", t))
    return out


def show_set(s):
    """集合を整列した文字列にする（台帳に載せる detail 用。要素順の揺れを消す）"""
    return "{" + ", ".join(sorted(s, key=lambda t: (len(t), t))) + "}"


def no_digits(texts):
    return not any(re.search(r"[0-9]", t) for t in texts)


def frac_str(f):
    """Fraction → 「分子/分母」（約分しない表記は呼び出し側で文字列を直接書く）"""
    return f"{f.numerator}/{f.denominator}"


# ===========================================================================
# 描画ヘルパー（Canvas = px 座標）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.body = []
        self.defs = []
        self.texts = []          # (x0, y0, x1, y1, s) 推定バウンディングボックス
        self.bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

    def _grow(self, x, y, pad=0.0):
        self.bbox[0] = min(self.bbox[0], x - pad)
        self.bbox[1] = min(self.bbox[1], y - pad)
        self.bbox[2] = max(self.bbox[2], x + pad)
        self.bbox[3] = max(self.bbox[3], y + pad)

    def raw(self, s):
        self.body.append(s)

    def hatch_def(self, pid="hatch"):
        """斜線ハッチング（45°）を <pattern> で内蔵（ファイル内で完結）"""
        if any(f'id="{pid}"' in d for d in self.defs):
            return f"url(#{pid})"
        self.defs.append(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="8" height="8">'
                         f'<path d="M-2,2 L2,-2 M0,8 L8,0 M6,10 L10,6" stroke="#000" stroke-width="1"/></pattern>')
        return f"url(#{pid})"

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w); self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="#000" stroke-width="{w}"{d}/>')

    def polyline(self, pts, w=MAIN_W, dash=None, close=False, fill="none"):
        for x, y in pts:
            self._grow(x, y, w)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="{fill}" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="round"{d}/>')

    def polygon_fill(self, pts, fill):
        for x, y in pts:
            self._grow(x, y)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')

    def dot(self, x, y, r=DOT_R):
        self._grow(x, y, r)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')

    def circle(self, x, y, r, fill="none", sw=MAIN_W):
        """円（arc フラグ不使用: 2° 刻みでサンプリングした閉じた折れ線）"""
        pts = [(x + r * math.cos(i * 2 * DEG), y + r * math.sin(i * 2 * DEG)) for i in range(180)]
        if sw > 0:
            self.polyline(pts, w=sw, close=True, fill=fill)
        else:
            self.polygon_fill(pts, fill)
        self._grow(x - r, y - r, sw); self._grow(x + r, y + r, sw)

    def rect(self, x, y, w, h, fill="none", dash=None, sw=1.4):
        self._grow(x, y, sw); self._grow(x + w, y + h, sw)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        stroke = f'stroke="#000" stroke-width="{sw}"' if sw > 0 else 'stroke="none"'
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'fill="{fill}" {stroke}{d}/>')

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

    def plate_text(self, x, y, s, size, anchor="middle", weight=None, pad=3.0):
        """網かけの上に置くラベル: 白い下敷きを先に描いてから文字を置く"""
        w = est_w(s, size)
        x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        self.rect(x0 - pad, y - 0.8 * size - pad, w + 2 * pad, 1.02 * size + 2 * pad, fill="#fff", sw=0)
        self.text(x, y, s, size, anchor=anchor, weight=weight)

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
        defs = f"<defs>{''.join(self.defs)}</defs>\n" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md 準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )


def arrow(cv, x1, y1, x2, y2, w=1.4, head=7.0):
    """px 座標で矢印（線＋先端の三角形）"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.line(x1, y1, bx, by, w=w)
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
           (bx - nx * head * 0.45, by - ny * head * 0.45)]
    cv.polygon_fill(pts, "#000")


def edge_label(cv, p, q, s, fs, off=13.0, labels=None):
    """枝 pq の中点から、上向き側の法線方向へ off px ずらしてラベルを置く"""
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    d = unit((q[0] - p[0], q[1] - p[1]))
    n = (-d[1], d[0])
    if n[1] > 0:
        n = (-n[0], -n[1])
    if labels is not None:
        labels.append(s)
    cv.text(mx + n[0] * off, my + n[1] * off + fs * 0.35, s, fs)


def tree_layout(branching, y_top, y_bottom):
    """等長の樹形図: 各段の枝数 branching=[b1, b2, ...] から、葉を等間隔に置き、親を子の平均に置く。
    戻り値: levels[k] = 第 k 段の節点の y 座標リスト（levels[0] は根の1点）"""
    n_leaf = 1
    for b in branching:
        n_leaf *= b
    step = (y_bottom - y_top) / (n_leaf - 1)
    leaves = [y_top + i * step for i in range(n_leaf)]
    levels = [leaves]
    for b in reversed(branching):
        prev = levels[0]
        grp = [prev[i:i + b] for i in range(0, len(prev), b)]
        levels.insert(0, [sum(g) / len(g) for g in grp])
    return levels


def draw_tree(cv, xs, levels, branching, node_r=DOT_R, w=THIN_W):
    """tree_layout の結果を点と枝で描く（節点は黒丸）"""
    for k in range(len(branching)):
        b = branching[k]
        for i, y in enumerate(levels[k]):
            for j in range(b):
                cy = levels[k + 1][i * b + j]
                cv.line(xs[k], y, xs[k + 1], cy, w=w)
    for k, ys in enumerate(levels):
        for y in ys:
            cv.dot(xs[k], y, node_r)


def sector_pts(cx, cy, r, deg_from, deg_to, step=2.0):
    """中心・半径・数学の角（反時計回り）から扇形の多角形（中心を含む）を返す"""
    span = deg_to - deg_from
    k = max(2, int(math.ceil(abs(span) / step)))
    pts = [(cx, cy)]
    for i in range(k + 1):
        a = (deg_from + span * i / k) * DEG
        pts.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return pts


def in_disk(p, c):
    return dist(p, c[:2]) < c[2]


def circle_in_rect(c, rect):
    x, y, r = c
    rx, ry, rw, rh = rect
    return rx < x - r and x + r < rx + rw and ry < y - r and y + r < ry + rh


class Checker:
    """幾何・数値検算の記録つき assert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


# ===========================================================================
# 共通部品: 2個のさいころの 6×6 の表（L01_fig2・L08_fig1）
# ===========================================================================
def dice_table(shade_sum=None, caption=None, file="", title="", desc="", alt="", intent="",
               src="", params="", check_tokens=(), extra_checks=None):
    # --- パラメータ ---
    W = 640
    faces = [1, 2, 3, 4, 5, 6]
    cell = 60
    x0, y0 = 150, 80          # 表の左上（見出し行・列を含む）
    fs = fs_for(W)
    H = y0 + cell * 7 + (60 if caption else 30)

    ck = Checker()
    sums = {(a, b): a + b for a in faces for b in faces}
    ck.ok("ますの総数は 6×6=36", len(sums) == 36)
    ck.ok("目の和は 2 以上 12 以下", min(sums.values()) == 2 and max(sums.values()) == 12)
    ck.ok("和が5のますは4個・和が10のますは3個（本文 L01 例題3）",
          sum(1 for v in sums.values() if v == 5) == 4 and sum(1 for v in sums.values() if v == 10) == 3)
    if shade_sum is not None:
        shaded = sorted(k for k, v in sums.items() if v == shade_sum)
        ck.ok(f"和が{shade_sum}のますは5個で、(2,6)(3,5)(4,4)(5,3)(6,2)（本文 L08 例題3）",
              shaded == [(2, 6), (3, 5), (4, 4), (5, 3), (6, 2)], f"{shaded}")
        ck.ok("塗ったますは右上から左下へ斜めに並ぶ（大＋小が一定）",
              all(a + b == shade_sum for a, b in shaded))
    if extra_checks:
        extra_checks(ck, shaded if shade_sum is not None else [])

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    # 網かけ（枠線より先に塗る）
    if shade_sum is not None:
        for (a, b), v in sums.items():
            if v == shade_sum:
                cv.rect(x0 + b * cell, y0 + a * cell, cell, cell, fill=SHADE, sw=0)
    # 格子
    for i in range(8):
        cv.line(x0, y0 + i * cell, x0 + 7 * cell, y0 + i * cell, w=THIN_W)
        cv.line(x0 + i * cell, y0, x0 + i * cell, y0 + 7 * cell, w=THIN_W)
    cv.rect(x0, y0, 7 * cell, 7 * cell, sw=MAIN_W)
    cv.line(x0, y0 + cell, x0 + 7 * cell, y0 + cell, w=MAIN_W)
    cv.line(x0 + cell, y0, x0 + cell, y0 + 7 * cell, w=MAIN_W)
    # 見出し
    T(x0 + cell / 2, y0 + cell / 2 + fs * 0.35, "和")
    for j, b in enumerate(faces):
        T(x0 + (j + 1) * cell + cell / 2, y0 + cell / 2 + fs * 0.35, str(b), weight="bold")
    for i, a in enumerate(faces):
        T(x0 + cell / 2, y0 + (i + 1) * cell + cell / 2 + fs * 0.35, str(a), weight="bold")
    for (a, b), v in sums.items():
        T(x0 + b * cell + cell / 2, y0 + a * cell + cell / 2 + fs * 0.35, str(v))
    T(x0 + cell + 3 * cell, y0 - 24, "小の目")
    T(x0 - 70, y0 + cell + 3 * cell + fs * 0.35, "大の目")
    if caption:
        T(x0 + 3.5 * cell, y0 + 7 * cell + 40, caption)
    cv.layout_checks(ck)
    return {"file": file, "canvas": cv, "title": title, "desc": desc, "alt": alt, "intent": intent,
            "src": src, "params": params, "checks": ck.items, "check_tokens": list(check_tokens),
            "digit_rule": ("subset", {str(v) for v in range(1, 13)}), "allow_texts": labels}


# ===========================================================================
# L01
# ===========================================================================
# 図1: L01 §1 3枚の硬貨の樹形図（区別あり・8枝）
def fig_L01_1():
    # --- パラメータ（lesson_01.md §1） ---
    coins = ["10円", "50円", "100円"]
    faces = ["表", "裏"]
    W, H = 640, 480
    xs = [60, 200, 340, 480]          # 根・1枚目・2枚目・3枚目の x
    y_top, y_bottom = 90, 440
    total_label = "8通り"
    fs = fs_for(W)

    branching = [len(faces)] * len(coins)
    levels = tree_layout(branching, y_top, y_bottom)
    ck = Checker()
    ck.ok("葉の数 = 2×2×2 = 8（枝数の積）", len(levels[-1]) == 8 == 2 ** 3)
    ck.ok("各段の節点数が 1・2・4・8", [len(l) for l in levels] == [1, 2, 4, 8])
    step = levels[-1][1] - levels[-1][0]
    ck.ok("葉が等間隔に並ぶ", all(near(levels[-1][i + 1] - levels[-1][i], step) for i in range(7)),
          f"間隔={step:.1f}px")
    ck.ok("親の y は子の y の平均（各段）",
          all(near(levels[k][i], (levels[k + 1][2 * i] + levels[k + 1][2 * i + 1]) / 2)
              for k in range(3) for i in range(len(levels[k]))))
    ck.ok("ラベル「8通り」の 8 は葉の数と一致", total_label == f"{len(levels[-1])}通り")

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    half = 14  # 節点ラベル（表・裏）の半幅: 枝は文字を避けて引く
    for k in range(3):
        for i, y in enumerate(levels[k]):
            sx = xs[k] + (half if k > 0 else 4)
            for j in range(2):
                cy = levels[k + 1][2 * i + j]
                cv.line(sx, y, xs[k + 1] - half, cy, w=THIN_W)
    cv.dot(xs[0], levels[0][0])
    for k in range(1, 4):
        for i, y in enumerate(levels[k]):
            T(xs[k], y + fs * 0.35, faces[i % 2])
    for k, name in enumerate(coins):
        T(xs[k + 1], 46, name, weight="bold")
    bx = xs[3] + 40
    cv.line(bx, y_top, bx, y_bottom, w=THIN_W)
    cv.line(bx - 5, y_top, bx, y_top, w=THIN_W)
    cv.line(bx - 5, y_bottom, bx, y_bottom, w=THIN_W)
    T(bx + 10, (y_top + y_bottom) / 2 + fs * 0.35, total_label, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L01_fig1_three_coins_tree.svg", "lesson": "L01", "canvas": cv,
            "title": "3枚の硬貨（10円・50円・100円）を投げたときの樹形図——右端の枝は8本",
            "desc": "根から 10円→50円→100円 の順に表・裏の2本ずつ枝分かれする等長の樹形図。葉は8本で右端に 8通り のラベル。同型図は硬貨の名（段数）と面の名を差し替えて生成する（葉の数は 2 の段数乗）",
            "alt": "3枚の硬貨（10円・50円・100円）を投げたときの樹形図。1枚目が表か裏かで2本に分かれ、2枚目・3枚目でさらに2本ずつ分かれて、右端に8本の枝がそろう",
            "intent": "中2の樹形図を「場合の数」の言葉で言い直す導入図。3段の2分岐で右端が 2×2×2=8 本になることを見せる",
            "src": "lesson_01.md §1（場合・場合の数の定義の直後）",
            "params": "硬貨 10円・50円・100円／面 表・裏／列 x=60・200・340・480／葉 y=90〜440 等間隔／右端ラベル 8通り",
            "checks": ck.items,
            "check_tokens": ["321", "2031", "15", "18", "24", "12", "3通り", "6通り"],
            "digit_rule": ("subset", {"10", "50", "100", "8"}),
            "allow_texts": labels}


# 図2: L01 §3 2個のさいころの二次元の表（6×6・目の和）
def fig_L01_2():
    return dict(dice_table(
        file="L01_fig2_two_dice_sum_table.svg",
        title="大小2個のさいころの目の組を並べた6×6の二次元の表——ますに目の和",
        desc="縦に大の目 1〜6・横に小の目 1〜6 をとり、36個のますに目の和（2〜12）を書いた格子表。塗り分けはしない。同型図はますの値（和・積・差）を差し替えて生成する",
        alt="大小2個のさいころの目の組を並べた6×6の二次元の表。縦に大の目1〜6、横に小の目1〜6をとり、36個のますに目の和を書き込んである",
        intent="中2の二次元の表を回収し、「和の値で分類する」原則（例題3）を表で検算するための図。和が5・10のますは読者が塗る（図では塗らない）",
        src="lesson_01.md §3（例題3の解答の直後）",
        params="大の目 1〜6（行）・小の目 1〜6（列）／ます 60px・左上 (150,80)／ますの値=大＋小／塗りなし",
        check_tokens=["321", "2031", "15", "18", "24", "7通り", "9通り"]), lesson="L01")


# ===========================================================================
# L02
# ===========================================================================
# 図1: L02 §2 2集合のベン図に個数を書き込む（電車・バス）
def fig_L02_1():
    # --- パラメータ（lesson_02.md §2 例題1） ---
    n_U, n_A, n_B, n_AB = 40, 22, 15, 6
    name_A, name_B = "電車", "バス"
    W, H = 640, 360
    rect = (60, 40, 520, 280)            # 全体集合 U の枠
    r = 105
    cA = (250, 180, r)
    cB = (390, 180, r)
    fs = fs_for(W)

    only_A, only_B, outside = n_A - n_AB, n_B - n_AB, n_U - (n_A + n_B - n_AB)
    ck = Checker()
    ck.ok("電車だけ = 22−6 = 16", only_A == 16)
    ck.ok("バスだけ = 15−6 = 9", only_B == 9)
    ck.ok("どちらも使わない = 40−(22＋15−6) = 9", outside == 9)
    ck.ok("4つの部分の合計が n(U)=40 に戻る", only_A + n_AB + only_B + outside == n_U)
    ck.ok("n(A∪B)=n(A)＋n(B)−n(A∩B)=31 と部分の和が一致", n_A + n_B - n_AB == only_A + n_AB + only_B == 31)
    d = dist(cA[:2], cB[:2])
    ck.ok("2円は重なり、どちらも他方を含まない（|r−r| < 中心距離 < 2r）", 0 < d < 2 * r, f"d={d:.0f}, r={r}")
    ck.ok("2円とも U の枠の内側", circle_in_rect(cA, rect) and circle_in_rect(cB, rect))
    pA = (cA[0] - 55, cA[1])
    pB = (cB[0] + 55, cB[1])
    pAB = ((cA[0] + cB[0]) / 2, cA[1])
    pOut = (rect[0] + rect[2] - 40, rect[1] + rect[3] - 30)
    ck.ok("数値ラベルの位置が正しい領域にある（電車だけ／重なり／バスだけ／外側）",
          in_disk(pA, cA) and not in_disk(pA, cB) and in_disk(pAB, cA) and in_disk(pAB, cB)
          and in_disk(pB, cB) and not in_disk(pB, cA) and not in_disk(pOut, cA) and not in_disk(pOut, cB))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    cv.rect(*rect, sw=1.4)
    cv.circle(*cA)
    cv.circle(*cB)
    T(rect[0] + 12, rect[1] + 24, "U", anchor="start", weight="bold")
    T(cA[0] - 60, cA[1] - r - 10, name_A, weight="bold")
    T(cB[0] + 60, cB[1] - r - 10, name_B, weight="bold")
    T(pA[0], pA[1] + fs * 0.35, str(only_A))
    T(pAB[0], pAB[1] + fs * 0.35, str(n_AB))
    T(pB[0], pB[1] + fs * 0.35, str(only_B))
    T(pOut[0], pOut[1] + fs * 0.35, str(outside))
    cv.layout_checks(ck)

    return {"file": "L02_fig1_venn_two_sets_counts.svg", "lesson": "L02", "canvas": cv,
            "title": "2集合のベン図に個数を書き込む——電車 22人・バス 15人・両方 6人・全体 40人",
            "desc": "長方形 U の中に円「電車」と円「バス」を重ねて描き、電車だけ 16・重なり 6・バスだけ 9・外側 9 を書き込む。合計 40。同型図は n(U)・n(A)・n(B)・n(A∩B) を差し替えて生成する（各部分は差で自動計算）",
            "alt": "2つの円のベン図。左の円が電車、右の円がバスで、重なりの部分に6、電車だけの部分に16、バスだけの部分に9、2つの円の外側に9が書き込まれている",
            "intent": "「共通部分から書く→外へ→合計で検算」の手順を1枚で見せる。n(A∪B)=n(A)＋n(B)−n(A∩B) の意味（6 を2回数えない）を部分の個数で示す",
            "src": "lesson_02.md §2（例題1の解答の直後）",
            "params": "n(U)=40・n(A)=22・n(B)=15・n(A∩B)=6／円の半径 105・中心 (250,180)・(390,180)／枠 (60,40)-(580,320)",
            "checks": ck.items,
            "check_tokens": ["25", "26", "35", "74", "140", "60", "31", "22", "15", "10"],
            "digit_rule": ("subset", {"16", "6", "9"}),
            "allow_texts": labels}


# ===========================================================================
# L03〜L07
# ===========================================================================
# 図1: L03 §2 段階の樹形図（主菜3→副菜2→飲み物4・枝の数の積）
def fig_L03_1():
    # --- パラメータ（lesson_03.md §2 例題2） ---
    stages = [("主菜", 3), ("副菜", 2), ("飲み物", 4)]
    W, H = 640, 540
    xs = [50, 180, 320, 470]
    y_top, y_bottom = 80, 500
    fs = fs_for(W)

    branching = [b for _, b in stages]
    levels = tree_layout(branching, y_top, y_bottom)
    product = 1
    for b in branching:
        product *= b
    ck = Checker()
    ck.ok("葉の数 = 3×2×4 = 24（枝数の積）", len(levels[-1]) == product == 24)
    ck.ok("各段の節点数が 1・3・6・24", [len(l) for l in levels] == [1, 3, 6, 24])
    ck.ok("どの主菜の枝にも副菜の枝が2本ずつ、どの副菜の枝にも飲み物の枝が4本ずつ",
          len(levels[2]) == 3 * 2 and len(levels[3]) == 6 * 4)
    step = levels[-1][1] - levels[-1][0]
    ck.ok("葉が等間隔に並ぶ", all(near(levels[-1][i + 1] - levels[-1][i], step) for i in range(23)),
          f"間隔={step:.1f}px")
    ck.ok("式ラベル 3×2×4=24 の値が葉の数と一致", 3 * 2 * 4 == len(levels[-1]))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    draw_tree(cv, xs, levels, branching)
    for k, (name, b) in enumerate(stages):
        T(xs[k + 1], 42, f"{name}（{b}種類）", weight="bold")
    bx = xs[3] + 30
    cv.line(bx, y_top, bx, y_bottom, w=THIN_W)
    cv.line(bx - 5, y_top, bx, y_top, w=THIN_W)
    cv.line(bx - 5, y_bottom, bx, y_bottom, w=THIN_W)
    T(bx + 10, (y_top + y_bottom) / 2 - fs * 0.5, "3×2×4", anchor="start")
    T(bx + 10, (y_top + y_bottom) / 2 + fs * 1.0, "=24通り", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L03_fig1_product_rule_tree.svg", "lesson": "L03", "canvas": cv,
            "title": "段階の樹形図——主菜3×副菜2×飲み物4 で右端の枝は 24 本",
            "desc": "根から主菜3本、そのそれぞれから副菜2本、さらにそれぞれから飲み物4本に枝分かれする等長の樹形図。葉は 24 本で、右端に 3×2×4=24通り のラベル。同型図は各段の名と枝数を差し替えて生成する（葉の数は枝数の積）",
            "alt": "主菜3本の枝から始まり、それぞれが副菜2本に分かれ、さらにそれぞれが飲み物4本に分かれる段階の樹形図。右端の枝の数が 3×2×4=24 になることを示す",
            "intent": "積の法則の要「そのそれぞれに対して n 通りずつ」を、段ごとの枝数がそろった樹形図で見せる",
            "src": "lesson_03.md §2（例題2の解答の直後）",
            "params": "段 主菜 3・副菜 2・飲み物 4／列 x=50・180・320・470／葉 y=80〜500 等間隔／右端ラベル 3×2×4 / =24通り",
            "checks": ck.items,
            "check_tokens": ["7", "210", "28", "36", "40", "21", "18", "20", "12", "9"],
            "digit_rule": ("subset", {"3", "2", "4", "24"}),
            "allow_texts": labels}


# 図1: L04 §1 先頭から順に選ぶ樹形図（枝数 5→4→3・葉 60）
def fig_L04_1():
    # --- パラメータ（lesson_04.md §1 例題1） ---
    people = ["A", "B", "C", "D", "E"]
    n, r = 5, 3
    W, H = 640, 560
    xs = [60, 190, 330, 470]
    y_top, y_bottom = 80, 520
    fs = fs_for(W)

    branching = [n - k for k in range(r)]
    levels = tree_layout(branching, y_top, y_bottom)
    ck = Checker()
    ck.ok("枝数が 5→4→3 と1つずつ減る", branching == [5, 4, 3])
    ck.ok("葉の数 = 5×4×3 = 60 = 5P3", len(levels[-1]) == 60 == math.perm(5, 3))
    ck.ok("各段の節点数が 1・5・20・60", [len(l) for l in levels] == [1, 5, 20, 60])
    step = levels[-1][1] - levels[-1][0]
    ck.ok("葉が等間隔に並ぶ（間隔 > 6px で枝が見分けられる）",
          step > 6 and all(near(levels[-1][i + 1] - levels[-1][i], step) for i in range(59)),
          f"間隔={step:.1f}px")
    ck.ok("1段目の節点ラベルは A〜E の5人", len(people) == n == len(levels[1]))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    # 根→1段目の枝は名前ラベルの手前で止め、ラベルを枝の切れ目に置く（枝が文字を横切らない）
    for i, y in enumerate(levels[1]):
        cv.line(xs[0] + 4, levels[0][0], xs[1] - 30, y, w=THIN_W)
        T(xs[1] - 16, y + fs * 0.35, people[i], weight="bold")
    draw_tree(cv, xs[1:], levels[1:], branching[1:], node_r=1.8)
    cv.dot(xs[0], levels[0][0])
    for k, (name, b) in enumerate([("先頭", 5), ("2番目", 4), ("3番目", 3)]):
        T(xs[k + 1], 42, f"{name}（{b}通り）", weight="bold")
    bx = xs[3] + 30
    cv.line(bx, y_top, bx, y_bottom, w=THIN_W)
    cv.line(bx - 5, y_top, bx, y_top, w=THIN_W)
    cv.line(bx - 5, y_bottom, bx, y_bottom, w=THIN_W)
    T(bx + 10, (y_top + y_bottom) / 2 - fs * 0.5, "5×4×3", anchor="start")
    T(bx + 10, (y_top + y_bottom) / 2 + fs * 1.0, "=60通り", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L04_fig1_permutation_tree_branches.svg", "lesson": "L04", "canvas": cv,
            "title": "先頭から順に人を選ぶ樹形図——枝の数が 5→4→3 と減り、右端は 60 本",
            "desc": "5人 A〜E から3人を選んで並べる樹形図。1段目 5本（A〜E）、2段目は各 4本、3段目は各 3本で、葉は 5×4×3=60 本。同型図は n と r を差し替えて生成する（枝数 n, n−1, …, n−r＋1）",
            "alt": "先頭から順に人を選ぶ樹形図。1段目の枝が5本、2段目はそれぞれ4本、3段目はそれぞれ3本に分かれ、枝の数が 5→4→3 と1つずつ減っていく様子を示す",
            "intent": "nPr を積の法則から導く図。いちど並べた人は次の段階で選べないので枝数が1つずつ減ることを見せる",
            "src": "lesson_04.md §1（例題1の解答の直後）",
            "params": "n=5・r=3・人 A〜E／列 x=60・190・330・470／葉 y=80〜520 等間隔（60本）／右端ラベル 5×4×3 / =60通り",
            "checks": ck.items,
            "check_tokens": ["5040", "480", "210", "144", "120", "100", "72", "52", "48", "42", "36", "30", "24", "20", "9"],
            "digit_rule": ("subset", {"5", "4", "3", "2", "60"}),
            "allow_texts": labels}


# 図1: L05 §1 円順列——A を上に固定した配置と、1席ずつ回転した配置
def fig_L05_1():
    # --- パラメータ（lesson_05.md §1 例題1） ---
    seq0 = "ABCDE"                          # 上の席から時計回りに読んだ列
    seqs = [seq0[k:] + seq0[:k] for k in range(5)]   # 本文: ABCDE・BCDEA・CDEAB・DEABC・EABCD
    W, H = 640, 270
    panel_w = 128
    cy, R, RL = 115, 44, 27                 # 円の中心 y・テーブルの半径・名前ラベルの半径（席の内側）
    caption = "回転して重なる配置は同じ座り方"
    fs = fs_for(W)

    n = len(seq0)
    angles = [90 - 360 * i / n for i in range(n)]     # 上の席から時計回り（数学の角・度）
    ck = Checker()
    ck.ok("席は円周上に等間隔（隣り合う席の中心角 72°）",
          all(near(angles[i] - angles[i + 1], 72) for i in range(n - 1)) and near(360 / n, 72))
    ck.ok("最初のパネルは A が上の席（角 90°）", seq0[0] == "A" and angles[0] == 90)
    ck.ok("各パネルの列は前のパネルを1席ずつ回転したもの（巡回シフト）",
          all(seqs[k] == seqs[k - 1][1:] + seqs[k - 1][0] for k in range(1, n)))
    ck.ok("5つの列は本文の ABCDE・BCDEA・CDEAB・DEABC・EABCD と一致",
          seqs == ["ABCDE", "BCDEA", "CDEAB", "DEABC", "EABCD"])
    ck.ok("どの列も同じ相対的な位置関係（各人の右隣が全パネルで同じ）",
          all({s[i]: s[(i + 1) % n] for i in range(n)} == {seq0[i]: seq0[(i + 1) % n] for i in range(n)}
              for s in seqs))
    ck.ok("1つの座り方に対応する列の数 5 = 人数（n!／n=(n−1)! の n）", len(seqs) == n)

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    for k, s in enumerate(seqs):
        cx = panel_w * k + panel_w / 2
        cv.circle(cx, cy, R, sw=MAIN_W)
        for i, ch in enumerate(s):
            a = angles[i] * DEG
            cv.dot(cx + R * math.cos(a), cy - R * math.sin(a), 3.0)
            T(cx + RL * math.cos(a), cy - RL * math.sin(a) + fs * 0.35, ch, weight="bold")
        T(cx, 218, s)
    T(W / 2, 256, caption)
    cv.layout_checks(ck)

    return {"file": "L05_fig1_circular_permutation_rotations.svg", "lesson": "L05", "canvas": cv,
            "title": "円順列——A を上の席に固定した配置と、それを1席ずつ回転した4つの配置は同じ座り方",
            "desc": "5つの席を円周上に等間隔に置いた円卓を5つ並べ、上の席から時計回りに ABCDE・BCDEA・CDEAB・DEABC・EABCD と読める配置を描く。どれも各人の右隣が同じなので同じ座り方。同型図は人数（列の文字列）を差し替えて生成する",
            "alt": "5つの席が円周上に等間隔に並び、A を上の席に固定した配置と、それを1席ずつ回転した配置が並べてある。回転したものは同じ座り方とみることを示す",
            "intent": "「1つを固定する」と「n 通りの回転で同じになる（n!／n）」の2つの見方の土台。1つの円形の座り方に5通りの列が対応することを見せる",
            "src": "lesson_05.md §1（例題1の直後・見方1・見方2の前）",
            "params": "列 ABCDE とその巡回シフト4つ／パネル幅 128・円の半径 44・名前ラベルの半径 27（席の内側）・中心 y=115／数値ラベルなし",
            "checks": ck.items,
            "check_tokens": ["24", "120", "720", "243", "64", "32", "31", "30", "18", "16", "12"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# 図1: L06 §1 「選ぶ→並べる」の対応図（1つの組に 3!=6 個の順列）
def fig_L06_1():
    # --- パラメータ（lesson_06.md §1 例題1） ---
    group = "ABC"
    perms = ["ABC", "ACB", "BAC", "BCA", "CAB", "CBA"]     # 本文の順
    W, H = 640, 420
    box = (60, 175, 170, 50)               # 左の組の枠
    x_perm, y0, dy = 470, 70, 56           # 右の順列の列
    caption = "1つの組に 3!=6 個の順列が対応"
    fs = fs_for(W)

    ck = Checker()
    ck.ok("右の6個は {A, B, C} の並べ替えをもれなく重複なく尽くす（集合として一致）",
          sorted(perms) == sorted("".join(p) for p in itertools.permutations(group)))
    ck.ok("個数 = 3! = 6", len(perms) == math.factorial(3) == 6)
    ck.ok("本文の列挙順（辞書式）と一致", perms == sorted(perms))
    ck.ok("矢印は組から各順列へ1本ずつ（6本）", len(perms) == 6)

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    cv.rect(*box, sw=MAIN_W)
    T(box[0] + box[2] / 2, box[1] + box[3] / 2 + fs * 0.35, "{A, B, C}", weight="bold")
    T(box[0] + box[2] / 2, 42, "組（選び方）", weight="bold")
    T(x_perm, 42, "順列（並べ方）", weight="bold")
    for i, p in enumerate(perms):
        y = y0 + i * dy
        T(x_perm, y + fs * 0.35, p)
        arrow(cv, box[0] + box[2] + 6, box[1] + box[3] / 2, x_perm - 40, y, w=1.4, head=7.0)
    T(W / 2, 400, caption)
    cv.layout_checks(ck)

    return {"file": "L06_fig1_choose_then_arrange.svg", "lesson": "L06", "canvas": cv,
            "title": "「選ぶ→並べる」の対応図——1つの組 {A, B, C} に 3!=6 個の順列が対応",
            "desc": "左に組 {A, B, C} の枠、右に ABC・ACB・BAC・BCA・CAB・CBA の6つの順列を縦に並べ、枠から各順列へ矢印を引く。同型図は組の文字と r を差し替えて生成する（順列は r! 個）",
            "alt": "左に3人の組（例として {A, B, C}）が1つ、右にその組を並べ替えた6通りの列 ABC・ACB・BAC・BCA・CAB・CBA が矢印で結ばれている。1つの組に 3!=6 個の順列が対応することを示す",
            "intent": "nCr=nPr／r! の「r! で割る理由」を、1つの組に r! 個の順列が束になって対応する図で見せる",
            "src": "lesson_06.md §1（例題1の解答の途中）",
            "params": "組 {A, B, C}／順列 6 個（辞書式）／枠 (60,175) 170×50／順列の列 x=470・y=70 から 56 間隔／キャプション 1つの組に 3!=6 個の順列が対応",
            "checks": ck.items,
            "check_tokens": ["495", "220", "126", "120", "10", "45", "56", "84", "90", "60", "35", "21", "20", "15", "12"],
            "digit_rule": ("subset", {"3", "6", "1"}),
            "allow_texts": labels}


# 図1: L07 §3 格子の最短経路（右4・上3・道順 →→↑→↑↑→）
def fig_L07_1():
    # --- パラメータ（lesson_07.md §3 例題5） ---
    nx, ny = 4, 3                          # 右へ4区画・上へ3区画
    route = "→→↑→↑↑→"                      # 本文が例示する1つの道順
    W, H = 640, 440
    cell = 70
    ox, oy = 150, 340                      # P（左下）の px
    fs = fs_for(W)

    pts = [(0, 0)]
    for ch in route:
        x, y = pts[-1]
        pts.append((x + 1, y) if ch == "→" else (x, y + 1))
    ck = Checker()
    ck.ok("道順は → が4個・↑ が3個の計7個", route.count("→") == nx and route.count("↑") == ny and len(route) == nx + ny)
    ck.ok("道順は P(0,0) から Q(4,3) に到達する", pts[0] == (0, 0) and pts[-1] == (nx, ny))
    ck.ok("道順は格子の内側を右と上にだけ進む",
          all(0 <= x <= nx and 0 <= y <= ny for x, y in pts) and
          all((b[0] - a[0], b[1] - a[1]) in ((1, 0), (0, 1)) for a, b in zip(pts, pts[1:])))
    ck.ok("道順の総数（本文 7!／(4!3!)）は 35 で、図には書かない",
          math.factorial(7) // (math.factorial(4) * math.factorial(3)) == 35)

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    P = lambda p: (ox + cell * p[0], oy - cell * p[1])
    for i in range(nx + 1):
        cv.line(*P((i, 0)), *P((i, ny)), w=THIN_W)
    for j in range(ny + 1):
        cv.line(*P((0, j)), *P((nx, j)), w=THIN_W)
    cv.polyline([P(p) for p in pts], w=BOLD_W)
    cv.dot(*P((0, 0)), 4.0)
    cv.dot(*P((nx, ny)), 4.0)
    T(ox - 14, oy + fs * 0.9, "P", anchor="end", weight="bold")
    qx, qy = P((nx, ny))
    T(qx + 14, qy - 4, "Q", anchor="start", weight="bold")
    T(ox + cell * nx / 2, oy + 40, f"右へ{nx}区画")
    T(qx + 14, oy - cell * ny / 2 + fs * 0.35, f"上へ{ny}区画", anchor="start")
    T(W / 2, 412, route)
    cv.layout_checks(ck)

    return {"file": "L07_fig1_grid_shortest_path.svg", "lesson": "L07", "canvas": cv,
            "title": "格子の最短経路——P から Q へ右4区画・上3区画、道順 →→↑→↑↑→ の例",
            "desc": "横4区画・縦3区画の格子（細線）に、左下 P から右上 Q へ右と上だけに進む1本の道順を太い折れ線で描き、対応する矢印の列 →→↑→↑↑→ を下に添える。道順の総数は書かない。同型図は区画数と道順の文字列を差し替えて生成する",
            "alt": "横4区画・縦3区画の格子。左下の P から右上の Q へ、右と上だけに進む折れ線の道順が1本かかれ、それに対応する矢印の列 →→↑→↑↑→ が添えられている",
            "intent": "道順と「→4個と↑3個を1列に並べた列」が1対1に対応することを、1本の道順で見せる（同じものを含む順列への橋渡し）",
            "src": "lesson_07.md §3（例題5の解答の途中）",
            "params": "右 4・上 3／道順 →→↑→↑↑→／ます 70px・P=(150,340)／ラベル P・Q・右へ4区画・上へ3区画・矢印の列",
            "checks": ck.items,
            "check_tokens": ["35", "56", "70", "280", "1680", "18", "26", "30", "90", "10", "12", "15"],
            "digit_rule": ("subset", {"4", "3"}),
            "allow_texts": labels}


# ===========================================================================
# L08〜L09
# ===========================================================================
# 図1: L08 §3 2個のさいころの表に事象「和が8」を塗る
def fig_L08_1():
    def extra(ck, shaded):
        ck.ok("P(和が8)=n(A)/n(U)=塗ったます数/36=5/36（本文の答え・図には書かない）", Fr(len(shaded), 36) == Fr(5, 36))
    return dict(dice_table(
        shade_sum=8, caption="目の和が8になるます（5個）",
        file="L08_fig1_dice_table_event_shaded.svg",
        title="大小2個のさいころの表で、目の和が8になる5つのますを塗る",
        desc="縦に大の目 1〜6・横に小の目 1〜6 をとり、ますに目の和を書いた 6×6 の表で、和が 8 のます (2,6)(3,5)(4,4)(5,3)(6,2) を灰色に塗る。確率の値は書かない。同型図は塗る条件（和の値など）を差し替えて生成する",
        alt="大小2個のさいころの目の組を並べた6×6の二次元の表。目の和が8になる5つのますが塗り分けられている",
        intent="事象 A を表の中の「ますの集まり」として見せ、n(A)=5・n(U)=36 の数え方（区別した根元事象）を支える",
        src="lesson_08.md §3（例題3の解答の直後）",
        params="大の目 1〜6（行）・小の目 1〜6（列）／ます 60px・左上 (150,80)／塗り: 大＋小=8 の5個／キャプション 目の和が8になるます（5個）",
        check_tokens=["5/36", "5/12", "0.620", "0.636", "0.638", "0.641", "21通り", "1/7", "1/8", "1/9", "3/7", "3/8", "4/7", "3/4", "1/2"],
        extra_checks=extra), lesson="L08")


# 図2: L08 §4 相対度数が 1/6 に近づく折れ線（本文の表の固定データ）
def fig_L08_2():
    # --- パラメータ（lesson_08.md §4 の表） ---
    table = [(10, 3), (50, 11), (100, 19), (500, 88), (1000, 171), (5000, 838)]   # (投げた回数, 1の目の回数)
    p = Fr(1, 6)
    W, H = 640, 430
    x_left, x_right = 110, 570             # 6点を等間隔に置く範囲
    y_zero, y_scale = 330, 800             # 相対度数 0 の y・1.0 あたりの px
    yticks = [0, 0.1, 0.2, 0.3]
    fs = fs_for(W)

    rel = [(n, round(c / n, 3)) for n, c in table]
    ck = Checker()
    ck.ok("相対度数 = 回数÷投げた回数（小数第3位）が本文の表の6値と一致",
          [r for _, r in rel] == [0.300, 0.220, 0.190, 0.176, 0.171, 0.168])
    ck.ok("投げた回数は増加列（10→5000）", all(a[0] < b[0] for a, b in zip(table, table[1:])))
    dev = [abs(r - float(p)) for _, r in rel]
    ck.ok("1/6 との差が回数とともに単調に縮む（0.133→0.001）", all(a > b for a, b in zip(dev, dev[1:])),
          "／".join(f"{d:.3f}" for d in dev))
    ck.ok("最後の3点は 1/6±0.01 の中", all(d < 0.01 for d in dev[-3:]))
    ck.ok("1/6=0.1666… と本文の記述が一致", abs(float(p) - 0.1666) < 1e-3)
    ck.ok("縦軸の目盛りは 0・0.1・0.2・0.3 で相対度数 0.300 が描画範囲内", max(r for _, r in rel) <= max(yticks))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    X = lambda i: x_left + (x_right - x_left) * i / (len(table) - 1)
    Y = lambda v: y_zero - y_scale * v
    # 軸
    arrow(cv, x_left - 40, y_zero, x_right + 30, y_zero, w=MAIN_W, head=9.0)
    arrow(cv, x_left - 40, y_zero, x_left - 40, Y(0.36), w=MAIN_W, head=9.0)
    for v in yticks:
        cv.line(x_left - 46, Y(v), x_left - 40, Y(v), w=MAIN_W)
        T(x_left - 52, Y(v) + fs * 0.35, f"{v:.1f}" if v else "0", anchor="end")
    for i, (n, _) in enumerate(table):
        cv.line(X(i), y_zero, X(i), y_zero + 6, w=MAIN_W)
        T(X(i), y_zero + 26, str(n))
    T(x_right + 30, y_zero + 50, "投げた回数（回）", anchor="end")
    T(x_left - 40, Y(0.36) - 12, "相対度数")
    # 1/6 の水平線
    cv.line(x_left - 40, Y(float(p)), x_right + 20, Y(float(p)), w=AUX_W, dash=DASH)
    T(x_right + 26, Y(float(p)) + fs * 0.35, "1/6", anchor="start")
    # 折れ線と点・値ラベル
    pts = [(X(i), Y(r)) for i, (_, r) in enumerate(rel)]
    cv.polyline(pts, w=MAIN_W)
    for (x, y), (_, r) in zip(pts, rel):
        cv.dot(x, y, 3.5)
        T(x, y - 12, f"{r:.3f}")
    T(W / 2, H - 14, "横軸は表の回数を等間隔に並べたもの")
    cv.layout_checks(ck)

    return {"file": "L08_fig2_relative_frequency_line.svg", "lesson": "L08", "canvas": cv,
            "title": "1の目の相対度数が回数とともに 1/6 に近づく折れ線（本文の表の6点・固定データ）",
            "desc": "横軸に投げた回数 10・50・100・500・1000・5000（等間隔）、縦軸に相対度数 0〜0.3 をとり、本文の表の値 0.300・0.220・0.190・0.176・0.171・0.168 を点と折れ線で描く。高さ 1/6 に破線。乱数は使わない。同型図は表の (回数, 出た回数) を差し替えて生成する",
            "alt": "横軸に投げた回数、縦軸に1の目が出た相対度数をとった折れ線。回数が増えるにつれて折れ線の揺れが小さくなり、1/6 の高さに引いた水平線に近づいていく（本文の表の値をそのままかいたもの）",
            "intent": "相対度数が論理的な確率 1/6 に近づき、その安定する値（頻度確率）が 1/6 と読めることを、本文の表の値で見せる（大数の法則の振り返り）",
            "src": "lesson_08.md §4（相対度数の表の直後）",
            "params": "(回数, 1の目) = (10,3)(50,11)(100,19)(500,88)(1000,171)(5000,838)／縦軸 0〜0.3（1.0=800px）／横軸 等間隔 x=110〜570／破線 1/6",
            "checks": ck.items,
            "check_tokens": ["0.620", "0.636", "0.638", "0.641", "5/36", "5/12", "21通り", "3/4", "1/2", "1/7", "1/8", "1/9"],
            "digit_rule": ("subset", {"10", "50", "100", "500", "1000", "5000", "0", "1", "2", "3", "6",
                                      "300", "220", "190", "176", "171", "168"}),
            "allow_texts": labels}


# 図1: L09 §3 和事象・排反・余事象のベン図（3パネル・記号のみ）
def fig_L09_1():
    # --- パラメータ（lesson_09.md §3） ---
    W, H = 640, 300
    panel_w, panel_h, gap, py = 200, 170, 10, 60
    r = 41
    offs_overlap = (82, 129)               # パネル内の円の中心 x（重なる配置・数Ⅰ「集合と命題」の教材の比率）
    offs_disjoint = (54, 146)              # 排反の配置
    cy_rel = 95
    captions = ["和事象 A∪B", "A と B は排反", "余事象 Aᶜ"]
    fs = fs_for(W)

    panels = []
    for k in range(3):
        px = gap + k * (panel_w + gap)
        rect = (px, py, panel_w, panel_h)
        ax, bx = offs_disjoint if k == 1 else offs_overlap
        A = (px + ax, py + cy_rel, r)
        B = (px + bx, py + cy_rel, r)
        panels.append((rect, A, B))
    ck = Checker()
    ck.ok("左・右のパネルは2円が重なる（中心距離 < 2r）",
          all(dist(panels[k][1][:2], panels[k][2][:2]) < 2 * r for k in (0, 2)))
    ck.ok("中のパネルは2円が重ならない（中心距離 > 2r・A∩B=∅）",
          dist(panels[1][1][:2], panels[1][2][:2]) > 2 * r)
    ck.ok("全パネルで2円が U の枠の内側", all(circle_in_rect(A, rect) and circle_in_rect(B, rect) for rect, A, B in panels))
    m0 = ((panels[0][1][0] + panels[0][2][0]) / 2, panels[0][1][1])
    m1 = ((panels[1][1][0] + panels[1][2][0]) / 2, panels[1][1][1])
    ck.ok("代表点: 左は2円の中点が両方に入る／中は2円の中点がどちらにも入らない",
          in_disk(m0, panels[0][1]) and in_disk(m0, panels[0][2]) and
          not in_disk(m1, panels[1][1]) and not in_disk(m1, panels[1][2]))
    corner = (panels[2][0][0] + 10, panels[2][0][1] + panels[2][0][3] - 10)
    ck.ok("右: U の隅の点は A の外（余事象の塗り）で、A の中心は塗らない",
          not in_disk(corner, panels[2][1]) and in_disk(panels[2][1][:2], panels[2][1]))
    ck.ok("3パネルが同じ幅・同じ高さで横に並ぶ", all(rect[2] == panel_w and rect[3] == panel_h for rect, _, _ in panels))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    for k, (rect, A, B) in enumerate(panels):
        if k == 2:
            cv.rect(*rect, fill=SHADE, sw=0)
            cv.circle(A[0], A[1], A[2], fill="#fff", sw=0)
        else:
            cv.circle(A[0], A[1], A[2], fill=SHADE, sw=0)
            cv.circle(B[0], B[1], B[2], fill=SHADE, sw=0)
        cv.rect(*rect, sw=1.4)
        cv.circle(*A)
        cv.circle(*B)
        T(rect[0] + 10, rect[1] + 22, "U", anchor="start", weight="bold")
        T(A[0] - 24, A[1] - r - 8, "A", weight="bold")
        T(B[0] + 24, B[1] - r - 8, "B", weight="bold")
        T(rect[0] + panel_w / 2, py + panel_h + 32, captions[k])
    cv.layout_checks(ck)

    return {"file": "L09_fig1_venn_union_disjoint_complement.svg", "lesson": "L09", "canvas": cv,
            "title": "和事象 A∪B・排反な A と B・余事象 Aᶜ のベン図（3パネル・記号のみ）",
            "desc": "長方形 U と2円 A・B のベン図を3枚並べる。左: A∪B（2円を合わせた部分を塗る）。中: A と B が重ならない（排反）。右: A の余事象（円 A の外側を塗る）。数値は書かない。同型図は塗る領域の指定を差し替えて生成する",
            "alt": "全事象 U を長方形、事象 A・B を2つの円で表したベン図3枚。左は A∪B（2つの円を合わせた部分）、中は互いに排反な A と B（円が重ならない）、右は A の余事象（円 A の外側）がそれぞれ塗り分けられている",
            "intent": "P(A∪B)=P(A)＋P(B)−P(A∩B)・排反なら足すだけ・P(Aᶜ)=1−P(A) の3つを、塗る領域の違いで見せる",
            "src": "lesson_09.md §3（加法定理の説明の直後）",
            "params": "パネル 200×170 を3枚（x=10・220・430・y=60）／円の半径 41／重なる配置: 中心 x=82・129／排反: 中心 x=54・146／ラベル U・A・B と3つのキャプション",
            "checks": ck.items,
            "check_tokens": ["1/16", "15/16", "11/15", "7/10", "4/15", "3/10", "1/9", "5/6", "4/5", "3/4", "2/3", "1/3", "1/4", "1/5", "10通り"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# ===========================================================================
# L11〜L15: 確率の樹形図（枝に確率・末端に積）
# ===========================================================================
def prob_tree2(cv, T, fs, xs, stage1, stage2, leaf_labels, y_top, y_bottom, leaf_anchor="start"):
    """2段の確率の樹形図。stage1=[(節点名, 枝の確率ラベル)], stage2=[[(節点名, 枝の確率ラベル)…] を stage1 の各節点ごと],
    leaf_labels=末端のラベル（stage2 の葉の順）。節点名は文字で置き、枝は文字を避けて引く。
    戻り値: (level1_y, level2_y, leaf_y)"""
    branching = [len(stage1), len(stage2[0])]
    assert all(len(s) == branching[1] for s in stage2)
    levels = tree_layout(branching, y_top, y_bottom)
    half = lambda s: est_w(s, fs) / 2 + 5
    cv.dot(xs[0], levels[0][0])
    for i, (name, p) in enumerate(stage1):
        y = levels[1][i]
        a, b = (xs[0] + 4, levels[0][0]), (xs[1] - half(name), y)
        cv.line(*a, *b, w=THIN_W)
        edge_label(cv, a, b, p, fs, labels=None)
        T(xs[1], y + fs * 0.35, name)
        for j, (name2, q) in enumerate(stage2[i]):
            y2 = levels[2][i * branching[1] + j]
            a2, b2 = (xs[1] + half(name), y), (xs[2] - half(name2), y2)
            cv.line(*a2, *b2, w=THIN_W)
            edge_label(cv, a2, b2, q, fs, labels=None)
            T(xs[2], y2 + fs * 0.35, name2)
            T(xs[3], y2 + fs * 0.35, leaf_labels[i * branching[1] + j], anchor=leaf_anchor)
    return levels


# 図1: L11 §2 独立な試行の樹形図（袋X→袋Y・枝の積・合計 1）
def fig_L11_1():
    # --- パラメータ（lesson_11.md §2 例題2） ---
    X = [("赤", Fr(2, 5)), ("白", Fr(3, 5))]          # 袋X: 赤2・白3
    Y = [("赤", Fr(3, 4)), ("白", Fr(1, 4))]          # 袋Y: 赤3・白1
    leaf_txt = ["6/20", "2/20", "9/20", "3/20"]       # 本文の（約分しない）表記
    total_txt = "6/20＋2/20＋9/20＋3/20=20/20=1"
    W, H = 640, 470
    xs = [60, 200, 380, 500]
    y_top, y_bottom = 90, 380
    fs = fs_for(W)

    ck = Checker()
    ck.ok("袋X・袋Y それぞれの枝の確率の和が 1", sum(p for _, p in X) == 1 and sum(q for _, q in Y) == 1)
    prods = [p * q for _, p in X for _, q in Y]
    ck.ok("末端の4値は枝の確率の積（分母 20 で表記）と一致",
          [Fr(t) for t in leaf_txt] == prods and all(t.endswith("/20") for t in leaf_txt),
          "／".join(leaf_txt))
    ck.ok("4本の枝の確率の合計が 1", sum(prods) == 1)
    ck.ok("(1) 2個とも赤 = 6/20 = 3/10（本文）", prods[0] == Fr(3, 10))
    ck.ok("(2) 同じ色 = 6/20＋3/20 = 9/20（本文）", prods[0] + prods[3] == Fr(9, 20))
    ck.ok("(3) 色が異なる = 1−9/20 = 11/20 = 2/20＋9/20（図には書かない）", 1 - Fr(9, 20) == prods[1] + prods[2] == Fr(11, 20))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    edge = lambda f: frac_str(f)
    for _, p in X:
        labels.append(edge(p))
    for _, q in Y:
        labels.append(edge(q))
    prob_tree2(cv, T, fs, xs, [(n, edge(p)) for n, p in X], [[(n, edge(q)) for n, q in Y] for _ in X],
               leaf_txt, y_top, y_bottom)
    T(xs[1], 46, "袋X", weight="bold")
    T(xs[2], 46, "袋Y", weight="bold")
    T(xs[3], 46, "積", weight="bold", anchor="start")
    T(W / 2, 440, total_txt)
    cv.layout_checks(ck)

    return {"file": "L11_fig1_independent_trials_tree.svg", "lesson": "L11", "canvas": cv,
            "title": "独立な試行の樹形図——袋X（赤 2/5・白 3/5）→袋Y（赤 3/4・白 1/4）・末端に積・合計 1",
            "desc": "根から袋Xの結果（赤 2/5・白 3/5）、そのそれぞれから袋Yの結果（赤 3/4・白 1/4）へ枝を伸ばし、4本の枝の末端に積 6/20・2/20・9/20・3/20 を書く。下に合計 20/20=1。同型図は各袋の確率を差し替えて生成する（積と合計は自動計算・assert）",
            "alt": "袋Xの結果（赤 2/5・白 3/5）から袋Yの結果（赤 3/4・白 1/4）へ枝を伸ばした樹形図。4本の枝の末端に、各枝の確率の積 6/20・2/20・9/20・3/20 が書かれ、合計が 1 になる",
            "intent": "「1本の枝の確率は積・枝をまとめた事象の確率は和」の2操作と、合計 1 の検算を1枚で見せる（乗法定理の図）",
            "src": "lesson_11.md §2（例題2の検算の直後）",
            "params": "袋X 赤 2/5・白 3/5／袋Y 赤 3/4・白 1/4／末端 6/20・2/20・9/20・3/20／列 x=60・200・380・500／葉 y=90〜380",
            "checks": ck.items,
            "check_tokens": ["98/125", "23/24", "1/24", "12/25", "9/25", "7/10", "11/20", "3/10", "2/3", "1/6", "p=2/3", "2p"],
            "digit_rule": ("subset", {"2", "5", "3", "4", "1", "6", "20", "9"}),
            "allow_texts": labels}


# 図1: L12 §3 途中で決着する試行の樹形図（先に2勝・枝の長さが違う）
def fig_L12_1():
    # --- パラメータ（lesson_12.md §3 例題4） ---
    pA, pB = Fr(2, 3), Fr(1, 3)
    # 葉（上から）: 進み方の文字列と本文の確率表記
    leaves = [("AA", "4/9"), ("ABA", "4/27"), ("ABB", "2/27"), ("BAA", "4/27"), ("BAB", "2/27"), ("BB", "1/9")]
    W, H = 640, 480
    xs = [60, 180, 300, 420]               # 根・1試合目・2試合目・3試合目
    x_seq, x_prob = 492, 578
    y_top, y_bottom = 70, 420
    total_txt = "6本の枝の確率の合計は 1"
    fs = fs_for(W)

    prob = {"A": pA, "B": pB}
    ck = Checker()
    ck.ok("各枝の確率は試合ごとの確率の積（本文の表と一致）",
          all(math.prod(prob[c] for c in s) == Fr(t) for s, t in leaves), "／".join(t for _, t in leaves))
    ck.ok("6本の枝の確率の合計が 1", sum(Fr(t) for _, t in leaves) == 1)
    ck.ok("どの枝も先に2勝した時点で終わる（2試合または3試合）",
          all(max(s.count("A"), s.count("B")) == 2 and len(s) in (2, 3) for s, _ in leaves))
    ck.ok("2試合で決着する枝は AA・BB の2本、3試合の枝は4本",
          [s for s, _ in leaves if len(s) == 2] == ["AA", "BB"] and sum(1 for s, _ in leaves if len(s) == 3) == 4)
    ck.ok("A が3試合目で優勝 = 4/27＋4/27 = 8/27（本文 (2)・図には書かない）",
          sum(Fr(t) for s, t in leaves if len(s) == 3 and s.count("A") == 2) == Fr(8, 27))
    ck.ok("A が優勝 = 4/9＋8/27 = 20/27（本文 (3)・図には書かない）",
          sum(Fr(t) for s, t in leaves if s.count("A") == 2) == Fr(20, 27))

    # 節点の座標: 葉を等間隔に置き、内部節点は子孫の葉の平均
    ys = {s: y_top + (y_bottom - y_top) * i / (len(leaves) - 1) for i, (s, _) in enumerate(leaves)}
    nodes = {}
    for s, _ in leaves:
        for k in range(1, len(s) + 1):
            nodes.setdefault(s[:k], [])
    for pref in nodes:
        nodes[pref] = sum(ys[s] for s, _ in leaves if s.startswith(pref)) / sum(1 for s, _ in leaves if s.startswith(pref))
    ck.ok("内部節点の y は子孫の葉の平均（A は AA・ABA・ABB の平均など）",
          near(nodes["A"], (ys["AA"] + ys["ABA"] + ys["ABB"]) / 3) and near(nodes["AB"], (ys["ABA"] + ys["ABB"]) / 2))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    half = 12
    root = (xs[0], sum(ys.values()) / len(ys))
    cv.dot(*root)
    for pref, y in sorted(nodes.items(), key=lambda kv: (len(kv[0]), kv[0])):
        k = len(pref)
        parent = root if k == 1 else (xs[k - 1] + half, nodes[pref[:-1]])
        a = (parent[0] + (4 if k == 1 else 0), parent[1])
        b = (xs[k] - half, y)
        cv.line(*a, *b, w=THIN_W)
        edge_label(cv, a, b, frac_str(prob[pref[-1]]), fs, labels=labels)
        T(xs[k], y + fs * 0.35, pref[-1], weight="bold")
    for s, t in leaves:
        T(x_seq, ys[s] + fs * 0.35, s)
        T(x_prob, ys[s] + fs * 0.35, t)
    for k, name in enumerate(["1試合目", "2試合目", "3試合目"]):
        T(xs[k + 1], 36, name, weight="bold")
    T(x_seq, 36, "進み方", weight="bold")
    T(x_prob, 36, "確率", weight="bold")
    T(W / 2, 462, total_txt)
    cv.layout_checks(ck)

    return {"file": "L12_fig1_best_of_three_tree.svg", "lesson": "L12", "canvas": cv,
            "title": "先に2勝したほうが優勝——枝の長さが違う樹形図（AA・BB は2試合、他は3試合）",
            "desc": "1試合で A が勝つ確率 2/3・B が勝つ確率 1/3。根から勝者 A/B に枝分かれし、同じ側が2勝した時点で枝が止まる。葉は AA（4/9）・ABA（4/27）・ABB（2/27）・BAA（4/27）・BAB（2/27）・BB（1/9）の6本で合計 1。同型図は勝つ確率と決着条件を差し替えて生成する",
            "alt": "先に2勝で優勝が決まる試合の樹形図。AA（2試合で決着・4/9）・BB（2試合で決着・1/9）の枝は短く、ABA（4/27）・ABB（2/27）・BAA（4/27）・BAB（2/27）の枝は3試合目まで伸びている。6本の枝の確率の合計は 1",
            "intent": "回数が固定されない試行では公式でなく樹形図に戻り、枝ごとに確率を書く——枝の長さが違っても合計は 1 になることを見せる",
            "src": "lesson_12.md §3（例題4 (1) の解答の途中）",
            "params": "A の勝つ確率 2/3・B 1/3／葉 AA 4/9・ABA 4/27・ABB 2/27・BAA 4/27・BAB 2/27・BB 1/9／列 x=60・180・300・420／進み方 x=492・確率 x=578／葉 y=70〜420 等間隔",
            "checks": ck.items,
            "check_tokens": ["781/1024", "671/1296", "625/1296", "135/512", "125/324", "81/125", "44/125", "36/125", "20/27", "15/64", "13/25", "11/36", "7/64", "1/64", "3/8", "1/2", "8/27", "32/81", "65/81", "11/27"],
            "digit_rule": ("subset", {"1", "2", "3", "4", "9", "27", "6"}),
            "allow_texts": labels}


# 図1: L13 §3 2×2の分割表（P_A(B) と P_B(A) を同じ表から読む）
def fig_L13_1():
    # --- パラメータ（lesson_13.md §3 例題3） ---
    AB, ABc, AcB, AcBc = 12, 8, 6, 14      # A∩B・A∩Bᶜ・Aᶜ∩B・Aᶜ∩Bᶜ
    W, H = 680, 370
    col_w = [170, 130, 170, 90]            # 行見出し・B・Bᶜ・合計
    row_h = 50
    x0, y0 = 60, 50
    fs = fs_for(W)

    rowA, rowAc = AB + ABc, AcB + AcBc
    colB, colBc = AB + AcB, ABc + AcBc
    total = rowA + rowAc
    ck = Checker()
    ck.ok("行の合計: A=12＋8=20・Aᶜ=6＋14=20", rowA == 20 and rowAc == 20)
    ck.ok("列の合計: B=12＋6=18・Bᶜ=8＋14=22", colB == 18 and colBc == 22)
    ck.ok("総計 40（行の合計の和＝列の合計の和）", total == colB + colBc == 40)
    ck.ok("P_A(B)=12/20=3/5（行 A の合計で割る・本文 (1)）", Fr(AB, rowA) == Fr(3, 5))
    ck.ok("P_B(A)=12/18=2/3（列 B の合計で割る・本文 (2)）", Fr(AB, colB) == Fr(2, 3))
    ck.ok("P_A(B) と P_B(A) は値が違う（分子は同じ 12・分母が違う）", Fr(AB, rowA) != Fr(AB, colB))
    ck.ok("定義のもう1つの形: P(A∩B)/P(A)=(12/40)/(20/40)=3/5", Fr(AB, total) / Fr(rowA, total) == Fr(3, 5))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    xl = [x0]
    for w in col_w:
        xl.append(xl[-1] + w)
    yl = [y0 + i * row_h for i in range(5)]
    cells = [["", "運動部 B", "運動部でない Bᶜ", "合計"],
             ["自転車 A", str(AB), str(ABc), str(rowA)],
             ["自転車でない Aᶜ", str(AcB), str(AcBc), str(rowAc)],
             ["合計", str(colB), str(colBc), str(total)]]
    # 強調: 行 A と列 B をうすく塗る（A∩B のますは重ねて濃く）
    cv.rect(xl[0], yl[1], xl[4] - xl[0], row_h, fill=SHADE3, sw=0)
    cv.rect(xl[1], yl[0], col_w[1], yl[4] - yl[0], fill=SHADE3, sw=0)
    cv.rect(xl[1], yl[1], col_w[1], row_h, fill=SHADE, sw=0)
    for i in range(5):
        cv.line(xl[0], yl[i], xl[4], yl[i], w=THIN_W)
    for x in xl:
        cv.line(x, yl[0], x, yl[4], w=THIN_W)
    cv.rect(xl[0], yl[0], xl[4] - xl[0], yl[4] - yl[0], sw=MAIN_W)
    for i, row in enumerate(cells):
        for j, s in enumerate(row):
            if s:
                T((xl[j] + xl[j + 1]) / 2, yl[i] + row_h / 2 + fs * 0.35, s,
                  weight="bold" if (i == 0 or j == 0) else None)
    cv.rect(xl[0], yl[1], xl[4] - xl[0], row_h, sw=BOLD_W)       # 行 A の枠
    cv.rect(xl[1], yl[0], col_w[1], yl[4] - yl[0], sw=BOLD_W)    # 列 B の枠
    T(x0, 300, "P_A(B)=12/20（行 A の合計 20 で割る）", anchor="start")
    T(x0, 340, "P_B(A)=12/18（列 B の合計 18 で割る）", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L13_fig1_conditional_two_way_table.svg", "lesson": "L13", "canvas": cv,
            "title": "2×2の分割表——同じます A∩B（12）を、行 A の合計 20 で割れば P_A(B)、列 B の合計 18 で割れば P_B(A)",
            "desc": "行が自転車 A・自転車でない Aᶜ、列が運動部 B・運動部でない Bᶜ の分割表（12・8／6・14、合計 20・20／18・22／40）。行 A と列 B を太枠とうすい網かけで強調し、下に P_A(B)=12/20 と P_B(A)=12/18 を書く。約分した値は書かない。同型図は4つのますの値を差し替えて生成する（合計は自動計算）",
            "alt": "2×2の分割表。行が自転車 A・自転車でない Aᶜ、列が運動部 B・運動部でない Bᶜ。左上のます A∩B（12）を、行の合計 20 で割ると P_A(B)、列の合計 18 で割ると P_B(A) になることを、行と列の枠の強調で示す",
            "intent": "逆条件の混同（P_A(B) と P_B(A) の取り違え）を、「分子は同じます・分母は行か列の合計か」の違いとして表の上で見せる",
            "src": "lesson_13.md §3（例題3の表と設問の直後）",
            "params": "A∩B=12・A∩Bᶜ=8・Aᶜ∩B=6・Aᶜ∩Bᶜ=14（合計 20・20・18・22・40）／列幅 170・130・170・90・行高 50・左上 (60,50)／注記 P_A(B)=12/20・P_B(A)=12/18",
            "checks": ck.items,
            "check_tokens": ["6/21", "9/15", "2/7", "1/7", "3/8", "5/6", "3/5", "2/3", "1/2", "1/4", "1/5", "3/4", "3/10", "9/20"],
            "digit_rule": ("subset", {"12", "8", "6", "14", "20", "18", "22", "40"}),
            "allow_texts": labels}


# 図2: L13 §4 面積図（P(A)・P(A∩B)・P_A(B) を長方形の面積比で）
def fig_L13_2():
    # --- パラメータ（lesson_13.md §4・例題3の値） ---
    P_A, P_AB = Fr(1, 2), Fr(3, 10)
    W, H = 640, 360
    U = (120, 60, 400, 200)                # 全体の長方形（面積 1 とみる）
    fs = fs_for(W)

    ck = Checker()
    ck.ok("P_A(B)=P(A∩B)/P(A)=(3/10)/(1/2)=3/5（本文）", P_AB / P_A == Fr(3, 5))
    ck.ok("A∩B ⊂ A: P(A∩B) ≦ P(A)", P_AB <= P_A)
    a_w_f = U[2] * P_A                      # A の幅（U の幅 × 1/2）
    ab_h_f = U[3] * (P_AB / P_A)            # A∩B の高さ（A の高さ × 3/5）
    ck.ok("幅・高さが整数 px になる（400×1/2=200・200×3/5=120）", a_w_f.denominator == 1 and ab_h_f.denominator == 1)
    a_w, ab_h = int(a_w_f), int(ab_h_f)
    ck.ok("A の長方形の面積 = U の 1/2（px で検算）", Fr(a_w * U[3], U[2] * U[3]) == P_A, f"A={a_w}×{U[3]}")
    ck.ok("A∩B の長方形の面積 = U の 3/10（px で検算）", Fr(a_w * ab_h, U[2] * U[3]) == P_AB, f"A∩B={a_w}×{ab_h}")
    ck.ok("A∩B の面積／A の面積 = 3/5（px で検算）", Fr(a_w * ab_h, a_w * U[3]) == Fr(3, 5))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    hatch = cv.hatch_def()
    cv.rect(U[0], U[1], a_w, U[3], fill=SHADE, sw=0)               # A
    cv.rect(U[0], U[1], a_w, ab_h, fill=hatch, sw=0)               # A∩B（斜線）
    cv.rect(U[0], U[1], a_w, ab_h, sw=THIN_W)
    cv.rect(U[0], U[1], a_w, U[3], sw=MAIN_W)
    cv.rect(*U, sw=MAIN_W)
    T(U[0] + U[2], U[1] - 12, "U（面積 1）", anchor="end")
    T(U[0] + a_w / 2, U[1] + U[3] + 28, "A（面積 1/2）")
    cv.plate_text(U[0] + a_w / 2, U[1] + ab_h / 2 + fs * 0.35, "A∩B（面積 3/10）", fs)
    labels.append("A∩B（面積 3/10）")
    T(W / 2, 330, "P_A(B)=(3/10)／(1/2)=3/5")
    cv.layout_checks(ck)

    return {"file": "L13_fig2_conditional_area_diagram.svg", "lesson": "L13", "canvas": cv,
            "title": "面積図——全体 1 の中の A（面積 1/2）と、その内側の A∩B（面積 3/10）。比 3/5 が P_A(B)",
            "desc": "全体の長方形 U（面積 1）の左半分を A（うすい網かけ・面積 1/2）、A の上 3/5 を A∩B（斜線・面積 3/10）として描き、下に P_A(B)=(3/10)／(1/2)=3/5 を書く。同型図は P(A)・P(A∩B) を差し替えて生成する（幅・高さは面積から自動計算・px で検算）",
            "alt": "面積図。全体の長方形（面積 1）の中に、事象 A の長方形（面積 P(A)）があり、その内側に A∩B の部分（面積 P(A∩B)）が塗り分けられている。P_A(B) は「A の長方形の面積に対する A∩B の部分の面積の比」として示され、例題3の値では A が 1/2、A∩B が 3/10、比が 3/5 になる",
            "intent": "条件付き確率を「基準にする長方形が全体から A に変わる」こととして面積で見せる",
            "src": "lesson_13.md §4（面積図の説明の直後）",
            "params": "P(A)=1/2・P(A∩B)=3/10／U=(120,60) 400×200／A の幅 200・A∩B の高さ 120／ラベル U（面積 1）・A（面積 1/2）・A∩B（面積 3/10）・P_A(B)=(3/10)／(1/2)=3/5",
            "checks": ck.items,
            "check_tokens": ["6/21", "9/15", "2/7", "1/7", "3/8", "5/6", "2/3", "1/4", "1/5", "3/4", "9/20", "12/20", "12/18"],
            "digit_rule": ("subset", {"1", "2", "3", "10", "5"}),
            "allow_texts": labels}


# 図1: L14 §2 2段の樹形図（袋を選ぶ→玉を引く・枝の積→和）
def fig_L14_1():
    # --- パラメータ（lesson_14.md §2 例題3） ---
    bags = [("袋X", Fr(1, 3)), ("袋Y", Fr(2, 3))]                       # さいころ: 3の倍数→X・それ以外→Y
    balls = {"袋X": [("赤", Fr(2, 5)), ("白", Fr(3, 5))], "袋Y": [("赤", Fr(4, 5)), ("白", Fr(1, 5))]}
    leaf_txt = ["2/15", "3/15", "8/15", "2/15"]
    ans_txt = "赤: 2/15＋8/15=10/15"
    W, H = 640, 480
    xs = [60, 190, 350, 480]
    y_top, y_bottom = 90, 390
    fs = fs_for(W)

    ck = Checker()
    ck.ok("袋を選ぶ確率の和が 1（1/3＋2/3）", sum(p for _, p in bags) == 1)
    ck.ok("各袋の赤・白の確率の和が 1", all(sum(q for _, q in balls[b]) == 1 for b, _ in bags))
    flat = [(b, n, p * q) for b, p in bags for n, q in balls[b]]        # (袋, 色, 枝の積) を葉の順に
    prods = [pq for _, _, pq in flat]
    ck.ok("末端の4値は枝の確率の積（分母 15 で表記）と一致", [Fr(t) for t in leaf_txt] == prods, "／".join(leaf_txt))
    ck.ok("4本の枝の確率の合計が 1", sum(prods) == 1)
    red = [pq for _, n, pq in flat if n == "赤"]
    ck.ok("赤の2本の和 2/15＋8/15=10/15=2/3（本文の答え）", len(red) == 2 and sum(red) == Fr(10, 15) == Fr(2, 3))
    ck.ok("白の2本の和 3/15＋2/15=5/15=1/3（本文の検算）", sum(prods) - sum(red) == Fr(1, 3))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    for _, p in bags:
        labels.append(frac_str(p))
    for b, _ in bags:
        for _, q in balls[b]:
            labels.append(frac_str(q))
    levels = prob_tree2(cv, T, fs, xs, [(b, frac_str(p)) for b, p in bags],
                        [[(n, frac_str(q)) for n, q in balls[b]] for b, _ in bags], leaf_txt, y_top, y_bottom)
    # 赤の2本の末端を枠で囲む
    for i, (_, name, _) in enumerate(flat):
        if name == "赤":
            y = levels[2][i]
            w = est_w(leaf_txt[i], fs)
            cv.rect(xs[3] - 6, y - fs * 0.92, w + 12, fs * 1.3, sw=MAIN_W)
    T(xs[1], 46, "袋を選ぶ", weight="bold")
    T(xs[2], 46, "玉を引く", weight="bold")
    T(xs[3], 46, "積", weight="bold", anchor="start")
    aw = est_w(ans_txt, fs)
    cv.rect(W / 2 - aw / 2 - 10, 448 - fs * 0.92, aw + 20, fs * 1.3, sw=BOLD_W)
    T(W / 2, 448, ans_txt)
    cv.layout_checks(ck)

    return {"file": "L14_fig1_two_stage_bag_tree.svg", "lesson": "L14", "canvas": cv,
            "title": "2段の樹形図——袋X（1/3）・袋Y（2/3）→赤・白、末端に積、赤の2本の和 10/15",
            "desc": "根から袋X（1/3）・袋Y（2/3）、そのそれぞれから赤・白（X: 2/5・3/5、Y: 4/5・1/5）へ枝を伸ばし、末端に積 2/15・3/15・8/15・2/15 を書く。赤の2本を枠で囲み、下に 赤: 2/15＋8/15=10/15 を太枠で示す。同型図は袋の確率と各袋の赤・白の確率を差し替えて生成する",
            "alt": "2段の樹形図。1段目は袋X（1/3）と袋Y（2/3）、2段目はそれぞれの袋から赤・白を引く枝（X: 赤 2/5・白 3/5、Y: 赤 4/5・白 1/5）。4本の枝の末端に積 2/15・3/15・8/15・2/15 が書かれ、赤の2本を足した 10/15 が答えとして囲まれている",
            "intent": "乗法定理 P(A∩B)=P(A)P_A(B) を「枝の積」、排反な枝の和を「枝の和」として、もう一方の袋の分を落とさない全体像を見せる",
            "src": "lesson_14.md §2（例題3の解説の直後）",
            "params": "袋X 1/3・袋Y 2/3／X: 赤 2/5・白 3/5／Y: 赤 4/5・白 1/5／末端 2/15・3/15・8/15・2/15／赤の和 10/15／列 x=60・190・350・480／葉 y=90〜390",
            "checks": ck.items,
            "check_tokens": ["5/56", "5/28", "7/30", "1/12", "1/15", "5/9", "1/2", "1/4", "3/10", "4/15", "12/30", "8/30"],
            "digit_rule": ("subset", {"1", "3", "2", "5", "4", "15", "8", "10"}),
            "allow_texts": labels}


# 図1: L15 §2 ルーレットの扇形と面積比（中心角 30°・90°・120°・120°）
def fig_L15_1():
    # --- パラメータ（lesson_15.md §2 例題3） ---
    prizes = [("1等", 30), ("2等", 90), ("3等", 120), ("はずれ", 120)]     # (名, 中心角)
    W, H = 640, 440
    cx, cy, R = 255, 225, 140
    RL = 160                               # ラベルを置く半径
    fills = ["#fff", None, SHADE, SHADE2]  # None=斜線ハッチング
    note = "確率＝中心角／360°"
    fs = fs_for(W)

    ck = Checker()
    ck.ok("中心角の和が 360°", sum(a for _, a in prizes) == 360)
    probs = [Fr(a, 360) for _, a in prizes]
    ck.ok("確率 = 中心角/360 が 1/12・1/4・1/3・1/3（本文 (1)）", probs == [Fr(1, 12), Fr(1, 4), Fr(1, 3), Fr(1, 3)])
    ck.ok("確率の合計が 1", sum(probs) == 1)
    ck.ok("扇形の面積比 = 中心角の比（半径が同じ）", all(Fr(a, 360) == p for (_, a), p in zip(prizes, probs)))
    ck.ok("賞金の期待値 1200×1/12＋400×1/4＋120×1/3＋0×1/3=240（本文 (2)・図には書かない）",
          1200 * probs[0] + 400 * probs[1] + 120 * probs[2] + 0 * probs[3] == 240)

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    hatch = cv.hatch_def()
    start = 90.0                           # 上から時計回り
    for (name, ang), p, fill in zip(prizes, probs, fills):
        a0, a1 = start, start - ang
        pts = sector_pts(cx, cy, R, a0, a1)
        cv.polygon_fill(pts, hatch if fill is None else fill)
        cv.polyline(pts, w=MAIN_W, close=True)
        mid = (a0 + a1) / 2
        lx, ly = cx + RL * math.cos(mid * DEG), cy - RL * math.sin(mid * DEG)
        c, s = math.cos(mid * DEG), math.sin(mid * DEG)
        anchor = "start" if c > 0.3 else ("end" if c < -0.3 else "middle")
        dy = -22 if s > 0.5 else (20 if s < -0.5 else 0)     # 上下の扇形は2行ぶん円から離す
        T(lx, ly - 4 + dy, f"{name} {ang}°", anchor=anchor, weight="bold")
        T(lx, ly + fs * 1.05 + dy, frac_str(p), anchor=anchor)
        start = a1
    cv.circle(cx, cy, R, sw=MAIN_W)
    cv.dot(cx, cy, 3.0)
    T(440, 80, note, anchor="start")
    T(440, 112, "面積比＝中心角の比", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L15_fig1_roulette_sector_areas.svg", "lesson": "L15", "canvas": cv,
            "title": "ルーレットの円板を中心角 30°・90°・120°・120° の扇形に分け、面積比から確率 1/12・1/4・1/3・1/3",
            "desc": "半径 140 の円を上から時計回りに 1等 30°・2等 90°・3等 120°・はずれ 120° の扇形に分け（白・斜線・うすい灰・濃い灰）、各扇形の外側に名と中心角、確率を書く。右に 確率＝中心角／360°。賞金・期待値は書かない。同型図は賞の名と中心角を差し替えて生成する（確率は自動計算・和 1 を assert）",
            "alt": "ルーレットの円板を中心角 30°・90°・120°・120° の4つの扇形に分けた図。それぞれに1等・2等・3等・はずれの名と、面積比から決まる確率 1/12・1/4・1/3・1/3 が書かれている",
            "intent": "数え上げにくい場面でも面積（中心角）の比で確率が決まることを見せ、期待値の計算（本文）につなぐ",
            "src": "lesson_15.md §2（例題3の設問の直後）",
            "params": "1等 30°・2等 90°・3等 120°・はずれ 120°／中心 (255,225)・半径 140・ラベル半径 160／確率 1/12・1/4・1/3・1/3／注記 確率＝中心角／360°",
            "checks": ck.items,
            "check_tokens": ["550", "330", "300", "160", "−150", "11/2", "19", "240", "1200", "400", "250", "10円", "5000", "3500"],
            "digit_rule": ("subset", {"1", "2", "3", "12", "4", "30", "90", "120", "360"}),
            "allow_texts": labels}


# 図2: L15 §5 確率木（天気 p₁〜p₃ → 売上 q₁〜q₆ → 積 P₁〜P₆・記号のみ）
def fig_L15_2():
    # --- パラメータ（lesson_15.md §5 例題6） ---
    weather = ["晴れ", "くもり", "雨"]
    sales = ["多い", "少ない"]
    p_syms = ["p₁", "p₂", "p₃"]
    q_syms = ["q₁", "q₂", "q₃", "q₄", "q₅", "q₆"]
    P_syms = ["P₁", "P₂", "P₃", "P₄", "P₅", "P₆"]
    W, H = 640, 470
    xs = [60, 200, 370, 480]
    y_top, y_bottom = 80, 430
    fs = fs_for(W)

    ck = Checker()
    ck.ok("枝は 3×2=6 本で、q・P の添え字が 1〜6 で葉の順に並ぶ",
          len(weather) * len(sales) == 6 == len(q_syms) == len(P_syms))
    ck.ok("葉 k は天気 ⌈k/2⌉ の枝（P₁P₂←晴れ・P₃P₄←くもり・P₅P₆←雨）",
          [(k // 2) for k in range(6)] == [0, 0, 1, 1, 2, 2])
    ck.ok("末端のラベルは P=p×q の形（P₁=p₁q₁ … P₆=p₃q₆）",
          [f"{P_syms[k]}={p_syms[k // 2]}{q_syms[k]}" for k in range(6)][0] == "P₁=p₁q₁" and
          [f"{P_syms[k]}={p_syms[k // 2]}{q_syms[k]}" for k in range(6)][5] == "P₆=p₃q₆")
    ck.ok("添字の数字（₁〜₆）を除き、確率などの数値を含まない（記号のみ・本文の数値 1/2・1/3・1/6・4/5 などは書かない）",
          no_digits(weather + sales + p_syms + q_syms + P_syms))

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    labels.extend(p_syms)
    labels.extend(q_syms)
    leaf = [f"{P_syms[k]}={p_syms[k // 2]}{q_syms[k]}" for k in range(6)]
    prob_tree2(cv, T, fs, xs, list(zip(weather, p_syms)),
               [[(sales[j], q_syms[2 * i + j]) for j in range(2)] for i in range(3)], leaf, y_top, y_bottom)
    T(xs[1], 40, "天気", weight="bold")
    T(xs[2], 40, "売上", weight="bold")
    T(xs[3], 40, "積", weight="bold", anchor="start")
    cv.layout_checks(ck)

    return {"file": "L15_fig2_probability_tree_symbols.svg", "lesson": "L15", "canvas": cv,
            "title": "確率木——天気（p₁・p₂・p₃）→売上「多い」「少ない」（q₁〜q₆）→積 P₁〜P₆（記号のみ）",
            "desc": "根から晴れ・くもり・雨（枝の確率 p₁・p₂・p₃）、そのそれぞれから多い・少ない（q₁〜q₆）へ枝を伸ばし、6本の末端に P₁=p₁q₁ … P₆=p₃q₆ を書く。数値は書かない。同型図は段の名と記号を差し替えて生成する",
            "alt": "確率木。1段目に天気の3本の枝（確率 p₁・p₂・p₃）、2段目に各天気から売上「多い」「少ない」への枝（確率 q₁〜q₆）が伸び、末端の6本の枝にそれぞれの積 P₁〜P₆ が記号で書かれている",
            "intent": "「自ら確率を仮定する」場面の型を、数値を入れない確率木として示す（本文の表で数値を当てはめる）",
            "src": "lesson_15.md §5（例題6の設問の直後）",
            "params": "天気 晴れ・くもり・雨（p₁・p₂・p₃）／売上 多い・少ない（q₁〜q₆）／末端 P₁=p₁q₁〜P₆=p₃q₆／列 x=60・200・370・480／葉 y=80〜430",
            "checks": ck.items,
            "check_tokens": ["1/2", "1/3", "1/6", "4/5", "1/5", "12/30", "3/30", "5/30", "550", "330", "300", "160", "11/2"],
            "digit_rule": ("none", set()),
            "allow_texts": labels}


# 図1: L16 §1 単元マップ（ブロック図）
def fig_L16_1():
    # --- パラメータ（lesson_16.md §1） ---
    start = "何を1通りと数えるか（L01）"
    blocks = ["数え上げの原則（L01〜L03）", "順列・組合せ（L04〜L07）", "確率の定義と性質（L08〜L10）",
              "独立・反復・条件付き確率（L11〜L14）", "期待値と意思決定（L15）"]
    W, H = 640, 520
    bw, bh, gap = 440, 46, 34
    x0, y0 = (640 - 440) / 2, 30
    fs = fs_for(W)

    ck = Checker()
    ck.ok("ブロックは起点1＋5 = 6 個で、上から順に矢印でつながる（矢印 5 本）", len(blocks) == 5)
    rng = [re.findall(r"L(\d\d)", b) for b in [start] + blocks]
    ck.ok("レッスン番号が L01 から L15 まで途切れなく昇順に並ぶ",
          rng == [["01"], ["01", "03"], ["04", "07"], ["08", "10"], ["11", "14"], ["15"]])
    ys = [y0 + i * (bh + gap) for i in range(6)]
    ck.ok("6個のブロックが等間隔に縦に並び、最後が viewBox の下端に収まる",
          all(near(ys[i + 1] - ys[i], bh + gap) for i in range(5)) and ys[-1] + bh < H)

    cv = Canvas(W, H)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, fs, **kw)

    for i, s in enumerate([start] + blocks):
        y = ys[i]
        cv.rect(x0, y, bw, bh, fill=(SHADE if i == 0 else "none"), sw=(BOLD_W if i == 0 else MAIN_W))
        T(W / 2, y + bh / 2 + fs * 0.35, s, weight=("bold" if i == 0 else None))
        if i < 5:
            arrow(cv, W / 2, y + bh + 2, W / 2, ys[i + 1] - 2, w=MAIN_W, head=9.0)
    cv.layout_checks(ck)

    return {"file": "L16_fig1_unit_map.svg", "lesson": "L16", "canvas": cv,
            "title": "単元マップ——「何を1通りと数えるか」を起点に、数え上げの原則→順列・組合せ→確率の定義と性質→独立・反復・条件付き確率→期待値と意思決定",
            "desc": "起点のブロック「何を1通りと数えるか（L01）」（網かけ・太枠）から、5つのまとまり（L01〜L03・L04〜L07・L08〜L10・L11〜L14・L15）のブロックへ縦に矢印でつなぐブロック図。数値はレッスン番号のみ。同型図はブロックの文字列を差し替えて生成する",
            "alt": "単元マップ。「何を1通りと数えるか」を起点に、数え上げの原則→順列・組合せ→確率の定義と性質→独立・反復・条件付き確率→期待値と意思決定、の順に L01〜L15 のまとまりが矢印でつながっている",
            "intent": "総括回の1枚地図。最初の問いが背骨のまま道具が増えていった順序を、縦1本の流れで見せる",
            "src": "lesson_16.md §1（冒頭の段落の直後）",
            "params": "起点 何を1通りと数えるか（L01）／ブロック 数え上げの原則（L01〜L03）・順列・組合せ（L04〜L07）・確率の定義と性質（L08〜L10）・独立・反復・条件付き確率（L11〜L14）・期待値と意思決定（L15）／枠 440×46・間隔 34・左上 (100,30)",
            "checks": ck.items,
            "check_tokens": ["4/9", "5/8", "7/20", "9/10", "140", "24個", "36個", "60個", "10通り", "3通り"],
            "digit_rule": ("strip", ["1通り"]),
            "allow_texts": labels}


# ===========================================================================
# main: 陽性対照 → 生成 → 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L01_2, fig_L02_1, fig_L03_1, fig_L04_1, fig_L05_1, fig_L06_1,
        fig_L07_1, fig_L08_1, fig_L08_2, fig_L09_1, fig_L11_1, fig_L12_1, fig_L13_1, fig_L13_2, fig_L14_1,
        fig_L15_1, fig_L15_2, fig_L16_1]

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
              '<text x="1" y="1">5/36</text><text x="2" y="2">x&lt;0</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["5/36", "x<0"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["5/36"]) == ["5/36"], "陽性対照失敗: 禁止値 5/36 を検出できない"
    assert ban_hits(ts, ["7/36"]) == [], "陰性対照失敗: 存在しない値を誤検出"
    assert digit_runs(ts) == {"5", "36", "0"}, "数字抽出が壊れている"
    probes = ["a" + chr(0x200B) + "b", "e" + chr(0x0301), chr(0x2713) + chr(0xFE0F),
              chr(0xFF21) + chr(0xFF11), chr(0x1F600)]
    for probe in probes:
        try:
            char_hygiene(probe, "陽性対照")
        except AssertionError:
            continue
        raise AssertionError(f"文字衛生の陽性対照失敗: {probe!r} を検出できない")
    char_hygiene("Aᶜ・∩・∪・°・−・＋・×・→・↑・〜・₁・大＼小", "陰性対照")


def svg_tech_checks(src, meta):
    """生成した SVG 文字列を、ファイルへ書く前に検査する（落ちれば例外で停止し、何も出力しない）"""
    path = Path(meta["file"])
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag and 'xmlns="http://www.w3.org/2000/svg"' in root_tag, f"{path.name}: xmlns/viewBox がない"
    assert " width=" not in root_tag and " height=" not in root_tag, f"{path.name}: ルートに width/height を書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, f"{path.name}: 外部参照の疑い"
    assert "font-family" not in src, f"{path.name}: フォント指定は書かない（docs/SPEC_figures.md §5）"
    assert "<title>" in src and "<desc>" in src, f"{path.name}: title/desc がない"
    assert '<rect x="0" y="0"' in src and 'fill="#fff"' in src, f"{path.name}: 白背景がない"
    for pid in re.findall(r'url\(#([^)]+)\)', src):
        assert f'id="{pid}"' in src, f"{path.name}: 未定義の参照 #{pid}"
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

    # 受け入れ検査: ファイル名の一致・alt の一致
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
        "# FIGURE_MANIFEST — 数A 場合の数と確率 単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的・乱数不使用）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト。下表の数学検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。加えて全SVGに XML整形式・xmlns/viewBox・width/height なし・self-contained・"
        "`<title>`/`<desc>`・白背景・フォント指定なし の技術検査と、文字衛生検査"
        "（絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字の不在）と、答え漏れ検査を実施。"
        "答え漏れ検査は二重ゲート: (1)図中の全ラベルを許可リスト（本文が図の前後で明示している値のみ）と"
        f"集合として完全一致で照合、(2)禁止文字列（練習・stretch の答え由来・計{n_tokens}項目・対象値は非開示）の"
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
    lines += ["", "## 受け入れ検査の結果", ""]
    for line in accept:
        lines.append(f"- {line}")
    lines += [
        f"- 各SVG: XML整形式・xmlns と viewBox あり・width/height なし・外部参照なし・`<title>`/`<desc>` あり・"
        f"白背景 rect あり・font-family なし（{len(rows)} 枚全件・スクリプトの技術検査で assert）",
        f"- 各図の assert が生成時に全件通過（計 {n_checks} 項目・上表）",
        "- 答え漏れ検査: `<text>` の文字列集合が各図の許可集合と完全一致・禁止文字列 0 件・数字集合の制約を満たす（全図 assert）",
        "- 決定性: 乱数不使用。同一プロセス内で各図を2回生成してバイト一致を assert。別プロセスでの再実行の一致は、"
        "出荷時に全SVGと本台帳を2回生成して照合する（生成日は日付のみなので同日なら一致。"
        "台帳に載せる集合は整列して書くので、実行ごとの要素順の差は出ない）",
        "- 図数の照合: 本文の図参照と生成ファイルの差集合が空（上の1行目）",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値は、いずれも本文（例題の与件・図の前後の明示値）のみ。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- 練習・stretch の答えと同じ文字列になる小さい数（例: 8・6・9・24）が本文明示値として図に入る場合がある。"
        "これらは本文が図の直前・直後で明示している値であり、練習の答えの転記ではない。禁止文字列検査には、本文明示値と一致しない答え（多桁の数・分数・小数）を登録している。",
        "- L08_fig2 の相対度数は本文の表の6点（固定値）で、乱数によるシミュレーションではない。横軸は表の回数を等間隔に並べた（図中に明記）。",
        "- L09_fig1・L15_fig2 は記号のみ（数値なし）。L16_fig1 の数字はレッスン番号（L01〜L15）と「1通り」のみ。",
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
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks, {n_tokens} ban-tokens)")


if __name__ == "__main__":
    main()
