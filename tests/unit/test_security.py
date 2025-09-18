from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password


def test_password_hash_round_trip():
    password = "super-secret"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_token_generation():
    token = create_access_token("user-id")
    refresh = create_refresh_token("user-id")
    assert isinstance(token, str)
    assert isinstance(refresh, str)
    assert token != refresh
