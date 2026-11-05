# abunda-tisu

A small Discord music bot. Spotify is used for **search only**; the audio comes
from YouTube through a Lavalink node. `?play never gonna give you up` asks the
Spotify Web API for the best match, then searches YouTube for that title and
artist.

```
?play <query>  ->  Spotify Web API  ->  YouTube search (Lavalink)  ->  voice
```

## Layout

```
bot.py                  entrypoint
music/
  config.py             environment settings
  models.py             transport-free values
  spotify.py            Spotify search (spotipy, off the event loop)
  search.py             YouTube search through wavelink
  service.py            play/queue decisions, stdlib only
  embeds.py             Discord embed rendering
  discord_bot.py        commands, voice, track-end handling
  fakes.py              deterministic fakes
  harness.py            offline end-to-end session
tests/                  unittest suite
scripts/verify.sh       harness + tests, bootstraps its own venv
lavalink/               Lavalink 4 configuration
```

## Requirements

- Python 3.10+
- Java 17+ for Lavalink 4

## Setup

1. Copy the environment template and fill in the Discord and Spotify values:

   ```sh
   cp .env.example .env
   ```

   | Variable | Meaning |
   | --- | --- |
   | `DISCORD_TOKEN` | bot token from the Discord developer portal |
   | `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | Spotify app credentials |
   | `LAVALINK_URI` | node address, default `http://localhost:2333` |
   | `LAVALINK_PASSWORD` | must match the Lavalink config |
   | `COMMAND_PREFIX` | default `?` |

   Lavalink reads its own password from `application.yml`. To change it, either
   edit that file or start the node with `LAVALINK_SERVER_PASSWORD` set, and put
   the same value in the bot's `LAVALINK_PASSWORD`.

2. Download the Lavalink 4 jar into `lavalink/` from
   <https://github.com/lavalink-devs/Lavalink/releases>. The jar is not tracked
   in git. The bundled `application.yml` downloads the YouTube source plugin on
   first start.

3. Start the node:

   ```sh
   cd lavalink && java -jar Lavalink.jar
   ```

4. Install and run the bot:

   ```sh
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python bot.py
   ```

## Commands

| Command | Effect |
| --- | --- |
| `?play <query>` | play now, or queue if something is already playing |
| `?skip` | play the next queued track, or stop |
| `?queue` | list queued tracks |
| `?disconnect` | stop, clear the queue and leave the channel |
| `?ping` | gateway latency |

## Offline check

No tokens, Discord connection or Lavalink are needed for the harness. It drives
the real service with fakes and fails if the play/queue/skip flow regresses:

```sh
python3 -m music.harness
```

The full check also installs the pinned dependencies into `.venv` and runs the
test suite:

```sh
bash scripts/verify.sh
```

## Notes

- The Lavalink config is for Lavalink 4. The old v3 jar that used to be tracked
  here is not compatible with it.
- Playlists are not implemented. The stale wavelink 1.x playlist notes and the
  dead helpers that used to live in `def_func.py` were removed.
- `LAVALINK_PASSWORD` defaults to the config's development value. Set both to
  something private before exposing the node.
