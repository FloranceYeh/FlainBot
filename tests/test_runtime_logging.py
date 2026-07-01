from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot.runtime_logging import RuntimeLogger


class RuntimeLoggingTests(unittest.TestCase):
    def test_runtime_logger_emits_structured_fact_events(self):
        events = []
        logger = RuntimeLogger(
            sink=events.append,
            run_id="run_1",
            session_id="default",
        )

        logger.node_info(
            "provider_call.started",
            node_id="provider_1",
            node_type="provider_call",
            provider_id="openai_main",
            model="gpt-test",
        )

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["level"], "info")
        self.assertEqual(event["source"], "node")
        self.assertEqual(event["message"], "provider_call.started")
        self.assertEqual(
            event["details"],
            {
                "run_id": "run_1",
                "session_id": "default",
                "event": "provider_call.started",
                "node_id": "provider_1",
                "node_type": "provider_call",
                "provider_id": "openai_main",
                "model": "gpt-test",
            },
        )


if __name__ == "__main__":
    unittest.main()
