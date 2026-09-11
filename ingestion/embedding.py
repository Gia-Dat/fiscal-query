from config import Config
from typing import List, Dict, Any
from tqdm.auto import tqdm

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    def __init__(self, collection_name: str = "sec_10k_filings"):
        self.client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        self.ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=Config.OPENAI_API_KEY,
            model_name=Config.EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )

    def embedding(self, chunks: List[Dict[str, Any]]):
        docs = [c["text"] for c in chunks]
        metas = [c["metadata"] for c in chunks]
        ids = [f"{c['metadata']['company']}_{c['metadata']['item']}_{i}" for i,
               c in enumerate(chunks)]

        batch_size = 150
        for i in tqdm(range(0, len(docs), batch_size)):
            self.collection.add(
                documents=docs[i:i+batch_size],
                metadatas=metas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
