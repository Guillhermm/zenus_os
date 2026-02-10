# Zenus OS

Zenus OS is a voice-first, AI-mediated operating system layer that replaces traditional user interfaces with intent-based interaction and bounded autonomy.

This is a full operating system that can be controlled by voice, where AI:

- Understands complex user intent
- Plans and performs operations autonomously
- Interacts with system APIs to get things done
- Can talk back, ask clarifying questions, and learn from user behavior

## Features

- **CLI-First**: Direct execution, interactive shell, help system, dry-run mode
- **Intent-Driven**: Natural language to validated structured commands
- **Adaptive Execution**: Automatic retry with observation on failures
- **Memory System**: Learns from usage, remembers context, tracks patterns
- **OS-Grade Safety**: Path validation, resource limits, sandbox enforcement
- **Local LLM Support**: Run on your hardware with Ollama (4-16GB RAM)

## Setup

### Prerequisites

Make sure `python3` and `python3-venv` are installed:

```bash
sudo apt update
sudo apt install python3 python3-venv
```

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd zenus_os
```

2. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt

# For development (testing):
pip install -r requirements-dev.txt
```

4. Configure environment variables:

```bash
cp .env.example .env
# Edit .env to choose your LLM backend
```

**Important:** Each line in `.env` must be on a separate line. Format:
```
ZENUS_LLM=ollama
OLLAMA_MODEL=phi3:mini
```

**Not:**
```
ZENUS_LLM=ollamaOLLAMA_MODEL=phi3:mini  # Wrong!
```

### LLM Backend Options

**Option 1: Ollama (Local, FREE - Recommended)**
```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama service
ollama serve
# Or with systemd:
# sudo systemctl enable ollama
# sudo systemctl start ollama

# 3. Pull a model
ollama pull phi3:mini        # 3.8GB - Fast, efficient (recommended)
# OR
ollama pull llama3.2:3b      # 2GB - Lightweight
# OR
ollama pull qwen2.5:3b       # 2.3GB - Good reasoning

# 4. Configure .env
ZENUS_LLM=ollama
OLLAMA_MODEL=phi3:mini
```

**Option 2: OpenAI (Cloud, requires API key)**
```bash
# Get API key: https://platform.openai.com/api-keys
# Edit .env:
ZENUS_LLM=openai
OPENAI_API_KEY=sk-your-key-here
```

**Option 3: DeepSeek (Cloud, requires API key)**
```bash
# Get API key: https://platform.deepseek.com
# Edit .env:
ZENUS_LLM=deepseek
DEEPSEEK_API_KEY=sk-your-key-here
```

### System-Wide Alias (Recommended)

To run `zenus_os` from anywhere:

**For Bash** (add to `~/.bashrc`):

```bash
alias zenus_os='cd ~/projects/zenus_os && source .venv/bin/activate && python src/main.py'
```

**For Zsh** (add to `~/.zshrc`):

```bash
alias zenus_os='cd ~/projects/zenus_os && source .venv/bin/activate && python src/main.py'
```

**Apply changes:**

```bash
# For Bash
source ~/.bashrc

# For Zsh
source ~/.zshrc
```

**Note:** Adjust `~/projects/zenus_os` to your actual installation path.

### Verify Installation

```bash
# Using alias (if configured)
zenus_os version
zenus_os help

# Or from project directory
python src/main.py version
```

## Usage

### Interactive Mode (REPL)

```bash
zenus_os

# Or from project directory:
python src/main.py
```

This starts an interactive shell:

```
zenus > organize my Downloads folder by file type
zenus > show disk usage
zenus > list top 10 processes
zenus > read my notes.txt file
zenus > exit
```

### Direct Execution

Run commands directly from your shell:

```bash
zenus_os "organize my downloads by file type"
zenus_os "show system memory usage"
zenus_os "find processes named python"
zenus_os "read ~/Documents/notes.txt"
```

### Dry-Run Mode

Preview what Zenus will do without executing:

```bash
zenus_os --dry-run "delete all tmp files"

# In interactive mode:
zenus > --dry-run organize downloads
```

## Available Tools

### FileOps
- `scan`: List directory contents
- `mkdir`: Create directories
- `move`: Move files
- `write_file`: Create files with content
- `touch`: Create empty files

### TextOps
- `read`: Read text file contents
- `write`: Write text file
- `append`: Append to text file
- `search`: Search for pattern in file
- `count_lines`: Count lines in file
- `head`: Show first N lines
- `tail`: Show last N lines

### SystemOps
- `disk_usage`: Show disk space
- `memory_info`: Show memory usage
- `cpu_info`: Show CPU usage
- `list_processes`: List top processes
- `uptime`: Show system uptime

### ProcessOps
- `find_by_name`: Find processes by name
- `info`: Get process details
- `kill`: Terminate processes (requires confirmation)

## Memory System

Zenus learns from usage through three memory layers:

- **Session Memory**: Current context (paths, references)
- **World Model**: Learned preferences and frequent paths
- **Intent History**: Complete audit trail

Memory stored in `~/.zenus/`:
- `logs/` - Execution audit logs (JSONL)
- `history/` - Intent history
- `world_model.json` - Learned knowledge

## Development

### Running Tests

```bash
pytest
# or
pytest -v  # verbose
pytest --cov  # with coverage
```

### Project Structure

```
zenus_os/
├── src/
│   ├── brain/          # Intent translation and planning
│   ├── cli/            # Command routing and orchestration
│   ├── tools/          # Available operations
│   ├── memory/         # Session, world model, history
│   ├── safety/         # Safety policies
│   ├── sandbox/        # Sandbox enforcement
│   ├── audit/          # Audit logging
│   └── zenusd/         # Main entry point
├── tests/              # Test suite
├── docs/               # Documentation
└── README.md
```

## Architecture

Zenus operates through a formal Intent IR (Intermediate Representation):

```
User Input → LLM → Intent IR → Validation → Adaptive Execution → Results
```

Every operation is:
- **Validated**: Schema-checked before execution
- **Logged**: Complete audit trail
- **Sandboxed**: Path and resource constraints
- **Adaptive**: Auto-retry on transient failures

## Comparison with OpenClaw

| Feature | OpenClaw | Zenus OS |
|---------|----------|----------|
| Philosophy | Flexible agent | Deterministic OS layer |
| Safety | Plugin marketplace | Formal contracts |
| Memory | Vector + markdown | Three-layer system |
| Execution | Async messaging | Validated pipeline |
| Focus | Task automation | System control |

Zenus prioritizes correctness and safety over flexibility.

## Documentation

- [Architecture Overview](docs/architecture/01-system-overview.md)
- [Intent IR Specification](docs/architecture/02-intent-ir.md)
- [Adaptive Execution](docs/architecture/03-adaptive-execution.md)
- [Memory System](docs/architecture/04-memory-system.md)
- [Sandboxing](docs/architecture/05-sandboxing.md)
- [Development Progress](docs/PROGRESS.md)
- [Current Status](docs/STATUS.md)

## Roadmap

- ✅ Foundation: CLI, Intent IR, Tools, Memory, Sandbox
- ✅ Integration: Memory + Sandbox + Orchestrator
- 🔄 Next: Voice interface (Whisper + TTS)
- 📋 Future: Vector search, learning, custom distro

## License

[To be determined]

## Contributing

[To be determined]

---

**Zenus OS: Computing should understand intent, not just commands.** ⚡
