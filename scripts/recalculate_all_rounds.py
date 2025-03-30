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
    """すべてのラウンドのスコアを再計算し、total_scoreを更新してround_resultsテーブルに保存する"""
    print("===== ゴルフスコア全ラウンド再計算ツール =====\n")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # すべてのラウンドを取得（日付降順）
    print("ラウンド情報を取得中...")
    rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    
    if not rounds_result.data:
        print("ラウンドデータが存在しません。")
        return
    
    rounds = rounds_result.data
    print(f"{len(rounds)}件のラウンドが見つかりました。\n")
    
    # 処理するかどうかの確認
    confirm = input(f"すべてのラウンド({len(rounds)}件)を再計算しますか？処理には時間がかかる場合があります [y/N]: ")
    if confirm.lower() != 'y':
        print("処理をキャンセルしました。")
        return
    
    # 統計情報の初期化
    stats = {
        "total_rounds": len(rounds),
        "processed_rounds": 0,
        "success_rounds": 0,
        "failed_rounds": 0,
        "updated_total_scores": 0,
        "start_time": datetime.now()
    }
    
    # 各ラウンドを処理
    for index, round_data in enumerate(rounds):
        round_id = round_data['round_id']
        print(f"\n--- ラウンドID {round_id} ({round_data['date_played']} - {round_data['course_name']}) " +
              f"[{index+1}/{len(rounds)}] ---")
        
        try:
            # 1. total_scoreを更新
            updated_scores = update_total_scores(supabase, round_id)
            if updated_scores > 0:
                stats["updated_total_scores"] += updated_scores
                print(f"  ✓ {updated_scores}件のtotal_scoreを更新しました")
            else:
                print("  ℹ total_scoreの更新は不要でした")
            
            # 2. ポイント計算と保存
            success = recalculate_round(supabase, round_id, round_data)
            
            stats["processed_rounds"] += 1
            if success:
                stats["success_rounds"] += 1
            else:
                stats["failed_rounds"] += 1
        except Exception as e:
            import traceback
            print(f"  ✗ ラウンドID {round_id} の処理中にエラーが発生しました: {str(e)}")
            print(traceback.format_exc())
            stats["failed_rounds"] += 1
    
    # 処理結果のサマリーを表示
    end_time = datetime.now()
    duration = end_time - stats["start_time"]
    
    print("\n===== 処理結果サマリー =====")
    print(f"処理開始時間: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"処理終了時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"処理時間: {duration}")
    print(f"総ラウンド数: {stats['total_rounds']}")
    print(f"処理したラウンド数: {stats['processed_rounds']}")
    print(f"成功: {stats['success_rounds']} 件")
    print(f"失敗: {stats['failed_rounds']} 件")
    print(f"更新したtotal_score数: {stats['updated_total_scores']} 件")
    print("===== 処理完了 =====")

def update_total_scores(supabase, round_id):
    """scoreテーブルのtotal_scoreカラムを更新する"""
    try:
        # スコアデータを取得
        scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
        if not scores_result.data:
            print(f"  スコアデータが見つかりません。")
            return 0
        
        updated_count = 0
        for score in scores_result.data:
            front_score = score.get('front_score', 0) or 0
            back_score = score.get('back_score', 0) or 0
            current_total = score.get('total_score', 0) or 0
            calculated_total = front_score + back_score
            
            # 現在の値と計算値が異なる場合のみ更新
            if current_total != calculated_total:
                member_id = score['member_id']
                supabase.table('score').update({
                    'total_score': calculated_total
                }).eq('round_id', round_id).eq('member_id', member_id).execute()
                updated_count += 1
        
        return updated_count
    
    except Exception as e:
        print(f"  ✗ total_score更新エラー: {e}")
        return 0

def recalculate_round(supabase, round_id, round_data):
    """指定されたラウンドのスコアを再計算し保存する"""
    try:
        # スコア情報を取得
        scores = get_scores_with_fallback(round_id)
        if not scores:
            print(f"  スコアデータが見つかりません。スキップします。")
            return False
        
        print(f"  {len(scores)}件のスコアデータを取得しました。")
        
        # ハンディキャップ情報を取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data or []
        
        # 既存のround_resultsデータを取得（存在すれば）
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
        
        # 計算処理を実行
        updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, round_data)
        
        # ポイント計算の要約を表示
        print("  計算結果の概要:")
        for pid in player_ids[:3]:  # 最初の3人だけ表示
            player = updated_player_data[pid]
            match_pt = player.get('Match Pt', 0)
            putt_pt = player.get('Putt Pt', 0) 
            game_pt = player.get('Game Pt', 0)
            total_pt = player.get('Total Pt', 0)
            
            print(f"    {player['Player']}: Match({match_pt}) + Putt({putt_pt}) + Game({game_pt}) = Total({total_pt})")
        
        if len(player_ids) > 3:
            print(f"    ...他 {len(player_ids) - 3} 名")
        
        # round_resultsテーブルに保存
        save_result = save_round_results(round_id, updated_player_data)
        
        if save_result:
            print(f"  ✓ ラウンドID {round_id} の計算結果を正常に保存しました。")
            return True
        else:
            print(f"  ✗ ラウンドID {round_id} の計算結果の保存に失敗しました。")
            return False
    
    except Exception as e:
        import traceback
        print(f"  ✗ ラウンドID {round_id} の処理中にエラーが発生しました: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    main()
