"""ラウンド中のオフラインスコア入力用PWAの起動・同期画面。"""

import json

import streamlit as st

from modules.auth import require_login
from modules.calculation_logic import calculate_player_points
from modules.db import ensure_supabase
from modules.data_formatter import initialize_player_data
from modules.input_helpers import close_sidebar_on_mobile
from modules.offline_score_pwa import offline_instance_id, render_offline_score_pwa
from modules.round_results import get_round_results, save_round_results
from modules.supabase_client import get_scores_with_fallback


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

    round_data = round_result.data[0]
    return {
        "format": "golf-score-offline-v1",
        "instance_id": offline_instance_id(round_data, players),
        "round": round_data,
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
    if not payload.get("sync_exported_at"):
        raise ValueError(
            "開始用ファイルです。入力画面の「入力後：同期用ファイルを出力」から保存した -sync.json を選んでください"
        )
    return round_data["round_id"], players


def _recalculate_round_results(supabase, round_id):
    """通常のスコア入力と同じポイント計算を、同期後に実行する。"""
    scores = get_scores_with_fallback(round_id)
    if not scores:
        raise ValueError("同期後のスコアデータを取得できませんでした")

    round_result = (
        supabase.table("rounds").select("*").eq("round_id", round_id).execute()
    )
    if not round_result.data:
        raise ValueError("ラウンド情報を取得できませんでした")

    handicaps_result = (
        supabase.table("handicap_match")
        .select("*")
        .eq("round_id", round_id)
        .execute()
    )
    handicaps = {}
    total_only_set = set()
    for handicap in handicaps_result.data or []:
        player_1_id = handicap["player_1_id"]
        player_2_id = handicap["player_2_id"]
        handicaps[(player_1_id, player_2_id)] = handicap["player_1_to_2"]
        handicaps[(player_2_id, player_1_id)] = handicap["player_2_to_1"]
        if handicap.get("total_only"):
            total_only_set.add(frozenset((player_1_id, player_2_id)))

    player_data = initialize_player_data(scores, get_round_results(round_id))
    player_ids = sorted(player_data)
    updated_player_data = calculate_player_points(
        player_data,
        player_ids,
        handicaps,
        total_only_set,
        round_result.data[0],
    )
    if not save_round_results(round_id, updated_player_data):
        raise ValueError("計算結果を保存できませんでした")
    return len(updated_player_data)


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

    calculated_count = _recalculate_round_results(supabase, round_id)
    return round_id, updated_count, calculated_count


def run():
    require_login()
    close_sidebar_on_mobile()
    st.title("📱 オフライン入力")
    st.caption("出発前に開始ファイルを保存し、現地で入力、通信復帰後に同期します。")

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
        st.warning("開始ファイルを作成できる未確定ラウンドがありません。先にラウンド設定を保存してください。")
        st.page_link(
            "pages/01_ラウンド設定.py",
            label="① ラウンド設定へ",
            icon="🗓️",
            use_container_width=True,
        )
        return

    st.subheader("① 出発前：入力するラウンドを選択")
    st.info("最初にラウンド設定を保存してください。ここには、保存済みで未確定のラウンドだけが表示されます。")
    options = _round_options(rounds)
    selected_round_id = st.selectbox(
        "オフライン入力するラウンドを選択",
        options=list(options),
        format_func=options.get,
    )
    package = _create_offline_package(supabase, selected_round_id)

    st.success("選択したラウンドは、下の入力画面へ自動で読み込まれます。")
    st.download_button(
        "予備の開始ファイルを保存（JSON）",
        data=json.dumps(package, ensure_ascii=False, indent=2),
        file_name=f"golf-round-{selected_round_id}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("通常は保存不要です。別の端末で入力する場合や、入力画面へ自動読込できない場合だけ使用します。")
    st.divider()
    st.subheader("② 現地：スコアを入力")
    st.info("選択したラウンドは自動で読み込まれます。そのまま入力してください。OUT・IN終了後やラウンド終了後に端末へ保存できます。")
    render_offline_score_pwa(package)
    st.divider()
    st.subheader("③ 通信復帰後：同期ファイルを読み込んで反映")
    st.warning("ここでは、現地入力画面で出力した **-sync.json** だけを選びます。①の開始ファイル（golf-round-XX.json）は選びません。")
    uploaded_file = st.file_uploader("同期ファイル（-sync.json）を選択", type=["json"])
    confirmed = st.checkbox("現在のスコアを同期ファイルの内容で更新する")
    if st.button("同期して結果を更新", type="primary", disabled=not (uploaded_file and confirmed)):
        try:
            payload = json.loads(uploaded_file.getvalue().decode("utf-8"))
            round_id, updated_count, calculated_count = _sync_offline_package(supabase, payload)
            st.success(
                f"ラウンド {round_id} の {updated_count}人分を同期し、{calculated_count}人分の "
                "マッチ対戦・パット・合計ポイントを再計算しました。"
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            st.error(f"同期できませんでした: {error}")
        except Exception:
            st.error("同期に失敗しました。通信状況を確認して再度お試しください。")


if __name__ == "__main__":
    run()
