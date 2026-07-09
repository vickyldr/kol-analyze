"""聚合：
  A) KOL 按【语言】的指标 + 素材分档（来自 excel 明细）
  B) 产出 vs 消耗 的【缺口分析】（结合大盘截图）—— 核心产出
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from . import country
from .config import Thresholds
from .loader import Dataset, LangGroup
from .market import MarketContext


@dataclass
class CreativeAgg:
    ad_name: str
    influencer: str | None
    play: str | None
    spend: float
    roi7: float | None       # 小数
    conv_devices: float
    tier: str                # strong / potential / weak
    spend_share_in_lang: float


@dataclass
class LangMetrics:
    lang: str
    name: str
    count: int                       # 去重后的素材条数
    raw_count: int                   # 原始行数（含同素材多组）
    spend: float
    spend_share: float = 0.0         # 占 KOL 总消耗 %
    breakout_rate: float | None = None  # 有转化条数 / 总条数 %
    avg_roi7: float | None = None    # %
    creatives: list[CreativeAgg] = field(default_factory=list)
    top_influencers: list[tuple[str, int]] = field(default_factory=list)
    top_plays: list[tuple[str, int]] = field(default_factory=list)

    @property
    def strong(self):
        return [c for c in self.creatives if c.tier == "strong"]

    @property
    def potential(self):
        return [c for c in self.creatives if c.tier == "potential"]

    @property
    def weak(self):
        return [c for c in self.creatives if c.tier == "weak"]


@dataclass
class GapRow:
    lang: str
    name: str
    ad_market_share: float | None    # 大盘（设计+KOL）该语言消耗占比 %
    kol_spend_share: float | None    # KOL 消耗占比 %
    publish_share: float | None      # 产出（发布）占比 %
    breakout_rate: float | None
    verdict: str                     # 加量 / 削减 / 覆盖缺口 / 减少 / 维持 / 高潜
    one_line: str                    # 一句话结论


@dataclass
class Analysis:
    langs: list[LangMetrics]
    gaps: list[GapRow]
    kol_total_spend: float
    market: MarketContext
    coverage_gaps: list[str] = field(default_factory=list)  # 大盘有钱但没产出的语言/国家


def _tier(roi7: float | None, converted: bool, share: float,
          th: Thresholds) -> str:
    r = roi7 if roi7 is not None else 0.0
    if converted and r >= th.roi7_strong / 100 and share >= th.spend_share_meaningful:
        return "strong"
    if converted or r >= th.roi7_potential / 100:
        return "potential"
    return "weak"


def _lang_metrics(g: LangGroup, th: Thresholds) -> LangMetrics:
    # 去重：同 ad_name 合并（同素材可能投多个广告组）
    agg: dict[str, dict] = defaultdict(
        lambda: {"spend": 0.0, "roi7": None, "conv": 0.0,
                 "influencer": None, "play": None})
    conv_names, all_names = set(), set()
    infl_counter: dict[str, int] = defaultdict(int)
    play_counter: dict[str, int] = defaultdict(int)
    roi_vals = []

    for r in g.rows:
        a = agg[r.ad_name]
        a["spend"] += r.spend
        if r.roi7 is not None:
            a["roi7"] = max(a["roi7"] or 0.0, r.roi7)
        a["conv"] += r.conv_devices
        a["influencer"] = a["influencer"] or r.influencer
        a["play"] = a["play"] or r.play
        all_names.add(r.ad_name)
        if r.converted:
            conv_names.add(r.ad_name)

    total_spend = sum(a["spend"] for a in agg.values())
    for name, a in agg.items():
        if a["influencer"]:
            infl_counter[a["influencer"]] += 1
        if a["play"]:
            play_counter[a["play"]] += 1
        if a["roi7"] is not None:
            roi_vals.append(a["roi7"])

    creatives = []
    for name, a in agg.items():
        share = (a["spend"] / total_spend) if total_spend else 0.0
        creatives.append(CreativeAgg(
            ad_name=name, influencer=a["influencer"], play=a["play"],
            spend=a["spend"], roi7=a["roi7"], conv_devices=a["conv"],
            tier=_tier(a["roi7"], name in conv_names, share, th),
            spend_share_in_lang=share,
        ))
    creatives.sort(key=lambda c: c.spend, reverse=True)

    count = len(all_names)
    breakout = (len(conv_names) / count * 100) if count else None
    avg_roi7 = (sum(roi_vals) / len(roi_vals) * 100) if roi_vals else None

    return LangMetrics(
        lang=g.lang, name=g.name, count=count, raw_count=len(g.rows),
        spend=total_spend, breakout_rate=breakout, avg_roi7=avg_roi7,
        creatives=creatives,
        top_influencers=sorted(infl_counter.items(), key=lambda x: -x[1])[:6],
        top_plays=sorted(play_counter.items(), key=lambda x: -x[1])[:6],
    )


def _market_lang_share(market: MarketContext) -> dict[str, float]:
    """把大盘【国家】消耗占比聚合成【语言】占比。"""
    out: dict[str, float] = defaultdict(float)
    for c, pct in market.ad_country_share.items():
        lang = country.country_lang(c)
        if lang:
            out[lang] += pct
    return dict(out)


def _verdict(ad_share, kol_share, pub_share, breakout, th, incomplete=False):
    """给一句话结论 + 档位。incomplete=该语言 excel 消耗疑似未填充。"""
    ad = ad_share or 0.0
    kol = kol_share or 0.0
    pub = pub_share or 0.0
    br = breakout

    # excel 消耗未填充但有产出：先别下「削减」，标记待补全
    if incomplete and kol < 0.5 and pub >= 1.0:
        return "待补全", "本期 excel 该语言消耗数据可能未填充，补全后再判断加量/削减。"

    # 大盘有明显消耗，但 KOL 几乎没产出/没承接 -> 覆盖缺口
    if ad >= 2.0 and pub < 1.0 and kol < 1.0:
        return "覆盖缺口", "广告大盘有量、KOL 却没覆盖，值得补产出验证。"
    # 产出远大于承接 -> 削减
    if pub - kol >= th.over_invest_gap:
        return "削减", "产出明显多于消耗承接，投入过量，应降频提质。"
    # 承接远大于产出 且 跑得动 -> 加量
    if kol - pub >= th.over_invest_gap * 0.6 and (br is None or br >= th.breakout_low):
        return "加量", "承接强于产出、跑出不差，值得加量放大。"
    # 有产出但几乎没消耗承接 -> 减少
    if pub >= 3.0 and kol < 1.0:
        return "减少", "有产出但广告几乎不消耗，建议减少或先优化。"
    # 样本很小但跑出率高 -> 高潜
    if br is not None and br >= th.breakout_high and pub < 3.0:
        return "高潜", "样本少但信号好，作为高潜新线小步补量。"
    return "维持", "产出与消耗大体匹配，维持并精选。"


def compute(ds: Dataset, market: MarketContext, th: Thresholds,
            assume_complete: bool = False) -> Analysis:
    langs = [_lang_metrics(g, th) for g in ds.langs if g.rows]
    total = sum(l.spend for l in langs) or 1.0
    for l in langs:
        l.spend_share = l.spend / total * 100
    langs.sort(key=lambda l: l.spend, reverse=True)

    # 产出占比：优先用截图发布占比，否则用 excel 条数占比
    total_count = sum(l.count for l in langs) or 1
    pub_share_by_lang = dict(market.kol_publish_share) if market.kol_publish_share else {}
    if not pub_share_by_lang:
        pub_share_by_lang = {l.lang: l.count / total_count * 100 for l in langs}

    # KOL 消耗占比：优先 excel 语言口径
    kol_share_by_lang = {l.lang: l.spend_share for l in langs}

    ad_lang_share = _market_lang_share(market)

    # 覆盖的语言集合
    covered = {l.lang for l in langs if l.count > 0}

    # excel 是否被单一语言主导（说明其余语言消耗可能未填充完整）
    top_share = max((l.spend_share for l in langs), default=0.0)
    excel_incomplete = (top_share >= 85.0) and not assume_complete
    if excel_incomplete:
        dominant = max(langs, key=lambda l: l.spend_share).name
        market.notes.append(
            f"数据提醒：本期 excel 消耗高度集中在「{dominant}」（{top_share:.0f}%），"
            "其余语言的 KOL 消耗口径可能尚未填充完整，缺口结论以「待补全」标注、暂缓下削减判断。")

    gaps: list[GapRow] = []
    seen = set()
    for l in langs:
        seen.add(l.lang)
        ad_s = ad_lang_share.get(l.lang)
        verdict, line = _verdict(ad_s, kol_share_by_lang.get(l.lang),
                                 pub_share_by_lang.get(l.lang), l.breakout_rate, th,
                                 incomplete=excel_incomplete and l.spend_share < 85.0)
        gaps.append(GapRow(
            lang=l.lang, name=l.name, ad_market_share=ad_s,
            kol_spend_share=kol_share_by_lang.get(l.lang),
            publish_share=pub_share_by_lang.get(l.lang),
            breakout_rate=l.breakout_rate, verdict=verdict, one_line=line,
        ))

    # 大盘有量、但 KOL 完全没覆盖的语言（纯缺口）
    coverage_gaps = []
    for lang, share in sorted(ad_lang_share.items(), key=lambda x: -x[1]):
        if share >= 2.0 and lang not in covered:
            gaps.append(GapRow(
                lang=lang, name=country.lang_name(lang), ad_market_share=share,
                kol_spend_share=0.0, publish_share=0.0, breakout_rate=None,
                verdict="覆盖缺口",
                one_line="广告大盘有量、KOL 完全没产出，是明确的补产出机会。",
            ))
            coverage_gaps.append(f"{country.lang_name(lang)}（大盘 {share:.1f}%）")

    return Analysis(langs=langs, gaps=gaps, kol_total_spend=sum(l.spend for l in langs),
                    market=market, coverage_gaps=coverage_gaps)
