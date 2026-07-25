import sys
import os
import logging

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
from modules.db import ensure_supabase
from modules.page_utils import switch_page
# 追加: 必要なモジュールをインポート
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback
from modules.input_helpers import smart_number_input, close_sidebar_on_mobile
from modules.scorecard_reader_ui import render_scorecard_reader
from modules.auth import require_login
from modules.round_context import select_editable_round

logger = logging.getLogger(__name__)

def run():
    require_login()

    # スマホでサイドバーを自動的に閉じる
    close_sidebar_on_mobile()
    
    # show_navigation(active_page="エキストラスコア入力")  # 共通ナビゲーションバーを削除
    
    st.title("エキストラスコア入力")
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
    active_round = select_editable_round(supabase, "extra_active_round")
    if not active_round:
        return
    round_id = active_round["round_id"]
    
    # エキストラ入力を明示的に開始した場合だけ has_extra を更新する
    if not active_round.get('has_extra'):
        st.info("エキストラを実施した場合だけ入力を開始してください。")
        start_extra, skip_extra = st.columns(2)
        with start_extra:
            if st.button("エキストラ入力を開始", type="primary", use_container_width=True):
                supabase.table('rounds').update({'has_extra': True}).eq('round_id', round_id).execute()
                st.rerun()
        with skip_extra:
            if st.button("実施なし・結果確認へ", use_container_width=True):
                switch_page("05_結果確認")
        return
    
    # スコア情報を取得
    scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores.data:
        st.error("スコアデータが見つかりません。")
        return
      # 並び替え: member_idでソート
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])    # バックスコアがまだ入力されていない場合の警告
    back_scores_missing = any(score.get('back_score', 0) == 0 for score in scores_data)
    if back_scores_missing and not st.session_state.get('skip_back_warning', False):
        st.warning("⚠️ 一部のバックスコアがまだ入力されていません。先にバックスコアを入力することをお勧めします。")
        
        # 未入力のプレイヤーを表示
        missing_players = []
        for score in scores_data:
            if score.get('back_score', 0) == 0:
                player_name = score['member']['name'] if score['member'] else f"Player {score['member_id']}"
                missing_players.append(player_name)
        
        if missing_players:
            st.error(f"バックスコア未入力: {', '.join(missing_players)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("バックスコア入力へ", type="primary"):
                switch_page("03_バックスコア入力")
        with col2:
            if st.button("このまま続行"):
                st.session_state['skip_back_warning'] = True
                st.rerun()
        
        return  # 警告表示中はフォームを表示しない    
    
    # ラウンドIDが変更された場合、セッション状態をクリア
    if 'last_round_id_extra' not in st.session_state or st.session_state.last_round_id_extra != round_id:
        # 古いスコアデータのセッション状態をクリア
        keys_to_remove = [key for key in st.session_state.keys() if 
                         isinstance(key, str) and (
                         key.startswith('extra_score_') or 
                         key.startswith('extra_putt_') or 
                         key.startswith('extra_game_pt_'))]
        for key in keys_to_remove:
            del st.session_state[key]
        st.session_state.last_round_id_extra = round_id
        # 初期化フラグもリセット
        initialization_key_temp = f"extra_initialized_{round_id}"
        if initialization_key_temp in st.session_state:
            del st.session_state[initialization_key_temp]
    
    # セッション状態の初期化（データベース値を一度だけ設定）
    initialization_key = f"extra_initialized_{round_id}"
    if initialization_key not in st.session_state:
        st.session_state[initialization_key] = True
        for score in scores_data:
            member_id = score['member_id']
            
            # データベースから取得した値をセッション状態に設定
            score_values = {
                'extra_score': score.get('extra_score'),
                'extra_putt': score.get('extra_putt'), 
                'extra_game_pt': score.get('extra_game_pt')
            }
            
            for field, db_value in score_values.items():
                session_key = f"{field}_{member_id}"
                
                # データベースの値を優先（nullの場合は0、-300の異常値も0に）
                if db_value is not None and db_value != -300:
                    st.session_state[session_key] = db_value
                else:
                    st.session_state[session_key] = 0
    
    # プレイヤーごとのスコア入力フォーム
    st.write("### スコア入力")
    render_scorecard_reader(scores_data, "extra", "エキストラスコア")
    
    # フォーム送信状態を追跡
    if "extra_form_submitted" not in st.session_state:
        st.session_state.extra_form_submitted = False
      # プレイヤーごとの入力フォームを表示
    with st.form("extra_scores_form"):
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            with st.container(border=True):
                st.write(f"#### {player_name}")
                current_extra_score = score.get('extra_score', 0)
                current_extra_putt = score.get('extra_putt', 0)
                current_extra_game_pt = score.get('extra_game_pt', 0)
                if current_extra_score != 0 or current_extra_putt != 0 or current_extra_game_pt != 0:
                    st.caption(f"保存済み：スコア {current_extra_score}／パット {current_extra_putt}／GP {current_extra_game_pt:+}")

                col1, col2 = st.columns(2)
                with col1:
                    smart_number_input(
                        "Extraスコア",
                        key=f"extra_score_{member_id}",
                        min_value=0,
                        max_value=100,
                        default_value=st.session_state.get(f"extra_score_{member_id}", 0),
                    )
                with col2:
                    smart_number_input(
                        "Extraパット",
                        key=f"extra_putt_{member_id}",
                        min_value=0,
                        max_value=40,
                        default_value=st.session_state.get(f"extra_putt_{member_id}", 0),
                    )
                smart_number_input(
                    "Extraゲームポイント",
                    key=f"extra_game_pt_{member_id}",
                    min_value=-300,
                    max_value=300,
                    default_value=st.session_state.get(f"extra_game_pt_{member_id}", 0),
                )
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.extra_form_submitted = True
    # 入力内容の確認と保存
    if st.session_state.extra_form_submitted:
        # バッチレコード作成
        records = []
        errors = []
        for score in scores_data:
            member_id = score['member_id']
            member_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            extra_score = st.session_state.get(f"extra_score_{member_id}", 0)
            extra_putt = st.session_state.get(f"extra_putt_{member_id}", 0)
            extra_game_pt = st.session_state.get(f"extra_game_pt_{member_id}", 0)
            # 入力値の検証
            if extra_score < 0 or extra_score > 100:
                errors.append(f"{member_name}: エキストラスコア範囲外")
                continue
            if extra_putt < 0 or extra_putt > 40:
                errors.append(f"{member_name}: エキストラパット範囲外")
                continue
            if extra_game_pt < -300 or extra_game_pt > 300:
                errors.append(f"{member_name}: エキストラゲームポイント範囲外")
                continue
            rec = {
                'member_id': member_id,
                'extra_score': extra_score,
                'extra_putt': extra_putt,
                'extra_game_pt': extra_game_pt
            }
            records.append(rec)

        if errors:
            for e in errors:
                st.error(e)
            return

        from modules.supabase_client import upsert_scores_batch
        ok, res = upsert_scores_batch(round_id, records)
        if not ok:
            st.error(f"一括保存に失敗しました: {res}")
            return
        else:
            st.success("エキストラスコアを保存しました")
        # ▼▼▼ 追加: 計算結果をround_resultsに保存 ▼▼▼
        try:
            # --- 進捗コメント出力をすべて削除 ---
            # 現在のround_idのすべてのスコアを取得
            scores = get_scores_with_fallback(round_id)
            if not scores:
                raise Exception("スコアデータの取得に失敗しました")
            
            # ハンディキャップ情報を取得
            handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
            handicaps_data = handicaps_result.data
            
            # ラウンド情報を取得
            round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
            active_round = round_result.data[0] if round_result.data else None
            if not active_round:
                raise Exception("ラウンド情報の取得に失敗しました")
            
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
            
            # round_resultsに保存
            save_result = save_round_results(round_id, updated_player_data)
            
            if save_result:
                st.success("✅ 計算結果をround_resultsテーブルに保存しました")
            else:
                st.error("❌ 計算結果の保存に失敗しました")
                
        except Exception as e:
            logger.exception("エキストラスコアの計算に失敗しました")
            st.error(f"❌ 計算処理中にエラーが発生しました: {str(e)}")
          
        # 初期化フラグをリセットして、次回アクセス時にデータベースから最新値を取得
        initialization_key = f"extra_initialized_{round_id}"
        if initialization_key in st.session_state:
            del st.session_state[initialization_key]
        
        # フォーム送信状態をリセット
        st.session_state.extra_form_submitted = False
        # 結果確認ページへのリンク
        st.info("エキストラスコアを保存しました。結果を確認してください。")
        # # ↓もし遷移が機能する場合は下記を有効化
        # if st.button("結果確認へ", use_container_width=True, key="to_results"):
        #     st.session_state.active_round_id = round_id
        #     st.cache_data.clear()
        #     switch_page("06_結果確認")
        
        # 確認表示
        st.write("### 入力内容の確認")
        
        # 入力されたスコアの一覧表を表示
        scores_df = []
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            scores_df.append({
                'プレイヤー': player_name,
                'エキストラスコア': st.session_state[f"extra_score_{member_id}"],
                'エキストラパット': st.session_state[f"extra_putt_{member_id}"],
                'エキストラゲームポイント': st.session_state[f"extra_game_pt_{member_id}"]
            })
        
        # DataFrameとして表示
        scores_table = pd.DataFrame(scores_df)
        st.dataframe(scores_table, use_container_width=True)
    
    # 結果確認ページへのリンク
    if st.button("結果確認へ", use_container_width=True):
        switch_page("05_結果確認")

if __name__ == "__main__":
    run()
