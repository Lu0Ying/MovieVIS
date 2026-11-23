# -*- coding: utf-8 -*-
"""按实际实现改写文本清洗步骤表（表 13）。"""

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

ROWS = [
    ("1", "去首尾空白与控制字符", "Comment"),
    ("2", "合并连续空白；全角标点统一（仅用于判重键）", "dup_key"),
    ("3", "超长截断 300 字（本批最长 200 字，未触发）", "Comment"),
    ("4", "URL/联系方式由 F4/F5 整条删除，不进入清洗语料", "drop_reason"),
    ("5", "统计字符数与中文字符占比", "char_len, zh_ratio"),
    ("6", "剧透、场外体验关键词标记", "is_spoiler, is_offtopic"),
    ("7", "按电影 × 星级分层抽样 19,954 条", "sample_20k.csv"),
    ("8", "输出过滤后语料", "filtered.csv.gz"),
]


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
    t = d.tables[12]
    for i, vals in enumerate(ROWS):
        r = t.rows[i + 1]
        for j, v in enumerate(vals):
            cell_set(r.cells[j], v)
    d.save(DOCX)
    print("cleaning table fixed")


if __name__ == "__main__":
    main()
