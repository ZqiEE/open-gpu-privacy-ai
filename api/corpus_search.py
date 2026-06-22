from __future__ import annotations


class CorpusSearch:
    def __init__(self, document_store) -> None:
        self.document_store = document_store

    def search(self, query: str, limit: int = 10) -> dict:
        query_terms = [term.lower() for term in query.split() if term.strip()]
        results = []
        for doc in self.document_store.list_documents(limit=500):
            if not doc.get("allowed_for_search"):
                continue
            haystack = f"{doc.get('title', '')} {doc.get('text', '')} {' '.join(doc.get('tags', []))}".lower()
            score = sum(1 for term in query_terms if term in haystack)
            if score:
                results.append({
                    "doc_id": doc["doc_id"],
                    "url": doc["url"],
                    "title": doc["title"],
                    "score": score,
                    "quality_score": doc["quality_score"],
                    "tags": doc["tags"],
                    "snippet": doc["text"][:300],
                })
        results.sort(key=lambda item: (item["score"], item["quality_score"]), reverse=True)
        return {"query": query, "results": results[:limit]}
