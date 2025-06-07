#!/usr/bin/env python3
import os
import subprocess
import sys

def main():
    repo_path = r"c:\Users\user\Documents\GitHub\golf_score"
    commit_hash = "e53d2ddc54bdb1a3533294f5c73e2203525fe938"
    
    print(f"Changing to repository directory: {repo_path}")
    os.chdir(repo_path)
    
    print(f"Current directory: {os.getcwd()}")
    
    try:
        # First check current status
        print("Checking current git status...")
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print("Working directory has changes:")
            print(result.stdout)
        else:
            print("Working directory is clean")
        
        # Execute hard reset
        print(f"Executing: git reset --hard {commit_hash}")
        result = subprocess.run(['git', 'reset', '--hard', commit_hash], 
                              capture_output=True, text=True, check=True)
        print("Reset output:")
        print(result.stdout)
        if result.stderr:
            print("Stderr:")
            print(result.stderr)
        
        # Verify the reset
        print("Verifying reset...")
        result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                              capture_output=True, text=True, check=True)
        print("Current HEAD:")
        print(result.stdout)
        
        # Check final status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print("Working directory still has changes:")
            print(result.stdout)
        else:
            print("Working directory is now clean")
            
        print("Git reset completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing git command: {e}")
        print(f"Return code: {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("Script completed successfully")
        sys.exit(0)
    else:
        print("Script failed")
        sys.exit(1)
