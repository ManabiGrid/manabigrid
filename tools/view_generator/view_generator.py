#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate ManabiGrid views from tagged core Markdown lessons.

The accepted block syntax is:

    :::guide
    Content
    :::

Closers use LIFO semantics, so nested blocks are deterministic.  A block
opener must contain exactly one supported tag and a closer must be exactly
``:::``.  Front matter is metadata and is never copied into a view.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


TAGS = frozenset({"guide", "answer", "zatsudan", "stretch", "plus", "internal"})
DEFAULT_ANSWER_LINK = "answers/{lesson_id}_answers.md"
CURRICULUM_DISPLAY = "学習指導要領（平成29/30年告示）準拠"


class ViewGeneratorError(ValueError):
    """Raised when a core document violates the tagged-core contract."""


@dataclass
class Node:
    text: str = ""
    tag: str | None = None
    children: list["Node"] = field(default_factory=list)

    @property
    def is_block(self) -> bool:
        return self.tag is not None


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    title: str
    nodes: tuple[Node, ...]
    source_path: Path
    unit_id: str


@dataclass(frozen=True)
class ViewSpec:
    name: str
    filename: str
    visible_tags: frozenset[str]
    include_stretch: bool = False
    include_plus: bool = False
    notebook: bool = False
    append_answers_link: bool = True
    writing_space: bool = False


VIEW_SPECS = (
    ViewSpec(
        "student_print",
        "student_print.md",
        frozenset({"zatsudan"}),
        writing_space=True,
    ),
    ViewSpec(
        "student_self_study",
        "student_self_study.md",
        frozenset({"zatsudan", "guide", "answer"}),
    ),
    ViewSpec(
        "teacher",
        "teacher.md",
        frozenset(TAGS - {"internal"}),
        include_stretch=True,
        include_plus=True,
    ),
    ViewSpec(
        "notebooklm_exercise",
        "notebooklm_exercise.md",
        frozenset({"zatsudan"}),
        notebook=True,
    ),
    ViewSpec(
        "notebooklm_self_study",
        "notebooklm_self_study.md",
        frozenset({"zatsudan", "guide", "answer"}),
        notebook=True,
    ),
)


OPEN_RE = re.compile(r"^:::(?P<tag>[a-z][a-z0-9_-]*)[ \t]*\n?$")
CLOSE_RE = re.compile(r"^:::[ \t]*\n?$")
H1_RE = re.compile(r"^# (.+?)\s*$")
UNIT_ID_RE = re.compile(r"^[-*] unit_id:\s*(\S+)\s*$", re.MULTILINE)
APPENDIX_RE = re.compile(r"^## 付録: 期待されるビュー出力の対応表", re.MULTILINE)
DATE_RE = re.compile(r"生成日:\s*\d{4}-\d{2}-\d{2}")


def _strip_front_matter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end < 0:
        raise ViewGeneratorError("front matter starts with --- but has no closing ---")
    return text[end + len("\n---") :].lstrip("\n")


def _core_body(text: str) -> str:
    body = _strip_front_matter(text)
    lines = body.splitlines(keepends=True)
    first_h1 = next((i for i, line in enumerate(lines) if H1_RE.match(line)), None)
    if first_h1 is not None:
        lines = lines[first_h1:]
    body = "".join(lines)
    appendix = APPENDIX_RE.search(body)
    if appendix:
        body = body[: appendix.start()].rstrip() + "\n"
    return body


