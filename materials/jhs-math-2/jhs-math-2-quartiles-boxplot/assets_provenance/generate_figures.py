#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2数学「四分位範囲と箱ひげ図」単元 図版パラメトリック生成スクリプト
================================================================================
様式: docs/SPEC_figures.md に準拠（コード来歴・白黒両立・答え非記載・<title>/<desc>のAI再利用メタ情報）。
描画ヘルパーは jhs-math-3-sampling-survey/assets_provenance/generate_figures.py の実装を流用（無変更の方針）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（10枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証:
  1) 統計検算assert — 五数要約（最小値・第1四分位数・中央値・第3四分位数・最大値）を
     **教科書方式（中央値で前後半に分割・奇数個は中央値を除外）**で生データから再計算し、
     本文の値と一致しなければ図を出力しない。度数分布も生データから再集計して検算する。
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

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px) — viewBox幅~480で約3%
FS_CAP = 12       # キャプション
DOT_R = 2.5       # 点マーカー半径


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


def five_number_summary(data):
    """五数要約——この単元の教科書方式（L03本文の手順そのもの）。
    ①小さい順に並べる ②中央値（第2四分位数）で前半・後半に分ける。
    **奇数個のとき、ど真ん中の中央値は前半にも後半にも入れない** ③各半分の
    中央値が第1・第3四分位数。本単元のデータは全て整数なので浮動小数誤差は
    出ない（÷2は2進で厳密）。"""
    d = sorted(data)
    n = len(d)

    def med(seg):
        m = len(seg)
        if m % 2 == 1:
            return seg[m // 2]              # 奇数個: ど真ん中の値
        return (seg[m // 2 - 1] + seg[m // 2]) / 2  # 偶数個: 真ん中2つの平均

    if n % 2 == 1:
        lower, upper = d[: n // 2], d[n // 2 + 1:]   # 中央値を除外
    else:
        lower, upper = d[: n // 2], d[n // 2:]
    return dict(min=d[0], q1=med(lower), med=med(d), q3=med(upper), max=d[-1])


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

# レッスンID（L01〜L06）・「主概念1」等の構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "06", "1", "2", "3"}


def audit_numbers(svg, allowed, check_tokens, fig_id):
    """禁止文字列の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。allowed=許可数値トークン集合、check_tokens=答え漏れ検査トークン
    （answer_keyにのみ現れる値・検査の実装定数）。"""
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
# 描画ヘルパー（sampling-survey版から流用。統計図中心のためpx座標で直接描く）
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
            f'(docs/SPEC_figures.md準拠・AI再利用メタ情報つき・SVG直接編集禁止/'
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


def draw_boxplot(cv, X, y, fv, box_h=26, w=MAIN_W, color="#000"):
    """五数要約fv（dict）を座標へ厳密変換して箱ひげ図を1本描く（流用ヘルパー）"""
    xmin, xq1, xmed, xq3, xmax = (X(fv[k]) for k in ("min", "q1", "med", "q3", "max"))
    # 検算: 座標の単調性（数値→座標変換の向き事故防止）
    assert xmin <= xq1 <= xmed <= xq3 <= xmax, "箱ひげ図の座標が単調でない"
    cv.line(xmin, y, xq1, y, w=w, color=color)                    # 左ひげ
    cv.line(xq3, y, xmax, y, w=w, color=color)                    # 右ひげ
    cv.line(xmin, y - box_h * 0.32, xmin, y + box_h * 0.32, w=w, color=color)
    cv.line(xmax, y - box_h * 0.32, xmax, y + box_h * 0.32, w=w, color=color)
    cv.rect(xq1, y - box_h / 2, xq3 - xq1, box_h, sw=w, color=color)
    cv.line(xmed, y - box_h / 2, xmed, y + box_h / 2, w=w, color=color)
    return dict(xmin=xmin, xq1=xq1, xmed=xmed, xq3=xq3, xmax=xmax)


def draw_dotplot(cv, X, y_base, data, r=3.0, step=8.5):
    """ドットプロット（1人1点・同じ値は縦に積む）。戻り値=打点数"""
    seen = {}
    for v in sorted(data):
        k = seen.get(v, 0)
        cv.dot(X(v), y_base - k * step, r=r)
        seen[v] = k + 1
    return sum(seen.values())


# ===========================================================================
# 共有パラメータ: L01の3クラスの生データ（各24人・架空）
# figure-spec生成時制約: ヒストグラム（fig1）と箱ひげ図（fig2）を**同一の生データ**
# から作る（別々に作ると2つの図が食い違うため）。五数要約と山の位置の両方を
# 満たすことを両方の図の生成時にassertで検算する。
# ===========================================================================
CLASS1 = [1, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 6, 7, 8, 8, 9, 9, 10, 11, 12]
CLASS2 = [2, 3, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 7, 7, 7, 8, 9, 9, 9, 10, 10, 11, 11]
CLASS3 = [0, 1, 2, 2, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 6, 6, 7, 8, 9, 11, 13]
FV1_EXPECT = dict(min=1, q1=3, med=5, q3=8, max=12)     # lesson_01本文
FV2_EXPECT = dict(min=2, q1=5, med=7, q3=9, max=11)
FV3_EXPECT = dict(min=0, q1=2, med=4, q3=6, max=13)


def check_l01_data(ck):
    """L01の2図で共通に走る検算（同一データから両図を作る構造の保証）"""
    for name, data, exp in (("1組", CLASS1, FV1_EXPECT), ("2組", CLASS2, FV2_EXPECT),
                            ("3組", CLASS3, FV3_EXPECT)):
        ck.ok(f"{name}: 24人（本文「各24人」と一致）", len(data) == 24)
        fv = five_number_summary(data)
        ck.ok(f"{name}: 五数要約を生データから教科書方式で再計算——本文値と一致",
              fv == exp, f"実測={fv}")
    c1 = freq_counts(CLASS1, 0, 2, 7)
    c2 = freq_counts(CLASS2, 0, 2, 7)
    c3 = freq_counts(CLASS3, 0, 2, 7)
    ck.ok("1組: 山が中央（階級4〜6時間が最多）——本文の分布設定と一致",
          max(c1) == c1[2], f"度数={c1}")
    ck.ok("2組: 山がやや右（階級6〜8時間が最多）——本文の分布設定と一致",
          max(c2) == c2[3], f"度数={c2}")
    ck.ok("3組: 山が左（階級2〜4時間が最多）で右すそが長い——本文の分布設定と一致",
          max(c3) == c3[1] and c3[5] + c3[6] > 0 and c3[1] > c3[5] + c3[6],
          f"度数={c3}")
    return c1, c2, c3


# ===========================================================================
# 図1: L01 3クラスのヒストグラム（比較の大変さの体感）
# 本文根拠: lesson_01.md 主概念1の figure-spec
# ===========================================================================
def fig_L01_hist():
    ck = Checker()
    c1, c2, c3 = check_l01_data(ck)
    ck.ok("3枚とも度数合計=24（生データから再集計）",
          sum(c1) == sum(c2) == sum(c3) == 24)

    cv = Canvas(480, 500)
    panels = [("1組（24人）", c1, 40), ("2組（24人）", c2, 190), ("3組（24人）", c3, 340)]
    yscale = 12.0   # 度数1あたりのpx
    for name, counts, top in panels:
        base = top + 112
        X = int_number_line(cv, 60, 440, base, 0, 14, label_vals=[0, 2, 4, 6, 8, 10, 12, 14],
                            tick_step=2, label_dy=16, label_size=10.5)
        # 度数の縦軸（左端）: 0・4・8にラベル
        for f in (0, 4, 8):
            cv.line(56, base - f * yscale, 60, base - f * yscale, w=0.9)
            cv.text(48, base - f * yscale + 4, f"{f}", size=10.5, anchor="end")
        cv.line(60, base, 60, base - 9.5 * yscale, w=1.2)
        for k, c in enumerate(counts):
            if c > 0:
                cv.rect(X(k * 2), base - c * yscale, X((k + 1) * 2) - X(k * 2),
                        c * yscale, sw=1.3, fill="#e6e6e6")
        cv.text(66, top + 2, name, size=FS, anchor="start", weight="bold")
    cv.text(250, 22, "3クラスの家庭学習時間のヒストグラム", size=FS, weight="bold")
    cv.text(250, 490, "横軸: 家庭学習時間（時間・階級の幅2）／縦軸: 度数（人）"
                      "（架空の練習用データ）", size=11)

    title = "3クラスの家庭学習時間のヒストグラム（3枚縦並び）"
    desc = ("L01主概念1の導入図。3クラス各24人の家庭学習時間（架空の練習用データ）の"
            "ヒストグラム3枚を縦に並べた。階級の幅は2時間・横軸0〜14時間・縦軸は度数。"
            "1組は山が中央、2組は山がやや右、3組は山が左で右すそが長い。形はそれぞれ"
            "分かるが、どのクラスが全体として長いのか一目では判断しにくい——複数集団の"
            "比較には情報の縮約（箱ひげ図）が要る、という必要性を体感させる。度数は"
            "生データから再集計してassert検算済み。同じ生データからL01の箱ひげ図"
            "（L01_fig2）も生成しており、2つの図は食い違わない。再現指示: 同じ横軸"
            "（0〜14・幅2）のヒストグラムを3段に描き、山の位置を中央・右寄り・左寄り"
            "（右すそ長）にする。棒は薄いグレー塗り＋黒枠。白黒のみ。")
    allowed = {"0", "2", "4", "6", "8", "10", "12", "14", "24"}
    return dict(file="L01_fig1_three_class_histograms.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="複数集団はヒストグラムの並置では比べにくい（縮約の必要性の導入）",
                params="3クラス各24人の生データ（fig2と共通）→度数[階級幅2]を再集計",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図2: L01 同じ3クラスの箱ひげ図（初対面・5つの値の名前）
# 本文根拠: lesson_01.md 主概念2の figure-spec（生成時制約=fig1と同一データ）
# 答え漏れ注意: 練習1（2組の五数の読み取り）の答えになる数値ラベルは打たない
# ===========================================================================
def fig_L01_box():
    ck = Checker()
    check_l01_data(ck)
    fv1 = five_number_summary(CLASS1)
    fv2 = five_number_summary(CLASS2)
    fv3 = five_number_summary(CLASS3)
    # 本文の読み取り記述の検算
    ck.ok("「2組の箱はいちばん右」——第1・第3四分位数とも3クラス中最大（本文と一致）",
          fv2["q1"] == max(fv1["q1"], fv2["q1"], fv3["q1"])
          and fv2["q3"] == max(fv1["q3"], fv2["q3"], fv3["q3"]))
    ck.ok("「3組は左寄りで右にひげが長い」——箱が最左・右ひげが最長（本文と一致）",
          fv3["q3"] == min(fv1["q3"], fv2["q3"], fv3["q3"])
          and (fv3["max"] - fv3["q3"]) == max(f["max"] - f["q3"] for f in (fv1, fv2, fv3)))
    # 「箱=真ん中の約半数（約12人）」の検算（1組・境界の扱いでゆれる幅ごと確認）
    strict = sum(1 for v in CLASS1 if fv1["q1"] < v < fv1["q3"])
    incl = sum(1 for v in CLASS1 if fv1["q1"] <= v <= fv1["q3"])
    ck.ok("1組: 箱の区間の人数が約半数（境界を含めない〜含める数え方で12人をはさむ）",
          strict <= 12 <= incl, f"{strict}〜{incl}人")

    cv = Canvas(480, 330)
    X = int_number_line(cv, 60, 440, 285, 0, 14, label_vals=[0, 2, 4, 6, 8, 10, 12, 14],
                        tick_step=1, label_dy=18, label_size=11)
    rows = [("1組", fv1, 118), ("2組", fv2, 185), ("3組", fv3, 245)]
    for name, fv, y in rows:
        draw_boxplot(cv, X, y, fv, box_h=26)
        cv.text(34, y + 4, name, size=FS_CAP, weight="bold")
    # 1組にだけ5つの値の名前を引き出し線で注記（数値は書かない——読み取りは練習）
    y1 = rows[0][2]
    ann = [(fv1["min"], "最小値", 34), (fv1["q1"], "第1四分位数", 62),
           (fv1["med"], "中央値", 34), (fv1["q3"], "第3四分位数", 62),
           (fv1["max"], "最大値", 34)]
    for v, lab, ly in ann:
        cv.line(X(v), ly + 8, X(v), y1 - 16, w=0.8, dash="2 3", color="#888")
        cv.text(X(v), ly, lab, size=11, weight="bold")
    cv.text(250, 318, "横軸: 家庭学習時間（時間）・各クラス24人（架空の練習用データ）",
            size=11)

    title = "3クラスの家庭学習時間の箱ひげ図（5つの値の名前つき）"
    desc = ("L01主概念2の初対面図。同じ数直線（0〜14時間）上に1組・2組・3組の箱ひげ図を"
            "縦に3本並べた。各図は左右にのびる線（ひげ）と中央の箱、箱の中の縦線からなる。"
            "1組にだけ5つの値の名前（最小値・第1四分位数・中央値・第3四分位数・最大値）を"
            "破線の引き出し線で注記した。数値のラベルは意図的に打たない（五数の読み取りは"
            "練習問題のため）。ヒストグラム図（L01_fig1）と同一の生データ各24人分から生成し、"
            "五数要約は教科書方式（中央値で前後半に分割・奇数個は中央値除外）で再計算して"
            "本文と一致をassert検算済み。再現指示: 同じ横軸の上に箱ひげ図を3本並べ、最上段の"
            "1本にだけ五数の名前を引き出し線で添える。数値ラベルなし。白黒のみ。")
    # 「5」は「5つの値」の語のみ（図中に五数の数値ラベルは打っていない）
    allowed = {"0", "2", "4", "6", "8", "10", "12", "14", "24", "5"}
    check_tokens = set()
    return dict(file="L01_fig2_three_class_boxplots.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="箱ひげ図の初対面。3本並置の一覧性と5つの値の名前の導入（数値非記載）",
                params="fig1と同一の生データ→五数を教科書方式で再計算（1組=1/3/5/8/12ほか）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図3: L02 A班のドットプロット＋箱ひげ図（「約半数」を数える）
# 本文根拠: lesson_02.md 主概念1の figure-spec
# ===========================================================================
DATA_A = [12, 14, 15, 16, 17, 18, 18, 19, 20, 21, 22, 23, 24, 26, 28, 31]
DATA_B = [14, 16, 17, 18, 18, 19, 19, 19, 20, 20, 20, 21, 21, 22, 24, 27]
FVA_EXPECT = dict(min=12, q1=16.5, med=19.5, q3=23.5, max=31)
FVB_EXPECT = dict(min=14, q1=18, med=19.5, q3=21, max=27)


def fig_L02_count():
    ck = Checker()
    fva = five_number_summary(DATA_A)
    ck.ok("A班16人・五数要約を生データから教科書方式で再計算——本文値"
          "（12・16.5・19.5・23.5・31）と一致", len(DATA_A) == 16 and fva == FVA_EXPECT,
          f"実測={fva}")
    in_box = sum(1 for v in DATA_A if fva["q1"] < v < fva["q3"])
    left = sum(1 for v in DATA_A if v < fva["q1"])
    right = sum(1 for v in DATA_A if v > fva["q3"])
    ck.ok("箱の区間（16.5〜23.5）のドット=8人（ちょうど半数・本文と一致）", in_box == 8)
    ck.ok("左ひげ側4人・右ひげ側4人（約4分の1ずつ・本文と一致）",
          left == 4 and right == 4)
    ck.ok("範囲=31−12=19回（本文guideと一致）", fva["max"] - fva["min"] == 19)

    cv = Canvas(480, 260)
    X = int_number_line(cv, 55, 445, 205, 10, 32, label_vals=[10, 15, 20, 25, 30],
                        tick_step=1, label_dy=18, label_size=11)
    n_dots = draw_dotplot(cv, X, 108, DATA_A)
    ck.ok("ドットプロットの打点数=16（1人1点）", n_dots == 16)
    draw_boxplot(cv, X, 160, fva, box_h=26)
    cv.text(34, 112, "A班", size=FS_CAP, weight="bold")
    cv.text(250, 30, "A班の上体起こしの回数——ドットプロットと箱ひげ図", size=FS,
            weight="bold")
    cv.text(250, 56, "箱の区間の真上にあるドットを数えてみよう", size=FS_CAP)
    cv.text(250, 244, "横軸: 回数（回）・16人（架空の練習用データ）", size=11)

    title = "A班の上体起こし回数——ドットプロットと箱ひげ図（同じ数直線）"
    desc = ("L02主概念1の実測図。横軸10〜32回の同じ数直線の上に、A班16人の"
            "ドットプロット（1人1点・同じ値の18は縦に2点積む）と、その真下に箱ひげ図を"
            "並べた。箱は第1四分位数16.5から第3四分位数23.5まで、中央値19.5の縦線入り。"
            "箱の区間の真上にあるドットが数えられる配置で、「箱=真ん中の約半数」を自分の"
            "目で数えて確かめる。五数は生データから教科書方式で再計算し本文と一致を"
            "assert検算済み（箱の中8人も検算。右ひげ側の人数は練習の答えのため記載しない）。"
            "再現指示: 同じ"
            "横軸の上段にドットプロット・下段に箱ひげ図を描き、五数の数値ラベルは"
            "打たない。白黒のみ。")
    allowed = {"10", "15", "20", "25", "30", "16", "32", "18", "16.5", "23.5",
               "19.5", "8"}
    check_tokens = {"4人"}   # 練習1の答え（右ひげ側の人数）は図にもdescにも入れない
    return dict(file="L02_fig1_dotplot_boxplot_a.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="「箱=真ん中の約半数」をドットを数えて実測する中心活動の図",
                params=f"A班16人の生データ（本文転記）→五数={fva}・箱内8人を検算",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図4: L02 A班・B班の4段比較（箱の長さ≠人数の反証）
# 本文根拠: lesson_02.md 主概念2の figure-spec
# 答え漏れ注意: B班の範囲13回（練習4の答え）は図にもdescにも入れない
# ===========================================================================
def fig_L02_ab():
    ck = Checker()
    fva = five_number_summary(DATA_A)
    fvb = five_number_summary(DATA_B)
    ck.ok("A班の五数=本文値（12・16.5・19.5・23.5・31）", fva == FVA_EXPECT)
    ck.ok("B班16人・五数要約を生データから再計算——本文値（14・18・19.5・21・27）と一致",
          len(DATA_B) == 16 and fvb == FVB_EXPECT, f"実測={fvb}")
    ck.ok("箱の長さ: A班=7回分・B班=3回分（本文の計算と一致）",
          fva["q3"] - fva["q1"] == 7 and fvb["q3"] - fvb["q1"] == 3)
    ck.ok("同じ人数（16人ずつ）なのに箱の長さが大きく違う（本単元最大の誤概念の反証）",
          len(DATA_A) == len(DATA_B) and (fva["q3"] - fva["q1"]) > 2 * (fvb["q3"] - fvb["q1"]))

    cv = Canvas(480, 360)
    X = int_number_line(cv, 55, 445, 305, 10, 32, label_vals=[10, 15, 20, 25, 30],
                        tick_step=1, label_dy=18, label_size=11)
    na = draw_dotplot(cv, X, 88, DATA_A)
    draw_boxplot(cv, X, 130, fva, box_h=24)
    nb = draw_dotplot(cv, X, 218, DATA_B)
    draw_boxplot(cv, X, 262, fvb, box_h=24)
    ck.ok("ドットは両班とも16個ずつ（図から数えて確かめられる）", na == nb == 16)
    cv.text(34, 92, "A班", size=FS_CAP, weight="bold")
    cv.text(34, 222, "B班", size=FS_CAP, weight="bold")
    cv.text(250, 26, "A班とB班（各16人）——箱の長さは何を表す？", size=FS, weight="bold")
    cv.text(250, 344, "横軸: 上体起こしの回数（回）（架空の練習用データ）", size=11)

    title = "A班とB班の上体起こし回数——ドットプロットつき箱ひげ図の比較（4段）"
    desc = ("L02主概念2の反証図。同じ数直線（10〜32回）の上に、上からA班ドットプロット・"
            "A班箱ひげ図・B班ドットプロット・B班箱ひげ図の4段を並べた。A班の箱"
            "（16.5〜23.5）はB班の箱（18〜21）より明らかに長いが、それぞれの上の"
            "ドットプロットの点はどちらも16個ある——「箱が長い＝人数が多い」の誤読を、"
            "ドットを数えて反証する。両班の五数は生データから教科書方式で再計算し本文と"
            "一致をassert検算済み。再現指示: 同じ横軸に2班分のドットプロット＋箱ひげ図を"
            "4段で描き、五数の数値ラベルは打たない。白黒のみ。")
    allowed = {"10", "15", "20", "25", "30", "16", "32", "16.5", "23.5", "18", "21",
               "4"}   # 「4」は「4段」の語のみ
    check_tokens = {"13"}   # B班の範囲（answer_key練習4の答え）
    return dict(file="L02_fig2_ab_dotplot_boxplot.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="「箱の長さ=個数」の誤概念への中心反証図（同数16人・箱の長さ7対3）",
                params=f"A班・B班各16人の生データ（本文転記）→五数={fva}／{fvb}",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図5: L03 四分位数の場合分けフローチャート
# 本文根拠: lesson_03.md 主概念2の figure-spec
# ===========================================================================
def fig_L03_flow():
    ck = Checker()
    # チャートの手順ロジックそのものを、本文の例1・例2で検算する
    ex1 = [7, 10, 13, 16, 20, 22, 25, 28, 31]          # n=9（奇数）
    ex2 = [12, 14, 15, 17, 19, 21, 24, 26, 28, 30]     # n=10（偶数）
    fv_ex1 = five_number_summary(ex1)
    fv_ex2 = five_number_summary(ex2)
    ck.ok("奇数個の分岐: 例1（n=9）で中央値を除き前半4個・後半4個→11.5/20/26.5（本文と一致）",
          fv_ex1 == dict(min=7, q1=11.5, med=20, q3=26.5, max=31), f"実測={fv_ex1}")
    ck.ok("偶数個の分岐: 例2（n=10）で前半5個・後半5個→15/20/26（本文と一致）",
          fv_ex2 == dict(min=12, q1=15, med=20, q3=26, max=30), f"実測={fv_ex2}")
    ck.ok("奇数個では中央値が前半にも後半にも入らない（4+1+4=9）",
          len(ex1[:4]) + 1 + len(ex1[5:]) == 9)

    cv = Canvas(480, 340)

    def box(x, y, w, h, lines, size=11.5, dash=None, weight=None):
        cv.rect(x, y, w, h, sw=1.4, rx=6, dash=dash)
        y0 = y + h / 2 - (len(lines) - 1) * 8 + 4
        for i, s in enumerate(lines):
            cv.text(x + w / 2, y0 + i * 16, s, size=size, weight=weight)

    box(120, 22, 240, 40, ["① 小さい順に並べ、個数を数える"], weight="bold")
    cv.arrow(240, 62, 240, 84, w=1.4)
    box(120, 84, 240, 40, ["② 全体は偶数個？ 奇数個？"], weight="bold")
    cv.arrow(180, 124, 120, 152, w=1.4)
    cv.text(128, 142, "偶数個", size=11, weight="bold")
    cv.arrow(300, 124, 360, 152, w=1.4)
    cv.text(352, 142, "奇数個", size=11, weight="bold")
    box(20, 152, 210, 74, ["前半・後半にきっちり", "半分ずつ分ける", "（中央値は真ん中2つの平均）"])
    box(250, 152, 210, 74, ["ど真ん中の1個＝中央値。", "これを除いて", "前半・後半に分ける"])
    cv.arrow(125, 226, 200, 254, w=1.4)
    cv.arrow(355, 226, 280, 254, w=1.4)
    box(80, 254, 320, 56, ["③ 前半の中央値＝第1四分位数", "後半の中央値＝第3四分位数"],
        weight="bold")
    cv.text(240, 330, "（各半分が奇数個ならど真ん中の値・偶数個なら真ん中2つの平均）",
            size=11)

    title = "四分位数を求める場合分けフローチャート"
    desc = ("L03主概念2の手順図。①小さい順に並べて個数を数える→②全体が偶数個なら"
            "前半・後半にきっちり半分ずつ（中央値は真ん中2つの平均）、奇数個なら"
            "ど真ん中の1個＝中央値を除いて前半・後半に分ける→③各半分の中央値が"
            "第1・第3四分位数（半分が奇数個ならど真ん中の値・偶数個なら真ん中2つの平均）。"
            "この手順ロジック自体を本文の例1（9個）・例2（10個）に適用して答えが本文と"
            "一致することをassert検算済み。再現指示: 角丸の箱3つと左右分岐2箱を矢印で"
            "つなぎ、分岐ラベルを「偶数個」「奇数個」とする。数値は入れない。白黒のみ。")
    allowed = {"9", "10"}
    return dict(file="L03_fig1_quartile_flowchart.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="場合分けの固定（中央値の除き忘れ・目分量半分のミス防止）",
                params="フロー図（手順ロジックを本文の例1・例2で検算）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図6: L03 例1の4ブロック位置図（区切りの値と幅≠個数）
# 本文根拠: lesson_03.md「検算の型」の記述（例1の数値・幅4.5/8.5の対比）
# ===========================================================================
def fig_L03_blocks():
    ck = Checker()
    ex1 = [7, 10, 13, 16, 20, 22, 25, 28, 31]
    fv = five_number_summary(ex1)
    ck.ok("例1の五数を生データから再計算——本文値（7・11.5・20・26.5・31）と一致",
          fv == dict(min=7, q1=11.5, med=20, q3=26.5, max=31), f"実測={fv}")
    blocks = [[v for v in ex1 if v < fv["q1"]],
              [v for v in ex1 if fv["q1"] < v < fv["med"]],
              [v for v in ex1 if fv["med"] < v < fv["q3"]],
              [v for v in ex1 if v > fv["q3"]]]
    ck.ok("中央値を除いた8個が2個ずつの4ブロックに分かれる（本文の検算の型と一致）",
          [len(b) for b in blocks] == [2, 2, 2, 2], f"内訳={[len(b) for b in blocks]}")
    ck.ok("ブロックの幅はバラバラ: 最小〜第1四分位数=4.5・第1四分位数〜中央値=8.5・"
          "第3四分位数〜最大=4.5（本文の数値と一致）",
          fv["q1"] - fv["min"] == 4.5 and fv["med"] - fv["q1"] == 8.5
          and fv["max"] - fv["q3"] == 4.5)

    cv = Canvas(480, 230)
    X = int_number_line(cv, 50, 450, 130, 5, 33, label_vals=[],
                        tick_step=1, label_dy=18)
    for v in ex1:
        cv.dot(X(v), 130, r=3.2)
        cv.text(X(v), 158, f"{v}", size=11)
    # 区切りの破線と名前・値
    cuts = [(fv["q1"], "第1四分位数", "11.5", 46), (fv["med"], "中央値", "20", 78),
            (fv["q3"], "第3四分位数", "26.5", 46)]
    for v, name, lab, ly in cuts:
        cv.line(X(v), ly + 24, X(v), 142, w=AUX_W, dash=DASH)
        cv.text(X(v), ly, name, size=11, weight="bold")
        cv.text(X(v), ly + 16, lab, size=11)
    # 4ブロックの下カッコと個数
    spans = [(fv["min"], fv["q1"]), (fv["q1"], fv["med"]),
             (fv["med"], fv["q3"]), (fv["q3"], fv["max"])]
    for a, b in spans:
        xa, xb = X(a) + 4, X(b) - 4
        cv.line(xa, 176, xb, 176, w=1.1)
        cv.line(xa, 170, xa, 176, w=1.1)
        cv.line(xb, 170, xb, 176, w=1.1)
        cv.text((xa + xb) / 2, 192, "2個", size=11)
    cv.text(240, 24, "例1（9週間の貸出冊数）——3つの区切りと4ブロック", size=FS,
            weight="bold")
    cv.text(240, 212, "個数はどのブロックも2個ずつ。でも幅はバラバラ——幅≠個数", size=11)
    cv.text(240, 226, "（中央値の20はどちらの半分にも入れない）", size=11)

    title = "例1の4ブロック位置図（四分位数の区切りと「幅≠個数」）"
    desc = ("L03検算の型の可視化図。数直線上に例1の9個のデータ（7・10・13・16・20・22・"
            "25・28・31）を黒点と数値で置き、第1四分位数11.5・中央値20・第3四分位数26.5の"
            "位置に破線の区切りを立てた。区切りの間の4ブロックはどれも2個ずつ（中央値は"
            "除外）だが、数直線上の幅はバラバラ——「幅が広い＝個数が多い、ではない」を"
            "計算の側から見せる。五数・ブロック個数・幅はすべて生データから再計算して"
            "assert検算済み。再現指示: 数直線に9個の値を打点し、3本の破線区切りと"
            "各ブロック下の「2個」ラベルを添える。白黒のみ。")
    allowed = {"7", "10", "13", "16", "20", "22", "25", "28", "31", "11.5", "26.5",
               "9", "4"}
    return dict(file="L03_fig2_quartile_blocks.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="「4等分の区切り」の意味の固定と、幅≠個数の計算側からの確認",
                params=f"例1の生データ9個（本文転記）→五数={fv}・4ブロック2個ずつ",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図7: L04 かく手順の見本（Aデータ・手順①〜④つき）
# 本文根拠: lesson_04.md 主概念3の figure-spec
# ===========================================================================
DATA_BOOKS_A = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 35]
DATA_BOOKS_B = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]


def fig_L04_steps():
    ck = Checker()
    fva = five_number_summary(DATA_BOOKS_A)
    ck.ok("Aデータ11人の五数を生データから再計算——本文値（0・3・6・9・35）と一致",
          len(DATA_BOOKS_A) == 11 and fva == dict(min=0, q1=3, med=6, q3=9, max=35),
          f"実測={fva}")
    ck.ok("右のひげが左のひげよりはるかに長い（かけ離れた値35の効果・本文と一致）",
          (fva["max"] - fva["q3"]) > 8 * (fva["q1"] - fva["min"]))
    ck.ok("範囲=35・四分位範囲=6（本文の実験の値と一致）",
          fva["max"] - fva["min"] == 35 and fva["q3"] - fva["q1"] == 6)

    cv = Canvas(480, 250)
    X = int_number_line(cv, 50, 450, 185, 0, 36, label_vals=[0, 5, 10, 15, 20, 25, 30, 35],
                        tick_step=1, label_dy=18, label_size=11)
    y = 120
    draw_boxplot(cv, X, y, fva, box_h=28)
    # 手順番号の注記（丸数字は数値トークンにならない）
    cv.text(X(35), 210, "", size=1)
    cv.line(X(fva["q1"]) + 4, y - 46, X(fva["q1"]) + 14, y - 17, w=0.9, color="#888")
    cv.text(X(fva["q1"]) - 2, y - 52, "③ 箱（第1四分位数〜第3四分位数）と中央値の縦線",
            size=11, anchor="start")
    cv.line(X(1.5), y + 22, X(1.5), y + 6, w=0.9, color="#888")
    cv.text(X(1.5), y + 36, "④ 左のひげは最小値まで", size=11, anchor="start")
    cv.line(X(24), y - 22, X(24), y - 6, w=0.9, color="#888")
    cv.text(X(24), y - 28, "④ 右のひげは最大値まで", size=11)
    cv.text(56, 218, "② 数直線（データ全体が収まる目盛り）", size=11, anchor="start")
    cv.text(250, 28, "① 5つの値を求めてから——箱ひげ図をかく手順", size=FS, weight="bold")
    cv.text(250, 242, "横軸: 借りた本の冊数（冊）・11人（架空の練習用データ）", size=11)

    title = "箱ひげ図をかく手順の見本（Aデータ・手順①〜④つき）"
    desc = ("L04主概念3の手順見本図。冊数0〜36の数直線上にAデータ（11人・35冊の読書家を"
            "含む）の箱ひげ図を1本描き、かく手順①5つの値を求める・②数直線・③箱と中央値の"
            "縦線・④左右のひげ、の番号を対応箇所に添えた。箱は第1四分位数3から第3四分位数"
            "9まで・中央値6の縦線入り。左のひげは0まで短く、右のひげは35まで非常に長い——"
            "極端にかけ離れた値がひげをのばす様子も同時に見せる。五数は生データから教科書"
            "方式で再計算し本文と一致をassert検算済み。再現指示: 数直線上の箱ひげ図1本に"
            "手順番号①〜④の注記を引き出し線で添える。五数の数値ラベルは打たない。白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "25", "30", "35", "36", "11", "6", "9"}
    return dict(file="L04_fig1_boxplot_draw_steps.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="かく手順①〜④の見本＋かけ離れた値が右ひげをのばす様子の同時提示",
                params=f"Aデータ11人（本文転記）→五数={fva}・範囲35・四分位範囲6",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図8: L04 差し替え実験の比較図（35冊→12冊で箱は動かない）
# 本文根拠: lesson_04.md 主概念1・2の実験（表の可視化・追加図）
# ===========================================================================
def fig_L04_experiment():
    ck = Checker()
    fva = five_number_summary(DATA_BOOKS_A)
    fvb = five_number_summary(DATA_BOOKS_B)
    ck.ok("A（35冊あり）の五数=0・3・6・9・35（本文と一致）",
          fva == dict(min=0, q1=3, med=6, q3=9, max=35))
    ck.ok("B（12冊に差し替え）の五数を再計算——四分位数は0・3・6・9のまま・最大だけ12",
          fvb == dict(min=0, q1=3, med=6, q3=9, max=12), f"実測={fvb}")
    ck.ok("範囲は35→12へ激変（本文の表と一致）",
          fva["max"] - fva["min"] == 35 and fvb["max"] - fvb["min"] == 12)
    ck.ok("四分位範囲はどちらも6で不変（本文と一致）",
          fva["q3"] - fva["q1"] == fvb["q3"] - fvb["q1"] == 6)
    ck.ok("箱（第1〜第3四分位数）と中央値が完全に一致（「1ミリも動かない」の検算）",
          all(fva[k] == fvb[k] for k in ("q1", "med", "q3")))

    cv = Canvas(480, 330)
    X = int_number_line(cv, 50, 450, 265, 0, 36, label_vals=[0, 5, 10, 15, 20, 25, 30, 35],
                        tick_step=1, label_dy=18, label_size=11)
    ya, yb = 95, 205
    draw_boxplot(cv, X, ya, fva, box_h=26)
    draw_boxplot(cv, X, yb, fvb, box_h=26)
    cv.text(56, ya - 26, "A（35冊の生徒あり）", size=FS_CAP, anchor="start", weight="bold")
    cv.text(56, yb - 26, "B（35冊→12冊に差し替え）", size=FS_CAP, anchor="start",
            weight="bold")
    # 箱が動かないことを示す破線ガイド（第1・第3四分位数の位置を上下に通す）
    for v in (fva["q1"], fva["q3"]):
        cv.line(X(v), ya + 16, X(v), yb - 40, w=AUX_W, dash=DASH)
    cv.text(X(6), (ya + yb) / 2 - 6, "箱は", size=11)
    cv.text(X(6), (ya + yb) / 2 + 8, "動かない", size=11)
    cv.arrow(X(34), (ya + yb) / 2, X(13.5), (ya + yb) / 2, w=1.2, dash=DASH)
    cv.text(X(24), (ya + yb) / 2 - 10, "右のひげだけが縮む", size=11)
    cv.text(250, 28, "差し替え実験——範囲は激変・四分位数は不変", size=FS, weight="bold")
    cv.text(250, 318, "横軸: 借りた本の冊数（冊）・各11人（架空の練習用データ）", size=11)

    title = "差し替え実験の箱ひげ図比較（35冊→12冊で箱は動かない）"
    desc = ("L04主概念1・2の実験の可視化図。同じ数直線（0〜36冊）にA（35冊の読書家あり）と"
            "B（その1人を12冊に差し替え）の箱ひげ図を上下に並べた。第1四分位数・中央値・"
            "第3四分位数の位置は2本で完全に同じ（破線ガイドで上下対応）で、右のひげの長さ"
            "だけが激変する——範囲はかけ離れた値の影響を受けやすく、四分位範囲はほとんど"
            "受けない、という本文の実験を図で確かめる。両データの五数は生データから再計算し"
            "本文の表と一致をassert検算済み。再現指示: 同じ横軸に箱ひげ図2本を並べ、四分位数"
            "位置の不変を破線で、右ひげの短縮を矢印で示す。白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "25", "30", "35", "36", "12", "11", "6"}
    return dict(file="L04_fig2_outlier_swap_experiment.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="範囲とかけ離れた値の実験の可視化（箱の不変＝四分位範囲の頑健さ）",
                params=f"A・B各11人の生データ（本文転記）→五数={fva}／{fvb}",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図9: L05 A組・B組の比較図（箱が短いのに位置が右）
# 本文根拠: lesson_05.md 主概念1の figure-spec（五数の形で提示・生データなし）
# 注: 本図のみ生データが本文にない（五数提示型）ため、検算は五数の整合
#     （並び順・箱の長さ・位置関係が本文記述と一致するか）で行う
# ===========================================================================
def fig_L05_ab():
    # --- パラメータ（lesson_05.md 本文の五数をそのまま転記） ---
    fva = dict(min=2, q1=5, med=8, q3=12, max=16)
    fvb = dict(min=4, q1=9, med=11, q3=13, max=18)

    ck = Checker()
    for name, fv in (("A組", fva), ("B組", fvb)):
        ck.ok(f"{name}: 五数が小さい順に並ぶ（作図前の整合検算）",
              fv["min"] <= fv["q1"] <= fv["med"] <= fv["q3"] <= fv["max"])
    ck.ok("箱の長さ: A組=7時間分・B組=4時間分（本文の計算と一致）",
          fva["q3"] - fva["q1"] == 7 and fvb["q3"] - fvb["q1"] == 4)
    ck.ok("B組の箱が短いのに位置は右——第1・第3四分位数・中央値ともB組が大きい（本文と一致）",
          fvb["q1"] > fva["q1"] and fvb["q3"] > fva["q3"] and fvb["med"] > fva["med"])
    ck.ok("箱は重なる（パターン3は使えない配置——本文の設計と一致）",
          fvb["q1"] < fva["q3"])
    ck.ok("A組の最大値はB組の中央値より上（「全員が長い」とは言えない根拠・本文guideと一致)",
          fva["max"] > fvb["med"])

    cv = Canvas(480, 250)
    X = int_number_line(cv, 55, 445, 190, 0, 20, label_vals=[0, 5, 10, 15, 20],
                        tick_step=1, label_dy=18, label_size=11)
    draw_boxplot(cv, X, 90, fva, box_h=26)
    draw_boxplot(cv, X, 150, fvb, box_h=26)
    cv.text(34, 94, "A組", size=FS_CAP, weight="bold")
    cv.text(34, 154, "B組", size=FS_CAP, weight="bold")
    cv.text(250, 28, "1か月の読書時間（各35人）——どちらが長い傾向？", size=FS,
            weight="bold")
    cv.text(250, 232, "横軸: 読書時間（時間）（架空の練習用データ）", size=11)

    title = "A組とB組の読書時間の箱ひげ図（箱が短いのに位置が右）"
    desc = ("L05主概念1の主教材図。横軸0〜20時間の同じ数直線にA組・B組（各35人）の"
            "箱ひげ図を並べた。A組の箱は長く、B組の箱は短いが全体に右側にある——"
            "「長い方が上」「短い方が少ない」の両誤読を同時に試せる配置。比較の根拠は"
            "箱の位置・中央値・四分位数で語る（箱の長さは散らばりの幅）。五数の数値"
            "ラベルは打たない（値の読み取りと記述が練習のため）。五数の並び順・箱の"
            "長さの比・位置関係が本文記述と一致することをassert検算済み。再現指示: "
            "同じ横軸に箱ひげ図2本。上の箱を長く左寄り、下の箱を短く右寄りに描く。"
            "白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "35"}
    return dict(file="L05_fig1_ab_reading_boxplots.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="位置と長さの分離を試す比較の主教材（数値非記載・読み取りは練習）",
                params="A組=2/5/8/12/16・B組=4/9/11/13/18（本文の五数提示を転記・整合検算）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# 図10: L06 二山分布のヒストグラムと箱ひげ図（限界の体感）
# 本文根拠: lesson_06.md 主概念3の figure-spec（QA修正後の度数=[20,25)5人・[25,30)3人）
# ===========================================================================
def fig_L06_bimodal():
    ck = Checker()
    commute = [5, 6, 6, 7, 7, 8, 8, 9, 22, 23, 23, 24, 24, 25, 25, 26]
    fv = five_number_summary(commute)
    ck.ok("通学時間16人の五数を生データから再計算——本文値（5・7・15.5・24・26）と一致",
          len(commute) == 16 and fv == dict(min=5, q1=7, med=15.5, q3=24, max=26),
          f"実測={fv}")
    counts = freq_counts(commute, 0, 5, 6)   # 階級 [0,5)〜[25,30)・以上〜未満
    ck.ok("度数分布を生データから再集計——QA修正後のfigure-spec値"
          "（5〜10分に8人・20〜25分に5人・25〜30分に3人・10〜20分は0人）と一致",
          counts == [0, 8, 0, 0, 5, 3], f"実測={counts}")
    ck.ok("値25の2個は「25以上30未満」に入る（半開区間の扱い・figure-spec指定と一致）",
          counts[5] == 3 and commute.count(25) == 2)
    ck.ok("二山分布: 山が2つ・真ん中の2階級は度数0（本文の主旨）",
          counts[1] > 0 and counts[4] > 0 and counts[2] == counts[3] == 0)
    ck.ok("中央値15.5は度数0の谷間に落ちる（「15分前後の生徒は1人もいない」の検算）",
          10 <= fv["med"] < 20 and sum(1 for v in commute if 10 < v < 20) == 0)

    cv = Canvas(480, 360)
    X = int_number_line(cv, 60, 440, 190, 0, 30, label_vals=[0, 5, 10, 15, 20, 25, 30],
                        tick_step=1, label_dy=17, label_size=11)
    # 上段: ヒストグラム
    yscale = 14.0
    cv.line(60, 190, 60, 190 - 9 * yscale, w=1.2)
    for f in (0, 4, 8):
        cv.line(56, 190 - f * yscale, 60, 190 - f * yscale, w=0.9)
        cv.text(48, 190 - f * yscale + 4, f"{f}", size=10.5, anchor="end")
    for k, c in enumerate(counts):
        if c > 0:
            cv.rect(X(k * 5), 190 - c * yscale, X((k + 1) * 5) - X(k * 5),
                    c * yscale, sw=1.3, fill="#e6e6e6")
    cv.text(66, 52, "度数（人）", size=10.5, anchor="start")
    # 下段: 同じ横軸スケールの箱ひげ図
    yb = 265
    X2 = int_number_line(cv, 60, 440, 310, 0, 30, label_vals=[0, 5, 10, 15, 20, 25, 30],
                         tick_step=1, label_dy=17, label_size=11)
    draw_boxplot(cv, X2, yb, fv, box_h=28)
    cv.text(250, 26, "同じ通学時間データの2つの顔——ヒストグラムと箱ひげ図", size=FS,
            weight="bold")
    cv.text(250, 348, "横軸: 通学時間（分）・16人（架空の練習用データ）", size=11)

    title = "二山分布のヒストグラムと箱ひげ図（箱ひげ図の限界）"
    desc = ("L06主概念3の限界体感図。横軸0〜30分を上下段で共通にし、上段に16人の通学時間の"
            "ヒストグラム（階級幅5分・以上〜未満）、下段に同じデータの箱ひげ図を描いた。"
            "ヒストグラムは左（5〜10分に8人）と右（20〜25分に5人・25〜30分に3人）に山が"
            "2つあり、真ん中（10〜20分）は度数0。同じデータの箱ひげ図は7から24までの大きな"
            "箱に15.5の中央値線が入るだけで、二山の情報が見えない——五数への縮約で分布の形が"
            "失われることを対比で体感させる。五数・度数とも生データから再計算してassert検算済み"
            "（度数はQA修正後の値）。再現指示: 同じ横軸スケールの上段ヒストグラム＋下段"
            "箱ひげ図。二山の間の階級を空にする。白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "25", "30", "4", "8", "16", "15.5", "24", "7"}
    return dict(file="L06_fig1_bimodal_hist_boxplot.svg", canvas=cv, lesson="L06",
                title=title, desc=desc,
                intent="五数への縮約で二山が消える対比（箱ひげ図の限界の中心図）",
                params=f"通学時間16人の生データ（本文転記）→五数={fv}・度数={counts}"
                       "（QA修正後: [20,25)=5人・[25,30)=3人）",
                checks=ck.items, allowed=allowed, check_tokens=set())


# ===========================================================================
# メイン: 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_hist, fig_L01_box, fig_L02_count, fig_L02_ab,
        fig_L03_flow, fig_L03_blocks, fig_L04_steps, fig_L04_experiment,
        fig_L05_ab, fig_L06_bimodal]


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
        "spec: docs/SPEC_figures.md 準拠（SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 四分位範囲と箱ひげ図単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "五数要約は**教科書方式**（中央値で前後半に分割・奇数個は中央値を除外）で"
        "生データから再計算してassert検算。度数分布も生データから再集計して検算。"
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
