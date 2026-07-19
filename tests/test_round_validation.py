from modules.round_validation import validate_round_data


def _round(has_extra=False):
    return {"num_players": 2, "has_extra": has_extra}


def _scores(extra_score=0):
    return [
        {"member_id": 1, "front_score": 45, "back_score": 44, "extra_score": extra_score},
        {"member_id": 2, "front_score": 46, "back_score": 43, "extra_score": extra_score},
    ]


def test_valid_scores_can_be_finalized():
    assert validate_round_data(_round(), _scores()) == []


def test_missing_back_score_is_reported():
    scores = _scores()
    scores[1]["back_score"] = 0
    errors = validate_round_data(_round(), scores)
    assert any("INスコアが未入力" in error for error in errors)


def test_extra_score_is_required_when_enabled():
    errors = validate_round_data(_round(has_extra=True), _scores())
    assert len([error for error in errors if "エキストラスコア" in error]) == 2


def test_unbalanced_results_are_reported():
    results = [
        {"member_id": 1, "match_pt": 10, "putt_pt": 0, "total_game_pt": 0},
        {"member_id": 2, "match_pt": 0, "putt_pt": 0, "total_game_pt": 0},
    ]
    errors = validate_round_data(
        _round(), _scores(), results, require_results=True
    )
    assert any("マッチポイント" in error for error in errors)
