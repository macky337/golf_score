import os
from supabase import create_client
from dotenv import load_dotenv

def add_game_pt_columns():
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        return
    
    supabase = create_client(url, key)
    
    try:
        # PostgreSQLのALTER TABLE文を直接実行
        sql = """
        ALTER TABLE score 
        ADD COLUMN IF NOT EXISTS temp_game_pt integer,
        ADD COLUMN IF NOT EXISTS total_game_pt integer;
        """
        
        result = supabase.postgrest.rpc('execute_sql', {'query': sql}).execute()
        print("Successfully added new columns")
        print(result)
        
    except Exception as e:
        print(f"Error adding columns: {str(e)}")

if __name__ == "__main__":
    add_game_pt_columns()