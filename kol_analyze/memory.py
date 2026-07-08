"""命名修正记忆库。

广告命名由实习生填，常不准/不全。这里让你注入修正，并持久化，
分析时自动套用。支持三层（优先级从高到低）：

1) play_overrides：对某个「玩法字符串」或「ad_name」精确改写标签
2) keyword_rules ：命中关键词就追加/替换 脚本/形式 标签
3) influencer_alias / lang_overrides：红人别名、语言纠正

例：TR 的「图生音乐混合功能_口播功能录屏介绍」——
   形式其实是「口播」，脚本本质是「自制AI热歌」（AI热歌口述），
   所以给它同时打上 口播 + 自制AI热歌 两个标签。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Override:
    set_script: list[str] = field(default_factory=list)   # 替换脚本主题
    add_script: list[str] = field(default_factory=list)   # 追加脚本主题
    set_format: list[str] = field(default_factory=list)   # 替换形式
    add_format: list[str] = field(default_factory=list)   # 追加形式
    note: str = ""


@dataclass
class KeywordRule:
    match: str                                    # 命中的关键词（子串，忽略大小写）
    add_script: list[str] = field(default_factory=list)
    add_format: list[str] = field(default_factory=list)
    set_script: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Memory:
    play_overrides: dict[str, Override] = field(default_factory=dict)
    keyword_rules: list[KeywordRule] = field(default_factory=list)
    influencer_alias: dict[str, str] = field(default_factory=dict)
    lang_overrides: dict[str, str] = field(default_factory=dict)  # ad_name/play -> 语言代码
    path: Path | None = None

    # ---------------- 应用 ----------------
    def apply_tags(self, ad_name: str, play: str | None,
                   base_scripts: list[str], base_formats: list[str]
                   ) -> tuple[list[str], list[str]]:
        scripts = list(base_scripts)
        formats = list(base_formats)

        # 精确覆盖：优先 ad_name，其次 play
        for key in (ad_name, play):
            if key and key in self.play_overrides:
                ov = self.play_overrides[key]
                if ov.set_script:
                    scripts = list(ov.set_script)
                if ov.set_format:
                    formats = list(ov.set_format)
                scripts += [s for s in ov.add_script if s not in scripts]
                formats += [f for f in ov.add_format if f not in formats]

        # 关键词规则
        hay = f"{ad_name} {play or ''}".lower()
        for rule in self.keyword_rules:
            if rule.match.lower() in hay:
                if rule.set_script:
                    scripts = list(rule.set_script)
                scripts += [s for s in rule.add_script if s not in scripts]
                formats += [f for f in rule.add_format if f not in formats]

        return (scripts or ["其他"]), formats

    def alias_influencer(self, name: str | None) -> str | None:
        return self.influencer_alias.get(name, name) if name else name

    def override_lang(self, ad_name: str, play: str | None) -> str | None:
        for key in (ad_name, play):
            if key and key in self.lang_overrides:
                return self.lang_overrides[key]
        return None

    # ---------------- 增改（供 CLI / Web 注入） ----------------
    def add_play_override(self, key: str, *, set_script=None, add_script=None,
                          set_format=None, add_format=None, note="") -> None:
        self.play_overrides[key] = Override(
            set_script=set_script or [], add_script=add_script or [],
            set_format=set_format or [], add_format=add_format or [], note=note)

    def save(self, path: str | Path | None = None) -> Path:
        p = Path(path or self.path or "memory/overrides.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(to_dict(self), ensure_ascii=False, indent=2),
                     encoding="utf-8")
        self.path = p
        return p


def to_dict(m: Memory) -> dict:
    return {
        "play_overrides": {
            k: {"set_script": v.set_script, "add_script": v.add_script,
                "set_format": v.set_format, "add_format": v.add_format,
                "note": v.note}
            for k, v in m.play_overrides.items()},
        "keyword_rules": [
            {"match": r.match, "add_script": r.add_script,
             "add_format": r.add_format, "set_script": r.set_script,
             "note": r.note} for r in m.keyword_rules],
        "influencer_alias": m.influencer_alias,
        "lang_overrides": m.lang_overrides,
    }


def from_dict(data: dict, path: Path | None = None) -> Memory:
    return Memory(
        play_overrides={
            k: Override(
                set_script=v.get("set_script", []), add_script=v.get("add_script", []),
                set_format=v.get("set_format", []), add_format=v.get("add_format", []),
                note=v.get("note", ""))
            for k, v in (data.get("play_overrides") or {}).items()},
        keyword_rules=[
            KeywordRule(match=r["match"], add_script=r.get("add_script", []),
                        add_format=r.get("add_format", []),
                        set_script=r.get("set_script", []), note=r.get("note", ""))
            for r in (data.get("keyword_rules") or [])],
        influencer_alias=data.get("influencer_alias", {}) or {},
        lang_overrides=data.get("lang_overrides", {}) or {},
        path=path,
    )


def load(path: str | Path | None) -> Memory:
    if not path:
        return Memory()
    p = Path(path)
    if not p.exists():
        return Memory(path=p)
    return from_dict(json.loads(p.read_text(encoding="utf-8")), path=p)
