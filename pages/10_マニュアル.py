import streamlit as st
import sys
import os
from streamlit_extras.switch_page_button import switch_page

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run():
    # タイトルとホームボタンを横に配置
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("マニュアル")
    with col2:
        if st.button("🏠 Home", key="manual_home_button"):
            switch_page("main")
    
    # マニュアルの内容を表示
    display_embedded_manual()

def display_embedded_manual():
    """
    埋め込みマニュアルを表示
    """
    st.markdown("""
# Golf Score App マニュアル

## 1. アプリケーションの概要
本アプリケーションは、ゴルフのスコア管理、マッチ戦の記録、ポイント集計を行うためのツールです。

## 2. 基本的な使用手順

### 2.1. メンバー登録
1. メインメニューから「メンバー登録」を選択
2. メンバー名を入力
3. 「登録」ボタンをクリック

### 2.2. ラウンド設定
1. メインメニューから「ラウンド設定」を選択
2. 必要項目を設定して保存

### 2.3. スコア入力
- フロントスコア → バックスコア → エキストラスコアの順で入力

### 2.4. 結果確認
- ラウンド結果とPDF出力が可能

### 2.5. ポイント集計
- 期間を指定してポイント集計を表示

## 3. 注意事項
- データはSupabaseに保存されます
- インターネット接続が必要です
""")

if __name__ == "__main__":
    run()
else:
    # Streamlit Pages用の直接実行
    run()