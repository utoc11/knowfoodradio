#!/usr/bin/env python3
"""
簡易版派生テキスト生成スクリプト

文字起こしから基本的な派生テキストを生成します。
Claude APIが利用できない場合のフォールバック用。
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
import sys


BASE_DIR = Path(__file__).parent
FROM_RSS_DIR = BASE_DIR / "from-rss"


def parse_srt(srt_content: str) -> list:
    """SRTファイルをパースして、タイムスタンプとテキストを抽出"""
    entries = []
    lines = srt_content.strip().split('\n')
    i = 0
    
    while i < len(lines):
        # インデックスをスキップ
        if lines[i].strip().isdigit():
            i += 1
            
            # タイムスタンプ
            if i < len(lines) and ' --> ' in lines[i]:
                time_match = re.match(r'(\d{2}:\d{2}:\d{2}),\d{3} --> (\d{2}:\d{2}:\d{2}),\d{3}', lines[i])
                if time_match:
                    start_time = time_match.group(1)
                    i += 1
                    
                    # テキスト（複数行の場合あり）
                    text_lines = []
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                        text_lines.append(lines[i].strip())
                        i += 1
                    
                    if text_lines:
                        entries.append({
                            'time': start_time,
                            'text': ' '.join(text_lines)
                        })
        else:
            i += 1
    
    return entries


def extract_speakers(text: str) -> list:
    """テキストから話者を抽出"""
    speakers = []
    if 'TTです' in text or 'TT:' in text:
        speakers.append('TTさん')
    if 'ゆとです' in text or 'ゆと:' in text:
        speakers.append('ゆとさん')
    # ゲストの検出（「さん」で終わる場合が多い）
    guest_pattern = r'([ぁ-んァ-ヶー一-龠]+)さん'
    matches = re.findall(guest_pattern, text)
    for match in matches:
        if match not in ['TT', 'ゆと'] and len(match) > 1:
            speakers.append(f'{match}さん')
    return list(set(speakers))


def generate_summary(entries: list, metadata: dict) -> str:
    """要約を生成"""
    title = metadata.get('title', '')
    
    # 最初の5分間のテキストを結合
    early_text = ' '.join([e['text'] for e in entries[:50]])
    
    # ゲストの検出
    speakers = extract_speakers(early_text)
    guest = None
    for speaker in speakers:
        if speaker not in ['TTさん', 'ゆとさん']:
            guest = speaker
            break
    
    # キーワード抽出
    keywords = []
    if '円' in early_text:
        money_match = re.search(r'(\d+[万千億]?円)', early_text)
        if money_match:
            keywords.append(money_match.group(1))
    
    numbers = re.findall(r'(\d+[%％]|\d+倍|\d+個|\d+人)', early_text)
    keywords.extend(numbers[:2])
    
    # 要約作成
    summary_parts = []
    
    if guest:
        summary_parts.append(f"{guest}をゲストに迎えたエピソード。")
    
    # タイトルから主要テーマを抽出
    if '〜' in title:
        theme = title.split('〜')[0].split('／')[0]
        summary_parts.append(f"{theme}について深く掘り下げる。")
    
    if keywords:
        summary_parts.append(f"話題の中心は{', '.join(keywords[:2])}など。")
    
    summary_parts.append("科学とビジネスの視点から食の世界を探求する内容となっている。")
    
    return '\n\n'.join(summary_parts)


def generate_timeline(entries: list) -> str:
    """タイムラインを生成"""
    timeline = ["# エピソード目次\n"]
    
    # 5分ごとにセクションを作成
    section_interval = 300  # 5分 = 300秒
    current_section = 0
    section_texts = []
    
    for entry in entries:
        time_parts = entry['time'].split(':')
        total_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
        section = total_seconds // section_interval
        
        if section > current_section:
            # セクションのタイトルを生成
            if section_texts:
                # 最も特徴的なキーワードを探す
                combined_text = ' '.join(section_texts)
                
                # 数字を含む表現を優先
                number_match = re.search(r'(\d+[万千億]?円|\d+[%％]|\d+倍|\d+個)', combined_text)
                if number_match:
                    highlight = number_match.group(1)
                    timeline.append(f"{current_section * 5:02d}:00 {highlight}が話題に")
                else:
                    # 疑問文を探す
                    question_match = re.search(r'([^。？！]+[？?])', combined_text)
                    if question_match:
                        timeline.append(f"{current_section * 5:02d}:00 {question_match.group(1)}")
                    else:
                        # 一般的なトピック
                        timeline.append(f"{current_section * 5:02d}:00 話題は続く")
            
            current_section = section
            section_texts = []
        
        section_texts.append(entry['text'])
    
    return '\n'.join(timeline)


def generate_keywords(entries: list, metadata: dict) -> str:
    """キーワードを抽出"""
    full_text = ' '.join([e['text'] for e in entries])
    
    keywords = {
        '人物': [],
        '専門用語': [],
        '企業・サービス': [],
        'トピック・概念': [],
        '数字・データ': []
    }
    
    # 人物
    person_pattern = r'([ぁ-んァ-ヶー一-龠]+)さん'
    persons = re.findall(person_pattern, full_text)
    keywords['人物'] = list(set([p for p in persons if len(p) > 1]))[:5]
    
    # 数字・データ
    numbers = re.findall(r'(\d+[万千億]?円|\d+[%％]|\d+倍|\d+個|\d+人)', full_text)
    keywords['数字・データ'] = list(set(numbers))[:5]
    
    # 企業名（カタカナ）
    companies = re.findall(r'([ァ-ヶー]{3,})', full_text)
    keywords['企業・サービス'] = list(set([c for c in companies if len(c) < 10]))[:5]
    
    # 専門用語（漢字が多い）
    terms = re.findall(r'([一-龠]{3,6})', full_text)
    keywords['専門用語'] = list(set(terms))[:10]
    
    # フォーマット
    result = []
    for category, words in keywords.items():
        if words:
            result.append(f"## {category}")
            for word in words:
                result.append(f"- {word}")
            result.append("")
    
    return '\n'.join(result)


def generate_instagram_post(entries: list, metadata: dict) -> str:
    """Instagram投稿文を生成"""
    title = metadata.get('title', '')
    
    # 最初の興味深い数字や事実を探す
    highlight = None
    for entry in entries[:30]:
        number_match = re.search(r'(\d+[万千億]?円|\d+[%％])', entry['text'])
        if number_match:
            highlight = number_match.group(1)
            break
    
    post = []
    if highlight:
        post.append(f"【{highlight}】って知ってました？🤔")
    else:
        post.append("【今週のKNOWフードラジオ】🎙️")
    
    post.append("")
    post.append(f"今回のテーマは\n「{title.split('／')[0] if '／' in title else title}」")
    post.append("")
    post.append("詳しくはポッドキャストで！")
    post.append("プロフィールのリンクから聴けます📻")
    post.append("")
    post.append("#KNOWフードラジオ #ポッドキャスト #食の科学")
    
    return '\n'.join(post)


def generate_x_post(entries: list, metadata: dict) -> str:
    """X投稿文を生成"""
    title = metadata.get('title', '')
    
    # 数字を含む興味深い事実を探す
    for entry in entries[:20]:
        number_match = re.search(r'(\d+[万千億]?円|\d+[%％])', entry['text'])
        if number_match:
            return f"{number_match.group(1)}!? 今週のKNOWフードラジオは衝撃の内容でした。\n\n{title}\n\n#KNOWフードラジオ"
    
    # デフォルト
    short_title = title.split('／')[0] if '／' in title else title
    return f"🎙️ {short_title}\n\n今週のKNOWフードラジオ配信中！\n#KNOWフードラジオ"


def generate_quotes(entries: list) -> str:
    """印象的な引用を抽出"""
    quotes = ["# 印象的な引用集\n"]
    
    # 疑問文を探す
    questions = []
    for entry in entries:
        if '？' in entry['text'] or '?' in entry['text']:
            if 10 < len(entry['text']) < 50:
                questions.append(entry['text'])
    
    if questions:
        quotes.append("## 興味深い問いかけ")
        for q in questions[:5]:
            quotes.append(f"「{q}」")
            quotes.append("")
    
    # 数字を含む発言
    number_quotes = []
    for entry in entries:
        if re.search(r'\d+[万千億]?円|\d+[%％]|\d+倍', entry['text']):
            if 20 < len(entry['text']) < 80:
                number_quotes.append(entry['text'])
    
    if number_quotes:
        quotes.append("## 衝撃の数字")
        for nq in number_quotes[:3]:
            quotes.append(f"「{nq}」")
            quotes.append("")
    
    return '\n'.join(quotes)


def generate_links(metadata: dict) -> str:
    """関連リンク集を生成"""
    links = ["# 関連リンク集\n"]
    
    links.append("## 番組関連")
    links.append("- KNOWフードラジオ Instagram: @knowfoodradio")
    links.append("- お便りフォーム: [URL]")
    links.append("- Spotifyプレイリスト: [URL]")
    links.append("")
    
    # ゲストがいる場合
    title = metadata.get('title', '')
    if '／' in title:
        guest_info = title.split('／')[1]
        if 'さん' in guest_info:
            links.append("## ゲスト関連")
            links.append(f"- {guest_info}の情報: [URL]")
            links.append("")
    
    return '\n'.join(links)


def process_episode(episode_dir: Path) -> bool:
    """エピソードの派生テキストを生成"""
    print(f"処理中: {episode_dir.name}")
    
    # 文字起こしファイルの確認
    transcript_path = episode_dir / "transcript.srt"
    if not transcript_path.exists():
        print("  ⚠️  文字起こしファイルが見つかりません")
        return False
    
    # 既に処理済みかチェック
    if (episode_dir / "summary.md").exists():
        print("  ⏭️  既に処理済み")
        return True
    
    try:
        # ファイル読み込み
        with open(transcript_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # メタデータ読み込み
        metadata_path = episode_dir / "metadata.json"
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        
        # SRTパース
        entries = parse_srt(srt_content)
        if not entries:
            print("  ⚠️  文字起こしの解析に失敗")
            return False
        
        # 各種ファイル生成
        files_to_generate = {
            'summary.md': generate_summary(entries, metadata),
            'timeline.md': generate_timeline(entries),
            'keywords.txt': generate_keywords(entries, metadata),
            'social/instagram.txt': generate_instagram_post(entries, metadata),
            'social/x.txt': generate_x_post(entries, metadata),
            'quotes.txt': generate_quotes(entries),
            'links.md': generate_links(metadata)
        }
        
        # ファイル保存
        for file_name, content in files_to_generate.items():
            file_path = episode_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ {file_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False


def main():
    # コマンドライン引数の処理
    import argparse
    parser = argparse.ArgumentParser(description='簡易版派生テキスト生成')
    parser.add_argument('--limit', type=int, default=30, help='処理するエピソード数の上限')
    args = parser.parse_args()
    
    # 派生テキストがないエピソードを検索
    episodes_to_process = []
    for episode_dir in FROM_RSS_DIR.iterdir():
        if episode_dir.is_dir() and not episode_dir.name.startswith('.'):
            if (episode_dir / "transcript.srt").exists() and not (episode_dir / "summary.md").exists():
                episodes_to_process.append(episode_dir)
    
    # 処理数を制限
    total_episodes = len(episodes_to_process)
    episodes_to_process = episodes_to_process[:args.limit]
    
    print(f"処理対象: {len(episodes_to_process)} エピソード（全{total_episodes}エピソード中）")
    
    # 各エピソードを処理
    success_count = 0
    for i, episode_dir in enumerate(episodes_to_process):
        print(f"\n[{i+1}/{len(episodes_to_process)}]", end=" ")
        if process_episode(episode_dir):
            success_count += 1
    
    print(f"\n\n完了: {success_count}/{len(episodes_to_process)} エピソードを処理しました")
    if total_episodes > args.limit:
        print(f"残り {total_episodes - args.limit} エピソードは未処理です")


if __name__ == '__main__':
    main()