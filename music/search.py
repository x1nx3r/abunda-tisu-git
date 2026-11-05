"""Track search backed by Lavalink through wavelink."""

from __future__ import annotations

from typing import Protocol

import wavelink

from .models import Track


class TrackSearcher(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[Track]: ...


class WavelinkSearcher:
    """Turns a text query into playables using ``wavelink.Playable.search``.

    ``Playable.search`` returns either a list of tracks or a playlist; both
    expose the tracks lazily, so the result is flattened with ``getattr``.
    """

    def __init__(
        self, source: wavelink.TrackSource = wavelink.TrackSource.YouTube
    ) -> None:
        self._source = source

    @property
    def source(self) -> wavelink.TrackSource:
        return self._source

    async def search(self, query: str, *, limit: int = 5) -> list[Track]:
        result = await wavelink.Playable.search(query, source=self._source)
        playables = getattr(result, "tracks", result)

        return [
            Track(
                title=playable.title,
                author=playable.author,
                uri=playable.uri,
                reference=playable,
            )
            for playable in list(playables)[:limit]
        ]
