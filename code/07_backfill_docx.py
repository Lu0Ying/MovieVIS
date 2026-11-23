# -*- coding: utf-8 -*-
"""把作业1 docx 中的待回填表格、示意图与叙述替换为实测结果。

输入：outputs/第X组-作业1-....docx（已生成的占位版）
      work/processed/*.csv / *.json，work/figures/real_*.png，work/screenshots/*.png
输出：同名 docx（原地更新），备份为 *_占位版.docx
"""

import json
import os
import re

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
OUT = os.path.join(BASE, "outputs")
DOCX = os.path.join(OUT, "第X组-作业1-电影评论可视化-组长姓名(学号)-组员B(学号)-组员C(学号)-组员D(学号).docx")
PROC = os.path.join(BASE, "work", "processed")
FIG = os.path.join(BASE, "work", "figures")
SHOT = os.path.join(BASE, "work", "screenshots")

with open(os.path.join(PROC, "stats.json"), encoding="utf-8") as f:
    ST = json.load(f)
with open(os.path.join(PROC, "filter_summary.json"), encoding="utf-8") as f:
    FS = json.load(f)
with open(os.path.join(PROC, "stats_extra.json"), encoding="utf-8") as f:
    EX = json.load(f)


def set_run_font(run, size=12, bold=False, color=(0x22, 0x22, 0x22)):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = "宋体"
    run.font.color.rgb = docx.shared.RGBColor(*color)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def set_para_text(p, text):
    if not p.runs:
        r = p.add_run(text)
        set_run_font(r)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)


DOCG = None


def find_para(prefix):
    for p in DOCG.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    raise KeyError(prefix)


def replace_prefix(prefix, text):
    p = find_para(prefix)
    set_para_text(p, text)


def cell_set(cell, text):
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = str(text)
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        r = p.add_run(str(text))
        set_run_font(r, 9.2)


def row_by_label(tb, label):
    for r in tb.rows:
        if r.cells[0].text.strip() == label:
            return r
    raise KeyError(f"{label} not in table")


def fill_table(tb, values):
    for label, col, text in values:
        r = row_by_label(tb, label)
        cell_set(r.cells[col], text)


