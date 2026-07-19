"""入力画面で共通利用する操作中ラウンド管理。"""

import streamlit as st


def select_editable_round(supabase, key):
    """未確定ラウンドを選択し、現在の操作対象として返す。"""
    rounds = (
        supabase.table("rounds")
        .select("*")
        .eq("finalized", False)
        .order("date_played", desc=True)
        .execute()
        .data
        or []
    )
    if not rounds:
        st.warning("入力できる未確定ラウンドがありません。")
        st.page_link(
            "pages/01_ラウンド設定.py",
            label="新しいラウンドを設定",
            icon="🗓️",
            use_container_width=True,
        )
        return None

    round_by_id = {item["round_id"]: item for item in rounds}
    round_ids = list(round_by_id)
    active_round_id = st.session_state.get("active_round_id")
    default_index = round_ids.index(active_round_id) if active_round_id in round_ids else 0

    selected_round_id = st.selectbox(
        "操作するラウンド",
        options=round_ids,
        index=default_index,
        format_func=lambda round_id: (
            f"{round_by_id[round_id]['date_played']} - "
            f"{round_by_id[round_id]['course_name']}"
        ),
        key=key,
    )
    st.session_state.active_round_id = selected_round_id
    active_round = round_by_id[selected_round_id]
    st.caption(
        f"操作中：{active_round['date_played']}・{active_round['course_name']}・未確定"
    )
    return active_round
