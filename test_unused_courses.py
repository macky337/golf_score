#!/usr/bin/env python3
from modules.db import supabase
from modules.models import get_unused_courses, delete_unused_courses

def main():
    print("=== 未使用ゴルフ場削除機能テスト ===")
    
    # コース一覧の確認
    print("\n=== 全コース一覧 ===")
    courses = supabase.table('courses').select('*').order('name').execute()
    print(f"コース数: {len(courses.data)}")
    for c in courses.data:
        print(f"  ID:{c['id']} - {c['name']}")
    
    # 使用されているコースIDの確認
    print("\n=== ラウンドで使用されているコース ===")
    rounds = supabase.table('rounds').select('course_id').execute()
    used_course_ids = set()
    for r in rounds.data:
        if r.get('course_id'):
            used_course_ids.add(r['course_id'])
    print(f"使用されているコースID: {sorted(used_course_ids)}")
    
    # 未使用コースの確認
    print("\n=== 未使用ゴルフ場の検出 ===")
    unused_courses = get_unused_courses()
    print(f"未使用ゴルフ場数: {len(unused_courses)}")
    for c in unused_courses:
        print(f"  ID:{c['id']} - {c['name']}")
    
    if unused_courses:
        print("\n=== 削除テスト（確認のみ）===")
        print("削除対象のゴルフ場:")
        for c in unused_courses:
            print(f"  - {c['name']} (ID: {c['id']})")
        
        response = input("\n実際に削除を実行しますか？ (y/n): ")
        if response.lower() == 'y':
            deleted_count, message = delete_unused_courses()
            print(f"\n削除結果: {message}")
        else:
            print("削除をキャンセルしました。")
    else:
        print("削除対象の未使用ゴルフ場はありません。")

if __name__ == "__main__":
    main()
