# Anthropic Claude Integration

Added support for Anthropic's Claude models to Zenus OS.

## What Was Added

### 1. Core Package Changes

**New File**: `packages/core/src/zenus_core/brain/llm/anthropic_llm.py`
- Full Claude integration following the existing LLM provider pattern
- Support for structured JSON output via `translate_intent()`
- Support for reflection via `reflect_on_goal()` with streaming
- Support for vision via `analyze_image()`
- Uses Anthropic's Python SDK

**Updated**: `packages/core/src/zenus_core/brain/llm/factory.py`
- Added `anthropic` as a backend option
- Import and instantiate `AnthropicLLM` when `ZENUS_LLM=anthropic`

**Updated**: `packages/core/pyproject.toml`
- Added `anthropic = "^0.47.0"` dependency

### 2. Configuration Updates

**Updated**: `.env.example`
- Added Anthropic configuration section
- Default model: `claude-3-5-sonnet-20241022`
- Default max tokens: `4096`

### 3. Installation Script Updates

**Updated**: `install.sh`
- Added Claude as option 2 (after Ollama, before OpenAI)
- Interactive model selection during installation:
  1. claude-3-5-sonnet-20241022 (recommended)
  2. claude-3-5-haiku-20241022 (faster, cheaper)
  3. claude-3-opus-20240229 (most capable)

## Usage

### Configuration

Add to your `.env`:

```bash
ZENUS_LLM=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # optional, this is the default
ANTHROPIC_MAX_TOKENS=4096                    # optional, this is the default
```

### Get an API Key

1. Go to: https://console.anthropic.com/account/keys
2. Create a new API key
3. Add it to your `.env` file

### Fresh Installation

Run the installer and select option 2:

```bash
./install.sh
```

You'll be prompted to:
1. Choose LLM backend → Select **2** (Anthropic Claude)
2. Enter your Anthropic API key
3. Choose a Claude model (sonnet recommended)

### Existing Installation

Update your `.env` file:

```bash
# Change from:
ZENUS_LLM=ollama  # or openai, deepseek

# To:
ZENUS_LLM=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Then test:

```bash
zenus "list files in current directory"
```

## Supported Models

### claude-3-5-sonnet-20241022 (Recommended)
- **Best balance** of intelligence, speed, and cost
- Excellent at reasoning and code generation
- ~\$0.003 per command (estimate)
- Max context: 200k tokens

### claude-3-5-haiku-20241022
- **Fastest and cheapest** Claude model
- Still highly capable
- ~\$0.0008 per command (estimate)
- Max context: 200k tokens

### claude-3-opus-20240229
- **Most capable** Claude model
- Best for complex reasoning tasks
- ~\$0.015 per command (estimate)
- Max context: 200k tokens

## Features Supported

✅ **Intent Translation** - Convert natural language to IntentIR  
✅ **Goal Reflection** - Iterative mode with goal achievement evaluation  
✅ **Vision** - Image analysis with Claude's vision capabilities  
✅ **Streaming** - Real-time token streaming for reflection

## Testing

Verify the integration works:

```bash
# Test import
cd packages/core
poetry run python -c "from zenus_core.brain.llm.anthropic_llm import AnthropicLLM; print('✓ Import successful')"

# Test factory
poetry run python -c "
import os
os.environ['ZENUS_LLM'] = 'anthropic'
os.environ['ANTHROPIC_API_KEY'] = 'test'
from zenus_core.brain.llm.factory import get_llm
llm = get_llm()
print(f'✓ Factory created: {type(llm).__name__}')
"
```

## Implementation Details

### JSON Extraction

Claude sometimes returns JSON wrapped in markdown code blocks. The implementation includes a `extract_json()` helper that:
1. Finds the first `{` and last `}`
2. Extracts the JSON substring
3. Validates and parses it

### Streaming

The reflection method supports streaming via Anthropic's `messages.stream()` API:
- Integrates with Zenus's existing stream handler
- Provides real-time feedback during iterative mode
- Falls back to non-streaming if not requested

### Error Handling

- Validates API key presence on initialization
- Provides clear error messages if API key is missing
- Handles JSON parsing errors gracefully
- Reports vision analysis failures

## Architecture

```
zenus_os/
├── packages/core/
│   ├── pyproject.toml                 # anthropic ^0.47.0
│   └── src/zenus_core/brain/llm/
│       ├── anthropic_llm.py          # NEW: Claude integration
│       ├── factory.py                # UPDATED: Added anthropic option
│       ├── base.py                   # LLM interface
│       ├── openai_llm.py             # OpenAI implementation
│       ├── deepseek_llm.py           # DeepSeek implementation
│       └── ollama_llm.py             # Ollama implementation
├── .env.example                      # UPDATED: Anthropic config
└── install.sh                        # UPDATED: Claude install option
```

## Why Claude?

- **Excellent reasoning**: Superior performance on complex tasks
- **Long context**: 200k token context window
- **Vision capabilities**: Strong multimodal support
- **Safety**: Built-in Constitutional AI
- **Privacy**: Anthropic doesn't train on API data by default

## Cost Comparison (Estimated per Command)

- **Ollama**: FREE (local)
- **DeepSeek**: ~\$0.0001-0.0003
- **OpenAI GPT-4o-mini**: ~\$0.001
- **Claude Haiku**: ~\$0.0008
- **Claude Sonnet**: ~\$0.003
- **Claude Opus**: ~\$0.015

*Costs are estimates based on typical command complexity*

## Next Steps

Consider adding:
- [ ] Prompt caching support (for repeated system prompts)
- [ ] Extended thinking mode (Claude's chain-of-thought)
- [ ] Custom model parameters (temperature, top_p, etc.)
- [ ] Cost tracking and usage reporting

## Commit

All changes committed in: `53e82e3`

```bash
git show 53e82e3
```
