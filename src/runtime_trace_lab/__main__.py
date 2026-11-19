import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .spans import Span, analyze_spans, summarize_operations, summarize_trace


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    item: dict[str, object] = {}
    for key, value in pairs:
        if key in item:
            raise ValueError(f"duplicate field {key!r}")
        item[key] = value
    return item


def load_spans(path: Path) -> list[Span]:
    spans: list[Span] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line, object_pairs_hook=_unique_fields)
                if not isinstance(item, dict):
                    raise ValueError("span must be a JSON object")
                if not isinstance(item.get("span_id"), str) or not isinstance(item.get("name"), str):
                    raise ValueError("span_id and name must be strings")
                if item.get("parent_id") is not None and not isinstance(item["parent_id"], str):
                    raise ValueError("parent_id must be a string or null")
                if type(item.get("start_ns")) is not int or type(item.get("end_ns")) is not int:
                    raise ValueError("timestamps must be integer nanoseconds")
                spans.append(
                    Span(
                        span_id=item["span_id"],
                        parent_id=item.get("parent_id"),
                        name=item["name"],
                        start_ns=item["start_ns"],
                        end_ns=item["end_ns"],
                    )
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid span on line {line_number}: {error}") from error
    return spans


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze runtime span JSONL")
    parser.add_argument("path", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    spans = load_spans(args.path)
    timings = [asdict(item) for item in analyze_spans(spans)]
    payload = (
        {
            "trace": asdict(summarize_trace(spans)),
            "operations": [asdict(item) for item in summarize_operations(spans)],
            "spans": timings,
        }
        if args.summary
        else timings
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
