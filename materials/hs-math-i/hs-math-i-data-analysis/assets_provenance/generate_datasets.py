#!/usr/bin/env python3
"""数Ⅰ「データの分析」——全レッスン共通のデータ生成スクリプト（標準ライブラリのみ）。

- 本文の表に載せるデータはすべて自作・架空・小規模（10〜20個）。関数が返す値が正本。
- L01〜L03 のデータは手で設計した定数（乱数ではない）。設計意図は各関数の docstring。
- 「多数回の実験」（L07〜L08 用）は coin_counts(seed=20260902) が固定シードで生成する。
- L04〜L06・L07〜L09 の関数群は 2026-09-02 に追記。
- `python3 generate_datasets.py` で全表を Markdown 表として標準出力に出し、
  同時に本文で使う統計量（平均値 m・分散 s²・標準偏差 s・四分位数・外れ値）を再計算して
  設計値と一致することを assert で確かめる（不一致なら終了コード 1）。

四分位数の方式: 中2教材（jhs-math-2-quartiles-boxplot L03）の採用方式をそのまま踏襲する。
  (1) 小さい順に並べる (2) 中央値で前半・後半に分ける——奇数個のとき中央値はどちらにも入れない
  (3) 前半の中央値が第1四分位数、後半の中央値が第3四分位数。
分散の方式: 偏差の2乗の平均（データの総数 n で割る）= statistics.pvariance。
"""
from __future__ import annotations

import random
import statistics
import sys
from fractions import Fraction as F

COIN_SEED = 20260902


# ---------------------------------------------------------------------------
# 統計量（本文と同じ手順で計算する）
# ---------------------------------------------------------------------------
def mean(data):
    return F(sum(data), len(data))


def pvariance(data):
    m = mean(data)
    return F(sum((F(x) - m) ** 2 for x in data), len(data))


