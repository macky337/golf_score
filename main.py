import streamlit as st
from modules.page_utils import switch_page
from scripts.version_manager import load_version
import os
from dotenv import load_dotenv
import traceback

# Streamlit ページ設定
st.set_page_config(
    page_title="Golf Score App", 
    page_icon="⛳",
    layout="wide",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': 'https://github.com/your-repo/issues',
        'About': "Golf Score App - main"
    }
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
                switch_page("10_マニュアル")

        # メインメニューの作成
        st.subheader("📌 メインメニュー")
        
        # 2列のレイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 スコア入力")
            if st.button("ラウンド設定", key="nav_main_round_settings"): 
                st.write("ボタン押下: ラウンド設定")
                # デバッグ: ファイルの存在確認
                import os
                page_path = os.path.join("pages", "01_ラウンド設定.py")
                st.write(f"デバッグ: ファイルパス = {page_path}")
                st.write(f"デバッグ: ファイル存在 = {os.path.exists(page_path)}")
                try:
                    switch_page("01_ラウンド設定")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
                    # 他の方法も試してみる
                    try:
                        st.write("別の方法を試行中...")
                        switch_page("pages/01_ラウンド設定")
                    except Exception as e2:
                        st.error(f"別の方法でも失敗: {e2}")
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
                    switch_page("04_エキストラスコア入力")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
                    
        with col2:
            st.markdown("### 📊 集計・確認")
            if st.button("結果確認", key="nav_main_results"): 
                st.write("ボタン押下: 結果確認")
                try:
                    switch_page("05_結果確認")
                except Exception as e:
                    st.error(f"switch_page例外: {e}")
            if st.button("ポイント集計", key="nav_main_points"): 
                st.write("ボタン押下: ポイント集計")
                try:
                    switch_page("06_ポイント集計")
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
                    switch_page("07_メンバー登録")
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
        
        # バージョン情報の表示（複数のフォールバック対応）
        try:
            version_info = load_version()
        except Exception as e:
            # フォールバック1: version.pyから読み込み
            try:
                from version import VERSION
                version_info = VERSION
            except Exception:
                # フォールバック2: 固定値
                version_info = {
                    'major': 1,
                    'minor': 0, 
                    'patch': 246,
                    'last_updated': '2025-06-14'
                }
        
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
            # 複数のパスで CHANGELOG.md を検索
            possible_paths = [
                # 1. スクリプトと同じディレクトリ
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "CHANGELOG.md"),
                # 2. 現在の作業ディレクトリ
                os.path.join(os.getcwd(), "CHANGELOG.md"),
                # 3. Railway環境での絶対パス
                "/app/CHANGELOG.md",
                # 4. 相対パス
                "CHANGELOG.md",
                # 5. 一つ上のディレクトリ
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "CHANGELOG.md")
            ]
            
            changelog_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    changelog_path = path
                    break
            
            if changelog_path:
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog = f.read()
                st.markdown(changelog)
                st.caption(f"📍 読み込み元: {changelog_path}")
            else:
                st.warning("📋 更新履歴ファイルが見つかりません")
                # フォールバック: 基本的な更新情報を表示
                st.markdown("""
                ### 🚀 最新の更新内容
                - ✅ Railway デプロイエラー解決
                - ⚡ 超高速デプロイ最適化 (2-3分)
                - 📦 依存関係96%削減 (129個→5個)
                - 🔧 CHANGELOG読み込み問題修正
                """)
    except Exception as e:
        with st.expander("📋 更新履歴"):
            st.error(f"更新履歴の読み込みに失敗しました: {str(e)}")
            # デバッグ情報を追加
            st.subheader("🔍 デバッグ情報")
            st.code(f"現在の作業ディレクトリ: {os.getcwd()}")
            st.code(f"スクリプトの場所: {os.path.abspath(__file__)}")
            
            # 利用可能なファイルを表示
            try:
                current_files = os.listdir(os.getcwd())
                md_files = [f for f in current_files if f.endswith('.md')]
                st.code(f"現在のディレクトリのMDファイル: {md_files}")
                
                script_dir = os.path.dirname(os.path.abspath(__file__))
                if os.path.exists(script_dir):
                    script_files = os.listdir(script_dir)
                    script_md_files = [f for f in script_files if f.endswith('.md')]
                    st.code(f"スクリプトディレクトリのMDファイル: {script_md_files}")
            except Exception as debug_e:
                st.code(f"ディレクトリ情報取得エラー: {str(debug_e)}")
            
            # フォールバック情報
            st.markdown("""
            ### 🚀 主要な更新内容
            - ✅ Railway デプロイエラー解決
            - ⚡ 超高速デプロイ最適化
            - 📦 依存関係大幅削減
            """)

if __name__ == "__main__":
    main()
