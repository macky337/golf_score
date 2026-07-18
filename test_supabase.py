#!/usr/bin/env python3
"""
Supabase接続テストスクリプト
"""
import os
from dotenv import load_dotenv

def check_supabase_connection():
    """手動でSupabase疎通を確認する（pytestの自動テスト対象外）。"""
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"SUPABASE_URL configured: {bool(supabase_url)}")
    print(f"SUPABASE_KEY configured: {bool(supabase_key)}")
    
    if not supabase_url or not supabase_key:
        print("Error: 環境変数が設定されていません")
        return False
    
    try:
        from supabase import create_client
        
        print("Supabaseクライアントをインポートしました")
        
        supabase = create_client(supabase_url, supabase_key)
        print("Supabaseクライアントを作成しました")
        
        # 基本的な接続テスト
        response = supabase.table('rounds').select('*').limit(1).execute()
        print(f"Rounds table response: {response}")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    raise SystemExit(0 if check_supabase_connection() else 1)
