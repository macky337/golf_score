import streamlit as st
import pandas as pd
from modules.supabase_client import get_supabase_client, cache_scores_in_session, get_scores_with_fallback, update_scores_batch
from modules.pdf_generator import generate_pdf, set_font, get_pdf_filename
from modules.match_analyzer import create_match_matrix, create_detailed_match_results
from modules.data_formatter import highlight_total_only, color_points
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from streamlit_extras.switch_page_button import switch_page
from modules.debug import handle_error

from modules.game_points import calculate_total_game_points
from modules.calculation_logic import calculate_player_points

# 日本語対応フォントの登録
FONT_NAME = "Helvetica"
if os.path.exists("ipaexg.ttf"):
    try:
        pdfmetrics.registerFont(TTFont('IPAexGothic', 'ipaexg.ttf'))
        FONT_NAME = "IPAexGothic"
        set_font(FONT_NAME)
    except Exception as e:
        st.warning(f"フォント登録エラー: {e}. デフォルトHelveticaを使用します。")
else:
    st.warning("ipaexg.ttf が見つかりません。PDF出力は Helvetica となります（日本語表示に問題が生じる可能性があります）。")


def run():
    supabase = get_supabase_client()
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("結果確認")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")
    
    with col1:
        st.markdown("""
            <style>
            /* スコア詳細テーブルのプレイヤー列を強制的に固定表示するためのより強力なCSS */
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
                left: 0 !重要;
                background-color: white !important;
                z-index: 10 !important;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !important;
                min-width: 100px !重要;
            }
            [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:first-child th:first-child,
            [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:nth-child(2) th:first-child,
            [data-testid="stDataFrame"] > div > div > div > div > div table thead tr:nth-child(2) th:first-child {
                z-index: 20 !important;
                background-color: #f0f2f6 !important;
            }
            [data-testid="stDataFrame"] div[data-testid="stTable"] table thead th,
            [data-testid="stDataFrame"] > div > div > div > div > div table thead th {
                background-color: #f0f2f6 !important;
                position: relative !重要;
                z-index: 5 !重要;
            }
            [data-testid="stDataFrame"] > div {
                overflow-x: auto !重要;
                max-width: 100% !重要;
                display: block !重要;
            }
            [data-testid="stDataFrame"] div[data-testid="stTable"] table tr th:first-child,
            [data-testid="stDataFrame"] > div > div > div > div > div table tr th:first-child {
                position: sticky !重要;
                left: 0 !重要;
                z-index: 20 !重要;
            }
            html body [data-testid="stDataFrame"] div[data-testid="stTable"] table td:first-of-type {
                position: sticky !重要;
                left: 0 !重要;
                background-color: white !重要;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("""
            <style>
            /* DataFrame全体を横スクロール可能に */
            [data-testid="stDataFrame"] > div {
                overflow-x: auto !重要;
                max-width: 100% !重要;
                display: block !重要;
            }

            /* テーブルにposition: relativeを付与 */
            [data-testid="stDataFrame"] table {
                position: relative !重要;
                border-collapse: collapse !重要;
                table-layout: auto !重要;
            }

            /* 先頭列（Player列）を固定表示 */
            [data-testid="stDataFrame"] table th:nth-child(3),
            [data-testid="stDataFrame"] table td:nth-child(3) {
                position: sticky !重要;
                left: 0 !重要;
                background-color: white !重要;
                z-index: 10 !重要;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !重要;
                min-width: 100px !重要;
            }

            /* ヘッダーの先頭セルに追加スタイルを適用 */
            [data-testid="stDataFrame"] table thead tr:first-child th:nth-child(3) {
                z-index: 20 !重要;
                background-color: #f0f2f6 !重要;
            }
            </style>
        """, unsafe_allow_html=True)

    # 未確定ラウンドの取得
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
        round_id = int(selected_round_str.split("ID: ")[1].rstrip(")"))
        
        try:
            # データを1回だけ取得
            scores = get_scores_with_fallback(round_id)
            if not scores:
                st.warning("スコアデータが見つかりません。")
                # ユーザーにアクションを促す
                st.info("このラウンドにはスコアデータが登録されていないようです。フロントスコア入力から始めるか、新しいラウンドを設定してください。")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("新しいラウンドを設定"):
                        # セッションに選択したラウンドIDを保存
                        st.session_state.active_round_id = round_id
                        switch_page("01_ラウンド設定")
                with col2:
                    if st.button("フロントスコア入力へ"):
                        # セッションに選択したラウンドIDを保存
                        st.session_state.active_round_id = round_id
                        switch_page("02_フロントスコア入力")
                return

            round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
            active_round = round_result.data[0] if round_result.data else None
            if not active_round:
                st.warning("選択されたラウンドが見つかりません。")
                return

            handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
            handicaps_data = handicaps_result.data

        except Exception as e:
            handle_error(e)
            return

        # プレイヤーデータの初期化（一度だけ）
        player_data = {}
        for sc in scores:
            player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {sc.get('member_id', 'Unknown')}"

            # デバッグ用: スコアデータの全フィールド名と値を出力
            if round_id == 16:  # 千葉よみうりのラウンドIDのみ
                st.write(f"### デバッグ情報: {player_name} のスコアデータ")
                debug_data = {k: v for k, v in sc.items() if k not in ['member']}
                st.json(debug_data)

            # データベースから取得した値をそのまま使用
            player_data[sc['member_id']] = {
                "Player": player_name,
                "Front Score": sc.get('front_score', 0),
                "Back Score": sc.get('back_score', 0),
                "Extra Score": sc.get('extra_score', 0),
                "Total Score": sc.get('front_score', 0) + sc.get('back_score', 0),
                # Game Point関連
                "Front GP": sc.get('front_game_pt', 0) or 0,
                "Back GP": sc.get('back_game_pt', 0) or 0,
                "Extra GP": sc.get('extra_game_pt', 0) or 0,
                "Game Pt": (sc.get('front_game_pt', 0) or 0) + (sc.get('back_game_pt', 0) or 0) + (sc.get('extra_game_pt', 0) or 0),
                # Match Point関連
                "Match Front": sc.get('match_front', 0),
                "Match Back": sc.get('match_back', 0),
                "Match Total": sc.get('match_total', 0),
                "Match Extra": sc.get('match_extra', 0),
                "Match Pt": sc.get('match_pt', 0),
                # Putt関連
                "Front Putt": sc.get('front_putt', 0),
                "Back Putt": sc.get('back_putt', 0),
                "Extra Putt": sc.get('extra_putt', 0),
                "Putt Pt": sc.get('putt_pt', 0),  # putt_pt を Putt Pt として表示
                # Total Point
                "Total Pt": sc.get('total_pt', 0)
            }

        player_ids = sorted(list(player_data.keys()))
        n_players = len(player_ids)

        # データベースからTotal Only情報を取得
        handicaps = {}
        total_only_set = set()
        if handicaps_data:
            for h in handicaps_data:
                handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                if 'total_only' in h and h['total_only']:
                    total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

        # スコア詳細の表を作成
        df_columns = [
            "Player",
            "Front Score", "Back Score", "Total Score", "Extra Score",
            "Match Front", "Match Back", "Match Total", "Match Extra", "Match Pt",
            "Front GP", "Back GP", "Extra GP", "Game Pt",
            "Front Putt", "Back Putt", "Extra Putt", "Putt Pt",
            "Total Pt"
        ]

        # データベースから取得した値をそのまま使ってDataFrameを作成
        score_data_list = []
        for sc in scores:
            player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {sc.get('member_id', 'Unknown')}"

            # データベースのスコアをそのまま使用
            score_data_list.append({
                "Player": player_name,
                "Front Score": sc.get('front_score', 0) or 0,
                "Back Score": sc.get('back_score', 0) or 0,
                "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
                "Extra Score": sc.get('extra_score', 0) or 0,
                # マッチポイント - データベースから直接取得
                "Match Front": sc.get('match_front', 0) or 0,
                "Match Back": sc.get('match_back', 0) or 0,
                "Match Total": sc.get('match_total', 0) or 0,
                "Match Extra": sc.get('match_extra', 0) or 0,
                "Match Pt": sc.get('match_pt', 0) or 0,
                # ゲームポイント
                "Front GP": sc.get('front_game_pt', 0) or 0,
                "Back GP": sc.get('back_game_pt', 0) or 0,
                "Extra GP": sc.get('extra_game_pt', 0) or 0,
                "Game Pt": (sc.get('front_game_pt', 0) or 0) + (sc.get('back_game_pt', 0) or 0) + (sc.get('extra_game_pt', 0) or 0),
                # パット
                "Front Putt": sc.get('front_putt', 0) or 0,
                "Back Putt": sc.get('back_putt', 0) or 0,
                "Extra Putt": sc.get('extra_putt', 0) or 0,
                "Putt Pt": sc.get('putt_pt', 0) or 0,
                # 合計ポイント
                "Total Pt": sc.get('total_pt', 0) or 0
            })

            # player_dataにもデータを保存（他の機能用）
            player_data[sc['member_id']] = {
                "Player": player_name,
                "Front Score": sc.get('front_score', 0) or 0,
                "Back Score": sc.get('back_score', 0) or 0,
                "Extra Score": sc.get('extra_score', 0) or 0,
                "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
                # Game Point関連
                "Front GP": sc.get('front_game_pt', 0) or 0,
                "Back GP": sc.get('back_game_pt', 0) or 0,
                "Extra GP": sc.get('extra_game_pt', 0) or 0,
                "Game Pt": (sc.get('front_game_pt', 0) or 0) + (sc.get('back_game_pt', 0) or 0) + (sc.get('extra_game_pt', 0) or 0),
                # Match Point関連（データベースから直接取得）
                "Match Front": sc.get('match_front', 0) or 0,
                "Match Back": sc.get('match_back', 0) or 0,
                "Match Total": sc.get('match_total', 0) or 0,
                "Match Extra": sc.get('match_extra', 0) or 0,
                "Match Pt": sc.get('match_pt', 0) or 0,
                # Putt関連
                "Front Putt": sc.get('front_putt', 0) or 0,
                "Back Putt": sc.get('back_putt', 0) or 0,
                "Extra Putt": sc.get('extra_putt', 0) or 0,
                "Putt Pt": sc.get('putt_pt', 0) or 0,
                # Total Point
                "Total Pt": sc.get('total_pt', 0) or 0
            }

        # DataFrameを作成
        df = pd.DataFrame(score_data_list)
        df.set_index("Player", inplace=True)
        df = df[df_columns[1:]]  # "Player"列は既にインデックスになっているので除外

        # デバッグ情報（元のデータ）
        if round_id == 16:  # 千葉よみうりのラウンドIDのみ
            st.write("### 元のデータ（修正後）")
            for sc in scores:
                player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {sc.get('member_id', 'Unknown')}"
                st.write(f"{player_name}: Match Front={sc.get('match_front', 0)}, Match Back={sc.get('match_back', 0)}, Match Total={sc.get('match_total', 0)}")

        # DataFrameのフォーマット
        formatted_df = df.copy()

        # 数値列を+/-付きの文字列に変換
        for col in formatted_df.columns:
            if col.endswith((' Pt', ' GP')) or col in ['Match Front', 'Match Back', 'Match Total', 'Match Extra']:
                # 値が0の場合は "0"、それ以外は "+数値" または "-数値" の形式で表示
                formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:+d}" if x != 0 else "0")
                
        # デバッグ情報を追加（確認用）
        if round_id == 16:  # ID 16のラウンドのみ
            st.write("### データ変換前:")
            st.dataframe(df[['Match Front', 'Match Back', 'Match Total', 'Match Extra', 'Match Pt']], use_container_width=True)
            
            st.write("### データ変換後:")
            st.dataframe(formatted_df[['Match Front', 'Match Back', 'Match Total', 'Match Extra', 'Match Pt']], use_container_width=True)

        st.write("### スコア詳細")
        st.dataframe(formatted_df, use_container_width=True)

        # マッチ対戦表と詳細なマッチ結果の表示
        st.write("### マッチ対戦表")
        match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
        match_matrix_reset = match_matrix.reset_index()
        match_matrix_reset.rename(columns={'index': 'Player'}, inplace=True)
        match_matrix_reset = match_matrix_reset.apply(lambda col: col.astype(str) if col.dtype == object else col)

        st.dataframe(
            match_matrix_reset.style.map(color_points).format(None),
            use_container_width=True,
            hide_index=True
        )

        st.write("### 詳細なマッチ結果")
        match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
        df_reset = match_results.reset_index()
        df_reset.rename(columns={'index': 'Player'}, inplace=True)
        df_reset = df_reset.apply(lambda col: col.astype(str) if col.dtype == object else col)

        st.dataframe(
            df_reset.style.apply(highlight_total_only, axis=1).map(color_points).format(None),
            use_container_width=True,
            hide_index=True
        )

        # PDF出力機能
        st.subheader("PDF出力")
        if st.button("スコア表をPDFで出力"):
            try:
                pdf_df = df.copy()
                for col in pdf_df.columns:
                    if col.endswith((' Pt', 'Front', 'Back', 'Total', 'Extra')) and col not in [
                        'Front Score', 'Back Score', 'Total Score', 'Extra Score',
                        'Putt Front', 'Putt Back', 'Putt Extra'
                    ]:
                        pdf_df[col] = pd.to_numeric(pdf_df[col], errors='coerce').fillna(0)

                # "Player" を df_columns から削除
                pdf_df_columns = [col for col in df_columns if col != "Player"]
                pdf_df = pdf_df[pdf_df_columns]

                pdf_buffer = generate_pdf(pdf_df, match_results, match_matrix, active_round)
                pdf_filename = get_pdf_filename(active_round)
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
                st.error(traceback.format_exc())

        # ラウンド確定機能
        if not active_round['finalized']:
            if st.button("このラウンドを確定する"):
                try:
                    # プレイヤーデータを集める
                    player_data = {}
                    player_ids = []
                    for sc in scores:
                        player_name = sc['member']['name'] if ('member' in sc and sc['member']) else f"Player {sc.get('member_id', 'Unknown')}"
                        member_id = sc['member_id']
                        player_ids.append(member_id)
                        player_data[member_id] = {
                            "Player": player_name,
                            "Front Score": sc.get('front_score', 0) or 0,
                            "Back Score": sc.get('back_score', 0) or 0,
                            "Extra Score": sc.get('extra_score', 0) or 0,
                            "Total Score": (sc.get('front_score', 0) or 0) + (sc.get('back_score', 0) or 0),
                            "Front Putt": sc.get('front_putt', 0) or 0,
                            "Back Putt": sc.get('back_putt', 0) or 0,
                            "Extra Putt": sc.get('extra_putt', 0) or 0,
                            "Front GP": 0,
                            "Back GP": 0,
                            "Extra GP": 0,
                            "Game Pt": 0,
                            "Match Front": 0,
                            "Match Back": 0,
                            "Match Total": 0,
                            "Match Extra": 0,
                            "Match Pt": 0,
                            "Putt Pt": 0,
                            "Total Pt": 0
                        }

                    # ハンディキャップ情報を集める
                    handicaps = {}
                    total_only_set = set()
                    if handicaps_data:
                        for h in handicaps_data:
                            handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                            if 'total_only' in h and h['total_only']:
                                total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

                    # 全ポイントを再計算
                    from modules.calculation_logic import calculate_player_points
                    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)

                    # スコアテーブルを更新
                    update_data = {}
                    for mid in player_ids:
                        data = updated_player_data[mid]
                        update_data[mid] = {
                            'front_game_pt': data.get('Front GP', 0),
                            'back_game_pt': data.get('Back GP', 0),
                            'extra_game_pt': data.get('Extra GP', 0),
                            'temp_game_pt': data.get('temp_game_pt', 0),
                            'total_game_pt': data.get('total_game_pt', 0),
                            'match_front': data.get('Match Front', 0),
                            'match_back': data.get('Match Back', 0),
                            'match_total': data.get('Match Total', 0),
                            'match_extra': data.get('Match Extra', 0),
                            'match_pt': data.get('Match Pt', 0),
                            'putt_pt': data.get('Putt Pt', 0),
                            'total_pt': data.get('Total Pt', 0)
                        }

                    success, updates, failures = update_scores_batch(round_id, update_data)
                    if success:
                        st.success("ラウンドを確定しました")
                        supabase.table('rounds').update({'finalized': True}).eq('round_id', round_id).execute()
                        if updates:
                            st.rerun()
                    else:
                        st.warning(f"一部のスコア更新に成功しましたが、{len(failures)}件の失敗がありました。")
                        for failure in failures:
                            st.error(f"プレイヤーID {failure['member_id']}: {failure['error']}")
                        if "calculation_results" not in st.session_state:
                            st.session_state.calculation_results = {}
                        st.session_state.calculation_results[round_id] = player_data
                        st.error("スコア更新に失敗しました。再試行してください。")
                except Exception as e:
                    st.error(f"ラウンドの確定中にエラーが発生しました: {str(e)}")
                    if "calculation_results" not in st.session_state:
                        st.session_state.calculation_results = {}
                    st.session_state.calculation_results[round_id] = player_data
                    st.info("計算結果はセッションに保存されました。再試行することで保存できる可能性があります。")

if __name__ == "__main__":
    run()
