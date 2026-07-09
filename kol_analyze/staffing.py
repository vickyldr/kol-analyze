"""人力分工：谁负责哪些语言 + 结合缺口/脚本结论给调整建议。

输入（每行一人，姓名后跟其负责的地区/语言/角色）：
    景雨: 西语, 台湾, 阿语
    杨岚平: 土语, 意, 英
    章若冰: 葡语, 泰语, 采买
「采买」这类不是语言的，按角色保留、不参与语言现状匹配。
"""

from __future__ import annotations

import re

from .country import LANG_NAME

# 分工表里常见简写 -> 语言代码
_REGION_ALIAS = {
    "西语": "SP", "西": "SP", "sp": "SP",
    "台湾": "TW", "繁中": "TW", "tw": "TW",
    "阿语": "AR", "阿": "AR", "ar": "AR",
    "土语": "TR", "土耳其": "TR", "土耳其语": "TR", "tr": "TR",
    "意": "IT", "意语": "IT", "意大利": "IT", "it": "IT",
    "英": "US", "英语": "US", "美国": "US", "us": "US", "en": "US",
    "葡语": "BR", "葡": "BR", "巴西": "BR", "br": "BR",
    "泰语": "TH", "泰": "TH", "th": "TH",
    "日语": "JP", "日": "JP", "jp": "JP",
    "德语": "DE", "德": "DE", "de": "DE",
    "法语": "FR", "法": "FR", "fr": "FR",
    "韩语": "KR", "韩": "KR", "kr": "KR",
    "俄语": "RU", "俄": "RU", "ru": "RU",
}


def resolve_region(region: str) -> str | None:
    """把一个分工项解析成语言名；不是语言（如「采买/拍摄」）返回 None。"""
    r = str(region).strip()
    code = _REGION_ALIAS.get(r) or _REGION_ALIAS.get(r.lower())
    if code:
        return LANG_NAME.get(code, code)
    return None


def parse(text: str) -> list[dict]:
    """解析分工文本为 [{person, regions:[...]}]。"""
    people = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.split(r"[:：]", line, maxsplit=1)
        if len(m) < 2:
            continue
        person = m[0].strip()
        regions = [x.strip() for x in re.split(r"[,，、/\s]+", m[1]) if x.strip()]
        if person and regions:
            people.append({"person": person, "regions": regions})
    return people


def build_facts(text: str, gaps, strategies) -> dict:
    """把分工 + 各语言现状，整理成给 Claude / 兜底用的事实。"""
    people = parse(text)
    gap_by = {g.name: g for g in gaps}
    strat_by = {s.name: s for s in strategies}
    assigned = set()
    out = []
    for p in people:
        langs, roles = [], []
        for reg in p["regions"]:
            ln = resolve_region(reg)
            if ln:
                assigned.add(ln)
                g = gap_by.get(ln)
                s = strat_by.get(ln)
                langs.append({
                    "语言": ln,
                    "档位": g.verdict if g else "无数据",
                    "结论": g.one_line if g else None,
                    "消耗占比%": round(g.kol_spend_share, 2) if g and g.kol_spend_share is not None else None,
                    "产出占比%": round(g.publish_share, 2) if g and g.publish_share is not None else None,
                    "脚本策略": (s.suggestion if s else None),
                })
            else:
                roles.append(reg)
        out.append({"负责人": p["person"], "负责语言": langs, "其他角色": roles})

    opportunities = [
        {"语言": g.name, "档位": g.verdict, "原因": g.one_line}
        for g in gaps if g.verdict in ("覆盖缺口", "高潜") and g.name not in assigned
    ]
    return {"people": out, "无人负责的机会语言": opportunities,
            "has_staffing": bool(people)}
