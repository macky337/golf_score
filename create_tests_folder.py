import os
import shutil

# テスト用のフォルダを作成
tests_folder = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\tests"
os.makedirs(tests_folder, exist_ok=True)

# モジュール内のテストファイルを移動
source = "c:\\Users\\user\\Documents\\GitHub\\golf_score\\modules\\test_game_point_logic.py"
destination = os.path.join(tests_folder, "test_game_point_logic.py")

if os.path.exists(source):
    shutil.copy(source, destination)  # コピーのみ（元ファイルも必要かもしれないため）
    print(f"コピー: modules/test_game_point_logic.py → tests/test_game_point_logic.py")
else:
    print(f"ファイルが見つかりません: {source}")

print("\nテストファイルの整理が完了しました。")
