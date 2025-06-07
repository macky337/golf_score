import os

# 直接削除を試みる
pages_dir = r"c:\Users\user\Documents\GitHub\golf_score\pages"

# 削除対象ファイル
files_to_remove = [
    "06_結果確認.py",
    "07_ポイント集計.py"
]

for filename in files_to_remove:
    filepath = os.path.join(pages_dir, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"削除成功: {filename}")
        except Exception as e:
            print(f"削除失敗: {filename} - {e}")
    else:
        print(f"ファイルが見つかりません: {filename}")

# 削除後のディレクトリ内容を確認
print("\n削除後のページファイル一覧:")
for file in sorted(os.listdir(pages_dir)):
    if file.endswith('.py'):
        print(f"  {file}")
