from dataclasses import asdict, dataclass
from typing import Literal, NewType, Protocol

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status
from loguru import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.domain.oauth import ExternalUser, OAuthBackend

router = APIRouter(route_class=DishkaRoute)


@dataclass(frozen=True)
class CookieConfig:
    max_age: int
    path: str
    secure: bool
    httponly: bool
    samesite: Literal["lax", "strict", "none"]


class GenerateRedirectUriFn(Protocol):
    async def __call__(self, request: Request) -> RedirectResponse: ...


class GetExternalIdentity(Protocol):
    async def __call__(self, request: Request) -> ExternalUser: ...


class CreateAccessTokenFn(Protocol):
    def __call__(self, data: dict[str, str]) -> str: ...


RedirectUriRegistry = NewType(
    "RedirectUriRegistry",
    dict[OAuthBackend, GenerateRedirectUriFn],
)

CallbackRegistry = NewType(
    "CallbackRegistry",
    dict[OAuthBackend, GetExternalIdentity],
)


@router.get("/login/{oauth_backend}")
async def login(
    request: Request,
    registry: FromDishka[RedirectUriRegistry],
    oauth_backend: OAuthBackend,
):
    logger.info("New request to login with {}.", oauth_backend)
    generate_redirect_uri = registry[oauth_backend]
    return await generate_redirect_uri(request)


@router.get("/callback/{oauth_backend}")
async def callback(
    request: Request,
    registry: FromDishka[CallbackRegistry],
    create_access_token: FromDishka[CreateAccessTokenFn],
    cookie_config: FromDishka[CookieConfig],
    oauth_backend: OAuthBackend,
):
    logger.info("New request to finish login with {}.", oauth_backend)

    get_external_identity = registry[oauth_backend]
    payload = await get_external_identity(request)

    key = payload.generate_key()
    access_token = create_access_token({"sub": key})

    redirect = RedirectResponse(
        request.app.url_path_for("home"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    redirect.set_cookie("access_token", access_token, **asdict(cookie_config))

    logger.info("Successful login for user {}.", key)
    return redirect
