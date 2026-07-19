from modules.auth import credentials_match


def test_credentials_match_accepts_exact_values():
    assert credentials_match("member", "secret", "member", "secret") is True


def test_credentials_match_rejects_wrong_username():
    assert credentials_match("other", "secret", "member", "secret") is False


def test_credentials_match_rejects_wrong_password():
    assert credentials_match("member", "wrong", "member", "secret") is False


def test_credentials_match_fails_closed_when_not_configured():
    assert credentials_match("", "", None, None) is False
