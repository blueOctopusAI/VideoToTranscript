# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Video to Transcript.

Build with: pyinstaller VideoToTranscript.spec

This creates a macOS .app bundle with:
- Python runtime and all dependencies
- ffmpeg binary bundled
- Whisper models download on first use
"""

import os
import subprocess
from pathlib import Path

block_cipher = None

# Find ffmpeg location
def find_ffmpeg():
    """Find ffmpeg binary path."""
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass

    # Common locations
    locations = [
        '/opt/homebrew/bin/ffmpeg',  # Apple Silicon Homebrew
        '/usr/local/bin/ffmpeg',      # Intel Homebrew
        '/usr/bin/ffmpeg',            # System
    ]
    for loc in locations:
        if os.path.exists(loc):
            return loc

    raise FileNotFoundError("ffmpeg not found. Install with: brew install ffmpeg")

ffmpeg_path = find_ffmpeg()
ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe')

# Collect ffmpeg binaries - put in 'bin' subdirectory to avoid conflict with ffmpeg-python package
binaries = [
    (ffmpeg_path, 'bin'),
    (ffprobe_path, 'bin'),
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'faster_whisper',
        'ctranslate2',
        'huggingface_hub',
        'tokenizers',
        'numpy',
        'av',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VideoToTranscript',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS argv emulation for drag-drop
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoToTranscript',
)

app = BUNDLE(
    coll,
    name='Video to Transcript.app',
    icon=None,  # Add icon path here if you have one: 'assets/icon.icns'
    bundle_identifier='com.videototranscript.app',
    info_plist={
        'CFBundleName': 'Video to Transcript',
        'CFBundleDisplayName': 'Video to Transcript',
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Video File',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': [
                    'public.movie',
                    'public.video',
                    'public.mpeg-4',
                    'com.apple.quicktime-movie',
                ],
            },
            {
                'CFBundleTypeName': 'Audio File',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': [
                    'public.audio',
                    'public.mp3',
                    'public.mpeg-4-audio',
                ],
            },
        ],
    },
)
