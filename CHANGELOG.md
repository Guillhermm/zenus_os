# Changelog

All notable changes to Zenus OS will be documented in this file.

## [Unreleased]

### 2026-02-09 20:15

**Implement sandboxing with constraint validation**

- Add SandboxConstraints for filesystem/time/network/resource limits
- Add SandboxExecutor for constraint enforcement
- Add preset constraint profiles (safe, restricted, permissive)
- Add SandboxedTool base class for tool integration
- Document sandboxing architecture and safety layers

Sandboxing prevents damage from incorrect plans by validating all operations against defined constraints.

### 2026-02-09 20:00

**Implement three-layer memory system**

- Add SessionMemory for short-term context and reference resolution
- Add WorldModel for long-term user preferences and system knowledge
- Add IntentHistory for learning from past executions
- Document memory architecture and usage patterns

Memory enables natural conversation with context awareness across commands and sessions.

### 2026-02-09 19:45

**Implement adaptive execution with retry and observation**

- Add AdaptivePlanner with step-level retry capability
- Execute with observation and failure detection
- Track execution history for debugging and reporting
- Integrate adaptive planner into orchestrator
- Document adaptive execution architecture

Adaptive execution makes Zenus feel autonomous instead of brittle by recovering from failures.

### 2026-02-09 19:30

**Add system architecture documentation**

- Core architecture overview with Mermaid diagrams
- Intent IR specification and validation rules
- Data flow diagrams for execution pipeline
- Comparison with OpenClaw approach

### 2026-02-09 19:15

**Add system and process tools with README alias setup**

- Add SystemOps: disk_usage, memory_info, cpu_info, list_processes, uptime
- Add ProcessOps: find_by_name, info, kill
- Update README with installation guide and system-wide alias setup
- Update LLM prompts with new tool capabilities
- Add psutil dependency

### 2026-02-09 19:00

**Add comprehensive test suite**

- 42 tests covering all core modules
- Tests for: router, planner, safety policy, schemas, file operations
- pytest configuration with proper fixtures and isolation
- 100% coverage on critical execution paths

### 2026-02-09 18:50

**Add logging, dry-run mode, and error handling**

- Add structured audit logging to ~/.zenus/logs/ (JSONL format)
- Add dry-run mode with --dry-run flag
- Add custom exception types
- Improve error messages throughout pipeline
- Comprehensive .gitignore patterns

### 2026-02-09 18:40

**Introduce CLI command router and intent pipeline**

- Add proper CLI routing with help/version/shell/direct modes
- Separate parsing, orchestration, and execution layers
- Foundation for logging and automation

---

## [0.1.0-alpha] - 2026-02-09

Initial prototype with basic intent to plan to execute flow.
