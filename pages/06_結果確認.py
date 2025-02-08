import streamlit as st
import datetime
import itertools
import io
import os
import pandas as pd
from sqlalchemy import func, extract
from sqlalchemy.orm import joinedload  # 追加: スコアと同時に member をロードするためのjoinedload
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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

# ===== 共通ヘルパー関数 =====
def safe_get_score(data, key):
    """スコア取得時、Noneや例外発生時は 0 を返す"""
    try:
        value = data.get(key, 0)
        if value is None:
            return 0
        return value
    except Exception:
        return 0

def calc_net_score(data, key, handicap, multiplier=1):
    """指定されたセクションのスコアから、ハンディキャップ（multiplier 倍）を差し引いた値を返す"""
    score = safe_get_score(data, key)
    try:
        return score - (handicap * multiplier)
    except Exception:
        return 0

def calc_net_total(data, handicap, multiplier=2):
    """FrontとBackのスコアの合計から、ハンディキャップ（multiplier 倍）を差し引いた値を返す"""
    front = safe_get_score(data, "Front Score")
    back = safe_get_score(data, "Back Score")
    return front + back - (handicap * multiplier)

def calc_net_extra(data, handicap, multiplier=1):
    """Extraスコアから、ハンディキャップ（multiplier 倍）を差し引いた値を返す"""
    extra = safe_get_score(data, "Extra Score")
    return extra - (handicap * multiplier)

def df_to_table_data_with_index(df, index_header="項目名"):
    """
    DataFrame を、インデックスを先頭列として含む2次元リストに変換する。
    先頭行は [index_header, カラム名1, カラム名2, …] とする。
    """
    header = [index_header] + list(df.columns)
    data = []
    for idx, row in df.iterrows():
        # index を文字列化して先頭に追加
        data.append([str(idx)] + list(row))
    return [header] + data

