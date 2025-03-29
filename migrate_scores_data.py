import os
from dotenv import load_dotenv
from supabase import create_client
from sqlalchemy import create_engine, text
import time

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Initialize SQLite connection
sqlite_engine = create_engine('sqlite:///golf_app.db', echo=False)

def migrate_scores():
    try:
        with sqlite_engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=ON"))
            result = conn.execute(text("SELECT * FROM score ORDER BY score_id"))
            scores = [dict(zip(row._fields, row)) for row in result]
            
            batch_size = 50
            successful = 0
            failed = 0
            
            for i in range(0, len(scores), batch_size):
                batch = scores[i:i+batch_size]
                batch_data = []
                
                for score_data in batch:
                    try:
                        clean_score = {
                            'score_id': score_data['score_id'],
                            'round_id': score_data['round_id'],
                            'member_id': score_data['member_id'],
                            'front_score': score_data.get('front_score', 0),
                            'back_score': score_data.get('back_score', 0),
                            'extra_score': score_data.get('extra_score', 0),
                            'front_putt': score_data.get('front_putt', 0),
                            'back_putt': score_data.get('back_putt', 0),
                            'extra_putt': score_data.get('extra_putt', 0),
                            'front_game_pt': score_data.get('front_game_pt', 0),
                            'back_game_pt': score_data.get('back_game_pt', 0),
                            'extra_game_pt': score_data.get('extra_game_pt', 0),
                            'match_front': score_data.get('match_front', 0),
                            'match_back': score_data.get('match_back', 0),
                            'match_total': score_data.get('match_total', 0),
                            'match_extra': score_data.get('match_extra', 0),
                            'match_pt': score_data.get('match_pt', 0),
                            'putt_pt': score_data.get('put_pt', 0),  # Note: SQLite column is put_pt
                            'total_pt': score_data.get('total_pt', 0)
                        }
                        
                        # Remove None values
                        clean_score = {k: (v if v is not None else 0) for k, v in clean_score.items()}
                        batch_data.append(clean_score)
                        
                    except Exception as e:
                        print(f"Error processing score {score_data.get('score_id', 'unknown')}: {str(e)}")
                        failed += 1
                        continue
                
                try:
                    if batch_data:
                        result = supabase.table('score').upsert(batch_data).execute()
                        successful += len(batch_data)
                        print(f"Processed {i + len(batch_data)} of {len(scores)} scores")
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error inserting batch: {str(e)}")
                    failed += len(batch_data)
            
            print(f"\nMigration complete:")
            print(f"Successfully migrated: {successful} scores")
            print(f"Failed to migrate: {failed} scores")
            
    except Exception as e:
        print(f"Fatal error during migration: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_scores()