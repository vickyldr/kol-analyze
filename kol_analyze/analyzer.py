"""调用 Claude 生成复盘叙述；无 API key 时用规则兜底。"""

from __future__ import annotations

import json
import os

from . import prompts
from .config import Settings, Thresholds
from .metrics import Analysis, LangMetrics


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e != -1:
        text = text[s:e + 1]
    return json.loads(text)


def analyze(analysis: Analysis, settings: Settings,
            title: str, period: str) -> dict:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        if not settings.allow_offline_fallback:
            raise RuntimeError("未检测到 ANTHROPIC_API_KEY，且未允许离线兜底。")
        return _offline(analysis, settings.thresholds, title, period)

    import anthropic
    client = anthropic.Anthropic()
    facts = prompts.build_facts(analysis)
    user = prompts.USER_TEMPLATE.format(
        title=title, period=period,
        schema=json.dumps(prompts.OUTPUT_SCHEMA_HINT, ensure_ascii=False, indent=2),
        facts=json.dumps(facts, ensure_ascii=False, indent=2))
    msg = client.messages.create(
        model=settings.model, max_tokens=settings.max_tokens,
        temperature=settings.temperature, system=prompts.SYSTEM,
        messages=[{"role": "user", "content": user}])
    text = "".join(b.text for b in msg.content
                   if getattr(b, "type", "") == "text")
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, ValueError):
        return _offline(analysis, settings.thresholds, title, period)


# --------------------------------------------------------------------------
# 规则兜底
# --------------------------------------------------------------------------

def _pct(v) -> str:
    return f"{v:.2f}%" if v is not None else "—"


def _label(c) -> str:
    """红人·玩法 的可读标签，玩法为空时回退到素材名尾段。"""
    play = c.play or (c.ad_name.split("_")[-1] if c.ad_name else "")
    infl = c.influencer or ""
    return f"{infl}·{play}".strip("·") or c.ad_name


def _dedup(creatives):
    """按 红人·玩法 合并（btta/日期版本视为同一素材），累计消耗、取最高 ROI7。"""
    merged: dict[str, dict] = {}
    for c in creatives:
        key = _label(c)
        m = merged.setdefault(key, {"spend": 0.0, "roi7": 0.0})
        m["spend"] += c.spend
        m["roi7"] = max(m["roi7"], (c.roi7 or 0.0))
    return sorted(merged.items(), key=lambda kv: kv[1]["spend"], reverse=True)


def _lang_block(l: LangMetrics) -> dict:
    strong = "\n".join(
        f"强/有转化：{name}（ROI7 {m['roi7']*100:.0f}%，消耗 {m['spend']:.0f}）"
        for name, m in _dedup(l.strong)[:5])
    pot = "\n".join(f"潜力：{name}" for name, _ in _dedup(l.potential)[:4])
    weak = "\n".join(f"弱：{name}" for name, _ in _dedup(l.weak)[:3])
    ca = "\n".join(x for x in [strong, pot, weak] if x) or "本期该语言暂无可识别分档素材。"

    plays = "、".join(f"{p}" for p, _ in l.top_plays[:3])
    if l.strong:
        top_name = _dedup(l.strong)[0][0]
        todo = (f"继续放大 {top_name}\n"
                f"围绕主力玩法（{plays}）继续复刻，精选红人\n"
                "减少 ROI7 偏低的弱版，控制泛量")
        one = "主力语言池" if l.spend_share >= 15 else "有承接的次主力"
    else:
        todo = "小步验证，先跑老脚本提高命中率，不泛铺"
        one = "样本/承接偏弱，需精选"

    conv = (f"产出条数：{l.count}\n消耗占比：{_pct(l.spend_share)}\n"
            f"跑出率：{_pct(l.breakout_rate)}\n平均 ROI7：{_pct(l.avg_roi7)}")
    return {"name": l.name, "one_liner": one, "conversion": conv,
            "creative_analysis": ca, "todo": todo}


def _offline(a: Analysis, th: Thresholds, title: str, period: str) -> dict:
    add = [g.name for g in a.gaps if g.verdict == "加量"]
    cut = [g.name for g in a.gaps if g.verdict in ("削减", "减少")]
    gap = a.coverage_gaps + [g.name for g in a.gaps
                             if g.verdict == "覆盖缺口" and g.name not in
                             [x.split("（")[0] for x in a.coverage_gaps]]
    hi = [g.name for g in a.gaps if g.verdict == "高潜"]

    pending = [g.name for g in a.gaps if g.verdict == "待补全"]
    gap_summary = "；".join(x for x in [
        f"值得加量：{('、'.join(add)) or '暂无'}",
        f"应削减/降频：{('、'.join(cut)) or '暂无'}",
        f"覆盖缺口(大盘有量但没产出)：{('、'.join(dict.fromkeys(gap))) or '暂无'}",
        (f"高潜新线：{'、'.join(hi)}" if hi else ""),
        (f"待 excel 补全消耗：{'、'.join(pending)}" if pending else ""),
    ] if x)

    m = a.market
    top_c = sorted(m.ad_country_share.items(), key=lambda x: -x[1])[:5]
    top_str = "、".join(f"{c} {p:.2f}%" for c, p in top_c) or "（无大盘截图数据）"
    ad_overview = (
        f"广告大盘（设计+KOL）总消耗约 {m.grand_total_spend or '—'}，"
        f"分国家头部：{top_str}，明显集中在少数头部国家。\n"
        f"KOL 占整体约 {_pct(m.kol_share_of_total)}，"
        "仍是设计素材为主、KOL 为重要补充。")

    return {
        "title": title, "period": period,
        "ad_section": {
            "overview": ad_overview,
            "caveat": "KOL 素材一律按语言看，英语(US) 与 西语(SP) 分开，不用「美国」国家口径；"
                      "实际执行与产出都看语言。",
        },
        "gap_summary": gap_summary,
        "langs": [_lang_block(l) for l in a.langs],
    }
