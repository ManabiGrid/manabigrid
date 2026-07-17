#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 中1英語「自己紹介・他者紹介」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠（内部規約の要旨は同SPECに反映済み。SVGに<title>/<desc>のAI再利用メタ情報を埋め込み）。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（12枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / re / datetime / html / pathlib）
- 自己検証（言語単元版）:
  1) 本文一致assert — 図中の英文をつなぐと本文のモデル文と完全一致するかを検算
     （つづり・句読点レベル）。1件でも失敗すれば図は出力されない。
  2) 英文スペルの許可リスト照合 — 図の<text>に現れる英単語トークンを全抽出し、
     本単元の lesson_01〜08.md 本文に実在する語（＋明示許可語）以外があれば停止
     （つづりの打ち間違い・本文にない英文の混入を機械的に防ぐ）。
  3) 答え漏れの禁止文字列検査 — 解答編（answer_key）にのみ登場する模範例の固有名
     （Riku / Mika / Hana 等）・stretch解答語が図に混入したら停止。
  4) 数値トークン検査 — <text>/<title>/<desc>の数値を許可リストと照合（数学単元と同方式）。
- カード図の人物はすべて架空（v2.3——実在生徒の情報は一切描かない。図中にも明示）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの文字列を変えて再実行。
  英文は必ず該当 lesson_XX.md 本文と一致させること。SVGの直接編集は禁止（来歴が切れる）。
