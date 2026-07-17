# 単元レジストリ: 社会

単元の全量と現在の状態の一覧（社会）。状態は次の7語のみを使う:
未着手 / 調査済 / ドラフト / QA済 / 外部レビュー済 / 人間レビュー済 / 公開済。
このファイルは `tools/progress_index/build_progress_index.py` が読み取り、
`curriculum/PROGRESS_INDEX.md` に集計される。

> **注記（全量性について）**: 中学3分野と高校必履修3科目（地理総合・歴史総合・公共）は
> 学習指導要領解説との逐条照合を完了し、単元の切り方を照合結果にもとづき再設計した。
> 高校選択5科目（地理探究・日本史探究・世界史探究・倫理・政治・経済）は第1版のまま（照合・分割は未実施。
> 着手時に同方式で改訂予定）。単元の切り方は本プロジェクトの編集判断。一覧への追加提案も歓迎（Issueで）。

> **注記（正直な開示・カーネル第2版化について）**: 社会でも理科・数学と同様に、教科カーネル（単元一覧の元表）を正本とし、
> 学習指導要領解説との逐条照合と単元粒度の再設計（カーネル第2版化）を実施のうえ、
> 中学3分野と高校必履修3科目をカーネル準拠へ**改訂済み**である。
> 従来の単元を「親ノード」として**既存IDの意味を保って維持**したまま、
> 学習単位を `親ID--子` 形式の子単元へ分割している（理科と同じ意味継承方式）。
> 進捗は子単元（および分割していない単元）のみで数え、親ノードは集計に含めない（二重計上防止）。
> 制作済み教材（`jhs-soc-civics-market-price`・`jhs-soc-geography-climate-life-reading`）は
> ID・状態・成果物ファイルを一切変更せず継承している。
> 学習順序（前提関係）は「必須」と「参考」の2階建てで別途設計している。表内の並びは仮であり、学習順は前提関係に従う。
> 単元総数は **133単元**（中学 地理25・歴史34・公民21、高校必履修 地理総合9・歴史総合9・公共13、高校選択22）
> ＋親ノード26＋共通モジュール4＋入口診断2＋私立・入試レーン6。
> 今後も単元の統廃合（分割・統合・名称変更）がありうる。

## 公開コア（public_core）— 中学・高校必履修（カーネル第2版）

