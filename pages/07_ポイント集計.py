# 07_point_aggregation.py
import streamlit as st
import pandas as pd
import datetime
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def main():
    # ページタイトル
    st.title("ポイント集計")
    
    # サイドバーにメニュー表示（選択肢：全体集計、年度集計）
    st.sidebar.title("ポイント集計")
    aggregation_method = st.sidebar.selectbox("集計方法を選択してください", ["全体集計", "年度集計"])
    
    session = SessionLocal()
    # 確定されたラウンドのみ対象とする（ラウンドの最終化フラグが True のもの）
    rounds = session.query(Round).filter(Round.finalized == True).all()
    if not rounds:
        st.warning("確定されたラウンドがありません。")
        session.close()
        return

    # 各ラウンドのスコアから、各プレイヤーのゲームポイント合計を算出する
    # ※ここでは、各スコアレコードの front_game_pt, back_game_pt, extra_game_pt を単純に合算した値を「ゲームポイント」としています。
    records = []
    for rnd in rounds:
        # ラウンドの日付情報（round_date）が存在する前提です
        if not hasattr(rnd, 'round_date'):
            continue
        scores = session.query(Score).join(Member).filter(Score.round_id == rnd.round_id).all()
        for s in scores:
            # バックやエキストラのポイントが未入力の場合に備えて None チェック
            game_total = s.front_game_pt if s.front_game_pt else 0
            game_total += s.back_game_pt if s.back_game_pt else 0
            game_total += s.extra_game_pt if s.extra_game_pt else 0
            records.append({
                "Player": s.member.name,
                "Round Date": rnd.round_date,
                "Game Total": game_total
            })
    session.close()
    
    if not records:
        st.warning("スコアデータが見つかりませんでした。")
        return

    # DataFrameに変換
    df = pd.DataFrame(records)
    
    # 集計方法によって処理を分岐
    if aggregation_method == "全体集計":
        # 各プレイヤーごとに全ラウンドのゲームポイント合計を算出
        agg_df = df.groupby("Player")["Game Total"].sum().reset_index().sort_values(by="Game Total", ascending=False)
        st.subheader("全体集計（ゲームポイント合計）")
        st.dataframe(agg_df)
        # 棒グラフ表示
        st.bar_chart(agg_df.set_index("Player"))
        
    elif aggregation_method == "年度集計":
        # ラウンド日付から年度を抽出（round_dateがdatetime型である前提）
        df["Year"] = df["Round Date"].apply(lambda x: x.year if isinstance(x, datetime.date) else pd.to_datetime(x).year)
        # 年度＋プレイヤーごとに集計
        agg_df = df.groupby(["Year", "Player"])["Game Total"].sum().reset_index()
        st.subheader("年度集計（ゲームポイント合計）")
        st.dataframe(agg_df)
        
        # サイドバーから表示する年度を選択できるようにする
        years = sorted(agg_df["Year"].unique())
        selected_year = st.sidebar.selectbox("年度を選択してください", years)
        year_df = agg_df[agg_df["Year"] == selected_year].sort_values(by="Game Total", ascending=False)
        st.subheader(f"{selected_year}年度集計")
        st.dataframe(year_df)
        # 棒グラフで年度内の各プレイヤーのポイントを表示
        st.bar_chart(year_df.set_index("Player")["Game Total"])

if __name__ == "__main__":
    main()
