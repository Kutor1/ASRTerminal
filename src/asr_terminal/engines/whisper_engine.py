"""
OpenAI Whisper speech recognition engine.
"""
import io
import asyncio
import numpy as np
import torch
import whisper
import soundfile as sf
from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
from .base import ASREngine, RecognitionResult, EngineConfig
from ..models.transcript import Transcript, Segment
from ..exceptions import RecognitionError, EngineInitializationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WhisperConfig(EngineConfig):
    """
    Whisper engine configuration.

    Attributes:
        model_size: Whisper model size (tiny/base/small/medium/large)
        device: Device to run on (auto/cpu/cuda)
        compute_type: Computation type (float16/float32/int8)
        model_path: Optional local model path
        language: Default language (auto/zh/en/etc)
    """
    model_size: str = "base"
    device: str = "auto"
    compute_type: str = "float16"
    model_path: Optional[str] = None
    language: str = "auto"


class WhisperEngine(ASREngine):
    """
    OpenAI Whisper local speech recognition engine.

    Supports multiple model sizes from tiny to large-v3.
    """

    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    SUPPORTED_LANGUAGES = [
        "zh", "en", "es", "fr", "de", "ja", "ko", "ru",
        "ar", "pt", "it", "nl", "tr", "pl", "sv", "vi",
        "auto"
    ]

    def __init__(self, config: WhisperConfig):
        """
        Initialize Whisper engine.

        Args:
            config: Whisper configuration
        """
        super().__init__(config)
        self.model = None
        self.device = self._determine_device()
        logger.info(f"Whisper engine created with model: {config.model_size}")

    async def initialize(self) -> None:
        """
        Load Whisper model.

        This may take a while on first run as it downloads the model.
        """
        if self._is_initialized:
            return

        logger.info(f"Loading Whisper model: {self.config.model_size}")

        try:
            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                self._load_model
            )

            self._is_initialized = True
            logger.info("Whisper model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise EngineInitializationError(f"Whisper initialization failed: {e}")

    def _load_model(self) -> whisper.Whisper:
        """
        Load Whisper model (synchronous).

        Returns:
            Loaded Whisper model
        """
        model_path = self.config.model_path or self.config.model_size

        model = whisper.load_model(
            model_path,
            device=self.device,
            in_memory=True
        )

        # Convert to half precision for GPU
        if self.device == "cuda" and self.config.compute_type == "float16":
            model = model.half()

        return model

    async def recognize(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> Transcript:
        """
        Recognize audio data.

        Args:
            audio_data: Audio data as bytes
            language: Language code (None for auto-detect)

        Returns:
            Transcript object

        Raises:
            RecognitionError: If recognition fails
        """
        if not self._is_initialized:
            await self.initialize()

        try:
            # Prepare audio
            audio_array = self._prepare_audio(audio_data)

            # Perform recognition
            language = language or self.config.language
            if language == "auto":
                language = None

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe,
                audio_array,
                language
            )

            # Build transcript
            transcript = Transcript(
                text=result["text"].strip(),
                language=result.get("language", "unknown"),
                segments=self._convert_segments(result.get("segments", [])),
                engine=self.get_name()
            )

            logger.info(f"Recognition completed: {len(transcript.text)} chars")
            return transcript

        except Exception as e:
            logger.error(f"Recognition failed: {e}")
            raise RecognitionError(f"Whisper recognition failed: {e}")

    def _transcribe(
        self,
        audio_array: np.ndarray,
        language: Optional[str]
    ) -> dict:
        """
        Transcribe audio (synchronous).

        Args:
            audio_array: Audio numpy array
            language: Language code

        Returns:
            Whisper result dictionary
        """
        fp16 = self.config.compute_type == "float16" and self.device == "cuda"

        result = self.model.transcribe(
            audio_array,
            language=language,
            task="transcribe",
            fp16=fp16
        )

        return result

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None
    ) -> AsyncIterator[RecognitionResult]:
        """
        Recognize streaming audio.

        Note: Whisper doesn't natively support streaming, so this processes
        audio in chunks (default 30 seconds).

        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code

        Yields:
            RecognitionResult objects
        """
        buffer = []
        chunk_duration = 30.0  # Process in 30-second chunks

        async for chunk in audio_stream:
            buffer.append(chunk)

            # Check if we have enough data
            current_duration = len(b''.join(buffer)) / 16000 / 2  # Assuming 16kHz, 16-bit

            if current_duration >= chunk_duration:
                audio_data = b''.join(buffer)
                transcript = await self.recognize(audio_data, language)

                yield RecognitionResult(
                    text=transcript.text,
                    confidence=0.95,  # Whisper doesn't provide confidence
                    timestamp=(0.0, current_duration),
                    is_final=True
                )

                buffer = []

        # Process remaining data
        if buffer:
            audio_data = b''.join(buffer)
            transcript = await self.recognize(audio_data, language)
            yield RecognitionResult(
                text=transcript.text,
                confidence=0.95,
                timestamp=(0.0, len(audio_data) / 16000 / 2),
                is_final=True
            )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()

    def get_name(self) -> str:
        """Get engine name."""
        return f"whisper-{self.config.model_size}"

    def _determine_device(self) -> str:
        """
        Determine the device to run on.

        Returns:
            Device string (cpu/cuda/mps)
        """
        if self.config.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return self.config.device

    def _prepare_audio(self, audio_data: bytes) -> np.ndarray:
        """
        Prepare audio data for Whisper.

        Args:
            audio_data: Audio bytes

        Returns:
            Audio numpy array at 16kHz mono
        """
        # Load audio from bytes
        audio, sr = sf.read(io.BytesIO(audio_data))

        # Convert to mono if needed
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # Convert to float32 (Whisper expects float32)
        audio = audio.astype(np.float32)

        # Resample to 16kHz if needed
        if sr != 16000:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        return audio

    def _convert_segments(self, segments: List) -> List[Segment]:
        """
        Convert Whisper segments to standard format.

        Args:
            segments: List of Whisper segment dictionaries

        Returns:
            List of Segment objects
        """
        result = []

        for seg in segments:
            segment = Segment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=seg["text"].strip(),
                confidence=float(seg.get("avg_logprob", 0.0))
            )
            result.append(segment)

        return result

    async def cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        await super().cleanup()
