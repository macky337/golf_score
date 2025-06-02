#!/usr/bin/env python3
"""
シンプルなポイントバランス修復スクリプト
round_resultsテーブルのtotal_ptバランスを修正
"""
import sys
import os
sys.path.append('.')

# Streamlitを使わない直接的なアプローチ
from modules.supabase_client import get_supabase_client

def fix_point_balance():
    """ポイントバランスを自動修復"""
    print("=== シンプルポイントバランス修復ツール ===")
    
    # Supabaseクライアントを取得
    supabase = get_supabase_client()
    
    # 現在のバランス状況をチェック
    print("現在のポイントバランスをチェック中...")
    all_results = supabase.table('round_results').select('total_pt, round_id, member_id').execute().data
    
    if not all_results:
        print("round_resultsデータがありません。")
        return
    
    # 総バランスを計算
    total_balance = sum(result.get('total_pt', 0) for result in all_results)
    print(f"総ポイントバランス: {total_balance:+d}")
    print(f"レコード数: {len(all_results)}")
    
    if total_balance == 0:
        print("✅ ポイントバランスは正常です！")
        return
    
    print(f"❌ {total_balance:+d}ポイントの不均衡があります。")
    
    # ラウンドごとのバランスを確認
    round_balances = {}
    for result in all_results:
        round_id = result['round_id']
        total_pt = result.get('total_pt', 0)
        if round_id not in round_balances:
            round_balances[round_id] = []
        round_balances[round_id].append(total_pt)
    
    # 不均衡なラウンドを特定
    problematic_rounds = []
    for round_id, points in round_balances.items():
        round_total = sum(points)
        if round_total != 0:
            problematic_rounds.append({
                'round_id': round_id,
                'imbalance': round_total,
                'player_count': len(points)
            })
    
    print(f"不均衡ラウンド数: {len(problematic_rounds)}")
    
    # 最も簡単な修正方法：最初のプレイヤーのポイントを調整
    if problematic_rounds:
        print("\n修復方法: 各ラウンドの最初のプレイヤーのポイントを調整して0バランスにします。")
        
        for round_info in problematic_rounds[:10]:  # 最初の10ラウンドのみ修復
            round_id = round_info['round_id']
            imbalance = round_info['imbalance']
            
            print(f"\nラウンド {round_id} を修復中... (不均衡: {imbalance:+d})")
            
            try:
                # このラウンドの最初のプレイヤーを取得
                first_player = supabase.table('round_results').select('*').eq('round_id', round_id).limit(1).execute().data
                
                if first_player:
                    player_data = first_player[0]
                    current_total_pt = player_data.get('total_pt', 0)
                    new_total_pt = current_total_pt - imbalance  # バランスを調整
                    
                    # 更新
                    supabase.table('round_results').update({
                        'total_pt': new_total_pt
                    }).eq('id', player_data['id']).execute()
                    
                    print(f"  プレイヤーID {player_data['member_id']}: {current_total_pt} → {new_total_pt}")
                    
            except Exception as e:
                print(f"  修復に失敗: {str(e)}")
    
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
