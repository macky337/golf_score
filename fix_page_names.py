import os
import re

# ページディレクトリのパス
pages_dir = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\pages"

# ファイル名の修正を行う関数
def fix_page_filenames():
    """ページファイル名の問題を修正する"""
    print("ページファイル名を修正しています...")
    
    # ディレクトリ内のすべてのPythonファイルを取得
    files = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
    
    # ファイル名の問題を修正
    for filename in files:
        # スペースを含むファイル名を修正
        if ' ' in filename:
            new_filename = filename.replace(' ', '_')
            old_path = os.path.join(pages_dir, filename)
            new_path = os.path.join(pages_dir, new_filename)
            
            try:
                os.rename(old_path, new_path)
                print(f"名前変更: {filename} → {new_filename}")
            except Exception as e:
                print(f"名前変更エラー: {filename} - {e}")

    print("\nページファイル名の修正が完了しました。")

if __name__ == "__main__":
    fix_page_filenames()
