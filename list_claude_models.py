#!/usr/bin/env python3
"""List available Claude models"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ ANTHROPIC_API_KEY not set")
    exit(1)

# Clean key
api_key = api_key.strip()
if api_key.startswith('"') or api_key.startswith("'"):
    api_key = api_key[1:-1]

print("Checking available Claude models...")
print()

try:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    
    # Test the most common model names
    models_to_test = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-5-sonnet",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-sonnet-4",
        "claude-4-opus",
    ]
    
    print("Testing models...")
    for model in models_to_test:
        try:
            response = client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            print(f"✅ {model} - WORKS")
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not_found" in error_msg:
                print(f"❌ {model} - NOT FOUND")
            elif "401" in error_msg or "authentication" in error_msg.lower():
                print(f"⚠️  {model} - AUTH ERROR (check API key)")
            else:
                print(f"❌ {model} - ERROR: {error_msg[:50]}")
    
    print()
    print("Recommendation: Use the first model that shows ✅")
    
except Exception as e:
    print(f"❌ Failed: {e}")
