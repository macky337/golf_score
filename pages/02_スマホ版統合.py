import sys
import os

# モジュールのインポートパスを追加（__file__の代替手法を使用）
try:
    # Streamlit環境での実行時
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # テスト環境などで__file__が未定義の場合
    current_dir = os.getcwd()
    
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
from datetime import datetime
import json

# 既存ロジックのインポート
from modules.calculation_logic import calculate_player_points

def main():
    st.set_page_config(
        page_title="スマホ版ゴルフスコア",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # スマホ最適化CSS
    st.markdown("""
    <style>
    /* モバイルファースト設計 */
    .main > div { padding-top: 0.5rem; }
    
    .stButton > button {
        width: 100%;
        height: 3.5rem;
        font-size: 20px;
        font-weight: bold;
        border-radius: 12px;
        margin: 3px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* 強制的な3列レイアウト */
    .stColumns {
        display: flex !important;
        flex-direction: row !important;
        gap: 10px !important;
    }
    
    .stColumn {
        flex: 1 !important;
        min-width: 0 !important;
    }
    
    .score-big {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        border: 3px solid white;
    }
    
    .player-header {
        background: linear-gradient(45deg, #007bff, #0056b3);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 3px 6px rgba(0,123,255,0.3);
    }
    
    .summary-card {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* タブスタイル最適化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 8px 16px;
        font-size: 16px;
        font-weight: bold;
    }
    
    /* レスポンシブ対応 */
    @media (max-width: 768px) {
        .score-big { font-size: 32px; padding: 20px; }
        .stButton > button { height: 3rem; font-size: 18px; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("# 📱 スマホ版ゴルフスコア")
    
    # 初期化
    initialize_mobile_data()
    
    # ラウンド情報表示
    show_round_header()
    
    # メインタブ（エキストラホール対応）
    round_info = st.session_state['round_info']
    has_extra = round_info.get('has_extra', False)
    
    if has_extra:
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["⛳ スコア入力", "🎯 ハンディキャップ設定", "🎉 エキストラホール", "📊 リアルタイム結果", "📄 PDF出力"])
        
        with tab1:
            show_score_input()
        
        with tab2:
            show_handicap_settings()
        
        with tab3:
            show_extra_hole_input()
        
        with tab4:
            show_realtime_results()
        
        with tab5:
            show_pdf_export()
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["⛳ スコア入力", "🎯 ハンディキャップ設定", "📊 リアルタイム結果", "📄 PDF出力"])
        
        with tab1:
            show_score_input()
        
        with tab2:
            show_handicap_settings()
        
        with tab3:
            show_realtime_results()
        
        with tab4:
            show_pdf_export()

def initialize_mobile_data():
    """モバイル用データ初期化"""
    if 'mobile_initialized' not in st.session_state:
        # ラウンド情報
        st.session_state['round_info'] = {
            'round_id': 901,  # 数値型で設定
            'date': datetime.now().strftime('%Y-%m-%d'),
            'course': 'モバイルテストコース',
            'finalized': False,
            'has_extra': False
        }
        
        # プレイヤー情報（ハンディキャップ付き）
        st.session_state['players'] = [
            {'id': 1, 'name': 'プレイヤー1', 'handicap': 8},
            {'id': 2, 'name': 'プレイヤー2', 'handicap': 12},
            {'id': 3, 'name': 'プレイヤー3', 'handicap': 18},
            {'id': 4, 'name': 'プレイヤー4', 'handicap': 24}
        ]
        
        # スコア初期化（エキストラホール対応）
        for player in st.session_state['players']:
            for score_type in ['front_score', 'front_putt', 'front_game_pt', 'back_score', 'back_putt', 'back_game_pt', 'extra_score', 'extra_putt', 'extra_game_pt']:
                key = f"{score_type}_{player['id']}"
                if key not in st.session_state:
                    defaults = {
                        'front_score': 45, 'front_putt': 16, 'front_game_pt': 0,
                        'back_score': 45, 'back_putt': 16, 'back_game_pt': 0,
                        'extra_score': 45, 'extra_putt': 16, 'extra_game_pt': 0
                    }
                    st.session_state[key] = defaults[score_type]
        
        st.session_state['mobile_initialized'] = True

def show_round_header():
    """ラウンド情報ヘッダー"""
    round_info = st.session_state['round_info']
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 15px; margin: 10px 0;'>
    <h3 style='margin: 0; text-align: center;'>📅 {round_info['date']}</h3>
    <h4 style='margin: 5px 0 0 0; text-align: center;'>🏌️ {round_info['course']}</h4>
    <p style='margin: 10px 0 0 0; text-align: center; opacity: 0.9;'>📱 スマホ最適化版</p>
    </div>
    """, unsafe_allow_html=True)

def show_handicap_settings():
    """ハンディキャップ設定画面"""
    st.markdown("## 🎯 ハンディキャップ設定")
    st.markdown("**このアプリ独自のシステム**: プレイヤー間の個別ハンディキャップを設定")
    
    # 注意事項
    st.info("💡 基本ハンディキャップは参考値です。実際の対戦では下記の個別設定が使用されます。")
    
    players = st.session_state['players']
    
    # ハンディキャップデータの初期化
    if 'handicap_matches' not in st.session_state:
        st.session_state['handicap_matches'] = []
    
    # プレイヤー組み合わせ生成
    player_combinations = []
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            player_combinations.append((players[i], players[j]))
    
    # ハンディキャップ設定状況の表示
    st.markdown("### 📋 現在の設定状況")
    handicap_matches = st.session_state.get('handicap_matches', [])
    
    if handicap_matches:
        st.success(f"✅ {len(handicap_matches)}組の対戦ハンディキャップが設定済み")
        show_handicap_summary()
    else:
        st.warning("⚠️ ハンディキャップが未設定です。下記で設定してください。")
    
    st.markdown("### 👥 対戦組み合わせ")
    
    for i, (player1, player2) in enumerate(player_combinations):
        with st.expander(f"🏌️ {player1['name']} vs {player2['name']}", expanded=i<2):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### {player1['name']} → {player2['name']}")
                handicap_1_to_2 = st.number_input(
                    f"{player1['name']}から{player2['name']}へのハンデ",
                    min_value=0,
                    max_value=30,
                    value=get_saved_handicap(player1['id'], player2['id'], '1_to_2'),
                    key=f"handicap_{player1['id']}_to_{player2['id']}"
                )
                
            with col2:
                st.markdown(f"#### {player2['name']} → {player1['name']}")
                handicap_2_to_1 = st.number_input(
                    f"{player2['name']}から{player1['name']}へのハンデ",
                    min_value=0,
                    max_value=30,
                    value=get_saved_handicap(player1['id'], player2['id'], '2_to_1'),
                    key=f"handicap_{player2['id']}_to_{player1['id']}"
                )
            
            # 対戦方式設定
            total_only = st.checkbox(
                f"🎯 トータルスコアのみで勝負（フロント・バック個別勝負なし）",
                value=get_saved_total_only(player1['id'], player2['id']),
                key=f"total_only_{player1['id']}_{player2['id']}"
            )
            
            # 設定保存
            if st.button(f"💾 設定保存", key=f"save_{player1['id']}_{player2['id']}", use_container_width=True):
                save_handicap_setting(player1['id'], player2['id'], handicap_1_to_2, handicap_2_to_1, total_only)
                st.success(f"✅ {player1['name']} vs {player2['name']} の設定を保存しました")
    
    # 一括設定
    st.markdown("---")
    st.markdown("### ⚡ 一括設定")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 すべてリセット", use_container_width=True):
            st.session_state['handicap_matches'] = []
            st.success("✅ すべてのハンディキャップ設定をリセットしました")
            st.rerun()
    
    with col2:
        if st.button("📊 設定確認", use_container_width=True):
            show_handicap_summary()
    
    with col3:
        auto_handicap = st.selectbox("自動設定", ["選択してください", "基本ハンデから推定", "均等配分"])
        if auto_handicap != "選択してください":
            apply_auto_handicap(auto_handicap)

def get_saved_handicap(player1_id, player2_id, direction):
    """保存されたハンディキャップ値を取得"""
    handicap_matches = st.session_state.get('handicap_matches', [])
    for match in handicap_matches:
        if ((match['player1_id'] == player1_id and match['player2_id'] == player2_id) or
            (match['player1_id'] == player2_id and match['player2_id'] == player1_id)):
            if direction == '1_to_2':
                return match.get('player_1_to_2', 0) if match['player1_id'] == player1_id else match.get('player_2_to_1', 0)
            else:
                return match.get('player_2_to_1', 0) if match['player1_id'] == player1_id else match.get('player_1_to_2', 0)
    return 0

def get_saved_total_only(player1_id, player2_id):
    """保存されたトータルオンリー設定を取得"""
    handicap_matches = st.session_state.get('handicap_matches', [])
    for match in handicap_matches:
        if ((match['player1_id'] == player1_id and match['player2_id'] == player2_id) or
            (match['player1_id'] == player2_id and match['player2_id'] == player1_id)):
            return match.get('total_only', False)
    return False

def save_handicap_setting(player1_id, player2_id, handicap_1_to_2, handicap_2_to_1, total_only):
    """ハンディキャップ設定を保存"""
    handicap_matches = st.session_state.get('handicap_matches', [])
    
    # 既存設定を更新または新規追加
    found = False
    for i, match in enumerate(handicap_matches):
        if ((match['player1_id'] == player1_id and match['player2_id'] == player2_id) or
            (match['player1_id'] == player2_id and match['player2_id'] == player1_id)):
            handicap_matches[i] = {
                'player1_id': player1_id,
                'player2_id': player2_id,
                'player_1_to_2': handicap_1_to_2,
                'player_2_to_1': handicap_2_to_1,
                'total_only': total_only
            }
            found = True
            break
    
    if not found:
        handicap_matches.append({
            'player1_id': player1_id,
            'player2_id': player2_id,
            'player_1_to_2': handicap_1_to_2,
            'player_2_to_1': handicap_2_to_1,
            'total_only': total_only
        })
    
    st.session_state['handicap_matches'] = handicap_matches

def show_handicap_summary():
    """ハンディキャップ設定サマリー表示"""
    handicap_matches = st.session_state.get('handicap_matches', [])
    players = st.session_state['players']
    
    if not handicap_matches:
        st.info("ハンディキャップ設定がありません")
        return
    
    st.markdown("#### 📋 設定サマリー")
    
    summary_data = []
    for match in handicap_matches:
        player1_name = next(p['name'] for p in players if p['id'] == match['player1_id'])
        player2_name = next(p['name'] for p in players if p['id'] == match['player2_id'])
        
        summary_data.append({
            '対戦': f"{player1_name} vs {player2_name}",
            f'{player1_name}→{player2_name}': match['player_1_to_2'],
            f'{player2_name}→{player1_name}': match['player_2_to_1'],
            'トータルのみ': "✅" if match['total_only'] else "❌"
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def apply_auto_handicap(auto_type):
    """自動ハンディキャップ設定"""
    players = st.session_state['players']
    
    if auto_type == "基本ハンデから推定":
        # 基本ハンディキャップの差分から推定
        for i, player1 in enumerate(players):
            for j, player2 in enumerate(players):
                if i < j:
                    handicap_diff = abs(player1['handicap'] - player2['handicap'])
                    if player1['handicap'] > player2['handicap']:
                        save_handicap_setting(player1['id'], player2['id'], handicap_diff//2, 0, False)
                    else:
                        save_handicap_setting(player1['id'], player2['id'], 0, handicap_diff//2, False)
        
        st.success("✅ 基本ハンディキャップから自動設定しました")
        st.rerun()

def show_score_input():
    """スコア入力画面"""
    players = st.session_state['players']
    round_info = st.session_state['round_info']
    
    # エキストラホール設定
    st.markdown("### 🎉 エキストラホール設定")
    
    if not round_info.get('has_extra', False):
        # エキストラホール有効化ボタン
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("📢 フロント・バック終了後、エキストラホールを追加できます")
        with col2:
            if st.button("🎉 エキストラ\n有効化", use_container_width=True, type="primary"):
                st.session_state['round_info']['has_extra'] = True
                st.success("✅ エキストラホールを有効化しました！")
                st.rerun()
    else:
        st.success("🎉 エキストラホールが有効化されています（エキストラホールタブで入力してください）")
    
    st.markdown("---")
    
    # プレイヤータブ
    player_tabs = st.tabs([f"🏌️ {p['name']}" for p in players])
    
    for i, (tab, player) in enumerate(zip(player_tabs, players)):
        with tab:
            render_player_input_mobile(player)

def render_player_input_mobile(player):
    """モバイル最適化プレイヤー入力"""
    player_id = player['id']
    
    # プレイヤーヘッダー（基本HC非表示版）
    st.markdown(f"""
    <div class="player-header">
    <h3 style='margin: 0;'>👤 {player['name']}</h3>
    <p style='margin: 5px 0 0 0; opacity: 0.7; font-size: 14px;'>対戦ハンディキャップは「ハンディキャップ設定」タブで設定</p>
    </div>
    """, unsafe_allow_html=True)
    
    # レスポンシブレイアウト
    # セッション状態で表示モードを管理
    if 'display_mode' not in st.session_state:
        st.session_state['display_mode'] = 'mobile'  # デフォルトをmobileに変更
    
    # 表示モード切り替え
    display_mode = st.radio(
        "🖱️ 表示モード",
        options=['mobile', 'pc'],
        index=['mobile', 'pc'].index(st.session_state['display_mode']),
        format_func=lambda x: {
            'pc': '🖥️ PC表示（横並び）',
            'mobile': '📱 スマホ表示（縦並び）'
        }[x],
        horizontal=True,
        key=f"display_mode_{player_id}"
    )
    st.session_state['display_mode'] = display_mode
    
    # レイアウト判定：明確にPC表示を選択した場合のみ横並び
    use_horizontal = (display_mode == 'pc')
    
    if use_horizontal:
        # PC: フロント/バック横並び
        front_col, back_col = st.columns(2)
        
        with front_col:
            st.markdown("### 🌅 フロント9")
            render_nine_holes_input(player_id, "front")
        
        with back_col:
            st.markdown("### 🌇 バック9")
            render_nine_holes_input(player_id, "back")
    else:
        # スマホ/デフォルト: フロント/バック縦並び
        st.markdown("### 🌅 フロント9")
        render_nine_holes_input(player_id, "front")
        
        st.markdown("### 🌇 バック9")
        render_nine_holes_input(player_id, "back")
    
    # プレイヤー統計
    show_player_summary_mobile(player)

def render_nine_holes_input(player_id, half):
    """9ホール入力（フロント/バック）"""
    
    # スコア入力
    st.markdown("#### 🏌️ スコア")
    score_key = f"{half}_score_{player_id}"
    quick_scores = [60, 55, 50, 45, 40, 35]  # 降順に変更
    create_mobile_score_widget(score_key, quick_scores, "score")
    
    # パット入力
    st.markdown("#### ⛳ パット")
    putt_key = f"{half}_putt_{player_id}"
    quick_putts = [22, 20, 18, 16, 14, 12]  # 降順に変更
    create_mobile_score_widget(putt_key, quick_putts, "putt")
    
    # ゲームポイント
    st.markdown("#### 🎯 ゲームPT")
    game_key = f"{half}_game_pt_{player_id}"
    quick_games = [30, 20, 10, 0, -10, -20]  # 降順に変更
    create_mobile_score_widget(game_key, quick_games, "game")

def show_extra_hole_input():
    """エキストラホール入力画面"""
    st.markdown("## 🎉 エキストラホール入力")
    
    # エキストラホール有効化の説明
    st.info("🎯 プレーオフ・エキストラホールのスコアを入力してください")
    
    # プレイヤータブ
    players = st.session_state['players']
    player_tabs = st.tabs([f"🏌️ {p['name']}" for p in players])
    
    for i, (tab, player) in enumerate(zip(player_tabs, players)):
        with tab:
            render_extra_hole_input(player)
    
    # エキストラホール結果計算
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 エキストラ結果を計算", use_container_width=True, type="primary"):
            calculate_results_mobile()
            st.success("✅ エキストラホール含む結果を計算しました")
    
    with col2:
        if st.button("❌ エキストラホールを削除", use_container_width=True):
            # エキストラホールフラグをオフに
            st.session_state['round_info']['has_extra'] = False
            # エキストラスコアをリセット
            for player in players:
                player_id = player['id']
                st.session_state[f"extra_score_{player_id}"] = 45
                st.session_state[f"extra_putt_{player_id}"] = 16
                st.session_state[f"extra_game_pt_{player_id}"] = 0
            st.success("✅ エキストラホールを削除しました")
            st.rerun()

def render_extra_hole_input(player):
    """エキストラホール入力（1プレイヤー分）"""
    player_id = player['id']
    
    # プレイヤーヘッダー
    st.markdown(f"""
    <div class="player-header">
    <h3 style='margin: 0;'>🎉 {player['name']} - エキストラホール</h3>
    <p style='margin: 5px 0 0 0; opacity: 0.7; font-size: 14px;'>追加9ホールのスコア入力</p>
    </div>
    """, unsafe_allow_html=True)
    
    # エキストラスコア入力
    st.markdown("### 🏌️ エキストラスコア")
    score_key = f"extra_score_{player_id}"
    quick_scores = [60, 55, 50, 45, 40, 35]  # 降順
    create_mobile_score_widget(score_key, quick_scores, "score")
    
    # エキストラパット入力
    st.markdown("### ⛳ エキストラパット")
    putt_key = f"extra_putt_{player_id}"
    quick_putts = [22, 20, 18, 16, 14, 12]  # 降順
    create_mobile_score_widget(putt_key, quick_putts, "putt")
    
    # エキストラゲームポイント
    st.markdown("### 🎯 エキストラゲームPT")
    game_key = f"extra_game_pt_{player_id}"
    quick_games = [30, 20, 10, 0, -10, -20]  # 降順
    create_mobile_score_widget(game_key, quick_games, "game")
    
    # エキストラホール統計
    show_extra_hole_summary(player)

def show_extra_hole_summary(player):
    """エキストラホール統計表示"""
    player_id = player['id']
    
    # データ取得
    extra_score = st.session_state.get(f"extra_score_{player_id}", 0)
    extra_putt = st.session_state.get(f"extra_putt_{player_id}", 0)
    extra_game = st.session_state.get(f"extra_game_pt_{player_id}", 0)
    
    # 統計カード
    st.markdown(f"""
    <div class="summary-card">
    <h4 style='margin: 0 0 10px 0; color: #ff6b35;'>🎉 エキストラ統計</h4>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
        <div><strong>エキストラスコア:</strong> {extra_score}</div>
        <div><strong>PAR差:</strong> {extra_score - 36:+d}</div>
        <div><strong>エキストラパット:</strong> {extra_putt}</div>
        <div><strong>平均/H:</strong> {extra_putt/9:.1f}</div>
        <div><strong>エキストラPT:</strong> {extra_game:+d}</div>
        <div><strong>ハンデ後:</strong> {extra_score - (player['handicap']//2)}</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

def create_mobile_score_widget(key, quick_values, score_type):
    """モバイル最適化スコアウィジェット"""
    current_value = st.session_state.get(key, quick_values[3])  # 中央値をデフォルトに
    
    # 3列2行のStreamlitボタンレイアウト
    # 1行目: 降順配置
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(f"{quick_values[0]}", key=f"{key}_btn_{quick_values[0]}", use_container_width=True):
            st.session_state[key] = quick_values[0]
            st.rerun()
    with col2:
        if st.button(f"{quick_values[1]}", key=f"{key}_btn_{quick_values[1]}", use_container_width=True):
            st.session_state[key] = quick_values[1]
            st.rerun()
    with col3:
        if st.button(f"{quick_values[2]}", key=f"{key}_btn_{quick_values[2]}", use_container_width=True):
            st.session_state[key] = quick_values[2]
            st.rerun()
    
    # 2行目: 降順配置
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button(f"{quick_values[3]}", key=f"{key}_btn_{quick_values[3]}", use_container_width=True):
            st.session_state[key] = quick_values[3]
            st.rerun()
    with col5:
        if st.button(f"{quick_values[4]}", key=f"{key}_btn_{quick_values[4]}", use_container_width=True):
            st.session_state[key] = quick_values[4]
            st.rerun()
    with col6:
        if st.button(f"{quick_values[5]}", key=f"{key}_btn_{quick_values[5]}", use_container_width=True):
            st.session_state[key] = quick_values[5]
            st.rerun()
    
    # 大きな数値表示
    color = get_mobile_score_color(current_value, score_type)
    st.markdown(f"""
    <div class="score-big" style="background-color: {color}; color: white;">
    {current_value}
    </div>
    """, unsafe_allow_html=True)
    
    # 微調整ボタン（2x2レイアウト）
    adj_col1, adj_col2 = st.columns(2)
    with adj_col1:
        if st.button("-1", key=f"{key}_m1", use_container_width=True):
            st.session_state[key] = max(0, current_value - 1)
            st.rerun()
    with adj_col2:
        if st.button("+1", key=f"{key}_p1", use_container_width=True):
            st.session_state[key] = min(100, current_value + 1)
            st.rerun()

def get_mobile_score_color(value, score_type):
    """スコアタイプ別色分け"""
    if score_type == "score":
        if value <= 40: return "#28a745"
        elif value <= 50: return "#ffc107" 
        else: return "#dc3545"
    elif score_type == "putt":
        if value <= 14: return "#28a745"
        elif value <= 18: return "#ffc107"
        else: return "#dc3545"
    else:  # game points
        if value > 10: return "#28a745"
        elif value >= -5: return "#ffc107"
        else: return "#dc3545"

def show_player_summary_mobile(player):
    """プレイヤー統計（モバイル版・エキストラホール対応）"""
    player_id = player['id']
    round_info = st.session_state['round_info']
    
    # データ取得
    front_score = st.session_state.get(f"front_score_{player_id}", 0)
    back_score = st.session_state.get(f"back_score_{player_id}", 0)
    front_putt = st.session_state.get(f"front_putt_{player_id}", 0)
    back_putt = st.session_state.get(f"back_putt_{player_id}", 0)
    front_game = st.session_state.get(f"front_game_pt_{player_id}", 0)
    back_game = st.session_state.get(f"back_game_pt_{player_id}", 0)
    
    # エキストラホールデータ（有効な場合のみ）
    has_extra = round_info.get('has_extra', False)
    if has_extra:
        extra_score = st.session_state.get(f"extra_score_{player_id}", 0)
        extra_putt = st.session_state.get(f"extra_putt_{player_id}", 0)
        extra_game = st.session_state.get(f"extra_game_pt_{player_id}", 0)
    else:
        extra_score = extra_putt = extra_game = 0
    
    # 合計計算
    total_score = front_score + back_score + extra_score
    total_putt = front_putt + back_putt + extra_putt
    total_game = front_game + back_game + extra_game
    
    # ホール数（エキストラ考慮）
    total_holes = 27 if has_extra else 18
    par_total = 108 if has_extra else 72
    
    # 統計カード
    st.markdown(f"""
    <div class="summary-card">
    <h4 style='margin: 0 0 10px 0; color: #007bff;'>📊 統計サマリー {'(27H)' if has_extra else '(18H)'}</h4>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
        <div><strong>総スコア:</strong> {total_score}</div>
        <div><strong>PAR差:</strong> {total_score - par_total:+d}</div>
        <div><strong>総パット:</strong> {total_putt}</div>
        <div><strong>平均/H:</strong> {total_putt/total_holes:.1f}</div>
        <div><strong>ゲームPT:</strong> {total_game:+d}</div>
        <div><strong>ハンデ後:</strong> {total_score - player['handicap']}</div>
    </div>
    </div>
    """, unsafe_allow_html=True)

def show_realtime_results():
    """リアルタイム結果表示"""
    st.markdown("## 🏆 リアルタイム順位")
    
    # 即座に計算実行
    if st.button("🔄 最新結果を計算", use_container_width=True, type="primary"):
        calculate_results_mobile()
    
    # 結果表示
    if 'calculated_results' in st.session_state:
        show_calculated_results()
    else:
        st.info("「最新結果を計算」ボタンを押してください")

def calculate_results_mobile():
    """モバイル版結果計算（既存ロジック使用）"""
    try:
        players = st.session_state['players']
        # ラウンド情報（数値型に変換）
        round_info = st.session_state['round_info'].copy()
        # round_idを数値に変換
        if isinstance(round_info.get('round_id'), str):
            try:
                # 文字列から数値部分を抽出
                round_id_str = round_info['round_id']
                if 'MOBILE_' in round_id_str:
                    round_info['round_id'] = 901  # モバイルテスト用のID
                else:
                    round_info['round_id'] = int(round_id_str)
            except:
                round_info['round_id'] = 901  # デフォルト値
        
        # プレイヤーデータ準備（エキストラホール対応・型変換を確実に）
        scores_data = []
        has_extra = round_info.get('has_extra', False)
        
        for player in players:
            player_id = player['id']
            
            # 数値型に確実に変換
            front_score = int(st.session_state.get(f"front_score_{player_id}", 0))
            front_putt = int(st.session_state.get(f"front_putt_{player_id}", 0))
            front_game_pt = int(st.session_state.get(f"front_game_pt_{player_id}", 0))
            back_score = int(st.session_state.get(f"back_score_{player_id}", 0))
            back_putt = int(st.session_state.get(f"back_putt_{player_id}", 0))
            back_game_pt = int(st.session_state.get(f"back_game_pt_{player_id}", 0))
            
            # エキストラホールデータ（有効な場合のみ）
            if has_extra:
                extra_score = int(st.session_state.get(f"extra_score_{player_id}", 0))
                extra_putt = int(st.session_state.get(f"extra_putt_{player_id}", 0))
                extra_game_pt = int(st.session_state.get(f"extra_game_pt_{player_id}", 0))
                total_score = front_score + back_score + extra_score
            else:
                extra_score = extra_putt = extra_game_pt = 0
                total_score = front_score + back_score
            
            score_data = {
                'member_id': player_id,
                'member': {'name': player['name']},
                'front_score': front_score,
                'front_putt': front_putt,
                'front_game_pt': front_game_pt,
                'back_score': back_score,
                'back_putt': back_putt,
                'back_game_pt': back_game_pt,
                'extra_score': extra_score,
                'extra_putt': extra_putt,
                'extra_game_pt': extra_game_pt,
                'total_score': total_score,
                'handicap': int(player['handicap'])
            }
            scores_data.append(score_data)
        
        # 既存ロジック用のデータ形式に変換（エキストラホール対応）
        player_data = {}
        for score in scores_data:
            player_id = score['member_id']
            player_data[player_id] = {
                'name': score['member']['name'],
                'Front Score': score['front_score'],
                'Front Putt': score['front_putt'],
                'Front GP': score['front_game_pt'],
                'Back Score': score['back_score'],
                'Back Putt': score['back_putt'],
                'Back GP': score['back_game_pt'],
                'Extra Score': score['extra_score'],
                'Extra Putt': score['extra_putt'],
                'Extra GP': score['extra_game_pt'],
                'Total Score': score['total_score'],
                'handicap': score['handicap']
            }
        
        player_ids = sorted(list(player_data.keys()))
        
        # ハンディキャップ辞書（既存ロジックに合わせた形式）
        handicaps = {}
        total_only_set = set()
        
        # セッション状態からハンディキャップデータを取得
        handicap_matches = st.session_state.get('handicap_matches', [])
        for match in handicap_matches:
            player1_id = match['player1_id']
            player2_id = match['player2_id']
            
            # ハンディキャップ辞書に追加
            handicaps[(player1_id, player2_id)] = match['player_1_to_2']
            handicaps[(player2_id, player1_id)] = match['player_2_to_1']
            
            # トータルオンリー設定
            if match.get('total_only', False):
                total_only_set.add(frozenset([player1_id, player2_id]))
        
        # 既存の計算ロジックを呼び出し
        calculated_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, round_info)
        
        st.session_state['calculated_results'] = calculated_data
        st.success("✅ 計算完了！")
        
        # デバッグ情報表示
        with st.expander("🔍 計算詳細"):
            st.json({
                'player_count': len(player_ids),
                'sample_data': list(calculated_data.values())[0] if calculated_data else {},
                'handicaps_used': len(handicaps),
                'total_only_matches': len(total_only_set)
            })
        
    except Exception as e:
        st.error(f"計算エラー: {e}")
        st.error(f"エラー詳細: {type(e).__name__}")
        
        # デバッグ情報
        with st.expander("🐛 エラー詳細"):
            import traceback
            st.code(traceback.format_exc())

def show_calculated_results():
    """計算結果表示（エキストラホール対応）"""
    results = st.session_state['calculated_results']
    handicap_matches = st.session_state.get('handicap_matches', [])
    round_info = st.session_state['round_info']
    has_extra = round_info.get('has_extra', False)
    
    # ハンディキャップ使用状況
    if handicap_matches:
        st.success(f"✅ {len(handicap_matches)}組のハンディキャップ設定を適用済み")
    else:
        st.info("ℹ️ ハンディキャップ設定なしで計算")
    
    # エキストラホール状況表示
    if has_extra:
        st.info("🎉 エキストラホール含む27ホール結果")
    else:
        st.info("⛳ 通常の18ホール結果")
    
    # 順位表作成（エキストラホール対応）
    ranking_data = []
    for player_id, data in results.items():
        # エキストラホールスコア取得
        extra_score = data.get('Extra Score', 0) if has_extra else 0
        total_score_display = data.get('total_score', 0)
        
        ranking_data.append({
            'プレイヤー': data.get('name', f'Player {player_id}'),
            'フロント': data.get('Front Score', 0),
            'バック': data.get('Back Score', 0),
            'エキストラ': extra_score if has_extra else '-',
            'グロス': total_score_display,
            'ネット': data.get('net_score', 0),
            'パット': data.get('total_putt', 0),
            'ポイント': data.get('total_points', 0)
        })
    
    # ポイント順でソート
    ranking_data.sort(key=lambda x: x['ポイント'], reverse=True)
    
    # 順位追加
    for i, data in enumerate(ranking_data):
        data['順位'] = i + 1
    
    # 表示カラムを動的に決定
    if has_extra:
        columns = ['順位', 'プレイヤー', 'フロント', 'バック', 'エキストラ', 'グロス', 'ネット', 'パット', 'ポイント']
    else:
        columns = ['順位', 'プレイヤー', 'フロント', 'バック', 'グロス', 'ネット', 'パット', 'ポイント']
        # エキストラ列を削除
        for data in ranking_data:
            del data['エキストラ']
    
    # 表示
    df = pd.DataFrame(ranking_data)
    df = df[columns]
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_pdf_export():
    """PDF出力機能（エキストラホール対応）"""
    st.markdown("## 📄 PDF出力")
    round_info = st.session_state['round_info']
    has_extra = round_info.get('has_extra', False)
    
    # エキストラホール状況表示
    if has_extra:
        st.info("🎉 エキストラホール含む27ホール結果をPDF出力")
    else:
        st.info("⛳ 通常の18ホール結果をPDF出力")
    
    if 'calculated_results' not in st.session_state:
        st.warning("まず「リアルタイム結果」で計算を実行してください")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 データ準備")
        if st.button("📋 結果データ確認", use_container_width=True):
            show_export_preview()
    
    with col2:
        st.markdown("### 📥 出力オプション")
        if st.button("📄 PDF生成", use_container_width=True, type="primary"):
            generate_pdf_mobile()

def show_export_preview():
    """エクスポートプレビュー（エキストラホール対応）"""
    results = st.session_state['calculated_results']
    round_info = st.session_state['round_info']
    has_extra = round_info.get('has_extra', False)
    
    st.json({
        'round_info': round_info,
        'has_extra': has_extra,
        'holes': '27ホール' if has_extra else '18ホール',
        'results_count': len(results),
        'sample_player': list(results.values())[0] if results else {}
    })

def generate_pdf_mobile():
    """モバイル版PDF生成（エキストラホール対応）"""
    try:
        round_info = st.session_state['round_info']
        has_extra = round_info.get('has_extra', False)
        
        # エキストラホール対応のPDF生成ロジック
        st.success("✅ PDF生成機能準備完了")
        
        if has_extra:
            st.info("📋 エキストラホール含む27ホール結果をPDF化")
        else:
            st.info("📋 通常の18ホール結果をPDF化")
        
        # ダウンロードボタン（将来的に実装）
        filename_suffix = "_27H" if has_extra else "_18H"
        st.download_button(
            label=f"📥 PDFダウンロード {filename_suffix}",
            data="PDF content placeholder",
            file_name=f"golf_results{filename_suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"PDF生成エラー: {e}")

if __name__ == "__main__":
    main()
