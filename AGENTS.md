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

- **Python 3.10+**。用 `python --version` 确认；Windows 下 `python` 不存在就试 `py -3`。
- **智谱 API Key**：用户需要先在 https://open.bigmodel.cn/usercenter/apikeys 注册并创建 Key。**用用户的 Key，绝不要用仓库里任何占位符或示例 Key。**

---

## Step 1：安装依赖

在仓库根目录执行：

```bash
python -m pip install -r requirements.txt
```

> 用 `python -m pip` 而不是裸 `pip`，确保装进同一个解释器。Windows 下若 `python` 不行，用 `py -3 -m pip install -r requirements.txt`。

验证：`python -c "import mcp, httpx; print('ok')"` 无报错。记下可用的 python 命令，后续步骤要用。

## Step 2：注册 MCP Server（推荐用一键脚本）

### 推荐方式：运行 install.py（跨平台，自动完成配置 + skill + 验证）

```bash
python install.py
```

脚本会自动：
- 检测/安装依赖
- 收集 API Key（环境变量没有就交互提示用户输入——此时让用户去申请，**不要替用户编造 Key**）
- 合并配置到 ZCode 的 `~/.zcode/cli/config.json`（写前备份、写前打印）
- 拷贝 skill 到 `~/.zcode/skills/vision`
- 实测 server 返回工具列表

脚本会打印一份**标准 `mcpServers` 配置**，如果用户不是 ZCode（是 Claude Desktop / Cursor / VS Code 等），把这份配置按该客户端的方式填入即可。

先跑 `python install.py --dry-run` 预览动作（不写文件），确认无误再正式跑。

### 手动方式（脚本失败或需要手工干预时）

**情况 A：标准 `mcpServers` 顶层键**（Claude Desktop、Cursor、VS Code 等）

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
      }
    }
  }
}
```

**情况 B：ZCode（嵌套 `mcp.servers`）**

配置文件在 `~/.zcode/cli/config.json`。**如果文件不存在，创建它**并写 `{"mcp": {"servers": {}}}` 骨架；如果存在，读取并合并（保留原有内容，只加 `glm-vision`）。ZCode 专用字段：

```json
{
  "mcp": {
    "servers": {
      "glm-vision": {
        "type": "stdio",
        "command": "<python 绝对路径>",
        "args": ["<仓库绝对路径>/server.py"],
        "env": { "ZHIPUAI_API_KEY": "<用户自己的 Key>" },
        "enabled": true,
        "timeoutMs": 120000
      }
    }
  }
}
```

> **Windows JSON 路径注意**：JSON 里反斜杠必须转义。`C:\Program Files\...` 要写成 `C:\\Program Files\\...`，否则 JSON 非法、配置加载失败。

### Key 流程（重要）

- **用户还没给 Key**：先让用户去 https://open.bigmodel.cn/usercenter/apikeys 申请并给你，拿到后再写配置。**不要用占位符写进配置**——server 无 Key 会直接退出，客户端 MCP 面板会显示 failed，用户会误以为装坏了。
- **Key 只走 MCP 配置的 env 字段**。不要创建 `.env` 文件——server.py 不读 `.env`（源码只读环境变量），填了也没用。

### 验证（两种情况通用）

用这个命令直接测试 server 能启动并返回工具列表（注意：这是 bash 语法；Windows CMD/PowerShell 用户请改用 `python install.py` 里的自动验证，或让 Agent 直接用 install.py）：

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | ZHIPUAI_API_KEY=<用户的Key> <python> <仓库绝对路径>/server.py
```

期望输出里能看到 `analyze_image` 和 `batch_analyze_images`（输出中混有 INFO 日志是正常的，用文本搜索而不是整体 JSON 解析）。

## Step 3：（仅 ZCode）安装 Vision Skill

如果用了 install.py，这一步已自动完成。手动安装：

```bash
mkdir -p ~/.zcode/skills
cp -r skill ~/.zcode/skills/vision
```

> Windows CMD/PowerShell 下 `cp` 不可用，用 `Copy-Item -Recurse skill ~\.zcode\skills\vision`（PowerShell）或让 Agent 用 Python 的 shutil。若 `~/.zcode/skills/vision` 已存在，先备份或确认覆盖。非 ZCode 客户端跳过此步。

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
| server 启动报 `ZHIPUAI_API_KEY 未设置` | env 没配或 Key 为空 | 确认配置里 `env.ZHIPUAI_API_KEY` 填了用户 Key（不用 .env） |
| 配置加载失败 / JSON 报错 | Windows 路径反斜杠没转义 | `C:\` 写成 `C:\\`；校验 JSON 语法 |
| MCP 工具不出现 | 配置没加载或格式错 | 检查 JSON；ZCode 用嵌套 `mcp.servers`；配置文件不存在时先创建骨架 |
| 调用报 `429 该模型当前访问量过大` | 免费模型限流 | 稍后重试，不是配置问题 |
| 调用报 `1210 图片输入格式/解析错误` | 图片 URL 跨区/防盗链 | 换图片源或改用本地文件路径 |
| `failed: ENOENT`（Windows） | command 路径不对 | 用 python 的绝对 `.exe` 路径 |

## 完成清单（向用户汇报时对照）

**Agent 可自验项：**
- [ ] 依赖装好，`import mcp, httpx` 通过
- [ ] 配置已写入正确位置，server 实测返回两个工具（或 install.py 验证通过）
- [ ] （ZCode）skill 已安装到 `~/.zcode/skills/vision`

**需用户操作项（Agent 负责提醒，不能替用户完成）：**
- [ ] 用户已提供自己的 API Key，已填入配置 env 字段
- [ ] 用户已重启客户端，`glm-vision` connected
- [ ] 用户已测试识别一张图成功
