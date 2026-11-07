from enum import StrEnum, auto


class OAuthBackend(StrEnum):
    google = auto()
    github = auto()
