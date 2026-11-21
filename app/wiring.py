from dataclasses import asdict
from functools import partial

from authlib.integrations.starlette_client import OAuth
from dishka import Provider, Scope, from_context, provide

from app.adapters.oauth import (
    OAuthData,
    get_oauth_data,
)
from app.api.routes.oauth import CallbackRegistry, RedirectUriRegistry
from app.settings import Settings


class OAuthProvider(Provider):
    scope = Scope.APP
    settings = from_context(Settings)

    @provide
    def wire_oauth_data(self) -> OAuthData:
        return OAuthData(get_oauth_data())

    @provide
    def wire_oauth(self, settings: Settings, data: OAuthData) -> OAuth:
        oauth = OAuth()
        for key, value in data.items():
            credentials = settings.oauth[key]
            oauth.register(
                name=key,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret.get_secret_value(),
                **asdict(value.config),
            )
        return oauth

    @provide
    def wire_oauth_redirect(
        self,
        oauth: OAuth,
        settings: Settings,
        data: OAuthData,
    ) -> RedirectUriRegistry:
        return RedirectUriRegistry({
            name: partial(
                oauth.create_client(name).authorize_redirect,
                redirect_uri=settings.oauth[name].redirect_uri,
            )
            for name in data
        })

    @provide
    def wire_oauth_callback(
        self,
        oauth: OAuth,
        data: OAuthData,
    ) -> CallbackRegistry:
        return CallbackRegistry({
            key: partial(
                value.fetch_identity,
                client=oauth.create_client(key),
            )
            for key, value in data.items()
        })


def get_all_providers() -> frozenset[Provider]:
    return frozenset({OAuthProvider()})
