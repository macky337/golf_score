import os
import sys
from modules.supabase_client import get_supabase_client

def main():
    """scoreテーブルからround_resultsテーブルにtotal_ptを転記し、計算値と比較検証する"""
    print("=== total_pt転記・検証ツール ===")
    supabase = get_supabase_client()

    # 未確定のラウンドを取得
    print("\n1. ラウンド情報取得中...")
    try:
        rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
        if not rounds_result.data:
            print("  ラウンドが見つかりません。")
            return
        
        rounds = rounds_result.data
        print(f"  {len(rounds)}件のラウンドが見つかりました。")
    except Exception as e:
        print(f"  ラウンド取得エラー: {e}")
        return

    # 全処理の統計
    stats = {
        "rounds_processed": 0,
        "scores_checked": 0,
        "scores_transferred": 0,
        "scores_matching": 0,
        "scores_different": 0,
        "errors": 0
    }
    
    # 各ラウンドごとに処理
    for round_data in rounds:
        round_id = round_data['round_id']
        print(f"\n--- ラウンドID: {round_id} ({round_data['date_played']} - {round_data['course_name']}) ---")
        
        try:
            # スコアとラウンド結果を取得
            scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
            results_result = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
            
            if not scores_result.data:
                print("  このラウンドにはスコアデータがありません。")
                continue

            # 各スコアに対応するround_resultを検索して値を比較・転記
            for score in scores_result.data:
                stats["scores_checked"] += 1
                member_id = score['member_id']
                
                # 対応するround_resultを検索
                matching_results = [r for r in results_result.data if r['member_id'] == member_id]
                
                if not matching_results:
                    print(f"  ⚠ メンバーID {member_id} のround_resultレコードがありません。")
                    continue

                result = matching_results[0]  # 最初の一致レコードを使用

                # 現在の値を取得
                score_total_pt = score.get('total_pt', 0) or 0
                result_total_pt = result.get('total_pt', 0) or 0
                
                # 計算したはずの値を検証
                calculated_total_pt = (result.get('match_pt', 0) or 0) + \
                                    (result.get('putt_pt', 0) or 0) + \
                                    (result.get('total_game_pt', 0) or 0)
                
                print(f"  メンバーID {member_id}:")
                print(f"    score.total_pt: {score_total_pt}")
                print(f"    result.total_pt: {result_total_pt}")
                print(f"    計算値 (match_pt + putt_pt + total_game_pt): {calculated_total_pt}")
                
                # 値を転記する必要があるか判断
                if result_total_pt != calculated_total_pt:
                    print(f"    ⚠ round_resultsの現在値と計算値が不一致")
                    stats["scores_different"] += 1
                    
                    # 確認プロンプト
                    if input(f"  round_resultのtotal_ptを計算値 {calculated_total_pt} に更新しますか？ [y/N]: ").lower() == 'y':
                        try:
                            # round_resultの更新
                            supabase.table('round_results').update({'total_pt': calculated_total_pt}).eq('id', result['id']).execute()
                            print(f"    ✓ round_resultsのtotal_ptを更新しました。")
                            stats["scores_transferred"] += 1
                        except Exception as e:
                            print(f"    ✗ 更新エラー: {e}")
                            stats["errors"] += 1
                else:
                    print(f"    ✓ round_resultsの値は計算値と一致しています。")
                    stats["scores_matching"] += 1
            
            stats["rounds_processed"] += 1
                    
        except Exception as e:
            print(f"  ラウンドID {round_id} の処理中にエラーが発生: {e}")
            stats["errors"] += 1
    
    # 統計情報を表示
    print("\n=== 処理サマリー ===")
    print(f"処理ラウンド数: {stats['rounds_processed']}")
    print(f"確認スコア数: {stats['scores_checked']}")
    print(f"一致していたスコア: {stats['scores_matching']}")
    print(f"不一致だったスコア: {stats['scores_different']}")
    print(f"更新スコア数: {stats['scores_transferred']}")
    print(f"エラー数: {stats['errors']}")
    
    # scoreテーブルのtotal_pt列削除の案内
    print("\n2. scoreテーブルの'total_pt'カラムを削除しますか？")
    print("  注意: この操作は元に戻せません。すべてのデータが正しく転記されたことを確認してください。")
    
    if input("  scoreテーブルから'total_pt'カラムを削除しますか？ [y/N]: ").lower() == 'y':
        print("\n  注意: Supabaseでカラム削除にはSQL実行が必要です。")
        print("  以下のSQLをSupabaseのSQLエディタで実行してください:")
        print("\n    ALTER TABLE score DROP COLUMN IF EXISTS total_pt;")

if __name__ == "__main__":
    main()
