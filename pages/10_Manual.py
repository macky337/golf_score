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
        # 複数のパス候補を順に試す
        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "マニュアル.md"),
            os.path.join(os.getcwd(), "マニュアル.md"),
            os.path.abspath("マニュアル.md"),
            os.path.join(os.path.dirname(__file__), "..", "マニュアル.md"),
            os.path.join(os.path.dirname(__file__), "../..", "マニュアル.md")
        ]
        manual_content = None
        for manual_path in candidates:
            if os.path.exists(manual_path):
                with open(manual_path, "r", encoding='utf-8') as f:
                    manual_content = f.read()
                break
        if manual_content:
            st.markdown(manual_content)
        else:
            st.error(f"マニュアルファイルが見つかりません。パス候補: {candidates}")
    except Exception as e:
        st.error(f"マニュアルファイルの読み込み中にエラー: {e}")

if __name__ == "__main__":
    run()