import os
import sys
from datetime import datetime

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.supabase_client import get_supabase_client, get_scores_with_fallback
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.data_formatter import initialize_player_data

def main():
    """
    レストアしたscoreテーブルデータに基づいてround_resultsを再計算するスクリプト
    ゲームポイントを復元した後に実行することを想定
    """
    print("===== score → round_results 再計算ツール =====")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # 再計算対象ラウンドの選択
    round_ids = select_rounds_to_recalculate(supabase)
    if not round_ids:
        print("再計算するラウンドが選択されていません。処理を終了します。")
        return
    
    # 統計情報の初期化
    stats = {
        "total_rounds": len(round_ids),
        "processed_rounds": 0,
        "success_rounds": 0,
        "failed_rounds": 0,
        "start_time": datetime.now()
    }
    
    # 各ラウンドを再計算
    for index, round_id in enumerate(round_ids):
        # ラウンド情報を取得
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        if not round_result.data:
            print(f"ラウンドID {round_id} の情報が見つかりません。スキップします。")
            stats["failed_rounds"] += 1
            continue
        
        round_data = round_result.data[0]
        print(f"\n--- ラウンドID {round_id} ({round_data['date_played']} - {round_data['course_name']}) " +
              f"[{index+1}/{len(round_ids)}] ---")
        
        # 再計算を実行
        success = recalculate_round(supabase, round_id, round_data)
        
        stats["processed_rounds"] += 1
        if success:
            stats["success_rounds"] += 1
        else:
            stats["failed_rounds"] += 1
    
    # 処理結果のサマリーを表示
    end_time = datetime.now()
    duration = end_time - stats["start_time"]
    
    print("\n===== 処理結果サマリー =====")
    print(f"処理開始時間: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"処理終了時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"処理時間: {duration}")
    print(f"総ラウンド数: {stats['total_rounds']}")
    print(f"成功: {stats['success_rounds']} 件")
    print(f"失敗: {stats['failed_rounds']} 件")
    
    print("\n処理が完了しました。")

def select_rounds_to_recalculate(supabase):
    """再計算対象のラウンドを選択"""
    try:
        # 全ラウンド取得
        rounds_result = supabase.table('rounds').select('round_id, date_played, course_name').order('date_played', desc=True).execute()
        
        if not rounds_result.data:
            print("ラウンドデータが見つかりません。")
            return []
        
        rounds = rounds_result.data
        print(f"\n{len(rounds)}件のラウンドが見つかりました。")
        
        # 選択オプションを表示
        print("\n再計算するラウンドを選択してください:")
        print("0: すべてのラウンド")
        
        # 最新10件のみ表示
        display_rounds = rounds[:10]
        for i, r in enumerate(display_rounds):
            print(f"{i+1}: ID:{r['round_id']} - {r['date_played']} {r['course_name']}")
        
        if len(rounds) > 10:
            print(f"... 他 {len(rounds) - 10} 件")
        
        # 選択入力
        choice = input("\n数字を入力してください (複数選択はカンマ区切り、例: 1,3,4): ")
        
        if choice == "0":
            return [r['round_id'] for r in rounds]
        
        selected_ids = []
        try:
            # カンマ区切りの入力を処理
            for part in choice.split(','):
                if part.strip():
                    index = int(part.strip()) - 1
                    if 0 <= index < len(display_rounds):
                        selected_ids.append(display_rounds[index]['round_id'])
                    else:
                        print(f"警告: {index+1} は有効な選択肢ではありません")
        except ValueError:
            print("無効な入力です。処理を中止します")
            return []
        
        if not selected_ids:
            print("有効なラウンドが選択されませんでした")
            return []
        
        return selected_ids
        
    except Exception as e:
        print(f"ラウンド取得エラー: {e}")
        return []

