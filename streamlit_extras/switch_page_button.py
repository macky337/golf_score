import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    # クエリパラメータを設定 (内部APIまたは experimental fallback)
    if hasattr(st, '_set_query_params'):
        st._set_query_params(page=page_name)
    else:
        st.experimental_set_query_params(page=page_name)
    # パラメータ設定後にスクリプト停止
    st.stop()
