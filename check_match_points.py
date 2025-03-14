import streamlit as st
import pandas as pd
from modules.db import supabase
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

def calculate_match_points(player_i, player_j, handicap_ij, handicap_ji, is_total_only=False):
    """1対1のマッチポイント計算（各セクション±10pt）- ロジックのコピー"""
    front_pt = back_pt = total_pt = extra_pt = 0

    # スコアの取得と安全化
    front_score_i = player_i.get('front_score', 0) or 0
    back_score_i = player_i.get('back_score', 0) or 0
    extra_score_i = player_i.get('extra_score', 0) or 0
    
    front_score_j = player_j.get('front_score', 0) or 0
    back_score_j = player_j.get('back_score', 0) or 0
    extra_score_j = player_j.get('extra_score', 0) or 0

    # バックとエキストラのプレイ状態を確認（両方とも0より大きい場合にプレイ済みと判断）
    has_back = back_score_i > 0 and back_score_j > 0
    has_extra = extra_score_i > 0 and extra_score_j > 0

    if is_total_only:
        # Total Onlyモードでは、バックスコアまたはエキストラスコアがある場合のみ判定
        # フロント9だけの場合は判定しない（0-0のまま）
        
        # フロントとバックのスコアが入力されている場合
        if has_back:
            # フロント+バックの合計を比較（ハンディキャップは相手のスコアから引く）
            # handicap_ijはプレイヤーiからjへのハンディキャップなのでjのスコアから引く
            net_score_i = front_score_i + back_score_i
            net_score_j = (front_score_j + back_score_j) - handicap_ij
            if net_score_i < net_score_j:
                # 修正: iの方がスコアが低い（良い）場合はプラスポイント
                total_pt = 10
            elif net_score_i > net_score_j:
                # 修正: iの方がスコアが高い（悪い）場合はマイナスポイント
                total_pt = -10
        else:
            # バックスコアがない場合は判定しない（0-0）
            total_pt = 0
            
        # エキストラスコアの比較（両方プレイしている場合のみ）
        if has_extra:
            # ハンディキャップはハーフ分をそのまま適用
            net_extra_i = extra_score_i
            net_extra_j = extra_score_j - handicap_ij
            if net_extra_i < net_extra_j:
                extra_pt = 10
            elif net_extra_i > net_extra_j:
                extra_pt = -10
                
        # Front/Backのポイントはゼロ（Total Only モードでは計算しない）
        front_pt = 0
        back_pt = 0
    else:
        # 通常モード - 各セクションごとに比較
        
        # フロントスコアの比較（フロントは必ず比較）
        # ハンディキャップはハーフ分をそのまま適用（割らない）
        net_front_i = front_score_i
        net_front_j = front_score_j - handicap_ij
        if net_front_i < net_front_j:
            # 修正: iの方がスコアが低い（良い）場合はプラスポイント
            front_pt = 10
        elif net_front_i > net_front_j:
            # 修正: iの方がスコアが高い（悪い）場合はマイナスポイント
            front_pt = -10
            
        # バックスコアの比較（両方のスコアが入力されている場合のみ）
        if has_back:
            # バック9にもハーフ分のハンディキャップをそのまま適用
            net_back_i = back_score_i
            net_back_j = back_score_j - handicap_ij
            if net_back_i < net_back_j:
                back_pt = 10
            elif net_back_i > net_back_j:
                back_pt = -10
            
            # トータルスコアはバックスコアが入力されている場合のみ比較
            # 18ホール分のハンディキャップを適用するため、handicap_ij * 2
            net_total_i = front_score_i + back_score_i
            net_total_j = (front_score_j + back_score_j) - (handicap_ij * 2)
            if net_total_i < net_total_j:
                total_pt = 10
            elif net_total_i > net_total_j:
                total_pt = -10
        else:
            # バックが入力されていない場合、バックとトータルのポイントは計算しない
            back_pt = 0
            total_pt = 0
                
        # エキストラスコアの比較（両方プレイしている場合のみ）
        if has_extra:
            # ハンディキャップはハーフ分をそのまま適用
            net_extra_i = extra_score_i
            net_extra_j = extra_score_j - handicap_ij
            if net_extra_i < net_extra_j:
                extra_pt = 10
            elif net_extra_i > net_extra_j:
                extra_pt = -10
        else:
            extra_pt = 0

    # 合計ポイントを計算
    total_points_i = front_pt + back_pt + total_pt + extra_pt
    total_points_j = -(front_pt + back_pt + total_pt + extra_pt)

    # デバッグ情報を追加
    st.write("### デバッグ情報（修正版）")
    st.write(f"Player i: {player_i['member']['name'] if 'member' in player_i else '不明'}")
    st.write(f"Player j: {player_j['member']['name'] if 'member' in player_j else '不明'}")
    
    # 修正したハンディキャップ表示
    st.write(f"Handicap i→j: {handicap_ij}")
    st.write(f"Front score i: {front_score_i}")
    st.write(f"Front score j: {front_score_j} - {handicap_ij} = {front_score_j - handicap_ij}")
    st.write(f"Front pt: {front_pt}")
    
    if has_back:
        st.write(f"Back score i: {back_score_i}")
        st.write(f"Back score j: {back_score_j} - {handicap_ij} = {back_score_j - handicap_ij}")
        st.write(f"Back pt: {back_pt}")
        st.write(f"Total score i: {front_score_i + back_score_i}")
        st.write(f"Total score j: {front_score_j + back_score_j} - {handicap_ij} = {front_score_j + back_score_j - handicap_ij}")
        st.write(f"Total pt: {total_pt}")
    
    if has_extra:
        st.write(f"Extra score i: {extra_score_i}")
        st.write(f"Extra score j: {extra_score_j} - {handicap_ij} = {extra_score_j - handicap_ij}")
        st.write(f"Extra pt: {extra_pt}")
    
    st.write(f"Total points i: {total_points_i}")
    st.write(f"Total points j: {total_points_j}")
    
    return total_points_i, total_points_j, {
        "front": front_pt,
        "back": back_pt, 
        "total": total_pt,
        "extra": extra_pt,
        "has_back": has_back,
        "has_extra": has_extra
    }

