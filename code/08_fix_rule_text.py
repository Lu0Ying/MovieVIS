# -*- coding: utf-8 -*-
"""对齐规则表与实现口径（F2/F3/F8/F14、表 8 方法、表 21 表头）。"""

import docx

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
DOCX = (BASE + r"\outputs\第X组-作业1-电影评论可视化-组长姓名(学号)-"
        r"组员B(学号)-组员C(学号)-组员D(学号).docx")


def cell_set(cell, text):
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = str(text)
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(str(text))


def row(tb, label):
    for r in tb.rows:
        if r.cells[0].text.strip() == label:
            return r
    raise KeyError(label)


def main():
    d = docx.Document(DOCX)

    t10 = d.tables[9]
    cell_set(row(t10, "F2").cells[2], "去标点/表情/数字后完全相同（SimHash 近似检索留第二轮）")
    cell_set(row(t10, "F3").cells[2], "同一用户名 + 电影 + 归一化文本相同")
    cell_set(row(t10, "F3").cells[3], "保留点赞最高一条")
    cell_set(row(t10, "F8").cells[4], "本批无触发（最长 200 字）")
    cell_set(row(t10, "F14").cells[2], "文本首 8 字符指纹在 ≥20 条评论重复")
    cell_set(row(t10, "F14").cells[3], "标记并排除")

    t14 = d.tables[13]
    cell_set(row(t14, "sent_text").cells[2], "自建正负词典计数差（否定式作复合词），±1 分档")

    t8 = d.tables[7]
    cell_set(row(t8, "近似重复").cells[1], "去标点/表情/数字后完全相同（含同用户重复）")
    cell_set(row(t8, "近似重复").cells[3], "51,263（2.41%）")

    t21 = d.tables[20]
    cell_set(t21.rows[0].cells[1], "回填项")
    t21.autofit = False
    for r in t21.rows:
        r.cells[0].width = docx.shared.Cm(3.0)
        r.cells[1].width = docx.shared.Cm(6.2)
        r.cells[2].width = docx.shared.Cm(5.4)
        r.cells[3].width = docx.shared.Cm(2.8)

    d.save(DOCX)
    print("fixed", DOCX)


if __name__ == "__main__":
    main()
