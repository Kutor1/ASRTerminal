# FunASR引擎使用指南

## 概述

FunASR是阿里云DashScope提供的**异步文件语音识别服务**，专门用于处理录音文件的语音转文字。

## 特性

- ✅ **异步处理**：提交任务后异步等待结果，适合长音频
- ✅ **批量识别**：一次提交多个音频文件URL
- ✅ **URL输入**：支持公网可访问的音频URL
- ✅ **高准确率**：基于Paraformer2模型，识别准确率高
- ✅ **多语言支持**：中文、英语、日语、韩语等
- ✅ **时间戳**：提供详细的句子级别时间戳

## 与Qwen引擎的区别

| 特性 | FunASR | Qwen |
|------|--------|------|
| 输入方式 | URL（公网可访问） | 音频流（PCM/Opus） |
| 处理模式 | 异步任务 | 实时WebSocket |
| 适用场景 | 录音文件 | 实时语音 |
| 本地文件 | ❌ 需上传到云存储 | ✅ 支持直接传输 |
| 时间戳 | ✅ 详细 | ❌ 无 |
| 批量处理 | ✅ 支持多文件 | ❌ 单次处理 |

## 安装

FunASR使用DashScope SDK，与Qwen引擎共享依赖：

```bash
pip install dashscope>=1.24.8
```

## 获取API Key

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 开通百炼服务
3. 获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key

```bash
# 设置环境变量
export DASHSCOPE_API_KEY=sk-your-actual-api-key
```

## 配置

编辑 `config/engines.yaml`：

```yaml
funasr:
  enabled: true
  model: "fun-asr"

  # API配置（与Qwen共享）
  api_key: "${DASHSCOPE_API_KEY}"
  base_url: "https://dashscope.aliyuncs.com/api/v1"

  # 识别参数
  language_hints: ["zh", "en"]  # 语言提示

  # 任务设置
  poll_interval: 2  # 轮询间隔（秒）
  max_wait_time: 300  # 最大等待时间（秒）
```

## 使用方法

### ⚠️ 重要说明

**FunASR引擎只接受公网可访问的URL，不支持本地文件！**

对于本地文件，您需要：
1. 使用Whisper引擎（本地识别）
2. 使用Qwen引擎（实时识别）
3. 将本地文件上传到云存储（如阿里云OSS），然后使用FunASR识别URL

### 方式1：Python API使用

```python
import asyncio
from asr_terminal.service import ASRService
from asr_terminal.config.manager import ConfigManager

async def main():
    # 初始化服务
    config = ConfigManager("config/config.yaml")
    service = ASRService(config)

    # 初始化FunASR引擎
    await service.initialize("funasr")

    # 识别公网可访问的音频URL
    audio_url = "https://example.com/audio.wav"

    # 使用FunASR特有的URL识别方法
    engine = service.engine
    transcript = await engine.recognize_from_url(
        file_url=audio_url,
        language_hints=["zh", "en"]
    )

    print(f"识别结果: {transcript.text}")

    await service.cleanup()

asyncio.run(main())
```

### 方式2：直接使用FunASR引擎

```python
import asyncio
from asr_terminal.engines import EngineFactory
from asr_terminal.engines.funasr_engine import FunASRConfig

async def main():
    # 创建引擎
    config = FunASRConfig(
        api_key="sk-your-api-key",
        language_hints=["zh", "en"]
    )

    engine = await EngineFactory.create_engine("funasr", {
        "api_key": "sk-your-api-key",
        "language_hints": ["zh", "en"]
    })

    # 识别URL
    transcript = await engine.recognize_from_url(
        file_url="https://example.com/audio.wav"
    )

    print(transcript.text)

    await engine.cleanup()

asyncio.run(main())
```

### 方式3：使用FunASR原始API

如果您有多个音频文件的URL，可以直接使用FunASR API：

```python
from http import HTTPStatus
from dashscope.audio.asr import Transcription
from urllib import request
import dashscope
import os
import json

# 配置API
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 提交异步任务
task_response = Transcription.async_call(
    model='fun-asr',
    file_urls=[
        'https://example.com/audio1.wav',
        'https://example.com/audio2.wav'
    ],
    language_hints=['zh', 'en']
)

# 等待任务完成
transcription_response = Transcription.wait(task=task_response.output.task_id)

# 获取结果
if transcription_response.status_code == HTTPStatus.OK:
    for transcription in transcription_response.output['results']:
        if transcription['subtask_status'] == 'SUCCEEDED':
            url = transcription['transcription_url']
            result = json.loads(request.urlopen(url).read().decode('utf8'))
            print(json.dumps(result, indent=4, ensure_ascii=False))
```

## 云存储方案

由于FunASR需要公网URL，您可以将本地文件上传到云存储：

### 方案1：阿里云OSS

```python
import oss2

# 配置OSS
auth = oss2.Auth('your-access-key-id', 'your-access-key-secret')
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'your-bucket-name')

# 上传文件
bucket.put_object_from_file('audio.wav', 'local_audio.wav')

# 生成公网URL（需要设置bucket为公共读）
file_url = f"https://your-bucket.oss-cn-hangzhou.aliyuncs.com/audio.wav"

# 使用FunASR识别
transcript = await engine.recognize_from_url(file_url=file_url)
```

### 方案2：临时文件服务器

您也可以搭建临时文件服务器：

