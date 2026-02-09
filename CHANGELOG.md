# Changelog

All notable changes to Zenus OS will be documented in this file.

## [Unreleased]

### 2026-02-09 18:40 — Introduce CLI command router and intent pipeline

**Changed:**
- Refactored entry point (`src/zenusd/main.py`) to use proper CLI routing
- Separated concerns: CLI parsing → Intent translation → Plan execution
- Added `CommandRouter` for parsing CLI arguments (help, version, shell, direct)
- Added `Orchestrator` to manage the full pipeline and confirmation flow
- Refactored `execute_plan()` to focus purely on execution (no UI concerns)

**Added:**
- New `src/cli/` package with `router.py` and `orchestrator.py`
- Support for direct command execution: `zenus "organize my downloads"`
- Help command: `zenus help`
- Version command: `zenus version`
- Interactive shell mode (default): `zenus` or `zenus shell`

**Impact:**
- System is now truly CLI-first (was REPL-only before)
- Clear separation between parsing, intent, and execution layers
- Foundation for logging, audit trails, and non-interactive automation
- More deterministic and testable architecture

---

## [0.1.0-alpha] - 2026-02-09

Initial prototype with basic intent → plan → execute flow.
