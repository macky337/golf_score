import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    try:
        # 公式APIがあればそれを使う
        if hasattr(st, "switch_page"):
            st.switch_page(page_name)
        else:
            st.experimental_set_query_params(page=page_name)
            st.experimental_rerun()
    except Exception as e:
        st.error(f"switch_page例外: {e}")
        raise
