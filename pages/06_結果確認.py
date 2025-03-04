import streamlit as st
import pandas as pd
from modules.supabase_client import get_supabase_client, safe_update_score, cache_scores_in_session, get_scores_with_fallback, update_scores_batch
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
from modules.debug import handle_error

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
    """Extraスコアから、ハンディキャップ（multiplier 倍）を差し引いた値を差し引いた値を返す"""
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
    headers = [Paragraph('Player', style)]  # プレイヤー名のヘッダー
    
    # 各カラムのヘッダーを追加
    for col in df.columns:
        headers.append(Paragraph(str(col), style))
    
    formatted_data.append(headers)
    
    # データ行の作成（プレイヤー名を含む）
    for idx, row in df.iterrows():
        formatted_row = [Paragraph(str(idx), style)]  # プレイヤー名
        for col in df.columns:
            val = row[col]
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

def get_round_date_attr(active_round):
    """Roundモデルで利用可能な日付属性を返す。
    優先順位: play_date > date > round_date > created_at
    """
    for attr in ['play_date', 'date', 'round_date', 'created_at']:
        if hasattr(active_round, attr):
            return getattr(active_round, attr)
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

    # プレイ日とコース名を取得（辞書アクセス方式に修正）
    play_date = datetime.datetime.strptime(active_round['date_played'], '%Y-%m-%d').strftime('%Y年%m月%d日')
    course_name = active_round['course_name'] if 'course_name' in active_round else ''
    
    # タイトル行を追加
    elements.append(Paragraph(f"{play_date} {course_name} スコア集計結果", main_title_style))
    elements.append(Spacer(1, 20))

    # セクション1: 最終結果
    elements.append(Paragraph("最終結果（Game Pt + Match Pt + Put Pt ＝ Total Pt）", title_style))
    elements.append(Spacer(1, 12))
    
    # コラム順序を設定（エキストラホールの有無で切り替え）
    if active_round['has_extra']:
        ordered_columns = [
            "Player", "Front Score", "Back Score", "Total Score", "Put Pt", 
            "Extra Score", "Front GP", "Back GP", "Extra GP", "Game Pt",
            "Match Front", "Match Back", "Match Total", "Match Extra", "Match Pt",
            "Putt Front", "Putt Back", "Putt Extra", "Total Pt"
        ]
    else:
        ordered_columns = [
            "Player", "Front Score", "Back Score", "Total Score", "Put Pt", 
            "Front GP", "Back GP", "Game Pt", 
            "Match Front", "Match Back", "Match Total", "Match Pt",
            "Putt Front", "Putt Back", "Total Pt"
        ]
    
    # 結果表用のDataFrameを整形
    result_df = final_df.copy().reset_index().rename(columns={'index': 'Player'})
    
    # 既存の列と指定列のインターセクションを取得（存在する列のみ使用）
    available_cols = [col for col in ordered_columns if col in result_df.columns]
    
    # 列の順序を設定
    result_df = result_df[available_cols]
    
    # player列をindexにセットして詳細表示用のデータフレーム作成
    table_df = result_df.setIndex('Player')
    
    # PDFテーブル用のデータ作成
    final_data = create_df_for_pdf(table_df)
    
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
    
    # 正しく実装されたロジック
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
        # Total Onlyモードではトータルスコアとエキストラスコアの比較のみ行い
        # Front/Backは無視して、Totalで±10pt
        total_i = calc_net_total(data_i, handicap_ij, multiplier=2)
        total_j = calc_net_total(data_j, handicap_ji, multiplier=2)
        if total_i < total_j:
            total_pt = 10  # ±10pt
        elif total_i > total_j:
            total_pt = -10  # ±10pt
            
        # エキストラスコアがある場合は比較
        if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
            extra_i = calc_net_extra(data_i, handicap_ij)
            extra_j = calc_net_extra(data_j, handicap_ji)
            if extra_i < extra_j:
                extra_pt = 10  # ±10pt
            elif extra_i > extra_j:
                extra_pt = -10  # ±10pt
                
        # Front/Backのポイントはゼロ
        front_pt = 0
        back_pt = 0
    else:
        # 通常モード - 各セクションごとに比較
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

    # スコア情報を更新
    data_i["Match Front"] = front_pt
    data_i["Match Back"] = back_pt
    data_i["Match Total"] = total_pt
    data_i["Match Extra"] = extra_pt
    data_j["Match Front"] = -front_pt
    data_j["Match Back"] = -back_pt
    data_j["Match Total"] = -total_pt
    data_j["Match Extra"] = -extra_pt

    # 合計ポイントを計算 - 制限なしで元の計算結果をそのまま返す
    total_points_i = front_pt + back_pt + total_pt + extra_pt
    total_points_j = -(front_pt + back_pt + total_pt + extra_pt)
    
    return total_points_i, total_points_j

