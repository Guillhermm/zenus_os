#!/bin/bash
set -e

echo "╔════════════════════════════════════╗"
echo "║   Zenus OS Installation Script     ║"
echo "╚════════════════════════════════════╝"
echo ""

# Get absolute path to project
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo "Installing Python 3..."
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check/Install Poetry
echo "════════════════════════════════════"
echo "  Checking Poetry..."
echo "════════════════════════════════════"
echo ""

if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing..."
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Add poetry to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "✓ Poetry installed: $(poetry --version)"
else
    echo "✓ Poetry already installed: $(poetry --version)"
fi

echo ""
echo "════════════════════════════════════"
echo "  Installing Zenus Packages..."
echo "════════════════════════════════════"
echo ""

# Install core package first
echo "→ Installing zenus-core..."
cd "$PROJECT_DIR/packages/core"
poetry install --no-interaction --quiet
echo "✓ zenus-core installed"

# Install CLI package
echo "→ Installing zenus-cli..."
cd "$PROJECT_DIR/packages/cli"
poetry install --no-interaction --quiet
echo "✓ zenus-cli installed"

# Install TUI package
echo "→ Installing zenus-tui..."
cd "$PROJECT_DIR/packages/tui"
poetry install --no-interaction --quiet
echo "✓ zenus-tui installed"

cd "$PROJECT_DIR"

echo ""
echo "════════════════════════════════════"
echo "  LLM Configuration"
echo "════════════════════════════════════"
echo ""

# Config directory
CONFIG_DIR="$HOME/.zenus"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
SECRETS_FILE="$CONFIG_DIR/.env"

# Create config directory
mkdir -p "$CONFIG_DIR"

# Check if already configured
if [ -f "$CONFIG_FILE" ] && [ -f "$SECRETS_FILE" ]; then
    echo "✓ Configuration already exists"
    echo "  Config: $CONFIG_FILE"
    echo "  Secrets: $SECRETS_FILE"
    echo ""
    read -p "Reconfigure? (y/N): " reconfigure
    if [ "$reconfigure" != "y" ] && [ "$reconfigure" != "Y" ]; then
        echo "Skipping configuration"
        # Jump to aliases section
        skip_config=true
    fi
fi

