# 换机迁移指南

把本项目的 MCP Server 和 Vision Skill 完整迁到新机器，需要迁移 3 件套并改 3 处路径。

## 需要迁移的 3 件套

| # | 是什么 | 目标位置 | 作用 |
|---|---|---|---|
| 1 | 仓库代码（含 server.py） | 任意目录，如 `C:\Users\<用户>\ZCodeProject\glm-vision-mcp\` | 底层引擎，真正调智谱 API 的程序 |
| 2 | MCP 配置 | `~/.zcode/cli/config.json` 的 `mcp.servers.glm-vision` | 告诉 ZCode 怎么启动 server |
| 3 | Skill | `~/.zcode/skills/vision/SKILL.md` | `/vision` 触发入口 |

少了任何一个都无法工作：
- 没代码 → server.py 找不到，MCP 启动失败
- 没配置 → ZCode 不知道有这个 MCP，`mcp__glm-vision__*` 工具不注册
- 没 Skill → 没有 `/vision` 入口，模型不会按规范调用

> API Key 不绑机器，智谱的 Key 直接复用，无需重新申请。

## 迁移步骤

### 1. 克隆仓库

```bash
git clone <仓库地址> glm-vision-mcp
cd glm-vision-mcp
```

### 2. 装依赖

新机器需要 **Python 3.10+**：

```bash
# 确认版本
python --version

# 装依赖
pip install -r requirements.txt
```

### 3. 改 3 处路径

新机器的用户名/安装位置可能不同，下面 3 处硬编码路径必须按实际改：

**① MCP 配置里的 python 路径**（`~/.zcode/cli/config.json` 的 `command`）
```json
"command": "C:\\Program Files\\Python312\\python.exe"
```
→ 改成新机器 python 的绝对路径。用 `where python`（Windows）/ `which python`（Unix）查。

**② MCP 配置里的 server.py 路径**（`~/.zcode/cli/config.json` 的 `args`）
```json
"args": ["C:\\Users\\Administrator\\ZCodeProject\\glm-vision-mcp\\server.py"]
```
→ 改成新机器实际克隆位置。

**③ MCP 配置里的 API Key**（`env.ZHIPUAI_API_KEY`）
```json
"env": { "ZHIPUAI_API_KEY": "your-key-here" }
```
→ 填入你的真实 Key。

完整配置片段（加进新机器 `~/.zcode/cli/config.json` 的 `mcp.servers` 下）：

```json
"glm-vision": {
  "type": "stdio",
  "command": "<新机器 python 绝对路径>",
  "args": ["<新机器 server.py 绝对路径>"],
  "env": { "ZHIPUAI_API_KEY": "<你的 Key>" },
  "enabled": true,
  "timeoutMs": 120000
}
```

### 4. 安装 Skill

```bash
cp -r skill ~/.zcode/skills/vision
```

### 5. 重启 ZCode，验证

- 打开 Settings → MCP，确认 `glm-vision` 显示 **connected**
- 对 AI 说 `/vision 帮我识别这张图 <某个本地图片路径>`，能返回模型描述即成功

## 常见迁移问题

| 症状 | 原因 | 解决 |
|---|---|---|
| Settings → MCP 显示 `failed: ENOENT` | python 路径不对 | 用绝对路径，Windows 指向 `.exe` |
| Settings → MCP 显示 `failed` 且 server.py 找不到 | args 里的 server.py 路径不对 | 用克隆位置的绝对路径 |
| `mcp__glm-vision__*` 工具不出现 | 配置没加载 / Key 缺失 | 检查 JSON 语法、`env.ZHIPUAI_API_KEY` 已填，重启 ZCode |
| 调用返回 `429 该模型当前访问量过大` | 免费模型限流 | 稍后重试，批量拉开间隔 |
| 调用返回 `1210 图片输入格式/解析错误` | 图片 URL 跨区/防盗链 | 换图片源或改用本地文件 |
