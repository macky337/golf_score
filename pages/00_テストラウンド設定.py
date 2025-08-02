import sys
import os

# モジュールのインポートパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import datetime
from modules.db import ensure_supabase

def create_test_data():
    """テスト用のラウンドとプレイヤーデータを作成"""
    supabase = ensure_supabase()
    
    try:
        # テスト用メンバーを作成（既存チェック）
        test_members = [
            {"name": "テストプレイヤー1", "member_id": 901},
            {"name": "テストプレイヤー2", "member_id": 902},
            {"name": "テストプレイヤー3", "member_id": 903},
            {"name": "テストプレイヤー4", "member_id": 904}
        ]
        
        for member in test_members:
            # 既存チェック
            existing = supabase.table('member').select('member_id').eq('member_id', member['member_id']).execute()
            if not existing.data:
                supabase.table('member').insert(member).execute()
                st.write(f"✅ {member['name']} を作成しました")
            else:
                st.write(f"ℹ️ {member['name']} は既に存在します")
        
        # テスト用ラウンドを作成
        today = datetime.date.today().strftime('%Y-%m-%d')
        
        # 既存のテストラウンドをチェック
        existing_round = supabase.table('rounds').select('round_id').gte('round_id', 900).execute()
        if existing_round.data:
            round_id = existing_round.data[0]['round_id']
            st.write(f"ℹ️ 既存のテストラウンド ID: {round_id} を使用します")
        else:
            # 新しいテストラウンドを作成
            round_data = {
                'round_id': 901,
                'date_played': today,
                'course_name': 'テストゴルフ場',
                'finalized': False,
                'has_extra': False
            }
            
            result = supabase.table('rounds').insert(round_data).execute()
            round_id = 901
            st.write(f"✅ テストラウンド ID: {round_id} を作成しました")
        
        # スコアレコードを作成
        for i, member in enumerate(test_members):
            member_id = member['member_id']
            score_id = 900 + i + 1
            
            # 既存チェック
            existing_score = supabase.table('score').select('score_id').eq('score_id', score_id).execute()
            if not existing_score.data:
                score_data = {
                    'score_id': score_id,
                    'round_id': round_id,
                    'member_id': member_id,
                    'front_score': 0,
                    'back_score': 0,
                    'extra_score': 0,
                    'front_putt': 0,
                    'back_putt': 0,
                    'extra_putt': 0,
                    'front_game_pt': 0,
                    'back_game_pt': 0,
                    'extra_game_pt': 0,
                    'total_score': 0
                }
                supabase.table('score').insert(score_data).execute()
                st.write(f"✅ {member['name']} のスコアレコードを作成しました")
            else:
                st.write(f"ℹ️ {member['name']} のスコアレコードは既に存在します")
        
        # セッション状態にラウンドIDを設定
        st.session_state.active_round_id = round_id
        
        return round_id
        
    except Exception as e:
        st.error(f"❌ エラー: {e}")
        return None

def run():
    st.set_page_config(
        page_title="テストラウンド設定",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 テストラウンド設定")
    st.write("改善版UIをテストするためのテストデータを作成します")
    
    # 現在のアクティブラウンド表示
    if "active_round_id" in st.session_state:
        st.write(f"✅ 現在のアクティブラウンド ID: {st.session_state.active_round_id}")
    else:
        st.write("⚠️ アクティブなラウンドが設定されていません")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 テストデータ作成", use_container_width=True, type="primary"):
            with st.spinner("テストデータを作成中..."):
                round_id = create_test_data()
                if round_id:
                    st.write(f"🎉 テストラウンド ID: {round_id} の準備完了！")
                    # st.balloons()を削除してエラーを回避
    
    with col2:
        if st.button("⛳ フロントスコア入力へ", use_container_width=True):
            if "active_round_id" in st.session_state:
                st.write("✅ アクティブラウンドが設定されています")
                st.write("改善版フロントスコア入力画面は別ポート(8502)で起動中です")
                st.markdown("**http://localhost:8502** にアクセスしてください")
                st.write("💡 ヒント: 新しいタブで http://localhost:8502 を開いてテストしてください")
            else:
                st.error("まずテストデータを作成してください")
    
    with col3:
        if st.button("🏠 メインに戻る", use_container_width=True):
            st.write("メインページは http://localhost:8501 で起動中です")
            st.write("💡 現在のページを更新するか、メインタブに戻ってください")
    
    st.markdown("---")
    
    # 現在のデータベース状況確認
    st.write("### 📊 データベース状況")
    
    try:
        supabase = ensure_supabase()
        
        # ラウンド一覧
        rounds = supabase.table('rounds').select('*').gte('round_id', 900).execute()
        if rounds.data:
            st.write("**🏌️ テストラウンド:**")
            for round_data in rounds.data:
                st.write(f"- ID: {round_data['round_id']} | 日付: {round_data['date_played']} | コース: {round_data['course_name']}")
        
        # メンバー一覧
        members = supabase.table('member').select('*').gte('member_id', 900).execute()
        if members.data:
            st.write("**👥 テストメンバー:**")
            for member in members.data:
                st.write(f"- ID: {member['member_id']} | 名前: {member['name']}")
        
        # スコア一覧
        scores = supabase.table('score').select('*, member:member_id(name)').gte('score_id', 900).execute()
        if scores.data:
            st.write("**📊 テストスコア:**")
            for score in scores.data:
                member_name = score['member']['name'] if score['member'] else f"ID: {score['member_id']}"
                st.write(f"- Score ID: {score['score_id']} | ラウンド: {score['round_id']} | プレイヤー: {member_name}")
    
    except Exception as e:
        st.error(f"データベース確認エラー: {e}")
    
    st.markdown("---")
    st.write("### 🔧 テストフロー")
    st.markdown("""
    1. **「テストデータ作成」**ボタンをクリック
    2. テストラウンドとプレイヤーが作成される
    3. **新しいタブで http://localhost:8502 を開く**
    4. 改善されたUI機能を確認:
       - タブベースのプレイヤー切り替え
       - クイック選択ボタン
       - ±1, ±5の微調整ボタン
       - 色分け表示
       - 大きなボタンサイズ
    """)
    
    st.markdown("### 🌐 起動中のページ")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**メインアプリ**")
        st.code("http://localhost:8501")
    with col2:
        st.markdown("**改善版フロントスコア**")
        st.code("http://localhost:8502")
    with col3:
        st.markdown("**テストラウンド設定**")
        st.code("http://localhost:8503")

if __name__ == "__main__":
    run()
