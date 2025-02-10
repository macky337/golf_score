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
def convert_to_paragraphs(data, style):
    """テーブルデータの文字列をParagraphオブジェクトに変換"""
    if isinstance(data, list):
        return [[Paragraph(str(cell), style) if isinstance(cell, (str, int, float)) else cell 
                for cell in row] for row in data]
    return data

def create_df_for_pdf(df):
    """DataFrameをPDF用に整形する"""
    style = ParagraphStyle(
        'Normal',
        fontName=FONT_NAME,
        fontSize=10,
        leading=12,
        alignment=1
    )
    
    formatted_data = []
    
    # インデックス（プレイヤー名）を含むヘッダー行の作成
    headers = [Paragraph('Player', style)] + [Paragraph(str(col), style) for col in df.columns]
    formatted_data.append(headers)
    
    # データ行の作成（プレイヤー名を含む）
    for idx, row in df.iterrows():
        formatted_row = [Paragraph(str(idx), style)]  # プレイヤー名
        for val in row:
            if pd.isna(val):
                val = ""
            if isinstance(val, (int, float)):
                val = f"{val:+d}" if val != 0 else "0"
            formatted_row.append(Paragraph(str(val), style))
        formatted_data.append(formatted_row)
    
    return formatted_data

def get_round_date_attr():
    """Roundモデルで利用可能な日付属性を返す。
    優先順位: play_date > date > round_date > created_at
    """
    for attr in ['play_date', 'date', 'round_date', 'created_at']:
        if hasattr(Round, attr):
            return getattr(Round, attr)
    return None

def get_play_date(active_round):
    """active_roundからプレイ日を取得する"""
    for attr in ['play_date', 'date', 'round_date', 'created_at']:
        if hasattr(active_round, attr) and getattr(active_round, attr) is not None:
            return getattr(active_round, attr)
    # すべてなしの場合、現在の日付を返す
    return datetime.date.today()

def generate_pdf(final_df, detailed_df, star_df, active_round):
    """PDFレポートを生成する"""
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
    
    # メインタイトルのスタイル定義
    main_title_style = ParagraphStyle(
        'MainTitle',
        fontName=FONT_NAME,
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=10
    )

    # サブタイトルのスタイル
    title_style = ParagraphStyle(
        'Title',
        fontName=FONT_NAME,
        fontSize=14,
        leading=16,
        alignment=1
    )

    # プレイ日を取得
    play_date = get_play_date(active_round).strftime('%Y年%m月%d日')
    course_name = active_round.course_name if hasattr(active_round, 'course_name') else ''
    
    # タイトル行を追加
    elements.append(Paragraph(f"{play_date} {course_name} スコア集計結果", main_title_style))
    elements.append(Spacer(1, 20))

    # セクション1: 最終結果
    elements.append(Paragraph("最終結果（Game Pt + Match Pt + Put Pt ＝ Total Pt）", title_style))
    elements.append(Spacer(1, 12))
    
    final_data = create_df_for_pdf(final_df.set_index('Player'))
    col_widths = [landscape(letter)[0] / len(final_data[0])] * len(final_data[0])
    t1 = Table(final_data, colWidths=col_widths)
    t1.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 20))

    # セクション2: マッチ戦詳細結果
    elements.append(Paragraph("マッチ戦詳細結果", title_style))
    elements.append(Spacer(1, 12))
    
    detailed_data = create_df_for_pdf(detailed_df)  # インデックスを保持
    col_widths = [landscape(letter)[0] / len(detailed_data[0])] * len(detailed_data[0])
    t2 = Table(detailed_data, colWidths=col_widths)
    t2.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 20))

    # セクション3: 対戦表
    elements.append(Paragraph("対戦結果（Much Pt 集計）", title_style))
    elements.append(Spacer(1, 12))
    
    star_data = create_df_for_pdf(star_df)  # インデックスを保持
    col_widths = [landscape(letter)[0] / len(star_data[0])] * len(star_data[0])
    t3 = Table(star_data, colWidths=col_widths)
    t3.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t3)

    doc.build(elements)
    buffer.seek(0)
    return buffer