def parse_nodes(body: str) -> tuple[Node, ...]:
    root: list[Node] = []
    stack: list[Node] = []
    text_buffer: list[str] = []

    def current_children() -> list[Node]:
        return stack[-1].children if stack else root

    def flush() -> None:
        if text_buffer:
            current_children().append(Node(text="".join(text_buffer)))
            text_buffer.clear()

    for line_no, line in enumerate(body.splitlines(keepends=True), start=1):
        if CLOSE_RE.match(line):
            flush()
            if not stack:
                raise ViewGeneratorError(f"line {line_no}: closing ::: has no open block")
            stack.pop()
            continue
        opener = OPEN_RE.match(line)
        if opener:
            flush()
            tag = opener.group("tag")
            if tag not in TAGS:
                raise ViewGeneratorError(f"line {line_no}: unknown tag {tag!r}")
            node = Node(tag=tag)
            current_children().append(node)
            stack.append(node)
            continue
        if line.startswith(":::"):
            raise ViewGeneratorError(
                f"line {line_no}: fence must be exactly ::: or :::<tag>"
            )
        text_buffer.append(line)
    flush()
    if stack:
        tags = ", ".join(node.tag or "?" for node in stack)
        raise ViewGeneratorError(f"unclosed tagged block(s): {tags}")
    return tuple(root)


def _extract_title(body: str, fallback: str) -> str:
    match = H1_RE.search(body)
    return match.group(1).strip() if match else fallback


def load_lesson(path: Path, unit_id: str | None = None) -> Lesson:
    raw = path.read_text(encoding="utf-8")
    body = _core_body(raw)
    parsed_unit = UNIT_ID_RE.search(body)
    resolved_unit = unit_id or (parsed_unit.group(1) if parsed_unit else "VERIFY_REQUIRED")
    lesson_id = path.stem
    return Lesson(
        lesson_id=lesson_id,
        title=_extract_title(body, lesson_id),
        nodes=parse_nodes(body),
        source_path=path,
        unit_id=resolved_unit,
    )


def _node_visible(node: Node, spec: ViewSpec, ancestors_visible: bool = True) -> bool:
    if not node.is_block:
        return ancestors_visible
    assert node.tag is not None
    own = node.tag in spec.visible_tags
    if node.tag == "internal":
        own = False
    if node.tag == "stretch":
        own = spec.include_stretch
    if node.tag == "plus":
        own = spec.include_plus
    return ancestors_visible and own


def _render_nodes(nodes: Iterable[Node], spec: ViewSpec, ancestors_visible: bool = True) -> str:
    out: list[str] = []
    for node in nodes:
        visible = _node_visible(node, spec, ancestors_visible)
        if not node.is_block:
            if visible:
                out.append(node.text)
            continue
        out.append(_render_nodes(node.children, spec, visible))
    return "".join(out)


def extract_unmarked_text(nodes: Iterable[Node]) -> str:
    """Return the exact raw text outside all tagged blocks for equality checks."""
    out: list[str] = []
    for node in nodes:
        if not node.is_block:
            out.append(node.text)
    return "".join(out)


def _writing_space() -> str:
    return "\n\n---\n\n### 書き込み欄\n\n\n\n\n\n"


def _header(lesson: Lesson, spec: ViewSpec, generated_date: str) -> str:
    if spec.notebook:
        return (
            f"# {lesson.title}\n\n"
            f"教材単元: {lesson.unit_id}\n"
            f"{CURRICULUM_DISPLAY}・生成日: {generated_date}\n\n"
            "## 出典・利用条件\n\n"
            f"出典: {lesson.source_path.name} から自動生成したビュー（原稿が正・本ファイルは生成物）。\n"
            "ライセンス: リポジトリの LICENSE-materials.md（CC BY 4.0。第三者引用部分を除く——NOTICE.md参照）に従う。\n"
            "免責: 専門家の監修完了前の内容を含みうる。重要な用途の前に原典と DISCLAIMER.md を確認すること。\n\n"
        )
    return (
        f"# {lesson.title}\n\n"
        f"単元: {lesson.unit_id}\n"
        f"{CURRICULUM_DISPLAY}・生成日: {generated_date}\n\n"
    )


