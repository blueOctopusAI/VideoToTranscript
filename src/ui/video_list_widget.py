"""Video list widget with drag-and-drop support."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFileDialog,
    QLabel,
    QProgressBar,
    QMessageBox,
    QCheckBox,
)

from ..models.video_item import VideoItem, TranscriptionStatus
from ..services.audio_extractor import AudioExtractor


class VideoListWidget(QWidget):
    """
    Widget displaying a list of video files with drag-and-drop support.

    Signals:
        video_selected: Emitted when a video is selected
        transcribe_requested: Emitted when user wants to transcribe selected videos
        transcribe_all_requested: Emitted when user wants to transcribe all videos
    """

    video_selected = Signal(VideoItem)
    transcribe_requested = Signal(list)  # List of VideoItems
    transcribe_all_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the video list widget."""
        super().__init__(parent)
        self._video_items: dict[str, VideoItem] = {}  # path -> VideoItem
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header (matches right panel header structure)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_label = QLabel("Videos")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # List widget with drag-drop
        self.list_widget = QListWidget()
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setMinimumWidth(250)

        # Placeholder text
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ccc;
                border-radius: 5px;
                background-color: #fafafa;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)

        layout.addWidget(self.list_widget)

        # Drop hint label (shown when empty)
        self.drop_hint = QLabel("Drag & drop videos here\nor use buttons below")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_hint.setStyleSheet("color: #999; padding: 20px;")

        # Buttons row
        buttons_layout = QHBoxLayout()

        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.setToolTip("Add video files")
        buttons_layout.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.setToolTip("Add all videos from a folder")
        buttons_layout.addWidget(self.add_folder_btn)

        layout.addLayout(buttons_layout)

        # Segmentation option
        self.sentence_segments_checkbox = QCheckBox("Sentence-level segments")
        self.sentence_segments_checkbox.setChecked(False)
        self.sentence_segments_checkbox.setToolTip(
            "Split transcript at sentence boundaries (., !, ?) instead of speech pauses"
        )
        layout.addWidget(self.sentence_segments_checkbox)

        # Action buttons row
        action_layout = QHBoxLayout()

        self.transcribe_btn = QPushButton("Transcribe Selected")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        action_layout.addWidget(self.transcribe_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Remove all videos")
        action_layout.addWidget(self.clear_btn)

        layout.addLayout(action_layout)

        # Enable drag-drop on the widget itself
        self.setAcceptDrops(True)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self.add_files_btn.clicked.connect(self._on_add_files)
        self.add_folder_btn.clicked.connect(self._on_add_folder)
        self.transcribe_btn.clicked.connect(self._on_transcribe)
        self.clear_btn.clicked.connect(self._on_clear)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemClicked.connect(self._on_item_clicked)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events."""
        urls = event.mimeData().urls()
        paths = []

        for url in urls:
            path = Path(url.toLocalFile())
            if path.is_file() and AudioExtractor.is_supported_file(path):
                paths.append(path)
            elif path.is_dir():
                # Recursively find videos in directory (case-insensitive)
                for ext in AudioExtractor.SUPPORTED_VIDEO_EXTENSIONS:
                    paths.extend(path.rglob(f"*{ext}"))
                    paths.extend(path.rglob(f"*{ext.upper()}"))
                for ext in AudioExtractor.SUPPORTED_AUDIO_EXTENSIONS:
                    paths.extend(path.rglob(f"*{ext}"))
                    paths.extend(path.rglob(f"*{ext.upper()}"))

        # Remove duplicates
        paths = list(set(paths))
        self._add_video_paths(paths)
        event.acceptProposedAction()

    def _on_add_files(self) -> None:
        """Handle add files button click."""
        # Build file filter
        video_exts = " ".join(f"*{ext}" for ext in AudioExtractor.SUPPORTED_VIDEO_EXTENSIONS)
        audio_exts = " ".join(f"*{ext}" for ext in AudioExtractor.SUPPORTED_AUDIO_EXTENSIONS)

        file_filter = f"Media Files ({video_exts} {audio_exts});;Video Files ({video_exts});;Audio Files ({audio_exts});;All Files (*)"

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            file_filter
        )

        if paths:
            self._add_video_paths([Path(p) for p in paths])

    def _on_add_folder(self) -> None:
        """Handle add folder button click."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            folder_path = Path(folder)
            paths = []

            # Search for both lowercase and uppercase extensions
            for ext in AudioExtractor.SUPPORTED_VIDEO_EXTENSIONS:
                paths.extend(folder_path.rglob(f"*{ext}"))
                paths.extend(folder_path.rglob(f"*{ext.upper()}"))
            for ext in AudioExtractor.SUPPORTED_AUDIO_EXTENSIONS:
                paths.extend(folder_path.rglob(f"*{ext}"))
                paths.extend(folder_path.rglob(f"*{ext.upper()}"))

            # Remove duplicates (in case filesystem is case-insensitive)
            paths = list(set(paths))

            if paths:
                self._add_video_paths(paths)
            else:
                QMessageBox.information(
                    self,
                    "No Videos Found",
                    "No supported video files were found in the selected folder."
                )

    def _add_video_paths(self, paths: list[Path]) -> None:
        """Add video paths to the list."""
        added_count = 0
        for path in paths:
            path_str = str(path.resolve())
            if path_str not in self._video_items:
                video_item = VideoItem.from_path(path)
                self._video_items[path_str] = video_item
                self._add_list_item(video_item)
                added_count += 1

        if added_count > 0:
            self._update_ui_state()

    def _add_list_item(self, video_item: VideoItem) -> None:
        """Add a VideoItem to the list widget."""
        item = QListWidgetItem(video_item.filename)
        item.setData(Qt.ItemDataRole.UserRole, str(video_item.file_path.resolve()))
        item.setToolTip(str(video_item.file_path))
        self._update_item_status(item, video_item)
        self.list_widget.addItem(item)

    def _update_item_status(self, item: QListWidgetItem, video_item: VideoItem) -> None:
        """Update the visual status of a list item."""
        status_icons = {
            TranscriptionStatus.PENDING: "",
            TranscriptionStatus.EXTRACTING: "[...] ",
            TranscriptionStatus.TRANSCRIBING: "[>>>] ",
            TranscriptionStatus.COMPLETED: "[OK] ",
            TranscriptionStatus.ERROR: "[!] ",
        }

        status_colors = {
            TranscriptionStatus.PENDING: "#333",
            TranscriptionStatus.EXTRACTING: "#ff9800",
            TranscriptionStatus.TRANSCRIBING: "#2196f3",
            TranscriptionStatus.COMPLETED: "#4caf50",
            TranscriptionStatus.ERROR: "#f44336",
        }

        icon = status_icons.get(video_item.status, "")
        color = status_colors.get(video_item.status, "#333")

        item.setText(f"{icon}{video_item.filename}")
        item.setForeground(Qt.GlobalColor.black)

    def _on_transcribe(self) -> None:
        """Handle transcribe button click."""
        selected_items = self.get_selected_video_items()
        if selected_items:
            self.transcribe_requested.emit(selected_items)

    def _on_clear(self) -> None:
        """Handle clear button click."""
        self.list_widget.clear()
        self._video_items.clear()
        self._update_ui_state()

    def _on_selection_changed(self) -> None:
        """Handle selection changes."""
        has_selection = len(self.list_widget.selectedItems()) > 0
        self.transcribe_btn.setEnabled(has_selection)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click."""
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if path_str and path_str in self._video_items:
            self.video_selected.emit(self._video_items[path_str])

    def _update_ui_state(self) -> None:
        """Update UI state based on current items."""
        has_items = self.list_widget.count() > 0
        self.clear_btn.setEnabled(has_items)

    def get_selected_video_items(self) -> list[VideoItem]:
        """Get the currently selected VideoItems."""
        items = []
        for list_item in self.list_widget.selectedItems():
            path_str = list_item.data(Qt.ItemDataRole.UserRole)
            if path_str and path_str in self._video_items:
                items.append(self._video_items[path_str])
        return items

    def get_all_video_items(self) -> list[VideoItem]:
        """Get all VideoItems in the list."""
        return list(self._video_items.values())

    def update_video_status(self, video_item: VideoItem) -> None:
        """Update the display status of a video item."""
        path_str = str(video_item.file_path.resolve())

        # Find the list item
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == path_str:
                self._update_item_status(item, video_item)
                break

    def get_video_item(self, path: Path | str) -> Optional[VideoItem]:
        """Get a VideoItem by its path."""
        path_str = str(Path(path).resolve())
        return self._video_items.get(path_str)
