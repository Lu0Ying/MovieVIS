# -*- coding: utf-8 -*-
"""生成《疯狂动物城 × C0》词云图，并插入 Word 4.6 可视化预览小节（图 10）。"""

import glob
import json
import math
import os

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from PIL import Image, ImageDraw, ImageFont

BASE = r"c:\Users\联想电脑\Desktop\可视化\小组作业\2026-11-23\movie-review-viz-plan"
HTML = os.path.join(BASE, "outputs", "index.html")
OUTDIR = os.path.join(BASE, "outputs")
FIG = os.path.join(BASE, "work", "preview", "wc_figure.png")
FONT = r"C:\Windows\Fonts\msyh.ttc"

KEY = "疯狂动物城|C0"
CAPTION = "图 10 词云示例：《疯狂动物城》× C0 整体评价（基于 19,954 条分层抽样的词频，非全量）"

with open(HTML, encoding="utf-8") as f:
    html = f.read()
raw = html[html.index("const DATA = ") + len("const DATA = "):]
data = json.loads(raw[:raw.index(";\nconst CATS")])
words = data["words"][KEY]
stat = data["wstat"][KEY]

# ---- 词云图（PIL 绘制，确定性布局） ----
W, H = 2400, 1000
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)
logs = [math.log(w[1]) for w in words]
lo, hi = min(logs), max(logs)
step = 26
cx, cy = W / 2, H / 2
pos = [(x, y) for y in range(step, H - step, step) for x in range(step, W - step, step)]
pos.sort(key=lambda p: math.hypot((p[0] - cx) / 1.65, (p[1] - cy) / .95))
placed, shown = [], 0
for w, n, d in words:
    size = int(26 + 46 * (math.log(n) - lo) / (hi - lo or 1))
    font = ImageFont.truetype(FONT, size)
    box = draw.textbbox((0, 0), w, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    for x, y in pos:
        x0, y0 = x - tw / 2 - 8, y - th / 2 - 6
        if x0 < 6 or y0 < 6 or x0 + tw + 16 > W - 6 or y0 + th + 12 > H - 6:
            continue
        if any(x0 < p[0] + p[2] + 6 and x0 + tw + 16 > p[0] - 6 and
               y0 < p[1] + p[3] + 4 and y0 + th + 12 > p[1] - 4 for p in placed):
            continue
        placed.append((x0, y0, tw + 16, th + 12))
        draw.text((x, y), w, font=font, fill=(27, 28, 30), anchor="mm")
        shown += 1
        break
img.save(FIG)
print("figure", FIG, "words", shown, "/", len(words), "scope comments", stat)

# ---- 插入 Word ----
f = [x for x in glob.glob(OUTDIR + r"\*.docx") if not os.path.basename(x).startswith("~")][0]
d = docx.Document(f)
assert sum(1 for p in d.paragraphs if "图 10" in p.text) == 1, "图 10 引用不唯一，终止"

anchor = next(p for p in d.paragraphs if p.text.strip().startswith("5 第一轮小结"))

h = anchor.insert_paragraph_before(style="Heading 3")
r = h.add_run("4.6.4 词云：影片 × 类别的词频")
r.bold = True
r.font.size = Pt(12)
r2 = h.add_run("【主完成：组员D】")
r2.font.size = Pt(10.5)

body = anchor.insert_paragraph_before()
rb = body.add_run(
    "词云用于检查“某个类别的评论到底在说什么”。口径为 19,954 条分层抽样：先用 jieba 分词，过滤停用词、"
    "单字、纯数字与英文缩写，再按“影片 × 类别”聚合，统计每个词的出现次数与来源评论条数；"
    "字号按词频对数映射，位置按确定性碰撞检测排布，不做随机装饰。原型页面中词云随顶部选片与类别联动，"
    "悬停可看到精确频次。下图为《疯狂动物城》× C0 整体评价的示例。")
rb.font.size = Pt(12)

pic = anchor.insert_paragraph_before()
pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
pic.add_run().add_picture(FIG, width=Cm(14.2))

cap = anchor.insert_paragraph_before()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
rc = cap.add_run(CAPTION)
rc.font.size = Pt(10.5)

for p in d.paragraphs:
    if p.text.strip().startswith("图 10 过滤漏斗脚本实测输出"):
        for run in p.runs:
            if "图 10" in run.text:
                run.text = run.text.replace("图 10", "图 11")
        break

d.save(f)
print("docx", os.path.basename(f), "paras", len(d.paragraphs),
      "imgs", len(d.inline_shapes), "size MB", round(os.path.getsize(f) / 1048576, 2))
