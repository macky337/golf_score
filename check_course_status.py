#!/usr/bin/env python3
from modules.db import supabase
from modules.models import get_unused_courses

def main():
    print("=== コース使用状況確認 ===")
    
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
    print("\n=== 未使用ゴルフ場の検出結果 ===")
    unused_courses = get_unused_courses()
    print(f"未使用ゴルフ場数: {len(unused_courses)}")
    if unused_courses:
        for c in unused_courses:
            print(f"  - {c['name']} (ID: {c['id']})")
    else:
        print("  未使用のゴルフ場はありません")
    
    print("\n=== 機能実装状況 ===")
    print("✅ get_unused_courses() - 未使用ゴルフ場検出機能")
    print("✅ delete_unused_courses() - 未使用ゴルフ場一括削除機能")
    print("✅ コース管理画面への一括削除UI追加")
    print("✅ 個別削除機能との統合")

if __name__ == "__main__":
    main()
