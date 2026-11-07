from dataclasses import asdict
from functools import partial

from authlib.integrations.starlette_client import OAuth
from dishka import Provider, Scope, from_context, provide

from app.adapters.oauth import get_oauth_configs
from app.api.routes.oauth import CallbackRegistry, RedirectUriRegistry
from app.settings import Settings


class OAuthProvider(Provider):
    scope = Scope.APP
    settings = from_context(Settings)

    @provide
    def wire_oauth(self, settings: Settings) -> OAuth:
        oauth = OAuth()
        for name, config in get_oauth_configs().items():
            credentials = settings.oauth[name]
            oauth.register(
                name=name,
                client_id=credentials.client_id,
                client_secret=credentials.client_secret.get_secret_value(),
                **asdict(config),
            )
        return oauth

    @provide
    def wire_oauth_redirect(
        self,
        oauth: OAuth,
        settings: Settings,
    ) -> RedirectUriRegistry:
        return RedirectUriRegistry(
            {
                name: partial(
                    oauth.create_client(name).authorize_redirect,
                    redirect_uri=settings.oauth[name].redirect_uri,
                )
                for name in get_oauth_configs()
            },
        )

    @provide
    def wire_oauth_callback(self, oauth: OAuth) -> CallbackRegistry:
        return CallbackRegistry(
            {
                name: oauth.create_client(name).authorize_access_token
                for name in get_oauth_configs()
            },
        )


def get_all_providers() -> frozenset[Provider]:
    return frozenset({OAuthProvider()})
