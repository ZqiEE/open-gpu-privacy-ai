from __future__ import annotations

import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run queue maintenance tasks")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--older-than-minutes", type=int, default=30)
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        retry = client.post(f"{api}/jobs/retry-failed", params={"max_attempts": args.max_attempts})
        retry.raise_for_status()
        print("retry_failed:", retry.json())

        requeue = client.post(f"{api}/jobs/requeue-stale", params={"older_than_minutes": args.older_than_minutes})
        requeue.raise_for_status()
        print("requeue_stale:", requeue.json())

        status = client.get(f"{api}/network/status")
        status.raise_for_status()
        print("status:", status.json())


if __name__ == "__main__":
    main()
