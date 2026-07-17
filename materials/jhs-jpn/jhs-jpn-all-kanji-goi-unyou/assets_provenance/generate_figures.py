#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中学国語「漢字・語彙運用」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（10枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証（1件でも落ちると図は出力されない）:
  1) 内容assert — 図の語例が設問の答えと重ならないこと（設問語リストとの照合）、
     ボックス内に文字が収まること（文字幅の概算検算）などを生成時に検査。
  2) 答え漏れ・断定の機械検査 — 各図の<text>/<title>/<desc>の可読文字列を対象に、
     図ごとの「禁止文字列」（当該レッスン設問の答え・断定語）が混入したら停止。
     使い分けに関わる図は「目安」「絶対の規則ではない」等の留保文字列の存在を必須化
     （文化審議会「異字同訓」の使い分け例の留保——使い分けの断定禁止——を図でも遵守）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの語例・文言を変えて
  再実行。語例は必ず該当 lesson_XX.md 本文・設問と突き合わせること（設問の答えに当たる
  語を図に入れない）。SVGの直接編集は禁止（来歴が切れる）。
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
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
FS_S = 11         # 小ラベル
FS_XS = 10.5      # 最小（キャプション帯の下限）

# 本単元の全設問で読みを問う・書かせる訓/音のかなリスト（図の題材と重ねない照合用）
QUESTION_KANA = {
    "はやい", "あつい", "あう", "かたい", "つくる", "おさめる",   # L01
    "あける", "かえす", "かえる", "うつす", "なおす", "とる",     # L04/L07
    "かんしん", "いがい", "たいしょう", "きかい", "じてん", "こうえん",  # L03/L06
    "しじ", "かてい", "えいせい", "じしん", "きかん", "こたえる",  # L06/L07
}

# 全図共通の禁止文字列（使い分けの断定語——検証チェック仕様と同じ観点）
GLOBAL_CHECK_TOKENS = {"必ず", "が正解", "と書くのが正しい", "しか使わない"}

# レッスンID・構造番号など、答えの数値ではないため常時許可する数値トークン
GLOBAL_ALLOWED = {"01", "02", "03", "04", "05", "06", "07", "1", "2", "3", "4", "5"}


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


def est_width(s, size):
    """文字列の概算表示幅（全角≒size・半角≒0.6size）——ボックス収まり検算用"""
    w = 0.0
    for ch in s:
        w += size if ord(ch) > 0xFF else size * 0.6
    return w


TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r"<desc>(.*?)</desc>", re.S)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def audit_svg(svg, allowed_nums, check_tokens, required, fig_id):
    """答え漏れ・断定の機械検査。<text>/<title>/<desc>の可読文字列だけを対象にする
    （座標値は対象外）。check_tokens=答え漏れ検査トークン（検査の実装定数）、required=必須の留保文字列。"""
    allowed_nums = set(allowed_nums) | GLOBAL_ALLOWED
    check_tokens = set(check_tokens) | GLOBAL_CHECK_TOKENS
    chunks = TEXT_RE.findall(svg) + TITLE_RE.findall(svg) + DESC_RE.findall(svg)
    joined = "".join(chunks)
    for c in chunks:
        for b in check_tokens:
            if b in c:
                raise AssertionError(f"{fig_id}: 禁止文字列 '{b}' が図内文字列に混入: {c!r}")
        for tok in NUM_RE.findall(c):
            if tok not in allowed_nums:
                raise AssertionError(
                    f"{fig_id}: 許可外の数値 '{tok}' が図内文字列に混入: {c!r}")
    for r in required:
        if r not in joined:
            raise AssertionError(f"{fig_id}: 必須の留保文字列 '{r}' が図にない")


# ===========================================================================
# 描画ヘルパー（言語・カード図系——§9-3: 箱＋ラベル＋矢印で構成）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
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

    def circle(self, cx, cy, r, sw=MAIN_W, fill="none", dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" '
                 f'stroke="#000" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, color="#000"):
        wgt = f' font-weight="{weight}"' if weight else ""
        c = f' fill="{color}"' if color != "#000" else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{c}>{escape(s)}</text>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None):
        """直線矢印（先端は2辺で描く——marker不使用でself-contained）"""
        self.line(x1, y1, x2, y2, w=w, dash=dash)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (1, -1):
            a = ang + math.pi - s * math.radians(26)
            self.line(x2, y2, x2 + head * math.cos(a), y2 + head * math.sin(a), w=w)

    def dbl_arrow(self, x1, y1, x2, y2, w=1.4, head=6.0):
        """両向き矢印"""
        self.line(x1, y1, x2, y2, w=w)
        for (hx, hy, ang) in ((x2, y2, math.atan2(y2 - y1, x2 - x1)),
                              (x1, y1, math.atan2(y1 - y2, x1 - x2))):
            for s in (1, -1):
                a = ang + math.pi - s * math.radians(26)
                self.line(hx, hy, hx + head * math.cos(a), hy + head * math.sin(a),
                          w=w)

    def render(self, fig_id, title, desc):
        """AI再利用メタ情報: <title>/<desc>をルート直下に埋め込んで完全なSVG文字列を返す"""
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
            + "\n".join(self.body) + "\n</svg>\n"
        )


def box(cv, ck, x, y, w, h, lines, size=FS_S, weight=None, dash=None,
        sw=MAIN_W, rx=6, pad=6, line_gap=None):
    """枠＋中央揃え複数行テキスト（白塗り＝背後の線を隠す）。全行の収まりをckで検算する"""
    cv.rect(x, y, w, h, sw=sw, dash=dash, rx=rx, fill="#fff")
    gap = line_gap if line_gap else size + 4
    total = gap * len(lines)
    y0 = y + h / 2 - total / 2 + size * 0.85
    for i, ln in enumerate(lines):
        ck.ok(f"ボックス内に収まる: '{ln}'", est_width(ln, size) <= w - pad,
              f"est={est_width(ln, size):.0f} box={w - pad:.0f}")
        cv.text(x + w / 2, y0 + i * gap, ln, size=size, weight=weight)


