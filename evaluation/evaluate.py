#!/usr/bin/env python3
"""API-based evaluation harness for UNI-RAG Agent."""

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REFUSAL_TERMS = (
    "cannot answer", "can't answer", "not available", "not found",
    "insufficient context", "access denied", "not authorized", "restricted",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    cases = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            for field in ("id", "category", "question"):
                if field not in case:
                    raise ValueError(f"Line {line_number} is missing '{field}'")
            cases.append(case)
    return cases


def nested_get(data: dict[str, Any], dotted_path: str, default: Any) -> Any:
    current: Any = data
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def post_json(endpoint: str, payload: dict[str, Any], timeout: float) -> tuple[dict[str, Any], float]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body, round((time.perf_counter() - started) * 1000, 2)


def normalized_sources(items: Any) -> set[str]:
    if not isinstance(items, list):
        return set()
    sources = set()
    for item in items:
        value = item.get("source", "") if isinstance(item, dict) else str(item)
        if value:
            sources.add(Path(value).name.lower())
    return sources


def evaluate_case(case: dict[str, Any], response: dict[str, Any], latency_ms: float, args: argparse.Namespace) -> dict[str, Any]:
    answer = str(nested_get(response, args.answer_field, ""))
    citations = nested_get(response, args.citations_field, [])
    retrieved = nested_get(response, args.sources_field, [])
    expected_sources = {Path(str(x)).name.lower() for x in case.get("expected_sources", [])}
    actual_sources = normalized_sources(retrieved)
    expected_refusal = bool(case.get("expect_refusal", False))
    refused = any(term in answer.lower() for term in REFUSAL_TERMS) or bool(
        nested_get(response, args.refused_field, False)
    )

    retrieval_hit = (
        bool(expected_sources.intersection(actual_sources))
        if expected_sources else None
    )
    citation_present = bool(citations)
    refusal_correct = refused == expected_refusal
    access_correct = (
        refusal_correct if case.get("category") == "access_restricted" else None
    )

    return {
        "id": case["id"],
        "category": case["category"],
        "question": case["question"],
        "retrieval_mode": args.retrieval_mode,
        "answer": answer,
        "expected_sources": sorted(expected_sources),
        "retrieved_sources": sorted(actual_sources),
        "retrieval_hit": retrieval_hit,
        "citation_present": citation_present,
        "expected_refusal": expected_refusal,
        "refused": refused,
        "refusal_correct": refusal_correct,
        "access_control_correct": access_correct,
        "latency_ms": latency_ms,
        "error": "",
    }


def percentage(values: list[bool | None]) -> float | None:
    valid = [value for value in values if value is not None]
    return round(100 * sum(valid) / len(valid), 2) if valid else None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [row for row in rows if not row["error"]]
    latencies = [row["latency_ms"] for row in successful]
    return {
        "total_cases": len(rows),
        "successful_requests": len(successful),
        "retrieval_hit_rate_pct": percentage([r["retrieval_hit"] for r in successful]),
        "citation_coverage_pct": percentage([r["citation_present"] for r in successful]),
        "refusal_accuracy_pct": percentage([r["refusal_correct"] for r in successful]),
        "access_control_accuracy_pct": percentage([r["access_control_correct"] for r in successful]),
        "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
    }


def write_reports(output: Path, rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.json").write_text(
        json.dumps({"summary": summary, "cases": rows}, indent=2), encoding="utf-8"
    )
    columns = [
        "id", "category", "retrieval_mode", "retrieval_hit",
        "citation_present", "refusal_correct", "access_control_correct",
        "latency_ms", "error",
    ]
    with (output / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in columns} for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a UNI-RAG HTTP endpoint")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--retrieval-mode", choices=("similarity", "mmr"), default="mmr")
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--answer-field", default="answer")
    parser.add_argument("--citations-field", default="citations")
    parser.add_argument("--sources-field", default="sources")
    parser.add_argument("--refused-field", default="refused")
    args = parser.parse_args()

    rows = []
    for case in read_jsonl(args.dataset):
        payload = {
            "question": case["question"],
            "user_role": case.get("user_role", "student"),
            "retrieval_mode": args.retrieval_mode,
        }
        try:
            response, latency = post_json(args.endpoint, payload, args.timeout)
            rows.append(evaluate_case(case, response, latency, args))
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            rows.append({
                "id": case["id"], "category": case["category"],
                "retrieval_mode": args.retrieval_mode, "retrieval_hit": None,
                "citation_present": None, "refusal_correct": None,
                "access_control_correct": None, "latency_ms": None, "error": str(exc),
            })

    summary = summarize(rows)
    write_reports(args.output, rows, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
