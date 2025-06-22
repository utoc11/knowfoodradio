#!/usr/bin/env python3
"""
KNOWフードラジオ - 文字起こし取得スクリプト

RSSフィードから文字起こしデータ（.srtファイル）を取得し、
適切なディレクトリ構造で保存します。

【使用例】
# 最新エピソードを取得（デフォルト）
python fetch_transcript.py

# 特定の日付のエピソードを取得（時刻は無視）
python fetch_transcript.py --date 2024-01-15

# 特定の年月の全エピソードを取得
python fetch_transcript.py --year-month 2024-01

# 期間を指定して取得（from/toは片方だけでも可）
python fetch_transcript.py --from 2024-01-01 --to 2024-03-31
python fetch_transcript.py --from 2024-01-01  # 2024年1月1日以降全て
python fetch_transcript.py --to 2024-03-31    # 2024年3月31日まで全て

# 全エピソードを取得
python fetch_transcript.py --all

# ドライラン（実際にダウンロードせず対象を確認）
python fetch_transcript.py --year-month 2024-01 --dry-run
python fetch_transcript.py --all --dry-run

【pipenv使用時】
pipenv run python fetch_transcript.py --year-month 2024-01
pipenv run fetch  # 最新エピソード（Pipfileにスクリプトとして定義済み）
pipenv run fetch-all  # 全エピソード（Pipfileにスクリプトとして定義済み）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, date
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

import requests


RSS_URL = "https://anchor.fm/s/7637c118/podcast/rss"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FROM_RSS_DIR = os.path.join(BASE_DIR, "from-rss")


def sanitize_filename(filename: str) -> str:
    """ファイル名として使えない文字を置換"""
    # Windowsでも使えるように特殊文字を置換
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    # 連続したアンダースコアを1つに
    sanitized = re.sub(r'_+', '_', sanitized)
    # 先頭・末尾の空白とアンダースコアを削除
    return sanitized.strip('_ ')


def parse_date(date_str: str) -> Optional[date]:
    """RSS形式の日付文字列をdateオブジェクトに変換"""
    try:
        # RSS標準形式: "Mon, 15 Jan 2024 00:00:00 GMT"
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.date()
    except ValueError:
        try:
            # 別の形式を試す
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.date()
        except ValueError:
            print(f"警告: 日付の解析に失敗しました: {date_str}")
            return None


def fetch_rss_feed() -> ET.Element:
    """RSSフィードを取得してパース"""
    print(f"RSSフィードを取得中: {RSS_URL}")
    response = requests.get(RSS_URL)
    response.raise_for_status()
    
    root = ET.fromstring(response.content)
    return root


def extract_episode_info(item: ET.Element) -> Dict:
    """RSSのitemエレメントからエピソード情報を抽出"""
    # 名前空間の定義
    namespaces = {
        'podcast': 'https://podcastindex.org/namespace/1.0',
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    }
    
    # 基本情報の取得
    title = item.findtext('title', '')
    description = item.findtext('description', '')
    pub_date_str = item.findtext('pubDate', '')
    pub_date = parse_date(pub_date_str)
    
    # エピソード番号の抽出（タイトルから）
    episode_match = re.search(r'第(\d+)回', title)
    episode_number = int(episode_match.group(1)) if episode_match else None
    
    # transcriptタグの取得
    transcript_elem = item.find('podcast:transcript', namespaces)
    transcript_url = None
    if transcript_elem is not None:
        transcript_url = transcript_elem.get('url')
    
    # 他の有用な情報
    duration = item.findtext('itunes:duration', '', namespaces)
    author = item.findtext('itunes:author', '', namespaces)
    
    return {
        'title': title,
        'description': description,
        'pub_date': pub_date,
        'pub_date_str': pub_date_str,
        'episode_number': episode_number,
        'transcript_url': transcript_url,
        'duration': duration,
        'author': author
    }


def filter_episodes_by_date(
    episodes: List[Dict],
    date_filter: Optional[str] = None,
    year_month: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict]:
    """日付でエピソードをフィルタリング"""
    filtered = []
    
    for episode in episodes:
        pub_date = episode['pub_date']
        if not pub_date:
            continue
        
        # 特定の日付（時刻無視）
        if date_filter:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            if pub_date == filter_date:
                filtered.append(episode)
        
        # 特定の年月
        elif year_month:
            year, month = map(int, year_month.split('-'))
            if pub_date.year == year and pub_date.month == month:
                filtered.append(episode)
        
        # 期間指定
        elif date_from or date_to:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else date.min
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else date.max
            if from_date <= pub_date <= to_date:
                filtered.append(episode)
        
        # フィルタなし
        else:
            filtered.append(episode)
    
    return filtered


def download_transcript(url: str, save_path: str) -> bool:
    """文字起こしファイルをダウンロード"""
    try:
        print(f"文字起こしをダウンロード中: {url}")
        response = requests.get(url)
        response.raise_for_status()
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # ファイルを保存
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"保存完了: {save_path}")
        return True
    
    except Exception as e:
        print(f"エラー: 文字起こしのダウンロードに失敗しました: {e}")
        return False


def save_metadata(episode_info: Dict, save_dir: str):
    """メタデータをJSON形式で保存"""
    metadata_path = os.path.join(save_dir, 'metadata.json')
    
    # 保存用のメタデータを作成（date型は文字列に変換）
    metadata = episode_info.copy()
    if metadata['pub_date']:
        metadata['pub_date'] = metadata['pub_date'].isoformat()
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"メタデータ保存完了: {metadata_path}")


def process_episode(episode_info: Dict) -> bool:
    """エピソードを処理（ダウンロード・保存）"""
    if not episode_info['transcript_url']:
        print(f"警告: 文字起こしURLが見つかりません: {episode_info['title']}")
        return False
    
    # 保存先ディレクトリの作成
    dir_name = sanitize_filename(episode_info['title'])
    save_dir = os.path.join(FROM_RSS_DIR, dir_name)
    
    # 既に存在する場合はスキップするか確認
    if os.path.exists(save_dir):
        transcript_path = os.path.join(save_dir, 'transcript.srt')
        if os.path.exists(transcript_path):
            print(f"スキップ: 既に存在します - {dir_name}")
            return True
    
    # ディレクトリ作成
    os.makedirs(save_dir, exist_ok=True)
    
    # 文字起こしをダウンロード
    transcript_path = os.path.join(save_dir, 'transcript.srt')
    if download_transcript(episode_info['transcript_url'], transcript_path):
        # メタデータを保存
        save_metadata(episode_info, save_dir)
        return True
    
    return False


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='KNOWフードラジオの文字起こしをRSSから取得'
    )
    
    # フィルタリングオプション
    parser.add_argument(
        '--date',
        help='特定の日付のエピソードを取得 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--year-month',
        help='特定の年月のエピソードを取得 (YYYY-MM)'
    )
    parser.add_argument(
        '--from',
        dest='date_from',
        help='この日付以降のエピソードを取得 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--to',
        dest='date_to',
        help='この日付以前のエピソードを取得 (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='全てのエピソードを取得'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='実際にダウンロードせず、対象エピソードを表示するのみ'
    )
    
    args = parser.parse_args()
    
    # from-rssディレクトリの作成
    os.makedirs(FROM_RSS_DIR, exist_ok=True)
    
    try:
        # RSSフィードを取得
        root = fetch_rss_feed()
        
        # エピソード情報を抽出
        episodes = []
        channel = root.find('channel')
        if channel is None:
            print("エラー: RSSフィードにchannelエレメントが見つかりません")
            sys.exit(1)
        
        for item in channel.findall('item'):
            episode_info = extract_episode_info(item)
            if episode_info:
                episodes.append(episode_info)
        
        print(f"総エピソード数: {len(episodes)}")
        
        # 日付でフィルタリング
        filtered_episodes = filter_episodes_by_date(
            episodes,
            date_filter=args.date,
            year_month=args.year_month,
            date_from=args.date_from,
            date_to=args.date_to
        )
        
        # デフォルト: 最新エピソードのみ
        if not any([args.all, args.date, args.year_month, args.date_from, args.date_to]):
            filtered_episodes = filtered_episodes[:1] if filtered_episodes else []
        
        print(f"処理対象エピソード数: {len(filtered_episodes)}")
        
        # ドライランモード
        if args.dry_run:
            print("\n[ドライランモード] 以下のエピソードが処理対象です:")
            for ep in filtered_episodes:
                print(f"- {ep['title']} ({ep['pub_date']})")
            return
        
        # エピソードを処理
        success_count = 0
        for episode in filtered_episodes:
            print(f"\n処理中: {episode['title']}")
            if process_episode(episode):
                success_count += 1
        
        print(f"\n完了: {success_count}/{len(filtered_episodes)} エピソードを処理しました")
    
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()