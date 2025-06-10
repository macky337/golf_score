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
    # 方法1: セッションステートからの取得（最優先）
    try:
        if hasattr(st, 'session_state'):
            # 直接_media_filenameから取得
            if hasattr(st.session_state, '_media_filename'):
                filename = st.session_state._media_filename
                if filename:
                    return urllib.parse.unquote(filename)
            
            # セッションステート内のURL情報をスキャン
            for key, value in st.session_state.items():
                if isinstance(value, str) and '/media/' in value and any(ext in value for ext in ['.pdf', '.jpg', '.jpeg', '.png']):
                    # URLからファイル名を抽出
                    url_parts = value.split('/media/')
                    if len(url_parts) > 1:
                        potential_filename = url_parts[-1]
                        # クエリパラメータを除去
                        if '?' in potential_filename:
                            potential_filename = potential_filename.split('?')[0]
                        if potential_filename:
                            return urllib.parse.unquote(potential_filename)
    except Exception as e:
        pass
    
    # 方法2: Streamlitの新しいクエリパラメータAPI
    try:
        if hasattr(st, 'query_params'):
            # 複数の取得方法を試行
            query_params = None
            
            # 方法2a: 直接辞書変換
            try:
                query_params = dict(st.query_params)
            except:
                pass
            
            # 方法2b: .to_dict()メソッド使用
            if not query_params:
                try:
                    if hasattr(st.query_params, 'to_dict'):
                        query_params = st.query_params.to_dict()
                except:
                    pass
            
            # 方法2c: 個別アクセス
            if not query_params:
                try:
                    query_params = {}
                    for key in ['file', 'media_file', 'filename', 'f']:
                        try:
                            value = st.query_params.get(key)
                            if value:
                                query_params[key] = value
                        except:
                            continue
                except:
                    pass
            
            # クエリパラメータが取得できた場合の処理
            if query_params:
                # ファイル名の取得を試行（複数のキー名で）
                for key in ['file', 'media_file', 'filename', 'f']:
                    if key in query_params:
                        filename = query_params[key]
                        if filename:
                            return urllib.parse.unquote(filename)
                
                # URLパスそのものをチェック（拡張子付きのキー）
                for key, value in query_params.items():
                    if key.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                        return urllib.parse.unquote(key)
                    if value and str(value).endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                        return urllib.parse.unquote(str(value))
                        
    except Exception as e:
        # エラーをログに記録（開発時のみ）
        if os.getenv('ENVIRONMENT') == 'development':
            print(f"Query params extraction error (new API): {e}")
    
    # 方法3: 古いStreamlit APIでの取得を試行
    try:
        if hasattr(st, 'experimental_get_query_params'):
            query_params = st.experimental_get_query_params()
            
            # ファイル名の取得を試行
            for key in ['file', 'media_file', 'filename', 'f']:
                if key in query_params and query_params[key]:
                    filename = query_params[key][0]  # リスト形式なので最初の要素
                    if filename:
                        return urllib.parse.unquote(filename)
                        
    except Exception as e:
        if os.getenv('ENVIRONMENT') == 'development':
            print(f"Query params extraction error (old API): {e}")
    
    # 方法4: URL直接解析（ブラウザのURL取得を試行）
    try:
        # JavaScriptを使用してブラウザのURLを取得（実験的）
        import streamlit.components.v1 as components
        
        # カスタムコンポーネントでURL情報を取得
        url_params = components.html("""
        <script>
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        parent.postMessage({type: 'streamlit:setComponentValue', value: params}, '*');
        </script>
        """, height=0, width=0)
        
        if url_params:
            for key in ['file', 'media_file', 'filename', 'f']:
                if key in url_params:
                    filename = url_params[key]
                    if filename:
                        return urllib.parse.unquote(filename)
    except Exception as e:
        pass
    
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
        
        # クエリパラメータの詳細表示
        try:
            if hasattr(st, 'query_params'):
                query_params = st.query_params
                st.write(f"**Query Params (新API)**: {dict(query_params)}")
                for key, value in query_params.items():
                    st.write(f"  - {key}: {value}")
        except Exception as e:
            st.write(f"**Query Params取得エラー**: {e}")
        
        # 旧APIでの取得も試行
        try:
            if hasattr(st, 'experimental_get_query_params'):
                old_params = st.experimental_get_query_params()
                st.write(f"**Query Params (旧API)**: {old_params}")
        except Exception as e:
            st.write(f"**旧Query Params取得エラー**: {e}")
            
        # セッションステートの確認
        try:
            if hasattr(st, 'session_state') and hasattr(st.session_state, '_media_filename'):
                st.write(f"**Session State Media**: {st.session_state._media_filename}")
            else:
                st.write("**Session State Media**: None")
        except Exception as e:
            st.write(f"**Session State エラー**: {e}")
            
        st.write(f"**Is Facebook Crawler**: {is_facebook_crawler()}")
        st.write(f"**Is Social Media Crawler**: {is_social_media_crawler()}")
        
        # URL抽出の結果をリアルタイムで表示
        extracted_filename = extract_media_path_from_url()
        st.write(f"**抽出されたファイル名**: {extracted_filename}")

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
