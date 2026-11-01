"""全画面で共通利用するラウンド再計算処理。"""

from modules.calculation_logic import calculate_player_points
from modules.data_formatter import initialize_player_data
from modules.round_persistence import SCORE_FIELDS, save_calculation_atomic, score_snapshot
from modules.round_validation import validate_round_data


def calculate_from_snapshot(scores, round_data, handicap_rows):
    handicaps = {}
    total_only_set = set()
    for handicap in handicap_rows:
        player_1_id, player_2_id = handicap["player_1_id"], handicap["player_2_id"]
        handicaps[(player_1_id, player_2_id)] = handicap["player_1_to_2"]
        handicaps[(player_2_id, player_1_id)] = handicap["player_2_to_1"]
        if handicap.get("total_only"):
            total_only_set.add(frozenset((player_1_id, player_2_id)))
    player_data = initialize_player_data(scores, {})
    return calculate_player_points(player_data, sorted(player_data), handicaps, total_only_set, round_data)


def recalculate_round(supabase, round_id, *, finalize=False, expected_scores=None, expected_handicaps=None,
                      replacement_handicaps=None, replacement_scores=None):
    """DBからの取得失敗時には保存せず、取得した入力が現在も同じ場合だけ結果を保存。"""
    scores = supabase.table("score").select("*, member:member_id(name)").eq("round_id", round_id).execute().data or []
    if not scores:
        raise ValueError("スコアデータを取得できません")
    rounds = supabase.table("rounds").select("*").eq("round_id", round_id).execute().data
    if not rounds:
        raise ValueError("ラウンド情報を取得できません")
    round_data = rounds[0]
    handicaps = supabase.table("handicap_match").select("*").eq("round_id", round_id).execute().data or []
    calculation_scores = replacement_scores if replacement_scores is not None else scores
    if finalize:
        errors = validate_round_data(round_data, calculation_scores)
        if errors:
            raise ValueError("\n".join(errors))
    calculation_handicaps = replacement_handicaps if replacement_handicaps is not None else handicaps
    calculated = calculate_from_snapshot(calculation_scores, round_data, calculation_handicaps)
    save_calculation_atomic(supabase, round_id, calculated,
                            expected_round=round_data,
                            expected_scores=(expected_scores if expected_scores is not None else scores),
                            expected_handicaps=(
                                expected_handicaps if expected_handicaps is not None else handicaps
                            ),
                            replacement_handicaps=replacement_handicaps,
                            replacement_scores=replacement_scores, finalize=finalize)
    return calculated


def save_score_changes_and_recalculate(supabase, round_id, changes, expected_scores, *, finalize=False):
    """スコア変更と計算結果を一つの保存RPCで確定する。"""
    replacement = {row["member_id"]: row for row in score_snapshot(expected_scores)}
    for change in changes:
        member_id = int(change["member_id"])
        if member_id not in replacement:
            raise ValueError("このラウンドの参加者ではないメンバーが含まれています")
        replacement[member_id].update({key: value for key, value in change.items() if key in SCORE_FIELDS})
    return recalculate_round(
        supabase, round_id, expected_scores=expected_scores,
        replacement_scores=list(replacement.values()), finalize=finalize,
    )
