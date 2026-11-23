# -*- coding: utf-8 -*-
"""按图注把图片替换为正确文件（修正插图后索引错位的问题）。"""

import os
import re

import docx
from docx.oxml.ns import qn
from docx.shared import Cm
from docx.shape import InlineShape
from PIL import Image

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
DOCX = (BASE + r"\outputs\第X组-作业1-电影评论可视化-组长姓名(学号)-"
        r"组员B(学号)-组员C(学号)-组员D(学号).docx")
FIG = os.path.join(BASE, "work", "figures")
SHOT = os.path.join(BASE, "work", "screenshots")

PLAN = {
    1: ("fig_data_flow.png", 14.2),
    2: ("s2_download_check.png", 14.2),
    3: ("real_scatter.png", 14.2),
    4: ("fig_filter_funnel.png", 13.2),
    5: ("fig_classification_flow.png", 14.0),
    6: ("real_matrix.png", 14.8),
    7: ("real_radar.png", 12.2),
    8: ("real_sankey.png", 14.2),
    9: ("real_linked.png", 13.4),
    10: ("s3_filter.png", 14.2),
}


def main():
    d = docx.Document(DOCX)
    paras = d.paragraphs
    done = []
    for i, p in enumerate(paras):
        blips = p._p.xpath(".//a:blip")
        if not blips:
            continue
        cap = ""
        for q in paras[i + 1:i + 3]:
            if q.text.strip().startswith("图 "):
                cap = q.text.strip()
                break
        m = re.match(r"图\s*(\d+)", cap)
        if not m:
            print("skip image without caption", i)
            continue
        num = int(m.group(1))
        name, width = PLAN[num]
        path = os.path.join(SHOT if name.startswith("s") else FIG, name)
        rid = blips[0].get(qn("r:embed"))
        d.part.related_parts[rid]._blob = open(path, "rb").read()
        inl = p._p.xpath(".//wp:inline")[0]
        shp = InlineShape(inl)
        iw, ih = Image.open(path).size
        shp.width = Cm(width)
        shp.height = Cm(width * ih / iw)
        done.append((num, name, round(width, 1), round(width * ih / iw, 2)))

    for x in done:
        print(x)
    d.save(DOCX)
    print("saved", len(done), "images")


if __name__ == "__main__":
    main()
