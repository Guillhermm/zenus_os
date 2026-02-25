# Budget Roadmap: $4 Token Budget

**Goal**: Maximize value with ~$4 of Anthropic tokens (~400K input + 80K output tokens)

**Strategy**: Build features that are mostly code (low token usage) with high immediate impact, prioritizing the **Model Router** which will save money going forward.

---

## Priority 1: Model Router (SAVES MONEY!) 🎯

**Why First:** This feature will PAY FOR ITSELF by routing cheap tasks to DeepSeek and expensive tasks to Claude.

**Token Cost:** ~$0.50 (testing and iteration)

**Implementation:**
1. **Task Complexity Estimator** (~200 lines)
   - Heuristics: command length, keywords, risk level
   - Simple = DeepSeek, Complex = Claude
   - Example:
     - "list files" → DeepSeek (cheap)
     - "analyze codebase and refactor" → Claude (expensive)

2. **Cost Tracking** (~100 lines)
   - Track tokens per command
   - Show cost in status command
   - Alert when approaching budget

3. **Fallback Cascade** (~150 lines)
   - Try DeepSeek first
   - If fails or low confidence → Claude
   - If Claude fails → local rules

**Impact:**
- ✅ 70-80% cost reduction (most tasks are simple)
- ✅ Claude used only when needed
- ✅ Better resource allocation
- ✅ Real-time cost visibility

**Estimated Savings:** ~$2-3 per $4 spent (50-75% reduction going forward)

---

## Priority 2: Configuration Management (NO TOKENS!)

**Why:** Makes Zenus more professional and easier to configure.

**Token Cost:** $0 (pure coding)

**Implementation:**
1. **YAML Config** (~200 lines)
   - Replace .env with zenus.yaml
   - Structured configuration
   - Validation with schema
   - Example:
     ```yaml
     llm:
       default: deepseek
       fallback: anthropic
       models:
         deepseek:
           api_key: ${DEEPSEEK_API_KEY}
           max_tokens: 2048
         anthropic:
           api_key: ${ANTHROPIC_API_KEY}
           model: claude-3-5-sonnet-20241022
     
     execution:
       parallel: true
       max_retries: 2
       timeout: null
     
     memory:
       enabled: true
       semantic_search: true
     ```

2. **Hot Reload** (~100 lines)
   - Watch config file for changes
   - Reload without restart
   - Validate before applying

3. **Profile System** (~150 lines)
   - Dev, staging, production profiles
   - Override per environment
   - Easy switching

**Impact:**
- ✅ Professional configuration
- ✅ Easier for users to customize
- ✅ Foundation for multi-user

---

## Priority 3: Feedback System (MINIMAL TOKENS)

**Why:** Learn what works, improve prompts over time.

**Token Cost:** ~$0.20 (testing)

**Implementation:**
1. **Thumbs Up/Down** (~150 lines)
   - After each command: "Was this helpful? (y/n/skip)"
   - Store in feedback.jsonl
   - Track per command type

2. **Success Metrics** (~100 lines)
   - Success rate per tool
   - Success rate per intent type
   - Show in status command

3. **Prompt Tuning Data** (~100 lines)
   - Export successful commands for fine-tuning
   - JSON format for training
   - Privacy-aware (filter sensitive data)

**Impact:**
- ✅ Data-driven improvements
- ✅ Identify problem areas
- ✅ Foundation for self-improvement

---

## Priority 4: Enhanced Error Handling (MINIMAL TOKENS)

**Why:** Reduce frustration, increase success rate.

**Token Cost:** ~$0.30 (testing edge cases)

**Implementation:**
1. **Better Error Messages** (~200 lines)
   - Structured error types
   - User-friendly explanations
   - Actionable suggestions
   - Example:
     ```
     ❌ Command failed: Package not found
     
     Reason: 'teams' is not in apt repositories
     
     Suggestions:
     1. Try: zenus "search for teams package"
     2. Install from snap: zenus "install teams from snap"
     3. Check if already installed: zenus "is teams installed"
     ```

2. **Fallback Strategies** (~150 lines)
   - If tool fails, suggest alternatives
   - Example: apt fails → try snap → try manual download

3. **Recovery Suggestions** (~100 lines)
   - Based on error type
   - Context-aware
   - Learn from past recoveries

**Impact:**
- ✅ Higher success rate
- ✅ Less user frustration
- ✅ Better UX

---

## Priority 5: Performance Improvements (NO TOKENS!)

**Why:** Faster = better UX, no cost increase.

**Token Cost:** $0 (pure optimization)

**Implementation:**
1. **Intent Memoization** (~200 lines)
   - Hash user input + context
   - Cache Intent IR for identical requests
   - TTL: 1 hour
   - Example: "list files" → cached plan reused

2. **Lazy Loading** (~150 lines)
   - Import tools only when needed
   - Defer heavy imports
   - Faster startup (2-3x)

3. **Connection Pooling** (~100 lines)
   - Reuse HTTP connections to LLM APIs
   - Reduce latency
   - Better throughput

