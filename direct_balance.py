#!/usr/bin/env python3
"""直接的なポイントバランス確認"""

def main():
    try:
        import os
        import sys
        sys.path.append('.')
        
        # 環境変数とDB接続
        from dotenv import load_dotenv
        load_dotenv()
        
        from modules.db import supabase
        
        print("=== 直接ポイントバランス確認 ===")
        
        # 1. round_resultsからtotal_ptを全取得
        print("1. round_resultsテーブルからtotal_ptを取得...")
        result = supabase.table('round_results').select('total_pt, round_id, member_id').execute()
        
        if not result.data:
            print("データが見つかりません")
            return
            
        # 2. 合計計算
        total_pts = [float(r.get('total_pt') or 0) for r in result.data]
        total_sum = sum(total_pts)
        
        print(f"レコード数: {len(total_pts)}")
        print(f"Total Pt合計: {total_sum}")
        
        # 3. ラウンド別集計
        round_sums = {}
        for record in result.data:
            round_id = record.get('round_id')
            total_pt = float(record.get('total_pt') or 0)
            
            if round_id not in round_sums:
                round_sums[round_id] = 0
            round_sums[round_id] += total_pt
        
        # 4. バランスが崩れているラウンドを特定
        unbalanced = {rid: balance for rid, balance in round_sums.items() if abs(balance) > 0.01}
        
        print(f"\nバランス分析:")
        print(f"全ラウンド数: {len(round_sums)}")
        print(f"バランス崩れラウンド数: {len(unbalanced)}")
        
        if unbalanced:
            print("\nバランス崩れトップ10:")
            sorted_unbalanced = sorted(unbalanced.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            for round_id, balance in sorted_unbalanced:
                print(f"  ラウンドID {round_id}: {balance:+.1f}")
        
        # 5. 最大の問題ラウンドの詳細
        if unbalanced:
            worst_round = max(unbalanced.keys(), key=lambda x: abs(unbalanced[x]))
            worst_balance = unbalanced[worst_round]
            print(f"\n最も問題のあるラウンド:")
            print(f"ラウンドID {worst_round}: バランス {worst_balance:+.1f}")
            
            # 該当ラウンドの詳細データ
            worst_records = [r for r in result.data if r.get('round_id') == worst_round]
            print(f"参加者数: {len(worst_records)}")
            
            for record in worst_records:
                member_id = record.get('member_id')
                total_pt = record.get('total_pt', 0)
                print(f"  メンバーID {member_id}: {total_pt}")
                
    except Exception as e:
        print(f"エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
