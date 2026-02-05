# Changelog

## Development Progress

### Phase 1: Foundation - COMPLETE

- [x] Project setup (pyproject.toml, requirements.txt)
- [x] Virtual environment configuration
- [x] Basic PySide6 main window with splitter layout
- [x] Video list widget with drag-and-drop support
- [x] Data models (VideoItem, TranscriptionSegment)
- [x] Audio extraction service (ffmpeg integration)
- [x] Model manager for Whisper models
- [x] Single video transcription worker (QThread)
- [x] Transcript panel with live preview

### Phase 2: Core Features - COMPLETE

- [x] Folder import functionality
- [x] Progress indication with live preview
- [x] Multiple export formats (TXT, SRT, VTT, JSON)
- [x] Settings dialog (model size selection)
- [x] Batch queue processing (BatchTranscriptionWorker)

### Phase 3: Polish - IN PROGRESS

- [x] Basic error handling
- [x] Application styling (Fusion theme)
- [x] Status indicators in video list
- [x] Fixed text color visibility (white on white issue)
- [x] Simplified timestamps to HH:MM:SS format (no milliseconds in view)
- [x] Toggle timestamps checkbox (default on)
- [x] Format preview - view updates when switching export formats
- [x] Smart checkbox - greyed out when format requires timestamps (SRT/VTT)
- [x] Consistent paragraph spacing in view and TXT export
- [x] TXT export respects timestamp checkbox setting
- [x] Edit mode for modifying transcripts
- [x] PyInstaller packaging for distributable .app bundle
- [x] Beginner-friendly documentation
- [ ] Enhanced error messages for common issues
- [ ] Keyboard shortcuts
- [ ] Remember window size/position
- [ ] Dark mode support

---

## [1.2.0] - 2025-02-04

### Added
- PyInstaller packaging for distributable macOS .app bundle
- Build script (`scripts/build-app.sh`) for easy app building
- Development dependencies file (`requirements-dev.txt`)
- Comprehensive beginner-friendly documentation
- Troubleshooting section in README

### Changed
- README completely rewritten with two installation paths (app download vs source)
- Step-by-step instructions for virtual environment setup

---

## [1.1.0] - 2025-02-04

### Added
- "Show timestamps" checkbox to toggle timestamp display in preview
- Format preview - switching export format shows that format in the view
- Simplified timestamp format (HH:MM:SS) for display, full precision for SRT/VTT
- Edit mode - toggle to edit transcript text, updates all export formats
  - Orange border and "EDITING" badge indicate edit mode
  - Edits parsed back to segments preserving timestamps

### Changed
- Checkbox is greyed out and forced on when SRT or VTT format is selected
- TXT export respects timestamp checkbox (includes timestamps when checked, omits when unchecked)
- TXT export now uses paragraph spacing (double newlines) matching the view
- Copy button now copies the current view (respecting format and timestamp settings)

### Fixed
- Text visibility issue (white text on white background)
- Folder import now finds files with uppercase extensions (.MOV, .MP4, etc.)

---

## [1.0.0] - 2025-02-04

### Added
- Initial release
- PySide6 desktop application
- Drag-and-drop video import
- Folder import with recursive search
- faster-whisper transcription with model selection (tiny, base, small, medium, large-v3)
- Live transcript preview during processing
- Export to TXT, SRT, VTT, JSON formats
- Batch transcription support
- Settings dialog for model configuration
- Progress tracking with status updates

### Supported Formats
- Video: MP4, MKV, AVI, MOV, WMV, FLV, WebM, M4V, MPEG, MPG, 3GP, OGV
- Audio: MP3, WAV, M4A, AAC, OGG, FLAC, WMA

### Technical Details
- Uses QThread for non-blocking UI
- Audio extracted to 16kHz mono WAV for optimal Whisper performance
- Models cached in ~/.cache/video-to-transcript/models/
- INT8 quantization for efficient CPU/Apple Silicon inference
