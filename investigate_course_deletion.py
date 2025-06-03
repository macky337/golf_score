#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.supabase_client import get_supabase_client

def investigate_course_deletion_issue():
    """Sample Golf Club (ID: 7) の削除阻害要因を詳細調査"""
    
    try:
        supabase = get_supabase_client()
        course_id = 7
        course_name = "Sample Golf Club"
        
        print(f"=== {course_name} (ID: {course_id}) の削除阻害要因調査 ===\n")
        
        # 1. コースの存在確認
        print("1. コースの存在確認:")
        try:
            course_result = supabase.table('courses').select('*').eq('id', course_id).execute()
            if course_result.data:
                course = course_result.data[0]
                print(f"   ✓ コースが存在します: {course}")
            else:
                print(f"   ✗ ID {course_id} のコースが見つかりません")
                return
        except Exception as e:
            print(f"   ✗ coursesテーブルのアクセスエラー: {e}")
            # 代替テーブル名を試行
            try:
                course_result = supabase.table('course').select('*').eq('id', course_id).execute()
                if course_result.data:
                    course = course_result.data[0]
                    print(f"   ✓ コースが存在します (courseテーブル): {course}")
                else:
                    print(f"   ✗ ID {course_id} のコースが見つかりません (courseテーブル)")
                    return
            except Exception as e2:
                print(f"   ✗ courseテーブルのアクセスエラー: {e2}")
                return
        print()
        
        # 2. rounds/roundテーブルでの使用確認
        print("2. ラウンドテーブルでの使用状況:")
        try:
            # roundsテーブルを試行
            rounds_result = supabase.table('rounds').select('id, date, course_id').eq('course_id', course_id).execute()
            rounds = rounds_result.data
            table_name = 'rounds'
        except Exception:
            try:
                # roundテーブルを試行
                rounds_result = supabase.table('round').select('id, date, course_id').eq('course_id', course_id).execute()
                rounds = rounds_result.data
                table_name = 'round'
            except Exception as e:
                print(f"   ✗ ラウンドテーブルのアクセスエラー: {e}")
                rounds = []
                table_name = 'unknown'
        
        if rounds:
            print(f"   ✗ {table_name}テーブルで {len(rounds)} 件のラウンドが使用中")
            for i, round_data in enumerate(rounds[:5]):  # 最初の5件だけ表示
                print(f"   - ラウンドID: {round_data.get('id')}, 日付: {round_data.get('date')}")
            if len(rounds) > 5:
                print(f"   ... 他 {len(rounds) - 5} 件")
        else:
            print(f"   ✓ {table_name}テーブルでは使用されていません")
        print()
        
        # 3. scoreテーブルでの間接的使用確認
        print("3. スコアテーブルでの間接的使用状況:")
        try:
            # ラウンドIDのリストを取得
            round_ids = [r.get('id') for r in rounds] if rounds else []
            
            if round_ids:
                # スコアテーブルでこれらのラウンドIDが使用されているか確認
                score_result = supabase.table('score').select('player_id, round_id').in_('round_id', round_ids).execute()
                scores = score_result.data
                
                if scores:
                    print(f"   ✗ scoreテーブルで {len(scores)} 件のスコア記録が存在")
                    # プレイヤー別の集計
                    player_counts = {}
                    for score in scores:
                        player_id = score.get('player_id')
                        player_counts[player_id] = player_counts.get(player_id, 0) + 1
                    
                    print(f"   関連するプレイヤー数: {len(player_counts)} 名")
                    for player_id, count in list(player_counts.items())[:5]:
                        print(f"   - プレイヤーID {player_id}: {count} 件のスコア")
                    if len(player_counts) > 5:
                        print(f"   ... 他 {len(player_counts) - 5} 名")
                else:
                    print("   ✓ 関連するスコア記録はありません")
            else:
                print("   ✓ 確認対象のラウンドがないため、スコア記録もありません")
        except Exception as e:
            print(f"   ✗ スコアテーブルのアクセスエラー: {e}")
        print()
        
        # 4. その他のテーブルでの使用確認
        print("4. その他のテーブルでの使用確認:")
        other_tables = ['round_results', 'handicap_match']
        
        for table in other_tables:
            try:
                # course_idカラムがあるかチェック
                result = supabase.table(table).select('*').limit(1).execute()
                if result.data and 'course_id' in result.data[0]:
                    # course_idで検索
                    usage_result = supabase.table(table).select('*').eq('course_id', course_id).execute()
                    if usage_result.data:
                        print(f"   ✗ {table}テーブルで {len(usage_result.data)} 件の記録が存在")
                    else:
                        print(f"   ✓ {table}テーブルでは使用されていません")
                else:
                    print(f"   - {table}テーブルにはcourse_idカラムがありません")
            except Exception as e:
                print(f"   - {table}テーブルのチェックでエラー: {e}")
        print()
        
        # 5. 削除の試行シミュレーション
        print("5. 削除可能性の確認:")
        if rounds:
            print(f"   ✗ 削除不可能: {len(rounds)} 件のラウンドで使用中")
            print("   解決方法:")
            print("   1. 関連するスコア記録を削除")
            print("   2. 関連するラウンド記録を削除")
            print("   3. 最後にコース記録を削除")
            print("   ⚠️  注意: この操作により関連データが完全に失われます")
        else:
            print("   ✓ 削除可能: 依存関係がありません")
        print()
        
        # 6. 解決策スクリプトの提案
        if rounds:
            print("6. 自動削除スクリプトの生成:")
            print("   以下のコマンドで関連データを含めて削除できます:")
            print(f"   python delete_course_with_dependencies.py {course_id}")
            
            # 削除スクリプトを生成
            create_deletion_script(course_id, course_name, rounds)
        
    except Exception as e:
        print(f"調査中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

def create_deletion_script(course_id, course_name, rounds):
    """コースとその依存関係を削除するスクリプトを生成"""
    
    script_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{course_name} (ID: {course_id}) とその依存関係を削除するスクリプト

⚠️ 警告: このスクリプトを実行すると、以下のデータが完全に削除されます:
- ラウンド記録: {len(rounds)} 件
- 関連するスコア記録: すべて
- コース記録: 1 件

実行前に必ずバックアップを取ってください。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.supabase_client import get_supabase_client

def delete_course_with_dependencies():
    course_id = {course_id}
    course_name = "{course_name}"
    
    print(f"=== {{course_name}} (ID: {{course_id}}) の削除処理開始 ===\\n")
    
    try:
        supabase = get_supabase_client()
        
        # 1. 確認プロンプト
        print("⚠️  この操作により以下のデータが削除されます:")
        print(f"- コース: {{course_name}} (ID: {{course_id}})")
        print(f"- ラウンド記録: {len(rounds)} 件")
        print("- 関連するすべてのスコア記録")
        print()
        
        confirm = input("本当に削除しますか？ (yes/no): ")
        if confirm.lower() != 'yes':
            print("削除がキャンセルされました。")
            return
        
        # 2. 依存関係の取得
        print("\\n1. 依存関係の確認...")
        
        # ラウンドIDの取得
        try:
            rounds_result = supabase.table('rounds').select('id').eq('course_id', course_id).execute()
            round_ids = [r['id'] for r in rounds_result.data]
        except:
            rounds_result = supabase.table('round').select('id').eq('course_id', course_id).execute()
            round_ids = [r['id'] for r in rounds_result.data]
        
        print(f"削除対象ラウンド: {{len(round_ids)}} 件")
        
        # 3. スコア記録の削除
        print("\\n2. スコア記録の削除...")
        if round_ids:
            score_result = supabase.table('score').delete().in_('round_id', round_ids).execute()
            print(f"削除されたスコア記録: {{len(score_result.data)}} 件")
        
        # 4. ラウンド記録の削除
        print("\\n3. ラウンド記録の削除...")
        try:
            round_result = supabase.table('rounds').delete().eq('course_id', course_id).execute()
        except:
            round_result = supabase.table('round').delete().eq('course_id', course_id).execute()
        print(f"削除されたラウンド記録: {{len(round_result.data)}} 件")
        
        # 5. コース記録の削除
        print("\\n4. コース記録の削除...")
        try:
            course_result = supabase.table('courses').delete().eq('id', course_id).execute()
        except:
            course_result = supabase.table('course').delete().eq('id', course_id).execute()
        print(f"削除されたコース記録: {{len(course_result.data)}} 件")
        
        print(f"\\n✅ {{course_name}} (ID: {{course_id}}) の削除が完了しました。")
        
    except Exception as e:
        print(f"\\n❌ 削除処理中にエラーが発生しました: {{e}}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    delete_course_with_dependencies()
'''
    
    with open('delete_course_with_dependencies.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"   ✓ 削除スクリプトを生成しました: delete_course_with_dependencies.py")

if __name__ == "__main__":
    investigate_course_deletion_issue()
