import streamlit as st
import datetime
import itertools
import io
import os
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 日本語対応フォントの登録（ipaexg.ttf が同一ディレクトリに存在する場合）
FONT_NAME = "Helvetica"
if os.path.exists("ipaexg.ttf"):
    try:
        pdfmetrics.registerFont(TTFont('IPAexGothic', 'ipaexg.ttf'))
        FONT_NAME = "IPAexGothic"
    except Exception as e:
        st.warning(f"フォント登録エラー: {e}. デフォルトHelveticaを使用します。")
else:
    st.warning("ipaexg.ttf が見つかりません。PDF出力は Helvetica となります（日本語表示に問題が生じる可能性があります）。")

def generate_pdf(final_df, star_df):
    """最終結果と星取表をPDFで出力する"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    title_style = styles["Heading2"]

    # タイトル
    elements.append(Paragraph("Golf Round Results", title_style))
    elements.append(Spacer(1, 12))

    # 最終結果テーブル
    elements.append(Paragraph("最終結果（Front & Back & Extra終了時点）", title_style))
    elements.append(Spacer(1, 12))
    final_data = [final_df.columns.tolist()] + final_df.values.tolist()
    available_width = landscape(letter)[0] - 40  # 余白を考慮
    col_width = available_width / len(final_df.columns)
    table1 = Table(final_data, colWidths=[col_width]*len(final_df.columns))
    table1.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
    ]))
    elements.append(table1)
    elements.append(Spacer(1, 24))

    # 星取表（対戦結果）テーブル
    elements.append(Paragraph("対戦結果（獲得ポイント） 星取表（Total判定含む）", title_style))
    elements.append(Spacer(1, 12))
    star_header = [Paragraph(f"<para align='center'>{col}</para>", styles["BodyText"]) for col in star_df.columns]
    star_data = [star_header] + star_df.values.tolist()
    col_width2 = available_width / len(star_df.columns)
    table2 = Table(star_data, colWidths=[col_width2]*len(star_df.columns))
    table2.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
    ]))
    elements.append(table2)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def calc_putt_points(putt_scores, n):
    """パット戦の得点計算（4人 or 3人の場合）"""
    scores = list(putt_scores.values())
    min_score = min(scores)
    winners = [m_id for m_id, score in putt_scores.items() if score == min_score]
    points = {m_id: 0 for m_id in putt_scores}
    if n == 4:
        if len(winners) == 1:
            points[winners[0]] = 30
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10
        elif len(winners) == 2:
            for m_id in putt_scores:
                points[m_id] = 10 if m_id in winners else -10
        elif len(winners) == 3:
            for m_id in putt_scores:
                points[m_id] = 10 if m_id in winners else -30
    elif n == 3:
        if len(winners) == 1:
            points[winners[0]] = 20
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -20
        elif len(winners) == 2:
            for m_id in putt_scores:
                points[m_id] = 10 if m_id in winners else -20
    return points

def run():
    st.title("集計結果確認 (Total Only + パット戦なしの星取表)")
    session = SessionLocal()
    detailed_match_log = []  # 対戦詳細ログ

    # 1) 未確定ラウンドの取得
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return
    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) スコアとプレイヤー情報の取得
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

    # 3) ハンディキャップの取得
    handicaps = {}
    handicap_matches = session.query(HandicapMatch).filter(HandicapMatch.round_id == active_round.round_id).all()
    for match in handicap_matches:
        p1 = match.player_1_id
        p2 = match.player_2_id
        if (p1, p2) not in handicaps:
            handicaps[(p1, p2)] = match.player_1_to_2
        if (p2, p1) not in handicaps:
            handicaps[(p2, p1)] = match.player_2_to_1

    # 4) スコアデータ作成
    player_data = {}
    for sc in score_rows:
        f = sc.front_score or 0
        b = sc.back_score or 0
        e = sc.extra_score or 0
        putt_f = sc.front_putt or 0
        putt_b = sc.back_putt or 0
        input_game_front = sc.front_game_pt or 0
        input_game_back  = sc.back_game_pt or 0
        input_game_extra = sc.extra_game_pt if sc.extra_game_pt is not None else 0
        player_data[sc.member_id] = {
            "Member ID": sc.member_id,
            "Player": sc.member.name,
            "Front Score": f,
            "Back Score": b,
            "Extra Score": e,
            "Total Score": f + b,
            "Input Game Front": input_game_front,
            "Input Game Back": input_game_back,
            "Input Game Extra": input_game_extra,
            # マッチ戦の得点
            "Match Front": 0,
            "Match Back": 0,
            "Match Total": 0,
            "Match Extra": 0,
            # パット戦の得点
            "Putt Front": 0,
            "Putt Back": 0
        }

    # total_only_pairs の取得 （例：st.session_state.total_only_pairs）
    total_only_pairs = st.session_state.get("total_only_pairs", [])
    total_only_set = {frozenset(pair) for pair in total_only_pairs}

    # 5) 1対1のマッチ戦
    # front / back / total / extra の比較を行うが、
    # total_only_set に含まれるペアは front/back をスキップし total + extra のみ判定
    player_ids = list(player_data.keys())
    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            pid_i, pid_j = player_ids[i], player_ids[j]
            data_i, data_j = player_data[pid_i], player_data[pid_j]
            pair_key = frozenset([pid_i, pid_j])

            # ハンデ
            # (相手, 自分) キーに応じてスコアから差し引く
            # net_front_i = frontスコア - handicaps.get((pid_j, pid_i), 0)
            # net_front_j = frontスコア - handicaps.get((pid_i, pid_j), 0)

            if pair_key in total_only_set:
                # total only （Front & Back 比較はスキップ）
                # net_total
                net_total_i = (data_i["Front Score"] + data_i["Back Score"]) - handicaps.get((pid_j, pid_i), 0)
                net_total_j = (data_j["Front Score"] + data_j["Back Score"]) - handicaps.get((pid_i, pid_j), 0)
                if net_total_i < net_total_j:
                    data_i["Match Total"] += 10
                    data_j["Match Total"] -= 10
                elif net_total_i > net_total_j:
                    data_i["Match Total"] -= 10
                    data_j["Match Total"] += 10

                # extra（エキストラ）
                if data_i["Extra Score"] > 0 or data_j["Extra Score"] > 0:
                    net_extra_i = data_i["Extra Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_extra_j = data_j["Extra Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_extra_i < net_extra_j:
                        data_i["Match Extra"] += 10
                        data_j["Match Extra"] -= 10
                    elif net_extra_i > net_extra_j:
                        data_i["Match Extra"] -= 10
                        data_j["Match Extra"] += 10
            else:
                # 通常：front / back / total / extra の全比較
                # front
                net_front_i = data_i["Front Score"] - handicaps.get((pid_j, pid_i), 0)
                net_front_j = data_j["Front Score"] - handicaps.get((pid_i, pid_j), 0)
                if net_front_i < net_front_j:
                    data_i["Match Front"] += 10
                    data_j["Match Front"] -= 10
                elif net_front_i > net_front_j:
                    data_i["Match Front"] -= 10
                    data_j["Match Front"] += 10

                # back
                if data_i["Back Score"] > 0 and data_j["Back Score"] > 0:
                    net_back_i = data_i["Back Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_back_j = data_j["Back Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_back_i < net_back_j:
                        data_i["Match Back"] += 10
                        data_j["Match Back"] -= 10
                    elif net_back_i > net_back_j:
                        data_i["Match Back"] -= 10
                        data_j["Match Back"] += 10
                    # total
                    net_total_i = (data_i["Front Score"] + data_i["Back Score"]) - handicaps.get((pid_j, pid_i), 0)
                    net_total_j = (data_j["Front Score"] + data_j["Back Score"]) - handicaps.get((pid_i, pid_j), 0)
                    if net_total_i < net_total_j:
                        data_i["Match Total"] += 10
                        data_j["Match Total"] -= 10
                    elif net_total_i > net_total_j:
                        data_i["Match Total"] -= 10
                        data_j["Match Total"] += 10

                # extra
                if data_i["Extra Score"] > 0 or data_j["Extra Score"] > 0:
                    net_extra_i = data_i["Extra Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_extra_j = data_j["Extra Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_extra_i < net_extra_j:
                        data_i["Match Extra"] += 10
                        data_j["Match Extra"] -= 10
                    elif net_extra_i > net_extra_j:
                        data_i["Match Extra"] -= 10
                        data_j["Match Extra"] += 10

    # 6) パット戦の得点計算（Front＆Back） - 最終結果でのみ使用、星取表には加算しない
    front_putt = {sc.member_id: (sc.front_putt or 0) for sc in score_rows}
    back_putt  = {sc.member_id: (sc.back_putt or 0) for sc in score_rows}
    n_players = len(score_rows)
    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points  = calc_putt_points(back_putt, n_players)

    # 7) 各プレイヤーの個人ポイント集計
    for pid, data in player_data.items():
        # パット戦
        data["Putt Front"] = putt_front_points.get(pid, 0)
        data["Putt Back"]  = putt_back_points.get(pid, 0)
        # 入力ゲームポイントの合計
        input_game_total = data["Input Game Front"] + data["Input Game Back"] + data["Input Game Extra"]
        match_points_total = data["Match Front"] + data["Match Back"] + data["Match Total"] + data["Match Extra"]
        putt_points_total = data["Putt Front"] + data["Putt Back"]
        data["Input Game Total"] = input_game_total
        data["Match Points Total"] = match_points_total
        data["Putt Points Total"] = putt_points_total
        # 個人の総ゲームポイント = 入力ゲームポイント + マッチ戦得点 + パット戦得点
        individual_total = input_game_total + match_points_total + putt_points_total
        data["Individual Total"] = individual_total

    # 8) 集計ポイント計算（4人⇒自分のIndividual Total×3 - 他3人、3人⇒×2 - 他2人）
    overall_points = {pid: player_data[pid]["Individual Total"] for pid in player_data}
    for pid in player_data:
        others_sum = sum(overall_points[other] for other in overall_points if other != pid)
        if n_players == 4:
            agg = player_data[pid]["Individual Total"] * 3 - others_sum
        elif n_players == 3:
            agg = player_data[pid]["Individual Total"] * 2 - others_sum
        else:
            agg = player_data[pid]["Individual Total"]
        player_data[pid]["Aggregate Points"] = agg

    total_agg = sum(player_data[pid]["Aggregate Points"] for pid in player_data)
    st.write(f"**検算：全体の集計ポイント合計 = {total_agg} (理論的に0になるはず)**")

    # 9) 結果を表形式にまとめて表示
    result_data = []
    for pid, data in player_data.items():
        result_data.append({
            "Player": data["Player"],
            "前半スコア": data["Front Score"],
            "後半スコア": data["Back Score"],
            "エキストラスコア": data["Extra Score"],
            "合計スコア": data["Total Score"],
            "Input GP (Front)": data["Input Game Front"],
            "Input GP (Back)": data["Input Game Back"],
            "Input GP (Extra)": data["Input Game Extra"],
            "Input GP (Total)": data["Input Game Total"],
            "Match Front": data["Match Front"],
            "Match Back": data["Match Back"],
            "Match Total": data["Match Total"],
            "Match Extra": data["Match Extra"],
            "Match Points Total": data["Match Points Total"],
            "Putt Front": data["Putt Front"],
            "Putt Back": data["Putt Back"],
            "Putt Points Total": data["Putt Points Total"],
            "Individual Total": data["Individual Total"],
            "Aggregate Points": data["Aggregate Points"]
        })
    final_df = pd.DataFrame(result_data)
    st.write("### 最終結果（Front & Back & Extra終了時点）")
    st.dataframe(final_df)

    # 10) 対戦結果 星取表の作成
    #  => 「total_only_pairs」 を加味し、パット戦は加算しない
    match_matrix = pd.DataFrame(
        index=[data["Player"] for data in player_data.values()],
        columns=[data["Player"] for data in player_data.values()]
    )
    total_points = {}
    for pid in player_data:
        total_points[player_data[pid]["Player"]] = 0

    for i, pid_i in enumerate(player_ids):
        player_name_i = player_data[pid_i]["Player"]
        for j, pid_j in enumerate(player_ids):
            if i == j:
                match_matrix.loc[player_name_i, player_data[pid_j]["Player"]] = ""
            else:
                # pair
                pair_key = frozenset([pid_i, pid_j])
                score = 0
                # total only ペアかどうか
                if pair_key in total_only_set:
                    # total only (Front,Backをスキップし、Total+Extraのみ)
                    net_total_i = (player_data[pid_i]["Front Score"] + player_data[pid_i]["Back Score"]) - handicaps.get((pid_j, pid_i), 0)
                    net_total_j = (player_data[pid_j]["Front Score"] + player_data[pid_j]["Back Score"]) - handicaps.get((pid_i, pid_j), 0)
                    if net_total_i < net_total_j:
                        score += 10
                    elif net_total_i > net_total_j:
                        score -= 10
                    # extra
                    if player_data[pid_i]["Extra Score"] > 0 or player_data[pid_j]["Extra Score"] > 0:
                        net_extra_i = player_data[pid_i]["Extra Score"] - handicaps.get((pid_j, pid_i), 0)
                        net_extra_j = player_data[pid_j]["Extra Score"] - handicaps.get((pid_i, pid_j), 0)
                        if net_extra_i < net_extra_j:
                            score += 10
                        elif net_extra_i > net_extra_j:
                            score -= 10
                else:
                    # フロント比較
                    net_front_i = player_data[pid_i]["Front Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_front_j = player_data[pid_j]["Front Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_front_i < net_front_j:
                        score += 10
                    elif net_front_i > net_front_j:
                        score -= 10
                    # バック（両者にBack Scoreがあれば）
                    if player_data[pid_i]["Back Score"] > 0 and player_data[pid_j]["Back Score"] > 0:
                        net_back_i = player_data[pid_i]["Back Score"] - handicaps.get((pid_j, pid_i), 0)
                        net_back_j = player_data[pid_j]["Back Score"] - handicaps.get((pid_i, pid_j), 0)
                        if net_back_i < net_back_j:
                            score += 10
                        elif net_back_i > net_back_j:
                            score -= 10
                        # total
                        net_total_i = (player_data[pid_i]["Front Score"] + player_data[pid_i]["Back Score"]) - handicaps.get((pid_j, pid_i), 0)
                        net_total_j = (player_data[pid_j]["Front Score"] + player_data[pid_j]["Back Score"]) - handicaps.get((pid_i, pid_j), 0)
                        if net_total_i < net_total_j:
                            score += 10
                        elif net_total_i > net_total_j:
                            score -= 10
                    # extra
                    if player_data[pid_i]["Extra Score"] > 0 or player_data[pid_j]["Extra Score"] > 0:
                        net_extra_i = player_data[pid_i]["Extra Score"] - handicaps.get((pid_j, pid_i), 0)
                        net_extra_j = player_data[pid_j]["Extra Score"] - handicaps.get((pid_i, pid_j), 0)
                        if net_extra_i < net_extra_j:
                            score += 10
                        elif net_extra_i > net_extra_j:
                            score -= 10

                match_matrix.loc[player_name_i, player_data[pid_j]["Player"]] = f"{score:+d}"
                total_points[player_name_i] += score

    star_df = pd.DataFrame(match_matrix)
    st.write("### 対戦結果（獲得ポイント） 星取表（Total判定含む, パット戦除外）")
    st.dataframe(star_df)

    # 合計列（プレイヤーごとの対戦総合）
    st.write("### 各プレイヤーの総対戦獲得ポイント")
    total_points_df = pd.DataFrame(list(total_points.items()), columns=["Player", "Match Matrix Points"])
    st.dataframe(total_points_df)

    # 11) 対戦詳細ログの表示
    # （本コードでは省略または従来通り detailed_match_log で保存しているならここで表示）
    # for log in detailed_match_log:
    #     st.write(log)

    # 12) PDFダウンロードボタン
    pdf_buffer = generate_pdf(final_df, star_df)
    st.download_button(
        label="Download PDF of Results",
        data=pdf_buffer,
        file_name="golf_round_results.pdf",
        mime="application/pdf"
    )

    # 13) ラウンド結果最終化ボタン
    if st.button("Finalize Results"):
        session.query(Round).filter(Round.finalized == False).update({Round.finalized: True})
        session.commit()
        session.close()
        st.success("Results have been finalized.")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run()
