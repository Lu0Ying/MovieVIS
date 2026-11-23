# -*- coding: utf-8 -*-
"""补充统计：日期解析失败率、噪声标记原始计数、每片评论数分位、元数据匹配。"""

import json
import os

import numpy as np
import pandas as pd

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
PROC = os.path.join(BASE, "work", "processed")

with open(os.path.join(PROC, "download_stats.json"), encoding="utf-8") as f:
    ds = json.load(f)
arr = np.load(os.path.join(PROC, "filter_arrays.npz"), allow_pickle=True)
flags = arr["flags"]
names = list(arr["flag_names"])
bit = {n: 1 << i for i, n in enumerate(names)}
get = lambda n: (flags & bit[n]) > 0

counts = ds["movie_counts"]
vals = np.array(list(counts.values()))

dates = pd.read_csv(os.path.join(BASE, "work", "data", "raw", "DMSC.csv"),
                    usecols=["Date"], encoding="utf-8-sig", on_bad_lines="skip")
bad = int(pd.to_datetime(dates["Date"], errors="coerce").isna().sum())

meta = pd.read_csv(os.path.join(PROC, "movie_meta_match.csv"))

extra = {
    "date_parse_fail": bad,
    "date_parse_fail_pct": round(bad / len(dates) * 100, 3),
    "flag_counts": {n: int(get(n).sum()) for n in names},
    "noinfo_not_nonzh": int((get("noinfo") & ~get("nonzh")).sum()),
    "emoji_only": int(get("emoji").sum()),
    "movie_min": int(vals.min()),
    "movie_median": int(np.median(vals)),
    "movie_max": int(vals.max()),
    "meta_match": int((meta["method"] != "unmatched").sum()),
    "meta_total": len(meta),
    "meta_exact": int((meta["method"] == "exact").sum()),
    "meta_fuzzy": int((meta["method"] == "fuzzy").sum()),
    "meta_alias": 0,
}
# 别名匹配行（匹配名与原名不同且 exact）
extra["meta_alias"] = int(((meta["method"] == "exact") &
                           (meta["movie"] != meta["matched_title"])).sum())

with open(os.path.join(PROC, "stats_extra.json"), "w", encoding="utf-8") as f:
    json.dump(extra, f, ensure_ascii=False, indent=2)
print(json.dumps(extra, ensure_ascii=False, indent=2))
