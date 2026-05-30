import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from repo_python.main import greeting
from repo_python.page_generator import build_html, write_html


class GreetingTests(unittest.TestCase):
    def test_default_greeting(self) -> None:
        self.assertEqual(greeting(), "Hello from Python project")

    def test_custom_greeting(self) -> None:
        self.assertEqual(greeting("Codex"), "Hello from Codex")


class PageGeneratorTests(unittest.TestCase):
    def test_build_html_contains_title(self) -> None:
        html = build_html(title="My Test Page")

        self.assertIn("<title>My Test Page</title>", html)
        self.assertIn("<h1>My Test Page</h1>", html)

    def test_write_html_creates_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "docs" / "index.html"

            written_path = write_html(output_path)

            self.assertEqual(written_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("Python Generated Web Page", output_path.read_text())


if __name__ == "__main__":
    unittest.main()
