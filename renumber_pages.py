import os
import re

# ページファイルのパス
pages_dir = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\pages"

# ページファイルの定義（正しい順序）
page_definitions = [
    {"name": "ラウンド設定", "old_prefix": "01"},
    {"name": "フロントスコア入力", "old_prefix": "02"},
    {"name": "バックスコア入力", "old_prefix": "03"},
    {"name": "エキストラスコア入力", "old_prefix": "04"},
    {"name": "結果確認", "old_prefix": "05"}
]

# ディレクトリ内のファイルを取得
files = [f for f in os.listdir(pages_dir) if os.path.isfile(os.path.join(pages_dir, f)) and f.endswith(".py")]

print("ファイル番号を整理しています...")

# 各ファイルの名前を振り直す
for i, page in enumerate(page_definitions, 1):
    old_name = f"{page['old_prefix']}_{page['name']}.py"
    new_name = f"{i:02d}_{page['name']}.py"
    
    old_path = os.path.join(pages_dir, old_name)
    new_path = os.path.join(pages_dir, new_name)
    
    if os.path.exists(old_path) and old_name != new_name:
        try:
            os.rename(old_path, new_path)
            print(f"名前変更: {old_name} → {new_name}")
        except Exception as e:
            print(f"名前変更エラー: {old_name} - {e}")

print("\nファイル番号の整理が完了しました。")
