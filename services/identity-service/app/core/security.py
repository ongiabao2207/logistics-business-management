from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings


password_hasher = PasswordHash.recommended()


class TokenValidationError(Exception):
    pass


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def _read_key(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to read JWT key at {path}") from exc


def create_access_token(*, account_id: int, username: str, role: str, settings: Settings) -> tuple[str, int]:
    now = datetime.now(UTC)
    expires_in = settings.access_token_ttl_minutes * 60
    claims = {
        "sub": str(account_id),
        "username": username,
        "role": role,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "jti": str(uuid4()),
    }
    token = jwt.encode(
        claims,
        _read_key(settings.jwt_private_key_path),
        algorithm="RS256",
        headers={"kid": "identity-key-1", "typ": "JWT"},
    )
    return token, expires_in


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        return jwt.decode(
            token,
            _read_key(settings.jwt_public_key_path),
            algorithms=["RS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "role", "iss", "aud", "iat", "exp", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenValidationError("Invalid or expired access token") from exc


def public_jwk(settings: Settings) -> dict:
    import json
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    public_key = load_pem_public_key(_read_key(settings.jwt_public_key_path).encode("utf-8"))
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(public_key))
    return {**jwk, "kid": "identity-key-1", "use": "sig", "alg": "RS256"}
