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

    # Supabaseから取得したFront GPを使用する（存在する場合）
    for pid in player_ids:
        # 既存の"Front GP"があればそのまま使用する条件を追加
        if "Front GP" in player_data[pid]:
            # 既存値をそのまま維持
            pass
        elif "Front Game Pt" in player_data[pid]:
            player_data[pid]["Front GP"] = player_data[pid]["Front Game Pt"]
        elif "front_game_pt" in player_data[pid]:
            player_data[pid]["Front GP"] = player_data[pid]["front_game_pt"]
        else:
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

    # Back GPも同様に処理
    for pid in player_ids:
        # 既存の"Back GP"があればそのまま使用する条件を追加
        if "Back GP" in player_data[pid]:
            # 既存値をそのまま維持
            pass
        elif "Back Game Pt" in player_data[pid]:
            player_data[pid]["Back GP"] = player_data[pid]["Back Game Pt"]
        elif "back_game_pt" in player_data[pid]:
            player_data[pid]["Back GP"] = player_data[pid]["back_game_pt"]
        else:
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

    # Extra GPも同様に処理
    if active_round.get('has_extra', False):
        for pid in player_ids:
            # 既存の"Extra GP"があればそのまま使用する条件を追加
            if "Extra GP" in player_data[pid]:
                # 既存値をそのまま維持
                pass
            elif "Extra Game Pt" in player_data[pid]:
                player_data[pid]["Extra GP"] = player_data[pid]["Extra Game Pt"]
            elif "extra_game_pt" in player_data[pid]:
                player_data[pid]["Extra GP"] = player_data[pid]["extra_game_pt"]
            else:
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

    # temp_game_ptsの計算を行う
    temp_game_pts = {}
    for mid in player_ids:
        fgp = player_data[mid]["Front GP"]
        bgp = player_data[mid]["Back GP"]
        egp = player_data[mid].get("Extra GP", 0)
        temp_game_pts[mid] = fgp + bgp + egp
        player_data[mid]["temp_game_pt"] = temp_game_pts[mid]

    print("Debug - Temp Game Points:", temp_game_pts)

    # 3人プレイでの特殊計算
    if len(player_ids) == 3:
        # 3人プレイ用の新しい計算
        for mid in player_ids:
            # フロント、バック、エクストラの個別ポイントを取得
            front_gp = player_data[mid]["Front GP"]
            back_gp = player_data[mid].get("Back GP", 0)
            extra_gp = player_data[mid].get("Extra GP", 0)
            
            # 他のプレイヤーのフロント、バック、エクストラの合計を取得
            others_front_gp = sum(player_data[oid]["Front GP"] for oid in player_ids if oid != mid)
            others_back_gp = sum(player_data[oid].get("Back GP", 0) for oid in player_ids if oid != mid)
            others_extra_gp = sum(player_data[oid].get("Extra GP", 0) for oid in player_ids if oid != mid)
            
            # セクションごとのゲームポイント計算
            front_game_pt = front_gp * 2 - others_front_gp
            back_game_pt = back_gp * 2 - others_back_gp
            extra_game_pt = extra_gp * 2 - others_extra_gp
            
            # 各セクションのポイント計算結果をデバッグ出力
            print(f"Player {mid} - Front: {front_gp}*2-{others_front_gp}={front_game_pt}")
            print(f"Player {mid} - Back: {back_gp}*2-{others_back_gp}={back_game_pt}")
            if extra_gp != 0 or others_extra_gp != 0:
                print(f"Player {mid} - Extra: {extra_gp}*2-{others_extra_gp}={extra_game_pt}")
            
            # 合計ゲームポイント
            total_game_pt = front_game_pt + back_game_pt + extra_game_pt
            
            # 元のキーを保存しながら新しい計算値を使用
            if "total_game_pt" in player_data[mid]:
                old_total = player_data[mid]["total_game_pt"]
                print(f"Player {mid} - 元のtotal_game_pt: {old_total}, 新計算値: {total_game_pt}")
                # 値が異なる場合は警告を表示
                if abs(old_total - total_game_pt) > 0.1:  # 誤差を許容
                    print(f"警告: Player {mid}のゲームポイントが異なります (旧:{old_total} vs 新:{total_game_pt})")
            
            player_data[mid]["total_game_pt"] = total_game_pt
            player_data[mid]["Game Pt"] = total_game_pt
            
            print(f"Player {mid} - 最終Game Pt: {total_game_pt}")
    else:
        # 4人プレイは単純合計のまま
        for mid in player_ids:
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
    is_test_round = round_id > 900 or active_round.get('is_test', False)  # テストフラグも確認
    
    if round_id and not is_test_round:  # テストモードではデータを保存しない
        if save_round_results(round_id, player_data):
            print(f"Successfully saved round results and scores for round_id: {round_id}")
        else:
            print(f"Failed to save data for round_id: {round_id}")
    elif is_test_round:
        print("テストモード: データベースへの保存をスキップします")

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