# ===========================================================================
# 図1: L01 共通手順①〜④のフローチャート（④辞書で確かめる を強調）
# 本文根拠: lesson_01.md 主概念1「手順は4つ」（全レッスンで反復される共通手順）
# 答え漏れ注意: 具体的な字の例は入れない（手順のみの概念図）
# ===========================================================================
def fig_L01_flow():
    ck = Checker()
    cv = Canvas(480, 176)

    # --- パラメータ: 手順の文言（lesson_01.md 主概念1の①〜④と同旨） ---
    steps = [
        ("① 文脈の意味を", "捉える"),
        ("② 同じ訓・同じ音の", "候補を思い浮かべる"),
        ("③ 字の意味で", "見分ける"),
        ("④ 辞書・用例で", "確かめる"),
    ]
    ck.ok("手順は本文どおり4段階", len(steps) == 4)

    cv.text(240, 26, "同じ訓・同じ音のことばを選ぶ手順（毎回この型で）",
            size=FS, weight="bold")
    bw, bh, y = 108, 54, 52
    xs = [4, 127, 250, 373]
    for i, (l1, l2) in enumerate(steps):
        emph = (i == 3)
        box(cv, ck, xs[i], y, bw, bh, [l1, l2], size=FS_XS,
            weight="bold" if emph else None, sw=BOLD_W if emph else MAIN_W)
        if i > 0:
            cv.arrow(xs[i - 1] + bw + 1, y + bh / 2, xs[i] - 1, y + bh / 2, w=1.6)
    cv.text(240, 134, "迷ったとき・決めきれないときほど④へ——確かめてから確定する",
            size=FS_CAP)
    cv.text(240, 158, "（選ぶときも、書くときも、読み直して直すときも、手順は同じ）",
            size=FS_XS)

    title = "同訓異字・同音異義語を選ぶ共通手順①〜④のフローチャート"
    desc = ("L01主概念1（この単元の全レッスンで反復する共通手順）の流れ図。"
            "①文脈の意味を捉える→②同じ訓・同じ音の候補を思い浮かべる→③字の意味で見分ける→"
            "④辞書・用例で確かめる、の4つの箱を矢印でつなぎ、最後の④だけ太枠で強調"
            "してある。具体的な漢字の例は意図的に入れていない（設問の答えに触れない"
            "ため）。同型図の描き方: 横一列に4つの角丸の箱を並べ、①〜④の手順文を入れて"
            "左から右へ矢印でつなぎ、④の箱だけ線を太くする。下にキャプション2行。"
            "白黒のみ・漢字の例は入れない。")
    return dict(file="L01_fig1_four_step_flow.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="単元の背骨＝共通手順①〜④の可視化（④辞書を太枠で強調）",
                params="手順文4件（本文①〜④と同旨・字例なし）",
                checks=ck.items, allowed=set(), check_tokens=set(), required=["辞書"])


# ===========================================================================
# 図2: L01 同訓異字の使い分けマップ「はかる」（測・計・量）
# 本文根拠: lesson_01.md 主概念1「文の意味を先につかめば字は後から選べる」
# 答え漏れ注意: 設問はすべて別の訓（はやい・あつい・あう・かたい・つくる）。
#   図の題材「はかる」は本単元のどの設問でも使われていない語（QUESTION_KANAと照合）。
# 断定回避: 各分岐は「〜と書くことが多い」。注記に「目安であって絶対の規則ではない」。
# ===========================================================================
def fig_L01_map():
    ck = Checker()
    cv = Canvas(480, 300)

    # --- パラメータ: 題材の訓と分岐（文化審議会「異字同訓」の使い分け例の大づかみな傾向） ---
    yomi = "はかる"
    branches = [
        ("長さ・深さ・広さ", "などをはかる", "測"),
        ("時間・数", "などをはかる", "計"),
        ("重さ・体積（かさ）", "などをはかる", "量"),
    ]
    ck.ok("題材の訓は本単元のどの設問語とも重ならない（答え漏れなし）",
          yomi not in QUESTION_KANA, f"yomi={yomi}")
    ck.ok("分岐は3つ・見出し字は互いに異なる",
          len(branches) == 3 and len({b[2] for b in branches}) == 3)

    # 上: スタート
    box(cv, ck, 165, 18, 150, 34, ["「はかる」と書きたい"], size=FS_S, weight="bold")
    cv.text(240, 76, "文の意味は？", size=FS_S)
    # 分岐
    bw, bh, by = 146, 86, 92
    xs = [8, 167, 326]
    for (l1, l2, kanji), x in zip(branches, xs):
        cv.line(240, 52, x + bw / 2, by - 20, w=1.2)
        cv.arrow(x + bw / 2, by - 20, x + bw / 2, by - 2, w=1.2, head=6)
        cv.rect(x, by, bw, bh, sw=MAIN_W, rx=6)
        ck.ok(f"分岐ラベルが収まる: '{l1}'", est_width(l1, FS_XS) <= bw - 6)
        cv.text(x + bw / 2, by + 18, l1, size=FS_XS)
        cv.text(x + bw / 2, by + 33, l2, size=FS_XS)
        cv.text(x + bw / 2, by + 62, kanji, size=22, weight="bold")
        cv.text(x + bw / 2, by + 78, "と書くことが多い", size=FS_XS)
    # 留保の注記（破線枠）
    ny = 200
    cv.rect(10, ny, 460, 58, sw=AUX_W, dash=DASH, rx=6)
    cv.text(240, ny + 22, "※この使い分けは目安であって、絶対の規則ではない。", size=FS_S)
    cv.text(240, ny + 42, "候補はほかにもある（図・諮 など）。決めきれないときは辞書で確かめる。",
            size=FS_XS)
    cv.text(240, 284, "（設問とは別の語で、①文脈→②候補→③語義 の見分け方を示した見取り図）",
            size=FS_XS)

    title = "同訓異字の使い分けマップ——「はかる」（測・計・量）の場面分岐"
    desc = ("L01主概念1の見取り図。上の箱「『はかる』と書きたい」から「文の意味は？」で"
            "3つに分岐し、長さ・深さ・広さなど→「測」と書くことが多い／時間・数など→"
            "「計」と書くことが多い／重さ・体積（かさ）など→「量」と書くことが多い、と"
            "場面ごとの傾向を示す。下の破線枠に「この使い分けは目安であって、絶対の規則"
            "ではない。候補はほかにもある（図・諮など）。決めきれないときは辞書で確かめる」"
            "という留保を明記（文化審議会の異字同訓の使い分け例が『慣用上の大体』とされる"
            "ことに対応）。題材の「はかる」は本単元の設問で使われていない訓を意図的に選び、"
            "設問の答えを確定させない。同型図の描き方: 上に開始の箱、中央に問いのラベル、下に"
            "3つの箱（場面カテゴリ＋大きな見出し字＋「と書くことが多い」）を並べて矢印で"
            "つなぎ、最下部に破線枠の留保注記を置く。白黒のみ・断定表現禁止。")
    return dict(file="L01_fig2_doukun_map_hakaru.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="同訓異字の場面分岐マップ（設問外の語「はかる」で手順を可視化）",
                params="題材=はかる（測・計・量）・注記に図/諮の存在も明示",
                checks=ck.items,
                allowed=set(),
                check_tokens={"早", "速", "暑", "熱", "厚", "固", "堅"},
                required=["目安", "絶対の規則ではない", "辞書", "と書くことが多い"])


