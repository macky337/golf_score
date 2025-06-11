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
        if st.button("🏠 Home", key="manual_home_button"):
            switch_page("main")
    
    # マニュアルの内容を読み込んで表示
    try:
        # 複数のパスを試行する（より堅牢なファイル検索）
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "マニュアル.md"),
            os.path.join(os.getcwd(), "マニュアル.md"),
            r"C:\Users\user\Documents\GitHub\golf_score\マニュアル.md",
            "マニュアル.md"
        ]
        
        manual_content = None
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r", encoding='utf-8') as f:
                    manual_content = f.read()
                break
        
        if manual_content:
            st.markdown(manual_content)
        else:
            raise FileNotFoundError("マニュアルファイルが見つかりませんでした")
            
    except Exception as e:
        st.error("マニュアルファイルが見つかりません。")
        st.info("管理者にお問い合わせください。")

if __name__ == "__main__":
    run()
else:
    # Streamlit Pages用の直接実行
    run()