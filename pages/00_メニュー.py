"""スマホから主要機能へ移動するためのメニューページ。"""

import streamlit as st

from modules.auth import render_logout_button, require_login
from modules.input_helpers import close_sidebar_on_mobile
from modules.mobile_navigation import navigation_link


st.set_page_config(
    page_title="メニュー - Golf Score App",
    page_icon="☰",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def run():
    require_login()
    close_sidebar_on_mobile()

    st.title("メニュー")
    st.caption("目的の機能を選んでください。")

    st.subheader("ラウンド")
    left, right = st.columns(2)
    with left:
        navigation_link(
            "pages/01_ラウンド設定.py",
            "ラウンド設定",
            "🗓️",
            "menu_round_settings",
        )
        navigation_link(
            "pages/04_エキストラスコア入力.py",
            "エキストラ入力",
            "➕",
            "menu_extra",
        )
    with right:
        navigation_link(
            "pages/11_オフライン入力.py",
            "オフライン入力",
            "📱",
            "menu_offline",
        )
        navigation_link(
            "pages/06_ポイント集計.py",
            "ポイント集計",
            "🏆",
            "menu_points",
        )

    st.subheader("登録・管理")
    left, right = st.columns(2)
    with left:
        navigation_link(
            "pages/07_メンバー登録.py",
            "メンバー登録",
            "👤",
            "menu_members",
        )
        navigation_link(
            "pages/08_管理画面.py",
            "管理画面",
            "⚙️",
            "menu_admin",
        )
    with right:
        navigation_link(
            "pages/09_コース管理.py",
            "コース管理",
            "⛳",
            "menu_courses",
        )
        navigation_link(
            "pages/10_マニュアル.py",
            "マニュアル",
            "📖",
            "menu_manual",
        )

    st.divider()
    st.caption("アカウント")
    render_logout_button(key="mobile_menu_logout")


if __name__ == "__main__":
    run()
