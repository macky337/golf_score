"""ラウンドの計算結果を、入力値の比較後に単一RPCで保存する。"""

SCORE_FIELDS = (
    "front_score", "front_putt", "back_score", "back_putt", "extra_score", "extra_putt",
    "front_game_pt", "back_game_pt", "extra_game_pt",
)
PLAYER_FIELDS = (
    "Front Score", "Front Putt", "Back Score", "Back Putt", "Extra Score", "Extra Putt",
    "Front GP", "Back GP", "Extra GP",
)
RESULT_FIELDS = {
    "match_front": "Match Front", "match_back": "Match Back", "match_total": "Match Total",
    "match_extra": "Match Extra", "match_pt": "Match Pt", "putt_pt": "Putt Pt",
    "temp_game_pt": "temp_game_pt", "total_game_pt": "Game Pt",
}


def score_snapshot(scores):
    return sorted(
        [{"member_id": int(row["member_id"]), **{key: row.get(key) or 0 for key in SCORE_FIELDS}} for row in scores],
        key=lambda row: row["member_id"],
    )


def save_calculation_atomic(client, round_id, player_data, *, expected_scores=None,
                            expected_round=None, expected_handicaps=None,
                            finalize=False):
    if not player_data:
        raise ValueError("保存する計算結果がありません。")
    if expected_scores is None:
        expected_scores = [
            {"member_id": int(member_id), **{
                key: data.get(label, data.get(label.replace("Front Putt", "Putt Front").replace("Back Putt", "Putt Back").replace("Extra Putt", "Putt Extra"), 0)) or 0
                for key, label in zip(SCORE_FIELDS, PLAYER_FIELDS)
            }} for member_id, data in player_data.items()
        ]
    records = [
        {"member_id": int(member_id), **{key: data.get(label, 0) or 0 for key, label in RESULT_FIELDS.items()}}
        for member_id, data in sorted(player_data.items())
    ]
    return client.rpc("save_golf_round_atomic", {
        "p_round_id": int(round_id), "p_expected_scores": score_snapshot(expected_scores),
        "p_results": records,
        "p_expected_round": expected_round, "p_expected_handicaps": expected_handicaps,
        "p_finalize": finalize,
    }).execute()


def create_round_setup_atomic(client, round_data, member_ids, handicaps):
    """ラウンド、参加者スコア、ハンディキャップを単一RPCで作成する。"""
    response = client.rpc("create_golf_round_atomic", {
        "p_round": round_data,
        "p_member_ids": [int(member_id) for member_id in member_ids],
        "p_handicaps": handicaps,
    }).execute()
    return response.data


def save_score_updates_atomic(client, round_id, segment, records, *, allow_finalized=False):
    """対象ラウンドの参加者全員分を1トランザクションで更新する。"""
    if not records:
        raise ValueError("保存するスコアがありません")
    response = client.rpc("save_golf_score_segment_atomic", {
        "p_round_id": int(round_id),
        "p_segment": segment,
        "p_records": records,
        "p_allow_finalized": allow_finalized,
    }).execute()
    return response.data


def delete_round_atomic(client, round_id):
    """ラウンドと関連データを単一RPCで削除する。"""
    response = client.rpc("delete_golf_round_atomic", {
        "p_round_id": int(round_id),
    }).execute()
    return response.data
