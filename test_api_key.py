#!/usr/bin/env python3
"""Test Anthropic API key"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load .env from project directory
load_dotenv(find_dotenv(usecwd=True))

api_key = os.getenv("ANTHROPIC_API_KEY")

print("=" * 60)
print("Anthropic API Key Diagnostic")
print("=" * 60)
print()

if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in environment")
    print()
    print("Check:")
    print("  1. .env file exists in project directory")
    print("  2. Contains: ANTHROPIC_API_KEY=sk-ant-...")
    exit(1)

# Show key info (masked)
print(f"✓ API Key found")
print(f"  Length: {len(api_key)} characters")
print(f"  Preview: {api_key[:10]}...{api_key[-4:]}")
print(f"  Starts with: {api_key[:7]}")

# Check for common issues
issues = []

if api_key != api_key.strip():
    issues.append("Contains leading/trailing whitespace")

if api_key.startswith('"') or api_key.startswith("'"):
    issues.append("Wrapped in quotes (should be: ANTHROPIC_API_KEY=sk-ant-..., not ANTHROPIC_API_KEY=\"sk-ant-...\")")

if not api_key.startswith("sk-ant-"):
    issues.append(f"Doesn't start with 'sk-ant-' (starts with '{api_key[:10]}')")

if len(api_key) < 20:
    issues.append(f"Too short ({len(api_key)} chars, should be ~100+)")

if issues:
    print()
    print("⚠️  Potential issues:")
    for issue in issues:
        print(f"  • {issue}")
else:
    print("  No obvious formatting issues")

print()
print("Testing API connection...")
print()

try:
    from anthropic import Anthropic
    
    # Clean the key
    clean_key = api_key.strip()
    if (clean_key.startswith('"') and clean_key.endswith('"')) or \
       (clean_key.startswith("'") and clean_key.endswith("'")):
        clean_key = clean_key[1:-1]
        print("  ℹ️  Removed quotes from key")
    
    client = Anthropic(api_key=clean_key)
    
    # Try a simple API call
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    
    print("✅ SUCCESS! API key is valid")
    print(f"   Model: {response.model}")
    print(f"   Response: {response.content[0].text}")
    
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}")
    print(f"   {str(e)}")
    print()
    
    if "authentication" in str(e).lower() or "401" in str(e):
        print("This is an authentication error. Possible causes:")
        print("  1. API key is invalid or expired")
        print("  2. API key doesn't have correct permissions")
        print("  3. You're using an old/test key")
        print()
        print("To fix:")
        print("  1. Get a new API key from: https://console.anthropic.com/settings/keys")
        print("  2. Update .env file: ANTHROPIC_API_KEY=sk-ant-...")
        print("  3. Run this test again")
    
    elif "rate" in str(e).lower():
        print("Rate limit hit - your key works but you've made too many requests")
    
    else:
        print("Unexpected error - check your internet connection")

print()
print("=" * 60)
