# -*- coding: utf-8 -*-
"""把命令行输出日志渲染成终端风格截图，用于过程留痕与 Word 配图。

用法：
  python 00_make_screenshot.py <日志文件> <输出png> <标题> [最大行数]
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_LATIN = r"C:\Windows\Fonts\consola.ttf"
FONT_CN = r"C:\Windows\Fonts\msyh.ttc"

BG = (30, 34, 40)
BAR = (46, 52, 60)
FG = (226, 232, 240)
DIM = (148, 163, 184)
ACCENT = (96, 165, 250)


def is_ascii(ch):
    return ord(ch) < 128


def draw_runs(draw, xy, text, f_latin, f_cn, fill):
    """按 ASCII / 非 ASCII 分段绘制，保证 ASCII 列对齐且中文正常显示。"""
    x, y = xy
    buf, cur_ascii = "", None
    for ch in text:
        a = is_ascii(ch)
        if cur_ascii is None or a == cur_ascii:
            buf += ch
            cur_ascii = a
        else:
            f = f_latin if cur_ascii else f_cn
            draw.text((x, y), buf, font=f, fill=fill)
            x += draw.textlength(buf, font=f)
            buf, cur_ascii = ch, a
    if buf:
        f = f_latin if cur_ascii else f_cn
        draw.text((x, y), buf, font=f, fill=fill)
        x += draw.textlength(buf, font=f)
    return x


def main():
    log_path, out_path, title = sys.argv[1], sys.argv[2], sys.argv[3]
    max_lines = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    with open(log_path, encoding="utf-8", errors="replace") as f:
        raw = [ln.rstrip("\n") for ln in f]

    lines = [ln for ln in raw if ln.strip()][:max_lines]
    if not lines:
        raise SystemExit("日志为空")

    size = 17
    f_latin = ImageFont.truetype(FONT_LATIN, size)
    f_cn = ImageFont.truetype(FONT_CN, size)
    f_title = ImageFont.truetype(FONT_CN, 15)

    probe = Image.new("RGB", (10, 10))
    pd = ImageDraw.Draw(probe)
    widths = [pd.textlength(ln, font=f_latin) if ln.isascii() else None for ln in lines]
    # 中文行按分字符宽度估算
    est = []
    for ln, w in zip(lines, widths):
        if w is None:
            w = sum(pd.textlength(c, font=f_latin if is_ascii(c) else f_cn) for c in ln)
        est.append(w)
    content_w = int(max(est)) + 2

    pad_x, pad_y = 26, 18
    line_h = 26
    bar_h = 46
    width = min(max(content_w + pad_x * 2, 760), 1800)
    height = bar_h + pad_y * 2 + line_h * len(lines) + 56

    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, bar_h], fill=BAR)
    for i, c in enumerate([(239, 68, 68), (234, 179, 8), (34, 197, 94)]):
        d.ellipse([16 + i * 22, 16, 28 + i * 22, 28], fill=c)
    d.text((width // 2, bar_h // 2), title, font=f_title, fill=DIM, anchor="mm")

    y = bar_h + pad_y
    for ln in lines:
        draw_runs(d, (pad_x, y), ln, f_latin, f_cn, FG)
        y += line_h

    d.text((pad_x, height - 32), "实际执行输出 · 2026-11-23", font=f_title, fill=DIM)
    img.save(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
