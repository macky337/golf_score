import os
import time
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# .env から環境変数をロード
load_dotenv()

# グローバルクライアント変数
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Supabaseクライアントを取得する"""
    global _supabase_client
    
    # 既にクライアントが初期化されている場合はそれを返す
    if _supabase_client is not None:
        return _supabase_client
    
    # 認証情報の取得 (環境変数 → Streamlit secrets)
    supabase_url = os.getenv("SUPABASE_URL") or None
    supabase_key = os.getenv("SUPABASE_KEY") or None
    
    if not supabase_url or not supabase_key:
        try:
            supabase_url = st.secrets["supabase"]["url"]
            supabase_key = st.secrets["supabase"]["key"]
        except Exception:
            try:
                supabase_url = st.secrets.get("SUPABASE_URL")
                supabase_key = st.secrets.get("SUPABASE_KEY")
            except Exception:
                pass
    
    if not supabase_url or not supabase_key:
        return None
    
    # クライアントを初期化
    try:
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as e:
        return None

# スコア関連の操作
def save_score(round_id, member_id, score_data):
    """メンバー単位のスコアデータを保存する。"""
    client = get_supabase_client()
    if client is None:
        return None

    # 既存のスコアを確認
    existing = client.table("score").select("*").eq("round_id", round_id) \
                    .eq("member_id", member_id).execute()

    if len(existing.data) > 0:
        # 更新
        return client.table("score").update(score_data) \
                    .eq("round_id", round_id) \
                    .eq("member_id", member_id).execute()
    else:
        # 新規作成
        insert_data = dict(score_data)
        insert_data.update({
            "round_id": round_id,
            "member_id": member_id,
        })
        return client.table("score").insert(insert_data).execute()

def get_player_scores(round_id, member_id):
    """メンバーのスコアを取得する。"""
    client = get_supabase_client()
    if client is None:
        return None
    return client.table("score").select("*") \
                .eq("round_id", round_id) \
                .eq("member_id", member_id).execute()

# 新規追加: エラーハンドリング付きのデータ保存・取得関数
def safe_update_score(round_id, member_id, update_data, retry_count=3):
    """エラーハンドリングとリトライ機能を備えたスコア更新"""
    client = get_supabase_client()
    if client is None:
        return None
    
    for attempt in range(retry_count):
        try:
            result = client.table("score").update(update_data) \
                    .eq("round_id", round_id) \
                    .eq("member_id", member_id).execute()
            # 成功したら結果を返す
            return result
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(1)  # 1秒待機してリトライ
                st.toast(f"スコア更新を再試行中... ({attempt + 1}/{retry_count})")
            else:
                # 最後の試行でも失敗した場合はエラーを記録
                st.error(f"データ更新エラー: {str(e)}")
                # セッションに失敗したデータを保存（後で再試行のため）
                if "failed_updates" not in st.session_state:
                    st.session_state.failed_updates = []
                st.session_state.failed_updates.append({
                    "round_id": round_id,
                    "member_id": member_id,
                    "update_data": update_data
                })
                raise e

def cache_scores_in_session(round_id):
    """計算済みスコアをセッションに保存"""
    client = get_supabase_client()
    if client is None:
        return []
    try:
        result = client.table("score").select("*").eq("round_id", round_id).execute()
        if result.data:
            # スコアデータをセッションに保存
            if "cached_scores" not in st.session_state:
                st.session_state.cached_scores = {}
            st.session_state.cached_scores[round_id] = result.data
            return result.data
    except Exception as e:
        st.warning(f"スコアデータのキャッシュ中にエラーが発生しました: {str(e)}")
    return []

def get_scores_with_fallback(round_id):
    """DBからスコア取得、失敗時はキャッシュから取得"""
    try:
        client = get_supabase_client()
        if client is None:
            return []
        # member情報を結合して取得するよう修正
        result = client.table("score").select("*, member:member_id(name)").eq("round_id", round_id).execute()
        
        # 結果がある場合
        if result.data:
            # memberデータをフラット化して扱いやすくする
            for score in result.data:
                if 'member' in score and score['member']:
                    # スコアデータに直接nameフィールドを追加
                    score['name'] = score['member']['name']
            
            # 成功した場合はキャッシュも更新
            if "cached_scores" not in st.session_state:
                st.session_state.cached_scores = {}
            st.session_state.cached_scores[round_id] = result.data
            return result.data
    except Exception as e:
        st.warning(f"データベース接続エラー: {str(e)}. キャッシュを使用します。")
    
    # キャッシュからデータを取得
    if "cached_scores" in st.session_state and round_id in st.session_state.cached_scores:
        st.info("キャッシュからスコアデータを読み込みました。")
        return st.session_state.cached_scores[round_id]
    
    return []

def update_scores_batch(round_id, update_data):
    """スコアバッチ更新 - 複数メンバーのスコアを一度に更新"""
    supabase = get_supabase_client()
    success_count = 0
    failed_updates = []
    
    # 許可されるフィールド (score テーブルに存在するフィールドのみ)
    allowed_fields = [
        'front_score', 'back_score', 'extra_score',
        'front_putt', 'back_putt', 'extra_putt', 
        'front_game_pt', 'back_game_pt', 'extra_game_pt',
        'total_score'
    ]
    
    try:
        for member_id, data in update_data.items():
            # 不正なフィールドをフィルタリング
            filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            try:
                if supabase is None:
                    continue
                result = supabase.table('score').update(filtered_data).eq('round_id', round_id).eq('member_id', member_id).execute()
                success_count += 1
            except Exception as e:
                failed_updates.append({
                    'member_id': member_id,
                    'data': filtered_data,
                    'error': str(e)
                })
        
        return (len(failed_updates) == 0, success_count, failed_updates)
    except Exception as e:
        print(f"バッチ更新エラー: {e}")
        return (False, success_count, failed_updates + [{'error': str(e)}])


def upsert_scores_batch(round_id, records):
    """
    一括でスコアを更新する。records は各要素が
    {'member_id': ..., 'front_score': ..., ...} のような辞書のリストとする。
    既存のスコアレコードを更新するため、upsertではなくupdateを使用。
    戻り値: (success: bool, result_or_error)
    """
    client = get_supabase_client()
    if client is None:
        return (False, "Supabase client not available")

    # 個別に更新を実行（バッチ更新）
    failures = []
    success_count = 0
    
    try:
        for r in records:
            member_id = r.get('member_id')
            if not member_id:
                failures.append({'error': 'member_id is required', 'record': r})
                continue
            
            # 更新データを作成（round_idとmember_idは除外）
            update_data = dict(r)
            update_data.pop('member_id', None)
            update_data.pop('round_id', None)
            
            try:
                # 既存レコードを更新
                res = client.table('score').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
                
                if res.data:
                    success_count += 1
                else:
                    failures.append({'member_id': member_id, 'error': 'No data returned from update'})
                    
            except Exception as e2:
                failures.append({'member_id': member_id, 'error': str(e2)})
        
        if failures:
            return (False, {'error': f'{len(failures)} updates failed', 'failures': failures, 'success_count': success_count})
        else:
            return (True, {'success_count': success_count})
            
    except Exception as e:
        return (False, {'error': str(e), 'failures': failures})

def update_score_total_pts():
    """
    すべての確定済みスコアのtotal_pt値を再計算して更新する
    DBのround_resultsテーブルを更新
    """
    try:
        supabase = get_supabase_client()
        if supabase is None:
            return {
                'success': False,
                'error': 'Supabase client is not available'
            }
        
        # 確定済みのラウンドに紐づくround_resultsを全て取得
        results_query = supabase.table('round_results').select(
            'id, round_id, member_id, match_pt, putt_pt, total_game_pt, total_pt'
        ).execute()
        
        results = results_query.data
        updates_count = 0
        
        for result in results:
            # Noneの場合は0として扱う
            total_game_pt = result.get('total_game_pt', 0) or 0
            match_pt = result.get('match_pt', 0) or 0
            putt_pt = result.get('putt_pt', 0) or 0
            
            # 再計算したtotal_pt
            calculated_total = total_game_pt + match_pt + putt_pt
            
            # 現在のtotal_ptと再計算した値を比較し、異なる場合のみ更新
            if abs(calculated_total - (result.get('total_pt', 0) or 0)) > 0.01:
                supabase.table('round_results').update({
                    'total_pt': calculated_total
                }).eq('id', result['id']).execute()
                updates_count += 1
        
        return {
            'success': True,
            'updates_count': updates_count,
            'total_results': len(results)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'updates_count': 0
        }
