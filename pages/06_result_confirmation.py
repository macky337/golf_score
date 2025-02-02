import streamlit as st
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import itertools

def generate_pdf(df):
    # PDF生成用のバッファ
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # タイトルを追加
    c.setFont("Helvetica", 16)
    c.drawString(100, height - 40, "Golf Round Results")

    # 表のヘッダーを追加
    c.setFont("Helvetica", 10)
    y_position = height - 80
    for column in df.columns:
        c.drawString(100, y_position, column)
        y_position -= 20

    # データ行を追加
    for index, row in df.iterrows():
        y_position -= 20
        for col in df.columns:
            c.drawString(100, y_position, str(row[col]))
            y_position -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def run():
    st.title("Result Confirmation")

    session = SessionLocal()
    match_results = []  # 結果表示用リスト

    # 1) 未確定ラウンドの取得
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) ラウンドのスコアとプレイヤー情報を取得
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
    matches = session.query(HandicapMatch).filter(HandicapMatch.round_id == active_round.round_id).all()
    for match in matches:
        p1 = match.player_1_id
        p2 = match.player_2_id
        if (p1, p2) in handicaps:
            if handicaps[(p1, p2)] == 0 and match.player_1_to_2 != 0:
                handicaps[(p1, p2)] = match.player_1_to_2
        else:
            handicaps[(p1, p2)] = match.player_1_to_2

        if (p2, p1) in handicaps:
            if handicaps[(p2, p1)] == 0 and match.player_2_to_1 != 0:
                handicaps[(p2, p1)] = match.player_2_to_1
        else:
            handicaps[(p2, p1)] = match.player_2_to_1

    # 4) スコアデータの作成
    player_data = {}
    for sc in score_rows:
        f_score = sc.front_score or 0
        b_score = sc.back_score or 0
        e_score = sc.extra_score or 0
        f_putt  = sc.front_putt or 0
        b_putt  = sc.back_putt or 0
        e_putt  = sc.extra_putt or 0

        # ゲームポイント
        game_front = sc.front_game_pt or 0
        game_back  = sc.back_game_pt  or 0
        game_extra = sc.extra_game_pt if sc.extra_game_pt else 0
        game_total = game_front + game_back + game_extra

        player_data[sc.member_id] = {
            "Member ID": sc.member_id,
            "Player": sc.member.name,
            "Front Score": f_score,
            "Back Score": b_score,
            "Extra Score": e_score,
            "Score Total": f_score + b_score + e_score,
            "Front Putt": f_putt,
            "Back Putt": b_putt,
            "Extra Putt": e_putt,
            "Putt Total": f_putt + b_putt + e_putt,
            "Game Front": game_front,
            "Game Back": game_back,
            "Game Extra": game_extra,
            "Game Total": game_total,
            "Match Points": 0,
            "Overall Points": 0,
            "Adjusted Points": 0
        }

    # ----- マッチ戦ポイントの計算 -----
    players = list(score_rows)
    n_players = len(players)
    for i in range(n_players):
        for j in range(i+1, n_players):
            for seg in ["front_score", "back_score", "extra_score"]:
                score_i = getattr(players[i], seg) or 0
                score_j = getattr(players[j], seg) or 0

                # Extraホールの場合、両者のグロスが0なら除外
                if seg == "extra_score" and score_i == 0 and score_j == 0:
                    continue

                # 受けるハンデを差し引く
                handicap_for_i = handicaps.get((players[j].member_id, players[i].member_id), 0)
                handicap_for_j = handicaps.get((players[i].member_id, players[j].member_id), 0)
                net_score_i = score_i - handicap_for_i
                net_score_j = score_j - handicap_for_j

                # ネットスコアが低い方が勝ち
                if net_score_i < net_score_j:
                    player_data[players[i].member_id]["Match Points"] += 10
                    player_data[players[j].member_id]["Match Points"] -= 10
                    match_results.append(
                        f"{players[i].member.name} vs {players[j].member.name} ({seg}): {score_i} - {score_j} (Handicap: {handicap_for_i} vs {handicap_for_j}) | {players[i].member.name} wins (Net: {net_score_i} - {net_score_j})"
                    )
                elif net_score_i > net_score_j:
                    player_data[players[i].member_id]["Match Points"] -= 10
                    player_data[players[j].member_id]["Match Points"] += 10
                    match_results.append(
                        f"{players[i].member.name} vs {players[j].member.name} ({seg}): {score_i} - {score_j} (Handicap: {handicap_for_i} vs {handicap_for_j}) | {players[j].member.name} wins (Net: {net_score_i} - {net_score_j})"
                    )
                else:
                    match_results.append(
                        f"{players[i].member.name} vs {players[j].member.name} ({seg}): {score_i} - {score_j} (Handicap: {handicap_for_i} vs {handicap_for_j}) | Draw (Net: {net_score_i} - {net_score_j})"
                    )

    # ----- パット戦ポイントの計算 -----
    def calc_putt_points(putt_scores, n):
        scores = list(putt_scores.values())
        min_score = min(scores)
        winners = [m_id for m_id, score in putt_scores.items() if score == min_score]
        points = {m_id: 0 for m_id in putt_scores}
        if n == 4:
            if len(winners) == 1:
                points[winners[0]] = 30
            elif len(winners) == 2:
                for m_id in putt_scores:
                    if m_id not in winners:
                        points[m_id] = -10
            elif len(winners) == 3:
                for m_id in putt_scores:
                    if m_id not in winners:
                        points[m_id] = -30
        elif n == 3:
            if len(winners) == 1:
                points[winners[0]] = 20
            elif len(winners) == 2:
                for m_id in putt_scores:
                    if m_id not in winners:
                        points[m_id] = -20
        return points

    putt_front = {sc.member_id: (sc.front_putt or 0) for sc in score_rows}
    front_putt_points = calc_putt_points(putt_front, n_players)
    putt_back = {sc.member_id: (sc.back_putt or 0) for sc in score_rows}
    back_putt_points = calc_putt_points(putt_back, n_players)
    for m_id in player_data:
        player_data[m_id]["Putt Front"] = front_putt_points.get(m_id, 0)
        player_data[m_id]["Putt Back"] = back_putt_points.get(m_id, 0)
        player_data[m_id]["Putt Total"] = player_data[m_id]["Putt Front"] + player_data[m_id]["Putt Back"]

    # ----- 各個人の最終総合ポイントの集計 -----
    for m_id in player_data:
        overall = (player_data[m_id]["Game Total"] +
                   player_data[m_id]["Match Points"] +
                   player_data[m_id]["Putt Total"])
        player_data[m_id]["Overall Points"] = overall

    # ----- Adjusted Points 計算 -----
    for m_id in player_data:
        other_players_points = sum(
            player_data[other_id]["Overall Points"] for other_id in player_data if other_id != m_id
        )
        if n_players == 4:
            adj = player_data[m_id]["Overall Points"] * 3 - other_players_points
        elif n_players == 3:
            adj = player_data[m_id]["Overall Points"] * 2 - other_players_points
        player_data[m_id]["Adjusted Points"] = adj

    # ----- 結果の DataFrame 化と表示 -----
    result_data = list(player_data.values())
    df = pd.DataFrame(result_data, columns=[
        "Player", "Front Score", "Back Score", "Extra Score", "Score Total",
        "Front Putt", "Back Putt", "Extra Putt", "Putt Total",
        "Game Front", "Game Back", "Game Extra", "Game Total",
        "Match Points", "Overall Points", "Adjusted Points"
    ])
    st.dataframe(df)

    # PDF保存用のダウンロードボタン
    pdf_buffer = generate_pdf(df)
    st.download_button(
        label="Download PDF of Results",
        data=pdf_buffer,
        file_name="golf_round_results.pdf",
        mime="application/pdf"
    )

    # Match Results の表示
    st.write("Match Results:")
    for result in match_results:
        st.write(result)

    # ----- マッチ戦結果の星取表に変換 -----
    match_matrix = pd.DataFrame(
        index=[player["Player"] for player in player_data.values()],
        columns=[player["Player"] for player in player_data.values()]
    )

    for i, player_i in enumerate(player_data.values()):
        for j, player_j in enumerate(player_data.values()):
            if i != j:
                for seg in ["Front Score", "Back Score"]:
                    score_i = player_data[player_i["Member ID"]].get(seg, 0)
                    score_j = player_data[player_j["Member ID"]].get(seg, 0)
                    handicap_for_i = handicaps.get((player_j["Member ID"], player_i["Member ID"]), 0)
                    handicap_for_j = handicaps.get((player_i["Member ID"], player_j["Member ID"]), 0)
                    net_score_i = score_i - handicap_for_i
                    net_score_j = score_j - handicap_for_j
                    if net_score_i < net_score_j:
                        match_matrix.loc[player_i["Player"], player_j["Player"]] = "○"
                        match_matrix.loc[player_j["Player"], player_i["Player"]] = "×"
                    elif net_score_i > net_score_j:
                        match_matrix.loc[player_i["Player"], player_j["Player"]] = "×"
                        match_matrix.loc[player_j["Player"], player_i["Player"]] = "○"
                    else:
                        match_matrix.loc[player_i["Player"], player_j["Player"]] = "△"
                        match_matrix.loc[player_j["Player"], player_i["Player"]] = "△"

    st.write("### Match Results (Star Table)")
    st.dataframe(match_matrix.style.applymap(
        lambda x: 'background-color: green' if x == '○' else ('background-color: red' if x == '×' else 'background-color: gray')
    ))

    # 7) ラウンド結果を最終化
    if st.button("Finalize Results"):
        session.query(Round).filter(Round.finalized == False).update({Round.finalized: True})
        session.commit()
        session.close()
        st.success("Results have been finalized.")
        st.experimental_rerun()

if __name__ == "__main__":
    run()
