import streamlit as st
import os
import sys
import traceback

def enter_debug_mode():
    """デバッグモードを有効化する"""
    st.session_state.debug_mode = True
    st.info("デバッグモードが有効になりました。隠しページにアクセスできます。")

def exit_debug_mode():
    """デバッグモードを無効化する"""
    st.session_state.debug_mode = False
    st.info("通常モードに戻りました。")

def is_debug_mode():
    """現在デバッグモードかどうかを確認する"""
    return st.session_state.get("debug_mode", False)

def handle_error(exception):
    """例外をキャプチャして表示する"""
    st.error(f"エラーが発生しました: {str(exception)}")
    
    # デバッグモードが有効な場合は詳細情報を表示
    if st.session_state.get("debug_mode", False):
        st.code(traceback.format_exc())
    else:
        st.info("詳細情報を表示するには、デバッグモードを有効にしてください。")

def toggle_debug_mode():
    """デバッグモードの切り替え"""
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
        
    st.session_state.debug_mode = not st.session_state.debug_mode
    
    if st.session_state.debug_mode:
        return "デバッグモードを無効化"
    else:
        return "デバッグモードを有効化"

def debug_info():
    """デバッグ情報を表示"""
    st.write("### デバッグ情報")
    st.write(f"Python バージョン: {sys.version}")
    st.write(f"Streamlit バージョン: {st.__version__}")
    
    # 環境変数（機密情報除く）
    safe_env = {k: v for k, v in os.environ.items() 
                if not any(secret in k.lower() for secret in 
                           ["key", "secret", "password", "token", "pwd"])}
    
    with st.expander("環境変数"):
        st.json(safe_env)
    
    # セッション状態
    with st.expander("セッション状態"):
        # 機密情報を除外
        safe_session = {k: v for k, v in st.session_state.items()
                        if not any(secret in k.lower() for secret in 
                                   ["key", "secret", "password", "token", "pwd"])}
        st.write(safe_session)
    
    # エラー履歴
    if "errors" in st.session_state and st.session_state.errors:
        with st.expander("エラー履歴"):
            for i, err in enumerate(st.session_state.errors):
                st.text(f"{i+1}. {err}")
