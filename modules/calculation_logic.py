from modules.score_calculator import calc_putt_points, calc_match_points_by_section, calc_match_points

def calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round):
    """
    プレイヤーのポイントを計算するメイン関数
    """
    n_players = len(player_ids)

    front_putt = {mid: player_data[mid]["Putt Front"] for mid in player_data}
    back_putt = {mid: player_data[mid]["Putt Back"] for mid in player_data}
    extra_putt = {mid: player_data[mid].get("Putt Extra", 0) for mid in player_data} if active_round['has_extra'] else None

    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points = calc_putt_points(back_putt, n_players)
    putt_extra_points = calc_putt_points(extra_putt, n_players) if extra_putt else {mid: 0 for mid in player_data}

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
        player_data[mid]["Temp Game Pt"] = temp_game_pts[mid]

    if n_players == 3:
        for mid in player_data:
            my_total = temp_game_pts[mid]
            others_total = sum(temp_game_pts[oid] for oid in temp_game_pts if oid != mid)
            player_data[mid]["Game Pt"] = my_total * 2 - others_total
    else:
        for mid in player_data:
            player_data[mid]["Game Pt"] = temp_game_pts[mid]

    # Match Pt計算初期化
    for mid in player_data:
        player_data[mid]["Match Front"] = 0
        player_data[mid]["Match Back"] = 0
        player_data[mid]["Match Total"] = 0
        player_data[mid]["Match Extra"] = 0
        player_data[mid]["Match Pt"] = 0

    # マッチポイント計算
    for i in range(len(player_ids)):
        for j in range(i+1, len(player_ids)):
            pid_i = player_ids[i]
            pid_j = player_ids[j]
            data_i = player_data[pid_i]
            data_j = player_data[pid_j]
            pair_key = frozenset([pid_i, pid_j])

            handicap_ij = handicaps.get((pid_j, pid_i), 0)
            handicap_ji = handicaps.get((pid_i, pid_j), 0)

            if pair_key in total_only_set:
                # Total Onlyモード
                total_points_i, total_points_j = calc_match_points(data_i, data_j, handicap_ij, handicap_ji, is_total_only=True)
                data_i["Match Pt"] += total_points_i
                data_j["Match Pt"] += total_points_j
            else:
                # 通常モード
                total_points_i, total_points_j = calc_match_points(data_i, data_j, handicap_ij, handicap_ji, is_total_only=False)
                data_i["Match Pt"] += total_points_i
                data_j["Match Pt"] += total_points_j

    for mid in player_data:
        d = player_data[mid]
        d["Total Pt"] = d["Game Pt"] + d["Match Pt"] + d["Put Pt"]

    return player_data

def calculate_match_points_for_section(data_i, data_j, pid_i, pid_j, handicaps, section, active_round):
    """
    特定のセクションのマッチポイントを計算する関数
    """
    points = calc_match_points_by_section(
        data_i, data_j,
        handicaps.get((pid_j, pid_i), 0),
        handicaps.get((pid_i, pid_j), 0),
        section
    )
    if points is not None:
        print(f"Section: {section}, Player {pid_i} vs {pid_j}, Points: {points}") # Debugging
        data_i["Match " + section] += points
        data_j["Match " + section] -= points
