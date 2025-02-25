import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from scripts.version_manager import load_version

def main():
    st.title("⛳ Golf Score App")
    
    # アプリの説明とマニュアルリンク
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.markdown("""
        ### ようこそ Golf Score App へ
        このアプリでは、ゴルフのスコア管理や集計が簡単に行えます。
        """)
    with col2:
        # マニュアルページへのリンク
        if st.button("📚 マニュアル", key="manual_button"):
            switch_page("マニュアル")

    # メインメニューの作成
    st.subheader("📌 メインメニュー")
    
    # 2列のレイアウト
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 スコア入力")
        st.markdown("""
        - [ラウンド設定](ラウンド設定)
        - [フロントスコア入力](フロントスコア入力)
        - [バックスコア入力](バックスコア入力)
        - [エキストラスコア入力](エキストラスコア入力)
        """)
        
    with col2:
        st.markdown("### 📊 集計・確認")
        st.markdown("""
        - [結果確認](結果確認)
        - [ポイント集計](ポイント集計)
        - [管理画面](管理画面)
        - [メンバー登録](メンバー登録)
        """)
    
    # 使い方ガイド
    with st.expander("💡 使い方ガイド"):
        st.markdown("""
        #### 基本的な使い方
        1. **ラウンド設定**: 新規ラウンドの基本情報を設定します
        2. **フロントスコア入力**: フロント9のスコアを入力します
        3. **バックスコア入力**: バック9のスコアを入力します
        4. **エキストラスコア入力**: 追加ホールのスコアを入力します（必要な場合）
        5. **結果確認**: 入力した内容を確認し、PDFで出力できます
        6. **ポイント集計**: 全期間または期間を指定してポイントを集計します
        7. **管理画面**: データの修正や削除ができます
        8. **メンバー登録**: 新しいプレイヤーを登録します
        """)
    
    show_changelog()
    
    # フッター
    st.markdown("---")
    st.markdown("""
    #### 📌 注意事項
    - スコアの入力は、ラウンド設定 → フロント → バック → エキストラの順で行ってください
    - 入力したデータは「結果確認」画面で確認できます
    - データの修正が必要な場合は「管理画面」をご利用ください
    """)
    
    # バージョン情報の表示
    version_info = load_version()
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: right; color: gray; font-size: 0.8em;'>
        バージョン: {version_info['major']}.{version_info['minor']}.{version_info['patch']}<br>
        最終更新日: {version_info['last_updated']}
    </div>
    """, unsafe_allow_html=True)

def show_changelog():
    with st.expander("📋 更新履歴"):
        with open("CHANGELOG.md", "r", encoding="utf-8") as f:
            changelog = f.read()
        st.markdown(changelog)

if __name__ == "__main__":
    main()
