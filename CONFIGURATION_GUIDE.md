# Configuration Guide

**Status**: ✅ Complete | **Phase**: Foundation Hardening  
**Version**: 0.5.1

Modern configuration system with YAML support, profiles, and hot-reload.

---

## 🎯 Overview

Zenus uses a **two-tier configuration system**:
1. **Configuration** (`config.yaml`) - Settings, features, profiles
2. **Secrets** (`.env`) - API keys, sensitive data

**Benefits:**
- ✅ Type-safe (Pydantic validation)
- ✅ Profile support (dev/staging/production)
- ✅ Hot-reload (instant changes)
- ✅ Secrets separate from config
- ✅ Well-organized structure

---

## 📂 File Locations

### Config File
```
~/.zenus/config.yaml        # Recommended
./zenus.yaml                # Project-specific
$ZENUS_CONFIG               # Custom location
```

### Secrets File
```
~/.zenus/.env              # Recommended
./.env                     # Project-specific
```

---

## ⚙️ Configuration Structure

### Complete Example

```yaml
# config.yaml
version: "0.5.1"
profile: dev  # dev, staging, production

llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.7
  timeout_seconds: 30

fallback:
  enabled: true
  providers:
    - anthropic
    - deepseek
    - rule_based

circuit_breaker:
  enabled: true
  failure_threshold: 5
  timeout_seconds: 60.0
  success_threshold: 2

retry:
  enabled: true
  max_attempts: 3
  initial_delay_seconds: 1.0
  max_delay_seconds: 30.0
  exponential_base: 2.0
  jitter: true

cache:
  enabled: true
  ttl_seconds: 3600
  max_size_mb: 100

safety:
  sandbox_enabled: true
  max_file_size_mb: 100
  allowed_paths:
    - "."
  blocked_commands:
    - "rm -rf /"

monitoring:
  enabled: true
  check_interval_seconds: 300
  disk_warning_threshold: 0.8
  disk_critical_threshold: 0.9
  cpu_warning_threshold: 0.8
  memory_warning_threshold: 0.85

features:
  voice_interface: false
  multi_agent: false
  proactive_monitoring: true
  tree_of_thoughts: true
  prompt_evolution: true
  goal_inference: true
  self_reflection: true
  data_visualization: true

profiles:
  dev:
    llm:
      temperature: 0.9
    safety:
      sandbox_enabled: false
  
  production:
    llm:
      temperature: 0.5
    safety:
      sandbox_enabled: true
```

---

## 🎭 Profile System

### Available Profiles

**dev** (Development)
- More creative (higher temperature)
- Shorter cache TTL
- Sandbox disabled for convenience
- All features enabled

**staging** (Staging)
- Balanced settings
- Medium cache TTL
- Sandbox enabled
- Stable features only

**production** (Production)
- Conservative (lower temperature)
- Longer cache TTL
- Sandbox always enabled
- Experimental features disabled

### Using Profiles

```bash
# Set via environment
export ZENUS_PROFILE=production
zenus "deploy app"

# Or inline
ZENUS_PROFILE=dev zenus "test feature"

# Check current profile
zenus config profile
```

---

## 🔧 Configuration Sections

### LLM Configuration

```yaml
llm:
  provider: anthropic  # anthropic, openai, deepseek, ollama
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.7     # 0.0-1.0 (creativity)
  timeout_seconds: 30
```

**Providers:**
- `anthropic` - Claude (best quality)
- `openai` - GPT-4 (fast, good)
- `deepseek` - DeepSeek (cheap, fast)
- `ollama` - Local (offline, private)

### Fallback Chain

```yaml
fallback:
  enabled: true
  providers:
    - anthropic      # Try first (best)
    - deepseek       # Try second (fast)
    - rule_based     # Always works (fallback)
```

### Circuit Breaker

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 5        # Open after 5 failures
  timeout_seconds: 60.0       # Try reset after 60s
  success_threshold: 2        # Close after 2 successes
```

### Retry Logic

```yaml
retry:
  enabled: true
  max_attempts: 3
  initial_delay_seconds: 1.0  # Start with 1s
  max_delay_seconds: 30.0     # Cap at 30s
  exponential_base: 2.0       # Double each time
  jitter: true                # Add randomness
```

### Cache

```yaml
cache:
  enabled: true
  ttl_seconds: 3600           # 1 hour
  max_size_mb: 100            # 100MB max
```

### Safety & Sandbox

```yaml
safety:
  sandbox_enabled: true
  max_file_size_mb: 100
  allowed_paths:
    - "."
    - "/home/user/projects"
  blocked_commands:
    - "rm -rf /"
    - "dd if="
```

### Proactive Monitoring

```yaml
monitoring:
  enabled: true
  check_interval_seconds: 300     # Every 5 minutes
  disk_warning_threshold: 0.8     # Warn at 80%
  disk_critical_threshold: 0.9    # Critical at 90%
  cpu_warning_threshold: 0.8
  memory_warning_threshold: 0.85
