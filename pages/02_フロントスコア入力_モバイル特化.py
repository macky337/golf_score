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

def create_mobile_score_input(label, current_value, key, score_type="score"):
    """モバイル最適化されたスコア入力UI"""
    
    # スコアタイプごとの設定
    if score_type == "score":
        typical_range = list(range(35, 65, 5))  # 35, 40, 45, 50, 55, 60
        min_val, max_val = 25, 80
        color_scheme = {
            'excellent': '#28a745',  # 緑
            'good': '#17a2b8',       # 水色
            'average': '#ffc107',    # 黄
            'challenging': '#fd7e14', # オレンジ
            'difficult': '#dc3545'   # 赤
        }
        def get_color(score):
            if score <= 40: return color_scheme['excellent']
            elif score <= 45: return color_scheme['good']
            elif score <= 50: return color_scheme['average']
            elif score <= 55: return color_scheme['challenging']
            else: return color_scheme['difficult']
            
    elif score_type == "putt":
        typical_range = list(range(12, 25, 2))  # 12, 14, 16, 18, 20, 22, 24
        min_val, max_val = 8, 30
        def get_color(putts):
            if putts <= 14: return '#28a745'    # 素晴らしい
            elif putts <= 18: return '#17a2b8'  # 良い
            elif putts <= 20: return '#ffc107'  # 普通
            else: return '#fd7e14'              # 改善余地あり
            
    else:  # game_pt
        typical_range = [-30, -20, -10, 0, 10, 20, 30]
        min_val, max_val = -100, 100
        def get_color(game_pts):
            if game_pts >= 20: return '#28a745'      # 大勝利
            elif game_pts >= 0: return '#17a2b8'     # プラス
            elif game_pts >= -10: return '#ffc107'   # 小さなマイナス
            else: return '#fd7e14'              # 大きなマイナス
    
    # ラベル表示
    st.markdown(f"""
    <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 15px;'>
        <h4 style='margin: 0; color: #007bff;'>{label}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # 現在の値の大きな表示
    current_color = get_color(current_value)
    st.markdown(f"""
    <div style='text-align: center; font-size: 32px; font-weight: bold; 
                background: linear-gradient(135deg, {current_color}, {current_color}dd); 
                color: white; padding: 20px; border-radius: 15px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 15px 0;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>
        {current_value}
    </div>
    """, unsafe_allow_html=True)
    
    # クイック選択（ゴルフ場でよくあるスコア）
    st.markdown("**🎯 クイック選択**")
    cols = st.columns(len(typical_range))
    for i, val in enumerate(typical_range):
        with cols[i]:
            button_color = get_color(val)
            if st.button(
                str(val), 
                key=f"{key}_quick_{val}",
                use_container_width=True,
                help=f"{val}に設定"
            ):
                st.session_state[key] = val
                st.rerun()
    
    # 微調整ボタン（大きめ、見やすく）
    st.markdown("**⚡ 微調整**")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    adjustments = [(-10, "📉 -10"), (-5, "➖ -5"), (-1, "👇 -1"), 
                   (+1, "👆 +1"), (+5, "➕ +5"), (+10, "📈 +10")]
    
    for i, (adj, label_btn) in enumerate(adjustments):
        with [col1, col2, col3, col4, col5, col6][i]:
            if st.button(
                label_btn, 
                key=f"{key}_adj_{adj}",
                use_container_width=True,
                help=f"{abs(adj)}{'減らす' if adj < 0 else '増やす'}"
            ):
                new_val = max(min_val, min(max_val, current_value + adj))
                st.session_state[key] = new_val
                st.rerun()
    
    # 詳細入力（エキスパンダー内）
    with st.expander("🔧 詳細入力・手動設定"):
        manual_input = st.number_input(
            f"手動で{label}を入力",
            min_value=min_val,
            max_value=max_val,
            value=current_value,
            key=f"{key}_manual",
            help=f"{min_val}から{max_val}まで入力可能"
        )
        
        if manual_input != current_value:
            st.session_state[key] = manual_input
            st.success(f"✅ {label}を{manual_input}に更新しました")
            st.rerun()
        
        # リセットボタン
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 リセット", key=f"{key}_reset", use_container_width=True):
                if score_type == "score":
                    st.session_state[key] = 45
                elif score_type == "putt":
                    st.session_state[key] = 16
                else:
                    st.session_state[key] = 0
                st.rerun()
        
        with col_b:
            if score_type == "score" and st.button("🎯 パー想定", key=f"{key}_par", use_container_width=True):
                st.session_state[key] = 36  # 9ホールパー想定
                st.rerun()

def create_player_summary_card(player_name, member_id, scores_data):
    """プレイヤーのサマリーカード"""
    front_score = st.session_state.get(f"front_score_{member_id}", 0)
    front_putt = st.session_state.get(f"front_putt_{member_id}", 0)
    front_game_pt = st.session_state.get(f"front_game_pt_{member_id}", 0)
    
    # スコアの評価
    if front_score <= 40:
        score_status = "🔥 絶好調"
        score_color = "#28a745"
    elif front_score <= 50:
        score_status = "✨ 好調"
        score_color = "#17a2b8"
    else:
        score_status = "💪 がんばれ"
        score_color = "#ffc107"
    
    # パットの評価
    if front_putt <= 16:
        putt_status = "🎯 ナイスパット"
        putt_color = "#28a745"
    else:
        putt_status = "⛳ 要練習"
        putt_color = "#ffc107"
    
    return f"""
    <div style='background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
                padding: 20px; border-radius: 15px; border: 2px solid #dee2e6; 
                margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        <h3 style='margin: 0 0 15px 0; color: #495057; text-align: center;'>👤 {player_name}</h3>
        
        <div style='display: flex; justify-content: space-around; flex-wrap: wrap;'>
            <div style='text-align: center; min-width: 80px; margin: 5px;'>
                <div style='background-color: {score_color}; color: white; 
                           font-size: 20px; font-weight: bold; padding: 10px; 
                           border-radius: 8px; margin-bottom: 5px;'>{front_score}</div>
                <div style='font-size: 12px; color: #6c757d;'>🏌️ スコア</div>
                <div style='font-size: 10px; color: {score_color}; font-weight: bold;'>{score_status}</div>
            </div>
            
            <div style='text-align: center; min-width: 80px; margin: 5px;'>
                <div style='background-color: {putt_color}; color: white; 
                           font-size: 20px; font-weight: bold; padding: 10px; 
                           border-radius: 8px; margin-bottom: 5px;'>{front_putt}</div>
                <div style='font-size: 12px; color: #6c757d;'>⛳ パット</div>
                <div style='font-size: 10px; color: {putt_color}; font-weight: bold;'>{putt_status}</div>
            </div>
            
            <div style='text-align: center; min-width: 80px; margin: 5px;'>
                <div style='background-color: #6f42c1; color: white; 
                           font-size: 20px; font-weight: bold; padding: 10px; 
                           border-radius: 8px; margin-bottom: 5px;'>{front_game_pt:+d}</div>
                <div style='font-size: 12px; color: #6c757d;'>🎯 GP</div>
                <div style='font-size: 10px; color: #6f42c1; font-weight: bold;'>ボーナス</div>
            </div>
        </div>
    </div>
    """

def run():
    st.set_page_config(
        page_title="⛳ フロントスコア入力",
        page_icon="⛳",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # カスタムCSS（モバイル完全最適化）
    st.markdown("""
    <style>
    /* メイン設定 */
    .main > div {
        padding-top: 0.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* ボタンスタイル */
    .stButton > button {
        width: 100%;
        height: 3.5rem;
        font-size: 16px;
        font-weight: bold;
        border-radius: 12px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* プライマリボタン */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        font-size: 18px;
        height: 4rem;
    }
    
    /* タブスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding-left: 1rem;
        padding-right: 1rem;
        border-radius: 8px;
        font-weight: bold;
    }
    
    /* エキスパンダースタイル */
    .streamlit-expanderHeader {
        font-size: 16px;
        font-weight: bold;
    }
    
    /* モバイル特化 */
    @media (max-width: 768px) {
        .main > div {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        .stButton > button {
            height: 3rem;
            font-size: 14px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ヘッダー
    st.markdown("""
    <div style='background: linear-gradient(90deg, #007bff, #0056b3); 
                padding: 20px; border-radius: 15px; margin-bottom: 20px;
                text-align: center; color: white;'>
        <h1 style='margin: 0; font-size: 28px;'>⛳ フロントスコア入力</h1>
        <p style='margin: 10px 0 0 0; opacity: 0.9;'>前半9ホールのスコアを入力してください</p>
    </div>
    """, unsafe_allow_html=True)
    
    # プログレス表示
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
            <span style='font-weight: bold; color: #007bff;'>📍 進行状況</span>
            <span style='color: #6c757d;'>1 / 3 ステップ</span>
        </div>
        <div style='background-color: #e9ecef; height: 8px; border-radius: 4px;'>
            <div style='background-color: #007bff; height: 100%; width: 33%; border-radius: 4px; transition: width 0.5s ease;'></div>
        </div>
        <div style='text-align: center; margin-top: 8px; color: #6c757d; font-size: 14px;'>
            フロント → バック → エクストラ
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Supabaseクライアント取得
    supabase = ensure_supabase()
    
    # アクティブラウンドチェック
    if "active_round_id" not in st.session_state:
        st.error("🚨 ラウンドが選択されていません")
        if st.button("🏠 ホームに戻る", use_container_width=True):
            st.session_state.clear()
            st.switch_page("main.py")
        return
    
    round_id = st.session_state.active_round_id
    
    # ラウンド情報取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        st.error("ラウンド情報が見つかりません")
        return
    
    active_round = round_result.data[0]
    
    # ラウンド情報表示
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #e3f2fd, #bbdefb); 
                padding: 15px; border-radius: 12px; border-left: 5px solid #2196f3; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <h4 style='margin: 0; color: #1976d2;'>📅 {active_round['date_played']}</h4>
                <h5 style='margin: 5px 0 0 0; color: #424242;'>🏌️ {active_round['course_name']}</h5>
            </div>
            <div style='text-align: right; color: #1976d2; font-size: 24px;'>⛳</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # スコア情報取得
    scores = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores.data:
        st.error("スコアデータが見つかりません")
        return
    
    scores_data = sorted(scores.data, key=lambda x: x['member_id'])
    
    # セッション状態初期化
    for score in scores_data:
        member_id = score['member_id']
        for field, default in [('front_score', 45), ('front_putt', 16), ('front_game_pt', 0)]:
            key = f"{field}_{member_id}"
            if key not in st.session_state:
                db_value = score.get(field, default)
                st.session_state[key] = db_value if db_value is not None else default
    
    # プレイヤー選択（タブ形式）
    player_names = [score['member']['name'] if score['member'] else f"Player {score['member_id']}" 
                   for score in scores_data]
    
    # 現在のプレイヤー選択状態
    if 'current_player_index' not in st.session_state:
        st.session_state.current_player_index = 0
    
    # プレイヤー選択ボタン
    st.markdown("### 👥 プレイヤー選択")
    cols = st.columns(len(player_names))
    for i, name in enumerate(player_names):
        with cols[i]:
            button_style = "primary" if i == st.session_state.current_player_index else "secondary"
            if st.button(f"👤 {name}", key=f"player_select_{i}", use_container_width=True):
                st.session_state.current_player_index = i
                st.rerun()
    
    # 現在選択中のプレイヤー
    current_score = scores_data[st.session_state.current_player_index]
    current_member_id = current_score['member_id']
    current_player_name = current_score['member']['name'] if current_score['member'] else f"Player {current_member_id}"
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #fff3cd, #ffeaa7); 
                padding: 20px; border-radius: 15px; border-left: 5px solid #ffc107; 
                margin: 20px 0; text-align: center;'>
        <h3 style='margin: 0; color: #856404;'>🎯 現在入力中: {current_player_name}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # スコア入力エリア
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # スコア入力
        st.markdown("---")
        create_mobile_score_input(
            "🏌️‍♀️ フロントスコア (9ホール)",
            st.session_state.get(f"front_score_{current_member_id}", 45),
            f"front_score_{current_member_id}",
            "score"
        )
        
        st.markdown("---")
        create_mobile_score_input(
            "⛳ フロントパット数",
            st.session_state.get(f"front_putt_{current_member_id}", 16),
            f"front_putt_{current_member_id}",
            "putt"
        )
        
        st.markdown("---")
        create_mobile_score_input(
            "🎯 ゲームポイント",
            st.session_state.get(f"front_game_pt_{current_member_id}", 0),
            f"front_game_pt_{current_member_id}",
            "game_pt"
        )
    
    with col2:
        # サイドパネル: 他プレイヤーの状況
        st.markdown("### 📊 他プレイヤー")
        for i, score in enumerate(scores_data):
            if i != st.session_state.current_player_index:
                member_id = score['member_id']
                player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
                front_score = st.session_state.get(f"front_score_{member_id}", 0)
                front_putt = st.session_state.get(f"front_putt_{member_id}", 0)
                
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 10px; border-radius: 8px; margin: 5px 0; font-size: 12px;'>
                    <div style='font-weight: bold; color: #495057;'>{player_name}</div>
                    <div>🏌️ {front_score} ⛳ {front_putt}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # 全プレイヤーサマリー
    st.markdown("---")
    st.markdown("### 📋 入力状況サマリー")
    
    for score in scores_data:
        member_id = score['member_id']
        player_name = score['member']['name'] if score['member'] else f"Player {member_id}"
        st.markdown(create_player_summary_card(player_name, member_id, scores_data), unsafe_allow_html=True)
    
    # 保存とナビゲーション
    st.markdown("---")
    st.markdown("### 💾 保存・次へ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 データを保存", use_container_width=True, type="primary"):
            # 保存処理
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
                    st.error(f"❌ 保存エラー: {e}")
                    success = False
                    break
            
            if success:
                st.success("✅ データを保存しました！")
                st.balloons()
                
                # 計算処理も実行
                try:
                    scores = get_scores_with_fallback(round_id)
                    if scores:
                        handicaps_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                        handicaps_data = handicaps_result.data
                        round_results = get_round_results(round_id)
                        
                        from modules.data_formatter import initialize_player_data
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
                        
                        updated_player_data = calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round)
                        save_round_results(round_id, updated_player_data)
                        
                except Exception as e:
                    st.warning(f"⚠️ 計算処理エラー: {e}")
    
    with col2:
        if st.button("➡️ バックスコア入力へ", use_container_width=True):
            st.switch_page("pages/03_バックスコア入力.py")
    
    # 成功メッセージ（アニメーション付き）
    if 'show_success' in st.session_state and st.session_state.show_success:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                    padding: 20px; border-radius: 15px; border-left: 5px solid #28a745; 
                    margin: 20px 0; text-align: center; animation: fadeIn 0.5s;'>
            <h4 style='margin: 0; color: #155724;'>🎉 フロントスコア入力完了！</h4>
            <p style='margin: 10px 0 0 0; color: #155724;'>次はバックスコア入力に進んでください</p>
        </div>
        
        <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 自動でフラグをリセット
        st.session_state.show_success = False

if __name__ == "__main__":
    run()
