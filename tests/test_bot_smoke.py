import asyncio
import unittest

from music.config import Settings
from music.discord_bot import DiscordMusicBot, Music

SETTINGS = Settings(
    token="test-token",
    spotify_client_id="test-client-id",
    spotify_client_secret="test-client-secret",
    command_prefix="?",
)

EXPECTED_COMMANDS = {"ping", "play", "skip", "queue", "disconnect"}


class BotSmokeTests(unittest.TestCase):
    def test_commands_register_without_connecting(self) -> None:
        bot = DiscordMusicBot(SETTINGS)

        async def scenario() -> set[str]:
            await bot.add_cog(Music(bot))
            names = {command.name for command in bot.commands}
            await bot.close()
            return names

        names = asyncio.run(scenario())

        self.assertTrue(
            EXPECTED_COMMANDS.issubset(names),
            f"missing commands: {EXPECTED_COMMANDS - names}",
        )

    def test_prefix_comes_from_settings(self) -> None:
        bot = DiscordMusicBot(SETTINGS)

        self.assertEqual(bot.command_prefix, "?")

    def test_searcher_targets_youtube(self) -> None:
        bot = DiscordMusicBot(SETTINGS)

        self.assertEqual(bot.searcher.source.name, "YouTube")


if __name__ == "__main__":
    unittest.main()
