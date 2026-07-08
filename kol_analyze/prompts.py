"""Claude 分析用 prompt 与 facts 构造。"""

from __future__ import annotations

SYSTEM = """你是一名资深效果广告 / KOL 投放分析师，为月度 KOL 复盘写分析。
我会给你已经聚合好的客观数字（按【语言】看 KOL，英语/西语等分开，不用「美国」国家口径）。

写作要求（严格遵守）：
- 中文，投手内部复盘口吻，结论先行、敢下判断，不写 PPT 套话。
- 缺口分析的总结要【一句话】说清：哪些语言该加量、哪些该削减、哪些是大盘有量但没覆盖的机会。
  不要每个语言写长段落，点到为止。
- 每个语言的 todo 要具体到动作与素材/红人/玩法，例如
  「继续放大 凝视哥·口播功能录屏介绍」「减少 ROI7 偏低的拉踩Gb 弱版」。
- 只能基于我给的数字、红人、玩法、素材名判断，不要编造。

只输出 JSON，不要任何解释文字，不要 markdown 代码围栏。"""

OUTPUT_SCHEMA_HINT = {
    "title": "报告标题",
    "period": "周期，如 5月",
    "ad_section": {
        "overview": "一、广告部份：大盘（设计+KOL）分国家消耗集中在哪、设计师 vs KOL 占比、KOL 分国家消耗（1-2 段）",
        "caveat": "口径提醒：KOL 按语言看，英语/西语分开",
    },
    "gap_summary": "二、产出 vs 消耗 缺口分析的【一句话总结】：加量=…；削减=…；覆盖缺口(大盘有量没产出)=…",
    "langs": [
        {
            "name": "语言名，如 土耳其语",
            "one_liner": "一句话定位，如 最稳定的 KOL 主力语言池",
            "conversion": "转化情况：把消耗占比/产出占比/跑出率读成判断",
            "creative_analysis": "素材分析：点名强/潜力/弱素材（红人·玩法），给方向",
            "todo": "todo：留/放大/降频/优化 的可执行动作（可多条，用换行）",
        }
    ],
}


def build_facts(analysis) -> dict:
    langs = []
    for l in analysis.langs:
        langs.append({
            "语言": l.name, "代码": l.lang,
            "产出条数": l.count, "消耗": round(l.spend, 2),
            "消耗占比%": round(l.spend_share, 2),
            "跑出率%": round(l.breakout_rate, 2) if l.breakout_rate is not None else None,
            "平均ROI7%": round(l.avg_roi7, 2) if l.avg_roi7 is not None else None,
            "top红人": [f"{n}×{c}" for n, c in l.top_influencers[:5]],
            "top玩法": [f"{p}×{c}" for p, c in l.top_plays[:5]],
            "强素材": [
                {"素材": c.ad_name, "红人": c.influencer, "玩法": c.play,
                 "ROI7%": round((c.roi7 or 0) * 100, 1), "消耗": round(c.spend, 1)}
                for c in l.strong[:8]],
            "潜力素材": [f"{c.influencer}·{c.play}" for c in l.potential[:6]],
            "弱素材": [f"{c.influencer}·{c.play}" for c in l.weak[:5]],
        })
    gaps = [{
        "语言": g.name, "大盘消耗占比%": g.ad_market_share,
        "KOL消耗占比%": round(g.kol_spend_share, 2) if g.kol_spend_share is not None else None,
        "产出占比%": round(g.publish_share, 2) if g.publish_share is not None else None,
        "跑出率%": round(g.breakout_rate, 2) if g.breakout_rate is not None else None,
        "档位": g.verdict, "结论": g.one_line,
    } for g in analysis.gaps]

    m = analysis.market
    return {
        "KOL总消耗": round(analysis.kol_total_spend, 2),
        "大盘总消耗": m.grand_total_spend,
        "KOL占整体%": m.kol_share_of_total,
        "大盘分国家占比": m.ad_country_share or None,
        "覆盖缺口(大盘有量但KOL没产出)": analysis.coverage_gaps or None,
        "各语言指标": langs,
        "缺口分析表": gaps,
    }


USER_TEMPLATE = """下面是本期聚合好的客观数据（JSON）。据此产出复盘 JSON。

标题用：{title}
周期用：{period}

严格按此结构输出（键名一致）：
{schema}

客观数据：
{facts}
"""
