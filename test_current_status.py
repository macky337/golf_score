#!/usr/bin/env python3
"""現在の状況をテストするスクリプト"""

import os
import sys
from dotenv import load_dotenv
import pandas as pd

# 環境変数を読み込み
load_dotenv()

# モジュールパスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from modules.db import supabase
    print("✅ Supabase接続成功")
except Exception as e:
    print(f"❌ Supabase接続エラー: {e}")
    sys.exit(1)

def test_round_53():
    """Round 53のデータを確認"""
    print("\n=== Round 53 テスト ===")
    
    try:
        # Roundsテーブルから基本情報を取得
        rounds = supabase.table('rounds').select('*').eq('id', 53).execute()
        if rounds.data:
            round_data = rounds.data[0]
            print(f"Round ID: {round_data['id']}")
            print(f"Course: {round_data['course_name']}")
            print(f"Date: {round_data['date']}")
            print(f"Status: {round_data.get('status', 'N/A')}")
        else:
            print("Round 53が見つかりません")
            return False
            
        # 参加者情報を取得
        participants = supabase.table('participants').select('*').eq('round_id', 53).execute()
        if participants.data:
            print(f"参加者数: {len(participants.data)}人")
            df = pd.DataFrame(participants.data)
            print("参加者一覧:")
            print(df[['id', 'name', 'handicap']].head(5).to_string(index=False))
        else:
            print("参加者が見つかりません")
            
        # エキストラスコアを確認
        extra_scores = supabase.table('extra_scores').select('*').eq('round_id', 53).execute()
        if extra_scores.data:
            print(f"\nエキストラスコア登録数: {len(extra_scores.data)}件")
            df = pd.DataFrame(extra_scores.data)
            print("エキストラスコア詳細:")
            print(df.head().to_string(index=False))
        else:
            print("\nエキストラスコアが登録されていません")
            
        return True
        
    except Exception as e:
        print(f"データベースアクセスエラー: {e}")
        return False

def test_extra_score_functionality():
    """エキストラスコア機能のテスト"""
    print("\n=== エキストラスコア機能テスト ===")
    
    try:
        # テスト用データの作成
        test_player_id = None
        participants = supabase.table('participants').select('id, name').eq('round_id', 53).limit(1).execute()
        
        if participants.data:
            test_player_id = participants.data[0]['id']
            test_player_name = participants.data[0]['name']
            print(f"テスト対象プレイヤー: {test_player_name} (ID: {test_player_id})")
            
            # エキストラスコアのテスト保存
            test_data = {
                'round_id': 53,
                'player_id': test_player_id,
                'nearest_pin': 1,
                'long_drive': 0,
                'chip_in': 0,
                'alba': 0,
                'hole_in_one': 0
            }
            
            # 既存データを削除
            supabase.table('extra_scores').delete().eq('round_id', 53).eq('player_id', test_player_id).execute()
            
            # 新しいデータを挿入
            result = supabase.table('extra_scores').insert(test_data).execute()
            
            if result.data:
                print("✅ エキストラスコアのテスト保存が成功しました")
                
                # 保存されたデータを確認
                saved_data = supabase.table('extra_scores').select('*').eq('round_id', 53).eq('player_id', test_player_id).execute()
                if saved_data.data:
                    print("保存されたデータ:", saved_data.data[0])
                    return True
                else:
                    print("❌ 保存されたデータの確認に失敗")
                    return False
            else:
                print("❌ エキストラスコアの保存に失敗")
                return False
        else:
            print("❌ テスト用プレイヤーが見つかりません")
            return False
            
    except Exception as e:
        print(f"エキストラスコア機能テストエラー: {e}")
        return False

if __name__ == "__main__":
    # 結果をファイルに出力
    with open("test_results.txt", "w", encoding="utf-8") as f:
        import sys
        
        # 標準出力をファイルにリダイレクト
        original_stdout = sys.stdout
        sys.stdout = f
        
        try:
            print("現在の状況テストを開始します...")
            
            # Round 53のテスト
            round_test_ok = test_round_53()
            
            # エキストラスコア機能のテスト
            extra_score_test_ok = test_extra_score_functionality()
            
            print("\n=== テスト結果 ===")
            print(f"Round 53データ確認: {'✅ OK' if round_test_ok else '❌ NG'}")
            print(f"エキストラスコア機能: {'✅ OK' if extra_score_test_ok else '❌ NG'}")
            
            if round_test_ok and extra_score_test_ok:
                print("\n🎉 すべてのテストが成功しました！")
                print("千葉よみうり (ID: 53) のエキストラスコア機能は正常に動作しています。")
            else:
                print("\n⚠️ 一部のテストが失敗しました。")
                
        finally:
            sys.stdout = original_stdout
    
    print("テスト完了。結果は test_results.txt をご確認ください。")
