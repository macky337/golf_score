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
                            rightMargin=20, leftMargin=20,
                            topMargin=20, bottomMargin=20)
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
    available_width = landscape(letter)[0] - 40
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

    # 星取表
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
            # 1人勝ち → +30, 他3人 -10
            points[winners[0]] = 30
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10
        elif len(winners) == 2:
            # 2人同点勝ち → その2人 +10, 他2人 -10
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10
                else:
                    points[m_id] = -10
        elif len(winners) == 3:
            # 3人同点勝ち → その3人 +10, 残り1人 -30
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10
                else:
                    points[m_id] = -30
        else:
            # 全員同点 → 0
            pass
    elif n == 3:
        if len(winners) == 1:
            # 1人勝ち → +20, 他2人 -20
            points[winners[0]] = 20
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -20
        elif len(winners) == 2:
            # 2人同点勝ち → 勝ち組 +10, 残り1人 -20
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10
                else:
                    points[m_id] = -20
        else:
            # 全員同点 → 0
            pass
    return points


def calc_match_points(data_i, data_j, handicap_ij, handicap_ji, is_total_only=False):
    """1対1のマッチポイント計算（各セクション±10pt）"""
    front_pt = back_pt = total_pt = extra_pt = 0
    
    if is_total_only:
        # Total Score の判定時はハンディを2倍にする
        total_i = (data_i["Front Score"] + data_i["Back Score"]) - (handicap_ij * 2)
        total_j = (data_j["Front Score"] + data_j["Back Score"]) - (handicap_ji * 2)
        if total_i < total_j:
            total_pt = 10
        elif total_i > total_j:
            total_pt = -10
            
        # Extra は通常のハンディで判定
        if data_i["Extra Score"] > 0 or data_j["Extra Score"] > 0:
            extra_i = data_i["Extra Score"] - handicap_ij
            extra_j = data_j["Extra Score"] - handicap_ji
            if extra_i < extra_j:
                extra_pt = 10
            elif extra_i > extra_j:
                extra_pt = -10
        
        # Total Only の場合は Front/Back は0
        front_pt = 0
        back_pt = 0
        
    else:
        # Front/Back はそれぞれハーフのハンディで判定
        front_i = data_i["Front Score"] - handicap_ij
        front_j = data_j["Front Score"] - handicap_ji
        if front_i < front_j:
            front_pt = 10
        elif front_i > front_j:
            front_pt = -10

        if data_i["Back Score"] > 0 and data_j["Back Score"] > 0:
            back_i = data_i["Back Score"] - handicap_ij
            back_j = data_j["Back Score"] - handicap_ji
            if back_i < back_j:
                back_pt = 10
            elif back_i > back_j:
                back_pt = -10

            # Total はハンディを2倍にして判定
            total_i = (data_i["Front Score"] + data_i["Back Score"]) - (handicap_ij * 2)
            total_j = (data_j["Front Score"] + data_j["Back Score"]) - (handicap_ji * 2)
            if total_i < total_j:
                total_pt = 10
            elif total_i > total_j:
                total_pt = -10

        # Extra は通常のハンディで判定
        if data_i["Extra Score"] > 0 or data_j["Extra Score"] > 0:
            extra_i = data_i["Extra Score"] - handicap_ij
            extra_j = data_j["Extra Score"] - handicap_ji
            if extra_i < extra_j:
                extra_pt = 10
            elif extra_i > extra_j:
                extra_pt = -10

    # Player 1の視点でのポイントを設定
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
    
    # 初期化
    for i in range(len(player_ids)):
        name_i = player_data[player_ids[i]]["Player"]
        for j in range(len(player_ids)):
            name_j = player_data[player_ids[j]]["Player"]
            if i == j:
                match_matrix.loc[name_i, name_j] = ""
            else:
                match_matrix.loc[name_i, name_j] = "0"
    
    # 対戦結果を記入
    for i in range(len(player_ids)):
        pid_i = player_ids[i]
        name_i = player_data[pid_i]["Player"]
        for j in range(i + 1, len(player_ids)):
            pid_j = player_ids[j]
            name_j = player_data[pid_j]["Player"]
            
            # ハンディキャップの取得
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            
            # Total Only かどうかの判定
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            
            # マッチポイントの計算
            points_i, points_j = calc_match_points(
                player_data[pid_i], 
                player_data[pid_j],
                handicap_ij,
                handicap_ji,
                is_total_only
            )
            
            # 星取表に記入
            match_matrix.loc[name_i, name_j] = f"{points_i:+d}"
            match_matrix.loc[name_j, name_i] = f"{points_j:+d}"
            
    return match_matrix

