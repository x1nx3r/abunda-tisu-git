import asyncio
import unittest
from types import SimpleNamespace

import wavelink

from music.config import Settings
from music.discord_bot import DiscordMusicBot, Music, WavelinkTarget
from music.fakes import FakePlaybackTarget, FakeResolver, FakeSearcher
from music.models import Track, TrackRequest
from music.service import MusicService

SETTINGS = Settings(
    token="test-token",
    spotify_client_id="test-client-id",
    spotify_client_secret="test-client-secret",
)

TRACK = Track("Lonely Boy", "The Black Keys", "https://example.invalid/lonely-boy")


def make_playable() -> wavelink.Playable:
    return wavelink.Playable(
        {
            "encoded": "not-a-real-track",
            "info": {
                "identifier": "lonely-boy",
                "isSeekable": True,
                "author": "The Black Keys",
                "length": 200_000,
                "isStream": False,
                "sourceName": "youtube",
                "title": "Lonely Boy",
                "uri": "https://example.invalid/lonely-boy",
                "position": 0,
                "isrc": None,
                "artworkUrl": None,
            },
            "pluginInfo": {},
        }
    )


class FakePlayer:
    def __init__(self) -> None:
        self.playing = False
        self.played: list[wavelink.Playable] = []
        self.stop_calls = 0

    async def play(self, track: wavelink.Playable) -> None:
        self.playing = True
        self.played.append(track)

    async def stop(self) -> None:
        self.playing = False
        self.stop_calls += 1


class WavelinkTargetTests(unittest.IsolatedAsyncioTestCase):
    async def test_play_forwards_the_playable(self) -> None:
        playable = make_playable()
        player = FakePlayer()
        target = WavelinkTarget(player)

        await target.play(Track(TRACK.title, TRACK.author, TRACK.uri, reference=playable))

        self.assertEqual(len(player.played), 1)
        self.assertIs(player.played[0], playable)
        self.assertTrue(target.playing)

    async def test_play_without_a_reference_is_rejected(self) -> None:
        target = WavelinkTarget(FakePlayer())

        with self.assertRaises(TypeError):
            await target.play(TRACK)

    async def test_stop_only_touches_a_playing_player(self) -> None:
        player = FakePlayer()
        target = WavelinkTarget(player)

        await target.stop()
        self.assertEqual(player.stop_calls, 0)

        player.playing = True
        await target.stop()
        self.assertEqual(player.stop_calls, 1)


class TrackEndTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.bot = DiscordMusicBot(SETTINGS)
        self.cog = Music(self.bot)
        await self.bot.add_cog(self.cog)

        self.target = FakePlaybackTarget()
        self.service = MusicService(
            FakeResolver({"song": TrackRequest("Song", "Artist", "Album")}),
            FakeSearcher({"song artist": [TRACK]}),
            self.target,
        )
        self.player = SimpleNamespace(guild=SimpleNamespace(id=42))
        self.bot.services[42] = (self.player, self.service)  # type: ignore[assignment]
        self.announcements: list[dict] = []
        self.bot.announce_channels[42] = self  # type: ignore[assignment]

    async def asyncTearDown(self) -> None:
        await self.bot.close()

    async def send(self, **kwargs) -> None:
        self.announcements.append(kwargs)

    async def test_finished_track_advances_the_queue(self) -> None:
        await self.service.play("song")
        await self.service.play("song")

        await self.cog.on_wavelink_track_end(
            SimpleNamespace(player=self.player, reason="finished")
        )

        self.assertEqual(len(self.target.played), 2)
        self.assertEqual(len(self.announcements), 1)

    async def test_stopped_track_is_ignored(self) -> None:
        await self.service.play("song")

        await self.cog.on_wavelink_track_end(
            SimpleNamespace(player=self.player, reason="stopped")
        )

        self.assertEqual(len(self.target.played), 1)
        self.assertEqual(self.announcements, [])

    async def test_missing_player_is_ignored(self) -> None:
        await self.cog.on_wavelink_track_end(
            SimpleNamespace(player=None, reason="finished")
        )

        self.assertEqual(self.target.played, [])


if __name__ == "__main__":
    unittest.main()
