from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.domain.oauth import OAuthBackend


class OAuthSettings(BaseModel):
    client_id: str
    client_secret: SecretStr
    redirect_uri: str


class JWTSettings(BaseModel):
    algorithm: str = "HS256"
    secret_key: SecretStr


class AccessCookieSettings(BaseModel):
    max_age: int = 60 * 30
    path: str = "/api"
    secure: bool = True
    httponly: bool = True
    samesite: Literal["lax", "strict", "none"] = "lax"


class FastAPISettings(BaseModel):
    oauth_prefix: str = "/oauth"
    access_cookie: AccessCookieSettings = Field(default_factory=AccessCookieSettings)
    https_only: bool = True
    middleware_key: SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    oauth: dict[OAuthBackend, OAuthSettings]
    fastapi: FastAPISettings
    jwt: JWTSettings
