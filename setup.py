"""
ASR Terminal - Multi-Engine Speech Recognition Tool
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="asr-terminal",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A multi-engine speech recognition terminal tool supporting real-time and batch processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/asr-terminal",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "librosa>=0.10.0",
        "soundfile>=0.12.0",
        "pyaudio>=0.2.13",
        "webrtcvad>=2.0.10",
        "openai-whisper>=20231117",
        "torch>=2.1.0",
        "torchaudio>=2.1.0",
        "pyyaml>=6.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "rich>=13.7.0",
        "tqdm>=4.66.0",
        "pysrt>=1.1.2",
        "numpy>=1.24.0",
    ],
    extras_require={
        "qwen": ["dashscope>=1.14.0"],
        "azure": ["azure-cognitiveservices-speech>=1.34.0"],
        "baidu": ["requests>=2.31.0"],
        "paddle": ["paddlepaddle>=2.5.2", "paddleaudio>=1.0.0"],
        "all": [
            "dashscope>=1.14.0",
            "azure-cognitiveservices-speech>=1.34.0",
            "requests>=2.31.0",
            "paddlepaddle>=2.5.2",
            "paddleaudio>=1.0.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "asr=asr_terminal.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "asr_terminal": ["config/*.yaml", "config/*.yml"],
    },
    zip_safe=False,
)
