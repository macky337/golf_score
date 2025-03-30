import os
import sys
from modules.supabase_client import get_supabase_client, get_scores_with_fallback
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.data_formatter import initialize_player_data

def main():
    """round_resultsテーブルへのtotal_pt保存問題をデバッグする"""
    print("=== round_results保存デバッグツール ===")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # テスト対象のラウンド選択
    round_id = select_round(supabase)
    if not round_id:
        print("テスト用ラウンドを選択できませんでした。")
        return
    
    # テスト対象ラウンドの情報取得
    test_round = get_round_info(supabase, round_id)
    if not test_round:
        print(f"ラウンドID {round_id} の情報が取得できませんでした。")
        return
    
    print(f"ラウンドID {round_id} ({test_round['date_played']} - {test_round['course_name']})を使用します")
    
    # テーブル構造の確認
    check_round_results_schema(supabase)
    
    # 現在のround_resultsデータを取得
    current_data = get_current_round_results(supabase, round_id)
    if not current_data:
        print(f"ラウンドID {round_id} のround_resultsデータが見つかりません。新規作成します。")
    
    # スコアデータを取得して計算
    process_and_save_results(supabase, round_id, test_round)
    
    # 保存後のデータを確認
    verify_saved_data(supabase, round_id)

def select_round(supabase):
    """テスト用ラウンドを選択"""
    try:
        # 最新5件のラウンドを取得
        rounds_result = supabase.table('rounds').select('round_id, date_played, course_name').order('date_played', desc=True).limit(5).execute()
        if not rounds_result.data:
            print("ラウンドデータがありません")
            return None
        
        rounds = rounds_result.data
        print("\nテスト用ラウンドを選択してください:")
        for i, r in enumerate(rounds):
            print(f"{i+1}. ID:{r['round_id']} - {r['date_played']} {r['course_name']}")
        
        choice = input("\n番号を入力してください (デフォルト: 1): ")
        if not choice:
            return rounds[0]['round_id']
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(rounds):
                return rounds[index]['round_id']
            else:
                print("無効な選択です。最初のラウンドを使用します。")
                return rounds[0]['round_id']
        except ValueError:
            print("無効な入力です。最初のラウンドを使用します。")
            return rounds[0]['round_id']
    except Exception as e:
        print(f"ラウンド取得エラー: {e}")
        return None

def get_round_info(supabase, round_id):
    """ラウンド情報を取得"""
    try:
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        if round_result.data:
            return round_result.data[0]
        return None
    except Exception as e:
        print(f"ラウンド情報取得エラー: {e}")
        return None

def check_round_results_schema(supabase):
    """round_resultsテーブルのスキーマを確認"""
    print("\n== round_resultsテーブルのスキーマ確認 ==")
    try:
        # テーブルから1件取得してカラム情報を表示
        result = supabase.table('round_results').select('*').limit(1).execute()
        if result.data:
            print("テーブル構造:")
            for key in result.data[0].keys():
                print(f"- {key}")
            
            # total_ptカラムが存在するか確認
            if 'total_pt' in result.data[0]:
                print(f"✓ total_ptカラムが存在します (値: {result.data[0]['total_pt']})")
            else:
                print("✗ total_ptカラムが存在しません！")
        else:
            print("round_resultsテーブルにデータがありません。スキーマを確認できません。")
    except Exception as e:
        print(f"スキーマ確認エラー: {e}")

def get_current_round_results(supabase, round_id):
    """現在のround_resultsデータを取得"""
    print(f"\n== ラウンドID {round_id} の現在のround_resultsデータ ==")
    try:
        results = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
        if results.data:
            print(f"{len(results.data)}件のデータが存在します")
            for i, r in enumerate(results.data[:3]):  # 最初の3件だけ表示
                print(f"  {i+1}. member_id: {r.get('member_id')}, total_pt: {r.get('total_pt')}")
            if len(results.data) > 3:
                print(f"  ...他 {len(results.data) - 3} 件")
            return results.data
        else:
            print("データがありません")
            return None
    except Exception as e:
        print(f"データ取得エラー: {e}")
        return None

