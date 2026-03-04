#!/usr/bin/env python3
"""Test that AnthropicLLM loads the correct model from config.yaml"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load .env
load_dotenv(find_dotenv(usecwd=True))

# Add to path
sys.path.insert(0, 'packages/core/src')

print("Testing AnthropicLLM model loading...")
print()

# Check config.yaml
import yaml
config_path = Path.cwd() / "config.yaml"
if config_path.exists():
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        expected_model = config['llm']['model']
        print(f"✓ config.yaml exists")
        print(f"  Expected model: {expected_model}")
else:
    print("❌ config.yaml not found!")
    sys.exit(1)

print()

# Try to instantiate AnthropicLLM
try:
    from zenus_core.brain.llm.anthropic_llm import AnthropicLLM
    
    llm = AnthropicLLM()
    
    print(f"✓ AnthropicLLM instantiated")
    print(f"  Actual model: {llm.model}")
    print(f"  Max tokens: {llm.max_tokens}")
    print()
    
    if llm.model == expected_model:
        print(f"✅ SUCCESS! Model matches config.yaml: {llm.model}")
    else:
        print(f"❌ FAILED! Model mismatch:")
        print(f"   Expected: {expected_model}")
        print(f"   Got: {llm.model}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Failed to instantiate AnthropicLLM: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
