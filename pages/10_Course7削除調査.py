import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page

def run():
    """Course ID 7 削除阻害要因調査ページ"""
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🔍 Course ID 7 削除問題調査")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")
    
    course_id = 7
    course_name = "Sample Golf Club"
    
    st.info(f"調査対象: {course_name} (ID: {course_id})")
    
    # 1. コースの存在確認
    st.subheader("1. コースの存在確認")
    try:
        course_result = supabase.table('courses').select('*').eq('id', course_id).execute()
        if course_result.data:
            course = course_result.data[0]
            st.success(f"✅ コースが存在します")
            st.json(course)
        else:
            st.error(f"❌ ID {course_id} のコースが見つかりません")
            return
    except Exception as e:
        st.error(f"❌ coursesテーブルのアクセスエラー: {e}")
        return
    
    # 2. roundsテーブルでの使用確認
    st.subheader("2. roundsテーブルでの使用確認")
    try:
        # 正しいクエリ方法
        rounds_result = supabase.table('rounds').select('round_id, date_played, course_name').eq('course_id', course_id).execute()
        
        if rounds_result.data:
            st.warning(f"⚠️ roundsテーブルで {len(rounds_result.data)} 件のラウンドが使用中")
            
            # ラウンドの詳細を表示
            for round_data in rounds_result.data:
                st.write(f"- ラウンドID: {round_data.get('round_id')}, 日付: {round_data.get('date_played')}, コース名: {round_data.get('course_name')}")
        else:
            st.success("✅ roundsテーブルでは使用されていません")
            
        # 現在の is_course_in_use 関数の結果も確認
        st.subheader("3. is_course_in_use 関数のテスト")
        
        # 修正前後の比較
        st.write("**修正後のクエリ結果:**")
        try:
            correct_result = supabase.table('rounds').select('round_id').eq('course_id', course_id).execute()
            st.json(correct_result.data)
            is_used = len(correct_result.data) > 0
            st.write(f"使用中判定: {is_used}")
        except Exception as e:
            st.error(f"修正後クエリでエラー: {e}")
            
    except Exception as e:
        st.error(f"❌ roundsテーブルのアクセスエラー: {e}")
        rounds_result = None
    
    # 4. scoreテーブルでの間接的使用確認
    st.subheader("4. scoreテーブルでの間接的使用確認")
    if rounds_result and rounds_result.data:
        try:
            round_ids = [r.get('round_id') for r in rounds_result.data]
            
            total_scores = 0
            for round_id in round_ids:
                score_result = supabase.table('score').select('score_id').eq('round_id', round_id).execute()
                total_scores += len(score_result.data)
            
            if total_scores > 0:
                st.warning(f"⚠️ scoreテーブルで {total_scores} 件のスコア記録が存在")
            else:
                st.success("✅ 関連するスコア記録はありません")
        except Exception as e:
            st.error(f"❌ scoreテーブルのアクセスエラー: {e}")
    else:
        st.info("📋 確認対象のラウンドがないため、スコア記録の確認をスキップします")
    
    # 5. 解決策の提案
    st.subheader("5. 解決策")
    
    if rounds_result and rounds_result.data:
        st.error("🚫 このコースは削除できません")
        st.write("**削除を阻止している要因:**")
        st.write(f"- {len(rounds_result.data)} 件のラウンドデータ")
        
        st.write("**解決方法:**")
        st.write("1. 管理画面のスコア修正タブでラウンドを削除")
        st.write("2. または、以下の強制削除機能を使用")
        
        # 強制削除セクション
        with st.expander("⚠️ 強制削除（関連データすべて削除）"):
            st.error("注意: この操作により以下のデータが完全に削除されます")
            st.write(f"- ラウンド記録: {len(rounds_result.data)} 件")
            st.write("- 関連するすべてのスコア記録")
            st.write(f"- コース記録: {course_name}")
            
            confirm = st.checkbox("削除を実行することを確認しました", key="confirm_force_delete")
            
            if confirm and st.button("🗑️ 強制削除を実行", type="primary", key="execute_delete"):
                with st.spinner("削除中..."):
                    try:
                        deleted_scores = 0
                        # スコア記録の削除
                        for round_data in rounds_result.data:
                            round_id = round_data.get('round_id')
                            score_result = supabase.table('score').delete().eq('round_id', round_id).execute()
                            deleted_scores += len(score_result.data)
                        
                        # ラウンド記録の削除
                        round_result = supabase.table('rounds').delete().eq('course_id', course_id).execute()
                        deleted_rounds = len(round_result.data)
                        
                        # コース記録の削除
                        course_result = supabase.table('courses').delete().eq('id', course_id).execute()
                        deleted_courses = len(course_result.data)
                        
                        st.success(f"✅ 削除完了:")
                        st.write(f"- スコア記録: {deleted_scores} 件")
                        st.write(f"- ラウンド記録: {deleted_rounds} 件")
                        st.write(f"- コース記録: {deleted_courses} 件")
                        
                        if st.button("コース管理画面へ"):
                            switch_page("コース管理")
                            
                    except Exception as e:
                        st.error(f"❌ 削除中にエラー: {e}")
    else:
        st.success("✅ このコースは削除可能です")
        
        if st.button("🗑️ コースを削除", type="primary"):
            try:
                course_result = supabase.table('courses').delete().eq('id', course_id).execute()
                if course_result.data:
                    st.success(f"✅ {course_name} (ID: {course_id}) を削除しました")
                    if st.button("コース管理画面へ"):
                        switch_page("コース管理")
                else:
                    st.error("削除に失敗しました")
            except Exception as e:
                st.error(f"❌ 削除中にエラー: {e}")

if __name__ == "__main__":
    run()
