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
        self.assertIn("graph-canvas", html)
        self.assertIn("edge-layer", html)
        self.assertIn("<marker", html)
        self.assertNotIn("property-editor", html)
        self.assertIn("OpenAIChatNode", js)
        self.assertIn("AnthropicMessagesNode", js)
        self.assertIn("generatePython", js)
        self.assertIn("edges", js)
        self.assertIn("GraphExecutor", js)
        self.assertIn("graph.connect(", js)
        self.assertIn("Graph()", js)
        self.assertIn("pointerdown", js)
        self.assertIn("data-port", js)
        self.assertIn("marker-end", js)

    def test_chat_page_references_assets_and_api(self):
        html = (ROOT / "frontend" / "chat.html").read_text(encoding="utf-8")
        js = (ROOT / "frontend" / "chat.js").read_text(encoding="utf-8")

        self.assertIn("FlainBot Chat", html)
        self.assertIn("chat.css", html)
        self.assertIn("chat.js", html)
        self.assertIn("/api/chat", js)


if __name__ == "__main__":
    unittest.main()
