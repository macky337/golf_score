import os
import sys
from datetime import datetime
import json

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.supabase_client import get_supabase_client, get_scores_with_fallback

def main():
    """ラウンドID 16のround_resultsデータを作成・挿入する"""
    print("===== ラウンドID 16 データ作成ツール =====")
    
    # Supabaseクライアント初期化
    supabase = get_supabase_client()
    
    # 対象ラウンド
    round_id = 16
    
    # まずラウンドの存在を確認
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        print(f"ラウンドID {round_id} が見つかりません。")
        return
    
    round_data = round_result.data[0]
    print(f"ラウンド {round_id}: {round_data['date_played']} - {round_data['course_name']}")
    
    # round_resultsテーブルの既存データを確認
    check_results = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
    if check_results.data and len(check_results.data) > 0:
        print(f"ラウンドID {round_id} のround_resultsデータが {len(check_results.data)} 件見つかりました")
        print("既存のデータ:")
        for r in check_results.data:
            print(f"  メンバーID {r['member_id']}: total_pt={r.get('total_pt')}")
        
        if input("\n既存データを削除して再作成しますか？[y/N]: ").lower() != 'y':
            print("操作をキャンセルしました。")
            return
        
        # 既存データ削除
        supabase.table('round_results').delete().eq('round_id', round_id).execute()
        print(f"ラウンドID {round_id} の既存データを削除しました。")
    
    # スコアデータを取得
    scores = get_scores_with_fallback(round_id)
    
    if not scores:
        print("スコアデータが見つかりません。")
        return
    
    print(f"スコアデータ: {len(scores)}件")
    
    # 各プレイヤーの正しいポイント値（前回の分析で確認済み）
    correct_points = {
        1: {"name": "荒巻", "front_gp": -54, "back_gp": -12, "game_pt": -66, "match_pt": 20, "putt_pt": 20, "total_pt": -26},
        2: {"name": "吉井", "front_gp": 54, "back_gp": 48, "game_pt": 102, "match_pt": 30, "putt_pt": -20, "total_pt": 112},
        3: {"name": "福澤", "front_gp": 22, "back_gp": -6, "game_pt": 16, "match_pt": 40, "putt_pt": 20, "total_pt": 76},
        5: {"name": "清村", "front_gp": -22, "back_gp": -30, "game_pt": -52, "match_pt": -90, "putt_pt": -20, "total_pt": -162}
    }
    
    # スコアデータとマッチング
    records_to_insert = []
    
    for score in scores:
        member_id = score['member_id']
        if member_id in correct_points:
            points = correct_points[member_id]
            
            # round_results テーブル用のレコードを作成
            record = {
                'round_id': round_id,
                'member_id': member_id,
                'match_front': 0, # 元の値がわからない場合はデフォルト値を設定
                'match_back': 0,
                'match_total': 0,
                'match_extra': 0,
                'match_pt': points["match_pt"],
                'putt_pt': points["putt_pt"],
                'total_game_pt': points["game_pt"],
                'total_pt': points["total_pt"]
            }
            
            # マッチポイントを分配（ラウンドタイプによって異なる場合がある）
            # ここでは簡単化のためにmatch_ptの値をmatch_frontに全て入れる
            record['match_front'] = points["match_pt"]
            
            records_to_insert.append(record)
    
    # データ挿入
    if records_to_insert:
        print(f"\n挿入するデータ: {len(records_to_insert)}件")
        print(json.dumps(records_to_insert, indent=2))
        
        if input("\n上記データをround_resultsテーブルに挿入しますか？[y/N]: ").lower() == 'y':
            try:
                result = supabase.table('round_results').insert(records_to_insert).execute()
                print(f"データ挿入成功: {len(result.data)}件")
            except Exception as e:
                print(f"データ挿入エラー: {e}")
        else:
            print("挿入操作をキャンセルしました。")
    else:
        print("挿入するデータがありません。")

if __name__ == "__main__":
    main()
