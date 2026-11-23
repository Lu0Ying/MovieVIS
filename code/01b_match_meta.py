# -*- coding: utf-8 -*-
"""把 DMSC 的 28 部电影与豆瓣元数据匹配，输出关联表与覆盖率。"""

import difflib
import json
import os
import re

import pandas as pd

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
PROC = os.path.join(BASE, "work", "processed")
META = os.path.join(BASE, "work", "data", "raw", "douban_all_movies.csv")
OUT = os.path.join(PROC, "movie_meta_match.csv")

ALIAS = {
    "大圣归来": "西游记之大圣归来",
    "泰囧": "人再囧途之泰囧",
    "复仇者联盟": "复仇者联盟",
    "复仇者联盟2": "复仇者联盟2：奥创纪元",
    "钢铁侠1": "钢铁侠",
    "美国队长3": "美国队长3：内战",
    "变形金刚4": "变形金刚4：绝迹重生",
    "小时代1": "小时代",
    "小时代3": "小时代3：刺金时代",
    "西游降魔篇": "西游降魔篇",
    "西游伏妖篇": "西游伏妖篇",
    "栀子花开": "栀子花开",
    "何以笙箫默": "何以笙箫默",
}


def norm(s):
    return re.sub(r"[\s《》·:：!！?？,，.。'\"\-]", "", str(s)).lower()


def main():
    with open(os.path.join(PROC, "download_stats.json"), encoding="utf-8") as f:
        st = json.load(f)
    names = list(st["movie_counts"].keys())
    meta = pd.read_csv(META)
    meta["_n"] = meta["title"].map(norm)
    pool = meta["_n"].tolist()

    rows = []
    for n in names:
        key = norm(ALIAS.get(n, n))
        hit = meta[meta["_n"] == key]
        method = "exact"
        score = 1.0
        if hit.empty:
            cand = difflib.get_close_matches(key, pool, n=1, cutoff=0.72)
            if cand:
                hit = meta[meta["_n"] == cand[0]]
                method = "fuzzy"
                score = round(difflib.SequenceMatcher(None, key, cand[0]).ratio(), 3)
        if hit.empty:
            rows.append({"movie": n, "matched_title": "", "method": "unmatched",
                         "score": 0, "movie_id": None, "genres": "", "release_date": "",
                         "directors": "", "rating": None})
            continue
        r = hit.iloc[0]
        rows.append({
            "movie": n, "matched_title": r["title"], "method": method, "score": score,
            "movie_id": r["movie_id"], "genres": r["genres"],
            "release_date": r["release_date"], "directors": r["directors"],
            "rating": r["rating"],
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    ok = int((df["method"] != "unmatched").sum())
    print(f"匹配 {ok}/{len(df)}（{ok/len(df)*100:.1f}%）")
    print(df.to_string(index=False))
    print(OUT)


if __name__ == "__main__":
    main()
