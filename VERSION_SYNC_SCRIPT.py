#!/usr/bin/env python3
"""
バージョン同期スクリプト
全てのバージョン管理ファイルを最新の状態に統一する
"""
import json
import os
import datetime
import pytz

def sync_all_versions():
    """全てのバージョンファイルを最新のversion.jsonに合わせて同期"""
    
    # 1. version.jsonから現在のバージョンを読み込み
    version_json_path = 'version.json'
    
    if os.path.exists(version_json_path):
        with open(version_json_path, 'r', encoding='utf-8') as f:
            current_version = json.load(f)
        print(f"📋 現在のバージョン: v{current_version['major']}.{current_version['minor']}.{current_version['patch']}")
    else:
        print("❌ version.jsonが見つかりません")
        return False
    
    # 2. version.pyファイルを更新
    version_py_content = f'''import datetime

VERSION = {{
    'major': {current_version['major']},  # メジャーアップデート（大きな機能追加や破壊的変更）
    'minor': {current_version['minor']},  # マイナーアップデート（後方互換性のある機能追加）
    'patch': {current_version['patch']},  # パッチ（バグ修正）
    'last_updated': '{current_version['last_updated']}'  # 最終更新日
}}

def get_version_string():
    """バージョン文字列を生成"""
    return f"v{{VERSION['major']}}.{{VERSION['minor']}}.{{VERSION['patch']}}"

def get_version_info():
    """バージョン情報を取得"""
    return {{
        'version': get_version_string(),
        'last_updated': VERSION['last_updated']
    }}
'''
    
    with open('version.py', 'w', encoding='utf-8') as f:
        f.write(version_py_content)
    print("✅ version.py を更新しました")
    
    # 3. scripts/version_manager.pyのget_default_version()を更新
    version_manager_path = 'scripts/version_manager.py'
    if os.path.exists(version_manager_path):
        with open(version_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # get_default_version関数のpatch値を更新
        updated_content = content.replace(
            "'patch': 0,",
            f"'patch': {current_version['patch']},"
        )
        
        with open(version_manager_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("✅ scripts/version_manager.py を更新しました")
    
    # 4. version_manager.pyのload_version()のデフォルト値を更新
    old_version_manager_path = 'version_manager.py'
    if os.path.exists(old_version_manager_path):
        with open(old_version_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # load_version関数内のpatch値を更新
        updated_content = content.replace(
            "'patch': 0,",
            f"'patch': {current_version['patch']},"
        )
        
        with open(old_version_manager_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("✅ version_manager.py を更新しました")
    
    # 5. デプロイ用メトリクスファイルも更新
    deploy_metrics_files = [
        'deploy_metrics.json',
        'deploy_metrics_fixed.json',
        'deploy_metrics_temp_fixed.json'
    ]
    
    for metrics_file in deploy_metrics_files:
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                
                # バージョン情報を更新
                if 'version' in metrics:
                    metrics['version'] = f"v{current_version['major']}.{current_version['minor']}.{current_version['patch']}"
                
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f, indent=2, ensure_ascii=False)
                print(f"✅ {metrics_file} を更新しました")
            except:
                print(f"⚠️ {metrics_file} の更新をスキップしました")
    
    print(f"\n🎯 バージョン同期完了: v{current_version['major']}.{current_version['minor']}.{current_version['patch']}")
    return True

if __name__ == "__main__":
    sync_all_versions()
