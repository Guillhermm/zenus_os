# Streaming Reflection Fix - StreamHandler Interface Issue

## The Problem

After fixing the main streaming issue for `translate_intent`, users encountered a new error during iterative execution:

```
could not determine goal status: 'StreamHandler' object has no attribute 'start_section'
```

This error appeared in the reflection phase (goal achievement evaluation) but didn't prevent the task from completing successfully. However, it indicated a potential issue that could cause problems in future iterations.

## Root Cause

### What Was Happening

In `anthropic_llm.py`, the `reflect_on_goal` method tried to use the `StreamHandler` with methods that don't exist:

```python
# WRONG - these methods don't exist on StreamHandler
handler.start_section("Reflecting: ")
for text in stream.text_stream:
    handler.handle_token(text)
    full_text += text
handler.end_section()
```

### Why This Happened

The `StreamHandler` class was designed for OpenAI's streaming format and only has one main method:

```python
def stream_llm_tokens(self, stream_iterator, prefix: str = ""):
    """Expects OpenAI format with .choices[0].delta.content"""
```

This method expects:
- Iterator with `.choices` attribute
- Each chunk has `.choices[0].delta.content`

**Anthropic's streaming format is different:**
- Iterator yields text chunks directly via `.text_stream`
- No `.choices` structure
- Different chunk format

## The Solution

### Manual Token Handling for Anthropic

Since `StreamHandler` doesn't support Anthropic's format, the fix manually handles streaming output:

```python
def reflect_on_goal(self, reflection_prompt: str, user_goal: str, 
                    observations: list, stream: bool = False) -> str:
    if stream:
        # Manually handle Anthropic streaming (format differs from OpenAI)
        from rich.console import Console
        import sys
        
        console = Console()
        console.print("[cyan]Reflecting: [/cyan]", end="")
        sys.stdout.flush()
        
        full_text = ""
        try:
            with self.client.messages.stream(...) as stream:
                for text in stream.text_stream:
                    console.print(text, end="")
                    sys.stdout.flush()
                    full_text += text
            
            console.print()  # New line
        except Exception as e:
            console.print(f"\n[yellow]Reflection streaming error: {str(e)}[/yellow]")
            # Fallback to non-streaming
            return self.reflect_on_goal(reflection_prompt, user_goal, 
                                       observations, stream=False)
        
        return full_text
```

### Key Changes

1. **Direct console output** instead of StreamHandler
   - Uses `rich.Console` directly
   - No dependency on StreamHandler's non-existent methods

2. **Proper error handling**
   - Catches streaming errors
   - Falls back to non-streaming mode
   - User-friendly error message

3. **Correct Anthropic format**
   - Uses `stream.text_stream` (Anthropic's iterator)
   - No `.choices` assumptions

4. **Visual feedback maintained**
   - Still shows "Reflecting: " prefix
   - Still streams tokens in real-time
   - Still adds newline after completion

## Why Not Fix StreamHandler?

### Option A: Make StreamHandler support both formats (Rejected)

**Pros:**
- One unified interface
- Cleaner code in LLM providers

**Cons:**
- Complex: Need to detect format dynamically
- Fragile: What about future providers with different formats?
- Overhead: Format detection on every chunk

### Option B: Provider-specific streaming (Current approach)

**Pros:**
- Simple and explicit
- Each provider handles its own format
- Easy to understand and debug
- No performance overhead

**Cons:**
- Slight code duplication (but minimal)
- Manual console handling in each provider

**Decision:** Option B is better for maintainability and clarity.

## Other LLM Providers

### OpenAI
- Uses `StreamHandler.stream_llm_tokens` ✓
- Works because format matches what StreamHandler expects

### DeepSeek
- Uses `StreamHandler.stream_llm_tokens` ✓
- OpenAI-compatible API, same format

### Ollama
- Doesn't use streaming for reflection currently
- Could be updated with provider-specific handling if needed

### Anthropic (Fixed)
- Now uses manual console output ✓
- Correctly handles Anthropic's streaming format

## Testing

### Before Fix
```bash
zenus --iterative "write a large document"
# ✓ Task completes successfully
# ❌ Error message: 'StreamHandler' object has no attribute 'start_section'
# Reflection shows: could not determine goal status
```

### After Fix
```bash
zenus --iterative "write a large document"
# ✓ Task completes successfully
# ✓ Reflection streams correctly
# ✓ No error messages
# ✓ Goal status determined properly
```

## Files Changed

1. **packages/core/src/zenus_core/brain/llm/anthropic_llm.py**
   - Updated `reflect_on_goal` method
   - Removed `StreamHandler` usage
   - Added manual streaming with proper error handling
   - Added fallback to non-streaming on errors

## Future Improvements

### Option 1: Abstract Streaming Interface

Create a provider-agnostic streaming interface:

```python
class StreamingProvider(ABC):
    @abstractmethod
    def stream_tokens(self, iterator) -> str:
        """Provider-specific streaming implementation"""
        pass
```

Each LLM provider implements its own streaming format.

### Option 2: Streaming Adapters

Create adapters that convert different formats to a common interface:

```python
class AnthropicStreamAdapter:
    def __init__(self, anthropic_stream):
        self.stream = anthropic_stream
    
    def __iter__(self):
        for text in self.stream.text_stream:
            yield MockChunk(text)  # Convert to OpenAI-like format
```

### Current Status: YAGNI

For now, manual handling in each provider is simple and works well. We can refactor later if we add many more providers and the duplication becomes significant.

## Error Handling

The new implementation includes defensive error handling:

1. **Try-catch around streaming**
   - Catches any unexpected streaming errors
   - Shows user-friendly error message

2. **Automatic fallback**
   - If streaming fails, falls back to non-streaming
   - Ensures reflection always completes
   - User still gets result even if streaming breaks

3. **Graceful degradation**
   - Streaming is an enhancement, not a requirement
   - Non-streaming is always available as backup

## Performance Impact

No performance impact:
- Same amount of data transferred
- Same API calls
- Only difference: manual printing vs. StreamHandler printing

## Commit

Changes committed in: `[upcoming]`

View the diff:
```bash
git show [commit-hash]
```
