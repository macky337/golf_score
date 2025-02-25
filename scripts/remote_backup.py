import sqlite3
import json
from datetime import datetime
import os

def create_backup_from_remote_sqlite():
    """リモートmainのSQLiteデータベースからバックアップを作成"""
    backup_data = {
        'rounds': [],
        'scores': [],
        'members': [],
        'handicap_matches': []
    }
    
    # SQLiteデータベースに接続
    conn = sqlite3.connect('golf_scores.db')
    cursor = conn.cursor()
    
    # スコアデータの取得（game_ptを含む）
    cursor.execute('''
        SELECT score_id, round_id, member_id, 
               front_score, back_score, extra_score,
               front_putt, back_putt, extra_putt,
               front_game_pt, back_game_pt, extra_game_pt
        FROM scores
    ''')
    scores = cursor.fetchall()
    
    for s in scores:
        backup_data['scores'].append({
            'score_id': s[0],
            'round_id': s[1],
            'member_id': s[2],
            'front_score': s[3],
            'back_score': s[4],
            'extra_score': s[5],
            'front_putt': s[6],
            'back_putt': s[7],
            'extra_putt': s[8],
            'front_game_pt': s[9],
            'back_game_pt': s[10],
            'extra_game_pt': s[11]
        })
    
    # ラウンドデータの取得
    cursor.execute('SELECT * FROM rounds')
    rounds = cursor.fetchall()
    
    for r in rounds:
        backup_data['rounds'].append({
            'round_id': r[0],
            'date_played': r[1],
            'course_name': r[2],
            'has_extra': bool(r[3]),
            'finalized': bool(r[4])
        })

    # バックアップファイルの保存
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{backup_dir}/remote_main_backup_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    conn.close()
    return filename