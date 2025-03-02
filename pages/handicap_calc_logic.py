import streamlit as st

def safe_get_score(data, key):
    """スコア取得時、Noneや例外発生時は 0 を返す"""
    try:
        value = data.get(key, 0)
        if value is None:
            return 0
        return value
    except Exception:
        return 0

def calc_net_score(data, key, handicap, multiplier=1):
    """指定されたセクションのスコアから、ハンディキャップ（multiplier 倍）を差し引いた値を返す"""
    score = safe_get_score(data, key)
    try:
        return score - (handicap * multiplier)
    except Exception:
        return 0

def calc_net_total(data, handicap, multiplier=2):
    """FrontとBackのスコアの合計から、ハンディキャップ（multiplier 倍）を差し引いた値を返す"""
    front = safe_get_score(data, "Front Score")
    back = safe_get_score(data, "Back Score")
    return front + back - (handicap * multiplier)

def calc_net_extra(data, handicap, multiplier=1):
    """Extraスコアから、ハンディキャップ（multiplier 倍）を差し引いた値を返す"""
    extra = safe_get_score(data, "Extra Score")
    return extra - (handicap * multiplier)

def calc_putt_points(putt_scores, n):
    """パット戦の得点計算（4人 or 3人の場合）"""
    if not putt_scores:  # スコアが空の場合
        return {}
        
    scores = list(putt_scores.values())
    min_score = min(scores)
    winners = [m_id for m_id, score in putt_scores.items() if score == min_score]
    points = {m_id: 0 for m_id in putt_scores}
    
    if n == 3:
        if len(winners) == 1:
            points[winners[0]] = 20  # 最少が1名の場合は+20pt
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10  # 残り2名は-10pt
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 5  # 最少が2名の場合は+5pt
                else:
                    points[m_id] = -10  # 残り1名は-10pt
    
    elif n == 4:
        if len(winners) == 1:
            points[winners[0]] = 30  # 最少が1名の場合は+30pt
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = -10  # 残り3名は-10pt
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10  # 最少が2名の場合は+10pt
                else:
                    points[m_id] = -10  # 残り2名は-10pt
        elif len(winners) == 3:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = 10  # 最少が3名の場合は+10pt
                else:
                    points[m_id] = -30  # 残り1名は-30pt
    
    return points

