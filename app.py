"""
アプリのエントリポイント
このスクリプトを Streamlit で起動すると `main.py` の `main()` が呼び出されます。
"""
import streamlit as st

# Streamlit ページ設定（最初に実行する必要がある）
st.set_page_config(
    page_title="Golf Score App", 
    page_icon="⛳",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': "Golf Score App - main"
    }
)

# main.pyから必要な関数をインポート
from main import main

if __name__ == "__main__":
    main()