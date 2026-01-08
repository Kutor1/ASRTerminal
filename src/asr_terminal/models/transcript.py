"""
Data models for speech recognition results.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Language(Enum):
    """Supported languages."""
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"
    AUTO = "auto"


@dataclass
class Segment:
    """
    Audio segment with timestamp and text.

    Attributes:
        start: Start time in seconds
        end: End time in seconds
        text: Text content
        confidence: Confidence score (0-1)
    """
    start: float
    end: float
    text: str
    confidence: float = 1.0

    @property
    def duration(self) -> float:
        """Get segment duration in seconds."""
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary."""
        return {
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "text": self.text,
            "confidence": self.confidence
        }


@dataclass
class Transcript:
    """
    Complete transcription result.

    Attributes:
        text: Complete transcribed text
        language: Detected language code
        segments: List of time-stamped segments
        engine: Name of the engine used
        created_at: Timestamp of creation
        metadata: Additional metadata
    """
    text: str
    language: str
    segments: List[Segment]
    engine: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get total duration in seconds."""
        if not self.segments:
            return 0.0
        return self.segments[-1].end

    @property
    def word_count(self) -> int:
        """Get word count of the transcription."""
        return len(self.text.split())

    def get_segment_at_time(self, time: float) -> Optional[Segment]:
        """
        Get segment at specific time.

        Args:
            time: Time in seconds

        Returns:
            Segment if found, None otherwise
        """
        for segment in self.segments:
            if segment.start <= time <= segment.end:
                return segment
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert transcript to dictionary."""
        return {
            "text": self.text,
            "language": self.language,
            "duration": self.duration,
            "word_count": self.word_count,
            "engine": self.engine,
            "created_at": self.created_at.isoformat(),
            "segments": [s.to_dict() for s in self.segments],
            "metadata": self.metadata
        }

    def to_srt(self) -> str:
        """
        Generate SRT subtitle format.

        Returns:
            SRT formatted string
        """
        srt_lines = []

        for i, segment in enumerate(self.segments, 1):
            start_time = self._format_srt_time(segment.start)
            end_time = self._format_srt_time(segment.end)

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(segment.text)
            srt_lines.append("")  # Empty line

        return "\n".join(srt_lines)

    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """
        Format seconds to SRT time format (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Transcript("
            f"engine={self.engine}, "
            f"language={self.language}, "
            f"duration={self.duration:.2f}s, "
            f"words={self.word_count})"
        )
