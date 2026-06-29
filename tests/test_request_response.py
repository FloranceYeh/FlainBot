from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import MessageContext, Pipeline, RequestNode, ResponseNode


class RequestResponseTests(unittest.TestCase):
    def test_request_response_nodes_run_minimal_chat_chain(self):
        seen_requests = []

        def fake_client(request):
            seen_requests.append(request)
            return {"text": f"echo: {request['messages'][-1]['content']}"}

        pipeline = Pipeline(
            [
                RequestNode(client=fake_client),
                ResponseNode(),
            ]
        )

        context = pipeline.run(MessageContext(input_text="hello"))

        self.assertEqual(
            seen_requests,
            [{"messages": [{"role": "user", "content": "hello"}]}],
        )
        self.assertEqual(context.data["request"]["messages"][0]["content"], "hello")
        self.assertEqual(context.data["response"]["text"], "echo: hello")
        self.assertEqual(context.output_text, "echo: hello")
        self.assertEqual(
            [trace.node_name for trace in context.trace],
            ["request", "response"],
        )

    def test_request_node_accepts_custom_request_builder(self):
        def fake_client(request):
            return {"text": request["prompt"].upper()}

        def build_request(context):
            return {"prompt": context.input_text}

        pipeline = Pipeline(
            [
                RequestNode(client=fake_client, build_request=build_request),
                ResponseNode(),
            ]
        )

        context = pipeline.run(MessageContext(input_text="hello"))

        self.assertEqual(context.data["request"], {"prompt": "hello"})
        self.assertEqual(context.output_text, "HELLO")


if __name__ == "__main__":
    unittest.main()
