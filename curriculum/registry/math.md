# 単元レジストリ: 数学

単元の全量と現在の状態の一覧（数学）。状態は次の7語のみを使う:
未着手 / 調査済 / ドラフト / QA済 / 外部レビュー済 / 人間レビュー済 / 公開済。
このファイルは `tools/progress_index/build_progress_index.py` が読み取り、
`curriculum/PROGRESS_INDEX.md` に集計される。

> **注記（全量性について）**: 中学（中1〜中3）は全単元、高校は数学Ⅰ・A・Ⅱ・B・Ⅲ・Cの主要単元を収録している。
> 単元の切り方は本プロジェクトの編集判断であり、教科書の章立てとは異なる場合がある。

> **注記（正直な開示・カーネル第2版化について）**: 数学でも理科と同様に、教科カーネル（単元一覧の元表）を正本とし、
> 学習指導要領解説との逐条照合と単元粒度の再設計（カーネル第2版化）を実施のうえ、
> 中学と数学Ⅰをカーネル準拠へ**改訂済み**である。
> 既存の単元IDは意味を保ったまま維持し、学習単位を `親ID--子` 形式の子単元へ分割している（理科と同じ意味継承方式）。
> 進捗は子単元（および分割していない単元）のみで数え、親ノードは集計に含めない（二重計上防止）。
> 制作済み教材の原本は親単位のまま保全し、分割済みの子は親成果物のレッスン範囲を参照する（該当子の備考に明記）。
> 数学Ⅱ・Ⅲ・A・B・Cは第1版のまま（照合・分割は未実施。着手時に同方式で改訂予定）。
> 入試演習・領域横断テーマの単元化は今後の改訂で扱う。
> 単元総数は **65単元**（中1 20・中2 9・中3 8・数Ⅰ 11・数A〜C 17）＋親ノード13＋モジュール3。
> 今後も単元の統廃合（分割・統合・名称変更）がありうる。一覧への追加提案も歓迎（Issueで）。

## 公開コア（public_core）— 中学・数学Ⅰ（カーネル第2版）

