# Zenus OS Troubleshooting

Common issues and their solutions.

---

## Module Not Found Errors

### Error: `ModuleNotFoundError: No module named 'anthropic'`

**Symptom**: After pulling updates, Zenus fails with:
```
ModuleNotFoundError: No module named 'anthropic'
```

Even though `anthropic` is in `poetry.lock`.

**Cause**: The CLI/TUI packages use their own virtual environments. Even though they depend on core, Poetry doesn't automatically install core's dependencies into CLI/TUI environments.

**Solution**: 

This issue was fixed in commit `[upcoming]`. After pulling the latest updates, run:

```bash
cd ~/projects/zenus_os
git pull
./update.sh
```

The CLI and TUI packages now explicitly include LLM provider dependencies (anthropic, openai) so they're always available at runtime.

**Manual fix** (if you're on an older version):

```bash
cd packages/cli
poetry add anthropic@^0.47.0 openai@^1.0.0
cd ../tui
poetry add anthropic@^0.47.0 openai@^1.0.0
```

### Error: `ModuleNotFoundError: No module named 'zenus_cli'`

**Symptom**: Running `zenus` command fails with module not found.

**Cause**: CLI package not installed.

**Solution**:

```bash
cd packages/cli
poetry install
```

### Error: `ModuleNotFoundError: No module named 'zenus_core'`

**Symptom**: Any zenus command fails, can't find core.

**Cause**: Core package not installed (all other packages depend on it).

**Solution**: Install core first, then others:

```bash
cd packages/core && poetry install
cd ../cli && poetry install
cd ../tui && poetry install
```

---

## LLM Configuration Issues

### Error: `ANTHROPIC_API_KEY not set`

**Symptom**: Zenus fails immediately when trying to use Claude.

**Cause**: Missing or incorrect `.env` configuration.

**Solution**: Edit `.env` in the project root:

```bash
ZENUS_LLM=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Get your API key from: https://console.anthropic.com/account/keys

### Error: `OPENAI_API_KEY not set`

**Symptom**: Zenus fails when using OpenAI backend.

**Solution**: Edit `.env`:

```bash
ZENUS_LLM=openai
OPENAI_API_KEY=sk-your-actual-key-here
```

### Error: `Connection refused` when using Ollama

**Symptom**: Can't connect to Ollama service.

**Solution**: Start Ollama:

```bash
# Option 1: Systemd service
sudo systemctl start ollama

# Option 2: Manual
ollama serve
```

Then verify it's running:

```bash
curl http://localhost:11434/api/tags
```

---

## Poetry Issues

### Error: `poetry.lock is out of sync with pyproject.toml`

**Symptom**: Running poetry commands fails with lock file mismatch.

**Solution**: Regenerate the lock file:

```bash
cd packages/core  # or cli, or tui
poetry lock
poetry install
```

### Error: `poetry: command not found`

**Symptom**: Poetry isn't installed.

**Solution**: Install Poetry:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

Add to your `~/.bashrc` for persistence:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## Alias Issues

### Error: `zenus: command not found`

**Symptom**: Shell doesn't recognize `zenus` command.

**Solution**: Source your bashrc:

```bash
source ~/.bashrc
```

If that doesn't work, check aliases exist:

```bash
grep zenus ~/.bashrc
```

Should show:
```
alias zenus='/path/to/zenus_os/zenus.sh'
alias zenus-tui='/path/to/zenus_os/zenus-tui.sh'
```

If not, re-run the installer:

```bash
./install.sh
```

### Error: Aliases point to wrong directory

**Symptom**: Aliases work but fail to find the scripts.

**Solution**: Update aliases manually:

```bash
# Remove old aliases
sed -i '/alias zenus=/d' ~/.bashrc
sed -i '/alias zenus-tui=/d' ~/.bashrc

# Add new ones with correct path
echo "alias zenus='$(pwd)/zenus.sh'" >> ~/.bashrc
echo "alias zenus-tui='$(pwd)/zenus-tui.sh'" >> ~/.bashrc

source ~/.bashrc
```

---

## Git/Update Issues

### After `git pull`, things break

**Symptom**: After pulling updates, various module errors occur.

**Solution**: Always run update script after pulling:

```bash
git pull
./update.sh
```

This ensures all dependencies are installed.

---

## Permission Issues

### Error: `Permission denied` running scripts

**Symptom**: Can't execute `./zenus.sh` or `./install.sh`

**Solution**: Make scripts executable:

```bash
chmod +x zenus.sh zenus-tui.sh install.sh update.sh
```

---

## Common Workflow

### Fresh Installation

```bash
git clone <repo-url>
cd zenus_os
./install.sh
source ~/.bashrc
zenus help
```

### Updating Existing Installation

```bash
cd ~/projects/zenus_os
git pull
./update.sh
zenus help  # Test it works
```

### Switching LLM Backend

Edit `.env` and change `ZENUS_LLM`:

```bash
# From this:
ZENUS_LLM=ollama

# To this:
ZENUS_LLM=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

No reinstall needed, just change config.

---

## Still Having Issues?

1. Check you're in the right directory: `pwd` should show `zenus_os`
2. Check Poetry is working: `poetry --version`
3. Check Python version: `python3 --version` (should be 3.10+)
4. Try a clean reinstall:

```bash
cd ~/projects/zenus_os

# Clean virtual environments
rm -rf packages/*/poetry.lock
rm -rf packages/*/.venv

# Reinstall everything
./install.sh
```

5. Check the logs in `~/.zenus/logs/` for detailed error messages

---

## Quick Diagnostics

Run this to check your setup:

```bash
cd ~/projects/zenus_os

echo "=== Python ==="
python3 --version

echo "=== Poetry ==="
poetry --version

echo "=== Core Package ==="
cd packages/core && poetry show | grep anthropic

echo "=== Aliases ==="
grep zenus ~/.bashrc

echo "=== Environment ==="
cat .env | grep ZENUS_LLM
```

This will show if Poetry, Python, dependencies, and config are correct.