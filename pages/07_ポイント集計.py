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
        if st.button("重複ゼロスコアデータ削除"):
            delete_zero_score_duplicates()
        if st.button("front scoreが0のレコード削除"):
            delete_front_score_zero_records()


#############################################
# 過去データ一覧表示：各ラウンドの各プレーヤーごとの詳細
#############################################
def show_all_past_data():
    st.subheader("過去ラウンドデータ一覧（プレーヤー別詳細）")
    session = SessionLocal()
    
    # Round IDでフィルタするための入力フィールド（0の場合は全件表示）
    round_id_filter = st.number_input("フィルタ：Round ID（0なら全件表示）", min_value=0, step=1, value=0)
    
    query = session.query(
        Round.round_id,
        Round.date_played,
        Round.course_name,
        Member.name.label("Player"),
        Score.front_score,
        Score.back_score,
        Score.extra_score,
        Score.front_game_pt,
        Score.back_game_pt,
        Score.extra_game_pt,
        (Score.front_game_pt + Score.back_game_pt + Score.extra_game_pt).label("Game Pt"),
        Score.match_front,
        Score.match_back,
        Score.match_total,
        Score.match_extra,
        Score.match_pt,
        Score.put_pt,
        Score.total_pt
    ).join(Member, Score.member_id == Member.member_id)\
     .join(Round, Round.round_id == Score.round_id)\
     .filter(Round.finalized == True)
     
    # round_id_filterが0以外なら追加フィルタを適用
    if round_id_filter != 0:
        query = query.filter(Round.round_id == round_id_filter)
        
    results = query.order_by(Round.date_played.desc(), Round.round_id.desc(), Member.name).all()
    
    session.close()
    
    if not results:
        st.info("該当する過去ラウンドデータは存在しません。")
        return

    # 結果をDataFrameに変換
    columns = ["Round ID", "日付", "ゴルフ場名", "Player", 
               "Front Score", "Back Score", "Extra Score", 
               "Front GP", "Back GP", "Extra GP", "Game Pt", 
               "Match Front", "Match Back", "Match Total", "Match Extra", 
               "Match Pt", "Put Pt", "Total Pt"]
    df = pd.DataFrame(results, columns=columns)
    st.dataframe(df)


#############################################
# データ削除画面：指定したラウンドの詳細表示と削除
#############################################
def show_data_deletion():
    st.subheader("ラウンド削除（Round ID 指定）")
    session = SessionLocal()
    all_rounds = session.query(Round).all()
    if not all_rounds:
        st.info("ラウンドデータが存在しません。")
        session.close()
        return

    # 全ラウンド情報の一覧を表示して、対象のRound IDを確認できるようにする
    rounds_info = [(r.round_id, r.date_played, r.course_name) for r in all_rounds]
    df_rounds = pd.DataFrame(rounds_info, columns=["Round ID", "日付", "ゴルフ場名"])
    st.dataframe(df_rounds)

    # ユーザーに削除対象のRound IDを入力させる
    round_id = st.number_input("削除したいラウンドのRound IDを入力", min_value=1, step=1)

    # 入力されたRound IDの詳細を、各プレーヤーごとに表示
    if round_id:
        detail_results = session.query(
            Round.round_id,
            Round.date_played,
            Round.course_name,
            Member.name.label("Player"),
            Score.front_score,
            Score.back_score,
            Score.extra_score,
            Score.front_game_pt,
            Score.back_game_pt,
            Score.extra_game_pt,
            (Score.front_game_pt + Score.back_game_pt + Score.extra_game_pt).label("Game Pt"),
            Score.match_front,
            Score.match_back,
            Score.match_total,
            Score.match_extra,
            Score.match_pt,
            Score.put_pt,
            Score.total_pt
        ).join(Member, Score.member_id == Member.member_id)\
         .join(Round, Round.round_id == Score.round_id)\
         .filter(Round.round_id == round_id).all()
        
        if detail_results:
            detail_columns = ["Round ID", "日付", "ゴルフ場名", "Player", 
                              "Front Score", "Back Score", "Extra Score",
                              "Front GP", "Back GP", "Extra GP", "Game Pt", 
                              "Match Front", "Match Back", "Match Total", "Match Extra", 
                              "Match Pt", "Put Pt", "Total Pt"]
            detail_df = pd.DataFrame(detail_results, columns=detail_columns)
            st.markdown("### 選択したラウンドの各プレーヤー詳細")
            st.dataframe(detail_df)
        else:
            st.warning("指定されたRound IDの詳細は存在しません。")
    
    confirm = st.checkbox("本当に削除しますか？", key="delete_confirm")
    if st.button("Delete Data"):
        if not confirm:
            st.warning("削除の確認チェックを入れてください。")
        else:
            round_to_delete = session.query(Round).filter(Round.round_id == round_id).first()
            if not round_to_delete:
                st.warning("該当するRound IDのラウンドが見つかりませんでした。")
            else:
                # 先に関連するScoreレコードを削除（ON DELETE CASCADEが設定されていない場合）
                session.query(Score).filter(Score.round_id == round_to_delete.round_id).delete()
                session.delete(round_to_delete)
                session.commit()
                st.success(f"Round ID: {round_id} のラウンドと関連スコアを削除しました。")
    session.close()


#############################################
# 重複しているゼロスコアの削除処理
#############################################
def delete_zero_score_duplicates():
    session = SessionLocal()
    # Roundテーブルと結合して、Scoreレコードのうちスコア関連カラムが全て0のものを取得
    scores_with_date = session.query(Score, Round.date_played.label("date_played")).\
        join(Round, Score.round_id == Round.round_id).filter(
            Score.front_score == 0,
            Score.back_score == 0,
            Score.extra_score == 0,
            Score.front_game_pt == 0,
            Score.back_game_pt == 0,
            Score.extra_game_pt == 0,
            Score.match_front == 0,
            Score.match_back == 0,
            Score.match_total == 0,
            Score.match_extra == 0,
            Score.match_pt == 0,
            Score.put_pt == 0,
            Score.total_pt == 0
        ).all()

    # 同一の (Round ID, Member ID, 日付) の組み合わせで最初の1件を残し、それ以外を削除
    seen = {}
    delete_count = 0
    for record in scores_with_date:
        score = record[0]
        date_played = record[1]
        key = (score.round_id, score.member_id, date_played)
        if key in seen:
            session.delete(score)
            delete_count += 1
        else:
            seen[key] = score

    session.commit()
    session.close()
    st.success(f"重複したゼロスコアのレコードを {delete_count} 件削除しました。")


#############################################
# front scoreが0のレコード削除処理
#############################################
def delete_front_score_zero_records():
    session = SessionLocal()
    # front_scoreが0のScoreレコードをすべて取得
    zero_front_scores = session.query(Score).filter(Score.front_score == 0).all()
    delete_count = 0
    for score in zero_front_scores:
        session.delete(score)
        delete_count += 1
    session.commit()
    session.close()
    st.success(f"front scoreが0のレコードを {delete_count} 件削除しました。")


if __name__ == "__main__":
    main()