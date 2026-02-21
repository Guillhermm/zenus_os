from dotenv import load_dotenv # type: ignore

import os
from brain.llm.openai_llm import OpenAILLM
from brain.llm.deepseek_llm import DeepSeekLLM
from brain.llm.ollama_llm import OllamaLLM

load_dotenv()

def get_llm():
    backend = os.getenv("ZENUS_LLM", "openai")

    if backend == "deepseek":
        return DeepSeekLLM()
    elif backend == "ollama":
        model = os.getenv("OLLAMA_MODEL", "phi3:mini")
        return OllamaLLM(model=model)
    return OpenAILLM()
