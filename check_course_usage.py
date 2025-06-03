#!/usr/bin/env python3
"""
特定のコース（Sample Golf Club, ID: 7）の使用状況を調査するスクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase

def check_course_usage(course_id=7, course_name="Sample Golf Club"):
    """指定されたコースの使用状況を調査"""
    print(f"=== コース使用状況調査: {course_name} (ID: {course_id}) ===\n")
    
    usage_found = False
    
    # 1. roundsテーブルでの使用確認
    try:
        rounds_result = supabase.table('rounds').select('round_id, date_played, course_name, course_id').eq('course_id', course_id).execute()
        if rounds_result.data:
            usage_found = True
            print(f"📅 roundsテーブルで使用されています ({len(rounds_result.data)}件):")
            for round_data in rounds_result.data:
                print(f"  - ラウンドID: {round_data['round_id']}, 日付: {round_data.get('date_played', '不明')}")
        else:
            print("📅 roundsテーブル: 使用されていません")
    except Exception as e:
        print(f"📅 roundsテーブル確認エラー: {e}")
    
    print()
    
    # 2. scoreテーブルでの間接的な使用確認（roundsを経由）
    try:
        score_query = """
        SELECT DISTINCT s.round_id, r.date_played, r.course_name
        FROM score s 
        JOIN rounds r ON s.round_id = r.round_id 
        WHERE r.course_id = %s
        ORDER BY r.date_played DESC
        """
        
        # Supabaseでは直接SQLを実行できないため、別の方法で確認
        all_rounds = supabase.table('rounds').select('round_id, date_played, course_name').eq('course_id', course_id).execute()
        if all_rounds.data:
            round_ids = [r['round_id'] for r in all_rounds.data]
            score_usage = []
            
            for round_id in round_ids:
                score_result = supabase.table('score').select('score_id, member_id').eq('round_id', round_id).execute()
                if score_result.data:
                    score_usage.extend(score_result.data)
            
            if score_usage:
                usage_found = True
                print(f"🎯 scoreテーブルで間接的に使用されています ({len(score_usage)}件のスコア記録):")
                for round_data in all_rounds.data:
                    round_scores = [s for s in score_usage if s.get('round_id') == round_data['round_id']]
                    if round_scores:
                        print(f"  - ラウンド{round_data['round_id']} ({round_data.get('date_played', '不明')}): {len(round_scores)}件のスコア")
            else:
                print("🎯 scoreテーブル: 間接的な使用もありません")
        else:
            print("🎯 scoreテーブル: 関連するラウンドがありません")
    except Exception as e:
        print(f"🎯 scoreテーブル確認エラー: {e}")
    
    print()
    
    # 3. round_resultsテーブルでの間接的な使用確認
    try:
        all_rounds = supabase.table('rounds').select('round_id, date_played').eq('course_id', course_id).execute()
        if all_rounds.data:
            round_ids = [r['round_id'] for r in all_rounds.data]
            round_results_usage = []
            
            for round_id in round_ids:
                result = supabase.table('round_results').select('*').eq('round_id', round_id).execute()
                if result.data:
                    round_results_usage.extend(result.data)
            
            if round_results_usage:
                usage_found = True
                print(f"📊 round_resultsテーブルで間接的に使用されています ({len(round_results_usage)}件):")
                for round_data in all_rounds.data:
                    round_results = [r for r in round_results_usage if r.get('round_id') == round_data['round_id']]
                    if round_results:
                        print(f"  - ラウンド{round_data['round_id']} ({round_data.get('date_played', '不明')}): {len(round_results)}件の結果")
            else:
                print("📊 round_resultsテーブル: 間接的な使用もありません")
    except Exception as e:
        print(f"📊 round_resultsテーブル確認エラー: {e}")
    
    print()
    
    # 4. handicap_matchテーブルでの間接的な使用確認
    try:
        all_rounds = supabase.table('rounds').select('round_id, date_played').eq('course_id', course_id).execute()
        if all_rounds.data:
            round_ids = [r['round_id'] for r in all_rounds.data]
            handicap_usage = []
            
            for round_id in round_ids:
                result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
                if result.data:
                    handicap_usage.extend(result.data)
            
            if handicap_usage:
                usage_found = True
                print(f"🎲 handicap_matchテーブルで間接的に使用されています ({len(handicap_usage)}件):")
                for round_data in all_rounds.data:
                    handicaps = [h for h in handicap_usage if h.get('round_id') == round_data['round_id']]
                    if handicaps:
                        print(f"  - ラウンド{round_data['round_id']} ({round_data.get('date_played', '不明')}): {len(handicaps)}件のハンディキャップ")
            else:
                print("🎲 handicap_matchテーブル: 間接的な使用もありません")
    except Exception as e:
        print(f"🎲 handicap_matchテーブル確認エラー: {e}")
    
    print()
    
    # 5. コース情報の確認
    try:
        course_result = supabase.table('courses').select('*').eq('course_id', course_id).execute()
        if course_result.data:
            course_info = course_result.data[0]
            print("📋 コース情報:")
            for key, value in course_info.items():
                print(f"  {key}: {value}")
        else:
            print("📋 コース情報: 見つかりませんでした")
    except Exception as e:
        print(f"📋 コース情報確認エラー: {e}")
    
    print("\n" + "="*60)
    
    if usage_found:
        print("❌ このコースは削除できません。")
        print("💡 削除するには、関連するラウンドデータを先に削除するか、")
        print("   管理画面の「ラウンド削除」機能を使用してください。")
        
        # 削除手順の提案
        print("\n🔧 削除手順の提案:")
        print("1. 管理画面 → スコア修正タブ")
        print("2. 削除したいラウンドを選択")
        print("3. 「ラウンドの削除」展開メニューから削除")
        print("4. すべての関連ラウンドを削除後、コース管理でコースを削除")
    else:
        print("✅ このコースは使用されていないため、削除可能です。")
        print("💡 コース管理画面から安全に削除できます。")

if __name__ == "__main__":
    check_course_usage()