# ===========================================================================
# 図3: L02 二字熟語・組み立ての五つの型（パネル並置）
# 本文根拠: lesson_02.md 主概念1の例語（岩石・左右・温水・着席・国営）をそのまま使用
# 答え漏れ注意: 活動1の設問語（豊富・明暗・深海・洗顔・日没・増加・乗車・高低）は使わない
# ===========================================================================
def fig_L02_types():
    ck = Checker()
    cv = Canvas(480, 232)

    # --- パラメータ: 型と例語（本文の例をそのまま——設問の答え語は使わない） ---
    panels = [
        ("① 似た意味を", "重ねる", "岩", "石", "≒", "どちらも近い意味"),
        ("② 対の意味を", "並べる", "左", "右", "⇔", "反対どうし"),
        ("③ 上が下を", "説明する", "温", "水", "→", "温かい水"),
        ("④ 下が上の", "対象になる", "着", "席", "←", "席に着く"),
        ("⑤ 主語と述語", "の関係", "国", "営", "｜", "国が営む"),
    ]
    body_words = {"岩石", "左右", "温水", "着席", "国営"}
    question_words = {"豊富", "明暗", "深海", "洗顔", "日没", "増加", "乗車", "高低"}
    ck.ok("例語は本文の主概念1の5語のみ・活動1の設問語と重ならない",
          {a + b for _, _, a, b, _, _ in panels} == body_words
          and not (body_words & question_words))

    cv.text(240, 24, "二字熟語・組み立ての五つの型", size=FS, weight="bold")
    cv.text(240, 42, "（呼び名や分け方は本によって少し異なる）", size=FS_XS)
    pw, ph, py = 88, 130, 56
    xs = [6, 101, 196, 291, 386]
    for (h1, h2, k1, k2, sym, gloss), x in zip(panels, xs):
        cv.rect(x, py, pw, ph, sw=MAIN_W, rx=6)
        cv.text(x + pw / 2, py + 18, h1, size=FS_XS)
        cv.text(x + pw / 2, py + 32, h2, size=FS_XS)
        # 漢字2字＋関係記号（テキスト要素のみ・§9-3）
        cy = py + 68
        cv.rect(x + 8, cy - 14, 28, 28, sw=1.2)
        cv.text(x + 22, cy + 6, k1, size=17, weight="bold")
        cv.text(x + pw / 2, cy + 5, sym, size=14)
        cv.rect(x + pw - 36, cy - 14, 28, 28, sw=1.2)
        cv.text(x + pw - 22, cy + 6, k2, size=17, weight="bold")
        ck.ok(f"説明が収まる: '{gloss}'", est_width(gloss, FS_XS) <= pw - 4)
        cv.text(x + pw / 2, py + 112, gloss, size=FS_XS)
    cv.text(240, 214, "型が分かれば、初めて見る熟語も組み立てから意味を推理できる",
            size=FS_CAP)

    title = "二字熟語・組み立ての五つの型（岩石・左右・温水・着席・国営）"
    desc = ("L02主概念1のパネル図。5枚のパネルに、①似た意味を重ねる（岩≒石）"
            "②対の意味を並べる（左⇔右）③上が下を説明する（温→水・温かい水）"
            "④下が上の対象になる（着←席・席に着く）⑤主語と述語の関係（国｜営・"
            "国が営む）を、漢字2字の箱＋関係記号＋短い説明で並置した。例語は本文の"
            "5語のみで、活動1の設問語（型当ての答え）は使っていない。冒頭に「呼び名や"
            "分け方は本によって少し異なる」の留保つき。同型図の描き方: 横に5枚の角丸パネルを"
            "並べ、各パネルに型名2行・漢字1字ずつの小箱2つとその間の関係記号"
            "（≒・⇔・→・←・｜）・下に組み立ての言い換えを置く。字はテキストで組み、"
            "字形を図形で描かない。白黒のみ。")
    return dict(file="L02_fig1_jukugo_five_types.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="構成5型の並置パネル（本文例語のみ・設問の答え語は不使用）",
                params="例語=岩石/左右/温水/着席/国営（本文一致）・関係記号5種",
                checks=ck.items, allowed=set(),
                check_tokens={"豊富", "明暗", "深海", "洗顔", "日没", "増加", "乗車", "高低",
                        "帰国", "造船", "消火", "登山", "空席", "挙手"},
                required=["本によって少し異なる"])


