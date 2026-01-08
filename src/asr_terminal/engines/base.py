"""
Base abstract class for speech recognition engines.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
from ..models.transcript import Transcript
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RecognitionResult:
    """
    Single recognition result.

    Attributes:
        text: Recognized text
        confidence: Confidence score (0-1)
        timestamp: Tuple of (start_time, end_time) in seconds
        is_final: Whether this is a final result (vs intermediate)
    """
    text: str
    confidence: float
    timestamp: tuple[float, float]  # (start, end) in seconds
    is_final: bool = True


@dataclass
class EngineConfig:
    """
    Base configuration for engines.

    Attributes:
        enabled: Whether the engine is enabled
        name: Engine name
    """
    enabled: bool = True
    name: str = ""


class ASREngine(ABC):
    """
    Abstract base class for speech recognition engines.

    All engines must implement this interface to ensure compatibility.
    """

    def __init__(self, config: EngineConfig):
        """
        Initialize engine.

        Args:
            config: Engine configuration
        """
        self.config = config
        self._is_initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the engine.

        This method should load models, establish API connections, etc.
        """
        pass

    @abstractmethod
    async def recognize(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> Transcript:
        """
        Recognize audio data.

        Args:
            audio_data: Audio data as bytes
            language: Language code (e.g., 'zh', 'en'), None for auto-detect

        Returns:
            Transcript object with recognition results

        Raises:
            RecognitionError: If recognition fails
        """
        pass

    @abstractmethod
    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None
    ) -> AsyncIterator[RecognitionResult]:
        """
        Recognize streaming audio.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code

        Yields:
            RecognitionResult objects (may include intermediate results)

        Raises:
            RecognitionError: If recognition fails
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of language codes (e.g., ['zh', 'en', 'ja'])
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get engine name.

        Returns:
            Engine name string
        """
        pass

    async def cleanup(self) -> None:
        """
        Clean up resources.

        This method should release models, close connections, etc.
        """
        self._is_initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if engine is initialized."""
        return self._is_initialized

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(initialized={self._is_initialized})"
