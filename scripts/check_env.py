from dotenv import load_dotenv
import os

def check_env():
    load_dotenv()
    
    # 環境変数の確認
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        return False
    
    print("✅ 環境変数の設定は正常です")
    return True

if __name__ == '__main__':
    check_env()