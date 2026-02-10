# Configuration Guide

## Environment Variables

Zenus OS configuration is managed through the `.env` file in the project root.

### File Format

**Important:** Each variable must be on its own line with no spaces around `=`:

✅ **Correct:**
```
ZENUS_LLM=ollama
OLLAMA_MODEL=phi3:mini
```

❌ **Incorrect:**
```
ZENUS_LLM = ollama          # Spaces around =
ZENUS_LLMollamaOLLAMA_MODEL # Missing newline
```

### LLM Backend Configuration

#### Ollama (Local, FREE)

**Recommended for:**
- Privacy-conscious users
- Offline usage
- No API costs

**Requirements:**
- 4-16GB RAM
- 5-10GB disk space for models

**Configuration:**
```bash
ZENUS_LLM=ollama
OLLAMA_MODEL=phi3:mini
```

**Available models:**
- `phi3:mini` - 3.8GB, fast, recommended
- `llama3.2:3b` - 2GB, lightweight
- `qwen2.5:3b` - 2.3GB, good reasoning
- `mistral:7b` - 4.1GB, powerful

**Start Ollama:**
```bash
# Background service
ollama serve

# Or with systemd
sudo systemctl start ollama
```

#### OpenAI (Cloud)

**Recommended for:**
- Best accuracy
- Fastest response times

**Configuration:**
```bash
ZENUS_LLM=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE_URL=https://api.openai.com/v1  # Optional
```

**Get API Key:**
1. Visit https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to `.env`

**Cost:** ~$0.001 per command (very cheap)

#### DeepSeek (Cloud)

**Recommended for:**
- Lower cost than OpenAI
- Good performance

**Configuration:**
```bash
ZENUS_LLM=deepseek
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_API_BASE_URL=https://api.deepseek.com  # Optional
LLM_MODEL=deepseek-chat  # Optional
LLM_TOKENS=8192  # Optional
```

**Get API Key:**
1. Visit https://platform.deepseek.com
2. Create account and get API key
3. Copy to `.env`

## Memory Configuration

Memory is enabled by default and stores data in `~/.zenus/`:

```
~/.zenus/
├── logs/              # Audit logs (JSONL)
├── history/           # Intent history
└── world_model.json   # Learned knowledge
```

**Disable memory** (not recommended):
Edit `src/cli/orchestrator.py`:
```python
orchestrator = Orchestrator(use_memory=False)
```

**Clear memory:**
```bash
zenus > memory clear     # Clear session only
rm -rf ~/.zenus/         # Clear everything
```

## Advanced Configuration

### Custom LLM Endpoint

For OpenAI-compatible endpoints:
```bash
ZENUS_LLM=openai
OPENAI_API_KEY=your-key
OPENAI_API_BASE_URL=https://your-endpoint.com/v1
```

### Sandbox Configuration

Sandbox is enabled by default. To customize paths, edit:
`src/sandbox/constraints.py`

### Logging

Logs stored at: `~/.zenus/logs/session_*.jsonl`

**Disable logging** (not recommended):
Edit `src/cli/orchestrator.py` and remove logger initialization.

## Troubleshooting Configuration

### Check current configuration:
```bash
zenus > status
```

### Verify .env is loaded:
```bash
cd ~/projects/zenus_os
source .venv/bin/activate
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('LLM:', os.getenv('ZENUS_LLM'))"
```

### Common issues:

**"ValueError: invalid literal for int()"**
- Check `.env` format (no extra characters)
- Ensure each variable on separate line
- Re-run: `./install.sh`

**"Failed to understand command"**
- Verify LLM backend is configured
- For Ollama: Check `ollama serve` is running
- For cloud: Verify API key is valid

**Changes not taking effect:**
- Restart Zenus after editing `.env`
- Check for typos in variable names (case-sensitive)

## Example Configurations

### Minimum (Ollama only):
```bash
ZENUS_LLM=ollama
OLLAMA_MODEL=phi3:mini
```

### Full OpenAI:
```bash
ZENUS_LLM=openai
OPENAI_API_KEY=sk-...
OPENAI_API_BASE_URL=https://api.openai.com/v1
```

### Multiple backends (switch by editing ZENUS_LLM):
```bash
# Active backend
ZENUS_LLM=ollama

# Ollama config
OLLAMA_MODEL=phi3:mini

# OpenAI config (commented out)
# OPENAI_API_KEY=sk-...

# DeepSeek config (commented out)
# DEEPSEEK_API_KEY=sk-...
```

To switch: change `ZENUS_LLM=` value and restart Zenus.
