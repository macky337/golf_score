import datetime

VERSION = {
    'major': 1,  # メジャーアップデート（大きな機能追加や破壊的変更）
    'minor': 0,  # マイナーアップデート（後方互換性のある機能追加）
    'patch': 244,  # パッチ（バグ修正）
    'last_updated': '2025-06-14'  # 最終更新日
}

def get_version_string():
    """バージョン文字列を生成"""
    return f"v{VERSION['major']}.{VERSION['minor']}.{VERSION['patch']}"

def get_version_info():
    """バージョン情報を取得"""
    return {
        'version': get_version_string(),
        'last_updated': VERSION['last_updated']
    }