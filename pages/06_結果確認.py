import streamlit as st
import pandas as pd
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from streamlit_extras.switch_page_button import switch_page

# ▼▼▼ 必要モジュールのインポート ▼▼▼
from modules.supabase_client import (
    get_supabase_client,
    get_scores_with_fallback,
    update_scores_batch,
)
from modules.pdf_generator import generate_pdf, set_font, get_pdf_filename
from modules.match_analyzer import create_match_matrix, create_detailed_match_results
from modules.data_formatter import highlight_total_only, color_points
from modules.debug import handle_error
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results

# ▼▼▼ フォント登録（日本語対応） ▼▼▼
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


def initialize_player_data(scores, round_results):
    player_data = {}
    for sc in scores:
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
    supabase = get_supabase_client()

    # タイトルとホームボタンのレイアウト
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("結果確認")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")

    st.markdown(
        """
        <style>
        /* スコア詳細テーブルのスタイル設定 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table,
        [data-testid="stDataFrame"] > div > div > div > div > div table {
            position: relative !important;
            border-collapse: collapse !important;
            table-layout: auto !important;
        }
        /* プレイヤー列を固定表示 */
        [data-testid="stDataFrame"] table th:first-child,
        [data-testid="stDataFrame"] table td:first-child {
            position: sticky !important;
            left: 0 !important;
            background-color: white !important;
            z-index: 10 !important;
            box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !important;
            min-width: 100px !important;
        }
        /* ヘッダー行のスタイル */
        [data-testid="stDataFrame"] table thead th {
            position: sticky !重要;
            top: 0 !important;
            background-color: #f0f2f6 !important;
            z-index: 20 !important;
        }
        /* テーブル全体の横スクロール */
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            max-width: 100% !important;
            display: block !important;
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
                switch_page("フロントスコア入力")
        with col2:
            if st.button("バックスコア修正", use_container_width=True):
                st.session_state.active_round_id = round_id
                switch_page("バックスコア入力")
        with col3:
            has_extra = active_round.get('has_extra', False)
            if has_extra:
                if st.button("エキストラスコア修正", use_container_width=True):
                    st.session_state.active_round_id = round_id
                    st.session_state.has_extra = True
                    switch_page("エキストラスコア入力")

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
        handle_error(e)
        return

    # round_results を取得（必ず実行）
    round_results = get_round_results(round_id)
    # ▼▼▼ 追加: round_results を辞書形式に変換（メンバーIDをキーに設定） ▼▼▼
    if isinstance(round_results, list):
        round_results = { item.get('member_id'): item for item in round_results if item.get('member_id') is not None }

    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    active_round = round_result.data[0] if round_result.data else None
    if not active_round:
        st.error("選択されたラウンドが見つかりません。")
        return

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

    df_columns = [
        "Player",
        "Front Score", "Back Score", "Total Score", "Extra Score",
        "Match Front", "Match Back", "Match Total", "Match Extra", "Match Pt",
        "Front GP", "Back GP", "Extra GP", "Game Pt",
        "Front Putt", "Back Putt", "Extra Putt", "Putt Pt",
        "Total Pt"
    ]
    score_data_list = []
    for pid, p_data in player_data.items():
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

    st.write("### スコア詳細")
    st.dataframe(df, use_container_width=True)

    st.write("### マッチ対戦表")
    match_matrix = create_match_matrix(player_data, handicaps, total_only_set)
    match_matrix_reset = match_matrix.reset_index()
    match_matrix_reset.rename(columns={'index': 'Player'}, inplace=True)
    match_matrix_reset = match_matrix_reset.astype(str)
    st.dataframe(
        match_matrix_reset.style.map(color_points).format(None),
        use_container_width=True,
        hide_index=True
    )

    st.write("### 詳細なマッチ結果")
    match_results = create_detailed_match_results(player_data, handicaps, total_only_set)
    df_reset = match_results.reset_index()
    df_reset.rename(columns={'index': 'Player'}, inplace=True)
    df_reset = df_reset.astype(str)
    st.dataframe(
        df_reset.style.apply(highlight_total_only, axis=1).map(color_points).format(None),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("PDF出力")
    if st.button("スコア表をPDFで出力"):
        try:
            pdf_df = df.copy()
            # PDF用に数値に戻す必要がある場合、各列ごとに変換してください
            for col in pdf_df.columns:
                pdf_df[col] = pd.to_numeric(pdf_df[col], errors='coerce').fillna(0)
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

    # ラウンド確定ボタン
    if not active_round['finalized']:
        st.markdown("---")
        st.subheader("ラウンド確定")
        st.warning("⚠️ 確定すると、以降はスコア入力画面からの修正ができなくなります。")
        st.info("確定後にスコアの修正が必要な場合は、管理画面のスコア修正タブから行ってください。")
        if st.button("このラウンドを確定する", type="primary"):
            try:
                updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
                if save_round_results(round_id, updated_player_data):
                    update_data = {}
                    for mid in player_ids:
                        data = updated_player_data[mid]
                        update_data[mid] = {
                            'front_game_pt': data.get('Front GP', 0),
                            'back_game_pt':  data.get('Back GP', 0),
                            'extra_game_pt': data.get('Extra GP', 0),
                            'total_pt':      data.get('Total Pt', 0)
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
                    if "calculation_results" not in st.session_state:
                        st.session_state.calculation_results = {}
                    st.session_state.calculation_results[round_id] = updated_player_data
                    st.info("計算結果はセッションに保存されました。再試行してください。")
            except Exception as e:
                st.error(f"ラウンドの確定中にエラーが発生しました: {str(e)}")
                if "calculation_results" not in st.session_state:
                    st.session_state.calculation_results = {}
                st.session_state.calculation_results[round_id] = player_data
                st.info("計算結果はセッションに保存されました。再試行してください。")
    else:
        # 確定済みのラウンドの場合、管理画面へのリンクを表示
        st.markdown("---")
        if st.button("管理画面でスコアを修正する", use_container_width=True):
            st.session_state.admin_selected_round_id = round_id
            switch_page("管理画面")

    st.markdown("---")
    if st.button("過去のラウンドデータを再計算して保存"):
        recalculate_and_save_results()

    if st.button("このラウンドの計算詳細をテスト表示", help="現在のロジックでこのラウンドを再計算し、詳細を表示します"):
        test_calculation_logic(round_id)


def recalculate_and_save_results():
    supabase = get_supabase_client()
    all_rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).execute()
    all_rounds = all_rounds_result.data

    if not all_rounds:
        st.warning("ラウンドデータが見つかりません。")
        return

    for round_data in all_rounds:
        round_id = round_data['round_id']
        st.info(f"ラウンドID {round_id} の再計算を開始します...")
        try:
            scores = get_scores_with_fallback(round_id)
            if not scores:
                st.warning(f"ラウンドID {round_id} のスコアデータが見つかりません。")
                continue
            round_results = get_round_results(round_id)
            handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
            handicaps_data = handicaps_result.data

            player_data = initialize_player_data(scores, round_results)
            player_ids = sorted(list(player_data.keys()))
            handicaps = {}
            total_only_set = set()
            if handicaps_data:
                for h in handicaps_data:
                    handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                    handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                    if 'total_only' in h and h['total_only']:
                        total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

            updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, round_data)
            if save_round_results(round_id, updated_player_data):
                st.success(f"ラウンドID {round_id} の計算結果を保存しました。")
            else:
                st.error(f"ラウンドID {round_id} の計算結果の保存に失敗しました。")
        except Exception as e:
            st.error(f"ラウンドID {round_id} の再計算中にエラーが発生しました: {str(e)}")


def test_calculation_logic(round_id: int):
    st.subheader("計算ロジックのテスト表示")
    supabase = get_supabase_client()
    try:
        scores = get_scores_with_fallback(round_id)
        if not scores:
            st.warning("スコアデータがありません。")
            return
    except Exception as e:
        st.error("スコア取得エラー: {}".format(e))
        return

    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    active_round = round_result.data[0] if round_result.data else {}
    round_results = get_round_results(round_id)
    handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
    handicaps_data = handicaps_result.data if handicaps_result.data else []

    player_data = initialize_player_data(scores, round_results)
    player_ids = sorted(player_data.keys())
    handicaps = {}
    total_only_set = set()
    for h in handicaps_data:
        handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
        handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
        if 'total_only' in h and h['total_only']:
            total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))

    updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)

    with st.expander("計算結果の詳細を表示"):
        st.write("**再計算された各プレイヤーのスコアデータ:**")
        for pid in player_ids:
            data = updated_player_data[pid]
            player_name = data["Player"]
            st.write(f"- **{player_name}**")
            st.write(f"  - Front Score: {data['Front Score']}")
            st.write(f"  - Back Score:  {data['Back Score']}")
            st.write(f"  - Extra Score: {data['Extra Score']}")
            st.write(f"  - Front GP: {data['Front GP']} / Back GP: {data['Back GP']} / Extra GP: {data['Extra GP']} => **Game Pt: {data['Game Pt']}**")
            st.write(f"  - Match Front: {data['Match Front']} / Match Back: {data['Match Back']} / Match Total: {data['Match Total']} / Match Extra: {data['Match Extra']} => **Match Pt: {data['Match Pt']}**")
            st.write(f"  - Putt Front: {data['Putt Front']} / Putt Back: {data['Putt Back']} / Putt Extra: {data['Putt Extra']} => **Putt Pt: {data['Putt Pt']}**")
            st.write(f"  - **Total Pt: {data['Total Pt']}**")
            st.write("---")
    st.success("再計算のテスト表示が完了しました。")


if __name__ == "__main__":
    run()