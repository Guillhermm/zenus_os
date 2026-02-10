# Troubleshooting Guide

## Installation Issues

### Ollama: "could not connect to ollama app"

**Problem:** Ollama service isn't running after installation.

**Solution:**
```bash
# Start Ollama service manually
ollama serve
```

Then in a new terminal, run the installer again:
```bash
./install.sh
```

**Permanent fix (Linux with systemd):**
```bash
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Ollama: Model download fails

**Problem:** Network issues or insufficient disk space.

**Solution:**
1. Check disk space: `df -h`
2. Check connection: `curl -I https://ollama.com`
3. Retry: `ollama pull phi3:mini`

## Runtime Errors

### "Plan execution failed"

**Possible causes:**
1. File/path doesn't exist
2. Permission denied
3. Syntax error in command

**Debug:**
```bash
zenus > status          # Check system status
zenus > memory stats    # Check memory state
```

Try with `--dry-run` first:
```bash
zenus > --dry-run <your command>
```

### "Failed to understand command"

**Possible causes:**
1. LLM backend not responding
2. Ambiguous command
3. API key invalid

**Solution:**
- Check LLM backend: `zenus status`
- Verify API key in `.env`
- For Ollama: `curl http://localhost:11434/api/tags`
- Be more specific in command

### "Unexpected error: ..."

**Debug steps:**
1. Check logs: `~/.zenus/logs/session_*.jsonl`
2. Run with Python directly to see full traceback:
   ```bash
   source .venv/bin/activate
   python src/main.py
   ```
3. Check GitHub issues for similar errors

## LLM Backend Issues

### OpenAI: "Invalid API key"

**Solution:**
1. Get API key: https://platform.openai.com/api-keys
2. Update `.env`:
   ```
   ZENUS_LLM=openai
   OPENAI_API_KEY=sk-...
   ```
3. Restart Zenus

### DeepSeek: Connection timeout

**Solution:**
1. Check API endpoint in `.env`
2. Verify API key is valid
3. Test connection:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" \
        https://api.deepseek.com/v1/models
   ```

### Ollama: Slow responses

**Possible causes:**
1. Model too large for RAM
2. CPU-only inference
3. System under load

**Solutions:**
- Use smaller model: `ollama pull llama3.2:3b`
- Close other applications
- Check system resources: `zenus > show memory usage`

## Memory Issues

### "SessionMemory object has no attribute..."

**Solution:** This is a version mismatch. Update:
```bash
zenus > update
```

Or manually:
```bash
git pull
pip install --upgrade -r requirements.txt
```

### Memory not learning/forgetting paths

**Check:**
```bash
zenus > memory stats
```

**If empty, memory might not be enabled:**
- Check orchestrator initialization
- Verify `~/.zenus/` directory exists and is writable

## Performance Issues

### Slow intent translation

**For cloud LLMs:**
- Network latency (normal: 1-3s)
- Try local Ollama instead

**For Ollama:**
- First run loads model (10-30s)
- Subsequent runs faster (1-5s)
- Use smaller model if too slow

### High CPU usage

**If using Ollama:**
- Normal during inference
- Use `nice` or `cpulimit`:
  ```bash
  sudo cpulimit -e ollama -l 50
  ```

## Getting Help

1. **Check logs:** `~/.zenus/logs/`
2. **Search issues:** GitHub issues page
3. **Ask on Discord:** [link]
4. **Report bug:**
   ```bash
   # Include:
   - Zenus version (zenus status)
   - OS version (uname -a)
   - Error message
   - Steps to reproduce
   ```

## Common Fixes

### Reset everything
```bash
# Clear memory
zenus > memory clear

# Remove logs
rm -rf ~/.zenus/logs/*

# Restart fresh
```

### Reinstall dependencies
```bash
./install.sh  # Or:
source .venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

### Check Python version
```bash
python3 --version  # Should be 3.10+
```

If older, install Python 3.10+:
```bash
sudo apt install python3.10 python3.10-venv
python3.10 -m venv .venv
```
