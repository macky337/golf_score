import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import func, extract
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def main():
    st.title("ポイント集計・過去データ管理")
    st.sidebar.title("メニュー")
    # サイドバーの選択肢：「ポイント集計」（過去データ一覧）と「データ削除」
    menu = st.sidebar.radio("メニューを選択してください", ["ポイント集計", "データ削除"])
    
    if menu == "ポイント集計":
        show_all_past_data()
    else:
        show_data_deletion()

#############################################
# 過去データ一覧表示：全ラウンドの詳細データ
#############################################
def show_all_past_data():
    st.subheader("過去ラウンドデータ一覧")
    session = SessionLocal()
    # 完了済みラウンドと関連スコア、Member情報をJOINして取得
    results = session.query(
        Round.round_id,
        Round.date_played,
        Round.course_name,
        Member.name.label("Player"),
        Score.front_score.label("Front Score"),
        Score.back_score.label("Back Score"),
        Score.extra_score.label("Extra Score"),
        Score.front_game_pt.label("Front GP"),
        Score.back_game_pt.label("Back GP"),
        Score.extra_game_pt.label("Extra GP"),
        (Score.front_game_pt + Score.back_game_pt + Score.extra_game_pt).label("Game Pt"),
        Score.match_front.label("Match Front"),
        Score.match_back.label("Match Back"),
        Score.match_total.label("Match Total"),
        Score.match_extra.label("Match Extra"),
        Score.match_pt.label("Match Pt"),
        Score.put_pt.label("Put Pt"),
        Score.total_pt.label("Total Pt")
    ).join(Member, Score.member_id == Member.member_id)\
     .join(Round, Round.round_id == Score.round_id)\
     .filter(Round.finalized == True)\
     .order_by(Round.date_played.desc()).all()
    session.close()
    
    if not results:
        st.info("過去のラウンドデータは存在しません。")
        return
    
    columns = ["Round ID", "日付", "ゴルフ場名", "Player", "Front Score", "Back Score", "Extra Score",
               "Front GP", "Back GP", "Extra GP", "Game Pt", "Match Front", "Match Back",
               "Match Total", "Match Extra", "Match Pt", "Put Pt", "Total Pt"]
    df = pd.DataFrame(results, columns=columns)
    st.dataframe(df)

#############################################
# データ削除画面：指定したラウンドを削除
#############################################
def show_data_deletion():
    st.subheader("データ削除（日付＋ゴルフ場）")
    session = SessionLocal()
    # Roundテーブルから全ラウンドを取得
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

    # 削除確認
    confirm = st.checkbox("本当に削除しますか？", key="delete_confirm")
    if st.button("Delete Data"):
        if not confirm:
            st.warning("削除の確認チェックを入れてください。")
        else:
            rounds_to_delete = session.query(Round).filter(
                Round.date_played == selected_date,
                Round.course_name == selected_course
            ).all()
            if not rounds_to_delete:
                st.warning("該当するラウンドが見つかりませんでした。")
            else:
                for r in rounds_to_delete:
                    # 先に Score を削除（ON DELETE CASCADEが設定されていない場合）
                    session.query(Score).filter(Score.round_id == r.round_id).delete()
                    session.delete(r)
                session.commit()
                st.success(f"{len(rounds_to_delete)} 件のラウンドおよび関連スコアを削除しました。")
    session.close()

if __name__ == "__main__":
    main()
