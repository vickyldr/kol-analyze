#!/usr/bin/env python3
"""KOL 月度广告复盘 · 自动分析工具

用法：
    python analyze.py 数据.xlsx                       # 最简：丢一个多 sheet 的 Excel
    python analyze.py 数据文件夹/ -o 5月复盘.docx      # 丢一个装着多国 CSV/Excel 的文件夹
    python analyze.py 数据.xlsx --shot 大盘1.png 大盘2.png   # 附带大盘截图
    python analyze.py 数据.xlsx --title "26 RM月度KOL广告分析" --period "5月"
    python analyze.py 数据.xlsx --offline             # 不调用 Claude，用规则兜底

需要 Claude 自动写分析时，先设置：
    export ANTHROPIC_API_KEY=sk-...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kol_analyze import analyzer, docx_writer, loader, metrics, vision
from kol_analyze.config import Settings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="丢入按国家整理的素材数据，自动产出月度 KOL 广告复盘 docx。")
    ap.add_argument("input", help="输入：多 sheet 的 Excel / CSV / 装着多国文件的文件夹")
    ap.add_argument("-o", "--output", default=None, help="输出 docx 路径")
    ap.add_argument("--title", default="月度 KOL 广告复盘", help="报告标题")
    ap.add_argument("--period", default="", help="报告周期，如 5月")
    ap.add_argument("--shot", nargs="*", default=[], help="大盘截图（可多张）")
    ap.add_argument("--model", default=None, help="覆盖使用的模型")
    ap.add_argument("--offline", action="store_true",
                    help="不调用 Claude，仅用规则兜底生成")
    args = ap.parse_args(argv)

    inp = Path(args.input)
    if not inp.exists():
        print(f"✗ 输入不存在：{inp}", file=sys.stderr)
        return 2

    settings = Settings()
    if args.model:
        settings.model = args.model
        settings.vision_model = args.model
    if args.offline:
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)

    print(f"→ 读取数据：{inp}")
    countries = loader.load(inp)
    if not countries:
        print("✗ 没有从输入里读到任何素材行，请检查列名/格式。", file=sys.stderr)
        return 1
    print(f"  识别到 {len(countries)} 个国家/区：{'、'.join(c.name for c in countries)}")

    overall = metrics.compute(countries, settings.thresholds)

    if args.shot:
        print(f"→ 读取 {len(args.shot)} 张大盘截图 …")
        overall = vision.enrich_from_screenshots(overall, args.shot, settings)

    import os
    mode = "Claude" if os.environ.get("ANTHROPIC_API_KEY") else "规则兜底(offline)"
    print(f"→ 生成分析（{mode}，model={settings.model}）…")
    data = analyzer.analyze(overall, settings, args.title, args.period)

    out = args.output or f"{args.title}_{args.period or '复盘'}.docx"
    out = docx_writer.render(data, overall, out)
    print(f"✓ 已生成复盘文档：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
