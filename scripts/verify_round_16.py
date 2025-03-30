import os
import sys
from modules.supabase_client import get_supabase_client, get_scores_with_fallback
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.data_formatter import initialize_player_data

def main():
    """ラウンドID 16の計算結果を検証"""
    print("===== ラウンドID 16 検証ツール =====")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # テスト対象のラウンド
    round_id = 16
    
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        print(f"ラウンドID {round_id} が見つかりません。")
        return
    
    active_round = round_result.data[0]
    print(f"ラウンド: {active_round['date_played']} - {active_round['course_name']}")
    
    # スコアデータを取得
    scores = get_scores_with_fallback(round_id)
    if not scores:
        print("スコアデータがありません。")
        return
    
    # round_results を取得
    round_results = get_round_results(round_id)
    print(f"round_results データ: {len(round_results) if round_results else 0} 件")
    
    # ハンディキャップ情報を取得
    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data
    
    # プレイヤーデータの初期化
    player_data = initialize_player_data(scores, round_results)
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
    
    # 期待される結果データ（手動入力）
    expected_data = {
        "荒巻": {"Game Pt": -66, "Match Pt": 20, "Putt Pt": 20, "Total Pt": -26},
        "吉井": {"Game Pt": 102, "Match Pt": 30, "Putt Pt": -20, "Total Pt": 112},
        "福澤": {"Game Pt": 16, "Match Pt": 40, "Putt Pt": 20, "Total Pt": 76},
        "清村": {"Game Pt": -52, "Match Pt": -90, "Putt Pt": -20, "Total Pt": -162}
    }
    
    # 再計算実行
    print("\n再計算実行...")
    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
    
    # 結果を表形式で表示
    print("\n計算結果と期待値の比較:")
    print(f"{'プレイヤー':<10} {'Game Pt':>10} {'Match Pt':>10} {'Putt Pt':>10} {'Total Pt':>10} {'期待値':>10} {'検証':>10}")
    print("-" * 70)
    
    for pid, data in updated_player_data.items():
        player_name = data['Player']
        game_pt = data['Game Pt']
        match_pt = data['Match Pt']
        putt_pt = data['Putt Pt']
        total_pt = data['Total Pt']
        
        # 計算結果の検証
        calculated_total = game_pt + match_pt + putt_pt
        
        # 期待値と比較（名前で一致するものを検索）
        expected = None
        for name, values in expected_data.items():
            if name in player_name:
                expected = values
                break
        
        if expected:
            expected_total = expected["Total Pt"]
            validation = "✓" if total_pt == expected_total else "✗"
        else:
            expected_total = "不明"
            validation = "?"
            
        print(f"{player_name:<10} {game_pt:>10} {match_pt:>10} {putt_pt:>10} {total_pt:>10} {expected_total:>10} {validation:>10}")
        
        # 不一致がある場合の詳細情報
        if validation == "✗":
            print(f"  → 計算値: {calculated_total}, DB値: {total_pt}, 期待値: {expected_total}")
            if calculated_total != total_pt:
                print(f"  ※ 計算値とDB値が一致していません！")
    
    # 保存処理の確認
    print("\n現在のround_resultsテーブルの値を確認しますか？[y/N]: ", end="")
    if input().lower() == 'y':
        results = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
        if results.data:
            print("\nround_resultsテーブルの値:")
            for r in results.data:
                member_id = r['member_id']
                player = next((p for p_id, p in player_data.items() if p_id == member_id), None)
                if player:
                    player_name = player['Player']
                    print(f"{player_name}: total_pt={r['total_pt']}, match_pt={r['match_pt']}, putt_pt={r['putt_pt']}, total_game_pt={r['total_game_pt']}")
        else:
            print("データがありません")
    
    # 再計算して保存するかの確認
    print("\nこのラウンドを再計算して保存しますか？[y/N]: ", end="")
    if input().lower() == 'y':
        if save_round_results(round_id, updated_player_data):
            print("保存に成功しました")
        else:
            print("保存に失敗しました")

if __name__ == "__main__":
    main()
