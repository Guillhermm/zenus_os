# Zenus Development TODO

Task list for short-term and medium-term improvements.

## 🚨 Immediate (Before First Release)

### Setup & Verification
- [ ] Install Poetry on development machine
- [ ] Run `poetry install` and verify no errors
- [ ] Run all tests: `poetry run pytest`
- [ ] Verify CLI works: `poetry run zenus --version`
- [ ] Test all major features (rollback, parallel, learning)
- [ ] Fix any broken tests from migration

### Critical Bugs
- [ ] Test import paths are all correct
- [ ] Verify rollback works in new structure
- [ ] Test parallel execution with new imports
- [ ] Verify failure learning database paths
- [ ] Test action tracker database paths

### Documentation
- [ ] Update README with monorepo instructions
- [ ] Verify all examples in docs still work
- [ ] Update CONFIGURATION.md for new structure
- [ ] Add CONTRIBUTING.md guide

## 📊 Short-Term Improvements (Week 1-2)

### Test Coverage
- [ ] Expand test coverage to 80%+
- [ ] Add integration tests for parallel executor
- [ ] Add end-to-end workflow tests
- [ ] Add performance regression tests
- [ ] Test rollback edge cases
- [ ] Add tests for failure learning patterns

### Configuration System
- [ ] Create `~/.zenus/config.yaml` support
- [ ] Add configuration schema validation
- [ ] Support custom tool paths
- [ ] Allow safety policy overrides
- [ ] Configure parallel execution limits
- [ ] Add logging level configuration

### Error Handling
- [ ] Improve network timeout handling in parallel execution
- [ ] Add LLM rate limiting handling
- [ ] Better partial rollback failure messages
- [ ] Add retry logic for LLM API errors
- [ ] Improve error messages for users

### Tool Expansion
- [ ] Add DatabaseOps (PostgreSQL, MySQL, SQLite)
  - connect, query, schema, backup
- [ ] Add CloudOps (basic AWS/GCP/Azure CLI wrappers)
  - list-instances, start, stop, logs
- [ ] Add NotificationOps (email, Slack, Discord)
  - send-email, post-slack, send-discord
- [ ] Add MediaOps (ffmpeg, imagemagick)
  - convert-image, resize, compress-video, extract-audio

### Performance
- [ ] Add performance profiling
  - Per-step timing
  - Memory usage tracking
  - Parallel efficiency metrics
  - LLM latency breakdown
- [ ] Optimize LLM prompt caching
- [ ] Add result caching for repeated operations
- [ ] Optimize dependency analysis algorithm

## 🔧 Medium-Term Improvements (Month 1-2)

### Vector Search for Memory
- [ ] Install sentence-transformers
- [ ] Create embedding index for past intents
- [ ] Semantic similarity search for similar commands
- [ ] Better failure prediction using embeddings
- [ ] Smart context retrieval

### LLM-Powered Features
- [ ] LLM-generated failure fixes (beyond rule-based)
- [ ] LLM suggests alternative approaches
- [ ] LLM generates test cases for commands
- [ ] LLM improves error messages
- [ ] LLM explains execution plans in natural language

### Advanced Rollback
- [ ] Automatic checkpointing before destructive ops
- [ ] Git branch restore capability
- [ ] Database snapshot support
- [ ] Configuration file backups
- [ ] Multi-machine rollback sync (future)

### Performance Dashboard
- [ ] Create `zenus stats` command
- [ ] Show success rate over time
- [ ] Display average speedup from parallelization
- [ ] Most used tools ranking
- [ ] Failure trends visualization
- [ ] Resource usage statistics

### Plugin System
- [ ] Design plugin API
- [ ] Create plugin registry
- [ ] Support loading external tools
- [ ] Plugin discovery mechanism
- [ ] Plugin testing framework
- [ ] Example plugins (AWS, Kubernetes, etc.)

