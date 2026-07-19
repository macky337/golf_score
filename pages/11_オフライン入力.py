"""ラウンド中のオフラインスコア入力用PWAの起動・同期画面。"""

import json

import streamlit as st

from modules.auth import require_login
from modules.db import ensure_supabase
from modules.input_helpers import close_sidebar_on_mobile
from modules.offline_score_pwa import render_offline_score_pwa


SCORE_FIELDS = (
    "front_score",
    "front_putt",
    "back_score",
    "back_putt",
    "extra_score",
    "extra_putt",
)
GAME_POINT_FIELDS = (
    "front_game_pt",
    "back_game_pt",
    "extra_game_pt",
)
OFFLINE_INPUT_FIELDS = SCORE_FIELDS + GAME_POINT_FIELDS


def _round_options(rounds):
    return {
        round_data["round_id"]: (
            f"{round_data['date_played']} - {round_data['course_name']}"
        )
        for round_data in rounds
    }


def _create_offline_package(supabase, round_id):
    round_result = supabase.table("rounds").select("*").eq("round_id", round_id).execute()
    score_result = (
        supabase.table("score")
        .select("*, member:member_id(name)")
        .eq("round_id", round_id)
        .execute()
    )
    if not round_result.data:
        raise ValueError("ラウンドが見つかりません")

    players = []
    for score in score_result.data or []:
        players.append(
            {
                "member_id": score["member_id"],
                "name": (score.get("member") or {}).get("name", "未登録"),
                **{field: score.get(field) or 0 for field in OFFLINE_INPUT_FIELDS},
            }
        )

    return {
        "format": "golf-score-offline-v1",
        "round": round_result.data[0],
        "players": players,
        "checkpoints": {},
    }


def _validate_offline_package(payload):
    if not isinstance(payload, dict) or payload.get("format") != "golf-score-offline-v1":
        raise ValueError("オフラインスコアファイルの形式が正しくありません")
    round_data = payload.get("round")
    players = payload.get("players")
    if not isinstance(round_data, dict) or not isinstance(round_data.get("round_id"), int):
        raise ValueError("ラウンドIDが不正です")
    if not isinstance(players, list) or not players:
        raise ValueError("プレイヤーデータがありません")
    return round_data["round_id"], players


def _sync_offline_package(supabase, payload):
    round_id, players = _validate_offline_package(payload)
    existing_scores = (
        supabase.table("score").select("member_id").eq("round_id", round_id).execute().data
    )
    known_member_ids = {item["member_id"] for item in existing_scores or []}
    updated_count = 0

    for player in players:
        member_id = player.get("member_id")
        if not isinstance(member_id, int) or member_id not in known_member_ids:
            raise ValueError("パッケージ内に対象外メンバーが含まれています")

        values = {}
        for field in OFFLINE_INPUT_FIELDS:
            value = player.get(field, 0)
            is_game_point = field in GAME_POINT_FIELDS
            minimum, maximum = (-1000, 1000) if is_game_point else (0, 200)
            if not isinstance(value, int) or value < minimum or value > maximum:
                raise ValueError(f"スコア値が不正です: {field}")
            values[field] = value

        supabase.table("score").update(values).eq("round_id", round_id).eq(
            "member_id", member_id
        ).execute()
        updated_count += 1

    return round_id, updated_count


def run():
    require_login()
    close_sidebar_on_mobile()
    st.title("📱 オフラインスコア入力")
    st.caption("電波が弱い場所でも、端末内にスコアを保存できます。")

    st.info(
        "1. 開始前にラウンドデータをダウンロード  →  "
        "2. PWAでオフライン入力  →  "
        "3. 終了後に同期ファイルを読み込み"
    )

    supabase = ensure_supabase()
    rounds = (
        supabase.table("rounds")
        .select("round_id, date_played, course_name, finalized")
        .eq("finalized", False)
        .order("date_played", desc=True)
        .execute()
        .data
    )
    if not rounds:
        st.warning("オフライン入力用の未確定ラウンドがありません。")
        return

    options = _round_options(rounds)
    selected_round_id = st.selectbox(
        "ラウンドを選択",
        options=list(options),
        format_func=options.get,
    )
    package = _create_offline_package(supabase, selected_round_id)

    st.download_button(
        "1. ラウンドデータを保存",
        data=json.dumps(package, ensure_ascii=False, indent=2),
        file_name=f"golf-round-{selected_round_id}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("下の入力画面でダウンロードしたJSONを読み込みます。ラウンド中はそのまま開き続けてください。")
    render_offline_score_pwa()
    st.divider()
    st.subheader("3. 同期ファイルを保存")
    uploaded_file = st.file_uploader("オフライン入力から出力したJSON", type=["json"])
    confirmed = st.checkbox("現在のスコアをオフライン入力の内容で更新する")
    if st.button("一括同期", type="primary", disabled=not (uploaded_file and confirmed)):
        try:
            payload = json.loads(uploaded_file.getvalue().decode("utf-8"))
            round_id, updated_count = _sync_offline_package(supabase, payload)
            st.success(f"ラウンド {round_id} の {updated_count}人分を同期しました。結果確認で最終計算を実行できます。")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            st.error(f"同期できませんでした: {error}")
        except Exception:
            st.error("同期に失敗しました。通信状況を確認して再度お試しください。")


if __name__ == "__main__":
    run()
