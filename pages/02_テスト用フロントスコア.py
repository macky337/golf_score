import streamlit as st
import pandas as pd

# テスト専用の完全オフラインUIデモ
def main():
    st.set_page_config(
        page_title="テスト用フロントスコア入力",
        page_icon="🧪",
        layout="wide"
    )
    
    # 強制的にテストモード設定
    st.session_state['active_round_id'] = 901
    st.session_state['test_mode'] = True
    
    st.markdown("# 🧪 テスト用フロントスコア入力")
    st.success("✅ テストモード - データベース接続不要")
    
    # テストラウンド情報
    st.markdown("""
    <div style='background-color: #fff3cd; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107;'>
    <h4 style='margin: 0; color: #856404;'>📅 2025-08-02 🧪 (テストモード)</h4>
    <h5 style='margin: 5px 0 0 0; color: #495057;'>🏌️ テストゴルフ場</h5>
    </div>
    """, unsafe_allow_html=True)
    
    # ダミープレイヤーデータ
    players = [
        {'id': 901, 'name': 'テストプレイヤー1'},
        {'id': 902, 'name': 'テストプレイヤー2'},
        {'id': 903, 'name': 'テストプレイヤー3'},
        {'id': 904, 'name': 'テストプレイヤー4'}
    ]
    
    # セッション状態初期化
    for player in players:
        for field in ['front_score', 'front_putt', 'front_game_pt']:
            key = f"{field}_{player['id']}"
            if key not in st.session_state:
                defaults = {'front_score': 45, 'front_putt': 16, 'front_game_pt': 0}
                st.session_state[key] = defaults[field]
    
    # タブ形式でプレイヤー入力
    tabs = st.tabs([f"👤 {player['name']}" for player in players])
    
    for i, (tab, player) in enumerate(zip(tabs, players)):
        with tab:
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 15px; border: 2px solid #e9ecef; margin: 10px 0;'>
            <h3 style='text-align: center; color: #007bff; margin-bottom: 20px;'>👤 {player['name']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # スコア入力
            st.markdown("### 🏌️‍♀️ スコア")
            create_score_widget(f"front_score_{player['id']}", "前半9ホール スコア", [35, 40, 45, 50, 55, 60])
            
            st.markdown("---")
            
            # パット入力
            st.markdown("### ⛳ パット")
            create_score_widget(f"front_putt_{player['id']}", "前半9ホール パット数", [12, 14, 16, 18, 20, 22])
            
            st.markdown("---")
            
            # ゲームポイント入力
            st.markdown("### 🎯 ゲームポイント")
            create_score_widget(f"front_game_pt_{player['id']}", "ニアピン・ドラコンなど", [-30, -10, 0, 10, 30, 50])
    
    # 入力状況サマリー
    st.markdown("---")
    st.markdown("### 📊 入力状況")
    
    summary_data = []
    for player in players:
        summary_data.append({
            '👤 プレイヤー': player['name'],
            '🏌️ スコア': st.session_state.get(f"front_score_{player['id']}", 0),
            '⛳ パット': st.session_state.get(f"front_putt_{player['id']}", 0),
            '🎯 GP': st.session_state.get(f"front_game_pt_{player['id']}", 0)
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 保存ボタン（テスト用）
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 テスト保存（実際には保存されません）", use_container_width=True, type="primary"):
            st.success("✅ テストモード: データ保存をスキップしました")
            st.balloons()
            
            st.markdown("""
            <div style='background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin: 20px 0;'>
            <h4 style='margin: 0; color: #155724;'>🎉 テスト完了！</h4>
            <p style='margin: 10px 0 0 0; color: #155724;'>改善版UIの機能をご確認いただけました</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("### 📱 改善版UIの特徴")
            st.write("✅ タブベースのプレイヤー切り替え")
            st.write("✅ クイック選択ボタン")
            st.write("✅ ±1, ±5の微調整ボタン")
            st.write("✅ 色分け表示")
            st.write("✅ 大きなボタンサイズ（モバイル最適化）")

def create_score_widget(key, label, quick_values):
    """シンプルなスコア入力ウィジェット"""
    current_value = st.session_state.get(key, quick_values[2])
    
    # クイック選択ボタン
    st.write("クイック選択:")
    cols = st.columns(len(quick_values))
    for i, val in enumerate(quick_values):
        with cols[i]:
            if st.button(str(val), key=f"{key}_quick_{val}", use_container_width=True):
                st.session_state[key] = val
                st.rerun()
    
    # 現在の値表示（色分け）
    if "score" in key:
        if current_value <= 40:
            color = "#28a745"  # 緑
        elif current_value <= 50:
            color = "#ffc107"  # 黄
        else:
            color = "#dc3545"  # 赤
    else:
        color = "#1f77b4"  # 青
    
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
            st.session_state[key] = max(0, current_value - 5)
            st.rerun()
    with col2:
        if st.button("-1", key=f"{key}_minus1", use_container_width=True):
            st.session_state[key] = max(0, current_value - 1)
            st.rerun()
    with col3:
        if st.button("+1", key=f"{key}_plus1", use_container_width=True):
            st.session_state[key] = min(100, current_value + 1)
            st.rerun()
    with col4:
        if st.button("+5", key=f"{key}_plus5", use_container_width=True):
            st.session_state[key] = min(100, current_value + 5)
            st.rerun()

if __name__ == "__main__":
    main()
