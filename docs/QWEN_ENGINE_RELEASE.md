# ASR Terminal - Qwen引擎集成完成

## 新增功能

✅ **阿里云Qwen语音识别引擎**

已成功集成阿里云百炼平台的Qwen实时语音识别引擎！

## 主要特性

### 🎯 支持多语言和方言

- 中文（普通话、四川话、闽南语、吴语、粤语）
- 英语、日语、韩语
- 德语、法语、西班牙语、俄语
- 葡萄牙语、阿拉伯语、意大利语

### 🚀 实时流式识别

- 基于WebSocket协议
- 低延迟实时转写
- 自动VAD语音检测

### 💰 性价比高

- 新用户免费10小时（36,000秒）
- 低至 ¥0.00033/秒
- 按实际使用付费

## 快速开始

### 1. 安装依赖

```bash
pip install dashscope>=1.24.8 websocket-client
```

### 2. 获取API Key

访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/) 开通服务并获取API Key。

### 3. 配置

```bash
# 设置环境变量
export DASHSCOPE_API_KEY=sk-your-api-key
```

或编辑 `.env` 文件：
```bash
DASHSCOPE_API_KEY=sk-your-api-key
```

### 4. 使用

```bash
# 启用Qwen引擎（编辑 config/engines.yaml）
qwen:
  enabled: true

# 转录音频
asr transcribe audio.wav -e qwen -l zh

# 批量处理
asr batch *.wav -e qwen
```

## 文件更新

### 新增文件

- `src/asr_terminal/engines/qwen_engine.py` - Qwen引擎实现
- `docs/QWEN_ENGINE_GUIDE.md` - Qwen引擎使用指南
- `tests/test_qwen_engine.py` - Qwen引擎测试脚本

### 修改文件

- `requirements.txt` - 添加 DashScope SDK 依赖
- `src/asr_terminal/engines/__init__.py` - 注册Qwen引擎
- `config/engines.yaml` - 更新Qwen配置项
- `.env.example` - 添加DASHSCOPE_API_KEY说明

## 技术实现

### WebSocket连接

使用WebSocket协议实现实时音频流传输：

```python
url = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
```

### VAD语音检测

服务器端VAD自动检测语音开始和结束：

```yaml
qwen:
  enable_vad: true
  vad_threshold: 0.2
  vad_silence_duration_ms: 800
```

### 音频格式支持

- **格式**: PCM (16-bit), Opus
- **采样率**: 8kHz, 16kHz
- **声道**: 单声道

## 引擎对比

| 特性 | Whisper | Qwen | Azure |
|------|---------|------|-------|
| 类型 | 本地 | 云端 | 云端 |
| 成本 | 免费 | 付费（有免费额度） | 付费 |
| 实时性 | 慢 | 快 | 快 |
| 准确率 | 最高 | 高 | 高 |
| 离线使用 | ✅ | ❌ | ❌ |
| 多语言 | 99种 | 12种 | 100+种 |

## 使用场景

### 适合使用Qwen的场景

✅ 需要实时语音识别
✅ 对准确率要求高
✅ 中文语音识别（包括方言）
✅ 有网络环境
✅ 成本可控（有免费额度）

### 适合使用Whisper的场景

✅ 需要离线识别
✅ 预算有限（完全免费）
✅ 对隐私要求高
✅ 支持99种语言
✅ 可接受较慢的速度

## 配置示例

### 中文普通话识别

```yaml
qwen:
  enabled: true
  model: "qwen3-asr-flash-realtime"
  language: "zh"
  sample_rate: 16000
  enable_vad: true
```

### 英语识别

```yaml
qwen:
  enabled: true
  language: "en"
  sample_rate: 16000
```

### 日语识别

```yaml
qwen:
  enabled: true
  language: "ja"
  sample_rate: 16000
```

## 故障排除

### API Key问题

```bash
# 检查环境变量
echo $DASHSCOPE_API_KEY

# 设置环境变量
export DASHSCOPE_API_KEY=sk-your-key
```

### 连接问题

- 检查网络连接
- 确认URL地域（北京/新加坡）
- 验证防火墙设置

### 音频格式问题

```bash
# 转换为PCM格式
ffmpeg -i input.mp3 -f s16le -ar 16000 -ac 1 output.pcm
```

## 文档

详细使用指南请查看：[docs/QWEN_ENGINE_GUIDE.md](QWEN_ENGINE_GUIDE.md)

## 下一步

计划集成更多云端引擎：

- [ ] Azure Speech Services
- [ ] 百度语音识别
- [ ] PaddleSpeech

## 反馈

如有问题或建议，请提交Issue。

---

**版本**: v1.1.0
**日期**: 2025-01-08
**作者**: ASR Terminal Team
