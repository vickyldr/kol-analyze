"""把原始素材行聚合成国家级指标，并给素材分档。

这些是“客观数字”，交给 Claude 去写“主观判断/复盘话术”。
规则兜底（offline）也用这里的分档结果。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import Thresholds
from .loader import CountryData, CreativeRow


@dataclass
class CreativeStat:
    creative: str
    spend: float
    spend_share_in_country: float  # 占该国总消耗
    roi7: float | None
    breakout: float | None
    influencer: str | None
    tier: str  # strong / potential / weak


@dataclass
class CountryMetrics:
    name: str
    sheet_name: str
    total_spend: float
    published_count: float
    breakout_rate: float | None  # 该国跑出率（若原始有跑出率则取均值，否则由强素材占比估算）
    avg_roi7: float | None
    # 跨国占比（需要全局才能算，先占位，聚合后回填）
    spend_share: float = 0.0
    published_share: float = 0.0
    creatives: list[CreativeStat] = field(default_factory=list)

    @property
    def strong(self) -> list[CreativeStat]:
        return [c for c in self.creatives if c.tier == "strong"]

    @property
    def potential(self) -> list[CreativeStat]:
        return [c for c in self.creatives if c.tier == "potential"]

    @property
    def weak(self) -> list[CreativeStat]:
        return [c for c in self.creatives if c.tier == "weak"]


@dataclass
class OverallMetrics:
    total_spend: float
    countries: list[CountryMetrics]
    # 大盘（设计+KOL）层面的数据，通常来自截图，可选
    grand_total_spend: float | None = None
    country_spend_share: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _tier_of(row: CreativeRow, country_total_spend: float,
             th: Thresholds) -> str:
    share = (row.spend / country_total_spend) if country_total_spend else 0.0
    roi = row.roi7
    if roi is not None:
        if roi >= th.roi7_strong and share >= th.spend_share_meaningful:
            return "strong"
        if roi >= th.roi7_potential:
            return "potential"
        return "weak"
    # 没有 ROI 时，用消耗占比粗判
    if share >= th.spend_share_meaningful * 2:
        return "strong"
    if share >= th.spend_share_meaningful:
        return "potential"
    return "weak"


def _country_metrics(cd: CountryData, th: Thresholds) -> CountryMetrics:
    total_spend = sum(r.spend for r in cd.rows)
    published = sum(1 for r in cd.rows if r.published) or float(len(cd.rows))

    roi_vals = [r.roi7 for r in cd.rows if r.roi7 is not None]
    avg_roi7 = sum(roi_vals) / len(roi_vals) if roi_vals else None

    breakout_vals = [r.breakout for r in cd.rows if r.breakout is not None]

    stats: list[CreativeStat] = []
    for r in cd.rows:
        tier = _tier_of(r, total_spend, th)
        stats.append(CreativeStat(
            creative=r.creative,
            spend=r.spend,
            spend_share_in_country=(r.spend / total_spend) if total_spend else 0.0,
            roi7=r.roi7,
            breakout=r.breakout,
            influencer=r.influencer,
            tier=tier,
        ))
    stats.sort(key=lambda s: s.spend, reverse=True)

    if breakout_vals:
        breakout_rate = sum(breakout_vals) / len(breakout_vals)
    else:
        # 用强素材条数占比估一个跑出率
        strong = sum(1 for s in stats if s.tier == "strong")
        breakout_rate = (strong / len(stats) * 100) if stats else None

    return CountryMetrics(
        name=cd.name,
        sheet_name=cd.sheet_name,
        total_spend=total_spend,
        published_count=published,
        breakout_rate=breakout_rate,
        avg_roi7=avg_roi7,
        creatives=stats,
    )


def compute(countries: list[CountryData], th: Thresholds) -> OverallMetrics:
    cms = [_country_metrics(c, th) for c in countries]
    total_spend = sum(c.total_spend for c in cms)
    total_pub = sum(c.published_count for c in cms) or 1.0

    for c in cms:
        c.spend_share = (c.total_spend / total_spend * 100) if total_spend else 0.0
        c.published_share = (c.published_count / total_pub * 100)

    cms.sort(key=lambda c: c.total_spend, reverse=True)
    return OverallMetrics(total_spend=total_spend, countries=cms)
