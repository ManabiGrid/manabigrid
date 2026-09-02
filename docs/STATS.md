# 実測統計（自動生成）

> このファイルは `tools/gen_stats.py` が実ファイルと `curriculum/registry/` から自動生成する。直接編集せず、教材・レジストリを更新したら `python3 tools/gen_stats.py` で再生成すること。出力は同一ツリーから常にバイト一致（生成日時を含めない）。`python3 tools/gen_stats.py --check` で、同梱の本ファイルが再生成結果と一致するかを機械検査できる。
>
> README 等の文中へ数字を直書きすると教材の追加のたびに古くなるため、数字の正本はこの表に置く。数字を直書きしている巡回先の一覧は [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) が持つ。

## レジストリ定義の全量（設計図）

生成元: `curriculum/registry/*.md`（表の解析は `tools/progress_index/build_progress_index.py` と同一）。各単元の状態は [../curriculum/PROGRESS_INDEX.md](../curriculum/PROGRESS_INDEX.md) が正。

| 教科 | 単元 | モジュール |
|---|---|---|
| 数学 | 65 | 4 |
| 英語 | 48 | 14 |
| 国語 | 46 | 12 |
| 理科 | 145 | 0 |
| 社会 | 133 | 12 |
| **計（5教科）** | **437** | **42** |

## 同梱教材の実測（materials/）

同梱パッケージ＝ `materials/<教科フォルダ>/` 直下の `.md` を含むフォルダ（単元・診断・巻末資料）。ファイル数は配下の全ファイルの実測。SVG図版は各パッケージの `assets/` 配下の `.svg` の実測。構成の説明は [../materials/README.md](../materials/README.md) を参照。

| 教科フォルダ | パッケージ | ファイル | SVG図版 |
|---|---|---|---|
| `hs-math-i` | 2 | 86 | 38 |
| `jhs-eng-1` | 1 | 29 | 12 |
| `jhs-jpn` | 1 | 26 | 10 |
| `jhs-math-1` | 8 | 254 | 112 |
| `jhs-math-2` | 6 | 183 | 80 |
| `jhs-math-3` | 10 | 291 | 125 |
| `jhs-sci-2` | 1 | 22 | 8 |
| `jhs-soc` | 1 | 24 | 8 |
| （`materials/` 直下のファイル） | — | 1 | — |
| **計** | **30** | **916** | **393** |

