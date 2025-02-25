import json
import os

def check_backup_data():
    """バックアップデータの内容を確認"""
    backup_dir = "backups"
    backup_files = [f for f in os.listdir(backup_dir) 
                   if f.startswith("remote_main_backup_") and f.endswith(".json")]
    
    if not backup_files:
        print("バックアップファイルが見つかりません")
        return
    
    latest_backup = max(backup_files)
    backup_path = os.path.join(backup_dir, latest_backup)
    
    print(f"バックアップファイル: {backup_path}")
    
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    # game_ptの値が0以外のデータを確認
    non_zero_scores = [
        score for score in backup_data['scores']
        if score['front_game_pt'] != 0 or 
           score['back_game_pt'] != 0 or 
           score['extra_game_pt'] != 0
    ]
    
    if non_zero_scores:
        print("\ngame_ptが0以外のスコア:")
        for score in non_zero_scores:
            print(f"\nスコアID: {score['score_id']}")
            print(f"front_game_pt: {score['front_game_pt']}")
            print(f"back_game_pt: {score['back_game_pt']}")
            print(f"extra_game_pt: {score['extra_game_pt']}")
    else:
        print("\n全てのgame_ptが0になっています")
        print("バックアップデータのサンプル:")
        for i, score in enumerate(backup_data['scores'][:3]):
            print(f"\nスコア {i+1}:")
            print(json.dumps(score, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    check_backup_data()