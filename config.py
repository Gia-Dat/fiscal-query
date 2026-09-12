import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    CIKS = {
        "Shopify": "0001594805",
    }
