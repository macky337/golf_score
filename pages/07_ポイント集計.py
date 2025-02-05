import streamlit as st
import pandas as pd
import datetime
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def main():
    st.title("ポイント集計")
    st.sidebar.title("ポイント集計")
    aggregation_method = st.sidebar.selectbox("集計方法を選択してください", ["全体集計", "年度集計"])
    
    session = SessionLocal()
    # 「finalized=True」のラウンドを取得
    rounds = session.query(Round).filter(Round.finalized == True).all()
    if not rounds:
        st.warning("確定されたラウンドがありません。")
        session.close()
        return

    records = []
    for rnd in rounds:
        # Roundテーブルに「date_played」カラムがあると想定
        # もし別のカラム名なら適宜置き換えてください
        if not hasattr(rnd, 'date_played'):
            continue
        
        scores = session.query(Score).join(Member).filter(Score.round_id == rnd.round_id).all()
        for s in scores:
            # ゲームポイント合計を計算 (None対策)
            game_total = (s.front_game_pt or 0) + (s.back_game_pt or 0) + (s.extra_game_pt or 0)
            records.append({
                "Player": s.member.name,
                # ここでラウンド日付を「Round Date」列に保存
                "Round Date": rnd.date_played,  
                "Game Total": game_total
            })
    session.close()
    
    if not records:
        st.warning("スコアデータが見つかりませんでした。")
        return

    df = pd.DataFrame(records)
    
    if aggregation_method == "全体集計":
        agg_df = df.groupby("Player")["Game Total"].sum().reset_index().sort_values(by="Game Total", ascending=False)
        st.subheader("全体集計（ゲームポイント合計）")
        st.dataframe(agg_df)
        st.bar_chart(agg_df.set_index("Player"))
    else:
        # 年度集計
        df["Year"] = df["Round Date"].apply(lambda x: x.year if isinstance(x, datetime.date) else pd.to_datetime(x).year)
        agg_df = df.groupby(["Year", "Player"])["Game Total"].sum().reset_index()
        st.subheader("年度集計（ゲームポイント合計）")
        st.dataframe(agg_df)
        
        years = sorted(agg_df["Year"].unique())
        selected_year = st.sidebar.selectbox("年度を選択してください", years)
        year_df = agg_df[agg_df["Year"] == selected_year].sort_values(by="Game Total", ascending=False)
        st.subheader(f"{selected_year}年度集計")
        st.dataframe(year_df)
        st.bar_chart(year_df.set_index("Player")["Game Total"])

if __name__ == "__main__":
    main()
