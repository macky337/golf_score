from modules.supabase_client import get_supabase_client

def check_constraints():
    supabase = get_supabase_client()
    
    # round_resultsテーブルの外部キー制約を確認
    query = """
    SELECT conname, pg_catalog.pg_get_constraintdef(r.oid, true) as condef 
    FROM pg_catalog.pg_constraint r 
    WHERE r.conrelid = (SELECT oid FROM pg_class WHERE relname = 'round_results') 
    AND r.contype = 'f'
    """
    
    response = supabase.postgrest.schema('public').rpc('exec_sql', {'query': query}).execute()
    
    print('Foreign key constraints on round_results table:')
    for constraint in response.data:
        print(f"{constraint['conname']}: {constraint['condef']}")
    
    # memberとmembersテーブルの存在確認
    tables_query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('member', 'members')
    """
    
    tables_response = supabase.postgrest.schema('public').rpc('exec_sql', {'query': tables_query}).execute()
    
    print('\nExisting tables:')
    for table in tables_response.data:
        print(f"- {table['table_name']}")
    
    # member_idの確認
    if any(table['table_name'] == 'member' for table in tables_response.data):
        member_query = "SELECT member_id, name FROM member ORDER BY member_id"
        member_response = supabase.postgrest.schema('public').rpc('exec_sql', {'query': member_query}).execute()
        
        print('\nEntries in member table:')
        for member in member_response.data:
            print(f"ID: {member['member_id']}, Name: {member.get('name', 'N/A')}")

if __name__ == "__main__":
    check_constraints()