from modules.score_calculator import calc_putt_points, calc_match_points_by_section, calc_match_points
from modules.round_results import save_round_results

def calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round):
    """プレイヤーのポイントを計算"""
    result = {pid: player_data[pid].copy() for pid in player_ids}
    
    # パットスコアでポイント計算
    # キー名の互換性を確保するために get() を使う
    front_putt = {mid: player_data[mid].get("Front Putt", player_data[mid].get("Putt Front", 0)) for mid in player_data}
    back_putt = {mid: player_data[mid].get("Back Putt", player_data[mid].get("Putt Back", 0)) for mid in player_data}
    extra_putt = {mid: player_data[mid].get("Extra Putt", player_data[mid].get("Putt Extra", 0)) for mid in player_data}
    
    # 実際にExtra Puttのスコアがあるか確認
    has_actual_extra = any(score > 0 for score in extra_putt.values())

    putt_front_points = calc_putt_points(front_putt, len(player_ids))
    putt_back_points = calc_putt_points(back_putt, len(player_ids))
    putt_extra_points = calc_putt_points(extra_putt, len(player_ids) if has_actual_extra else {mid: 0 for mid in player_data})

    # 計算結果をデバッグ出力
    print("Front Putt:", front_putt)
    print("Front Putt Points:", putt_front_points)
    print("Back Putt:", back_putt)
    print("Back Putt Points:", putt_back_points)
    print("Extra Putt:", extra_putt)
    print("Extra Putt Points:", putt_extra_points)

    for mid in player_data:
        data = player_data[mid]
        pf = putt_front_points.get(mid, 0)
        pb = putt_back_points.get(mid, 0)
        pe = putt_extra_points.get(mid, 0)
        data["Putt Pt"] = pf + pb + pe 

    # Game Ptの計算
    front_scores = {pid: player_data[pid].get("Front Score", 0) for pid in player_ids}
    back_scores = {pid: player_data[pid].get("Back Score", 0) for pid in player_ids}
    extra_scores = {pid: player_data[pid].get("Extra Score", 0) for pid in player_ids}

    sorted_front = sorted(front_scores.items(), key=lambda x: (x[1], x[0]))
    if len(player_ids) == 3:
        player_data[sorted_front[0][0]]["Front GP"] = 30
        player_data[sorted_front[1][0]]["Front GP"] = 0
        player_data[sorted_front[2][0]]["Front GP"] = -30
    else:
        player_data[sorted_front[0][0]]["Front GP"] = 30
        player_data[sorted_front[1][0]]["Front GP"] = 10
        player_data[sorted_front[2][0]]["Front GP"] = -10
        player_data[sorted_front[3][0]]["Front GP"] = -30

    sorted_back = sorted(back_scores.items(), key=lambda x: (x[1], x[0]))
    if len(player_ids) == 3:
        player_data[sorted_back[0][0]]["Back GP"] = 30
        player_data[sorted_back[1][0]]["Back GP"] = 0
        player_data[sorted_back[2][0]]["Back GP"] = -30
    else:
        player_data[sorted_back[0][0]]["Back GP"] = 30
        player_data[sorted_back[1][0]]["Back GP"] = 10
        player_data[sorted_back[2][0]]["Back GP"] = -10
        player_data[sorted_back[3][0]]["Back GP"] = -30

    if active_round.get('has_extra', False):
        sorted_extra = sorted(extra_scores.items(), key=lambda x: (x[1], x[0]))
        if len(player_ids) == 3:
            player_data[sorted_extra[0][0]]["Extra GP"] = 30
            player_data[sorted_extra[1][0]]["Extra GP"] = 0
            player_data[sorted_extra[2][0]]["Extra GP"] = -30
        else:
            player_data[sorted_extra[0][0]]["Extra GP"] = 30
            player_data[sorted_extra[1][0]]["Extra GP"] = 10
            player_data[sorted_extra[2][0]]["Extra GP"] = -10
            player_data[sorted_extra[3][0]]["Extra GP"] = -30

    temp_game_pts = {}
    for mid in player_ids:
        fgp = player_data[mid]["Front GP"]
        bgp = player_data[mid]["Back GP"]
        egp = player_data[mid].get("Extra GP", 0)
        temp_game_pts[mid] = fgp + bgp + egp
        player_data[mid]["temp_game_pt"] = temp_game_pts[mid]

    print("Debug - Temp Game Points:", temp_game_pts)

    for mid in player_ids:
        if len(player_ids) == 3:
            my_total = temp_game_pts[mid]
            others_total = sum(temp_game_pts[oid] for oid in temp_game_pts if oid != mid)
            total_game_pt = my_total * 2 - others_total
            player_data[mid]["total_game_pt"] = total_game_pt
            player_data[mid]["Game Pt"] = total_game_pt
        else:
            player_data[mid]["total_game_pt"] = temp_game_pts[mid]
            player_data[mid]["Game Pt"] = temp_game_pts[mid]

    print("Debug - Final Game Points:", {mid: player_data[mid]["Game Pt"] for mid in player_ids})

    for mid in player_data:
        player_data[mid]["Match Front"] = 0
        player_data[mid]["Match Back"] = 0
        player_data[mid]["Match Total"] = 0
        player_data[mid]["Match Extra"] = 0
        player_data[mid]["Match Pt"] = 0

    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            pair_key = frozenset([pid_i, pid_j])

            handicap_ij_val = handicaps.get((pid_j, pid_i), 0)
            handicap_ji_val = handicaps.get((pid_i, pid_j), 0)

            if pair_key in total_only_set:
                pts = calc_match_points(data_i, data_j, handicap_ij_val, handicap_ji_val, is_total_only=True)
            else:
                pts = calc_match_points(data_i, data_j, handicap_ij_val, handicap_ji_val, is_total_only=False)
            data_i["Match Front"] += pts["Match Front"]
            data_i["Match Back"] += pts["Match Back"]
            data_i["Match Total"] += pts["Match Total"]
            data_i["Match Extra"] += pts["Match Extra"]
            data_j["Match Front"] -= pts["Match Front"]
            data_j["Match Back"] -= pts["Match Back"]
            data_j["Match Total"] -= pts["Match Total"]
            data_j["Match Extra"] -= pts["Match Extra"]
            data_i["Match Pt"] += pts["Total"]
            data_j["Match Pt"] -= pts["Total"]

    for mid in player_data:
        d = player_data[mid]
        d["Total Pt"] = d["Game Pt"] + d["Match Pt"] + d["Putt Pt"]

    round_id = active_round.get('round_id')
    is_test_round = round_id > 900  # テスト用IDは通常900以上と仮定
    
    if not is_test_round and round_id:
        if save_round_results(round_id, player_data):
            print(f"Successfully saved round results for round_id: {round_id}")
        else:
            print(f"Failed to save round results for round_id: {round_id}")

    return player_data

def calculate_match_points_for_section(data_i, data_j, pid_i, pid_j, handicaps, section, active_round):
    """特定のセクションのマッチポイントを計算"""
    points = calc_match_points_by_section(
        data_i, data_j,
        handicaps.get((pid_j, pid_i), 0),
        handicaps.get((pid_i, pid_j), 0),
        section
    )
    if points is not None:
        print(f"Section: {section}, Player {pid_i} vs {pid_j}, Points: {points}")
        data_i["Match " + section] += points
        data_j["Match " + section] -= points
