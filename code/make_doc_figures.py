# -*- coding: utf-8 -*-
"""生成作业1配图：数据获取流程、过滤漏斗、分类处理流程。"""

import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan\work\figures"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

font_manager.fontManager.addfont(FONT_REG)
font_manager.fontManager.addfont(FONT_BOLD)
FONT_FAMILY = font_manager.FontProperties(fname=FONT_REG).get_name()
plt.rcParams.update({
    "font.family": FONT_FAMILY,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

INK = "#222222"
MUTED = "#666666"
BLUE = "#2F5D8A"
LIGHT = "#EDF2F7"
EDGE = "#B8C4D0"
ACCENT = "#B22222"


def stamp(fig):
    fig.text(0.995, 0.008, "示意，非真实数据", ha="right", va="bottom",
             fontsize=11, color=ACCENT,
             bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=ACCENT, lw=0.8),
             zorder=100)


def save(fig, name):
    path = os.path.join(BASE, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    return path


def box(ax, x, y, w, h, title, body, fc=LIGHT, ec=EDGE, title_size=12.5, body_size=9.6):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=1.1))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", color=INK)
    if body:
        ax.text(x + w / 2, y + h / 2 - 0.14, body, ha="center", va="center",
                fontsize=body_size, color=MUTED, linespacing=1.45)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, color="#7A8A99",
                                 linewidth=1.5, shrinkA=2, shrinkB=2))


def fig_data_flow():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(5, 9.65, "数据获取与落盘流程", ha="center", va="top",
            fontsize=18, fontweight="bold", color=INK)
    ax.text(5, 9.22, "从公开数据集到可复核的分析表；实际行数与关联率待实测回填",
            ha="center", va="top", fontsize=10.2, color=MUTED)

    box(ax, 3.0, 7.55, 4.0, 1.20, "① 选题与数据需求",
        "目标：电影口碑“好在哪、差在哪”\n维度：D1—D8；数据量目标 ≥ 5,000")
    box(ax, 3.0, 5.75, 4.0, 1.22, "② 数据源组合",
        "DMSC v2：28 部 / 约 213 万条 / 405.61 MB / CC0\n豆瓣电影元数据：2,065 部（公开说明）")
    box(ax, 3.0, 3.95, 4.0, 1.22, "③ Kaggle API 下载与解压",
        "kaggle datasets download … --unzip\n输出：data/raw/DMSC.csv + 元数据 CSV")
    box(ax, 3.0, 2.15, 4.0, 1.22, "④ 校验与关联",
        "字段/星级/日期解析；中文名去副标题后关联\n未匹配影片：28 行手工映射兜底")
    box(ax, 2.35, 0.35, 5.3, 1.25, "⑤ 分析用数据表",
        "comments_flagged.parquet / comments_labeled.parquet\nmovie_agg.csv / category_agg.csv",
        fc="#E8F0E8", ec="#9DB39D")

    for y1, y2 in [(7.55, 6.97), (5.75, 5.17), (3.95, 3.37), (2.15, 1.60)]:
        arrow(ax, 5.0, y1, 5.0, y2)

    ax.text(7.25, 6.95, "可获取性已核实\n（2026-11-23）", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)
    ax.text(7.25, 5.15, "许可：CC0（DMSC）\n仅课程研究使用", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)
    ax.text(7.25, 3.35, "校验脚本：01_download_check.py\n日志：work/logs/", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)
    ax.text(7.25, 1.55, "关联覆盖率待回填\n目标：类型字段 ≥ 90%", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)

    stamp(fig)
    return save(fig, "fig_data_flow.png")


