from __future__ import annotations

import argparse
import json

import httpx


def parse_metric(values: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for value in values:
        key, raw = value.split("=", 1)
        result[key] = float(raw)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Record live model metrics and run rollback check")
    parser.add_argument("model")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--metric", action="append", default=[])
    parser.add_argument("--baseline", action="append", default=[])
    parser.add_argument("--max-drop", type=float, default=0.05)
    args = parser.parse_args()
    metrics = parse_metric(args.metric)
    baseline = parse_metric(args.baseline)
    with httpx.Client(timeout=120) as client:
        metric_response = client.post(args.api_url.rstrip("/") + "/model-monitor/metrics", json={"model": args.model, "metrics": metrics, "mode": "live"})
        metric_response.raise_for_status()
        check_response = client.post(args.api_url.rstrip("/") + "/model-monitor/rollback-check", json={"live_model": args.model, "baseline_metrics": baseline, "max_drop": args.max_drop})
        check_response.raise_for_status()
    print(json.dumps({"metric": metric_response.json(), "check": check_response.json()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
