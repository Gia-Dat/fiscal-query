import hashlib
import os
import requests
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import Config
from extract_item import Extract


def crawl_file(company_name: str, form_type="10-K"):
    os.makedirs("data", exist_ok=True)
    raw_file_path = f"data/{company_name.lower()}_raw.html"

    if os.path.exists(raw_file_path):
        return raw_file_path

    cik = Config.CIKS.get(company_name)
    headers = {"User-Agent": Config.SEC_USER_AGENT}

    # Fetch company submissions metadata
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    recent_filings = response.json()["filings"]["recent"]
    idx = recent_filings["form"].index(form_type)
    accession_number = recent_filings["accessionNumber"][idx].replace("-", "")
    primary_doc = recent_filings["primaryDocument"][idx]

    # Fetch primary document content
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_doc}"
    doc_response = requests.get(doc_url, headers=headers)
    doc_response.raise_for_status()

    with open(raw_file_path, "w", encoding="utf-8") as f:
        f.write(doc_response.text)

    return raw_file_path


def load_sec_data(company_name: str):
    raw_path = crawl_file(company_name)
    extractor = Extract(raw_path)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    # Target key 10-K sections
    sections = [
        {"section": "Item 1 - Business",
            "content": extractor.extract_item_content("Item 1", "Item 1B")},
        {"section": "Item 7 - MD&A",
            "content": extractor.extract_item_content("Item 7", "Item 8")},
        {"section": "Item 8 - Financial Statements",
            "content": extractor.extract_item_content("Item 8", "Item 9")},
    ]

    documents = []

    for item in sections:
        content = item["content"] or ""
        chunks = text_splitter.split_text(content)

        for idx, chunk in enumerate(chunks):
            # Deterministic unique ID for traceability
            doc_id = hashlib.md5(
                f"{company_name}_{item['section']}_{idx}".encode()).hexdigest()[:10]

            documents.append({
                "id": doc_id,
                "text": chunk,
                "section": item["section"],
                "company": company_name
            })

    return documents


def build_vector_store(documents: list[dict], collection_name="sec_filings", persist_dir="./chroma_db"):
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(name=collection_name)

    if not documents:
        return collection

    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [
        {"section": doc["section"], "company": doc["company"]}
        for doc in documents
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas
    )

    print(f"Indexed {len(documents)} chunks to ChromaDB at '{persist_dir}'.")
    return collection


# def main():
#     company = "Shopify"
#     print(f"Starting ingestion pipeline for {company}...")
#     documents = load_sec_data(company)
#     print(f"Generated {len(documents)} document chunks.")
#     build_vector_store(documents)


# if __name__ == "__main__":
#     main()
