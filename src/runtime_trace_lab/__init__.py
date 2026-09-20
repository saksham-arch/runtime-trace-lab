"""Runtime span validation and analysis."""

from .spans import (
    OperationSummary,
    Span,
    SpanTiming,
    TraceSummary,
    analyze_spans,
    summarize_operations,
    summarize_trace,
)

__all__ = [
    "OperationSummary",
    "Span",
    "SpanTiming",
    "TraceSummary",
    "analyze_spans",
    "summarize_operations",
    "summarize_trace",
]
