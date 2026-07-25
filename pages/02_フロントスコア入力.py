import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
from modules.db import ensure_supabase
from modules.page_utils import switch_page
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback  # 追加: バックスコア入力と同様に必要な関数をインポート
from modules.input_helpers import smart_number_input, close_sidebar_on_mobile
from modules.scorecard_reader_ui import render_scorecard_reader
from modules.auth import require_login
from modules.round_context import select_editable_round

def run():
    require_login()

    # スマホでサイドバーを自動的に閉じる
    close_sidebar_on_mobile()
    
    # ナビゲーションバーを表示（ページ間の移動を容易にする）
    # show_navigation(active_page="フロントスコア入力")
    
    # タイトル表示
    st.title("フロントスコア入力")
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
    active_round = select_editable_round(supabase, "front_active_round")
    if not active_round:
        return
    round_id = active_round["round_id"]
    
    # スコア情報を取得
    scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores.data:
        st.error("スコアデータが見つかりません。")
        return
      # 並び替え: member_idでソート
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])
    
    # ラウンドIDが変更された場合、セッション状態をクリア
    if 'last_round_id' not in st.session_state or st.session_state.last_round_id != round_id:
        # 古いスコアデータのセッション状態をクリア
        keys_to_remove = [key for key in st.session_state.keys() if 
                         isinstance(key, str) and (
                         key.startswith('front_score_') or 
                         key.startswith('front_putt_') or 
                         key.startswith('front_game_pt_'))]
        for key in keys_to_remove:
            del st.session_state[key]
        st.session_state.last_round_id = round_id
    
    # セッション状態の初期化（フォーム実行前に必ず実行）
    for score in scores_data:
        member_id = score['member_id']
        # フロントスコアの初期化：安全な初期化処理
        db_front_score = score.get('front_score', 0)
        session_key = f"front_score_{member_id}"
        if session_key not in st.session_state:
            st.session_state[session_key] = db_front_score if db_front_score is not None else 0
        # フロントパットの初期化：安全な初期化処理
        db_front_putt = score.get('front_putt', 0)
        session_key = f"front_putt_{member_id}"
        if session_key not in st.session_state:
            st.session_state[session_key] = db_front_putt if db_front_putt is not None else 0
        # フロントゲームポイントの初期化：安全な初期化処理
        db_front_game_pt = score.get('front_game_pt', 0)
        session_key = f"front_game_pt_{member_id}"
        if session_key not in st.session_state:
            st.session_state[session_key] = db_front_game_pt if db_front_game_pt is not None else 0
    
    # プレイヤーごとのスコア入力フォーム
    st.write("### スコア入力")
    render_scorecard_reader(scores_data, "front", "OUTスコア")
    
    # フォーム送信状態を追跡
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    
    # プレイヤーごとの入力フォームを表示
    with st.form("front_scores_form"):
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            with st.container(border=True):
                st.write(f"#### {player_name}")
                col1, col2 = st.columns(2)
                with col1:
                    smart_number_input(
                        "OUTスコア",
                        key=f"front_score_{member_id}",
                        min_value=0,
                        max_value=100,
                        default_value=st.session_state.get(f"front_score_{member_id}", 0),
                    )
                with col2:
                    smart_number_input(
                        "OUTパット",
                        key=f"front_putt_{member_id}",
                        min_value=0,
                        max_value=40,
                        default_value=st.session_state.get(f"front_putt_{member_id}", 0),
                    )
                smart_number_input(
                    "OUTゲームポイント",
                    key=f"front_game_pt_{member_id}",
                    min_value=-300,
                    max_value=300,
                    default_value=st.session_state.get(f"front_game_pt_{member_id}", 0),
                )
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.form_submitted = True
    
    # 入力内容の確認と保存
    if st.session_state.form_submitted:
        # スコア情報を更新
        # 変更点: 各プレイヤーの更新データをローカルリストにまとめ、一括 upsert を行う
        records = []
        for score in scores_data:
            member_id = score['member_id']
            front_score = st.session_state[f"front_score_{member_id}"]
            front_putt = st.session_state[f"front_putt_{member_id}"]
            front_game_pt = st.session_state[f"front_game_pt_{member_id}"]
            back_score = score.get('back_score', 0) or 0
            rec = {
                'member_id': member_id,
                'front_score': front_score,
                'front_putt': front_putt,
                'front_game_pt': front_game_pt,
                'total_score': front_score + back_score
            }
            records.append(rec)

        from modules.supabase_client import upsert_scores_batch
        ok, res = upsert_scores_batch(round_id, records)
        if not ok:
            st.error(f"一括保存に失敗しました: {res}")
            st.session_state.form_submitted = False
            return
        else:
            st.success("フロントスコアを保存しました")
        
        # ▼▼▼ 追加: 計算結果をround_resultsに保存 ▼▼▼
        try:
            # 現在のround_idのすべてのスコアを取得
            scores = get_scores_with_fallback(round_id)  # 変更: より堅牢な関数を使用
            if scores:
                # ハンディキャップ情報を取得
                handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                handicaps_data = handicaps_result.data
                
                # ラウンド情報を取得
                round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
                active_round = round_result.data[0] if round_result.data else None
                
                # round_resultsを取得（存在する場合）
                round_results = get_round_results(round_id)
                
                # プレイヤーデータ初期化
                from modules.data_formatter import initialize_player_data
                player_data = initialize_player_data(scores, round_results)
                player_ids = sorted(list(player_data.keys()))
                
                # ハンディキャップ辞書作成
                handicaps = {}
                total_only_set = set()
                if handicaps_data:
                    for h in handicaps_data:
                        handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                        handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                        if 'total_only' in h and h['total_only']:
                            total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
                
                # ポイント計算と保存
                updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
                save_result = save_round_results(round_id, updated_player_data)
                if save_result:
                    st.info("計算結果をround_resultsテーブルに保存しました")
                else:
                    st.warning("計算結果の保存に失敗しました")
        except Exception as e:
            st.warning(f"計算処理中にエラーが発生しました: {e}")
          # フォーム送信状態をリセット
        st.session_state.form_submitted = False
        
        # 確認表示
        st.write("### 入力内容の確認")
        
        # 入力されたスコアの一覧表を表示
        scores_df = []
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            scores_df.append({
                'プレイヤー': player_name,
                'フロントスコア': st.session_state[f"front_score_{member_id}"],
                'フロントパット': st.session_state[f"front_putt_{member_id}"],
                'フロントゲームポイント': st.session_state[f"front_game_pt_{member_id}"]
            })
        
        # DataFrameとして表示
        scores_table = pd.DataFrame(scores_df)
        st.dataframe(scores_table, use_container_width=True)
        
        # バックスコア入力ページへのリンク
        st.markdown("### 次のステップ")
        st.info("フロントスコアを保存しました。続けてINのスコアを入力してください。")
        if st.button("IN入力へ", type="primary", use_container_width=True):
            switch_page("03_バックスコア入力")

if __name__ == "__main__":
    run()
