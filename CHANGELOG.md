# Zenus OS Changelog

## [Unreleased] - 2026-02-10

### Added - Semantic Memory & Explain Mode
- **Semantic Search**: sentence-transformers integration for finding similar past commands
  - Embeddings cached in `~/.zenus/semantic_cache/`
  - Cosine similarity search with configurable threshold
  - Success rate tracking per command type
- **Explain Mode**: `--explain` flag shows reasoning before execution
  - Display similar past commands
  - Show success probability
  - Require confirmation before proceeding
  - Detailed step-by-step breakdown
- **Visual Improvements**: Rich library for beautiful CLI output
  - Color-coded output: green (success), red (error), yellow (warning), cyan (info)
  - Risk levels with emoji: 🟢 (read), 🔵 (create), 🟡 (modify), 🔴 (delete)
  - Formatted tables and panels
  - Syntax highlighting for code/JSON
  - Bold/italic/underline support
- **Readline Support**: Arrow keys for command history
  - History saved to `~/.zenus/history.txt`
  - 1000 commands stored
  - Persists across sessions

### Fixed
- **Ollama Timeout**: Increased from 30s to 300s (5 minutes)
- **Token Limits**: Increased from 512 to 2048 tokens for longer responses
- **Context Window**: Added 8192 token context window
- **Lazy Loading**: Fixed API key errors when using Ollama
- **Text Operations**: Fixed write() detection for new vs existing files
- **.env Parsing**: Fixed corruption issues in installer
- **Module Imports**: Moved OpenAI imports inside __init__ to prevent eager loading

### Changed
- All execution steps now print with formatted output
- Success/failure automatically tracked in semantic index
- Orchestrator integrated with new formatter and explain mode

## [0.1.0-alpha] - 2026-02-09

### Added - Foundation
- **CLI Routing**: help, version, shell, direct command modes
- **Intent IR Schema**: Formal contract between LLM and execution
- **LLM Backends**: OpenAI, DeepSeek, Ollama (local) support
- **Audit Logging**: JSONL logs to `~/.zenus/logs/`
- **Dry-run Mode**: `--dry-run` flag for safe preview
- **Adaptive Planner**: Retry with observation on failure
- **Three-layer Memory**: Session (RAM), World (persistent), History (audit)
- **Sandboxing**: Path validation and resource limits
- **Tools**: FileOps, TextOps, SystemOps, ProcessOps
- **Progress Indicators**: Spinner with elapsed time
- **Built-in Commands**: status, memory, update

### Documentation
- README.md - Installation and usage
- CONFIGURATION.md - LLM backend setup
- TROUBLESHOOTING.md - Common issues
- OLLAMA_TUNING.md - Model optimization
- STATUS.md - Project status and roadmap

### Tests
- 57 test cases covering all core modules
- 100% passing test suite

## Roadmap

### Next (Phase 2: Reliability)
- [ ] Execution traces with detailed error messages
- [ ] Better Ollama prompt engineering
- [ ] Fallback strategies for failed commands
- [ ] Success metrics dashboard

### Future (Phase 3: Enhancement)
- [ ] Voice interface (Whisper STT + Piper TTS)
- [ ] Code editing tools
- [ ] Git operations
- [ ] Project scaffolding
- [ ] Task decomposition for complex workflows

---

**Installation:**
```bash
git clone <repo>
cd zenus_os
./install.sh
```

**Usage:**
```bash
./zenus.sh                    # Interactive mode
./zenus.sh "list files"       # Direct command
./zenus.sh --explain "task"   # Show explanation first
```
