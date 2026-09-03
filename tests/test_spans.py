import unittest

from runtime_trace_lab import Span, analyze_spans


class SpanAnalysisTests(unittest.TestCase):
    def test_calculates_exclusive_time_without_double_counting_overlap(self) -> None:
        spans = [
            Span("root", None, "request", 0, 100),
            Span("a", "root", "database", 10, 50),
            Span("b", "root", "cache", 40, 70),
        ]
        timings = {item.span_id: item for item in analyze_spans(spans)}
        self.assertEqual(timings["root"].inclusive_ns, 100)
        self.assertEqual(timings["root"].exclusive_ns, 40)
        self.assertEqual(timings["a"].exclusive_ns, 40)

    def test_rejects_duplicate_or_missing_parent(self) -> None:
        with self.assertRaises(ValueError):
            analyze_spans([Span("a", None, "one", 0, 1), Span("a", None, "two", 0, 1)])
        with self.assertRaises(ValueError):
            analyze_spans([Span("child", "missing", "work", 0, 1)])

    def test_rejects_child_outside_parent(self) -> None:
        with self.assertRaises(ValueError):
            analyze_spans([Span("root", None, "root", 5, 10), Span("child", "root", "child", 4, 9)])

    def test_rejects_parent_cycle(self) -> None:
        with self.assertRaises(ValueError):
            analyze_spans([Span("a", "b", "one", 0, 1), Span("b", "a", "two", 0, 1)])


if __name__ == "__main__":
    unittest.main()
