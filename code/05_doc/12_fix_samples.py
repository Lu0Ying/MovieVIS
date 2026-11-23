# -*- coding: utf-8 -*-
"""把过滤样例表替换为真实语料节选，并修正一处图注误判。"""

import docx

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from config import (ROOT, DATA, RAW, PROCESSED, LOGS, PREVIEW,
                    FIGURES, FIG_PLAN, FIG_DOC, FIG_SHOT, DOCS, WEB,
                    FONT_CJK, FONT_CJK_BOLD, FONT_MONO)
BASE = str(ROOT)
DOCX = (str(DOCS) + r"\第X组-作业1-电影评论可视化-组长姓名(学号)-"
        r"组员B(学号)-组员C(学号)-组员D(学号).docx")


def cell_set(cell, text):
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = str(text)
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(str(text))


def main():
    d = docx.Document(DOCX)

    t12 = d.tables[11]
    rows = [
        ("广告外链",
         "http://2twotoo.taobao.com/ 格瓦拉电影优惠券 在这买貌似很划算",
         "删除", "命中 F4"),
        ("重复引用",
         "“喜欢就会放肆，但爱就是克制。”原文出现 144 次，另有 96 条仅差标点",
         "保留 1 条", "命中 F1/F2"),
        ("剧透",
         "“爽！我来剧透，彩蛋有灭霸～～～”",
         "保留，标记折叠", "命中 F11"),
    ]
    for i, vals in enumerate(rows):
        r = t12.rows[i + 1]
        for j, v in enumerate(vals):
            cell_set(r.cells[j], v)

    for p in d.paragraphs:
        if p.text.strip().startswith("表 12 过滤前后样例"):
            p.runs[0].text = "表 12 过滤前后样例（真实语料节选）"
            for r in p.runs[1:]:
                r._element.getparent().remove(r._element)
            break

    for p in d.paragraphs:
        if p.text.strip().startswith("课程要求数据量不少于"):
            p.runs[0].text = p.text.replace(
                "具体行数、抽样条数与聚合表行数在下载和执行后回填。",
                "具体行数、抽样条数与聚合表行数见下表，均为实测值。")
            for r in p.runs[1:]:
                r._element.getparent().remove(r._element)
            break

    for p in d.paragraphs:
        if p.text.strip().startswith("表 2 中已给出"):
            p.runs[0].text = p.text.replace("表 2 中已给出", "上表已给出", 1)
            for r in p.runs[1:]:
                r._element.getparent().remove(r._element)
            break

    d.save(DOCX)
    print("samples fixed")


if __name__ == "__main__":
    main()
