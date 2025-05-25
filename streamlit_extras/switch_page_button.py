import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    # ページ名をクエリパラメータに設定して終了（次回読み込みで反映）
    st.set_query_params(page=page_name)
    st.stop()
