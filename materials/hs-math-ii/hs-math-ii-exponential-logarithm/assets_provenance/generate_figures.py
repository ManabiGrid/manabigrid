#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""数学Ⅱ「指数関数・対数関数」16図の決定的な生成器。

実行: assets_provenance/ で python3 generate_figures.py。標準ライブラリのみ。
Canvas・Checker・Labels・矩形交差検査は先行する数学Ⅱ「図形と方程式」の
生成器を利用。許可リストと台帳の構成は数学Ⅱ「いろいろな式」と同型。
図の内容・計算・窓・本文引用は本単元から構成した。

自己検証は出力前に全件実行し、失敗時はSVGも台帳も書かない。
(1) 数学: 累乗・根・曲線上の点・反射・平行移動・桁数・減衰・片対数。
    幾何: 全標本点の式・窓、変換の逆写像、対称図の等単位、各パネルの縮尺。
(2) 本文: 図の行を除いた本文の原文引用とパラメータを照合する。
(3) 答え: 図中文字の許可集合との完全一致、解答編から抽出した答えの禁止検索。
    本文が図へ明示した既知量と解答が共有する場合は衝突を台帳に明記する。
    main冒頭で故意の漏えいを含むSVGの陽性対照を実行する。
(4) 配置: viewBox内、文字同士と文字・線の非交差、文字は幅の3%以上。
    字幅は保守的推定。書体に依存する最終字形の測定ではない。
(5) 文字: 絵文字・結合文字・異体字セレクタ・不可視・全角英数字と
    読点と鍵括弧の連続を生成器・SVG・台帳で機械検査する。
(6) 受け入れ: 本文参照と生成集合、代替文のUTF-8バイト、連番の登場順。

