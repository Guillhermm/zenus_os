# Zenus OS Architecture

High-level overview of the Zenus OS system design.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interfaces                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │   TUI    │  │  Voice   │  │  Future  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │        Orchestrator Layer            │
        │  • Intent Translation                │
        │  • Context Building                  │
        │  • Execution Coordination            │
        │  • Memory Management                 │
        └──────────────┬──────────────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │         Brain Layer              │
        │  ┌──────────┐   ┌────────────┐  │
        │  │   LLM    │   │  Planner   │  │
        │  │ Factory  │   │ (Adaptive) │  │
        │  └──────────┘   └────────────┘  │
        │  ┌──────────┐   ┌────────────┐  │
        │  │  Goal    │   │  Failure   │  │
        │  │ Tracker  │   │  Analyzer  │  │
        │  └──────────┘   └────────────┘  │
        └──────────────┬──────────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │       Execution Layer            │
        │  • Tool Registry                 │
        │  • Parallel Executor             │
        │  • Error Recovery                │
        │  • Smart Cache                   │
        └──────────────┬──────────────────┘
                       │
        ┌──────────────▼──────────────────┐
        │         Tools Layer              │
        │  FileOps  SystemOps  ProcessOps  │
        │  TextOps  BrowserOps PackageOps  │
        │  GitOps   NetworkOps ServiceOps  │
        │  ContainerOps  VisionOps         │
        └───────────────────────────────────┘
```

## Core Components

### 1. User Interfaces

**CLI** (`packages/cli/`)
- Interactive shell with tab completion
- Direct command execution
- Progress indicators and formatted output
- Command history and navigation

**TUI** (`packages/tui/`)
- Terminal dashboard with Textual
- Live status panels
- Execution log viewer
- Memory browser
- Statistics dashboard

### 2. Orchestrator Layer (`packages/core/src/zenus_core/cli/orchestrator.py`)

**Responsibilities:**
- Translate natural language → Intent IR
- Build context from memory and environment
- Coordinate execution through planner
- Update memory with results
- Handle errors and logging

**Key Features:**
- Context-aware execution
- Session state management
- Transaction tracking for rollback
- Semantic search integration

### 3. Brain Layer (`packages/core/src/zenus_core/brain/`)

**LLM Factory** (`llm/factory.py`)
- Multi-backend support (Anthropic, OpenAI, DeepSeek, Ollama)
- Model selection and routing
- Streaming support
- Lazy loading

**Adaptive Planner** (`adaptive_planner.py`, `sandboxed_planner.py`)
- Step-by-step execution with observation
- Retry logic with backoff
- Failure recovery
- Execution history tracking

**Goal Tracker** (`goal_tracker.py`)
- LLM-based reflection on goal achievement
- Confidence scoring
- Next-step suggestions
- Iteration limit enforcement

**Failure Analyzer** (`failure_analyzer.py`)
- Failure pattern detection
- Root cause analysis
- Suggestion generation
- Success probability estimation

### 4. Execution Layer (`packages/core/src/zenus_core/execution/`)

**Parallel Executor** (`parallel_executor.py`)
- Dependency graph analysis
- Concurrent execution of independent steps
- Thread pool management
- 2-3x speedup on batch operations

**Error Recovery** (`error_recovery.py`)
- Automatic retry with exponential backoff
- Error classification
- Alternative strategy suggestions
- Graceful degradation

**Smart Cache** (`smart_cache.py`)
- LLM response caching (1hr TTL)
- Filesystem scan caching (5min TTL)
- LRU eviction
- Optional persistence

**Shell Executor** (`tools/shell_executor.py`)
- Real-time output streaming
- No fixed timeouts
- stdout/stderr separation
- Capture while streaming

### 5. Tools Layer (`packages/core/src/zenus_core/tools/`)

**File Operations** (`file_ops.py`)
- scan, mkdir, move, write_file, touch
- Large file support (10MB chunks)
- Wildcard/glob patterns

**System Operations** (`system_ops.py`)
- Resource monitoring (CPU, memory, disk)
- Process management
- Uptime tracking
- Large file discovery

**Git Operations** (`git_ops.py`)
- status, add, commit, push, pull
- Branch management
- Diff and log viewing

**Package Operations** (`package_ops.py`)
- Multi-distro support (apt, dnf, pacman)
- install, remove, update
- Search and info
- No timeout for long operations

**10 Total Tool Categories** - See `tools/registry.py` for full list

### 6. Memory System (`packages/core/src/zenus_core/memory/`)

**Three-Layer Architecture:**

1. **Session Memory** (`session_memory.py`)
   - Ephemeral (RAM only)
   - Recent intents and context
   - Context summarization

2. **World Model** (`world_model.py`)
   - Persistent (disk)
   - Frequent paths, preferences
   - Application usage patterns
   - Learning over time

3. **Intent History** (`intent_history.py`)
   - Audit trail (JSONL files)
   - Success/failure tracking
   - Query and search
   - Analytics (success rate, popular goals)

**Semantic Search** (`semantic_search.py`)
- sentence-transformers embeddings
- Cosine similarity matching
- Find similar past commands
- Used in explain mode

### 7. Safety Layer (`packages/core/src/zenus_core/safety/`)

**Policy Engine** (`policy.py`)
- Risk assessment (0-3 scale)
- Path validation
- Resource limits
- Confirmation requirements

**Sandbox** (`sandbox/`)
- Capability-based constraints
- Violation detection
- Isolated execution (future)

### 8. Context System (`packages/core/src/zenus_core/context/`)

**Context Manager** (`context_manager.py`)
- Current directory tracking
- Git repository state
- Time of day awareness
- Recent file monitoring
- Running process detection

**Dynamic Context:**
- Updates on every command
- Provides environmental prompt
- Influences LLM decisions

## Data Flow

### Request Flow

1. **User Input** → CLI/TUI captures command
2. **Orchestrator** → Builds context + translates intent
3. **LLM** → Generates Intent IR (JSON plan)
4. **Planner** → Executes steps sequentially/parallel
5. **Tools** → Perform actual operations
6. **Results** → Formatted output + memory update

### Iterative Flow (Complex Tasks)

1. **Initial Plan** → LLM generates first attempt
2. **Execute** → Run plan, collect observations
3. **Reflect** → Goal Tracker checks achievement
4. **Loop** → If not achieved, re-plan with observations
5. **Safety** → Max 50 iterations, stuck detection, user confirmation

### Memory Flow

**Write Path:**
```
Execution → IntentHistory (JSONL)
          → SessionMemory (RAM)
          → WorldModel (update frequencies)
          → SemanticSearch (embedding)
