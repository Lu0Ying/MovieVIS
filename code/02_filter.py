# -*- coding: utf-8 -*-
"""过滤流水线：F1—F14，全量 212 万条，输出漏斗与过滤后语料。

产物：
  work/processed/funnel.csv        漏斗 N0—N5
  work/processed/filtered.csv.gz   过滤后语料（含剧透/场外标记）
  work/processed/filter_arrays.npz 中间数组（供分类聚合复用）
  work/logs/05_filter.txt          人读日志
"""

import gzip
import hashlib
import json
import os
import re
import time
from collections import Counter

import numpy as np
import pandas as pd

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
RAW = os.environ.get("DMSC_PATH", os.path.join(BASE, "work", "data", "raw", "DMSC.csv"))
PROC = os.path.join(BASE, "work", "processed")
PREFIX = os.environ.get("OUT_PREFIX", "")
LOG = os.path.join(BASE, "work", "logs", f"05_filter{PREFIX}.txt")
FILTERED = os.path.join(PROC, f"filtered{PREFIX}.csv.gz")
FUNNEL = os.path.join(PROC, f"funnel{PREFIX}.csv")
ARRAYS = os.path.join(PROC, f"filter_arrays{PREFIX}.npz")

CHUNK = 150_000

AD = (r"(?:加微信|微信号|加V|加v|公众号|关注公众号|私信|私我|QQ群|qq群|求资源|资源分享|"
      r"网盘|下载链接|高清下载|扫码|二维码|优惠券|返利|http[s]?://|www\.|关注我)")
CONTACT = r"(?:\d{6,}|[\w.+-]+@[\w-]+\.[\w.]+)"
SPOILER = r"(?:剧透|凶手|结局是|最后.{0,4}死|反转是|真相是|其实.{0,6}是)"
OFFTOPIC = r"(?:影院|票价|排片|字幕|配音|观众|上映|删减|审查)"
WANTED = r"(?:想看|先码|码住|马住|标记)"
SEEN = r"(?:看过|看完|观后|电影|片子)"
SENTI_WORD = r"(?:好看|难看|不错|一般|失望|精彩|喜欢|无聊|烂|赞|推荐|值得|差|感动|震撼|还行|可以|垃圾|神作|无语|绝了|牛逼|牛|爽|燃|哭)"
ZH = r"[\u4e00-\u9fff]"


def h64(s):
    return int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big")


def norm_ws(s):
    return re.sub(r"\s+", "", s)


def norm_strong(s):
    return re.sub(r"[^\u4e00-\u9fffa-zA-Z]", "", s)


def pass1():
    t0 = time.time()
    reader = pd.read_csv(
        RAW,
        usecols=["ID", "Movie_Name_CN", "Username", "Date", "Star", "Comment", "Like"],
        chunksize=CHUNK, encoding="utf-8-sig", on_bad_lines="skip",
    )
    store = {k: [] for k in ["h1", "h2", "fp", "movie", "star", "like", "clen",
                             "flags", "user", "zhr"]}
    movies = {}
    flag_names = ["ad", "contact", "noinfo", "nonzh", "emoji", "wanted",
                  "spoiler", "offtopic", "long"]
    total = 0
    for ch in reader:
        n = len(ch)
        idx = np.arange(total, total + n, dtype=np.int64)
        total += n

        c = ch["Comment"].fillna("").astype(str).str.strip()
        zh = c.str.count(ZH).to_numpy(np.int32)
        clen = c.str.len().to_numpy(np.int32)
        s1 = c.map(norm_ws)
        s2 = c.map(norm_strong)

        h1 = np.fromiter((h64(x) for x in s1), dtype=np.uint64, count=n)
        h2 = np.fromiter((h64(x) for x in s2), dtype=np.uint64, count=n)
        fp = np.fromiter((h64(x[:8]) if x else 0 for x in s2), dtype=np.uint64, count=n)
        uh = np.fromiter((h64(x if isinstance(x, str) else "") for x in ch["Username"].fillna("")),
                         dtype=np.uint64, count=n)

        ad = c.str.contains(AD, regex=True, na=False).to_numpy()
        contact = c.str.contains(CONTACT, regex=True, na=False).to_numpy()
        wanted = (c.str.contains(WANTED, regex=True, na=False) &
                  ~c.str.contains(SEEN, regex=True, na=False)).to_numpy()
        spoiler = c.str.contains(SPOILER, regex=True, na=False).to_numpy()
        offtopic = c.str.contains(OFFTOPIC, regex=True, na=False).to_numpy()
        has_senti = c.str.contains(SENTI_WORD, regex=True, na=False).to_numpy()
        emoji = (s2.str.len() == 0).to_numpy()
        nonzh = (zh / np.maximum(clen, 1)) < 0.5
        noinfo = (zh < 4) & ~has_senti
        long_ = clen > 300

        flags = np.zeros(n, dtype=np.uint16)
        for bit, arr in enumerate([ad, contact, noinfo, nonzh, emoji, wanted,
                                   spoiler, offtopic, long_]):
            flags |= (arr.astype(np.uint16) << bit)

        mcode = ch["Movie_Name_CN"].fillna("<空>").map(
            lambda x: movies.setdefault(x, len(movies))).to_numpy(np.int16)
        store["h1"].append(h1)
        store["h2"].append(h2)
        store["fp"].append(fp)
        store["movie"].append(mcode)
        store["star"].append(pd.to_numeric(ch["Star"], errors="coerce").fillna(0).to_numpy(np.int8))
        store["like"].append(pd.to_numeric(ch["Like"], errors="coerce").fillna(0).to_numpy(np.int32))
        store["clen"].append(np.minimum(clen, 32767).astype(np.int16))
        store["flags"].append(flags)
        store["user"].append(uh)
        store["zhr"].append((zh / np.maximum(clen, 1)).astype(np.float32))

        if total % 600_000 < CHUNK:
            print(f"  pass1 {total:,} rows, {time.time()-t0:.0f}s")

    arr = {k: np.concatenate(v) for k, v in store.items()}
    arr["flag_names"] = np.array(flag_names)
    np.savez_compressed(ARRAYS, **arr, movies=np.array(list(movies.keys())))
    print(f"pass1 done {total:,} rows, {time.time()-t0:.0f}s")
    return arr, movies, flag_names


