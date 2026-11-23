# -*- coding: utf-8 -*-
"""生成电影评论可视化方案对比图（合成示意数据）。"""

import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, to_rgb, rgb_to_hsv, hsv_to_rgb
from matplotlib.patches import Rectangle, PathPatch, ConnectionPatch, Patch
from matplotlib.path import Path
from matplotlib.ticker import PercentFormatter
from PIL import Image, ImageDraw, ImageFont

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from config import (ROOT, DATA, RAW, PROCESSED, LOGS, PREVIEW,
                    FIGURES, FIG_PLAN, FIG_DOC, FIG_SHOT, DOCS, WEB,
                    FONT_CJK, FONT_CJK_BOLD, FONT_MONO)
BASE = str(FIG_PLAN)
FONT_REG = FONT_CJK
FONT_BOLD = FONT_CJK_BOLD

font_manager.fontManager.addfont(FONT_REG)
font_manager.fontManager.addfont(FONT_BOLD)
FONT_FAMILY = font_manager.FontProperties(fname=FONT_REG).get_name()

plt.rcParams.update({
    "font.family": FONT_FAMILY,
    "font.size": 11.5,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": "#222222",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
})

# 13 部电影：名称、平均星级、星级标准差、评论量、正面率
MOVIES = [
    ("流浪地球2", 4.5, 0.95, 18000, 0.78),
    ("长安三万里", 4.6, 0.88, 14000, 0.83),
    ("宇宙探索编辑部", 4.6, 0.92, 9000, 0.81),
    ("封神第一部", 4.4, 1.08, 17000, 0.74),
    ("深海", 4.5, 1.18, 11000, 0.76),
    ("八角笼中", 4.2, 1.12, 13000, 0.68),
    ("满江红", 4.0, 1.28, 15000, 0.62),
    ("消失的她", 3.9, 1.46, 22000, 0.55),
    ("热烈", 3.9, 1.20, 10000, 0.58),
    ("孤注一掷", 3.8, 1.38, 20000, 0.52),
    ("好像也没那么热血沸腾", 3.8, 1.30, 7000, 0.50),
    ("学爸", 3.7, 1.26, 8000, 0.48),
    ("无名", 3.6, 1.52, 12000, 0.45),
]

CAT_SHORT = ["C0\n整体", "C1\n剧情", "C2\n表演", "C3\n视听", "C4\n音乐",
             "C5\n导演", "C6\n主题", "C7\n场外", "C8\n其他"]
CAT_FULL = ["C0 整体评价", "C1 剧情叙事", "C2 表演角色", "C3 视听特效", "C4 音乐音效",
            "C5 导演风格", "C6 主题情感", "C7 场外体验", "C8 其他/无信息"]
CAT_COLORS = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
              "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F"]
SENT_NAMES = ["正面", "中性", "负面"]
SENT_COLORS = ["#2E8B57", "#8C8C8C", "#C0392B"]

POS_CMAP = LinearSegmentedColormap.from_list(
    "pos_rate", ["#C0392B", "#F4F4F4", "#1F6FB2"]
)

NAMES = [m[0] for m in MOVIES]
AVG = np.array([m[1] for m in MOVIES])
STD = np.array([m[2] for m in MOVIES])
NCOM = np.array([m[3] for m in MOVIES], dtype=float)
POS = np.array([m[4] for m in MOVIES])

# 按平均星级从高到低排序，后续矩阵/堆叠条共用
ORDER = np.argsort(-AVG)
NAMES_S = [NAMES[i] for i in ORDER]
AVG_S = AVG[ORDER]
STD_S = STD[ORDER]
NCOM_S = NCOM[ORDER]
POS_S = POS[ORDER]

rng = np.random.default_rng(20261123)
BASE_SHARE = np.array([0.34, 0.22, 0.13, 0.11, 0.05, 0.06, 0.14, 0.05, 0.03])
SHARE = rng.dirichlet(BASE_SHARE * 12, size=len(MOVIES))
SHARE = SHARE / SHARE.sum(axis=1, keepdims=True)
SHARE_S = SHARE[ORDER]
MENTIONS_S = SHARE_S * NCOM_S[:, None]
POS_CELL = np.clip(
    POS_S[:, None] + rng.normal(0, 0.07, (len(MOVIES), 9)) +
    np.array([0.02, 0.00, -0.01, 0.01, 0.00, 0.00, 0.02, -0.08, 0.00]),
    0.18, 0.95
)

