"""旧インポートパスとの互換性を保つためのラッパー。

新規コードは ``modules.supabase_client`` を直接利用してください。
"""

from modules.supabase_client import (
    get_player_scores,
    get_supabase_client,
    save_score,
)

__all__ = ["get_supabase_client", "save_score", "get_player_scores"]
