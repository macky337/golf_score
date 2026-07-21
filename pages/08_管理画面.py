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
import logging
from dotenv import load_dotenv
from modules.input_helpers import close_sidebar_on_mobile
from modules.backup_restore import restore_backup_atomic
from modules.auth import require_login
from modules.round_calculation import recalculate_round
from modules.round_validation import validate_round
from modules.competition_rules import get_default_rules, save_default_rules

logger = logging.getLogger(__name__)

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
    
# from modules.page_utils import switch_page  # 未使用のため削除

# パスワード取得関数を完全にインライン化
def get_admin_password():
    """管理画面用のパスワードを取得する

    環境変数 > Streamlit secrets の順で探索する。
    未設定時は管理機能を無効化し、既定パスワードにはフォールバックしない。
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
    
    return None

def check_password():
    """パスワードチェック機能"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        admin_password = get_admin_password()
        if not admin_password:
            st.error("管理者パスワードが設定されていないため、管理機能は無効です。")
            st.info("Railway Variables または Streamlit secrets に ADMIN_PASSWORD を設定してください。")
            return False

        pwd = st.text_input("パスワードを入力してください", type="password")
        if pwd:
            if pwd == admin_password:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("パスワードが正しくありません")
        return False
    return True

def run():
    require_login()

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
    
    st.caption("日常的な修正は「スコア・ハンディキャップ」、復元・削除・診断は「データ保守」から行えます。")
    admin_menu = st.selectbox(
        "管理メニュー",
        (
            "📝 スコア修正",
            "⚖️ ハンディキャップ修正",
            "🎯 競技ルール設定",
            "👤 メンバー管理",
            "🛡️ データ保守・危険操作",
        ),
        key="admin_menu",
    )

    if admin_menu == "📝 スコア修正":
        score_edit_tab()
    elif admin_menu == "⚖️ ハンディキャップ修正":
        show_handicap_editor()
    elif admin_menu == "🎯 競技ルール設定":
        show_competition_rule_settings()
    elif admin_menu == "👤 メンバー管理":
        show_member_manager()
    else:
        show_data_maintenance()

def recalculate_single_round(round_id):
    """通常画面と同じロジックで単一ラウンドを再計算する。"""
    try:
        recalculate_round(ensure_supabase(), round_id)
        return True
    except Exception as e:
        raise Exception(f"ラウンド{round_id}の再計算に失敗: {str(e)}")

