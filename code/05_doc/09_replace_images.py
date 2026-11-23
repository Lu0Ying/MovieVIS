# -*- coding: utf-8 -*-
"""只替换 docx 中 5 张真实数据图（保持其余内容不动）。"""

import os

import docx
from docx.shared import Cm
from PIL import Image

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from config import (ROOT, DATA, RAW, PROCESSED, LOGS, PREVIEW,
                    FIGURES, FIG_PLAN, FIG_DOC, FIG_SHOT, DOCS, WEB,
                    FONT_CJK, FONT_CJK_BOLD, FONT_MONO)
BASE = str(ROOT)
DOCX = (str(DOCS) + r"\第X组-作业1-电影评论可视化-组长姓名(学号)-"
        r"组员B(学号)-组员C(学号)-组员D(学号).docx")
FIG = str(FIG_DOC)

PAIRS = [
    (1, "real_scatter.png"),
    (4, "real_matrix.png"),
    (5, "real_radar.png"),
    (6, "real_sankey.png"),
    (7, "real_linked.png"),
]


def main():
    d = docx.Document(DOCX)
    for idx, name in PAIRS:
        path = os.path.join(FIG, name)
        shp = d.inline_shapes[idx]
        rid = shp._inline.graphic.graphicData.pic.blipFill.blip.embed
        d.part.related_parts[rid]._blob = open(path, "rb").read()
        w = shp.width.cm
        iw, ih = Image.open(path).size
        shp.width = Cm(w)
        shp.height = Cm(w * ih / iw)
        print(name, round(w, 2), "x", round(w * ih / iw, 2))
    d.save(DOCX)
    print("saved")


if __name__ == "__main__":
    main()