```python
from http.server import HTTPServer, SimpleHTTPRequestServer
import threading

# 在后台启动简单的HTTP服务器
def start_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestServer)
    server.serve_forever()

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# 确保端口对外开放
file_url = "http://your-server-ip:8000/audio.wav"
```

## 支持的音频格式

### URL要求

- URL必须公网可访问
- 支持HTTP/HTTPS协议
- 文件大小建议不超过100MB
- 音频时长建议不超过1小时

### 音频格式

- **格式**：WAV, MP3, FLAC, M4A等常见格式
- **采样率**：8kHz - 48kHz
- **编码**：支持各种编码格式

## 语言支持

| 语言 | 代码 | 说明 |
|------|------|------|
| 中文 | zh | 默认 |
| 英语 | en | |
| 日语 | ja | |
| 韩语 | ko | |
| 粤语 | yue | |
| 德语 | de | |
| 法语 | fr | |
| 西班牙语 | es | |
| 俄语 | ru | |

## 配置示例

### 示例1：中文识别

```yaml
funasr:
  enabled: true
  language_hints: ["zh"]
  poll_interval: 2
  max_wait_time: 300
```

### 示例2：中英混合

```yaml
funasr:
  enabled: true
  language_hints: ["zh", "en"]
```

### 示例3：长音频处理

```yaml
funasr:
  enabled: true
  poll_interval: 5  # 降低轮询频率
  max_wait_time: 600  # 增加等待时间到10分钟
```

## 输出格式

FunASR返回详细的识别结果：

```json
{
  "sentences": [
    {
      "text": "这是第一句话",
      "begin_time": 0,
      "end_time": 2500,
      "confidence": 0.98
    },
    {
      "text": "这是第二句话",
      "begin_time": 2600,
      "end_time": 5000,
      "confidence": 0.95
    }
  ],
  "language": "zh",
  "duration": 5.0
}
```

## 性能建议

### 批量处理

```python
# 一次提交多个URL
task_response = Transcription.async_call(
    model='fun-asr',
    file_urls=[
        'https://example.com/audio1.wav',
        'https://example.com/audio2.wav',
        'https://example.com/audio3.wav'
    ]
)
```

### 轮询策略

- **短音频**（<1分钟）：`poll_interval: 2`
- **中长音频**（1-10分钟）：`poll_interval: 5`
- **长音频**（>10分钟）：`poll_interval: 10`

### 超时设置

根据音频长度设置合理的超时时间：

```yaml
# 一般音频：5分钟
max_wait_time: 300

# 长音频：10-30分钟
max_wait_time: 1800
```

## 错误处理

### 常见错误

#### 1. URL不可访问

```python
RecognitionError: Failed to submit FunASR task
```

**解决方案**：
- 确保URL公网可访问
- 检查防火墙设置
- 验证文件是否存在

#### 2. 任务超时

```python
RecognitionError: FunASR task timeout after 300s
```

**解决方案**：
- 增加`max_wait_time`
- 检查音频文件大小
- 考虑分割长音频

#### 3. API Key无效

```python
EngineInitializationError: DashScope API key is not configured
```

**解决方案**：
```bash
export DASHSCOPE_API_KEY=sk-your-actual-key
```

## 价格和限额

### 免费额度

新用户开通百炼服务后90天内：
- 免费识别时长：36,000秒（10小时）

### 计费

- **单价**：约 ¥0.00033/秒
- **计费方式**：按实际识别时长计费

### 限额

- **并发限制**：20 RPS
- **文件大小**：建议不超过100MB
- **音频时长**：建议不超过1小时

## 使用场景推荐

### ✅ 适合使用FunASR

- 已有云存储的音频文件
- 需要详细时间戳
- 批量处理多个文件
- 长音频文件（>10分钟）
- 对准确率要求高

### ❌ 不适合使用FunASR

- 本地音频文件（无云存储）
- 实时语音识别
- 需要立即返回结果
- 短音频片段（<5秒）

## 完整示例

### 示例：批量处理URL列表

```python
import asyncio
from asr_terminal.engines import EngineFactory

async def batch_process_urls():
    # 创建引擎
    engine = await EngineFactory.create_engine("funasr", {
        "api_key": "sk-your-key",
        "language_hints": ["zh", "en"]
    })

    # URL列表
    urls = [
        "https://example.com/meeting1.wav",
        "https://example.com/meeting2.wav",
        "https://example.com/interview.wav"
    ]

    # 批量处理
    for url in urls:
        try:
            transcript = await engine.recognize_from_url(file_url=url)
            print(f"{url}: {transcript.text[:100]}...")
        except Exception as e:
            print(f"Error processing {url}: {e}")

    await engine.cleanup()

asyncio.run(batch_process_urls())
```

## 最佳实践

1. **使用云存储**：将音频文件上传到阿里云OSS以获得最佳性能
2. **批量处理**：一次提交多个URL提高效率
3. **合理设置超时**：根据音频长度调整`max_wait_time`
4. **语言提示**：提供准确的语言提示可提高识别率
5. **错误重试**：实现自动重试机制处理网络问题

## 参考链接

- [DashScope ASR API文档](https://help.aliyun.com/zh/model-studio/)
- [获取API Key](https://help.aliyun.com/zh/model-studio/get-api-key)
- [FunASR模型介绍](https://github.com/alibaba-damo-academy/FunASR)
