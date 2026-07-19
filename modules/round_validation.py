"""ラウンド確定前後の整合性チェック。"""


def validate_round_data(round_data, scores, results=None, require_results=False):
    """取得済みデータを検証し、利用者向けエラー文の一覧を返す。"""
    errors = []
    scores = scores or []
    results = results or []
    expected_players = round_data.get("num_players") or len(scores)

    if len(scores) != expected_players:
        errors.append(
            f"参加人数は{expected_players}人ですが、スコアは{len(scores)}人分です。"
        )

    member_ids = set()
    for score in scores:
        member_id = score.get("member_id")
        member_ids.add(member_id)
        member = score.get("member") or {}
        player_name = member.get("name") or f"メンバーID {member_id}"
        if (score.get("front_score") or 0) <= 0:
            errors.append(f"{player_name}のOUTスコアが未入力です。")
        if (score.get("back_score") or 0) <= 0:
            errors.append(f"{player_name}のINスコアが未入力です。")
        if round_data.get("has_extra") and (score.get("extra_score") or 0) <= 0:
            errors.append(f"{player_name}のエキストラスコアが未入力です。")

    if require_results:
        result_member_ids = {item.get("member_id") for item in results}
        if len(results) != len(scores) or result_member_ids != member_ids:
            errors.append("参加者全員の計算結果が保存されていません。")

        for field, label in (
            ("match_pt", "マッチポイント"),
            ("putt_pt", "パットポイント"),
            ("total_game_pt", "ゲームポイント"),
        ):
            total = sum((item.get(field) or 0) for item in results)
            if total != 0:
                errors.append(f"{label}の全員合計が0ではありません（現在 {total:+}）。")

    return errors


def validate_round(supabase, round_id, require_results=False):
    """DBの最新データを使ってラウンドを検証する。"""
    round_response = (
        supabase.table("rounds").select("*").eq("round_id", round_id).execute()
    )
    if not round_response.data:
        return ["ラウンド情報を取得できません。"]

    scores = (
        supabase.table("score")
        .select("*, member:member_id(name)")
        .eq("round_id", round_id)
        .execute()
        .data
        or []
    )
    results = []
    if require_results:
        results = (
            supabase.table("round_results")
            .select("member_id, match_pt, putt_pt, total_game_pt")
            .eq("round_id", round_id)
            .execute()
            .data
            or []
        )

    return validate_round_data(
        round_response.data[0],
        scores,
        results,
        require_results=require_results,
    )
