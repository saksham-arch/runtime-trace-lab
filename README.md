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

Summary mode reports the trace envelope and the union of root-span coverage, so
concurrent roots do not inflate observed wall time.
