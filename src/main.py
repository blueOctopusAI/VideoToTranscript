#!/usr/bin/env python3
"""
Video to Transcript - Desktop application for transcribing video files.

Usage:
    python -m src.main
    or
    python src/main.py
"""

import sys
from pathlib import Path

# Ensure the src directory is in the path for imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow


def main() -> int:
    """Main entry point for the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Video to Transcript")
    app.setOrganizationName("VideoToTranscript")

    # Set application style
    app.setStyle("Fusion")

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Run the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
