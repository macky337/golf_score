from modules.score_calculator import calc_putt_points

# 4人プレイで3人が同点最小の場合
test_scores = {1: 1, 2: 1, 3: 1, 4: 3}
result = calc_putt_points(test_scores, 4)
expected = {1: 5, 2: 5, 3: 5, 4: -15}

print("4人、3人同点最小のテスト:")
print(f"入力: {test_scores}")
print(f"結果: {result}")
print(f"期待値: {expected}")
print(f"テスト成功: {result == expected}")
