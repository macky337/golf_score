#!/usr/bin/env python3
"""
エキストラスコア入力の問題をテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase
from modules.supabase_client import get_scores_with_fallback
from modules.round_results import get_round_results

def test_extra_score_functionality(round_id):
    """エキストラスコア機能のテスト"""
    print(f"=== ラウンドID {round_id} のエキストラスコア機能テスト ===")
    
    try:
        # 1. ラウンド情報を確認
        print(f"\n1. ラウンド情報の確認...")
        round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
        
        if not round_result.data:
            print(f"❌ ラウンドID {round_id} が見つかりません")
            return False
            
        round_info = round_result.data[0]
        print(f"✓ ラウンド: {round_info['date_played']} - {round_info['course_name']}")
        print(f"  プレイヤー数: {round_info.get('num_players')}")
        print(f"  エキストラフラグ: {round_info.get('has_extra')}")
        print(f"  確定フラグ: {round_info.get('finalized')}")
        
        # 2. スコアデータを確認
        print(f"\n2. スコアデータの確認...")
        score_result = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
        
        if not score_result.data:
            print(f"❌ ラウンドID {round_id} のスコアデータが見つかりません")
            return False
            
        scores_data = score_result.data
        print(f"✓ スコアデータ: {len(scores_data)}件")
        
        for score in scores_data:
            member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
            print(f"  {member_name} (ID: {score['member_id']})")
            print(f"    front_score: {score.get('front_score')}, back_score: {score.get('back_score')}")
            print(f"    extra_score: {score.get('extra_score')}, extra_putt: {score.get('extra_putt')}")
            print(f"    extra_game_pt: {score.get('extra_game_pt')}")
        
        # 3. バックスコア入力状況を確認
        print(f"\n3. バックスコア入力状況...")
        back_scores_missing = any(score.get('back_score', 0) == 0 for score in scores_data)
        
        if back_scores_missing:
            print("⚠️  一部のバックスコアが未入力です:")
            for score in scores_data:
                if score.get('back_score', 0) == 0:
                    member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
                    print(f"    - {member_name}")
        else:
            print("✓ 全プレイヤーのバックスコアが入力済みです")
        
        # 4. エキストラスコア入力状況を確認
        print(f"\n4. エキストラスコア入力状況...")
        extra_scores_entered = any(score.get('extra_score', 0) != 0 for score in scores_data)
        
        if extra_scores_entered:
            print("✓ エキストラスコアが入力されています:")
            for score in scores_data:
                if score.get('extra_score', 0) != 0:
                    member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
                    print(f"    {member_name}: {score.get('extra_score', 0)}")
        else:
            print("❌ エキストラスコアが入力されていません")
        
        # 5. ハンディキャップ設定を確認
        print(f"\n5. ハンディキャップ設定の確認...")
        handicap_result = supabase.table('handicap_match').select('*').eq('round_id', round_id).execute()
        
        if handicap_result.data:
            print(f"✓ ハンディキャップ設定: {len(handicap_result.data)}件")
            for h in handicap_result.data:
                print(f"    Player {h['player_1_id']} → Player {h['player_2_id']}: {h['player_1_to_2']}")
                print(f"    Player {h['player_2_id']} → Player {h['player_1_id']}: {h['player_2_to_1']}")
                print(f"    Total Only: {h.get('total_only', False)}")
        else:
            print("❌ ハンディキャップ設定がありません")
        
        # 6. round_results状況を確認
        print(f"\n6. round_results状況の確認...")
        round_results = get_round_results(round_id)
        
        if round_results:
            print(f"✓ round_results: {len(round_results)}件")
            for member_id, result in round_results.items():
                print(f"    Member {member_id}:")
                print(f"      match_extra: {result.get('match_extra', 'N/A')}")
                print(f"      total_pt: {result.get('total_pt', 'N/A')}")
        else:
            print("❌ round_resultsが存在しません")
        
        # 7. エキストラスコア保存テスト
        print(f"\n7. エキストラスコア保存テスト...")
        return test_save_extra_scores(round_id, scores_data)
        
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_extra_scores(round_id, scores_data):
    """エキストラスコアの保存テスト"""
    print("  テスト用のエキストラスコアを保存します...")
    
    try:
        test_data = {
            'extra_score': 4,
            'extra_putt': 2,
            'extra_game_pt': 10
        }
        
        for score in scores_data:
            member_id = score['member_id']
            member_name = score['member']['name'] if score['member'] else f"Member {member_id}"
            
            # テストデータで更新
            result = supabase.table('score').update(test_data).eq('round_id', round_id).eq('member_id', member_id).execute()
            
            if result.data:
                print(f"    ✓ {member_name}: エキストラスコア保存成功")
            else:
                print(f"    ❌ {member_name}: エキストラスコア保存失敗")
                return False
        
        print("  ✅ 全プレイヤーのエキストラスコア保存が成功しました")
        return True
        
    except Exception as e:
        print(f"  ❌ エキストラスコア保存テスト中にエラー: {e}")
        return False

def main():
    """メイン関数"""
    print("エキストラスコア入力問題の調査を開始します")
    
    # 千葉よみうりのラウンドを検索
    try:
        chiba_rounds = supabase.table('rounds').select('*').ilike('course_name', '%千葉よみうり%').execute()
        
        if chiba_rounds.data:
            print(f"\n千葉よみうりのラウンド: {len(chiba_rounds.data)}件")
            for round_data in chiba_rounds.data:
                round_id = round_data['round_id']
                print(f"\n{'='*50}")
                success = test_extra_score_functionality(round_id)
                if success:
                    print(f"✅ ラウンドID {round_id} のテストが完了しました")
                else:
                    print(f"❌ ラウンドID {round_id} のテストに失敗しました")
        else:
            print("千葉よみうりのラウンドが見つかりません")
            
            # 最新のラウンドでテスト
            latest_round = supabase.table('rounds').select('*').order('round_id', desc=True).limit(1).execute()
            if latest_round.data:
                round_id = latest_round.data[0]['round_id']
                print(f"\n最新ラウンド（ID: {round_id}）でテストします")
                test_extra_score_functionality(round_id)
    
    except Exception as e:
        print(f"メイン処理でエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