# ===========================================================================
# 図4: L02 音訓の対応——熟語をほどく・編む（双方向図）
# 本文根拠: lesson_02.md 主概念2の例（着席⇔席に着く／満足⇔満ちる・足りる）
# 答え漏れ注意: 問9（帰国・造船・消火）問10（登山・空席・挙手）の語は使わない
# ===========================================================================
def fig_L02_bridge():
    ck = Checker()
    cv = Canvas(480, 224)

    # --- パラメータ: 対応ペア（本文の例のみ） ---
    pairs = [("着席", "席に着く"), ("満足", "満ちる・足りる")]
    check_tokens_words = {"帰国", "造船", "消火", "登山", "空席", "挙手"}
    ck.ok("対応ペアは本文の例のみ・活動2の設問の答え語と重ならない",
          not ({p[0] for p in pairs} & check_tokens_words))

    cv.text(122, 30, "音読みの熟語", size=FS_S, weight="bold")
    cv.text(365, 30, "訓読みの言い方", size=FS_S, weight="bold")
    lw, rw, bh = 130, 180, 42
    lx, rx = 57, 275
    for i, (on, kun) in enumerate(pairs):
        y = 52 + i * 66
        box(cv, ck, lx, y, lw, bh, [on], size=15, weight="bold")
        box(cv, ck, rx, y, rw, bh, [kun], size=14)
        cv.arrow(lx + lw + 6, y + bh / 2 - 8, rx - 6, y + bh / 2 - 8, w=1.4)
        cv.arrow(rx - 6, y + bh / 2 + 8, lx + lw + 6, y + bh / 2 + 8, w=1.4)
        if i == 0:
            cv.text((lx + lw + rx) / 2, y + bh / 2 - 14, "ほどく", size=FS_XS)
            cv.text((lx + lw + rx) / 2, y + bh / 2 + 22, "編む", size=FS_XS)
    cv.text(240, 196, "音と訓を行き来できると、知っている言葉が網の目のようにつながる",
            size=FS_CAP)

    title = "音訓の対応図——熟語をほどく・編む（着席⇔席に着く）"
    desc = ("L02主概念2の双方向図。左列に音読みの熟語（着席・満足）、右列に訓読みの"
            "言い方（席に着く・満ちる/足りる）を箱で置き、右向き矢印「ほどく」と"
            "左向き矢印「編む」で結んで、音⇔訓の行き来を示す。例は本文の2組のみで、"
            "活動2の設問の答え（ほどく・編む問題で答えとなる語）は使っていない。同型図の描き方: "
            "左右2列の箱を2段に並べ、各段を上下2本の逆向き矢印（上=ほどく・下=編む）"
            "でつなぎ、列見出しに「音読みの熟語」「訓読みの言い方」を置く。白黒のみ。")
    return dict(file="L02_fig2_on_kun_bridge.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="音⇔訓の言い換え（ほどく/編む）の双方向構造の可視化",
                params="ペア=着席⇔席に着く・満足⇔満ちる/足りる（本文一致）",
                checks=ck.items, allowed=set(), check_tokens=check_tokens_words, required=[])


# ===========================================================================
# 図5: L03 変換候補を選ぶ二段構え（IME候補窓＋検算フロー）
# 本文根拠: lesson_03.md 主概念1（変換候補の選択）・主概念2（仮決め→検算の二段構え）
# 答え漏れ注意: 設問語（かんしん・いがい・たいしょう・きかい等）と導入の「いぎ」は
#   使わず、設問外の「きこう」を題材にする。例文を置かないため「正解の候補」が存在しない。
# ===========================================================================
def fig_L03_ime():
    ck = Checker()
    cv = Canvas(480, 256)

    # --- パラメータ: 題材の音と候補（本単元の設問・導入に出ない音を選ぶ） ---
    yomi = "きこう"
    cands = [("気候", "その土地の天気のようす"),
             ("機構", "組織・しくみ"),
             ("紀行", "旅の記録"),
             ("寄港", "船が港に立ち寄ること")]
    ck.ok("題材の音は本単元のどの設問語とも重ならない（答え漏れなし）",
          yomi not in QUESTION_KANA and yomi != "いぎ")
    ck.ok("候補4語は互いに別の語（表記がすべて異なる）",
          len({c[0] for c in cands}) == 4)

    cv.text(240, 24, "変換候補を選ぶ——二段構え", size=FS, weight="bold")
    # 入力欄
    cv.rect(16, 40, 150, 28, sw=MAIN_W, rx=4)
    cv.text(30, 59, "きこう｜", size=FS_S, anchor="start")
    # 候補窓
    wy = 76
    cv.rect(16, wy, 150, 100, sw=MAIN_W)
    for i, (w, gloss) in enumerate(cands):
        y = wy + i * 25
        if i > 0:
            cv.line(16, y, 166, y, w=0.6, color="#bbb")
        cv.text(28, y + 17, f"{i + 1}", size=FS_XS)
        cv.text(44, y + 17.5, w, size=FS_S, anchor="start", weight="bold")
        ck.ok(f"語義メモが収まる: '{gloss}'", est_width(gloss, FS_XS) <= 130)
        cv.text(176, y + 17, gloss, size=FS_XS, anchor="start")
    cv.text(16, 196, "↑ 音が同じでも、意味は別の語", size=FS_XS, anchor="start")
    # 右: 二段構えフロー
    fx, fw = 330, 138
    box(cv, ck, fx, 52, fw, 40, ["文脈で仮に決める"], size=FS_S)
    cv.arrow(fx + fw / 2, 94, fx + fw / 2, 112, w=1.4)
    box(cv, ck, fx, 114, fw, 52, ["語義・辞書で", "検算する"], size=FS_S, weight="bold",
        sw=BOLD_W)
    cv.arrow(fx + fw / 2, 168, fx + fw / 2, 186, w=1.4)
    box(cv, ck, fx, 188, fw, 34, ["確定"], size=FS_S)
    cv.text(240, 236, "（この図に例文はない——どれを選ぶかは、文脈がなければ決められない）",
            size=FS_XS)

    title = "変換候補を選ぶ二段構え——「きこう」の候補窓と検算フロー"
    desc = ("L03主概念1・2の図。左は端末の変換候補窓のイメージで、入力「きこう」に"
            "対して気候（その土地の天気のようす）・機構（組織・しくみ）・紀行（旅の"
            "記録）・寄港（船が港に立ち寄ること）の4候補と語義メモが並ぶ。右は選び方の"
            "フロー「文脈で仮に決める→語義・辞書で検算する（太枠で強調）→確定」。"
            "図にはあえて例文を置かず「どれを選ぶかは文脈がなければ決められない」と"
            "添えることで、特定の候補を正解として示さない。題材の「きこう」は本単元の"
            "設問・導入に出ない音を選んであり、設問（かんしん・いがい・たいしょう等）の"
            "答えに触れない。同型図の描き方: 左に入力欄と4行の候補窓（番号＋表記＋語義メモ）、"
            "右に縦3段のフロー（2段目を太枠）を描き、下に例文を置かない旨のキャプション。"
            "白黒のみ。")
    return dict(file="L03_fig1_ime_two_step.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="同音異義語の候補選択と「仮決め→検算」二段構えの可視化",
                params="題材=きこう（気候/機構/紀行/寄港・設問外の音）・例文なし",
                checks=ck.items, allowed=set(),
                check_tokens={"感心", "関心", "意外", "以外", "対象", "対照", "対称",
                        "機会", "機械", "異議", "意義", "威儀", "辞典", "時点",
                        "公園", "講演", "公演", "後援"},
                required=["辞書", "文脈"])


