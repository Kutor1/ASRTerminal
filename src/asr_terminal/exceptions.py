"""
Custom exceptions for ASR Terminal.
"""


class ASRTerminalError(Exception):
    """Base exception for ASR Terminal."""
    pass


class EngineError(ASRTerminalError):
    """Base exception for engine errors."""
    pass


class EngineNotFoundError(EngineError):
    """Raised when requested engine is not found."""

    def __init__(self, engine_name: str, available_engines: list):
        self.engine_name = engine_name
        self.available_engines = available_engines
        super().__init__(
            f"Engine '{engine_name}' not found. "
            f"Available engines: {', '.join(available_engines)}"
        )


class EngineInitializationError(EngineError):
    """Raised when engine fails to initialize."""
    pass


class RecognitionError(EngineError):
    """Raised when recognition fails."""
    pass


class AudioProcessingError(ASRTerminalError):
    """Raised when audio processing fails."""
    pass


class ConfigurationError(ASRTerminalError):
    """Raised when configuration is invalid."""
    pass


class AudioStreamError(ASRTerminalError):
    """Raised when audio streaming fails."""
    pass
