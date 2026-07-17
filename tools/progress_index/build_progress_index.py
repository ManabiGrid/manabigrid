#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""ManabiGrid 進捗一覧ジェネレータ（公開版）.

`curriculum/registry/*.md` の単元レジストリ表（列: unit_id / 単元名 /
学校段階・学年 / 状態）を読み取り、`curriculum/PROGRESS_INDEX.md` に
公私レーン → 中高 → 科目 → 学年 の階層別一覧と、状態別・科目別の集計を
生成する。

- 依存: Python 3 標準ライブラリのみ
- 入力の正: レジストリの表（このスクリプトは集計・整形のみを行う）
- 使い方: python3 build_progress_index.py [リポジトリルート]
  （省略時はカレントディレクトリをルートとみなす）

レジストリの約束事:
- 見出し（##）に「私立」または「入試」を含むセクションの表は
  私立・入試レーン、それ以外は公開コア（public_core）として扱う。
- 先頭列が module_id の表は「科目モジュール」（診断・巻末資料）として
  単元と別枠で集計する。
- 状態は7語のみ: 未着手 / 調査済 / ドラフト / QA済 / 外部レビュー済 /
  人間レビュー済 / 公開済。それ以外はエラーで停止する。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 表示順（工程の進んでいる順）
STATUS_ORDER = ["公開済", "人間レビュー済", "外部レビュー済", "QA済", "ドラフト", "調査済", "未着手"]

# レジストリファイル名 → 科目表示名（この順で表示）
SUBJECT_FILES = [
    ("math", "数学"),
    ("english", "英語"),
    ("japanese", "国語"),
    ("science", "理科"),
    ("social_studies", "社会"),
]

STAGES = ["中学", "高校", "その他"]

STATUS_LEGEND = [
    ("未着手", "レジストリに行があるのみ（成果物なし）。貢献者が着手できる単元"),
    ("調査済", "執筆前調査（一次資料ベースの調査ノート）まで完了"),
    ("ドラフト", "レッスン本文の初稿あり"),
    ("QA済", "セルフQA（数値再計算・独習完結性などの点検）まで完了"),
    ("外部レビュー済", "執筆と別系統のAIによる批判レビューと、その裁定まで完了"),
    ("人間レビュー済", "人間による単元ごとの正式な検収記録あり（README等の「通読・検収」＝同梱前ゲートの通し読み確認とは別の、正式工程）"),
    ("公開済", "正式な人間レビューを経て公開版へ昇格した記録あり（**リポジトリへの同梱とは独立**——同梱中でも候補ドラフト段階の単元は公開済とは数えない）"),
]


class RegistryError(ValueError):
    """レジストリ表が約束事に違反しているときに送出する。"""


class AnchorAllocator:
    """GitHub の自動見出しアンカーを文書内の出現順に再現する。

    GitHub は見出しテキストを小文字化し、記号を除去し、空白をハイフンに
    置換してアンカーにする。同名見出しには出現順に -1, -2 … を付ける。
    目次を本文より先に出力するため、見出しを文書に現れる順で登録して
    アンカーを確定させる。
    """

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def allocate(self, heading_text: str) -> str:
        slug = heading_text.strip().lower()
        slug = re.sub(r"[^\w\- ]", "", slug)  # 記号除去（日本語などの文字は保持）
        slug = slug.replace(" ", "-")
        n = self._counts.get(slug, 0)
        self._counts[slug] = n + 1
        return slug if n == 0 else f"{slug}-{n}"


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_registry(path: Path, subject: str) -> tuple[list[dict], list[dict]]:
    """1教科のレジストリから（単元行, モジュール行）を返す。"""
    units: list[dict] = []
    modules: list[dict] = []
    lane = "public"
    header: list[str] | None = None
    kind: str | None = None
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            if line.startswith("## "):
                lane = "private" if ("私立" in heading or "入試" in heading) else "public"
            header = None
            kind = None
            continue
        if not line.startswith("|"):
            header = None
            kind = None
            continue
        cells = split_row(line)
        if header is None:
            first = cells[0].strip("`")
            if first == "unit_id":
                kind = "unit"
            elif first == "module_id":
                kind = "module"
            else:
                kind = None
            header = cells
            continue
        if set(line.replace("|", "").strip()) <= {"-", " ", ":"}:
            continue  # 区切り行
        if kind is None or len(cells) < 4:
            continue
        row = {
            "id": cells[0].strip("`"),
            "title": cells[1],
            "grade": cells[2],
            "status": cells[3].strip("*"),
            "subject": subject,
            "lane": lane,
            "source": path.name,
        }
        if row["status"] not in STATUS_ORDER:
            raise RegistryError(
                f"{path.name}:{line_no}: 状態 {row['status']!r} は許可語彙にない"
            )
        (units if kind == "unit" else modules).append(row)
    return units, modules


def stage_of(unit_id: str) -> str:
    if unit_id.startswith("jhs-"):
        return "中学"
    if unit_id.startswith("hs-"):
        return "高校"
    return "その他"