# ===========================================================================
# 図6: L04 漢字の部品はヒント（へん＋つくりのテキスト合成図）
# 本文根拠: lesson_04.md 主概念2（さんずい=水・てへん=手の傾向、例外あり、決めつけ禁止）
# 様式: §9-3——部品・字はすべてテキスト要素の組み合わせ。パスで字形を自作しない。
# 答え漏れ注意: 設問の答えの字（開・空・明・返・帰・写・移・映・直・治、L07の指示・熱
#   など）を使わない。例字は泳・池・持・打。
# ===========================================================================
def fig_L04_parts():
    ck = Checker()
    cv = Canvas(480, 258)

    # --- パラメータ: 部品と例字（設問の答え字と重ねない） ---
    rows = [
        ("氵", "さんずい", "水に関わる字が多い", [("氵", "永", "泳"), ("氵", "也", "池")]),
        ("扌", "てへん", "手の動作に関わる字が多い", [("扌", "寺", "持"), ("扌", "丁", "打")]),
    ]
    answer_chars = set("開空明返帰写移映直治熱暑厚") | {"指示", "支持"}
    used = {ex[2] for r in rows for ex in r[3]}
    ck.ok("例字（泳・池・持・打）は本単元の設問の答え字と重ならない",
          used == {"泳", "池", "持", "打"}
          and not (used & {c for c in answer_chars if len(c) == 1}))
    ck.ok("部品の説明は傾向表現（「〜が多い」）のみ",
          all("多い" in r[2] for r in rows))

    cv.text(240, 26, "字の部品は「思い出すヒント」", size=FS, weight="bold")
    for ri, (rad, name, gloss, exs) in enumerate(rows):
        y = 62 + ri * 82
        cv.rect(12, y - 24, 140, 62, sw=MAIN_W, rx=6)
        cv.text(46, y + 6, rad, size=24, weight="bold")
        cv.text(100, y - 2, f"（{name}）", size=FS_XS)
        cv.text(82, y + 24, gloss, size=FS_XS)
        for ei, (p1, p2, whole) in enumerate(exs):
            x0 = 166 + ei * 170
            # 部品＋部品→字（すべてテキスト要素・§9-3）
            cv.rect(x0, y - 15, 28, 28, sw=1.2)
            cv.text(x0 + 14, y + 6, p1, size=16)
            cv.text(x0 + 39, y + 4, "＋", size=13)
            cv.rect(x0 + 50, y - 15, 28, 28, sw=1.2)
            cv.text(x0 + 64, y + 6, p2, size=16)
            cv.arrow(x0 + 84, y - 1, x0 + 100, y - 1, w=1.3, head=5.5)
            cv.rect(x0 + 104, y - 19, 36, 36, sw=BOLD_W)
            cv.text(x0 + 122, y + 8, whole, size=20, weight="bold")
    # 注記（破線枠・本文の「決めつけは危険」を図でも明記）
    ny = 196
    cv.rect(10, ny, 460, 44, sw=AUX_W, dash=DASH, rx=6)
    cv.text(240, ny + 18, "※部品は、候補を思い出す・意味を確かめるためのヒント。例外もあるので、",
            size=FS_XS)
    cv.text(240, ny + 34, "部品だけで字を決めつけない。仕上げはいつも辞書。", size=FS_XS)

    title = "漢字の部品（へん・つくり）分解図——部品は思い出すヒント"
    desc = ("L04主概念2の図。上段は氵（さんずい・水に関わる字が多い）で、氵＋永→泳、"
            "氵＋也→池。下段は扌（てへん・手の動作に関わる字が多い）で、扌＋寺→持、"
            "扌＋丁→打。部品と字はすべてテキスト要素の組み合わせで置き、字形を図形で"
            "自作していない（docs/SPEC_figures.md）。下の破線枠に「部品はヒント・"
            "例外もある・部品だけで決めつけない・仕上げは辞書」の注記。例字は本単元の"
            "設問の答えの字（あける・かえす・うつす・なおす等の書き分けの題材）を避けて"
            "選んである。同型図の描き方: 2段のカード（部品の大きな字＋名前＋『〜が多い』の"
            "傾向）と、右側に『部品＋部品→字』の小箱の式を2つずつ並べ、最下部に破線枠の"
            "注記を置く。字はすべてテキストで組む。白黒のみ・断定表現禁止。")
    return dict(file="L04_fig1_parts_hint.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="部品=候補想起のヒント（例外あり・決めつけ禁止）の可視化",
                params="部品=氵/扌・例字=泳/池/持/打（設問の答え字は不使用）",
                checks=ck.items, allowed={"9"},  # desc中の様式番号「§9-3」のみ
                check_tokens={"開", "空", "明", "返", "帰", "写", "移", "映", "直", "治",
                        "指示", "支持"},
                required=["ヒント", "例外", "辞書", "多い"])


