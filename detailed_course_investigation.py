#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db_connection import get_db_connection

def investigate_course_usage():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    course_id = 7
    course_name = "Sample Golf Club"
    
    print(f"=== {course_name} (ID: {course_id}) の削除阻害要因調査 ===\n")
    
    # 1. roundテーブルでの使用確認
    print("1. roundテーブルでの使用状況:")
    cursor.execute("SELECT id, date, course_id FROM round WHERE course_id = ?", (course_id,))
    rounds = cursor.fetchall()
    if rounds:
        print(f"   使用されているラウンド数: {len(rounds)}件")
        for round_data in rounds[:5]:  # 最初の5件だけ表示
            print(f"   - ラウンドID: {round_data[0]}, 日付: {round_data[1]}, コースID: {round_data[2]}")
        if len(rounds) > 5:
            print(f"   ... 他 {len(rounds) - 5} 件")
    else:
        print("   使用されていません")
    print()
    
    # 2. scoreテーブルでの間接的使用確認
    print("2. scoreテーブルでの間接的使用状況:")
    cursor.execute("""
        SELECT COUNT(*) FROM score 
        WHERE round_id IN (SELECT id FROM round WHERE course_id = ?)
    """, (course_id,))
    score_count = cursor.fetchone()[0]
    if score_count > 0:
        print(f"   関連するスコア記録数: {score_count}件")
        
        # どのプレイヤーのスコアがあるか確認
        cursor.execute("""
            SELECT DISTINCT s.player_id, p.name 
            FROM score s 
            JOIN player p ON s.player_id = p.id
            WHERE s.round_id IN (SELECT id FROM round WHERE course_id = ?)
        """, (course_id,))
        players = cursor.fetchall()
        print(f"   関連するプレイヤー数: {len(players)}名")
        for player in players[:5]:  # 最初の5名だけ表示
            print(f"   - プレイヤーID: {player[0]}, 名前: {player[1]}")
        if len(players) > 5:
            print(f"   ... 他 {len(players) - 5} 名")
    else:
        print("   関連するスコア記録はありません")
    print()
    
    # 3. 外部キー制約の確認
    print("3. 外部キー制約の確認:")
    cursor.execute("PRAGMA foreign_key_list(round)")
    fk_constraints = cursor.fetchall()
    for constraint in fk_constraints:
        if constraint[2] == 'course':  # course テーブルへの参照
            print(f"   roundテーブル -> courseテーブル: {constraint}")
    print()
    
    # 4. データベースの外部キー設定確認
    print("4. 外部キー制約の有効状況:")
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    print(f"   外部キー制約: {'有効' if fk_enabled else '無効'}")
    print()
    
    # 5. courseテーブルの現在の状態確認
    print("5. courseテーブルの現在の状態:")
    cursor.execute("SELECT id, name FROM course ORDER BY id")
    courses = cursor.fetchall()
    print(f"   登録されているコース数: {len(courses)}件")
    for course in courses:
        status = " ← 削除対象" if course[0] == course_id else ""
        print(f"   - ID: {course[0]}, 名前: {course[1]}{status}")
    print()
    
    # 6. 削除試行のシミュレーション
    print("6. 削除可能性の確認:")
    try:
        # トランザクション開始
        cursor.execute("BEGIN")
        
        # 削除試行（実際には実行しない）
        cursor.execute("DELETE FROM course WHERE id = ?", (course_id,))
        affected_rows = cursor.rowcount
        
        # ロールバック
        cursor.execute("ROLLBACK")
        
        print(f"   削除可能: はい（影響行数: {affected_rows}）")
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        print(f"   削除可能: いいえ")
        print(f"   エラー: {str(e)}")
    print()
    
    # 7. 解決策の提案
    print("7. 解決策の提案:")
    if rounds:
        print(f"   ✗ このコースは {len(rounds)} 件のラウンドで使用されています")
        print(f"   ✗ 関連する {score_count} 件のスコア記録があります")
        print("   推奨解決策:")
        print("   1. 関連するスコア記録を先に削除する")
        print("   2. 関連するラウンド記録を削除する")
        print("   3. 最後にコース記録を削除する")
        print("   または:")
        print("   4. カスケード削除を設定する（注意：データが完全に失われます）")
    else:
        print("   ✓ このコースは使用されていないため、削除可能です")
    
    conn.close()

if __name__ == "__main__":
    investigate_course_usage()
