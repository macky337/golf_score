import subprocess
import datetime
import re
from pathlib import Path
import sys
import locale

# システムのエンコーディングを設定
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def get_git_commits():
    """Gitのコミット履歴を取得"""
    try:
        # Windows環境でのエンコーディング対応
        startupinfo = None
        if sys.platform.startswith('win'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        process = subprocess.run(
            ['git', 'log', '--pretty=format:%H|%s|%ad', '--date=short'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            startupinfo=startupinfo
        )
        
        if process.returncode != 0:
            print(f"Gitコマンドエラー: {process.stderr}", file=sys.stderr)
            return []
            
        return process.stdout.strip().split('\n')
    except Exception as e:
        print(f"エラー発生: {str(e)}", file=sys.stderr)
        return []

def categorize_commit(message):
    """コミットメッセージを分類"""
    if message.startswith('BREAKING CHANGE'):
        return 'BREAKING CHANGES'
    elif message.startswith('feat:'):
        return '追加機能'
    elif message.startswith('fix:'):
        return '修正'
    else:
        return '更新'

def generate_changelog():
    """変更履歴を生成"""
    try:
        commits = get_git_commits()
        if not commits:
            print("コミット履歴が取得できませんでした")
            return False

        changes = {}
        for commit in commits:
            try:
                hash_id, message, date = commit.split('|')
                category = categorize_commit(message)
                
                if date not in changes:
                    changes[date] = {}
                if category not in changes[date]:
                    changes[date][category] = []
                
                clean_message = re.sub(r'^(BREAKING CHANGE:|feat:|fix:)\s*', '', message)
                changes[date][category].append(clean_message)
            except Exception as e:
                print(f"コミット解析エラー: {str(e)}", file=sys.stderr)
                continue

        changelog = "# 変更履歴\n\n"
        for date in sorted(changes.keys(), reverse=True):
            changelog += f"## [{date}]\n"
            for category in ['BREAKING CHANGES', '追加機能', '修正', '更新']:
                if category in changes[date]:
                    changelog += f"\n### {category}\n"
                    for message in changes[date][category]:
                        changelog += f"- {message}\n"
            changelog += "\n"

        # UTF-8でファイルを保存
        changelog_path = Path(__file__).parent.parent / 'CHANGELOG.md'
        changelog_path.write_text(changelog, encoding='utf-8')
        
        print(f"CHANGELOGを生成しました: {changelog_path}")
        return True
    except Exception as e:
        print(f"CHANGELOG生成エラー: {str(e)}", file=sys.stderr)
        return False

if __name__ == '__main__':
    generate_changelog()