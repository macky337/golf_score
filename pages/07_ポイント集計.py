import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import func, extract
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def main():
    st.title("ポイント集計")

    # サイドバー: 集計 or 削除の切り替え
    st.sidebar.title("ポイント集計 / データ削除")
    menu = st.sidebar.radio("メニューを選択してください", ["ポイント集計", "データ削除"])

    if menu == "ポイント集計":
        show_aggregation()
    else:
        show_data_deletion()

def show_aggregation():
    """個人別のIndividual Totalの集計（全体集計と年度集計）
       ※本集計では、各ラウンドのゲームポイント合計（front_game_pt + back_game_pt + extra_game_pt）をIndividual Totalとみなしています。
    """
    aggregation_method = st.sidebar.selectbox("集計方法を選択してください", ["全体集計", "年度集計"])
    
    session = SessionLocal()
    
    # 計算式: 各Scoreレコードのゲームポイント合計
    total_points_expr = Score.front_game_pt + Score.back_game_pt + func.coalesce(Score.extra_game_pt, 0)
    
    if aggregation_method == "全体集計":
        overall_data = session.query(
            Member.name.label("Member"),
            func.sum(total_points_expr).label("Individual Total")
        ).join(Score, Score.member_id == Member.member_id) \
         .join(Round, Round.round_id == Score.round_id) \
         .filter(Round.finalized == True) \
         .group_by(Member.name) \
         .order_by(Member.name) \
         .all()
         
        if not overall_data:
            st.warning("集計データが存在しません。")
        else:
            df_overall = pd.DataFrame(overall_data, columns=["Member", "Individual Total"])
            st.subheader("全体集計（Individual Total）")
            st.dataframe(df_overall)
    else:
        yearly_data = session.query(
            Member.name.label("Member"),
            extract('year', Round.date_played).label("Year"),
            func.sum(total_points_expr).label("Individual Total")
        ).join(Score, Score.member_id == Member.member_id) \
         .join(Round, Round.round_id == Score.round_id) \
         .filter(Round.finalized == True) \
         .group_by(Member.name, extract('year', Round.date_played)) \
         .order_by(extract('year', Round.date_played), Member.name) \
         .all()
         
        if not yearly_data:
            st.warning("集計データが存在しません。")
        else:
            df_yearly = pd.DataFrame(yearly_data, columns=["Member", "Year", "Individual Total"])
            st.subheader("年度集計（Individual Total）")
            st.dataframe(df_yearly)
    session.close()

def show_data_deletion():
    """日付＋ゴルフ場単位でラウンド/スコアを削除する画面"""
    st.subheader("データ削除（日付＋ゴルフ場）")

    session = SessionLocal()
    # Roundテーブルから日付とゴルフ場の一覧を取得
    all_rounds = session.query(Round).all()
    if not all_rounds:
        st.info("ラウンドデータが存在しません。")
        session.close()
        return

    # 日付とコース名のペアを作成
    date_course_pairs = [(r.date_played, r.course_name) for r in all_rounds]
    date_course_pairs = list(set(date_course_pairs))
    date_course_pairs.sort(key=lambda x: (x[0], x[1]))

    # 1) 日付を選択
    unique_dates = sorted(list({p[0] for p in date_course_pairs}))
    selected_date = st.selectbox("削除したいラウンドの日付を選択", unique_dates)

    # 2) 同日付のコースを選択
    filtered_pairs = [p for p in date_course_pairs if p[0] == selected_date]
    course_list = sorted({p[1] for p in filtered_pairs})
    selected_course = st.selectbox("削除したいゴルフ場名を選択", course_list)

    # 削除の確認チェックボックス
    confirm = st.checkbox("本当に削除しますか？")

    if st.button("Delete Data"):
        if not confirm:
            st.warning("削除の確認チェックを入れてください。")
        else:
            rounds_to_delete = (
                session.query(Round)
                .filter(Round.date_played == selected_date, Round.course_name == selected_course)
                .all()
            )
            if not rounds_to_delete:
                st.warning("該当するラウンドが見つかりませんでした。")
            else:
                for r in rounds_to_delete:
                    # 先に Score を削除（ON DELETE CASCADE が無い場合）
                    session.query(Score).filter(Score.round_id == r.round_id).delete()
                    # Round を削除
                    session.delete(r)
                session.commit()
                st.success(f"{len(rounds_to_delete)} 件のラウンドおよび関連スコアを削除しました。")
    session.close()

if __name__ == "__main__":
    main()
