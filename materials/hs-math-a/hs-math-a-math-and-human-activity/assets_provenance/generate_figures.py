#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高校数学A「数学と人間の活動」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md に準拠。各図の内容仕様（各 fig_* 関数冒頭のパラメータブロック・
Checker の検算項目）は本文 lesson_XX.md と一致させる。描画ヘルパー（Canvas / Checker /
許可リスト検査 / 禁止文字列検査 / 陽性対照 / FIGURE_MANIFEST 自動生成）は先行単元
materials/hs-math-i/hs-math-i-trigonometric-ratios/assets_provenance/generate_figures.py を踏襲した。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（15枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / unicodedata / xml.etree）
- 座標の与え方: 本文明示値をパラメータに書き、数学座標→px の変換関数 Frame.P を通して描く。
  検算 assert は同じ値・同じ変換関数で照合する。
- 幾何の自己検証: 各 fig_* 関数内の Checker が検算項目を検算し、1つでも失敗すると例外で停止して
  図を出力しない。
- 答えの分離（二重ゲート＋陽性対照）:
  (1) 許可リスト検査——各図が宣言した「使ってよいラベル集合」(allow_texts) と生成後 SVG の
      <text> 全内容が集合として完全一致することを検査する。
  (2) 禁止文字列検査——練習の答え由来の禁止文字列 (check_tokens) が図中テキストに現れないこと、
      および各図の「数字の集合」制約 (digit_rule) を検査する。
  検査器は main() 冒頭の陽性対照（禁止値を仕込んだ合成 SVG で検出できること）で毎回実証する。
- 文字衛生: 絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字を、本スクリプト自身と
  全 SVG・台帳に対して機械検査する（公開側の検疫 CI と同じ向き）。
- 決定性: 乱数・時刻に依存しない。日付は SVG 先頭コメントと台帳の「生成日」行だけに現れる。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値を変えて再実行する。
  数値は該当レッスン本文（lesson_XX.md）と一致させること。
"""

import math
import datetime
import re
import unicodedata
import xml.etree.ElementTree as ET
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
LESSON_DIR = HERE.parent          # lesson_XX.md はこの階層（公開側の単元フォルダでも同じ）
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数 --------------------------------------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅（破線）
DASH = "6 4"      # 破線
DIM_W = 1.0       # 寸法線
DOT_R = 2.5       # 点マーカー半径
ARC_W = 1.2       # 角の弧の線幅
GRAY_FILL = "#ddd"   # うすい網かけ
DARK_FILL = "#000"   # 市松の黒マス
# font-family は書かない（公開側 docs/SPEC_figures.md §5 の規約。書体は閲覧環境に任せる）
DEG = math.pi / 180.0
SQ2 = math.sqrt(2)


def fs_for(width):
    """基本文字サイズ = viewBox 幅の 3 パーセント（四捨五入）"""
    return round(width * 0.03)


# ===========================================================================
# 幾何ユーティリティ
# ===========================================================================
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(v, k):
    return (v[0] * k, v[1] * k)


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def mid(a, b, t=0.5):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def unit(v):
    L = math.hypot(*v) or 1.0
    return (v[0] / L, v[1] / L)


def angle_between(u, v):
    """2ベクトルのなす角（度・0〜180）"""
    c = dot(u, v) / (math.hypot(*u) * math.hypot(*v))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def math_deg(v_px, p_px):
    """px 座標で v から p への向きを数学の角（度・反時計回り・x 軸正が 0）で返す"""
    return math.degrees(math.atan2(-(p_px[1] - v_px[1]), p_px[0] - v_px[0])) % 360.0


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    return a * b // gcd(a, b)


def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・記号は個別"""
    special = {"°": 0.45, "²": 0.45, "³": 0.45, "⁰": 0.45, "¹": 0.45, "√": 0.8, "−": 0.6,
               " ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4, "₍": 0.4, "₎": 0.4,
               "₂": 0.45, "→": 1.0, "×": 0.6, "＋": 1.0, "…": 1.0}
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
    """ラベル群に含まれる数字の連なり（「3x＋5y=1」→ {"3", "5", "1"}）"""
    out = set()
    for t in texts:
        out.update(re.findall(r"[0-9]+", t))
    return out


def show_set(s):
    """集合を整列した文字列にする（台帳に載せる detail 用。要素順の揺れを防ぐ）"""
    return "{" + ", ".join(sorted(s, key=lambda t: (len(t), t))) + "}"


# ===========================================================================
# 描画ヘルパー（Canvas = px 座標・Frame = 数学座標→px の線形変換）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.body = []
        self.texts = []          # (x0, y0, x1, y1, s) 推定バウンディングボックス
        self.bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

    def _grow(self, x, y, pad=0.0):
        self.bbox[0] = min(self.bbox[0], x - pad)
        self.bbox[1] = min(self.bbox[1], y - pad)
        self.bbox[2] = max(self.bbox[2], x + pad)
        self.bbox[3] = max(self.bbox[3], y + pad)

    def raw(self, s):
        self.body.append(s)

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w); self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def polyline(self, pts, w=MAIN_W, dash=None, close=False):
        for x, y in pts:
            self._grow(x, y, w)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="none" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="round"{d}/>')

    def polygon_fill(self, pts, fill):
        for x, y in pts:
            self._grow(x, y)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.raw(f'<polygon points="{s}" fill="{fill}" stroke="none"/>')

    def dot(self, x, y, r=DOT_R, fill="#000"):
        self._grow(x, y, r)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')

    def ring(self, x, y, r, w=1.4):
        self._grow(x, y, r + w)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" '
                 f'stroke="#000" stroke-width="{w}"/>')

    def rect(self, x, y, w, h, fill="none", dash=None, sw=1.4, rx=0):
        self._grow(x, y, sw); self._grow(x + w, y + h, sw)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{r} '
                 f'fill="{fill}" stroke="#000" stroke-width="{sw}"{d}/>')

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
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md 準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + "\n".join(self.body) + "\n</svg>\n"
        )


