import os
import shutil

# 管理ツール用のフォルダを作成
admin_folder = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\admin_tools"
os.makedirs(admin_folder, exist_ok=True)

# 移動対象のファイル
files_to_move = [
    "fix_database.py",
    "db_schema_check.py",
    "fix_security.py",
    "fix_security_simple.py",
    "test_data_save.py"
]

# SQLファイルの移動先フォルダを作成
sql_folder = os.path.join(admin_folder, "sql")
os.makedirs(sql_folder, exist_ok=True)

# ファイルを移動
for file in files_to_move:
    source = f"c:\\Users\\user\\Documents\\GitHub\\golf_score\\{file}"
    destination = os.path.join(admin_folder, file)
    
    if os.path.exists(source):
        shutil.move(source, destination)
        print(f"移動: {file} → admin_tools/{file}")
    else:
        print(f"ファイルが見つかりません: {file}")

# SQLファイルの移動
sql_files = ["fix_security.sql", "fix_rls_policy.sql", "disable_rls.sql"]
for file in sql_files:
    source = f"c:\\Users\\user\\Documents\\GitHub\\golf_score\\sql\\{file}"
    destination = os.path.join(sql_folder, file)
    
    if os.path.exists(source):
        shutil.move(source, destination)
        print(f"移動: sql/{file} → admin_tools/sql/{file}")
    else:
        print(f"ファイルが見つかりません: sql/{file}")

print("\n管理用ファイルの整理が完了しました。")
