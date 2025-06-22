# KNOWフードラジオ ディレクトリ設計プラン

## 概要
Podcast番組「KNOWフードラジオ」の文字起こしデータを管理し、番組運営に役立つ派生テキストを生成するためのシンプルな構成です。

## ディレクトリ構造

```
knowfoodradio/
├── README.md                    # プロジェクト概要
├── PLANNING.md                  # このファイル
├── fetch_transcript.py          # RSSから文字起こしを取得するスクリプト
│
├── manual/                      # 手動管理エピソード（配信前・配信日未定）
│   ├── EP023_draft/            # 仮番号_識別子
│   │   ├── transcript.txt      # 文字起こし（手動配置）※ない場合もあり
│   │   ├── timeline-review.md  # 時系列詳細レビュー（transcriptの代替）
│   │   ├── metadata.json       # 暫定情報
│   │   ├── preview.md          # 配信予告文
│   │   ├── teaser.md           # ティーザー（興味喚起用）
│   │   └── social/             # SNS事前告知用
│   │       ├── instagram_preview.txt
│   │       └── x_preview.txt
│   └── #30.1-お便り回（ネイチャーポジティブ中心）/  # 実例
│
├── from-rss/                    # RSS自動取得エピソード（配信済み）
│   ├── 第23回_ゲスト山田太郎さんと語る発酵食品の世界/  # RSSのタイトルそのまま
│   │   ├── transcript.srt      # 文字起こし（RSS取得）
│   │   ├── metadata.json       # RSS情報から自動生成
│   │   ├── summary.md          # 要約（200-300文字）
│   │   ├── briefing.md         # ブリーフィング（詳細な要約）
│   │   ├── highlights.md       # 切り抜き用ハイライト
│   │   ├── timeline.md         # 目次（mm:ss形式）
│   │   └── social/             # SNS投稿用
│   │       ├── instagram.txt   
│   │       └── twitter.txt     
│   └── ...
│
└── templates/                   # 出力フォーマットの参考例
    ├── summary_example.md
    ├── briefing_example.md
    ├── highlights_example.md
    └── timeline_example.md
```

## ファイル命名ルール

### 手動管理（manual/）
1. **エピソードフォルダ**: `EP{仮番号3桁}_{識別子}/`
   - 例: `EP023_draft/`, `EP024_guest-tanaka/`, `EP025_curry-special/`
   - 識別子：draft、ゲスト名、トピック名など

### RSS取得（from-rss/）
1. **エピソードフォルダ**: RSSのエピソードタイトルをそのまま使用
   - 例: `第23回_ゲスト山田太郎さんと語る発酵食品の世界/`
   - 例: `第24回_夏野菜を使った簡単レシピ特集/`
   - 特殊文字（/、:、?等）は_に置換

### 共通の固定ファイル名（from-rss/配信済み）:
   - `transcript.srt`: 文字起こし（RSS取得）
   - `metadata.json`: エピソード情報
   - `summary.md`: 200-300文字の要約
   - `briefing.md`: ブリーフィング・ドキュメント（800-1200文字の詳細要約）
   - `highlights.md`: 切り抜き候補（タイムスタンプ付き）
   - `timeline.md`: 目次（mm:ss形式）
   - `social/instagram.txt`: Instagram投稿用（150文字程度）
   - `social/x.txt`: X投稿用（140文字以内）

### manual/配信前エピソード専用ファイル:
   - `timeline-review.md`: 時系列詳細レビュー（transcriptの代替）
   - `preview.md`: 配信予告文（300-500文字）
   - `teaser.md`: ティーザー（100-200文字、興味喚起用）
   - `social/instagram_preview.txt`: Instagram予告投稿
   - `social/x_preview.txt`: X予告投稿

## RSSから文字起こし取得スクリプト仕様

`fetch_transcript.py` の機能:
1. RSS feed（https://anchor.fm/s/7637c118/podcast/rss）からエピソード情報を取得
2. `<podcast:transcript>` タグから.srtファイルをダウンロード
3. from-rss/配下に適切なディレクトリ構造で保存
4. metadata.jsonを自動生成（タイトル、配信日、説明文等）

実行例:
```bash
# 最新エピソードを取得
python fetch_transcript.py

# 全エピソードを取得
python fetch_transcript.py --all

# 特定のエピソード番号を取得
python fetch_transcript.py --episode 23
```

## 派生テキストの種類と用途

### 1. 要約 (summary.md)
- 200-300文字でエピソードの内容を説明
- ゲスト紹介と主要トピックを含む

### 2. ブリーフィング・ドキュメント (briefing.md)
- 800-1200文字の詳細な要約
- 話題の流れ、重要な発言、具体的な情報を網羅
- ゲストの経歴・専門分野の説明
- 議論されたトピックの背景情報
- 番組で紹介された具体的なレシピ・テクニック

### 3. ハイライト (highlights.md)
- 30秒〜1分30秒の切り抜き用
- 1エピソードあたり3-5箇所
- 開始・終了タイムスタンプ付き
- 内容の面白さ・インパクトを重視

### 4. 目次 (timeline.md)
- mm:ss形式でトピックを列挙
- YouTubeの動画説明欄に貼れる形式
- 例:
  ```
  00:00 オープニング
  02:15 今週の食材紹介
  08:30 ゲストトーク開始
  ```

### 5. SNS投稿文
- Instagram: 150文字程度、ハッシュタグ含む
- X: 140文字以内、簡潔なキャッチコピー

## 追加提案：番組運営に役立つテキスト

### 1. キーワード抽出 (keywords.txt)
- SEO対策用の重要キーワード
- ゲストの専門用語
- トレンドワード

### 2. 質問リスト (questions.txt)
- リスナーからの想定質問
- 次回エピソードの企画用

### 3. リスナー問いかけ (audience_engagement.txt)
- SNSで投稿する際の問いかけ文
- Yes/Noで答えられる質問
- 体験をシェアしたくなる質問

### 4. 引用集 (quotes.txt)
- ゲストの印象的な発言
- SNS用の短い引用文

### 5. 関連リンク集 (links.md)
- エピソード内で言及したURL
- 参考資料・レシピサイト等

## 使用方法

1. **文字起こし取得**:
   ```bash
   python fetch_transcript.py
   ```

2. **派生テキスト生成依頼例**:
   「manual/EP023_draftの文字起こしから要約を作成してください」
   「from-rss/EP001_20240115のハイライトを3つ抽出してください」
   「EP023のInstagram投稿文を作成してください」

## エピソード管理の流れ

1. **配信前**: manual/配下で管理
   - timeline-review.mdから予告文・ティーザーを生成
   - SNSで事前告知を展開
   - リスナーの期待を醸成
   
2. **配信後**: RSSから取得してfrom-rss/配下に保存
   - 実際の配信内容から各種派生テキストを生成
   - 視聴促進・拡散用コンテンツを作成
   
3. **移行時**: 必要に応じてmanual/の一部情報を活用

## 備考
- 文字起こしの自動取得以外は、都度LLMに依頼する運用
- シンプルな構造で、必要に応じて拡張可能
- ファイル形式は基本的にプレーンテキストまたはMarkdown
- manual/とfrom-rss/で重複するエピソードがある場合、from-rss/を正とする