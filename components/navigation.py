import streamlit as st
from streamlit_extras.switch_page_button import switch_page

def show_navigation(active_page=""):
    """共通ナビゲーションバーを表示する"""
    # 余分なマージンを削減
    st.markdown("""
        <style>
        div.block-container {padding-top: 1rem;}
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    # ホームボタン - appではなくMainを使用
    with col1:
        if st.button("🏠 Home", key="nav_home"):
            switch_page("Main")  # "app" から "Main" に変更
    
    # アクティブなラウンドがある場合のみスコア入力関連のナビゲーションを表示
    if "active_round_id" in st.session_state and st.session_state.active_round_id:
        round_id = st.session_state.active_round_id
        
        # フロントスコア入力ボタン
        with col2:
            if st.button("🏌️ フロント", key="nav_front"):
                switch_page("フロントスコア入力")
        
        # バックスコア入力ボタン
        with col3:
            if st.button("🏌️ バック", key="nav_back"):
                switch_page("バックスコア入力")
        
        # エキストラスコア入力ボタン（ラウンドがエキストラホールを持つ場合のみ表示）
        if "has_extra" in st.session_state and st.session_state.has_extra:
            with col4:
                if st.button("🏌️ エキストラ", key="nav_extra"):
                    # スペースを削除して正確なページ名を指定
                    switch_page("エキストラスコア入力")  # 先頭スペースを削除
        
        # 結果確認ボタン
        with col5:
            if st.button("📊 結果確認", key="nav_results"):
                switch_page("結果確認")
    
    # ラウンド設定画面へのボタン
    with col6:
        if st.button("⚙️ ラウンド設定", key="nav_round_settings"):
            switch_page("ラウンド設定")
    
    # 現在のページを示す
    if active_page:
        st.markdown(f"### {active_page}")
    
    # アクティブなラウンド情報を表示
    if "active_round_id" in st.session_state and st.session_state.active_round_id:
        round_id = st.session_state.active_round_id
        st.info(f"アクティブなラウンド ID: {round_id}")
