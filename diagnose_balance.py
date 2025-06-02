#!/usr/bin/env python3
"""ポイントバランスの問題を診断するスクリプト"""

import sys
import os
import pandas as pd

# パスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from modules.db import supabase

def main():
    print("=== ポイントバランス診断ツール ===")
    
    try:
        # 1. 確定済みラウンドの取得
        print("\n1. 確定済みラウンドの取得...")
        rounds_result = supabase.table('rounds').select('*').eq('finalized', True).execute()
        rounds = rounds_result.data
        print(f"   確定済みラウンド数: {len(rounds)}")
        
        # 2. round_resultsテーブルの合計値を取得
        print("\n2. round_resultsテーブルからポイント合計を取得...")
        results_result = supabase.table('round_results').select('*').execute()
        results = results_result.data
        print(f"   round_resultsレコード数: {len(results)}")
        
        # 3. 全体のtotal_ptバランスを確認
        total_pt_sum = sum(r.get('total_pt', 0) or 0 for r in results)
        print(f"   全体のtotal_pt合計: {total_pt_sum}")
        
        # 4. ラウンド別のバランスを確認
        print("\n3. ラウンド別バランスの確認...")
        round_balances = {}
        for result in results:
            round_id = result.get('round_id')
            total_pt = result.get('total_pt', 0) or 0
            
            if round_id not in round_balances:
                round_balances[round_id] = 0
            round_balances[round_id] += total_pt
        
        # バランスが0でないラウンドを特定
        unbalanced_rounds = {rid: balance for rid, balance in round_balances.items() if abs(balance) > 0.01}
        
        if unbalanced_rounds:
            print(f"   バランスが取れていないラウンド数: {len(unbalanced_rounds)}")
            print("   問題のあるラウンド:")
            for round_id, balance in sorted(unbalanced_rounds.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
                # ラウンド情報を取得
                round_info = next((r for r in rounds if r['round_id'] == round_id), None)
                if round_info:
                    date_str = round_info.get('date_played', '不明')
                    course_str = round_info.get('course_name', '不明')
                    print(f"     ラウンドID {round_id} ({date_str} - {course_str}): バランス = {balance:+.1f}")
                else:
                    print(f"     ラウンドID {round_id}: バランス = {balance:+.1f}")
        else:
            print("   ✅ すべてのラウンドでバランスが取れています")
            
        # 5. 最新の問題ラウンドの詳細分析
        if unbalanced_rounds:
            print("\n4. 最も問題の大きいラウンドの詳細分析...")
            worst_round_id = max(unbalanced_rounds.keys(), key=lambda x: abs(unbalanced_rounds[x]))
            worst_balance = unbalanced_rounds[worst_round_id]
            
            print(f"   分析対象: ラウンドID {worst_round_id} (バランス: {worst_balance:+.1f})")
            
            # 該当ラウンドの詳細データを取得
            round_results = [r for r in results if r.get('round_id') == worst_round_id]
            
            print(f"   参加者数: {len(round_results)}")
            print("   プレイヤー別詳細:")
            
            for result in round_results:
                member_id = result.get('member_id')
                total_pt = result.get('total_pt', 0) or 0
                match_pt = result.get('match_pt', 0) or 0
                putt_pt = result.get('putt_pt', 0) or 0
                total_game_pt = result.get('total_game_pt', 0) or 0
                
                # メンバー名を取得
                member_result = supabase.table('members').select('name').eq('member_id', member_id).execute()
                member_name = member_result.data[0]['name'] if member_result.data else f"ID:{member_id}"
                
                print(f"     {member_name}: Total={total_pt:+.1f} (Game={total_game_pt:+.1f}, Match={match_pt:+.1f}, Putt={putt_pt:+.1f})")
                
        # 6. 対処法の提案
        print("\n5. 対処法:")
        if total_pt_sum != 0:
            print(f"   全体バランス: {total_pt_sum:+.1f}")
            print("   推奨アクション:")
            print("   1. scripts/check_total_points_balance.py を実行してラウンド別の詳細確認")
            print("   2. scripts/verify_calculation_logic.py で計算ロジックの検証")
            print("   3. 必要に応じて特定ラウンドの再計算")
        else:
            print("   ✅ 全体のポイントバランスは正常です")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
