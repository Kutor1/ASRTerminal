"""
Speech recognition engines.

This module automatically registers all available engines.
"""
from .base import ASREngine, EngineConfig, RecognitionResult
from .factory import EngineFactory
from .whisper_engine import WhisperEngine, WhisperConfig

# Register Whisper engine
EngineFactory.register_engine("whisper", WhisperEngine, WhisperConfig)

# Cloud engines will be registered when their dependencies are installed

try:
    from .qwen_engine import QwenEngine, QwenConfig
    EngineFactory.register_engine("qwen", QwenEngine, QwenConfig)
except ImportError:
    pass

# try:
#     from .azure_engine import AzureEngine, AzureConfig
#     EngineFactory.register_engine("azure", AzureEngine, AzureConfig)
# except ImportError:
#     pass

# try:
#     from .baidu_engine import BaiduEngine, BaiduConfig
#     EngineFactory.register_engine("baidu", BaiduEngine, BaiduConfig)
# except ImportError:
#     pass

# try:
#     from .paddle_engine import PaddleEngine, PaddleConfig
#     EngineFactory.register_engine("paddle", PaddleEngine, PaddleConfig)
# except ImportError:
#     pass

__all__ = [
    "ASREngine",
    "EngineConfig",
    "RecognitionResult",
    "EngineFactory",
    "WhisperEngine",
    "WhisperConfig",
    "QwenEngine",
    "QwenConfig",
]
