import asyncio
import threading
import unittest

from music.models import TrackRequest
from music.spotify import SpotifyResolver


class FakeSpotify:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str, int]] = []
        self.threads: list[str] = []

    def search(self, q: str, type: str = "track", limit: int = 1) -> dict:
        self.calls.append((q, type, limit))
        self.threads.append(threading.current_thread().name)
        return self.payload


def payload(title: str = "Song", artist: str = "Artist", album: str = "Album") -> dict:
    return {
        "tracks": {
            "items": [
                {
                    "name": title,
                    "artists": [{"name": artist}],
                    "album": {"name": album},
                }
            ]
        }
    }


class SpotifyResolverTests(unittest.TestCase):
    def resolve(self, fake: FakeSpotify, query: str = "song"):
        resolver = SpotifyResolver("id", "secret", client=fake)
        return asyncio.run(resolver.resolve(query))

    def test_maps_the_first_track(self) -> None:
        fake = FakeSpotify(payload())

        request = self.resolve(fake, query="never gonna give you up")

        self.assertEqual(
            request,
            TrackRequest(title="Song", artist="Artist", album="Album"),
        )
        self.assertEqual(fake.calls, [("never gonna give you up", "track", 1)])

    def test_uses_free_text_search(self) -> None:
        # The old implementation sent ``track:<query>``, which only matches
        # Spotify's field syntax and failed for ordinary song names.
        fake = FakeSpotify(payload())

        self.resolve(fake, query="daft punk one more time")

        self.assertEqual(fake.calls[0][0], "daft punk one more time")

    def test_calls_spotipy_off_the_event_loop(self) -> None:
        fake = FakeSpotify(payload())

        self.resolve(fake)

        self.assertNotEqual(fake.threads, [threading.current_thread().name])

    def test_no_results_returns_none(self) -> None:
        self.assertIsNone(self.resolve(FakeSpotify({"tracks": {"items": []}})))

    def test_missing_keys_do_not_raise(self) -> None:
        self.assertIsNone(self.resolve(FakeSpotify({})))

    def test_partial_payload_is_tolerated(self) -> None:
        request = self.resolve(
            FakeSpotify({"tracks": {"items": [{"name": "Only A Name"}]}})
        )

        self.assertEqual(request, TrackRequest(title="Only A Name", artist="", album=""))


if __name__ == "__main__":
    unittest.main()
