import streamlit as st
import pandas as pd
from modules.db import supabase
import datetime
from streamlit_extras.switch_page_button import switch_page
import json
import os
import pytz
import time
from dotenv import load_dotenv
from modules.game_points import calculate_game_pt  # 必要な関数のみをインポート

# config からの直接インポートを削除
# from config import get_admin_password

# パスワード取得関数を完全にインライン化
def get_admin_password():
    """管理画面用のパスワードを取得する
    
    環境変数 > Streamlit secrets > デフォルトパスワード の順で探索
    """
    # 1. 環境変数から取得
    if 'ADMIN_PASSWORD' in os.environ:
        return os.environ['ADMIN_PASSWORD']
    
    # 2. Streamlit secretsから取得
    try:
        if 'admin_password' in st.secrets:
            return st.secrets['admin_password']
    except Exception:
        pass  # secretsがない場合は無視
    
    # 3. デフォルトパスワード
    return "golf_score_admin"

def calculate_game_pt(player_pt, other_pts):
    """ゲームポイントを計算する
    
    3人プレーの場合：自分のポイント×2 - 他のプレイヤーの合計
    4人プレーの場合：そのままのポイント
    """
    if len(other_pts) == 2:  # 3人プレー
        return player_pt * 2 - sum(other_pts)
    return player_pt  # 4人プレー

