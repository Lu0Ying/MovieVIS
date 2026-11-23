# MovieVIS · 豆瓣电影短评可视化（作业 1）

对 DMSC v2 豆瓣电影短评数据集做“下载校验 → 过滤 → 分类聚合 → 图表 → 文档 / 交互原型”的完整小流水线，
并输出一份 Word 报告与一个可离线打开的单文件交互原型。

数据本身不入库，仓库只保留代码、图表成品、文档与原型页面。

## 目录结构

```
.
├─ code/
│  ├─ config.py              # 全部路径配置（唯一需要改的地方）
│  ├─ 01_download/           # 下载校验、元数据匹配
│  ├─ 02_filter/             # 去重、去短评、去水军等过滤
│  ├─ 03_aggregate/          # 九类规则分类、聚合、抽样、统计
│  ├─ 04_figures/            # 示意图与真实数据图
│  ├─ 05_doc/                # 生成 Word、真实值回填、词云插图、文档修补
│  └─ 06_web/                # 构建 web/index.html 交互原型
├─ data/                     # 数据目录（.gitignore，不入库）
│  ├─ raw/                   # Kaggle 原始 CSV
│  ├─ processed/             # 过滤/抽样/聚合结果
│  ├─ logs/                  # 运行日志
│  └─ preview/               # 预览截图与临时产物
├─ figures/
│  ├─ plan/                  # 五个可视化方案示意图
│  ├─ doc/                   # 文档插图（流程图、漏斗图、真实数据图）
│  └─ screenshots/           # 实际运行截图
├─ docs/                     # 两份计划 md 与作业 Word 文档
├─ web/index.html            # 单文件交互原型（双击即开，断网可用）
└─ README.md
```

## 环境依赖

- Python 3.10+（开发环境 3.14）
- `pandas`、`numpy`、`matplotlib`、`python-docx`、`jieba`、`Pillow`
- 中文字体：默认读取 `C:\Windows\Fonts`（msyh / msyhbd / consola），
  可用环境变量 `MOVIEVIS_FONT_DIR` 指向其他字体目录。

```bash
pip install pandas numpy matplotlib python-docx jieba pillow
```

## 数据从哪来

1. DMSC v2（Douban Movie Short Comments）：<https://www.kaggle.com/datasets/utmhikari/doubanmovieshortcomments>
2. 豆瓣电影元数据（用于片名、上映年份匹配），需自行下载后放入 `data/raw/`。

把原始文件放到以下位置后即可运行（文件名见各脚本头部注释）：

```
data/raw/DMSC.csv
data/raw/douban_all_movies.csv
```

数据目录可用环境变量覆盖：`MOVIEVIS_DATA=D:\path\to\data`。

## 运行顺序

```bash
python code/01_download/01_check_download.py     # 校验下载完整性
python code/01_download/01b_match_meta.py        # 片名与元数据匹配
python code/02_filter/02_filter.py               # 过滤 → filtered.csv.gz
python code/03_aggregate/03_classify_aggregate.py# 九类分类 + 聚合 + 抽样
python code/03_aggregate/06_extra_stats.py       # 补充统计
python code/04_figures/05_make_process_figs.py   # 过程图（真实数字）
python code/04_figures/04_make_real_figures.py   # 真实数据图
python code/06_web/14_build_prototype.py         # 生成 web/index.html
```

文档相关（生成与回填，一般只需跑一次）：

```bash
python code/05_doc/make_docx.py            # 生成 Word 骨架（docs/）
python code/05_doc/07_backfill_docx.py     # 用真实聚合值回填正文与表格
python code/05_doc/15_wordcloud_doc.py     # 生成词云图并插入 4.6.4 小节
```

## 各脚本产出

| 脚本 | 产出 |
| --- | --- |
| `01_check_download.py` | `data/processed/download_stats.json`、`data/logs/04_download_check.txt` |
| `01b_match_meta.py` | 片名匹配表（`data/processed/`） |
| `02_filter.py` | `data/processed/funnel.csv`、`filtered.csv.gz`、`filter_arrays.npz` |
| `03_classify_aggregate.py` | `movie_agg.csv`、`category_agg.csv`、`sample_20k.csv`、`stats.json`、`filter_summary.json` |
| `06_extra_stats.py` | 评论文本与星级分布补充统计 |
| `05_make_process_figs.py` | `figures/doc/` 下的流程、漏斗、分类聚合图 |
| `04_make_real_figures.py` | `figures/doc/real_*.png` 真实数据图 |
| `14_build_prototype.py` | `web/index.html`（内嵌全部聚合数据，约 400 KB） |
| `make_docx.py` / `07_backfill_docx.py` | `docs/` 下的作业 Word 文档 |
| `15_wordcloud_doc.py` | `data/preview/wc_figure.png` + Word 4.6.4 词云小节 |

## 交互原型说明

`web/index.html` 为单文件页面，内嵌 28 部电影、252 个电影×类别单元、99 条评论摘要与词频数据：

- 顶部散点：按平均星级 / 标准差定位，四象限用中位数切分；
- 电影×类别气泡矩阵：类别开关即列筛选，点击气泡查看详情；
- 六维雷达：最多叠加 3 部影片，与全库加权均值对照，附分值与差值表；
- 类别→情感桑基：支持“全库 / 当前影片”切换；
- 词云：跟随影片 × 类别联动，基于 19,954 条分层抽样词频。

## 说明

- `docs/` 中的 Word 是提交用定稿快照，图片中的目录文字以当时版本为准；
  重新运行流水线可得到与当前仓库结构一致的新图。
- `data/` 已在 `.gitignore` 中排除；超过 50 MB 的文件不入库。
