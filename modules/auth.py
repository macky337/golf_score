"""Streamlitアプリ全体で使用する共通ログイン処理。"""

import hmac
import os

import streamlit as st


AUTHENTICATED_KEY = "app_authenticated"
AUTH_USERNAME_KEY = "app_auth_username"


def _read_secret(name):
    """環境変数、Streamlit secretsの順で設定値を取得する。"""
    value = os.getenv(name)
    if value:
        return value

    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass

    try:
        value = st.secrets["auth"].get(name.lower().removeprefix("app_"))
        if value:
            return value
    except Exception:
        pass

    return None


def get_login_credentials():
    """設定済みのログイン情報を返す。未設定なら ``(None, None)``。"""
    return _read_secret("APP_USERNAME"), _read_secret("APP_PASSWORD")


def credentials_match(input_username, input_password, expected_username, expected_password):
    """ユーザー名とパスワードをタイミング差が出にくい方法で比較する。"""
    if not expected_username or not expected_password:
        return False

    return hmac.compare_digest(str(input_username), str(expected_username)) and hmac.compare_digest(
        str(input_password), str(expected_password)
    )


def is_authenticated():
    return st.session_state.get(AUTHENTICATED_KEY, False) is True


def _render_login():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
            display: none;
        }
        .login-heading {
            text-align: center;
            margin-top: 8vh;
        }
        .login-subtitle {
            color: #667085;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        </style>
        <div class="login-heading"><h1>⛳ Golf Score App</h1></div>
        <div class="login-subtitle">ログインしてスコア管理を始めます</div>
        """,
        unsafe_allow_html=True,
    )

    expected_username, expected_password = get_login_credentials()
    if not expected_username or not expected_password:
        st.error("ログイン情報が設定されていないため、現在アプリを利用できません。")
        st.info("管理者は APP_USERNAME と APP_PASSWORD を設定してください。")
        return False

    _, center, _ = st.columns([1, 2, 1])
    with center:
        with st.form("app_login_form"):
            username = st.text_input("ユーザー名", autocomplete="username")
            password = st.text_input(
                "パスワード",
                type="password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "ログイン",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if credentials_match(username, password, expected_username, expected_password):
                st.session_state[AUTHENTICATED_KEY] = True
                st.session_state[AUTH_USERNAME_KEY] = expected_username
                st.rerun()
            else:
                st.error("ユーザー名またはパスワードが正しくありません。")

    return False


def render_logout():
    """ログイン済み画面のサイドバーへログアウト操作を表示する。"""
    username = st.session_state.get(AUTH_USERNAME_KEY, "")
    with st.sidebar:
        st.divider()
        if username:
            st.caption(f"ログイン中: {username}")
        if st.button("ログアウト", key="app_logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def require_login():
    """未ログインならログイン画面だけを表示し、ページ処理を停止する。"""
    if not is_authenticated():
        _render_login()
        st.stop()

    render_logout()
    return True
