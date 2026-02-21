# Zenus TUI - Functionality Overview

**Status**: ✅ **Day 2 Complete - Fully Wired & Functional**

## What's Working Now

### 🎯 Command Execution
- **Execute Button**: Runs command normally (auto-detects if iterative needed)
- **Dry Run Button**: Shows plan without executing
- **Iterative Button**: Forces iterative mode (12 iterations max)
- **Enter Key**: Quick execute from input field
- **Async Execution**: Commands run in background workers (UI stays responsive)
- **Error Handling**: Graceful failure display with error messages

### 📊 Status Bar (Top)
- **Session Duration**: Shows minutes since TUI started
- **Command Count**: Total commands executed this session
- **Last Result**: "Ready ✓" / "Executing... ⏳" / "Success ✓" / "Failed ✗"
- **Real-time Updates**: Changes as you execute commands

### 📝 Execution Tab (F1)
**ExecutionLog Panel** (60% height):
- Shows last ~20 executions with timestamps
- Format: `[HH:MM:SS] command ✓/✗ duration`
- Displays result summary (first line)
- Auto-scrolls to latest
- Color-coded: green (success), red (fail), cyan (command)

**PatternSuggestion Panel** (40% height):
- Hidden by default
- Appears after every 10 commands
- Shows detected patterns (recurring, workflows, time-based)
- Suggests automation (cron expressions)
- Based on last 100 transactions

### 🕰️ History Tab (F2)
- **Data Source**: `action_tracker.get_recent_transactions(limit=50)`
- **Columns**: Time, Command, Status (✓/✗), Duration
- **Format**: MM/DD HH:MM for easy scanning
- **Auto-refresh**: Updates after each execution
- **Manual refresh**: F5 key

### 🧠 Memory Tab (F3)
**Detected Patterns Section**:
- Shows top 10 patterns from last 30 days
- Pattern types: recurring, workflow, preference, time-based
- Displays: description, confidence %, occurrences
- Suggests cron expressions for automation

**World Model Section**:
- Shows last 10 facts from world_model
- Format: `category: key = value`
- Examples: filesystem paths, system state, user preferences

**Auto-refresh**: Updates after each execution
**Manual refresh**: F5 key

### 📖 Explain Tab (F4)
- Shows last executed command + result
- Displays user input and output summary
- *Advanced step-by-step explanation coming soon*

### ⌨️ Keyboard Shortcuts
- `F1-F4`: Switch between tabs
- `F5`: Refresh current tab (History/Memory)
- `Enter`: Execute command (when in input field)
- `q` or `Ctrl+C`: Quit TUI

## Architecture

### Components
```
ZenusDashboard (App)
├── StatusBar (custom widget)
├── TabbedContent
│   ├── ExecutionLog + PatternSuggestion
│   ├── HistoryView (DataTable)
│   ├── MemoryView (RichLog)
│   └── ExplainView (RichLog)
└── CommandInput (Input + 3 Buttons)
```

### Integrations
- **Orchestrator**: `execute_command()` + `execute_iterative()`
- **ActionTracker**: `get_recent_transactions()` for history
- **PatternDetector**: `detect_patterns()` for automation suggestions
- **WorldModel**: `get_recent_facts()` for context
- **ExplainMode**: Coming soon for detailed step breakdowns

### Execution Flow
1. User types command → presses button/Enter
2. Input validated → cleared
3. Status → "Executing... ⏳"
4. Worker spawned → orchestrator.execute_command()
5. Result captured → duration calculated
6. UI updated on main thread:
   - Status bar (count + result)
   - Execution log (append entry)
   - History tab (refresh)
   - Memory tab (refresh)
   - Explain tab (update)
7. Every 10 commands → pattern check

## Launch

```bash
# From anywhere (after setup)
zenus-tui

# Or directly
~/projects/zenus_os/zenus-tui.sh

# Or via Poetry
cd ~/projects/zenus_os/packages/tui
poetry run zenus-tui
```

## What's Next (Polish Phase)

### Visual Improvements
- [ ] Better color scheme for dark/light modes
- [ ] Progress bars for long-running commands
- [ ] More detailed explain view with step tree
- [ ] Command history autocomplete in input
- [ ] Search/filter in History tab
- [ ] Export logs to file

### Features
- [ ] Split view (watch execution live)
- [ ] Command templates/snippets
- [ ] Favorite commands quick-access
- [ ] Real-time streaming (show output as it happens)
- [ ] Confirmation dialogs for dangerous commands
- [ ] Rollback button (undo last command)

### Performance
- [ ] Lazy loading for large history
- [ ] Pagination in Memory tab
- [ ] Cache pattern detection results
- [ ] Debounce auto-refresh

## Known Limitations

1. **No real-time streaming yet**: Results appear after completion
2. **Basic explain view**: Doesn't show step-by-step breakdown
3. **Pattern detection**: Only checks every 10 commands (not real-time)
4. **No rollback UI**: Must use CLI for undo
5. **No confirmation dialogs**: Executes immediately (same as CLI)

---

**Day 2 Time**: ~1.5 hours (wiring + testing)
**Status**: ✅ Functional TUI ready for testing
**Next**: Polish UI, add streaming, improve explain view
