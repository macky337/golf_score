#!/usr/bin/env python3
"""Sample Golf Club (ID: 7) 削除の影響を迅速に確認"""

import os
from supabase import create_client

def check_deletion_impact():
    """削除の影響を迅速にチェック"""
    try:
        # Supabase接続
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')  # SUPABASE_ANON_KEY から修正
        
        if not url or not key:
            print("❌ 環境変数が設定されていません")
            return
            
        supabase = create_client(url, key)
        
        print("🔍 Sample Golf Club (ID: 7) 削除影響調査")
        print("=" * 50)
        
        # 1. コース情報確認
        course_result = supabase.table('courses').select('*').eq('id', 7).execute()
        if course_result.data:
            course = course_result.data[0]
            print(f"📍 コース名: {course['name']}")
            print(f"📍 コースID: {course['id']}")
        else:
            print("❌ コースが見つかりません")
            return
        
        # 2. ラウンド数確認
        rounds_result = supabase.table('rounds').select('round_id, round_date, players(player_name)').eq('course_id', 7).execute()
        round_count = len(rounds_result.data) if rounds_result.data else 0
        print(f"🎯 関連ラウンド数: {round_count}件")
        
        if round_count > 0:
            print("\n📊 影響を受けるラウンド:")
            for round_data in rounds_result.data[:5]:  # 最初の5件表示
                player_name = round_data.get('players', {}).get('player_name', '不明') if round_data.get('players') else '不明'
                print(f"  - ラウンドID {round_data['round_id']}: {round_data['round_date']} ({player_name})")
            
            if round_count > 5:
                print(f"  ... 他 {round_count - 5}件")
        
        # 3. スコア数確認
        scores_result = supabase.table('score').select('score_id').eq('course_id', 7).execute()
        score_count = len(scores_result.data) if scores_result.data else 0
        print(f"📈 関連スコア数: {score_count}件")
        
        # 4. 削除の安全性評価
        print(f"\n⚠️ 削除影響評価:")
        if round_count == 0 and score_count == 0:
            print("✅ 安全: 関連データなし - 削除可能")
            risk_level = "低"
        elif round_count <= 5:
            print("⚠️ 注意: 少数の関連データあり - 慎重に削除")
            risk_level = "中"
        else:
            print("🚨 高リスク: 多数の関連データあり - 削除前にバックアップ推奨")
            risk_level = "高"
        
        print(f"🎯 リスクレベル: {risk_level}")
        
        # 5. 削除手順提示
        print(f"\n🔧 推奨削除手順:")
        if round_count > 0 or score_count > 0:
            print("1. データベースのバックアップ作成")
            print("2. 関連スコアデータの削除")
            print("3. 関連ラウンドデータの削除") 
            print("4. コースデータの削除")
            print("5. 削除確認とテスト")
        else:
            print("1. コースデータの直接削除")
            print("2. 削除確認")
        
        return {
            'course_exists': bool(course_result.data),
            'round_count': round_count,
            'score_count': score_count,
            'risk_level': risk_level
        }
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        return None

if __name__ == "__main__":
    result = check_deletion_impact()
    if result:
        print(f"\n📋 サマリー:")
        print(f"コース存在: {result['course_exists']}")
        print(f"ラウンド数: {result['round_count']}")
        print(f"スコア数: {result['score_count']}")
        print(f"リスクレベル: {result['risk_level']}")
