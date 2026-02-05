"""Main application window."""

from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QMenuBar,
    QMenu,
    QStatusBar,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QComboBox,
    QFormLayout,
)

from ..models.video_item import VideoItem, TranscriptionSegment, SegmentationMode
from ..services.model_manager import ModelManager, AVAILABLE_MODELS, DEFAULT_MODEL
from ..services.transcription_worker import TranscriptionWorker, BatchTranscriptionWorker, build_sentence_segments
from .video_list_widget import VideoListWidget
from .transcript_panel import TranscriptPanel


class SettingsDialog(QDialog):
    """Settings dialog for configuring the application."""

    def __init__(self, current_model: str, parent: Optional[QWidget] = None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Model selection
        form_layout = QFormLayout()

        self.model_combo = QComboBox()
        for name, info in AVAILABLE_MODELS.items():
            self.model_combo.addItem(
                f"{name} ({info.size_mb}MB) - {info.description}",
                name
            )
            if name == current_model:
                self.model_combo.setCurrentIndex(self.model_combo.count() - 1)

        form_layout.addRow("Whisper Model:", self.model_combo)

        # Model info
        info_label = QLabel(
            "Larger models are more accurate but slower.\n"
            "Models are downloaded on first use (~75MB - 1.5GB)."
        )
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        form_layout.addRow("", info_label)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_model(self) -> str:
        """Get the selected model name."""
        return self.model_combo.currentData()

class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()

        self.setWindowTitle("Video to Transcript")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        # Services
        self._model_manager = ModelManager()
        self._current_model = DEFAULT_MODEL
        self._current_worker: Optional[TranscriptionWorker | BatchTranscriptionWorker] = None

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Video list
        self.video_list = VideoListWidget()
        self.splitter.addWidget(self.video_list)

        # Right panel - Transcript
        self.transcript_panel = TranscriptPanel()
        self.splitter.addWidget(self.transcript_panel)

        # Set initial sizes (1:2 ratio)
        self.splitter.setSizes([350, 700])

        layout.addWidget(self.splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        add_files_action = file_menu.addAction("Add Files...")
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.video_list._on_add_files)

        add_folder_action = file_menu.addAction("Add Folder...")
        add_folder_action.setShortcut("Ctrl+Shift+O")
        add_folder_action.triggered.connect(self.video_list._on_add_folder)

        file_menu.addSeparator()

        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)

        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")

        settings_action = edit_menu.addAction("Settings...")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)

        # Help menu
        help_menu = menu_bar.addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about)

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Video list signals
        self.video_list.video_selected.connect(self._on_video_selected)
        self.video_list.transcribe_requested.connect(self._on_transcribe_requested)
        self.video_list.sentence_segments_checkbox.stateChanged.connect(self._on_segment_mode_changed)

    @Slot(VideoItem)
    def _on_video_selected(self, video_item: VideoItem) -> None:
        """Handle video selection."""
        self.transcript_panel.set_video(video_item)

    @Slot(int)
    def _on_segment_mode_changed(self, state: int) -> None:
        """Handle sentence-level segments checkbox toggle.

        Re-segments the current video's transcript without re-transcribing,
        using stored word-level timing data.
        """
        current = self.transcript_panel._current_video
        if not current or not current.is_transcribed:
            return

        if self.video_list.sentence_segments_checkbox.isChecked():
            # Switch to sentence-level segments
            if current.word_data:
                sentence_segs = build_sentence_segments(current.word_data)
                if sentence_segs:
                    current.segments = sentence_segs
        else:
            # Switch back to natural pauses
            if current.original_segments:
                current.segments = list(current.original_segments)

        # Refresh transcript display
        self.transcript_panel._refresh_display()

    @Slot(list)
    def _on_transcribe_requested(self, video_items: list[VideoItem]) -> None:
        """Handle transcription request."""
        if not video_items:
            return

        # Cancel any existing worker
        if self._current_worker and self._current_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Transcription in Progress",
                "A transcription is already in progress. Cancel it and start a new one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            self._current_worker.cancel()
            self._current_worker.wait()

        # Filter out already transcribed items
        items_to_transcribe = [
            item for item in video_items
            if not item.is_transcribed and not item.is_processing
        ]

        if not items_to_transcribe:
            # All selected are already transcribed - offer to re-transcribe
            reply = QMessageBox.question(
                self,
                "Re-transcribe?",
                "All selected videos have already been transcribed.\n\n"
                "Would you like to re-transcribe them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            # Clear transcriptions and re-transcribe
            for item in video_items:
                if not item.is_processing:
                    item.clear_transcription()
                    self.video_list.update_video_status(item)
            items_to_transcribe = [
                item for item in video_items
                if not item.is_processing
            ]
            if not items_to_transcribe:
                return

        # Start transcription
        if len(items_to_transcribe) == 1:
            self._transcribe_single(items_to_transcribe[0])
        else:
            self._transcribe_batch(items_to_transcribe)

    def _get_segment_mode(self) -> str:
        """Get the current segmentation mode from the checkbox."""
        if self.video_list.sentence_segments_checkbox.isChecked():
            return SegmentationMode.SENTENCE_LEVEL
        return SegmentationMode.NATURAL_PAUSES

    def _transcribe_single(self, video_item: VideoItem) -> None:
        """Transcribe a single video."""
        self.transcript_panel.set_video(video_item)

        worker = TranscriptionWorker(
            video_item=video_item,
            model_manager=self._model_manager,
            model_name=self._current_model,
            segment_mode=self._get_segment_mode(),
            parent=self
        )

        # Connect signals
        worker.progress.connect(self._on_transcription_progress)
        worker.segment_ready.connect(self._on_segment_ready)
        worker.completed.connect(self._on_transcription_completed)
        worker.error.connect(self._on_transcription_error)

        self._current_worker = worker
        worker.start()

        self.status_bar.showMessage(f"Transcribing: {video_item.filename}")

    def _transcribe_batch(self, video_items: list[VideoItem]) -> None:
        """Transcribe multiple videos in batch."""
        # Show first item
        self.transcript_panel.set_video(video_items[0])

        worker = BatchTranscriptionWorker(
            video_items=video_items,
            model_manager=self._model_manager,
            model_name=self._current_model,
            segment_mode=self._get_segment_mode(),
            parent=self
        )

        # Connect signals
        worker.item_started.connect(self._on_batch_item_started)
        worker.item_progress.connect(self._on_transcription_progress)
        worker.item_completed.connect(self._on_batch_item_completed)
        worker.item_error.connect(self._on_transcription_error)
        worker.batch_completed.connect(self._on_batch_completed)

        self._current_worker = worker
        worker.start()

        self.status_bar.showMessage(f"Batch transcription: {len(video_items)} videos")

    @Slot(VideoItem, float, str)
    def _on_transcription_progress(self, video_item: VideoItem, progress: float, status: str) -> None:
        """Handle transcription progress updates."""
        self.video_list.update_video_status(video_item)
        self.transcript_panel.update_progress(video_item, progress, status)
        self.status_bar.showMessage(f"{video_item.filename}: {status}")

    @Slot(VideoItem, TranscriptionSegment)
    def _on_segment_ready(self, video_item: VideoItem, segment: TranscriptionSegment) -> None:
        """Handle new transcription segment."""
        self.transcript_panel.append_segment(video_item, segment)

    @Slot(VideoItem)
    def _on_transcription_completed(self, video_item: VideoItem) -> None:
        """Handle transcription completion."""
        self.video_list.update_video_status(video_item)
        self.transcript_panel.on_transcription_complete(video_item)
        self.status_bar.showMessage(f"Completed: {video_item.filename}")

    @Slot(VideoItem, str)
    def _on_transcription_error(self, video_item: VideoItem, error: str) -> None:
        """Handle transcription error."""
        self.video_list.update_video_status(video_item)
        self.transcript_panel.on_transcription_error(video_item, error)
        self.status_bar.showMessage(f"Error: {video_item.filename}")

    @Slot(VideoItem)
    def _on_batch_item_started(self, video_item: VideoItem) -> None:
        """Handle batch item start."""
        self.transcript_panel.set_video(video_item)

    @Slot(VideoItem)
    def _on_batch_item_completed(self, video_item: VideoItem) -> None:
        """Handle batch item completion."""
        self.video_list.update_video_status(video_item)
        self.transcript_panel.on_transcription_complete(video_item)

    @Slot()
    def _on_batch_completed(self) -> None:
        """Handle batch completion."""
        self.status_bar.showMessage("Batch transcription complete")
        QMessageBox.information(
            self,
            "Batch Complete",
            "All videos have been transcribed."
        )

    def _show_settings(self) -> None:
        """Show the settings dialog."""
        dialog = SettingsDialog(self._current_model, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_model = dialog.get_selected_model()
            if new_model != self._current_model:
                self._current_model = new_model
                self.status_bar.showMessage(f"Model changed to: {new_model}")

    def _show_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About Video to Transcript",
            "<h3>Video to Transcript</h3>"
            "<p>Desktop application for transcribing video files using local Whisper AI.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Drag-and-drop video files</li>"
            "<li>Batch transcription</li>"
            "<li>Export to TXT, SRT, VTT, JSON</li>"
            "<li>Local processing (no cloud required)</li>"
            "</ul>"
            "<p>Powered by faster-whisper and PySide6.</p>"
        )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        # Cancel any running worker
        if self._current_worker and self._current_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Transcription in Progress",
                "A transcription is in progress. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self._current_worker.cancel()
            self._current_worker.wait()

        event.accept()
