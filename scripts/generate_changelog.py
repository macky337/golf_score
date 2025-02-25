import subprocess
import datetime
import re
from pathlib import Path

def get_git_commits():
    """Gitのコミット履歴を取得"""
    cmd = ['git', 'log', '--pretty=format:%H|%s|%ad', '--date=short']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip().split('\n')

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
    """CHANGELOGを生成"""
    commits = get_git_commits()
    changes = {}
    
    for commit in commits:
        hash_id, message, date = commit.split('|')
        category = categorize_commit(message)
        
        if date not in changes:
            changes[date] = {}
        
        if category not in changes[date]:
            changes[date][category] = []
            
        # コミットメッセージからプレフィックスを削除
        clean_message = re.sub(r'^(BREAKING CHANGE:|feat:|fix:)\s*', '', message)
        changes[date][category].append(clean_message)

    # CHANGELOGの生成
    changelog = "# 変更履歴\n\n"
    
    for date in sorted(changes.keys(), reverse=True):
        changelog += f"## [{date}]\n"
        
        for category in ['BREAKING CHANGES', '追加機能', '修正', '更新']:
            if category in changes[date]:
                changelog += f"\n### {category}\n"
                for message in changes[date][category]:
                    changelog += f"- {message}\n"
        
        changelog += "\n"
    
    # ファイルに保存
    changelog_path = Path(__file__).parent.parent / 'CHANGELOG.md'
    with open(changelog_path, 'w', encoding='utf-8') as f:
        f.write(changelog)
    
    print(f"CHANGELOGを生成しました: {changelog_path}")

if __name__ == '__main__':
    generate_changelog()