#!/bin/bash
# Auto-generated installation script for Pomodoro Timer
# Generated on 2025-10-19

set -e

echo "🍅 Installing Pomodoro Timer..."

# Check if required tools are installed
command -v git >/dev/null 2>&1 || { echo "❌ Git is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }

echo "✅ Checking system dependencies..."

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Installing..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y ffmpeg
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg
    else
        echo "❌ Please install FFmpeg manually from: https://ffmpeg.org/"
        exit 1
    fi
fi

# Check for VLC
if ! command -v vlc &> /dev/null; then
    echo "⚠️  VLC not found. Installing..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update && sudo apt install -y vlc python3-vlc
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install vlc
    else
        echo "❌ Please install VLC manually from: https://www.videolan.org/"
        exit 1
    fi
fi

echo "📦 Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

echo "📁 Creating required directories..."
mkdir -p pomodoro/audio
mkdir -p pomodoro/video
mkdir -p pomodoro/downloads

# Set permissions
chmod +x pomodoro/main.py

echo "✅ Installation completed successfully!"
echo ""
echo "🚀 To run the Pomodoro Timer:"
echo "   source venv/bin/activate"
echo "   python pomodoro/main.py"
echo ""
echo "📖 Check README.md for usage instructions"
