# ASR Terminal - 多引擎语音识别终端工具

<div align="center">

**支持本地和云端多种引擎的语音识别终端工具**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[**🇺🇸 English**](README.md) | 支持实时语音转文字和批量文件处理，集成多种识别引擎

[功能特性](#功能特性) • [安装](#安装) • [使用方法](#使用方法) • [配置](#配置) • [支持的引擎](#支持的引擎)

</div>

---

## 功能特性

- 🎙️ **多引擎支持**
  - 本地：OpenAI Whisper（tiny/base/small/medium/large等7种模型）
  - 云端：Qwen实时识别、FunASR异步识别（阿里云百炼）
  - 可扩展：Azure、百度、飞桨等引擎（开发中）

- 📁 **批量文件处理**
  - 多文件并发处理
  - 进度条显示
  - 性能优化

- 📝 **多种输出格式**
  - 纯文本（.txt）
  - 字幕（.srt）
  - JSON格式（带时间戳）

- ⚙️ **灵活配置**
  - YAML配置文件
  - 环境变量支持
  - 每个引擎独立配置

- 🔄 **自动降级**
  - 失败自动重试
  - 引擎自动切换

## 安装

### 系统要求

- Python 3.8 或更高版本
- FFmpeg（用于音频处理）

### 基础安装

```bash
# 克隆仓库
git clone https://github.com/Kutor1/ASRTerminal.git
cd ASRTerminal

# 安装依赖
pip install -r requirements.txt

# 安装项目
pip install -e .
```

### 可选依赖

```bash
# 云端引擎
pip install -e ".[qwen]"      # 阿里云Qwen（包含FunASR）
pip install -e ".[azure]"     # Azure Speech
pip install -e ".[baidu]"     # 百度语音
pip install -e ".[paddle]"    # 飞桨语音

# 或安装所有
pip install -e ".[all]"
```

## 使用方法

### 基本命令

#### 转录单个文件

```bash
asr transcribe audio.wav
```

#### 批量处理多个文件

```bash
asr batch audio1.wav audio2.mp3 audio3.flac
```

#### 指定引擎和语言

```bash
asr transcribe audio.wav -e whisper -l zh
```

#### 导出多种格式

```bash
asr batch *.wav -f txt -f srt -f json -o ./output
```

### 命令参考

```bash
# 转录单个文件
asr transcribe 文件路径 [选项]

# 批量处理文件
asr batch 文件列表... [选项]

# 列出可用引擎
asr list-engines

# 显示配置信息
asr config-info

# 显示帮助
asr --help
asr 命令 --help
```

### 选项说明

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-e, --engine` | 识别引擎 | whisper |
| `-l, --language` | 语言代码（zh、en等） | auto |
| `-o, --output` | 输出目录 | ./output |
| `-f, --format` | 输出格式（txt/srt/json） | txt |
| `-w, --workers` | 并发工作线程数（批量） | 4 |
| `-c, --config` | 配置文件路径 | config/config.yaml |
| `--debug` | 启用调试模式 | False |

## 配置

### 配置文件结构

项目使用 `config/` 目录下的YAML配置文件：

- `config/config.yaml` - 主配置文件
- `config/engines.yaml` - 引擎配置文件

### 配置示例

**config/config.yaml（主配置）**

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

**config/engines.yaml（引擎配置）**

```yaml
whisper:
  enabled: true
  model_size: "base"  # tiny/base/small/medium/large
  device: "auto"      # auto/cpu/cuda
  language: "auto"

qwen:
  enabled: false
  model: "qwen3-asr-flash-realtime"
  api_key: "${QWEN_API_KEY}"

funasr:
  enabled: false
  model: "fun-asr"
  api_key: "${DASHSCOPE_API_KEY}"
  language_hints: ["zh", "en"]
```

### 环境变量

创建 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
nano .env
```

**.env 示例**

```bash
# 阿里云DashScope API Key（Qwen和FunASR共用）
DASHSCOPE_API_KEY=sk-your-key-here

# Azure Speech Key
AZURE_SPEECH_KEY=your-key-here

# 百度语音
BAIDU_APP_ID=your-app-id
BAIDU_API_KEY=your-api-key
BAIDU_SECRET_KEY=your-secret-key
```

## 支持的引擎

### Whisper（本地）

**模型大小：**
- `tiny` - 最快，准确率最低（约39M参数）
- `base` - 平衡（约74M参数）**[默认]**
- `small` - 更高准确率（约244M参数）
- `medium` - 高准确率（约769M参数）
- `large` / `large-v2` / `large-v3` - 最高准确率（约1550M参数）

**配置：**

```yaml
whisper:
  enabled: true
  model_size: "base"
  device: "auto"      # auto/cpu/cuda
  compute_type: "float16"  # float16/float32/int8
```

**使用：**

```bash
asr transcribe audio.wav -e whisper -l zh
```

### Qwen（阿里云）

**特点：** 实时流式识别，WebSocket连接

**配置：**

```yaml
qwen:
  enabled: true
  model: "qwen3-asr-flash-realtime"
  api_key: "${DASHSCOPE_API_KEY}"
  language: "zh"
  sample_rate: 16000
```

**使用：**

```bash
asr transcribe audio.wav -e qwen -l zh
```

### FunASR（阿里云）

**特点：** 异步文件识别，需要公网URL，详细时间戳

**配置：**

```yaml
funasr:
  enabled: true
  model: "fun-asr"
  api_key: "${DASHSCOPE_API_KEY}"
  language_hints: ["zh", "en"]
```

**使用：**

```python
# FunASR需要公网URL
import asyncio
from asr_terminal.engines import EngineFactory

async def main():
    engine = await EngineFactory.create_engine("funasr")
    transcript = await engine.recognize_from_url(
        file_url="https://example.com/audio.wav"
    )
    print(transcript.text)

asyncio.run(main())
```

## 使用示例

### 示例1：转录会议录音

```bash
asr transcribe meeting.wav -e whisper -l zh -f srt -o ./transcripts
```

输出：
- `transcripts/meeting.txt` - 纯文本
- `transcripts/meeting.srt` - 字幕文件

### 示例2：批量处理播客

```bash
asr batch episode_*.wav -e whisper -w 8 -o ./podcast_transcripts
```

### 示例3：生成视频字幕

```bash
asr transcribe video_audio.wav -f srt -o ./subtitles
```

然后将SRT文件与视频一起使用。

### 示例4：对比不同引擎

```bash
# 使用Whisper转录
asr transcribe audio.wav -e whisper -o ./whisper_output

# 使用Qwen转录
asr transcribe audio.wav -e qwen -o ./qwen_output

# 对比结果
diff whisper_output/audio.txt qwen_output/audio.txt
```

## 故障排除

### 问题："模型未找到"

**解决方案：** Whisper模型会在首次使用时自动下载。如果下载失败：

```bash
# 手动下载模型
python -c "import whisper; whisper.load_model('base')"

# 或在配置中指定本地路径
whisper:
  model_path: "/path/to/model.pt"
```

### 问题："内存不足"

**解决方案：** 使用更小的模型或CPU：

```yaml
whisper:
  model_size: "tiny"  # 或 "base"
  device: "cpu"
```

### 问题："未找到FFmpeg"

**解决方案：** 安装FFmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 从 https://ffmpeg.org/download.html 下载
```

## 开发

### 项目结构

```
ASRTerminal/
├── src/asr_terminal/
│   ├── engines/          # 识别引擎
│   ├── audio/            # 音频处理
│   ├── config/           # 配置管理
│   ├── output/           # 导出和显示
│   ├── cli/              # 命令行接口
│   └── service.py        # 服务门面
├── config/               # 配置文件
├── tests/                # 测试
└── requirements.txt      # 依赖
```

### 添加自定义引擎

1. 创建继承自 `ASREngine` 的引擎类
2. 实现必需方法：`initialize()`、`recognize()` 等
3. 在 `engines/__init__.py` 中注册

示例：

```python
from ..engines.base import ASREngine, EngineConfig

class MyEngine(ASREngine):
    async def initialize(self):
        # 加载模型
        pass

    async def recognize(self, audio_data, language=None):
        # 实现识别
        pass

# 注册引擎
EngineFactory.register_engine("my_engine", MyEngine, MyConfig)
```

## 性能建议

1. **使用GPU加速**（Whisper）
   ```yaml
   whisper:
     device: "cuda"
     compute_type: "float16"
   ```

2. **批量处理多线程**
   ```bash
   asr batch *.wav -w 8
   ```

3. **选择合适的模型**
   - 实时应用：使用 `tiny`
   - 最高准确率：使用 `large-v3`

## 引擎对比

| 引擎 | 类型 | 输入 | 本地文件 | 时间戳 | 成本 |
|------|------|------|----------|--------|------|
| Whisper | 本地 | 文件 | ✅ | ✅ | 免费 |
| Qwen | 云端 | 流式 | ✅ | ❌ | 付费 |
| FunASR | 云端 | URL | ❌ | ✅ | 付费 |

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎贡献！请随时提交Pull Request。

## 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 本地语音识别
- [阿里云百炼](https://bailian.console.aliyun.com/) - Qwen和FunASR
- [Rich](https://rich.readthedocs.io/) - 美化终端输出
- [Click](https://click.palletsprojects.com/) - CLI框架

## 支持

- 📧 邮箱：kutor1nota@outlook.com
- 🐛 问题反馈：[GitHub Issues](https://github.com/Kutor1/ASRTerminal/issues)
- 💬 讨论：[GitHub Discussions](https://github.com/Kutor1/ASRTerminal/discussions)

---

<div align="center">

**用 ❤️ 打造，专注于语音识别**

[⬆ 返回顶部](#asr-terminal---多引擎语音识别终端工具)

</div>
