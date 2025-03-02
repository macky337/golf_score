import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.models import get_course_list, create_course

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("コース管理")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")
            
    # 既存コースの一覧を表示
    courses = get_course_list()
    
    if courses:
        st.write("### 登録済みコース")
        
        # 削除対象のコース選択用のセレクトボックス
        delete_course_id = st.selectbox(
            "削除するコースを選択",
            options=[None] + [(c.get('id', ''), c.get('name', '')) for c in courses],
            format_func=lambda x: "選択してください" if x is None else f"{x[1]} (ID: {x[0]})"
        )
        
        if delete_course_id:
            course_id, course_name = delete_course_id
            # 削除確認
            if st.button(f"「{course_name}」を削除", type="primary", help="このコースを削除します"):
                try:
                    # コース削除処理
                    result = supabase.table('courses').delete().eq('id', course_id).execute()
                    if result.data:
                        st.success(f"ゴルフ場「{course_name}」を削除しました")
                        # 画面更新
                        st.rerun()
                    else:
                        st.error("削除に失敗しました。別の画面で利用されている可能性があります。")
                except Exception as e:
                    st.error(f"削除中にエラーが発生しました: {str(e)}")
        
        # コース一覧をテーブル表示
        course_df = pd.DataFrame(
            [(c.get('id', ''), c.get('name', '')) for c in courses],
            columns=["ID", "ゴルフ場名"]
        )
        st.dataframe(course_df)
    else:
        st.info("登録されているコースはありません。")
    
    # 新規コース追加フォーム
    with st.form("add_course_form"):
        st.write("### 新規コース追加")
        new_course_name = st.text_input("ゴルフ場名")
        
        submit = st.form_submit_button("追加")
        if submit:
            if new_course_name:
                try:
                    # 同じ名前のコースが既に存在するかチェック
                    existing = [c for c in courses if c.get('name', '').lower() == new_course_name.lower()]
                    if existing:
                        st.error(f"ゴルフ場「{new_course_name}」は既に登録されています")
                    else:
                        # 新しいコースを作成
                        new_course = create_course(new_course_name)
                        if new_course:
                            st.success(f"ゴルフ場「{new_course_name}」を追加しました")
                            st.rerun()
                        else:
                            st.error("ゴルフ場の追加に失敗しました")
                except Exception as e:
                    st.error(f"ゴルフ場の追加中にエラーが発生しました: {str(e)}")
            else:
                st.warning("ゴルフ場名を入力してください")

if __name__ == "__main__":
    run()