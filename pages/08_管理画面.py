import streamlit as st
# サイドバーを常時表示
st.set_page_config(
    page_title="管理画面 - Golf Score App",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import sys
import os
import datetime
import json
import pytz
import time
from dotenv import load_dotenv
from modules.input_helpers import close_sidebar_on_mobile

# モジュールのインポートパスを追加（確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# パスが存在することを確認
if os.path.exists(parent_dir) and parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# モジュールディレクトリも直接追加
modules_path = os.path.join(parent_dir, 'modules')
if os.path.exists(modules_path) and modules_path not in sys.path:
    sys.path.insert(0, modules_path)

try:
    from modules.db import get_supabase, ensure_supabase
    from modules.models import *
    from modules.game_points import calculate_game_pt
    from modules.calculation_logic import calculate_player_points
    from modules.round_results import save_round_results, get_round_results
    import_success = True
    # Supabaseクライアントを取得
    supabase = get_supabase()
    if not supabase:
        supabase = ensure_supabase()
except ImportError as e:
    st.error(f"モジュールのインポートエラー: {e}")
    import_success = False
    # エラー時の代替処理用
    supabase = None
    # 代替のensure_supabase関数を定義
    def ensure_supabase():
        from modules.supabase_client import get_supabase_client
        client = get_supabase_client()
        if not client:
            st.error("⚠️ データベース接続エラー")
            st.stop()
        return client
    
    # 代替の関数を定義
    def calculate_player_points(*args, **kwargs):
        st.error("calculation_logicモジュールが利用できません")
        return {}, {}, {}, {}
    
    def save_round_results(*args, **kwargs):
        st.error("round_resultsモジュールが利用できません")
        return False
    
    def get_round_results(*args, **kwargs):
        st.error("round_resultsモジュールが利用できません")
        return {}

# from modules.page_utils import switch_page  # 未使用のため削除

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
    # スマホでサイドバーを自動的に閉じる
    close_sidebar_on_mobile()
    
    # タイトルとホームボタンを横に配置
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("管理画面")
    with col2:
        if st.button("🏠 Home"):
            st.switch_page("main.py")
    
    if not check_password():
        return
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "スコア修正", 
        "ハンディキャップ修正", 
        "メンバー管理",
        "バックアップ・リストア",
        "ポイントバランス診断"
    ])

    with tab1:
        score_edit_tab()
    
    with tab2:
        show_handicap_editor()
    
    with tab3:
        show_member_manager()

    with tab4:
        show_backup_restore()
    
    with tab5:
        show_balance_diagnostics()

def recalculate_single_round(round_id):
    """単一ラウンドの再計算（エキストラスコア診断用）"""
    try:
        # 既存のrecalculate_scores関数を使用
        recalculate_scores(round_id)
        return True
    except Exception as e:
        raise Exception(f"ラウンド{round_id}の再計算に失敗: {str(e)}")

def recalculate_scores(round_id):
    """ラウンドのスコアを再計算する"""
    try:
        # Supabaseクライアントを取得
        supabase = ensure_supabase()
        if not supabase:
            raise Exception("Supabaseクライアントが初期化できません")
        
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
                
                # total_ptとgame_ptはround_resultsテーブルで管理されるため、ここでは更新しない
                # scoreテーブルにはfront_game_pt, back_game_pt, extra_game_ptのみ保存
        else:
            # 4人の場合は各セクションの合計をそのまま使用
            # 4人の場合も、game_ptとtotal_ptはround_resultsテーブルで管理されるため、
            # scoreテーブルには保存しない
            pass

    except Exception as e:
        raise Exception(f"スコアの再計算中にエラーが発生しました: {str(e)}")

