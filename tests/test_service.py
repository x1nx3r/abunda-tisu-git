import unittest

from music.fakes import FakePlaybackTarget, FakeResolver, FakeSearcher
from music.models import Outcome, Track, TrackRequest
from music.service import MusicService

RICK = TrackRequest("Never Gonna Give You Up", "Rick Astley", "Whenever You Need Somebody")
SANDSTORM = TrackRequest("Sandstorm", "Darude", "Before the Storm")

RICK_TRACK = Track("Never Gonna Give You Up", "Rick Astley", "https://example.invalid/rick")
SANDSTORM_TRACK = Track("Sandstorm", "Darude", "https://example.invalid/sandstorm")


def make_service(
    searcher: FakeSearcher | None = None,
) -> tuple[MusicService, FakePlaybackTarget]:
    target = FakePlaybackTarget()
    service = MusicService(
        FakeResolver(
            {"never gonna give you up": RICK, "sandstorm": SANDSTORM}
        ),
        searcher
        or FakeSearcher(
            {
                "never gonna give you up rick astley": [RICK_TRACK],
                "sandstorm darude": [SANDSTORM_TRACK],
            }
        ),
        target,
    )
    return service, target


class MusicServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_first_play_starts_the_track(self) -> None:
        service, target = make_service()

        reply = await service.play("never gonna give you up")

        self.assertIs(reply.outcome, Outcome.PLAYING)
        self.assertIs(target.current, RICK_TRACK)
        self.assertEqual(service.queue, ())

    async def test_second_play_is_queued(self) -> None:
        service, target = make_service()
        await service.play("never gonna give you up")

        reply = await service.play("sandstorm")

        self.assertIs(reply.outcome, Outcome.QUEUED)
        self.assertIn("Sandstorm", reply.description)
        self.assertIs(target.current, RICK_TRACK)
        self.assertEqual(service.queue, (SANDSTORM_TRACK,))

    async def test_unknown_spotify_track_is_reported(self) -> None:
        service, target = make_service()

        reply = await service.play("not in the catalogue")

        self.assertIs(reply.outcome, Outcome.NO_RESULTS)
        self.assertIsNone(target.current)

    async def test_unknown_youtube_track_is_reported(self) -> None:
        service, target = make_service(searcher=FakeSearcher({}))

        reply = await service.play("sandstorm")

        self.assertIs(reply.outcome, Outcome.NO_RESULTS)
        self.assertIn("Sandstorm", reply.description)
        self.assertIsNone(target.current)

    async def test_blank_query_is_rejected(self) -> None:
        service, target = make_service()

        reply = await service.play("   ")

        self.assertIs(reply.outcome, Outcome.NO_RESULTS)
        self.assertIsNone(target.current)

    async def test_skip_plays_the_next_track(self) -> None:
        service, target = make_service()
        await service.play("never gonna give you up")
        await service.play("sandstorm")

        reply = await service.skip()

        self.assertIs(reply.outcome, Outcome.SKIPPED)
        self.assertIs(target.current, SANDSTORM_TRACK)
        self.assertEqual(service.queue, ())
        self.assertEqual(len(target.played), 2)

    async def test_skip_with_empty_queue_stops_playback(self) -> None:
        service, target = make_service()
        await service.play("never gonna give you up")

        reply = await service.skip()

        self.assertIs(reply.outcome, Outcome.QUEUE_EMPTY)
        self.assertIsNone(target.current)
        self.assertEqual(target.stop_calls, 1)

    async def test_advance_is_silent_without_a_queue(self) -> None:
        service, target = make_service()

        reply = await service.advance()

        self.assertIsNone(reply)
        self.assertIsNone(target.current)

    async def test_advance_plays_the_next_track(self) -> None:
        service, target = make_service()
        await service.play("never gonna give you up")
        await service.play("sandstorm")

        reply = await service.advance()

        self.assertIsNotNone(reply)
        self.assertIs(reply.outcome, Outcome.PLAYING)
        self.assertIs(target.current, SANDSTORM_TRACK)

    async def test_queue_reply_lists_tracks_in_order(self) -> None:
        service, _ = make_service()
        await service.play("never gonna give you up")
        await service.play("sandstorm")

        reply = service.queue_reply()

        self.assertIs(reply.outcome, Outcome.QUEUE_INFO)
        self.assertIn("1. **Sandstorm**", reply.description)

    async def test_queue_reply_when_empty(self) -> None:
        service, _ = make_service()

        self.assertIn("empty", service.queue_reply().description.lower())

    async def test_disconnect_clears_the_queue_and_player(self) -> None:
        service, target = make_service()
        await service.play("never gonna give you up")
        await service.play("sandstorm")

        reply = await service.disconnect()

        self.assertIs(reply.outcome, Outcome.DISCONNECTED)
        self.assertIsNone(target.current)
        self.assertEqual(service.queue, ())


if __name__ == "__main__":
    unittest.main()
