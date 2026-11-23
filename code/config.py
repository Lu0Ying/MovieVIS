# -*- coding: utf-8 -*-
"""项目路径配置：所有脚本共用，均基于仓库根目录推导，不含本机绝对路径。

如需把数据放到别处，可用环境变量覆盖（示例）：
    set MOVIEVIS_DATA=D:\\datasets\\movievis
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = Path(os.environ.get("MOVIEVIS_DATA", ROOT / "data"))
RAW = DATA / "raw"                  # Kaggle 原始 CSV
PROCESSED = DATA / "processed"      # 过滤、抽样、聚合结果
LOGS = DATA / "logs"                # 运行日志
PREVIEW = DATA / "preview"          # 预览截图与临时产物

FIGURES = ROOT / "figures"
FIG_PLAN = FIGURES / "plan"         # 五方案示意图
FIG_DOC = FIGURES / "doc"           # 文档插图（流程、漏斗、真实图）
FIG_SHOT = FIGURES / "screenshots"  # 实测截图

DOCS = ROOT / "docs"                # 计划 md 与作业 docx
WEB = ROOT / "web"                  # 交互原型 index.html

# 中文字体（默认 Windows 自带；可用环境变量指向其他目录）
FONT_DIR = Path(os.environ.get("MOVIEVIS_FONT_DIR", r"C:\Windows\Fonts"))
FONT_CJK = str(FONT_DIR / "msyh.ttc")
FONT_CJK_BOLD = str(FONT_DIR / "msyhbd.ttc")
FONT_MONO = str(FONT_DIR / "consola.ttf")
