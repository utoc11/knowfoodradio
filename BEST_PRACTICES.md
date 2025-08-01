# KNOWフードラジオ ベストプラクティス

## よくある課題と解決策

### 1. 文字起こしファイルが大きすぎて読み込めない
**問題**: SRTファイルが25,000トークンを超える
**解決策**: 
- Taskツールを使用して全体を分析
- 必要に応じて部分的に読み込み（offset/limit指定）
- 重要な部分を先に特定してから詳細確認

### 2. エピソードタイトルに特殊文字が含まれる
**問題**: ディレクトリ名に使えない文字（/、:、?等）
**解決策**: 
- fetch_transcript.pyが自動的に_に置換
- 手動の場合も同じルールで統一

### 3. 派生テキストの品質がバラつく
**問題**: 作成者によって品質が異なる
**解決策**: 
- 必ずCONTENT_GUIDELINES.mdを参照
- templatesフォルダの例を活用
- チェックリストで最終確認

### 4. SNS投稿文が文字数オーバー
**問題**: X（Twitter）の140文字制限を超える
**解決策**: 
- 絵文字は2文字分として計算
- URLは23文字として計算
- ハッシュタグは最小限に

## 効率的なワークフロー

### 配信前（manual/）の流れ
1. timeline-review.mdを読み込み
2. preview.md → teaser.md → SNS予告の順で作成
3. 配信日の1週間前から段階的に告知

### 配信後（from-rss/）の流れ
1. fetch_transcript.pyで自動取得
2. 全体分析（Taskツール推奨）
3. summary.md → briefing.md → highlights.md → timeline.mdの順
4. SNS投稿は配信直後と翌日の2回

## 品質向上のコツ

### 1. 読者目線の確認
- 専門用語ゼロで理解できるか？
- 初めての人でも興味を持てるか？
- 次のアクションが明確か？

### 2. 感情を動かす要素
- 驚き：「えっ、○○なの！？」
- 共感：「あるある」「そうそう」
- 好奇心：「それってどういうこと？」

### 3. 具体性の追求
- 曖昧：多くの企業が取り組んでいる
- 具体的：日清食品、KDDI、NECなど大手企業が続々参入

### 4. ストーリー性
- 時系列で追える構成
- 起承転結がある
- 最後に「で、どうなった？」に答える

## トラブルシューティング

### Q: 配信前なのにネタバレしすぎた
A: teaser.mdは最も抽象的に、preview.mdでも核心は避ける

### Q: highlights.mdの時間が長すぎる
A: 「※編集で短縮推奨」を追記し、核となる部分を明示

### Q: timeline.mdが単調になる
A: 感情表現、数字、疑問形をバランスよく配置

### Q: briefing.mdが堅い
A: 最初の3行で雰囲気を作る。会話から始めるのも効果的

## 継続的改善

### 月次レビュー項目
- [ ] 最も反響があった投稿の分析
- [ ] 新しい表現パターンの発掘
- [ ] リスナーフィードバックの反映
- [ ] ガイドラインのアップデート

### 実験的取り組み
- 絵文字の使い方を変えてみる
- 新しい切り口でハイライトを選ぶ
- 異なる時間帯でSNS投稿してみる

## 参考：成功事例

### 反響が大きかったtimeline.md見出し
- 「えっ、1000万円！？」衝撃の検査費用
- お父さんの腸内細菌も子どもに影響する新事実
- カルビーがグラノーラで狙う一石二鳥戦略

### シェアされやすいSNS投稿
- 質問形式：「○○って知ってた？」
- 数字のインパクト：「38兆個の○○」
- 意外性：「実は○○じゃなくて○○だった」