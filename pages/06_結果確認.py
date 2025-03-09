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
from modules.calculation_logic import calculate_player_points # 追加

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


def test_calculation_logic(round_id):
    """計算ロジックのテストを行う"""
    supabase = get_supabase_client()
    from pages.handicap_calc_logic import process_round_scores
    st.subheader("計算ロジックのテスト")

    scores = get_scores_with_fallback(round_id)
    if not scores:
        st.error("スコアデータが取得できませんでした")
        return

    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data
    if not handicaps_data:
        st.error("ハンディキャップデータが取得できませんでした")
        return

    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    round_data = round_result.data[0] if round_result.data else None
    if not round_data:
        st.error("ラウンド情報が取得できませんでした")
        return

    with st.spinner("計算ロジックをテスト中..."):
        updated_scores = process_round_scores(scores, handicaps_data, round_data)
        st.success(f"{len(updated_scores)}名分のスコア計算が完了しました")

    with st.expander("計算結果の詳細を表示"):
        for score in updated_scores:
            st.write(f"**{score.get('name', score.get('member_id'))}**")
            st.write(f"- Game Pt: {score['game_pt']}")
            st.write(f"- Match Pt: {score['match_pt']}")
            st.write(f"- Put Pt: {score['put_pt']}")
            st.write(f"- Total Pt: {score['total_pt']}")
            st.write("---")


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
                border-collapse: collapse !重要;
                table-layout: auto !important;
            }
            [data-testid="stDataFrame"] div[data-testid="stTable"] table th:first-of-type,
            [data-testid="stDataFrame"] div[data-testid="stTable"] table td:first-of-type,
            [data-testid="stDataFrame"] > div > div > div > div > div table th:first-of-type,
            [data-testid="stDataFrame"] > div > div > div > div > div table td:first-of-type {
                position: sticky !important;
                left: 0 !important;
                background-color: white !important;
                z-index: 10 !重要;
                box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !重要;
                min-width: 100px !重要;
            }
            [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:first-child th:first-child,
            [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:nth-child(2) th:first-child,
            [data-testid="stDataFrame"] > div > div > div > div > div table thead tr:nth-child(2) th:first-child {
                z-index: 20 !重要;
                background-color: #f0f2f6 !重要;
            }
            [data-testid="stDataFrame"] div[data-testid="stTable"] table thead th,
            [data-testid="stDataFrame"] > div > div > div > div > div table thead th {
                background-color: #f0f2f6 !重要;
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
        cache_scores_in_session(round_id)

        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        active_round = round_result.data[0] if round_result.data else None
        if not active_round:
            st.warning("選択されたラウンドが見つかりません。")
            return

        try:
            scores = get_scores_with_fallback(round_id)
        except Exception as e:
            handle_error(e)
            return

        if st.session_state.get("debug_mode", False):
            st.write(f"取得したスコア数: {len(scores)}")
            if scores:
                sample = scores[0]
                st.write(f"サンプルデータ構造: {list(sample.keys())}")

        if not scores:
            st.warning("スコアデータが見つかりません。")
            return

        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        handicaps_data = handicaps_result.data

        player_data = {}
        for sc in scores:
            if 'name' in sc:
                player_name = sc['name']
            elif 'member' in sc and isinstance(sc['member'], dict) and 'name' in sc['member']:
                player_name = sc['member']['name']
            else:
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
                "Front Putt": sc.get('front_putt', 0),
                "Back Putt": sc.get('back_putt', 0),
                "Extra Putt": sc.get('extra_putt', 0),
                "put_pt": sc.get('put_pt', 0),  # 修正：Putt Pt → put_pt
                "Total Pt": sc.get('total_pt', 0),
            }

        player_ids = sorted(list(player_data.keys()))
        n_players = len(player_ids)

        handicaps = {}
        total_only_set = set()
        if handicaps_data:
            for h in handicaps_data:
                handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                if 'total_only' in h and h['total_only']:
                    total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

        if total_only_set:
            st.sidebar.info(f"Total Onlyモード: {len(total_only_set)}ペア")
            for pair in total_only_set:
                pair_list = list(pair)
                name1 = player_data[pair_list[0]]["Player"] if pair_list[0] in player_data else f"Player {pair_list[0]}"
                name2 = player_data[pair_list[1]]["Player"] if pair_list[1] in player_data else f"Player {pair_list[1]}"
                st.sidebar.text(f"- {name1} vs {name2}")

        # ポイント計算ロジックの呼び出し
        player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)

        total_match_pts = sum(player_data[mid]["Match Pt"] for mid in player_ids)
        if abs(total_match_pts) > 0.01:
            st.warning(f"警告: プレイヤー間のマッチポイント合計が0になっていません。合計: {total_match_pts}pt")

        df_columns = [
            "Player",
            "Front Score", "Back Score", "Total Score", "Extra Score",
            "Match Front", "Match Back", "Match Total", "Match Extra", "Match Pt",
            "Front GP", "Back GP", "Extra GP", "Game Pt",
            "Front Putt", "Back Putt", "Extra Putt", "put_pt", "Total Pt"  # 修正：Putt Pt → put_pt
        ]
        df = pd.DataFrame(
            {col: player_data[mid].get(col, 0) for col in df_columns}
            for mid in player_ids
        )

        # ★ Playerをインデックスに
        df.set_index("Player", inplace=True)
        # 追加: DataFrame の object カラムを文字列に変換（Arrow互換を確保）
        df = df.apply(lambda col: col.astype(str) if col.dtype == object else col)

        st.write("### スコア詳細")
        # --- CSSを定義 ---
        st.markdown("""
        <style>
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !重要;
            max-width: 100% !重要;
            display: block !重要;
        }

        [data-testid="stDataFrame"] table {
            position: relative !重要;
            border-collapse: collapse !重要;
            table-layout: auto !重要;
        }

        /* 行インデックス（Player）を固定 */
        [data-testid="stDataFrame"] table tbody tr th {
            position: sticky !重要;
            left: 0 !重要;
            background-color: white !重要;
            z-index: 10 !重要;
            box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !重要;
            min-width: 100px !重要;
        }

        /* ヘッダーのインデックスセル */
        [data-testid="stDataFrame"] table thead tr:first-child th:first-child {
            position: sticky !重要;
            left: 0 !重要;
            z-index: 20 !重要;
            background-color: #f0f2f6 !重要;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- 表示 ---
        st.dataframe(
            df.style.format({
                col: '{:+d}' if col.endswith((' Pt', 'Front', 'Back', 'Total', 'Extra')) 
                        and col not in ['Front Score', 'Back Score', 'Total Score', 'Extra Score',
                                        'Putt Front', 'Putt Back', 'Putt Extra']
                        else '{:d}'
                for col in df.columns
            }),
            use_container_width=True,
            hide_index=False  # ★ インデックスを表示する
        )

        # ★修正★ マッチ対戦表をリセットして「Player」列を作り、行インデックス非表示
        st.write("### マッチ対戦表")
        match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
        match_matrix_reset = match_matrix.reset_index()  # 行インデックスを列に変換
        match_matrix_reset.rename(columns={'index': 'Player'}, inplace=True)  # index → Player
        match_matrix_reset = match_matrix_reset.apply(lambda col: col.astype(str) if col.dtype == object else col)

        st.markdown("""
            <style>
            /* マッチ対戦表のプレイヤー列を固定表示 */
            [data-testid="stDataFrame"] + div + div + div [data-testid="stDataFrame"] table th:first-child,
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

        st.dataframe(
            match_matrix_reset.style.map(color_points).format(None),
            use_container_width=True,
            hide_index=True  # 行インデックス非表示
        )

        # ★修正★ 詳細なマッチ結果も同様にリセットして「Player」列を作成
        st.write("### 詳細なマッチ結果")
        match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
        df_reset = match_results.reset_index()
        df_reset.rename(columns={'index': 'Player'}, inplace=True)
        df_reset = df_reset.apply(lambda col: col.astype(str) if col.dtype == object else col)

        custom_css = """
        <style>
        .detailed-match-results th {
            min-width: 180px !重要; 
            max-width: 180px !重要; 
            white-space: normal !重要;
            height: auto !重要;
            padding: 8px !重要;
        }
        /* Player列を固定表示 */
        [data-testid="stDataFrame"] + div + div + div [data-testid="stDataFrame"] table th:first-child,
        [data-testid="stDataFrame"] + div + div + div [data-testid="stDataFrame"] table td:first-child {
            position: sticky;
            left: 0;
            background-color: white;
            z-index: 1;
            box-shadow: 2px 0px 3px rgba(0,0,0,0.1);
        }
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)
        st.markdown('<div class="detailed-match-results">', unsafe_allow_html=True)

        st.dataframe(
            df_reset.style.apply(highlight_total_only, axis=1).map(color_points).format(None),
            use_container_width=True,
            hide_index=True  # ★修正★ 行インデックスを非表示に
        )
        st.markdown('</div>', unsafe_allow_html=True)

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

        if not active_round['finalized']:
            if st.button("このラウンドを確定する"):
                try:
                    update_data = {}
                    for mid in player_ids:
                        data = player_data[mid]
                        update_data[mid] = {
                            'game_pt': data['Game Pt'],
                            'match_pt': data['Match Pt'],
                            'put_pt': data['put_pt'],  # 修正：Put Pt → put_pt
                            'total_pt': data['Total Pt']
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
