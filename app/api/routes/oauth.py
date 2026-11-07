from typing import Any, NewType, Protocol

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from loguru import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.domain.oauth import OAuthBackend

router = APIRouter(route_class=DishkaRoute)


class GenerateRedirectUriFn(Protocol):
    async def __call__(self, request: Request) -> RedirectResponse: ...


class HandleCallbackFn(Protocol):
    async def __call__(self, request: Request) -> dict[str, Any]: ...


RedirectUriRegistry = NewType(
    "RedirectUriRegistry",
    dict[OAuthBackend, GenerateRedirectUriFn],
)

CallbackRegistry = NewType(
    "CallbackRegistry",
    dict[OAuthBackend, HandleCallbackFn],
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
    oauth_backend: OAuthBackend,
):
    logger.info("New request to finish login with {}.", oauth_backend)
    handle_callback = registry[oauth_backend]
    payload = await handle_callback(request)  # ruff: ignore[unused-variable]
    # logic: validation for openid/oauth, token generation, cookies
    logger.info("Successful login via {}.", oauth_backend)
    return {"status": "ok"}  # should be redirect to home
