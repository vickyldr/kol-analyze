"""大盘上下文（来自后台截图或手填 JSON）。

用于「覆盖缺口」分析：广告大盘（设计+KOL）某国消耗高，但该语言 KOL 没产出。
四类截图：
  1) 广告大盘分国家消耗占比      -> ad_country_share
  2) 设计师 vs KOL 占比           -> designer_vs_kol（KOL 占整体的比例）
  3) KOL 分国家消耗占比           -> kol_country_share（可选，excel 也能算）
  4) 5月发布分语言（条数/占比）    -> kol_publish_share（可选，excel 也能算）
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MarketContext:
    period_label: str | None = None
    grand_total_spend: float | None = None       # 大盘总消耗（设计+KOL）
    kol_total_spend: float | None = None
    ad_country_share: dict[str, float] = field(default_factory=dict)   # 国家 -> %
    ad_country_spend: dict[str, float] = field(default_factory=dict)   # 国家 -> 绝对值
    kol_share_of_total: float | None = None                            # KOL 占整体 %
    kol_country_share: dict[str, float] = field(default_factory=dict)  # 国家 -> %
    kol_publish_share: dict[str, float] = field(default_factory=dict)  # 语言 -> %
    kol_publish_count: dict[str, int] = field(default_factory=dict)    # 语言 -> 条数
    notes: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.ad_country_share or self.kol_country_share
                    or self.kol_publish_share)


def to_dict(m: "MarketContext") -> dict:
    return {
        "period_label": m.period_label, "grand_total_spend": m.grand_total_spend,
        "kol_total_spend": m.kol_total_spend, "ad_country_share": m.ad_country_share,
        "ad_country_spend": m.ad_country_spend, "kol_share_of_total": m.kol_share_of_total,
        "kol_country_share": m.kol_country_share, "kol_publish_share": m.kol_publish_share,
        "kol_publish_count": m.kol_publish_count, "notes": m.notes,
    }


def load_json(path: str | Path) -> MarketContext:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return from_dict(data)


def _num_dict(d) -> dict:
    """只保留能转成数字的项，丢掉 None / 非数值（截图有时会读到 null）。"""
    out = {}
    for k, v in (d or {}).items():
        if v is None:
            continue
        try:
            out[str(k)] = float(str(v).replace("%", "").replace(",", "").strip())
        except (ValueError, TypeError):
            continue
    return out


def from_dict(data: dict) -> MarketContext:
    return MarketContext(
        period_label=data.get("period_label"),
        grand_total_spend=data.get("grand_total_spend"),
        kol_total_spend=data.get("kol_total_spend"),
        ad_country_share=_num_dict(data.get("ad_country_share")),
        ad_country_spend=_num_dict(data.get("ad_country_spend")),
        kol_share_of_total=data.get("kol_share_of_total"),
        kol_country_share=_num_dict(data.get("kol_country_share")),
        kol_publish_share=_num_dict(data.get("kol_publish_share")),
        kol_publish_count=_num_dict(data.get("kol_publish_count")),
        notes=data.get("notes", []) or [],
    )
