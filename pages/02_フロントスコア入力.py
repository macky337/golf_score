import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback  # 追加: バックスコア入力と同様に必要な関数をインポート
from components.navigation import show_navigation  # ナビゲーションコンポーネントを追加

def run():
    # ナビゲーションバーを表示（ページ間の移動を容易にする）
    show_navigation(active_page="フロントスコア入力")
    
    # タイトル表示
    st.title("フロントスコア入力")
    
    # アクティブなラウンドIDをセッション状態から取得
    if "active_round_id" not in st.session_state:
        st.error("ラウンドが選択されていません。ホーム画面から選択してください。")
        if st.button("ホームに戻る"):
            switch_page("main")
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
    
    # フォーム送信状態を追跡
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False
    
    # プレイヤーごとの入力フォームを表示
    with st.form("front_scores_form"):
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            st.write(f"#### {player_name}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input(
                    "フロントスコア", 
                    min_value=0, 
                    max_value=100,
                    key=f"front_score_{member_id}"
                )
            
            with col2:
                st.number_input(
                    "フロントパット",
                    min_value=0,
                    max_value=40,
                    key=f"front_putt_{member_id}"
                )
            
            with col3:
                st.number_input(
                    "フロントゲームポイント",
                    min_value=-300,
                    max_value=300,
                    key=f"front_game_pt_{member_id}"
                )
            
            st.write("---")  # プレイヤー間の区切り線
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.form_submitted = True
    
    # 入力内容の確認と保存
    if st.session_state.form_submitted:
        st.success("スコアを保存しました！")
        
        # スコア情報を更新
        for score in scores_data:
            member_id = score['member_id']
            front_score = st.session_state[f"front_score_{member_id}"]
            front_putt = st.session_state[f"front_putt_{member_id}"]
            front_game_pt = st.session_state[f"front_game_pt_{member_id}"]
            
            # back_score が既存の場合は取得
            back_score = score.get('back_score', 0) or 0
            
            # 更新データを作成
            update_data = {
                'front_score': front_score,
                'front_putt': front_putt,
                'front_game_pt': front_game_pt,
                'total_score': front_score + back_score  # total_score を計算して保存
            }
            
            # データベース更新
            supabase.table('score').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
        
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
        st.info("フロントスコアの入力が完了しました。サイドバーから『03_バックスコア入力』を選択してください。")

if __name__ == "__main__":
    run()