import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Settings:
    """
    Configuration settings for the UniPal application.
    """

    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'unipal.db'))}")
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq") # set groq as default LLM, use 'ollama' for local ollama
    LLM_MODEL = os.getenv("LLM_MODEL", "mixtral-8x7b-32768") #set default model
    TRAVILY_API_KEY=os.getenv("TRAVILY_API_KEY")
    

    def __init__(self):
      logging.info(f"Loaded environment variables: {os.environ}")
      logging.info(f"GROQ_API_KEY is: {self.GROQ_API_KEY}")
      logging.info(f"LLM_PROVIDER is: {self.LLM_PROVIDER}")


settings = Settings()