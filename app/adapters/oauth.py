from dataclasses import dataclass, field
from functools import partial
from typing import NewType, Protocol

from authlib.integrations.starlette_client import StarletteOAuth2App
from loguru import logger
from pydantic import BaseModel, EmailStr
from starlette.requests import Request

from app.domain.oauth import ExternalUser, OAuthBackend

# ============================================================
# OpenID
# ============================================================


@dataclass(frozen=True)
class GoogleConfig:
    server_metadata_url: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    client_kwargs: dict[str, str] = field(
        default_factory=lambda: {"scope": "openid email profile"},
    )


class GoogleOpenIDSchema(BaseModel):
    sub: str
    name: str
    email: EmailStr | None = None


class GoogleSchema(BaseModel):
    userinfo: GoogleOpenIDSchema

    def to_domain(self) -> ExternalUser:
        data = self.userinfo
        return ExternalUser(
            provider=OAuthBackend.google,
            uid=data.sub,
            name=data.name,
            email=data.email,
        )


# ============================================================
# OAuth
# ============================================================


@dataclass(frozen=True)
class GithubConfig:
    access_token_url: str = "https://github.com/login/oauth/access_token"
    authorize_url: str = "https://github.com/login/oauth/authorize"
    api_base_url: str = "https://api.github.com/"
    userinfo_endpoint: str = "https://api.github.com/user"


class GithubSchema(BaseModel):
    id: int
    login: str

    def to_domain(self) -> ExternalUser:
        return ExternalUser(
            provider=OAuthBackend.github,
            uid=str(self.id),
            name=self.login,
        )


# ============================================================
# Functions
# ============================================================

type OAuthSchema = GithubSchema

type OpenIDSchema = GoogleSchema


async def get_identity_openid(
    request: Request,
    client: StarletteOAuth2App,
    expected_schema: type[OpenIDSchema],
) -> ExternalUser:
    response = await client.authorize_access_token(request)
    return expected_schema.model_validate(response).to_domain()


async def get_identity_oauth(
    request: Request,
    client: StarletteOAuth2App,
    expected_schema: type[OAuthSchema],
) -> ExternalUser:
    oauth_response = await client.authorize_access_token(request)
    userinfo_response = await client.userinfo(token=oauth_response)
    logger.debug("Raw userinfo response: {}", userinfo_response)
    return expected_schema.model_validate(userinfo_response).to_domain()


# ============================================================
# Registry
# ============================================================

type Config = GoogleConfig | GithubConfig


class GetIdentityFn(Protocol):
    async def __call__(
        self,
        request: Request,
        client: StarletteOAuth2App,
    ) -> ExternalUser: ...


@dataclass(frozen=True)
class OAuthProviderSpec:
    config: Config
    fetch_identity: GetIdentityFn


OAuthData = NewType(
    "OAuthData",
    dict[OAuthBackend, OAuthProviderSpec],
)


def get_oauth_data() -> OAuthData:
    return {
        OAuthBackend.google: OAuthProviderSpec(
            config=GoogleConfig(),
            fetch_identity=partial(get_identity_openid, expected_schema=GoogleSchema),
        ),
        OAuthBackend.github: OAuthProviderSpec(
            config=GithubConfig(),
            fetch_identity=partial(get_identity_oauth, expected_schema=GithubSchema),
        ),
    }
