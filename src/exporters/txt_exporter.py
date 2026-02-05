"""Plain text transcript exporter."""

from pathlib import Path
from typing import Optional

from ..models.video_item import VideoItem


class TxtExporter:
    """Export transcriptions as plain text files."""

    @staticmethod
    def export(
        video_item: VideoItem,
        output_path: Optional[Path] = None,
        include_timestamps: bool = False
    ) -> Path:
        """
        Export the transcript as a plain text file.

        Args:
            video_item: VideoItem with transcription segments
            output_path: Optional output path. If not provided, uses video
                        filename with .txt extension in same directory.
            include_timestamps: Whether to include timestamps in the export

        Returns:
            Path to the exported file

        Raises:
            ValueError: If video has no transcription
        """
        if not video_item.segments:
            raise ValueError("No transcription available to export")

        # Generate output path if not provided
        if output_path is None:
            output_path = video_item.file_path.with_suffix('.txt')
        else:
            output_path = Path(output_path)

        # Build the transcript text with proper paragraph spacing
        lines = []
        for segment in video_item.segments:
            text = segment.text.strip()
            if text:
                if include_timestamps:
                    timestamp = f"[{segment.start_timestamp_simple}]"
                    lines.append(f"{timestamp} {text}")
                else:
                    lines.append(text)

        # Join with double newlines for paragraph spacing (matches view)
        content = "\n\n".join(lines)

        # Write to file
        output_path.write_text(content, encoding='utf-8')

        return output_path

    @staticmethod
    def export_with_timestamps(
        video_item: VideoItem,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export the transcript with timestamps.

        Args:
            video_item: VideoItem with transcription segments
            output_path: Optional output path

        Returns:
            Path to the exported file
        """
        if not video_item.segments:
            raise ValueError("No transcription available to export")

        if output_path is None:
            output_path = video_item.file_path.with_name(
                f"{video_item.file_path.stem}_timestamped.txt"
            )
        else:
            output_path = Path(output_path)

        lines = []
        for segment in video_item.segments:
            timestamp = f"[{segment.start_timestamp} --> {segment.end_timestamp}]"
            text = segment.text.strip()
            if text:
                lines.append(f"{timestamp}\n{text}\n")

        content = "\n".join(lines)
        output_path.write_text(content, encoding='utf-8')

        return output_path
