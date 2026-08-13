#!/usr/bin/env python3
"""glm-vision-mcp 一键安装脚本（跨平台，Windows/macOS/Linux 通用）。

自动完成：
  1. 检查 Python 依赖（mcp、httpx）
  2. 收集 ZHIPUAI_API_KEY（优先环境变量，否则交互输入）
  3. 合并 MCP 配置到 ZCode 的 ~/.zcode/cli/config.json（写前备份、写前打印）
  4. 拷贝 skill 到 ~/.zcode/skills/vision
  5. 实测 server 能启动并返回工具列表

用法：
  python install.py            # 正常安装
  python install.py --dry-run  # 只打印将执行的动作，不写任何文件

注意：
  - 本脚本只配置 ZCode 客户端（~/.zcode/cli/config.json）。
  - 非 ZCode 客户端（Claude Desktop / Cursor / VS Code 等）：脚本会打印
    一份标准 mcpServers 配置，请按各客户端的方式手动填入。
  - API Key 只写入 MCP 配置的 env 字段，不写入任何源码或 .env 文件。
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

SERVER_NAME = "glm-vision"
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def log(msg: str) -> None:
    print(f"[install] {msg}")


def fail(msg: str) -> None:
    print(f"[install] 错误：{msg}")
    sys.exit(1)


# ---------- 1. 依赖检查 ----------

def check_deps() -> None:
    log("检查依赖（mcp、httpx）…")
    try:
        import mcp  # noqa: F401
        import httpx  # noqa: F401
    except ImportError as e:
        log(f"缺少依赖：{e.name}。正在安装 requirements.txt …")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements.txt")],
            capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"pip 安装失败：{r.stderr[-500:]}")
        log("依赖安装完成")
    else:
        log("依赖已就绪")


# ---------- 2. API Key ----------

def get_api_key() -> str:
    key = os.environ.get("ZHIPUAI_API_KEY", "").strip()
    if key:
        log("已从环境变量 ZHIPUAI_API_KEY 读取 Key")
        return key
    if DRY_RUN:
        log("（dry-run）未检测到 Key，跳过交互输入")
        return "<dry-run-占位>"
    log("未检测到 ZHIPUAI_API_KEY 环境变量。")
    print("  请到 https://open.bigmodel.cn/usercenter/apikeys 创建 API Key")
    key = input("  粘贴你的 API Key：").strip()
    if not key:
        fail("未输入 API Key，中止。")
    return key


# ---------- 3. ZCode 配置合并 ----------

def config_path() -> Path:
    home = Path.home()
    if platform.system() == "Windows":
        # Windows 下 ~/.zcode 可能落在非 C 盘，但标准是 HOME/.zcode
        return home / ".zcode" / "cli" / "config.json"
    return home / ".zcode" / "cli" / "config.json"


def build_zcode_entry(api_key: str) -> dict:
    py_exe = str(Path(sys.executable).resolve())
    server_py = str((REPO_ROOT / "server.py").resolve())
    return {
        "type": "stdio",
        "command": py_exe,
        "args": [server_py],
        "env": {"ZHIPUAI_API_KEY": api_key},
        "enabled": True,
        "timeoutMs": 120000,
    }


def merge_zcode_config(api_key: str) -> Path:
    cfg = config_path()
    if DRY_RUN:
        log(f"（dry-run）将写入配置：{cfg}")
        print(json.dumps({SERVER_NAME: build_zcode_entry(api_key)}, ensure_ascii=False, indent=2))
        return cfg

    data = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fail(f"配置文件 {cfg} 不是合法 JSON，请先修复或备份后删除。")
    data.setdefault("mcp", {}).setdefault("servers", {})
    data["mcp"]["servers"][SERVER_NAME] = build_zcode_entry(api_key)

    # 写前备份
    backup = cfg.with_name(f"config.json.bak-{time.strftime('%Y%m%d%H%M%S')}")
    if cfg.exists():
        shutil.copy2(cfg, backup)
        log(f"已备份原配置到 {backup}")
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"已写入 {SERVER_NAME} 配置到 {cfg}")
    return cfg


# ---------- 4. skill 安装 ----------

def install_skill() -> None:
    src = REPO_ROOT / "skill"
    dst = Path.home() / ".zcode" / "skills" / "vision"
    if not src.is_dir():
        log("仓库内无 skill/ 目录，跳过（非 ZCode 场景）")
        return
    if DRY_RUN:
        log(f"（dry-run）将拷贝 {src} → {dst}")
        return
    if dst.exists():
        backup = dst.parent / f"vision.bak-{time.strftime('%Y%m%d%H%M%S')}"
        shutil.move(str(dst), str(backup))
        log(f"已备份旧 skill 到 {backup}")
    shutil.copytree(src, dst)
    log(f"已安装 skill 到 {dst}")


# ---------- 4.5 通用配置打印（非 ZCode 客户端用） ----------

def print_generic_config(api_key: str) -> None:
    """打印标准 mcpServers 配置，供 Claude Desktop / Cursor / VS Code 等客户端使用。"""
    py_exe = str(Path(sys.executable).resolve())
    server_py = str((REPO_ROOT / "server.py").resolve())
    entry = {
        "type": "stdio",
        "command": py_exe,
        "args": [server_py],
        "env": {"ZHIPUAI_API_KEY": api_key},
    }
    generic = {"mcpServers": {SERVER_NAME: entry}}
    log("以下为标准 mcpServers 配置（用于 Claude Desktop / Cursor / VS Code 等）：")
    print(json.dumps(generic, ensure_ascii=False, indent=2))


# ---------- 5. server 实测验证 ----------

def verify_server(api_key: str) -> bool:
    log("实测 server 启动并返回工具列表…")
    server_py = str((REPO_ROOT / "server.py").resolve())
    env = dict(os.environ)
    env["ZHIPUAI_API_KEY"] = api_key
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                  "clientInfo": {"name": "install-check", "version": "1"}}})
    tools = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    payload = f"{init}\n{tools}\n"
    try:
        r = subprocess.run(
            [sys.executable, server_py], input=payload,
            capture_output=True, text=True, timeout=60, env=env)
    except subprocess.TimeoutExpired:
        fail("server 启动超时（60s）。请检查 python 路径和依赖。")
    out = r.stdout + r.stderr
    if "analyze_image" in out and "batch_analyze_images" in out:
        log("验证通过：server 返回了 analyze_image 和 batch_analyze_images")
        return True
    log("验证未通过，server 输出如下：")
    print(out[-800:])
    return False


# ---------- 主流程 ----------

def main() -> None:
    global REPO_ROOT, DRY_RUN
    ap = argparse.ArgumentParser(description="glm-vision-mcp 一键安装")
    ap.add_argument("--dry-run", action="store_true", help="只打印动作，不写任何文件")
    args = ap.parse_args()
    DRY_RUN = args.dry_run
    REPO_ROOT = Path(__file__).resolve().parent

    log(f"glm-vision-mcp 安装脚本（仓库：{REPO_ROOT}）")
    if DRY_RUN:
        log("dry-run 模式：只打印，不写入")

    check_deps()
    api_key = get_api_key()

    cfg = merge_zcode_config(api_key)
    print_generic_config(api_key)
    if not DRY_RUN:
        install_skill()
        ok = verify_server(api_key)
        if not ok:
            fail("验证未通过，见上方 server 输出。常见原因：API Key 无效或网络问题。")
        log("全部完成！请重启客户端，确认 glm-vision 显示 connected。")
        log(f"ZCode 配置位置：{cfg}")
        log("非 ZCode 客户端请使用上方打印的标准 mcpServers 配置，按客户端方式填入。")
    else:
        log("dry-run 结束（未写入任何文件）")


if __name__ == "__main__":
    main()
