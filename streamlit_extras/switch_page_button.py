import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    # ページ名をクエリパラメータに設定（APIの違いに対応）
    if hasattr(st, "set_query_params"):
        st.set_query_params(page=page_name)
    else:
        st.experimental_set_query_params(page=page_name)
    # 処理を停止してページ切替を反映
    st.stop()
