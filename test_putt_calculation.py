#!/usr/bin/env python3
"""
パット計算ロジックの簡易テスト
"""
from modules.score_calculator import calc_putt_points

def main():
    print("=== パット計算ロジックのテスト ===")
    
    # テストケース1: 4人プレイで3人が同点最小の場合
    test_scores_1 = {1: 1, 2: 1, 3: 1, 4: 3}
    result_1 = calc_putt_points(test_scores_1, 4)
    expected_1 = {1: 5, 2: 5, 3: 5, 4: -15}
    
    print(f"テストケース1（4人、3人同点最小）:")
    print(f"  入力: {test_scores_1}")
    print(f"  結果: {result_1}")
    print(f"  期待値: {expected_1}")
    print(f"  正しい: {result_1 == expected_1}")
    print()
    
    # テストケース2: 4人プレイで1人が最小の場合
    test_scores_2 = {1: 1, 2: 2, 3: 2, 4: 2}
    result_2 = calc_putt_points(test_scores_2, 4)
    expected_2 = {1: 30, 2: -10, 3: -10, 4: -10}
    
    print(f"テストケース2（4人、1人最小）:")
    print(f"  入力: {test_scores_2}")
    print(f"  結果: {result_2}")
    print(f"  期待値: {expected_2}")
    print(f"  正しい: {result_2 == expected_2}")
    print()
    
    # テストケース3: 4人プレイで2人が同点最小の場合
    test_scores_3 = {1: 1, 2: 1, 3: 2, 4: 2}
    result_3 = calc_putt_points(test_scores_3, 4)
    expected_3 = {1: 10, 2: 10, 3: -10, 4: -10}
    
    print(f"テストケース3（4人、2人同点最小）:")
    print(f"  入力: {test_scores_3}")
    print(f"  結果: {result_3}")
    print(f"  期待値: {expected_3}")
    print(f"  正しい: {result_3 == expected_3}")
    print()
    
    # テストケース4: 3人プレイで2人が同点最小の場合
    test_scores_4 = {1: 1, 2: 1, 3: 2}
    result_4 = calc_putt_points(test_scores_4, 3)
    expected_4 = {1: 5, 2: 5, 3: -10}
    
    print(f"テストケース4（3人、2人同点最小）:")
    print(f"  入力: {test_scores_4}")
    print(f"  結果: {result_4}")
    print(f"  期待値: {expected_4}")
    print(f"  正しい: {result_4 == expected_4}")
    print()
    
    # 全テストケースの合計チェック
    all_correct = (
        result_1 == expected_1 and
        result_2 == expected_2 and
        result_3 == expected_3 and
        result_4 == expected_4
    )
    
    print(f"=== 全体の結果 ===")
    print(f"すべてのテストケースが正しい: {all_correct}")
    
    if all_correct:
        print("✅ パット計算ロジックの修正が正常に完了しました！")
    else:
        print("❌ 一部のテストケースで問題があります。")

if __name__ == "__main__":
    main()
