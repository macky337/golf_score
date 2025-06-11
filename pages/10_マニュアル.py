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
        if st.button("🏠 Home", key="manual_home_button"):
            switch_page("main")
    
    # マニュアルの内容を読み込んで表示
    try:
        # より堅牢なファイル検索（本番環境対応）
        possible_paths = [
            # 1. プロジェクトルートからの相対パス
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "マニュアル.md"),
            # 2. 現在の作業ディレクトリ
            os.path.join(os.getcwd(), "マニュアル.md"),
            # 3. 開発環境の絶対パス
            r"C:\Users\user\Documents\GitHub\golf_score\マニュアル.md",
            # 4. Railway環境の絶対パス
            "/app/マニュアル.md",
            # 5. 相対パス
            "マニュアル.md",
            # 6. 一つ上のディレクトリ
            os.path.join("..", "マニュアル.md"),
            # 7. スクリプトファイルと同じディレクトリ
            os.path.join(os.path.dirname(__file__), "マニュアル.md")
        ]
        
        manual_content = None
        used_path = None
        
        # デバッグ情報（開発時のみ）
        debug_mode = os.environ.get('STREAMLIT_DEBUG', 'false').lower() == 'true'
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding='utf-8') as f:
                        manual_content = f.read()
                    used_path = path
                    if debug_mode:
                        st.success(f"✅ マニュアルファイルを発見: {path}")
                    break
            except Exception as path_error:
                if debug_mode:
                    st.write(f"❌ パスエラー {path}: {path_error}")
                continue
        
        if manual_content:
            # マニュアル内容を表示
            st.markdown(manual_content)
            if debug_mode and used_path:
                st.info(f"📁 使用したパス: {used_path}")
        else:
            # フォールバック: ファイル検索
            st.warning("マニュアルファイルを検索中...")
            found_manual = search_manual_file()
            if found_manual:
                with open(found_manual, "r", encoding='utf-8') as f:
                    manual_content = f.read()
                st.markdown(manual_content)
                st.info(f"📁 発見したマニュアル: {found_manual}")
            else:
                raise FileNotFoundError("マニュアルファイルが見つかりませんでした")
            
    except Exception as e:
        st.error("マニュアルファイルが見つかりません。")
        
        # 緊急時フォールバック: ハードコードされたマニュアル内容を表示
        st.warning("フォールバックモード: 埋め込みマニュアルを表示します")
        display_embedded_manual()

def display_embedded_manual():
    """
    緊急時フォールバック用の埋め込みマニュアル
    """
    manual_content = """
# Golf Score App マニュアル

## 1. アプリケーションの概要
本アプリケーションは、ゴルフのスコア管理、マッチ戦の記録、ポイント集計を行うためのツールです。
ユーザーはメンバー登録、ラウンド設定、スコア入力などを行い、最終的な結果確認・PDF出力・ポイント集計を実施できます。

## 2. 基本的な使用手順

### 2.1. メンバー登録
1. メインメニューから「メンバー登録」を選択
2. メンバー名を入力
3. 「登録」ボタンをクリック

### 2.2. ラウンド設定
1. メインメニューから「ラウンド設定」を選択
2. 以下の項目を設定：
   - プレイ日付
   - ゴルフ場名（新規登録または既存コースから選択）
   - プレイ人数（3名または4名）
   - 参加メンバー
   - ハンディキャップの設定
   - マッチ方式（Total Only など）
3. 「保存」ボタンをクリックしてラウンド情報を登録

### 2.3. スコア入力
#### 2.3.1. フロントスコア入力
- 各ホールのスコア、パット数、ゲームポイントを入力
- ハンディ補正後のネットスコアが自動計算されます

#### 2.3.2. バックスコア入力  
- 各ホールのスコア、パット数、ゲームポイントを入力
- フロントスコアと合算してトータルスコアが計算されます

#### 2.3.3. エキストラスコア入力（必要な場合）
- 追加ホールのスコアを入力できます

### 2.4. 結果確認
- 入力したスコアの確認
- PDFでの出力
- マッチ戦の詳細結果表示

### 2.5. ポイント集計
- 全期間または指定期間のポイント集計
- ランキング表示
- グラフによる可視化

## 3. 注意事項
- スコアの入力は、ラウンド設定 → フロント → バック → エキストラの順で行ってください
- 入力したデータは「結果確認」画面で確認できます
- データの修正が必要な場合は「管理画面」をご利用ください

## 4. トラブルシューティング
問題が発生した場合は、画面を再読み込みしてください。
それでも解決しない場合は、管理者にお問い合わせください。
"""
    st.markdown(manual_content)
        
        # 詳細なデバッグ情報を表示
        with st.expander("🔧 デバッグ情報"):
            st.write(f"エラー: {e}")
            st.write(f"現在のディレクトリ: {os.getcwd()}")
            st.write(f"スクリプトディレクトリ: {os.path.dirname(__file__)}")
            st.write(f"プロジェクトルート: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
            
            # 利用可能なファイルを検索
            search_results = search_manual_file()
            if search_results:
                st.write(f"発見されたマニュアルファイル: {search_results}")
            else:
                st.write("マニュアルファイルが見つかりませんでした")

def search_manual_file():
    """
    マニュアルファイルを再帰的に検索する
    """
    search_dirs = [
        os.getcwd(),
        os.path.dirname(__file__),
        os.path.dirname(os.path.dirname(__file__)),
        "/app" if os.path.exists("/app") else None
    ]
    
    for search_dir in search_dirs:
        if search_dir is None:
            continue
        try:
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if "マニュアル" in file and file.endswith('.md'):
                        return os.path.join(root, file)
        except Exception:
            continue
    return None

if __name__ == "__main__":
    run()
else:
    # Streamlit Pages用の直接実行
    run()