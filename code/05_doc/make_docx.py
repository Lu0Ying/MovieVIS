# -*- coding: utf-8 -*-
"""生成作业1 Word 文档（电影评论可视化）。"""

import os
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from config import (ROOT, DATA, RAW, PROCESSED, LOGS, PREVIEW,
                    FIGURES, FIG_PLAN, FIG_DOC, FIG_SHOT, DOCS, WEB,
                    FONT_CJK, FONT_CJK_BOLD, FONT_MONO)
BASE = str(ROOT)
OUT_DIR = str(DOCS)
WORK_FIG = str(FIG_DOC)
OUT_FIG = str(FIG_PLAN)
DOCX = os.path.join(
    OUT_DIR,
    "第X组-作业1-电影评论可视化-组长姓名(学号)-组员B(学号)-组员C(学号)-组员D(学号).docx",
)

INK = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x55, 0x55, 0x55)
ACCENT = RGBColor(0x8A, 0x4B, 0x08)

# 图片路径
FIG_FLOW = os.path.join(WORK_FIG, "fig_data_flow.png")
FIG_SCATTER = os.path.join(OUT_FIG, "01_方案一_口碑争议散点气泡.png")
FIG_FUNNEL = os.path.join(WORK_FIG, "fig_filter_funnel.png")
FIG_CLASS = os.path.join(WORK_FIG, "fig_classification_flow.png")
FIG_MATRIX = os.path.join(OUT_FIG, "02_方案二_电影类别气泡矩阵.png")
FIG_RADAR = os.path.join(OUT_FIG, "03_方案三_六维画像雷达.png")
FIG_SANKEY = os.path.join(OUT_FIG, "04_方案四_类别情感桑基图.png")
FIG_LINKED = os.path.join(OUT_FIG, "05_方案五_散点导航与矩阵联动.png")


def set_run_font(run, name="宋体", size=12, bold=False, color=INK):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = color


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    trPr.append(el)


def add_table(doc, headers, rows, widths=None, font_size=9.2):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    hdr = table.rows[0]
    for i, text in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.keep_with_next = True
        r = p.add_run(str(text))
        set_run_font(r, "宋体", font_size, True)
        shade_cell(cell, "D9E2F3")
    repeat_header(hdr)
    cant_split(hdr)

    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(val))
            set_run_font(r, "宋体", font_size, False)
            if i == 0:
                r.bold = True
        cant_split(table.rows[-1])

    if widths:
        table.autofit = False
        total = sum(widths)
        scale = 14.8 / total if total > 14.8 else 1.0
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w * scale)
    return table


def add_caption(doc, text, kind="图"):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = (kind == "表")
    r = p.add_run(text)
    set_run_font(r, "宋体", 10.5, False, MUTED)


