import unittest

from repo_python.main import greeting


class GreetingTests(unittest.TestCase):
    def test_default_greeting(self) -> None:
        self.assertEqual(greeting(), "Hello from Python project")

    def test_custom_greeting(self) -> None:
        self.assertEqual(greeting("Codex"), "Hello from Codex")


if __name__ == "__main__":
    unittest.main()
