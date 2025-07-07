import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from modules.db import ensure_supabase
from modules.page_utils import switch_page
from modules.models import get_members_list

# ページ設定
st.set_page_config(
    page_title="メンバー登録 - Golf Score App",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run():
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("メンバー登録")
    with col2:
        if st.button("🏠 Home"):
            st.switch_page("main.py")

    # 既存メンバーの表示（ID昇順で取得するように変更）
    members = get_members_list()

    if members:
        st.write("### 登録済みメンバー")
        member_df = pd.DataFrame(
            [(m['member_id'], m['name']) for m in members],
            columns=["ID", "名前"]
        )
        # データフレームをIDの昇順で表示することを明示
        member_df = member_df.sort_values("ID", ascending=True)
        st.dataframe(member_df)

    # 新規メンバー追加フォーム
    with st.form("add_member_form"):
        st.write("### 新規メンバー追加")
        new_name = st.text_input("名前")
        if st.form_submit_button("追加"):
            if new_name:
                try:
                    # 同じ名前のメンバーが既に存在するかチェック
                    existing = supabase.table('member').select('*').eq('name', new_name).execute()
                    if existing.data:
                        st.error(f"メンバー「{new_name}」は既に登録されています")
                    else:
                        # 最大のmember_idを取得して、新しいIDを作成
                        max_id_result = supabase.table('member').select('member_id').order('member_id', desc=True).limit(1).execute()
                        next_id = 1
                        if max_id_result.data:
                            next_id = max_id_result.data[0]['member_id'] + 1
                        
                        # member_idを明示的に指定して挿入
                        supabase.table('member').insert({
                            'member_id': next_id,
                            'name': new_name
                        }).execute()
                        
                        st.success(f"メンバー「{new_name}」を追加しました (ID: {next_id})")
                        st.rerun()
                except Exception as e:
                    st.error(f"メンバーの追加に失敗しました: {str(e)}")
            else:
                st.warning("名前を入力してください")

    # --- ラウンド未参加メンバー削除機能 ---
    st.write("### ラウンド未参加メンバーの一括削除")
    if st.button("ラウンド未参加メンバーを削除", key="delete_unplayed_members"):
        try:
            # すべてのメンバーIDを取得
            all_members = supabase.table('member').select('member_id', 'name').execute().data
            all_member_ids = [m['member_id'] for m in all_members]
            # スコアテーブルに一度も出現しないmember_idを抽出
            played_member_ids = set()
            scores = supabase.table('score').select('member_id').execute().data
            for s in scores:
                played_member_ids.add(s['member_id'])
            unplayed_members = [m for m in all_members if m['member_id'] not in played_member_ids]
            if not unplayed_members:
                st.info("すべてのメンバーがラウンドに参加しています。削除対象はありません。")
            else:
                for m in unplayed_members:
                    supabase.table('member').delete().eq('member_id', m['member_id']).execute()
                st.success(f"{len(unplayed_members)}名の未参加メンバーを削除しました。")
                st.rerun()
        except Exception as e:
            st.error(f"未参加メンバーの削除に失敗しました: {str(e)}")
    # --- ここまで ---

if __name__ == "__main__":
    run()