SELECTED = "流浪地球2"
SEL_IDX = NAMES_S.index(SELECTED)


def stamp(fig):
    fig.text(
        0.995, 0.008, "示意，非真实数据", ha="right", va="bottom",
        fontsize=11, color="#B22222",
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#B22222", lw=0.8, alpha=0.95),
        zorder=100,
    )


def save(fig, filename):
    path = os.path.join(BASE, filename)
    fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    return path


def bubble_size(n, n_min=7000, n_max=22000, s_min=90, s_max=1100):
    return s_min + (np.asarray(n, dtype=float) - n_min) / (n_max - n_min) * (s_max - s_min)


def lighten(color, t):
    r, g, b = to_rgb(color)
    h, s, v = rgb_to_hsv((r, g, b))
    s = min(0.72, s)
    v = 0.42 + 0.53 * float(np.clip(t, 0, 1))
    return hsv_to_rgb((h, s, v))


def clean_ax(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#CCCCCC")


# ---------------------------------------------------------------------------
# 方案一：口碑—争议散点气泡图
# ---------------------------------------------------------------------------
def fig_scatter():
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.subplots_adjust(left=0.09, right=0.88, top=0.80, bottom=0.20)

    sizes = bubble_size(NCOM)
    sc = ax.scatter(AVG, STD, s=sizes, c=POS, cmap=POS_CMAP, vmin=0, vmax=1,
                    edgecolors="white", linewidths=1.2, alpha=0.92, zorder=3)

    x_med, y_med = np.median(AVG), np.median(STD)
    ax.axvline(x_med, color="#9A9A9A", lw=1.0, ls=(0, (4, 4)), zorder=1)
    ax.axhline(y_med, color="#9A9A9A", lw=1.0, ls=(0, (4, 4)), zorder=1)

    quad = [
        (0.015, 0.975, "低分高争议\n话题 / 烂片", "left", "top"),
        (0.985, 0.975, "高分高争议\n两极神作", "right", "top"),
        (0.015, 0.025, "低分低争议\n平庸", "left", "bottom"),
        (0.985, 0.025, "高分低争议\n稳健佳作", "right", "bottom"),
    ]
    for x, y, text, ha, va in quad:
        ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=10.5,
                color="#777777", linespacing=1.5,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="none", alpha=0.78),
                zorder=2)

    offsets = {
        "流浪地球2": (-14, -20), "长安三万里": (12, -14), "宇宙探索编辑部": (-14, 16),
        "封神第一部": (12, 8), "深海": (12, 10), "八角笼中": (-12, 10),
        "满江红": (12, 8), "消失的她": (12, 10), "热烈": (-16, -22),
        "孤注一掷": (-12, 8), "好像也没那么热血沸腾": (12, -20),
        "学爸": (-12, -16), "无名": (12, 8),
    }
    for name, x, y in zip(NAMES, AVG, STD):
        dx, dy = offsets.get(name, (10, 8))
        label_text = name.replace("好像也没那么热血沸腾", "好像也没那么\n热血沸腾")
        ax.annotate(label_text, (x, y), xytext=(dx, dy), textcoords="offset points",
                    fontsize=8.2 if len(name) >= 8 else 9.2, color="#222222",
                    ha="left" if dx > 0 else "right", va="center", linespacing=1.0,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.72),
                    zorder=4)

    ax.set_xlim(3.45, 4.78)
    ax.set_ylim(0.72, 1.66)
    ax.set_xlabel("平均星级（口碑）", fontsize=12.5, labelpad=8)
    ax.set_ylabel("星级标准差（争议度）", fontsize=12.5, labelpad=8)
    ax.tick_params(labelsize=11)
    ax.grid(color="#EEEEEE", lw=0.7, zorder=0)
    clean_ax(ax)
    ax.set_title("方案一｜口碑—争议散点气泡图", fontsize=17, fontweight="bold", pad=0, y=1.12)
    ax.text(0.5, 1.04, "X=平均星级｜Y=星级标准差｜气泡大小=评论量｜颜色=正面率",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=10.5, color="#555555")

    cbar = fig.colorbar(sc, ax=ax, fraction=0.032, pad=0.02)
    cbar.set_label("正面率（4—5 星占比）", fontsize=10.5)
    cbar.ax.tick_params(labelsize=9.5)

    handles = [
        ax.scatter([], [], s=bubble_size(v), c="none", edgecolors="#999999",
                   linewidths=0.9, label=f"{v // 1000}k")
        for v in (8000, 14000, 22000)
    ]
    fig.legend(handles=handles, title="气泡大小 = 评论量", loc="lower center",
               ncol=3, frameon=False, fontsize=10, title_fontsize=10,
               bbox_to_anchor=(0.48, 0.01), columnspacing=2.0)

    stamp(fig)
    return save(fig, "01_方案一_口碑争议散点气泡.png")


