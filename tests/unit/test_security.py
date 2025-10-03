from app.services.security import (
    hash_api_key,
    sign_webhook_payload,
    verify_webhook_signature,
)


def test_hash_api_key_is_deterministic():
    key = "abc123"
    assert hash_api_key(key) == hash_api_key(key)


def test_webhook_signature_roundtrip():
    payload = b'{"event": "test"}'
    signature = sign_webhook_payload(payload, secret="secret")
    assert verify_webhook_signature(payload, signature, secret="secret")
    assert not verify_webhook_signature(payload, signature + "0", secret="secret")
