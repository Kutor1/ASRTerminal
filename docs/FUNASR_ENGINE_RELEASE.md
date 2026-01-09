# ASR Terminal - FunASR引擎集成完成

## 新增功能

✅ **阿里云FunASR异步文件语音识别引擎**

已成功集成阿里云DashScope平台的FunASR异步语音识别引擎！

## 主要特性

### 🎯 专为录音文件设计

- 异步任务处理，适合长音频
- 支持公网URL输入
- 批量文件识别
- 详细的句子级时间戳

### 💡 与Qwen引擎的对比

| 特性 | FunASR | Qwen | Whisper |
|------|--------|------|---------|
| 输入方式 | URL | 音频流 | 本地文件 |
| 处理模式 | 异步 | 实时 | 同步 |
| 适用场景 | 录音文件 | 实时语音 | 离线识别 |
| 时间戳 | ✅ 详细 | ❌ | ✅ 有 |
| 批量处理 | ✅ | ❌ | ✅ |
| 本地文件 | ❌ | ✅ | ✅ |
| 成本 | 付费 | 付费 | 免费 |

### 🚀 核心优势

- **异步处理**：提交任务后轮询等待，不阻塞
- **高准确率**：基于Paraformer2模型
- **详细时间戳**：句子级别的时间戳信息
- **批量支持**：一次提交多个URL
- **多语言**：支持中文、英语、日语等9种语言

## 快速开始

### 1. 安装依赖

FunASR使用DashScope SDK，与Qwen共享依赖：

```bash
pip install dashscope>=1.24.8
```

### 2. 配置API Key

```bash
export DASHSCOPE_API_KEY=sk-your-actual-key
```

### 3. 配置引擎

编辑 `config/engines.yaml`：

```yaml
funasr:
  enabled: true
  model: "fun-asr"
  api_key: "${DASHSCOPE_API_KEY}"
  language_hints: ["zh", "en"]
  poll_interval: 2
  max_wait_time: 300
```

### 4. Python API使用

```python
import asyncio
from asr_terminal.engines import EngineFactory

async def main():
    # 创建引擎
    engine = await EngineFactory.create_engine("funasr", {
        "api_key": "sk-your-key"
    })

    # 识别公网URL
    transcript = await engine.recognize_from_url(
        file_url="https://example.com/audio.wav"
    )

    print(transcript.text)

    await engine.cleanup()

asyncio.run(main())
```

## ⚠️ 重要说明

### URL要求

**FunASR引擎只接受公网可访问的URL，不支持本地文件！**

解决方案：
1. **上传到云存储**（推荐）：阿里云OSS、腾讯云COS等
2. **使用Whisper引擎**：本地文件识别
3. **使用Qwen引擎**：实时音频流识别

### 云存储方案

#### 阿里云OSS

```python
import oss2

# 上传到OSS
auth = oss2.Auth('access-key', 'secret-key')
bucket = oss2.Bucket(auth, 'endpoint', 'bucket-name')
bucket.put_object_from_file('audio.wav', 'local_audio.wav')

# 生成公网URL
file_url = "https://bucket.oss-region.aliyuncs.com/audio.wav"
```

#### 临时服务器

```python
from http.server import HTTPServer, SimpleHTTPRequestServer
import threading

# 启动HTTP服务器
threading.Thread(
    target=lambda: HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler).serve_forever(),
    daemon=True
).start()

file_url = "http://your-ip:8000/audio.wav"
```

## 文件更新

### 新增文件

- `src/asr_terminal/engines/funasr_engine.py` - FunASR引擎实现
- `docs/FUNASR_ENGINE_GUIDE.md` - 详细使用指南
- `tests/test_funasr_engine.py` - 测试脚本

### 修改文件

- `config/engines.yaml` - 添加FunASR配置
- `src/asr_terminal/engines/__init__.py` - 注册FunASR引擎

## 技术实现

### 异步任务处理

```python
# 1. 提交异步任务
task_response = Transcription.async_call(
    model='fun-asr',
    file_urls=[url]
)

# 2. 轮询等待结果
transcription_response = Transcription.wait(task_id)

# 3. 获取识别结果
result_url = transcription_response.output['results'][0]['transcription_url']
result_data = json.loads(request.urlopen(result_url).read())
```

### 轮询机制

