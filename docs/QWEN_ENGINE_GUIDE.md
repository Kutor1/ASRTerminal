# Qwen引擎使用指南

## 概述

Qwen引擎是阿里云百炼平台提供的实时语音识别服务，支持多种语言和方言。

## 特性

- ✅ **多语言支持**：中文（普通话、四川话、闽南语、吴语、粤语）、英语、日语、德语、韩语、俄语、法语、葡萄牙语、阿拉伯语、意大利语、西班牙语
- ✅ **实时流式识别**：基于WebSocket的实时语音转文字
- ✅ **VAD语音检测**：服务器端VAD自动检测语音开始和结束
- ✅ **标点符号预测**：自动添加标点符号
- ✅ **语种识别**：自动识别音频语种

## 安装

### 1. 安装DashScope SDK

```bash
pip install dashscope>=1.24.8
```

### 2. 安装websocket-client

```bash
pip uninstall websocket-client websocket
pip install websocket-client
```

### 3. 获取API Key

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 开通百炼服务（新用户有免费额度）
3. 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key

**注意**：
- 北京地域和新加坡地域的API Key不同
- 确保使用正确地域的API Key

### 4. 配置环境变量

创建 `.env` 文件：

```bash
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
```

或直接设置：

```bash
export DASHSCOPE_API_KEY=sk-your-actual-api-key-here
```

## 配置

编辑 `config/engines.yaml`：

```yaml
qwen:
  enabled: true
  model: "qwen3-asr-flash-realtime"

  # API配置
  api_key: "${DASHSCOPE_API_KEY}"
  url: "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"

  # 识别参数
  language: "zh"  # 语言代码
  sample_rate: 16000  # 采样率：8000或16000
  format: "pcm"  # 音频格式：pcm或opus

  # VAD配置
  enable_vad: true
  vad_threshold: 0.2
  vad_silence_duration_ms: 800

  # 可选：语料文本（提升识别准确率）
  corpus_text: null
```

## 使用

### 基本用法

```bash
# 转录单个文件
asr transcribe audio.wav -e qwen -l zh

# 批量处理
asr batch *.wav -e qwen
```

### 支持的语言

| 语言 | 代码 | 说明 |
|------|------|------|
| 中文（普通话） | zh | 默认 |
| 四川话 | zh | 自动识别 |
| 粤语 | zh | 自动识别 |
| 闽南语 | zh | 自动识别 |
| 吴语 | zh | 自动识别 |
| 英语 | en | |
| 日语 | ja | |
| 韩语 | ko | |
| 德语 | de | |
| 法语 | fr | |
| 西班牙语 | es | |
| 俄语 | ru | |
| 葡萄牙语 | pt | |
| 阿拉伯语 | ar | |
| 意大利语 | it | |

### 音频格式要求

- **格式**：PCM (16-bit, mono) 或 Opus
- **采样率**：8000 Hz 或 16000 Hz
- **声道**：单声道
- **编码**：PCM需要16-bit signed integer

如果音频不是PCM格式，需要先转换：

```bash
# 使用ffmpeg转换
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 output.pcm
```

### 使用示例

#### 示例1：识别中文音频

```bash
asr transcribe meeting.wav -e qwen -l zh
```

#### 示例2：识别日语音频

```bash
asr transcribe japanese.wav -e qwen -l ja
```

#### 示例3：使用VAD模式（默认）

VAD模式会自动检测语音开始和结束：

```bash
asr transcribe interview.wav -e qwen
```

#### 示例4：批量处理

```bash
asr batch episode_*.wav -e qwen -w 4
```

## 高级配置

### VAD（语音活动检测）

VAD自动检测语音的开始和结束，适合实时场景。

```yaml
qwen:
  enable_vad: true
  vad_threshold: 0.2  # 阈值（0-1），越大越严格
  vad_silence_duration_ms: 800  # 静音持续时间（毫秒）
```

### 语料文本

提供领域相关的语料可以提升识别准确率：

```yaml
qwen:
  corpus_text: "这是一段关于人工智能的讨论"
```

### 地域选择

**北京地域**：
```yaml
url: "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
```

**新加坡地域**：
```yaml
url: "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"
```

**注意**：两个地域的API Key不同！

## 限流

| 模型 | 每秒调用次数（RPS） |
|------|---------------------|
| qwen3-asr-flash-realtime | 20 |

## 免费额度

新用户开通百炼服务后90天内，可享受：
- 36,000秒（10小时）的免费识别额度
- 适用于 qwen3-asr-flash-realtime 模型

## 价格

| 模型 | 单价 |
|------|------|
| qwen3-asr-flash-realtime | ¥0.00033/秒 |

## 故障排除

### 问题1：ImportError: DashScope SDK is not installed

**解决方案**：
```bash
pip install dashscope>=1.24.8
```

### 问题2：API key is not configured

**解决方案**：
```bash
export DASHSCOPE_API_KEY=sk-your-key
```

或在 `.env` 文件中设置：
```bash
DASHSCOPE_API_KEY=sk-your-key
```

### 问题3：认证失败

**检查**：
1. API Key是否正确
2. 使用的是正确的地域（北京/新加坡）
3. API Key是否已开通百炼服务

### 问题4：WebSocket连接失败

**检查**：
1. 网络连接是否正常
2. URL是否正确
3. 防火墙是否阻止WebSocket连接

### 问题5：识别结果不准确

**优化**：
1. 设置正确的语言代码
2. 提供语料文本（corpus_text）
3. 确保音频质量良好（16kHz推荐）
4. 使用VAD模式自动检测语音

## Python API使用

除了命令行，也可以在代码中直接使用：

```python
import asyncio
from asr_terminal.service import ASRService
from asr_terminal.config.manager import ConfigManager

async def main():
    # 初始化服务
    config = ConfigManager("config/config.yaml")
    service = ASRService(config)

    # 使用Qwen引擎
    await service.initialize("qwen")

    # 识别音频
    transcript = await service.recognize_file("audio.wav", language="zh")

    print(f"识别结果: {transcript.text}")

    await service.cleanup()

asyncio.run(main())
```

## 对比其他引擎

| 特性 | Qwen | Whisper | Azure |
|------|------|---------|-------|
| 本地运行 | ❌ | ✅ | ❌ |
| 实时流式 | ✅ | ❌ | ✅ |
| 免费额度 | ✅ (10小时) | ✅ (完全免费) | ❌ |
| 多语言支持 | ✅ 12种语言 | ✅ 99种语言 | ✅ 100+种语言 |
| 准确率 | 高 | 最高 | 高 |
| 延迟 | 低 | 高 | 低 |
| 成本 | ¥0.00033/秒 | 免费（本地） | 按使用付费 |

## 参考链接

- [官方文档](https://help.aliyun.com/zh/model-studio/qwen-real-time-speech-recognition)
- [DashScope SDK](https://github.com/aliyun/pai-dashscope)
- [获取API Key](https://help.aliyun.com/zh/model-studio/get-api-key)
- [价格说明](https://help.aliyun.com/zh/model-studio/qwen-real-time-speech-recognition#section-price-2)
