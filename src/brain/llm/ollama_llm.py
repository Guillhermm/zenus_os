"""
Ollama LLM Backend

Local LLM support using Ollama.
Optimized for low-resource machines (4-16GB RAM).

Recommended models:
- phi3:mini (3.8GB) - Fast, efficient
- llama3.2:3b (2GB) - Lightweight
- qwen2.5:3b (2.3GB) - Good reasoning
"""

import json
import requests
from typing import Optional
from brain.llm.schemas import IntentIR


class OllamaLLM:
    """
    Ollama backend for local LLM execution
    
    Requires Ollama installed: https://ollama.ai/
    Install: curl -fsSL https://ollama.com/install.sh | sh
    """
    
    def __init__(
        self, 
        model: str = "phi3:mini",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                raise RuntimeError("Ollama is not responding")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Ollama not running. Start with: ollama serve\n"
                "Install from: https://ollama.com/download"
            )
    
    def translate_intent(self, user_input: str) -> IntentIR:
        """Translate user input to Intent IR using Ollama"""
        
        system_prompt = """You are an OS intent compiler. Convert user commands to structured JSON.

Available tools:
- FileOps: scan, mkdir, move, write_file, touch
- TextOps: read, write, append, search, count_lines, head, tail
- SystemOps: disk_usage, memory_info, cpu_info, list_processes, uptime
- ProcessOps: find_by_name, info, kill

Risk levels:
0 = read-only
1 = create/move
2 = overwrite
3 = delete (requires confirmation)

Output ONLY valid JSON matching this schema:
{
  "goal": "brief description",
  "requires_confirmation": true/false,
  "steps": [
    {
      "tool": "ToolName",
      "action": "action_name",
      "args": {"key": "value"},
      "risk": 0-3
    }
  ]
}

No markdown, no explanations, just JSON."""

        prompt = f"{system_prompt}\n\nUser: {user_input}\n\nJSON:"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Force JSON output
                    "options": {
                        "temperature": 0.1,      # More deterministic
                        "num_predict": 2048,     # Allow longer responses
                        "num_ctx": 8192,         # Larger context window
                        "top_k": 10,
                        "top_p": 0.9
                    }
                },
                timeout=300  # 5 minutes (was 30s)
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama error: {response.status_code}")
            
            result = response.json()
            content = result.get("response", "")
            
            # Extract JSON from response
            content = self._extract_json(content)
            
            # Parse and validate
            data = json.loads(content)
            return IntentIR.model_validate(data)
            
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama request timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON from Ollama: {content}")
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text"""
        # Remove markdown code blocks
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
        
        # Find JSON object boundaries
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start == -1 or end == 0:
            return text
        
        return text[start:end]
