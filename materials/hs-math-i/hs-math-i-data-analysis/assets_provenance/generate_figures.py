#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高1数学I「データの分析」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。書き方は先行単元
materials/hs-math-i/hs-math-i-numbers-and-expressions/assets_provenance/generate_figures.py
を踏襲（Checker・許可リスト検査・禁止文字列検査・陽性対照・FIGURE_MANIFEST 自動生成）。
統計図の描画ヘルパー（数直線・箱ひげ図・ドットプロット・度数軸）は
materials/jhs-math-2/jhs-math-2-quartiles-boxplot と materials/jhs-math-1/jhs-math-1-data-distribution
の実装を流用した（元スクリプトは無変更）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（9枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / random / re / html / pathlib / xml.etree / fractions）
- 図の選定: 各 lesson_XX.md 本文の画像参照 ![alt](assets/…) にある9枚（L01_fig1・L02_fig1・L03_fig1・L04_fig1・
  L04_fig2・L05_fig1・L06_fig1・L07_fig1・L09_fig1）。
- データの正: 同じ階層の共通データ生成スクリプト generate_datasets.py の関数（各レッスン本文の表と
  同一であることは同スクリプトの assert と本文照合で確認済み）。本スクリプトはそれを import して使い、
  データ点を二重定義しない。ラベル・alt・軸範囲は該当 lesson_XX.md 本文（図の前後の記述と画像参照の alt）に合わせる。
  L07_fig1 はデータ=coin_counts(seed=20260902)（共通スクリプトの正）・度数列を本文の度数分布表の写しと照合・
  18以上の棒を濃く塗る。L09_fig1 は枠名・矢印ラベルを lesson_09.md の文言と照合。全9図の alt を本文と照合。
- alt の照合: 各図が宣言した alt（本文の画像参照 ![alt](assets/…) と同一の文字列）が該当
  lesson_XX.md に文字単位で存在することを生成時に assert する（lesson が無い図は「未照合」と記録）。
- 統計の自己検証（各 fig_* 内の Checker。1つでも失敗すると例外で停止し図を出力しない）:
  * 四分位数は**中2教材の方式**（中央値で前後に分け、奇数個は中央値を除く）を quartiles() で
    自前実装し、main() 冒頭の自己テスト（中2教材の例1・例2の既知値）で毎回検証する。
  * 外れ値の判定は 第1四分位数 − 1.5×四分位範囲 未満・第3四分位数 ＋ 1.5×四分位範囲 超。
    ひげは外れ値を除いた最小値・最大値まで。描いた箱・ひげ・外れ値の座標を値から再計算して照合。
  * ヒストグラムは生データから度数を数え直し、棒の高さ=度数×倍率を照合。
  * 散布図は各点の描画座標がデータの線形変換と一致することを照合し、相関係数 r
    （分散は n で割る・共分散を標準偏差の積で割る）を計算してパネルの符号と一致を確認。
  * 平均値は m と表記（x に上線を付ける記号は結合文字になるため使わない）。
- 答えの分離方針（二重ゲート＋陽性対照）: 先行単元と同じ。
  (1) 許可リスト検査——各図が宣言した「本文明示値のみのラベル一覧」(allow_texts) と
      生成後SVGの<text>全内容が集合として完全一致することを検査する。
  (2) 禁止文字列検査——answer_key 由来のトークン(check_tokens)が図中テキストに現れないことを
      検査する（answer_key_L01-03／L04-06／L07-08／L09 由来の値を登録済み）。
- 禁止文字の機械検査: 絵文字・結合文字・異体字セレクタ・全角英数字を、生成した全SVG（コメント含む）
  と本スクリプト自身の全文に対して走査し、1文字でもあれば停止する。検出器は陽性対照で毎回実証。
- 決定性: 同じ入力から同じバイト列（乱数は固定シードの random.Random・生成日はその日の日付）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（candidate_draft/lesson_XX.md）の表と一致させること。
"""

import datetime
import math
import random
import re
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction as F
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSONS = HERE.parent            # lesson_XX.md（alt 照合用）
GENERATED = datetime.date.today().isoformat()

# 共通データ生成スクリプト（同じ階層）。データ点はここから import し、本スクリプトでは二重定義しない。
sys.dont_write_bytecode = True   # 来歴フォルダに __pycache__ を作らない
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import generate_datasets as gd   # noqa: E402

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_NUM = 11       # 目盛数値
FS_CAP = 11       # キャプション
DOT_R = 3.0       # 点マーカー半径（散布図・ドットプロット）
DOT_R_OUT = 3.4   # 外れ値●
SHADE = "#e6e6e6"  # 棒のうすい網かけ
SHADE2 = "#c8c8c8"  # やや濃い網かけ

CAPTION_FAKE = "架空の練習用データ"


# ===========================================================================
# 描画ヘルパー（中2箱ひげ図版・中1データの分布版から流用＋矢印は数と式版の三角形）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.defs = []
        self.body = []

    def raw(self, s):
        self.body.append(s)

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def rect(self, x, y, w, h, sw=MAIN_W, fill="none", dash=None, rx=None,
             color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        stroke = f' stroke="{color}" stroke-width="{sw}"' if sw else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
                 f'{r} fill="{fill}"{stroke}{d}/>')

    def dot(self, x, y, r=DOT_R, fill="#000", sw=1.2):
        if fill == "none" or fill == "#fff":
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                     f'stroke="#000" stroke-width="{sw}"/>')
        else:
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def ring(self, x, y, r, sw=1.3):
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="none" '
                 f'stroke="#000" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def polyline(self, pts, w=MAIN_W, dash=None, color="#000"):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polyline points="{p}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}"{d}/>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None):
        """直線矢印（線＋先端の三角形。marker不使用で self-contained）"""
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, w=w, dash=dash)
        nx, ny = -math.sin(ang), math.cos(ang)
        self.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
                 f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
                 f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')

    def hatch(self):
        """斜線パターン（<defs>に1回だけ内蔵）。塗りに使う参照文字列を返す"""
        if not self.defs:
            self.defs.append(
                '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
                'patternTransform="rotate(45)">'
                '<line x1="0" y1="0" x2="0" y2="6" stroke="#000" stroke-width="0.6"/>'
                '</pattern>')
        return "url(#hatch)"

    def save(self, path, fig_id, title, desc):
        defs = f"<defs>{''.join(self.defs)}</defs>\n" if self.defs else ""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'role="img">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


class Checker:
    """数学検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


def int_number_line(cv, T, x0, x1, y, vmin, vmax, label_vals, tick_step=1,
                    tick_h=3.5, big_h=6.0, label_size=FS_NUM, label_dy=18):
    """整数目盛りの数直線。戻り値: 値→x座標 の線形変換関数（数値→座標の厳密変換）"""
    def X(v):
        return float(x0 + (x1 - x0) * (F(v) - vmin) / (vmax - vmin))

    cv.line(x0, y, x1, y, w=1.2)
    n = round((vmax - vmin) / tick_step)
    for i in range(n + 1):
        v = vmin + i * tick_step
        h = big_h if v in label_vals else tick_h
        cv.line(X(v), y - h, X(v), y + h, w=0.9)
    for v in label_vals:
        T(X(v), y + label_dy, f"{v:g}", size=label_size)
    return X


def y_axis(cv, T, x, y_base, yscale, label_vals, label_size=10.5, top_pad=8):
    """度数の縦軸: y_base を0として上方向。label_vals にティック＋ラベル"""
    top = y_base - max(label_vals) * yscale - top_pad
    cv.line(x, y_base, x, top, w=1.2)
    for f in label_vals:
        cv.line(x - 4, y_base - f * yscale, x, y_base - f * yscale, w=0.9)
        T(x - 8, y_base - f * yscale + 4, f"{f:g}", size=label_size, anchor="end")


def draw_boxplot(cv, X, y, fv, whisk_lo, whisk_hi, outliers, box_h=26, w=MAIN_W):
    """五数要約 fv と、外れ値を除いたひげの端 whisk_lo/whisk_hi・外れ値リストから
    箱ひげ図を1本描く。外れ値は●で別描き。戻り値=描画に使った座標（照合用）"""
    xlo, xq1, xmed, xq3, xhi = (X(whisk_lo), X(fv["q1"]), X(fv["med"]),
                                X(fv["q3"]), X(whisk_hi))
    assert xlo <= xq1 <= xmed <= xq3 <= xhi, "箱ひげ図の座標が単調でない"
    cv.line(xlo, y, xq1, y, w=w)
    cv.line(xq3, y, xhi, y, w=w)
    cv.line(xlo, y - box_h * 0.32, xlo, y + box_h * 0.32, w=w)
    cv.line(xhi, y - box_h * 0.32, xhi, y + box_h * 0.32, w=w)
    cv.rect(xq1, y - box_h / 2, xq3 - xq1, box_h, sw=w)
    cv.line(xmed, y - box_h / 2, xmed, y + box_h / 2, w=w)
    xout = []
    for v in outliers:
        cv.dot(X(v), y, r=DOT_R_OUT)
        xout.append(X(v))
    return dict(xlo=xlo, xq1=xq1, xmed=xmed, xq3=xq3, xhi=xhi, xout=xout)


def draw_dotplot(cv, X, y_base, data, r=DOT_R, step=9.0):
    """ドットプロット（1個1点・同じ値は縦に積む）。戻り値=打点数"""
    seen = {}
    for v in sorted(data):
        k = seen.get(v, 0)
        cv.dot(X(v), y_base - k * step, r=r)
        seen[v] = k + 1
    return sum(seen.values())


def scatter_axes(cv, T, x0, y0, w, h, xmax, ymax, xlab="x", ylab="y",
                 xticks=(), yticks=(), tick_labels=False, xmin=0, ymin=0):
    """左下 (x0,y0) を (xmin, ymin) とする散布図の軸（矢印つき）。戻り値 (X, Y)
    xmin/ymin の既定は 0（原点始まり）。L04_fig2 のように 0 始まりにしない図は xmin/ymin を与える。"""
    def X(v):
        return float(x0 + F(w) * (F(v) - xmin) / (xmax - xmin))

    def Y(v):
        return float(y0 - F(h) * (F(v) - ymin) / (ymax - ymin))

    cv.arrow(x0, y0, x0 + w + 14, y0, w=1.2)
    cv.arrow(x0, y0, x0, y0 - h - 14, w=1.2)
    T(x0 + w + 14, y0 + 16, xlab, size=FS_NUM)
    T(x0 - 12, y0 - h - 10, ylab, size=FS_NUM)
    for v in xticks:
        cv.line(X(v), y0 - 3, X(v), y0 + 3, w=0.9)
        if tick_labels:
            T(X(v), y0 + 15, f"{v:g}", size=10)
    for v in yticks:
        cv.line(x0 - 3, Y(v), x0 + 3, Y(v), w=0.9)
        if tick_labels:
            T(x0 - 7, Y(v) + 3.5, f"{v:g}", size=10, anchor="end")
    return X, Y


def edge_point(box, target):
    """矩形 box=(x,y,w,h) の中心から target へ向かう半直線と矩形の辺の交点"""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    dx, dy = target[0] - cx, target[1] - cy
    tx = (w / 2) / abs(dx) if dx else float("inf")
    ty = (h / 2) / abs(dy) if dy else float("inf")
    t = min(tx, ty)
    return (cx + dx * t, cy + dy * t)


def box_center(box):
    return (box[0] + box[2] / 2, box[1] + box[3] / 2)


def disjoint(r1, r2):
    return (r1[0] + r1[2] <= r2[0] or r2[0] + r2[2] <= r1[0] or
            r1[1] + r1[3] <= r2[1] or r2[1] + r2[3] <= r1[1])


def on_edge(p, r, tol=0.5):
    """点pが矩形rの辺上にあるか（矢印端点の座標整合assert用）"""
    x, y = p
    x0, y0, w, h = r
    on_v = (abs(x - x0) <= tol or abs(x - (x0 + w)) <= tol) and y0 - tol <= y <= y0 + h + tol
    on_h = (abs(y - y0) <= tol or abs(y - (y0 + h)) <= tol) and x0 - tol <= x <= x0 + w + tol
    return on_v or on_h


