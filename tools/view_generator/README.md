# view_generator — 1つの原稿から5つのビューを生成する

`view_generator.py` は、タグ付きのレッスン原稿（コアMarkdown）1つから、
読者別の5つのビューを機械生成するツール。**原稿（コア）が正であり、
ビューは常に生成物**——ビューを手で直さず、原稿を直して再生成する。

ライセンス: MIT（各ソースファイル冒頭に SPDX-License-Identifier: MIT を表示）。

## 5つのビュー

| ビュー | 対象読者 | 内容 |
|---|---|---|
| `student_print.md` | 生徒（印刷・演習用） | 本文＋雑談コラム。解答・ガイドなし。書き込み欄つき |
| `student_self_study.md` | 生徒（独習用） | 本文＋雑談コラム＋学習ガイド＋解答 |
| `teacher.md` | 指導者 | internal 以外の全タグ（発展 stretch・追加 plus を含む） |
| `notebooklm_exercise.md` | AIノートツール読込用（演習） | 単体で完結する演習向けビュー（出典・利用条件・免責つき） |
| `notebooklm_self_study.md` | AIノートツール読込用（独習） | 単体で完結する独習向けビュー（ガイド・解答つき） |

## 原稿のタグ記法

原稿では、読者によって出し分けたい部分を3コロンのブロックで囲む:

```text
:::guide
学習ガイドの本文。
:::
```

- 使えるタグ: `guide`（学習ガイド）/ `answer`（解答）/ `zatsudan`（雑談コラム）/
  `stretch`（発展）/ `plus`（追加）/ `internal`（内部メモ——どのビューにも出ない）
- 開始行は `:::タグ` ちょうど、終了行は `:::` ちょうど。
- 入れ子は内側から順に閉じる（LIFO）。未知のタグ・閉じ忘れ・対応しない閉じ行は
  生成エラーとして停止する（黙って壊れた出力を作らない）。
- ファイル冒頭のメタデータ（front matter）はビューへ複写されない。

## 使い方

生成（1ファイルまたはレッスンディレクトリを指定）:

```sh
python3 view_generator.py generate lessons/lesson_01.md generated-views --date 2026-07-13
```

検証（生成済みビューが原稿と正確に対応しているかを機械照合）:

```sh
python3 view_generator.py verify lessons/lesson_01.md generated-views
```

- `--unit-id`: 原稿から unit_id を読み取れない場合に明示指定する
- `--answer-link-template`: 解答ファイルへのリンク書式
  （既定: `answers/{lesson_id}_answers.md`）
- 出力は `出力先/{レッスンID}/` の下に5ビューが並ぶ。各ビューには
  準拠課程の表示と生成日が付く。

`verify` は、タグ外の本文（コアテキスト）がビューと**厳密一致**するかを
比較する。意味の類似ではなくバイト単位の一致検査なので、ビューへの手編集は
必ず検出される——直したいときは原稿を直して `generate` し直すこと。

生成器は原稿を一切変更しない。図版（`assets/` など）は原稿側の資産であり、
このツールの管理対象外。

## テスト

```sh
python3 -m unittest discover -s . -p 'test_*.py' -v
```

テストは同梱の受け入れサンプル（`sample/SAMPLE_LESSON_L01.md`・実教材ではない）
で完結する。サンプルはタグ語彙の記述例としても読める。
