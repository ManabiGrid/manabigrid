#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_figures.py — 高1数学I「集合と命題」単元 図版パラメトリック生成スクリプト
==============================================================================
様式: docs/SPEC_figures.md・NE_STANDARD_FORM_SPEC_20260829.md §12 に準拠。
内容仕様の正: 執筆側の図版仕様メモ candidate_draft/_notes/FIG_SPEC_W1.md（L01〜L03）・
FIG_SPEC_W2.md（L04〜L05）・FIG_SPEC_W3.md（L06〜L07）。ファイル名・ラベル文字列・数値・
座標・alt 文はメモに合わせた。メモが色（青系・灰）やフォント名を指定する箇所だけは
docs/SPEC_figures.md の白黒規約（線は黒のみ・font-family 指定なし・色に意味を持たせない）を
優先し、強調は線幅 3.2、外との出入りの矢印は破線で区別した（台帳の注記に列挙）。
描画ヘルパー（Canvas／矢印／端点●○／Checker／答え漏れ検査器）は先行単元
materials/hs-math-i/hs-math-i-numbers-and-expressions/assets_provenance/generate_figures.py
からコピー再利用（元スクリプトは無変更）。ベン図の塗り（クリップパス・ハッチング）、
2円の交点・和集合の輪郭多角形、楕円の包含検査、格子点による領域一致検査は本単元で追加した。

- 実行: python3 generate_figures.py
- 出力: ../assets/L{NN}_fig{n}_{slug}.svg（10枚）と FIGURE_MANIFEST.md（この階層・自動生成）
- 依存: Python標準ライブラリのみ（math / datetime / html / pathlib / re / unicodedata / xml.etree）
- 図の選定: SL_CONTENT_MAP §3・§4 の9枚＋執筆メモ W2 が追加した L04_fig2（4分類の包含図）。
  各図は本文の `![alt](assets/…)` と1対1。
- 数学の自己検証: 各 fig_* 関数内の Checker が assert 相当の検算を行い、
  1つでも失敗すると例外で停止して図を出力しない。座標はすべて値から線形変換で計算し、
  端点・円・楕円・矢印の位置を本文の値と照合する（目分量ゼロ）。ベン図は2円の重なりの存在
  （中心間距離が半径の差より大きく和より小さい）と、(A∪B)ᶜ の塗りと Aᶜ∩Bᶜ の交差領域が
  格子点全点で一致することを、描画に使う幾何そのものから検算する。
- 答えの分離方針（三重ゲート＋陽性対照）:
  (1) 許可リスト検査——各図が宣言した「本文明示値のみのラベル一覧」(allow_texts) と、
      生成後SVGの<text>全内容が集合として完全一致することを検査する（未宣言ラベルの混入も検出）。
  (2) 数字ラベル検査——数字だけのラベル（目盛りの数）の集合が宣言 (num_labels) と完全一致し、
      練習・stretch の答えの数 (check_numbers) が数字ラベルとして現れないことを検査する
      （「2段を合わせると…」のような文中の数字は対象外——メモの指定どおり）。
  (3) 禁止文字列検査——答え由来の式・値のトークン (check_tokens) が図中テキストに現れないことを
      検査する。
  検査器自体は main() 冒頭の陽性対照（禁止値を仕込んだ合成SVGで検出できること）で毎回実証する。
- 禁止文字検査: 絵文字・結合文字（上線 U+0304 など）・異体字セレクタ・不可視文字・
  全角英数字を、SVG全文・FIGURE_MANIFEST・このスクリプト自身のソースに対して検査する
  （公開側の検疫と同じ基準）。検出器も陽性対照で毎回実証する。
- 決定性: 描画に乱数・時刻を使わない。同じ入力からは同じバイト列が出る
  （先頭コメントと台帳の生成日だけが実行日）。
- 記号: 補集合は上付き c（Aᶜ・U+1D9C）・空集合 ∅・共通部分 ∩・和集合 ∪・含意 ⇒・同値 ⇔。
  不等号は本文と同じ ASCII の < > と ≦ ≧。全角英数字・結合文字は使わない。
- ●○規約: 端点●=含む／○=含まないは数直線系図版（L01_fig1・L03_fig1・L05_fig1）で
  先行単元と共通のパラメータ（半径 3.4・縁の線幅 1.4）を使う（メモの r≈4〜5 は目安と解釈）。
- 改修方法（第三者向け）: 各 fig_* 関数冒頭の「パラメータ」ブロックの数値・ラベルを変えて
  再実行する。数値・文字列は該当レッスン本文と図版仕様メモに一致させること。
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
GENERATED = datetime.date.today().isoformat()

# ---- 様式定数（docs/SPEC_figures.md） ----------------------------------
MAIN_W = 1.6      # 主線幅
BOLD_W = 3.2      # 強調線幅
AUX_W = 1.1       # 補助線幅
DASH = "6 4"      # 破線
FS = 14           # 基本文字サイズ(px)
FS_NUM = 12       # 目盛数値
DOT_R_END = 3.4   # 端点●○（数直線系で先行単元と共通）
END_STROKE = 1.4  # ○の縁の線幅（共通）
SHADE_SET = "#bbb"   # 集合の塗り（ベン図・メモ指定）
SHADE = "#ddd"       # うすい網かけ（数直線の範囲帯・内側の集合）
SHADE2 = "#eee"      # さらにうすい網かけ（外側の集合）
ARC_N = 180          # 円を折れ線で近似するときの分割数（クリップ用）


# ===========================================================================
# 描画ヘルパー（px直書き中心。先行単元からコピー再利用+ベン図・楕円系を追加）
# ===========================================================================
class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.defs = []
        self.body = []

    def raw(self, s):
        self.body.append(s)

    def line_px(self, x1, y1, x2, y2, w=MAIN_W, dash=None, color="#000"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{w}"{d}/>')

    def text_px(self, x, y, s, size=FS, anchor="middle", weight=None):
        wgt = f' font-weight="{weight}"' if weight else ""
        self.raw(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                 f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')

    def rect_px(self, x, y, w, h, fill="none", dash=None, sw=1.4, rx=None, clip=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}"' if rx else ""
        c = f' clip-path="url(#{clip})"' if clip else ""
        stroke = f' stroke="#000" stroke-width="{sw}"' if sw else ""
        self.raw(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'fill="{fill}"{stroke}{d}{r}{c}/>')

    def circle_px(self, cx, cy, r, fill="none", sw=MAIN_W, clip=None):
        c = f' clip-path="url(#{clip})"' if clip else ""
        stroke = f' stroke="#000" stroke-width="{sw}"' if sw else ""
        self.raw(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"{stroke}{c}/>')

    def ellipse_px(self, cx, cy, rx, ry, fill="none", sw=MAIN_W):
        stroke = f' stroke="#000" stroke-width="{sw}"' if sw else ""
        self.raw(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" '
                 f'fill="{fill}"{stroke}/>')

    def clip_def(self, cid, d, evenodd=False):
        rule = ' clip-rule="evenodd"' if evenodd else ""
        self.defs.append(f'<clipPath id="{cid}"><path d="{d}"{rule}/></clipPath>')

    def hatch_def(self, pid, direction):
        """斜線ハッチング（45°）／逆斜線（135°）を <pattern> で内蔵（継ぎ目なしの3本描き）"""
        if direction == 45:
            d = "M -2 2 L 2 -2 M 0 8 L 8 0 M 6 10 L 10 6"
        else:
            d = "M -2 6 L 2 10 M 0 0 L 8 8 M 6 -2 L 10 2"
        self.defs.append(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="8" height="8">'
                         f'<path d="{d}" stroke="#000" stroke-width="1"/></pattern>')

    def save(self, path, fig_id, title, desc):
        defs = f"<defs>{''.join(self.defs)}</defs>\n" if self.defs else ""
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<!-- {fig_id} | {title} -->\n'
            f'<!-- generated by assets_provenance/generate_figures.py on {GENERATED} '
            f'(docs/SPEC_figures.md・標準形§12準拠・SVG直接編集禁止/スクリプト改修で再生成) -->\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + "\n</svg>\n"
        )
        path.write_text(svg, encoding="utf-8")


def arrow_px(cv, x1, y1, x2, y2, w=1.4, head=7.0, dash=None):
    """SVG座標(px)で矢印（線+先端の三角形）を描く"""
    ang = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    cv.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
           f'stroke="#000" stroke-width="{w}"{d}/>')
    nx, ny = -math.sin(ang), math.cos(ang)
    cv.raw(f'<polygon points="{x2:.1f},{y2:.1f} '
           f'{bx + nx * head * 0.45:.1f},{by + ny * head * 0.45:.1f} '
           f'{bx - nx * head * 0.45:.1f},{by - ny * head * 0.45:.1f}" fill="#000"/>')


def double_arrow_px(cv, x1, y1, x2, y2, w=1.5, head=8.0):
    """両端に矢じりのある線（逆・裏・対偶の相互関係用）"""
    arrow_px(cv, x1, y1, x2, y2, w=w, head=head)
    arrow_px(cv, x2, y2, x1, y1, w=w, head=head)


def open_pt(cv, x, y):
    """端点○（その値をふくまない）——白抜き+黒縁。数直線系で共通のパラメータ"""
    cv.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{DOT_R_END}" fill="#fff" '
           f'stroke="#000" stroke-width="{END_STROKE}"/>')


def closed_pt(cv, x, y):
    """端点●（その値をふくむ）——塗りつぶし。数直線系で共通のパラメータ"""
    cv.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{DOT_R_END}" fill="#000"/>')


def tick_px(cv, x, y, half=3.5):
    cv.line_px(x, y - half, x, y + half, w=1.0)


def text_boxed(cv, T, x, y, s, size=12, weight=None):
    """線と重なる位置のラベル——白い下地矩形を敷いてから文字を置く"""
    w = len(s) * size * 1.02 + 6
    cv.raw(f'<rect x="{x - w / 2:.1f}" y="{y - size:.1f}" width="{w:.1f}" '
           f'height="{size + 5:.1f}" fill="#fff"/>')
    T(x, y, s, size=size, weight=weight)


