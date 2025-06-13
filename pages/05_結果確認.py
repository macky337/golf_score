import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from modules.page_utils import switch_page

# ▼▼▼ 必要モジュールのインポート ▼▼▼
from modules.supabase_client import (
    get_supabase_client,
    get_scores_with_fallback,
    update_scores_batch,
)
from modules.pdf_generator import generate_pdf, set_font, get_pdf_filename
from modules.match_analyzer import create_match_matrix, create_detailed_match_results
from modules.data_formatter import highlight_total_only, color_points, get_color_points_function, get_color_function_for_column, apply_ranking_colors_to_dataframe
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
import traceback

# ▼▼▼ フォント登録（日本語対応） ▼▼▼
FONT_NAME = "Helvetica"

# フォントファイルの検索パス
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_file_dir)  # 1つ上のディレクトリ

font_paths = [
    "ipaexg.ttf",  # 現在のディレクトリ
    os.path.join(current_file_dir, "ipaexg.ttf"),  # pagesディレクトリ内
    os.path.join(project_root, "ipaexg.ttf"),  # プロジェクトルート
    os.path.join(os.getcwd(), "ipaexg.ttf"),  # 作業ディレクトリ
    r"c:\Users\user\Documents\GitHub\golf_score\ipaexg.ttf",  # 絶対パス（プロジェクトルート）
    "/app/ipaexg.ttf"  # Railway/Docker環境
]

font_found = False
for font_path in font_paths:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('IPAexGothic', font_path))
            FONT_NAME = "IPAexGothic"
            set_font(FONT_NAME)
            font_found = True
            print(f"フォントが見つかりました: {font_path}")  # デバッグ用
            break
        except Exception as e:
            print(f"フォント登録エラー ({font_path}): {e}")  # デバッグ用
            continue

if not font_found:
    st.warning("⚠️ 日本語フォント(ipaexg.ttf)が見つかりません。PDF出力は英語フォント(Helvetica)となり、日本語文字が正しく表示されない可能性があります。")
    # デバッグ情報を表示
    with st.expander("🔍 フォント検索詳細情報（トラブルシューティング用）"):
        st.write("**検索したパス:**")
        for i, path in enumerate(font_paths):
            exists = os.path.exists(path)
            icon = "✅" if exists else "❌"
            st.write(f"{icon} `{path}` - {'存在する' if exists else '存在しない'}")
        st.write("**システム情報:**")
        st.write(f"- 現在のファイル位置: `{os.path.abspath(__file__)}`")
        st.write(f"- 現在の作業ディレクトリ: `{os.getcwd()}`")
        st.write(f"- プロジェクトルート: `{project_root}`")
        st.write(f"現在のファイル位置: {os.path.abspath(__file__)}")
        st.write(f"現在の作業ディレクトリ: {os.getcwd()}")


def initialize_player_data(scores, round_results):
    player_data = {}
    # スコアデータをmember_idでソート
    sorted_scores = sorted(scores, key=lambda x: x['member_id'])
    
    for sc in sorted_scores:
        member_id = sc['member_id']
        player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {member_id}"
        # DB側のキーがスネークケースの場合
        round_result_data = round_results.get(member_id, {}) if round_results else {}
        
        player_data[member_id] = {
            "Player": player_name,
            "Front Score": sc.get('front_score', 0) or 0,
            "Back Score": sc.get('back_score', 0) or 0,
            "Extra Score": sc.get('extra_score', 0) or 0,
            "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
            "Front GP": sc.get('front_game_pt', 0) or 0,
            "Back GP": sc.get('back_game_pt', 0) or 0,
            "Extra GP": sc.get('extra_game_pt', 0) or 0,
            "Game Pt": round_result_data.get("Game Pt", sc.get('total_game_pt', 0) or 0),  # round_resultsからゲームポイントを優先取得
            # キー名を DB のテーブル構造に合わせる（両方のケースを試す）
            "Match Front": round_result_data.get("Match Front", round_result_data.get("match_front", 0)),
            "Match Back":  round_result_data.get("Match Back", round_result_data.get("match_back", 0)),
            "Match Total": round_result_data.get("Match Total", round_result_data.get("match_total", 0)),
            "Match Extra": round_result_data.get("Match Extra", round_result_data.get("match_extra", 0)),
            "Match Pt":    round_result_data.get("Match Pt", round_result_data.get("match_pt", 0)),
            "Putt Front": sc.get('front_putt', 0) or 0,
            "Putt Back": sc.get('back_putt', 0) or 0,
            "Putt Extra": sc.get('extra_putt', 0) or 0,
            "Putt Pt": round_result_data.get("Putt Pt", round_result_data.get("putt_pt", 0)),
        }
        
        # Total Ptを正確に計算（ゲームポイント + マッチポイント + パットポイント）
        player_data[member_id]["Total Pt"] = (
            player_data[member_id]["Game Pt"] + 
            player_data[member_id]["Match Pt"] + 
            player_data[member_id]["Putt Pt"]
        )
    
    return player_data


