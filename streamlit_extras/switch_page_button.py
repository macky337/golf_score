import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    # ページ名をクエリパラメータに設定して再実行
    st.experimental_set_query_params(page=page_name)
    st.experimental_rerun()
