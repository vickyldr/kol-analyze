"""把分析结果渲染成 .docx，结构对齐示例复盘文档。"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from .metrics import OverallMetrics

_HEADER_BG = "2F5496"    # 深蓝表头
_ALT_BG = "F2F5FB"       # 隔行浅蓝


def _set_cell_bg(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.makeelement(qn("w:shd"), {
        qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): hex_color})
    tcPr.append(shd)


def _multiline(cell, text: str, bold_first: bool = False, size: int = 9):
    cell.text = ""
    para = cell.paragraphs[0]
    lines = [l for l in str(text).split("\n")]
    for i, line in enumerate(lines):
        if i > 0:
            para = cell.add_paragraph()
        para.paragraph_format.space_after = Pt(1)
        run = para.add_run(line)
        run.font.size = Pt(size)
        if bold_first and i == 0:
            run.bold = True


def _heading(doc, text: str, size: int, color: str = "1F3864",
             bold: bool = True, space_before: int = 10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    return p


def _body(doc, text: str, size: int = 10):
    for line in str(text).split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(line)
        r.font.size = Pt(size)


def render(data: dict, overall: OverallMetrics, out_path: str | Path) -> Path:
    doc = Document()
    # 默认中文字体
    style = doc.styles["Normal"]
    style.font.name = "微软雅黑"
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    style.font.size = Pt(10)

    # ---- 标题 ----
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

    # ---- 一、整体 ----
    _heading(doc, "一、整体", 15)
    ov = data.get("overall", {})
    _heading(doc, "1）整体广告盘", 12, color="2F5496", space_before=6)
    _body(doc, ov.get("big_picture", ""))
    _heading(doc, "2）KOL 在整体盘里的位置", 12, color="2F5496", space_before=6)
    _body(doc, ov.get("kol_position", ""))

    caveats = ov.get("caveats") or []
    if caveats:
        _heading(doc, "口径提醒", 11, color="C00000", space_before=6)
        for c in caveats:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(c).font.size = Pt(9.5)

    # ---- 跨国家整体分析 ----
    if data.get("strategy_overview"):
        _heading(doc, "跨国家整体分层", 12, color="2F5496", space_before=8)
        _body(doc, data["strategy_overview"])

    # ---- 二、KOL素材分国家分析（表格） ----
    _heading(doc, "二、KOL素材分国家分析", 15, space_before=12)

    headers = ["国家区", "相关表", "转化情况", "素材分析", "整体分析", "todo"]
    countries = data.get("countries", [])
    strategy = data.get("strategy_overview", "")
    sheet_by_name = {c.name: c.sheet_name for c in overall.countries}

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = 1
    widths = [Pt(48), Pt(90), Pt(120), Pt(120), Pt(120), Pt(110)]

    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        _set_cell_bg(hdr[i], _HEADER_BG)
        hdr[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor.from_string("FFFFFF")

    for idx, c in enumerate(countries):
        cells = table.add_row().cells
        name = c.get("name", "")
        related = sheet_by_name.get(name, "")
        one_liner = c.get("one_liner", "")
        col0 = name + (f"\n{one_liner}" if one_liner else "")
        _multiline(cells[0], col0, bold_first=True)
        _multiline(cells[1], related, size=8)
        _multiline(cells[2], c.get("conversion", ""))
        _multiline(cells[3], c.get("creative_analysis", ""))
        _multiline(cells[4], strategy)   # 整体分析：跨国家共享块，与示例一致
        _multiline(cells[5], c.get("todo", ""))
        if idx % 2 == 1:
            for cell in cells:
                _set_cell_bg(cell, _ALT_BG)

    for row in table.rows:
        for i, cell in enumerate(row.cells):
            if i < len(widths):
                cell.width = widths[i]

    # 页脚
    foot = doc.add_paragraph()
    foot.paragraph_format.space_before = Pt(12)
    fr = foot.add_run("本报告由 KOL 复盘分析工具自动生成，请结合业务判断复核。")
    fr.italic = True
    fr.font.size = Pt(8)
    fr.font.color.rgb = RGBColor.from_string("808080")

    out = Path(out_path)
    doc.save(out)
    return out
