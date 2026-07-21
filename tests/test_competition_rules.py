from modules.competition_rules import DEFAULT_RULES, normalize_rules, rules_for_round
from modules.score_calculator import calc_match_points, calc_putt_points


def test_legacy_round_uses_original_defaults():
    rules = rules_for_round({"round_id": 1})

    assert rules["match_win_points"] == 10
    assert rules["game_points_4"] == [30, 10, -10, -30]


def test_partial_rules_are_completed_with_defaults():
    rules = normalize_rules({"match_win_points": 7})

    assert rules["match_win_points"] == 7
    assert rules["putt_4_solo_winner"] == DEFAULT_RULES["putt_4_solo_winner"]


def test_custom_match_points_are_used():
    player_a = {"Front Score": 40, "Back Score": 40, "Extra Score": 0}
    player_b = {"Front Score": 41, "Back Score": 41, "Extra Score": 0}

    result = calc_match_points(
        player_a,
        player_b,
        0,
        0,
        rules={"match_win_points": 6},
    )

    assert result["Match Front"] == 6
    assert result["Match Back"] == 6
    assert result["Match Total"] == 6
    assert result["Total"] == 18


def test_custom_putt_points_are_used():
    rules = {
        "putt_3_solo_winner": 12,
        "putt_3_solo_loser": -6,
    }

    result = calc_putt_points({1: 14, 2: 16, 3: 17}, 3, rules)

    assert result == {1: 12, 2: -6, 3: -6}
