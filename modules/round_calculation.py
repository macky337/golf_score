"""全画面で共通利用するラウンド再計算処理。"""

from modules.calculation_logic import calculate_player_points
from modules.data_formatter import initialize_player_data
from modules.round_persistence import save_calculation_atomic
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


def recalculate_round(supabase, round_id, *, finalize=False):
    """DBからの取得失敗時には保存せず、取得した入力が現在も同じ場合だけ結果を保存。"""
    scores = supabase.table("score").select("*, member:member_id(name)").eq("round_id", round_id).execute().data or []
    if not scores:
        raise ValueError("スコアデータを取得できません")
    rounds = supabase.table("rounds").select("*").eq("round_id", round_id).execute().data
    if not rounds:
        raise ValueError("ラウンド情報を取得できません")
    round_data = rounds[0]
    handicaps = supabase.table("handicap_match").select("*").eq("round_id", round_id).execute().data or []
    if finalize:
        errors = validate_round_data(round_data, scores)
        if errors:
            raise ValueError("\n".join(errors))
    calculated = calculate_from_snapshot(scores, round_data, handicaps)
    save_calculation_atomic(supabase, round_id, calculated, expected_scores=scores,
                            expected_round=round_data, expected_handicaps=handicaps, finalize=finalize)
    return calculated
