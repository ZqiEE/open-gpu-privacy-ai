from __future__ import annotations

import json

from api.source_registry import SourceRegistry
from api.training_candidate_store import TrainingCandidateStore
from api.web_document_store import WebDocumentStore


def main() -> None:
    sources = SourceRegistry()
    documents = WebDocumentStore()
    candidates = TrainingCandidateStore()
    report = {
        "sources": len(sources.list_sources(limit=1000)),
        "documents": documents.summary(),
        "candidates": candidates.summary(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
