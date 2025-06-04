import sys
import os
# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from scripts.version_manager import load_version
from dotenv import load_dotenv
import traceback

# Streamlit ページ設定
st.set_page_config(
    page_title="Golf Score App", 
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def check_supabase_connection():
    """Supabaseの接続状況を確認する関数"""
    load_dotenv()
    
    # 環境変数の確認
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        return False, "環境変数が設定されていません"
    
    try:
        # Supabaseクライアントのインポートを試行
        from supabase import create_client
        
        # クライアントの作成を試行
        supabase = create_client(supabase_url, supabase_key)
        
        # 実際に存在するテーブルを使用して接続テスト
        # existsメソッドを使用してテーブルの存在チェックのみを行う（データ取得は不要）
        response = supabase.table('rounds').select('count').limit(1).execute()
        
        return True, "接続成功"
    except ImportError:
        return False, "supabaseモジュールがインストールされていません"
    except Exception as e:
        return False, f"接続エラー: {str(e)}"

def main():
    """メインページの表示関数"""
    try:
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
                switch_page("09_マニュアル")

        # メインメニューの作成
        st.subheader("📌 メインメニュー")
        
        # 2列のレイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 スコア入力")
            if st.button("ラウンド設定", key="nav_main_round_settings"): 
                st.write("ボタン押下: ラウンド設定")
                try:
                    switch_page("01_ラウンド設定")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("フロントスコア入力", key="nav_main_front"): 
                st.write("ボタン押下: フロントスコア入力")
                try:
                    switch_page("02_フロントスコア入力")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("バックスコア入力", key="nav_main_back"): 
                try:
                    switch_page("03_バックスコア入力")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("エキストラスコア入力", key="nav_main_extra"): 
                st.write("ボタン押下: エキストラスコア入力")
                try:
                    switch_page("05_エキストラスコア入力")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
                    
        with col2:
            st.markdown("### 📊 集計・確認")
            if st.button("結果確認", key="nav_main_results"): 
                st.write("ボタン押下: 結果確認")
                try:
                    switch_page("06_結果確認")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("ポイント集計", key="nav_main_points"): 
                st.write("ボタン押下: ポイント集計")
                try:
                    switch_page("07_ポイント集計")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("管理画面", key="nav_main_admin"): 
                st.write("ボタン押下: 管理画面")
                try:
                    switch_page("08_管理画面")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("メンバー登録", key="nav_main_members"): 
                st.write("ボタン押下: メンバー登録")
                try:
                    switch_page("08_メンバー登録")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("コース管理", key="nav_main_courses"): 
                st.write("ボタン押下: コース管理")
                try:
                    switch_page("09_コース管理")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
        
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
        
        # Supabase接続状況の確認と表示
        supabase_connected, message = check_supabase_connection()
        connection_status = "✅ 接続済み" if supabase_connected else f"❌ 未接続 ({message})"
        connection_color = "green" if supabase_connected else "red"
        
        # バージョン情報の表示
        version_info = load_version()
        st.markdown("---")
        st.markdown(f"""
        <div style='text-align: right; color: gray; font-size: 0.8em;'>
            バージョン: {version_info['major']}.{version_info['minor']}.{version_info['patch']}<br>
            最終更新日: {version_info['last_updated']}<br>
        Supabase: <span style='color: {connection_color};'>{connection_status}</span>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"アプリケーションの初期化中にエラーが発生しました: {str(e)}")
        st.error("ページを再読み込みしてください。問題が続く場合は管理者にお問い合わせください。")
        with st.expander("詳細なエラー情報"):
            st.code(traceback.format_exc())

def show_changelog():
    try:
        with st.expander("📋 更新履歴"):
            # スクリプトのディレクトリを基準にCHANGELOG.mdのパスを構築
            script_dir = os.path.dirname(os.path.abspath(__file__))
            changelog_path = os.path.join(script_dir, "CHANGELOG.md")
            
            if os.path.exists(changelog_path):
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog = f.read()
                st.markdown(changelog)
            else:
                st.warning(f"CHANGELOG.mdファイルが見つかりません: {changelog_path}")
    except Exception as e:
        with st.expander("📋 更新履歴"):
            st.error(f"更新履歴の読み込みに失敗しました: {str(e)}")
            # デバッグ情報を追加
            script_dir = os.path.dirname(os.path.abspath(__file__))
            changelog_path = os.path.join(script_dir, "CHANGELOG.md")
            st.code(f"探索パス: {changelog_path}")
            st.code(f"ファイル存在確認: {os.path.exists(changelog_path)}")
            if os.path.exists(script_dir):
                files = os.listdir(script_dir)
                st.code(f"ディレクトリ内容: {files}")

if __name__ == "__main__":
    main()