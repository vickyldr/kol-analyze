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
    products: dict[str, int] = field(default_factory=dict)  # 检测到的产品 -> 素材条数


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

def _is_backend_export(pairs: list[tuple[str, pd.DataFrame]]) -> bool:
    for _, df in pairs:
        if _find_col(df, _C_ADNAME) and _find_col(df, _C_ROLE):
            return True
    return False


def _kol_frame_of_file(sheets: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame | None:
    """从「一个文件的若干 sheet」里取 KOL 明细：优先 KOL素材 sheet，否则按 role 筛。"""
    for label, df in sheets:
        sheet = label.split("::")[-1]
        if "kol" in sheet.lower() and _find_col(df, _C_ADNAME):
            return df
    for _, df in sheets:
        role = _find_col(df, _C_ROLE)
        if role and _find_col(df, _C_ADNAME):
            return df[df[role].astype(str).str.upper().str.contains("KOL")]
    return None


def _load_backend(pairs: list[tuple[str, pd.DataFrame]], _mem=None) -> Dataset:
    # 关键：跨【所有文件】把 KOL 明细累加合并（每个文件取自己的 KOL素材 sheet）
    by_file: dict[str, list[tuple[str, pd.DataFrame]]] = {}
    for label, df in pairs:
        by_file.setdefault(label.split("::")[0], []).append((label, df))

    frames = []
    for _, sheets in by_file.items():
        kf = _kol_frame_of_file(sheets)
        if kf is not None and not kf.empty:
            frames.append(kf)
    if not frames:
        raise ValueError("未在后台导出里找到 KOL 明细。")
    kol_df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]

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

    summary = _load_summary(pairs)
    langs = sorted(groups.values(), key=lambda g: sum(x.spend for x in g.rows),
                   reverse=True)
    products: dict[str, int] = {}
    for g in groups.values():
        for r in g.rows:
            pr = country.detect_product(r.ad_name)
            if pr:
                products[pr] = products.get(pr, 0) + 1
    return Dataset(langs=langs, summary=summary, kol_total_spend=total_spend,
                   products=products)


def _load_summary(pairs: list[tuple[str, pd.DataFrame]]) -> Summary | None:
    for name, df in pairs:
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

def _load_simple(pairs: list[tuple[str, pd.DataFrame]]) -> Dataset:
    rev = build_reverse_alias()
    groups: list[LangGroup] = []
    total = 0.0
    for label, df in pairs:
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
    # 用「列表」而不是「字典」收集所有 sheet，label 带文件名前缀，
    # 避免多个文件里同名 sheet（如都叫 KOL素材）互相覆盖。
    pairs: list[tuple[str, pd.DataFrame]] = []

    def add_excel(f: Path):
        for sheet, df in pd.read_excel(f, sheet_name=None).items():
            pairs.append((f"{f.stem}::{sheet}", df))

    if p.is_dir():
        for f in sorted(p.iterdir()):
            if f.suffix.lower() == ".csv":
                pairs.append((f.stem, pd.read_csv(f)))
            elif f.suffix.lower() in (".xlsx", ".xls"):
                add_excel(f)
    elif p.suffix.lower() in (".xlsx", ".xls"):
        add_excel(p)
    elif p.suffix.lower() == ".csv":
        pairs.append((p.stem, pd.read_csv(p)))
    else:
        raise ValueError(f"不支持的输入类型: {p}")

    if _is_backend_export(pairs):
        return _load_backend(pairs, mem)
    return _load_simple(pairs)
