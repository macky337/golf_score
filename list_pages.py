import os
import streamlit as st

def list_available_pages():
    """利用可能なすべてのページを表示する"""
    # Streamlitのページ情報にアクセスする
    try:
        from streamlit.runtime.state import get_session_info
        session_info = get_session_info()
        all_pages = session_info.all_pages
        
        print("利用可能なページ一覧:")
        for page in all_pages:
            print(f" - {page}")
            
    except Exception as e:
        print(f"Streamlitのページ情報にアクセスできませんでした: {e}")
        
        # 代替方法: ディレクトリを直接検索
        pages_dir = "pages"
        if os.path.exists(pages_dir):
            print("\nページディレクトリの内容:")
            files = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
            for f in sorted(files):
                page_name = f.split('_', 1)[1].rsplit('.', 1)[0] if '_' in f else f.rsplit('.', 1)[0]
                print(f" - {page_name}")
        else:
            print("pages ディレクトリが見つかりません。")

if __name__ == "__main__":
    list_available_pages()
