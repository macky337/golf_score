import json
import os
import datetime
import pytz
from pathlib import Path

def get_version_file_path():
    """バージョンファイルのパスを取得"""
    return Path(__file__).parent.parent / 'version.json'

def load_version():
    """バージョン情報を読み込む"""
    version_file = get_version_file_path()
    if os.path.exists(version_file):
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    # ファイルが空の場合はデフォルトを返す
                    return get_default_version()
                return json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"バージョンファイルの読み込みエラー: {e}")
            print("デフォルトバージョンを使用します")
            return get_default_version()
    return get_default_version()

def get_default_version():
    """デフォルトバージョン情報を返す"""
    return {
        'major': 1,
        'minor': 0,
        'patch': 237,
        'last_updated': datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d')
    }

def save_version(version_info):
    """バージョン情報を保存"""
    version_file = get_version_file_path()
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)

def update_version(level='patch'):
    """バージョンを更新"""
    version_info = load_version()
    
    if level == 'major':
        version_info['major'] += 1
        version_info['minor'] = 0
        version_info['patch'] = 0
    elif level == 'minor':
        version_info['minor'] += 1
        version_info['patch'] = 0
    else:
        version_info['patch'] += 1
    
    version_info['last_updated'] = datetime.datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d')
    save_version(version_info)
    print(f"バージョンを更新しました: v{version_info['major']}.{version_info['minor']}.{version_info['patch']}")

if __name__ == '__main__':
    import sys
    level = sys.argv[1] if len(sys.argv) > 1 else 'patch'
    update_version(level)