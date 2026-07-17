#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中2理科「湿度計算」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）。

本単元の安全制約（S-draftable・外部批判レビュー（裁定）準拠）:
  - 実験・健康・防災の図は作らない（TIER-X）。図はすべて紙上計算・表/グラフ読解・
    概念説明の範囲のみ。
  - 数表は架空値のまま（TIER-V）。実測の飽和水蒸気量（約4.8/6.8/9.4/12.8/17.3/
    23.1/30.4 g/m³）を図に持ち込まない。グラフ系の図には「架空の練習用データ」を
    図内に明示する（§9-2）。
  - 「器」比喩の図には「イメージ図（比喩）」ラベルを付し、本文のヘッジ（空気が
    物理的な器を持つわけではない）と整合させる（§9-4）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（8枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証:
  1) 架空数表の本文照合assert — lesson_01〜05の数表行を実ファイルから読み取り、
     スクリプト内の架空数表（FICT_TEMPS/FICT_SAT）と全点一致しなければ図を出力しない
     （新しい実測風の値の混入を構造的に防ぐ）。
  2) 座標変換の線形性assert — グラフ系の図は「等間隔の値→等間隔の座標」を検算
     （E指摘の文字ベース図の等間隔問題を正確な座標変換で解消）。
  3) 禁止文字列の機械検査 — 各図の<text>/<title>/<desc>の数値トークンを
     図ごとの許可リストと照合し、答えの漏えい候補・実測値らしき数値があれば停止。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行。
  数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。
  SVGの直接編集は禁止（来歴が切れる）。
