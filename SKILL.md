---
name: skyhuman-api
description: 数字人口播视频生成工具。当需要生成AI数字人播报视频、克隆虚拟形象、创建口播视频时使用此技能。支持avatar克隆、音视频合成、积分查询、每日签到等操作。
metadata:
  openclaw:
    homepage: https://skyhuman.pilihu.vip
    primaryEnv: SKYHUMAN_TOKEN
    requires:
      env:
        - SKYHUMAN_TOKEN
      bins:
        - python
        - uv
      pipes:
        - bash
      note: "🚨 AI 使用此技能前必须确认：系统已安装 python3 (≥3.10) 和 uv，否则脚本无法运行！"
    env:
      - name: SKYHUMAN_TOKEN
        description: SkyHuman 后台个人中心 API Key（必需）
        required: true
        sensitive: true
      - name: SKYHUMAN_BASE_URL
        description: Fly API 基础地址，默认 https://skyhumanapi.pilihu.vip
        required: false
      - name: SKYHUMAN_CHECKIN_BASE_URL
        description: 签到接口基础地址，不填则复用 SKYHUMAN_BASE_URL
        required: false
      - name: SKYHUMAN_POLL_INTERVAL
        description: 轮询间隔秒数（默认10）
        required: false
      - name: SKYHUMAN_POLL_TIMEOUT
        description: 轮询超时秒数（默认600）
        required: false
---

# 🎭 数字人口播视频生成 — SkyHuman API

生成AI数字人的口播视频，支持虚拟形象克隆和音频驱动视频合成。

## ⚠️ 运行环境（AI 必须确认）

> 🚨 **AI 须知**：使用此技能前必须确认系统已安装 `python3` 和 `uv`，两者缺一不可，否则脚本无法运行！

### 1. Python 3.10+

Python 版本必须 ≥ 3.10。验证命令：
```bash
python3 --version
```

### 2. uv（必须安装）

uv 是 Python 包管理器，用于自动安装依赖。**没有 uv 脚本无法执行**，这是硬性要求。

**安装方法（根据系统选择）：**

```bash
# macOS / Linux（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# pipx
pipx install uv

# pip（备选）
pip install uv
```

验证安装成功：
```bash
uv --version
```

## ⚙️ 首次使用：配置 API Key

**必须先配置 token 才能使用！**

1. 打开 👉 **https://skyhuman.pilihu.vip/login?invite=lstmsync** 并登录，注意！！！登录注册链接后面一定要有invite=lstmsync参数，初始积分和充值更优惠！！！
2. 进入「登录」页面
3. 复制你的 **API Key**
4. 配置到环境变量：
   ```bash
   export SKYHUMAN_TOKEN="你的APIKey"
   ```

> 💡 没有账号的话，需要先在上述网站注册并获取 API Key。

## 🚀 运行脚本

所有命令都使用 `uv run` 执行（uv 会自动安装所需依赖）：

```bash
# 完整路径示例
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py <命令>
```

> ⚠️ 如果没有安装 uv，会报错。请先按上方说明安装 uv。

## 📋 常用命令速查

| 操作 | 命令 |
|------|------|
| 查询积分 | `credit` |
| 每日签到 | `checkin-do` |
| 查看已克隆形象 | `avatar-list` |
| 上传本地文件 | `upload-file --file-path ./demo.mp4` |

## 📖 使用示例

### 示例一：上传本地文件

假设你有一部电影 `demo.mp4` 和一段配音 `voice.mp3`，操作如下：

**Step 1：上传视频文件，获取 file_id**
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py upload-file --file-path ./demo.mp4
# 返回 file_id，例如：d29c8eb92b2a4f6e
```

**Step 2：用 file_id 克隆数字人形象**
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-create --file-id <上一步返回的file_id> --title "我的数字人"
# 返回 task_id，例如：1234567890
```