def run():
    """結果確認画面のメイン関数"""
    try:
        # エラーハンドリングを追加
        if 'supabase' not in st.session_state:
            supabase = get_supabase_client()
            if supabase is None:
                st.error("データベースに接続できません。しばらくしてから再度お試しください。")
                return
        else:
            supabase = st.session_state.supabase

        # タイトルとホームボタンのレイアウト
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.title("結果確認")
        with col2:
            if st.button("🏠 Home"):
                switch_page("main")

        # CSSスタイルを追加 - プレイヤー名の表示問題を修正
        st.markdown(
            """
            <style>
            /* テーブル全体の横スクロール */
            [data-testid="stDataFrame"] > div {
                overflow-x: auto !important;
                max-width: 100% !important;
                display: block !important;
            }
            
            /* プレイヤー列を固定表示 */
            [data-testid="stDataFrame"] table th:first-child,
            [data-testid="stDataFrame"] table td:first-child {
                position: sticky !important;
                left: 0 !important;
                z-index: 10 !important;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !important;
                min-width: 100px !important;
            }
            
            /* ヘッダー行のスタイル */
            [data-testid="stDataFrame"] table thead th {
                position: sticky !important;
                top: 0 !important;
                z-index: 20 !important;
            }
            
            /* 基本テーブル設定 */
            [data-testid="stDataFrame"] table {
                position: relative !important;
                border-collapse: collapse !important;
                table-layout: auto !important;
            }
            
            /* プレイヤー名列の文字色と背景色を強制適用 */
            [data-testid="stDataFrame"] table tbody tr td:first-child,
            [data-testid="stDataFrame"] table tbody tr th:first-child,
            [data-testid="stDataFrame"] td:first-child,
            [data-testid="stDataFrame"] th:first-child {
                color: #555555 !important;
                background-color: #f8f9fa !important;
                font-weight: bold !important;
                border-right: 1px solid #ddd !important;
            }
            
            /* より具体的なStreamlitの構造に対応 */
            div[data-testid="stDataFrame"] table tr td:first-child,
            div[data-testid="stDataFrame"] table tr th:first-child {
                color: #495057 !important;
                background-color: #f8f9fa !important;
                font-weight: bold !important;
            }
            
            /* ダークモード専用スタイル */
            @media (prefers-color-scheme: dark) {
                [data-testid="stDataFrame"] table tbody tr td:first-child,
                [data-testid="stDataFrame"] table tbody tr th:first-child,
                [data-testid="stDataFrame"] td:first-child,
                [data-testid="stDataFrame"] th:first-child,
                div[data-testid="stDataFrame"] table tr td:first-child,
                div[data-testid="stDataFrame"] table tr th:first-child {
                    color: #cccccc !important;
                    background-color: rgba(50, 50, 50, 0.8) !important;
                }
            }
            
            /* Streamlitのtheme属性に基づく強制適用 */
            .stApp[data-theme="dark"] [data-testid="stDataFrame"] table tr td:first-child,
            .stApp[data-theme="dark"] [data-testid="stDataFrame"] table tr th:first-child {
                color: #cccccc !important;
                background-color: rgba(50, 50, 50, 0.9) !important;
            }
            
            .stApp[data-theme="light"] [data-testid="stDataFrame"] table tr td:first-child,
            .stApp[data-theme="light"] [data-testid="stDataFrame"] table tr th:first-child {
                color: #555555 !important;
                background-color: rgba(240, 242, 246, 0.9) !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # 未確定ラウンドと全ラウンドの取得
        rounds_result = supabase.table('rounds').select('*').eq('finalized', False).order('date_played', desc=True).execute()
        unfinalized_rounds = rounds_result.data
        all_rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
        all_rounds = all_rounds_result.data

        if unfinalized_rounds:
            st.warning(f"⚠️ 未確定のラウンドが {len(unfinalized_rounds)} 件あります")
            for r in unfinalized_rounds:
                st.info(f"📝 {r['date_played']} - {r['course_name']} (ID: {r['round_id']})")

        round_options = [
            f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})"
            for r in all_rounds
        ]
        default_index = 0 if unfinalized_rounds else 0
        selected_round_str = st.selectbox(
            "ラウンドを選択してください",
            options=round_options,
            index=default_index if round_options else None
        )

        if not selected_round_str:
            st.warning("表示するラウンドがありません。")
            return

        round_id = int(selected_round_str.split("ID: ")[1].rstrip(")"))

        # ラウンド情報を取得
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        active_round = round_result.data[0] if round_result.data else None
        if not active_round:
            st.error("選択されたラウンドが見つかりません。")
            return
        
        # ラウンドが確定済みかどうかを表示
        if active_round['finalized']:
            st.info("このラウンドは確定済みです。スコア修正が必要な場合は管理画面から行ってください。")
        else:
            st.warning("このラウンドはまだ確定されていません。各スコア入力画面からスコアを修正できます。")
            # スコア入力へのリンクボタンを追加
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("フロントスコア修正", use_container_width=True):
                    st.session_state.active_round_id = round_id
                    st.session_state.admin_selected_round_id = round_id
                    switch_page("02_フロントスコア入力")
            with col2:
                if st.button("バックスコア修正", use_container_width=True):
                    st.session_state.active_round_id = round_id
                    st.session_state.admin_selected_round_id = round_id
                    switch_page("03_バックスコア入力")
            with col3:
                has_extra = active_round.get('has_extra', False)
                if has_extra:
                    if st.button("エキストラスコア修正", use_container_width=True):
                        st.session_state.active_round_id = round_id
                        st.session_state.admin_selected_round_id = round_id
                        st.session_state.has_extra = True
                        switch_page("05_エキストラスコア入力")

        # スコア取得
        try:
            scores = get_scores_with_fallback(round_id)
            if not scores:
                st.warning("スコアデータが見つかりません。")
                st.info("このラウンドにはスコアデータが登録されていないようです。フロントスコア入力から始めるか、新しいラウンドを設定してください。")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("新しいラウンドを設定"):
                        st.session_state.active_round_id = round_id
                        switch_page("01_ラウンド設定")
                with col2:
                    if st.button("フロントスコア入力へ"):
                        st.session_state.active_round_id = round_id
                        switch_page("02_フロントスコア入力")
                return
        except Exception as e:
            st.error(f"データ取得中にエラーが発生しました: {str(e)}")
            st.error(traceback.format_exc())
            return

        # round_results を取得（必ず実行）
        round_results = get_round_results(round_id)
        # round_results を辞書形式に変換（メンバーIDをキーに設定）
        if isinstance(round_results, list):
            round_results = { item.get('member_id'): item for item in round_results if item.get('member_id') is not None }

        # ハンディキャップ情報の取得
        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data

        # プレイヤーデータの初期化（scores と round_results を合体）
        player_data = initialize_player_data(scores, round_results)
        player_ids = sorted(list(player_data.keys()))
        
        if handicaps_data:
            # ハンディキャップ辞書作成
            handicaps = {}
            total_only_set = set()
            for h in handicaps_data:
                handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                if 'total_only' in h and h['total_only']:
                    total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

        # データフレーム作成とスタイリング
        df_columns = [
            "Player",
            "Front Score", "Back Score", "Total Score", "Extra Score",
            "Match Front", "Match Back", "Match Total", "Match Extra", "Match Pt",
            "Front GP", "Back GP", "Extra GP", "Game Pt",
            "Front Putt", "Back Putt", "Extra Putt", "Putt Pt",
            "Total Pt"    ]
        
        score_data_list = []
        # player_ids（ソート済み）の順序でデータを構築
        for pid in player_ids:
            p_data = player_data[pid]
            score_data_list.append({
                "Player":      p_data["Player"],
                "Front Score": p_data["Front Score"],
                "Back Score":  p_data["Back Score"],
                "Total Score": p_data["Total Score"],
                "Extra Score": p_data["Extra Score"],
                "Match Front": p_data["Match Front"],
                "Match Back":  p_data["Match Back"],
                "Match Total": p_data["Match Total"],
                "Match Extra": p_data["Match Extra"],
                "Match Pt":    p_data["Match Pt"],
                "Front GP":    p_data["Front GP"],
                "Back GP":     p_data["Back GP"],
                "Extra GP":    p_data["Extra GP"],
                "Game Pt":     p_data["Game Pt"],
                "Front Putt":  p_data["Putt Front"],
                "Back Putt":   p_data["Putt Back"],
                "Extra Putt":  p_data["Putt Extra"],
                "Putt Pt":     p_data["Putt Pt"],
                "Total Pt":    p_data["Total Pt"],
            })
        
        # Arrow変換エラー回避のため、全体を文字列型に変換
        df = pd.DataFrame(score_data_list)
        df.set_index("Player", inplace=True)
        # ±表示カラムは表示用として保持（ここでは既に文字列になっています）
        df = df.astype(str)
        
        # 順位ベースグラデーションのオプション
        st.write("### スコア詳細")
        
        # 色付けオプション
        col1, col2 = st.columns(2)
        with col1:
            use_ranking_colors = st.checkbox("順位ベースのグラデーション表示", value=False, key="ranking_colors")
        with col2:
            if use_ranking_colors:
                ranking_column = st.selectbox(
                    "順位判定に使用する列を選択",
                    options=['Total Score', 'Front Score', 'Back Score', 'Total Pt', 'Game Pt'],
                    index=0,
                    key="ranking_column"
                )
        
        # 列ごとに適切な色付け関数を適用
        styled_df = df.style.apply(highlight_total_only, axis=1)
        
        if use_ranking_colors and 'ranking_column' in locals():
            # 順位ベースグラデーションを適用
            ranking_colors = apply_ranking_colors_to_dataframe(df, ranking_column)
            styled_df = styled_df.apply(lambda x: ranking_colors, axis=0, subset=[ranking_column])
              # 他の列は通常の色付け
            for column in df.columns:
                if column != ranking_column:
                    color_func = get_color_function_for_column(column)
                    styled_df = styled_df.map(color_func, subset=[column])
        else:
            # 通常の色付け
            for column in df.columns:
                color_func = get_color_function_for_column(column)
                styled_df = styled_df.map(color_func, subset=[column])
        
        # プレイヤー名（インデックス）のスタイルのみを設定
        styled_df = styled_df.set_table_styles([
            {
                'selector': 'th.row_heading',  # 行ヘッダー（プレイヤー名）のスタイル
                'props': [
                    ('color', '#495057 !important'),
                    ('background-color', '#f8f9fa !important'),
                    ('font-weight', 'bold !important'),
                    ('border', '1px solid #dee2e6 !important')
                ]
            }
        ])

        st.dataframe(styled_df, use_container_width=True)
        
        # マッチ対戦表の作成と表示
        if handicaps_data:
            match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
            match_matrix_reset = match_matrix.reset_index()
            match_matrix_reset.rename(columns={'index': 'Player'}, inplace=True)
            m_df = match_matrix_reset.astype(str)
            m_df.set_index("Player", inplace=True)  # スコア詳細と同じようにインデックスに設定
            styled_matrix = m_df.style.map(color_func)
            
            # プレイヤー名（インデックス）のスタイルのみを設定（スコア詳細と同じ書式）
            styled_matrix = styled_matrix.set_table_styles([
                {
                    'selector': 'th.row_heading',  # 行ヘッダー（プレイヤー名）のスタイル
                    'props': [
                        ('color', '#495057 !important'),
                        ('background-color', '#f8f9fa !important'),
                        ('font-weight', 'bold !important'),
                        ('border', '1px solid #dee2e6 !important')
                    ]
                }
            ])
            
            st.write("### マッチ対戦表")
            st.dataframe(
                styled_matrix,
                use_container_width=True
            )
            
            # 詳細なマッチ結果の作成と表示
            match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
            df_reset = match_results.reset_index()
            df_reset.rename(columns={'index': 'Player'}, inplace=True)
            r_df = df_reset.astype(str)
            r_df.set_index("Player", inplace=True)  # スコア詳細と同じようにインデックスに設定
            styled_results = r_df.style.map(color_func)
            
            # プレイヤー名（インデックス）のスタイルのみを設定（スコア詳細と同じ書式）
            styled_results = styled_results.set_table_styles([
                {
                    'selector': 'th.row_heading',  # 行ヘッダー（プレイヤー名）のスタイル
                    'props': [
                        ('color', '#495057 !important'),
                        ('background-color', '#f8f9fa !important'),
                        ('font-weight', 'bold !important'),
                        ('border', '1px solid #dee2e6 !important')
                    ]
                }
            ])
            
            st.write("### 詳細なマッチ結果")
            st.dataframe(
                styled_results,
                use_container_width=True
            )
        else:
            st.info("ハンディキャップが設定されていないため、マッチ対戦表は表示されません。")
            
        # PDF出力機能
        st.subheader("PDF出力")
        if st.button("スコア表をPDFで出力", use_container_width=True):
            try:
                pdf_df = df.copy()
                # PDF用に数値に戻す必要がある場合、各列ごとに変換してください
                for col in pdf_df.columns:
                    pdf_df[col] = pd.to_numeric(pdf_df[col], errors='coerce').fillna(0)
                
                if handicaps_data:
                    pdf_buffer = generate_pdf(pdf_df, match_results, match_matrix, active_round)
                else:
                    pdf_buffer = generate_pdf(pdf_df, None, None, active_round)
                
                # PDFファイル名を生成
                pdf_filename = get_pdf_filename(active_round)
                
                # ダウンロードボタンを提供
                st.download_button(
                    label="📥 PDFをダウンロード",
                    data=pdf_buffer,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
                
                st.success("✅ PDFが正常に生成されました。ダウンロードボタンをクリックしてPDFをダウンロードしてください。")
                
                # SNS シェア用の情報を表示
                with st.expander("📱 SNS での共有について"):
                    st.info("""
                    **現在のシェア方法:**
                    1. 上記のダウンロードボタンでPDFファイルをダウンロード
                    2. ダウンロードしたPDFファイルをSNSに直接添付して投稿
                    
                    **将来実装予定の機能:**
                    - クラウドストレージによるシェア用URL生成
                    - SNS投稿時のプレビュー表示対応
                    - ワンクリック共有機能
                    """)
                    
            except Exception as e:
                st.error(f"PDFの生成中にエラーが発生しました: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

        # ラウンド確定機能
        if not active_round['finalized']:
            st.markdown("---")
            st.subheader("ラウンド確定")
            st.warning("⚠️ 確定すると、以降はスコア入力画面からの修正ができなくなります。")
            st.info("確定後にスコアの修正が必要な場合は、管理画面のスコア修正タブから行ってください。")
            
            if st.button("このラウンドを確定する", type="primary"):
                try:
                    if handicaps_data:
                        updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
                    else:
                        updated_player_data = player_data
                    
                    if save_round_results(round_id, updated_player_data):
                        update_data = {}
                        for mid in player_ids:
                            data = updated_player_data[mid]
                            update_data[mid] = {
                                'front_game_pt': data.get('Front GP', 0),
                                'back_game_pt':  data.get('Back GP', 0),
                                'extra_game_pt': data.get('Extra GP', 0)
                                # total_ptはround_resultsテーブルで管理するため、scoreテーブルの更新からは除外
                            }
                        
                        success, updates, failures = update_scores_batch(round_id, update_data)
                        if success:
                            # Finalizedフラグを更新
                            supabase.table('rounds').update({'finalized': True}).eq('round_id', round_id).execute()
                            st.success("🎉 ラウンドを確定しました！")
                            st.info("今後スコアの修正が必要な場合は、管理画面のスコア修正タブから行ってください。")
                            # 画面を再読み込み
                            st.rerun()
                        else:
                            st.warning(f"一部のスコア更新に成功しましたが、{len(failures)}件の失敗がありました。")
                            for failure in failures:
                                st.error(f"プレイヤーID {failure['member_id']}: {failure['error']}")
                    else:
                        st.error("計算結果の保存に失敗しました。")
                except Exception as e:
                    st.error(f"ラウンドの確定中にエラーが発生しました: {str(e)}")
        else:    
            # 確定済みのラウンドの場合、管理画面へのリンクを表示
            st.markdown("---")
            if st.button("管理画面でスコアを修正する", use_container_width=True):
                st.session_state.admin_selected_round_id = round_id
                switch_page("08_管理画面")
        
        # 開発者向けツール
        st.markdown("---")

    except Exception as e:
        st.error(f"ページの読み込み中にエラーが発生しました: {str(e)}")
        st.error("ページを再読み込みしてください。問題が続く場合は管理者にお問い合わせください。")
        import traceback
        with st.expander("詳細なエラー情報"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    st.set_page_config(
    page_title="結果確認 - Golf Score App",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)
    run()
