import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    # ページ名をクエリパラメータに設定（APIの違いに対応）
    if hasattr(st, "set_query_params"):
        st.set_query_params(page=page_name)
    else:
        st.experimental_set_query_params(page=page_name)
    # ページ切替後に再実行
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.stop()
