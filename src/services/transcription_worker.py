"""Transcription worker using QThread for non-blocking UI."""

import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from ..models.video_item import VideoItem, TranscriptionSegment, TranscriptionStatus, SegmentationMode, WordTiming
from .audio_extractor import AudioExtractor
from .model_manager import ModelManager, DEFAULT_MODEL

# Sentence-ending punctuation pattern
_SENTENCE_END_RE = re.compile(r'[.!?]$')


def build_sentence_segments(word_data: list[WordTiming]) -> list[TranscriptionSegment]:
    """
    Build sentence-level segments from word timing data.

    Splits at sentence-ending punctuation (., !, ?) to build
    new sentence-based segments with precise word-level timing.
    """
    if not word_data:
        return []

    sentence_segments = []
    current_words = []
    sentence_start = None

    for wt in word_data:
        word_text = wt.word.strip()
        if not word_text:
            continue

        if sentence_start is None:
            sentence_start = wt.start

        current_words.append(word_text)

        # Check if this word ends a sentence
        if _SENTENCE_END_RE.search(word_text):
            sentence_text = " ".join(current_words)
            sentence_segments.append(TranscriptionSegment(
                start=sentence_start,
                end=wt.end,
                text=sentence_text,
            ))
            current_words = []
            sentence_start = None

    # Handle remaining words (no sentence-ending punctuation)
    if current_words:
        last = word_data[-1]
        sentence_segments.append(TranscriptionSegment(
            start=sentence_start if sentence_start is not None else last.start,
            end=last.end,
            text=" ".join(current_words),
        ))

    return sentence_segments


def _store_word_data(video_item: VideoItem, raw_segments: list) -> None:
    """
    Extract and store word timing data from raw Whisper segments onto the VideoItem.
    Each raw segment should have a .words attribute (from word_timestamps=True).
    """
    word_data = []
    for seg in raw_segments:
        if hasattr(seg, 'words') and seg.words:
            for w in seg.words:
                word_data.append(WordTiming(start=w.start, end=w.end, word=w.word))
    video_item.word_data = word_data


