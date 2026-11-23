from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.errors import get_error_handlers
from app.api.routes import home, oauth
from app.settings import FastAPISettings, Settings
from app.wiring import get_all_providers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await app.state.dishka_container.close()


def create_app(settings: FastAPISettings, container: AsyncContainer) -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        exception_handlers=get_error_handlers(),
    )
    app.include_router(oauth.router, prefix=settings.oauth_prefix, tags=["oauth"])
    app.include_router(home.router, prefix=settings.home_prefix, tags=["api"])
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.middleware_key.get_secret_value(),
        https_only=settings.https_only,
    )
    setup_dishka(container, app)
    return app


def create_container(settings: Settings) -> AsyncContainer:
    return make_async_container(
        *get_all_providers(),
        context={Settings: settings},
    )


def main() -> FastAPI:
    settings = Settings()
    return create_app(settings.fastapi, create_container(settings))
