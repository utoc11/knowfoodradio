#!/usr/bin/env python3
"""
KNOWフードラジオ - 派生テキスト自動生成スクリプト

from-rssディレクトリ内の文字起こしファイル（transcript.srt）から
各種派生テキストを生成します。

使用方法:
python generate_derivatives.py [エピソードディレクトリ名]

例:
python generate_derivatives.py "#30.完ペキな腸内細菌検査は、推定1000万円超！？／腸内細菌相談室 鈴木大輔さん〜後編"
python generate_derivatives.py --all  # 全エピソードを処理
python generate_derivatives.py --missing  # 派生テキストがないエピソードのみ処理
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
import anthropic
from typing import Dict, List, Optional

# APIキーの設定
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# 基本設定
BASE_DIR = Path(__file__).parent
FROM_RSS_DIR = BASE_DIR / "from-rss"
TEMPLATES_DIR = BASE_DIR / "templates"
GUIDELINES_PATH = BASE_DIR / "CONTENT_GUIDELINES.md"


def read_srt(file_path: Path) -> str:
    """SRTファイルを読み込んで文字列として返す"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def read_metadata(episode_dir: Path) -> Dict:
    """メタデータを読み込む"""
    metadata_path = episode_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def read_guidelines() -> str:
    """ガイドラインを読み込む"""
    if GUIDELINES_PATH.exists():
        with open(GUIDELINES_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def generate_with_claude(prompt: str, max_tokens: int = 4000) -> str:
    """Claude APIを使用してテキストを生成"""
    if not ANTHROPIC_API_KEY:
        print("  ⚠️  ANTHROPIC_API_KEY環境変数が設定されていません")
        return ""
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            temperature=0.7,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude API エラー: {e}")
        return ""


def create_derivative_prompt(transcript: str, metadata: Dict, derivative_type: str, guidelines: str) -> str:
    """派生テキスト生成用のプロンプトを作成"""
    
    episode_title = metadata.get('title', '不明なエピソード')
    
    prompts = {
        'summary': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、200-300文字の要約（summary.md）を作成してください。

ガイドライン抜粋：
- ゲスト名と肩書きを明記
- エピソードの核となる発見や数字を含める
- 次も聴きたくなるような締めくくり
- 2-3段落構成で視覚的に読みやすく

文字起こし：
{transcript[:8000]}

要約のみを出力してください。マークダウン記法は使わないでください。""",

        'briefing': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、800-1200文字のブリーフィング・ドキュメント（briefing.md）を作成してください。

ガイドライン抜粋：
- 堅すぎず、でも信頼感のある文体
- エピソードの雰囲気や掛け合いの様子を含める
- 笑いが起きた場面や盛り上がったポイント
- 難しい概念は身近な例えで説明
- 会話の一部から始める、情景描写から始める、問いかけから始めるなど工夫

文字起こし：
{transcript[:10000]}

マークダウン形式で、適切な見出しを付けて出力してください。""",

        'highlights': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、切り抜き用のハイライト（highlights.md）を作成してください。

ガイドライン：
- 5つのハイライトを選定
- 各ハイライトは30秒〜1分30秒
- インパクトのある数字や事実
- 笑いや驚きの反応がある場面
- 「へぇ〜」となる豆知識

文字起こし：
{transcript[:10000]}

各ハイライトに以下を含めてください：
- タイトル
- 時間（開始〜終了）
- 内容説明
- なぜその部分が面白いのか

マークダウン形式で出力してください。""",

        'timeline': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、目次（timeline.md）を作成してください。

ガイドライン：
- mm:ss 見出し の形式
- 内容が一目で分かる見出し
- 具体的な数字や固有名詞を活用
- 感情や反応を含めると親近感UP

良い例：
- 16:00 【衝撃】完全な検査は最低1000万円！
- 19:20 カルビーがグラノーラで狙う一石二鳥戦略
- 33:30 父親の腸内細菌も子どもに影響する新事実

文字起こし：
{transcript}

# エピソード目次

という見出しから始めて、時系列で出力してください。""",

        'instagram': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、Instagram投稿文を作成してください。

ガイドライン：
- 150文字程度
- 絵文字は適度に使用
- ハッシュタグは5-7個
- 改行で読みやすく

文字起こし抜粋：
{transcript[:5000]}

投稿文のみを出力してください。""",

        'x': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、X（旧Twitter）投稿文を作成してください。

ガイドライン：
- 140文字以内厳守
- フックとなる一文から始める
- ハッシュタグは2-3個

文字起こし抜粋：
{transcript[:5000]}

投稿文のみを出力してください。""",

        'keywords': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、キーワードリスト（keywords.txt）を作成してください。

カテゴリー分けして整理：
- 人物
- 専門用語
- 企業・サービス
- トピック・概念
- 数字・データ

文字起こし抜粋：
{transcript[:8000]}

各カテゴリーごとにキーワードを列挙してください。""",

        'quotes': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、印象的な引用集（quotes.txt）を作成してください。

ガイドライン：
- 前後の文脈が分からなくても理解できる引用
- インパクトと共感性のバランス
- SNSでシェアされやすい長さ
- 話者名を明記（ゲスト名、TTさん、ゆとさん等）

文字起こし：
{transcript[:10000]}

# 印象的な引用集

という見出しから始めて、カテゴリー分けして出力してください。""",

        'questions': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、リスナーからの想定質問（questions.txt）を作成してください。

以下の観点で10個程度：
- リスナーが実際に抱きそうな疑問
- 次回エピソードの企画につながる提案
- 実践的で具体的な質問

文字起こし抜粋：
{transcript[:8000]}

# リスナーからの想定質問

という見出しから始めて出力してください。""",

        'audience_engagement': f"""以下のポッドキャストエピソード「{episode_title}」の文字起こしから、SNS用のリスナー問いかけ文（audience_engagement.txt）を作成してください。

以下の種類を含める：
- Yes/Noで答えられる質問（5個）
- 体験をシェアしたくなる質問（5個）
- 議論を呼びそうなトピック（3個）

文字起こし抜粋：
{transcript[:8000]}

# リスナーへの問いかけ（SNS投稿用）

という見出しから始めて、カテゴリー分けして出力してください。""",

        'links': f"""以下のポッドキャストエピソード「{episode_title}」の情報から、関連リンク集（links.md）を作成してください。

メタデータ：
{json.dumps(metadata, ensure_ascii=False, indent=2)}

以下のカテゴリーで整理：
- ゲスト関連
- 番組関連
- エピソード内で言及された企業・サービス
- 参考情報

# 関連リンク集

という見出しから始めて、各リンクに説明を添えて出力してください。
注意：実際のURLは推測せず、プレースホルダー（[URL]）を使用してください。"""
    }
    
    return prompts.get(derivative_type, "")


def save_file(content: str, file_path: Path):
    """ファイルを保存"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✓ {file_path.name}")


def process_episode(episode_dir: Path, force: bool = False) -> bool:
    """エピソードの派生テキストを生成"""
    print(f"\n処理中: {episode_dir.name}")
    
    # 文字起こしファイルの確認
    transcript_path = episode_dir / "transcript.srt"
    if not transcript_path.exists():
        print("  ⚠️  文字起こしファイルが見つかりません")
        return False
    
    # 既に処理済みかチェック
    if not force and (episode_dir / "summary.md").exists():
        print("  ⏭️  既に処理済み（--forceで再生成可能）")
        return True
    
    # ファイル読み込み
    transcript = read_srt(transcript_path)
    metadata = read_metadata(episode_dir)
    guidelines = read_guidelines()
    
    # 各種派生テキストを生成
    derivatives = {
        'summary.md': 'summary',
        'briefing.md': 'briefing',
        'highlights.md': 'highlights',
        'timeline.md': 'timeline',
        'social/instagram.txt': 'instagram',
        'social/x.txt': 'x',
        'keywords.txt': 'keywords',
        'quotes.txt': 'quotes',
        'questions.txt': 'questions',
        'audience_engagement.txt': 'audience_engagement',
        'links.md': 'links'
    }
    
    print("  生成中...")
    for file_name, derivative_type in derivatives.items():
        prompt = create_derivative_prompt(transcript, metadata, derivative_type, guidelines)
        if prompt:
            content = generate_with_claude(prompt)
            if content:
                save_file(content, episode_dir / file_name)
            else:
                print(f"  ❌ {file_name} の生成に失敗")
    
    return True


def find_episodes_without_derivatives() -> List[Path]:
    """派生テキストがないエピソードを検索"""
    episodes = []
    for episode_dir in FROM_RSS_DIR.iterdir():
        if episode_dir.is_dir() and not episode_dir.name.startswith('.'):
            # 文字起こしがあって、summaryがない場合
            if (episode_dir / "transcript.srt").exists() and not (episode_dir / "summary.md").exists():
                episodes.append(episode_dir)
    return episodes


def main():
    parser = argparse.ArgumentParser(
        description='KNOWフードラジオの派生テキストを生成'
    )
    
    parser.add_argument(
        'episode',
        nargs='?',
        help='エピソードディレクトリ名'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='全エピソードを処理'
    )
    parser.add_argument(
        '--missing',
        action='store_true',
        help='派生テキストがないエピソードのみ処理'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='既存のファイルを上書き'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='処理するエピソード数の上限（デバッグ用）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際に生成せず、対象エピソードを表示'
    )
    
    args = parser.parse_args()
    
    # 処理対象のエピソードを決定
    episodes_to_process = []
    
    if args.all:
        for episode_dir in FROM_RSS_DIR.iterdir():
            if episode_dir.is_dir() and not episode_dir.name.startswith('.'):
                if (episode_dir / "transcript.srt").exists():
                    episodes_to_process.append(episode_dir)
    
    elif args.missing:
        episodes_to_process = find_episodes_without_derivatives()
    
    elif args.episode:
        episode_dir = FROM_RSS_DIR / args.episode
        if episode_dir.exists():
            episodes_to_process.append(episode_dir)
        else:
            print(f"エラー: エピソードが見つかりません: {args.episode}")
            sys.exit(1)
    
    else:
        print("エピソード名を指定するか、--all または --missing オプションを使用してください")
        parser.print_help()
        sys.exit(1)
    
    # 処理数の制限
    if args.limit > 0:
        episodes_to_process = episodes_to_process[:args.limit]
    
    print(f"処理対象: {len(episodes_to_process)} エピソード")
    
    # ドライランモード
    if args.dry_run:
        print("\n[ドライランモード] 以下のエピソードが処理対象です:")
        for episode_dir in episodes_to_process:
            print(f"- {episode_dir.name}")
        return
    
    # 各エピソードを処理
    success_count = 0
    for episode_dir in episodes_to_process:
        if process_episode(episode_dir, args.force):
            success_count += 1
        print("")  # 空行で区切る
    
    print(f"\n完了: {success_count}/{len(episodes_to_process)} エピソードを処理しました")


if __name__ == '__main__':
    main()