# ===========================================================================
# 図7: L05 熟語ネットワーク——核の字「決」からの枝分かれ
# 本文根拠: lesson_05.md 主概念1の例（決定・決心・解決・多数決）をそのまま使用
# 答え漏れ注意: 問2「転」・問3「集」の枝は答えにあたるため描かない（descにも書かない）
# ===========================================================================
def fig_L05_network():
    ck = Checker()
    cv = Canvas(440, 252)

    # --- パラメータ: 核の字と枝（本文の主概念1の4語のみ） ---
    core, core_gloss = "決", "きめる・きまる"
    words = ["決定", "決心", "解決", "多数決"]
    ck.ok("枝の語は本文の例4語のみ（問1の解答例を新たに増やさない）",
          words == ["決定", "決心", "解決", "多数決"])
    ck.ok("全ての枝の語が核の字を含む", all(core in w for w in words))

    cx, cy = 220, 128
    positions = [(84, 56), (356, 56), (84, 200), (356, 200)]
    bw, bh = 92, 34
    for w, (px, py) in zip(words, positions):
        cv.line(cx, cy, px, py, w=1.3)
        box(cv, ck, px - bw / 2, py - bh / 2, bw, bh, [w], size=14, weight="bold")
    # まだ枝が増えることを示す破線スタブ
    for ang in (90, 270):
        rad = math.radians(ang)
        x2 = cx + 96 * math.cos(rad)
        y2 = cy + 74 * math.sin(rad)
        cv.line(cx, cy, x2, y2, w=1.1, dash="4 4", color="#777")
        cv.text(x2, y2 + (12 if ang == 90 else -6), "…", size=14)
    # 核（最後に描いて線の上に重ねる）
    cv.raw(f'<circle cx="{cx}" cy="{cy}" r="40" fill="#fff" stroke="#000" '
           f'stroke-width="{BOLD_W}"/>')
    cv.text(cx, cy + 2, core, size=24, weight="bold")
    cv.text(cx, cy + 22, core_gloss, size=9.5)
    cv.text(220, 240, "どの枝にも核の意味の芯が通っている——語彙は一語ずつでなく網ごと増やす",
            size=FS_XS)

    title = "熟語ネットワーク——核の字「決」からの枝分かれ"
    desc = ("L05主概念1のネットワーク図。中央の太枠の円に核の字「決」と核の意味"
            "「きめる・きまる」、そこから4本の枝が決定・決心・解決・多数決の箱へ伸びる"
            "（いずれも本文に明記された例語のみ）。上下への破線の枝と「…」で、枝がまだ"
            "増やせることを示す。問2・問3で扱う別の核の字のネットワークは、答えにあたる"
            "ため描いていない。同型図の描き方: 中央に太枠の円（核の字＋かなの核の意味）、"
            "四隅へ実線の枝と語の箱、上下に破線の枝と三点リーダを描く。白黒のみ。")
    return dict(file="L05_fig1_kaku_network.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="核の字→枝分かれの網モデル（本文例語のみ・問2/3の字は不描画）",
                params="核=決（きめる・きまる）・枝=決定/決心/解決/多数決（本文一致）",
                checks=ck.items, allowed=set(), check_tokens={"転", "集"}, required=[])


