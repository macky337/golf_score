#!/usr/bin/env python3
"""
モジュールインポートテスト
"""

import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print(f"Current dir: {current_dir}")
print(f"Parent dir: {parent_dir}")
print(f"Sys path (first 3): {sys.path[:3]}")

try:
    from modules.db import supabase
    print("✅ SUCCESS: modules.db import successful")
    
    # 簡単なデータベーステスト
    rounds_result = supabase.table('rounds').select('round_id').limit(1).execute()
    if rounds_result.data:
        print(f"✅ SUCCESS: Database connection works, found round ID: {rounds_result.data[0]['round_id']}")
    else:
        print("⚠️ WARNING: Database connection works but no rounds found")
        
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
except Exception as e:
    print(f"❌ DATABASE ERROR: {e}")

print("\n=== Testing streamlit import ===")
try:
    import streamlit as st
    print("✅ SUCCESS: streamlit import successful")
except ImportError as e:
    print(f"❌ STREAMLIT IMPORT ERROR: {e}")
