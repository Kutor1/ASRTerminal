# ASR Terminal

<div align="center">

**A Multi-Engine Speech Recognition Terminal Tool**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Support real-time and batch speech recognition with multiple engines.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Configuration](#configuration) • [Engines](#engines)

</div>

---

## Features

- 🎙️ **Multiple Recognition Engines**
  - Local: OpenAI Whisper (tiny/base/small/medium/large)
  - Cloud: Qwen, Azure Speech, Baidu, PaddleSpeech (extensible)

- 📁 **Batch Processing**
  - Process multiple audio files concurrently
  - Progress tracking with beautiful terminal output

- 📝 **Multiple Output Formats**
  - Plain text (.txt)
  - Subtitles (.srt)
  - JSON with metadata

- ⚙️ **Flexible Configuration**
  - YAML-based configuration
  - Environment variable support
  - Per-engine settings

- 🔄 **Automatic Fallback**
  - Retry mechanism on failures
  - Engine fallback strategy

## Installation

### Requirements

- Python 3.8 or higher
- FFmpeg (for audio processing)

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/asr-terminal.git
cd asr-terminal

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Optional Dependencies

```bash
# For cloud engines
pip install -e ".[qwen]"      # Alibaba Qwen
pip install -e ".[azure]"     # Azure Speech
pip install -e ".[baidu]"     # Baidu Speech
pip install -e ".[paddle]"    # PaddleSpeech

# Or install all
pip install -e ".[all]"
```

## Usage

### Basic Commands

#### Transcribe a Single File

```bash
asr transcribe audio.wav
```

#### Batch Process Multiple Files

```bash
asr batch audio1.wav audio2.mp3 audio3.flac
```

#### Specify Engine and Language

```bash
asr transcribe audio.wav -e whisper -l zh
```

#### Export to Multiple Formats

```bash
asr batch *.wav -f txt -f srt -f json -o ./output
```

### Command Reference

```bash
# Transcribe single file
asr transcribe FILE [OPTIONS]

# Batch process files
asr batch FILES... [OPTIONS]

# List available engines
asr list-engines

# Show configuration
asr config-info

# Show help
asr --help
asr COMMAND --help
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-e, --engine` | Recognition engine | whisper |
| `-l, --language` | Language code (zh, en, etc.) | auto |
| `-o, --output` | Output directory | ./output |
| `-f, --format` | Output format (txt/srt/json) | txt |
| `-w, --workers` | Concurrent workers (batch only) | 4 |
| `-c, --config` | Config file path | config/config.yaml |
| `--debug` | Enable debug mode | False |

## Configuration

### Config File Structure

The application uses YAML configuration files in the `config/` directory:

- `config/config.yaml` - Main configuration
- `config/engines.yaml` - Engine-specific settings

### Example Configuration

**config/config.yaml**

```yaml
app:
  log_level: "INFO"

engine:
  default: "whisper"
  fallback:
    enabled: true
    max_retries: 3

audio:
  sample_rate: 16000
  channels: 1

output:
  console:
    show_timestamps: true
  export:
    formats: [txt, srt, json]
    directory: "./output"
```

**config/engines.yaml**

```yaml
whisper:
  enabled: true
  model_size: "base"  # tiny/base/small/medium/large
  device: "auto"      # auto/cpu/cuda
  language: "auto"

qwen:
  enabled: false
  api_key: "${QWEN_API_KEY}"

azure:
  enabled: false
  api_key: "${AZURE_SPEECH_KEY}"
  region: "eastasia"
```

### Environment Variables

Create a `.env` file for API keys:

```bash
# Copy example file
cp .env.example .env

# Edit with your keys
nano .env
```

**.env**

```bash
QWEN_API_KEY=sk-your-key-here
AZURE_SPEECH_KEY=your-key-here
BAIDU_APP_ID=your-app-id
BAIDU_API_KEY=your-api-key
BAIDU_SECRET_KEY=your-secret-key
```

## Engines

### Whisper (Local)

**Model Sizes:**
- `tiny` - Fastest, lowest accuracy (~39M params)
- `base` - Balanced (~74M params) **[Default]**
- `small` - Better accuracy (~244M params)
- `medium` - High accuracy (~769M params)
- `large` / `large-v2` / `large-v3` - Best accuracy (~1550M params)

**Configuration:**

```yaml
whisper:
  enabled: true
  model_size: "base"
  device: "auto"      # auto/cpu/cuda
  compute_type: "float16"  # float16/float32/int8
```

**Usage:**

```bash
asr transcribe audio.wav -e whisper -l zh
```

### Qwen (Alibaba Cloud)

**Setup:**

1. Get API key from [Dashscope Console](https://dashscope.console.aliyun.com/)
2. Add to `.env`: `QWEN_API_KEY=sk-...`
3. Enable in `config/engines.yaml`

**Configuration:**

```yaml
qwen:
  enabled: true
  model: "paraformer-realtime-v2"
  api_key: "${QWEN_API_KEY}"
```

### Azure Speech Services

**Setup:**

1. Create Azure Speech resource
2. Get API key and region
3. Add to `.env`

**Configuration:**

```yaml
azure:
  enabled: true
  region: "eastasia"
  api_key: "${AZURE_SPEECH_KEY}"
  language: "zh-CN"
```

### Baidu Speech

**Setup:**

1. Create app at [Baidu AI Cloud](https://cloud.baidu.com/product/speech/asr)
2. Get credentials
3. Add to `.env`

**Configuration:**

```yaml
baidu:
  enabled: true
  app_id: "${BAIDU_APP_ID}"
  api_key: "${BAIDU_API_KEY}"
  secret_key: "${BAIDU_SECRET_KEY}"
```

## Examples

### Example 1: Transcribe Meeting Recording

```bash
asr transcribe meeting.wav -e whisper -l zh -f srt -o ./transcripts
```

Output:
- `transcripts/meeting.txt` - Plain text
- `transcripts/meeting.srt` - Subtitle file

### Example 2: Batch Process Podcast Episodes

```bash
asr batch episode_*.wav -e whisper -w 8 -o ./podcast_transcripts
```

### Example 3: Generate Subtitles for Video

```bash
asr transcribe video_audio.wav -f srt -o ./subtitles
```

Then use the SRT file with your video editor.

### Example 4: Compare Engines

```bash
# Transcribe with Whisper
asr transcribe audio.wav -e whisper -o ./whisper_output

# Transcribe with Qwen
asr transcribe audio.wav -e qwen -o ./qwen_output

# Compare results
diff whisper_output/audio.txt qwen_output/audio.txt
```

## Troubleshooting

### Issue: "Model not found"

**Solution:** Whisper models are downloaded automatically on first use. If download fails:

```bash
# Manually download model
python -c "import whisper; whisper.load_model('base')"

# Or specify local path in config
whisper:
  model_path: "/path/to/model.pt"
```

### Issue: "Out of memory"

**Solution:** Use a smaller model or CPU:

```yaml
whisper:
  model_size: "tiny"  # or "base"
  device: "cpu"
```

### Issue: "FFmpeg not found"

**Solution:** Install FFmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Development

### Project Structure

```
ASRTerminal/
├── src/asr_terminal/
│   ├── engines/          # Recognition engines
│   ├── audio/            # Audio processing
│   ├── config/           # Configuration management
│   ├── output/           # Export and display
│   ├── cli/              # Command line interface
│   └── service.py        # Main service facade
├── config/               # Configuration files
├── tests/                # Tests
└── requirements.txt      # Dependencies
```

### Adding a Custom Engine

1. Create engine class inheriting from `ASREngine`
2. Implement required methods: `initialize()`, `recognize()`, etc.
3. Register in `engines/__init__.py`

Example:

```python
from ..engines.base import ASREngine, EngineConfig

class MyEngine(ASREngine):
    async def initialize(self):
        # Load model
        pass

    async def recognize(self, audio_data, language=None):
        # Implement recognition
        pass

# Register
EngineFactory.register_engine("my_engine", MyEngine, MyConfig)
```

## Performance Tips

1. **Use GPU acceleration** for Whisper
   ```yaml
   whisper:
     device: "cuda"
     compute_type: "float16"
   ```

2. **Batch processing** with multiple workers
   ```bash
   asr batch *.wav -w 8
   ```

3. **Use appropriate model size**
   - Use `tiny` for real-time applications
   - Use `large-v3` for highest accuracy

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Local speech recognition
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output
- [Click](https://click.palletsprojects.com/) - CLI framework

## Support

- 📧 Email: kutor1nota@outlook.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/asr-terminal/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/asr-terminal/discussions)

---

<div align="center">

**Made with ❤️ for speech recognition**

[⬆ Back to Top](#asr-terminal)

</div>
