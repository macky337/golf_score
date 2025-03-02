from modules.db import supabase
import datetime

def test_course_creation():
    """コースの作成をテストする"""
    try:
        # テスト用のコース名
        test_course = {
            'name': 'Test Golf Course',
            'created_at': datetime.datetime.now().isoformat()
        }
        
        print(f"Attempting to create course: {test_course}")
        
        # コースを作成
        response = supabase.table('courses').insert(test_course).execute()
        
        # レスポンスを確認
        print(f"Response data: {response.data}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        if hasattr(e, 'details'):
            print(f"Error details: {e.details}")
        if hasattr(e, 'code'):
            print(f"Error code: {e.code}")

if __name__ == "__main__":
    test_course_creation()