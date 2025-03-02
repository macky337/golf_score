import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.debug import handle_error

def run():
    # タイトルと戻るボタン
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("エキストラスコア入力")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")
    
    # アクティブなラウンドを取得
    try:
        active_rounds_result = supabase.table('rounds').select('*').eq('finalized', False).order('date_played', desc=True).execute()
        active_rounds = active_rounds_result.data
    except Exception as e:
        handle_error(e)
        return
        
    if not active_rounds:
        st.warning("アクティブなラウンドがありません。")
        if st.button("ラウンド設定へ"):
            switch_page("ラウンド設定")
        return
    
    # 最新のアクティブラウンドを取得
    active_round = active_rounds[0]
    round_id = active_round['round_id']
    
    # ラウンド情報を表示
    st.write(f"### {active_round['date_played']} - {active_round['course_name']}")
    
    # スコアデータを取得
    try:
        scores_result = supabase.table('score').select('*, member(name)').eq('round_id', round_id).execute()
        scores = scores_result.data
    except Exception as e:
        handle_error(e)
        return
        
    if not scores:
        st.warning("スコアデータが見つかりません。")
        return
    
    # スコア入力フォーム
    with st.form("extra_score_form"):
        # プレイヤーごとにエキストラのスコアとパットを入力
        for score in scores:
            player_name = score['member']['name']
            st.write(f"#### {player_name}")
            
            col1, col2 = st.columns(2)
            with col1:
                extra_score = st.number_input(
                    "エキストラスコア",
                    min_value=0,
                    max_value=100,
                    value=score['extra_score'] or 0,
                    key=f"extra_{score['score_id']}"
                )
            with col2:
                extra_putt = st.number_input(
                    "エキストラパット",
                    min_value=0,
                    max_value=50,
                    value=score['extra_putt'] or 0,
                    key=f"putt_{score['score_id']}"
                )
            
            # Hidden field to store score_id
            st.markdown(f"""<input type="hidden" id="score_{score['score_id']}" value="{score['score_id']}">""", unsafe_allow_html=True)
        
        # ゲームポイントの入力欄
        st.write("### ゲームポイント")
        game_points = {}
        for score in scores:
            player_name = score['member']['name']
            game_points[score['score_id']] = st.number_input(
                f"{player_name} ゲームポイント",
                min_value=-50,
                max_value=50,
                value=score['extra_game_pt'] or 0,
                key=f"game_pt_{score['score_id']}"
            )
        
        # フォーム送信ボタン
        if st.form_submit_button("スコアを保存"):
            try:
                # スコアの保存
                for score in scores:
                    score_id = score['score_id']
                    extra_score_value = st.session_state[f"extra_{score_id}"]
                    extra_putt_value = st.session_state[f"putt_{score_id}"]
                    game_pt_value = st.session_state[f"game_pt_{score_id}"]
                    
                    # データを更新
                    supabase.table('score').update({
                        'extra_score': extra_score_value,
                        'extra_putt': extra_putt_value,
                        'extra_game_pt': game_pt_value
                    }).eq('score_id', score_id).execute()
                
                st.success("エキストラスコアを保存しました")
                st.rerun()
                
            except Exception as e:
                handle_error(e)
    
    # フォームの外にはボタンを配置できる
    col1, col2 = st.columns(2)
    with col1:
        if st.button("バックスコア入力へ戻る"):
            switch_page("バックスコア入力")
    
    with col2:
        if st.button("結果確認へ"):
            switch_page("結果確認")

if __name__ == "__main__":
    run()
