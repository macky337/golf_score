import base64
import json
import re

from modules.offline_score_pwa import _initial_package_script, offline_instance_id


def test_initial_package_script_embeds_utf8_json_safely():
    package = {
        "format": "golf-score-offline-v1",
        "round": {"round_id": 72, "course_name": "千葉＆みらい</script>"},
        "players": [{"member_id": 1, "name": "山田"}],
    }

    script = _initial_package_script(package)
    encoded = re.search(r"atob\('([^']+)'\)", script).group(1)

    assert json.loads(base64.b64decode(encoded).decode("utf-8")) == package
    assert "千葉＆みらい</script>" not in script
    assert script.count("</script>") == 1


def test_initial_package_script_is_empty_without_package():
    assert _initial_package_script(None) == ""


def test_offline_instance_id_changes_when_round_record_is_recreated():
    players = [{"member_id": 2}, {"member_id": 1}]
    original = {
        "round_id": 72,
        "created_at": "2026-07-19T01:00:00+00:00",
        "date_played": "2026-07-19",
        "course_name": "千葉よみうり",
    }
    recreated = {**original, "created_at": "2026-07-22T11:51:37+00:00"}

    assert offline_instance_id(original, players) != offline_instance_id(recreated, players)
    assert offline_instance_id(original, players) == offline_instance_id(
        original, list(reversed(players))
    )
