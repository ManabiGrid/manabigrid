# ManabiGrid 進捗一覧（自動生成）

> このファイルは `tools/progress_index/build_progress_index.py` により `curriculum/registry/` の単元レジストリから自動生成されている。直接編集せず、レジストリを更新してから再生成すること。

- 生成元: `curriculum/registry/`（本ファイルはレジストリの内容だけから決定的に生成される——同一レジストリなら常にバイト一致）
- 対象: 単元 437 件＋科目モジュール 40 件（診断・巻末資料）

## この表の見方

- **状態列**は工程の到達点を7値で表す（意味は[状態の定義](#状態の定義)）。
- 状態は**制作の進行**を示すもので、公開リポジトリへの成果物の同梱有無とは独立（同梱されている教材の一覧は [materials/README.md](../materials/README.md)）。
- **いま誰かが作業中かどうか**はこの表には載らない——着手宣言Issue（タイトル「【着手】unit_id」）の一覧で分かる。
- 制作済み（成果物あり——候補ドラフト段階を含む・「完成」の意味ではない）の単元は状態列で分かるので、制作済み単元への遡及の着手宣言Issueは不要。

## 目次

- [状態の定義](#状態の定義)
- [状態別集計（単元）](#状態別集計単元)
- [集計（科目 × 状態）](#集計科目--状態)
- [公開コア（public_core）](#公開コアpublic_core)
  - [中学](#中学): [数学（37単元）](#数学37単元) / [英語（29単元）](#英語29単元) / [国語（27単元）](#国語27単元) / [理科（81単元）](#理科81単元) / [社会（80単元）](#社会80単元)
  - [高校](#高校): [数学（28単元）](#数学28単元) / [英語（19単元）](#英語19単元) / [国語（19単元）](#国語19単元) / [理科（64単元）](#理科64単元) / [社会（53単元）](#社会53単元)
- [全単元一覧（unit_id 順）](#全単元一覧unit_id-順)
- [科目モジュール](#科目モジュール単元と別枠-診断巻末資料)

## 状態の定義

| 状態 | 意味 |
|---|---|
| 未着手 | レジストリに行があるのみ（成果物なし）。貢献者が着手できる単元 |
| 調査済 | 執筆前調査（一次資料ベースの調査ノート）まで完了 |
| ドラフト | レッスン本文の初稿あり |
| QA済 | セルフQA（数値再計算・独習完結性などの点検）まで完了 |
| 外部レビュー済 | 執筆と別系統のAIによる批判レビューと、その裁定まで完了 |
| 人間レビュー済 | 人間による単元ごとの正式な検収記録あり（README等の「通読・検収」＝同梱前ゲートの通し読み確認とは別の、正式工程） |
| 公開済 | 正式な人間レビューを経て公開版へ昇格した記録あり（**リポジトリへの同梱とは独立**——同梱中でも候補ドラフト段階の単元は公開済とは数えない） |

## 状態別集計（単元）

| 状態 | 件数 |
|---|---|
| 公開済 | · |
| 人間レビュー済 | 28 |
| 外部レビュー済 | 13 |
| QA済 | · |
| ドラフト | 3 |
| 調査済 | 2 |
| 未着手 | 391 |
| **計** | **437** |

## 集計（科目 × 状態）

| 科目 | 公開済 | 人間レビュー済 | 外部レビュー済 | QA済 | ドラフト | 調査済 | 未着手 | 計 |
|---|---|---|---|---|---|---|---|---|
| 数学 | · | 28 | 9 | · | 3 | · | 25 | 65 |
| 英語 | · | · | 1 | · | · | · | 47 | 48 |
| 国語 | · | · | 1 | · | · | 1 | 44 | 46 |
| 理科 | · | · | 1 | · | · | · | 144 | 145 |
| 社会 | · | · | 1 | · | · | 1 | 131 | 133 |
| **計** | · | **28** | **13** | · | **3** | **2** | **391** | **437** |

## 公開コア（public_core）

公立課程の標準内容。誰でも無料で使う本線。

### 中学

#### 数学（37単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 中1 | 度数分布表・ヒストグラム・度数折れ線 | `jhs-math-1-data-distribution--frequency-distribution` | **人間レビュー済** |
| 中1 | 相対度数（D(1)限定） | `jhs-math-1-data-distribution--relative-frequency` | **人間レビュー済** |
| 中1 | 代表値と範囲（小6既習の学び直し） | `jhs-math-1-data-distribution--representative-values-range` | **人間レビュー済** |
| 中1 | 不確定な事象の起こりやすさ（頻度確率） | `jhs-math-1-empirical-probability` | **人間レビュー済** |
| 中1 | 一次式の計算 | `jhs-math-1-letters-and-expressions--calculation` | **人間レビュー済** |
| 中1 | 文字を用いた式の表し方と数量関係（--relationships統合） | `jhs-math-1-letters-and-expressions--representation` | **人間レビュー済** |
| 中1 | 一次方程式の文章題 | `jhs-math-1-linear-equations--applications` | **人間レビュー済** |
| 中1 | 方程式と等式の性質 | `jhs-math-1-linear-equations--meaning-equivalence` | **人間レビュー済** |
| 中1 | 一次方程式の解法 | `jhs-math-1-linear-equations--solving` | **人間レビュー済** |
| 中1 | 基本の作図と図形の移動（作図による条件の表現を含む・--locus-intro統合） | `jhs-math-1-plane-figures--construction-movement` | **人間レビュー済** |
| 中1 | 円・おうぎ形と接線 | `jhs-math-1-plane-figures--sector-circle` | **人間レビュー済** |
| 中1 | 正負の数の加法・減法 | `jhs-math-1-positive-negative-numbers--addition-subtraction` | **人間レビュー済** |
| 中1 | 正負の数の活用 | `jhs-math-1-positive-negative-numbers--applications` | **人間レビュー済** |
| 中1 | 正負の数の意味・大小・絶対値 | `jhs-math-1-positive-negative-numbers--meaning-order` | **人間レビュー済** |
| 中1 | 正負の数の乗法・除法と累乗 | `jhs-math-1-positive-negative-numbers--multiplication-division-powers` | **人間レビュー済** |
| 中1 | 比例・反比例の活用 | `jhs-math-1-proportion-inverse-proportion--applications` | **人間レビュー済** |
| 中1 | 反比例の関係とグラフ | `jhs-math-1-proportion-inverse-proportion--inverse-proportion` | **人間レビュー済** |
| 中1 | 比例の関係とグラフ | `jhs-math-1-proportion-inverse-proportion--proportion` | **人間レビュー済** |
| 中1 | 柱体・錐体・球の表面積と体積 | `jhs-math-1-solid-figures--surface-area-volume` | **人間レビュー済** |
| 中1 | 空間図形の見取図・投影図・切断 | `jhs-math-1-solid-figures--views-sections` | **人間レビュー済** |
| 中2 | 二等辺三角形・平行四辺形の性質と証明 | `jhs-math-2-congruence-and-proof--isosceles-parallelogram` | **人間レビュー済** |
| 中2 | 証明のしくみと書き方 | `jhs-math-2-congruence-and-proof--proof` | **人間レビュー済** |
| 中2 | 三角形の合同条件と基本性質 | `jhs-math-2-congruence-and-proof--triangle-congruence` | **人間レビュー済** |
| 中2 | 単項式・多項式の計算 | `jhs-math-2-expression-calculation--polynomial-calculation` | **人間レビュー済** |
| 中2 | 文字式による説明 | `jhs-math-2-expression-calculation--proof-by-expression` | **人間レビュー済** |
| 中2 | 一次関数 | `jhs-math-2-linear-function` | **外部レビュー済** |
| 中2 | 確率 | `jhs-math-2-probability` | **人間レビュー済** |
| 中2 | 四分位範囲と箱ひげ図 | `jhs-math-2-quartiles-boxplot` | **人間レビュー済** |
| 中2 | 連立方程式 | `jhs-math-2-simultaneous-equations` | **人間レビュー済** |
| 中3 | 展開と因数分解 | `jhs-math-3-expansion-factorization` | **外部レビュー済** |
| 中3 | 関数 y=ax² | `jhs-math-3-function-y-ax2` | **外部レビュー済** |
| 中3 | 円周角の定理 | `jhs-math-3-inscribed-angle` | **外部レビュー済** |
| 中3 | 三平方の定理 | `jhs-math-3-pythagorean-theorem` | **外部レビュー済** |
| 中3 | 二次方程式 | `jhs-math-3-quadratic-equations` | **外部レビュー済** |
| 中3 | 標本調査 | `jhs-math-3-sampling-survey` | **外部レビュー済** |
| 中3 | 相似な図形 | `jhs-math-3-similar-figures` | **外部レビュー済** |
| 中3 | 平方根 | `jhs-math-3-square-roots` | **外部レビュー済** |

#### 英語（29単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 中1 | できることを伝える（can） | `jhs-eng-1-abilities-and-requests--can` | **未着手** |
| 中1 | 指示・依頼を伝える（命令文・Please） | `jhs-eng-1-abilities-and-requests--imperatives` | **未着手** |
| 中1 | 今していることを伝える（現在進行形） | `jhs-eng-1-actions-in-progress` | **未着手** |
| 中1 | be動詞で人・ものの状態を伝える | `jhs-eng-1-be-and-do-verbs--be` | **未着手** |
| 中1 | be動詞と一般動詞を使い分ける | `jhs-eng-1-be-and-do-verbs--contrast` | **未着手** |
| 中1 | 一般動詞で習慣・好みを伝える | `jhs-eng-1-be-and-do-verbs--general-verbs` | **未着手** |
| 中1 | 場所とあり方を伝える（There is/are・前置詞） | `jhs-eng-1-describing-places` | **未着手** |
| 中1 | 自分と身近な人を紹介する（三単現含む） | `jhs-eng-1-introducing-yourself-and-others` | **外部レビュー済** |
| 中1 | 疑問文と応答のやり取り | `jhs-eng-1-questions-and-responses` | **未着手** |
| 中2 | 比較して伝える | `jhs-eng-2-comparing-things` | **未着手** |
| 中2 | 条件・時を表す接続詞 if / when | `jhs-eng-2-conditions-and-connections--if-when` | **未着手** |
| 中2 | 考え・事実をつなぐ that節 | `jhs-eng-2-conditions-and-connections--that` | **未着手** |
| 中2 | 義務と助言を伝える（must・have to・should） | `jhs-eng-2-obligations-and-advice` | **未着手** |
| 中2 | 予定と意志を伝える（未来表現・不定詞） | `jhs-eng-2-plans-and-intentions` | **未着手** |
| 中2 | 好み・活動を表す動名詞と不定詞 | `jhs-eng-2-purposes-and-preferences--preferences` | **未着手** |
| 中2 | 目的を表す不定詞 | `jhs-eng-2-purposes-and-preferences--purpose` | **未着手** |
| 中2 | 過去の出来事を語る | `jhs-eng-2-telling-past-events` | **未着手** |
| 中2 | 手紙・メールで近況を伝える | `jhs-eng-2-writing-letters-and-emails` | **未着手** |
| 中3 | 受け身で出来事を描写する（受動態） | `jhs-eng-3-describing-with-passive` | **未着手** |
| 中3 | 完了・結果を語る現在完了 | `jhs-eng-3-experience-and-duration--completion-result` | **未着手** |
| 中3 | 継続を語る現在完了・現在完了進行形 | `jhs-eng-3-experience-and-duration--continuation` | **未着手** |
| 中3 | 経験を語る現在完了 | `jhs-eng-3-experience-and-duration--experience` | **未着手** |
| 中3 | まとまった文章を読む方略 | `jhs-eng-3-reading-longer-texts` | **未着手** |
| 中3 | 後置修飾で説明を加える | `jhs-eng-3-relative-clauses-enrichment--postmodification` | **未着手** |
| 中3 | 関係代名詞で人・ものを説明する | `jhs-eng-3-relative-clauses-enrichment--pronouns` | **未着手** |
| 中3 | まとまりのあるスピーチをする（発表） | `jhs-eng-3-structured-speech` | **未着手** |
| 中3 | 願望と仮定を語る（仮定法の基礎） | `jhs-eng-3-wishes-and-hypotheticals` | **未着手** |
| 中学共通 | 聞いて捉える（日常・社会的話題の聴解） | `jhs-eng-listening-comprehension` | **未着手** |
| 中学共通 | 文型を広げる（SVC・SVOO・SVOC・基本文型の残差整理） | `jhs-eng-sentence-patterns` | **未着手** |

#### 国語（27単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 中1 | 文学的文章の基礎読解：場面分けと登場人物の把握 | `jhs-jpn-1-bungaku-bamen-jinbutsu` | **未着手** |
| 中1 | 情報の扱い方入門：比較・分類と引用の基礎 | `jhs-jpn-1-jouhou-hikaku-bunrui` | **未着手** |
| 中1 | 記録文・報告文の基礎：事実を順序立てて書く | `jhs-jpn-1-kiroku-houkokubun` | **未着手** |
| 中1 | 古典入門：歴史的仮名遣いと古文の読み方 | `jhs-jpn-1-rekishiteki-kanazukai` | **未着手** |
| 中1 | 説明的文章の構造読解 | `jhs-jpn-1-setsumei-kouzou` | **未着手** |
| 中1 | 中1書写：楷書の字形・大きさ・配列と行書の基礎 | `jhs-jpn-1-shosha` | **未着手** |
| 中1 | 紹介スピーチと聞き方の基礎 | `jhs-jpn-1-shoukai-speech` | **未着手** |
| 中2 | 複数の説明的文章を比較して評価する | `jhs-jpn-2-explanatory-comparison` | **未着手** |
| 中2 | 根拠を示して書く意見文 | `jhs-jpn-2-ikenbun` | **未着手** |
| 中2 | 漢文入門：訓読のしくみ | `jhs-jpn-2-kanbun-kundoku` | **未着手** |
| 中2 | 聞き取りとメモ：要点把握・質問づくり | `jhs-jpn-2-kikitori-memo` | **未着手** |
| 中2 | 古文読解の基礎：係り結びと古語の意味 | `jhs-jpn-2-kobun-dokkai-kiso` | **未着手** |
| 中2 | 文学的文章の心情読解 | `jhs-jpn-2-shinjou-dokkai` | **未着手** |
| 中2 | 中2書写：行書と仮名の調和・楷書行書の使い分け | `jhs-jpn-2-shosha` | **未着手** |
| 中3 | 論説を批判的に読み、根拠を吟味する | `jhs-jpn-3-critical-argument-reading` | **未着手** |
| 中3 | 論点を整理して話し合う | `jhs-jpn-3-hanashiai-speech--discussion` | **未着手** |
| 中3 | 構成と表現を工夫してスピーチする | `jhs-jpn-3-hanashiai-speech--speech` | **未着手** |
| 中3 | 条件作文：資料を踏まえて条件に沿って書く | `jhs-jpn-3-jouken-sakubun` | **未着手** |
| 中3 | 敬語の運用：尊敬・謙譲・丁寧と場面判断 | `jhs-jpn-3-keigo-unyou` | **未着手** |
| 中3 | 文学的文章の表現と語りを評価する | `jhs-jpn-3-literary-expression-evaluation` | **未着手** |
| 中3 | 中3・入試読解総合：説明文+文学+古文小問のセット演習 | `jhs-jpn-3-nyushi-dokkai-integrated` | **調査済** |
| 中3 | 資料を統合して報告する | `jhs-jpn-3-shiryou-houkoku` | **未着手** |
| 中3 | 中3書写：文字文化の豊かさと効果的な文字 | `jhs-jpn-3-shosha` | **未着手** |
| 中学 全学年 | 助詞・助動詞の働き | `jhs-jpn-1-bun-no-seibun--auxiliaries-particles` | **未着手** |
| 中学 全学年 | 文の成分と文節の関係 | `jhs-jpn-1-bun-no-seibun--sentence-components` | **未着手** |
| 中学 全学年 | 単語の分類と自立語・付属語 | `jhs-jpn-1-bun-no-seibun--words-parts-of-speech` | **未着手** |
| 全学年 | 中学・漢字と語彙の運用：同訓異字/熟語の構成/文脈判断 | `jhs-jpn-all-kanji-goi-unyou` | **外部レビュー済** |

#### 理科（81単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 中1 | 動物の分類 | `jhs-sci-1-animal-classification` | **未着手** |
| 中1 | 水溶液の濃度 | `jhs-sci-1-aqueous-solutions--concentration` | **未着手** |
| 中1 | 溶解と溶解度 | `jhs-sci-1-aqueous-solutions--solubility` | **未着手** |
| 中1 | 自然の恵みと火山・地震災害 | `jhs-sci-1-earth-benefits-hazards` | **未着手** |
| 中1 | 地震の揺れと地震波 | `jhs-sci-1-earthquakes--earthquake-waves` | **未着手** |
| 中1 | 地震による大地の変化 | `jhs-sci-1-earthquakes--earthquakes-land` | **未着手** |
| 中1 | 力のはたらき | `jhs-sci-1-force-basics` | **未着手** |
| 中1 | 気体の発生と性質 | `jhs-sci-1-gas-generation-properties` | **未着手** |
| 中1 | 光の反射・屈折と像 | `jhs-sci-1-light-and-sound--light` | **未着手** |
| 中1 | 音の発生・伝わり方と性質 | `jhs-sci-1-light-and-sound--sound` | **未着手** |
| 中1 | 生物を分類する観点と方法 | `jhs-sci-1-observation-classification--classification-methods` | **未着手** |
| 中1 | 生物観察の基本技能 | `jhs-sci-1-observation-classification--observation-skills` | **未着手** |
| 中1 | 植物の分類 | `jhs-sci-1-plant-classification` | **未着手** |
| 中1 | 金属・非金属・プラスチックの性質 | `jhs-sci-1-properties-of-matter--plastics-metals` | **未着手** |
| 中1 | 物質の性質と見分け方 | `jhs-sci-1-properties-of-matter--properties-identification` | **未着手** |
| 中1 | 融点・沸点と蒸留 | `jhs-sci-1-states-of-matter--melting-boiling` | **未着手** |
| 中1 | 物質の状態変化と粒子モデル | `jhs-sci-1-states-of-matter--state-changes` | **未着手** |
| 中1 | 身近な地形・地層・岩石と土地の広がり | `jhs-sci-1-strata-sedimentary-rocks--landforms-introduction` | **未着手** |
| 中1 | 堆積岩と地層の観察 | `jhs-sci-1-strata-sedimentary-rocks--sedimentary-rocks` | **未着手** |
| 中1 | 地層のでき方と地層から分かること | `jhs-sci-1-strata-sedimentary-rocks--strata-formation` | **未着手** |
| 中1 | 火成岩のつくりと分類 | `jhs-sci-1-volcanoes-igneous-rocks--igneous-rocks` | **未着手** |
| 中1 | 火山活動と噴出物 | `jhs-sci-1-volcanoes-igneous-rocks--volcanoes` | **未着手** |
| 中2 | 消化と吸収 | `jhs-sci-2-animal-body-functions--digestion-absorption` | **未着手** |
| 中2 | 排出とからだの調節 | `jhs-sci-2-animal-body-functions--excretion-regulation` | **未着手** |
| 中2 | 呼吸と血液循環 | `jhs-sci-2-animal-body-functions--respiration-circulation` | **未着手** |
| 中2 | 刺激と反応・神経系 | `jhs-sci-2-animal-body-functions--stimulus-response` | **未着手** |
| 中2 | 気団・前線と天気の変化 | `jhs-sci-2-atmospheric-movement-japan-weather--air-masses-fronts` | **未着手** |
| 中2 | 日本の季節の天気 | `jhs-sci-2-atmospheric-movement-japan-weather--japan-seasons` | **未着手** |
| 中2 | 気圧配置と風 | `jhs-sci-2-atmospheric-movement-japan-weather--pressure-wind` | **未着手** |
| 中2 | 原子・分子と化学式 | `jhs-sci-2-atoms-molecules-decomposition--atoms-molecules` | **未着手** |
| 中2 | 物質の分解 | `jhs-sci-2-atoms-molecules-decomposition--decomposition` | **未着手** |
| 中2 | 生物と細胞 | `jhs-sci-2-cells` | **未着手** |
| 中2 | 化合と化学反応式 | `jhs-sci-2-chemical-reactions-oxidation-reduction--combination` | **未着手** |
| 中2 | 酸化と燃焼 | `jhs-sci-2-chemical-reactions-oxidation-reduction--oxidation` | **未着手** |
| 中2 | 化学変化と熱 | `jhs-sci-2-chemical-reactions-oxidation-reduction--reaction-heat` | **未着手** |
| 中2 | 還元 | `jhs-sci-2-chemical-reactions-oxidation-reduction--reduction` | **未着手** |
| 中2 | 電磁誘導と発電 | `jhs-sci-2-current-and-magnetic-fields--electromagnetic-induction` | **未着手** |
| 中2 | 磁界中の電流が受ける力 | `jhs-sci-2-current-and-magnetic-fields--force-on-current` | **未着手** |
| 中2 | 電流がつくる磁界 | `jhs-sci-2-current-and-magnetic-fields--magnetic-field-current` | **未着手** |
| 中2 | 回路の電流と電圧 | `jhs-sci-2-electric-circuits--current-voltage` | **未着手** |
| 中2 | 電力と電力量・発熱 | `jhs-sci-2-electric-circuits--power-energy` | **未着手** |
| 中2 | 電気抵抗とオームの法則 | `jhs-sci-2-electric-circuits--resistance-ohm` | **未着手** |
| 中2 | 湿度と飽和水蒸気量の計算 | `jhs-sci-2-humidity-calculation` | **外部レビュー済** |
| 中2 | 化学変化と物質の質量 | `jhs-sci-2-mass-conservation-ratio` | **未着手** |
| 中2 | 光合成と葉のつくり | `jhs-sci-2-plant-body-functions--photosynthesis` | **未着手** |
| 中2 | 植物の呼吸 | `jhs-sci-2-plant-body-functions--respiration` | **未着手** |
| 中2 | 水・養分の移動と蒸散 | `jhs-sci-2-plant-body-functions--transport-transpiration` | **未着手** |
| 中2 | 静電気と電流の正体 | `jhs-sci-2-static-electricity-current` | **未着手** |
| 中2 | 自然の恵みと気象災害 | `jhs-sci-2-weather-benefits-hazards` | **未着手** |
| 中2 | 霧・雲の発生と湿度 | `jhs-sci-2-weather-observation--fog-clouds-humidity` | **未着手** |
| 中2 | 気象データから天気の変化を読む | `jhs-sci-2-weather-observation--weather-changes` | **未着手** |
| 中2 | 気象要素の観測と記録 | `jhs-sci-2-weather-observation--weather-elements` | **未着手** |
| 中3 | 酸・アルカリと中和 | `jhs-sci-3-acids-bases-neutralization` | **未着手** |
| 中3 | 生物の多様性と進化 | `jhs-sci-3-biodiversity-evolution` | **未着手** |
| 中3 | 太陽・星の年周運動と地球の公転 | `jhs-sci-3-celestial-motion--annual-motion` | **未着手** |
| 中3 | 天体の日周運動と地球の自転 | `jhs-sci-3-celestial-motion--daily-motion` | **未着手** |
| 中3 | 月と金星の見え方 | `jhs-sci-3-celestial-motion--moon-venus` | **未着手** |
| 中3 | 化学変化と電池 | `jhs-sci-3-chemical-batteries` | **未着手** |
| 中3 | 食物連鎖・食物網と生物間関係 | `jhs-sci-3-ecosystems--food-webs` | **未着手** |
| 中3 | 物質循環と生態系のつり合い | `jhs-sci-3-ecosystems--material-cycles-balance` | **未着手** |
| 中3 | 自然環境の調査と保全 | `jhs-sci-3-environment-science-technology--environment-conservation` | **未着手** |
| 中3 | 自然環境の保全と科学技術の利用 | `jhs-sci-3-environment-science-technology--science-technology-society` | **未着手** |
| 中3 | 浮力 | `jhs-sci-3-forces-pressure-buoyancy--buoyancy` | **未着手** |
| 中3 | 力の合成・分解 | `jhs-sci-3-forces-pressure-buoyancy--force-composition` | **未着手** |
| 中3 | 水圧 | `jhs-sci-3-forces-pressure-buoyancy--water-pressure` | **未着手** |
| 中3 | 細胞分裂と生物の成長 | `jhs-sci-3-growth-reproduction--cell-division-growth` | **未着手** |
| 中3 | 生物の生殖 | `jhs-sci-3-growth-reproduction--reproduction` | **未着手** |
| 中3 | 遺伝子と形質 | `jhs-sci-3-heredity-genes--genes` | **未着手** |
| 中3 | 遺伝の規則性 | `jhs-sci-3-heredity-genes--heredity-rules` | **未着手** |
| 中3 | 水溶液とイオン | `jhs-sci-3-ions` | **未着手** |
| 中3 | 力と運動の関係 | `jhs-sci-3-motion--force-motion` | **未着手** |
| 中3 | 運動の記録・速さ・向き | `jhs-sci-3-motion--motion-measurement` | **未着手** |
| 中3 | 地域の自然災害を資料から科学的に考察する | `jhs-sci-3-nature-and-humans--regional-natural-disasters` | **未着手** |
| 中3 | エネルギーとエネルギー資源 | `jhs-sci-3-science-technology-humans--energy-resources` | **未着手** |
| 中3 | 様々な物質とその利用 | `jhs-sci-3-science-technology-humans--materials-utilization` | **未着手** |
| 中3 | 科学技術の発展 | `jhs-sci-3-science-technology-humans--technology-development` | **未着手** |
| 中3 | 太陽系の構成と惑星 | `jhs-sci-3-solar-system-stars--solar-system` | **未着手** |
| 中3 | 太陽・恒星と宇宙 | `jhs-sci-3-solar-system-stars--sun-stars` | **未着手** |
| 中3 | エネルギーの変換と保存 | `jhs-sci-3-work-and-energy--energy-transformations` | **未着手** |
| 中3 | 力学的エネルギーとその保存 | `jhs-sci-3-work-and-energy--mechanical-energy` | **未着手** |
| 中3 | 仕事と仕事率 | `jhs-sci-3-work-and-energy--work-power` | **未着手** |

#### 社会（80単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 中学 公民 | 金融のしくみ | `jhs-soc-civics-banking-finance` | **未着手** |
| 中学 公民 | よりよい社会を目指して（社会科のまとめ探究） | `jhs-soc-civics-better-society` | **未着手** |
| 中学 公民 | 日本国憲法の基本原理 | `jhs-soc-civics-constitution-principles` | **未着手** |
| 中学 公民 | 消費生活と経済（家計・消費者の権利） | `jhs-soc-civics-consumer-life` | **未着手** |
| 中学 公民 | 民主主義の基本原理（多数決と少数意見の尊重） | `jhs-soc-civics-democracy-election-data--democracy-principles` | **未着手** |
| 中学 公民 | 選挙のしくみと政治参加・政治データ読解 | `jhs-soc-civics-democracy-election-data--elections-participation` | **未着手** |
| 中学 公民 | 内閣と行政 | `jhs-soc-civics-diet-cabinet-courts--cabinet` | **未着手** |
| 中学 公民 | 裁判所と司法 | `jhs-soc-civics-diet-cabinet-courts--courts` | **未着手** |
| 中学 公民 | 国会のしくみと立法 | `jhs-soc-civics-diet-cabinet-courts--diet` | **未着手** |
| 中学 公民 | 地球規模の課題（環境・資源・貧困） | `jhs-soc-civics-global-issues` | **未着手** |
| 中学 公民 | 基本的人権の尊重 | `jhs-soc-civics-human-rights` | **未着手** |
| 中学 公民 | 国際社会のしくみ（主権国家・国際連合） | `jhs-soc-civics-international-society` | **未着手** |
| 中学 公民 | 地方自治のしくみ | `jhs-soc-civics-local-government` | **未着手** |
| 中学 公民 | 市場経済と価格のはたらき | `jhs-soc-civics-market-price` | **外部レビュー済** |
| 中学 公民 | 現代社会における文化の意義・影響と継承（科学・芸術・宗教） | `jhs-soc-civics-modern-society--culture-meaning` | **未着手** |
| 中学 公民 | 現代社会の構造変化（少子高齢化・情報化・グローバル化） | `jhs-soc-civics-modern-society--structural-change` | **未着手** |
| 中学 公民 | 企業・生産と経済活動 | `jhs-soc-civics-production-labor--firms-production` | **未着手** |
| 中学 公民 | 労働の権利と働き方 | `jhs-soc-civics-production-labor--labor` | **未着手** |
| 中学 公民 | 財政と租税 | `jhs-soc-civics-public-finance-welfare--public-finance` | **未着手** |
| 中学 公民 | 社会保障のしくみと課題 | `jhs-soc-civics-public-finance-welfare--social-security` | **未着手** |
| 中学 公民 | 現代社会を捉える枠組み（対立と合意・効率と公正） | `jhs-soc-civics-social-frameworks` | **未着手** |
| 中学 地理 | 世界の気候と人々の生活を資料で読み解く | `jhs-soc-geography-climate-life-reading` | **調査済** |
| 中学 地理 | 日本の農林水産業 | `jhs-soc-geography-japan-industry-energy--agriculture-fisheries` | **未着手** |
| 中学 地理 | 工業と商業・サービス業（製造業から第3次産業まで拡張） | `jhs-soc-geography-japan-industry-energy--manufacturing-commerce-services` | **未着手** |
| 中学 地理 | 日本の資源・エネルギー | `jhs-soc-geography-japan-industry-energy--resources-energy` | **未着手** |
| 中学 地理 | 日本の自然災害と防災 | `jhs-soc-geography-japan-nature--hazards-adaptation` | **未着手** |
| 中学 地理 | 日本の地形・気候 | `jhs-soc-geography-japan-nature--landforms-climate` | **未着手** |
| 中学 地理 | 日本の姿（位置・領域・時差・都道府県） | `jhs-soc-geography-japan-overview` | **未着手** |
| 中学 地理 | 日本の地域的特色（人口） | `jhs-soc-geography-japan-population` | **未着手** |
| 中学 地理 | 地域調査・フィールドワーク方法モジュール | `jhs-soc-geography-japan-regional-survey` | **未着手** |
| 中学 地理 | 日本の諸地域（中部地方） | `jhs-soc-geography-japan-regions-chubu` | **未着手** |
| 中学 地理 | 日本の諸地域（中国・四国地方） | `jhs-soc-geography-japan-regions-chugoku-shikoku` | **未着手** |
| 中学 地理 | 日本の諸地域（北海道地方） | `jhs-soc-geography-japan-regions-hokkaido` | **未着手** |
| 中学 地理 | 日本の諸地域（関東地方） | `jhs-soc-geography-japan-regions-kanto` | **未着手** |
| 中学 地理 | 日本の諸地域（近畿地方） | `jhs-soc-geography-japan-regions-kinki` | **未着手** |
| 中学 地理 | 日本の諸地域（九州地方） | `jhs-soc-geography-japan-regions-kyushu` | **未着手** |
| 中学 地理 | 日本の諸地域（東北地方） | `jhs-soc-geography-japan-regions-tohoku` | **未着手** |
| 中学 地理 | 日本の地域的特色（交通・通信） | `jhs-soc-geography-japan-transport-communication` | **未着手** |
| 中学 地理 | 地域の在り方（身近な地域の課題と構想） | `jhs-soc-geography-region-vision` | **未着手** |
| 中学 地理 | 世界の姿（六大陸と三大洋・国々の位置） | `jhs-soc-geography-world-overview` | **未着手** |
| 中学 地理 | 世界の諸地域（アフリカ州） | `jhs-soc-geography-world-regions-africa` | **未着手** |
| 中学 地理 | 世界の諸地域（アジア州） | `jhs-soc-geography-world-regions-asia` | **未着手** |
| 中学 地理 | 世界の諸地域（ヨーロッパ州） | `jhs-soc-geography-world-regions-europe` | **未着手** |
| 中学 地理 | 世界の諸地域（北アメリカ州） | `jhs-soc-geography-world-regions-north-america` | **未着手** |
| 中学 地理 | 世界の諸地域（オセアニア州） | `jhs-soc-geography-world-regions-oceania` | **未着手** |
| 中学 地理 | 世界の諸地域（南アメリカ州） | `jhs-soc-geography-world-regions-south-america` | **未着手** |
| 中学 歴史 | 古代文明の成立 | `jhs-soc-history-ancient-civilizations--ancient-civilizations` | **未着手** |
| 中学 歴史 | 人類の出現と生活の変化 | `jhs-soc-history-ancient-civilizations--human-origins` | **未着手** |
| 中学 歴史 | 宗教・帝国と古代世界 | `jhs-soc-history-ancient-civilizations--religions-empires` | **未着手** |
| 中学 歴史 | 開国と幕末の動乱 | `jhs-soc-history-bakumatsu-meiji-restoration--opening-bakumatsu` | **未着手** |
| 中学 歴史 | 明治維新と文明開化 | `jhs-soc-history-bakumatsu-meiji-restoration--restoration-civilization` | **未着手** |
| 中学 歴史 | 高度経済成長と社会変化 | `jhs-soc-history-contemporary-japan--high-growth` | **未着手** |
| 中学 歴史 | 石油危機後の日本と国際化 | `jhs-soc-history-contemporary-japan--post-growth-internationalization` | **未着手** |
| 中学 歴史 | 世界恐慌・ファシズムと戦争への道 | `jhs-soc-history-depression-wwii--depression-fascism-road` | **未着手** |
| 中学 歴史 | 総力戦・戦時社会と戦争の惨禍 | `jhs-soc-history-depression-wwii--total-war-devastation` | **未着手** |
| 中学 歴史 | 江戸初期の対外政策と四つの窓口 | `jhs-soc-history-edo-bakuhan-system--foreign-relations` | **未着手** |
| 中学 歴史 | 江戸幕府の成立と大名統制 | `jhs-soc-history-edo-bakuhan-system--formation` | **未着手** |
| 中学 歴史 | 身分制と村・町の社会 | `jhs-soc-history-edo-bakuhan-system--society-status` | **未着手** |
| 中学 歴史 | 産業の発達と町人文化（江戸時代の社会） | `jhs-soc-history-edo-industry-culture` | **未着手** |
| 中学 歴史 | 幕府政治の改革 | `jhs-soc-history-edo-reforms` | **未着手** |
| 中学 歴史 | ヨーロッパ人の来航と全国統一 | `jhs-soc-history-european-contact-unification` | **未着手** |
| 中学 歴史 | 貴族の政治と国風文化（平安時代） | `jhs-soc-history-heian-court-culture` | **未着手** |
| 中学 歴史 | 日本列島の成り立ちと国家の形成（縄文〜古墳） | `jhs-soc-history-jomon-yayoi-kofun` | **未着手** |
| 中学 歴史 | 鎌倉幕府の成立 | `jhs-soc-history-kamakura-warrior-government--formation` | **未着手** |
| 中学 歴史 | 元寇と幕府の衰退 | `jhs-soc-history-kamakura-warrior-government--mongol-invasions` | **未着手** |
| 中学 歴史 | 鎌倉幕府の政治と社会 | `jhs-soc-history-kamakura-warrior-government--rule-society` | **未着手** |
| 中学 歴史 | 身近な地域の歴史（地域史の調べ方） | `jhs-soc-history-local-history` | **未着手** |
| 中学 歴史 | 自由民権運動と立憲国家の成立 | `jhs-soc-history-meiji-constitutional-state--rights-constitution` | **未着手** |
| 中学 歴史 | 日清・日露戦争と条約改正・帝国主義 | `jhs-soc-history-meiji-constitutional-state--wars-treaties-imperialism` | **未着手** |
| 中学 歴史 | 近代産業の発展と近代文化の形成 | `jhs-soc-history-modern-industry-culture` | **未着手** |
| 中学 歴史 | 市民革命と国民国家 | `jhs-soc-history-modern-revolutions--citizen-revolutions-nation-states` | **未着手** |
| 中学 歴史 | 産業革命と資本主義 | `jhs-soc-history-modern-revolutions--industrial-revolution-capitalism` | **未着手** |
| 中学 歴史 | 民衆の成長と産業・文化 | `jhs-soc-history-muromachi-society--popular-growth` | **未着手** |
| 中学 歴史 | 室町幕府と東アジア | `jhs-soc-history-muromachi-society--shogunate` | **未着手** |
| 中学 歴史 | 戦国大名と社会変化 | `jhs-soc-history-muromachi-society--warring-states` | **未着手** |
| 中学 歴史 | 時代区分・年表・年代計算モジュール | `jhs-soc-history-periodization-timeline` | **未着手** |
| 中学 歴史 | 戦後日本の民主化と国際社会への復帰 | `jhs-soc-history-postwar-reconstruction` | **未着手** |
| 中学 歴史 | 律令国家の成立（飛鳥・奈良時代） | `jhs-soc-history-ritsuryo-state` | **未着手** |
| 中学 歴史 | 歴史のまとめ（歴史と私たち・未来への構想） | `jhs-soc-history-summary-inquiry` | **未着手** |
| 中学 歴史 | 第一次世界大戦と大正デモクラシー | `jhs-soc-history-taisho-wwi` | **未着手** |

### 高校

#### 数学（28単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 高校 数学A | 場合の数と確率 | `hs-math-a-counting-and-probability` | **未着手** |
| 高校 数学A | 図形の性質 | `hs-math-a-geometry-properties` | **未着手** |
| 高校 数学A | 数学と人間の活動（整数など） | `hs-math-a-math-and-human-activity` | **未着手** |
| 高校 数学B | 数学と社会生活 | `hs-math-b-math-and-social-life` | **未着手** |
| 高校 数学B | 数列 | `hs-math-b-sequences` | **未着手** |
| 高校 数学B | 統計的な推測 | `hs-math-b-statistical-inference` | **未着手** |
| 高校 数学C | 数学的な表現の工夫 | `hs-math-c-mathematical-expression-devices` | **未着手** |
| 高校 数学C | 平面上の曲線と複素数平面 | `hs-math-c-plane-curves-complex-plane` | **未着手** |
| 高校 数学C | ベクトル | `hs-math-c-vectors` | **未着手** |
| 高校 数学Ⅰ | データの散らばりと相関 | `hs-math-i-data-analysis--description` | **未着手** |
| 高校 数学Ⅰ | 仮説検定の考え方 | `hs-math-i-data-analysis--inference-intro` | **未着手** |
| 高校 数学Ⅰ | 一次不等式 | `hs-math-i-numbers-and-expressions--inequalities` | **未着手** |
| 高校 数学Ⅰ | 多項式の展開と因数分解 | `hs-math-i-numbers-and-expressions--polynomial-expansion-factorization` | **未着手** |
| 高校 数学Ⅰ | 数の体系と実数・根号 | `hs-math-i-numbers-and-expressions--real-numbers` | **未着手** |
| 高校 数学Ⅰ | 二次関数のグラフと平行移動 | `hs-math-i-quadratic-functions--graph-transformations` | **ドラフト** |
| 高校 数学Ⅰ | 二次関数の最大・最小 | `hs-math-i-quadratic-functions--max-min` | **ドラフト** |
| 高校 数学Ⅰ | 二次方程式・二次不等式とグラフ | `hs-math-i-quadratic-functions--quadratic-equations-inequalities` | **ドラフト** |
| 高校 数学Ⅰ | 集合と命題 | `hs-math-i-sets-and-logic` | **未着手** |
| 高校 数学Ⅰ | 三角比の定義と相互関係 | `hs-math-i-trigonometric-ratios--ratios` | **未着手** |
| 高校 数学Ⅰ | 正弦定理・余弦定理と三角形の計量 | `hs-math-i-trigonometric-ratios--triangle-measurement` | **未着手** |
| 高校 数学Ⅱ | 微分・積分の考え | `hs-math-ii-calculus-basics` | **未着手** |
| 高校 数学Ⅱ | 指数関数・対数関数 | `hs-math-ii-exponential-logarithm` | **未着手** |
| 高校 数学Ⅱ | 図形と方程式 | `hs-math-ii-figures-and-equations` | **未着手** |
| 高校 数学Ⅱ | 三角関数 | `hs-math-ii-trigonometric-functions` | **未着手** |
| 高校 数学Ⅱ | いろいろな式 | `hs-math-ii-various-expressions` | **未着手** |
| 高校 数学Ⅲ | 微分法 | `hs-math-iii-differentiation` | **未着手** |
| 高校 数学Ⅲ | 積分法 | `hs-math-iii-integration` | **未着手** |
| 高校 数学Ⅲ | 極限 | `hs-math-iii-limits` | **未着手** |

#### 英語（19単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 高1 | 概要・要点を把握する | `hs-eng-ec1-gist-and-presentation--gist` | **未着手** |
| 高1 | 把握した内容を整理して発表する | `hs-eng-ec1-gist-and-presentation--presentation` | **未着手** |
| 高1 | 意見文の構成（主張・理由・根拠） | `hs-eng-le1-opinion-structure` | **未着手** |
| 高1 | パラグラフライティング | `hs-eng-le1-paragraph-writing` | **未着手** |
| 高2 | 要約を踏まえて応答する | `hs-eng-ec2-summary-and-response--response` | **未着手** |
| 高2 | 英語で要約する | `hs-eng-ec2-summary-and-response--summary` | **未着手** |
| 高2 | 立場を分けてディベートする | `hs-eng-le2-debate-discussion--debate` | **未着手** |
| 高2 | 論点を整理して議論する | `hs-eng-le2-debate-discussion--discussion` | **未着手** |
| 高校 英語コミュニケーションⅠ | 詳細と話者の意図を読み取る | `hs-eng-ec1-detail-and-intent` | **未着手** |
| 高校 英語コミュニケーションⅠ | 読んだ内容をもとに話し合う（ディスカッション入門） | `hs-eng-ec1-structured-discussion` | **未着手** |
| 高校 英語コミュニケーションⅠ | 聞き・読みした内容をもとに書く（英コミュⅠの書く受け皿） | `hs-eng-ec1-writing-from-input` | **未着手** |
| 高校 英語コミュニケーションⅡ | 社会的な話題を読み解き意見を交わす | `hs-eng-ec2-abstract-topics-discussion` | **未着手** |
| 高校 英語コミュニケーションⅡ | 資料を用いた発表（図表・データの読み取りと引用） | `hs-eng-ec2-presentation-with-sources` | **未着手** |
| 高校 英語コミュニケーションⅢ | 長く複雑な文章の読解（多様なジャンル） | `hs-eng-ec3-extended-reading` | **未着手** |
| 高校 英語コミュニケーションⅢ | 聞き・読みから統合して発信する（統合的言語活動） | `hs-eng-ec3-integrated-output` | **未着手** |
| 高校 論理・表現Ⅰ | 伝えるための文法再整理（機能から使う文法） | `hs-eng-le1-grammar-for-expression` | **未着手** |
| 高校 論理・表現Ⅱ | 反対意見をふまえた意見文（譲歩と反駁） | `hs-eng-le2-argumentative-essay` | **未着手** |
| 高校 論理・表現Ⅲ | エッセイの推敲プロセス（書き直しの技術） | `hs-eng-le3-essay-revision` | **未着手** |
| 高校 論理・表現Ⅲ | 発展的なディベート・ディスカッション（論点整理と合意形成） | `hs-eng-le3-extended-debate` | **未着手** |

#### 国語（19単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 高校 古典探究 | 古典探究・古典文法の読解運用：助動詞と敬語 | `hs-jpn-classical-jodoushi-keigo` | **未着手** |
| 高校 古典探究 | 漢文句形の反復運用モジュール | `hs-jpn-classical-kanbun-kukei` | **未着手** |
| 高校 国語表現 | 国語表現・実用的表現とプレゼンテーション | `hs-jpn-expression-jitsuyou-presen` | **未着手** |
| 高校 国語表現 | 小論文の型と推敲 | `hs-jpn-expression-shouronbun` | **未着手** |
| 高校 文学国語 | 文学国語・小説の語りと視点 | `hs-jpn-literary-katari-shiten` | **未着手** |
| 高校 文学国語 | 文学国語・詩の読解と創作 | `hs-jpn-literary-shi-dokkai-sousaku` | **未着手** |
| 高校 現代の国語 | 現代の国語・根拠を吟味する話合い | `hs-jpn-modern-discussion` | **未着手** |
| 高校 現代の国語 | 現代の国語・資料を用いた論理的文章 | `hs-jpn-modern-evidence-writing` | **未着手** |
| 高校 現代の国語 | 現代の国語・実用的な文章を書く：手順書・案内文・報告書 | `hs-jpn-modern-jitsuyou-bunsho` | **未着手** |
| 高校 現代の国語 | 現代の国語・実用文書読解：規約/案内/グラフつき文書 | `hs-jpn-modern-jitsuyoubun` | **未着手** |
| 高校 現代の国語 | 現代の国語・論理的文章の読解基礎：主張と根拠の把握 | `hs-jpn-modern-ronri-dokkai` | **未着手** |
| 高校 現代の国語 | 現代の国語・スピーチと発表：資料に基づいて話す・聞く | `hs-jpn-modern-speech-presentation` | **未着手** |
| 高校 言語文化 | 言語文化・表現創作：短歌俳句と随筆（伝統的題材から拡張） | `hs-jpn-culture-hyougen-sousaku` | **未着手** |
| 高校 言語文化 | 言語文化・漢文入門：訓読の復習と基本句形 | `hs-jpn-culture-kanbun-nyuumon` | **未着手** |
| 高校 言語文化 | 言語文化・近代小説入門：あらすじ/心情/表現の基礎 | `hs-jpn-culture-kindai-shousetsu` | **未着手** |
| 高校 言語文化 | 言語文化・古文入門：用言の活用と読みの基礎 | `hs-jpn-culture-kobun-nyuumon` | **未着手** |
| 高校 言語文化 | 言語文化・和歌と韻文入門：句切れ/掛詞/鑑賞の型 | `hs-jpn-culture-waka-inbun` | **未着手** |
| 高校 論理国語 | 論理国語・評論読解と要約 | `hs-jpn-logical-hyouron-youyaku` | **未着手** |
| 高校 論理国語 | 論理国語・論証的な文章を書く：反論処理と資料の活用 | `hs-jpn-logical-ronshou-kijutsu` | **未着手** |

#### 理科（64単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 高校 化学基礎 | 酸・塩基の定義と強弱 | `hs-sci-chemistry-basic-acids-and-bases--acids-bases` | **未着手** |
| 高校 化学基礎 | 中和反応と塩 | `hs-sci-chemistry-basic-acids-and-bases--neutralization` | **未着手** |
| 高校 化学基礎 | 中和滴定 | `hs-sci-chemistry-basic-acids-and-bases--titration` | **未着手** |
| 高校 化学基礎 | 原子の構造 | `hs-sci-chemistry-basic-atomic-structure-periodic-table--atomic-structure` | **未着手** |
| 高校 化学基礎 | 周期表と元素の性質 | `hs-sci-chemistry-basic-atomic-structure-periodic-table--periodic-table` | **未着手** |
| 高校 化学基礎 | 共有結合と分子 | `hs-sci-chemistry-basic-chemical-bonds--covalent-bond` | **未着手** |
| 高校 化学基礎 | イオンとイオン結合 | `hs-sci-chemistry-basic-chemical-bonds--ionic-bond` | **未着手** |
| 高校 化学基礎 | 金属結合と物質の性質 | `hs-sci-chemistry-basic-chemical-bonds--metallic-intermolecular` | **未着手** |
| 高校 化学基礎 | 化学が拓く世界 | `hs-sci-chemistry-basic-chemistry-opens-world` | **未着手** |
| 高校 化学基礎 | 単体と化合物 | `hs-sci-chemistry-basic-composition-of-matter--pure-substances` | **未着手** |
| 高校 化学基礎 | 混合物の分離と精製 | `hs-sci-chemistry-basic-composition-of-matter--separation` | **未着手** |
| 高校 化学基礎 | 化学の特徴 | `hs-sci-chemistry-basic-introduction--chemistry-characteristics` | **未着手** |
| 高校 化学基礎 | 熱運動と物質の三態 | `hs-sci-chemistry-basic-introduction--thermal-motion-states` | **未着手** |
| 高校 化学基礎 | 物質量と粒子数・質量・気体体積 | `hs-sci-chemistry-basic-mole-stoichiometry--amount-of-substance` | **未着手** |
| 高校 化学基礎 | 化学反応式と量的関係 | `hs-sci-chemistry-basic-mole-stoichiometry--chemical-equations` | **未着手** |
| 高校 化学基礎 | 溶液の濃度と調製 | `hs-sci-chemistry-basic-mole-stoichiometry--solutions` | **未着手** |
| 高校 化学基礎 | 電池と酸化還元（化学基礎） | `hs-sci-chemistry-basic-oxidation-reduction--batteries` | **未着手** |
| 高校 化学基礎 | 酸化数と酸化還元 | `hs-sci-chemistry-basic-oxidation-reduction--oxidation-number` | **未着手** |
| 高校 地学基礎 | 大気の構造と運動 | `hs-sci-earth-basic-atmosphere-ocean--atmosphere` | **未着手** |
| 高校 地学基礎 | 大気・海洋相互作用と気候 | `hs-sci-earth-basic-atmosphere-ocean--climate` | **未着手** |
| 高校 地学基礎 | 海洋の構造と循環 | `hs-sci-earth-basic-atmosphere-ocean--ocean` | **未着手** |
| 高校 地学基礎 | 地球環境の科学 | `hs-sci-earth-basic-earth-environment--global-environment` | **未着手** |
| 高校 地学基礎 | 日本の自然環境・恩恵・災害・予測防災 | `hs-sci-earth-basic-earth-environment--japan-environment` | **未着手** |
| 高校 地学基礎 | 地球と生命の歴史 | `hs-sci-earth-basic-earth-history--earth-life-history` | **未着手** |
| 高校 地学基礎 | 地層・化石と地質時代 | `hs-sci-earth-basic-earth-history--geologic-time` | **未着手** |
| 高校 地学基礎 | 地球内部の構造 | `hs-sci-earth-basic-earth-structure--interior` | **未着手** |
| 高校 地学基礎 | 地球の形と大きさ | `hs-sci-earth-basic-earth-structure--shape-gravity` | **未着手** |
| 高校 地学基礎 | 地震・火山・気象災害のしくみ | `hs-sci-earth-basic-natural-hazards-disaster-prevention--hazard-mechanisms` | **未着手** |
| 高校 地学基礎 | 災害リスクの評価と防災 | `hs-sci-earth-basic-natural-hazards-disaster-prevention--risk-reduction` | **未着手** |
| 高校 地学基礎 | 地震の発生と分布 | `hs-sci-earth-basic-plate-tectonics--earthquakes` | **未着手** |
| 高校 地学基礎 | プレート運動と地形 | `hs-sci-earth-basic-plate-tectonics--plates` | **未着手** |
| 高校 地学基礎 | 火山活動と火成岩 | `hs-sci-earth-basic-plate-tectonics--volcanoes` | **未着手** |
| 高校 地学基礎 | 太陽系と地球の誕生 | `hs-sci-earth-basic-universe-solar-system--solar-system-earth-origin` | **未着手** |
| 高校 地学基礎 | 宇宙の誕生 | `hs-sci-earth-basic-universe-solar-system--universe-origin` | **未着手** |
| 高校 物理基礎 | 電流・電圧・抵抗と回路 | `hs-sci-physics-basic-electricity--current-circuits` | **未着手** |
| 高校 物理基礎 | 電気エネルギーと利用 | `hs-sci-physics-basic-electricity--electric-energy` | **未着手** |
| 高校 物理基礎 | エネルギーとその利用 | `hs-sci-physics-basic-energy-utilization` | **未着手** |
| 高校 物理基礎 | 自由落下・鉛直投射と落下運動 | `hs-sci-physics-basic-force-and-motion-laws--falling-motion` | **未着手** |
| 高校 物理基礎 | 力の表し方とつり合い | `hs-sci-physics-basic-force-and-motion-laws--forces-equilibrium` | **未着手** |
| 高校 物理基礎 | 運動の法則 | `hs-sci-physics-basic-force-and-motion-laws--laws-motion` | **未着手** |
| 高校 物理基礎 | 加速度と等加速度直線運動 | `hs-sci-physics-basic-motion--acceleration` | **未着手** |
| 高校 物理基礎 | 物理量の測定・有効数字・データの扱い | `hs-sci-physics-basic-motion--measurement-data` | **未着手** |
| 高校 物理基礎 | 速度と相対運動 | `hs-sci-physics-basic-motion--velocity` | **未着手** |
| 高校 物理基礎 | 物理学が拓く世界 | `hs-sci-physics-basic-physics-opens-world` | **未着手** |
| 高校 物理基礎 | 熱運動・温度・内部エネルギー | `hs-sci-physics-basic-thermal-energy--heat-temperature` | **未着手** |
| 高校 物理基礎 | 熱と仕事・エネルギー保存 | `hs-sci-physics-basic-thermal-energy--thermodynamics-intro` | **未着手** |
| 高校 物理基礎 | 音波と共鳴 | `hs-sci-physics-basic-waves-sound--sound` | **未着手** |
| 高校 物理基礎 | 波の表し方と性質 | `hs-sci-physics-basic-waves-sound--wave-properties` | **未着手** |
| 高校 物理基礎 | 力学的エネルギー | `hs-sci-physics-basic-work-mechanical-energy--mechanical-energy` | **未着手** |
| 高校 物理基礎 | 仕事と仕事率 | `hs-sci-physics-basic-work-mechanical-energy--work-power` | **未着手** |
| 高校 生物基礎 | 細胞とエネルギー代謝 | `hs-sci-biology-basic-cells-common-features--cells-metabolism` | **未着手** |
| 高校 生物基礎 | 生物の共通性と多様性 | `hs-sci-biology-basic-cells-common-features--common-features` | **未着手** |
| 高校 生物基礎 | 生物多様性 | `hs-sci-biology-basic-ecosystems-conservation--biodiversity` | **未着手** |
| 高校 生物基礎 | 生態系の保全 | `hs-sci-biology-basic-ecosystems-conservation--conservation` | **未着手** |
| 高校 生物基礎 | 生態系の成り立ちと物質循環 | `hs-sci-biology-basic-ecosystems-conservation--ecosystem-processes` | **未着手** |
| 高校 生物基礎 | DNAと遺伝情報 | `hs-sci-biology-basic-genes-dna--dna-structure` | **未着手** |
| 高校 生物基礎 | 遺伝情報の発現 | `hs-sci-biology-basic-genes-dna--gene-expression` | **未着手** |
| 高校 生物基礎 | 体液と循環 | `hs-sci-biology-basic-homeostasis--body-fluids` | **未着手** |
| 高校 生物基礎 | 自律神経・ホルモンと恒常性 | `hs-sci-biology-basic-homeostasis--regulation` | **未着手** |
| 高校 生物基礎 | 獲得免疫と免疫記憶 | `hs-sci-biology-basic-immunity--adaptive` | **未着手** |
| 高校 生物基礎 | 免疫と医療・免疫異常 | `hs-sci-biology-basic-immunity--disorders` | **未着手** |
| 高校 生物基礎 | 自然免疫 | `hs-sci-biology-basic-immunity--innate` | **未着手** |
| 高校 生物基礎 | 遷移とバイオーム | `hs-sci-biology-basic-vegetation-succession--succession` | **未着手** |
| 高校 生物基礎 | 植生と環境 | `hs-sci-biology-basic-vegetation-succession--vegetation` | **未着手** |

#### 社会（53単元）

| 学校段階・学年 | 単元名 | unit_id | 状態 |
|---|---|---|---|
| 高校 世界史探究 | 地球世界の課題 | `hs-soc-world_history_inquiry-contemporary-world` | **未着手** |
| 高校 世界史探究 | 諸地域の交流・再編 | `hs-soc-world_history_inquiry-interregional-exchange` | **未着手** |
| 高校 世界史探究 | 諸地域の結合・変容 | `hs-soc-world_history_inquiry-modern-integration` | **未着手** |
| 高校 世界史探究 | 諸地域の歴史的特質の形成 | `hs-soc-world_history_inquiry-regional-characteristics` | **未着手** |
| 高校 倫理 | 現代の諸課題と倫理（生命・環境・情報） | `hs-soc-ethics-contemporary-issues` | **未着手** |
| 高校 倫理 | 日本思想の展開 | `hs-soc-ethics-japanese-thought` | **未着手** |
| 高校 倫理 | 源流思想（ギリシア思想と宗教） | `hs-soc-ethics-source-thought` | **未着手** |
| 高校 倫理 | 西洋近現代思想 | `hs-soc-ethics-western-modern-thought` | **未着手** |
| 高校 公共 | 対立・合意・効率・公正の思考ツールモジュール | `hs-soc-public-conflict-consensus` | **未着手** |
| 高校 公共 | 選挙・政治参加と世論・メディア | `hs-soc-public-democracy-participation--elections-media-participation` | **未着手** |
| 高校 公共 | 民主政治の仕組みと地方自治 | `hs-soc-public-democracy-participation--governance-local-autonomy` | **未着手** |
| 高校 公共 | 財政・租税と社会保障 | `hs-soc-public-economy-and-society--fiscal-social-security` | **未着手** |
| 高校 公共 | 労働と職業生活 | `hs-soc-public-economy-and-society--labor-work` | **未着手** |
| 高校 公共 | 市場経済と企業・貨幣・金融 | `hs-soc-public-economy-and-society--market-finance` | **未着手** |
| 高校 公共 | 公共的な空間における基本的原理（幸福・正義・公正） | `hs-soc-public-foundational-principles` | **未着手** |
| 高校 公共 | 国際経済と地球規模課題の国際協力 | `hs-soc-public-international-cooperation--global-economy-cooperation` | **未着手** |
| 高校 公共 | 国際秩序と主権・安全保障 | `hs-soc-public-international-cooperation--order-security` | **未着手** |
| 高校 公共 | 契約・消費者と法の働き（法や規範の意義を含む） | `hs-soc-public-law-and-life--contracts-consumers-law` | **未着手** |
| 高校 公共 | 司法制度と市民の司法参加（裁判員制度） | `hs-soc-public-law-and-life--judiciary-participation` | **未着手** |
| 高校 公共 | 公共的な空間をつくる私たち（青年期と先人の思想） | `hs-soc-public-self-and-society` | **未着手** |
| 高校 公共 | 持続可能な社会づくりの主体となる私たち（まとめ探究） | `hs-soc-public-sustainable-capstone` | **未着手** |
| 高校 地理探究 | 地誌（世界の諸地域） | `hs-soc-geography_inquiry-regional-geography` | **未着手** |
| 高校 地理探究 | 系統地理（産業・人口・都市） | `hs-soc-geography_inquiry-systematic-human` | **未着手** |
| 高校 地理探究 | 系統地理（自然環境） | `hs-soc-geography_inquiry-systematic-physical` | **未着手** |
| 高校 地理総合 | 災害の地域性とリスク情報（ハザードマップ・新旧地形図） | `hs-soc-geography_comprehensive-disaster-prevention--hazard-risk-information` | **未着手** |
| 高校 地理総合 | 地域の防災・減災の計画 | `hs-soc-geography_comprehensive-disaster-prevention--regional-disaster-planning` | **未着手** |
| 高校 地理総合 | 地球環境問題と資源・エネルギー問題 | `hs-soc-geography_comprehensive-global-issues--environment-resources-energy` | **未着手** |
| 高校 地理総合 | 地球的課題の相互関連と国際協力 | `hs-soc-geography_comprehensive-global-issues--interrelation-cooperation` | **未着手** |
| 高校 地理総合 | 人口・食料問題と居住・都市問題 | `hs-soc-geography_comprehensive-global-issues--population-food-housing-urban` | **未着手** |
| 高校 地理総合 | グローバル化と生活文化の変容 | `hs-soc-geography_comprehensive-life-culture-diversity--globalization-culture-change` | **未着手** |
| 高校 地理総合 | 自然・社会環境と生活文化（宗教・言語を含む） | `hs-soc-geography_comprehensive-life-culture-diversity--nature-society-culture` | **未着手** |
| 高校 地理総合 | 地図・GIS活用スパイラルモジュール | `hs-soc-geography_comprehensive-map-gis-literacy` | **未着手** |
| 高校 地理総合 | 生活圏の調査と地域の展望 | `hs-soc-geography_comprehensive-region-future` | **未着手** |
| 高校 政治・経済 | 憲法と統治機構の構造整理 | `hs-soc-politics_economics-constitution-governance` | **未着手** |
| 高校 政治・経済 | 財政と金融 | `hs-soc-politics_economics-fiscal-monetary` | **未着手** |
| 高校 政治・経済 | 国際経済の動向と課題 | `hs-soc-politics_economics-international-economy` | **未着手** |
| 高校 政治・経済 | 国際政治の動向と課題 | `hs-soc-politics_economics-international-politics` | **未着手** |
| 高校 政治・経済 | 労働と社会保障 | `hs-soc-politics_economics-labor-social-security` | **未着手** |
| 高校 政治・経済 | 現代経済のしくみ（市場機構と国民所得） | `hs-soc-politics_economics-market-national-income` | **未着手** |
| 高校 政治・経済 | 現代日本の政治（選挙・政党・世論） | `hs-soc-politics_economics-political-participation` | **未着手** |
| 高校 日本史探究 | 原始・古代の日本 | `hs-soc-japanese_history_inquiry-ancient` | **未着手** |
| 高校 日本史探究 | 近世の日本 | `hs-soc-japanese_history_inquiry-early-modern` | **未着手** |
| 高校 日本史探究 | 中世の日本 | `hs-soc-japanese_history_inquiry-medieval` | **未着手** |
| 高校 日本史探究 | 近現代の日本 | `hs-soc-japanese_history_inquiry-modern-contemporary` | **未着手** |
| 高校 歴史総合 | 冷戦の展開と終結 | `hs-soc-history_comprehensive-globalization--cold-war-transformation` | **未着手** |
| 高校 歴史総合 | 経済のグローバル化と現代的課題の歴史的形成 | `hs-soc-history_comprehensive-globalization--economic-globalization-contemporary` | **未着手** |
| 高校 歴史総合 | 歴史の扉（歴史と私たち・歴史の特質と資料） | `hs-soc-history_comprehensive-history-door` | **未着手** |
| 高校 歴史総合 | 経済危機とファシズム・第二次世界大戦 | `hs-soc-history_comprehensive-mass-society--depression-wwii` | **未着手** |
| 高校 歴史総合 | 戦後国際秩序と脱植民地化 | `hs-soc-history_comprehensive-mass-society--postwar-decolonization` | **未着手** |
| 高校 歴史総合 | 第一次世界大戦と大衆社会 | `hs-soc-history_comprehensive-mass-society--wwi-mass-society` | **未着手** |
| 高校 歴史総合 | 18世紀のアジアと結び付く世界・日本の開国 | `hs-soc-history_comprehensive-modernization--asia-and-opening` | **未着手** |
| 高校 歴史総合 | 近代化への問い（資料から問いを立てる） | `hs-soc-history_comprehensive-modernization--modernization-questions` | **未着手** |
| 高校 歴史総合 | 国民国家の形成と産業化・帝国主義 | `hs-soc-history_comprehensive-modernization--nation-state-industrialization-imperialism` | **未着手** |

## 全単元一覧（unit_id 順）

| unit_id | 単元名 | 科目 | 学校段階・学年 | レーン | 状態 |
|---|---|---|---|---|---|
| `hs-eng-ec1-detail-and-intent` | 詳細と話者の意図を読み取る | 英語 | 高校 英語コミュニケーションⅠ | 公開コア | **未着手** |
| `hs-eng-ec1-gist-and-presentation--gist` | 概要・要点を把握する | 英語 | 高1 | 公開コア | **未着手** |
| `hs-eng-ec1-gist-and-presentation--presentation` | 把握した内容を整理して発表する | 英語 | 高1 | 公開コア | **未着手** |
| `hs-eng-ec1-structured-discussion` | 読んだ内容をもとに話し合う（ディスカッション入門） | 英語 | 高校 英語コミュニケーションⅠ | 公開コア | **未着手** |
| `hs-eng-ec1-writing-from-input` | 聞き・読みした内容をもとに書く（英コミュⅠの書く受け皿） | 英語 | 高校 英語コミュニケーションⅠ | 公開コア | **未着手** |
| `hs-eng-ec2-abstract-topics-discussion` | 社会的な話題を読み解き意見を交わす | 英語 | 高校 英語コミュニケーションⅡ | 公開コア | **未着手** |
| `hs-eng-ec2-presentation-with-sources` | 資料を用いた発表（図表・データの読み取りと引用） | 英語 | 高校 英語コミュニケーションⅡ | 公開コア | **未着手** |
| `hs-eng-ec2-summary-and-response--response` | 要約を踏まえて応答する | 英語 | 高2 | 公開コア | **未着手** |
| `hs-eng-ec2-summary-and-response--summary` | 英語で要約する | 英語 | 高2 | 公開コア | **未着手** |
| `hs-eng-ec3-extended-reading` | 長く複雑な文章の読解（多様なジャンル） | 英語 | 高校 英語コミュニケーションⅢ | 公開コア | **未着手** |
| `hs-eng-ec3-integrated-output` | 聞き・読みから統合して発信する（統合的言語活動） | 英語 | 高校 英語コミュニケーションⅢ | 公開コア | **未着手** |
| `hs-eng-le1-grammar-for-expression` | 伝えるための文法再整理（機能から使う文法） | 英語 | 高校 論理・表現Ⅰ | 公開コア | **未着手** |
| `hs-eng-le1-opinion-structure` | 意見文の構成（主張・理由・根拠） | 英語 | 高1 | 公開コア | **未着手** |
| `hs-eng-le1-paragraph-writing` | パラグラフライティング | 英語 | 高1 | 公開コア | **未着手** |
| `hs-eng-le2-argumentative-essay` | 反対意見をふまえた意見文（譲歩と反駁） | 英語 | 高校 論理・表現Ⅱ | 公開コア | **未着手** |
| `hs-eng-le2-debate-discussion--debate` | 立場を分けてディベートする | 英語 | 高2 | 公開コア | **未着手** |
| `hs-eng-le2-debate-discussion--discussion` | 論点を整理して議論する | 英語 | 高2 | 公開コア | **未着手** |
| `hs-eng-le3-essay-revision` | エッセイの推敲プロセス（書き直しの技術） | 英語 | 高校 論理・表現Ⅲ | 公開コア | **未着手** |
| `hs-eng-le3-extended-debate` | 発展的なディベート・ディスカッション（論点整理と合意形成） | 英語 | 高校 論理・表現Ⅲ | 公開コア | **未着手** |
| `hs-jpn-classical-jodoushi-keigo` | 古典探究・古典文法の読解運用：助動詞と敬語 | 国語 | 高校 古典探究 | 公開コア | **未着手** |
| `hs-jpn-classical-kanbun-kukei` | 漢文句形の反復運用モジュール | 国語 | 高校 古典探究 | 公開コア | **未着手** |
| `hs-jpn-culture-hyougen-sousaku` | 言語文化・表現創作：短歌俳句と随筆（伝統的題材から拡張） | 国語 | 高校 言語文化 | 公開コア | **未着手** |
| `hs-jpn-culture-kanbun-nyuumon` | 言語文化・漢文入門：訓読の復習と基本句形 | 国語 | 高校 言語文化 | 公開コア | **未着手** |
| `hs-jpn-culture-kindai-shousetsu` | 言語文化・近代小説入門：あらすじ/心情/表現の基礎 | 国語 | 高校 言語文化 | 公開コア | **未着手** |
| `hs-jpn-culture-kobun-nyuumon` | 言語文化・古文入門：用言の活用と読みの基礎 | 国語 | 高校 言語文化 | 公開コア | **未着手** |
| `hs-jpn-culture-waka-inbun` | 言語文化・和歌と韻文入門：句切れ/掛詞/鑑賞の型 | 国語 | 高校 言語文化 | 公開コア | **未着手** |
| `hs-jpn-expression-jitsuyou-presen` | 国語表現・実用的表現とプレゼンテーション | 国語 | 高校 国語表現 | 公開コア | **未着手** |
| `hs-jpn-expression-shouronbun` | 小論文の型と推敲 | 国語 | 高校 国語表現 | 公開コア | **未着手** |
| `hs-jpn-literary-katari-shiten` | 文学国語・小説の語りと視点 | 国語 | 高校 文学国語 | 公開コア | **未着手** |
| `hs-jpn-literary-shi-dokkai-sousaku` | 文学国語・詩の読解と創作 | 国語 | 高校 文学国語 | 公開コア | **未着手** |
| `hs-jpn-logical-hyouron-youyaku` | 論理国語・評論読解と要約 | 国語 | 高校 論理国語 | 公開コア | **未着手** |
| `hs-jpn-logical-ronshou-kijutsu` | 論理国語・論証的な文章を書く：反論処理と資料の活用 | 国語 | 高校 論理国語 | 公開コア | **未着手** |
| `hs-jpn-modern-discussion` | 現代の国語・根拠を吟味する話合い | 国語 | 高校 現代の国語 | 公開コア | **未着手** |
| `hs-jpn-modern-evidence-writing` | 現代の国語・資料を用いた論理的文章 | 国語 | 高校 現代の国語 | 公開コア | **未着手** |
| `hs-jpn-modern-jitsuyou-bunsho` | 現代の国語・実用的な文章を書く：手順書・案内文・報告書 | 国語 | 高校 現代の国語 | 公開コア | **未着手** |
| `hs-jpn-modern-jitsuyoubun` | 現代の国語・実用文書読解：規約/案内/グラフつき文書 | 国語 | 高校 現代の国語 | 公開コア | **未着手** |
| `hs-jpn-modern-ronri-dokkai` | 現代の国語・論理的文章の読解基礎：主張と根拠の把握 | 国語 | 高校 現代の国語 | 公開コア | **未着手** |
| `hs-jpn-modern-speech-presentation` | 現代の国語・スピーチと発表：資料に基づいて話す・聞く | 国語 | 高校 現代の国語 | 公開コア | **未着手** |
| `hs-math-a-counting-and-probability` | 場合の数と確率 | 数学 | 高校 数学A | 公開コア | **未着手** |
| `hs-math-a-geometry-properties` | 図形の性質 | 数学 | 高校 数学A | 公開コア | **未着手** |
| `hs-math-a-math-and-human-activity` | 数学と人間の活動（整数など） | 数学 | 高校 数学A | 公開コア | **未着手** |
| `hs-math-b-math-and-social-life` | 数学と社会生活 | 数学 | 高校 数学B | 公開コア | **未着手** |
| `hs-math-b-sequences` | 数列 | 数学 | 高校 数学B | 公開コア | **未着手** |
| `hs-math-b-statistical-inference` | 統計的な推測 | 数学 | 高校 数学B | 公開コア | **未着手** |
| `hs-math-c-mathematical-expression-devices` | 数学的な表現の工夫 | 数学 | 高校 数学C | 公開コア | **未着手** |
| `hs-math-c-plane-curves-complex-plane` | 平面上の曲線と複素数平面 | 数学 | 高校 数学C | 公開コア | **未着手** |
| `hs-math-c-vectors` | ベクトル | 数学 | 高校 数学C | 公開コア | **未着手** |
| `hs-math-i-data-analysis--description` | データの散らばりと相関 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-data-analysis--inference-intro` | 仮説検定の考え方 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-numbers-and-expressions--inequalities` | 一次不等式 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-numbers-and-expressions--polynomial-expansion-factorization` | 多項式の展開と因数分解 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-numbers-and-expressions--real-numbers` | 数の体系と実数・根号 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-quadratic-functions--graph-transformations` | 二次関数のグラフと平行移動 | 数学 | 高校 数学Ⅰ | 公開コア | **ドラフト** |
| `hs-math-i-quadratic-functions--max-min` | 二次関数の最大・最小 | 数学 | 高校 数学Ⅰ | 公開コア | **ドラフト** |
| `hs-math-i-quadratic-functions--quadratic-equations-inequalities` | 二次方程式・二次不等式とグラフ | 数学 | 高校 数学Ⅰ | 公開コア | **ドラフト** |
| `hs-math-i-sets-and-logic` | 集合と命題 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-trigonometric-ratios--ratios` | 三角比の定義と相互関係 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-i-trigonometric-ratios--triangle-measurement` | 正弦定理・余弦定理と三角形の計量 | 数学 | 高校 数学Ⅰ | 公開コア | **未着手** |
| `hs-math-ii-calculus-basics` | 微分・積分の考え | 数学 | 高校 数学Ⅱ | 公開コア | **未着手** |
| `hs-math-ii-exponential-logarithm` | 指数関数・対数関数 | 数学 | 高校 数学Ⅱ | 公開コア | **未着手** |
| `hs-math-ii-figures-and-equations` | 図形と方程式 | 数学 | 高校 数学Ⅱ | 公開コア | **未着手** |
| `hs-math-ii-trigonometric-functions` | 三角関数 | 数学 | 高校 数学Ⅱ | 公開コア | **未着手** |
| `hs-math-ii-various-expressions` | いろいろな式 | 数学 | 高校 数学Ⅱ | 公開コア | **未着手** |
| `hs-math-iii-differentiation` | 微分法 | 数学 | 高校 数学Ⅲ | 公開コア | **未着手** |
| `hs-math-iii-integration` | 積分法 | 数学 | 高校 数学Ⅲ | 公開コア | **未着手** |
| `hs-math-iii-limits` | 極限 | 数学 | 高校 数学Ⅲ | 公開コア | **未着手** |
| `hs-sci-biology-basic-cells-common-features--cells-metabolism` | 細胞とエネルギー代謝 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-cells-common-features--common-features` | 生物の共通性と多様性 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-ecosystems-conservation--biodiversity` | 生物多様性 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-ecosystems-conservation--conservation` | 生態系の保全 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-ecosystems-conservation--ecosystem-processes` | 生態系の成り立ちと物質循環 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-genes-dna--dna-structure` | DNAと遺伝情報 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-genes-dna--gene-expression` | 遺伝情報の発現 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-homeostasis--body-fluids` | 体液と循環 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-homeostasis--regulation` | 自律神経・ホルモンと恒常性 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-immunity--adaptive` | 獲得免疫と免疫記憶 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-immunity--disorders` | 免疫と医療・免疫異常 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-immunity--innate` | 自然免疫 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-vegetation-succession--succession` | 遷移とバイオーム | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-biology-basic-vegetation-succession--vegetation` | 植生と環境 | 理科 | 高校 生物基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-acids-and-bases--acids-bases` | 酸・塩基の定義と強弱 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-acids-and-bases--neutralization` | 中和反応と塩 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-acids-and-bases--titration` | 中和滴定 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-atomic-structure-periodic-table--atomic-structure` | 原子の構造 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-atomic-structure-periodic-table--periodic-table` | 周期表と元素の性質 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-chemical-bonds--covalent-bond` | 共有結合と分子 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-chemical-bonds--ionic-bond` | イオンとイオン結合 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-chemical-bonds--metallic-intermolecular` | 金属結合と物質の性質 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-chemistry-opens-world` | 化学が拓く世界 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-composition-of-matter--pure-substances` | 単体と化合物 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-composition-of-matter--separation` | 混合物の分離と精製 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-introduction--chemistry-characteristics` | 化学の特徴 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-introduction--thermal-motion-states` | 熱運動と物質の三態 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-mole-stoichiometry--amount-of-substance` | 物質量と粒子数・質量・気体体積 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-mole-stoichiometry--chemical-equations` | 化学反応式と量的関係 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-mole-stoichiometry--solutions` | 溶液の濃度と調製 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-oxidation-reduction--batteries` | 電池と酸化還元（化学基礎） | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-chemistry-basic-oxidation-reduction--oxidation-number` | 酸化数と酸化還元 | 理科 | 高校 化学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-atmosphere-ocean--atmosphere` | 大気の構造と運動 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-atmosphere-ocean--climate` | 大気・海洋相互作用と気候 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-atmosphere-ocean--ocean` | 海洋の構造と循環 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-earth-environment--global-environment` | 地球環境の科学 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-earth-environment--japan-environment` | 日本の自然環境・恩恵・災害・予測防災 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-earth-history--earth-life-history` | 地球と生命の歴史 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-earth-history--geologic-time` | 地層・化石と地質時代 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-earth-structure--interior` | 地球内部の構造 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-earth-structure--shape-gravity` | 地球の形と大きさ | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-natural-hazards-disaster-prevention--hazard-mechanisms` | 地震・火山・気象災害のしくみ | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-natural-hazards-disaster-prevention--risk-reduction` | 災害リスクの評価と防災 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-plate-tectonics--earthquakes` | 地震の発生と分布 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-plate-tectonics--plates` | プレート運動と地形 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-plate-tectonics--volcanoes` | 火山活動と火成岩 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-universe-solar-system--solar-system-earth-origin` | 太陽系と地球の誕生 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-earth-basic-universe-solar-system--universe-origin` | 宇宙の誕生 | 理科 | 高校 地学基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-electricity--current-circuits` | 電流・電圧・抵抗と回路 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-electricity--electric-energy` | 電気エネルギーと利用 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-energy-utilization` | エネルギーとその利用 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-force-and-motion-laws--falling-motion` | 自由落下・鉛直投射と落下運動 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-force-and-motion-laws--forces-equilibrium` | 力の表し方とつり合い | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-force-and-motion-laws--laws-motion` | 運動の法則 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-motion--acceleration` | 加速度と等加速度直線運動 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-motion--measurement-data` | 物理量の測定・有効数字・データの扱い | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-motion--velocity` | 速度と相対運動 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-physics-opens-world` | 物理学が拓く世界 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-thermal-energy--heat-temperature` | 熱運動・温度・内部エネルギー | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-thermal-energy--thermodynamics-intro` | 熱と仕事・エネルギー保存 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-waves-sound--sound` | 音波と共鳴 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-waves-sound--wave-properties` | 波の表し方と性質 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-work-mechanical-energy--mechanical-energy` | 力学的エネルギー | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-sci-physics-basic-work-mechanical-energy--work-power` | 仕事と仕事率 | 理科 | 高校 物理基礎 | 公開コア | **未着手** |
| `hs-soc-ethics-contemporary-issues` | 現代の諸課題と倫理（生命・環境・情報） | 社会 | 高校 倫理 | 公開コア | **未着手** |
| `hs-soc-ethics-japanese-thought` | 日本思想の展開 | 社会 | 高校 倫理 | 公開コア | **未着手** |
| `hs-soc-ethics-source-thought` | 源流思想（ギリシア思想と宗教） | 社会 | 高校 倫理 | 公開コア | **未着手** |
| `hs-soc-ethics-western-modern-thought` | 西洋近現代思想 | 社会 | 高校 倫理 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-disaster-prevention--hazard-risk-information` | 災害の地域性とリスク情報（ハザードマップ・新旧地形図） | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-disaster-prevention--regional-disaster-planning` | 地域の防災・減災の計画 | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-global-issues--environment-resources-energy` | 地球環境問題と資源・エネルギー問題 | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-global-issues--interrelation-cooperation` | 地球的課題の相互関連と国際協力 | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-global-issues--population-food-housing-urban` | 人口・食料問題と居住・都市問題 | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-life-culture-diversity--globalization-culture-change` | グローバル化と生活文化の変容 | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-life-culture-diversity--nature-society-culture` | 自然・社会環境と生活文化（宗教・言語を含む） | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-map-gis-literacy` | 地図・GIS活用スパイラルモジュール | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_comprehensive-region-future` | 生活圏の調査と地域の展望 | 社会 | 高校 地理総合 | 公開コア | **未着手** |
| `hs-soc-geography_inquiry-regional-geography` | 地誌（世界の諸地域） | 社会 | 高校 地理探究 | 公開コア | **未着手** |
| `hs-soc-geography_inquiry-systematic-human` | 系統地理（産業・人口・都市） | 社会 | 高校 地理探究 | 公開コア | **未着手** |
| `hs-soc-geography_inquiry-systematic-physical` | 系統地理（自然環境） | 社会 | 高校 地理探究 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-globalization--cold-war-transformation` | 冷戦の展開と終結 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-globalization--economic-globalization-contemporary` | 経済のグローバル化と現代的課題の歴史的形成 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-history-door` | 歴史の扉（歴史と私たち・歴史の特質と資料） | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-mass-society--depression-wwii` | 経済危機とファシズム・第二次世界大戦 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-mass-society--postwar-decolonization` | 戦後国際秩序と脱植民地化 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-mass-society--wwi-mass-society` | 第一次世界大戦と大衆社会 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-modernization--asia-and-opening` | 18世紀のアジアと結び付く世界・日本の開国 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-modernization--modernization-questions` | 近代化への問い（資料から問いを立てる） | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-history_comprehensive-modernization--nation-state-industrialization-imperialism` | 国民国家の形成と産業化・帝国主義 | 社会 | 高校 歴史総合 | 公開コア | **未着手** |
| `hs-soc-japanese_history_inquiry-ancient` | 原始・古代の日本 | 社会 | 高校 日本史探究 | 公開コア | **未着手** |
| `hs-soc-japanese_history_inquiry-early-modern` | 近世の日本 | 社会 | 高校 日本史探究 | 公開コア | **未着手** |
| `hs-soc-japanese_history_inquiry-medieval` | 中世の日本 | 社会 | 高校 日本史探究 | 公開コア | **未着手** |
| `hs-soc-japanese_history_inquiry-modern-contemporary` | 近現代の日本 | 社会 | 高校 日本史探究 | 公開コア | **未着手** |
| `hs-soc-politics_economics-constitution-governance` | 憲法と統治機構の構造整理 | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-politics_economics-fiscal-monetary` | 財政と金融 | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-politics_economics-international-economy` | 国際経済の動向と課題 | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-politics_economics-international-politics` | 国際政治の動向と課題 | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-politics_economics-labor-social-security` | 労働と社会保障 | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-politics_economics-market-national-income` | 現代経済のしくみ（市場機構と国民所得） | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-politics_economics-political-participation` | 現代日本の政治（選挙・政党・世論） | 社会 | 高校 政治・経済 | 公開コア | **未着手** |
| `hs-soc-public-conflict-consensus` | 対立・合意・効率・公正の思考ツールモジュール | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-democracy-participation--elections-media-participation` | 選挙・政治参加と世論・メディア | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-democracy-participation--governance-local-autonomy` | 民主政治の仕組みと地方自治 | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-economy-and-society--fiscal-social-security` | 財政・租税と社会保障 | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-economy-and-society--labor-work` | 労働と職業生活 | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-economy-and-society--market-finance` | 市場経済と企業・貨幣・金融 | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-foundational-principles` | 公共的な空間における基本的原理（幸福・正義・公正） | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-international-cooperation--global-economy-cooperation` | 国際経済と地球規模課題の国際協力 | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-international-cooperation--order-security` | 国際秩序と主権・安全保障 | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-law-and-life--contracts-consumers-law` | 契約・消費者と法の働き（法や規範の意義を含む） | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-law-and-life--judiciary-participation` | 司法制度と市民の司法参加（裁判員制度） | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-self-and-society` | 公共的な空間をつくる私たち（青年期と先人の思想） | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-public-sustainable-capstone` | 持続可能な社会づくりの主体となる私たち（まとめ探究） | 社会 | 高校 公共 | 公開コア | **未着手** |
| `hs-soc-world_history_inquiry-contemporary-world` | 地球世界の課題 | 社会 | 高校 世界史探究 | 公開コア | **未着手** |
| `hs-soc-world_history_inquiry-interregional-exchange` | 諸地域の交流・再編 | 社会 | 高校 世界史探究 | 公開コア | **未着手** |
| `hs-soc-world_history_inquiry-modern-integration` | 諸地域の結合・変容 | 社会 | 高校 世界史探究 | 公開コア | **未着手** |
| `hs-soc-world_history_inquiry-regional-characteristics` | 諸地域の歴史的特質の形成 | 社会 | 高校 世界史探究 | 公開コア | **未着手** |
| `jhs-eng-1-abilities-and-requests--can` | できることを伝える（can） | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-abilities-and-requests--imperatives` | 指示・依頼を伝える（命令文・Please） | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-actions-in-progress` | 今していることを伝える（現在進行形） | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-be-and-do-verbs--be` | be動詞で人・ものの状態を伝える | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-be-and-do-verbs--contrast` | be動詞と一般動詞を使い分ける | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-be-and-do-verbs--general-verbs` | 一般動詞で習慣・好みを伝える | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-describing-places` | 場所とあり方を伝える（There is/are・前置詞） | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-1-introducing-yourself-and-others` | 自分と身近な人を紹介する（三単現含む） | 英語 | 中1 | 公開コア | **外部レビュー済** |
| `jhs-eng-1-questions-and-responses` | 疑問文と応答のやり取り | 英語 | 中1 | 公開コア | **未着手** |
| `jhs-eng-2-comparing-things` | 比較して伝える | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-conditions-and-connections--if-when` | 条件・時を表す接続詞 if / when | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-conditions-and-connections--that` | 考え・事実をつなぐ that節 | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-obligations-and-advice` | 義務と助言を伝える（must・have to・should） | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-plans-and-intentions` | 予定と意志を伝える（未来表現・不定詞） | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-purposes-and-preferences--preferences` | 好み・活動を表す動名詞と不定詞 | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-purposes-and-preferences--purpose` | 目的を表す不定詞 | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-telling-past-events` | 過去の出来事を語る | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-2-writing-letters-and-emails` | 手紙・メールで近況を伝える | 英語 | 中2 | 公開コア | **未着手** |
| `jhs-eng-3-describing-with-passive` | 受け身で出来事を描写する（受動態） | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-experience-and-duration--completion-result` | 完了・結果を語る現在完了 | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-experience-and-duration--continuation` | 継続を語る現在完了・現在完了進行形 | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-experience-and-duration--experience` | 経験を語る現在完了 | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-reading-longer-texts` | まとまった文章を読む方略 | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-relative-clauses-enrichment--postmodification` | 後置修飾で説明を加える | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-relative-clauses-enrichment--pronouns` | 関係代名詞で人・ものを説明する | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-structured-speech` | まとまりのあるスピーチをする（発表） | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-3-wishes-and-hypotheticals` | 願望と仮定を語る（仮定法の基礎） | 英語 | 中3 | 公開コア | **未着手** |
| `jhs-eng-listening-comprehension` | 聞いて捉える（日常・社会的話題の聴解） | 英語 | 中学共通 | 公開コア | **未着手** |
| `jhs-eng-sentence-patterns` | 文型を広げる（SVC・SVOO・SVOC・基本文型の残差整理） | 英語 | 中学共通 | 公開コア | **未着手** |
| `jhs-jpn-1-bun-no-seibun--auxiliaries-particles` | 助詞・助動詞の働き | 国語 | 中学 全学年 | 公開コア | **未着手** |
| `jhs-jpn-1-bun-no-seibun--sentence-components` | 文の成分と文節の関係 | 国語 | 中学 全学年 | 公開コア | **未着手** |
| `jhs-jpn-1-bun-no-seibun--words-parts-of-speech` | 単語の分類と自立語・付属語 | 国語 | 中学 全学年 | 公開コア | **未着手** |
| `jhs-jpn-1-bungaku-bamen-jinbutsu` | 文学的文章の基礎読解：場面分けと登場人物の把握 | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-1-jouhou-hikaku-bunrui` | 情報の扱い方入門：比較・分類と引用の基礎 | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-1-kiroku-houkokubun` | 記録文・報告文の基礎：事実を順序立てて書く | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-1-rekishiteki-kanazukai` | 古典入門：歴史的仮名遣いと古文の読み方 | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-1-setsumei-kouzou` | 説明的文章の構造読解 | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-1-shosha` | 中1書写：楷書の字形・大きさ・配列と行書の基礎 | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-1-shoukai-speech` | 紹介スピーチと聞き方の基礎 | 国語 | 中1 | 公開コア | **未着手** |
| `jhs-jpn-2-explanatory-comparison` | 複数の説明的文章を比較して評価する | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-2-ikenbun` | 根拠を示して書く意見文 | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-2-kanbun-kundoku` | 漢文入門：訓読のしくみ | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-2-kikitori-memo` | 聞き取りとメモ：要点把握・質問づくり | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-2-kobun-dokkai-kiso` | 古文読解の基礎：係り結びと古語の意味 | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-2-shinjou-dokkai` | 文学的文章の心情読解 | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-2-shosha` | 中2書写：行書と仮名の調和・楷書行書の使い分け | 国語 | 中2 | 公開コア | **未着手** |
| `jhs-jpn-3-critical-argument-reading` | 論説を批判的に読み、根拠を吟味する | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-hanashiai-speech--discussion` | 論点を整理して話し合う | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-hanashiai-speech--speech` | 構成と表現を工夫してスピーチする | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-jouken-sakubun` | 条件作文：資料を踏まえて条件に沿って書く | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-keigo-unyou` | 敬語の運用：尊敬・謙譲・丁寧と場面判断 | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-literary-expression-evaluation` | 文学的文章の表現と語りを評価する | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-nyushi-dokkai-integrated` | 中3・入試読解総合：説明文+文学+古文小問のセット演習 | 国語 | 中3 | 公開コア | **調査済** |
| `jhs-jpn-3-shiryou-houkoku` | 資料を統合して報告する | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-3-shosha` | 中3書写：文字文化の豊かさと効果的な文字 | 国語 | 中3 | 公開コア | **未着手** |
| `jhs-jpn-all-kanji-goi-unyou` | 中学・漢字と語彙の運用：同訓異字/熟語の構成/文脈判断 | 国語 | 全学年 | 公開コア | **外部レビュー済** |
| `jhs-math-1-data-distribution--frequency-distribution` | 度数分布表・ヒストグラム・度数折れ線 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-data-distribution--relative-frequency` | 相対度数（D(1)限定） | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-data-distribution--representative-values-range` | 代表値と範囲（小6既習の学び直し） | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-empirical-probability` | 不確定な事象の起こりやすさ（頻度確率） | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-letters-and-expressions--calculation` | 一次式の計算 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-letters-and-expressions--representation` | 文字を用いた式の表し方と数量関係（--relationships統合） | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-linear-equations--applications` | 一次方程式の文章題 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-linear-equations--meaning-equivalence` | 方程式と等式の性質 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-linear-equations--solving` | 一次方程式の解法 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-plane-figures--construction-movement` | 基本の作図と図形の移動（作図による条件の表現を含む・--locus-intro統合） | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-plane-figures--sector-circle` | 円・おうぎ形と接線 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-positive-negative-numbers--addition-subtraction` | 正負の数の加法・減法 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-positive-negative-numbers--applications` | 正負の数の活用 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-positive-negative-numbers--meaning-order` | 正負の数の意味・大小・絶対値 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-positive-negative-numbers--multiplication-division-powers` | 正負の数の乗法・除法と累乗 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-proportion-inverse-proportion--applications` | 比例・反比例の活用 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-proportion-inverse-proportion--inverse-proportion` | 反比例の関係とグラフ | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-proportion-inverse-proportion--proportion` | 比例の関係とグラフ | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-solid-figures--surface-area-volume` | 柱体・錐体・球の表面積と体積 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-1-solid-figures--views-sections` | 空間図形の見取図・投影図・切断 | 数学 | 中1 | 公開コア | **人間レビュー済** |
| `jhs-math-2-congruence-and-proof--isosceles-parallelogram` | 二等辺三角形・平行四辺形の性質と証明 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-congruence-and-proof--proof` | 証明のしくみと書き方 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-congruence-and-proof--triangle-congruence` | 三角形の合同条件と基本性質 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-expression-calculation--polynomial-calculation` | 単項式・多項式の計算 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-expression-calculation--proof-by-expression` | 文字式による説明 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-linear-function` | 一次関数 | 数学 | 中2 | 公開コア | **外部レビュー済** |
| `jhs-math-2-probability` | 確率 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-quartiles-boxplot` | 四分位範囲と箱ひげ図 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-2-simultaneous-equations` | 連立方程式 | 数学 | 中2 | 公開コア | **人間レビュー済** |
| `jhs-math-3-expansion-factorization` | 展開と因数分解 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-function-y-ax2` | 関数 y=ax² | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-inscribed-angle` | 円周角の定理 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-pythagorean-theorem` | 三平方の定理 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-quadratic-equations` | 二次方程式 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-sampling-survey` | 標本調査 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-similar-figures` | 相似な図形 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-math-3-square-roots` | 平方根 | 数学 | 中3 | 公開コア | **外部レビュー済** |
| `jhs-sci-1-animal-classification` | 動物の分類 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-aqueous-solutions--concentration` | 水溶液の濃度 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-aqueous-solutions--solubility` | 溶解と溶解度 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-earth-benefits-hazards` | 自然の恵みと火山・地震災害 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-earthquakes--earthquake-waves` | 地震の揺れと地震波 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-earthquakes--earthquakes-land` | 地震による大地の変化 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-force-basics` | 力のはたらき | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-gas-generation-properties` | 気体の発生と性質 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-light-and-sound--light` | 光の反射・屈折と像 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-light-and-sound--sound` | 音の発生・伝わり方と性質 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-observation-classification--classification-methods` | 生物を分類する観点と方法 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-observation-classification--observation-skills` | 生物観察の基本技能 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-plant-classification` | 植物の分類 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-properties-of-matter--plastics-metals` | 金属・非金属・プラスチックの性質 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-properties-of-matter--properties-identification` | 物質の性質と見分け方 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-states-of-matter--melting-boiling` | 融点・沸点と蒸留 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-states-of-matter--state-changes` | 物質の状態変化と粒子モデル | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-strata-sedimentary-rocks--landforms-introduction` | 身近な地形・地層・岩石と土地の広がり | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-strata-sedimentary-rocks--sedimentary-rocks` | 堆積岩と地層の観察 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-strata-sedimentary-rocks--strata-formation` | 地層のでき方と地層から分かること | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-volcanoes-igneous-rocks--igneous-rocks` | 火成岩のつくりと分類 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-1-volcanoes-igneous-rocks--volcanoes` | 火山活動と噴出物 | 理科 | 中1 | 公開コア | **未着手** |
| `jhs-sci-2-animal-body-functions--digestion-absorption` | 消化と吸収 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-animal-body-functions--excretion-regulation` | 排出とからだの調節 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-animal-body-functions--respiration-circulation` | 呼吸と血液循環 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-animal-body-functions--stimulus-response` | 刺激と反応・神経系 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-atmospheric-movement-japan-weather--air-masses-fronts` | 気団・前線と天気の変化 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-atmospheric-movement-japan-weather--japan-seasons` | 日本の季節の天気 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-atmospheric-movement-japan-weather--pressure-wind` | 気圧配置と風 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-atoms-molecules-decomposition--atoms-molecules` | 原子・分子と化学式 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-atoms-molecules-decomposition--decomposition` | 物質の分解 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-cells` | 生物と細胞 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--combination` | 化合と化学反応式 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--oxidation` | 酸化と燃焼 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--reaction-heat` | 化学変化と熱 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--reduction` | 還元 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-current-and-magnetic-fields--electromagnetic-induction` | 電磁誘導と発電 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-current-and-magnetic-fields--force-on-current` | 磁界中の電流が受ける力 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-current-and-magnetic-fields--magnetic-field-current` | 電流がつくる磁界 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-electric-circuits--current-voltage` | 回路の電流と電圧 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-electric-circuits--power-energy` | 電力と電力量・発熱 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-electric-circuits--resistance-ohm` | 電気抵抗とオームの法則 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-humidity-calculation` | 湿度と飽和水蒸気量の計算 | 理科 | 中2 | 公開コア | **外部レビュー済** |
| `jhs-sci-2-mass-conservation-ratio` | 化学変化と物質の質量 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-plant-body-functions--photosynthesis` | 光合成と葉のつくり | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-plant-body-functions--respiration` | 植物の呼吸 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-plant-body-functions--transport-transpiration` | 水・養分の移動と蒸散 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-static-electricity-current` | 静電気と電流の正体 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-weather-benefits-hazards` | 自然の恵みと気象災害 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-weather-observation--fog-clouds-humidity` | 霧・雲の発生と湿度 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-weather-observation--weather-changes` | 気象データから天気の変化を読む | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-2-weather-observation--weather-elements` | 気象要素の観測と記録 | 理科 | 中2 | 公開コア | **未着手** |
| `jhs-sci-3-acids-bases-neutralization` | 酸・アルカリと中和 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-biodiversity-evolution` | 生物の多様性と進化 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-celestial-motion--annual-motion` | 太陽・星の年周運動と地球の公転 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-celestial-motion--daily-motion` | 天体の日周運動と地球の自転 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-celestial-motion--moon-venus` | 月と金星の見え方 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-chemical-batteries` | 化学変化と電池 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-ecosystems--food-webs` | 食物連鎖・食物網と生物間関係 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-ecosystems--material-cycles-balance` | 物質循環と生態系のつり合い | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-environment-science-technology--environment-conservation` | 自然環境の調査と保全 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-environment-science-technology--science-technology-society` | 自然環境の保全と科学技術の利用 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-forces-pressure-buoyancy--buoyancy` | 浮力 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-forces-pressure-buoyancy--force-composition` | 力の合成・分解 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-forces-pressure-buoyancy--water-pressure` | 水圧 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-growth-reproduction--cell-division-growth` | 細胞分裂と生物の成長 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-growth-reproduction--reproduction` | 生物の生殖 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-heredity-genes--genes` | 遺伝子と形質 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-heredity-genes--heredity-rules` | 遺伝の規則性 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-ions` | 水溶液とイオン | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-motion--force-motion` | 力と運動の関係 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-motion--motion-measurement` | 運動の記録・速さ・向き | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-nature-and-humans--regional-natural-disasters` | 地域の自然災害を資料から科学的に考察する | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-science-technology-humans--energy-resources` | エネルギーとエネルギー資源 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-science-technology-humans--materials-utilization` | 様々な物質とその利用 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-science-technology-humans--technology-development` | 科学技術の発展 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-solar-system-stars--solar-system` | 太陽系の構成と惑星 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-solar-system-stars--sun-stars` | 太陽・恒星と宇宙 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-work-and-energy--energy-transformations` | エネルギーの変換と保存 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-work-and-energy--mechanical-energy` | 力学的エネルギーとその保存 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-sci-3-work-and-energy--work-power` | 仕事と仕事率 | 理科 | 中3 | 公開コア | **未着手** |
| `jhs-soc-civics-banking-finance` | 金融のしくみ | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-better-society` | よりよい社会を目指して（社会科のまとめ探究） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-constitution-principles` | 日本国憲法の基本原理 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-consumer-life` | 消費生活と経済（家計・消費者の権利） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-democracy-election-data--democracy-principles` | 民主主義の基本原理（多数決と少数意見の尊重） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-democracy-election-data--elections-participation` | 選挙のしくみと政治参加・政治データ読解 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-diet-cabinet-courts--cabinet` | 内閣と行政 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-diet-cabinet-courts--courts` | 裁判所と司法 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-diet-cabinet-courts--diet` | 国会のしくみと立法 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-global-issues` | 地球規模の課題（環境・資源・貧困） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-human-rights` | 基本的人権の尊重 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-international-society` | 国際社会のしくみ（主権国家・国際連合） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-local-government` | 地方自治のしくみ | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-market-price` | 市場経済と価格のはたらき | 社会 | 中学 公民 | 公開コア | **外部レビュー済** |
| `jhs-soc-civics-modern-society--culture-meaning` | 現代社会における文化の意義・影響と継承（科学・芸術・宗教） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-modern-society--structural-change` | 現代社会の構造変化（少子高齢化・情報化・グローバル化） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-production-labor--firms-production` | 企業・生産と経済活動 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-production-labor--labor` | 労働の権利と働き方 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-public-finance-welfare--public-finance` | 財政と租税 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-public-finance-welfare--social-security` | 社会保障のしくみと課題 | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-civics-social-frameworks` | 現代社会を捉える枠組み（対立と合意・効率と公正） | 社会 | 中学 公民 | 公開コア | **未着手** |
| `jhs-soc-geography-climate-life-reading` | 世界の気候と人々の生活を資料で読み解く | 社会 | 中学 地理 | 公開コア | **調査済** |
| `jhs-soc-geography-japan-industry-energy--agriculture-fisheries` | 日本の農林水産業 | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-industry-energy--manufacturing-commerce-services` | 工業と商業・サービス業（製造業から第3次産業まで拡張） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-industry-energy--resources-energy` | 日本の資源・エネルギー | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-nature--hazards-adaptation` | 日本の自然災害と防災 | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-nature--landforms-climate` | 日本の地形・気候 | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-overview` | 日本の姿（位置・領域・時差・都道府県） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-population` | 日本の地域的特色（人口） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regional-survey` | 地域調査・フィールドワーク方法モジュール | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-chubu` | 日本の諸地域（中部地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-chugoku-shikoku` | 日本の諸地域（中国・四国地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-hokkaido` | 日本の諸地域（北海道地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-kanto` | 日本の諸地域（関東地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-kinki` | 日本の諸地域（近畿地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-kyushu` | 日本の諸地域（九州地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-regions-tohoku` | 日本の諸地域（東北地方） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-japan-transport-communication` | 日本の地域的特色（交通・通信） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-region-vision` | 地域の在り方（身近な地域の課題と構想） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-overview` | 世界の姿（六大陸と三大洋・国々の位置） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-regions-africa` | 世界の諸地域（アフリカ州） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-regions-asia` | 世界の諸地域（アジア州） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-regions-europe` | 世界の諸地域（ヨーロッパ州） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-regions-north-america` | 世界の諸地域（北アメリカ州） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-regions-oceania` | 世界の諸地域（オセアニア州） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-geography-world-regions-south-america` | 世界の諸地域（南アメリカ州） | 社会 | 中学 地理 | 公開コア | **未着手** |
| `jhs-soc-history-ancient-civilizations--ancient-civilizations` | 古代文明の成立 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-ancient-civilizations--human-origins` | 人類の出現と生活の変化 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-ancient-civilizations--religions-empires` | 宗教・帝国と古代世界 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-bakumatsu-meiji-restoration--opening-bakumatsu` | 開国と幕末の動乱 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-bakumatsu-meiji-restoration--restoration-civilization` | 明治維新と文明開化 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-contemporary-japan--high-growth` | 高度経済成長と社会変化 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-contemporary-japan--post-growth-internationalization` | 石油危機後の日本と国際化 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-depression-wwii--depression-fascism-road` | 世界恐慌・ファシズムと戦争への道 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-depression-wwii--total-war-devastation` | 総力戦・戦時社会と戦争の惨禍 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-edo-bakuhan-system--foreign-relations` | 江戸初期の対外政策と四つの窓口 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-edo-bakuhan-system--formation` | 江戸幕府の成立と大名統制 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-edo-bakuhan-system--society-status` | 身分制と村・町の社会 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-edo-industry-culture` | 産業の発達と町人文化（江戸時代の社会） | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-edo-reforms` | 幕府政治の改革 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-european-contact-unification` | ヨーロッパ人の来航と全国統一 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-heian-court-culture` | 貴族の政治と国風文化（平安時代） | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-jomon-yayoi-kofun` | 日本列島の成り立ちと国家の形成（縄文〜古墳） | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-kamakura-warrior-government--formation` | 鎌倉幕府の成立 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-kamakura-warrior-government--mongol-invasions` | 元寇と幕府の衰退 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-kamakura-warrior-government--rule-society` | 鎌倉幕府の政治と社会 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-local-history` | 身近な地域の歴史（地域史の調べ方） | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-meiji-constitutional-state--rights-constitution` | 自由民権運動と立憲国家の成立 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-meiji-constitutional-state--wars-treaties-imperialism` | 日清・日露戦争と条約改正・帝国主義 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-modern-industry-culture` | 近代産業の発展と近代文化の形成 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-modern-revolutions--citizen-revolutions-nation-states` | 市民革命と国民国家 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-modern-revolutions--industrial-revolution-capitalism` | 産業革命と資本主義 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-muromachi-society--popular-growth` | 民衆の成長と産業・文化 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-muromachi-society--shogunate` | 室町幕府と東アジア | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-muromachi-society--warring-states` | 戦国大名と社会変化 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-periodization-timeline` | 時代区分・年表・年代計算モジュール | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-postwar-reconstruction` | 戦後日本の民主化と国際社会への復帰 | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-ritsuryo-state` | 律令国家の成立（飛鳥・奈良時代） | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-summary-inquiry` | 歴史のまとめ（歴史と私たち・未来への構想） | 社会 | 中学 歴史 | 公開コア | **未着手** |
| `jhs-soc-history-taisho-wwi` | 第一次世界大戦と大正デモクラシー | 社会 | 中学 歴史 | 公開コア | **未着手** |

## 科目モジュール（単元と別枠: 診断・巻末資料）

| module_id | 名称 | 科目 | 学校段階・学年 | 状態 |
|---|---|---|---|---|
| `hs-eng-entry-diagnostic` | 高校英語・学び直し入口診断 | 英語 | 高校 | **未着手** |
| `hs-eng-exam-reading-strategies` | 受験長文の設問方略 | 英語 | 高3 | **未着手** |
| `hs-eng-module-listening-notetaking` | 高校英語・聴解とノートテイキング | 英語 | 高校 | **未着手** |
| `hs-eng-module-speaking-interaction` | 高校英語・対話運用モジュール | 英語 | 高校 | **未着手** |
| `hs-jpn-entry-diagnostic` | 高校国語・学び直し入口診断 | 国語 | 高校 | **未着手** |
| `hs-soc-entry-diagnostic` | 高校社会・学び直し入口診断 | 社会 | 高校 | **未着手** |
| `hs-soc-history_comprehensive-turning-points` | 歴史総合・複数資料統合アセスメント | 社会 | 高校 歴史総合 | **未着手** |
| `hs-soc-japanese_history_inquiry-essay-frame` | 歴史論述・因果説明スパイラルモジュール | 社会 | 高校 日本史探究 | **未着手** |
| `jhs-eng-entry-diagnostic` | 中学英語・学び直し入口診断 | 英語 | 中学 | **未着手** |
| `jhs-eng-module-spoken-interaction` | 中学英語・やり取り方略モジュール | 英語 | 中学 | **未着手** |
| `jhs-eng-module-writing-process` | 中学英語・ライティング過程モジュール | 英語 | 中学 | **未着手** |
| `jhs-jpn-entry-diagnostic` | 中学国語・学び直し入口診断 | 国語 | 中学 | **未着手** |
| `jhs-math-3-appendix` | 中3数学 巻末資料 | 数学 | 中3 | **ドラフト** |
| `jhs-math-3-diagnostic` | 中3数学 科目診断 | 数学 | 中3 | **QA済** |
| `jhs-math-entry-diagnostic` | 中学数学・学び直し入口診断 | 数学 | 中学 | **未着手** |
| `jhs-soc-entry-diagnostic` | 中学社会・学び直し入口診断 | 社会 | 中学 | **未着手** |
| `jhs-soc-history-modernization-causality` | 歴史因果説明スパイラルモジュール | 社会 | 中学 歴史 | **未着手** |
| `jhs-soc-history-source-inference` | 史料読解・時代推論スパイラルモジュール | 社会 | 中学 歴史 | **未着手** |
| `lane-eng-dictionary-and-reference-skills` | 辞書・参照スキルモジュール | 英語 | 中高共通 | **未着手** |
| `lane-eng-entrance-exam-writing-strategies` | 入試英作文の型（和文英訳・自由英作文） | 英語 | 中高共通 | **未着手** |
| `lane-eng-listening-training` | リスニング訓練システム（ディクテーション等） | 英語 | 中高共通 | **未着手** |
| `lane-eng-native-teacher-conversation` | 外国人講師との会話活動の設計 | 英語 | 中高共通 | **未着手** |
| `lane-eng-sound-and-spelling` | 音と綴り（発音・音読・シャドーイング） | 英語 | 中高共通 | **未着手** |
| `lane-eng-vocabulary-system` | 語彙学習システム | 英語 | 中高共通 | **未着手** |
| `lane-jpn-entrance-jouken-sakubun-kata` | 高校入試・条件作文の型（補完モジュール） | 国語 | 中3 | **未着手** |
| `lane-jpn-entrance-koten-shoumon` | 入試古典小問系統：仮名遣い・古語・文法・句形（補完モジュール） | 国語 | 中3〜高校 | **未着手** |
| `lane-jpn-entrance-mensetsu-koutou-shimon` | 面接・口頭試問の型：話す・応答の系統（補完モジュール） | 国語 | 中3〜高校 | **未着手** |
| `lane-jpn-entrance-modern-multitext` | 共通テスト型現代文：複数テクスト・図表つき実用文の統合読解（補完モジュール） | 国語 | 高校 | **未着手** |
| `lane-soc-causal-comparison` | 社会・因果説明と比較 | 社会 | 中高共通 | **未着手** |
| `lane-soc-entrance-civics-source-quant` | 入試公民・資料と数量の読解（時事資料・経済計算の型） | 社会 | 中高共通 | **未着手** |
| `lane-soc-entrance-geography-multisource-analysis` | 入試地理・複数資料の統合分析（地形図・統計地図） | 社会 | 中高共通 | **未着手** |
| `lane-soc-maps-data` | 社会・地図・統計・図表リテラシー | 社会 | 中高共通 | **未着手** |
| `lane-soc-multiperspective-argument` | 社会・多面的・多角的な論証 | 社会 | 中高共通 | **未着手** |
| `lane-soc-source-criticism` | 社会・史資料の批判的読解 | 社会 | 中高共通 | **未着手** |
| `module-jpn-common-dokusho` | 読書・学校図書館活用モジュール（中高横断） | 国語 | 中高共通 | **未着手** |
| `module-jpn-common-editing` | 推敲と編集モジュール（中高共通） | 国語 | 中高共通 | **未着手** |
| `module-jpn-common-gengo-no-hataraki` | 言葉の働き・話し言葉と書き言葉モジュール（中高横断） | 国語 | 中高共通 | **未着手** |
| `module-jpn-common-onsei-hougen` | 音声の働き・共通語と方言モジュール（中高横断） | 国語 | 中高共通 | **未着手** |
| `module-jpn-hs-kanji` | 高校漢字・語彙運用モジュール：常用漢字と実社会の語彙（埋込型限定） | 国語 | 高校 | **未着手** |
| `module-jpn-jhs-sousaku` | 創作表現モジュール：詩・短歌俳句・物語を書く（任意） | 国語 | 中学 | **未着手** |

## 既知の限界（正直に残す）

- 理科は教科カーネル（単元一覧の元表）を正本とし、一覧をカーネル準拠へ改訂済み（学習指導要領解説との逐条照合・別ベンダAIとの相互検証・機械検査を通過）。今後も単元の統廃合（分割・統合・名称変更）がありうる。
- この一覧はレジストリの記載を集計したもの。教材本体との突き合わせは各単元のレビュー工程で行う。

[⬆ ページの最上部へ戻る](#manabigrid-進捗一覧自動生成)
