from modules.supabase_client import get_supabase_client

def create_round_results_table():
    """Create round_results table for storing calculated points"""
    supabase = get_supabase_client()
    
    # Create round_results table using SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS round_results (
        id BIGSERIAL PRIMARY KEY,
        round_id BIGINT NOT NULL,
        member_id BIGINT NOT NULL,
        match_front INTEGER DEFAULT 0,
        match_back INTEGER DEFAULT 0,
        match_total INTEGER DEFAULT 0,
        match_extra INTEGER DEFAULT 0,
        match_pt INTEGER DEFAULT 0,
        putt_pt INTEGER DEFAULT 0,
        temp_game_pt INTEGER DEFAULT 0,
        total_game_pt INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        FOREIGN KEY (round_id) REFERENCES rounds(round_id),
        FOREIGN KEY (member_id) REFERENCES member(member_id),
        UNIQUE(round_id, member_id)
    );
    """
    
    try:
        supabase.table("round_results").select("*").limit(1).execute()
        print("round_results table already exists")
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            # テーブルが存在しない場合は作成
            response = supabase.postgrest.schema("public").rpc("exec_sql", {"query": create_table_sql}).execute()
            print("Created round_results table")
            return True
        else:
            raise e

def main():
    try:
        create_round_results_table()
        print("Successfully completed round_results table setup")
    except Exception as e:
        print(f"Error creating round_results table: {e}")

if __name__ == "__main__":
    main()