def main():
    st.title("マッチポイント計算の検証")
    
    # ラウンドID選択機能を追加
    st.sidebar.header("ラウンド選択")
    
    # 最新ラウンドを取得
    rounds_result = supabase.table('rounds').select('*').order('date_played', desc=True).limit(20).execute()
    if not rounds_result.data:
        st.error("ラウンドデータが見つかりません")
        return
        
    rounds = rounds_result.data
    round_options = [(r['round_id'], f"{r['date_played']} - {r['course_name']} (ID: {r['round_id']})") for r in rounds]
    
    # デフォルトでID 41を選択
    default_index = next((i for i, (rid, _) in enumerate(round_options) if rid == 41), 0)
    
    selected_round = st.sidebar.selectbox(
        "検証するラウンドを選択",
        options=round_options,
        index=default_index,
        format_func=lambda x: x[1]
    )
    
    # 選択されたラウンドID
    round_id = selected_round[0]
    
    # ラウンドデータ取得
    round_result = supabase.table('rounds').select('*').eq('round_id', round_id).execute()
    if not round_result.data:
        st.error(f"ラウンドID {round_id} が見つかりません")
        return
        
    round_data = round_result.data[0]
    st.write(f"### {round_data['date_played']} - {round_data['course_name']} (ID: {round_id})")
    
    # スコアデータ取得
    scores_result = supabase.table('score').select('*, member:member_id(name)').eq('round_id', round_id).execute()
    if not scores_result.data:
        st.error("スコアデータが見つかりません")
        return
        
    scores = scores_result.data
    
    # プレイヤー選択
    player_names = [score['member']['name'] for score in scores]
    selected_player = st.selectbox("プレイヤーを選択", options=player_names, index=player_names.index('荒巻') if '荒巻' in player_names else 0)
    
    # スコアデータをプレーヤー名でアクセスしやすいように整理
    players = {}
    for score in scores:
        player_name = score['member']['name']
        players[player_name] = score
        players[score['member_id']] = score
    
    # ハンディキャップデータ取得
    handicaps_result = supabase.table('handicap_match').select(
        '*', 
        'player1:member!player_1_id(name)',
        'player2:member!player_2_id(name)'
    ).eq('round_id', round_id).execute()
    
    if not handicaps_result.data:
        st.error("ハンディキャップデータが見つかりません")
        return
        
    handicaps = handicaps_result.data
    
    # ハンディキャップデータを表示
    st.write("### ハンディキャップ設定")
    
    handicap_records = []
    for h in handicaps:
        handicap_records.append({
            "プレーヤー1": h['player1']['name'],
            "プレーヤー2": h['player2']['name'],
            "P1→P2": h['player_1_to_2'],
            "P2→P1": h['player_2_to_1'],
            "Total Only": "はい" if h['total_only'] else "いいえ"
        })
    
    st.dataframe(pd.DataFrame(handicap_records))
    
    # スコアデータを表示
    st.write("### スコアデータ")
    
    score_records = []
    for score in scores:
        score_records.append({
            "プレーヤー": score['member']['name'],
            "FRONT": score['front_score'],
            "BACK": score['back_score'],
            "TOTAL": score['front_score'] + score['back_score'],
            "EXTRA": score['extra_score'],
            "Match Pt": score['match_pt']
        })
    
    st.dataframe(pd.DataFrame(score_records))
    
    # 選択されたプレイヤーのマッチポイント検証
    st.write(f"### {selected_player}さんのマッチポイント検証")
    
    # 選択されたプレイヤーのスコアを取得
    player_score = next((s for s in scores if s['member']['name'] == selected_player), None)
    if not player_score:
        st.error(f"{selected_player}さんのスコアが見つかりません")
        return
        
    # 選択されたプレイヤーの対戦相手のマッチポイント計算
    st.write(f"#### {selected_player}さん vs 他プレーヤーのマッチポイント計算")
    
    match_results = []
    player_total_pts = 0
    
    for h in handicaps:
        if h['player1']['name'] == selected_player:
            opponent_id = h['player_2_id']
            opponent = players[opponent_id]
            handicap_ij = h['player_1_to_2']
            handicap_ji = h['player_2_to_1']
            is_total_only = h['total_only']
            
            # マッチポイントを再計算
            pts_i, pts_j, details = calculate_match_points(
                player_score, opponent, 
                handicap_ij, handicap_ji, 
                is_total_only
            )
            
            player_total_pts += pts_i
            
            match_results.append({
                "対戦相手": opponent['member']['name'],
                "FRONT差分": f"{player_score['front_score']}(-{handicap_ij//2}) vs {opponent['front_score']}(-{handicap_ji//2})",
                "FRONT Pt": details['front'],
                "BACK差分": f"{player_score['back_score']}(-{handicap_ij-handicap_ij//2}) vs {opponent['back_score']}(-{handicap_ji-handicap_ji//2})",
                "BACK Pt": details['back'],
                "TOTAL差分": f"{player_score['front_score']+player_score['back_score']}(-{handicap_ij*2}) vs {opponent['front_score']+opponent['back_score']}(-{handicap_ji*2})",
                "TOTAL Pt": details['total'],
                "EXTRA Pt": details['extra'],
                "Total Only": "はい" if is_total_only else "いいえ",
                f"{selected_player} Pt": pts_i,
                "対戦相手 Pt": pts_j
            })
            
        elif h['player2']['name'] == selected_player:
            opponent_id = h['player_1_id']
            opponent = players[opponent_id]
            handicap_ij = h['player_2_to_1']
            handicap_ji = h['player_1_to_2']
            is_total_only = h['total_only']
            
            # マッチポイントを再計算
            pts_i, pts_j, details = calculate_match_points(
                player_score, opponent, 
                handicap_ij, handicap_ji, 
                is_total_only
            )
            
            player_total_pts += pts_i
            
            match_results.append({
                "対戦相手": opponent['member']['name'],
                "FRONT差分": f"{player_score['front_score']}(-{handicap_ij//2}) vs {opponent['front_score']}(-{handicap_ji//2})",
                "FRONT Pt": details['front'],
                "BACK差分": f"{player_score['back_score']}(-{handicap_ij-handicap_ij//2}) vs {opponent['back_score']}(-{handicap_ji-handicap_ji//2})",
                "BACK Pt": details['back'],
                "TOTAL差分": f"{player_score['front_score']+player_score['back_score']}(-{handicap_ij*2}) vs {opponent['front_score']+opponent['back_score']}(-{handicap_ji*2})",
                "TOTAL Pt": details['total'],
                "EXTRA Pt": details['extra'],
                "Total Only": "はい" if is_total_only else "いいえ",
                f"{selected_player} Pt": pts_i,
                "対戦相手 Pt": pts_j
            })
    
    # 検証結果を表示
    st.dataframe(pd.DataFrame(match_results))
    
    # 結論
    st.write("#### 検証結果")
    st.write(f"再計算した{selected_player}さんのマッチポイント合計: **{player_total_pts}**")
    st.write(f"データベース上の{selected_player}さんのマッチポイント: **{player_score['match_pt']}**")
    
    if player_total_pts != player_score['match_pt']:
        st.error(f"不一致があります: {player_total_pts} ≠ {player_score['match_pt']}")
        
        # 修正オプション
        if st.button("マッチポイントを修正する"):
            try:
                # 選択されたプレイヤーのスコアを更新
                supabase.table('score').update({
                    'match_pt': player_total_pts
                }).eq('score_id', player_score['score_id']).execute()
                
                # total_ptも更新
                game_pt = (player_score.get('front_game_pt') or 0) + (player_score.get('back_game_pt') or 0) + (player_score.get('extra_game_pt') or 0)
                putt_pt = player_score.get('putt_pt') or 0
                total_pt = game_pt + player_total_pts + putt_pt
                
                supabase.table('score').update({
                    'total_pt': total_pt
                }).eq('score_id', player_score['score_id']).execute()
                
                st.success(f"{selected_player}さんのマッチポイントを {player_score['match_pt']} から {player_total_pts} に修正しました")
                st.success(f"Total Ptも {player_score.get('total_pt')} から {total_pt} に更新しました")
                
                # 再読み込み
                st.rerun()
            except Exception as e:
                st.error(f"更新中にエラーが発生しました: {str(e)}")
    else:
        st.success("マッチポイントの計算は正確です")

    # 計算ロジックをさらに詳しく表示
    st.write("### 計算ロジックの詳細検証")
    st.write("スコアが低い方がプラスポイントを獲得することを確認します")
    
    # デバッグ用に荒巻さんのスコアのみ集中的に検証
    if '荒巻' in player_names:
        aramaki_score = next((s for s in scores if s['member']['name'] == '荒巻'), None)
        
        # 詳細な対戦内容を表形式で表示
        st.write("#### 荒巻さんの対戦詳細")
        
        # 全ての対戦データを表示
        detailed_matches = []
        for h in handicaps:
            if h['player1']['name'] == '荒巻':
                opponent_id = h['player_2_id']
                opponent = players[opponent_id]
                handicap_ij = h['player_1_to_2']
                handicap_ji = h['player_2_to_1']
                is_total_only = h['total_only']
                
                # ネットスコア計算（ハンディキャップをそのまま適用）
                net_front_i = aramaki_score['front_score']
                net_front_j = opponent['front_score'] - handicap_ij
                
                detailed_matches.append({
                    '対戦': f"荒巻 vs {opponent['member']['name']}",
                    '荒巻Front': aramaki_score['front_score'],
                    'ハンデ': handicap_ij,  # 2で割らない
                    'ネット': net_front_i,
                    '相手Front': opponent['front_score'],
                    '相手ハンデ': handicap_ji,  # 2で割らない
                    '相手ネット': net_front_j,
                    'Total Only': "はい" if is_total_only else "いいえ",
                    '荒巻勝ち?': "はい" if net_front_i < net_front_j else "いいえ",
                    '結果PT': 10 if net_front_i < net_front_j else (-10 if net_front_i > net_front_j else 0)
                })
                
            elif h['player2']['name'] == '荒巻':
                opponent_id = h['player_1_id']
                opponent = players[opponent_id]
                handicap_ij = h['player_2_to_1']
                handicap_ji = h['player_1_to_2']
                is_total_only = h['total_only']
                
                # ネットスコア計算（ハンディキャップをそのまま適用）
                net_front_i = aramaki_score['front_score']
                net_front_j = opponent['front_score'] - handicap_ij
                
                detailed_matches.append({
                    '対戦': f"荒巻 vs {opponent['member']['name']}",
                    '荒巻Front': aramaki_score['front_score'],
                    'ハンデ': handicap_ij,  # 2で割らない
                    'ネット': net_front_i,
                    '相手Front': opponent['front_score'],
                    '相手ハンデ': handicap_ji,  # 2で割らない
                    '相手ネット': net_front_j,
                    'Total Only': "はい" if is_total_only else "いいえ",
                    '荒巻勝ち?': "はい" if net_front_i < net_front_j else "いいえ",
                    '結果PT': 10 if net_front_i < net_front_j else (-10 if net_front_i > net_front_j else 0)
                })
                
        # データフレームとして表示
        if detailed_matches:
            st.dataframe(pd.DataFrame(detailed_matches))

if __name__ == "__main__":
    main()
