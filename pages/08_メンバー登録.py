import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.models import get_members_list

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("メンバー登録")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")

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

if __name__ == "__main__":
    run()