def calc_match_points_by_section(player_i, player_j, handicap_ij, handicap_ji, section, multiplier=1):
    """セクション（Front/Back/Total/Extra）ごとのマッチポイントを計算"""
    if section == "Front":
        score_i = player_i["Front Score"] - handicap_ij//2
        score_j = player_j["Front Score"] - handicap_ji//2
    elif section == "Back":
        score_i = player_i["Back Score"] - (handicap_ij - handicap_ij//2)
        score_j = player_j["Back Score"] - (handicap_ji - handicap_ji//2)
    elif section == "Total":
        # ハンディキャップは2倍だが、ポイントは各セクションと同じ10ポイント
        score_i = player_i["Total Score"] - handicap_ij * 2
        score_j = player_j["Total Score"] - handicap_ji * 2
    else:  # Extra
        score_i = player_i["Extra Score"] - handicap_ij
        score_j = player_j["Extra Score"] - handicap_ji
    
    if score_i < score_j:
        # 常に10ポイント返す (multiplierは使わない)
        return 10
    elif score_i > score_j:
        return -10
    return 0

def create_match_matrix(player_data, handicaps, total_only_set):
    """マッチ対戦表（星取表）の作成"""
    # member_idの昇順に並べ替え済みのプレイヤーIDリスト
    player_ids = sorted(list(player_data.keys()))
    
    # player_idsの順序通りにDataFrameを作成
    match_matrix = pd.DataFrame(
        index=[player_data[mid]["Player"] for mid in player_ids],
        columns=[player_data[mid]["Player"] for mid in player_ids]
    )
    
    # 対角要素と初期値の設定
    for i in range(len(player_ids)):
        name_i = player_data[player_ids[i]]["Player"]
        for j in range(len(player_ids)):
            name_j = player_data[player_ids[j]]["Player"]
            if i == j:
                match_matrix.loc[name_i, name_j] = "X"  # 自分対自分のマスには "X"
            else:
                match_matrix.loc[name_i, name_j] = "0"  # 初期値 "0"
    
    # マッチポイントの計算と設定
    for i in range(len(player_ids)):
        for j in range(i + 1, len(player_ids)):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            name_i = player_data[pid_i]["Player"]
            name_j = player_data[pid_j]["Player"]
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            
            # マッチポイント計算
            points_i, points_j = calc_match_points(
                player_data[pid_i],
                player_data[pid_j],
                handicap_ij,
                handicap_ji,
                is_total_only
            )
            
            # マトリックスに格納
            match_matrix.loc[name_i, name_j] = f"{points_i:+d}"
            match_matrix.loc[name_j, name_i] = f"{points_j:+d}"
            
    return match_matrix

def create_detailed_match_results(player_data, handicaps, total_only_set):
    """マッチ戦の詳細結果を作成（横：対戦カード、縦：プレイヤーのポイント）"""
    # member_idの昇順に並べ替え済みのプレイヤーIDリスト
    player_ids = sorted(list(player_data.keys()))
    n_players = len(player_ids)
    match_results = {}
    matches = []
    multi_columns = []
    
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            match_name = f"{player_data[pid_i]['Player']} vs {player_data[pid_j]['Player']}"
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            # Total Onlyモードかどうかを判定
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            handicap_str = f"{handicap_ij} vs {handicap_ji}"
            if is_total_only:
                handicap_str += " (Total Only)"
            matches.append(match_name)
            multi_columns.append((match_name, handicap_str))
    
    # プレイヤーごとの結果を初期化（player_idsの順序通りに）
    for pid in player_ids:
        match_results[player_data[pid]["Player"]] = {match: "-" for match in matches}
    
    # 対戦結果を計算して格納
    for i in range(n_players-1):
        for j in range(i+1, n_players):  # ここを修正: j < n_players に変更
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            match_name = f"{data_i['Player']} vs {data_j['Player']}"
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            
            points_i, points_j = calc_match_points(
                data_i,
                data_j,
                handicap_ij,
                handicap_ji,
                is_total_only
            )
            
            match_results[data_i["Player"]][match_name] = f"{points_i:+d}" if points_i != 0 else "0"
            match_results[data_j["Player"]][match_name] = f"{points_j:+d}" if points_j != 0 else "0"
    
    # DataFrameを作成し、元のplayer_idsの順序を保持するためにインデックスを再整列
    df = pd.DataFrame.from_dict(match_results, orient='index')
    ordered_players = [player_data[pid]["Player"] for pid in player_ids]
    df = df.reindex(ordered_players)
    
    # カラム数をチェックして一致していることを確認
    if len(df.columns) != len(multi_columns):
        st.warning(f"カラム数の不一致: DataFrame列数={len(df.columns)}, マルチインデックス数={len(multi_columns)}")
        # 不一致の場合は単純なカラム名を使用
        return df
    
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
    # 辞書アクセス方式に修正
    play_date = active_round['date_played'].replace('-', '')
    round_id = active_round['round_id']
    return f"{play_date}_Round{round_id}_golf_results.pdf"

def test_calculation_logic(round_id):
    """計算ロジックのテストを行う"""
    supabase = get_supabase_client()
    
    st.subheader("計算ロジックのテスト")
    
    # スコアデータを取得
    scores = get_scores_with_fallback(round_id)
    if not scores:
        st.error("スコアデータが取得できませんでした")
        return
    
    # ハンディキャップデータを取得
    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data
    if not handicaps_data:
        st.error("ハンディキャップデータが取得できませんでした")
        return
    
    # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    round_data = round_result.data[0] if round_result.data else None
    if not round_data:
        st.error("ラウンド情報が取得できませんでした")
        return
    
    # テスト実行
    from pages.handicap_calc_logic import process_round_scores
    with st.spinner("計算ロジックをテスト中..."):
        updated_scores = process_round_scores(scores, handicaps_data, round_data)
    
    # 結果表示
    st.success(f"{len(updated_scores)}名分のスコア計算が完了しました")
    
    # 詳細表示
    with st.expander("計算結果の詳細を表示"):
        for score in updated_scores:
            st.write(f"**{score.get('name', score.get('member_id'))}**")
            st.write(f"- Game Pt: {score['game_pt']}")
            st.write(f"- Match Pt: {score['match_pt']}")
            st.write(f"- Put Pt: {score['put_pt']}")
            st.write(f"- Total Pt: {score['total_pt']}")
            st.write("---")

def run():
    # Supabaseクライアントの取得
    supabase = get_supabase_client()
    # Supabaseクライアントの取得
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("結果確認")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")
    
    # カスタムCSSを追加して最初の列を固定表示に（より強力な選択子で確実に適用）
    st.markdown("""
        <style>
        /* プレイヤー列を強制的に固定表示するためのより強力なCSS */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table,
        [data-testid="stDataFrame"] > div > div > div > div > div table {
            position: relative !important;
            border-collapse: collapse !important;
            table-layout: auto !important;
        }
        
        [data-testid="stDataFrame"] div[data-testid="stTable"] table th:first-of-type,
        [data-testid="stDataFrame"] div[data-testid="stTable"] table td:first-of-type,
        [data-testid="stDataFrame"] > div > div > div > div > div table th:first-of-type,
        [data-testid="stDataFrame"] > div > div > div > div > div table td:first-of-type {
            position: sticky !important;
            left: 0 !important;
            background-color: white !important;
            z-index: 10 !important;
            box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !important;
            min-width: 100px !important;
        }
        
        /* ヘッダーとプレイヤー列の交差部分 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:first-child th:first-child,
        [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:nth-child(2) th:first-child,
        [data-testid="stDataFrame"] > div > div > div > div > div table thead tr:first-child th:first-child,
        [data-testid="stDataFrame"] > div > div > div > div > div table thead tr:nth-child(2) th:first-child {
            z-index: 20 !important;
            background-color: #f0f2f6 !important;
        }
        
        /* すべてのヘッダーセルの背景色を設定 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table thead th,
        [data-testid="stDataFrame"] > div > div > div > div > div table thead th {
            background-color: #f0f2f6 !important;
            position: relative !important;
            z-index: 5 !important;
        }
        
        /* スクロールコンテナを指定 */
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            max-width: 100% !important;
            display: block !important;
        }
        
        /* マルチインデックスヘッダー対応 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table tr th:first-child,
        [data-testid="stDataFrame"] > div > div > div > div > div table tr th:first-child {
            position: sticky !重要;
            left: 0 !important;
            z-index: 20 !important;
        }
        
        /* スタイルの優先度を上げる */
        html body [data-testid="stDataFrame"] div[data-testid="stTable"] table td:first-of-type {
            position: sticky !important;
            left: 0 !important;
            background-color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    rounds_result = supabase.table('rounds').select('*').eq('finalized', False).order('date_played', desc=True).execute()
    # 未確定ラウンドの存在チェック
    unfinalized_rounds = rounds_result.data
    all_rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    # すべてのラウンドを取得（date_playedで降順ソート）
    all_rounds = all_rounds_result.data
    if unfinalized_rounds:
        # 未確定ラウンドがある場合は警告表示
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
        # セッションにスコアをキャッシュ
        cache_scores_in_session(round_id)
        # ラウンド情報を取得
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        active_round = round_result.data[0] if round_result.data else None
        if not active_round:
            st.warning("選択されたラウンドが見つかりません。")
            return
        # スコアデータの取得（フォールバック機能付き）
        try:
            scores = get_scores_with_fallback(round_id)
        except Exception as e:
            handle_error(e)
            return  # エラー発生時は処理を中断
        
        # デバッグ情報を非表示に修正
        if st.session_state.get("debug_mode", False):  # デバッグモード時のみ表示
            st.write(f"取得したスコア数: {len(scores)}")
            if scores:
                sample = scores[0]
                st.write(f"サンプルデータ構造: {list(sample.keys())}")
        
        if not scores:
            st.warning("スコアデータが見つかりません。")
            return
            
        # ハンディキャップデータの取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data
        # プレーヤーデータの準備
        player_data = {}
        for sc in scores:
            # 名前を取得する（直接nameキーか、memberオブジェクト内のnameキーを試みる）
            player_name = None
            if 'name' in sc:
                player_name = sc['name']
            elif 'member' in sc and isinstance(sc['member'], dict) and 'name' in sc['member']:
                player_name = sc['member']['name']
            else:
                # nameが見つからない場合は代替の識別子を使用
                player_name = f"Player {sc.get('member_id', 'Unknown')}"
            player_data[sc['member_id']] = {
                "Player": player_name,
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
                "Total Pt": sc.get('total_pt', 0),
            }
        # member_idの昇順にプレイヤーIDのリストを並べ替え
        player_ids = sorted(list(player_data.keys()))
        n_players = len(player_ids)
        # ハンディキャップの準備（リストから辞書に変換）
        handicaps = {}
        total_only_set = set()  # total_onlyモードのペアを格納する集合
        for h in handicaps_data:
            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
            # total_onlyフラグがある場合、total_only_setにプレイヤーペアを追加
            if 'total_only' in h and h['total_only']:
                # frozensetを使用して順序に依存しないペアキーを作成
                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
        # デバッグ情報を表示（サイドバーに）
        if total_only_set:
            st.sidebar.info(f"Total Onlyモード: {len(total_only_set)}ペア")
            for pair in total_only_set:
                pair_list = list(pair)
                name1 = player_data[pair_list[0]]["Player"] if pair_list[0] in player_data else f"Player {pair_list[0]}"
                name2 = player_data[pair_list[1]]["Player"] if pair_list[1] in player_data else f"Player {pair_list[1]}"
                st.sidebar.text(f"- {name1} vs {name2}")
        # Putts (Front/Back/Extra) のデータ収集を追加
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
        # まず、各プレイヤーの一時的なGame Ptを算出（temp_game_pt）
        temp_game_pts = {}
        for mid in player_data:
            fgp = player_data[mid]["Front GP"]
            bgp = player_data[mid]["Back GP"]
            egp = player_data[mid]["Extra GP"]
            temp_game_pts[mid] = fgp + bgp + egp
            player_data[mid]["Temp Game Pt"] = temp_game_pts[mid]
        if n_players == 3:
            # 3人の場合、各プレイヤーの最終Game Ptを再計算
            for mid in player_data:
                my_total = temp_game_pts[mid]
                others_total = sum(temp_game_pts[oid] for oid in temp_game_pts if oid != mid)
                player_data[mid]["Game Pt"] = my_total * 2 - others_total
        else:
            # 3人以外の場合は一時的なポイントをそのまま使用
            for mid in player_data:
                player_data[mid]["Game Pt"] = temp_game_pts[mid]
        # マッチポイントの計算前に各プレイヤーのマッチポイントを初期化
        for mid in player_data:
            player_data[mid]["Match Front"] = 0
            player_data[mid]["Match Back"] = 0
            player_data[mid]["Match Total"] = 0
            player_data[mid]["Match Extra"] = 0
            player_data[mid]["Match Pt"] = 0
            
        # マッチポイントの計算
        for i in range(len(player_ids)):
            for j in range(i+1, len(player_ids)):
                pid_i = player_ids[i]
                pid_j = player_ids[j]
                data_i = player_data[pid_i]
                data_j = player_data[pid_j]
                pair_key = frozenset([pid_i, pid_j])
                
                # total_onlyモードの場合は専用の処理
                if pair_key in total_only_set:
                    # Total Onlyモード - Front/Backはスキップ、TotalとExtraだけ計算
                    # Total
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Total"
                    )
                    data_i["Match Total"] += points
                    data_j["Match Total"] -= points
                    data_i["Match Pt"] += points
                    data_j["Match Pt"] -= points
                    
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
                        data_i["Match Pt"] += points
                        data_j["Match Pt"] -= points
                else:
                    # 通常モード（Front, Back, Total, Extra別々に勝敗を決める）
                    # Front
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Front"
                    )
                    data_i["Match Front"] += points
                    data_j["Match Front"] -= points
                    data_i["Match Pt"] += points
                    data_j["Match Pt"] -= points
                    
                    # Back
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Back"
                    )
                    data_i["Match Back"] += points
                    data_j["Match Back"] -= points
                    data_i["Match Pt"] += points
                    data_j["Match Pt"] -= points
                    
                    # Total - ポイントは10固定
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Total"
                    )
                    data_i["Match Total"] += points
                    data_j["Match Total"] -= points
                    data_i["Match Pt"] += points
                    data_j["Match Pt"] -= points
                    
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
                        data_i["Match Pt"] += points
                        data_j["Match Pt"] -= points
        
        # 最終的なトータルポイントの計算 - マッチポイントの再計算はしない
        for mid in player_data:
            d = player_data[mid]
            # 直接計算されたMatch Ptをそのまま使用
            d["Total Pt"] = d["Game Pt"] + d["Match Pt"] + d["Put Pt"]
        # マッチポイント合計の整合性チェック
        total_match_pts = sum(player_data[mid]["Match Pt"] for mid in player_ids)
        if abs(total_match_pts) > 0.01:  # 浮動小数点の計算誤差を考慮
            st.warning(f"警告: プレイヤー間のマッチポイント合計が0になっていません。合計: {total_match_pts}pt")
        # デバッグ情報: 特定のラウンドのマッチポイント確認を非表示に修正
        if round_id == 16 and st.session_state.get("debug_mode", False):  # デバッグモード時のみ表示
            st.info("### マッチポイント確認 (ID: 16)")
            for mid, data in player_data.items():
                player_name = data["Player"]
                match_pt = data["Match Pt"]
                st.text(f"{player_name}: {match_pt:+d} pt")
                
            # 期待される値を表示
            expected = {
                "荒巻": +20,
                "吉井": +30,
                "福澤": +40,
                "清村": -90
            }
            
            # 期待値との差異を確認
            found_mismatch = False
            for name, expected_pt in expected.items():
                for mid, data in player_data.items():
                    if data["Player"] == name and data["Match Pt"] != expected_pt:
                        st.warning(f"{name}のマッチポイントが期待値と異なります: 実際={data['Match Pt']:+d}pt, 期待={expected_pt:+d}pt")
                        found_mismatch = True
            
            if not found_mismatch:
                st.success("全プレイヤーのマッチポイントが期待値通りです！")
                
        # 表示用のDataFrameを作成（プレイヤーをmember_idの昇順で並べ替え）
        df_columns = [
            "Player",
            "Front Score", "Back Score", "Total Score",
            "Put Pt",
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
        # Putt Extraがなければ追加
        for mid in player_data:
            if "Putt Extra" not in player_data[mid]:
                player_data[mid]["Putt Extra"] = player_data[mid].get("extra_putt", 0)
        # DataFrameの作成時にmember_idの昇順に従ってデータを整列させる
        df = pd.DataFrame(
            {col: player_data[mid].get(col, 0) for col in df_columns}  # dataにキーがない場合は0をデフォルト値とする
            for mid in player_ids  # ソートされたIDリストを使用
        )
        # 結果の表示
        st.write("### スコア詳細")
        
        # カスタムCSSを追加して最初の列を固定表示に
        st.markdown("""
            <style>
            /* スコア詳細テーブルのプレイヤー列を固定表示にする */
            [data-testid="stDataFrame"] table {
                position: relative;
            }
            
            [data-testid="stDataFrame"] table th:first-child,
            [data-testid="stDataFrame"] table td:first-child {
                position: sticky;
                left: 0;
                background-color: white;
                z-index: 1;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1);
            }
            
            /* テーブルヘッダーとプレイヤー列の交差部分 */
            [data-testid="stDataFrame"] table th:first-child {
                z-index: 2;
                background-color: white;
            }
            
            /* スクロールバーを常に表示 */
            [data-testid="stDataFrame"] {
                overflow-x: auto;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # DataFrame表示（スタイル定義は従来通り）
        st.dataframe(df.style.format({
            col: '{:+d}' if col.endswith((' Pt', 'Front', 'Back', 'Total', 'Extra')) 
                    and col not in ['Front Score', 'Back Score', 'Total Score', 'Extra Score',
                                'Putt Front', 'Putt Back', 'Putt Extra']
                    else '{:d}'
            for col in df.columns
            if col != 'Player'
        }), use_container_width=True)

        # マッチ対戦表の作成と表示
        st.write("### マッチ対戦表")
        # 星取表のCSSも追加
        st.markdown("""
            <style>
            /* マッチ対戦表のプレイヤー列を固定表示にする */
            [data-testid="stDataFrame"] + div + div [data-testid="stDataFrame"] table th:first-child,
            [data-testid="stDataFrame"] + div + div [data-testid="stDataFrame"] table td:first-child {
                position: sticky;
                left: 0;
                background-color: white;
                z-index: 1;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
        
        # 表示スタイルを詳細なマッチ結果と揃える
        st.dataframe(
            match_matrix.style.map(color_points)  # color_points関数を適用して背景色を設定
                         .format(None)  # フォーマットはそのまま
        )
        
        # 詳細なマッチ結果
        st.write("### 詳細なマッチ結果")
        match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
        
        # 詳細マッチ結果のCSS追加 - マルチインデックスヘッダー対応
        st.markdown("""
            <style>
            /* 詳細マッチ結果のプレイヤー列を固定表示にする */
            [data-testid="stDataFrame"] + div + div + div [data-testid="stDataFrame"] table th:first-child,
            [data-testid="stDataFrame"] + div + div + div [data-testid="stDataFrame"] table td:first-child {
                position: sticky;
                left: 0;
                background-color: white;
                z-index: 1;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 各カラムの最大幅を設定（カラム名が長いため適切な幅に調整）
        custom_css = """
        <style>
        .detailed-match-results th {
            min-width: 180px !important; 
            max-width: 180px !important;
            white-space: normal !important;
            height: auto !important;
            padding: 8px !important;
        }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)
        
        # スタイリングとともにデータフレームを表示
        st.markdown('<div class="detailed-match-results">', unsafe_allow_html=True)
        st.dataframe(
            match_results.style.apply(highlight_total_only, axis=1)
                         .map(color_points)
                         .format(None),
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # PDF出力ボタンを追加
        st.subheader("PDF出力")
        if st.button("スコア表をPDFで出力"):
            try:
                # 結果表のデータフレームを作成
                # player_idsはすでにソートされているので、これに合わせてデータを整列させる
                
                # エキストラホールの有無に応じて出力カラムを設定
                if active_round['has_extra']:
                    # エキストラホールありの場合のカラム
                    pdf_columns = [
                        "Player", "Front Score", "Back Score", "Total Score", "Put Pt",
                        "Extra Score", "Front GP", "Back GP", "Extra GP", "Game Pt",
                        "Match Front", "Match Back", "Match Total", "Match Extra", "Match Pt",
                        "Putt Front", "Putt Back", "Putt Extra", "Total Pt"
                    ]
                else:
                    # エキストラホールなしの場合のカラム
                    pdf_columns = [
                        "Player", "Front Score", "Back Score", "Total Score", "Put Pt",
                        "Front GP", "Back GP", "Game Pt",
                        "Match Front", "Match Back", "Match Total", "Match Pt",
                        "Putt Front", "Putt Back", "Total Pt"
                    ]
                
                # 指定の順序でデータフレームを構築
                pdf_data = {}
                for col in pdf_columns:
                    if col == "Player":
                        pdf_data[col] = [player_data[mid]["Player"] for mid in player_ids]
                    else:
                        pdf_data[col] = [player_data[mid].get(col, 0) for mid in player_ids]
                
                result_table = pd.DataFrame(pdf_data)
                
                # PDFを生成
                pdf_buffer = generate_pdf(result_table, match_results, match_matrix, active_round)
                
                # ファイル名を設定
                pdf_filename = get_pdf_filename(active_round)
                
                # ダウンロードリンクを表示
                st.download_button(
                    label="PDFをダウンロード",
                    data=pdf_buffer,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )
                
                st.success("PDFが正常に生成されました。ダウンロードボタンをクリックしてPDFをダウンロードしてください。")
            except Exception as e:
                st.error(f"PDFの生成中にエラーが発生しました: {str(e)}")
                import traceback
                st.error(traceback.format_exc())  # 詳細なエラー情報を表示
        
        # ラウンドの確定ボタン
        if not active_round['finalized']:
            if st.button("このラウンドを確定する"):
                try:
                    # 更新データの準備
                    update_data = {}
                    for mid, data in player_data:
                        update_data[mid] = {
                            'game_pt': data['Game Pt'],
                            'match_pt': data['Match Pt'],
                            'put_pt': data['Put Pt'],
                            'total_pt': data['Total Pt']
                        }
                    # 一括更新を試みる
                    success, updates, failures = update_scores_batch(round_id, update_data)
                    if success:
                        st.success("ラウンドを確定しました")
                        supabase.table('rounds').update({'finalized': True}).eq('round_id', round_id).execute()
                        # ラウンドを確定済みに更新
                        if updates:
                            st.rerun()
                    else:
                        st.warning(f"一部のスコア更新に成功しましたが、{len(failures)}件の失敗がありました。")
                        # 失敗した項目の詳細を表示
                        for failure in failures:
                            st.error(f"プレイヤーID {failure['member_id']}: {failure['error']}")
                        # エラーが発生した場合、セッションに計算結果を保存
                        if "calculation_results" not in st.session_state:
                            st.session_state.calculation_results = {}
                        st.session_state.calculation_results[round_id] = player_data
                        st.error("スコア更新に失敗しました。再試行してください。")
                except Exception as e:
                    st.error(f"ラウンドの確定中にエラーが発生しました: {str(e)}")
                    # エラーが発生した場合、セッションに計算結果を保存
                    if "calculation_results" not in st.session_state:
                        st.session_state.calculation_results = {}
                    st.session_state.calculation_results[round_id] = player_data
                    st.info("計算結果はセッションに保存されました。再試行することで保存できる可能性があります。")

    # ラウンド確定ボタンの後に過去データ再計算ボタンと計算ロジックテストボタンを追加
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        if st.button("過去のすべてのラウンドデータを再計算", help="過去の全ラウンドを現在のロジックで再計算します"):
            with st.spinner("過去データを再計算中..."):
                from modules.supabase_client import recalculate_all_past_rounds
                success = recalculate_all_past_rounds()
                if success:
                    st.success("過去データの再計算が完了しました")
                else:
                    st.error("過去データの再計算に失敗しました")
    
    with col2:
        if selected_round_str and st.button("このラウンドの計算ロジックをテスト", help="現在のロジックでこのラウンドのスコアを計算します"):
            test_calculation_logic(round_id)
    
    st.info("過去のすべてのラウンドのポイントを最新のロジックで再計算します。\n"
            "時間がかかる場合があります。")

if __name__ == "__main__":
    run()