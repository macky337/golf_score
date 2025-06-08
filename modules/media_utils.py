"""
メディアファイル管理ユーティリティ
PDFファイルやその他のメディアファイルの生成・管理を行う
"""
import os
import tempfile
import time
from typing import BinaryIO, Optional
import streamlit as st

def get_media_directory() -> str:
    """メディアファイル用ディレクトリのパスを取得"""
    # 本番環境では一時ディレクトリを使用
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'):
        return tempfile.gettempdir()
    
    # 開発環境では./mediaディレクトリを使用
    media_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media')
    os.makedirs(media_dir, exist_ok=True)
    return media_dir

def create_secure_filename(original_filename: str) -> str:
    """安全なファイル名を生成"""
    import re
    import secrets
    
    # ファイル名をサニタイズ
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_filename)
    
    # タイムスタンプとランダム文字列を追加
    timestamp = str(int(time.time()))
    random_suffix = secrets.token_hex(4)
    
    name, ext = os.path.splitext(safe_filename)
    return f"{name}_{timestamp}_{random_suffix}{ext}"

def save_temporary_file(file_data: bytes, filename: str, mime_type: str = "application/octet-stream") -> Optional[str]:
    """一時ファイルを保存し、ファイルパスを返す（将来的な拡張用）"""
    try:
        media_dir = get_media_directory()
        safe_filename = create_secure_filename(filename)
        file_path = os.path.join(media_dir, safe_filename)
        
        # バイナリデータを直接書き込み
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # 現在はローカルパスを返す（クリーンアップ用）
        return file_path
            
    except Exception as e:
        st.error(f"ファイル保存エラー: {e}")
        return None

def create_shareable_link(filename: str, file_data: bytes) -> str:
    """共有可能なリンクを生成（将来的にクラウドストレージ対応）"""
    # TODO: 将来的にS3、GCS、Cloudinaryなどのクラウドストレージに対応
    # 現在は情報メッセージのみ返す
    return f"📎 {filename} (ファイルが生成されました)"

def get_file_download_url(file_path: str) -> Optional[str]:
    """ファイルのダウンロードURLを生成（将来的にクラウドストレージ対応）"""
    # 現在は None を返してダウンロードボタンのみを使用
    return None

def cleanup_old_files(max_age_hours: int = 24):
    """古いファイルを削除（バックグラウンドクリーンアップ）"""
    try:
        media_dir = get_media_directory()
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(media_dir):
            if filename.startswith('.'):
                continue
                
            file_path = os.path.join(media_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass  # ファイル削除に失敗しても続行
    except Exception:
        pass  # クリーンアップに失敗しても続行

def get_public_url(file_path: str) -> Optional[str]:
    """ファイルのパブリックURLを生成（本番環境用）"""
    # この関数は必要に応じてクラウドストレージのURLを返すように拡張可能
    return None

def create_download_response(file_data: BinaryIO, filename: str, mime_type: str):
    """ダウンロード用のレスポンスを作成"""
    # Streamlitのダウンロードボタンを使用する場合
    return st.download_button(
        label=f"📥 {filename}をダウンロード",
        data=file_data,
        file_name=filename,
        mime=mime_type,
        use_container_width=True
    )
