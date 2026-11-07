from collections.abc import Awaitable, Callable

from authlib.integrations.starlette_client import OAuthError
from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from loguru import logger

type ErrorHandler = Callable[[Request, Exception], Awaitable[Response]]


async def handle_oauth_error(
    _request: Request,
    exc: OAuthError,
) -> JSONResponse:
    logger.error("Error occurred during authorization.\n{}", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Login failed."},
    )


def get_error_handlers() -> dict[type[Exception], ErrorHandler]:
    return {
        OAuthError: handle_oauth_error,
    }