def render_view(
    lesson: Lesson,
    spec: ViewSpec,
    generated_date: str,
    answer_link: str = DEFAULT_ANSWER_LINK,
) -> str:
    content = _render_nodes(lesson.nodes, spec)
    # Keep the raw unmarked text byte-for-byte. Separators belong outside the
    # core markers so the equality check cannot hide whitespace drift.
    rendered = _header(lesson, spec, generated_date) + content
    if spec.writing_space:
        rendered += "\n\n" + _writing_space().strip()
    if spec.append_answers_link:
        rendered += (
            "\n\n## 対応する解答ファイル\n\n"
            f"対応解答: [{answer_link}]({answer_link})\n"
        )
    return rendered


def _iter_lesson_paths(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    if not input_path.is_dir():
        raise ViewGeneratorError(f"input path does not exist: {input_path}")
    paths = sorted(input_path.glob("*.md"))
    if not paths:
        raise ViewGeneratorError(f"no Markdown lessons found in: {input_path}")
    return paths


def generate(
    input_path: Path,
    output_dir: Path,
    generated_date: str,
    unit_id: str | None = None,
    answer_link_template: str = DEFAULT_ANSWER_LINK,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for path in _iter_lesson_paths(input_path):
        lesson = load_lesson(path, unit_id=unit_id)
        lesson_out = output_dir / lesson.lesson_id
        lesson_out.mkdir(parents=True, exist_ok=True)
        answer_link = answer_link_template.format(lesson_id=lesson.lesson_id)
        for spec in VIEW_SPECS:
            target = lesson_out / spec.filename
            target.write_text(
                render_view(lesson, spec, generated_date, answer_link), encoding="utf-8"
            )
            written.append(target)
    return written


def verify_unmarked_text(
    input_path: Path,
    generated_dir: Path,
    unit_id: str | None = None,
    answer_link_template: str = DEFAULT_ANSWER_LINK,
) -> None:
    """Fail unless every generated view is the exact AST-derived rendering."""
    for path in _iter_lesson_paths(input_path):
        lesson = load_lesson(path, unit_id=unit_id)
        expected = extract_unmarked_text(lesson.nodes)
        lesson_dir = generated_dir / lesson.lesson_id
        for spec in VIEW_SPECS:
            view_path = lesson_dir / spec.filename
            if not view_path.exists():
                raise ViewGeneratorError(f"missing generated view: {view_path}")
            actual = view_path.read_text(encoding="utf-8")
            answer_link = answer_link_template.format(lesson_id=lesson.lesson_id)
            expected_render = render_view(lesson, spec, "1970-01-01", answer_link)
            # Generation date is the only permitted run-to-run difference.
            actual_normalized = DATE_RE.sub("生成日: 1970-01-01", actual)
            if actual_normalized != expected_render:
                raise ViewGeneratorError(
                    f"unmarked core mismatch: {path.name} vs {spec.filename}"
                )
            if extract_unmarked_text(lesson.nodes) != expected:
                raise ViewGeneratorError(f"source core extraction changed: {path.name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="generate all views")
    gen.add_argument("input", type=Path, help="lesson Markdown file or lessons directory")
    gen.add_argument("output", type=Path, help="output directory")
    gen.add_argument("--date", default=dt.date.today().isoformat())
    gen.add_argument("--unit-id")
    gen.add_argument("--answer-link-template", default=DEFAULT_ANSWER_LINK)

    verify = sub.add_parser("verify", help="verify exact unmarked-core equality")
    verify.add_argument("input", type=Path)
    verify.add_argument("generated", type=Path)
    verify.add_argument("--unit-id")
    verify.add_argument("--answer-link-template", default=DEFAULT_ANSWER_LINK)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            written = generate(
                args.input,
                args.output,
                args.date,
                unit_id=args.unit_id,
                answer_link_template=args.answer_link_template,
            )
            print(f"generated {len(written)} view file(s) under {args.output}")
        else:
            verify_unmarked_text(
                args.input,
                args.generated,
                unit_id=args.unit_id,
                answer_link_template=args.answer_link_template,
            )
            print("PASS: exact unmarked core text matches across all generated views")
        return 0
    except (OSError, ViewGeneratorError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
