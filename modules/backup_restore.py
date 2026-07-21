"""Supabase バックアップの検証と原子的な復元。"""

from collections.abc import Mapping


BACKUP_LIST_KEYS = (
    "members",
    "rounds",
    "scores",
    "handicap_matches",
    "round_results",
    "app_settings",
)


def validate_backup_payload(payload):
    """復元RPCへ渡せる形式か検証し、古いバックアップを補完する。"""
    if not isinstance(payload, Mapping):
        raise ValueError("バックアップデータの形式が正しくありません")

    normalized = dict(payload)
    for key in BACKUP_LIST_KEYS:
        value = normalized.get(key, [])
        if not isinstance(value, list):
            raise ValueError(f"バックアップの {key} は配列である必要があります")
        normalized[key] = value

    return normalized


def restore_backup_atomic(supabase, payload):
    """単一のPostgreSQLトランザクションでバックアップを復元する。"""
    backup_data = validate_backup_payload(payload)
    return supabase.rpc(
        "restore_golf_score_backup",
        {"backup_data": backup_data},
    ).execute()
