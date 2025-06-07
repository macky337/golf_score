#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正しいJSONファイルを作成
"""
import json

def create_deploy_metrics():
    """deploy_metrics.jsonを作成"""
    data = {
        "timestamp": "2025-06-07 21:42:00",
        "optimization_level": "ultra",
        "python_files": 22574,
        "total_size_mb": 595.97,
        "core_packages": 5,
        "estimated_deploy_time": "2-3分"
    }
    
    with open('deploy_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("deploy_metrics.json作成完了")

def test_json_files():
    """JSONファイルの有効性をテスト"""
    files = ['version.json', 'deploy_metrics.json']
    
    for filename in files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✓ {filename}: OK - {data}")
        except Exception as e:
            print(f"✗ {filename}: エラー - {e}")

if __name__ == "__main__":
    create_deploy_metrics()
    test_json_files()
