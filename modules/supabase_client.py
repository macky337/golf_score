import os
import time
from supabase import create_client, Client
import streamlit as st

def get_supabase_client() -> Client:
    """Supabaseクライアントを取得する"""
    # Streamlitのセッションステートからクライアントを取得（既に初期化済みの場合）
    if "supabase" in st.session_state:
        return st.session_state.supabase
    
    # 環境変数またはstreamlit secretsから認証情報を取得
    if 'SUPABASE_URL' in os.environ and 'SUPABASE_KEY' in os.environ:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
    else:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
    
    # クライアントを初期化
    client = create_client(supabase_url, supabase_key)
    
    # セッションステートに保存
    st.session_state.supabase = client
    return client

# スコア関連の操作
def save_score(round_id, player_id, hole_number, score_data):
    """スコアデータを保存する"""
    client = get_supabase_client()
    
    # 既存のスコアを確認
    existing = client.table("score").select("*").eq("round_id", round_id) \
                    .eq("player_id", player_id) \
                    .eq("hole_number", hole_number).execute()
    
    if len(existing.data) > 0:
        # 更新
        return client.table("score").update(score_data) \
                    .eq("round_id", round_id) \
                    .eq("player_id", player_id) \
                    .eq("hole_number", hole_number).execute()
    else:
        # 新規作成
        score_data.update({
            "round_id": round_id,
            "player_id": player_id,
            "hole_number": hole_number,
        })
        return client.table("score").insert(score_data).execute()

def get_player_scores(round_id, player_id):
    """プレイヤーの全スコアを取得する"""
    client = get_supabase_client()
    return client.table("score").select("*") \
                .eq("round_id", round_id) \
                .eq("player_id", player_id) \
                .order("hole_number").execute()

# 新規追加: エラーハンドリング付きのデータ保存・取得関数
def safe_update_score(round_id, member_id, update_data, retry_count=3):
    """エラーハンドリングとリトライ機能を備えたスコア更新"""
    client = get_supabase_client()
    
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

def recalculate_all_past_rounds():
    """
    過去のすべてのラウンドデータを最新のロジックで再計算して更新する
    進捗状況と結果をユーザーに表示
    """
    client = get_supabase_client()
    
    try:
        # すべての確定済みラウンドを取得
        all_rounds_result = client.table('rounds').select('*').eq('finalized', True).order('date_played').execute()
        all_rounds = all_rounds_result.data
        
        if not all_rounds:
            st.warning("更新対象のラウンドが見つかりません。")
            return False
            
        # 処理状態の追跡
        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total": len(all_rounds)
        }
        
        # プログレスバーを表示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 各ラウンドを処理
        for i, round_data in enumerate(all_rounds):
            round_id = round_data['round_id']
            progress_percent = (i / stats["total"])
            progress_bar.progress(progress_percent)
            status_text.text(f"ラウンド {i+1}/{stats['total']} を処理中... (ID: {round_id}, {round_data['date_played']} {round_data['course_name']})")
            
            try:
                # スコアデータを取得
                scores = get_scores_with_fallback(round_id)
                if not scores or len(scores) < 2:
                    status_text.text(f"ラウンド ID {round_id}: スコアデータが不足しています (スキップ)")
                    stats["skipped"] += 1
                    continue
                    
                # ハンディキャップデータを取得
                handicaps_result = client.table('handicap_match').select('*').eq('round_id', round_id).execute()
                if not handicaps_result.data:
                    status_text.text(f"ラウンド ID {round_id}: ハンディキャップデータがありません (スキップ)")
                    stats["skipped"] += 1
                    continue
                    
                # バッチ処理で06_結果確認.pyと同じロジックで計算
                from pages.handicap_calc_logic import process_round_scores
                updated_scores = process_round_scores(scores, handicaps_result.data, round_data)
                
                # 計算されたスコアを一括で保存
                update_data = {}
                for score in updated_scores:
                    member_id = score['member_id']
                    update_data[member_id] = {
                        'game_pt': score['game_pt'],
                        'match_pt': score['match_pt'],
                        'putt_pt': score['putt_pt'],  # put_pt から putt_pt に修正
                        'total_pt': score['total_pt']
                    }
                
                # デバッグ情報を表示
                st.text(f"ラウンド ID {round_id}: {len(update_data)}名分のデータを更新します")
                
                # 一括更新
                success, updates, failures = update_scores_batch(round_id, update_data)
                if success:
                    stats["success"] += 1
                    status_text.text(f"ラウンド ID {round_id}: 更新成功 ({len(updates)}件)")
                else:
                    stats["failed"] += 1
                    status_text.text(f"ラウンド ID {round_id}: 一部更新失敗 ({len(failures)}件)")
                    for failure in failures:
                        st.error(f"  - 失敗: {failure.get('error', 'Unknown error')}")
                
            except Exception as e:
                stats["failed"] += 1
                status_text.text(f"ラウンド ID {round_id}: エラー発生 ({str(e)})")
                st.error(f"ラウンド ID {round_id} の処理中にエラーが発生しました: {str(e)}")
        
        # 完了表示
        progress_bar.progress(1.0)
        status_text.text("処理完了")
        
        # 結果表示
        st.write("### 過去データ再計算の結果")
        st.write(f"- 成功: {stats['success']} ラウンド")
        st.write(f"- 失敗: {stats['failed']} ラウンド") 
        st.write(f"- スキップ: {stats['skipped']} ラウンド")
        st.write(f"- 合計: {stats['total']} ラウンド")
        
        if stats["failed"] == 0 and stats["skipped"] == 0:
            st.success("過去データも更新しました。")
        elif stats["failed"] == 0:
            st.info(f"処理完了しましたが、{stats['skipped']}ラウンドはスキップされました。")
        else:
            st.warning(f"一部のラウンド({stats['failed']}件)で更新に失敗しました。")
            
        return stats["success"] > 0
            
    except Exception as e:
        st.error(f"過去データの再計算処理中にエラーが発生しました: {str(e)}")
        return False
