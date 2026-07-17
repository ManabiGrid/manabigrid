# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path

from view_generator import (
    ViewGeneratorError,
    extract_unmarked_text,
    generate,
    load_lesson,
    parse_nodes,
    verify_unmarked_text,
)


SAMPLE = Path(__file__).resolve().parent / "sample" / "SAMPLE_LESSON_L01.md"


class ViewGeneratorTests(unittest.TestCase):
    def test_acceptance_sample_generates_all_views_and_exact_core_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "views"
            written = generate(SAMPLE, output, "2026-07-11")
            self.assertEqual(len(written), 5)
            verify_unmarked_text(SAMPLE, output)
            self.assertTrue((output / SAMPLE.stem / "teacher.md").exists())

    def test_visibility_and_internal_exclusion(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "views"
            generate(SAMPLE, output, "2026-07-11")
            student = (output / SAMPLE.stem / "student_print.md").read_text(encoding="utf-8")
            teacher = (output / SAMPLE.stem / "teacher.md").read_text(encoding="utf-8")
            self.assertNotIn("判定問題のよくある考え方", student)
            self.assertIn("判定問題のよくある考え方", teacher)
            self.assertIn("**問1**", teacher)
            self.assertNotIn("本ファイルはビュー生成器", student)

    def test_nested_blocks_use_lifo_and_can_be_filtered(self):
        nodes = parse_nodes("before\n:::stretch\nstretch\n:::answer\nanswer\n:::\n:::\nafter\n")
        self.assertIn("before", extract_unmarked_text(nodes))
        self.assertIn("after", extract_unmarked_text(nodes))
        self.assertEqual(nodes[1].tag, "stretch")
        self.assertEqual(nodes[1].children[1].tag, "answer")

    def test_malformed_fences_are_rejected(self):
        with self.assertRaises(ViewGeneratorError):
            parse_nodes(":::guide\nnot closed\n")
        with self.assertRaises(ViewGeneratorError):
            parse_nodes(":::unknown\ntext\n:::\n")
        with self.assertRaises(ViewGeneratorError):
            parse_nodes(":::\n")

    def test_front_matter_and_acceptance_appendix_are_not_core_content(self):
        lesson = load_lesson(SAMPLE)
        core = extract_unmarked_text(lesson.nodes)
        self.assertNotIn("sample_metadata", core)
        self.assertNotIn("期待されるビュー出力の対応表", core)

    def test_verifier_catches_manual_core_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "views"
            generate(SAMPLE, output, "2026-07-11")
            view = output / SAMPLE.stem / "student_print.md"
            view.write_text(
                view.read_text(encoding="utf-8").replace("y=ax²", "y=CHANGED", 1),
                encoding="utf-8",
            )
            with self.assertRaises(ViewGeneratorError):
                verify_unmarked_text(SAMPLE, output)


if __name__ == "__main__":
    unittest.main()
