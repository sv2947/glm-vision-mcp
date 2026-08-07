"""glm-vision MCP Server — 封装智谱 glm-4.6v-flash 视觉模型。

stdio 启动，暴露 analyze_image / batch_analyze_images 两个工具。
API Key 从环境变量 ZHIPUAI_API_KEY 读取。
"""

import asyncio
import base64
import mimetypes
import os
import sys
from pathlib import Path

import httpx

# mcp >= 1.10 左右将 fast_mcp 改名为 fastmcp，兼容新旧两种路径
try:
    from mcp.server.fast_mcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
MODEL = "glm-4.6v-flash"
ALLOWED_TYPES = {"image", "video", "file"}
# media_type -> content 元素 type 映射
TYPE_MAP = {"image": "image_url", "video": "video_url", "file": "file_url"}
# media_type -> mime 兜底
MIME_FALLBACK = {
    "image": "image/jpeg",
    "video": "video/mp4",
    "file": "application/octet-stream",
}

mcp = FastMCP("glm-vision")


def _resolve_media_url(media_url: str, media_type: str) -> str:
    """归一化 media_url 为可用作 url 的值。

    三种形态：
    - http:// / https:// 开头 -> 原样返回
    - 本地文件路径 -> 读字节转 data URI
    - 其他（含不存在的本地路径）-> 当作裸 base64，直接作为 data URI 的 base64 部分
    """
    if media_url.startswith(("http://", "https://")):
        return media_url
    mime = MIME_FALLBACK.get(media_type, "application/octet-stream")
    path = Path(media_url)
    if path.is_file():
        guessed, _ = mimetypes.guess_type(path.name)
        if guessed:
            mime = guessed
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    # 本地路径不存在 -> 当作裸 base64 字符串
    return f"data:{mime};base64,{media_url}"


async def _call_glm_vision(
    media_url: str,
    media_type: str,        # "image" | "video" | "file"
    prompt: str,
    thinking: bool = False,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> str:
    """底层共享函数：调智谱多模态接口，返回模型回答文本。"""
    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        raise RuntimeError("环境变量 ZHIPUAI_API_KEY 未设置")

    resolved = _resolve_media_url(media_url, media_type)
    media_key = TYPE_MAP[media_type]  # image->image_url / video->video_url / file->file_url
    content = [
        {"type": media_key, media_key: {"url": resolved}},
        {"type": "text", "text": prompt},
    ]
    body: dict = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
        "stream": False,
    }
    if thinking:
        body["thinking"] = {"type": "enabled"}
    if max_tokens is not None:
        body["max_tokens"] = max_tokens

    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(API_URL, json=body, headers=headers)
        if resp.status_code >= 300:
            raise RuntimeError(f"GLM API 调用失败 {resp.status_code}: {resp.text}")
        data = resp.json()
    return data["choices"][0]["message"]["content"]


def _validate_media_type(media_type: str) -> None:
    if media_type not in ALLOWED_TYPES:
        raise ValueError(
            f"media_type 必须是 {sorted(ALLOWED_TYPES)} 之一，收到: {media_type!r}"
        )


@mcp.tool()
async def analyze_image(
    prompt: str,
    media_url: str,
    media_type: str = "image",       # "image"|"video"|"file"
    thinking: bool = False,
    temperature: float = 0.7,
    max_tokens: int | None = None,
) -> str:
    """分析图片/视频/文件内容。media_url 可为公网 URL、本地文件路径或 base64 字符串。"""
    _validate_media_type(media_type)
    return await _call_glm_vision(
        media_url=media_url,
        media_type=media_type,
        prompt=prompt,
        thinking=thinking,
        temperature=temperature,
        max_tokens=max_tokens,
    )


@mcp.tool()
async def batch_analyze_images(
    media_urls: list[str],
    prompt: str,
    media_type: str = "image",
    thinking: bool = False,
) -> list[dict]:
    """并发批量分析多张图片/视频/文件。每项独立，失败不影响其他。返回每项结果。"""
    _validate_media_type(media_type)
    sem = asyncio.Semaphore(5)

    async def _one(i: int, u: str) -> dict:
        async with sem:
            try:
                result = await _call_glm_vision(
                    media_url=u,
                    media_type=media_type,
                    prompt=prompt,
                    thinking=thinking,
                )
                return {"index": i, "url": u, "ok": True, "result": result}
            except Exception as e:  # noqa: BLE001 - 单项失败不影响整体
                return {"index": i, "url": u, "ok": False, "error": str(e)}

    return await asyncio.gather(*(_one(i, u) for i, u in enumerate(media_urls)))


if __name__ == "__main__":
    if not os.environ.get("ZHIPUAI_API_KEY"):
        print(
            "错误：环境变量 ZHIPUAI_API_KEY 未设置，无法启动 glm-vision MCP Server",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run()
