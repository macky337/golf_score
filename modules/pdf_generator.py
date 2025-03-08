import io
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

# フォント設定を共有
FONT_NAME = "Helvetica"  # デフォルト値、実際にはメインファイルで設定される値を使用

def set_font(font_name):
    """フォント名を設定する"""
    global FONT_NAME
    FONT_NAME = font_name

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
    
    # ヘッダー行
    headers = [Paragraph('Player', style)]
    for col in df.columns:
        headers.append(Paragraph(str(col), style))
    formatted_data.append(headers)
    
    # データ行の作成
    for idx, row in df.iterrows():
        formatted_row = [Paragraph(str(idx), style)]
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                val = ""
            # スコア関連のカラム（符号なし表示）
            elif col in ['Front Score', 'Back Score', 'Total Score', 'Extra Score', 
                         'Putt Front', 'Putt Back', 'Putt Extra']:
                val = f"{int(round(val))}" if isinstance(val, (int, float)) else str(val)
            # Match系カラム（符号付きの整数表示）
            elif col in ['Match Front', 'Match Back', 'Match Total', 'Match Extra', 'Match Pt']:
                try:
                    val = f"{int(round(val)):+d}" if isinstance(val, (int, float)) else str(val)
                except ValueError:
                    val = "0"  # 変換に失敗した場合は "0" を表示
            # ゲーム点、パット得点、合計点
            elif col in ['Front GP', 'Back GP', 'Extra GP', 'Game Pt', 'Put Pt', 'Total Pt']:
                val = f"{int(round(val)):+d}" if isinstance(val, (int, float)) and val != 0 else "0"
            else:
                val = str(val)
            
            formatted_row.append(Paragraph(str(val), style))
        formatted_data.append(formatted_row)
    
    return formatted_data

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
    
    main_title_style = ParagraphStyle(
        'MainTitle',
        fontName=FONT_NAME,
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=10
    )
    
    title_style = ParagraphStyle(
        'Title',
        fontName=FONT_NAME,
        fontSize=14,
        leading=16,
        alignment=1
    )
    
    play_date = datetime.datetime.strptime(active_round['date_played'], '%Y-%m-%d').strftime('%Y年%m月%d日')
    course_name = active_round['course_name'] if 'course_name' in active_round else ''
    
    elements.append(Paragraph(f"{play_date} {course_name} スコア集計結果", main_title_style))
    elements.append(Spacer(1, 20))
    
    final_df = final_df.reset_index()
    
    for col in ['Match Front', 'Match Back', 'Match Total', 'Match Pt']:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)
    
    table_data = create_df_for_pdf(final_df)
    
    col_widths = [landscape(letter)[0] / len(table_data[0])] * len(table_data[0])
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
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
    elements.append(table)
    
    # セクション2: マッチ戦詳細結果
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("マッチ戦詳細結果", title_style))
    elements.append(Spacer(1, 12))
    
    # 詳細なマッチ結果テーブルを作成
    detailed_data = create_df_for_pdf(detailed_df)
    col_widths_detailed = [landscape(letter)[0] / len(detailed_data[0])] * len(detailed_data[0])
    detail_table = Table(detailed_data, colWidths=col_widths_detailed)
    detail_table.setStyle(TableStyle([
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
    elements.append(detail_table)
    
    # セクション3: マッチ対戦表
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("対戦結果（Match Pt 集計）", title_style))
    elements.append(Spacer(1, 12))
    
    # マッチ対戦表（星取表）を作成
    star_data = create_df_for_pdf(star_df)
    col_widths_star = [landscape(letter)[0] / len(star_data[0])] * len(star_data[0])
    star_table = Table(star_data, colWidths=col_widths_star)
    star_table.setStyle(TableStyle([
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
    elements.append(star_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def get_pdf_filename(active_round):
    """PDFファイル名を生成"""
    play_date = active_round['date_played'].replace('-', '')
    round_id = active_round['round_id']
    return f"{play_date}_Round{round_id}_golf_results.pdf"
