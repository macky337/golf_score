import os

# 重複ファイルのリスト
duplicate_files = [
    "pages/05_エキストラスコア入力.py",  # 04_エキストラスコア入力.pyの重複
    "pages/06_結果確認.py"               # 05_結果確認.pyの重複
]

# 各ファイルを削除
for file_path in duplicate_files:
    full_path = os.path.join("c:\\Users\\user\\Documents\\GitHub\\golf_score", file_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
            print(f"削除成功: {file_path}")
        except Exception as e:
            print(f"削除失敗: {file_path} - エラー: {e}")
    else:
        print(f"ファイルなし: {file_path}")

print("\n重複ファイルの整理が完了しました。")
