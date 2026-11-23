import datetime as dt
from collections.abc import Callable
from typing import Any

from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OctKey

type GetNowFn = Callable[[], dt.datetime]


class InvalidTokenError(Exception):
    def __init__(self, details: str):
        super().__init__(details)


def create_access_token(
    data: dict[str, str],
    get_now: GetNowFn,
    expires_delta: dt.timedelta,
    secret_key: OctKey,
    algorithm: str,
) -> str:
    to_encode = data.copy()
    expire = get_now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(
        header={"alg": algorithm},
        claims=to_encode,
        key=secret_key,
        algorithms=[algorithm],
    )


def verify_access_token(
    token: str,
    secret_key: OctKey,
    algorithm: str,
    claims_registry: jwt.JWTClaimsRegistry,
) -> dict[str, Any]:
    try:
        verified_token = jwt.decode(token, secret_key, algorithms=[algorithm])
        claims_registry.validate(verified_token.claims)
    except JoseError as e:
        raise InvalidTokenError(e) from e
    return dict(verified_token.claims)
