# Changelog

All notable changes to Zenus OS will be documented in this file.

## [Unreleased]

### 2026-02-09 18:50

**Add logging, dry-run mode, and improved error handling**

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
