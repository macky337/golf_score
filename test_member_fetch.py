#!/usr/bin/env python3
"""
メンバーデータ取得テスト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from modules.supabase_client import get_supabase_client
    print("✅ supabase_client インポート成功")
    
    supabase = get_supabase_client()
    if supabase:
        print("✅ Supabaseクライアント取得成功")
        
        # メンバーテーブルから直接取得（正しい環境変数使用）
        result = supabase.table('member').select('*').order('member_id').execute()
        print(f"✅ メンバーデータ取得成功: {len(result.data)}件")
        for member in result.data:
            print(f"  - ID: {member['member_id']}, 名前: {member['name']}")
    else:
        print("❌ Supabaseクライアント取得失敗")
        
except Exception as e:
    print(f"❌ エラー: {str(e)}")
    import traceback
    traceback.print_exc()

try:
    from modules.models import get_members_list
    print("\n✅ models.get_members_list インポート成功")
    
    # 修正後の関数をテスト
    members = get_members_list()
    print(f"get_members_list結果: {len(members)}件")
    if members:
        for member in members:
            print(f"  - ID: {member['member_id']}, 名前: {member['name']}")
    else:
        print("  メンバーデータが空です")
        
except Exception as e:
    print(f"❌ get_members_list エラー: {str(e)}")
    import traceback
    traceback.print_exc()
