#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(__file__))

from modules.data_formatter import (
    get_color_points_function, 
    get_color_function_for_column,
    color_score_columns,
    color_putt_columns,
    get_ranking_colors_for_players,
    apply_ranking_colors_to_dataframe,
    USE_ADVANCED_COLORS
)

def test_gradient_colors():
    print("=== Enhanced Gradient Color Test ===")
    print(f"Advanced Colors Mode: {USE_ADVANCED_COLORS}")
    
    # スコア列のテスト
    print("\n=== Score Columns Test ===")
    score_values = [28, 32, 36, 40, 45, 50, 55, 65]
    for val in score_values:
        result = color_score_columns(val)
        print(f"Score {val:2d} -> {result}")
    
    # パット列のテスト
    print("\n=== Putt Columns Test ===")
    putt_values = [10, 14, 18, 22, 26, 30, 35]
    for val in putt_values:
        result = color_putt_columns(val)
        print(f"Putt {val:2d} -> {result}")
    
    # ポイント列のテスト
    print("\n=== Point Columns Test ===")
    point_values = [15, 5, 0, -5, -15]
    point_func = get_color_points_function()
    for val in point_values:
        result = point_func(val)
        print(f"Point {val:3d} -> {result}")
    
    # 順位グラデーションのテスト
    print("\n=== Ranking Gradient Test ===")
    for num_players in [3, 4, 5]:
        colors = get_ranking_colors_for_players(num_players)
        print(f"\n{num_players}人の場合:")
        for i, color in enumerate(colors):
            print(f"  {i+1}位: {color}")
    
    # DataFrameを使った順位グラデーションテスト
    print("\n=== DataFrame Ranking Test ===")
    test_data = {
        'Player': ['Alice', 'Bob', 'Charlie', 'David'],
        'Total Score': ['72', '68', '75', '70']
    }
    df = pd.DataFrame(test_data)
    df.set_index('Player', inplace=True)
    
    print("テストデータ:")
    print(df)
    
    ranking_colors = apply_ranking_colors_to_dataframe(df, 'Total Score')
    print("\n順位ベース色付け結果:")
    for i, (player, color) in enumerate(zip(df.index, ranking_colors)):
        print(f"{player}: {color}")
    
    # 列名に応じた関数選択のテスト
    print("\n=== Column Function Selection Test ===")
    test_columns = [
        'Front Score', 'Back Score', 'Total Score',
        'Front Putt', 'Back Putt', 'Putt Extra',
        'Front GP', 'Match Pt', 'Total Pt'
    ]
    
    for col in test_columns:
        func = get_color_function_for_column(col)
        print(f"Column '{col}' -> {func.__name__}")

if __name__ == "__main__":
    test_gradient_colors()
