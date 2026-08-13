# PROMPT.md — 给朋友 / 让 Agent 帮你安装的提示词

把这个文件里的提示词发给你的 AI Agent（ZCode / Claude Code / Cursor 等任意支持 Agent 的客户端），
它会自动完成 glm-vision-mcp 的全部安装和配置。你只需要在它要求时提供你自己的智谱 API Key。

---

## 复制下面这段发给你的 Agent

```
请帮我安装一个叫 "glm-vision-mcp" 的 AI 图片识别项目。

## 项目信息
- GitHub 仓库地址：https://github.com/sv2947/glm-vision-mcp （公开仓库，可直接访问）
- 这个项目是一个 MCP Server + Vision Skill，封装智谱 GLM-4.6V-Flash 视觉模型，
  安装后你的 AI 客户端就能识别图片（网页图片 URL、本地图片、批量图片）

## 请按以下步骤执行

1. 把仓库克隆到本地，例如：git clone https://github.com/sv2947/glm-vision-mcp.git
2. 阅读仓库根目录的 AGENTS.md 文件，里面有完整的自动安装指引
3. 严格按 AGENTS.md 里的步骤执行：
   - 先安装依赖（AGENTS.md Step 1）
   - 优先运行一键脚本 `python install.py`（AGENTS.md Step 2 推荐方式），
     它会自动完成配置注册、skill 安装、server 验证；先跑 `--dry-run` 预览再正式跑
   - 如果脚本不可用或失败，再按 AGENTS.md 里的手动方式配置
     （注意：如果我是 ZCode，用嵌套 mcp.servers 格式；
      如果是 Claude Desktop / Cursor / VS Code 等其他客户端，用标准 mcpServers 格式）
   - 最后让我重启客户端（AGENTS.md Step 4）
4. 每完成一步，告诉我这一步的结果；全部完成后，对照 AGENTS.md 末尾的完成清单逐项汇报
5. 需要我提供智谱 API Key 时，提醒我去 https://open.bigmodel.cn/usercenter/apikeys 申请
   （用我自己的 Key，不要用仓库里的示例值）
6. 如果安装过程中遇到 AGENTS.md 常见问题表里的错误，按表里的方法解决
```

## 预期结果

安装成功后，你的客户端里会出现两个工具：
- `analyze_image`（单张图片识别）
- `batch_analyze_images`（批量图片识别）

你可以对它说「识别这张图 <路径或URL>」来测试。
