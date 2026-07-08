"""Claude 分析用的 prompt 与输出 schema。"""

from __future__ import annotations

SYSTEM = """你是一名资深的效果广告 / KOL 投放分析师。
你的任务是：根据我给你的「已经聚合好的客观数字」，写出一份月度 KOL 广告复盘。

写作风格要求（非常重要，请严格模仿）：
- 中文，口语但专业，像投手内部复盘，不要写成 PPT 套话。
- 结论先行、敢下判断。多用这类措辞：「最值得继续放大」「可以做但要收着做」
  「明显投入过量」「低效盘 / 应降频盘」「表面好看、底层偏弱」「高潜新线」。
- 每个国家都要落到「留 / 放大 / 降频 / 优化什么」的具体动作，不要泛泛而谈。
- 只能基于我给的数字与素材名做判断，不要编造不存在的素材或数据。
- todo 用短句、可执行，例如「继续放大 口播功能录屏介绍」「减少 ROI7 低于 20% 的弱版」。

只输出 JSON，不要任何解释性文字、不要 markdown 代码块围栏。"""

# 期望的 JSON 结构（也用于校验/兜底）
OUTPUT_SCHEMA_HINT = {
    "title": "报告标题，如：26 RM月度KOL广告分析",
    "period": "周期，如：5月",
    "overall": {
        "big_picture": "整体广告盘：总消耗、头部国家占比、集中度结论（1-2段）",
        "kol_position": "KOL 在整体盘里的位置：是主力还是补充，后续优化要看什么（1段）",
        "caveats": ["需要提醒的口径问题，如 广告消耗国家≠素材生产语言 …"],
    },
    "strategy_overview": "跨国家的整体分层结论：哪些盘最值得放大 / 收着做 / 需要控制投入（分档列出国家并说明理由）",
    "countries": [
        {
            "name": "国家名",
            "one_liner": "一句话定位，如：最稳定的 KOL 主力投放池",
            "conversion": "转化情况：把消耗占比/发布占比/跑出率读成一段判断",
            "creative_analysis": "素材分析：点名有转化/潜力/弱素材，并给方向",
            "todo": "todo：留/放大/降频/优化的可执行动作（可多条，用换行）",
        }
    ],
}


def build_facts(overall) -> dict:
    """把 metrics 转成喂给模型的紧凑 facts。"""
    countries = []
    for c in overall.countries:
        countries.append({
            "name": c.name,
            "sheet_name": c.sheet_name,
            "total_spend": round(c.total_spend, 2),
            "spend_share_pct": round(c.spend_share, 2),
            "published_share_pct": round(c.published_share, 2),
            "breakout_rate_pct": (round(c.breakout_rate, 2)
                                  if c.breakout_rate is not None else None),
            "avg_roi7_pct": (round(c.avg_roi7, 2)
                             if c.avg_roi7 is not None else None),
            "strong_creatives": [
                {"name": s.creative, "roi7": s.roi7,
                 "spend_share_in_country": round(s.spend_share_in_country, 3)}
                for s in c.strong[:8]
            ],
            "potential_creatives": [s.creative for s in c.potential[:8]],
            "weak_creatives": [s.creative for s in c.weak[:8]],
        })
    return {
        "total_kol_spend": round(overall.total_spend, 2),
        "grand_total_spend": overall.grand_total_spend,
        "country_spend_share_from_screenshot": overall.country_spend_share or None,
        "extra_notes": overall.notes or None,
        "countries": countries,
    }


USER_TEMPLATE = """下面是本期已聚合好的客观数据（JSON）。请据此产出复盘 JSON。

报告标题请用：{title}
报告周期请用：{period}

严格按这个结构输出（键名保持一致）：
{schema}

客观数据：
{facts}
"""
