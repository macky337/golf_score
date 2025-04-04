from modules.supabase_client import get_supabase_client
from modules.round_results import save_round_results

def test_round_data_save():
    """ラウンド結果保存のテスト"""
    print("===== ラウンド結果保存テスト =====")
    
    # 既存のラウンドIDを取得
    supabase = get_supabase_client()
    rounds_result = supabase.table('rounds').select('round_id').limit(1).execute()
    
    if not rounds_result.data:
        print("テスト用のラウンドデータが見つかりませんでした")
        return
        
    test_round_id = rounds_result.data[0]['round_id']
    
    # テストデータを作成
    test_player_data = {
        1: {  # 荒巻
            "Front Score": 40, 
            "Back Score": 43,
            "Front Putt": 15,
            "Back Putt": 16,
            "Front GP": 39,
            "Back GP": 30,
            "Match Front": 10,
            "Match Back": 20,
            "Match Total": 10,
            "Match Extra": 0,
            "Match Pt": 40,
            "Putt Pt": 10,
            "Game Pt": 153,
            "total_game_pt": 153,
            "Total Pt": 203
        },
        2: {  # 吉井
            "Front Score": 42, 
            "Back Score": 41,
            "Front Putt": 17,
            "Back Putt": 14,
            "Front GP": 6,
            "Back GP": 0,
            "Match Front": -10,
            "Match Back": -20,
            "Match Total": -10,
            "Match Extra": 0,
            "Match Pt": -40,
            "Putt Pt": 10,
            "Game Pt": -36,
            "total_game_pt": -36,
            "Total Pt": -66
        }
    }
    
    print(f"テストデータをラウンドID {test_round_id} に保存します")
    
    # データの保存を試みる
    success = save_round_results(test_round_id, test_player_data)
    
    if success:
        print("✓ テストデータの保存に成功しました")
        
        # 保存されたデータを確認
        round_results = supabase.table('round_results').select('*').eq('round_id', test_round_id).execute()
        score_results = supabase.table('score').select('*').eq('round_id', test_round_id).execute()
        
        print(f"\n保存されたround_resultsデータ: {len(round_results.data)}件")
        if round_results.data:
            print(f"サンプルデータ: {round_results.data[0]}")
        
        print(f"\n保存されたscoreデータ: {len(score_results.data)}件")
        if score_results.data:
            print(f"サンプルデータ: {score_results.data[0]}")
    else:
        print("✗ テストデータの保存に失敗しました")
    
    print("\n===== テスト完了 =====")

if __name__ == "__main__":
    test_round_data_save()
