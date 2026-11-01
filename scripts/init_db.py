# scripts/init_db.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_db():
    """現行スキーマの案内を表示する。"""
    print("Supabase SQL Editorで init_supabase_tables.sql を実行してください。")
    print("既存環境には初期化SQLではなく sql/ 配下の個別マイグレーションを使用してください。")

if __name__ == "__main__":
    init_db()
