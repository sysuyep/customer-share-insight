#!/usr/bin/env python3
"""
检查可编辑 PPTX 是否可以交付。

严重问题：
- 页数和预期不一致（提供 --expected-slides 时）
- 有页面是整页图片、几乎没有可编辑文字（截图贴进 PPT）
- 有页面的演讲备注为空

警告：
- 备注里残留资料来源或文件路径
- 某页没有任何文本框

依赖：python-pptx（pip install python-pptx）。

用法：
  python3 scripts/check_pptx.py deck.pptx --expected-slides 22
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_checks import find_sources_and_paths  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="检查可编辑 PPTX")
    ap.add_argument("pptx")
    ap.add_argument("--expected-slides", type=int, default=0)
    a = ap.parse_args()
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        print("缺少 python-pptx。请运行：pip install python-pptx（或换用已安装它的 Python 环境）")
        return 2

    prs = Presentation(a.pptx)
    area = prs.slide_width * prs.slide_height
    issues, warnings = [], []
    total_text, total_pic = 0, 0

    for i, slide in enumerate(prs.slides, 1):
        texts = [sh for sh in slide.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
        pics = [sh for sh in slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
        total_text += len(texts)
        total_pic += len(pics)
        big = [pc for pc in pics if pc.width and pc.height and pc.width * pc.height >= 0.85 * area]
        if big and len(texts) <= 1:
            issues.append(f"P{i} 是整页图片，几乎没有可编辑文字。请用文本框和形状重建这一页。")
        if not texts:
            warnings.append(f"P{i} 没有任何可编辑文字。")
        notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        if not notes:
            issues.append(f"P{i} 的演讲备注为空。")
        else:
            src = find_sources_and_paths(notes)
            if src:
                warnings.append(f"P{i} 备注里有来源或路径：{src[0][:40]}")

    n = len(prs.slides)
    if a.expected_slides and n != a.expected_slides:
        issues.append(f"PPT 有 {n} 页，预期 {a.expected_slides} 页。")

    print("=" * 72)
    print(f"PPTX 检查：{Path(a.pptx).name}　共 {n} 页，可编辑文字框 {total_text} 个，图片 {total_pic} 张")
    print("=" * 72)
    for title, items in (("严重问题", issues), ("警告", warnings)):
        if items:
            print(f"\n{title}")
            for x in items:
                print(f"- {x}")
    if not issues and not warnings:
        print("通过：没有发现问题。")
    elif not issues:
        print("\n通过，但有警告，请逐条确认。")
    else:
        print("\n有严重问题，修复后再交付。")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
