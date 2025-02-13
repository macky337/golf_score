import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import func, extract
from modules.db import SessionLocal
from modules.models import Round, Score, Member
import plotly.express as px
import plotly.graph_objects as go

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
    
    # 集計期間の選択（デフォルトは通算成績）
    aggregation_type = st.radio("集計期間", options=["通算成績", "年度別", "月別"], index=0)
    year = None
    month = None
    if aggregation_type == "年度別":
        year = st.number_input("集計する年度を入力", min_value=2000, max_value=datetime.datetime.now().year, value=datetime.datetime.now().year)
    elif aggregation_type == "月別":
        year = st.number_input("集計する年度を入力", min_value=2000, max_value=datetime.datetime.now().year, value=datetime.datetime.now().year)
        month = st.number_input("集計する月を入力", min_value=1, max_value=12, value=datetime.datetime.now().month)
    
    # 通常の詳細表示（フィルタ：Round ID）
    round_id_filter = st.number_input("詳細表示：Round ID（0なら全件表示）", min_value=0, step=1, value=0)
    
    session = SessionLocal()
    
    # Detail部分：各ラウンドの各プレーヤー詳細
    detail_query = session.query(
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
    
    if round_id_filter != 0:
        detail_query = detail_query.filter(Round.round_id == round_id_filter)
        
    detail_results = detail_query.order_by(Round.date_played.desc(), Round.round_id.desc(), Member.name).all()
    
    if not detail_results:
        st.info("該当する過去ラウンドデータは存在しません。")
    else:
        detail_columns = ["Round ID", "日付", "ゴルフ場名", "Player", 
                          "Front Score", "Back Score", "Extra Score", 
                          "Front GP", "Back GP", "Extra GP", "Game Pt", 
                          "Match Front", "Match Back", "Match Total", "Match Extra", 
                          "Match Pt", "Put Pt", "Total Pt"]
        detail_df = pd.DataFrame(detail_results, columns=detail_columns)
        st.markdown("### 各ラウンド・各プレーヤー詳細")
        st.dataframe(detail_df)
    
    # 集計部分：Member別にTotal Ptを集計
    from sqlalchemy import extract  # SQLAlchemyのextract関数で日付の年・月抽出
    agg_query = session.query(
        Member.name.label("Player"),
        func.sum(Score.total_pt).label("Total Pt")
    ).join(Score, Score.member_id == Member.member_id)\
     .join(Round, Round.round_id == Score.round_id)\
     .filter(Round.finalized == True)
    
    if aggregation_type == "年度別":
        agg_query = agg_query.filter(extract('year', Round.date_played) == year)
    elif aggregation_type == "月別":
        agg_query = agg_query.filter(extract('year', Round.date_played) == year)\
                           .filter(extract('month', Round.date_played) == month)
    
    agg_query = agg_query.group_by(Member.name)
    agg_results = agg_query.order_by(Member.name).all()
    session.close()
    
    if agg_results:
        agg_df = pd.DataFrame(agg_results, columns=["Player", "Total Pt"])
        agg_df = agg_df.sort_values(by="Total Pt", ascending=False)  # Total Ptの降順でソート
       
        st.markdown(f"### {aggregation_type} 集計結果")
        
        # データフレームの表示
        st.dataframe(agg_df)
        
        # グラフタイトルの設定
        title_text = f"{aggregation_type} Total Pt 集計結果"
        if aggregation_type == "年度別":
            title_text += f" ({year}年)"
        elif aggregation_type == "月別":
            title_text += f" ({year}年{month}月)"
        
        # plotly.expressを使用してグラフを作成
        fig = px.bar(
            agg_df,
            x="Player",
            y="Total Pt",
            title=title_text,
            labels={"Player": "プレーヤー", "Total Pt": "Total Pt"},
            text="Total Pt"  # 棒グラフ上に値を表示
        )
        
        # グラフのレイアウト調整
        fig.update_traces(
            texttemplate='%{text:.0f}',  # 整数で表示
            textposition='auto',
            hovertemplate='プレーヤー: %{x}<br>Total Pt: %{y:.0f}<extra></extra>'
        )
        
        fig.update_layout(
            title={
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            plot_bgcolor='white',
            height=500,
            showlegend=False,
            yaxis=dict(
                zeroline=True,
                zerolinewidth=1,
                zerolinecolor='grey',
                gridcolor='rgba(0,0,0,0.1)'
            )
        )
        
        # グラフの表示
        st.plotly_chart(fig, use_container_width=True)
        
        # 集計の補足情報
        with st.expander("集計の補足情報"):
            st.write("- 各プレーヤーのTotal Ptの合計を表示しています")
            st.write("- グラフは棒の上にマウスを置くと詳細な数値を確認できます")
            if aggregation_type == "月別":
                st.write(f"- {year}年{month}月の集計結果です")
            elif aggregation_type == "年度別":
                st.write(f"- {year}年の集計結果です")
            else:
                st.write("- 全期間の通算集計結果です")
            
    else:
        st.info("集計結果がありません。")


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