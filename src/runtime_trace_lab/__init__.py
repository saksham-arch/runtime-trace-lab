"""Runtime span validation and analysis."""

from .spans import Span, SpanTiming, TraceSummary, analyze_spans, summarize_trace

__all__ = ["Span", "SpanTiming", "TraceSummary", "analyze_spans", "summarize_trace"]
