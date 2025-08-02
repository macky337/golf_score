import sys
import os

# モジュールのインポートパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
from modules.db import ensure_supabase
from modules.calculation_logic import calculate_player_points
from modules.round_results import save_round_results, get_round_results
from modules.supabase_client import get_scores_with_fallback

def create_score_input_widget(label, value, min_val, max_val, key, help_text=None):
    """カスタムスコア入力ウィジェット"""
    st.write(f"**{label}**")
    
    # ボタンベースの入力（+-1, +-5ボタン）
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("-5", key=f"{key}_minus5", help="5減らす"):
            new_val = max(min_val, st.session_state.get(key, value) - 5)
            st.session_state[key] = new_val
            st.rerun()
    
    with col2:
        if st.button("-1", key=f"{key}_minus1", help="1減らす"):
            new_val = max(min_val, st.session_state.get(key, value) - 1)
            st.session_state[key] = new_val
            st.rerun()
    
    with col3:
        # 大きな数値表示と直接入力
        current_value = st.session_state.get(key, value)
        st.markdown(f"<div style='text-align: center; font-size: 24px; font-weight: bold; background-color: #f0f2f6; padding: 10px; border-radius: 5px; border: 2px solid #1f77b4;'>{current_value}</div>", unsafe_allow_html=True)
        
        # 直接入力オプション（小さく）
        direct_input = st.number_input(
            "直接入力", 
            min_value=min_val, 
            max_value=max_val, 
            value=current_value,
            key=f"{key}_direct",
            label_visibility="collapsed",
            help=help_text or f"{min_val}から{max_val}の間で入力"
        )
        if direct_input != current_value:
            st.session_state[key] = direct_input
    
    with col4:
        if st.button("+1", key=f"{key}_plus1", help="1増やす"):
            new_val = min(max_val, st.session_state.get(key, value) + 1)
            st.session_state[key] = new_val
            st.rerun()
    
    with col5:
        if st.button("+5", key=f"{key}_plus5", help="5増やす"):
            new_val = min(max_val, st.session_state.get(key, value) + 5)
            st.session_state[key] = new_val
            st.rerun()

def create_golf_score_widget(label, value, key, score_type="score"):
    """ゴルフ専用スコア入力ウィジェット"""
    st.write(f"**{label}**")
    
    if score_type == "score":
        # ゴルフスコア用（30-80の範囲）
        quick_values = [35, 40, 45, 50, 55, 60]
        min_val, max_val = 25, 80
        help_text = "前半9ホールのスコア"
    elif score_type == "putt":
        # パット用（10-25の範囲）
        quick_values = [12, 14, 16, 18, 20, 22]
        min_val, max_val = 8, 30
        help_text = "前半9ホールのパット数"
    else:
        # ゲームポイント用
        quick_values = [-30, -10, 0, 10, 30, 50]
        min_val, max_val = -300, 300
        help_text = "ニアピン、ドラコンなどのポイント"
    
    # クイック選択ボタン
    st.write("クイック選択:")
    cols = st.columns(len(quick_values))
    for i, val in enumerate(quick_values):
        with cols[i]:
            if st.button(str(val), key=f"{key}_quick_{val}", use_container_width=True):
                st.session_state[key] = val
                st.rerun()
    
    # 現在の値表示
    current_value = st.session_state.get(key, value)
    
    # 色分けによる視覚的フィードバック
    if score_type == "score":
        if current_value <= 40:
            color = "#28a745"  # 緑（良いスコア）
        elif current_value <= 50:
            color = "#ffc107"  # 黄（普通）
        else:
            color = "#dc3545"  # 赤（厳しいスコア）
    else:
        color = "#1f77b4"  # 標準色
    
    st.markdown(f"""
    <div style='text-align: center; font-size: 28px; font-weight: bold; 
    background-color: {color}; color: white; padding: 15px; 
    border-radius: 10px; margin: 10px 0;'>
    {current_value}
    </div>
    """, unsafe_allow_html=True)
    
    # 微調整ボタン
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("-5", key=f"{key}_minus5", use_container_width=True):
            st.session_state[key] = max(min_val, current_value - 5)
            st.rerun()
    with col2:
        if st.button("-1", key=f"{key}_minus1", use_container_width=True):
            st.session_state[key] = max(min_val, current_value - 1)
            st.rerun()
    with col3:
        if st.button("+1", key=f"{key}_plus1", use_container_width=True):
            st.session_state[key] = min(max_val, current_value + 1)
            st.rerun()
    with col4:
        if st.button("+5", key=f"{key}_plus5", use_container_width=True):
            st.session_state[key] = min(max_val, current_value + 5)
            st.rerun()
    
    # 詳細入力（折りたたみ）
    with st.expander("詳細入力"):
        direct_value = st.number_input(
            f"{label} (詳細)",
            min_value=min_val,
            max_value=max_val,
            value=current_value,
            key=f"{key}_detail",
            help=help_text
        )
        if direct_value != current_value:
            st.session_state[key] = direct_value

