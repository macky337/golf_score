import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# .env から環境変数をロード
load_dotenv()

def get_supabase_client() -> Client:
    """Supabaseクライアントを取得する（エラーハンドリング強化版）"""
    
    # セッションステートから既存のクライアントを取得
    try:
        if hasattr(st, 'session_state') and "supabase" in st.session_state:
            return st.session_state.supabase
    except:
        pass
    
    # 環境変数から認証情報を取得
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    # デバッグ情報
    print(f"DEBUG: URL: {supabase_url[:30] if supabase_url else 'None'}...")
    print(f"DEBUG: KEY: {'設定済み' if supabase_key else 'None'}")
    
    # Streamlit secrets からの取得を試行
    if not supabase_url or not supabase_key:
        try:
            if hasattr(st, 'secrets'):
                supabase_url = st.secrets["supabase"]["url"]
                supabase_key = st.secrets["supabase"]["key"]
                print("DEBUG: Streamlit secretsから取得")
        except:
            pass
    
    # 認証情報の確認
    if not supabase_url or not supabase_key:
        error_msg = "Supabase認証情報が設定されていません"
        print(f"ERROR: {error_msg}")
        try:
            if hasattr(st, 'error'):
                st.error(f"❌ {error_msg}")
        except:
            pass
        return None
    
    # クライアント初期化
    try:
        print("DEBUG: Supabaseクライアント初期化中...")
        client = create_client(supabase_url, supabase_key)
        print("DEBUG: 初期化成功")
        
        # セッションステートに保存
        try:
            if hasattr(st, 'session_state'):
                st.session_state.supabase = client
                print("DEBUG: セッション保存完了")
        except:
            pass
        
        return client
        
    except FileNotFoundError as e:
        error_msg = f"ファイルエラー: {str(e)} - ネットワーク接続を確認してください"
        print(f"ERROR: {error_msg}")
        try:
            if hasattr(st, 'error'):
                st.error(f"❌ {error_msg}")
                st.info("解決方法:\n• インターネット接続を確認\n• pip install --upgrade supabase")
        except:
            pass
        return None
        
    except Exception as e:
        error_msg = f"初期化エラー: {str(e)}"
        print(f"ERROR: {error_msg}")
        try:
            if hasattr(st, 'error'):
                st.error(f"❌ {error_msg}")
        except:
            pass
        return None

# 基本的なスコア操作関数
def save_score(round_id, player_id, hole_number, score_data):
    """スコアデータを保存する"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        # 既存のスコアを確認
        existing = client.table("score").select("*").eq("round_id", round_id).eq("player_id", player_id).eq("hole_number", hole_number).execute()
        
        if len(existing.data) > 0:
            # 更新
            return client.table("score").update(score_data).eq("round_id", round_id).eq("player_id", player_id).eq("hole_number", hole_number).execute()
        else:
            # 新規作成
            score_data.update({
                "round_id": round_id,
                "player_id": player_id,
                "hole_number": hole_number,
            })
            return client.table("score").insert(score_data).execute()
    except Exception as e:
        print(f"ERROR: スコア保存エラー: {e}")
        return None

def get_player_scores(round_id, player_id):
    """プレイヤーの全スコアを取得する"""
    client = get_supabase_client()
    if not client:
        return None
    
    try:
        return client.table("score").select("*").eq("round_id", round_id).eq("player_id", player_id).order("hole_number").execute()
    except Exception as e:
        print(f"ERROR: スコア取得エラー: {e}")
        return None
