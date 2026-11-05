import unittest

from music.embeds import BLURPLE, GREY, GREEN, ORANGE, RED, YELLOW, ping_color, ping_embed, reply_embed
from music.models import Outcome, Reply


class PingTests(unittest.TestCase):
    def test_color_tiers(self) -> None:
        cases = {
            0: GREEN,
            50: GREEN,
            51: YELLOW,
            100: YELLOW,
            101: ORANGE,
            200: ORANGE,
            201: RED,
            1000: RED,
        }

        for latency, expected in cases.items():
            with self.subTest(latency=latency):
                self.assertEqual(ping_color(latency), expected)

    def test_embed_reports_the_latency(self) -> None:
        embed = ping_embed(42)

        self.assertEqual(embed.title, "PING")
        self.assertIn("**42** milliseconds", embed.description)
        self.assertEqual(embed.color.value, GREEN)


class ReplyEmbedTests(unittest.TestCase):
    def test_playing_uses_the_success_color(self) -> None:
        embed = reply_embed(Reply(Outcome.PLAYING, "Now playing", "song"))

        self.assertEqual(embed.title, "Now playing")
        self.assertEqual(embed.description, "song")
        self.assertEqual(embed.color.value, GREEN)

    def test_no_results_uses_the_error_color(self) -> None:
        embed = reply_embed(Reply(Outcome.NO_RESULTS, "No match", "nothing"))

        self.assertEqual(embed.color.value, RED)

    def test_queued_uses_the_info_color(self) -> None:
        embed = reply_embed(Reply(Outcome.QUEUED, "Queued", "song"))

        self.assertEqual(embed.color.value, BLURPLE)

    def test_disconnected_uses_the_muted_color(self) -> None:
        embed = reply_embed(Reply(Outcome.DISCONNECTED, "Disconnected", "bye"))

        self.assertEqual(embed.color.value, GREY)


if __name__ == "__main__":
    unittest.main()
