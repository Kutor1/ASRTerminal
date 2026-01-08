"""
Test script for Qwen engine.
"""
import asyncio
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asr_terminal.config.manager import ConfigManager
from asr_terminal.service import ASRService


async def test_qwen_engine():
    """Test Qwen engine with a sample audio file."""

    # Check if API key is set
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("❌ DASHSCOPE_API_KEY not set!")
        print("Please set the environment variable:")
        print("  export DASHSCOPE_API_KEY=sk-your-actual-key")
        return

    print("✅ API Key found")

    # Initialize service
    config = ConfigManager("config/config.yaml")
    service = ASRService(config)

    try:
        # Initialize Qwen engine
        print("🔧 Initializing Qwen engine...")
        await service.initialize("qwen")
        print("✅ Qwen engine initialized")

        # Test recognition
        audio_file = "test_audio.pcm"  # Replace with actual audio file

        if not Path(audio_file).exists():
            print(f"⚠️  Audio file not found: {audio_file}")
            print("Please provide a valid PCM audio file (16-bit, 16kHz, mono)")
            return

        print(f"🎙️  Recognizing: {audio_file}")
        transcript = await service.recognize_file(audio_file, language="zh")

        print("\n" + "="*50)
        print("📝 Recognition Result:")
        print("="*50)
        print(f"Text: {transcript.text}")
        print(f"Language: {transcript.language}")
        print(f"Engine: {transcript.engine}")
        print(f"Duration: {transcript.duration:.2f}s")
        print("="*50)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await service.cleanup()
        print("\n✅ Cleanup completed")


if __name__ == "__main__":
    asyncio.run(test_qwen_engine())