## 🚀 Long-Term Features (Month 3+)

### zenus-tui Package
- [ ] Design TUI interface (using Textual)
- [ ] Multi-panel layout (command, history, suggestions, status)
- [ ] Real-time execution visualization
- [ ] Interactive command editing
- [ ] Keyboard shortcuts
- [ ] Theme support

### zenus-voice Package
- [ ] Whisper integration (local STT)
- [ ] Wake word detection
- [ ] Voice command processing
- [ ] TTS for responses (ElevenLabs/Piper)
- [ ] Conversational context
- [ ] Multi-turn dialogues

### zenus-web Package
- [ ] FastAPI backend
- [ ] React/HTMX frontend
- [ ] Real-time execution monitoring
- [ ] History browser with search
- [ ] Failure analytics dashboard
- [ ] Remote execution capability
- [ ] Multi-user support

### zenus-agent Package (The True OS)
- [ ] Autonomous daemon
- [ ] Scheduled tasks ("every morning at 9am")
- [ ] Triggered actions ("when disk > 90%")
- [ ] Proactive suggestions
- [ ] Background optimization
- [ ] Learning from user patterns
- [ ] Predictive maintenance

### Advanced Features
- [ ] Multi-LLM routing (choose model per task)
- [ ] Distributed execution (multiple machines)
- [ ] Shared learning database (opt-in community patterns)
- [ ] Automatic fix application
- [ ] Time-travel rollback (to specific timestamp)
- [ ] AI-powered code generation
- [ ] Natural language API documentation

## 📝 Code Quality

### Ongoing
- [ ] Maintain 80%+ test coverage
- [ ] Keep all tests passing
- [ ] Run black on every commit
- [ ] Run ruff and fix issues
- [ ] Type hints for all new code
- [ ] Docstrings for all public APIs
- [ ] Update CHANGELOG.md
- [ ] Semantic versioning

### Refactoring
- [ ] Extract common patterns into utilities
- [ ] Reduce code duplication
- [ ] Improve error handling consistency
- [ ] Optimize hot paths
- [ ] Reduce dependencies where possible

## 🐛 Known Issues

### To Fix
- [ ] CLI tests may need adjustment for new imports
- [ ] Some integration tests need `poetry run` prefix
- [ ] Verify all tool imports work correctly
- [ ] Test semantic search in new structure
- [ ] Verify .zenus directory paths work

### To Investigate
- [ ] Performance impact of import changes
- [ ] Memory usage in parallel execution
- [ ] LLM token usage optimization
- [ ] Database lock contentions
- [ ] Thread pool sizing

## 📦 Publishing Checklist

Before each PyPI release:
- [ ] Update version in both pyproject.toml files (must match)
- [ ] Update CHANGELOG.md
- [ ] Run all tests: `poetry run pytest`
- [ ] Verify CLI: `poetry run zenus --version`
- [ ] Test installation: `pip install .`
- [ ] Test rollback functionality
- [ ] Test parallel execution
- [ ] Review documentation
- [ ] Create git tag
- [ ] Push to GitHub
- [ ] Create GitHub release
- [ ] Monitor CI/CD workflow
- [ ] Verify PyPI upload
- [ ] Test installation from PyPI
- [ ] Announce release

## 🎯 Priority Order

1. **P0 (Critical)**: Setup verification, broken tests, critical bugs
2. **P1 (High)**: Test coverage, error handling, configuration system
3. **P2 (Medium)**: Tool expansion, performance, vector search
4. **P3 (Low)**: Advanced features, new packages, UI

## 📊 Progress Tracking

- [ ] Week 1: P0 + P1 (critical + high priority)
- [ ] Week 2-4: P2 (medium priority + some P1)
- [ ] Month 2: P3 + new packages (TUI/Voice planning)
- [ ] Month 3+: Advanced features + ecosystem

---

**Note**: This is a living document. Update as priorities change and tasks are completed.
