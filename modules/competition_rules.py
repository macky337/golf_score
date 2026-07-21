"""競技ルールの既定値、DB保存、ラウンド用スナップショットを管理する。"""

from copy import deepcopy


SETTINGS_KEY = "competition_rules"

DEFAULT_RULES = {
    "version": 1,
    "match_win_points": 10,
    "putt_3_solo_winner": 20,
    "putt_3_solo_loser": -10,
    "putt_3_two_winners": 5,
    "putt_3_two_losers": -10,
    "putt_4_solo_winner": 30,
    "putt_4_solo_loser": -10,
    "putt_4_two_winners": 10,
    "putt_4_two_losers": -10,
    "putt_4_three_winners": 5,
    "putt_4_three_losers": -15,
    "game_points_2": [10, -10],
    "game_points_3": [30, 0, -30],
    "game_points_4": [30, 10, -10, -30],
}


def normalize_rules(value=None):
    """不足項目や不正値を既定値で補い、安全なルール辞書を返す。"""
    rules = deepcopy(DEFAULT_RULES)
    if not isinstance(value, dict):
        return rules

    for key, default in DEFAULT_RULES.items():
        candidate = value.get(key)
        if isinstance(default, int) and isinstance(candidate, int):
            rules[key] = candidate
        elif isinstance(default, list) and isinstance(candidate, list):
            if len(candidate) == len(default) and all(isinstance(item, int) for item in candidate):
                rules[key] = list(candidate)
    rules["match_win_points"] = max(1, abs(rules["match_win_points"]))
    return rules


def rules_for_round(round_data=None):
    """ラウンドに保存された設定を返す。旧ラウンドは従来の既定値を使う。"""
    if not isinstance(round_data, dict):
        return normalize_rules()
    return normalize_rules(round_data.get("rule_settings"))


def get_default_rules(supabase):
    """新規ラウンド用の標準ルールをDBから取得する。未導入時は既定値を返す。"""
    try:
        response = (
            supabase.table("app_settings")
            .select("value")
            .eq("key", SETTINGS_KEY)
            .limit(1)
            .execute()
        )
        if response.data:
            return normalize_rules(response.data[0].get("value"))
    except Exception:
        pass
    return normalize_rules()


def save_default_rules(supabase, rules):
    """新規ラウンド用の標準ルールを保存する。"""
    normalized = normalize_rules(rules)
    supabase.table("app_settings").upsert(
        {"key": SETTINGS_KEY, "value": normalized}, on_conflict="key"
    ).execute()
    return normalized
