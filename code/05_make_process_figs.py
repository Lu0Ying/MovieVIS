# -*- coding: utf-8 -*-
"""用实测数字重绘三张过程图：数据获取流程、过滤漏斗、分类聚合流程。"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan\work\figures"
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
font_manager.fontManager.addfont(FONT_REG)
font_manager.fontManager.addfont(FONT_BOLD)
FAMILY = font_manager.FontProperties(fname=FONT_REG).get_name()
plt.rcParams.update({"font.family": FAMILY, "axes.unicode_minus": False,
                     "figure.facecolor": "white", "savefig.facecolor": "white"})

INK, MUTED, BLUE = "#222222", "#666666", "#2F5D8A"
LIGHT, EDGE, ACCENT = "#EDF2F7", "#B8C4D0", "#B22222"


def badge(fig, text="真实数据 · 2026-11-23", color=BLUE):
    fig.text(0.995, 0.008, text, ha="right", va="bottom", fontsize=9.5, color=color,
             bbox=dict(boxstyle="round,pad=0.32", fc="white", ec=color, lw=0.8), zorder=100)


def save(fig, name):
    p = os.path.join(BASE, name)
    fig.savefig(p, dpi=200, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    print(p)
    return p


def box(ax, x, y, w, h, title, body, fc=LIGHT, ec=EDGE, ts=12.5, bs=9.6):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=1.1))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="top",
            fontsize=ts, fontweight="bold", color=INK)
    if body:
        ax.text(x + w / 2, y + h / 2 - 0.14, body, ha="center", va="center",
                fontsize=bs, color=MUTED, linespacing=1.45)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, color="#7A8A99",
                                 linewidth=1.5, shrinkA=2, shrinkB=2))


def fig_data_flow():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(5, 9.65, "数据获取与落盘流程", ha="center", va="top", fontsize=18,
            fontweight="bold", color=INK)
    ax.text(5, 9.22, "实测：DMSC.csv 2,125,056 行 / 28 部；元数据 2,065 部，关联 28/28",
            ha="center", va="top", fontsize=10.2, color=MUTED)

    box(ax, 3.0, 7.55, 4.0, 1.20, "① 选题与数据需求",
        "目标：电影口碑“好在哪、差在哪”\n维度：D1—D8；数据量目标 ≥ 5,000")
    box(ax, 3.0, 5.75, 4.0, 1.22, "② 数据源组合",
        "DMSC v2：28 部 / 2,125,056 条 / 405.61 MB / CC0\n豆瓣电影元数据：2,065 部")
    box(ax, 3.0, 3.95, 4.0, 1.22, "③ Kaggle API 下载与解压",
        "kaggle datasets download … --unzip\n输出：work/data/raw/DMSC.csv + 元数据 CSV")
    box(ax, 3.0, 2.15, 4.0, 1.22, "④ 校验与关联",
        "行数/字段/星级/日期校验；中文名归一化关联\n匹配率 28/28（100%）")
    box(ax, 2.35, 0.35, 5.3, 1.25, "⑤ 分析用数据表",
        "filtered.csv.gz / sample_20k.csv\nmovie_agg.csv / category_agg.csv",
        fc="#E8F0E8", ec="#9DB39D")

    for y1, y2 in [(7.55, 6.97), (5.75, 5.17), (3.95, 3.37), (2.15, 1.60)]:
        arrow(ax, 5.0, y1, 5.0, y2)

    ax.text(7.25, 6.95, "2026-11-23 下载完成\nCC0 许可", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)
    ax.text(7.25, 5.15, "文件：405,610,647 字节\n10 个字段", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)
    ax.text(7.25, 3.35, "校验脚本：01_check_download.py\n日志：work/logs/", ha="left",
            va="center", fontsize=9.2, color=BLUE, linespacing=1.5)
    ax.text(7.25, 1.55, "关联：28/28（100%）\n别名匹配 2 部", ha="left", va="center",
            fontsize=9.2, color=BLUE, linespacing=1.5)
    badge(fig, "流程示意 · 数字为实测值")
    return save(fig, "fig_data_flow.png")


def fig_funnel():
    fig, ax = plt.subplots(figsize=(10.5, 7.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(5, 9.65, "数据过滤漏斗（全量实测）", ha="center", va="top", fontsize=18,
            fontweight="bold", color=INK)
    ax.text(5, 9.22, "宽度仅示意阶段顺序；条数与保留率为真实运行结果（N0 → N5）",
            ha="center", va="top", fontsize=10.0, color=MUTED)

    stages = [
        ("原始评论", "2,125,056 条（100%）", 7.6),
        ("完全/近似去重", "1,907,956 条（89.78%）", 7.0),
        ("广告/水印/联系方式", "1,902,920 条（89.55%）", 6.4),
        ("非中文/无信息短文本", "1,854,090 条（87.25%）", 5.8),
        ("想看/模板/无关", "1,847,982 条（86.96%）", 5.2),
        ("最终可用", "1,829,442 条（86.09%）", 4.6),
    ]
    top, h, gap = 8.35, 1.06, 0.20
    colors = ["#DCE6F0", "#D5E1EC", "#CDDBE8", "#C5D5E4", "#BDCFDF", "#B5C9DB"]
    for i, (label, count, w) in enumerate(stages):
        x0 = 5 - w / 2
        y0 = top - i * (h + gap)
        poly = Polygon([[x0, y0], [x0 + w, y0], [x0 + w - 0.35, y0 - h], [x0 + 0.35, y0 - h]],
                       closed=True, facecolor=colors[i], edgecolor="#8FA3B5", linewidth=1.0)
        ax.add_patch(poly)
        ax.text(5, y0 - h / 2 + 0.16, label, ha="center", va="center",
                fontsize=11.5, fontweight="bold", color=INK)
        ax.text(5, y0 - h / 2 - 0.20, count, ha="center", va="center", fontsize=8.8,
                color=MUTED)
        ax.text(x0 + w + 0.25, y0 - h / 2, f"N{i}", ha="left", va="center",
                fontsize=9.2, color="#7A8A99")

    ax.text(5, 0.55, "实测：保留 1,829,442 条（86.09%）；剧透标记 20,715 条（1.13%），"
                     "场外标记 112,360 条（6.14%）；误杀率待人工抽检。",
            ha="center", va="center", fontsize=9.2, color=MUTED)
    badge(fig)
    return save(fig, "fig_filter_funnel.png")


def fig_classification():
    fig, ax = plt.subplots(figsize=(13, 6.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis("off")
    ax.text(7, 6.65, "评论分类与聚合流程（已跑通）", ha="center", va="top", fontsize=18,
            fontweight="bold", color=INK)
    ax.text(7, 6.22, "L0 规则已处理 1,829,442 条；抽样 19,954 条用于校验；gold 300 待标注",
            ha="center", va="top", fontsize=10.0, color=MUTED)

    boxes = [
        (0.4, 4.35, 2.9, 1.35, "清洗文本", "去空白/控制符\n保留原始短评\n长度截断至 300 字"),
        (3.9, 4.35, 3.0, 1.35, "分类识别", "L0 关键词/正则\n9 类多标签\n最多保留 3 个"),
        (7.6, 4.35, 2.9, 1.35, "多标签输出", "C0—C8 + 主标签\nsent_star / sent_text\n20k 抽样带标签"),
        (11.1, 4.35, 2.5, 1.35, "聚合指标", "movie_agg（28 行）\ncategory_agg（252 行）\n气泡矩阵 / 桑基"),
    ]
    for x, y, w, h, title, body in boxes:
        box(ax, x, y, w, h, title, body, ts=11.8, bs=8.8)
    for x1 in (3.3, 6.9, 10.5):
        arrow(ax, x1, 5.02, x1 + 0.55, 5.02)

    box(ax, 3.9, 2.55, 3.0, 1.15, "人工标注 gold 300",
        "100 条双标 → Cohen's kappa\n目标 ≥ 0.60；尚未开始",
        fc="#FBF3E4", ec="#D8C39A", ts=11.0, bs=8.6)
    box(ax, 7.6, 2.55, 2.9, 1.15, "评估指标",
        "每类 P/R/F1、macro-F1\n规则覆盖率 63.25%",
        fc="#FBF3E4", ec="#D8C39A", ts=11.0, bs=8.6)
    arrow(ax, 5.4, 3.70, 5.4, 4.30)
    arrow(ax, 9.05, 3.70, 9.05, 4.30)

    ax.text(7, 1.45, "关键约束：分类是多标签问题；“整体评价”不能吞掉具体维度；未命中任何维度的评论归 C8。",
            ha="center", va="center", fontsize=9.6, color="#555555")
    ax.text(7, 0.95, "已生成分类与聚合结果；覆盖率=非 C8 评论占比；kappa、macro-F1 待标注后回填。",
            ha="center", va="center", fontsize=9.2, color=BLUE)
    badge(fig, "流程示意 · 分类已运行")
    return save(fig, "fig_classification_flow.png")


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    for p in (fig_data_flow(), fig_funnel(), fig_classification()):
        print(p)
