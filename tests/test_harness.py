import asyncio
import io
import unittest
from contextlib import redirect_stdout

from music import harness


class HarnessTests(unittest.TestCase):
    def test_scripted_session_passes(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            code = asyncio.run(harness.run())

        self.assertEqual(code, 0, output.getvalue())
        self.assertIn("0 failed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