| unit_id | 単元名 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-soc-geography-climate-life-reading` | 世界の気候と人々の生活を資料で読み解く | 中学 地理 | 調査済 | 調査成果あり・完全保全 |
| `jhs-soc-geography-japan-industry-energy--agriculture-fisheries` | 日本の農林水産業 | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-industry-energy--manufacturing-commerce-services` | 工業と商業・サービス業（製造業から第3次産業まで拡張） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-industry-energy--resources-energy` | 日本の資源・エネルギー | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-nature--hazards-adaptation` | 日本の自然災害と防災 | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-nature--landforms-climate` | 日本の地形・気候 | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-overview` | 日本の姿（位置・領域・時差・都道府県） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-population` | 日本の地域的特色（人口） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regional-survey` | 地域調査・フィールドワーク方法モジュール | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-chubu` | 日本の諸地域（中部地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-chugoku-shikoku` | 日本の諸地域（中国・四国地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-hokkaido` | 日本の諸地域（北海道地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-kanto` | 日本の諸地域（関東地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-kinki` | 日本の諸地域（近畿地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-kyushu` | 日本の諸地域（九州地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-regions-tohoku` | 日本の諸地域（東北地方） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-transport-communication` | 日本の地域的特色（交通・通信） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-region-vision` | 地域の在り方（身近な地域の課題と構想） | 中学 地理 | 未着手 | 新設（照合で判明した欠落の解消） |
| `jhs-soc-geography-world-overview` | 世界の姿（六大陸と三大洋・国々の位置） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-world-regions-africa` | 世界の諸地域（アフリカ州） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-world-regions-asia` | 世界の諸地域（アジア州） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-world-regions-europe` | 世界の諸地域（ヨーロッパ州） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-world-regions-north-america` | 世界の諸地域（北アメリカ州） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-world-regions-oceania` | 世界の諸地域（オセアニア州） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-world-regions-south-america` | 世界の諸地域（南アメリカ州） | 中学 地理 | 未着手 |  |
| `jhs-soc-history-ancient-civilizations--ancient-civilizations` | 古代文明の成立 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-ancient-civilizations--human-origins` | 人類の出現と生活の変化 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-ancient-civilizations--religions-empires` | 宗教・帝国と古代世界 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-bakumatsu-meiji-restoration--opening-bakumatsu` | 開国と幕末の動乱 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-bakumatsu-meiji-restoration--restoration-civilization` | 明治維新と文明開化 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-contemporary-japan--high-growth` | 高度経済成長と社会変化 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-contemporary-japan--post-growth-internationalization` | 石油危機後の日本と国際化 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-depression-wwii--depression-fascism-road` | 世界恐慌・ファシズムと戦争への道 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-depression-wwii--total-war-devastation` | 総力戦・戦時社会と戦争の惨禍 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-edo-bakuhan-system--foreign-relations` | 江戸初期の対外政策と四つの窓口 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-edo-bakuhan-system--formation` | 江戸幕府の成立と大名統制 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-edo-bakuhan-system--society-status` | 身分制と村・町の社会 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-edo-industry-culture` | 産業の発達と町人文化（江戸時代の社会） | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-edo-reforms` | 幕府政治の改革 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-european-contact-unification` | ヨーロッパ人の来航と全国統一 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-heian-court-culture` | 貴族の政治と国風文化（平安時代） | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-jomon-yayoi-kofun` | 日本列島の成り立ちと国家の形成（縄文〜古墳） | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-kamakura-warrior-government--formation` | 鎌倉幕府の成立 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-kamakura-warrior-government--mongol-invasions` | 元寇と幕府の衰退 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-kamakura-warrior-government--rule-society` | 鎌倉幕府の政治と社会 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-local-history` | 身近な地域の歴史（地域史の調べ方） | 中学 歴史 | 未着手 | 新設（照合で判明した欠落の解消） |
| `jhs-soc-history-meiji-constitutional-state--rights-constitution` | 自由民権運動と立憲国家の成立 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-meiji-constitutional-state--wars-treaties-imperialism` | 日清・日露戦争と条約改正・帝国主義 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-modern-industry-culture` | 近代産業の発展と近代文化の形成 | 中学 歴史 | 未着手 | 新設（照合で判明した欠落の解消） |
| `jhs-soc-history-modern-revolutions--citizen-revolutions-nation-states` | 市民革命と国民国家 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-modern-revolutions--industrial-revolution-capitalism` | 産業革命と資本主義 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-muromachi-society--popular-growth` | 民衆の成長と産業・文化 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-muromachi-society--shogunate` | 室町幕府と東アジア | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-muromachi-society--warring-states` | 戦国大名と社会変化 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-periodization-timeline` | 時代区分・年表・年代計算モジュール | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-postwar-reconstruction` | 戦後日本の民主化と国際社会への復帰 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-ritsuryo-state` | 律令国家の成立（飛鳥・奈良時代） | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-summary-inquiry` | 歴史のまとめ（歴史と私たち・未来への構想） | 中学 歴史 | 未着手 | 新設（照合で判明した欠落の解消） |
| `jhs-soc-history-taisho-wwi` | 第一次世界大戦と大正デモクラシー | 中学 歴史 | 未着手 |  |
| `jhs-soc-civics-banking-finance` | 金融のしくみ | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-better-society` | よりよい社会を目指して（社会科のまとめ探究） | 中学 公民 | 未着手 | 新設（照合で判明した欠落の解消） |
| `jhs-soc-civics-constitution-principles` | 日本国憲法の基本原理 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-consumer-life` | 消費生活と経済（家計・消費者の権利） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-democracy-election-data--democracy-principles` | 民主主義の基本原理（多数決と少数意見の尊重） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-democracy-election-data--elections-participation` | 選挙のしくみと政治参加・政治データ読解 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-diet-cabinet-courts--cabinet` | 内閣と行政 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-diet-cabinet-courts--courts` | 裁判所と司法 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-diet-cabinet-courts--diet` | 国会のしくみと立法 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-global-issues` | 地球規模の課題（環境・資源・貧困） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-human-rights` | 基本的人権の尊重 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-international-society` | 国際社会のしくみ（主権国家・国際連合） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-local-government` | 地方自治のしくみ | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-market-price` | 市場経済と価格のはたらき | 中学 公民 | 外部レビュー済 | 制作済み・完全保全 |
| `jhs-soc-civics-modern-society--culture-meaning` | 現代社会における文化の意義・影響と継承（科学・芸術・宗教） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-modern-society--structural-change` | 現代社会の構造変化（少子高齢化・情報化・グローバル化） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-production-labor--firms-production` | 企業・生産と経済活動 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-production-labor--labor` | 労働の権利と働き方 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-public-finance-welfare--public-finance` | 財政と租税 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-public-finance-welfare--social-security` | 社会保障のしくみと課題 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-social-frameworks` | 現代社会を捉える枠組み（対立と合意・効率と公正） | 中学 公民 | 未着手 | 新設（照合で判明した欠落の解消） |
| `hs-soc-geography_comprehensive-disaster-prevention--hazard-risk-information` | 災害の地域性とリスク情報（ハザードマップ・新旧地形図） | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-disaster-prevention--regional-disaster-planning` | 地域の防災・減災の計画 | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-global-issues--environment-resources-energy` | 地球環境問題と資源・エネルギー問題 | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-global-issues--interrelation-cooperation` | 地球的課題の相互関連と国際協力 | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-global-issues--population-food-housing-urban` | 人口・食料問題と居住・都市問題 | 高校 地理総合 | 未着手 | 照合で判明したスコープ欠落の解消 |
| `hs-soc-geography_comprehensive-life-culture-diversity--globalization-culture-change` | グローバル化と生活文化の変容 | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-life-culture-diversity--nature-society-culture` | 自然・社会環境と生活文化（宗教・言語を含む） | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-map-gis-literacy` | 地図・GIS活用スパイラルモジュール | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-region-future` | 生活圏の調査と地域の展望 | 高校 地理総合 | 未着手 | 新設（照合で判明した欠落の解消） |
| `hs-soc-history_comprehensive-globalization--cold-war-transformation` | 冷戦の展開と終結 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-globalization--economic-globalization-contemporary` | 経済のグローバル化と現代的課題の歴史的形成 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-history-door` | 歴史の扉（歴史と私たち・歴史の特質と資料） | 高校 歴史総合 | 未着手 | 新設（照合で判明した欠落の解消） |
| `hs-soc-history_comprehensive-mass-society--depression-wwii` | 経済危機とファシズム・第二次世界大戦 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-mass-society--postwar-decolonization` | 戦後国際秩序と脱植民地化 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-mass-society--wwi-mass-society` | 第一次世界大戦と大衆社会 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-modernization--asia-and-opening` | 18世紀のアジアと結び付く世界・日本の開国 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-modernization--modernization-questions` | 近代化への問い（資料から問いを立てる） | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-modernization--nation-state-industrialization-imperialism` | 国民国家の形成と産業化・帝国主義 | 高校 歴史総合 | 未着手 |  |
| `hs-soc-public-conflict-consensus` | 対立・合意・効率・公正の思考ツールモジュール | 高校 公共 | 未着手 |  |
| `hs-soc-public-democracy-participation--elections-media-participation` | 選挙・政治参加と世論・メディア | 高校 公共 | 未着手 |  |
| `hs-soc-public-democracy-participation--governance-local-autonomy` | 民主政治の仕組みと地方自治 | 高校 公共 | 未着手 |  |
| `hs-soc-public-economy-and-society--fiscal-social-security` | 財政・租税と社会保障 | 高校 公共 | 未着手 |  |
| `hs-soc-public-economy-and-society--labor-work` | 労働と職業生活 | 高校 公共 | 未着手 |  |
| `hs-soc-public-economy-and-society--market-finance` | 市場経済と企業・貨幣・金融 | 高校 公共 | 未着手 | 照合で判明したスコープ欠落の解消 |
| `hs-soc-public-foundational-principles` | 公共的な空間における基本的原理（幸福・正義・公正） | 高校 公共 | 未着手 | 新設（照合で判明した欠落の解消） |
| `hs-soc-public-international-cooperation--global-economy-cooperation` | 国際経済と地球規模課題の国際協力 | 高校 公共 | 未着手 |  |
| `hs-soc-public-international-cooperation--order-security` | 国際秩序と主権・安全保障 | 高校 公共 | 未着手 |  |
| `hs-soc-public-law-and-life--contracts-consumers-law` | 契約・消費者と法の働き（法や規範の意義を含む） | 高校 公共 | 未着手 |  |
| `hs-soc-public-law-and-life--judiciary-participation` | 司法制度と市民の司法参加（裁判員制度） | 高校 公共 | 未着手 |  |
| `hs-soc-public-self-and-society` | 公共的な空間をつくる私たち（青年期と先人の思想） | 高校 公共 | 未着手 |  |
| `hs-soc-public-sustainable-capstone` | 持続可能な社会づくりの主体となる私たち（まとめ探究） | 高校 公共 | 未着手 | 新設（照合で判明した欠落の解消） |

### 親ノード（進捗集計対象外・進捗は子単元で計上）

分割した既存単元のIDは、親ノードとして意味を保って維持する。制作済み教材の原本は該当単元でそのまま保全する。

| parent_id | 名称 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `jhs-soc-geography-japan-industry-energy` | 日本の地域的特色（資源・エネルギーと産業） | 中学 地理 | 未着手 |  |
| `jhs-soc-geography-japan-nature` | 日本の地域的特色（自然環境） | 中学 地理 | 未着手 |  |
| `jhs-soc-history-ancient-civilizations` | 人類の出現と古代文明 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-bakumatsu-meiji-restoration` | 開国と明治維新 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-contemporary-japan` | 高度経済成長と現代の日本 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-depression-wwii` | 世界恐慌と第二次世界大戦 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-edo-bakuhan-system` | 江戸幕府の成立と幕藩体制 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-kamakura-warrior-government` | 武家政権の成立（鎌倉時代） | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-meiji-constitutional-state` | 立憲国家の成立と日清・日露戦争 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-modern-revolutions` | 欧米の市民革命と産業革命 | 中学 歴史 | 未着手 |  |
| `jhs-soc-history-muromachi-society` | 室町幕府と民衆の成長（室町時代） | 中学 歴史 | 未着手 |  |
| `jhs-soc-civics-democracy-election-data` | 民主政治と選挙のしくみを資料で読む | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-diet-cabinet-courts` | 国会・内閣・裁判所のしくみ | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-modern-society` | 現代社会の特色（情報化・少子高齢化・グローバル化） | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-production-labor` | 生産のしくみと企業・労働 | 中学 公民 | 未着手 |  |
| `jhs-soc-civics-public-finance-welfare` | 財政と社会保障 | 中学 公民 | 未着手 |  |
| `hs-soc-geography_comprehensive-disaster-prevention` | 自然環境と防災 | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-global-issues` | 地球的課題と国際協力 | 高校 地理総合 | 未着手 |  |
| `hs-soc-geography_comprehensive-life-culture-diversity` | 生活文化の多様性と国際理解 | 高校 地理総合 | 未着手 |  |
| `hs-soc-history_comprehensive-globalization` | グローバル化と私たち | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-mass-society` | 国際秩序の変化や大衆化と私たち | 高校 歴史総合 | 未着手 |  |
| `hs-soc-history_comprehensive-modernization` | 近代化と私たち | 高校 歴史総合 | 未着手 |  |
| `hs-soc-public-democracy-participation` | 民主政治と政治参加 | 高校 公共 | 未着手 |  |
| `hs-soc-public-economy-and-society` | 経済社会で生きる私たち（市場・労働・社会保障） | 高校 公共 | 未着手 |  |
| `hs-soc-public-international-cooperation` | 国際社会と人類の課題 | 高校 公共 | 未着手 |  |
| `hs-soc-public-law-and-life` | 法の働きと私たち（契約・消費者・司法参加） | 高校 公共 | 未着手 |  |

## 公開コア（public_core）— 高校 選択5科目（第1版のまま・現行無変更）

> 以下22単元は第1版のまま（学習指導要領解説との照合・粒度再設計は着手時に同方式で実施予定）。
> 既存IDは意味を保って維持する方針。

| unit_id | 単元名 | 学校段階・学年 | 状態 | 備考 |
|---|---|---|---|---|
| `hs-soc-geography_inquiry-systematic-physical` | 系統地理（自然環境） | 高校 地理探究 | 未着手 |  |
| `hs-soc-geography_inquiry-systematic-human` | 系統地理（産業・人口・都市） | 高校 地理探究 | 未着手 |  |
| `hs-soc-geography_inquiry-regional-geography` | 地誌（世界の諸地域） | 高校 地理探究 | 未着手 |  |
| `hs-soc-japanese_history_inquiry-ancient` | 原始・古代の日本 | 高校 日本史探究 | 未着手 |  |
| `hs-soc-japanese_history_inquiry-medieval` | 中世の日本 | 高校 日本史探究 | 未着手 |  |
| `hs-soc-japanese_history_inquiry-early-modern` | 近世の日本 | 高校 日本史探究 | 未着手 |  |
| `hs-soc-japanese_history_inquiry-modern-contemporary` | 近現代の日本 | 高校 日本史探究 | 未着手 |  |
| `hs-soc-world_history_inquiry-regional-characteristics` | 諸地域の歴史的特質の形成 | 高校 世界史探究 | 未着手 |  |
| `hs-soc-world_history_inquiry-interregional-exchange` | 諸地域の交流・再編 | 高校 世界史探究 | 未着手 |  |
| `hs-soc-world_history_inquiry-modern-integration` | 諸地域の結合・変容 | 高校 世界史探究 | 未着手 |  |
| `hs-soc-world_history_inquiry-contemporary-world` | 地球世界の課題 | 高校 世界史探究 | 未着手 |  |
| `hs-soc-ethics-source-thought` | 源流思想（ギリシア思想と宗教） | 高校 倫理 | 未着手 |  |
| `hs-soc-ethics-japanese-thought` | 日本思想の展開 | 高校 倫理 | 未着手 |  |
| `hs-soc-ethics-western-modern-thought` | 西洋近現代思想 | 高校 倫理 | 未着手 |  |
| `hs-soc-ethics-contemporary-issues` | 現代の諸課題と倫理（生命・環境・情報） | 高校 倫理 | 未着手 |  |
| `hs-soc-politics_economics-constitution-governance` | 憲法と統治機構の構造整理 | 高校 政治・経済 | 未着手 |  |
| `hs-soc-politics_economics-political-participation` | 現代日本の政治（選挙・政党・世論） | 高校 政治・経済 | 未着手 |  |
| `hs-soc-politics_economics-international-politics` | 国際政治の動向と課題 | 高校 政治・経済 | 未着手 |  |
| `hs-soc-politics_economics-market-national-income` | 現代経済のしくみ（市場機構と国民所得） | 高校 政治・経済 | 未着手 |  |
| `hs-soc-politics_economics-fiscal-monetary` | 財政と金融 | 高校 政治・経済 | 未着手 |  |
| `hs-soc-politics_economics-labor-social-security` | 労働と社会保障 | 高校 政治・経済 | 未着手 |  |
| `hs-soc-politics_economics-international-economy` | 国際経済の動向と課題 | 高校 政治・経済 | 未着手 |  |

## 共通スキルモジュール・入口診断（単元と別枠）

> 進捗集計の単元数には含めない（単元を横断して適用するモジュール／診断。対象単元との関係は
> applies_to / assesses で管理し、前提（prerequisite）辺は張らない）。入口診断の実体化は
> 診断仕様書の受入合格を唯一の条件とする。

| module_id | 名称 | 学校段階・学年 | 状態 | 区分 |
|---|---|---|---|---|
| `lane-soc-causal-comparison` | 社会・因果説明と比較 | 中高共通 | 未着手 | 共通モジュール |
| `lane-soc-maps-data` | 社会・地図・統計・図表リテラシー | 中高共通 | 未着手 | 共通モジュール |
| `lane-soc-multiperspective-argument` | 社会・多面的・多角的な論証 | 中高共通 | 未着手 | 共通モジュール |
| `lane-soc-source-criticism` | 社会・史資料の批判的読解 | 中高共通 | 未着手 | 共通モジュール |
| `jhs-soc-entry-diagnostic` | 中学社会・学び直し入口診断 | 中学 | 未着手 | 入口診断 |
| `hs-soc-entry-diagnostic` | 高校社会・学び直し入口診断 | 高校 | 未着手 | 入口診断 |

## 私立・入試レーン（スキルモジュール群）

> 私立・入試レーンは「内容の単元」ではなく、公開コアの単元を素材として横断的に使う
> 「読み方・書き方の型」のスキルモジュール群として再構成した（骨子段階から予告していた再編）。
> 地理・歴史・公民の3分野バランスで構成する。過去問の転載は行わない（入試の「型」の指導であって過去問集ではない）。
> 時事資料・統計を使うモジュールは、資料ごとに時点（as_of）・出典・ライセンス・取得日を明記する。
> 論述型の評価は構成・因果の妥当性を観点とし、歴史的・政治的に評価が分かれる論点を正解扱いしない。

| module_id | 名称 | 学校段階・学年 | 状態 | 区分 |
|---|---|---|---|---|
| `jhs-soc-history-modernization-causality` | 歴史因果説明スパイラルモジュール | 中学 歴史 | 未着手 | スキルモジュール |
| `jhs-soc-history-source-inference` | 史料読解・時代推論スパイラルモジュール | 中学 歴史 | 未着手 | スキルモジュール |
| `lane-soc-entrance-geography-multisource-analysis` | 入試地理・複数資料の統合分析（地形図・統計地図） | 中高共通 | 未着手 | スキルモジュール |
| `lane-soc-entrance-civics-source-quant` | 入試公民・資料と数量の読解（時事資料・経済計算の型） | 中高共通 | 未着手 | スキルモジュール |
| `hs-soc-japanese_history_inquiry-essay-frame` | 歴史論述・因果説明スパイラルモジュール | 高校 日本史探究 | 未着手 | スキルモジュール |
| `hs-soc-history_comprehensive-turning-points` | 歴史総合・複数資料統合アセスメント | 高校 歴史総合 | 未着手 | 評価パッケージ |

---

### 改訂の根拠と保全（正直な開示）

- 制作済み単元のID・状態は全件無変更で保全した（`jhs-soc-civics-market-price`=外部レビュー済・`jhs-soc-geography-climate-life-reading`=調査済）。
- 学習順序（前提関係）は「必須」と「参考」の2階建てで別途設計している。表内の並びは仮であり、学習順は前提関係に従う。
- 入口診断は診断仕様書の受入合格までは実体化しない（予約枠として登記のみ）。
- 従来「私立・入試レーン中心」として単元扱いだった4件は、内容の単元ではなくスキルモジュール（横断適用）へ再類型化した（IDは維持・単元の進捗集計からは外れる）。
