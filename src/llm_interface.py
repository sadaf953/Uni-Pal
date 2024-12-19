from src.config import settings
from langchain.schema import HumanMessage
import logging
try:
    from langchain_groq import ChatGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    logging.warning("ChatGroq not available. Please update Langchain or use Groq")


def get_llm():
    """
    Initializes and returns the specified LLM.
    """
    try:
        if not HAS_GROQ:
           logging.error("ChatGroq is not available. Please update Langchain or use Groq")
           return None
        if settings.LLM_PROVIDER == "groq":
            if settings.GROQ_API_KEY is None:
                logging.error("GROQ_API_KEY not found in environment variables")
                return None
            return ChatGroq(api_key=settings.GROQ_API_KEY, model=settings.LLM_MODEL)
        else:
            logging.error(f"LLM Provider {settings.LLM_PROVIDER} not supported")
            return None
    except Exception as e:
        logging.error(f"Error initializing LLM: {e}")
        return None


def create_prompt(prompt: str) -> HumanMessage:
    """
    Creates a HumanMessage object from a prompt string.
    """
    return HumanMessage(content=prompt)


def query_llm(prompt: str) -> str:
    """
    Queries the LLM with the given prompt and returns the response.
    """
    llm = get_llm()
    if llm is None:
        return "Error: LLM not initialized."
    try:
        message = create_prompt(prompt)
        result = llm.invoke([message])
        return result.content
    except Exception as e:
        logging.error(f"Error querying LLM: {e}")
        return f"Error: LLM query failed: {e}"