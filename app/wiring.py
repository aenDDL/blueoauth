import datetime as dt
from dataclasses import asdict
from functools import partial

from authlib.integrations.starlette_client import OAuth
from dishka import Provider, Scope, from_context, provide
from joserfc import jwk, jwt

from app.adapters.oauth import (
    OAuthData,
    get_oauth_data,
)
from app.api.routes.home import VerifyTokenFn
from app.api.routes.oauth import (
    CallbackRegistry,
    CookieConfig,
    CreateAccessTokenFn,
    RedirectUriRegistry,
)
from app.services.tokens import create_access_token, verify_access_token
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


class SecurityProvider(Provider):
    scope = Scope.APP

    @provide
    def wire_cookie_config(self, s: Settings) -> CookieConfig:
        return CookieConfig(**s.fastapi.access_cookie.model_dump())

    @provide(provides=CreateAccessTokenFn)
    def wire_create_access_token(
        self,
        s: Settings,
    ) -> CreateAccessTokenFn:
        return partial(
            create_access_token,
            get_now=partial(dt.datetime.now, dt.UTC),
            expires_delta=dt.timedelta(seconds=s.fastapi.access_cookie.max_age),
            secret_key=jwk.import_key(s.jwt.secret_key.get_secret_value(), "oct"),
            algorithm=s.jwt.algorithm,
        )

    @provide(provides=VerifyTokenFn)
    def wire_verify_token(
        self,
        s: Settings,
    ) -> VerifyTokenFn:
        claims_registry = jwt.JWTClaimsRegistry(
            leeway=10,
            exp={"essential": True},
        )
        return partial(
            verify_access_token,
            secret_key=jwk.import_key(s.jwt.secret_key.get_secret_value(), "oct"),
            algorithm=s.jwt.algorithm,
            claims_registry=claims_registry,
        )


def get_all_providers() -> frozenset[Provider]:
    return frozenset({OAuthProvider(), SecurityProvider()})
