#!/usr/bin/env python3
"""
モジュールインポートテスト
"""
import sys
import os

# プロジェクトルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

print(f"プロジェクトルート: {project_root}")
print(f"Pythonパス: {sys.path}")

try:
    from modules.db import supabase
    print("✅ modules.db インポート成功")
except ImportError as e:
    print(f"❌ modules.db インポートエラー: {e}")

try:
    from modules.models import get_members_list
    print("✅ modules.models インポート成功")
except ImportError as e:
    print(f"❌ modules.models インポートエラー: {e}")

try:
    from modules.calculation_logic import calculate_player_points
    print("✅ modules.calculation_logic インポート成功")
except ImportError as e:
    print(f"❌ modules.calculation_logic インポートエラー: {e}")

try:
    from modules.round_results import save_round_results, get_round_results
    print("✅ modules.round_results インポート成功")
except ImportError as e:
    print(f"❌ modules.round_results インポートエラー: {e}")

print("\nモジュールインポートテスト完了")
