from modules.db import supabase

def create_courses_table():
    """coursesテーブルを作成し、既存のラウンドデータからゴルフ場情報を移行"""
    try:
        # 1. coursesテーブルの作成
        print("Creating courses table...")
        supabase.table('courses').delete().neq('id', 0).execute()  # 既存のテーブルをクリア
        
        # 既存のラウンドからユニークなゴルフ場名を取得
        rounds_result = supabase.table('rounds').select('course_name').execute()
        unique_courses = set()
        for round_data in rounds_result.data:
            if round_data['course_name']:
                unique_courses.add(round_data['course_name'].strip())
        
        # ゴルフ場情報を登録
        for course_name in sorted(unique_courses):
            print(f"Adding course: {course_name}")
            supabase.table('courses').insert({
                'name': course_name
            }).execute()
        
        print("Courses table created and populated successfully!")
        
        # 登録されたコース一覧を表示
        courses = supabase.table('courses').select('*').order('name').execute()
        print("\nRegistered courses:")
        for course in courses.data:
            print(f"- {course['name']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_courses_table()