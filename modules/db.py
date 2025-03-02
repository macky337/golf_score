import os
from dotenv import load_dotenv
from modules.supabase_client import get_supabase_client

# 環境変数の読み込み
load_dotenv()

# Supabaseの接続設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("環境変数 SUPABASE_URL または SUPABASE_KEY が設定されていません")

# インポートの簡略化のために、supabase クライアントを直接エクスポート
supabase = get_supabase_client()