if [ "$skip_config" != "true" ]; then
    # Copy base config
    cp "$PROJECT_DIR/config.yaml.example" "$CONFIG_FILE"
    
    # Create/clear secrets file
    > "$SECRETS_FILE"
    chmod 600 "$SECRETS_FILE"
    
    echo "Choose your PRIMARY LLM backend:"
    echo ""
    echo "1) Anthropic Claude (recommended for complex tasks)"
    echo "   - Excellent reasoning and code generation"
    echo "   - claude-3-5-sonnet recommended"
    echo "   - Costs ~\$0.003 per command"
    echo ""
    echo "2) DeepSeek (good balance of performance and cost)"
    echo "   - Strong code capabilities"
    echo "   - Very affordable (~\$0.0003 per command)"
    echo ""
    echo "3) OpenAI (fast and reliable)"
    echo "   - Costs ~\$0.001 per command"
    echo ""
    echo "4) Ollama (Local, FREE - privacy-first)"
    echo "   - Runs on your hardware"
    echo "   - No API key needed"
    echo "   - Requires 4-16GB RAM"
    echo ""

    read -p "Enter choice [1-4]: " primary_choice

    PRIMARY_PROVIDER=""
    PRIMARY_MODEL=""

    case $primary_choice in
        1)
            PRIMARY_PROVIDER="anthropic"
            echo ""
            read -sp "Enter your Anthropic API key: " api_key
            echo ""
            echo "ANTHROPIC_API_KEY=$api_key" >> "$SECRETS_FILE"
            
            echo ""
            echo "Choose Claude model:"
            echo "1) claude-3-5-sonnet-20241022 (recommended)"
            echo "2) claude-3-5-haiku-20241022 (faster, cheaper)"
            echo "3) claude-3-opus-20240229 (most capable)"
            
            read -p "Enter choice [1-3]: " model_choice
            
            case $model_choice in
                1) PRIMARY_MODEL="claude-3-5-sonnet-20241022" ;;
                2) PRIMARY_MODEL="claude-3-5-haiku-20241022" ;;
                3) PRIMARY_MODEL="claude-3-opus-20240229" ;;
                *) PRIMARY_MODEL="claude-3-5-sonnet-20241022" ;;
            esac
            
            echo "✓ Anthropic configured with $PRIMARY_MODEL"
            ;;
            
        2)
            PRIMARY_PROVIDER="deepseek"
            echo ""
            read -sp "Enter your DeepSeek API key: " api_key
            echo ""
            echo "DEEPSEEK_API_KEY=$api_key" >> "$SECRETS_FILE"
            PRIMARY_MODEL="deepseek-chat"
            
            echo "✓ DeepSeek configured"
            ;;
            
        3)
            PRIMARY_PROVIDER="openai"
            echo ""
            read -sp "Enter your OpenAI API key: " api_key
            echo ""
            echo "OPENAI_API_KEY=$api_key" >> "$SECRETS_FILE"
            
            echo ""
            echo "Choose OpenAI model:"
            echo "1) gpt-4o (recommended)"
            echo "2) gpt-4o-mini (faster, cheaper)"
            echo "3) gpt-4-turbo"
            
            read -p "Enter choice [1-3]: " model_choice
            
            case $model_choice in
                1) PRIMARY_MODEL="gpt-4o" ;;
                2) PRIMARY_MODEL="gpt-4o-mini" ;;
                3) PRIMARY_MODEL="gpt-4-turbo" ;;
                *) PRIMARY_MODEL="gpt-4o" ;;
            esac
            
            echo "✓ OpenAI configured with $PRIMARY_MODEL"
            ;;
            
        4)
            PRIMARY_PROVIDER="ollama"
            echo ""
            echo "Setting up Ollama..."
            
            # Check if ollama installed
            if ! command -v ollama &> /dev/null; then
                echo "Ollama not found. Installing..."
                curl -fsSL https://ollama.com/install.sh | sh
            fi
            
            echo "✓ Ollama installed"
            
            # Start Ollama service
            echo "Starting Ollama service..."
            
            # Try systemctl first (most common)
            if command -v systemctl &> /dev/null; then
                sudo systemctl start ollama 2>/dev/null || true
                sudo systemctl enable ollama 2>/dev/null || true
            fi
            
            # Start manually if service not available
            if ! pgrep -x ollama &> /dev/null; then
                echo "Starting Ollama in background..."
                nohup ollama serve > /dev/null 2>&1 &
                sleep 2
            fi
            
            # Verify it's running
            if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
                echo "⚠️  Ollama service didn't start automatically"
                echo "Please run: ollama serve"
                echo "Then run this installer again"
                exit 1
            fi
            
            echo "✓ Ollama service running"
            echo ""
            echo "Choose a model:"
            echo "1) phi3:mini (3.8GB) - Recommended, fast and efficient"
            echo "2) llama3.2:3b (2GB) - Lightweight"
            echo "3) qwen2.5:3b (2.3GB) - Good reasoning"
            
            read -p "Enter choice [1-3]: " model_choice
            
            case $model_choice in
                1) PRIMARY_MODEL="phi3:mini" ;;
                2) PRIMARY_MODEL="llama3.2:3b" ;;
                3) PRIMARY_MODEL="qwen2.5:3b" ;;
                *) PRIMARY_MODEL="phi3:mini" ;;
            esac
            
            echo "Pulling model $PRIMARY_MODEL (this may take a few minutes)..."
            ollama pull $PRIMARY_MODEL
            
            echo "OLLAMA_MODEL=$PRIMARY_MODEL" >> "$SECRETS_FILE"
            echo "✓ Ollama configured with $PRIMARY_MODEL"
            ;;
            
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
    
    # Update config.yaml with primary provider
    sed -i "s/provider: anthropic/provider: $PRIMARY_PROVIDER/" "$CONFIG_FILE"
    sed -i "s/model: claude-3-5-sonnet-20241022/model: $PRIMARY_MODEL/" "$CONFIG_FILE"
    
    echo ""
    echo "════════════════════════════════════"
    echo "  Fallback Configuration (Optional)"
    echo "════════════════════════════════════"
    echo ""
    echo "Zenus can route simple tasks to cheaper models and fallback"
    echo "to more powerful models when needed."
    echo ""
    read -p "Configure fallback providers? (Y/n): " configure_fallback
    
    FALLBACK_PROVIDERS=""
    
    if [ "$configure_fallback" != "n" ] && [ "$configure_fallback" != "N" ]; then
        echo ""
        echo "Available fallback providers:"
        if [ "$PRIMARY_PROVIDER" != "anthropic" ]; then
            echo "  [1] Anthropic Claude"
        fi
        if [ "$PRIMARY_PROVIDER" != "deepseek" ]; then
            echo "  [2] DeepSeek"
        fi
        if [ "$PRIMARY_PROVIDER" != "openai" ]; then
            echo "  [3] OpenAI"
        fi
        if [ "$PRIMARY_PROVIDER" != "ollama" ]; then
            echo "  [4] Ollama (local)"
        fi
        echo ""
        echo "Enter numbers separated by space (e.g., '2 4' for DeepSeek and Ollama)"
        read -p "Fallback providers: " fallback_choices
        
        for choice in $fallback_choices; do
            case $choice in
                1)
                    if [ "$PRIMARY_PROVIDER" != "anthropic" ]; then
                        read -sp "Enter Anthropic API key: " api_key
                        echo ""
                        echo "ANTHROPIC_API_KEY=$api_key" >> "$SECRETS_FILE"
                        FALLBACK_PROVIDERS="$FALLBACK_PROVIDERS anthropic"
                        echo "✓ Anthropic added as fallback"
                    fi
                    ;;
                2)
                    if [ "$PRIMARY_PROVIDER" != "deepseek" ]; then
                        read -sp "Enter DeepSeek API key: " api_key
                        echo ""
                        echo "DEEPSEEK_API_KEY=$api_key" >> "$SECRETS_FILE"
                        FALLBACK_PROVIDERS="$FALLBACK_PROVIDERS deepseek"
                        echo "✓ DeepSeek added as fallback"
                    fi
                    ;;
                3)
                    if [ "$PRIMARY_PROVIDER" != "openai" ]; then
                        read -sp "Enter OpenAI API key: " api_key
                        echo ""
                        echo "OPENAI_API_KEY=$api_key" >> "$SECRETS_FILE"
                        FALLBACK_PROVIDERS="$FALLBACK_PROVIDERS openai"
                        echo "✓ OpenAI added as fallback"
                    fi
                    ;;
                4)
                    if [ "$PRIMARY_PROVIDER" != "ollama" ]; then
                        # Ollama already set up or skip if not installed
                        if command -v ollama &> /dev/null; then
                            FALLBACK_PROVIDERS="$FALLBACK_PROVIDERS ollama"
                            echo "✓ Ollama added as fallback"
                        else
                            echo "⚠️  Ollama not installed, skipping"
                        fi
                    fi
                    ;;
            esac
        done
        
        # Update fallback providers in config.yaml
        if [ -n "$FALLBACK_PROVIDERS" ]; then
            echo ""
            echo "✓ Fallback enabled with:$FALLBACK_PROVIDERS"
            echo "  You can customize the fallback order in: $CONFIG_FILE"
            echo "  (Look for the 'fallback:' section)"
        fi
    else
        # Disable fallback in config.yaml
        # Find the line with "enabled: true" under fallback section and change it
        sed -i '/fallback:/,/^[^ ]/ { /enabled: true/s/true/false/ }' "$CONFIG_FILE"
        echo "✓ Fallback disabled"
    fi
    
    echo ""
    echo "✓ Configuration saved:"
    echo "  Config: $CONFIG_FILE"
    echo "  Secrets: $SECRETS_FILE (secure, chmod 600)"
