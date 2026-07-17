# 単元レジストリ: 理科

単元の全量と現在の状態の一覧（理科）。状態は次の7語のみを使う:
未着手 / 調査済 / ドラフト / QA済 / 外部レビュー済 / 人間レビュー済 / 公開済。
このファイルは `tools/progress_index/build_progress_index.py` が読み取り、
`curriculum/PROGRESS_INDEX.md` に集計される。

> **注記（正直な開示・全量性について）**: 理科は教科カーネル（単元一覧の元表）を正本とし、
> この一覧をカーネル準拠へ**改訂済み**である
> （学習指導要領解説との逐条照合・別ベンダAIとの相互検証・機械検査を通過したカーネルに基づく）。
> 改訂では、既存の単元IDは意味を保ったまま維持し、内容の分割・追加分は新しいIDとして加えた
> （分割された単元は、元のIDを引き継ぐ子ID `親ID--子` の形で表す）。
> 今後も単元の統廃合（分割・統合・名称変更）がありうる。一覧への追加提案も歓迎（Issueで）。
> 入試演習・領域横断テーマの単元化は今後の改訂で扱う（他教科の私立・入試レーンと同方針: 過去問は転載しない）。
> 高校は基礎4科目を先行収録。発展5科目（物理・化学・生物・地学）と「科学と人間生活」は対象範囲として確定済みで、単元表の照合が済み次第追加する。

> **注記（Fable 5 の執筆可否と備考欄）**: 制作の正本モデル Claude Fable 5 には生命科学分野の安全機構があり、
> 理科には執筆できない単元がある（扱いの正式な定めは [docs/MODEL_POLICY.md](../../docs/MODEL_POLICY.md) §5）。
> 単元ごとの執筆可否は §5-1 の手順で機械的に判定し、判定済みの単元から備考欄に
> `fable_ok`（Fable 5 で制作可能・通常ルール適用）／`fable_blocked`（拒否判定・§5-2 の複数モデル工程のみ受付）を記録する。
> 備考欄が空欄の単元は**判定前**。判定前の単元に着手したい場合は、着手宣言Issueで判定をメンテナへ依頼できる。

## 公開コア（public_core）

> **制作済み教材の保全**: `jhs-sci-2-humidity-calculation`（湿度と飽和水蒸気量の計算）は本一覧のカーネル準拠改訂前に制作された単元で、ID・名称・状態・成果物を無変更で保全している。カーネル葉 `jhs-sci-2-weather-observation--fog-clouds-humidity` と範囲が重なる（湿度・飽和水蒸気量の計算部分の実装済み単元）。統合・分割は今後の改訂で扱う。

