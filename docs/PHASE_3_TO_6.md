# Phases 3-6 Implementation Plan

## Overview
Complete implementation of the final 4 major features for Zenus OS.

## Status
- ✅ Phase 1: Tool Expansion (57 methods, 6 categories)
- ✅ Phase 2: Streaming Output
- 🚧 Phase 3: Learning from Failures (IN PROGRESS)
- ⏳ Phase 4: Undo/Rollback
- ⏳ Phase 5: Parallel Execution
- ⏳ Phase 6: Proactive Suggestions

---

## Phase 3: Learning from Failures 🧠

### Goal
Record and learn from execution failures to improve future performance.

### Components

#### 1. Failure Logger (`src/memory/failure_logger.py`)
- Record failure details (command, error, context)
- Categorize failure types (syntax, permission, network, etc.)
- Store in SQLite database for persistent learning

#### 2. Failure Analyzer (`src/brain/failure_analyzer.py`)
- Analyze failure patterns
- Suggest corrections based on past failures
- Calculate success probability for similar commands

#### 3. Adaptive Suggestions
- Before execution, check if similar commands failed before
- Suggest modifications based on past failures
- Learn which tools/approaches work better

### Implementation Tasks
- [ ] Create failure_logger.py with SQLite backend
- [ ] Create failure_analyzer.py with pattern matching
- [ ] Integrate failure checks into orchestrator
- [ ] Add failure recovery suggestions
- [ ] Create failure database schema
- [ ] Add tests for failure learning
- [ ] Documentation (FAILURE_LEARNING.md)

### Success Metrics
- 80%+ reduction in repeated failures
- Accurate failure prediction (>70% precision)
- Helpful recovery suggestions

---

## Phase 4: Undo/Rollback 🔄

### Goal
Safely reverse operations when needed.

### Components

#### 1. Action Tracker (`src/memory/action_tracker.py`)
- Track all executed operations with metadata
- Generate inverse operations for rollback
- Support transaction-like operation groups

#### 2. Rollback Engine (`src/cli/rollback.py`)
- Execute inverse operations safely
- Support partial rollbacks
- Validate rollback feasibility

#### 3. Checkpointing
- Create snapshots before risky operations
- Allow rollback to specific checkpoints
- Manage checkpoint lifecycle

### Implementation Tasks
- [ ] Create action_tracker.py with operation logging
- [ ] Create rollback.py with inverse operation mapping
- [ ] Implement checkpoint system
- [ ] Add rollback command to CLI
- [ ] Create rollback safety checks
- [ ] Add tests for rollback scenarios
- [ ] Documentation (UNDO_ROLLBACK.md)

### Success Metrics
- 95%+ successful rollbacks for supported operations
- Zero data loss in rollback scenarios
- Clear rollback feasibility indication

---

## Phase 5: Parallel Execution ⚡

### Goal
Execute independent operations concurrently for performance.

### Components

#### 1. Dependency Analyzer (`src/brain/dependency_analyzer.py`)
- Analyze step dependencies
- Build dependency graph
- Identify parallelizable operations

#### 2. Parallel Executor (`src/execution/parallel_executor.py`)
- Execute independent steps concurrently
- Manage thread/process pools
- Handle partial failures gracefully

#### 3. Resource Management
- Limit concurrent operations
- Prioritize critical operations
- Handle resource contention

### Implementation Tasks
- [ ] Create dependency_analyzer.py with graph building
- [ ] Create parallel_executor.py with concurrent execution
- [ ] Add resource management and limits
- [ ] Integrate into orchestrator
- [ ] Add progress tracking for parallel operations
- [ ] Add tests for parallel execution
- [ ] Documentation (PARALLEL_EXECUTION.md)

### Success Metrics
- 2-5x speedup for parallelizable workloads
- Zero race conditions or resource conflicts
- Graceful degradation on failures

---

## Phase 6: Proactive Suggestions 💡

### Goal
Suggest optimizations and improvements proactively.

### Components

#### 1. Suggestion Engine (`src/brain/suggestion_engine.py`)
- Analyze command patterns
- Detect inefficiencies
- Generate improvement suggestions

#### 2. Optimization Detector (`src/brain/optimizer.py`)
- Detect batch opportunities (*.pdf vs multiple files)
- Suggest better tool choices
- Recommend workflow improvements

#### 3. Learning Integration
- Use failure history for suggestions
- Learn user preferences
- Improve suggestions over time

### Implementation Tasks
- [ ] Create suggestion_engine.py with pattern analysis
- [ ] Create optimizer.py with optimization rules
- [ ] Add suggestion points in orchestrator
- [ ] Create suggestion database
- [ ] Add preference learning
- [ ] Add tests for suggestions
- [ ] Documentation (PROACTIVE_SUGGESTIONS.md)

### Success Metrics
- 60%+ suggestion acceptance rate
- Measurable performance improvements
- Non-intrusive suggestion delivery

---

## Integration Points

### Orchestrator Updates
All phases require integration into `orchestrator.py`:
- Pre-execution checks (failure learning, suggestions)
- Execution monitoring (action tracking, parallel execution)
- Post-execution updates (failure logging, rollback preparation)

### CLI Commands
New commands needed:
- `zenus rollback [steps]` - Rollback last N operations
- `zenus history --failures` - Show failure history
- `zenus suggest` - Get proactive suggestions
- `zenus optimize <command>` - Optimize a command

### Memory Integration
All phases interact with memory:
- Failure history in SQLite
- Action history for rollback
- Execution patterns for suggestions

---

## Testing Strategy

### Unit Tests
Each component needs comprehensive unit tests:
- 10+ tests per major component
- Edge case coverage
- Mock external dependencies

### Integration Tests
Test interactions between phases:
- Failure learning → suggestions
- Action tracking → rollback
- Dependency analysis → parallel execution

### End-to-End Tests
Real-world scenarios:
- Complex multi-step operations
- Failure scenarios and recovery
- Performance benchmarks

---

## Quality Gates

Before marking each phase complete:
1. ✅ All tests passing (95%+ coverage)
2. ✅ Documentation complete
3. ✅ Integration working smoothly
4. ✅ Performance benchmarks met
5. ✅ User testing successful

---

## Timeline Estimate
- Phase 3: 4-6 hours
- Phase 4: 6-8 hours
- Phase 5: 5-7 hours
- Phase 6: 4-6 hours
- **Total: 19-27 hours**

(These are working hours, not wall-clock time)