# ---------------------------------------------------------------------------
# 方案二：电影 × 类别 气泡矩阵（主推）
# ---------------------------------------------------------------------------
def draw_matrix(ax, dim_rows=None, selected_row=None):
    n, k = MENTIONS_S.shape
    max_m = MENTIONS_S.max()
    for i in range(n):
        for j in range(k):
            s = 24 + (MENTIONS_S[i, j] / max_m) * 820
            alpha = 1.0
            edge = "white"
            lw = 0.8
            if dim_rows is not None and i != selected_row:
                alpha = 0.20
                edge = "#F2F2F2"
                lw = 0.4
            ax.scatter(j, i, s=s, c=[POS_CELL[i, j]], cmap=POS_CMAP, vmin=0, vmax=1,
                       edgecolors=edge, linewidths=lw, alpha=alpha, zorder=3)
    ax.set_xlim(-0.62, 8.62)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xticks(range(k))
    ax.set_xticklabels(CAT_SHORT, fontsize=9.5, linespacing=1.3)
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False,
                   length=0, pad=8)
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{name}  {star:.1f}" for name, star in zip(NAMES_S, AVG_S)],
                       fontsize=10)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.grid(axis="x", color="#E8E8E8", lw=0.8, zorder=0)
    ax.grid(axis="y", color="#F3F3F3", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)


def fig_matrix():
    fig, ax = plt.subplots(figsize=(13, 8.5))
    fig.subplots_adjust(left=0.21, right=0.88, top=0.80, bottom=0.10)
    draw_matrix(ax)

    fig.suptitle("方案二（主推）｜电影 × 类别 气泡矩阵", fontsize=17,
                 fontweight="bold", y=0.975)
    fig.text(0.5, 0.915, "气泡面积=提及量｜颜色=该类别正面率｜纵轴按平均星级从高到低",
             ha="center", va="bottom", fontsize=10.2, color="#555555")
    fig.text(0.5, 0.875, "主推理由：一部电影一行，能同时比较“评价维度结构”和“每个维度的口碑”。",
             ha="center", va="bottom", fontsize=9.6, color="#8A4B08")

    sm = plt.cm.ScalarMappable(cmap=POS_CMAP, norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.02)
    cbar.set_label("该类别正面率", fontsize=10.5)
    cbar.ax.tick_params(labelsize=9.5)
    cbar.outline.set_edgecolor("#DDDDDD")

    stamp(fig)
    return save(fig, "02_方案二_电影类别气泡矩阵.png")


# ---------------------------------------------------------------------------
# 方案三：六维雷达画像（替代横向堆叠条，避免条形图形态）
# ---------------------------------------------------------------------------
def fig_radar():
    labels = ["剧情", "表演", "视听", "音乐", "导演", "主题"]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    movie_vals = np.array([86, 78, 92, 74, 88, 95], dtype=float)
    avg_vals = np.array([70, 72, 68, 65, 66, 74], dtype=float)
    mv = np.r_[movie_vals, movie_vals[0]]
    av = np.r_[avg_vals, avg_vals[0]]

    fig = plt.figure(figsize=(9.6, 8.2))
    ax = fig.add_subplot(111, polar=True)
    fig.subplots_adjust(left=0.10, right=0.78, top=0.80, bottom=0.10)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=13.5)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=9, color="#999999")
    ax.set_rlabel_position(30)
    ax.grid(color="#E8E8E8", lw=0.8)
    ax.spines["polar"].set_color("#DDDDDD")

    ax.plot(angles, mv, color="#1F6FB2", lw=2.8, label=f"《{SELECTED}》", zorder=3)
    ax.fill(angles, mv, color="#1F6FB2", alpha=0.16, zorder=2)
    ax.plot(angles, av, color="#E15759", lw=2.2, ls=(0, (5, 3)),
            label="全库平均", zorder=3)
    ax.fill(angles, av, color="#E15759", alpha=0.07, zorder=1)
    ax.scatter(angles[:-1], movie_vals, color="#1F6FB2", s=42, zorder=4)
    ax.scatter(angles[:-1], avg_vals, color="#E15759", s=28, zorder=4)

    ax.legend(loc="upper right", bbox_to_anchor=(1.33, 1.14), frameon=False, fontsize=11)
    fig.suptitle("方案三｜六维画像：一部电影 vs 全库平均", fontsize=17,
                 fontweight="bold", y=0.98)
    fig.text(0.5, 0.915, "分值=该类别评论平均星级映射到 0—100（非文本情感）｜合成示意",
             ha="center", va="bottom", fontsize=10.2, color="#555555")
    fig.text(0.12, 0.10, "越靠外 = 该类别平均星级越高；虚线=全库平均",
             fontsize=9.8, color="#777777")

    stamp(fig)
    return save(fig, "03_方案三_六维画像雷达.png")