| unit_id | 単元名 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-sci-1-animal-classification` | 動物の分類 | 中1 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-1-aqueous-solutions--concentration` | 水溶液の濃度 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-aqueous-solutions--solubility` | 溶解と溶解度 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-earth-benefits-hazards` | 自然の恵みと火山・地震災害 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-earthquakes--earthquake-waves` | 地震の揺れと地震波 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-earthquakes--earthquakes-land` | 地震による大地の変化 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-force-basics` | 力のはたらき | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-gas-generation-properties` | 気体の発生と性質 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-light-and-sound--light` | 光の反射・屈折と像 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-light-and-sound--sound` | 音の発生・伝わり方と性質 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-observation-classification--classification-methods` | 生物を分類する観点と方法 | 中1 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-1-observation-classification--observation-skills` | 生物観察の基本技能 | 中1 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-1-plant-classification` | 植物の分類 | 中1 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-1-properties-of-matter--plastics-metals` | 金属・非金属・プラスチックの性質 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-properties-of-matter--properties-identification` | 物質の性質と見分け方 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-states-of-matter--melting-boiling` | 融点・沸点と蒸留 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-states-of-matter--state-changes` | 物質の状態変化と粒子モデル | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-strata-sedimentary-rocks--landforms-introduction` | 身近な地形・地層・岩石と土地の広がり | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-strata-sedimentary-rocks--sedimentary-rocks` | 堆積岩と地層の観察 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-strata-sedimentary-rocks--strata-formation` | 地層のでき方と地層から分かること | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-volcanoes-igneous-rocks--igneous-rocks` | 火成岩のつくりと分類 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-1-volcanoes-igneous-rocks--volcanoes` | 火山活動と噴出物 | 中1 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-animal-body-functions--digestion-absorption` | 消化と吸収 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-animal-body-functions--excretion-regulation` | 排出とからだの調節 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-animal-body-functions--respiration-circulation` | 呼吸と血液循環 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-animal-body-functions--stimulus-response` | 刺激と反応・神経系 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-atmospheric-movement-japan-weather--air-masses-fronts` | 気団・前線と天気の変化 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-atmospheric-movement-japan-weather--japan-seasons` | 日本の季節の天気 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-atmospheric-movement-japan-weather--pressure-wind` | 気圧配置と風 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-atoms-molecules-decomposition--atoms-molecules` | 原子・分子と化学式 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-atoms-molecules-decomposition--decomposition` | 物質の分解 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-cells` | 生物と細胞 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--combination` | 化合と化学反応式 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--oxidation` | 酸化と燃焼 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--reaction-heat` | 化学変化と熱 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-chemical-reactions-oxidation-reduction--reduction` | 還元 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-current-and-magnetic-fields--electromagnetic-induction` | 電磁誘導と発電 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-current-and-magnetic-fields--force-on-current` | 磁界中の電流が受ける力 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-current-and-magnetic-fields--magnetic-field-current` | 電流がつくる磁界 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-electric-circuits--current-voltage` | 回路の電流と電圧 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-electric-circuits--power-energy` | 電力と電力量・発熱 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-electric-circuits--resistance-ohm` | 電気抵抗とオームの法則 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-mass-conservation-ratio` | 化学変化と物質の質量 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-plant-body-functions--photosynthesis` | 光合成と葉のつくり | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-plant-body-functions--respiration` | 植物の呼吸 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-plant-body-functions--transport-transpiration` | 水・養分の移動と蒸散 | 中2 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-2-static-electricity-current` | 静電気と電流の正体 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-weather-benefits-hazards` | 自然の恵みと気象災害 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-weather-observation--fog-clouds-humidity` | 霧・雲の発生と湿度 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-humidity-calculation` | 湿度と飽和水蒸気量の計算 | 中2 | 外部レビュー済 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-weather-observation--weather-changes` | 気象データから天気の変化を読む | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-2-weather-observation--weather-elements` | 気象要素の観測と記録 | 中2 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-acids-bases-neutralization` | 酸・アルカリと中和 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-biodiversity-evolution` | 生物の多様性と進化 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-celestial-motion--annual-motion` | 太陽・星の年周運動と地球の公転 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-celestial-motion--daily-motion` | 天体の日周運動と地球の自転 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-celestial-motion--moon-venus` | 月と金星の見え方 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-chemical-batteries` | 化学変化と電池 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-ecosystems--food-webs` | 食物連鎖・食物網と生物間関係 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-ecosystems--material-cycles-balance` | 物質循環と生態系のつり合い | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-environment-science-technology--environment-conservation` | 自然環境の調査と保全 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-environment-science-technology--science-technology-society` | 自然環境の保全と科学技術の利用 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-forces-pressure-buoyancy--buoyancy` | 浮力 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-forces-pressure-buoyancy--force-composition` | 力の合成・分解 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-forces-pressure-buoyancy--water-pressure` | 水圧 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-growth-reproduction--cell-division-growth` | 細胞分裂と生物の成長 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-growth-reproduction--reproduction` | 生物の生殖 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-heredity-genes--genes` | 遺伝子と形質 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-heredity-genes--heredity-rules` | 遺伝の規則性 | 中3 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `jhs-sci-3-ions` | 水溶液とイオン | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-motion--force-motion` | 力と運動の関係 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-motion--motion-measurement` | 運動の記録・速さ・向き | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-nature-and-humans--regional-natural-disasters` | 地域の自然災害を資料から科学的に考察する | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-science-technology-humans--energy-resources` | エネルギーとエネルギー資源 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-science-technology-humans--materials-utilization` | 様々な物質とその利用 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-science-technology-humans--technology-development` | 科学技術の発展 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-solar-system-stars--solar-system` | 太陽系の構成と惑星 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-solar-system-stars--sun-stars` | 太陽・恒星と宇宙 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-work-and-energy--energy-transformations` | エネルギーの変換と保存 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-work-and-energy--mechanical-energy` | 力学的エネルギーとその保存 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `jhs-sci-3-work-and-energy--work-power` | 仕事と仕事率 | 中3 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-electricity--current-circuits` | 電流・電圧・抵抗と回路 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-electricity--electric-energy` | 電気エネルギーと利用 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-energy-utilization` | エネルギーとその利用 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-force-and-motion-laws--falling-motion` | 自由落下・鉛直投射と落下運動 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-force-and-motion-laws--forces-equilibrium` | 力の表し方とつり合い | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-force-and-motion-laws--laws-motion` | 運動の法則 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-motion--acceleration` | 加速度と等加速度直線運動 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-motion--measurement-data` | 物理量の測定・有効数字・データの扱い | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-motion--velocity` | 速度と相対運動 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-physics-opens-world` | 物理学が拓く世界 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-thermal-energy--heat-temperature` | 熱運動・温度・内部エネルギー | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-thermal-energy--thermodynamics-intro` | 熱と仕事・エネルギー保存 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-waves-sound--sound` | 音波と共鳴 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-waves-sound--wave-properties` | 波の表し方と性質 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-work-mechanical-energy--mechanical-energy` | 力学的エネルギー | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-physics-basic-work-mechanical-energy--work-power` | 仕事と仕事率 | 高校 物理基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-acids-and-bases--acids-bases` | 酸・塩基の定義と強弱 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-acids-and-bases--neutralization` | 中和反応と塩 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-acids-and-bases--titration` | 中和滴定 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-atomic-structure-periodic-table--atomic-structure` | 原子の構造 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-atomic-structure-periodic-table--periodic-table` | 周期表と元素の性質 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-chemical-bonds--covalent-bond` | 共有結合と分子 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-chemical-bonds--ionic-bond` | イオンとイオン結合 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-chemical-bonds--metallic-intermolecular` | 金属結合と物質の性質 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-chemistry-opens-world` | 化学が拓く世界 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-composition-of-matter--pure-substances` | 単体と化合物 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-composition-of-matter--separation` | 混合物の分離と精製 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-introduction--chemistry-characteristics` | 化学の特徴 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-introduction--thermal-motion-states` | 熱運動と物質の三態 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-mole-stoichiometry--amount-of-substance` | 物質量と粒子数・質量・気体体積 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-mole-stoichiometry--chemical-equations` | 化学反応式と量的関係 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-mole-stoichiometry--solutions` | 溶液の濃度と調製 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-oxidation-reduction--batteries` | 電池と酸化還元（化学基礎） | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-chemistry-basic-oxidation-reduction--oxidation-number` | 酸化数と酸化還元 | 高校 化学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-biology-basic-cells-common-features--cells-metabolism` | 細胞とエネルギー代謝 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-cells-common-features--common-features` | 生物の共通性と多様性 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-ecosystems-conservation--biodiversity` | 生物多様性 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-ecosystems-conservation--conservation` | 生態系の保全 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-ecosystems-conservation--ecosystem-processes` | 生態系の成り立ちと物質循環 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-genes-dna--dna-structure` | DNAと遺伝情報 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-genes-dna--gene-expression` | 遺伝情報の発現 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-homeostasis--body-fluids` | 体液と循環 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-homeostasis--regulation` | 自律神経・ホルモンと恒常性 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-immunity--adaptive` | 獲得免疫と免疫記憶 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-immunity--disorders` | 免疫と医療・免疫異常 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-immunity--innate` | 自然免疫 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-vegetation-succession--succession` | 遷移とバイオーム | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-biology-basic-vegetation-succession--vegetation` | 植生と環境 | 高校 生物基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-earth-basic-atmosphere-ocean--atmosphere` | 大気の構造と運動 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-atmosphere-ocean--climate` | 大気・海洋相互作用と気候 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-atmosphere-ocean--ocean` | 海洋の構造と循環 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-earth-environment--global-environment` | 地球環境の科学 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-earth-environment--japan-environment` | 日本の自然環境・恩恵・災害・予測防災 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-earth-history--earth-life-history` | 地球と生命の歴史 | 高校 地学基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-earth-basic-earth-history--geologic-time` | 地層・化石と地質時代 | 高校 地学基礎 | 未着手 | fable_blocked（2026-07-16判定・MODEL_POLICY §5の例外対象） |
| `hs-sci-earth-basic-earth-structure--interior` | 地球内部の構造 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-earth-structure--shape-gravity` | 地球の形と大きさ | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-natural-hazards-disaster-prevention--hazard-mechanisms` | 地震・火山・気象災害のしくみ | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-natural-hazards-disaster-prevention--risk-reduction` | 災害リスクの評価と防災 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-plate-tectonics--earthquakes` | 地震の発生と分布 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-plate-tectonics--plates` | プレート運動と地形 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-plate-tectonics--volcanoes` | 火山活動と火成岩 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-universe-solar-system--solar-system-earth-origin` | 太陽系と地球の誕生 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
| `hs-sci-earth-basic-universe-solar-system--universe-origin` | 宇宙の誕生 | 高校 地学基礎 | 未着手 | fable_ok（2026-07-16判定） |
