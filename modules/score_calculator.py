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
    """Extraスコアから、ハンディキャップ（multiplier 倍）を差し引いた値を差し引いた値を返す"""
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

def calc_match_points(data_i, data_j, handicap_ij, handicap_ji, is_total_only=False):
    front_pt = back_pt = total_pt = extra_pt = 0
    # バックスコアの入力が不足している場合（フロント９のみ入力）
    if safe_get_score(data_i, "Back Score") <= 0 or safe_get_score(data_j, "Back Score") <= 0:
        # Total Onlyモードの場合、判定すべきではないので全て0を返す
        if is_total_only:
            return {"Match Front": 0, "Match Back": 0, "Match Total": 0, "Match Extra": 0, "Total": 0}
        # 通常モード：フロントのみ・エキストラのみで判定
        front_i = calc_net_score(data_i, "Front Score", handicap_ij, multiplier=1)
        front_j = calc_net_score(data_j, "Front Score", handicap_ji, multiplier=1)
        if front_i < front_j:
            front_pt = 10
        elif front_i > front_j:
            front_pt = -10
        if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
            extra_i = calc_net_extra(data_i, handicap_ij, multiplier=1)
            extra_j = calc_net_extra(data_j, handicap_ji, multiplier=1)
            if extra_i < extra_j:
                extra_pt = 10
            elif extra_i > extra_j:
                extra_pt = -10
        total_points = front_pt + extra_pt
        return {"Match Front": front_pt, "Match Back": 0, "Match Total": front_pt, "Match Extra": extra_pt, "Total": total_points}
    else:
        # バックスコア入力がある場合
        if is_total_only:
            total_i = calc_net_total(data_i, handicap_ij, multiplier=2)
            total_j = calc_net_total(data_j, handicap_ji, multiplier=2)
            if total_i < total_j:
                total_pt = 10
            elif total_i > total_j:
                total_pt = -10
            if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
                extra_i = calc_net_extra(data_i, handicap_ij, multiplier=1)
                extra_j = calc_net_extra(data_j, handicap_ji, multiplier=1)
                if extra_i < extra_j:
                    extra_pt = 10
                elif extra_i > extra_j:
                    extra_pt = -10
            total_points = total_pt + extra_pt
            return {"Match Front": 0, "Match Back": 0, "Match Total": total_pt, "Match Extra": extra_pt, "Total": total_points}
        else:
            front_i = calc_net_score(data_i, "Front Score", handicap_ij, multiplier=1)
            front_j = calc_net_score(data_j, "Front Score", handicap_ji, multiplier=1)
            if front_i < front_j:
                front_pt = 10
            elif front_i > front_j:
                front_pt = -10
            back_i = calc_net_score(data_i, "Back Score", handicap_ij, multiplier=1)
            back_j = calc_net_score(data_j, "Back Score", handicap_ji, multiplier=1)
            if back_i < back_j:
                back_pt = 10
            elif back_i > back_j:
                back_pt = -10
            total_i = calc_net_total(data_i, handicap_ij, multiplier=2)
            total_j = calc_net_total(data_j, handicap_ji, multiplier=2)
            if total_i < total_j:
                total_pt = 10
            elif total_i > total_j:
                total_pt = -10
            if safe_get_score(data_i, "Extra Score") > 0 or safe_get_score(data_j, "Extra Score") > 0:
                extra_i = calc_net_extra(data_i, handicap_ij, multiplier=1)
                extra_j = calc_net_extra(data_j, handicap_ji, multiplier=1)
                if extra_i < extra_j:
                    extra_pt = 10
                elif extra_i > extra_j:
                    extra_pt = -10
            total_points = front_pt + back_pt + total_pt + extra_pt
            return {"Match Front": front_pt, "Match Back": back_pt, "Match Total": total_pt, "Match Extra": extra_pt, "Total": total_points}

def calc_match_points_by_section(player_i, player_j, handicap_ij, handicap_ji, section, multiplier=1):
    """セクション（Front/Back/Total/Extra）ごとのマッチポイントを計算"""
    if section == "Front":
        score_i = player_i["Front Score"] - handicap_ij
        score_j = player_j["Front Score"] - handicap_ji
    elif section == "Back":
        if player_i["Back Score"] == 0 or player_j["Back Score"] == 0:
            return None
        score_i = player_i["Back Score"] - handicap_ij
        score_j = player_j["Back Score"] - handicap_ji
    elif section == "Total":
        if player_i["Back Score"] == 0 or player_j["Back Score"] == 0:
            return None
        score_i = player_i["Total Score"] - handicap_ij * 2
        score_j = player_j["Total Score"] - handicap_ji * 2
    else:  # Extra
        if player_i["Extra Score"] == 0 or player_j["Extra Score"] == 0:
            return None
        score_i = player_i["Extra Score"] - handicap_ij
        score_j = player_j["Extra Score"] - handicap_ji
    
    score_diff = score_i - score_j
    if score_diff < 0:
        return 10
    elif score_diff > 0:
        return -10
    else:
        return 0