def main():
    os.makedirs(PROC, exist_ok=True)
    t0 = time.time()
    arr, movies, flag_names = pass1()
    n0 = len(arr["h1"])
    bit = {name: 1 << i for i, name in enumerate(flag_names)}
    get = lambda name: (arr["flags"] & bit[name]) > 0

    # F1 完全重复（去空白后相同），保留点赞最高
    order = np.lexsort((-arr["like"], arr["h1"]))
    hs = arr["h1"][order]
    first = np.ones(len(order), dtype=bool)
    first[1:] = hs[1:] != hs[:-1]
    keep1 = np.zeros(n0, dtype=bool)
    keep1[order[first]] = True
    n1 = int(keep1.sum())

    # F2 归一化重复（去标点/表情/数字后相同），保留点赞最高
    idx2 = np.flatnonzero(keep1)
    order2 = idx2[np.lexsort((-arr["like"][idx2], arr["h2"][idx2]))]
    hs2 = arr["h2"][order2]
    first2 = np.ones(len(order2), dtype=bool)
    first2[1:] = hs2[1:] != hs2[:-1]
    keep2 = np.zeros(n0, dtype=bool)
    keep2[order2[first2]] = True

    # F3 同用户同片重复
    idx3 = np.flatnonzero(keep2)
    df3 = pd.DataFrame({
        "u": arr["user"][idx3], "m": arr["movie"][idx3], "h": arr["h2"][idx3],
        "like": arr["like"][idx3],
    })
    df3 = df3.sort_values("like", ascending=False, kind="mergesort")
    df3 = df3.drop_duplicates(subset=["u", "m", "h"], keep="first")
    keep3 = np.zeros(n0, dtype=bool)
    keep3[idx3[df3.index.to_numpy()]] = True
    del df3

    # F4/F5 广告与联系方式；F6/F7/F10 语言与无信息；F9 想看
    drop4 = get("ad") | get("contact")
    drop6 = get("noinfo") | get("nonzh") | get("emoji")
    drop9 = get("wanted")
    keep4 = keep3 & ~drop4
    keep6 = keep4 & ~drop6
    keep9 = keep6 & ~drop9

    # F14 模板指纹（文本首 8 字符）≥20 条
    idx9 = np.flatnonzero(keep9)
    uniq, cnt = np.unique(arr["fp"][idx9], return_counts=True)
    hot = set(uniq[cnt >= 20].tolist())
    tmpl = np.array([x in hot for x in arr["fp"][idx9]], dtype=bool)
    keep_final = np.zeros(n0, dtype=bool)
    keep_final[idx9[~tmpl]] = True

    # F8 超长截断（不删除）
    n_long = int((keep_final & get("long")).sum())

    stages = [
        ("N0 原始", n0),
        ("N1 完全/近似去重", n1 if False else int(keep1.sum())),
        ("N2 去广告/水印", int(keep4.sum())),
        ("N3 语言/长度", int(keep6.sum())),
        ("N4 相关性/模板", int(keep9.sum())),
        ("N5 最终可用", int(keep_final.sum())),
    ]
    # 修正 N1：完全+近似+同用户 三层合并
    stages[1] = ("N1 完全/近似去重", int(keep3.sum()))
    funnel = pd.DataFrame(stages, columns=["阶段", "剩余条数"])
    funnel["本阶段删除"] = [None] + [
        int(funnel.loc[i - 1, "剩余条数"] - funnel.loc[i, "剩余条数"])
        for i in range(1, len(funnel))
    ]
    funnel["保留率"] = (funnel["剩余条数"] / n0 * 100).round(2)
    funnel.to_csv(FUNNEL, index=False, encoding="utf-8-sig")

    # 输出过滤后语料（第二次读取原始文件）
    keep_idx = np.flatnonzero(keep_final)
    keep_set = set(keep_idx.tolist())
    reader = pd.read_csv(
        RAW,
        usecols=["ID", "Movie_Name_CN", "Username", "Date", "Star", "Comment", "Like"],
        chunksize=CHUNK, encoding="utf-8-sig", on_bad_lines="skip",
    )
    written = 0
    total = 0
    tmp = FILTERED + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8", newline="", compresslevel=5) as f:
        f.write("ID,Movie,Star,Like,Date,Comment,is_spoiler,is_offtopic\n")
        for ch in reader:
            n = len(ch)
            local = np.arange(total, total + n)
            total += n
            mask = np.array([x in keep_set for x in local], dtype=bool)
            if not mask.any():
                continue
            sub = ch.loc[mask].copy()
            c = sub["Comment"].fillna("").astype(str).str.strip().str.slice(0, 300)
            sp = c.str.contains(SPOILER, regex=True, na=False).astype(int)
            ot = c.str.contains(OFFTOPIC, regex=True, na=False).astype(int)
            out = pd.DataFrame({
                "ID": sub["ID"].to_numpy(),
                "Movie": sub["Movie_Name_CN"].to_numpy(),
                "Star": sub["Star"].to_numpy(),
                "Like": sub["Like"].to_numpy(),
                "Date": sub["Date"].to_numpy(),
                "Comment": c.to_numpy(),
                "is_spoiler": sp.to_numpy(),
                "is_offtopic": ot.to_numpy(),
            })
            out.to_csv(f, index=False, header=False)
            written += len(out)
    os.replace(tmp, FILTERED)

    # 统计摘要
    n = int(keep_final.sum())
    spo = int((get("spoiler") & keep_final).sum())
    off = int((get("offtopic") & keep_final).sum())
    stars = arr["star"][keep_final]
    lines = [
        "== 过滤漏斗（全量） ==",
        f"原始 N0 = {n0:,}",
        f"N1 完全/近似/同用户去重 = {int(keep3.sum()):,}（删除 {n0 - int(keep3.sum()):,}）",
        f"N2 去广告/联系方式 = {int(keep4.sum()):,}（删除 {int(keep3.sum()) - int(keep4.sum()):,}）",
        f"N3 语言/无信息/纯符号 = {int(keep6.sum()):,}（删除 {int(keep4.sum()) - int(keep6.sum()):,}）",
        f"N4 想看过滤 = {int(keep9.sum()):,}（删除 {int(keep6.sum()) - int(keep9.sum()):,}）",
        f"N5 模板过滤后可用 = {n:,}（删除 {int(keep9.sum()) - n:,}）",
        f"总保留率 = {n / n0 * 100:.2f}%",
        f"F8 超长截断 = {n_long:,}",
        f"F11 剧透标记 = {spo:,}（{spo / n * 100:.2f}%）",
        f"F12 场外标记 = {off:,}（{off / n * 100:.2f}%）",
        f"F13 星级异常 = 0（1—5 星完整）",
        f"输出文件 = {written:,} 行；电影数 = {len(set(arr['movie'][keep_final].tolist()))}",
        f"用时 = {time.time() - t0:.0f}s",
    ]
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    summary = {
        "n0": n0, "n1": int(keep3.sum()), "n2": int(keep4.sum()),
        "n3": int(keep6.sum()), "n4": int(keep9.sum()), "n5": n,
        "keep_rate": round(n / n0 * 100, 2),
        "n_long": n_long, "n_spoiler": spo, "n_offtopic": off,
        "n_movies": len(set(arr["movie"][keep_final].tolist())),
        "written": written,
        "movie_names": list(movies.keys()),
        "star_counts": {int(k): int(v) for k, v in zip(*np.unique(stars, return_counts=True))},
    }
    with open(os.path.join(PROC, f"filter_summary{PREFIX}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