| unit_id | 単元名 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-math-1-positive-negative-numbers--addition-subtraction` | 正負の数の加法・減法 | 中1 | 未着手 |  |
| `jhs-math-1-positive-negative-numbers--applications` | 正負の数の活用 | 中1 | 未着手 |  |
| `jhs-math-1-positive-negative-numbers--meaning-order` | 正負の数の意味・大小・絶対値 | 中1 | 未着手 |  |
| `jhs-math-1-positive-negative-numbers--multiplication-division-powers` | 正負の数の乗法・除法と累乗 | 中1 | 未着手 |  |
| `jhs-math-1-letters-and-expressions--calculation` | 一次式の計算 | 中1 | 未着手 |  |
| `jhs-math-1-letters-and-expressions--representation` | 文字を用いた式の表し方と数量関係（--relationships統合） | 中1 | 未着手 |  |
| `jhs-math-1-linear-equations--applications` | 一次方程式の文章題 | 中1 | 未着手 |  |
| `jhs-math-1-linear-equations--meaning-equivalence` | 方程式と等式の性質 | 中1 | 未着手 |  |
| `jhs-math-1-linear-equations--solving` | 一次方程式の解法 | 中1 | 未着手 |  |
| `jhs-math-1-proportion-inverse-proportion--applications` | 比例・反比例の活用 | 中1 | 未着手 |  |
| `jhs-math-1-proportion-inverse-proportion--inverse-proportion` | 反比例の関係とグラフ | 中1 | 未着手 |  |
| `jhs-math-1-proportion-inverse-proportion--proportion` | 比例の関係とグラフ | 中1 | 未着手 |  |
| `jhs-math-1-plane-figures--construction-movement` | 基本の作図と図形の移動（作図による条件の表現を含む・--locus-intro統合） | 中1 | 未着手 |  |
| `jhs-math-1-plane-figures--sector-circle` | 円・おうぎ形と接線 | 中1 | 未着手 |  |
| `jhs-math-1-solid-figures--surface-area-volume` | 柱体・錐体・球の表面積と体積 | 中1 | 未着手 |  |
| `jhs-math-1-solid-figures--views-sections` | 空間図形の見取図・投影図・切断 | 中1 | 未着手 |  |
| `jhs-math-1-data-distribution--frequency-distribution` | 度数分布表・ヒストグラム・度数折れ線 | 中1 | 未着手 |  |
| `jhs-math-1-data-distribution--relative-frequency` | 相対度数（D(1)限定） | 中1 | 未着手 |  |
| `jhs-math-1-data-distribution--representative-values-range` | 代表値と範囲（小6既習の学び直し） | 中1 | 未着手 |  |
| `jhs-math-1-empirical-probability` | 不確定な事象の起こりやすさ（頻度確率） | 中1 | 未着手 | 新設（中1D(2)の独立単元化） |
| `jhs-math-2-expression-calculation--polynomial-calculation` | 単項式・多項式の計算 | 中2 | ドラフト | 親成果物（10レッスン）参照・要差分QA |
| `jhs-math-2-expression-calculation--proof-by-expression` | 文字式による説明 | 中2 | ドラフト | 親成果物（10レッスン）参照・要差分QA |
| `jhs-math-2-simultaneous-equations` | 連立方程式 | 中2 | ドラフト |  |
| `jhs-math-2-linear-function` | 一次関数 | 中2 | QA済 |  |
| `jhs-math-2-congruence-and-proof--isosceles-parallelogram` | 二等辺三角形・平行四辺形の性質と証明 | 中2 | ドラフト | 親成果物（16レッスン）参照・要差分QA |
| `jhs-math-2-congruence-and-proof--proof` | 証明のしくみと書き方 | 中2 | ドラフト | 親成果物（16レッスン）参照・要差分QA |
| `jhs-math-2-congruence-and-proof--triangle-congruence` | 三角形の合同条件と基本性質 | 中2 | ドラフト | 親成果物（16レッスン）参照・要差分QA |
| `jhs-math-2-quartiles-boxplot` | 四分位範囲と箱ひげ図 | 中2 | ドラフト |  |
| `jhs-math-2-probability` | 確率 | 中2 | ドラフト | レッスン数が推奨粒度を超えるため将来の分割候補（例外として現行維持） |
| `jhs-math-3-expansion-factorization` | 展開と因数分解 | 中3 | 外部レビュー済 | 将来の分割候補（粒度の見直し予定） |
| `jhs-math-3-square-roots` | 平方根 | 中3 | 外部レビュー済 | 将来の分割候補（粒度の見直し予定） |
| `jhs-math-3-quadratic-equations` | 二次方程式 | 中3 | 外部レビュー済 | 将来の分割候補（粒度の見直し予定） |
| `jhs-math-3-function-y-ax2` | 関数 y=ax² | 中3 | 外部レビュー済 | 将来の分割候補（粒度の見直し予定） |
| `jhs-math-3-similar-figures` | 相似な図形 | 中3 | 外部レビュー済 | 将来の分割候補（粒度の見直し予定） |
| `jhs-math-3-inscribed-angle` | 円周角の定理 | 中3 | 外部レビュー済 |  |
| `jhs-math-3-pythagorean-theorem` | 三平方の定理 | 中3 | 外部レビュー済 | 将来の分割候補（粒度の見直し予定） |
| `jhs-math-3-sampling-survey` | 標本調査 | 中3 | 外部レビュー済 |  |
| `hs-math-i-numbers-and-expressions--inequalities` | 一次不等式 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-numbers-and-expressions--polynomial-expansion-factorization` | 多項式の展開と因数分解 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-numbers-and-expressions--real-numbers` | 数の体系と実数・根号 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-sets-and-logic` | 集合と命題 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-quadratic-functions--graph-transformations` | 二次関数のグラフと平行移動 | 高校 数学Ⅰ | ドラフト | 親成果物（外部レビュー済12レッスン）参照・要差分QA・外部レビュー再裁定 |
| `hs-math-i-quadratic-functions--max-min` | 二次関数の最大・最小 | 高校 数学Ⅰ | ドラフト | 親成果物（外部レビュー済12レッスン）参照・要差分QA・外部レビュー再裁定 |
| `hs-math-i-quadratic-functions--quadratic-equations-inequalities` | 二次方程式・二次不等式とグラフ | 高校 数学Ⅰ | ドラフト | 親成果物（外部レビュー済12レッスン）参照・要差分QA・外部レビュー再裁定 |
| `hs-math-i-trigonometric-ratios--ratios` | 三角比の定義と相互関係 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-trigonometric-ratios--triangle-measurement` | 正弦定理・余弦定理と三角形の計量 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-data-analysis--description` | データの散らばりと相関 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-data-analysis--inference-intro` | 仮説検定の考え方 | 高校 数学Ⅰ | 未着手 |  |

### 親ノード（進捗集計対象外・進捗は子単元で計上）

分割した既存単元のIDは、親ノードとして意味を保って維持する。制作済み教材の原本は親単位のまま保全する。

