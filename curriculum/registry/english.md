# 単元レジストリ: 英語

単元の全量と現在の状態の一覧（英語）。状態は次の7語のみを使う:
未着手 / 調査済 / ドラフト / QA済 / 外部レビュー済 / 人間レビュー済 / 公開済。
このファイルは `tools/progress_index/build_progress_index.py` が読み取り、
`curriculum/PROGRESS_INDEX.md` に集計される。

> **注記（全量性について）**: 中学（3学年）と高校必履修（英語コミュニケーションⅠ）は学習指導要領解説との
> 逐条照合を完了し、単元の切り方を照合結果にもとづき再設計した。高校選択4科目（英語コミュニケーションⅡ・Ⅲ／
> 論理・表現Ⅰ〜Ⅲ）は科目単位の予約（照合は着手時に実施）だが、対応する単元自体は
> 本一覧に収録している。単元の切り方は本プロジェクトの編集判断。一覧への追加提案も歓迎（Issueで）。

> **注記（正直な開示・カーネル第2版化について）**: 英語でも理科・数学・社会と同様に、教科カーネル（単元一覧の元表）を正本とし、
> 学習指導要領解説との逐条照合と単元粒度の再設計（カーネル第2版化）を実施のうえ、一覧をカーネル準拠へ**改訂済み**である。
> 従来の単元を「親ノード」として**既存IDの意味を保って維持**したまま、
> 学習単位を `親ID--子` 形式の子単元へ分割している（理科と同じ意味継承方式）。
> 進捗は子単元（および分割していない単元）のみで数え、親ノードは集計に含めない（二重計上防止）。
> 制作済み教材（`jhs-eng-1-introducing-yourself-and-others`）はID・名称・状態・成果物ファイルを一切変更せず継承している。
> 単元総数は **48単元**（中学29・高校19。うち分割子20・新設4）＋親ノード9＋共通モジュール8＋入口診断2
> ＋付録1＋私立・入試レーン2（評価パッケージ1・スキルモジュール1）。
> 新設単元4件は実体化条件つき（provisional）であり、条件達成まで進捗の分母に含めない（備考に明記）。
> 今後も単元の統廃合（分割・統合・名称変更）がありうる。

> **注記（学年表示について）**: 中学の言語材料は指導要領上3学年一括の配当であり、学年表示は本プロジェクトの
> 編集判断である。

## 公開コア（public_core）— 中学・高校（カーネル第2版）

