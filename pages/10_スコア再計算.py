import streamlit as st
import time
from modules.recalculate_scores import recalculate_all_rounds

def run():
    st.title("スコア再計算ツール")
    st.write("""
    このツールは、復元されたSupabaseのscoreテーブルから、全てのスコアデータを再計算します。
    ゲームポイント（既存のデータを保持）をベースに、以下を再計算します：
    - マッチポイント（フロント、バック、トータル、エキストラ）
    - パットポイント
    - トータルポイント
    """)
    
    st.warning("⚠️ この操作を実行すると、全てのラウンドのスコアデータが再計算されます。")
    
    # 処理ステータスを表示するための領域
    status_area = st.empty()
    progress_bar = st.progress(0.0)
    log_area = st.empty()
    
    logs = []
    
    def update_status(message):
        logs.append(message)
        log_area.code("\n".join(logs))
    
    if st.button("スコアデータを再計算", type="primary"):
        status_area.info("再計算を開始しています...")
        
        # ラウンド情報を取得して総数を確認
        try:
            report = recalculate_all_rounds(update_status)
            
            # 処理完了後の表示
            status_area.success("再計算が完了しました")
            progress_bar.progress(1.0)
            st.write("### 処理結果")
            st.code(report)
            st.balloons()
            
        except Exception as e:
            status_area.error(f"エラーが発生しました: {str(e)}")
            st.error(f"詳細: {e}")

if __name__ == "__main__":
    run()