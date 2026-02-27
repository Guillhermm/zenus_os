"""
Secrets Management

Secure handling of API keys and sensitive data.
Separates secrets from configuration files.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv


class SecretsManager:
    """
    Manage secrets securely
    
    Features:
    - Load from .env files
    - Environment variable override
    - Never log secrets
    - Validate required secrets
    """
    
    def __init__(self, env_file: Optional[Path] = None):
        self.env_file = env_file or self._find_env_file()
        self._secrets: Dict[str, str] = {}
        
        # Load secrets
        self._load_secrets()
    
    def _find_env_file(self) -> Optional[Path]:
        """Find .env file in standard locations"""
        search_paths = [
            Path.cwd() / ".env",
            Path.cwd() / ".env.local",
            Path.home() / ".zenus" / ".env",
        ]
        
        for path in search_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_secrets(self):
        """Load secrets from .env file and environment"""
        # Load from .env file if exists
        if self.env_file and self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Load common secrets from environment
        secret_keys = [
            # Anthropic
            "ANTHROPIC_API_KEY",
            
            # OpenAI
            "OPENAI_API_KEY",
            "OPENAI_API_BASE_URL",
            
            # DeepSeek
            "DEEPSEEK_API_KEY",
            "DEEPSEEK_API_BASE_URL",
            
            # Ollama
            "OLLAMA_BASE_URL",
            "OLLAMA_MODEL",
            
            # Database (if needed)
            "DATABASE_URL",
            "REDIS_URL",
            
            # Custom
            "ZENUS_API_KEY",
        ]
        
        for key in secret_keys:
            value = os.getenv(key)
            if value:
                self._secrets[key] = value
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value
        
        Args:
            key: Secret key
            default: Default value if not found
        
        Returns:
            Secret value or default
        """
        return self._secrets.get(key, default)
    
    def get_llm_api_key(self, provider: str) -> Optional[str]:
        """
        Get LLM API key for provider
        
        Args:
            provider: LLM provider (anthropic, openai, deepseek, etc.)
        
        Returns:
            API key if found
        """
        key_mapping = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        
        key_name = key_mapping.get(provider.lower())
        if not key_name:
            return None
        
        return self.get(key_name)
    
    def has_secret(self, key: str) -> bool:
        """Check if secret exists"""
        return key in self._secrets
    
    def validate_required(self, *keys: str) -> bool:
        """
        Validate that required secrets exist
        
        Args:
            *keys: Required secret keys
        
        Returns:
            True if all exist, False otherwise
        """
        missing = [key for key in keys if not self.has_secret(key)]
        
        if missing:
            print(f"❌ Missing required secrets: {', '.join(missing)}")
            return False
        
        return True
    
    def list_available(self) -> list:
        """List available secret keys (not values!)"""
        return list(self._secrets.keys())
    
    def mask_secret(self, value: str) -> str:
        """
        Mask secret for logging
        
        Args:
            value: Secret value
        
        Returns:
            Masked value (e.g., "sk-ant-***")
        """
        if not value or len(value) < 8:
            return "***"
        
        return f"{value[:6]}***{value[-3:]}"


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets(reload: bool = False) -> SecretsManager:
    """
    Get global secrets manager
    
    Args:
        reload: Force reload from file
    
    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    
    if _secrets_manager is None or reload:
        _secrets_manager = SecretsManager()
    
    return _secrets_manager
