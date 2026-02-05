"""JSON format exporter with full metadata."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..models.video_item import VideoItem


class JsonExporter:
    """Export transcriptions as JSON files with full metadata."""

    @staticmethod
    def export(
        video_item: VideoItem,
        output_path: Optional[Path] = None,
        include_metadata: bool = True,
        pretty_print: bool = True
    ) -> Path:
        """
        Export the transcript as a JSON file.

        Args:
            video_item: VideoItem with transcription segments
            output_path: Optional output path. If not provided, uses video
                        filename with .json extension in same directory.
            include_metadata: Whether to include file metadata
            pretty_print: Whether to format JSON with indentation

        Returns:
            Path to the exported file

        Raises:
            ValueError: If video has no transcription
        """
        if not video_item.segments:
            raise ValueError("No transcription available to export")

        # Generate output path if not provided
        if output_path is None:
            output_path = video_item.file_path.with_suffix('.json')
        else:
            output_path = Path(output_path)

        # Build the JSON structure
        data: dict[str, Any] = {}

        if include_metadata:
            data["metadata"] = {
                "source_file": str(video_item.file_path),
                "filename": video_item.filename,
                "exported_at": datetime.now().isoformat(),
                "total_segments": len(video_item.segments),
                "total_duration": video_item.segments[-1].end if video_item.segments else 0,
            }

        # Full text
        data["text"] = video_item.full_text

        # Segments with timestamps
        data["segments"] = [
            {
                "id": i,
                "start": segment.start,
                "end": segment.end,
                "start_formatted": segment.start_timestamp,
                "end_formatted": segment.end_timestamp,
                "text": segment.text.strip(),
                "confidence": segment.confidence,
                "duration": segment.duration,
            }
            for i, segment in enumerate(video_item.segments)
            if segment.text.strip()
        ]

        # Write to file
        indent = 2 if pretty_print else None
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        output_path.write_text(content, encoding='utf-8')

        return output_path

    @staticmethod
    def export_segments_only(
        video_item: VideoItem,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export only the segments array (minimal format).

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
                f"{video_item.file_path.stem}_segments.json"
            )
        else:
            output_path = Path(output_path)

        segments = [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            }
            for segment in video_item.segments
            if segment.text.strip()
        ]

        content = json.dumps(segments, indent=2, ensure_ascii=False)
        output_path.write_text(content, encoding='utf-8')

        return output_path

    @staticmethod
    def to_dict(video_item: VideoItem) -> dict[str, Any]:
        """
        Convert a VideoItem to a dictionary (for API use).

        Args:
            video_item: VideoItem with transcription segments

        Returns:
            Dictionary representation
        """
        return {
            "source_file": str(video_item.file_path),
            "filename": video_item.filename,
            "status": video_item.status.value,
            "text": video_item.full_text,
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": segment.confidence,
                }
                for segment in video_item.segments
                if segment.text.strip()
            ]
        }