class TranscriptionWorker(QThread):
    """
    Worker thread for transcribing video files.

    Signals:
        progress: Emitted with (video_item, progress_percent, status_message)
        segment_ready: Emitted when a new segment is transcribed
        completed: Emitted when transcription is complete
        error: Emitted when an error occurs
    """

    progress = Signal(VideoItem, float, str)
    segment_ready = Signal(VideoItem, TranscriptionSegment)
    completed = Signal(VideoItem)
    error = Signal(VideoItem, str)

    def __init__(
        self,
        video_item: VideoItem,
        model_manager: ModelManager,
        model_name: str = DEFAULT_MODEL,
        segment_mode: str = SegmentationMode.NATURAL_PAUSES,
        parent=None
    ):
        """
        Initialize the transcription worker.

        Args:
            video_item: The video item to transcribe
            model_manager: Shared model manager instance
            model_name: Whisper model to use
            segment_mode: Segmentation mode (natural_pauses or sentence_level)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.video_item = video_item
        self.model_manager = model_manager
        self.model_name = model_name
        self.segment_mode = segment_mode
        self._is_cancelled = False
        self._audio_extractor: Optional[AudioExtractor] = None

    def cancel(self) -> None:
        """Request cancellation of the transcription."""
        self._is_cancelled = True

    def run(self) -> None:
        """Run the transcription process."""
        try:
            self._transcribe()
        except Exception as e:
            self.video_item.set_error(str(e))
            self.error.emit(self.video_item, str(e))
        finally:
            # Cleanup
            if self._audio_extractor:
                self._audio_extractor.cleanup()

    def _transcribe(self) -> None:
        """Internal transcription logic."""
        if self._is_cancelled:
            return

        video_path = self.video_item.file_path

        # Validate file exists
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Update status: extracting audio
        self.video_item.status = TranscriptionStatus.EXTRACTING
        self.video_item.progress = 5.0
        self.progress.emit(self.video_item, 5.0, "Extracting audio...")

        if self._is_cancelled:
            return

        # Extract audio
        self._audio_extractor = AudioExtractor()
        audio_path = self._audio_extractor.extract_audio(video_path)

        if self._is_cancelled:
            return

        # Update status: loading model
        self.video_item.progress = 10.0
        self.progress.emit(self.video_item, 10.0, "Loading model...")

        # Load model (will use cached if already loaded)
        model = self.model_manager.load_model(self.model_name)

        if self._is_cancelled:
            return

        # Update status: transcribing
        self.video_item.status = TranscriptionStatus.TRANSCRIBING
        self.video_item.progress = 15.0
        self.progress.emit(self.video_item, 15.0, "Transcribing...")

        # Clear any previous segments
        self.video_item.segments = []

        # Always use word_timestamps so we can switch segmentation modes after the fact
        segments_iter, info = model.transcribe(
            str(audio_path),
            beam_size=5,
            language=None,  # Auto-detect
            vad_filter=True,  # Voice activity detection
            vad_parameters=dict(
                min_silence_duration_ms=500,
            ),
            word_timestamps=True,
        )

        # Get total duration for progress calculation
        total_duration = info.duration if info.duration > 0 else 1.0

        # Collect raw segments for word data extraction
        raw_segments = []

        # Process segments
        for segment in segments_iter:
            if self._is_cancelled:
                return

            raw_segments.append(segment)

            # Create segment object
            transcription_segment = TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                confidence=segment.avg_logprob if hasattr(segment, 'avg_logprob') else 1.0
            )

            # Add to video item
            self.video_item.segments.append(transcription_segment)

            # Emit segment signal for live preview
            self.segment_ready.emit(self.video_item, transcription_segment)

            # Calculate and emit progress (15% to 95% range for transcription)
            progress_pct = 15.0 + (segment.end / total_duration) * 80.0
            progress_pct = min(progress_pct, 95.0)
            self.video_item.progress = progress_pct
            self.progress.emit(
                self.video_item,
                progress_pct,
                f"Transcribing... ({int(segment.end)}/{int(total_duration)}s)"
            )

        if self._is_cancelled:
            return

        # Store original segments and word data for post-hoc mode switching
        self.video_item.original_segments = list(self.video_item.segments)
        _store_word_data(self.video_item, raw_segments)

        # Post-process: resegment by sentences if requested
        use_sentence_mode = self.segment_mode == SegmentationMode.SENTENCE_LEVEL
        if use_sentence_mode and self.video_item.word_data:
            self.video_item.progress = 96.0
            self.progress.emit(self.video_item, 96.0, "Resegmenting by sentences...")
            sentence_segs = build_sentence_segments(self.video_item.word_data)
            if sentence_segs:
                self.video_item.segments = sentence_segs

        # Complete
        self.video_item.status = TranscriptionStatus.COMPLETED
        self.video_item.progress = 100.0
        self.progress.emit(self.video_item, 100.0, "Complete")
        self.completed.emit(self.video_item)


class BatchTranscriptionWorker(QThread):
    """
    Worker thread for batch transcription of multiple videos.

    Signals:
        item_started: Emitted when starting a new video
        item_progress: Emitted with progress updates for current video
        item_completed: Emitted when a video is completed
        item_error: Emitted when a video has an error
        batch_completed: Emitted when all videos are done
    """

    item_started = Signal(VideoItem)
    item_progress = Signal(VideoItem, float, str)
    item_completed = Signal(VideoItem)
    item_error = Signal(VideoItem, str)
    batch_completed = Signal()

    def __init__(
        self,
        video_items: list[VideoItem],
        model_manager: ModelManager,
        model_name: str = DEFAULT_MODEL,
        segment_mode: str = SegmentationMode.NATURAL_PAUSES,
        parent=None
    ):
        """
        Initialize the batch transcription worker.

        Args:
            video_items: List of video items to transcribe
            model_manager: Shared model manager instance
            model_name: Whisper model to use
            segment_mode: Segmentation mode (natural_pauses or sentence_level)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.video_items = video_items
        self.model_manager = model_manager
        self.model_name = model_name
        self.segment_mode = segment_mode
        self._is_cancelled = False
        self._current_worker: Optional[TranscriptionWorker] = None

    def cancel(self) -> None:
        """Request cancellation of the batch."""
        self._is_cancelled = True
        if self._current_worker:
            self._current_worker.cancel()

    def run(self) -> None:
        """Run the batch transcription process."""
        for video_item in self.video_items:
            if self._is_cancelled:
                break

            # Skip already transcribed items
            if video_item.is_transcribed:
                continue

            # Skip items with errors (allow retry by clearing error first)
            if video_item.has_error:
                continue

            self.item_started.emit(video_item)

            try:
                self._transcribe_single(video_item)
                self.item_completed.emit(video_item)
            except Exception as e:
                video_item.set_error(str(e))
                self.item_error.emit(video_item, str(e))

        self.batch_completed.emit()

    def _transcribe_single(self, video_item: VideoItem) -> None:
        """Transcribe a single video item synchronously."""
        audio_extractor = None
        try:
            # Extract audio
            video_item.status = TranscriptionStatus.EXTRACTING
            video_item.progress = 5.0
            self.item_progress.emit(video_item, 5.0, "Extracting audio...")

            if self._is_cancelled:
                return

            audio_extractor = AudioExtractor()
            audio_path = audio_extractor.extract_audio(video_item.file_path)

            if self._is_cancelled:
                return

            # Load model
            video_item.progress = 10.0
            self.item_progress.emit(video_item, 10.0, "Loading model...")
            model = self.model_manager.load_model(self.model_name)

            if self._is_cancelled:
                return

            # Transcribe
            video_item.status = TranscriptionStatus.TRANSCRIBING
            video_item.progress = 15.0
            self.item_progress.emit(video_item, 15.0, "Transcribing...")

            video_item.segments = []

            # Always use word_timestamps for post-hoc mode switching
            segments_iter, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                language=None,
                vad_filter=True,
                word_timestamps=True,
            )

            total_duration = info.duration if info.duration > 0 else 1.0
            raw_segments = []

            for segment in segments_iter:
                if self._is_cancelled:
                    return

                raw_segments.append(segment)

                transcription_segment = TranscriptionSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    confidence=segment.avg_logprob if hasattr(segment, 'avg_logprob') else 1.0
                )
                video_item.segments.append(transcription_segment)

                progress_pct = 15.0 + (segment.end / total_duration) * 80.0
                progress_pct = min(progress_pct, 95.0)
                video_item.progress = progress_pct
                self.item_progress.emit(
                    video_item,
                    progress_pct,
                    f"Transcribing... ({int(segment.end)}/{int(total_duration)}s)"
                )

            if self._is_cancelled:
                return

            # Store original segments and word data for post-hoc mode switching
            video_item.original_segments = list(video_item.segments)
            _store_word_data(video_item, raw_segments)

            # Post-process: resegment by sentences if requested
            use_sentence_mode = self.segment_mode == SegmentationMode.SENTENCE_LEVEL
            if use_sentence_mode and video_item.word_data:
                video_item.progress = 96.0
                self.item_progress.emit(video_item, 96.0, "Resegmenting by sentences...")
                sentence_segs = build_sentence_segments(video_item.word_data)
                if sentence_segs:
                    video_item.segments = sentence_segs

            video_item.status = TranscriptionStatus.COMPLETED
            video_item.progress = 100.0
            self.item_progress.emit(video_item, 100.0, "Complete")

        finally:
            if audio_extractor:
                audio_extractor.cleanup()