# ---------------------------------------------------------------------------
# 方案四：类别 → 情感 桑基图
# ---------------------------------------------------------------------------
def flow_patch(ax, x0, y0, x1, y1, h, color, alpha=0.45):
    verts = [
        (x0, y0), (x0 + 0.28, y0), (x1 - 0.28, y1), (x1, y1),
        (x1, y1 - h), (x1 - 0.28, y1 - h), (x0 + 0.28, y0 - h), (x0, y0 - h),
        (x0, y0),
    ]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none",
                           alpha=alpha, zorder=1))


def fmt_count(v):
    if v >= 10000:
        return f"{v / 10000:.1f}万"
    return f"{v:.0f}"


def fig_sankey():
    pos = POS_CELL
    neg = (1 - pos) * 0.55
    neu = np.clip(1 - pos - neg, 0, 1)
    sent_share = np.stack([pos, neu, neg], axis=2)  # 13 x 9 x 3
    flows = (MENTIONS_S[:, :, None] * sent_share).sum(axis=0)  # 9 x 3

    left_totals = flows.sum(axis=1)
    right_totals = flows.sum(axis=0)
    left_gap = left_totals.sum() * 0.012
    right_gap = left_totals.sum() * 0.060
    height = max(left_totals.sum() + left_gap * 8,
                 right_totals.sum() + right_gap * 2)

    left_pos = []
    cur = height
    for t in left_totals:
        left_pos.append((cur, cur - t))
        cur -= t + left_gap
    right_pos = []
    cur = height
    for t in right_totals:
        right_pos.append((cur, cur - t))
        cur -= t + right_gap

    fig, ax = plt.subplots(figsize=(13, 7.5))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.86, bottom=0.06)
    ax.set_xlim(0, 1)
    ax.set_ylim(-height * 0.03, height * 1.05)
    ax.axis("off")

    x0, x1 = 0.14, 0.19
    x2, x3 = 0.81, 0.86
    left_cursor = [top for top, _ in left_pos]
    right_cursor = [top for top, _ in right_pos]

    for i in range(len(CAT_SHORT)):
        for j in range(3):
            h = flows[i, j]
            if h <= 0:
                continue
            y0 = left_cursor[i]
            y1 = right_cursor[j]
            flow_patch(ax, x1, y0, x2, y1, h, SENT_COLORS[j], alpha=0.42)
            left_cursor[i] -= h
            right_cursor[j] -= h

    for i, (top, bottom) in enumerate(left_pos):
        ax.add_patch(Rectangle((x0, bottom), x1 - x0, top - bottom,
                               facecolor="#E6E6E6", edgecolor="#999999", lw=0.7, zorder=3))
        ax.text(x0 - 0.012, (top + bottom) / 2, f"{CAT_FULL[i]}  {fmt_count(left_totals[i])}",
                ha="right", va="center", fontsize=9.8, color="#222222")
    for j, (top, bottom) in enumerate(right_pos):
        ax.add_patch(Rectangle((x2, bottom), x3 - x2, top - bottom,
                               facecolor=lighten(SENT_COLORS[j], 0.55),
                               edgecolor=SENT_COLORS[j], lw=0.9, zorder=3))
        ax.text(x3 + 0.012, (top + bottom) / 2, f"{SENT_NAMES[j]}\n{fmt_count(right_totals[j])}",
                ha="left", va="center", fontsize=10.5, color=SENT_COLORS[j],
                fontweight="bold", linespacing=1.35)

    ax.text(0.5, 1.02, "方案四｜类别 → 情感：观众在哪个维度上满意或不满意",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=17, fontweight="bold")
    ax.text(0.5, 0.975, "流宽=提及量｜颜色=情感极性｜左右节点高度按总量缩放",
            transform=ax.transAxes, ha="center", va="bottom",
            fontsize=10.5, color="#555555")

    stamp(fig)
    return save(fig, "04_方案四_类别情感桑基图.png")


