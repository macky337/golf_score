import os
import sys

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def mock_save_results(*args, **kwargs):
    """テスト時のデータ保存をモック化するための関数"""
    print("テスト用にデータ保存処理をスキップしました")
    return True

def verify_player_data(player_data):
    """プレイヤーデータの整合性を検証する"""
    # マッチポイントは合計0になるはず
    match_pt_sum = sum(data["Match Pt"] for _, data in player_data.items())
    
    results = {
        "match_pt_sum": match_pt_sum,
        "match_pt_valid": match_pt_sum == 0,
    }
    
    # プレイヤー数に応じた検証
    player_count = len(player_data)
    if player_count == 3:
        # 3人プレイの特殊ゲームポイント計算を検証
        for pid, data in player_data.items():
            temp_pt = data.get('temp_game_pt', 0)
            game_pt = data['Game Pt']
            others_temp_pt = sum(p_data.get('temp_game_pt', 0) for p_id, p_data in player_data.items() if p_id != pid)
            expected = temp_pt * 2 - others_temp_pt
            
            if game_pt != expected:
                results["game_pt_valid"] = False
                results["game_pt_error"] = f"Player {pid}: expected {expected}, got {game_pt}"
                break
        else:
            results["game_pt_valid"] = True
    
    return results

def print_test_summary(test_name, player_data):
    """テスト結果のサマリーを表示する"""
    print(f"\n===== {test_name} 検証結果 =====")
    
    # マッチポイント合計を検証
    match_pt_sum = sum(data["Match Pt"] for _, data in player_data.items())
    print(f"マッチポイント合計: {match_pt_sum} {'✓' if match_pt_sum == 0 else '✗'}")
    
    # ゲームポイントの検証
    print("ゲームポイント検証:")
    for pid, data in player_data.items():
        player_name = data["Player"]
        front_gp = data["Front GP"]
        back_gp = data["Back GP"]
        extra_gp = data.get("Extra GP", 0)
        game_pt = data["Game Pt"]
        
        if len(player_data) == 3:
            temp_pt = data.get('temp_game_pt', front_gp + back_gp + extra_gp)
            others_temp_pt = sum(p_data.get('temp_game_pt', p_data["Front GP"] + p_data["Back GP"] + p_data.get("Extra GP", 0)) 
                                for p_id, p_data in player_data.items() if p_id != pid)
            expected = temp_pt * 2 - others_temp_pt
            valid = game_pt == expected
        else:
            expected = front_gp + back_gp + extra_gp
            valid = game_pt == expected
            
        print(f"  {player_name}: {game_pt} {'✓' if valid else '✗'} (期待値: {expected})")
    
    print(f"===== {test_name} 完了 =====\n")
