"""
LLM Factory

Creates LLM instances based on configuration.
Priority: config.yaml > environment variables (backwards compat)
"""

from dotenv import load_dotenv, find_dotenv # type: ignore
import os
from typing import Optional
from zenus_core.brain.llm.openai_llm import OpenAILLM
from zenus_core.brain.llm.deepseek_llm import DeepSeekLLM
from zenus_core.brain.llm.anthropic_llm import AnthropicLLM
from zenus_core.brain.llm.ollama_llm import OllamaLLM
from zenus_core.config.loader import get_config

# Load secrets from multiple locations (first match wins via override=False):
# 1. ~/.zenus/.env  — user-level secrets (system-wide install)
# 2. find_dotenv()  — project .env when running from source
from pathlib import Path as _Path
_user_env = _Path.home() / ".zenus" / ".env"
if _user_env.exists():
    load_dotenv(_user_env)
load_dotenv(find_dotenv(usecwd=True))

# Maps provider name → required env var
_PROVIDER_KEY_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai":    "OPENAI_API_KEY",
    "deepseek":  "DEEPSEEK_API_KEY",
    "ollama":    None,  # No API key needed
}

_SETUP_HINTS = {
    "anthropic": "export ANTHROPIC_API_KEY=sk-ant-...\nor add it to .env",
    "openai":    "export OPENAI_API_KEY=sk-...\nor add it to .env",
    "deepseek":  "export DEEPSEEK_API_KEY=sk-...\nor add it to .env",
    "ollama":    "Start Ollama: ollama serve\nThen pull a model: ollama pull llama3.1:8b",
}


def _check_provider_credentials(backend: str) -> None:
    """Raise a clear, actionable error if the provider's credentials are missing."""
    required_key = _PROVIDER_KEY_MAP.get(backend)
    if required_key and not os.getenv(required_key):
        hint = _SETUP_HINTS.get(backend, "")
        raise EnvironmentError(
            f"\n"
            f"  Provider '{backend}' is configured but {required_key} is not set.\n"
            f"\n"
            f"  Fix:\n"
            f"    {hint}\n"
            f"\n"
            f"  To switch provider: zenus model set <anthropic|openai|deepseek|ollama>\n"
            f"  To list options:    zenus model list\n"
        )


def get_llm(force_provider: Optional[str] = None):
    """
    Get LLM instance based on configuration.

    Priority:
    1. force_provider argument (per-command override)
    2. config.yaml llm.provider setting
    3. ZENUS_LLM environment variable (backwards compatibility)

    Args:
        force_provider: Override provider for this call only.

    Returns:
        LLM instance

    Raises:
        EnvironmentError: If the selected provider's credentials are missing.
        ValueError: If an unknown provider name is given.
    """
    backend = None
    model = None

    try:
        config = get_config()
        backend = config.llm.provider
        model = config.llm.model
    except Exception:
        pass  # Fall through to env-var fallback

    # Per-command override (highest priority)
    if force_provider:
        backend = force_provider

    # Last-resort fallback — only if config AND env are both absent
    if not backend:
        backend = os.getenv("ZENUS_LLM")

    if not backend:
        raise EnvironmentError(
            "\n"
            "  No LLM provider configured.\n"
            "  Run the setup wizard:  ./install.sh\n"
            "  Or set manually:       zenus model set anthropic\n"
        )

    # Validate credentials before attempting to instantiate the backend
    _check_provider_credentials(backend)

    if backend == "deepseek":
        return DeepSeekLLM()
    elif backend == "anthropic":
        return AnthropicLLM()
    elif backend == "ollama":
        ollama_model = model if model else os.getenv("OLLAMA_MODEL", "phi3:mini")
        return OllamaLLM(model=ollama_model)
    elif backend == "openai":
        return OpenAILLM()
    else:
        raise ValueError(
            f"\n"
            f"  Unknown provider '{backend}'.\n"
            f"  Valid options: anthropic, openai, deepseek, ollama\n"
            f"  Fix: zenus model set anthropic\n"
        )


def get_available_providers() -> list[str]:
    """
    Detect which LLM providers are configured and available
    
    Checks for:
    - API keys in environment
    - config.yaml settings
    - Ollama service availability
    
    Returns:
        List of available provider names (e.g., ['anthropic', 'deepseek'])
    """
    available = []
    
    # Check Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        available.append("anthropic")
    
    # Check DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        available.append("deepseek")
    
    # Check OpenAI
    if os.getenv("OPENAI_API_KEY"):
        available.append("openai")
    
    # Check Ollama (try to connect)
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            available.append("ollama")
    except Exception:
        pass
    
    # If nothing is available, default to anthropic
    # (will fail later with better error message)
    if not available:
        available.append("anthropic")
    
    return available
