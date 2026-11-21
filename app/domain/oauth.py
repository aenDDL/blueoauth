from dataclasses import dataclass
from enum import StrEnum, auto


@dataclass
class ExternalUser:
    provider: str
    uid: str
    name: str
    email: str | None = None

    def generate_key(self) -> str:
        return f"{self.provider}: {self.uid}"


class OAuthBackend(StrEnum):
    google = auto()
    github = auto()
