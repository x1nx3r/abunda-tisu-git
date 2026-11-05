import unittest

from music.config import ConfigError, Settings

REQUIRED = {
    "DISCORD_TOKEN": "token",
    "SPOTIFY_CLIENT_ID": "client-id",
    "SPOTIFY_CLIENT_SECRET": "client-secret",
}


class SettingsTests(unittest.TestCase):
    def test_defaults(self) -> None:
        settings = Settings.from_env(REQUIRED)

        self.assertEqual(settings.token, "token")
        self.assertEqual(settings.lavalink_uri, "http://localhost:2333")
        self.assertEqual(settings.lavalink_password, "youshallnotpass")
        self.assertEqual(settings.command_prefix, "?")

    def test_overrides(self) -> None:
        settings = Settings.from_env(
            {
                **REQUIRED,
                "LAVALINK_URI": "http://node.internal:2333",
                "LAVALINK_PASSWORD": "secret-node-password",
                "COMMAND_PREFIX": "!",
            }
        )

        self.assertEqual(settings.lavalink_uri, "http://node.internal:2333")
        self.assertEqual(settings.lavalink_password, "secret-node-password")
        self.assertEqual(settings.command_prefix, "!")

    def test_missing_variables_are_named(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            Settings.from_env({"DISCORD_TOKEN": "token"})

        message = str(caught.exception)
        self.assertIn("SPOTIFY_CLIENT_ID", message)
        self.assertIn("SPOTIFY_CLIENT_SECRET", message)
        self.assertNotIn("DISCORD_TOKEN", message)

    def test_blank_values_count_as_missing(self) -> None:
        with self.assertRaises(ConfigError):
            Settings.from_env({**REQUIRED, "DISCORD_TOKEN": "   "})

    def test_blank_values_are_stripped(self) -> None:
        settings = Settings.from_env({**REQUIRED, "DISCORD_TOKEN": " token "})

        self.assertEqual(settings.token, "token")


if __name__ == "__main__":
    unittest.main()