def add_figure(doc, path, caption, width_cm=14.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    add_caption(doc, caption)


def add_h(doc, text, level, owner):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.25
    r = p.add_run(text)
    size = 16 if level == 1 else 14 if level == 2 else 12
    set_run_font(r, "黑体", size, True, INK)
    r2 = p.add_run(f"【主完成：{owner}】")
    set_run_font(r2, "宋体", 10.5, False, MUTED)


def P(doc, text, indent=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.5
    pf.space_after = Pt(4)
    if indent:
        pf.first_line_indent = Pt(24)
    r = p.add_run(text)
    set_run_font(r, "宋体", 12, False, INK)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.first_line_indent = Pt(0)
    r = p.add_run(text)
    set_run_font(r, "宋体", 12, False, INK)


def num(doc, text):
    p = doc.add_paragraph(style="List Number")
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.first_line_indent = Pt(0)
    r = p.add_run(text)
    set_run_font(r, "宋体", 12, False, INK)


def small_note(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    set_run_font(r, "宋体", 9.5, False, MUTED)


def add_page_field(paragraph):
    run = paragraph.add_run()
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)


def build():
    doc = Document()

    # ---------- 页面与样式 ----------
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    for i in (1, 2, 3):
        st = doc.styles[f"Heading {i}"]
        st.font.name = "黑体"
        st._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    # 页眉页脚
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = hp.add_run("电影评论可视化 · 作业1")
    set_run_font(r, "宋体", 9, False, MUTED)

    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = fp.add_run("第 ")
    set_run_font(r1, "宋体", 9, False, MUTED)
    add_page_field(fp)
    r2 = fp.add_run(" 页")
    set_run_font(r2, "宋体", 9, False, MUTED)

    # ---------- 封面 ----------
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("电影评论可视化")
    set_run_font(r, "黑体", 26, True, INK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run("作业1：数据下载、数据理解、数据过滤与数据处理（第一轮）")
    set_run_font(r, "宋体", 14, False, MUTED)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(36)
    r = p.add_run("第 X 组")
    set_run_font(r, "黑体", 16, True, INK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("组长：组长姓名（学号）　【正文占位：组员A】")
    set_run_font(r, "宋体", 12, False, INK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("组员：组员B（学号）、组员C（学号）、组员D（学号）")
    set_run_font(r, "宋体", 12, False, INK)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run("正文分工占位：组员A（组长）、组员B、组员C、组员D")
    set_run_font(r, "宋体", 10.5, False, MUTED)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(120)
    r = p.add_run("2026 年 11 月 24 日")
    set_run_font(r, "宋体", 12, False, INK)

    doc.add_page_break()

    # ---------- 文档说明 ----------
    add_h(doc, "文档说明与分工", 1, "组员A")
    P(doc, "本文档对应课程项目可视化七步设计方法的第 1—4 步第一轮设计：数据下载、数据理解、数据过滤、数据处理。"
           "选题属于个人类选题，个人背景只作为“一个影迷想搞清电影口碑好在哪、差在哪”的切入视角；"
           "数据主体是中文电影短评语料，不引入个人观影记录。")
    P(doc, "文档中的公开数据集规模来自数据源页面说明，已在相应位置注明来源；凡未实际下载或未运行脚本得到的统计值，"
           "一律写作“待实测回填”，并在第 5 章表 21 汇总，不虚构精确数字。示意图均标注“示意，非真实数据”。")

    add_h(doc, "分工总表", 2, "组员A")
    add_caption(doc, "表 1 正文分工与七步法对应（4 人，不重叠）", "表")
    add_table(
        doc,
        ["成员", "角色", "主责章节", "对应七步法", "主要交付物"],
        [
            ["组员A", "组长 / 统稿", "文档说明、1 数据下载", "第 1 步 数据下载", "数据与下载日志、数据源对比表、Word 成稿"],
            ["组员B", "数据理解", "2 数据理解", "第 2 步 数据理解", "字段与维度表、质量检查清单、数据概况图"],
            ["组员C", "数据过滤", "3 数据过滤", "第 3 步 数据过滤", "过滤规则表、funnel.csv、误杀抽检记录"],
            ["组员D", "数据处理", "4 数据处理", "第 4 步 数据处理", "清洗/分类/聚合表、气泡矩阵与辅助视图预览"],
        ],
        widths=[2.0, 2.6, 4.2, 3.2, 5.0],
    )
    small_note(doc, "说明：前四步由四位同学分别主责，章节不交叉；第 5 章“第一轮小结”由组员A 统稿，不计入前四步主责。")

    # ---------- 1 数据下载 ----------
    add_h(doc, "1 数据下载", 1, "组员A")
    P(doc, "本章完成数据需求定义、数据源核实、下载与落盘流程设计。由于 Kaggle Token 尚未配置，"
           "本章给出可复现的获取步骤与校验清单；实际行数、电影数、关联覆盖率等待下载后回填。")

    add_h(doc, "1.1 数据需求与选题边界", 2, "组员A")
    P(doc, "选题从一个影迷的具体困惑出发：同一部电影为什么有人打五星、有人打一星？好评和差评到底集中在哪些维度？"
           "因此需要“电影身份 + 评分 + 评论文本 + 评论类别 + 情感 + 时间 + 热度 + 电影属性”八类信息，"
           "而不是只拿到一个平均分。")

    add_h(doc, "1.1.1 数据维度清单", 3, "组员A")
    add_caption(doc, "表 2 数据维度清单（8 个维度，满足“不少于 5 个”）", "表")
    add_table(
        doc,
        ["编号", "维度", "对应字段", "分析用途"],
        [
            ["D1", "电影身份", "电影 ID、中文名、英文名", "气泡主体、跨表关联"],
            ["D2", "评分", "星级 1—5、豆瓣评分", "口碑、争议度、气泡位置"],
            ["D3", "评论文本", "Comment", "分类、情感、词云、代表评论"],
            ["D4", "评论类别", "从文本派生的 C0—C8 多标签", "气泡矩阵横轴、雷达轴"],
            ["D5", "情感倾向", "星级弱标签 + 文本情感", "气泡颜色、桑基流向"],
            ["D6", "时间", "评论日期、抓取日期", "时间趋势、数据时效说明"],
            ["D7", "讨论热度", "评论数、点赞数", "气泡大小、代表评论排序"],
            ["D8", "电影属性", "类型、年份、导演、海报", "分组、筛选、详情卡"],
        ],
        widths=[1.6, 2.6, 6.0, 5.6],
    )

    add_h(doc, "1.1.2 数据规模核算", 3, "组员A")
    P(doc, "课程要求数据量不少于 5,000。本项目以影评语料为数据主体：公开说明 DMSC v2 含 28 部电影、"
           "200 万条以上短评；实际分析时再分层抽取约 2 万条做分类训练与校验。即使只计算分析抽样，也远高于 5,000。"
           "具体行数、抽样条数与聚合表行数在下载和执行后回填。")
    add_caption(doc, "表 3 数据规模核算（公开说明值 + 待回填项）", "表")
    add_table(
        doc,
        ["数据层", "规模", "来源 / 状态"],
        [
            ["影评语料总量", "约 213 万条 / 28 部电影", "Kaggle 页面公开说明；实际行数待回填"],
            ["电影元数据", "2,065 部 / 约 15 MB", "Kaggle 页面公开说明；实际行数待回填"],
            ["分析抽样", "计划 2 万条", "按电影 × 星级分层；实际条数待回填"],
            ["分类标注 gold", "计划 300 条（100 条双标）", "执行标注后回填 kappa"],
            ["电影级聚合表", "约 28 行 movie_agg", "以实际电影数为准，待回填"],
            ["类别级聚合表", "电影数 × 9 类", "以实际输出为准，待回填"],
            ["维度数量", "8 个（D1—D8）", "已满足 ≥ 5"],
        ],
        widths=[4.0, 5.4, 6.2],
    )

    add_h(doc, "1.2 数据源与可获取性", 2, "组员A")
    P(doc, "2026 年 11 月 23 日对候选数据源做了页面核实：优先选择公开、字段完整、可直接下载、许可清晰的数据集；"
           "爬虫只作为小批量补充，不作为今晚主路径。")

    add_h(doc, "1.2.1 候选数据源对比", 3, "组员A")
    add_caption(doc, "表 4 候选数据源对比（核实日期 2026-11-23）", "表")
    add_table(
        doc,
        ["编号", "数据源", "内容与体量", "获取方式", "许可 / 合规", "结论"],
        [
            ["A", "Kaggle：DMSC v2", "28 部电影、200 万+ 短评；DMSC.csv 约 405.61 MB", "Kaggle 账号 + API Token", "CC0；豆瓣来源，课程使用需注明", "主方案"],
            ["B", "OpenBayes：dmsc_v2", "28 部、超 200 万条；处理后 104.99 MB", "OpenBayes 页面下载", "脱敏处理；具体许可需页面确认", "镜像备选"],
            ["C", "textdata：douba-movie-1000w", "10,269 部、10,310,989 条；1.35 GB", "百度网盘公开链接", "许可需自行确认；仅课程研究", "扩展备选"],
            ["D", "Kaggle：豆瓣电影元数据", "2,065 部、约 15 MB", "Kaggle API", "CC0", "元数据主方案"],
            ["E", "自建爬虫", "条数自定；单 IP 易限流", "短评页 / 接口", "需 Cookie/CSRF；受服务条款约束", "仅小批量补充"],
        ],
        widths=[1.5, 3.4, 4.8, 3.2, 3.6, 2.2],
        font_size=8.8,
    )

    add_h(doc, "1.2.2 主方案与备选方案", 3, "组员A")
    P(doc, "主方案为“DMSC v2 + 豆瓣电影元数据”：前者提供评论、星级、点赞与时间，后者补类型、年份、导演、海报。"
           "若 Kaggle 无法登录或下载失败，切换到 OpenBayes 的 dmsc_v2 镜像；若需要更多影片，再用 1000w 数据集抽样扩展。"
           "爬虫不作为主方案：短评接口依赖 Cookie 与 CSRF，缺失会 403 或返回空数据，连续请求还会触发限流。")

    add_h(doc, "1.3 数据获取流程", 2, "组员A")
    add_figure(doc, FIG_FLOW, "图 1 数据获取与落盘流程（示意，非真实数据）", 14.2)

    add_h(doc, "1.3.1 下载与校验步骤", 3, "组员A")
    P(doc, "下载前先准备 Kaggle API Token，将 kaggle.json 放到用户目录下的 .kaggle 文件夹；随后执行以下命令（路径按实际项目调整）：")
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run("kaggle datasets download -d utmhikari/doubanmovieshortcomments -p data/raw --unzip\n"
                  "kaggle datasets download -d dengfuping/douban-movies-dataset -p data/raw --unzip")
    set_run_font(r, "Consolas", 9.5, False, RGBColor(0x33, 0x33, 0x33))
    P(doc, "下载后必须运行校验脚本，记录行数、字段名、电影数、星级分布、元数据关联覆盖率。没有这些输出，"
           "后续章节的统计数字不得填写。")
    add_caption(doc, "表 5 下载与校验记录（实际值待回填）", "表")
    add_table(
        doc,
        ["检查项", "期望 / 目标", "实际值", "回填条件"],
        [
            ["DMSC.csv 行数", "≥ 2,000,000（公开说明）", "待实测回填", "下载后 len(df)"],
            ["电影数", "28（公开说明）", "待实测回填", "Movie_Name_CN.nunique()"],
            ["字段数", "10", "待实测回填", "df.columns"],
            ["元数据行数", "2,065（公开说明）", "待实测回填", "len(meta)"],
            ["元数据关联覆盖率", "目标 ≥ 90%", "待实测回填", "中文名清洗后匹配"],
            ["DMSC.csv 文件大小", "约 405.61 MB（公开说明）", "待实测回填", "文件属性"],
        ],
        widths=[4.6, 5.6, 3.4, 4.0],
    )

    add_h(doc, "1.3.2 合规与隐私", 3, "组员A")
    P(doc, "数据仅用于课程研究，报告中注明来源、抓取时间与许可；不展示用户名原文，示例统一使用“用户***”或哈希 ID；"
           "不抓取用户主页、不做用户画像；剧透内容默认折叠。若使用 1000w 数据集，需先确认其许可并在报告中单独说明。")

    # ---------- 2 数据理解 ----------
    add_h(doc, "2 数据理解", 1, "组员B")
    P(doc, "本章回答三个问题：数据里有什么、规模是否够、文本有什么特点与噪声。由于尚未下载，"
           "本章以字段字典、维度对应、质量检查清单和文本特性为主，统计表保留待实测回填位。")

    add_h(doc, "2.1 数据集与来源", 2, "组员B")
    add_h(doc, "2.1.1 数据集基本信息", 3, "组员B")
    add_caption(doc, "表 6 数据集基本信息（公开说明值）", "表")
    add_table(
        doc,
        ["数据集", "来源", "规模", "时间范围", "许可", "状态"],
        [
            ["DMSC v2", "Kaggle / 豆瓣电影", "28 部、200 万+ 条、405.61 MB", "抓取时间约 2016-12 至 2017-03", "CC0", "待下载"],
            ["豆瓣电影元数据", "Kaggle / 豆瓣电影", "2,065 部、约 15 MB", "2025 年采集", "CC0", "待下载"],
        ],
        widths=[2.8, 2.4, 3.4, 3.0, 1.9, 1.8],
        font_size=9.0,
    )
    P(doc, "DMSC v2 的评论集中在 2017 年初，属于历史快照，不能直接代表“当前口碑”。报告中将明确这一时效边界；"
           "若需要更新，可在第二轮用小批量爬虫或 1000w 数据集补充，但不与主数据混算。")

    add_h(doc, "2.1.2 数据时效与代表性", 3, "组员B")
    P(doc, "28 部电影覆盖类型有限，适合作为方法演示与第一轮分析样本，不适合推断整个中国电影市场。"
           "因此本项目的结论只针对“这 28 部电影的评论语料”，不写“中国观众普遍如何”的过度概括。")

    add_h(doc, "2.2 字段与维度", 2, "组员B")
    add_h(doc, "2.2.1 字段字典", 3, "组员B")
    add_caption(doc, "表 7 字段字典（以实际下载为准）", "表")
    add_table(
        doc,
        ["字段", "类型", "含义", "质量风险", "处理动作"],
        [
            ["ID", "int", "评论序号", "可能重复/不连续", "去重辅助，不作主键"],
            ["Movie_Name_EN", "string", "英文片名", "缺失、译名不一", "仅展示"],
            ["Movie_Name_CN", "string", "中文片名", "可能含副标题", "清洗后作为关联键"],
            ["Crawl_Date", "date", "抓取日期", "集中在 2017 年初", "写入时效说明"],
            ["Number", "int", "评论计数", "语义需核对", "仅统计"],
            ["Username", "string", "用户名", "隐私", "哈希/不展示"],
            ["Date", "datetime", "评论时间", "格式不统一", "解析为 datetime"],
            ["Star", "int", "1—5 星", "可能缺失/为 0", "缺失单列，不参与情感聚合"],
            ["Comment", "text", "短评正文", "广告、重复、非中文、符号", "过滤与清洗"],
            ["Like", "int", "有用数", "可能缺失", "代表评论排序"],
            ["movie_id / title", "int/string", "豆瓣电影 ID 与片名", "译名不一致", "按中文名关联"],
            ["genres / release_date", "string/date", "类型与上映日期", "缺失", "分组与时间分析"],
            ["rating / poster", "float/string", "豆瓣评分与海报", "缺失", "详情卡与参考"],
        ],
        widths=[4.0, 2.2, 3.4, 4.4, 4.8],
        font_size=8.9,
    )

    add_h(doc, "2.2.2 维度与字段对应", 3, "组员B")
    P(doc, "表 2 中已给出 D1—D8 的完整定义。这里补充实现口径：D2 的“争议度”用星级标准差，D4 的类别由第 4 章的多标签分类派生，"
           "D5 同时保留星级弱标签与文本情感两轨，D7 的评论量用过滤后的有效评论数而不是原始行数。")

    add_h(doc, "2.2.3 缺失与质量初检", 3, "组员B")
    add_caption(doc, "表 8 数据质量检查清单（实际结果待回填）", "表")
    add_table(
        doc,
        ["检查项", "检查方法", "主要风险", "状态"],
        [
            ["星级缺失/异常", "Star 为空、0 或 >5 的占比", "情感聚合偏差", "待实测回填"],
            ["日期解析", "Date 转 datetime 的失败率", "时间趋势错误", "待实测回填"],
            ["完全重复", "Comment 去空白后完全相同", "虚增热度", "待实测回填"],
            ["近似重复", "SimHash 汉明距离 ≤ 3", "模板/洗稿", "待实测回填"],
            ["非中文", "中文字符占比 < 0.5", "分词失效", "待实测回填"],
            ["广告/水印", "正则命中率", "污染词云", "待实测回填"],
            ["短文本", "去标点后中文字符 < 4 且无情感词", "无信息噪声", "待实测回填"],
            ["每片评论数", "min / median / max", "气泡大小悬殊", "待实测回填"],
            ["元数据关联", "中文名匹配率", "类型/年份缺失", "待实测回填"],
        ],
        widths=[4.0, 6.2, 4.4, 3.2],
    )

    add_h(doc, "2.3 文本特性与噪声", 2, "组员B")
    add_h(doc, "2.3.1 文本特性", 3, "组员B")
    bullet(doc, "短：以口语化、情绪化短句为主，单条信息量低，“好看”“一般”“烂”这类整体评价占比高。")
    bullet(doc, "多维度：同一句可能同时评价剧情、演技、特效，例如“演技在线，但剧情拖沓”，因此分类必须多标签。")
    bullet(doc, "反讽与玩梗多：“真是谢谢导演了”这类文本会让词典情感误判，需要人工抽检与反例说明。")
    bullet(doc, "形式杂：表情符号、颜文字、重复标点、全角字符、繁体字、英文片名混用。")
    bullet(doc, "模板化：热门影片存在复制粘贴、刷好评/差评，重复文本会虚增热度。")

    add_h(doc, "2.3.2 噪声类型", 3, "组员B")
    add_caption(doc, "表 9 噪声类型与处理方向", "表")
    add_table(
        doc,
        ["噪声类型", "例子（示意）", "影响", "处理"],
        [
            ["广告引流", "加微信 xxx 拿资源", "污染词云与分类", "正则删除"],
            ["无信息短评", "沙发、打卡、哈哈哈", "拉低分类质量", "长度 + 规则过滤"],
            ["非中文", "纯英文、日文、数字、表情", "分词与情感失效", "中文字符占比过滤"],
            ["重复/模板", "同一文本多人发布", "虚增热度", "完全去重 + SimHash"],
            ["剧透", "凶手就是……、最后都死了", "影响阅读体验", "标记并默认折叠"],
            ["场外抱怨", "影院太吵、票太贵", "与电影质量无关", "单列 C7，可选排除"],
            ["想看/标记", "想看、先码、留着看", "不是观后评论", "关键词过滤"],
            ["星级缺失", "空值、0", "情感聚合偏差", "单列，不参与均值"],
        ],
        widths=[3.4, 6.0, 4.0, 4.6],
    )

    add_h(doc, "2.3.3 数据理解结论", 3, "组员B")
    P(doc, "第一轮可以确认三件事：其一，数据量足够支撑 5,000 条以上的分析；其二，维度足够覆盖“电影—评论—情感—属性”四层；"
           "其三，噪声主要来自广告、重复、非中文与无信息短文本，必须在第 3 章先过滤。具体比例与分布待脚本输出后回填。")

    add_h(doc, "2.4 数据概况图（编码示意）", 2, "组员B")
    P(doc, "下图只用于说明“口碑—争议”两个维度将如何编码，不代表真实统计结果。实际点位置、气泡大小与颜色在数据下载后重绘。")
    add_figure(doc, FIG_SCATTER, "图 2 口碑—争议散点气泡图（示意，非真实数据）", 14.2)

    # ---------- 3 数据过滤 ----------
    add_h(doc, "3 数据过滤", 1, "组员C")
    P(doc, "本章把“能用于分析的评论”从原始数据中筛出来。原则是先保真、再保量：宁可少几百条，也不让广告和模板文本进入词云；"
           "每条被删评论必须留下 drop_reason，便于复核与写报告。")

    add_h(doc, "3.1 过滤原则", 2, "组员C")
    num(doc, "先保真，再保量：广告、模板、非中文优先删除，不用数量换质量。")
    num(doc, "可解释：每条删除都有原因，漏斗各阶段可加总。")
    num(doc, "不误杀有效短评：“好看”“一般”只有 2—3 字，但属于有效整体评价，不能只用长度阈值一刀切。")
    num(doc, "剧透不删除：只标记并默认折叠，保留情感统计价值。")
    num(doc, "顺序固定：去重 → 去广告 → 语言/长度 → 相关性 → 模板，避免规则互相污染。")

    add_h(doc, "3.2 过滤规则", 2, "组员C")
    add_h(doc, "3.2.1 规则总表", 3, "组员C")
    add_caption(doc, "表 10 数据过滤规则（F1—F14）", "表")
    add_table(
        doc,
        ["编号", "规则", "判定条件", "处理", "预期影响"],
        [
            ["F1", "完全重复", "Comment 去空白后完全相同", "保留最早或点赞最高一条", "降低模板文本"],
            ["F2", "近似重复", "SimHash 64 位，汉明距离 ≤ 3", "保留点赞最高一条", "去除洗稿/复制"],
            ["F3", "同用户同片重复", "同一用户名 + 电影，文本高度相似", "保留最长/最新一条", "去除刷评"],
            ["F4", "广告/水印引流", "URL、微信号、QQ、加群、资源、公众号、二维码等", "删除", "净化词云"],
            ["F5", "联系方式", "连续 6 位以上数字、邮箱、手机号", "删除", "隐私与广告"],
            ["F6", "无信息文本", "去标点/表情后中文字符 < 4 且不含情感词", "删除", "去除“哈哈哈”“沙发”"],
            ["F7", "非中文", "中文字符占比 < 0.5", "删除", "保证分词有效"],
            ["F8", "超长短评", "字符数 > 300", "截断或转长评表", "控制文本长度"],
            ["F9", "想看/标记", "“想看”“标记”“先码”且无观后语义", "删除", "去除未观影文本"],
            ["F10", "纯表情/符号", "去除表情与标点后为空", "删除", "降低噪声"],
            ["F11", "剧透", "“剧透/凶手/结局是/最后死/反转是”等", "标记 is_spoiler=1，默认折叠", "保留统计价值"],
            ["F12", "场外体验", "影院、票价、排片、字幕、配音、观众", "保留，标 is_offtopic=1", "聚合时可排除"],
            ["F13", "星级异常", "Star 为空、0、>5", "star_valid=0，不参与情感聚合", "防止均值偏差"],
            ["F14", "机器模板", "相同 8-gram 在 ≥ 20 条评论重复", "标记 is_template=1，默认排除", "去除水军文本"],
        ],
        widths=[1.5, 3.2, 6.4, 4.6, 3.2],
        font_size=8.6,
    )

    add_h(doc, "3.2.2 阈值设定依据", 3, "组员C")
    P(doc, "短文本阈值采用“长度 + 情感词”双条件，避免误杀“好看”“一般”；非中文只按中文字符占比判断，短句交给 F6；"
           "近似重复先抽 2,000 条调阈值，确认误杀率可接受后再全量跑。所有阈值写入 config.yaml，报告中列出并说明依据。")

    add_h(doc, "3.3 执行顺序与实现", 2, "组员C")
    add_h(doc, "3.3.1 处理顺序", 3, "组员C")
    P(doc, "执行顺序固定为：解析字段 → 完全去重 → 近似去重 → 广告/联系方式 → 语言 → 短文本 → 想看/标记 → 剧透/场外 → 星级异常 → 模板检测。"
           "每条规则只写第一个命中的 drop_reason，保证漏斗可加总。")
    add_h(doc, "3.3.2 规则实现要点", 3, "组员C")
    P(doc, "正则、阈值与判定函数集中在 rules.py；输出 comments_flagged.parquet，保留 text_clean、char_len、zh_ratio、"
           "is_spoiler、is_offtopic、star_valid、is_template、keep、drop_reason 等字段，方便复核。")
    P(doc, "示例正则（起步版，需在真实样本上调）：URL、微信号、QQ、加群/资源/公众号、邮箱、手机号；剧透词包括“剧透、凶手就是、结局是、最后死、反转是”。")

    add_figure(doc, FIG_FUNNEL, "图 3 数据过滤漏斗（示意，非真实数据）", 13.0)

    add_h(doc, "3.4 过滤结果与抽检", 2, "组员C")
    add_h(doc, "3.4.1 漏斗统计", 3, "组员C")
    add_caption(doc, "表 11 过滤漏斗统计（实际值待回填）", "表")
    add_table(
        doc,
        ["阶段", "剩余条数", "本阶段删除", "删除原因", "状态"],
        [
            ["原始", "N0", "—", "—", "待实测回填"],
            ["完全/近似去重", "N1", "N0-N1", "重复、模板", "待实测回填"],
            ["去广告/水印", "N2", "N1-N2", "引流、联系方式", "待实测回填"],
            ["语言/长度", "N3", "N2-N3", "非中文、无信息短文本", "待实测回填"],
            ["相关性", "N4", "N3-N4", "想看、模板、无关", "待实测回填"],
            ["最终可用", "N5", "N4-N5", "兜底清理", "待实测回填"],
        ],
        widths=[3.6, 3.0, 3.0, 5.6, 3.4],
    )
    small_note(doc, "回填条件：运行 03_filter.py 生成 funnel.csv；各阶段数量必须可加总，差额为 0。")

    add_h(doc, "3.4.2 误杀与残留抽检", 3, "组员C")
    P(doc, "随机抽 50 条被删样本，人工判断误杀率；再抽 50 条保留样本，检查广告/非中文残留。"
           "目标：误杀率 ≤ 10%，保留样本广告/非中文残留 ≤ 5%。实际结果待抽检后回填。")

    add_h(doc, "3.5 过滤样例", 2, "组员C")
    add_caption(doc, "表 12 过滤前后样例（示例，非真实数据）", "表")
    add_table(
        doc,
        ["类型", "过滤前", "处理后", "原因"],
        [
            ["广告", "“加微信 abc123 拿高清资源”", "删除", "命中 F4"],
            ["重复", "同一句“太好看了”出现 20 次", "保留 1 条", "命中 F1/F14"],
            ["剧透", "“凶手就是那个医生”", "保留，标记折叠", "命中 F11"],
        ],
        widths=[2.2, 8.2, 3.0, 2.2],
    )

    # ---------- 4 数据处理 ----------
    add_h(doc, "4 数据处理", 1, "组员D")
    P(doc, "本章把过滤后的评论变成可聚合的指标：先清洗、分词，再算情感和 C0—C8 多标签，最后聚合到电影级与类别级表，"
           "供气泡矩阵、散点导航、桑基图使用。")

    add_h(doc, "4.1 清洗与标准化", 2, "组员D")
    add_h(doc, "4.1.1 清洗步骤", 3, "组员D")
    add_caption(doc, "表 13 文本清洗步骤与输出字段", "表")
    add_table(
        doc,
        ["步骤", "操作", "输出字段"],
        [
            ["1", "HTML 标签与实体反转义（&nbsp;、<br>）", "text_html_clean"],
            ["2", "全角转半角，统一标点", "text_norm"],
            ["3", "繁体转简体（OpenCC t2s）", "text_norm"],
            ["4", "去零宽字符、控制字符、连续重复标点", "text_clean"],
            ["5", "URL、@用户、话题标签删除或替换", "text_clean"],
            ["6", "表情符号：保留少量语义表情，其余删除", "emoji_cnt"],
            ["7", "英文统一小写，保留片名英文", "text_clean"],
            ["8", "合并空白、去首尾空格，计算长度与中文占比", "char_len、zh_ratio"],
        ],
        widths=[1.4, 10.4, 3.8],
    )

    add_h(doc, "4.1.2 分词与停用词", 3, "组员D")
    P(doc, "使用 jieba，并加载自定义词典：电影名、角色名、演员/导演名，以及“演技、剧情、节奏、镜头、配乐、特效、反转、烂尾、出戏、代入感、服化道、IMAX”等领域词。"
           "停用词采用哈工大/百度停用词表加自定义补充；词云额外过滤片名、演员名、单字和纯数字。")

    add_h(doc, "4.2 情感倾向", 2, "组员D")
    add_h(doc, "4.2.1 双轨设计", 3, "组员D")
    add_caption(doc, "表 14 情感双轨：星级弱标签与文本情感", "表")
    add_table(
        doc,
        ["轨道", "定义", "生成方式", "用途", "局限"],
        [
            ["sent_star", "1—2 负、3 中、4—5 正", "由 Star 直接映射", "气泡颜色、整体正面率", "星级与文本可能不一致"],
            ["sent_text", "负/中/正 + 分数", "BosonNLP 词典 + 否定/程度词；SnowNLP 对照", "类别内比较、词云分区", "反讽与短文本易误判"],
        ],
        widths=[2.6, 4.0, 5.2, 4.0, 4.2],
        font_size=8.9,
    )
    P(doc, "否定词窗口取情感词前 3 个词，命中“不、没、别、无、未、不是”则翻转；程度副词按权重缩放；"
           "阈值在 100 条人工标注上校准。sent_star 与 sent_text 的一致率待实测回填；若低于 65%，以星级为主，文本情感只做类别内相对比较。")

    add_h(doc, "4.3 评论分类体系", 2, "组员D")
    add_h(doc, "4.3.1 C0—C8 类别定义", 3, "组员D")
    add_caption(doc, "表 15 评论分类体系（9 类多标签）", "表")
    add_table(
        doc,
        ["编码", "标签", "定义", "典型触发词", "边界说明"],
        [
            ["C0", "整体评价", "只给总体好坏、推荐/不推荐，不展开具体维度", "好看、难看、一般、推荐、失望", "有具体维度时 C0 可保留但不作主标签"],
            ["C1", "剧情叙事", "故事、剧本、逻辑、节奏、结局、改编、反转", "剧情、剧本、逻辑、拖沓、烂尾、反转", "“节奏慢”归此；单纯“无聊”无线索归 C0"],
            ["C2", "表演角色", "演技、演员、选角、人物塑造、台词功底", "演技、演员、出戏、人物、选角", "角色颜值讨论也归此"],
            ["C3", "视听特效", "画面、摄影、特效、美术、服化道、镜头", "画面、特效、摄影、美术、IMAX", "“镜头美”归此；镜头语言风格归 C5"],
            ["C4", "音乐音效", "配乐、主题曲、声音设计", "配乐、音乐、主题曲、音效、BGM", "歌词内容讨论归 C6"],
            ["C5", "导演风格", "导演、风格、叙事手法、致敬、作者性", "导演、风格、镜头语言、致敬、氛围", "导演个人八卦归 C8"],
            ["C6", "主题情感", "立意、价值观、共鸣、感动、治愈、压抑", "感动、治愈、共鸣、立意、压抑、后劲", "只写“哭了”且有情绪指向可归此"],
            ["C7", "场外体验", "影院、票价、排片、字幕、配音、观众", "影院、票价、排片、字幕、配音", "与影片质量无关，聚合时可排除"],
            ["C8", "其他/无信息", "无法归类、纯情绪符号、无关内容", "哈哈哈、打卡、路过", "广告应已被过滤，不应大量落入此列"],
        ],
        widths=[1.5, 2.4, 6.4, 5.4, 4.2],
        font_size=8.4,
    )

    add_h(doc, "4.3.2 多标签与主标签规则", 3, "组员D")
    P(doc, "一条评论提到几个维度就打几个标签，最多 3 个；超过 3 个取证据最强的 3 个。主标签取篇幅最大或情感最集中的维度；"
           "纯整体评价的主标签为 C0。疑问句、比较句按实际评价对象打标；无法判断归 C8，并在备注写“语义不明”，不强行归类。")

    add_figure(doc, FIG_CLASS, "图 4 评论分类与聚合流程（示意，非真实数据）", 14.0)

    add_h(doc, "4.4 标注与识别落地", 2, "组员D")
    add_h(doc, "4.4.1 标注方案", 3, "组员D")
    P(doc, "从过滤后的数据中分层抽 300 条作为 gold set，覆盖 28 部电影 × 负/中/正星级；其中 100 条由两人独立标注，计算 Cohen's kappa，"
           "目标 ≥ 0.60；其余 200 条一人标注、一人抽查 20%。争议样本由第三人裁决并记录理由。")
    add_caption(doc, "表 16 标注表字段", "表")
    add_table(
        doc,
        ["字段", "类型", "说明"],
        [
            ["comment_id", "string", "评论唯一标识"],
            ["text", "string", "清洗后文本"],
            ["movie / star", "string/int", "电影与星级"],
            ["c0—c8", "0/1", "九类多标签"],
            ["primary", "string", "主标签"],
            ["sent_gold", "string", "人工情感：负/中/正"],
            ["is_spoiler", "0/1", "是否剧透"],
            ["annotator / note", "string", "标注人与备注"],
        ],
        widths=[3.4, 3.0, 8.8],
    )

    add_h(doc, "4.4.2 规则与模型阶梯", 3, "组员D")
    add_caption(doc, "表 17 分类识别阶梯（L0—L3）", "表")
    add_table(
        doc,
        ["层级", "方法", "输入", "输出", "评估 / 状态"],
        [
            ["L0", "关键词/正则规则（每类 30—50 个种子词）", "清洗文本", "多标签 + 主标签", "coverage 与 macro-F1 待回填"],
            ["L1", "TF-IDF 字符 2—4 gram + OneVsRest LinearSVC", "gold 300—500 条", "多标签 + 置信度", "macro-F1 待回填；目标 ≥ 0.60"],
            ["L2", "LLM 零样本/少样本，输出 JSON", "定义 + 每类 2 例 + 文本", "多标签", "在 100 条 gold 上评估，成本可控才用"],
            ["L3", "微调 Chinese-RoBERTa", "1—10 万条弱标签/人工标签", "多标签", "第二轮，不在作业1阻塞"],
        ],
        widths=[1.8, 6.2, 3.6, 3.2, 4.4],
        font_size=8.8,
    )
    P(doc, "第一轮至少完成 L0：先跑全量，得到每类提及率与初步聚合；用 gold 300 评估，若 macro-F1 不足，优先补种子词与规则，"
           "而不是盲目上模型。未达置信度的评论归 C8，不强行分类。")

    add_h(doc, "4.5 聚合到气泡图指标", 2, "组员D")
    add_h(doc, "4.5.1 电影级指标", 3, "组员D")
    add_caption(doc, "表 18 电影级聚合指标（movie_agg）", "表")
    add_table(
        doc,
        ["指标", "公式 / 口径", "用途"],
        [
            ["n_valid", "过滤后评论数", "气泡大小"],
            ["avg_star", "mean(Star)", "气泡 X 轴"],
            ["star_std", "std(Star, ddof=1)", "气泡 Y 轴（争议度）"],
            ["pos_rate", "count(Star≥4)/n_valid", "气泡颜色"],
            ["neg_rate", "count(Star≤2)/n_valid", "负面率"],
            ["polarization", "4 × pos_rate × neg_rate", "两极分化指数，tooltip"],
            ["category_share[c]", "提及 c 的评论数 / n_valid", "矩阵面积"],
            ["category_score[c]", "(mean_star_c - 1)/4 × 100", "雷达图数值"],
            ["diversity", "-Σ p_c log(p_c)/log(9)", "评价维度丰富度"],
            ["top_category", "argmax(category_share)", "主评价维度"],
        ],
        widths=[4.2, 7.2, 4.2],
        font_size=8.9,
    )

    add_h(doc, "4.5.2 类别级指标", 3, "组员D")
    add_caption(doc, "表 19 类别级聚合指标（category_agg）", "表")
    add_table(
        doc,
        ["字段", "说明", "用途"],
        [
            ["movie_id / category", "电影与类别", "主键"],
            ["mention_cnt", "该电影该类别被提及次数", "矩阵气泡面积"],
            ["share", "mention_cnt / n_valid", "类别占比"],
            ["avg_star", "该类别提及评论的平均星级", "类别口碑"],
            ["pos_rate", "该类别提及评论中 Star≥4 的占比", "矩阵颜色"],
            ["top_words", "该类别 TF-IDF Top 15 词", "词云/详情"],
        ],
        widths=[4.2, 8.0, 4.0],
    )

    add_h(doc, "4.5.3 输出表结构", 3, "组员D")
    add_caption(doc, "表 20 数据处理输出文件", "表")
    add_table(
        doc,
        ["文件", "内容", "状态"],
        [
            ["comments_clean.parquet", "清洗后评论与长度/语言字段", "待生成"],
            ["comments_flagged.parquet", "过滤标记、drop_reason、keep", "待生成"],
            ["comments_labeled.parquet", "情感、C0—C8 标签、主标签", "待生成"],
            ["movie_agg.csv", "电影级聚合指标", "待生成"],
            ["category_agg.csv", "电影 × 类别聚合指标", "待生成"],
            ["funnel.csv / gold_300.csv", "漏斗与人工标注", "待生成"],
        ],
        widths=[5.2, 8.0, 2.6],
    )

    add_h(doc, "4.6 可视化预览：聚合指标怎么用", 2, "组员D")
    P(doc, "本节不属于前四步的强制交付，只说明第 4 章输出如何被后续可视化使用。以下图片均为编码示意，不是实测结果；"
           "最终作品会根据真实聚合表重绘。")

    add_h(doc, "4.6.1 主视图：电影 × 类别气泡矩阵", 3, "组员D")
    P(doc, "矩阵横轴为 C0—C8，纵轴为电影（按平均星级排序），气泡面积表示该类别提及量，颜色表示该类别正面率。"
           "它把“评价维度结构”和“每个维度的口碑”放在同一张图里，是后续主视图的首选。")
    add_figure(doc, FIG_MATRIX, "图 5 电影 × 类别气泡矩阵（示意，非真实数据）", 14.8)

    add_h(doc, "4.6.2 辅助视图：雷达与桑基", 3, "组员D")
    P(doc, "雷达图用于单部电影的六维画像，对比全库均值；桑基图用于看九类评论分别流向正面、中性还是负面。"
           "两者都不使用柱形图或饼图，避免与课程要求冲突。")
    add_figure(doc, FIG_RADAR, "图 6 六维画像雷达（示意，非真实数据）", 12.0)
    add_figure(doc, FIG_SANKEY, "图 7 类别 → 情感桑基图（示意，非真实数据）", 14.2)

    add_h(doc, "4.6.3 联动原型：散点导航 + 矩阵下钻", 3, "组员D")
    P(doc, "顶部细长散点用于选片，下方矩阵对应行高亮；点击矩阵单元格后，右侧详情接雷达、词云与评论列表。"
           "这组联动是后续交互设计的骨架，也是“从总览到下钻”的主要路径。")
    add_figure(doc, FIG_LINKED, "图 8 散点导航与矩阵联动（示意，非真实数据）", 13.6)

    # ---------- 5 小结 ----------
    add_h(doc, "5 第一轮小结与待回填", 1, "组员A")
    P(doc, "第一轮已完成：数据源核实与获取流程、8 个维度与规模核算、字段与质量检查清单、F1—F14 过滤规则、"
           "C0—C8 分类体系、情感双轨、电影级/类别级聚合指标，以及气泡矩阵、雷达、桑基、联动原型的编码预览。"
           "尚未完成的是实际下载、实测统计、300 条 gold 标注与模型评估；这些都在下表中列出回填条件。")

    add_caption(doc, "表 21 待实测回填清单", "表")
    add_table(
        doc,
        ["位置", "待回填项", "回填条件", "状态"],
        [
            ["表 5", "DMSC 行数、电影数、字段数、关联覆盖率", "配置 Kaggle Token 并运行 01_download_check.py", "待回填"],
            ["表 8", "缺失率、重复率、非中文率、广告命中率", "运行 02_eda.py", "待回填"],
            ["表 11", "漏斗 N0—N5、保留率", "运行 03_filter.py 生成 funnel.csv", "待回填"],
            ["3.4.2", "误杀率、广告/非中文残留率", "完成 50 + 50 条人工抽检", "待回填"],
            ["表 14", "星级与文本情感一致率", "完成 100 条人工情感标注", "待回填"],
            ["表 17", "L0/L1 coverage、macro-F1、每类 P/R/F1", "完成 gold 300 并运行评估", "待回填"],
            ["4.4.1", "Cohen's kappa", "完成 100 条双标", "待回填"],
            ["表 18—20", "聚合表行数与字段完整性", "运行 05_aggregate.py", "待回填"],
            ["图 2、5—8", "真实数据重绘", "聚合表生成后替换示意图", "待重绘"],
            ["全文", "组号、姓名、学号", "用户提供名单后替换占位符", "待替换"],
        ],
        widths=[3.4, 7.2, 6.8, 2.0],
        font_size=8.8,
    )

    # ---------- 参考资料 ----------
    add_h(doc, "参考资料", 1, "组员A")
    refs = [
        "Kaggle. Douban Movie Short Comments Dataset V2. https://www.kaggle.com/datasets/utmhikari/doubanmovieshortcomments（核实日期 2026-11-23）",
        "Kaggle. Douban Movies Dataset. https://www.kaggle.com/datasets/dengfuping/douban-movies-dataset（核实日期 2026-11-23）",
        "OpenBayes. dmsc_v2 电影评论数据集. https://openbayes.com/console/public/models/O8JueiMPoPI/1/overview（核实日期 2026-11-23）",
        "大邓和他的 Python. 数据集 | 使用 1000w 条豆瓣影评训练 Word2Vec. https://textdata.cn/blog/2024-04-16-douban-movie-1000w-ratings-comments-dataset/（核实日期 2026-11-23）",
        "豆瓣电影 robots.txt. https://movie.douban.com/robots.txt（核实日期 2026-11-23）",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.first_line_indent = Pt(0)
        r = p.add_run(ref)
        set_run_font(r, "宋体", 10, False, MUTED)

    doc.save(DOCX)
    print(DOCX)


if __name__ == "__main__":
    build()
