"""
URL処理とルーティングユーティリティ
Railway環境でのメディアファイルアクセス処理
"""
import os
import urllib.parse
import streamlit as st

def extract_media_path_from_url():
    """
    様々な方法でURL中のメディアパスを抽出する
    Returns: ファイル名またはNone
    """
    # 方法1: Streamlitのクエリパラメータ
    query_params = st.query_params
    filename = query_params.get("file", None) or query_params.get("media_file", None)
    
    if filename:
        return urllib.parse.unquote(filename)
    
    # 方法2: 環境変数からパス情報を取得
    for env_var in ['REQUEST_URI', 'PATH_INFO', 'SCRIPT_NAME']:
        path = os.getenv(env_var, '')
        if '/media/' in path:
            # /media/ 以降の部分を抽出
            media_part = path.split('/media/')[-1]
            # クエリパラメータを除去
            if '?' in media_part:
                media_part = media_part.split('?')[0]
            if media_part:
                return urllib.parse.unquote(media_part)
      # 方法3: リクエストヘッダーから推測（試験的）
    try:
        # 一部のWebサーバー環境でヘッダー情報が利用できる場合
        if hasattr(st, 'session_state') and hasattr(st.session_state, '_media_filename'):
            return st.session_state._media_filename
    except:
        pass
    
    return None

def is_facebook_crawler():
    """
    Facebook外部クローラーかどうかを判定
    """
    user_agent = os.getenv('HTTP_USER_AGENT', '').lower()
    facebook_agents = [
        'facebookexternalhit',
        'facebookcatalog',
        'facebot',
        'facebook'
    ]
    return any(agent in user_agent for agent in facebook_agents)

def is_social_media_crawler():
    """
    ソーシャルメディアクローラーかどうかを判定
    """
    user_agent = os.getenv('HTTP_USER_AGENT', '').lower()
    social_agents = [
        'facebookexternalhit',
        'twitterbot',
        'linkedinbot',
        'whatsapp',
        'telegrambot',
        'discordbot',
        'slackbot'
    ]
    return any(agent in user_agent for agent in social_agents)

def log_access_attempt():
    """
    アクセス試行をログに記録（デバッグ用）
    """
    if os.getenv('ENVIRONMENT') == 'development':
        st.write("### デバッグ: URL処理情報")
        st.write(f"**User-Agent**: {os.getenv('HTTP_USER_AGENT', 'None')}")
        st.write(f"**Request URI**: {os.getenv('REQUEST_URI', 'None')}")
        st.write(f"**Path Info**: {os.getenv('PATH_INFO', 'None')}")
        st.write(f"**Script Name**: {os.getenv('SCRIPT_NAME', 'None')}")
        st.write(f"**Query Params**: {dict(st.query_params)}")
        st.write(f"**Is Facebook Crawler**: {is_facebook_crawler()}")

def create_media_url(filename):
    """
    メディアファイルの公開URLを生成
    """
    base_url = os.getenv('RAILWAY_STATIC_URL', 'https://golfscore-production.up.railway.app')
    return f"{base_url}/media/{filename}"

def validate_filename(filename):
    """
    ファイル名のセキュリティ検証
    """
    if not filename:
        return False, "ファイル名が指定されていません"
    
    # URL デコード
    filename = urllib.parse.unquote(filename)
    
    # セキュリティチェック
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "不正なファイル名です"
    
    # 許可された拡張子のチェック
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        return False, "許可されていないファイル形式です"
    
    return True, filename
