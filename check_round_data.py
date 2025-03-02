import pandas as pd
from modules.db import supabase
import argparse
import sys

def check_round_data(round_id=None, show_all=False, limit=10):
    """
    Check round data in the database
    
    Args:
        round_id (int, optional): Specific round ID to check
        show_all (bool): Show all rounds info
        limit (int): Limit for the number of rounds/scores to display
    """
    print("=== Golf Score Database Checker ===")
    
    # Get all rounds info
    rounds_result = supabase.table('rounds').select('*').order('round_id', desc=True).execute()
    rounds = rounds_result.data
    
    print(f"Total rounds in database: {len(rounds)}")
    
    # Show all rounds info if requested
    if show_all:
        print("\n=== All Rounds ===")
        rounds_df = pd.DataFrame(rounds)
        print(rounds_df.to_string())
    
    # Check specific round ID
    if round_id:
        print(f"\n=== Checking Round ID: {round_id} ===")
        # Round info
        round_info = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        
        if round_info.data:
            print(f"Round ID {round_id} exists!")
            print("Round info:")
            print(pd.DataFrame([round_info.data[0]]).to_string())
            
            # Score info
            scores = supabase.table('score').select('*').eq('round_id', round_id).execute()
            
            if scores.data:
                print(f"\nFound {len(scores.data)} score records for Round ID {round_id}:")
                scores_df = pd.DataFrame(scores.data)
                print(scores_df.to_string())
            else:
                print(f"\nNo score data found for Round ID {round_id}")
        else:
            print(f"Round ID {round_id} does not exist!")
    
    # Show latest scores
    print("\n=== Latest Score Data ===")
    latest_scores = supabase.table('score').select('*').order('score_id', desc=True).limit(limit).execute()
    if latest_scores.data:
        latest_df = pd.DataFrame(latest_scores.data)
        print(latest_df.to_string())
    else:
        print("No score data found")

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Check golf score database')
    parser.add_argument('-r', '--round', type=int, help='Specific round ID to check')
    parser.add_argument('-a', '--all', action='store_true', help='Show all rounds')
    parser.add_argument('-l', '--limit', type=int, default=10, help='Limit for number of records to display')
    
    args = parser.parse_args()
    
    try:
        check_round_data(args.round, args.all, args.limit)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
