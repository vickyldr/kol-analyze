"""调用 Claude 生成复盘叙述；无 API key 时用规则兜底。"""

from __future__ import annotations

import json
import os

from . import prompts
from .config import Settings, Thresholds
from .metrics import CountryMetrics, OverallMetrics


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    # 截取第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def analyze(overall: OverallMetrics, settings: Settings,
            title: str, period: str) -> dict:
    facts = prompts.build_facts(overall)
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        if not settings.allow_offline_fallback:
            raise RuntimeError(
                "未检测到 ANTHROPIC_API_KEY。请设置环境变量，或用 --offline 走规则兜底。")
        return _offline(overall, settings.thresholds, title, period)

    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("请先安装 anthropic： pip install anthropic") from e

    client = anthropic.Anthropic(api_key=api_key)
    user = prompts.USER_TEMPLATE.format(
        title=title, period=period,
        schema=json.dumps(prompts.OUTPUT_SCHEMA_HINT, ensure_ascii=False, indent=2),
        facts=json.dumps(facts, ensure_ascii=False, indent=2),
    )
    msg = client.messages.create(
        model=settings.model,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
        system=prompts.SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    try:
        data = _extract_json(text)
    except (json.JSONDecodeError, ValueError):
        # 模型没给合法 JSON，退回兜底，避免整个流程失败
        data = _offline(overall, settings.thresholds, title, period)
    return data


# --------------------------------------------------------------------------
# 规则兜底：无 API key 也能端到端跑出一份（话术较模板化）
# --------------------------------------------------------------------------

def _fmt_pct(v: float | None) -> str:
    return f"{v:.2f}%" if v is not None else "—"


def _country_verdict(c: CountryMetrics, th: Thresholds) -> tuple[str, str, str]:
    """返回 (一句话定位, 分层标签, 建议动作)。"""
    br = c.breakout_rate
    over_invest = (c.published_share - c.spend_share) >= th.over_invest_gap

    if br is not None and br >= th.breakout_high:
        return ("最稳定的 KOL 主力投放池", "最值得放大",
                "稳住量，提高单条素材质量，围绕主力脚本继续复刻。")
    if over_invest:
        return ("有量但效率一般，已现过量投入迹象", "明显投入过量",
                "降频提质，精选供给，减少泛量与低质复制版本。")
    if br is not None and br <= th.breakout_low:
        return ("表面好看、底层偏弱", "需要控制投入",
                "缩窄方向，只打老脚本、提高命中率，不适合扩量。")
    return ("有量，承接中等", "可以做但要收着做",
            "精选强素材小步放大，不泛铺。")


def _offline(overall: OverallMetrics, th: Thresholds,
             title: str, period: str) -> dict:
    top = overall.countries[:5]
    top_str = "、".join(f"{c.name} {_fmt_pct(c.spend_share)}" for c in top)

    strong_names = [c.name for c in overall.countries
                    if c.breakout_rate and c.breakout_rate >= th.breakout_high]
    weak_names = [c.name for c in overall.countries
                  if c.breakout_rate is not None and c.breakout_rate <= th.breakout_low]

    countries = []
    for c in overall.countries:
        one_liner, tag, action = _country_verdict(c, th)
        conv = (
            f"KOL投放消耗占比：{_fmt_pct(c.spend_share)}\n"
            f"发布占比：{_fmt_pct(c.published_share)}\n"
            f"跑出率：{_fmt_pct(c.breakout_rate)}\n"
            f"平均 ROI7：{_fmt_pct(c.avg_roi7)}\n"
            f"判断：{tag}。"
        )
        strong = "\n".join(f"强/有转化素材：{s.creative}" for s in c.strong[:5])
        pot = "\n".join(f"潜力素材：{s.creative}" for s in c.potential[:4])
        weak = "\n".join(f"弱素材：{s.creative}" for s in c.weak[:3])
        creative_analysis = "\n".join(x for x in [strong, pot, weak] if x) \
            or "本期该国暂无可识别的分档素材。"
        countries.append({
            "name": c.name,
            "one_liner": one_liner,
            "conversion": conv,
            "creative_analysis": creative_analysis,
            "todo": action,
        })

    strategy = (
        f"最值得继续放大：{('、'.join(strong_names)) or '（暂无明显强盘）'}——"
        "有跑出、有主力脚本、ROI7 健康。\n"
        f"当前最弱、需控制投入：{('、'.join(weak_names)) or '（暂无明显弱盘）'}——"
        "跑出率偏低、头部素材依赖严重、可持续性不够。\n"
        "其余国家可以做但要收着做，需精选、不适合泛铺。"
    )

    return {
        "title": title,
        "period": period,
        "overall": {
            "big_picture": (
                f"本期 KOL 素材总消耗约 {overall.total_spend:.2f}。"
                f"国家占比头部主要是：{top_str}。\n"
                "结论：投放盘明显集中在少数头部国家。"
            ),
            "kol_position": (
                "KOL 已经不是边缘补充项，而是整体盘里一个比较重要的消耗来源；"
                "但整体仍是设计素材为主、KOL 素材为重要补充。"
                "后续优化重点不是「有没有量」，而是能否更高效承接消耗、"
                "供给是否投到了对的语言池/国家池。"
            ),
            "caveats": [
                "广告消耗国家 ≠ 素材生产语言：部分西语 KOL 素材实际投在美国广告组，"
                "消耗会记到「美国」。分析时要分清投放池承接能力与素材供给来源。"
            ],
        },
        "strategy_overview": strategy,
        "countries": countries,
    }
