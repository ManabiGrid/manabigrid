---
distribution_status: published_draft
---

# materials/ — 教材本文

**現在14単元＋診断・巻末の2モジュール（計16パッケージ・447ファイル）を同梱しています**（2026-07-18時点。中3数学8単元＋科目診断・巻末資料の2モジュール、中2数学1単元、数学Ⅰ1単元、中1英語1単元、中学国語1単元、中2理科1単元、中学社会1単元。ファイル数はこのREADME自身を含む実測値）。各単元の工程の到達点（外部レビュー済・QA済・ドラフト等）は [../curriculum/PROGRESS_INDEX.md](../curriculum/PROGRESS_INDEX.md) で確認できます。**人間レビュー（実務者検収）が完了するまで、すべて候補ドラフト扱いです。**

単元パッケージの基本構成:

```text
materials/{科目・学年}/{unit_id}/
├── lesson_map.md          # 単元の設計図
├── lesson_01.md ...       # タグ付きcore原稿（原稿の正）
├── answer_key_*.md        # 解答（別ファイル分離）
├── teacher_notes.md       # 指導ノート（編集公開版）
├── assets/                # 自作SVG図版のみ（借用画像ゼロ・現在185枚）
└── assets_provenance/     # 図版生成スクリプト＋図版台帳（来歴）
```

一部の単元は、タグ付きcoreから生成した閲覧用ビュー（`teacher_guide` / `student_textbook_print` / `interactive_landing.html` 等）と同梱物一覧（`MANIFEST.md`）を持ちます（生成の仕組みは [../docs/SPEC_tagged_core.md](../docs/SPEC_tagged_core.md)）。内部処理用ビュー（AI処理用パック等）は非同梱です。

`distribution_status` の意味（frontmatterのステータス語彙）:

- `published_draft` = 公開済み・人間レビュー前の**候補ドラフト**。人間レビュー（実務者検収）が完了したファイルから、レビュー済みを示すステータス値（draft を reviewed に置き換えた値）へ昇格します。
- 各単元の工程到達点そのものは [../curriculum/PROGRESS_INDEX.md](../curriculum/PROGRESS_INDEX.md)（レジストリ由来）が正です。

読むときの注意:

- teacher_notes / teacher_guide の設計判断には**根拠区分ラベル**（Established / Adapted / Derived / Experimental / Rejected の5値・〔根拠区分: X〕のタグ様式）が付いています。
- 科目診断（`jhs-math-3-diagnostic`）は**試行版**です。難度・判定閾値は実利用データによる較正前で、較正後に改訂されます。
- teacher_notes 等が参照する内部調査資料（HR番号等）は非公開です。非公開の理由と照会方法は [../docs/METHODOLOGY.md](../docs/METHODOLOGY.md)（§6「内部調査資料について」）を参照してください。
- `verify_required` の標記がある記述は原典照合が未了です。重要な用途の前に利用者側で原典を確認してください（[../DISCLAIMER.md](../DISCLAIMER.md)）。
