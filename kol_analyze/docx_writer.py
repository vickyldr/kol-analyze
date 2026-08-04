"""渲染复盘 .docx：
  一、广告部份（大盘/设计vsKOL/KOL分国家 + 概述）
  二、KOL 分语言素材分析（核心；两层建议：每个语言=现状+国家级建议+脚本级明细表）
  三、素材/脚本维度分析（跨语言：迁移 / 形式覆盖 / 各语言脚本策略）
  四、人力分工与调整建议
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from .metrics import Analysis
from .scripts import ScriptAnalysis

_HEADER_BG = "2F5496"
_ALT_BG = "F2F5FB"
_VERDICT_COLOR = {
    "加量": "2E7D32", "高潜": "1565C0", "维持": "555555",
    "削减": "C62828", "减少": "C62828", "覆盖缺口": "E65100",
    "待补全": "8E24AA",
}


def _shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(tcPr.makeelement(qn("w:shd"), {
        qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): hex_color}))


def _multiline(cell, text, bold_first=False, size=9, color=None):
    cell.text = ""
    para = cell.paragraphs[0]
    for i, line in enumerate(str(text).split("\n")):
        if i > 0:
            para = cell.add_paragraph()
        para.paragraph_format.space_after = Pt(1)
        run = para.add_run(line)
        run.font.size = Pt(size)
        if bold_first and i == 0:
            run.bold = True
        if color:
            run.font.color.rgb = RGBColor.from_string(color)


def _heading(doc, text, size, color="1F3864", bold=True, before=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)


def _body(doc, text, size=10, color=None):
    for line in str(text).split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(line)
        r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def _mk_table(doc, headers, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = 1
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        _shade(hdr[i], _HEADER_BG)
        hdr[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor.from_string("FFFFFF")
    return t, widths


def _apply_widths(table, widths):
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths):
                cell.width = widths[i]


def _pct(v):
    return f"{v:.2f}%" if v is not None else "—"


# 单条素材（脚本）级建议的档 -> 颜色
_TIER_COLOR = {"放大": "2E7D32", "优化": "1565C0", "再试": "1565C0",
               "砍": "C62828", "淘汰": "999999"}


def _script_advice(tier, conv, share) -> tuple[str, str]:
    """按单条素材（同红人·玩法合并后）的真实数据，给档 + 一句脚本级建议。"""
    if tier == "strong":
        return "放大", "主力，继续放大 + 精选红人复刻，可作跨语言母版"
    if tier == "potential":
        if conv and conv > 0:
            return "优化", "有转化但 ROI 未达标，优化脚本 / 换红人后再加量"
        return "再试", "信号一般，换红人或小改脚本再验证一轮"
    # weak
    if share >= 0.12:
        return "砍", "ROI 偏低仍在吃量，收量或换方向"
    return "淘汰", "弱版，淘汰或仅留极小量测试"


_TIER_ORDER = {"strong": 2, "potential": 1, "weak": 0}


def _merge_scripts(creatives) -> list[dict]:
    """把同一「红人·玩法」的多条（btta/日期版本）合并：累计消耗、取最高 ROI7、
    累计转化、取更强的档。返回按消耗降序的行。"""
    merged: dict[str, dict] = {}
    for c in creatives:
        key = " · ".join(x for x in [c.influencer, c.play] if x) or c.ad_name
        m = merged.get(key)
        if not m:
            merged[key] = {"label": key, "spend": c.spend, "roi7": c.roi7,
                           "conv": c.conv_devices or 0.0, "platform": c.platform,
                           "tier": c.tier, "share": c.spend_share_in_lang}
        else:
            m["spend"] += c.spend
            m["roi7"] = max(m["roi7"] or 0.0, c.roi7 or 0.0)
            m["conv"] += c.conv_devices or 0.0
            m["share"] += c.spend_share_in_lang
            m["platform"] = m["platform"] or c.platform
            if _TIER_ORDER[c.tier] > _TIER_ORDER[m["tier"]]:
                m["tier"] = c.tier
    return sorted(merged.values(), key=lambda x: -x["spend"])


def _lang_detail(doc, lb, g, lm):
    """一个语言两层建议：语言级（现状+国家级建议）+ 脚本级明细表（有数据支持）。"""
    name = lb.get("name", "")

    # 语言标题：语言 + 【档位】（同段混合上色）
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(2)
    rn = p.add_run(name)
    rn.bold = True
    rn.font.size = Pt(12.5)
    rn.font.color.rgb = RGBColor.from_string("1F3864")
    if g and g.verdict:
        rv = p.add_run(f"　【{g.verdict}】")
        rv.bold = True
        rv.font.size = Pt(11)
        rv.font.color.rgb = RGBColor.from_string(
            _VERDICT_COLOR.get(g.verdict, "555555"))

    # 现状数据行（透明、可复核）
    facts = []
    if g:
        facts += [f"大盘 {_pct(g.ad_market_share)}", f"KOL消耗 {_pct(g.kol_spend_share)}",
                  f"产出 {_pct(g.publish_share)}", f"跑出 {_pct(g.breakout_rate)}"]
    if lm:
        facts += [f"均ROI7 {_pct(lm.avg_roi7)}", f"{lm.count}条"]
    if facts:
        _body(doc, "现状：" + " · ".join(facts), size=9, color="555555")

    # 语言级（国家级）建议
    todo = lb.get("todo") or lb.get("one_liner") or ""
    if todo:
        pp = doc.add_paragraph()
        pp.paragraph_format.space_after = Pt(3)
        rr = pp.add_run("国家级建议：")
        rr.bold = True
        rr.font.size = Pt(9.5)
        rr.font.color.rgb = RGBColor.from_string("2F5496")
        for i, line in enumerate(str(todo).split("\n")):
            if i:
                pp = doc.add_paragraph()
                pp.paragraph_format.space_after = Pt(1)
            tr = pp.add_run(line)
            tr.font.size = Pt(9.5)

    # 脚本级明细表：每条素材（同红人·玩法合并）的数据 + 脚本级建议
    rows = _merge_scripts(lm.creatives) if lm else []
    if rows:
        tb, w = _mk_table(
            doc, ["红人 · 玩法", "消耗", "ROI7", "转化", "平台", "脚本级建议"],
            [Pt(150), Pt(50), Pt(46), Pt(40), Pt(44), Pt(170)])
        for idx, m in enumerate(rows[:8]):
            cells = tb.add_row().cells
            _multiline(cells[0], m["label"], bold_first=True, size=8.5)
            _multiline(cells[1], f"{m['spend']:.0f}", size=8.5)
            _multiline(cells[2],
                       _pct(m["roi7"] * 100) if m["roi7"] is not None else "—", size=8.5)
            _multiline(cells[3], f"{m['conv']:.0f}" if m["conv"] else "—", size=8.5)
            _multiline(cells[4], m["platform"] or "—", size=8.5)
            tier_cn, advice = _script_advice(m["tier"], m["conv"], m["share"])
            _multiline(cells[5], f"【{tier_cn}】{advice}", size=8.5,
                       color=_TIER_COLOR.get(tier_cn, "555555"))
            if idx % 2 == 1:
                for cc in cells:
                    _shade(cc, _ALT_BG)
        _apply_widths(tb, w)
        if len(rows) > 8:
            _body(doc, f"（共 {len(rows)} 个脚本，上表列消耗前 8）",
                  size=8, color="999999")


# 脚本层档位 -> 颜色
_SVERDICT_COLOR = {"加发布": "2E7D32", "微调": "555555",
                   "提质不提量": "C62828", "收缩": "C62828", "收缩/量极小": "999999"}


def _eff_str(e):
    return f"{e:.2f}" if e is not None else "—"


def _stat_table(doc, stats, has_pub, top=None):
    """渲染一张脚本层表（全盘或某地区）。"""
    if has_pub:
        headers = ["脚本", "条数", "发布占比", "消耗占比", "效率比", "跑出率", "档位建议"]
        widths = [Pt(110), Pt(40), Pt(56), Pt(56), Pt(46), Pt(48), Pt(78)]
    else:
        headers = ["脚本", "条数", "条数占比", "消耗占比", "效率比", "跑出率", "档位建议"]
        widths = [Pt(120), Pt(42), Pt(56), Pt(56), Pt(46), Pt(48), Pt(78)]
    tb, w = _mk_table(doc, headers, widths)
    for idx, s in enumerate(stats if top is None else stats[:top]):
        cells = tb.add_row().cells
        _multiline(cells[0], s.name, bold_first=True, size=8.5)
        _multiline(cells[1], str(s.n), size=8.5)
        _multiline(cells[2],
                   f"{s.publish_share:.1f}%" if has_pub else f"{s.count_share:.1f}%",
                   size=8.5)
        _multiline(cells[3], f"{s.spend_share:.1f}%", size=8.5)
        _multiline(cells[4], _eff_str(s.eff), size=8.5)
        _multiline(cells[5], f"{s.breakout:.0f}%", size=8.5)
        _multiline(cells[6], s.verdict, size=8.5,
                   color=_SVERDICT_COLOR.get(s.verdict, "555555"))
        if idx % 2 == 1:
            for cc in cells:
                _shade(cc, _ALT_BG)
    _apply_widths(tb, w)


def _render_scripts(doc, data, sa: ScriptAnalysis):
    _heading(doc, "三、脚本维度分析（内容脚本 × 效率比）", 15, before=14)
    rv = getattr(sa, "review", None)
    if not rv or not rv.overall:
        _body(doc, "本期无可识别的脚本明细。", size=9.5, color="777777")
        return

    base = "发布占比" if rv.has_publish else "条数占比"
    _body(doc,
          f"口径：脚本=内容母题（口播/mv/街采是形式、图生/文生是方法，均不计脚本）；"
          f"跑出=ROI0>0；效率比=消耗占比÷{base}，>1.2 该加发布、<0.6 提质不提量。",
          size=9, color="555555")

    # 3.1 脚本层（全盘）
    _heading(doc, "3.1 脚本层 · 全盘（该加发布 / 提质 / 收缩）", 11.5,
             color="2F5496", before=8)
    _stat_table(doc, rv.overall, rv.has_publish)

    # 3.2 跨盘警示
    if rv.warnings:
        _heading(doc, "3.2 跨盘警示（同脚本两极分化，禁止照搬）", 11.5,
                 color="2F5496", before=8)
        for wn in rv.warnings:
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(wn.detail)
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor.from_string("C62828")

    # 3.3 AI热歌内部（功能录屏 vs 普通自制热歌）
    if rv.ai_split:
        _heading(doc, "3.3 AI热歌内部 · 功能录屏 vs 普通自制热歌", 11.5,
                 color="2F5496", before=8)
        tb, w = _mk_table(doc, ["盘", "功能录屏(条)", "录屏跑出", "普通热歌(条)", "普通跑出"],
                          [Pt(90), Pt(80), Pt(60), Pt(80), Pt(60)])
        for a in rv.ai_split:
            cells = tb.add_row().cells
            _multiline(cells[0], a.region, bold_first=True, size=9)
            _multiline(cells[1], str(a.demo_n), size=9)
            _multiline(cells[2], f"{a.demo_run:.0f}%" if a.demo_run is not None else "—",
                       size=9)
            _multiline(cells[3], str(a.normal_n), size=9)
            _multiline(cells[4],
                       f"{a.normal_run:.0f}%" if a.normal_run is not None else "—", size=9)
        _apply_widths(tb, w)
        _body(doc, "注：功能录屏与普通自制热歌跑出率跨盘常两极（如 TR 录屏更强），别跨盘照搬。",
              size=8.5, color="999999")

    # 3.4 各地区脚本明细（消耗前几）
    if rv.regions:
        _heading(doc, "3.4 各盘脚本明细（消耗前 6）", 11.5, color="2F5496", before=8)
        for reg in rv.regions:
            if not reg.scripts:
                continue
            _body(doc, f"{reg.region}（{reg.n} 条 · 消耗 {reg.spend:.0f}）",
                  size=9.5, color="1F3864")
            _stat_table(doc, reg.scripts, False, top=6)


def render(data: dict, analysis: Analysis, scripts: ScriptAnalysis, out_path) -> Path:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    style.font.size = Pt(10)

    # 标题
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(data.get("title", "月度 KOL 广告复盘"))
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor.from_string("1F3864")
    per = doc.add_paragraph()
    per.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pr = per.add_run(data.get("period", ""))
    pr.font.size = Pt(13)
    pr.font.color.rgb = RGBColor.from_string("2F5496")

    m = analysis.market

    # ---- 一、广告部份 ----
    _heading(doc, "一、广告部份", 15)
    ad = data.get("ad_section", {})
    _body(doc, ad.get("overview", ""))
    if ad.get("caveat"):
        _heading(doc, "口径提醒", 10.5, color="C00000", before=6)
        _body(doc, ad["caveat"], size=9.5, color="C00000")

    if m.ad_country_share:
        _heading(doc, "广告大盘 · 分国家消耗（设计+KOL）", 11, color="2F5496", before=8)
        tb, w = _mk_table(doc, ["国家", "消耗", "占比"], [Pt(120), Pt(90), Pt(70)])
        for c, p in sorted(m.ad_country_share.items(), key=lambda x: -(x[1] or 0))[:15]:
            cells = tb.add_row().cells
            _multiline(cells[0], c, size=9)
            _multiline(cells[1], f"{m.ad_country_spend.get(c, '')}", size=9)
            _multiline(cells[2], f"{p:.2f}%", size=9)
        _apply_widths(tb, w)

    if m.kol_share_of_total is not None:
        _body(doc, f"设计师 vs KOL：KOL 占整体约 {m.kol_share_of_total:.2f}%。", size=10)

    # ---- 二、KOL 分语言素材分析（核心；档位/缺口已并入本表）----
    _heading(doc, "二、KOL 分语言素材分析", 15, before=14)
    if data.get("gap_summary"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run("一句话总结：")
        run.bold = True
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor.from_string("C00000")
        run2 = p.add_run(data["gap_summary"])
        run2.font.size = Pt(10.5)

    gap_by = {g.name: g for g in analysis.gaps}
    lm_by = {l.name: l for l in analysis.langs}
    for lb in data.get("langs", []):
        name = lb.get("name", "")
        _lang_detail(doc, lb, gap_by.get(name), lm_by.get(name))

    # ---- 三、脚本/形式洞察 ----
    _render_scripts(doc, data, scripts)

    # ---- 四、人力分工与调整建议 ----
    staff = data.get("staffing_section") or {}
    if staff.get("overview") or staff.get("people"):
        _heading(doc, "四、人力分工与调整建议", 15, before=14)
        if staff.get("overview"):
            _body(doc, staff["overview"])
        ppl = staff.get("people") or []
        if ppl:
            tb, w = _mk_table(doc, ["负责人", "调整建议"], [Pt(70), Pt(360)])
            for i, pr in enumerate(ppl):
                cells = tb.add_row().cells
                _multiline(cells[0], pr.get("person", ""), bold_first=True, size=9.5)
                _multiline(cells[1], pr.get("suggestion", ""), size=9.5)
                if i % 2 == 1:
                    for c in cells:
                        _shade(c, _ALT_BG)
            _apply_widths(tb, w)

    foot = doc.add_paragraph()
    foot.paragraph_format.space_before = Pt(12)
    fr = foot.add_run("本报告由 KOL 复盘分析工具自动生成，请结合业务判断复核。")
    fr.italic = True
    fr.font.size = Pt(8)
    fr.font.color.rgb = RGBColor.from_string("808080")

    out = Path(out_path)
    doc.save(out)
    return out
