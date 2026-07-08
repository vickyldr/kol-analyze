"""读取输入数据。

支持两种输入：
1) 【后台标准导出】一个 xlsx，含 `KOL素材` / `设计师素材` / `汇总统计` 等 sheet，
   每行一条广告，国家/红人/玩法 从 ad_name 解析（推荐，你的真实格式）。
2) 【简单格式】每个 sheet/CSV = 一个国家，列名如 素材名称/消耗/ROI7 …（兜底）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import country
from .config import build_reverse_alias, normalize_key

# 后台导出里认得的列名
_C_ADNAME = ["ad_name", "素材名称", "广告名称"]
_C_ROLE = ["设计师orkol", "设计师ORKOL", "role", "类型"]
_C_SPEND = ["投放花费（爬虫）", "投放花费", "消耗", "花费", "spend"]
_C_ROI7 = ["roi7（归因）", "roi7", "roi_7"]
_C_ROI0 = ["roi0（归因）", "roi0"]
_C_CONV = ["安装7日内试用&付费设备数", "安装当日试用&付费设备数", "转化设备数"]
_C_CTR = ["点击率(全部)(爬虫)", "点击率", "ctr"]
_C_FUNC = ["功能点", "玩法功能"]


@dataclass
class CreativeRow:
    ad_name: str
    lang: str | None = None
    influencer: str | None = None
    play: str | None = None
    spend: float = 0.0
    roi7: float | None = None       # 小数口径，0.52 = 52%
    roi0: float | None = None
    converted: bool = False         # 是否有转化
    conv_devices: float = 0.0
    ctr: float | None = None


@dataclass
class LangGroup:
    """按语言聚合的一组 KOL 素材。"""
    lang: str
    name: str                       # 中文语言名
    rows: list[CreativeRow] = field(default_factory=list)


@dataclass
class Summary:
    """汇总统计 sheet：整体/设计师/KOL 的条数、消耗、跑出率。"""
    rows: dict[str, dict] = field(default_factory=dict)  # 分组 -> 指标


@dataclass
class Dataset:
    langs: list[LangGroup]
    summary: Summary | None = None
    kol_total_spend: float = 0.0


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    norm = {normalize_key(c): c for c in df.columns}
    for cand in candidates:
        c = norm.get(normalize_key(cand))
        if c:
            return c
    return None


def _to_float(v) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", "").replace("%", "").replace("$", "")
    if s == "" or s.lower() in ("nan", "none", "-", "/"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# 后台标准导出
# --------------------------------------------------------------------------

def _is_backend_export(sheets: dict[str, pd.DataFrame]) -> bool:
    for df in sheets.values():
        if _find_col(df, _C_ADNAME) and _find_col(df, _C_ROLE):
            return True
    return False


def _load_backend(sheets: dict[str, pd.DataFrame], _mem=None) -> Dataset:
    # 选一个 KOL 明细 sheet：优先叫 KOL素材 的；否则从含 role 的 sheet 里筛 KOL
    kol_df = None
    for name, df in sheets.items():
        if "kol" in name.lower() and _find_col(df, _C_ADNAME):
            kol_df = df
            break
    if kol_df is None:
        for df in sheets.values():
            role = _find_col(df, _C_ROLE)
            if role and _find_col(df, _C_ADNAME):
                kol_df = df[df[role].astype(str).str.upper().str.contains("KOL")]
                break
    if kol_df is None or kol_df.empty:
        raise ValueError("未在后台导出里找到 KOL 明细。")

    c_name = _find_col(kol_df, _C_ADNAME)
    c_spend = _find_col(kol_df, _C_SPEND)
    c_roi7 = _find_col(kol_df, _C_ROI7)
    c_roi0 = _find_col(kol_df, _C_ROI0)
    c_conv = _find_col(kol_df, _C_CONV)
    c_ctr = _find_col(kol_df, _C_CTR)

    groups: dict[str, LangGroup] = {}
    total_spend = 0.0
    for _, r in kol_df.iterrows():
        name = str(r[c_name]).strip()
        if not name or name.lower() == "nan":
            continue
        parts = country.parse_ad_name(name)
        # 记忆库：语言纠正 + 红人别名
        forced_lang = _mem.override_lang(name, parts.play) if _mem else None
        influencer = _mem.alias_influencer(parts.influencer) if _mem else parts.influencer
        lang = forced_lang or parts.lang or "OTHER"
        conv_dev = _to_float(r.get(c_conv)) or 0.0 if c_conv else 0.0
        spend = _to_float(r.get(c_spend)) or 0.0 if c_spend else 0.0
        total_spend += spend
        row = CreativeRow(
            ad_name=name,
            lang=forced_lang or parts.lang,
            influencer=influencer,
            play=country.clean_play(parts.play),
            spend=spend,
            roi7=_to_float(r.get(c_roi7)) if c_roi7 else None,
            roi0=_to_float(r.get(c_roi0)) if c_roi0 else None,
            converted=conv_dev > 0,
            conv_devices=conv_dev,
            ctr=_to_float(r.get(c_ctr)) if c_ctr else None,
        )
        g = groups.setdefault(lang, LangGroup(lang=lang, name=country.lang_name(lang)))
        g.rows.append(row)

    summary = _load_summary(sheets)
    langs = sorted(groups.values(), key=lambda g: sum(x.spend for x in g.rows),
                   reverse=True)
    return Dataset(langs=langs, summary=summary, kol_total_spend=total_spend)


def _load_summary(sheets: dict[str, pd.DataFrame]) -> Summary | None:
    for name, df in sheets.items():
        if "汇总" in name or "summary" in name.lower():
            grp_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            out: dict[str, dict] = {}
            for _, r in df.iterrows():
                key = str(r[grp_col]).strip()
                if key and key.lower() != "nan":
                    out[key] = {c: r[c] for c in df.columns}
            return Summary(rows=out)
    return None


# --------------------------------------------------------------------------
# 简单格式（兜底）：每个 sheet/CSV = 一个国家/语言
# --------------------------------------------------------------------------

def _load_simple(sheets: dict[str, pd.DataFrame]) -> Dataset:
    rev = build_reverse_alias()
    groups: list[LangGroup] = []
    total = 0.0
    for label, df in sheets.items():
        colmap = {}
        for col in df.columns:
            std = rev.get(normalize_key(col))
            if std and std not in colmap:
                colmap[std] = col
        namecol = colmap.get("creative", df.columns[0])
        # 从 sheet 名猜语言
        parts = country.parse_ad_name(str(label)) if str(label).startswith("RM_") else None
        lang = parts.lang if parts else None
        g = LangGroup(lang=lang or label, name=country.lang_name(lang) if lang else str(label))
        for _, r in df.dropna(how="all").iterrows():
            nm = str(r[namecol]).strip()
            if not nm or nm.lower() == "nan":
                continue
            p = country.parse_ad_name(nm)
            spend = _to_float(r.get(colmap.get("spend"))) or 0.0
            total += spend
            roi = _to_float(r.get(colmap.get("roi7")))
            if roi is not None and roi > 3:  # 简单格式常填百分数
                roi = roi / 100.0
            g.rows.append(CreativeRow(
                ad_name=nm, lang=p.lang, influencer=p.influencer,
                play=country.clean_play(p.play), spend=spend, roi7=roi,
                converted=(roi or 0) > 0,
            ))
        if g.rows:
            groups.append(g)
    return Dataset(langs=groups, summary=None, kol_total_spend=total)


def load(path: str | Path, mem=None) -> Dataset:
    p = Path(path)
    sheets: dict[str, pd.DataFrame] = {}
    if p.is_dir():
        for f in sorted(p.iterdir()):
            if f.suffix.lower() == ".csv":
                sheets[f.stem] = pd.read_csv(f)
            elif f.suffix.lower() in (".xlsx", ".xls"):
                sheets.update(pd.read_excel(f, sheet_name=None))
    elif p.suffix.lower() in (".xlsx", ".xls"):
        sheets = pd.read_excel(p, sheet_name=None)
    elif p.suffix.lower() == ".csv":
        sheets[p.stem] = pd.read_csv(p)
    else:
        raise ValueError(f"不支持的输入类型: {p}")

    if _is_backend_export(sheets):
        return _load_backend(sheets, mem)
    return _load_simple(sheets)