| unit_id | 単元名 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-eng-1-abilities-and-requests--can` | できることを伝える（can） | 中1 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-1-abilities-and-requests--imperatives` | 指示・依頼を伝える（命令文・Please） | 中1 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-1-actions-in-progress` | 今していることを伝える（現在進行形） | 中1 | 未着手 |  |
| `jhs-eng-1-be-and-do-verbs--be` | be動詞で人・ものの状態を伝える | 中1 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-1-be-and-do-verbs--contrast` | be動詞と一般動詞を使い分ける | 中1 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-1-be-and-do-verbs--general-verbs` | 一般動詞で習慣・好みを伝える | 中1 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-1-describing-places` | 場所とあり方を伝える（There is/are・前置詞） | 中1 | 未着手 |  |
| `jhs-eng-1-introducing-yourself-and-others` | 自分と身近な人を紹介する（三単現含む） | 中1 | 外部レビュー済 | 制作済み・完全保全（ID・名称・状態・成果物を無変更） |
| `jhs-eng-1-questions-and-responses` | 疑問文と応答のやり取り | 中1 | 未着手 |  |
| `jhs-eng-2-comparing-things` | 比較して伝える | 中2 | 未着手 |  |
| `jhs-eng-2-conditions-and-connections--if-when` | 条件・時を表す接続詞 if / when | 中2 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-2-conditions-and-connections--that` | 考え・事実をつなぐ that節 | 中2 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-2-obligations-and-advice` | 義務と助言を伝える（must・have to・should） | 中2 | 未着手 |  |
| `jhs-eng-2-plans-and-intentions` | 予定と意志を伝える（未来表現・不定詞） | 中2 | 未着手 |  |
| `jhs-eng-2-purposes-and-preferences--preferences` | 好み・活動を表す動名詞と不定詞 | 中2 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-2-purposes-and-preferences--purpose` | 目的を表す不定詞 | 中2 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-2-telling-past-events` | 過去の出来事を語る | 中2 | 未着手 |  |
| `jhs-eng-2-writing-letters-and-emails` | 手紙・メールで近況を伝える | 中2 | 未着手 | 新設（照合で判明した欠落の解消）・provisional（実体化条件あり・進捗分母除外） |
| `jhs-eng-3-describing-with-passive` | 受け身で出来事を描写する（受動態） | 中3 | 未着手 |  |
| `jhs-eng-3-experience-and-duration--completion-result` | 完了・結果を語る現在完了 | 中3 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-3-experience-and-duration--continuation` | 継続を語る現在完了・現在完了進行形 | 中3 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-3-experience-and-duration--experience` | 経験を語る現在完了 | 中3 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-3-reading-longer-texts` | まとまった文章を読む方略 | 中3 | 未着手 |  |
| `jhs-eng-3-relative-clauses-enrichment--postmodification` | 後置修飾で説明を加える | 中3 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-3-relative-clauses-enrichment--pronouns` | 関係代名詞で人・ものを説明する | 中3 | 未着手 | 分割子（親ID--子・意味継承） |
| `jhs-eng-3-structured-speech` | まとまりのあるスピーチをする（発表） | 中3 | 未着手 |  |
| `jhs-eng-3-wishes-and-hypotheticals` | 願望と仮定を語る（仮定法の基礎） | 中3 | 未着手 |  |
| `jhs-eng-listening-comprehension` | 聞いて捉える（日常・社会的話題の聴解） | 中学共通 | 未着手 | 新設（照合で判明した欠落の解消）・provisional（実体化条件あり・進捗分母除外） |
| `jhs-eng-sentence-patterns` | 文型を広げる（SVC・SVOO・SVOC・基本文型の残差整理） | 中学共通 | 未着手 | 新設（照合で判明した欠落の解消）・provisional（実体化条件あり・進捗分母除外） |
| `hs-eng-ec1-detail-and-intent` | 詳細と話者の意図を読み取る | 高校 英語コミュニケーションⅠ | 未着手 |  |
| `hs-eng-ec1-gist-and-presentation--gist` | 概要・要点を把握する | 高1 | 未着手 | 分割子（親ID--子・意味継承） |
| `hs-eng-ec1-gist-and-presentation--presentation` | 把握した内容を整理して発表する | 高1 | 未着手 | 分割子（親ID--子・意味継承） |
| `hs-eng-ec1-structured-discussion` | 読んだ内容をもとに話し合う（ディスカッション入門） | 高校 英語コミュニケーションⅠ | 未着手 |  |
| `hs-eng-ec1-writing-from-input` | 聞き・読みした内容をもとに書く（英コミュⅠの書く受け皿） | 高校 英語コミュニケーションⅠ | 未着手 | 新設（照合で判明した欠落の解消）・provisional（実体化条件あり・進捗分母除外） |
| `hs-eng-ec2-abstract-topics-discussion` | 社会的な話題を読み解き意見を交わす | 高校 英語コミュニケーションⅡ | 未着手 |  |
| `hs-eng-ec2-presentation-with-sources` | 資料を用いた発表（図表・データの読み取りと引用） | 高校 英語コミュニケーションⅡ | 未着手 |  |
| `hs-eng-ec2-summary-and-response--response` | 要約を踏まえて応答する | 高2 | 未着手 | 分割子（親ID--子・意味継承） |
| `hs-eng-ec2-summary-and-response--summary` | 英語で要約する | 高2 | 未着手 | 分割子（親ID--子・意味継承） |
| `hs-eng-ec3-extended-reading` | 長く複雑な文章の読解（多様なジャンル） | 高校 英語コミュニケーションⅢ | 未着手 |  |
| `hs-eng-ec3-integrated-output` | 聞き・読みから統合して発信する（統合的言語活動） | 高校 英語コミュニケーションⅢ | 未着手 |  |
| `hs-eng-le1-grammar-for-expression` | 伝えるための文法再整理（機能から使う文法） | 高校 論理・表現Ⅰ | 未着手 |  |
| `hs-eng-le1-opinion-structure` | 意見文の構成（主張・理由・根拠） | 高1 | 未着手 |  |
| `hs-eng-le1-paragraph-writing` | パラグラフライティング | 高1 | 未着手 |  |
| `hs-eng-le2-argumentative-essay` | 反対意見をふまえた意見文（譲歩と反駁） | 高校 論理・表現Ⅱ | 未着手 |  |
| `hs-eng-le2-debate-discussion--debate` | 立場を分けてディベートする | 高2 | 未着手 | 分割子（親ID--子・意味継承） |
| `hs-eng-le2-debate-discussion--discussion` | 論点を整理して議論する | 高2 | 未着手 | 分割子（親ID--子・意味継承） |
| `hs-eng-le3-essay-revision` | エッセイの推敲プロセス（書き直しの技術） | 高校 論理・表現Ⅲ | 未着手 |  |
| `hs-eng-le3-extended-debate` | 発展的なディベート・ディスカッション（論点整理と合意形成） | 高校 論理・表現Ⅲ | 未着手 |  |

### 親ノード（進捗集計対象外・進捗は子単元で計上）

分割した既存単元のIDは、親ノードとして意味を保って維持する。制作済み教材の原本は該当単元でそのまま保全する。

