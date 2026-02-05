"""Data models for video items and transcription results."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class TranscriptionStatus(Enum):
    """Status of a video item's transcription."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class TranscriptionSegment:
    """A single segment of transcribed text with timing information."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text
    confidence: float = 1.0  # Confidence score (0-1)

    @property
    def duration(self) -> float:
        """Duration of the segment in seconds."""
        return self.end - self.start

    def format_timestamp(self, time_seconds: float, include_ms: bool = True) -> str:
        """Format a time in seconds to HH:MM:SS,mmm or HH:MM:SS.mmm format."""
        hours = int(time_seconds // 3600)
        minutes = int((time_seconds % 3600) // 60)
        seconds = int(time_seconds % 60)
        milliseconds = int((time_seconds % 1) * 1000)

        if include_ms:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def start_timestamp(self) -> str:
        """Start time formatted as HH:MM:SS,mmm (for SRT/VTT export)."""
        return self.format_timestamp(self.start)

    @property
    def end_timestamp(self) -> str:
        """End time formatted as HH:MM:SS,mmm (for SRT/VTT export)."""
        return self.format_timestamp(self.end)

    @property
    def start_timestamp_simple(self) -> str:
        """Start time formatted as HH:MM:SS (for display)."""
        return self.format_timestamp(self.start, include_ms=False)

    @property
    def end_timestamp_simple(self) -> str:
        """End time formatted as HH:MM:SS (for display)."""
        return self.format_timestamp(self.end, include_ms=False)


@dataclass
class VideoItem:
    """Represents a video file and its transcription state."""
    file_path: Path
    status: TranscriptionStatus = TranscriptionStatus.PENDING
    segments: list[TranscriptionSegment] = field(default_factory=list)
    error_message: Optional[str] = None
    progress: float = 0.0  # 0-100

    def __post_init__(self):
        """Ensure file_path is a Path object."""
        if isinstance(self.file_path, str):
            self.file_path = Path(self.file_path)

    @property
    def filename(self) -> str:
        """Return just the filename without path."""
        return self.file_path.name

    @property
    def full_text(self) -> str:
        """Return the full transcript as a single string."""
        return " ".join(segment.text.strip() for segment in self.segments)

    @property
    def exists(self) -> bool:
        """Check if the video file exists."""
        return self.file_path.exists()

    @property
    def is_transcribed(self) -> bool:
        """Check if transcription is complete."""
        return self.status == TranscriptionStatus.COMPLETED and len(self.segments) > 0

    @property
    def has_error(self) -> bool:
        """Check if there was an error during transcription."""
        return self.status == TranscriptionStatus.ERROR

    @property
    def is_processing(self) -> bool:
        """Check if the video is currently being processed."""
        return self.status in (
            TranscriptionStatus.EXTRACTING,
            TranscriptionStatus.TRANSCRIBING
        )

    def clear_transcription(self) -> None:
        """Clear the transcription data and reset status."""
        self.segments = []
        self.status = TranscriptionStatus.PENDING
        self.error_message = None
        self.progress = 0.0

    def set_error(self, message: str) -> None:
        """Set error status with a message."""
        self.status = TranscriptionStatus.ERROR
        self.error_message = message
        self.progress = 0.0

    @classmethod
    def from_path(cls, path: str | Path) -> "VideoItem":
        """Create a VideoItem from a file path."""
        return cls(file_path=Path(path))

    def __hash__(self) -> int:
        """Hash based on file path for use in sets/dicts."""
        return hash(self.file_path)

    def __eq__(self, other: object) -> bool:
        """Equality based on file path."""
        if isinstance(other, VideoItem):
            return self.file_path == other.file_path
        return False
