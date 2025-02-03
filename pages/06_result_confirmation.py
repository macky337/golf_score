import streamlit as st
import datetime
import itertools
import io
import os
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 日本語対応フォントの登録（ipaexg.ttf が存在する場合）
if os.path.exists("ipaexg.ttf"):
    pdfmetrics.registerFont(TTFont('IPAexGothic', 'ipaexg.ttf'))
    FONT_NAME = "IPAexGothic"
else:
    st.warning("ipaexg.ttf not found. Falling back to default Helvetica (PDF output may not support Japanese).")
    FONT_NAME = "Helvetica"

def generate_pdf(df):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    y_position = height - margin

    c.setFont(FONT_NAME, 16)
    c.drawString(margin, y_position, "Golf Round Results")
    y_position -= 40

    c.setFont(FONT_NAME, 10)
    # ヘッダー出力
    for column in df.columns:
        # ヘッダー1行あたりの表示領域を確保
        c.drawString(margin, y_position, str(column))
        y_position -= 20
        if y_position < margin:
            c.showPage()
            y_position = height - margin
            c.setFont(FONT_NAME, 10)

    # データ行出力
    for index, row in df.iterrows():
        # 改ページ判定：下部余白以下になったら新規ページ
        if y_position < margin + 20:
            c.showPage()
            y_position = height - margin
            c.setFont(FONT_NAME, 10)
        for col in df.columns:
            text = str(row[col])
            c.drawString(margin, y_position, text)
            y_position -= 20
            if y_position < margin:
                c.showPage()
                y_position = height - margin
                c.setFont(FONT_NAME, 10)
        y_position -= 10  # 行間スペース
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

