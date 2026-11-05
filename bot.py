"""Entrypoint for the Discord music bot."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from music.config import ConfigError, Settings
from music.discord_bot import DiscordMusicBot


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        settings = Settings.from_env(os.environ)
    except ConfigError as exc:
        raise SystemExit(f"configuration error: {exc}") from exc

    DiscordMusicBot(settings).run(settings.token)


if __name__ == "__main__":
    main()
