#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""gen_stats.py — 同梱教材・レジストリの実測統計の機械生成（docs/STATS.md）

実行: リポジトリのどこからでも `python3 tools/gen_stats.py`
標準ライブラリのみ。同一ツリーからは常にバイト一致の出力を生成する
（生成日時を含めない——`--check` で再生成漏れを機械検知できるようにするため）。

目的: README 等の文中に数字を直書きすると、教材の追加・レジストリの改訂の
たびに古くなる（実例: レジストリのモジュール数が 40→41 に増えても、文中の
「40」は誰も直さなかった）。数字の正本を「実ファイルとレジストリからの実測」
＝本スクリプトの出力 docs/STATS.md に置き、文中は STATS.md を参照する運用へ
寄せる。数字を直書きしている巡回先の一覧は docs/RELEASE_CHECKLIST.md が持つ。

集計対象:
  - レジストリ定義: curriculum/registry/*.md の単元数・モジュール数（教科別）。
    表の解析は tools/progress_index/build_progress_index.py を正として再利用する
    （同じ表を2つの実装で読まない）。
  - 同梱教材: materials/ の同梱パッケージ数（`.md` を含むフォルダ）・
    総ファイル数・自作SVG図版数（教科フォルダ別の内訳つき）。

使い方:
  python3 tools/gen_stats.py [リポジトリルート] [--out 出力先]
  python3 tools/gen_stats.py --check
    # 同梱の docs/STATS.md が再生成結果とバイト一致するか検査
    #（不一致・生成不能は失敗。CI からの利用を想定）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# レジストリ表の解析は build_progress_index.py を正として再利用する
sys.path.insert(0, str(Path(__file__).resolve().parent / "progress_index"))
import build_progress_index as B  # noqa: E402


class StatsError(ValueError):
    """集計対象が空集合など、統計を生成できないときに送出する。"""


def material_packages(root: Path) -> list[tuple[str, list[Path]]]:
    """materials/ 直下の教科フォルダ名 → `.md` を含む同梱パッケージの一覧。"""
    materials = root / "materials"
    if not materials.is_dir():
        raise StatsError(f"materials/ が見つからない: {materials}")
    out: list[tuple[str, list[Path]]] = []
    for subject_dir in sorted(p for p in materials.iterdir() if p.is_dir()):
        pkgs = [
            d for d in sorted(subject_dir.iterdir())
            if d.is_dir() and any(d.rglob("*.md"))
        ]
        out.append((subject_dir.name, pkgs))
    return out


def count_files(path: Path) -> int:
    return sum(1 for p in path.rglob("*") if p.is_file())


def count_svgs(pkgs: list[Path]) -> int:
    """各パッケージの assets/ 配下の .svg を数える（出荷図版の実測）。"""
    return sum(
        sum(1 for p in (pkg / "assets").rglob("*.svg")) if (pkg / "assets").is_dir() else 0
        for pkg in pkgs
    )


def build(root: Path) -> str:
    # ---- レジストリ定義（設計図の全量） ----
    registry_dir = root / "curriculum" / "registry"
    subjects: list[tuple[str, int, int]] = []
    total_units = total_modules = 0
    for stem, subject in B.SUBJECT_FILES:
        path = registry_dir / f"{stem}.md"
        if not path.is_file():
            continue
        units, modules = B.parse_registry(path, subject)
        subjects.append((subject, len(units), len(modules)))
        total_units += len(units)
        total_modules += len(modules)
    if not subjects or total_units == 0:
        # 空集合からの「全部0」を統計として出さない（走査不能と区別できないため）
        raise StatsError(f"レジストリから単元を1件も読めない: {registry_dir}")

    # ---- 同梱教材の実測（materials/） ----
    materials = root / "materials"
    per_subject = material_packages(root)
    rows: list[tuple[str, int, int, int]] = []  # (フォルダ名, パッケージ, ファイル, SVG)
    total_pkgs = 0
    for name, pkgs in per_subject:
        files = count_files(materials / name)
        svgs = count_svgs(pkgs)
        rows.append((name, len(pkgs), files, svgs))
        total_pkgs += len(pkgs)
    if total_pkgs == 0:
        raise StatsError(f"materials/ に .md を含む同梱パッケージが1件もない: {materials}")
    direct_files = sum(1 for p in materials.iterdir() if p.is_file())
    total_files = count_files(materials)
    total_svgs = sum(r[3] for r in rows)
    # 内訳の合計が全体と一致することをその場で検算する（内訳と合計のズレを出荷しない）
    assert direct_files + sum(r[2] for r in rows) == total_files

    # ---- Markdown 出力（決定的・生成日時なし） ----
    out: list[str] = []
    out.append("# 実測統計（自動生成）")
    out.append("")
    out.append(
        "> このファイルは `tools/gen_stats.py` が実ファイルと `curriculum/registry/` から"
        "自動生成する。直接編集せず、教材・レジストリを更新したら "
        "`python3 tools/gen_stats.py` で再生成すること。"
        "出力は同一ツリーから常にバイト一致（生成日時を含めない）。"
        "`python3 tools/gen_stats.py --check` で、同梱の本ファイルが再生成結果と"
        "一致するかを機械検査できる。"
    )
    out.append(">")
    out.append(
        "> README 等の文中へ数字を直書きすると教材の追加のたびに古くなるため、"
        "数字の正本はこの表に置く。数字を直書きしている巡回先の一覧は "
        "[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) が持つ。"
    )
    out.append("")
    out.append("## レジストリ定義の全量（設計図）")
    out.append("")
    out.append(
        "生成元: `curriculum/registry/*.md`"
        "（表の解析は `tools/progress_index/build_progress_index.py` と同一）。"
        "各単元の状態は [../curriculum/PROGRESS_INDEX.md](../curriculum/PROGRESS_INDEX.md) が正。"
    )
    out.append("")
    out.append("| 教科 | 単元 | モジュール |")
    out.append("|---|---|---|")
    for subject, nu, nm in subjects:
        out.append(f"| {subject} | {nu} | {nm} |")
    out.append(
        f"| **計（{len(subjects)}教科）** | **{total_units}** | **{total_modules}** |"
    )
    out.append("")
    out.append("## 同梱教材の実測（materials/）")
    out.append("")
    out.append(
        "同梱パッケージ＝ `materials/<教科フォルダ>/` 直下の `.md` を含むフォルダ"
        "（単元・診断・巻末資料）。ファイル数は配下の全ファイルの実測。"
        "SVG図版は各パッケージの `assets/` 配下の `.svg` の実測。"
        "構成の説明は [../materials/README.md](../materials/README.md) を参照。"
    )
    out.append("")
    out.append("| 教科フォルダ | パッケージ | ファイル | SVG図版 |")
    out.append("|---|---|---|---|")
    for name, npkg, nfile, nsvg in rows:
        out.append(f"| `{name}` | {npkg} | {nfile} | {nsvg} |")
    out.append(f"| （`materials/` 直下のファイル） | — | {direct_files} | — |")
    out.append(
        f"| **計** | **{total_pkgs}** | **{total_files}** | **{total_svgs}** |"
    )
    out.append("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="実測統計 docs/STATS.md を生成・検査する")
    parser.add_argument(
        "root", nargs="?", type=Path, default=REPO,
        help="リポジトリルート（省略時はこのスクリプトの位置から自動判定）",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="出力先ファイル（省略時は <root>/docs/STATS.md）",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="書き込まず、同梱ファイルと再生成結果のバイト一致を検査する（不一致・生成不能で失敗）",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        md = build(root)
    except (B.RegistryError, StatsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    target = args.out if args.out is not None else root / "docs" / "STATS.md"
    if args.check:
        if not target.is_file():
            print(f"ERROR: 検査対象が存在しない: {target}", file=sys.stderr)
            return 1
        if target.read_bytes() != md.encode("utf-8"):
            print(
                f"ERROR: {target} が再生成結果とバイト不一致"
                "（教材・レジストリ更新後の再生成漏れ）",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {target} は再生成結果とバイト一致")
        return 0
    target.write_text(md, encoding="utf-8")
    print(f"written: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
