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
python3 -m unittest discover -s tests
```

Exclusive duration subtracts the union of direct-child intervals, so
overlapping children are not double-counted. Timestamps must share one
monotonic clock domain.

Summary mode reports the trace envelope, the union of root-span coverage, and
peak simultaneous spans. Spans ending exactly when another starts are not
concurrent, and zero-duration spans do not raise the peak. This metric describes
instrumented span overlap, not operating-system thread or CPU concurrency.

Summary mode also groups validated span timings by operation name, reporting
counts plus total and median inclusive and exclusive duration. Totals can
identify where the supplied trace spent time, but they are not a statistical
claim about other runs. Inclusive totals can double-count nested work;
exclusive totals subtract direct-child coverage.
