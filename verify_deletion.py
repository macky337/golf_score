#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
削除確認スクリプト - Sample Golf Club (ID: 7) が削除されたかチェック
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase

def verify_deletion():
    """削除の確認"""
    
    course_id = 7
    print("🔍 Sample Golf Club (ID: 7) 削除確認")
    print("=" * 40)
    
    try:
        # 1. コースの確認
        print("1. コース存在確認...")
        course_result = supabase.table('courses').select('*').eq('course_id', course_id).execute()
        if course_result.data:
            print(f"❌ コースがまだ存在しています: {len(course_result.data)}件")
            for course in course_result.data:
                print(f"   - {course}")
        else:
            print("✅ コースは削除されました")
        
        # 2. ラウンドの確認
        print("\n2. 関連ラウンド確認...")
        rounds_result = supabase.table('rounds').select('*').eq('course_id', course_id).execute()
        if rounds_result.data:
            print(f"❌ 関連ラウンドがまだ存在しています: {len(rounds_result.data)}件")
        else:
            print("✅ 関連ラウンドは削除されました")
        
        # 3. スコアの確認
        print("\n3. 関連スコア確認...")
        scores_result = supabase.table('score').select('*').eq('course_id', course_id).execute()
        if scores_result.data:
            print(f"❌ 関連スコアがまだ存在しています: {len(scores_result.data)}件")
        else:
            print("✅ 関連スコアは削除されました")
        
        # 4. 全体サマリー
        print("\n📋 削除確認サマリー:")
        all_deleted = (
            not course_result.data and 
            not rounds_result.data and 
            not scores_result.data
        )
        
        if all_deleted:
            print("🎉 Sample Golf Club (ID: 7) とすべての関連データが正常に削除されました!")
            return True
        else:
            print("⚠️ 一部のデータが残っています。追加の削除処理が必要です。")
            return False
        
    except Exception as e:
        print(f"❌ 確認中にエラー: {str(e)}")
        return False

def check_all_courses():
    """全コースの一覧確認"""
    
    print("\n📊 現在のコース一覧:")
    print("-" * 30)
    
    try:
        all_courses = supabase.table('courses').select('*').order('course_id').execute()
        if all_courses.data:
            print(f"登録済みコース数: {len(all_courses.data)}件")
            for course in all_courses.data:
                print(f"  ID: {course.get('course_id', 'N/A')} - {course.get('course_name', 'N/A')}")
        else:
            print("登録されているコースはありません")
    except Exception as e:
        print(f"❌ コース一覧取得エラー: {str(e)}")

if __name__ == "__main__":
    # 削除確認
    deletion_success = verify_deletion()
    
    # 全コース確認
    check_all_courses()
    
    # 結果
    if deletion_success:
        print("\n✅ 削除処理は正常に完了しました")
        print("💡 管理画面でコース管理を確認してください")
    else:
        print("\n⚠️ 削除処理に問題があります")
        print("💡 詳細調査ページで再度確認してください")
