import os
import sys
from datetime import datetime
import pandas as pd

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.supabase_client import get_supabase_client, get_scores_with_fallback
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.data_formatter import initialize_player_data

def main():
    print("\n===== ゴルフスコア計算ロジックテスト =====\n")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # テスト用ラウンドIDを取得（最新の未確定ラウンド、または指定したID）
    test_round_id = get_test_round_id(supabase)
    if not test_round_id:
        print("テスト対象のラウンドが見つかりません。")
        return
    
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', test_round_id).execute()
    if not round_result.data:
        print(f"ラウンドID {test_round_id} の情報が見つかりません。")
        return
    
    active_round = round_result.data[0]
    print(f"\n▶ テスト対象: ラウンドID {test_round_id} ({active_round['date_played']} - {active_round['course_name']})")
    
    # 1. フロントスコア入力のテスト
    print("\n▶ フロントスコア入力後の計算テスト")
    test_front_score_calculation(supabase, test_round_id, active_round)
    
    # 2. バックスコア入力のテスト
    print("\n▶ バックスコア入力後の計算テスト")
    test_back_score_calculation(supabase, test_round_id, active_round)
    
    # 3. エキストラスコア入力のテスト（has_extraがTrueの場合のみ）
    if active_round.get('has_extra'):
        print("\n▶ エキストラスコア入力後の計算テスト")
        test_extra_score_calculation(supabase, test_round_id, active_round)
    
    print("\n===== テスト完了 =====\n")

def get_test_round_id(supabase):
    """テスト用ラウンドIDを取得（最新の未確定ラウンド）"""
    # コマンドライン引数からIDを取得するオプションも追加可能
    
    # 最新の未確定ラウンドを取得
    rounds_result = supabase.table('rounds').select('*').eq('finalized', False).order('date_played', desc=True).execute()
    if rounds_result.data:
        return rounds_result.data[0]['round_id']
    
    # 未確定ラウンドがなければ最新のラウンドを取得
    all_rounds = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    if all_rounds.data:
        return all_rounds.data[0]['round_id']
    
    return None

def test_front_score_calculation(supabase, round_id, active_round):
    """フロントスコア入力後の計算テスト"""
    # スコア情報を取得
    scores = get_scores_with_fallback(round_id)
    if not scores:
        print("  スコアデータが見つかりません。")
        return
    
    # ハンディキャップ情報を取得
    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data
    
    # round_resultsを確認（計算前の状態）
    print("  計算前のround_results:")
    round_results_before = get_round_results(round_id)
    print(f"  データ件数: {len(round_results_before) if isinstance(round_results_before, list) else ('辞書型: ' + str(len(round_results_before)) if round_results_before else 'なし')}")
    
    # 計算処理を実行
    # プレイヤーデータ初期化
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
    
    # ポイント計算を実行
    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
    
    # プレイヤーごとの計算結果を表示
    print("\n  計算結果:")
    for player_id, player_info in updated_player_data.items():
        print(f"    Player: {player_info['Player']}")
        print(f"      Front Score: {player_info['Front Score']}")
        print(f"      Match Front: {player_info['Match Front']}")
        print(f"      Front GP: {player_info['Front GP']}")
        print(f"      Putt Pt: {player_info['Putt Pt']}")
    
    # 結果をround_resultsテーブルに保存
    save_result = save_round_results(round_id, updated_player_data)
    if save_result:
        print("\n  ✓ 計算結果をround_resultsテーブルに保存しました")
    else:
        print("\n  ✗ 計算結果の保存に失敗しました")
    
    # 保存後のround_resultsデータを取得して確認
    round_results_after = get_round_results(round_id)
    print("\n  保存後のround_results:")
    if isinstance(round_results_after, list):
        for result in round_results_after:
            member_id = result.get('member_id')
            if member_id:
                player_name = next((info['Player'] for pid, info in player_data.items() if pid == member_id), f"Player {member_id}")
                print(f"    {player_name}: match_front={result.get('match_front')}, match_pt={result.get('match_pt')}")
    elif round_results_after:
        for member_id, result in round_results_after.items():
            player_name = next((info['Player'] for pid, info in player_data.items() if pid == member_id), f"Player {member_id}")
            print(f"    {player_name}: Match Front={result.get('Match Front')}, Match Pt={result.get('Match Pt')}")
    else:
        print("    データなし")

