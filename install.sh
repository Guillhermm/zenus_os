#!/bin/bash
set -e

echo "╔════════════════════════════════════╗"
echo "║   Zenus OS Installation Script     ║"
echo "╚════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo "Installing Python 3..."
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo "✓ Dependencies installed"
echo ""

# LLM Backend Setup
echo "════════════════════════════════════"
echo "  LLM Backend Configuration"
echo "════════════════════════════════════"
echo ""
echo "Choose your LLM backend:"
echo ""
echo "1) Ollama (Local, FREE - recommended for privacy)"
echo "   - Runs on your hardware"
echo "   - No API key needed"
echo "   - Requires 4-16GB RAM"
echo ""
echo "2) OpenAI (Cloud, requires API key)"
echo "   - Fast and reliable"
echo "   - Costs ~\$0.001 per command"
echo ""
echo "3) DeepSeek (Cloud, requires API key)"
echo "   - Good performance"
echo "   - Lower cost than OpenAI"
echo ""

read -p "Enter choice [1-3]: " llm_choice

# Backup old .env if exists, create fresh
if [ -f ".env" ]; then
    mv .env .env.backup
    echo "⚠️  Backed up existing .env to .env.backup"
fi

cp .env.example .env

case $llm_choice in
    1)
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
            sleep 2  # Give it time to start
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
            1) MODEL="phi3:mini" ;;
            2) MODEL="llama3.2:3b" ;;
            3) MODEL="qwen2.5:3b" ;;
            *) MODEL="phi3:mini" ;;
        esac
        
        echo "Pulling model $MODEL (this may take a few minutes)..."
        ollama pull $MODEL
        
        # Update .env with proper format (sed to replace existing lines)
        sed -i "s/^ZENUS_LLM=.*/ZENUS_LLM=ollama/" .env
        sed -i "s/^OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL/" .env
        
        echo "✓ Ollama configured with $MODEL"
        ;;
        
    2)
        echo ""
        read -p "Enter your OpenAI API key: " api_key
        sed -i "s/^ZENUS_LLM=.*/ZENUS_LLM=openai/" .env
        sed -i "s/^# OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
        echo "✓ OpenAI configured"
        ;;
        
    3)
        echo ""
        read -p "Enter your DeepSeek API key: " api_key
        sed -i "s/^ZENUS_LLM=.*/ZENUS_LLM=deepseek/" .env
        sed -i "s/^# DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=$api_key/" .env
        echo "✓ DeepSeek configured"
        ;;
        
    *)
        echo "Invalid choice, defaulting to Ollama"
        ollama pull phi3:mini
        sed -i "s/^ZENUS_LLM=.*/ZENUS_LLM=ollama/" .env
        sed -i "s/^OLLAMA_MODEL=.*/OLLAMA_MODEL=phi3:mini/" .env
        ;;
esac

echo ""
echo "════════════════════════════════════"
echo "  Installation Complete!"
echo "════════════════════════════════════"
echo ""
echo "Run Zenus OS:"
echo "  ./zenus.sh               # Start interactive shell"
echo "  ./zenus.sh help          # Show help"
echo "  ./zenus.sh \"<command>\"   # Direct execution"
echo ""
echo "Or add to PATH:"
echo "  echo 'alias zenus_os=\"$(pwd)/zenus.sh\"' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo ""
