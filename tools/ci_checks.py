# SPDX-License-Identifier: MIT
"""ci_checks.py — 品質検査の一括実行（CI用・標準ライブラリのみ）

実行: リポジトリのどこからでも `python3 tools/ci_checks.py`
終了コード: 0=全チェック通過 / 1=いずれか失敗

チェック内容:
  1. リンク照合 — 全 .md / .html のローカル参照（リンク・画像）の実在確認
     （コードフェンス・インラインコード内は対象外）
  2. アンカー照合 — 全 .md のfragmentリンク（#見出し）を、GitHubのslug規則
     （小文字化・空白→ハイフン・記号除去・重複見出しは-1,-2…）で全数照合
  3. frontmatter検査 — materials/ 配下の全 .md に distribution_status があること
  4. ビュー生成器テスト — tools/view_generator/test_view_generator.py を実行
  5. 図版再生成検算 — 各単元の assets_provenance/generate_figures.py を
     一時ディレクトリのコピーで実行し（出荷SVGは書き換えない）、
     ①スクリプト内の全assert（幾何検算・答え漏れ検査）の通過
     ②再生成SVGと出荷SVGの一致（生成日コメントのみ正規化して比較）を確認
  6. 進捗一覧バイト一致 — curriculum/PROGRESS_INDEX.md がレジストリからの
     再生成結果とバイト一致することを確認（レジストリ更新後の再生成漏れ検出）
  7. 強調崩れ検査 — 全 .md をレンダリングし、コード（`<code>`）外に literal `**`
     が露出するファイルを検出する。二段構成:
       - markdown-it-py（CommonMark）が導入済みなら、それでレンダリングして
         `<code>` 外の literal `**` を厳密検出する（未閉鎖・区切り内空白・
         CJK約物隣接などあらゆる崩れを捕捉）。
       - 未導入の環境（本番CI等）では標準ライブラリだけで動く近似検出に切り替える:
         CJK約物の直後に置かれ閉じ側に来る `**`（例: `…重要。**次` のように
         約物のあとで閉じられず literal 化するパターン）を正規表現で検出する。
     どちらの経路でも、現状の materials は 0 件で pass する。
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FENCE_RE = re.compile(r"^(```|~~~).*?^\1\s*$", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_REF_RE = re.compile(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# サブプロセスがリポジトリ内に __pycache__ を残さないようにする
SUBPROC_ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def is_local(target: str) -> bool:
    t = target.strip()
    if not t or t.startswith("#"):
        return False
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", t):  # http:, https:, mailto:, data: など
        return False
    if t.startswith("//"):
        return False
    return True


def iter_repo_files(suffixes: tuple[str, ...]):
    for p in sorted(REPO.rglob("*")):
        if ".git" in p.parts:
            continue
        if p.is_file() and p.suffix in suffixes:
            yield p


def check_links() -> list[str]:
    problems: list[str] = []
    for path in iter_repo_files((".md", ".html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        targets: list[str] = []
        if path.suffix == ".md":
            stripped = INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))
            targets = [m.group(1) for m in MD_LINK_RE.finditer(stripped)]
        else:
            targets = [m.group(1) for m in HTML_REF_RE.finditer(text)]
        for raw in targets:
            if not is_local(raw):
                continue
            rel = raw.split("#", 1)[0]
            if not rel:
                continue
            try:
                rel = re.sub(r"%20", " ", rel)
                resolved = (path.parent / rel).resolve()
            except OSError:
                problems.append(f"{path.relative_to(REPO)}: 解決不能な参照 {raw}")
                continue
            # リポジトリ外への相対参照（GitHub UI 用の ../../issues 等）は実在検査の対象外
            if not resolved.is_relative_to(REPO):
                continue
            if not resolved.exists():
                problems.append(f"{path.relative_to(REPO)}: 参照先が存在しない → {raw}")
    return problems


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
MD_FORMAT_RE = re.compile(r"(\*\*|\*|__|`|~~)")
MD_INLINE_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def github_slug(heading: str, seen: dict[str, int]) -> str:
    """GitHubのMarkdown見出しslug規則を再現する。

    レンダリング後テキストを小文字化し、英数字（Unicode含む）・
    ハイフン・アンダースコア・空白以外を除去、空白をハイフンへ。
    同名見出しの2回目以降は -1, -2, … を付ける。
    """
    text = MD_INLINE_LINK_RE.sub(r"\1", heading)   # [text](url) → text
    text = HTML_TAG_RE.sub("", text)               # HTMLタグ除去
    text = MD_FORMAT_RE.sub("", text)              # 強調・コード記号除去
    text = text.lower()
    text = "".join(ch for ch in text if ch.isalnum() or ch in ("-", "_", " "))
    slug = text.replace(" ", "-")
    n = seen.get(slug, 0)
    seen[slug] = n + 1
    return slug if n == 0 else f"{slug}-{n}"


def md_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    stripped = FENCE_RE.sub("", text)
    seen: dict[str, int] = {}
    anchors = set()
    for m in HEADING_RE.finditer(stripped):
        anchors.add(github_slug(m.group(2), seen))
    # 明示アンカー（<a id="..."> / <a name="...">）も有効
    for m in re.finditer(r"<a\s+(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", text, re.IGNORECASE):
        anchors.add(m.group(1))
    return anchors


def check_anchors() -> list[str]:
    from urllib.parse import unquote

    problems: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}

    def anchors_of(p: Path) -> set[str]:
        if p not in anchor_cache:
            anchor_cache[p] = md_anchors(p)
        return anchor_cache[p]

    for path in iter_repo_files((".md",)):
        text = path.read_text(encoding="utf-8", errors="replace")
        stripped = INLINE_CODE_RE.sub("", FENCE_RE.sub("", text))
        for m in MD_LINK_RE.finditer(stripped):
            raw = m.group(1)
            if "#" not in raw:
                continue
            rel, frag = raw.split("#", 1)
            frag = unquote(frag.strip())
            if not frag:
                continue
            if rel:
                if not is_local(rel):
                    continue
                try:
                    target = (path.parent / re.sub(r"%20", " ", rel)).resolve()
                except OSError:
                    continue
                if not target.is_relative_to(REPO) or target.suffix != ".md" or not target.exists():
                    continue  # 実在はリンク照合側で検査済み・md以外は対象外
            else:
                target = path
            if frag not in anchors_of(target):
                problems.append(f"{path.relative_to(REPO)}: アンカー欠落 → {raw}")
    return problems


def parse_frontmatter(text: str) -> tuple[str | None, str | None]:
    """frontmatter本文と問題文を返す。(fm, None)=正常 / (None, None)=frontmatterなし / (None, 問題文)=不正。

    終端は「行全体が --- 」との**文字どおりの完全一致**で判定する（R10/R11対応:
    `---oops` のような偽終端も、`--- `・`---<TAB>` のような末尾空白つきも受理しない。
    許容するのは `---` と、CRLFファイルの `---\r` のみ）。
    """
    def _is_delim(line: str) -> bool:
        return line == "---" or line == "---\r"
    lines = text.split("\n")
    if not lines or not _is_delim(lines[0]):
        return None, None
    for i in range(1, len(lines)):
        if _is_delim(lines[i]):
            return "\n".join(lines[1:i]), None
    return None, "frontmatter が正規の終端行（--- 単独行・末尾空白なし）で閉じていない"


def _selftest_parse_frontmatter() -> None:
    # 偽終端・未閉鎖を検出できることを実行のたびに確認する（R10反例の回帰試験）
    ok, err = parse_frontmatter("---\na: 1\n---\n本文")
    assert ok == "a: 1" and err is None
    ok, err = parse_frontmatter("---\na: 1\n---oops\n本文")
    assert ok is None and err is not None, "偽終端 ---oops を受理してはならない"
    ok, err = parse_frontmatter("---\na: 1\n本文")
    assert ok is None and err is not None, "未閉鎖frontmatterを受理してはならない"
    ok, err = parse_frontmatter("---\na: 1\n--- \n本文")
    assert ok is None and err is not None, "末尾1空白つき終端 '--- ' を受理してはならない"
    ok, err = parse_frontmatter("---\na: 1\n---   \n本文")
    assert ok is None and err is not None, "末尾空白つき終端 '---   ' を受理してはならない"
    ok, err = parse_frontmatter("---\na: 1\n---\t\n本文")
    assert ok is None and err is not None, "末尾タブつき終端を受理してはならない"
    ok, err = parse_frontmatter("---\r\na: 1\r\n---\r\n本文")
    assert ok == "a: 1\r" and err is None, "CRLFの正規終端は受理する"
    ok, err = parse_frontmatter("本文だけ")
    assert ok is None and err is None


def check_frontmatter() -> list[str]:
    problems: list[str] = []
    _selftest_parse_frontmatter()
    # 正規YAMLパース（R9対応: GitHubが赤エラーを出す構文不正を検出する）。
    # PyYAML未導入は検査不能として失敗にする（R10対応: fail-openにしない）。
    try:
        import yaml  # type: ignore
    except ImportError:
        return ["PyYAML未導入のためfrontmatterのYAML構文検査を実行できない（python3 -m pip install PyYAML==6.0.2 で導入すること）"]
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "*.md"], capture_output=True, cwd=REPO
    ).stdout.decode()
    for rel in sorted(f for f in tracked.split("\0") if f):
        path = REPO / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, err = parse_frontmatter(text)
        if err is not None:
            problems.append(f"{rel}: {err}")
            continue
        if fm is None:
            if rel.startswith("materials/"):
                problems.append(f"{rel}: frontmatter がない")
            continue
        if rel.startswith("materials/") and not re.search(r"^distribution_status:\s*\S+", fm, re.MULTILINE):
            problems.append(f"{rel}: frontmatter に distribution_status がない")
        try:
            yaml.safe_load(fm)
        except Exception as e:
            problems.append(f"{rel}: frontmatter がYAMLとして不正（GitHubで赤エラー表示になる）: {str(e).splitlines()[0]}")
    return problems


def check_view_generator() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(REPO / "tools" / "view_generator"), "-p", "test_*.py"],
        capture_output=True,
        text=True,
        env=SUBPROC_ENV,
    )
    if proc.returncode != 0:
        return ["view_generator テスト失敗:\n" + proc.stdout + proc.stderr]
    return []


def normalize_svg(text: str) -> str:
    return DATE_RE.sub("DATE", text)


def check_figures() -> list[str]:
    problems: list[str] = []
    scripts = sorted(REPO.glob("materials/*/*/assets_provenance/generate_figures.py"))
    if not scripts:
        return ["generate_figures.py が1本も見つからない（配置変更の可能性）"]
    for script in scripts:
        unit_dir = script.parent.parent  # materials/<subject>/<unit>
        shipped_assets = unit_dir / "assets"
        with tempfile.TemporaryDirectory(prefix="figcheck_") as tmp:
            # 単元ディレクトリごとコピー（スクリプトがlesson本文を照合検査で読むため）。
            # 出荷SVGは書き換えない（作業はすべて一時コピー側で行う）。
            work_unit = Path(tmp) / unit_dir.name
            shutil.copytree(unit_dir, work_unit)
            work_prov = work_unit / "assets_provenance"
            work_assets = work_unit / "assets"
            work_assets.mkdir(exist_ok=True)
            # 再生成の独立性を担保するため、コピー先の既存SVGは消してから実行する
            for old_svg in work_assets.glob("*.svg"):
                old_svg.unlink()
            proc = subprocess.run(
                [sys.executable, "generate_figures.py"],
                cwd=work_prov,
                capture_output=True,
                text=True,
                env=SUBPROC_ENV,
            )
            rel = script.relative_to(REPO)
            if proc.returncode != 0:
                problems.append(f"{rel}: 再生成失敗（assert等）:\n{proc.stdout[-1500:]}{proc.stderr[-1500:]}")
                continue
            gen = {p.name: p for p in work_assets.glob("*.svg")}
            shipped = {p.name: p for p in shipped_assets.glob("*.svg")}
            if set(gen) != set(shipped):
                only_gen = sorted(set(gen) - set(shipped))
                only_ship = sorted(set(shipped) - set(gen))
                problems.append(f"{rel}: SVGファイル集合が不一致 生成のみ={only_gen} 出荷のみ={only_ship}")
                continue
            for name in sorted(gen):
                a = normalize_svg(gen[name].read_text(encoding="utf-8"))
                b = normalize_svg(shipped[name].read_text(encoding="utf-8"))
                if a != b:
                    problems.append(f"{rel}: {name} が出荷SVGと不一致（生成日以外の差分あり）")
            # 図版台帳（FIGURE_MANIFEST.md等）も同じスクリプトの生成物なので照合する（R9対応）
            for mf in sorted(script.parent.glob("FIGURE_MANIFEST*.md")):
                regen = work_prov / mf.name
                if not regen.exists():
                    problems.append(f"{rel}: 再生成側に {mf.name} が生成されなかった")
                    continue
                a = normalize_svg(regen.read_text(encoding="utf-8"))
                b = normalize_svg(mf.read_text(encoding="utf-8"))
                if a != b:
                    problems.append(f"{rel}: {mf.name} が出荷版と不一致（生成日以外の差分あり）")
    return problems


def check_progress_index() -> list[str]:
    # 進捗一覧はレジストリから決定的に生成される（R9対応で生成日を廃止）。
    # 再生成結果が同梱ファイルとバイト一致することを検査する。
    shipped = (REPO / "curriculum" / "PROGRESS_INDEX.md").read_bytes()
    with tempfile.TemporaryDirectory(prefix="pidx_") as tmp:
        out = Path(tmp) / "PROGRESS_INDEX.md"
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "progress_index" / "build_progress_index.py"), str(REPO), "--out", str(out)],
            capture_output=True, text=True, env=SUBPROC_ENV,
        )
        if proc.returncode != 0 or not out.exists():
            return ["進捗一覧の再生成に失敗:\n" + proc.stdout[-800:] + proc.stderr[-800:]]
        if out.read_bytes() != shipped:
            return ["curriculum/PROGRESS_INDEX.md が再生成結果とバイト不一致（レジストリ更新後の再生成漏れ）"]
    return []


# ---- 7. 強調崩れ検査（Markdown強調記号の露出）----------------------------

_STRONG_HTML_CODE_RE = re.compile(r"<code[^>]*>.*?</code>", re.DOTALL)

# CJK約物（句読点・かぎ括弧・中点など）。閉じ側 `**` がこの直後に来ると
# CommonMark の flanking 規則で閉じられず literal 化しやすい。
_CJK_PUNCT = set("、。，．・：；！？「」『』（）〔〕【】〈〉《》〜～…—―‐’”＂｡｢｣､")
# かな・カナのブロックに同居する「文字ではない」記号（誤検出を避けるため除外する）。
_KANA_NONLETTER = set("・゠〜ー…‥　･")


def _is_cjk_letter(ch: str | None) -> bool:
    """かな・漢字・全角カナなど『語を構成する文字』なら真（約物・記号は偽）。"""
    if ch is None or ch in _KANA_NONLETTER or ch in _CJK_PUNCT:
        return False
    o = ord(ch)
    return (
        0x3041 <= o <= 0x30FA          # ひらがな＋カタカナ（記号域は上で除外済み）
        or 0x3400 <= o <= 0x9FFF       # CJK統合漢字（拡張A含む）
        or 0xFF66 <= o <= 0xFF9D       # 半角カナ
        or ch in "々〆〤ヶ〇"
    )


def _approx_emphasis_problems(text: str) -> list[str]:
    """標準ライブラリだけで動く近似検出（markdown-it-py 不在時のフォールバック）。

    コード（フェンス・インライン）を除いたうえで、各行の `**` を出現順に数え、
    『閉じ側（偶数番目）で、直前が CJK約物・直後が CJK文字』の `**` を崩れ候補とする。
    これは `…重要。**次` のように約物のあとで閉じられず literal 化するパターンで、
    現状の materials では 0 件（誤検出なし）。
    """
    stripped = INLINE_CODE_RE.sub(
        lambda m: " " * len(m.group()), FENCE_RE.sub(lambda m: " " * len(m.group()), text)
    )
    problems: list[str] = []
    for line in stripped.split("\n"):
        for k, m in enumerate(re.finditer(r"\*\*", line), 1):
            i, j = m.start(), m.end()
            prev = line[i - 1] if i > 0 else None
            nxt = line[j] if j < len(line) else None
            if k % 2 == 0 and prev in _CJK_PUNCT and _is_cjk_letter(nxt):
                problems.append(line[max(0, i - 10):j + 8].strip())
    return problems


def _selftest_approx_emphasis() -> None:
    # 崩れ例を検出し、健全例を誤検出しないことを毎回確認する（回帰試験）。
    assert _approx_emphasis_problems("文中の**重要。**次へ"), "約物直後の閉じ ** を検出できていない"
    assert _approx_emphasis_problems("**「引用」**の形"), "かぎ括弧直後の閉じ ** を検出できていない"
    assert not _approx_emphasis_problems("これは**大事**。次へ"), "正常な強調を誤検出している"
    assert not _approx_emphasis_problems("正しい**強調**です"), "正常な強調を誤検出している"
    assert not _approx_emphasis_problems("`**x。**y`"), "インラインコード内を誤検出している"


def check_emphasis_exposure() -> list[str]:
    _selftest_approx_emphasis()
    problems: list[str] = []
    try:
        from markdown_it import MarkdownIt  # type: ignore
        md = MarkdownIt("commonmark")
    except ImportError:
        md = None  # 近似検出へフォールバック（標準ライブラリのみ）

    for path in iter_repo_files((".md",)):
        rel = path.relative_to(REPO)
        text = path.read_text(encoding="utf-8", errors="replace")
        if md is not None:
            # 厳密検査: レンダリング後、<code> 外に literal ** が残れば崩れ。
            html = md.render(text)
            outside_code = _STRONG_HTML_CODE_RE.sub("", html)
            if "**" in outside_code:
                problems.append(f"{rel}: 強調記号 ** がレンダリング後もコード外に露出（強調が閉じていない）")
        else:
            for ctx in _approx_emphasis_problems(text):
                problems.append(f"{rel}: 約物直後の閉じ ** が崩れの疑い → …{ctx}…")
    return problems


def main() -> int:
    failed = False
    for label, fn in (
        ("1/7 リンク照合", check_links),
        ("2/7 アンカー照合", check_anchors),
        ("3/7 frontmatter検査", check_frontmatter),
        ("4/7 ビュー生成器テスト", check_view_generator),
        ("5/7 図版再生成検算", check_figures),
        ("6/7 進捗一覧バイト一致", check_progress_index),
        ("7/7 強調崩れ検査", check_emphasis_exposure),
    ):
        problems = fn()
        if problems:
            failed = True
            print(f"[FAIL] {label}: {len(problems)}件")
            for p in problems:
                print("  -", p)
        else:
            print(f"[PASS] {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
