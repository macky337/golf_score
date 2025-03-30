import os
import sys
from modules.supabase_client import get_supabase_client, get_scores_with_fallback
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.data_formatter import initialize_player_data

def main():
    """計算ロジックがtotal_ptを正しく計算・保存するか検証する"""
    print("=== 計算ロジック検証ツール ===")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # 最新の未確定ラウンドを取得
    rounds_result = supabase.table('rounds').select('*').eq('finalized', False).order('date_played', desc=True).execute()
    
    if not rounds_result.data:
        print("未確定のラウンドが見つかりません。最新のラウンドを使用します。")
        rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
        
        if not rounds_result.data:
            print("ラウンドが見つかりません。")
            return
    
    # テスト対象のラウンドを選択
    test_round = rounds_result.data[0]
    round_id = test_round['round_id']
    
    print(f"テスト対象: ラウンドID {round_id} ({test_round['date_played']} - {test_round['course_name']})")
    
    try:
        # ラウンド関連データの取得
        scores = get_scores_with_fallback(round_id)
        if not scores:
            print("スコアデータがありません。")
            return
        
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data
        
        round_results_before = get_round_results(round_id)
        if round_results_before:
            print("現在のround_results:")
            if isinstance(round_results_before, list):
                for result in round_results_before[:3]:  # 最初の3件だけ表示
                    print(f"  メンバーID {result.get('member_id')}: total_pt={result.get('total_pt')}")
            else:
                for member_id, result in list(round_results_before.items())[:3]:
                    print(f"  メンバーID {member_id}: total_pt={result.get('total_pt')}")
        
        # プレイヤーデータの初期化
        if isinstance(round_results_before, list):
            round_results_dict = {item.get('member_id'): item for item in round_results_before if item.get('member_id') is not None}
        else:
            round_results_dict = round_results_before
        
        player_data = initialize_player_data(scores, round_results_dict)
        player_ids = sorted(list(player_data.keys()))
        
        # ハンディキャップ辞書作成
        handicaps = {}
        total_only_set = set()
        if handicaps_data:
            for h in handicaps_data:
                handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                if 'total_only' in h and h['total_only']:
                    total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
        
        # 再計算実行
        print("\n計算実行中...")
        updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, test_round)
        
        # 計算結果を検証
        print("\n計算結果検証:")
        for player_id, player_info in updated_player_data.items():
            match_pt = player_info['Match Pt']
            putt_pt = player_info['Putt Pt']
            game_pt = player_info['Game Pt']
            total_pt = player_info['Total Pt']
            
            # 合計が正しいか検証
            expected_total = match_pt + putt_pt + game_pt
            
            print(f"プレイヤー {player_info['Player']}:")
            print(f"  Match Pt: {match_pt}")
            print(f"  Putt Pt: {putt_pt}")
            print(f"  Game Pt: {game_pt}")
            print(f"  Total Pt: {total_pt}")
            print(f"  検証: {match_pt} + {putt_pt} + {game_pt} = {expected_total}")
            
            if total_pt == expected_total:
                print("  ✓ total_ptは正しく計算されています。")
            else:
                print(f"  ✗ total_ptが異なります。期待値: {expected_total}, 実際: {total_pt}")
        
        # round_resultsテーブルへの保存テスト
        print("\n保存テスト実行中...")
        save_result = save_round_results(round_id, updated_player_data)
        
        if save_result:
            print("✓ round_resultsテーブルへの保存に成功しました。")
        else:
            print("✗ round_resultsテーブルへの保存に失敗しました。")
        
        # 保存後の検証
        print("\n保存後の検証:")
        round_results_after = get_round_results(round_id)
        
        if isinstance(round_results_after, list):
            for result in round_results_after[:3]:  # 最初の3件だけ表示
                member_id = result.get('member_id')
                if member_id:
                    player = next((p for pid, p in updated_player_data.items() if pid == member_id), None)
                    if player:
                        expected = player['Total Pt']
                        actual = result.get('total_pt', 0)
                        print(f"メンバーID {member_id}:")
                        print(f"  期待値: {expected}")
                        print(f"  実際値: {actual}")
                        print(f"  {'✓ 一致' if expected == actual else '✗ 不一致'}")
        else:
            for member_id, result in list(round_results_after.items())[:3]:
                player = next((p for pid, p in updated_player_data.items() if pid == member_id), None)
                if player:
                    expected = player['Total Pt']
                    actual = result.get('total_pt', 0)
                    print(f"メンバーID {member_id}:")
                    print(f"  期待値: {expected}")
                    print(f"  実際値: {actual}")
                    print(f"  {'✓ 一致' if expected == actual else '✗ 不一致'}")
    
    except Exception as e:
        import traceback
        print(f"エラーが発生しました: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
