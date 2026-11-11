#!/usr/bin/env python3
"""
把逐页讲稿写进 PPTX 每一页的演讲备注。

- 按 "## P# · 标题" 切分讲稿，第 N 段写入第 N 页。
- 默认去掉"来源 / 依据 / Sources"等行和文件路径；需要保留时加 --keep-sources。
- 讲稿里有 **English** 段时一并写入，中文在前、英文在后。
- 讲稿页数和 PPT 页数不一致时报错退出，不会写一半。

依赖：python-pptx（pip install python-pptx）。

用法：
  python3 scripts/notes_to_pptx.py deck.pptx speaker_notes.md -o deck_with_notes.pptx
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_checks import PATH_RE, SOURCE_LINE_RE  # noqa: E402

PAGE_RE = re.compile(r"^\s{0,3}#{2,3}\s*P(\d+)\b.*$", re.M | re.I)


def split_pages(text):
    marks = list(PAGE_RE.finditer(text))
    return [(int(m.group(1)), text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))])
            for i, m in enumerate(marks)]


def clean(body, keep_sources):
    lines = []
    for line in body.strip().splitlines():
        if not keep_sources and (SOURCE_LINE_RE.match(line) or (PATH_RE.search(line) and len(PATH_RE.sub("", line).strip()) < 6)):
            continue
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)          # 去掉加粗记号
        line = re.sub(r"^\s*[-*]\s+", "· ", line)               # 列表符号
        if not keep_sources:
            line = PATH_RE.sub("", line)
        lines.append(line.rstrip())
    out = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def main():
    ap = argparse.ArgumentParser(description="把逐页讲稿写进 PPTX 演讲备注")
    ap.add_argument("pptx")
    ap.add_argument("notes")
    ap.add_argument("-o", "--output", help="输出文件，默认覆盖原 PPTX")
    ap.add_argument("--keep-sources", action="store_true", help="保留来源和路径")
    a = ap.parse_args()

    try:
        from pptx import Presentation
    except ImportError:
        print("缺少 python-pptx。请运行：pip install python-pptx（或换用已安装它的 Python 环境）")
        return 2

    prs = Presentation(a.pptx)
    pages = split_pages(Path(a.notes).read_text(encoding="utf-8", errors="ignore"))
    slides = list(prs.slides)
    if not pages:
        print("讲稿里没有找到「## P1 · 标题」格式的逐页标题。")
        return 1
    if len(pages) != len(slides):
        print(f"讲稿 {len(pages)} 页，PPT {len(slides)} 页，页数不一致，未写入。请先让两者逐页对应。")
        return 1

    empty = []
    for (n, body), slide in zip(pages, slides):
        text = clean(body, a.keep_sources)
        if not text:
            empty.append(n)
        slide.notes_slide.notes_text_frame.text = text
    out = a.output or a.pptx
    prs.save(out)
    print(f"已写入 {len(slides)} 页备注：{out}")
    if empty:
        print(f"注意：第 {empty} 页的备注为空。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