def main():
    global DOCG
    doc = docx.Document(DOCX)
    DOCG = doc
    doc.save(DOCX.replace(".docx", "_占位版.docx"))

    # 1) 图号后移：旧 2—8 → 新 3—9
    pat = re.compile(r"图\s*([2-8])")
    for p in doc.paragraphs:
        if pat.search(p.text):
            set_para_text(p, pat.sub(lambda m: f"图 {int(m.group(1)) + 1}", p.text))

    # 2) 替换 8 张图（保持原宽度，按新图比例更新高度）
    imgs = [
        os.path.join(FIG, "fig_data_flow.png"),
        os.path.join(FIG, "real_scatter.png"),
        os.path.join(FIG, "fig_filter_funnel.png"),
        os.path.join(FIG, "fig_classification_flow.png"),
        os.path.join(FIG, "real_matrix.png"),
        os.path.join(FIG, "real_radar.png"),
        os.path.join(FIG, "real_sankey.png"),
        os.path.join(FIG, "real_linked.png"),
    ]
    for i, path in enumerate(imgs):
        shp = doc.inline_shapes[i]
        rid = shp._inline.graphic.graphicData.pic.blipFill.blip.embed
        part = doc.part.related_parts[rid]
        part._blob = open(path, "rb").read()
        w = shp.width.cm
        iw, ih = Image.open(path).size
        shp.width = Cm(w)
        shp.height = Cm(w * ih / iw)

    # 3) 插入两张执行记录截图
    def insert_figure(anchor, path, caption, width=14.2):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(8)
        p.add_run().add_picture(path, width=Cm(width))
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = c.add_run(caption)
        set_run_font(r, 10.5, False, (0x55, 0x55, 0x55))
        c.paragraph_format.space_after = Pt(10)
        anchor._p.addprevious(p._p)
        anchor._p.addprevious(c._p)

    insert_figure(find_para("1.3.2 合规与隐私"),
                  os.path.join(SHOT, "s2_download_check.png"),
                  "图 2 下载与校验脚本实测输出（2026-11-23）")
    insert_figure(find_para("表 21"),
                  os.path.join(SHOT, "s3_filter.png"),
                  "图 10 过滤漏斗脚本实测输出（2026-11-23）")

    # 4) 图注改为真实数据
    replace_prefix("图 1 数据获取与落盘流程",
                   "图 1 数据获取与落盘流程（流程示意，数字为实测值）")
    replace_prefix("图 3 口碑—争议散点气泡图",
                   "图 3 口碑—争议散点气泡图（真实数据：DMSC v2，28 部）")
    replace_prefix("图 4 数据过滤漏斗",
                   "图 4 数据过滤漏斗（全量实测，N0—N5）")
    replace_prefix("图 5 评论分类与聚合流程",
                   "图 5 评论分类与聚合流程（已运行，数字为实测）")
    replace_prefix("图 6 电影 × 类别气泡矩阵",
                   "图 6 电影 × 类别气泡矩阵（真实数据）")
    replace_prefix("图 7 六维画像雷达",
                   "图 7 六维画像雷达（《栀子花开》vs 全库，真实数据）")
    replace_prefix("图 8 类别 → 情感桑基图",
                   "图 8 类别 → 情感桑基图（真实数据）")
    replace_prefix("图 9 散点导航与矩阵联动",
                   "图 9 散点导航与矩阵联动（真实数据渲染）")

    # 5) 表 3 / 5 / 6
    t3 = doc.tables[2]
    fill_table(t3, [
        ("影评语料总量", 1, "2,125,056 条 / 28 部（实测）"),
        ("影评语料总量", 2, "DMSC.csv 实际行数；2026-11-23 下载"),
        ("电影元数据", 1, "2,065 部 / 2.12 MB（实测）"),
        ("电影元数据", 2, "douban_all_movies.csv；关联 28/28"),
        ("分析抽样", 1, "19,954 条（实测）"),
        ("分析抽样", 2, "按电影 × 星级分层抽样"),
        ("电影级聚合表", 1, "28 行（实测）"),
        ("电影级聚合表", 2, "movie_agg.csv"),
        ("类别级聚合表", 1, "252 行（28×9，实测）"),
        ("类别级聚合表", 2, "category_agg.csv"),
    ])

    t5 = doc.tables[4]
    fill_table(t5, [
        ("DMSC.csv 行数", 2, "2,125,056"),
        ("电影数", 2, "28"),
        ("字段数", 2, "10"),
        ("元数据行数", 2, "2,065"),
        ("元数据关联覆盖率", 2, "100%（28/28）"),
        ("DMSC.csv 文件大小", 2, "405.61 MB"),
    ])
    replace_prefix("表 5 下载与校验记录", "表 5 下载与校验记录（实测）")

    t6 = doc.tables[5]
    r = row_by_label(t6, "DMSC v2")
    cell_set(r.cells[5], "已下载")
    r2 = row_by_label(t6, "豆瓣电影元数据")
    cell_set(r2.cells[5], "已下载")

    # 6) 表 8 质量检查
    t8 = doc.tables[7]
    fill_table(t8, [
        ("星级缺失/异常", 3, "0（0.00%）"),
        ("日期解析", 3, "0（0.00%）"),
        ("完全重复", 3, "165,837（7.80%）"),
        ("近似重复", 3, "51,263（2.41%）"),
        ("非中文", 3, "72,123（3.39%）"),
        ("广告/水印", 3, "2,531（0.12%）"),
        ("短文本", 3, f"61,206（2.88%）"),
        ("每片评论数", 3, "23,739 / 79,121 / 137,511"),
        ("元数据关联", 3, "28/28（100%）"),
    ])
    replace_prefix("表 8 数据质量检查清单", "表 8 数据质量检查清单（实测）")
    replace_prefix("表 3 数据规模核算", "表 3 数据规模核算（公开说明值 + 实测值）")

    # 7) 表 11 漏斗
    t11 = doc.tables[10]
    vals = [
        ("原始", "2,125,056", "—", "—", "已实测"),
        ("完全/近似去重", "1,907,956", "217,100", "重复、模板", "已实测"),
        ("去广告/水印", "1,902,920", "5,036", "引流、联系方式", "已实测"),
        ("语言/长度", "1,854,090", "48,830", "非中文、无信息短文本", "已实测"),
        ("相关性", "1,847,982", "6,108", "想看、模板、无关", "已实测"),
        ("最终可用", "1,829,442", "18,540", "兜底清理", "保留率 86.09%"),
    ]
    for label, n, d, why, status in vals:
        r = row_by_label(t11, label)
        cell_set(r.cells[1], n)
        cell_set(r.cells[2], d)
        if label != "原始":
            cell_set(r.cells[3], why)
        cell_set(r.cells[4], status)
    replace_prefix("表 11 过滤漏斗统计", "表 11 过滤漏斗统计（实测）")

    # 8) 表 17 / 20
    t17 = doc.tables[16]
    r = row_by_label(t17, "L0")
    cell_set(r.cells[4], "规则覆盖 63.25%（非 C8）；F1 待 gold 后评估")
    r = row_by_label(t17, "L1")
    cell_set(r.cells[4], "待 300 条 gold 标注；尚未运行")

    t20 = doc.tables[19]
    mapping = [
        ("comments_clean.parquet", "filtered.csv.gz", "过滤后评论（1,829,442 行）", "已生成"),
        ("comments_flagged.parquet", "filter_arrays.npz", "标记位与去重数组", "已生成"),
        ("comments_labeled.parquet", "sample_20k.csv", "情感、C0—C8 标签（19,954 行）", "已生成"),
        ("movie_agg.csv", "movie_agg.csv", "28 行电影级指标", "已生成"),
        ("category_agg.csv", "category_agg.csv", "252 行类别级指标", "已生成"),
        ("funnel.csv / gold_300.csv", "funnel.csv", "漏斗结果；gold 300 未标注", "部分生成"),
    ]
    for old, f, content, status in mapping:
        r = row_by_label(t20, old)
        cell_set(r.cells[0], f)
        cell_set(r.cells[1], content)
        cell_set(r.cells[2], status)

    # 9) 表 21 与第 5 章
    replace_prefix("表 21", "表 21 回填与完成情况")
    t21 = doc.tables[20]
    status = {
        "表 5": "已回填", "表 8": "已回填", "表 11": "已回填",
        "3.4.2": "未完成：需 50+50 人工抽检", "表 14": "已回填（67.90%）",
        "表 17": "规则覆盖已回填；F1 未评估", "4.4.1": "未完成：需 100 条双标",
        "表 18—20": "已回填", "图 2、5—8": "已重绘", "全文": "待替换",
    }
    for k, v in status.items():
        r = row_by_label(t21, k)
        cell_set(r.cells[3], v)
    r = row_by_label(t21, "图 2、5—8")
    cell_set(r.cells[0], "图 3、6—9")
    cell_set(r.cells[1], "真实数据重绘")

    # 10) 叙述改写
    replace_prefix("文档中的公开数据集规模",
                   "文档中的公开数据集规模来自数据源页面说明；除特别注明外，正文统计值均来自 "
                   "2026-11-23 的实际下载与脚本运行（脚本见 code/，日志与截图见 work/）。"
                   "示意图与真实数据图在标题中分别注明。")
    replace_prefix("本章完成数据需求定义",
                   "本章完成数据需求定义、数据源核实、下载与落盘。Kaggle 凭证已配置，两个数据集已于 "
                   "2026-11-23 下载完成：DMSC.csv 共 2,125,056 行、28 部电影、10 个字段，"
                   "元数据 2,065 部，关联覆盖率 28/28（100%）。")
    replace_prefix("本章回答三个问题",
                   "本章回答三个问题：数据里有什么、规模是否够、文本有什么特点与噪声。下载完成后，"
                   "字段字典、质量检查与文本特性均以实测统计为准，具体数值见各表。")
    replace_prefix("第一轮可以确认三件事",
                   "第一轮可以确认三件事：其一，数据量足够支撑 5,000 条以上的分析（实测 2,125,056 条）；"
                   "其二，维度足够覆盖“电影—评论—情感—属性”四层；其三，噪声主要来自重复（7.80%）、"
                   "非中文（3.39%）与无信息短文本（2.88%），已在第 3 章过滤。")
    p68 = find_para("2.4 数据概况图")
    set_para_text(p68, "2.4 数据概况图（真实数据）【主完成：组员B】")
    replace_prefix("下图只用于说明",
                   "下图由 28 部电影的真实聚合指标绘制：横轴平均星级、纵轴星级标准差、气泡大小为评论量、"
                   "颜色为正面率，用于在进入气泡矩阵前先看整体口碑与争议结构。")
    replace_prefix("否定词窗口取情感词前",
                   "否定式已作为复合词收入负向词典（如“不好看”“不推荐”），阈值取正负词计数差 ±1。"
                   "实测 sent_star 与 sent_text 的一致率为 67.90%（比较 988,177 条文本情感非中性样本），"
                   "高于 65% 的预设下限，因此文本情感可用于类别内相对比较。")
    replace_prefix("本节不属于前四步",
                   "本节不属于前四步的强制交付，只说明第 4 章输出如何被后续可视化使用。"
                   "以下 5 张图均由真实聚合表渲染，交互部分仍为原型设计，尚未实现为可操作界面。")
    p149 = find_para("5 第一轮小结与待回填")
    set_para_text(p149, "5 第一轮小结与完成情况【主完成：组员A】")
    replace_prefix("第一轮已完成",
                   "第一轮已完成：数据下载与校验（2,125,056 条 / 28 部 / 关联 100%）、F1—F14 过滤"
                   "（保留 1,829,442 条，86.09%）、C0—C8 分类与情感双轨、19,954 条分层抽样、"
                   "28 行电影级与 252 行类别级聚合，并按真实结果重绘散点、矩阵、雷达、桑基与联动原型。"
                   "尚未完成：300 条 gold 人工标注、L1 模型评估、误杀抽检与 kappa；"
                   "这些不影响前四步交付，完成条件列在表 21。")

    doc.save(DOCX)
    print("updated", DOCX)


if __name__ == "__main__":
    main()