def check_password():
    """パスワードチェック機能"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        pwd = st.text_input("パスワードを入力してください", type="password")
        if pwd:
            # 管理者パスワードを取得
            admin_password = get_admin_password()
            if pwd == admin_password:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("パスワードが正しくありません")
        return False
    return True

def run():
    # タイトルとホームボタンを横に配置
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("管理画面")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")
    
    if not check_password():
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "スコア修正", 
        "ハンディキャップ修正", 
        "メンバー管理",
        "バックアップ・リストア"
    ])

    with tab1:
        show_score_editor()
    
    with tab2:
        show_handicap_editor()
    
    with tab3:
        show_member_manager()

    with tab4:
        show_backup_restore()

def recalculate_scores(round_id):
    """ラウンドのスコアを再計算する"""
    try:
        # ラウンドのスコアデータを取得
        scores = supabase.table('score').select('*').eq('round_id', round_id).execute().data
        
        # ハンディキャップデータを取得
        handicaps = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute().data
        
        # ハンディキャップをペアごとにマッピング
        handicap_map = {}
        total_only_pairs = set()
        for h in handicaps:
            handicap_map[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicap_map[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if h['total_only']:
                total_only_pairs.add(frozenset([h['player_1_id'], h['player_2_id']]))

        # スコアの計算
        for score in scores:
            front_total = score['front_score']
            back_total = score['back_score']
            extra_total = score['extra_score'] if score['extra_score'] is not None else 0
            
            # マッチポイントの初期化
            total_match_points = 0
            
            # 他のプレイヤーとの対戦結果を計算
            for opponent in scores:
                if score['member_id'] == opponent['member_id']:
                    continue
                
                pair = frozenset([score['member_id'], opponent['member_id']])
                is_total_only = pair in total_only_pairs
                
                # ハンディキャップを取得
                handicap = handicap_map.get((score['member_id'], opponent['member_id']), 0)
                
                # ネットスコアの計算
                net_front = front_total - (0 if is_total_only else handicap//2)
                net_back = back_total - (0 if is_total_only else (handicap - handicap//2))
                net_extra = extra_total - handicap if extra_total else 0
                
                opp_handicap = handicap_map.get((opponent['member_id'], score['member_id']), 0)
                opp_net_front = opponent['front_score'] - (0 if is_total_only else opp_handicap//2)
                opp_net_back = opponent['back_score'] - (0 if is_total_only else (opp_handicap - opp_handicap//2))
                opp_net_extra = opponent['extra_score'] - opp_handicap if opponent['extra_score'] else 0
                
                # マッチポイントの計算
                if not is_total_only:
                    # Front 9
                    if net_front < opp_net_front:
                        total_match_points += 5
                    elif net_front > opp_net_front:
                        total_match_points -= 5
                    
                    # Back 9
                    if net_back < opp_net_back:
                        total_match_points += 5
                    elif net_back > opp_net_back:
                        total_match_points -= 5
                
                # Total（必ず計算）
                net_total = (net_front + net_back) - handicap
                opp_net_total = (opp_net_front + opp_net_back) - opp_handicap
                if net_total < opp_net_total:
                    total_match_points += 10
                elif net_total > opp_net_total:
                    total_match_points -= 10
                
                # Extra holes（もしあれば）
                if extra_total is not None and opponent['extra_score'] is not None:
                    if net_extra < opp_net_extra:
                        total_match_points += 5
                    elif net_extra > opp_net_extra:
                        total_match_points -= 5
            
            # マッチポイントの更新
            supabase.table('score').update({
                'match_pt': total_match_points
            }).eq('score_id', score['score_id']).execute()

        # プレイヤー数を確認
        player_count = len(scores)
        
        # Game Ptの計算（手動入力された値を使用）
        # 3人プレイの場合は再計算が必要
        if player_count == 3:
            for score in scores:
                temp_gp = (score['front_game_pt'] or 0) + (score['back_game_pt'] or 0) + (score['extra_game_pt'] or 0)
                others_gp = [
                    (s['front_game_pt'] or 0) + (s['back_game_pt'] or 0) + (s['extra_game_pt'] or 0)
                    for s in scores if s['member_id'] != score['member_id']
                ]
                final_game_pt = calculate_game_pt(temp_gp, others_gp)
                
                # total_ptの計算（Game Pt + Match Pt + Putt Pt）
                total_pt = final_game_pt + score['match_pt'] + (score['put_pt'] or 0)
                
                # Game PtとTotal Ptの更新
                supabase.table('score').update({
                    'game_pt': final_game_pt,
                    'total_pt': total_pt
                }).eq('score_id', score['score_id']).execute()
        else:
            # 4人の場合は各セクションの合計をそのまま使用
            for score in scores:
                final_game_pt = (score['front_game_pt'] or 0) + (score['back_game_pt'] or 0) + (score['extra_game_pt'] or 0)
                
                # total_ptの計算（Game Pt + Match Pt + Putt Pt）
                total_pt = final_game_pt + score['match_pt'] + (score['put_pt'] or 0)
                
                # Game PtとTotal Ptの更新
                supabase.table('score').update({
                    'game_pt': final_game_pt,
                    'total_pt': total_pt
                }).eq('score_id', score['score_id']).execute()

    except Exception as e:
        raise Exception(f"スコアの再計算中にエラーが発生しました: {str(e)}")

def show_score_editor():
    st.subheader("スコア修正")
    
    # ラウンドデータの取得
    rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    rounds = rounds_result.data
    
    round_options = [
        f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})"
        for r in rounds
    ]
    
    selected_round = st.selectbox(
        "修正するラウンドを選択",
        options=round_options,
        index=0 if round_options else None
    )
    
    if selected_round:
        round_id = int(selected_round.split("ID: ")[1].rstrip(")"))
        round_data = next((r for r in rounds if r['round_id'] == round_id), None)
        
        # ラウンド削除機能
        with st.expander("⚠️ ラウンドの削除"):
            st.warning("このラウンドのデータをすべて削除します。この操作は取り消せません。")
            
            # 削除の確認チェックボックス
            confirm_delete = st.checkbox("このラウンドを削除することを確認しました")
            
            if st.button("ラウンドを削除", disabled=not confirm_delete, type="primary"):
                try:
                    # 関連データの削除（順序が重要）
                    # 1. ハンディキャップマッチデータの削除
                    supabase.table('handicap_match').delete().eq('round_id', round_id).execute()
                    
                    # 2. スコアデータの削除
                    supabase.table('score').delete().eq('round_id', round_id).execute()
                    
                    # 3. ラウンドデータの削除
                    supabase.table('rounds').delete().eq('round_id', round_id).execute()
                    
                    st.success(f"ラウンドID: {round_id} を削除しました")
                    st.rerun()  # 画面を再読み込み
                    
                except Exception as e:
                    st.error(f"ラウンドの削除中にエラーが発生しました: {str(e)}")
                    if hasattr(e, 'details'):
                        st.error(f"エラーの詳細: {e.details}")
        
        if round_data:
            # スコアデータの取得
            scores_result = supabase.table('score').select(
                '*, member(name)'
            ).eq('round_id', round_id).execute()
            scores = scores_result.data
            
            if scores:
                # スコア編集フォーム
                with st.form("score_edit_form"):
                    updated_scores = {}
                    
                    for score in scores:
                        st.write(f"### {score['member']['name']}")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            front_score = st.number_input(
                                "Front Score",
                                value=score['front_score'],
                                key=f"front_{score['score_id']}"
                            )
                            front_putt = st.number_input(
                                "Front Putt",
                                value=score['front_putt'] or 0,
                                key=f"front_putt_{score['score_id']}"
                            )
                        
                        with col2:
                            back_score = st.number_input(
                                "Back Score",
                                value=score['back_score'],
                                key=f"back_{score['score_id']}"
                            )
                            back_putt = st.number_input(
                                "Back Putt",
                                value=score['back_putt'] or 0,
                                key=f"back_putt_{score['score_id']}"
                            )
                        
                        with col3:
                            extra_score = st.number_input(
                                "Extra Score",
                                value=score['extra_score'] or 0,
                                key=f"extra_{score['score_id']}"
                            )
                            extra_putt = st.number_input(
                                "Extra Putt",
                                value=score['extra_putt'] or 0,
                                key=f"extra_putt_{score['score_id']}"
                            )
                        
                        with col4:
                            front_game_pt = st.number_input(
                                "Front Game Pt",
                                value=score['front_game_pt'] or 0,
                                key=f"front_game_{score['score_id']}"
                            )
                            back_game_pt = st.number_input(
                                "Back Game Pt",
                                value=score['back_game_pt'] or 0,
                                key=f"back_game_{score['score_id']}"
                            )
                            extra_game_pt = st.number_input(
                                "Extra Game Pt",
                                value=score['extra_game_pt'] or 0,
                                key=f"extra_game_{score['score_id']}"
                            )
                        
                        # 更新データの準備
                        updated_scores[score['score_id']] = {
                            'front_score': st.session_state[f"front_{score['score_id']}"],
                            'front_putt': st.session_state[f"front_putt_{score['score_id']}"],
                            'back_score': st.session_state[f"back_{score['score_id']}"],
                            'back_putt': st.session_state[f"back_putt_{score['score_id']}"],
                            'extra_score': st.session_state[f"extra_{score['score_id']}"],
                            'extra_putt': st.session_state[f"extra_putt_{score['score_id']}"],
                            'front_game_pt': st.session_state[f"front_game_{score['score_id']}"],
                            'back_game_pt': st.session_state[f"back_game_{score['score_id']}"],
                            'extra_game_pt': st.session_state[f"extra_game_{score['score_id']}"]
                        }
                    
                    if st.form_submit_button("スコアを更新"):
                        try:
                            for score_id, new_values in updated_scores.items():
                                supabase.table('score').update(new_values).eq('score_id', score_id).execute()
                            
                            if round_data['finalized']:
                                with st.spinner("スコアを再計算中..."):
                                    recalculate_scores(round_id)
                                
                            st.success("スコアを更新しました")
                            st.rerun()
                        except Exception as e:
                            st.error(f"更新中にエラーが発生しました: {str(e)}")
            else:
                st.warning("スコアデータが見つかりません")

def show_handicap_editor():
    st.subheader("ハンディキャップ修正")
    
    # ラウンドデータの取得
    rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    rounds = rounds_result.data
    
    round_options = [
        f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})"
        for r in rounds
    ]
    
    selected_round = st.selectbox(
        "修正するラウンドを選択",
        options=round_options,
        index=0 if round_options else None,
        key="handicap_round_select"
    )
    
    if selected_round:
        round_id = int(selected_round.split("ID: ")[1].rstrip(")"))
        
        # ハンディキャップデータの取得
        handicaps_result = supabase.table('handicap_match').select(
            '*, player1:member!player_1_id(name), player2:member!player_2_id(name)'
        ).eq('round_id', round_id).execute()
        handicaps = handicaps_result.data

        # メンバーデータの取得
        members_result = supabase.table('member').select('*').order('name').execute()
        members = members_result.data

        # 既存の重複データをクリーンアップするフォーム
        with st.form("cleanup_form"):
            st.write("### 重複データのクリーンアップ")
            if st.form_submit_button("重複データをクリーンアップ"):
                try:
                    seen_pairs = set()
                    to_delete = []
                    
                    # ハンディキャップデータを日付でソート
                    sorted_handicaps = sorted(handicaps, key=lambda x: x['id'], reverse=True)
                    
                    for h in sorted_handicaps:
                        pair = tuple(sorted([h['player_1_id'], h['player_2_id']]))
                        if pair in seen_pairs:
                            to_delete.append(h['id'])
                        else:
                            seen_pairs.add(pair)
                    
                    # 重複データの削除
                    if to_delete:
                        for handicap_id in to_delete:
                            supabase.table('handicap_match').delete().eq('id', handicap_id).execute()
                    
                    st.success("重複データを削除しました")
                    st.rerun()
                except Exception as e:
                    st.error(f"クリーンアップ中にエラーが発生しました: {str(e)}")

        # 既存のハンディキャップ表示
        if handicaps:
            st.write("### 現在のハンディキャップ設定")
            handicap_df = pd.DataFrame([
                {
                    'プレーヤー1': h['player1']['name'],
                    'プレーヤー2': h['player2']['name'],
                    'P1→P2': h['player_1_to_2'],
                    'P2→P1': h['player_2_to_1'],
                    'Total Only': 'はい' if h['total_only'] else 'いいえ'
                }
                for h in handicaps
            ])
            st.dataframe(handicap_df)

        # 新規ハンディキャップ設定の追加フォーム
        with st.form(f"add_handicap_form_{round_id}"):
            st.write("### 新規ハンディキャップ設定の追加")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                player1 = st.selectbox(
                    "プレーヤー1",
                    options=[(m['member_id'], m['name']) for m in members],
                    format_func=lambda x: x[1]
                )
            with col2:
                player2 = st.selectbox(
                    "プレーヤー2",
                    options=[(m['member_id'], m['name']) for m in members],
                    format_func=lambda x: x[1]
                )
            with col3:
                p1_to_2 = st.number_input("P1→P2ハンディ", value=0)
                p2_to_1 = st.number_input("P2→P1ハンディ", value=0)
            with col4:
                total_only = st.checkbox("Total Only")
            
            if st.form_submit_button("ハンディキャップ設定を追加"):
                if player1[0] != player2[0]:
                    try:
                        supabase.table('handicap_match').insert({
                            'round_id': round_id,
                            'player_1_id': player1[0],
                            'player_2_id': player2[0],
                            'player_1_to_2': p1_to_2,
                            'player_2_to_1': p2_to_1,
                            'total_only': total_only
                        }).execute()
                        st.success("ハンディキャップ設定を追加しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"追加中にエラーが発生しました: {str(e)}")
                else:
                    st.error("同じプレーヤーは選択できません")

def show_member_manager():
    st.subheader("メンバー管理")
    
    # メンバーデータの取得 (ID昇順)
    members_result = supabase.table('member').select('*').order('member_id').execute()
    members = members_result.data
    
    if members:
        with st.form("edit_members_form"):
            st.write("### 登録済みメンバー")
            updated_members = {}
            
            for member in members:
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_name = st.text_input(
                        "名前",
                        value=member['name'],
                        key=f"name_{member['member_id']}"
                    )
                    updated_members[member['member_id']] = new_name
                
                with col2:
                    if st.checkbox("削除", key=f"delete_{member['member_id']}"):
                        st.session_state[f"delete_{member['member_id']}_confirmed"] = True
            
            # フォーム送信ボタン
            if st.form_submit_button("変更を保存"):
                try:
                    # メンバーの更新と削除
                    for member_id, new_name in updated_members.items():
                        if st.session_state.get(f"delete_{member_id}_confirmed"):
                            # メンバーの削除前に関連データをチェック
                            scores = supabase.table('score').select('*').eq('member_id', member_id).execute()
                            if scores.data:
                                st.error(f"メンバー '{new_name}' はスコアデータが存在するため削除できません")
                                continue
                            
                            handicaps = supabase.table('handicap_match').select('*').or_(
                                f'player_1_id.eq.{member_id},player_2_id.eq.{member_id}'
                            ).execute()
                            if handicaps.data:
                                st.error(f"メンバー '{new_name}' はハンディキャップデータが存在するため削除できません")
                                continue
                            
                            # 関連データがなければ削除実行
                            supabase.table('member').delete().eq('member_id', member_id).execute()
                            st.success(f"メンバー '{new_name}' を削除しました")
                        else:
                            # 名前が変更されている場合のみ更新
                            if new_name != next((m['name'] for m in members if m['member_id'] == member_id), None):
                                supabase.table('member').update({'name': new_name}).eq('member_id', member_id).execute()
                                st.success(f"メンバー名を '{new_name}' に更新しました")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"メンバー情報の更新中にエラーが発生しました: {str(e)}")
    
    # 新規メンバー追加フォーム
    with st.form("add_member_form"):
        st.write("### 新規メンバー追加")
        new_name = st.text_input("名前")
        
        # フォーム送信ボタン
        submit = st.form_submit_button("追加")
        if submit:
            if new_name:
                try:
                    # 同じ名前のメンバーが既に存在するかチェック
                    existing = supabase.table('member').select('*').eq('name', new_name).execute()
                    if existing.data:
                        st.error(f"メンバー「{new_name}」は既に登録されています")
                    else:
                        # 最大のmember_idを取得して、新しいIDを作成
                        max_id_result = supabase.table('member').select('member_id').order('member_id', desc=True).limit(1).execute()
                        next_id = 1
                        if max_id_result.data:
                            next_id = max_id_result.data[0]['member_id'] + 1
                        
                        # member_idを明示的に指定して挿入
                        supabase.table('member').insert({
                            'member_id': next_id,
                            'name': new_name
                        }).execute()
                        
                        st.success(f"メンバー「{new_name}」を追加しました (ID: {next_id})")
                        st.rerun()
                except Exception as e:
                    st.error(f"メンバーの追加に失敗しました: {str(e)}")
            else:
                st.warning("名前を入力してください")

def show_backup_restore():
    """バックアップ・リストア機能のUI（Supabase版）"""
    st.subheader("データバックアップ・リストア")

    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### バックアップ作成")
        st.caption("※ 最新5件まで保存されます")
        with st.form("backup_form"):
            if st.form_submit_button("バックアップを作成"):
                try:
                    with st.spinner("バックアップを作成中..."):
                        # 全テーブルのデータを取得
                        rounds = supabase.table('rounds').select('*').execute().data
                        scores = supabase.table('score').select('*').execute().data
                        members = supabase.table('member').select('*').execute().data
                        handicaps = supabase.table('handicap_match').select('*').execute().data

                        backup_data = {
                            'rounds': rounds,
                            'scores': scores,
                            'members': members,
                            'handicap_matches': handicaps
                        }

                        # バックアップの保存
                        backup_id = save_backup_to_supabase(backup_data)
                        st.success(f"バックアップを作成しました: {backup_id}")
                except Exception as e:
                    st.error(f"バックアップ作成中にエラーが発生しました: {str(e)}")

    with col2:
        st.write("### バックアップからリストア")
        try:
            backups = get_backups_from_supabase()
            if backups:
                # タイムスタンプをJSTに変換して表示
                jst = pytz.timezone('Asia/Tokyo')
                backup_options = []
                for b in backups:
                    utc_time = datetime.datetime.fromisoformat(b['created_at'].replace('Z', '+00:00'))
                    jst_time = utc_time.astimezone(jst)
                    backup_options.append({
                        'id': b['backup_id'],
                        'created_at': jst_time.strftime('%Y-%m-%d %H:%M')
                    })
                
                with st.form("restore_form"):
                    selected_backup = st.selectbox(
                        "リストアするバックアップを選択",
                        options=backup_options,
                        format_func=lambda x: f"{x['id']} ({x['created_at']})"
                    )

                    st.warning("⚠️ この操作は取り消せません")
                    
                    if st.form_submit_button("リストアを実行"):
                        try:
                            with st.spinner("リストア中..."):
                                result = supabase.table('backups').select('*').eq('backup_id', selected_backup['id']).execute()
                                
                                if not result.data:
                                    raise ValueError("バックアップが見つかりません")
                                    
                                backup_data = result.data[0]['data']
                                
                                # 既存のデータを依存関係の逆順で削除
                                st.write("既存のデータを削除中...")
                                supabase.table('handicap_match').delete().neq('id', -1).execute()
                                supabase.table('score').delete().neq('score_id', -1).execute()
                                supabase.table('rounds').delete().neq('round_id', -1).execute()
                                supabase.table('member').delete().neq('member_id', -1).execute()
                                
                                # データの復元
                                st.write("データを復元中...")
                                if backup_data.get('members'):
                                    st.write("メンバーデータを復元中...")
                                    supabase.table('member').insert(backup_data['members']).execute()
                                
                                if backup_data.get('rounds'):
                                    st.write("ラウンドデータを復元中...")
                                    rounds_to_insert = []
                                    for round_data in backup_data['rounds']:
                                        player_count = len([
                                            s for s in backup_data['scores'] 
                                            if s['round_id'] == round_data['round_id']
                                        ])
                                        
                                        round_to_insert = {
                                            'round_id': round_data['round_id'],
                                            'date': round_data['date_played'],
                                            'date_played': round_data['date_played'],
                                            'course_name': round_data['course_name'],
                                            'num_players': player_count,
                                            'has_extra': round_data.get('has_extra', False),
                                            'finalized': round_data.get('finalized', False)
                                        }
                                        rounds_to_insert.append(round_to_insert)
                                    
                                    if rounds_to_insert:
                                        supabase.table('rounds').insert(rounds_to_insert).execute()
                                
                                if backup_data.get('scores'):
                                    st.write("スコアデータを復元中...")
                                    rounds_result = supabase.table('rounds').select('round_id').execute()
                                    valid_round_ids = {r['round_id'] for r in rounds_result.data}
                                    
                                    valid_scores = [
                                        score for score in backup_data['scores']
                                        if score['round_id'] in valid_round_ids
                                    ]
                                    
                                    if valid_scores:
                                        supabase.table('score').insert(valid_scores).execute()
                                
                                if backup_data.get('handicap_matches'):
                                    st.write("ハンディキャップデータを復元中...")
                                    members_result = supabase.table('member').select('member_id').execute()
                                    valid_member_ids = {m['member_id'] for m in members_result.data}
                                    
                                    valid_handicaps = [
                                        h for h in backup_data['handicap_matches']
                                        if h['round_id'] in valid_round_ids and
                                        h['player_1_id'] in valid_member_ids and
                                        h['player_2_id'] in valid_member_ids
                                    ]
                                    
                                    if valid_handicaps:
                                        supabase.table('handicap_match').insert(valid_handicaps).execute()
                                
                                st.success("リストアが完了しました。ページをリロードします...")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"リストア中にエラーが発生しました: {str(e)}")
                            if hasattr(e, 'details'):
                                st.error(f"エラーの詳細: {e.details}")
            else:
                st.info("バックアップが見つかりません")
        except Exception as e:
            st.error(f"バックアップ一覧の取得に失敗しました: {str(e)}")

def save_backup_to_supabase(backup_data):
    """バックアップデータをSupabaseに保存（最新5件まで）"""
    try:
        # 既存のバックアップを取得
        existing_backups = supabase.table('backups').select('*').order('created_at.desc').execute()
        
        # 5件以上ある場合、古いものを削除
        if len(existing_backups.data) >= 5:
            # 古い順にソート
            sorted_backups = sorted(existing_backups.data, key=lambda x: x['created_at'])
            # 超過分を削除
            for old_backup in sorted_backups[:(len(existing_backups.data) - 4)]:
                supabase.table('backups').delete().eq('backup_id', old_backup['backup_id']).execute()

        # 新しいバックアップを保存
        jst = pytz.timezone('Asia/Tokyo')
        now = datetime.datetime.now(jst)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        
        supabase.table('backups').insert({
            'backup_id': timestamp,
            'data': backup_data,
            'created_at': now.isoformat(),
            'description': f"Backup {timestamp}"
        }).execute()
        
        return timestamp
    except Exception as e:
        raise Exception(f"Supabaseへの保存に失敗しました: {str(e)}")

def get_backups_from_supabase():
    """Supabaseからバックアップ一覧を取得"""
    result = supabase.table('backups').select('*').order('created_at.desc').execute()
    return result.data

if __name__ == "__main__":
    run()