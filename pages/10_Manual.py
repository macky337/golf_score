import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

def run():
    # タイトルとホームボタンを横に配置
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("マニュアル")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")
    
    # マニュアルの内容を読み込んで表示
    try:
        manual_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "マニュアル.md")
        with open(manual_path, "r", encoding='utf-8') as f:
            manual_content = f.read()
        st.markdown(manual_content)
    except FileNotFoundError:
        st.error("マニュアルファイルが見つかりません。")

if __name__ == "__main__":
    run()