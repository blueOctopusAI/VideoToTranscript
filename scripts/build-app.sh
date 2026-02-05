#!/bin/bash
#
# Build Video to Transcript as a macOS .app bundle
#
# Usage: ./scripts/build-app.sh
#
# Prerequisites:
#   - macOS with Apple Silicon (M1/M2/M3/M4)
#   - Python 3.10+
#   - ffmpeg installed (brew install ffmpeg)
#
# Output: dist/Video to Transcript.app
#

set -e  # Exit on error

echo "========================================="
echo "Building Video to Transcript.app"
echo "========================================="
echo ""

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg not found"
    echo "Install with: brew install ffmpeg"
    exit 1
fi
echo "Found ffmpeg: $(which ffmpeg)"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi
echo "Found Python: $(python3 --version)"

# Create/activate virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist

# Run PyInstaller
echo ""
echo "Running PyInstaller..."
pyinstaller VideoToTranscript.spec --noconfirm

# Check if build succeeded
if [ -d "dist/Video to Transcript.app" ]; then
    echo ""
    echo "========================================="
    echo "BUILD SUCCESSFUL!"
    echo "========================================="
    echo ""
    echo "App location: dist/Video to Transcript.app"
    echo ""
    echo "To run: open \"dist/Video to Transcript.app\""
    echo ""
    echo "To install: drag the app to your Applications folder"
    echo ""

    # Show app size
    APP_SIZE=$(du -sh "dist/Video to Transcript.app" | cut -f1)
    echo "App size: $APP_SIZE"
    echo ""
    echo "Note: Whisper models will download on first transcription (~74MB for base model)"
else
    echo ""
    echo "ERROR: Build failed"
    exit 1
fi