| parent_id | 名称 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-math-1-positive-negative-numbers` | 正負の数 | 中1 | 未着手 |  |
| `jhs-math-1-letters-and-expressions` | 文字と式 | 中1 | 未着手 |  |
| `jhs-math-1-linear-equations` | 一次方程式 | 中1 | 未着手 |  |
| `jhs-math-1-proportion-inverse-proportion` | 比例と反比例 | 中1 | 未着手 |  |
| `jhs-math-1-plane-figures` | 平面図形 | 中1 | 未着手 |  |
| `jhs-math-1-solid-figures` | 空間図形 | 中1 | 未着手 |  |
| `jhs-math-1-data-distribution` | データの活用（度数分布・ヒストグラム） | 中1 | 未着手 |  |
| `jhs-math-2-expression-calculation` | 式の計算 | 中2 | ドラフト | 原本教材（10レッスン）を親単位で保全 |
| `jhs-math-2-congruence-and-proof` | 図形の合同と証明 | 中2 | ドラフト | 原本教材（16レッスン）を親単位で保全 |
| `hs-math-i-numbers-and-expressions` | 数と式 | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-quadratic-functions` | 二次関数 | 高校 数学Ⅰ | 外部レビュー済 | 原本教材（12レッスン）を親単位で保全 |
| `hs-math-i-trigonometric-ratios` | 図形と計量（三角比） | 高校 数学Ⅰ | 未着手 |  |
| `hs-math-i-data-analysis` | データの分析 | 高校 数学Ⅰ | 未着手 |  |

## 公開コア（public_core）— 数学A・Ⅱ・B・Ⅲ・C（第1版のまま・現行無変更）

| unit_id | 単元名 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `hs-math-a-counting-and-probability` | 場合の数と確率 | 高校 数学A | 未着手 |  |
| `hs-math-a-geometry-properties` | 図形の性質 | 高校 数学A | 未着手 |  |
| `hs-math-a-math-and-human-activity` | 数学と人間の活動（整数など） | 高校 数学A | 未着手 |  |
| `hs-math-ii-various-expressions` | いろいろな式 | 高校 数学Ⅱ | 未着手 |  |
| `hs-math-ii-figures-and-equations` | 図形と方程式 | 高校 数学Ⅱ | 未着手 |  |
| `hs-math-ii-trigonometric-functions` | 三角関数 | 高校 数学Ⅱ | 未着手 |  |
| `hs-math-ii-exponential-logarithm` | 指数関数・対数関数 | 高校 数学Ⅱ | 未着手 |  |
| `hs-math-ii-calculus-basics` | 微分・積分の考え | 高校 数学Ⅱ | 未着手 |  |
| `hs-math-b-sequences` | 数列 | 高校 数学B | 未着手 |  |
| `hs-math-b-statistical-inference` | 統計的な推測 | 高校 数学B | 未着手 |  |
| `hs-math-b-math-and-social-life` | 数学と社会生活 | 高校 数学B | 未着手 |  |
| `hs-math-iii-limits` | 極限 | 高校 数学Ⅲ | 未着手 |  |
| `hs-math-iii-differentiation` | 微分法 | 高校 数学Ⅲ | 未着手 |  |
| `hs-math-iii-integration` | 積分法 | 高校 数学Ⅲ | 未着手 |  |
| `hs-math-c-vectors` | ベクトル | 高校 数学C | 未着手 |  |
| `hs-math-c-plane-curves-complex-plane` | 平面上の曲線と複素数平面 | 高校 数学C | 未着手 |  |
| `hs-math-c-mathematical-expression-devices` | 数学的な表現の工夫 | 高校 数学C | 未着手 |  |

## 科目モジュール（単元と別枠: 診断・巻末資料）

| module_id | 名称 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-math-3-diagnostic` | 中3数学 科目診断 | 中3 | QA済 | 中3の8単元すべてとの対応関係（どの単元を診断するか）を登記済み |
| `jhs-math-3-appendix` | 中3数学 巻末資料 | 中3 | ドラフト |  |
| `jhs-math-entry-diagnostic` | 中学数学・学び直し入口診断 | 中学 | 未着手 | 新設（実体化前に診断仕様書の作成が必須） |

---

### 改訂の根拠と保全（正直な開示）

- 制作済み単元のID・状態は全件無変更で保全した（中2の6単元・中3の8単元＋科目診断＋巻末資料・数Ⅰ二次関数）。
- 分割済みの子単元の「ドラフト」は親成果物のレッスン範囲参照を意味し、公開前に差分QAを要する（備考に明記）。
- 学習順序（前提関係）は「必須」と「参考」の2階建てで別途設計している。子単元の表内の並びは仮であり、学習順は前提関係に従う。
- 高校の学び直し入口診断は予約枠（数Ⅱ〜C着手時に追加）のため本一覧には載せていない。
