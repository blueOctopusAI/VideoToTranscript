# Video to Transcript

Desktop application to transcribe video files using local Whisper AI.

See [README.md](README.md) for user documentation and [CHANGELOG.md](CHANGELOG.md) for progress tracking.

## Quick Start

```bash
source venv/bin/activate
python src/main.py
```

## Project Structure

```
VideoToTranscript/
├── src/
│   ├── main.py                    # Entry point
│   ├── ui/
│   │   ├── main_window.py         # Main layout with splitter
│   │   ├── video_list_widget.py   # Left panel - drag-drop list
│   │   └── transcript_panel.py    # Right panel - transcript display
│   ├── services/
│   │   ├── audio_extractor.py     # ffmpeg audio extraction
│   │   ├── transcription_worker.py # QThread workers
│   │   └── model_manager.py       # Whisper model management
│   ├── models/
│   │   └── video_item.py          # VideoItem, TranscriptionSegment
│   └── exporters/
│       ├── txt_exporter.py        # Plain text
│       ├── srt_exporter.py        # SRT subtitles
│       ├── vtt_exporter.py        # WebVTT subtitles
│       └── json_exporter.py       # JSON with metadata
├── scripts/
│   └── build-app.sh               # PyInstaller build script
├── venv/                          # Virtual environment (not in repo)
├── dist/                          # Built app output (not in repo)
├── build/                         # PyInstaller temp files (not in repo)
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Build dependencies (includes pyinstaller)
├── VideoToTranscript.spec         # PyInstaller configuration
├── pyproject.toml
├── .gitignore
├── run.sh                         # Quick run script (activates venv)
├── LICENSE                        # MIT License
├── README.md                      # User documentation
├── CHANGELOG.md                   # Progress & version history
└── CLAUDE.md                      # Developer reference (this file)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PySide6 UI Layer                      │
│  ┌──────────────┐  ┌─────────────────────────────────┐  │
│  │ VideoList    │  │     TranscriptPanel             │  │
│  │ - Drag/Drop  │  │  - Progress bar                 │  │
│  │ - Add Files  │  │  - Live preview                 │  │
│  │ - Add Folder │  │  - Timestamp toggle             │  │
│  │ - Selection  │  │  - Edit mode                    │  │
│  │ - Status     │  │  - Format preview               │  │
│  │              │  │  - Export (TXT/SRT/VTT/JSON)    │  │
│  └──────────────┘  └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                  Service Layer (QThread)                 │
│  AudioExtractor (ffmpeg) → TranscriptionWorker (whisper)│
└─────────────────────────────────────────────────────────┘
```

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | App entry point, QApplication setup |
| `main_window.py` | MainWindow, menus, signal routing |
| `video_list_widget.py` | Drag-drop, file dialogs, list management |
| `transcript_panel.py` | Display, edit mode, progress, export UI |
| `transcription_worker.py` | QThread workers for transcription |
| `audio_extractor.py` | ffmpeg integration, format validation |
| `model_manager.py` | Model loading, device detection |
| `VideoToTranscript.spec` | PyInstaller build configuration |
| `build-app.sh` | Automated build script |

## Features

- **Drag-and-drop** video files or folders
- **Batch transcription** with progress tracking
- **Live preview** during transcription
- **Timestamp toggle** - show/hide `[HH:MM:SS]` timestamps
- **Format preview** - switch between TXT/SRT/VTT/JSON views
- **Edit mode** - modify transcript text, updates all formats
- **Export** - TXT respects timestamp checkbox; SRT/VTT/JSON include timing

## Edit Mode

Click "Edit" button to enter edit mode:
- Orange border + "EDITING" badge indicate active editing
- Forces TXT format with timestamps visible
- Parse logic matches `[HH:MM:SS]` pattern to preserve segment timing
- Exit edit mode to save changes and re-enable export

## Supported Formats

**Video:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpeg`, `.mpg`, `.3gp`, `.ogv`

**Audio:** `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.wma`

**Note:** File search is case-insensitive (handles `.MOV`, `.MP4`, etc.)

## Building the App

To create a distributable `.app` bundle:

```bash
# Activate venv
source venv/bin/activate

# Install build dependencies
pip install -r requirements-dev.txt

# Run build script
./scripts/build-app.sh
```

Output: `dist/Video to Transcript.app`

### What Gets Bundled

- Python runtime
- All pip dependencies (PySide6, faster-whisper, etc.)
- ffmpeg and ffprobe binaries (in `bin/` subdirectory)
- Application code

### What's Required on User's System

- **FFmpeg libraries** - The bundled ffmpeg binary is dynamically linked and requires ffmpeg to be installed via Homebrew (`brew install ffmpeg`). This is noted in the README.

> **Why not fully standalone?** Bundling all ffmpeg dylibs would require complex library dependency resolution and significantly increase app size. The Homebrew requirement is a reasonable tradeoff for most Mac users.

### What Downloads at Runtime

- Whisper models (74MB - 1.5GB depending on selection)
- Cached in `~/.cache/video-to-transcript/models/`

### Build Configuration

The `VideoToTranscript.spec` file configures:
- Hidden imports for PySide6 and faster-whisper
- ffmpeg binary bundling
- macOS .app bundle settings
- Document type associations (video/audio files)

## Development Notes

- Audio extracted to 16kHz mono WAV for Whisper
- Models cached in `~/.cache/video-to-transcript/models/`
- Uses INT8 quantization on CPU/Apple Silicon
- QThread prevents UI blocking during transcription
- Folder search handles both lowercase and uppercase extensions

## Release Workflow

1. Update version in `VideoToTranscript.spec` and `CHANGELOG.md`
2. Run `./scripts/build-app.sh`
3. Test the built app
4. Zip the app: `cd dist && zip -r "Video to Transcript.zip" "Video to Transcript.app"`
5. Create GitHub release and attach the zip
