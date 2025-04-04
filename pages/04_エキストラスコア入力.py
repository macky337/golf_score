import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback
from components.navigation import show_navigation

def run():
    # ナビゲーションバーを表示
    show_navigation(active_page="エキストラスコア入力")
    
    # タイトル表示
    st.title("エキストラスコア入力")
    
    # アクティブなラウンドIDをセッション状態から取得
    if "active_round_id" not in st.session_state:
        st.error("ラウンドが選択されていません。ホーム画面から選択してください。")
        return
    
    round_id = st.session_state.active_round_id
    
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        st.error("ラウンド情報が見つかりません。")
        return
    
    active_round = round_result.data[0]
    st.write(f"### {active_round['date_played']} - {active_round['course_name']}")
    
    # スコア情報を取得
    scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores.data:
        st.error("スコアデータが見つかりません。")
        return
    
    # 並び替え: member_idでソート
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])
    
    # フロントスコアとバックスコアがまだ入力されていない場合の警告
    front_scores_missing = any(score.get('front_score', 0) == 0 for score in scores_data)
    back_scores_missing = any(score.get('back_score', 0) == 0 for score in scores_data)
    
    if front_scores_missing:
        st.warning("一部のフロントスコアがまだ入力されていません。先にフロントスコアを入力することをお勧めします。")
        if st.button("フロントスコア入力へ"):
            switch_page("フロントスコア入力")
    
    if back_scores_missing:
        st.warning("一部のバックスコアがまだ入力されていません。先にバックスコアを入力することをお勧めします。")
        if st.button("バックスコア入力へ"):
            switch_page("バックスコア入力")
    
    # プレイヤーごとのスコア入力フォーム
    st.write("### スコア入力")
    
    # フォーム送信状態を追跡
    if "extra_form_submitted" not in st.session_state:
        st.session_state.extra_form_submitted = False
    
    # 以前の入力内容をセッションから初期化（一度だけ）
    if "initialized_extra_scores" not in st.session_state:
        st.session_state.initialized_extra_scores = True
        for score in scores_data:
            member_id = score['member_id']
            st.session_state[f"extra_score_{member_id}"] = score.get('extra_score', 0)
            st.session_state[f"extra_putt_{member_id}"] = score.get('extra_putt', 0)
            st.session_state[f"extra_game_pt_{member_id}"] = score.get('extra_game_pt', 0)
    
    # プレイヤーごとの入力フォームを表示
    with st.form("extra_scores_form"):
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            st.write(f"#### {player_name}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input(
                    "エキストラスコア", 
                    min_value=0, 
                    max_value=100, 
                    key=f"extra_score_{member_id}"
                )
            
            with col2:
                st.number_input(
                    "エキストラパット",
                    min_value=0,
                    max_value=40,
                    key=f"extra_putt_{member_id}"
                )
            
            with col3:
                st.number_input(
                    "エキストラゲームポイント",
                    min_value=-50,
                    max_value=50,
                    key=f"extra_game_pt_{member_id}"
                )
            
            st.write("---")  # プレイヤー間の区切り線
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.extra_form_submitted = True
    
    # 入力内容の確認と保存
    if st.session_state.extra_form_submitted:
        st.success("スコアを保存しました！")
        
        # スコア情報を更新
        for score in scores_data:
            member_id = score['member_id']
            extra_score = st.session_state[f"extra_score_{member_id}"]
            extra_putt = st.session_state[f"extra_putt_{member_id}"]
            extra_game_pt = st.session_state[f"extra_game_pt_{member_id}"]
            
            # 更新データを作成
            update_data = {
                'extra_score': extra_score,
                'extra_putt': extra_putt,
                'extra_game_pt': extra_game_pt,
            }
            
            # データベース更新
            supabase.table('score').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
            
            # エキストラホールが入力されたらhas_extraフラグをTrueに更新
            if not active_round.get('has_extra', False) and extra_score > 0:
                supabase.table('rounds').update({'has_extra': True}).eq('round_id', round_id).execute()
                # セッション状態も更新
                st.session_state.has_extra = True
        
        # ポイント計算と保存
        try:
            # 現在のround_idのすべてのスコアを取得
            scores = get_scores_with_fallback(round_id)
            if scores:
                # ハンディキャップ情報を取得
                handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                handicaps_data = handicaps_result.data
                
                # 最新のラウンド情報を再取得
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
        st.session_state.extra_form_submitted = False
        # データの再初期化フラグをリセット
        if "initialized_extra_scores" in st.session_state:
            del st.session_state.initialized_extra_scores
        
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
        
        # 結果確認画面へのボタン
        if st.button("結果確認へ", use_container_width=True):
            switch_page("結果確認")

if __name__ == "__main__":
    run()