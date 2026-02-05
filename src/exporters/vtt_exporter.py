"""WebVTT subtitle format exporter."""

from pathlib import Path
from typing import Optional

from ..models.video_item import VideoItem


class VttExporter:
    """Export transcriptions as WebVTT subtitle files."""

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """
        Format seconds to VTT timestamp format (HH:MM:SS.mmm).

        Note: VTT uses period (.) instead of comma (,) for milliseconds.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    @staticmethod
    def export(video_item: VideoItem, output_path: Optional[Path] = None) -> Path:
        """
        Export the transcript as a WebVTT subtitle file.

        VTT format:
        WEBVTT

        00:00:00.000 --> 00:00:05.000
        First subtitle text

        00:00:05.000 --> 00:00:10.000
        Second subtitle text

        Args:
            video_item: VideoItem with transcription segments
            output_path: Optional output path. If not provided, uses video
                        filename with .vtt extension in same directory.

        Returns:
            Path to the exported file

        Raises:
            ValueError: If video has no transcription
        """
        if not video_item.segments:
            raise ValueError("No transcription available to export")

        # Generate output path if not provided
        if output_path is None:
            output_path = video_item.file_path.with_suffix('.vtt')
        else:
            output_path = Path(output_path)

        # Build the VTT content
        lines = ["WEBVTT", ""]  # Header and blank line

        for segment in video_item.segments:
            text = segment.text.strip()
            if not text:
                continue

            # Timestamps (VTT doesn't require sequence numbers)
            start_ts = VttExporter.format_timestamp(segment.start)
            end_ts = VttExporter.format_timestamp(segment.end)
            lines.append(f"{start_ts} --> {end_ts}")

            # Text
            lines.append(text)

            # Blank line separator
            lines.append("")

        content = "\n".join(lines)

        # Write to file
        output_path.write_text(content, encoding='utf-8')

        return output_path

    @staticmethod
    def export_with_metadata(
        video_item: VideoItem,
        output_path: Optional[Path] = None,
        title: Optional[str] = None
    ) -> Path:
        """
        Export with optional VTT metadata header.

        Args:
            video_item: VideoItem with transcription segments
            output_path: Optional output path
            title: Optional title for the VTT file

        Returns:
            Path to the exported file
        """
        if not video_item.segments:
            raise ValueError("No transcription available to export")

        if output_path is None:
            output_path = video_item.file_path.with_suffix('.vtt')
        else:
            output_path = Path(output_path)

        # Build VTT with metadata
        lines = ["WEBVTT"]

        if title:
            lines.append(f"Title: {title}")

        lines.append("")  # Blank line after header

        for segment in video_item.segments:
            text = segment.text.strip()
            if not text:
                continue

            start_ts = VttExporter.format_timestamp(segment.start)
            end_ts = VttExporter.format_timestamp(segment.end)
            lines.append(f"{start_ts} --> {end_ts}")
            lines.append(text)
            lines.append("")

        content = "\n".join(lines)
        output_path.write_text(content, encoding='utf-8')

        return output_path