def calc_match_points_by_section(player_i, player_j, handicap_ij, handicap_ji, section):
    """セクション（Front/Back/Total/Extra）ごとのマッチポイントを計算"""
    if section == "Front":
        score_i = player_i["Front Score"] - handicap_ij//2
        score_j = player_j["Front Score"] - handicap_ji//2
    elif section == "Back":
        score_i = player_i["Back Score"] - (handicap_ij - handicap_ij//2)
        score_j = player_j["Back Score"] - (handicap_ji - handicap_ji//2)
    elif section == "Total":
        # ハンディキャップは2倍だが、ポイントは各セクションと同じ10ポイント
        score_i = player_i["Total Score"] - handicap_ij * 2
        score_j = player_j["Total Score"] - handicap_ji * 2
    else:  # Extra
        score_i = player_i["Extra Score"] - handicap_ij
        score_j = player_j["Extra Score"] - handicap_ji
    
    if score_i < score_j:
        return 10
    elif score_i > score_j:
        return -10
    return 0

def process_round_scores(scores, handicaps_data, round_data):
    """ラウンドのスコアを計算"""
    # プレーヤーデータの準備
    player_data = {}
    for sc in scores:
        # 名前を取得する
        player_name = None
        if 'name' in sc:
            player_name = sc['name']
        elif 'member' in sc and isinstance(sc['member'], dict) and 'name' in sc['member']:
            player_name = sc['member']['name']
        else:
            player_name = f"Player {sc.get('member_id', 'Unknown')}"
            
        player_data[sc['member_id']] = {
            "Player": player_name,
            "Front Score": sc['front_score'],
            "Back Score": sc['back_score'],
            "Extra Score": sc['extra_score'],
            "Total Score": sc['front_score'] + sc['back_score'],
            "Front GP": sc.get('front_game_pt', 0),
            "Back GP": sc.get('back_game_pt', 0),
            "Extra GP": sc.get('extra_game_pt', 0),
            "Game Pt": 0,
            "Match Front": 0,
            "Match Back": 0,
            "Match Total": 0,
            "Match Extra": 0,
            "Match Pt": 0,
            "Putt Front": sc['front_putt'] or 0,
            "Putt Back": sc['back_putt'] or 0,
            "Putt Extra": sc.get('extra_putt', 0) or 0,
            "Put Pt": 0,
        }
    
    # member_idの昇順にプレイヤーIDのリストを並べ替え
    player_ids = sorted(list(player_data.keys()))
    n_players = len(player_ids)
    
    # ハンディキャップの準備
    handicaps = {}
    total_only_set = set() 
    for h in handicaps_data:
        handicaps[(h['player_1_id'], h['player_2_id'])] = h['player_1_to_2']
        # もう一方向のハンディキャップ値も追加（プレイヤー2→プレイヤー1）
        if 'player_2_to_1' in h:
            handicaps[(h['player_2_id'], h['player_1_id'])] = h['player_2_to_1']
        
        if 'total_only' in h and h['total_only']:
            total_only_set.add(frozenset([h['player_1_id'], h['player_2_id']]))
    
    # パットポイントの計算
    front_putt = {mid: player_data[mid]["Putt Front"] for mid in player_data}
    back_putt = {mid: player_data[mid]["Putt Back"] for mid in player_data}
    extra_putt = {mid: player_data[mid]["Putt Extra"] for mid in player_data} if round_data.get('has_extra') else None
    
    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points = calc_putt_points(back_putt, n_players)
    putt_extra_points = calc_putt_points(extra_putt, n_players) if extra_putt else {mid: 0 for mid in player_data}
    
    # 各プレイヤーのパットポイント合計を計算
    for mid in player_data:
        data = player_data[mid]
        pf = putt_front_points.get(mid, 0)
        pb = putt_back_points.get(mid, 0)
        pe = putt_extra_points.get(mid, 0)
        data["Put Pt"] = pf + pb + pe
    
    # Game Ptの計算
    temp_game_pts = {}
    for mid in player_data:
        fgp = player_data[mid]["Front GP"]
        bgp = player_data[mid]["Back GP"]
        egp = player_data[mid]["Extra GP"]
        temp_game_pts[mid] = fgp + bgp + egp
        
    if n_players == 3:
        # 3人の場合、各プレイヤーの最終Game Ptを再計算
        for mid in player_data:
            my_total = temp_game_pts[mid]
            others_total = sum(temp_game_pts[oid] for oid in temp_game_pts if oid != mid)
            player_data[mid]["Game Pt"] = my_total * 2 - others_total
    else:
        # 3人以外の場合は一時的なポイントをそのまま使用
        for mid in player_data:
            player_data[mid]["Game Pt"] = temp_game_pts[mid]
    
    # マッチポイントの計算
    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            pair_key = frozenset([pid_i, pid_j])
            
            # total_onlyモードの処理
            if pair_key in total_only_set:
                # Total Onlyモード - TotalとExtraだけ計算
                # Total
                points = calc_match_points_by_section(
                    data_i, data_j,
                    handicaps.get((pid_j, pid_i), 0),
                    handicaps.get((pid_i, pid_j), 0),
                    "Total"
                )
                data_i["Match Total"] += points
                data_j["Match Total"] -= points
                data_i["Match Pt"] += points
                data_j["Match Pt"] -= points
                
                # Extra (if exists)
                if round_data.get('has_extra'):
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Extra"
                    )
                    data_i["Match Extra"] += points
                    data_j["Match Extra"] -= points
                    data_i["Match Pt"] += points
                    data_j["Match Pt"] -= points
            else:
                # 通常モード（Front, Back, Total, Extra別々に勝敗を決める）
                # Front
                points = calc_match_points_by_section(
                    data_i, data_j,
                    handicaps.get((pid_j, pid_i), 0),
                    handicaps.get((pid_i, pid_j), 0),
                    "Front"
                )
                data_i["Match Front"] += points
                data_j["Match Front"] -= points
                data_i["Match Pt"] += points
                data_j["Match Pt"] -= points
                
                # Back
                points = calc_match_points_by_section(
                    data_i, data_j,
                    handicaps.get((pid_j, pid_i), 0),
                    handicaps.get((pid_i, pid_j), 0),
                    "Back"
                )
                data_i["Match Back"] += points
                data_j["Match Back"] -= points
                data_i["Match Pt"] += points
                data_j["Match Pt"] -= points
                
                # Total
                points = calc_match_points_by_section(
                    data_i, data_j,
                    handicaps.get((pid_j, pid_i), 0),
                    handicaps.get((pid_i, pid_j), 0),
                    "Total"
                )
                data_i["Match Total"] += points
                data_j["Match Total"] -= points
                data_i["Match Pt"] += points
                data_j["Match Pt"] -= points
                
                # Extra (if exists)
                if round_data.get('has_extra'):
                    points = calc_match_points_by_section(
                        data_i, data_j,
                        handicaps.get((pid_j, pid_i), 0),
                        handicaps.get((pid_i, pid_j), 0),
                        "Extra"
                    )
                    data_i["Match Extra"] += points
                    data_j["Match Extra"] -= points
                    data_i["Match Pt"] += points
                    data_j["Match Pt"] -= points
    
    # 最終的なトータルポイントの計算
    for mid in player_data:
        d = player_data[mid]
        d["Total Pt"] = d["Game Pt"] + d["Match Pt"] + d["Put Pt"]
    
    # 更新用データ形式に変換
    result_scores = []
    for mid in player_ids:  # player_idsを使って順序を保証
        player_idx = None
        for idx, score in enumerate(scores):
            if score['member_id'] == mid:
                player_idx = idx
                break
                
        if player_idx is not None:
            score_data = dict(scores[player_idx])  # 該当するスコアデータをコピー
            score_data.update({
                'game_pt': player_data[mid]['Game Pt'],
                'match_pt': player_data[mid]['Match Pt'],
                'put_pt': player_data[mid]['Put Pt'],
                'total_pt': player_data[mid]['Total Pt']
            })
            result_scores.append(score_data)
    
    return result_scores
