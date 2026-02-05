"""Audio extraction service using ffmpeg."""

import os
import sys
import tempfile
from pathlib import Path

import ffmpeg


def _setup_ffmpeg_path():
    """Set up PATH to include bundled ffmpeg when running as PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        bin_dir = bundle_dir / 'bin'
        if bin_dir.exists():
            # Add bin directory to PATH
            os.environ['PATH'] = str(bin_dir) + os.pathsep + os.environ.get('PATH', '')


# Set up ffmpeg path on import
_setup_ffmpeg_path()


class AudioExtractor:
    """Extract audio from video files using ffmpeg."""

    SUPPORTED_VIDEO_EXTENSIONS = {
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.mpeg', '.mpg', '.3gp', '.ogv'
    }

    SUPPORTED_AUDIO_EXTENSIONS = {
        '.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma'
    }

    def __init__(self):
        """Initialize the audio extractor."""
        self._temp_dir = tempfile.mkdtemp(prefix="video_transcript_")

    @classmethod
    def is_supported_file(cls, file_path: Path | str) -> bool:
        """Check if the file is a supported video or audio format."""
        path = Path(file_path)
        ext = path.suffix.lower()
        return ext in cls.SUPPORTED_VIDEO_EXTENSIONS or ext in cls.SUPPORTED_AUDIO_EXTENSIONS

    @classmethod
    def is_audio_file(cls, file_path: Path | str) -> bool:
        """Check if the file is an audio file (no extraction needed)."""
        path = Path(file_path)
        return path.suffix.lower() in cls.SUPPORTED_AUDIO_EXTENSIONS

    def extract_audio(self, video_path: Path | str, output_path: Path | str | None = None) -> Path:
        """
        Extract audio from a video file.

        Args:
            video_path: Path to the video file
            output_path: Optional path for the output WAV file.
                        If not provided, creates a temp file.

        Returns:
            Path to the extracted audio file (WAV format, 16kHz mono)

        Raises:
            FileNotFoundError: If the video file doesn't exist
            RuntimeError: If ffmpeg fails to extract audio
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # If it's already an audio file, convert to proper format for Whisper
        if self.is_audio_file(video_path):
            pass  # Still need to convert to 16kHz mono WAV for Whisper

        # Generate output path if not provided
        if output_path is None:
            output_path = Path(self._temp_dir) / f"{video_path.stem}_audio.wav"
        else:
            output_path = Path(output_path)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Extract audio using ffmpeg
            # Convert to 16kHz mono WAV (optimal for Whisper)
            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(output_path),
                    acodec='pcm_s16le',  # 16-bit PCM
                    ar='16000',           # 16kHz sample rate
                    ac=1,                 # Mono
                    y=None                # Overwrite output
                )
                .run(quiet=True, overwrite_output=True)
            )

            if not output_path.exists():
                raise RuntimeError(f"Failed to create audio file: {output_path}")

            return output_path

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"FFmpeg error extracting audio: {error_msg}") from e

    def get_video_duration(self, video_path: Path | str) -> float:
        """
        Get the duration of a video file in seconds.

        Args:
            video_path: Path to the video file

        Returns:
            Duration in seconds

        Raises:
            FileNotFoundError: If the video file doesn't exist
            RuntimeError: If ffprobe fails to get duration
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            return duration
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"FFprobe error getting duration: {error_msg}") from e
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"Could not parse video duration: {e}") from e

    def cleanup(self) -> None:
        """Remove temporary files created during extraction."""
        import shutil
        try:
            shutil.rmtree(self._temp_dir)
        except Exception:
            pass  # Ignore cleanup errors

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()