# ---------------------------------------------------------------------------
# 方案五：散点导航 + 类别矩阵联动
# ---------------------------------------------------------------------------
def fig_linked():
    fig = plt.figure(figsize=(13, 10))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 2.9], hspace=0.55,
                          left=0.21, right=0.88, top=0.86, bottom=0.06)
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1])

    sizes = bubble_size(NCOM_S, s_min=60, s_max=520)
    ax_top.scatter(AVG_S, STD_S, s=sizes, c=POS_S, cmap=POS_CMAP, vmin=0, vmax=1,
                   edgecolors="#999999", linewidths=0.6, alpha=0.38, zorder=2)
    ax_top.scatter([AVG_S[SEL_IDX]], [STD_S[SEL_IDX]], s=[sizes[SEL_IDX]],
                   c=[POS_S[SEL_IDX]], cmap=POS_CMAP, vmin=0, vmax=1,
                   edgecolors="#111111", linewidths=1.8, zorder=4)
    ax_top.annotate(f"已选：{SELECTED}", (AVG_S[SEL_IDX], STD_S[SEL_IDX]),
                    xytext=(10, 12), textcoords="offset points", fontsize=10,
                    fontweight="bold", color="#111111",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#B22222", lw=0.8),
                    zorder=5)
    ax_top.set_xlim(3.45, 4.78)
    ax_top.set_ylim(0.72, 1.66)
    ax_top.set_xlabel("平均星级（口碑）", fontsize=10.5, labelpad=4)
    ax_top.set_ylabel("星级标准差", fontsize=10.5, labelpad=4)
    ax_top.tick_params(labelsize=9)
    ax_top.grid(color="#EFEFEF", lw=0.6, zorder=0)
    clean_ax(ax_top)
    ax_top.text(0.0, 1.035, "① 顶部散点导航：先选一部电影",
                transform=ax_top.transAxes, ha="left", va="bottom",
                fontsize=12, fontweight="bold", color="#333333")
    ax_top.text(0.99, 0.96, "颜色=正面率", transform=ax_top.transAxes,
                ha="right", va="top", fontsize=9, color="#666666")

    ax_bot.axhspan(SEL_IDX - 0.5, SEL_IDX + 0.5, color="#FFF1C9", alpha=0.55, zorder=0)
    draw_matrix(ax_bot, dim_rows="all", selected_row=SEL_IDX)
    ax_bot.get_yticklabels()[SEL_IDX].set_fontweight("bold")
    ax_bot.get_yticklabels()[SEL_IDX].set_color("#8A4B08")

    sm = plt.cm.ScalarMappable(cmap=POS_CMAP, norm=plt.Normalize(0, 1))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax_bot, fraction=0.024, pad=0.02)
    cbar.set_label("该类别正面率", fontsize=9.5)
    cbar.ax.tick_params(labelsize=8.5)
    cbar.outline.set_edgecolor("#DDDDDD")

    fig.text(0.21, 0.595, "② 下方类别矩阵：看这部电影的评价结构",
             ha="left", va="bottom", fontsize=12, fontweight="bold", color="#333333")

    ax_top.annotate("", xy=(AVG_S[SEL_IDX], 0.73),
                    xytext=(AVG_S[SEL_IDX], STD_S[SEL_IDX]),
                    arrowprops=dict(arrowstyle="-|>", color="#B22222", lw=1.5,
                                    shrinkA=10, shrinkB=0), zorder=6)
    ax_top.text(AVG_S[SEL_IDX] + 0.03, 0.80, "下方高亮", color="#B22222",
                fontsize=9, ha="left", va="bottom")

    fig.suptitle("方案五｜散点导航 + 类别矩阵联动", fontsize=17,
                 fontweight="bold", y=0.975)
    fig.text(0.5, 0.935, "点击顶部气泡 → 下方矩阵高亮对应电影；右侧详情接雷达/词云/评论列表",
             ha="center", va="bottom", fontsize=10.2, color="#555555")

    stamp(fig)
    return save(fig, "05_方案五_散点导航与矩阵联动.png")


