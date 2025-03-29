import sys
import os

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_front_score import test_front_score
from tests.test_back_score import test_back_score
from tests.test_extra_score import test_extra_score
from tests.test_three_players import test_three_players
from tests.test_four_players import test_four_players

def run_all_tests():
    """すべてのテストを実行"""
    print("===== ゴルフスコア計算ロジックテスト一括実行 =====\n")
    
    test_results = []
    
    # フロントスコアテスト
    print("\n=== フロントスコアテスト ===")
    try:
        test_front_score()
        test_results.append(("フロントスコアテスト", "成功"))
    except Exception as e:
        test_results.append(("フロントスコアテスト", f"失敗: {str(e)}"))
    
    # バックスコアテスト
    print("\n=== バックスコアテスト ===")
    try:
        test_back_score()
        test_results.append(("バックスコアテスト", "成功"))
    except Exception as e:
        test_results.append(("バックスコアテスト", f"失敗: {str(e)}"))
    
    # エキストラスコアテスト
    print("\n=== エキストラスコアテスト ===")
    try:
        test_extra_score()
        test_results.append(("エキストラスコアテスト", "成功"))
    except Exception as e:
        test_results.append(("エキストラスコアテスト", f"失敗: {str(e)}"))
    
    # 3人プレイヤーテスト
    print("\n=== 3人プレイヤーテスト ===")
    try:
        test_three_players()
        test_results.append(("3人プレイヤーテスト", "成功"))
    except Exception as e:
        test_results.append(("3人プレイヤーテスト", f"失敗: {str(e)}"))
    
    # 4人プレイヤーテスト
    print("\n=== 4人プレイヤーテスト ===")
    try:
        test_four_players()
        test_results.append(("4人プレイヤーテスト", "成功"))
    except Exception as e:
        test_results.append(("4人プレイヤーテスト", f"失敗: {str(e)}"))
    
    # 結果サマリー
    print("\n===== テスト結果サマリー =====")
    for test_name, result in test_results:
        status = "✓" if "成功" in result else "✗"
        print(f"{status} {test_name}: {result}")
    
    success_count = sum(1 for _, result in test_results if "成功" in result)
    print(f"\n合計: {len(test_results)}テスト中 {success_count}テスト成功")

if __name__ == "__main__":
    run_all_tests()
