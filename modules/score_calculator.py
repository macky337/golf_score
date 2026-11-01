# filepath: c:\Users\user\Documents\GitHub\golf_score\modules\score_calculator.py
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

from modules.competition_rules import normalize_rules


def calc_putt_points(putt_scores, n, rules=None):
    """
    パット戦の得点計算（参加人数に応じたルール）
    
    ルール:
    1. 各プレイヤーのパットスコア（例："Putt Front", "Putt Back", "Putt Extra" など）を収集し、参加者全体のスコアリストから最小値 (min_score) を特定する。
    2. 最小スコアを出したプレイヤー（winners）のリストを作成する。
    3. 【2人の場合】
       - 勝者に +10pt、敗者に -10pt
    4. 【3人の場合】
       - 勝者が1名の場合: 勝者に +20pt、残り2名に -10pt
       - 勝者が2名の場合: 両勝者に +5pt、残り1名に -10pt
    5. 【4人の場合】
       - 勝者が1名の場合: 勝者に +30pt、残り3名に -10pt
       - 勝者が2名の場合: 両勝者に +10pt、残り2名に -10pt
       - 勝者が3名の場合: 勝者に +5pt、残り1名に -15pt
    なお、すべてのプレイヤーが同じスコアの場合は全員0点とする。
    """
    rules = normalize_rules(rules)
    if not putt_scores:
        return {}
    
    # 0/Noneは未入力。全員分が揃うまで、この区分の配点は保留する。
    if len(putt_scores) != n or any(value is None or value <= 0 for value in putt_scores.values()):
        return {member_id: 0 for member_id in putt_scores}
    scores = list(putt_scores.values())
    min_score = min(scores)
    winners = [m_id for m_id, score in putt_scores.items() if score == min_score]
    points = {m_id: 0 for m_id in putt_scores}
    
    # すべてのプレイヤーが同じスコアの場合
    if len(winners) == n:
        return points
    
    if n == 2:
        points[winners[0]] = rules["putt_2_winner"]
        for m_id in putt_scores:
            if m_id not in winners:
                points[m_id] = rules["putt_2_loser"]
    elif n == 3:
        if len(winners) == 1:
            points[winners[0]] = rules["putt_3_solo_winner"]
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = rules["putt_3_solo_loser"]
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = rules["putt_3_two_winners"]
                else:
                    points[m_id] = rules["putt_3_two_losers"]
    elif n == 4:
        if len(winners) == 1:
            points[winners[0]] = rules["putt_4_solo_winner"]
            for m_id in putt_scores:
                if m_id not in winners:
                    points[m_id] = rules["putt_4_solo_loser"]
        elif len(winners) == 2:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = rules["putt_4_two_winners"]
                else:
                    points[m_id] = rules["putt_4_two_losers"]
        elif len(winners) == 3:
            for m_id in putt_scores:
                if m_id in winners:
                    points[m_id] = rules["putt_4_three_winners"]
                else:
                    points[m_id] = rules["putt_4_three_losers"]
    
    return points

def calc_match_points(data_i, data_j, handicap_ij, handicap_ji, is_total_only=False, rules=None):
    """双方が入力済みの区分だけを判定する。合計戦にはOUT/IN両方が必要。"""
    points = {f"Match {section}": 0 for section in ("Front", "Back", "Total", "Extra")}
    for section in ("Front", "Back", "Total", "Extra"):
        if is_total_only and section in {"Front", "Back"}:
            continue
        value = calc_match_points_by_section(
            data_i, data_j, handicap_ij, handicap_ji, section, rules=rules
        )
        points[f"Match {section}"] = value if value is not None else 0
    points["Total"] = sum(points.values())
    return points


def calc_match_points_by_section(player_i, player_j, handicap_ij, handicap_ji, section, multiplier=1, rules=None):
    """入力されていない区分はNoneを返し、0打として勝敗判定しない。"""
    fields = ("Front Score", "Back Score") if section == "Total" else (f"{section} Score",)
    if any(safe_get_score(player, field) <= 0 for player in (player_i, player_j) for field in fields):
        return None
    handicap_multiplier = 2 if section == "Total" else 1
    score_i = sum(safe_get_score(player_i, field) for field in fields) - handicap_ij * handicap_multiplier
    score_j = sum(safe_get_score(player_j, field) for field in fields) - handicap_ji * handicap_multiplier
    match_value = normalize_rules(rules)["match_win_points"]
    return match_value if score_i < score_j else -match_value if score_i > score_j else 0