def recalculate_round(supabase, round_id, round_data):
    """ラウンドIDに基づいて再計算を実行"""
    try:
        # スコア情報を取得（リストアされたゲームポイントを含む）
        scores = get_scores_with_fallback(round_id)
        if not scores:
            print(f"  スコアデータが見つかりません。スキップします。")
            return False
        
        print(f"  {len(scores)}件のスコアデータを取得しました。")
        
        # スコアデータのゲームポイントを表示（サンプル）
        sample_score = scores[0]
        print(f"  サンプルスコア（メンバーID {sample_score['member_id']}）:")
        print(f"    front_game_pt: {sample_score.get('front_game_pt', 0)}")
        print(f"    back_game_pt: {sample_score.get('back_game_pt', 0)}")
        if round_data.get('has_extra'):
            print(f"    extra_game_pt: {sample_score.get('extra_game_pt', 0)}")
        
        # ハンディキャップ情報を取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data or []
        
        # 現在のround_resultsデータを取得（存在すれば）
        round_results = get_round_results(round_id)
        
        # プレイヤーデータを初期化
        player_data = initialize_player_data(scores, round_results)
        player_ids = sorted(list(player_data.keys()))
        
        if not player_ids:
            print("  有効なプレイヤーIDが見つかりません。スキップします。")
            return False
        
        print(f"  {len(player_ids)}人のプレイヤーデータを処理します。")
        
        # ハンディキャップ辞書を作成
        handicaps = {}
        total_only_set = set()
        for h in handicaps_data:
            handicaps[(h.get('player_1_id'), h.get('player_2_id'))] = h.get('player_1_to_2', 0)
            handicaps[(h.get('player_2_id'), h.get('player_1_id'))] = h.get('player_2_to_1', 0)
            if h.get('total_only'):
                total_only_set.add(frozenset([h.get('player_1_id'), h.get('player_2_id')]))
        
        # 計算前の状態を保存（比較用）
        print("\n  計算前のGame Point:")
        pre_calc_data = {}
        for pid in player_ids:
            player_name = player_data[pid]['Player']
            front_gp = player_data[pid]['Front GP']
            back_gp = player_data[pid]['Back GP']
            extra_gp = player_data[pid].get('Extra GP', 0)
            game_pt = front_gp + back_gp + extra_gp
            pre_calc_data[pid] = {
                'front_gp': front_gp,
                'back_gp': back_gp,
                'extra_gp': extra_gp,
                'game_pt': game_pt
            }
            print(f"    {player_name}: {front_gp} + {back_gp} + {extra_gp} = {game_pt}")
        
        # 計算処理を実行
        print("\n  計算処理実行中...")
        updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, round_data)
        
        # 計算結果の検証（特にゲームポイント）
        print("\n  計算結果の検証:")
        for pid in player_ids:
            player_name = updated_player_data[pid]['Player']
            match_pt = updated_player_data[pid]['Match Pt']
            putt_pt = updated_player_data[pid]['Putt Pt']
            game_pt = updated_player_data[pid]['Game Pt']
            total_pt = updated_player_data[pid]['Total Pt']
            
            # 計算値の検証
            expected_total = match_pt + putt_pt + game_pt
            game_pt_diff = game_pt - pre_calc_data[pid]['game_pt']
            
            print(f"    {player_name}:")
            print(f"      Match Pt: {match_pt}")
            print(f"      Putt Pt: {putt_pt}")
            print(f"      Game Pt: {game_pt} (元の値から{'+' if game_pt_diff>=0 else ''}{game_pt_diff})")
            print(f"      Total Pt: {total_pt} (期待値: {expected_total})")
            
            if total_pt != expected_total:
                print(f"      ⚠ 総合ポイント計算に不一致があります！")
        
        # round_resultsテーブルに保存
        save_result = save_round_results(round_id, updated_player_data)
        
        if save_result:
            print(f"\n  ✓ ラウンドID {round_id} の計算結果を保存しました。")
            return True
        else:
            print(f"\n  ✗ ラウンドID {round_id} の計算結果の保存に失敗しました。")
            return False
        
    except Exception as e:
        import traceback
        print(f"  ✗ ラウンドID {round_id} の処理中にエラーが発生しました: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()
