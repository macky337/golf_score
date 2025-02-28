import os
from dotenv import load_dotenv
from supabase import create_client

# 環境変数の読み込み
load_dotenv()

# Supabaseの接続設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("環境変数 SUPABASE_URL または SUPABASE_KEY が設定されていません")

# Supabaseクライアントの作成
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
