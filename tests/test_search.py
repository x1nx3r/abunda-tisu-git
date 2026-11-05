import asyncio
import unittest
from types import SimpleNamespace
from unittest import mock

import wavelink

from music.search import WavelinkSearcher


def playable(title: str, author: str = "Artist", uri: str = "https://example.invalid/x"):
    return SimpleNamespace(title=title, author=author, uri=uri)


class WavelinkSearcherTests(unittest.TestCase):
    def search(self, result, query: str = "query", limit: int = 5):
        with mock.patch.object(
            wavelink.Playable, "search", new=mock.AsyncMock(return_value=result)
        ) as search:
            tracks = asyncio.run(WavelinkSearcher().search(query, limit=limit))
        return tracks, search

    def test_maps_playables_and_keeps_the_reference(self) -> None:
        first = playable("First")
        second = playable("Second")

        tracks, search = self.search([first, second])

        self.assertEqual([track.title for track in tracks], ["First", "Second"])
        self.assertIs(tracks[0].reference, first)
        search.assert_awaited_once_with(
            "query", source=wavelink.TrackSource.YouTube
        )

    def test_accepts_a_playlist_like_result(self) -> None:
        tracks, _ = self.search(SimpleNamespace(tracks=[playable("From playlist")]))

        self.assertEqual([track.title for track in tracks], ["From playlist"])

    def test_respects_the_limit(self) -> None:
        tracks, _ = self.search([playable("One"), playable("Two")], limit=1)

        self.assertEqual(len(tracks), 1)

    def test_empty_result(self) -> None:
        tracks, _ = self.search([])

        self.assertEqual(tracks, [])


if __name__ == "__main__":
    unittest.main()
