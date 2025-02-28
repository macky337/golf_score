import streamlit as st
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page

def calculate_game_pt(player_pt, other_pts):
    """ゲームポイントを計算する
    
    3人プレーの場合：自分のポイント×2 - 他のプレイヤーの合計
    4人プレーの場合：そのままのポイント
    """
    if len(other_pts) == 2:  # 3人プレー
        return player_pt * 2 - sum(other_pts)
    return player_pt  # 4人プレー

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("エキストラスコア入力")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")
    
    # エキストラホールありの未確定ラウンドを取得
    rounds_result = supabase.table('rounds').select('*').eq('finalized', False).eq('has_extra', True).order('date_played', desc=True).execute()
    unfinalized_rounds = rounds_result.data

    if not unfinalized_rounds:
        st.warning("エキストラホール有りの未確定ラウンドがありません。")
        if st.button("ラウンド結果確認へ"):
            switch_page("06_結果確認")
        return

    # ラウンド選択
    round_options = [
        f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})"
        for r in unfinalized_rounds
    ]
    
    selected_round = st.selectbox(
        "ラウンドを選択",
        options=round_options,
        index=0
    )
    
    if selected_round:
        round_id = int(selected_round.split("ID: ")[1].rstrip(")"))
        round_data = next((r for r in unfinalized_rounds if r['round_id'] == round_id), None)
        
        if round_data:
            # スコアデータの取得
            scores_result = supabase.table('score').select(
                '*, member(name)'
            ).eq('round_id', round_id).execute()
            scores = scores_result.data

            if not scores:
                st.error("スコアデータが見つかりません")
                return

            # スコア入力フォーム
            with st.form("extra_score_form"):
                players_game_pts = {}  # プレイヤーごとのゲームポイントを保持
                
                # 最初のパスでゲームポイントを収集
                for score in scores:
                    player_name = score['member']['name']
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.number_input(
                            f"{player_name} - Extra Score",
                            min_value=0,
                            max_value=100,
                            value=score['extra_score'] or 0,
                            key=f"extra_{score['score_id']}"
                        )
                    
                    with col2:
                        st.number_input(
                            f"{player_name} - Extra Putt",
                            min_value=0,
                            max_value=50,
                            value=score['extra_putt'] or 0,
                            key=f"putt_{score['score_id']}"
                        )
                    
                    with col3:
                        game_pt = st.number_input(
                            f"{player_name} - Extra Game Pt",
                            value=score['extra_game_pt'] or 0,
                            key=f"game_{score['score_id']}"
                        )
                        players_game_pts[player_name] = game_pt
                
                # 3人プレーの場合、ゲームポイントを再計算
                if len(scores) == 3:
                    st.info("3人プレーの場合、ゲームポイントは自動計算されます（自分のポイント×2 - 他のプレイヤーの合計）")
                    for score in scores:
                        player_name = score['member']['name']
                        other_pts = [pt for name, pt in players_game_pts.items() if name != player_name]
                        calculated_pt = calculate_game_pt(players_game_pts[player_name], other_pts)
                        # セッション状態を更新
                        st.session_state[f"game_{score['score_id']}"] = calculated_pt
                
                submitted = st.form_submit_button("スコアを保存")
                
                if submitted:
                    try:
                        for score in scores:
                            # 更新データの準備
                            updated_data = {
                                'extra_score': st.session_state[f"extra_{score['score_id']}"],
                                'extra_putt': st.session_state[f"putt_{score['score_id']}"],
                                'extra_game_pt': st.session_state[f"game_{score['score_id']}"]
                            }
                            
                            # スコアの更新
                            supabase.table('score').update(
                                updated_data
                            ).eq('score_id', score['score_id']).execute()
                        
                        st.success("エキストラスコアを保存しました")
                        
                        # ラウンド結果確認ページへ移動するボタン
                        if st.button("ラウンド結果確認へ"):
                            switch_page("06_結果確認")
                            
                    except Exception as e:
                        st.error(f"スコアの保存中にエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    run()