```python
while elapsed < max_wait_time:
    response = Transcription.wait(task_id)

    if response.status_code == HTTPStatus.OK:
        return response

    await asyncio.sleep(poll_interval)
```

### 结果解析

```python
# 提取文本
text = result_data["sentences"][0]["text"]

# 提取时间戳
begin_time = result_data["sentences"][0]["begin_time"]
end_time = result_data["sentences"][0]["end_time"]
```

## 使用场景

### ✅ 适合使用FunASR

- 音频文件已存储在云
- 需要详细时间戳
- 批量处理多个文件
- 长音频（>10分钟）
- 对准确率要求高

### ❌ 不适合使用FunASR

- 本地音频文件
- 实时语音识别
- 需要立即返回结果
- 短音频片段（<5秒）

### 引擎选择指南

```
本地文件 + 离线使用 → Whisper引擎
本地文件 + 实时识别 → Qwen引擎
云端URL + 长音频 → FunASR引擎
云端URL + 需要时间戳 → FunASR引擎
```

## 配置示例

### 中文识别

```yaml
funasr:
  enabled: true
  language_hints: ["zh"]
```

### 中英混合

```yaml
funasr:
  enabled: true
  language_hints: ["zh", "en"]
```

### 长音频处理

```yaml
funasr:
  enabled: true
  poll_interval: 5
  max_wait_time: 600  # 10分钟
```

### 批量处理

```python
urls = [
    "https://example.com/audio1.wav",
    "https://example.com/audio2.wav",
    "https://example.com/audio3.wav"
]

# FunASR自动批量处理
for url in urls:
    transcript = await engine.recognize_from_url(file_url=url)
```

## 性能优化

### 批量提交

```python
# 一次提交多个URL（更高效）
task_response = Transcription.async_call(
    model='fun-asr',
    file_urls=[url1, url2, url3]
)
```

### 轮询策略

| 音频时长 | poll_interval | max_wait_time |
|---------|---------------|---------------|
| < 1分钟 | 2秒 | 60秒 |
| 1-10分钟 | 5秒 | 300秒 |
| > 10分钟 | 10秒 | 600秒 |

### 错误重试

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        transcript = await engine.recognize_from_url(url)
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(5)  # 等待后重试
```

## 价格和限额

### 免费额度

新用户90天内：36,000秒（10小时）

### 计费标准

- **单价**：约 ¥0.00033/秒
- **计费**：按实际识别时长

### 限额

- 并发：20 RPS
- 文件大小：建议<100MB
- 音频时长：建议<1小时

## 测试

运行测试脚本：

```bash
# 设置API Key
export DASHSCOPE_API_KEY=sk-your-key

# 运行测试
python tests/test_funasr_engine.py
```

测试脚本会：
1. 验证API Key配置
2. 使用DashScope示例URL测试
3. 显示识别结果
4. 展示时间戳信息

## 文档

- **使用指南**：`docs/FUNASR_ENGINE_GUIDE.md`
- **API文档**：https://help.aliyun.com/zh/model-studio/
- **FunASR项目**：https://github.com/alibaba-damo-academy/FunASR

## 下一步

现在ASR Terminal支持3种引擎：

- ✅ **Whisper** - 本地离线识别
- ✅ **Qwen** - 实时流式识别
- ✅ **FunASR** - 异步文件识别

计划集成更多引擎：

- [ ] Azure Speech Services
- [ ] 百度语音识别
- [ ] PaddleSpeech

## 示例代码

### 完整示例

```python
import asyncio
from asr_terminal.engines import EngineFactory

async def main():
    # 创建FunASR引擎
    engine = await EngineFactory.create_engine("funasr", {
        "api_key": "sk-your-key",
        "language_hints": ["zh", "en"]
    })

    # 准备音频URL（公网可访问）
    audio_url = "https://example.com/meeting.wav"

    # 识别
    transcript = await engine.recognize_from_url(audio_url)

    # 输出结果
    print(f"识别文本: {transcript.text}")
    print(f"检测语言: {transcript.language}")
    print(f"音频时长: {transcript.duration:.2f}秒")

    # 显示时间轴
    for seg in transcript.segments:
        print(f"[{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}")

    await engine.cleanup()

asyncio.run(main())
```

## 反馈

如有问题或建议，请提交Issue或Pull Request。

---

**版本**: v1.2.0
**日期**: 2025-01-09
**作者**: ASR Terminal Team
