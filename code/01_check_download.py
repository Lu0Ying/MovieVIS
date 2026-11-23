# -*- coding: utf-8 -*-
"""下载校验：统计 DMSC 真实行数、字段、电影数、星级分布、文本特征与元数据覆盖率。

输出：
  work/logs/04_download_check.txt   人读日志
  work/processed/download_stats.json 机器可读统计
"""

import json
import os
import re
import hashlib
from collections import Counter

import numpy as np
import pandas as pd

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
RAW = os.path.join(BASE, "work", "data", "raw")
LOG = os.path.join(BASE, "work", "logs", "04_download_check.txt")
OUT = os.path.join(BASE, "work", "processed", "download_stats.json")

DMSC = os.path.join(RAW, "DMSC.csv")
META = os.path.join(RAW, "douban_all_movies.csv")

AD_PAT = (
    r"(加微信|微信号|加V|加v|公众号|关注公众号|私信|私我|QQ群|qq群|资源|网盘|下载链接|"
    r"高清下载|扫码|二维码|代理|代购|优惠券|返利|http[s]?://|www\.)"
)
ZH = r"[\u4e00-\u9fff]"


def pct(a, b):
    return round(a / b * 100, 2) if b else 0.0


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = []
    log = lines.append

    df_meta = pd.read_csv(META)
    log("== 元数据 douban_all_movies.csv ==")
    log(f"行数={len(df_meta)} 列数={df_meta.shape[1]}")
    log(f"字段={df_meta.columns.tolist()}")
    log(f"缺失率：rating={pct(df_meta['rating'].isna().sum(), len(df_meta))}% "
        f"genres={pct(df_meta['genres'].isna().sum(), len(df_meta))}% "
        f"directors={pct(df_meta['directors'].isna().sum(), len(df_meta))}%")

    meta_titles = set()
    for t in df_meta["title"].dropna().astype(str):
        meta_titles.add(re.sub(r"[\s《》·:：!！?？,，.。'\"-]", "", t).lower())

    usecols = ["ID", "Movie_Name_EN", "Movie_Name_CN", "Crawl_Date",
               "Number", "Username", "Date", "Star", "Comment", "Like"]
    reader = pd.read_csv(DMSC, usecols=usecols, chunksize=200_000,
                         encoding="utf-8-sig", on_bad_lines="skip")

    total = 0
    star_cnt = Counter()
    movie_cnt = Counter()
    crawl_cnt = Counter()
    date_min, date_max = None, None
    n_star_null = n_comment_null = n_user_null = n_like_null = 0
    n_ad = n_nonzh = 0
    n_dup = 0
    seen = set()
    lengths = []
    n_like_sum = 0

    for ch in reader:
        total += len(ch)
        s = ch["Star"]
        star_cnt.update(s.fillna(-1).astype(int).value_counts().to_dict())
        movie_cnt.update(ch["Movie_Name_CN"].fillna("<空>").value_counts().to_dict())
        crawl_cnt.update(ch["Crawl_Date"].astype(str).value_counts().to_dict())

        dt = pd.to_datetime(ch["Date"], errors="coerce")
        if dt.notna().any():
            lo, hi = dt.min(), dt.max()
            date_min = lo if date_min is None or lo < date_min else date_min
            date_max = hi if date_max is None or hi > date_max else date_max

        n_star_null += int(s.isna().sum() + (s == 0).sum())
        c = ch["Comment"].fillna("").astype(str)
        n_comment_null += int((c.str.strip() == "").sum())
        n_user_null += int(ch["Username"].isna().sum())
        n_like_null += int(ch["Like"].isna().sum())
        n_like_sum += int(pd.to_numeric(ch["Like"], errors="coerce").fillna(0).sum())

        n_ad += int(c.str.contains(AD_PAT, regex=True, na=False).sum())
        zh = c.str.count(ZH)
        ln = c.str.len().replace(0, np.nan)
        n_nonzh += int(((zh / ln).fillna(0) < 0.5).sum())
        lengths.append(ln.fillna(0).to_numpy(dtype=np.int32))

        norm = c.str.replace(r"\s+", "", regex=True)
        for text in norm:
            h = int.from_bytes(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")
            if h in seen:
                n_dup += 1
            else:
                seen.add(h)

    lengths = np.concatenate(lengths)
    movies_cn = [m for m in movie_cnt if m != "<空>"]
    norm_titles = {re.sub(r"[\s《》·:：!！?？,，.。'\"-]", "", m).lower() for m in movies_cn}
    matched = len(norm_titles & meta_titles)

    stats = {
        "dmsc_file_bytes": os.path.getsize(DMSC),
        "dmsc_rows": total,
        "dmsc_cols": len(usecols),
        "movies": len(movies_cn),
        "movie_counts": dict(movie_cnt.most_common()),
        "star_counts": {str(k): v for k, v in sorted(star_cnt.items())},
        "star_missing_or_zero": n_star_null,
        "date_min": str(date_min.date()) if date_min is not None else None,
        "date_max": str(date_max.date()) if date_max is not None else None,
        "crawl_dates": dict(crawl_cnt.most_common(5)),
        "comment_null": n_comment_null,
        "user_null": n_user_null,
        "like_null": n_like_null,
        "like_sum": n_like_sum,
        "dup_rows": n_dup,
        "ad_rows": n_ad,
        "nonzh_rows": n_nonzh,
        "len_mean": round(float(np.nanmean(lengths)), 2),
        "len_median": float(np.median(lengths)),
        "len_p95": float(np.percentile(lengths, 95)),
        "len_max": int(lengths.max()),
        "meta_rows": len(df_meta),
        "meta_matched_movies": matched,
        "meta_match_rate": pct(matched, len(movies_cn)),
    }

    log("")
    log("== 主数据 DMSC.csv ==")
    log(f"文件字节={stats['dmsc_file_bytes']:,} ({stats['dmsc_file_bytes']/1024/1024:.2f} MB)")
    log(f"真实行数={total:,} 字段数={len(usecols)} 电影数={len(movies_cn)}")
    log(f"评论日期范围={stats['date_min']} ~ {stats['date_max']}")
    log(f"抓取日期 Top5={stats['crawl_dates']}")
    log(f"星级缺失或为0={n_star_null:,} ({pct(n_star_null, total)}%)")
    log(f"星级分布={dict(sorted(star_cnt.items()))}")
    log(f"评论为空={n_comment_null:,} 用户名缺失={n_user_null:,} 点赞缺失={n_like_null:,}")
    log(f"完全重复（去空白后）={n_dup:,} ({pct(n_dup, total)}%)")
    log(f"广告/引流命中={n_ad:,} ({pct(n_ad, total)}%)")
    log(f"非中文占比(中文字符<50%)={n_nonzh:,} ({pct(n_nonzh, total)}%)")
    log(f"评论长度：均值={stats['len_mean']} 中位数={stats['len_median']} "
        f"P95={stats['len_p95']} 最大={stats['len_max']}")
    log(f"元数据匹配电影={matched}/{len(movies_cn)} ({stats['meta_match_rate']}%)")
    log("")
    log("每部电影评论数（前 10 / 后 5）：")
    items = movie_cnt.most_common()
    for name, n in items[:10]:
        log(f"  {name}: {n:,}")
    for name, n in items[-5:]:
        log(f"  {name}: {n:,}")

    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\n".join(lines))
    print(f"\n写入 {LOG}\n写入 {OUT}")


if __name__ == "__main__":
    main()
