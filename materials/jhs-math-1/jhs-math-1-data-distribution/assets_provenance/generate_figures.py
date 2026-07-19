#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1数学「データの分布」単元 図版パラメトリック生成スクリプト
================================================================================
様式: jhs-math-2-quartiles-boxplot/assets_provenance/generate_figures.py と同一
（コード来歴・白黒両立・答え非記載・<title>/<desc>のAI再利用メタ情報）。
描画ヘルパー（Canvas/int_number_line/draw_dotplot/audit_numbers等）は同スクリプトの
実装を流用（無変更の方針）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（10枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証:
  1) 統計検算assert — 度数分布は本文の生データから**スクリプト内で再集計**し、
     本文の度数分布表と一致しなければ図を出力しない。平均値・中央値・最頻値・
     累積度数・相対度数も生データ／度数から再計算して本文値と照合する。
  2) 禁止文字列の機械検査 — 各図の<text>/<title>/<desc>に現れる数値トークンを全て抽出し、
     図ごとの「許可数値リスト」外の数値（＝答えの漏えい候補）があれば停止。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
  SVGの直接編集は禁止（来歴が切れる）。
"""

import math
import re
import datetime
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数 ----------------------------------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
DOT_R = 2.5      # 点マーカー半径


# ===========================================================================
# 検算ヘルパー
# ===========================================================================
class Checker:
    """assert相当の検算記録。1件でも失敗すると例外で停止（図は出力されない）"""

    def __init__(self):
        self.items = []

    def ok(self, desc, cond, note=""):
        if not cond:
            raise AssertionError(f"検算失敗: {desc} {note}")
        self.items.append((desc, note))


def mean_of(data):
    return sum(data) / len(data)


def median_of(data):
    """中央値——本文L01の手順（偶数個は真ん中2つの平均）"""
    d = sorted(data)
    n = len(d)
    if n % 2 == 1:
        return d[n // 2]
    return (d[n // 2 - 1] + d[n // 2]) / 2


def freq_counts(data, cmin, cwidth, nclass):
    """度数分布（各階級は「以上〜未満」の半開区間）を生データから再集計"""
    counts = [0] * nclass
    for v in data:
        k = int((v - cmin) // cwidth)
        assert 0 <= k < nclass, f"データ {v} が階級の範囲外"
        counts[k] += 1
    return counts


TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# レッスンID（L01〜L08）・「主概念1」等の構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "06", "07", "08", "1", "2", "3"}


def audit_numbers(svg, allowed, check_tokens, fig_id):
    """禁止文字列の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。allowed=許可数値トークン集合、check_tokens=答え漏れ検査トークン
    （answer_keyにのみ現れる値）。"""
    allowed = set(allowed) | GLOBAL_ALLOWED
    chunks = TEXT_RE.findall(svg) + TITLE_RE.findall(svg) + DESC_RE.findall(svg)
    for c in chunks:
        for b in check_tokens:
            if b in c:
                raise AssertionError(f"{fig_id}: 禁止文字列 '{b}' が図内文字列に混入: {c!r}")
        for tok in NUM_RE.findall(c):
            if tok not in allowed:
                raise AssertionError(
                    f"{fig_id}: 許可外の数値 '{tok}' が図内文字列に混入: {c!r}")


# ===========================================================================
# 描画ヘルパー（quartiles-boxplot版から流用）
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
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"'
                 f'{r} fill="{fill}" stroke="{color}" stroke-width="{sw}"{d}/>')

    def dot(self, x, y, r=DOT_R, fill="#000", sw=1.2):
        if fill == "none" or fill == "#fff":
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                     f'stroke="#000" stroke-width="{sw}"/>')
        else:
            self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, color="#000"):
        wgt = f' font-weight="{weight}"' if weight else ""
        c = f' fill="{color}"' if color != "#000" else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{c}>{escape(s)}</text>')

    def polyline(self, pts, w=MAIN_W, dash=None, color="#000"):
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polyline points="{p}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}"{d}/>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None, color="#000"):
        """直線矢印（先端は三角形の2辺で描く——marker不使用でself-contained）"""
        self.line(x1, y1, x2, y2, w=w, dash=dash, color=color)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (1, -1):
            a = ang + math.pi - s * math.radians(26)
            self.line(x2, y2, x2 + head * math.cos(a), y2 + head * math.sin(a),
                      w=w, color=color)

    def render(self, fig_id, title, desc):
        """AI再利用メタ情報: <title>/<desc>をルート直下に埋め込んで完全なSVG文字列を返す"""
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'role="img">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(quartiles-boxplot単元と同一様式・AI再利用メタ情報つき・SVG直接編集禁止/'
            f'スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )


def int_number_line(cv, x0, x1, y, vmin, vmax, label_vals, tick_step=1,
                    tick_h=3.5, big_h=6.0, label_size=11, label_dy=18):
    """整数目盛りの数直線: tick_step刻みの小ティック＋label_valsに大ティック＋数値ラベル。
    戻り値: 値→x座標 の線形変換関数（数値→座標の厳密変換）"""
    def X(v):
        return x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)

    cv.line(x0, y, x1, y, w=1.2)
    n = round((vmax - vmin) / tick_step)
    for i in range(n + 1):
        v = vmin + i * tick_step
        h = big_h if v in label_vals else tick_h
        cv.line(X(v), y - h, X(v), y + h, w=0.9)
    for v in label_vals:
        cv.text(X(v), y + label_dy, f"{v:g}", size=label_size)
    return X


def draw_dotplot(cv, X, y_base, data, r=3.0, step=8.5):
    """ドットプロット（1人1点・同じ値は縦に積む）。戻り値=打点数"""
    seen = {}
    for v in sorted(data):
        k = seen.get(v, 0)
        cv.dot(X(v), y_base - k * step, r=r)
        seen[v] = k + 1
    return sum(seen.values())


def y_axis(cv, x, y_base, yscale, label_vals, label_size=10.5, top_pad=0):
    """度数の縦軸: y_baseを0として上方向。label_valsにティック＋ラベル"""
    top = y_base - max(label_vals) * yscale - top_pad
    cv.line(x, y_base, x, top, w=1.2)
    for f in label_vals:
        cv.line(x - 4, y_base - f * yscale, x, y_base - f * yscale, w=0.9)
        cv.text(x - 8, y_base - f * yscale + 4, f"{f:g}", size=label_size,
                anchor="end")


# ===========================================================================
# 図1: L01-1 ドットプロット（計算テスト10人）
# 本文根拠: lesson_01.md 主概念1（生データ 7,9,5,8,7,4,9,6,7,8）
# 答え漏れ注意: 平均値・中央値・最頻値（いずれも7点）は図の後の本文で求める
#   活動なので、図には代表値の位置や値を一切描かない
# ===========================================================================
TEST10 = [7, 9, 5, 8, 7, 4, 9, 6, 7, 8]   # lesson_01 主概念1の生データ（転記）


def fig_L01_dotplot():
    ck = Checker()
    ck.ok("10人分のデータ（本文「10人が受けた」と一致）", len(TEST10) == 10)
    ck.ok("並べ替えると本文の 4,5,6,7,7,7,8,8,9,9 と一致",
          sorted(TEST10) == [4, 5, 6, 7, 7, 7, 8, 8, 9, 9])
    tally = {v: TEST10.count(v) for v in set(TEST10)}
    ck.ok("積み上がり: 7に3個・8と9に2個ずつ（図版指定と一致）",
          tally[7] == 3 and tally[8] == 2 and tally[9] == 2
          and tally[4] == tally[5] == tally[6] == 1)
    ck.ok("合計70・平均値7点（本文の計算と一致——図には描かない）",
          sum(TEST10) == 70 and mean_of(TEST10) == 7)
    ck.ok("中央値7点（偶数個・真ん中2つの平均。本文と一致——図には描かない）",
          median_of(TEST10) == 7)
    ck.ok("最頻値7点（最多3回。本文と一致——図には描かない）",
          max(tally, key=lambda v: tally[v]) == 7)

    cv = Canvas(480, 210)
    X = int_number_line(cv, 55, 445, 150, 0, 10,
                        label_vals=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                        tick_step=1, label_dy=18, label_size=11)
    n = draw_dotplot(cv, X, 138, TEST10, r=4.0, step=13.0)
    ck.ok("打点数=10（1人1点）", n == 10)
    cv.text(240, 28, "計算テスト10人の得点のドットプロット", size=FS, weight="bold")
    cv.text(240, 196, "横軸: 得点（点）・10人（架空の練習用データ）", size=11)

    title = "計算テスト10人の得点のドットプロット"
    desc = ("L01主概念1の導入図。得点0〜10点の数直線上に、10人の計算テストの得点"
            "（架空の練習用データ）を1人1点のドットで積んだ。同じ値は縦に積む。"
            "散らばりの全体を目で見る最初の表現（表現の階段の1段目）。代表値の位置や"
            "値は意図的に描かない（3つの代表値を求めるのは図の後の本文の活動のため）。"
            "打点の内訳は生データから再集計してassert検算済み。再現指示: 整数目盛りの"
            "数直線の上に黒丸を置き、同じ値は縦に積む。数値の注記なし。白黒のみ。")
    allowed = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
    return dict(file="L01_fig1_dotplot_test10.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="生データを1人1点で並べ「散らばりの全体」を見る最初の表現",
                params="10人の得点（本文転記）→積み上がり{7:3個,8:2個,9:2個}を再集計",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図2: L02-1 外れ値実験のドットプロット2段比較
# 本文根拠: lesson_02.md 主概念1（8人の練習時間・90分を除く実験）
#   平均値20分・中央値10.5分／除いた7人で平均値10分・中央値10分は本文が明示する
#   実験結果なので、矢印ラベルとして図に載せる（答え漏れではない）
# ===========================================================================
PRACTICE8 = [6, 8, 9, 10, 11, 12, 14, 90]   # lesson_02 主概念1の生データ（転記）


def fig_L02_outlier():
    ck = Checker()
    p7 = [v for v in PRACTICE8 if v != 90]
    ck.ok("8人・合計160・平均値20分（本文の計算と一致）",
          len(PRACTICE8) == 8 and sum(PRACTICE8) == 160 and mean_of(PRACTICE8) == 20)
    ck.ok("中央値10.5分（偶数個・4番目と5番目の平均。本文と一致）",
          median_of(PRACTICE8) == 10.5)
    ck.ok("90分を除いた7人: 合計70・平均値10分・中央値10分（本文と一致）",
          len(p7) == 7 and sum(p7) == 70 and mean_of(p7) == 10 and median_of(p7) == 10)
    ck.ok("平均値は10→20へ2倍・中央値は10→10.5とほとんど動かない（本文の主旨）",
          mean_of(PRACTICE8) == 2 * mean_of(p7)
          and abs(median_of(PRACTICE8) - median_of(p7)) == 0.5)

    cv = Canvas(480, 420)
    # 上段: 90分を入れた8人
    cv.text(56, 48, "90分を入れた8人", size=FS_CAP, anchor="start", weight="bold")
    X = int_number_line(cv, 50, 450, 150, 0, 100, label_vals=[0, 20, 40, 60, 80, 100],
                        tick_step=5, label_dy=17, label_size=11)
    draw_dotplot(cv, X, 138, PRACTICE8, r=3.6)
    cv.arrow(X(20), 76, X(20), 120, w=1.4)
    cv.text(X(20) + 8, 70, "平均値 20分", size=11, weight="bold", anchor="start")
    cv.arrow(X(10.5), 214, X(10.5), 168, w=1.4, dash="4 3")
    cv.text(X(10.5) + 8, 228, "中央値 10.5分", size=11, anchor="start")
    cv.text(300, 246, "横軸: 練習時間（分）（架空の練習用データ）", size=10.5)
    # 下段: 90分を除いた7人
    cv.text(56, 258, "90分を除いた7人", size=FS_CAP, anchor="start", weight="bold")
    X2 = int_number_line(cv, 50, 450, 350, 0, 100, label_vals=[0, 20, 40, 60, 80, 100],
                         tick_step=5, label_dy=17, label_size=11)
    draw_dotplot(cv, X2, 338, p7, r=3.6)
    cv.arrow(X2(10), 286, X2(10), 326, w=1.4)
    cv.text(X2(10) + 8, 280, "平均値 10分", size=11, weight="bold", anchor="start")
    cv.arrow(X2(10), 410, X2(10), 368, w=1.4, dash="4 3")
    cv.text(X2(10) + 8, 416, "中央値 10分", size=11, anchor="start")
    cv.text(240, 24, "たった1人で、平均値だけが大きく動く", size=FS, weight="bold")

    title = "外れ値実験のドットプロット2段比較（90分の1人と平均値の動き）"
    desc = ("L02主概念1の実験図。横軸0〜100分の同じ目盛りの数直線2本に、上段は90分を"
            "入れた8人・下段は90分を除いた7人の練習時間（架空の練習用データ）をドットで"
            "打ち、それぞれの平均値（実線矢印）と中央値（破線矢印）の位置を示した。"
            "90分の1個が入ると平均値は10分から20分へ2倍にはね上がるのに、中央値は10分"
            "から10.5分とほとんど動かない——矢印の動き幅の差で外れ値の影響を可視化する。"
            "平均値・中央値は生データから再計算して本文と一致をassert検算済み。"
            "再現指示: 同じ目盛りの数直線2段にドットを打ち、平均値は上から実線矢印・"
            "中央値は下から破線矢印で指す。白黒のみ。")
    allowed = {"0", "20", "40", "60", "80", "100", "90", "8", "7", "10.5", "10"}
    return dict(file="L02_fig1_outlier_dotplot_compare.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="90分の1個が平均値だけを大きく動かすことの可視化（外れ値実験）",
                params="8人の練習時間（本文転記）→平均20/中央10.5・除外後は平均10/中央10を再計算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図3: L03-1 ヒストグラム（通学時間・階級幅5分）＋表の行と柱の1対1矢印
# 本文根拠: lesson_03.md 主概念1の生データ30個と度数分布表・主概念2の figure-spec
# 答え漏れ注意: 練習2(2)の答え「4人」（30分以上の合計）は文字列として載せない
# ===========================================================================
COMMUTE30 = [16, 22, 9, 18, 14, 27, 17, 36, 12, 19, 23, 15, 4, 21, 18,
             32, 13, 24, 16, 7, 26, 11, 34, 17, 22, 29, 19, 14, 37, 28]
COMMUTE_FREQ = [1, 2, 5, 9, 5, 4, 2, 2]   # lesson_03 主概念1の表（幅5・0〜40）


def fig_L03_hist():
    ck = Checker()
    counts = freq_counts(COMMUTE30, 0, 5, 8)
    ck.ok("30個の生データから度数を再集計——本文の表（1,2,5,9,5,4,2,2）と一致",
          counts == COMMUTE_FREQ, f"実測={counts}")
    ck.ok("度数の合計=30（本文の検算と一致）", sum(counts) == 30)
    ck.ok("山は1つ・頂上は15以上20未満（度数9）で右へ裾（本文の読みと一致）",
          max(counts) == counts[3] and counts[3] == 9
          and counts[4] >= counts[5] >= counts[6])

    cv = Canvas(480, 450)
    # 上: 度数分布表（本文の表と同一の値・柱と同じ列に整列）
    x0t, x1t = 100, 460
    cw = (x1t - x0t) / 8
    top_t, mid_t, bot_t = 52, 92, 122
    cv.rect(x0t - 92, top_t, x1t - x0t + 92, bot_t - top_t, sw=1.1)
    cv.line(x0t - 92, mid_t, x1t, mid_t, w=0.8)
    cv.text(x0t - 86, 74, "階級（分）", size=10, anchor="start")
    cv.text(x0t - 86, 112, "度数（人）", size=10, anchor="start")
    for k, c in enumerate(counts):
        xx = x0t + k * cw
        cv.line(xx, top_t, xx, bot_t, w=0.8)
        cx = xx + cw / 2
        cv.text(cx, 71, f"{5 * k}以上", size=9.5)
        cv.text(cx, 85, f"{5 * (k + 1)}未満", size=9.5)
        cv.text(cx, 112, f"{c}", size=11, weight="bold")
    # 下: ヒストグラム（表の列と同じx位置に柱）
    base = 385
    X = int_number_line(cv, x0t, x1t, base, 0, 40,
                        label_vals=[0, 5, 10, 15, 20, 25, 30, 35, 40],
                        tick_step=5, label_dy=17, label_size=10)
    yscale = 22.0
    y_axis(cv, x0t, base, yscale, [0, 2, 4, 6, 8, 10])
    for k, c in enumerate(counts):
        if c > 0:
            cv.rect(X(k * 5), base - c * yscale, X((k + 1) * 5) - X(k * 5),
                    c * yscale, sw=1.3, fill="#e6e6e6")
        # 表のマス→柱の1対1矢印（まっすぐ下へ）
        cx = (X(k * 5) + X((k + 1) * 5)) / 2
        cv.arrow(cx, bot_t + 6, cx, base - c * yscale - 6, w=0.9, head=5.5,
                 color="#888")
    cv.text(x0t - 86, 148, "度数（人）", size=10.5, anchor="start")
    cv.text(240, 26, "表の1列が、柱1本になる——柱の高さ=度数", size=FS, weight="bold")
    cv.text(240, 438, "30人の通学時間・階級の幅5分（架空の練習用データ）", size=11)

    title = "通学時間のヒストグラム（階級幅5分・表と柱の1対1対応つき)"
    desc = ("L03主概念2の初対面図。上に階級幅5分の度数分布表（8階級・合計30人）を柱と"
            "同じ列位置で横向きに置き、下にそのヒストグラム（横軸0〜40分・縦軸度数）を"
            "描いて、表の各マスから対応する柱へまっすぐ下向きの灰色矢印を1本ずつ引き、"
            "「表の1階級=柱1本・柱の高さ=度数」の対応を示した。山は1つで頂上は度数9の"
            "階級、右へなだらかに裾を引く形。度数は30個の生データから再集計して本文の表と"
            "一致をassert検算済み。柱はすき間なく並べる。再現指示: 上に横向きの度数分布表・"
            "下にヒストグラムを列をそろえて置き、各マスから柱へ垂直の細い矢印を引く。"
            "棒は薄いグレー塗り＋黒枠。白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "25", "30", "35", "40",
               "1", "2", "4", "6", "8", "9"}
    check_tokens = {"4人"}   # 練習2(2)の答え（30分以上=4人）は図内文字列に入れない
    return dict(file="L03_fig1_histogram_commute.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="度数分布表→ヒストグラムの変換の初対面（行と柱の1対1対応）",
                params=f"通学時間30個の生データ（本文転記）→度数={counts}を再集計",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図4: L04-1 ヒストグラム＋度数折れ線の重ね図（通学時間・階級幅5分）
# 本文根拠: lesson_04.md 主概念2の figure-spec（データはL03と同一）
# 答え漏れ注意: 最頻値17.5分・中央値18.5分・平均値20.0分（主概念3で求める値）は
#   図に描かない
# ===========================================================================
def fig_L04_polyline():
    ck = Checker()
    counts = freq_counts(COMMUTE30, 0, 5, 8)
    ck.ok("L03と同一データ: 度数を生データから再集計——本文の表と一致",
          counts == COMMUTE_FREQ, f"実測={counts}")
    mids = [(5 * k + 5 * (k + 1)) / 2 for k in range(8)]
    ck.ok("折れ線の頂点は各階級の真ん中（階級値）——2.5,7.5,…,37.5",
          mids == [2.5 + 5 * k for k in range(8)])
    ck.ok("両端は隣の度数0の階級の階級値（-2.5と42.5）で横軸に降りる（本文の手順と一致）",
          mids[0] - 5 == -2.5 and mids[-1] + 5 == 42.5)

    cv = Canvas(480, 320)
    base = 250
    x0, x1 = 55, 455
    vmin, vmax = -5, 45

    def X(v):
        return x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)

    yscale = 15.0
    # 横軸（-5〜45まで引くが、目盛りラベルは0〜40のみ）
    cv.line(x0, base, x1, base, w=1.2)
    for v in range(0, 45, 5):
        cv.line(X(v), base - 3.5, X(v), base + 3.5, w=0.9)
        cv.text(X(v), base + 17, f"{v}", size=10)
    y_axis(cv, X(-5), base, yscale, [0, 5, 10])
    # 柱（薄いグレー）
    for k, c in enumerate(counts):
        if c > 0:
            cv.rect(X(k * 5), base - c * yscale, X((k + 1) * 5) - X(k * 5),
                    c * yscale, sw=1.1, fill="#ececec", color="#666")
    # 度数折れ線（濃い実線・頂点に点）
    pts = [(X(mids[0] - 5), base)] + \
          [(X(m), base - c * yscale) for m, c in zip(mids, counts)] + \
          [(X(mids[-1] + 5), base)]
    cv.polyline(pts, w=2.6)
    for px, py in pts:
        cv.dot(px, py, r=3.0)
    cv.text(X(-5) + 6, 62, "度数（人）", size=10.5, anchor="start")
    cv.text(255, 288, "通学時間（分）・30人（架空の練習用データ）", size=11)
    cv.text(240, 26, "柱の頂上の真ん中を、順に結ぶ——度数折れ線", size=FS, weight="bold")
    cv.text(X(27), 78, "両端は、となりの度数0の階級の", size=10, anchor="start")
    cv.text(X(27), 91, "真ん中まで降ろす", size=10, anchor="start")
    cv.arrow(X(41), 96, X(42.3), base - 12, w=0.9, head=5.5, color="#888")

    title = "ヒストグラムと度数折れ線の重ね図（通学時間・階級幅5分）"
    desc = ("L04主概念2の作図手順図。L03と同一の通学時間30人のヒストグラム（階級幅5分・"
            "薄いグレーの柱）に、各柱の上の辺の真ん中（階級値の位置）を順に線分で結んだ"
            "度数折れ線を濃い実線で重ねた。両端は、両どなりに度数0の階級があるものとして"
            "その階級値の位置で横軸に降りる。折れ線だけ残せば分布の山の稜線になる。"
            "度数は生データから再集計して本文の表と一致をassert検算済み。最頻値・中央値・"
            "平均値の位置は描かない（主概念3で求める活動のため）。再現指示: ヒストグラムの"
            "各柱の頂上中央に点を打ち、隣どうしを太めの実線で結び、両端を横軸に降ろす。"
            "白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "25", "30", "35", "40"}
    check_tokens = {"17.5", "18.5", "20.0"}   # 主概念3で求める3つの代表値
    return dict(file="L04_fig1_freq_polygon_overlay.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="柱の頂上の中点を結ぶ作図手順と「山の形だけを抜き出す」表現の可視化",
                params=f"L03と同一の生データ→度数={counts}・頂点は階級値2.5〜37.5",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図5: L04-2 分布の形と代表値の並びの3型比較図（模式図・数値なし）
# 本文根拠: lesson_04.md 主概念3の figure-spec
# 生成方式: 滑らかな密度曲線を数式からサンプリングし、その曲線自身から平均値・
#   中央値・最頻値を数値的に計算して縦線の位置を決める（線の並び順が作図の
#   都合ではなく分布の性質から出ることをassertで保証）
# ===========================================================================
def _density_stats(f, n=600):
    """[0,1]上の密度fを離散近似し (mean, median, mode) を返す"""
    xs = [i / n for i in range(n + 1)]
    ys = [f(x) for x in xs]
    total = sum(ys)
    mean = sum(x * y for x, y in zip(xs, ys)) / total
    acc, median = 0.0, None
    for x, y in zip(xs, ys):
        acc += y
        if acc >= total / 2:
            median = x
            break
    mode = xs[ys.index(max(ys))]
    return mean, median, mode, xs, ys


def fig_L04_shapes():
    ck = Checker()
    f_sym = lambda t: math.exp(-((t - 0.5) / 0.13) ** 2)
    f_right = lambda t: (10 * t) ** 2 * math.exp(-10 * t / 1.3)
    f_left = lambda t: f_right(1 - t)
    stats = {}
    for name, f in (("対称", f_sym), ("右裾", f_right), ("左裾", f_left)):
        stats[name] = _density_stats(f)
    m, md, mo = stats["対称"][:3]
    ck.ok("①対称: 平均値・中央値・最頻値が中央でほぼ一致（曲線から数値計算）",
          abs(m - 0.5) < 0.005 and abs(md - 0.5) < 0.01 and abs(mo - 0.5) < 0.01)
    m, md, mo = stats["右裾"][:3]
    ck.ok("②右に裾: 最頻値＜中央値＜平均値の順に右へ（曲線から数値計算・本文と一致）",
          mo + 0.01 < md < m - 0.01)
    m, md, mo = stats["左裾"][:3]
    ck.ok("③左に裾: 平均値＜中央値＜最頻値の順に左へ（曲線から数値計算・本文と一致）",
          m + 0.01 < md < mo - 0.01)

    cv = Canvas(480, 300)
    panels = [("① 左右対称", "対称", 14), ("② 右に裾", "右裾", 172),
              ("③ 左に裾", "左裾", 330)]
    pw, base, hmax = 136, 200, 100
    for label, key, px0 in panels:
        mean, median, mode, xs, ys = stats[key]
        ymax = max(ys)
        cv.text(px0 + pw / 2, 52, label, size=FS_CAP, weight="bold")
        # 軸
        cv.arrow(px0, base, px0 + pw + 6, base, w=1.1, head=5.5)
        cv.text(px0 + pw + 2, base + 15, "値", size=10, anchor="end")
        # 曲線
        pts = [(px0 + x * pw, base - ys[i] / ymax * hmax)
               for i, x in enumerate(xs) if i % 6 == 0]
        cv.polyline(pts, w=1.8)

        def hgt(t):
            return ys[min(range(len(xs)), key=lambda i: abs(xs[i] - t))] / ymax * hmax

        if key == "対称":
            cv.line(px0 + mode * pw, base, px0 + mode * pw, base - hgt(mode) - 8,
                    w=2.0)
            cv.text(px0 + pw / 2, 226, "3つの値が", size=10)
            cv.text(px0 + pw / 2, 239, "ほぼ一致（重なる）", size=10)
        else:
            for t, wdt, dash in ((mode, 2.0, None), (median, 1.4, "6 4"),
                                 (mean, 1.4, "2 3")):
                cv.line(px0 + t * pw, base, px0 + t * pw, base - hgt(t) - 8,
                        w=wdt, dash=dash)
            order = ("最頻値＜中央値＜平均値" if key == "右裾"
                     else "平均値＜中央値＜最頻値")
            cv.text(px0 + pw / 2, 226, order, size=10)
            cv.text(px0 + pw / 2, 239, "の順に並びやすい", size=10)
    # 凡例
    lx = 92
    for lab, wdt, dash in (("最頻値（実線）", 2.0, None), ("中央値（破線）", 1.4, "6 4"),
                           ("平均値（点線）", 1.4, "2 3")):
        cv.line(lx, 268, lx + 26, 268, w=wdt, dash=dash)
        cv.text(lx + 32, 272, lab, size=10, anchor="start")
        lx += 118
    cv.text(240, 26, "山の形と、3つの代表値の並び方", size=FS, weight="bold")
    cv.text(240, 292, "横軸: 値／縦軸: 度数（数値なしの模式図）", size=10.5)

    title = "分布の形と代表値の並びの3型比較図（対称・右裾・左裾）"
    desc = ("L04主概念3の一覧整理図。数値なしの滑らかな山型の模式図3枚を横に並べ、"
            "①左右対称では平均値・中央値・最頻値の3つが中央でほぼ一致、②右に裾を引く形"
            "では最頻値＜中央値＜平均値の順に右へ、③左に裾を引く形では平均値＜中央値＜"
            "最頻値の順に左へ並びやすいことを、縦線（最頻値=実線・中央値=破線・平均値="
            "点線）で示した。3本の縦線の位置は、描いた密度曲線そのものから平均値・中央値・"
            "最頻値を数値計算して決めており、並び順が分布の性質から出ることをassert検算済み"
            "（「なりやすい」であって必ずではない点は本文guideのとおり）。再現指示: 山型曲線"
            "3枚に、線種を変えた縦線3本（対称のみ1本に重なる）を立て、凡例を添える。白黒のみ。")
    allowed = set()
    return dict(file="L04_fig2_shape_vs_averages.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="対称・右裾・左裾での代表値の位置関係の一覧整理（L02 guideの回収）",
                params="密度曲線3本（数式定義）→曲線から平均・中央値・最頻値を数値計算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図6: L05-1 幅2のヒストグラム（的当てスコア40人）
# 本文根拠: lesson_05.md 主概念1の生データ40個と幅2の度数分布表
# 答え漏れ注意: 練習1（幅4の表: 3,13,7,13,4）の値「13」は図内文字列に入れない
# ===========================================================================
SCORES40 = [7, 12, 5, 16, 8, 13, 6, 10, 14, 3, 12, 7, 15, 9, 13, 4, 11, 7, 18, 12,
            6, 14, 8, 13, 2, 16, 10, 5, 12, 7, 17, 11, 14, 5, 13, 6, 15, 4, 7, 1]
W2_FREQ = [1, 2, 5, 8, 3, 4, 8, 5, 3, 1]    # lesson_05 幅2の表
W8_FREQ = [16, 20, 4]                        # lesson_05 幅8の表


def fig_L05_w2():
    ck = Checker()
    counts = freq_counts(SCORES40, 0, 2, 10)
    ck.ok("40個の生データから幅2の度数を再集計——本文の表（1,2,5,8,3,4,8,5,3,1）と一致",
          counts == W2_FREQ, f"実測={counts}")
    ck.ok("度数の合計=40（本文の検算と一致）", sum(counts) == 40)
    ck.ok("山が2つ: [6,8)と[12,14)が最多8・あいだの[8,10)がへこむ（本文の読みと一致）",
          counts[3] == counts[6] == max(counts) == 8
          and counts[4] < counts[3] and counts[4] < counts[6])

    cv = Canvas(480, 300)
    base = 240
    X = int_number_line(cv, 60, 450, base, 0, 20,
                        label_vals=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
                        tick_step=2, label_dy=17, label_size=10.5)
    yscale = 17.0
    y_axis(cv, 60, base, yscale, [0, 2, 4, 6, 8, 10])
    for k, c in enumerate(counts):
        if c > 0:
            cv.rect(X(k * 2), base - c * yscale, X((k + 1) * 2) - X(k * 2),
                    c * yscale, sw=1.3, fill="#e6e6e6")
    cv.text(66, 58, "度数（人）", size=10.5, anchor="start")
    cv.text(240, 26, "的当てスコアのヒストグラム——階級の幅2点", size=FS, weight="bold")
    cv.text(240, 282, "横軸: スコア（点）・40人（架空の練習用データ）", size=11)

    title = "的当てスコアのヒストグラム（階級幅2点・山が2つ）"
    desc = ("L05主概念1の前半図。40人の的当てスコア（架空の練習用データ）を階級幅2点で"
            "整理したヒストグラム。横軸0〜20点・縦軸度数。山が2つあり、あいだの階級が"
            "へこんでいる——2つのグループがありそうだと読みたくなる形。度数は40個の"
            "生データから再集計して本文の表と一致をassert検算済み。同じ生データから"
            "幅8の図（L05_fig2）も生成しており、2枚は同一データである。再現指示: 幅2の"
            "柱をすき間なく並べ、2つの頂上とあいだの谷が見える形にする。棒は薄いグレー"
            "塗り＋黒枠。白黒のみ。")
    allowed = {"0", "2", "4", "6", "8", "10", "12", "14", "16", "18", "20", "40"}
    check_tokens = {"13"}   # 練習1（幅4の表）の答えに現れる度数
    return dict(file="L05_fig1_hist_width2.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="山が2つある分布の姿を見せる（幅8との比較の前半）",
                params=f"スコア40個の生データ（本文転記）→幅2の度数={counts}を再集計",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図7: L05-2 幅8のヒストグラム（的当てスコア・同一データ）
# 本文根拠: lesson_05.md 主概念1の幅8の表（幅2の表を合算したもの）
# ===========================================================================
def fig_L05_w8():
    ck = Checker()
    counts = freq_counts(SCORES40, 0, 8, 3)
    ck.ok("同じ40個の生データから幅8の度数を再集計——本文の表（16,20,4）と一致",
          counts == W8_FREQ, f"実測={counts}")
    ck.ok("度数の合計=40（同一データの検算）", sum(counts) == 40)
    merged = [sum(W2_FREQ[i:i + 4]) for i in range(0, 12, 4)]
    ck.ok("幅2の表を4階級ずつ合算しても同じ値になる（本文「合算したもの」と一致）",
          merged == counts, f"合算={merged}")
    ck.ok("山が1つ: 真ん中の階級だけが最多の単峰（本文の読みと一致）",
          counts[1] == max(counts) and counts[0] < counts[1] > counts[2])

    cv = Canvas(480, 300)
    base = 240
    X = int_number_line(cv, 60, 450, base, 0, 24, label_vals=[0, 8, 16, 24],
                        tick_step=8, label_dy=17, label_size=10.5)
    yscale = 7.6
    y_axis(cv, 60, base, yscale, [0, 8, 16, 24])
    for k, c in enumerate(counts):
        if c > 0:
            cv.rect(X(k * 8), base - c * yscale, X((k + 1) * 8) - X(k * 8),
                    c * yscale, sw=1.3, fill="#e6e6e6")
    cv.text(66, 46, "度数（人）", size=10.5, anchor="start")
    cv.text(240, 26, "同じデータで、階級の幅を8点にすると", size=FS, weight="bold")
    cv.text(240, 282, "横軸: スコア（点）・40人（図L05-1と同一データ）", size=11)

    title = "的当てスコアのヒストグラム（階級幅8点・山が1つに見える）"
    desc = ("L05主概念1の後半図。図L05-1とまったく同じ40人のスコアを、階級幅8点で"
            "整理し直したヒストグラム。横軸0〜24点・縦軸度数。山が1つのふつうの分布に"
            "見え、幅2のときの2つの山の気配は消える——階級の幅が異なると読み取れる傾向が"
            "異なる場合があることの体感。度数は同じ生データから再集計し、幅2の表の合算とも"
            "一致することをassert検算済み。再現指示: 幅8の柱3本をすき間なく並べ、単峰の山に"
            "見える形にする。図L05-1と縦に並べて対比する用途。棒は薄いグレー塗り＋黒枠。"
            "白黒のみ。")
    allowed = {"0", "8", "16", "24", "40"}
    check_tokens = {"13"}
    return dict(file="L05_fig2_hist_width8.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="幅を広げると2つの山が1つに見えることの体感（L05-1との対比）",
                params=f"同一の生データ40個→幅8の度数={counts}を再集計（幅2の合算とも照合）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図8: L06-1 度数の柱と相対度数の柱の並置比較図（けん玉・1年生40人と2年生25人）
# 本文根拠: lesson_06.md 主概念1の表（度数・相対度数）と主概念2の figure-spec
# ===========================================================================
KENDAMA_F1 = [4, 10, 12, 8, 6]    # 1年生の度数（lesson_06の表・転記）
KENDAMA_F2 = [2, 5, 9, 6, 3]      # 2年生の度数（同）
REL1_EXPECT = [0.10, 0.25, 0.30, 0.20, 0.15]
REL2_EXPECT = [0.08, 0.20, 0.36, 0.24, 0.12]


def fig_L06_pair():
    ck = Checker()
    n1, n2 = sum(KENDAMA_F1), sum(KENDAMA_F2)
    ck.ok("総度数: 1年生40人・2年生25人（本文と一致）", n1 == 40 and n2 == 25)
    r1 = [f / n1 for f in KENDAMA_F1]
    r2 = [f / n2 for f in KENDAMA_F2]
    ck.ok("1年生の相対度数を度数÷総度数で再計算——本文の表（0.10〜0.15）と一致",
          r1 == REL1_EXPECT, f"実測={r1}")
    ck.ok("2年生の相対度数を再計算——本文の表（0.08〜0.12）と一致",
          r2 == REL2_EXPECT, f"実測={r2}")
    ck.ok("相対度数の合計はどちらも1.00（部分÷全体の検算）",
          abs(sum(r1) - 1.0) < 1e-9 and abs(sum(r2) - 1.0) < 1e-9)
    ck.ok("[8,12)と[12,16)で逆転: 度数は1年生が多いのに相対度数は2年生が上（本文と一致）",
          KENDAMA_F1[2] > KENDAMA_F2[2] and r1[2] < r2[2]
          and KENDAMA_F1[3] > KENDAMA_F2[3] and r1[3] < r2[3])

    cv = Canvas(480, 560)
    cv.defs.append(
        '<pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)">'
        '<line x1="0" y1="0" x2="0" y2="5" stroke="#555" stroke-width="1.1"/></pattern>')

    def panel(base, vals1, vals2, yscale, ylabels, ylab_fmt):
        X = int_number_line(cv, 70, 450, base, 0, 20, label_vals=[0, 4, 8, 12, 16, 20],
                            tick_step=4, label_dy=17, label_size=10.5)
        cv.line(70, base, 70, base - max(ylabels) * yscale - 6, w=1.2)
        for f in ylabels:
            cv.line(66, base - f * yscale, 70, base - f * yscale, w=0.9)
            cv.text(62, base - f * yscale + 4, ylab_fmt(f), size=10, anchor="end")
        bw = 13.5
        for k, (a, b) in enumerate(zip(vals1, vals2)):
            cx = (X(k * 4) + X((k + 1) * 4)) / 2
            cv.rect(cx - bw - 1.5, base - a * yscale, bw, a * yscale,
                    sw=1.2, fill="#d9d9d9")
            cv.rect(cx + 1.5, base - b * yscale, bw, b * yscale,
                    sw=1.2, fill="url(#hatch)")
        return X

    # 上段: 度数
    cv.text(240, 26, "同じ2つの学年を、度数で見る／相対度数で見る", size=FS, weight="bold")
    cv.text(70, 56, "上段: 度数（人）で比較", size=FS_CAP, anchor="start", weight="bold")
    panel(240, KENDAMA_F1, KENDAMA_F2, 13.0, [0, 4, 8, 12], lambda f: f"{f:g}")
    # 下段: 相対度数
    cv.text(70, 306, "下段: 相対度数で比較", size=FS_CAP, anchor="start", weight="bold")
    Xr = panel(500, REL1_EXPECT, REL2_EXPECT, 480.0, [0, 0.1, 0.2, 0.3, 0.4],
               lambda f: f"{f:g}")
    # 逆転の注記（下段の[8,12)・[12,16)）
    for k in (2, 3):
        cx = (Xr(k * 4) + Xr((k + 1) * 4)) / 2 + 8
        cv.text(cx, 500 - REL2_EXPECT[k] * 480 - 8, "▲", size=10)
    cv.text(Xr(10) + 40, 336, "▲=2年生が1年生を上回る階級", size=10, anchor="start")
    # 凡例
    cv.rect(120, 66, 14, 11, sw=1.2, fill="#d9d9d9")
    cv.text(140, 76, "1年生（40人）", size=10.5, anchor="start")
    cv.rect(250, 66, 14, 11, sw=1.2, fill="url(#hatch)")
    cv.text(270, 76, "2年生（25人）", size=10.5, anchor="start")
    cv.text(240, 542, "横軸: けん玉の成功回数（回）・階級の幅4回（架空の練習用データ）",
            size=11)

    title = "度数の柱と相対度数の柱の並置比較図（1年生40人と2年生25人）"
    desc = ("L06主概念2の可視化図。けん玉チャレンジの1年生40人（グレー塗り）と2年生25人"
            "（斜線）を、上段は度数の柱・下段は相対度数の柱で、同じ横軸（成功回数0〜20回・"
            "階級幅4回）に並べた。上段ではほぼ全階級で1年生の柱が高いが、下段では2つの"
            "階級で2年生が上回る逆転が起きる（▲印）——総度数が違うと度数のままではフェアに"
            "比べられないことの可視化。相対度数は度数÷総度数で再計算して本文の表と一致を"
            "assert検算済み（合計1.00の検算つき）。再現指示: 同じ横軸の2段構成で、上段=度数・"
            "下段=相対度数のグループ棒グラフを描き、逆転する階級に印を付ける。白黒のみ"
            "（塗りと斜線パターンで2集団を区別）。")
    allowed = {"0", "4", "8", "12", "16", "20", "40", "25", "0.1", "0.2", "0.3",
               "0.4", "1.00"}   # 1.00は<desc>内の検算説明の語のみ（図中の文字にはない）
    return dict(file="L06_fig1_freq_vs_relfreq.svg", canvas=cv, lesson="L06",
                title=title, desc=desc,
                intent="総度数が違うと度数の図はフェアな比較にならないことの可視化（逆転の体感）",
                params=f"度数1年={KENDAMA_F1}／2年={KENDAMA_F2}（本文転記）→相対度数を再計算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図9: L07-1 累積度数の積み上げ模式図（1年生40人）
# 本文根拠: lesson_07.md 主概念1の表（度数4,10,12,8,6→累積4,14,26,34,40）
# ===========================================================================
def fig_L07_stack():
    ck = Checker()
    f = KENDAMA_F1   # L06と同一の1年生の度数
    cums = []
    acc = 0
    for v in f:
        acc += v
        cums.append(acc)
    ck.ok("累積度数を「1つ上の累積度数＋その階級の度数」で再計算——本文の表"
          "（4,14,26,34,40）と一致", cums == [4, 14, 26, 34, 40], f"実測={cums}")
    ck.ok("最後の累積度数=総度数40人（本文の検算の型と一致）",
          cums[-1] == sum(f) == 40)

    cv = Canvas(480, 440)
    base, yscale = 380, 7.6
    x0, bw = 150, 150
    cls = ["0以上 4未満", "4以上 8未満", "8以上12未満", "12以上16未満", "16以上20未満"]
    # 左軸: 人数の積み上がり
    cv.line(x0 - 26, base, x0 - 26, base - 40 * yscale, w=1.2)
    for v in (0, 10, 20, 30, 40):
        cv.line(x0 - 30, base - v * yscale, x0 - 26, base - v * yscale, w=0.9)
        cv.text(x0 - 34, base - v * yscale + 4, f"{v}", size=10.5, anchor="end")
    cv.text(x0 - 26, base - 40 * yscale - 14, "人数の積み上がり（人）", size=10.5)
    # ブロックを下から積む
    prev = 0
    for k, (lab, v, c) in enumerate(zip(cls, f, cums)):
        y_top = base - c * yscale
        cv.rect(x0, y_top, bw, v * yscale, sw=1.4,
                fill="#ececec" if k % 2 == 0 else "#fff")
        cv.text(x0 + bw / 2, (y_top + base - prev * yscale) / 2 + 4,
                f"{lab}（{v}人）", size=10)
        # 右: 累積度数のラベル
        cv.line(x0 + bw, y_top, x0 + bw + 16, y_top, w=0.9, dash="2 3", color="#888")
        cv.text(x0 + bw + 22, y_top + 4, f"{c}", size=11.5, anchor="start",
                weight="bold")
        prev = c
    cv.text(x0 + bw + 50, base - 40 * yscale + 4, "＝総度数（40人）と一致",
            size=10.5, anchor="start")
    cv.text(x0 + bw + 46, base - 26, "← 各段の右の数が", size=10, anchor="start")
    cv.text(x0 + bw + 58, base - 13, "累積度数（人）", size=10, anchor="start")
    cv.text(240, 26, "下から順に、飛ばさずに積む——累積度数", size=FS, weight="bold")
    cv.text(240, 424, "1年生40人のけん玉の成功回数（架空の練習用データ）", size=11)

    title = "累積度数の積み上げ模式図（下から順に積んで最後は総度数）"
    desc = ("L07主概念1の動きの可視化図。1年生40人のけん玉の度数を、最小の階級から"
            "ブロックとして下から順に積み上げ、各段の上端の右に累積度数を示した。"
            "最上段の累積度数は総度数40人に一致する——「途中の階級を飛ばさずに積む」"
            "動きと検算の型を1枚で見せる。累積度数は度数列から再計算して本文の表と一致を"
            "assert検算済み（度数はL06と同一の1年生の表）。再現指示: 度数に比例した高さの"
            "ブロックを1本の柱として下から積み、各段の上端右に累積の値・最上段に総度数"
            "一致の注記を添える。白黒のみ。")
    allowed = {"0", "4", "8", "12", "16", "20", "10", "26", "34", "40", "14", "6",
               "30"}   # 30は左軸の目盛りラベルのみ
    return dict(file="L07_fig1_cumulative_stack.svg", canvas=cv, lesson="L07",
                title=title, desc=desc,
                intent="「下から順に積む」動きの可視化（途中を飛ばす誤りの予防）",
                params=f"度数={f}（L06と同一・本文転記）→累積={cums}を再計算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図10: L08-1 同じデータの2通りの棒グラフ（誇張の実験）
# 本文根拠: lesson_08.md 主概念2（A班105本・B班98本・差7本・右図は2倍以上に見える）
# ===========================================================================
def fig_L08_bars():
    ck = Checker()
    a, b = 105, 98
    ck.ok("差=105−98=7本（本文と一致）", a - b == 7)
    ck.ok("差は7%ほど（7÷98≒0.07・本文と一致）", abs((a - b) / b - 0.0714) < 0.01)
    ck.ok("左図（縦軸0から）: 柱の高さの比は1.1倍未満——ほぼ同じ高さに見える",
          a / b < 1.1)
    ck.ok("右図（縦軸95から）: 柱の高さの比は(105−95)/(98−95)＝2倍以上——本文と一致",
          (a - 95) / (b - 95) > 2)

    cv = Canvas(480, 330)
    # 左パネル: 縦軸0〜120
    lbase, ltop = 260, 80
    lscale = (lbase - ltop) / 120
    cv.line(70, lbase, 70, ltop - 6, w=1.2)
    for v in (0, 30, 60, 90, 120):
        cv.line(66, lbase - v * lscale, 70, lbase - v * lscale, w=0.9)
        cv.text(62, lbase - v * lscale + 4, f"{v}", size=10, anchor="end")
    cv.line(70, lbase, 210, lbase, w=1.2)
    for name, v, x in (("A班", a, 100), ("B班", b, 155)):
        cv.rect(x, lbase - v * lscale, 36, v * lscale, sw=1.3, fill="#e6e6e6")
        cv.text(x + 18, lbase + 16, name, size=11)
        cv.text(x + 18, lbase - v * lscale - 6, f"{v}", size=10.5)
    cv.text(140, 62, "縦軸が0から", size=FS_CAP, weight="bold")
    # 右パネル: 縦軸95〜106（途中省略）
    rbase, rtop = 260, 80
    rscale = (rbase - rtop) / (106 - 95)

    def RY(v):
        return rbase - (v - 95) * rscale

    cv.line(300, rbase - 14, 300, rtop - 6, w=1.2)
    # 波線マーク（縦軸が0から始まっていない印）
    cv.polyline([(294, rbase), (306, rbase - 4), (294, rbase - 9),
                 (306, rbase - 14)], w=1.2)
    for v in (95, 100, 105):
        cv.line(296, RY(v), 300, RY(v), w=0.9)
        cv.text(292, RY(v) + 4, f"{v}", size=10, anchor="end")
    cv.line(300, rbase, 440, rbase, w=1.2)
    for name, v, x in (("A班", a, 330), ("B班", b, 385)):
        cv.rect(x, RY(v), 36, rbase - RY(v), sw=1.3, fill="#e6e6e6")
        cv.text(x + 18, rbase + 16, name, size=11)
        cv.text(x + 18, RY(v) - 6, f"{v}", size=10.5)
    cv.text(370, 62, "縦軸が95から（途中を省略）", size=FS_CAP, weight="bold")
    cv.text(240, 26, "同じデータ、2通りの棒グラフ", size=FS, weight="bold")
    cv.text(240, 306, "縦軸: 販売数（本）。データは2枚とも同一（架空の練習用データ）",
            size=11)

    title = "同じデータの2通りの棒グラフ（縦軸の始点操作による誇張の実験）"
    desc = ("L08主概念2の実験図。飲み物販売のA班105本・B班98本という同一のデータを、"
            "左は縦軸0〜120の棒グラフ、右は縦軸95〜106（途中省略・波線マークつき）の"
            "棒グラフで描いた。左では2本の柱はほとんど同じ高さだが、右では縦軸の切り取り"
            "だけでA班の柱がB班の2倍以上の高さに見える。差7本・柱の高さの比（左は1.1倍"
            "未満・右は2倍以上）をassert検算済み。グラフを見たらまず軸の目盛りを確かめる、"
            "の教材図。再現指示: 同じ2値の棒グラフを2枚並べ、右だけ縦軸の始点を上げて"
            "波線の省略マークを付ける。白黒のみ。")
    allowed = {"0", "30", "60", "90", "120", "95", "100", "105", "98", "106", "7", "1.1"}
    return dict(file="L08_fig1_axis_trick_bars.svg", canvas=cv, lesson="L08",
                title=title, desc=desc,
                intent="縦軸の始点操作による視覚的誇張の体感（批判的考察・観点5）",
                params="A班105本・B班98本（本文転記)→差7本・高さ比を左右両図で検算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# メイン: 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_dotplot, fig_L02_outlier, fig_L03_hist, fig_L04_polyline,
        fig_L04_shapes, fig_L05_w2, fig_L05_w8, fig_L06_pair,
        fig_L07_stack, fig_L08_bars]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    total_checks = 0
    for fn in FIGS:
        meta = fn()
        svg = meta["canvas"].render(meta["file"], meta["title"], meta["desc"])
        audit_numbers(svg, meta["allowed"], meta["check_tokens"], meta["file"])
        out = ASSETS / meta["file"]
        out.write_text(svg, encoding="utf-8")
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓"
                           for d, t in meta["checks"])
        if meta["check_tokens"]:
            checks += (f"／答え漏れ検査: PASS（{len(meta['check_tokens'])}項目・"
                       "対象値はanswer_key由来・非開示） ✓")
        else:
            checks += "／数値トークン検査（許可外なし） ✓"
        total_checks += len(meta["checks"])
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: jhs-math-2-quartiles-boxplot/assets_provenance と同一様式（SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — データの分布単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "度数分布は**本文の生データからスクリプト内で再集計**してassert検算"
        "（平均値・中央値・最頻値・相対度数・累積度数も再計算して本文値と照合）。"
        "全図で下表の統計検算（スクリプト内assert）と禁止文字列の機械検査"
        "（<text>/<title>/<desc>の数値トークンを許可リストと照合）が生成時に自動実行され、全件合格。"
        "全SVGにAI再利用メタ情報（<title>=図名・<desc>=意図/主要数値/同型図をAIに描かせる再現指示）を埋め込み済み。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | パラメータ（本文一致） | 検証結果（生成時assert＋機械検査） |",
        "|---|---|---|---|---|",
    ]
    for f, lsn, title, intent, params, checks in rows:
        lines.append(f"| `{f}` | {lsn} | {title}——{intent} | {params} | {checks} |")
    lines += [
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロック"
        "（またはモジュール先頭の共有生データ）を編集する",
        "   （数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。統計検算assert・禁止文字列検査に",
        "   1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n"
        + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {total_checks} checks)")


if __name__ == "__main__":
    main()
