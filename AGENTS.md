# AGENTS.md — glm-vision-mcp 自动安装指引（给 AI Agent 看）

> 本文档写给 AI Agent 读，请严格按步骤执行。每一步都有验证点，完成所有步骤后向用户汇报结果。

## 这是什么

**glm-vision-mcp** 是一个 MCP Server + Vision Skill 组合包，封装智谱 GLM-4.6V-Flash 视觉模型，让 AI Agent 具备图片理解能力（识别 URL 图片、本地图片、批量图片）。

- MCP Server 提供 2 个工具：`analyze_image`（单图）、`batch_analyze_images`（批量）
- Vision Skill 提供 `/vision` 触发入口（仅 ZCode 需要装）

## 安装目标（4 件事）

1. 安装 Python 依赖（mcp、httpx）
2. 在用户的 MCP 客户端配置中注册 `glm-vision` server
3. （仅 ZCode）安装 vision skill
4. 让用户提供**他自己的**智谱 API Key

## 环境要求

- **Python 3.10+**。用 `python --version` 确认，没有则先让用户安装。
- **智谱 API Key**：用户需要先在 https://open.bigmodel.cn/usercenter/apikeys 注册并创建 Key。**用用户的 Key，绝不要用仓库里任何占位符或示例 Key。**

---

## Step 1：安装依赖

在仓库根目录执行：

```bash
pip install -r requirements.txt
```

验证：`python -c "import mcp, httpx; print('ok')"` 无报错。

> Windows 下若 `python` 命令不存在，试 `py -3` 或 `python3`，并把后续所有 `python` 换成实际可用的命令。记下这个命令，Step 2 要用。

## Step 2：注册 MCP Server

MCP server 的定义如下（不同客户端格式略有差异，见下）：

- **command**：本机可用的 python 命令或绝对路径（如 Windows 的 `C:\Program Files\Python312\python.exe`）
- **args**：`["<仓库绝对路径>/server.py"]`
- **env**：`{"ZHIPUAI_API_KEY": "<用户自己的 Key>"}`

### 情况 A：客户端用标准 `mcpServers` 顶层键（Claude Desktop、Cursor、VS Code 等大部分 IDE）

在这些客户端的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "glm-vision": {
      "type": "stdio",
      "command": "<python 命令或绝对路径>",
      "args": ["<仓库绝对路径>/server.py"],
      "env": {
        "ZHIPUAI_API_KEY": "<用户自己的 Key>"
      },
      "enabled": true,
      "timeoutMs": 120000
    }
  }
}
```

### 情况 B：客户端是 ZCode

ZCode 用嵌套 `mcp.servers`，配置在 `~/.zcode/cli/config.json`。读取现有文件，在 `mcp.servers` 下合并（保留原有内容，不要覆盖）：

```json
{
  "mcp": {
    "servers": {
      "glm-vision": {
        "type": "stdio",
        "command": "<python 绝对路径>",
        "args": ["<仓库绝对路径>/server.py"],
        "env": {
          "ZHIPUAI_API_KEY": "<用户自己的 Key>"
        },
        "enabled": true,
        "timeoutMs": 120000
      }
    }
  }
}
```

> ZCode 注意：配置文件不展开 `${...}` 模板，必须用绝对路径；Windows 下 `command` 指向 `.exe` 路径。

### 验证（两种情况通用）

用这个命令直接测试 server 能启动并返回工具列表：

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | ZHIPUAI_API_KEY=<用户的Key> <python> <仓库绝对路径>/server.py
```

期望输出里能看到 `analyze_image` 和 `batch_analyze_images`。如果报错，按文末"常见问题"排查。

## Step 3：（仅 ZCode）安装 Vision Skill

把仓库的 `skill/` 目录复制到用户级 skills 目录：

```bash
cp -r skill ~/.zcode/skills/vision
```

> 若 `~/.zcode/skills/vision` 已存在，先备份或确认覆盖。此步对非 ZCode 客户端可跳过。

## Step 4：让用户重启客户端

MCP 配置改动需要重启客户端才生效。告诉用户：
- ZCode：重启 ZCode，在 Settings → MCP 确认 `glm-vision` 显示 connected
- 其他 IDE：按该 IDE 的方式重启/重新加载 MCP

重启后让用户说一句「用 vision 识别一张图」或 `/vision` 测试，能识别即成功。

---

## 常见问题

| 症状 | 原因 | 解决 |
|---|---|---|
| `python: command not found` / `py` 报错 | python 命令名不对 | 用 `where python` / `py -3 --version` 找可用命令 |
| server 启动报 `ZHIPUAI_API_KEY 未设置` | env 没配或 Key 为空 | 确认配置里 `env.ZHIPUAI_API_KEY` 填了用户 Key |
| MCP 工具不出现 | 配置没加载或格式错 | 检查 JSON 语法；ZCode 检查是否用了 `mcp.servers` 嵌套 |
| 调用报 `429 该模型当前访问量过大` | 免费模型限流 | 稍后重试，不是配置问题 |
| 调用报 `1210 图片输入格式/解析错误` | 图片 URL 跨区/防盗链 | 换图片源或改用本地文件路径 |
| `failed: ENOENT`（Windows） | command 路径不对 | 用 python 的绝对 `.exe` 路径 |

## 完成清单（向用户汇报时对照）

- [ ] 依赖装好，`import mcp, httpx` 通过
- [ ] MCP 配置已写入正确位置，server 实测返回两个工具
- [ ] （ZCode）skill 已复制到 `~/.zcode/skills/vision`
- [ ] 用户已重启客户端，`glm-vision` connected
- [ ] 用户自己的 API Key 已填入，仓库源码未改动