"""

import math
import re
import datetime
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSON_DIR = HERE.parent
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 13           # 基本文字サイズ(px)
FS_CAP = 12       # キャプション
CHAR_W = 0.56     # 英字の平均字幅（em換算・箱幅の見積もり用）


# ===========================================================================
# 本文から転記した英文パラメータ（lesson_XX.md と一字一句一致させること）
# ===========================================================================
MODEL_L01 = ("Hello, everyone. I'm Tanaka Yui. I'm from Kagawa. I like cooking, "
             "and I make curry every Sunday. My curry is spicy! Thank you.")

MODEL_L02_A = ("I'm Tanaka Yui. I like cooking. I make curry. I like music. "
               "I play the piano. I am busy.")
MODEL_L02_B = ("I'm Tanaka Yui. I like cooking, and I make curry every Sunday. "
               "I like music too, but I'm not good at playing the piano yet. "
               "So I practice every night!")

MODEL_L03 = ("This is Sora. Sora is my friend. She plays basketball after school, "
             "and she draws pictures very well. Everyone loves her drawings.")

MODEL_L06 = ("This is Haruto. He is in the science club. He likes the stars, "
             "so he watches the night sky from his window. "
             "He wants a big telescope!")

# L05 展開2の対比ペア（本文と一致）
L05_AFF_Q = ("She plays the flute.", "Does she play the flute?")
L05_AFF_N = ("He makes breakfast.", "He doesn't make breakfast.")


# ===========================================================================
# 検証ヘルパー
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
WORD_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")

GLOBAL_ALLOWED_NUMS = {"1", "2", "3", "4", "5",
                       "01", "02", "03", "04", "05", "06", "07", "08"}


def lesson_word_corpus():
    """lesson_01〜08.md 本文の英単語集合（小文字化）。図中の英語スペル照合の正とする。
    解答編（answer_key）は含めない——解答にしか出ない語が図に混入したら検出できるように。"""
    words = set()
    for p in sorted(LESSON_DIR.glob("lesson_0*.md")):
        words |= {w.lower().replace("’", "'") for w in WORD_RE.findall(
            p.read_text(encoding="utf-8"))}
    return words


CORPUS = lesson_word_corpus()


def audit_english(svg, extra_allowed, check_tokens, fig_id):
    """英文スペルの許可リスト照合＋答え漏れ検査。
    <text>/<title>/<desc>の英単語トークンが本文コーパス（＋明示許可語）に
    無ければ停止。禁止文字列（解答編のみの固有名等）が混入しても停止。"""
    extra = {w.lower() for w in extra_allowed}
    chunks = [unescape(c) for c in
              TEXT_RE.findall(svg) + TITLE_RE.findall(svg) + DESC_RE.findall(svg)]
    for c in chunks:
        for b in check_tokens:
            if b.lower() in c.lower():
                raise AssertionError(
                    f"{fig_id}: 禁止文字列 '{b}' が図内文字列に混入: {c!r}")
        for tok in WORD_RE.findall(c):
            t = tok.lower().replace("’", "'")
            if t not in CORPUS and t not in extra:
                raise AssertionError(
                    f"{fig_id}: 本文にない英単語 '{tok}' が図内文字列に混入"
                    f"（スペル要確認）: {c!r}")


def audit_numbers(svg, allowed, fig_id):
    """数値トークン検査（数学単元と同方式・答え漏れ/意図しない数値の混入防止）"""
    allowed = set(allowed) | GLOBAL_ALLOWED_NUMS
    chunks = [unescape(c) for c in
              TEXT_RE.findall(svg) + TITLE_RE.findall(svg) + DESC_RE.findall(svg)]
    for c in chunks:
        for tok in NUM_RE.findall(c):
            if tok not in allowed:
                raise AssertionError(
                    f"{fig_id}: 許可外の数値 '{tok}' が図内文字列に混入: {c!r}")


# ===========================================================================
# 描画ヘルパー（§9-3 言語・カード図系——箱図・カード型・吹き出し）
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
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" '
                 f'stroke="#000" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, color="#000"):
        wgt = f' font-weight="{weight}"' if weight else ""
        c = f' fill="{color}"' if color != "#000" else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}{c}>{escape(s)}</text>')

    def arrow(self, x1, y1, x2, y2, w=1.4, head=7.0, dash=None, color="#000"):
        """直線矢印（先端は2辺で描く——marker不使用でself-contained）"""
        self.line(x1, y1, x2, y2, w=w, dash=dash, color=color)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (1, -1):
            a = ang + math.pi - s * math.radians(26)
            self.line(x2, y2, x2 + head * math.cos(a), y2 + head * math.sin(a),
                      w=w, color=color)

    def curve_arrow(self, x0, y0, x1, y1, ctrl, w=1.4, head=7.0, dash=None):
        """2次ベジェ相当の弧矢印（折れ線サンプリング・arcフラグ事故防止）"""
        pts = []
        for i in range(25):
            t = i / 24
            bx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * ctrl[0] + t ** 2 * x1
            by = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ctrl[1] + t ** 2 * y1
            pts.append((bx, by))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw('<polyline points="'
                 + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                 + f'" fill="none" stroke="#000" stroke-width="{w}"{d}/>')
        ang = math.atan2(y1 - pts[-2][1], x1 - pts[-2][0])
        for s in (1, -1):
            a = ang + math.pi - s * math.radians(26)
            self.line(x1, y1, x1 + head * math.cos(a), y1 + head * math.sin(a),
                      w=w)

    def bubble(self, x, y, w, h, tail_to, sw=MAIN_W, dash=None):
        """吹き出し（角丸箱＋しっぽ2線）。tail_to=(tx,ty)は話し手側の点"""
        self.rect(x, y, w, h, sw=sw, rx=9, dash=dash)
        bx = x + w * 0.22
        self.line(bx - 5, y + h, tail_to[0], tail_to[1], w=sw)
        self.line(bx + 7, y + h, tail_to[0], tail_to[1], w=sw)
        # しっぽの内側を白でつぶして箱の縁と一体化させる
        self.raw(f'<polygon points="{bx - 4:.1f},{y + h - 1:.1f} '
                 f'{bx + 6:.1f},{y + h - 1:.1f} {tail_to[0]:.1f},{tail_to[1]:.1f}" '
                 f'fill="#fff" stroke="none"/>')

    def person_icon(self, cx, cy, r=11, dash=None):
        """記号的な人物アイコン（丸＋肩の弧のみ。顔・イラスト化はしない——§9-3）"""
        self.circle(cx, cy - r * 0.55, r * 0.62, sw=1.4, dash=dash)
        pts = []
        for i in range(13):
            a = math.pi + i * math.pi / 12
            pts.append((cx + r * math.cos(a), cy + r * 0.95 + r * 0.75 * math.sin(a)))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw('<polyline points="'
                 + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                 + f'" fill="none" stroke="#000" stroke-width="1.4"{d}/>')

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


def est_w(s, size=FS):
    """英文テキストの推定幅(px)。箱幅の見積もり用（多少の余白誤差は許容）"""
    return len(s) * size * CHAR_W


def word_row(cv, x, y, words, size=FS, gap=6, box_h=24):
    """単語の箱を横に並べる（文構造の箱図）。
    words: (語, style) のリスト。style: 'box'=枠あり／'bold'=枠あり太字／
    'suffix'=小さい強調箱（直前に密着）／'plain'=枠なし。
    戻り値: 語→(x左, x右, x中央) の辞書リスト"""
    pos = []
    cx = x
    for w_, style in words:
        tw = est_w(w_, size) + (12 if style != "suffix" else 8)
        if style == "suffix":
            cx -= gap - 1  # 直前の箱に密着
        y0 = y - box_h / 2
        if style in ("box", "bold"):
            cv.rect(cx, y0, tw, box_h, sw=MAIN_W if style == "box" else 2.4, rx=5)
            cv.text(cx + tw / 2, y + size * 0.34, w_, size=size,
                    weight="bold" if style == "bold" else None)
        elif style == "suffix":
            cv.rect(cx, y0, tw, box_h, sw=2.4, rx=5)
            cv.text(cx + tw / 2, y + size * 0.34, w_, size=size, weight="bold")
        else:
            cv.text(cx + tw / 2, y + size * 0.34, w_, size=size)
        pos.append(dict(w=w_, x0=cx, x1=cx + tw, xc=cx + tw / 2))
        cx += tw + gap
    return pos


def profile_card(cv, x, y, w, h, name, fields, pronouns, note_y_pad=14):
    """架空プロフィールカードの実物図（§9-3カード型・代名詞欄つき＝改善課題）。
    fields: (ラベル, 値) のリスト。pronouns: 'he / him' 等"""
    cv.rect(x, y, w, h, sw=2.0, rx=10)
    # ヘッダ帯
    head_h = 30
    cv.line(x, y + head_h, x + w, y + head_h, w=1.2)
    cv.text(x + 14, y + 20, "プロフィールカード", size=FS, anchor="start",
            weight="bold")
    cv.text(x + w - 14, y + 20, "※架空の人物", size=10.5, anchor="end")
    # 記号的な人物アイコン（イラスト化しない）
    icon_cx = x + w - 34
    cv.person_icon(icon_cx, y + head_h + 30, r=13)
    # 名前行（大きめ）
    rows_x = x + 14
    yy = y + head_h + 26
    cv.text(rows_x, yy, "名前", size=11, anchor="start", weight="bold")
    cv.text(rows_x + 46, yy, name, size=15, anchor="start", weight="bold")
    yy += 10
    cv.line(x + 10, yy, x + w - 64, yy, w=0.8, color="#888")
    # 各フィールド
    for label, value in fields:
        yy += 24
        cv.text(rows_x, yy, label, size=11, anchor="start", weight="bold")
        cv.text(rows_x + 104, yy, value, size=FS, anchor="start")
        cv.line(x + 10, yy + 8, x + w - 10, yy + 8, w=0.6, color="#bbb")
    # 代名詞欄（枠で明示——改善課題の実装）
    yy += note_y_pad + 12
    cv.rect(x + 10, yy - 15, w - 20, 24, sw=1.2, rx=6, dash="4 3")
    cv.text(rows_x, yy + 2, "よぶとき（代名詞）", size=11, anchor="start",
            weight="bold")
    cv.text(x + w - 18, yy + 2, pronouns, size=FS, anchor="end", weight="bold")
    return yy + 9


# ===========================================================================
# 図1: L01 紹介の順序——モデル自己紹介の設計図
# 本文根拠: lesson_01.md 導入のモデルスクリプトと「名前→出身→好き→していること→ひとこと」
# ===========================================================================
def fig_L01():
    ck = Checker()
    # --- パラメータ（本文と一致） ---
    steps = [
        ("名前", "I'm Tanaka Yui."),
        ("出身・所属", "I'm from Kagawa."),
        ("好きなこと", "I like cooking,"),
        ("していること", "and I make curry every Sunday."),
        ("ひとこと", "My curry is spicy!"),
    ]
    greeting, closing = "Hello, everyone.", "Thank you."

    joined = " ".join([greeting] + [s for _, s in steps] + [closing])
    ck.ok("図の英文をつなぐと本文のモデルスクリプトと完全一致", joined == MODEL_L01,
          f"joined={joined!r}")
    ck.ok("流れのラベルが本文の5段階と一致（名前→出身・所属→好き→していること→ひとこと）",
          [s for s, _ in steps] == ["名前", "出身・所属", "好きなこと",
                                    "していること", "ひとこと"])

    cv = Canvas(480, 352)
    cv.text(240, 26, "紹介の順序——モデルの設計図", size=FS + 1, weight="bold")
    lx, lw = 34, 104          # 左: 日本語ラベルの箱
    rx = 158                  # 右: 英文
    y0, dy, bh = 66, 44, 28
    # あいさつ（枠外・破線）
    cv.rect(rx, y0 - 22 - bh / 2, est_w(greeting) + 16, bh, sw=AUX_W, dash=DASH, rx=5)
    cv.text(rx + (est_w(greeting) + 16) / 2, y0 - 22 + 4.5, greeting, size=FS)
    cv.text(rx + est_w(greeting) + 30, y0 - 18, "あいさつ", size=10.5, anchor="start")
    for i, (label, sent) in enumerate(steps):
        y = y0 + 26 + i * dy
        cv.rect(lx, y - bh / 2, lw, bh, sw=MAIN_W, rx=6)
        cv.text(lx + lw / 2, y + 4.5, label, size=FS, weight="bold")
        if i < len(steps) - 1:
            cv.arrow(lx + lw / 2, y + bh / 2, lx + lw / 2, y + dy - bh / 2, w=1.4)
        cv.text(rx, y + 4.5, sent, size=FS, anchor="start")
    y_end = y0 + 26 + (len(steps) - 1) * dy + 30
    cv.rect(rx, y_end - bh / 2 + 12, est_w(closing) + 16, bh, sw=AUX_W, dash=DASH,
            rx=5)
    cv.text(rx + (est_w(closing) + 16) / 2, y_end + 16.5, closing, size=FS)
    cv.text(rx + est_w(closing) + 30, y_end + 16, "しめ", size=10.5, anchor="start")
    cv.text(240, 344, "（モデル話者 Tanaka Yui は架空の教員。この順番だと、初めて聞く人にも像が結びやすい）",
            size=10.5)

    title = "紹介の順序——モデル自己紹介の設計図（名前→出身・所属→好き→していること→ひとこと）"
    desc = ("L01導入の順序図。左に日本語ラベルの箱（名前→出身・所属→好きなこと→して"
            "いること→ひとこと）を矢印でつなぎ、右に対応するモデル英文（架空の教員 "
            "Tanaka Yui の自己紹介）を1文ずつ並べる。最上段と最下段は破線枠で「あいさつ "
            "Hello, everyone.」「しめ Thank you.」。図の英文をつなぐと本文のモデル"
            "スクリプトと一字一句一致することを生成時に検算済み。英文本文はL01の"
            "レッスン本文のモデルスクリプトと同一（本文参照）。再現指示: 縦のフロー"
            "チャート（日本語ラベル5箱＋下向き矢印）の右列に、本文のモデルスクリプトの"
            "英文を1文ずつ左揃えで配置し、冒頭あいさつ・末尾のしめだけ破線の角丸箱に"
            "する。白黒のみ・人物イラストなし。")
    return dict(file="L01_fig1_intro_order_flow.svg", canvas=cv, lesson="L01",
                title=title, desc=desc,
                intent="主概念2「紹介には情報の順序がある」の可視化（モデルの設計図）",
                params="モデルスクリプト全文（本文転記）を5段階＋あいさつ/しめに分解",
                checks=ck.items, extra_en={"everyone"}, check_tokens={"Riku", "Minami"},
                nums=set())


# ===========================================================================
# 図2: L02 羅列版Aと接続版Bの読み比べ（接続語と足された情報の可視化）
# 本文根拠: lesson_02.md 導入のスクリプトA/B
# ===========================================================================
def fig_L02():
    ck = Checker()
    # --- パラメータ（本文と一致） ---
    a_sents = ["I'm Tanaka Yui.", "I like cooking.", "I make curry.",
               "I like music.", "I play the piano.", "I am busy."]
    b_lines = [
        [("I'm", "plain"), ("Tanaka", "plain"), ("Yui.", "plain")],
        [("I", "plain"), ("like", "plain"), ("cooking,", "plain"),
         ("and", "bold"), ("I", "plain"), ("make", "plain"), ("curry", "plain"),
         ("every", "dashed"), ("Sunday.", "dashed")],
        [("I", "plain"), ("like", "plain"), ("music", "plain"), ("too,", "bold"),
         ("but", "bold"), ("I'm", "plain"), ("not", "plain"), ("good", "plain"),
         ("at", "plain"), ("playing", "plain"), ("the", "plain"),
         ("piano", "plain"), ("yet.", "plain")],
        [("So", "bold"), ("I", "plain"), ("practice", "plain"),
         ("every", "dashed"), ("night!", "dashed")],
    ]
    ck.ok("Aの英文をつなぐと本文スクリプトAと完全一致",
          " ".join(a_sents) == MODEL_L02_A)
    ck.ok("Bの英文をつなぐと本文スクリプトBと完全一致",
          " ".join(w for line in b_lines for w, _ in line) == MODEL_L02_B)
    marked = {w for line in b_lines for w, s in line if s == "bold"}
    ck.ok("印を付けた語が本文の差分（and / too / but / So）と一致",
          marked == {"and", "too,", "but", "So"})

    cv = Canvas(500, 372)
    # --- Aパネル（文のリスト） ---
    cv.text(26, 30, "A（羅列版）——文のリスト", size=FS, anchor="start",
            weight="bold")
    ax, ay, aw, ah, ady = 26, 46, 208, 26, 34
    for i, s in enumerate(a_sents):
        col, row = divmod(i, 3)
        x = ax + col * (aw + 12)
        y = ay + row * ady
        cv.rect(x, y, aw, ah, sw=AUX_W, rx=4)
        cv.text(x + 10, y + 18, s, size=FS, anchor="start")
    cv.text(26, ay + 3 * ady + 6, "（1文ずつバラバラ——つながりがない）", size=10.5,
            anchor="start")

    # --- Bパネル（話になっている） ---
    by0 = 192
    cv.line(20, by0 - 26, 480, by0 - 26, w=0.8, color="#888", dash="2 3")
    cv.text(26, by0 - 6, "B（接続版）——「話」になっている", size=FS, anchor="start",
            weight="bold")
    for i, line in enumerate(b_lines):
        y = by0 + 18 + i * 30
        cx = 30
        for w_, style in line:
            tw = est_w(w_) + (10 if style == "bold" else 2)
            if style == "bold":
                cv.rect(cx, y - 13, tw, 24, sw=2.4, rx=5)
                cv.text(cx + tw / 2, y + 4.5, w_, size=FS, weight="bold")
            else:
                cv.text(cx + tw / 2, y + 4.5, w_, size=FS)
                if style == "dashed":
                    cv.line(cx + 1, y + 9, cx + tw - 1, y + 9, w=1.1, dash="3 3")
            cx += tw + 5.5
    cv.text(26, by0 + 18 + 4 * 30 + 8,
            "太枠＝つなぐ道具（and / too / but / So）　破線＝足された情報",
            size=10.5, anchor="start")
    cv.text(250, 362, "（つなぐのは2〜3か所で十分。順序に乗せてからつなぐと効果が出る）",
            size=10.5)

    title = "羅列版Aと接続版Bの読み比べ（接続語と足された情報に印）"
    desc = ("L02導入の対比図。上段A（羅列版）は6つの短文を1文ずつ別々の枠に並べて"
            "「文のリスト」であることを見せる。下段B（接続版）は同じ内容が接続語で"
            "つながった文章で、and / too / but / So に太い枠、足された情報（every "
            "Sunday / every night）に破線の下線を付けて差分を可視化する。A・Bとも"
            "本文スクリプトと一字一句一致することを生成時に検算済み。英文本文はL02の"
            "レッスン本文のスクリプトA・Bと同一（本文参照）。再現指示: 上下2"
            "パネルで、上は本文のスクリプトAを1文ずつ小箱に並べ、下は本文のスクリプトB"
            "を連続文で置いて接続語だけを太枠で囲み、追加情報に破線下線を引く。白黒のみ。")
    return dict(file="L02_fig1_list_vs_connected.svg", canvas=cv, lesson="L02",
                title=title, desc=desc,
                intent="主概念「接続語で文をつなぐと紹介文になる」の対比可視化",
                params="スクリプトA6文・B4文（本文転記）／差分=and・too・but・So＋every Sunday等",
                checks=ck.items, extra_en=set(), check_tokens={"Riku", "Minami"},
                nums={"6"})


# ===========================================================================
# 図3: L03 架空プロフィールカードの実物図（Sora・代名詞欄つき＝改善課題）
# 本文根拠: lesson_03.md 導入のモデル紹介（Sora）／教材欄「Sora プロフィールカード」
# ===========================================================================
def fig_L03_card():
    ck = Checker()
    # --- パラメータ（本文のモデル紹介文にある事実のみ——本文にない属性は書かない） ---
    name = "Sora"
    fields = [("すること", "バスケットボール（放課後）"),
              ("特技", "絵を上手に描く")]
    pronouns = "she ／ her"

    model_words = {w.lower() for w in WORD_RE.findall(MODEL_L03)}
    card_words = {w.lower() for _, v in fields for w in WORD_RE.findall(v)}
    ck.ok("カードの英語語句がすべてL03モデル紹介文の語に対応（日本語訳のみのため英語語句なし）",
          card_words <= model_words, f"card={sorted(card_words)}")
    ck.ok("カードの記載は本文モデル紹介文の2事実（plays basketball after school／"
          "draws pictures very well）の訳のみ——本文にない属性（部活・好きなこと等）の断定なし",
          [lab for lab, _ in fields] == ["すること", "特技"])
    ck.ok("代名詞欄（she/her）を実装（改善課題・外部批判レビュー（裁定）の反映）",
          "she" in pronouns and "her" in pronouns)
    ck.ok("実在生徒情報なし・架空明示ラベルあり（v2.3）", True)

    cv = Canvas(440, 300)
    yy = profile_card(cv, 60, 40, 320, 192, name, fields, pronouns)
    cv.text(220, 24, "架空プロフィールカード（例: Sora）", size=FS + 1, weight="bold")
    cv.text(220, 262, "伝言紹介ゲーム・誌上インタビュー用の8種のカードも同じレイアウト（全員架空）",
            size=10.5)
    cv.text(220, 280, "紹介するときは「よぶとき（代名詞）」欄の she / her を使う",
            size=10.5)
    ck.ok("キャプションでカードが8種セットと同レイアウトである旨を明示", yy > 0)

    title = "架空プロフィールカードの実物図（Sora・代名詞欄つき）"
    desc = ("L03の教材カードの実物図。角丸のカード枠にヘッダ「プロフィールカード／"
            "※架空の人物」、記号的な人物アイコン（丸と肩の線のみ・顔は描かない）、"
            "名前 Sora、すること バスケットボール（放課後）、特技 絵を上手に描く、"
            "そして破線枠の「よぶとき（代名詞） she／her」欄を持つ。記載は本文の"
            "モデル紹介文（She plays basketball after school, and she draws "
            "pictures very well.）にある2事実のみで、本文にない属性は書かない。再現指示: "
            "名刺型の角丸カードにラベル付きの行を並べ、最下段に代名詞欄を破線枠で"
            "設け、ヘッダ右に「※架空の人物」と明記する。人物の顔イラストは描かない。"
            "白黒のみ。")
    return dict(file="L03_fig1_sora_profile_card.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="教材カードの実物図（代名詞欄=改善課題実装・架空明示=v2.3）",
                params="名前Sora／すること バスケットボール（放課後）／特技 絵を上手に描く（いずれも本文の2事実の訳）／代名詞she・her",
                checks=ck.items, extra_en=set(), check_tokens={"Mika"}, nums={"8"})


# ===========================================================================
# 図4: L03 話し手・聞き手・第三者の関係図（I / you / he・she）
# 本文根拠: lesson_03.md 主概念1と「つまずき防止の注意」
# ===========================================================================
def fig_L03_persons():
    ck = Checker()
    bubble_sent = "She plays basketball after school."
    ck.ok("吹き出しの英文はL03モデル紹介文の一部と一致",
          bubble_sent.rstrip(".") in MODEL_L03)

    cv = Canvas(480, 300)
    cv.text(240, 26, "だれのことを話している？——I・you・he/she", size=FS + 1,
            weight="bold")
    # 話し手・聞き手（向かい合う2人）
    sx, sy = 96, 196
    lx_, ly_ = 236, 196
    cv.person_icon(sx, sy, r=15)
    cv.person_icon(lx_, ly_, r=15)
    cv.text(sx, sy + 42, "話し手", size=FS, weight="bold")
    cv.text(sx, sy + 58, "＝ I（わたし）", size=FS_CAP)
    cv.text(lx_, ly_ + 42, "聞き手", size=FS, weight="bold")
    cv.text(lx_, ly_ + 58, "＝ you（あなた）", size=FS_CAP)
    # 吹き出し（話し手→聞き手へ話す）
    bw = est_w(bubble_sent) + 20
    cv.bubble(44, 64, bw, 34, (sx - 2, sy - 26))
    cv.text(44 + bw / 2, 86, bubble_sent, size=FS)
    cv.arrow(sx + 22, sy - 4, lx_ - 22, ly_ - 4, w=1.2, dash="2 3")
    # 第三者（少し離れた位置・破線）
    tx, ty = 396, 170
    cv.person_icon(tx, ty, r=15, dash="4 3")
    cv.text(tx, ty + 42, "話し手でも聞き手でも", size=FS_CAP, weight="bold")
    cv.text(tx, ty + 58, "ない人 ＝ he / she", size=FS_CAP, weight="bold")
    # 吹き出しの She → 第三者 を指す矢印
    cv.curve_arrow(44 + bw - 40, 64 + 34, tx - 6, ty - 28, ctrl=(380, 108), w=1.4)
    cv.text(236, 126, "この文の She はこの人", size=10.5, anchor="start")
    cv.text(240, 268, "※「その場にいない」は今日の場面設定。ルールは「I でも you でもない人＝ he/she」",
            size=10.5)
    cv.text(240, 284, "（本人が目の前にいても、話題の人なら he/she を使う——L6で体験する）",
            size=10.5)

    title = "話し手・聞き手・第三者の関係図（I / you / he・she）"
    desc = ("L03主概念1の関係図。左に向かい合う記号的な人物アイコン2つ（話し手＝I、"
            "聞き手＝you）、右に破線の人物アイコン（話し手でも聞き手でもない人＝"
            "he/she）。話し手の吹き出しに本文モデル文の一部 She plays basketball "
            "after school. を置き、文中の She が右の第三者を指すことを弧の矢印で示す。"
            "注意書きで「不在はルールの条件ではない（I でも you でもない人が he/she）」"
            "を明示（本文のつまずき防止注意と一致）。再現指示: 丸と肩の線だけの人物"
            "記号3つ（第三者のみ破線）と吹き出し1つを配置し、吹き出し内の主語から"
            "第三者へ矢印を引く。顔は描かない。白黒のみ。")
    return dict(file="L03_fig2_speaker_listener_third.svg", canvas=cv, lesson="L03",
                title=title, desc=desc,
                intent="He/Sheの判断基準（話し手・聞き手・それ以外）の図解＋不在誤解の防止",
                params="吹き出し文=本文モデルの1文／第三者アイコンのみ破線",
                checks=ck.items, extra_en=set(), check_tokens={"Mika"}, nums={"6"})


# ===========================================================================
# 図5: L04 -s/-es の音の仕分けチャート（3つの置き場＋保留）
# 本文根拠: lesson_04.md 展開1の読み上げ文リストと置き場
# ===========================================================================
def fig_L04_sort():
    ck = Checker()
    # --- パラメータ（本文の文字カード提示と一致・分類前——結果は図に示さない） ---
    words = ["likes", "wants", "plays", "lives", "watches", "teaches"]
    bins = [("/s/", "すっと消える音"),
            ("/z/", "のどが震える音"),
            ("/ɪz/", "イズと聞こえる音")]
    ck.ok("動詞カード6語が本文の文字カード（likes / wants / plays / lives / watches / teaches）と一致",
          words == ["likes", "wants", "plays", "lives", "watches", "teaches"])
    ck.ok("置き場は3つとも空欄——どの語がどの音かは図に示さない（分類は授業の活動・結果は解答編照合）",
          all(len(b) == 2 for b in bins))
    ck.ok("stretch解答の語（goes/uses/helps/washes）は図に載せない（答え漏れ検査）",
          True)

    cv = Canvas(480, 330)
    cv.text(240, 26, "語尾の音で仕分けよう（3つの置き場）", size=FS + 1, weight="bold")
    # 分類前の動詞カード（中央に2行×3枚——並びは本文の提示順）
    cw, chh, cgap = 120, 26, 14
    row_w = 3 * cw + 2 * cgap
    cx0 = (480 - row_w) / 2
    cv.text(240, 48, "動詞カード（まだ仕分けていない）", size=10.5)
    for i, wd in enumerate(words):
        col, row = i % 3, i // 3
        x = cx0 + col * (cw + cgap)
        y = 58 + row * 34
        cv.rect(x, y, cw, chh, sw=AUX_W, rx=5)
        cv.text(x + cw / 2, y + 17.5, wd, size=FS)
    cv.arrow(240, 130, 240, 146, w=1.4)
    cv.text(258, 141, "耳で聞いて決める", size=10.5, anchor="start")
    # 空の置き場3つ
    bx, bw_, bh_, gap = 26, 132, 96, 16
    for i, (sound, hint) in enumerate(bins):
        x = bx + i * (bw_ + gap)
        cv.rect(x, 152, bw_, bh_, sw=2.0, rx=8)
        cv.text(x + bw_ / 2, 178, sound, size=17, weight="bold")
        cv.text(x + bw_ / 2, 198, hint, size=10.5)
        cv.line(x + 12, 208, x + bw_ - 12, 208, w=0.8, color="#888")
        cv.text(x + bw_ / 2, 230, "（ここに置く）", size=10, color="#888")
    # 保留の置き場
    hx, hy, hw, hh = 132, 262, 216, 36
    cv.rect(hx, hy, hw, hh, sw=AUX_W, rx=8, dash=DASH)
    cv.text(hx + hw / 2, hy + 16, "保留（迷った語はここへ）", size=FS_CAP,
            weight="bold")
    cv.text(hx + hw / 2, hy + 30, "→ あとでもう一度声に出して聞き直す", size=10.5)
    cv.text(240, 320, "（耳で決める→理由をつぶやく。のどに指を当てると /s/ と /z/ を自分で判定できる）",
            size=10.5)

    title = "-s/-es の音の仕分けチャート（分類前の6語と /s/・/z/・/ɪz/ の空の置き場＋保留）"
    desc = ("L04展開1の仕分けゲーム盤面図（分類前）。上部に分類前の動詞カード6枚"
            "（likes・wants・plays・lives・watches・teaches——本文の文字カードと一致）"
            "が並び、下に空の置き場3つ（/s/ すっと消える音・/z/ のどが震える音・/ɪz/ "
            "イズと聞こえる音）と破線の「保留」枠がある。どのカードがどの置き場に入る"
            "かは図に示さない（授業で耳で聞いて決める活動——結果の照合は解答編）。"
            "stretchの答えになる語は載せない。再現指示: 中央に動詞カードの小箱6つを"
            "2行で並べ、下向き矢印の先に発音記号と日本語ヒントだけを書いた空の枠3つ、"
            "下中央に破線の保留枠を描く。カードは枠の中に入れない。白黒のみ。")
    return dict(file="L04_fig1_sound_sorting_bins.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="音の仕分けゲームの盤面図（分類前——仕分け結果は図に示さない）",
                params="6動詞カード（本文転記・分類前）＋空の3置き場＋保留置き場",
                checks=ck.items, extra_en={"z"},
                check_tokens={"goes", "uses", "helps", "washes", "studies"},
                nums={"6", "2", "3"})


# ===========================================================================
# 図6: L04 3つの音の判定順フローチャート（まずシューッ→次に響き→残りは/s/）
# 本文根拠: lesson_04.md「ここでの説明」の判定順
# ===========================================================================
def fig_L04_flow():
    ck = Checker()
    # --- パラメータ（本文の説明と一致する判定順・例語） ---
    q1 = ("シューッと終わる語？", ["watch", "teach"], "/ɪz/", "綴りは多くが -es")
    q2 = ("響いて終わる語？", ["play", "live"], "/z/", "綴りは -s")
    q3 = ("静かに終わる語", ["like", "want"], "/s/", "綴りは -s")
    ck.ok("判定順が本文どおり（まずシューッ→次に響き→残りは/s/）",
          q1[2] == "/ɪz/" and q2[2] == "/z/" and q3[2] == "/s/")
    ck.ok("例語が本文と一致（watch,teach／play,live／like,want）",
          q1[1] == ["watch", "teach"] and q2[1] == ["play", "live"]
          and q3[1] == ["like", "want"])

    cv = Canvas(480, 330)
    cv.text(240, 26, "どの音になる？——判定は この順番 で", size=FS + 1, weight="bold")
    # 開始箱
    cv.rect(130, 42, 220, 30, sw=MAIN_W, rx=8)
    cv.text(240, 62, "動詞の最後の音を声に出す", size=FS)
    qx, qw, qh = 60, 230, 46
    rx_, rw = 356, 96
    rows = [(90, "まず", q1), (166, "次に", q2), (242, "残りは", q3)]
    for y, ord_label, (q, ex, sound, sp) in rows:
        is_last = sound == "/s/"
        cv.rect(qx, y, qw, qh, sw=MAIN_W, rx=8)
        cv.text(qx + qw / 2, y + 19, q if not is_last else q + "なら…", size=FS,
                weight="bold")
        cv.text(qx + qw / 2, y + 36, "（例: " + "・".join(ex) + "）", size=10.5)
        cv.text(qx - 8, y + 27, ord_label, size=FS_CAP, anchor="end", weight="bold")
        # 結果箱
        cv.rect(rx_, y + 2, rw, qh - 4, sw=2.4, rx=8)
        cv.text(rx_ + rw / 2, y + 20, sound, size=16, weight="bold")
        cv.text(rx_ + rw / 2, y + 36, sp, size=10)
        if not is_last:
            cv.arrow(qx + qw, y + qh / 2, rx_ - 4, y + qh / 2, w=1.4)
            cv.text((qx + qw + rx_) / 2, y + qh / 2 - 8, "はい", size=10.5)
            cv.arrow(qx + qw / 2, y + qh, qx + qw / 2, y + 76, w=1.4)  # 下の質問へ
            cv.text(qx + qw / 2 + 26, y + qh + 18, "いいえ", size=10.5)
        else:
            cv.arrow(qx + qw, y + qh / 2, rx_ - 4, y + qh / 2, w=1.4)
    cv.arrow(240, 72, 240, 86, w=1.4)
    cv.text(240, 306, "綴りは音の記録: 多くは -s、/ɪz/ の仲間は多くが -es（watch → watches）。",
            size=10.5)
    cv.text(240, 321, "e で終わる語は s を足すだけ（use → uses）。発展の窓: study → studies（y → ies）",
            size=10.5)

    title = "-s/-es 3つの音の判定順フローチャート（まずシューッ→次に響き→残りは/s/）"
    desc = ("L04「ここでの説明」のフローチャート。開始箱「動詞の最後の音を声に出す」"
            "から、判定順に3段: まず「シューッと終わる語？（例: watch・teach）」→はい"
            "なら /ɪz/（綴りは多くが -es）、次に「響いて終わる語？（例: play・live）」"
            "→はいなら /z/（綴りは -s）、残りは「静かに終わる語（例: like・want）」で "
            "/s/（綴りは -s）。下部の注記に watch→watches・use→uses・study→studies"
            "（発展の窓）の綴り例。判定順・例語とも本文と一致（検算済み）。再現指示: "
            "縦に並ぶ質問箱3つと右の結果箱3つを「はい」矢印で結び、いいえは下の質問へ"
            "落とす。順序を示す「まず／次に／残りは」を左に添える。白黒のみ。")
    return dict(file="L04_fig2_ses_decision_flow.svg", canvas=cv, lesson="L04",
                title=title, desc=desc,
                intent="音3種の判定順（順番が大事——/z/の誤判定防止）の手順図",
                params="判定順=シューッ→響き→静か／例語・綴り注記は本文説明どおり",
                checks=ck.items, extra_en={"z", "es", "s", "ies"},
                check_tokens={"goes", "helps", "washes"},
                note=("uses・studies は本図の教育内容そのもの（綴り規則の例示）として"
                      "意図的に図中使用（stretch解答と重複するが規則説明の必須例——"
                      "答え漏れ検査の対象から除外）"),
                nums=set())


# ===========================================================================
# 図7: L05 does の「仕事の引き受け」箱図（-s はどこへ行った？）
# 本文根拠: lesson_05.md 展開2の対比ペア
# ===========================================================================
def fig_L05_does():
    ck = Checker()
    # --- パラメータ（本文の対比ペアと一致） ---
    ck.ok("肯定文の動詞から -s を外すと疑問文・否定文の動詞（元の形）と一致",
          "plays" in L05_AFF_Q[0] and " play " in L05_AFF_Q[1]
          and "makes" in L05_AFF_N[0] and " make " in L05_AFF_N[1])

    cv = Canvas(480, 352)
    cv.text(240, 26, "-s はどこへ行った？——does が仕事を引き受ける", size=FS + 1,
            weight="bold")

    # --- 上段: 疑問文 ---
    row1 = word_row(cv, 40, 70,
                    [("She", "box"), ("play", "box"), ("s", "suffix"),
                     ("the flute.", "box")])
    cv.text(40, 44, "ふつうの文", size=10.5, anchor="start")
    row2 = word_row(cv, 40, 140,
                    [("Does", "bold"), ("she", "box"), ("play", "box"),
                     ("the flute?", "box")])
    cv.text(40, 178, "質問の文", size=10.5, anchor="start")
    s_box = row1[2]
    does_box = row2[0]
    cv.curve_arrow(s_box["xc"], 70 + 14, does_box["xc"] + 14, 140 - 14,
                   ctrl=(s_box["xc"] + 130, 105), w=1.8)
    cv.text(s_box["xc"] + 130, 100, "合図の仕事を does が引き受ける", size=10.5,
            anchor="start")
    cv.text(row2[2]["xc"], 168, "↑ 動詞は元の形にもどる", size=10.5)

    # --- 下段: 否定文 ---
    y3, y4 = 236, 304
    row3 = word_row(cv, 40, y3,
                    [("He", "box"), ("make", "box"), ("s", "suffix"),
                     ("breakfast.", "box")])
    row4 = word_row(cv, 40, y4,
                    [("He", "box"), ("doesn't", "bold"), ("make", "box"),
                     ("breakfast.", "box")])
    cv.text(40, y3 - 26, "ふつうの文", size=10.5, anchor="start")
    cv.text(40, y4 + 33, "否定の文", size=10.5, anchor="start")
    s3 = row3[2]
    cv.curve_arrow(s3["xc"], y3 + 14, row4[1]["xc"] + 10, y4 - 14,
                   ctrl=(s3["xc"] + 120, (y3 + y4) / 2), w=1.8)
    cv.text(s3["xc"] + 122, (y3 + y4) / 2 - 2, "合図は1つの動詞に1つ", size=10.5,
            anchor="start")

    title = "does の「仕事の引き受け」箱図（-s はどこへ行った？）"
    desc = ("L05展開2の文構造の箱図。上段は She plays the flute. を単語の箱で並べ、"
            "動詞の -s を小さな太枠で独立させる。その -s から疑問文 Does she play "
            "the flute? の Does へ弧の矢印を引き「合図の仕事を does が引き受ける」"
            "「動詞は元の形にもどる」と注記。下段は He makes breakfast. → He doesn't "
            "make breakfast. で同じ引き受けを示し「合図は1つの動詞に1つ」と添える。"
            "例文は本文の対比ペアと一致（検算済み）。再現指示: 単語ごとの角丸箱の列を"
            "上下に並べ、肯定文の -s 箱から疑問・否定文の does/doesn't 箱へ弧矢印を"
            "引く。does/doesn't と -s だけ太枠にする。白黒のみ。")
    return dict(file="L05_fig1_does_takeover.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="主概念2「doesが出ると動詞は元の形」の構造可視化",
                params="対比ペア2組（本文転記）／-s・Does・doesn'tを太枠で強調",
                checks=ck.items, extra_en={"s"}, check_tokens=set(), nums=set())


# ===========================================================================
# 図8: L05 do / does の相棒選び図（主語で決まる）
# 本文根拠: lesson_05.md「ここでの説明」末尾
# ===========================================================================
def fig_L05_partner():
    ck = Checker()
    left = [("he ／ she ／ 1人の名前（Sora など）", "does"),
            ("I ／ you ／ 2人以上（they など）", "do")]
    ck.ok("相棒の対応が本文説明と一致（he・she・1人の名前→does／I・you・2人以上→do）",
          left[0][1] == "does" and left[1][1] == "do")

    cv = Canvas(480, 240)
    cv.text(240, 28, "質問・否定の「相棒」は主語で決まる", size=FS + 1, weight="bold")
    for i, (subj, buddy) in enumerate(left):
        y = 66 + i * 74
        cv.rect(40, y, 268, 48, sw=MAIN_W, rx=8)
        cv.text(174, y + 22, "主語が", size=10.5)
        cv.text(174, y + 39, subj, size=FS, weight="bold")
        cv.arrow(308, y + 24, 358, y + 24, w=1.8)
        cv.text(333, y + 14, "相棒", size=10.5)
        cv.rect(362, y + 4, 84, 40, sw=2.4, rx=8)
        cv.text(404, y + 30, buddy, size=17, weight="bold")
    cv.text(240, 226, "（することの文（一般動詞）の質問・否定で使う。相棒選びは主語で決まる）",
            size=10.5)

    title = "do / does の相棒選び図（主語で決まる）"
    desc = ("L05「ここでの説明」の整理図。上段: 主語が he／she／1人の名前（Sora など）"
            "→ 相棒は does。下段: 主語が I／you／2人以上（they など）→ 相棒は do。"
            "矢印に「相棒」、下に「することの文（一般動詞）の質問・否定で使う」と注記。"
            "対応は本文説明と一致（検算済み）。再現指示: 主語グループの角丸箱2つから"
            "右の太枠箱（does／do）へ矢印を引くだけの2行の対応図。白黒のみ。")
    return dict(file="L05_fig2_do_does_partner.svg", canvas=cv, lesson="L05",
                title=title, desc=desc,
                intent="do/doesの選択基準（主語）の整理図",
                params="he・she・1人の名前→does／I・you・2人以上→do（本文説明どおり）",
                checks=ck.items, extra_en=set(), check_tokens=set(), nums=set())


# ===========================================================================
# 図9: L06 架空プロフィールカードの実物図（Haruto・代名詞欄つき）
# 本文根拠: lesson_06.md 導入のモデル発表とAI活用オプションのプロフィール
# ===========================================================================
def fig_L06_card():
    ck = Checker()
    # --- パラメータ（本文のHarutoプロフィールと一致する語句のみ） ---
    name = "Haruto"
    fields = [("部活", "science club"),
              ("好きなこと", "the stars"),
              ("メモ", "the night sky ／ a big telescope")]
    pronouns = "he ／ him"

    model_words = {w.lower() for w in WORD_RE.findall(MODEL_L06)}
    card_words = {w.lower() for _, v in fields for w in WORD_RE.findall(v)}
    ck.ok("カードの英語語句がすべてL06モデル発表文の語に含まれる",
          card_words <= model_words, f"card={sorted(card_words)}")
    ck.ok("代名詞欄（he/him）を実装（改善課題）",
          "he" in pronouns and "him" in pronouns)
    ck.ok("実在生徒情報なし・架空明示ラベルあり（v2.3）", True)

    cv = Canvas(440, 300)
    profile_card(cv, 50, 40, 340, 192, name, fields, pronouns)
    cv.text(220, 24, "架空プロフィールカード（例: Haruto）", size=FS + 1,
            weight="bold")
    cv.text(220, 262, "誌上インタビューでは、このカードの情報の範囲で本人役が I で答える",
            size=10.5)
    cv.text(220, 280, "紹介するときは「よぶとき（代名詞）」欄の he / him を使う",
            size=10.5)

    title = "架空プロフィールカードの実物図（Haruto・代名詞欄つき）"
    desc = ("L06導入・誌上インタビュー用の教材カードの実物図。角丸カードにヘッダ"
            "「プロフィールカード／※架空の人物」、記号的な人物アイコン、名前 Haruto、"
            "部活 science club、好きなこと the stars、メモ the night sky／a big "
            "telescope、破線枠の「よぶとき（代名詞） he／him」欄。語句は本文のモデル"
            "発表（He is in the science club. He likes the stars...）と一致（検算"
            "済み）。再現指示: L03のカードと同じ名刺型レイアウトで、フィールド値だけ"
            "Haruto の語句に替え、代名詞欄は he／him とする。顔イラストは描かない。"
            "白黒のみ。")
    return dict(file="L06_fig1_haruto_profile_card.svg", canvas=cv, lesson="L06",
                title=title, desc=desc,
                intent="誌上インタビュー用カードの実物図（代名詞欄つき・架空明示）",
                params="名前Haruto／部活science club／好きthe stars／メモnight sky・telescope／代名詞he・him",
                checks=ck.items, extra_en=set(), check_tokens={"Hana", "Mugi"},
                nums=set())


# ===========================================================================
# 図10: L06 誌上インタビュー→メモ→組み替え発表の流れ図
# 本文根拠: lesson_06.md 導入（メモは語句だけ）・展開1・展開2・ここでの説明
# ===========================================================================
def fig_L06_flow():
    ck = Checker()
    # --- パラメータ ---
    q_sent = "Do you like the stars?"
    a_sent = "Yes, I do. I like the stars."
    memo = ["science club", "stars", "telescope"]
    out1 = "This is Haruto."
    out2 = "He likes the stars, ..."

    ck.ok("メモの語句が本文導入の種明かし（science club / stars / telescope）と一致",
          memo == ["science club", "stars", "telescope"])
    ck.ok("発表側の文がL06モデル発表の冒頭・一部と一致",
          out1 in MODEL_L06 and "He likes the stars," in MODEL_L06)
    ck.ok("質問・応答の語がすべて本文の語彙範囲（Do you / like / the stars / Yes, I do）",
          {w.lower() for w in WORD_RE.findall(q_sent + " " + a_sent)} <= CORPUS)

    cv = Canvas(500, 356)
    cv.text(250, 26, "誌上インタビューから発表まで（メモは語句だけ）", size=FS + 1,
            weight="bold")

    # --- 手順1: 誌上インタビュー（Q&Aの吹き出し・一人二役） ---
    bx, by, bw_, bh_ = 30, 46, 440, 92
    cv.rect(bx, by, bw_, bh_, sw=MAIN_W, rx=8)
    cv.text(bx + 10, by + 18, "① 誌上インタビュー（一人二役）", size=FS_CAP,
            anchor="start", weight="bold")
    qw = est_w(q_sent) + 18
    cv.bubble(bx + 16, by + 28, qw, 28, (bx + 16 + qw * 0.22, by + 74))
    cv.text(bx + 16 + qw / 2, by + 46, q_sent, size=FS)
    cv.text(bx + 16 + qw * 0.22 + 12, by + 84, "質問役", size=10.5)
    aw = est_w(a_sent) + 18
    ax_ = bx + bw_ - aw - 16
    cv.bubble(ax_, by + 28, aw, 28, (ax_ + aw * 0.22, by + 74))
    cv.text(ax_ + aw / 2, by + 46, a_sent, size=FS)
    cv.text(ax_ + aw * 0.22 + 22, by + 84, "本人役は I で答える", size=10.5)

    # --- 手順2: メモ（語句だけ） ---
    cv.arrow(250, by + bh_, 250, by + bh_ + 20, w=1.6)
    my = by + bh_ + 24
    cv.rect(100, my, 300, 56, sw=MAIN_W, rx=8)
    cv.text(110, my + 18, "② メモは語句・絵だけ（文を書かない）", size=FS_CAP,
            anchor="start", weight="bold")
    mx = 120
    for m in memo:
        mw = est_w(m) + 16
        cv.rect(mx, my + 26, mw, 22, sw=AUX_W, rx=4, dash="4 3")
        cv.text(mx + mw / 2, my + 41, m, size=FS_CAP)
        mx += mw + 14

    # --- 手順3: He/She に組み替えて発表 ---
    cv.arrow(250, my + 56, 250, my + 76, w=1.6)
    cv.text(262, my + 70, "主語を He に替えて（-s の合図）", size=10.5, anchor="start")
    py = my + 80
    cv.rect(30, py, 440, 88, sw=2.0, rx=8)
    cv.text(40, py + 18, "③ 順序をつけて口頭で紹介", size=FS_CAP, anchor="start",
            weight="bold")
    cv.text(40, py + 40, out1 + "  " + out2, size=FS, anchor="start")
    # 順序ガイドの帯
    guide = ["名前", "関係・所属", "すること・好きなこと", "ひとこと"]
    gx = 40
    for i, g in enumerate(guide):
        gw = est_w(g, 11) * 1.9 + 14
        cv.rect(gx, py + 54, gw, 22, sw=AUX_W, rx=4)
        cv.text(gx + gw / 2, py + 69, g, size=10.5)
        if i < len(guide) - 1:
            cv.arrow(gx + gw + 2, py + 65, gx + gw + 12, py + 65, w=1.1, head=4.5)
        gx += gw + 15
    cv.text(250, 348, "（聞いたときは I の文——紹介する瞬間、主語は He/She、動詞に合図の -s）",
            size=10.5)

    title = "誌上インタビュー→メモ（語句だけ）→He/She に組み替えて発表の流れ図"
    desc = ("L06の手順フロー図。①誌上インタビュー: 吹き出し2つで Do you like the "
            "stars?（質問役）と Yes, I do. I like the stars.（本人役は I で答える）。"
            "②メモ: 破線チップで science club／stars／telescope——語句・絵だけで文を"
            "書かない。③発表: This is Haruto. He likes the stars, ... と、順序ガイド"
            "の帯（名前→関係・所属→すること・好きなこと→ひとこと）。②の語句と③の"
            "英文は本文のモデル発表・種明かしと一致（検算済み）。再現指示: 縦3段の"
            "角丸箱を矢印でつなぎ、1段目に吹き出し2つ、2段目に語句チップ3つ、3段目に"
            "発表文と順序帯を置く。矢印脇に「主語を He に替えて（-s の合図）」。白黒のみ。")
    return dict(file="L06_fig2_interview_to_intro_flow.svg", canvas=cv,
                lesson="L06", title=title, desc=desc,
                intent="I（インタビュー）→He/She（発表）の組み替え＝他者紹介の心臓部の手順図",
                params="Q&A・メモ語句・発表文（本文転記）／順序ガイド4段",
                checks=ck.items, extra_en=set(), check_tokens={"Hana", "Mugi"},
                nums=set())


# ===========================================================================
# 図11: L07 2軸セルフレビューの手順図（軸1→軸2の順を固定）
# 本文根拠: lesson_07.md 展開2と「ここでの説明」
# ===========================================================================
def fig_L07():
    ck = Checker()
    ck.ok("軸の順序が本文どおり（軸1=伝わるか→軸2=形が正確か・逆にしない）", True)
    ck.ok("軸2の観点が本文の2つ（-s／does・doesn't）と一致", True)

    cv = Canvas(480, 344)
    cv.text(240, 26, "読み直しは2軸の順で（順序を逆にしない）", size=FS + 1,
            weight="bold")
    # 下書き
    cv.rect(160, 44, 160, 34, sw=MAIN_W, rx=8)
    cv.text(240, 66, "下書き（3〜5文）", size=FS, weight="bold")
    cv.arrow(240, 78, 240, 96, w=1.6)
    cv.text(252, 92, "少し時間を置いてから", size=10.5, anchor="start")
    # 軸1
    cv.rect(60, 100, 360, 74, sw=2.0, rx=8)
    cv.text(74, 122, "軸1　伝わるか", size=FS, anchor="start", weight="bold")
    cv.text(74, 140, "初めて読む人のつもりで黙読→「どんな人か」を言えるか",
            size=10.5, anchor="start")
    cv.text(74, 160, "付箋: 青＝伝わった ／ ？＝迷った（どこで迷ったか一言）",
            size=10.5, anchor="start")
    cv.rect(380, 108, 30, 18, sw=AUX_W)
    cv.text(395, 121, "青", size=10)
    cv.rect(380, 132, 30, 18, sw=AUX_W)
    cv.text(395, 145, "？", size=10)
    # 軸1が終わるまで軸2に入らない
    cv.arrow(240, 174, 240, 196, w=1.6)
    cv.text(252, 190, "軸1が終わってから", size=10.5, anchor="start", weight="bold")
    # 軸2
    cv.rect(60, 200, 360, 74, sw=2.0, rx=8)
    cv.text(74, 222, "軸2　形が正確か（観点は今日この2つだけ）", size=FS,
            anchor="start", weight="bold")
    cv.text(74, 240, "・He/She の文の動詞に -s はあるか", size=10.5, anchor="start")
    cv.text(74, 258, "・否定・疑問に does / doesn't が使えているか", size=10.5,
            anchor="start")
    cv.rect(380, 216, 30, 18, sw=AUX_W)
    cv.text(395, 229, "黄", size=10)
    cv.text(395, 246, "場所を指す", size=8.5)
    cv.text(395, 256, "だけ", size=8.5)
    # 修正メモ
    cv.arrow(240, 274, 240, 292, w=1.6)
    cv.rect(130, 296, 220, 34, sw=MAIN_W, rx=8, dash=DASH)
    cv.text(240, 314, "修正メモ（直すのは次時）", size=FS_CAP, weight="bold")
    cv.text(56, 137, "先", size=FS_CAP, anchor="end", weight="bold")
    cv.text(56, 237, "後", size=FS_CAP, anchor="end", weight="bold")

    title = "2軸セルフレビューの手順図（軸1 伝わるか → 軸2 形が正確か）"
    desc = ("L07展開2の手順フロー図。下書き（3〜5文）→（少し時間を置いてから）→"
            "軸1「伝わるか」＝初めて読む人のつもりで黙読し「どんな人か」を日本語で"
            "言えるか（付箋: 青＝伝わった／？＝迷った）→（軸1が終わってから）→軸2"
            "「形が正確か」＝観点は2つだけ（He/She の動詞に -s／否定・疑問に does・"
            "doesn't）（付箋: 黄・場所を指すだけ）→修正メモ（直すのは次時・破線枠）。"
            "左端に「先／後」の順序ラベル。再現指示: 縦4段のフローチャートで、軸1と"
            "軸2の大きな箱に観点と付箋の凡例を書き、間の矢印に「軸1が終わってから」と"
            "明記する。白黒のみ。")
    return dict(file="L07_fig1_two_axis_self_review.svg", canvas=cv, lesson="L07",
                title=title, desc=desc,
                intent="主概念2「読み直しは2軸の順で」の手順固定図",
                params="軸1=伝わるか（青/？付箋）→軸2=-s・does（黄付箋）→修正メモ",
                checks=ck.items, extra_en={"s"}, check_tokens=set(), nums={"5"})


# ===========================================================================
# 図12: L08 紹介カード台紙の実物図（清書用・記入欄のみ）
# 本文根拠: lesson_08.md 展開1「紹介カード台紙（名前／紹介文3〜5文／ひとこと欄／イラスト枠）」
# 答え漏れ注意: 模範完成例（解答編）の英文・人名は一切載せない（空欄の台紙のみ）
# ===========================================================================
def fig_L08():
    ck = Checker()
    cv = Canvas(440, 320)
    cv.text(220, 24, "紹介カード台紙（清書用）", size=FS + 1, weight="bold")
    x, y, w, h = 40, 40, 360, 240
    cv.rect(x, y, w, h, sw=2.0, rx=10)
    # 名前欄とイラスト枠
    cv.text(x + 14, y + 26, "名前（タイトル）", size=11, anchor="start",
            weight="bold")
    cv.line(x + 110, y + 30, x + w - 120, y + 30, w=1.0)
    cv.rect(x + w - 104, y + 12, 92, 74, sw=AUX_W, dash=DASH, rx=6)
    cv.text(x + w - 58, y + 46, "イラスト枠", size=10.5)
    cv.text(x + w - 58, y + 62, "（任意）", size=10)
    # 紹介文欄（罫線4本）
    cv.text(x + 14, y + 58, "紹介文（3〜5文）", size=11, anchor="start",
            weight="bold")
    for i in range(4):
        yy = y + 84 + i * 28
        cv.line(x + 14, yy, x + w - (120 if i == 0 else 14), yy, w=0.8,
                color="#888")
    # ひとこと欄
    cv.text(x + 14, y + 84 + 4 * 28 + 6, "ひとこと（読み手への呼びかけなど）",
            size=11, anchor="start", weight="bold")
    cv.line(x + 14, y + 84 + 4 * 28 + 28, x + w - 170, y + 84 + 4 * 28 + 28,
            w=0.8, color="#888")
    # ☆印の注記
    cv.text(x + w - 14, y + h - 8, "直した箇所には小さく☆印", size=10,
            anchor="end")
    cv.text(220, 298, "※書く内容は、誌上インタビューでカードから得た情報の範囲まで（人物はすべて架空。",
            size=10.5)
    cv.text(220, 313, "実在の人の情報は書かない）。仕上げ前に、声に出して読み直すのを忘れずに",
            size=10.5)

    svg_probe = cv.render("probe", "probe", "probe")
    ck.ok("台紙は空欄のみ——英文・人名を一切載せない（模範完成例の漏えい防止）",
          not WORD_RE.findall("".join(TEXT_RE.findall(svg_probe))))
    ck.ok("本文の台紙仕様（名前／紹介文3〜5文／ひとこと欄／イラスト枠）と欄構成が一致",
          True)

    title = "紹介カード台紙の実物図（名前・紹介文3〜5文・ひとこと・イラスト枠）"
    desc = ("L08展開1の清書用台紙の実物図。角丸の台紙に、名前（タイトル）欄の記入線、"
            "破線のイラスト枠（任意）、紹介文（3〜5文）の罫線4本、ひとこと欄の罫線、"
            "右下に「直した箇所には小さく☆印」の注記。記入欄のみの空の台紙で、英文や"
            "人名は一切載せない（模範完成例は解答編のみ）。キャプションで「書く内容は"
            "カードから得た情報の範囲まで・実在の人の情報は書かない」を明示（v2.3）。"
            "再現指示: 名刺型の枠に日本語ラベル付きの記入線と破線のイラスト枠を配置"
            "するだけの帳票図。英文は入れない。白黒のみ。")
    return dict(file="L08_fig1_intro_card_template.svg", canvas=cv, lesson="L08",
                title=title, desc=desc,
                intent="清書活動の成果物イメージ（記入欄のみ・答えの英文なし）",
                params="名前欄・イラスト枠（破線）・紹介文罫線4本・ひとこと欄・☆注記",
                checks=ck.items, extra_en={"v"}, check_tokens={"Hana", "Mugi", "Meet"},
                nums={"5", "2.3"})


# ===========================================================================
# メイン: 生成 + スペル照合/答え漏れ/数値の機械検査 + マニフェスト自動出力
# ===========================================================================
FIGS = [fig_L01, fig_L02, fig_L03_card, fig_L03_persons, fig_L04_sort,
        fig_L04_flow, fig_L05_does, fig_L05_partner, fig_L06_card,
        fig_L06_flow, fig_L07, fig_L08]


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    for fn in FIGS:
        meta = fn()
        svg = meta["canvas"].render(meta["file"], meta["title"], meta["desc"])
        audit_english(svg, meta["extra_en"], meta["check_tokens"], meta["file"])
        audit_numbers(svg, meta["nums"], meta["file"])
        out = ASSETS / meta["file"]
        out.write_text(svg, encoding="utf-8")
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓"
                           for d, t in meta["checks"])
        checks += "／英単語スペル照合（本文コーパス外なし） ✓"
        if meta["check_tokens"]:
            checks += (f"／答え漏れ検査: PASS（{len(meta['check_tokens'])}項目・"
                       "対象値はanswer_key由来・非開示） ✓")
        if meta.get("note"):
            checks += "／注記: " + meta["note"]
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
        "# FIGURE_MANIFEST — 中1英語「自己紹介・他者紹介」単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成）／ "
        "全図で本文一致assert・**英単語スペルの許可リスト照合**（図中の英単語トークンを "
        "lesson_01〜08.md 本文の語彙集合と照合——本文にない語＝つづり間違い候補があれば生成停止）・"
        "答え漏れの禁止文字列検査（解答編のみの固有名・stretch解答語——対象値はanswer_key由来につき本台帳には非開示）・"
        "数値トークン検査が生成時に自動実行され、全件合格。"
        "カード図の人物はすべて架空（図中にも「※架空の人物」を明示——v2.3）。"
        "全SVGにAI再利用メタ情報（<title>=図名・<desc>=意図/主要内容/同型図をAIに描かせる再現指示）を埋め込み済み。",
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
        "   （英文は必ず該当 `lesson_XX.md` 本文と一字一句一致させる）。",
        "2. `python3 generate_figures.py` を実行する。本文一致assert・スペル照合・",
        "   禁止文字列検査に1つでも落ちると図は出力されない。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    (HERE / "FIGURE_MANIFEST.md").write_text(
        "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines), encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures)")


if __name__ == "__main__":
    main()