```

### Feature Flags

```yaml
features:
  voice_interface: false         # Experimental
  multi_agent: false             # Experimental
  proactive_monitoring: true     # Stable
  tree_of_thoughts: true         # Stable
  prompt_evolution: true         # Stable
  goal_inference: true           # Stable
  self_reflection: true          # Stable
  data_visualization: true       # Stable
```

---

## 🔒 Secrets Management

### .env File

```bash
# ~/.zenus/.env

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI (GPT)
OPENAI_API_KEY=sk-your-key-here
OPENAI_API_BASE_URL=https://api.openai.com/v1

# DeepSeek
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_API_BASE_URL=https://api.deepseek.com

# Ollama (Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini

# Custom
ZENUS_API_KEY=your-custom-key
```

### Programmatic Access

```python
from zenus_core.config import get_secrets

secrets = get_secrets()

# Get specific secret
api_key = secrets.get("ANTHROPIC_API_KEY")

# Get LLM API key
api_key = secrets.get_llm_api_key("anthropic")

# Check if secret exists
if secrets.has_secret("OPENAI_API_KEY"):
    # Use OpenAI

# Mask for logging
masked = secrets.mask_secret(api_key)
print(f"Using key: {masked}")  # sk-ant-***xyz
```

---

## 🔄 Hot-Reload

Config changes apply **instantly** without restart!

```bash
# Start Zenus
zenus

# Edit config (in another terminal)
vim ~/.zenus/config.yaml
# Change temperature: 0.7 -> 0.9
# Save

# Next command uses new temperature!
# No restart needed! 🎉
```

**How it works:**
- Uses `watchdog` to monitor config file
- Reloads automatically on changes
- Validates schema before applying
- Falls back to old config on errors

---

## 🛠️ CLI Commands

```bash
# Show current config
zenus config show

# Show current profile
zenus config profile

# Validate config
zenus config validate

# Reload config (manual)
zenus config reload

# Show config file path
zenus config path

# Create default config
zenus config init
```

---

## 💻 Programmatic Usage

### Load Configuration

```python
from zenus_core.config import get_config

# Get config (auto-loads)
config = get_config()

# Access settings
print(config.llm.provider)      # "anthropic"
print(config.llm.temperature)   # 0.7
print(config.features.tree_of_thoughts)  # True

# Check profile
if config.is_production():
    # Production-specific logic
    pass

# Reload manually
from zenus_core.config import reload_config
config = reload_config()
```

### Save Configuration

```python
from zenus_core.config import get_config, ConfigLoader

config = get_config()

# Modify config
config.llm.temperature = 0.9
config.features.multi_agent = True

# Save (writes to file)
loader = ConfigLoader()
loader.save_config(config)
```

---

## 🎯 Best Practices

### ✅ DO:
- Use `production` profile in production
- Keep secrets in `.env` files
- Use profiles for different environments
- Enable sandbox in production
- Set restrictive `allowed_paths`
- Version control `config.yaml.example`

### ❌ DON'T:
- Put API keys in `config.yaml`
- Commit `.env` files
- Use dev config in production
- Disable sandbox in production
- Share secrets across environments

---

## 🐛 Troubleshooting

### Config Not Found

```bash
# Check search paths
ls -la ~/.zenus/config.yaml
ls -la ./zenus.yaml

# Create default
zenus config init
```

### Invalid Config

```bash
# Validate
zenus config validate

# Check errors
zenus config check

# Use default if broken
mv ~/.zenus/config.yaml ~/.zenus/config.yaml.backup
zenus config init
```

### Hot-Reload Not Working

```bash
# Install watchdog
pip install watchdog

# Check if installed
python -c "import watchdog; print('✓ Installed')"

# Restart Zenus
```

### Secrets Not Loading

```bash
# Check .env location
ls -la ~/.zenus/.env
ls -la ./.env

# Check syntax
cat ~/.zenus/.env

# Test loading
python -c "
from zenus_core.config import get_secrets
secrets = get_secrets()
print(secrets.list_available())
"
```

---

## 📊 Configuration Priority

Settings are loaded in this order (later overrides earlier):

1. **Default values** (in schema)
2. **Base config** (config.yaml root level)
3. **Profile overrides** (config.yaml profiles section)
4. **Environment variables** (ZENUS_*)
5. **Command-line flags** (--temperature, etc.)

---

## 🚀 Examples

### Development Setup

```yaml
# ~/.zenus/config.yaml
profile: dev

llm:
  temperature: 0.9  # More creative

safety:
  sandbox_enabled: false  # Convenience

cache:
  ttl_seconds: 300  # 5 minutes (shorter)

features:
  voice_interface: true  # Experimental OK
  multi_agent: true
```

### Production Setup

```yaml
# ~/.zenus/config.yaml
profile: production

llm:
  temperature: 0.5  # Conservative

safety:
  sandbox_enabled: true  # Always
  allowed_paths:
    - "/app/workspace"

cache:
  ttl_seconds: 3600  # 1 hour

features:
  voice_interface: false  # Stable only
  multi_agent: true
```

---

**See Also:**
- [CONFIG_MIGRATION_GUIDE.md](CONFIG_MIGRATION_GUIDE.md) - Migrate from .env
- [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) - Circuit breakers & retries
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing configuration
