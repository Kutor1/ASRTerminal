"""
Alibaba Qwen (DashScope) speech recognition engine.
"""
import asyncio
import base64
import json
import time
from typing import AsyncIterator, List, Optional
from dataclasses import dataclass
import websocket

try:
    import dashscope
    from dashscope.audio.qwen_omni import (
        OmniRealtimeConversation,
        OmniRealtimeCallback,
        MultiModality,
        TranscriptionParams
    )
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

from .base import ASREngine, RecognitionResult, EngineConfig
from ..models.transcript import Transcript, Segment
from ..exceptions import RecognitionError, EngineInitializationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QwenConfig(EngineConfig):
    """
    Qwen engine configuration.

    Attributes:
        model: Model name (default: qwen3-asr-flash-realtime)
        api_key: DashScope API key
        url: WebSocket URL
        language: Language code (zh/en/ja/etc)
        sample_rate: Audio sample rate (8000 or 16000)
        format: Audio format (pcm/opus)
        enable_vad: Enable server-side VAD
        corpus_text: Optional corpus text for better recognition
    """
    model: str = "qwen3-asr-flash-realtime"
    api_key: str = ""
    url: str = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
    language: str = "zh"
    sample_rate: int = 16000
    format: str = "pcm"
    enable_vad: bool = True
    corpus_text: Optional[str] = None


