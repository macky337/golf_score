import sys
import os

# モジュールのインポートパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import datetime

st.set_page_config(
    page_title="簡単テストセットアップ",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 簡単テストセットアップ")

st.write("### 📋 テスト手順")
st.write("1. 下のボタンをクリックしてテストラウンドIDを設定")
st.write("2. 新しいタブで改善版UIを開く")

col1, col2 = st.columns(2)

with col1:
    if st.button("🎯 テストラウンド設定", use_container_width=True, type="primary"):
        st.session_state.active_round_id = 901
        st.write("✅ テストラウンド ID: 901 を設定しました")

with col2:
    if st.button("⛳ 改善版UIを開く", use_container_width=True):
        st.write("新しいタブで以下のURLを開いてください：")
        st.code("http://localhost:8502")

if "active_round_id" in st.session_state:
    st.write(f"現在のアクティブラウンド: {st.session_state.active_round_id}")

st.write("### 🌐 起動中のアプリ")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("**メインアプリ**")
    st.code("http://localhost:8501")
with col2:
    st.write("**改善版フロントスコア**")
    st.code("http://localhost:8502")
with col3:
    st.write("**簡単テスト**")
    st.code("http://localhost:8504")

st.write("### 💡 ヒント")
st.write("- 改善版UIでは「🧪 テストモードで開始」ボタンが使用できます")
st.write("- データベース接続エラーが出る場合は、テストモードで試してください")
st.write("- ブラウザを縮小してモバイル表示を確認してください")
