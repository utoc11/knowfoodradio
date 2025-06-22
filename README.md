# KNOWフードラジオ - 文字起こし管理システム

Podcast番組「KNOWフードラジオ」の文字起こしデータを管理し、番組運営に役立つ派生テキストを生成するためのシステムです。

## セットアップ

### 必要な環境
- Python 3.9以上
- pipenv

### インストール
```bash
# 依存関係のインストール
pipenv install

# 開発環境の場合
pipenv install --dev
```

## 使い方

### 文字起こしの取得

```bash
# 仮想環境を有効化
pipenv shell

# 最新エピソードを取得
python fetch_transcript.py

# または pipenv run を使用
pipenv run fetch

# 特定の年月のエピソードを取得
pipenv run python fetch_transcript.py --year-month 2024-01

# 期間を指定して取得
pipenv run python fetch_transcript.py --from 2024-01-01 --to 2024-03-31

# 全エピソードを取得
pipenv run fetch-all
```

### ディレクトリ構造

- `manual/` - 配信前の手動管理エピソード
- `from-rss/` - RSS経由で取得した配信済みエピソード
- `templates/` - 出力フォーマットの参考例

詳細は[PLANNING.md](PLANNING.md)を参照してください。

## 派生テキストの生成

文字起こしから以下のような派生テキストをLLMに依頼して生成できます：

### 基本的な派生テキスト
- 要約（summary.md）- 200-300文字の簡潔な要約
- ブリーフィング・ドキュメント（briefing.md）- 800-1200文字の詳細レポート
- ハイライト（highlights.md）- 30秒〜1分30秒の切り抜き候補
- 目次（timeline.md）- mm:ss形式のタイムスタンプ付き目次
- SNS投稿文（social/instagram.txt、social/x.txt）

### 追加の派生テキスト
- キーワード（keywords.txt）- SEO対策用
- 引用集（quotes.txt）- 印象的な発言
- 質問リスト（questions.txt）- 想定質問と企画案
- リスナー問いかけ（audience_engagement.txt）- SNS用の問いかけ
- 関連リンク（links.md）- 参考URL集

## 実際の使用例

### 配信済みエピソードの処理
```bash
# 1. 最新エピソードを取得
pipenv run fetch

# 2. LLMに派生テキスト作成を依頼
# 「from-rss/第30回_XXX/の文字起こしから派生テキストを作成してください」
# ※必ずCONTENT_GUIDELINES.mdに従うよう指示
```

### 配信前エピソードの準備
```bash
# manual/配下にtimeline-review.mdを配置後
# 「manual/#30.1-お便り回/のtimeline-review.mdから配信予告を作成してください」
```

## 重要なドキュメント

- [PLANNING.md](PLANNING.md) - ディレクトリ構造と運用フロー
- [CONTENT_GUIDELINES.md](CONTENT_GUIDELINES.md) - 派生テキストの品質基準
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - トラブルシューティングとコツ

## 開発

```bash
# コードフォーマット
pipenv run format

# リンター実行
pipenv run lint

# 型チェック
pipenv run typecheck
```