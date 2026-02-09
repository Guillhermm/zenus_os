# Zenus OS

Zenus OS is a voice-first, AI-mediated operating system layer that replaces traditional user interfaces with intent-based interaction and bounded autonomy.

This is, a full operating systems that can be controlled by voice, where AI:

- Understands complex user intent.
- Plans and performs operations autonomously.
- Interacts with system APIs to get things done.
- Can talk back, ask clarifying questions, and learn from user behavior.

Although there are research prototypes already in place, still there is no full voice controlled OS consumer-ready for end users. With this project, we aim to create voice-first AI assisted OS that is not just reactive, but autonomous, context aware, and capable of executing complex tasks based on natural language instructions.

What would be the impacts on user experience? Should we build a new concept of user interface, or the new concept is totally user customizable?

Discussions over possible impacts and needed technology and scientific improvements can be found **[here](./docs/advances.md)**.

## 1. Prototype

### 1.1. System Architecture

#### 1.1.1. AI Assistant Layer

- LLM (Large Language Model) that interprets intent.
- Is there another better way than LLM, more efficient that does not consume much from CPU, for the system core?
- Options to consider are GPT, Mistral, LLaMa (local or cloud?).
- Autonomous agent capabilities?
- Maybe we can build this as a modular backend that sits between voice and the system APIs?

#### 1.1.2. Voice Interface Layer

- Voice-to-text: Whisper (local), Deepgram, or Google SST.
- Text-to-voice: ElevenLabs, Piper, or built-in TTS engines.

Natural conversion loop:

```
Wake word → voice capture → intent → action → AI response → spoken feedback
```

#### 1.1.3. OS Shell/Control Layer

This layer connects AI actions to real system commands.

**Options:**

- Build a custom Linux distro with voice + AI shell (desirable by the end of the prototype).
- Overlay it on existing OS (like a custom desktop environment).
- Use an existing OS but control it fully via APIs/scripts

Would we be able to fully control OS in second and third approaches?

#### 1.1.4. Autonomous Task Engine

AI should not just follow single commands, it should:

- Decompose tasks.
- Ask for clarification when needed.
- Execute subtasks step by step.
- Adapt to errors or unexpected results.

#### 1.1.5. Security and Permissions

A voice controlled OS must have strong authentication, especially for destructive actions.

**Options:**

- Voice ID or wake word auth.
- Role-based task restrictions.
- Confirmation layers for sensitive operations.

We should be able to "translate" voice into a single id, combined with passphrase, for authentication. Passwords might be fallback. Instead of wake word, OS might recognize user voice timbre.

## 2. Use Case Scenarios Examples

### 2.1. Daily Tasks

"Check my calendar and tell me what's coming up"

"Organize my downloads by file type and delete duplicates"

"Summarize latest posts from my social media"

### 2.2. Autonomous Ops

"Find the 5 largest files on my system, back them up, and free up space"

"Setup a new dev environment with Python, Docker, and VS Code"

### 2.3. Developer Mode

"Create a Python script that monitors CPU usage and logs"

"Download latest stable release of MySQL and configure it"

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
# Edit .env with your API keys
```

### System-Wide Alias (Recommended)

To run `zenus_os` from anywhere without manual activation:

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
zenus > Organize my Downloads folder by file type
zenus > Show disk usage
zenus > List top 10 processes
zenus > exit
```

### Direct Execution

Run commands directly from your shell:

```bash
zenus_os "organize my downloads by file type"
zenus_os "show system memory usage"
zenus_os "find processes named python"
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
│   ├── safety/         # Safety policies
│   ├── audit/          # Audit logging
│   └── zenusd/         # Main entry point
├── tests/              # Test suite
├── docs/               # Documentation
└── README.md
```

## Logs

All operations are logged to `~/.zenus/logs/` in JSONL format for audit and debugging.