def show_score_editor():
    st.subheader("スコア修正")
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
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
                    # 1. round_resultsテーブルからデータを削除（これが追加部分）
                    supabase.table('round_results').delete().eq('round_id', round_id).execute()
                    
                    # 2. ハンディキャップマッチデータの削除
                    supabase.table('handicap_match').delete().eq('round_id', round_id).execute()
                    
                    # 3. スコアデータの削除
                    supabase.table('score').delete().eq('round_id', round_id).execute()
                    
                    # 4. ラウンドデータの削除
                    supabase.table('rounds').delete().eq('round_id', round_id).execute()
                    
                    st.success(f"ラウンドID: {round_id} を削除しました")
                    st.rerun()  # 画面を再読み込み
                    
                except Exception as e:
                    st.error(f"ラウンドの削除中にエラーが発生しました: {str(e)}")
                    # 詳細なエラー情報を表示（安全な方法）
                    import traceback
                    st.error(f"エラーの詳細: {traceback.format_exc()}")
        
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
                            for record_id, new_values in updated_scores.items():
                                supabase.table('score').update(new_values).eq('score_id', record_id).execute()
                            
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
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
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

        # 既存のハンディキャップ表示と編集
        if handicaps:
            st.write("### 現在のハンディキャップ設定")
            
            # 各ハンディキャップの編集フォーム
            for idx, h in enumerate(handicaps):
                with st.expander(f"📝 {h['player1']['name']} vs {h['player2']['name']}"):
                    with st.form(f"edit_handicap_form_{h['id']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**プレーヤー1:** {h['player1']['name']}")
                            st.write(f"**プレーヤー2:** {h['player2']['name']}")
                        
                        with col2:
                            new_p1_to_2 = st.number_input(
                                f"{h['player1']['name']} → {h['player2']['name']} ハンディ",
                                value=h['player_1_to_2'],
                                min_value=-50,
                                max_value=50,
                                key=f"edit_p1_to_2_{h['id']}"
                            )
                            new_p2_to_1 = st.number_input(
                                f"{h['player2']['name']} → {h['player1']['name']} ハンディ",
                                value=h['player_2_to_1'],
                                min_value=-50,
                                max_value=50,
                                key=f"edit_p2_to_1_{h['id']}"
                            )
                        
                        with col3:
                            new_total_only = st.checkbox(
                                "Total Only",
                                value=h['total_only'],
                                key=f"edit_total_only_{h['id']}"
                            )
                        
                        col_update, col_delete = st.columns(2)
                        
                        with col_update:
                            if st.form_submit_button("更新", type="primary", use_container_width=True):
                                try:
                                    supabase.table('handicap_match').update({
                                        'player_1_to_2': new_p1_to_2,
                                        'player_2_to_1': new_p2_to_1,
                                        'total_only': new_total_only
                                    }).eq('id', h['id']).execute()
                                    st.success("ハンディキャップを更新しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"更新エラー: {str(e)}")
                        
                        with col_delete:
                            if st.form_submit_button("削除", use_container_width=True):
                                try:
                                    supabase.table('handicap_match').delete().eq('id', h['id']).execute()
                                    st.success("ハンディキャップを削除しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"削除エラー: {str(e)}")
        else:
            st.info("このラウンドにはハンディキャップ設定がありません。")

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
                        # 既存のハンディキャップ設定を確認
                        existing = supabase.table('handicap_match').select('*').eq('round_id', round_id).eq('player_1_id', player1[0]).eq('player_2_id', player2[0]).execute()
                        
                        if existing.data:
                            st.warning("この組み合わせのハンディキャップ設定は既に存在します。既存の設定を編集してください。")
                        else:
                            # 最大のIDを取得して次のIDを決定
                            max_id_result = supabase.table('handicap_match').select('id').order('id', desc=True).limit(1).execute()
                            next_id = 1
                            if max_id_result.data:
                                next_id = max_id_result.data[0]['id'] + 1
                            
                            # 新規追加（idを明示的に指定）
                            insert_data = {
                                'id': next_id,
                                'round_id': round_id,
                                'player_1_id': player1[0],
                                'player_2_id': player2[0],
                                'player_1_to_2': p1_to_2,
                                'player_2_to_1': p2_to_1,
                                'total_only': total_only
                            }
                            result = supabase.table('handicap_match').insert(insert_data).execute()
                            st.success("ハンディキャップ設定を追加しました")
                            st.rerun()
                    except Exception as e:
                        st.error(f"追加中にエラーが発生しました: {str(e)}")
                        # デバッグ情報を表示
                        with st.expander("エラー詳細"):
                            st.code(str(e))
                else:
                    st.error("同じプレーヤーは選択できません")

def show_member_manager():
    st.subheader("メンバー管理")
    
    # Supabaseクライアントを取得
    supabase = ensure_supabase()
    
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
                        # Supabaseクライアントを取得
                        supabase = ensure_supabase()
                        
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
                                # Supabaseクライアントを取得
                                supabase = ensure_supabase()
                                
                                result = supabase.table('backups').select('*').eq('backup_id', selected_backup['id']).execute()
                                
                                if not result.data:
                                    raise ValueError("バックアップが見つかりません")
                                    
                                backup_data = result.data[0]['data']
                                
                                # 既存のデータを依存関係の逆順で削除
                                st.write("既存のデータを削除中...")
                                supabase.table('handicap_match').delete().neq('id', -1).execute()
                                supabase.table('score').delete().neq('id', -1).execute()
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
                                else:
                                    # スコアデータがない場合も空のvalid_round_idsを定義
                                    rounds_result = supabase.table('rounds').select('round_id').execute()
                                    valid_round_ids = {r['round_id'] for r in rounds_result.data}
                                
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
                            # 詳細なエラー情報を表示（安全な方法）
                            import traceback
                            st.error(f"エラーの詳細: {traceback.format_exc()}")
            else:
                st.info("バックアップが見つかりません")
        except Exception as e:
            st.error(f"バックアップ一覧の取得に失敗しました: {str(e)}")

def save_backup_to_supabase(backup_data):
    """バックアップデータをSupabaseに保存（最新5件まで）"""
    supabase = ensure_supabase()
    
    try:
        # 既存のバックアップを取得
        existing_backups = supabase.table('backups').select('*').order('created_at', desc=True).execute()
        
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
    supabase = ensure_supabase()
    result = supabase.table('backups').select('*').order('created_at', desc=True).execute()
    return result.data

def score_edit_tab():
    """スコア修正タブの表示と処理"""
    st.header("スコア修正")
    
    # ラウンド選択
    supabase = ensure_supabase()
    rounds_result = supabase.table('rounds').select('round_id', 'date_played', 'course_name').order('date_played', desc=True).execute()
    
    if not rounds_result.data:
        st.warning("ラウンドデータがありません。")
        return
    
    # セッションから事前選択されたラウンドIDを取得（結果確認画面から遷移した場合）
    preselected_round_id = st.session_state.get("admin_selected_round_id", None)
    default_index = 0
    
    round_options = []
    for i, r in enumerate(rounds_result.data):
        round_options.append((r['round_id'], f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})"))
        if r['round_id'] == preselected_round_id:
            default_index = i
    
    selected_round = st.selectbox(
        "修正するラウンドを選択", 
        options=round_options,
        format_func=lambda x: x[1],
        index=default_index
    )
    
    if not selected_round:
        st.info("ラウンドを選択してください。")
        return
    
    round_id, round_name = selected_round
    
    # ここにラウンド削除機能を追加
    with st.expander("⚠️ ラウンドの削除"):
        st.warning("このラウンドのデータをすべて削除します。この操作は取り消せません。")
        
        # 削除の確認チェックボックス
        confirm_delete = st.checkbox("このラウンドを削除することを確認しました", key="confirm_delete_round")
        
        if st.button("ラウンドを削除", disabled=not confirm_delete, type="primary", key="delete_round_button"):
            try:
                # 関連データの削除（順序が重要）
                # 1. round_resultsテーブルからデータを削除
                supabase.table('round_results').delete().eq('round_id', round_id).execute()
                
                # 2. ハンディキャップマッチデータの削除
                supabase.table('handicap_match').delete().eq('round_id', round_id).execute()
                
                # 3. スコアデータの削除
                supabase.table('score').delete().eq('round_id', round_id).execute()
                
                # 4. ラウンドデータの削除
                supabase.table('rounds').delete().eq('round_id', round_id).execute()
                
                st.success(f"ラウンドID: {round_id} を削除しました")
                st.rerun()  # 画面を再読み込み
                
            except Exception as e:
                st.error(f"ラウンドの削除中にエラーが発生しました: {str(e)}")
                # 詳細なエラー情報を表示（安全な方法）
                import traceback
                st.error(f"エラーの詳細: {traceback.format_exc()}")
    
    # 選択されたラウンドのスコア情報を取得
    scores_result = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    
    if not scores_result.data:
        st.warning("選択されたラウンドにスコアデータがありません。")
        return
    
    # ラウンド情報を取得（確定状態の表示用）
    round_info = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    
    # 変数の初期化
    is_finalized = False
    has_extra = False
    
    if round_info.data:
        is_finalized = round_info.data[0].get('finalized', False)
        has_extra = round_info.data[0].get('has_extra', False)
        
        if is_finalized:
            st.success("このラウンドは確定済みです。スコア修正後、自動的に結果が再計算されます。")
        else:
            st.warning("このラウンドはまだ確定されていません。結果確認画面から確定できます。")
    
    scores = sorted(scores_result.data, key=lambda s: s.get('member_id', 0))
    
    # スコア編集用フォーム
    with st.form("score_edit_form"):
        edited_scores = {}
        
        # プレイヤーごとのタブを作成
        player_tabs = st.tabs([s['member']['name'] if s.get('member') else f"Player {s['member_id']}" for s in scores])
        
        for i, (tab, score) in enumerate(zip(player_tabs, scores)):
            with tab:
                member_id = score['member_id']
                edited_scores[member_id] = {"id": member_id}
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("フロント")
                    edited_scores[member_id]["front_score"] = st.number_input(
                        "フロントスコア", 
                        min_value=0, 
                        max_value=100, 
                        value=score.get('front_score', 0) or 0,
                        key=f"front_score_{member_id}"
                    )
                    edited_scores[member_id]["front_putt"] = st.number_input(
                        "フロントパット", 
                        min_value=0, 
                        max_value=50,
                        value=score.get('front_putt', 0) or 0,
                        key=f"front_putt_{member_id}"
                    )
                    edited_scores[member_id]["front_game_pt"] = st.number_input(
                        "フロントゲームポイント", 
                        min_value=-100, 
                        max_value=100, 
                        value=score.get('front_game_pt', 0) or 0,
                        key=f"front_game_pt_{member_id}"
                    )
                
                with col2:
                    st.subheader("バック")
                    edited_scores[member_id]["back_score"] = st.number_input(
                        "バックスコア", 
                        min_value=0, 
                        max_value=100, 
                        value=score.get('back_score', 0) or 0,
                        key=f"back_score_{member_id}"
                    )
                    edited_scores[member_id]["back_putt"] = st.number_input(
                        "バックパット", 
                        min_value=0, 
                        max_value=50, 
                        value=score.get('back_putt', 0) or 0,
                        key=f"back_putt_{member_id}"
                    )
                    edited_scores[member_id]["back_game_pt"] = st.number_input(
                        "バックゲームポイント", 
                        min_value=-100, 
                        max_value=100, 
                        value=score.get('back_game_pt', 0) or 0,
                        key=f"back_game_pt_{member_id}"
                    )
                
                if has_extra:
                    with col3:
                        st.subheader("エキストラ")
                        edited_scores[member_id]["extra_score"] = st.number_input(
                            "エキストラスコア", 
                            min_value=0, 
                            max_value=100, 
                            value=score.get('extra_score', 0) or 0,
                            key=f"extra_score_{member_id}"
                        )
                        edited_scores[member_id]["extra_putt"] = st.number_input(
                            "エキストラパット",
                            min_value=0, 
                            max_value=50, 
                            value=score.get('extra_putt', 0) or 0,
                            key=f"extra_putt_{member_id}"
                        )
                        edited_scores[member_id]["extra_game_pt"] = st.number_input(
                            "エキストラゲームポイント", 
                            min_value=-100, 
                            max_value=100, 
                            value=score.get('extra_game_pt', 0) or 0,
                            key=f"extra_game_pt_{member_id}"
                        )
        
        submit = st.form_submit_button("スコアを保存して再計算する", use_container_width=True, type="primary")
        
        if submit:
            success_count = 0
            failure_count = 0            # 各プレイヤーのスコアを更新
            for member_id, data in edited_scores.items():
                try:
                    # 明示的に更新するフィールドのみを指定
                    update_data = {
                        'front_score': data.get("front_score", 0),
                        'front_putt': data.get("front_putt", 0),
                        'front_game_pt': data.get("front_game_pt", 0),
                        'back_score': data.get("back_score", 0),
                        'back_putt': data.get("back_putt", 0),
                        'back_game_pt': data.get("back_game_pt", 0),
                        'total_score': data.get("front_score", 0) + data.get("back_score", 0)
                    }
                    
                    # エキストラデータがある場合のみ追加
                    if has_extra:
                        update_data.update({
                            'extra_score': data.get("extra_score", 0),
                            'extra_putt': data.get("extra_putt", 0),
                            'extra_game_pt': data.get("extra_game_pt", 0)
                        })
                    
                    # score IDを取得するためのクエリ
                    record_result = supabase.table('score').select('score_id').eq('round_id', round_id).eq('member_id', member_id).execute()
                    if record_result.data:
                        record_id = record_result.data[0]['score_id']
                        
                        # スコアを更新
                        supabase.table('score').update(update_data).eq('score_id', record_id).execute()
                        success_count += 1
                    else:
                        st.error(f"プレイヤーID {member_id} のスコアレコードが見つかりません。")
                        failure_count += 1
                except Exception as e:
                    st.error(f"プレイヤーID {member_id} のスコア更新エラー: {str(e)}")
                    failure_count += 1
            
            if success_count > 0:
                st.success(f"{success_count}人のプレイヤーのスコアを更新しました。")
                  # スコア更新後、ラウンド結果を再計算
                try:
                    # 最新のスコアデータを取得
                    updated_scores = supabase.table('score').select('*').eq('round_id', round_id).execute().data
                    
                    # ハンディキャップ情報を取得
                    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                    handicaps_data = handicaps_result.data or []
                    
                    # ラウンド情報を取得
                    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
                    active_round = round_result.data[0] if round_result.data else {}
                    
                    # 現在のラウンド結果を取得
                    round_results = get_round_results(round_id)
                    if isinstance(round_results, list):
                        round_results = {item.get('member_id'): item for item in round_results if item.get('member_id') is not None}
                    
                    # プレイヤーデータの初期化
                    from modules.data_formatter import initialize_player_data
                    player_data = initialize_player_data(updated_scores, round_results)
                    player_ids = sorted(list(player_data.keys()))
                    
                    # ハンディキャップマップを作成
                    handicaps = {}
                    total_only_set = set()
                    for h in handicaps_data:
                        handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                        handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                        if 'total_only' in h and h['total_only']:
                            total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
                    
                    # ポイント再計算
                    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
                    
                    # 計算結果をDBに保存
                    save_success = save_round_results(round_id, updated_player_data)
                    
                    if save_success:
                        st.success("ラウンド結果の再計算と保存が完了しました。")
                        
                        # Score テーブルにゲームポイントを更新
                        for mid in player_ids:
                            data = updated_player_data[mid]
                            score_update = {
                                'front_game_pt': data.get('Front GP', 0),
                                'back_game_pt': data.get('Back GP', 0),
                                'extra_game_pt': data.get('Extra GP', 0) if has_extra else 0
                            }
                            # score IDを取得して更新
                            record_result = supabase.table('score').select('score_id').eq('round_id', round_id).eq('member_id', mid).execute()
                            if record_result.data:
                                record_id = record_result.data[0]['score_id']
                                supabase.table('score').update(score_update).eq('score_id', record_id).execute()
                    else:
                        st.error("ラウンド結果の保存に失敗しました。")
                except Exception as e:
                    st.error(f"ラウンド結果の再計算中にエラーが発生しました: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
            
            if failure_count > 0:
                st.warning(f"{failure_count}人のプレイヤーのスコア更新に失敗しました。")
    
    # フォーム外に配置する結果確認画面への遷移ボタン
    st.markdown("---")
    if st.button("結果確認画面へ移動", use_container_width=True):
        st.session_state.active_round_id = round_id
        st.switch_page("pages/05_結果確認.py")

def show_balance_diagnostics():
    """ポイントバランス診断と修復機能"""
    st.header("ポイントバランス診断")
    
    # 現在のポイントバランスを確認
    supabase = ensure_supabase()
    
    try:        
        # 全ラウンドの合計ポイントを計算
        all_rounds = supabase.table('rounds').select('*').execute().data
        total_balance = 0
        round_details = []
        
        for round_data in all_rounds:
            round_id = round_data['round_id']
            # このラウンドの全プレイヤーのTotal Ptを合計（round_resultsテーブルから計算）
            round_results = supabase.table('round_results').select('match_pt, putt_pt, total_game_pt, member_id').eq('round_id', round_id).execute().data
            
            # total_ptカラムが存在しないため、計算で算出
            round_total = 0
            for result in round_results:
                match_pt = result.get('match_pt', 0) or 0
                putt_pt = result.get('putt_pt', 0) or 0
                total_game_pt = result.get('total_game_pt', 0) or 0
                total_pt = match_pt + putt_pt + total_game_pt
                round_total += total_pt
            
            total_balance += round_total
            
            round_details.append({
                'round_id': round_id,
                'date': round_data.get('round_date', '不明'),
                'course': round_data.get('course_name', '不明'),
                'round_total': round_total,
                'player_count': len(round_results)
            })
        
        # 診断結果を表示
        st.subheader("📊 ポイントバランス診断結果")
        
        # バランス状況の表示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総ポイント合計", f"{total_balance:+d}")
        with col2:
            status = "✅ 正常" if total_balance == 0 else "⚠️ 不均衡"
            st.metric("バランス状況", status)
        with col3:
            st.metric("対象ラウンド数", len(all_rounds))
        
        # 詳細データの表示
        if st.checkbox("ラウンド別詳細を表示", value=False):
            df = pd.DataFrame(round_details)
            if not df.empty:
                df = df.sort_values('date', ascending=False)
                st.dataframe(df, use_container_width=True)
        
        # 修復オプション
        st.subheader("🔧 修復オプション")
        
        if total_balance != 0:
            st.warning(f"ポイントバランスが {total_balance:+d} の不均衡があります。")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 全ラウンド再計算", help="すべてのラウンドのポイントを再計算します"):
                    with st.spinner("再計算中..."):
                        repair_count = 0
                        for round_data in all_rounds:
                            try:
                                recalculate_single_round(round_data['round_id'])
                                repair_count += 1
                            except Exception as e:
                                st.error(f"ラウンド{round_data['round_id']}の再計算に失敗: {str(e)}")
                        
                        st.success(f"{repair_count}ラウンドの再計算が完了しました。")
                        st.rerun()
            
            with col2:
                if st.button("📋 詳細レポート", help="問題のあるラウンドの詳細を表示します"):
                    show_detailed_balance_report(round_details)
        else:
            st.success("ポイントバランスは正常です！")
            
    except Exception as e:
        st.error(f"診断中にエラーが発生しました: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def recalculate_single_round_v2(round_id):
    """単一ラウンドのポイントを再計算する（別実装）"""
    supabase = ensure_supabase()
    
    try:
        # ラウンドのスコアデータを取得
        scores = supabase.table('score').select('*').eq('round_id', round_id).execute().data
        
        if not scores:
            raise Exception(f"ラウンド{round_id}のスコアデータが見つかりません")
        
        # ハンディキャップデータを取得
        handicaps = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute().data
        
        # ハンディキャップをペアごとにマッピング
        handicap_map = {}
        for hc in handicaps:
            key = tuple(sorted([hc['member_id_1'], hc['member_id_2']]))
            handicap_map[key] = hc['handicap_difference']
        
        # 各プレイヤーのポイントを再計算
        updated_scores = []
        player_ids = [score['member_id'] for score in scores]
        
        for score in scores:
            member_id = score['member_id']
            
            # ゲームポイントを計算
            front_gp, back_gp, extra_gp, total_pt = calculate_player_points(
                round_id, member_id, player_ids, handicap_map, active_round={'round_id': round_id}
            )
            
            # スコアを更新（total_ptはround_resultsで管理）
            update_data = {
                'front_game_pt': front_gp,
                'back_game_pt': back_gp,
                'extra_game_pt': extra_gp
            }
            
            supabase.table('score').update(update_data).eq('score_id', score['score_id']).execute()
            updated_scores.append({**score, **update_data})
        
        # ラウンド結果も更新
        save_round_results(round_id, updated_scores)
        
        return True
        
    except Exception as e:
        raise Exception(f"ラウンド{round_id}の再計算に失敗: {str(e)}")

def show_detailed_balance_report(round_details):
    """詳細なバランスレポートを表示"""
    st.subheader("📋 詳細バランスレポート")
    
    # 不均衡のあるラウンドをフィルタ
    problematic_rounds = [r for r in round_details if r['round_total'] != 0]
    
    if problematic_rounds:
        st.warning(f"{len(problematic_rounds)}個のラウンドで不均衡が検出されました")
        
        supabase = ensure_supabase()
        
        for round_info in problematic_rounds:
            with st.expander(f"ラウンド {round_info['round_id']} - {round_info['date']} ({round_info['round_total']:+d}pt)"):
                # このラウンドの詳細スコアを取得
                scores = supabase.table('score').select(
                    'member_id, front_game_pt, back_game_pt, extra_game_pt, total_pt'
                ).eq('round_id', round_info['round_id']).execute().data
                
                # メンバー名も取得
                for score in scores:
                    member = supabase.table('member').select('name').eq('member_id', score['member_id']).execute()
                    score['name'] = member.data[0]['name'] if member.data else f"Member {score['member_id']}"
                
                # データフレームで表示
                df = pd.DataFrame(scores)
                if not df.empty:
                    # 合計行を追加
                    totals = {
                        'name': '合計',
                        'member_id': '',
                        'front_game_pt': df['front_game_pt'].sum(),
                        'back_game_pt': df['back_game_pt'].sum(),
                        'extra_game_pt': df['extra_game_pt'].sum(),
                        'total_pt': df['total_pt'].sum()
                    }
                    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
                    
                    st.dataframe(df[['name', 'front_game_pt', 'back_game_pt', 'extra_game_pt', 'total_pt']], 
                               use_container_width=True)
                
                # 個別修復ボタン                if st.button(f"このラウンドを修復", key=f"repair_{round_info['round_id']}"):
                    try:
                        recalculate_single_round(round_info['round_id'])
                        st.success(f"ラウンド {round_info['round_id']} の修復が完了しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"修復に失敗: {str(e)}")
    else:
        st.info("すべてのラウンドが正常なバランスです")

if __name__ == "__main__":
    run()