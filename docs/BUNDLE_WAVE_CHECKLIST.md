# 同梱波チェックリスト（新しい教材を公開ツリーに同梱するときの手順）

新しい単元・モジュールを `materials/` に同梱する「同梱波」のたびに、この順で確認する。
目的は**同梱事故の再発防止**——frontmatter 漏れ・内部語彙の混入・ナビ/目次の生成漏れ・
数字の陳腐化・強調崩れ・レジストリと実体のズレを、公開前に機械検査でつぶす。

すべてローカルで完結する読み取り／生成手順で、外部送信は含まない。
コマンドはリポジトリのルートから実行する。Python は標準ライブラリのみで動く
（frontmatter の YAML 構文検査だけ `PyYAML`、強調検査の厳密モードだけ任意で
`markdown-it-py` を使う。未導入でも近似検査に自動フォールバックする）。

## 0. 事前確認

- [ ] 追加する教材フォルダが `materials/<教科>/<unit_id>/` の既存ツリーに倣っている
      （lesson 群・answer_key・出典リスト・工程成果物一式）。
- [ ] `verify_required`（要原典確認）の印を勝手に外していない。
      （PR 差分での削除は CI（`.github/workflows/quarantine.yml`）が検知して失敗する。）

## 1. frontmatter の付与

- [ ] 追加した `materials/` 配下の全 `.md` に frontmatter があり、`distribution_status` を含む。
- [ ] frontmatter は `---` 単独行（末尾空白なし）で正しく開閉している。
- 検査は後述の `ci_checks.py`（3番目「frontmatter検査」）が YAML 構文まで含めて行う。

## 2. 内部管理用の語彙・ID・ローカルパスの除去（検疫）

- [ ] 公開ツリーに、内部管理でしか使わない語彙・ステータス・ID・フラグ・ローカルパスが
      混入していない。**禁止パターンの正本は `.github/workflows/quarantine.yml` の
      「Internal vocabulary grep」**（ここに列挙し直すと、この文書自体が検査に引っかかるため参照に留める）。
- [ ] 不可視文字・全角化・Unicode 正規化での回避もしていない
      （同ワークフローの「Unicode evasion check」が検査する）。
- ローカルでの素早い確認: 上記ワークフローの `PATTERNS` を使って
      `grep -rInE -e "<pattern>" .` を回す（`.git` を除外）。ヒット 0 が合格。

## 3. ナビ・目次の再生成（べき等）

- [ ] `python3 tools/gen_nav.py` を実行し、各単元の `README.md`（目次）と
      lesson/answer_key 末尾のナビ行を再生成する。何度実行しても結果は同じ（べき等）。
- [ ] 生成物の差分が意図どおり（新規ファイル分のみ）であることを目視する。

## 4. 数字（同梱パッケージ数・ファイル数）の更新

- [ ] `materials/README.md` の同梱数（パッケージ数・ファイル数・内訳・時点）を実測で更新する。
      **数字の正本はこの1箇所**に集約してある（`README.md`・`CLAUDE.md`・`AGENTS.md` は
      具体的な数字を持たず、`materials/README.md` を指すだけにしてある——陳腐化の再発防止）。
- [ ] ファイル数は実測で数える（例: `find materials -type f | wc -l` を目安に、
      README 自身を含む数え方を `materials/README.md` の注記と揃える）。

## 5. 品質検査（ci_checks.py・7項目）

- [ ] `python3 tools/ci_checks.py` を実行し、**全項目 pass（終了コード 0）**。内訳:
  1. リンク照合（ローカル参照の実在）
  2. アンカー照合（`#見出し` の実在）
  3. frontmatter 検査（`distribution_status`＋YAML 構文）
  4. ビュー生成器テスト
  5. 図版再生成検算（assert 通過＋出荷 SVG との一致）
  6. 進捗一覧バイト一致（`PROGRESS_INDEX.md` の再生成一致）
  7. 強調崩れ検査（次項）

## 6. 強調崩れ検査（Markdown の `**` 露出）

- [ ] 上記 `ci_checks.py` の 7 番目でカバーされる。コード外に literal な強調記号が
      露出していないことを確認する（`markdown-it-py` があれば CommonMark で厳密検査、
      なければ「CJK 約物直後で閉じられない強調」の近似検査に自動で切り替わる）。
- 崩れの典型: 句読点・かぎ括弧のあとで強調を閉じようとして閉じられず、記号がそのまま残る形。

## 7. レジストリと実体の照合（R5a）

- [ ] `python3 tools/progress_index/reconcile_registry_materials.py .` を実行し、
      `curriculum/REGISTRY_MATERIALS_RECONCILE.md` を再生成する。
- [ ] レポートの「A（成果物があるべきだが実体なし）」「B（実体があるが未着手/調査済）」
      「孤児フォルダ」を確認する。**このレポートは警告に留め、CI を fail させない**
      （状態語の更新が必要ならレジストリ側を直してから進捗一覧を再生成する）。
- 状態を変えたら `python3 tools/progress_index/build_progress_index.py .` で
      `PROGRESS_INDEX.md` を再生成し、5-6（バイト一致）を再確認する。

## 完了条件

- [ ] 2〜7 のすべてがローカルで pass（`ci_checks.py` が終了コード 0、検疫 grep がヒット 0）。
- [ ] 変更が新規同梱分と、それに伴う生成物（ナビ・目次・進捗一覧・照合レポート・数字）に
      限られている（教材本文の意図しない改変が混ざっていない）。
