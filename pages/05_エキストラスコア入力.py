import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
from modules.db import supabase
from streamlit_extras.switch_page_button import switch_page
# 追加: 必要なモジュールをインポート
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback
from components.navigation import show_navigation  # ナビゲーションコンポーネントを追加

def run():
    # ナビゲーションバーを表示（ページ間の移動を容易にする）
    show_navigation(active_page="エキストラスコア入力")
    
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("エキストラスコア入力")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")
    
    # アクティブなラウンドIDをセッション状態から取得
    if "active_round_id" not in st.session_state:
        st.error("ラウンドが選択されていません。ホーム画面から選択してください。")
        if st.button("ホームに戻る"):
            switch_page("main")
        return
    
    round_id = st.session_state.active_round_id
      # ラウンド情報を取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        st.error("ラウンド情報が見つかりません。")
        return
    
    active_round = round_result.data[0]
    st.write(f"### {active_round['date_played']} - {active_round['course_name']}")
    
    # has_extraフラグを更新
    if not active_round.get('has_extra'):
        supabase.table('rounds').update({'has_extra': True}).eq('round_id', round_id).execute()
        st.info("このラウンドにエキストラホールが設定されました。")
    
    # スコア情報を取得
    scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores.data:
        st.error("スコアデータが見つかりません。")
        return
      # 並び替え: member_idでソート
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])    # バックスコアがまだ入力されていない場合の警告
    back_scores_missing = any(score.get('back_score', 0) == 0 for score in scores_data)
    if back_scores_missing and not st.session_state.get('skip_back_warning', False):
        st.warning("⚠️ 一部のバックスコアがまだ入力されていません。先にバックスコアを入力することをお勧めします。")
        
        # 未入力のプレイヤーを表示
        missing_players = []
        for score in scores_data:
            if score.get('back_score', 0) == 0:
                player_name = score['member']['name'] if score['member'] else f"Player {score['member_id']}"
                missing_players.append(player_name)
        
        if missing_players:
            st.error(f"バックスコア未入力: {', '.join(missing_players)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("バックスコア入力へ", type="primary"):
                switch_page("03_バックスコア入力")
        with col2:
            if st.button("このまま続行"):
                st.session_state['skip_back_warning'] = True
                st.rerun()
        
        return  # 警告表示中はフォームを表示しない    # セッション状態の初期化（データベース値を一度だけ設定）
    initialization_key = f"extra_initialized_{round_id}"
    if initialization_key not in st.session_state:
        st.session_state[initialization_key] = True
        for score in scores_data:
            member_id = score['member_id']
            
            # データベースから取得した値をセッション状態に設定
            score_values = {
                'extra_score': score.get('extra_score'),
                'extra_putt': score.get('extra_putt'), 
                'extra_game_pt': score.get('extra_game_pt')
            }
            
            for field, db_value in score_values.items():
                session_key = f"{field}_{member_id}"
                
                # データベースの値を優先（nullの場合は0、-300の異常値も0に）
                if db_value is not None and db_value != -300:
                    st.session_state[session_key] = db_value
                else:
                    st.session_state[session_key] = 0
    
    # プレイヤーごとのスコア入力フォーム
    st.write("### スコア入力")
    
    # フォーム送信状態を追跡
    if "extra_form_submitted" not in st.session_state:
        st.session_state.extra_form_submitted = False
      # プレイヤーごとの入力フォームを表示
    with st.form("extra_scores_form"):
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            st.write(f"#### {player_name}")
              # 現在のデータベース値を表示
            current_extra_score = score.get('extra_score', 0)
            current_extra_putt = score.get('extra_putt', 0)
            current_extra_game_pt = score.get('extra_game_pt', 0)
            
            if current_extra_score != 0 or current_extra_putt != 0 or current_extra_game_pt != 0:
                st.info(f"現在の値 - スコア: {current_extra_score}, パット: {current_extra_putt}, GP: {current_extra_game_pt}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.number_input(
                    "エキストラスコア", 
                    min_value=0, 
                    max_value=100,
                    key=f"extra_score_{member_id}",
                    help=f"現在: {current_extra_score}"
                )
            
            with col2:
                st.number_input(
                    "エキストラパット",
                    min_value=0,
                    max_value=40,
                    key=f"extra_putt_{member_id}",
                    help=f"現在: {current_extra_putt}"
                )
            
            with col3:
                st.number_input(
                    "エキストラゲームポイント",
                    min_value=-300,
                    max_value=300,
                    key=f"extra_game_pt_{member_id}",
                    help=f"現在: {current_extra_game_pt}"
                )
            
            st.write("---")  # プレイヤー間の区切り線
        
        # 送信ボタン
        submitted = st.form_submit_button("スコアを保存", use_container_width=True)
        
        if submitted:
            st.session_state.extra_form_submitted = True
      # 入力内容の確認と保存
    if st.session_state.extra_form_submitted:
        st.success("スコアを保存しました！")
        
        # 保存結果を記録
        save_success = True
        save_errors = []        # スコア情報を更新
        for score in scores_data:
            try:
                member_id = score['member_id']
                member_name = score['member']['name'] if score['member'] else f"Player {member_id}"
                
                # セッション状態から値を取得
                extra_score_key = f"extra_score_{member_id}"
                extra_putt_key = f"extra_putt_{member_id}" 
                extra_game_pt_key = f"extra_game_pt_{member_id}"
                
                extra_score = st.session_state.get(extra_score_key, 0)
                extra_putt = st.session_state.get(extra_putt_key, 0)
                extra_game_pt = st.session_state.get(extra_game_pt_key, 0)
                
                # 入力値の検証
                if extra_score < 0 or extra_score > 100:
                    raise ValueError(f"エキストラスコア ({extra_score}) が範囲外です")
                if extra_putt < 0 or extra_putt > 40:
                    raise ValueError(f"エキストラパット ({extra_putt}) が範囲外です")
                if extra_game_pt < -300 or extra_game_pt > 300:
                    raise ValueError(f"エキストラゲームポイント ({extra_game_pt}) が範囲外です")
                
                # 更新データを作成
                update_data = {
                    'extra_score': extra_score,
                    'extra_putt': extra_putt,
                    'extra_game_pt': extra_game_pt
                }
                
                # データベース更新
                result = supabase.table('score').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
                
                # 更新結果を確認
                if not result.data:
                    raise Exception(f"データベース更新に失敗しました（結果が空）")
                
                # 個別の成功メッセージは削除
                # st.write(f"✓ {member_name} のエキストラスコアを保存しました")
                
            except Exception as e:
                save_success = False
                error_msg = f"{member_name}: {str(e)}"
                save_errors.append(error_msg)
                st.error(f"❌ {error_msg}")
        
        # 保存結果のサマリー
        if save_success:
            st.success("全プレイヤーのエキストラスコアが正常に保存されました")
        else:
            st.error("一部のプレイヤーのスコア保存に失敗しました")
            for error in save_errors:
                st.error(f"- {error}")
            return  # エラーがある場合は計算処理をスキップ        
        # ▼▼▼ 追加: 計算結果をround_resultsに保存 ▼▼▼
        try:
            # --- 進捗コメント出力をすべて削除 ---
            # 現在のround_idのすべてのスコアを取得
            scores = get_scores_with_fallback(round_id)
            if not scores:
                raise Exception("スコアデータの取得に失敗しました")
            
            # ハンディキャップ情報を取得
            handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
            handicaps_data = handicaps_result.data
            
            # ラウンド情報を取得
            round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
            active_round = round_result.data[0] if round_result.data else None
            if not active_round:
                raise Exception("ラウンド情報の取得に失敗しました")
            
            # round_resultsを取得（存在する場合）
            round_results = get_round_results(round_id)
            
            # プレイヤーデータ初期化
            from modules.data_formatter import initialize_player_data
            player_data = initialize_player_data(scores, round_results)
            player_ids = sorted(list(player_data.keys()))
            
            # ハンディキャップ辞書作成
            handicaps = {}
            total_only_set = set()
            if handicaps_data:
                for h in handicaps_data:
                    handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
                    handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
                    if 'total_only' in h and h['total_only']:
                        total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
            
            # ポイント計算と保存
            updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
            
            # round_resultsに保存
            save_result = save_round_results(round_id, updated_player_data)
            
            if save_result:
                st.success("✅ 計算結果をround_resultsテーブルに保存しました")
            else:
                st.error("❌ 計算結果の保存に失敗しました")
                
        except Exception as e:
            st.error(f"❌ 計算処理中にエラーが発生しました: {str(e)}")
            st.write("詳細なエラー情報:")
            import traceback
            st.code(traceback.format_exc())            # エラーが発生してもページを継続表示
          
        # 初期化フラグをリセットして、次回アクセス時にデータベースから最新値を取得
        initialization_key = f"extra_initialized_{round_id}"
        if initialization_key in st.session_state:
            del st.session_state[initialization_key]
        
        # フォーム送信状態をリセット
        st.session_state.extra_form_submitted = False
        # 結果確認ページへのリンク
        st.info("結果確認ページへはサイドバーから選択してください。")
        # # ↓もし遷移が機能する場合は下記を有効化
        # if st.button("結果確認へ", use_container_width=True, key="to_results"):
        #     st.session_state.active_round_id = round_id
        #     st.cache_data.clear()
        #     switch_page("06_結果確認")
        
        # 確認表示
        st.write("### 入力内容の確認")
        
        # 入力されたスコアの一覧表を表示
        scores_df = []
        for score in scores_data:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            scores_df.append({
                'プレイヤー': player_name,
                'エキストラスコア': st.session_state[f"extra_score_{member_id}"],
                'エキストラパット': st.session_state[f"extra_putt_{member_id}"],
                'エキストラゲームポイント': st.session_state[f"extra_game_pt_{member_id}"]
            })
        
        # DataFrameとして表示
        scores_table = pd.DataFrame(scores_df)
        st.dataframe(scores_table, use_container_width=True)
    
    # 結果確認ページへのリンク
    if st.button("結果確認へ", use_container_width=True):
        switch_page("06_結果確認")

if __name__ == "__main__":
    run()
