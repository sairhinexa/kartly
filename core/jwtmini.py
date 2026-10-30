







import hmac
import json
import base64
import hashlib


JWT_SECRET = "kartly"


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64u_decode(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


def encode(payload: dict, secret: str = JWT_SECRET) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (_b64u_encode(json.dumps(header, separators=(",", ":")).encode())
                     + "." + _b64u_encode(json.dumps(payload, separators=(",", ":")).encode()))
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64u_encode(sig)


def decode(token: str, secret: str = JWT_SECRET) -> dict:
    signing_input, _, sig = token.rpartition(".")
    expected = _b64u_encode(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid signature")
    payload_seg = signing_input.split(".", 1)[1]
    return json.loads(_b64u_decode(payload_seg))
