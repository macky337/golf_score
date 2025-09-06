import os
from dotenv import load_dotenv
import streamlit as st
from typing import Optional

# 環境変数の読み込み
load_dotenv()

def get_supabase():
    """Supabaseクライアントを取得する関数"""
    try:
        from modules.supabase_client import get_supabase_client
        return get_supabase_client()
    except Exception:
        return None

def ensure_supabase():
    """Supabaseクライアントを確実に取得し、エラーハンドリングを行う"""
    client = get_supabase()
    if client is None:
        st.error("❌ Supabaseクライアントが利用できません。環境変数を確認してください。")
        st.stop()
    return client

# インポートの簡略化のために、supabase クライアントを直接エクスポート
supabase = get_supabase()
