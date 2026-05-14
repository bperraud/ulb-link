from django.conf import settings

import hmac, hashlib


def sign(payload: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def verify_token(token: str):
    try:
        payload, signature = token.split(".")
    except ValueError:
        return None

    expected_signature = sign(payload)

    if hmac.compare_digest(signature, expected_signature):
        return payload

    return None
