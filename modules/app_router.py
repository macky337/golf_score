"""
Railway環境での直接URL処理
Streamlitの標準機能を拡張してメディアファイル配信を実現
"""
import streamlit as st
import os
import sys
from pathlib import Path

def setup_media_routing():
    """
    メディアルーティングのセットアップ
    Railway環境での /media/ パス処理を設定
    """
    # 環境変数からURL情報を取得
    request_uri = os.getenv('REQUEST_URI', '')
    path_info = os.getenv('PATH_INFO', '')
    script_name = os.getenv('SCRIPT_NAME', '')
    
    # /media/ パスアクセスの検出
    urls_to_check = [request_uri, path_info, script_name]
    media_access_detected = any('/media/' in url for url in urls_to_check if url)
    
    if media_access_detected:
        # セッション状態にメディアアクセスフラグを設定
        st.session_state['_media_access'] = True
        
        # URL から実際のファイル名を抽出
        for url in urls_to_check:
            if '/media/' in url:
                media_part = url.split('/media/')[-1]
                # クエリパラメータを除去
                if '?' in media_part:
                    media_part = media_part.split('?')[0]
                if media_part:
                    st.session_state['_media_filename'] = media_part
                    break
    
    return media_access_detected

def is_media_request():
    """
    現在のリクエストがメディアファイルアクセスかどうかを判定
    """
    return st.session_state.get('_media_access', False)

def get_requested_media_file():
    """
    リクエストされたメディアファイル名を取得
    """
    return st.session_state.get('_media_filename', None)

def handle_direct_media_access():
    """
    直接的なメディアアクセスの処理
    Railway環境でのURL処理最適化版
    """
    if setup_media_routing():
        # メディアアクセスが検出された場合の処理
        filename = get_requested_media_file()
        if filename:
            # ページを切り替えずに直接ファイルを配信
            try:
                from modules.media_utils import get_media_directory
                from modules.url_handler import validate_filename
                import time
                
                # ファイル名の検証
                is_valid, validated_filename = validate_filename(filename)
                if not is_valid:
                    st.error(validated_filename)
                    return
                
                media_dir = get_media_directory()
                file_path = os.path.join(media_dir, validated_filename)
                
                # ファイルの存在と有効期限確認
                if not os.path.exists(file_path):
                    st.error("ファイルが見つかりません")
                    return
                
                file_age = time.time() - os.path.getmtime(file_path)
                if file_age > 24 * 3600:  # 24時間
                    st.error("ファイルの有効期限が切れています")
                    return
                
                # ファイルを直接配信
                with open(file_path, "rb") as f:
                    file_data = f.read()
                
                # Streamlitのダウンロード機能を使用
                st.download_button(
                    label=f"📥 {validated_filename} をダウンロード",
                    data=file_data,
                    file_name=validated_filename,
                    mime='application/pdf' if validated_filename.endswith('.pdf') else 'application/octet-stream'
                )
                
                # PDFの場合は埋め込み表示
                if validated_filename.endswith('.pdf'):
                    import base64
                    base64_pdf = base64.b64encode(file_data).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                
                return True
                
            except Exception as e:
                st.error(f"ファイル配信エラー: {str(e)}")
                return True  # エラーでも処理は完了とする
    
    return False

def init_app_with_media_support():
    """
    メディアサポート付きでアプリを初期化
    """
    # 直接的なメディアアクセスを最初にチェック
    if handle_direct_media_access():
        return True  # メディアファイルが処理された場合は他の処理をスキップ
    
    return False  # 通常のアプリ処理を続行
