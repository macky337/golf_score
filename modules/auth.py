"""Streamlitアプリ全体で使用する共通ログイン処理。"""

import base64
import binascii
import datetime as dt
import hashlib
import hmac
import os

import streamlit as st

try:
    import extra_streamlit_components as stx
except ImportError:
    stx = None


AUTHENTICATED_KEY = "app_authenticated"
AUTH_USERNAME_KEY = "app_auth_username"
COOKIE_MANAGER_KEY = "_app_cookie_manager_instance"
COOKIE_COMPONENT_KEY = "app_cookie_component"
SESSION_COOKIE = "golf_score_session"
SESSION_TTL = dt.timedelta(days=7)


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


def create_session_token(username, password, expires_at=None):
    """パスワードを含まない、有効期限付き署名トークンを作成する。"""
    if not username or not password:
        return None

    expires_at = expires_at or (dt.datetime.now(dt.timezone.utc) + SESSION_TTL)
    expires_at = int(expires_at.timestamp())
    payload = f"{username}:{expires_at}".encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii")
    signature = hmac.new(
        str(password).encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def verify_session_token(token, expected_username, expected_password, now=None):
    """Cookieトークンの署名・利用者・有効期限を検証する。"""
    if not token or not expected_username or not expected_password:
        return False

    try:
        encoded_payload, signature = token.rsplit(".", 1)
        expected_signature = hmac.new(
            str(expected_password).encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False

        payload = base64.urlsafe_b64decode(encoded_payload.encode("ascii")).decode("utf-8")
        username, expires_at = payload.rsplit(":", 1)
        current_time = int((now or dt.datetime.now(dt.timezone.utc)).timestamp())
        return hmac.compare_digest(username, str(expected_username)) and int(expires_at) > current_time
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return False


def _cookie_manager():
    if stx is None:
        return None

    # CookieManagerはコンポーネントを描画するため、同一実行内で複数回生成すると
    # Streamlitのキーが重複する。セッションごとに1つだけ保持する。
    if COOKIE_MANAGER_KEY not in st.session_state:
        st.session_state[COOKIE_MANAGER_KEY] = stx.CookieManager(key=COOKIE_COMPONENT_KEY)
    return st.session_state[COOKIE_MANAGER_KEY]


def _restore_cookie_session():
    manager = _cookie_manager()
    expected_username, expected_password = get_login_credentials()
    if manager is None or not expected_username or not expected_password:
        return False

    token = manager.get(SESSION_COOKIE)
    if verify_session_token(token, expected_username, expected_password):
        st.session_state[AUTHENTICATED_KEY] = True
        st.session_state[AUTH_USERNAME_KEY] = expected_username
        return True
    return False


def _save_cookie_session(username, password):
    manager = _cookie_manager()
    if manager is None:
        return

    manager.set(
        SESSION_COOKIE,
        create_session_token(username, password),
        expires_at=dt.datetime.now() + SESSION_TTL,
    )


def is_authenticated():
    return st.session_state.get(AUTHENTICATED_KEY, False) is True or _restore_cookie_session()


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
                _save_cookie_session(expected_username, expected_password)
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
            manager = _cookie_manager()
            if manager is not None:
                manager.delete(SESSION_COOKIE)
            st.session_state.clear()
            st.rerun()


def require_login():
    """未ログインならログイン画面だけを表示し、ページ処理を停止する。"""
    if not is_authenticated():
        _render_login()
        st.stop()

    render_logout()
    return True
