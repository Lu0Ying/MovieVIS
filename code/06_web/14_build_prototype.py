# -*- coding: utf-8 -*-
"""生成自包含交互原型 web/index.html（数据来自 data/processed 真实聚合结果）。"""

import json
import os
import pickle
import re
from collections import Counter, defaultdict

import jieba
import pandas as pd

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from config import (ROOT, DATA, RAW, PROCESSED, LOGS, PREVIEW,
                    FIGURES, FIG_PLAN, FIG_DOC, FIG_SHOT, DOCS, WEB,
                    FONT_CJK, FONT_CJK_BOLD, FONT_MONO)
BASE = str(ROOT)
PROC = str(PROCESSED)
OUT = str(WEB / "index.html")

CATS = ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
CAT_NAMES = ["整体评价", "剧情叙事", "表演角色", "视听特效", "音乐音效",
             "导演风格", "主题情感", "场外体验", "其他/无信息"]
CAT_SHORT = ["整体", "剧情", "表演", "视听", "音乐", "导演", "主题", "场外", "其他"]

with open(os.path.join(PROC, "stats.json"), encoding="utf-8") as f:
    ST = json.load(f)
with open(os.path.join(PROC, "filter_summary.json"), encoding="utf-8") as f:
    FS = json.load(f)

mv = pd.read_csv(os.path.join(PROC, "movie_agg.csv"))
ca = pd.read_csv(os.path.join(PROC, "category_agg.csv"))
sm = pd.read_csv(os.path.join(PROC, "sample_20k.csv"))

# 全库类别基准（按提及量加权）
gcat = {}
for c in CATS:
    g = ca[ca["category"] == c]
    m = g["mention_cnt"].sum()
    gcat[c] = {
        "pos": round(float((g["pos_rate"] * g["mention_cnt"]).sum() / m), 4),
        "avg": round(float((g["avg_star"] * g["mention_cnt"]).sum() / m), 3),
        "share": round(float(m / mv["n_valid"].sum()), 4),
        "score": round(float((g["score"] * g["mention_cnt"]).sum() / m), 1),
    }

# 类别 → 情感：抽样情感比例 × 全量提及量（同时按影片留存，供单片桑基用）
raw = {c: {"pos": 0, "neu": 0, "neg": 0} for c in CATS}
rawm = {}
for _, r in sm.iterrows():
    labs = str(r.get("labels", "")).split("|")
    s = r.get("sent_star")
    k = {"正面": "pos", "中性": "neu", "负面": "neg"}.get(s)
    if not k:
        continue
    mvn = r.get("Movie")
    for c in labs:
        if c in raw:
            raw[c][k] += 1
            if isinstance(mvn, str) and mvn:
                rawm.setdefault((mvn, c), {"pos": 0, "neu": 0, "neg": 0})[k] += 1
sankey = {}
for c in CATS:
    tot = int(ST["cat_mentions"][c])
    s = sum(raw[c].values()) or 1
    sankey[c] = {k: int(round(tot * v / s)) for k, v in raw[c].items()}

# 代表评论：每个电影×类别取点赞最高的 2 条（抽样语料）
sm = sm.dropna(subset=["Movie", "Comment"])
comments = {}
for _, r in sm.iterrows():
    text = str(r["Comment"]).strip().replace("\n", " ")
    if len(text) < 5 or "http" in text:
        continue
    rec = {
        "t": text[:110] + ("…" if len(text) > 110 else ""),
        "star": int(r["Star"]) if pd.notna(r["Star"]) else None,
        "date": str(r.get("Date", ""))[:10],
        "sp": int(r.get("is_spoiler", 0) or 0),
        "like": int(r.get("Like", 0) or 0),
    }
    for c in str(r.get("labels", "")).split("|"):
        if c in CATS:
            comments.setdefault(f"{r['Movie']}|{c}", []).append(rec)

for k, v in comments.items():
    v.sort(key=lambda x: (-x["like"], -len(x["t"])))
    comments[k] = v[:2]

movies = []
for _, r in mv.sort_values("avg_star", ascending=False).iterrows():
    movies.append({
        "name": r["movie"], "n": int(r["n_valid"]),
        "avg": round(float(r["avg_star"]), 3), "std": round(float(r["star_std"]), 3),
        "pos": round(float(r["pos_rate"]), 4), "neg": round(float(r["neg_rate"]), 4),
        "polar": round(float(r["polarization"]), 4),
        "top": r["top_category"],
        "share": {c: round(float(r[f"share_{c}"]), 4) for c in CATS},
        "posrate": {c: round(float(r[f"posrate_{c}"]), 4) for c in CATS},
        "mention": {c: int(r[f"mention_{c}"]) for c in CATS},
        "score": {c: round(float(r[f"score_{c}"]), 1) for c in CATS},
    })

# 词云：抽样评论分词后的词频（按 影片 × 类别 聚合）
CJK = re.compile(r"^[\u4e00-\u9fa5]{2,}$")
STOP = set("""的 了 是 我 你 他 她 它 我们 你们 他们 这 那 这个 那个 这些 那些 也 就 都 和 与 在 有 没
没有 不 不是 很 太 更 还 又 再 但 而 却 因为 所以 如果 就是 一个 一部 一场 一样 一些 一点 一直 真的
真是 感觉 觉得 知道 看到 看过 看完 出来 起来 什么 怎么 那么 这样 那样 自己 时候 现在 还是 可以 不能
能够 应该 可能 已经 只是 不过 而且 或者 然后 之后 之前 虽然 但是 其实 比较 非常 特别 十分 有点 有些
东西 事情 问题 地方 方面 样子 人生 世界 故事 电影 影片 片子 这部 那部 好看 不好看 喜欢
不喜欢 讨厌 一般 还行 不错 挺好 那种 这种 让人 感受 印象 总体 整体 全片 全程 这么 怎样 如何
一起 只有 还有 也是 都是 而是 于是 觉着 看来 看样子 真是 一次 一遍 两个 三个 很多 许多 所有 一切
各种 任何 别人 大家 之前 之后 以后 以前 觉得 感觉 知道 看到 看到 这样 那样 这么 那么
不会 作为 为了 确实 简直 只能 一下 里面 完全 不要 无法 如此 开始 希望 值得 算是 不同 需要 终于
啊啊 啊啊啊 哈哈 哈哈哈 呵呵 嘿嘿 啧啧 嗯 哦 喔 唉 诶 哎 呀 吧 呢 啊 哇 哈 啦 嘛 嘤 喵 那段 那句 这回 那次
""".split())

CACHE = os.path.join(PROC, "word_tokens.pkl")
CACHE_VER = "v5"
if os.path.exists(CACHE):
    with open(CACHE, "rb") as f:
        cached = pickle.load(f)
    tok_rows = cached["rows"] if cached.get("ver") == CACHE_VER else None
else:
    tok_rows = None