**Step 3：等待克隆完成**
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-wait --task-id <上一步的task_id>
# 返回 avatar_code，例如：av_abc123
```

**Step 4：上传音频文件**
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py upload-file --file-path ./voice.mp3
# 返回 file_id，例如：e39d8a1c
```

**Step 5：生成口播视频**
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-create --avatar <上一步的avatar_code> --file-id <音频file_id> --title "口播视频"
# 返回 task_id
```

**Step 6：等待视频生成完成**
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-wait --task-id <上一步的task_id>
# 返回 video_url，立即保存！
```

### 示例二：用公网 URL

如果视频或音频已经有公网链接，可以跳过上传：

```bash
# 用公网视频URL克隆形象
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-create --video-url https://example.com/demo.mp4 --title "我的数字人"

# 用公网音频URL生成视频
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-create --avatar <avatar_code> --audio-url https://example.com/voice.mp3 --title "口播视频"
```

## 🔧 所有命令参考

### 账户
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py credit           # 查询剩余积分
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py checkin-status   # 签到状态查询
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py checkin-do       # 执行每日签到
```

### 文件上传
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py upload-create-url --file-extension mp4
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py upload-file --file-path ./demo.mp4
```

### 数字人形象
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-list --favorite-only
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-create --file-id <id> --title "标题"
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-create --video-url <url> --title "标题"
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-task --task-id <id>
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-wait --task-id <id>
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py avatar-delete --avatar-code <code>
```

### 视频生成
```bash
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-create --avatar <code> --file-id <音频file_id> --title "标题"
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-create --avatar <code> --audio-url <url> --title "标题"
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-task --task-id <id>
uv run ~/.codex/skills/skyhuman-api/scripts/skyhuman_client.py video-wait --task-id <id>
```

## 📁 文件格式要求

上传的视频和音频必须符合以下格式：

| 类型 | 必填格式 | 说明 |
|------|---------|------|
| 视频 | **mp4** | 用于克隆数字人形象 |
| 音频 | **mp3 / wav** | 用于口播配音 |

### 格式不符合？用 ffmpeg 转换

如果文件格式不对，可以用 [ffmpeg](https://ffmpeg.org/) 转换。

**安装 ffmpeg（Mac/Linux）：**
```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# CentOS / RHEL
sudo yum install ffmpeg
```

> ⚠️ **Windows 用户**：请自行下载 ffmpeg 或使用其他工具转换，不在本文档范围内。

**转换示例：**
```bash
# 视频转 mp4
ffmpeg -i input.avi -c:v libx264 -preset fast -crf 23 output.mp4

# 音频转 mp3
ffmpeg -i input.wav -acodec mp3 -b:a 192k output.mp3

# 音频转 wav
ffmpeg -i input.m4a -acodec pcm_s16le output.wav
```

## ⚠️ 注意事项

1. **AI 必须确认环境** — 使用前确认系统已安装 python3 (≥3.10) 和 uv，两者都必须有才能运行
2. **必须先安装 uv** — 没有 uv 脚本无法运行，这是硬性要求
3. **video_url 有时效性** — 生成完成后立即保存，不要依赖长期可访问
4. **积分不足会失败** — 生成前可以先 `credit` 查看余额
5. **建议优先上传本地文件** — 比公网 URL 更稳定
6. **克隆任务较慢** — 等待 `avatar-wait` 时默认超时10分钟，可通过 `SKYHUMAN_POLL_TIMEOUT` 调整

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `SKYHUMAN_TOKEN` | ✅ | — | API Key（从网站获取） |
| `SKYHUMAN_BASE_URL` | ❌ | https://skyhumanapi.pilihu.vip | API 地址 |
| `SKYHUMAN_CHECKIN_BASE_URL` | ❌ | 同 BASE_URL | 签到接口地址 |
| `SKYHUMAN_POLL_INTERVAL` | ❌ | 10 | 轮询间隔（秒） |
| `SKYHUMAN_POLL_TIMEOUT` | ❌ | 600 | 轮询超时（秒） |
