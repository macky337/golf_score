"""
アプリケーション設定ファイル
"""
import os
from dotenv import load_dotenv
import streamlit as st

# .envファイルを読み込む
load_dotenv()

# 管理者設定
ADMIN = {
    'password': 'admin'  # 管理画面のパスワード
}

# アプリケーション設定
APP = {
    'name': 'Golf Score App',
    'version': '1.0.0'
}

# データベース設定
DATABASE = {
    'supabase_url': os.getenv('SUPABASE_URL'),
    'supabase_key': os.getenv('SUPABASE_KEY')
}

# ファイルパス設定
PATHS = {
    'fonts': {
        'japanese': 'ipaexg.ttf'
    }
}

# 取得
def get_admin_password():
    """管理画面用のパスワードを取得する
    
    環境変数 > Streamlit secrets > デフォルトパスワード の順で探索
    """
    # 1. 環境変数から取得
    if 'ADMIN_PASSWORD' in os.environ:
        return os.environ['ADMIN_PASSWORD']
    
    # 2. Streamlit secretsから取得
    try:
        if 'admin_password' in st.secrets:
            return st.secrets['admin_password']
    except Exception:
        pass  # secretsがない場合は無視
    
    # 3. デフォルトパスワード
    return "golf_score_admin"

def get_app_name():
    """アプリ名を取得"""
    return APP['name']

def get_app_version():
    """アプリバージョンを取得"""
    return APP['version']

def get_db_config():
    """データベース設定を取得"""
    return DATABASE

def get_font_path(font_type='japanese'):
    """フォントパスを取得"""
    return PATHS['fonts'].get(font_type, None)