fi

echo ""
echo "════════════════════════════════════"
echo "  Setting up shell aliases..."
echo "════════════════════════════════════"
echo ""

# Define the aliases
ZENUS_ALIAS="alias zenus='$PROJECT_DIR/zenus.sh'"
ZENUS_TUI_ALIAS="alias zenus-tui='$PROJECT_DIR/zenus-tui.sh'"

# Check if aliases already exist in bashrc
if grep -q "alias zenus=" ~/.bashrc 2>/dev/null; then
    echo "⚠️  Zenus aliases already exist in ~/.bashrc"
    echo "   Updating to standardized format..."
    
    # Remove old aliases (zenus_os, zenus, zenus-tui)
    sed -i '/alias zenus_os=/d' ~/.bashrc
    sed -i '/alias zenus=/d' ~/.bashrc
    sed -i '/alias zenus-tui=/d' ~/.bashrc
    
    # Add new standardized aliases
    echo "" >> ~/.bashrc
    echo "# Zenus OS aliases" >> ~/.bashrc
    echo "$ZENUS_ALIAS" >> ~/.bashrc
    echo "$ZENUS_TUI_ALIAS" >> ~/.bashrc
    
    echo "✓ Aliases updated"
else
    # Add aliases for the first time
    echo "" >> ~/.bashrc
    echo "# Zenus OS aliases" >> ~/.bashrc
    echo "$ZENUS_ALIAS" >> ~/.bashrc
    echo "$ZENUS_TUI_ALIAS" >> ~/.bashrc
    
    echo "✓ Aliases added to ~/.bashrc"
fi

echo ""
echo "════════════════════════════════════"
echo "  Installation Complete!"
echo "════════════════════════════════════"
echo ""
echo "Configuration files:"
echo "  $CONFIG_FILE"
echo "  $SECRETS_FILE (secure)"
echo ""
echo "To start using Zenus, run:"
echo "  source ~/.bashrc"
echo ""
echo "Then you can use:"
echo "  zenus                    # Interactive shell"
echo "  zenus help               # Show help"
echo "  zenus \"<command>\"        # Direct execution"
echo "  zenus-tui                # Launch TUI interface"
echo ""
echo "Or run directly:"
echo "  $PROJECT_DIR/zenus.sh"
echo "  $PROJECT_DIR/zenus-tui.sh"
echo ""
