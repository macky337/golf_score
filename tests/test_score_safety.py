from copy import deepcopy
from types import SimpleNamespace

import pytest

from modules.data_formatter import initialize_player_data
from modules.calculation_logic import calculate_player_points
from modules.round_persistence import SCORE_FIELDS, save_calculation_atomic
from modules.round_validation import validate_round_data
from modules.score_calculator import calc_match_points, calc_putt_points


def scores():
    return [dict(member_id=i, front_score=40+i, back_score=42+i, extra_score=0,
                 front_putt=15+i, back_putt=16+i, extra_putt=0,
                 front_game_pt=10 if i == 1 else 0, back_game_pt=0, extra_game_pt=0)
            for i in (1, 2, 3)]


def test_display_uses_calculated_game_points_and_total_not_raw_score_total():
    raw = scores()
    raw[0]['total_pt'] = -999
    result = initialize_player_data(raw, {1: {'Game Pt': 20, 'Match Pt': 60, 'Putt Pt': 40}})
    assert result[1]['Game Pt'] == 20
    assert result[1]['Total Pt'] == 120


def test_display_supports_database_result_column_names():
    result = initialize_player_data(scores(), {1: {'total_game_pt': 20, 'match_pt': 60, 'putt_pt': 40}})
    assert result[1]['Total Pt'] == 120


def test_three_player_game_points_are_zero_sum_and_recalculation_is_stable():
    players = initialize_player_data(scores(), {})
    calculated = calculate_player_points(players, [1, 2, 3], {}, set(), {})
    assert [calculated[i]['Game Pt'] for i in (1, 2, 3)] == [20, -10, -10]
    assert sum(player['Total Pt'] for player in calculated.values()) == 0
    assert calculate_player_points(deepcopy(calculated), [1, 2, 3], {}, set(), {}) == calculated


@pytest.mark.parametrize('missing', [0, None, -1])
def test_incomplete_putt_section_awards_nobody(missing):
    assert calc_putt_points({1: missing, 2: 16, 3: 18}, 3) == {1: 0, 2: 0, 3: 0}


@pytest.mark.parametrize('counts,n,expected', [
    ({1: 15, 2: 16, 3: 18}, 3, {1: 20, 2: -10, 3: -10}),
    ({1: 15, 2: 15, 3: 18}, 3, {1: 5, 2: 5, 3: -10}),
    ({1: 15, 2: 16, 3: 18, 4: 19}, 4, {1: 30, 2: -10, 3: -10, 4: -10}),
    ({1: 15, 2: 15, 3: 18, 4: 19}, 4, {1: 10, 2: 10, 3: -10, 4: -10}),
    ({1: 15, 2: 15, 3: 15, 4: 19}, 4, {1: 5, 2: 5, 3: 5, 4: -15}),
    ({1: 15, 2: 15, 3: 15}, 3, {1: 0, 2: 0, 3: 0}),
])
def test_complete_putt_rules_are_preserved(counts,n,expected):
    assert calc_putt_points(counts,n) == expected


def test_incomplete_match_sections_are_pending_and_not_double_counted():
    a = {'Front Score': 40, 'Back Score': 0, 'Extra Score': 0}
    b = {'Front Score': 45, 'Back Score': 44, 'Extra Score': 45}
    pts = calc_match_points(a, b, 0, 0)
    assert pts == {'Match Front': 10, 'Match Back': 0, 'Match Total': 0, 'Match Extra': 0, 'Total': 10}
    a['Front Score'] = 0
    assert calc_match_points(a, b, 0, 0)['Total'] == 0


def test_total_only_with_handicap_preserves_independent_extra_match():
    a = {'Front Score': 45, 'Back Score': 45, 'Extra Score': 45}
    b = {'Front Score': 44, 'Back Score': 44, 'Extra Score': 44}
    pts = calc_match_points(a, b, 2, 0, is_total_only=True)
    assert pts == {'Match Front': 0, 'Match Back': 0, 'Match Total': 10, 'Match Extra': 10, 'Total': 20}


def test_missing_putt_blocks_finalization():
    raw = scores()
    raw[0]['front_putt'] = 0
    assert any('OUTパット' in error for error in validate_round_data({'num_players':3}, raw))