# マッチ戦詳細結果の表示部分を修正
def create_detailed_match_results(player_data, handicaps, total_only_set):
    """マッチ戦の詳細結果を作成（横：対戦カード、縦：プレイヤーのポイント）"""
    player_ids = list(player_data.keys())
    n_players = len(player_ids)
    match_results = {}
    
    # 対戦カード（列）の作成
    matches = []
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            matches.append(f"{player_data[player_ids[i]]['Player']} vs {player_data[player_ids[j]]['Player']}")
    
    # プレイヤーごとの対戦結果を格納
    for pid in player_ids:
        match_results[player_data[pid]["Player"]] = {match: "-" for match in matches}
    
    # 対戦結果の計算と格納
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            match_name = f"{data_i['Player']} vs {data_j['Player']}"
            
            # ハンディキャップの取得
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            
            # マッチポイントの計算
            points_i, points_j = calc_match_points(
                data_i, data_j,
                handicap_ij, handicap_ji,
                is_total_only
            )
            
            # 結果を格納
            match_results[data_i["Player"]][match_name] = f"{points_i:+d}" if points_i != 0 else "0"
            match_results[data_j["Player"]][match_name] = f"{points_j:+d}" if points_j != 0 else "0"
    
    return pd.DataFrame.from_dict(match_results, orient='index')

def highlight_total_only(row):
    """Total Onlyモードの行の背景色とテキストカラーを設定"""
    if row["Total Only Mode"] == "Yes":
        # Total Only の場合：濃い黄色背景で黒テキスト
        return ['background-color: #FFD700; color: black'] * len(row)
    # 通常の場合：薄い青背景で黒テキスト
    return ['background-color: #E6F3FF; color: black'] * len(row)

def color_points(val):
    """点数表示のスタイリング"""
    try:
        if val == "":
            return "background-color: transparent; color: black"
        points = int(val)
        if points > 0:
            # プラスポイント：緑背景で黒テキスト
            return 'background-color: #90EE90; color: black'
        elif points < 0:
            # マイナスポイント：ピンク背景で黒テキスト
            return 'background-color: #FFB6C6; color: black'
        # ゼロ：グレー背景で黒テキスト
        return 'background-color: #F0F0F0; color: black'
    except:
        return "background-color: transparent; color: black"

