"""
Test script for FunASR engine.
"""
import asyncio
import os
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asr_terminal.engines import EngineFactory
from asr_terminal.engines.funasr_engine import FunASRConfig


async def test_funasr_with_url():
    """Test FunASR engine with a public URL."""

    # Check if API key is set
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        print("❌ DASHSCOPE_API_KEY not set!")
        print("Please set the environment variable:")
        print("  export DASHSCOPE_API_KEY=sk-your-actual-key")
        return

    print("✅ API Key found")

    try:
        # Create FunASR engine
        print("🔧 Initializing FunASR engine...")
        engine = await EngineFactory.create_engine("funasr", {
            "api_key": api_key,
            "language_hints": ["zh", "en"],
            "poll_interval": 2,
            "max_wait_time": 300
        })
        print("✅ FunASR engine initialized")

        # Test with DashScope sample URL
        test_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/samples/audio/paraformer/hello_world_female2.wav"

        print(f"\n🎙️  Testing with sample URL:")
        print(f"   {test_url}")

        transcript = await engine.recognize_from_url(
            file_url=test_url,
            language_hints=["zh", "en"]
        )

        print("\n" + "="*50)
        print("📝 Recognition Result:")
        print("="*50)
        print(f"Text: {transcript.text}")
        print(f"Language: {transcript.language}")
        print(f"Engine: {transcript.engine}")
        print(f"Segments: {len(transcript.segments)}")

        if transcript.segments:
            print("\nTimeline:")
            for seg in transcript.segments:
                print(f"  [{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}")

        print("="*50)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_local_file_limitation():
    """Test that local files are not supported."""
    print("\n⚠️  Testing local file limitation...")

    print("\nℹ️  FunASR engine only accepts public URLs!")
    print("   For local files, please use:")
    print("   - Whisper engine (local recognition)")
    print("   - Qwen engine (real-time recognition)")
    print("   - Or upload local file to cloud storage first")


async def main():
    """Run all tests."""
    print("="*60)
    print("FunASR Engine Test")
    print("="*60)

    # Test with URL
    await test_funasr_with_url()

    # Show limitation
    test_local_file_limitation()

    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