def median(seg):
    d = sorted(seg)
    k = len(d)
    if k % 2 == 1:
        return F(d[k // 2])
    return F(d[k // 2 - 1] + d[k // 2], 2)


def quartiles(data):
    """五数要約（中2方式）。"""
    d = sorted(data)
    n = len(d)
    if n % 2 == 1:
        lower, upper = d[: n // 2], d[n // 2 + 1:]
    else:
        lower, upper = d[: n // 2], d[n // 2:]
    return dict(min=F(d[0]), q1=median(lower), med=median(d), q3=median(upper), max=F(d[-1]))


def outliers(data):
    """外れ値（教科書標準）: Q1−1.5×IQR 未満、Q3＋1.5×IQR 超。戻り値=(外れ値, 下境界, 上境界)。"""
    fv = quartiles(data)
    iqr = fv["q3"] - fv["q1"]
    lo, hi = fv["q1"] - F(3, 2) * iqr, fv["q3"] + F(3, 2) * iqr
    return [x for x in data if x < lo or x > hi], lo, hi


def fnum(x):
    """Fraction を本文表記の文字列に。"""
    x = F(x)
    txt = str(x.numerator) if x.denominator == 1 else f"{float(x):g}"
    return txt.replace("-", "−")  # 負号は本文と同じ U+2212


# ---------------------------------------------------------------------------
# L01 中学の道具を棚卸しする——代表値・四分位範囲・箱ひげ図と「外れ値」
# ---------------------------------------------------------------------------
def l01_library_visits():
    """A班・B班（各11人）の先月1か月間の図書室利用回数（回）。
    設計: 平均値・中央値・最頻値がどちらも 8 で一致するのに、散らばりが違う。
    A班は外れ値 18 を1つ持ち（図書委員という背景=異常値ではない）、箱は短いのに範囲は大きい。"""
    return dict(
        A=[3, 5, 6, 6, 7, 8, 8, 8, 9, 10, 18],
        B=[2, 4, 5, 6, 8, 8, 9, 10, 11, 12, 13],
    )


def l01_practice():
    return dict(
        q1_quiz=[5, 6, 7, 7, 8, 8, 8, 9],                      # 問1: 8回の小テスト（10点満点）
        q2_odd=[3, 5, 6, 8, 9, 11, 12, 14, 17],                # 問2(1): 9個
        q2_even=[2, 4, 5, 5, 7, 8, 9, 10, 12, 15],             # 問2(2): 10個
        q4_outlier=[5, 8, 9, 10, 10, 11, 12, 13, 14, 15, 16, 28],  # 問4: 12個・外れ値28
    )


# ---------------------------------------------------------------------------
# L02 散らばりを1つの数にする——分散と標準偏差
# ---------------------------------------------------------------------------
def l02_freethrow():
    """Aさん・Bさんの5日間のフリースロー成功数（20本中）。
    設計: 平均値 14・中央値 14 が同じで、分散が 4（s=2）と 16（s=4）。"""
    return dict(A=[11, 13, 14, 15, 17], B=[8, 12, 14, 16, 20])


def l02_example2():
    """L02 例題1: Cさんの6日間のフリースロー成功数（20本中）。設計: m=14・s²=10・s=√10（整数にならない例）。"""
    return [9, 12, 13, 15, 16, 19]


def l02_test20():
    """1組20人の小テスト（100点満点）の得点。設計: m=60・偏差の2乗の和 2000・s=10。
    m±2s の帯（40以上80以下）に 19 人、外は 83 の1人。"""
    return [42, 44, 48, 52, 54, 54, 54, 57, 57, 59, 61, 61, 63, 63, 66, 66, 68, 72, 76, 83]


def l02_practice():
    return dict(
        q1=[2, 4, 5, 6, 8],                                    # 問1: m=5, s=2
        q2=[5, 7, 9, 9, 11, 11, 13, 15],                       # 問2: m=10, s=3
        q3_X=[5, 7, 8, 9, 11],                                 # 問3: m=8, s=2
        q3_Y=[2, 6, 8, 10, 14],                                # 問3: m=8, s=4
        q4=[14, 15, 17, 19, 20, 22, 22, 31],                   # 問4: m=20, s=5・帯の外は31
        s1=[2, 3, 7],                                          # S1: 平均値 4・中央値 3
    )


# ---------------------------------------------------------------------------
# L03 分散・標準偏差を使う——2つのデータの比較と変量の変換
# ---------------------------------------------------------------------------
def l03_test20_class2():
    """2組20人の小テスト（100点満点）の得点。設計: m=60（1組と同じ）・偏差は ±38, ±30, ±25,
    ±20, ±15, ±12, ±10, ±8, ±7, ±7 の対称な組・偏差の2乗の和 8000・s=20。"""
    return [22, 30, 35, 40, 45, 48, 50, 52, 53, 53, 67, 67, 68, 70, 72, 75, 80, 85, 90, 98]


def l03_commute_table():
    """16人の通学時間（分）の度数分布表。設計: 階級値 5,15,25,35,45・度数 1,4,6,4,1・
    階級値から求めた m=25・分散 100・s=10。"""
    return dict(classes=[(0, 10), (10, 20), (20, 30), (30, 40), (40, 50)],
                values=[5, 15, 25, 35, 45], freqs=[1, 4, 6, 4, 1])


def l03_transform_base():
    """変量の変換の土台: L02 の Aさんの記録（m=14・s=2）。+3（3本ずつ加算）と ×5（100点換算）。"""
    return l02_freethrow()["A"]


def l03_heights():
    """仮平均の例: 5人の身長（cm）。仮平均 170 との差 −5,−3,−2,−1,1 → m=168・s=2。"""
    return [165, 167, 168, 169, 171]


def l03_practice():
    return dict(
        q1_X=[5, 7, 7, 8, 10, 11],                             # 問1: m=8, s=2
        q1_Y=[3, 3, 8, 9, 11, 14],                             # 問1: m=8, s=4
        q2_table=dict(values=[15, 25, 35, 45, 55], freqs=[1, 1, 6, 1, 1]),  # 問2: m=35, s=10
        q3=[3, 5, 5, 6, 8, 9],                                 # 問3: m=6, s=2 → +4／×3
        q4=[153, 155, 155, 156, 158, 159],                     # 問4: 仮平均155 → m=156, s=2
        s1=[17, 19, 20, 21, 23],                               # S1: 気温（℃）m=20, s=2 → 華氏
    )


# ---------------------------------------------------------------------------
# L07〜L08 用: コイン30回投げ×200回の「表の枚数」（固定シード）
# ---------------------------------------------------------------------------
def coin_counts(seed=COIN_SEED, n_trials=200, n_toss=30):
    """コインを n_toss 回投げて表の枚数を数える試行を n_trials 回。
    各回は sum(rng.random() < 0.5 for _ in range(n_toss))。generate_figures.py の simulate_coin() と同じ列。"""
    rng = random.Random(seed)
    return [sum(rng.random() < 0.5 for _ in range(n_toss)) for _ in range(n_trials)]


# ===========================================================================
# L04〜L06（2026-09-02 追記）
# - すべて手設計の固定リテラル（乱数なし）。seed 引数は上の関数群との互換のため受け取るが使わない。
# - 分散は n で割る・共分散は偏差の積の平均・r=共分散÷(sx×sy)。四分位数・外れ値は上の
#   quartiles()／outliers()（中2方式）をそのまま使う（同じ方式のため二重定義しない）。
# - verify_l04_l06() が本文（lesson_04〜06）に書いた統計量を assert で照合し、偏差・積の表を印字する。
# ===========================================================================
import math


def mean_of(v):
    v = [F(str(a)) for a in v]
    return sum(v) / len(v)


def dev(v):
    m = mean_of(v)
    return [F(str(a)) - m for a in v]


def var_of(v):
    d = dev(v)
    return sum(a * a for a in d) / len(d)


def sd_of(v):
    return math.sqrt(var_of(v))


def cov_of(xs, ys):
    dx, dy = dev(xs), dev(ys)
    return sum(a * b for a, b in zip(dx, dy)) / len(dx)


def corr_of(xs, ys):
    r = float(cov_of(xs, ys)) / (sd_of(xs) * sd_of(ys))
    # 対照: statistics モジュールでも同じ値（相関係数は n で割っても n−1 で割っても同じ）
    r2 = statistics.correlation([float(a) for a in xs], [float(b) for b in ys])
    assert abs(r - r2) < 1e-9, (r, r2)
    return r


# ---------- L04 ----------

def L04_fig1_three_types(seed=None):
    """L04 §1 表（散布図3パネル A・B・C）。x は 1〜8 共通"""
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    return {"x": x,
            "A": [2, 3, 5, 4, 6, 5, 7, 8],
            "B": [8, 6, 7, 5, 4, 2, 3, 1],
            "C": [5, 2, 7, 4, 8, 3, 6, 4]}


def L04_ex1_temperature_drinks(seed=None):
    """L04 例題1: 6日間の最高気温 x（℃）と冷たい飲み物の売上 y（本）。fig2 と共通"""
    return {"x": [20, 23, 24, 27, 27, 29], "y": [33, 39, 41, 38, 44, 45]}


def L04_ex2_sprint_longjump(seed=None):
    """L04 例題2: 5人の 100 m 走 x（秒）と走り幅跳び y（cm）"""
    return {"x": [13.3, 12.7, 13.1, 12.9, 13.0], "y": [470, 530, 510, 490, 500]}


def L04_q3_ads_sales(seed=None):
    """L04 問3: 5店舗の広告費 x（万円）と売上 y（万円）"""
    return {"x": [8, 2, 6, 4, 5], "y": [330, 270, 290, 310, 300]}


def L04_q4_shoes_score(seed=None):
    """L04 問4: 5人の靴のサイズ x（cm）と小テスト y（点）"""
    return {"x": [28, 22, 26, 24, 25], "y": [61, 59, 57, 63, 60]}


def L04_s1_lines(seed=None):
    """L04 S1: y=2x＋1 と y=−2x＋13 の5組"""
    x = [1, 2, 3, 4, 5]
    return {"x": x, "y_up": [2 * a + 1 for a in x], "y_down": [-2 * a + 13 for a in x]}


# ---------- L05 ----------

def L05_breakfast_score(seed=None):
    """L05 §1: 8人の朝食日数 x（日・20日中）と小テスト y（点・20点満点）"""
    return {"x": [20, 18, 16, 15, 12, 10, 8, 5], "y": [18, 16, 14, 16, 12, 13, 8, 7]}


def L05_ex1_ushape(seed=None):
    """L05 例題1: 7日間の最高気温 x（℃）と電気使用量 y（kWh）——U字・r=0"""
    return {"x": [5, 10, 15, 20, 25, 30, 35], "y": [19, 14, 11, 10, 11, 14, 19]}


def L05_ex2_basketball(seed=None):
    """L05 例題2・fig1: 8人の自主練習時間 x（時間）とシュート成功数 y（本）。部員8が外れ値"""
    return {"x": [2, 3, 4, 5, 6, 7, 8, 13], "y": [3, 5, 4, 6, 2, 5, 3, 12]}


def L05_s1_basketball_alt(seed=None):
    """L05 S1: 部員8を (13, 0) に置き換えた8人"""
    return {"x": [2, 3, 4, 5, 6, 7, 8, 13], "y": [3, 5, 4, 6, 2, 5, 3, 0]}


def L05_table_workbook(seed=None):
    """L05 §4: 問題集の使用と合否（90人）。(合格, 不合格) を 学年×使用 で持つ"""
    return {("1年", "使った"): (4, 6), ("1年", "使わなかった"): (20, 20),
            ("2年", "使った"): (24, 6), ("2年", "使わなかった"): (9, 1)}


def L05_q4_bicycle(seed=None):
    """L05 問4: 通学手段と遅刻（60人）。(遅刻あり, 遅刻なし) を 距離×手段 で持つ"""
    return {("近い", "自転車"): (1, 9), ("近い", "徒歩"): (4, 20),
            ("遠い", "自転車"): (8, 12), ("遠い", "徒歩"): (3, 3)}


# ---------- L06 ----------

def L06_jumprope_trials(seed=None):
    """L06 §2: 大縄跳び 20 試技（試技番号・並び方・回し手・連続回数）"""
    return [(1, "1列", "A", 8), (2, "1列", "A", 12), (3, "1列", "B", 10), (4, "1列", "A", 15),
            (5, "1列", "B", 11), (6, "2列", "A", 14), (7, "1列", "B", 17), (8, "2列", "B", 19),
            (9, "1列", "A", 13), (10, "2列", "A", 22), (11, "1列", "B", 18), (12, "2列", "B", 25),
            (13, "1列", "A", 16), (14, "2列", "A", 21), (15, "2列", "B", 28), (16, "1列", "B", 20),
            (17, "2列", "A", 24), (18, "2列", "B", 30), (19, "2列", "A", 27), (20, "2列", "B", 33)]


# ---------- 検算（本文に書いた値との照合）——verify_l04_l06() ----------

def _report_xy(label, xs, ys):
    dx, dy = dev(xs), dev(ys)
    prods = [a * b for a, b in zip(dx, dy)]
    print(f"\n### {label}（n={len(xs)}）")
    print("| 番号 | x | y | x の偏差 | y の偏差 | x 偏差² | y 偏差² | 偏差の積 |")
    print("|---|---|---|---|---|---|---|---|")
    for i, (x, y, a, b, p) in enumerate(zip(xs, ys, dx, dy, prods), 1):
        print(f"| {i} | {x} | {y} | {a} | {b} | {a*a} | {b*b} | {p} |")
    print(f"| 合計 | | | {sum(dx)} | {sum(dy)} | {sum(a*a for a in dx)} | {sum(b*b for b in dy)} | {sum(prods)} |")
    r = corr_of(xs, ys)
    print(f"mx={mean_of(xs)} my={mean_of(ys)} x分散={var_of(xs)} y分散={var_of(ys)} "
          f"共分散={cov_of(xs, ys)} sx={sd_of(xs):.4f} sy={sd_of(ys):.4f} r={r:.4f}")
    return r


def verify_l04_l06():
    """L04〜L06 の本文に書いた統計量を全件 assert で照合（1件でも食い違えば例外で停止）。"""
    ok = []
    # L04 fig1
    d = L04_fig1_three_types()
    rA = _report_xy("L04 §1 A（正の相関）", d["x"], d["A"])
    rB = _report_xy("L04 §1 B（負の相関）", d["x"], d["B"])
    rC = _report_xy("L04 §1 C（相関なし）", d["x"], d["C"])
    assert rA > 0.7 and rB < -0.7 and abs(rC) < 0.2, (rA, rB, rC)
    assert all(1 <= v <= 8 for k in ("A", "B", "C") for v in d[k])
    ok.append("L04 fig1: A r=%.2f / B r=%.2f / C r=%.2f" % (rA, rB, rC))
    # L04 例題1
    d = L04_ex1_temperature_drinks()
    r = _report_xy("L04 例題1", d["x"], d["y"])
    assert mean_of(d["x"]) == 25 and mean_of(d["y"]) == 40
    assert var_of(d["x"]) == 9 and var_of(d["y"]) == 16 and cov_of(d["x"], d["y"]) == 10
    assert abs(r - 5 / 6) < 1e-12
    assert all(a != 0 for a in dev(d["x"])) and all(b != 0 for b in dev(d["y"]))  # fig2: 平均線上の点なし
    ok.append("L04 例題1: mx=25 my=40 sx=3 sy=4 共分散=10 r=5/6")
    # L04 例題2
    d = L04_ex2_sprint_longjump()
    r = _report_xy("L04 例題2", d["x"], d["y"])
    assert mean_of(d["x"]) == 13 and mean_of(d["y"]) == 500
    assert var_of(d["x"]) == F(1, 25) and var_of(d["y"]) == 400 and cov_of(d["x"], d["y"]) == F(-16, 5)
    assert abs(r + 0.8) < 1e-12
    ok.append("L04 例題2: sx=0.2 sy=20 共分散=−3.2 r=−0.8")
    # L04 問2（例題1の平均値に対する追加点の偏差の積）
    for (x, y), expect in (((23, 43), -6), ((28, 44), 12)):
        assert (x - 25) * (y - 40) == expect
    ok.append("L04 問2: (23,43)→−6（左上）/(28,44)→12（右上）")
    # L04 問3
    d = L04_q3_ads_sales()
    r = _report_xy("L04 問3", d["x"], d["y"])
    assert var_of(d["x"]) == 4 and var_of(d["y"]) == 400 and cov_of(d["x"], d["y"]) == 32
    assert abs(r - 0.8) < 1e-12
    ok.append("L04 問3: sx=2 sy=20 共分散=32 r=0.8")
    # L04 問4
    d = L04_q4_shoes_score()
    r = _report_xy("L04 問4", d["x"], d["y"])
    assert cov_of(d["x"], d["y"]) == 0 and r == 0
    ok.append("L04 問4: 共分散=0 r=0")
    # L04 S1
    d = L04_s1_lines()
    r1 = _report_xy("L04 S1(1)", d["x"], d["y_up"])
    r2 = _report_xy("L04 S1(2)", d["x"], d["y_down"])
    assert var_of(d["x"]) == 2 and var_of(d["y_up"]) == 8 and cov_of(d["x"], d["y_up"]) == 4
    assert abs(r1 - 1) < 1e-12 and abs(r2 + 1) < 1e-12
    ok.append("L04 S1: 共分散=±4 sx=√2 sy=2√2 r=1 / −1")
    # L05 朝食
    d = L05_breakfast_score()
    r = _report_xy("L05 §1 朝食", d["x"], d["y"])
    assert mean_of(d["x"]) == 13 and mean_of(d["y"]) == 13 and abs(r - 0.947) < 0.001
    ok.append("L05 §1: r=%.3f（本文 0.95）" % r)
    # L05 例題1
    d = L05_ex1_ushape()
    r = _report_xy("L05 例題1 U字", d["x"], d["y"])
    assert cov_of(d["x"], d["y"]) == 0 and r == 0 and var_of(d["x"]) == 100 and var_of(d["y"]) == 12
    ok.append("L05 例題1: 共分散=0 r=0 sx=10 sy=√12")
    # L05 例題2
    d = L05_ex2_basketball()
    r8 = _report_xy("L05 例題2 8人", d["x"], d["y"])
    r7 = _report_xy("L05 例題2 7人", d["x"][:7], d["y"][:7])
    assert var_of(d["x"]) == F(21, 2) and var_of(d["y"]) == F(17, 2) and cov_of(d["x"], d["y"]) == F(27, 4)
    assert abs(r8 - 0.7145) < 0.001
    assert var_of(d["x"][:7]) == 4 and var_of(d["y"][:7]) == F(12, 7) and cov_of(d["x"][:7], d["y"][:7]) == F(-2, 7)
    assert abs(r7 + 0.1091) < 0.001
    assert d["x"][7] > max(d["x"][:7]) and d["y"][7] > max(d["y"][:7])  # fig1: 右上に離れた1点
    qy = quartiles(d["y"])  # 本文 §3: y=12 は L01 の基準で外れ値（上の線 9.25）・x=13 は外れ値でない（上の線 13.5）
    assert qy["q1"] == 3 and qy["q3"] == F(11, 2) and outliers(d["y"])[0] == [12] and outliers(d["y"])[2] == F(37, 4)
    assert outliers(d["x"])[0] == [] and outliers(d["x"])[2] == F(27, 2)
    ok.append("L05 例題2: 8人 r=%.2f / 7人 r=%.2f" % (r8, r7))
    # L05 S1
    d = L05_s1_basketball_alt()
    r = _report_xy("L05 S1 (13,0)", d["x"], d["y"])
    assert mean_of(d["y"]) == F(7, 2) and cov_of(d["x"], d["y"]) == F(-15, 4) and var_of(d["y"]) == F(13, 4)
    assert abs(r + 0.6419) < 0.001
    assert outliers(d["x"])[0] == [] and outliers(d["y"])[0] == []  # S1 の (13, 0) は L01 の基準では外れ値にならない
    ok.append("L05 S1: r=%.2f" % r)
    # L05 二次元表
    t = L05_table_workbook()

    def rate(pairs):
        p = sum(a for a, b in pairs)
        q = sum(b for a, b in pairs)
        return F(p, p + q), p, q
    used = rate([t[("1年", "使った")], t[("2年", "使った")]])
    notu = rate([t[("1年", "使わなかった")], t[("2年", "使わなかった")]])
    assert used == (F(7, 10), 28, 12) and notu == (F(29, 50), 29, 21)
    assert sum(a + b for a, b in t.values()) == 90
    assert F(4, 10) < F(20, 40) and F(24, 30) < F(9, 10) and used[0] > notu[0]
    ok.append("L05 §4: 全体 0.70 vs 0.58／1年 0.40 vs 0.50／2年 0.80 vs 0.90（逆転）")
    t = L05_q4_bicycle()
    bike = rate([t[("近い", "自転車")], t[("遠い", "自転車")]])
    walk = rate([t[("近い", "徒歩")], t[("遠い", "徒歩")]])
    assert bike == (F(3, 10), 9, 21) and walk == (F(7, 30), 7, 23)
    assert F(1, 10) < F(4, 24) and F(8, 20) < F(3, 6) and bike[0] > walk[0]
    ok.append("L05 問4: 全体 0.30 vs 0.23／近い 0.10 vs 0.17／遠い 0.40 vs 0.50（逆転）")
    # L06
    tr = L06_jumprope_trials()
    assert [t[0] for t in tr] == list(range(1, 21))
    one = [t[3] for t in tr if t[1] == "1列"]
    two = [t[3] for t in tr if t[1] == "2列"]
    assert len(one) == 10 and len(two) == 10
    q1_, q2_ = quartiles(one), quartiles(two)
    print("\n### L06 五数要約（中2方式）")
    print("1列:", sorted(one), {k: str(v) for k, v in q1_.items()})
    print("2列:", sorted(two), {k: str(v) for k, v in q2_.items()})
    assert (q1_["min"], q1_["q1"], q1_["med"], q1_["q3"], q1_["max"]) == (8, 11, 14, 17, 20)
    assert (q2_["min"], q2_["q1"], q2_["med"], q2_["q3"], q2_["max"]) == (14, 21, F(49, 2), 28, 33)
    o1, lo1, hi1 = outliers(one)
    o2, lo2, hi2 = outliers(two)
    print("外れ値判定 1列:", o1, "境界", lo1, hi1, "／2列:", o2, "境界", lo2, hi2)
    assert o1 == [] and o2 == [] and (lo1, hi1) == (2, 26) and (lo2, hi2) == (F(21, 2), F(77, 2))
    r = corr_of([t[0] for t in tr], [t[3] for t in tr])
    print(f"試技番号と回数の r={r:.4f}")
    assert abs(r - 0.8949) < 0.001

    def med(v):
        return quartiles(v)["med"]
    strat = {(h, f): sorted(t[3] for t in tr if t[2] == h and t[1] == f) for h in "AB" for f in ("1列", "2列")}
    for k, v in strat.items():
        print("層別", k, v, "中央値", med(v))
    assert med(strat[("A", "1列")]) == 13 and med(strat[("A", "2列")]) == 22
    assert med(strat[("B", "1列")]) == 17 and med(strat[("B", "2列")]) == 28
    byA = sorted(t[3] for t in tr if t[2] == "A")
    byB = sorted(t[3] for t in tr if t[2] == "B")
    print("回し手A", byA, "中央値", med(byA), "／回し手B", byB, "中央値", med(byB))
    assert med(byA) == F(31, 2) and med(byB) == F(39, 2)
    two_ids = [t[0] for t in tr if t[1] == "2列"]
    assert two_ids == [6, 8, 10, 12, 14, 15, 17, 18, 19, 20]
    ok.append("L06: 五数要約 1列 8/11/14/17/20・2列 14/21/24.5/28/33・外れ値なし・r=%.2f・層別中央値 A 13/22・B 17/28・回し手別 15.5/19.5" % r)
    print("\n== L04〜L06 照合結果（全件 assert 通過） ==")
    for line in ok:
        print("-", line)
    return True


# ===========================================================================
# L07〜L09（2026-09-02 追記）
# - コイン投げは上の coin_counts()（シード 20260902）を n_toss だけ変えて使う（二重定義しない）。
# - L09 の例題・問題のデータは手設計の固定リテラル（乱数なし）。
# - verify_l07_l09() が本文（lesson_07〜09・answer_key）に書いた集計値を assert で照合する。
# ===========================================================================
def L08_coin10(seed=COIN_SEED):
    """L08 §4: コインを10回投げる試行を200回（Cさん・○×クイズ10問）。"""
    return coin_counts(seed, 200, 10)


def L08_coin100(seed=COIN_SEED):
    """L08 §4: コインを100回投げる試行を200回（Dさん・○×クイズ100問）。"""
    return coin_counts(seed, 200, 100)


def coin_freq(results, n_toss):
    """表の枚数ごとの回数（0〜n_toss 枚の全欄。度数分布表の再集計）。"""
    return [results.count(k) for k in range(n_toss + 1)]


def coin_class_table(results):
    """L08 §4 の100回投げ用・幅5の階級表（35〜39・40〜44・…・60〜64・65以上。「以上〜以下」）。
    戻り値=[(ラベル, 回数), ...]"""
    rows = []
    for lo in range(35, 65, 5):
        rows.append((f"{lo}〜{lo + 4}", sum(1 for v in results if lo <= v <= lo + 4)))
    rows.append(("65以上", sum(1 for v in results if v >= 65)))
    return rows


def L09_ex1_study_hours():
    """L09 例題1: 10人の1週間の自習時間（時間・小さい順）。設計: m=20・s=3・Q1=18・Q3=22・外れ値なし。"""
    return [14, 18, 18, 19, 20, 20, 21, 22, 22, 26]


def L09_ex2_temp_hot_drinks():
    """L09 例題2: 5日間の最高気温 x（℃）と温かい飲み物の売上 y（本）。設計: r=−0.8。"""
    return {"x": [23, 24, 25, 26, 27], "y": [31, 32, 30, 28, 29]}


def L09_q1_library_visits():
    """L09 問1: 6人の図書室利用回数（回・小さい順）。設計: m=15・s=2・＋2 で m=17・s=2。"""
    return [12, 13, 15, 16, 16, 18]


def L09_q2_reading_score():
    """L09 問2: 5人の読書時間 x（時間）と国語の小テスト y（点）。設計: r=0.6。"""
    return {"x": [3, 4, 5, 6, 7], "y": [8, 11, 10, 9, 12]}


def L09_q3_five_numbers():
    """L09 問3: 五数要約のみ（生データは持たない）。(最小値, Q1, 中央値, Q3, 最大値)。"""
    return {"従来の練習法": (-2, 0, 2, 4, 7), "新しい練習法": (-1, 2, 4, 6, 9)}


def _count_ge(results, k):
    return sum(1 for v in results if v >= k)


def _count_le(results, k):
    return sum(1 for v in results if v <= k)


def verify_l07_l09():
    """L07〜L09 の本文に書いた集計値を全件 assert で照合（1件でも食い違えば例外で停止）。"""
    ok = []
    # ---- 30回投げ×200回（L07 §3〜§4・L08 §1〜§3・L09 §4） ----
    c30 = coin_counts()
    f30 = coin_freq(c30, 30)
    assert len(c30) == 200 and sum(f30) == 200
    assert {k: v for k, v in enumerate(f30) if v} == {6: 1, 7: 1, 8: 2, 9: 1, 10: 11, 11: 7, 12: 18, 13: 27,
                                                        14: 22, 15: 34, 16: 25, 17: 18, 18: 16, 19: 9, 20: 5,
                                                        21: 1, 22: 1, 23: 1}, f30
    for k, expect in ((24, 0), (23, 1), (22, 2), (21, 3), (20, 8), (19, 17), (18, 33), (16, 76)):
        assert _count_ge(c30, k) == expect, (k, _count_ge(c30, k), expect)
    assert c30.count(15) == 34 and _count_le(c30, 9) == 5 and _count_le(c30, 7) == 2
    assert _count_le(c30, 9) + _count_ge(c30, 21) == 8
    assert _count_ge(c30[:100], 20) == 6 and _count_ge(c30[100:], 20) == 2  # 解答編 L08 問2 の指導メモ: 20枚以上は前半100回で6回・後半100回で2回
    assert min(c30) == 6 and max(c30) == 23 and sum(c30) == 2941
    m30, v30 = mean(c30), pvariance(c30)
    assert m30 == F(2941, 200) and float(m30) == 14.705
    assert sum(x * x for x in c30) == 44847 and v30 == F(44847, 200) - m30 ** 2 and float(v30) == 7.997975
    s30 = float(v30) ** 0.5
    assert abs(s30 - 2.8281) < 0.001 and abs(float(m30) + 2 * s30 - 20.361) < 0.001 and abs(float(m30) - 2 * s30 - 9.049) < 0.001
    assert statistics.mean(c30) == 14.705 and abs(statistics.pvariance(c30) - 7.997975) < 1e-9
    ok.append("30回投げ: 24以上0・23以上1・22以上2・21以上3・20以上8・19以上17・18以上33・16以上76・ちょうど15は34・"
              "9以下5・7以下2・2sの外8・合計2941・m=14.705・2乗の合計44847・s²=7.997975・s≒2.828・m＋2s≒20.36・m−2s≒9.05")
    # ---- 10回投げ×200回（L08 §4・問3） ----
    c10 = L08_coin10()
    f10 = coin_freq(c10, 10)
    assert len(c10) == 200 and f10 == [0, 4, 11, 16, 35, 52, 45, 20, 13, 4, 0], f10
    assert _count_ge(c10, 8) == 17 and _count_ge(c10, 9) == 4 and _count_ge(c10, 7) == 37
    assert min(c10) == 1 and max(c10) == 9 and sum(c10) == 1024
    m10, v10 = mean(c10), pvariance(c10)
    assert float(m10) == 5.12 and float(v10) == 2.8256
    s10 = float(v10) ** 0.5
    assert abs(s10 - 1.6810) < 0.001 and abs(float(m10) + 2 * s10 - 8.482) < 0.001
    assert 8 < float(m10) + 2 * s10 < 9   # 8枚は帯の中・9枚は帯の外（L08 §4・問3）
    ok.append("10回投げ: 度数 [0,4,11,16,35,52,45,20,13,4,0]・8以上17・9以上4・m=5.12・s²=2.8256・s≒1.681・m＋2s≒8.48")
    # ---- 100回投げ×200回（L08 §4・問4） ----
    c100 = L08_coin100()
    f100 = coin_freq(c100, 100)
    assert len(c100) == 200 and sum(f100) == 200
    assert {k: v for k, v in enumerate(f100) if v} == {36: 1, 37: 1, 38: 3, 40: 4, 41: 3, 42: 6, 43: 5, 44: 8, 45: 10,
                                                          46: 14, 47: 10, 48: 17, 49: 20, 50: 15, 51: 13, 52: 20, 53: 8,
                                                          54: 14, 55: 8, 56: 6, 57: 5, 58: 2, 59: 3, 60: 2, 61: 1, 63: 1}
    cls = coin_class_table(c100)
    assert [n for _, n in cls] == [5, 26, 71, 70, 24, 4, 0] and sum(n for _, n in cls) == 200, cls
    assert _count_ge(c100, 80) == 0 and _count_ge(c100, 60) == 4
    assert min(c100) == 36 and max(c100) == 63 and sum(c100) == 9880
    m100, v100 = mean(c100), pvariance(c100)
    assert float(m100) == 49.4 and float(v100) == 24.24
    s100 = float(v100) ** 0.5
    assert abs(s100 - 4.9234) < 0.001 and abs(float(m100) + 2 * s100 - 59.246) < 0.001
    assert 59 < float(m100) + 2 * s100 < 60   # 60枚は帯の外（L08 問4）
    ok.append("100回投げ: 階級 [5,26,71,70,24,4,0]・80以上0・60以上4・最小36・最大63・m=49.4・s²=24.24・s≒4.923・m＋2s≒59.25")
    # ---- L09 例題1 ----
    d = L09_ex1_study_hours()
    fv = quartiles(d)
    outs, lo, hi = outliers(d)
    assert d == sorted(d) and len(d) == 10 and sum(d) == 200 and mean(d) == 20
    assert (fv["med"], fv["q1"], fv["q3"]) == (20, 18, 22) and fv["q3"] - fv["q1"] == 4
    assert (lo, hi) == (12, 28) and outs == []
    devs = [x - 20 for x in d]
    assert devs == [-6, -2, -2, -1, 0, 0, 1, 2, 2, 6] and sum(devs) == 0 and sum(x * x for x in devs) == 90
    assert pvariance(d) == 9 and F(sum(x * x for x in d), 10) - 20 ** 2 == 9 and sum(x * x for x in d) == 4090
    assert all(14 <= x <= 26 for x in d)   # 2s の帯（14〜26）に10人全員
    ok.append("L09 例題1: m=20・中央値20・Q1=18・Q3=22・四分位範囲4・外れ値なし（境界12/28）・s²=9・s=3・帯14〜26に全員・2乗の和4090")
    # ---- L09 例題2 ----
    d = L09_ex2_temp_hot_drinks()
    assert mean_of(d["x"]) == 25 and mean_of(d["y"]) == 30
    assert dev(d["x"]) == [-2, -1, 0, 1, 2] and dev(d["y"]) == [1, 2, 0, -2, -1]
    assert var_of(d["x"]) == 2 and var_of(d["y"]) == 2 and cov_of(d["x"], d["y"]) == F(-8, 5)
    assert abs(corr_of(d["x"], d["y"]) + 0.8) < 1e-12
    ok.append("L09 例題2: mx=25・my=30・分散2・2・共分散−1.6・r=−0.8")
    # ---- L09 問1 ----
    d = L09_q1_library_visits()
    assert d == sorted(d) and sum(d) == 90 and mean(d) == 15
    assert [x - 15 for x in d] == [-3, -2, 0, 1, 1, 3] and sum((x - 15) ** 2 for x in d) == 24 and pvariance(d) == 4
    assert F(sum(x * x for x in d), 6) - 15 ** 2 == 4 and sum(x * x for x in d) == 1374
    assert all(11 <= x <= 19 for x in d)
    d2 = [x + 2 for x in d]
    assert d2 == [14, 15, 17, 18, 18, 20] and mean(d2) == 17 and pvariance(d2) == 4
    ok.append("L09 問1: m=15・s²=4・s=2・帯11〜19に全員・＋2 で m=17・s=2・2乗の和1374")
    # ---- L09 問2 ----
    d = L09_q2_reading_score()
    assert mean_of(d["x"]) == 5 and mean_of(d["y"]) == 10
    assert dev(d["x"]) == [-2, -1, 0, 1, 2] and dev(d["y"]) == [-2, 1, 0, -1, 2]
    assert var_of(d["x"]) == 2 and var_of(d["y"]) == 2 and cov_of(d["x"], d["y"]) == F(6, 5)
    assert abs(corr_of(d["x"], d["y"]) - 0.6) < 1e-12
    ok.append("L09 問2: mx=5・my=10・共分散1.2・r=0.6")
    # ---- L09 問3 ----
    q = L09_q3_five_numbers()
    a, b = q["従来の練習法"], q["新しい練習法"]
    assert a[3] - a[1] == 4 and b[3] - b[1] == 4 and (a[2], b[2]) == (2, 4)
    ok.append("L09 問3: 四分位範囲 4・4・中央値 2・4")
    print("\n== L07〜L09 照合結果（全件 assert 通過） ==")
    for line in ok:
        print("-", line)
    return True


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------
def md_row_table(title, data, per_row=10):
    print(f"\n### {title}（{len(data)}個）")
    for i in range(0, len(data), per_row):
        chunk = data[i:i + per_row]
        print("| " + " | ".join(str(x) for x in chunk) + " |")
        if i == 0:
            print("|" + "---|" * len(chunk))


def md_stats(label, data, expect=None):
    m, v = mean(data), pvariance(data)
    s = v ** 0.5 if v.denominator == 1 and int(v) ** 0.5 == int(int(v) ** 0.5) else None
    fv = quartiles(data)
    outs, lo, hi = outliers(data)
    s_txt = fnum(int(v) ** 0.5) if s is not None and int(int(v) ** 0.5) ** 2 == int(v) else f"√{fnum(v)}≒{float(v) ** 0.5:.3f}"
    print(f"- {label}: n={len(data)}・合計={sum(data)}・m={fnum(m)}・中央値={fnum(fv['med'])}"
          f"・範囲={fnum(fv['max'] - fv['min'])}・Q1={fnum(fv['q1'])}・Q3={fnum(fv['q3'])}"
          f"・四分位範囲={fnum(fv['q3'] - fv['q1'])}・外れ値={outs or 'なし'}（境界 {fnum(lo)} 未満／{fnum(hi)} 超）"
          f"・s²={fnum(v)}・s={s_txt}")
    # statistics モジュールでの再計算（別経路の検算）
    assert statistics.mean(data) == float(m), label
    assert abs(statistics.pvariance(data) - float(v)) < 1e-9, label
    assert statistics.median(data) == float(fv["med"]), label
    if expect:
        for k, val in expect.items():
            got = {"m": m, "var": v, "q1": fv["q1"], "q3": fv["q3"], "med": fv["med"],
                   "outs": outs}[k]
            assert got == val, f"{label}: {k} 期待={val} 実測={got}"


def deviation_table(label, data):
    m = mean(data)
    print(f"\n### {label}——偏差の表（m={fnum(m)}）")
    print("| 値 | 偏差（値−m） | 偏差の2乗 |")
    print("|---|---|---|")
    tot = 0
    for x in data:
        d = F(x) - m
        tot += d * d
        print(f"| {x} | {fnum(d)} | {fnum(d * d)} |")
    print(f"| 合計 | 0 | {fnum(tot)} |")


def freq_table_stats(label, values, freqs, expect_m, expect_var):
    n = sum(freqs)
    m = F(sum(v * f for v, f in zip(values, freqs)), n)
    var = F(sum(f * (F(v) - m) ** 2 for v, f in zip(values, freqs)), n)
    print(f"\n### {label}（度数分布表・n={n}）")
    print("| 階級値 | 度数 | 階級値×度数 | 偏差 | 偏差の2乗 | 偏差の2乗×度数 |")
    print("|---|---|---|---|---|---|")
    for v, f in zip(values, freqs):
        d = F(v) - m
        print(f"| {v} | {f} | {v * f} | {fnum(d)} | {fnum(d * d)} | {fnum(f * d * d)} |")
    print(f"| 合計 | {n} | {sum(v * f for v, f in zip(values, freqs))} | — | — | {fnum(var * n)} |")
    print(f"- m={fnum(m)}・s²={fnum(var)}・s={fnum(int(var) ** 0.5) if int(var) ** 0.5 == int(int(var) ** 0.5) else float(var) ** 0.5}")
    assert m == expect_m and var == expect_var, label
    # 展開して各階級値を度数分繰り返した生データでも一致（別経路）
    raw = [v for v, f in zip(values, freqs) for _ in range(f)]
    assert statistics.pvariance(raw) == float(var), label


def main():
    print("# generate_datasets.py 出力（本文の表と一致すること）")

    # ---- L01 ----
    print("\n## L01")
    d = l01_library_visits()
    md_row_table("A班（図書室利用回数・回）", d["A"], 11)
    md_stats("A班", d["A"], dict(m=8, med=8, q1=6, q3=9, outs=[18]))
    md_row_table("B班（図書室利用回数・回）", d["B"], 11)
    md_stats("B班", d["B"], dict(m=8, med=8, q1=5, q3=11, outs=[]))
    p = l01_practice()
    md_row_table("問1 小テスト（10点満点）", p["q1_quiz"])
    md_stats("問1", p["q1_quiz"], dict(m=F(29, 4), med=F(15, 2), outs=[]))
    md_row_table("問2(1)", p["q2_odd"])
    md_stats("問2(1)", p["q2_odd"], dict(med=9, q1=F(11, 2), q3=13))
    md_row_table("問2(2)", p["q2_even"])
    md_stats("問2(2)", p["q2_even"], dict(med=F(15, 2), q1=5, q3=10))
    md_row_table("問4", p["q4_outlier"], 12)
    md_stats("問4", p["q4_outlier"], dict(q1=F(19, 2), q3=F(29, 2), outs=[28]))
    md_stats("問4（28を除く）", [x for x in p["q4_outlier"] if x != 28], dict(q1=9, q3=14, outs=[]))

    e, f = [1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 4, 5, 5, 6, 6, 7, 8, 20]
    md_stats("S1 解答例 E", e, dict(q1=F(5, 2), q3=F(15, 2)))
    md_stats("S1 解答例 F", f, dict(q1=F(9, 2), q3=F(15, 2)))
    assert (quartiles(e)["q3"] - quartiles(e)["q1"]) > (quartiles(f)["q3"] - quartiles(f)["q1"]) and (max(e) - min(e)) < (max(f) - min(f))

    # ---- L02 ----
    print("\n## L02")
    d = l02_freethrow()
    md_row_table("Aさん（フリースロー成功数・20本中）", d["A"])
    md_stats("Aさん", d["A"], dict(m=14, var=4))
    deviation_table("Aさん", d["A"])
    md_row_table("Bさん（フリースロー成功数・20本中）", d["B"])
    md_stats("Bさん", d["B"], dict(m=14, var=16))
    deviation_table("Bさん", d["B"])
    c6 = l02_example2()
    md_row_table("Cさん（例題1・フリースロー成功数・20本中）", c6)
    md_stats("Cさん", c6, dict(m=14, var=10))
    sq_mean = F(sum(x * x for x in c6), len(c6))
    print(f"- 例題1の検算（値の2乗の平均−平均値の2乗）: {fnum(sq_mean)}−14²={fnum(sq_mean - 196)}")
    assert sq_mean - 196 == 10
    t = l02_test20()
    md_row_table("1組20人の小テスト（100点満点）", t)
    md_stats("1組", t, dict(m=60, var=100))
    deviation_table("1組", t)
    band = [x for x in t if 40 <= x <= 80]
    print(f"- m±2s の帯（40以上80以下）に入る人数={len(band)}／外={[x for x in t if not 40 <= x <= 80]}")
    assert len(band) == 19
    p = l02_practice()
    md_row_table("問1", p["q1"]); md_stats("問1", p["q1"], dict(m=5, var=4))
    md_row_table("問2", p["q2"]); md_stats("問2", p["q2"], dict(m=10, var=9))
    md_row_table("問3 X", p["q3_X"]); md_stats("問3 X", p["q3_X"], dict(m=8, var=4))
    md_row_table("問3 Y", p["q3_Y"]); md_stats("問3 Y", p["q3_Y"], dict(m=8, var=16))
    md_row_table("問4", p["q4"]); md_stats("問4", p["q4"], dict(m=20, var=25))
    for lab in ("q1", "q2", "q4"):
        d_ = p[lab]
        alt = F(sum(x * x for x in d_), len(d_)) - mean(d_) ** 2
        print(f"- {lab} 別経路（値の2乗の平均−平均値の2乗）={fnum(alt)}")
        assert alt == pvariance(d_)
    assert [x for x in p["q4"] if not 10 <= x <= 30] == [31]
    md_row_table("S1", p["s1"]); md_stats("S1", p["s1"], dict(m=4, med=3))
    for pval in (3, 4, 5):
        print(f"- S1: p={pval} のとき (値−p)² の和={sum((x - pval) ** 2 for x in p['s1'])}"
              f"・|値−p| の和={sum(abs(x - pval) for x in p['s1'])}")

    # ---- L03 ----
    print("\n## L03")
    t2 = l03_test20_class2()
    md_row_table("2組20人の小テスト（100点満点）", t2)
    md_stats("2組", t2, dict(m=60, var=400))
    deviation_table("2組", t2)
    def freq_counts(data, cmin, cwidth, nclass):
        counts = [0] * nclass
        for x in data:
            counts[(x - cmin) // cwidth] += 1
        return counts
    ca, cb = freq_counts(t, 0, 10, 10), freq_counts(t2, 0, 10, 10)
    print(f"- ヒストグラム度数（幅10・0〜100）: 1組={ca}／2組={cb}")
    assert ca == [0, 0, 0, 0, 3, 7, 7, 2, 1, 0] and cb == [0, 0, 1, 2, 3, 4, 3, 3, 2, 2]
    ct = l03_commute_table()
    freq_table_stats("16人の通学時間（分）", ct["values"], ct["freqs"], 25, 100)
    base = l03_transform_base()
    for label, conv in (("＋3", lambda x: x + 3), ("×5", lambda x: 5 * x)):
        conv_data = [conv(x) for x in base]
        md_row_table(f"Aさんの記録 {label}", conv_data)
        md_stats(f"Aさん {label}", conv_data)
    md_stats("Aさん ＋3", [x + 3 for x in base], dict(m=17, var=4))
    md_stats("Aさん ×5", [5 * x for x in base], dict(m=70, var=100))
    ex = [4, 6, 8]
    print(f"- L03 例題1の検算例: {ex} m={fnum(mean(ex))} s²={fnum(pvariance(ex))}／×5 → {[5 * x for x in ex]} m={fnum(mean([5 * x for x in ex]))} s²={fnum(pvariance([5 * x for x in ex]))}")
    assert pvariance([5 * x for x in ex]) == 25 * pvariance(ex)
    h = l03_heights()
    md_row_table("5人の身長（cm）", h)
    md_stats("身長", h, dict(m=168, var=4))
    u = [x - 170 for x in h]
    print(f"- 仮平均170との差 u={u}・u の平均={fnum(mean(u))}・m=170＋({fnum(mean(u))})={fnum(170 + mean(u))}・u の分散={fnum(pvariance(u))}")
    assert mean(u) == -2 and pvariance(u) == 4
    p = l03_practice()
    md_row_table("問1 X", p["q1_X"]); md_stats("問1 X", p["q1_X"], dict(m=8, var=4))
    md_row_table("問1 Y", p["q1_Y"]); md_stats("問1 Y", p["q1_Y"], dict(m=8, var=16))
    freq_table_stats("問2", p["q2_table"]["values"], p["q2_table"]["freqs"], 35, 100)
    md_row_table("問3", p["q3"]); md_stats("問3", p["q3"], dict(m=6, var=4))
    md_stats("問3 ＋4", [x + 4 for x in p["q3"]], dict(m=10, var=4))
    md_stats("問3 ×3", [3 * x for x in p["q3"]], dict(m=18, var=36))
    md_row_table("問4 身長（cm）", p["q4"]); md_stats("問4", p["q4"], dict(m=156, var=4))
    u4 = [x - 155 for x in p["q4"]]
    print(f"- 問4: 仮平均155との差 u={u4}・u の平均={fnum(mean(u4))}・u の分散={fnum(pvariance(u4))}")
    assert mean(u4) == 1 and pvariance(u4) == 4
    md_row_table("S1 気温（℃）", p["s1"]); md_stats("S1", p["s1"], dict(m=20, var=4))
    fah = [F(9, 5) * x + 32 for x in p["s1"]]
    print(f"- S1: 華氏 y=1.8x＋32 → {[fnum(y) for y in fah]}・m={fnum(mean(fah))}・s²={fnum(pvariance(fah))}・s={float(pvariance(fah)) ** 0.5:g}")
    assert mean(fah) == 68 and pvariance(fah) == F(324, 25)

    # ---- L07〜L08 用 コイン実験 ----
    print("\n## コイン30回投げ×200回（coin_counts(seed=20260902)）")
    c = coin_counts()
    md_row_table("表の枚数（実験1〜200回目の順）", c, 20)
    dist = {k: c.count(k) for k in sorted(set(c))}
    print("\n| 表の枚数 | " + " | ".join(str(k) for k in dist) + " | 計 |")
    print("|---|" + "---|" * len(dist) + "---|")
    print("| 回数 | " + " | ".join(str(v) for v in dist.values()) + f" | {len(c)} |")
    m_c, v_c = mean(c), pvariance(c)
    print(f"- 平均値 m={float(m_c):.3f}・分散≒{float(v_c):.3f}・標準偏差 s≒{float(v_c) ** 0.5:.3f}・最小={min(c)}・最大={max(c)}")
    print(f"- 24枚以上の回数={sum(1 for x in c if x >= 24)}（相対度数 {sum(1 for x in c if x >= 24) / len(c):.3f}）")
    print(f"- 18枚以上の回数={sum(1 for x in c if x >= 18)}（相対度数 {sum(1 for x in c if x >= 18) / len(c):.3f}）")
    print(f"- 理論値（参考・本文には書かない）: 1回の表の枚数の平均 15・標準偏差 √7.5≒2.739")
    assert len(c) == 200 and sum(dist.values()) == 200
    # 同じシードで2回呼んで同じ列（再現性）
    assert coin_counts() == c

    # ---- L04〜L06（2026-09-02 追記） ----
    print("\n## L04〜L06（偏差と積の表）")
    verify_l04_l06()

    # ---- L07〜L09（2026-09-02 追記） ----
    print("\n## L07〜L09")
    for label, res, n_toss in (("コイン10回投げ×200回（L08_coin10()・L08 §4）", L08_coin10(), 10),
                               ("コイン100回投げ×200回（L08_coin100()・L08 §4）", L08_coin100(), 100)):
        md_row_table(f"{label}: 表の枚数（実験1〜200回目の順）", res, 20)
        fr = coin_freq(res, n_toss)
        keys = list(range(n_toss + 1)) if n_toss == 10 else [k for k, v in enumerate(fr) if v]
        print("\n| 表の枚数 | " + " | ".join(str(k) for k in keys) + " | 計 |")
        print("|---|" + "---|" * len(keys) + "---|")
        print("| 回数 | " + " | ".join(str(fr[k]) for k in keys) + f" | {len(res)} |")
        if n_toss == 100:
            cls = coin_class_table(res)
            print("\n| 表の枚数 | " + " | ".join(lab for lab, _ in cls) + " | 計 |")
            print("|---|" + "---|" * len(cls) + "---|")
            print("| 回数 | " + " | ".join(str(n) for _, n in cls) + f" | {len(res)} |")
        m_, v_ = mean(res), pvariance(res)
        print(f"- 平均値 m={float(m_):g}・分散={float(v_):g}・標準偏差 s≒{float(v_) ** 0.5:.4f}・m＋2s≒{float(m_) + 2 * float(v_) ** 0.5:.3f}・最小={min(res)}・最大={max(res)}")
    md_row_table("L09 例題1 10人の自習時間（時間）", L09_ex1_study_hours())
    md_stats("L09 例題1", L09_ex1_study_hours(), dict(m=20, var=9, med=20, q1=18, q3=22, outs=[]))
    d = L09_ex2_temp_hot_drinks()
    _report_xy("L09 例題2（気温 x と温かい飲み物 y）", d["x"], d["y"])
    md_row_table("L09 問1 6人の利用回数（回）", L09_q1_library_visits())
    md_stats("L09 問1", L09_q1_library_visits(), dict(m=15, var=4))
    d = L09_q2_reading_score()
    _report_xy("L09 問2（読書時間 x と得点 y）", d["x"], d["y"])
    for name, fv5 in L09_q3_five_numbers().items():
        print(f"- L09 問3 {name}: 最小値={fnum(fv5[0])}・Q1={fnum(fv5[1])}・中央値={fnum(fv5[2])}・Q3={fnum(fv5[3])}・最大値={fnum(fv5[4])}")
    verify_l07_l09()
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