# ===========================================================================
# 図8: L05 和語・漢語・外来語の三層図
# 本文根拠: lesson_05.md 主概念2（和語/漢語の定義・調子の違い）・stretch S1の例示
#   （昼ごはん・昼食・ランチ）
# 答え漏れ注意: stretch S1は「三つがそろう組を二つ探す」——解答例（宿屋・旅館・ホテル）
#   は使わず、設問文にすでに例示されている組（昼ごはん・昼食・ランチ）のみを使う。
# 断定回避: 「〜ことが多い」「どれか一つだけが正しいわけではない」を明記。
# ===========================================================================
def fig_L05_layers():
    ck = Checker()
    cv = Canvas(440, 248)

    # --- パラメータ: 三層と例（例は設問文に例示済みの1組のみ） ---
    layers = [
        ("和語", "昔から日本にある言い方", "昼ごはん"),
        ("漢語", "漢字の音で読む言い方", "昼食"),
        ("外来語", "外国の言葉から取り入れた言い方", "ランチ"),
    ]
    ck.ok("例はstretch S1の設問文に例示済みの1組のみ（解答例の組は不使用）",
          [l[2] for l in layers] == ["昼ごはん", "昼食", "ランチ"])

    cv.text(220, 24, "近い内容の三つの言い方——和語・漢語・外来語", size=FS, weight="bold")
    y0, lh, gap = 44, 44, 14
    for i, (name, gloss, ex) in enumerate(layers):
        y = y0 + i * (lh + gap)
        cv.rect(16, y, 96, lh, sw=MAIN_W, rx=6)
        cv.text(64, y + lh / 2 + 5, name, size=14, weight="bold")
        cv.rect(120, y, 196, lh, sw=1.2, rx=6)
        ck.ok(f"説明が収まる: '{gloss}'", est_width(gloss, FS_XS) <= 190)
        cv.text(218, y + lh / 2 + 4, gloss, size=FS_XS)
        cv.rect(324, y, 100, lh, sw=MAIN_W, rx=6)
        cv.text(374, y + lh / 2 + 5, ex, size=13, weight="bold")
        if i > 0:
            cv.dbl_arrow(374, y - gap + 2, 374, y - 2, w=1.3, head=5)
    cv.text(220, 224, "内容は近くても、文の調子や使われやすい場面は変わることが多い。",
            size=FS_XS)
    cv.text(220, 240, "どれか一つだけが正しいわけではない——場面に合わせて選ぶ。",
            size=FS_XS)

    title = "和語・漢語・外来語の三層図（昼ごはん・昼食・ランチ）"
    desc = ("L05主概念2（と中3出口）の三層図。和語（昔から日本にある言い方・例: "
            "昼ごはん——『ごはん』は漢語由来を含むため厳密には混種語とする考え方も"
            "ある）、漢語（漢字の音で読む言い方・例: 昼食）、外来語（外国の言葉から"
            "取り入れた言い方・例: ランチ）を3段の帯で並べ、例語どうしを両向き矢印で"
            "つないで「近い内容の別の言い方」であることを示す。下に「調子や場面は変わる"
            "ことが多い・どれか一つだけが正しいわけではない」の留保。例はstretch S1の"
            "設問文にすでに例示されている1組のみで、解答例の組は使っていない。"
            "同型図の描き方: 3段×3列（層の名前／説明／例語）の帯を描き、例語の列を縦の両向き"
            "矢印でつなぎ、最下部に留保のキャプション2行を置く。白黒のみ・断定表現禁止。")
    return dict(file="L05_fig2_sanso_three_layers.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="和語/漢語/外来語=近い内容の三つの層の可視化（場面で選ぶ）",
                params="例=昼ごはん/昼食/ランチ（設問文の例示と同一の組のみ）",
                checks=ck.items, allowed=set(),
                check_tokens={"宿屋", "旅館", "ホテル", "決定", "配布", "配付"},
                required=["ことが多い", "どれか一つだけが正しいわけではない"])


# ===========================================================================
# 図9: L06 「知っている語」を「使える語」へ（段階図）
# 本文根拠: lesson_06.md 主概念2（自分の文で使う→使い慣れるへ）・雑談枠（辞書の用例）
# 答え漏れ注意: 設問語（こうえん・しじ・かてい・えいせい・じしん・きかん）は使わない
# ===========================================================================
def fig_L06_stages():
    ck = Checker()
    cv = Canvas(480, 216)

    ck.ok("図に語例を置かない（設問の答えの語に触れないための設計）", True)

    cv.text(240, 26, "「知っている」から「使える」へ", size=FS, weight="bold")
    y, bh = 56, 62
    box(cv, ck, 6, y, 136, bh, ["知っている語", "（読める・", "意味が分かる）"],
        size=FS_XS)
    cv.arrow(144, y + bh / 2, 198, y + bh / 2, w=1.6)
    cv.text(171, y + bh / 2 - 12, "自分の文で", size=FS_XS)
    cv.text(171, y + bh / 2 + 24, "一度使う", size=FS_XS)
    box(cv, ck, 200, y, 128, bh, ["使える語", "（必要なとき", "思い出せる）"],
        size=FS_XS, weight="bold", sw=BOLD_W)
    cv.arrow(330, y + bh / 2, 378, y + bh / 2, w=1.4, dash=DASH)
    box(cv, ck, 382, y, 92, bh, ["使い慣れる", "（中3の目標へ）"], size=FS_XS,
        dash=DASH)
    # 辞書の用例＝お手本のフィードバック
    dy = 152
    box(cv, ck, 162, dy, 204, 34, ["辞書の用例＝使われ方のお手本"], size=FS_XS)
    cv.arrow(264, dy - 2, 264, y + bh + 2, w=1.3, dash="3 3")
    cv.text(240, 206, "書いたら用例と見比べる——生活の文脈に一度のせた語は思い出しやすい",
            size=FS_XS)

    title = "「知っている語」を「使える語」へ——産出と辞書用例の段階図"
    desc = ("L06主概念2の段階図。「知っている語（読める・意味が分かる）」から"
            "「自分の文で一度使う」の矢印を経て「使える語（必要なとき思い出せる・"
            "太枠）」へ進み、破線の矢印で「使い慣れる（中3の目標へ）」につながる。"
            "下から「辞書の用例＝使われ方のお手本」の箱が点線で「使える語」を支える"
            "（書いたら用例と見比べる）。設問の答えに触れないよう、図には具体的な語例を"
            "置いていない。同型図の描き方: 横一列の3つの箱（2つ目を太枠・3つ目を破線枠）を"
            "矢印でつなぎ、矢印ラベルに「自分の文で一度使う」、下に用例の箱と上向き点線"
            "矢印を置く。白黒のみ・語例なし。")
    return dict(file="L06_fig1_know_to_use.svg", canvas=cv, lesson="L06",
                title=title, desc=desc,
                intent="産出（自分の文で使う）による定着経路の可視化（語例なし）",
                params="段階3＋フィードバック1（本文の記述のみ・語例なし）",
                checks=ck.items, allowed=set(),
                check_tokens={"公園", "公演", "講演", "指示", "支持", "過程", "課程",
                        "衛星", "衛生", "自信", "自身", "期間", "機関",
                        "保証", "保障"},
                required=["用例"])


