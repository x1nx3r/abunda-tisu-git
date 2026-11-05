"""Environment-backed settings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import os

DEFAULT_LAVALINK_URI = "http://localhost:2333"
DEFAULT_LAVALINK_PASSWORD = "youshallnotpass"


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing."""


@dataclass(frozen=True, slots=True)
class Settings:
    token: str
    spotify_client_id: str
    spotify_client_secret: str
    lavalink_uri: str = DEFAULT_LAVALINK_URI
    lavalink_password: str = DEFAULT_LAVALINK_PASSWORD
    command_prefix: str = "?"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if environ is None else environ

        def read(name: str, default: str = "") -> str:
            return (env.get(name) or default).strip()

        required = ("DISCORD_TOKEN", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET")
        missing = [name for name in required if not read(name)]
        if missing:
            raise ConfigError(
                "missing required environment variables: " + ", ".join(missing)
            )

        return cls(
            token=read("DISCORD_TOKEN"),
            spotify_client_id=read("SPOTIFY_CLIENT_ID"),
            spotify_client_secret=read("SPOTIFY_CLIENT_SECRET"),
            lavalink_uri=read("LAVALINK_URI", DEFAULT_LAVALINK_URI),
            lavalink_password=read("LAVALINK_PASSWORD", DEFAULT_LAVALINK_PASSWORD),
            command_prefix=read("COMMAND_PREFIX", "?") or "?",
        )
