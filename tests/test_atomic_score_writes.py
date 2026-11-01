from types import SimpleNamespace

from modules.round_persistence import (
    create_round_setup_atomic,
    delete_round_atomic,
    save_score_updates_atomic,
)
from modules import supabase_client
import pytest

ROUND_DATA = {"date_played": "2026-10-31", "num_players": 2, "course_id": 1, "course_name": "Test"}


class FakeRpcClient:
    def __init__(self):
        self.calls = []

    def rpc(self, name, params):
        self.calls.append((name, params))
        return SimpleNamespace(execute=lambda: SimpleNamespace(data={"ok": True}))


def test_round_setup_is_one_rpc_and_normalizes_member_ids():
    client = FakeRpcClient()

    result = create_round_setup_atomic(
        client,
        ROUND_DATA,
        ["3", 5],
        [],
    )

    assert result == {"ok": True}
    assert client.calls == [(
        "create_golf_round_atomic",
        {
            "p_round": ROUND_DATA,
            "p_member_ids": [3, 5],
            "p_handicaps": [],
        },
    )]


def test_round_setup_rejects_more_than_four_participants():
    client = FakeRpcClient()

    with pytest.raises(ValueError, match="2名から4名"):
        create_round_setup_atomic(client, {**ROUND_DATA, "num_players": 5}, [1, 2, 3, 4, 5], [])

    assert client.calls == []


def test_round_setup_requires_registered_course():
    client = FakeRpcClient()

    with pytest.raises(ValueError, match="ゴルフ場"):
        create_round_setup_atomic(client, {"num_players": 2}, [1, 2], [])

    assert client.calls == []


def test_round_setup_rejects_reversed_duplicate_handicap_pair():
    client = FakeRpcClient()
    handicaps = [
        {"player_1_id": 1, "player_2_id": 2},
        {"player_1_id": 2, "player_2_id": 1},
    ]

    with pytest.raises(ValueError, match="重複"):
        create_round_setup_atomic(client, ROUND_DATA, [1, 2], handicaps)

    assert client.calls == []


def test_round_setup_rejects_handicap_player_outside_participants():
    client = FakeRpcClient()

    with pytest.raises(ValueError, match="参加者"):
        create_round_setup_atomic(
            client, ROUND_DATA, [1, 2], [{"player_1_id": 1, "player_2_id": 3}]
        )

    assert client.calls == []


def test_score_batch_uses_one_atomic_rpc(monkeypatch):
    client = FakeRpcClient()
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: client)
    records = [{"member_id": 1, "front_score": 45}]

    success, result = supabase_client.upsert_scores_batch(7, records, "front")

    assert success is True
    assert result == {"ok": True}
    assert client.calls == [(
        "save_golf_score_segment_atomic",
        {
            "p_round_id": 7,
            "p_segment": "front",
            "p_records": records,
            "p_allow_finalized": False,
        },
    )]


def test_legacy_batch_update_delegates_to_atomic_rpc(monkeypatch):
    class ClientWithScores(FakeRpcClient):
        def table(self, name):
            assert name == "score"

            class Query:
                def select(self, *_args): return self
                def eq(self, *_args): return self
                def execute(self):
                    return SimpleNamespace(data=[
                        {"member_id": 1, "front_score": 40, "front_putt": 15,
                         "front_game_pt": 0, "back_score": 42, "back_putt": 16,
                         "back_game_pt": 0, "extra_score": 0, "extra_putt": 0,
                         "extra_game_pt": 0, "total_score": 82},
                        {"member_id": 2, "front_score": 41, "front_putt": 16,
                         "front_game_pt": 0, "back_score": 43, "back_putt": 17,
                         "back_game_pt": 0, "extra_score": 0, "extra_putt": 0,
                         "extra_game_pt": 0, "total_score": 84},
                    ])
            return Query()

    client = ClientWithScores()
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: client)

    success, count, errors = supabase_client.update_scores_batch(7, {1: {"front_score": 44}})

    assert (success, count, errors) == (True, 1, [])
    assert len(client.calls) == 1
    name, params = client.calls[0]
    assert name == "save_golf_score_segment_atomic"
    assert params["p_segment"] == "all"
    assert params["p_records"] == [
        {"member_id": 1, "front_score": 44, "front_putt": 15, "front_game_pt": 0,
         "back_score": 42, "back_putt": 16, "back_game_pt": 0,
         "extra_score": 0, "extra_putt": 0, "extra_game_pt": 0, "total_score": 86},
        {"member_id": 2, "front_score": 41, "front_putt": 16, "front_game_pt": 0,
         "back_score": 43, "back_putt": 17, "back_game_pt": 0,
         "extra_score": 0, "extra_putt": 0, "extra_game_pt": 0, "total_score": 84},
    ]


def test_legacy_single_score_save_delegates_to_atomic_rpc(monkeypatch):
    class ClientWithScores(FakeRpcClient):
        def table(self, name):
            assert name == "score"

            class Query:
                def select(self, *_args): return self
                def eq(self, *_args): return self
                def execute(self):
                    return SimpleNamespace(data=[
                        {"member_id": 1, "front_score": 40, "front_putt": 15,
                         "front_game_pt": 0, "back_score": 42, "back_putt": 16,
                         "back_game_pt": 0, "extra_score": 0, "extra_putt": 0,
                         "extra_game_pt": 0, "total_score": 82},
                        {"member_id": 2, "front_score": 41, "front_putt": 16,
                         "front_game_pt": 0, "back_score": 43, "back_putt": 17,
                         "back_game_pt": 0, "extra_score": 0, "extra_putt": 0,
                         "extra_game_pt": 0, "total_score": 84},
                    ])
            return Query()

    client = ClientWithScores()
    monkeypatch.setattr(supabase_client, "get_supabase_client", lambda: client)

    supabase_client.save_score(7, 2, {"back_putt": 14})

    assert len(client.calls) == 1
    name, params = client.calls[0]
    assert name == "save_golf_score_segment_atomic"
    assert params["p_records"][1]["back_putt"] == 14


def test_admin_score_batch_can_explicitly_allow_finalized_round():
    client = FakeRpcClient()

    result = save_score_updates_atomic(
        client, 11, "all", [{"member_id": 2, "front_score": 46}], allow_finalized=True
    )

    assert result == {"ok": True}
    assert client.calls[0][1]["p_allow_finalized"] is True


def test_round_delete_uses_one_atomic_rpc():
    client = FakeRpcClient()

    result = delete_round_atomic(client, "12")

    assert result == {"ok": True}
    assert client.calls == [(
        "delete_golf_round_atomic",
        {"p_round_id": 12},
    )]
