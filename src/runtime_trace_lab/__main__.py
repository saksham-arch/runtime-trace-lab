import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .spans import Span, analyze_spans, summarize_trace


def load_spans(path: Path) -> list[Span]:
    spans: list[Span] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                spans.append(
                    Span(
                        span_id=str(item["span_id"]),
                        parent_id=None if item.get("parent_id") is None else str(item["parent_id"]),
                        name=str(item["name"]),
                        start_ns=int(item["start_ns"]),
                        end_ns=int(item["end_ns"]),
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
        {"trace": asdict(summarize_trace(spans)), "spans": timings}
        if args.summary
        else timings
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