def calc_putt_points(putt_scores, n):
    """パット戦の得点計算（4人 or 3人の場合）
    
    4人の場合:
      - 1名のみが最少 → 最少者+30pt、残り3名-10pt
      - 2名同点最少 → 最少2名+10pt、残り2名-10pt
      - 3名同点最少 → 最少3名+10pt、残り1名-30pt
      - 全員同点 → 0pt
      
    3人の場合:
      - 1名のみが最少 → 最少者+20pt、残り2名-10pt
      - 2名同点最少 → 最少2名+5pt、残り1名-10pt
      - 全員同点 → 0pt
    """
    if not putt_scores:  # スコアが空の場合
        return {}
        
    scores = list(putt_scores.values())
    min_score = min(scores)
    winners = [m_id for m_id, score in putt_scores.items() if score == min_score]
    points = {m_id: 0 for m_id in putt_scores}
    
    if n == 3:
        if len(winners) == 1:
            points[winners[0]] = 20  # 最少が1名の場合は+20pt
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10  # 残り2名は-10pt
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 5  # 最少が2名の場合は+5pt
                else:
                    points[m_id] = -10  # 残り1名は-10pt
        # 全員同点の場合は初期値の0のまま
    
    elif n == 4:
        if len(winners) == 1:
            points[winners[0]] = 30  # 最少が1名の場合は+30pt
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10  # 残り3名は-10pt
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10  # 最少が2名の場合は+10pt
                else:
                    points[m_id] = -10  # 残り2名は-10pt
        elif len(winners) == 3:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10  # 最少が3名の場合は+10pt
                else:
                    points[m_id] = -30  # 残り1名は-30pt
        # 全員同点の場合は初期値の0のまま
    
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
    multi_columns = []  # マルチインデックス用のリスト

    # 対戦カードとハンディキャップ情報を収集
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            match_name = f"{player_data[player_ids[i]]['Player']} vs {player_data[player_ids[j]]['Player']}"
            matches.append(match_name)
            handicap_ij = handicaps.get((player_ids[j], player_ids[i]), 0)
            handicap_ji = handicaps.get((player_ids[i], player_ids[j]), 0)
            handicap_str = f"{handicap_ij} vs {handicap_ji}"
            multi_columns.append((match_name, handicap_str))

    # プレイヤーごとの結果を初期化
    for pid in player_ids:
        match_results[player_data[pid]["Player"]] = {match: "-" for match in matches}

    # 対戦結果を計算して格納
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

    # DataFrameを作成し、マルチインデックスを設定
    df = pd.DataFrame.from_dict(match_results, orient='index')
    df.columns = pd.MultiIndex.from_tuples(multi_columns, names=['Match', 'Handicap'])
    
    return df

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

def get_pdf_filename(active_round):
    """PDFファイル名を生成する
    
    Format: YYYYMMDD_golf_results.pdf
    例: 20250209_golf_results.pdf
    """
    return f"{get_play_date(active_round).strftime('%Y%m%d')}_golf_results.pdf"

