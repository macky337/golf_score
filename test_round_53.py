#!/usr/bin/env python3
"""
ラウンドID 53（千葉よみうり）の簡単なテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import streamlit as st
    from modules.db import supabase
    
    print("=== ラウンドID 53（千葉よみうり）のテスト ===")
    
    # ラウンドID 53を直接検索
    print("ラウンドID 53を検索中...")
    round_53 = supabase.table('rounds').select('*').eq('round_id', 53).execute()
    
    if round_53.data:
        round_data = round_53.data[0]
        print("✓ ラウンドID 53が見つかりました:")
        print(f"  日付: {round_data.get('date_played')}")
        print(f"  コース: {round_data.get('course_name')}")
        print(f"  プレイヤー数: {round_data.get('num_players')}")
        print(f"  エキストラフラグ: {round_data.get('has_extra')}")
        print(f"  確定フラグ: {round_data.get('finalized')}")
        
        # スコアデータを確認
        score_53 = supabase.table('score').select('*, member:member_id(name)').eq('round_id', 53).execute()
        if score_53.data:
            print(f"\n✓ スコアデータ: {len(score_53.data)}件")
            for score in score_53.data:
                member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
                print(f"  {member_name} (ID: {score['member_id']})")
                print(f"    front: {score.get('front_score')}, back: {score.get('back_score')}")
                print(f"    extra: {score.get('extra_score')}, putt: {score.get('extra_putt')}")
                print(f"    game_pt: {score.get('extra_game_pt')}")
        else:
            print("❌ スコアデータなし")
    else:
        print("❌ ラウンドID 53が見つかりません")
        
        # 代わりに千葉よみうりのラウンドを検索
        print("\n千葉よみうりのラウンド検索中...")
        chiba_rounds = supabase.table('rounds').select('*').ilike('course_name', '%千葉%').execute()
        
        if chiba_rounds.data:
            print(f"✓ 千葉関連のラウンド: {len(chiba_rounds.data)}件")
            for round_data in chiba_rounds.data:
                print(f"  ID: {round_data['round_id']}, 日付: {round_data['date_played']}")
                print(f"  コース: {round_data['course_name']}")
        else:
            print("❌ 千葉関連のラウンドが見つかりません")

except Exception as e:
    print(f"❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
