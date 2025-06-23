#!/usr/bin/env python3
import json
import os
from datetime import datetime
import re

# エピソード情報を格納するリスト
episodes = []

# from-rssディレクトリのパス
base_dir = "/Users/yutokikuchi/dev/knowfoodradio/from-rss"

# 各ディレクトリを走査
for dir_name in os.listdir(base_dir):
    dir_path = os.path.join(base_dir, dir_name)
    
    # ディレクトリかどうかチェック
    if os.path.isdir(dir_path):
        metadata_path = os.path.join(dir_path, "metadata.json")
        
        # metadata.jsonが存在するかチェック
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                    # エピソード番号を抽出（タイトルから）
                    title = metadata.get('title', '')
                    episode_match = re.match(r'#(\d+(?:\.\d+)?)', title)
                    episode_number = episode_match.group(1) if episode_match else None
                    
                    # エピソード情報を追加
                    episodes.append({
                        'title': title,
                        'pub_date': metadata.get('pub_date', ''),
                        'episode_number': episode_number,
                        'folder': dir_name
                    })
            except Exception as e:
                print(f"エラー: {dir_name} - {e}")

# pubDateでソート（古い順）
episodes.sort(key=lambda x: x['pub_date'] if x['pub_date'] else '9999-12-31')

# 結果を出力
print(f"総エピソード数: {len(episodes)}\n")
print("=== エピソードリスト（pubDate順：古い順）===\n")

for idx, episode in enumerate(episodes, 1):
    print(f"{idx}. {episode['title']}")
    print(f"   公開日: {episode['pub_date']}")
    if episode['episode_number']:
        print(f"   エピソード番号: #{episode['episode_number']}")
    print(f"   フォルダ: {episode['folder']}")
    print()

# JSONファイルとして保存
output_path = os.path.join(base_dir, "episodes_sorted_by_date.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(episodes, f, ensure_ascii=False, indent=2)

print(f"\nソート済みエピソードリストを保存しました: {output_path}")