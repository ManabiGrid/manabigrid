# SPDX-License-Identifier: MIT
"""gen_nav.py — 単元パッケージの目次READMEとレッスン間ナビの機械生成（べき等）

実行: リポジトリのどこからでも `python3 tools/gen_nav.py`
標準ライブラリのみ。何度実行しても結果は同じ（べき等）。

生成物:
  1. materials/<教科>/<単元>/README.md — 単元の目次
     （単元名・このパッケージの読み方・レッスン一覧・解答一覧・その他の資料）。
     マーカーコメント付きの自動生成ファイルとして全文を書き直す。
  2. 各 lesson_NN.md の末尾 — 区切り線＋ナビ行
     「← 前のレッスン｜単元の目次｜解答｜次のレッスン →」
     （存在するファイルだけをリンクする。解答の対応は本文の「対応解答:」行
     →なければファイル名の番号範囲から機械判定→どちらも不明なら目次のみ）。
  3. 各 answer_key*.md の末尾 — 「単元の目次に戻る」リンク。

既存のナビはマーカーコメント（gen_nav:...）で囲んであるため、再実行時は
その区間だけを置き換える（frontmatterや本文には触れない）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MATERIALS = REPO / "materials"

NAV_START = "<!-- gen_nav:nav:start（自動生成・手編集しない） -->"
NAV_END = "<!-- gen_nav:nav:end -->"
README_MARK = "<!-- gen_nav:readme（このファイルは tools/gen_nav.py による自動生成。手編集せず、スクリプトを直して再実行する） -->"

# 単元の表示名（unit_id → 見出し）
UNIT_NAMES = {
    "hs-math-i-quadratic-functions": "高校数学Ⅰ「二次関数」",
    "jhs-eng-1-introducing-yourself-and-others": "中1英語「自己紹介・他者紹介」",
    "jhs-jpn-all-kanji-goi-unyou": "中学国語「漢字と語彙の運用」（全学年横断）",
    "jhs-math-1-positive-negative-numbers": "中1数学「正負の数」",
    "jhs-math-1-letters-and-expressions": "中1数学「文字と式」",
    "jhs-math-1-linear-equations": "中1数学「一次方程式」",
    "jhs-math-1-proportion-inverse-proportion": "中1数学「比例と反比例」",
    "jhs-math-1-plane-figures": "中1数学「平面図形」",
    "jhs-math-1-solid-figures": "中1数学「空間図形」",
    "jhs-math-1-data-distribution": "中1数学「データの活用（度数分布・ヒストグラム）」",
    "jhs-math-1-empirical-probability": "中1数学「不確定な事象の起こりやすさ（頻度確率）」",
    "jhs-math-2-expression-calculation": "中2数学「式の計算」",
    "jhs-math-2-simultaneous-equations": "中2数学「連立方程式」",
    "jhs-math-2-linear-function": "中2数学「一次関数」",
    "jhs-math-2-congruence-and-proof": "中2数学「図形の合同と証明」",
    "jhs-math-2-quartiles-boxplot": "中2数学「四分位範囲と箱ひげ図」",
    "jhs-math-2-probability": "中2数学「確率」",
    "jhs-math-3-appendix": "中3数学 巻末資料",
    "jhs-math-3-diagnostic": "中3数学 診断テスト（試行版）",
    "jhs-math-3-expansion-factorization": "中3数学「式の展開と因数分解」",
    "jhs-math-3-function-y-ax2": "中3数学「関数y=ax²」",
    "jhs-math-3-inscribed-angle": "中3数学「円周角の定理」",
    "jhs-math-3-pythagorean-theorem": "中3数学「三平方の定理」",
    "jhs-math-3-quadratic-equations": "中3数学「二次方程式」",
    "jhs-math-3-sampling-survey": "中3数学「標本調査」",
    "jhs-math-3-similar-figures": "中3数学「相似な図形」",
    "jhs-math-3-square-roots": "中3数学「平方根」",
    "jhs-sci-2-humidity-calculation": "中2理科「湿度と飽和水蒸気量の計算」",
    "jhs-soc-civics-market-price": "中3公民「市場経済と価格のはたらき」",
}

LESSON_RE = re.compile(r"^lesson_(\d{2})\.md$")
ANSWER_RANGE_RE = re.compile(r"^answer_key_L(\d+)(?:-(\d+))?\.md$")
ANSWER_FROM_RE = re.compile(r"^answer_key_L(\d+)以降\.md$")
TAIL_ANSWER_RE = re.compile(r"^対応解答:\s*(answer_key\S+?\.md)\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
# 解答キー本文の見出しからの収録レッスン判定（answer_key_supplement.md など、
# ファイル名に範囲を持たない解答キー向け）。対応する見出しの例:
#   「## L01」「## L1」「## Lesson 1」「## Lesson 01 同訓異字」「## lesson_01」「## レッスン1」
ANSWER_HEADING_RE = re.compile(
    r"^#{2,3}\s*(?:L|Lesson[ _]?|lesson[ _]?|レッスン)\s*0?(\d{1,2})(?:\s|$)", re.MULTILINE
)


def h1_of(path: Path) -> str:
    m = H1_RE.search(path.read_text(encoding="utf-8"))
    return m.group(1) if m else path.name


def covered_lessons(answer_text: str) -> set[int]:
    """解答キー本文の見出しから、収録しているレッスン番号の集合を返す。"""
    return {int(m.group(1)) for m in ANSWER_HEADING_RE.finditer(answer_text)}


def answer_for(pkg: Path, lesson_no: int, lesson_text: str, answer_keys: list[str]) -> str | None:
    """レッスンに対応する解答ファイル名を機械判定する（不明なら None）。"""
    m = TAIL_ANSWER_RE.findall(lesson_text)
    if m and m[-1] in answer_keys:
        return m[-1]
    for name in answer_keys:
        r = ANSWER_RANGE_RE.match(name)
        if r:
            lo = int(r.group(1))
            hi = int(r.group(2)) if r.group(2) else lo
            if lo <= lesson_no <= hi:
                return name
        f = ANSWER_FROM_RE.match(name)
        if f and lesson_no >= int(f.group(1)):
            return name
    # 本文が参照する解答ファイルがちょうど1種類ならそれを採用
    mentioned = sorted({m for m in re.findall(r"answer_key\S+?\.md", lesson_text) if m in answer_keys})
    if len(mentioned) == 1:
        return mentioned[0]
    # 最終フォールバック: ファイル名に範囲を持たない解答キー（supplement等）の
    # 本文見出しから収録レッスンを解釈し、該当がちょうど1ファイルならそれを採用
    candidates = []
    for name in answer_keys:
        if ANSWER_RANGE_RE.match(name) or ANSWER_FROM_RE.match(name):
            continue
        if lesson_no in covered_lessons((pkg / name).read_text(encoding="utf-8")):
            candidates.append(name)
    if len(candidates) == 1:
        return candidates[0]
    return None


def replace_block(text: str, block: str) -> str:
    """マーカー区間があれば置換、なければ末尾に追記する（べき等）。"""
    if NAV_START in text:
        pattern = re.compile(re.escape(NAV_START) + r".*?" + re.escape(NAV_END), re.DOTALL)
        return pattern.sub(block, text)
    if not text.endswith("\n"):
        text += "\n"
    return text + "\n" + block + "\n"


def build_readme(pkg: Path, lessons: list[str], answer_keys: list[str], others: list[str]) -> str:
    unit = pkg.name
    title = UNIT_NAMES.get(unit, unit)
    lines = [
        "---",
        "distribution_status: published_draft",
        "---",
        "",
        README_MARK,
        "",
        f"# {title} — 単元の目次",
        "",
        "## このパッケージの読み方",
        "",
    ]
    if lessons:
        lines += [
            "- `lesson_01.md` から順に読む。途中の問題は紙に書いて解く（頭の中だけで済ませない）。",
            "- 解答は別ファイル（下の「解答」一覧）。自分で解いてから見る。",
        ]
    else:
        lines += [
            "- 下の一覧から読みたいファイルを開く。",
        ]
    lines += [
        "- 本文中の `:::guide`（ガイド）・`:::stretch`（発展）・`:::zatsudan`（雑談）や `:::` だけの行は区切り記号（ガイド/発展/雑談の目印）。そのまま読み進めてよい。",
        "",
    ]
    if lessons:
        lines += ["## レッスン一覧", ""]
        for name in lessons:
            lines.append(f"1. [{h1_of(pkg / name)}]({name})")
        lines.append("")
    if answer_keys:
        lines += ["## 解答", ""]
        for name in answer_keys:
            lines.append(f"- [{name}]({name})")
        lines.append("")
    if others:
        lines += ["## その他の資料", ""]
        for name in others:
            lines.append(f"- [{name}]({name})")
        lines.append("")
    return "\n".join(lines)


def process_package(pkg: Path) -> list[str]:
    changed: list[str] = []
    mds = sorted(p.name for p in pkg.glob("*.md") if p.name != "README.md")
    htmls = sorted(p.name for p in pkg.glob("*.html"))
    lessons = sorted(n for n in mds if LESSON_RE.match(n))
    answer_keys = sorted(n for n in mds if n.startswith("answer_key"))
    others = [n for n in mds if n not in lessons and n not in answer_keys] + htmls

    # 1. README.md（全文自動生成）
    readme = pkg / "README.md"
    new = build_readme(pkg, lessons, answer_keys, others)
    if not readme.exists() or readme.read_text(encoding="utf-8") != new:
        readme.write_text(new, encoding="utf-8")
        changed.append(str(readme.relative_to(REPO)))

    # 2. lesson ナビ
    for i, name in enumerate(lessons):
        path = pkg / name
        text = path.read_text(encoding="utf-8")
        no = int(LESSON_RE.match(name).group(1))
        parts = []
        if i > 0:
            parts.append(f"[← 前のレッスン]({lessons[i - 1]})")
        parts.append("[単元の目次](README.md)")
        ans = answer_for(pkg, no, text, answer_keys)
        if ans:
            parts.append(f"[解答]({ans})")
        if i + 1 < len(lessons):
            parts.append(f"[次のレッスン →]({lessons[i + 1]})")
        block = f"{NAV_START}\n\n---\n\n{'｜'.join(parts)}\n\n{NAV_END}"
        new_text = replace_block(text, block)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(path.relative_to(REPO)))

    # 3. answer_key の戻りリンク
    for name in answer_keys:
        path = pkg / name
        text = path.read_text(encoding="utf-8")
        block = f"{NAV_START}\n\n---\n\n[単元の目次に戻る](README.md)\n\n{NAV_END}"
        new_text = replace_block(text, block)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed.append(str(path.relative_to(REPO)))
    return changed


def main() -> int:
    packages = sorted(
        d for d in MATERIALS.glob("*/*") if d.is_dir() and any(d.glob("*.md"))
    )
    if not packages:
        print("パッケージが見つからない（materials/ の配置変更の可能性）", file=sys.stderr)
        return 1
    total_changed = []
    for pkg in packages:
        total_changed += process_package(pkg)
    print(f"packages: {len(packages)} / 更新ファイル: {len(total_changed)}")
    for f in total_changed:
        print("  -", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