def run():
    st.title("集計結果確認 (Game Pt + Match Pt + Put Pt)")
    session = SessionLocal()
    
    date_attr = get_round_date_attr()
    if date_attr is None:
        st.error("Roundモデルに日付属性が定義されていません。")
        session.close()
        return

    # Roundモデルの日付属性を利用して全ラウンドデータを取得
    all_rounds = (
        session.query(Round)
        .order_by(date_attr.desc())  # 日付の新しい順
        .all()
    )
    
    # ラウンド選択の際、各Roundオブジェクトから表示用日付を取得
    round_options = []
    for rnd in all_rounds:
        # 優先順位: play_date > date > round_date
        for attr in ['play_date', 'date', 'round_date']:
            if hasattr(rnd, attr) and getattr(rnd, attr) is not None:
                round_date = getattr(rnd, attr)
                break
        else:
            round_date = None
        if round_date:
            option = f"{round_date.strftime('%Y-%m-%d')} - {rnd.course_name} (ID: {rnd.round_id})"
        else:
            option = f"未設定日付 - {rnd.course_name} (ID: {rnd.round_id})"
        round_options.append(option)
    
    selected_round_str = st.selectbox(
        "ラウンドを選択してください",
        options=round_options,
        index=0 if round_options else None
    )
    
    if selected_round_str:
        # 選択されたラウンドIDを抽出
        round_id = int(selected_round_str.split("ID: ")[1].rstrip(")"))
        
        active_round = (
            session.query(Round)
            .filter_by(round_id=round_id)
            .first()
        )
        
        if not active_round:
            st.warning("選択されたラウンドが見つかりません。")
            session.close()
            return
        
        # 表示用日付を取得（先ほどの優先順位を使用）
        play_date = get_play_date(active_round)
        st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}, **Date**: {play_date.strftime('%Y-%m-%d')}")
        
        # スコアデータの取得
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

        # ハンディキャップデータの取得と設定
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

        # DBから全Memberを取得して辞書を作成
        member_dict = {m.member_id: m.name for m in session.query(Member).all()}

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

        # Game Ptの計算部分を修正
        # まず、各プレイヤーのGame Ptを算出（Front GP + Back GP + Extra GP）
        for mid in player_data:
            fgp = player_data[mid]["Front GP"]
            bgp = player_data[mid]["Back GP"]
            egp = player_data[mid]["Extra GP"]
            player_data[mid]["Game Pt"] = fgp + bgp + egp

        # 3人の場合、各プレイヤーの最終Game Ptを再計算
        if n_players == 3:
            # 元のGame Ptを退避
            original_game_pts = {mid: player_data[mid]["Game Pt"] for mid in player_data}
            for mid in player_data:
                my_total = original_game_pts[mid]
                others_total = sum(original_game_pts[oid] for oid in original_game_pts if oid != mid)
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
        # パットポイントの計算部分を修正
        front_putt = {mid: player_data[mid]["Putt Front"] for mid in player_data}
        back_putt = {mid: player_data[mid]["Putt Back"] for mid in player_data}
        extra_putt = {mid: safe_get_score(player_data[mid], "Putt Extra") 
                      for mid in player_data 
                      if safe_get_score(player_data[mid], "Extra Score") > 0}

        # Front, Back, Extraそれぞれのパットポイントを計算
        putt_front_points = calc_putt_points(front_putt, n_players)
        putt_back_points = calc_putt_points(back_putt, n_players)
        putt_extra_points = calc_putt_points(extra_putt, n_players) if extra_putt else {mid: 0 for mid in player_data}

        # 各プレイヤーのパットポイント合計を計算
        for mid in player_data:
            data = player_data[mid]
            pf = putt_front_points.get(mid, 0)
            pb = putt_back_points.get(mid, 0)
            pe = putt_extra_points.get(mid, 0)
            data["Put Pt"] = pf + pb + pe  # Front + Back + Extra の合計

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
                    left: 0 !重要;
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
                    overflow-x: auto !重要;
                }
                .match-details {
                    margin: 0 !重要;
                }
                .match-details th:first-child,
                .match-details td:first-child {
                    position: sticky !重要;
                    left: 0 !重要;
                    background-color: white !重要;
                    z-index: 1 !重要;
                    border-right: 2px solid #ccc !重要;
                }
            </style>
        """, unsafe_allow_html=True)

        # detailed_df をフラットなカラム名に変換してから表示
        detailed_df_flat = detailed_df.copy()
        # 例: "Player vs Player (handicap_ij vs handicap_ji)" の形式に変換
        detailed_df_flat.columns = [f"{m}\n({h})" for m, h in detailed_df_flat.columns]

        st.markdown(
            f"""
            <div class="match-details-container">
                {detailed_df_flat.style.map(color_points).to_html(classes='match-details', index=True)}
            </div>
            """,
            unsafe_allow_html=True
        )
        star_df = create_match_matrix(player_data, handicaps, total_only_set)
        st.write("### 対戦結果（Much Pt 集計）")
        st.dataframe(star_df.style.map(color_points))
        pdf_buffer = generate_pdf(final_df, detailed_df, star_df, active_round)
        st.download_button(
            label="Download PDF of Results",
            data=pdf_buffer,
            file_name=get_pdf_filename(active_round),  # ここを変更
            mime="application/pdf"
        )

        # ★ DB に計算結果を保存する処理 ★
        for sc in score_rows:
            mid = sc.member_id
            if mid in player_data:
                sc.match_front = player_data[mid]["Match Front"]
                sc.match_back = player_data[mid]["Match Back"]
                sc.match_total = player_data[mid]["Match Total"]
                sc.match_extra = player_data[mid]["Match Extra"]
                sc.match_pt = player_data[mid]["Match Pt"]
                sc.put_pt = player_data[mid]["Put Pt"]
                sc.total_pt = player_data[mid]["Total Pt"]
        session.commit()
        session.expire_all()  # キャッシュをクリアして再取得できるようにする

        # ★ ラウンド設定およびハンディキャップ設定変更用フォーム ★
        if not active_round.finalized:
            with st.form("round_update_form"):
                st.header("ラウンド設定・ハンディキャップ設定の変更")
                new_course_name = st.text_input("コース名", value=active_round.course_name)
                new_date_played = st.date_input("プレイ日", value=active_round.date_played)
                st.subheader("【ハンディキャップ設定の変更】")
                updated_handicap = {}
                # 重複する対戦を除外するためのセットを用意
                processed_matches = set()
                # 各ハンディキャップ設定の変更項目を表示
                for match in handicap_matches:
                    key = frozenset({match.player_1_id, match.player_2_id})
                    if key in processed_matches:
                        continue
                    processed_matches.add(key)
                    # Player名を取得（存在しない場合はIDを文字列で表示）
                    p1_name = member_dict.get(match.player_1_id, str(match.player_1_id))
                    p2_name = member_dict.get(match.player_2_id, str(match.player_2_id))
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**対戦:** {p1_name} vs {p2_name}")
                        new_p1 = st.number_input(f"{p1_name}→{p2_name}", 
                                                   min_value=-100, max_value=100, step=1, 
                                                   value=match.player_1_to_2, key=f"p1_{match.id}")
                    with col2:
                        new_p2 = st.number_input(f"{p2_name}→{p1_name}", 
                                                   min_value=-100, max_value=100, step=1, 
                                                   value=match.player_2_to_1, key=f"p2_{match.id}")
                    with col3:
                        new_total_only = st.checkbox("Total Only", value=match.total_only, key=f"tot_{match.id}")
                    updated_handicap[match.id] = {
                        "player_1_to_2": new_p1,
                        "player_2_to_1": new_p2,
                        "total_only": new_total_only
                    }
                update_submit = st.form_submit_button("設定を更新する")
                if update_submit:
                    # ラウンド設定更新
                    active_round.course_name = new_course_name
                    active_round.date_played = new_date_played
                    active_round.date = new_date_played  # dateも同様に更新（必要に応じて）
                    # 各ハンディキャップ設定の更新
                    for match in handicap_matches:
                        updated = updated_handicap.get(match.id)
                        if updated:
                            match.player_1_to_2 = updated["player_1_to_2"]
                            match.player_2_to_1 = updated["player_2_to_1"]
                            match.total_only = updated["total_only"]
                    session.commit()
                    st.success("ラウンド設定とハンディキャップ設定が更新されました.")

            # ★ Finalize ボタンはフォームの外で表示する ★
            if st.button("Finalize Results"):
                active_round.finalized = True
                session.commit()
                st.success("Results have been finalized.")
                st.rerun()
    
    session.close()

if __name__ == "__main__":
    run()

