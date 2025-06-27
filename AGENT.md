# KNOWフードラジオ - LLM向け実装ガイドライン

## プロジェクト概要

KNOWフードラジオは、食と科学をテーマにしたPodcast番組の文字起こしデータ管理システムです。エピソードの文字起こしから様々な派生テキストを生成し、番組運営を支援します。

## ディレクトリ構造

```
knowfoodradio/
├── from-rss/              # RSS経由で取得した配信済みエピソード
│   └── {エピソード名}/
│       ├── metadata.json  # エピソード情報
│       ├── transcript.srt # 文字起こし
│       ├── summary.md     # 要約
│       ├── briefing.md    # 詳細レポート
│       ├── highlights.md  # ハイライト
│       ├── timeline.md    # タイムライン
│       ├── keywords.txt   # キーワード
│       ├── quotes.txt     # 引用集
│       ├── questions.txt  # 想定質問
│       ├── links.md       # 関連リンク
│       └── audience_engagement.txt # リスナー問いかけ
├── manual/                # 配信前の手動管理エピソード
├── notebooklm/           # NotebookLM用の統合ファイル
└── templates/            # 出力フォーマットの参考例
```

## NotebookLM連携機能

### create_notebooklm_files.py の詳細

このスクリプトは、NotebookLMにアップロードしやすい形式でエピソード情報を統合します。

#### 主要クラス: NotebookLMFileCreator

**初期化パラメータ:**
- `base_dir`: プロジェクトのベースディレクトリ（デフォルト: `/Users/yutokikuchi/dev/knowfoodradio`）
- `group_size`: 1ファイルにまとめるエピソード数（デフォルト: 10）

**主要メソッド:**

1. `setup_output_directory()`: 出力ディレクトリの準備
2. `copy_overview_file()`: 番組概要ファイルのコピー
3. `get_episode_directories()`: エピソードディレクトリの取得
4. `read_episode_data()`: エピソードデータの読み込み
5. `format_episode_content()`: エピソードデータのフォーマット
6. `create_grouped_files()`: グループ化されたファイルの作成
7. `create_index_file()`: インデックスファイルの作成

#### データ処理フロー

1. **エピソードデータの読み込み順序**:
   - metadata.json（メタデータ）
   - summary.md（要約）
   - briefing.md（詳細レポート）
   - highlights.md（ハイライト）
   - timeline.md（タイムライン）
   - keywords.txt（キーワード）
   - quotes.txt（引用）
   - questions.txt（質問）
   - links.md（リンク）

2. **フォーマット構造**:
   ```markdown
   # 🎙️ {エピソードタイトル}
   
   ## 📊 エピソード情報
   - **配信日**: {日付}
   - **収録時間**: {時間}
   - **エピソード番号**: #{番号}
   
   ## 📝 要約
   {要約内容}
   
   ## 📋 詳細ブリーフィング
   {ブリーフィング内容}
   
   ... (他のセクション)
   ```

3. **ファイル命名規則**:
   - `00_KNOWフードラジオとは.md` - 番組概要
   - `00_INDEX.md` - エピソードインデックス
   - `{番号:02d}_episodes_{開始:03d}-{終了:03d}.md` - グループ化されたエピソード

## 派生テキスト生成ルール

各派生テキストを生成する際は、必ず`CONTENT_GUIDELINES.md`の品質基準に従ってください。

### 重要な制約

1. **文字数制限の厳守**:
   - summary.md: 200-300文字
   - briefing.md: 800-1200文字
   - social/instagram.txt: 2200文字以内
   - social/x.txt: 140文字以内

2. **フォーマットの統一**:
   - timeline.md: 必ず`mm:ss`形式
   - highlights.md: 30秒〜1分30秒の範囲
   - links.md: Markdown形式のリンク

3. **トーンとスタイル**:
   - 親しみやすく、専門用語は避ける
   - 「食と科学」のテーマを意識
   - リスナーの知的好奇心を刺激する

## 技術的な注意事項

1. **文字エンコーディング**: 全ファイルはUTF-8で保存
2. **改行コード**: LF（Unix形式）を使用
3. **パス処理**: `pathlib.Path`を使用して環境非依存に
4. **エラーハンドリング**: ファイル読み込み時は例外をキャッチして継続

## よくあるタスクの実装パターン

### 新しいエピソードの処理

```python
# 1. 文字起こしの取得
pipenv run fetch

# 2. 派生テキストの生成（LLMで実行）
# from-rss/{エピソード名}/transcript.srtから各種ファイルを生成

# 3. NotebookLM用ファイルの再生成
python create_notebooklm_files.py
```

### カスタム処理の追加

新しい派生テキストタイプを追加する場合：

1. `read_episode_data()`メソッドの`files_to_read`リストに追加
2. `format_episode_content()`メソッドに新しいセクションを追加
3. 適切なアイコンと見出しを使用

## デバッグとトラブルシューティング

- **エピソードが見つからない**: `from-rss`ディレクトリの存在を確認
- **文字化け**: ファイルのエンコーディングを確認（UTF-8必須）
- **メモリ不足**: `group_size`を小さくして実行

## 今後の拡張予定

- 自動的な派生テキスト生成（LLM API連携）
- エピソード間の関連性分析
- テーマ別の自動分類機能