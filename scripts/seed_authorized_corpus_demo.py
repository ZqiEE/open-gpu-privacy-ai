from __future__ import annotations

import json

from api.corpus_pipeline import CorpusPipeline
from api.corpus_search import CorpusSearch
from api.source_registry import SourceRegistry
from api.training_candidate_store import TrainingCandidateStore
from api.web_document_store import WebDocumentStore


DOCS = [
    {"url": "local://ai-compute", "title": "Private AI compute network", "text": "Private AI compute network with local GPU nodes scheduler intelligence worker safety and model evaluation."},
    {"url": "local://corpus-engine", "title": "Authorized corpus engine", "text": "Authorized corpus engine records source permission document hash quality score tags and training candidate status."},
    {"url": "local://model-training", "title": "Model training lifecycle", "text": "Model lifecycle includes corpus search RAG candidates evaluation sets model registry and usage metering."},
]


def main() -> None:
    sources = SourceRegistry()
    documents = WebDocumentStore()
    pipeline = CorpusPipeline()
    candidates = TrainingCandidateStore()

    source = sources.add_source({"source_id": "src_authorized_demo", "name": "Authorized Demo Source", "source_type": "local", "base_url": "local://authorized-demo", "permission_scope": "authorized demo", "allowed_for_search": True, "allowed_for_training": True, "allowed_for_finetune": True, "allowed_for_eval": True})
    print("source:", json.dumps(source, ensure_ascii=False, indent=2))

    for item in DOCS:
        processed = pipeline.process(item["url"], item["title"], item["text"])
        saved = documents.add_document(source, processed)
        print("document:", json.dumps(saved, ensure_ascii=False, indent=2))

    search = CorpusSearch(documents)
    print("search:", json.dumps(search.search("model training corpus", limit=5), ensure_ascii=False, indent=2))
    print("promote:", json.dumps(candidates.promote_from_documents(documents, min_quality=0.2, candidate_type="rag"), ensure_ascii=False, indent=2))
    print("candidate_summary:", json.dumps(candidates.summary(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
