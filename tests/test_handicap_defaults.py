from modules.handicap_defaults import (
    MAX_ROUND_PLAYERS,
    default_for_pair,
    latest_pair_defaults,
)


def test_latest_pair_value_is_used_for_each_pair():
    defaults = latest_pair_defaults([
        {"id": 1, "round_id": 3, "rounds": {"date_played": "2026-01-01"}, "player_1_id": 2, "player_2_id": 5, "player_1_to_2": 1, "player_2_to_1": -1, "total_only": False},
        {"id": 2, "round_id": 4, "rounds": {"date_played": "2026-02-01"}, "player_1_id": 2, "player_2_id": 5, "player_1_to_2": 3, "player_2_to_1": -3, "total_only": True},
    ])

    assert default_for_pair(defaults, 2, 5) == {"h1to2": 3, "h2to1": -3, "total_only": True}


def test_defaults_reverse_direction_when_selected_order_is_reversed():
    defaults = latest_pair_defaults([
        {"id": 1, "round_id": 3, "rounds": {"date_played": "2026-01-01"}, "player_1_id": 2, "player_2_id": 5, "player_1_to_2": 4, "player_2_to_1": -4, "total_only": False},
    ])

    assert default_for_pair(defaults, 5, 2) == {"h1to2": -4, "h2to1": 4, "total_only": False}


def test_maximum_round_players_is_four():
    assert MAX_ROUND_PLAYERS == 4
