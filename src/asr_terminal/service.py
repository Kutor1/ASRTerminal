"""
ASR Service - Main service facade.
"""
import asyncio
from pathlib import Path
from typing import List, Optional, Callable
from .engines.factory import EngineFactory
from .engines.base import RecognitionResult
from .audio.processor import AudioProcessor
from .output.exporter import Exporter
from .output.display import Display
from .config.manager import ConfigManager
from .models.transcript import Transcript
from .utils.logger import get_logger
from .utils.retry import RetryStrategy
from .exceptions import ASRTerminalError

logger = get_logger(__name__)


class ASRService:
    """
    ASR Service facade.

    Provides a unified high-level API for speech recognition functionality.
    """

    def __init__(self, config: ConfigManager):
        """
        Initialize ASR service.

        Args:
            config: Configuration manager
        """
        self.config = config
        self.engine = None
        self.audio_processor = AudioProcessor(config.get('audio', {}))
        self.exporter = Exporter(config.get('output', {}))
        self.display = Display(config.get('output', {}))
        self.retry_strategy = RetryStrategy(config.get('engine.fallback', {}))

    async def initialize(self, engine_name: Optional[str] = None) -> None:
        """
        Initialize the service with specified engine.

        Args:
            engine_name: Engine name (uses default if None)
        """
        engine_name = engine_name or self.config.get('engine.default', 'whisper')

        try:
            engine_config = self.config.get_engine_config(engine_name)
        except ValueError as e:
            logger.error(f"Failed to get engine config: {e}")
            raise

        self.engine = await EngineFactory.get_or_create_engine(
            engine_name,
            engine_config
        )

        logger.info(f"ASR service initialized with engine: {engine_name}")

    async def recognize_file(
        self,
        file_path: str | Path,
        language: Optional[str] = None,
        engine: Optional[str] = None
    ) -> Transcript:
        """
        Recognize audio file (batch mode).

        Args:
            file_path: Path to audio file
            language: Language code
            engine: Override engine name

        Returns:
            Transcript object

        Raises:
            ASRTerminalError: If recognition fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ASRTerminalError(f"File not found: {file_path}")

        # Switch engine if specified
        if engine:
            await self.switch_engine(engine)

        logger.info(f"Processing file: {file_path}")

        try:
            # Preprocess audio
            audio_data = await self.audio_processor.process_file(file_path)

            # Recognize with retry
            transcript = await self.retry_strategy.execute(
                self.engine.recognize,
                audio_data,
                language
            )

            # Export results
            await self._export_results(transcript, file_path.stem)

            return transcript

        except Exception as e:
            logger.error(f"Failed to recognize file: {e}")
            raise ASRTerminalError(f"File recognition failed: {e}")

    async def recognize_files_batch(
        self,
        file_paths: List[str | Path],
        language: Optional[str] = None,
        max_workers: int = 4
    ) -> List[Transcript]:
        """
        Batch recognize multiple audio files.

        Args:
            file_paths: List of file paths
            language: Language code
            max_workers: Maximum concurrent workers

        Returns:
            List of Transcript objects
        """
        semaphore = asyncio.Semaphore(max_workers)

        async def process_file(path: Path) -> Transcript:
            async with semaphore:
                return await self.recognize_file(path, language)

        tasks = [process_file(Path(p)) for p in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successes and failures
        transcripts = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {file_paths[i]}: {result}")
                errors.append((file_paths[i], result))
            else:
                transcripts.append(result)

        logger.info(
            f"Batch processing completed: "
            f"{len(transcripts)} successful, {len(errors)} failed"
        )

        return transcripts

    async def switch_engine(self, engine_name: str) -> None:
        """
        Switch to a different recognition engine.

        Args:
            engine_name: New engine name
        """
        logger.info(f"Switching engine to: {engine_name}")

        # Clean up current engine
        if self.engine:
            old_name = self.engine.get_name()
            logger.debug(f"Cleaning up engine: {old_name}")

        # Initialize new engine
        await self.initialize(engine_name)

        logger.info(f"Engine switched successfully")

    async def _export_results(self, transcript: Transcript, base_name: str) -> None:
        """
        Export and display results.

        Args:
            transcript: Transcript object
            base_name: Base name for output files
        """
        # Display in console
        self.display.print_transcript(transcript)

        # Export to files
        try:
            exported = self.exporter.export(transcript, base_name)
            for path in exported:
                self.display.print_success(f"Exported: {path}")
        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.display.print_warning(f"Failed to export results: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.engine:
            await self.engine.cleanup()
        await EngineFactory.cleanup_all()
        logger.info("ASR service cleaned up")
