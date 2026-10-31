from types import SimpleNamespace

from modules.round_persistence import (
    create_round_setup_atomic,
    delete_round_atomic,
    save_score_updates_atomic,
)
from modules import supabase_client


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
        {"date_played": "2026-10-31", "num_players": 2},
        ["3", 5],
        [],
    )

    assert result == {"ok": True}
    assert client.calls == [(
        "create_golf_round_atomic",
        {
            "p_round": {"date_played": "2026-10-31", "num_players": 2},
            "p_member_ids": [3, 5],
            "p_handicaps": [],
        },
    )]


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
