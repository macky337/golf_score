#!/usr/bin/env python3
"""簡単なインポートテスト"""

try:
    import os
    import sys
    from dotenv import load_dotenv
    
    # 環境変数を読み込み
    load_dotenv()
    
    # モジュールパスを追加
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    print("基本インポート成功")
    
    # Supabase接続をテスト
    from modules.db import supabase
    print("Supabase接続成功")
    
    # Round 53の基本情報を取得
    rounds = supabase.table('rounds').select('id, course_name, date').eq('id', 53).execute()
    if rounds.data:
        round_data = rounds.data[0]
        print(f"Round 53 found: {round_data['course_name']} on {round_data['date']}")
    else:
        print("Round 53 not found")
    
    print("簡単テスト完了")
    
except Exception as e:
    print(f"エラー: {e}")
    import traceback
    traceback.print_exc()
