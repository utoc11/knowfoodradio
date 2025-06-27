#!/usr/bin/env python3
"""
NotebookLM用ファイル作成スクリプト
エピソード情報を指定されたグループサイズでまとめて、NotebookLMにアップロードしやすい形式で出力します。
"""

import os
import json
import shutil
from pathlib import Path
from typing import List, Dict
import argparse

class NotebookLMFileCreator:
    def __init__(self, base_dir: str = "/Users/yutokikuchi/dev/knowfoodradio", group_size: int = 10):
        self.base_dir = Path(base_dir)
        self.from_rss_dir = self.base_dir / "from-rss"
        self.output_dir = self.base_dir / "notebooklm"
        self.group_size = group_size
        
    def setup_output_directory(self):
        """出力ディレクトリを作成（既存の場合は削除して再作成）"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        print(f"✅ 出力ディレクトリを作成しました: {self.output_dir}")
        
    def copy_overview_file(self):
        """KNOWフードラジオとは.mdをコピー"""
        source = self.base_dir / "KNOWフードラジオとは.md"
        dest = self.output_dir / "00_KNOWフードラジオとは.md"
        
        if source.exists():
            shutil.copy2(source, dest)
            print(f"✅ 番組概要ファイルをコピーしました: {dest.name}")
        else:
            print(f"⚠️  番組概要ファイルが見つかりません: {source}")
            
    def get_episode_directories(self) -> List[Path]:
        """from-rss内のエピソードディレクトリを取得"""
        if not self.from_rss_dir.exists():
            print(f"❌ from-rssディレクトリが見つかりません: {self.from_rss_dir}")
            return []
            
        episodes = []
        for item in sorted(self.from_rss_dir.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                episodes.append(item)
        
        print(f"📁 {len(episodes)}個のエピソードディレクトリを発見")
        return episodes
        
    def read_episode_data(self, episode_dir: Path) -> Dict:
        """エピソードディレクトリから必要な情報を読み込む"""
        data = {
            "title": episode_dir.name,
            "path": str(episode_dir),
            "content": {}
        }
        
        # 読み込むファイルのリスト（優先順位順）
        files_to_read = [
            ("metadata.json", "metadata"),
            ("summary.md", "summary"),
            ("briefing.md", "briefing"),
            ("highlights.md", "highlights"),
            ("timeline.md", "timeline"),
            ("keywords.txt", "keywords"),
            ("quotes.txt", "quotes"),
            ("questions.txt", "questions")
        ]
        
        for filename, key in files_to_read:
            file_path = episode_dir / filename
            if file_path.exists():
                try:
                    if filename.endswith('.json'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data["content"][key] = json.load(f)
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data["content"][key] = f.read()
                except Exception as e:
                    print(f"  ⚠️  {filename}の読み込みエラー: {e}")
                    
        return data
        
    def format_episode_content(self, episode_data: Dict) -> str:
        """エピソードデータを読みやすい形式にフォーマット"""
        lines = []
        
        # タイトル
        lines.append(f"# 🎙️ {episode_data['title']}")
        lines.append("")
        
        # メタデータ
        if "metadata" in episode_data["content"]:
            meta = episode_data["content"]["metadata"]
            lines.append("## 📊 エピソード情報")
            if "pub_date" in meta:
                lines.append(f"- **配信日**: {meta['pub_date']}")
            if "duration" in meta:
                lines.append(f"- **収録時間**: {meta['duration']}")
            if "episode_number" in meta and meta["episode_number"]:
                lines.append(f"- **エピソード番号**: #{meta['episode_number']}")
            lines.append("")
            
        # サマリー
        if "summary" in episode_data["content"]:
            lines.append("## 📝 要約")
            lines.append(episode_data["content"]["summary"])
            lines.append("")
            
        # ブリーフィング
        if "briefing" in episode_data["content"]:
            lines.append("## 📋 詳細ブリーフィング")
            lines.append(episode_data["content"]["briefing"])
            lines.append("")
            
        # ハイライト
        if "highlights" in episode_data["content"]:
            lines.append("## ✨ ハイライト")
            lines.append(episode_data["content"]["highlights"])
            lines.append("")
            
        # タイムライン
        if "timeline" in episode_data["content"]:
            lines.append("## ⏱️ タイムライン")
            lines.append(episode_data["content"]["timeline"])
            lines.append("")
            
        # キーワード
        if "keywords" in episode_data["content"]:
            lines.append("## 🏷️ キーワード")
            lines.append(episode_data["content"]["keywords"])
            lines.append("")
            
        # 引用
        if "quotes" in episode_data["content"]:
            lines.append("## 💬 印象的な発言")
            lines.append(episode_data["content"]["quotes"])
            lines.append("")
            
        # 質問
        if "questions" in episode_data["content"]:
            lines.append("## ❓ 想定質問")
            lines.append(episode_data["content"]["questions"])
            lines.append("")
            
            
        lines.append("---")
        lines.append("")
        
        return "\n".join(lines)
        
    def create_grouped_files(self, episodes: List[Path]):
        """エピソードをグループ化してファイルを作成"""
        total_episodes = len(episodes)
        total_groups = (total_episodes + self.group_size - 1) // self.group_size
        
        print(f"\n📊 {total_episodes}エピソードを{self.group_size}個ずつ、計{total_groups}ファイルに分割します")
        
        for group_index in range(total_groups):
            start_idx = group_index * self.group_size
            end_idx = min(start_idx + self.group_size, total_episodes)
            group_episodes = episodes[start_idx:end_idx]
            
            # ファイル名を決定（01_episodes_001-010.md のような形式）
            start_num = start_idx + 1
            end_num = end_idx
            filename = f"{group_index + 1:02d}_episodes_{start_num:03d}-{end_num:03d}.md"
            output_path = self.output_dir / filename
            
            print(f"\n📝 {filename}を作成中...")
            
            # グループ内のエピソードデータを収集
            content_lines = []
            content_lines.append(f"# KNOWフードラジオ エピソード集 ({start_num}-{end_num})")
            content_lines.append("")
            content_lines.append(f"このファイルには、KNOWフードラジオのエピソード{start_num}から{end_num}までの情報がまとめられています。")
            content_lines.append("")
            content_lines.append("---")
            content_lines.append("")
            
            for i, episode_dir in enumerate(group_episodes):
                print(f"  - {episode_dir.name}を処理中...")
                episode_data = self.read_episode_data(episode_dir)
                formatted_content = self.format_episode_content(episode_data)
                content_lines.append(formatted_content)
                
            # ファイルに書き出し
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(content_lines))
                
            print(f"  ✅ {filename}を作成しました ({len(group_episodes)}エピソード)")
            
    def create_index_file(self, episodes: List[Path]):
        """全エピソードのインデックスファイルを作成"""
        index_path = self.output_dir / "00_INDEX.md"
        
        lines = []
        lines.append("# KNOWフードラジオ エピソードインデックス")
        lines.append("")
        lines.append(f"全{len(episodes)}エピソードの一覧です。")
        lines.append("")
        
        for i, episode_dir in enumerate(episodes, 1):
            # メタデータを読み込んで日付を取得
            metadata_path = episode_dir / "metadata.json"
            pub_date = ""
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        pub_date = metadata.get("pub_date", "")
                except:
                    pass
                    
            lines.append(f"{i:03d}. {episode_dir.name} ({pub_date})")
            
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        print(f"✅ インデックスファイルを作成しました: {index_path.name}")
        
    def run(self):
        """メイン処理を実行"""
        print("🚀 NotebookLM用ファイル作成を開始します")
        print(f"   グループサイズ: {self.group_size}エピソード/ファイル")
        
        # 1. 出力ディレクトリをセットアップ
        self.setup_output_directory()
        
        # 2. 番組概要ファイルをコピー
        self.copy_overview_file()
        
        # 3. エピソードディレクトリを取得
        episodes = self.get_episode_directories()
        if not episodes:
            print("❌ エピソードが見つかりませんでした")
            return
            
        # 4. インデックスファイルを作成
        self.create_index_file(episodes)
        
        # 5. グループ化したファイルを作成
        self.create_grouped_files(episodes)
        
        # 完了メッセージ
        print("\n✨ 完了しました！")
        print(f"📁 作成されたファイルは以下にあります:")
        print(f"   {self.output_dir}")
        print("\n💡 使い方:")
        print("   1. Finderで上記のフォルダを開く")
        print("   2. すべてのファイルを選択（Cmd+A）")
        print("   3. NotebookLMにドラッグ&ドロップ")


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM用にKNOWフードラジオのエピソード情報をまとめたファイルを作成します"
    )
    parser.add_argument(
        "-g", "--group-size",
        type=int,
        default=10,
        help="1ファイルにまとめるエピソード数（デフォルト: 10）"
    )
    parser.add_argument(
        "-d", "--directory",
        type=str,
        default="/Users/yutokikuchi/dev/knowfoodradio",
        help="KNOWフードラジオのベースディレクトリ"
    )
    
    args = parser.parse_args()
    
    creator = NotebookLMFileCreator(
        base_dir=args.directory,
        group_size=args.group_size
    )
    creator.run()


if __name__ == "__main__":
    main()