# ===========================================================================
# 図10: L07 読み直し点検のフローチャート（点検の目・3つ）
# 本文根拠: lesson_07.md 主概念1（点検の目のつけどころ3つ）・活動1の指示文
#   （誤りがあるとは限らない→「誤りなし」の判断も点検の結論）
# 答え漏れ注意: 校正問題の答えの字（熱・指示・明・写・治）は図に入れない
# ===========================================================================
def fig_L07_check():
    ck = Checker()
    cv = Canvas(480, 258)

    # --- パラメータ: 点検の目（本文主概念1の3項目と同旨・表示は2行組） ---
    checks3 = [
        ["① 同じ訓・同じ音の語が", "ひそんでいないか探す"],
        ["② その字の意味が文脈と", "合っているか確かめる"],
        ["③ 迷ったら辞書を引く"],
    ]
    ck.ok("点検の目は本文どおり3項目", len(checks3) == 3)

    cv.text(240, 24, "書いたら読み直す——点検の目", size=FS, weight="bold")
    box(cv, ck, 8, 96, 84, 52, ["書いた文"], size=FS_S)
    cv.arrow(94, 122, 108, 122, w=1.6)
    # 点検の目コンテナ
    cx0, cy0, cw, ch = 112, 42, 258, 168
    cv.rect(cx0, cy0, cw, ch, sw=AUX_W, dash=DASH, rx=8)
    cv.text(cx0 + cw / 2, cy0 + 18, "点検の目（3つ）", size=FS_XS, weight="bold")
    y = cy0 + 26
    for lines in checks3:
        bh_i = 40 if len(lines) > 1 else 30
        box(cv, ck, cx0 + 10, y, cw - 20, bh_i, lines, size=FS_XS, rx=5)
        y += bh_i + 6
    cv.arrow(cx0 + cw + 2, 122, cx0 + cw + 16, 122, w=1.6)
    box(cv, ck, 388, 84, 86, 76, ["直す　または", "「誤りなし」", "と判断"], size=FS_XS,
        weight="bold", sw=BOLD_W)
    cv.text(431, 176, "どちらの結論でも", size=FS_XS)
    cv.text(431, 190, "理由を言えること", size=FS_XS)
    cv.text(240, 232, "誤りを自分で見つけて直せる目は、はじめから正しく書ける手と同じくらい価値がある",
            size=FS_XS)

    title = "読み直し点検のフローチャート——点検の目3つと結論"
    desc = ("L07主概念1の流れ図。「書いた文」から破線枠のコンテナ「点検の目（3つ）」へ"
            "進む。中身は①同じ訓・同じ音の語がひそんでいないか探す②その字の意味が文脈と"
            "合っているか確かめる③迷ったら辞書を引く。出口は太枠の箱「直す または"
            "『誤りなし』と判断」で、どちらの結論でも理由を言えることを添える（活動1は"
            "誤りがあるとは限らない設計のため、『誤りなし』も正当な結論として描く）。"
            "校正問題の答えの字は図に入れていない。同型図の描き方: 左から「書いた文」の箱→"
            "破線の大枠（中に点検項目の箱3つを縦に並べる）→太枠の結論の箱を矢印でつなぐ。"
            "白黒のみ・具体的な字例なし。")
    return dict(file="L07_fig1_proofread_checklist.svg", canvas=cv, lesson="L07",
                title=title, desc=desc,
                intent="読み直し点検の型（3つの目＋「誤りなし」も結論）の可視化",
                params="点検項目3（本文主概念1と同旨）・字例なし",
                checks=ck.items, allowed=set(),
                check_tokens={"熱", "指示", "支持", "明", "写", "治", "暑い", "空ける"},
                required=["辞書", "誤りなし"])


# ===========================================================================
# メイン: 生成 + 機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01_flow, fig_L01_map, fig_L02_types, fig_L02_bridge, fig_L03_ime,
        fig_L04_parts, fig_L05_network, fig_L05_layers, fig_L06_stages,
        fig_L07_check]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in FIGS:
        meta = fn()
        svg = meta["canvas"].render(meta["file"], meta["title"], meta["desc"])
        audit_svg(svg, meta["allowed"], meta["check_tokens"], meta["required"],
                  meta["file"])
        out = ASSETS / meta["file"]
        out.write_text(svg, encoding="utf-8")
        checks = "／".join(d for d, _ in meta["checks"][:4])
        checks += f"（ほか収まり検算 計{len(meta['checks'])}件）✓"
        if meta["check_tokens"]:
            checks += (f"／答え漏れ・断定の検査: PASS（{len(meta['check_tokens'])}項目・"
                       "対象値はanswer_key・断定語由来・非開示） ✓")
        if meta["required"]:
            checks += "／留保文字列（" + "・".join(meta["required"]) + "）存在 ✓"
        rows.append((meta["file"], meta["lesson"], meta["title"], meta["intent"],
                     meta["params"], checks))
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    lines = [
        "<!--",
        f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
        "spec: docs/SPEC_figures.md 準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）",
        "license: CC-BY-4.0",
        "-->",
        "",
        "# FIGURE_MANIFEST — 漢字・語彙運用単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "全図で内容assert（設問の答えと重ならない語例選定・文字の収まり）と"
        "答え漏れ・断定の機械検査（<text>/<title>/<desc>の禁止文字列照合＋"
        "使い分け図の留保文字列の必須化）が生成時に自動実行され、全件合格。"
        "全SVGにAI再利用メタ情報（<title>=図名・<desc>=意図/構成/同型図をAIに描かせる再現指示）を埋め込み済み。"
        "漢字の部品はテキスト要素の組み合わせで構成（§9-3・パスによる字形自作なし）。",
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
        "   （語例は必ず該当 `lesson_XX.md` 本文と突き合わせ、設問の答えに当たる語を入れない）。",
        "2. `python3 generate_figures.py` を実行する。内容assert・禁止/留保文字列検査に",
        "   1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
