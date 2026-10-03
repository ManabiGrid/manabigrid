#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
generate_trig_table.py — 高1数学I「図形と計量（三角比）」三角比の表（trig_table.md）生成スクリプト

- 実行（既定・標準出力）: python3 generate_trig_table.py
    trig_table.md の「表」部分（見出し行 `| 角 | sin | cos | tan |`・区切り行・0°〜90° の 91 行）と
    同じ文字列を標準出力へ書く。ファイルは変更しない。
    照合の例: python3 generate_trig_table.py | diff - <(sed -n '/^| 角 |/,$p' ../trig_table.md)
- 実行（書き出し）: python3 generate_trig_table.py --write
    ../trig_table.md（この階層の1つ上）を、固定の前書き＋表で上書きする。
- 実行（照合）: python3 generate_trig_table.py --check
    既存の ../trig_table.md と、いま生成した内容（前書き＋表）を比較し、一致なら終了コード 0、
    不一致なら 1（差分の先頭行を標準エラーへ出す）。
- 依存: Python標準ライブラリのみ（math / pathlib / sys）。乱数・時刻を使わない決定的生成。
- 内容: 0°〜90°を1°刻みで sin・cos・tan を小数第4位まで（tan 90° は「—」）。
  値は math.sin / math.cos / math.tan（引数は math.radians で度→ラジアン変換）を
  書式 '.4f' で丸めたもの（-0.0000 は出ない範囲だが、念のため正規化する）。
- 自己検査: 生成した91行について sin²＋cos²=1（丸め前の値）・sin(θ)=cos(90°−θ)・
  tan=sin/cos（θ≠90°）を assert し、1つでも失敗すれば例外で停止して表を出力しない。
  さらに本文が引く代表値（35°・45°・30°・90° の行）を文字列で固定検査する。
- 改修方法（第三者向け）: 刻み幅・桁数を変える場合は STEP / DIGITS を変えて再実行する。
  本文（lesson_01.md §5）は「1°刻み・小数第4位」を前提にしているので、変えるときは本文も直す。
"""

import math
import sys
from pathlib import Path

STEP = 1
DIGITS = 4
OUT = Path(__file__).resolve().parent.parent / "trig_table.md"

PREAMBLE = """---
distribution_status: published_draft
---

# 三角比の表（0°〜90°・1°刻み）

- unit_id: hs-math-i-trigonometric-ratios
- 位置づけ: L01〜L12 で使う三角比の表。0°から90°まで1°刻みで sin・cos・tan の値を小数第4位まで示す（小数第5位を四捨五入）。本表は生成スクリプト（assets_provenance/generate_trig_table.py・Python標準ライブラリのみ）で自作したものであり、教科書・他資料の表の転載ではない。
- distribution_status: published_draft
- license: CC-BY-4.0
- verify_required: 値は math モジュールで生成し sin²＋cos²=1 等の自己検査を通過しているが、監修者による桁・表記の確認必須。

---

## 表の引き方

**角から値へ**: 左の列で角を探し、その行の sin・cos・tan の列を読む。たとえば 35° の行は sin 0.5736・cos 0.8192・tan 0.7002 で、これが sin 35°・cos 35°・tan 35° の値である（小数第4位まで）。

**値から角へ（逆引き）**: 求めたい三角比の列（sin なら sin の列）を上から下へ目で追い、与えられた値に最も近い値を探す。その行の角が答えである。たとえば tan A=0.7 なら、tan の列で 0.7 に最も近いのは 35° の行の 0.7002 だから A≒35°（表は1°刻みなので、答えは「およそ何度」になる）。値が2つの行のちょうど中間に近いときは、どちらに近いかを差で確かめる。

**表の範囲の外**: 90° より大きい角（鈍角）の値は、L04・L05 で学ぶ関係を使って 90° 以下の角に直してから引く。電卓の sin・cos・tan キーを使ってもよい（角の単位を「度」にし、結果は小数第5位を四捨五入すれば本表と一致する）。

**表の中の tan 90°**: tan 90° は定められない（L04）。表では「—」と書く。

## 表

"""

TABLE_HEAD = "| 角 | sin | cos | tan |\n|---|---|---|---|\n"


def fmt(v: float) -> str:
    s = f"{v:.{DIGITS}f}"
    if s.startswith("-") and float(s) == 0.0:
        s = s[1:]
    return s


def build_rows() -> list:
    rows = []
    for deg in range(0, 90 + 1, STEP):
        rad = math.radians(deg)
        s, c = math.sin(rad), math.cos(rad)
        assert abs(s * s + c * c - 1.0) < 1e-12, deg
        assert abs(s - math.cos(math.radians(90 - deg))) < 1e-12, deg
        if deg == 90:
            t_str = "—"
        else:
            t = math.tan(rad)
            assert abs(t - s / c) < 1e-9 * max(1.0, abs(t)), deg
            t_str = fmt(t)
        rows.append(f"| {deg}° | {fmt(s)} | {fmt(c)} | {t_str} |")
    assert len(rows) == 91, len(rows)
    # 代表値の固定検査（本文が引く値）
    table = {int(r.split("|")[1].strip().rstrip("°")): r for r in rows}
    assert "| 35° | 0.5736 | 0.8192 | 0.7002 |" == table[35], table[35]
    assert "| 45° | 0.7071 | 0.7071 | 1.0000 |" == table[45], table[45]
    assert "| 30° | 0.5000 | 0.8660 | 0.5774 |" == table[30], table[30]
    assert "| 90° | 1.0000 | 0.0000 | — |" == table[90], table[90]
    return rows


def table_text() -> str:
    return TABLE_HEAD + "\n".join(build_rows()) + "\n"


def full_text() -> str:
    return PREAMBLE + table_text()


def main(argv) -> int:
    mode = argv[1] if len(argv) > 1 else "--stdout"
    if mode == "--stdout":
        sys.stdout.write(table_text())
        return 0
    if mode == "--write":
        text = full_text()
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT} ({text.count(chr(10)) - PREAMBLE.count(chr(10)) - 2} data rows)")
        return 0
    if mode == "--check":
        generated = full_text()
        existing = OUT.read_text(encoding="utf-8")
        if generated == existing:
            print(f"OK: {OUT} matches the generated text ({len(existing)} chars)")
            return 0
        gen_lines, ex_lines = generated.splitlines(), existing.splitlines()
        for i, (g, e) in enumerate(zip(gen_lines, ex_lines), 1):
            if g != e:
                print(f"MISMATCH at line {i}:\n  generated: {g}\n  existing : {e}", file=sys.stderr)
                break
        else:
            print(f"MISMATCH in length: generated {len(gen_lines)} lines, existing {len(ex_lines)} lines", file=sys.stderr)
        return 1
    print(f"usage: {argv[0]} [--stdout | --write | --check]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
