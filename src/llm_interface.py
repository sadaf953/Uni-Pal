from langchain.chat_models import ChatOllama
from src.config import settings
from langchain.schema import HumanMessage

def get_llm():
  return ChatOllama(model="llama2") # You might need to download it first with ollama pull llama2

def query_llm(prompt: str) -> str:
    llm = get_llm()
    result = llm.invoke([HumanMessage(content=prompt)])
    return result.content