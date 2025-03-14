from modules.supabase_client import get_supabase_client

def fix_table_sequences():
    supabase = get_supabase_client()
    
    # roundsテーブルのシーケンス修正
    sql = """
    CREATE SEQUENCE IF NOT EXISTS rounds_round_id_seq;
    ALTER TABLE rounds ALTER COLUMN round_id SET DEFAULT nextval('rounds_round_id_seq');
    SELECT setval('rounds_round_id_seq', COALESCE((SELECT MAX(round_id) FROM rounds), 0) + 1);
    """
    
    try:
        result = supabase.postgrest.rpc('execute_sql', {'query': sql}).execute()
        print("テーブルのシーケンスを修正しました")
        return True
    except Exception as e:
        print(f"シーケンス修正中にエラーが発生しました: {str(e)}")
        return False

if __name__ == "__main__":
    fix_table_sequences()