def recalculate_after_handicap_change(supabase, round_id):
    """ハンデ変更後に結果を再計算し、確定済みなら整合性も確認する。"""
    recalculate_round(supabase, round_id)
    round_response = (
        supabase.table("rounds").select("finalized").eq("round_id", round_id).execute()
    )
    if round_response.data and round_response.data[0].get("finalized"):
        errors = validate_round(supabase, round_id, require_results=True)
        if errors:
            raise ValueError("／".join(errors))

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
        selected_round_data = next(r for r in rounds if r['round_id'] == round_id)
        status = "確定済み（変更後に再計算）" if selected_round_data.get('finalized') else "未確定"
        st.info(f"**管理対象**：{selected_round}　／　{status}")
        # ハンディキャップデータの取得
        handicaps_result = supabase.table('handicap_match').select(
            '*, player1:member!player_1_id(name), player2:member!player_2_id(name)'
        ).eq('round_id', round_id).execute()
        handicaps = handicaps_result.data

        # メンバーデータの取得
        members_result = supabase.table('member').select('*').order('name').execute()
        members = members_result.data

        # 重複データの修復は通常編集から目立たない位置へ分離
        with st.expander("詳細：重複ハンディキャップを整理する"):
            st.caption("同じプレーヤー組み合わせの重複登録を整理します。通常は実行不要です。")
            with st.form("cleanup_form"):
                if st.form_submit_button("重複データをクリーンアップ"):
                    try:
                        seen_pairs = set()
                        to_delete = []
                        sorted_handicaps = sorted(handicaps, key=lambda x: x['id'], reverse=True)
                        for h in sorted_handicaps:
                            pair = tuple(sorted([h['player_1_id'], h['player_2_id']]))
                            if pair in seen_pairs:
                                to_delete.append(h['id'])
                            else:
                                seen_pairs.add(pair)
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
                        st.caption("方向ごとに入力します。Total Only を有効にするとOUT/IN別の対戦計算を行いません。")
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
                                    recalculate_after_handicap_change(supabase, round_id)
                                    st.success("ハンディキャップを更新し、結果を再計算しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"更新エラー: {str(e)}")
                        
                        with col_delete:
                            if st.form_submit_button("削除", use_container_width=True):
                                try:
                                    supabase.table('handicap_match').delete().eq('id', h['id']).execute()
                                    recalculate_after_handicap_change(supabase, round_id)
                                    st.success("ハンディキャップを削除し、結果を再計算しました")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"削除エラー: {str(e)}")
        else:
            st.info("このラウンドにはハンディキャップ設定がありません。")

        # 新規ハンディキャップ設定の追加フォーム
        with st.form(f"add_handicap_form_{round_id}"):
            st.write("### 新規ハンディキャップ設定の追加")
            st.caption("プレーヤーの組み合わせを選び、方向ごとのハンディキャップを入力します。")
            col1, col2 = st.columns(2)
            
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
            p1_to_2 = st.number_input("プレーヤー1 → プレーヤー2 ハンディ", value=0)
            p2_to_1 = st.number_input("プレーヤー2 → プレーヤー1 ハンディ", value=0)
            total_only = st.checkbox("Total Only（OUT/IN別の対戦計算を行わない）")
            
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
                            recalculate_after_handicap_change(supabase, round_id)
                            st.success("ハンディキャップ設定を追加し、結果を再計算しました")
                            st.rerun()
                    except Exception as e:
                        st.error(f"追加中にエラーが発生しました: {str(e)}")
                        # デバッグ情報を表示
                        with st.expander("エラー詳細"):
                            st.code(str(e))
                else:
                    st.error("同じプレーヤーは選択できません")

def show_competition_rule_settings():
    """新規ラウンドへ適用する標準の競技ルールを編集する。"""
    st.subheader("競技ルール設定")
    st.info(
        "ここで保存したルールは、次に作成する新規ラウンドから適用されます。"
        "作成済みラウンドの配点は変更されません。"
    )
    st.caption("ログイン情報やDB接続情報はこの画面では変更できません。")
    supabase = ensure_supabase()
    rules = get_default_rules(supabase)

    with st.form("competition_rule_settings_form"):
        st.markdown("### マッチ対戦")
        match_win_points = st.number_input(
            "1勝あたりのポイント",
            min_value=1,
            max_value=100,
            value=rules["match_win_points"],
            step=1,
        )

        st.markdown("### パット戦（3人）")
        putt_3_solo_winner = st.number_input("単独勝者", value=rules["putt_3_solo_winner"], step=1)
        putt_3_solo_loser = st.number_input("単独勝者時・その他", value=rules["putt_3_solo_loser"], step=1)
        putt_3_two_winners = st.number_input("2人同率勝者・各人", value=rules["putt_3_two_winners"], step=1)
        putt_3_two_losers = st.number_input("2人同率勝者時・その他", value=rules["putt_3_two_losers"], step=1)

        st.markdown("### パット戦（4人）")
        putt_4_solo_winner = st.number_input("単独勝者（4人）", value=rules["putt_4_solo_winner"], step=1)
        putt_4_solo_loser = st.number_input("単独勝者時・その他（4人）", value=rules["putt_4_solo_loser"], step=1)
        putt_4_two_winners = st.number_input("2人同率勝者・各人（4人）", value=rules["putt_4_two_winners"], step=1)
        putt_4_two_losers = st.number_input("2人同率勝者時・その他（4人）", value=rules["putt_4_two_losers"], step=1)
        putt_4_three_winners = st.number_input("3人同率勝者・各人", value=rules["putt_4_three_winners"], step=1)
        putt_4_three_losers = st.number_input("3人同率勝者時・その他", value=rules["putt_4_three_losers"], step=1)

        st.markdown("### ゲームポイント")
        st.caption(
            "ゲームポイントは各入力画面で手動入力する値のため、標準配点の変更対象には含めません。"
        )

        if st.form_submit_button("標準ルールを保存", type="primary", use_container_width=True):
            updated = {
                **rules,
                "match_win_points": match_win_points,
                "putt_3_solo_winner": putt_3_solo_winner,
                "putt_3_solo_loser": putt_3_solo_loser,
                "putt_3_two_winners": putt_3_two_winners,
                "putt_3_two_losers": putt_3_two_losers,
                "putt_4_solo_winner": putt_4_solo_winner,
                "putt_4_solo_loser": putt_4_solo_loser,
                "putt_4_two_winners": putt_4_two_winners,
                "putt_4_two_losers": putt_4_two_losers,
                "putt_4_three_winners": putt_4_three_winners,
                "putt_4_three_losers": putt_4_three_losers,
            }
            balance_checks = (
                putt_3_solo_winner + 2 * putt_3_solo_loser,
                2 * putt_3_two_winners + putt_3_two_losers,
                putt_4_solo_winner + 3 * putt_4_solo_loser,
                2 * putt_4_two_winners + 2 * putt_4_two_losers,
                3 * putt_4_three_winners + putt_4_three_losers,
            )
            if any(total != 0 for total in balance_checks):
                st.error("各配点パターンの合計が0になるように設定してください。")
            else:
                try:
                    save_default_rules(supabase, updated)
                    st.success("標準ルールを保存しました。次の新規ラウンドから適用されます。")
                except Exception as error:
                    logger.exception("競技ルール設定の保存に失敗しました")
                    st.error(
                        "保存できませんでした。先にSupabaseで "
                        "sql/add_competition_rules.sql を実行してください。"
                    )


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

