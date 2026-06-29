from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendStaticTests(unittest.TestCase):
    def test_planner_page_references_assets_and_nodes(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

        self.assertIn("FlainBot Node Planner", html)
        self.assertIn("styles.css", html)
        self.assertIn("app.js", html)
        self.assertIn("OpenAIChatNode", js)
        self.assertIn("AnthropicMessagesNode", js)
        self.assertIn("generatePython", js)


if __name__ == "__main__":
    unittest.main()
