"""Fake end-to-end run of the music flow.

Drives the real :class:`music.service.MusicService` with a fake metadata
provider, a fake search backend and a fake player. It needs no Discord
connection, no Spotify credentials and no Lavalink, so it runs on a bare
Python install:

    python3 -m music.harness

The scripted session mirrors what ``?play``, ``?skip``, ``?queue`` and
``?disconnect`` do, and exits non-zero if any expectation fails.
"""

from __future__ import annotations

import asyncio
import sys

from .fakes import FakePlaybackTarget, FakeResolver, FakeSearcher
from .models import Outcome, Reply, Track, TrackRequest
from .service import MusicService

CATALOG = {
    "never gonna give you up": TrackRequest(
        "Never Gonna Give You Up", "Rick Astley", "Whenever You Need Somebody"
    ),
    "sandstorm": TrackRequest("Sandstorm", "Darude", "Before the Storm"),
}

SEARCH = {
    "never gonna give you up rick astley": [
        Track(
            "Never Gonna Give You Up",
            "Rick Astley",
            "https://example.invalid/never-gonna-give-you-up",
        )
    ],
    "sandstorm darude": [
        Track("Sandstorm", "Darude", "https://example.invalid/sandstorm")
    ],
}


class _Checks:
    def __init__(self) -> None:
        self.passed = 0
        self.failures: list[str] = []

    def check(self, label: str, condition: bool) -> None:
        if condition:
            self.passed += 1
            print(f"  ok   {label}")
        else:
            self.failures.append(label)
            print(f"  FAIL {label}")

    def show(self, command: str, reply: Reply) -> None:
        print(f"? {command}")
        print(f"  <- [{reply.outcome.value}] {reply.title}: {reply.description}")


async def run() -> int:
    target = FakePlaybackTarget()
    service = MusicService(FakeResolver(CATALOG), FakeSearcher(SEARCH), target)
    checks = _Checks()

    print("== fake session ==")

    reply = await service.play("   ")
    checks.show("?play", reply)
    checks.check("blank query is rejected", reply.outcome is Outcome.NO_RESULTS)

    reply = await service.play("never gonna give you up")
    checks.show("?play never gonna give you up", reply)
    checks.check("idle player starts the track", reply.outcome is Outcome.PLAYING)
    checks.check("first track reached the player", target.current is not None)

    reply = await service.play("sandstorm")
    checks.show("?play sandstorm", reply)
    checks.check("busy player queues the track", reply.outcome is Outcome.QUEUED)
    checks.check("queue holds one track", len(service.queue) == 1)

    reply = await service.play("a song that does not exist")
    checks.show("?play a song that does not exist", reply)
    checks.check("unknown song is reported, not raised", reply.outcome is Outcome.NO_RESULTS)
    checks.check("failed lookup leaves the queue alone", len(service.queue) == 1)

    reply = await service.skip()
    checks.show("?skip", reply)
    checks.check("skip plays the queued track", reply.outcome is Outcome.SKIPPED)
    checks.check(
        "player history is in order",
        [track.title for track in target.played]
        == ["Never Gonna Give You Up", "Sandstorm"],
    )
    checks.check("queue is drained", service.queue == ())

    reply = await service.advance()
    checks.check("natural track end with empty queue is silent", reply is None)

    reply = await service.skip()
    checks.show("?skip (empty)", reply)
    checks.check("skip with nothing queued stops playback", reply.outcome is Outcome.QUEUE_EMPTY)
    checks.check("player actually stopped", target.current is None)

    reply = service.queue_reply()
    checks.show("?queue", reply)
    checks.check("empty queue is reported", "empty" in reply.description.lower())

    reply = await service.play("never gonna give you up")
    checks.show("?play never gonna give you up", reply)
    checks.check("playback restarts after a stop", reply.outcome is Outcome.PLAYING)

    reply = await service.disconnect()
    checks.show("?disconnect", reply)
    checks.check("disconnect clears the player", target.current is None)
    checks.check("disconnect clears the queue", service.queue == ())
    checks.check("disconnect was reported", reply.outcome is Outcome.DISCONNECTED)

    print(f"\n{checks.passed} checks passed, {len(checks.failures)} failed")
    if checks.failures:
        for failure in checks.failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
