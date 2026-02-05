# Video to Transcript

A desktop application that transcribes video and audio files using AI. All processing happens locally on your Mac - no cloud services, no subscriptions, no data leaving your computer.

![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Drag-and-drop** - Just drop your video files onto the app
- **Batch processing** - Transcribe multiple files at once
- **Live preview** - Watch the transcript appear in real-time
- **Edit mode** - Fix words, add punctuation, capitalize names
- **Multiple formats** - Export to TXT, SRT, VTT, or JSON
- **Timestamps** - Toggle timestamps on/off
- **100% local** - Uses Whisper AI running on your Mac
- **Apple Silicon optimized** - Fast performance on M1/M2/M3/M4

## Supported Files

| Type | Formats |
|------|---------|
| **Video** | MP4, MKV, AVI, MOV, WMV, FLV, WebM, M4V, MPEG, MPG, 3GP, OGV |
| **Audio** | MP3, WAV, M4A, AAC, OGG, FLAC, WMA |

---

## Installation

Choose ONE of these methods:

### Option A: Download the App (Easiest)

> **For users who just want to run the app**

**Prerequisite:** You need FFmpeg installed on your Mac:
```bash
brew install ffmpeg
```
Don't have Homebrew? Install it first: https://brew.sh

**Then:**
1. Go to [Releases](../../releases)
2. Download `Video.to.Transcript.app.zip`
3. Unzip and drag to your Applications folder
4. Double-click to run

**First run note:** macOS may show a security warning. Right-click the app and select "Open" to bypass it.

---

### Option B: Run from Source (For Developers)

> **For users who want to modify the code or always have the latest version**

#### Prerequisites

You need these installed on your Mac:

1. **Python 3.10 or newer**
   ```bash
   # Check if you have Python
   python3 --version

   # If not installed, get it from python.org or:
   brew install python
   ```

2. **FFmpeg** (handles video/audio processing)
   ```bash
   # Install via Homebrew
   brew install ffmpeg

   # Don't have Homebrew? Install it first:
   # /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

#### Setup Steps

**Step 1: Download the code**
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/VideoToTranscript.git
cd VideoToTranscript
```

Or download and unzip from the GitHub page.

**Step 2: Create a virtual environment**

A virtual environment keeps this project's dependencies separate from your system Python. This is important!

```bash
# Create the virtual environment (only need to do this once)
python3 -m venv venv
```

**Step 3: Activate the virtual environment**

```bash
# On macOS/Linux
source venv/bin/activate
```

You'll see `(venv)` appear at the start of your terminal prompt. This means you're in the virtual environment.

> **Important:** You need to activate the virtual environment EVERY time you open a new terminal to run the app.

**Step 4: Install dependencies**

```bash
# Install required packages (only need to do this once)
pip install -r requirements.txt
```

**Step 5: Run the app**

```bash
python src/main.py
```

#### Quick Start Commands (After Setup)

Once you've done the setup, here's all you need each time:

```bash
cd VideoToTranscript
source venv/bin/activate
python src/main.py
```

**Or even simpler** - use the run script (it handles venv activation for you):

```bash
cd VideoToTranscript
./run.sh
```

---

## How to Use

1. **Add videos** - Drag files onto the app, or use "Add Files" / "Add Folder" buttons
2. **Select videos** - Click to select one or more videos in the list
3. **Transcribe** - Click "Transcribe Selected" and wait for processing
4. **Review** - The transcript appears in the right panel
5. **Edit (optional)** - Click "Edit" to fix any mistakes
6. **Export** - Choose a format and click "Export"

### Timestamps

- Use the "Show timestamps" checkbox to toggle `[HH:MM:SS]` display
- TXT export respects this setting
- SRT/VTT formats always include timestamps (required for subtitles)

### Editing Transcripts

Click the **Edit** button to enter edit mode:

- Orange border and "EDITING" badge show you're in edit mode
- Fix misspelled words, add punctuation, capitalize names
- Keep the `[HH:MM:SS]` timestamps intact - they mark segment boundaries
- Click **Edit** again to save and exit edit mode
- Your changes apply to all export formats

### Export Formats

| Format | Best For |
|--------|----------|
| **TXT** | Reading, copying text |
| **SRT** | Video subtitles (VLC, Premiere, etc.) |
| **VTT** | Web video subtitles (HTML5) |
| **JSON** | Programmatic use, data processing |

---

## Settings

Access via **Edit > Settings** in the menu bar.

### Whisper Models

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| `tiny` | 39 MB | Fastest | Good | Quick drafts, testing |
| `base` | 74 MB | Fast | Better | **Default - good balance** |
| `small` | 244 MB | Medium | Great | Most content |
| `medium` | 769 MB | Slow | Excellent | Difficult audio |
| `large-v3` | 1.5 GB | Slowest | Best | Maximum accuracy |

Models download automatically on first use and are cached for future runs.

---

## Building the App (For Developers)

Want to create a distributable `.app` bundle?

```bash
# Make sure you're in the project directory with venv activated
source venv/bin/activate

# Install build dependencies
pip install -r requirements-dev.txt

# Run the build script
./scripts/build-app.sh
```

The built app will be at `dist/Video to Transcript.app`

---

## Troubleshooting

### "ffmpeg not found" or transcription fails immediately

FFmpeg is required even when using the standalone app. Install it:
```bash
brew install ffmpeg
```

Don't have Homebrew? Install it first:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### "No supported files found" when adding a folder

Make sure your files have standard extensions (.mp4, .mov, etc.). The app searches for common video/audio formats.

### Model download is slow

The first transcription downloads the Whisper model. The base model is ~74 MB. Once downloaded, it's cached at `~/.cache/video-to-transcript/models/`

### App won't open (macOS security)

Right-click the app and select "Open", then click "Open" in the dialog. You only need to do this once.

### "zsh: command not found: python"

Use `python3` instead of `python`:
```bash
python3 src/main.py
```

### Transcript quality is poor

Try a larger model in Settings. The `small` or `medium` models are significantly more accurate than `base`.

### Virtual environment issues

If you see errors about missing packages, make sure you've activated the venv:
```bash
source venv/bin/activate
```

Your prompt should show `(venv)` at the beginning.

---

## Tech Stack

- **UI:** PySide6 (Qt6)
- **Transcription:** faster-whisper (CTranslate2)
- **Audio Processing:** FFmpeg
- **Packaging:** PyInstaller

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
