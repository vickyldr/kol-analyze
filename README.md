# KOL 月度广告复盘 · 自动分析工具

丢入按国家整理的素材数据（Excel / CSV）＋（可选）大盘截图，
自动产出一份结构对齐团队现有模板的**月度 KOL 广告复盘文档（.docx）**。

分析话术由 Claude 自动生成（结论先行、敢下判断，模仿投手复盘口吻）；
未配置 API key 时，会用内置规则兜底也能端到端跑出一份。

---

## 它做什么

```
国别素材数据(Excel/CSV) ──┐
                          ├─► 聚合&素材分档 ─► Claude 写分析 ─► 复盘 .docx
大盘截图(可选, 图片)   ──┘        (客观数字)      (主观判断)
```

产出的文档结构：

- **一、整体**
  - 1）整体广告盘（总消耗、头部国家占比、集中度结论）
  - 2）KOL 在整体盘里的位置
  - 口径提醒（如：广告消耗国家 ≠ 素材生产语言）
  - 跨国家整体分层（最值得放大 / 收着做 / 需控制投入）
- **二、KOL素材分国家分析**（表格）
  - 国家区 ｜ 相关表 ｜ 转化情况 ｜ 素材分析 ｜ 整体分析 ｜ todo

---

## 安装

```bash
pip install -r requirements.txt
```

想让 Claude 自动写分析（推荐），配置 API key：

```bash
export ANTHROPIC_API_KEY=sk-...
```

## 用法

```bash
# 最简：丢一个多 sheet 的 Excel（每个 sheet = 一个国家）
python analyze.py 你的数据.xlsx --title "26 RM月度KOL广告分析" --period "5月"

# 丢一个装着多国 CSV/Excel 的文件夹
python analyze.py 数据文件夹/ -o 5月复盘.docx

# 附带大盘截图（自动读图回填总消耗/各国占比）
python analyze.py 数据.xlsx --shot 大盘1.png 大盘2.png

# 不调用 Claude，仅用规则兜底（离线/无 key 时）
python analyze.py 数据.xlsx --offline
```

## 输入格式

每个国家一个 sheet（或一个 CSV 文件），sheet/文件名里带上国家（中文/英文/缩写都能识别，
如 `土耳其`、`TR`、`turkey`）。每行是一条素材，列名容错（见下），常用列：

| 素材名称 | 红人 | 消耗 | 发布 | ROI7 | 跑出率 | 预估净收入 | 点击率 |
|---|---|---|---|---|---|---|---|
| RM_TR_KOL_口播功能录屏介绍 | 小白牙 | 1420 | 1 | 42 | 18 | 980 | 3.1 |

- 只有 **素材名称 + 消耗** 是基本必需；其余列有则用、没有则跳过。
- 列名不必完全一致，工具会做别名匹配（`花费`→消耗、`cost`→消耗、`roi_7`→ROI7…）。
  别名表在 `kol_analyze/config.py` 里可扩展。
- ROI7 / 跑出率按百分比数字填（`42` 表示 42%）。

看一眼期望格式，直接生成示例：

```bash
python templates/make_sample.py      # 生成 templates/sample_input.xlsx
```

`examples/sample_output.docx` 就是用该示例跑出来的复盘文档。

## 大盘截图（发布/投入产出）

「发布占比 / 投入产出」等大盘数据通常在后台截图里、不在数据文件里。
用 `--shot` 传入截图，工具会用 Claude 视觉能力读成结构化数字
（总消耗、各国占比等）回填到「整体」部分。需要 `ANTHROPIC_API_KEY`。

## 可调项（`kol_analyze/config.py`）

- `Thresholds`：素材分档（强/潜力/弱）与国家分层（放大/过量/降频）的阈值口径。
- `Settings.model`：使用的模型（默认 `claude-opus-4-8`）。
- 列别名：`COLUMN_ALIASES`。

## 目录结构

```
analyze.py               # CLI 入口
kol_analyze/
  config.py              # 列别名、阈值、模型设置
  loader.py              # 读 Excel/CSV，按国家分组、列名归一化
  metrics.py             # 聚合国家级指标 + 素材分档
  vision.py              # 读大盘截图（Claude 视觉）
  prompts.py             # 分析 prompt 与输出 schema
  analyzer.py            # 调 Claude 写分析（含规则兜底）
  docx_writer.py         # 渲染成 .docx
templates/
  make_sample.py         # 生成示例输入
  sample_input.xlsx      # 示例输入
examples/
  sample_output.docx     # 示例输出
```

## 说明

- 工具只基于你给的数字与素材名做判断，不会编造不存在的素材/数据。
- 生成结果建议结合业务判断复核后再使用。
