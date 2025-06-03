#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Golf Club (ID: 7) を安全に削除するスクリプト

⚠️ 警告: このスクリプトを実行すると、関連するすべてのデータが削除されます
- ラウンド記録
- スコア記録  
- コース記録

実行前に必ずバックアップを確認してください。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase

def delete_course_7_safely():
    """Sample Golf Club (ID: 7) を関連データと共に安全に削除"""
    
    course_id = 7
    course_name = "Sample Golf Club"
    
    print(f"=== {course_name} (ID: {course_id}) 削除処理開始 ===\n")
    
    try:
        # 1. コースの存在確認
        print("1. コースの存在確認...")
        course_result = supabase.table('courses').select('*').eq('id', course_id).execute()
        if not course_result.data:
            print(f"❌ ID {course_id} のコースが見つかりません")
            return False
        
        course = course_result.data[0]
        print(f"✅ コースが見つかりました: {course['name']}")
        
        # 2. 使用中のラウンドを確認
        print("\n2. 使用中のラウンドを確認...")
        rounds_result = supabase.table('rounds').select('round_id, date_played, course_name').eq('course_id', course_id).execute()
        
        if not rounds_result.data:
            print("✅ 使用中のラウンドはありません")
            # 単純削除
            print("\n3. コースを削除...")
            delete_result = supabase.table('courses').delete().eq('id', course_id).execute()
            if delete_result.data:
                print(f"✅ {course_name} (ID: {course_id}) を削除しました")
                return True
            else:
                print("❌ コースの削除に失敗しました")
                return False
        
        # 関連データがある場合
        round_ids = [r['round_id'] for r in rounds_result.data]
        print(f"⚠️ 使用中のラウンド: {len(round_ids)} 件")
        
        for round_data in rounds_result.data:
            print(f"  - ラウンドID: {round_data['round_id']}, 日付: {round_data['date_played']}")
        
        # 3. 関連スコア記録の確認
        print("\n3. 関連スコア記録の確認...")
        total_scores = 0
        score_details = []
        
        for round_id in round_ids:
            score_result = supabase.table('score').select('score_id, member_id').eq('round_id', round_id).execute()
            scores_count = len(score_result.data)
            total_scores += scores_count
            if scores_count > 0:
                score_details.append(f"  - ラウンドID {round_id}: {scores_count} 件のスコア")
        
        if total_scores > 0:
            print(f"⚠️ 関連スコア記録: {total_scores} 件")
            for detail in score_details:
                print(detail)
        else:
            print("✅ 関連スコア記録はありません")
        
        # 4. 削除確認
        print(f"\n4. 削除内容の確認")
        print(f"削除されるデータ:")
        print(f"  - コース: {course_name} (ID: {course_id})")
        print(f"  - ラウンド記録: {len(round_ids)} 件")
        print(f"  - スコア記録: {total_scores} 件")
        print()
        
        # ユーザー確認
        while True:
            confirm = input("本当に削除しますか？ (yes/no): ").strip().lower()
            if confirm in ['yes', 'y']:
                break
            elif confirm in ['no', 'n']:
                print("削除をキャンセルしました")
                return False
            else:
                print("'yes' または 'no' で回答してください")
        
        # 5. 削除実行
        print("\n5. 削除実行中...")
        
        # スコア記録の削除
        deleted_scores = 0
        if round_ids:
            print("  スコア記録を削除中...")
            for round_id in round_ids:
                score_result = supabase.table('score').delete().eq('round_id', round_id).execute()
                deleted_scores += len(score_result.data)
            print(f"  ✅ スコア記録 {deleted_scores} 件を削除しました")
        
        # ラウンド記録の削除
        print("  ラウンド記録を削除中...")
        round_result = supabase.table('rounds').delete().eq('course_id', course_id).execute()
        deleted_rounds = len(round_result.data)
        print(f"  ✅ ラウンド記録 {deleted_rounds} 件を削除しました")
        
        # コース記録の削除
        print("  コース記録を削除中...")
        course_delete_result = supabase.table('courses').delete().eq('id', course_id).execute()
        deleted_courses = len(course_delete_result.data)
        print(f"  ✅ コース記録 {deleted_courses} 件を削除しました")
        
        # 6. 結果報告
        print(f"\n✅ {course_name} (ID: {course_id}) の削除が完了しました")
        print(f"削除されたデータ:")
        print(f"  - スコア記録: {deleted_scores} 件")
        print(f"  - ラウンド記録: {deleted_rounds} 件")
        print(f"  - コース記録: {deleted_courses} 件")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 削除処理中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン実行関数"""
    try:
        success = delete_course_7_safely()
        if success:
            print("\n🎉 削除処理が正常に完了しました")
        else:
            print("\n⚠️ 削除処理が中断またはエラーで終了しました")
    except KeyboardInterrupt:
        print("\n\n⚠️ 処理がユーザーによって中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
