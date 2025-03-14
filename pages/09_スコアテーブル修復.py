import streamlit as st
import time
from modules.restore_score_table import restore_combined_score_table

def run():
    st.title("スコアテーブル修復ツール")
    st.write("""
    このツールは、Supabaseのスコアテーブルが破損した場合に、複数のバックアップからスコアデータを復元します。
    2つのバックアップファイルのデータを統合して、すべてのカラムに完全なデータを復元します。
    """)
    
    st.info("""
    使用するバックアップファイル:
    - `backups/golf_score_backup_20250225_140823.json` (メイン)
    - `backups/remote_main_backup_20250225_140525.json` (追加)
    """)
    
    st.warning("⚠️ この操作はスコアテーブル内の既存のデータをすべて削除し、バックアップから復元します。この操作は取り消せません。")
    
    if st.button("スコアテーブルを修復", type="primary"):
        with st.spinner("スコアテーブルを復元中..."):
            success = restore_combined_score_table()
            if success:
                st.success("スコアテーブルの復元が完了しました！")
                st.balloons()
                # 数秒後にページをリロード
                time.sleep(3)
                st.rerun()
            else:
                st.error("スコアテーブルの復元に失敗しました。上記のエラーメッセージを確認してください。")

if __name__ == "__main__":
    run()