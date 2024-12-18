import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'unipal.db')}")
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")


settings = Settings()