**Impact:**
- ✅ 2-3x faster responses for cached commands
- ✅ Faster startup
- ✅ Better perceived performance

---

## Priority 6: Rich Output (MINIMAL TOKENS)

**Why:** Better visualization = easier to understand results.

**Token Cost:** ~$0.50 (testing visualization logic)

**Implementation:**
1. **Auto-Detect Data Types** (~200 lines)
   - Detect tables in output
   - Detect lists/arrays
   - Format appropriately

2. **Table Rendering** (~150 lines)
   - Pretty tables with borders
   - Sortable columns
   - Pagination for large data

3. **Chart Generation** (~200 lines)
   - ASCII charts (lightweight)
   - Matplotlib integration (optional)
   - Auto-detect chart-worthy data

**Impact:**
- ✅ Better readability
- ✅ More professional output
- ✅ Easier to spot patterns

---

## Priority 7: Git Integration Improvements (MINIMAL TOKENS)

**Why:** Core developer workflow enhancement.

**Token Cost:** ~$0.50 (testing)

**Implementation:**
1. **Advanced Git Operations** (~300 lines)
   - Interactive rebase helper
   - Cherry-pick assistant
   - Merge conflict resolver
   - Commit message generator

2. **GitHub API** (~200 lines)
   - Create PRs
   - List issues
   - Comment on PRs
   - Webhook integration

3. **Git Workflow Templates** (~100 lines)
   - Feature branch workflow
   - Gitflow
   - Trunk-based development

**Impact:**
- ✅ Streamline development
- ✅ Less context switching
- ✅ Better Git UX

---

## Priority 8: Better Observability (NO TOKENS!)

**Why:** Understand system behavior, debug issues.

**Token Cost:** $0 (infrastructure)

**Implementation:**
1. **Structured Logging** (~200 lines)
   - JSON logs with levels
   - Contextual information
   - Easy to parse

2. **Metrics Collection** (~150 lines)
   - Token usage per command
   - Latency distribution
   - Success/failure rates
   - Cache hit rates

3. **Status Dashboard** (~200 lines)
   - Real-time metrics in TUI
   - Historical graphs
   - Cost tracking

**Impact:**
- ✅ Better debugging
- ✅ Performance insights
- ✅ Cost awareness

---

## Budget Breakdown

| Feature                      | Token Cost | Dev Time | Impact | ROI   |
|------------------------------|------------|----------|--------|-------|
| 1. Model Router              | $0.50      | 4 hours  | 🔥🔥🔥  | ⭐⭐⭐⭐⭐ |
| 2. Configuration Management  | $0.00      | 3 hours  | 🔥🔥    | ⭐⭐⭐⭐⭐ |
| 3. Feedback System           | $0.20      | 2 hours  | 🔥🔥    | ⭐⭐⭐⭐  |
| 4. Enhanced Error Handling   | $0.30      | 3 hours  | 🔥🔥🔥  | ⭐⭐⭐⭐  |
| 5. Performance Improvements  | $0.00      | 3 hours  | 🔥🔥    | ⭐⭐⭐⭐⭐ |
| 6. Rich Output               | $0.50      | 4 hours  | 🔥     | ⭐⭐⭐   |
| 7. Git Integration           | $0.50      | 4 hours  | 🔥🔥    | ⭐⭐⭐   |
| 8. Better Observability      | $0.00      | 3 hours  | 🔥🔥    | ⭐⭐⭐⭐  |
| **TOTAL**                    | **$2.00**  | **26h**  |        |       |

**Remaining Budget:** $2.00 for testing and iteration

---

## Implementation Order

**Week 1 (High ROI, No Tokens):**
1. Configuration Management (0 tokens, huge UX improvement)
2. Performance Improvements (0 tokens, immediate speedup)
3. Better Observability (0 tokens, foundation for everything)

**Week 2 (Model Router - PAYS FOR ITSELF):**
4. Model Router ($0.50, will save $2-3 going forward!)
5. Cost Tracking (part of router)

**Week 3 (Better UX):**
6. Feedback System ($0.20)
7. Enhanced Error Handling ($0.30)

**Week 4 (Polish):**
8. Rich Output ($0.50)
9. Git Integration ($0.50)

---

## Beyond $4 Budget

Once Model Router is live and saving money, we can tackle:
- Multi-agent collaboration (high token usage)
- Voice interface (STT/TTS infrastructure)
- Advanced reasoning (tree of thoughts)
- Cloud integrations (AWS/Azure)

---

## Key Insight

**The Model Router is the golden feature** - it's the ONLY feature that reduces future costs. Everything else either costs nothing (pure code) or costs tokens (features).

By building the router first, your $4 becomes more like $6-8 in effective purchasing power going forward.

---

## Questions?

1. Does this priority order make sense?
2. Any features you'd swap out?
3. Should we start with Model Router immediately?

---

*Budget: ~$4 | Estimated Usage: $2.00 (with $2 buffer) | Expected Savings: $2-3 per future $4*
