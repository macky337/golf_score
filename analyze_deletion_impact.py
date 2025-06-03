#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Golf Club (ID: 7) 削除による影響調査

このスクリプトは削除による影響を詳細に分析し、
どのデータが失われるかを事前に確認します。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db import supabase
from datetime import datetime

def analyze_deletion_impact():
    """削除による影響を詳細分析"""
    
    course_id = 7
    course_name = "Sample Golf Club"
    
    print(f"=== {course_name} (ID: {course_id}) 削除影響調査 ===\n")
    
    try:
        # 1. コースの基本情報
        print("📋 1. コースの基本情報")
        course_result = supabase.table('courses').select('*').eq('id', course_id).execute()
        if not course_result.data:
            print(f"❌ ID {course_id} のコースが見つかりません")
            return
        
        course = course_result.data[0]
        print(f"  コース名: {course['name']}")
        print(f"  コースID: {course['id']}")
        print()
        
        # 2. 影響を受けるラウンドデータ
        print("🎯 2. 影響を受けるラウンドデータ")
        rounds_result = supabase.table('rounds').select('*').eq('course_id', course_id).execute()
        
        if not rounds_result.data:
            print("  ✅ 影響を受けるラウンドはありません")
            print("  → 安全に削除可能です")
            return
        
        rounds = rounds_result.data
        print(f"  削除されるラウンド数: {len(rounds)} 件")
        print()
        
        # ラウンドの詳細情報
        print("  📅 削除されるラウンドの詳細:")
        round_dates = []
        round_ids = []
        
        for round_data in rounds:
            round_id = round_data['round_id']
            date_played = round_data['date_played']
            num_players = round_data.get('num_players', 'N/A')
            has_extra = round_data.get('has_extra', False)
            
            round_ids.append(round_id)
            round_dates.append(date_played)
            
            print(f"    - ラウンドID: {round_id}")
            print(f"      日付: {date_played}")
            print(f"      参加者数: {num_players}名")
            print(f"      エキストラ: {'あり' if has_extra else 'なし'}")
            print()
        
        # 期間の分析
        if round_dates:
            round_dates.sort()
            print(f"  📊 ラウンド実施期間:")
            print(f"    最古: {round_dates[0]}")
            print(f"    最新: {round_dates[-1]}")
            print()
        
        # 3. 影響を受けるスコアデータ
        print("🏌️ 3. 影響を受けるスコアデータ")
        
        total_scores = 0
        player_impact = {}
        score_details = []
        
        for round_id in round_ids:
            score_result = supabase.table('score').select('*').eq('round_id', round_id).execute()
            scores = score_result.data
            
            if scores:
                total_scores += len(scores)
                score_details.append({
                    'round_id': round_id,
                    'score_count': len(scores),
                    'scores': scores
                })
                
                # プレイヤー別の影響分析
                for score in scores:
                    member_id = score.get('member_id')
                    if member_id:
                        if member_id not in player_impact:
                            player_impact[member_id] = {
                                'round_count': 0,
                                'score_count': 0,
                                'rounds': []
                            }
                        player_impact[member_id]['round_count'] += 1
                        player_impact[member_id]['score_count'] += 1
                        player_impact[member_id]['rounds'].append(round_id)
        
        print(f"  削除されるスコア記録数: {total_scores} 件")
        
        if total_scores > 0:
            print(f"  影響を受けるプレイヤー数: {len(player_impact)} 名")
            print()
            
            # 4. プレイヤー別影響詳細
            print("👥 4. プレイヤー別影響詳細")
            
            # メンバー情報を取得
            member_result = supabase.table('member').select('*').execute()
            member_dict = {m['member_id']: m['name'] for m in member_result.data}
            
            for member_id, impact in player_impact.items():
                member_name = member_dict.get(member_id, f"Unknown (ID: {member_id})")
                print(f"  👤 {member_name}")
                print(f"     失われるラウンド数: {impact['round_count']} 回")
                print(f"     失われるスコア記録: {impact['score_count']} 件")
                print(f"     ラウンドID: {', '.join(map(str, impact['rounds']))}")
                print()
        
        # 5. 統計・ランキングへの影響
        print("📈 5. 統計・ランキングへの影響")
        
        # round_resultsテーブルの確認
        try:
            round_results_result = supabase.table('round_results').select('*').in_('round_id', round_ids).execute()
            if round_results_result.data:
                print(f"  削除される集計結果: {len(round_results_result.data)} 件")
                
                # 各プレイヤーのポイント情報
                for result in round_results_result.data:
                    member_id = result.get('member_id')
                    member_name = member_dict.get(member_id, f"Unknown (ID: {member_id})")
                    total_pt = result.get('total_pt', 0)
                    match_pt = result.get('match_pt', 0)
                    putt_pt = result.get('putt_pt', 0)
                    
                    print(f"    {member_name}: 総合{total_pt}pt (マッチ{match_pt}pt + パット{putt_pt}pt)")
            else:
                print("  集計結果データはありません")
        except Exception as e:
            print(f"  集計結果の確認でエラー: {e}")
        print()
        
        # 6. ハンディキャップマッチへの影響
        print("🎯 6. ハンディキャップマッチへの影響")
        try:
            handicap_result = supabase.table('handicap_match').select('*').in_('round_id', round_ids).execute()
            if handicap_result.data:
                print(f"  削除されるハンディキャップマッチ: {len(handicap_result.data)} 件")
                for match in handicap_result.data:
                    player1_name = member_dict.get(match.get('player_1_id'), 'Unknown')
                    player2_name = member_dict.get(match.get('player_2_id'), 'Unknown')
                    print(f"    {player1_name} vs {player2_name}")
            else:
                print("  ハンディキャップマッチデータはありません")
        except Exception as e:
            print(f"  ハンディキャップマッチの確認でエラー: {e}")
        print()
        
        # 7. データ保護の提案
        print("💾 7. データ保護の提案")
        print("  削除前に以下のバックアップを推奨:")
        print("  1. ラウンドデータの手動バックアップ")
        print("  2. スコア記録のエクスポート")
        print("  3. 統計データのスナップショット保存")
        print()
        
        # 8. 削除による利点
        print("✨ 8. 削除による利点")
        print("  1. データベースの整理")
        print("  2. 不要なゴルフ場の除去")
        print("  3. コース管理画面の見やすさ向上")
        print()
        
        # 9. 総合的な影響評価
        print("⚖️ 9. 総合的な影響評価")
        
        severity_score = 0
        if len(rounds) > 10:
            severity_score += 3
        elif len(rounds) > 5:
            severity_score += 2
        elif len(rounds) > 0:
            severity_score += 1
            
        if len(player_impact) > 5:
            severity_score += 2
        elif len(player_impact) > 2:
            severity_score += 1
            
        if total_scores > 50:
            severity_score += 3
        elif total_scores > 20:
            severity_score += 2
        elif total_scores > 0:
            severity_score += 1
        
        if severity_score >= 7:
            risk_level = "🔴 高リスク"
            recommendation = "削除は慎重に検討してください"
        elif severity_score >= 4:
            risk_level = "🟡 中リスク"
            recommendation = "バックアップを取ってから削除してください"
        elif severity_score >= 1:
            risk_level = "🟢 低リスク"
            recommendation = "比較的安全に削除可能です"
        else:
            risk_level = "✅ リスクなし"
            recommendation = "安全に削除可能です"
        
        print(f"  影響レベル: {risk_level}")
        print(f"  推奨事項: {recommendation}")
        print(f"  影響スコア: {severity_score}/9")
        print()
        
        # 10. 削除実行の確認
        print("❓ 10. 削除実行の確認")
        print("  上記の影響を確認した上で、削除を実行しますか？")
        print("  削除するには、delete_sample_golf_club.py を実行してください")
        print()
        
        return {
            'course': course,
            'rounds_count': len(rounds),
            'scores_count': total_scores,
            'players_affected': len(player_impact),
            'risk_level': risk_level,
            'severity_score': severity_score
        }
        
    except Exception as e:
        print(f"\n❌ 影響調査中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン実行関数"""
    try:
        result = analyze_deletion_impact()
        if result:
            print("=" * 60)
            print("📊 影響調査完了")
            print("=" * 60)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
