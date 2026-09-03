from dataclasses import dataclass
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
    inclusive_ns: int
    exclusive_ns: int


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
                inclusive,
                inclusive - _covered_duration(child_intervals),
            )
        )
    return sorted(results, key=lambda item: (-item.inclusive_ns, item.span_id))