def count_by_status(rows: list[dict]) -> list[int]:
    return [sum(1 for r in rows if r["status"] == s) for s in STATUS_ORDER]


def emit_unit_table(out: list[str], rows: list[dict]) -> None:
    out.append("| 学校段階・学年 | 単元名 | unit_id | 状態 |")
    out.append("|---|---|---|---|")
    for r in rows:
        out.append(f"| {r['grade']} | {r['title']} | `{r['id']}` | **{r['status']}** |")


def build(root: Path) -> str:
    registry_dir = root / "curriculum" / "registry"
    if not registry_dir.is_dir():
        raise RegistryError(f"レジストリが見つからない: {registry_dir}")

    units: list[dict] = []
    modules: list[dict] = []
    subjects: list[str] = []
    for stem, subject in SUBJECT_FILES:
        path = registry_dir / f"{stem}.md"
        if not path.is_file():
            continue
        subjects.append(subject)
        u, m = parse_registry(path, subject)
        units.extend(u)
        modules.extend(m)

    seen: set[str] = set()
    for r in units + modules:
        if r["id"] in seen:
            raise RegistryError(f"unit_id が重複している: {r['id']}")
        seen.add(r["id"])

    # ---- 階層構造（公私レーン → 中高 → 科目）を先に確定する ----
    lane_defs = (
        ("public", "公開コア（public_core）", "公立課程の標準内容。誰でも無料で使う本線。"),
        ("private", "私立・入試レーン中心", "公開コアを含まない差分レーン（私立先取り・入試演習等）。"),
    )
    lane_groups: list[dict] = []
    for lane, lane_ja, desc in lane_defs:
        lrows = [r for r in units if r["lane"] == lane]
        if not lrows:
            continue
        stages_list: list[dict] = []
        for stage in STAGES:
            srows = [r for r in lrows if stage_of(r["id"]) == stage]
            if not srows:
                continue
            subj_list: list[dict] = []
            for subject in subjects:
                rows = sorted(
                    (r for r in srows if r["subject"] == subject),
                    key=lambda r: (r["grade"], r["id"]),
                )
                if not rows:
                    continue
                subj_list.append(
                    {"heading": f"{subject}（{len(rows)}単元）", "rows": rows}
                )
            stages_list.append({"heading": stage, "subjects": subj_list})
        lane_groups.append({"heading": lane_ja, "desc": desc, "stages": stages_list})

    # ---- 見出しアンカーを文書の出現順に確定する（目次が先頭に来るため） ----
    alloc = AnchorAllocator()
    alloc.allocate("ManabiGrid 進捗一覧（自動生成）")
    alloc.allocate("この表の見方")
    alloc.allocate("目次")
    anchor_legend = alloc.allocate("状態の定義")
    anchor_status_total = alloc.allocate("状態別集計（単元）")
    anchor_matrix = alloc.allocate("集計（科目 × 状態）")
    for lg in lane_groups:
        lg["anchor"] = alloc.allocate(lg["heading"])
        for st in lg["stages"]:
            st["anchor"] = alloc.allocate(st["heading"])
            for sj in st["subjects"]:
                sj["anchor"] = alloc.allocate(sj["heading"])
    anchor_all = alloc.allocate("全単元一覧（unit_id 順）")
    anchor_modules = (
        alloc.allocate("科目モジュール（単元と別枠: 診断・巻末資料）") if modules else None
    )
    alloc.allocate("既知の限界（正直に残す）")

    out: list[str] = []
    out.append("# ManabiGrid 進捗一覧（自動生成）")
    out.append("")
    out.append(
        "> このファイルは `tools/progress_index/build_progress_index.py` により "
        "`curriculum/registry/` の単元レジストリから自動生成されている。"
        "直接編集せず、レジストリを更新してから再生成すること。"
    )
    out.append("")
    out.append("- 生成元: `curriculum/registry/`（本ファイルはレジストリの内容だけから決定的に生成される——同一レジストリなら常にバイト一致）")
    out.append(f"- 対象: 単元 {len(units)} 件＋科目モジュール {len(modules)} 件（診断・巻末資料）")
    out.append("")

    # この表の見方
    out.append("## この表の見方")
    out.append("")
    out.append(
        f"- **状態列**は工程の到達点を7値で表す（意味は[状態の定義](#{anchor_legend})）。"
    )
    out.append(
        "- 状態は**制作の進行**を示すもので、公開リポジトリへの成果物の同梱有無とは独立"
        "（同梱されている教材の一覧は [materials/README.md](../materials/README.md)）。"
    )
    out.append(
        "- **いま誰かが作業中かどうか**はこの表には載らない——"
        "着手宣言Issue（タイトル「【着手】unit_id」）の一覧で分かる。"
    )
    out.append(
        "- 制作済み（成果物あり——候補ドラフト段階を含む・「完成」の意味ではない）の単元は状態列で分かるので、"
        "制作済み単元への遡及の着手宣言Issueは不要。"
    )
    out.append("")

    # 目次
    out.append("## 目次")
    out.append("")
    out.append(f"- [状態の定義](#{anchor_legend})")
    out.append(f"- [状態別集計（単元）](#{anchor_status_total})")
    out.append(f"- [集計（科目 × 状態）](#{anchor_matrix})")
    for lg in lane_groups:
        out.append(f"- [{lg['heading']}](#{lg['anchor']})")
        for st in lg["stages"]:
            subj_links = " / ".join(
                f"[{sj['heading']}](#{sj['anchor']})" for sj in st["subjects"]
            )
            out.append(f"  - [{st['heading']}](#{st['anchor']}): {subj_links}")
    out.append(f"- [全単元一覧（unit_id 順）](#{anchor_all})")
    if anchor_modules:
        out.append(f"- [科目モジュール](#{anchor_modules})")
    out.append("")

    # 状態の定義
    out.append("## 状態の定義")
    out.append("")
    out.append("| 状態 | 意味 |")
    out.append("|---|---|")
    for name, desc in STATUS_LEGEND:
        out.append(f"| {name} | {desc} |")
    out.append("")

    # 状態別集計
    out.append("## 状態別集計（単元）")
    out.append("")
    out.append("| 状態 | 件数 |")
    out.append("|---|---|")
    for s, c in zip(STATUS_ORDER, count_by_status(units)):
        out.append(f"| {s} | {c if c else '·'} |")
    out.append(f"| **計** | **{len(units)}** |")
    out.append("")

    # 科目×状態
    out.append("## 集計（科目 × 状態）")
    out.append("")
    out.append("| 科目 | " + " | ".join(STATUS_ORDER) + " | 計 |")
    out.append("|---|" + "---|" * (len(STATUS_ORDER) + 1))
    for subject in subjects:
        rows = [r for r in units if r["subject"] == subject]
        cnt = count_by_status(rows)
        out.append(
            f"| {subject} | "
            + " | ".join(str(c) if c else "·" for c in cnt)
            + f" | {len(rows)} |"
        )
    total = count_by_status(units)
    out.append(
        "| **計** | "
        + " | ".join(f"**{c}**" if c else "·" for c in total)
        + f" | **{len(units)}** |"
    )
    out.append("")

    # 階層別一覧: 公私 → 中高 → 科目 → 学年順
    for lg in lane_groups:
        out.append(f"## {lg['heading']}")
        out.append("")
        out.append(lg["desc"])
        out.append("")
        for st in lg["stages"]:
            out.append(f"### {st['heading']}")
            out.append("")
            for sj in st["subjects"]:
                out.append(f"#### {sj['heading']}")
                out.append("")
                emit_unit_table(out, sj["rows"])
                out.append("")

    # 全単元一覧
    out.append("## 全単元一覧（unit_id 順）")
    out.append("")
    out.append("| unit_id | 単元名 | 科目 | 学校段階・学年 | レーン | 状態 |")
    out.append("|---|---|---|---|---|---|")
    for r in sorted(units, key=lambda r: r["id"]):
        lane_ja = "公開コア" if r["lane"] == "public" else "私立・入試"
        out.append(
            f"| `{r['id']}` | {r['title']} | {r['subject']} | {r['grade']} |"
            f" {lane_ja} | **{r['status']}** |"
        )
    out.append("")

    # 科目モジュール
    if modules:
        out.append("## 科目モジュール（単元と別枠: 診断・巻末資料）")
        out.append("")
        out.append("| module_id | 名称 | 科目 | 学校段階・学年 | 状態 |")
        out.append("|---|---|---|---|---|")
        for r in sorted(modules, key=lambda r: r["id"]):
            out.append(
                f"| `{r['id']}` | {r['title']} | {r['subject']} |"
                f" {r['grade']} | **{r['status']}** |"
            )
        out.append("")

    # 既知の限界
    out.append("## 既知の限界（正直に残す）")
    out.append("")
    out.append(
        "- 理科は教科カーネル（単元一覧の元表）を正本とし、一覧をカーネル準拠へ改訂済み"
        "（学習指導要領解説との逐条照合・別ベンダAIとの相互検証・機械検査を通過）。"
        "今後も単元の統廃合（分割・統合・名称変更）がありうる。"
    )
    out.append("- この一覧はレジストリの記載を集計したもの。教材本体との突き合わせは各単元のレビュー工程で行う。")
    out.append("")
    out.append("[⬆ ページの最上部へ戻る](#manabigrid-進捗一覧自動生成)")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="単元レジストリから進捗一覧を生成する")
    parser.add_argument(
        "root", nargs="?", type=Path, default=Path("."),
        help="リポジトリルート（省略時はカレントディレクトリ）",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="出力先ファイル（省略時は <root>/curriculum/PROGRESS_INDEX.md）",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        md = build(root)
    except RegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output = args.out if args.out is not None else root / "curriculum" / "PROGRESS_INDEX.md"
    output.write_text(md, encoding="utf-8")
    print(f"written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