# ---------------------------------------------------------------------------
# 总览图
# ---------------------------------------------------------------------------
def make_overview(paths):
    W, H = 3000, 2520
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT_BOLD, 56)
    f_sub = ImageFont.truetype(FONT_REG, 28)
    f_cell = ImageFont.truetype(FONT_BOLD, 32)
    f_body = ImageFont.truetype(FONT_REG, 25)
    f_small = ImageFont.truetype(FONT_REG, 22)

    draw.text((W // 2, 36), "电影评论可视化：五套方案总览", font=f_title,
              fill="#111111", anchor="ma")
    draw.text((W // 2, 108), "以电影短评语料为主体数据，比较信息密度、可读性与交互潜力（合成示意）",
              font=f_sub, fill="#666666", anchor="ma")

    margin_x, margin_top = 58, 168
    gap_x, gap_y = 46, 34
    cell_w = (W - 2 * margin_x - gap_x) // 2
    cell_h = (H - margin_top - 54 - 2 * gap_y) // 3

    titles = [
        "① 导航：口碑—争议散点",
        "② 主视图：电影 × 类别矩阵（主推）",
        "③ 详情：六维画像",
        "④ 辅助：类别 → 情感",
        "⑤ 原型：选片与下钻联动",
    ]
    captions = [
        "回答“先看哪部”：口碑、争议、热度、正面率一屏对比。",
        "回答“强在哪、弱在哪”：每部电影九类提及量与类别口碑。",
        "回答“这一部哪里强”：六维画像对比全库均值。",
        "回答“满意流向哪”：类别到正/中/负的情感分流。",
        "回答“怎么下钻”：顶部选片，下方矩阵联动。",
    ]

    for i, path in enumerate(paths):
        row, col = divmod(i, 2)
        x = margin_x + col * (cell_w + gap_x)
        y = margin_top + row * (cell_h + gap_y)
        draw.text((x + 6, y), titles[i], font=f_cell, fill="#1A1A1A")
        img = Image.open(path).convert("RGB")
        max_w, max_h = cell_w - 16, cell_h - 74
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        ix = x + (cell_w - img.width) // 2
        iy = y + 48 + (max_h - img.height) // 2
        canvas.paste(img, (ix, iy))
        draw.text((x + 6, y + cell_h - 22), captions[i], font=f_small, fill="#777777")

    # 第六格：结论与拍板建议
    row, col = divmod(5, 2)
    x = margin_x + col * (cell_w + gap_x)
    y = margin_top + row * (cell_h + gap_y)
    draw.text((x + 6, y), "结论｜建议怎么拍板", font=f_cell, fill="#8A4B08")
    lines = [
        "1. 主推方案二：电影 × 类别矩阵，信息最全，适合作为主视图。",
        "2. 方案一做首页导航：先决定“先看哪部”。",
        "3. 方案三做影片详情：六维画像对比全库均值。",
        "4. 方案四讲情感流向：解释“观众为什么满意/不满意”。",
        "5. 方案五做交互原型：顶部选片，下方矩阵联动。",
        "",
        "组合建议：方案一（导航）+ 方案二（主视图）+ 方案五（联动）。",
        "方案三、方案四作为详情页/分析页的辅助视图。",
    ]
    yy = y + 54
    for line in lines:
        draw.text((x + 10, yy), line, font=f_body, fill="#333333")
        yy += 38

    # 水印
    draw.rounded_rectangle([W - 360, H - 64, W - 38, H - 22], radius=9,
                           outline="#B22222", width=2, fill="white")
    draw.text((W - 199, H - 43), "示意，非真实数据", font=f_small, fill="#B22222",
              anchor="mm")

    out = os.path.join(BASE, "00_五方案总览.png")
    canvas.save(out, quality=95)
    return out


if __name__ == "__main__":
    os.makedirs(BASE, exist_ok=True)
    paths = [
        fig_scatter(),
        fig_matrix(),
        fig_radar(),
        fig_sankey(),
        fig_linked(),
    ]
    overview = make_overview(paths)
    print("generated:")
    for p in paths + [overview]:
        print(p)
