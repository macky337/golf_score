#!/usr/bin/env python3
"""
ラウンドID 53（千葉よみうり）のエキストラスコア問題を調査するスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase

def main():
    print("=== ラウンドID 53（千葉よみうり）の調査 ===")
    
    try:
        # 1. 千葉よみうりのラウンドを検索
        print("\n1. 千葉よみうりのラウンド検索...")
        chiba_rounds = supabase.table('rounds').select('*').ilike('course_name', '%千葉よみうり%').execute()
        
        if chiba_rounds.data:
            print(f"千葉よみうりのラウンド: {len(chiba_rounds.data)}件")
            for round_data in chiba_rounds.data:
                print(f"  round_id: {round_data['round_id']}")
                print(f"  date_played: {round_data['date_played']}")
                print(f"  course_name: {round_data['course_name']}")
                print(f"  num_players: {round_data.get('num_players')}")
                print(f"  has_extra: {round_data.get('has_extra')}")
                print(f"  finalized: {round_data.get('finalized')}")
                print("  ---")
                
                # 該当ラウンドのスコアデータを確認
                round_id = round_data['round_id']
                score_result = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
                
                if score_result.data:
                    print(f"  スコアデータ: {len(score_result.data)}件")
                    for score in score_result.data:
                        member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
                        print(f"    {member_name} (ID: {score['member_id']})")
                        print(f"      front_score: {score.get('front_score')}, back_score: {score.get('back_score')}")
                        print(f"      extra_score: {score.get('extra_score')}, extra_putt: {score.get('extra_putt')}")
                        print(f"      extra_game_pt: {score.get('extra_game_pt')}")
                else:
                    print("  スコアデータなし")
                print("  ===")
        else:
            print("千葉よみうりのラウンドが見つかりません")
        
        # 2. ラウンドID 53を直接検索
        print("\n2. ラウンドID 53を直接検索...")
        round_53 = supabase.table('rounds').select('*').eq('round_id', 53).execute()
        
        if round_53.data:
            round_data = round_53.data[0]
            print("ラウンドID 53が見つかりました:")
            for key, value in round_data.items():
                print(f"  {key}: {value}")
            
            # スコアデータも確認
            score_53 = supabase.table('score').select('*, member:member_id(name)').eq('round_id', 53).execute()
            if score_53.data:
                print(f"\nスコアデータ: {len(score_53.data)}件")
                for score in score_53.data:
                    member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
                    print(f"  {member_name} (ID: {score['member_id']})")
                    print(f"    extra_score: {score.get('extra_score')}")
                    print(f"    extra_putt: {score.get('extra_putt')}")
                    print(f"    extra_game_pt: {score.get('extra_game_pt')}")
        else:
            print("ラウンドID 53が見つかりません")
        
        # 3. 最新のラウンドを確認
        print("\n3. 最新10ラウンドの確認...")
        latest_rounds = supabase.table('rounds').select('round_id, date_played, course_name, has_extra').order('round_id', desc=True).limit(10).execute()
        
        for r in latest_rounds.data:
            print(f"ID: {r['round_id']}, Date: {r['date_played']}, Course: {r['course_name']}, has_extra: {r.get('has_extra')}")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
