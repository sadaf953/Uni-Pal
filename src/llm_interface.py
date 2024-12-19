from src.config import settings
import datetime
import os
from dotenv import load_dotenv
from langchain.schema import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
import logging
try:
    from langchain_groq import ChatGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    logging.warning("ChatGroq not available. Please update Langchain or use Groq")



# Load environment variables from .env file
load_dotenv()


class LLMs:
    def __init__(self):
        # Model names
        self.sonnet = "claude-3-5-sonnet-20240620"
        self.haiku = "claude-3-haiku-20240307"
        self.new_sonnet = "max-tokens-3-5-sonnet-2024-07-15"
        self.mixtral8x7b = "mixtral-8x7b-32768"
        self.llama70b = "llama-3.3-70b-versatile"
        self.gemini_flash = "gemini-1.5-flash"
        self.gemini_pro = "gemini-1.5-pro"
        self.gemini_exp1206 = "gemini-exp-1206"
        self.gemini_2_flash = "gemini-2.0-flash-exp"


        # Initialize models with API keys
        self.mixtral8x7b = ChatGroq(
            model=self.mixtral8x7b,
            temperature=0.4,
            )# type: ignore

        self.gemini_flash = ChatGoogleGenerativeAI(
            model=self.gemini_flash,
            temperature=0.4,
        )
        self.gemini_pro = ChatGoogleGenerativeAI(
            model=self.gemini_pro,
            temperature=0.4,
        )
        self.gemini_exp1206 = ChatGoogleGenerativeAI(
            model=self.gemini_exp1206,
            temperature=0.1,
            max_retries=3,
            timeout=30,
            max_output_tokens=8048,
        )
        self.gemini_2_flash = ChatGoogleGenerativeAI(
            model=self.gemini_2_flash,
            temperature=0.1,
        )
        self.llama70b = ChatGroq(
            model=self.llama70b,
            temperature=0.4,
        )# type: ignore

model = LLMs()
Mixtral8x7b = model.mixtral8x7b
Llama70b = model.llama70b
Gemini_Flash = model.gemini_flash
Gemini_Pro = model.gemini_pro
Gemini_Exp1206 = model.gemini_exp1206
Gemini_2_flash = model.gemini_2_flash
models = [Mixtral8x7b, Llama70b, Gemini_Flash, Gemini_Pro, Gemini_Exp1206, Gemini_2_flash]
model_names = ["mixtral8x7b", "llama70b", "gemini_flash", "gemini_pro", "gemini_exp-1206", "gemini_2_flash"]

def testing_llms():
    parser = StrOutputParser()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"llm_test_results_{timestamp}.md"
    
    with open(output_file, "w") as f:
        f.write(f"# LLM Testing Results - {timestamp}\n\n")
        for model in models:
            model_name = model_names[models.index(model)]
            f.write(f"## {model_name}\n\n")
            messages = [
                SystemMessage(content="Reply only in 30 words"),
                HumanMessage(content="explain a random topic from philosophy"),
            ]

            try:
                result = model.invoke(messages)
                output = parser.invoke(result)
                f.write(f"**Response:**\n\n{output}\n\n")

            except Exception as e:
                f.write(f"**Error:**\n\n```\n{str(e)}\n```\n\n")
    
    print(f"Results have been saved to {output_file}")



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