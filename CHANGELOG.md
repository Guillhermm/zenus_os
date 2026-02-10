# Changelog

All notable changes to Zenus OS will be documented in this file.

## [Unreleased]

### 2026-02-09 22:10

**Integrate memory and sandbox into orchestrator**

- Memory system now integrated: context building, path tracking, history recording
- Session memory tracks recent activity and provides context
- World model learns frequent paths automatically
- Intent history records all executions for analysis
- Sandboxed planner added (simplified initial implementation)
- All features enabled by default in orchestrator

### 2026-02-09 20:15

**Implement sandboxed execution with resource limits**

- SandboxedExecutor: path validation and resource limits
- BubblewrapSandbox: advanced isolation (optional, requires bubblewrap)
- SandboxedTool: wraps tools with sandbox enforcement
- Temp workspace creation for isolated operations
- Enforces filesystem boundaries and prevents resource exhaustion
- Foundation for OS-grade security

### 2026-02-09 20:00

**Implement three-layer memory system**

- SessionMemory: short-term context within current session
- WorldModel: persistent system and user knowledge
- IntentHistory: complete audit trail with search capability
- Enables context-aware intent translation and learning
- Storage at ~/.zenus/ in JSON/JSONL formats
- Privacy controls and data ownership

### 2026-02-09 19:45

**Implement adaptive execution with retry and observation**

- AdaptivePlanner with step-level retry capability
- Execute with observation and failure detection
- Track execution history for debugging and reporting
- Integrate adaptive planner into orchestrator by default
- Enables autonomous recovery from transient failures

### 2026-02-09 19:30

**Add system architecture documentation with Mermaid diagrams**

- Core architecture overview with component responsibilities
- Intent IR specification and validation rules
- Data flow diagrams for execution pipeline
- Comparison with OpenClaw approach
- Adaptive execution architecture
- Memory system architecture
- Sandboxing architecture

### 2026-02-09 19:15

**Add system and process tools with README alias setup**

- Add SystemOps tool: disk_usage, memory_info, cpu_info, list_processes, uptime
- Add ProcessOps tool: find_by_name, info, kill
- Register new tools in registry
- Update LLM prompts (OpenAI and DeepSeek) with new tool capabilities
- Add psutil dependency for system monitoring
- Comprehensive README update with installation guide and alias setup

### 2026-02-09 19:00

**Add comprehensive test suite**

- Add pytest configuration and test infrastructure
- Add 42 tests covering all core modules
- Tests for: router, planner, safety policy, schemas, file operations
- 100% test coverage on critical paths
- Add requirements-dev.txt with testing dependencies

### 2026-02-09 18:50

**Add logging, dry-run mode, and error handling**

- Add structured audit logging to ~/.zenus/logs/ (JSONL format)
- Add dry-run mode: --dry-run flag to preview plans without executing
- Add custom exception types: SafetyError, IntentTranslationError, ExecutionError
- Improve error messages throughout the pipeline
- Update .gitignore with comprehensive patterns

### 2026-02-09 18:40

**Introduce CLI command router and intent pipeline**

- Add proper CLI routing with help/version/shell/direct modes
- Separate parsing, orchestration, and execution layers
- Foundation for logging and automation

---

## [0.1.0-alpha] - 2026-02-09

Initial prototype with basic intent to plan to execute flow.