def show_data_maintenance():
    """復元・診断・削除を通常の編集画面から分離する。"""
    st.subheader("データ保守・危険操作")
    st.warning("ここではデータ全体に影響する操作を扱います。通常のスコア修正は「スコア修正」から行ってください。")
    maintenance_menu = st.selectbox(
        "操作を選択",
        ("📦 バックアップ・リストア", "🔎 ポイントバランス診断", "⚠️ ラウンド削除"),
        key="admin_maintenance_menu",
    )
    if maintenance_menu == "📦 バックアップ・リストア":
        show_backup_restore()
    elif maintenance_menu == "🔎 ポイントバランス診断":
        show_balance_diagnostics()
    else:
        show_round_delete()


def show_round_delete():
    """削除対象とバックアップを明示したラウンド削除画面。"""
    st.subheader("ラウンド削除")
    st.error("この操作はラウンド、スコア、ハンディキャップ、計算結果を削除します。削除前に自動バックアップを作成します。")
    supabase = ensure_supabase()
    rounds = supabase.table('rounds').select('round_id', 'date_played', 'course_name', 'finalized').order('date_played', desc=True).execute().data
    if not rounds:
        st.info("削除できるラウンドはありません。")
        return

    selected = st.selectbox(
        "削除するラウンド",
        rounds,
        format_func=lambda r: f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})",
        key="delete_round_selection",
    )
    round_id = selected['round_id']
    status = "確定済み" if selected.get('finalized') else "未確定"
    st.caption(f"対象：{selected['date_played']} / {selected['course_name']} / ID: {round_id} / {status}")
    confirmation = st.text_input(f"確認のためラウンドID「{round_id}」を入力してください", key="confirm_delete_round")
    if st.button(
        "バックアップを作成して削除する",
        disabled=confirmation != str(round_id),
        type="primary",
        use_container_width=True,
        key="delete_round_button",
    ):
        try:
            with st.spinner("削除前バックアップを作成中..."):
                backup_id = create_backup_snapshot(supabase)
            supabase.table('round_results').delete().eq('round_id', round_id).execute()
            supabase.table('handicap_match').delete().eq('round_id', round_id).execute()
            supabase.table('score').delete().eq('round_id', round_id).execute()
            supabase.table('rounds').delete().eq('round_id', round_id).execute()
            st.success(f"ラウンドID: {round_id} を削除しました。削除前バックアップ: {backup_id}")
            st.rerun()
        except Exception as e:
            logger.exception("ラウンドの削除に失敗しました")
            st.error(f"ラウンドの削除中にエラーが発生しました: {str(e)}")


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
                        backup_id = create_backup_snapshot(supabase)
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
                    restore_confirmation = st.text_input(
                        "確認のため RESTORE と入力してください"
                    )

                    if st.form_submit_button("リストアを実行"):
                        try:
                            if restore_confirmation != "RESTORE":
                                st.error("確認文字が一致しません")
                                st.stop()

                            with st.spinner("リストア中..."):
                                # Supabaseクライアントを取得
                                supabase = ensure_supabase()
                                
                                result = supabase.table('backups').select('*').eq('backup_id', selected_backup['id']).execute()
                                
                                if not result.data:
                                    raise ValueError("バックアップが見つかりません")
                                    
                                backup_data = result.data[0]['data']

                                # PostgreSQL側の単一トランザクションで削除・復元する
                                restore_backup_atomic(supabase, backup_data)
                                
                                st.success("リストアが完了しました。ページをリロードします...")
                                time.sleep(1)
                                st.rerun()
                        except Exception:
                            logger.exception("バックアップの復元に失敗しました")
                            st.error("リストアに失敗しました。データは変更されていません。")
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


