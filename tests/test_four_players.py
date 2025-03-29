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

def test_four_players():
    """4人プレイヤーのテスト - 標準的なGame Point計算ロジックの検証"""
    print("===== 4人プレイヤー計算テスト =====")
    
    # テスト用データ (4人プレイヤー)
    test_scores = [
        {
            'member_id': 1,
            'front_score': 45,
            'front_putt': 15,
            'front_game_pt': 30,  # 1位
            'back_score': 46,
            'back_putt': 17,
            'back_game_pt': 30,   # 1位
            'member': {'name': 'プレイヤーA'}
        },
        {
            'member_id': 2,
            'front_score': 47,
            'front_putt': 16,
            'front_game_pt': 10,  # 2位
            'back_score': 48,
            'back_putt': 18,
            'back_game_pt': 10,   # 2位
            'member': {'name': 'プレイヤーB'}
        },
        {
            'member_id': 3,
            'front_score': 49,
            'front_putt': 20,
            'front_game_pt': -10, # 3位
            'back_score': 50,
            'back_putt': 19,
            'back_game_pt': -10,  # 3位
            'member': {'name': 'プレイヤーC'}
        },
        {
            'member_id': 4,
            'front_score': 52,
            'front_putt': 22,
            'front_game_pt': -30, # 4位
            'back_score': 53,
            'back_putt': 21,
            'back_game_pt': -30,  # 4位
            'member': {'name': 'プレイヤーD'}
        }
    ]
    
    # ラウンド情報
    test_round = {
        'round_id': 999,
        'date_played': '2025-03-30',
        'course_name': 'テストコース',
        'num_players': 4,  # 4人プレイ
        'has_extra': False
    }
    
    # ハンディキャップ情報 (全プレイヤー間の組み合わせ)
    test_handicaps = []
    for i in range(1, 5):
        for j in range(i+1, 5):
            test_handicaps.append({
                'player_1_id': i,
                'player_2_id': j,
                'player_1_to_2': 0,
                'player_2_to_1': 0,
                'total_only': False
            })
    
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
        print(f"  プレイヤー: {player_info['Player']}")
        print(f"    フロント/バックゲームポイント: {player_info['Front GP']}/{player_info['Back GP']}")
        print(f"    Game Pt: {player_info['Game Pt']} (4人プレイではフロント+バックの合計)")
        print(f"    Match Pt: {player_info['Match Pt']}")
        print(f"    Putt Pt: {player_info['Putt Pt']}")
        print(f"    Total Pt: {player_info['Total Pt']}")
        print(f"    -" * 30)
    
    # 4人プレイヤーの計算を検証
    print("\n4人プレイヤーのGame Point計算検証:")
    for player_id, player_info in updated_player_data.items():
        front_gp = player_info['Front GP']
        back_gp = player_info['Back GP']
        game_pt = player_info['Game Pt']
        
        # 4人プレイでは単純合計
        expected_game_pt = front_gp + back_gp
        
        print(f"  プレイヤー {player_info['Player']}:")
        print(f"    Front GP: {front_gp}")
        print(f"    Back GP: {back_gp}")
        print(f"    期待値: {front_gp} + {back_gp} = {expected_game_pt}")
        print(f"    実際値: {game_pt}")
        print(f"    検証結果: {'✓ 正しい' if expected_game_pt == game_pt else '✗ 誤差あり'}")
    
    # マッチポイント合計の検証
    print("\nマッチポイント合計の検証:")
    match_pt_sum = sum(player_info['Match Pt'] for player_info in updated_player_data.values())
    print(f"  全プレイヤーのMatch Pt合計: {match_pt_sum} (理論上は0になるべき)")
    
    print("\nテスト完了")
    return updated_player_data

if __name__ == "__main__":
    test_four_players()
