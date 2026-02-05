"""SRT subtitle format exporter."""

from pathlib import Path
from typing import Optional

from ..models.video_item import VideoItem


class SrtExporter:
    """Export transcriptions as SRT subtitle files."""

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Format seconds to SRT timestamp format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @staticmethod
    def export(video_item: VideoItem, output_path: Optional[Path] = None) -> Path:
        """
        Export the transcript as an SRT subtitle file.

        SRT format:
        1
        00:00:00,000 --> 00:00:05,000
        First subtitle text

        2
        00:00:05,000 --> 00:00:10,000
        Second subtitle text

        Args:
            video_item: VideoItem with transcription segments
            output_path: Optional output path. If not provided, uses video
                        filename with .srt extension in same directory.

        Returns:
            Path to the exported file

        Raises:
            ValueError: If video has no transcription
        """
        if not video_item.segments:
            raise ValueError("No transcription available to export")

        # Generate output path if not provided
        if output_path is None:
            output_path = video_item.file_path.with_suffix('.srt')
        else:
            output_path = Path(output_path)

        # Build the SRT content
        lines = []
        for i, segment in enumerate(video_item.segments, start=1):
            text = segment.text.strip()
            if not text:
                continue

            # Sequence number
            lines.append(str(i))

            # Timestamps
            start_ts = SrtExporter.format_timestamp(segment.start)
            end_ts = SrtExporter.format_timestamp(segment.end)
            lines.append(f"{start_ts} --> {end_ts}")

            # Text (can be multi-line, but we'll keep it simple)
            lines.append(text)

            # Blank line separator
            lines.append("")

        content = "\n".join(lines)

        # Write to file
        output_path.write_text(content, encoding='utf-8')

        return output_path
