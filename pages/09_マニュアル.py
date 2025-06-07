
import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

def run():
    # タイトルとホームボタンを横に配置
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("マニュアル")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")
    
    # マニュアルの内容を読み込んで表示
    try:
        # 複数のパスを試す
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_file_dir)
        
        # マニュアルファイルの検索パス
        possible_paths = [
            os.path.join(project_root, "マニュアル.md"),  # プロジェクトルート
            os.path.join(current_file_dir, "マニュアル.md"),  # pagesディレクトリ
            os.path.join(os.getcwd(), "マニュアル.md"),  # 作業ディレクトリ
            r"c:\Users\user\Documents\GitHub\golf_score\マニュアル.md",  # 絶対パス
            "/app/マニュアル.md"  # Railway/Docker環境
        ]
        
        manual_found = False
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding='utf-8') as f:
                        manual_content = f.read()
                    st.markdown(manual_content)
                    st.caption(f"📍 読み込み元: {path}")
                    manual_found = True
                    break
                except Exception as e:
                    st.warning(f"マニュアルファイル読み込みエラー: {e}")
                    continue
        
        if not manual_found:
            st.error("マニュアルファイルが見つかりませんでした。")
            
            # フォールバック: 基本的なマニュアル情報を表示
            st.subheader("⛳ Golf Score App 基本マニュアル")
            st.markdown("""
            ## 🏌️‍♂️ 基本的な使い方
            1. **ラウンド設定**: 新規ラウンドの基本情報を設定します
            2. **フロントスコア入力**: フロント9のスコアを入力します
            3. **バックスコア入力**: バック9のスコアを入力します
            4. **エキストラスコア入力**: 追加ホールのスコアを入力します（必要な場合）
            5. **結果確認**: 入力した内容を確認し、PDFで出力できます
            6. **ポイント集計**: 全期間または期間を指定してポイントを集計します
            7. **管理画面**: データの修正や削除ができます
            8. **メンバー登録**: 新しいプレイヤーを登録します
            
            ## ⚠️ 注意事項
            - スコアの入力は、ラウンド設定 → フロント → バック → エキストラの順で行ってください
            - 入力したデータは「結果確認」画面で確認できます
            - データの修正が必要な場合は「管理画面」をご利用ください
            """)
            
            st.info("詳細なマニュアルファイルをプロジェクトルートの「マニュアル.md」として配置してください。")
    except Exception as e:
        st.error(f"マニュアルファイル読み込みエラー: {str(e)}")
        st.warning("プロジェクトルートに「マニュアル.md」ファイルが存在することを確認してください。")

if __name__ == "__main__":
    # Streamlit ページ設定
    st.set_page_config(
        page_title="マニュアル - Golf Score App", 
        page_icon="📖",
        layout="wide"
    )
    run()