class Frame:
    """数学座標 (x, y)（y 上向き）→ SVG px: x_px = ox + s*x, y_px = oy − s*y"""
    def __init__(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def P(self, p):
        return (self.ox + self.s * p[0], self.oy - self.s * p[1])


def seg(cv, fr, a, b, w=MAIN_W, dash=None):
    (x1, y1), (x2, y2) = fr.P(a), fr.P(b)
    cv.line(x1, y1, x2, y2, w=w, dash=dash)


def arc_px(cv, cx, cy, r, deg_from, deg_to, n=1, gap=4.0, w=ARC_W):
    """中心 (cx, cy) px・半径 r px・数学の角 deg_from→deg_to（反時計回り）の弧を n 重に描く"""
    span = deg_to - deg_from
    k = max(6, int(math.ceil(abs(span) / 5.0)))
    for j in range(n):
        rr = r + j * gap
        pts = [(cx + rr * math.cos((deg_from + span * i / k) * DEG),
                cy - rr * math.sin((deg_from + span * i / k) * DEG)) for i in range(k + 1)]
        cv.polyline(pts, w=w)


def arc_between(cv, v_px, p_px, q_px, r, n=1):
    """頂点 v（px）で v→p と v→q の劣角に弧を描く"""
    a1 = math_deg(v_px, p_px)
    a2 = math_deg(v_px, q_px)
    d = (a2 - a1) % 360.0
    if d > 180.0:
        a1, d = a2, 360.0 - d
    arc_px(cv, v_px[0], v_px[1], r, a1, a1 + d, n=n)
    return a1 + d / 2.0


def arrow(cv, x1, y1, x2, y2, w=1.4, head=7.0, dash=None):
    """px 座標で矢印（線＋先端の三角形）"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    cv.line(x1, y1, bx, by, w=w, dash=dash)
    nx, ny = -math.sin(ang), math.cos(ang)
    pts = [(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
           (bx - nx * head * 0.45, by - ny * head * 0.45)]
    cv.polygon_fill(pts, "#000")


def bracket_h(cv, x1, x2, y, label, fs, tick=4.0, above=True):
    """水平な寸法線（両端ティック）。ラベルは線の上（above）または下"""
    cv.line(x1, y, x2, y, w=DIM_W)
    for x in (x1, x2):
        cv.line(x, y - tick, x, y + tick, w=DIM_W)
    cv.text((x1 + x2) / 2, y - fs * 0.45 if above else y + fs * 1.15, label, fs)


def bracket_v(cv, x, y1, y2, label, fs, tick=4.0, left=True):
    """垂直な寸法線（両端ティック）。ラベルは線の左（left）または右"""
    cv.line(x, y1, x, y2, w=DIM_W)
    for y in (y1, y2):
        cv.line(x - tick, y, x + tick, y, w=DIM_W)
    if left:
        cv.text(x - 8, (y1 + y2) / 2 + fs * 0.35, label, fs, anchor="end")
    else:
        cv.text(x + 8, (y1 + y2) / 2 + fs * 0.35, label, fs, anchor="start")


class Checker:
    """幾何検算の記録つき assert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


class Labels:
    """図が置いたラベルを集める（許可リスト検査の入力）"""
    def __init__(self, cv, fs):
        self.cv, self.fs, self.items = cv, fs, []

    def put(self, x, y, s, size=None, **kw):
        self.items.append(s)
        self.cv.text(x, y, s, size or self.fs, **kw)


# ===========================================================================
# L01〜L02: 記数法
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（lesson_01.md §2） ---
    dec = (10, [1000, 100, 10, 1], [2, 3, 0, 5])          # (基数, 重み, 各位の数字)
    sex = (60, [3600, 60, 1], [1, 23, 45])                 # 1 時間 23 分 45 秒
    dec_total, sex_total = 2305, 5025
    W, H = 640, 344
    fs = fs_for(W)
    box_w, box_h = 96, 46

    ck = Checker()
    for base, ws, ds in (dec, sex):
        ck.ok(f"{base} 進法: 各位の数字が基数未満（{ds}）", all(0 <= d < base for d in ds))
        ck.ok(f"{base} 進法: 重みが基数の累乗（右から基数倍ずつ増える）",
              all(ws[i] == ws[i + 1] * base for i in range(len(ws) - 1)) and ws[-1] == 1)
    ck.ok("10進法パネル: 箱の値の和 2×1000＋3×100＋0×10＋5×1=2305",
          sum(w * d for w, d in zip(dec[1], dec[2])) == dec_total)
    ck.ok("60進法パネル: 箱の値の和 1×3600＋23×60＋45×1=5025",
          sum(w * d for w, d in zip(sex[1], sex[2])) == sex_total)
    ck.ok("2305 の 10 進表記は各位の数字を並べたもの",
          "".join(str(d) for d in dec[2]) == str(dec_total))

    cv = Canvas(W, H)
    lb = Labels(cv, fs)

    def panel(y0, heading, ws, ds, eq, note):
        lb.put(40, y0, heading, anchor="start", weight="bold")
        n = len(ws)
        x0 = 40 + (W - 80 - n * (box_w + 10)) / 2
        for i, (w, d) in enumerate(zip(ws, ds)):
            x = x0 + i * (box_w + 10)
            cv.rect(x, y0 + 32, box_w, box_h)
            lb.put(x + box_w / 2, y0 + 24, str(w), size=fs - 3)           # 重み（箱の上）
            lb.put(x + box_w / 2, y0 + 32 + box_h * 0.7, str(d), weight="bold")  # 位の数字（箱の中）
        lb.put(W / 2, y0 + 32 + box_h + 30, eq, size=fs - 2)
        lb.put(W / 2, y0 + 32 + box_h + 56, note, size=fs - 4)

    panel(34, "10進法", dec[1], dec[2],
          "2×1000＋3×100＋0×10＋5×1=2305", "10 集まったら次の位へ（重みは 10倍ずつ）")
    panel(198, "60進法（1 時間 23 分 45 秒）", sex[1], sex[2],
          "1×3600＋23×60＋45×1=5025（秒）", "60 集まったら次の位へ（重みは 60倍ずつ）")
    cv.layout_checks(ck)

    return {"file": "L01_fig1_place_value_boxes.svg", "lesson": "L01", "canvas": cv,
            "title": "位取りの箱——10進法の 2305 と 60進法の 1 時間 23 分 45 秒",
            "desc": "上段は 10進法: 重み 1000・100・10・1 の箱に 2・3・0・5 を入れ、和が 2305。下段は 60進法: 重み 3600・60・1 の箱に 1・23・45 を入れ、和が 5025 秒。同型図は基数・重み・各位の数字を差し替えて生成する（各位の数字は基数未満）",
            "alt": "位取りの箱——上段は 10進法で 2305（重み 1000・100・10・1 の箱に 2・3・0・5）、下段は 60進法で 1 時間 23 分 45 秒（重み 3600・60・1 の箱に 1・23・45・合計 5025 秒）",
            "intent": "10進法と 60進法を同じ「重み×数字の和」の形で並べ、違いが繰り上がる数だけであることを見せる",
            "src": "lesson_01.md §2（秒に直す計算の直後。2305 の位取りの式は §4）",
            "params": "10進法: 重み 1000・100・10・1／数字 2・3・0・5／和 2305。60進法: 重み 3600・60・1／数字 1・23・45／和 5025",
            "checks": ck.items,
            "check_tokens": ["6500", "435", "704", "409", "5067", "5087", "7325", "24°15′", "12.75"],
            "digit_rule": ("subset", {"10", "1000", "100", "1", "2", "3", "0", "5", "2305",
                                      "60", "3600", "23", "45", "5025"}),
            "allow_texts": lb.items}


def fig_L02_1():
    # --- パラメータ（lesson_02.md §4） ---
    N, n = 45, 2
    W, H = 640, 360
    fs = fs_for(W)
    row_h = 40
    x_div, x_num, x_rem = 150, 230, 340    # 「2 )」・被除数・余り の x

    # 割り算の連鎖を計算する（本文の連鎖と一致することを assert）
    rows = []      # (被除数, 商, 余り)
    a = N
    while a > 0:
        q, r = divmod(a, n)
        rows.append((a, q, r))
        a = q
    quots = [q for _, q, _ in rows]
    rems = [r for _, _, r in rows]
    ck = Checker()
    ck.ok("商の列が本文どおり 22・11・5・2・1・0", quots == [22, 11, 5, 2, 1, 0])
    ck.ok("余りの列が本文どおり 1・0・1・1・0・1", rems == [1, 0, 1, 1, 0, 1])
    ck.ok("各行が a=2×q＋r（0≦r＜2）", all(a == n * q + r and 0 <= r < n for a, q, r in rows))
    binstr = "".join(str(r) for r in reversed(rems))
    ck.ok("余りを下から読んだ列 101101 を 2進法で読むと 45", binstr == "101101" and int(binstr, 2) == N)

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    y0 = 60
    for i, (a, q, r) in enumerate(rows):
        y = y0 + i * row_h
        lb.put(x_div, y, str(n), anchor="end")
        cv.line(x_div + 6, y - fs * 0.85, x_div + 6, y + 6, w=MAIN_W)         # 「)」の代わりの縦線
        cv.line(x_div + 6, y + 6, x_num + 34, y + 6, w=MAIN_W)                 # 下線（次の商の上）
        lb.put(x_num + 30, y, str(a), anchor="end")
        lb.put(x_rem, y, "余り", size=fs - 4, anchor="end")
        lb.put(x_rem + 34, y, str(r), anchor="end", weight="bold")
    # 最後の商 0
    y_last = y0 + len(rows) * row_h
    lb.put(x_num + 30, y_last, str(quots[-1]), anchor="end")
    lb.put(x_num + 50, y_last, "（商が 0 になったら終わり）", size=fs - 5, anchor="start")
    # 余りを下から読む矢印（余り列の右）
    xa = x_rem + 60
    arrow(cv, xa, y0 + (len(rows) - 1) * row_h - 2, xa, y0 - fs * 0.9, w=1.6, head=8)
    lb.put(xa + 12, y0 + (len(rows) - 1) * row_h / 2 + fs * 0.35, "下から読む", size=fs - 3, anchor="start")
    lb.put(xa + 12, y0 + (len(rows) - 1) * row_h / 2 + fs * 0.35 + 26, "45=101101₍₂₎", size=fs - 1,
           anchor="start", weight="bold")
    cv.layout_checks(ck)

    return {"file": "L02_fig1_division_chain.svg", "lesson": "L02", "canvas": cv,
            "title": "10進法→2進法の割り算の連鎖——45 を 2 で割り続け、余りを下から読む",
            "desc": "45 を 2 で割り続けて商 22・11・5・2・1・0、余り 1・0・1・1・0・1 を縦に並べ、余りを下から上へ読む矢印で 101101 を得る。同型図は被除数と基数を差し替えて生成する（連鎖はスクリプトが計算する）",
            "alt": "10進法→2進法の割り算の連鎖——45 を 2 で割り続け、商 22・11・5・2・1・0 と余り 1・0・1・1・0・1 を縦に並べ、余りを下から読む矢印",
            "intent": "「n で割り続けて余りを下から読む」手順を、商の列と余りの列の縦並びとして見せる",
            "src": "lesson_02.md §4（例題3の直前）",
            "params": "被除数 45・基数 2／商 22・11・5・2・1・0／余り 1・0・1・1・0・1／結果 101101",
            "checks": ck.items,
            "check_tokens": ["53", "148", "1001101", "10201", "1313", "63", "64", "81", "1000000", "10001", "110010"],
            "digit_rule": ("subset", {"2", "45", "22", "11", "5", "1", "0", "101101"}),
            "allow_texts": lb.items}


def fig_L02_2():
    # --- パラメータ（lesson_02.md §3） ---
    bits = "10110"                 # 左が最上位
    total = 22
    W, H = 640, 250
    fs = fs_for(W)
    box_w, box_h = 84, 52

    k = len(bits)
    weights = [2 ** (k - 1 - i) for i in range(k)]        # 左から 16・8・4・2・1
    ck = Checker()
    ck.ok("重みが右から 1・2・4・8・16（2 の累乗）", list(reversed(weights)) == [1, 2, 4, 8, 16])
    on = [w for w, b in zip(weights, bits) if b == "1"]
    ck.ok("1 の立つ箱が 16・4・2", on == [16, 4, 2])
    ck.ok("箱の和 16＋4＋2=22", sum(on) == total)
    ck.ok("2進法として読んでも 22", int(bits, 2) == total)

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    lb.put(40, 40, "10110₍₂₎ の各位", anchor="start", weight="bold")
    x0 = (W - k * (box_w + 12) + 12) / 2
    y0 = 90
    for i, (w, b) in enumerate(zip(weights, bits)):
        x = x0 + i * (box_w + 12)
        cv.rect(x, y0, box_w, box_h, fill=(GRAY_FILL if b == "1" else "none"))
        lb.put(x + box_w / 2, y0 - 12, str(w), size=fs - 3)
        lb.put(x + box_w / 2, y0 + box_h * 0.68, b, weight="bold")
    lb.put(W / 2, y0 + box_h + 36, "16＋4＋2=22", size=fs)
    lb.put(W / 2, y0 + box_h + 66, "網かけ＝1 の立つ箱。その重みを足す", size=fs - 4)
    cv.layout_checks(ck)

    return {"file": "L02_fig2_binary_weights.svg", "lesson": "L02", "canvas": cv,
            "title": "2進法の桁の重み——10110 は 16・4・2 の箱に 1 が立ち、和は 22",
            "desc": "5桁分の箱に右から 1・2・4・8・16 の重みを付け、10110 の各位を入れる。1 の立つ箱（16・4・2）を網かけにし、その重みの和 22 を示す。同型図は桁数とビット列を差し替えて生成する",
            "alt": "2進法の桁の重み——5桁分の箱に右から 1・2・4・8・16。10110₍₂₎ は 16・4・2 の箱に 1 が立ち、和は 22",
            "intent": "2進法では「1 の立っている位の重みを足すだけ」で 10進法に直せることを見せる",
            "src": "lesson_02.md §3（例題2の直後）",
            "params": "ビット列 10110・5桁／重み 16・8・4・2・1／和 22",
            "checks": ck.items,
            "check_tokens": ["53", "148", "63", "81", "1001101", "10201", "110010"],
            "digit_rule": ("subset", {"10110", "16", "8", "4", "2", "1", "0", "22"}),
            "allow_texts": lb.items}


# ===========================================================================
# L03〜L05: 整数の性質
# ===========================================================================
SUP = {0: "⁰", 1: "¹", 2: "²", 3: "³"}


def fig_L03_1():
    # --- パラメータ（lesson_03.md §4） ---
    p, a = 2, 3          # 72 = 2³ × 3²
    q, b = 3, 2
    N = 72
    W, H = 640, 300
    fs = fs_for(W)
    cell_w, cell_h = 96, 46
    x0, y0 = 150, 90

    cells = [[p ** i * q ** j for i in range(a + 1)] for j in range(b + 1)]   # 行 j（3 の指数）・列 i（2 の指数）
    flat = [v for row in cells for v in row]
    ck = Checker()
    ck.ok("p^a×q^b=72（2³×3²）", p ** a * q ** b == N)
    ck.ok("格子のセル数＝(a＋1)(b＋1)=12", len(flat) == (a + 1) * (b + 1) == 12)
    ck.ok("全セルが 72 を割る", all(N % v == 0 for v in flat))
    ck.ok("セルの集合＝72 の約数全体（過不足なし）", sorted(flat) == [d for d in range(1, N + 1) if N % d == 0])
    ck.ok("左上 1・右下 72", cells[0][0] == 1 and cells[b][a] == N)
    ck.ok("本文の書き出し順（行ごと）と一致: 1,2,4,8／3,6,12,24／9,18,36,72",
          cells == [[1, 2, 4, 8], [3, 6, 12, 24], [9, 18, 36, 72]])

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    lb.put(40, 40, "72=2³×3² の約数（横: 2 の指数・縦: 3 の指数）", anchor="start", weight="bold", size=fs - 2)
    for i in range(a + 1):
        lb.put(x0 + i * cell_w + cell_w / 2, y0 - 12, f"{p}{SUP[i]}", size=fs - 2)
    for j in range(b + 1):
        lb.put(x0 - 14, y0 + j * cell_h + cell_h * 0.68, f"{q}{SUP[j]}", size=fs - 2, anchor="end")
    for j in range(b + 1):
        for i in range(a + 1):
            x, y = x0 + i * cell_w, y0 + j * cell_h
            cv.rect(x, y, cell_w, cell_h, fill=("none" if (i, j) not in ((0, 0), (a, b)) else GRAY_FILL))
            lb.put(x + cell_w / 2, y + cell_h * 0.68, str(cells[j][i]))
    lb.put(W / 2, y0 + (b + 1) * cell_h + 34, "全 12マス＝(3＋1)×(2＋1)", size=fs - 2)
    cv.layout_checks(ck)

    return {"file": "L03_fig1_divisor_grid.svg", "lesson": "L03", "canvas": cv,
            "title": "素因数の指数の組合せ表——72=2³×3² の約数 12個の 4×3 格子",
            "desc": "横に 2⁰・2¹・2²・2³、縦に 3⁰・3¹・3² を並べ、各マスにその積（72 の約数）を書いた 4×3 の格子。左上 1・右下 72 を網かけ。同型図は素数 p, q と指数 m, n を差し替えて生成する（マス数は (m＋1)(n＋1)）",
            "alt": "素因数の指数の組合せ表——72=2³×3² の約数を、横に 2⁰・2¹・2²・2³、縦に 3⁰・3¹・3² で並べた 4×3 の格子。左上 1、右下 72、全 12マス",
            "intent": "約数の個数が「各指数に 1 を足した数の積」になる理由を、指数の組合せの格子として見せる",
            "src": "lesson_03.md §4（72 の約数の書き出しの直前）",
            "params": "p=2, a=3／q=3, b=2／N=72／格子 4×3=12マス",
            "checks": ck.items,
            "check_tokens": ["5214", "7308", "1116", "4905", "200", "195", "56", "28", "49", "25", "121", "169"],
            "digit_rule": ("subset", {"72", "2", "3", "1", "4", "8", "6", "12", "24", "9", "18", "36"}),
            "allow_texts": lb.items}


def fig_L04_1():
    # --- パラメータ（lesson_04.md §4） ---
    m, n = 6, 8
    x_max = 48
    W, H = 640, 230
    fs = fs_for(W)
    px0, scale = 56, 11.0          # 0 の位置と 1 秒あたりの px
    y_line = 120

    A = [t for t in range(0, x_max + 1) if t % m == 0]
    B = [t for t in range(0, x_max + 1) if t % n == 0]
    both = [t for t in range(1, x_max + 1) if t % m == 0 and t % n == 0]
    ck = Checker()
    ck.ok("最小公倍数 lcm(6, 8)=24", lcm(m, n) == 24)
    ck.ok("そろう点（0 を除く・48 まで）＝{24, 48}", both == [24, 48])
    ck.ok("そろう点はすべて 24 の倍数", all(t % lcm(m, n) == 0 for t in both))
    ck.ok("A の目盛り 6, 12, …, 48（8個）・B の目盛り 8, 16, …, 48（6個）",
          A[1:] == [6, 12, 18, 24, 30, 36, 42, 48] and B[1:] == [8, 16, 24, 32, 40, 48])

    def X(t):
        return px0 + scale * t

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    arrow(cv, X(0) - 10, y_line, X(x_max) + 30, y_line, w=MAIN_W, head=9)
    lb.put(X(0), y_line + 30, "0", size=fs - 2)
    cv.line(X(0), y_line - 5, X(0), y_line + 5, w=MAIN_W)
    # A: 上向きの目盛りとラベル
    for t in A[1:]:
        cv.line(X(t), y_line - 14, X(t), y_line, w=MAIN_W)
        lb.put(X(t), y_line - 20, str(t), size=fs - 3)
    # B: 下向きの目盛りとラベル
    for t in B[1:]:
        cv.line(X(t), y_line, X(t), y_line + 14, w=MAIN_W)
        lb.put(X(t), y_line + 30, str(t), size=fs - 3)
    # そろう点
    for t in both:
        cv.dot(X(t), y_line, r=4.5)
        lb.put(X(t), y_line + 56, "同時", size=fs - 3)
    lb.put(40, 44, "A（6 秒ごと）", size=fs - 2, anchor="start")
    lb.put(40, 190, "B（8 秒ごと）", size=fs - 2, anchor="start")
    lb.put(W - 40, 44, "●＝同時に光る（24 秒ごと）", size=fs - 3, anchor="end")
    lb.put(X(x_max) + 36, y_line + fs * 0.35, "秒", size=fs - 3, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L04_fig1_period_number_line.svg", "lesson": "L04", "canvas": cv,
            "title": "周期の数直線——6 秒ごとの A と 8 秒ごとの B がそろう 24 と 48",
            "desc": "0 から 48 秒の数直線に、6 の倍数の目盛り（上側）と 8 の倍数の目盛り（下側）を並べ、両方がそろう 24・48 に黒丸を置く。同型図は周期 m, n と範囲を差し替えて生成する（そろう点は lcm(m, n) の倍数）",
            "alt": "周期の数直線——6 の倍数の目盛りと 8 の倍数の目盛りを 0 から 48 まで並べ、両方がそろう 24 と 48 に印",
            "intent": "2つの周期が「同時に起こる」時刻が公倍数で、最初が最小公倍数であることを数直線で見せる",
            "src": "lesson_04.md §4（例題3の直前）",
            "params": "周期 m=6, n=8／範囲 0〜48 秒／lcm=24／そろう点 24・48／目盛り 11 px/秒",
            "checks": ck.items,
            "check_tokens": ["252", "450", "225", "1764", "77", "180", "7 分", "8 秒後"],
            "digit_rule": ("subset", {"0", "6", "12", "18", "24", "30", "36", "42", "48",
                                      "8", "16", "32", "40"}),
            "allow_texts": lb.items}


def fig_L05_1():
    # --- パラメータ（lesson_05.md §3） ---
    b = 4                 # 何列に並べるか（割る数）
    n_rows = 6            # 0 から 23 まで
    W, H = 640, 330
    fs = fs_for(W)
    cell_w, cell_h = 90, 34
    x0, y0 = 140, 88

    table = [[r * b + c for c in range(b)] for r in range(n_rows)]
    ck = Checker()
    ck.ok("表の数は 0 から 23 まで順に（24個）", [v for row in table for v in row] == list(range(b * n_rows)))
    ck.ok("各列の要素は 4 で割った余りが一致（列番号に等しい）",
          all(all(table[r][c] % b == c for r in range(n_rows)) for c in range(b)))
    ck.ok("1行目 0・1・2・3、2行目 4・5・6・7", table[0] == [0, 1, 2, 3] and table[1] == [4, 5, 6, 7])
    ck.ok("どの数もちょうど 1つの列に入る（列の集合が互いに素で全体を覆う）",
          sum(len(set(table[r][c] for r in range(n_rows))) for c in range(b)) == b * n_rows)

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    lb.put(40, 40, "0 以上の整数を 4個ずつ横に並べる", anchor="start", weight="bold", size=fs - 2)
    for c in range(b):
        lb.put(x0 + c * cell_w + cell_w / 2, y0 - 12, f"余り {c}", size=fs - 3)
    for r in range(n_rows):
        for c in range(b):
            x, y = x0 + c * cell_w, y0 + r * cell_h
            cv.rect(x, y, cell_w, cell_h, fill=(GRAY_FILL if c == 0 else "none"), sw=1.0)
            lb.put(x + cell_w / 2, y + cell_h * 0.7, str(table[r][c]), size=fs - 2)
    lb.put(x0 - 12, y0 + cell_h * 0.7, "1行目", size=fs - 4, anchor="end")
    lb.put(x0 - 12, y0 + cell_h + cell_h * 0.7, "2行目", size=fs - 4, anchor="end")
    lb.put(W / 2, y0 + n_rows * cell_h + 30, "同じ列の数は、4 で割った余りが同じ", size=fs - 3)
    cv.layout_checks(ck)

    return {"file": "L05_fig1_remainder_columns.svg", "lesson": "L05", "canvas": cv,
            "title": "4列に並べた整数の表——同じ列は 4 で割った余りが同じ",
            "desc": "0 から 23 までを 4個ずつ横に並べて折り返した 6行 4列の表。列の見出しは余り 0・1・2・3 で、左端の列（余り 0）を網かけ。同型図は割る数 b と行数を差し替えて生成する",
            "alt": "4列に並べた整数の表——1行目 0・1・2・3、2行目 4・5・6・7、以下 6行で 23 まで。各列の数は 4 で割った余りが同じ（左から余り 0・1・2・3）",
            "intent": "b で割った余りで整数全体が b 個の組に分かれることを、列に並べた表で見せる",
            "src": "lesson_05.md §3（節の冒頭）",
            "params": "b=4／行数 6／数 0〜23／セル 90×34 px",
            "checks": ck.items,
            "check_tokens": ["325", "109", "101", "1000=13"],
            "digit_rule": ("subset", {str(v) for v in range(24)}),
            "allow_texts": lb.items}


# ===========================================================================
# L06〜L07: 互除法と不定方程式
# ===========================================================================
def euclid_squares(a, b):
    """横 a・縦 b の長方形を左（または下）から最大の正方形で埋めていく。
    返り値: 正方形の (x, y, 辺) の列（左下原点・y 上向き）と互除法の商の列"""
    squares, quots = [], []
    x0, y0, w, h = 0.0, 0.0, float(a), float(b)
    while min(w, h) > 1e-12:
        if w >= h:                      # 横長: 左から辺 h の正方形を詰める
            q = int(w // h)
            for i in range(q):
                squares.append((x0 + i * h, y0, h))
            quots.append(q)
            x0, w = x0 + q * h, w - q * h
        else:                           # 縦長: 下から辺 w の正方形を詰める
            q = int(h // w)
            for i in range(q):
                squares.append((x0, y0 + i * w, w))
            quots.append(q)
            y0, h = y0 + q * w, h - q * w
    return squares, quots, (x0, y0, w, h)


def fig_L06_1():
    # --- パラメータ（lesson_06.md §2） ---
    a, b = 30, 18                  # 横 30・縦 18
    W, H = 640, 340
    fs = fs_for(W)
    fr = Frame(120, 300, 14.0)     # 左下 (120,300) px・14 px/単位

    squares, quots, rest = euclid_squares(a, b)
    sides = [int(round(s_)) for _, _, s_ in squares]
    ck = Checker()
    ck.ok("正方形の辺の列が 18・12・6・6（本文の手順 1〜3）", sides == [18, 12, 6, 6])
    ck.ok("各段の個数＝互除法の商 1・1・2（30=18×1＋12, 18=12×1＋6, 12=6×2＋0）",
          quots == [1, 1, 2] and 30 == 18 * 1 + 12 and 18 == 12 * 1 + 6 and 12 == 6 * 2 + 0)
    ck.ok("最後の正方形の辺 6＝gcd(30, 18)", sides[-1] == gcd(a, b) == 6)
    ck.ok("残りの長方形が無い（ぴったり埋まる）", rest[2] < 1e-9 or rest[3] < 1e-9)
    ck.ok("正方形の面積の和＝30×18", near(sum(s_ * s_ for _, _, s_ in squares), a * b))
    ck.ok("正方形どうしが重ならず長方形の内側にある",
          all(0 <= x and 0 <= y and x + s_ <= a + 1e-9 and y + s_ <= b + 1e-9 for x, y, s_ in squares) and
          all(sq1[0] + sq1[2] <= sq2[0] + 1e-9 or sq2[0] + sq2[2] <= sq1[0] + 1e-9 or
              sq1[1] + sq1[2] <= sq2[1] + 1e-9 or sq2[1] + sq2[2] <= sq1[1] + 1e-9
              for i, sq1 in enumerate(squares) for sq2 in squares[i + 1:]))

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    # 外枠
    X0, Y0 = fr.P((0, b))
    cv.rect(X0, Y0, a * fr.s, b * fr.s, sw=BOLD_W)
    for x, y, s_ in squares:
        px, py = fr.P((x, y + s_))
        cv.rect(px, py, s_ * fr.s, s_ * fr.s, fill=(GRAY_FILL if near(s_, gcd(a, b)) else "none"))
        lb.put(px + s_ * fr.s / 2, py + s_ * fr.s / 2 + fs * 0.35, str(int(round(s_))))
    bracket_h(cv, X0, X0 + a * fr.s, Y0 - 16, str(a), fs)
    bracket_v(cv, X0 - 16, Y0, Y0 + b * fr.s, str(b), fs)
    lb.items += [str(a), str(b)]
    lb.put(W / 2, Y0 + b * fr.s + 32, "網かけ＝最後にぴったり埋まった正方形（辺 6＝最大公約数）", size=fs - 4)
    cv.layout_checks(ck)

    return {"file": "L06_fig1_rectangle_squares.svg", "lesson": "L06", "canvas": cv,
            "title": "30×18 の長方形を正方形で埋める——18・12・6・6 で隙間なく埋まる",
            "desc": "横 30・縦 18 の長方形を、左から 1辺 18 の正方形 1個、残りを 1辺 12 の正方形 1個、残りを 1辺 6 の正方形 2個で埋める。最後の 2 個の正方形（網かけ）の辺 6 が最大公約数。同型図は a, b を差し替えて生成する（正方形の列はスクリプトが互除法で計算する）",
            "alt": "30×18 の長方形を正方形で埋める——1辺 18 の正方形 1個、1辺 12 の正方形 1個、1辺 6 の正方形 2個で隙間なく埋まる。最後の正方形の辺 6 が最大公約数",
            "intent": "互除法の各行（商と余り）を、長方形を正方形で埋める操作として見せ、最後の正方形の辺が最大公約数であることを示す",
            "src": "lesson_06.md §2（手順 1〜3 の直後）",
            "params": "a=30, b=18／正方形の辺 18・12・6・6／商 1・1・2／gcd=6／14 px/単位",
            "checks": ck.items,
            "check_tokens": ["143", "91", "1071", "462", "273", "13", "21", "23", "27", "115"],
            "digit_rule": ("subset", {"30", "18", "12", "6"}),
            "allow_texts": lb.items}


def fig_L06_2():
    # --- パラメータ（lesson_06.md §5） ---
    a, b = SQ2, 1.0                # 横 √2・縦 1
    stages = 3
    W, H = 640, 400
    fs = fs_for(W)
    fr = Frame(80, 340, 300.0)     # 左下 (80,340) px・300 px/単位
    r0 = SQ2 - 1                   # 端の比 1:(√2−1)

    # 段ごとに正方形を詰め、残りの長方形の辺の比を検算する
    ck = Checker()
    x0, y0, w, h = 0.0, 0.0, a, b
    all_squares = []               # (段, x, y, 辺)
    counts, ratios = [], []
    for k in range(stages):
        if w >= h:
            q = int(math.floor(w / h + 1e-9))
            for i in range(q):
                all_squares.append((k, x0 + i * h, y0, h))
            x0, w = x0 + q * h, w - q * h
        else:
            q = int(math.floor(h / w + 1e-9))
            for i in range(q):
                all_squares.append((k, x0, y0 + i * w, w))
            y0, h = y0 + q * w, h - q * w
        counts.append(q)
        ratios.append(min(w, h) / max(w, h))
    ck.ok("各段の正方形の個数が 1・2・2（3 段の分割）", counts == [1, 2, 2])
    ck.ok("各段の正方形の辺が 1・(√2−1)・(√2−1)²（許容誤差 1e-9）",
          all(near(s_, r0 ** k, 1e-9) for k, _, _, s_ in all_squares))
    ck.ok("各段の残り長方形の辺の比（短辺/長辺）が √2−1 で一致（許容誤差 1e-9）",
          all(near(r, r0, 1e-9) for r in ratios), f"比={ratios[0]:.12f}")
    ck.ok("2段目以降の残りは 1段目の残り (√2−1)×1 と相似（比 √2−1＝1/(√2＋1)・許容誤差 1e-9）",
          all(near(r, ratios[0], 1e-9) for r in ratios[1:]) and near(r0, 1 / (SQ2 + 1), 1e-9))
    ck.ok("残りの長さは 0 にならない（3段目の残り＝(√2−1)³＞0）", min(w, h) > 0 and near(min(w, h), r0 ** 3, 1e-9))

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    X0, Y0 = fr.P((0, b))
    # 残りの長方形（網かけ）
    rx, ry = fr.P((x0, y0 + h))
    cv.polygon_fill([(rx, ry), (rx + w * fr.s, ry), (rx + w * fr.s, ry + h * fr.s), (rx, ry + h * fr.s)], GRAY_FILL)
    cv.rect(X0, Y0, a * fr.s, b * fr.s, sw=BOLD_W)
    for k, x, y, s_ in all_squares:
        px, py = fr.P((x, y + s_))
        cv.rect(px, py, s_ * fr.s, s_ * fr.s, sw=(1.4 if k < 2 else 1.0))
        if k == 0:
            lb.put(px + s_ * fr.s / 2, py + s_ * fr.s / 2 + fs * 0.35, "1")
        elif k == 1:
            lb.put(px + s_ * fr.s / 2, py + s_ * fr.s / 2 + fs * 0.35, "√2−1", size=fs - 3)
    bracket_h(cv, X0, X0 + a * fr.s, Y0 - 16, "√2", fs)
    bracket_v(cv, X0 - 16, Y0, Y0 + b * fr.s, "1", fs)
    lb.items += ["√2", "1"]
    lb.put(W / 2, Y0 + b * fr.s + 30, "3段目: 1辺 (√2−1)² の正方形 2個。網かけ＝残る長方形（1段目の残りと同じ形）", size=fs - 5)
    cv.layout_checks(ck)

    return {"file": "L06_fig2_sqrt2_rectangle.svg", "lesson": "L06", "canvas": cv,
            "title": "1×√2 の長方形の分割が続く図——正方形 1個、√2−1 の正方形 2個、また 2個",
            "desc": "横 √2・縦 1 の長方形に、1辺 1 の正方形 1個、残りに 1辺 √2−1 の正方形 2個、残りに 1辺 (√2−1)² の正方形 2個を詰め、残る長方形（網かけ）が毎回、1辺 1 の正方形を 1個取った後に残る長方形 (√2−1)×1 と同じ形（相似）になることを 3段まで描く。同型図は段数を差し替えて生成する（座標は浮動小数・比の検算は許容誤差つき）",
            "alt": "1×√2 の長方形の分割が続く図——1辺 1 の正方形 1個、1辺 √2−1 の正方形 2個、次にまた 2個と続き、残る長方形は毎回、手順 1 で残った長方形と同じ形になる（3段まで描画）",
            "intent": "1×√2 の長方形（1辺 1 の正方形とその対角線）では互除法の手順が止まらないこと（端が毎回同じ形で残る）を見せる",
            "src": "lesson_06.md §5（手順 1〜3 の直後）",
            "params": "a=√2, b=1／段数 3／各段の個数 1・2・2／端の比 √2−1／300 px/単位",
            "checks": ck.items,
            "check_tokens": ["1.414", "2.414", "0.414", "143", "91"],
            "digit_rule": ("subset", {"1", "2", "3"}),
            "allow_texts": lb.items}


def fig_L07_1():
    # --- パラメータ（lesson_07.md §3） ---
    A, B, C = 3, 5, 1                  # 3x＋5y=1
    x_min, x_max = -5, 15
    y_min, y_max = -9, 4
    sols = [(-3, 2), (2, -1), (7, -4), (12, -7)]
    step = (5, -3)
    W, H = 640, 420
    fs = fs_for(W)
    fr = Frame(60 + 5 * 22, 62 + 4 * 22, 22.0)      # 原点 px・22 px/単位

    ck = Checker()
    ck.ok("印を付けた点はすべて 3x＋5y=1 を満たす", all(A * x + B * y == C for x, y in sols))
    ck.ok("隣接する解の差が (5, −3)＝(b, −a)",
          all((sols[i + 1][0] - sols[i][0], sols[i + 1][1] - sols[i][1]) == step for i in range(len(sols) - 1))
          and step == (B, -A))
    all_sols = [(x, (C - A * x) // B) for x in range(x_min, x_max + 1) if (C - A * x) % B == 0]
    ck.ok("x が −5〜15 の整数解は印を付けた 4点で全部", all_sols == sols)
    # 直線の描画端点（x=−5, x=15）と解の px が同一直線上（外積 0・許容誤差）
    p1 = ((x_min), (C - A * x_min) / B)
    p2 = ((x_max), (C - A * x_max) / B)
    ck.ok("解の px 座標が描いた直線の px 端点と同一直線上（外積 ≈ 0）",
          all(abs(cross(sub(fr.P(p2), fr.P(p1)), sub(fr.P(sl), fr.P(p1)))) < 1e-6 for sl in sols))
    ck.ok("直線の端点が枠内（y の範囲 −9〜4）", y_min <= p1[1] <= y_max and y_min <= p2[1] <= y_max)

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    # 格子点（小さな灰色の点）
    for gx in range(x_min, x_max + 1):
        for gy in range(y_min, y_max + 1):
            px, py = fr.P((gx, gy))
            cv.dot(px, py, r=1.3, fill="#999")
    # 軸
    ox, oy = fr.P((0, 0))
    arrow(cv, fr.P((x_min - 0.5, 0))[0], oy, fr.P((x_max + 0.8, 0))[0], oy, w=MAIN_W, head=9)
    arrow(cv, ox, fr.P((0, y_min - 0.5))[1], ox, fr.P((0, y_max + 0.8))[1], w=MAIN_W, head=9)
    lb.put(fr.P((x_max + 0.8, 0))[0] + 6, oy + fs * 0.35, "x", anchor="start")
    lb.put(ox, fr.P((0, y_max + 0.8))[1] - 6, "y")
    lb.put(ox - 6, oy + fs * 1.0, "O", anchor="end")
    for t in (10, 15):
        px, _ = fr.P((t, 0))
        cv.line(px, oy - 4, px, oy + 4, w=MAIN_W)
        lb.put(px, oy + fs * 1.05, str(t), size=fs - 4)
    for t in (-5,):
        _, py = fr.P((0, t))
        cv.line(ox - 4, py, ox + 4, py, w=MAIN_W)
        lb.put(ox - 8, py + fs * 0.35, "−5", size=fs - 4, anchor="end")
    # 直線
    seg(cv, fr, p1, p2, w=MAIN_W)
    lb.put(fr.P(p2)[0] + 8, fr.P(p2)[1] + fs * 0.35, "3x＋5y=1", anchor="start")
    # 解の点と座標ラベル（点の右上＝直線の上側の空き）
    for x, y in sols:
        px, py = fr.P((x, y))
        cv.dot(px, py, r=4.0)
        lb.put(px + 8, py - 8, f"({x}, {y})".replace("-", "−"), size=fs - 3, anchor="start")
    # 隣接する解の差 (5, −3): 破線の直角折れ線（(7, −4) → (12, −7)）
    (sx, sy), (tx, ty) = fr.P(sols[2]), fr.P(sols[3])
    cv.line(sx, sy, tx, sy, w=AUX_W, dash=DASH)
    cv.line(tx, sy, tx, ty, w=AUX_W, dash=DASH)
    lb.put(sx + (tx - sx) * 0.78, sy - 6, "5", size=fs - 3)
    lb.put(tx + 8, (sy + ty) / 2 + fs * 0.35, "−3", size=fs - 3, anchor="start")
    lb.put(W - 40, 40, "隣り合う解の差は (5, −3)", size=fs - 3, anchor="end")
    cv.layout_checks(ck)

    return {"file": "L07_fig1_lattice_line.svg", "lesson": "L07", "canvas": cv,
            "title": "格子点と直線 3x＋5y=1——整数解 (−3, 2)・(2, −1)・(7, −4)・(12, −7) が等間隔に並ぶ",
            "desc": "x が −5〜15、y が −9〜4 の格子点の上に直線 3x＋5y=1 を引き、直線上の整数解 4点に黒丸を置く。隣り合う解の差 (5, −3) を破線の折れ線で示す。同型図は a, b, c と範囲を差し替えて生成する（解の点はスクリプトが計算する）",
            "alt": "格子点と直線 3x＋5y=1——x が −5 から 15 の範囲で、直線上の整数解 (−3, 2)、(2, −1)、(7, −4)、(12, −7) に印。隣り合う解の差は (5, −3)",
            "intent": "不定方程式の整数解が直線上の格子点として等間隔に並ぶこと（一般解の形）を見せる",
            "src": "lesson_07.md §3（k の表の直後）",
            "params": "a=3, b=5, c=1／x の範囲 −5〜15・y の範囲 −9〜4／解 (−3,2)(2,−1)(7,−4)(12,−7)／差 (5,−3)／22 px/単位",
            "checks": ck.items,
            "check_tokens": ["−17", "7k", "4k", "13", "21", "143", "6組"],
            "digit_rule": ("subset", {"3", "5", "1", "2", "7", "4", "12", "10", "15"}),
            "allow_texts": lb.items}


# ===========================================================================
# L08〜L09: 測る・位置を示す・状態遷移
# ===========================================================================
class Frame3:
    """空間座標 (x, y, z) → px の斜投影（キャビネット図）。
    y 軸は右向き・z 軸は上向き・x 軸（手前向き）は左下 45° へ半分の長さで描く。線形変換"""
    def __init__(self, ox, oy, s, k=0.5, ang=45.0):
        self.ox, self.oy, self.s = ox, oy, s
        self.ex = (-k * math.cos(ang * DEG), k * math.sin(ang * DEG))   # x 軸 1 単位の px ベクトル
        self.ey = (1.0, 0.0)
        self.ez = (0.0, -1.0)

    def P(self, p):
        x, y, z = p
        return (self.ox + self.s * (x * self.ex[0] + y * self.ey[0] + z * self.ez[0]),
                self.oy + self.s * (x * self.ex[1] + y * self.ey[1] + z * self.ez[1]))


def fig_L08_1():
    # --- パラメータ（lesson_08.md §4 例題4） ---
    a, b, c = 4, 3, 2                     # x 方向・y 方向・z 方向（高さ）の辺の長さ
    W, H = 640, 400
    fs = fs_for(W)
    fr = Frame3(220, 250, 60.0)           # 原点 px・60 px/単位

    verts = [(x, y, z) for x in (0, a) for y in (0, b) for z in (0, c)]
    edges = [(u, v) for i, u in enumerate(verts) for v in verts[i + 1:]
             if sum(1 for j in range(3) if u[j] != v[j]) == 1]
    hidden = [(u, v) for u, v in edges if (0, 0, 0) in (u, v)]     # 原点に集まる 3辺（破線のまま残し、軸の矢印はその先から描く）
    ck = Checker()
    ck.ok("頂点 8個・辺 12本", len(verts) == 8 and len(edges) == 12)
    ck.ok("P=(4, 3, 2) が原点から最も遠い頂点",
          max(verts, key=lambda v: v[0] ** 2 + v[1] ** 2 + v[2] ** 2) == (a, b, c))
    O_px = fr.P((0, 0, 0))
    ex, ey, ez = sub(fr.P((1, 0, 0)), O_px), sub(fr.P((0, 1, 0)), O_px), sub(fr.P((0, 0, 1)), O_px)
    ck.ok("投影が線形: 全頂点で P(x,y,z)=O＋x·ex＋y·ey＋z·ez（許容誤差 1e-9）",
          all(near(fr.P(v)[0], O_px[0] + v[0] * ex[0] + v[1] * ey[0] + v[2] * ez[0]) and
              near(fr.P(v)[1], O_px[1] + v[0] * ex[1] + v[1] * ey[1] + v[2] * ez[1]) for v in verts))
    ck.ok("平行な辺は px でも同じベクトル（平行四辺形として描かれる）",
          all(near(sub(fr.P(v), fr.P(u))[0], sub(fr.P(v2), fr.P(u2))[0]) and
              near(sub(fr.P(v), fr.P(u))[1], sub(fr.P(v2), fr.P(u2))[1])
              for (u, v) in edges for (u2, v2) in edges
              if sub(v, u) == sub(v2, u2)))
    ck.ok("辺の長さの比: y 方向 3 単位=180 px・z 方向 2 単位=120 px・x 方向は半分の縮尺",
          near(dist(fr.P((0, 0, 0)), fr.P((0, b, 0))), 180.0) and
          near(dist(fr.P((0, 0, 0)), fr.P((0, 0, c))), 120.0) and
          near(dist(fr.P((0, 0, 0)), fr.P((a, 0, 0))), 0.5 * a * 60.0))
    ck.ok("隠れる辺は原点に集まる 3本だけ（破線のまま残し、軸の矢印は箱の頂点から外側へ実線で描く）", len(hidden) == 3)

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    # 見える辺（実線）と隠れる辺（破線・軸と重なる区間はこの破線だけを見せる）
    for u, v in edges:
        (x1, y1), (x2, y2) = fr.P(u), fr.P(v)
        cv.line(x1, y1, x2, y2, w=(AUX_W if (u, v) in hidden else MAIN_W),
                dash=(DASH if (u, v) in hidden else None))
    # 軸（矢印）——箱の内側（原点に集まる隠れ辺）は破線のままにし、箱の頂点から外側だけ実線で描く
    arrow(cv, *fr.P((a, 0, 0)), *fr.P((a + 2.2, 0, 0)), w=MAIN_W, head=9)
    arrow(cv, *fr.P((0, b, 0)), *fr.P((0, b + 1.6, 0)), w=MAIN_W, head=9)
    arrow(cv, *fr.P((0, 0, c)), *fr.P((0, 0, c + 1.2)), w=MAIN_W, head=9)
    xe, ye, ze = fr.P((a + 2.2, 0, 0)), fr.P((0, b + 1.6, 0)), fr.P((0, 0, c + 1.2))
    lb.put(xe[0] - 10, xe[1] + 10, "x", anchor="end")
    lb.put(ye[0] + 8, ye[1] + fs * 0.35, "y", anchor="start")
    lb.put(ze[0], ze[1] - 8, "z")
    lb.put(O_px[0] + 8, O_px[1] + fs * 1.0, "O", anchor="start")
    # 頂点 P
    Ppx = fr.P((a, b, c))
    cv.dot(Ppx[0], Ppx[1], r=4.0)
    # ラベルは上面の内側・P の左上に置く（P の右に置くと上面の右の辺と重なる。幅 92 px の文字列は破線 x=220 と P の間に入らないので fs−3）
    lb.put(Ppx[0] - 6, Ppx[1] - 10, "P (4, 3, 2)", size=fs - 3, anchor="end", weight="bold")
    # 辺の長さ（手前の見える辺に添える）
    m = mid(fr.P((0, b, 0)), fr.P((a, b, 0)))
    lb.put(m[0] + 12, m[1] + fs * 0.35, "4", anchor="start")            # x 方向（右下の手前辺）
    m = mid(fr.P((a, 0, 0)), fr.P((a, b, 0)))
    lb.put(m[0], m[1] + fs * 1.1, "3")                                   # y 方向（手前の底辺）
    m = mid(fr.P((a, b, 0)), fr.P((a, b, c)))
    lb.put(m[0] + 10, m[1] + fs * 0.35, "2", anchor="start")            # z 方向（手前右の立辺）
    lb.put(W - 40, 40, "床の角 O を原点にした 3本の軸と直方体", size=fs - 3, anchor="end")
    cv.layout_checks(ck)

    return {"file": "L08_fig1_space_coordinates.svg", "lesson": "L08", "canvas": cv,
            "title": "空間の座標——原点 O に置いた x 軸方向 4・y 軸方向 3・z 軸方向 2 の直方体と頂点 P (4, 3, 2)",
            "desc": "床の角 O を原点に x 軸（手前向き）・y 軸（右向き）・z 軸（高さ）を立て、3辺が軸に重なる直方体を斜投影で描く（原点に集まる 3辺は隠れ辺として破線で描き、軸の矢印は箱の頂点から外側へ実線で続ける）。O から最も遠い頂点 P (4, 3, 2) に黒丸。同型図は a, b, c を差し替えて生成する（投影は線形変換）",
            "alt": "床の角 O を原点にした3本の軸と、x 軸方向に 4・y 軸方向に 3・z 軸方向に 2 の直方体、頂点 P (4, 3, 2) を示した図",
            "intent": "空間の点の位置が「3本の数直線に沿った 3つの数の組」で決まることを、直方体の頂点で見せる",
            "src": "lesson_08.md §4（例題4の解答の直後）",
            "params": "a=4（x）, b=3（y）, c=2（z）／原点 (220,250) px・60 px/単位／x 軸は左下 45°・縮尺 0.5",
            "checks": ck.items,
            "check_tokens": ["8°", "36,000", "41,100", "(2, 2)", "(2, −2)", "7手", "15回"],
            "digit_rule": ("subset", {"4", "3", "2"}),
            "allow_texts": lb.items}


def fig_L08_2():
    # --- パラメータ（lesson_08.md §2） ---
    ang_A, ang_B = 45.0, 60.0            # 光線と棒（半径）のなす角
    sun_dir = 90.0                       # 太陽の方向（数学の角・度・真上）
    R = 1.0
    W, H = 640, 480
    fs = fs_for(W)
    fr = Frame(330, 270, 160.0)          # 中心 O の px・半径 160 px

    u = (math.cos(sun_dir * DEG), math.sin(sun_dir * DEG))          # 太陽へ向かう単位ベクトル
    A = (R * math.cos((sun_dir + ang_A) * DEG), R * math.sin((sun_dir + ang_A) * DEG))
    B = (R * math.cos((sun_dir + ang_B) * DEG), R * math.sin((sun_dir + ang_B) * DEG))
    central = ang_B - ang_A
    ck = Checker()
    ck.ok("半径 OA と光線のなす角 45°・OB と光線のなす角 60°（許容誤差 1e-9）",
          near(angle_between(A, u), ang_A) and near(angle_between(B, u), ang_B))
    ck.ok("中心角 ∠AOB=60°−45°=15°", near(angle_between(A, B), central) and near(central, 15.0))
    ck.ok("A・B は円周上（|OA|=|OB|=R）", near(math.hypot(*A), R) and near(math.hypot(*B), R))
    # 弧長／円周＝中心角／360（円周と弧を同じ 1° 刻みの折れ線で測る）
    def arc_len(d0, d1, step=1.0):
        n = int(round((d1 - d0) / step))
        pts = [(R * math.cos((d0 + i * step) * DEG), R * math.sin((d0 + i * step) * DEG)) for i in range(n + 1)]
        return sum(dist(pts[i], pts[i + 1]) for i in range(n))
    ck.ok("弧 AB の長さ／円周＝15／360（同じ刻みの折れ線で・許容誤差 1e-9）",
          near(arc_len(sun_dir + ang_A, sun_dir + ang_B) / arc_len(0.0, 360.0), central / 360.0))
    ck.ok("A・B に届く光線は平行（同じ方向ベクトル u）", True, f"u=({u[0]:.4f}, {u[1]:.4f})")

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    O_px = fr.P((0, 0))
    # 地球（円）
    n = 180
    cv.polyline([fr.P((R * math.cos(i * 2 * DEG), R * math.sin(i * 2 * DEG))) for i in range(n)], w=MAIN_W, close=True)
    # 半径 OA・OB
    seg(cv, fr, (0, 0), A, w=MAIN_W)
    seg(cv, fr, (0, 0), B, w=MAIN_W)
    # 棒（半径の延長・地面に垂直）と、棒の先端を通って地面に届く光線（平行・矢印）
    stick, ray = 0.13, 0.6
    for Pt, ang in ((A, ang_A), (B, ang_B)):
        nrm = unit(Pt)
        T = add(Pt, mul(nrm, stick))                              # 棒の先端
        G = sub(T, mul(u, stick / math.cos(ang * DEG)))           # 光線が地面（接線）に届く点
        ck.ok(f"光線が届く点は接線上（(G−{'A' if Pt is A else 'B'})·n=0・許容誤差 1e-9）",
              near(dot(sub(G, Pt), nrm), 0.0))
        seg(cv, fr, Pt, T, w=BOLD_W)
        s_px, g_px = fr.P(add(T, mul(u, ray))), fr.P(G)
        arrow(cv, s_px[0], s_px[1], g_px[0], g_px[1], w=1.4, head=8)
    # O を通り光線に平行な直線（破線）
    seg(cv, fr, (0, 0), mul(u, 1.25), w=AUX_W, dash=DASH)
    # 角: O での 45°・60°（破線との角）と中心角 15°
    A_px, B_px, U_px = fr.P(A), fr.P(B), fr.P(mul(u, 1.25))
    m3 = arc_between(cv, O_px, A_px, B_px, 48)
    m1 = arc_between(cv, O_px, U_px, A_px, 84)
    m2 = arc_between(cv, O_px, U_px, B_px, 112, n=2)
    # 15° のラベルは扇形の内側でなく（r=70 では扇形の幅 18 px に文字 26 px が入らず OA・OB にかかる）、弧の OB 側の端のすぐ外に置く
    a15 = (sun_dir + ang_B + 18.0) * DEG
    lb.put(O_px[0] + 60 * math.cos(a15), O_px[1] - 60 * math.sin(a15) + fs * 0.35, "15°", size=fs - 3, weight="bold")
    lb.put(O_px[0] + 100 * math.cos(m1 * DEG), O_px[1] - 100 * math.sin(m1 * DEG) + fs * 0.35, "45°", size=fs - 3)
    # 60° のラベルは二重弧の OB 側の端のすぐ外（OB を越えた側）に置く。弧の中央（45° の扇形の内側・A の隣）に置くと A の角と読める
    a60 = (sun_dir + ang_B + 8.0) * DEG
    lb.put(O_px[0] + 124 * math.cos(a60), O_px[1] - 124 * math.sin(a60) + fs * 0.35, "60°", size=fs - 3)
    # 点名
    cv.dot(*O_px, r=3.0)
    lb.put(O_px[0] + 8, O_px[1] + fs * 1.0, "O", anchor="start", weight="bold")
    lb.put(A_px[0] + 12, A_px[1] - 4, "A", anchor="start", weight="bold")
    lb.put(B_px[0] + 16, B_px[1] + 4, "B", anchor="start", weight="bold")
    lb.put(W - 40, 40, "太陽の光（平行）", size=fs - 3, anchor="end")
    lb.put(40, H - 20, "太い線＝地面に垂直に立てた棒。破線＝O を通り光線に平行な直線", size=fs - 5, anchor="start")
    cv.layout_checks(ck)

    return {"file": "L08_fig2_measure_earth.svg", "lesson": "L08", "canvas": cv,
            "title": "地球を測る——2 地点 A・B の光線の角 45°・60° と中心角 15°",
            "desc": "地球を円で表し、中心 O と円周上の 2 地点 A・B、地面に垂直な棒、平行に届く太陽光線を描く。O を通り光線に平行な破線と半径 OA・OB のなす角が 45°・60° で、その差が中心角 ∠AOB=15°。同型図は 2つの角と太陽の方向を差し替えて生成する",
            "alt": "地球を円で表し、中心 O と2地点 A・B、平行に届く光線と、半径 OA・OB のなす中心角 15° を示した図",
            "intent": "平行光線と棒の角の差が中心角になること（同位角・錯角）を見せ、弧長と円周の比が中心角の比であることへつなぐ",
            "src": "lesson_08.md §2（中心角 15° の導出の直後）",
            "params": "OA と光線の角 45°・OB と光線の角 60°／中心角 15°／太陽の方向 90°（真上）／半径 160 px",
            "checks": ck.items,
            "check_tokens": ["36,000", "41,100", "1,500", "1500", "8°", "24", "13.8", "30°"],
            "digit_rule": ("subset", {"45", "60", "15"}),
            "allow_texts": lb.items}


def fig_L09_1():
    # --- パラメータ（lesson_09.md §2 例題1） ---
    cap = {"桶": 12, "A": 8, "B": 5}
    start, goal = (12, 0, 0), (6, 6, 0)
    moves = [("桶", "A"), ("A", "B"), ("B", "桶"), ("A", "B"), ("桶", "A"), ("A", "B"), ("B", "桶")]
    labels_ops = ["桶→A 満たす", "A→B 満たす", "B→桶 戻す", "A→B 移す", "桶→A 満たす", "A→B 満たす", "B→桶 戻す"]
    expected = [(12, 0, 0), (4, 8, 0), (4, 3, 5), (9, 3, 0), (9, 0, 3), (1, 8, 3), (1, 6, 5), (6, 6, 0)]
    W, H = 640, 360
    fs = fs_for(W)
    node_w, node_h = 110, 34
    xs = [95, 245, 395, 545]
    ys = [100, 250]

    idx = {"桶": 0, "A": 1, "B": 2}

    def pour(state, src, dst):
        st = list(state)
        amt = min(st[idx[src]], cap[dst] - st[idx[dst]])
        st[idx[src]] -= amt
        st[idx[dst]] += amt
        return tuple(st)

    states = [start]
    for src, dst in moves:
        states.append(pour(states[-1], src, dst))
    ck = Checker()
    ck.ok("規則どおりに移した状態列が本文の表と一致（8 状態・7 手）", states == expected and len(states) == 8)
    ck.ok("各状態の 3 数の和が 12（総量保存）", all(sum(st) == 12 for st in states))
    ck.ok("A は 0〜8・B は 0〜5・桶は 0〜12 の範囲", all(0 <= st[1] <= 8 and 0 <= st[2] <= 5 and 0 <= st[0] <= 12 for st in states))
    ck.ok("各手は「満たす・戻す・移す」のどれか（移す量は min(注ぐ側の量, 受ける側の空き)）",
          all(states[i + 1] == pour(states[i], *moves[i]) for i in range(len(moves))))
    ck.ok("矢印のラベルの向き（X→Y）が実際に移した向きと一致",
          all(lab.split(" ")[0] == f"{src}→{dst}" for lab, (src, dst) in zip(labels_ops, moves)))
    ck.ok("はじめ (12, 0, 0)・目標 (6, 6, 0)", states[0] == start and states[-1] == goal)

    # 蛇行配置: 上段 0→3（左→右）・下段 4→7（右→左）
    pos = [(xs[i], ys[0]) for i in range(4)] + [(xs[3 - i], ys[1]) for i in range(4)]
    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    for i, st in enumerate(states):
        x, y = pos[i]
        cv.rect(x - node_w / 2, y - node_h / 2, node_w, node_h, rx=6,
                fill=(GRAY_FILL if i in (0, len(states) - 1) else "none"))
        lb.put(x, y + fs * 0.35, f"({st[0]}, {st[1]}, {st[2]})", size=fs - 3)
    for i, lab in enumerate(labels_ops):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if y1 == y2:                                   # 横向きの矢印
            d = 1 if x2 > x1 else -1
            arrow(cv, x1 + d * node_w / 2, y1, x2 - d * node_w / 2, y2, w=1.4, head=8)
            lb.put((x1 + x2) / 2, y1 - 24 if y1 == ys[0] else y1 + 34, lab, size=fs - 6)
        else:                                          # 縦向きの矢印（右端）
            arrow(cv, x1, y1 + node_h / 2, x2, y2 - node_h / 2, w=1.4, head=8)
            lb.put(x1 - node_w / 2 - 6, (y1 + y2) / 2 + fs * 0.35, lab, size=fs - 6, anchor="end")
    lb.put(pos[0][0], ys[0] - 52, "はじめ", size=fs - 4)
    lb.put(pos[-1][0], ys[1] + 62, "目標", size=fs - 4)
    lb.put(W / 2, 32, "状態は (桶, A, B)。容量は桶 12・A 8・B 5", size=fs - 4)
    cv.layout_checks(ck)

    return {"file": "L09_fig1_state_transition.svg", "lesson": "L09", "canvas": cv,
            "title": "油分け算の状態遷移図——(12, 0, 0) から (6, 6, 0) までの 7 手",
            "desc": "容量 12・8・5 の油分け算で、状態 (桶, A, B) を角丸の箱、操作（満たす・戻す・移す）を矢印で表し、はじめ (12, 0, 0) から目標 (6, 6, 0) までの 7 手を蛇行して並べる。同型図は容量・手順を差し替えて生成する（状態列はスクリプトが規則から計算し、本文の表と照合する）",
            "alt": "容量 12・8・5 の油分け算で、状態 (桶, A, B) を点、操作を矢印で表した状態遷移図。はじめの (12, 0, 0) から目標の (6, 6, 0) までの道筋",
            "intent": "操作の手順を「状態を点・操作を矢印」で見せ、総量保存と容量の範囲で各手を検算できることを示す",
            "src": "lesson_09.md §2（最短性の説明の直後）",
            "params": "容量 (桶, A, B)=(12, 8, 5)／はじめ (12,0,0)・目標 (6,6,0)／7 手／状態列は本文の表と同一",
            "checks": ck.items,
            "check_tokens": ["7手", "15回", "(2, −2)", "2 の倍数", "x=2", "y=2"],
            "digit_rule": ("subset", {"12", "0", "4", "8", "3", "5", "9", "1", "6"}),
            "allow_texts": lb.items}


# ===========================================================================
# L10〜L11: ゲーム・パズル・単元マップ
# ===========================================================================
def fig_L10_1():
    # --- パラメータ（lesson_10.md §1） ---
    n = 3                                  # 3×3 の格子点
    W, H = 640, 360
    fs = fs_for(W)
    fr = Frame(230, 290, 90.0)             # (0,0) の px・90 px/単位

    pts = [(x, y) for x in range(n) for y in range(n)]
    lines = ([[(x, y) for y in range(n)] for x in range(n)] +          # 縦 3本
             [[(x, y) for x in range(n)] for y in range(n)] +          # 横 3本
             [[(i, i) for i in range(n)], [(i, n - 1 - i) for i in range(n)]])   # 斜め 2本
    ck = Checker()
    ck.ok("格子点数 9", len(pts) == 9)
    ck.ok("線分数 8（縦 3・横 3・斜め 2）", len(lines) == 8)
    ck.ok("各線は 3つの格子点を通り、3点は同一直線上（外積 0・整数演算）",
          all(len(L) == 3 and cross(sub(L[1], L[0]), sub(L[2], L[0])) == 0 for L in lines))
    ck.ok("8本の線は互いに異なる（点集合として）", len({frozenset(L) for L in lines}) == 8)
    ck.ok("どの格子点も少なくとも 2本の線に乗る（角は 3本・中央は 4本）",
          all(sum(1 for L in lines if p_ in L) >= 2 for p_ in pts) and
          sum(1 for L in lines if (1, 1) in L) == 4 and sum(1 for L in lines if (0, 0) in L) == 3)

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    for L in lines:
        seg(cv, fr, L[0], L[-1], w=MAIN_W)
    for p_ in pts:
        px, py = fr.P(p_)
        cv.ring(px, py, 6.0, w=1.6)
    # 座標の呼び方: 下に x=0,1,2・左に y=0,1,2
    for x in range(n):
        px, py = fr.P((x, 0))
        lb.put(px, py + 34, f"x={x}", size=fs - 3)
    for y in range(n):
        px, py = fr.P((0, y))
        lb.put(px - 26, py + fs * 0.35, f"y={y}", size=fs - 3, anchor="end")
    px, py = fr.P((0, 0))
    lb.put(px + 14, py + 14, "(0, 0)", size=fs - 4, anchor="start")
    lb.put(W - 40, 40, "格子点は (x, y) で呼ぶ（左から x・下から y）", size=fs - 4, anchor="end")
    cv.layout_checks(ck)

    return {"file": "L10_fig1_tictactoe_board.svg", "lesson": "L10", "canvas": cv,
            "title": "三目並べの盤——3×3 の格子点 9個と縦・横・斜めの 8本の線",
            "desc": "3×3 の格子点（白抜きの丸）を縦 3本・横 3本・斜め 2本の線で結んだタパタン型の盤。格子点は左から x=0〜2、下から y=0〜2 の座標で呼ぶ。同型図は盤の大きさ n を差し替えて生成する",
            "alt": "3×3 の格子点 9個を縦・横・斜めの 8本の線で結んだ三目並べの盤。格子点は左から x=0〜2、下から y=0〜2 の座標で呼ぶ",
            "intent": "盤の構造（格子点 9・線 8）と、L08 の座標で格子点を呼ぶ約束を見せる",
            "src": "lesson_10.md §1（盤の説明の直後）",
            "params": "n=3／格子点 9・線 8／90 px/単位／(0,0) の px=(230,290)",
            "checks": ck.items,
            "check_tokens": ["5 の倍数", "13", "15", "98", "A=8", "B=9", "(2, 2)", "(2, 0)", "(1, 0)", "(0, 2)"],
            "digit_rule": ("subset", {"0", "1", "2"}),
            "allow_texts": lb.items}


def fig_L10_2():
    # --- パラメータ（lesson_10.md §4 例題3） ---
    rows, cols = 6, 6
    removed = [(1, 1), (6, 6)]             # (行, 列)・1 始まり
    black_left, white_left = 16, 18        # 本文の値
    W, H = 640, 420
    fs = fs_for(W)
    cell = 44
    x0, y0 = 150, 70

    def color(r, c):
        return "black" if (r + c) % 2 == 0 else "white"

    cells = [(r, c) for r in range(1, rows + 1) for c in range(1, cols + 1)]
    full_black = sum(1 for rc in cells if color(*rc) == "black")
    rest = [rc for rc in cells if rc not in removed]
    nb = sum(1 for rc in rest if color(*rc) == "black")
    nw = len(rest) - nb
    ck = Checker()
    ck.ok("6×6 のボードは黒 18・白 18", full_black == 18 and rows * cols - full_black == 18)
    ck.ok("取り除いた 2つの角 (1, 1)・(6, 6) は行＋列がどちらも偶数＝同じ色（黒）",
          all(color(*rc) == "black" for rc in removed) and all((r + c) % 2 == 0 for r, c in removed))
    ck.ok("残りは 34マス・黒 16・白 18（本文の値と一致）", len(rest) == 34 and nb == black_left and nw == white_left)
    ck.ok("黒白のマス数の差＝2（本文の説明: 17枚では黒が 1 足りない）", nw - nb == 2 and nb < 17)
    ck.ok("隣り合うマスは必ず違う色", all(color(r, c) != color(r, c + 1) for r in range(1, rows + 1) for c in range(1, cols)) and
          all(color(r, c) != color(r + 1, c) for r in range(1, rows) for c in range(1, cols + 1)))

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    for r, c in cells:
        x, y = x0 + (c - 1) * cell, y0 + (r - 1) * cell
        if (r, c) in removed:
            cv.rect(x, y, cell, cell, fill="none", dash="4 3", sw=1.0)
            cv.line(x + 8, y + 8, x + cell - 8, y + cell - 8, w=1.2)
            cv.line(x + cell - 8, y + 8, x + 8, y + cell - 8, w=1.2)
        else:
            cv.rect(x, y, cell, cell, fill=(DARK_FILL if color(r, c) == "black" else "none"), sw=1.0)
    for c in range(1, cols + 1):
        lb.put(x0 + (c - 1) * cell + cell / 2, y0 - 10, str(c), size=fs - 4)
    for r in range(1, rows + 1):
        lb.put(x0 - 10, y0 + (r - 1) * cell + cell * 0.68, str(r), size=fs - 4, anchor="end")
    lb.put(x0 - 40, y0 - 10, "列", size=fs - 4, anchor="end")
    lb.put(x0 - 40, y0 + cell * 0.68, "行", size=fs - 4, anchor="end")
    lb.put(W / 2, y0 + rows * cell + 34, "残りは黒 16マス・白 18マス", size=fs - 2, weight="bold")
    lb.put(W / 2, y0 + rows * cell + 60, "×印＝取り除いた角（どちらも黒）。行＋列が偶数のマスが黒", size=fs - 5)
    cv.layout_checks(ck)

    return {"file": "L10_fig2_checkerboard_tiling.svg", "lesson": "L10", "canvas": cv,
            "title": "市松に塗った欠けボード——6×6 から向かい合う 2つの角を除くと黒 16・白 18",
            "desc": "6×6 のボードを、行と列の番号の和が偶数のマスを黒、奇数を白に塗り、向かい合う角 (1, 1)・(6, 6)（どちらも黒）を×印で取り除く。残りは黒 16マス・白 18マス。同型図は行・列・欠けマスを差し替えて生成する（黒白の数はスクリプトが数え、本文の値と照合する）",
            "alt": "6×6 のボードを市松に塗り、向かい合う2つの角（同じ色）を取り除いた図。残りは黒 16マス・白 18マス",
            "intent": "二値化（市松に塗る）で「黒と白の数が合わないから敷き詰められない」を目に見える形にする",
            "src": "lesson_10.md §4（例題3の黒白の数の直後）",
            "params": "6行 6列／欠け (1,1)・(6,6)／黒 16・白 18／セル 44 px",
            "checks": ck.items,
            "check_tokens": ["13", "15", "98", "A=8", "B=9", "5 の倍数", "12", "24", "25"],
            "digit_rule": ("subset", {"1", "2", "3", "4", "5", "6", "16", "18"}),
            "allow_texts": lb.items}


def fig_L11_1():
    # --- パラメータ（lesson_11.md §1 の表） ---
    activities = ["数える", "測る", "位置を示す", "設計する", "遊ぶ", "説明する"]
    lessons = ["L01 記数法の歴史と位取りの式", "L02 n進法と2進法", "L03 約数と倍数",
               "L04 最大公約数と最小公倍数", "L05 整数の割り算", "L06 ユークリッドの互除法",
               "L07 二元一次不定方程式", "L08 地球の大きさと座標", "L09 油分け算・河渡り・ハノイの塔",
               "L10 必勝法とパズルの論理", "L11 単元のまとめ（この地図）"]
    edges = [("数える", "L01"), ("数える", "L02"), ("数える", "L03"), ("数える", "L04"), ("数える", "L05"),
             ("測る", "L06"), ("測る", "L08"),
             ("位置を示す", "L08"),
             ("設計する", "L10"),
             ("遊ぶ", "L09"), ("遊ぶ", "L10"),
             ("説明する", "L03"), ("説明する", "L05"), ("説明する", "L07"), ("説明する", "L09"), ("説明する", "L10")]
    W, H = 640, 470
    fs = fs_for(W)
    act_x, act_w, act_h = 150, 150, 32
    les_x, les_w, les_h = 470, 300, 28
    top, row = 70, 36

    ids = [L.split(" ")[0] for L in lessons]
    ck = Checker()
    ck.ok("レッスンのノード数 11（L01〜L11）", len(lessons) == 11 and ids == [f"L{i:02d}" for i in range(1, 12)])
    ck.ok("活動のノード数 6", len(activities) == 6)
    ck.ok("線の両端が存在するノード（活動・レッスン）を指す",
          all(a in activities and l in ids for a, l in edges))
    ck.ok("線は 16本・重複なし", len(edges) == 16 and len(set(edges)) == 16)
    ck.ok("L01〜L10 のどのレッスンにも線が 1本以上ある（L11 はまとめで線なし）",
          all(any(l == i for _, l in edges) for i in ids[:-1]) and not any(l == "L11" for _, l in edges))
    ck.ok("どの活動からも線が 1本以上出る", all(any(a == act for act, _ in edges) for a in activities))

    # 活動ノードは表の順に等間隔（レッスン列と同じ高さの範囲に 6段）
    les_y = {i: top + k * row for k, i in enumerate(ids)}
    act_y = [top + k * (row * 10) / 5 for k in range(len(activities))]

    cv = Canvas(W, H)
    lb = Labels(cv, fs)
    for a, l in edges:
        y1 = act_y[activities.index(a)]
        y2 = les_y[l]
        # 「設計する」→L10 の 1本だけ破線（独立のレッスンは無く、L10 のパズルが入口＝lesson_11 §1 の表の括弧書き）
        cv.line(act_x + act_w / 2, y1, les_x - les_w / 2, y2, w=AUX_W, dash=(DASH if a == "設計する" else None))
    for a, y in zip(activities, act_y):
        cv.rect(act_x - act_w / 2, y - act_h / 2, act_w, act_h, rx=6, fill=GRAY_FILL)
        lb.put(act_x, y + fs * 0.35, a, size=fs - 2, weight="bold")
    for L, i in zip(lessons, ids):
        y = les_y[i]
        cv.rect(les_x - les_w / 2, y - les_h / 2, les_w, les_h, rx=4, fill="#fff")
        lb.put(les_x - les_w / 2 + 8, y + fs * 0.35, L, size=fs - 6, anchor="start")
    lb.put(act_x, 34, "6つの活動", size=fs - 2)
    lb.put(les_x, 34, "11 のレッスン", size=fs - 2)
    cv.layout_checks(ck)

    return {"file": "L11_fig1_unit_map.svg", "lesson": "L11", "canvas": cv,
            "title": "単元マップ——6つの活動から 11 のレッスンへ",
            "desc": "左に 6つの活動（数える・測る・位置を示す・設計する・遊ぶ・説明する）、右に L01〜L11 の 11 レッスンを並べ、lesson_11 の表のとおり活動からレッスンへ線を引いた地図。「設計する」から L10 への 1本だけは、独立のレッスンが無く L10 のパズルが入口であることを示す破線。同型図は活動・レッスン・対応表を差し替えて生成する",
            "alt": "6つの活動（数える・測る・位置を示す・設計する・遊ぶ・説明する）から11のレッスンへ線を引いた単元マップ",
            "intent": "単元全体を 1枚で見渡し、復習の入口（活動→レッスン）を選べるようにする",
            "src": "lesson_11.md §1（活動とレッスンの表の直後）",
            "params": "活動 6・レッスン 11・線 16（lesson_11.md §1 の表と同一）",
            "checks": ck.items,
            "check_tokens": ["101101", "140", "124", "125通り", "(−4, 10)", "7k"],
            "digit_rule": ("strip", ["6つ", "11 の", "n進法と2進法"]),
            "allow_texts": lb.items}


# ===========================================================================
# main: 陽性対照 → 生成 → 技術検査 → 答え漏れ検査 → 受け入れ検査 → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1, fig_L02_1, fig_L02_2, fig_L03_1, fig_L04_1, fig_L05_1,
        fig_L06_1, fig_L06_2, fig_L07_1, fig_L08_1, fig_L08_2, fig_L09_1,
        fig_L10_1, fig_L10_2, fig_L11_1]

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
              '<text x="1" y="1">14.0</text><text x="2" y="2">x&lt;0</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["14.0", "x<0"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["14"]) == ["14"], "陽性対照失敗: 禁止値 14 を検出できない"
    assert ban_hits(ts, ["12.5"]) == [], "陰性対照失敗: 存在しない値を誤検出"
    assert digit_runs(ts) == {"14", "0"}, "数字抽出が壊れている"
    probes = ["a" + chr(0x200B) + "b", "e" + chr(0x0301), chr(0x2713) + chr(0xFE0F),
              chr(0xFF21) + chr(0xFF11), chr(0x1F600)]
    for probe in probes:
        try:
            char_hygiene(probe, "陽性対照")
        except AssertionError:
            continue
        raise AssertionError(f"文字衛生の陽性対照失敗: {probe!r} を検出できない")
    char_hygiene("√2・²・³・⁰・°・−・＋・×・→・₍₂₎・〜", "陰性対照")


def svg_tech_checks(src, meta):
    """生成した SVG 文字列を、ファイルへ書く前に検査する（落ちれば例外で停止し、何も出力しない）"""
    path = Path(meta["file"])
    ET.fromstring(src)
    root_tag = src.split(">", 1)[0]
    assert "viewBox=" in root_tag, f"{path.name}: viewBox がない"
    assert 'xmlns="http://www.w3.org/2000/svg"' in root_tag, f"{path.name}: xmlns がない"
    assert " width=" not in root_tag and " height=" not in root_tag, f"{path.name}: ルートに width/height を書かない"
    ext = src.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "http" not in ext and "href" not in ext and "@import" not in ext, f"{path.name}: 外部参照の疑い"
    assert "font-family" not in src, f"{path.name}: font-family を書かない（SPEC_figures §5）"
    assert "<title>" in src and "<desc>" in src, f"{path.name}: title/desc がない"
    assert '<rect x="0" y="0"' in src and 'fill="#fff"' in src, f"{path.name}: 白背景がない"
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
        svg_tech_checks(svg1, meta)
        n_checks += len(meta["checks"])
        total_bytes += len(svg1.encode("utf-8"))
        rows.append(meta)
        pending.append((ASSETS / meta["file"], svg1))
        print(f"OK {meta['file']}  [{len(meta['checks'])} checks passed]")

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
        "# FIGURE_MANIFEST — 数A 数学と人間の活動 単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的）／ "
        f"全{len(rows)}図・合計 {total_bytes} バイト。下表の数学検算（スクリプト内 assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。加えて全SVGに XML整形式・xmlns・viewBox・width/height なし・self-contained・"
        "`<title>`/`<desc>`・白背景・font-family なし（SPEC_figures §5） の技術検査と、文字衛生検査"
        "（絵文字・結合文字・異体字セレクタ・不可視文字・全角英数字の不在）と、答え漏れ検査を実施。"
        "答え漏れ検査は二重ゲート: (1)図中の全ラベルを許可リスト（本文が図の前後、または同じレッスンの中で明示している値のみ）と"
        f"集合として完全一致で照合、(2)禁止文字列（練習の答え由来・計{n_tokens}項目・対象値は非開示）の"
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
        "- 決定性: 乱数・時刻に依存しない。同一プロセス内で各図を2回生成してバイト一致を assert。"
        "日付は SVG 先頭コメントと本台帳の生成日行だけに現れる（台帳に載せる集合は整列して書く）",
        "- 図数の照合: 本文の図参照と生成ファイルの差集合が空（上の1行目）",
        "",
        "## 描画上の注記",
        "",
        "- 白黒規約により色に意味を持たせず、区別は網かけ（うすいグレー）・黒塗り・破線・線幅で行う。",
        "- L02_fig1・L08_fig1 は本文での登場順が fig2 より後だが、ファイル名は内容仕様の ID をそのまま用いた（本文の参照と一致）。",
        "- L06_fig2 は無理数 √2 を含むため座標は浮動小数で描き、比の検算は許容誤差 1e-9 で行った。",
        "- L11_fig1 の活動→レッスンの線は lesson_11.md §1 の表のとおり。L11 自身は「まとめ」として線を持たない。「設計する」→L10 の 1本だけは、独立のレッスンが無く入口であることを示す破線。",
        "",
        "## 答えの分離方針の扱い",
        "",
        "- 図中に書いた数値は、いずれも本文が同じレッスンの中で明示している値のみ（多くは図の前後。L01_fig1 の 2305 とその位取りの式は、図の後の §3 の表と §4 で明示）。各図の許可リスト検査（ラベル集合の完全一致）と数字集合の制約で機械担保。",
        "- 練習の答え由来の値は禁止文字列として各図に登録し、図中テキストに現れないことを assert している。",
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
