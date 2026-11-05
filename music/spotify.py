"""Spotify metadata lookup."""

from __future__ import annotations

import asyncio
from typing import Protocol

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .models import TrackRequest


class TrackResolver(Protocol):
    async def resolve(self, query: str) -> TrackRequest | None: ...


class SpotifyResolver:
    """Resolves free-text queries through the Spotify Web API.

    spotipy is synchronous, so each request is handed to a worker thread.
    Calling it directly from a command coroutine would stall the event loop.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        client: spotipy.Spotify | None = None,
    ) -> None:
        self._client = client or spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret,
            )
        )

    async def resolve(self, query: str) -> TrackRequest | None:
        results = await asyncio.to_thread(
            self._client.search, q=query, type="track", limit=1
        )

        items = (results.get("tracks") or {}).get("items") or []
        if not items:
            return None

        track = items[0] or {}
        artists = track.get("artists") or []
        artist = (artists[0] or {}).get("name", "") if artists else ""
        album = (track.get("album") or {}).get("name", "")

        return TrackRequest(
            title=track.get("name", ""),
            artist=artist,
            album=album,
        )
