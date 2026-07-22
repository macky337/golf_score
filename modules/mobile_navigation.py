"""スマホ向けの共通ボトムナビゲーション。"""

import streamlit as st


def navigation_link(page, label, icon, key, use_container_width=True):
    """ページリンクを表示し、テスト環境ではボタンへフォールバックする。"""
    try:
        st.page_link(
            page,
            label=label,
            icon=icon,
            use_container_width=use_container_width,
        )
    except KeyError:
        if st.button(
            f"{icon} {label}",
            key=key,
            use_container_width=use_container_width,
        ):
            st.switch_page(page)


def render_mobile_navigation():
    """スマホだけに固定ボトムナビゲーションを表示する。"""
    st.markdown(
        """
        <style>
        .st-key-mobile_bottom_nav {
            display: none;
        }

        @media (max-width: 768px) {
            [data-testid="stSidebar"],
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapsedControl"],
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }

            [data-testid="stAppViewContainer"] .main .block-container {
                padding-bottom: calc(5.6rem + env(safe-area-inset-bottom)) !important;
            }

            .st-key-mobile_bottom_nav {
                display: block;
                position: fixed;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 999999;
                padding: 0.35rem 0.35rem calc(0.35rem + env(safe-area-inset-bottom));
                border-top: 1px solid rgba(128, 128, 128, 0.28);
                background: var(--background-color);
                background: color-mix(in srgb, var(--background-color) 94%, transparent);
                box-shadow: 0 -5px 18px rgba(0, 0, 0, 0.12);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
            }

            .st-key-mobile_bottom_nav [data-testid="stHorizontalBlock"] {
                gap: 0.15rem;
            }

            .st-key-mobile_bottom_nav [data-testid="stColumn"] {
                min-width: 0 !important;
            }

            .st-key-mobile_bottom_nav a[data-testid="stPageLink-NavLink"] {
                min-height: 3.35rem;
                padding: 0.25rem 0.1rem;
                border-radius: 0.75rem;
                justify-content: center;
                text-align: center;
                font-size: 0.72rem;
                font-weight: 650;
                line-height: 1.05;
                white-space: nowrap;
            }

            .st-key-mobile_bottom_nav a[data-testid="stPageLink-NavLink"] span {
                margin: 0 !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="mobile_bottom_nav"):
        home, front, back, results, menu = st.columns(5)
        with home:
            navigation_link("main.py", "ホーム", "🏠", "mobile_nav_home")
        with front:
            navigation_link(
                "pages/02_フロントスコア入力.py",
                "フロント",
                "1️⃣",
                "mobile_nav_front",
            )
        with back:
            navigation_link(
                "pages/03_バックスコア入力.py",
                "バック",
                "2️⃣",
                "mobile_nav_back",
            )
        with results:
            navigation_link(
                "pages/05_結果確認.py",
                "結果",
                "📊",
                "mobile_nav_results",
            )
        with menu:
            navigation_link(
                "pages/00_メニュー.py",
                "メニュー",
                "📋",
                "mobile_nav_menu",
            )
