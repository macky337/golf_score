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

def test_three_players():
    """3人プレイヤーのテスト - 特殊なGame Point計算ロジックの検証"""
    print("===== 3人プレイヤー計算テスト =====")
    
    # テスト用データ (3人プレイヤー)
    test_scores = [
        {
            'member_id': 1,
            'front_score': 45,
            'front_putt': 18,
            'front_game_pt': 30,  # 1位
            'back_score': 46,
            'back_putt': 17,
            'back_game_pt': 30,   # 1位
            'extra_score': 4,
            'extra_putt': 2,
            'extra_game_pt': 30,  # 1位
            'member': {'name': 'プレイヤーA'}
        },
        {
            'member_id': 2,
            'front_score': 48,
            'front_putt': 16,
            'front_game_pt': 0,   # 2位
            'back_score': 47,
            'back_putt': 19,
            'back_game_pt': 0,    # 2位
            'extra_score': 5,
            'extra_putt': 3,
            'extra_game_pt': 0,   # 2位
            'member': {'name': 'プレイヤーB'}
        },
        {
            'member_id': 3,
            'front_score': 49,
            'front_putt': 20,
            'front_game_pt': -30, # 3位
            'back_score': 50,
            'back_putt': 21,
            'back_game_pt': -30,  # 3位
            'extra_score': 6,
            'extra_putt': 4,
            'extra_game_pt': -30, # 3位
            'member': {'name': 'プレイヤーC'}
        }
    ]
    
    # ラウンド情報
    test_round = {
        'round_id': 999,
        'date_played': '2025-03-30',
        'course_name': 'テストコース',
        'num_players': 3,  # 3人プレイ
        'has_extra': True
    }
    
    # ハンディキャップ情報
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
        print(f"  プレイヤー: {player_info['Player']}")
        print(f"    フロント/バック/エキストラゲームポイント: {player_info['Front GP']}/{player_info['Back GP']}/{player_info['Extra GP']}")
        print(f"    一時Game Pt: {player_info.get('temp_game_pt', 'N/A')} → 最終Game Pt: {player_info['Game Pt']}")
        print(f"    Match Pt: {player_info['Match Pt']}")
        print(f"    Putt Pt: {player_info['Putt Pt']}")
        print(f"    Total Pt: {player_info['Total Pt']}")
        print(f"    -" * 30)
    
    # 3人プレイヤーの特殊計算を検証
    print("\n3人プレイヤーのGame Point計算検証:")
    for player_id, player_info in updated_player_data.items():
        temp_pt = player_info.get('temp_game_pt', 0)
        game_pt = player_info['Game Pt']
        
        # 他のプレイヤーの一時Game Ptの合計を計算
        others_temp_pt = sum(p_info.get('temp_game_pt', 0) for pid, p_info in updated_player_data.items() if pid != player_id)
        
        # 計算式の検証: Game Pt = 一時GamePt × 2 - 他プレイヤーの一時GamePt合計
        expected_game_pt = temp_pt * 2 - others_temp_pt
        
        print(f"  プレイヤー {player_info['Player']}:")
        print(f"    一時Game Pt: {temp_pt}")
        print(f"    他プレイヤーの一時Game Pt合計: {others_temp_pt}")
        print(f"    期待値: {temp_pt} × 2 - {others_temp_pt} = {expected_game_pt}")
        print(f"    実際値: {game_pt}")
        print(f"    検証結果: {'✓ 正しい' if expected_game_pt == game_pt else '✗ 誤差あり'}")
    
    print("\nテスト完了")
    return updated_player_data

def print_match_results(player_data, player_ids):
    """マッチ結果を表形式で出力"""
    print("\nマッチ対戦結果:")
    
    # ヘッダー行
    header = "プレイヤー"
    for pid in player_ids:
        header += f" | {player_data[pid]['Player']}"
    print(header)
    print("-" * len(header))
    
    # 各プレイヤーの行
    for pid1 in player_ids:
        row = f"{player_data[pid1]['Player']}"
        for pid2 in player_ids:
            if pid1 == pid2:
                row += " | -"
            else:
                # 実際はマッチ計算ロジックに基づきここに計算結果が入る
                row += " | ?"
        print(row)

if __name__ == "__main__":
    test_three_players()
