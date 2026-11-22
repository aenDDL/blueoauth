import datetime as dt
from collections.abc import Callable

from joserfc import jwt
from joserfc.jwk import OctKey

type GetNowFn = Callable[[], dt.datetime]


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