| parent_id | 名称 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-eng-1-abilities-and-requests` | できること・お願いを伝える（can・命令文） | 中1 | 未着手 |  |
| `jhs-eng-1-be-and-do-verbs` | be動詞と一般動詞の世界の立ち上げ | 中1 | 未着手 |  |
| `jhs-eng-2-conditions-and-connections` | 条件・時・考えをつなぐ（接続詞 if / when / that） | 中2 | 未着手 |  |
| `jhs-eng-2-purposes-and-preferences` | 目的と好みを伝える（不定詞・動名詞） | 中2 | 未着手 |  |
| `jhs-eng-3-experience-and-duration` | 経験と継続を語る（現在完了） | 中3 | 未着手 |  |
| `jhs-eng-3-relative-clauses-enrichment` | 関係詞で説明を厚くする | 中3 | 未着手 |  |
| `hs-eng-ec1-gist-and-presentation` | 概要・要点の把握と発表 | 高1 | 未着手 |  |
| `hs-eng-ec2-summary-and-response` | 要約と応答（サマリーライティング） | 高2 | 未着手 |  |
| `hs-eng-le2-debate-discussion` | ディベートとディスカッション | 高2 | 未着手 |  |

## 共通スキルモジュール・入口診断（単元と別枠）

> 進捗集計の単元数には含めない（単元を横断して適用するモジュール／診断。対象単元との関係は
> applies_to / assesses で管理し、前提（prerequisite）辺は張らない）。入口診断の実体化は
> 診断仕様書の受入合格を唯一の条件とする。

| module_id | 名称 | 学校段階・学年 | 状態 | 区分 |
|---|---|---|---|---|
| `jhs-eng-module-spoken-interaction` | 中学英語・やり取り方略モジュール | 中学 | 未着手 | 共通モジュール（新設・provisional） |
| `jhs-eng-module-writing-process` | 中学英語・ライティング過程モジュール | 中学 | 未着手 | 共通モジュール（新設・provisional） |
| `hs-eng-module-listening-notetaking` | 高校英語・聴解とノートテイキング | 高校 | 未着手 | 共通モジュール（新設・provisional） |
| `hs-eng-module-speaking-interaction` | 高校英語・対話運用モジュール | 高校 | 未着手 | 共通モジュール（新設・provisional） |
| `lane-eng-dictionary-and-reference-skills` | 辞書・参照スキルモジュール | 中高共通 | 未着手 | 共通モジュール（新設・provisional） |
| `lane-eng-listening-training` | リスニング訓練システム（ディクテーション等） | 中高共通 | 未着手 | 共通モジュール（既存レーンの再類型化） |
| `lane-eng-sound-and-spelling` | 音と綴り（発音・音読・シャドーイング） | 中高共通 | 未着手 | 共通モジュール（既存レーンの再類型化） |
| `lane-eng-vocabulary-system` | 語彙学習システム | 中高共通 | 未着手 | 共通モジュール（既存レーンの再類型化） |
| `jhs-eng-entry-diagnostic` | 中学英語・学び直し入口診断 | 中学 | 未着手 | 入口診断（新設・provisional。診断仕様書の受入合格が条件） |
| `hs-eng-entry-diagnostic` | 高校英語・学び直し入口診断 | 高校 | 未着手 | 入口診断（新設・provisional。診断仕様書の受入合格が条件） |

## 公開コア付録（appendix）

> 実施形態に依存する活動テンプレート。内容単元の完了率集計から除外する。

| module_id | 名称 | 学校段階・学年 | 状態 | 区分 |
|---|---|---|---|---|
| `lane-eng-native-teacher-conversation` | 外国人講師との会話活動の設計 | 中高共通 | 未着手 | 付録（activity guide。受験対策でなく実施形態依存の活動ガイドのため、旧・私立・入試レーンから移動） |

## 私立・入試レーン（スキルモジュール・評価パッケージ群）

> 私立・入試レーンは「内容の単元」ではなく、公開コアの単元を素材として
> 横断的に使う「読み方・書き方の型」のスキルモジュール・評価パッケージ群として再構成した。
> 過去問の転載は行わない（入試の「型」の指導であって過去問集ではない）。出題傾向に関する記述は
> `verify_required` タグつきの事実スロット方式とし、時点（as_of）・出典を明記する。
> リスニングは新設せず、既存 `lane-eng-listening-training` が入試向けプロファイル1本を追加して兼務する（条件つき）。
> スピーキング（面接型）は次版の課題として台帳管理している。

| module_id | 名称 | 学校段階・学年 | 状態 | 区分 |
|---|---|---|---|---|
| `hs-eng-exam-reading-strategies` | 受験長文の設問方略 | 高3 | 未着手 | 評価パッケージ（単元から再類型化・対象単元は trains_for で登記） |
| `lane-eng-entrance-exam-writing-strategies` | 入試英作文の型（和文英訳・自由英作文） | 中高共通 | 未着手 | スキルモジュール（新設・provisional。中3への適用は任意） |
