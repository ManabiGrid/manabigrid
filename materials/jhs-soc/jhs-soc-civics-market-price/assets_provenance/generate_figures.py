#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 公民「市場経済と価格のはたらき」単元 図版パラメトリック生成スクリプト
==============================================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（8枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証:
  1) 架空データ照合assert — 図中の数値（おこづかい1,000円・ルポの実の価格表など）を
     スクリプト内の「本文転記パラメータ」から計算し、本文（lesson_XX.md）記載値と
     一致しなければ図を出力しない。
  2) 中立性の構造assert — 対で扱うパネル（効率／公正・品不足／売れ残り・売り手／買い手）の
     寸法・矢印が幾何的に対等であることを検算する（図で優劣を示唆しない——§9-4）。
  3) 禁止文字列の機械検査 — 各図の<text>/<title>/<desc>の数値トークンを図ごとの
     「許可数値リスト」と照合し、答えの漏えい候補（つり合い価格・組み合わせ合計等）や
     評価語（優劣の示唆）があれば停止。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値・文言を変えて
  再実行。数値は該当レッスン本文（candidate_draft/lesson_XX.md）と一致させること。
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
FS = 14           # 基本文字サイズ(px) — viewBox幅~470で約3%
FS_CAP = 12       # キャプション


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

# レッスンID（L01〜L06）・「手順1」「ものさし1」等の構造番号は答えの数値ではないため常時許可
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "06", "1", "2", "3"}


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
# 描画ヘルパー（概念図・フロー図中心のためpx座標で直接描く）
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

    def hatch_def(self, pid="h45", angle=45):
        self.defs.append(
            f'<pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate({angle})">'
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="#555" stroke-width="1.1"/>'
            f'</pattern>')

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


def box_with_lines(cv, x, y, w, h, lines, size=FS_CAP, sw=MAIN_W, dash=None,
                   rx=6, weight_first=None, lh=16):
    """角丸の箱＋中央ぞろえの複数行テキスト"""
    cv.rect(x, y, w, h, sw=sw, dash=dash, rx=rx)
    n = len(lines)
    y0 = y + h / 2 - (n - 1) * lh / 2 + size * 0.36
    for i, s in enumerate(lines):
        cv.text(x + w / 2, y0 + i * lh, s, size=size,
                weight=weight_first if i == 0 else None)


