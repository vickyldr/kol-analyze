"""统一的「让 Claude 生成」入口，兼容三种鉴权：

1) Claude Code 订阅（CLI）：直接调用 `claude -p`，用你已有的订阅登录，
   不需要官方 API key。← 你的情况
2) 官方 API key：设置了 ANTHROPIC_API_KEY 时走 anthropic SDK。
3) 都没有：返回 None，交给调用方走规则兜底。
"""

from __future__ import annotations

import os
import shutil
import subprocess


def available() -> str:
    """返回可用引擎：'cli' / 'api' / 'offline'。"""
    if os.environ.get("KOL_FORCE_OFFLINE"):
        return "offline"
    if shutil.which("claude"):
        return "cli"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api"
    return "offline"


def label() -> str:
    return {"cli": "Claude Code 订阅(CLI)", "api": "官方 API",
            "offline": "规则兜底(offline)"}[available()]


def generate_text(system: str, user: str, model: str,
                  max_tokens: int = 8000, timeout: int = 240) -> str | None:
    """返回模型输出文本；失败/不可用时返回 None。"""
    eng = available()
    if eng == "cli":
        return _via_cli(system, user, model, timeout)
    if eng == "api":
        return _via_api(system, user, model, max_tokens)
    return None


def _via_cli(system: str, user: str, model: str, timeout: int) -> str | None:
    prompt = f"{system}\n\n---\n\n{user}"
    try:
        proc = subprocess.run(
            ["claude", "-p", "--output-format", "text", "--model", model],
            input=prompt, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _via_api(system: str, user: str, model: str, max_tokens: int) -> str | None:
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content
                       if getattr(b, "type", "") == "text").strip() or None
    except Exception:
        return None


def read_images(system: str, instruction: str, image_paths: list[str],
                model: str, timeout: int = 240) -> str | None:
    """用 Claude 读图（大盘截图）。CLI 模式下让 Claude Code 读文件路径。"""
    eng = available()
    if eng == "cli":
        paths = " ".join(f'"{p}"' for p in image_paths)
        prompt = (f"{system}\n\n请读取这些图片文件并按要求输出：{paths}\n\n{instruction}")
        try:
            proc = subprocess.run(
                ["claude", "-p", "--output-format", "text", "--model", model,
                 "--allowedTools", "Read"],
                input=prompt, capture_output=True, text=True, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError):
            return None
        return proc.stdout.strip() or None if proc.returncode == 0 else None
    if eng == "api":
        return _images_via_api(system, instruction, image_paths, model)
    return None


def _images_via_api(system, instruction, image_paths, model) -> str | None:
    import base64
    from pathlib import Path
    try:
        import anthropic
    except ImportError:
        return None
    media = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".gif": "image/gif"}
    content = []
    for p in image_paths:
        pp = Path(p)
        if not pp.exists():
            continue
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": media.get(pp.suffix.lower(), "image/png"),
            "data": base64.standard_b64encode(pp.read_bytes()).decode()}})
    content.append({"type": "text", "text": instruction})
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(model=model, max_tokens=3000, system=system,
                                     messages=[{"role": "user", "content": content}])
        return "".join(b.text for b in msg.content
                       if getattr(b, "type", "") == "text").strip() or None
    except Exception:
        return None
