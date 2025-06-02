#!/usr/bin/env python3
"""シンプルなポイントバランス確認スクリプト"""

import sys
import os
sys.path.append('.')

try:
    from modules.db import supabase
    
    print("=== シンプルポイントバランス確認 ===")
    
    # round_resultsテーブルから全データを取得
    print("round_resultsテーブルからデータを取得中...")
    results = supabase.table('round_results').select('total_pt').execute()
    
    if results.data:
        total_pts = [r.get('total_pt', 0) or 0 for r in results.data]
        total_sum = sum(total_pts)
        
        print(f"レコード数: {len(total_pts)}")
        print(f"total_pt合計: {total_sum}")
        
        if abs(total_sum) > 0.01:
            print(f"❌ バランス異常: {total_sum:+.1f}")
        else:
            print("✅ バランス正常")
            
        # 統計情報
        print(f"最大値: {max(total_pts)}")
        print(f"最小値: {min(total_pts)}")
        print(f"平均値: {sum(total_pts)/len(total_pts):.2f}")
    else:
        print("データが見つかりません")
        
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()
