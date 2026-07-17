# 単元プロンプト（unit_prompts）

「未着手」の単元を、**Claude Fable 5** を使って制作するためのプロンプト置き場
（新単元の制作は Fable 5 限定——理由と条件は [CONTRIBUTING.md](../../CONTRIBUTING.md)）。
このディレクトリには、テンプレートの変数を実際の単元で差し替えた**実例**を置く。
型そのものは [docs/prompts/UNIT_PROMPT_TEMPLATE.md](../../docs/prompts/UNIT_PROMPT_TEMPLATE.md) が正本。

## 使い方（4ステップ）

1. **未着手の単元を選ぶ** — [curriculum/PROGRESS_INDEX.md](../PROGRESS_INDEX.md) か
   [curriculum/registry/](../registry/) で状態が「未着手」の単元から選ぶ。
2. **着手宣言のIssueを立てる** — 選んだ unit_id を書いて着手を宣言する
   （同じ単元への二重着手を防ぐため。詳細は CONTRIBUTING.md）。
3. **テンプレートの変数を差し替えて、Claude Fable 5 で実行する** —
   `docs/prompts/UNIT_PROMPT_TEMPLATE.md` をコピーし、`{{UNIT_ID}}` などの変数を
   自分の単元に差し替える。工程1（調査）→工程2（正規化）→工程3（執筆）→
   工程4（セルフQA）を、**毎回新しい会話で**順に実行する
   （前の工程の成果物ファイルだけを次の工程に渡す——ここが品質の要）。
4. **PRを出す** — CONTRIBUTING.md のチェックリストに沿って提出する。
   使ったAIの名前と、どの工程を実行したかをPR説明に書く。
   verify_required（未確認事項）が残っていても提出してよい——残っていることが正直さの証明。

## 実例

変数を差し替え済みの、そのまま使える実例:

- [jhs-math-1-positive-negative-numbers--meaning-order.md](jhs-math-1-positive-negative-numbers--meaning-order.md) — 中1数学「正負の数の意味・大小・絶対値」
- [jhs-math-1-linear-equations--solving.md](jhs-math-1-linear-equations--solving.md) — 中1数学「一次方程式の解法」

新しい単元に着手するときは、これらをひな形にして自分の単元用のファイルを作るとよい
（このディレクトリへの追加もPR歓迎）。
