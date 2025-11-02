#!/usr/bin/env python3
"""
文字起こしファイル（transcript.srt）から「へぇ」「へー」「へえ」などの
リアクションを抽出して、エピソードごとにカウントするスクリプト
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import json


class HeeAnalyzer:
    """「へぇ」リアクションを解析するクラス"""

    def __init__(self, context_blocks: int = 0):
        """
        Args:
            context_blocks: 前後に含めるブロック数（0=前後なし、2=前後2ブロックずつ）
        """
        # スペース・改行・全角スペースを含む可能性を考慮した「へぇ」パターン
        # 例: "へ え"、"へ\nえ"、"へ　ー"、"へええ" など
        #
        # パターン設計の考慮事項:
        # 1. 1文字ごとにスペースが入る: "へ え"
        # 2. 改行が入る: "へ\nえ"
        # 3. 全角スペースが入る: "へ　え"
        # 4. 複数の「え/ー/ぇ」が続く: "へええ"、"へえー"
        # 5. スペースと改行が混在: "へ \n え"
        self.hee_patterns = [
            # ひらがな版: へ + (ぇ/え/ー)の組み合わせ
            # [\s\u3000\n]* = 半角スペース、全角スペース(\u3000)、改行(\n)のいずれかが0回以上
            # [ぇえー] が1〜3回繰り返される（へええ まで対応）
            r'へ[\s\u3000\n]*[ぇえー][\s\u3000\n]*[ぇえー]?[\s\u3000\n]*[ぇえー]?',

            # カタカナ版: ヘ + (ェ/エ/ー)の組み合わせ
            r'ヘ[\s\u3000\n]*[ェエー][\s\u3000\n]*[ェエー]?[\s\u3000\n]*[ェエー]?',
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.hee_patterns]
        self.context_blocks = context_blocks

    def extract_text_from_srt(self, srt_path: Path) -> str:
        """SRTファイルからテキスト部分のみを抽出"""
        with open(srt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        text_parts = []
        skip_next = False

        for line in lines:
            line = line.strip()

            # 空行はスキップ
            if not line:
                skip_next = False
                continue

            # 番号行（数字のみ）をスキップ
            if line.isdigit():
                skip_next = True
                continue

            # タイムスタンプ行をスキップ
            if '-->' in line:
                skip_next = True
                continue

            # テキスト行を収集
            if not skip_next:
                text_parts.append(line)

        return ' '.join(text_parts)

    def find_hee_with_context(self, srt_path: Path, context_blocks: int = 0) -> List[Dict[str, str]]:
        """「へぇ」が含まれる箇所をタイムスタンプとともに抽出

        Args:
            srt_path: SRTファイルのパス
            context_blocks: 前後に含めるブロック数（0=前後なし、1=前後1ブロックずつ、2=前後2ブロックずつ）
        """
        results = []

        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # SRTのブロックごとに分割（空行で区切られる）
        blocks = content.strip().split('\n\n')

        # 各ブロックをパース
        parsed_blocks = []
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # タイムスタンプ行を探す
            timestamp = None
            text_lines = []

            for line in lines:
                if '-->' in line:
                    timestamp = line.strip()
                elif not line.isdigit():  # 番号行でない
                    text_lines.append(line.strip())

            if timestamp:
                parsed_blocks.append({
                    'timestamp': timestamp,
                    'text': ' '.join(text_lines)
                })

        # 「へぇ」を含むブロックを検索
        for i, block_data in enumerate(parsed_blocks):
            full_text = block_data['text']

            # 「へぇ」パターンをチェック
            matched = False
            for pattern in self.compiled_patterns:
                if pattern.search(full_text):
                    matched = True
                    break

            if not matched:
                continue

            # 前後のコンテキストを追加
            start_idx = max(0, i - context_blocks)
            end_idx = min(len(parsed_blocks), i + context_blocks + 1)

            context_texts = []
            for j in range(start_idx, end_idx):
                context_texts.append(parsed_blocks[j]['text'])

            context_text = ' '.join(context_texts)

            results.append({
                'timestamp': block_data['timestamp'],
                'text': full_text,
                'cleaned_text': full_text.replace(' ', '').replace('　', ''),
                'context': context_text.replace(' ', '').replace('　', '') if context_blocks > 0 else None
            })

        return results

    def analyze_episode(self, episode_dir: Path) -> Dict:
        """1エピソードを解析"""
        srt_path = episode_dir / 'transcript.srt'

        if not srt_path.exists():
            return None

        hee_instances = self.find_hee_with_context(srt_path, self.context_blocks)

        return {
            'episode_name': episode_dir.name,
            'count': len(hee_instances),
            'instances': hee_instances
        }

    def analyze_all_episodes(self, from_rss_dir: Path) -> List[Dict]:
        """from-rss配下の全エピソードを解析"""
        results = []

        # ディレクトリを名前順にソート
        episode_dirs = sorted([d for d in from_rss_dir.iterdir() if d.is_dir()])

        for episode_dir in episode_dirs:
            result = self.analyze_episode(episode_dir)
            if result:
                results.append(result)

        return results

    def print_summary(self, results: List[Dict], show_details: bool = False):
        """結果サマリを出力"""
        print("=" * 80)
        print("「へぇ」リアクション解析結果")
        print("=" * 80)
        print()

        total_count = sum(r['count'] for r in results)
        episodes_with_hee = sum(1 for r in results if r['count'] > 0)

        print(f"解析エピソード数: {len(results)}")
        print(f"「へぇ」を含むエピソード数: {episodes_with_hee}")
        print(f"「へぇ」総出現回数: {total_count}")
        print()

        # エピソードごとの集計
        print("-" * 80)
        print("エピソードごとの「へぇ」カウント")
        print("-" * 80)

        for result in results:
            if result['count'] > 0:
                print(f"[{result['count']:2d}回] {result['episode_name']}")

                if show_details and result['instances']:
                    for instance in result['instances']:
                        # タイムスタンプを見やすく整形
                        time_range = instance['timestamp'].split(' --> ')
                        start_time = time_range[0] if len(time_range) > 0 else ''

                        # コンテキストがあればそれを表示、なければcleaned_text
                        display_text = instance.get('context') or instance['cleaned_text']
                        print(f"  └ {start_time}: {display_text[:100]}...")
                    print()

        print()
        print("=" * 80)

    def export_to_json(self, results: List[Dict], output_path: Path):
        """結果をJSON形式でエクスポート"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"結果をJSONファイルに出力しました: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='文字起こしファイルから「へぇ」リアクションを抽出・集計するツール'
    )
    parser.add_argument(
        'episode',
        nargs='?',
        help='特定のエピソード名（例: "#32.機能性表示食品は誰のため？開発者目線で見るトクホとの違い"）'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='全エピソードを解析'
    )
    parser.add_argument(
        '--details',
        action='store_true',
        help='詳細情報（タイムスタンプと文脈）を表示'
    )
    parser.add_argument(
        '--json',
        type=str,
        help='結果をJSON形式で出力（ファイルパスを指定）'
    )
    parser.add_argument(
        '--context',
        type=int,
        default=2,
        help='前後に含めるブロック数（デフォルト: 2）。0にすると前後なし'
    )

    args = parser.parse_args()

    # プロジェクトルートの設定
    script_dir = Path(__file__).parent
    from_rss_dir = script_dir / 'from-rss'

    if not from_rss_dir.exists():
        print(f"エラー: from-rssディレクトリが見つかりません: {from_rss_dir}")
        return

    analyzer = HeeAnalyzer(context_blocks=args.context)

    # 実行モードの判定
    if args.all:
        # 全エピソード解析
        print("全エピソードを解析中...")
        results = analyzer.analyze_all_episodes(from_rss_dir)
    elif args.episode:
        # 特定エピソード解析
        episode_dir = from_rss_dir / args.episode
        if not episode_dir.exists():
            print(f"エラー: エピソードが見つかりません: {episode_dir}")
            # 候補を表示
            print("\n利用可能なエピソード:")
            for d in sorted(from_rss_dir.iterdir()):
                if d.is_dir():
                    print(f"  - {d.name}")
            return

        result = analyzer.analyze_episode(episode_dir)
        results = [result] if result else []
    else:
        # 引数なしの場合はヘルプを表示
        parser.print_help()
        print("\n使用例:")
        print("  # 全エピソードを解析")
        print("  python analyze_hee.py --all")
        print()
        print("  # 詳細情報も表示")
        print("  python analyze_hee.py --all --details")
        print()
        print("  # 特定のエピソードを解析")
        print('  python analyze_hee.py "#32.機能性表示食品は誰のため？開発者目線で見るトクホとの違い"')
        print()
        print("  # JSON形式で出力")
        print("  python analyze_hee.py --all --json hee_analysis.json")
        return

    # 結果の表示
    analyzer.print_summary(results, show_details=args.details)

    # JSON出力
    if args.json:
        output_path = Path(args.json)
        analyzer.export_to_json(results, output_path)


if __name__ == '__main__':
    main()
