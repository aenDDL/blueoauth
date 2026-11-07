from dataclasses import dataclass, field

from app.domain.oauth import OAuthBackend


@dataclass(frozen=True)
class GoogleOAuth:
    server_metadata_url: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )
    client_kwargs: dict[str, str] = field(
        default_factory=lambda: {"scope": "openid email profile"},
    )


@dataclass(frozen=True)
class GithubOAuth:
    access_token_url: str = "https://github.com/login/oauth/access_token"
    authorize_url: str = "https://github.com/login/oauth/authorize"
    api_base_url: str = "https://api.github.com/"
    client_kwargs: dict[str, str] = field(
        default_factory=lambda: {"scope": "user:email"},
    )


type OAuthConfig = GoogleOAuth | GithubOAuth


def get_oauth_configs() -> dict[OAuthBackend, OAuthConfig]:
    return {
        OAuthBackend.google: GoogleOAuth(),
        OAuthBackend.github: GithubOAuth(),
    }
