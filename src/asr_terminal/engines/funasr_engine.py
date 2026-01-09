"""
FunASR (Alibaba DashScope) speech recognition engine.

FunASR is an async file-based recognition service suitable for recorded audio files.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
from http import HTTPStatus
from urllib import request

try:
    import dashscope
    from dashscope.audio.asr import Transcription
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

from .base import ASREngine, RecognitionResult, EngineConfig
from ..models.transcript import Transcript, Segment
from ..exceptions import RecognitionError, EngineInitializationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FunASRConfig(EngineConfig):
    """
    FunASR engine configuration.

    Attributes:
        model: Model name (default: fun-asr)
        api_key: DashScope API key
        base_url: API base URL
        language_hints: Language hints for recognition
        poll_interval: Seconds between status checks
        max_wait_time: Maximum wait time in seconds
    """
    model: str = "fun-asr"
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    language_hints: List[str] = None
    poll_interval: int = 2
    max_wait_time: int = 300

    def __post_init__(self):
        if self.language_hints is None:
            self.language_hints = ["zh", "en"]


class FunASREngine(ASREngine):
    """
    FunASR async file-based speech recognition engine.

    This engine is designed for processing pre-recorded audio files
    using Alibaba DashScope's FunASR async API.
    """

    SUPPORTED_LANGUAGES = ["zh", "en", "ja", "ko", "yue", "de", "fr", "es", "ru"]

    def __init__(self, config: FunASRConfig):
        """
        Initialize FunASR engine.

        Args:
            config: FunASR configuration
        """
        if not DASHSCOPE_AVAILABLE:
            raise EngineInitializationError(
                "DashScope SDK is not installed. "
                "Install it with: pip install dashscope>=1.24.8"
            )

        super().__init__(config)

        # Configure API
        if config.api_key:
            dashscope.api_key = config.api_key

        if config.base_url:
            dashscope.base_http_api_url = config.base_url

        logger.info(
            f"FunASR engine initialized: model={config.model}, "
            f"base_url={config.base_url}"
        )

    async def initialize(self) -> None:
        """Initialize FunASR engine (validate API key)."""
        if self._is_initialized:
            return

        if not dashscope.api_key or dashscope.api_key == "YOUR_API_KEY":
            raise EngineInitializationError(
                "DashScope API key is not configured. "
                "Set DASHSCOPE_API_KEY environment variable or provide api_key in config."
            )

        logger.info("FunASR engine initialization completed")
        self._is_initialized = True

    async def recognize(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> Transcript:
        """
        Recognize audio data.

        Note: FunASR requires publicly accessible URLs. For local files,
        you need to upload them to a cloud storage service first.

        Args:
            audio_data: Audio data as bytes
            language: Language code (not used directly, uses language_hints)

        Returns:
            Transcript object

        Raises:
            RecognitionError: If recognition fails
        """
        if not self._is_initialized:
            await self.initialize()

        # FunASR requires URLs, not raw audio data
        raise RecognitionError(
            "FunASR engine requires publicly accessible audio URLs. "
            "Please use a different engine (whisper/qwen) for local files, "
            "or upload your audio to a cloud storage and provide the URL."
        )

    async def recognize_from_url(
        self,
        file_url: str,
        language_hints: Optional[List[str]] = None
    ) -> Transcript:
        """
        Recognize audio from a publicly accessible URL.

        Args:
            file_url: Public URL of the audio file
            language_hints: Optional language hints (overrides config)

        Returns:
            Transcript object

        Raises:
            RecognitionError: If recognition fails
        """
        if not self._is_initialized:
            await self.initialize()

        language_hints = language_hints or self.config.language_hints

        try:
            logger.info(f"Starting FunASR recognition for URL: {file_url}")

            # Submit async task
            task_response = Transcription.async_call(
                model=self.config.model,
                file_urls=[file_url],
                language_hints=language_hints
            )

            if task_response.status_code != HTTPStatus.OK:
                raise RecognitionError(
                    f"Failed to submit FunASR task: {task_response.output.message}"
                )

            task_id = task_response.output.task_id
            logger.info(f"FunASR task submitted: {task_id}")

            # Wait for completion
            transcription_response = await self._wait_for_task(task_id)

            if transcription_response.status_code != HTTPStatus.OK:
                raise RecognitionError(
                    f"FunASR recognition failed: {transcription_response.output.message}"
                )

            # Extract results
            transcripts = []
            for result in transcription_response.output['results']:
                if result['subtask_status'] == 'SUCCEEDED':
                    # Fetch result from URL
                    result_url = result['transcription_url']
                    result_data = json.loads(
                        request.urlopen(result_url).read().decode('utf8')
                    )
                    transcripts.append(result_data)
                else:
                    logger.warning(f"Subtask failed: {result}")

            if not transcripts:
                raise RecognitionError("No successful transcriptions received")

            # Parse first result
            result_data = transcripts[0]
            transcript_text = self._extract_text(result_data)
            detected_language = self._extract_language(result_data)

            # Build transcript object
            transcript = Transcript(
                text=transcript_text,
                language=detected_language,
                segments=self._create_segments(result_data),
                engine=self.get_name()
            )

            logger.info(f"FunASR recognition completed: {len(transcript_text)} chars")
            return transcript

        except Exception as e:
            logger.error(f"FunASR recognition failed: {e}")
            raise RecognitionError(f"FunASR recognition failed: {e}")

    async def _wait_for_task(self, task_id: str):
        """
        Wait for async task to complete.

        Args:
            task_id: Task ID

        Returns:
            Transcription response

        Raises:
            RecognitionError: If timeout or failed
        """
        import time

        start_time = asyncio.get_event_loop().time()
        elapsed = 0

        while elapsed < self.config.max_wait_time:
            # Run wait in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                Transcription.wait,
                task_id
            )

            # Check if completed
            if response.status_code == HTTPStatus.OK:
                # Check if task is truly finished
                if response.output['results']:
                    return response

            # Wait before polling again
            await asyncio.sleep(self.config.poll_interval)

            elapsed = asyncio.get_event_loop().time() - start_time
            logger.debug(f"Waiting for FunASR task {task_id}... ({elapsed:.1f}s)")

        raise RecognitionError(
            f"FunASR task timeout after {self.config.max_wait_time}s"
        )

    async def recognize_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None
    ) -> AsyncIterator[RecognitionResult]:
        """
        FunASR does not support streaming recognition.

        This method collects all audio data and recognizes at once.
        """
        # Collect all audio
        audio_buffer = []
        async for chunk in audio_stream:
            audio_buffer.append(chunk)

        audio_data = b''.join(audio_buffer)

        # FunASR requires URL, not raw data
        raise RecognitionError(
            "FunASR does not support streaming. "
            "Please use recognize_from_url() with a publicly accessible URL."
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()

    def get_name(self) -> str:
        """Get engine name."""
        return "funasr"

    def _extract_text(self, result_data: dict) -> str:
        """
        Extract text from FunASR result.

        Args:
            result_data: FunASR response data

        Returns:
            Transcribed text
        """
        # FunASR response format may vary, adapt as needed
        if "transcript" in result_data:
            return result_data["transcript"]
        elif "text" in result_data:
            return result_data["text"]
        elif "sentences" in result_data:
            return " ".join([s.get("text", "") for s in result_data["sentences"]])
        else:
            # Return entire JSON as fallback
            return json.dumps(result_data, ensure_ascii=False)

    def _extract_language(self, result_data: dict) -> str:
        """
        Extract detected language from result.

        Args:
            result_data: FunASR response data

        Returns:
            Language code
        """
        if "language" in result_data:
            return result_data["language"]
        return "unknown"

    def _create_segments(self, result_data: dict) -> List[Segment]:
        """
        Create segments from FunASR result.

        Args:
            result_data: FunASR response data

        Returns:
            List of segments
        """
        segments = []

        if "sentences" in result_data:
            # If sentence-level timestamps are available
            for i, sent in enumerate(result_data["sentences"]):
                segments.append(Segment(
                    start=float(sent.get("begin_time", 0.0)),
                    end=float(sent.get("end_time", 0.0)),
                    text=sent.get("text", ""),
                    confidence=float(sent.get("confidence", 0.95))
                ))
        else:
            # Create single segment for entire text
            text = self._extract_text(result_data)
            duration = float(result_data.get("duration", 0.0))
            segments.append(Segment(
                start=0.0,
                end=duration,
                text=text,
                confidence=0.95
            ))

        return segments

    async def cleanup(self) -> None:
        """Clean up resources."""
        await super().cleanup()
