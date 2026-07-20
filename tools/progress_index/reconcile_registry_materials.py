#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""レジストリの状態と materials/ の実体を照合するレポート生成器（機械判定の第一歩）.

`docs/SPEC_progress_index.md` は、状態判定を「レジストリの記載」から
「成果物ファイルの実在による機械判定」へ切り替えることを**将来課題**として
残している（人手のステータス表は実体とズレるため）。本スクリプトはその第一歩で、
**状態を書き換えず**、レジストリの状態と materials/ の実体の食い違いを検出して
一覧するだけの読み取り専用ツールである。

検出する2方向のズレ:
  A. 成果物があるべき状態（ドラフト／QA済／外部レビュー済／人間レビュー済／公開済）
     なのに、materials/ に対応する教材フォルダ（.md を含む）が無い単元。
  B. materials/ に実体（.md を含むフォルダ）があるのに、レジストリが
     「未着手／調査済」（成果物なしの想定）になっている単元。
  参考: どの単元にも対応づかない materials/ 直下の教材フォルダ（孤児）も併記する。

マッピング規約:
  レジストリの unit_id は下位トピックを `--suffix` で細分することがある
  （例: `jhs-math-1-linear-equations--solving`）。materials/ は上位の単元単位で
  梱包されるため、照合キーは unit_id の `--` 以前（教材フォルダ名）で合わせる。
  1つの教材フォルダを複数の下位単元が共有していてよい。

注意: 本レポートは**警告（レポート出力）に留め、CI を fail させない**。
  現時点でズレがあれば大量に出うるため、fail 化は将来の判断とする。

使い方:
  python3 tools/progress_index/reconcile_registry_materials.py [リポジトリルート]
  （省略時はカレントディレクトリ。--out で出力先を指定可）