class FakeClient:
    def __init__(self):
        self.round = {'round_id': 42, 'created_at': '2026-09-22T00:00:00+00:00',
                      'date_played': '2026-09-22', 'course_name': 'Test', 'finalized': False, 'num_players':3}
        self.scores = scores()
        self.calls = []
        self.fail_rpc = False

    def table(self, name):
        rows = {'score': self.scores, 'rounds': [self.round], 'handicap_match': []}[name]
        # No write methods: any client-side delete/update would fail this test.
        class Query:
            def select(self, *args): return self
            def eq(self, *args): return self
            def execute(self): return SimpleNamespace(data=deepcopy(rows))
        return Query()

    def rpc(self, name, params):
        self.calls.append((name, params))
        def execute():
            if self.fail_rpc: raise RuntimeError('database failure')
            return SimpleNamespace(data={'saved_players':3})
        return SimpleNamespace(execute=execute)


def test_rpc_error_is_not_retried_as_separate_writes():
    client = FakeClient()
    client.fail_rpc = True
    players = initialize_player_data(scores(), {})
    with pytest.raises(RuntimeError): save_calculation_atomic(client, 42, players)
    assert len(client.calls) == 1


def test_results_save_never_rewrites_raw_scores():
    client = FakeClient()
    players = initialize_player_data(scores(), {})
    save_calculation_atomic(client, 42, players)
    params = client.calls[0][1]
    assert 'p_scores' not in params
    assert {key for key in params['p_expected_scores'][0]} == {'member_id', *SCORE_FIELDS}
    assert params['p_replacement_handicaps'] is None


def test_handicap_replacement_is_sent_with_result_save():
    client = FakeClient()
    players = initialize_player_data(scores(), {})

    save_calculation_atomic(client, 42, players, replacement_handicaps=[{
        'player_1_id': 1, 'player_2_id': 2,
        'player_1_to_2': 3, 'player_2_to_1': -3, 'total_only': True,
        'id': 999,
    }])

    assert client.calls[0][0] == 'save_golf_round_atomic'
    assert client.calls[0][1]['p_replacement_handicaps'] == [{
        'player_1_id': 1, 'player_2_id': 2,
        'player_1_to_2': 3, 'player_2_to_1': -3, 'total_only': True,
    }]


def test_recalculation_read_error_stops_before_saving(monkeypatch):
    from modules.round_calculation import recalculate_round
    client = FakeClient()
    def fail(*args): raise RuntimeError('network unavailable')
    monkeypatch.setattr(client, 'table', fail)
    with pytest.raises(RuntimeError): recalculate_round(client, 42)
    assert client.calls == []


def test_finalization_is_part_of_same_rpc():
    from modules.round_calculation import recalculate_round
    client = FakeClient()
    recalculate_round(client, 42, finalize=True)
    assert len(client.calls) == 1
    assert client.calls[0][1]['p_finalize'] is True


def test_recalculation_replaces_handicaps_in_the_same_rpc():
    from modules.round_calculation import recalculate_round
    client = FakeClient()
    before = []
    replacement = [{
        'player_1_id': 1, 'player_2_id': 2,
        'player_1_to_2': 2, 'player_2_to_1': -2, 'total_only': False,
    }]

    recalculate_round(
        client, 42, expected_handicaps=before, replacement_handicaps=replacement
    )

    assert len(client.calls) == 1
    assert client.calls[0][0] == 'save_golf_round_atomic'
    assert client.calls[0][1]['p_expected_handicaps'] == before
    assert client.calls[0][1]['p_replacement_handicaps'] == replacement


def test_score_changes_and_results_are_saved_in_the_same_rpc():
    from modules.round_calculation import save_score_changes_and_recalculate
    client = FakeClient()
    before = scores()

    save_score_changes_and_recalculate(
        client, 42, [{'member_id': 1, 'front_score': 44, 'front_putt': 14}], before
    )

    assert len(client.calls) == 1
    params = client.calls[0][1]
    assert params['p_expected_scores'][0]['front_score'] == 41
    assert params['p_replacement_scores'][0]['front_score'] == 44
    assert params['p_replacement_scores'][0]['front_putt'] == 14
