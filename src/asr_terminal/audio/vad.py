"""
Voice Activity Detection (VAD).
"""
import webrtcvad
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VADFilter:
    """
    Voice Activity Detection filter.

    Uses WebRTC VAD to detect speech in audio chunks.
    """

    def __init__(self, aggressiveness: int = 2):
        """
        Initialize VAD filter.

        Args:
            aggressiveness: VAD aggressiveness (0-3)
                0: Least aggressive (more false positives)
                3: Most aggressive (more false negatives)
        """
        if not 0 <= aggressiveness <= 3:
            raise ValueError("aggressiveness must be between 0 and 3")

        self.vad = webrtcvad.Vad(aggressiveness)
        self.aggressiveness = aggressiveness

        logger.debug(f"VAD initialized with aggressiveness={aggressiveness}")

    def is_speech(self, audio_bytes: bytes, sample_rate: int) -> bool:
        """
        Check if audio chunk contains speech.

        Args:
            audio_bytes: Audio data bytes (16-bit PCM)
            sample_rate: Sample rate (must be 8000, 16000, 32000, or 48000)

        Returns:
            True if speech is detected, False otherwise

        Raises:
            ValueError: If sample rate is not supported
        """
        if sample_rate not in [8000, 16000, 32000, 48000]:
            raise ValueError(
                f"Sample rate {sample_rate} not supported by VAD. "
                "Must be 8000, 16000, 32000, or 48000."
            )

        # WebRTC VAD expects 30ms frames
        frame_duration = 30  # ms
        frame_size = int(sample_rate * frame_duration / 1000 * 2)  # 2 bytes per sample

        # If audio is shorter than frame size, pad it
        if len(audio_bytes) < frame_size:
            audio_bytes = audio_bytes + b'\x00' * (frame_size - len(audio_bytes))

        # Process first frame
        frame = audio_bytes[:frame_size]

        try:
            is_speech = self.vad.is_speech(frame, sample_rate)
            return is_speech

        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False  # Assume silence on error

    def filter_speech_frames(
        self,
        audio_bytes: bytes,
        sample_rate: int,
        frame_duration: int = 30
    ) -> list[bytes]:
        """
        Split audio into frames and filter speech frames.

        Args:
            audio_bytes: Audio data bytes
            sample_rate: Sample rate
            frame_duration: Frame duration in ms

        Returns:
            List of frames that contain speech
        """
        frame_size = int(sample_rate * frame_duration / 1000 * 2)
        frames = []

        for i in range(0, len(audio_bytes), frame_size):
            frame = audio_bytes[i:i + frame_size]

            # Pad last frame if needed
            if len(frame) < frame_size:
                frame = frame + b'\x00' * (frame_size - len(frame))

            if self.is_speech(frame, sample_rate):
                frames.append(frame)

        return frames
