# runtime-trace-lab

Dependency-free primitives for validating and analyzing runtime spans. The
first increment reads JSON Lines spans, verifies parent relationships and time
containment, then reports inclusive and exclusive duration for each span.

```json
{"span_id":"request","parent_id":null,"name":"GET /items","start_ns":0,"end_ns":100}
```

```bash
PYTHONPATH=src python3 -m runtime_trace_lab trace.jsonl
PYTHONPATH=src python3 -m runtime_trace_lab trace.jsonl --summary
PYTHONPATH=src python3 -m unittest discover -s tests
```

Exclusive duration subtracts the union of direct-child intervals, so
overlapping children are not double-counted. Timestamps must share one
monotonic clock domain. Each analyzed span includes its zero-based parent depth:
roots are depth 0, their children are depth 1, and so on.

Summary mode reports the trace envelope, the union of root-span coverage, and
peak simultaneous spans. `root_coverage_ratio` divides root coverage by the
trace envelope, making gaps between root spans visible; it is `null` for a
zero-duration trace. A gap can reflect missing instrumentation or intentional
idle time, so coverage is not a completeness score. Spans ending exactly when
another starts are not concurrent, and zero-duration spans do not raise the
peak. This metric describes instrumented span overlap, not operating-system
thread or CPU concurrency.
The trace summary also reports maximum nesting depth. Depth describes emitted
parent relationships; it is not a call-stack sample or a measure of complexity.

Summary mode also groups validated span timings by operation name, reporting
counts plus total, median, and nearest-rank p95 inclusive and exclusive
duration. P95 exposes slower observed spans but is coarse for small groups and
does not predict unobserved requests. Totals can identify where the supplied
trace spent time, but they are not a statistical claim about other runs.
Inclusive totals can double-count nested work; exclusive totals subtract
direct-child coverage.
Each operation also reports its share of the total exclusive duration across
all validated spans in the supplied trace. Shares sum to one when any exclusive
duration exists and are `null` for an all-zero-duration trace. This is a
composition of emitted spans, not CPU utilization or a claim about untraced
work; overlapping branches can also accumulate more exclusive duration than
wall-clock time.
