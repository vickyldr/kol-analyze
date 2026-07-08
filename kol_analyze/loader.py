"""读取输入数据：多 sheet 的 Excel，或一个文件夹里的多个 CSV。

每个 sheet / 文件 = 一个国家（区）。每行 = 一条素材。
列名做容错归一化。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .config import build_reverse_alias, normalize_key

# 从 sheet 名 / 文件名里识别国家的一部分线索（可扩展）
_COUNTRY_HINTS = {
    "土耳其": "土耳其", "tr": "土耳其", "turkey": "土耳其",
    "美国": "美国", "us": "美国", "usa": "美国", "西语": "美国", "sp": "美国",
    "巴西": "巴西", "br": "巴西", "brazil": "巴西",
    "台湾": "台湾", "tw": "台湾", "taiwan": "台湾",
    "意大利": "意大利", "it": "意大利", "italy": "意大利",
    "德国": "德国", "de": "德国", "germany": "德国",
    "阿语": "阿语", "ar": "阿语", "arabic": "阿语",
    "日本": "日本", "jp": "日本",
}


@dataclass
class CreativeRow:
    creative: str
    spend: float = 0.0
    published: float = 0.0
    roi7: float | None = None
    roi0: float | None = None
    breakout: float | None = None
    revenue: float | None = None
    ctr: float | None = None
    influencer: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class CountryData:
    name: str            # 展示用国家名，例：土耳其
    sheet_name: str      # 原始 sheet/文件名，用作“相关表”
    rows: list[CreativeRow] = field(default_factory=list)


def _guess_country(label: str) -> str:
    key = str(label).lower()
    for hint, country in _COUNTRY_HINTS.items():
        if hint in key:
            return country
    # 取 sheet 名里最像国家的中文段
    m = re.search(r"[一-龥]{2,}", str(label))
    return m.group(0) if m else str(label)


def _to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in ("nan", "none", "-", "/"):
        return None
    s = s.replace(",", "").replace("%", "").replace("￥", "").replace("$", "")
    try:
        return float(s)
    except ValueError:
        return None


def _map_columns(df: pd.DataFrame) -> dict[str, str]:
    """返回 标准字段 -> df 实际列名。"""
    rev = build_reverse_alias()
    mapping: dict[str, str] = {}
    for col in df.columns:
        std = rev.get(normalize_key(col))
        if std and std not in mapping:
            mapping[std] = col
    return mapping


def _rows_from_df(df: pd.DataFrame) -> list[CreativeRow]:
    df = df.dropna(how="all")
    colmap = _map_columns(df)
    if "creative" not in colmap:
        # 没有识别到素材名列，退化为用第一列当素材名
        colmap["creative"] = df.columns[0]

    rows: list[CreativeRow] = []
    for _, r in df.iterrows():
        name = str(r[colmap["creative"]]).strip()
        if not name or name.lower() == "nan":
            continue
        rows.append(
            CreativeRow(
                creative=name,
                spend=_to_float(r.get(colmap.get("spend"))) or 0.0,
                published=_to_float(r.get(colmap.get("published"))) or 0.0,
                roi7=_to_float(r.get(colmap.get("roi7"))),
                roi0=_to_float(r.get(colmap.get("roi0"))),
                breakout=_to_float(r.get(colmap.get("breakout"))),
                revenue=_to_float(r.get(colmap.get("revenue"))),
                ctr=_to_float(r.get(colmap.get("ctr"))),
                influencer=(str(r.get(colmap.get("influencer"))).strip()
                            if colmap.get("influencer") else None),
                raw={c: r[c] for c in df.columns},
            )
        )
    return rows


def load(path: str | Path) -> list[CountryData]:
    """从 Excel(多 sheet) 或 目录(多 CSV/Excel) 载入按国家分组的数据。"""
    p = Path(path)
    countries: list[CountryData] = []

    if p.is_dir():
        files = sorted(
            [f for f in p.iterdir()
             if f.suffix.lower() in (".csv", ".xlsx", ".xls")]
        )
        for f in files:
            if f.suffix.lower() == ".csv":
                df = pd.read_csv(f)
                countries.append(_country_from(df, f.stem))
            else:
                for sheet, df in pd.read_excel(f, sheet_name=None).items():
                    countries.append(_country_from(df, sheet))
    elif p.suffix.lower() in (".xlsx", ".xls"):
        for sheet, df in pd.read_excel(p, sheet_name=None).items():
            countries.append(_country_from(df, sheet))
    elif p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
        countries.append(_country_from(df, p.stem))
    else:
        raise ValueError(f"不支持的输入类型: {p}")

    # 过滤掉没有任何素材行的空表
    return [c for c in countries if c.rows]


def _country_from(df: pd.DataFrame, label: str) -> CountryData:
    return CountryData(
        name=_guess_country(label),
        sheet_name=str(label),
        rows=_rows_from_df(df),
    )
