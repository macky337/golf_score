import os
import time
from typing import Callable, Optional, TypeVar
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# .env から環境変数をロード
load_dotenv()

# グローバルクライアント変数
_supabase_client: Optional[Client] = None
T = TypeVar("T")

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


def execute_read_with_retry(operation: Callable[[Client], T], attempts: int = 3) -> T:
    """再試行で一時的なSupabase接続断を吸収して読み取りを実行する。"""
    global _supabase_client

    last_error: Optional[Exception] = None
    for attempt in range(attempts):
        client = get_supabase_client()
        if client is None:
            raise RuntimeError("Supabaseクライアントが利用できません。")
        try:
            return operation(client)
        except (httpx.RequestError, OSError) as exc:
            last_error = exc
            # 上流で閉じられたHTTP/2接続を破棄し、次回は新しい接続を使う。
            _supabase_client = None
            if attempt < attempts - 1:
                time.sleep(0.5 * (attempt + 1))

    assert last_error is not None
    raise last_error

# スコア関連の操作
SCORE_UPDATE_FIELDS = (
    "front_score", "front_putt", "front_game_pt",
    "back_score", "back_putt", "back_game_pt",
    "extra_score", "extra_putt", "extra_game_pt", "total_score",
)


def _save_score_changes_atomic(client, round_id, changes_by_member, *, allow_finalized=False):
    """既存の全参加者行を含めて、スコア変更を1回のRPCで保存する。"""
    from modules.round_persistence import save_score_updates_atomic

    scores = client.table("score").select("*").eq("round_id", round_id).execute().data or []
    if not scores:
        raise ValueError("スコアデータを取得できません")

    participant_ids = {int(score["member_id"]) for score in scores}
    unknown_members = set(changes_by_member) - participant_ids
    if unknown_members:
        raise ValueError("このラウンドの参加者ではないメンバーが含まれています")

    records = []
    for score in scores:
        member_id = int(score["member_id"])
        record = {"member_id": member_id}
        record.update({field: score.get(field) or 0 for field in SCORE_UPDATE_FIELDS})
        record.update({
            field: value for field, value in changes_by_member.get(member_id, {}).items()
            if field in SCORE_UPDATE_FIELDS
        })
        if "front_score" in changes_by_member.get(member_id, {}) or "back_score" in changes_by_member.get(member_id, {}):
            record["total_score"] = record["front_score"] + record["back_score"]
        records.append(record)

    return save_score_updates_atomic(
        client, round_id, "all", records, allow_finalized=allow_finalized
    )


def save_score(round_id, member_id, score_data):
    """メンバー単位の変更も、参加者全員を含む原子的RPCで保存する。"""
    client = get_supabase_client()
    if client is None:
        return None
    return _save_score_changes_atomic(client, round_id, {int(member_id): score_data})

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
    """エラーハンドリングとリトライ機能を備えた原子的スコア更新。"""
    client = get_supabase_client()
    if client is None:
        return None
    
    for attempt in range(retry_count):
        try:
            result = _save_score_changes_atomic(
                client, round_id, {int(member_id): update_data}
            )
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
    """スコアバッチ更新を、参加者全員を含む1回のRPCで保存する。"""
    supabase = get_supabase_client()
    if supabase is None:
        return (False, 0, [{"error": "Supabase client not available"}])
    try:
        changes = {
            int(member_id): {key: value for key, value in data.items() if key in SCORE_UPDATE_FIELDS}
            for member_id, data in update_data.items()
        }
        _save_score_changes_atomic(supabase, round_id, changes)
        return (True, len(changes), [])
    except Exception as e:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("スコアの一括更新に失敗しました")
        return (False, 0, [{"error": str(e)}])


def upsert_scores_batch(round_id, records, segment):
    """参加者全員の指定スコア区分を単一RPCで保存する。"""
    client = get_supabase_client()
    if client is None:
        return (False, "Supabase client not available")
    try:
        from modules.round_persistence import save_score_updates_atomic
        result = save_score_updates_atomic(client, round_id, segment, records)
        return (True, result)
    except Exception as e:
        return (False, str(e))

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
        
        from modules.round_calculation import recalculate_round
        rounds = supabase.table('rounds').select('round_id').execute().data or []
        for round_data in rounds:
            recalculate_round(supabase, round_data['round_id'])
        
        return {
            'success': True,
            'updates_count': len(rounds),
            'total_results': len(rounds)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'updates_count': 0
        }
