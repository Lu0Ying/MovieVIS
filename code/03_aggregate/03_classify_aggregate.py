# -*- coding: utf-8 -*-
"""分类、情感、分层抽样与聚合：C0—C8 多标签 + 星级/文本双轨情感 + 气泡图指标。

输入：data/processed/filtered.csv.gz
输出：
  data/processed/sample_20k.csv        分层抽样（带标签，供人工校验/词云）
  data/processed/movie_agg.csv         28 行电影级指标
  data/processed/category_agg.csv      28×9 类别级指标
  data/processed/stats.json            文档回填所需全部实测值
  data/logs/06_classify.txt            人读日志
"""

import json
import os
import re
import time
from collections import Counter, defaultdict

import jieba
import numpy as np
import pandas as pd

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from config import (ROOT, DATA, RAW, PROCESSED, LOGS, PREVIEW,
                    FIGURES, FIG_PLAN, FIG_DOC, FIG_SHOT, DOCS, WEB,
                    FONT_CJK, FONT_CJK_BOLD, FONT_MONO)
BASE = str(ROOT)
PROC = str(PROCESSED)
PREFIX = os.environ.get("OUT_PREFIX", "")
FILTERED = os.environ.get("FILTERED_PATH", os.path.join(PROC, "filtered.csv.gz"))
SUMMARY = os.environ.get("FILTER_SUMMARY", os.path.join(PROC, "filter_summary.json"))
LOG = os.path.join(str(LOGS), f"06_classify{PREFIX}.txt")
CHUNK = 120_000

CATS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
CAT_NAMES = ["整体评价", "剧情叙事", "表演角色", "视听特效", "音乐音效",
             "导演风格", "主题情感", "场外体验", "其他/无信息"]

PATTERNS = {
    "C0": r"(?:好看|难看|不错|一般|失望|精彩|喜欢|无聊|烂|赞|推荐|值得|差|感动|震撼|还行|"
          r"可以|垃圾|神作|无语|绝了|牛逼|爽|燃|哭|爱了|不喜欢|不行|好看|难看)",
    "C1": r"(?:剧情|故事|剧本|情节|节奏|叙事|结尾|结局|主线|拖沓|逻辑|反转|改编|设定|桥段|"
          r"冲突|铺垫|线索|烂尾|流水账|细节)",
    "C2": r"(?:演技|演员|表演|角色|主角|配角|台词|人物|演得|诠释|塑造|面瘫|木讷|选角|表情)",
    "C3": r"(?:画面|特效|镜头|摄影|美术|色彩|视觉|3D|IMAX|质感|场景|构图|剪辑|打光|服化道|"
          r"动作戏|场面)",
    "C4": r"(?:音乐|配乐|歌曲|插曲|主题曲|音效|声音|BGM|bgm|旋律|配乐)",
    "C5": r"(?:导演|执导|风格|叙事手法|致敬|作者性|功力|把控|调度|野心|掌控)",
    "C6": r"(?:主题|价值|意义|情感|共鸣|治愈|压抑|内核|表达|感动|温暖|绝望|希望|人性|成长|"
          r"现实|立意|深度)",
    "C7": r"(?:影院|票价|排片|字幕|配音|观众|上映|删减|审查|万达|场次|退票|票补)",
    "C8": r"(?!)",  # 兜底类，不主动匹配
}

POS = (r"(?:好看|喜欢|推荐|精彩|感动|满意|值得|惊艳|震撼|温暖|治愈|不错|棒|赞|爱|燃|爽|"
       r"牛|神作|经典|完美|舒服|享受|上头|细腻|扎实|惊喜|高级|流畅|深刻|真诚|可爱|美|强|"
       r"笑|哭|震撼|泪目|燃爆|入股)")
NEG = (r"(?:难看|失望|无聊|烂|差|垃圾|尴尬|拖沓|混乱|肤浅|生硬|尬|恶心|不行|无语|浪费|"
       r"糟糕|平庸|俗套|做作|崩|劝退|后悔|难受|讨厌|烦|假|空洞|敷衍|槽点|毛病|硬伤|扑街|"
       r"灾难|毁|烂尾|圈钱|难看|不好看|不喜欢|不推荐|不值得|没意思|无感|不好|不满意|不精彩)")

