import streamlit as st
import pandas as pd
from modules.db import supabase
import datetime
import io
import os
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from streamlit_extras.switch_page_button import switch_page

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
        for col, val in zip(df.columns, row):
            if pd.isna(val):
                val = ""
            # スコア関連のカラムは+記号なしで表示
            if col in ['Front Score', 'Back Score', 'Total Score', 'Extra Score']:
                if isinstance(val, (int, float)):
                    val = f"{int(val)}"
            # その他のカラムは従来通り+記号付きで表示
            else:
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
    """active_roundからプレイ日を取得"""
    if not active_round:
        return None
    if hasattr(active_round, 'date_played') and active_round.date_played:
        return active_round.date_played
    return None

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

    # プレイ日とコース名を取得
    play_date = active_round.date_played.strftime('%Y年%m月%d日')
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
    """Total Only Modeがデータにない場合はスタイリングを適用しない"""
    try:
        if "Total Only Mode" in row and row["Total Only Mode"] == "Yes":
            return ['background-color: #FFD700; color: black'] * len(row)
    except:
        pass
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
    """PDFファイル名を生成"""
    play_date = active_round.date_played.strftime('%Y%m%d')
    round_id = active_round.round_id
    return f"{play_date}_Round{round_id}_golf_results.pdf"

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("結果確認")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")

    # 未確定ラウンドの存在チェック
    rounds_result = supabase.table('rounds').select('*').eq('finalized', False).order('date_played', desc=True).execute()
    unfinalized_rounds = rounds_result.data

    # すべてのラウンドを取得（date_playedで降順ソート）
    all_rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    all_rounds = all_rounds_result.data
    
    # 未確定ラウンドがある場合は警告表示
    if unfinalized_rounds:
        st.warning(f"⚠️ 未確定のラウンドが {len(unfinalized_rounds)} 件あります")
        # 未確定ラウンドの一覧を表示
        for r in unfinalized_rounds:
            st.info(f"📝 {r['date_played']} - {r['course_name']} (ID: {r['round_id']})")
    
    # ラウンド選択オプションの作成
    round_options = [
        f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})"
        for r in all_rounds
    ]
    
    # 未確定ラウンドがある場合、最新の未確定ラウンドを初期選択に設定
    default_index = 0
    if unfinalized_rounds:
        default_round = unfinalized_rounds[0]
        default_str = f"{default_round['date_played']} - {default_round['course_name']} (ID: {default_round['round_id']})"
        default_index = round_options.index(default_str)
    
    selected_round_str = st.selectbox(
        "ラウンドを選択してください",
        options=round_options,
        index=default_index if round_options else None
    )
    
    if selected_round_str:
        # 選択されたラウンドIDを抽出
        round_id = int(selected_round_str.split("ID: ")[1].rstrip(")"))
        
        # ラウンド情報を取得
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        active_round = round_result.data[0] if round_result.data else None
        
        if not active_round:
            st.warning("選択されたラウンドが見つかりません。")
            return

        # スコアデータの取得
        scores_result = supabase.table('score').select(
            '*, member(name)'
        ).eq('round_id', round_id).execute()
        scores = scores_result.data

        # ハンディキャップデータの取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data

        if not scores:
            st.warning("スコアデータが見つかりません。")
            return

        # プレーヤーデータの準備
        player_data = {}
        for sc in scores:
            player_data[sc['member_id']] = {
                "Player": sc['member']['name'],
                "Front Score": sc['front_score'],
                "Back Score": sc['back_score'],
                "Extra Score": sc['extra_score'],
                "Total Score": sc['front_score'] + sc['back_score'],
                "Front GP": sc.get('front_game_pt', 0),
                "Back GP": sc.get('back_game_pt', 0),
                "Extra GP": sc.get('extra_game_pt', 0),
                "Game Pt": 0,
                "Match Front": 0,
                "Match Back": 0,
                "Match Total": 0,
                "Match Extra": 0,
                "Match Pt": sc.get('match_pt', 0),
                "Putt Front": sc['front_putt'] or 0,
                "Putt Back": sc['back_putt'] or 0,
                "Put Pt": sc.get('put_pt', 0),
                "Total Pt": sc.get('total_pt', 0)
            }

        player_ids = list(player_data.keys())
        n_players = len(player_ids)

        # ハンディキャップの準備（リストから辞書に変換）
        handicaps = {}
        total_only_set = set()
        for h in handicaps_data:
            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
            if h['total_only']:
                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

        # Putts (Front/Back/Extra) のデータ収集
        front_putt = {mid: player_data[mid]["Putt Front"] for mid in player_data}
        back_putt = {mid: player_data[mid]["Putt Back"] for mid in player_data}
        extra_putt = {mid: player_data[mid].get("Putt Extra", 0) for mid in player_data} if active_round['has_extra'] else None

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
            data["Put Pt"] = pf + pb + pe

        # Game Ptの計算
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

        # マッチポイントの計算
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
                else:
                    # Front
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Front"
                    )
                    data_i["Match Front"] += points
                    data_j["Match Front"] -= points

                    # Back
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Back"
                    )
                    data_i["Match Back"] += points
                    data_j["Match Back"] -= points

                    # Total
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Total",
                        multiplier=2
                    )
                    data_i["Match Total"] += points
                    data_j["Match Total"] -= points

                    # Extra (if exists)
                    if active_round['has_extra']:
                        points = calc_match_points_by_section(
                            data_i, data_j,
                            handicaps.get((pid_j, pid_i), 0),
                            handicaps.get((pid_i, pid_j), 0),
                            "Extra"
                        )
                        data_i["Match Extra"] += points
                        data_j["Match Extra"] -= points

        # 最終的なマッチポイントとトータルポイントの計算
        for mid in player_data:
            d = player_data[mid]
            d["Match Pt"] = (
                d["Match Front"] + 
                d["Match Back"] + 
                d["Match Total"] +
                d["Match Extra"]
            )
            d["Total Pt"] = d["Game Pt"] + d["Match Pt"] + d["Put Pt"]

        # 表示用のDataFrameを作成
        df_columns = [
            "Player",
            "Front Score", "Back Score", "Total Score"
        ]
        
        if active_round['has_extra']:
            df_columns.append("Extra Score")

        df_columns.extend([
            "Front GP", "Back GP"
        ])
        
        if active_round['has_extra']:
            df_columns.append("Extra GP")
        
        df_columns.extend([
            "Game Pt",
            "Match Front", "Match Back", "Match Total"
        ])
        
        if active_round['has_extra']:
            df_columns.append("Match Extra")
        
        df_columns.extend([
            "Match Pt",
            "Putt Front", "Putt Back"
        ])
        
        if active_round['has_extra']:
            df_columns.append("Putt Extra")
        
        df_columns.extend([
            "Put Pt",
            "Total Pt"
        ])

        # プレイヤーデータにPutt Extraがなければ追加
        if active_round['has_extra']:
            for mid in player_data:
                if "Putt Extra" not in player_data[mid]:
                    player_data[mid]["Putt Extra"] = player_data[mid].get("extra_putt", 0)

        df = pd.DataFrame([
            {col: data.get(col, 0) for col in df_columns}  # dataにキーがない場合は0をデフォルト値とする
            for data in player_data.values()
        ])

        # 結果の表示
        st.write("### スコア詳細")
        st.dataframe(df.style.format({
            col: '{:+d}' if col.endswith((' Pt', 'Front', 'Back', 'Total', 'Extra')) 
                    and col not in ['Front Score', 'Back Score', 'Total Score', 'Extra Score',
                                'Putt Front', 'Putt Back', 'Putt Extra']
                    else '{:d}' 
            for col in df.columns
            if col != 'Player'
        }))

        # マッチ対戦表の作成と表示
        st.write("### マッチ対戦表")
        match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
        st.dataframe(match_matrix.style.format(None))

        # 詳細なマッチ結果の表示
        st.write("### 詳細なマッチ結果")
        match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
        st.dataframe(
            match_results.style.apply(highlight_total_only, axis=1)
                           .map(color_points)  # applymap から map に変更
                           .format(None)
        )

        # ラウンドの確定ボタン
        if not active_round['finalized']:
            if st.button("このラウンドを確定する"):
                try:
                    # スコアの更新
                    for mid, data in player_data.items():
                        score_update = {
                            'match_pt': data['Match Pt'],
                            'put_pt': data['Put Pt'],
                            'total_pt': data['Total Pt']
                        }
                        supabase.table('score').update(score_update).eq('round_id', round_id).eq('member_id', mid).execute()
                    
                    # ラウンドを確定済みに更新
                    supabase.table('rounds').update({'finalized': True}).eq('round_id', round_id).execute()
                    
                    st.success("ラウンドを確定しました")
                    st.rerun()
                except Exception as e:
                    st.error(f"ラウンドの確定中にエラーが発生しました: {str(e)}")

def calc_match_points_by_section(player_i, player_j, handicap_ij, handicap_ji, section, multiplier=1):
    """セクション（Front/Back/Total/Extra）ごとのマッチポイントを計算"""
    if section == "Front":
        score_i = player_i["Front Score"] - handicap_ij//2
        score_j = player_j["Front Score"] - handicap_ji//2
    elif section == "Back":
        score_i = player_i["Back Score"] - (handicap_ij - handicap_ij//2)
        score_j = player_j["Back Score"] - (handicap_ji - handicap_ji//2)
    elif section == "Total":
        score_i = player_i["Total Score"] - handicap_ij
        score_j = player_j["Total Score"] - handicap_ji
    else:  # Extra
        score_i = player_i["Extra Score"] - handicap_ij
        score_j = player_j["Extra Score"] - handicap_ji
    
    if score_i < score_j:
        return 5 * multiplier
    elif score_i > score_j:
        return -5 * multiplier
    return 0

def calc_net_total(player, handicap, multiplier=1):
    """ネットトータルスコアを計算"""
    return (player["Total Score"] - handicap) * multiplier

if __name__ == "__main__":
    run()