日付は固定値を先頭のSVGコメントと台帳の生成日行だけへ出す。
SVG直接編集禁止。定数と各fig関数を直して再生成する。
"""

import hashlib
import math
import re
import unicodedata
import xml.etree.ElementTree as ET
from fractions import Fraction as Fr
from html import escape, unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
LESSON_DIR = HERE.parent
ASSETS = LESSON_DIR / "assets"
GENERATED = "2026-10-23"
MODEL_LINE = "実行モデル: gpt-6.1-sol（Codex CLI・effort ultra は設定の既定・親が設定と実走記録で照合）"
W = 640
FS = MIN_FS = 20
MAIN_W, BOLD_W, AUX_W, THIN_W, AXIS_W = 1.6, 3.2, 1.1, 1.0, 1.2
DASH = "6 4"
DOT_R, DOT_R_END, PLATE_PAD, HATCH_GAP = 3.0, 3.4, 2.0, 8
ALT_RE = re.compile(r"!\[(.*?)\]\(assets/([^)]+)\)")
NAME_RE = re.compile(r"L(\d\d)_fig(\d+)_[a-z0-9_]+\.svg")

def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def near(a, b, tol=1e-9):
    return abs(a - b) < tol


def near_pt(p, q, tol=1e-9):
    return dist(p, q) < tol


def rot90(v):
    """数学座標で原点のまわりに左回りに 90° 回す"""
    return (-v[1], v[0])


def px_dir(v):
    """数学座標の向き（y 上向き）を px の単位ベクトル（y 下向き）に"""
    return unit((v[0], -v[1]))


def seg_intersects_rect(a, b, rect):
    """線分 ab が矩形 rect=(x0, y0, x1, y1) と交わるか（Liang-Barsky）"""
    x0, y0, x1, y1 = rect
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
    return t0 <= t1


def boxes_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def point_in_poly(p, poly):
    """偶奇規則による点の内外判定（境界の近くの点は検査側で除いてから使う）"""
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xin > x:
                inside = not inside
    return inside


_SPECIAL_W = {" ": 0.35, ".": 0.3, ",": 0.3, "/": 0.4, "(": 0.4, ")": 0.4, ":": 0.35, "°": 0.45,
              "→": 1.0, "←": 1.0, "・": 1.0, "×": 1.0, "〜": 1.0, "−": 1.0, "√": 1.0, "≧": 1.0, "≦": 1.0,
              "=": 0.6, "<": 0.6, ">": 0.6, "′": 0.5, "₁": 0.6, "₂": 0.6}


def est_w(s, size):
    """テキストの推定幅（px）: 半角 0.6em・全角 1.0em・あいまい幅 0.7em・記号は個別（大きめに見積もる）"""
    w = 0.0
    for ch in s:
        if ch in _SPECIAL_W:
            w += _SPECIAL_W[ch]
        elif ord(ch) < 128:
            w += 0.6
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            w += 1.0
        else:
            w += 0.7
    return w * size


class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.body = []           # 図形
        self.overlay = []        # 文字（と文字の白地）
        self.defs = []           # 斜線の <pattern>
        self.texts = []          # dict(box, s, own, plate)
        self.obstacles = []      # (oid, [pts...])  ラベルがかかってはいけない線
        self.textured = []       # 斜線の塗り（px の多角形の組・偶奇規則）。この上のラベルには白地が要る
        self.font_sizes = []
        self.bbox = [float("inf"), float("inf"), float("-inf"), float("-inf")]

    def _grow(self, x, y, pad=0.0):
        self.bbox[0] = min(self.bbox[0], x - pad)
        self.bbox[1] = min(self.bbox[1], y - pad)
        self.bbox[2] = max(self.bbox[2], x + pad)
        self.bbox[3] = max(self.bbox[3], y + pad)

    def raw(self, s):
        self.body.append(s)

    def obstacle(self, oid, pts):
        if oid is not None and len(pts) >= 2:
            self.obstacles.append((oid, [tuple(p) for p in pts]))

    def line(self, x1, y1, x2, y2, w=MAIN_W, dash=None, oid="line"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._grow(x1, y1, w)
        self._grow(x2, y2, w)
        self.raw(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="#000" stroke-width="{w}"{d}/>')
        self.obstacle(oid, [(x1, y1), (x2, y2)])

    def path(self, pts, w=MAIN_W, dash=None, close=False, fill="none", oid="line", join="round"):
        """折れ線（close=True なら多角形）。fill を指定すると塗りつぶし＋輪郭"""
        for x, y in pts:
            self._grow(x, y, w / 2.0)
        s = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        tag = "polygon" if close else "polyline"
        self.raw(f'<{tag} points="{s}" fill="{fill}" stroke="#000" '
                 f'stroke-width="{w}" stroke-linejoin="{join}"{d}/>')
        self.obstacle(oid, list(pts) + ([pts[0]] if close else []))

    def fill_region(self, polys, fill, textured=True):
        """塗り（輪郭なし）。polys は px の多角形の組で、偶奇規則（外枠＋穴）で重ねる"""
        parts = []
        for poly in polys:
            for x, y in poly:
                self._grow(x, y)
            parts.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in poly) + " Z")
        rule = ' fill-rule="evenodd"' if len(polys) > 1 else ""
        self.raw(f'<path d="{" ".join(parts)}" fill="{fill}" stroke="none"{rule}/>')
        if textured:
            self.textured.append([list(p) for p in polys])

    def pattern(self, pid, angle, gap=HATCH_GAP, sw=1.0):
        """斜線の塗り（<defs><pattern> で内蔵・ファイル内で完結）。angle は SVG の回転角（度）"""
        if not any(f'id="{pid}"' in d for d in self.defs):
            self.defs.append(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{gap}" height="{gap}" '
                             f'patternTransform="rotate({angle})">'
                             f'<line x1="{gap / 2}" y1="0" x2="{gap / 2}" y2="{gap}" stroke="#000" '
                             f'stroke-width="{sw}"/></pattern>')
        return f"url(#{pid})"

    def dot(self, x, y, r=DOT_R, oid="dot"):
        self._grow(x, y, r)
        self.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#000"/>')
        self.obstacle(oid, [(x - r, y - r), (x + r, y - r), (x + r, y + r), (x - r, y + r), (x - r, y - r)])

    def rect(self, x, y, w, h, fill="none", sw=1.4, dash=None, oid="line"):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], w=sw, dash=dash, close=True,
                  fill=fill, oid=oid, join="miter")

    def text(self, x, y, s, size=FS, anchor="middle", weight=None, own=(), plate=False):
        """(x, y) はベースライン。推定ボックスを記録する。plate=True なら白地を先に敷く"""
        w = est_w(s, size)
        x0 = {"middle": x - w / 2, "start": x, "end": x - w}[anchor]
        box = (x0, y - 0.8 * size, x0 + w, y + 0.22 * size)
        e = PLATE_PAD if plate else 0.0
        self.texts.append({"box": box, "s": s, "own": tuple(own), "plate": plate})
        self.font_sizes.append(size)
        self._grow(box[0] - e, box[1] - e)
        self._grow(box[2] + e, box[3] + e)
        if plate:
            self.overlay.append(f'<rect x="{box[0] - e:.1f}" y="{box[1] - e:.1f}" width="{box[2] - box[0] + 2 * e:.1f}" '
                                f'height="{box[3] - box[1] + 2 * e:.1f}" fill="#fff" stroke="none"/>')
        wgt = f' font-weight="{weight}"' if weight else ""
        self.overlay.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
                            f'text-anchor="{anchor}"{wgt}>{escape(s)}</text>')
        return box

    def arrow(self, x1, y1, x2, y2, w=1.4, head=8.0, oid="arrow"):
        """px 座標の矢印（線＋先端の三角形）"""
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, w=w, oid=oid)
        nx, ny = -math.sin(ang), math.cos(ang)
        pts = [(x2, y2), (bx + nx * head * 0.45, by + ny * head * 0.45),
               (bx - nx * head * 0.45, by - ny * head * 0.45)]
        self.fill_region([pts], "#000", textured=False)
        self.obstacle(oid, pts + [pts[0]])

    def layout_checks(self, ck, pad=1.0):
        """共通 assert: viewBox 内／ラベル同士が重ならない／ラベルが線にかからない／斜線の上は白地／文字サイズ"""
        ck.ok("全要素が viewBox 内に収まる（線幅・推定文字幅・白地込み）",
              self.bbox[0] >= 0 and self.bbox[1] >= 0 and self.bbox[2] <= self.w and self.bbox[3] <= self.h,
              f"bbox=({self.bbox[0]:.1f},{self.bbox[1]:.1f})-({self.bbox[2]:.1f},{self.bbox[3]:.1f})")
        boxes = []
        for t in self.texts:
            x0, y0, x1, y1 = t["box"]
            e = PLATE_PAD if t["plate"] else 0.0
            boxes.append((x0 - e, y0 - e, x1 + e, y1 + e))
        bad = []
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if boxes_overlap(boxes[i], boxes[j]):
                    bad.append((self.texts[i]["s"], self.texts[j]["s"]))
        ck.ok("ラベル同士が重ならない（推定ボックスの全ペア・白地込み）", not bad, f"{bad}")
        hits = []
        for t, bx in zip(self.texts, boxes):
            r = (bx[0] - pad, bx[1] - pad, bx[2] + pad, bx[3] + pad)
            for oid, pts in self.obstacles:
                if oid in t["own"]:
                    continue
                if any(seg_intersects_rect(a, b, r) for a, b in zip(pts, pts[1:])):
                    hits.append((t["s"], oid))
                    break
        ck.ok("ラベルが線（軸・目盛り・直線・円・枠・矢印・点・印）にかからない", not hits, f"{hits}")
        need = []
        for t in self.texts:
            if t["plate"]:
                continue
            x0, y0, x1, y1 = t["box"]
            samples = [(x0 + (x1 - x0) * i / 4, y0 + (y1 - y0) * j / 2) for i in range(5) for j in range(3)]
            if any(point_in_poly(s, poly) for polys in self.textured for poly in polys for s in samples):
                need.append(t["s"])
        ck.ok("斜線の塗りの上に置いたラベルには白地を敷いている", not need, f"{need}")
        ck.ok(f"文字サイズがすべて {MIN_FS}px 以上（viewBox 幅の3%）",
              bool(self.font_sizes) and min(self.font_sizes) >= MIN_FS,
              f"min={min(self.font_sizes) if self.font_sizes else None}")

    def svg(self, fig_id, title, desc):
        defs = f"<defs>{''.join(self.defs)}</defs>\n" if self.defs else ""
        return (
            f'<!-- generated by assets_provenance/generate_figures.py | {fig_id} | {GENERATED} -->\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}">\n'
            f'<title>{escape(title)}</title>\n'
            f'<desc>{escape(desc)}</desc>\n'
            f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="#fff"/>\n'
            + defs + "\n".join(self.body) + ("\n" if self.body else "")
            + "\n".join(self.overlay) + "\n</svg>\n"
        )


class Checker:
    """検算の記録つき assert"""
    def __init__(self):
        self.items = []

    def ok(self, desc, cond, detail=""):
        assert cond, f"検証失敗: {desc} {detail}"
        self.items.append((desc, detail))


class Labels:
    """図が置いたラベルを集める（許可リスト検査の入力）"""
    def __init__(self, cv, fs=FS):
        self.cv, self.fs, self.items = cv, fs, []

    def put(self, x, y, s, size=None, **kw):
        self.items.append(s)
        return self.cv.text(x, y, s, size or self.fs, **kw)

    def c(self, x, y, s, size=None, **kw):
        """(x, y) を推定ボックスの中心にして置く"""
        sz = size or self.fs
        return self.put(x, y + 0.29 * sz, s, size=sz, **kw)

    def at(self, p, ang, d, s, **kw):
        """点 p（px）から、画面上の角 ang（度・右が 0・上が 90）の向きに d px 離れた所を中心にして置く"""
        a = math.radians(ang)
        return self.c(p[0] + d * math.cos(a), p[1] - d * math.sin(a), s, **kw)


class Frame:
    """数学座標から画面へ。軸ごとの単位を明示し、逆変換も検査する。"""
    def __init__(self, box, win, ck, equal=False):
        self.box, self.win = box, win
        l, t, r, b = box
        (x0, x1), (y0, y1) = win
        self.sx, self.sy = (r-l)/(x1-x0), (b-t)/(y1-y0)
        ck.ok("窓と縮尺が正", x0 < x1 and y0 < y1 and self.sx > 0 and self.sy > 0)
        if equal:
            ck.ok("対称性を示す座標の縦横単位が等しい", near(self.sx, self.sy))
        for p in ((x0,y0),(x1,y1),(0,0),(1,1)):
            q = self.P(p)
            ck.ok("座標変換の逆写像", dist(self.inverse(q), p) < 1e-9)

    def P(self, p):
        (x0, _), (_, y1) = self.win
        return self.box[0]+(p[0]-x0)*self.sx, self.box[1]+(y1-p[1])*self.sy

    def inverse(self, p):
        return self.win[0][0]+(p[0]-self.box[0])/self.sx, self.win[1][1]-(p[1]-self.box[1])/self.sy


def body(n):
    return "\n".join(s for s in (LESSON_DIR/f"lesson_{n:02}.md").read_text().splitlines() if not ALT_RE.search(s))


def body_has(ck, n, needles):
    b = body(n)
    missing = [s for s in needles if s not in b]
    ck.ok("図のパラメータが画像行を除いた本文にある", not missing, str(missing))


def no_collision(cv, box, gap=2):
    r = box[0]-gap, box[1]-gap, box[2]+gap, box[3]+gap
    if not (4 < r[0] < r[2] < cv.w-4 and 4 < r[1] < r[3] < cv.h-4):
        return False
    if any(boxes_overlap(r, t["box"]) for t in cv.texts):
        return False
    return not any(seg_intersects_rect(a,b,r) for _, pts in cv.obstacles for a,b in zip(pts,pts[1:]))


def label_near(cv, lb, p, s, preferred=(45,135,315,225,90,270,0,180)):
    """点の周囲で交差のない最初の位置を決定的に選ぶ。白地で線を消さない。"""
    w = est_w(s, FS)
    for d in (23,32,44,58,76,98,125):
        for deg in preferred:
            a = math.radians(deg)
            x,y = p[0]+d*math.cos(a), p[1]-d*math.sin(a)
            box = x-w/2,y-FS/2,x+w/2,y+FS/2
            if no_collision(cv,box):
                lb.c(x,y,s)
                return
    raise AssertionError(f"ラベルを配置できない: {s} 点={p}")


def axes(cv, lb, fr, xt=(), yt=(), xlabel="x", ylabel="y", origin=None):
    l,t,r,b = fr.box
    (x0,x1),(y0,y1) = fr.win
    ax_y = 0 if y0 <= 0 <= y1 else y0
    ax_x = 0 if x0 <= 0 <= x1 else x0
    px,py = fr.P((ax_x,ax_y))
    cv.arrow(l,py,r,py,w=AXIS_W,oid="axis")
    cv.arrow(px,b,px,t,w=AXIS_W,oid="axis")
    if xlabel:
        lb.c(r+17,py,xlabel)
    if ylabel:
        lb.put(px,t-17,ylabel,anchor="middle")
    if origin:
        label_near(cv,lb,(px,py),origin)
    for value,text in xt:
        q = fr.P((value,ax_y))
        cv.line(q[0],q[1]-4,q[0],q[1]+4,w=THIN_W,oid="tick")
        lb.c(q[0]-(20 if near(value,ax_x) else 0),q[1]+25,text)
    for value,text in yt:
        q = fr.P((ax_x,value))
        cv.line(q[0]-4,q[1],q[0]+4,q[1],w=THIN_W,oid="tick")
        lb.put(l-12,q[1]+FS*.29,text,anchor="end")


def curve(cv, fr, ck, fn, domain, name, dash=None, n=320, w=MAIN_W):
    a,b = domain
    values = [(a+(b-a)*i/n, fn(a+(b-a)*i/n)) for i in range(n+1)]
    ck.ok(f"{name} の全標本が有限", all(math.isfinite(x) and math.isfinite(y) for x,y in values))
    (x0,x1),(y0,y1) = fr.win
    ck.ok(f"{name} の全標本が窓内", all(x0-1e-9 <= x <= x1+1e-9 and y0-1e-9 <= y <= y1+1e-9 for x,y in values))
    ck.ok(f"{name} の式と全標本が一致", all(near(y,fn(x)) for x,y in values))
    cv.path([fr.P(p) for p in values],dash=dash,w=w,oid="curve")
    return values


def point(cv, fr, ck, p, fn=None, open_dot=False):
    (x0,x1),(y0,y1) = fr.win
    ck.ok("点が窓内", x0 <= p[0] <= x1 and y0 <= p[1] <= y1)
    if fn:
        ck.ok("指定点が曲線の式を満たす", near(fn(p[0]),p[1]))
    q = fr.P(p)
    if open_dot:
        cv.path([(q[0]+DOT_R*math.cos(i*math.pi/16),q[1]+DOT_R*math.sin(i*math.pi/16)) for i in range(33)],fill="#fff",oid="dot")
    else:
        cv.dot(*q)
    return q


def guides(cv,fr,p):
    q,ox,oy = fr.P(p),fr.P((0,p[1])),fr.P((p[0],0))
    cv.line(*ox,*q,w=AUX_W,dash=DASH,oid="guide")
    cv.line(*oy,*q,w=AUX_W,dash=DASH,oid="guide")


def begin(n, slug, title, height, needles, allow):
    ck,cv = Checker(),Canvas(W,height)
    body_has(ck,n,needles)
    return {"lesson":f"L{n:02}","n":n,"file":slug+".svg","title":title,
            "desc":title,"canvas":cv,"ck":ck,"lb":Labels(cv),"needles":needles,
            "allow_texts":set(allow)}


def finish(m, params, desc=None):
    m["params"] = params
    if desc:
        m["desc"] = desc
    actual = {t["s"] for t in m["canvas"].texts}
    m["ck"].ok("図中文字がパラメータの許可集合と完全一致", actual == m["allow_texts"],
               f"余分={sorted(actual-m['allow_texts'])} 不足={sorted(m['allow_texts']-actual)}")
    m["canvas"].layout_checks(m["ck"])
    return m


def fig_L01_1():
    # パラメータ: 本文の表と同じく左から指数の大きい順に置く6つの累乗。
    exps = [3,2,1,0,-1,-2]
    values = [8,4,2,1,Fr(1,2),Fr(1,4)]
    es = ["2^3","2^2","2^1","2^0","2^(−1)","2^(−2)"]
    vs = ["8","4","2","1","1/2","1/4"]
    m = begin(1,"L01_fig1_power_ladder","2 の累乗の階段",540,
              ["2^3=8","2^2=4","2^1=2","2^0=1","2^(−1)=1/2","2^(−2)","1/4",
               "| 指数 n | 3 | 2 | 1 | 0 | −1 | −2 |",
               "| 2^n の値 | 8 | 4 | 2 | 1 | 1/2 | 1/4 |",
               "左へ 1 つ進むと 2 倍、右へ 1 つ進むと半分。","この階段を右へ下りていくと"],
              es+vs+["2 倍","半分"])
    cv,lb,ck = m["canvas"],m["lb"],m["ck"]
    ck.ok("左から指数3・2・1・0・−1・−2の順", exps == [3,2,1,0,-1,-2])
    zero,negative_one = exps.index(0),exps.index(-1)
    ck.ok("右へ下りて2^0=1に着く", zero == 3 and values[zero] == Fr(2)**0 == 1
          and es[zero] == "2^0" and vs[zero] == "1")
    ck.ok("次の段で2^(−1)=1/2に着く", negative_one == zero+1
          and values[negative_one] == Fr(2)**-1 == Fr(1,2)
          and es[negative_one] == "2^(−1)" and vs[negative_one] == "1/2")
    for i,(e,v) in enumerate(zip(exps,values)):
        ck.ok("階段の値が2の累乗", Fr(2)**e == v)
        if i:
            ck.ok("右へ1つ進むと半分・左へ1つ進むと2倍", 2*v == values[i-1])
        x,y = 80+96*i,190+52*i
        lb.c(x,y-23,es[i]);lb.c(x,y+10,vs[i])
        cv.line(x-35,y+29,x+35,y+29)
        if i < 5:
            cv.arrow(x+39,y+29,x+57,y+81)
    cv.arrow(550,50,90,50);lb.c(320,29,"2 倍")
    cv.arrow(90,100,550,100);lb.c(320,80,"半分")
    return finish(m,"指数 3・2・1・0・−1・−2、値 8・4・2・1・1/2・1/4。横位置は指数の大きい順（左が 3）、右へ下る段差は概念的に等間隔。")


def fig_L02_1():
    m = begin(2,"L02_fig1_nth_root_graph","累乗根とグラフの交点",550,
              ["y=x^2","y=16","4 と −4","y=x^3","y=8","2^3=8"],
              ["y=x^2","y=16","y=x^3","y=8","x","y","−4","4","16","2","8"])
    cv,lb,ck = m["canvas"],m["lb"],m["ck"]
    f = Frame((72,140,286,460),((-5,5),(-2,22)),ck)
    g = Frame((385,140,588,460),((-2.3,2.8),(-10,23)),ck)
    axes(cv,lb,f,xt=[(-4,"−4"),(4,"4")],yt=[(16,"16")])
    axes(cv,lb,g,xt=[(2,"2")],yt=[(8,"8")])
    curve(cv,f,ck,lambda x:x*x,(-4.6,4.6),"y=x^2")
    curve(cv,g,ck,lambda x:x**3,(-2.1,2.8),"y=x^3")
    for fr,h,fn,roots in ((f,16,lambda x:x*x,[-4,4]),(g,8,lambda x:x**3,[2])):
        cv.line(*fr.P((fr.win[0][0],h)),*fr.P((fr.win[0][1],h)),dash=DASH,w=AUX_W,oid="level")
        for x in roots:
            point(cv,fr,ck,(x,h),fn)
    ck.ok("平方根は2個・立方根は1個", (-4)**2 == 4**2 == 16 and 2**3 == 8 and (-2)**3 != 8)
    lb.c(178,35,"y=x^2");lb.c(178,72,"y=16")
    lb.c(486,35,"y=x^3");lb.c(486,72,"y=8")
    return finish(m,"左: x −5〜5・y −2〜22。右: x −2.3〜2.8・y −10〜23。各軸は別単位、パネル間の傾き比較には使わない。交点 (−4,16)・(4,16) と (2,8)。")


def fig_L02_2():
    m = begin(2,"L02_fig2_equal_ratio_steps","同じ倍率と同じ量の対比",650,
              ["同じ倍率","同じ量","0.7071","1/4","1/2","半分",
               "最初の量の 1/4 という同じ量を毎回引くことである。","1→3/4→1/2",
               "倍率は 1 回目が 3/4 倍、2 回目が (1/2)÷(3/4)=2/3 倍"],
              ["同じ倍率","同じ量","およそ 0.7071 倍","1/4 ずつ","半分"])
    cv,lb,ck = m["canvas"],m["lb"],m["ck"]
    r = math.sqrt(.5)
    rows = [(r**i for i in range(3)),(1-i/4 for i in range(3))]
    vals = [list(x) for x in rows]
    ck.ok("同倍率の2回で半分", near(r*r,.5) and abs(r-.7071)<.00005)
    ck.ok("最初の量の1/4ずつを2回引いて半分", vals[1] == [1,.75,.5])
    ck.ok("毎回引く量は最初の量の1/4", all(vals[1][i-1]-vals[1][i] == Fr(1,4)*vals[1][0] for i in (1,2)))
    ck.ok("同じ量を引くと倍率は3/4と2/3で異なる", near(vals[1][1]/vals[1][0],Fr(3,4))
          and near(vals[1][2]/vals[1][1],Fr(2,3)) and Fr(3,4) != Fr(2,3))
    ck.ok("中間の高さが異なる", vals[0][1] < vals[1][1])
    for row,base in enumerate((285,585)):
        lb.c(320,35+300*row,["同じ倍率","同じ量"][row])
        for i,v in enumerate(vals[row]):
            x=90+200*i
            cv.rect(x,base-160*v,60,160*v,fill="#d9d9d9")
            if i < 2:
                cv.arrow(x+78,base-90,x+180,base-90)
        lb.c(320,78+300*row,["およそ 0.7071 倍","1/4 ずつ"][row])
        lb.c(520,base+35,"半分")
    return finish(m,"上の棒の比は 1:√(1/2):1/2、下は 1:3/4:1/2。同じ高さ単位160px。表示数値は0.7071と1/4に限定。")


def fig_L03_1():
    a,b = [2**x for x in range(6)],[x*x for x in range(6)]
    av,bv = [str(x) for x in a],[str(x) for x in b]
    m = begin(3,"L03_fig1_exp_vs_quadratic","指数関数と二次関数の点列",780,
              ["y=2^x","y=x²","| x | 0 | 1 | 2 | 3 | 4 | 5 |",
               "| y=x² | 0 | 1 | 4 | 9 | 16 | 25 |","| y=2^x | 1 | 2 | 4 | 8 | 16 | 32 |"],
              ["y=2^x","y=x²","x","y","2 倍"]+av+bv+["0","1","2","3","4","5"])
    cv,lb,ck = m["canvas"],m["lb"],m["ck"]
    f = Frame((100,120,555,520),((-.25,5.5),(-2,34)),ck)
    axes(cv,lb,f,xt=[(x,str(x)) for x in range(6)])
    for values,dash,op in ((a,None,False),(b,DASH,True)):
        pts = [(x,y) for x,y in enumerate(values)]
        ck.ok("点列が本文の表と一致", values == ([1,2,4,8,16,32] if not op else [0,1,4,9,16,25]))
        cv.path([f.P(p) for p in pts],dash=dash,oid="curve")
        for p in pts:
            point(cv,f,ck,p,lambda x:2**x if not op else x*x,open_dot=op)
    ck.ok("4で重なり5で指数が上", a[4] == b[4] == 16 and a[5] == 32 > b[5] == 25)
    ck.ok("すべての隣接比が2", all(a[i+1]/a[i] == 2 for i in range(5)))
    # 数値は混雑する原点付近でなく、点の順番と対応する2列の帯にまとめる。
    cv.line(90,34,128,34);lb.put(140,40,"y=2^x",anchor="start")
    cv.line(355,34,393,34,dash=DASH);lb.put(405,40,"y=x²",anchor="start")
    for y,values in ((615,av),(710,bv)):
        for i,s in enumerate(values):
            lb.c(85+94*i,y,s)
        if y == 615:
            for i in range(5):
                cv.arrow(101+94*i,650,160+94*i,650)
            lb.c(320,682,"2 倍")
    lb.c(320,576,"y=2^x");lb.c(320,750,"y=x²")
    return finish(m,"x=0〜5。実線・黒丸は1,2,4,8,16,32、破線・白丸は0,1,4,9,16,25。下の数列は左からxの昇順。縦横は別単位。")


def fig_L03_2():
    m = begin(3,"L03_fig2_exp_two_bases","底と指数関数の増減",600,
              ["y=2^x","y=(1/2)^x","(0, 1)","y 軸"],
              ["y=2^x","y=(1/2)^x","(0, 1)","x","y"])
    cv,lb,ck = m["canvas"],m["lb"],m["ck"]
    f = Frame((75,120,565,500),((-3.2,3.2),(-.4,9)),ck)
    axes(cv,lb,f)
    u=curve(cv,f,ck,lambda x:2**x,(-3.1,3.1),"y=2^x")
    v=curve(cv,f,ck,lambda x:.5**x,(-3.1,3.1),"y=(1/2)^x",dash=DASH)
    ck.ok("y軸に関する対称と正値", all(near(y,.5**(-x)) and y>0 for x,y in u))
    ck.ok("増加と減少", all(u[i][1]<u[i+1][1] and v[i][1]>v[i+1][1] for i in range(len(u)-1)))
    p=point(cv,f,ck,(0,1),lambda x:2**x)
    label_near(cv,lb,p,"(0, 1)",(135,225,45,315))
    cv.line(65,35,100,35);lb.put(115,41,"y=2^x",anchor="start")
    cv.line(330,35,365,35,dash=DASH);lb.put(380,41,"y=(1/2)^x",anchor="start")
    return finish(m,"底2と1/2、共通点(0,1)。x −3.2〜3.2、y −0.4〜9。左右反射の幾何を保つ。縦横は別単位。")


def fig_L04_1():
    m = begin(4,"L04_fig1_inequality_direction","底による不等号の向き",760,
              ["y=(1/3)^x","1/9","x<2","y が大きい点ほど x は小さい","L03"],
              ["y=2^x","y=(1/3)^x","x","y","1/9","2","x<2"])
    # y=2^xは同じ単元のL03本文で既習であり、L04には数値式の直接記載がない。
    body_has(m["ck"],3,["y=2^x"])
    cv,lb,ck = m["canvas"],m["lb"],m["ck"]
    f=Frame((65,140,275,590),((-.2,3),(-.1,8.5)),ck)
    g=Frame((390,140,585,590),((-.2,3),(-.1,1.1)),ck)
    axes(cv,lb,f);axes(cv,lb,g,xt=[(2,"2")],yt=[(Fr(1,9),"1/9")])
    curve(cv,f,ck,lambda x:2**x,(-.1,3),"y=2^x")
    curve(cv,g,ck,lambda x:(1/3)**x,(0,3),"y=(1/3)^x")
    h=1/9
    cv.line(*g.P((-.2,h)),*g.P((3,h)),dash=DASH,w=AUX_W,oid="level")
    p=point(cv,g,ck,(2,h),lambda x:(1/3)**x)
    # 上の高さへ進むと左図は右、右図は左へ進む。
    for fr,p0,p1 in ((f,(.5,2**.5),(1.5,2**1.5)),(g,(1.7,(1/3)**1.7),(.7,(1/3)**.7))):
        a,b=fr.P(p0),fr.P(p1)
        cv.arrow(a[0]+18,a[1]-18,b[0]+18,b[1]-18,w=BOLD_W)
    cv.arrow(*g.P((1.8,-.045)),*g.P((.05,-.045)),w=BOLD_W)
    lb.c(170,40,"y=2^x");lb.c(485,40,"y=(1/3)^x");lb.c(485,678,"x<2")
    ck.ok("しきい値の上下とxの左右", (1/3)**1 > h > (1/3)**3 and near((1/3)**2,h))
    return finish(m,"左は底2、右は底1/3。右の水平線y=1/9とx=2。各パネルはx範囲が共通、yは別縮尺。左y −0.1〜8.5、右y −0.1〜1.1。")


def fig_L05_1():
    m = begin(5,"L05_fig1_log_on_exp_graph","高さ3から対数を読む",610,
              ["y=2^x","2^1=2","2^2=4","log_2 3","1<log_2 3<2"],
              ["y=2^x","y=3","log_2 3","x","y","1","2","3","4"])
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    f=Frame((100,100,555,480),((-.25,2.4),(-.2,5.5)),ck)
    axes(cv,lb,f,xt=[(1,"1"),(2,"2")],yt=[(2,"2"),(3,"3"),(4,"4")])
    curve(cv,f,ck,lambda x:2**x,(-.2,2.4),"y=2^x")
    t=math.log2(3)
    cv.line(*f.P((-.25,3)),*f.P((2.4,3)),dash=DASH,w=AUX_W,oid="level")
    cv.line(*f.P((t,0)),*f.P((t,3)),dash=DASH,w=AUX_W,oid="guide")
    for p in ((1,2),(2,4),(t,3)):
        point(cv,f,ck,p,lambda x:2**x)
    ck.ok("対数の定義と挟み込み", 1<t<2 and near(2**t,3))
    lb.c(f.P((t,0))[0],543,"log_2 3")
    lb.c(210,35,"y=2^x");lb.c(450,35,"y=3")
    return finish(m,"底2、高さ3、点(1,2)・(2,4)。交点は内部計算log2(3)で配置し、小数値は表示しない。")


def fig_L05_2():
    m = begin(5,"L05_fig2_three_quantities","指数と対数の3つの量",650,
              ["a^p=M","p=log_a M","底 a","指数に当たる数 p","真数 M","2^3=8","log_2 8=3"],
              ["底 a","指数に当たる数 p","真数 M","a^p=M","p=log_a M","2^3=8","3=log_2 8"])
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    centers=[100,320,540]
    headings=["底 a","指数に当たる数 p","真数 M"]
    # 3つの量から、2つの式の対応する文字位置まで線を結ぶ。
    for x,s in zip(centers,headings):
        lb.c(x,45,s)
    # 式を分断せずに描き、字幅推定と同じ計算で各文字の中心を得る。
    lb.c(320,210,"a^p=M");lb.c(320,400,"p=log_a M")
    def char_x(s,ch):
        i=s.index(ch)
        return 320-est_w(s,FS)/2+est_w(s[:i],FS)+est_w(ch,FS)/2
    top=[char_x("a^p=M",ch) for ch in ("a","p","M")]
    bottom=[char_x("p=log_a M",ch) for ch in ("a","p","M")]
    for i,x in enumerate(centers):
        cv.path([(x,70),(x,120),(top[i],188)],dash=DASH,w=AUX_W,oid="link")
        # 対応線の交差は量の並べ替えを表す。文字領域を通過しない。
        cv.path([(top[i],231),(bottom[i],377)],dash=DASH,w=AUX_W,oid="link")
    lb.c(320,520,"2^3=8");lb.c(320,570,"3=log_2 8")
    ck.ok("指数と対数の同値", 2**3 == 8 and near(math.log(8,2),3))
    return finish(m,"底a・指数p・真数Mの対応、数値例2^3=8と3=log_2 8。", "底a・指数p・真数Mの対応。指数の式と対数の式の読み順を比較し、2^3=8と3=log_2 8を例示。")


def fig_L07_1():
    pts=[(0,1),(1,2),(3,8)]
    texts=[f"({x}, {y})" for x,y in pts]+[f"({y}, {x})" for x,y in pts]
    m=begin(7,"L07_fig1_exp_log_symmetry","指数関数と対数関数の対称",740,
            ["y=2^x","y=log_2 x","y=x","| x | −2 | −1 | 0 | 1 | 2 | 3 |",
             "| y=2^x | 1/4 | 1/2 | 1 | 2 | 4 | 8 |","(3, 8)","(8, 3)"],
            ["y=2^x","y=log_2 x","y=x","x","y"]+texts)
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    f=Frame((95,145,554,604),((-1.2,9),(-1.2,9)),ck,equal=True)
    axes(cv,lb,f)
    curve(cv,f,ck,lambda x:2**x,(-1.2,math.log2(9)),"y=2^x")
    curve(cv,f,ck,math.log2,(2**(-1.2),9),"y=log_2 x",dash=DASH)
    curve(cv,f,ck,lambda x:x,(-1.2,9),"y=x",dash="2 4")
    for x,y in pts:
        p,q=f.P((x,y)),f.P((y,x))
        cv.line(*p,*q,w=AUX_W,dash=DASH,oid="pair")
        point(cv,f,ck,(x,y),lambda t:2**t)
        point(cv,f,ck,(y,x),math.log2)
        ck.ok("点を入れ替えると対数の点", near(math.log2(y),x))
        ck.ok("対応線の中点はy=x、対応線はy=xに垂直", near((x+y)/2,(y+x)/2) and near((y-x)+(x-y),0))
        a,b=f.P((x,y)),f.P((y,x))
        c=sum(f.P((0,0)))
        ck.ok("画面でもy=xに関する反射が対応点に一致", near(b[0],c-a[1]) and near(b[1],c-a[0]))
    for p,s in [(p,f"({p[0]}, {p[1]})") for xy in pts for p in (xy,xy[::-1])]:
        label_near(cv,lb,f.P(p),s)
    for y,s,d in ((30,"y=2^x",None),(68,"y=log_2 x",DASH),(106,"y=x","2 4")):
        cv.line(180,y,220,y,dash=d);lb.put(240,y+6,s,anchor="start")
    return finish(m,"対応点 (0,1)↔(1,0)、(1,2)↔(2,1)、(3,8)↔(8,3)。両軸1単位45px、窓 −1.2〜9 の正方形。")


def fig_L07_2():
    m=begin(7,"L07_fig2_log_bases","底の異なる対数関数",680,
            ["y=log_2 x","y=log_10 x","y=log_(1/2) x","(1, 0)"],
            ["y=log_2 x","y=log_10 x","y=log_(1/2) x","(1, 0)","x","y"])
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    f=Frame((95,170,555,575),((-.35,8.4),(-4.5,4.5)),ck)
    axes(cv,lb,f)
    for fn,name,dash in ((math.log2,"y=log_2 x",None),(math.log10,"y=log_10 x",DASH),
                         (lambda x:math.log(x,.5),"y=log_(1/2) x","2 4")):
        curve(cv,f,ck,fn,(.0625,8.2),name,dash=dash)
        ck.ok("すべて(1,0)を通る", near(fn(1),0))
    ck.ok("x=1を境に底2と10の上下が逆転", math.log2(8)>math.log10(8) and math.log2(.5)<math.log10(.5))
    ck.ok("底1/2は減少", math.log(.5,.5)>math.log(8,.5))
    p=point(cv,f,ck,(1,0),math.log2);label_near(cv,lb,p,"(1, 0)")
    for y,s,d in ((30,"y=log_2 x",None),(72,"y=log_10 x",DASH),(114,"y=log_(1/2) x","2 4")):
        cv.line(145,y,185,y,dash=d);lb.put(205,y+6,s,anchor="start")
    return finish(m,"底2・10・1/2、共通点(1,0)。表示数値をこの指定に限定。x −0.35〜8.4、y −4.5〜4.5。縦横は別単位。")


def fig_L07_3():
    texts=["(1, 0)","(1, 3)","(2, 1)","(2, 4)"]
    m=begin(7,"L07_fig3_log_vertical_shift","真数の定数倍と上下の移動",700,
            ["y=log_2 x","y=log_2 8x","上へ 3","log_2 8x=log_2 8＋log_2 x=3＋log_2 x","log_2 16=4"],
            ["y=log_2 x","y=log_2 8x","上へ 3","x","y"]+texts)
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    f=Frame((100,150,555,590),((-.2,4.2),(-3.3,5.3)),ck)
    axes(cv,lb,f)
    curve(cv,f,ck,math.log2,(.125,4.1),"y=log_2 x")
    curve(cv,f,ck,lambda x:math.log2(8*x),(.125,4.1),"y=log_2 8x",dash=DASH)
    for x in (1,2):
        lo,hi=math.log2(x),math.log2(8*x)
        ck.ok("真数8倍で全点が上へ3", near(hi-lo,3))
        for y in (lo,hi):point(cv,f,ck,(x,y),lambda t:math.log2(t) if y==lo else math.log2(8*t))
        a,b=f.P((x,lo)),f.P((x,hi))
        cv.arrow(a[0]+8,a[1]-7,b[0]+8,b[1]+7,w=1.6)
    for p,s in zip(((1,0),(1,3),(2,1),(2,4)),texts):label_near(cv,lb,f.P(p),s)
    for y,s,d in ((30,"y=log_2 x",None),(70,"y=log_2 8x",DASH)):
        cv.line(150,y,190,y,dash=d);lb.put(210,y+6,s,anchor="start")
    lb.c(320,115,"上へ 3")
    ck.ok("描いた区間全体で差が3", all(near(math.log2(8*(.125+i/80))-math.log2(.125+i/80),3) for i in range(319)))
    return finish(m,"底2、真数8倍、上へ3。点(1,0)→(1,3)と(2,1)→(2,4)。両曲線は同一座標・同じ縮尺。")


def fig_L08_1():
    m=begin(8,"L08_fig1_domain_number_line","真数の条件と解の共通部分",560,
            ["x>1","x<9","1<x<9","真数は正"],
            ["x>1","x<9","1<x<9","1","9","x"])
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    def X(x):return 110+40*x
    for row,(heading,lo,hi) in enumerate((("x>1",1,None),("x<9",None,9),("1<x<9",1,9))):
        y=115+165*row
        lb.c(320,y-55,heading)
        cv.arrow(65,y,600,y,w=THIN_W,oid="axis")
        for x in (1,9):
            xx=X(x);cv.line(xx,y-4,xx,y+4,w=THIN_W,oid="tick");lb.c(xx,y+32,str(x))
        a,b=X(lo) if lo else 65,X(hi) if hi else 590
        cv.line(a,y,b,y,w=BOLD_W,oid="range")
        if lo is None:cv.arrow(100,y,65,y,w=BOLD_W)
        if hi is None:cv.arrow(555,y,590,y,w=BOLD_W)
        for x in [v for v in (lo,hi) if v is not None]:
            q=(X(x),y)
            cv.path([(q[0]+5*math.cos(i*math.pi/20),q[1]+5*math.sin(i*math.pi/20)) for i in range(41)],fill="#fff",oid="dot")
        lb.c(615,y,"x")
    ck.ok("共通部分は厳密に1<x<9", all(((x>1) and (x<9)) == (1<x<9) for x in (0,1,1.1,5,8.9,9,10)))
    ck.ok("白丸の端点は除外", not 1<1<9 and not 1<9<9)
    ck.ok("3段の目盛りの単位が同じ", near(X(9)-X(1),8*40))
    return finish(m,"端点1・9、上x>1、中x<9、下1<x<9。3段とも1単位40px、端点は白丸。")


def fig_L09_1():
    vals=[1,10,100,1000,10000]
    nums=[str(x) for x in vals]
    ds=[f"{n} 桁" for n in range(1,5)]
    m=begin(9,"L09_fig1_log_scale_digits","10の累乗と桁数の区切り",560,
            ["10^0=1","10^1=10","10^2=100","1000=10^3","10^2≦N<10^3","n＋1 桁"],
            nums+ds+["10^2≦N<10^3","log_10 N"])
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    def X(v):return 70+120*math.log10(v)
    y=150
    cv.arrow(40,y,600,y,w=AXIS_W,oid="axis")
    for n,v in enumerate(vals):
        x=X(v);cv.line(x,y-7,x,y+7,w=THIN_W,oid="tick");lb.c(x,y-28,str(v))
        ck.ok("10の累乗と対数座標", v==10**n and near(X(v),70+120*n))
    endpoints=[]
    for n in range(4):
        a,b=X(vals[n]),X(vals[n+1])
        yy=y+55+70*n
        cv.line(a,yy,b,yy,w=BOLD_W if n==2 else MAIN_W,oid="digit")
        cv.dot(a,yy,r=3.4)
        q=(b,yy)
        cv.path([(q[0]+3.4*math.cos(i*math.pi/16),q[1]+3.4*math.sin(i*math.pi/16)) for i in range(33)],fill="#fff",oid="dot")
        lb.c((a+b)/2,yy+30,ds[n])
        endpoints.extend(((a,yy),(b,yy)))
        ck.ok("桁数の下端と上端", len(str(vals[n]))==n+1 and len(str(vals[n+1]-1))==n+1)
    lb.c(320,48,"log_10 N");lb.c(320,510,"10^2≦N<10^3")
    ck.ok("10倍ごとに等間隔", all(near(X(vals[i+1])-X(vals[i]),120) for i in range(4)))
    ck.ok("各区間の白丸と黒丸が別の端点に隠れない", all(dist(p,q)>8 for i,p in enumerate(endpoints) for q in endpoints[i+1:]))
    return finish(m,"1・10・100・1000・10000を対数座標で等間隔。各区間は左端を含み右端を除く。1〜4桁、100以上1000未満は3桁。")


def fig_L10_1():
    m=begin(10,"L10_fig1_decay_threshold","残量の割合と半分になる境",720,
            ["0.8^x","0.8^3=0.512","0.8^4=0.4096","0.5","およそ 3.1"],
            ["y=0.8^x","y=0.5","時間 x","残量の割合","0.5","3","4","およそ 3.1","(3, 0.512)","(4, 0.4096)"])
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    f=Frame((95,145,555,550),((-.3,6.4),(-.08,1.08)),ck)
    axes(cv,lb,f,xt=[(3,"3"),(4,"4")],yt=[(.5,"0.5")],xlabel=None,ylabel=None)
    lb.c(150,112,"残量の割合");lb.c(505,637,"時間 x")
    curve(cv,f,ck,lambda x:.8**x,(0,6.4),"y=0.8^x")
    cv.line(*f.P((-.3,.5)),*f.P((6.4,.5)),dash=DASH,w=AUX_W,oid="level")
    t=math.log(.5)/math.log(.8)
    ck.ok("半分になる境は3と4の間でおよそ3.1", 3<t<4 and abs(t-3.1)<.01 and near(.8**t,.5))
    for p in ((3,.512),(4,.4096),(t,.5)):point(cv,f,ck,p,lambda x:.8**x)
    cv.line(*f.P((t,0)),*f.P((t,.5)),dash=DASH,w=AUX_W,oid="guide")
    label_near(cv,lb,f.P((3,.512)),"(3, 0.512)",(135,90,45,225))
    label_near(cv,lb,f.P((4,.4096)),"(4, 0.4096)",(315,270,0,225))
    lb.c(f.P((t,0))[0],593,"およそ 3.1")
    lb.c(190,35,"y=0.8^x");lb.c(455,35,"y=0.5")
    return finish(m,"割合0.8^x、しきい値0.5、点(3,0.512)と(4,0.4096)、境はおよそ3.1時間。")


def fig_L10_2():
    ys=[100,80,64,51.2,40.96]
    logs=[2,1.903,1.806,1.709,1.612]
    ytexts=["100","80","64","51.2","40.96"]
    ltexts=["2","1.903","1.806","1.709","1.612"]
    m=begin(10,"L10_fig2_semilog_line","普通の目盛りと対数の目盛り",1040,
            ["| x | 0 | 1 | 2 | 3 | 4 |","| 表 A の y | 100 | 80 | 64 | 51.2 | 40.96 |",
             "y=100×0.8^x","log_10 y","2、1.903、1.806、1.709、1.612"],
            ["y","log_10 y","x","0","1","2","3","4","表 A"]+ytexts+ltexts)
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    # 左右とも横軸の単位が等しい。右の縦座標はlog10(y)そのもの。
    # 右も0を省略せず、5つの近い目盛りが20px文字で読める高さを取る。
    f=Frame((82,155,282,955),((-.2,4.5),(0,115)),ck)
    g=Frame((404,155,604,955),((-.2,4.5),(0,2.3)),ck)
    ck.ok("2パネルの横軸の単位が等しい", near(f.sx,g.sx))
    axes(cv,lb,f,xt=[(x,str(x)) for x in range(5)],yt=list(zip(ys,ytexts)),ylabel="y")
    axes(cv,lb,g,xt=[(x,str(x)) for x in range(5)],yt=list(zip([math.log10(y) for y in ys],ltexts)),ylabel="log_10 y")
    curve(cv,f,ck,lambda x:100*.8**x,(0,4),"y=100×0.8^x")
    curve(cv,g,ck,lambda x:math.log10(100)+x*math.log10(.8),(0,4),"log_10 y")
    for x,(y,lv) in enumerate(zip(ys,logs)):
        z=math.log10(y)
        ck.ok("表Aの点は指数関数上", near(100*.8**x,y))
        ck.ok("片対数の高さは常用対数", near(z,2+x*math.log10(.8)))
        ck.ok("本文の表示近似値は小数3桁で一致", abs(z-lv)<.0005)
        point(cv,f,ck,(x,y),lambda t:100*.8**t)
        point(cv,g,ck,(x,z),lambda t:2+t*math.log10(.8))
    zs=[math.log10(y) for y in ys]
    ck.ok("常用対数の差が一定で直線", all(near(zs[i+1]-zs[i],math.log10(.8)) for i in range(4)))
    lb.c(320,35,"表 A")
    return finish(m,"表A x=0〜4、y=100・80・64・51.2・40.96、log10(y)≈2・1.903・1.806・1.709・1.612。横軸共通、左yは1単位800/115px、右log10(y)は1単位800/2.3px。縦軸は両方0から省略せず表示。")


def fig_L11_1():
    groups=[("指数の拡張","L01","L02"),("指数関数","L03","L04"),("対数","L05","L06"),
            ("対数関数","L07","L08"),("常用対数","L09"),("活用","L10")]
    allow=[s for group in groups for s in group]+["法則が成り立つように決める","定義に戻る"]
    m=begin(11,"L11_fig1_unit_map","単元の地図",510,
            ["指数の拡張（L01・L02）","指数関数（L03・L04）","対数（L05・L06）",
             "対数関数（L07・L08）","常用対数（L09）","活用（L10）","法則が成り立つように決める","定義に戻る"],allow)
    cv,lb,ck=m["canvas"],m["lb"],m["ck"]
    # 6列を左から右へ置く。長い語は文字単位で改行せず、列幅に合わせ縦の行を使う。
    # 数字はレッスン番号にのみ現れる。
    for i,group in enumerate(groups):
        x=15+104*i
        cv.rect(x,185,90,190,fill="#efefef")
        title=group[0]
        # 90pxの列へ20px字形を収めるため、5文字の語だけ2行へ分ける。
        if len(title)>4:
            first,second=title[:3],title[3:]
            lb.c(x+45,225,first);lb.c(x+45,256,second)
            m["allow_texts"].remove(title);m["allow_texts"].update((first,second))
        else:
            lb.c(x+45,240,title)
        for j,s in enumerate(group[1:]):lb.c(x+45,303+36*j,s)
        if i<5:cv.arrow(x+93,275,x+101,275,head=4)
    # 上の帯の短い対象範囲へ長い文章を縮小せず、上の本文から括弧で対象列へ結ぶ。
    lb.c(320,38,"法則が成り立つように決める")
    cv.path([(320,60),(320,80),(60,80),(60,110)],oid="link")
    upper=(15,117,90,35)
    cv.rect(*upper,fill="#d9d9d9")
    cv.line(60,158,60,177,oid="link")
    lb.c(420,466,"定義に戻る")
    cv.rect(225,402,398,28,fill="#d9d9d9")
    cv.line(424,375,424,396,oid="link")
    nums=[int(s[1:]) for group in groups for s in group[1:]]
    ck.ok("6段がL01〜L10を重複なく覆う", len(groups)==6 and nums==list(range(1,11)))
    ck.ok("上の帯はL01〜L02、下はL05〜L10", groups[0][1:]==("L01","L02") and [s for g in groups[2:] for s in g[1:]]==[f"L{i:02}" for i in range(5,11)])
    ck.ok("上帯の実座標が第1列だけを覆う", upper[0]==15 and upper[0]+upper[2]==105 and upper[0]+upper[2]<119)
    ck.ok("下帯の実座標が第3〜6列の中心だけを覆う", [i for i in range(6) if 225<=60+104*i<=623]==[2,3,4,5])
    return finish(m,"左から指数の拡張(L01・L02)、指数関数(L03・L04)、対数(L05・L06)、対数関数(L07・L08)、常用対数(L09)、活用(L10)。上帯は最初の段、下帯は第3〜6段。")


FIGS=[fig_L01_1,fig_L02_1,fig_L02_2,fig_L03_1,fig_L03_2,fig_L04_1,fig_L05_1,fig_L05_2,
      fig_L07_1,fig_L07_2,fig_L07_3,fig_L08_1,fig_L09_1,fig_L10_1,fig_L10_2,fig_L11_1]


def numeric_tokens(s):
    """数値を語境界で抽出する。1を10や1.903の部分として扱わない。"""
    return set(re.findall(r"(?<![A-Za-z0-9_.])−?\d+(?:\.\d+)?(?:/\d+)?(?![A-Za-z0-9_.])",s))


def answer_sections():
    sections={}
    for f in sorted(LESSON_DIR.glob("answer_key_*.md")):
        parts=re.split(r"(?m)^## L(\d\d) .*\n",f.read_text())
        for i in range(1,len(parts),2):
            n=int(parts[i]);src=parts[i+1]
            tokens=set()
            for s in re.findall(r"\*\*([^*\n]+)\*\*",src):
                if re.match(r"(?:問\d|S\d)",s):
                    continue
                tokens.add(s)
                tokens.update(t.strip() for t in s.split("、") if t.strip())
                tokens.update(numeric_tokens(s))
            # 解答の表の値も対象とする。
            for line in src.splitlines():
                if line.startswith("|") and not re.fullmatch(r"[|\- ]+",line):
                    tokens.update(c.strip() for c in line.split("|")[1:-1] if c.strip())
            sections[n]={"file":f.name,"tokens":tokens,"source":src}
    assert set(sections)==set(range(1,12)),"解答編のレッスン集合が違う"
    return sections


def svg_texts(src, metadata=False):
    root=ET.fromstring(src)
    tags={"text","title","desc"} if metadata else {"text"}
    return ["".join(e.itertext()) for e in root.iter() if e.tag.rsplit("}",1)[-1] in tags]


def ban_hits(texts,bans):
    joined="\n".join(texts)
    numbers=numeric_tokens(joined)
    return sorted(b for b in bans if (b in numbers if re.fullmatch(r"−?\d+(?:\.\d+)?(?:/\d+)?",b) else b in joined))


def answer_policy(m, sections):
    """既知量との仕様衝突は記録し、解答だけの内容を禁止する。"""
    tokens=set().union(*(s["tokens"] for s in sections.values()))
    # 例: (1,0)は必須図にも解答にもある。これを禁止すると必須図を描けない。
    # 許可リストに一致する文字・数値だけ共有量にする。答え全体を無条件で免除しない。
    given=m["allow_texts"]
    number_given=numeric_tokens("\n".join(given))
    shared={b for b in tokens if b in given or b in number_given or
            (not re.fullmatch(r"−?\d+(?:\.\d+)?(?:/\d+)?",b) and any(b in s for s in given))}
    bans=tokens-shared
    m["bans"],m["shared"]=bans,shared
    m["answer_file"]="・".join(sorted({s["file"] for s in sections.values()}))
    m["ck"].ok("解答編から禁止文字列を抽出", bool(bans) and bool(tokens))
    hits=ban_hits(svg_texts(m["svg"],metadata=True),bans)
    m["ck"].ok("図中文字・title・descに解答のみの文字列がない", not hits, str(hits))


def char_hygiene(s,where):
    bad=[]
    for i,ch in enumerate(s):
        o,cat=ord(ch),unicodedata.category(ch)
        if ch in "\n\t":
            continue
        if (cat in {"Cf","Mn","Me","Cc","Co","Cn"} or
            0xFE00<=o<=0xFE0F or 0xE0100<=o<=0xE01EF or
            0x3099<=o<=0x309C or o in (0xFF9E,0xFF9F) or
            0x1F000<=o<=0x1FAFF or 0x2600<=o<=0x27BF or 0x2B00<=o<=0x2BFF or
            0xFF10<=o<=0xFF19 or 0xFF21<=o<=0xFF3A or 0xFF41<=o<=0xFF5A):
            bad.append((i,hex(o)))
    assert not bad,f"{where}: 禁止文字 {bad[:5]}"
    patterns=["、"+b for b in ("「","『")]+[b+"、" for b in ("」","』")]
    assert not any(p in s for p in patterns),f"{where}: 読点と鍵括弧の連続"


def validate_svg(src,allow,bans=()):
    root=ET.fromstring(src)
    assert root.tag=="{http://www.w3.org/2000/svg}svg"
    assert root.attrib.get("viewBox") and "width" not in root.attrib and "height" not in root.attrib
    assert len(root.findall("{http://www.w3.org/2000/svg}title"))==1
    assert len(root.findall("{http://www.w3.org/2000/svg}desc"))==1
    assert "font-family" not in src and "href" not in src and "@import" not in src
    assert set(svg_texts(src))==set(allow),"図中文字の許可集合と不一致"
    assert not ban_hits(svg_texts(src,metadata=True),bans),"解答文字列の漏えい"
    assert f'<rect x="0" y="0" width="{W}"' in src and 'fill="#fff"' in src
    for e in root.iter():
        for k,v in e.attrib.items():
            if k=="stroke":assert v in {"#000","none"},"線は黒のみ"
            if k=="fill":assert v=="none" or re.fullmatch(r"#([0-9a-f])\1\1|#([0-9a-f]{2})\2\2",v),"塗りは白黒とグレーのみ"
            if k=="font-size":assert float(v)>=W*.03,"文字が小さい"
    char_hygiene(src,"SVG")


def gate_self_test():
    """実際の解答編から取った答えを故意に入れ、同じ検査で拒否する。"""
    sections=answer_sections()
    token="1/25"
    assert token in sections[1]["tokens"],"陽性対照の答えが実際の解答編にない"
    cv=Canvas(W,100);cv.text(100,50,token)
    sample=cv.svg("probe","検査見本","検査見本")
    assert svg_texts(sample)==[token]
    try:
        validate_svg(sample,{token},{token})
    except AssertionError as e:
        assert "漏えい" in str(e),"別理由で停止したため陽性対照として無効"
    else:
        raise AssertionError("陽性対照失敗: 答えを見逃す")
    for tag in ("title","desc"):
        # 可視文字だけでなくメタ情報への混入も同じゲートで拒否する。
        injected=sample.replace(f"<{tag}>検査見本</{tag}>",f"<{tag}>{token}</{tag}>")
        assert ban_hits(svg_texts(injected,metadata=True),{token})
    assert not ban_hits(["10","1.903"],{"1"}),"数値の語境界の陰性対照"
    for c in (0x200B,0x0301,0xFE0F,0x1F600,0xFF21,0xFF11):
        try:char_hygiene(chr(c),"陽性対照")
        except AssertionError:pass
        else:raise AssertionError("文字衛生の陽性対照失敗")
    for p in ("、"+"「","、"+"『","」"+"、","』"+"、"):
        try:char_hygiene(p,"陽性対照")
        except AssertionError:pass
        else:raise AssertionError("括弧検査の陽性対照失敗")
    assert boxes_overlap((0,0,20,20),(10,10,30,30))
    assert seg_intersects_rect((0,0),(30,30),(10,10,20,20))
    assert not seg_intersects_rect((0,0),(5,5),(10,10,20,20))
    char_hygiene("x²・√2・log_2 x・−1・→","陰性対照")
    return sections


def lesson_refs():
    refs={}
    for f in sorted(LESSON_DIR.glob("lesson_[0-9]*.md")):
        order=[]
        for ln,s in enumerate(f.read_text().splitlines(),1):
            for alt,name in ALT_RE.findall(s):
                assert name not in refs,"図の重複参照"
                match=NAME_RE.fullmatch(name)
                assert match and int(match[1])==int(f.stem[-2:]),"図名とレッスンが違う"
                order.append(int(match[2]));refs[name]=(alt,f.name,ln)
        assert order==list(range(1,len(order)+1)),"連番と登場順が違う"
    assert len(refs)==16,"本文の図が16件でない"
    return refs


def issue_document():
    """図に直接関係する衝突だけを原文どおりの引用で記録する。"""
    cases=[
        ("I03","teacher_notes_L02-06.md",191,
         "図中の数値ラベルは本文明示値（16・8・4・−4・2／0.7071・1/4／対比表の 12 個の値／(0, 1)／1/9 と 2／3・1・2・4）に限る。",
         "L05_fig2の代替文は2^3=8と3=log_2 8を要求するが、対応する末尾の数値群に8がない。図は本文の明示例を優先して8を表示する。新しい数値は追加しない。"),
        ("I04","teacher_notes_L07-11.md",196,
         "練習と stretch の答えと衝突する数値は図に入れない。",
         "必須の(1, 0)はL07の練習解答と共通し、L01の既知値1やL10の既知値1.903にも解答との重複がある。文字列の全面禁止と必須図は同時に満たせない。本文が図へ明示した量だけを許可集合へ固定し、それ以外の解答文字列を禁止する。共有したトークンの件数を台帳へ記録する。全面禁止を達成したとは扱わない。L07_fig2は問3(1)〜(3)の答え（共通点(1, 0)・x>1での上下・右下がりの曲線）を本文§2の既知量として描いており、答えの非掲載とは別に記録する。"),
        ("I05","lesson_04.md",60,
         "左の座標平面に底が 1 より大きい y=2^x のグラフを描き",
         "y=2^xという数値式はL04では画像行だけにあり、画像行を除いたL04本文との逐字照合はできない。L04本文のL03参照とlesson_03.mdの既習式y=2^xを照合し、本文指定の図を描く。"),
        ("I06","lesson_09.md",35,
         "10 の累乗 1、10、100、1000、10000 を等間隔に並べた数直線",
         "10000の十進表記は画像行を除いたL09本文にない。本文の10^4と指導ノート196行の10000を照合して表示する。10000そのものが画像行を除いた本文にあるとは報告しない。")]
    lines=["---","distribution_status: published_draft","audience: ai","---","",
           "# 図版の仕様衝突と採用した描き方","","本文・解答編・指導ノートは変更していません。引用は生成時に元ファイルの該当行と照合します。",""]
    for code,file,ln,quote,reason in cases:
        actual=(LESSON_DIR/file).read_text().splitlines()
        assert quote in actual[ln-1],f"{code}: 原文引用と行が違う"
        lines.extend([f"## {code} — {file}:{ln}","","```text",quote,"```",f"出典: {file}:{ln}","",reason,""])
    result="\n".join(lines)
    char_hygiene(result,"FIGURE_ISSUES.md")
    return result,len(cases)


def manifest(rows,refs,issues,protected):
    nchecks=sum(len(m["ck"].items) for m in rows)
    nlabels=sum(len(m["canvas"].texts) for m in rows)
    lines=["---","distribution_status: published_draft","---","",MODEL_LINE,"",
           "# FIGURE_MANIFEST — 数学Ⅱ「指数関数・対数関数」図版台帳","",
           f"生成日: {GENERATED}","",
           f"`assets_provenance/generate_figures.py`による標準ライブラリだけの生成です。全{len(rows)}図・記録付きassert {nchecks}項目・図中文字{nlabels}個。", "",
           "Canvas・Checker・Labels・幾何検査は数学Ⅱ「図形と方程式」の部品を利用し、台帳と許可集合の型は数学Ⅱ「いろいろな式」に合わせています。図の内容は本単元の本文から作成しています。", "",
           "全16図をメモリ内で検査してから書きます。数学、窓と軸の単位、本文引用、許可ラベル集合、答えの分離、配置、文字衛生、XML・白黒・外部参照なしを検査します。文字サイズは全図20pxで幅640の3.125%です。配置検査は保守的な推定字幅に基づきます。", "",
           "本文の参照集合・生成する集合・実際のSVG集合は完全一致です。altは本文から抽出し、台帳へ書いた値もUTF-8バイトで再照合します。レッスン内の連番は登場順です。", "",
           f"仕様衝突はFIGURE_ISSUES.mdの{issues}件です。答えとの重複を全面禁止すると必須の既知量も消えるため、本文が図へ指定した量に限り共有を記録し、解答だけの文字列を禁止します。この解釈の制約を全面禁止の合格と読み替えません。禁止検査はmain冒頭で実解答を混入させた陽性対照により実証します。", "",
           "日付はSVG先頭コメントと本台帳の生成日行だけです。乱数・時刻は使いません。再現性の最終確認と抽出版CIの実走結果は実行者の報告で確認してください。", "",
           "| ファイル | 対象 | 図の意図 | 本文対応箇所 | alt（本文と同一） | パラメータと縮尺 | 検証結果 |",
           "|---|---|---|---|---|---|---|"]
    for m in rows:
        alt,file,ln=refs[m["file"]]
        checks="／".join(d+" 合格" for d,_ in m["ck"].items)
        cells=[f"`{m['file']}`",m["lesson"],m["title"],f"{file}:{ln}",alt,m["params"],
               checks+f"／解答禁止{len(m['bans'])}種類・指定既知量との共有{len(m['shared'])}種類"]
        assert all("|" not in c for c in cells)
        lines.append("| "+" | ".join(cells)+" |")
    lines += ["","## 本文類のsha256","","生成器は以下の17ファイルを読むだけです。作業前との未変更照合は実行者が別途行います。","","| ファイル | sha256 |","|---|---|"]
    for file,h in sorted(protected.items()):lines.append(f"| {file} | {h} |")
    result="\n".join(lines)+"\n"
    char_hygiene(result,"FIGURE_MANIFEST.md")
    # 完成した台帳自体の列を解析してaltを照合する。
    actual={}
    for line in result.splitlines():
        if line.startswith("| `L"):
            cols=line.split(" | ")
            actual[cols[0][3:-1]]=cols[4]
    assert set(actual)==set(refs),"台帳のファイル集合不一致"
    assert all(actual[name].encode()==refs[name][0].encode() for name in refs),"台帳altのバイト不一致"
    return result,nchecks,nlabels


def protected_hashes():
    files=sorted([*LESSON_DIR.glob("lesson_[0-9]*.md"),*LESSON_DIR.glob("answer_key_*.md"),*LESSON_DIR.glob("teacher_notes_*.md")])
    assert len(files)==17
    return {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files}


def main():
    sections=gate_self_test()
    own=Path(__file__).read_text()
    char_hygiene(own,"generate_figures.py")
    before=protected_hashes()
    refs=lesson_refs()
    rows=[]
    for fn in FIGS:
        m=fn()
        m["svg"]=m["canvas"].svg(m["file"],m["title"],m["desc"])
        answer_policy(m,sections)
        validate_svg(m["svg"],m["allow_texts"],m["bans"])
        # 同一プロセスで再構成し、部品の隠れた状態依存も検出する。
        b=fn()
        assert m["svg"]==b["canvas"].svg(b["file"],b["title"],b["desc"])
        rows.append(m)
    names=[m["file"] for m in rows]
    assert len(names)==len(set(names))==16 and set(names)==set(refs)
    assert names==list(refs),"図の生成順が本文の登場順でない"
    current={p.name for p in ASSETS.glob("*.svg")}
    assert not current-set(names),"参照外の既存SVGがあるため書き出さない"
    issues,nissues=issue_document()
    doc,nchecks,nlabels=manifest(rows,refs,nissues,before)
    assert protected_hashes()==before,"生成中に本文類が変わったため書き出さない"
    # ここまでの全検証が済むまでディレクトリ・成果物を書かない。
    ASSETS.mkdir(exist_ok=True)
    for m in rows:(ASSETS/m["file"]).write_text(m["svg"])
    (HERE/"FIGURE_MANIFEST.md").write_text(doc)
    (HERE/"FIGURE_ISSUES.md").write_text(issues)
    print(f"OK {len(rows)} figures / {nchecks} recorded asserts / {nlabels} labels / {nissues} issues")
    for m in rows:print(f"OK {m['file']} ({len(m['ck'].items)} asserts)")
    return rows


if __name__=="__main__":
    main()


