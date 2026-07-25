from modules.scorecard_ocr import suggest_scores


def test_suggest_scores_matches_member_row_and_normalises_full_width_digits():
    text = "山田太郎 ４２ １６ -５\n佐藤花子 45 18 +10"
    members = [{"member_id": 1, "name": "山田 太郎"}, {"member_id": 2, "name": "佐藤花子"}]

    assert suggest_scores(text, members) == {
        1: {"score": 42, "putt": 16, "game_pt": -5},
        2: {"score": 45, "putt": 18, "game_pt": 10},
    }


def test_suggest_scores_ignores_rows_without_enough_values():
    assert suggest_scores("山田太郎 42", [{"member_id": 1, "name": "山田太郎"}]) == {}