if tok_rows is None:
    tok_rows = []
    for _, r in sm.iterrows():
        txt = str(r.get("Comment", ""))
        toks = tuple(w for w in jieba.lcut(txt) if CJK.match(w) and w not in STOP)
        tok_rows.append((r.get("Movie"), tuple(str(r.get("labels", "")).split("|")), toks))
    with open(CACHE, "wb") as f:
        pickle.dump({"ver": CACHE_VER, "rows": tok_rows}, f)

tf = defaultdict(Counter)
df = defaultdict(Counter)
wc_n = Counter()
wc_tok = Counter()
for movie, labs, toks in tok_rows:
    if not isinstance(movie, str) or not movie:
        continue
    keys = ["G|ALL", f"{movie}|ALL"]
    for c in labs:
        if c:
            keys.append(f"G|{c}")
            keys.append(f"{movie}|{c}")
    seen_all = set()
    for k in keys:
        wc_n[k] += 1
        wc_tok[k] += len(toks)
        seen = set()
        for w in toks:
            tf[k][w] += 1
            if w not in seen:
                seen.add(w)
                df[k][w] += 1

words = {}
for k, cntr in tf.items():
    arr = [[w, c, df[k][w]] for w, c in cntr.most_common(70) if c >= 3][:60]
    if len(arr) >= 8:
        words[k] = arr
wstat = {k: [wc_n[k], wc_tok[k]] for k in words}

# 单片类别 → 情感：抽样比例 × 该片该类别提及量
msankey = {}
for m in movies:
    per = {}
    for c in CATS:
        tot = m["mention"][c]
        src = rawm.get((m["name"], c))
        if not tot or not src:
            per[c] = {"pos": 0, "neu": 0, "neg": 0}
            continue
        s = sum(src.values()) or 1
        per[c] = {k: int(round(tot * v / s)) for k, v in src.items()}
    msankey[m["name"]] = per

