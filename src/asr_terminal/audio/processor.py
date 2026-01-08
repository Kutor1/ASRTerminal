"""
Audio processing utilities.
"""
import io
from pathlib import Path
from typing import Optional
import numpy as np
import soundfile as sf
import librosa
from ..exceptions import AudioProcessingError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """
    Audio preprocessing and conversion.

    Handles audio loading, resampling, normalization, and format conversion.
    """

    def __init__(self, config: dict):
        """
        Initialize audio processor.

        Args:
            config: Audio configuration dictionary
        """
        self.sample_rate = config.get('sample_rate', 16000)
        self.channels = config.get('channels', 1)
        self.normalize = config.get('batch', {}).get('normalize', True)
        self.preprocessing_steps = config.get('preprocessing', [])

    async def process_file(self, file_path: Path) -> bytes:
        """
        Process audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Processed audio data as bytes

        Raises:
            AudioProcessingError: If processing fails
        """
        try:
            logger.info(f"Processing audio file: {file_path}")

            # Load audio
            audio, sr = sf.read(file_path)

            # Apply preprocessing steps
            audio = self._preprocess(audio, sr)

            # Convert back to bytes
            audio_bytes = self._to_bytes(audio, sr)

            logger.info(f"Audio processing completed: {len(audio_bytes)} bytes")
            return audio_bytes

        except Exception as e:
            logger.error(f"Failed to process audio file: {e}")
            raise AudioProcessingError(f"Audio processing failed: {e}")

    def _preprocess(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply preprocessing pipeline.

        Args:
            audio: Audio array
            sample_rate: Sample rate

        Returns:
            Processed audio array
        """
        for step in self.preprocessing_steps:
            if step == "resample":
                if sample_rate != self.sample_rate:
                    audio = librosa.resample(
                        audio,
                        orig_sr=sample_rate,
                        target_sr=self.sample_rate
                    )
                    logger.debug(f"Resampled from {sample_rate} to {self.sample_rate}")

            elif step == "convert_to_mono":
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                    logger.debug("Converted to mono")

            elif step == "normalize":
                if self.normalize:
                    audio = self._normalize(audio)
                    logger.debug("Normalized audio")

            elif step == "trim_silence":
                audio = self._trim_silence(audio)
                logger.debug("Trimmed silence")

        return audio

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to [-1, 1].

        Args:
            audio: Audio array

        Returns:
            Normalized audio
        """
        if len(audio) == 0:
            return audio

        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio

    def _trim_silence(
        self,
        audio: np.ndarray,
        threshold: float = 0.01
    ) -> np.ndarray:
        """
        Trim silence from beginning and end.

        Args:
            audio: Audio array
            threshold: Silence threshold

        Returns:
            Trimmed audio
        """
        # Find non-silent regions
        non_silent = librosa.effects.split(
            audio.astype(np.float32),
            top_db=40
        )

        if len(non_silent) == 0:
            return audio

        # Trim from beginning and end
        start = non_silent[0][0]
        end = non_silent[-1][1]

        return audio[start:end]

    def _to_bytes(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """
        Convert audio array to bytes.

        Args:
            audio: Audio array
            sample_rate: Sample rate

        Returns:
            Audio data as bytes (WAV format)
        """
        # Ensure mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        # Write to bytes buffer
        buffer = io.BytesIO()
        sf.write(
            buffer,
            audio_int16,
            sample_rate,
            format='WAV',
            subtype='PCM_16'
        )
        buffer.seek(0)

        return buffer.read()

    @staticmethod
    def get_audio_info(file_path: Path) -> dict:
        """
        Get audio file information.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio info (duration, sample_rate, channels, etc.)
        """
        try:
            info = sf.info(str(file_path))
            return {
                'filename': file_path.name,
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'frames': info.frames,
                'format': info.format,
                'subtype': info.subtype
            }
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            return {}
