import json
from supabase import create_client
import os
from dotenv import load_dotenv

def load_json_file(file_path):
    """指定されたバックアップファイルからデータを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def merge_score_data(remote_backup, local_backup):
    """2つのバックアップデータからスコアデータをマージする"""
    remote_scores = remote_backup.get('scores', [])
    local_scores = local_backup.get('scores', [])
    
    # Create a dictionary with score_id as key for easy lookup and merging
    merged_scores = {}
    
    # Add remote scores first
    for score in remote_scores:
        if 'score_id' in score:
            merged_scores[score['score_id']] = score
    
    # Update/add local scores
    for score in local_scores:
        if 'score_id' in score:
            if score['score_id'] in merged_scores:
                # Merge data, prioritizing non-null values from local backup
                for key, value in score.items():
                    if value is not None:
                        merged_scores[score['score_id']][key] = value
            else:
                merged_scores[score['score_id']] = score
    
    return list(merged_scores.values())

def restore_data():
    """バックアップデータをSupabaseに復元する"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Load backup files
        remote_backup = load_json_file('backups/remote_main_backup_20250225_140525.json')
        local_backup = load_json_file('backups/golf_score_backup_20250225_140823.json')
        
        print("\nDebug: Checking backup data structure...")
        print("Local backup keys:", list(local_backup.keys()))
        print("Remote backup keys:", list(remote_backup.keys()))
        
        # Clear existing data first
        print("\nClearing existing data...")
        supabase.table('handicap_match').delete().neq('id', -1).execute()
        supabase.table('score').delete().neq('score_id', -1).execute()
        supabase.table('rounds').delete().neq('round_id', -1).execute()
        
        # 1. Restore rounds first
        print("\nRestoring rounds table...")
        rounds = local_backup.get('rounds', [])
        success_count = 0
        error_count = 0
        valid_round_ids = set()  # Keep track of successfully restored round IDs
        
        for round_data in rounds:
            try:
                clean_round = {
                    'round_id': round_data.get('round_id'),
                    'date': round_data.get('date_played'),  # Use date_played for both date fields
                    'date_played': round_data.get('date_played'),
                    'course_name': round_data.get('course_name'),
                    'num_players': round_data.get('num_players', 4),
                    'has_extra': round_data.get('has_extra', False),
                    'finalized': round_data.get('finalized', False)
                }
                supabase.table('rounds').insert(clean_round).execute()
                success_count += 1
                valid_round_ids.add(round_data.get('round_id'))
            except Exception as e:
                error_count += 1
                print(f"Error restoring round {round_data.get('round_id')}: {str(e)}")
                if hasattr(e, 'details'):
                    print(f"Error details: {e.details}")
        
        print(f"Rounds restoration complete: {success_count} successful, {error_count} failed")
        
        # 2. Restore scores (only for valid rounds)
        print("\nRestoring scores table...")
        merged_scores = merge_score_data(remote_backup, local_backup)
        valid_scores = [score for score in merged_scores if score.get('round_id') in valid_round_ids]
        print(f"Total merged scores: {len(merged_scores)}")
        print(f"Valid scores (matching restored rounds): {len(valid_scores)}")
        
        batch_size = 50
        success_count = 0
        error_count = 0
        
        for i in range(0, len(valid_scores), batch_size):
            batch = valid_scores[i:i+batch_size]
            try:
                # Clean up the data before insertion
                clean_batch = []
                for score in batch:
                    clean_score = {
                        'score_id': score.get('score_id'),
                        'round_id': score.get('round_id'),
                        'member_id': score.get('member_id'),
                        'front_score': score.get('front_score', 0),
                        'back_score': score.get('back_score', 0),
                        'extra_score': score.get('extra_score', 0),
                        'front_putt': score.get('front_putt', 0),
                        'back_putt': score.get('back_putt', 0),
                        'extra_putt': score.get('extra_putt', 0),
                        'front_game_pt': score.get('front_game_pt', 0),
                        'back_game_pt': score.get('back_game_pt', 0),
                        'extra_game_pt': score.get('extra_game_pt', 0),
                        'match_front': score.get('match_front', 0),
                        'match_back': score.get('match_back', 0),
                        'match_total': score.get('match_total', 0),
                        'match_extra': score.get('match_extra', 0),
                        'match_pt': score.get('match_pt', 0),
                        'putt_pt': score.get('putt_pt', 0),
                        'total_pt': score.get('total_pt', 0)
                    }
                    # Convert any None values to 0 for numeric fields
                    for key in clean_score:
                        if clean_score[key] is None:
                            clean_score[key] = 0
                    clean_batch.append(clean_score)
                
                result = supabase.table('score').insert(clean_batch).execute()
                success_count += len(batch)
                print(f"Restored scores {i+1} to {i+len(batch)}")
                
            except Exception as e:
                error_count += len(batch)
                print(f"Error restoring scores {i+1} to {i+len(batch)}: {str(e)}")
                if hasattr(e, 'details'):
                    print(f"Error details: {e.details}")
        
        print(f"Score restoration complete: {success_count} successful, {error_count} failed")
        
        # 3. Restore handicap matches (only for valid rounds)
        print("\nRestoring handicap_match table...")
        handicap_matches = local_backup.get('handicap_matches', [])
        valid_matches = [match for match in handicap_matches if match.get('round_id') in valid_round_ids]
        print(f"Total handicap matches: {len(handicap_matches)}")
        print(f"Valid handicap matches (matching restored rounds): {len(valid_matches)}")
        
        success_count = 0
        error_count = 0
        
        for match in valid_matches:
            try:
                clean_match = {
                    'id': match.get('id'),
                    'round_id': match.get('round_id'),
                    'player_1_id': match.get('player_1_id'),
                    'player_2_id': match.get('player_2_id'),
                    'player_1_to_2': match.get('player_1_to_2', 0),
                    'player_2_to_1': match.get('player_2_to_1', 0),
                    'total_only': match.get('total_only', False)
                }
                supabase.table('handicap_match').insert(clean_match).execute()
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error restoring handicap match {match.get('id')}: {str(e)}")
                if hasattr(e, 'details'):
                    print(f"Error details: {e.details}")
        
        print(f"Handicap match restoration complete: {success_count} successful, {error_count} failed")
        print("\nRestoration process completed!")
        
    except Exception as e:
        print(f"An error occurred during restoration: {str(e)}")
        if hasattr(e, 'details'):
            print(f"Error details: {e.details}")
        raise

if __name__ == "__main__":
    restore_data()
