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
from modules.supabase_client import get_scores_with_fallback
from modules.input_helpers import toggle_input_mode, smart_number_input, close_sidebar_on_mobile
from modules.auth import require_login

def run():
    require_login()

    # スマホでサイドバーを自動的に閉じる
    close_sidebar_on_mobile()
    
    st.title("バックスコア入力")
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
    # アクティブなラウンドIDをセッション状態から取得
    if "active_round_id" not in st.session_state:
        st.error("ラウンドが選択されていません。ホーム画面から選択してください。")
        if st.button("ホームに戻る"):
            st.switch_page("main.py")
        return
    
    round_id = st.session_state.active_round_id
    
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        st.error("ラウンド情報が見つかりません。")
        return
    
    active_round = round_result.data[0]
    st.write(f"### {active_round['date_played']} - {active_round['course_name']}")
    
    # 入力モード切り替えボタン
    toggle_input_mode()
    
    # スコア情報を取得
    scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores.data:
        st.error("スコアデータが見つかりません。")
        return    # 並び替え: member_idでソート
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])
    
    # ラウンドIDが変更された場合、セッション状態をクリア
    if 'last_round_id_back' not in st.session_state or st.session_state.last_round_id_back != round_id:
        # 古いスコアデータのセッション状態をクリア
        keys_to_remove = [key for key in st.session_state.keys() if 
                         isinstance(key, str) and (
                         key.startswith('back_score_') or 
                         key.startswith('back_putt_') or 
                         key.startswith('back_game_pt_'))]
        for key in keys_to_remove:
            del st.session_state[key]
        st.session_state.last_round_id_back = round_id
    
    # フロントスコアがまだ入力されていない場合の警告
    front_scores_missing = any(score.get('front_score', 0) == 0 for score in scores_data)
    if front_scores_missing:
        st.warning("一部のフロントスコアがまだ入力されていません。先にフロントスコアを入力することをお勧めします。")
        if st.button("フロントスコア入力へ"):
            switch_page("02_フロントスコア入力")    # セッション状態の初期化（ウィジェット表示前のみ！）
    for score in scores_data:
        member_id = score['member_id']
        score_values = {
            'back_score': score.get('back_score'),
            'back_putt': score.get('back_putt'),
            'back_game_pt': score.get('back_game_pt')
        }
        for field, db_value in score_values.items():
            session_key = f"{field}_{member_id}"
            if session_key not in st.session_state:
                st.session_state[session_key] = db_value if db_value is not None and db_value != -300 else 0

    # プレイヤーごとのスコア入力フォーム
    st.write("### スコア入力")
    
    # フォーム送信状態を追跡
    if "back_form_submitted" not in st.session_state:
        st.session_state.back_form_submitted = False
    
    # プレイヤーごとの入力フォームを表示
    with st.form("back_scores_form"):
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            st.write(f"#### {player_name}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                smart_number_input(
                    "バックスコア", 
                    key=f"back_score_{member_id}",
                    min_value=0, 
                    max_value=100,
                    default_value=st.session_state.get(f"back_score_{member_id}", 0),
                    step_buttons=[-5, -1, 1, 5]
                )
            
            with col2:
                smart_number_input(
                    "バックパット",
                    key=f"back_putt_{member_id}",
                    min_value=0,
                    max_value=40,
                    default_value=st.session_state.get(f"back_putt_{member_id}", 0),
                    step_buttons=[-2, -1, 1, 2]
                )
            
            with col3:
                smart_number_input(
                    "バックゲームポイント",
                    key=f"back_game_pt_{member_id}",
                    min_value=-300,
                    max_value=300,
                    default_value=st.session_state.get(f"back_game_pt_{member_id}", 0),
                    step_buttons=[-10, -1, 1, 10]
                )
            
            st.write("---")  # プレイヤー間の区切り線
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.back_form_submitted = True
      # 入力内容の確認と保存
    if st.session_state.back_form_submitted:
        st.success("スコアを保存しました！")

        # 一括 upsert 用のレコード作成
        records = []
        for score in scores_data:
            member_id = score['member_id']
            back_score = st.session_state[f"back_score_{member_id}"]
            back_putt = st.session_state[f"back_putt_{member_id}"]
            back_game_pt = st.session_state[f"back_game_pt_{member_id}"]
            front_score = score.get('front_score', 0) or 0
            rec = {
                'member_id': member_id,
                'back_score': back_score,
                'back_putt': back_putt,
                'back_game_pt': back_game_pt,
                'total_score': front_score + back_score
            }
            records.append(rec)

        from modules.supabase_client import upsert_scores_batch
        ok, res = upsert_scores_batch(round_id, records)
        if not ok:
            st.error(f"一括保存に失敗しました: {res}")
        else:
            st.success("一括でスコアを保存しました")

        # 計算処理は既存ロジックを再利用
        try:
            current_scores = get_scores_with_fallback(round_id)
            if current_scores:
                handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                handicaps_data = handicaps_result.data
                round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
                active_round = round_result.data[0] if round_result.data else None
                round_results = get_round_results(round_id)
                from modules.data_formatter import initialize_player_data
                player_data = initialize_player_data(current_scores, round_results)
                player_ids = sorted(list(player_data.keys()))
                handicaps = {}
                total_only_set = set()
                if handicaps_data:
                    for h in handicaps_data:
                        handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                        handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                        if 'total_only' in h and h['total_only']:
                            total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
                updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
                save_result = save_round_results(round_id, updated_player_data)
                if save_result:
                    st.info("計算結果をround_resultsテーブルに保存しました")
                else:
                    st.warning("計算結果の保存に失敗しました")
            else:
                st.warning("スコアデータの取得に失敗しました")
        except Exception as e:
            st.warning(f"計算処理中にエラーが発生しました: {e}")

        # 確認表示
        st.write("### 入力内容の確認")
        scores_df = []
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            scores_df.append({
                'プレイヤー': player_name,
                'バックスコア': st.session_state[f"back_score_{member_id}"],
                'バックパット': st.session_state[f"back_putt_{member_id}"],
                'バックゲームポイント': st.session_state[f"back_game_pt_{member_id}"]
            })
        scores_table = pd.DataFrame(scores_df)
        st.dataframe(scores_table, use_container_width=True)

        # round_results表示
        round_results = get_round_results(round_id)
        if round_results:
            id_to_name = {s['member_id']: s['member']['name'] if s.get('member') else f"Player {s['member_id']}" for s in scores_data}
            rows = []
            for member_id, data in round_results.items():
                row = {'名前': id_to_name.get(member_id, f"Player {member_id}")}
                row.update(data)
                rows.append(row)
            results_df = pd.DataFrame(rows)
            st.dataframe(results_df, use_container_width=True)
        else:
            st.info("まだラウンド結果が計算されていません。")
        
        st.session_state.back_form_submitted = False
    else:
        st.warning("ラウンドIDがアクティブではありません。")
        
        # --- スコア入力フォームのリセット機能 ---
    if st.button("スコア入力をリセット"):
        # Streamlit 1.32以降はst.rerun()に変更
        import streamlit as _st
        if hasattr(_st, "rerun"):
            _st.rerun()
        else:
            st.rerun()

if __name__ == "__main__":
    run()
