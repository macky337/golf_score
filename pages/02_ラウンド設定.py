import streamlit as st
import datetime
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
from modules.models import get_course_list, get_or_create_course

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("ラウンド設定")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")

    # メンバー一覧の取得
    members_result = supabase.table('member').select('*').order('name').execute()
    member_dict = {m['name']: m['member_id'] for m in members_result.data}

    # 過去のゴルフ場名を取得（coursesテーブルから）
    courses = get_course_list()
    unique_courses = sorted([c['name'] for c in courses])
    
    # コース管理画面へのリンク（フォームの外に配置）
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("➕ コース管理"):
            switch_page("コース管理")

    # フォーム入力部分
    with st.form("round_setup"):
        # 1) 開催日の選択
        date_played = st.date_input(
            "プレー日を選択",
            value=datetime.date.today(),
            min_value=datetime.date(2024, 1, 1)
        )
        
        # 2) ゴルフ場の選択
        if not unique_courses:
            st.warning("登録済みのゴルフ場がありません。")
            st.info("コース管理画面でゴルフ場を登録してください。")
            if st.form_submit_button("コース管理へ"):
                switch_page("コース管理")
            return
        
        course_name = st.selectbox(
            "ゴルフ場を選択",
            options=unique_courses
        )
        
        # 3) 参加者の選択
        st.write("### 参加者選択")
        selected_members = st.multiselect(
            "参加者を選択してください",
            options=list(member_dict.keys())
        )
        
        num_players = len(selected_members)
        if num_players > 1:
            # プレイヤーのペアを作成して、それぞれのハンディキャップを設定
            st.write("### ハンディキャップ設定")
            match_handicaps = []
            pairs = [(selected_members[i], selected_members[j]) 
                    for i in range(len(selected_members)) 
                    for j in range(i+1, len(selected_members))]
            
            for pair in pairs:
                st.write(f"#### {pair[0]} vs {pair[1]}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    h1to2 = st.number_input(
                        f"{pair[0]} → {pair[1]} Handicap",
                        min_value=0, max_value=50, step=1, value=0,
                        key=f"h_{pair[0]}_{pair[1]}"
                    )
                with col2:
                    h2to1 = st.number_input(
                        f"{pair[1]} → {pair[0]} Handicap",
                        min_value=0, max_value=50, step=1, value=0,
                        key=f"h_{pair[1]}_{pair[0]}"
                    )
                with col3:
                    total_only = st.checkbox(
                        "total scoreのみで戦う",
                        key=f"total_only_{pair[0]}_{pair[1]}"
                    )
                
                match_handicaps.append({
                    "player1": pair[0],
                    "player2": pair[1],
                    "handicap_1_to_2": h1to2,
                    "handicap_2_to_1": h2to1,
                    "total_only": total_only
                })
        else:
            st.info("ハンデキャップ設定は、参加者が2名以上選ばれた場合に利用可能です。")

        # 4) 「Start Round」ボタン
        if st.form_submit_button("Start Round"):
            if not course_name:
                st.error("ゴルフ場を選択してください。")
            elif len(selected_members) < 2:
                st.error("少なくとも2人の参加者を選択してください。")
            else:
                try:
                    # コースの取得
                    course_name = course_name.strip()
                    course = get_or_create_course(course_name)
                    
                    if not course:
                        st.error(f"ゴルフ場「{course_name}」の登録に失敗しました。")
                        return
                    
                    # 最大のround_idを取得して、新しいIDを作成
                    max_id_result = supabase.table('rounds').select('round_id').order('round_id', desc=True).limit(1).execute()
                    next_round_id = 1
                    if max_id_result.data:
                        next_round_id = max_id_result.data[0]['round_id'] + 1
                    
                    # roundsテーブルへ新規ラウンドをINSERT（round_idを明示的に指定）
                    round_data = {
                        'round_id': next_round_id,
                        'date_played': date_played.isoformat(),
                        'date': date_played.isoformat(),
                        'course_name': course_name,
                        'num_players': num_players,
                        'has_extra': False,
                        'finalized': False
                    }
                    
                    round_result = supabase.table('rounds').insert(round_data).execute()
                    round_id = round_result.data[0]['round_id']

                    # スコアの初期レコードを作成
                    max_score_id_result = supabase.table('score').select('score_id').order('score_id', desc=True).limit(1).execute()
                    next_score_id = 1
                    if max_score_id_result.data:
                        next_score_id = max_score_id_result.data[0]['score_id'] + 1

                    for member_name in selected_members:
                        member_id = member_dict[member_name]
                        score_data = {
                            'score_id': next_score_id,
                            'round_id': round_id,
                            'member_id': member_id,
                            'front_score': 0,
                            'back_score': 0,
                            'extra_score': 0,
                            'front_putt': 0,
                            'back_putt': 0,
                            'extra_putt': 0,
                            'front_game_pt': 0,
                            'back_game_pt': 0,
                            'extra_game_pt': 0,
                            'match_front': 0,
                            'match_back': 0,
                            'match_total': 0,
                            'match_extra': 0,
                            'match_pt': 0,
                            'put_pt': 0,
                            'total_pt': 0
                        }
                        supabase.table('score').insert(score_data).execute()
                        next_score_id += 1

                    # ハンディキャップ設定の保存
                    max_handicap_id_result = supabase.table('handicap_match').select('id').order('id', desc=True).limit(1).execute()
                    next_handicap_id = 1
                    if max_handicap_id_result.data:
                        next_handicap_id = max_handicap_id_result.data[0]['id'] + 1

                    for match in match_handicaps:
                        handicap_data = {
                            'id': next_handicap_id,
                            'round_id': round_id,
                            'player_1_id': member_dict[match['player1']],
                            'player_2_id': member_dict[match['player2']],
                            'player_1_to_2': match['handicap_1_to_2'],
                            'player_2_to_1': match['handicap_2_to_1'],
                            'total_only': match['total_only']
                        }
                        supabase.table('handicap_match').insert(handicap_data).execute()
                        next_handicap_id += 1

                    st.success("ラウンド設定が完了しました。")
                    switch_page("フロントスコア入力")

                except Exception as e:
                    st.error(f"ラウンド設定の保存中にエラーが発生しました: {str(e)}")

if __name__ == "__main__": 
    run()
