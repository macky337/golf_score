import pytest

from modules.backup_restore import restore_backup_atomic, validate_backup_payload


class FakeRpcRequest:
    def __init__(self, result):
        self.result = result
        self.executed = False

    def execute(self):
        self.executed = True
        return self.result


class FakeSupabase:
    def __init__(self):
        self.calls = []
        self.request = FakeRpcRequest({"restored": True})

    def rpc(self, function_name, params):
        self.calls.append((function_name, params))
        return self.request


def test_validate_backup_payload_completes_legacy_backup():
    payload = {
        "members": [{"member_id": 1, "name": "Test"}],
        "rounds": [],
        "scores": [],
        "handicap_matches": [],
    }

    normalized = validate_backup_payload(payload)

    assert normalized["round_results"] == []
    assert normalized["app_settings"] == []
    assert normalized["members"] == payload["members"]
    assert "round_results" not in payload


@pytest.mark.parametrize(
    "payload",
    [None, [], "invalid"],
)
def test_validate_backup_payload_rejects_non_object(payload):
    with pytest.raises(ValueError, match="形式"):
        validate_backup_payload(payload)


def test_validate_backup_payload_rejects_non_list_table_value():
    with pytest.raises(ValueError, match="scores"):
        validate_backup_payload({"scores": {"score_id": 1}})


def test_restore_backup_uses_one_atomic_rpc_call():
    client = FakeSupabase()

    result = restore_backup_atomic(client, {"members": []})

    assert result == {"restored": True}
    assert client.request.executed is True
    assert len(client.calls) == 1
    function_name, params = client.calls[0]
    assert function_name == "restore_golf_score_backup"
    assert params["backup_data"]["round_results"] == []