# ===== PDF出力等の関数 =====
def generate_pdf(final_df, detailed_df, star_df):
    """最終結果、マッチ戦詳細結果、対戦結果（Much Pt 集計）をすべてPDFで出力する"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    elements = []
    base_styles = getSampleStyleSheet()
    # 新たに日本語用のスタイルを定義
    title_style = ParagraphStyle(
        'titleStyle',
        parent=base_styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=14,
        leading=16,
        alignment=1  # 中央揃え
    )
    header_style = ParagraphStyle(
        'headerStyle',
        parent=base_styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=12,
        alignment=1
    )
    body_style = ParagraphStyle(
        'bodyStyle',
        parent=base_styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=12
    )

    # 利用可能な横幅の算出
    available_width = landscape(letter)[0] - 40

    # --- セクション1: 最終結果 ---
    elements.append(Paragraph("最終結果（Game Pt + Match Pt + Put Pt ＝ Total Pt）", title_style))
    elements.append(Spacer(1, 12))
    final_data = df_to_table_data_with_index(final_df)
    col_width_final = available_width / len(final_data[0])
    table_final = Table(final_data, colWidths=[col_width_final]*len(final_data[0]))
    table_final.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
    ]))
    elements.append(table_final)
    elements.append(Spacer(1, 24))

    # --- セクション2: マッチ戦詳細結果 ---
    elements.append(Paragraph("マッチ戦詳細結果", title_style))
    elements.append(Spacer(1, 12))
    detailed_data = df_to_table_data_with_index(detailed_df)
    col_width_detailed = available_width / len(detailed_data[0])
    table_detailed = Table(detailed_data, colWidths=[col_width_detailed]*len(detailed_data[0]))
    table_detailed.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
    ]))
    elements.append(table_detailed)
    elements.append(Spacer(1, 24))

    # --- セクション3: 対戦結果（Much Pt 集計） ---
    elements.append(Paragraph("対戦結果（Much Pt 集計）", title_style))
    elements.append(Spacer(1, 12))
    star_data = df_to_table_data_with_index(star_df)
    col_width_star = available_width / len(star_data[0])
    table_star = Table(star_data, colWidths=[col_width_star]*len(star_data[0]))
    table_star.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
    ]))
    elements.append(table_star)
    
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
                if m_id in winners:
                    points[m_id] = 10
                else:
                    points[m_id] = -10
        elif len(winners) == 3:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10
                else:
                    points[m_id] = -30
    elif n == 3:
        if len(winners) == 1:
            points[winners[0]] = 20
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -20
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10
                else:
                    points[m_id] = -20
    return points

def calc_match_points(data_i, data_j, handicap_ij, handicap_ji, is_total_only=False):
    """1対1のマッチポイント計算（各セクション±10pt）"""
    front_pt = back_pt = total_pt = extra_pt = 0

    if is_total_only:
        total_i = calc_net_total(data_i, handicap_ij, multiplier=2)
        total_j = calc_net_total(data_j, handicap_ji, multiplier=2)
        if total_i < total_j:
            total_pt = 10
        elif total_i > total_j:
            total_pt = -10
        if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
            extra_i = calc_net_extra(data_i, handicap_ij)
            extra_j = calc_net_extra(data_j, handicap_ji)
            if extra_i < extra_j:
                extra_pt = 10
            elif extra_i > extra_j:
                extra_pt = -10
        front_pt = 0
        back_pt = 0
    else:
        front_i = calc_net_score(data_i, "Front Score", handicap_ij, multiplier=1)
        front_j = calc_net_score(data_j, "Front Score", handicap_ji, multiplier=1)
        if front_i < front_j:
            front_pt = 10
        elif front_i > front_j:
            front_pt = -10
        if safe_get_score(data_i, "Back Score") > 0 and safe_get_score(data_j, "Back Score") > 0:
            back_i = calc_net_score(data_i, "Back Score", handicap_ij, multiplier=1)
            back_j = calc_net_score(data_j, "Back Score", handicap_ji, multiplier=1)
            if back_i < back_j:
                back_pt = 10
            elif back_i > back_j:
                back_pt = -10
            total_i = calc_net_total(data_i, handicap_ij, multiplier=2)
            total_j = calc_net_total(data_j, handicap_ji, multiplier=2)
            if total_i < total_j:
                total_pt = 10
            elif total_i > total_j:
                total_pt = -10
        if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
            extra_i = calc_net_extra(data_i, handicap_ij)
            extra_j = calc_net_extra(data_j, handicap_ji)
            if extra_i < extra_j:
                extra_pt = 10
            elif extra_i > extra_j:
                extra_pt = -10

    data_i["Match Front"] = front_pt
    data_i["Match Back"] = back_pt
    data_i["Match Total"] = total_pt
    data_i["Match Extra"] = extra_pt
    data_j["Match Front"] = -front_pt
    data_j["Match Back"] = -back_pt
    data_j["Match Total"] = -total_pt
    data_j["Match Extra"] = -extra_pt

    return front_pt + back_pt + total_pt + extra_pt, -(front_pt + back_pt + total_pt + extra_pt)

def create_match_matrix(player_data, handicaps, total_only_set):
    """マッチ対戦表（星取表）の作成"""
    player_ids = list(player_data.keys())
    match_matrix = pd.DataFrame(
        index=[player_data[mid]["Player"] for mid in player_ids],
        columns=[player_data[mid]["Player"] for mid in player_ids]
    )
    for i in range(len(player_ids)):
        name_i = player_data[player_ids[i]]["Player"]
        for j in range(len(player_ids)):
            name_j = player_data[player_ids[j]]["Player"]
            if i == j:
                match_matrix.loc[name_i, name_j] = ""
            else:
                match_matrix.loc[name_i, name_j] = "0"
    for i in range(len(player_ids)):
        pid_i = player_data[player_ids[i]]["Player"]
        for j in range(i + 1, len(player_ids)):
            pid_j = player_data[player_ids[j]]["Player"]
            handicap_ij = handicaps.get((player_ids[j], player_ids[i]), 0)
            handicap_ji = handicaps.get((player_ids[i], player_ids[j]), 0)
            is_total_only = frozenset([player_ids[i], player_ids[j]]) in total_only_set
            points_i, points_j = calc_match_points(
                player_data[player_ids[i]], 
                player_data[player_ids[j]],
                handicap_ij,
                handicap_ji,
                is_total_only
            )
            match_matrix.loc[pid_i, pid_j] = f"{points_i:+d}"
            match_matrix.loc[pid_j, pid_i] = f"{points_j:+d}"
    return match_matrix

def create_detailed_match_results(player_data, handicaps, total_only_set):
    """マッチ戦の詳細結果を作成（横：対戦カード、縦：プレイヤーのポイント）"""
    player_ids = list(player_data.keys())
    n_players = len(player_ids)
    match_results = {}
    matches = []
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            matches.append(f"{player_data[player_ids[i]]['Player']} vs {player_data[player_ids[j]]['Player']}")
    for pid in player_ids:
        match_results[player_data[pid]["Player"]] = {match: "-" for match in matches}
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            match_name = f"{data_i['Player']} vs {data_j['Player']}"
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            points_i, points_j = calc_match_points(
                data_i, data_j,
                handicap_ij, handicap_ji,
                is_total_only
            )
            match_results[data_i["Player"]][match_name] = f"{points_i:+d}" if points_i != 0 else "0"
            match_results[data_j["Player"]][match_name] = f"{points_j:+d}" if points_j != 0 else "0"
    return pd.DataFrame.from_dict(match_results, orient='index')

def highlight_total_only(row):
    if row["Total Only Mode"] == "Yes":
        return ['background-color: #FFD700; color: black'] * len(row)
    return ['background-color: #E6F3FF; color: black'] * len(row)

def color_points(val):
    try:
        if val == "":
            return "background-color: transparent; color: black"
        points = int(val)
        if points > 0:
            return 'background-color: #90EE90; color: black'
        elif points < 0:
            return 'background-color: #FFB6C6; color: black'
        return 'background-color: #F0F0F0; color: black'
    except:
        return "background-color: transparent; color: black"

def run():
    st.title("集計結果確認 (Game Pt + Match Pt + Put Pt)")
    session = SessionLocal()
    active_round = (
        session.query(Round)
        .filter_by(finalized=False)
        .order_by(Round.round_id.desc())
        .first()
    )
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return
    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")
    score_rows = (
        session.query(Score)
        .join(Member, Score.member_id == Member.member_id)
        .options(joinedload(Score.member))
        .filter(Score.round_id == active_round.round_id)
        .all()
    )
    if not score_rows:
        st.warning("No participants found for this round.")
        session.close()
        return
    handicap_matches = session.query(HandicapMatch).filter_by(round_id=active_round.round_id).all()
    handicaps = {}
    total_only_pairs = []
    for match in handicap_matches:
        p1 = match.player_1_id
        p2 = match.player_2_id
        handicaps[(p1, p2)] = match.player_1_to_2
        handicaps[(p2, p1)] = match.player_2_to_1
        if match.total_only:
            total_only_pairs.append((p1, p2))
    total_only_set = {frozenset(pair) for pair in total_only_pairs}
    session.close()
    player_data = {}
    for sc in score_rows:
        mid = sc.member_id
        fscore = sc.front_score or 0
        bscore = sc.back_score or 0
        escore = sc.extra_score or 0
        fgp = sc.front_game_pt or 0
        bgp = sc.back_game_pt or 0
        egp = sc.extra_game_pt or 0
        player_data[mid] = {
            "Player": sc.member.name,
            "Front Score": fscore,
            "Back Score": bscore,
            "Extra Score": escore,
            "Total Score": fscore + bscore,
            "Front GP": fgp,
            "Back GP": bgp,
            "Extra GP": egp,
            "Game Pt": 0,
            "Match Front": 0,
            "Match Back": 0,
            "Match Total": 0,
            "Match Extra": 0,
            "Match Pt": 0,
            "Putt Front": sc.front_putt or 0,
            "Putt Back": sc.back_putt or 0,
            "Put Pt": 0,
            "Total Pt": 0
        }
    player_ids = list(player_data.keys())
    n_players = len(player_ids)
    for mid in player_data:
        fgp = player_data[mid]["Front GP"]
        bgp = player_data[mid]["Back GP"]
        egp = player_data[mid]["Extra GP"]
        player_data[mid]["Game Pt"] = fgp + bgp + egp
    if n_players == 3:
        for mid in player_data:
            my_total = player_data[mid]["Game Pt"]
            others_total = sum(player_data[oid]["Game Pt"] for oid in player_data if oid != mid)
            player_data[mid]["Game Pt"] = my_total * 2 - others_total
    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            pair_key = frozenset([pid_i, pid_j])
            if pair_key in total_only_set:
                net_total_i = calc_net_total(data_i, handicaps.get((pid_j, pid_i), 0), multiplier=2)
                net_total_j = calc_net_total(data_j, handicaps.get((pid_i, pid_j), 0), multiplier=2)
                if net_total_i < net_total_j:
                    data_i["Match Total"] += 10
                    data_j["Match Total"] -= 10
                elif net_total_i > net_total_j:
                    data_i["Match Total"] -= 10
                    data_j["Match Total"] += 10
                if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
                    net_extra_i = calc_net_extra(data_i, handicaps.get((pid_j, pid_i), 0))
                    net_extra_j = calc_net_extra(data_j, handicaps.get((pid_i, pid_j), 0))
                    if net_extra_i < net_extra_j:
                        data_i["Match Extra"] += 10
                        data_j["Match Extra"] -= 10
                    elif net_extra_i > net_extra_j:
                        data_i["Match Extra"] -= 10
                        data_j["Match Extra"] += 10
            else:
                net_front_i = calc_net_score(data_i, "Front Score", handicaps.get((pid_j, pid_i), 0))
                net_front_j = calc_net_score(data_j, "Front Score", handicaps.get((pid_i, pid_j), 0))
                if net_front_i < net_front_j:
                    data_i["Match Front"] += 10
                    data_j["Match Front"] -= 10
                elif net_front_i > net_front_j:
                    data_i["Match Front"] -= 10
                    data_j["Match Front"] += 10
                if safe_get_score(data_i, "Back Score") > 0 and safe_get_score(data_j, "Back Score") > 0:
                    net_back_i = calc_net_score(data_i, "Back Score", handicaps.get((pid_j, pid_i), 0))
                    net_back_j = calc_net_score(data_j, "Back Score", handicaps.get((pid_i, pid_j), 0))
                    if net_back_i < net_back_j:
                        data_i["Match Back"] += 10
                        data_j["Match Back"] -= 10
                    elif net_back_i > net_back_j:
                        data_i["Match Back"] -= 10
                        data_j["Match Back"] += 10
                    net_total_i = calc_net_total(data_i, handicaps.get((pid_j, pid_i), 0), multiplier=2)
                    net_total_j = calc_net_total(data_j, handicaps.get((pid_i, pid_j), 0), multiplier=2)
                    if net_total_i < net_total_j:
                        data_i["Match Total"] += 10
                        data_j["Match Total"] -= 10
                    elif net_total_i > net_total_j:
                        data_i["Match Total"] -= 10
                        data_j["Match Total"] += 10
                if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
                    net_extra_i = calc_net_extra(data_i, handicaps.get((pid_j, pid_i), 0))
                    net_extra_j = calc_net_extra(data_j, handicaps.get((pid_i, pid_j), 0))
                    if net_extra_i < net_extra_j:
                        data_i["Match Extra"] += 10
                        data_j["Match Extra"] -= 10
                    elif net_extra_i > net_extra_j:
                        data_i["Match Extra"] -= 10
                        data_j["Match Extra"] += 10
    for mid in player_data:
        data = player_data[mid]
        data["Match Pt"] = data["Match Front"] + data["Match Back"] + data["Match Total"] + data["Match Extra"]
    front_putt = {mid: player_data[mid]["Putt Front"] for mid in player_data}
    back_putt = {mid: player_data[mid]["Putt Back"] for mid in player_data}
    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points = calc_putt_points(back_putt, n_players)
    for mid in player_data:
        data = player_data[mid]
        pf = putt_front_points.get(mid, 0)
        pb = putt_back_points.get(mid, 0)
        data["Put Pt"] = pf + pb
    for mid in player_data:
        d = player_data[mid]
        total_pt = d["Game Pt"] + d["Match Pt"] + d["Put Pt"]
        d["Total Pt"] = total_pt
    result_data = []
    for mid, d in player_data.items():
        result_data.append({
            "Player": d["Player"],
            "Front Score": d["Front Score"],
            "Back Score": d["Back Score"],
            "Extra Score": d["Extra Score"],
            "Front GP": d["Front GP"],
            "Back GP": d["Back GP"],
            "Extra GP": d["Extra GP"],
            "Game Pt": d["Game Pt"],
            "Match Front": d["Match Front"],
            "Match Back": d["Match Back"],
            "Match Total": d["Match Total"],
            "Match Extra": d["Match Extra"],
            "Match Pt": d["Match Pt"],
            "Put Pt": d["Put Pt"],
            "Total Pt": d["Total Pt"],
        })
    final_df = pd.DataFrame(result_data)
    st.write("### 最終結果（Game Pt + Match Pt + Put Pt ＝ Total Pt）")
    st.markdown("""
        <style>
            .dataframe-container {
                width: 100%;
                overflow-x: auto !important;
            }
            .dataframe {
                margin: 0 !重要;
            }
            .dataframe th:first-child,
            .dataframe td:first-child {
                position: sticky !important;
                left: 0 !important;
                background-color: white !重要;
                z-index: 1 !重要;
                border-right: 2px solid #ccc !重要;
            }
            .index_col {
                display: none !重要;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="dataframe-container">
            {final_df.to_html(classes='dataframe', index=False)}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("### マッチ戦詳細結果")
    detailed_df = create_detailed_match_results(player_data, handicaps, total_only_set)
    st.markdown("""
        <style>
            .match-details-container {
                width: 100%;
                overflow-x: auto !important;
            }
            .match-details {
                margin: 0 !重要;
            }
            .match-details th:first-child,
            .match-details td:first-child {
                position: sticky !important;
                left: 0 !重要;
                background-color: white !重要;
                z-index: 1 !重要;
                border-right: 2px solid #ccc !重要;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="match-details-container">
            {detailed_df.style.map(color_points).to_html(classes='match-details', index=False)}
        </div>
        """,
        unsafe_allow_html=True
    )
    star_df = create_match_matrix(player_data, handicaps, total_only_set)
    st.write("### 対戦結果（Much Pt 集計）")
    st.dataframe(star_df.style.map(color_points))
    pdf_buffer = generate_pdf(final_df, detailed_df, star_df)
    st.download_button(
        label="Download PDF of Results",
        data=pdf_buffer,
        file_name="golf_round_results.pdf",
        mime="application/pdf"
    )
    if st.button("Finalize Results"):
        sess = SessionLocal()
        sess.query(Round).filter(Round.round_id == active_round.round_id).update({Round.finalized: True})
        sess.commit()
        sess.close()
        st.success("Results have been finalized.")
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.info("Page rerun is not supported in this Streamlit version. Please refresh the page manually.")

if __name__ == "__main__":
    run()
