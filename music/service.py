"""Play and queue decisions, independent of Discord and Lavalink.

The Discord adapter supplies a real :class:`PlaybackTarget`; the harness and
the tests supply a fake. Nothing here imports ``discord``, ``wavelink`` or
``spotipy``, so it runs on a bare Python installation.
"""

from __future__ import annotations

from collections import deque
from typing import Protocol

from .models import Outcome, Reply, Track, TrackRequest


class TrackResolver(Protocol):
    async def resolve(self, query: str) -> TrackRequest | None: ...


class TrackSearcher(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[Track]: ...


class PlaybackTarget(Protocol):
    @property
    def playing(self) -> bool: ...

    async def play(self, track: Track) -> None: ...

    async def stop(self) -> None: ...


class MusicService:
    """State for one guild's queue."""

    def __init__(
        self,
        resolver: TrackResolver,
        searcher: TrackSearcher,
        target: PlaybackTarget,
    ) -> None:
        self._resolver = resolver
        self._searcher = searcher
        self._target = target
        self._queue: deque[Track] = deque()

    @property
    def target(self) -> PlaybackTarget:
        return self._target

    @property
    def queue(self) -> tuple[Track, ...]:
        return tuple(self._queue)

    async def play(self, query: str) -> Reply:
        query = query.strip()
        if not query:
            return Reply(
                Outcome.NO_RESULTS,
                "Nothing to play",
                "Give me a song name, for example `?play never gonna give you up`.",
            )

        request = await self._resolver.resolve(query)
        if request is None:
            return Reply(
                Outcome.NO_RESULTS,
                "No match",
                f"Spotify had no track for **{query}**.",
            )

        search = f"{request.title} {request.artist}".strip()
        tracks = await self._searcher.search(search, limit=1)
        if not tracks:
            return Reply(
                Outcome.NO_RESULTS,
                "No match",
                f"Could not find **{request.title}** on YouTube.",
            )

        track = tracks[0]
        if self._target.playing:
            self._queue.append(track)
            return Reply(
                Outcome.QUEUED,
                "Queued",
                f"**{track.title}** is #{len(self._queue)} in the queue.",
            )

        await self._target.play(track)
        return Reply(
            Outcome.PLAYING,
            "Now playing",
            f"**{track.title}** by {track.author}",
        )

    async def skip(self) -> Reply:
        if not self._queue:
            if self._target.playing:
                await self._target.stop()
            return Reply(
                Outcome.QUEUE_EMPTY,
                "Queue empty",
                "Nothing left to play.",
            )

        track = self._queue.popleft()
        await self._target.play(track)
        return Reply(
            Outcome.SKIPPED,
            "Now playing",
            f"**{track.title}** by {track.author}",
        )

    async def advance(self) -> Reply | None:
        """Start the next queued track after one finishes playing."""

        if not self._queue:
            return None

        track = self._queue.popleft()
        await self._target.play(track)
        return Reply(
            Outcome.PLAYING,
            "Now playing",
            f"**{track.title}** by {track.author}",
        )

    def queue_reply(self) -> Reply:
        if not self._queue:
            return Reply(Outcome.QUEUE_INFO, "Queue", "The queue is empty.")

        lines = [
            f"{position}. **{track.title}** by {track.author}"
            for position, track in enumerate(self._queue, start=1)
        ]
        return Reply(Outcome.QUEUE_INFO, "Queue", "\n".join(lines))

    async def disconnect(self) -> Reply:
        self._queue.clear()
        await self._target.stop()
        return Reply(Outcome.DISCONNECTED, "Disconnected", "Left the voice channel.")
