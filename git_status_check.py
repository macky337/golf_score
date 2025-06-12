import subprocess
import os

def run_git_command(command):
    try:
        os.chdir(r'c:\Users\user\Documents\GitHub\golf_score')
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def check_git_status():
    print("=== Git Status Check ===")
    
    # Current branch
    stdout, stderr, code = run_git_command("git branch --show-current")
    print(f"Current branch: {stdout}")
    
    # Git status
    stdout, stderr, code = run_git_command("git status --porcelain")
    if stdout:
        print(f"Changed files:\n{stdout}")
    else:
        print("No changed files")
    
    # Latest commits
    stdout, stderr, code = run_git_command("git log --oneline -3")
    print(f"Latest commits:\n{stdout}")
    
    # Remote status
    stdout, stderr, code = run_git_command("git log origin/develop..develop --oneline")
    if stdout:
        print(f"Unpushed commits:\n{stdout}")
    else:
        print("No unpushed commits")
    
    # Remote branches
    stdout, stderr, code = run_git_command("git branch -r")
    print(f"Remote branches:\n{stdout}")

if __name__ == "__main__":
    check_git_status()
