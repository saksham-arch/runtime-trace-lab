import unittest

from runtime_trace_lab import (
    Span,
    analyze_spans,
    summarize_operations,
    summarize_trace,
)


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

    def test_summarizes_overlapping_root_coverage(self) -> None:
        summary = summarize_trace(
            [Span("a", None, "worker-a", 10, 50), Span("b", None, "worker-b", 40, 80)]
        )
        self.assertEqual(summary.span_count, 2)
        self.assertEqual(summary.root_count, 2)
        self.assertEqual(summary.wall_time_ns, 70)
        self.assertEqual(summary.root_covered_ns, 70)
        self.assertEqual(summary.peak_concurrency, 2)

    def test_peak_concurrency_includes_nested_and_overlapping_spans(self) -> None:
        summary = summarize_trace(
            [
                Span("root", None, "request", 0, 100),
                Span("a", "root", "database", 10, 50),
                Span("b", "root", "cache", 40, 70),
            ]
        )
        self.assertEqual(summary.peak_concurrency, 3)

    def test_touching_and_zero_duration_spans_do_not_inflate_concurrency(self) -> None:
        summary = summarize_trace(
            [
                Span("a", None, "worker-a", 0, 10),
                Span("event", None, "marker", 5, 5),
                Span("b", None, "worker-b", 10, 20),
            ]
        )
        self.assertEqual(summary.peak_concurrency, 1)

    def test_rejects_empty_trace_summary(self) -> None:
        with self.assertRaises(ValueError):
            summarize_trace([])

    def test_summarizes_repeated_operations_by_exclusive_cost(self) -> None:
        spans = [
            Span("root", None, "request", 0, 100),
            Span("db-1", "root", "database", 10, 30),
            Span("db-2", "root", "database", 40, 70),
            Span("cache", "root", "cache", 80, 90),
        ]

        database, request, cache = summarize_operations(spans)

        self.assertEqual(database.name, "database")
        self.assertEqual(database.span_count, 2)
        self.assertEqual(database.total_inclusive_ns, 50)
        self.assertEqual(database.median_inclusive_ns, 25)
        self.assertEqual(database.total_exclusive_ns, 50)
        self.assertEqual(request.name, "request")
        self.assertEqual(request.total_exclusive_ns, 40)
        self.assertEqual(cache.total_exclusive_ns, 10)

    def test_empty_operation_summary_is_empty(self) -> None:
        self.assertEqual(summarize_operations([]), [])


if __name__ == "__main__":
    unittest.main()
