import streamlit as st

def switch_page(page_name):
    """ページ遷移を行う関数"""
    try:
        # Streamlit の新しい st.switch_page を使用
        if page_name == "main":
            st.switch_page("main.py")
        elif page_name.endswith(".py"):
            st.switch_page(page_name)
        else:
            # ページ名からファイルパスを生成
            if "/" in page_name:
                st.switch_page(page_name)
            else:
                st.switch_page(f"pages/{page_name}.py")
    except AttributeError:
        # st.switch_page が利用できない場合のフォールバック
        st.error(f"ページ '{page_name}' への遷移に失敗しました。")
        st.info("サイドバーからページを選択してください。")
    except Exception as e:
        st.error(f"ページ遷移エラー: {e}")