def fig_funnel():
    fig, ax = plt.subplots(figsize=(10.5, 7.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    ax.text(5, 9.65, "数据过滤漏斗", ha="center", va="top",
            fontsize=18, fontweight="bold", color=INK)
    ax.text(5, 9.22, "宽度仅示意阶段顺序，不代表真实保留比例；各阶段数量待实测回填",
            ha="center", va="top", fontsize=10.0, color=MUTED)

    stages = [
        ("原始评论", "N0（待实测回填）"),
        ("完全/近似去重", "N1（待实测回填）"),
        ("广告/水印/联系方式", "N2（待实测回填）"),
        ("非中文/无信息短文本", "N3（待实测回填）"),
        ("想看/模板/无关", "N4（待实测回填）"),
        ("最终可用", "N5（待实测回填）"),
    ]
    widths = [7.6, 6.9, 6.2, 5.5, 4.8, 4.1]
    top = 8.35
    h = 1.06
    gap = 0.20
    colors = ["#DCE6F0", "#D5E1EC", "#CDDBE8", "#C5D5E4", "#BDCFDF", "#B5C9DB"]
    for i, (label, count) in enumerate(stages):
        w = widths[i]
        x0 = 5 - w / 2
        y0 = top - i * (h + gap)
        poly = Polygon([[x0, y0], [x0 + w, y0], [x0 + w - 0.35, y0 - h], [x0 + 0.35, y0 - h]],
                       closed=True, facecolor=colors[i], edgecolor="#8FA3B5", linewidth=1.0)
        ax.add_patch(poly)
        ax.text(5, y0 - h / 2 + 0.16, label, ha="center", va="center",
                fontsize=11.5, fontweight="bold", color=INK)
        ax.text(5, y0 - h / 2 - 0.20, count, ha="center", va="center",
                fontsize=8.8, color=MUTED)
        ax.text(x0 + w + 0.25, y0 - h / 2, f"阶段 {i}", ha="left", va="center",
                fontsize=9.2, color="#7A8A99")

    ax.text(5, 0.55, "回填条件：运行 03_filter.py，生成 funnel.csv 后把 N0—N5 替换为实测值；保留率与误杀抽检同表记录。",
            ha="center", va="center", fontsize=9.4, color=MUTED)

    stamp(fig)
    return save(fig, "fig_filter_funnel.png")


def fig_classification():
    fig, ax = plt.subplots(figsize=(13, 6.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")

    ax.text(7, 6.65, "评论分类与聚合流程", ha="center", va="top",
            fontsize=18, fontweight="bold", color=INK)
    ax.text(7, 6.22, "规则 L0 先跑通，再用 300 条 gold 评估；有余力再上 TF-IDF / LLM",
            ha="center", va="top", fontsize=10.0, color=MUTED)

    boxes = [
        (0.4, 4.35, 2.9, 1.35, "清洗文本", "去 HTML/全角\n繁转简/去表情\n分词 + 停用词"),
        (3.9, 4.35, 3.0, 1.35, "分类识别", "L0 关键词/正则\nL1 TF-IDF+LinearSVC\nL2 LLM 零样本"),
        (7.6, 4.35, 2.9, 1.35, "多标签输出", "C0—C8，最多 3 个\n主标签 + 置信度\nsent_star / sent_text"),
        (11.1, 4.35, 2.5, 1.35, "聚合指标", "movie_agg\ncategory_agg\n气泡矩阵 / 桑基"),
    ]
    for x, y, w, h, title, body in boxes:
        box(ax, x, y, w, h, title, body, title_size=11.8, body_size=8.8)

    for x1 in (3.3, 6.9, 10.5):
        arrow(ax, x1, 5.02, x1 + 0.55, 5.02)

    box(ax, 3.9, 2.55, 3.0, 1.15, "人工标注 gold 300",
        "100 条双标 → Cohen's kappa\n目标 ≥ 0.60；争议样本第三人裁决",
        fc="#FBF3E4", ec="#D8C39A", title_size=11.0, body_size=8.6)
    box(ax, 7.6, 2.55, 2.9, 1.15, "评估指标",
        "每类 P/R/F1、macro-F1\n覆盖率；错误样本抽查",
        fc="#FBF3E4", ec="#D8C39A", title_size=11.0, body_size=8.6)
    arrow(ax, 5.4, 3.70, 5.4, 4.30)
    arrow(ax, 9.05, 3.70, 9.05, 4.30)

    ax.text(7, 1.45, "关键约束：分类是多标签问题；“整体评价”不能吞掉具体维度；未达置信度的评论归 C8，不强行分类。",
            ha="center", va="center", fontsize=9.6, color="#555555")
    ax.text(7, 0.95, "示意，非真实数据；实际覆盖率、kappa、macro-F1 待标注与评估后回填。",
            ha="center", va="center", fontsize=9.4, color=ACCENT)

    stamp(fig)
    return save(fig, "fig_classification_flow.png")


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    for p in (fig_data_flow(), fig_funnel(), fig_classification()):
        print(p)
