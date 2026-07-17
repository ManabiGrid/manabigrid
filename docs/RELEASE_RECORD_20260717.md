---
doc_type: release_record
date: 2026-07-17
---

# RELEASE_RECORD — ベータ版 初回公開（2026-07-17）

## 凍結記録（検証可能な方式・v3）

- 対象: **gitが追跡する全ファイル**（本ファイル自身 `docs/RELEASE_RECORD_20260717.md` を除く）。git管理外のファイルは対象外
- ファイル数: 488
- 集約SHA-256: `e9817e9d74530179ecd9ad38abe718ab51d71474c564152e217fab2e8b3d08c9`
- 算出方法（リポジトリ直下で下のコードを実行すれば再現できます）:

```python
import subprocess, hashlib
EXCL="docs/RELEASE_RECORD_20260717.md"
out=subprocess.run(["git","ls-files","-z"],capture_output=True).stdout.decode()
files=sorted(f for f in out.split("\0") if f and f!=EXCL)
h=hashlib.sha256()
for f in files:
    h.update(f.encode()); h.update(hashlib.sha256(open(f,"rb").read()).digest())
print(len(files), h.hexdigest())
```

- 公開履歴は**単一コミット**（クリーンルート方式・過去の作業履歴を持ち込まない）。凍結コミットのSHAはリリースタグ `v0.1.0-beta`（public化時に付与予定・現時点では未付与）の対象コミットとして確認できます
- 旧リポジトリの全コミットは、本リポジトリのGitHub APIで**全件取得不能**（HTTP 422 "No commit found"・2026-07-17全数照合）。取得不能の証拠値は404ではなく422

## 実施済みの検査（2026-07-17）

- 内部語彙・秘密情報・個人情報・ローカルパスの全数検査: 0件（NFKC正規化・区切りゆれ16種込み）
- 相対リンク・アンカーの全数照合: 欠落0件／レッスン→解答リンク: 126/126
- CommonMark実レンダリングでの強調崩れ（コード外の生アスタリスク）: 0件
- 図版185枚のコード来歴再現・自動検算: 全通過／ビュー生成器テスト: 全通過
- 進捗一覧はレジストリからの自動生成でバイト一致

## 既知の制限（正直な開示）

1. 一部のMarkdownレンダラ（marked等）では、数式記号に隣接する強調が生の `**` として表示される場合があります（GitHub標準のレンダリングでは0件を確認済み）。記号単独の強調の解消は改善課題です
2. 引用部分と出典台帳の機械的な1対1対応（source_id方式）は未導入です（改善課題）
3. 進捗一覧は分割済み単元の親ノードを掲載しません（親の状態は各教科レジストリ参照）
4. 検疫CIの検査パターンは透明性を優先して公開しています（実効的な防御はルールセットのCode Ownersレビュー・required checksです）
5. ルールセットには**リポジトリ管理者（メンテナ本人）のバイパスが設定されています**——単独運営でのセルフマージ用の意図的な例外です。GitHubのIssue作成画面の「Blank issue」は**メンテナ専用**として残ります（GitHubの仕様。一般の投稿者は構造化フォームまたは外部フォームのみ）
6. CODEOWNERSの個人アカウント表記は意図的な運用です
