from dotenv import load_dotenv # type: ignore

import os
from brain.llm.openai_llm import OpenAILLM
from brain.llm.deepseek_llm import DeepSeekLLM

load_dotenv()

def get_llm():
    backend = os.getenv("ZENUS_LLM", "openai")

    if backend == "deepseek":
        return DeepSeekLLM()
    return OpenAILLM()