data = {
    "meta": {
        "total": FS["n0"], "filtered": FS["n5"], "movies": FS["n_movies"],
        "sample": int(ST["sample_rows"]), "avg": ST["mean_star"],
        "pos": ST["pos_rate"], "neg": ST["neg_rate"],
        "date_min": "2008-04-29", "date_max": "2017-03-02",
        "url": "https://www.kaggle.com/datasets/utmhikari/doubanmovieshortcomments",
    },
    "cats": [{"id": c, "name": n, "short": s} for c, n, s in zip(CATS, CAT_NAMES, CAT_SHORT)],
    "movies": movies,
    "global": {"avg": ST["mean_star"], "pos": ST["pos_rate"], "cat": gcat},
    "gscore": {c: gcat[c]["score"] for c in ["C1", "C2", "C3", "C4", "C5", "C6"]},
    "sankey": sankey,
    "msankey": msankey,
    "words": words,
    "wstat": wstat,
    "comments": comments,
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>电影评论可视化 · 交互原型</title>
<style>
  :root{
    --ink:#1b1c1e; --muted:#6f7378; --faint:#a3a7ac; --line:#dcdedf;
    --bg:#fdfdfc; --accent:#2f5d8a; --band:#f4f5f5;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);
    font-family:"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Source Han Sans SC","Noto Sans CJK SC",sans-serif;
    -webkit-font-smoothing:antialiased;}
  body{font-size:16px;line-height:1.65;}
  .wrap{max-width:1500px;margin:0 auto;padding:34px 40px 60px;}
  header{display:flex;justify-content:space-between;align-items:flex-start;gap:40px;
    border-bottom:1px solid var(--line);padding-bottom:20px;}
  h1{font-size:31px;font-weight:600;letter-spacing:.01em;margin:0 0 6px;}
  .sub{color:var(--muted);font-size:15px;max-width:760px;}
  .meta{text-align:right;font-size:13px;color:var(--muted);line-height:1.9;min-width:330px;}
  .meta b{color:var(--ink);font-weight:500;}
  .note{margin-top:14px;font-size:13px;color:var(--faint);}
  .bar{display:flex;flex-wrap:wrap;align-items:center;gap:28px;padding:18px 0 6px;}
  .bar .label{font-size:13px;color:var(--muted);letter-spacing:.02em;}
  .range{display:flex;align-items:center;gap:12px;}
  input[type=range]{width:230px;accent-color:var(--accent);}
  .val{font-variant-numeric:tabular-nums;font-size:15px;min-width:92px;}
  .catbar{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:8px 0 12px;}
  .catbar .label{font-size:12.5px;color:var(--muted);margin-right:4px;}
  .cats{display:flex;gap:6px;flex-wrap:wrap;}
  .chip{border:1px solid #d8dadc;background:#fff;color:#a9adb1;font:inherit;
    font-size:13px;line-height:1.4;padding:3px 10px 4px;cursor:pointer;border-radius:0;}
  .chip.on{border-color:var(--ink);background:var(--ink);color:#fff;}
  .chip:hover{border-color:var(--muted);}
  .seg{display:inline-flex;margin:6px 0 0;}
  .segbtn{border:1px solid #d8dadc;background:#fff;color:var(--muted);font:inherit;
    font-size:12.5px;padding:3px 12px 4px;cursor:pointer;border-radius:0;}
  .segbtn + .segbtn{border-left:0;}
  .segbtn.on{border-color:var(--ink);background:var(--ink);color:#fff;}
  .segbtn.off{color:#c8cbce;cursor:default;}
  .pick3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0 2px;}
  .pick3 select{font:inherit;font-size:13px;color:var(--ink);background:#fff;
    border:1px solid var(--line);padding:5px 6px;width:100%;border-radius:0;}
  .rtable{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px;
    font-variant-numeric:tabular-nums;}
  .rtable th{font-weight:500;color:var(--muted);font-size:11.5px;text-align:right;
    padding:7px 0 5px;border-bottom:1px solid var(--line);white-space:nowrap;}
  .rtable th:first-child,.rtable td:first-child{text-align:left;}
  .rtable td{padding:6px 0 5px;border-bottom:1px dotted #e6e7e7;text-align:right;}
  .rtable td .m{display:block;font-size:10.5px;color:#a9adb1;letter-spacing:.01em;}
  .rtable td.up{color:#2f7d5a;} .rtable td.down{color:#b04a3a;}
  .wcmeta{font-size:13px;color:var(--muted);margin:8px 0 0;}
  .wcmeta b{color:var(--ink);font-weight:500;}
  .reset{border:0;background:none;font:inherit;font-size:13px;color:var(--accent);
    text-decoration:underline;text-underline-offset:3px;cursor:pointer;padding:0;}
  .sec-title{font-size:13px;letter-spacing:.12em;color:var(--muted);margin:26px 0 4px;}
  .chart{width:100%;display:block;}
  .legend{display:flex;gap:26px;align-items:center;font-size:12.5px;color:var(--muted);
    padding:6px 0 0;flex-wrap:wrap;}
  .ramp{width:132px;height:7px;background:linear-gradient(90deg,#c0392b,#f4f4f4,#1f6fb2);}
  .cols{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:46px;align-items:start;}
  aside{position:sticky;top:26px;border-left:1px solid var(--line);padding-left:26px;min-height:420px;}
  aside .ph{color:var(--faint);font-size:14px;margin-top:8px;}
  .d-movie{font-size:23px;font-weight:600;margin:2px 0 2px;}
  .d-sub{font-size:13px;color:var(--muted);margin-bottom:18px;}
  .d-cat{font-size:15px;font-weight:600;margin:18px 0 2px;}
  .kv{display:grid;grid-template-columns:1fr auto;font-size:14px;padding:5px 0;
    border-bottom:1px dotted #e6e7e7;}
  .kv span:last-child{font-variant-numeric:tabular-nums;}
  .cmp{margin:16px 0 4px;font-size:12.5px;color:var(--muted);}
  .track{height:6px;background:#eceeee;position:relative;margin:7px 0 3px;}
  .track i{position:absolute;left:0;top:0;bottom:0;background:var(--accent);}
  .track b{position:absolute;left:0;top:0;bottom:0;background:#b9c2ca;}
  .track span{position:absolute;top:-5px;bottom:-5px;width:1px;background:#1b1c1e;}
  .cmt{border-top:1px solid var(--line);padding:12px 0 2px;margin-top:10px;font-size:14px;line-height:1.6;}
  .cmt .t{color:#2b2c2e;}
  .cmt .s{font-size:12px;color:var(--faint);margin-top:4px;}
  .tag{color:#b04a3a;font-size:12px;margin-left:6px;}
  .empty{color:var(--faint);font-size:13px;margin-top:8px;}
  footer{margin-top:54px;border-top:1px solid var(--line);padding-top:14px;
    font-size:12.5px;color:var(--faint);display:flex;justify-content:space-between;gap:20px;}
  .duo{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.22fr);
    gap:54px;align-items:start;margin-top:10px;}
  .duo .sec-title{margin-top:30px;}
  .rlegend{display:flex;gap:24px;font-size:12.5px;color:var(--muted);
    padding-top:2px;flex-wrap:wrap;}
  .sw{display:inline-block;width:20px;height:0;border-top:2px solid var(--accent);
    vertical-align:3px;margin-right:7px;}
  .sw.g{border-top:2px dashed #8b8f94;}
  @media (max-width:1100px){ .duo{grid-template-columns:1fr;gap:10px;} }
  #tip{position:fixed;pointer-events:none;background:#fff;border:1px solid var(--line);
    padding:9px 12px;font-size:13px;line-height:1.55;box-shadow:0 6px 18px rgba(0,0,0,.06);
    display:none;z-index:50;max-width:300px;}
  #tip b{font-weight:600;}
  .dim{opacity:.16;transition:opacity .15s;}
  .fade{transition:opacity .15s;}
  svg text{font-family:inherit;}
  @media (max-width:1100px){ .cols{grid-template-columns:1fr;} aside{position:static;border-left:0;
    border-top:1px solid var(--line);padding-left:0;padding-top:18px;} header{flex-direction:column;} .meta{text-align:left;} }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>电影评论可视化 · 交互原型</h1>
      <div class="sub">从“口碑—争议”散点到“电影 × 评价维度”矩阵：先看整体格局，再下钻到具体维度与真实评论。</div>
      <div class="note">矩阵数值覆盖全量有效短评；代表评论来自分层抽样，页脚标注样本量。</div>
    </div>
    <div class="meta" id="meta"></div>
  </header>

  <div class="bar">
    <div class="range">
      <span class="label">有效评论量</span>
      <input id="minN" type="range">
      <span class="val" id="minNv"></span>
    </div>
    <span class="note" style="margin:0">类别列筛选在下方矩阵标题行</span>
    <button class="reset" id="reset">重置筛选</button>
  </div>

  <div class="sec-title">① 口碑—争议散点导航　点击气泡选中影片</div>
  <svg id="scatter" class="chart" viewBox="0 0 1200 330" preserveAspectRatio="xMidYMid meet"></svg>
  <div class="legend">
    <span><span class="ramp" style="display:inline-block;vertical-align:-1px;margin-right:8px"></span>颜色：整体正面率（4—5 星占比，不随类别筛选变化）</span>
    <span>气泡面积：有效评论量</span>
    <span id="qlegend"></span>
  </div>

  <div class="cols">
    <div>
      <div class="sec-title">② 电影 × 类别气泡矩阵　点击气泡查看详情</div>
      <div class="catbar">
        <span class="label">显示类别（列）</span>
        <div class="cats" id="cats"></div>
        <button class="reset" id="catall">全部显示</button>
      </div>
      <svg id="matrix" class="chart" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="legend">
        <span>气泡面积：该类别提及量</span>
        <span>颜色：该类别正面率</span>
        <span>行内数值：平均星级</span>
        <span>开关只筛选矩阵列，不影响散点与雷达</span>
      </div>
    </div>
    <aside id="detail">
      <div class="ph">点击矩阵中的气泡，这里会显示该影片该类别的正面率、与全库均值的对比，以及两条真实评论节选。</div>
    </aside>
  </div>

  <div class="duo">
    <div>
      <div class="sec-title">③ 六维画像　可叠加 3 部影片，与全库对照</div>
      <div class="pick3" id="pick3"></div>
      <svg id="radar" class="chart" viewBox="0 0 640 440" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="rlegend" id="rlegend"></div>
      <div id="rtable"></div>
    </div>
    <div>
      <div class="sec-title">④ 类别 → 情感　流宽=提及量</div>
      <div class="seg" id="skmode">
        <button class="segbtn on" data-m="global">全库</button>
        <button class="segbtn" data-m="movie">当前影片</button>
      </div>
      <svg id="sankey" class="chart" viewBox="0 0 700 470" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="rlegend" id="sknote"></div>
    </div>
  </div>

  <div class="sec-title">⑤ 词云　跟随所选影片与类别</div>
  <div class="wcmeta" id="wcmeta"></div>
  <svg id="wordcloud" class="chart" viewBox="0 0 1200 400" preserveAspectRatio="xMidYMid meet"></svg>
  <div class="rlegend">字号=词频，位置按确定性排布（无随机）；悬停查看出现频次与来源评论条数；基于 19,954 条分层抽样的词频，非全量。</div>

  <footer>
    <span>数据：Kaggle《Douban Movie Short Comments Dataset V2》（CC0）｜下载与计算：2026-11-23</span>
    <span>第X组 · 作业1 交互原型 · 单文件离线运行</span>
  </footer>
</div>
<div id="tip"></div>

<script>
const DATA = __DATA__;
const CATS = DATA.cats, MOVIES = DATA.movies, GCAT = DATA.global.cat;
const META = DATA.meta;

const NS = "http://www.w3.org/2000/svg";
const $ = (s) => document.querySelector(s);
const tip = $("#tip");

const state = {
  minN: Math.min(...MOVIES.map(d => d.n)),
  cats: new Set(CATS.map(c => c.id)),
  movie: null,
  cat: null,
  picks: [],
  skmode: "global"
};

function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function fmt(n) { return n.toLocaleString("zh-CN"); }
function pct(x) { return (x * 100).toFixed(1) + "%"; }
function ramp(t) {
  t = Math.max(0, Math.min(1, t));
  const a = [192, 57, 43], b = [244, 244, 244], c = [31, 111, 178];
  let lo, hi, u;
  if (t < .5) { lo = a; hi = b; u = t / .5; } else { lo = b; hi = c; u = (t - .5) / .5; }
  const p = lo.map((v, i) => Math.round(v + (hi[i] - v) * u));
  return `rgb(${p[0]},${p[1]},${p[2]})`;
}
function wan(n) {
  return n >= 10000 ? (n / 10000).toFixed(1) + " 万" : fmt(n);
}
function showTip(e, html) {
  tip.innerHTML = html;
  tip.style.display = "block";
  const pad = 16;
  let x = e.clientX + pad, y = e.clientY + pad;
  const r = tip.getBoundingClientRect();
  if (x + r.width > innerWidth - 10) x = e.clientX - r.width - pad;
  if (y + r.height > innerHeight - 10) y = e.clientY - r.height - pad;
  tip.style.left = x + "px"; tip.style.top = y + "px";
}
function hideTip() { tip.style.display = "none"; }

/* ---------------- 元信息 ---------------- */
$("#meta").innerHTML =
  `<div><b>${fmt(META.filtered)}</b> 条有效短评 / <b>${META.movies}</b> 部电影</div>` +
  `<div>评论时间 ${META.date_min} — ${META.date_max}</div>` +
  `<div>分层抽样 <b>${fmt(META.sample)}</b> 条用于文本节选</div>`;

/* ---------------- 筛选控件 ---------------- */
const maxN = Math.max(...MOVIES.map(d => d.n));
const slider = $("#minN");
slider.min = Math.floor(state.minN / 1000) * 1000;
slider.max = maxN;
slider.step = 1000;
slider.value = state.minN;
function syncMinN() {
  $("#minNv").textContent = "≥ " + (state.minN / 10000).toFixed(1) + " 万条";
}
syncMinN();
slider.addEventListener("input", e => {
  state.minN = +e.target.value;
  syncMinN();
  if (state.movie && MOVIES.find(d => d.name === state.movie).n < state.minN) {
    state.picks = state.picks.filter(x => x !== state.movie);
    state.movie = state.picks[0] || null;
    state.cat = null;
    if (!state.movie) state.skmode = "global";
    syncPicks(); syncSkMode();
  }
  render();
});

const catBox = $("#cats");
CATS.forEach(c => {
  const b = document.createElement("button");
  b.className = "chip on"; b.textContent = c.short; b.dataset.c = c.id;
  b.title = `${c.id} ${c.name}`;
  b.addEventListener("click", () => {
    if (state.cats.has(c.id)) { if (state.cats.size > 1) state.cats.delete(c.id); }
    else state.cats.add(c.id);
    b.classList.toggle("on", state.cats.has(c.id));
    if (state.cat && !state.cats.has(state.cat)) state.cat = null;
    render();
  });
  catBox.appendChild(b);
});
$("#catall").addEventListener("click", () => {
  state.cats = new Set(CATS.map(c => c.id));
  document.querySelectorAll(".chip").forEach(b => b.classList.add("on"));
  render();
});

/* ---------------- 选片（散点 / 矩阵 / 雷达下拉共用） ---------------- */
function pickMovie(name) {
  state.movie = name;
  state.picks = [name, ...state.picks.filter(x => x && x !== name)].slice(0, 3);
  state.skmode = "movie";
  syncPicks(); syncSkMode(); render();
}

const pickBox = $("#pick3");
["A", "B", "C"].forEach((slot, i) => {
  const sel = document.createElement("select");
  const o0 = document.createElement("option");
  o0.value = ""; o0.textContent = `${slot} 位 · 未选`;
  sel.appendChild(o0);
  MOVIES.forEach(m => {
    const o = document.createElement("option");
    o.value = m.name; o.textContent = m.name;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => {
    const v = sel.value || null;
    if (v && state.picks.some((x, j) => x === v && j !== i)) { sel.value = state.picks[i] || ""; return; }
    state.picks[i] = v;
    state.picks = [0, 1, 2].map(j => state.picks[j] || null);
    state.movie = state.picks[0] || null;
    state.skmode = state.movie ? "movie" : "global";
    syncPicks(); syncSkMode(); render();
  });
  pickBox.appendChild(sel);
});
function syncPicks() {
  [...pickBox.querySelectorAll("select")].forEach((sel, i) => {
    sel.value = state.picks[i] || "";
  });
}

const skBox = $("#skmode");
skBox.querySelectorAll(".segbtn").forEach(b => {
  b.addEventListener("click", () => {
    if (b.dataset.m === "movie" && !state.movie) return;
    state.skmode = b.dataset.m; syncSkMode(); render();
  });
});
function syncSkMode() {
  skBox.querySelectorAll(".segbtn").forEach(b => {
    b.classList.toggle("on", b.dataset.m === state.skmode);
    b.classList.toggle("off", b.dataset.m === "movie" && !state.movie);
  });
}

$("#reset").addEventListener("click", () => {
  state.minN = +slider.min; slider.value = slider.min;
  state.cats = new Set(CATS.map(c => c.id));
  state.movie = null; state.cat = null;
  state.picks = []; state.skmode = "global";
  document.querySelectorAll(".chip").forEach(b => b.classList.add("on"));
  syncPicks(); syncSkMode(); syncMinN(); render();
});

/* ---------------- 散点 ---------------- */
function drawScatter() {
  const svg = $("#scatter");
  svg.innerHTML = "";
  const W = 1200, H = 330, L = 78, R = 26, T = 26, B = 58;
  const vis = MOVIES.filter(d => d.n >= state.minN);
  if (!vis.length) {
    const t = el("text", {x: W / 2, y: H / 2, "text-anchor": "middle",
      fill: "#a3a7ac", "font-size": 16}, svg);
    t.textContent = "当前筛选下没有电影";
    return;
  }
  const xs = vis.map(d => d.avg), ys = vis.map(d => d.std);
  const x0 = Math.min(...xs) - .12, x1 = Math.max(...xs) + .12;
  const y0 = Math.min(...ys) - .08, y1 = Math.max(...ys) + .08;
  const X = v => L + (v - x0) / (x1 - x0) * (W - L - R);
  const Y = v => T + (y1 - v) / (y1 - y0) * (H - T - B);
  const n0 = Math.min(...MOVIES.map(d => d.n)), n1 = Math.max(...MOVIES.map(d => d.n));
  const rOf = n => Math.sqrt((n - n0 * .55) / (n1 - n0 * .55)) * 27 + 5;

  // 轴与网格
  for (let i = 0; i <= 4; i++) {
    const v = x0 + (x1 - x0) * i / 4, x = X(v);
    el("line", {x1: x, y1: T, x2: x, y2: H - B, stroke: "#eeeeee"}, svg);
    const t = el("text", {x, y: H - B + 20, "text-anchor": "middle", fill: "#8b8f94",
      "font-size": 13}, svg);
    t.textContent = v.toFixed(1);
  }
  for (let i = 0; i <= 3; i++) {
    const v = y0 + (y1 - y0) * i / 3, y = Y(v);
    el("line", {x1: L, y1: y, x2: W - R, y2: y, stroke: "#f2f2f2"}, svg);
    const t = el("text", {x: L - 10, y: y + 4, "text-anchor": "end", fill: "#8b8f94",
      "font-size": 13}, svg);
    t.textContent = v.toFixed(2);
  }
  el("line", {x1: L, y1: H - B, x2: W - R, y2: H - B, stroke: "#c9ccce"}, svg);
  el("line", {x1: L, y1: T, x2: L, y2: H - B, stroke: "#c9ccce"}, svg);
  const ax = el("text", {x: (L + W - R) / 2, y: H - 12, "text-anchor": "middle",
    fill: "#5f6368", "font-size": 14}, svg);
  ax.textContent = "平均星级（口碑）";
  const ay = el("text", {x: 18, y: (T + H - B) / 2, fill: "#5f6368", "font-size": 14,
    transform: `rotate(-90 18 ${(T + H - B) / 2})`, "text-anchor": "middle"}, svg);
  ay.textContent = "星级标准差（争议度）";

  // 四象限：按当前可见影片的中位数切分，保证四格都有片
  const med = arr => { const a = [...arr].sort((p, q) => p - q); return a[Math.floor(a.length / 2)]; };
  const mx = med(xs), my = med(ys);
  const qn = {lt: 0, rt: 0, lb: 0, rb: 0};
  vis.forEach(d => {
    const right = d.avg >= mx, up = d.std >= my;
    if (right && up) qn.rt++; else if (right) qn.rb++;
    else if (up) qn.lt++; else qn.lb++;
  });
  el("line", {x1: X(mx), y1: T, x2: X(mx), y2: H - B, stroke: "#8b8f94",
    "stroke-width": 1.2, "stroke-dasharray": "4 4"}, svg);
  el("line", {x1: L, y1: Y(my), x2: W - R, y2: Y(my), stroke: "#8b8f94",
    "stroke-width": 1.2, "stroke-dasharray": "4 4"}, svg);
  const halo = {stroke: "#fdfdfc", "stroke-width": 3.5, "paint-order": "stroke"};
  const quad = [];
  let t = el("text", Object.assign({x: X(mx) + 6, y: T + 14, "font-size": 11.5,
    fill: "#7e8388"}, halo), svg);
  t.textContent = "均星中位 " + mx.toFixed(2);
  t = el("text", Object.assign({x: W - R - 4, y: Y(my) - 7, "text-anchor": "end",
    "font-size": 11.5, fill: "#7e8388"}, halo), svg);
  t.textContent = "标准差中位 " + my.toFixed(2);
  [[L + 8, T + 18, "start", "低口碑 · 高争议", qn.lt],
   [W - R - 8, T + 18, "end", "高口碑 · 高争议", qn.rt],
   [L + 8, H - B - 10, "start", "低口碑 · 低争议", qn.lb],
   [W - R - 8, H - B - 10, "end", "高口碑 · 低争议", qn.rb]].forEach(([x, y, anchor, name, n]) => {
    quad.push({x, y, anchor, text: `${name} ${n} 部`});
  });
  $("#qlegend").innerHTML = `四象限按这 ${vis.length} 部片的中位数切分（均星 ${mx.toFixed(2)} / 标准差 ${my.toFixed(2)}）：` +
    `左上 ${qn.lt} · 右上 ${qn.rt} · 左下 ${qn.lb} · 右下 ${qn.rb} 部`;

  const byN = [...vis].sort((a, b) => b.n - a.n);
  const maxPolar = vis.reduce((a, b) => a.polar > b.polar ? a : b);
  const maxAvg = vis.reduce((a, b) => a.avg > b.avg ? a : b);
  const minAvg = vis.reduce((a, b) => a.avg < b.avg ? a : b);
  const role = {[byN[0].name]: "top", [maxPolar.name]: "right",
    [maxAvg.name]: "left", [minAvg.name]: "right"};
  if (state.movie) role[state.movie] = "sel";
  const geo = {};

  vis.slice().sort((a, b) => b.n - a.n).forEach(d => {
    const cx = X(d.avg), cy = Y(d.std), sel = d.name === state.movie;
    const g = el("g", {style: "cursor:pointer"}, svg);
    el("circle", {cx, cy, r: rOf(d.n), fill: ramp(d.pos), "fill-opacity": .88,
      stroke: sel ? "#111" : "#ffffff", "stroke-width": sel ? 2 : 1.2}, g);
    if (sel) el("circle", {cx, cy, r: rOf(d.n) + 6, fill: "none", stroke: "#111",
      "stroke-width": 1, "stroke-dasharray": "3 4"}, g);
    geo[d.name] = {cx, cy, r: rOf(d.n), sel};
    g.addEventListener("mousemove", e => showTip(e,
      `<b>${d.name}</b><br>平均星级 ${d.avg.toFixed(2)}｜标准差 ${d.std.toFixed(2)}<br>` +
      `有效评论 ${fmt(d.n)} 条｜正面率 ${pct(d.pos)}`));
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("click", () => {
      if (!state.cat) state.cat = d.top;
      pickMovie(d.name);
    });
  });

  Object.keys(role).forEach(name => {
    const p = geo[name];
    if (!p) return;
    let x = p.cx + p.r + 6, y = p.cy + 4, anchor = "start";
    if (role[name] === "left") { x = p.cx - p.r - 6; anchor = "end"; }
    if (role[name] === "top") { x = p.cx; y = p.cy - p.r - 8; anchor = "middle"; }
    if (role[name] === "sel" && p.cx > W * .62) { x = p.cx - p.r - 6; anchor = "end"; }
    const t = el("text", {x, y, "text-anchor": anchor, "font-size": p.sel ? 14 : 12.5,
      fill: p.sel ? "#111" : "#4c5054", "font-weight": p.sel ? 600 : 400}, svg);
    t.textContent = name;
  });

  // 象限标签最后画，避免被气泡遮挡
  quad.forEach(q => {
    const s = el("text", Object.assign({x: q.x, y: q.y, "text-anchor": q.anchor,
      "font-size": 11.5, fill: "#9ea3a7"}, halo), svg);
    s.textContent = q.text;
  });
}

/* ---------------- 矩阵 ---------------- */
function drawMatrix() {
  const svg = $("#matrix");
  svg.innerHTML = "";
  const rows = MOVIES.filter(d => d.n >= state.minN);
  const cats = CATS.filter(c => state.cats.has(c.id));
  const rowH = 27, top = 84, left = 205, right = 24;
  const W = 1200, H = top + rows.length * rowH + 24;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.style.height = Math.min(H, 980) + "px";
  if (!rows.length || !cats.length) return;

  const colW = (W - left - right) / cats.length;
  const maxMention = Math.max(...rows.flatMap(d => cats.map(c => d.mention[c.id])));

  cats.forEach((c, j) => {
    const x = left + colW * (j + .5);
    let t = el("text", {x, y: 34, "text-anchor": "middle", "font-size": 13,
      fill: "#6f7378"}, svg);
    t.textContent = c.id;
    t = el("text", {x, y: 54, "text-anchor": "middle", "font-size": 14, fill: "#3c4044"}, svg);
    t.textContent = c.short;
  });
  el("line", {x1: left, y1: top - 12, x2: W - right, y2: top - 12, stroke: "#c9ccce"}, svg);

  rows.forEach((d, i) => {
    const y = top + i * rowH;
    const selRow = state.movie === d.name;
    if (selRow) {
      el("rect", {x: left - 10, y: y - rowH / 2, width: W - left - right + 20,
        height: rowH, fill: "#f4f5f5"}, svg);
    }
    const lab = el("text", {x: 12, y: y + 5, "font-size": selRow ? 14 : 13,
      "font-weight": selRow ? 600 : 400, fill: selRow ? "#1b1c1e" : "#4c5054",
      style: "cursor:pointer"}, svg);
    lab.textContent = `${d.name}  ${d.avg.toFixed(1)}`;
    lab.addEventListener("click", () => { pickMovie(d.name); });
    if (state.movie && !selRow) {
      lab.setAttribute("fill", "#a8acb0");
    }
    el("line", {x1: left, y1: y + rowH / 2, x2: W - right, y2: y + rowH / 2,
      stroke: "#f1f2f2"}, svg);

    cats.forEach((c, j) => {
      const x = left + colW * (j + .5);
      const m = d.mention[c.id], share = d.share[c.id], pos = d.posrate[c.id];
      const r = Math.sqrt(m / maxMention) * 11.5 + 2.5;
      const g = el("g", {style: "cursor:pointer"}, svg);
      const circle = el("circle", {cx: x, cy: y, r, fill: ramp(pos),
        "fill-opacity": .9, stroke: "#fff", "stroke-width": .8}, g);
      if (state.movie && !selRow) g.classList.add("dim");
      const selCell = state.movie === d.name && state.cat === c.id;
      if (selCell) el("circle", {cx: x, cy: y, r: r + 4, fill: "none", stroke: "#111",
        "stroke-width": 1, "stroke-dasharray": "2 3"}, g);
      g.addEventListener("mousemove", e => showTip(e,
        `<b>${d.name}</b>｜${c.id} ${c.name}<br>提及 ${fmt(m)} 次（占该片 ${pct(share)}）<br>` +
        `该类正面率 ${pct(pos)}｜该片样本 ${fmt(d.n)} 条`));
      g.addEventListener("mouseleave", hideTip);
      g.addEventListener("click", () => {
        state.cat = c.id; pickMovie(d.name);
      });
    });
  });
}

/* ---------------- 详情 ---------------- */
function drawDetail() {
  const box = $("#detail");
  if (!state.movie) {
    box.innerHTML = `<div class="ph">点击矩阵中的气泡，这里会显示该影片该类别的正面率、与全库均值的对比，以及两条真实评论节选。</div>`;
    return;
  }
  const d = MOVIES.find(m => m.name === state.movie);
  const c = CATS.find(x => x.id === state.cat) || CATS.find(x => x.id === d.top);
  const gc = GCAT[c.id];
  let html = `<div class="d-movie">${d.name}</div>
    <div class="d-sub">平均 ${d.avg.toFixed(2)} 星｜正面率 ${pct(d.pos)}｜${fmt(d.n)} 条有效短评</div>
    <div class="d-cat">${c.id} ${c.name}</div>
    <div class="kv"><span>该类提及量</span><span>${fmt(d.mention[c.id])} 次</span></div>
    <div class="kv"><span>占该片评论</span><span>${pct(d.share[c.id])}</span></div>
    <div class="kv"><span>该类正面率</span><span>${pct(d.posrate[c.id])}</span></div>
    <div class="kv"><span>该类平均星级</span><span>${(d.score[c.id] / 25 + 1).toFixed(2)}</span></div>
    <div class="cmp">该类正面率：本片 vs 全库 ${pct(gc.pos)}</div>
    <div class="track"><i style="width:${Math.min(100, d.posrate[c.id] * 100)}%"></i></div>
    <div class="track"><b style="width:${Math.min(100, gc.pos * 100)}%"></b>
      <span style="left:${Math.min(100, gc.pos * 100)}%"></span></div>
    <div class="cmp">上条：本片（蓝）｜下条：全库（灰，黑线为全库值）</div>`;

  const list = (DATA.comments[`${d.name}|${c.id}`] || []);
  if (!list.length) {
    html += `<div class="empty">该单元格没有可用的抽样评论。</div>`;
  } else {
    list.forEach(x => {
      const stars = x.star ? "★".repeat(x.star) + "☆".repeat(5 - x.star) : "";
      html += `<div class="cmt"><div class="t">“${x.t}”</div>
        <div class="s">${stars}　${x.date}${x.sp ? '<span class="tag">含剧透</span>' : ""}　有用 ${x.like}</div></div>`;
    });
  }
  html += `<div class="cmp">评论文本来自 ${fmt(META.sample)} 条分层抽样，仅作示例，不代表全量。</div>`;
  box.innerHTML = html;
}

/* ---------------- 六维雷达 ---------------- */
const RCATS = ["C1", "C2", "C3", "C4", "C5", "C6"];
const RNAMES = ["剧情", "表演", "视听", "音乐", "导演", "主题"];
const RCOL = ["#2f5d8a", "#a8622c", "#2f7d5a"];
const RFILL = ["rgba(47,93,138,.11)", "rgba(168,98,44,.10)", "rgba(47,125,90,.10)"];

function drawRadar() {
  const svg = $("#radar");
  svg.innerHTML = "";
  const W = 640, H = 440, cx = 320, cy = 212, R = 152;
  const films = state.picks.filter(Boolean)
    .map(n => MOVIES.find(m => m.name === n)).filter(Boolean);
  const ang = i => -Math.PI / 2 + i * Math.PI / 3;
  const pt = (v, i) => [cx + Math.cos(ang(i)) * R * v / 100,
                        cy + Math.sin(ang(i)) * R * v / 100];
  const poly = vals => vals.map((v, i) => pt(v, i).join(",")).join(" ");

  for (let g = 1; g <= 5; g++) {
    el("polygon", {points: poly([g * 20, g * 20, g * 20, g * 20, g * 20, g * 20]),
      fill: "none", stroke: "#eceeee", "stroke-width": 1}, svg);
  }
  RCATS.forEach((c, i) => {
    const [x, y] = pt(100, i);
    el("line", {x1: cx, y1: cy, x2: x, y2: y, stroke: "#e4e6e7"}, svg);
  });
  [50, 100].forEach(v => {
    const t = el("text", {x: cx - 9, y: cy - R * v / 100 + 4, "font-size": 10.5,
      "text-anchor": "end", fill: "#bcc0c3"}, svg);
    t.textContent = v;
  });

  const gvals = RCATS.map(c => DATA.gscore[c]);
  el("polygon", {points: poly(gvals), fill: "rgba(139,143,148,.05)", stroke: "#8b8f94",
    "stroke-width": 1.6, "stroke-dasharray": "5 4"}, svg);

  const placed = RCATS.map(() => []);
  films.forEach((mv, k) => {
    const mvals = RCATS.map(c => mv.score[c]);
    el("polygon", {points: poly(mvals), fill: RFILL[k], stroke: RCOL[k],
      "stroke-width": 2.1}, svg);
    RCATS.forEach((c, i) => {
      const v = mvals[i];
      el("circle", {cx: pt(v, i)[0], cy: pt(v, i)[1], r: 3.4, fill: RCOL[k]}, svg);
      const [ox, oy] = pt(Math.min(97, v + 7), i);
      if (placed[i].some(([px, py]) => Math.hypot(px - ox, py - oy) < 12)) return;
      placed[i].push([ox, oy]);
      const t = el("text", {x: ox, y: oy + 3.6, "text-anchor": "middle", "font-size": 10.5,
        fill: RCOL[k], stroke: "#fdfdfc", "stroke-width": 2.6, "paint-order": "stroke"}, svg);
      t.textContent = v.toFixed(0);
    });
  });

  // 轴标签（放在图形之上，避免被多边形压住）
  RCATS.forEach((c, i) => {
    const [lx, ly] = pt(116, i);
    const anchor = Math.abs(lx - cx) < 6 ? "middle" : (lx > cx ? "start" : "end");
    const t = el("text", {x: lx, y: ly + 5, "text-anchor": anchor, "font-size": 15,
      fill: "#3c4044"}, svg);
    t.textContent = RNAMES[i];
    const s = el("text", {x: lx, y: ly + 22, "text-anchor": anchor, "font-size": 12,
      fill: "#9aa0a5"}, svg);
    s.textContent = c;
  });

  if (!films.length) {
    const t = el("text", {x: cx, y: 22, "text-anchor": "middle", "font-size": 12.5,
      fill: "#a3a7ac"}, svg);
    t.textContent = "未选影片 · 当前显示全库平均；点击上方散点，或用下面 A/B/C 下拉叠加对比";
  }

  $("#rlegend").innerHTML =
    films.map((mv, k) => `<span><i class="sw" style="border-top-color:${RCOL[k]}"></i>` +
      `${"ABC"[k]}《${mv.name}》提及 ${wan(CATS.reduce((a, c) => a + mv.mention[c.id], 0))}</span>`).join("") +
    `<span><i class="sw g"></i>全库（按提及量加权）</span>`;

  drawRTable(films);
}

function drawRTable(films) {
  const box = $("#rtable");
  if (!films.length) {
    box.innerHTML = `<div class="empty">选片后这里逐轴列出分值、提及量与相对全库的差值。</div>`;
    return;
  }
  let head = `<tr><th>维度</th>` +
    films.map((m, k) => `<th style="color:${RCOL[k]}">${"ABC"[k]}</th>`).join("") +
    `<th>全库</th><th>Δ A−全库</th></tr>`;
  let body = "";
  RCATS.forEach((c, i) => {
    const g = DATA.gscore[c], a = films[0].score[c], diff = a - g;
    body += `<tr><td>${RNAMES[i]} <span style="color:#b6babd;font-size:11px">${c}</span></td>` +
      films.map(m => `<td>${m.score[c].toFixed(0)}<span class="m">${wan(m.mention[c])}</span></td>`).join("") +
      `<td>${g.toFixed(0)}</td>` +
      `<td class="${diff >= 0 ? "up" : "down"}">${diff >= 0 ? "+" : "−"}${Math.abs(diff).toFixed(1)}</td></tr>`;
  });
  box.innerHTML = `<table class="rtable">${head}${body}</table>`;
}

/* ---------------- 类别 → 情感 桑基 ---------------- */
const SENTS = [["pos", "正面", "#2f7d5a"], ["neu", "中性", "#9aa0a5"],
               ["neg", "负面", "#b04a3a"]];

function drawSankey() {
  const svg = $("#sankey");
  svg.innerHTML = "";
  const film = state.movie ? MOVIES.find(m => m.name === state.movie) : null;
  const mode = (state.skmode === "movie" && film) ? "movie" : "global";
  const src = mode === "movie" ? DATA.msankey[film.name] : DATA.sankey;
  const cats = CATS;
  const W = 700, H = 470, L = 164, R = 522, top = 30, bottom = 438;
  const gapL = 11, gapR = 26;

  $("#sknote").innerHTML = mode === "movie"
    ? `当前影片《${film.name}》：每条流的宽度=该片该类别的提及量；情感比例取自抽样，按提及量等比放大。`
    : `全库汇总：情感按星级判定（4—5 正 / 3 中 / 1—2 负）；类别为多标签，合计可大于总量。`;

  const flows = cats.map(c => {
    const v = SENTS.map(s => src[c.id][s[0]]);
    return {c, v, total: v[0] + v[1] + v[2]};
  }).filter(f => f.total > 0);
  if (!flows.length) {
    const t = el("text", {x: W / 2, y: H / 2, "text-anchor": "middle", fill: "#a3a7ac",
      "font-size": 14}, svg);
    t.textContent = mode === "movie" ? "该片在所选类别下没有提及" : "没有可展示的类别";
    return;
  }
  const total = flows.reduce((a, b) => a + b.total, 0);
  const sumR = SENTS.map((_, j) => flows.reduce((a, b) => a + b.v[j], 0));

  const scaleL = (bottom - top - gapL * (flows.length - 1)) / total;
  const scaleR = (bottom - top - gapR * 2) / total;

  let y = top;
  flows.forEach(f => { f.y0 = y; f.y1 = y + f.total * scaleL; y = f.y1 + gapL; });
  const rmap = {};
  y = top;
  sumR.forEach((v, j) => { rmap[j] = {y0: y, y1: y + v * scaleR}; y += v * scaleR + gapR; });

  const lcur = {}, rcur = {};
  flows.forEach(f => { lcur[f.c.id] = f.y0; });
  SENTS.forEach((_, j) => { rcur[j] = rmap[j].y0; });

  const mid = (L + R) / 2;
  flows.forEach(f => {
    SENTS.forEach((s, j) => {
      const h0 = f.v[j] * scaleL, h1 = f.v[j] * scaleR;
      if (h0 <= 0) return;
      const y0 = lcur[f.c.id], y1 = rcur[j];
      const d = `M ${L} ${y0} C ${mid} ${y0}, ${mid} ${y1}, ${R} ${y1} ` +
                `L ${R} ${y1 + h1} C ${mid} ${y1 + h1}, ${mid} ${y0 + h0}, ${L} ${y0 + h0} Z`;
      const p = el("path", {d, fill: s[2], "fill-opacity": .33}, svg);
      p.addEventListener("mousemove", e => {
        const share = f.v[j] / f.total * 100;
        showTip(e, `<b>${mode === "movie" ? film.name + " · " : ""}${f.c.id} ${f.c.name} → ${s[1]}</b><br>` +
          `${fmt(f.v[j])} 条（占该类 ${share.toFixed(1)}%）<br>` +
          `该类提及合计 ${fmt(f.total)} 条`);
      });
      p.addEventListener("mouseleave", hideTip);
      lcur[f.c.id] += h0;
      rcur[j] += h1;
    });
  });

  // 左侧节点与标签（简单防重叠）
  let lastY = -100;
  flows.forEach(f => {
    el("rect", {x: L - 7, y: f.y0, width: 7, height: Math.max(f.y1 - f.y0, 1),
      fill: "#d3d6d8"}, svg);
    let ly = (f.y0 + f.y1) / 2 + 4;
    if (ly - lastY < 17) ly = lastY + 17;
    lastY = ly;
    const g = el("g", {style: "cursor:pointer"}, svg);
    const t = el("text", {x: L - 14, y: ly, "text-anchor": "end", "font-size": 12,
      fill: "#3c4044"}, g);
    t.textContent = `${f.c.id} ${f.c.short}  ${wan(f.total)}`;
    g.addEventListener("mousemove", e => showTip(e,
      `<b>${f.c.id} ${f.c.name}</b><br>提及 ${fmt(f.total)} 条`));
    g.addEventListener("mouseleave", hideTip);
    g.addEventListener("click", () => {
      if (!state.movie) return;
      state.cat = f.c.id; render();
    });
  });

  // 右侧节点与标签
  SENTS.forEach((s, j) => {
    const r = rmap[j];
    el("rect", {x: R, y: r.y0, width: 7, height: Math.max(r.y1 - r.y0, 1),
      fill: s[2], "fill-opacity": .55}, svg);
    const t = el("text", {x: R + 16, y: (r.y0 + r.y1) / 2 - 2, "font-size": 13,
      fill: s[2], "font-weight": 600}, svg);
    t.textContent = s[1];
    const c = el("text", {x: R + 16, y: (r.y0 + r.y1) / 2 + 15, "font-size": 11.5,
      fill: "#6f7378"}, svg);
    c.textContent = wan(sumR[j]);
  });
}

/* ---------------- 词云 ---------------- */
const wcCache = {};

function wcKey() {
  const m = state.movie, c = state.cat;
  const cand = [];
  if (m && c) cand.push(m + "|" + c, m + "|ALL", "G|" + c, "G|ALL");
  else if (m) cand.push(m + "|ALL", "G|ALL");
  else if (c) cand.push("G|" + c, "G|ALL");
  else cand.push("G|ALL");
  return cand.find(k => DATA.words[k]) || null;
}

function layoutWc(list, W, H) {
  const ctx = layoutWc.ctx || (layoutWc.ctx = document.createElement("canvas").getContext("2d"));
  const logs = list.map(x => Math.log(x[1]));
  const lo = Math.min(...logs), hi = Math.max(...logs);
  const pos = [];
  for (let y = 12; y < H - 8; y += 12)
    for (let x = 12; x < W - 8; x += 12) pos.push([x, y]);
  const cx = W / 2, cy = H / 2;
  const dist = (x, y) => Math.hypot((x - cx) / 1.65, (y - cy) / .95);
  pos.sort((a, b) => dist(a[0], a[1]) - dist(b[0], b[1]));
  const placed = [], out = [];
  list.forEach(([w, n, d]) => {
    const size = 12 + 20 * (Math.log(n) - lo) / (hi - lo || 1);
    ctx.font = `${size.toFixed(1)}px "PingFang SC","Microsoft YaHei",sans-serif`;
    const bw = ctx.measureText(w).width + 9, bh = size * 1.2 + 5;
    for (const [x, y] of pos) {
      const x0 = x - bw / 2, y0 = y - bh / 2;
      if (x0 < 2 || y0 < 2 || x0 + bw > W - 2 || y0 + bh > H - 2) continue;
      if (placed.some(p => x0 < p.x + p.w + 3 && x0 + bw + 3 > p.x &&
                           y0 < p.y + p.h + 2 && y0 + bh + 2 > p.y)) continue;
      placed.push({x: x0, y: y0, w: bw, h: bh});
      out.push({w, n, d, size, x, y});
      break;
    }
  });
  return out;
}

function drawWordCloud() {
  const svg = $("#wordcloud");
  svg.innerHTML = "";
  const W = 1200, H = 400;
  const k = wcKey();
  const meta = $("#wcmeta");
  if (!k) { meta.textContent = "该范围内没有足够的词频样本。"; return; }
  const [who, cat] = k.split("|");
  const catName = cat === "ALL" ? "全部类别" :
    cat + " " + ((CATS.find(c => c.id === cat) || {}).name || "");
  const scope = (who === "G" ? "全库" : "《" + who + "》") + " × " + catName;
  const st = DATA.wstat[k] || [0, 0];
  if (!wcCache[k]) wcCache[k] = layoutWc(DATA.words[k], W, H);
  const out = wcCache[k];
  meta.innerHTML = `${scope} · 该范围抽样评论 <b>${fmt(st[0])}</b> 条 / <b>${fmt(st[1])}</b> 个词次 · 显示 <b>${out.length}</b> 个词`;
  if (!out.length) return;
  out.forEach(o => {
    const t = el("text", {x: o.x, y: o.y, "text-anchor": "middle",
      "dominant-baseline": "middle", "font-size": o.size.toFixed(1),
      fill: "#3c4044", "fill-opacity": .92}, svg);
    t.textContent = o.w;
    t.addEventListener("mousemove", e => showTip(e,
      `<b>${o.w}</b><br>出现 ${fmt(o.n)} 次 · 来自 ${fmt(o.d)} 条评论<br>${scope}｜抽样词频`));
    t.addEventListener("mouseleave", hideTip);
  });
}

function render() { drawScatter(); drawMatrix(); drawDetail(); drawRadar(); drawSankey(); drawWordCloud(); }

syncPicks(); syncSkMode();
render();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("written", OUT)
print("movies", len(movies), "cells with comments", len(comments),
      "comments", sum(len(v) for v in comments.values()))
print("size KB", round(os.path.getsize(OUT) / 1024, 1))