def run():
    st.title("集計結果確認 (Game Pt + Match Pt + Put Pt)")
    session = SessionLocal()
    
    # 1) 未確定ラウンドの取得
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

    # 2) スコアの取得 (joinedload により member を同時取得)
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

    # 3) ハンディキャップとtotal_onlyの取得
    handicap_matches = session.query(HandicapMatch).filter_by(round_id=active_round.round_id).all()
    handicaps = {}
    total_only_pairs = []  # total_only のペアを保存するリスト
    
    for match in handicap_matches:
        p1 = match.player_1_id
        p2 = match.player_2_id
        handicaps[(p1, p2)] = match.player_1_to_2
        handicaps[(p2, p1)] = match.player_2_to_1
        
        # total_only が True の場合、ペアをリストに追加
        if match.total_only:
            total_only_pairs.append((p1, p2))

    # total_only_pairs を frozenset に変換
    total_only_set = {frozenset(pair) for pair in total_only_pairs}

    session.close()

    # 4) player_dataを構築
    player_data = {}
    for sc in score_rows:
        mid = sc.member_id
        if mid not in player_data:
            player_data[mid] = {}
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
            # sum for total
            "Total Score": fscore + bscore,
            # game pt input
            "Front GP": fgp,
            "Back GP": bgp,
            "Extra GP": egp,
            "Game Pt": 0,       # 後で計算
            # match
            "Match Front": 0,
            "Match Back": 0,
            "Match Total": 0,
            "Match Extra": 0,
            "Match Pt": 0,
            # putt
            "Putt Front": sc.front_putt or 0,
            "Putt Back": sc.back_putt or 0,
            "Put Pt": 0,
            # final total
            "Total Pt": 0
        }

    player_ids = list(player_data.keys())
    n_players = len(player_ids)

    # ========== (A) Game Pt 計算 ==========
    # 各プレイヤーのトータルGame Ptを計算
    for mid in player_data:
        fgp = player_data[mid]["Front GP"]
        bgp = player_data[mid]["Back GP"]
        egp = player_data[mid]["Extra GP"]
        # Game Ptはそのまま合計値を使用
        player_data[mid]["Game Pt"] = fgp + bgp + egp

    # プレイヤー数に応じた補正
    if n_players == 3:
        # 3人の場合：自分の合計×2から他プレイヤーの合計を引く
        for mid in player_data:
            my_total = player_data[mid]["Game Pt"]
            others_total = sum(
                player_data[oid]["Game Pt"] 
                for oid in player_data 
                if oid != mid
            )
            player_data[mid]["Game Pt"] = my_total * 2 - others_total
    # 4人の場合は合計値をそのまま使用（補正なし）

    # ========== (B) Match Pt 計算 ==========

    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            pair_key = frozenset([pid_i, pid_j])

            if pair_key in total_only_set:
                net_total_i = (data_i["Front Score"] + data_i["Back Score"]) - (handicaps.get((pid_j, pid_i), 0) * 2)
                net_total_j = (data_j["Front Score"] + data_j["Back Score"]) - (handicaps.get((pid_i, pid_j), 0) * 2)
                if net_total_i < net_total_j:
                    data_i["Match Total"] += 10
                    data_j["Match Total"] -= 10
                elif net_total_i > net_total_j:
                    data_i["Match Total"] -= 10
                    data_j["Match Total"] += 10

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
                net_front_i = data_i["Front Score"] - handicaps.get((pid_j, pid_i), 0)
                net_front_j = data_j["Front Score"] - handicaps.get((pid_i, pid_j), 0)
                if net_front_i < net_front_j:
                    data_i["Match Front"] += 10
                    data_j["Match Front"] -= 10
                elif net_front_i > net_front_j:
                    data_i["Match Front"] -= 10
                    data_j["Match Front"] += 10

                if data_i["Back Score"] > 0 and data_j["Back Score"] > 0:
                    net_back_i = data_i["Back Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_back_j = data_j["Back Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_back_i < net_back_j:
                        data_i["Match Back"] += 10
                        data_j["Match Back"] -= 10
                    elif net_back_i > net_back_j:
                        data_i["Match Back"] -= 10
                        data_j["Match Back"] += 10

                    net_total_i = (data_i["Front Score"] + data_i["Back Score"]) - (handicaps.get((pid_j, pid_i), 0) * 2)
                    net_total_j = (data_j["Front Score"] + data_j["Back Score"]) - (handicaps.get((pid_i, pid_j), 0) * 2)
                    if net_total_i < net_total_j:
                        data_i["Match Total"] += 10
                        data_j["Match Total"] -= 10
                    elif net_total_i > net_total_j:
                        data_i["Match Total"] -= 10
                        data_j["Match Total"] += 10

                if data_i["Extra Score"] > 0 or data_j["Extra Score"] > 0:
                    net_extra_i = data_i["Extra Score"] - handicaps.get((pid_j, pid_i), 0)
                    net_extra_j = data_j["Extra Score"] - handicaps.get((pid_i, pid_j), 0)
                    if net_extra_i < net_extra_j:
                        data_i["Match Extra"] += 10
                        data_j["Match Extra"] -= 10
                    elif net_extra_i > net_extra_j:
                        data_i["Match Extra"] -= 10
                        data_j["Match Extra"] += 10

    for mid in player_data:
        data = player_data[mid]
        data["Match Pt"] = data["Match Front"] + data["Match Back"] + data["Match Total"] + data["Match Extra"]

    # ========== (C) パット戦 Put Pt 計算 ============
    front_putt = {mid: player_data[mid]["Putt Front"] for mid in player_data}
    back_putt = {mid: player_data[mid]["Putt Back"] for mid in player_data}

    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points = calc_putt_points(back_putt, n_players)

    for mid in player_data:
        data = player_data[mid]
        pf = putt_front_points.get(mid, 0)
        pb = putt_back_points.get(mid, 0)
        data["Put Pt"] = pf + pb

    # ========== (D) 最終合計 ==========
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
    
    # 最終結果の表示部分を修正
    st.write("### 最終結果（Game Pt + Match Pt + Put Pt ＝ Total Pt）")
    
    # カスタムCSSを適用
    st.markdown("""
        <style>
            .dataframe-container {
                width: 100%;
                overflow-x: auto !important;
            }
            
            .dataframe {
                margin: 0 !重要;
            }
            
            /* Player列の固定表示 */
            .dataframe th:first-child,
            .dataframe td:first-child {
                position: sticky !important;
                left: 0 !important;
                background-color: white !重要;
                z-index: 1 !重要;
                border-right: 2px solid #ccc !重要;
            }
            
            /* インデックス列の非表示 */
            .index_col {
                display: none !重要;
            }
        </style>
    """, unsafe_allow_html=True)

    # データフレームをHTMLとして表示
    st.markdown(
        f"""
        <div class="dataframe-container">
            {final_df.to_html(classes='dataframe', index=False)}
        </div>
        """,
        unsafe_allow_html=True
    )

    # マッチ戦の詳細結果を表示
    st.write("### マッチ戦詳細結果")
    detailed_df = create_detailed_match_results(player_data, handicaps, total_only_set)
    
    # プレーヤー列を固定表示するためのカスタムCSS
    st.markdown("""
        <style>
            .match-details-container {
                width: 100%;
                overflow-x: auto !important;
            }
            
            .match-details {
                margin: 0 !important;
            }
            
            /* Player列の固定表示 */
            .match-details th:first-child,
            .match-details td:first-child {
                position: sticky !important;
                left: 0 !important;
                background-color: white !important;
                z-index: 1 !important;
                border-right: 2px solid #ccc !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # マッチ戦詳細結果の表示（color_pointsのみ適用）
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
    
    # スタイル適用部分を修正
    st.dataframe(star_df.style.map(color_points))

    pdf_buffer = generate_pdf(final_df, star_df)
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
        st.experimental_rerun()




if __name__ == "__main__":
    run()