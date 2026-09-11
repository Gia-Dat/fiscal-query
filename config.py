import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    LLM_MODEL = os.getenv("LLM_MODEL")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")

    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    CIKS = {
        "Shopify": "0001594805",
    }
