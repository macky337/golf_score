import copy
import pprint
from modules.calculation_logic import calculate_player_points

# 5ラウンド分のダミーデータ（ラウンド情報）
dummy_rounds = [
    {
        "round_id": 1,
        "has_extra": False,
        "date_played": "2023-01-01",
        "course_name": "コースA"
    },
    {
        "round_id": 2,
        "has_extra": True,
        "date_played": "2023-02-01",
        "course_name": "コースB"
    },
    {
        "round_id": 3,
        "has_extra": False,
        "date_played": "2023-03-01",
        "course_name": "コースC"
    },
    {
        "round_id": 4,
        "has_extra": True,
        "date_played": "2023-04-01",
        "course_name": "コースD"
    },
    {
        "round_id": 5,
        "has_extra": False,
        "date_played": "2023-05-01",
        "course_name": "コースE"
    }
]

# ダミーのプレイヤーデータ（4名の場合の例）
dummy_player_data_template = {
    1: {"Player": "Alice", "Front Score": 40, "Back Score": 45, "Extra Score": 0,
        "Front GP": 10, "Back GP": 10, "Extra GP": 0, "match_pt": 0,
        # 追加: パットスコア
        "Putt Front": 0, "Putt Back": 0, "Putt Extra": 0},
    2: {"Player": "Bob", "Front Score": 42, "Back Score": 44, "Extra Score": 0,
        "Front GP": 8, "Back GP": 12, "Extra GP": 0, "match_pt": 0,
        "Putt Front": 0, "Putt Back": 0, "Putt Extra": 0},
    3: {"Player": "Charlie", "Front Score": 41, "Back Score": 46, "Extra Score": 0,
        "Front GP": 9, "Back GP": 11, "Extra GP": 0, "match_pt": 0,
        "Putt Front": 0, "Putt Back": 0, "Putt Extra": 0},
    4: {"Player": "Diana", "Front Score": 43, "Back Score": 43, "Extra Score": 0,
        "Front GP": 7, "Back GP": 13, "Extra GP": 0, "match_pt": 0,
        "Putt Front": 0, "Putt Back": 0, "Putt Extra": 0},
}

# ダミーハンディキャップ（全ペア0）およびTotal Onlyペア（例として1対2のみ）
dummy_hc = {
    (2, 1): 0, (1, 2): 0,
    (3, 1): 0, (1, 3): 0,
    (4, 1): 0, (1, 4): 0,
    (3, 2): 0, (2, 3): 0,
    (4, 2): 0, (2, 4): 0,
    (4, 3): 0, (3, 4): 0,
}
dummy_total_only_set = {frozenset([1, 2])}

def run_dummy_tests():
    for rnd in dummy_rounds:
        # 各ラウンドごとにテンプレートをDeepCopy
        player_data = copy.deepcopy(dummy_player_data_template)
        player_ids = sorted(list(player_data.keys()))
        active_round = rnd

        # has_extra が True の場合、Extra Scoreにダミー値を設定
        if active_round.get("has_extra"):
            for pid in player_data:
                player_data[pid]["Extra Score"] = 38
        else:
            for pid in player_data:
                player_data[pid]["Extra Score"] = 0

        # Total Scoreを計算
        for pid, data in player_data.items():
            data["Total Score"] = data["Front Score"] + data["Back Score"]

        updated_data = calculate_player_points(player_data, player_ids, dummy_hc, dummy_total_only_set, active_round)

        print("Round:", rnd["round_id"])
        pprint.pprint(updated_data)
        print("-----------------------------------------------------\n")

if __name__ == '__main__':
    run_dummy_tests()
