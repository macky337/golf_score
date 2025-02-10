import streamlit as st
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
from sqlalchemy import func
import datetime
import hashlib

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
    st.title("管理画面")
    
    if not check_password():
        return
        
    session = SessionLocal()
    tab1, tab2, tab3 = st.tabs(["スコア修正", "ハンディキャップ修正", "メンバー管理"])

    with tab1:
        show_score_editor(session)
    
    with tab2:
        show_handicap_editor(session)
    
    with tab3:
        show_member_manager(session)

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
                        else:
                            extra = 0
                            extra_putt = 0
                    
                    updated_scores[score.score_id] = {
                        "front_score": front,
                        "back_score": back,
                        "extra_score": extra,
                        "front_putt": front_putt,
                        "back_putt": back_putt,
                        "extra_putt": extra_putt
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

if __name__ == "__main__":
    run()