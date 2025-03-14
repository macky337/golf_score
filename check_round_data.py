import pandas as pd
from modules.db import supabase
import argparse
import sys
import streamlit as st
from modules.data_integrity import verify_putt_points

def check_round_data(round_id=None, show_all=False, limit=10):
    """
    Check round data in the database
    
    Args:
        round_id (int, optional): Specific round ID to check
        show_all (bool): Show all rounds info
        limit (int): Limit for the number of rounds/scores to display
    """
    print("=== Golf Score Database Checker ===")
    
    # Get all rounds info
    rounds_result = supabase.table('rounds').select('*').order('round_id', desc=True).execute()
    rounds = rounds_result.data
    
    print(f"Total rounds in database: {len(rounds)}")
    
    # Show all rounds info if requested
    if show_all:
        print("\n=== All Rounds ===")
        rounds_df = pd.DataFrame(rounds)
        print(rounds_df.to_string())
    
    # Check specific round ID
    if round_id:
        print(f"\n=== Checking Round ID: {round_id} ===")
        # Round info
        round_info = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        
        if round_info.data:
            print(f"Round ID {round_id} exists!")
            print("Round info:")
            print(pd.DataFrame([round_info.data[0]]).to_string())
            
            # Score info
            scores = supabase.table('score').select('*').eq('round_id', round_id).execute()
            
            if scores.data:
                print(f"\nFound {len(scores.data)} score records for Round ID {round_id}:")
                scores_df = pd.DataFrame(scores.data)
                print(scores_df.to_string())
            else:
                print(f"\nNo score data found for Round ID {round_id}")
        else:
            print(f"Round ID {round_id} does not exist!")
    
    # Show latest scores
    print("\n=== Latest Score Data ===")
    latest_scores = supabase.table('score').select('*').order('score_id', desc=True).limit(limit).execute()
    if latest_scores.data:
        latest_df = pd.DataFrame(latest_scores.data)
        print(latest_df.to_string())
    else:
        print("No score data found")

def main():
    st.title("ラウンドデータ検証")
    
    # 検証するラウンドID
    round_id = 41  # 2025-03-03 - テストコース
    
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        st.error(f"ラウンドID {round_id} が見つかりません")
        return
    
    round_data = round_result.data[0]
    st.write(f"### {round_data['date_played']} - {round_data['course_name']} (ID: {round_id})")
    
    # パット戦ポイントの検証
    st.write("### パット戦ポイント計算の検証")
    with st.spinner("検証中..."):
        result = verify_putt_points(round_id)
    
    if result.get("status") == "error":
        st.error(f"検証中にエラーが発生しました: {result['message']}")
        return
    
    # プレイヤー情報を表示
    st.write(f"プレイヤー数: {result['player_count']}")
    
    # データフレームの作成
    player_data = []
    for p in result["players"]:
        player_data.append({
            "名前": p["name"],
            "パット数": p["front_putt"] + p["back_putt"] + p.get("extra_putt", 0),
            "計算合計": p["calculated_putt_pt"],
            "実際の値": p["actual_putt_pt"],
            "差分": p["calculated_putt_pt"] - p["actual_putt_pt"]
        })
    
    df = pd.DataFrame(player_data)
    st.dataframe(df)
    
    # 検証結果
    if result["is_correct"]:
        st.success("✅ パット戦のポイント計算は正確です")
    else:
        st.error("❌ パット戦のポイント計算に不一致があります")
        
        st.write("### 不一致の詳細")
        diff_data = []
        for d in result["differences"]:
            diff_data.append({
                "プレイヤー": d["player"],
                "実際の値": d["actual"],
                "計算値": d["calculated"],
                "差分": d["diff"]
            })
        
        st.dataframe(pd.DataFrame(diff_data))
        
        # 不一致があれば修正オプションを提供
        if st.button("パット戦のポイントを修正"):
            try:
                # スコアデータを更新
                for p in result["players"]:
                    supabase.table('score').update({
                        'putt_pt': p["calculated_putt_pt"]
                    }).eq('member_id', p["member_id"]).eq('round_id', round_id).execute()
                
                st.success("パット戦のポイントを修正しました")
                st.rerun()  # ページを再読み込み
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
