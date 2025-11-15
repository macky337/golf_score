import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from modules.db import ensure_supabase
from modules.page_utils import switch_page
from modules.models import get_course_list, create_course, is_course_in_use, update_rounds_course_references, get_unused_courses, delete_unused_courses

st.set_page_config(
    page_title="コース管理 - Golf Score App",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run():
    # スマホでサイドバーを自動的に閉じる
    close_sidebar_on_mobile()
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("コース管理")
    with col2:
        if st.button("🏠 Home"):
            st.switch_page("main.py")
            
    # 既存コースの一覧を表示
    courses = get_course_list()
    
    # マイグレーションボタン（一度だけ実行）
    if st.sidebar.button("ラウンドデータのコース参照を更新"):
        with st.spinner("ラウンドデータを更新中..."):
            count = update_rounds_course_references()
            st.sidebar.success(f"{count}件のラウンドデータを更新しました")
    
    if courses:
        st.write("### 登録済みコース")
        
        # 未使用ゴルフ場の一括削除機能
        st.write("#### 🗑️ 未使用ゴルフ場の一括削除")
        unused_courses = get_unused_courses()
        
        if unused_courses:
            st.warning(f"⚠️ {len(unused_courses)}個の未使用ゴルフ場が見つかりました")
            
            # 未使用ゴルフ場の一覧を表示
            unused_df = pd.DataFrame(
                [(c.get('id', ''), c.get('name', '')) for c in unused_courses],
                columns=["ID", "ゴルフ場名"]
            )
            st.dataframe(unused_df, use_container_width=True)
            
            # 削除確認
            with st.expander("⚠️ 未使用ゴルフ場を一括削除"):
                st.error("注意: この操作は取り消せません。上記の未使用ゴルフ場がすべて削除されます。")
                confirm_bulk_delete = st.checkbox("未使用ゴルフ場を一括削除することを確認しました", key="confirm_bulk_delete")
                
                if st.button("未使用ゴルフ場を一括削除", disabled=not confirm_bulk_delete, type="primary", key="bulk_delete_button"):
                    with st.spinner("未使用ゴルフ場を削除中..."):
                        deleted_count, message = delete_unused_courses()
                        if deleted_count > 0:
                            st.success(message)
                            st.rerun()
                        else:
                            st.info(message)
        else:
            st.success("✅ 未使用のゴルフ場はありません")
        
        st.write("---")
          # 削除対象のコース選択用のセレクトボックス
        st.write("#### 個別コース削除")
        delete_course_id = st.selectbox(
            "削除するコースを選択",
            options=[None] + [(c.get('id', ''), c.get('name', '')) for c in courses],
            format_func=lambda x: "選択してください" if x is None else f"{x[1]} (ID: {x[0]})"
        )
        
        if delete_course_id:
            course_id, course_name = delete_course_id
            # コースが使用中か確認
            if is_course_in_use(course_id):
                st.warning(f"「{course_name}」はラウンドデータで使用されているため削除できません")
                
                # 詳細情報の表示
                try:
                    rounds_result = supabase.table('rounds').select('round_id, date_played').eq('course_id', course_id).execute()
                    if rounds_result.data:
                        st.info(f"📊 使用中のラウンド数: {len(rounds_result.data)} 件")
                        
                        with st.expander("📋 使用中のラウンド詳細"):
                            for round_data in rounds_result.data:
                                st.write(f"- ラウンドID: {round_data.get('round_id')}, 日付: {round_data.get('date_played')}")
                        
                        # 解決策の提示
                        st.write("**解決方法:**")
                        st.write("1. 管理画面のスコア修正タブで関連ラウンドを削除")
                        st.write("2. または、詳細調査ページで強制削除を実行")
                        
                        # 詳細調査ページへのリンク
                        if st.button("🔍 詳細調査ページで確認", help="Course ID 7の削除問題を詳しく調査"):
                            switch_page("Course7削除調査")
                            
                except Exception as e:
                    st.error(f"ラウンド使用状況の確認でエラー: {e}")
            else:
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