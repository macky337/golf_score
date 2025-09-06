import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import datetime
from modules.db import supabase
from modules.page_utils import switch_page
from modules.models import get_course_list, get_or_create_course, get_course_by_id, get_members_list


def create_score_records(supabase, round_id, member_ids):
    """選択されたメンバーのスコアレコードを作成"""
    success = True
    
    for member_id in member_ids:
        try:
            # メンバー情報を取得してプレイヤー名をログに表示
            member_info = supabase.table('member').select('name').eq('member_id', member_id).execute()
            player_name = member_info.data[0]['name'] if member_info.data else f"Player {member_id}"
            
            # スコアレコード作成 - score テーブルに存在するカラムのみを指定（idは自動生成される）
            score_data = {
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
                'total_score': 0  # total_scoreも初期化
            }
            
            # スコア追加
            supabase.table('score').insert(score_data).execute()
            print(f"{player_name} のスコアレコードを作成しました")
            
            # 次のスコアIDに進む
            next_score_id += 1
            
        except Exception as e:
            print(f"{player_name} のスコア作成エラー: {e}")
            success = False
    
    return success

def run():
    # ▼▼▼ 未確定ラウンド選択セクション ▼▼▼
    unfinalized_rounds = supabase.table('rounds').select('round_id', 'date_played', 'course_name').eq('finalized', False).order('date_played', desc=True).execute().data
    if unfinalized_rounds:
        st.write('### 未確定ラウンドの選択')
        round_options = [
            f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})" for r in unfinalized_rounds
        ]
        selected = st.selectbox('未確定ラウンドを選択して編集', options=round_options, key='unfinalized_round_select')
        if selected:
            round_id = int(selected.split('ID: ')[1].rstrip(')'))
            st.session_state.active_round_id = round_id
            st.info(f"選択中のラウンドID: {round_id} の編集画面に切り替わりました。サイドバーや各スコア入力ページから編集を続けてください。")
            st.stop()
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("ラウンド設定")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")

    # メンバー一覧の取得（ID順） 
    members = get_members_list()
    member_dict = {m['name']: m['member_id'] for m in members}
    
    # 名前とIDのリストを用意
    member_names = [m['name'] for m in members]

    # 過去のゴルフ場名を取得（coursesテーブルから）
    courses = get_course_list()
      # コース管理画面へのリンク（フォームの外に配置）
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("➕ コース管理"):
            switch_page("09_コース管理")

    # フォーム入力部分 - 全体のフォームをやめて個別のフォームに変更
    # 1) 開催日の選択
    date_played = st.date_input(
        "プレー日を選択",
        value=datetime.date.today(),
        min_value=datetime.date(2024, 1, 1)
    )
      # 2) ゴルフ場の選択
    if not courses:
        st.warning("登録済みのゴルフ場がありません。")
        st.info("コース管理画面でゴルフ場を登録してください。")
        if st.button("コース管理へ"):
            switch_page("09_コース管理")
        return
    
    # コースのID, 名前のタプルを作成
    course_options = [(c.get('id'), c.get('name')) for c in courses]

    # 一番多いゴルフ場名を集計
    from collections import Counter
    course_name_list = [c.get('name') for c in courses]
    # roundsテーブルからも集計（過去のラウンド数が多いコースを優先）
    all_rounds = supabase.table('rounds').select('course_name').execute().data
    round_course_names = [r['course_name'] for r in all_rounds if r.get('course_name')]
    if round_course_names:
        most_played_course = Counter(round_course_names).most_common(1)[0][0]
    else:
        most_played_course = course_name_list[0] if course_name_list else None

    # デフォルトインデックスを決定
    default_index = 0
    if most_played_course:
        for i, (_, name) in enumerate(course_options):
            if name == most_played_course:
                default_index = i
                break

    selected_course = st.selectbox(
        "ゴルフ場を選択",
        options=course_options,
        format_func=lambda x: x[1],  # IDは表示せず、名前だけ表示
        index=default_index if course_options else 0
    )
    
    # 選択されたコースのIDと名前を取得
    course_id, course_name = selected_course if selected_course else (None, None)
    
    # 3) 参加者の選択（ID昇順表示）
    st.write("### 参加者選択")
    selected_members = st.multiselect(
        "参加者を選択してください",
        options=member_names
    )
    
    num_players = len(selected_members)
    
    # ハンディキャップ設定セクション
    st.write("### ハンディキャップ設定")
    
    # ハンディキャップ設定の初期化
    if "handicaps" not in st.session_state:
        st.session_state.handicaps = {}
    
    # 参加者が2名以上いる場合に表示
    match_handicaps = []
    if num_players >= 2:
        # すべての可能なペアを生成
        pairs = []
        for i in range(len(selected_members)):
            for j in range(i+1, len(selected_members)):
                pairs.append((selected_members[i], selected_members[j]))
        
        # 各ペアのハンディキャップを設定
        for i, (player1, player2) in enumerate(pairs):
            pair_key = f"{player1}_vs_{player2}"
            
            # セッションステートに保存されていなければ初期化
            if pair_key not in st.session_state.handicaps:
                st.session_state.handicaps[pair_key] = {
                    "h1to2": 0,
                    "h2to1": 0,
                    "total_only": False
                }
                
            st.write(f"#### {player1} vs {player2}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                h1to2 = st.number_input(
                    f"{player1} → {player2} ハンディキャップ",
                    min_value=0, max_value=50, step=1, 
                    value=st.session_state.handicaps[pair_key]["h1to2"],
                    key=f"h1to2_{player1}_{player2}"
                )
                st.session_state.handicaps[pair_key]["h1to2"] = h1to2
                
            with col2:
                h2to1 = st.number_input(
                    f"{player2} → {player1} ハンディキャップ",
                    min_value=0, max_value=50, step=1,
                    value=st.session_state.handicaps[pair_key]["h2to1"],
                    key=f"h2to1_{player1}_{player2}"
                )
                st.session_state.handicaps[pair_key]["h2to1"] = h2to1
                
            with col3:
                total_only = st.checkbox(
                    "total scoreのみで戦う",
                    value=st.session_state.handicaps[pair_key]["total_only"],
                    key=f"total_only_{player1}_{player2}"
                )
                st.session_state.handicaps[pair_key]["total_only"] = total_only
            
            # この対戦カードのハンディキャップ情報を保存
            match_handicaps.append({
                "player1": player1,
                "player2": player2,
                "handicap_1_to_2": h1to2,
                "handicap_2_to_1": h2to1,
                "total_only": total_only
            })
    else:
        st.info("ハンディキャップ設定は、参加者が2名以上選ばれた場合に利用可能です。")

    # 4) 「Start Round」ボタン
    if st.button("Start Round"):
        if not course_name:
            st.error("ゴルフ場を選択してください。")
        elif len(selected_members) < 2:
            st.error("少なくとも2人の参加者を選択してください。")
        else:
            try:
                # コースを取得（すでに選択済み）
                
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
                    'course_name': course_name,  # 後方互換性のために残す
                    'course_id': course_id,      # 新しいリレーション用
                    'num_players': num_players,
                    'has_extra': False,
                    'finalized': False
                }
                
                round_result = supabase.table('rounds').insert(round_data).execute()
                round_id = round_result.data[0]['round_id']

                # アクティブなラウンドIDをセッション状態に保存
                st.session_state.active_round_id = round_id

                # スコアの作成（新しい実装に置き換え）
                member_ids = [member_dict[name] for name in selected_members]
                success = create_score_records(supabase, round_id, member_ids)
                
                if not success:
                    st.warning("スコアデータ作成に失敗したメンバーがいます。")
                
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

                if success:
                    st.success("ラウンド設定が完了しました。")
                    switch_page("02_フロントスコア入力")

            except Exception as e:
                st.error(f"ラウンド設定の保存中にエラーが発生しました: {str(e)}")

if __name__ == "__main__": 
    run()