def create_backup_snapshot(supabase):
    """破壊的操作の直前にも使える、全データのバックアップを作成する。"""
    try:
        app_settings = supabase.table('app_settings').select('*').execute().data
    except Exception:
        app_settings = []
    backup_data = {
        'rounds': supabase.table('rounds').select('*').execute().data,
        'scores': supabase.table('score').select('*').execute().data,
        'members': supabase.table('member').select('*').execute().data,
        'handicap_matches': supabase.table('handicap_match').select('*').execute().data,
        'round_results': supabase.table('round_results').select('*').execute().data,
        'app_settings': app_settings,
    }
    return save_backup_to_supabase(backup_data)

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
        
        status = "確定済み（保存後に結果を再計算）" if is_finalized else "未確定（結果確認画面で確定できます）"
        st.info(f"**管理対象**：{round_name}　／　{status}")
    
    scores = sorted(scores_result.data, key=lambda s: s.get('member_id', 0))
    
    # スコア編集用フォーム
    with st.form("score_edit_form"):
        edited_scores = {}
        
        st.caption("各プレーヤーを開いて入力してください。ゲームポイントはスコア・パットとは別に保存されます。")
        for i, score in enumerate(scores):
            player_name = score['member']['name'] if score.get('member') else f"Player {score['member_id']}"
            with st.expander(f"{player_name} のスコア", expanded=(i == 0)):
                member_id = score['member_id']
                edited_scores[member_id] = {"id": member_id}
                st.markdown("##### フロント（OUT）")
                front_score_col, front_putt_col = st.columns(2)
                with front_score_col:
                    edited_scores[member_id]["front_score"] = st.number_input(
                        "スコア（OUT）",
                        min_value=0, 
                        max_value=100, 
                        value=score.get('front_score', 0) or 0,
                        key=f"front_score_{member_id}"
                    )
                with front_putt_col:
                    edited_scores[member_id]["front_putt"] = st.number_input(
                        "パット（OUT）",
                        min_value=0, 
                        max_value=50,
                        value=score.get('front_putt', 0) or 0,
                        key=f"front_putt_{member_id}"
                    )
                edited_scores[member_id]["front_game_pt"] = st.number_input(
                        "ゲームポイント（OUT）",
                        min_value=-300,
                        max_value=300,
                        value=score.get('front_game_pt', 0) or 0,
                        key=f"front_game_pt_{member_id}"
                    )
                st.markdown("##### バック（IN）")
                back_score_col, back_putt_col = st.columns(2)
                with back_score_col:
                    edited_scores[member_id]["back_score"] = st.number_input(
                        "スコア（IN）",
                        min_value=0, 
                        max_value=100, 
                        value=score.get('back_score', 0) or 0,
                        key=f"back_score_{member_id}"
                    )
                with back_putt_col:
                    edited_scores[member_id]["back_putt"] = st.number_input(
                        "パット（IN）",
                        min_value=0, 
                        max_value=50, 
                        value=score.get('back_putt', 0) or 0,
                        key=f"back_putt_{member_id}"
                    )
                edited_scores[member_id]["back_game_pt"] = st.number_input(
                        "ゲームポイント（IN）",
                        min_value=-300,
                        max_value=300,
                        value=score.get('back_game_pt', 0) or 0,
                        key=f"back_game_pt_{member_id}"
                    )
                if has_extra:
                    st.markdown("##### エキストラ")
                    extra_score_col, extra_putt_col = st.columns(2)
                    with extra_score_col:
                        edited_scores[member_id]["extra_score"] = st.number_input(
                            "スコア（エキストラ）",
                            min_value=0, 
                            max_value=100, 
                            value=score.get('extra_score', 0) or 0,
                            key=f"extra_score_{member_id}"
                        )
                    with extra_putt_col:
                        edited_scores[member_id]["extra_putt"] = st.number_input(
                            "パット（エキストラ）",
                            min_value=0, 
                            max_value=50, 
                            value=score.get('extra_putt', 0) or 0,
                            key=f"extra_putt_{member_id}"
                        )
                    edited_scores[member_id]["extra_game_pt"] = st.number_input(
                        "ゲームポイント（エキストラ）",
                        min_value=-300,
                        max_value=300,
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
            
            if failure_count == 0 and success_count == len(edited_scores):
                st.success(f"{success_count}人のプレイヤーのスコアを更新しました。")
                # 全員分の保存成功後だけ、共通ロジックで再計算する
                try:
                    recalculate_round(supabase, round_id)
                    if is_finalized:
                        validation_errors = validate_round(
                            supabase, round_id, require_results=True
                        )
                        if validation_errors:
                            raise ValueError("／".join(validation_errors))
                    st.success("ラウンド結果の再計算と保存が完了しました。")
                except Exception as e:
                    logger.exception("ラウンド結果の再計算に失敗しました")
                    st.error(f"ラウンド結果の再計算中にエラーが発生しました: {str(e)}")
            else:
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
                'date': round_data.get('date_played', '不明'),
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
            confirm_recalculate = st.checkbox(
                "全ラウンドを再計算することを確認しました",
                key="confirm_recalculate_all_rounds",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "🔄 全ラウンド再計算",
                    help="すべてのラウンドのポイントを再計算します",
                    disabled=not confirm_recalculate,
                    use_container_width=True,
                ):
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
                show_details = st.checkbox(
                    "📋 詳細レポートを表示",
                    key="show_balance_details",
                    help="問題のあるラウンドの詳細を表示します",
                )
                if show_details:
                    show_detailed_balance_report(round_details)
        else:
            st.success("ポイントバランスは正常です！")
            
    except Exception as e:
        logger.exception("ポイントバランスの診断に失敗しました")
        st.error(f"診断中にエラーが発生しました: {str(e)}")

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
                # 診断元と同じround_resultsから詳細を取得する
                results = supabase.table('round_results').select(
                    'member_id, match_pt, putt_pt, total_game_pt, member:member_id(name)'
                ).eq('round_id', round_info['round_id']).execute().data or []
                for result in results:
                    member = result.get('member') or {}
                    result['name'] = member.get('name', f"Member {result['member_id']}")
                    result['total_pt'] = (
                        (result.get('match_pt') or 0)
                        + (result.get('putt_pt') or 0)
                        + (result.get('total_game_pt') or 0)
                    )

                # データフレームで表示
                df = pd.DataFrame(results)
                if not df.empty:
                    # 合計行を追加
                    totals = {
                        'name': '合計',
                        'member_id': '',
                        'match_pt': df['match_pt'].sum(),
                        'putt_pt': df['putt_pt'].sum(),
                        'total_game_pt': df['total_game_pt'].sum(),
                        'total_pt': df['total_pt'].sum()
                    }
                    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)

                    st.dataframe(df[['name', 'match_pt', 'putt_pt', 'total_game_pt', 'total_pt']],
                               use_container_width=True)

                if st.button(
                    "このラウンドだけ再計算する",
                    key=f"repair_{round_info['round_id']}",
                    use_container_width=True,
                ):
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