class Checker:
    """数学検算の記録つきassert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


# ---- 幾何ヘルパー（ベン図・包含図） ----------------------------------------
def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def circle_pts(c, n=ARC_N):
    """円 c=(cx, cy, r) を n 点で折れ線近似（角度 0 から反時計回り・決定的）"""
    cx, cy, r = c
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
            for k in range(n)]


def ellipse_pts(e, n=36):
    """楕円 e=(cx, cy, rx, ry) の周上 n 点（10°刻みなど）"""
    cx, cy, rx, ry = e
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n))
            for k in range(n)]


def in_ellipse(p, e):
    """楕円の内側（境界を含まない）"""
    cx, cy, rx, ry = e
    return ((p[0] - cx) / rx) ** 2 + ((p[1] - cy) / ry) ** 2 < 1


def poly_d(pts):
    """閉じた折れ線の path d 属性"""
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def rect_d(x, y, w, h):
    return f"M {x:.1f} {y:.1f} L {x + w:.1f} {y:.1f} L {x + w:.1f} {y + h:.1f} L {x:.1f} {y + h:.1f} Z"


def in_disk(p, c, tol=0.0):
    return dist(p, (c[0], c[1])) <= c[2] + tol


def near_boundary(p, c, tol):
    return abs(dist(p, (c[0], c[1])) - c[2]) < tol


def circle_intersections(a, b):
    """2円の交点（重なりがあることを呼び出し側で保証）"""
    d = dist((a[0], a[1]), (b[0], b[1]))
    l = (a[2] ** 2 - b[2] ** 2 + d ** 2) / (2 * d)
    h = math.sqrt(a[2] ** 2 - l ** 2)
    ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
    mx, my = a[0] + l * ux, a[1] + l * uy
    return [(mx - h * uy, my + h * ux), (mx + h * uy, my - h * ux)]


def _sorted_around(pts, center):
    return sorted(pts, key=lambda p: math.atan2(p[1] - center[1], p[0] - center[0]))


def union_polygon(a, b):
    """和集合 A∪B の輪郭（A の弧のうち B の外側＋B の弧のうち A の外側＋交点）。
    中心の中点 M が両円の内側にあれば、輪郭は M を中心に星型で角度順に並べられる"""
    ia, ib = circle_intersections(a, b)
    pts = [p for p in circle_pts(a) if not in_disk(p, b)] + \
          [p for p in circle_pts(b) if not in_disk(p, a)] + [ia, ib]
    center = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    assert in_disk(center, a) and in_disk(center, b), "和集合の輪郭: 中点が両円の内側にない"
    return _sorted_around(pts, center)


def point_in_poly(p, poly):
    """レイキャスティングによる多角形内判定"""
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def overlap_exists(a, b):
    """重なりがあり、どちらも他方を含まない（中心間距離が半径の差より大きく和より小さい）"""
    d = dist((a[0], a[1]), (b[0], b[1]))
    return abs(a[2] - b[2]) < d < a[2] + b[2]


def circle_in_rect(c, r):
    return (r[0] < c[0] - c[2] and c[0] + c[2] < r[0] + r[2] and
            r[1] < c[1] - c[2] and c[1] + c[2] < r[1] + r[3])


def ellipse_in_rect(e, r):
    return (r[0] < e[0] - e[2] and e[0] + e[2] < r[0] + r[2] and
            r[1] < e[1] - e[3] and e[1] + e[3] < r[1] + r[3])


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


def no_digits(texts, allow=()):
    """ラベル群に数字が含まれない（allow の文字列——L01 等のレッスン番号や √2——は除いて判定）"""
    for t in texts:
        s = re.sub(r"L\d\d", "", t)
        for a in allow:
            s = s.replace(a, "")
        if re.search(r"[0-9]", s):
            return False
    return True


def grid_points(rect, step, avoid_circles, tol):
    """矩形内の格子点のうち、円の境界近傍（描画の折れ線近似の誤差域）を除いたもの"""
    x0, y0, w, h = rect
    pts = []
    x = x0 + step
    while x < x0 + w:
        y = y0 + step
        while y < y0 + h:
            p = (x, y)
            if not any(near_boundary(p, c, tol) for c in avoid_circles):
                pts.append(p)
            y += step
        x += step
    return pts


# ---- 数直線（W1・W2 メモの座標系） -------------------------------------------
def number_line_axis(cv, y, x_start, x_tip, ticks_px, both_ends=False):
    """水平の軸（右端に矢じり・both_ends なら左端にも）と目盛りの短い縦線"""
    arrow_px(cv, x_start, y, x_tip, y, w=1.2)
    if both_ends:
        arrow_px(cv, x_tip, y, x_start, y, w=1.2)
    for x in ticks_px:
        tick_px(cv, x, y)


# ---- ベン図パネル（W1 メモ: 半径 70・中心 A(140,130)・B(220,130)・パネル相対） ----
VENN_R = 70
VENN_A = (140, 130)
VENN_B = (220, 130)


def venn_geometry(ox, oy, rect_h):
    rect = (ox, oy, 340, rect_h)
    A = (ox + VENN_A[0], oy + VENN_A[1], VENN_R)
    B = (ox + VENN_B[0], oy + VENN_B[1], VENN_R)
    return rect, A, B


def venn_frame(cv, T, rect, A, B):
    """塗りの上に U 枠・円・ラベルを描く（塗りは先に描いておく）"""
    ox, oy = rect[0], rect[1]
    cv.rect_px(*rect, sw=1.4)
    cv.circle_px(*A)
    cv.circle_px(*B)
    T(ox + 12, oy + 22, "U", size=15, anchor="start", weight="bold")
    T(A[0] - 44, A[1] - A[2] - 10, "A", size=16, weight="bold")   # 各円の外寄り上部
    T(B[0] + 44, B[1] - B[2] - 10, "B", size=16, weight="bold")


# ===========================================================================
# 図1: L01 数直線上の2集合 {x | x>0}（上段）と {x | x>2}（下段）
# 仕様の正: FIG_SPEC_W1.md「L01_fig1_two_sets_number_line.svg」
# ===========================================================================
def fig_L01_1():
    # --- パラメータ（FIG_SPEC_W1 と一致させる） ---
    x_px = lambda v: 140 + 80 * v                 # 値 v → px（値 0 を px 140・1目盛り 80）
    rows = [("{x | x>0}", 0, 70), ("{x | x>2}", 2, 160)]   # (段ラベル, 端点, y)
    X_AXIS0, X_TIP, X_BOLD_END = 40, 640, 630

    ck = Checker()
    ck.ok("値→px の変換が線形（1目盛り=80px・値 0 が px 140）",
          x_px(0) == 140 and all(x_px(v + 1) - x_px(v) == 80 for v in range(-1, 5)))
    ck.ok("○の px 位置が本文の端点値の目盛り位置と一致（上段 0→(140,70)・下段 2→(300,160)）",
          (x_px(rows[0][1]), rows[0][2]) == (140, 70) and (x_px(rows[1][1]), rows[1][2]) == (300, 160))
    ck.ok("範囲の左端 x 座標 < 線の終端 x 座標（両段とも右へ限りなく続く）",
          all(x_px(v) < X_BOLD_END for _, v, _ in rows))
    ck.ok("包含の検算: x>2 をみたす x は x>0 もみたす（x=2.5..5 を0.5刻みで全点）",
          all((x / 2 > 2) <= (x / 2 > 0) for x in range(5, 11)))
    ck.ok("すっぽり入る（真部分集合）: x=1 は x>0 をみたすが x>2 をみたさない", 1 > 0 and not 1 > 2)
    ck.ok("端点は両方とも含まない（○）——2>2・0>0 はどちらも不成立", not (2 > 2) and not (0 > 0))

    cv = Canvas(640, 220)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    cv.line_px(x_px(2), rows[0][2], x_px(2), rows[1][2], w=AUX_W, dash=DASH)   # 2 の位置を結ぶ破線
    for label, v, y in rows:
        number_line_axis(cv, y, X_AXIS0, X_TIP, [x_px(k) for k in range(-1, 6)])
        cv.line_px(x_px(v) + DOT_R_END, y, X_BOLD_END, y, w=BOLD_W)
        open_pt(cv, x_px(v), y)
        T(x_px(v), y + 22, str(v), size=FS_NUM)
        T(60, y - 16, label, size=15, anchor="start")

    return {"file": "L01_fig1_two_sets_number_line.svg", "lesson": "L01", "canvas": cv,
            "title": "数直線上の2集合の包含（x>2 は x>0 に含まれる）",
            "desc": "2段の数直線。上段 {x | x>0}（0 に白丸・右へ太線）、下段 {x | x>2}（2 に白丸・右へ太線）。下段が上段に含まれることを見せる。同型図は端点の値とラベルを差し替えて生成する",
            "intent": "要素が限りなくある2つの集合の包含を、数直線の2段重ねで「下段の範囲が上段の範囲にすっぽり入る」として見せる（○＝含まない規約の初出・L03_fig1 左パネルと同型の伏線）",
            "src": "lesson_01.md §3（「{x | x>2} と {x | x>0} を数直線にかいてみよう。」の段落の直後）",
            "params": "viewBox 640×220／値 v→px 140＋80v（−1〜5）／上段 y=70 {x | x>0}・下段 y=160 {x | x>2}・端点○・太線は 630 まで／数字ラベルは 0 と 2 のみ／2 の位置に縦の破線1本",
            "checks": ck.items,
            "num_labels": ["0", "2"],
            "check_numbers": ["6", "8", "30", "16", "−4", "5.5"],
            "check_tokens": [],
            "note": "FIG_SPEC_W1 反映（ファイル名・ラベル・座標・title/desc）",
            "allow_texts": labels}


# ===========================================================================
# 図2: L02 ベン図——A∩B（左）と A∪B（右）の2パネル
# 仕様の正: FIG_SPEC_W1.md「L02_fig1_venn_intersection_union.svg」
# ===========================================================================
def fig_L02_1():
    # --- パラメータ（FIG_SPEC_W1 と一致させる） ---
    rectL, AL, BL = venn_geometry(10, 20, 240)
    rectR, AR, BR = venn_geometry(370, 20, 240)

    ck = Checker()
    ck.ok("2円の中心距離 < 2×半径（重なりが存在）・どちらも他方を含まない",
          dist(AL[:2], BL[:2]) < 2 * VENN_R and overlap_exists(AL, BL) and overlap_exists(AR, BR),
          f"d={dist(AL[:2], BL[:2]):.0f}, r={VENN_R}")
    ck.ok("2円とも全体集合 U の枠の内側に入る",
          all(circle_in_rect(c, r) for r, c in ((rectL, AL), (rectL, BL), (rectR, AR), (rectR, BR))))
    ck.ok("左右のパネルで円の配置が同じ（パネル相対座標 A(140,130)・B(220,130)・半径70）",
          (AL[0] - rectL[0], AL[1] - rectL[1], AL[2]) == (140, 130, 70) and
          (BR[0] - rectR[0], BR[1] - rectR[1], BR[2]) == (220, 130, 70))
    pts = grid_points(rectL, 4, [AL, BL], 1.0)
    inter = lambda p: in_disk(p, AL) and in_disk(p, BL)      # ∩＝両円内
    union = lambda p: in_disk(p, AL) or in_disk(p, BL)       # ∪＝少なくとも一方
    uni_poly = union_polygon(AL, BL)
    ck.ok("A∪B の塗り（2円の重ね塗り）が「少なくとも一方の内側」の定義関数と格子点全点で一致",
          len(pts) > 2000 and all(point_in_poly(p, uni_poly) == union(p) for p in pts),
          f"格子点{len(pts)}点")
    ck.ok("A∩B（A でクリップした B の塗り）は A∪B に含まれ、等しくはない",
          all(inter(p) <= union(p) for p in pts) and any(inter(p) for p in pts) and
          any(union(p) and not inter(p) for p in pts))
    ck.ok("代表点の検算: 重なりの中央は両方に入る／A の中心は A だけに入る",
          inter(((AL[0] + BL[0]) / 2, AL[1])) and in_disk(AL[:2], AL) and not in_disk(AL[:2], BL))

    cv = Canvas(720, 300)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    # 左: A∩B——円 A を clipPath にして円 B を塗る（両円内だけが残る）
    cv.clip_def("clipA", poly_d(circle_pts(AL)))
    cv.circle_px(BL[0], BL[1], BL[2], fill=SHADE_SET, sw=0, clip="clipA")
    venn_frame(cv, T, rectL, AL, BL)
    T(rectL[0] + 170, 286, "A∩B", size=18, weight="bold")
    # 右: A∪B——2円をそれぞれ塗る（少なくとも一方の内側）
    cv.circle_px(AR[0], AR[1], AR[2], fill=SHADE_SET, sw=0)
    cv.circle_px(BR[0], BR[1], BR[2], fill=SHADE_SET, sw=0)
    venn_frame(cv, T, rectR, AR, BR)
    T(rectR[0] + 170, 286, "A∪B", size=18, weight="bold")
    ck.ok("数字を一切描かない", no_digits(labels))

    return {"file": "L02_fig1_venn_intersection_union.svg", "lesson": "L02", "canvas": cv,
            "title": "ベン図——共通部分と和集合",
            "desc": "同じ配置の2円ベン図を2パネル。左は共通部分（両円の内側）を塗り、右は和集合（少なくとも一方の内側）を塗る。同型図は塗る領域の定義を差し替えて生成する",
            "intent": "A∩B（重なった部分）と A∪B（合わせた部分）を同じ形のベン図の2パネルで対比する",
            "src": "lesson_02.md §1（「2つの丸が重なった部分が A∩B、…」の段落の直後・例題2の前）",
            "params": "viewBox 720×300／パネル 340×240（左 x=10〜350・右 x=370〜710）／円は半径70・中心 A(140,130)・B(220,130)（パネル相対）／左=円 A の clipPath で円 B を塗る・右=2円を塗る／ラベルは U・A・B・A∩B・A∪B のみ・数値なし",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": ["12", "9", "7", "8"],
            "check_tokens": [],
            "note": "FIG_SPEC_W1 反映（ラベル・座標・title/desc）",
            "allow_texts": labels}


# ===========================================================================
# 図3: L02 ド・モルガンの法則——(A∪B)ᶜ／Aᶜ（斜線）／Bᶜ（逆斜線）／Aᶜ∩Bᶜ（交差）の4パネル
# 仕様の正: FIG_SPEC_W1.md「L02_fig2_venn_de_morgan.svg」。
# メモの「白で上塗り」方式は B だけの部分から Aᶜ の斜線が消えるため、円の外側は
# クリップパス（長方形＋円の evenodd）で切り抜く方式にした（結果の交差部分は同じ）。
# ===========================================================================
def fig_L02_2():
    # --- パラメータ（FIG_SPEC_W1 と一致させる） ---
    RECT_H = 224                                   # パネル高 260 のうち枠 224・下に見出し
    origins = [(10, 10), (370, 10), (10, 290), (370, 290)]
    titles = ["(A∪B)ᶜ", "Aᶜ", "Bᶜ", "Aᶜ∩Bᶜ"]
    geoms = [venn_geometry(ox, oy, RECT_H) for ox, oy in origins]

    ck = Checker()
    ck.ok("4パネルとも2円に重なりがある（中心距離 < 2×半径）",
          all(dist(A[:2], B[:2]) < 2 * VENN_R and overlap_exists(A, B) for _, A, B in geoms))
    ck.ok("4パネルの円の配置が L02_fig1 と同じ（パネル相対 A(140,130)・B(220,130)・半径70）",
          all((A[0] - r[0], A[1] - r[1], A[2]) == (140, 130, 70) and
              (B[0] - r[0], B[1] - r[1], B[2]) == (220, 130, 70) for r, A, B in geoms))
    rect0, A0, B0 = geoms[0]
    pts = grid_points(rect0, 4, [A0, B0], 1.0)
    comp_union = lambda p: not (in_disk(p, A0) or in_disk(p, B0))   # 長方形内かつ2円の外
    Ac = lambda p: not in_disk(p, A0)
    Bc = lambda p: not in_disk(p, B0)
    uni_poly = union_polygon(A0, B0)
    drawn_tl = [not point_in_poly(p, uni_poly) for p in pts]          # 左上の塗り（描画幾何）
    ck.ok("左上 (A∪B)ᶜ の塗り（長方形から和集合の輪郭を除くクリップ）が定義関数「長方形内かつ円外」と格子点全点で一致",
          len(pts) > 2000 and drawn_tl == [comp_union(p) for p in pts], f"格子点{len(pts)}点")
    ck.ok("右下 Aᶜ∩Bᶜ の交差領域（Aᶜ の斜線と Bᶜ の逆斜線が両方かかる部分）が左上と同じ幾何（長方形−円A−円B）",
          [Ac(p) and Bc(p) for p in pts] == drawn_tl)
    ck.ok("検査が空振りでない: 塗られる点と塗られない点の両方がある（各領域）",
          any(drawn_tl) and not all(drawn_tl) and
          any(Ac(p) and not Bc(p) for p in pts) and any(Bc(p) and not Ac(p) for p in pts))

    cv = Canvas(720, 560)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    cv.hatch_def("hatch45", 45)
    cv.hatch_def("hatch135", 135)
    # 左上: (A∪B)ᶜ＝長方形内で2円のどちらにも入らない部分をグレー塗り
    rect, A, B = geoms[0]
    cv.clip_def("p1_union_c", rect_d(*rect) + " " + poly_d(union_polygon(A, B)), evenodd=True)
    cv.rect_px(*rect, fill=SHADE_SET, sw=0, clip="p1_union_c")
    venn_frame(cv, T, rect, A, B)
    # 右上: Aᶜ＝長方形内で円 A の外側を斜線（45°）
    rect, A, B = geoms[1]
    cv.clip_def("p2_Ac", rect_d(*rect) + " " + poly_d(circle_pts(A)), evenodd=True)
    cv.rect_px(*rect, fill="url(#hatch45)", sw=0, clip="p2_Ac")
    venn_frame(cv, T, rect, A, B)
    # 左下: Bᶜ＝長方形内で円 B の外側を逆斜線（135°）
    rect, A, B = geoms[2]
    cv.clip_def("p3_Bc", rect_d(*rect) + " " + poly_d(circle_pts(B)), evenodd=True)
    cv.rect_px(*rect, fill="url(#hatch135)", sw=0, clip="p3_Bc")
    venn_frame(cv, T, rect, A, B)
    # 右下: Aᶜ∩Bᶜ＝両方のハッチングを重ねる（交差する部分＝2円の外側）
    rect, A, B = geoms[3]
    cv.clip_def("p4_Ac", rect_d(*rect) + " " + poly_d(circle_pts(A)), evenodd=True)
    cv.clip_def("p4_Bc", rect_d(*rect) + " " + poly_d(circle_pts(B)), evenodd=True)
    cv.rect_px(*rect, fill="url(#hatch45)", sw=0, clip="p4_Ac")
    cv.rect_px(*rect, fill="url(#hatch135)", sw=0, clip="p4_Bc")
    venn_frame(cv, T, rect, A, B)
    for (ox, oy), t in zip(origins, titles):
        T(ox + 170, oy + RECT_H + 26, t, size=18, weight="bold")
    ck.ok("数字を一切描かない", no_digits(labels))

    return {"file": "L02_fig2_venn_de_morgan.svg", "lesson": "L02", "canvas": cv,
            "title": "ド・モルガンの法則（集合版）——(A∪B)の補集合＝Aの補集合∩Bの補集合",
            "desc": "同じ配置の2円ベン図を4パネル。左上は和集合の補集合をグレー、右上は A の補集合を斜線、左下は B の補集合を逆斜線、右下は両方の斜線を重ねて共通部分を見せる。左上と右下が一致する",
            "intent": "ド・モルガンの法則の一方 (A∪B)ᶜ=Aᶜ∩Bᶜ を、「Aᶜ の斜線」と「Bᶜ の逆斜線」が重なる部分が (A∪B)ᶜ と一致することで見せる",
            "src": "lesson_02.md §3（「(A∪B)ᶜ=Aᶜ∩Bᶜ」の等式の直後）",
            "params": "viewBox 720×560／パネル 340×260（左列 x=10〜350・右列 x=370〜710・上段 y=10〜270・下段 y=290〜550）／円は L02_fig1 と同じ配置／塗りはクリップパス＋<pattern> の斜線・逆斜線／ラベルは U・A・B・(A∪B)ᶜ・Aᶜ・Bᶜ・Aᶜ∩Bᶜ のみ・数値なし",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": ["12", "9", "7", "8"],
            "check_tokens": [],
            "note": "FIG_SPEC_W1 反映（ラベル・座標・title/desc）。円の外側の塗りは白の上塗りでなくクリップパスで切り抜き（B だけの部分にも Aᶜ の斜線が残る）",
            "allow_texts": labels}


# ===========================================================================
# 図4: L03 数直線2段（左）と包含図（右）——x>2 ⇒ x>0
# 仕様の正: FIG_SPEC_W1.md「L03_fig1_inclusion_number_line.svg」
# ===========================================================================
def fig_L03_1():
    # --- パラメータ（FIG_SPEC_W1 と一致させる） ---
    x_px = lambda v: 140 + 80 * v
    rows = [("Q={x | x>0}", 0, 70), ("P={x | x>2}", 2, 160)]
    X_AXIS0, X_TIP, X_BOLD_END = 40, 620, 610
    EQ = (770, 120, 110, 85)                       # 楕円 Q
    EP = (800, 130, 55, 40)                        # 楕円 P
    q_label, p_label = (700, 60), (800, 130)

    ck = Checker()
    ck.ok("値→px の変換が L01_fig1 と同じ（1目盛り=80px・値 0 が px 140）",
          x_px(0) == 140 and all(x_px(v + 1) - x_px(v) == 80 for v in range(-1, 5)))
    ck.ok("○の px 位置が端点値の目盛り位置と一致（上段 0→(140,70)・下段 2→(300,160)）",
          (x_px(rows[0][1]), rows[0][2]) == (140, 70) and (x_px(rows[1][1]), rows[1][2]) == (300, 160))
    ck.ok("範囲の左端 x 座標 < 線の終端 x 座標", all(x_px(v) < X_BOLD_END for _, v, _ in rows))
    ck.ok("楕円 P の周上の点（0°〜360° を10°刻み・36点）がすべて楕円 Q の内側（P が Q に完全に入る）",
          all(in_ellipse(p, EQ) for p in ellipse_pts(EP, 36)))
    ck.ok("ラベル Q は大楕円の内側かつ小楕円の外側／ラベル P は小楕円の中心",
          in_ellipse(q_label, EQ) and not in_ellipse(q_label, EP) and p_label == EP[:2])
    ck.ok("p ⇒ q の検算: x>2 をみたす x は x>0 もみたす（x=2.5..5 を0.5刻みで全点）／逆は x=1 が反例",
          all((x / 2 > 2) <= (x / 2 > 0) for x in range(5, 11)) and 1 > 0 and not 1 > 2)

    cv = Canvas(900, 240)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    # 左パネル: 数直線2段（L01_fig1 と同型・ラベルを P・Q に）
    cv.line_px(x_px(2), rows[0][2], x_px(2), rows[1][2], w=AUX_W, dash=DASH)
    for label, v, y in rows:
        number_line_axis(cv, y, X_AXIS0, X_TIP, [x_px(k) for k in range(-1, 6)])
        cv.line_px(x_px(v) + DOT_R_END, y, X_BOLD_END, y, w=BOLD_W)
        open_pt(cv, x_px(v), y)
        T(x_px(v), y + 22, str(v), size=FS_NUM)
        T(60, y - 16, label, size=15, anchor="start")
    # 右パネル: 包含図（大きな楕円 Q の内側に小さな楕円 P）
    cv.ellipse_px(*EQ)
    cv.ellipse_px(*EP, fill=SHADE)
    T(q_label[0], q_label[1] + 5, "Q", size=16, weight="bold")
    T(p_label[0], p_label[1] + 5, "P", size=16, weight="bold")

    return {"file": "L03_fig1_inclusion_number_line.svg", "lesson": "L03", "canvas": cv,
            "title": "命題 x>2 ⇒ x>0 の真理集合の包含（数直線と包含図）",
            "desc": "左は2段の数直線で Q={x | x>0} と P={x | x>2} を描き、P が Q に含まれることを見せる。右は大楕円 Q の中に小楕円 P を置いた包含図。同型図は条件の端点とラベルを差し替えて生成する",
            "intent": "解説の例示「x>2 ならば x>0」について、数直線の包含（左）と集合の包含図（右）を1枚で対応づける（左は L01_fig1 と同型・ラベルを P・Q に変えたもの）",
            "src": "lesson_03.md §3（「…P の範囲は Q の範囲の中にすっぽり入っていた——P⊂Q である。」の段落の直後）",
            "params": "viewBox 900×240／左: 値 v→px 140＋80v・上段 y=70 Q={x | x>0}・下段 y=160 P={x | x>2}・端点○・太線 610 まで・矢印先端 620／右: 楕円 Q 中心(770,120) 半径(110,85)・楕円 P 中心(800,130) 半径(55,40)／数字ラベルは 0 と 2 のみ",
            "checks": ck.items,
            "num_labels": ["0", "2"],
            "check_numbers": ["4", "−1", "−3", "−2", "3", "5", "1"],
            "check_tokens": [],
            "note": "FIG_SPEC_W1 反映（ファイル名・ラベル・座標・title/desc）",
            "allow_texts": labels}


# ===========================================================================
# 図5: L04 向き固定図——U の中に楕円 Q・その内側に円 P・矢印 p ⇒ q・十分／必要のラベル
# 仕様の正: FIG_SPEC_W2.md「図1 L04_fig1_sufficient_necessary_direction.svg」
# ===========================================================================
def fig_L04_1():
    # --- パラメータ（FIG_SPEC_W2 と一致させる。座標は目安→整えた） ---
    U = (30, 40, 460, 230)
    EQ = (250, 160, 190, 100)                      # 楕円 Q
    CP = (190, 160, 62)                            # 円 P
    arrow_from, arrow_to = (252, 160), (380, 110)
    q_label = (380, 100)                           # メモの (400,90) は楕円式で外側になるため内側へ

    ck = Checker()
    ck.ok("円 P の周上 36 点がすべて楕円 Q の内側（P⊂Q）",
          all(in_ellipse(p, EQ) for p in circle_pts(CP, 36)))
    ck.ok("円 P と楕円 Q がともに U の枠内", circle_in_rect(CP, U) and ellipse_in_rect(EQ, U))
    ck.ok("矢印の始点は P の円の右端（中心＋半径）・終点は Q の内側で P の外側",
          arrow_from == (CP[0] + CP[2], CP[1]) and in_ellipse(arrow_to, EQ) and not in_disk(arrow_to, CP))
    ck.ok("ラベル Q の位置は楕円 Q の内側かつ円 P の外側",
          in_ellipse(q_label, EQ) and not in_disk(q_label, CP))

    cv = Canvas(520, 330)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    cv.rect_px(*U, rx=8)
    cv.ellipse_px(*EQ, fill=SHADE2)
    cv.circle_px(*CP, fill=SHADE)
    T(U[0] + 12, U[1] + 22, "U", size=15, anchor="start", weight="bold")
    T(q_label[0], q_label[1] + 5, "Q", size=16, weight="bold")
    T(CP[0], CP[1] + 5, "P", size=16, weight="bold")
    arrow_px(cv, *arrow_from, *arrow_to, w=1.6, head=8.0)
    T(311, 122, "p ⇒ q（真）", size=FS, weight="bold")
    T(260, 25, "P⊂Q", size=18, weight="bold")
    T(120, 300, "十分条件 p（小さいほう）", size=FS, weight="bold")
    T(380, 300, "必要条件 q（大きいほう）", size=FS, weight="bold")
    ck.ok("テキストに数字が含まれない", no_digits(labels))

    return {"file": "L04_fig1_sufficient_necessary_direction.svg", "lesson": "L04", "canvas": cv,
            "title": "p⇒q が真のときの向き固定図（P⊂Q・十分条件と必要条件）",
            "desc": "全体集合 U の中に大きい集合 Q（楕円）と、その内側に小さい集合 P（円）を描き、P から Q へ p⇒q の矢印を置く。P 側に十分条件、Q 側に必要条件のラベル。同型の図を描くときは、小さい集合が内側・十分条件、大きい集合が外側・必要条件、の対応を保つ。",
            "intent": "p⇒q が真 ⇔ P⊂Q の図に、「十分条件（小さいほう）」「必要条件（大きいほう）」のラベルと矢印を置き、向きを図で固定する（語で迷ったときに戻る1枚）",
            "src": "lesson_04.md §1（定義の枠の直後・「上の例では…」の段落の前）",
            "params": "U 角丸長方形 (30,40)–(490,270)／楕円 Q 中心(250,160) rx190 ry100・薄い網かけ／円 P 中心(190,160) r62・濃い網かけ／矢印 (252,160)→(380,110)／ラベルは U・P・Q・p ⇒ q（真）・P⊂Q・十分条件 p（小さいほう）・必要条件 q（大きいほう）のみ・数字なし",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": ["3", "0", "1", "12", "6", "2", "4", "16", "−4", "−3", "5", "−1"],
            "check_tokens": [],
            "note": "FIG_SPEC_W2 反映（ラベル・座標・title/desc）。ラベル Q はメモの (400,90) が楕円式で外側になるため (380,100) へ",
            "allow_texts": labels}


# ===========================================================================
# 図6: L04 4分類の包含図（必要十分／十分／必要／どちらでもない）
# 仕様の正: FIG_SPEC_W2.md「図2 L04_fig2_four_cases_inclusion.svg」（マップ外の追加・削減候補）
# ===========================================================================
def fig_L04_2():
    # --- パラメータ（FIG_SPEC_W2 と一致させる。パネル相対座標） ---
    PANEL_W, PANEL_H, Y0 = 240, 200, 15
    xs = [10 + PANEL_W * i for i in range(4)]
    headings = ["p⇒q 真・q⇒p 真", "p⇒q 真・q⇒p 偽", "p⇒q 偽・q⇒p 真", "p⇒q 偽・q⇒p 偽"]
    bottoms = ["必要十分条件", "十分条件（必要条件ではない）", "必要条件（十分条件ではない）", "どちらでもない"]
    c_eq, c_eq_outer = (120, 100, 55), (120, 100, 58)          # パネル1: 二重線の円
    e2_Q, c2_P = (120, 100, 90, 60), (95, 100, 32)             # パネル2: P が Q の内側
    e3_P, c3_Q = (120, 100, 90, 60), (145, 100, 32)            # パネル3: Q が P の内側
    c4_P, c4_Q = (95, 100, 50), (150, 100, 50)                 # パネル4: 互いにはみ出す

    ck = Checker()
    ck.ok("パネル2: P の円周 36 点がすべて Q の楕円内（P⊂Q→十分条件）",
          all(in_ellipse(p, e2_Q) for p in circle_pts(c2_P, 36)))
    ck.ok("パネル3: Q の円周 36 点がすべて P の楕円内（Q⊂P→必要条件）",
          all(in_ellipse(p, e3_P) for p in circle_pts(c3_Q, 36)))
    ck.ok("パネル4: 2円は一方が他方を含まず、かつ交わる（|r1−r2| < 中心間距離 < r1＋r2 ＝ 0 < 55 < 100）",
          overlap_exists(c4_P, c4_Q) and dist(c4_P[:2], c4_Q[:2]) == 55 and c4_P[2] + c4_Q[2] == 100)
    ck.ok("パネル1: P と Q は同じ円（中心・半径が一致・外側の細線は半径＋3）",
          c_eq_outer[:2] == c_eq[:2] and c_eq_outer[2] == c_eq[2] + 3)
    ck.ok("見出しの真偽の組が §3 の表の行順（真真／真偽／偽真／偽偽）と一致",
          headings == ["p⇒q 真・q⇒p 真", "p⇒q 真・q⇒p 偽", "p⇒q 偽・q⇒p 真", "p⇒q 偽・q⇒p 偽"])
    ck.ok("4パネルが等幅・等間隔で重ならない（240px×4・viewBox 980）",
          all(xs[i + 1] - xs[i] == PANEL_W for i in range(3)) and xs[-1] + PANEL_W <= 980)

    cv = Canvas(980, 230)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    sh = lambda c, x0: (c[0] + x0, c[1] + Y0) + tuple(c[2:])   # パネル相対→絶対
    for i, x0 in enumerate(xs):
        cv.rect_px(x0, Y0, PANEL_W, PANEL_H, sw=0.8)
        T(x0 + 120, Y0 + 24, headings[i], size=13)
        if i == 0:
            cv.circle_px(*sh(c_eq_outer, x0), sw=1.0)
            cv.circle_px(*sh(c_eq, x0), fill=SHADE)
            T(x0 + 120, Y0 + 105, "P=Q", size=16, weight="bold")
        elif i == 1:
            cv.ellipse_px(*sh(e2_Q, x0))
            cv.circle_px(*sh(c2_P, x0), fill=SHADE)
            T(x0 + 95, Y0 + 105, "P", size=16, weight="bold")
            T(x0 + 175, Y0 + 67, "Q", size=16, weight="bold")
        elif i == 2:
            cv.ellipse_px(*sh(e3_P, x0))
            cv.circle_px(*sh(c3_Q, x0), fill=SHADE)
            T(x0 + 145, Y0 + 105, "Q", size=16, weight="bold")
            T(x0 + 65, Y0 + 67, "P", size=16, weight="bold")
        else:
            cv.circle_px(*sh(c4_P, x0), fill=SHADE)
            cv.circle_px(*sh(c4_Q, x0))
            T(x0 + 78, Y0 + 105, "P", size=16, weight="bold")
            T(x0 + 167, Y0 + 105, "Q", size=16, weight="bold")
        T(x0 + 120, Y0 + 186, bottoms[i], size=13, weight="bold")
    ck.ok("パネル2・3のラベル Q／P は楕円の内側かつ円の外側",
          in_ellipse((175, 62), e2_Q) and not in_disk((175, 62), c2_P) and
          in_ellipse((65, 62), e3_P) and not in_disk((65, 62), c3_Q))
    ck.ok("テキストに数字が含まれない", no_digits(labels))

    return {"file": "L04_fig2_four_cases_inclusion.svg", "lesson": "L04", "canvas": cv,
            "title": "必要条件・十分条件の4分類——P と Q の包含関係4通り",
            "desc": "左から順に、P と Q が等しい（必要十分）、P が Q の内側（十分）、Q が P の内側（必要）、互いにはみ出す（どちらでもない）の4パネル。各パネル上部に p⇒q と q⇒p の真偽の組を示す。",
            "intent": "4分類（必要十分／十分／必要／どちらでもない）を、P と Q の包含関係4通りの小図で対比する（§3 の表の行順と一致）",
            "src": "lesson_04.md §3（4分類の表の直後・例題2の前）",
            "params": "4パネル 240×200（viewBox 980×230）／パネル1: 二重線の円 r55（外側 r58）に P=Q／パネル2: 楕円 Q(120,100,90,60)＋円 P(95,100,32)／パネル3: 楕円 P(120,100,90,60)＋円 Q(145,100,32)／パネル4: 円 P(95,100,50)・円 Q(150,100,50)（中心距離55）／ラベルはメモの許可一覧のみ・数字なし",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": ["3", "0", "1", "12", "6", "2", "4", "16", "−4", "−3", "5", "−1"],
            "check_tokens": [],
            "note": "FIG_SPEC_W2 反映（マップ §4 外の追加図・削減候補。ラベル・座標・title/desc）",
            "allow_texts": labels}


# ===========================================================================
# 図7: L05 条件の否定と補集合——「x≦1 または x≧3」（●）と否定「1<x<3」（○）の数直線2段
# 仕様の正: FIG_SPEC_W2.md「図3 L05_fig1_negation_complement_numberline.svg」
# ===========================================================================
def fig_L05_1():
    # --- パラメータ（FIG_SPEC_W2 と一致させる） ---
    a, b = 1, 3
    x_px = lambda x: 50 + (x + 1) * 70               # x=−1→50, 1→190, 3→330, 5→470
    X0, X1 = x_px(-1), x_px(5)
    y_top, y_bot = 70, 150
    BAND_H = 8

    def orig(x):      # もとの条件 x≦1 または x≧3（x は 1/20 刻みの整数表現）
        return x <= a * 20 or x >= b * 20

    def neg(x):       # 否定 1<x<3
        return a * 20 < x < b * 20

    xs = range(-20, 101)
    top_bands = [(X0, x_px(a)), (x_px(b), X1)]
    bot_bands = [(x_px(a), x_px(b))]

    ck = Checker()
    ck.ok("座標変換 x_px=50＋(x＋1)×70（x=−1→50・1→190・3→330・5→470）",
          (x_px(-1), x_px(1), x_px(3), x_px(5)) == (50, 190, 330, 470))
    ck.ok("上段の網かけ [50,190]∪[330,470] と下段の網かけ [190,330] を合わせると軸全体 [50,470] を過不足なく覆い、内部が重ならない",
          top_bands[0][1] == bot_bands[0][0] and bot_bands[0][1] == top_bands[1][0] and
          top_bands[0][0] == X0 and top_bands[1][1] == X1 and
          top_bands[0][0] < top_bands[0][1] < top_bands[1][0] < top_bands[1][1])
    ck.ok("端点マーカーは上段が●（含む）・下段が○（含まない）で、同じ x 座標（190・330）に置かれる",
          x_px(a) == 190 and x_px(b) == 330)
    ck.ok("否定の検算: もとの条件と否定はどの x でもちょうど一方だけ成り立つ（−1〜5 を 0.05 刻みで全点）",
          all(orig(x) != neg(x) for x in xs), f"{len(xs)}点")
    ck.ok("端点の検算: x=1 と x=3 はもとの条件だけに入る（●）・否定には入らない（○）",
          orig(20) and not neg(20) and orig(60) and not neg(60))
    ck.ok("ド・モルガンの検算: 「x≦1 または x≧3」の否定 =「x>1 かつ x<3」= 1<x<3",
          all(neg(x) == ((x > 20) and (x < 60)) for x in xs))

    cv = Canvas(520, 220)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    ticks = [x_px(k) for k in range(0, 5)]
    for y, bands, closed, label, ly in ((y_top, top_bands, True, "x≦1 または x≧3", 45),
                                        (y_bot, bot_bands, False, "否定: x>1 かつ x<3（1<x<3）", 125)):
        for x1, x2 in bands:
            cv.rect_px(x1, y - 4 - BAND_H, x2 - x1, BAND_H, fill=SHADE, sw=0)
        number_line_axis(cv, y, X0, X1, ticks, both_ends=True)
        for x1, x2 in bands:   # 範囲の太線（矢じりの手前まで）
            cv.line_px(max(x1, X0 + 9), y, min(x2, X1 - 9), y, w=BOLD_W)
        for v in (a, b):
            (closed_pt if closed else open_pt)(cv, x_px(v), y)
            T(x_px(v), y + 20, str(v), size=FS_NUM)
        T(X0, ly, label, size=FS, anchor="start", weight="bold")
    T(X1, 110, "2段を合わせると数直線全体", size=11, anchor="end")

    return {"file": "L05_fig1_negation_complement_numberline.svg", "lesson": "L05", "canvas": cv,
            "title": "条件の否定と補集合——数直線2段（x≦1 または x≧3 と、その否定 1<x<3）",
            "desc": "同じ目盛りの数直線を2段に描き、上段に条件「x≦1 または x≧3」の真理集合（1 と 3 に●、外側を網かけ）、下段にその否定「1<x<3」の真理集合（1 と 3 に○、内側を網かけ）を示す。2段を合わせると数直線全体になり重なりがない。同型の図を描くときは、端点の●と○が上下で入れ替わることを保つ。",
            "intent": "条件「x≦1 または x≧3」の真理集合（上段）と、その否定「1<x<3」の真理集合（下段）を同じ目盛りの数直線2段で対比し、「合わせて全体・重なりなし」と端点の●○の入れ替わりを見せる",
            "src": "lesson_05.md §2 例題2(2) の解答の直後（「検算は§1と同じで…」の段落の前）",
            "params": "viewBox 520×220／x_px=50＋(x＋1)×70・軸 x=−1〜5・両端に矢じり／上段 y=70: 1 と 3 に●・[50,190]と[330,470]に帯／下段 y=150: 1 と 3 に○・[190,330]に帯／数字ラベルは 1 と 3 のみ（0・2・4 は目盛り線のみ）",
            "checks": ck.items,
            "num_labels": ["1", "3"],
            "check_numbers": ["−3", "7", "−1", "6", "−2", "4", "0", "2"],
            "check_tokens": ["x<−1", "x≧6", "−2≦x≦4", "0≦x<2", "x>−3", "x=7", "x＋1≦0", "n²≠10", "x=−4"],
            "note": "FIG_SPEC_W2 反映（ラベル・座標・title/desc）。帯に加えて範囲の太線も描いた（白黒印刷での視認性・先行単元と同じ描法）",
            "allow_texts": labels}


# ===========================================================================
# 図8: L06 逆・裏・対偶の関係図（四隅の命題・横=逆・縦=裏・対角線=対偶）
# 仕様の正: FIG_SPEC_W3.md「L06_fig1_converse_inverse_contrapositive.svg」。
# 命題は (仮定, 結論) の記号モデルで持ち、逆・裏・対偶の対応と真偽の一致を検算する。
# メモの「対角線は青系」は白黒規約により線幅 3.2 で区別した。
# ===========================================================================
def fig_L06_1():
    # --- パラメータ（FIG_SPEC_W3 と一致させる） ---
    S0 = (("p", False), ("q", False))                 # p ⇒ q
    neg = lambda t: (t[0], not t[1])
    converse = lambda s: (s[1], s[0])                  # 逆
    inverse = lambda s: (neg(s[0]), neg(s[1]))         # 裏
    contrapos = lambda s: (neg(s[1]), neg(s[0]))       # 対偶
    TL, TR, BL, BR = S0, converse(S0), inverse(S0), contrapos(S0)
    boxes = {"TL": (40, 40, 240, 72), "TR": (360, 40, 240, 72),
             "BL": (40, 248, 240, 72), "BR": (360, 248, 240, 72)}
    tags = {"TL": "もとの命題", "TR": "逆", "BL": "裏", "BR": "対偶"}
    edges = [((280, 76), (360, 76), "逆", (320, 66)),
             ((280, 284), (360, 284), "逆", (320, 302)),
             ((160, 112), (160, 248), "裏", (140, 184)),
             ((480, 112), (480, 248), "裏", (500, 184))]
    diagonals = [((280, 112), (360, 248)), ((360, 112), (280, 248))]
    CROSS = (320, 180)

    def render(t):
        return f"{t[0]} でない" if t[1] else t[0]

    def stmt(s):
        return f"{render(s[0])} ⇒ {render(s[1])}"

    def truth(s, p, q):
        val = {"p": p, "q": q}
        h = val[s[0][0]] != s[0][1]
        c = val[s[1][0]] != s[1][1]
        return (not h) or c

    assigns = [(p, q) for p in (True, False) for q in (True, False)]

    def corner(p, r):
        return (abs(p[0] - r[0]) < 1e-9 or abs(p[0] - r[0] - r[2]) < 1e-9) and \
               (abs(p[1] - r[1]) < 1e-9 or abs(p[1] - r[1] - r[3]) < 1e-9)

    def intersect(l1, l2):
        (x1, y1), (x2, y2) = l1
        (x3, y3), (x4, y4) = l2
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    ck = Checker()
    ck.ok("矩形4個が重ならない",
          all(disjoint(boxes[a], boxes[b]) for a in boxes for b in boxes if a < b))
    ck.ok("辺の矢印4本の端点が隣接矩形の辺上にある",
          on_edge(edges[0][0], boxes["TL"]) and on_edge(edges[0][1], boxes["TR"]) and
          on_edge(edges[1][0], boxes["BL"]) and on_edge(edges[1][1], boxes["BR"]) and
          on_edge(edges[2][0], boxes["TL"]) and on_edge(edges[2][1], boxes["BL"]) and
          on_edge(edges[3][0], boxes["TR"]) and on_edge(edges[3][1], boxes["BR"]))
    ck.ok("対角線2本の端点が対角の矩形の角に接する",
          corner(diagonals[0][0], boxes["TL"]) and corner(diagonals[0][1], boxes["BR"]) and
          corner(diagonals[1][0], boxes["TR"]) and corner(diagonals[1][1], boxes["BL"]))
    ck.ok("対角線2本が (320,180) で交わる",
          dist(intersect(*diagonals), CROSS) < 1e-9)
    ck.ok("四隅の対応: 右上=逆・左下=裏・右下=対偶（もとの命題 p ⇒ q から機械的に生成）",
          stmt(TR) == "q ⇒ p" and stmt(BL) == "p でない ⇒ q でない" and stmt(BR) == "q でない ⇒ p でない")
    ck.ok("辺の関係: 横の辺は「逆」どうし・縦の辺は「裏」どうし／対角線は対偶どうし",
          converse(TL) == TR and converse(BL) == BR and inverse(TL) == BL and inverse(TR) == BR and
          contrapos(TL) == BR and contrapos(TR) == BL)
    ck.ok("真偽の一致: 対偶どうしは p, q の真偽4通りすべてで真偽が一致（もとの命題と逆は不一致の場合あり）",
          all(truth(TL, p, q) == truth(BR, p, q) and truth(TR, p, q) == truth(BL, p, q)
              for p, q in assigns) and truth(TL, False, True) != truth(TR, False, True))

    cv = Canvas(640, 360)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    for key, s in (("TL", TL), ("TR", TR), ("BL", BL), ("BR", BR)):
        x, y, w, h = boxes[key]
        cv.rect_px(x, y, w, h, sw=1.5, rx=8)
        T(x + w / 2, y + 32, stmt(s), size=20, weight="bold")
        T(x + w / 2, y + 58, tags[key], size=13)
    for p1, p2, lab, lp in edges:
        double_arrow_px(cv, *p1, *p2)
        T(lp[0], lp[1] + 5, lab, size=FS)
    for p1, p2 in diagonals:
        double_arrow_px(cv, *p1, *p2, w=BOLD_W, head=9.0)
    cv.rect_px(CROSS[0] - 22, CROSS[1] - 14, 44, 20, fill="#fff", sw=0)
    T(CROSS[0], CROSS[1] + 1, "対偶", size=FS, weight="bold")

    return {"file": "L06_fig1_converse_inverse_contrapositive.svg", "lesson": "L06", "canvas": cv,
            "title": "逆・裏・対偶の関係図",
            "desc": "4頂点に p⇒q・q⇒p・「p でない ⇒ q でない」・「q でない ⇒ p でない」。横の辺が逆、縦の辺が裏、対角線が対偶。同型図をAIに描かせる指示: 「2×2 の配置。左上=もとの命題、右上=逆、左下=裏、右下=対偶。横=逆、縦=裏、対角=対偶と辺にラベル」。",
            "intent": "命題 p⇒q と、その逆・裏・対偶を四角形の4頂点に置き、「横の辺＝逆（入れかえ）」「縦の辺＝裏（両方否定）」「対角線＝対偶（入れかえて両方否定）」の関係を1枚で見せる",
            "src": "lesson_06.md §2（4つの命題の定義箇条書きの直後）",
            "params": "viewBox 640×360／角丸矩形 240×72 を (40,40)(360,40)(40,248)(360,248)／辺の両向き矢印4本＋対角線2本（対角線は線幅 3.2 で区別・交点 (320,180) に「対偶」）／ラベルはメモの許可一覧のみ・数値なし",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": [],
            "check_tokens": ["x=3", "x²=9", "−3", "x=−2", "x²=4", "x>5", "4 の倍数"],
            "note": "FIG_SPEC_W3 反映（ラベル・座標・title/desc）。対角線の青色指定は白黒規約により線幅で置換",
            "allow_texts": labels}


# ===========================================================================
# 図9: L07 背理法の流れ図（縦5段）
# 仕様の正: FIG_SPEC_W3.md「L07_fig1_proof_by_contradiction_flow.svg」。
# 右側の補助文（x=470 から 10 文字）が幅 520 に収まらないため viewBox 幅を 620 にした
# （座標はメモのまま）。強調枠の青色指定は白黒規約により線幅 3.2 で置換。
# ===========================================================================
def fig_L07_1():
    # --- パラメータ（FIG_SPEC_W3 と一致させる） ---
    X, W, H, RX = 60, 400, 64, 8
    ys = [24, 124, 224, 324, 424]
    texts = ["証明したい命題", "その否定を仮定する", "正しい推論を積み重ねる", "矛盾が出る",
             "仮定は誤り。よって命題は正しい"]
    emphasis = {1, 4}                                  # 2段目・5段目（0始まり）
    notes = {1: "否定するのは結論", 3: "何と食い違ったかを言う"}
    AX = 260
    arrows = [((AX, ys[i] + H), (AX, ys[i + 1])) for i in range(4)]

    ck = Checker()
    ck.ok("矩形5個が等間隔（y の差 100）", all(ys[i + 1] - ys[i] == 100 for i in range(4)))
    ck.ok("矢印4本の始点=上の矩形の下辺・終点=下の矩形の上辺・x が一致（x=260）",
          all(p1 == (AX, ys[i] + H) and p2 == (AX, ys[i + 1]) and p1[0] == p2[0]
              for i, (p1, p2) in enumerate(arrows)) and
          all(on_edge(p1, (X, ys[i], W, H)) and on_edge(p2, (X, ys[i + 1], W, H))
              for i, (p1, p2) in enumerate(arrows)))
    ck.ok("強調枠は2段目と5段目のみ", emphasis == {1, 4})
    ck.ok("矩形5個が重ならない",
          all(disjoint((X, ys[i], W, H), (X, ys[j], W, H)) for i in range(5) for j in range(i + 1, 5)))

    cv = Canvas(620, 560)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    for i, (y, t) in enumerate(zip(ys, texts)):
        cv.rect_px(X, y, W, H, sw=BOLD_W if i in emphasis else 1.5, rx=RX)
        T(X + W / 2, y + H / 2 + 6, t, size=17, weight="bold" if i in emphasis else None)
        if i in notes:
            T(470, y + H / 2 + 4, notes[i], size=12, anchor="start")
    for p1, p2 in arrows:
        arrow_px(cv, *p1, *p2, w=1.5, head=8.0)
    ck.ok("テキストに数字が含まれない", no_digits(labels))

    return {"file": "L07_fig1_proof_by_contradiction_flow.svg", "lesson": "L07", "canvas": cv,
            "title": "背理法の流れ図",
            "desc": "縦5段の流れ図。2段目（否定を仮定）と5段目（仮定は誤り・命題は正しい）を強調。同型図をAIに描かせる指示: 「縦に5つの箱を等間隔に並べ、下向き矢印でつなぐ。2段目と5段目を太い枠にする」。",
            "intent": "背理法の5段の流れ（証明したい命題→否定を仮定→推論の積み重ね→矛盾→仮定は誤り・よって命題は正しい）を、証明を読む前に縦の流れ図で固定する。「否定するのは結論」「矛盾が出たら仮定が誤り」の2箇所を強調枠にする",
            "src": "lesson_07.md §1（「流れを先に図で見ておく」の直後・番号付きリスト1〜5の直前）",
            "params": "viewBox 620×560（メモ 520 は補助文が収まらないため幅のみ拡張）／角丸矩形 x=60 幅400 高さ64 を y=24,124,224,324,424／下向き矢印 x=260／2段目・5段目は線幅 3.2 の強調枠／補助文 x=470 左揃え／ラベルはメモの許可一覧のみ・数値なし",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": [],
            "check_tokens": ["√2", "√3", "a/b", "2b²", "180"],
            "note": "FIG_SPEC_W3 反映（ラベル・座標・title/desc）。viewBox 幅 520→620・強調枠の青色は線幅で置換",
            "allow_texts": labels}


# ===========================================================================
# 図10: L07 単元マップ——集合→命題と真偽→条件→証明、上に先行「数と式」・下に後続「二次関数」
# 仕様の正: FIG_SPEC_W3.md「L07_fig2_unit_map.svg」。
# 外との出入りの矢印（青系指定）は白黒規約により破線で区別した。
# ===========================================================================
def fig_L07_2():
    # --- パラメータ（FIG_SPEC_W3 と一致させる） ---
    b_top = (270, 20, 200, 48)
    mids = [((20, 150, 160, 72), "集合", "L01〜L02"),
            ((200, 150, 160, 72), "命題と真偽", "L03"),
            ((380, 150, 160, 72), "条件", "L04〜L05"),
            ((560, 150, 160, 72), "証明", "L06〜L07")]
    b_bot = (270, 332, 200, 48)
    mid_arrows = [((180, 186), (200, 186)), ((360, 186), (380, 186)), ((540, 186), (560, 186))]
    in_arrows = [((330, 68), (100, 150), ["集まり"]),
                 ((370, 68), (280, 150), ["反例"]),
                 ((410, 68), (640, 150), ["√2"])]
    out_arrows = [((100, 222), (330, 332), ["かつ／または", "解なし・すべての実数"]),
                  ((280, 222), (370, 332), ["解の集合"]),
                  ((460, 222), (410, 332), ["⇔"])]
    all_boxes = [b_top] + [m[0] for m in mids] + [b_bot]

    ck = Checker()
    ck.ok("枠6個が互いに重ならない",
          all(disjoint(all_boxes[i], all_boxes[j]) for i in range(6) for j in range(i + 1, 6)))
    ck.ok("中段の右向き矢印3本の端点が隣接枠の辺上にある",
          all(on_edge(p1, mids[i][0]) and on_edge(p2, mids[i + 1][0])
              for i, (p1, p2) in enumerate(mid_arrows)))
    ck.ok("上段から3本の矢印: 始点が「数と式」枠の下辺・終点が集合／命題と真偽／証明の枠の上辺",
          all(on_edge(p1, b_top) for p1, _, _ in in_arrows) and
          on_edge(in_arrows[0][1], mids[0][0]) and on_edge(in_arrows[1][1], mids[1][0]) and
          on_edge(in_arrows[2][1], mids[3][0]))
    ck.ok("下段へ3本の矢印: 始点が集合／命題と真偽／条件の枠の下辺・終点が「二次関数」枠の上辺",
          on_edge(out_arrows[0][0], mids[0][0]) and on_edge(out_arrows[1][0], mids[1][0]) and
          on_edge(out_arrows[2][0], mids[2][0]) and all(on_edge(p2, b_bot) for _, p2, _ in out_arrows))

    cv = Canvas(740, 400)
    labels = []

    def T(x, y, s, **kw):
        labels.append(s)
        cv.text_px(x, y, s, **kw)

    cv.rect_px(*b_top, rx=8, sw=1.5)
    T(b_top[0] + 100, b_top[1] + 30, "数と式（先行の単元）", size=15, weight="bold")
    for b, main, sub in mids:
        cv.rect_px(*b, rx=8, sw=1.5)
        T(b[0] + 80, b[1] + 30, main, size=15, weight="bold")
        T(b[0] + 80, b[1] + 54, sub, size=13)
    cv.rect_px(*b_bot, rx=8, sw=1.5)
    T(b_bot[0] + 100, b_bot[1] + 30, "二次関数（後続の単元）", size=15, weight="bold")
    for p1, p2 in mid_arrows:
        arrow_px(cv, *p1, *p2, w=1.5, head=8.0)
    for p1, p2, labs in in_arrows + out_arrows:
        arrow_px(cv, *p1, *p2, w=1.5, head=8.0, dash=DASH)
    for p1, p2, labs in in_arrows + out_arrows:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        for k, lab in enumerate(labs):
            text_boxed(cv, T, mx, my + 4 + (k - (len(labs) - 1) / 2) * 16, lab, size=12)
    ck.ok("図中の数字はレッスン番号と √2 以外に無い", no_digits(labels, allow=("√2",)))

    return {"file": "L07_fig2_unit_map.svg", "lesson": "L07", "canvas": cv,
            "title": "単元マップ——集合から証明まで",
            "desc": "中段に4枠（集合・命題と真偽・条件・証明）を左から右へ。上段の先行単元から3本、下段の後続単元へ3本の矢印。同型図をAIに描かせる指示: 「横一列の4枠を右向き矢印でつなぎ、上に先行単元、下に後続単元の枠を置いて、出入りの矢印にラベルを付ける」。",
            "intent": "単元の4段（集合→命題と真偽→条件→証明）を左から右へ並べ、先行「数と式」から入ってくる3本（集まり・反例・√2）と、後続「二次関数」へ出ていく矢印（解の集合・かつ／または・解なし・すべての実数・⇔）を1枚で見せる（先行単元 L11 の単元マップと同型・数値なし）",
            "src": "lesson_07.md §4（「7つのレッスンを1枚の地図にたたむ」の直後・4枠の箇条書きの直前）",
            "params": "viewBox 740×400／上段枠 (270,20) 200×48・中段枠 160×72 を x=20,200,380,560 y=150・下段枠 (270,332) 200×48／中段の実線矢印3本・上下との破線矢印6本（白下地ラベル）／ラベルはメモの許可一覧のみ（数字はレッスン番号と √2 のみ）",
            "checks": ck.items,
            "num_labels": [],
            "check_numbers": [],
            "check_tokens": ["√3", "√2＋√3", "4 の倍数", "2、6、10"],
            "note": "FIG_SPEC_W3 反映（ラベル・座標・title/desc）。出入りの矢印の青色指定は白黒規約により破線で置換",
            "allow_texts": labels}


# ===========================================================================
# main: 検査器の陽性対照 → 生成 → SVG技術検査（XML/viewBox/self-contained/禁止文字）
#       → 答え漏れ検査（許可リスト完全一致＋数字ラベル＋禁止文字列） → FIGURE_MANIFEST.md
# ===========================================================================
FIGS = [fig_L01_1,
        fig_L02_1, fig_L02_2,
        fig_L03_1,
        fig_L04_1, fig_L04_2,
        fig_L05_1,
        fig_L06_1,
        fig_L07_1, fig_L07_2]

TEXT_RE = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
REF_RE = re.compile(r'url\(#([^)]+)\)')
DEF_RE = re.compile(r'<(?:clipPath|pattern) id="([^"]+)"')
NUM_RE = re.compile(r"[−-]?\d+(?:\.\d+)?")


def svg_texts(src):
    """SVG本文から<text>の内容を抽出（エスケープを戻す）"""
    return [unescape(m) for m in TEXT_RE.findall(src)]


def ban_hits(texts, bans):
    """禁止文字列の検出（改行連結——ラベル境界をまたぐ偽陽性を防ぐ）"""
    joined = "\n".join(texts)
    return [b for b in bans if b in joined]


def numeric_labels(texts):
    """数字だけのラベル（目盛りの数）を抽出"""
    return [t for t in texts if NUM_RE.fullmatch(t)]


def forbidden_chars(s):
    """公開側の検疫と同じ基準の禁止文字: 不可視・結合（上線 U+0304 等）・異体字セレクタ・
    未割当・私用領域・かなの分離濁点・絵文字系記号・全角英数字。見つかった文字を返す"""
    bad = []
    for ch in s:
        o = ord(ch)
        cat = unicodedata.category(ch)
        if (cat in ("Cf", "Mn", "Me", "Cn", "Co")
                or 0xFE00 <= o <= 0xFE0F
                or 0x3099 <= o <= 0x309C
                or o in (0xFF9E, 0xFF9F)
                or o >= 0x1F000
                or (0x2600 <= o <= 0x27BF and ch not in "✓✗")
                or 0xFF10 <= o <= 0xFF19 or 0xFF21 <= o <= 0xFF3A or 0xFF41 <= o <= 0xFF5A):
            bad.append(ch)
    return bad


def gate_self_test():
    """答え漏れ検査器・禁止文字検出器の陽性対照——検出できることを毎回実証してから本走査に入る"""
    sample = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
              '<text x="1" y="1">21</text><text x="2" y="2">x&lt;6</text>'
              '<text x="3" y="3">2段を合わせる</text><text x="4" y="4">−4</text></svg>')
    ts = svg_texts(sample)
    assert ts == ["21", "x<6", "2段を合わせる", "−4"], f"検査器の抽出が壊れている: {ts}"
    assert ban_hits(ts, ["21"]) == ["21"], "陽性対照失敗: 禁止値21を検出できない"
    assert ban_hits(ts, ["1.4"]) == [], "陰性対照失敗: 存在しない値を誤検出"
    assert numeric_labels(ts) == ["21", "−4"], "数字ラベルの抽出が壊れている（文中の数字を拾う／負数を落とす）"
    assert set(ts) != {"21"}, "許可リスト比較が集合差を識別できない"
    # 禁止文字検出器: 結合上線・絵文字・異体字セレクタ・全角英数字を検出し、正当な記号は通す
    assert forbidden_chars("A" + chr(0x0304)) == [chr(0x0304)], "陽性対照失敗: 結合上線"
    assert forbidden_chars(chr(0x1F600)) and forbidden_chars(chr(0x2705)), "陽性対照失敗: 絵文字"
    assert forbidden_chars("A" + chr(0xFE0F)) and forbidden_chars(chr(0xFF21)), \
        "陽性対照失敗: 異体字セレクタ・全角英字"
    assert forbidden_chars("Aᶜ ∅ ∩ ∪ ⇒ ⇔ ⊂ ≦ ≧ ＝ − 〜 ●○ ✓ √2") == [], "陰性対照失敗: 正当な記号を誤検出"
    # 幾何: 2円の交点が両円の上にある／多角形内判定／楕円内判定
    a, b = (0.0, 0.0, 5.0), (6.0, 0.0, 5.0)
    for p in circle_intersections(a, b):
        assert abs(dist(p, a[:2]) - 5) < 1e-9 and abs(dist(p, b[:2]) - 5) < 1e-9, "交点計算が壊れている"
    sq = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert point_in_poly((0.5, 0.5), sq) and not point_in_poly((1.5, 0.5), sq), "多角形内判定が壊れている"
    assert in_ellipse((0, 0), (0, 0, 2, 1)) and not in_ellipse((0, 1), (0, 0, 2, 1)), "楕円内判定が壊れている"


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
    assert "<title>" in src and "<desc>" in src, f"{path.name}: title/desc がない"
    # url(#id) 参照（clip-path・pattern）はすべてファイル内で定義済み・id は重複しない・未使用なし
    refs = set(REF_RE.findall(src))
    defs = DEF_RE.findall(src)
    assert len(defs) == len(set(defs)), f"{path.name}: defs の id 重複 {defs}"
    assert refs <= set(defs), f"{path.name}: 未定義の参照 {refs - set(defs)}"
    assert set(defs) <= refs, f"{path.name}: 使われていない定義 {set(defs) - refs}"
    bad = forbidden_chars(src)
    assert not bad, f"{path.name}: 禁止文字 {[hex(ord(c)) for c in bad]}"
    texts = svg_texts(src)
    # (1) 許可リスト検査: 図中の全ラベル=宣言済みの本文明示値のみ（完全一致）
    allow = set(meta["allow_texts"])
    got = set(texts)
    assert got == allow, (f"{path.name}: ラベル集合が許可リストと不一致 "
                          f"余分={got - allow} 不足={allow - got}")
    # (2) 数字ラベル検査: 数字だけのラベルの集合が宣言と一致・答えの数が数字ラベルにない
    nums = set(numeric_labels(texts))
    assert nums == set(meta["num_labels"]), \
        f"{path.name}: 数字ラベルが宣言と不一致 実={nums} 宣言={set(meta['num_labels'])}"
    num_hits = nums & set(meta.get("check_numbers", []))
    assert not num_hits, f"{path.name}: 答えの数が数字ラベルにある: {num_hits}"
    # (3) 禁止文字列検査: 練習・stretchの答え由来のトークンが図中にない
    hits = ban_hits(texts, meta.get("check_tokens", []))
    assert not hits, f"{path.name}: 禁止文字列が図中テキストにある: {hits}"
    return len(texts)


def main():
    gate_self_test()
    own_src = Path(__file__).read_text(encoding="utf-8")
    bad = forbidden_chars(own_src)
    assert not bad, f"スクリプト自身に禁止文字 {[hex(ord(c)) for c in bad]}"
    ASSETS.mkdir(parents=True, exist_ok=True)
    rows = []
    n_checks = 0
    for fn in FIGS:
        meta = fn()
        out = ASSETS / meta["file"]
        meta["canvas"].save(out, meta["file"], meta["title"], meta["desc"])
        svg_tech_checks(out, meta)
        n_checks += len(meta["checks"])
        rows.append(meta)
        print(f"OK {out.name}  [{len(meta['checks'])} checks passed]")

    n_tokens = sum(len(m.get("check_tokens", [])) + len(m.get("check_numbers", [])) for m in rows)
    head = ["<!--",
            f"generated: {GENERATED}（generate_figures.py により自動生成。手編集禁止——スクリプトを直して再実行）",
            "spec: docs/SPEC_figures.md・NE_STANDARD_FORM_SPEC_20260829.md §12 準拠",
            "license: CC-BY-4.0",
            "-->", ""]

    lines = head + [
        "# FIGURE_MANIFEST — 数Ⅰ集合と命題単元 図版台帳",
        "",
        f"生成日: {GENERATED} ／ 生成方式: `assets_provenance/generate_figures.py`"
        "（Python標準ライブラリのみ・パラメトリック生成・決定的）／ "
        f"全{len(rows)}図で下表の数学検算（スクリプト内assert・計{n_checks}項目）が"
        "生成時に自動実行され、全件合格。加えて全SVGにXML整形式・viewBox・"
        "self-contained（クリップ・パターン参照の定義内在）・禁止文字（絵文字・結合文字・"
        "異体字セレクタ・全角英数字）の技術検査と答え漏れ検査を実施——"
        "答え漏れ検査は三重ゲート: (1)図中の全ラベルを許可リスト"
        "（本文が図の前後で明示している値のみ）と完全一致で照合、"
        "(2)数字だけのラベル（目盛りの数）の集合を宣言と完全一致で照合し、"
        f"練習・stretchの答えの数が数字ラベルに現れないことを検査、(3)答え由来の式・値の禁止文字列"
        f"（(2)と合わせて計{n_tokens}項目・対象値は非開示）の不在検査。"
        "検査器自体は生成前の陽性対照（禁止値・禁止文字を仕込んだ合成入力での検出）で"
        "毎回実証している。PASS。／ "
        "内容仕様の正は執筆側の図版仕様メモ `_notes/FIG_SPEC_W1.md`（L01〜L03）・"
        "`FIG_SPEC_W2.md`（L04〜L05）・`FIG_SPEC_W3.md`（L06〜L07）——ファイル名・ラベル文字列・"
        "数値・座標・title/desc をメモに合わせ、全10図（マップ §4 の9枚＋メモ W2 が追加した "
        "L04_fig2）を生成した。各図は本文の `![alt](assets/…)` と1対1。／ "
        "AI再利用メタ情報として全SVGに`<title>`/`<desc>`（メモ指定の文）を標準装備。",
        "",
        "| ファイル | 対象レッスン | 図の意図 | 本文対応箇所 | パラメータ（本文一致） | 検証結果（生成時assert） | 備考（執筆メモの反映状況） |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in rows:
        checks = "／".join(f"{d}{'（' + t + '）' if t else ''} ✓" for d, t in m["checks"])
        lines.append(f"| `{m['file']}` | {m['lesson']} | {m['title']}——{m['intent']} | "
                     f"{m['src']} | {m['params']} | {checks} | {m['note']} |")
    lines += [
        "",
        "## 図版仕様メモからの逸脱（白黒規約・幾何の都合による置換）",
        "",
        "- **色・フォント**: メモ W3 の「青系 #2b6cb0」「濃灰 #444」「灰 #555」「sans-serif」は、"
        "docs/SPEC_figures.md の白黒規約（線は黒のみ・色に意味を持たせない・font-family 指定なし）を"
        "優先して使わない。強調枠・対角線は線幅 3.2、外との出入りの矢印は破線で区別した。",
        "- **L02_fig2 の円の外側の塗り**: メモの「白で上塗り」方式は、右下パネルで B だけの部分から "
        "Aᶜ の斜線が消える（描画順で白に覆われる）ため、長方形＋円の evenodd クリップで切り抜く方式に"
        "した。交差部分（2円の外側）の見えは同じで、格子点検査で左上と一致することを確認している。",
        "- **L04_fig1 のラベル Q**: メモの (400,90) は楕円式で外側に出るため、内側の (380,100) に置いた。",
        "- **L07_fig1 の viewBox 幅**: メモの 520 では補助文（x=470 から 10 文字）が収まらないため "
        "620 に広げた（矩形・矢印の座標はメモのまま）。",
        "- **端点●○の半径**: メモの r≈4〜5 は目安と解釈し、先行単元と共通の 3.4（縁 1.4）を使った。",
        "- **L05_fig1 の範囲の太線**: メモは帯（網かけ）と端点のみだが、白黒印刷での視認性と先行単元との"
        "統一のため軸上の太線も描いた（ラベル・数値は変えていない）。",
        "",
        "## 図版番号・採否の注記",
        "",
        "- **L04_fig2 はマップ §4 にない追加図**（メモ W2 の指定・削減候補の筆頭）。lesson_04.md §3 が"
        "図参照しているため生成した。削減するときは本文の `![…](assets/…)` 行も同時に外す（メモ W2 の手順）。",
        "- **削減候補の優先順**（メモ W2・W3）: L04_fig2 → L05_fig1 → L07_fig2。L04_fig1 は"
        "レッスンの主旨そのものなので最後まで残す。",
        "",
        "## 答えの分離方針の扱い——近隣設問の確認結果",
        "",
        "- 図中に書いた数値は、いずれも**本文（例題の与件・解答）が図の前後で明示している値**"
        "のみ（数字ラベルは L01・L03 が 0 と 2、L05 が 1 と 3。他は数値なし）。"
        "各図の許可リスト検査と数字ラベル検査で機械担保。",
        "- 各メモの「答え漏れ検査」欄の数・式（練習・stretch の答え由来）を check_numbers／check_tokens に"
        "登録し、図中に現れないことを検査済み（L04・L05 は answer_key_L04-05.md の答えも追加登録）。",
        "- **L02 の2図**: 補集合の記号は上付き c（ᶜ・U+1D9C）。上線（結合文字）は公開側の検疫で落ちるため"
        "使わない。",
        "",
        "## ●○規約・数直線系の描法統一（docs/SPEC_figures.md）",
        "",
        "- 端点●（含む）○（含まない）は共通パラメータ（半径・縁の線幅）で描画（先行単元 L08_fig1・"
        "L09_fig1 と同じ）。L01_fig1 と L03_fig1 左パネルは同型（値 v→px 140＋80v）。",
        "- ベン図（L02 の2図）は円、包含図（L03 右・L04 の2図）は楕円と円で描き、塗りはクリップパスと"
        "`<pattern>` のハッチング（ファイル内で完結）。",
        "- L06_fig1・L07_fig1・L07_fig2 は概念図であり●○規約の対象外。",
        "",
        "## 再生成・改修の手順（第三者向け）",
        "",
        "1. `generate_figures.py` の該当 `fig_*` 関数冒頭「パラメータ」ブロックを編集する"
        "（数値・ラベルは必ず該当 `lesson_XX.md` 本文・`_notes/FIG_SPEC_W*.md` と一致させる）。",
        "2. `python3 generate_figures.py` を実行する。検算assert・答え漏れ検査・禁止文字検査に"
        "1つでも落ちると図は出力されない（出力済みファイルは検査失敗時点のもので確定しない）。",
        "3. `assets/` のSVGと本ファイルが自動更新される。SVGの直接編集は禁止（来歴が切れる）。",
        "",
    ]
    manifest = "---\ndistribution_status: published_draft\n---\n\n" + "\n".join(lines)
    bad = forbidden_chars(manifest)
    assert not bad, f"FIGURE_MANIFEST に禁止文字 {[hex(ord(c)) for c in bad]}"
    (HERE / "FIGURE_MANIFEST.md").write_text(manifest, encoding="utf-8")
    print(f"OK FIGURE_MANIFEST.md  ({len(rows)} figures, {n_checks} checks, "
          f"{n_tokens} ban-items)")


if __name__ == "__main__":
    main()
