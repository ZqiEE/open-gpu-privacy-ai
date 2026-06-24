from __future__ import annotations

import argparse

import httpx


BOOTSTRAP_BASE_MODEL = "ailovanta-bootstrap:local"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local training job demo flow")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    api = args.api_url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        training_job = client.post(
            f"{api}/training/jobs",
            json={
                "kind": "rag_import",
                "name": "demo-rag-import",
                "dataset_uri": "file://local/demo-docs",
                "base_model": BOOTSTRAP_BASE_MODEL,
                "max_steps": 100,
                "notes": "demo training flow; public/core bridge not attached yet",
            },
        )
        training_job.raise_for_status()
        job = training_job.json()["job"]
        print("training_job:", job)

        model = client.post(
            f"{api}/models/versions",
            json={
                "name": "demo-ailovanta-model",
                "base_model": BOOTSTRAP_BASE_MODEL,
                "source_job_id": job["id"],
                "notes": "model version metadata created from demo flow",
            },
        )
        model.raise_for_status()
        print("model_version:", model.json())

        models = client.get(f"{api}/models/versions")
        models.raise_for_status()
        print("models:", models.json())


if __name__ == "__main__":
    main()
