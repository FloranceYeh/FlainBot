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
        self.assertIn("save-graph", html)
        self.assertIn("id=\"status-message\"", html)
        self.assertIn("graph-canvas", html)
        self.assertIn("edge-layer", html)
        self.assertIn("<marker", html)
        self.assertNotIn("property-editor", html)
        self.assertIn("OpenAIChatNode", js)
        self.assertIn("AnthropicMessagesNode", js)
        self.assertIn("ChatInputNode", js)
        self.assertIn("ChatOutputNode", js)
        self.assertIn("PromptBuilderNode", js)
        self.assertIn("prompt_builder", js)
        self.assertIn("system_prompt", js)
        self.assertIn("user_prompt", js)
        self.assertIn("tools_json", js)
        self.assertIn("context_json", js)
        self.assertIn("\"json\"", js)
        self.assertIn("node.type === \"prompt_builder\"", js)
        self.assertIn("generatePython", js)
        self.assertIn("edges", js)
        self.assertIn("GraphExecutor", js)
        self.assertIn("graph.connect(", js)
        self.assertIn("Graph()", js)
        self.assertIn("pointerdown", js)
        self.assertIn("data-port", js)
        self.assertIn("marker-end", js)
        self.assertIn("apiUrl(\"/api/graph\")", js)
        self.assertIn("setStatus(", js)
        self.assertIn("Could not reach FlainBot server", js)
        self.assertIn("127.0.0.1:8765", js)
        self.assertIn("api_key", js)
        self.assertIn("<form class=\"node-properties\"", js)
        self.assertIn("autocomplete=\"off\"", js)
        self.assertIn("event.preventDefault()", js)

    def test_chat_view_is_in_single_index_shell(self):
        html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
        css = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("FlainBot Chat", html)
        self.assertIn("data-view=\"chat\"", html)
        self.assertIn("id=\"chat-form\"", html)
        self.assertIn("id=\"messages\"", html)
        self.assertNotIn("chat.css", html)
        self.assertNotIn("chat.js", html)
        self.assertIn("setActiveView", js)
        self.assertIn("hashchange", js)
        self.assertIn("apiUrl(\"/api/chat\")", js)
        self.assertIn("127.0.0.1:8765", js)
        self.assertIn(".chat-shell", css)

    def test_standalone_chat_assets_were_removed(self):
        self.assertFalse((ROOT / "frontend" / "chat.html").exists())
        self.assertFalse((ROOT / "frontend" / "chat.js").exists())
        self.assertFalse((ROOT / "frontend" / "chat.css").exists())


if __name__ == "__main__":
    unittest.main()
