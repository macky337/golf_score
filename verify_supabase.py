# filepath: /c:/Users/user/Documents/GitHub/golf_score/verify_supabase.py
from modules.db import get_db

def verify_data():
    supabase = get_db()
    response = supabase.table('rounds').select('*').execute()
    print("Rounds data:", response.data)

if __name__ == "__main__":
    verify_data()