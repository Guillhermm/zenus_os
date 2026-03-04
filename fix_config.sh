#!/bin/bash
# Quick fix for config.yaml fallback settings

CONFIG_FILE="$(cd "$(dirname "$0")" && pwd)/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "Current config.yaml settings:"
echo "─────────────────────────────"
grep -A3 "^llm:" "$CONFIG_FILE" | head -4
echo ""
grep -A5 "^fallback:" "$CONFIG_FILE"
echo "─────────────────────────────"
echo ""

# Get primary provider from config
PRIMARY=$(grep "provider:" "$CONFIG_FILE" | head -1 | awk '{print $2}')
echo "Primary LLM: $PRIMARY"
echo ""

read -p "Disable fallback and ONLY use $PRIMARY? (y/N): " disable

if [ "$disable" = "y" ] || [ "$disable" = "Y" ]; then
    echo ""
    echo "Updating config.yaml..."
    
    # Create a Python script to update YAML properly
    python3 << PYEOF
import sys
try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml", "-q"])
    import yaml

config_file = "$CONFIG_FILE"

with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

# Get primary provider
primary = config['llm']['provider']

# Disable fallback and set providers to only primary
config['fallback']['enabled'] = False
config['fallback']['providers'] = [primary]

with open(config_file, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print(f"✓ Fallback disabled")
print(f"✓ Providers set to: [{primary}]")
PYEOF
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Updated config.yaml:"
        echo "─────────────────────────────"
        grep -A5 "^fallback:" "$CONFIG_FILE"
        echo "─────────────────────────────"
        echo ""
        echo "✅ Done! Zenus will now ONLY use $PRIMARY"
    else
        echo ""
        echo "❌ Automatic update failed. Manual edit needed:"
        echo "   nano $CONFIG_FILE"
        echo ""
        echo "Change fallback section to:"
        echo "  fallback:"
        echo "    enabled: false"
        echo "    providers:"
        echo "      - $PRIMARY"
    fi
else
    echo "No changes made"
fi

echo ""
