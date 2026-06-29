from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import MessageContext, Pipeline, PipelineError


class MessageContextTests(unittest.TestCase):
    def test_context_starts_with_input_and_empty_trace(self):
        context = MessageContext(input_text="hello")

        self.assertEqual(context.input_text, "hello")
        self.assertIsNone(context.output_text)
        self.assertEqual(context.data, {})
        self.assertEqual(context.trace, [])


class PipelineTests(unittest.TestCase):
    def test_pipeline_runs_nodes_in_order(self):
        class CaptureInput:
            name = "capture_input"

            def handle(self, context):
                context.data["captured"] = context.input_text

        class BuildReply:
            name = "build_reply"

            def handle(self, context):
                context.output_text = f"echo: {context.data['captured']}"

        pipeline = Pipeline([CaptureInput(), BuildReply()])

        context = pipeline.run(MessageContext(input_text="hello"))

        self.assertEqual(context.output_text, "echo: hello")

    def test_pipeline_can_insert_extension_between_nodes(self):
        class Start:
            name = "start"

            def handle(self, context):
                context.output_text = "hello"

        class Segment:
            name = "segment"

            def handle(self, context):
                context.output_text = "|".join(context.output_text)

        pipeline = Pipeline([Start()])
        pipeline.insert_after("start", Segment())

        context = pipeline.run(MessageContext(input_text="ignored"))

        self.assertEqual(context.output_text, "h|e|l|l|o")
        self.assertEqual([node.name for node in pipeline.nodes], ["start", "segment"])

    def test_pipeline_records_node_trace(self):
        class Noop:
            name = "noop"

            def handle(self, context):
                context.data["handled"] = True

        context = Pipeline([Noop()]).run(MessageContext(input_text="hello"))

        self.assertEqual(len(context.trace), 1)
        self.assertEqual(context.trace[0].node_name, "noop")
        self.assertEqual(context.trace[0].status, "ok")

    def test_pipeline_wraps_node_errors_with_node_name(self):
        class Broken:
            name = "broken"

            def handle(self, context):
                raise RuntimeError("boom")

        context = MessageContext(input_text="hello")

        with self.assertRaises(PipelineError) as raised:
            Pipeline([Broken()]).run(context)

        self.assertEqual(raised.exception.node_name, "broken")
        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertEqual(context.trace[0].node_name, "broken")
        self.assertEqual(context.trace[0].status, "error")


if __name__ == "__main__":
    unittest.main()
