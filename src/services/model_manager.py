"""Model management for faster-whisper models."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel


@dataclass
class ModelInfo:
    """Information about a Whisper model."""
    name: str
    size_mb: int
    description: str


# Available Whisper models
AVAILABLE_MODELS = {
    "tiny": ModelInfo("tiny", 39, "Fastest, least accurate"),
    "base": ModelInfo("base", 74, "Good balance of speed and accuracy (recommended)"),
    "small": ModelInfo("small", 244, "Better accuracy, slower"),
    "medium": ModelInfo("medium", 769, "High accuracy, significantly slower"),
    "large-v3": ModelInfo("large-v3", 1550, "Best accuracy, slowest"),
}

DEFAULT_MODEL = "base"


class ModelManager:
    """Manages Whisper model loading and caching."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the model manager.

        Args:
            cache_dir: Optional directory for model cache.
                      Defaults to ~/.cache/video-to-transcript/models
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "video-to-transcript" / "models"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._loaded_model: Optional[WhisperModel] = None
        self._loaded_model_name: Optional[str] = None

    @staticmethod
    def get_available_models() -> dict[str, ModelInfo]:
        """Get information about all available models."""
        return AVAILABLE_MODELS.copy()

    @staticmethod
    def get_model_info(model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        return AVAILABLE_MODELS.get(model_name)

    def get_device(self) -> str:
        """
        Determine the best device to use for inference.

        Returns:
            'cuda' for NVIDIA GPUs, 'cpu' otherwise
            (faster-whisper uses CTranslate2 which handles Metal/MPS internally)
        """
        # faster-whisper with CTranslate2 will automatically use
        # the best available backend (including Metal on Apple Silicon)
        # when device is set to 'auto' or 'cpu'
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass

        # For Apple Silicon, 'cpu' with CTranslate2 still gets Metal acceleration
        return "cpu"

    def get_compute_type(self) -> str:
        """
        Determine the best compute type for the current device.

        Returns:
            Compute type string for faster-whisper
        """
        device = self.get_device()
        if device == "cuda":
            return "float16"  # Best for NVIDIA GPUs
        else:
            # INT8 provides good speed on CPU/Apple Silicon
            return "int8"

    def load_model(self, model_name: str = DEFAULT_MODEL) -> WhisperModel:
        """
        Load a Whisper model.

        Args:
            model_name: Name of the model to load (e.g., 'base', 'small')

        Returns:
            Loaded WhisperModel instance

        Raises:
            ValueError: If model name is invalid
        """
        if model_name not in AVAILABLE_MODELS:
            valid_models = ", ".join(AVAILABLE_MODELS.keys())
            raise ValueError(
                f"Invalid model: {model_name}. Valid models: {valid_models}"
            )

        # Return cached model if already loaded
        if self._loaded_model is not None and self._loaded_model_name == model_name:
            return self._loaded_model

        # Unload previous model
        self.unload_model()

        device = self.get_device()
        compute_type = self.get_compute_type()

        # Load the model
        self._loaded_model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            download_root=str(self.cache_dir)
        )
        self._loaded_model_name = model_name

        return self._loaded_model

    def unload_model(self) -> None:
        """Unload the currently loaded model to free memory."""
        if self._loaded_model is not None:
            del self._loaded_model
            self._loaded_model = None
            self._loaded_model_name = None

    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._loaded_model is not None

    def get_loaded_model_name(self) -> Optional[str]:
        """Get the name of the currently loaded model."""
        return self._loaded_model_name

    def is_model_downloaded(self, model_name: str) -> bool:
        """
        Check if a model has been downloaded.

        Note: This is approximate as model files may vary by version.
        """
        # CTranslate2 stores models in a specific structure
        model_dir = self.cache_dir / f"models--Systran--faster-whisper-{model_name}"
        return model_dir.exists()

    def __del__(self):
        """Cleanup on deletion."""
        self.unload_model()
