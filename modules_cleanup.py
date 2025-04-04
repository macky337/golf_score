import os
import shutil

# setup_db.pyを管理ツールフォルダに移動
source = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\modules\\setup_db.py"
destination = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\admin_tools\\setup_db.py"

if os.path.exists(source):
    shutil.move(source, destination)
    print(f"移動: modules/setup_db.py → admin_tools/setup_db.py")
else:
    print(f"ファイルが見つかりません: {source}")

print("\nモジュールの整理が完了しました。")
