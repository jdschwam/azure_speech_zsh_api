#!/bin/bash
# Install Python dependencies for avatar functionality

echo "📦 Installing Python dependencies for Azure TTS Avatar..."

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "avatar_env" ]]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv avatar_env
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source avatar_env/bin/activate

# Install required packages
echo "📥 Installing packages..."
pip install --upgrade pip
pip install aiortc aiohttp opencv-python websockets

echo "✅ Avatar dependencies installed successfully!"
echo ""
echo "To use avatar functionality:"
echo "1. Ensure your Azure avatar credentials are configured"
echo "2. Run: ./azure_speech_v1.sh ttsa \"Your text here\""
