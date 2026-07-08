#!/usr/bin/env python3
"""KOL 月度广告复盘 · 自动分析工具

用法：
    # 丢后台导出的 xlsx（含 KOL素材/设计师素材/汇总统计），配大盘截图
    python analyze.py 数据.xlsx --shot 大盘1.png 设计vsKOL.png KOL分国家.png 发布分语言.png \\
        --title "26 RM月度KOL广告分析" --period "5月"

    # 大盘数据用手填 JSON（无需读图，可离线测试）
    python analyze.py 数据.xlsx --market templates/market_sample.json --offline

    # 只有 excel，不给大盘（仍能出 KOL 分语言分析，缺口分析里大盘列为空）
    python analyze.py 数据.xlsx --offline

需要 Claude 写分析/读截图时：export ANTHROPIC_API_KEY=sk-...
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from kol_analyze import (analyzer, docx_writer, engine, loader, market, memory,
                         metrics, scripts, store, vision)
from kol_analyze.config import PRODUCTS, Settings
from kol_analyze.market import MarketContext


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="丢入 KOL 素材数据（+大盘截图），自动产出月度复盘 docx。")
    ap.add_argument("input", help="后台导出 xlsx / CSV / 目录")
    ap.add_argument("-o", "--output", default=None, help="输出 docx 路径")
    ap.add_argument("--title", default="月度 KOL 广告复盘", help="报告标题")
    ap.add_argument("--period", default="", help="周期，如 5月")
    ap.add_argument("--shot", nargs="*", default=[], help="大盘截图（1~4 张）")
    ap.add_argument("--market", default=None, help="大盘数据 JSON（替代截图）")
    ap.add_argument("--memory", default=None,
                    help="命名修正记忆库 JSON（默认按产品 kol_workspace/<产品>/memory.json）")
    ap.add_argument("--product", default=next(iter(PRODUCTS)),
                    help=f"产品线 {list(PRODUCTS)}（决定记忆库/历史归档）")
    ap.add_argument("--archive", action="store_true",
                    help="把本次结果归档进历史 kol_workspace/<产品>/history")
    ap.add_argument("--model", default=None, help="覆盖模型")
    ap.add_argument("--offline", action="store_true", help="不调用 Claude，规则兜底")
    args = ap.parse_args(argv)

    inp = Path(args.input)
    if not inp.exists():
        print(f"✗ 输入不存在：{inp}", file=sys.stderr)
        return 2

    settings = Settings()
    if args.model:
        settings.model = settings.vision_model = args.model
    if args.offline:
        os.environ["KOL_FORCE_OFFLINE"] = "1"

    mem_path = args.memory or store.memory_path(args.product)
    mem = memory.load(mem_path)
    print(f"→ 产品：{args.product}（{PRODUCTS.get(args.product, args.product)}）"
          f" · 记忆库：{mem_path}（{len(mem.play_overrides)} 精确、"
          f"{len(mem.keyword_rules)} 关键词）")

    print(f"→ 读取数据：{inp}")
    ds = loader.load(inp, mem)
    if not ds.langs:
        print("✗ 没读到任何 KOL 素材行，请检查格式。", file=sys.stderr)
        return 1
    print(f"  识别到 {len(ds.langs)} 个语言：" +
          "、".join(f"{l.name}({len(l.rows)})" for l in ds.langs))

    # 大盘上下文
    mkt = MarketContext()
    if args.market:
        mkt = market.load_json(args.market)
        print(f"→ 载入大盘数据：{args.market}")
    elif args.shot:
        print(f"→ 读取 {len(args.shot)} 张大盘截图 …")
        mkt = vision.read_screenshots(args.shot, settings)
    if ds.kol_total_spend and not mkt.kol_total_spend:
        mkt.kol_total_spend = ds.kol_total_spend

    analysis = metrics.compute(ds, mkt, settings.thresholds)
    # excel 被单一语言主导时，其余语言视为「消耗数据待补全」，避免误判脚本策略
    top_share = max((l.spend_share for l in analysis.langs), default=0.0)
    incomplete = ({l.lang for l in analysis.langs if l.spend_share < 5.0}
                  if top_share >= 85.0 else set())
    script_analysis = scripts.analyze(analysis.langs, settings.thresholds, incomplete, mem)
    for n in mkt.notes:
        print("  " + n)
    print(f"  素材维度：{len(script_analysis.scripts)} 类脚本、"
          f"{len(script_analysis.migrations)} 条迁移建议、"
          f"{len(script_analysis.formats)} 类形式")

    print(f"→ 生成分析（{engine.label()}，model={settings.model}）…")
    data = analyzer.analyze(analysis, script_analysis, settings, args.title, args.period)

    out = args.output or f"{args.title}_{args.period or '复盘'}.docx"
    out = docx_writer.render(data, analysis, script_analysis, out)
    print(f"✓ 已生成复盘文档：{out}")

    if args.archive:
        from datetime import datetime
        created = datetime.now().strftime("%Y%m%d-%H%M")
        stats = {"creatives": sum(l.count for l in analysis.langs),
                 "langs": len(analysis.langs),
                 "migrations": len(script_analysis.migrations)}
        entry = store.archive(args.product, args.period or "复盘", args.title,
                              created, Path(out), data, stats)
        print(f"✓ 已归档进历史：{entry.dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
