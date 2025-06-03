#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Golf Club (ID: 7) 即座削除スクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase

def delete_course_immediately():
    """Sample Golf Club (ID: 7) を即座に削除"""
    
    course_id = 7
    
    print("🚀 Sample Golf Club (ID: 7) 削除実行")
    print("=" * 40)
    
    try:
        # 確認なしで削除実行
        print("1. 関連スコア削除中...")
        scores_result = supabase.table('score').delete().eq('course_id', course_id).execute()
        print(f"   削除されたスコア: {len(scores_result.data) if scores_result.data else 0}件")
        
        print("2. 関連ラウンド削除中...")
        # まず round_results を削除
        rounds_to_delete = supabase.table('rounds').select('round_id').eq('course_id', course_id).execute()
        if rounds_to_delete.data:
            for round_data in rounds_to_delete.data:
                round_id = round_data.get('round_id')
                supabase.table('round_results').delete().eq('round_id', round_id).execute()
        # その後 rounds を削除
        rounds_result = supabase.table('rounds').delete().eq('course_id', course_id).execute()
        print(f"   削除されたラウンド: {len(rounds_result.data) if rounds_result.data else 0}件")
        
        print("3. コース削除中...")
        course_result = supabase.table('courses').delete().eq('course_id', course_id).execute()
        print(f"   削除されたコース: {len(course_result.data) if course_result.data else 0}件")
        
        print("\n✅ 削除完了!")
        print("✅ Sample Golf Club (ID: 7) およびすべての関連データが削除されました")
        
        # 削除確認
        print("\n🔍 削除確認...")
        verify_result = supabase.table('courses').select('*').eq('course_id', course_id).execute()
        if not verify_result.data:
            print("✅ コースが正常に削除されました")
        else:
            print("❌ コースがまだ存在しています")
        
        return True
        
    except Exception as e:
        print(f"❌ 削除エラー: {str(e)}")
        return False

if __name__ == "__main__":
    print("⚠️ これによりSample Golf Club (ID: 7)とすべての関連データが削除されます")
    
    # 自動実行（3秒待機）
    import time
    for i in range(3, 0, -1):
        print(f"削除まであと {i} 秒...")
        time.sleep(1)
    
    print("\n🚀 削除開始...")
    result = delete_course_immediately()
    
    if result:
        print("\n🎉 削除処理が正常に完了しました!")
        print("💡 管理画面でコース管理を確認してください")
    else:
        print("\n❌ 削除処理に失敗しました")
