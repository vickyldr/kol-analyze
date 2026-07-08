"""素材/脚本 维度分析（跨语言）。

在国家/语言维度之上，回答：
- 哪个脚本/形式在某语言做得好、其他语言要不要也做（迁移建议）
- 每个脚本 继续做 / 优化 / 砍
- 某语言跑出率普遍低 -> 要不要挖新脚本；脚本单一但有潜力 -> 要不要探索
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

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
