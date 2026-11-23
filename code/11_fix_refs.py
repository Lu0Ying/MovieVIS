# -*- coding: utf-8 -*-
"""修正正文中与实际脚本/输出不一致的表述。"""

import docx

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
DOCX = (BASE + r"\outputs\第X组-作业1-电影评论可视化-组长姓名(学号)-"
        r"组员B(学号)-组员C(学号)-组员D(学号).docx")


def set_para(p, text):
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)


def replace_prefix(d, prefix, text):
    for p in d.paragraphs:
        if p.text.strip().startswith(prefix):
            set_para(p, text)
            return
    raise KeyError(prefix)


def row(tb, label):
    for r in tb.rows:
        if r.cells[0].text.strip() == label:
            return r
    raise KeyError(label)


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
    replace_prefix(
        d, "正则、阈值与判定函数集中在",
        "正则、阈值与判定逻辑集中在 code/02_filter.py；输出 work/processed/filtered.csv.gz "
        "与 filter_arrays.npz，保留 Comment、is_spoiler、is_offtopic 等字段，便于复核。")
    replace_prefix(
        d, "示例正则（起步版",
        "示例正则（已在全量语料上运行）：URL、微信号、QQ、加群/资源/公众号、邮箱、手机号；"
        "剧透词包括“剧透、凶手就是、结局是、最后死、反转是”。")
    replace_prefix(
        d, "回填条件：运行 03_filter.py",
        "回填条件：运行 02_filter.py 生成 funnel.csv；各阶段数量必须可加总，差额为 0。")
    replace_prefix(
        d, "使用 jieba，并加载自定义词典",
        "使用 jieba 对 19,954 条抽样分词，过滤单字、片名与自定义停用词；"
        "未加载领域自定义词典，词表仅用于展示各类高频词，不参与分类决策。")
    replace_prefix(
        d, "本章把“能用于分析的评论”",
        "本章把“能用于分析的评论”从原始数据中筛出来。原则是先保真、再保量：宁可少几百条，"
        "也不让广告和模板文本进入词云；每条被删评论按阶段记录原因，漏斗各阶段可加总，便于复核。")

    t19 = d.tables[18]
    cell_set(row(t19, "top_words").cells[2], "该类别高频词 Top 12（19,954 条抽样）")

    t21 = d.tables[20]
    cond = {
        "表 5": "已完成：01_check_download.py",
        "表 8": "已完成：01_check_download.py",
        "表 11": "已完成：02_filter.py",
        "表 18—20": "已完成：03_classify_aggregate.py",
    }
    for k, v in cond.items():
        cell_set(row(t21, k).cells[2], v)

    d.save(DOCX)
    print("fixed refs")


if __name__ == "__main__":
    main()
