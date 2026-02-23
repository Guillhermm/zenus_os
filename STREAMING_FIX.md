# Streaming Fix for Long-Running Claude Requests

## The Problem

When using Anthropic Claude with iterative mode for complex tasks (e.g., generating a 30,000-word TeX file), users encountered this error:

```
iteractive execution error: Streaming is strongly recommended for operations 
that may take longer than 10 minutes. See https://github.com/anthropics... 
for more details.
```

Even though the user had configured `ANTHROPIC_MAX_TOKENS=64000`, the request timed out.

## Root Cause

### Anthropic's Timeout Policy

Anthropic enforces timeouts on non-streaming API requests to prevent long-running connections. For operations that may take more than 10 minutes to complete, streaming is required.

### Our Implementation Issue

The `translate_intent` method in `anthropic_llm.py` accepted a `stream` parameter but didn't use it:

```python
def translate_intent(self, user_input: str, stream: bool = False) -> IntentIR:
    # stream parameter was ignored!
    response = self.client.messages.create(...)  # Always non-streaming
```

In `orchestrator.py`, iterative mode called `translate_intent` without streaming:

```python
intent = self.llm.translate_intent(enhanced_input)  # No stream=True!
```

## The Solution

### 1. Implement Streaming in `translate_intent`

Updated `anthropic_llm.py` to actually use the `stream` parameter:

```python
def translate_intent(self, user_input: str, stream: bool = False) -> IntentIR:
    if stream:
        # Use streaming to avoid timeouts
        full_text = ""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_input}]
        ) as stream:
            for text in stream.text_stream:
                full_text += text
        
        content = full_text
    else:
        # Non-streaming mode for quick requests
        response = self.client.messages.create(...)
        content = response.content[0].text
    
    # Parse JSON and return IntentIR
    data = extract_json(content)
    return IntentIR.model_validate(data)
```

**How it works:**
- When `stream=True`, uses Anthropic's streaming API
- Collects all text chunks into `full_text`
- Parses the complete JSON after streaming completes
- Returns structured `IntentIR` object as before

**Benefits:**
- ✓ No timeout errors on long responses
- ✓ Still returns structured output (IntentIR)
- ✓ Backward compatible (stream=False works as before)

### 2. Enable Streaming in Iterative Mode

Updated `orchestrator.py` to use streaming for iterative execution:

```python
# Step 1: Translate intent with accumulated context
# Use streaming to avoid timeouts on complex planning
if self.progress:
    with self.progress.thinking("Planning next steps"):
        intent = self.llm.translate_intent(enhanced_input, stream=True)
else:
    intent = self.llm.translate_intent(enhanced_input, stream=True)
```

**Why iterative mode needs streaming:**
- Iterative mode is used for complex, multi-step tasks
- Each iteration may generate large plans (many steps)
- Planning can take several minutes
- Streaming prevents timeout errors

## When Streaming Is Used

### ✓ Always Streaming (After Fix)
- **Iterative mode** (`--iterative` flag or auto-detected complex tasks)
  - Each iteration uses streaming for intent translation
  - Each reflection uses streaming (already implemented)

### ✗ Non-Streaming (Current)
- **Regular mode** (simple, direct commands)
  - Quick requests don't need streaming overhead
  - Can be updated in the future if needed

## Files Changed

1. **packages/core/src/zenus_core/brain/llm/anthropic_llm.py**
   - Implemented actual streaming in `translate_intent`
   - Streams text chunks, then parses complete JSON

2. **packages/core/src/zenus_core/cli/orchestrator.py**
   - Added `stream=True` to `translate_intent` calls in iterative mode

## Testing

### Before Fix
```bash
zenus --iterative "write a 30000 word academic paper on AI"
# ❌ Error: Streaming is strongly recommended...
```

### After Fix
```bash
zenus --iterative "write a 30000 word academic paper on AI"
# ✓ Works! Streams the plan generation, avoids timeout
```

## Other LLM Providers

### OpenAI
- Uses `.parse()` for structured output
- Streaming structured output is complex with OpenAI
- May need different implementation if timeouts occur

### DeepSeek
- Similar to OpenAI (uses OpenAI-compatible API)
- Currently non-streaming for structured output
- Can be updated if needed

### Ollama
- Local model, no timeout concerns
- Non-streaming is fine

## Technical Details

### Why Not Stream + Parse Simultaneously?

**Option A: Stream and parse incrementally**
- Hard: JSON might not be complete mid-stream
- Would need state machine to detect valid JSON chunks
- Complex and error-prone

**Option B: Stream all, then parse** (Current approach)
- Simple: Collect everything, then parse complete JSON
- Reliable: Standard JSON parsing on complete text
- Gets streaming benefits (no timeout) while keeping structured output

### Streaming Overhead

Streaming adds minimal overhead:
- Network: Same data transfer, just chunked
- CPU: Slightly more (chunk processing)
- Memory: Same (accumulating full text either way)

Trade-off is worth it to avoid timeout errors on complex tasks.

## Future Improvements

Potential enhancements:

1. **Visual feedback during streaming**
   - Show progress indicator while waiting for complete response
   - Could display token count as it streams

2. **Adaptive streaming**
   - Use heuristics to auto-detect when streaming is needed
   - Based on: user input length, task complexity, history

3. **Streaming for regular mode**
   - Enable for any task that might take >60 seconds
   - Low risk, small overhead

4. **Provider-specific optimizations**
   - OpenAI: Use streaming with manual JSON parsing
   - DeepSeek: Same approach as Anthropic

## Configuration

No new configuration needed! The fix works automatically with existing settings:

```bash
# .env configuration remains the same
ZENUS_LLM=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=64000  # Now actually usable for large outputs!
```

## Commit

Changes committed in: `[upcoming]`

View the diff:
```bash
git show [commit-hash]
```
