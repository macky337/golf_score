import copy
import pandas as pd
from modules.score_calculator import calc_match_points

def create_match_matrix(player_data, handicaps, total_only_set, rules=None):
    # 累積前の元データ（Front, Back, Extra, Total）のみを抽出して使用する
    raw_data = {}
    for pid, data in player_data.items():
        raw_data[pid] = {
            "Front Score": data["Front Score"],
            "Back Score": data["Back Score"],
            "Extra Score": data["Extra Score"],
            "Total Score": data["Total Score"],
        }
    player_ids = sorted(list(raw_data.keys()))
    # 表示用のプレイヤー名は元のplayer_dataから取得
    players = [player_data[pid]["Player"] for pid in player_ids]
    matrix = {player_data[pid]["Player"]: {} for pid in player_ids}
    for i in range(len(player_ids)):
        for j in range(len(player_ids)):
            if i == j:
                matrix[players[i]][players[i]] = ""
            else:
                pid_i = player_ids[i]
                pid_j = player_ids[j]
                if i < j:
                    pair_key = frozenset([pid_i, pid_j])
                    pts = calc_match_points(
                        raw_data[pid_i], raw_data[pid_j],
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        is_total_only=(pair_key in total_only_set),
                        rules=rules,
                    )
                    # ptsは辞書なので、Total を使用
                    matrix[player_data[pid_i]["Player"]][player_data[pid_j]["Player"]] = -pts["Total"]
                    matrix[player_data[pid_j]["Player"]][player_data[pid_i]["Player"]] = pts["Total"]
    return pd.DataFrame(matrix)

def create_detailed_match_results(player_data, handicaps, total_only_set, rules=None):
    """マッチ戦の詳細結果を作成（横：対戦カード、縦：プレイヤーのポイント）"""
    # member_idの昇順に並べ替え済みのプレイヤーIDリスト
    player_ids = sorted(list(player_data.keys()))
    n_players = len(player_ids)
    match_results = {}
    matches = []
    multi_columns = []
    
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            match_name = f"{player_data[pid_i]['Player']} vs {player_data[pid_j]['Player']}"
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            # Total Onlyモードかどうかを判定
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            handicap_str = f"{handicap_ij} vs {handicap_ji}"
            if is_total_only:
                handicap_str += " (Total Only)"
            matches.append(match_name)
            multi_columns.append((match_name, handicap_str))
    
    # プレイヤーごとの結果を初期化（player_idsの順序通りに）    
    for pid in player_ids:
        match_results[player_data[pid]["Player"]] = {match: "-" for match in matches}
    
    # 対戦結果を計算して格納
    for i in range(n_players-1):
        for j in range(i+1, n_players):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            match_name = f"{data_i['Player']} vs {data_j['Player']}"
            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)
            is_total_only = frozenset([pid_i, pid_j]) in total_only_set
            
            points = calc_match_points(
                data_i,
                data_j,
                handicap_ij,
                handicap_ji,
                is_total_only,
                rules=rules,
            )
            
            match_results[data_i["Player"]][match_name] = f"{points['Total']:+d}" if points["Total"] != 0 else "0"
            match_results[data_j["Player"]][match_name] = f"{-points['Total']:+d}" if points["Total"] != 0 else "0"
    
    # DataFrameを作成し、元のplayer_idsの順序を保持するためにインデックスを再整列
    df = pd.DataFrame.from_dict(match_results, orient='index')
    ordered_players = [player_data[pid]["Player"] for pid in player_ids]
    df = df.reindex(ordered_players)
    
    # カラム数をチェックして一致していることを確認
    if len(df.columns) != len(multi_columns):
        import streamlit as st
        st.warning(f"カラム数の不一致: DataFrame列数={len(df.columns)}, マルチインデックス数={len(multi_columns)}")
        # 不一致の場合は単純なカラム名を使用
        return df
    
    df.columns = pd.MultiIndex.from_tuples(multi_columns, names=['Match', 'Handicap'])
    return df
