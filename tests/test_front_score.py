import os
import sys
import json
from datetime import datetime

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.supabase_client import get_supabase_client, get_scores_with_fallback
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.data_formatter import initialize_player_data

def test_front_score():
    """フロントスコア入力のテスト"""
    print("===== フロントスコア計算テスト =====")
    
    # テスト用データ - 3人プレイヤーに変更
    test_scores = [
        {
            'member_id': 1,
            'front_score': 45,
            'front_putt': 18,
            'front_game_pt': 30,  # 1位
            'member': {'name': 'テストプレイヤー1'}
        },
        {
            'member_id': 2,
            'front_score': 48,
            'front_putt': 16,
            'front_game_pt': 0,   # 2位
            'member': {'name': 'テストプレイヤー2'}
        },
        {
            'member_id': 3,
            'front_score': 52,
            'front_putt': 20,
            'front_game_pt': -30, # 3位
            'member': {'name': 'テストプレイヤー3'}
        }
    ]
    
    # ラウンド情報 - 3人プレイに変更
    test_round = {
        'round_id': 999,
        'date_played': '2025-03-30',
        'course_name': 'テストコース',
        'num_players': 3,  # 3人プレイに変更
        'has_extra': False
    }
    
    # ハンディキャップ情報 - 3人分に更新
    test_handicaps = [
        {
            'player_1_id': 1,
            'player_2_id': 2,
            'player_1_to_2': 0,
            'player_2_to_1': 0,
            'total_only': False
        },
        {
            'player_1_id': 1,
            'player_2_id': 3,
            'player_1_to_2': 0,
            'player_2_to_1': 0,
            'total_only': False
        },
        {
            'player_1_id': 2,
            'player_2_id': 3,
            'player_1_to_2': 0,
            'player_2_to_1': 0,
            'total_only': False
        }
    ]
    
    # プレイヤーデータの初期化
    player_data = initialize_player_data(test_scores, {})
    player_ids = sorted(list(player_data.keys()))
    
    # ハンディキャップ辞書作成
    handicaps = {}
    total_only_set = set()
    for h in test_handicaps:
        handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
        handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
        if h.get('total_only'):
            total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
    
    # ポイント計算テスト
    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, test_round)
    
    # 計算結果を表示
    print("\n計算結果:")
    for player_id, player_info in updated_player_data.items():
        print(f"  Player: {player_info['Player']}")
        print(f"    Front Score: {player_info['Front Score']}")
        print(f"    Match Front: {player_info['Match Front']}")
        print(f"    Front GP: {player_info['Front GP']}")
        print(f"    Putt Pt: {player_info['Putt Pt']}")
    
    print("\nテスト完了")
    return updated_player_data

if __name__ == "__main__":
    test_front_score()
