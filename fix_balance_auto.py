#!/usr/bin/env python3
"""
自動ポイントバランス修復スクリプト
"""
import sys
import os
sys.path.append('.')

from modules.db import supabase
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results

def fix_point_balance():
    """ポイントバランスを自動修復"""
    print("=== 自動ポイントバランス修復ツール ===")
    
    # 現在のバランス状況をチェック
    print("現在のポイントバランスをチェック中...")
    all_rounds = supabase.table('rounds').select('*').execute().data
    
    if not all_rounds:
        print("ラウンドデータがありません。")
        return
    
    # 総バランスを計算
    total_balance = 0
    problematic_rounds = []
      for round_data in all_rounds:
        round_id = round_data['round_id']
        # round_resultsテーブルからtotal_ptを取得
        results = supabase.table('round_results').select('total_pt, member_id').eq('round_id', round_id).execute().data
        round_total = sum(result.get('total_pt', 0) for result in results)
        total_balance += round_total
        
        if round_total != 0:
            problematic_rounds.append({
                'round_id': round_id,
                'imbalance': round_total,
                'date': round_data.get('date_played', '不明'),
                'course': round_data.get('course_name', '不明')
            })
    
    print(f"総ポイントバランス: {total_balance:+d}")
    print(f"不均衡ラウンド数: {len(problematic_rounds)}")
    
    if total_balance == 0:
        print("✅ ポイントバランスは正常です！")
        return
    
    print(f"❌ {total_balance:+d}ポイントの不均衡があります。修復を開始します...")
      # 各問題のあるラウンドを修復
    repaired_count = 0
    for round_info in problematic_rounds[:5]:  # 最初の5ラウンドのみ修復
        round_id = round_info['round_id']
        print(f"\nラウンド {round_id} を修復中... (現在の不均衡: {round_info['imbalance']:+d})")
        
        try:
            # ラウンドのスコアデータを取得
            scores = supabase.table('score').select('*').eq('round_id', round_id).execute().data
            
            if not scores:
                print(f"  スコアデータがありません。スキップします。")
                continue
            
            # ハンディキャップデータを取得
            handicaps = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute().data
            
            # ハンディキャップをペアごとにマッピング
            handicap_map = {}
            for hc in handicaps:
                key = tuple(sorted([hc['member_id_1'], hc['member_id_2']]))
                handicap_map[key] = hc['handicap_difference']
            
            # 各プレイヤーのポイントを再計算
            player_ids = [score['member_id'] for score in scores]
            updated_scores = []
            
            for score in scores:
                member_id = score['member_id']
                
                # ゲームポイントを計算
                front_gp, back_gp, extra_gp, total_pt = calculate_player_points(
                    round_id, member_id, player_ids, handicap_map
                )
                
                # round_resultsテーブルを更新（total_ptはここに保存される）
                update_data = {
                    'total_pt': total_pt
                }
                
                # 既存のround_resultsレコードを更新
                supabase.table('round_results').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
                updated_scores.append({**score, 'total_pt': total_pt})
            
            # ラウンド結果も更新
            save_round_results(round_id, updated_scores)
              # 修復後の確認
            new_results = supabase.table('round_results').select('total_pt').eq('round_id', round_id).execute().data
            new_total = sum(r.get('total_pt', 0) for r in new_results)
            
            print(f"  修復後のバランス: {new_total:+d}")
            repaired_count += 1
            
        except Exception as e:
            print(f"  修復に失敗: {str(e)}")
    
    print(f"\n修復完了: {repaired_count}/{len(problematic_rounds[:5])} ラウンド")
      # 最終バランス確認
    print("\n最終バランス確認中...")
    final_results = supabase.table('round_results').select('total_pt').execute().data
    final_balance = sum(result.get('total_pt', 0) for result in final_results)
    print(f"最終ポイントバランス: {final_balance:+d}")
    
    if final_balance == 0:
        print("✅ ポイントバランスが正常になりました！")
    else:
        print(f"⚠️ まだ {final_balance:+d}ポイントの不均衡があります。")

if __name__ == "__main__":
    fix_point_balance()
