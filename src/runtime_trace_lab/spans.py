from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional


@dataclass(frozen=True)
class Span:
    span_id: str
    parent_id: Optional[str]
    name: str
    start_ns: int
    end_ns: int

    def __post_init__(self) -> None:
        if not self.span_id or not self.name:
            raise ValueError("span_id and name must not be empty")
        if self.start_ns < 0 or self.end_ns < self.start_ns:
            raise ValueError("span timestamps must be ordered and non-negative")
        if self.parent_id == self.span_id:
            raise ValueError("a span cannot be its own parent")


@dataclass(frozen=True)
class SpanTiming:
    span_id: str
    parent_id: Optional[str]
    name: str
    depth: int
    inclusive_ns: int
    exclusive_ns: int


@dataclass(frozen=True)
class TraceSummary:
    span_count: int
    root_count: int
    start_ns: int
    end_ns: int
    wall_time_ns: int
    root_covered_ns: int
    root_coverage_ratio: Optional[float]
    peak_concurrency: int
    maximum_depth: int


@dataclass(frozen=True)
class OperationSummary:
    name: str
    span_count: int
    total_inclusive_ns: int
    median_inclusive_ns: float
    total_exclusive_ns: int
    median_exclusive_ns: float


def _covered_duration(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals)
    total = 0
    current_start, current_end = ordered[0]
    for start, end in ordered[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    return total + current_end - current_start


def _peak_concurrency(intervals: list[tuple[int, int]]) -> int:
    events: list[tuple[int, int]] = []
    for start, end in intervals:
        if start == end:
            continue
        events.append((start, 1))
        events.append((end, -1))

    active = 0
    peak = 0
    for _, change in sorted(events):
        active += change
        peak = max(peak, active)
    return peak


def _span_depth(span: Span, indexed: dict[str, Span]) -> int:
    depth = 0
    parent_id = span.parent_id
    while parent_id is not None:
        depth += 1
        parent_id = indexed[parent_id].parent_id
    return depth


def analyze_spans(spans: Iterable[Span]) -> list[SpanTiming]:
    span_list = list(spans)
    indexed = {span.span_id: span for span in span_list}
    if len(indexed) != len(span_list):
        raise ValueError("span_id values must be unique")

    for span in span_list:
        seen = {span.span_id}
        parent_id = span.parent_id
        while parent_id is not None:
            if parent_id in seen:
                raise ValueError("span parent relationships must be acyclic")
            seen.add(parent_id)
            parent = indexed.get(parent_id)
            if parent is None:
                break
            parent_id = parent.parent_id

    children: dict[str, list[Span]] = {}
    for span in span_list:
        if span.parent_id is None:
            continue
        parent = indexed.get(span.parent_id)
        if parent is None:
            raise ValueError(f"missing parent {span.parent_id!r}")
        if span.start_ns < parent.start_ns or span.end_ns > parent.end_ns:
            raise ValueError(f"child {span.span_id!r} falls outside its parent")
        children.setdefault(parent.span_id, []).append(span)

    results: list[SpanTiming] = []
    for span in span_list:
        inclusive = span.end_ns - span.start_ns
        child_intervals = [(child.start_ns, child.end_ns) for child in children.get(span.span_id, [])]
        results.append(
            SpanTiming(
                span.span_id,
                span.parent_id,
                span.name,
                _span_depth(span, indexed),
                inclusive,
                inclusive - _covered_duration(child_intervals),
            )
        )
    return sorted(results, key=lambda item: (-item.inclusive_ns, item.span_id))


def summarize_trace(spans: Iterable[Span]) -> TraceSummary:
    span_list = list(spans)
    if not span_list:
        raise ValueError("at least one span is required")
    # Reuse relationship and containment validation before summarizing.
    timings = analyze_spans(span_list)
    roots = [span for span in span_list if span.parent_id is None]
    start = min(span.start_ns for span in span_list)
    end = max(span.end_ns for span in span_list)
    wall_time = end - start
    root_covered = _covered_duration(
        [(root.start_ns, root.end_ns) for root in roots]
    )
    return TraceSummary(
        span_count=len(span_list),
        root_count=len(roots),
        start_ns=start,
        end_ns=end,
        wall_time_ns=wall_time,
        root_covered_ns=root_covered,
        root_coverage_ratio=(root_covered / wall_time if wall_time > 0 else None),
        peak_concurrency=_peak_concurrency(
            [(span.start_ns, span.end_ns) for span in span_list]
        ),
        maximum_depth=max(timing.depth for timing in timings),
    )


def summarize_operations(spans: Iterable[Span]) -> list[OperationSummary]:
    """Aggregate validated span timings by operation name."""
    grouped: dict[str, list[SpanTiming]] = {}
    for timing in analyze_spans(spans):
        grouped.setdefault(timing.name, []).append(timing)

    summaries: list[OperationSummary] = []
    for name, timings in grouped.items():
        inclusive = [timing.inclusive_ns for timing in timings]
        exclusive = [timing.exclusive_ns for timing in timings]
        summaries.append(
            OperationSummary(
                name=name,
                span_count=len(timings),
                total_inclusive_ns=sum(inclusive),
                median_inclusive_ns=median(inclusive),
                total_exclusive_ns=sum(exclusive),
                median_exclusive_ns=median(exclusive),
            )
        )
    return sorted(
        summaries,
        key=lambda item: (-item.total_exclusive_ns, item.name),
    )
