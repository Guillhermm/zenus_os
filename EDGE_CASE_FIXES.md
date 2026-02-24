# Edge Case Fixes - 2026-02-24

## Issues Fixed

This update addresses critical edge cases that were preventing Zenus from reliably executing various types of commands.

### 1. Real-Time Output Streaming ✅

**Problem:**
- Commands used `subprocess.run()` with `capture_output=True`
- No real-time feedback during long operations
- Timeouts causing "Streaming is strongly recommended..." errors
- Users couldn't see progress for package installs, updates, etc.

**Solution:**
- Created `shell_executor.py` with `StreamingExecutor` class
- Real-time line-by-line output streaming via `subprocess.Popen()`
- Progress visible immediately
- No more fixed timeouts (configurable, defaults to None)

**Impact:**
- Package installs/removes/updates now show live output
- Long-running operations won't timeout
- Better user experience with progress visibility

### 2. Empty Observations Fixed ✅

**Problem:**
- Commands returning `None` or empty strings created useless observations
- Iterative mode would show "observations completely empty"
- LLM couldn't reflect properly without meaningful observations
- LaTeX generation and other multi-step tasks would fail

**Solution:**
- Enhanced observation collection in `orchestrator.py`
- Graceful handling of empty/None results
- Context-aware observation formatting:
  - Empty results → `"(command executed, no visible output)"`
  - Short results → `"(output: X)"`
  - Long results → Truncated to 300 chars with `...`
- Include args in observations for better context
- Filter invalid observations in `goal_tracker.py`
- Special handling when all observations are empty

**Impact:**
- LaTeX iterations work reliably
- Multi-step execution provides meaningful feedback
- LLM can properly evaluate goal achievement

### 3. Large File Handling ✅

**Problem:**
- `write_file` would fail or timeout on large content
- No chunking for big files
- Memory issues with >10MB strings

**Solution:**
- Updated `FileOps.write_file()` with chunked writing
- 10MB chunk size for large files
- File size reporting in output
- Better error messages

**Impact:**
- Can now write large LaTeX documents (30,000+ words)
- Better memory efficiency
- Clear feedback on file sizes

### 4. System Resource Commands ✅

**Problem:**
- Commands like "check system resources" or "fix low disk space" would fail
- No comprehensive resource checking
- No way to find large files consuming disk space

**Solution:**
- Added `SystemOps.check_resource_usage()` - comprehensive CPU/memory/disk status
- Added `SystemOps.find_large_files()` - locate space hogs
- Warnings when resources are critically low:
  - Memory >80%
  - Disk >85%
  - CPU >90%

**Impact:**
- "check my system resources" works perfectly
- "system running low on disk" gets actionable response
- Can find and clean up large files

### 5. Package Manager Timeout Removal ✅

**Problem:**
- Package operations had 300-second (5 minute) timeout
- Large package installs/updates would fail
- "uninstall Teams" or similar operations would timeout

**Solution:**
- Removed fixed timeouts from `PackageOps` methods
- Uses streaming executor with `timeout=None`
- Operations can run as long as needed
- Real-time output shows progress

**Impact:**
- Large package operations work reliably
- No more timeout errors
- Can see apt/dnf output in real-time

### 6. Better Error Context ✅

**Problem:**
- When commands failed, error messages were generic
- "Failed to understand command" with no details
- Hard to debug what went wrong

**Solution:**
- Enhanced error messages throughout execution chain
- `execute_shell_command()` provides detailed failure info
- Observations include command args for context
- Streaming shows stderr in yellow for visibility

**Impact:**
- Easier to debug command failures
- Clear indication of what went wrong
- Better LLM reflection with error details

## Files Changed

### New Files
- `packages/core/src/zenus_core/tools/shell_executor.py` - Streaming command executor

### Modified Files
- `packages/core/src/zenus_core/tools/package_ops.py` - Use streaming executor, remove timeouts
- `packages/core/src/zenus_core/tools/file_ops.py` - Chunked large file writing
- `packages/core/src/zenus_core/tools/system_ops.py` - Added find_large_files(), check_resource_usage()
- `packages/core/src/zenus_core/cli/orchestrator.py` - Better observation formatting
- `packages/core/src/zenus_core/brain/goal_tracker.py` - Handle empty observations gracefully
- `packages/core/src/zenus_core/brain/llm/anthropic_llm.py` - Updated system prompt
- `packages/core/src/zenus_core/brain/llm/ollama_llm.py` - Updated system prompt
- `packages/core/src/zenus_core/brain/llm/openai_llm.py` - Updated system prompt
- `packages/core/src/zenus_core/brain/llm/deepseek_llm.py` - Updated system prompt

## Testing Recommendations

### Test Cases That Should Now Work:

1. **Large LaTeX Generation:**
   ```bash
   zenus "generate a 30,000 word LaTeX document about quantum computing" --iterative
   ```

2. **System Resource Check:**
   ```bash
   zenus "check my system resources"
   zenus "my system is running low on disk, help fix that"
   ```

3. **Package Operations:**
   ```bash
   zenus "uninstall Teams"
   zenus "update all packages"
   zenus "install docker and configure it"
   ```

4. **Find Large Files:**
   ```bash
   zenus "find large files consuming disk space in my home directory"
   ```

5. **Multi-Step with Minimal Output:**
   ```bash
   zenus "create project structure with empty files"
   zenus "configure git repo with remote"
   ```

## Architecture Notes

### Streaming Pattern

The new streaming executor uses `subprocess.Popen()` with line-buffered output:

```python
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line buffered
)

for line in iter(process.stdout.readline, ''):
    console.print(line)  # Real-time output
    captured_lines.append(line)  # Capture for observations
```

Benefits:
- Real-time feedback
- No timeout needed
- Still captures full output for observations

### Observation Format

Observations now follow this pattern:

```
ToolName.action(arg1=val1, arg2=val2) → (formatted result)
```

Examples:
- `FileOps.write_file(path=report.tex, content=...) → File written: report.tex (450.2KB)`
- `PackageOps.remove(package=teams, confirm=True) → (command executed, no visible output)`
- `SystemOps.check_resource_usage() → CPU: 45% used (8 cores)...`

This provides context even when output is minimal.

## Migration Notes

No breaking changes. All improvements are backward-compatible.

To update:
```bash
cd ~/projects/zenus_os
git pull
./update.sh
```

## Future Improvements

Consider:
1. Progress bars for long operations
2. Async parallel execution for independent commands
3. Smart retry on transient failures
4. Better disk space cleanup suggestions
