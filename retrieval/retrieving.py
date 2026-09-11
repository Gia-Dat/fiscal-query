from typing import List, Dict, Any, Optional
from ingestion.embedding import VectorStore


def retrieving(query: str, company: Optional[str] = None, top_k: int = 12) -> List[Dict[str, Any]]:
    store = VectorStore()
    filter_dict = {"company": company} if company else None

    results = store.collection.query(
        query_texts=[query],
        n_results=top_k,
        where=filter_dict,
    )

    retrieved = []
    if results and results["documents"]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            retrieved.append({"content": doc, "metadata": meta})
    return retrieved
