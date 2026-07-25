"""Streamlit UI shared by OUT/IN scorecard image readers."""
from __future__ import annotations

from typing import Any

import streamlit as st

from modules.scorecard_ocr import ScorecardOcrError, extract_scores, is_available


def render_scorecard_reader(scores_data: list[dict[str, Any]], prefix: str, label: str) -> None:
    """Render an OCR review UI and copy accepted suggestions into session state."""
    with st.expander(f"📷 画像から{label}を読み取る", expanded=False):
        st.caption("スコアカード画像を選択し、候補を確認してから入力欄へ反映します。OUT／INの合計スコア・パット・ゲームポイントを読み取ります。")
        if not is_available():
            st.warning("このサーバーでは画像読み取りを利用できません。OPENAI_API_KEY を設定してください。")
            return
        upload = st.file_uploader(
            "スコアカード画像を選択",
            type=["jpg", "jpeg", "png", "webp"],
            key=f"{prefix}_scorecard_upload",
        )
        if upload is None:
            return

        if st.button("画像を読み取る", key=f"{prefix}_scorecard_read", use_container_width=True):
            suffix = "." + (upload.name.rsplit(".", 1)[-1] if "." in upload.name else "jpg")
            try:
                mime_type = upload.type or {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(suffix[1:].lower(), "image/jpeg")
                members = [
                    {"member_id": score["member_id"], "name": (score.get("member") or {}).get("name")}
                    for score in scores_data
                ]
                suggestions = extract_scores(upload.getvalue(), mime_type, members, prefix)
            except ScorecardOcrError as exc:
                st.error(str(exc))
                return
            st.session_state[f"{prefix}_scorecard_suggestions"] = suggestions

        suggestions = st.session_state.get(f"{prefix}_scorecard_suggestions")
        if suggestions is None:
            return
        if not suggestions:
            st.warning("参加者名または集計値を確実に読み取れませんでした。画像全体が入る高解像度のファイルを選択するか、手入力してください。")
        else:
            rows = []
            for score in scores_data:
                member_id = score["member_id"]
                value = suggestions.get(member_id)
                if value:
                    rows.append({"プレイヤー": (score.get("member") or {}).get("name", f"Player {member_id}"), "スコア": value["score"], "パット": value["putt"], "ゲームポイント": value.get("game_pt", "")})
            st.dataframe(rows, use_container_width=True, hide_index=True)
            if st.button("候補を入力欄へ反映", key=f"{prefix}_scorecard_apply", type="primary", use_container_width=True):
                for member_id, value in suggestions.items():
                    st.session_state[f"{prefix}_score_{member_id}"] = value["score"]
                    st.session_state[f"{prefix}_putt_{member_id}"] = value["putt"]
                    if "game_pt" in value:
                        st.session_state[f"{prefix}_game_pt_{member_id}"] = value["game_pt"]
                    # smart_number_input has a device-specific widget key.  Drop
                    # its old value so the suggestion becomes the next default.
                    for field in ("score", "putt", "game_pt"):
                        st.session_state.pop(f"{prefix}_{field}_{member_id}_pc", None)
                        st.session_state.pop(f"{prefix}_{field}_{member_id}_mobile", None)
                st.rerun()
