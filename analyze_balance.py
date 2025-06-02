import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client

def analyze_balance():
    """ポイントバランスを非対話的に分析"""
    
    # 環境変数読み込み
    load_dotenv()
    
    # Supabaseクライアント作成
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("ERROR: Supabase credentials not found")
        return
    
    supabase = create_client(url, key)
    
    try:
        print("=== ポイントバランス分析 ===")
        
        # round_resultsテーブルからデータ取得
        print("1. round_resultsテーブルからデータ取得中...")
        results = supabase.table('round_results').select('round_id, member_id, total_pt').execute()
        
        if not results.data:
            print("ERROR: データが見つかりません")
            return
        
        print(f"   レコード数: {len(results.data)}")
        
        # 2. 全体合計計算
        total_sum = 0
        round_balances = {}
        
        for record in results.data:
            total_pt = float(record.get('total_pt') or 0)
            round_id = record.get('round_id')
            
            total_sum += total_pt
            
            if round_id not in round_balances:
                round_balances[round_id] = 0
            round_balances[round_id] += total_pt
        
        print(f"2. 全体合計: {total_sum}")
        
        # 3. バランス崩れラウンド特定
        unbalanced = []
        for round_id, balance in round_balances.items():
            if abs(balance) > 0.01:
                unbalanced.append((round_id, balance))
        
        print(f"3. バランス崩れラウンド数: {len(unbalanced)}")
        
        if unbalanced:
            # 最も問題の大きいラウンドを特定
            unbalanced.sort(key=lambda x: abs(x[1]), reverse=True)
            worst_rounds = unbalanced[:5]
            
            print("   最も問題の大きいラウンド (トップ5):")
            for round_id, balance in worst_rounds:
                print(f"     ラウンドID {round_id}: {balance:+.1f}")
                
            # 最悪のラウンドの詳細
            worst_round_id, worst_balance = worst_rounds[0]
            print(f"\n4. 最悪ラウンド ({worst_round_id}) の詳細:")
            
            worst_records = [r for r in results.data if r.get('round_id') == worst_round_id]
            print(f"   参加者数: {len(worst_records)}")
            
            for record in worst_records:
                member_id = record.get('member_id')
                total_pt = record.get('total_pt', 0)
                print(f"     メンバーID {member_id}: {total_pt}")
            
        else:
            print("   ✅ すべてのラウンドでバランスが取れています")
            
        print(f"\n5. 結論:")
        if abs(total_sum) > 0.01:
            print(f"   ❌ 全体バランス異常: {total_sum:+.1f}")
            print(f"   📊 問題ラウンド: {len(unbalanced)}個")
        else:
            print("   ✅ 全体バランス正常")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_balance()
