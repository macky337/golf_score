import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback  # 追加: 必要な関数をインポート

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("バックスコア入力")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")
    
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
        return    # 並び替え: member_idでソート
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])
    
    # フロントスコアがまだ入力されていない場合の警告
    front_scores_missing = any(score.get('front_score', 0) == 0 for score in scores_data)
    if front_scores_missing:
        st.warning("一部のフロントスコアがまだ入力されていません。先にフロントスコアを入力することをお勧めします。")
        if st.button("フロントスコア入力へ"):
            switch_page("02_フロントスコア入力")    # セッション状態の初期化（フォーム実行前に必ず実行）
    for score in scores_data:
        member_id = score['member_id']
          # データベースから取得した値を確実にセッション状態に設定
        score_values = {
            'back_score': score.get('back_score'),
            'back_putt': score.get('back_putt'),
            'back_game_pt': score.get('back_game_pt')
        }
        
        for field, db_value in score_values.items():
            session_key = f"{field}_{member_id}"
            
            # 入力中に再読み込みされた場合はセッション状態を優先
            if session_key not in st.session_state:
                # データベース値が有効な場合はそれを使用（nullまたは-300の場合は0を使用）
                if db_value is not None and db_value != -300:
                    st.session_state[session_key] = db_value
                else:
                    st.session_state[session_key] = 0
    
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
                st.number_input(
                    "バックスコア", 
                    min_value=0, 
                    max_value=100,
                    key=f"back_score_{member_id}"
                )
            
            with col2:
                st.number_input(
                    "バックパット",
                    min_value=0,
                    max_value=40,
                    key=f"back_putt_{member_id}"
                )
            
            with col3:
                st.number_input(
                    "バックゲームポイント",
                    min_value=-300,
                    max_value=300,
                    key=f"back_game_pt_{member_id}"
                )
            
            st.write("---")  # プレイヤー間の区切り線
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.back_form_submitted = True
      # 入力内容の確認と保存
    if st.session_state.back_form_submitted:
        st.success("スコアを保存しました！")
        
        # 確認表示用に入力データを保持
        saved_scores = {}
        try:
            # バックスコア保存後の各種処理
            
            # 1. 各プレイヤーのデータをデータベースに保存
            for score in scores_data:
                member_id = score['member_id']
                # セッション状態からスコアを取得
                back_score = st.session_state[f"back_score_{member_id}"]
                back_putt = st.session_state[f"back_putt_{member_id}"]
                back_game_pt = st.session_state[f"back_game_pt_{member_id}"]
                
                # 保存した値を記憶（確認表示用）
                saved_scores[member_id] = {
                    'back_score': back_score,
                    'back_putt': back_putt,
                    'back_game_pt': back_game_pt,
                    'name': score['member']['name'] if score.get('member') else f"Player {member_id}"
                }
                
                # front_score を取得して合計する
                front_score = score.get('front_score', 0) or 0
                
                # 更新データを作成
                update_data = {
                    'back_score': back_score,
                    'back_putt': back_putt,
                    'back_game_pt': back_game_pt,
                    'total_score': front_score + back_score  # total_score を計算して保存
                }
                
                # データベース更新
                supabase.table('score').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
            
            # 2. 計算結果をround_resultsに保存
            # 現在のround_idのすべてのスコアを取得
            current_scores = get_scores_with_fallback(round_id)
            if current_scores:
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
                player_data = initialize_player_data(current_scores, round_results)
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
        
        # 確認表示（Streamlitで表示するため、フォーム送信状態をリセットする前に処理）
        st.write("### 入力内容の確認")
        
        # 保存したスコアの一覧表を表示
        scores_df = []
        for member_id, saved_data in saved_scores.items():
            scores_df.append({
                'プレイヤー': saved_data['name'],
                'バックスコア': saved_data['back_score'],
                'バックパット': saved_data['back_putt'],
                'バックゲームポイント': saved_data['back_game_pt']
            })
        
        # DataFrameとして表示
        scores_table = pd.DataFrame(scores_df)
        st.dataframe(scores_table, use_container_width=True)
        
        # フォーム送信状態をリセット (表示した後でリセット)
        st.session_state.back_form_submitted = False
          # エキストラスコア入力またはハンディキャップ計算ページへのリンク
        col1, col2 = st.columns(2)
        with col1:
            if st.button("エキストラスコア入力へ", use_container_width=True, key="to_extra"):
                # セッション状態を明示的に保存
                st.session_state.active_round_id = round_id
                # Streamlitキャッシュをクリア
                st.cache_data.clear()
                # ラウンドのhas_extraフラグを更新
                supabase.table('rounds').update({'has_extra': True}).eq('round_id', round_id).execute()
                # シンプルなページ名で遷移
                switch_page("エキストラスコア入力")
        with col2:
            if st.button("結果確認へ", use_container_width=True, key="to_results"):
                # セッション状態を明示的に保存
                st.session_state.active_round_id = round_id
                # Streamlitキャッシュをクリア
                st.cache_data.clear()
                switch_page("結果確認")

if __name__ == "__main__":
    run()