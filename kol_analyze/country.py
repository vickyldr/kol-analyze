"""语言 / 国家 归一化，以及从 ad_name 解析 语言 / 红人 / 玩法。

关键口径（按你的要求）：KOL 素材的产出/分析一律按【语言】看，
英语(US) 与 西语(SP) 分开，不用「美国」这个国家口径。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import PRODUCTS  # 运行时会被原地更新（动态添加产品）

# 语言代码 -> 中文语言名（用于 KOL 产出/素材分析）
LANG_NAME: dict[str, str] = {
    "TR": "土耳其语", "US": "英语", "EN": "英语", "SP": "西语", "ES": "西语",
    "BR": "葡语", "PT": "葡语", "IT": "意语", "KR": "韩语", "JP": "日语",
    "AR": "阿语", "FR": "法语", "TW": "繁中", "DE": "德语", "RU": "俄语",
    "ID": "印尼语", "TH": "泰语", "VN": "越南语", "HI": "印地语",
}

# 大盘截图里的【国家】-> 对应【语言代码】（用于「覆盖缺口」分析：
# 广告大盘某国消耗高，但该语言 KOL 没产出）
COUNTRY_TO_LANG: dict[str, str] = {
    "美国": "US", "英国": "US", "加拿大": "US", "澳大利亚": "US",
    "土耳其": "TR",
    "西班牙": "SP", "墨西哥": "SP", "哥伦比亚": "SP", "阿根廷": "SP",
    "智利": "SP", "秘鲁": "SP",
    "巴西": "BR",
    "意大利": "IT", "德国": "DE", "法国": "FR", "荷兰": "FR", "比利时": "FR",
    "韩国": "KR", "日本": "JP", "台湾": "TW",
    "沙特阿拉伯": "AR", "阿联酋": "AR", "伊拉克": "AR", "科威特": "AR",
    "卡塔尔": "AR", "阿曼": "AR", "约旦": "AR", "埃及": "AR",
    "泰国": "TH", "乌克兰": "RU", "哈萨克斯坦": "RU", "白俄罗斯": "RU",
    "以色列": "AR", "瑞士": "DE", "奥地利": "DE", "阿塞拜疆": "RU",
    "乌兹别克斯坦": "RU", "马来西亚": "ID",
}


def lang_name(code: str | None) -> str:
    if not code:
        return "其他"
    return LANG_NAME.get(code.upper(), code.upper())


def country_lang(country: str) -> str | None:
    return COUNTRY_TO_LANG.get(str(country).strip())


@dataclass
class NameParts:
    lang: str | None       # 语言代码，如 TR
    influencer: str | None  # 红人，如 凝视哥
    play: str | None        # 玩法，如 图生音乐混合功能_口播功能录屏介绍


def parse_ad_name(name: str) -> NameParts:
    """解析 ad_name，如 RM_TR_KOL_凝视哥_20260212_图生音乐混合功能_口播功能录屏介绍。

    结构大致为：…前缀…_RM_<语言>_[KOL]_<红人>_<日期>_<玩法...>
    有些名字前面带哈希/文案前缀（如 24812446…_RM_TR_KOL_… 或
    「Los invito … app _RM_SP_KOL_…」），所以从 token 里定位 RM/KOL 锚点，
    而不是死认第 2 段。
    """
    n = str(name)
    toks = n.split("_")

    # 1) 定位语言锚点：<产品>_<CC>_ 或 KOL_<CC>_（产品动态，含 RM/RC/RO/自定义…）
    anchors = {p.upper() for p in PRODUCTS} | {"KOL"}
    lang = None
    core = 0  # 语言代码所在的 token 索引
    for i in range(len(toks) - 1):
        if toks[i].strip().upper() in anchors and \
                re.fullmatch(r"[A-Za-z]{2}", toks[i + 1].strip()):
            lang = toks[i + 1].strip().upper()
            core = i + 1
            break
    if lang is None:
        # 退化：找一个本身就是已知语言代码的独立 2 字母 token
        for i, t in enumerate(toks):
            if re.fullmatch(r"[A-Za-z]{2}", t.strip()) and t.strip().upper() in LANG_NAME:
                lang = t.strip().upper()
                core = i
                break

    rest = toks[core + 1:] if lang else toks

    # 2) 从锚点之后找日期，锚定红人 / 玩法
    date_idx = None
    for i, t in enumerate(rest):
        if re.fullmatch(r"\d{6,8}", t):
            date_idx = i
            break

    influencer = None
    play = None
    if date_idx is not None:
        mid = [t for t in rest[:date_idx] if t.upper() != "KOL"]
        influencer = mid[-1] if mid else None
        if date_idx + 1 < len(rest):
            play = "_".join(rest[date_idx + 1:])
    else:
        mid = [t for t in rest if t.upper() != "KOL"]
        influencer = mid[0] if mid else None

    return NameParts(lang=lang, influencer=influencer, play=play)


def detect_product(name: str) -> str | None:
    """从 ad_name 里认出产品前缀（RM/RC/RO…）。"""
    for t in str(name).split("_"):
        u = t.strip().upper()
        if u in PRODUCTS:
            return u
    return None


def clean_play(play: str | None) -> str | None:
    """去掉玩法尾部的 btta / 日期等噪声，保留可读的玩法主体。"""
    if not play:
        return None
    toks = play.split("_")
    keep = [t for t in toks
            if not re.fullmatch(r"\d{4,8}", t) and t.lower() != "btta"]
    return "_".join(keep) if keep else play
