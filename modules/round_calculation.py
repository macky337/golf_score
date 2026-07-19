"""全画面で共通利用するラウンド再計算処理。"""

from modules.calculation_logic import calculate_player_points
from modules.data_formatter import initialize_player_data
from modules.round_results import get_round_results, save_round_results


def recalculate_round(supabase, round_id):
    """最新のスコアとハンデから結果を再計算して保存する。"""
    scores = (
        supabase.table("score")
        .select("*, member:member_id(name)")
        .eq("round_id", round_id)
        .execute()
        .data
        or []
    )
    if not scores:
        raise ValueError("スコアデータを取得できません")

    round_response = (
        supabase.table("rounds").select("*").eq("round_id", round_id).execute()
    )
    if not round_response.data:
        raise ValueError("ラウンド情報を取得できません")

    handicaps_response = (
        supabase.table("handicap_match")
        .select("*")
        .eq("round_id", round_id)
        .execute()
    )
    handicaps = {}
    total_only_set = set()
    for handicap in handicaps_response.data or []:
        player_1_id = handicap["player_1_id"]
        player_2_id = handicap["player_2_id"]
        handicaps[(player_1_id, player_2_id)] = handicap["player_1_to_2"]
        handicaps[(player_2_id, player_1_id)] = handicap["player_2_to_1"]
        if handicap.get("total_only"):
            total_only_set.add(frozenset((player_1_id, player_2_id)))

    player_data = initialize_player_data(scores, get_round_results(round_id))
    updated_player_data = calculate_player_points(
        player_data,
        sorted(player_data),
        handicaps,
        total_only_set,
        round_response.data[0],
    )
    if not save_round_results(round_id, updated_player_data):
        raise RuntimeError("再計算結果を保存できません")
    return updated_player_data
