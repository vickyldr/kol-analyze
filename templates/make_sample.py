#!/usr/bin/env python3
"""生成一个「后台标准导出」风格的示例 xlsx（合成数据，非真实）。

用于演示期望的输入格式：
- `KOL素材` sheet：每行一条广告，关键列 ad_name / 设计师orKOL / 投放花费（爬虫）/
  ROI7（归因）/ 安装7日内试用&付费设备数 …
- 国家/语言、红人、玩法 都从 ad_name（RM_<语言>_KOL_<红人>_<日期>_<玩法>）解析。
真实使用时直接丢你后台导出的那份 xlsx 即可，无需整理成这个。
"""

from pathlib import Path

import pandas as pd

COLS = ["media_source", "ad_name", "设计师orKOL",
        "投放花费（爬虫）", "ROI7（归因）", "安装7日内试用&付费设备数", "点击率(全部)(爬虫)"]

# (ad_name, 消耗, ROI7小数, 7日转化设备)
KOL = [
    ("RM_TR_KOL_凝视哥_20260212_图生音乐混合功能_口播功能录屏介绍", 5296, 0.52, 201),
    ("RM_TR_KOL_凝视哥_20260212_图生音乐混合功能_口播功能录屏介绍_btta_260429", 4643, 0.48, 135),
    ("RM_TR_KOL_电子哥_20260506_文生音乐_自制AI热歌_btta", 1046, 0.79, 31),
    ("RM_TR_KOL_大胡子哥_20260428_文生音乐_拉踩Gb", 619, 2.99, 29),
    ("RM_TR_KOL_俯视哥_20260309_AImv_街采AImv", 632, 1.10, 23),
    ("RM_TR_KOL_鹅蛋哥_20260507_文生音乐_拉踩suno", 300, 0.08, 2),
    ("RM_SP_KOL_提子哥_20260421_AImv_海边开车拍照街采", 640, 0.35, 12),
    ("RM_SP_KOL_无袖哥_20260520_AImv_拍照街采海边弹琴", 420, 0.22, 6),
    ("RM_BR_KOL_joao_20260510_AImv_街采海边弹琴", 380, 0.26, 8),
    ("RM_BR_KOL_pedro_20260512_文生音乐_口播自制AI热歌", 260, 0.11, 3),
    ("RM_US_KOL_大白牙哥_20260108_文生音乐_拉踩街采", 90, 0.31, 4),
    ("RM_IT_KOL_marco_20260415_AImv_海边街采意语", 120, 0.16, 2),
    ("RM_AR_KOL_omar_20260518_AImv_街采海边高潜", 172, 0.73, 6),
    ("RM_TW_KOL_阿明_20260420_AImv_老脚本海边街采", 80, 0.30, 1),
]


def build(out: str = "templates/sample_input.xlsx") -> Path:
    out_p = Path(out)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    rows = [["FBad", n, "KOL", s, r, c, 0.03] for n, s, r, c in KOL]
    kol_df = pd.DataFrame(rows, columns=COLS)

    total_spend = sum(x[1] for x in KOL)
    summary = pd.DataFrame([
        ["所有", "整体", 1536, 120, 0.078, total_spend + 9313],
        ["所有", "设计师", 1177, 65, 0.055, 9313],
        ["所有", "KOL", len(KOL), sum(1 for x in KOL if x[3] > 0), 0.143, total_spend],
    ], columns=["渠道", "分组", "总广告条数", "有转化广告条数", "跑出率", "总消耗"])

    with pd.ExcelWriter(out_p, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="汇总统计", index=False)
        kol_df.to_excel(w, sheet_name="KOL素材", index=False)
    return out_p


if __name__ == "__main__":
    p = build()
    print(f"✓ 已生成示例输入：{p}")
