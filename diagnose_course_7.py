#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from modules.db import supabase

def diagnose_course_7():
    """Course ID 7 (Sample Golf Club) の削除阻害要因を調査"""
    
    st.title("🔍 Course ID 7 削除阻害要因調査")
    
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
        st.subheader("3. 現在の is_course_in_use 関数の結果")
        try:
            # 問題のあるクエリを実行してみる
            result = supabase.table('rounds').select('count').eq('course_id', course_id).execute()
            st.write("問題のあるクエリ結果:")
            st.json(result.data)
            st.write(f"len(result.data) > 0 = {len(result.data) > 0}")
        except Exception as e:
            st.error(f"問題のあるクエリでエラー: {e}")
            
        # 正しいクエリ
        try:
            correct_result = supabase.table('rounds').select('round_id').eq('course_id', course_id).execute()
            st.write("正しいクエリ結果:")
            st.json(correct_result.data)
            st.write(f"len(correct_result.data) > 0 = {len(correct_result.data) > 0}")
        except Exception as e:
            st.error(f"正しいクエリでエラー: {e}")
            
    except Exception as e:
        st.error(f"❌ roundsテーブルのアクセスエラー: {e}")
    
    # 4. scoreテーブルでの間接的使用確認
    st.subheader("4. scoreテーブルでの間接的使用確認")
    try:
        if rounds_result.data:
            round_ids = [r.get('round_id') for r in rounds_result.data]
            
            score_count = 0
            for round_id in round_ids:
                score_result = supabase.table('score').select('score_id').eq('round_id', round_id).execute()
                score_count += len(score_result.data)
            
            if score_count > 0:
                st.warning(f"⚠️ scoreテーブルで {score_count} 件のスコア記録が存在")
            else:
                st.success("✅ 関連するスコア記録はありません")
        else:
            st.info("📋 確認対象のラウンドがないため、スコア記録もありません")
    except Exception as e:
        st.error(f"❌ scoreテーブルのアクセスエラー: {e}")
    
    # 5. 解決策の提案
    st.subheader("5. 解決策")
    
    if rounds_result.data:
        st.error("🚫 このコースは削除できません")
        st.write("**削除を阻止している要因:**")
        st.write(f"- {len(rounds_result.data)} 件のラウンドデータ")
        
        st.write("**解決方法:**")
        st.write("1. 管理画面のスコア修正タブでラウンドを削除")
        st.write("2. または、関連データを含めて強制削除")
        
        # 強制削除ボタン
        st.warning("⚠️ 強制削除は関連するすべてのデータが失われます")
        
        if st.button("🗑️ 関連データを含めて強制削除", type="secondary"):
            confirm = st.checkbox("削除を実行することを確認しました", key="confirm_force_delete")
            
            if confirm and st.button("削除を実行", type="primary", key="execute_delete"):
                with st.spinner("削除中..."):
                    try:
                        # スコア記録の削除
                        for round_id in [r.get('round_id') for r in rounds_result.data]:
                            supabase.table('score').delete().eq('round_id', round_id).execute()
                        
                        # ラウンド記録の削除
                        supabase.table('rounds').delete().eq('course_id', course_id).execute()
                        
                        # コース記録の削除
                        supabase.table('courses').delete().eq('id', course_id).execute()
                        
                        st.success(f"✅ {course_name} (ID: {course_id}) を削除しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 削除中にエラー: {e}")
    else:
        st.success("✅ このコースは削除可能です")
        
        if st.button("🗑️ コースを削除", type="primary"):
            try:
                supabase.table('courses').delete().eq('id', course_id).execute()
                st.success(f"✅ {course_name} (ID: {course_id}) を削除しました")
                st.rerun()
            except Exception as e:
                st.error(f"❌ 削除中にエラー: {e}")

if __name__ == "__main__":
    diagnose_course_7()
