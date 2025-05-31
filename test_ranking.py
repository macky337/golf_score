#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.data_formatter import apply_ranking_colors_to_dataframe, get_ranking_colors_for_players

def test_ranking_functionality():
    print("=== 順位ベースグラデーション機能テスト ===")
    
    # テストデータの作成（4人のゴルファー）
    test_data = {
        'Player': ['田中太郎', '佐藤花子', '鈴木一郎', '高橋美咲'],
        'Total Score': ['72', '68', '75', '70'],  # スコア（少ない方が良い）
        'Total Pt': ['40', '60', '20', '50'],     # ポイント（多い方が良い）
        'Front Score': ['36', '34', '38', '35'],
        'Game Pt': ['15', '25', '5', '20']
    }
    
    df = pd.DataFrame(test_data)
    df.set_index('Player', inplace=True)
    
    print("テストデータ:")
    print(df)
    print()
    
    # Total Score による順位テスト（昇順：少ない方が良い）
    print("=== Total Score による順位グラデーション ===")
    ranking_colors = apply_ranking_colors_to_dataframe(df, 'Total Score')
    print("スコア順位（少ない方が1位）:")
    for i, (player, score) in enumerate(df['Total Score'].items()):
        print(f"{i+1}. {player}: {score} -> {ranking_colors[i]}")
    print()
    
    # Total Pt による順位テスト（降順：多い方が良い）
    print("=== Total Pt による順位グラデーション ===")
    ranking_colors_pt = apply_ranking_colors_to_dataframe(df, 'Total Pt')
    print("ポイント順位（多い方が1位）:")
    for i, (player, points) in enumerate(df['Total Pt'].items()):
        print(f"{i+1}. {player}: {points} -> {ranking_colors_pt[i]}")
    print()
    
    # プレイヤー数別色テスト
    print("=== プレイヤー数別順位色 ===")
    for num in [3, 4, 5]:
        colors = get_ranking_colors_for_players(num)
        print(f"{num}人の場合:")
        for i, color in enumerate(colors):
            print(f"  {i+1}位: {color}")
        print()

if __name__ == "__main__":
    test_ranking_functionality()
