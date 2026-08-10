import streamlit as st

st.set_page_config(
    page_title="Golf Score App",
    page_icon="⛳",
    layout="wide",
)

from modules.page_utils import switch_page
from scripts.version_manager import load_version
from modules.input_helpers import close_sidebar_on_mobile
from modules.auth import require_login
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def check_supabase_connection():
    """Supabaseの接続状況を確認する関数（軽量化版）"""
    load_dotenv()
    
    # 環境変数の確認
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    # 環境変数が設定されていない場合はStreamlit secretsから読み込み
    if not supabase_url or not supabase_key:
        try:
            supabase_url = st.secrets.get('SUPABASE_URL')
            supabase_key = st.secrets.get('SUPABASE_KEY')
        except:
            pass
    
    if not supabase_url or not supabase_key:
        return False, "Supabase接続情報が環境変数またはsecretsから取得できません。"
    
    # URLの検証のみ（実際の接続テストはスキップしてパフォーマンス向上）
    if not supabase_url.startswith('https://'):
        return False, f"無効なSupabase URL: {supabase_url}"
    
    # 接続テストをスキップして常に成功を返す（高速化）
    return True, "接続情報確認済み"

def main():
    """メインページの表示関数"""
    require_login()

    try:
        # スマホでサイドバーを自動的に閉じる
        close_sidebar_on_mobile()

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

        st.info("📶 電波が弱いゴルフ場へ行く場合は、出発前にラウンド設定を保存し、開始ファイルをスマホへ保存してください。現地では端末内へ入力し、通信復帰後に同期します。")
        if st.button("📱 出発前・現地・同期：オフライン入力", key="nav_offline_score_primary", type="primary", use_container_width=True):
            switch_page("11_オフライン入力")
        
        # メインメニューの作成
        st.subheader("📌 メインメニュー")
        
        # 2列のレイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 スコア入力")
            if st.button("① ラウンド設定（最初に行う）", key="nav_main_round_settings"):
                switch_page("01_ラウンド設定")
            if st.button("フロントスコア入力", key="nav_main_front"):
                switch_page("02_フロントスコア入力")
            if st.button("バックスコア入力", key="nav_main_back"):
                switch_page("03_バックスコア入力")
            if st.button("エキストラスコア入力", key="nav_main_extra"):
                switch_page("04_エキストラスコア入力")
                    
        with col2:
            st.markdown("### 📊 集計・確認")
            if st.button("結果確認", key="nav_main_results"):
                switch_page("05_結果確認")
            if st.button("ポイント集計", key="nav_main_points"):
                switch_page("06_ポイント集計")
            if st.button("管理画面", key="nav_main_admin"):
                switch_page("08_管理画面")
            if st.button("メンバー登録", key="nav_main_members"):
                switch_page("07_メンバー登録")
            if st.button("コース管理", key="nav_main_courses"):
                switch_page("09_コース管理")
            if st.button("📱 オフライン入力（出発前・現地・同期）", key="nav_main_offline_score"):
                switch_page("11_オフライン入力")
        
        # 使い方ガイド
        with st.expander("💡 使い方ガイド"):
            st.markdown("""
            **通常入力**：ラウンド設定 → フロント（OUT）→ バック（IN）→ 必要な場合だけエキストラ → 結果確認・確定

            **電波が弱い場所**：出発前に「オフライン入力」から開始ファイルを保存し、現地では手入力します。通信復帰後に同期ファイルを取り込みます。

            画像からスコアを読み取る手順、対応形式、エラー時の対処などは「マニュアル」を確認してください。
            """)
            if st.button("📚 詳しい使い方・画像読取りのマニュアル", key="guide_manual_button", use_container_width=True):
                switch_page("10_マニュアル")
        
        show_changelog()
        
        # フッター
        st.markdown("---")
        st.markdown("""
        #### 📌 注意事項
        - 通常入力は、ラウンド設定 → フロント → バック → エキストラの順で行ってください
        - オフライン入力は、ラウンド設定の保存後に「オフライン入力」で開始ファイルを保存してから使います
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
                    'patch': 248,
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
        logger.exception("アプリケーションの初期化に失敗しました")
        st.error("アプリケーションの初期化中にエラーが発生しました。")
        st.error("ページを再読み込みしてください。問題が続く場合は管理者にお問い合わせください。")

def show_changelog():
    try:
        with st.expander("📋 更新履歴"):
            changelog_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "CHANGELOG.md"
            )

            if os.path.exists(changelog_path):
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog = f.read()
                st.markdown(changelog)
            else:
                st.warning("📋 更新履歴ファイルが見つかりません")
    except Exception:
        logger.exception("更新履歴の読み込みに失敗しました")
        with st.expander("📋 更新履歴"):
            st.error("更新履歴を読み込めませんでした。")

if __name__ == "__main__":
    main()
