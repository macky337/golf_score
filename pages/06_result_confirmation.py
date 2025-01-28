# pages/06_result_confirmation.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Round, Score, Member
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
from fpdf import FPDF

def run():
    st.title("Result Confirmation and Save")

    session = SessionLocal()

    # 1) 未確定（finalized=False）のラウンドを取得
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up and finalize a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) 該当ラウンドのスコアを取得
    score_rows = (
        session.query(Score)
        .join(Member, Score.member_id == Member.member_id)
        .filter(Score.round_id == active_round.round_id)
        .all()
    )

    if not score_rows:
        st.warning("No participants found for this round.")
        session.close()
        return

    # 3) 結果表示用のデータ準備
    result_data = []
    for sc in score_rows:
        total_score = sc.front_score + sc.back_score + (sc.extra_score if sc.extra_score else 0)
        total_putt = sc.front_putt + sc.back_putt + (sc.extra_putt if sc.extra_putt else 0)
        total_game_points = sc.front_game_pt + sc.back_game_pt + (sc.extra_game_pt if sc.extra_game_pt else 0)
        
        result_data.append({
            'Player': sc.member.name,
            'Front Score': sc.front_score,
            'Back Score': sc.back_score,
            'Extra Score': sc.extra_score if sc.extra_score else 0,
            'Total Score': total_score,
            'Front Putt': sc.front_putt,
            'Back Putt': sc.back_putt,
            'Extra Putt': sc.extra_putt if sc.extra_putt else 0,
            'Total Putt': total_putt,
            'Total Game Points': total_game_points
        })

    # 4) DataFrameに変換して表示
    df = pd.DataFrame(result_data)
    st.dataframe(df)

    # 5) 集計ポイントの計算 (例: 自分の得点 × (人数 - 1) - 他のメンバー合計)
    total_points = []
    for row in result_data:
        total_points.append(row['Total Game Points'] * (len(result_data) - 1) - sum([r['Total Game Points'] for r in result_data if r != row]))

    df['Total Points'] = total_points
    st.write("Calculated Total Points for each player:")
    st.dataframe(df)

    # 6) ラウンド結果を最終化
    if st.button("Finalize Results"):
        active_round.finalized = True
        session.commit()
        session.close()
        st.success("Results have been finalized.")

    # 7) PDFまたは画像として保存する
    if st.button("Save as PDF"):
        save_as_pdf(df)

    if st.button("Save as Image"):
        save_as_image(df)

    session.close()

def save_as_pdf(df):
    """結果をPDFとして保存"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, txt="Golf Score Results", ln=True, align='C')

    # 表の内容をPDFに追加
    pdf.set_font('Arial', '', 12)
    for i, row in df.iterrows():
        pdf.cell(200, 10, txt=", ".join([str(val) for val in row]), ln=True)

    # PDFとして保存
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    st.download_button(
        label="Download PDF",
        data=pdf_output,
        file_name="golf_score_results.pdf",
        mime="application/pdf"
    )

def save_as_image(df):
    """結果を画像として保存"""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
    plt.savefig("/tmp/golf_score_results.png", bbox_inches="tight")

    with open("/tmp/golf_score_results.png", "rb") as file:
        st.download_button(
            label="Download Image",
            data=file,
            file_name="golf_score_results.png",
            mime="image/png"
        )

if __name__ == "__main__":
    run()