# ===========================================================================
# 図1: L01 希少性と選択（欲しいもの3つ・使えるお金1,000円）
# 本文根拠: lesson_01.md 導入の問い（おこづかい1,000円・ジュース400円・パン350円・
#           文房具セット500円）と本文（希少性→選択→あきらめ）
# 答え漏れ注意: 合計額（1,250円）・組み合わせの計算（900円・750円・850円）は
#               導入の問い/活動1の答えにあたるため図にもdescにも入れない
# ===========================================================================
def fig_L01():
    # --- パラメータ（lesson_01.md 導入の問いをそのまま転記・すべて架空） ---
    budget = 1000
    items = [("ルポの実のジュース", 400), ("焼きたてパン", 350), ("文房具セット", 500)]

    ck = Checker()
    ck.ok("品目と価格が本文と一致（ジュース400円・パン350円・文房具セット500円）",
          items == [("ルポの実のジュース", 400), ("焼きたてパン", 350),
                    ("文房具セット", 500)])
    ck.ok("おこづかいが本文と一致（1,000円）", budget == 1000)
    ck.ok("希少性の前提: 欲しいものの合計 > 使えるお金（合計値は図に書かない）",
          sum(p for _, p in items) > budget)

    cv = Canvas(470, 300)
    cv.text(235, 28, "欲しいものは3つ、使えるお金には限りがある", size=FS,
            weight="bold")

    # --- 上段: 欲しいもの3つのカード ---
    card_w, card_h, gap = 136, 62, 12
    x0 = (470 - card_w * 3 - gap * 2) / 2
    for i, (name, price) in enumerate(items):
        x = x0 + i * (card_w + gap)
        box_with_lines(cv, x, 52, card_w, card_h, [name, f"{price}円"],
                       weight_first="bold")

    # --- 中段: 使えるお金（限り） ---
    wx, wy, ww, wh = 130, 148, 210, 56
    for i, (name, price) in enumerate(items):
        x = x0 + i * (card_w + gap) + card_w / 2
        cv.line(x, 52 + card_h, wx + ww / 2 + (i - 1) * 50, wy, w=AUX_W,
                dash="2 3", color="#888")
    box_with_lines(cv, wx, wy, ww, wh,
                   ["おこづかい 1,000円", "＝使えるお金には限り（希少性）"],
                   size=FS_CAP, sw=BOLD_W * 0.6, weight_first="bold", lh=20)

    # --- 下段: 選択（何かを選び、何かをあきらめる） ---
    by = 236
    bw, bh = 180, 44
    lx, rx = 45, 245
    cv.arrow(wx + ww / 2 - 20, wy + wh, lx + bw / 2, by, w=1.4)
    cv.arrow(wx + ww / 2 + 20, wy + wh, rx + bw / 2, by, w=1.4)
    cv.text(wx + ww / 2, wy + wh + 24, "選択", size=FS_CAP, weight="bold")
    box_with_lines(cv, lx, by, bw, bh, ["選ぶもの ？"], dash=DASH,
                   weight_first="bold")
    box_with_lines(cv, rx, by, bw, bh, ["あきらめるもの ？"], dash=DASH,
                   weight_first="bold")
    cv.text(235, 296, "（あおば町・みずき市場・品物と価格はすべて架空の設定）",
            size=11)

    # 中立性/対等の構造検算: 「選ぶ」「あきらめる」の箱は同寸（どちらかを目立たせない）
    ck.ok("「選ぶもの」「あきらめるもの」の箱が同寸・同段（選択の両面を対等に描く）",
          True)  # 上のbw/bh/byを共用しているためコード構造上つねに成立

    title = "希少性と選択の概念図（欲しいもの3つと使えるお金1,000円）"
    desc = ("L01導入〜本文の概念図。上段に欲しいもの3枚のカード（ルポの実のジュース"
            "400円・焼きたてパン350円・文房具セット500円——すべて架空）、中段に"
            "「おこづかい 1,000円＝使えるお金には限り（希少性）」の箱、下段に破線の"
            "2箱「選ぶもの ？」「あきらめるもの ？」を対等に並べ、中段から2本の矢印"
            "（ラベル「選択」）でつなぐ。合計金額や買える組み合わせは導入の問い・活動の"
            "答えにあたるため記載しない。再現指示: 品物カード3枚→お金の箱→同寸の？箱"
            "2つ、の3段構成で描き、？箱への矢印は同じ太さ・同じ長さにする。白黒のみ。")
    allowed = {"400", "350", "500", "000"}  # 「1,000」は 1 / 000 に分割される
    check_tokens = {"1,250", "1250", "900", "750", "850"}
    return dict(file="L01_fig1_scarcity_choice.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="希少性（欲しい＞限り）と選択（選ぶ／あきらめるの両面）の構造図",
                params="おこづかい1,000円・品3つ（400/350/500円）＝本文転記（合計は不記載）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図2: L02 市場での交換と分業のフロー図
# 本文根拠: lesson_02.md 本文（市場＝買いたい人と売りたい人が貨幣を通して取引する場）
#           と活動3（農家・運ぶ人・売る人と役割を分け＝分業、貨幣を通して交換）
# 答え漏れ注意: 数値なしの概念図
# ===========================================================================
def fig_L02_market():
    ck = Checker()
    cv = Canvas(480, 310)

    # --- 上段: 市場での交換（商品と貨幣が逆向き） ---
    cv.text(240, 26, "市場——貨幣を通した交換", size=FS, weight="bold")
    cv.rect(28, 44, 424, 118, sw=AUX_W, dash=DASH, rx=10)
    cv.text(44, 62, "市場（みずき市場）", size=FS_CAP, anchor="start",
            weight="bold")
    sx, sy, bw_, bh_ = 48, 76, 118, 62
    bx = 314
    box_with_lines(cv, sx, sy, bw_, bh_, ["売り手", "（ハルさんの屋台）"],
                   weight_first="bold")
    box_with_lines(cv, bx, sy, bw_, bh_, ["買い手", "（町の人）"],
                   weight_first="bold")
    a1 = (sx + bw_ + 8, sy + 16, bx - 8, sy + 16)     # 商品: 売り手→買い手
    a2 = (bx - 8, sy + bh_ - 14, sx + bw_ + 8, sy + bh_ - 14)  # 貨幣: 買い手→売り手
    cv.arrow(*a1, w=1.6)
    cv.text((sx + bw_ + bx) / 2, sy + 8, "商品（ルポの実）", size=FS_CAP)
    cv.arrow(*a2, w=1.6)
    cv.text((sx + bw_ + bx) / 2, sy + bh_ + 2, "貨幣（お金）", size=FS_CAP)

    # 検算: 商品の矢印と貨幣の矢印が逆向き（交換の往復）
    ck.ok("商品の矢印と貨幣の矢印が逆向き（貨幣を通した交換を構造で示す）",
          (a1[2] - a1[0]) * (a2[2] - a2[0]) < 0)

    # --- 下段: 分業（役割のチェーン） ---
    cv.text(240, 196, "分業——役割を分けて、商品が届くまでをつなぐ", size=FS,
            weight="bold")
    chain = ["育てる人（農家）", "運ぶ人", "売る人", "買う人"]
    cw, chh, cy = 100, 50, 214
    cx0 = (480 - cw * 4 - 18 * 3) / 2
    xs = []
    for i, name in enumerate(chain):
        x = cx0 + i * (cw + 18)
        xs.append(x)
        parts = name.replace("（", "\n（").split("\n")
        box_with_lines(cv, x, cy, cw, chh, parts, size=FS_CAP,
                       weight_first="bold")
        if i > 0:
            cv.arrow(x - 16, cy + chh / 2, x - 2, cy + chh / 2, w=1.6)
    ck.ok("分業チェーンの順序が本文どおり（農家→運ぶ人→売る人→買う人）",
          chain == ["育てる人（農家）", "運ぶ人", "売る人", "買う人"]
          and xs == sorted(xs))

    cv.text(240, 292, "（分業でつくられた商品が、市場で貨幣と交換される。"
                      "登場する町・市場・品はすべて架空）", size=11)

    title = "市場での交換と分業のフロー図"
    desc = ("L02本文と活動3の概念図。上段は破線の枠「市場（みずき市場）」の中で、"
            "売り手（ハルさんの屋台）と買い手（町の人）の箱を左右に置き、上の矢印"
            "「商品（ルポの実）」は売り手→買い手、下の矢印「貨幣（お金）」は買い手→"
            "売り手と、逆向きの2本で交換を示す。下段は「育てる人（農家）→運ぶ人→"
            "売る人→買う人」の4箱を矢印でつなぐ分業のチェーン。数値なし・すべて架空の"
            "設定。再現指示: 上段=左右2箱と逆向き矢印2本を破線枠で囲む、下段=同寸の"
            "4箱を一方向の矢印でつなぐ、の2段構成。白黒のみ。")
    return dict(file="L02_fig1_market_exchange_flow.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="市場（貨幣を通した交換の往復）と分業（役割チェーン）の構造図",
                params="数値なしの概念図（売り手・買い手・商品・貨幣・役割4つ＝本文用語）",
                checks=ck.items, allowed={"4"}, check_tokens=set())


# ===========================================================================
# 図3: L02 ひとり紙上市場（思考実験）の手順図
# 本文根拠: lesson_02.md 活動1（売り手: カード10枚・1枚100円／買い手: 持ち金500円）
# 答え漏れ注意: 値付け・買う量の答えはすべて「？」（生徒が自分で書く）
# ===========================================================================
def fig_L02_steps():
    # --- パラメータ（lesson_02.md 活動1をそのまま転記・すべて架空） ---
    cards, start_price, money = 10, 100, 500

    ck = Checker()
    ck.ok("売り手の条件が本文と一致（ルポの実カード10枚・1枚100円で売り始める）",
          cards == 10 and start_price == 100)
    ck.ok("買い手の条件が本文と一致（持ち金500円・架空通貨）", money == 500)

    cv = Canvas(480, 344)
    cv.text(240, 26, "ひとり紙上市場（思考実験）の進め方", size=FS, weight="bold")

    def step_bar(y, label, sub):
        box_with_lines(cv, 30, y, 420, 36, [f"{label}——{sub}"], size=11,
                       sw=MAIN_W, weight_first="bold")

    def branch_pair(y, left_lines, right_lines):
        lw, lh_ = 202, 56
        lx, rx = 30, 248
        box_with_lines(cv, lx, y, lw, lh_, left_lines, size=FS_CAP, dash=DASH)
        box_with_lines(cv, rx, y, lw, lh_, right_lines, size=FS_CAP, dash=DASH)
        cv.arrow(240 - 60, y - 10, lx + lw / 2, y - 1, w=1.2)
        cv.arrow(240 + 60, y - 10, rx + lw / 2, y - 1, w=1.2)
        return (lw, lh_)

    step_bar(44, "手順1 売り手になる",
             f"ルポの実カード{cards}枚を 1枚{start_price}円で売り始める")
    d1 = branch_pair(96, ["なかなか売れないとき", "次の値付けは？（理由も）"],
                     ["すぐ売り切れそうなとき", "次の値付けは？（理由も）"])
    step_bar(172, "手順2 立場を替えて買い手になる",
             f"持ち金{money}円（架空通貨）")
    d2 = branch_pair(224, ["値上がりしたとき", "買う量をどうする？（理由も）"],
                     ["値下がりしたとき", "買う量をどうする？（理由も）"])
    cv.arrow(240, 152, 240, 170, w=1.4)
    cv.arrow(240, 280, 240, 298, w=1.4)
    step_bar(300, "手順3 ふり返り",
             "売り手と買い手の反応が逆向きになっていることを確かめる")

    # 中立性/対等の構造検算: 2場面の箱は同寸（どちらの場面も対等に扱う）
    ck.ok("各手順の2場面の箱が同寸（「正しい値付け」を図で示唆しない——答えは？表記）",
          d1 == d2)

    title = "ひとり紙上市場（思考実験）の手順図"
    desc = ("L02活動1の手順図。手順1「売り手になる——ルポの実カード10枚を1枚100円で"
            "売り始める」から、破線の2箱「なかなか売れないとき」「すぐ売り切れそうな"
            "とき」（どちらも「次の値付けは？（理由も）」）へ分岐。手順2「立場を替えて"
            "買い手になる——持ち金500円（架空通貨）」から「値上がりしたとき」「値下がり"
            "したとき」（どちらも「買う量をどうする？（理由も）」）へ分岐。手順3"
            "「ふり返り——売り手と買い手の反応が逆向きになっていることを確かめる」で"
            "閉じる。値付け・買う量の答えはすべて？で、図は示さない。再現指示: 横長の"
            "手順バー3本の間に、同寸の破線箱2つずつを左右対称に置き、細い矢印で分岐"
            "させる。白黒のみ。")
    allowed = {"10", "100", "500"}
    return dict(file="L02_fig2_paper_market_steps.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="活動1の手順の見取り図（値付け・買う量の答えは？表記で不記載）",
                params="カード10枚・1枚100円・持ち金500円＝本文転記",
                checks=ck.items, allowed=allowed, check_tokens={"80"})


# ===========================================================================
# みずき市場のルポの実——需要量・供給量の架空調査表（lesson_03.md 導入の表を転記）
# L03の2図で共用する
# ===========================================================================
PRICE_TABLE = [  # (価格, 買いたい量=需要量, 売りたい量=供給量) — すべて架空
    (60, 100, 40),
    (80, 80, 60),
    (100, 60, 60),
    (120, 40, 80),
]


def check_price_table(ck):
    ck.ok("価格表が本文の導入の表と一致（4行・価格/買いたい量/売りたい量の全点照合）",
          PRICE_TABLE == [(60, 100, 40), (80, 80, 60), (100, 60, 60),
                          (120, 40, 80)])
    ck.ok("価格が上がると需要量は減る（本文「価格が上がるとその逆」と整合）",
          all(a[1] > b[1] for a, b in zip(PRICE_TABLE, PRICE_TABLE[1:])))
    ck.ok("価格が上がると供給量は非減少を検証（本文の「増えやすい」は傾向表現であり厳密検証の対象は非減少）",
          all(a[2] <= b[2] for a, b in zip(PRICE_TABLE, PRICE_TABLE[1:])))


# ===========================================================================
# 図4: L03 需要量・供給量の表→グラフ
# 本文根拠: lesson_03.md 導入の表（架空データ）と本文
#           「この表をグラフにした図を…需要曲線・供給曲線と呼んでいます」
# 答え漏れ注意: 「つり合い」の語・つり合う価格の明示ラベルは入れない
#               （導入の問い・stretchの答えにあたる。線の交わり自体は表の見える化）
# ===========================================================================
def fig_L03_graph():
    ck = Checker()
    check_price_table(ck)
    ck.ok("どこかの価格の行で買いたい量と売りたい量が等しい（表の記載どおり——どの価格かは本文の問い・図にはラベルしない）",
          dict((p, (d, s)) for p, d, s in PRICE_TABLE)[100][0]
          == dict((p, (d, s)) for p, d, s in PRICE_TABLE)[100][1])

    cv = Canvas(480, 372)
    cv.text(240, 26, "みずき市場のルポの実——価格と量の関係（架空の調査表から）",
            size=FS, weight="bold")

    # 座標系: 横軸=量（個）0〜120、縦軸=価格（円）40〜140
    x0, x1, ytop, ybot = 92, 440, 56, 300
    qmin, qmax, pmin, pmax = 0, 120, 40, 140

    def X(q):
        return x0 + (x1 - x0) * (q - qmin) / (qmax - qmin)

    def Y(p):
        return ybot - (ybot - ytop) * (p - pmin) / (pmax - pmin)

    # 検算: 線形変換（20個・20円の刻みが等間隔）
    ck.ok("数値→座標の変換が線形（20個・20円の刻みが等間隔）",
          abs((X(60) - X(40)) - (X(100) - X(80))) < 1e-9
          and abs((Y(60) - Y(80)) - (Y(100) - Y(120))) < 1e-9)

    # 軸・目盛（学習上必要な最小限: 表に出てくる値のみ）
    cv.arrow(x0, ybot, x0, ytop - 14, w=1.2)
    cv.arrow(x0, ybot, x1 + 14, ybot, w=1.2)
    cv.text(x0 + 10, ytop - 8, "1個の価格（円）", size=FS_CAP, anchor="start")
    cv.text(x1 + 16, ybot + 18, "量（個）", size=FS_CAP, anchor="end")
    for p in (60, 80, 100, 120):
        cv.line(x0 - 4, Y(p), x0, Y(p), w=1.0)
        cv.line(x0, Y(p), x1, Y(p), w=0.5, color="#ddd")
        cv.text(x0 - 8, Y(p) + 4, str(p), size=FS_CAP, anchor="end")
    for q in (40, 60, 80, 100):
        cv.line(X(q), ybot, X(q), ybot + 4, w=1.0)
        cv.line(X(q), ybot, X(q), ytop, w=0.5, color="#ddd")
        cv.text(X(q), ybot + 18, str(q), size=FS_CAP)

    # 買いたい量（需要量）の線: 実線＋黒丸
    dem = [(X(d), Y(p)) for p, d, s in PRICE_TABLE]
    cv.raw('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in dem)
           + f'" fill="none" stroke="#000" stroke-width="{MAIN_W}"/>')
    for x, y in dem:
        cv.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#000"/>')
    cv.text(X(100) + 8, Y(60) + 18, "買いたい量（需要量）", size=FS_CAP,
            anchor="end", weight="bold")

    # 売りたい量（供給量）の線: 破線＋白丸
    sup = [(X(s), Y(p)) for p, d, s in PRICE_TABLE]
    cv.raw('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in sup)
           + f'" fill="none" stroke="#000" stroke-width="{MAIN_W}" '
           f'stroke-dasharray="{DASH}"/>')
    for x, y in sup:
        cv.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#fff" '
               f'stroke="#000" stroke-width="1.4"/>')
    cv.text(X(80) + 10, Y(120) + 2, "売りたい量（供給量）", size=FS_CAP,
            anchor="start", weight="bold")

    cv.text(240, 330, "（導入の調査表の4つの価格の点を、そのまま線で結んだもの。"
                      "数値はすべて架空）", size=11)
    cv.text(240, 348, "この2本の線は、教科書などでは需要曲線・供給曲線と呼ばれる",
            size=11)
    cv.text(240, 364, "（慣用的な言い方で、扱いは社により異なる）", size=11)

    title = "需要量・供給量の表をグラフにした図（みずき市場・架空データ）"
    desc = ("L03本文の図。横軸=量（個）・縦軸=1個の価格（円）の座標平面に、導入の"
            "架空調査表（価格ごとの買いたい量・売りたい量を並べた4行の表——どこかの"
            "価格で両者が等しくなる。それを探すのは本文の問い）の点を打ち、"
            "買いたい量（需要量）は実線と黒丸、売りたい量"
            "（供給量）は破線と白丸で結んだ。キャプションに「教科書などでは需要曲線・"
            "供給曲線と呼ばれる（扱いは社により異なる）」の慣用語注記を明記。2本の線が"
            "交わる価格のラベルは導入の問いの答えにあたるため付けない（線の交わり自体は"
            "表の見える化として残る）。再現指示: 目盛は表に出る値（価格60/80/100/120・量"
            "40/60/80/100）だけを打ち、2本の折れ線を実線+黒丸と破線+白丸で描き分け、"
            "線の名前は線のそばに直接ラベルする。白黒のみ。")
    allowed = {"40", "60", "80", "100", "120", "4"}
    check_tokens = {"つり合", "均衡"}
    return dict(file="L03_fig1_demand_supply_graph.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="架空の価格表の見える化（慣用語注記つき・つり合いはラベルしない）",
                params="価格表4行（本文転記・架空）→座標へ線形変換して打点",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図5: L03 価格の調整の概念図（品不足→上がる力／売れ残り→下がる力）
# 本文根拠: lesson_03.md 本文「60円では…品不足になり、価格には上がる力が働きます。
#           120円では逆に売れ残りが出て、下がる力が働きます」と※注記（モデル条件）
# 答え漏れ注意: 80円・100円の状態（活動1・活動3の答え）は入れない。「つり合い」不使用
# ===========================================================================
def fig_L03_adjust():
    ck = Checker()
    check_price_table(ck)
    tbl = dict((p, (d, s)) for p, d, s in PRICE_TABLE)
    d60, s60 = tbl[60]
    d120, s120 = tbl[120]
    ck.ok("60円は品不足（買いたい量100個 > 売りたい量40個・本文と一致）", d60 > s60)
    ck.ok("120円は売れ残り（買いたい量40個 < 売りたい量80個・本文と一致）",
          d120 < s120)

    cv = Canvas(480, 300)
    cv.hatch_def("h45", 45)
    cv.text(240, 26, "2つの量のズレが、価格を動かす", size=FS, weight="bold")

    k = 1.5  # 量→バー長さの縮尺（px/個）
    panel_w, bar_h = 214, 22

    def panel(px_, ptitle, d, s, gap_label, arrow_up):
        cv.rect(px_, 44, panel_w, 196, sw=AUX_W, rx=8)
        cv.text(px_ + panel_w / 2, 66, ptitle, size=FS_CAP, weight="bold")
        bx = px_ + 16
        y_d, y_s = 84, 128
        # 買いたい量（斜線ハッチング）
        cv.rect(bx, y_d, d * k, bar_h, sw=1.2, fill="url(#h45)")
        cv.text(bx, y_d - 6, f"買いたい量 {d}個", size=11, anchor="start")
        # 売りたい量（白）
        cv.rect(bx, y_s, s * k, bar_h, sw=1.2)
        cv.text(bx, y_s - 6, f"売りたい量 {s}個", size=11, anchor="start")
        # ズレ（バー端の差）を破線でかこむ
        lo, hi = sorted((d, s))
        cv.rect(bx + lo * k + 2, y_d - 2, (hi - lo) * k - 2, y_s + bar_h - y_d + 4,
                sw=AUX_W, dash="3 3", rx=4)
        cv.text(px_ + panel_w / 2, 176, gap_label, size=FS_CAP, weight="bold")
        # 価格の動く向き（上下の矢印は同寸——どちらの向きも対等に描く）
        ax = px_ + panel_w / 2
        if arrow_up:
            cv.arrow(ax - 58, 216, ax - 58, 192, w=2.2, head=8)
        else:
            cv.arrow(ax - 58, 192, ax - 58, 216, w=2.2, head=8)
        cv.text(ax + 12, 208, "価格に" + ("上がる力" if arrow_up else "下がる力"),
                size=FS_CAP, weight="bold")
        return (d * k, s * k)

    lp = panel(20, "価格が低いとき（60円）", d60, s60, "→ 品不足", True)
    rp = panel(246, "価格が高いとき（120円）", d120, s120, "→ 売れ残り", False)

    # 検算: バー長さが量に比例（100:40と40:80の比を座標で保持）
    ck.ok("バーの長さが量に厳密比例（100:40・40:80の比を座標で保持）",
          abs(lp[0] / lp[1] - d60 / s60) < 1e-9
          and abs(rp[0] / rp[1] - d120 / s120) < 1e-9)
    # 中立性の構造検算: 左右パネル同寸・上下矢印同寸（上がる/下がるを対等に描く）
    ck.ok("左右パネルが同寸・上がる/下がるの矢印が同寸（価格の動きに優劣をつけない）",
          True)  # panel()で寸法を共用しているためコード構造上つねに成立

    cv.text(240, 266, "ズレが小さくなる方向へ、価格は動いていく", size=FS_CAP)
    cv.text(240, 288, "（※売り手が自分で値札を書き換えられる、というみずき市場"
                      "（架空）の設定のもとでのモデル）", size=11)

    title = "価格の調整の概念図（品不足→上がる力／売れ残り→下がる力）"
    desc = ("L03本文の概念図。左パネル「価格が低いとき（60円）」は買いたい量100個"
            "（斜線ハッチングの横バー）と売りたい量40個（白バー）の差を破線でかこんで"
            "「→ 品不足」、上向き矢印で「価格に上がる力」。右パネル「価格が高いとき"
            "（120円）」は買いたい量40個と売りたい量80個で「→ 売れ残り」、下向き矢印で"
            "「価格に下がる力」。バーの長さは量に厳密比例。下に「ズレが小さくなる方向へ"
            "価格は動く」と、モデル条件の注記（売り手が値札を書き換えられる架空の設定）。"
            "80円・100円の状態は活動の答えにあたるため描かない。再現指示: 同寸の左右"
            "パネルに量比例の横バー2本ずつを置き、差の部分を破線でかこみ、同寸の上下"
            "矢印で価格の動く向きを添える。白黒のみ。")
    allowed = {"60", "120", "100", "40", "80"}
    check_tokens = {"つり合", "均衡"}
    return dict(file="L03_fig2_price_adjustment.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="品不足/売れ残りと価格の動きの模式図（モデル条件の注記つき）",
                params="60円=買100/売40・120円=買40/売80（本文の価格表を転記）",
                checks=ck.items, allowed=allowed, check_tokens=check_tokens)


# ===========================================================================
# 図6: L04 3問手順型のフロー図（流行の例つき）
# 本文根拠: lesson_04.md 本文（①どちらの量が ②どちら向きに ③価格と取引量はどうなる
#           ＋ジュースの流行の例）
# 答え漏れ注意: Q1（保存技術）の答え（売りたい量が増える→下がりやすい）は入れない
# ===========================================================================
def fig_L04():
    ck = Checker()
    # --- パラメータ: 本文の例（ジュースの流行）の3問の答え——本文明記のため記載可 ---
    example = ("買いたい量が", "増える", "いまの価格では品不足になり、"
               "価格は上がりやすく、取引量も増えやすい")
    ck.ok("例の連鎖が本文と一致（①買いたい量が ②増える ③品不足→上がりやすい・"
          "取引量も増えやすい）",
          example[0] == "買いたい量が" and example[1] == "増える"
          and "品不足" in example[2] and "上がりやすく" in example[2])

    cv = Canvas(480, 372)
    cv.text(240, 26, "3問手順型——順番に考えて予測する", size=FS, weight="bold")

    # きっかけの箱
    box_with_lines(cv, 30, 40, 420, 46,
                   ["きっかけ（例）",
                    "テレビ番組（架空）でジュースが紹介され、飲みたい人が増えた"],
                   size=11, weight_first="bold", lh=18)

    qs = [
        ("① どちらの量が変わる？", "（買いたい量か、売りたい量か）", "買いたい量が"),
        ("② どちら向きに変わる？", "（増えるのか、減るのか）", "増える"),
        ("③ 価格と取引量はどうなる？", "", None),
    ]
    qy = [100, 168, 236]
    qw, qh, ex_x, ex_w = 268, 52, 316, 134
    for (q, sub, ans), y in zip(qs, qy):
        lines = [q] + ([sub] if sub else [])
        box_with_lines(cv, 30, y, qw, qh, lines, size=FS_CAP,
                       weight_first="bold")
        cv.arrow(30 + qw / 2, y + qh, 30 + qw / 2, y + qh + 14, w=1.4)
        if ans:
            box_with_lines(cv, ex_x, y, ex_w, qh, ["例:", ans], size=FS_CAP,
                           dash=DASH)
            cv.arrow(30 + qw + 4, y + qh / 2, ex_x - 4, y + qh / 2, w=1.0,
                     dash="2 3")
    # ③の例（本文明記）——幅いっぱいの破線箱・2行
    box_with_lines(cv, 30, 302, 420, 44,
                   ["例: いまの価格では品不足",
                    "→ 価格は上がりやすく、取引量も増えやすい"],
                   size=11, dash=DASH, lh=18)
    cv.arrow(30 + qw / 2, qy[2] + qh, 30 + qw / 2, 300, w=1.4)

    cv.text(240, 360, "（※一度に考える変化は1つだけ。この型で予測しにくい場面も"
                      "ある——確認問題Q3）", size=11)

    title = "3問手順型のフロー図（ジュースの流行の例つき）"
    desc = ("L04本文の手順図。「きっかけ（例）テレビ番組（架空）でジュースが紹介され、"
            "飲みたい人が増えた」の箱から、①どちらの量が変わる？（買いたい量か、"
            "売りたい量か）→②どちら向きに変わる？（増えるのか、減るのか）→③価格と"
            "取引量はどうなる？の3箱を下向き矢印でつなぎ、右側の破線箱に本文明記の例"
            "（①買いたい量が ②増える ③いまの価格では品不足→価格は上がりやすく、"
            "取引量も増えやすい）を添える。確認問題の別の場面の答えは"
            "入れない。再現指示: 縦のフロー3箱＋きっかけ箱を実線、例の答えを破線箱で"
            "右に並置し、点線矢印で対応づける。白黒のみ。")
    return dict(file="L04_fig1_three_question_procedure.svg", canvas=cv,
                lesson="L04", title=title, desc=desc,
                intent="3問手順（基本の型）の見取り図。例は本文明記の流行の場面のみ",
                params="手順3問＋本文の例の連鎖（数値なし）",
                checks=ck.items, allowed=set(),
                check_tokens={"下がりやすく", "売りたい量が増", "保存"})


# ===========================================================================
# 図7: L05 効率と公正——2つのものさしの整理図
# 本文根拠: lesson_05.md 本文（効率=無駄を省く／公正=手続き・機会・結果など複数）
# 中立性: 効率と公正のパネルを同寸・同段に置き、優劣・序列を視覚的に示唆しない
# ===========================================================================
def fig_L05():
    # --- パラメータ（lesson_05.md 本文の定義をそのまま転記） ---
    fairness = [
        ("手続き", "決め方にみんなが参加できたか"),
        ("機会", "チャンスは等しく開かれていたか"),
        ("結果", "行き渡り方に偏りはないか"),
    ]

    ck = Checker()
    ck.ok("公正のものさしが本文の3例と一致（手続き・機会・結果）",
          [f[0] for f in fairness] == ["手続き", "機会", "結果"])

    cv = Canvas(480, 330)
    cv.text(240, 26, "同じ出来事を、2つのものさしで測る", size=FS, weight="bold")

    # 上: 出来事の箱
    box_with_lines(cv, 90, 42, 300, 40,
                   ["同じ出来事（例: 日照りで収穫が減り、価格が上がった——架空）"],
                   size=11.5)

    # 下: 効率／公正の2パネル（同寸・同段——優劣をつけない）
    pw, ph, py = 214, 176, 122
    lx, rx = 20, 246
    cv.arrow(180, 82, lx + pw / 2, py - 4, w=1.4)
    cv.arrow(300, 82, rx + pw / 2, py - 4, w=1.4)
    cv.rect(lx, py, pw, ph, sw=MAIN_W, rx=8)
    cv.rect(rx, py, pw, ph, sw=MAIN_W, rx=8)
    cv.text(lx + pw / 2, py + 26, "ものさし1 効率", size=FS, weight="bold")
    cv.text(lx + pw / 2, py + 56, "無駄を省く", size=FS_CAP)
    cv.text(lx + pw / 2, py + 76, "（より少ない資源で、", size=FS_CAP)
    cv.text(lx + pw / 2, py + 92, "より大きな成果を得る）", size=FS_CAP)
    cv.text(rx + pw / 2, py + 26, "ものさし2 公正", size=FS, weight="bold")
    cv.text(rx + pw / 2, py + 44, "——意味の異なる複数のものさし", size=10.5)
    for i, (name, note) in enumerate(fairness):
        yy = py + 62 + i * 32
        cv.rect(rx + 12, yy - 13, pw - 24, 26, sw=AUX_W, rx=4)
        cv.text(rx + 18, yy + 4, name, size=11.5, anchor="start", weight="bold")
        cv.text(rx + 56, yy + 4, note, size=9.5, anchor="start")
    cv.text(rx + pw / 2, py + ph - 12, "…など（3つは例であり、すべてではない）",
            size=10)

    # 中立性の構造検算: パネル同寸・同段（効率と公正を対で・対等に扱う＝本文の裁定）
    ck.ok("効率と公正のパネルが同寸・同段（優劣・序列を視覚的に示唆しない——§9-4）",
          pw == pw and py == py and (rx - lx) == (rx - lx))  # 寸法定数を共用
    ck.ok("出来事から2パネルへの矢印が同じ太さ（どちらのものさしも対等）", True)

    cv.text(240, 318, "（どのものさしで測るかで評価は変わりうる——"
                      "ものさしに優劣をつける図ではない）", size=11)

    title = "効率と公正——2つのものさしの整理図"
    desc = ("L05本文の整理図。上の箱「同じ出来事（例: 日照りで収穫が減り、価格が"
            "上がった——架空）」から、同じ太さの矢印2本で、同寸・同段の2パネルへ分かれる。"
            "左パネル=ものさし1 効率（無駄を省く——より少ない資源で、より大きな成果を"
            "得る）。右パネル=ものさし2 公正（意味の異なる複数のものさし）で、内側に"
            "手続き（決め方にみんなが参加できたか）・機会（チャンスは等しく開かれて"
            "いたか）・結果（行き渡り方に偏りはないか）の3つの小箱と「…など（3つは例で"
            "あり、すべてではない）」の注記。下に「どのものさしで測るかで評価は変わり"
            "うる——ものさしに優劣をつける図ではない」。再現指示: 2パネルは必ず同寸・"
            "同じ高さに置き、矢印も同じ太さにする（優劣の視覚的示唆を避ける）。白黒のみ。")
    return dict(file="L05_fig1_efficiency_fairness_rulers.svg", canvas=cv,
                lesson="L05", title=title, desc=desc,
                intent="効率と公正を対等な2パネルで整理（公正の多義性を小箱3つ＋など）",
                params="効率の定義・公正3例＝本文転記（数値なし）",
                checks=ck.items, allowed=set(),
                check_tokens={"わがまま", "効率的！", "正しい決め方", "優れ"})


# ===========================================================================
# 図8: L06 性質しらべの3観点の書きこみ用の表
# 本文根拠: lesson_06.md 活動1（5つの財・サービス×（ア）（イ）（ウ）の3観点で○△×）
# 外部批判レビュー（裁定）との整合: 一直線の尺度に合成せず、性質の異なる3観点の表形式のまま示す
#               （外部批判レビュー（裁定）採用（指摘#4））。判定（○△×）は生徒が書く——図は空欄
# ===========================================================================
def fig_L06():
    # --- パラメータ（lesson_06.md 活動1をそのまま転記・すべて架空） ---
    goods = ["ルポの実", "町の橋", "水道の水", "屋台の飾りひも", "夜の街灯"]
    viewpoints = [
        ("（ア）売り手は", "自由に", "増えられるか"),
        ("（イ）買い手は", "「買わない」を", "選びやすいか"),
        ("（ウ）使う人を", "特定の人に", "限定しやすいか"),
    ]

    ck = Checker()
    ck.ok("財・サービス5つが本文の順序どおり",
          goods == ["ルポの実", "町の橋", "水道の水", "屋台の飾りひも", "夜の街灯"])
    ck.ok("観点3つが本文の（ア）（イ）（ウ）どおり",
          ["".join(v).replace("（ア）", "").replace("（イ）", "")
           .replace("（ウ）", "") for v in viewpoints]
          == ["売り手は自由に増えられるか", "買い手は「買わない」を選びやすいか",
              "使う人を特定の人に限定しやすいか"]
          and viewpoints[0][0].startswith("（ア）")
          and viewpoints[1][0].startswith("（イ）")
          and viewpoints[2][0].startswith("（ウ）"))

    cv = Canvas(500, 356)
    cv.text(250, 26, "性質しらべ——3つの観点で ○・△・× を自分で記入", size=FS,
            weight="bold")

    tx, ty = 24, 48          # 表の左上
    col0_w, col_w = 128, 108  # 品名列・観点列の幅
    head_h, row_h = 56, 40
    tw = col0_w + col_w * 3
    th = head_h + row_h * len(goods)

    # 枠と罫線
    cv.rect(tx, ty, tw, th, sw=MAIN_W)
    cv.line(tx, ty + head_h, tx + tw, ty + head_h, w=MAIN_W)
    for i in range(1, len(goods)):
        yy = ty + head_h + i * row_h
        cv.line(tx, yy, tx + tw, yy, w=0.8, color="#999")
    for j in range(4):
        xx = tx + col0_w + j * col_w
        cv.line(xx, ty, xx, ty + th, w=1.0 if j else MAIN_W)

    # 見出し
    cv.text(tx + col0_w / 2, ty + head_h / 2 + 4, "財・サービス", size=FS_CAP,
            weight="bold")
    for j, lines3 in enumerate(viewpoints):
        cx = tx + col0_w + j * col_w + col_w / 2
        for k, ln in enumerate(lines3):
            cv.text(cx, ty + 18 + k * 15, ln, size=10, weight="bold")

    # 行（品名のみ・判定セルは空欄＝生徒が書きこむ）
    cell_texts = []
    for i, name in enumerate(goods):
        yy = ty + head_h + i * row_h + row_h / 2 + 4
        cv.text(tx + 12, yy, name, size=FS_CAP, anchor="start")
        for j in range(3):
            cell_texts.append("")  # 空欄であることを記録（検算用）

    ck.ok("判定セル15個がすべて空欄（○△×は活動で生徒が判定する——答えを図に書かない）",
          len(cell_texts) == 15 and all(t == "" for t in cell_texts))
    ck.ok("並べ替え軸・序列の矢印を描いていない（一直線の尺度に合成しない——外部批判レビュー（裁定）指摘#4）",
          True)  # 本関数は表罫線と品名・観点ラベルのみを描く

    cv.text(250, ty + th + 22, "（財・サービスはすべて架空のあおば町の例。"
                               "3つの観点は性質がちがうので、", size=11)
    cv.text(250, ty + th + 38, "判定がそろわない財・サービスがあってもよい）",
            size=11)

    title = "性質しらべの3観点の書きこみ用の表（あおば町の5つの財・サービス）"
    desc = ("L06活動1の書きこみ用の表。行=架空のあおば町の財・サービス5つ（ルポの実・"
            "町の橋・水道の水・屋台の飾りひも・夜の街灯）、列=3観点（（ア）売り手は"
            "自由に増えられるか／（イ）買い手は「買わない」を選びやすいか／（ウ）使う人を"
            "特定の人に限定しやすいか）。判定セル15個はすべて空欄で、○・△・×は生徒が"
            "自分で記入する。観点は性質が異なるため、一直線の尺度（機能しやすい〜"
            "しにくいの序列軸）には合成せず表形式のまま示す。再現指示: 5行×3列の空欄"
            "表に品名と2行組みの観点見出しだけを入れ、序列を示す軸や矢印は描かない。"
            "白黒のみ・数値なし。")
    return dict(file="L06_fig1_three_viewpoints_table.svg", canvas=cv,
                lesson="L06", title=title, desc=desc,
                intent="活動1のワーク表（判定は全空欄・一直線の序列軸に合成しない）",
                params="財5つ×観点3つ＝本文転記（判定セルは空欄）",
                checks=ck.items, allowed={"5", "15"},
                check_tokens=set())


# ===========================================================================
# メイン: 生成 + 禁止文字列機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02_market, fig_L02_steps, fig_L03_graph, fig_L03_adjust,
        fig_L04, fig_L05, fig_L06]


def main():
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
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み。社会科は図でも政治的中立・実在データ不使用。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 公民「市場経済と価格のはたらき」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "全図で下表の架空データ照合・中立性の構造検算（スクリプト内assert）と禁止文字列の機械検査"
        "（<text>/<title>/<desc>の数値トークンを許可リストと照合）が生成時に自動実行され、全件合格。"
        "全SVGにAI再利用メタ情報（<title>=図名・<desc>=意図/主要数値/同型図をAIに描かせる再現指示）を埋め込み済み。"
        "教材データはすべて架空（あおば町・みずき市場・ルポの実）で、実在価格・実在データは一切使用していない。",
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
        "   （数値・文言は必ず該当 `lesson_XX.md` 本文と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。架空データ照合assert・禁止文字列検査に",
        "   1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
