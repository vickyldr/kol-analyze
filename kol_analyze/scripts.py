"""素材/脚本 维度分析（跨语言）。

在国家/语言维度之上，回答：
- 哪个脚本/形式在某语言做得好、其他语言要不要也做（迁移建议）
- 每个脚本 继续做 / 优化 / 砍
- 某语言跑出率普遍低 -> 要不要挖新脚本；脚本单一但有潜力 -> 要不要探索
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from . import country
from .config import FORMAT_TAGS, SCRIPT_TAGS, TECH_TAGS, Thresholds
from .memory import Memory
from .metrics import CreativeAgg, LangMetrics


def _match_tags(text: str | None, table: dict[str, list[str]]) -> list[str]:
    if not text:
        return []
    low = text.lower()
    return [tag for tag, kws in table.items() if any(k.lower() in low for k in kws)]


def _base_scripts(c: CreativeAgg) -> list[str]:
    themes = _match_tags(c.play, SCRIPT_TAGS)
    if themes:
        return themes
    tech = _match_tags(c.play, TECH_TAGS)
    return tech[:1] if tech else [(c.play or "其他").split("_")[0]]


def script_themes(c: CreativeAgg, mem: Memory | None = None) -> list[str]:
    """给素材的脚本主题（可多个）；记忆库修正会追加/替换。"""
    base = _base_scripts(c)
    if mem is None:
        return base
    scripts, _ = mem.apply_tags(c.ad_name, c.play, base, _match_tags(c.play, FORMAT_TAGS))
    return scripts


def format_tags(c: CreativeAgg, mem: Memory | None = None) -> list[str]:
    base = _match_tags(c.play, FORMAT_TAGS)
    if mem is None:
        return base
    _, formats = mem.apply_tags(c.ad_name, c.play, _base_scripts(c), base)
    return formats


@dataclass
class Cell:
    lang: str
    name: str
    count: int = 0
    spend: float = 0.0
    best_roi7: float | None = None   # 小数
    converted: int = 0

    @property
    def is_strong(self) -> bool:
        return self.converted > 0 and (self.best_roi7 or 0) >= 0.30

    @property
    def is_weak(self) -> bool:
        return self.converted == 0 and self.spend > 0


@dataclass
class ScriptRow:
    theme: str
    cells: dict[str, Cell] = field(default_factory=dict)
    total_spend: float = 0.0
    best_lang: str | None = None
    strong_langs: list[str] = field(default_factory=list)
    migrate_to: list[str] = field(default_factory=list)   # 建议扩展到的语言
    reason: str = ""


@dataclass
class FormatRow:
    fmt: str
    present: dict[str, int] = field(default_factory=dict)   # 语言名 -> 条数
    suggest_to: list[str] = field(default_factory=list)     # 建议试的语言
    note: str = ""


@dataclass
class LangStrategy:
    lang: str
    name: str
    diversity: int
    breakout: float | None
    top_scripts: list[str]
    verdict: str        # 挖新脚本 / 探索新脚本 / 收窄精做 / 维持精选
    suggestion: str


@dataclass
class ScriptAnalysis:
    scripts: list[ScriptRow]
    formats: list[FormatRow]
    migrations: list[ScriptRow]
    lang_strategies: list[LangStrategy]
    review: "ScriptReview | None" = None   # 脚本层复盘（内容脚本 × 效率比，见下）


def analyze(langs: list[LangMetrics], th: Thresholds,
            incomplete_langs: set | None = None,
            mem: Memory | None = None) -> ScriptAnalysis:
    incomplete_langs = incomplete_langs or set()
    active = [l for l in langs if l.count >= 3]          # 有一定产出的语言
    active_names = {l.lang: l.name for l in active}

    # ---- 脚本(主题) × 语言（一条素材可归入多个主题：记忆库修正） ----
    script_map: dict[str, ScriptRow] = {}
    for l in langs:
        for c in l.creatives:
            for theme in script_themes(c, mem):
                row = script_map.setdefault(theme, ScriptRow(theme=theme))
                cell = row.cells.setdefault(l.lang, Cell(lang=l.lang, name=l.name))
                cell.count += 1
                cell.spend += c.spend
                if c.roi7 is not None:
                    cell.best_roi7 = max(cell.best_roi7 or 0.0, c.roi7)
                if c.conv_devices > 0:
                    cell.converted += 1
                row.total_spend += c.spend

    for row in script_map.values():
        row.strong_langs = [c.name for c in row.cells.values() if c.is_strong]
        strong_cells = [c for c in row.cells.values() if c.is_strong]
        if strong_cells:
            best = max(strong_cells, key=lambda c: (c.best_roi7 or 0, c.spend))
            row.best_lang = best.name
        # 建议迁移：在某语言强，但另一些活跃语言完全没做
        if row.strong_langs:
            done = set(row.cells.keys())
            row.migrate_to = [active_names[lg] for lg in active_names
                              if lg not in done]
            if row.migrate_to:
                row.reason = f"「{row.theme}」在 {row.best_lang} 已跑出，" \
                             f"但 {'、'.join(row.migrate_to)} 还没做，值得试。"

    scripts_sorted = sorted(script_map.values(),
                            key=lambda r: r.total_spend, reverse=True)
    migrations = [r for r in scripts_sorted if r.migrate_to and r.strong_langs]

    # ---- 形式 × 语言 ----
    fmt_map: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    lang_formats: dict[str, set] = defaultdict(set)
    for l in langs:
        for c in l.creatives:
            for f in format_tags(c, mem):
                fmt_map[f][l.name] += 1
                lang_formats[l.lang].add(f)

    formats: list[FormatRow] = []
    for fmt, present in fmt_map.items():
        # 哪些活跃语言几乎没用这个形式 -> 建议试
        suggest = [l.name for l in active
                   if fmt not in lang_formats[l.lang]]
        note = ""
        if suggest:
            top = max(present.items(), key=lambda x: x[1])[0]
            note = f"{top} 在用「{fmt}」，{'、'.join(suggest)} 基本没试，可测试。"
        formats.append(FormatRow(fmt=fmt, present=dict(present),
                                 suggest_to=suggest, note=note))
    formats.sort(key=lambda f: sum(f.present.values()), reverse=True)

    # ---- 各语言脚本策略 ----
    strategies: list[LangStrategy] = []
    for l in active:
        themes = {t for c in l.creatives if c.spend > 0 or c.conv_devices > 0
                  for t in script_themes(c, mem)}
        diversity = len(themes) or len({t for c in l.creatives
                                        for t in script_themes(c, mem)})
        br = l.breakout_rate
        strong = [t for c in l.strong for t in script_themes(c, mem)][:3]
        has_potential = bool(l.strong or l.potential)

        if l.lang in incomplete_langs:
            verdict = "待补全"
            sug = "本期该语言消耗/转化数据可能未填充，补全后再定脚本策略（继续/砍/挖新）。"
        elif br is not None and br < th.breakout_low and diversity >= 3:
            verdict = "收窄精做"
            sug = f"脚本多但跑出率低（{br:.1f}%），先收窄到强脚本、砍掉跑不出的弱版。"
        elif br is not None and br < th.breakout_low:
            verdict = "挖新脚本"
            sug = f"普遍跑出率低（{br:.1f}%），现有脚本承接弱，建议挖掘新脚本方向。"
        elif diversity <= 2 and has_potential:
            verdict = "探索新脚本"
            sug = f"脚本较单一（{diversity} 类）但有潜力，建议在保住主力的同时探索新脚本。"
        else:
            verdict = "维持精选"
            sug = "脚本结构健康，维持主力、精选红人即可。"
        strategies.append(LangStrategy(
            lang=l.lang, name=l.name, diversity=diversity, breakout=br,
            top_scripts=strong, verdict=verdict, suggestion=sug))

    return ScriptAnalysis(scripts=scripts_sorted, formats=formats,
                          migrations=migrations, lang_strategies=strategies)


# ==========================================================================
# 脚本层复盘（对齐 rm-kol-review skill）：
#   - 从 ad_name 抽【内容脚本】（形式 口播/mv/街采、方法 图生/文生 都不算脚本）
#   - 效率比 = 消耗占比 ÷ 投入占比（发布占比优先，无则条数占比）
#   - 跑出 = ROI0 > 0（按行不去重）
#   - 全盘脚本层 + 地区×脚本 + 跨盘警示 + AI热歌内部（功能录屏 vs 普通）
# ==========================================================================

# 西语系并入 SP；AR=阿语（单列，不并入西语）
_SPANISH = {"SP", "ES", "MX", "CO", "CL", "PE", "VE", "EC", "BO", "PY", "UY",
            "GT", "DO", "HN", "SV", "NI", "CR", "PA"}
_ISO = {"US", "GB", "CA", "AU", "BR", "TH", "TW", "TR", "IT", "DE", "JP", "KR",
        "RU", "FR", "AR", "IN", "ID", "VN", "PH", "MY", "SG", "NL", "PL"} | _SPANISH

# 内容脚本关键词，顺序=优先级（具体母题 > 泛街采兜底）
_SCRIPT_RULES = [
    ("拉踩(对比)", ["拉踩"]),
    ("财阀mv", ["财阀"]),
    ("省钱mv", ["省钱"]),
    ("公交白t", ["公交"]),
    ("海边开车", ["海边开车"]),
    ("黑白乌鸦海边", ["乌鸦"]),
    ("佛寺(TH场景)", ["佛寺"]),
    ("对镜", ["对镜"]),
    ("AI热歌", ["录屏", "rythmix介绍", "混合功能", "照片变", "功能介绍",
              "功能录屏", "热mv", "热歌", "ai热", "AI热"]),
    ("世界杯", ["世界杯"]),
    ("音乐人", ["音乐人"]),
    ("走位街采", ["走位"]),
    ("中年男舞台", ["舞台"]),
    ("情侣", ["情侣"]),
    ("一句话生成", ["一句话"]),
    ("复刻黑白镜头", ["复刻黑白"]),
    ("泛拍照街采", ["街采"]),   # 无具体母题的街采兜底
]
_DEMO_KW = ["录屏", "rythmix介绍", "混合功能", "照片变", "功能介绍", "功能录屏"]
_EFF_HI, _EFF_LO = 1.2, 0.6


def detect_region(ad: str) -> str:
    for t in re.split(r"[_\s]+", str(ad)):
        u = t.strip().upper()
        if u in _ISO:
            return "SP" if u in _SPANISH else u
    return "OTHER"


def content_script(ad: str, mem: Memory | None = None) -> str:
    """从 ad_name 抽【内容脚本】；记忆库的强制/规则可覆盖关键词判定。"""
    a = str(ad)
    base = "其他/自定义"
    for name, kws in _SCRIPT_RULES:
        if any(k in a for k in kws):
            base = name
            break
    if mem is not None:
        try:
            scr, _ = mem.apply_tags(a, None, [base], [])
            if scr:
                return scr[0]
        except Exception:
            pass
    return base


def _is_demo(ad: str) -> bool:
    a = str(ad)
    return any(k in a for k in _DEMO_KW)


def _ran(r) -> int:
    """跑出=1：优先 ROI0>0（skill 口径）；导出缺 ROI0 列时回退到「有转化」。"""
    if getattr(r, "roi0", None) is not None:
        return 1 if r.roi0 > 0 else 0
    return 1 if (getattr(r, "converted", False) or (r.conv_devices or 0) > 0) else 0


@dataclass
class ScriptStat:
    name: str
    n: int
    count_share: float          # 条数占比 %
    spend: float
    spend_share: float          # 消耗占比 %
    publish_share: float | None  # 发布占比 %（投入侧，来自看板；无则 None）
    eff: float | None           # 效率比 = 消耗占比 ÷ (发布占比 or 条数占比)
    breakout: float             # 跑出率 %（ROI0>0）
    verdict: str                # 加发布 / 提质不提量 / 微调 / 收缩


@dataclass
class RegionScripts:
    region: str                 # 显示名（语言/盘）
    code: str
    n: int
    spend: float
    scripts: list[ScriptStat]


@dataclass
class CrossWarn:
    script: str
    detail: str


@dataclass
class AiSplitRow:
    region: str
    demo_n: int
    demo_run: float | None
    normal_n: int
    normal_run: float | None


@dataclass
class ScriptReview:
    total_spend: float
    total_n: int
    overall: list[ScriptStat] = field(default_factory=list)
    regions: list[RegionScripts] = field(default_factory=list)
    warnings: list[CrossWarn] = field(default_factory=list)
    ai_split: list[AiSplitRow] = field(default_factory=list)
    has_publish: bool = False


def _script_tier(cp: float, eff: float | None, run: float) -> str:
    if cp < 1:
        return "收缩/量极小"
    if run < 10:
        return "收缩"
    if eff is not None and eff >= _EFF_HI:
        return "加发布"
    if eff is not None and eff < _EFF_LO:
        return "提质不提量"
    return "微调"


def _stats(agg: dict, tot_n: int, tot_sp: float,
           pub: dict | None) -> list[ScriptStat]:
    out = []
    for name, (n, sp, ru) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
        cs = n / tot_n * 100 if tot_n else 0.0
        ss = sp / tot_sp * 100 if tot_sp else 0.0
        p = pub.get(name) if pub else None
        base = p if p else cs
        eff = (ss / base) if base else None
        run = ru / n * 100 if n else 0.0
        out.append(ScriptStat(
            name=name, n=n, count_share=round(cs, 1), spend=round(sp),
            spend_share=round(ss, 1), publish_share=p,
            eff=round(eff, 2) if eff is not None else None,
            breakout=round(run, 1), verdict=_script_tier(ss, eff, run)))
    return out


def _region_name(code: str) -> str:
    return "未识别" if code == "OTHER" else country.lang_name(code)


def _cross_warn(reg_rows: dict, mem: Memory | None) -> list[CrossWarn]:
    """同一脚本在不同盘跑出率两极分化 -> 警示禁止照搬。"""
    by_script: dict[str, dict[str, tuple]] = defaultdict(dict)
    for code, rr in reg_rows.items():
        d = defaultdict(lambda: [0, 0])
        for r in rr:
            s = content_script(r.ad_name, mem)
            d[s][0] += 1
            d[s][1] += _ran(r)
        for s, (n, ru) in d.items():
            if n >= 3:
                by_script[s][code] = (n, ru / n * 100)
    warns = []
    for s, regs in by_script.items():
        if len(regs) < 2:
            continue
        best = max(regs.items(), key=lambda kv: kv[1][1])
        worst = min(regs.items(), key=lambda kv: kv[1][1])
        if best[1][1] - worst[1][1] >= 40 and worst[1][1] <= 25:
            warns.append(CrossWarn(
                script=s,
                detail=(f"「{s}」在 {_region_name(best[0])} 跑出 {best[1][1]:.0f}%"
                        f"（主力），在 {_region_name(worst[0])} 只有 {worst[1][1]:.0f}%"
                        f"（黑洞），禁止跨盘照搬。")))
    warns.sort(key=lambda w: w.script)
    return warns[:8]


def script_review(ds, market=None, mem: Memory | None = None) -> ScriptReview:
    """脚本层复盘：内容脚本 × 效率比 × 跑出率，全盘 + 地区 + 跨盘 + AI热歌内部。"""
    rows = [r for g in ds.langs for r in g.rows]
    tot_n = len(rows)
    tot_sp = sum(r.spend for r in rows) or 0.0

    pub = None
    if market is not None:
        ps = getattr(market, "kol_script_publish_share", None)
        pub = dict(ps) if ps else None

    # 全盘脚本层
    S = defaultdict(lambda: [0, 0.0, 0])
    for r in rows:
        s = content_script(r.ad_name, mem)
        S[s][0] += 1
        S[s][1] += r.spend
        S[s][2] += _ran(r)
    overall = _stats(S, tot_n, tot_sp, pub)

    # 地区 × 脚本
    reg_rows: dict[str, list] = defaultdict(list)
    for r in rows:
        reg_rows[detect_region(r.ad_name)].append(r)
    regions = []
    for code, rr in sorted(reg_rows.items(),
                           key=lambda kv: -sum(x.spend for x in kv[1])):
        tn = len(rr)
        tsp = sum(x.spend for x in rr)
        d = defaultdict(lambda: [0, 0.0, 0])
        for r in rr:
            s = content_script(r.ad_name, mem)
            d[s][0] += 1
            d[s][1] += r.spend
            d[s][2] += _ran(r)
        regions.append(RegionScripts(
            region=_region_name(code), code=code, n=tn, spend=round(tsp),
            scripts=_stats(d, tn, tsp, None)))

    # AI热歌内部：功能录屏 vs 普通自制热歌
    ai = []
    for code, rr in reg_rows.items():
        demo = [0, 0]
        norm = [0, 0]
        for r in rr:
            if content_script(r.ad_name, mem) != "AI热歌":
                continue
            hit = _ran(r)
            if _is_demo(r.ad_name):
                demo[0] += 1
                demo[1] += hit
            else:
                norm[0] += 1
                norm[1] += hit
        if demo[0] or norm[0]:
            ai.append(AiSplitRow(
                region=_region_name(code),
                demo_n=demo[0],
                demo_run=round(demo[1] / demo[0] * 100, 1) if demo[0] else None,
                normal_n=norm[0],
                normal_run=round(norm[1] / norm[0] * 100, 1) if norm[0] else None))
    ai.sort(key=lambda x: -(x.demo_n + x.normal_n))

    return ScriptReview(
        total_spend=round(tot_sp), total_n=tot_n, overall=overall,
        regions=regions, warnings=_cross_warn(reg_rows, mem), ai_split=ai,
        has_publish=bool(pub))
