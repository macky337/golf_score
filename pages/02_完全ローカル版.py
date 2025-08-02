import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 完全ローカル処理のゴルフスコア入力アプリ
def main():
    st.set_page_config(
        page_title="ローカル版フロントスコア入力",
        page_icon="🏌️",
        layout="wide"
    )
    
    # カスタムCSS（モバイル最適化）
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        margin: 2px 0;
    }
    .score-display {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .player-tab {
        background: linear-gradient(45deg, #007bff, #0056b3);
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("# 🏌️ ローカル版フロントスコア入力")
    st.markdown("**⚡ 完全オフライン対応 - 高速処理**")
    
    # ローカルデータ初期化
    initialize_local_data()
    
    # ラウンド情報表示
    round_info = st.session_state.get('round_info', {})
    st.markdown(f"""
    <div style='background-color: #e7f3ff; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; margin: 20px 0;'>
    <h4 style='margin: 0; color: #007bff;'>📅 {round_info.get('date', '2025-08-02')} ⚡ (ローカル高速版)</h4>
    <h5 style='margin: 5px 0 0 0; color: #495057;'>🏌️ {round_info.get('course', 'テストゴルフ場')}</h5>
    </div>
    """, unsafe_allow_html=True)
    
    # プレイヤーデータ取得
    players = st.session_state.get('players', [])
    
    # タブ形式でプレイヤー入力（改良版）
    tabs = st.tabs([f"🏌️ {player['name']}" for player in players])
    
    for i, (tab, player) in enumerate(zip(tabs, players)):
        with tab:
            render_player_input(player)
    
    # リアルタイム集計表示
    show_realtime_summary(players)
    
    # ローカル保存とエクスポート機能
    show_local_save_options()

def initialize_local_data():
    """ローカルデータの初期化"""
    if 'local_initialized' not in st.session_state:
        # ラウンド情報
        st.session_state['round_info'] = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'course': 'ローカルテストコース',
            'round_id': 'LOCAL_001'
        }
        
        # プレイヤーデータ
        st.session_state['players'] = [
            {'id': 1, 'name': 'プレイヤー1', 'handicap': 10},
            {'id': 2, 'name': 'プレイヤー2', 'handicap': 15},
            {'id': 3, 'name': 'プレイヤー3', 'handicap': 20},
            {'id': 4, 'name': 'プレイヤー4', 'handicap': 25}
        ]
        
        # スコアデータ初期化
        for player in st.session_state['players']:
            for score_type in ['front_score', 'front_putt', 'front_game_pt']:
                key = f"{score_type}_{player['id']}"
                if key not in st.session_state:
                    defaults = {'front_score': 45, 'front_putt': 16, 'front_game_pt': 0}
                    st.session_state[key] = defaults[score_type]
        
        st.session_state['local_initialized'] = True

def render_player_input(player):
    """プレイヤー入力UI"""
    player_id = player['id']
    
    # プレイヤー情報カード
    st.markdown(f"""
    <div class="player-tab">
    <h3 style='margin: 0; text-align: center;'>👤 {player['name']} (HC: {player['handicap']})</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # スコア入力セクション
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏌️‍♀️ スコア")
        create_fast_score_widget(
            f"front_score_{player_id}", 
            [35, 40, 45, 50, 55, 60],
            "score"
        )
        
        st.markdown("### ⛳ パット")
        create_fast_score_widget(
            f"front_putt_{player_id}", 
            [12, 14, 16, 18, 20, 22],
            "putt"
        )
    
    with col2:
        st.markdown("### 🎯 ゲームポイント")
        create_fast_score_widget(
            f"front_game_pt_{player_id}", 
            [-30, -10, 0, 10, 30, 50],
            "points"
        )
        
        # リアルタイム統計
        show_player_stats(player_id)

def create_fast_score_widget(key, quick_values, score_type):
    """高速スコア入力ウィジェット"""
    current_value = st.session_state.get(key, quick_values[2])
    
    # クイック選択（横一列）
    cols = st.columns(len(quick_values))
    for i, val in enumerate(quick_values):
        with cols[i]:
            if st.button(str(val), key=f"{key}_q{val}", use_container_width=True):
                st.session_state[key] = val
                st.rerun()
    
    # 現在値表示（色分け）
    color = get_score_color(current_value, score_type)
    st.markdown(f"""
    <div class="score-display" style="background-color: {color}; color: white;">
    {current_value}
    </div>
    """, unsafe_allow_html=True)
    
    # 微調整ボタン（コンパクト）
    adj_cols = st.columns(4)
    adjustments = [(-5, "-5"), (-1, "-1"), (+1, "+1"), (+5, "+5")]
    
    for i, (adj, label) in enumerate(adjustments):
        with adj_cols[i]:
            if st.button(label, key=f"{key}_adj{adj}", use_container_width=True):
                new_val = max(0, min(100, current_value + adj))
                st.session_state[key] = new_val
                st.rerun()

def get_score_color(value, score_type):
    """スコアタイプに応じた色分け"""
    if score_type == "score":
        if value <= 40: return "#28a745"    # 緑（良い）
        elif value <= 50: return "#ffc107"  # 黄（普通）
        else: return "#dc3545"              # 赤（厳しい）
    elif score_type == "putt":
        if value <= 14: return "#28a745"    # 緑（良い）
        elif value <= 18: return "#ffc107"  # 黄（普通）
        else: return "#dc3545"              # 赤（多い）
    else:  # points
        if value > 20: return "#28a745"     # 緑（プラス）
        elif value >= -10: return "#ffc107" # 黄（普通）
        else: return "#dc3545"              # 赤（マイナス）

def calculate_local_golf_points(player_id):
    """ローカルでゴルフポイント計算"""
    players = st.session_state.get('players', [])
    
    # 現在のプレイヤー情報取得
    current_player = next((p for p in players if p['id'] == player_id), None)
    if not current_player:
        return 0
    
    score = st.session_state.get(f"front_score_{player_id}", 0)
    putt = st.session_state.get(f"front_putt_{player_id}", 0)
    game_pt = st.session_state.get(f"front_game_pt_{player_id}", 0)
    handicap = current_player.get('handicap', 0)
    
    # 基本ポイント計算（簡易版）
    total_points = 0
    
    # 1. スコアポイント（PAR36基準）
    par_diff = score - 36
    handicap_adjusted = par_diff - (handicap / 2)  # 前半ハンデは半分
    
    if handicap_adjusted <= -2:
        total_points += 3  # イーグル以上
    elif handicap_adjusted == -1:
        total_points += 2  # バーディ
    elif handicap_adjusted == 0:
        total_points += 1  # パー
    elif handicap_adjusted == 1:
        total_points += 0  # ボギー
    else:
        total_points -= 1  # ダブルボギー以上
    
    # 2. パットポイント
    avg_putt = putt / 9
    if avg_putt <= 1.5:
        total_points += 2  # 優秀
    elif avg_putt <= 1.8:
        total_points += 1  # 良い
    elif avg_putt >= 2.2:
        total_points -= 1  # 多め
    
    # 3. ゲームポイント加算
    total_points += game_pt
    
    return total_points

def show_player_stats(player_id):
    """プレイヤー統計表示"""
    score = st.session_state.get(f"front_score_{player_id}", 0)
    putt = st.session_state.get(f"front_putt_{player_id}", 0)
    points = st.session_state.get(f"front_game_pt_{player_id}", 0)
    
    st.markdown("#### 📊 統計")
    
    # パーとの差（PAR36想定）
    par_diff = score - 36
    par_display = f"+{par_diff}" if par_diff > 0 else str(par_diff)
    
    # ローカルでゴルフポイント計算
    local_points = calculate_local_golf_points(player_id)
    
    st.metric("PAR差", par_display, delta=None)
    st.metric("平均パット/ホール", f"{putt/9:.1f}", delta=None)
    st.metric("ゲームPT", f"{points:+d}", delta=None)
    st.metric("計算済みPT", f"{local_points:+d}", delta=None)

def show_realtime_summary(players):
    """リアルタイム集計表示"""
    st.markdown("---")
    st.markdown("## 📊 リアルタイム集計")
    
    # 集計データ作成
    summary_data = []
    for player in players:
        player_id = player['id']
        score = st.session_state.get(f"front_score_{player_id}", 0)
        putt = st.session_state.get(f"front_putt_{player_id}", 0)
        points = st.session_state.get(f"front_game_pt_{player_id}", 0)
        par_diff = score - 36
        
        summary_data.append({
            '🏌️ プレイヤー': player['name'],
            '📊 スコア': score,
            '⛳ パット': putt,
            '🎯 GP': points,
            '📈 PAR差': f"{par_diff:+d}",
            '💯 平均パット': f"{putt/9:.1f}"
        })
    
    # 順位付け（スコア順）
    summary_data.sort(key=lambda x: x['📊 スコア'])
    for i, data in enumerate(summary_data):
        data['🏆 順位'] = i + 1
    
    # 並び替えて表示
    df = pd.DataFrame(summary_data)
    columns_order = ['🏆 順位', '🏌️ プレイヤー', '📊 スコア', '📈 PAR差', '⛳ パット', '💯 平均パット', '🎯 GP']
    df = df[columns_order]
    
    st.dataframe(df, use_container_width=True, hide_index=True)

def show_local_save_options():
    """ローカル保存オプション"""
    st.markdown("---")
    st.markdown("## 💾 保存オプション")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ ローカル保存（高速）")
        if st.button("📱 セッション保存", use_container_width=True, type="primary"):
            st.success("✅ セッションに保存済み（ブラウザを閉じるまで保持）")
        
        col1a, col1b = st.columns(2)
        with col1a:
            if st.button("📁 JSON出力", use_container_width=True):
                export_to_json()
        with col1b:
            if st.button("📊 CSV出力", use_container_width=True):
                export_to_csv()
    
    with col2:
        st.markdown("### 🌐 オンライン同期（オプション）")
        
        # DB接続状態チェック
        db_connected = check_db_connection()
        if db_connected:
            st.success("✅ データベース接続OK")
            if st.button("☁️ DBに同期保存", use_container_width=True, type="secondary"):
                sync_to_database()
        else:
            st.warning("⚠️ データベース未接続")
            if st.button("🔄 接続を試行", use_container_width=True):
                st.rerun()
        
        st.info("💡 オフラインでも完全に動作します")

def check_db_connection():
    """データベース接続チェック"""
    try:
        # ここで実際のDB接続をテスト
        # 今はFalseを返してオフライン状態をシミュレート
        return False
    except:
        return False

def sync_to_database():
    """データベースに同期保存"""
    try:
        # ここで実際のDB保存処理
        st.success("✅ データベースに同期しました")
        st.info("🔄 ローカルとクラウドの両方に保存済み")
    except Exception as e:
        st.error(f"❌ 同期エラー: {e}")
        st.info("💾 ローカルデータは安全に保存されています")

def export_to_json():
    """JSON形式でエクスポート"""
    players = st.session_state.get('players', [])
    round_info = st.session_state.get('round_info', {})
    
    export_data = {
        'round_info': round_info,
        'scores': []
    }
    
    for player in players:
        player_id = player['id']
        score_data = {
            'player': player,
            'front_score': st.session_state.get(f"front_score_{player_id}", 0),
            'front_putt': st.session_state.get(f"front_putt_{player_id}", 0),
            'front_game_pt': st.session_state.get(f"front_game_pt_{player_id}", 0)
        }
        export_data['scores'].append(score_data)
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📄 JSONファイルをダウンロード",
        data=json_str,
        file_name=f"golf_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        use_container_width=True
    )

def export_to_csv():
    """CSV形式でエクスポート"""
    players = st.session_state.get('players', [])
    
    csv_data = []
    for player in players:
        player_id = player['id']
        csv_data.append({
            'プレイヤー名': player['name'],
            'ハンディキャップ': player['handicap'],
            'フロントスコア': st.session_state.get(f"front_score_{player_id}", 0),
            'フロントパット': st.session_state.get(f"front_putt_{player_id}", 0),
            'ゲームポイント': st.session_state.get(f"front_game_pt_{player_id}", 0),
            'PAR差': st.session_state.get(f"front_score_{player_id}", 0) - 36
        })
    
    df = pd.DataFrame(csv_data)
    csv_str = df.to_csv(index=False, encoding='utf-8-sig')
    
    st.download_button(
        label="📊 CSVファイルをダウンロード",
        data=csv_str,
        file_name=f"golf_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

if __name__ == "__main__":
    main()