"""

from __future__ import annotations

import argparse
import datetime
import glob
import sys
from pathlib import Path

# build_progress_index の解析関数を再利用する（レジストリ表の正は同一）。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_progress_index as B  # noqa: E402

# 成果物（レッスン本文）があるべき状態
PRODUCED_STATES = {"ドラフト", "QA済", "外部レビュー済", "人間レビュー済", "公開済"}
# 成果物なしを想定する状態
NO_MATERIAL_STATES = {"未着手", "調査済"}


def materials_home(unit_id: str) -> str:
    """照合キー（教材フォルダ名）。下位トピックの `--suffix` を落とす。"""
    return unit_id.split("--", 1)[0]


def load_registry(root: Path) -> list[dict]:
    rd = root / "curriculum" / "registry"
    rows: list[dict] = []
    for stem, subject in B.SUBJECT_FILES:
        path = rd / f"{stem}.md"
        if not path.is_file():
            continue
        units, modules = B.parse_registry(path, subject)
        for r in units:
            r["kind"] = "unit"
        for r in modules:
            r["kind"] = "module"
        rows.extend(units)
        rows.extend(modules)
    return rows


def material_dirs(root: Path) -> dict[str, Path]:
    """materials/<subject>/<folder> のうち .md を含むフォルダ名 → パス。"""
    out: dict[str, Path] = {}
    for d in sorted(glob.glob(str(root / "materials" / "*" / "*"))):
        p = Path(d)
        if p.is_dir() and any(p.rglob("*.md")):
            out[p.name] = p
    return out


def reconcile(root: Path) -> dict:
    rows = load_registry(root)
    mats = material_dirs(root)

    missing: list[dict] = []   # A: 成果物あるべき but 実体なし
    unexpected: list[dict] = []  # B: 実体あり but 未着手/調査済
    for r in rows:
        home = materials_home(r["id"])
        present = home in mats
        if r["status"] in PRODUCED_STATES and not present:
            missing.append(r)
        elif r["status"] in NO_MATERIAL_STATES and present:
            unexpected.append(r)

    referenced = {materials_home(r["id"]) for r in rows}
    orphans = sorted(name for name in mats if name not in referenced)

    return {
        "rows": rows,
        "mats": mats,
        "missing": missing,
        "unexpected": unexpected,
        "orphans": orphans,
    }


def build_report(root: Path, result: dict) -> str:
    today = datetime.date.today().isoformat()
    rows = result["rows"]
    out: list[str] = []
    out.append("# レジストリ ⇄ materials 照合レポート")
    out.append("")
    out.append(
        "> 本ファイルは `tools/progress_index/reconcile_registry_materials.py` が生成する"
        "**照合レポート**（読み取り専用）。状態は書き換えず、レジストリの状態と "
        "materials/ の実体のズレを一覧するだけ。"
        "`docs/SPEC_progress_index.md` が将来課題とする「成果物ファイルの実在による"
        "機械判定」の第一歩。"
    )
    out.append("")
    out.append(f"- 実測日: {today}")
    out.append(f"- 対象: レジストリ行 {len(rows)} 件／教材フォルダ（.md を含む）{len(result['mats'])} 件")
    out.append(
        "- 照合キー: unit_id の `--` 以前（下位トピックは上位の教材フォルダを共有する）"
    )
    out.append(
        "- 判定: 本レポートは警告に留め、CI を fail させない（fail 化は将来の判断）"
    )
    out.append("")

    out.append("## 集計")
    out.append("")
    out.append("| 種別 | 件数 |")
    out.append("|---|---|")
    out.append(f"| A. 成果物があるべきだが実体なし | {len(result['missing'])} |")
    out.append(f"| B. 実体があるが未着手/調査済 | {len(result['unexpected'])} |")
    out.append(f"| 参考. どの単元にも対応しない教材フォルダ | {len(result['orphans'])} |")
    out.append("")

    out.append("## A. 成果物があるべき状態なのに materials/ に実体がない")
    out.append("")
    out.append(
        "対象状態: ドラフト／QA済／外部レビュー済／人間レビュー済／公開済。"
        "レジストリが先行し、教材フォルダ（`.md` を含む）が未作成の可能性。"
    )
    out.append("")
    if result["missing"]:
        out.append("| id | 種別 | 状態 | 想定フォルダ名 |")
        out.append("|---|---|---|---|")
        for r in sorted(result["missing"], key=lambda r: r["id"]):
            out.append(
                f"| `{r['id']}` | {r['kind']} | {r['status']} | `{materials_home(r['id'])}` |"
            )
    else:
        out.append("- 該当なし。")
    out.append("")

    out.append("## B. materials/ に実体があるのにレジストリが未着手/調査済")
    out.append("")
    out.append(
        "教材フォルダ（`.md` を含む）が実在するのに、レジストリ状態が"
        "「未着手」または「調査済」のもの。レジストリの状態更新漏れの可能性。"
    )
    out.append("")
    if result["unexpected"]:
        out.append("| id | 種別 | 状態 | 教材フォルダ名 |")
        out.append("|---|---|---|---|")
        for r in sorted(result["unexpected"], key=lambda r: r["id"]):
            out.append(
                f"| `{r['id']}` | {r['kind']} | {r['status']} | `{materials_home(r['id'])}` |"
            )
    else:
        out.append("- 該当なし。")
    out.append("")

    out.append("## 参考. どの単元・モジュールにも対応づかない教材フォルダ")
    out.append("")
    out.append(
        "`materials/*/` 直下にあり `.md` を含むが、レジストリのどの id からも"
        "（`--` 以前で）参照されないフォルダ。命名ずれ・レジストリ欠落の可能性。"
    )
    out.append("")
    if result["orphans"]:
        out.append("| 教材フォルダ名 |")
        out.append("|---|")
        for name in result["orphans"]:
            out.append(f"| `{name}` |")
    else:
        out.append("- 該当なし。")
    out.append("")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="レジストリと materials の照合レポートを生成する")
    parser.add_argument("root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--stdout", action="store_true", help="ファイルに書かず標準出力へ出す（確認用）"
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    result = reconcile(root)
    report = build_report(root, result)
    if args.stdout:
        sys.stdout.write(report)
    else:
        out = args.out if args.out is not None else root / "curriculum" / "REGISTRY_MATERIALS_RECONCILE.md"
        out.write_text(report, encoding="utf-8")
        print(f"written: {out}")
    print(
        f"[reconcile] A(実体なし)={len(result['missing'])} "
        f"B(未着手/調査済だが実体あり)={len(result['unexpected'])} "
        f"孤児フォルダ={len(result['orphans'])}"
    )
    return 0  # 常に 0（レポートのみ・fail 化はしない）


if __name__ == "__main__":
    raise SystemExit(main())
