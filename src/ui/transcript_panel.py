"""Transcript panel widget for displaying and exporting transcriptions."""

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QProgressBar,
    QComboBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
)

from ..models.video_item import VideoItem, TranscriptionSegment
from ..exporters import TxtExporter, SrtExporter, VttExporter, JsonExporter


class TranscriptPanel(QWidget):
    """
    Widget for displaying transcription results and export controls.
    """

    # Format indices
    FORMAT_TXT = 0
    FORMAT_SRT = 1
    FORMAT_VTT = 2
    FORMAT_JSON = 3

    # Styles
    STYLE_NORMAL = """
        QTextEdit {
            border: 2px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background-color: #ffffff;
            color: #1a1a1a;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            line-height: 1.5;
        }
    """

    STYLE_EDIT_MODE = """
        QTextEdit {
            border: 2px solid #ff9800;
            border-radius: 4px;
            padding: 10px;
            background-color: #fffdf5;
            color: #1a1a1a;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 13px;
            line-height: 1.5;
        }
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the transcript panel."""
        super().__init__(parent)
        self._current_video: Optional[VideoItem] = None
        self._is_edit_mode = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with video name
        header_layout = QHBoxLayout()

        self.header_label = QLabel("Transcript")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.header_label)

        self.video_name_label = QLabel("")
        self.video_name_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.video_name_label, 1)

        # Edit mode indicator
        self.edit_mode_label = QLabel("EDITING")
        self.edit_mode_label.setStyleSheet("""
            QLabel {
                background-color: #ff9800;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.edit_mode_label.hide()
        header_layout.addWidget(self.edit_mode_label)

        layout.addLayout(header_layout)

        # Progress section
        self.progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666;")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(self.progress_group)
        self.progress_group.hide()  # Hidden until transcription starts

        # View options
        view_options_layout = QHBoxLayout()

        self.show_timestamps_checkbox = QCheckBox("Show timestamps")
        self.show_timestamps_checkbox.setChecked(True)
        self.show_timestamps_checkbox.setToolTip("Toggle timestamp display in preview")
        view_options_layout.addWidget(self.show_timestamps_checkbox)

        view_options_layout.addStretch()

        # Edit button
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setEnabled(False)
        self.edit_btn.setCheckable(True)
        self.edit_btn.setToolTip("Toggle edit mode to modify transcript")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #ff9800;
                color: white;
                border: none;
            }
        """)
        view_options_layout.addWidget(self.edit_btn)

        layout.addLayout(view_options_layout)

        # Transcript text area
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setPlaceholderText(
            "Select a video and click 'Transcribe' to generate a transcript.\n\n"
            "Supported formats: MP4, MKV, AVI, MOV, WMV, FLV, WebM, and more."
        )
        self.transcript_text.setStyleSheet(self.STYLE_NORMAL)
        layout.addWidget(self.transcript_text, 1)

        # Export section
        export_group = QGroupBox("Export")
        export_layout = QHBoxLayout(export_group)

        export_layout.addWidget(QLabel("Format:"))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["TXT (Plain Text)", "SRT (Subtitles)", "VTT (Web Subtitles)", "JSON (Structured)"])
        self.format_combo.setMinimumWidth(150)
        export_layout.addWidget(self.format_combo)

        self.export_btn = QPushButton("Export")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #43a047;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        export_layout.addWidget(self.export_btn)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setEnabled(False)
        self.copy_btn.setToolTip("Copy transcript to clipboard")
        export_layout.addWidget(self.copy_btn)

        export_layout.addStretch()

        layout.addWidget(export_group)

    def _connect_signals(self) -> None:
        """Connect widget signals to slots."""
        self.export_btn.clicked.connect(self._on_export)
        self.copy_btn.clicked.connect(self._on_copy)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.show_timestamps_checkbox.stateChanged.connect(self._on_timestamps_toggled)
        self.edit_btn.clicked.connect(self._on_edit_toggled)

    def _on_edit_toggled(self) -> None:
        """Handle edit button toggle."""
        if self.edit_btn.isChecked():
            self._enter_edit_mode()
        else:
            self._exit_edit_mode()

    def _enter_edit_mode(self) -> None:
        """Enter edit mode."""
        if not self._current_video or not self._current_video.is_transcribed:
            self.edit_btn.setChecked(False)
            return

        self._is_edit_mode = True

        # Show edit mode indicator
        self.edit_mode_label.show()

        # Change text area style and make editable
        self.transcript_text.setStyleSheet(self.STYLE_EDIT_MODE)
        self.transcript_text.setReadOnly(False)

        # Force TXT format with timestamps for editing
        self.format_combo.setCurrentIndex(self.FORMAT_TXT)
        self.show_timestamps_checkbox.setChecked(True)

        # Disable controls that shouldn't change during edit
        self.format_combo.setEnabled(False)
        self.show_timestamps_checkbox.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)

        # Display in editable format
        self._display_txt_format(self._current_video, show_timestamps=True)

    def _exit_edit_mode(self) -> None:
        """Exit edit mode and save changes."""
        if not self._current_video:
            return

        # Parse the edited text back into segments
        self._parse_edited_text()

        self._is_edit_mode = False

        # Hide edit mode indicator
        self.edit_mode_label.hide()

        # Restore normal style and read-only
        self.transcript_text.setStyleSheet(self.STYLE_NORMAL)
        self.transcript_text.setReadOnly(True)

        # Re-enable controls
        self.format_combo.setEnabled(True)
        self._on_format_changed(self.format_combo.currentIndex())  # Restore checkbox state
        self.export_btn.setEnabled(True)
        self.copy_btn.setEnabled(True)

        # Refresh display
        self._refresh_display()

    def _parse_edited_text(self) -> None:
        """Parse the edited text and update segments."""
        if not self._current_video:
            return

        text = self.transcript_text.toPlainText()
        lines = text.split("\n\n")

        # Pattern to match [HH:MM:SS] timestamp
        timestamp_pattern = re.compile(r'^\[(\d{2}):(\d{2}):(\d{2})\]\s*(.*)$')

        new_segments = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            match = timestamp_pattern.match(line)
            if match:
                hours, minutes, seconds, text_content = match.groups()
                start_time = int(hours) * 3600 + int(minutes) * 60 + int(seconds)

                # Try to get end time from next segment, or estimate
                end_time = start_time + 5  # Default 5 second duration

                # Look for original segment with similar start time to get end time
                for orig_seg in self._current_video.segments:
                    if abs(orig_seg.start - start_time) < 2:  # Within 2 seconds
                        end_time = orig_seg.end
                        break

                if text_content.strip():
                    new_segments.append(TranscriptionSegment(
                        start=float(start_time),
                        end=float(end_time),
                        text=text_content.strip(),
                        confidence=1.0
                    ))
            else:
                # No timestamp - try to associate with previous segment's timing
                if new_segments:
                    # Append to previous segment
                    prev = new_segments[-1]
                    new_segments[-1] = TranscriptionSegment(
                        start=prev.start,
                        end=prev.end,
                        text=prev.text + " " + line,
                        confidence=prev.confidence
                    )
                elif self._current_video.segments:
                    # Use first original segment's timing
                    orig = self._current_video.segments[0]
                    new_segments.append(TranscriptionSegment(
                        start=orig.start,
                        end=orig.end,
                        text=line,
                        confidence=1.0
                    ))

        # Update the video item's segments
        if new_segments:
            self._current_video.segments = new_segments

    def _on_format_changed(self, index: int) -> None:
        """Handle format selection change - update preview and checkbox state."""
        if self._is_edit_mode:
            return

        # SRT and VTT require timestamps - grey out checkbox
        requires_timestamps = index in (self.FORMAT_SRT, self.FORMAT_VTT)

        if requires_timestamps:
            self.show_timestamps_checkbox.setChecked(True)
            self.show_timestamps_checkbox.setEnabled(False)
            self.show_timestamps_checkbox.setToolTip("Timestamps required for this format")
        else:
            self.show_timestamps_checkbox.setEnabled(True)
            self.show_timestamps_checkbox.setToolTip("Toggle timestamp display in preview")

        # Update the preview
        self._refresh_display()

    def _on_timestamps_toggled(self, state: int) -> None:
        """Handle timestamp checkbox toggle."""
        if not self._is_edit_mode:
            self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the transcript display based on current settings."""
        if self._is_edit_mode:
            return
        if self._current_video and self._current_video.is_transcribed:
            self._display_transcript(self._current_video)

    def set_video(self, video_item: VideoItem) -> None:
        """Set the current video item to display."""
        # Exit edit mode if switching videos
        if self._is_edit_mode:
            self.edit_btn.setChecked(False)
            self._exit_edit_mode()

        self._current_video = video_item
        self.video_name_label.setText(video_item.filename)

        # Update transcript display
        if video_item.is_transcribed:
            self._display_transcript(video_item)
            self.export_btn.setEnabled(True)
            self.copy_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
        else:
            self.transcript_text.clear()
            self.transcript_text.setPlaceholderText(
                f"Click 'Transcribe' to generate transcript for:\n{video_item.filename}"
            )
            self.export_btn.setEnabled(False)
            self.copy_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)

        # Update progress display
        self._update_progress_display(video_item)

    def _display_transcript(self, video_item: VideoItem) -> None:
        """Display the transcript based on selected format and options."""
        format_idx = self.format_combo.currentIndex()
        show_timestamps = self.show_timestamps_checkbox.isChecked()

        if format_idx == self.FORMAT_TXT:
            self._display_txt_format(video_item, show_timestamps)
        elif format_idx == self.FORMAT_SRT:
            self._display_srt_format(video_item)
        elif format_idx == self.FORMAT_VTT:
            self._display_vtt_format(video_item)
        elif format_idx == self.FORMAT_JSON:
            self._display_json_format(video_item, show_timestamps)

    def _display_txt_format(self, video_item: VideoItem, show_timestamps: bool) -> None:
        """Display as plain text format."""
        lines = []
        for segment in video_item.segments:
            text = segment.text.strip()
            if text:
                if show_timestamps:
                    timestamp = f"[{segment.start_timestamp_simple}]"
                    lines.append(f"{timestamp} {text}")
                else:
                    lines.append(text)

        self.transcript_text.setText("\n\n".join(lines))

    def _display_srt_format(self, video_item: VideoItem) -> None:
        """Display as SRT subtitle format."""
        lines = []
        counter = 1
        for segment in video_item.segments:
            text = segment.text.strip()
            if text:
                lines.append(str(counter))
                lines.append(f"{segment.start_timestamp} --> {segment.end_timestamp}")
                lines.append(text)
                lines.append("")
                counter += 1

        self.transcript_text.setText("\n".join(lines))

    def _display_vtt_format(self, video_item: VideoItem) -> None:
        """Display as WebVTT subtitle format."""
        lines = ["WEBVTT", ""]
        for segment in video_item.segments:
            text = segment.text.strip()
            if text:
                # VTT uses period instead of comma for milliseconds
                start_ts = segment.start_timestamp.replace(",", ".")
                end_ts = segment.end_timestamp.replace(",", ".")
                lines.append(f"{start_ts} --> {end_ts}")
                lines.append(text)
                lines.append("")

        self.transcript_text.setText("\n".join(lines))

    def _display_json_format(self, video_item: VideoItem, show_timestamps: bool) -> None:
        """Display as JSON format preview."""
        import json

        if show_timestamps:
            data = {
                "segments": [
                    {
                        "start": f"{segment.start_timestamp_simple}",
                        "end": f"{segment.end_timestamp_simple}",
                        "text": segment.text.strip()
                    }
                    for segment in video_item.segments
                    if segment.text.strip()
                ]
            }
        else:
            data = {
                "text": video_item.full_text,
                "segments": [
                    {"text": segment.text.strip()}
                    for segment in video_item.segments
                    if segment.text.strip()
                ]
            }

        self.transcript_text.setText(json.dumps(data, indent=2, ensure_ascii=False))

    def _update_progress_display(self, video_item: VideoItem) -> None:
        """Update the progress bar and status label."""
        if video_item.is_processing:
            self.progress_group.show()
            self.progress_bar.setValue(int(video_item.progress))
        elif video_item.is_transcribed:
            self.progress_group.hide()
        elif video_item.has_error:
            self.progress_group.show()
            self.progress_bar.setValue(0)
            self.status_label.setText(f"Error: {video_item.error_message}")
            self.status_label.setStyleSheet("color: #f44336;")
        else:
            self.progress_group.hide()

    def update_progress(self, video_item: VideoItem, progress: float, status: str) -> None:
        """Update the progress display during transcription."""
        if self._current_video == video_item:
            self.progress_group.show()
            self.progress_bar.setValue(int(progress))
            self.status_label.setText(status)
            self.status_label.setStyleSheet("color: #1976d2;")

    def append_segment(self, video_item: VideoItem, segment: TranscriptionSegment) -> None:
        """Append a new segment to the live transcript display."""
        if self._is_edit_mode:
            return
        if self._current_video == video_item:
            text = segment.text.strip()
            if text:
                show_timestamps = self.show_timestamps_checkbox.isChecked()
                if show_timestamps:
                    timestamp = f"[{segment.start_timestamp_simple}]"
                    new_line = f"{timestamp} {text}"
                else:
                    new_line = text

                current_text = self.transcript_text.toPlainText()
                if current_text:
                    new_text = f"{current_text}\n\n{new_line}"
                else:
                    new_text = new_line
                self.transcript_text.setText(new_text)

                # Scroll to bottom
                scrollbar = self.transcript_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

    def on_transcription_complete(self, video_item: VideoItem) -> None:
        """Handle transcription completion."""
        if self._current_video == video_item:
            self.progress_group.hide()
            self.status_label.setText("Complete")
            self.status_label.setStyleSheet("color: #4caf50;")
            self.export_btn.setEnabled(True)
            self.copy_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)

            # Refresh display with final transcript
            self._display_transcript(video_item)

    def on_transcription_error(self, video_item: VideoItem, error: str) -> None:
        """Handle transcription error."""
        if self._current_video == video_item:
            self.progress_group.show()
            self.progress_bar.setValue(0)
            self.status_label.setText(f"Error: {error}")
            self.status_label.setStyleSheet("color: #f44336;")

    def _on_export(self) -> None:
        """Handle export button click."""
        if not self._current_video or not self._current_video.is_transcribed:
            return

        format_idx = self.format_combo.currentIndex()
        format_info = [
            ("TXT", ".txt", TxtExporter),
            ("SRT", ".srt", SrtExporter),
            ("VTT", ".vtt", VttExporter),
            ("JSON", ".json", JsonExporter),
        ]

        format_name, extension, exporter_class = format_info[format_idx]

        # Get save path
        default_name = self._current_video.file_path.stem + extension
        default_path = str(self._current_video.file_path.parent / default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export as {format_name}",
            default_path,
            f"{format_name} Files (*{extension})"
        )

        if not file_path:
            return

        try:
            # For TXT format, respect the timestamp checkbox
            if format_idx == self.FORMAT_TXT:
                include_timestamps = self.show_timestamps_checkbox.isChecked()
                exporter_class.export(self._current_video, Path(file_path), include_timestamps=include_timestamps)
            else:
                exporter_class.export(self._current_video, Path(file_path))
            QMessageBox.information(
                self,
                "Export Successful",
                f"Transcript exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export transcript:\n{str(e)}"
            )

    def _on_copy(self) -> None:
        """Copy transcript to clipboard (copies current view)."""
        if not self._current_video or not self._current_video.is_transcribed:
            return

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.transcript_text.toPlainText())

        # Show brief feedback
        original_text = self.copy_btn.text()
        self.copy_btn.setText("Copied!")
        self.copy_btn.setEnabled(False)

        # Reset after short delay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._reset_copy_button(original_text))

    def _reset_copy_button(self, text: str) -> None:
        """Reset copy button after feedback."""
        self.copy_btn.setText(text)
        self.copy_btn.setEnabled(True)

    def clear(self) -> None:
        """Clear the panel."""
        if self._is_edit_mode:
            self.edit_btn.setChecked(False)
            self._is_edit_mode = False
            self.edit_mode_label.hide()
            self.transcript_text.setStyleSheet(self.STYLE_NORMAL)
            self.transcript_text.setReadOnly(True)

        self._current_video = None
        self.video_name_label.setText("")
        self.transcript_text.clear()
        self.progress_group.hide()
        self.export_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
