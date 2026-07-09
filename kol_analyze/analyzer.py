"""调用 Claude 生成复盘叙述；无 API key 时用规则兜底。"""

from __future__ import annotations

import json
import os

from . import engine, prompts
from .config import Settings, Thresholds
from .metrics import Analysis, LangMetrics
from .scripts import ScriptAnalysis


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


def analyze(analysis: Analysis, scripts: ScriptAnalysis, settings: Settings,
            title: str, period: str, mem=None) -> dict:
    if engine.available() == "offline":
        if not settings.allow_offline_fallback:
            raise RuntimeError("无可用的 Claude 引擎（订阅 CLI / API key 都没有），"
                               "且未允许离线兜底。")
        return _offline(analysis, scripts, settings.thresholds, title, period)

    user = prompts.USER_TEMPLATE.format(
        title=title, period=period, style=prompts.style_block(mem),
        schema=json.dumps(prompts.OUTPUT_SCHEMA_HINT, ensure_ascii=False, indent=2),
        facts=json.dumps(prompts.build_facts(analysis), ensure_ascii=False, indent=2),
        script_facts=json.dumps(prompts.build_script_facts(scripts),
                                ensure_ascii=False, indent=2))
    text = engine.generate_text(prompts.SYSTEM, user, settings.model,
                                settings.max_tokens)
    if not text:
        return _offline(analysis, scripts, settings.thresholds, title, period)
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, ValueError):
        return _offline(analysis, scripts, settings.thresholds, title, period)


def revise_passage(scope: str, text: str, instruction: str, reason: str,
                   settings: Settings) -> str | None:
    """让 Claude 只重写复盘里的一段。返回改后的文字；不可用/失败返回 None。"""
    if engine.available() == "offline":
        return None
    user = prompts.REVISE_USER.format(
        scope=scope, text=text, instruction=instruction,
        reason_line=(f"（我觉得原来不好的原因：{reason}）" if reason else ""))
    out = engine.generate_text(prompts.REVISE_SYSTEM, user, settings.model,
                               max_tokens=1500, timeout=120)
    return out.strip() if out else None


def polish_document(blocks_map: dict, settings: Settings, mem=None) -> dict | None:
    """一键润色全文：传入 {key: 文字}，返回润色后的 {key: 文字}。失败返回 None。"""
    if engine.available() == "offline":
        return None
    user = (prompts.style_block(mem)
            + "\n下面是复盘各段文字（JSON: key -> 文字），逐段润色后返回同结构 JSON：\n"
            + json.dumps(blocks_map, ensure_ascii=False, indent=2))
    out = engine.generate_text(prompts.POLISH_SYSTEM, user, settings.model,
                               max_tokens=settings.max_tokens, timeout=300)
    if not out:
        return None
    try:
        res = _extract_json(out)
        return res if isinstance(res, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


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


def _script_section(sa: ScriptAnalysis) -> dict:
    migrations = [r.reason for r in sa.migrations[:8] if r.reason]
    fmt_sug = [f.note for f in sa.formats if f.note][:6]
    strat = [{"name": s.name, "suggestion": s.suggestion}
             for s in sa.lang_strategies]

    strong_scripts = [r.theme for r in sa.scripts if r.strong_langs][:5]
    overview = (
        f"跨语言看，主力脚本集中在 {('、'.join(strong_scripts)) or '少数方向'}；"
        "口播/街采/MV 各语言覆盖不均，存在明确的迁移与补形式空间（见下）。")
    return {"overview": overview, "migrations": migrations or ["本期暂无明确的跨语言迁移点。"],
            "format_suggestions": fmt_sug or ["形式覆盖较均衡。"],
            "lang_strategies": strat}


def _offline(a: Analysis, sa: ScriptAnalysis, th: Thresholds,
             title: str, period: str) -> dict:
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
    top_c = sorted(m.ad_country_share.items(), key=lambda x: -(x[1] or 0))[:5]
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
        "script_section": _script_section(sa),
        "langs": [_lang_block(l) for l in a.langs],
    }
