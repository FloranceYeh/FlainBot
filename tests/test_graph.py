from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flainbot import Graph, GraphError, GraphExecutor


class GraphTests(unittest.TestCase):
    def test_graph_routes_output_ports_to_input_ports(self):
        class Source:
            name = "source"

            def run(self, inputs):
                return {"text": "hello"}

        class Upper:
            name = "upper"

            def run(self, inputs):
                return {"text": inputs["text"].upper()}

        graph = Graph()
        graph.add_node("source", Source())
        graph.add_node("upper", Upper())
        graph.connect("source", "text", "upper", "text")

        outputs = GraphExecutor(graph).run()

        self.assertEqual(outputs["source"]["text"], "hello")
        self.assertEqual(outputs["upper"]["text"], "HELLO")

    def test_graph_routes_one_output_to_multiple_inputs(self):
        class Source:
            name = "source"

            def run(self, inputs):
                return {"text": "hello"}

        class Suffix:
            def __init__(self, suffix):
                self.suffix = suffix

            def run(self, inputs):
                return {"text": f"{inputs['text']}{self.suffix}"}

        graph = Graph()
        graph.add_node("source", Source())
        graph.add_node("first", Suffix(" one"))
        graph.add_node("second", Suffix(" two"))
        graph.connect("source", "text", "first", "text")
        graph.connect("source", "text", "second", "text")

        outputs = GraphExecutor(graph).run()

        self.assertEqual(outputs["first"]["text"], "hello one")
        self.assertEqual(outputs["second"]["text"], "hello two")

    def test_graph_executes_dependencies_before_dependents(self):
        calls = []

        class First:
            name = "first"

            def run(self, inputs):
                calls.append("first")
                return {"value": 2}

        class Second:
            name = "second"

            def run(self, inputs):
                calls.append("second")
                return {"value": inputs["value"] + 1}

        graph = Graph()
        graph.add_node("second", Second())
        graph.add_node("first", First())
        graph.connect("first", "value", "second", "value")

        outputs = GraphExecutor(graph).run()

        self.assertEqual(calls, ["first", "second"])
        self.assertEqual(outputs["second"]["value"], 3)

    def test_graph_executor_records_node_trace(self):
        class Source:
            name = "source"

            def run(self, inputs):
                return {"text": "hello"}

        class Upper:
            name = "upper"

            def run(self, inputs):
                return {"text": inputs["text"].upper()}

        graph = Graph()
        graph.add_node("source", Source())
        graph.add_node("upper", Upper())
        graph.connect("source", "text", "upper", "text")

        executor = GraphExecutor(graph)
        executor.run()

        self.assertEqual(
            executor.trace,
            [
                {"node_id": "source", "inputs": {}, "outputs": {"text": "hello"}},
                {"node_id": "upper", "inputs": {"text": "hello"}, "outputs": {"text": "HELLO"}},
            ],
        )

    def test_graph_rejects_cycles(self):
        class Passthrough:
            name = "passthrough"

            def run(self, inputs):
                return {"value": inputs.get("value", 1)}

        graph = Graph()
        graph.add_node("a", Passthrough())
        graph.add_node("b", Passthrough())
        graph.connect("a", "value", "b", "value")
        graph.connect("b", "value", "a", "value")

        with self.assertRaisesRegex(GraphError, "cycle"):
            GraphExecutor(graph).run()


if __name__ == "__main__":
    unittest.main()
