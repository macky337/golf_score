from modules.supabase_client import get_supabase_client
import streamlit as st

def delete_round(round_id):
    """ラウンドとそれに関連するデータを削除する"""
    try:
        supabase = get_supabase_client()
        
        # 1. まず関連する round_results レコードを削除
        print(f"ラウンドID {round_id} に関連する round_results データを削除中...")
        results_response = supabase.table("round_results").delete().eq("round_id", round_id).execute()
        print(f"round_results 削除結果: {results_response}")
        
        # 2. 関連する score レコードを削除
        print(f"ラウンドID {round_id} に関連する score データを削除中...")
        score_response = supabase.table("score").delete().eq("round_id", round_id).execute()
        print(f"score 削除結果: {score_response}")
        
        # 3. 最後に rounds テーブルから対象ラウンドを削除
        print(f"ラウンドID {round_id} を削除中...")
        round_response = supabase.table("rounds").delete().eq("round_id", round_id).execute()
        print(f"round 削除結果: {round_response}")
        
        return True, "ラウンドとそれに関連するデータが正常に削除されました。"
    
    except Exception as e:
        error_msg = f"ラウンドの削除中にエラーが発生しました: {e}"
        print(error_msg)
        return False, error_msg