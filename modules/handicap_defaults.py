"""ラウンド設定で使うハンディキャップ初期値の取得・正規化。"""

MAX_ROUND_PLAYERS = 4


def _row_sort_key(row):
    round_data = row.get("rounds") or {}
    return (
        str(round_data.get("date_played") or ""),
        int(row.get("round_id") or 0),
        int(row.get("id") or 0),
    )


def latest_pair_defaults(rows):
    """各メンバー組み合わせについて、最も新しいハンディをID昇順で保持する。"""
    defaults = {}
    for row in sorted(rows or [], key=_row_sort_key, reverse=True):
        player_1_id = row.get("player_1_id")
        player_2_id = row.get("player_2_id")
        if player_1_id is None or player_2_id is None or player_1_id == player_2_id:
            continue
        player_1_id, player_2_id = int(player_1_id), int(player_2_id)
        pair = tuple(sorted((player_1_id, player_2_id)))
        if pair in defaults:
            continue

        if (player_1_id, player_2_id) == pair:
            first_to_second = row.get("player_1_to_2") or 0
            second_to_first = row.get("player_2_to_1") or 0
        else:
            first_to_second = row.get("player_2_to_1") or 0
            second_to_first = row.get("player_1_to_2") or 0
        defaults[pair] = {
            "first_to_second": int(first_to_second),
            "second_to_first": int(second_to_first),
            "total_only": bool(row.get("total_only", False)),
        }
    return defaults


def default_for_pair(defaults, player_1_id, player_2_id):
    """画面上の参加者順に合わせて、方向別ハンディキャップを返す。"""
    player_1_id, player_2_id = int(player_1_id), int(player_2_id)
    pair = tuple(sorted((player_1_id, player_2_id)))
    value = defaults.get(pair)
    if value is None:
        return {"h1to2": 0, "h2to1": 0, "total_only": False}
    if (player_1_id, player_2_id) == pair:
        return {
            "h1to2": value["first_to_second"],
            "h2to1": value["second_to_first"],
            "total_only": value["total_only"],
        }
    return {
        "h1to2": value["second_to_first"],
        "h2to1": value["first_to_second"],
        "total_only": value["total_only"],
    }


def load_previous_handicap_defaults(client, member_ids):
    """選択メンバー間で過去に設定したハンディキャップを取得する。"""
    member_ids = [int(member_id) for member_id in member_ids]
    if len(member_ids) < 2:
        return {}
    result = (
        client.table("handicap_match")
        .select("id, round_id, player_1_id, player_2_id, player_1_to_2, player_2_to_1, total_only, rounds!inner(date_played)")
        .in_("player_1_id", member_ids)
        .in_("player_2_id", member_ids)
        .execute()
    )
    return latest_pair_defaults(result.data or [])
