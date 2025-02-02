# pages/06_result_confirmation.py

import streamlit as st
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
import itertools

def run():
    st.title("Result Confirmation")

    session = SessionLocal()
    match_results = []  # ← ここで初期化

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
        handicaps[(p1, p2)] = match.player_1_to_2  # p1 → p2 に渡すハンデ
        handicaps[(p2, p1)] = match.player_2_to_1  # p2 → p1 に渡すハンデ

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

        # "Member ID" を追加
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
                handicap_i_to_j = handicaps.get((players[i].member_id, players[j].member_id), 0)
                handicap_j_to_i = handicaps.get((players[j].member_id, players[i].member_id), 0)
                net_score_i = score_i - handicap_i_to_j
                net_score_j = score_j - handicap_j_to_i

                if net_score_i > net_score_j:
                    player_data[players[i].member_id]["Match Points"] += 10
                    player_data[players[j].member_id]["Match Points"] -= 10
                elif net_score_i < net_score_j:
                    player_data[players[i].member_id]["Match Points"] -= 10
                    player_data[players[j].member_id]["Match Points"] += 10
                # 同点の場合は変更なし

                # マッチ結果を記録
                if seg == "front_score":
                    seg_name = "Front"
                elif seg == "back_score":
                    seg_name = "Back"
                else:
                    seg_name = "Extra"
                
                if net_score_i > net_score_j:
                    match_results.append(f"{players[i].member.name} vs {players[j].member.name} ({seg_name}): {score_i} - {score_j} (Handicap: {handicap_i_to_j} - {handicap_j_to_i}) | {players[i].member.name} wins (Net: {net_score_i} - {net_score_j})")
                elif net_score_i < net_score_j:
                    match_results.append(f"{players[i].member.name} vs {players[j].member.name} ({seg_name}): {score_i} - {score_j} (Handicap: {handicap_i_to_j} - {handicap_j_to_i}) | {players[j].member.name} wins (Net: {net_score_i} - {net_score_j})")
                else:
                    match_results.append(f"{players[i].member.name} vs {players[j].member.name} ({seg_name}): {score_i} - {score_j} (Handicap: {handicap_i_to_j} - {handicap_j_to_i}) | Draw (Net: {net_score_i} - {net_score_j})")

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
            # 全員同点 → 全員 0
        elif n == 3:
            if len(winners) == 1:
                points[winners[0]] = 20
            elif len(winners) == 2:
                for m_id in putt_scores:
                    if m_id not in winners:
                        points[m_id] = -20
            # 全員同点 → 0
        return points

    # パット戦 前後半の集計
    putt_front = {sc.member_id: (sc.front_putt or 0) for sc in score_rows}
    front_putt_points = calc_putt_points(putt_front, n_players)

    putt_back = {sc.member_id: (sc.back_putt or 0) for sc in score_rows}
    back_putt_points = calc_putt_points(putt_back, n_players)

    # 各プレイヤーにパット戦ポイントを加算
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

    # ----- 調整総合ポイントの計算 -----
    all_overall = {m_id: player_data[m_id]["Overall Points"] for m_id in player_data}
    for m_id in player_data:
        others_sum = sum([pt for mid, pt in all_overall.items() if mid != m_id])
        if n_players == 4:
            adj = player_data[m_id]["Overall Points"] * 3 - others_sum
        elif n_players == 3:
            adj = player_data[m_id]["Overall Points"] * 2 - others_sum
        else:
            adj = player_data[m_id]["Overall Points"]  # それ以外の場合はそのまま
        player_data[m_id]["Adjusted Points"] = adj

    # ----- 結果の DataFrame 化と表示 -----
    result_data = list(player_data.values())
    df = pd.DataFrame(result_data, columns=[
        "Player",
        "Front Score", "Back Score", "Extra Score", "Score Total",
        "Front Putt", "Back Putt", "Extra Putt", "Putt Total",
        "Game Front", "Game Back", "Game Extra", "Game Total",
        "Match Points",
        "Overall Points", "Adjusted Points"
    ])
    st.dataframe(df)

    # Match Results は既存の match_results を利用して表示
    st.write("Match Results:")
    for result in match_results:
        st.write(result)

    # 7) ラウンド結果を最終化
    if st.button("Finalize Results"):
        session.query(Round).filter(Round.finalized == False).update({Round.finalized: True})
        session.commit()
        session.close()
        st.success("Results have been finalized.")
        st.experimental_rerun()

if __name__ == "__main__":
    run()
