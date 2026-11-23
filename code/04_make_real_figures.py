# -*- coding: utf-8 -*-
"""用真实聚合结果重绘 5 张图：散点、气泡矩阵、雷达、桑基、联动原型。

输入：work/processed/movie_agg.csv、category_agg.csv、stats.json、sample_20k.csv
输出：work/figures/real_scatter.png / real_matrix.png / real_radar.png
      real_sankey.png / real_linked.png
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb, rgb_to_hsv, hsv_to_rgb
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
PROC = os.path.join(BASE, "work", "processed")
FIG = os.path.join(BASE, "work", "figures")
FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

font_manager.fontManager.addfont(FONT_REG)
font_manager.fontManager.addfont(FONT_BOLD)
FAMILY = font_manager.FontProperties(fname=FONT_REG).get_name()

plt.rcParams.update({
    "font.family": FAMILY,
    "font.size": 10.5,
    "axes.unicode_minus": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#CCCCCC",
})

CATS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
CAT_FULL = ["C0 整体评价", "C1 剧情叙事", "C2 表演角色", "C3 视听特效", "C4 音乐音效",
            "C5 导演风格", "C6 主题情感", "C7 场外体验", "C8 其他/无信息"]
CAT_SHORT = ["C0\n整体", "C1\n剧情", "C2\n表演", "C3\n视听", "C4\n音乐",
             "C5\n导演", "C6\n主题", "C7\n场外", "C8\n其他"]
SENT_NAMES = ["正面", "中性", "负面"]
SENT_COLORS = ["#2E8B57", "#8C8C8C", "#C0392B"]
POS_CMAP = LinearSegmentedColormap.from_list("pos", ["#C0392B", "#F4F4F4", "#1F6FB2"])

SELECTED = "栀子花开"


def load():
    mv = pd.read_csv(os.path.join(PROC, "movie_agg.csv"))
    ca = pd.read_csv(os.path.join(PROC, "category_agg.csv"))
    sm = pd.read_csv(os.path.join(PROC, "sample_20k.csv"))
    with open(os.path.join(PROC, "stats.json"), encoding="utf-8") as f:
        st = json.load(f)
    return mv, ca, sm, st


def badge(fig, text="真实数据 · DMSC v2 · 2026-11-23"):
    fig.text(0.995, 0.008, text, ha="right", va="bottom", fontsize=9.5,
             color="#1F6FB2",
             bbox=dict(boxstyle="round,pad=0.32", fc="white", ec="#1F6FB2", lw=0.8))


def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=200, bbox_inches="tight", pad_inches=0.16)
    plt.close(fig)
    print(p)
    return p


def lighten(color, t):
    r, g, b = to_rgb(color)
    h, s, v = rgb_to_hsv((r, g, b))
    s = min(0.72, s)
    v = 0.42 + 0.53 * float(np.clip(t, 0, 1))
    return hsv_to_rgb((h, s, v))


def bubble(n, lo, hi, s_lo=70, s_hi=1100):
    n = np.asarray(n, float)
    if hi <= lo:
        return np.full_like(n, s_lo)
    return s_lo + (n - lo) / (hi - lo) * (s_hi - s_lo)


# ---------------------------------------------------------------------------
# 1 口碑—争议散点
# ---------------------------------------------------------------------------
def fig_scatter(mv, st):
    fig, ax = plt.subplots(figsize=(10.5, 7.4))
    fig.subplots_adjust(left=0.11, right=0.87, top=0.80, bottom=0.20)
    sizes = bubble(mv["n_valid"], mv["n_valid"].min(), mv["n_valid"].max(), 80, 1150)
    sc = ax.scatter(mv["avg_star"], mv["star_std"], s=sizes, c=mv["pos_rate"],
                    cmap=POS_CMAP, vmin=0, vmax=1, edgecolors="white",
                    linewidths=1.2, alpha=0.92, zorder=3)

    xm, ym = mv["avg_star"].median(), mv["star_std"].median()
    ax.axvline(xm, color="#9A9A9A", lw=1.0, ls=(0, (4, 4)), zorder=1)
    ax.axhline(ym, color="#9A9A9A", lw=1.0, ls=(0, (4, 4)), zorder=1)

    offsets = {
        "栀子花开": (14, 2), "长城": (10, -2), "西游伏妖篇": (12, -12),
        "九层妖塔": (-10, 10), "小时代1": (10, -18), "疯狂动物城": (-10, -6),
        "你的名字": (-12, -14), "大圣归来": (10, 12), "夏洛特烦恼": (10, 4),
        "后会无期": (-12, -16), "寻龙诀": (8, -14), "何以笙箫默": (10, 2),
    }
    for _, r in mv.iterrows():
        if r["movie"] not in offsets:
            continue
        dx, dy = offsets[r["movie"]]
        ax.annotate(r["movie"], (r["avg_star"], r["star_std"]), xytext=(dx, dy),
                    textcoords="offset points", fontsize=10 if r["movie"] != SELECTED else 11,
                    color="#222222", fontweight="bold" if r["movie"] == SELECTED else "normal",
                    ha="left" if dx > 0 else "right",
                    bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.82),
                    zorder=5)
    sel = mv[mv["movie"] == SELECTED].iloc[0]
    ax.scatter([sel["avg_star"]], [sel["star_std"]], s=320, facecolors="none",
               edgecolors="#111111", linewidths=1.6, zorder=6)

    ax.set_xlabel("平均星级（口碑）", fontsize=11.5)
    ax.set_ylabel("星级标准差（争议度）", fontsize=11.5)
    ax.tick_params(labelsize=10)
    ax.grid(color="#EEEEEE", lw=0.7, zorder=0)
    ax.set_title("口碑—争议散点气泡图（真实数据）", fontsize=15.5, fontweight="bold", pad=0,
                 y=1.11)
    ax.text(0.5, 1.035, f"DMSC v2：{st['rows_filtered']:,} 条有效短评｜28 部电影｜"
                        "X=平均星级｜Y=星级标准差｜大小=评论量｜颜色=正面率｜虚线=中位数",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=9.2, color="#555555")
    cb = fig.colorbar(sc, ax=ax, fraction=0.032, pad=0.02)
    cb.set_label("正面率（4—5 星占比）", fontsize=9.5)
    cb.ax.tick_params(labelsize=9)

    handles = [ax.scatter([], [], s=bubble(v, mv.n_valid.min(), mv.n_valid.max(), 80, 1150),
                          c="none", edgecolors="#999999", lw=0.9,
                          label=f"{v/10000:.0f}万")
               for v in (30000, 80000, 130000)]
    fig.legend(handles=handles, title="气泡大小 = 评论量", loc="lower center", ncol=3,
               frameon=False, fontsize=9.5, title_fontsize=9.5,
               bbox_to_anchor=(0.47, 0.01), columnspacing=1.8)
    badge(fig)
    return save(fig, "real_scatter.png")


# ---------------------------------------------------------------------------
# 2 电影 × 类别 气泡矩阵
# ---------------------------------------------------------------------------
def draw_matrix(ax, mv, dim_rows=None, selected=None, labels=True):
    names = mv["movie"].tolist()
    n = len(names)
    share = mv[[f"share_{c}" for c in CATS]].to_numpy()
    pos = mv[[f"posrate_{c}" for c in CATS]].to_numpy()
    smax = np.percentile(share, 98)
    for i in range(n):
        for j in range(9):
            alpha, edge, lw = 1.0, "white", 0.7
            if dim_rows is not None and i != selected:
                alpha, edge, lw = 0.16, "#F2F2F2", 0.4
            base = 26 if labels else 60
            scale = 780 if labels else 900
            ax.scatter(j, i, s=base + min(share[i, j] / smax, 1) * scale,
                       c=[pos[i, j]], cmap=POS_CMAP, vmin=0, vmax=1,
                       edgecolors=edge, linewidths=lw, alpha=alpha, zorder=3)
    ax.set_xlim(-0.62, 8.62)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xticks(range(9))
    ax.set_xticklabels(CAT_SHORT, fontsize=9.2 if labels else 10.2, linespacing=1.25)
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", top=True, labeltop=True, bottom=False, labelbottom=False,
                   length=0, pad=6)
    ax.set_yticks(range(n))
    if labels:
        ax.set_yticklabels([f"{r.movie}  {r.avg_star:.1f}" for _, r in mv.iterrows()],
                           fontsize=9.2)
    else:
        ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0, pad=6)
    ax.grid(axis="x", color="#E8E8E8", lw=0.8, zorder=0)
    ax.grid(axis="y", color="#F3F3F3", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)


def fig_matrix(mv, st):
    mv = mv.sort_values("avg_star", ascending=False).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.5, 9.6))
    fig.subplots_adjust(left=0.23, right=0.88, top=0.80, bottom=0.07)
    draw_matrix(ax, mv)
    fig.suptitle("电影 × 类别 气泡矩阵（真实数据）", fontsize=15.5, fontweight="bold", y=0.975)
    fig.text(0.5, 0.912, "气泡面积=类别提及占比｜颜色=该类别正面率｜纵轴按平均星级从高到低",
             ha="center", va="bottom", fontsize=10, color="#555555")
    fig.text(0.5, 0.878, f"DMSC v2 全量 {st['rows_filtered']:,} 条有效短评，"
                         f"C0—C8 由关键词规则多标签识别（最多 3 个）",
             ha="center", va="bottom", fontsize=9.2, color="#8A4B08")
    sm = plt.cm.ScalarMappable(cmap=POS_CMAP, norm=Normalize(0, 1))
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.026, pad=0.02)
    cb.set_label("该类别正面率", fontsize=10)
    cb.ax.tick_params(labelsize=9)
    cb.outline.set_edgecolor("#DDDDDD")
    badge(fig)
    return save(fig, "real_matrix.png")


# ---------------------------------------------------------------------------
# 3 六维雷达
# ---------------------------------------------------------------------------
def fig_radar(mv, ca, st):
    labels = ["剧情", "表演", "视听", "音乐", "导演", "主题"]
    cats = ["C1", "C2", "C3", "C4", "C5", "C6"]
    sub = ca[ca["movie"] == SELECTED].set_index("category")
    movie_vals = np.array([sub.loc[c, "score"] for c in cats], float)
    overall = []
    for c in cats:
        g = ca[ca["category"] == c]
        overall.append((g["score"] * g["mention_cnt"]).sum() / g["mention_cnt"].sum())
    overall = np.array(overall, float)

    angles = np.linspace(0, 2 * np.pi, 6, endpoint=False).tolist()
    angles += angles[:1]
    mv_ = np.r_[movie_vals, movie_vals[0]]
    ov_ = np.r_[overall, overall[0]]

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

    ax.plot(angles, mv_, color="#1F6FB2", lw=2.8, label=f"《{SELECTED}》", zorder=3)
    ax.fill(angles, mv_, color="#1F6FB2", alpha=0.16, zorder=2)
    ax.plot(angles, ov_, color="#E15759", lw=2.2, ls=(0, (5, 3)), label="全库平均", zorder=3)
    ax.fill(angles, ov_, color="#E15759", alpha=0.07, zorder=1)
    ax.scatter(angles[:-1], movie_vals, color="#1F6FB2", s=42, zorder=4)
    ax.scatter(angles[:-1], overall, color="#E15759", s=28, zorder=4)
    ax.legend(loc="upper right", bbox_to_anchor=(1.33, 1.14), frameon=False, fontsize=11)

    fig.suptitle(f"六维画像：{SELECTED} vs 全库平均（真实数据）", fontsize=16.5,
                 fontweight="bold", y=0.98)
    fig.text(0.5, 0.915, "分值=该类别评论平均星级映射到 0—100｜全库平均按提及量加权",
             ha="center", va="bottom", fontsize=10, color="#555555")
    fig.text(0.12, 0.09, "越靠外=该类平均星级越高；虚线=全库平均\n"
                         f"样本：《{SELECTED}》{int(mv[mv.movie == SELECTED].n_valid.iloc[0]):,} 条",
             fontsize=9.2, color="#777777", linespacing=1.5)
    badge(fig)
    return save(fig, "real_radar.png")


# ---------------------------------------------------------------------------
# 4 类别 → 情感 桑基
# ---------------------------------------------------------------------------
def flow_patch(ax, x0, y0, x1, y1, h, color, alpha=0.42):
    verts = [(x0, y0), (x0 + 0.28, y0), (x1 - 0.28, y1), (x1, y1),
             (x1, y1 - h), (x1 - 0.28, y1 - h), (x0 + 0.28, y0 - h), (x0, y0 - h),
             (x0, y0)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
             Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none",
                           alpha=alpha, zorder=1))


def fmt_count(v):
    return f"{v/10000:.1f}万" if v >= 10000 else f"{v:.0f}"


def fig_sankey(st, sm):
    totals = np.array([st["cat_mentions"][c] for c in CATS], float)
    split = np.zeros((9, 3), float)
    for j, c in enumerate(CATS):
        m = sm["labels"].fillna("").str.contains(c, regex=False)
        cnt = sm.loc[m, "sent_star"].value_counts()
        p = cnt.get("正面", 0) / max(len(sm.loc[m]), 1)
        n = cnt.get("负面", 0) / max(len(sm.loc[m]), 1)
        split[j] = [p, max(1 - p - n, 0), n]
    flows = totals[:, None] * split

    left_tot = flows.sum(1)
    right_tot = flows.sum(0)
    gap_l = left_tot.sum() * 0.022
    gap_r = left_tot.sum() * 0.055
    height = left_tot.sum() + gap_l * 8

    lpos, cur = [], height
    for t in left_tot:
        lpos.append((cur, cur - t))
        cur -= t + gap_l
    rpos, cur = [], height
    for t in right_tot:
        rpos.append((cur, cur - t))
        cur -= t + gap_r

    fig, ax = plt.subplots(figsize=(11, 7.2))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.86, bottom=0.06)
    ax.set_xlim(0, 1)
    ax.set_ylim(-height * 0.03, height * 1.05)
    ax.axis("off")
    x0, x1, x2, x3 = 0.14, 0.19, 0.81, 0.86
    lc = [t for t, _ in lpos]
    rc = [t for t, _ in rpos]
    for i in range(9):
        for j in range(3):
            h = flows[i, j]
            if h <= 0:
                continue
            flow_patch(ax, x1, lc[i], x2, rc[j], h, SENT_COLORS[j])
            lc[i] -= h
            rc[j] -= h

    for i, (top, bottom) in enumerate(lpos):
        ax.add_patch(Rectangle((x0, bottom), x1 - x0, top - bottom, facecolor="#E6E6E6",
                               edgecolor="#999999", lw=0.7, zorder=3))
        ax.text(x0 - 0.012, (top + bottom) / 2,
                f"{CAT_FULL[i]}  {fmt_count(left_tot[i])}", ha="right", va="center",
                fontsize=9.8, color="#222222")
    for j, (top, bottom) in enumerate(rpos):
        ax.add_patch(Rectangle((x2, bottom), x3 - x2, top - bottom,
                               facecolor=lighten(SENT_COLORS[j], 0.55),
                               edgecolor=SENT_COLORS[j], lw=0.9, zorder=3))
        ax.text(x3 + 0.012, (top + bottom) / 2, f"{SENT_NAMES[j]}\n{fmt_count(right_tot[j])}",
                ha="left", va="center", fontsize=11.0, color=SENT_COLORS[j],
                fontweight="bold", linespacing=1.35)

    ax.text(0.5, 1.02, "类别 → 情感：观众在哪个维度上满意或不满意（真实数据）",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=15.5, fontweight="bold")
    ax.text(0.5, 0.972, "流宽=提及量｜颜色=情感极性｜情感按星级判定；类别可多标签，合计大于总量",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=10, color="#555555")
    badge(fig)
    return save(fig, "real_sankey.png")


# ---------------------------------------------------------------------------
# 5 联动原型
# ---------------------------------------------------------------------------
def fig_linked(mv, st):
    mv = mv.sort_values("avg_star", ascending=False).reset_index(drop=True)
    sel_i = int(mv.index[mv.movie == SELECTED][0])
    fig = plt.figure(figsize=(10.5, 9.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.55], hspace=0.58,
                          left=0.13, right=0.90, top=0.88, bottom=0.07)
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])

    sizes = bubble(mv["n_valid"], mv["n_valid"].min(), mv["n_valid"].max(), 40, 420)
    ax1.scatter(mv["avg_star"], mv["star_std"], s=sizes, c=mv["pos_rate"], cmap=POS_CMAP,
                vmin=0, vmax=1, edgecolors="white", linewidths=0.8, alpha=0.9, zorder=3)
    sel = mv.iloc[sel_i]
    ax1.scatter([sel.avg_star], [sel.star_std], s=220, facecolors="none",
                edgecolors="#111111", linewidths=1.5, zorder=5)
    ax1.annotate(f"{SELECTED}（已选中）", (sel.avg_star, sel.star_std), xytext=(8, -16),
                 textcoords="offset points", fontsize=9.5, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
    ax1.set_xlabel("平均星级", fontsize=10)
    ax1.set_ylabel("星级标准差", fontsize=10)
    ax1.tick_params(labelsize=8.5)
    ax1.grid(color="#EEEEEE", lw=0.6)
    for s in ("top", "right"):
        ax1.spines[s].set_visible(False)
    ax1.set_title("① 顶部散点导航：先选一部电影", fontsize=11.5, fontweight="bold", loc="left")

    draw_matrix(ax2, mv, dim_rows=True, selected=sel_i, labels=False)
    ax2.add_patch(Rectangle((-0.55, sel_i - 0.45), 9.1, 0.9, fill=False,
                            edgecolor="#111111", lw=1.2, zorder=5))
    ax2.text(-0.78, len(mv) / 2, "28 部电影（按平均星级排序）", rotation=90,
             ha="center", va="center", fontsize=9, color="#666666")
    ax2.set_title("② 下方类别矩阵：看这部电影的评价结构", fontsize=11.5,
                  fontweight="bold", loc="left", pad=14)

    fig.suptitle("散点导航与矩阵联动（真实数据渲染）", fontsize=15.5, fontweight="bold", y=0.965)
    fig.text(0.5, 0.925, f"点击上方气泡 → 下方对应行高亮｜数据：DMSC v2 {st['rows_filtered']:,} 条"
                         "有效短评｜交互为原型设计", ha="center", va="bottom",
             fontsize=9.6, color="#555555")
    badge(fig)
    return save(fig, "real_linked.png")


def main():
    os.makedirs(FIG, exist_ok=True)
    mv, ca, sm, st = load()
    fig_scatter(mv, st)
    fig_matrix(mv, st)
    fig_radar(mv, ca, st)
    fig_sankey(st, sm)
    fig_linked(mv, st)


if __name__ == "__main__":
    main()
