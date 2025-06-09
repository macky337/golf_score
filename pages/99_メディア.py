"""
メディアファイル配信ページ
/media/ パスへのアクセスを処理し、適切なファイルを配信する
Railway環境でのPDF配信404エラー対応版
"""
import streamlit as st
import os
import time
from modules.media_utils import get_media_directory
from modules.url_handler import (
    extract_media_path_from_url, 
    is_facebook_crawler, 
    is_social_media_crawler,
    log_access_attempt,
    validate_filename
)

def serve_media_file():
    """メディアファイルを配信する"""
    # デバッグログ（開発時のみ）
    if os.getenv('ENVIRONMENT') == 'development':
        log_access_attempt()
    
    # 高度なURL処理でファイル名を抽出
    filename = extract_media_path_from_url()
    
    if not filename:
        st.error("ファイルが指定されていません")
        st.info("正しいURLフォーマット: /media/filename.pdf")
        
        # ソーシャルメディアクローラー向けの案内
        if is_social_media_crawler():
            st.info("SNS共有用のPDFファイルをお探しの場合は、結果確認ページから再度PDFを生成してください。")
        return
    
    # ファイル名の検証
    is_valid, validated_filename = validate_filename(filename)
    if not is_valid:
        st.error(validated_filename)  # エラーメッセージが返される
        return
    
    filename = validated_filename
    
    try:
        media_dir = get_media_directory()
        file_path = os.path.join(media_dir, filename)
        
        # ファイルの存在確認
        if not os.path.exists(file_path):
            st.error("ファイルが見つかりません")
            return
        
        # ファイルの年齢チェック（24時間以内）
        file_age = time.time() - os.path.getmtime(file_path)
        if file_age > 24 * 3600:  # 24時間
            st.error("ファイルの有効期限が切れています")
            return
        
        # ファイルを読み込んで配信
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # ファイルタイプの判定
        if filename.endswith('.pdf'):
            mime_type = 'application/pdf'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif filename.endswith('.png'):
            mime_type = 'image/png'
        else:
            mime_type = 'application/octet-stream'
        
        # ダウンロードボタンを表示
        st.download_button(
            label="ファイルをダウンロード",
            data=file_data,
            file_name=filename,
            mime=mime_type
        )
        
        # PDF の場合は埋め込み表示も提供
        if filename.endswith('.pdf'):
            st.write("### PDF プレビュー")
            # Base64でエンコードしてPDFを表示
            import base64
            base64_pdf = base64.b64encode(file_data).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"ファイルの処理中にエラーが発生しました: {str(e)}")

def run():
    """メディア配信ページのメイン関数"""
    st.set_page_config(
        page_title="メディアファイル - Golf Score App",
        page_icon="📁",
        layout="wide"
    )
    
    # デバッグ情報（開発時のみ）
    if os.getenv('ENVIRONMENT') == 'development':
        with st.expander("デバッグ情報"):
            st.write("Query Params:", dict(st.query_params))
            st.write("Environment Variables:")
            for key in ['REQUEST_URI', 'HTTP_USER_AGENT', 'PATH_INFO']:
                st.write(f"{key}: {os.getenv(key, 'None')}")
    
    st.title("📁 メディアファイル")
    serve_media_file()

if __name__ == "__main__":
    run()
