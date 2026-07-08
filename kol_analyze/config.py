"""列名映射、阈值、模型等可配置项。

输入表格的列名往往不统一（中文/英文/不同后台导出），这里做一层
容错映射：把各种可能的写法都归一到内部标准字段。
"""

from __future__ import annotations

from dataclasses import dataclass, field

# 内部标准字段 -> 可能出现在输入表里的列名（大小写/空格不敏感匹配）
COLUMN_ALIASES: dict[str, list[str]] = {
    "creative": [
        "素材名称", "素材", "素材名", "creative", "creative_name",
        "material", "ad_name", "广告名称", "名称",
    ],
    "spend": [
        "消耗", "花费", "广告消耗", "spend", "cost", "投放消耗", "消耗金额",
    ],
    "published": [
        "发布", "发布数", "是否发布", "published", "publish", "上线",
    ],
    "roi7": [
        "roi7", "roi_7", "roi7天", "7日roi", "7天roi", "roi 7",
    ],
    "roi0": [
        "roi0", "roi_0", "当日roi",
    ],
    "breakout": [
        "跑出率", "跑出", "breakout", "breakout_rate", "跑出比例",
    ],
    "impressions": [
        "曝光", "展示", "impressions", "imp",
    ],
    "clicks": [
        "点击", "clicks", "点击数",
    ],
    "ctr": [
        "点击率", "ctr", "click_rate",
    ],
    "revenue": [
        "预估净收入", "净收入", "收入", "revenue", "income", "预估收入",
    ],
    "installs": [
        "安装", "installs", "下载",
    ],
    "influencer": [
        "红人", "达人", "kol", "influencer", "红人名称", "达人名称",
    ],
}


@dataclass
class Thresholds:
    """规则兜底 / 素材分档用到的阈值。可按业务口径调整。"""

    # ROI7 分档（百分比，如 30 表示 30%）
    roi7_strong: float = 30.0     # >= 强素材 / 有转化
    roi7_potential: float = 15.0  # >= 潜力素材
    # 单条素材被视为“有效承接消耗”的最低消耗占比（占该国总消耗）
    spend_share_meaningful: float = 0.03
    # 国家级：跑出率高/低的分界（百分比）
    breakout_high: float = 12.0
    breakout_low: float = 5.0
    # 国家级：判定“投入过量”的发布占比高于消耗占比的差值（百分点）
    over_invest_gap: float = 8.0


@dataclass
class Settings:
    model: str = "claude-opus-4-8"
    vision_model: str = "claude-opus-4-8"
    max_tokens: int = 8000
    temperature: float = 0.4
    thresholds: Thresholds = field(default_factory=Thresholds)
    # 没有 ANTHROPIC_API_KEY 时是否允许用规则兜底生成（便于离线演示/测试）
    allow_offline_fallback: bool = True
    language: str = "zh"  # 输出语言


def normalize_key(name: str) -> str:
    return "".join(str(name).lower().split())


def build_reverse_alias() -> dict[str, str]:
    """返回 归一化列名 -> 标准字段 的映射。"""
    rev: dict[str, str] = {}
    for std, aliases in COLUMN_ALIASES.items():
        for a in aliases:
            rev[normalize_key(a)] = std
    return rev
