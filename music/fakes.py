"""Deterministic fakes for the offline harness and the tests."""

from __future__ import annotations

from .models import Track, TrackRequest


class FakeResolver:
    def __init__(self, catalog: dict[str, TrackRequest] | None = None) -> None:
        self.catalog = {
            query.lower(): request for query, request in (catalog or {}).items()
        }

    async def resolve(self, query: str) -> TrackRequest | None:
        return self.catalog.get(query.strip().lower())


class FakeSearcher:
    def __init__(self, catalog: dict[str, list[Track]] | None = None) -> None:
        self.catalog = {
            query.lower(): tracks for query, tracks in (catalog or {}).items()
        }

    async def search(self, query: str, *, limit: int = 5) -> list[Track]:
        return list(self.catalog.get(query.strip().lower(), []))[:limit]


class FakePlaybackTarget:
    def __init__(self) -> None:
        self.current: Track | None = None
        self.played: list[Track] = []
        self.stop_calls = 0

    @property
    def playing(self) -> bool:
        return self.current is not None

    async def play(self, track: Track) -> None:
        self.current = track
        self.played.append(track)

    async def stop(self) -> None:
        self.current = None
        self.stop_calls += 1