def run():
    st.set_page_config(
        page_title="フロントスコア入力",
        page_icon="⛳",
        layout="wide",
        initial_sidebar_state="collapsed"  # スマホでサイドバーを初期非表示
    )
    
    # 初回アクセス時のテストモード案内
    if "page_visited" not in st.session_state:
        st.session_state.page_visited = True
        if "active_round_id" not in st.session_state:
            st.info("🎉 初回アクセスです！テストモードでUIを体験できます")
    
    # URLパラメータからテストモード起動
    query_params = st.query_params
    if "test" in query_params and "active_round_id" not in st.session_state:
        st.session_state.active_round_id = 901
        st.session_state.test_mode = True
        st.success("🧪 URLパラメータからテストモード開始")
        st.rerun()
    
    # カスタムCSS（スマホ最適化）
    st.markdown("""
    <style>
    .main > div {
        padding-top: 1rem;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
    }
    .player-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #e9ecef;
        margin: 10px 0;
    }
    .progress-indicator {
        background-color: #e9ecef;
        height: 8px;
        border-radius: 4px;
        margin: 20px 0;
    }
    .progress-fill {
        background-color: #28a745;
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # タイトルとプログレス表示
    st.markdown("# ⛳ フロントスコア入力")
    
    # プログレスバー
    st.markdown("""
    <div class="progress-indicator">
        <div class="progress-fill" style="width: 33%;"></div>
    </div>
    <p style='text-align: center; color: #6c757d;'>ステップ 1/3: フロントスコア入力</p>
    """, unsafe_allow_html=True)
    
    # Supabaseクライアント取得
    supabase = ensure_supabase()
    
    # デバッグ情報表示
    with st.sidebar:
        st.write("### 🔍 デバッグ情報")
        st.write(f"ラウンドID: {st.session_state.get('active_round_id', 'なし')}")
        st.write(f"テストモード: {st.session_state.get('test_mode', False)}")
        st.write(f"全セッション: {len(st.session_state)} 項目")
    
    # アクティブラウンドチェック
    if "active_round_id" not in st.session_state:
        st.warning("🚨 ラウンドが選択されていません")
        
        # 大きなテストモードボタン
        st.markdown("### 🧪 クイックスタート")
        st.markdown("データベース接続なしでUIの動作確認ができます")
        
        if st.button("🧪 テストモードで今すぐ開始", use_container_width=True, type="primary", key="quick_test"):
            # テストラウンドIDを設定
            st.session_state.active_round_id = 901
            st.session_state.test_mode = True
            st.success("✅ テストモード開始！")
            st.balloons()
            st.rerun()
        
        st.markdown("---")
        
        # その他のオプション
        with st.expander("� その他のオプション"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**カスタムラウンドID**")
                round_id_input = st.number_input("ラウンドID", min_value=1, max_value=9999, value=901)
                if st.button("設定", key="set_custom_round", use_container_width=True):
                    st.session_state.active_round_id = round_id_input
                    st.session_state.test_mode = True
                    st.success(f"✅ ラウンドID: {round_id_input}")
                    st.rerun()
            
            with col2:
                st.write("**他のページ**")
                st.markdown("- [簡単テスト](http://localhost:8504)")
                st.markdown("- [メインアプリ](http://localhost:8501)")
                st.markdown("- [テストラウンド設定](http://localhost:8503)")
                
                st.write("**テストモード直接リンク**")
                st.markdown("- [テストモードで開始](http://localhost:8502?test=1)")
        
        return
    
    round_id = st.session_state.active_round_id
    
    # ラウンド情報取得
    try:
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        if not round_result.data:
            st.error("ラウンド情報が見つかりません")
            
            # テストデータを提供
            st.write("### 🧪 テストデータモード")
            if st.button("テストデータで続行", use_container_width=True, type="primary"):
                # テストデータを作成
                active_round = {
                    'round_id': round_id,
                    'date_played': '2025-08-02',
                    'course_name': 'テストゴルフ場',
                    'finalized': False,
                    'has_extra': False
                }
                st.session_state['test_mode'] = True
                st.session_state['test_round_data'] = active_round
                st.write("✅ テストデータモードで続行")
                st.rerun()
            
            if st.button("🧪 テストラウンド設定に戻る", use_container_width=True):
                st.info("テストラウンド設定: http://localhost:8503")
            return
        
        active_round = round_result.data[0]
        st.session_state['test_mode'] = False
        
    except Exception as e:
        st.error(f"データベース接続エラー: {e}")
        
        # テストデータモードを提供
        st.write("### 🧪 オフラインテストモード")
        st.write("データベースに接続できませんが、UIのテストは可能です")
        
        if st.button("オフラインテストで続行", use_container_width=True, type="primary"):
            active_round = {
                'round_id': round_id,
                'date_played': '2025-08-02',
                'course_name': 'テストゴルフ場（オフライン）',
                'finalized': False,
                'has_extra': False
            }
            st.session_state['test_mode'] = True
            st.session_state['test_round_data'] = active_round
            st.write("✅ オフラインテストモードで続行")
            st.rerun()
        
        return
    
    # テストモードの場合はセッション状態からラウンド情報を取得
    if st.session_state.get('test_mode', False):
        active_round = st.session_state.get('test_round_data', {
            'round_id': round_id,
            'date_played': '2025-08-02',
            'course_name': 'テストゴルフ場',
            'finalized': False,
            'has_extra': False
        })
    
    # ラウンド情報表示（テストモード表示）
    test_indicator = " 🧪 (テストモード)" if st.session_state.get('test_mode', False) else ""
    bg_color = "#fff3cd" if st.session_state.get('test_mode', False) else "#e7f3ff"
    border_color = "#ffc107" if st.session_state.get('test_mode', False) else "#007bff"
    text_color = "#856404" if st.session_state.get('test_mode', False) else "#007bff"
    
    st.markdown(f"""
    <div style='background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color};'>
    <h4 style='margin: 0; color: {text_color};'>📅 {active_round['date_played']}{test_indicator}</h4>
    <h5 style='margin: 5px 0 0 0; color: #495057;'>🏌️ {active_round['course_name']}</h5>
    </div>
    """, unsafe_allow_html=True)
    
    # スコア情報取得
    if st.session_state.get('test_mode', False):
        # テストモード用のダミーデータ
        scores_data = [
            {
                'member_id': 901,
                'member': {'name': 'テストプレイヤー1'},
                'front_score': 0,
                'front_putt': 0,
                'front_game_pt': 0,
                'back_score': 0
            },
            {
                'member_id': 902,
                'member': {'name': 'テストプレイヤー2'},
                'front_score': 0,
                'front_putt': 0,
                'front_game_pt': 0,
                'back_score': 0
            },
            {
                'member_id': 903,
                'member': {'name': 'テストプレイヤー3'},
                'front_score': 0,
                'front_putt': 0,
                'front_game_pt': 0,
                'back_score': 0
            },
            {
                'member_id': 904,
                'member': {'name': 'テストプレイヤー4'},
                'front_score': 0,
                'front_putt': 0,
                'front_game_pt': 0,
                'back_score': 0
            }
        ]
    else:
        try:
            scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
            if not scores.data:
                st.error("スコアデータが見つかりません")
                st.info("テストラウンド設定でテストデータを作成してください")
                if st.button("🧪 テストラウンド設定に戻る", use_container_width=True):
                    st.info("テストラウンド設定: http://localhost:8503")
                return
            
            scores_data = sorted(scores.data, key=lambda x: x['member_id'])
        except Exception as e:
            st.error(f"スコアデータ取得エラー: {e}")
            if st.button("🧪 テストラウンド設定に戻る", use_container_width=True):
                st.info("テストラウンド設定: http://localhost:8503")
            return
    
    # セッション状態初期化
    for score in scores_data:
        member_id = score['member_id']
        for field, default in [('front_score', 45), ('front_putt', 16), ('front_game_pt', 0)]:
            key = f"{field}_{member_id}"
            if key not in st.session_state:
                db_value = score.get(field, default)
                st.session_state[key] = db_value if db_value is not None else default
    
    # プレイヤー別入力タブ（スマホ最適化）
    player_names = [score['member']['name'] if score['member'] else f"Player {score['member_id']}" 
                   for score in scores_data]
    
    # タブ形式でプレイヤー切り替え（スマホで見やすい）
    tabs = st.tabs([f"👤 {name}" for name in player_names])
    
    for i, (tab, score) in enumerate(zip(tabs, scores_data)):
        with tab:
            member_id = score['member_id']
            player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
            
            st.markdown(f"""
            <div class="player-card">
            <h3 style='text-align: center; color: #007bff; margin-bottom: 20px;'>
            👤 {player_name}
            </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # スコア入力
            st.markdown("### 🏌️‍♀️ スコア")
            create_golf_score_widget(
                "前半9ホール スコア",
                st.session_state.get(f"front_score_{member_id}", 45),
                f"front_score_{member_id}",
                "score"
            )
            
            st.markdown("---")
            
            # パット入力
            st.markdown("### ⛳ パット")
            create_golf_score_widget(
                "前半9ホール パット数",
                st.session_state.get(f"front_putt_{member_id}", 16),
                f"front_putt_{member_id}",
                "putt"
            )
            
            st.markdown("---")
            
            # ゲームポイント入力
            st.markdown("### 🎯 ゲームポイント")
            create_golf_score_widget(
                "ニアピン・ドラコンなど",
                st.session_state.get(f"front_game_pt_{member_id}", 0),
                f"front_game_pt_{member_id}",
                "game_pt"
            )
    
    # 入力状況サマリー
    st.markdown("---")
    st.markdown("### 📊 入力状況")
    
    summary_data = []
    for score in scores_data:
        member_id = score['member_id']
        player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
        summary_data.append({
            '👤 プレイヤー': player_name,
            '🏌️ スコア': st.session_state.get(f"front_score_{member_id}", 0),
            '⛳ パット': st.session_state.get(f"front_putt_{member_id}", 0),
            '🎯 GP': st.session_state.get(f"front_game_pt_{member_id}", 0)
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 保存ボタン（大きく、目立つように）
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 スコアを保存して次へ", use_container_width=True, type="primary"):
            # テストモードの場合は保存をスキップ
            if st.session_state.get('test_mode', False):
                st.write("✅ テストモード: データ保存をスキップしました")
                st.write("🎉 フロントスコア入力のテスト完了！")
                
                # テストモードでの成功メッセージ
                st.markdown("""
                <div style='background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 20px 0;'>
                <h4 style='margin: 0; color: #155724;'>🎉 テストモード完了！</h4>
                <p style='margin: 10px 0 0 0; color: #155724;'>改善版UIの機能をご確認いただけました</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("### 📱 改善版UIの特徴")
                st.write("✅ タブベースのプレイヤー切り替え")
                st.write("✅ クイック選択ボタン（35, 40, 45, 50, 55, 60）")
                st.write("✅ ±1, ±5の微調整ボタン")
                st.write("✅ 色分け表示（スコアの良し悪し）")
                st.write("✅ 大きなボタンサイズ（モバイル最適化）")
                
                return
            
            # 通常モードの保存処理
            success = True
            for score in scores_data:
                member_id = score['member_id']
                front_score = st.session_state.get(f"front_score_{member_id}", 0)
                front_putt = st.session_state.get(f"front_putt_{member_id}", 0)
                front_game_pt = st.session_state.get(f"front_game_pt_{member_id}", 0)
                
                back_score = score.get('back_score', 0) or 0
                
                update_data = {
                    'front_score': front_score,
                    'front_putt': front_putt,
                    'front_game_pt': front_game_pt,
                    'total_score': front_score + back_score
                }
                
                try:
                    supabase.table('score').update(update_data).eq('round_id', round_id).eq('member_id', member_id).execute()
                except Exception as e:
                    st.error(f"保存エラー: {e}")
                    success = False
                    break
            
            if success:
                # 計算処理
                try:
                    scores = get_scores_with_fallback(round_id)
                    if scores:
                        # ハンディキャップ情報取得
                        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                        handicaps_data = handicaps_result.data
                        
                        # round_results取得
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
                        save_round_results(round_id, updated_player_data)
                        
                except Exception as e:
                    st.warning(f"計算処理エラー: {e}")
                
                st.success("✅ フロントスコアを保存しました！")
                st.balloons()
                
                # 次のページへの案内
                st.markdown("""
                <div style='background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 20px 0;'>
                <h4 style='margin: 0; color: #155724;'>🎉 フロントスコア入力完了！</h4>
                <p style='margin: 10px 0 0 0; color: #155724;'>次は「03_バックスコア入力」に進んでください。</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("➡️ バックスコア入力へ", use_container_width=True):
                    st.switch_page("pages/03_バックスコア入力.py")

if __name__ == "__main__":
    run()
