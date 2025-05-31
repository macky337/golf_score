import streamlit as st

def switch_page(page_name: str):
    """Streamlit標準のマルチページ切り替えを行う"""
    try:
        # 公式APIがあればそれを使う
        if hasattr(st, "switch_page"):
            # ページ名をStreamlitが期待する形式に変換
            if page_name == "main":
                # メインページの場合
                st.switch_page("main.py")
            elif not page_name.startswith("pages/") and not page_name.endswith(".py"):
                # pages/プレフィックスと.py拡張子を追加
                st.switch_page(f"pages/{page_name}.py")
            else:
                # すでに正しい形式の場合
                st.switch_page(page_name)
        else:
            # ページ名から拡張子やパスを除去してページ名だけにする
            page_param = page_name
            if page_param.startswith("pages/"):
                page_param = page_param.replace("pages/", "")
            if page_param.endswith(".py"):
                page_param = page_param[:-3]
            st.experimental_set_query_params(page=page_param)
            st.experimental_rerun()
    except Exception as e:
        st.error(f"switch_page例外: {e}")
        raise