STOP = set("的了是我你他她它我们你们他们这那就都很也还又再才已经不过而且还但是因为所以如果"
           "一个一部一种什么怎么这个那个这样那样自己觉得感觉真的非常特别比较有点一些电影片子"
           "没有不是就是可以还是只是虽然然后时候东西地方".split())
STOP |= set("，。！？、；：“”‘’（）《》…—,.!?;:\"'()<>[]{}~` ")

SAMPLE_N = 20_000


def cat_counts(series):
    return np.vstack([series.str.count(PATTERNS[c]).to_numpy(np.int16) for c in CATS])  # 9×n


def main():
    t0 = time.time()
    with open(SUMMARY, encoding="utf-8") as f:
        fsum = json.load(f)
    movies = fsum["movie_names"]
    midx = {m: i for i, m in enumerate(movies)}
    nm = len(movies)

    # 第一遍：分层配额
    grp = Counter()
    total = 0
    for ch in pd.read_csv(FILTERED, usecols=["Movie", "Star"], chunksize=300_000):
        total += len(ch)
        grp.update(ch.groupby(["Movie", "Star"]).size().to_dict())
    quota = {}
    for k, n in grp.items():
        quota[k] = max(3, int(round(SAMPLE_N * n / total)))
    print(f"分层 {len(grp)} 组，配额合计 {sum(quota.values())}, 用时 {time.time()-t0:.0f}s")

    # 第二遍：分类、情感、聚合、抽样
    n = np.zeros(nm, np.int64)
    star_sum = np.zeros(nm, np.float64)
    star_sq = np.zeros(nm, np.float64)
    pos_star = np.zeros(nm, np.int64)
    neg_star = np.zeros(nm, np.int64)
    cat_mention = np.zeros((nm, 9), np.int64)
    cat_star = np.zeros((nm, 9), np.float64)
    cat_pos = np.zeros((nm, 9), np.int64)
    cat_neg = np.zeros((nm, 9), np.int64)
    cat_overall = np.zeros(9, np.int64)

    sent_star_tot = 0
    sent_text_tot = 0
    agree = 0
    sent_text_dist = Counter()
    text_pos_tot = text_neg_tot = 0

    rng = np.random.default_rng(20261123)
    samples = []
    sample_taken = Counter()
    qprob = {}

    burst = 0
    for ch in pd.read_csv(FILTERED, chunksize=CHUNK):
        ch = ch.dropna(subset=["Movie", "Star", "Comment"])
        if ch.empty:
            continue
        m = ch["Movie"].map(midx).fillna(-1).to_numpy(np.int64)
        star = ch["Star"].to_numpy(np.float64)
        text = ch["Comment"].fillna("").astype(str)
        nloc = len(ch)

        cnt = cat_counts(text)            # 9×n
        ment = cnt > 0
        ment[8] = ~ment[:8].any(axis=0)   # C8 = 无任何具体维度的兜底
        n += np.bincount(m, minlength=nm)
        star_sum += np.bincount(m, weights=star, minlength=nm)
        star_sq += np.bincount(m, weights=star ** 2, minlength=nm)
        pos_star += np.bincount(m[star >= 4], minlength=nm)
        neg_star += np.bincount(m[star <= 2], minlength=nm)

        for j in range(9):
            mj = ment[j]
            cat_overall[j] += int(mj.sum())
            cat_mention[:, j] += np.bincount(m[mj], minlength=nm)
            cat_star[:, j] += np.bincount(m[mj], weights=star[mj], minlength=nm)
            cat_pos[:, j] += np.bincount(m[mj & (star >= 4)], minlength=nm)
            cat_neg[:, j] += np.bincount(m[mj & (star <= 2)], minlength=nm)

        # 文本情感（词典 + 否定式复合词已含于 NEG）
        ph = text.str.count(POS).to_numpy(np.int16)
        nh = text.str.count(NEG).to_numpy(np.int16)
        score = ph - nh
        sent_text = np.where(score >= 1, 1, np.where(score <= -1, -1, 0))
        text_pos_tot += int((sent_text == 1).sum())
        text_neg_tot += int((sent_text == -1).sum())
        sent_text_dist.update(pd.Series(sent_text).value_counts().to_dict())

        st = np.where(star >= 4, 1, np.where(star <= 2, -1, 0))
        mask = sent_text != 0
        sent_star_tot += int(mask.sum())
        agree += int((sent_text[mask] == st[mask]).sum())

        # 分层抽样
        keys = list(zip(ch["Movie"].to_numpy(), ch["Star"].to_numpy()))
        keep = np.zeros(nloc, dtype=bool)
        for i, k in enumerate(keys):
            if sample_taken[k] >= quota.get(k, 0):
                continue
            p = qprob.get(k)
            if p is None:
                p = min(1.0, quota.get(k, 0) / max(grp.get(k, 1), 1) * 1.15)
                qprob[k] = p
            if rng.random() < p:
                keep[i] = True
        if keep.any():
            sub = ch.loc[keep].copy()
            sub["sent_text"] = pd.Series(sent_text[keep], index=sub.index).map(
                {1: "正面", -1: "负面", 0: "中性"})
            sub["sent_star"] = pd.Series(st[keep], index=sub.index).map(
                {1: "正面", -1: "负面", 0: "中性"})
            for i in np.flatnonzero(keep):
                sample_taken[keys[i]] += 1
            samples.append(sub)

        burst += 1
        if burst % 3 == 0:
            print(f"  pass2 {burst*CHUNK:,} rows, {time.time()-t0:.0f}s")

    sample = pd.concat(samples, ignore_index=True)

    # 截断到配额（按组随机裁剪）
    sample["_k"] = list(zip(sample["Movie"], sample["Star"]))
    parts = []
    for k, g in sample.groupby("_k"):
        q = quota.get(k, 3)
        if len(g) > q:
            g = g.sample(n=q, random_state=20261123)
        parts.append(g)
    sample = pd.concat(parts, ignore_index=True).drop(columns=["_k"])

    # 样本多标签
    def labels_of(t):
        cnt = np.array([len(re.findall(PATTERNS[c], t)) for c in CATS])
        hit = np.flatnonzero(cnt > 0)
        if len(hit) == 0:
            return "C8", "C8"
        top = hit[np.argsort(-cnt[hit])][:3]
        labs = "|".join(CATS[i] for i in sorted(top))
        primary = "C0" if cnt[0] > 0 else CATS[int(top[0])]
        return labs, primary

    lab = sample["Comment"].fillna("").map(labels_of)
    sample["labels"] = [x[0] for x in lab]
    sample["primary"] = [x[1] for x in lab]
    sample.to_csv(os.path.join(PROC, f"sample_20k{PREFIX}.csv"), index=False, encoding="utf-8-sig")

    # 词表（样本内，按类别）
    words = {c: Counter() for c in CATS}
    for t, labs in zip(sample["Comment"].fillna(""), sample["labels"]):
        toks = [w for w in jieba.cut(re.sub(r"[^\u4e00-\u9fff]", "", t))
                if len(w) >= 2 and w not in STOP]
        for c in labs.split("|"):
            words[c].update(toks)
    top_words = {c: "、".join([w for w, _ in words[c].most_common(12)]) for c in CATS}

    # 聚合表
    movie_rows = []
    cat_rows = []
    with np.errstate(invalid="ignore", divide="ignore"):
        for i, mv in enumerate(movies):
            nn = n[i]
            avg = star_sum[i] / nn
            std = np.sqrt(max(star_sq[i] / nn - avg ** 2, 0))
            p = pos_star[i] / nn
            q = neg_star[i] / nn
            shares = cat_mention[i] / nn
            ent = -np.sum([x * np.log(x) for x in shares if x > 0])
            div = ent / np.log(9)
            row = {
                "movie": mv, "n_valid": int(nn), "avg_star": round(avg, 3),
                "star_std": round(std, 3), "pos_rate": round(p, 4),
                "neg_rate": round(q, 4), "polarization": round(4 * p * q, 4),
                "diversity": round(div, 4), "top_category": CATS[int(np.argmax(shares))],
            }
            for j, c in enumerate(CATS):
                row[f"share_{c}"] = round(float(shares[j]), 4)
                cs = cat_mention[i, j]
                row[f"mention_{c}"] = int(cs)
                row[f"posrate_{c}"] = round(float(cat_pos[i, j] / cs), 4) if cs else 0
                score = (cat_star[i, j] / cs - 1) / 4 * 100 if cs else 0
                row[f"score_{c}"] = round(float(score), 2)
            movie_rows.append(row)
            for j, c in enumerate(CATS):
                cs = cat_mention[i, j]
                cat_rows.append({
                    "movie": mv, "category": c, "category_name": CAT_NAMES[j],
                    "mention_cnt": int(cs), "share": round(float(shares[j]), 4),
                    "avg_star": round(float(cat_star[i, j] / cs), 3) if cs else 0,
                    "pos_rate": round(float(cat_pos[i, j] / cs), 4) if cs else 0,
                    "score": round(float((cat_star[i, j] / cs - 1) / 4 * 100), 2) if cs else 0,
                    "top_words": top_words[c],
                })

    movie_df = pd.DataFrame(movie_rows).sort_values("avg_star", ascending=False)
    cat_df = pd.DataFrame(cat_rows)
    movie_df.to_csv(os.path.join(PROC, f"movie_agg{PREFIX}.csv"), index=False, encoding="utf-8-sig")
    cat_df.to_csv(os.path.join(PROC, f"category_agg{PREFIX}.csv"), index=False, encoding="utf-8-sig")

    # 统计汇总
    agreement = agree / sent_star_tot * 100 if sent_star_tot else 0
    stats = {
        "rows_filtered": int(n.sum()),
        "movies": nm,
        "sample_rows": int(len(sample)),
        "sent_text_agreement": round(agreement, 2),
        "sent_text_dist": {str(k): int(v) for k, v in sent_text_dist.items()},
        "text_pos": int(text_pos_tot), "text_neg": int(text_neg_tot),
        "cat_mentions": {c: int(cat_overall[j]) for j, c in enumerate(CATS)},
        "cat_share": {c: round(float(cat_overall[j] / n.sum()), 4) for j, c in enumerate(CATS)},
        "top_movie_polarization": movie_df.sort_values("polarization", ascending=False)
                                 .head(5)[["movie", "n_valid", "avg_star", "polarization"]]
                                 .to_dict("records"),
        "top_movie_n": movie_df.sort_values("n_valid", ascending=False)
                            .head(5)[["movie", "n_valid", "avg_star", "star_std"]]
                            .to_dict("records"),
        "mean_star": round(float(star_sum.sum() / n.sum()), 3),
        "pos_rate": round(float(pos_star.sum() / n.sum()), 4),
        "neg_rate": round(float(neg_star.sum() / n.sum()), 4),
        "top_words": top_words,
        "elapsed": round(time.time() - t0, 1),
    }
    with open(os.path.join(PROC, f"stats{PREFIX}.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    lines = [
        "== 分类与聚合 ==",
        f"过滤后评论 = {int(n.sum()):,}；电影 = {nm}；抽样 = {len(sample):,}",
        f"平均星级 = {stats['mean_star']}；正面率 = {stats['pos_rate']*100:.2f}%；"
        f"负面率 = {stats['neg_rate']*100:.2f}%",
        f"星级/文本情感一致率 = {agreement:.2f}%（仅比较文本非中性的 {sent_star_tot:,} 条）",
        "各类别提及量：" + "，".join(f"{c}={stats['cat_mentions'][c]:,}" for c in CATS),
        "各类别占比：" + "，".join(f"{c}={stats['cat_share'][c]*100:.2f}%" for c in CATS),
        "争议度 Top5：",
    ]
    for r in stats["top_movie_polarization"]:
        lines.append(f"  {r['movie']}: n={r['n_valid']:,} 均星={r['avg_star']} "
                     f"争议度={r['polarization']}")
    lines.append("样本分类示例：")
    for _, r in sample.head(8).iterrows():
        lines.append(f"  [{r['primary']}] {r['Comment'][:50]} -> {r['labels']}")
    lines.append(f"用时 = {time.time() - t0:.0f}s")

    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