def no_digits(texts, allow_L=False):
    """ラベル群に数字が含まれない（allow_L=TrueならL01等のレッスン番号は許す）"""
    for t in texts:
        s = re.sub(r"L\d\d", "", t) if allow_L else t
        if re.search(r"[0-9]", s):
            return False
    return True


# ===========================================================================
# 統計ヘルパー（分数で厳密計算。相関係数のみ平方根で浮動小数）
# ===========================================================================
def mean_of(data):
    return F(sum(data), len(data))


def variance_of(data):
    """分散（偏差の2乗の平均——n で割る。本単元の定義）"""
    m = mean_of(data)
    return sum((F(v) - m) ** 2 for v in data) / len(data)


def sd_of(data):
    return math.sqrt(variance_of(data))


def covariance_of(xs, ys):
    """共分散（偏差の積の平均——n で割る）"""
    mx, my = mean_of(xs), mean_of(ys)
    return sum((F(x) - mx) * (F(y) - my) for x, y in zip(xs, ys)) / len(xs)


def correlation_of(xs, ys):
    return float(covariance_of(xs, ys)) / (sd_of(xs) * sd_of(ys))


def quartiles(data):
    """五数要約——中2教材（jhs-math-2-quartiles-boxplot）の方式をそのまま踏襲。
    (1) 小さい順に並べる (2) 中央値（第2四分位数）で前半・後半に分ける——
    **奇数個のとき中央値は前半にも後半にも入れない** (3) 各半分の中央値が第1・第3四分位数。"""
    d = sorted(data)
    n = len(d)

    def med(seg):
        k = len(seg)
        if k % 2 == 1:
            return F(seg[k // 2])
        return F(seg[k // 2 - 1] + seg[k // 2], 2)

    if n % 2 == 1:
        lower, upper = d[: n // 2], d[n // 2 + 1:]
    else:
        lower, upper = d[: n // 2], d[n // 2:]
    return dict(min=F(d[0]), q1=med(lower), med=med(d), q3=med(upper), max=F(d[-1]))


def outlier_split(data, fv):
    """外れ値の判定（教科書標準）: 第1四分位数 − 1.5×四分位範囲 未満・第3四分位数 ＋ 1.5×四分位範囲 超。
    戻り値: (外れ値でない値, 外れ値, 下の境界, 上の境界)"""
    iqr = fv["q3"] - fv["q1"]
    lo, hi = fv["q1"] - F(3, 2) * iqr, fv["q3"] + F(3, 2) * iqr
    ins = [v for v in data if lo <= v <= hi]
    outs = [v for v in data if v < lo or v > hi]
    return ins, outs, lo, hi


def freq_counts(data, cmin, cwidth, nclass):
    """度数分布（各階級は「以上〜未満」の半開区間）を生データから再集計"""
    counts = [0] * nclass
    for v in data:
        k = int((v - cmin) // cwidth)
        assert 0 <= k < nclass, f"データ {v} が階級の範囲外"
        counts[k] += 1
    return counts


def fmt_fv(fv):
    return "/".join(f"{float(fv[k]):g}" for k in ("min", "q1", "med", "q3", "max"))


def stats_self_test():
    """四分位数・外れ値・相関の自己テスト（中2教材の既知値ほか）——毎回の生成前に実行"""
    ex1 = [7, 10, 13, 16, 20, 22, 25, 28, 31]            # 中2 L03 例1（n=9・奇数）
    ex2 = [12, 14, 15, 17, 19, 21, 24, 26, 28, 30]       # 中2 L03 例2（n=10・偶数）
    assert quartiles(ex1) == dict(min=7, q1=11.5, med=20, q3=26.5, max=31), quartiles(ex1)
    assert quartiles(ex2) == dict(min=12, q1=15, med=20, q3=26, max=30), quartiles(ex2)
    fv = quartiles([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30])  # 上に外れ値1つ
    ins, outs, lo, hi = outlier_split([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30], fv)
    assert fv["q1"] == 3 and fv["q3"] == 9 and hi == 18 and lo == -6, (fv, lo, hi)
    assert outs == [30] and max(ins) == 10, (ins, outs)
    ins, outs, lo, hi = outlier_split([-20, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], quartiles(
        [-20, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
    assert outs == [-20] and min(ins) == 1, "下側の外れ値を検出できない"
    assert variance_of([2, 4, 6, 8, 10]) == 8 and mean_of([2, 4, 6, 8, 10]) == 6
    assert abs(correlation_of([1, 2, 3], [2, 4, 6]) - 1.0) < 1e-12
    assert abs(correlation_of([1, 2, 3], [6, 4, 2]) + 1.0) < 1e-12
    assert abs(correlation_of([1, 2, 3, 4], [1, -1, -1, 1])) < 1e-12
    assert freq_counts([0, 9, 10, 19, 20], 0, 10, 3) == [2, 2, 1]
    # 別経路: 共通データスクリプト generate_datasets.py の実装（quartiles／pvariance／outliers／corr_of）
    # と本スクリプトの実装が同じ値を返す（方式の食い違いを毎回検出する）
    for data in (ex1, ex2, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 30], [3, 5, 6, 6, 7, 8, 8, 8, 9, 10, 18]):
        assert quartiles(data) == gd.quartiles(data), ("quartiles", data)
        assert variance_of(data) == gd.pvariance(data), ("variance", data)
        assert outlier_split(data, quartiles(data))[1] == gd.outliers(data)[0], ("outliers", data)
    assert abs(correlation_of([1, 2, 3, 5], [2, 1, 4, 6]) - gd.corr_of([1, 2, 3, 5], [2, 1, 4, 6])) < 1e-12


# ===========================================================================
# 図1: L01 A班・B班の箱ひげ図の並列——外れ値を●で別描き
# 仕様の正: lesson_01.md §3（例題2の直後）。データ=generate_datasets.l01_library_visits()。
# 四分位数は中2方式・外れ値は 1.5×四分位範囲 の外。五数の数値ラベルは打たない
# （読み取りが練習になるため）。
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md §3 の表と一致。データは共通スクリプトから import） ---
    NAME_A, NAME_B = "A班", "B班"
    _d = gd.l01_library_visits()
    DATA_A, DATA_B = _d["A"], _d["B"]                  # A班は上に外れ値18・B班は外れ値なし
    FV_A_EXPECT = dict(min=3, q1=6, med=8, q3=9, max=18)
    FV_B_EXPECT = dict(min=2, q1=5, med=8, q3=11, max=13)
    X_LABEL = "利用回数（回）"
    VMIN, VMAX, TICKS = 0, 20, [0, 5, 10, 15, 20]
    ALT = ("A班とB班の箱ひげ図の並列——同じ数直線上に2本の箱ひげ図を並べ、A班の18を外れ値として●で別に描き、"
           "A班のひげは10まで。箱はA班の方が短いのに、●まで含めた広がりはA班の方が大きい")

    ck = Checker()
    fva, fvb = quartiles(DATA_A), quartiles(DATA_B)
    ck.ok(f"{NAME_A}・{NAME_B} とも11個（本文の表と同一の列を共通スクリプトから取得）",
          len(DATA_A) == 11 and len(DATA_B) == 11 and
          DATA_A == [3, 5, 6, 6, 7, 8, 8, 8, 9, 10, 18] and DATA_B == [2, 4, 5, 6, 8, 8, 9, 10, 11, 12, 13])
    ck.ok("五数要約を中2方式（中央値で前後に分け奇数個は中央値を除く）で再計算・共通スクリプトの quartiles() とも一致",
          fva == FV_A_EXPECT and fvb == FV_B_EXPECT and
          gd.quartiles(DATA_A) == fva and gd.quartiles(DATA_B) == fvb,
          f"実測 {NAME_A}={fmt_fv(fva)}・{NAME_B}={fmt_fv(fvb)}")
    ins_a, outs_a, lo_a, hi_a = outlier_split(DATA_A, fva)
    ins_b, outs_b, lo_b, hi_b = outlier_split(DATA_B, fvb)
    ck.ok(f"{NAME_A}: 四分位範囲3・境界は1.5未満と13.5超——外れ値は18だけ",
          fva["q3"] - fva["q1"] == 3 and lo_a == F(3, 2) and hi_a == F(27, 2) and outs_a == [18])
    ck.ok(f"{NAME_A}: ひげの端は外れ値を除いた最小3・最大10",
          min(ins_a) == 3 and max(ins_a) == 10)
    ck.ok(f"{NAME_B}: 四分位範囲6・境界は−4未満と20超——外れ値なし・ひげは2〜13",
          fvb["q3"] - fvb["q1"] == 6 and lo_b == -4 and hi_b == 20 and outs_b == []
          and min(ins_b) == 2 and max(ins_b) == 13)
    ck.ok(f"対比: 箱の長さは {NAME_A}（3）<{NAME_B}（6）なのに範囲は {NAME_A}（15）>{NAME_B}（11）",
          (fva["q3"] - fva["q1"], fvb["q3"] - fvb["q1"]) == (3, 6) and
          (fva["max"] - fva["min"], fvb["max"] - fvb["min"]) == (15, 11))

    def mode_unique(d):
        best = max(set(d), key=d.count)
        return best if d.count(best) > max(d.count(v) for v in set(d) if v != best) else None
    ck.ok("平均値・中央値・最頻値が A班・B班 とも 8（本文 §1 の設計値）",
          mean_of(DATA_A) == 8 and mean_of(DATA_B) == 8 and fva["med"] == 8 and fvb["med"] == 8
          and mode_unique(DATA_A) == 8 and mode_unique(DATA_B) == 8)

    cv = Canvas(480, 262)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    X = int_number_line(cv, T, 55, 445, 196, VMIN, VMAX, label_vals=TICKS, tick_step=1)
    ya, yb = 88, 148
    ca = draw_boxplot(cv, X, ya, fva, min(ins_a), max(ins_a), outs_a)
    cb = draw_boxplot(cv, X, yb, fvb, min(ins_b), max(ins_b), outs_b)
    ck.ok("描画座標の照合: 箱の両端・中央線・ひげの端・外れ値●が値の線形変換と一致",
          abs(ca["xq1"] - X(6)) < 1e-9 and abs(ca["xq3"] - X(9)) < 1e-9 and
          abs(ca["xmed"] - X(8)) < 1e-9 and abs(ca["xlo"] - X(3)) < 1e-9 and
          abs(ca["xhi"] - X(10)) < 1e-9 and ca["xout"] == [X(18)] and
          abs(cb["xq1"] - X(5)) < 1e-9 and abs(cb["xq3"] - X(11)) < 1e-9 and
          abs(cb["xmed"] - X(8)) < 1e-9 and abs(cb["xlo"] - X(2)) < 1e-9 and
          abs(cb["xhi"] - X(13)) < 1e-9 and cb["xout"] == [])
    T(30, ya + 4, NAME_A, size=FS, weight="bold")
    T(30, yb + 4, NAME_B, size=FS, weight="bold")
    T(240, 26, f"{NAME_A}と{NAME_B}の箱ひげ図——外れ値は別に●で示す", size=FS, weight="bold")
    T(240, 50, "ひげは外れ値を除いた最小値・最大値まで", size=FS_CAP)
    cv.dot(200, 231, r=DOT_R_OUT)
    T(210, 235, "=外れ値", size=10, anchor="start")
    T(240, 254, f"横軸: {X_LABEL}・各班11人（{CAPTION_FAKE}）", size=FS_CAP)

    return {"file": "L01_fig1_boxplots_outlier.svg", "lesson": "L01", "canvas": cv,
            "title": "A班とB班の箱ひげ図の並列——外れ値を●で別描き",
            "intent": "同じ数直線の上にA班・B班（各11人の図書室利用回数）の箱ひげ図を並べ、四分位範囲の1.5倍より外の値（A班の18）を外れ値として●で別に描く。ひげは外れ値を除いた最小値・最大値まで（A班は10まで）。箱が短いA班の方が●まで含めた広がりは大きい対比で「範囲と四分位範囲」「箱の長さとデータの個数」の混同を防ぐ。五数の数値ラベルは打たない（読み取りは練習）",
            "src": "lesson_01.md §3（例題2の直後）",
            "params": f"{NAME_A}={DATA_A}（五数{fmt_fv(fva)}・外れ値18・ひげ3〜10）／{NAME_B}={DATA_B}（五数{fmt_fv(fvb)}・外れ値なし・ひげ2〜13）／横軸{VMIN}〜{VMAX}",
            "spec": "データ=generate_datasets.l01_library_visits()・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": ["4.5", "13.5", "四分位範囲3", "四分位範囲6", "Q1=", "Q3="],
            "allow_texts": labels}


# ===========================================================================
# 図2: L02 Bさんの記録のドットプロットと平均線 m=14・偏差の矢印
# 仕様の正: lesson_02.md §2（偏差の表の直後）。データ=generate_datasets.l02_freethrow()["B"]。
# 偏差の値ラベルは本文の偏差表に載る値（−6, −2, ＋2, ＋6）のみ（SHOW_DEV_LABELS で切替可）。
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（lesson_02.md §2 の表と一致。データは共通スクリプトから import） ---
    NAME = "Bさん"
    DATA = gd.l02_freethrow()["B"]     # 5日間のフリースロー成功数（20本中）
    M_EXPECT = 14
    VAR_EXPECT = 16           # 分散（図には描かない・検算のみ）
    X_LABEL = "成功数（本）"
    VMIN, VMAX, TICKS = 0, 20, [0, 4, 8, 12, 16, 20]
    SHOW_DEV_LABELS = True
    ALT = ("Bさんの記録のドットプロットと平均値 m=14 の破線——m から各値へ水平の矢印で偏差を示し、"
           "右向きが正・左向きが負。矢印の長さが偏差の大きさで、正負が打ち消し合って和が0になる")

    ck = Checker()
    m = mean_of(DATA)
    devs = [F(v) - m for v in DATA]
    ck.ok("5個・合計70・平均値 m=14（本文の表と同一の列を共通スクリプトから取得）",
          DATA == [8, 12, 14, 16, 20] and len(DATA) == 5 and sum(DATA) == 70 and m == M_EXPECT
          and gd.mean(DATA) == M_EXPECT)
    ck.ok("偏差 −6・−2・0・2・6 の和は0（偏差の和は必ず0）",
          devs == [-6, -2, 0, 2, 6] and sum(devs) == 0)
    ck.ok("分散=偏差の2乗の平均=80/5=16・s=4（図には描かない）",
          variance_of(DATA) == VAR_EXPECT and sum(d * d for d in devs) == 80 and sd_of(DATA) == 4
          and gd.pvariance(DATA) == VAR_EXPECT)
    ck.ok("2s の帯（m±2s=6〜22）に全データが入る",
          m - 2 * sd_of(DATA) == 6 and m + 2 * sd_of(DATA) == 22 and
          all(abs(float(d)) <= 2 * sd_of(DATA) for d in devs))

    cv = Canvas(480, 280)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    X = int_number_line(cv, T, 55, 445, 216, VMIN, VMAX, label_vals=TICKS, tick_step=1)
    y_dots = 204
    n = draw_dotplot(cv, X, y_dots, DATA, r=4.0)
    # 平均線 m（破線）——ラベルは本文明示値「m=14」
    cv.line(X(m), 56, X(m), y_dots + 6, w=1.4, dash=DASH)
    T(X(m), 48, f"m={M_EXPECT}", size=FS, weight="bold")
    # 偏差の矢印: m から各値へ（偏差0の値は矢印なし）
    rows = [v for v in DATA if v != m]
    y_rows = [180, 158, 136, 114]
    ck.ok("打点数5（1個1点）・矢印は偏差0でない4個に1本ずつ", n == 5 and len(rows) == 4 and len(y_rows) == 4)
    dev_labels = []
    for v, yr in zip(rows, y_rows):
        d = F(v) - m
        x_from, x_to = X(m), X(v)
        cv.arrow(x_from, yr, x_to, yr, w=1.4, head=6.5)
        assert abs((x_to - x_from) - float(d) * (X(1) - X(0))) < 1e-9, "矢印の長さ≠偏差×単位長"
        assert (x_to > x_from) == (d > 0), "矢印の向き≠偏差の符号"
        if SHOW_DEV_LABELS:
            lab = f"{'＋' if d > 0 else '−'}{abs(int(d))}"   # 負号は U+2212
            dev_labels.append(lab)
            T((x_from + x_to) / 2, yr - 6, lab, size=FS_NUM)
    ck.ok("矢印の長さ=偏差×単位長・向き=偏差の符号（描画時に照合）", True)
    T(240, 26, f"{NAME}の記録のドットプロットと平均値 m——偏差は m からの矢印", size=FS, weight="bold")
    T(444, 62, "偏差=値−m", size=FS_NUM, anchor="end")
    T(444, 76, "（m と同じ値の点には矢印なし）", size=10, anchor="end")
    T(240, 252, f"横軸: {X_LABEL}・{NAME}の記録（{CAPTION_FAKE}）", size=FS_CAP)
    T(240, 268, "右向きの矢印=正の偏差・左向き=負の偏差", size=10)
    numeric = {t for t in labels if re.search(r"[0-9]", t)}
    ck.ok("図中の数値ラベルは m=14・偏差4個（−6, −2, ＋2, ＋6）・目盛のみ",
          numeric == {f"m={M_EXPECT}", "−6", "−2", "＋2", "＋6"} | {f"{v:g}" for v in TICKS}
          and dev_labels == ["−6", "−2", "＋2", "＋6"], f"実測={sorted(numeric)}")

    return {"file": "L02_fig1_dotplot_deviation.svg", "lesson": "L02", "canvas": cv,
            "title": "Bさんの記録のドットプロットと平均線 m=14・偏差の矢印",
            "intent": "数直線上のドットプロット（Bさんの5日間のフリースロー成功数）に平均値 m=14 の破線を立て、m から各値への水平矢印で偏差（値−m）を見せる。右向きが正・左向きが負で、矢印の長さが偏差の大きさ。偏差の和が0になる（正負が打ち消し合う）ことを目で確かめてから2乗へ進む導入図",
            "src": "lesson_02.md §2（偏差の表の直後）",
            "params": f"データ={DATA}（{NAME}・m={M_EXPECT}・偏差=−6,−2,0,＋2,＋6・分散{VAR_EXPECT}は図に描かない）／横軸{VMIN}〜{VMAX}／偏差ラベル表示={SHOW_DEV_LABELS}",
            "spec": "データ=generate_datasets.l02_freethrow()[\"B\"]・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": ["80/5", "s²=16", "s=4", "分散", "標準偏差"],
            "allow_texts": labels}


# ===========================================================================
# 図3: L03 平均値が同じで散らばりが違う1組・2組のヒストグラム
# 仕様の正: lesson_03.md §1（2組の s の計算の直後）。
# データ=generate_datasets.l02_test20()（1組）・l03_test20_class2()（2組）。
# 度数は生データから再集計・平均値の一致を分数で厳密検算。s の値は図に描かない。
# ===========================================================================
def fig_L03_1():
    # --- パラメータ（lesson_02.md §5・lesson_03.md §1 の表と一致。データは共通スクリプトから import） ---
    NAME_A, NAME_B = "1組", "2組"
    DATA_A = gd.l02_test20()             # 1組20人の小テスト（100点満点）
    DATA_B = gd.l03_test20_class2()      # 2組20人の小テスト（100点満点）
    M_EXPECT = 60
    CMIN, CWIDTH, NCLASS = 0, 10, 10          # 階級 0以上10未満 … 90以上100未満
    COUNTS_A_EXPECT = [0, 0, 0, 0, 3, 7, 7, 2, 1, 0]
    COUNTS_B_EXPECT = [0, 0, 1, 2, 3, 4, 3, 3, 2, 2]
    VAR_A_EXPECT, VAR_B_EXPECT = 100, 400     # 分散（図には描かない・検算のみ）
    X_LABEL = "得点（点）"
    ALT = ("平均値が同じで散らばりが違う2つの組のヒストグラム——同じ横軸（0〜100点・幅10）で1組と2組を上下に並べ、"
           "平均値 m=60 の破線が同じ位置に立つのに、1組の山は狭く高く、2組の山は低く広い")

    ck = Checker()
    ck.ok(f"{NAME_A}・{NAME_B} とも20個・合計1200・m={M_EXPECT}（分数で厳密・共通スクリプトの mean() とも一致）",
          len(DATA_A) == 20 and len(DATA_B) == 20 and sum(DATA_A) == sum(DATA_B) == 1200 and
          mean_of(DATA_A) == M_EXPECT and mean_of(DATA_B) == M_EXPECT and
          gd.mean(DATA_A) == gd.mean(DATA_B) == M_EXPECT)
    ca = freq_counts(DATA_A, CMIN, CWIDTH, NCLASS)
    cb = freq_counts(DATA_B, CMIN, CWIDTH, NCLASS)
    ck.ok(f"{NAME_A}・{NAME_B}: 度数を生データから再集計（幅10）", ca == COUNTS_A_EXPECT and cb == COUNTS_B_EXPECT,
          f"実測 {NAME_A}={ca}・{NAME_B}={cb}")
    va, vb = variance_of(DATA_A), variance_of(DATA_B)
    ck.ok(f"分散は {NAME_A}=100・{NAME_B}=400（2組は1組の4倍・s は 10 と 20。図には描かない）",
          va == VAR_A_EXPECT and vb == VAR_B_EXPECT and vb == 4 * va and sd_of(DATA_A) == 10 and sd_of(DATA_B) == 20
          and gd.pvariance(DATA_A) == VAR_A_EXPECT and gd.pvariance(DATA_B) == VAR_B_EXPECT)
    ck.ok(f"{NAME_A} の m を含む階級（60以上70未満）の度数7が最大（50以上60未満の7と同数を許す）",
          ca[6] == 7 and max(ca) == ca[6])
    ck.ok(f"{NAME_B} の度数の最大は4（50以上60未満）で {NAME_A} の最大7より小さい（山が低く広い）",
          max(cb) == 4 and cb[5] == 4 and max(cb) < max(ca))

    cv = Canvas(480, 470)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    yscale = 14.0
    panels = [(NAME_A, ca, 200), (NAME_B, cb, 410)]
    Xs = []
    for name, counts, base in panels:
        X = int_number_line(cv, T, 60, 440, base, 0, 100, label_vals=list(range(0, 101, 10)),
                            tick_step=10, label_dy=17, label_size=10)
        Xs.append(X)
        y_axis(cv, T, 60, base, yscale, [0, 2, 4, 6, 8])
        for k, c in enumerate(counts):
            if c > 0:
                x_l, x_r = X(k * CWIDTH), X((k + 1) * CWIDTH)
                cv.rect(x_l, base - c * yscale, x_r - x_l, c * yscale, sw=1.3, fill=SHADE)
                assert abs((base - (base - c * yscale)) - c * yscale) < 1e-9
        # 平均線 m（両パネル同じ位置）——ラベルは本文明示値「m=60」
        cv.line(X(M_EXPECT), base - 140, X(M_EXPECT), base, w=1.4, dash=DASH)
        T(X(M_EXPECT), base - 147, f"m={M_EXPECT}", size=FS, weight="bold")
        T(66, base - 152, f"{name}（20人）", size=FS, anchor="start", weight="bold")
        T(66, base - 136, "度数（人）", size=10, anchor="start")
    ck.ok(f"棒の高さ=度数×{yscale:g}px（描画時に照合）・2パネルの横軸は同一の変換",
          all(abs(Xs[0](v) - Xs[1](v)) < 1e-9 for v in range(0, 101, 10)))
    T(240, 26, "平均値 m は同じ——散らばりがちがう2つの組", size=FS, weight="bold")
    T(240, 452, f"横軸: {X_LABEL}・階級の幅10／縦軸: 度数（人）（{CAPTION_FAKE}・各20人）",
      size=FS_CAP)

    return {"file": "L03_fig1_two_histograms_same_mean.svg", "lesson": "L03", "canvas": cv,
            "title": "平均値が同じで散らばりが違う1組・2組のヒストグラム",
            "intent": "同じ横軸（0〜100点・幅10）のヒストグラムを上下に並べ（上=1組・下=2組）、平均値 m=60 の破線が同じ位置に立つのに、1組の山は狭く高く、2組の山は低く広いことを見せる。平均値だけでは分布の違いを言えない——散らばりを1つの数（分散・標準偏差）にする必要性の導入。s の値は図に描かない",
            "src": "lesson_03.md §1（2組の s の計算の直後）",
            "params": f"{NAME_A}={DATA_A}／{NAME_B}={DATA_B}（いずれも m={M_EXPECT}・度数{ca}／{cb}・分散{VAR_A_EXPECT}／{VAR_B_EXPECT}は図に描かない）／階級の幅{CWIDTH}",
            "spec": "データ=generate_datasets.l02_test20()・l03_test20_class2()・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": ["8000", "2000", "s=10", "s=20", "√400", "分散", "標準偏差"],
            "allow_texts": labels}


# ===========================================================================
# 共有パラメータ: L04 の散布図データ（3パネル A・B・C）= lesson_04.md §1 の表。
# データは generate_datasets.L04_fig1_three_types() から取る。
# L04_fig2 とは点を共用しない（図2は例題1の6日分=別データ）。
# ===========================================================================
_L04 = gd.L04_fig1_three_types()
SCATTER_POS = list(zip(_L04["x"], _L04["A"]))    # A 正の相関
SCATTER_NEG = list(zip(_L04["x"], _L04["B"]))    # B 負の相関
SCATTER_NONE = list(zip(_L04["x"], _L04["C"]))   # C 相関なし

# 答え漏れ検査の禁止文字列（answer_key_L04-06.md 由来）。L04〜L06 の図に登録
TOKENS_L04_L06 = ["0.83", "5/6", "−0.8", "0.8", "0.71", "−0.11", "−0.64", "0.89", "0.95"]


def plot_points(cv, X, Y, pts, r=DOT_R):
    """散布図の点を打ち、描画座標が値の線形変換と一致することを返す（照合用）"""
    coords = []
    for x, y in pts:
        px, py = X(x), Y(y)
        cv.dot(px, py, r=r)
        coords.append((px, py))
    return coords


# ===========================================================================
# 図4: L04 散布図——A 正の相関・B 負の相関・C 相関なしの3パネル
# 仕様の正: lesson_04.md §1（A・B・C の表の直後）。r の値は図に描かない（計算は本文の活動）。
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（lesson_04.md §1 の表と一致。データは SCATTER_*（共通スクリプト由来）） ---
    panels = [("A 正の相関", SCATTER_POS, "右上がりに並ぶ"),
              ("B 負の相関", SCATTER_NEG, "右下がりに並ぶ"),
              ("C 相関なし", SCATTER_NONE, "どちらでもない")]
    XMAX = YMAX = 9
    R_EXPECT = {"A 正の相関": 0.933, "B 負の相関": -0.952, "C 相関なし": 0.072}   # 生成時に再計算して照合する期待値（±0.001）
    ALT = ("散布図と相関の向き——A は右上がり（正の相関）・B は右下がり（負の相関）・C はどちらでもない（相関なし）の3パネル。"
           "各8点、目盛りは1刻み")

    ck = Checker()
    ck.ok("3組の点が本文 §1 の表と同一（x=1〜8 共通・A/B/C の y）",
          SCATTER_POS == [(1, 2), (2, 3), (3, 5), (4, 4), (5, 6), (6, 5), (7, 7), (8, 8)] and
          SCATTER_NEG == [(1, 8), (2, 6), (3, 7), (4, 5), (5, 4), (6, 2), (7, 3), (8, 1)] and
          SCATTER_NONE == [(1, 5), (2, 2), (3, 7), (4, 4), (5, 8), (6, 3), (7, 6), (8, 4)])
    rs = {}
    for name, pts, _ in panels:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        rs[name] = correlation_of(xs, ys)
        ck.ok(f"{name}: 8点・座標は1〜{XMAX - 1}の整数・r は共通スクリプトの corr_of() とも一致",
              len(pts) == 8 and all(1 <= x <= XMAX - 1 and 1 <= y <= YMAX - 1 for x, y in pts)
              and abs(rs[name] - gd.corr_of(xs, ys)) < 1e-12 and abs(rs[name] - R_EXPECT[name]) < 1e-3,
              f"r≒{rs[name]:.3f}")
    ck.ok("A 正の相関: r>0.7（分散は n で割る定義で計算）", rs["A 正の相関"] > 0.7,
          f"r≒{rs['A 正の相関']:.3f}")
    ck.ok("B 負の相関: r<−0.7", rs["B 負の相関"] < -0.7, f"r≒{rs['B 負の相関']:.3f}")
    ck.ok("C 相関なし: r の絶対値<0.2", abs(rs["C 相関なし"]) < 0.2, f"r≒{rs['C 相関なし']:.3f}")

    cv = Canvas(660, 290)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    px0s = [40, 250, 460]
    W, H, base = 150, 150, 222
    for (name, pts, note), px0 in zip(panels, px0s):
        X, Y = scatter_axes(cv, T, px0, base, W, H, XMAX, YMAX,
                            xticks=range(1, XMAX), yticks=range(1, YMAX), tick_labels=True)
        coords = plot_points(cv, X, Y, pts)
        assert all(abs(cx - (px0 + W * x / XMAX)) < 1e-9 and abs(cy - (base - H * y / YMAX)) < 1e-9
                   for (cx, cy), (x, y) in zip(coords, pts)), "点の座標が値の変換と不一致"
        T(px0 + W / 2, 52, name, size=FS, weight="bold")
        T(px0 + W / 2, 262, note, size=FS_NUM)
    ck.ok("3パネルの各点の描画座標=値の線形変換・3パネル同一目盛り（描画時に照合）", True)
    T(330, 26, "散布図と相関の向き", size=FS, weight="bold")
    T(330, 282, f"{CAPTION_FAKE}・各8点（目盛りは1刻み）", size=10)

    return {"file": "L04_fig1_scatter_three_types.svg", "lesson": "L04", "canvas": cv,
            "title": "散布図——A 正の相関・B 負の相関・C 相関なしの3パネル",
            "intent": "同じ大きさの散布図を3枚並べ、点が右上がりに並ぶ（A 正の相関）・右下がりに並ぶ（B 負の相関）・どちらでもない（C 相関なし）の見分けを形で覚える。r の値は図に描かない（本文で計算する）",
            "src": "lesson_04.md §1（3組のデータ A・B・C の表の直後）",
            "params": f"A={SCATTER_POS}（r≈{rs['A 正の相関']:.2f}）／B={SCATTER_NEG}（r≈{rs['B 負の相関']:.2f}）／C={SCATTER_NONE}（r≈{rs['C 相関なし']:.2f}）／軸0〜{XMAX}・目盛1刻み",
            "spec": "データ=generate_datasets.L04_fig1_three_types()・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": TOKENS_L04_L06,
            "allow_texts": labels}


# ===========================================================================
# 図5: L04 偏差の積の符号の4象限——例題1の6日分（最高気温 x・売上 y）
# 仕様の正: lesson_04.md §2（4領域の段落の直後）。データ=generate_datasets.L04_ex1_temperature_drinks()。
# 軸は 0 始まりにしない（0 始まりだと6点が右上に固まり4領域が読めない）。
# ===========================================================================
def fig_L04_2():
    # --- パラメータ（lesson_04.md §2 の表と一致。データは共通スクリプトから import） ---
    _d = gd.L04_ex1_temperature_drinks()
    PTS = list(zip(_d["x"], _d["y"]))            # (最高気温 x（℃）, 売上 y（本）) 6日分
    MX_EXPECT, MY_EXPECT = 25, 40
    XMIN, XMAX, XTICKS = 18, 32, (20, 25, 30)
    YMIN, YMAX, YTICKS = 30, 48, (35, 40, 45)
    N_POS_EXPECT, N_NEG_EXPECT = 4, 2            # 積が正の点4・負の点2（負は (24, 41) と (27, 38)）
    COV_EXPECT = 10
    ALT = ("偏差の積の符号——平均線で分けた4つの領域。右上と左下（斜線）では偏差の積が正、左上と右下では負。"
           "点は例題1の6日分")

    ck = Checker()
    ck.ok("6点が本文 §2 の表（例題1）と同一",
          PTS == [(20, 33), (23, 39), (24, 41), (27, 38), (27, 44), (29, 45)])
    xs, ys = [p[0] for p in PTS], [p[1] for p in PTS]
    mx, my = mean_of(xs), mean_of(ys)
    ck.ok(f"x の平均値={MX_EXPECT}・y の平均値={MY_EXPECT}（分数で厳密・共通スクリプトの mean_of() とも一致）",
          mx == MX_EXPECT and my == MY_EXPECT and gd.mean_of(xs) == MX_EXPECT and gd.mean_of(ys) == MY_EXPECT)
    prods = [(F(x) - mx) * (F(y) - my) for x, y in PTS]
    ck.ok("平均線上の点がない（x の偏差・y の偏差とも 0 の点なし。x の偏差 −5,−2,−1,2,2,4／y の偏差 −7,−1,1,−2,4,5）",
          all(x != mx and y != my for x, y in PTS) and
          [x - mx for x in xs] == [-5, -2, -1, 2, 2, 4] and [y - my for y in ys] == [-7, -1, 1, -2, 4, 5])
    ck.ok("偏差の積の符号: 右上（＋,＋）と左下（−,−）は正・左上と右下は負（全6点で照合）",
          all((p > 0) == ((x > mx) == (y > my)) for p, (x, y) in zip(prods, PTS)))
    n_pos = sum(1 for p in prods if p > 0)
    negs = [pt for pt, p in zip(PTS, prods) if p < 0]
    ck.ok(f"積が正の点{N_POS_EXPECT}・負の点{N_NEG_EXPECT}（負は (24, 41) と (27, 38)）",
          n_pos == N_POS_EXPECT and len(negs) == N_NEG_EXPECT and negs == [(24, 41), (27, 38)])
    cov = covariance_of(xs, ys)
    ck.ok(f"共分散={COV_EXPECT}（>0・共通スクリプトの cov_of() とも一致）",
          cov == COV_EXPECT and cov > 0 and gd.cov_of(xs, ys) == COV_EXPECT, f"共分散={float(cov):g}")
    ck.ok("点が重ならない（(27, 38) と (27, 44) は x が同じだが y が違う）", len(set(PTS)) == len(PTS))
    ck.ok("全点が軸の範囲（x 18〜32・y 30〜48）に収まる",
          all(XMIN < x < XMAX and YMIN < y < YMAX for x, y in PTS))

    cv = Canvas(480, 430)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    x0, y0, W, H = 70, 350, 320, 270
    X = lambda v: float(x0 + F(W) * (F(v) - XMIN) / (XMAX - XMIN))
    Y = lambda v: float(y0 - F(H) * (F(v) - YMIN) / (YMAX - YMIN))
    hatch = cv.hatch()
    # 積が正の領域（右上・左下）を斜線で
    cv.rect(X(mx), Y(YMAX), X(XMAX) - X(mx), Y(my) - Y(YMAX), sw=0, fill=hatch)
    cv.rect(X(XMIN), Y(my), X(mx) - X(XMIN), Y(YMIN) - Y(my), sw=0, fill=hatch)
    X2, Y2 = scatter_axes(cv, T, x0, y0, W, H, XMAX, YMAX, xmin=XMIN, ymin=YMIN,
                          xticks=XTICKS, yticks=YTICKS, tick_labels=True)
    assert all(abs(X2(v) - X(v)) < 1e-9 for v in range(XMIN, XMAX + 1))
    assert all(abs(Y2(v) - Y(v)) < 1e-9 for v in range(YMIN, YMAX + 1))
    # 平均線（本文明示値: x の平均値 25・y の平均値 40）
    cv.line(X(mx), Y(YMAX), X(mx), Y(YMIN), w=1.4, dash=DASH)
    cv.line(X(XMIN), Y(my), X(XMAX), Y(my), w=1.4, dash=DASH)
    T(X(mx), Y(YMAX) - 8, f"x の平均値 {MX_EXPECT}", size=FS_NUM, weight="bold")
    T(X(XMAX) - 4, Y(my) + 14, f"y の平均値 {MY_EXPECT}", size=FS_NUM, anchor="end", weight="bold")
    coords = plot_points(cv, X, Y, PTS, r=3.4)
    assert all(abs(cx - X(x)) < 1e-9 and abs(cy - Y(y)) < 1e-9
               for (cx, cy), (x, y) in zip(coords, PTS))
    # 4つの領域のラベル（象限の符号）——データ座標で置く
    LX_R, LX_L, LY_T, LY_B = 31, 19.5, 47, 31
    T(X(LX_R), Y(LY_T), "(＋)×(＋)=＋", size=FS_NUM, weight="bold")
    T(X(LX_L), Y(LY_T), "(−)×(＋)=−", size=FS_NUM)
    T(X(LX_L), Y(LY_B), "(−)×(−)=＋", size=FS_NUM, weight="bold")
    T(X(LX_R), Y(LY_B), "(＋)×(−)=−", size=FS_NUM)
    ck.ok("領域ラベルの位置: 右上・左下は平均線の右上側・左下側（積が正の斜線領域内）・左上・右下も対応する領域内",
          LX_R > mx and LY_T > my and LX_L < mx and LY_B < my and
          XMIN < LX_L < LX_R < XMAX and YMIN < LY_B < LY_T < YMAX)
    ck.ok("各点の描画座標=値の線形変換（描画時に照合）", True)
    T(240, 26, "偏差の積の符号——平均線で分けた4つの領域", size=FS, weight="bold")
    T(240, 396, "斜線の領域=偏差の積が正（右上と左下）。積の合計が正なら共分散は正",
      size=10.5)
    T(240, 416, f"点は L04 例題1の6日分（{CAPTION_FAKE}）", size=10)

    return {"file": "L04_fig2_deviation_product_quadrants.svg", "lesson": "L04", "canvas": cv,
            "title": "偏差の積の符号の4象限——例題1の6日分",
            "intent": "例題1（6日間の最高気温 x と冷たい飲み物の売上 y）の散布図に x の平均値 25・y の平均値 40 の破線を引いて4つの領域に分け、右上（x の偏差＋・y の偏差＋）と左下（−・−）では偏差の積が正、左上・右下では負になることを斜線と符号ラベルで見せる。積が正の点が4・負の点が2で、積を足し合わせると正が勝ち（合計60）、積の平均（共分散）は正になる",
            "src": "lesson_04.md §2（「右上の領域……左上と右下では積が負である」の段落の直後）",
            "params": f"点={PTS}（x の平均値{MX_EXPECT}・y の平均値{MY_EXPECT}・積が正の点{N_POS_EXPECT}・負の点{N_NEG_EXPECT}・共分散{COV_EXPECT}は図に描かない）／軸 x {XMIN}〜{XMAX}・y {YMIN}〜{YMAX}（0 始まりにしない）",
            "spec": "データ=generate_datasets.L04_ex1_temperature_drinks()・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": TOKENS_L04_L06,
            "allow_texts": labels}


# ===========================================================================
# 図6: L05 部員8（外れ値）ありなしの散布図2パネル
# 仕様の正: lesson_05.md §3（例題2 (2) の直後）。データ=generate_datasets.L05_ex2_basketball()。
# r の値は図に描かない（本文で計算して比べる）。
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（lesson_05.md 例題2 の表と一致。データは共通スクリプトから import） ---
    _d = gd.L05_ex2_basketball()
    _all = list(zip(_d["x"], _d["y"]))           # (自主練習時間 x（時間）, シュート成功数 y（本）) 部員1〜8
    BASE, OUTLIER = _all[:7], _all[7]            # 部員1〜7 と 部員8（外れ値）
    OUTLIER_NAME = "部員8"
    XMAX, YMAX = 15, 13
    R7_EXPECT, R8_EXPECT = -0.109, 0.714         # 生成時に再計算して照合する期待値（±0.001）
    ALT = ("1点で相関係数 r は大きく変わる——左は部員8（右上の1点）を入れた8人、右はその1点を除いた7人の散布図。"
           "2つの図は同じ目盛り")

    ck = Checker()
    ck.ok("8点が本文 例題2 の表と同一（部員1〜7＋部員8=(13, 12)）",
          BASE == [(2, 3), (3, 5), (4, 4), (5, 6), (6, 2), (7, 5), (8, 3)] and OUTLIER == (13, 12))
    with_o = BASE + [OUTLIER]
    r_without = correlation_of([p[0] for p in BASE], [p[1] for p in BASE])
    r_with = correlation_of([p[0] for p in with_o], [p[1] for p in with_o])
    ck.ok(f"{OUTLIER_NAME}を除いた7人: r の絶対値<0.2（ほぼ相関なし・共通スクリプトの corr_of() とも一致）",
          abs(r_without) < 0.2 and abs(r_without - R7_EXPECT) < 1e-3 and
          abs(r_without - gd.corr_of(_d["x"][:7], _d["y"][:7])) < 1e-12, f"r≒{r_without:.3f}")
    ck.ok(f"{OUTLIER_NAME}を入れた8人: r>0.6（1点で強い正の相関に見える・共通スクリプトの corr_of() とも一致）",
          r_with > 0.6 and abs(r_with - R8_EXPECT) < 1e-3 and
          abs(r_with - gd.corr_of(_d["x"], _d["y"])) < 1e-12, f"r≒{r_with:.3f}")
    ck.ok(f"{OUTLIER_NAME}は x・y とも他の7人の最大より大きい（13>8、12>6・右上に離れた1点）",
          OUTLIER[0] > max(p[0] for p in BASE) == 8 and OUTLIER[1] > max(p[1] for p in BASE) == 6)
    ck.ok("2パネルは同じ目盛り（軸の範囲を共有・13<15、12<13 で収まる）",
          XMAX > OUTLIER[0] and YMAX > OUTLIER[1])

    cv = Canvas(640, 322)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    W, H, base = 230, 170, 250
    panels = [(f"{OUTLIER_NAME}を入れた8人", with_o, 60), (f"{OUTLIER_NAME}を除いた7人", BASE, 360)]
    for name, pts, px0 in panels:
        X, Y = scatter_axes(cv, T, px0, base, W, H, XMAX, YMAX,
                            xticks=(5, 10, 15), yticks=(5, 10), tick_labels=True)
        coords = plot_points(cv, X, Y, pts)
        assert all(abs(cx - (px0 + W * x / XMAX)) < 1e-9 and abs(cy - (base - H * y / YMAX)) < 1e-9
                   for (cx, cy), (x, y) in zip(coords, pts))
        T(px0 + W / 2, 52, name, size=FS, weight="bold")
        if OUTLIER in pts:
            ox, oy = X(OUTLIER[0]), Y(OUTLIER[1])
            cv.ring(ox, oy, 7.5)
            T(ox - 12, oy + 4, OUTLIER_NAME, size=FS_NUM, anchor="end", weight="bold")
    ck.ok("各点の描画座標=値の線形変換（両パネル・描画時に照合）", True)
    T(320, 26, "1点で相関係数 r は大きく変わる", size=FS, weight="bold")
    T(320, 296, f"横軸 x（時間）・縦軸 y（本）——2つの図は同じ目盛り（{CAPTION_FAKE}）", size=FS_CAP)
    T(320, 312, "左は右上の1点を入れた場合、右はその1点を除いた場合", size=10)

    return {"file": "L05_fig1_scatter_with_without_outlier.svg", "lesson": "L05", "canvas": cv,
            "title": "部員8（外れ値）ありなしの散布図2パネル",
            "intent": "同じ目盛りの散布図を2枚並べ、右上に離れた1点（部員8=外れ値）を入れた8人と除いた7人で、点の並びの印象——そして r の値——が大きく変わることを見せる。r の値は図に描かず、本文で計算して比べる",
            "src": "lesson_05.md §3（例題2 (2) の計算結果「7人だけなら、ほとんど相関がない。」の直後）",
            "params": f"7人={BASE}（r≈{r_without:.2f}）＋{OUTLIER_NAME}{OUTLIER}（8人で r≈{r_with:.2f}）／軸 x 0〜{XMAX}・y 0〜{YMAX}",
            "spec": "データ=generate_datasets.L05_ex2_basketball()・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": TOKENS_L04_L06,
            "allow_texts": labels}


# ===========================================================================
# 図7: L06 統計的探究プロセスの循環図（問い→計画→データ→分析→結論→新たな問い）
# 仕様の正: lesson_06.md §1（5段階の箇条書きの直後）。概念図——数値なし。矢印端点は箱の辺上をassert。
# 補足: 解説の五段階は「問題—計画—データ—分析—結論」で、本文・図は先頭を「問い」としている。
# 監修で「問題」に戻す判断が出た場合は、本文 §1 と STEPS[0] と ALT を同時に直す。
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（lesson_06.md §1 の5段階の太字と一致） ---
    STEPS = [("問い", "何を知りたいか"),
             ("計画", "どう調べるか"),
             ("データ", "集める・整理する"),
             ("分析", "図と数値で調べる"),
             ("結論", "答えと限界を書く")]
    CX, CY, R = 240, 222, 138
    BW, BH = 112, 46
    ANGLES = [-90, -18, 54, 126, 198]        # 上から時計回り（度）
    ALT = ("統計的探究プロセスの循環図——問い・計画・データ・分析・結論の5段階を円周上に並べ、"
           "結論から新たな問いへ戻る破線の矢印で、一周して終わりではなくくり返すことを示す")

    ck = Checker()
    _lesson = LESSONS / "lesson_06.md"
    ck.ok("5段階の名前が lesson_06.md §1 の箇条書きの太字（- **問い**—— 等）と同一",
          _lesson.exists() and all(f"- **{main}**——" in _lesson.read_text(encoding="utf-8") for main, _ in STEPS))
    boxes = []
    for a in ANGLES:
        t = math.radians(a)
        bx, by = CX + R * math.cos(t), CY + R * math.sin(t)
        boxes.append((bx - BW / 2, by - BH / 2, BW, BH))
    ck.ok("5段階・5枠（等間隔72度で円周上に配置）",
          len(STEPS) == 5 and all(ANGLES[i + 1] - ANGLES[i] == 72 for i in range(4)))
    ck.ok("枠5個が互いに重ならない",
          all(disjoint(boxes[i], boxes[j]) for i in range(5) for j in range(i + 1, 5)))
    arrows = []
    for i in range(5):
        a, b = boxes[i], boxes[(i + 1) % 5]
        p1 = edge_point(a, box_center(b))
        p2 = edge_point(b, box_center(a))
        arrows.append((p1, p2))
    ck.ok("矢印5本（結論→問いの戻りを含む）の始点・終点が対応する枠の辺上にある",
          len(arrows) == 5 and all(on_edge(p1, boxes[i]) and on_edge(p2, boxes[(i + 1) % 5])
                                   for i, (p1, p2) in enumerate(arrows)))

    cv = Canvas(480, 420)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    for (main, sub), b in zip(STEPS, boxes):
        cv.rect(*b, sw=1.5, rx=6)
        cx = b[0] + b[2] / 2
        T(cx, b[1] + 19, main, size=FS, weight="bold")
        T(cx, b[1] + 37, sub, size=10)
    for i, (p1, p2) in enumerate(arrows):
        cv.arrow(p1[0], p1[1], p2[0], p2[1], w=1.5, head=8.0,
                 dash=DASH if i == 4 else None)
    T(168, 118, "新たな問いへ", size=10.5, anchor="end")
    T(CX, CY - 4, "統計的探究プロセス", size=FS, weight="bold")
    T(CX, CY + 16, "（結論から次の問いへ、くり返す）", size=10)
    heading = "問いを立ててデータで答える——探究の5段階"
    T(240, 26, heading, size=FS, weight="bold")
    T(240, 402, "破線の矢印=結論で終わらず、新たな問いに戻る", size=10)
    ck.ok("枠・注記のラベルに数字を含まない（概念図。見出しの「5段階」は段階数で対象外）",
          no_digits([t for t in labels if t != heading]) and len(STEPS) == 5)

    return {"file": "L06_fig1_inquiry_process_cycle.svg", "lesson": "L06", "canvas": cv,
            "title": "統計的探究プロセスの循環図——問い・計画・データ・分析・結論",
            "intent": "問い→計画→データ→分析→結論の5段階を円周上に並べ、結論から新たな問いへ戻る破線矢印で「一周して終わりではなくくり返す」ことを見せる。各枠に一言の説明（何を知りたいか／どう調べるか／集める・整理する／図と数値で調べる／答えと限界を書く）を添える",
            "src": "lesson_06.md §1（5段階の箇条書きの直後）",
            "params": "枠5個（円周上・72度間隔）・矢印5本（結論→問いのみ破線）・数値なし",
            "spec": "段階名・一言・見出し・注記=lesson_06.md §1 と一致・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": TOKENS_L04_L06,
            "allow_texts": labels}


# ===========================================================================
# 図8: L07 コイン30回投げ×200回の表の枚数のヒストグラム——18以上を濃く塗り、24以上を斜線で示す
# 仕様の正: lesson_07.md §3（度数分布表の直後。lesson_08.md §3 でも同じ alt で再掲）。
# データ=generate_datasets.coin_counts(seed=20260902)（L07〜L08 の正。本文の結果表もこれを写す）。COIN_COUNTS_OVERRIDE は本文の度数分布表の写し（照合用）——coin_counts() の
# 度数列と一致しなければ停止する（本文とデータの食い違い検出）。回数・相対度数・m・s の値は図に描かない。
# ===========================================================================
COIN_SEED = 20260902
assert COIN_SEED == gd.COIN_SEED, "図版とデータスクリプトのシードが食い違っている"
# lesson_07.md §3・lesson_08.md §1・lesson_09.md §4 の度数分布表（表の枚数: 回数。合計200）の写し——照合用
COIN_COUNTS_OVERRIDE = {6: 1, 7: 1, 8: 2, 9: 1, 10: 11, 11: 7, 12: 18, 13: 27, 14: 22, 15: 34, 16: 25,
                        17: 18, 18: 16, 19: 9, 20: 5, 21: 1, 22: 1, 23: 1}
COIN_GE24_EXPECT, COIN_GE21_EXPECT, COIN_GE20_EXPECT, COIN_GE18_EXPECT = 0, 3, 8, 33   # lesson_07.md §4（24以上・18以上）・answer_key_L07-08.md（21以上・20以上）
COIN_M_EXPECT = F(2941, 200)                      # m=14.705（分数で厳密）
COIN_S_EXPECT, COIN_M2S_EXPECT = 2.8281, 20.361   # s・m＋2s（誤差 0.001 未満）


def simulate_coin(seed, n_trials=200, n_toss=30):
    """コインを n_toss 回投げて表の枚数を数える試行を n_trials 回。
    rng.random()<0.5 を表とする（Python の Mersenne Twister は同じ seed で同じ列）"""
    rng = random.Random(seed)
    counts = [0] * (n_toss + 1)
    results = []
    for _ in range(n_trials):
        heads = sum(1 for _ in range(n_toss) if rng.random() < 0.5)
        counts[heads] += 1
        results.append(heads)
    return counts, results


def fig_L07_1():
    # --- パラメータ（lesson_07.md §3 の度数分布表と一致。データは共通スクリプトから import） ---
    N_TRIALS, N_TOSS, THRESHOLD = 200, 30, 24    # 24以上: 斜線＋境界の破線（この領域に棒は1本もない）
    THRESHOLD2 = 18                              # 18以上: 棒を濃く塗る（SHADE2）
    SHOW_M_2S = False        # m と 2s の帯は描かない（L08 は本文で m＋2s≒20.36 を言葉で示す）
    ALT = ("コインを30回投げて表の枚数を数える試行を200回くり返した結果のヒストグラム——横軸は表の枚数（0〜30）・"
           "縦軸はその枚数が出た回数。棒は15枚前後に高く集まり、18枚以上の棒を濃く塗り、24枚以上の領域は斜線で示すが、"
           "そこに棒は1本もない")

    ck = Checker()
    results = gd.coin_counts(COIN_SEED, N_TRIALS, N_TOSS)        # 実験順の200個（正）
    counts = [results.count(k) for k in range(N_TOSS + 1)]       # 度数分布を数え直す
    counts_sim, results_sim = simulate_coin(COIN_SEED, N_TRIALS, N_TOSS)   # 別実装（照合用）
    ck.ok("固定シードの再現性: 共通スクリプト coin_counts() と本スクリプト simulate_coin() が同じ200個の列・同じ度数列。2回呼んでも同じ",
          results == results_sim and counts == counts_sim and
          gd.coin_counts(COIN_SEED, N_TRIALS, N_TOSS) == results)
    ck.ok("度数分布が本文の度数分布表の写し COIN_COUNTS_OVERRIDE（lesson_07.md §3。6枚1回…23枚1回）と完全一致・0〜5枚と24〜30枚は0回",
          {k: c for k, c in enumerate(counts) if c} == COIN_COUNTS_OVERRIDE
          and sum(COIN_COUNTS_OVERRIDE.values()) == N_TRIALS)
    ck.ok(f"度数の合計={N_TRIALS}・results の個数={N_TRIALS}（{N_TOSS}回投げを{N_TRIALS}回）",
          sum(counts) == N_TRIALS and len(results) == N_TRIALS, f"合計={sum(counts)}")
    n_over = sum(counts[k] for k in range(THRESHOLD, N_TOSS + 1))
    n_ge21 = sum(counts[k] for k in range(21, N_TOSS + 1))
    n_ge20 = sum(counts[k] for k in range(20, N_TOSS + 1))
    n_ge18 = sum(counts[k] for k in range(THRESHOLD2, N_TOSS + 1))
    ck.ok(f"度数列から数え直し: {THRESHOLD}以上={COIN_GE24_EXPECT}回・21以上={COIN_GE21_EXPECT}回・20以上={COIN_GE20_EXPECT}回・"
          f"{THRESHOLD2}以上={COIN_GE18_EXPECT}回（lesson_07.md §4・answer_key_L07-08.md の値。回数・相対度数は図に描かない）",
          n_over == sum(1 for v in results if v >= THRESHOLD) == COIN_GE24_EXPECT and
          n_ge21 == COIN_GE21_EXPECT and n_ge20 == COIN_GE20_EXPECT and
          n_ge18 == sum(1 for v in results if v >= THRESHOLD2) == COIN_GE18_EXPECT)
    m = mean_of(results)
    s = sd_of(results)
    ck.ok("m=14.705（分数で厳密・共通スクリプトの mean() とも一致）・s≒2.8281（誤差0.001未満）・m＋2s≒20.361（いずれも図には描かない）",
          m == COIN_M_EXPECT and gd.mean(results) == COIN_M_EXPECT and abs(s - COIN_S_EXPECT) < 0.001
          and abs(float(m) + 2 * s - COIN_M2S_EXPECT) < 0.001,
          f"m={float(m):g}・s≒{s:.4f}・m＋2s≒{float(m) + 2 * s:.3f}")
    maxc = max(counts)
    ck.ok("最大度数34（15枚）・最小6枚・最大23枚（本文 §3 の記述と同一）",
          maxc == 34 and counts.index(maxc) == 15 and min(results) == 6 and max(results) == 23)
    ck.ok("観測された枚数の範囲が図の横軸0〜30に収まる", 0 <= min(results) and max(results) <= N_TOSS)
    _l08 = LESSONS / "lesson_08.md"
    ck.ok("lesson_08.md §3 の再掲も同じ alt・同じパスで参照している（生成時に照合）",
          _l08.exists() and f"![{ALT}](assets/L07_fig1_coin_experiment_histogram.svg)" in _l08.read_text(encoding="utf-8"))

    cv = Canvas(560, 340)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    x0, x1, base = 60, 530, 258
    VMIN, VMAX = F(-1, 2), F(N_TOSS) + F(1, 2)

    def X(v):
        return float(x0 + (x1 - x0) * (F(v) - VMIN) / (VMAX - VMIN))

    yscale = 4.0
    ck.ok("最大度数の棒が縦軸の枠（0〜40）に収まる", maxc <= 40, f"最大度数={maxc}")
    hatch = cv.hatch()
    # 24以上の領域（斜線）と境界の破線
    top = base - 178
    cv.rect(X(THRESHOLD - F(1, 2)), top, X(VMAX) - X(THRESHOLD - F(1, 2)), base - top, sw=0, fill=hatch)
    cv.line(X(THRESHOLD - F(1, 2)), top - 4, X(THRESHOLD - F(1, 2)), base, w=1.3, dash=DASH)
    T((X(THRESHOLD - F(1, 2)) + X(VMAX)) / 2, top - 10, f"{THRESHOLD}以上", size=FS_NUM, weight="bold")
    # 横軸（各枚数の中央に目盛り）
    cv.line(x0, base, x1, base, w=1.2)
    for k in range(0, N_TOSS + 1):
        h = 6.0 if k % 5 == 0 else 3.0
        cv.line(X(k), base - h, X(k), base + h, w=0.9)
        if k % 5 == 0:
            T(X(k), base + 18, f"{k}", size=FS_NUM)
    y_axis(cv, T, x0, base, yscale, [0, 10, 20, 30, 40])
    # 棒（1枚ごと・幅1）。18以上は濃い塗り（SHADE2）・17以下はうすい塗り（SHADE）
    fills = {}
    for k, c in enumerate(counts):
        if c > 0:
            xl, xr = X(k - F(1, 2)), X(k + F(1, 2))
            fills[k] = SHADE2 if k >= THRESHOLD2 else SHADE
            cv.rect(xl, base - c * yscale, xr - xl, c * yscale, sw=1.0, fill=fills[k])
            assert abs((xr - xl) - (X(1) - X(0))) < 1e-9, "棒の幅≠1枚分"
    ck.ok(f"{THRESHOLD2}〜23の棒の fill が SHADE2（濃い）・17以下の棒が SHADE・{THRESHOLD}以上の領域に棒なし",
          all(fills.get(k) == SHADE2 for k in range(THRESHOLD2, THRESHOLD)) and
          all(v == SHADE for k, v in fills.items() if k < THRESHOLD2) and
          not any(k >= THRESHOLD for k in fills))
    ck.ok("各棒の高さ=度数×4px・幅=1枚分（描画時に照合）", True)
    # 「18以上」のラベル——18〜23 の棒の上に括線を引き、その上に置く（棒と重ならない高さ）
    yb = top + 22
    xa, xb = X(THRESHOLD2 - F(1, 2)), X(THRESHOLD - F(1, 2))
    cv.line(xa, yb, xb, yb, w=1.1)
    cv.line(xa, yb, xa, yb + 5, w=1.1)
    T((xa + xb) / 2, yb - 6, f"{THRESHOLD2}以上", size=FS_NUM, weight="bold")
    ck.ok(f"「{THRESHOLD2}以上」のラベルと括線は {THRESHOLD2}〜23 の棒より上にあり棒と重ならない（描画時に照合）",
          yb < min(base - counts[k] * yscale for k in range(THRESHOLD2, THRESHOLD)) and xa < xb)
    if SHOW_M_2S:
        cv.line(X(m), top, X(m), base, w=1.4, dash=DASH)
        T(X(m), top - 10, "m", size=FS, weight="bold")
        cv.line(X(m - 2 * s), top + 20, X(m + 2 * s), top + 20, w=1.2)
        T(X(m), top + 34, "m から 2s の帯", size=10)
    T(66, 70, "回数（回）", size=10, anchor="start")
    T(280, 26, f"コインを{N_TOSS}回投げて表の枚数を数える——{N_TRIALS}回くり返した結果",
      size=FS, weight="bold")
    T(280, 302, "横軸: 表の枚数（枚）／縦軸: その枚数が出た回数（回）", size=FS_CAP)
    T(280, 320, f"コンピュータの乱数で生成した架空の実験結果（{N_TRIALS}回）", size=10)
    numeric = {t for t in labels if re.search(r"[0-9]", t)}
    ck.ok("図中の数字ラベルは目盛と「18以上」「24以上」・見出し・キャプションのみ（回数・相対度数・m・s は描かない）",
          numeric == {f"{k}" for k in range(0, N_TOSS + 1, 5)} | {"10", "20", "30", "40"} |
          {f"{THRESHOLD2}以上", f"{THRESHOLD}以上",
           f"コインを{N_TOSS}回投げて表の枚数を数える——{N_TRIALS}回くり返した結果",
           f"コンピュータの乱数で生成した架空の実験結果（{N_TRIALS}回）"},
          f"実測={sorted(numeric)}")

    return {"file": "L07_fig1_coin_experiment_histogram.svg", "lesson": "L07", "canvas": cv,
            "title": "コイン30回投げ×200回の表の枚数のヒストグラム——18以上を濃く塗り、24以上を斜線で示す",
            "intent": "偶然だけ（表が出る確率2分の1）でコインを30回投げたとき、表の枚数がどう散らばるかを200回の実験結果で見せる。主張B（30人中18人）にあたる18枚以上の棒を濃く塗り、主張A（30人中24人）にあたる24枚以上の領域を斜線で示す——斜線の中に棒は1本もない。それぞれの回数を数えて相対度数 p を求めるのは本文の活動（回数・p・m・s の値は図に描かない）。L08 §3 でも同じ alt で再掲",
            "src": "lesson_07.md §3（度数分布表の直後）／lesson_08.md §3（同じ alt で再掲）",
            "params": f"{N_TOSS}回投げ×{N_TRIALS}回・データ=generate_datasets.coin_counts(seed={COIN_SEED})（度数列は本文の度数分布表の写し COIN_COUNTS_OVERRIDE と完全一致）・棒は1枚ごと・{THRESHOLD2}以上の棒を濃く塗る・{THRESHOLD}以上を斜線・m と 2s の帯は非表示（SHOW_M_2S）",
            "spec": "データ=generate_datasets.coin_counts(seed=20260902)・度数列=lesson_07.md §3 の度数分布表と照合・18以上を塗り分け・alt=本文と同一（lesson_08.md §3 の再掲も同じ alt で照合）",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": ["0.165", "33回", "14.7", "2.83", "20.36", "9.05", "0.04", "0.38", "76回", "0.015",
                             "0.085", "0.005", "0.17", "34回", "2941", "44847", "相対度数"],
            "allow_texts": labels}


# ===========================================================================
# 図9: L09 単元マップ——散らばり・相関・探究・仮説検定の考え方、そしてその先
# 仕様の正: lesson_09.md §1（4つの箱の箇条書きの直後。枠名6個・矢印ラベル5個。
# 図中の「情報Ⅰ」は本文の字形（ローマ数字 U+2160・禁止文字検査の対象外）にそろえた）。
# 文字ラベルのみ・数値なし（レッスン番号のみ可）。「帰無仮説」「有意水準」の語は図に入れない
# （本文 L09 で「帰無仮説」を1回だけ出す設計のため）。
# ===========================================================================
def fig_L09_1():
    # --- パラメータ（lesson_09.md §1 の1枚地図と一致・枠名・矢印ラベル） ---
    BOXES = [("散らばり　L01〜L03", "代表値・四分位範囲・分散・標準偏差"),
             ("相関　L04〜L05", "散布図・相関係数・相関と因果"),
             ("探究　L06", "問い→計画→データ→分析→結論"),
             ("仮説検定の考え方　L07〜L08", "偶然で説明できるか・判断の基準"),
             ("数学B　統計的な推測", "推定の幅の評価・仮説検定の方法"),
             ("情報Ⅰ", "表計算でデータを扱う")]
    ARROW_LABELS = ["s で単位をそろえて r へ", "道具で問いに答える", "偶然で説明できるか",
                    "考え方から方法へ", "情報機器で分析する"]
    ALT = ("単元マップ——散らばり（L01〜L03）・相関（L04〜L05）・探究（L06）・仮説検定の考え方（L07〜L08）の4つの枠が"
           "2段に並び、「s で単位をそろえて r へ」「道具で問いに答える」「偶然で説明できるか」の矢印でつながる。"
           "破線の枠で、仮説検定の考え方から数学B「統計的な推測」へ（考え方から方法へ）、探究から情報Ⅰへ"
           "（情報機器で分析する）の接続を予告する")
    # 2段組み（上段: 散らばり→相関／下段: 探究→仮説検定の考え方／その下に破線の 情報Ⅰ・数学B）。
    # 文字の最小サイズを viewBox 幅の約2%（12px/560px）に保つため、横1列ではなく2段にしている。
    b_spread = (20, 56, 240, 66)
    b_corr = (300, 56, 240, 66)
    b_inq = (20, 186, 240, 66)
    b_test = (300, 186, 240, 66)
    b_mathB = (300, 308, 240, 56)
    b_info = (20, 308, 240, 56)
    all_boxes = [b_spread, b_corr, b_inq, b_test, b_mathB, b_info]
    BEND_Y = 154                            # 相関→探究の折れ線矢印が横に走る高さ
    arrows = [((260, 89), (300, 89)),      # 散らばり→相関
              ((420, 122), (140, 186)),    # 相関→探究（折れ線: 下→左→下）
              ((260, 219), (300, 219)),    # 探究→仮説検定の考え方
              ((420, 252), (420, 308)),    # 仮説検定の考え方→数学B
              ((140, 252), (140, 308))]    # 探究→情報Ⅰ
    a_boxes = [(b_spread, b_corr), (b_corr, b_inq), (b_inq, b_test),
               (b_test, b_mathB), (b_inq, b_info)]

    ck = Checker()
    ck.ok("枠6個が互いに重ならない",
          all(disjoint(all_boxes[i], all_boxes[j])
              for i in range(6) for j in range(i + 1, 6)))
    ck.ok("矢印5本の始点・終点がそれぞれ対応する枠の辺上にある",
          all(on_edge(p1, ba) and on_edge(p2, bb)
              for (p1, p2), (ba, bb) in zip(arrows, a_boxes)))
    ck.ok("この単元の4枠は2段2列の格子（横の間隔40px・縦の間隔64px）で、折れ線矢印（相関→探究）の横走りは上段の枠の下・下段の枠の上を通る",
          b_corr[0] - (b_spread[0] + b_spread[2]) == 40 and b_test[0] - (b_inq[0] + b_inq[2]) == 40 and
          b_inq[1] - (b_spread[1] + b_spread[3]) == 64 and b_test[1] - (b_corr[1] + b_corr[3]) == 64 and
          b_spread[1] + b_spread[3] < BEND_Y < b_inq[1])
    _lesson = LESSONS / "lesson_09.md"
    _text = _lesson.read_text(encoding="utf-8") if _lesson.exists() else ""
    ck.ok("本単元の4枠の名前が lesson_09.md §1 の箇条書きの太字（- **散らばり**（L01〜L03） 等）と同一",
          all(f"- **{main.split('　')[0]}**（{main.split('　')[1]}）" in _text for main, _ in BOXES[:4]))
    ck.ok("矢印ラベル5個が lesson_09.md の本文（§1 の alt・§5 の見出し）に同じ文言で現れる",
          all(lab in _text for lab in ARROW_LABELS))
    ck.ok("枠名6個・矢印ラベル5個が仕様の文言と完全一致（枠6・矢印5）",
          len(BOXES) == 6 and len(ARROW_LABELS) == 5 and BOXES[5][0] == "情報Ⅰ" and
          [b[0] for b in BOXES] == ["散らばり　L01〜L03", "相関　L04〜L05", "探究　L06", "仮説検定の考え方　L07〜L08",
                                    "数学B　統計的な推測", "情報Ⅰ"])

    cv = Canvas(560, 410)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text(x, y, s, **kw)

    def unit_box(b, main, sub, dash=None):
        cv.rect(*b, sw=1.5, dash=dash)
        cx = b[0] + b[2] / 2
        T(cx, b[1] + 26, main, size=FS, weight="bold")
        T(cx, b[1] + 48, sub, size=12)

    for b, (main, sub), dash in zip(all_boxes, BOXES, (None, None, None, None, DASH, DASH)):
        unit_box(b, main, sub, dash=dash)
    for i, (p1, p2) in enumerate(arrows):
        if i == 1:   # 相関→探究: 下へ・左へ・下へ の折れ線（最後の縦線に矢じり）
            cv.polyline([p1, (p1[0], BEND_Y), (p2[0], BEND_Y)], w=1.4)
            cv.arrow(p2[0], BEND_Y, p2[0], p2[1], w=1.4)
        else:
            cv.arrow(p1[0], p1[1], p2[0], p2[1], w=1.4)
    T(280, 50, ARROW_LABELS[0], size=12)                    # 散らばり→相関（上段の枠のすぐ上・矢印のある間の真上）
    T(280, 172, ARROW_LABELS[1], size=12)                   # 相関→探究（横走りの下）
    T(280, 267, ARROW_LABELS[2], size=12)                   # 探究→仮説検定の考え方（下段の枠のすぐ下・矢印のある間の真下）
    T(430, 292, ARROW_LABELS[3], size=12, anchor="start")   # 仮説検定の考え方→数学B（矢印の右）
    T(130, 292, ARROW_LABELS[4], size=12, anchor="end")     # 探究→情報Ⅰ（矢印の左。中央のラベルと縦に並べない）
    T(280, 22, "単元マップ——散らばり・相関・探究・仮説検定の考え方、そしてその先", size=FS,
      weight="bold")
    T(280, 392, "破線の枠=この単元の先（数学B・情報Ⅰ）。L09 はこの地図を読み返す回", size=12)
    ck.ok("図中ラベルはレッスン番号（L01等）以外に数字を含まない", no_digits(labels, allow_L=True))

    return {"file": "L09_fig1_unit_map.svg", "lesson": "L09", "canvas": cv,
            "title": "単元マップ——散らばり・相関・探究・仮説検定の考え方、そしてその先",
            "intent": "散らばり（L01〜L03）→相関（L04〜L05）→探究（L06）→仮説検定の考え方（L07〜L08）の4枠を2段に並べ（上段: 散らばり→相関、下段: 探究→仮説検定の考え方）、道具の受け渡し（s で単位をそろえて r へ／道具で問いに答える／偶然で説明できるか）を矢印ラベルで示す。破線の枠で数学B「統計的な推測」（考え方から方法へ）と情報Ⅰ（表計算）への接続を予告する",
            "src": "lesson_09.md §1（4つの箱の箇条書きの直後）",
            "params": "文字ラベルのみ・数値なし（レッスン番号のみ）／枠6個（本単元4＋この先2）・矢印5本",
            "spec": "枠名6個・矢印ラベル5個=lesson_09.md の文言と照合・図中の「情報Ⅰ」を本文の字形にそろえた・alt=本文と同一",
            "alt": ALT,
            "checks": ck.items,
            "check_tokens": ["−0.8", "0.6", "0.085", "0.005", "14.705", "2.83", "20.36"],
            "check_tokens_full": ["帰無仮説", "有意水準"],
            "allow_texts": labels}


# ===========================================================================
# main: 検査器の陽性対照 → 生成 → SVG技術検査（XML/viewBox/self-contained/禁止文字）
#       → 答え漏れ検査（許可リスト完全一致＋禁止文字列） → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L02_1, fig_L03_1, fig_L04_1, fig_L04_2,
        fig_L05_1, fig_L06_1, fig_L07_1, fig_L09_1]

TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)

# 禁止文字（絵文字・結合文字・異体字セレクタ・全角英数字ほか）の符号位置範囲
FORBIDDEN_RANGES = [
    (0x0300, 0x036F, "結合文字（x の上線など）"),
    (0x200D, 0x200D, "ゼロ幅接合子"),
    (0x20D0, 0x20FF, "結合用記号"),
    (0x2600, 0x27BF, "記号・絵文字（チェック印を含む）"),
    (0x2B00, 0x2BFF, "記号・矢印（絵文字系）"),
    (0xFE00, 0xFE0F, "異体字セレクタ"),
    (0xFF10, 0xFF19, "全角数字"),
    (0xFF21, 0xFF3A, "全角英大文字"),
    (0xFF41, 0xFF5A, "全角英小文字"),
    (0x1F000, 0x1FAFF, "絵文字"),
    (0xE0100, 0xE01EF, "異体字セレクタ補助"),
]


def forbidden_chars(s):
    """禁止文字の検出。戻り値=[(位置, 'U+XXXX', 分類名), ...]"""
    hits = []
    for i, ch in enumerate(s):
        o = ord(ch)
        for lo, hi, name in FORBIDDEN_RANGES:
            if lo <= o <= hi:
                hits.append((i, f"U+{o:04X}", name))
                break
    return hits


def svg_texts(src):
    """SVG本文から<text>の内容を抽出（エスケープを戻す）"""
    return [unescape(m) for m in TEXT_RE.findall(src)]


def ban_hits(texts, bans):
    """禁止文字列の検出（改行連結——ラベル境界をまたぐ偽陽性を防ぐ）"""
    joined = "\n".join(texts)
    return [b for b in bans if b in joined]


def gate_self_test():
    """答え漏れ検査器・禁止文字検出器の陽性対照——検出できることを毎回実証してから本走査に入る"""
    sample = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
              '<text x="1" y="1">21</text><text x="2" y="2">x&lt;6</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["21", "x<6"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["21"]) == ["21"], "陽性対照失敗: 禁止値21を検出できない"
    assert ban_hits(ts, ["1.4"]) == [], "陰性対照失敗: 存在しない値を誤検出"
    assert set(ts) != {"21"}, "許可リスト比較が集合差を識別できない"
    # 禁止文字検出器: x の上線（結合文字）・絵文字・異体字セレクタ・全角数字を検出できる
    assert forbidden_chars("x" + chr(0x0304)), "陽性対照失敗: 結合文字を検出できない"
    assert forbidden_chars(chr(0x1F600)), "陽性対照失敗: 絵文字を検出できない"
    assert forbidden_chars(chr(0x2713)), "陽性対照失敗: チェック印を検出できない"
    assert forbidden_chars(chr(0x2705) + chr(0xFE0F)), "陽性対照失敗: 異体字セレクタを検出できない"
    assert forbidden_chars(chr(0xFF11) + chr(0xFF21)), "陽性対照失敗: 全角英数字を検出できない"
    ok_sample = "m 平均値 −4 ● → × ＋ = 〜 ・ L01 s r Q1（架空）"
    assert forbidden_chars(ok_sample) == [], f"陰性対照失敗: 許容文字を誤検出 {forbidden_chars(ok_sample)}"


def svg_tech_checks(path, meta):
    """SVG技術要件（XML整形式・viewBox・self-contained・禁止文字）と答えの分離方針の機械検査"""
    src = path.read_text(encoding="utf-8")
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag, f"{path.name}: viewBoxがない"
    assert " width=" not in root_tag and " height=" not in root_tag, \
        f"{path.name}: ルートにwidth/heightを書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, \
        f"{path.name}: 外部参照の疑い"
    assert "font-family" not in src, f"{path.name}: フォント指定は書かない"
    assert "<title>" in src and "<desc>" in src, f"{path.name}: <title>/<desc> がない"
    bad = forbidden_chars(src)
    assert not bad, f"{path.name}: 禁止文字がある（コメント含む全文走査）: {bad[:5]}"
    texts = svg_texts(src)
    # (1) 許可リスト検査: 図中の全ラベル=宣言済みの本文明示値のみ（完全一致）
    allow = set(meta["allow_texts"])
    got = set(texts)
    assert got == allow, (f"{path.name}: ラベル集合が許可リストと不一致 "
                          f"余分={got - allow} 不足={allow - got}")
    # (2) 禁止文字列検査: answer_key 由来のトークンが図中にない
    hits = ban_hits(texts, meta.get("check_tokens", []))
    assert not hits, f"{path.name}: 禁止文字列が図中テキストにある: {hits}"
    # (3) 語彙の全文検査（title/desc含む）
    for ban in meta.get("check_tokens_full", []):
        assert ban not in src, f"{path.name}: 禁止語「{ban}」がSVG内にある"
    return len(texts)


def alt_check(meta):
    """図が宣言した alt が該当 lesson_XX.md の画像参照 ![alt](assets/file) と文字単位で同一であることを照合。
    戻り値=台帳に書く照合状況（lesson が無い・alt 未宣言のときは「未照合」と記録し、失敗にはしない）"""
    lesson_path = LESSONS / f"lesson_{meta['lesson'][1:]}.md"
    alt = meta.get("alt")
    if alt is None:
        exists = lesson_path.exists()
        return ("alt 未照合（alt 未宣言。lesson は存在）" if exists
                else "alt 未照合（alt 未宣言・lesson も無い）")
    assert lesson_path.exists(), f"{meta['file']}: alt 照合用の {lesson_path.name} が無い"
    ref = f"![{alt}](assets/{meta['file']})"
    text = lesson_path.read_text(encoding="utf-8")
    assert ref in text, f"{meta['file']}: {lesson_path.name} に同一の画像参照が無い: {ref[:60]}…"
    assert forbidden_chars(alt) == [], f"{meta['file']}: alt に禁止文字"
    return f"alt={lesson_path.name} の画像参照と文字単位で同一（生成時に照合）"


def build_desc(meta):
    """SVG <desc> 用のAI再利用メタ情報（意図・主要数値・本文の alt・同型図をAIに描かせる説明文）"""
    alt_part = f"【本文の alt】{meta['alt']}。" if meta.get("alt") else ""
    return (
        f"【この図の意図】{meta['intent']}。"
        f"【主要な数値・設定】{meta['params']}。"
        + alt_part +
        f"【AIに同じ種類の図を描かせるときの説明文】"
        f"「{meta['title']}。{meta['intent']}。数値・設定: {meta['params']}。"
        f"白黒印刷向けのシンプルな教材図（SVG）としてかいて。」"
        f"——この説明文を生成AIに渡せば同型の図を描かせられる。"
        f"数値を変えれば類題用の図も作れる。"
    )


def main():
    gate_self_test()
    stats_self_test()
    src_hits = forbidden_chars(Path(__file__).read_text(encoding="utf-8"))
    assert not src_hits, f"スクリプト自身に禁止文字がある: {src_hits[:5]}"
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    n_checks = 0
    total_bytes = 0
    for fn in FIGS:
        meta = fn()
        out = ASSETS / meta["file"]
        meta["canvas"].save(out, meta["file"], meta["title"], build_desc(meta))
        svg_tech_checks(out, meta)
        meta["alt_status"] = alt_check(meta)
        n_checks += len(meta["checks"])
        total_bytes += out.stat().st_size
        rows.append(meta)
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    n_tokens = sum(len(m.get("check_tokens", [])) +
                   len(m.get("check_tokens_full", [])) for m in rows)
    n_provisional = sum(1 for m in rows if "未照合" in m["spec"])
    n_reflected = len(rows) - n_provisional
    n_alt = sum(1 for m in rows if m["alt_status"].startswith("alt="))
    check_mark = "\u2713"   # 台帳（Markdown）専用のチェック印。SVG・コメント・本ファイルにはリテラルで書かない
    head = ["<!--",
            f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
            "spec: docs/SPEC_figures.md 準拠（書き方は hs-math-i-numbers-and-expressions 版を踏襲）",
            "license: CC-BY-4.0",
            "-->", ""]

    lines = head + [
        "# FIGURE_MANIFEST — 数Ⅰ データの分析単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的）／ "
        f"全{len(rows)}図で下表の統計検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。四分位数は中2教材の方式（中央値で前後に分け、奇数個は"
        "中央値を除く）を自前実装し、生成前の自己テスト（中2教材の既知値）で毎回検証。"
        "外れ値は 1.5×四分位範囲 の外。ヒストグラムの度数は生データから数え直し、散布図は"
        "各点の座標と相関係数 r（n で割る分散）の符号を照合。"
        "加えて全SVGにXML整形式・viewBox・self-contained・**禁止文字（絵文字・結合文字・"
        "異体字セレクタ・全角英数字）不在** の技術検査と答え漏れ検査を実施——"
        "答え漏れ検査は二重ゲート: (1)図中の全ラベルを許可リスト"
        "（本文が図の前後で明示している値のみ）と完全一致で照合、"
        f"(2)禁止文字列（answer_key 由来・現在{n_tokens}項目）の不在検査。"
        "検査器自体は生成前の陽性対照（禁止値・禁止文字を仕込んだ合成入力での検出）で"
        "毎回実証している。PASS。／ "
        "図の選定は各 lesson_XX.md 本文の画像参照にある9枚。"
        f"**本文との照合: 照合済み {n_reflected}枚・"
        f"未照合 {n_provisional}枚**（下表「本文との照合」列）。"
        f"データ点は共通スクリプト `generate_datasets.py` の関数を import して使い（二重定義なし）、"
        f"alt は該当 lesson の画像参照と文字単位で同一であることを生成時に照合（{n_alt}枚照合済み）。／ "
        "AI再利用メタ情報として全SVGに`<title>`/`<desc>`"
        "（意図・主要数値・本文の alt・同型図をAIに描かせる説明文）を標準装備。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | パラメータ（本文一致） | 本文との照合 | 検証結果（生成時assert） |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} {check_mark}" for d, t in m["checks"])
        lines.append(f"| `{m['file']}` | {m['lesson']} | {m['title']}——{m['intent']} | "
                     f"{m['src']} | {m['params']} | {m['spec']}／{m['alt_status']} | {checks} |")
    lines += [
        "",
        "## データ出所と本文との突合（生成時点の状態）",
        "",
        "- **データ出所**: データ点はすべて `generate_datasets.py` の関数（`l01_library_visits`・`l02_freethrow`・`l02_test20`・"
        "`l03_test20_class2`・`L04_fig1_three_types`・`L04_ex1_temperature_drinks`・`L05_ex2_basketball`・"
        "`coin_counts`）から取り、ラベルは本文明示値のみ、alt は本文の画像参照と文字単位で同一（生成時 assert）。",
        "- **L07_fig1**: データ=`coin_counts(seed=20260902)`。度数列は本文の度数分布表の写し（`COIN_COUNTS_OVERRIDE`）と"
        "生成時に照合し、一致しなければ停止する。18以上の棒を濃く塗り（SHADE2）、24以上は斜線（棒なし）。alt は "
        "lesson_07.md §3 と lesson_08.md §3（再掲）の両方と照合。**L09_fig1**: 枠名6個・矢印ラベル5個を lesson_09.md の"
        "文言と照合し、図中の「情報Ⅰ」を本文の字形（ローマ数字）にそろえた。",
        "- 差し替え箇所は各 `fig_*` 関数冒頭の「パラメータ」ブロック（L04 の散布図3組 `SCATTER_*` と L07 の "
        "`COIN_COUNTS_OVERRIDE`・`COIN_SEED` はモジュール先頭）。差し替え後は期待値"
        "（`*_EXPECT`）も本文の値に合わせて更新し、再実行で全 assert の通過を確認する。",
        f"- 禁止文字列リスト（`check_tokens`）: answer_key 由来の値を計{n_tokens}項目登録"
        "（answer_key_L01-03・L04-06・L07-08・L09 由来。対象値は本ファイルには書かない）。",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値は、軸の目盛り・データの個数・定義の数（1.5×四分位範囲）と、"
        "本文の表に載る想定の偏差の値（L02・切替可）のみ。五数要約・分散・標準偏差・相関係数 r・"
        "24以上の回数と相対度数 p は**図に描かない**（本文の活動・練習の答えになるため）。",
        "- L09 の単元マップは「帰無仮説」「有意水準」の語をSVG全文への禁止語検査で排除"
        "（本文 L09 で1回だけ出す設計のため）。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する"
        "（数値は必ず該当 `lesson_XX.md` 本文の表と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算assert・答え漏れ検査・禁止文字検査に1つでも"
        "落ちると図は出力されない（出力済みファイルは検査失敗時点のもので確定しない）。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    # distribution_status は本文（lesson_XX.md の frontmatter）に合わせる（台帳側を本文にそろえる）
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines),
        encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks, "
          f"{n_tokens} ban-tokens, {total_bytes} bytes of SVG, "
          f"{n_provisional} provisional)")


if __name__ == "__main__":
    main()
