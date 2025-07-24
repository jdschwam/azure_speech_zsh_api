#!/bin/bash
# Install Python dependencies for avatar functionality (Batch API)

echo "📦 Installing Python dependencies for Azure TTS Avatar (Batch API)..."

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [[ ! -d ".venv" ]]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# Install required packages for batch synthesis
echo "📥 Installing packages for batch avatar synthesis..."
pip install --upgrade pip
pip install requests urllib3

echo "✅ Avatar batch dependencies installed successfully!"
echo ""
echo "Dependencies installed:"
echo "  • requests (HTTP client for Azure batch API)"
echo "  • urllib3 (URL parsing utilities)"
echo ""
echo "To use avatar functionality:"
echo "1. Ensure your Azure avatar credentials are configured"
echo "2. Run: ./azure_speech_v1.sh ttsa \"Your text here\""
echo ""
echo "Note: This uses the Azure Batch Avatar API, which is more reliable"
echo "      than real-time WebRTC and doesn't require special permissions."
