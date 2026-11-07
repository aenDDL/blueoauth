from pydantic import BaseModel, SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.domain.oauth import OAuthBackend


class OAuthSettings(BaseModel):
    client_id: str
    client_secret: SecretStr
    redirect_uri: str


class FastAPISettings(BaseModel):
    oauth_prefix: str = "/oauth"
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