class QwenEngine(ASREngine):
    """
    Alibaba Qwen (DashScope) real-time speech recognition engine.

    Supports multiple languages and real-time streaming via WebSocket.
    """

    SUPPORTED_LANGUAGES = [
        "zh",  # Chinese (Mandarin, Sichuan, Minnan, Wu, Cantonese)
        "en",  # English
        "ja",  # Japanese
        "de",  # German
        "ko",  # Korean
        "ru",  # Russian
        "fr",  # French
        "pt",  # Portuguese
        "ar",  # Arabic
        "it",  # Italian
        "es",  # Spanish
    ]

    SUPPORTED_FORMATS = ["pcm", "opus"]
    SUPPORTED_SAMPLE_RATES = [8000, 16000]

    def __init__(self, config: QwenConfig):
        """
        Initialize Qwen engine.

        Args:
            config: Qwen configuration
        """
        if not DASHSCOPE_AVAILABLE:
            raise EngineInitializationError(
                "DashScope SDK is not installed. "
                "Install it with: pip install dashscope>=1.24.8"
            )

        super().__init__(config)

        # Configure API key
        if config.api_key:
            dashscope.api_key = config.api_key

        self.conversation = None
        self.transcript_buffer = []
        self.final_transcript = ""
        self.is_recognition_complete = False

        logger.info(
            f"Qwen engine initialized: model={config.model}, "
            f"language={config.language}, sample_rate={config.sample_rate}"
        )

    async def initialize(self) -> None:
        """Initialize Qwen engine (validate API key)."""
        if self._is_initialized:
            return

        if not dashscope.api_key or dashscope.api_key == "YOUR_API_KEY":
            raise EngineInitializationError(
                "DashScope API key is not configured. "
                "Set DASHSCOPE_API_KEY environment variable or provide api_key in config."
            )

        logger.info("Qwen engine initialization completed")
        self._is_initialized = True

    async def recognize(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> Transcript:
        """
        Recognize audio data using WebSocket.

        Args:
            audio_data: Audio data as bytes (PCM, 16-bit, mono)
            language: Language code (overrides config)

        Returns:
            Transcript object

        Raises:
            RecognitionError: If recognition fails
        """
        if not self._is_initialized:
            await self.initialize()

        language = language or self.config.language

        try:
            # Use WebSocket for file recognition
            transcript_text = await self._recognize_with_websocket(audio_data, language)

            # Build transcript object
            transcript = Transcript(
                text=transcript_text,
                language=language,
                segments=self._create_segments(transcript_text),
                engine=self.get_name()
            )

            logger.info(f"Qwen recognition completed: {len(transcript_text)} chars")
            return transcript

        except Exception as e:
            logger.error(f"Qwen recognition failed: {e}")
            raise RecognitionError(f"Qwen recognition failed: {e}")

    async def _recognize_with_websocket(
        self,
        audio_data: bytes,
        language: str
    ) -> str:
        """
        Recognize audio using raw WebSocket connection.

        Args:
            audio_data: Audio bytes
            language: Language code

        Returns:
            Recognized text
        """
        model = self.config.model
        url = f"{self.config.url}?model={model}"
        api_key = dashscope.api_key

        final_text = ""
        recognition_complete = asyncio.Event()

        def on_open(ws):
            """WebSocket connection opened."""
            logger.info("WebSocket connection opened")

            # Send session update
            session_update = {
                "event_id": "event_init",
                "type": "session.update",
                "session": {
                    "modalities": ["text"],
                    "input_audio_format": self.config.format,
                    "sample_rate": self.config.sample_rate,
                    "input_audio_transcription": {
                        "language": language
                    }
                }
            }

            # Add VAD configuration if enabled
            if self.config.enable_vad:
                session_update["session"]["turn_detection"] = {
                    "type": "server_vad",
                    "threshold": 0.2,
                    "silence_duration_ms": 800
                }
            else:
                session_update["session"]["turn_detection"] = None

            ws.send(json.dumps(session_update))
            logger.info("Session configuration sent")

        def on_message(ws, message):
            """Handle WebSocket messages."""
            nonlocal final_text

            try:
                data = json.loads(message)
                event_type = data.get("type")

                logger.debug(f"Received event: {event_type}")

                # Handle final transcription result
                if event_type == "conversation.item.input_audio_transcription.completed":
                    final_text = data.get("transcript", "")
                    logger.info(f"Final transcript received: {final_text}")
                    recognition_complete.set()

                # Handle intermediate results
                elif event_type == "conversation.item.input_audio_transcription.text":
                    stash = data.get("stash", "")
                    logger.debug(f"Intermediate result: {stash}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message: {e}")

        def on_error(ws, error):
            """Handle WebSocket errors."""
            logger.error(f"WebSocket error: {error}")
            recognition_complete.set()

        def on_close(ws, close_status_code, close_msg):
            """WebSocket connection closed."""
            logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
            recognition_complete.set()

        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            url,
            header=[
                f"Authorization: Bearer {api_key}",
                "OpenAI-Beta: realtime=v1"
            ],
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        # Run WebSocket in background thread
        import threading
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.start()

        # Wait for session to be ready
        await asyncio.sleep(2)

        # Send audio data in chunks
        chunk_size = 3200  # ~0.1s for PCM16/16kHz
        offset = 0

        while offset < len(audio_data):
            chunk = audio_data[offset:offset + chunk_size]
            offset += chunk_size

            # Encode to base64
            encoded = base64.b64encode(chunk).decode('utf-8')

            # Send audio append event
            event = {
                "event_id": f"event_{int(time.time() * 1000)}",
                "type": "input_audio_buffer.append",
                "audio": encoded
            }

            ws.send(json.dumps(event))
            await asyncio.sleep(0.1)  # Simulate real-time streaming

        # Send silence to trigger VAD if enabled
        if self.config.enable_vad:
            for _ in range(30):
                silence = bytes(1024)
                encoded = base64.b64encode(silence).decode('utf-8')
                event = {
                    "event_id": f"event_silence_{int(time.time() * 1000)}",
                    "type": "input_audio_buffer.append",
                    "audio": encoded
                }
                ws.send(json.dumps(event))
                await asyncio.sleep(0.01)
        else:
            # Manual mode: send commit event
            commit_event = {
                "event_id": "event_commit",
                "type": "input_audio_buffer.commit"
            }
            ws.send(json.dumps(commit_event))

        # Wait for recognition to complete
        try:
            await asyncio.wait_for(recognition_complete.wait(), timeout=60)
        except asyncio.TimeoutError:
            logger.warning("Recognition timeout")

        # Close WebSocket
        ws.close()

        return final_text

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
            RecognitionResult objects (including intermediate results)
        """
        if not self._isinitialized:
            await self.initialize()

        language = language or self.config.language

        logger.info("Starting real-time recognition with Qwen")

        # For now, collect all audio and recognize at once
        # A true streaming implementation would use DashScope SDK's callback mechanism
        audio_buffer = []

        async for chunk in audio_stream:
            audio_buffer.append(chunk)

        audio_data = b''.join(audio_buffer)

        # Recognize
        transcript = await self.recognize(audio_data, language)

        yield RecognitionResult(
            text=transcript.text,
            confidence=0.95,
            timestamp=(0.0, len(audio_data) / self.config.sample_rate / 2),
            is_final=True
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.SUPPORTED_LANGUAGES.copy()

    def get_name(self) -> str:
        """Get engine name."""
        return f"qwen-{self.config.model}"

    def _create_segments(self, text: str) -> List[Segment]:
        """
        Create segments from text (Qwen doesn't provide timestamps).

        Args:
            text: Recognized text

        Returns:
            List of segments (single segment for entire text)
        """
        # Qwen doesn't provide detailed timestamps, so create a single segment
        return [
            Segment(
                start=0.0,
                end=0.0,  # Duration unknown
                text=text.strip(),
                confidence=0.95
            )
        ]

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.conversation:
            try:
                self.conversation.close()
            except Exception as e:
                logger.warning(f"Error closing conversation: {e}")
        await super().cleanup()
