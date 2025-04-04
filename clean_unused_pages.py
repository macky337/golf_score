import os
import shutil

def remove_unused_pages():
    """不要なページファイルを削除する"""
    pages_dir = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\pages"
    
    # 削除対象のファイルリスト
    files_to_remove = [
        "09_スコアテーブル修復.py",
        "10_スコア再計算.py"
    ]
    
    # バックアップディレクトリ作成
    backup_dir = os.path.join("c:\\Users\\user\\Documents\\GitHub\\golf_score", "backup_pages")
    os.makedirs(backup_dir, exist_ok=True)
    
    # 各ファイルについて処理
    for file_name in files_to_remove:
        file_path = os.path.join(pages_dir, file_name)
        
        if os.path.exists(file_path):
            try:
                # バックアップを取得
                backup_path = os.path.join(backup_dir, file_name)
                shutil.copy2(file_path, backup_path)
                print(f"バックアップを作成: {backup_path}")
                
                # ファイルを削除
                os.remove(file_path)
                print(f"削除しました: {file_name}")
            except Exception as e:
                print(f"エラー ({file_name}): {str(e)}")
        else:
            print(f"ファイルが見つかりません: {file_name}")
    
    print("\n不要なページの整理が完了しました。")

if __name__ == "__main__":
    print("不要なページファイルを削除します...")
    remove_unused_pages()
