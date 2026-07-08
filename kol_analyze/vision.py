"""从大盘截图里抽取全局数字（总消耗、各国占比、发布/投入产出）。

用户的「发布情况 / 投入产出占比」通常是后台截图，不在数据文件里。
这里用 Claude 视觉能力把截图读成结构化数字，回填到 OverallMetrics。
无 API key 时直接跳过（返回空）。
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from .config import Settings
from .metrics import OverallMetrics

_MEDIA = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp",
}

_VISION_SYSTEM = """你从广告后台截图里读取数字。只输出 JSON，不要解释。
结构：
{
  "grand_total_spend": 数字或 null,   // 大盘（设计+KOL）总消耗
  "country_spend_share": {"美国": 33.99, "土耳其": 10.77},  // 国家->消耗占比(%)
  "notes": ["截图里能看到、但上面字段没覆盖的关键信息，如发布占比/投入产出口径"]
}
读不到就给 null 或空对象，不要编造。"""


def _img_block(path: Path) -> dict:
    media = _MEDIA.get(path.suffix.lower(), "image/png")
    data = base64.standard_b64encode(path.read_bytes()).decode()
    return {"type": "image",
            "source": {"type": "base64", "media_type": media, "data": data}}


def enrich_from_screenshots(overall: OverallMetrics,
                            image_paths: list[str | Path],
                            settings: Settings) -> OverallMetrics:
    paths = [Path(p) for p in image_paths if Path(p).exists()]
    if not paths:
        return overall
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        overall.notes.append(
            f"（已忽略 {len(paths)} 张截图：未设置 ANTHROPIC_API_KEY，无法读图）")
        return overall

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    content: list = [_img_block(p) for p in paths]
    content.append({"type": "text",
                    "text": "把这些截图里的大盘数字读成上面约定的 JSON。"})
    msg = client.messages.create(
        model=settings.vision_model,
        max_tokens=2000,
        system=_VISION_SYSTEM,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in msg.content
                   if getattr(b, "type", "") == "text").strip()
    try:
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start:end + 1])
    except (json.JSONDecodeError, ValueError):
        overall.notes.append("（截图解析失败，已跳过大盘数字回填）")
        return overall

    if data.get("grand_total_spend"):
        overall.grand_total_spend = data["grand_total_spend"]
    if data.get("country_spend_share"):
        overall.country_spend_share = data["country_spend_share"]
    for n in data.get("notes", []) or []:
        overall.notes.append(n)
    return overall