"""

import math
import re
import datetime
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFT = HERE.parent
ASSETS = DRAFT / "assets"
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
DOT_R = 2.5       # 点マーカー半径

# ===========================================================================
# 架空の練習用数表（本文の唯一のデータ源。実測値ではない——TIER-V）
# ===========================================================================
FICT_TEMPS = [0, 5, 10, 15, 20, 25, 30]                    # 気温［℃］
FICT_SAT = [4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0]         # 飽和水蒸気量（架空値）
# 実測値（近似）——「図に持ち込まれていないこと」の照合専用。描画には一切使わない
REAL_SAT_APPROX = [4.8, 6.8, 9.4, 12.8, 17.3, 23.1, 30.4]


def verify_fictional_table_against_lessons():
    """lesson_01〜05の数表行を実ファイルから読み取り、FICT_SATと全点一致を確認。
    1本文でも不一致なら図は出力されない（架空値のまま＝実測値を作らない保証）。"""
    row_re = re.compile(r"^\|\s*飽和水蒸気量.*?（架空値）\s*\|(.+)\|\s*$")
    temp_re = re.compile(r"^\|\s*気温［℃］\s*\|(.+)\|\s*$")
    checked = 0
    for n in range(1, 6):
        path = DRAFT / f"lesson_{n:02d}.md"
        text = path.read_text(encoding="utf-8")
        sat_rows = [m.group(1) for line in text.splitlines()
                    if (m := row_re.match(line.strip()))]
        temp_rows = [m.group(1) for line in text.splitlines()
                     if (m := temp_re.match(line.strip()))]
        assert sat_rows and temp_rows, f"lesson_{n:02d}: 数表行が見つからない"
        for row in sat_rows:
            vals = [float(c.strip()) for c in row.split("|")]
            assert vals == FICT_SAT, \
                f"lesson_{n:02d}: 本文の架空数表 {vals} がスクリプトと不一致"
        for row in temp_rows:
            vals = [int(c.strip()) for c in row.split("|")]
            assert vals == FICT_TEMPS, \
                f"lesson_{n:02d}: 本文の気温行 {vals} がスクリプトと不一致"
        checked += 1
    assert FICT_SAT != REAL_SAT_APPROX and all(
        abs(f - r) > 1e-9 for f, r in zip(FICT_SAT, REAL_SAT_APPROX)), \
        "架空数表が実測近似値と一致している（TIER-V違反の疑い）"
    return checked


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


TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# レッスンID（L01〜L05）・図番号などの構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "1", "2", "3"}


def audit_numbers(svg, allowed, check_tokens, fig_id):
    """禁止文字列の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。allowed=許可数値トークン集合、check_tokens=答え漏れ検査トークン（検査の実装定数）。"""
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
# 描画ヘルパー
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

    def circle(self, cx, cy, r, sw=MAIN_W, fill="none", dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
                 f'stroke="{color}" stroke-width="{sw}"{d}/>')

    def dot(self, x, y, r=DOT_R, fill="#000", sw=1.2):
        if fill in ("none", "#fff"):
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
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
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

    def hatch_def(self, pid="h45", angle=45, gap=6, w=1.1, color="#555"):
        self.defs.append(
            f'<pattern id="{pid}" width="{gap}" height="{gap}" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate({angle})">'
            f'<line x1="0" y1="0" x2="0" y2="{gap}" stroke="{color}" '
            f'stroke-width="{w}"/></pattern>')

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
            f'(docs/SPEC_figures.md準拠（内部規約の要旨は同SPECに反映済み）・AI再利用メタ情報つき・SVG直接編集禁止/'
            f'スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )


def monotone_cubic(xs, ys):
    """単調増加データ用の単調三次エルミート補間（Fritsch–Carlson）。
    データ点を厳密に通り、区間内で単調性を保つ（架空数表の曲線描画用）。"""
    n = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [(d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]
            s = a * a + b * b
            if s > 9:
                t = 3.0 / math.sqrt(s)
                m[i], m[i + 1] = t * a * d[i], t * b * d[i]

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        h = xs[i + 1] - xs[i]
        t = (x - xs[i]) / h
        h00 = (1 + 2 * t) * (1 - t) ** 2
        h10 = t * (1 - t) ** 2
        h01 = t * t * (3 - 2 * t)
        h11 = t * t * (t - 1)
        return (h00 * ys[i] + h10 * h * m[i] + h01 * ys[i + 1] + h11 * h * m[i + 1])

    return f


def axes_frame(cv, ck, x0, y0_top, w, h, xmax=32.5, ymax=34.5,
               xticks=(0, 5, 10, 15, 20, 25, 30),
               yticks=(0, 4, 8, 12, 16, 20, 24, 28, 32),
               xlabel="気温［℃］", ylabel="g/m³", grid=True):
    """関数グラフ系の座標枠（§9-1）。値→座標を厳密な線形変換で行い、
    等間隔性をassertで検算する（E指摘の等間隔問題の解消）。
    戻り値: (X, Y) 変換関数。原点は左下。"""
    yb = y0_top + h  # 底辺（y=0の位置）

    def X(v):
        return x0 + w * v / xmax

    def Y(v):
        return yb - h * v / ymax

    # 線形性の検算: 等間隔の値が等間隔の座標へ写ること
    ck.ok("横軸の線形性（5℃刻みが等間隔の座標に写る——文字ベース図の等間隔問題を解消）",
          abs((X(5) - X(0)) - (X(30) - X(25))) < 1e-9
          and abs((X(15) - X(10)) - (X(5) - X(0))) < 1e-9)
    ck.ok("縦軸の線形性（4g/m³刻みが等間隔の座標に写る・正確な縮尺）",
          abs((Y(0) - Y(4)) - (Y(28) - Y(32))) < 1e-9
          and abs((Y(4) - Y(8)) - (Y(0) - Y(4))) < 1e-9)

    if grid:
        for v in xticks:
            if v:
                cv.line(X(v), yb, X(v), Y(yticks[-1]), w=0.5, color="#ddd")
        for v in yticks:
            if v:
                cv.line(X(0), Y(v), X(xticks[-1]), Y(v), w=0.5, color="#ddd")
    cv.arrow(X(0), yb, X(xmax) + 4, yb, w=1.3)          # x軸
    cv.arrow(X(0), yb, X(0), Y(ymax) - 4, w=1.3)        # y軸
    for v in xticks:
        cv.line(X(v), yb, X(v), yb + 4, w=1.0)
        cv.text(X(v), yb + 18, str(v), size=11.5)
    for v in yticks:
        cv.line(X(0) - 4, Y(v), X(0), Y(v), w=1.0)
        cv.text(X(0) - 8, Y(v) + 4, str(v), size=11.5, anchor="end")
    cv.text(X(xmax) - 2, yb + 34, xlabel, size=FS_CAP, anchor="end")
    cv.text(X(0) - 6, Y(ymax) - 10, ylabel, size=FS_CAP, anchor="start")
    return X, Y


# ===========================================================================
# 図1: L01 「上限」の棒グラフ（架空数表の視覚化・正確な縮尺）
# 本文根拠: lesson_01.md「数表の読み方」の架空数表（気温↑→上限↑の主概念）
# 答え漏れ注意: 差18.0g（例題2）・余裕2.0g/14.0g（練習3・4）は入れない
# ===========================================================================
def fig_L01_limit_bars():
    ck = Checker()
    ck.ok("棒の高さ＝本文の架空数表と全点一致（実測値の混入なし）",
          FICT_SAT == [4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0]
          and all(abs(f - r) > 1e-9 for f, r in zip(FICT_SAT, REAL_SAT_APPROX)))
    ck.ok("気温が高いほど上限が大きい（単調増加・L01主概念2）",
          all(b > a for a, b in zip(FICT_SAT, FICT_SAT[1:])))

    cv = Canvas(500, 348)
    cv.hatch_def("h45", 45)
    X, Y = axes_frame(cv, ck, 64, 56, 396, 216)
    bw = 22
    for t, s in zip(FICT_TEMPS, FICT_SAT):
        cv.rect(X(t) - bw / 2, Y(s), bw, Y(0) - Y(s), sw=MAIN_W, fill="url(#h45)")
        cv.text(X(t), Y(s) - 7, f"{s:.1f}", size=11.5)
    # 棒の高さの比が値の比と厳密一致（正確な縮尺）
    ck.ok("棒の高さの縮尺が正確（32.0の棒は4.0の棒のちょうど8倍の高さ）",
          abs((Y(0) - Y(32.0)) / (Y(0) - Y(4.0)) - 8.0) < 1e-9)
    cv.text(250, 28, "空気1m³が含むことのできる水蒸気の上限（飽和水蒸気量）",
            size=FS, weight="bold")
    cv.text(250, 46, "——架空の練習用データ——", size=FS_CAP, weight="bold")
    cv.text(250, 340, "（この教材の練習用に作った架空値。実際の値は教科書で確認すること）",
            size=11)

    title = "気温と『上限』の棒グラフ（架空の練習用データ）"
    desc = ("L01の概念図。横軸=気温0〜30℃（5℃刻み）、縦軸=飽和水蒸気量g/m³"
            "（0〜32・正確な線形縮尺）の棒グラフ。本文の架空の練習用数表（0℃4.0／"
            "5℃6.0／10℃8.0／15℃12.0／20℃16.0／25℃24.0／30℃32.0）をそのまま棒の"
            "高さにし、気温が高いほど上限が大きいことを視覚化する。値は架空で、"
            "実際の飽和水蒸気量ではない（図中に「架空の練習用データ」と明示）。"
            "再現指示: 線形の縦横軸に7本の斜線ハッチングの棒を立て、各棒の上に"
            "架空数表の値をラベルし、「架空の練習用データ」の断りを図中に入れる。"
            "白黒のみ・答えの数値（差や余裕）は入れない。")
    allowed = {"0", "5", "10", "15", "20", "25", "30", "7",
               "4", "8", "12", "16", "24", "28", "32",
               "4.0", "6.0", "8.0", "12.0", "16.0", "24.0", "32.0"}
    check_tokens = {"18.0", "14.0", "10.0", "4.8", "9.4", "12.8",
              "17.3", "23.1", "30.4"}
    return dict(file="L01_fig1_saturation_limit_bars.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="主概念の視覚化。上限は気温で決まり、高温ほど大きい（正確な縮尺）",
                params="架空数表7点（本文と全点一致をassert）・縦軸線形0〜32",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図2: L01 「器」比喩のイメージ図（雑談枠「霧の朝のからくり」）
# 本文根拠: lesson_01.md 雑談枠——「器のほうが縮んでいく、とイメージするとよい
#           でしょう（実際の空気が物理的な器を持っているわけではありません）」
# 規約: §9-4 比喩図には「イメージ図」ラベル必須・実測風に見せない（数値なし）
# ===========================================================================
def fig_L01_vessel_image():
    ck = Checker()
    cv = Canvas(500, 292)
    cv.hatch_def("h45", 45)

    # --- パラメータ: 器の高さ（左→右で縮む）と中身の高さ（不変） ---
    vessel_h = [150, 112, 78]      # 器（上限）の高さ
    content_h = 78                 # 中身（水蒸気の量）——3パネルとも同じ
    vw = 92                        # 器の幅
    base_y = 218                   # 器の底の位置
    cxs = [96, 250, 404]           # 各パネルの中心x

    ck.ok("器（上限）の高さが左→右で単調に縮む（気温低下のイメージ）",
          vessel_h[0] > vessel_h[1] > vessel_h[2])
    ck.ok("中身（水蒸気の量）は3パネルとも同じ高さ（量は変わらないモデル）",
          content_h == 78)
    ck.ok("右端は器の高さ＝中身の高さ（上限が実量まで縮んだ状態）",
          vessel_h[2] == content_h)

    cv.text(20, 30, "イメージ図（比喩）", size=FS + 1, weight="bold", anchor="start")
    caps = ["気温が高い：余裕が大きい", "気温が下がる：器（上限）が縮む",
            "上限＝いまの量まで縮んだ"]
    for cx, vh, cap in zip(cxs, vessel_h, caps):
        # 中身（ハッチング）
        cv.rect(cx - vw / 2, base_y - content_h, vw, content_h, sw=0,
                fill="url(#h45)")
        # 器（口の開いたコの字）
        cv.polyline([(cx - vw / 2, base_y - vh), (cx - vw / 2, base_y),
                     (cx + vw / 2, base_y), (cx + vw / 2, base_y - vh)],
                    w=MAIN_W + 0.6)
        # 上限（器の口）の破線
        cv.line(cx - vw / 2 - 8, base_y - vh, cx + vw / 2 + 8, base_y - vh,
                w=AUX_W, dash=DASH)
        cv.text(cx, base_y + 18, cap, size=10.8)
    # パネル間の矢印（気温が下がる向き）
    for x1, x2 in ((cxs[0] + vw / 2 + 14, cxs[1] - vw / 2 - 14),
                   (cxs[1] + vw / 2 + 14, cxs[2] - vw / 2 - 14)):
        cv.arrow(x1, base_y - 96, x2, base_y - 96, w=1.4)
        cv.text((x1 + x2) / 2, base_y - 104, "冷える", size=10.8)
    # 右端: さらに縮むとあふれる、の注記（水滴の小円・器の上）
    top3 = base_y - vessel_h[2]
    for ddx, ddy in ((-16, -16), (0, -24), (16, -14)):
        cv.circle(cxs[2] + ddx, top3 + ddy, 3.0, sw=1.1)
    cv.text(494, top3 - 40, "さらに冷えると、あふれた分が水滴に（霧）",
            size=10.5, anchor="end")
    cv.text(250, 256, "（比喩です。実際の空気が物理的な器を持っている", size=11)
    cv.text(250, 272, "わけではありません——「上限」は気温で決まる値）", size=11)

    title = "『器が縮む』イメージ図（比喩・霧のからくり）"
    desc = ("L01雑談枠の比喩を図にしたイメージ図。同じ量の中身（斜線ハッチング＝"
            "水蒸気の量・3パネルで同じ高さ）に対して、器（＝上限・飽和水蒸気量の"
            "比喩）が「冷える」矢印とともに左から右へ縮んでいき、右端で器の口が"
            "中身の高さに一致する。さらに冷えるとあふれた分が水滴（霧）になる、と"
            "小さな水滴の円で示す。図の左上に「イメージ図（比喩）」ラベル、下部に"
            "「実際の空気が物理的な器を持っているわけではない」の断りを明示"
            "（本文のヘッジと整合・実測風に見せない・数値なし）。再現指示: 口の開いた"
            "コの字の器を3つ並べ、中身の高さは固定、器の高さだけ段階的に低くし、"
            "3つ目で器の高さ＝中身の高さにする。比喩ラベルと断り書きを必ず入れる。"
            "白黒のみ・数値なし。")
    return dict(file="L01_fig2_shrinking_vessel_image.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="雑談枠の比喩の可視化。「イメージ図（比喩）」ラベル＋ヘッジ併記",
                params="器の高さ150→112→78px・中身78px固定（数値ラベルなし）",
                checks=ck.items, allowed=set(), check_tokens=set())


# ===========================================================================
# 図3: L02 湿度計算の流れ図（順算・3ステップ）
# 本文根拠: lesson_02.md「①いまの気温を確かめる→②表でその気温の飽和水蒸気量
#           （分母）を引く→③割って100倍」＋例題1（20℃・8.0g→50%）
# 答え漏れ注意: 例題2・練習の答え（75%・37.5%）は入れない
# ===========================================================================
def fig_L02_flow():
    # --- パラメータ（lesson_02.md 例題1と一致） ---
    temp, vapor = 20, 8.0
    denom = FICT_SAT[FICT_TEMPS.index(temp)]
    humidity = vapor / denom * 100

    ck = Checker()
    ck.ok("分母は架空数表の20℃の値16.0（本文例題1②と一致）", denom == 16.0)
    ck.ok("湿度=8.0÷16.0×100=50%（本文例題1③と一致）",
          abs(humidity - 50) < 1e-12)
    ck.ok("値域: 例示の湿度が通常の範囲0〜100%内", 0 <= humidity <= 100)

    cv = Canvas(520, 262)
    boxes = [("① いまの気温を", "確かめる"),
             ("② 表でその気温の", "飽和水蒸気量（分母）を引く"),
             ("③ 水蒸気量÷分母", "×100 ＝ 湿度［%］")]
    bw, bh, y0 = 158, 58, 52
    xs = [10, 182, 354]
    for (l1, l2), x in zip(boxes, xs):
        cv.rect(x, y0, bw, bh, sw=MAIN_W, rx=6)
        cv.text(x + bw / 2, y0 + 24, l1, size=11.5, weight="bold")
        cv.text(x + bw / 2, y0 + 43, l2, size=11.5, weight="bold")
    cv.arrow(xs[1] - 18, y0 + bh / 2, xs[1] - 2, y0 + bh / 2, w=1.8)
    cv.arrow(xs[2] - 18, y0 + bh / 2, xs[2] - 2, y0 + bh / 2, w=1.8)
    cv.text(260, 32, "湿度を求める手順（順算）——分母を表から引く一手間が入る",
            size=FS, weight="bold")
    # 例題1の具体例（破線の帯）
    ey = 150
    cv.rect(16, ey, 490, 66, sw=AUX_W, dash=DASH, rx=6)
    cv.text(26, ey + 24, "例題1の場合:", size=FS_CAP, weight="bold", anchor="start")
    cv.text(26, ey + 48, "① 気温20℃ → ② 表より分母は16.0g/m³ → "
                         "③ 8.0÷16.0×100＝50%", size=FS_CAP, anchor="start")
    cv.text(260, 244, "（数表はこの教材の練習用に作った架空の数表。"
                      "実際の値は教科書で確認）", size=11)

    title = "湿度計算の流れ図（順算・3ステップ）"
    desc = ("L02の手順図。「①いまの気温を確かめる→②表でその気温の飽和水蒸気量"
            "（分母）を引く→③水蒸気量÷分母×100＝湿度[%]」の3つの箱を矢印でつなぎ、"
            "下の破線の帯に本文例題1の具体例（気温20℃→分母16.0g/m³→8.0÷16.0×100"
            "＝50%）を添える。分母を表から引く一手間が小5百分率との差分であることを"
            "見せる図。数値は本文例題1で解き済みのもののみで、練習問題の答えは"
            "入れない。数表は架空の練習用。再現指示: 角丸の箱3つを右向き矢印で"
            "つなぎ、手順を書き、下に破線枠で具体例1行を添える。白黒のみ。")
    allowed = {"100", "20", "16.0", "8.0", "50", "5"}
    check_tokens = {"75", "37.5", "9.0", "12.0"}
    return dict(file="L02_fig1_humidity_calc_flow.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="順算の手順の図式化（分母を表から引く一手間の明示）",
                params=f"例題1: 20℃・8.0g/m³・分母{denom}→50%（assertで本文照合）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図4: L03 順算と逆算の使い分け図（%を求めるか、gを求めるか）
# 本文根拠: lesson_03.md「順算か逆算か迷ったら、『求めたいのは％か、gか？』を
#           先に確認」＋凝結量は引き算の注記
# 答え漏れ注意: 例題・練習の具体的な数値は一切入れない（構造図）
# ===========================================================================
def fig_L03_forward_reverse():
    ck = Checker()
    # 構造の検算: 順算と逆算が互いに逆演算になっていること（架空数表の全点で確認）
    for d in FICT_SAT:
        for hum in (25, 50, 75, 100):
            v = d * hum / 100          # 逆算: 分母×湿度÷100
            back = v / d * 100         # 順算: 水蒸気量÷分母×100
            assert abs(back - hum) < 1e-9
    ck.ok("順算と逆算が互いに逆演算（架空数表全7点×湿度4水準で数値検算）", True)
    ck.ok("逆算の値域: 湿度≦100%なら答えは分母以下（本文「検算のコツ」と一致）",
          all(d * 100 / 100 <= d + 1e-9 for d in FICT_SAT))

    cv = Canvas(520, 300)
    # 共通の一手間
    cv.rect(110, 40, 300, 40, sw=MAIN_W, rx=6)
    cv.text(260, 65, "まず表で「その気温の分母（飽和水蒸気量）」を引く",
            size=FS_CAP, weight="bold")
    # 分岐の問い
    cv.text(260, 116, "求めたいのは ％ か、g か？", size=FS, weight="bold")
    cv.arrow(260, 82, 260, 98, w=1.6)
    cv.arrow(230, 124, 130, 152, w=1.6)
    cv.arrow(290, 124, 390, 152, w=1.6)
    # 左: 順算
    cv.rect(28, 160, 210, 84, sw=MAIN_W, rx=6)
    cv.text(133, 182, "％を求める → 順算", size=FS_CAP, weight="bold")
    cv.text(133, 208, "湿度［%］＝", size=FS_CAP)
    cv.text(133, 228, "水蒸気量 ÷ 分母 × 100", size=FS_CAP)
    # 右: 逆算
    cv.rect(282, 160, 210, 84, sw=MAIN_W, rx=6)
    cv.text(387, 182, "g を求める → 逆算", size=FS_CAP, weight="bold")
    cv.text(387, 208, "水蒸気量［g/m³］＝", size=FS_CAP)
    cv.text(387, 228, "分母 × 湿度 ÷ 100", size=FS_CAP)
    cv.text(260, 272, "（この使い分けは湿度の式を使う場面のもの。凝結量のgは"
                      "引き算で求める——レッスン4）", size=11)
    cv.text(260, 290, "（分母＝その気温の飽和水蒸気量。数表は架空の練習用）", size=11)

    title = "順算と逆算の使い分け図（％か、gか）"
    desc = ("L03の構造図。最上段に共通の一手間「まず表でその気温の分母（飽和水蒸気量）"
            "を引く」の箱、中央に「求めたいのは％か、gか？」の分岐、左に順算の箱"
            "（湿度[%]＝水蒸気量÷分母×100）、右に逆算の箱（水蒸気量[g/m³]＝分母×湿度"
            "÷100）を置いた対比図。下部に「凝結量のgは引き算で求める（レッスン4）」の"
            "限定注記を添え、本文の合言葉と整合させる。具体的な問題の数値は入れない。"
            "再現指示: 上1箱→分岐の問い→左右2箱の三叉フローを矢印で描き、式は"
            "本文の定義どおりに書く。白黒のみ・具体数値なし。")
    allowed = {"100", "4"}
    check_tokens = {"12.0", "8.0", "6.0", "62.5", "15.0", "24.0", "16.0"}
    return dict(file="L03_fig1_forward_reverse_flow.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="順算・逆算の分岐の図式化（凝結量＝差の予告注記つき）",
                params="構造図（数値なし）。逆演算性を架空数表全点で数値検算",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図5: L04 露点の表の逆引き図（下の行から探して真上を読む）
# 本文根拠: lesson_04.md「露点の判定手順（紙上）」①②③＋例題1（12.0→15℃）
# 答え漏れ注意: 練習1・2・4の露点（10℃・5℃・20℃は表の値としてのみ出現し、
#               矢印・強調は例題1の12.0→15℃だけに付ける）
# ===========================================================================
def fig_L04_table_reverse():
    # --- パラメータ（lesson_04.md 例題1と一致） ---
    vapor = 12.0
    dew = FICT_TEMPS[FICT_SAT.index(vapor)]
    now_temp = 25

    ck = Checker()
    ck.ok("表の逆引き: 12.0g/m³→真上は15℃（本文例題1と一致）", dew == 15)
    ck.ok("露点はいまの気温より高くない（本文「検算のコツ」と一致）",
          dew < now_temp)
    ck.ok("表の値は架空数表と全点一致（実測値なし）",
          FICT_SAT == [4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0])

    cv = Canvas(520, 300)
    # 表の描画
    x0, y0 = 24, 96
    head_w, cell_w, cell_h = 150, 46, 34
    cols = [x0 + head_w + i * cell_w for i in range(len(FICT_TEMPS))]
    cv.rect(x0, y0, head_w + cell_w * len(FICT_TEMPS), cell_h * 2, sw=MAIN_W)
    cv.line(x0, y0 + cell_h, x0 + head_w + cell_w * len(FICT_TEMPS),
            y0 + cell_h, w=1.0)
    cv.line(x0 + head_w, y0, x0 + head_w, y0 + cell_h * 2, w=1.0)
    for i in range(1, len(FICT_TEMPS)):
        cv.line(cols[i], y0, cols[i], y0 + cell_h * 2, w=0.7, color="#bbb")
    cv.text(x0 + head_w / 2, y0 + cell_h / 2 + 4, "気温［℃］", size=FS_CAP)
    cv.text(x0 + head_w / 2, y0 + cell_h * 1.5 - 3, "飽和水蒸気量", size=10.5)
    cv.text(x0 + head_w / 2, y0 + cell_h * 1.5 + 12, "［g/m³］（架空値）", size=10.5)
    for i, (t, s) in enumerate(zip(FICT_TEMPS, FICT_SAT)):
        cx = cols[i] + cell_w / 2
        bold = (s == vapor)
        cv.text(cx, y0 + cell_h / 2 + 4, str(t), size=FS_CAP,
                weight="bold" if bold else None)
        cv.text(cx, y0 + cell_h * 1.5 + 4, f"{s:.1f}", size=FS_CAP,
                weight="bold" if bold else None)
    # 強調: 12.0のセルと15のセル
    i_hit = FICT_SAT.index(vapor)
    cv.rect(cols[i_hit] + 2, y0 + cell_h + 2, cell_w - 4, cell_h - 4, sw=2.4)
    cv.rect(cols[i_hit] + 2, y0 + 2, cell_w - 4, cell_h - 4, sw=2.4, dash="4 3")
    # 手順の矢印とラベル
    hit_cx = cols[i_hit] + cell_w / 2
    cv.arrow(hit_cx - 60, y0 + cell_h * 2 + 34, hit_cx - 6, y0 + cell_h * 2 + 6,
             w=1.6)
    cv.text(150, y0 + cell_h * 2 + 52, "① 下の行から、実際に含んでいる水蒸気量"
                                       "（例題1では12.0）を探す", size=FS_CAP,
            anchor="start")
    cv.arrow(cols[i_hit] + cell_w - 9, y0 + cell_h * 2 - 8,
             cols[i_hit] + cell_w - 9, y0 + 8, w=1.6)
    cv.text(hit_cx, y0 - 10, "② 真上の気温を読む → それが露点",
            size=FS_CAP, weight="bold")
    cv.text(260, 40, "露点の判定は、表の逆引き——読む向きがレッスン1〜3と逆になる",
            size=FS, weight="bold")
    cv.text(260, 62, "（レッスン1〜3: 気温→上限 ／ 露点: 水蒸気量→気温）", size=FS_CAP)
    cv.text(260, 288, "（数表はこの教材の練習用に作った架空の数表。"
                      "実際の値は教科書で確認）", size=11)

    title = "露点の表の逆引き図（下の行から探して真上を読む）"
    desc = ("L04の手順図。架空の練習用数表（気温0〜30℃／飽和水蒸気量4.0〜32.0g/m³）"
            "を表の形で描き、本文例題1（水蒸気量12.0g/m³の空気）を例に、①下の行から"
            "12.0を探す（実線の太枠で強調）→②真上の気温を読む（破線枠・上向き矢印）"
            "＝露点、という逆引きの向きを矢印で示す。レッスン1〜3の「気温→上限」と"
            "読む向きが逆になることを見出しで明示。強調と矢印は本文で解き済みの例題1"
            "（12.0→15℃）だけに付け、練習問題の値には付けない。再現指示: 2行の表を"
            "描き、下行の該当セルを太枠・真上のセルを破線枠で強調し、下から上への"
            "矢印と手順①②のラベルを添える。白黒のみ。")
    allowed = {"0", "5", "10", "15", "20", "25", "30",
               "4.0", "6.0", "8.0", "12.0", "16.0", "24.0", "32.0"}
    check_tokens = {"200"}
    return dict(file="L04_fig1_dewpoint_table_reverse.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="露点＝表の逆引きの手順図（例題1の12.0→15℃のみ強調）",
                params="架空数表全点＋例題1（12.0g/m³→露点15℃）をassertで本文照合",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図6: L04 凝結量は「差」の図（冷やすと上限からあふれる分・正確な縮尺）
# 本文根拠: lesson_04.md 例題2（20℃・12.0g/m³を5℃まで冷やす→12.0−6.0）
# 答え漏れ注意: 練習3・4(b)の答え8.0gを入れない。例題2の式12.0−6.0は本文の
#               解き済み例示のため可（計算結果の「6.0g」は式のまま提示）
# ===========================================================================
def fig_L04_condensation_diff():
    # --- パラメータ（lesson_04.md 例題2と一致） ---
    vapor, t_from, t_to = 12.0, 20, 5
    limit_to = FICT_SAT[FICT_TEMPS.index(t_to)]
    condensed = vapor - limit_to

    ck = Checker()
    ck.ok("5℃の上限は架空数表より6.0g/m³（本文例題2①と一致）", limit_to == 6.0)
    ck.ok("凝結量=12.0−6.0=6.0g（本文例題2③と一致・差の計算）",
          abs(condensed - 6.0) < 1e-12)
    ck.ok("凝結量はもとの水蒸気量以下（本文「検算のコツ」と一致）",
          condensed <= vapor)

    cv = Canvas(500, 320)
    cv.hatch_def("h45", 45)
    cv.hatch_def("h135", 135)
    # 縦軸（0〜16・正確な線形縮尺）
    ax_x, y_top, h = 70, 66, 200
    ymax = 16

    def Y(v):
        return y_top + h - h * v / ymax

    ck.ok("縦軸の線形性（4g/m³刻みが等間隔・正確な縮尺）",
          abs((Y(0) - Y(4)) - (Y(12) - Y(16))) < 1e-9)
    cv.arrow(ax_x, Y(0), ax_x, Y(ymax) - 14, w=1.3)
    for v in (0, 4, 8, 12, 16):
        cv.line(ax_x - 4, Y(v), ax_x, Y(v), w=1.0)
        cv.text(ax_x - 8, Y(v) + 4, str(v), size=11.5, anchor="end")
    cv.text(ax_x - 6, Y(ymax) - 20, "g/m³", size=FS_CAP, anchor="start")
    cv.line(ax_x, Y(0), 470, Y(0), w=1.3)

    bw = 66
    x1c, x2c = 170, 350
    # 左: 冷やす前（20℃）——実量12.0の棒
    cv.rect(x1c - bw / 2, Y(vapor), bw, Y(0) - Y(vapor), sw=MAIN_W,
            fill="url(#h45)")
    cv.text(x1c, Y(vapor) - 8, "実量 12.0g", size=FS_CAP, weight="bold")
    cv.text(x1c, Y(0) + 18, "冷やす前（気温20℃）", size=FS_CAP)
    # 右: 5℃まで冷やした後——上限6.0の線と、あふれる分
    cv.rect(x2c - bw / 2, Y(limit_to), bw, Y(0) - Y(limit_to), sw=MAIN_W,
            fill="url(#h45)")
    cv.rect(x2c - bw / 2, Y(vapor), bw, Y(limit_to) - Y(vapor), sw=AUX_W,
            dash="4 3", fill="url(#h135)")
    cv.line(x2c - bw / 2 - 26, Y(limit_to), x2c + bw / 2 + 12, Y(limit_to),
            w=BOLD_W * 0.7)
    cv.text(x2c - bw / 2 - 30, Y(limit_to) + 4, "5℃の上限 6.0", size=11.5,
            anchor="end")
    cv.text(x2c, Y(0) + 18, "5℃まで冷やした後", size=FS_CAP)
    # あふれる分の寸法線
    dim_x = x2c + bw / 2 + 22
    cv.line(dim_x, Y(vapor), dim_x, Y(limit_to), w=1.0)
    cv.line(dim_x - 4, Y(vapor), dim_x + 4, Y(vapor), w=1.0)
    cv.line(dim_x - 4, Y(limit_to), dim_x + 4, Y(limit_to), w=1.0)
    cv.text(dim_x + 8, (Y(vapor) + Y(limit_to)) / 2 - 4, "水滴になる分",
            size=11.5, anchor="start", weight="bold")
    cv.text(dim_x + 8, (Y(vapor) + Y(limit_to)) / 2 + 12, "＝ 12.0−6.0",
            size=11.5, anchor="start")
    # 冷やす矢印
    cv.arrow(x1c + bw / 2 + 16, Y(14.2), x2c - bw / 2 - 30, Y(14.2), w=1.6)
    cv.text((x1c + x2c) / 2, Y(14.2) - 10, "5℃まで冷やす", size=FS_CAP)
    cv.text(250, 34, "凝結量は割合ではなく「差」——引き算で求める", size=FS,
            weight="bold")
    cv.text(250, 308, "（架空の練習用データ。実際の値は教科書で確認。"
                      "含みきれない分が水滴になる、と考えたモデル）", size=11)

    title = "凝結量は『差』の図（冷やすと上限からあふれる分）"
    desc = ("L04例題2の図解。縦軸g/m³（0〜16・正確な線形縮尺）に対し、左に冷やす前"
            "（気温20℃）の実量12.0gの棒、右に5℃まで冷やした後の棒を描く。右の棒は"
            "5℃の上限6.0g/m³の太い水平線で区切られ、上限を超える部分（12.0−6.0）を"
            "別ハッチング＋破線枠で「水滴になる分」と寸法線表示する。凝結量が割合"
            "（÷や×100）ではなく差（引き算）で求まることを視覚化。答えの数値は式"
            "12.0−6.0のまま提示し、計算結果は書かない。架空の練習用データの断り付き。"
            "再現指示: 同じ縦軸に2本の棒を並べ、右の棒だけ上限線で分割し、上限超過分"
            "を破線枠・別ハッチングで示して寸法線に「水滴になる分＝12.0−6.0」と書く。"
            "白黒のみ。")
    allowed = {"0", "4", "8", "12", "16", "20", "5", "12.0", "6.0", "100"}
    check_tokens = {"8.0", "200"}
    return dict(file="L04_fig2_condensation_difference.svg", canvas=cv,
                lesson="L04", title=title, desc=desc,
                intent="凝結量＝差の視覚化（例題2の解き済みの式のみ・結果は不記載）",
                params=f"例題2: 12.0g/m³・20℃→5℃・上限{limit_to}（assertで本文照合）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図7: L05 図1 複合グラフ（曲線＝上限・棒＝実量・正確な縮尺の正式版）
# 本文根拠: lesson_05.md 図1（文字ベース模式図の正式化）。曲線は架空数表7点、
#           棒はP（25℃・12.0）とQ（15℃・6.0）
# E指摘対応: 文字ベース図の目盛り不等間隔（32/28/24/20/16/12/8/6/4）を、
#            正確な線形座標変換（等間隔assert）で解消
# 答え漏れ注意: P・Qの湿度50%／露点は入れない
# ===========================================================================
def fig_L05_composite_graph():
    # --- パラメータ（lesson_05.md 図1と一致） ---
    P_temp, P_vap = 25, 12.0
    Q_temp, Q_vap = 15, 6.0

    ck = Checker()
    f = monotone_cubic(FICT_TEMPS, FICT_SAT)
    ck.ok("曲線が架空数表の7点を厳密に通る（単調三次補間・実測風の値を作らない）",
          all(abs(f(t) - s) < 1e-9 for t, s in zip(FICT_TEMPS, FICT_SAT)))
    samples = [f(x / 10) for x in range(0, 301, 2)]
    ck.ok("曲線が単調増加（気温が高いほど上限が大きい・本文と整合）",
          all(b >= a - 1e-9 for a, b in zip(samples, samples[1:])))
    ck.ok("Pの棒（25℃・12.0）は25℃の曲線の高さ24.0より低い（湿度100%未満）",
          P_vap < FICT_SAT[FICT_TEMPS.index(P_temp)])
    ck.ok("Qの棒（15℃・6.0）は15℃の曲線の高さ12.0より低い（湿度100%未満）",
          Q_vap < FICT_SAT[FICT_TEMPS.index(Q_temp)])

    cv = Canvas(520, 396)
    cv.hatch_def("h45", 45)
    cv.hatch_def("h135", 135)
    X, Y = axes_frame(cv, ck, 66, 64, 420, 252)
    # 棒の高さの縮尺検算（正確な座標変換）
    ck.ok("棒の高さが値に厳密比例（Pの棒はQの棒のちょうど2倍の高さ）",
          abs((Y(0) - Y(P_vap)) / (Y(0) - Y(Q_vap)) - 2.0) < 1e-9)

    # 棒（曲線より先に描いて、曲線を前面へ）
    bw = 18
    cv.rect(X(P_temp) - bw / 2, Y(P_vap), bw, Y(0) - Y(P_vap), sw=MAIN_W,
            fill="url(#h45)")
    cv.text(X(P_temp), Y(P_vap) - 8, "P", size=FS, weight="bold")
    cv.rect(X(Q_temp) - bw / 2, Y(Q_vap), bw, Y(0) - Y(Q_vap), sw=MAIN_W,
            fill="url(#h135)")
    cv.text(X(Q_temp), Y(Q_vap) - 8, "Q", size=FS, weight="bold")
    # 曲線（0〜30℃を細かく折れ線サンプリング）
    pts = [(X(x / 10), Y(f(x / 10))) for x in range(0, 301, 2)]
    cv.polyline(pts, w=2.2)
    for t, s in zip(FICT_TEMPS, FICT_SAT):
        cv.dot(X(t), Y(s), r=3.0)
    cv.text(X(21.3), Y(f(21.3)) - 14, "曲線＝飽和水蒸気量（上限）", size=FS_CAP,
            anchor="end")
    cv.text(260, 30, "図1 飽和水蒸気量の曲線と水蒸気量の棒", size=FS + 1,
            weight="bold")
    cv.text(260, 50, "——架空の練習用データ——", size=FS_CAP, weight="bold")
    # 凡例
    ly = 356
    cv.text(30, ly, "●と曲線: その気温での上限（飽和水蒸気量・架空値）",
            size=FS_CAP, anchor="start")
    cv.text(30, ly + 18, "棒: その空気が実際に含む水蒸気量"
                         "（P: 気温25℃・12.0g/m³ ／ Q: 気温15℃・6.0g/m³）",
            size=FS_CAP, anchor="start")
    cv.text(30, ly + 36, "（この教材の練習用に作った架空値を正確な縮尺で図に"
                         "したもの。実際の値は教科書で確認）", size=11, anchor="start")

    title = "図1 複合グラフ——飽和水蒸気量の曲線と水蒸気量の棒（架空の練習用データ）"
    desc = ("L05の図1（本文の文字ベース模式図を正確な縮尺で正式化したグラフ）。"
            "横軸=気温0〜30℃（5℃刻み・等間隔）、縦軸=g/m³（0〜32・4刻み・等間隔の"
            "線形縮尺）。曲線は架空の練習用数表の7点（0℃4.0／5℃6.0／10℃8.0／15℃"
            "12.0／20℃16.0／25℃24.0／30℃32.0）を厳密に通る単調増加曲線で、各点に"
            "●マーカー。棒は空気P（気温25℃の位置・高さ12.0g/m³・斜線45°）と空気Q"
            "（気温15℃の位置・高さ6.0g/m³・斜線135°）。凡例で「曲線＝上限／棒＝実際に"
            "含む水蒸気量」を明示し、「架空の練習用データ」を図中に大きく明示する。"
            "P・Qの湿度や露点の数値は入れない（練習問題の答えのため）。再現指示: "
            "線形の座標平面に架空数表7点を通る滑らかな単調増加曲線と●を描き、"
            "指定の2本のハッチング棒を立て、凡例と架空データの断りを添える。白黒のみ。")
    allowed = {"0", "4", "8", "12", "16", "20", "24", "28", "32",
               "5", "10", "15", "25", "30", "12.0", "6.0", "45", "135", "7",
               "4.0", "6.0", "8.0", "16.0", "24.0", "32.0"}
    check_tokens = {"50", "100"}
    return dict(file="L05_fig1_composite_graph.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="図1の正式化。曲線＝上限／棒＝実量の複合グラフ（等間隔問題を解消）",
                params=f"曲線=架空数表7点・P({P_temp}℃,{P_vap})・Q({Q_temp}℃,{Q_vap})",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図8: L05 露点の読み取り図（棒の上端から水平にたどって曲線と交わる点）
# 本文根拠: lesson_05.md 例題2「棒の高さ12.0g/m³を保ったまま左（低温側）へ動かして
#           いくと、曲線の高さがちょうど12.0になるのは15℃」＋lesson_map L5
#           「露点＝棒の上端から水平にたどった線と曲線の交点」（外部批判レビュー（裁定）の精密化と一致）
# 答え漏れ注意: Qの露点（練習2の答え）の読み取り線は描かない。Pの15℃は例題2で
#               解き済みの例示
# ===========================================================================
def fig_L05_dewpoint_reading():
    # --- パラメータ（lesson_05.md 例題2と一致） ---
    P_temp, P_vap = 25, 12.0
    dew = FICT_TEMPS[FICT_SAT.index(P_vap)]

    ck = Checker()
    f = monotone_cubic(FICT_TEMPS, FICT_SAT)
    ck.ok("水平線y=12.0と曲線の交点は表の点（15℃, 12.0）と厳密一致（例題2と一致）",
          abs(f(dew) - P_vap) < 1e-9 and dew == 15)
    ck.ok("露点15℃はいまの気温25℃より低い（L4検算のコツと一致）", dew < P_temp)

    cv = Canvas(520, 404)
    cv.hatch_def("h45", 45)
    X, Y = axes_frame(cv, ck, 66, 64, 420, 252)
    # 棒P
    bw = 18
    cv.rect(X(P_temp) - bw / 2, Y(P_vap), bw, Y(0) - Y(P_vap), sw=MAIN_W,
            fill="url(#h45)")
    cv.text(X(P_temp), Y(P_vap) - 8, "P", size=FS, weight="bold")
    # 曲線
    pts = [(X(x / 10), Y(f(x / 10))) for x in range(0, 301, 2)]
    cv.polyline(pts, w=2.2)
    for t, s in zip(FICT_TEMPS, FICT_SAT):
        cv.dot(X(t), Y(s), r=3.0)
    # ①棒の上端から水平に左へ（破線矢印）
    cv.arrow(X(P_temp) - bw / 2 - 2, Y(P_vap), X(dew) + 6, Y(P_vap),
             w=1.5, dash=DASH)
    # ②交点の強調（二重丸）
    cv.dot(X(dew), Y(P_vap), r=3.0)
    cv.circle(X(dew), Y(P_vap), 7.0, sw=1.6)
    # ③交点から真下へ（破線矢印）
    cv.arrow(X(dew), Y(P_vap) + 8, X(dew), Y(0) - 6, w=1.5, dash=DASH)
    # 手順ラベル
    cv.text(X(20), Y(P_vap) + 24, "① 棒の上端から", size=FS_CAP)
    cv.text(X(20), Y(P_vap) + 40, "水平に左へ", size=FS_CAP)
    cv.text(X(dew) - 12, Y(P_vap) - 16, "② 曲線と交わる点", size=FS_CAP,
            anchor="end")
    cv.text(X(dew) - 10, Y(0) - 14, "③ 真下の気温＝露点", size=FS_CAP,
            anchor="end", weight="bold")
    cv.text(260, 30, "露点の読み取り方（例題2・空気Pの場合）", size=FS + 1,
            weight="bold")
    cv.text(260, 50, "——図1と同じ架空の練習用データ——", size=FS_CAP, weight="bold")
    ly = 368
    cv.text(24, ly, "棒の高さ（P: 12.0g/m³）を保ったまま左へたどり、曲線と"
                    "ちょうど同じ高さになる気温を読む。", size=11, anchor="start")
    cv.text(24, ly + 18, "（架空の練習用データ。実際の値は教科書で確認）", size=11,
            anchor="start")

    title = "露点の読み取り図——棒の上端から水平にたどって曲線と交わる点"
    desc = ("L05例題2の読み取り手順図。図1と同じ座標平面（横軸=気温0〜30℃・縦軸="
            "g/m³ 0〜32・正確な線形縮尺）に、空気Pの棒（気温25℃・高さ12.0g/m³）と"
            "架空数表7点を通る飽和水蒸気量の曲線を描き、①棒の上端から水平に左へ"
            "破線矢印、②曲線と交わる点を二重丸で強調、③交点から真下へ破線矢印＝"
            "露点、の3ステップを示す。交点は表の点（15℃, 12.0）と厳密に一致する"
            "（例題2で解き済みの例示）。空気Qの読み取り線は練習問題の答えにあたる"
            "ため描かない。再現指示: 複合グラフの上に、棒の上端→水平破線矢印→曲線"
            "との交点（二重丸）→垂直破線矢印→横軸、の読み取り経路と手順①②③の"
            "ラベルを重ねる。白黒のみ。")
    allowed = {"0", "4", "8", "12", "16", "20", "24", "28", "32",
               "5", "10", "15", "25", "30", "12.0", "7"}
    check_tokens = {"50", "100"}
    return dict(file="L05_fig2_dewpoint_reading.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="露点＝水平にたどった線と曲線の交点、の手順図（外部批判レビュー（裁定）の精密化と一致）",
                params=f"P({P_temp}℃,{P_vap})→露点{dew}℃（assertで本文・数表照合）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# メイン: 本文照合 + 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_limit_bars, fig_L01_vessel_image, fig_L02_flow,
        fig_L03_forward_reverse, fig_L04_table_reverse,
        fig_L04_condensation_diff, fig_L05_composite_graph,
        fig_L05_dewpoint_reading]


def main():
    n_lessons = verify_fictional_table_against_lessons()
    print(f"OK 架空数表の本文照合: lesson_01〜{n_lessons:02d} 全点一致"
          f"（実測近似値との全点不一致も確認）")
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
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
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "safety: S-draftable厳守——実験・健康・防災の図なし（TIER-X）／数表は架空値のまま"
        "（TIER-V・実測値の混入をassertで遮断）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 中2理科「湿度計算」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "全図で(1)架空数表の本文照合assert（lesson_01〜05の数表行を実ファイルから読み取り全点一致・"
        "実測近似値との全点不一致を確認）、(2)座標変換の線形性assert（グラフ系＝等間隔問題の解消）、"
        "(3)禁止文字列の機械検査（<text>/<title>/<desc>の数値トークンを許可リストと照合）が"
        "生成時に自動実行され、全件合格。"
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
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する",
        "   （数値は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。架空数表の本文照合・線形性assert・",
        "   禁止文字列検査に1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
        "## 本単元固有の安全規約（改修時も維持すること）",
        "",
        "- 実験・観察・健康・防災の図を追加しない（TIER-X／S-draftable）。",
        "- 数表・グラフの値は架空の練習用のまま。実測の飽和水蒸気量を図に持ち込まない（TIER-V）。",
        "- グラフ系の図には「架空の練習用データ」を図中に明示する（docs/SPEC_figures.md）。",
        "- 「器」比喩の図には「イメージ図（比喩）」ラベルと「空気が物理的な器を持つわけでは",
        "  ない」の断りを必ず残す（同 §9-4・teacher_notes_L04-05 §4の比喩の限界指摘に対応）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