def calc_putt_points(putt_scores, n):
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
    st.title("Result Confirmation")
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
    score_rows = (session.query(Score)
                  .join(Member, Score.member_id == Member.member_id)
                  .filter(Score.round_id == active_round.round_id)
                  .all())
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

    # 4) スコアデータ作成（前半(front), 後半(back), エキストラ(extra), 合計18ホール）
    player_data = {}
    for sc in score_rows:
        f = sc.front_score or 0
        b = sc.back_score or 0
        e = sc.extra_score or 0
        putt_f = sc.front_putt or 0
        putt_b = sc.back_putt or 0
        game_front = sc.front_game_pt or 0
        game_back  = sc.back_game_pt or 0
        game_extra = sc.extra_game_pt if sc.extra_game_pt else 0
        player_data[sc.member_id] = {
            "Member ID": sc.member_id,
            "Player": sc.member.name,
            "Front Score": f,
            "Back Score": b,
            "Total Score": f + b,
            "Extra Score": e,
            # 各セグメントでのマッチ戦勝敗ポイント（初期値0）
            "Match Front": 0,
            "Match Back": 0,
            "Match Total": 0,
            "Match Extra": 0,
            # パット戦得点（後で計算）
            "Putt Front": 0,
            "Putt Back": 0,
            # ゲームポイント（各セグメントの合算）
            "Game Front": 0,
            "Game Back": 0,
            "Game Extra": 0,
            "Game Total": 0,
            # 集計ポイント
            "Aggregate Points": 0
        }
    
    # 例外ルール：総合判定（totalスコア）で判定する対戦ペア
    total_only_pairs = st.session_state.get("total_only_pairs", [])
    total_only_set = {frozenset(pair) for pair in total_only_pairs}
    
    # 5) マッチ戦ポイントの計算
    # 5.1 Front判定
    player_ids = list(player_data.keys())
    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            id_i = player_ids[i]
            id_j = player_ids[j]
            data_i = player_data[id_i]
            data_j = player_data[id_j]
            net_front_i = data_i["Front Score"] - handicaps.get((id_j, id_i), 0)
            net_front_j = data_j["Front Score"] - handicaps.get((id_i, id_j), 0)
            if net_front_i < net_front_j:
                data_i["Match Front"] += 10
                data_j["Match Front"] -= 10
                detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Front): {net_front_i} vs {net_front_j} → {data_i['Player']} +10, {data_j['Player']} -10")
            elif net_front_i > net_front_j:
                data_i["Match Front"] -= 10
                data_j["Match Front"] += 10
                detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Front): {net_front_i} vs {net_front_j} → {data_i['Player']} -10, {data_j['Player']} +10")
            else:
                detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Front): Draw")
    
    # 5.2 Back判定（後半スコアが入力されている場合）
    if any(data["Back Score"] > 0 for data in player_data.values()):
        for i in range(len(player_ids)):
            for j in range(i+1, len(player_ids)):
                id_i = player_ids[i]
                id_j = player_ids[j]
                data_i = player_data[id_i]
                data_j = player_data[id_j]
                net_back_i = data_i["Back Score"] - handicaps.get((id_j, id_i), 0)
                net_back_j = data_j["Back Score"] - handicaps.get((id_i, id_j), 0)
                if net_back_i < net_back_j:
                    data_i["Match Back"] += 10
                    data_j["Match Back"] -= 10
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Back): {net_back_i} vs {net_back_j} → {data_i['Player']} +10, {data_j['Player']} -10")
                elif net_back_i > net_back_j:
                    data_i["Match Back"] -= 10
                    data_j["Match Back"] += 10
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Back): {net_back_i} vs {net_back_j} → {data_i['Player']} -10, {data_j['Player']} +10")
                else:
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Back): Draw")
    
    # 5.3 Total判定（Front＋Back、後半スコアが入力されている場合）
    if any(data["Back Score"] > 0 for data in player_data.values()):
        for i in range(len(player_ids)):
            for j in range(i+1, len(player_ids)):
                id_i = player_ids[i]
                id_j = player_ids[j]
                data_i = player_data[id_i]
                data_j = player_data[id_j]
                net_total_i = (data_i["Front Score"] + data_i["Back Score"]) - handicaps.get((id_j, id_i), 0)
                net_total_j = (data_j["Front Score"] + data_j["Back Score"]) - handicaps.get((id_i, id_j), 0)
                if net_total_i < net_total_j:
                    data_i["Match Total"] += 10
                    data_j["Match Total"] -= 10
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Total): {net_total_i} vs {net_total_j} → {data_i['Player']} +10, {data_j['Player']} -10")
                elif net_total_i > net_total_j:
                    data_i["Match Total"] -= 10
                    data_j["Match Total"] += 10
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Total): {net_total_i} vs {net_total_j} → {data_i['Player']} -10, {data_j['Player']} +10")
                else:
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Total): Draw")
    
    # 5.4 Extra判定（エキストラホールがある場合）
    if any(data["Extra Score"] > 0 for data in player_data.values()):
        for i in range(len(player_ids)):
            for j in range(i+1, len(player_ids)):
                id_i = player_ids[i]
                id_j = player_ids[j]
                data_i = player_data[id_i]
                data_j = player_data[id_j]
                net_extra_i = data_i["Extra Score"] - handicaps.get((id_j, id_i), 0)
                net_extra_j = data_j["Extra Score"] - handicaps.get((id_i, id_j), 0)
                if net_extra_i < net_extra_j:
                    data_i["Match Extra"] += 10
                    data_j["Match Extra"] -= 10
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Extra): {net_extra_i} vs {net_extra_j} → {data_i['Player']} +10, {data_j['Player']} -10")
                elif net_extra_i > net_extra_j:
                    data_i["Match Extra"] -= 10
                    data_j["Match Extra"] += 10
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Extra): {net_extra_i} vs {net_extra_j} → {data_i['Player']} -10, {data_j['Player']} +10")
                else:
                    detailed_match_log.append(f"{data_i['Player']} vs {data_j['Player']} (Extra): Draw")
    
    # 6) パット戦の得点計算（FrontとBack separately）
    front_putt = {sc.member_id: (sc.front_putt or 0) for sc in score_rows}
    back_putt  = {sc.member_id: (sc.back_putt or 0) for sc in score_rows}
    n_players = len(score_rows)
    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points  = calc_putt_points(back_putt, n_players)
    for pid in player_data:
        player_data[pid]["Putt Front"] = putt_front_points.get(pid, 0)
        player_data[pid]["Putt Back"]  = putt_back_points.get(pid, 0)
    
    # 7) ゲームポイントの計算（Front, Back, Extra終了時点）
    for pid, data in player_data.items():
        gp_front = data["Match Front"] + data["Putt Front"]
        gp_back = (data["Match Back"] + data["Putt Back"]) if data["Back Score"] > 0 else 0
        gp_total = data["Match Total"] if data["Back Score"] > 0 else 0
        gp_extra = data["Match Extra"]
        data["Game Front"] = gp_front
        data["Game Back"] = gp_back
        data["Game Extra"] = gp_extra
        data["Game Total"] = gp_front + gp_back + gp_total + gp_extra
    
    # 8) 集計ポイントの計算（4人なら自分のGame Total×3－他3人、3人なら×2－他2人）
    overall_points = {pid: player_data[pid]["Game Total"] for pid in player_data}
    for pid in player_data:
        others_sum = sum(overall_points[other] for other in overall_points if other != pid)
        if n_players == 4:
            agg = player_data[pid]["Game Total"] * 3 - others_sum
        elif n_players == 3:
            agg = player_data[pid]["Game Total"] * 2 - others_sum
        else:
            agg = player_data[pid]["Game Total"]
        player_data[pid]["Aggregate Points"] = agg
    total_agg = sum(player_data[pid]["Aggregate Points"] for pid in player_data)
    st.write(f"**検算：全体の集計ポイント合計 = {total_agg} (0であるべき)**")
    
    # 9) 結果を表形式にまとめて表示（項目名は指定通り）
    result_data = []
    for pid, data in player_data.items():
        result_data.append({
            "Player": data["Player"],
            "前半スコア": data["Front Score"],
            "後半スコア": data["Back Score"],
            "合計スコア": data["Total Score"],
            "エキストラスコア": data["Extra Score"],
            "前半勝敗ポイント": data["Match Front"],
            "後半勝敗ポイント": data["Match Back"],
            "合計勝敗ポイント": data["Match Total"],
            "エキストラ勝敗ポイント": data["Match Extra"],
            "パット戦前": data["Putt Front"],
            "パット戦後": data["Putt Back"],
            "パット戦合計": data["Putt Front"] + data["Putt Back"],
            "ゲームポイント前半": data["Game Front"],
            "ゲームポイント後半": data["Game Back"],
            "エキストラゲームポイント": data["Game Extra"],
            "合計ポイント": data["Game Total"],
            "集計ポイント": data["Aggregate Points"]
        })
    df = pd.DataFrame(result_data)
    st.write("### 最終結果（Front & Back & Extra終了時点）")
    st.dataframe(df)
    
    # 10) 対戦結果（獲得ポイント） 星取表の作成
    # Backスコアが入力されていればTotal＋Extra判定、そうでなければFrontのみを用いる
    match_matrix = pd.DataFrame(
        index=[data["Player"] for data in player_data.values()],
        columns=[data["Player"] for data in player_data.values()]
    )
    total_points = {}
    player_ids = list(player_data.keys())
    for i, pid_i in enumerate(player_ids):
        player_name_i = player_data[pid_i]["Player"]
        total_points[player_name_i] = 0
        for j, pid_j in enumerate(player_ids):
            if i == j:
                match_matrix.loc[player_name_i, player_data[pid_j]["Player"]] = ""
            else:
                if player_data[pid_i]["Back Score"] > 0 and player_data[pid_j]["Back Score"] > 0:
                    net_total_i = (player_data[pid_i]["Front Score"] + player_data[pid_i]["Back Score"]) - handicaps.get((pid_j, pid_i), 0)
                    net_total_j = (player_data[pid_j]["Front Score"] + player_data[pid_j]["Back Score"]) - handicaps.get((pid_i, pid_j), 0)
                    if net_total_i < net_total_j:
                        score_total = 10
                    elif net_total_i > net_total_j:
                        score_total = -10
                    else:
                        score_total = 0
                    extra_i = player_data[pid_i]["Extra Score"]
                    extra_j = player_data[pid_j]["Extra Score"]
                    if extra_i > 0 or extra_j > 0:
                        net_extra_i = extra_i - handicaps.get((pid_j, pid_i), 0)
                        net_extra_j = extra_j - handicaps.get((pid_i, pid_j), 0)
                        if net_extra_i < net_extra_j:
                            score_extra = 10
                        elif net_extra_i > net_extra_j:
                            score_extra = -10
                        else:
                            score_extra = 0
                    else:
                        score_extra = 0
                    score = score_total + score_extra
                else:
                    net_i = player_data[pid_i]["Front Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_j = player_data[pid_j]["Front Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_i < net_j:
                        score = 10
                    elif net_i > net_j:
                        score = -10
                    else:
                        score = 0
                match_matrix.loc[player_data[pid_i]["Player"], player_data[pid_j]["Player"]] = f"{score:+d}"
                total_points[player_data[pid_i]["Player"]] += score
    st.write("### 対戦結果（獲得ポイント） 星取表（Total判定含む）")
    st.dataframe(match_matrix)
    
    st.write("### 各プレイヤーの総獲得ポイント（Total判定含む）")
    total_points_df = pd.DataFrame(list(total_points.items()), columns=["Player", "Total Points"])
    st.dataframe(total_points_df)
    
    # 11) 対戦詳細ログの表示
    st.write("### 対戦詳細")
    for log in detailed_match_log:
        st.write(log)
    
    # 12) CSVダウンロードボタン（cp932エンコードで出力）
    csv_data = df.to_csv(index=False, encoding="cp932")
    st.download_button(
        label="Download CSV of Results",
        data=csv_data,
        file_name="golf_round_results.csv",
        mime="text/csv"
    )
    
    # 13) PDFダウンロードボタン
    pdf_buffer = generate_pdf(df)
    st.download_button(
        label="Download PDF of Results",
        data=pdf_buffer,
        file_name="golf_round_results.pdf",
        mime="application/pdf"
    )
    
    # 14) ラウンド結果最終化ボタン
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
