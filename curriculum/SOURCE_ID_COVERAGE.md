# source_id カバレッジ・レポート

実測日: 2026-07-21（tools/ci_checks.py の抽出ロジックで集計）

出典表への `source_id` 付与状況と、教材本文からの `[[SRC-...]]` 参照の付与状況（＝本文紐付けの残量）を可視化する。仕様は docs/SPEC_source_id.md。本文back-referenceは段階導入のため、導入直後の参照数は0が正常。

## サマリー

- 出典表を持つファイル数: 24
- 付与済み source_id 総数: 108（※理科=Codex管轄のため対象外・列付与せず）
- 本文からID参照済みの引用数: 0
- 本文未参照（今後の紐付け残量）: 108 / 108

## ファイル別内訳

| 教科 | 単元 | ファイル | source_id数 | 本文参照済み | 未参照 |
|---|---|---|---|---|---|
| hs-math-i | hs-math-i-quadratic-functions | teacher_notes.md | 1 | 0 | 1 |
| hs-math-i | hs-math-i-quadratic-functions | teacher_notes_L04-06.md | 1 | 0 | 1 |
| hs-math-i | hs-math-i-quadratic-functions | teacher_notes_L07-09.md | 1 | 0 | 1 |
| hs-math-i | hs-math-i-quadratic-functions | teacher_notes_L10-12.md | 2 | 0 | 2 |
| jhs-eng-1 | jhs-eng-1-introducing-yourself-and-others | teacher_notes.md | 2 | 0 | 2 |
| jhs-eng-1 | jhs-eng-1-introducing-yourself-and-others | teacher_notes_L04-08.md | 2 | 0 | 2 |
| jhs-jpn | jhs-jpn-all-kanji-goi-unyou | teacher_notes.md | 4 | 0 | 4 |
| jhs-jpn | jhs-jpn-all-kanji-goi-unyou | teacher_notes_L04以降.md | 2 | 0 | 2 |
| jhs-math-3 | jhs-math-3-expansion-factorization | teacher_notes.md | 8 | 0 | 8 |
| jhs-math-3 | jhs-math-3-function-y-ax2 | teacher_notes.md | 12 | 0 | 12 |
| jhs-math-3 | jhs-math-3-inscribed-angle | teacher_notes.md | 10 | 0 | 10 |
| jhs-math-3 | jhs-math-3-pythagorean-theorem | teacher_notes.md | 7 | 0 | 7 |
| jhs-math-3 | jhs-math-3-quadratic-equations | teacher_notes.md | 10 | 0 | 10 |
| jhs-math-3 | jhs-math-3-sampling-survey | teacher_notes.md | 8 | 0 | 8 |
| jhs-math-3 | jhs-math-3-similar-figures | teacher_notes.md | 6 | 0 | 6 |
| jhs-math-3 | jhs-math-3-similar-figures | teacher_notes_L17.md | 5 | 0 | 5 |
| jhs-math-3 | jhs-math-3-similar-figures | teacher_notes_S1.md | 4 | 0 | 4 |
| jhs-math-3 | jhs-math-3-similar-figures | teacher_notes_S2.md | 6 | 0 | 6 |
| jhs-math-3 | jhs-math-3-similar-figures | teacher_notes_S3S4.md | 4 | 0 | 4 |
| jhs-math-3 | jhs-math-3-square-roots | teacher_notes.md | 9 | 0 | 9 |
| jhs-soc | jhs-soc-civics-market-price | teacher_notes.md | 2 | 0 | 2 |
| jhs-soc | jhs-soc-civics-market-price | teacher_notes_L04-06.md | 2 | 0 | 2 |
| **合計** | | | **108** | **0** | **108** |

## 読み方

「未参照」は、出典行にIDは振られているが、教材本文側の引用箇所からまだ `[[SRC-...]]` で指していない件数を表す。既存単元の本文紐付けは改稿・レビュー時に順次進める（一括置換はしない）。新規単元は制作時点から本文参照を付ける。

