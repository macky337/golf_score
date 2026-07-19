import datetime as dt

from modules.auth import create_session_token, credentials_match, verify_session_token


def test_credentials_match_accepts_exact_values():
    assert credentials_match("member", "secret", "member", "secret") is True


def test_credentials_match_rejects_wrong_username():
    assert credentials_match("other", "secret", "member", "secret") is False


def test_credentials_match_rejects_wrong_password():
    assert credentials_match("member", "wrong", "member", "secret") is False


def test_credentials_match_fails_closed_when_not_configured():
    assert credentials_match("", "", None, None) is False


def test_session_token_is_valid_until_expiry():
    now = dt.datetime(2026, 7, 19, tzinfo=dt.timezone.utc)
    token = create_session_token("member", "secret", now + dt.timedelta(minutes=5))

    assert verify_session_token(token, "member", "secret", now=now) is True


def test_session_token_rejects_tampering_and_expiry():
    now = dt.datetime(2026, 7, 19, tzinfo=dt.timezone.utc)
    token = create_session_token("member", "secret", now + dt.timedelta(minutes=5))
    expired = create_session_token("member", "secret", now - dt.timedelta(minutes=1))

    assert verify_session_token(f"{token}tampered", "member", "secret", now=now) is False
    assert verify_session_token(expired, "member", "secret", now=now) is False
