from modules.score_calculator import calc_putt_points, calc_match_points_by_section, calc_match_points

def calculate_player_points(player_data, player_ids, handicaps, total_only_set, active_round):
    """
    プレイヤーのポイントを計算するメイン関数
    """
    n_players = len(player_ids)

    # パットスコアを常に辞書として取得、Extra Putt も含めて処理する
    front_putt = {mid: player_data[mid]["Front Putt"] for mid in player_data}
    back_putt = {mid: player_data[mid]["Back Putt"] for mid in player_data}
    # Extra Puttは必ず辞書として作成し、実際の値に基づいて計算
    extra_putt = {mid: player_data[mid].get("Extra Putt", 0) for mid in player_data}
    
    # 実際にExtra Puttのスコアがあるか確認
    has_actual_extra = any(score > 0 for score in extra_putt.values())

    putt_front_points = calc_putt_points(front_putt, n_players)
    putt_back_points = calc_putt_points(back_putt, n_players)
    # Extra Puttが実際に値を持つ場合のみ計算
    putt_extra_points = calc_putt_points(extra_putt, n_players) if has_actual_extra else {mid: 0 for mid in player_data}

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
        # "Putt Pt" として正しいキーを使用
        data["Putt Pt"] = pf + pb + pe 

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

    # Match Pt計算初期化（UI側に合わせてフィールド名を大文字にする）
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

            handicap_ij_val = handicaps.get((pid_j, pid_i), 0)
            handicap_ji_val = handicaps.get((pid_i, pid_j), 0)

            if pair_key in total_only_set:
                pts = calc_match_points(data_i, data_j, handicap_ij_val, handicap_ji_val, is_total_only=True)
            else:
                pts = calc_match_points(data_i, data_j, handicap_ij_val, handicap_ji_val, is_total_only=False)
            # 直接UI側のフィールド名に更新
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
        # Putt Pt を使って Total Pt を計算
        d["Total Pt"] = d["Game Pt"] + d["Match Pt"] + d["Putt Pt"]

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