def test_back_score_calculation(supabase, round_id, active_round):
    """バックスコア入力後の計算テスト - フロントスコアテストと同様の処理"""
    # 実装内容はtest_front_score_calculationとほぼ同じですが、
    # バックスコア固有の部分を強調して表示します
    
    scores = get_scores_with_fallback(round_id)
    if not scores:
        print("  スコアデータが見つかりません。")
        return
        
    # 以下の処理はtest_front_score_calculationとほぼ同じですが、
    # 出力メッセージを変えています
    
    # ハンディキャップ情報を取得
    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data
    
    # round_resultsを確認
    round_results_before = get_round_results(round_id)
    print(f"  計算前のround_results: {len(round_results_before) if isinstance(round_results_before, list) else ('辞書型: ' + str(len(round_results_before)) if round_results_before else 'なし')}件")
    
    # 計算処理を実行
    if isinstance(round_results_before, list):
        round_results_dict = {item.get('member_id'): item for item in round_results_before if item.get('member_id') is not None}
    else:
        round_results_dict = round_results_before
    
    player_data = initialize_player_data(scores, round_results_dict)
    player_ids = sorted(list(player_data.keys()))
    
    handicaps = {}
    total_only_set = set()
    if handicaps_data:
        for h in handicaps_data:
            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if 'total_only' in h and h['total_only']:
                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
    
    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
    
    print("\n  計算結果:")
    for player_id, player_info in updated_player_data.items():
        print(f"    Player: {player_info['Player']}")
        print(f"      Back Score: {player_info['Back Score']}")
        print(f"      Match Back: {player_info['Match Back']}")
        print(f"      Match Total: {player_info['Match Total']} (バック入力後に計算)")
        print(f"      Back GP: {player_info['Back GP']}")
    
    save_result = save_round_results(round_id, updated_player_data)
    if save_result:
        print("\n  ✓ バック計算結果をround_resultsテーブルに保存しました")
    else:
        print("\n  ✗ バック計算結果の保存に失敗しました")
    
    round_results_after = get_round_results(round_id)
    print("\n  保存後のround_results:")
    if isinstance(round_results_after, list):
        for result in round_results_after:
            member_id = result.get('member_id')
            if member_id:
                player_name = next((info['Player'] for pid, info in player_data.items() if pid == member_id), f"Player {member_id}")
                print(f"    {player_name}: match_back={result.get('match_back')}, match_total={result.get('match_total')}")
    elif round_results_after:
        for member_id, result in round_results_after.items():
            player_name = next((info['Player'] for pid, info in player_data.items() if pid == member_id), f"Player {member_id}")
            print(f"    {player_name}: Match Back={result.get('Match Back')}, Match Total={result.get('Match Total')}")
    else:
        print("    データなし")

def test_extra_score_calculation(supabase, round_id, active_round):
    """エキストラスコア入力後の計算テスト - フロント/バックと同様"""
    # フロント/バックテストとほぼ同じですが、エキストラスコア固有の表示を行います
    
    scores = get_scores_with_fallback(round_id)
    if not scores:
        print("  スコアデータが見つかりません。")
        return
        
    # 以下、test_front_score_calculation/test_back_score_calculationとほぼ同じ処理
    
    # ハンディキャップ情報を取得
    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data
    
    # round_resultsを確認
    round_results_before = get_round_results(round_id)
    print(f"  計算前のround_results: {len(round_results_before) if isinstance(round_results_before, list) else ('辞書型: ' + str(len(round_results_before)) if round_results_before else 'なし')}件")
    
    # 計算処理を実行
    if isinstance(round_results_before, list):
        round_results_dict = {item.get('member_id'): item for item in round_results_before if item.get('member_id') is not None}
    else:
        round_results_dict = round_results_before
    
    player_data = initialize_player_data(scores, round_results_dict)
    player_ids = sorted(list(player_data.keys()))
    
    handicaps = {}
    total_only_set = set()
    if handicaps_data:
        for h in handicaps_data:
            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if 'total_only' in h and h['total_only']:
                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
    
    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
    
    print("\n  計算結果:")
    for player_id, player_info in updated_player_data.items():
        print(f"    Player: {player_info['Player']}")
        print(f"      Extra Score: {player_info['Extra Score']}")
        print(f"      Match Extra: {player_info['Match Extra']}")
        print(f"      Extra GP: {player_info['Extra GP']}")
        print(f"      Total Pt: {player_info['Total Pt']} (最終合計ポイント)")
    
    save_result = save_round_results(round_id, updated_player_data)
    if save_result:
        print("\n  ✓ エキストラ計算結果をround_resultsテーブルに保存しました")
    else:
        print("\n  ✗ エキストラ計算結果の保存に失敗しました")
    
    round_results_after = get_round_results(round_id)
    print("\n  最終的なround_results:")
    if isinstance(round_results_after, list):
        for result in round_results_after:
            member_id = result.get('member_id')
            if member_id:
                player_name = next((info['Player'] for pid, info in player_data.items() if pid == member_id), f"Player {member_id}")
                print(f"    {player_name}: match_extra={result.get('match_extra')}, total_pt={result.get('total_pt')}")
    elif round_results_after:
        for member_id, result in round_results_after.items():
            player_name = next((info['Player'] for pid, info in player_data.items() if pid == member_id), f"Player {member_id}")
            print(f"    {player_name}: Match Extra={result.get('Match Extra')}, Total Pt={result.get('Total Pt')}")
    else:
        print("    データなし")

if __name__ == "__main__":
    main()
