#!/bin/bash
# Quick fix for config.yaml fallback settings

CONFIG_FILE="$(cd "$(dirname "$0")" && pwd)/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "Current fallback settings:"
grep -A5 "fallback:" "$CONFIG_FILE"
echo ""

read -p "Disable fallback and only use Anthropic? (y/N): " disable

if [ "$disable" = "y" ] || [ "$disable" = "Y" ]; then
    # Use Python to properly edit YAML
    python3 << PYEOF
import yaml

config_file = "$CONFIG_FILE"

with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

# Disable fallback
config['fallback']['enabled'] = False
config['fallback']['providers'] = ['anthropic']

with open(config_file, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print("✓ Fallback disabled - only Anthropic will be used")
PYEOF
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Updated fallback settings:"
        grep -A5 "fallback:" "$CONFIG_FILE"
    else
        echo "Error updating config. Manual edit required:"
        echo "  nano $CONFIG_FILE"
        echo ""
        echo "Change:"
        echo "  enabled: false"
        echo "  providers:"
        echo "    - anthropic"
    fi
else
    echo "No changes made"
fi
