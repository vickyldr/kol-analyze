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
- 【素材/脚本维度(script_section)】要做【跨语言】的具体建议，这是重点：
  · 迁移：某脚本/形式在 A 语言跑出，B 语言没做 -> 建议 B 也试（含脚本、MV模板、街采/口播形式）。
  · 每个脚本 继续做 / 优化 / 砍（跑不出的别做了）。
  · 某语言跑出率普遍低 -> 建议挖新脚本；脚本单一但有潜力 -> 建议探索新脚本。
  · 要和前面的国家/语言维度结论呼应，不要各说各话。
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
    "script_section": {
        "overview": "四、素材/脚本维度的总体判断（1-2 段）：哪些脚本/形式是跨语言主力、哪些该迁移",
        "migrations": ["跨语言迁移建议，每条一句：脚本X在A跑出，建议B也试（可含形式，如口播/街采/MV）"],
        "format_suggestions": ["形式覆盖建议，每条一句：某语言只做街采、没试口播，可测试"],
        "lang_strategies": [
            {"name": "语言名",
             "suggestion": "该语言脚本策略：继续做哪些强脚本、砍哪些弱脚本、要不要挖/探索新脚本"}
        ],
    },
    "staffing_section": {
        "overview": "五、人力分工与调整建议的总述：当前分工是否匹配各语言现状；有没有『机会语言(覆盖缺口/高潜)』没人负责该分给谁；谁的盘子该增/该减",
        "people": [
            {"person": "负责人姓名",
             "suggestion": "针对这个人的具体调整建议：他负责的语言里哪些该加码(加量/高潜)、哪些该降频(削减)、哪些是新机会要补；结合脚本策略给动作"}
        ],
    },
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


def build_script_facts(sa) -> dict:
    migr = [{
        "脚本": r.theme, "跑出语言": r.best_lang,
        "建议扩展到": r.migrate_to,
        "各语言": {c.name: {"条数": c.count, "消耗": round(c.spend, 1),
                          "ROI7%": round((c.best_roi7 or 0) * 100, 1),
                          "有转化条数": c.converted}
                 for c in r.cells.values()},
    } for r in sa.migrations[:12]]
    fmts = [{"形式": f.fmt, "在用语言": f.present, "建议试的语言": f.suggest_to}
            for f in sa.formats]
    strat = [{"语言": s.name, "脚本数": s.diversity,
              "跑出率%": round(s.breakout, 2) if s.breakout is not None else None,
              "主力脚本": s.top_scripts, "档位": s.verdict, "建议": s.suggestion}
             for s in sa.lang_strategies]
    top_scripts = [{"脚本": r.theme, "总消耗": round(r.total_spend, 1),
                    "跑出语言": r.best_lang or "—",
                    "覆盖语言数": len(r.cells)} for r in sa.scripts[:15]]
    return {"跨语言迁移建议": migr, "形式覆盖": fmts,
            "各语言脚本策略": strat, "脚本总榜": top_scripts}


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
                 "ROI0%": round((c.roi0 or 0) * 100, 1),
                 "ROI7%": round((c.roi7 or 0) * 100, 1),
                 "平台": c.platform, "消耗": round(c.spend, 1)}
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


def sop_block(sop: str) -> str:
    """本产品的复盘 SOP / 分析规则；提供了就作为最高优先级的判断标准。"""
    sop = (sop or "").strip()
    if not sop:
        return ""
    return ("【本产品复盘 SOP · 分析规则（最高优先级，务必严格照做）】\n"
            "下面是本产品团队的素材复盘 SOP：素材分类标准（消耗/ROI 阈值、iOS/Android 口径）"
            "与对应动作（放大/复刻/优化/观察/停止等）。请严格用它来判断每条素材属于哪一档、"
            "给出对应动作，分类名与动作名都沿用 SOP 里的说法，不要用你自己的一套。\n"
            "----- SOP 开始 -----\n" + sop + "\n----- SOP 结束 -----\n")


def style_block(mem) -> str:
    """把历史「写作偏好」渲染成注入文本；没有就返回空。"""
    notes = getattr(mem, "style_notes", None) or []
    if not notes:
        return ""
    lines = []
    for n in notes:
        loc = f"[{n.scope}] " if n.scope and n.scope != "general" else ""
        why = f"（原因：{n.reason}）" if n.reason else ""
        lines.append(f"- {loc}{n.instruction}{why}")
    return ("【写作偏好 · 来自我过往的修订，必须遵守】\n"
            "以下是我之前对复盘话术的反馈，这次生成请一并照做：\n"
            + "\n".join(lines) + "\n")


USER_TEMPLATE = """下面是本期聚合好的客观数据（JSON）。据此产出复盘 JSON。

标题用：{title}
周期用：{period}

{sop}
{style}
严格按此结构输出（键名一致）：
{schema}

【国家/语言维度】客观数据：
{facts}

【素材/脚本维度】客观数据（用于 script_section）：
{script_facts}

【人力分工】当前分工 + 各人负责语言的现状（用于 staffing_section；
若 has_staffing 为 false 就把 staffing_section 的 people 给空数组、overview 说明未提供分工）：
{staffing_facts}
"""


REVISE_SYSTEM = """你在帮我修订一份 KOL 广告复盘里的【某一段】文字。
我会给你：这段的位置、原文、我的修改要求（为什么不好 / 想改成什么样）。
请只重写这一段，保持投手复盘口吻、结论先行；只输出改后的文字本身，
不要解释、不要引号、不要 markdown。"""


REVISE_USER = """位置：{scope}
原文：
{text}

我的修改要求：{instruction}
{reason_line}
请给出改后的这一段文字。"""


POLISH_SYSTEM = """你在润色一份 KOL 广告复盘的文字。我给你各段文字（JSON：key -> 文字）。
逐段润色，让表达更顺、更专业、口语但不啰嗦，保持投手复盘口吻、结论先行。
铁律：绝不改动任何数字、百分比、素材名、红人名、玩法、国家/语言，以及判断方向和含义，
只改文字表达。返回同样结构的 JSON（同样的 key，值是润色后的文字），key 不增不减，
不要解释、不要 markdown、不要代码围栏。"""
