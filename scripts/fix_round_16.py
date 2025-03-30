import os
import sys
from modules.supabase_client import get_supabase_client

def main():
    """ラウンドID 16のデータを修正する特別スクリプト"""
    print("===== ラウンドID 16 データ修正ツール =====")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # 対象ラウンド
    round_id = 16
    
    # 期待値（正しい値）
    expected_values = {
        1: {"name": "荒巻", "front_gp": -54, "back_gp": -12, "game_pt": -66, "match_pt": 20, "putt_pt": 20, "total_pt": -26},
        2: {"name": "吉井", "front_gp": 54, "back_gp": 48, "game_pt": 102, "match_pt": 30, "putt_pt": -20, "total_pt": 112},
        3: {"name": "福澤", "front_gp": 22, "back_gp": -6, "game_pt": 16, "match_pt": 40, "putt_pt": 20, "total_pt": 76},
        5: {"name": "清村", "front_gp": -22, "back_gp": -30, "game_pt": -52, "match_pt": -90, "putt_pt": -20, "total_pt": -162}
    }
    
    # 現在の値を取得
    print("\n1. 現在のデータの確認...")
    
    # スコアデータ取得
    scores_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
    if not scores_result.data:
        print("スコアデータが見つかりません。")
        return
    
    # round_resultsデータ取得
    round_results_result = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
    if not round_results_result.data:
        print("round_resultsデータが見つかりません。")
        return
    
    # 現在の値と期待値を比較
    print("\n2. データ比較...")
    print(f"{'会員ID':<5} {'名前':<10} {'項目':<15} {'現在値':<10} {'期待値':<10} {'一致':<5}")
    print("-" * 60)
    
    # round_resultsデータをIDで検索できるようにする
    round_results_by_member = {r['member_id']: r for r in round_results_result.data}
    
    need_update = False
    updates = []
    
    for member_id, expected in expected_values.items():
        if member_id not in round_results_by_member:
            print(f"{member_id:<5} {expected['name']:<10} Missing in round_results!")
            continue
            
        current = round_results_by_member[member_id]
        
        # Game Pt確認
        game_pt_current = current.get('total_game_pt', 0)
        game_pt_match = game_pt_current == expected['game_pt']
        print(f"{member_id:<5} {expected['name']:<10} {'Game Pt':<15} {game_pt_current:<10} {expected['game_pt']:<10} {'✓' if game_pt_match else '✗'}")
        
        # Total Pt確認
        total_pt_current = current.get('total_pt', 0)
        total_pt_match = total_pt_current == expected['total_pt']
        print(f"{member_id:<5} {expected['name']:<10} {'Total Pt':<15} {total_pt_current:<10} {expected['total_pt']:<10} {'✓' if total_pt_match else '✗'}")
        
        # 更新が必要なら記録
        if not game_pt_match or not total_pt_match:
            need_update = True
            updates.append({
                "id": current['id'], 
                "member_id": member_id,
                "total_game_pt": expected['game_pt'],
                "total_pt": expected['total_pt']
            })
    
    # 更新確認
    if need_update:
        print("\n3. データの修正が必要です。")
        print("以下の更新を行いますか？")
        for update in updates:
            print(f"会員ID {update['member_id']}: Game Pt → {update['total_game_pt']}, Total Pt → {update['total_pt']}")
        
        confirm = input("\n更新を実行しますか？ [y/N]: ")
        if confirm.lower() == 'y':
            try:
                for update in updates:
                    supabase.table('round_results').update({
                        'total_game_pt': update['total_game_pt'],
                        'total_pt': update['total_pt']
                    }).eq('id', update['id']).execute()
                print("\n✓ データの更新が完了しました。")
            except Exception as e:
                print(f"\n✗ 更新中にエラーが発生しました: {e}")
        else:
            print("\n更新をキャンセルしました。")
    else:
        print("\n✓ すべてのデータが正しい値になっています。更新は必要ありません。")

if __name__ == "__main__":
    main()
