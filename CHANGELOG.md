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
- [x] Sentence-level segmentation toggle (switchable after transcription)
- [x] Export All button (all formats at once)
- [x] Improved Edit button visibility
- [x] Timestamped filename for TXT exports
- [x] Re-transcribe option for already-completed videos
- [x] Aligned left/right panel layout
- [ ] Enhanced error messages for common issues
- [ ] Keyboard shortcuts
- [ ] Remember window size/position
- [ ] Dark mode support

---

## [1.0.1] - 2026-02-05

### Added
- Sentence-level segmentation checkbox - toggle between natural pauses and sentence boundaries (., !, ?) without re-transcribing. Uses word-level timestamps for precise sentence timing.
- Export All button - export TXT, SRT, VTT, and JSON formats at once to a chosen directory
- Timestamped TXT filename - when exporting TXT with timestamps enabled, default filename includes `_timestamped` suffix
- Re-transcribe option - hitting "Transcribe" on already-completed videos now offers to re-transcribe instead of blocking

### Changed
- Edit button restyled with blue outline, bold text, and pencil icon for better visibility
- Aligned left and right panel headers for consistent layout

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
- "Show timestamps" checkbox to toggle timestamp display in preview
- Format preview - switching export format shows that format in the view
- Edit mode - toggle to edit transcript text, updates all export formats
- PyInstaller packaging for distributable macOS .app bundle
- Beginner-friendly documentation

### Supported Formats
- Video: MP4, MKV, AVI, MOV, WMV, FLV, WebM, M4V, MPEG, MPG, 3GP, OGV
- Audio: MP3, WAV, M4A, AAC, OGG, FLAC, WMA

### Technical Details
- Uses QThread for non-blocking UI
- Audio extracted to 16kHz mono WAV for optimal Whisper performance
- Models cached in ~/.cache/video-to-transcript/models/
- INT8 quantization for efficient CPU/Apple Silicon inference
