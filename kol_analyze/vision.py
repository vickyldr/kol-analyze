"""读取大盘截图 -> MarketContext。

针对你的 4 类后台截图做了适配：
  1) 广告大盘分国家消耗（国家 + 绝对值 + 占比，Total 在底部）
  2) 设计师 vs KOL 占比（其中 KOL 一行是 KOL 占整体的比例）
  3) KOL 素材分国家消耗（国家 + 占比）
  4) 发布分语言（饼图，语言代码 + 条数 + 占比）
无 API key 时跳过。
"""

from __future__ import annotations

import json
from pathlib import Path

from . import engine
from .config import Settings
from .market import MarketContext, from_dict

_MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
          ".webp": "image/webp", ".gif": "image/gif"}

_SYSTEM = """你从广告后台截图里读数字，输出 JSON，不要解释、不要代码围栏。
我会给你 1~4 张截图，可能包含：
- 广告大盘分【国家】消耗（每行：国家 绝对值 百分比，底部有 Total）
- 设计师 vs KOL 占比（其中有一行是「KOL」，代表 KOL 占整体的百分比，其余是设计师名字）
- KOL 素材分【国家】消耗（每行：国家 绝对值 百分比）
- 发布分【语言】（饼图，标签是语言代码 US/TR/SP/BR/IT/KR/JP/AR/FR/TW，含条数与百分比）

请合并成一个 JSON（读不到的字段给 null 或空对象，不要编造）：
{
  "grand_total_spend": 数字或null,          // 大盘 Total（设计+KOL）
  "kol_total_spend": 数字或null,            // KOL 分国家表的 Total
  "ad_country_share": {"美国": 33.99, ...}, // 大盘分国家占比%
  "ad_country_spend": {"美国": 3190, ...},  // 大盘分国家绝对值
  "kol_share_of_total": 29.37,              // KOL 占整体%
  "kol_country_share": {"土耳其": 37.07, ...}, // KOL 分国家占比%
  "kol_publish_share": {"TR": 33.33, ...},  // 发布分语言占比%（键用语言代码）
  "kol_publish_count": {"TR": 106, ...}     // 发布分语言条数
}"""


def read_screenshots(image_paths, settings: Settings) -> MarketContext:
    paths = [str(Path(p)) for p in image_paths if Path(p).exists()]
    if not paths:
        return MarketContext()
    if engine.available() == "offline":
        return MarketContext(notes=[
            f"（已忽略 {len(paths)} 张截图：没有可用的 Claude 引擎读图。"
            "可在页面里手填大盘数据，或改用 --market market.json。）"])

    text = engine.read_images(_SYSTEM, "把这些截图读成约定的 JSON，只输出 JSON。",
                              paths, settings.vision_model)
    if not text:
        return MarketContext(notes=["（截图解析失败，已跳过大盘回填。）"])
    try:
        s, e = text.find("{"), text.rfind("}")
        return from_dict(json.loads(text[s:e + 1]))
    except (json.JSONDecodeError, ValueError):
        return MarketContext(notes=["（截图解析结果非 JSON，已跳过大盘回填。）"])
