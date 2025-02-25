import streamlit as st
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
from sqlalchemy import func
import datetime
import hashlib
from streamlit_extras.switch_page_button import switch_page
import json
import os
import pytz
from dotenv import load_dotenv

# Supabase関連の関数を条件付きでインポート
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("Supabaseライブラリがインストールされていません。'pip install supabase'を実行してください。")

# パスワード認証の設定
def check_password():
    """パスワードチェック機能"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        pwd = st.text_input("パスワードを入力してください", type="password")
        if pwd:
            if pwd == "admin":  # 実際の運用では、ハッシュ化したパスワードを使用することを推奨
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("パスワードが違います")
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
        
    session = SessionLocal()
    tab1, tab2, tab3, tab4 = st.tabs([
        "スコア修正", 
        "ハンディキャップ修正", 
        "メンバー管理",
        "バックアップ・リストア"
    ])

    with tab1:
        show_score_editor(session)
    
    with tab2:
        show_handicap_editor(session)
    
    with tab3:
        show_member_manager(session)

    with tab4:
        show_backup_restore(session)

    session.close()

def recalculate_scores(session, round_id):
    """スコアの再計算を行う"""
    # ラウンドに関連する全データを取得
    round_data = session.query(Round).filter_by(round_id=round_id).first()
    scores = session.query(Score).filter_by(round_id=round_id).all()
    handicap_matches = session.query(HandicapMatch).filter_by(round_id=round_id).all()

    # ハンディキャップ情報の整理
    handicaps = {}
    total_only_pairs = []
    for match in handicap_matches:
        handicaps[(match.player_1_id, match.player_2_id)] = match.player_1_to_2
        handicaps[(match.player_2_id, match.player_1_id)] = match.player_2_to_1
        if match.total_only:
            total_only_pairs.append((match.player_1_id, match.player_2_id))
    
    total_only_set = {frozenset(pair) for pair in total_only_pairs}

    # プレーヤーデータの準備
    player_data = {}
    for score in scores:
        # ここで各スコアの計算処理を実装
        # （既存の計算ロジックを移植）
        pass  # 実際の計算ロジックをここに実装

    # 計算結果をDBに保存
    for score in scores:
        if score.member_id in player_data:
            data = player_data[score.member_id]
            score.match_front = data.get("Match Front", 0)
            score.match_back = data.get("Match Back", 0)
            score.match_total = data.get("Match Total", 0)
            score.match_extra = data.get("Match Extra", 0)
            score.match_pt = data.get("Match Pt", 0)
            score.put_pt = data.get("Put Pt", 0)
            score.total_pt = data.get("Total Pt", 0)

    session.commit()

def show_score_editor(session):
    st.subheader("スコア修正")
    
    rounds = session.query(Round).order_by(Round.date_played.desc()).all()
    round_options = [
        f"{r.date_played.strftime('%Y-%m-%d')} - {r.course_name} (ID: {r.round_id})"
        for r in rounds
    ]
    
    selected_round = st.selectbox(
        "修正するラウンドを選択",
        options=round_options,
        index=0 if round_options else None
    )
    
    if selected_round:
        round_id = int(selected_round.split("ID: ")[1].rstrip(")"))
        round_data = session.query(Round).filter_by(round_id=round_id).first()
        
        if round_data:
            # ラウンド基本設定の修正フォーム
            with st.form("round_settings_form"):
                st.write("### ラウンド設定")
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_course_name = st.text_input("コース名", value=round_data.course_name)
                with col2:
                    new_date = st.date_input("プレー日", value=round_data.date_played)
                with col3:
                    new_has_extra = st.checkbox("Extraホールあり", value=round_data.has_extra)
                
                if st.form_submit_button("ラウンド設定を更新"):
                    try:
                        round_data.course_name = new_course_name
                        round_data.date_played = new_date
                        round_data.has_extra = new_has_extra
                        session.commit()
                        st.success("ラウンド設定を更新しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新中にエラーが発生しました: {str(e)}")

            # スコアとパット数の修正フォーム
            scores = session.query(Score).filter_by(round_id=round_id).all()
            with st.form("score_edit_form"):
                st.write("### スコア修正")
                if round_data.finalized:
                    st.warning("このラウンドは確定済みです。修正すると再計算されます。")
                
                updated_scores = {}
                for score in scores:
                    st.write(f"#### {score.member.name}")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("Front 9")
                        front = st.number_input(
                            "Score",
                            value=score.front_score,
                            key=f"front_{score.score_id}"
                        )
                        front_putt = st.number_input(
                            "Putt",
                            value=score.front_putt or 0,
                            key=f"fputt_{score.score_id}"
                        )
                        front_game = st.number_input(
                            "Game Pt",
                            value=score.front_game_pt if hasattr(score, "front_game_pt") else 0,
                            key=f"fgame_{score.score_id}"
                        )
                    
                    with col2:
                        st.write("Back 9")
                        back = st.number_input(
                            "Score",
                            value=score.back_score,
                            key=f"back_{score.score_id}"
                        )
                        back_putt = st.number_input(
                            "Putt",
                            value=score.back_putt or 0,
                            key=f"bputt_{score.score_id}"
                        )
                        back_game = st.number_input(
                            "Game Pt",
                            value=score.back_game_pt if hasattr(score, "back_game_pt") else 0,
                            key=f"bgame_{score.score_id}"
                        )
                    
                    with col3:
                        if round_data.has_extra:
                            st.write("Extra")
                            extra = st.number_input(
                                "Score",
                                value=score.extra_score or 0,
                                key=f"extra_{score.score_id}"
                            )
                            extra_putt = st.number_input(
                                "Putt",
                                value=score.extra_putt or 0,
                                key=f"eputt_{score.score_id}"
                            )
                            extra_game = st.number_input(
                                "Game Pt",
                                value=score.extra_game_pt if hasattr(score, "extra_game_pt") else 0,
                                key=f"egame_{score.score_id}"
                            )
                        else:
                            extra = 0
                            extra_putt = 0
                            extra_game = 0
                    
                    updated_scores[score.score_id] = {
                        "front_score": front,
                        "back_score": back,
                        "extra_score": extra,
                        "front_putt": front_putt,
                        "back_putt": back_putt,
                        "extra_putt": extra_putt,
                        "front_game_pt": front_game,
                        "back_game_pt": back_game,
                        "extra_game_pt": extra_game,
                    }
                
                if st.form_submit_button("スコアを更新"):
                    try:
                        for score_id, new_values in updated_scores.items():
                            score = session.query(Score).get(score_id)
                            for key, value in new_values.items():
                                setattr(score, key, value)
                        
                        # スコアの再計算（finalized=Trueの場合）
                        if round_data.finalized:
                            recalculate_scores(session, round_id)
                            
                        session.commit()
                        st.success("スコアを更新しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新中にエラーが発生しました: {str(e)}")

            # ハンディキャップ設定の表示を修正
            if selected_round:
                # サブクエリを使用して最新のハンディキャップ設定のみを取得
                latest_handicaps_subq = (
                    session.query(
                        HandicapMatch.player_1_id,
                        HandicapMatch.player_2_id,
                        func.max(HandicapMatch.id).label('latest_id')
                    )
                    .filter_by(round_id=round_id)
                    .group_by(HandicapMatch.player_1_id, HandicapMatch.player_2_id)
                    .subquery()
                )

                # 最新のハンディキャップ設定を取得
                handicaps = (
                    session.query(HandicapMatch)
                    .join(
                        latest_handicaps_subq,
                        HandicapMatch.id == latest_handicaps_subq.c.latest_id
                    )
                    .all()
                )

                if handicaps:
                    st.write("### 現在のハンディキャップ設定")
                    st.write("※ 修正は「ハンディキャップ修正」タブで行ってください")
                    
                    for handicap in handicaps:
                        st.write(
                            f"- {handicap.player_1.name} vs {handicap.player_2.name}: "
                            f"({handicap.player_1.name}→{handicap.player_2.name}: {handicap.player_1_to_2}, "
                            f"{handicap.player_2.name}→{handicap.player_1.name}: {handicap.player_2_to_1}) "
                            f"{'[Total Only]' if handicap.total_only else ''}"
                        )

def show_handicap_editor(session):
    st.subheader("ハンディキャップ修正")
    
    rounds = session.query(Round).order_by(Round.date_played.desc()).all()
    round_options = [
        f"{r.date_played.strftime('%Y-%m-%d')} - {r.course_name} (ID: {r.round_id})"
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
        
        # サブクエリを使用して最新のハンディキャップ設定のみを取得
        latest_handicaps_subq = (
            session.query(
                HandicapMatch.player_1_id,
                HandicapMatch.player_2_id,
                func.max(HandicapMatch.id).label('latest_id')
            )
            .filter_by(round_id=round_id)
            .group_by(HandicapMatch.player_1_id, HandicapMatch.player_2_id)
            .subquery()
        )

        # 最新のハンディキャップ設定を取得
        handicaps = (
            session.query(HandicapMatch)
            .join(
                latest_handicaps_subq,
                HandicapMatch.id == latest_handicaps_subq.c.latest_id
            )
            .all()
        )

        members = session.query(Member).order_by(Member.name).all()

        # 既存の重複データをクリーンアップ
        if st.button("重複データをクリーンアップ"):
            try:
                # 各プレーヤーペアで最新のレコードのみを残し、他を削除
                seen_pairs = set()
                to_delete = []
                all_handicaps = session.query(HandicapMatch).filter_by(round_id=round_id).order_by(HandicapMatch.id.desc()).all()
                
                for h in all_handicaps:
                    pair = tuple(sorted([h.player_1_id, h.player_2_id]))
                    if pair in seen_pairs:
                        to_delete.append(h)
                    else:
                        seen_pairs.add(pair)
                
                for h in to_delete:
                    session.delete(h)
                
                session.commit()
                st.success("重複データを削除しました")
                st.rerun()
            except Exception as e:
                st.error(f"クリーンアップ中にエラーが発生しました: {str(e)}")

        # 新規ハンディキャップ設定の追加フォーム
        with st.form(f"add_handicap_form_{round_id}"):  # キーにround_idを追加
            st.write("### 新規ハンディキャップ設定の追加")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                player1 = st.selectbox("プレーヤー1", options=[(m.member_id, m.name) for m in members], format_func=lambda x: x[1])
            with col2:
                player2 = st.selectbox("プレーヤー2", options=[(m.member_id, m.name) for m in members], format_func=lambda x: x[1])
            with col3:
                p1_to_2 = st.number_input("P1→P2ハンディ", value=0)
                p2_to_1 = st.number_input("P2→P1ハンディ", value=0)
            with col4:
                total_only = st.checkbox("Total Only")
            
            if st.form_submit_button("ハンディキャップ設定を追加"):
                if player1[0] != player2[0]:
                    try:
                        new_handicap = HandicapMatch(
                            round_id=round_id,
                            player_1_id=player1[0],
                            player_2_id=player2[0],
                            player_1_to_2=p1_to_2,
                            player_2_to_1=p2_to_1,
                            total_only=total_only
                        )
                        session.add(new_handicap)
                        session.commit()
                        st.success("ハンディキャップ設定を追加しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"追加中にエラーが発生しました: {str(e)}")
                else:
                    st.error("同じプレーヤーは選択できません")

        # 既存のハンディキャップ設定の修正フォーム
        if handicaps:
            with st.form(f"handicap_edit_form_{round_id}"):  # キーにround_idを追加
                st.write("### ハンディキャップ設定の修正")
                updated_handicaps = {}
                delete_handicaps = set()
                
                for handicap in handicaps:
                    col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
                    with col1:
                        st.write(f"#### {handicap.player_1.name} vs {handicap.player_2.name}")
                        p1_to_2 = st.number_input(
                            f"{handicap.player_1.name}→{handicap.player_2.name}",
                            value=handicap.player_1_to_2,
                            key=f"p1to2_{handicap.id}"
                        )
                    with col2:
                        p2_to_1 = st.number_input(
                            f"{handicap.player_2.name}→{handicap.player_1.name}",
                            value=handicap.player_2_to_1,
                            key=f"p2to1_{handicap.id}"
                        )
                    with col3:
                        total_only = st.checkbox(
                            "Total Only",
                            value=handicap.total_only,
                            key=f"total_{handicap.id}"
                        )
                    with col4:
                        if st.checkbox("削除", key=f"delete_{handicap.id}"):
                            delete_handicaps.add(handicap.id)
                    
                    if handicap.id not in delete_handicaps:
                        updated_handicaps[handicap.id] = {
                            "player_1_to_2": p1_to_2,
                            "player_2_to_1": p2_to_1,
                            "total_only": total_only
                        }
                
                if st.form_submit_button("ハンディキャップ設定を更新"):
                    try:
                        # 削除対象の処理
                        for handicap_id in delete_handicaps:
                            handicap = session.query(HandicapMatch).get(handicap_id)
                            if handicap:
                                session.delete(handicap)
                        
                        # 更新対象の処理
                        for handicap_id, new_values in updated_handicaps.items():
                            handicap = session.query(HandicapMatch).get(handicap_id)
                            if handicap:
                                for key, value in new_values.items():
                                    setattr(handicap, key, value)
                        
                        session.commit()
                        st.success("ハンディキャップ設定を更新しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新中にエラーが発生しました: {str(e)}")

def show_member_manager(session):
    st.subheader("メンバー管理")
    
    # 既存メンバー一覧表示
    members = session.query(Member).order_by(Member.name).all()
    if members:
        st.write("### 登録済みメンバー")
        member_df = pd.DataFrame(
            [(m.member_id, m.name) for m in members],
            columns=["ID", "名前"]
        )
        st.dataframe(member_df)
    
    # 新規メンバー追加フォーム
    with st.form("add_member_form"):
        st.write("### 新規メンバー追加")
        new_name = st.text_input("名前")
        if st.form_submit_button("追加"):
            if new_name:
                try:
                    new_member = Member(name=new_name)
                    session.add(new_member)
                    session.commit()
                    st.success(f"メンバー「{new_name}」を追加しました")
                    st.rerun()
                except Exception as e:
                    st.error(f"追加中にエラーが発生しました: {str(e)}")
            else:
                st.warning("名前を入力してください")

def backup_database(session):
    """データベースのバックアップを作成"""
    backup_data = {
        'rounds': [],
        'scores': [],
        'members': [],
        'handicap_matches': []
    }

    # ラウンドデータのバックアップ
    rounds = session.query(Round).all()
    for r in rounds:
        backup_data['rounds'].append({
            'round_id': r.round_id,
            'date_played': r.date_played.isoformat(),
            'course_name': r.course_name,
            'has_extra': r.has_extra,
            'finalized': r.finalized
        })

    # スコアデータのバックアップ
    scores = session.query(Score).all()
    for s in scores:
        backup_data['scores'].append({
            'score_id': s.score_id,
            'round_id': s.round_id,
            'member_id': s.member_id,
            'front_score': s.front_score,
            'back_score': s.back_score,
            'extra_score': s.extra_score,
            'front_putt': s.front_putt,
            'back_putt': s.back_putt,
            'extra_putt': s.extra_putt
            # ...その他のスコア関連フィールド...
        })

    # メンバーデータのバックアップ
    members = session.query(Member).all()
    for m in members:
        backup_data['members'].append({
            'member_id': m.member_id,
            'name': m.name
        })

    # ハンディキャップデータのバックアップ
    handicaps = session.query(HandicapMatch).all()
    for h in handicaps:
        backup_data['handicap_matches'].append({
            'id': h.id,
            'round_id': h.round_id,
            'player_1_id': h.player_1_id,
            'player_2_id': h.player_2_id,
            'player_1_to_2': h.player_1_to_2,
            'player_2_to_1': h.player_2_to_1,
            'total_only': h.total_only
        })

    return backup_data

def save_backup(backup_data):
    """バックアップデータをJSONファイルとして保存"""
    # 日本のタイムゾーンを設定
    jst = pytz.timezone('Asia/Tokyo')
    timestamp = datetime.datetime.now(jst).strftime("%Y%m%d_%H%M%S")
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    filename = f"{backup_dir}/golf_score_backup_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    return filename

def restore_database(session, backup_data):
    """データベースをバックアップから復元"""
    try:
        # 既存のデータを全て削除
        session.query(Score).delete()
        session.query(HandicapMatch).delete()
        session.query(Round).delete()
        session.query(Member).delete()
        session.commit()

        # メンバーの復元
        for member_data in backup_data['members']:
            member = Member(
                member_id=member_data['member_id'],
                name=member_data['name']
            )
            session.add(member)
        session.commit()

        # ラウンドの復元
        for round_data in backup_data['rounds']:
            round = Round(
                round_id=round_data['round_id'],
                date_played=datetime.datetime.fromisoformat(round_data['date_played']).date(),
                course_name=round_data['course_name'],
                has_extra=round_data['has_extra'],
                finalized=round_data['finalized']
            )
            session.add(round)
        session.commit()

        # スコアの復元
        for score_data in backup_data['scores']:
            score = Score(
                score_id=score_data['score_id'],
                round_id=score_data['round_id'],
                member_id=score_data['member_id'],
                front_score=score_data['front_score'],
                back_score=score_data['back_score'],
                extra_score=score_data['extra_score'],
                front_putt=score_data['front_putt'],
                back_putt=score_data['back_putt'],
                extra_putt=score_data['extra_putt']
            )
            session.add(score)
        session.commit()

        # ハンディキャップの復元
        for handicap_data in backup_data['handicap_matches']:
            handicap = HandicapMatch(
                id=handicap_data['id'],
                round_id=handicap_data['round_id'],
                player_1_id=handicap_data['player_1_id'],
                player_2_id=handicap_data['player_2_id'],
                player_1_to_2=handicap_data['player_1_to_2'],
                player_2_to_1=handicap_data['player_2_to_1'],
                total_only=handicap_data['total_only']
            )
            session.add(handicap)
        session.commit()

        return True
    except Exception as e:
        st.error(f"リストア中にエラーが発生しました: {str(e)}")
        session.rollback()
        return False

def get_supabase_client():
    """Supabaseクライアントの取得（エラーハンドリング強化）"""
    if not SUPABASE_AVAILABLE:
        raise ImportError("Supabaseライブラリがインストールされていません")
    
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("環境変数 SUPABASE_URL または SUPABASE_KEY が設定されていません")
    
    try:
        return create_client(url, key)
    except Exception as e:
        raise ConnectionError(f"Supabaseへの接続に失敗しました: {str(e)}")

# バックアップ・リストア機能の修正版

def save_backup_to_supabase(backup_data):
    """バックアップデータをSupabaseに保存（最新5件まで）"""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.table('backups').insert({
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
    supabase = get_supabase_client()
    result = supabase.table('backups').select('*').order('created_at.desc').execute()
    return result.data

def restore_from_supabase(session, backup_id):
    """Supabaseのバックアップからデータを復元"""
    try:
        supabase = get_supabase_client()
        result = supabase.table('backups').select('*').eq('backup_id', backup_id).execute()
        
        if not result.data:
            raise ValueError("バックアップが見つかりません")
            
        backup_data = result.data[0]['data']
        return restore_database(session, backup_data)
    except Exception as e:
        raise Exception(f"Supabaseからの復元に失敗しました: {str(e)}")

def show_backup_restore(session):
    """バックアップ・リストア機能のUI（Supabase版）"""
    st.subheader("データバックアップ・リストア")

    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### バックアップ作成")
        st.caption("※ 最新5件まで保存されます")
        if st.button("バックアップを作成"):
            try:
                with st.spinner("バックアップを作成中..."):
                    backup_data = backup_database(session)
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
                
                selected_backup = st.selectbox(
                    "リストアするバックアップを選択",
                    options=backup_options,
                    format_func=lambda x: f"{x['id']} ({x['created_at']})"
                )
                
                st.warning("⚠️ この操作は取り消せません")
                
                if st.button("リストアを実行"):
                    if st.button("本当に実行しますか？"):
                        try:
                            with st.spinner("リストア中..."):
                                restore_from_supabase(session, selected_backup[0])
                                st.success("リストアが完了しました")
                                st.rerun()
                        except Exception as e:
                            st.error(f"リストア中にエラーが発生しました: {str(e)}")
            else:
                st.info("バックアップが見つかりません")
        except Exception as e:
            st.error(f"バックアップ一覧の取得に失敗しました: {str(e)}")

if __name__ == "__main__":
    run()