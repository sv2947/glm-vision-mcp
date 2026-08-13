# glm-vision-mcp

封装智谱 **GLM-4.6V-Flash** 视觉模型的 MCP Server，配套一个 ZCode Vision Skill。stdio 传输，对外暴露图片/视频/文件理解工具，底层用 httpx 调智谱 REST API。

> 📌 **想快速用起来 / 分享给朋友**：让 Agent 读 [PROMPT.md](./PROMPT.md)，把里面的提示词发给你的 AI Agent 即可自动完成安装。

## 仓库结构

```
glm-vision-mcp/
├── server.py           # MCP Server 主程序（FastMCP + httpx）
├── install.py          # ★ 一键安装脚本（跨平台，Agent 用）
├── pyproject.toml      # 项目元数据 + hatchling 构建
├── requirements.txt    # 依赖：mcp, httpx
├── .env.example        # API Key 占位模板
├── skill/
│   └── SKILL.md        # ZCode Vision Skill（/vision 触发）
├── AGENTS.md           # 给 AI Agent 看的自动安装指引
├── PROMPT.md           # 给朋友的提示词（复制发给 Agent 即可自动安装）
├── MIGRATE.md          # 换机迁移指南
└── README.md
```

## 工具

| 工具 | 说明 |
|---|---|
| `analyze_image` | 单模态理解。传一个媒体（图片/视频/文件）+ 提问，返回模型回答 |
| `batch_analyze_images` | 并发批量分析多个媒体（限并发 5），单项失败不影响整体 |

### `analyze_image` 参数

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `prompt` | str | 必填 | 提问内容 |
| `media_url` | str | 必填 | 公网 URL / 本地文件路径 / 裸 base64 字符串 |
| `media_type` | `"image"\|"video"\|"file"` | `"image"` | 媒体类型，对应 API 的 image_url/video_url/file_url |
| `thinking` | bool | `False` | 启用深度思考模式 |
| `temperature` | float | `0.7` | 采样温度 |
| `max_tokens` | int | — | 最大输出 token，省略则不限 |

> 注意：智谱 API 不支持同一请求同时传 image/video/file，每次调用只处理一种媒体类型。

### `batch_analyze_images` 参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `media_urls` | list[str] | 多个媒体 URL/路径/base64 |
| `prompt` | str | 对每项复用的提问 |
| `media_type` | str | 同上，默认 `"image"` |
| `thinking` | bool | 同上 |

返回 `[{index, url, ok, result/error}, ...]`。

## API Key

从环境变量 `ZHIPUAI_API_KEY` 读取。源码不含任何 Key 字面量。

获取地址：https://open.bigmodel.cn/usercenter/apikeys

## 安装

```bash
git clone <本仓库地址> glm-vision-mcp
cd glm-vision-mcp
pip install -r requirements.txt   # 需要 Python 3.10+
```

## 接入 ZCode

### 1. 注册 MCP Server

在 `~/.zcode/cli/config.json` 的 `mcp.servers` 下添加（路径按实际安装位置调整）：

```json
{
  "mcp": {
    "servers": {
      "glm-vision": {
        "type": "stdio",
        "command": "C:\\Program Files\\Python312\\python.exe",
        "args": [
          "C:\\path\\to\\glm-vision-mcp\\server.py"
        ],
        "env": {
          "ZHIPUAI_API_KEY": "your-key-here"
        },
        "enabled": true,
        "timeoutMs": 120000
      }
    }
  }
}
```

> 注意：ZCode 配置文件不展开 `${...}` 模板变量，必须用绝对路径。Windows 下 `command` 指向 python 可执行文件（`.exe`），避免 `command not found`。

### 2. 安装 Skill

把 `skill/` 目录复制到 ZCode 的 skills 目录，重命名为 `vision`：

```bash
# 用户级（所有项目可用，推荐）
cp -r skill ~/.zcode/skills/vision

# 或项目级
cp -r skill <project>/.zcode/skills/vision
```

### 3. 重启 ZCode

重启后：
- Settings → MCP 能看到 `glm-vision` 显示 connected
- 对 AI 说 `/vision 帮我识别这张图 <路径或URL>`，或自然语言「看下这张图」「分析这个截图」「批量识别这几张」均可触发

## 底层 API

- 端点：`POST https://open.bigmodel.cn/api/paas/v4/chat/completions`
- 模型：`glm-4.6v-flash`
- 认证：`Authorization: Bearer <ZHIPUAI_API_KEY>`
- 请求体格式：OpenAI 兼容多模态，`content` 为数组，元素 type 为 `image_url` / `video_url` / `file_url` / `text`

## 注意事项

- `glm-4.6v-flash` 是免费模型，**有限流**（高频返回 `429 该模型当前访问量过大`）。批量调用建议拉开间隔，或在高峰期重试。
- 本地文件路径会被自动读取并按扩展名转 `data:<mime>;base64,...`，无需手动转 base64。
- 传给 `media_url` 的裸字符串若不是合法路径，会被当作裸 base64 处理。

## 换机迁移

换电脑时按 [MIGRATE.md](./MIGRATE.md) 操作。
