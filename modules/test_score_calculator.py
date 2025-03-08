import pytest
from modules.score_calculator import calc_net_score, calc_match_points_by_section, calc_putt_points
from modules.calculation_logic import calculate_player_points

def test_calc_net_score():
    data = {"Front Score": 40}
    handicap = 5
    assert calc_net_score(data, "Front Score", handicap) == 35

def test_calc_match_points_by_section():
    player_i = {"Front Score": 40}
    player_j = {"Front Score": 45}
    handicap_ij = 2
    handicap_ji = -2
    section = "Front"
    assert calc_match_points_by_section(player_i, player_j, handicap_ij, handicap_ji, section) == 10
    assert calc_match_points_by_section(player_j, player_i, handicap_ji, handicap_ij, section) == -10

def test_calc_putt_points():
    putt_scores = {"player1": 15, "player2": 16, "player3": 15}
    n = 3
    expected_points = {"player1": 5, "player2": -10, "player3": 5}
    assert calc_putt_points(putt_scores, n) == expected_points

# 他の関数のテストも同様に追加