```

**Read Path:**
```
User Input → Context Manager (environment)
           → Session Memory (recent activity)
           → World Model (frequent paths)
           → Semantic Search (similar commands)
           → Enhanced Context → LLM
```

## Key Design Principles

### 1. **Modularity**
- Clear separation of concerns
- Each layer has single responsibility
- Easy to swap implementations

### 2. **Extensibility**
- Plugin-style tool registry
- Multiple LLM backend support
- Configurable memory storage

### 3. **Reliability**
- Graceful error handling
- Automatic retry mechanisms
- Undo/rollback capability

### 4. **Performance**
- Parallel execution where safe
- Smart caching (LLM, filesystem)
- Streaming for large operations

### 5. **Safety**
- Sandboxed execution
- Risk assessment
- User confirmation for dangerous ops
- Comprehensive audit logs

### 6. **Intelligence**
- Learn from failures
- Adapt strategies
- Proactive suggestions
- Context-aware decisions

## Technology Stack

**Languages:**
- Python 3.10+ (core, CLI, TUI)

**Key Dependencies:**
- `pydantic` - Schema validation (Intent IR)
- `rich` - Terminal formatting
- `textual` - TUI framework
- `anthropic`, `openai` - LLM APIs
- `requests` - HTTP client
- `psutil` - System monitoring
- `playwright` - Browser automation (optional)
- `sentence-transformers` - Semantic search (optional)

**Build System:**
- Poetry - Dependency management
- Poetry workspace - Monorepo structure

**Storage:**
- JSONL - Logs and history
- JSON - World model and cache
- SQLite - Future (for analytics)

## Deployment

**Current:**
- Self-hosted only
- Local installation via `install.sh`
- Runs on user's machine

**Future:**
- Cloud-hosted option
- Multi-user support
- Docker containers
- Kubernetes operator

## Performance Characteristics

**Latency:**
- One-shot commands: 1-5 seconds (LLM dependent)
- Iterative tasks: 10-60 seconds (task dependent)
- Cached commands: <100ms

**Throughput:**
- Sequential: 1 command/sec
- Parallel: 5-10 ops/sec (independent steps)

**Resource Usage:**
- Memory: ~100MB baseline + LLM cache
- CPU: Minimal (bursty during execution)
- Disk: ~10MB logs per day of active use

## Security Model

**Threat Model:**
- Malicious LLM outputs (injection attacks)
- Accidental destructive operations
- Unauthorized access to sensitive files
- Resource exhaustion

**Mitigations:**
- Intent IR schema validation
- Safety policy enforcement
- Path sandboxing
- Resource quotas
- User confirmation for high-risk ops
- Comprehensive audit logs

**Future:**
- RBAC (role-based access control)
- Multi-tenancy isolation
- Encrypted storage
- OAuth/SSO integration

## Monitoring & Observability

**Current:**
- Audit logs (JSONL)
- Session memory stats
- Execution history
- Success/failure tracking

**Future:**
- OpenTelemetry instrumentation
- Metrics dashboard
- Real-time alerts
- Performance profiling

## Testing Strategy

**Current:**
- Unit tests for core modules
- Integration tests for orchestrator
- Tool tests (mocked)

**Future:**
- E2E tests for workflows
- Property-based testing
- Fuzzing for safety policy
- Load testing
- CI/CD pipeline

---

## Learn More

- **[Full Architecture Docs](docs/ARCHITECTURE.md)** - Deep dive into each component
- **[Features Guide](docs/FEATURES.md)** - Complete feature documentation
- **[User Guide](docs/)** - Detailed usage and examples
- **[CHANGELOG](CHANGELOG.md)** - Version history
- **[ROADMAP](ROADMAP.md)** - Future plans

---

*Last updated: 2026-02-24*