def process_and_save_results(supabase, round_id, test_round):
    """データを処理して保存"""
    print(f"\n== データ処理と保存 ==")
    try:
        # スコアデータを取得
        scores = get_scores_with_fallback(round_id)
        if not scores:
            print("スコアデータがありません")
            return
        
        print(f"{len(scores)}件のスコアデータを取得しました")
        
        # ハンディキャップ情報を取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data
        
        # 前回計算結果を取得
        round_results = get_round_results(round_id)
        
        # プレイヤーデータを初期化
        player_data = initialize_player_data(scores, round_results)
        player_ids = sorted(list(player_data.keys()))
        
        # ハンディキャップ辞書を作成
        handicaps = {}
        total_only_set = set()
        if handicaps_data:
            for h in handicaps_data:
                handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                if 'total_only' in h and h['total_only']:
                    total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
        
        # 計算実行
        print("\n計算処理を実行します...")
        updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, test_round)
        
        # 計算結果を表示 (Total Pt に注目)
        print("\n計算結果 (Total Pt):")
        for player_id, data in updated_player_data.items():
            player_name = data['Player']
            total_pt = data['Total Pt']
            print(f"  {player_name}: {total_pt} (match_pt={data['Match Pt']}, putt_pt={data['Putt Pt']}, game_pt={data['Game Pt']})")
        
        # 保存実行 (直接デバッグ表示付きの保存)
        print("\n保存を実行します (詳細なデバッグ情報付き)...")
        
        # PascalCase→snake_caseの変換を明示的に確認
        print("\n変換するデータ:")
        records_to_save = []
        for member_id, data in updated_player_data.items():
            record = {
                'round_id': round_id,
                'member_id': member_id,
                'match_front': data.get('Match Front', 0),
                'match_back': data.get('Match Back', 0),
                'match_total': data.get('Match Total', 0),
                'match_extra': data.get('Match Extra', 0),
                'match_pt': data.get('Match Pt', 0),
                'putt_pt': data.get('Putt Pt', 0),
                'total_game_pt': data.get('Game Pt', 0),
                'total_pt': data.get('Total Pt', 0)
            }
            records_to_save.append(record)
            print(f"  Player {data['Player']}: Total Pt={data['Total Pt']} → total_pt={record['total_pt']}")
        
        # 直接Supabaseに保存
        print("\n直接Supabaseにデータを保存します...")
        try:
            # 既存レコードを削除
            delete_result = supabase.table('round_results').delete().eq('round_id', round_id).execute()
            print(f"  既存レコードを削除しました")
            
            # 新規レコードを挿入
            insert_result = supabase.table('round_results').insert(records_to_save).execute()
            print(f"  {len(insert_result.data) if hasattr(insert_result, 'data') and insert_result.data else 0}件のレコードを挿入しました")
            return True
        except Exception as e:
            print(f"  保存エラー: {e}")
            return False
    
    except Exception as e:
        print(f"処理エラー: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def verify_saved_data(supabase, round_id):
    """保存後のデータを確認"""
    print(f"\n== 保存後のデータ確認 ==")
    try:
        results = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
        if results.data:
            print(f"{len(results.data)}件のデータが存在します")
            print("\nTotal Ptフィールドの確認:")
            for r in results.data:
                member_id = r.get('member_id')
                total_pt = r.get('total_pt')
                match_pt = r.get('match_pt', 0)
                putt_pt = r.get('putt_pt', 0)
                game_pt = r.get('total_game_pt', 0)
                calculated = match_pt + putt_pt + game_pt
                
                print(f"  メンバーID {member_id}: total_pt={total_pt}, 計算値={calculated}, 一致={total_pt==calculated}")
                if total_pt != calculated:
                    print(f"    ✗ 不一致! (match_pt={match_pt}, putt_pt={putt_pt}, game_pt={game_pt})")
        else:
            print("データがありません！")
    except Exception as e:
        print(f"確認エラー: {e}")

if __name__ == "__main__":
    main()
