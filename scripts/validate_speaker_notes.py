#!/usr/bin/env python3
"""
校验逐页讲稿。

严重问题：
- 没有按 "## P# · 标题" 逐页组织
- 页数和演示稿不一致（提供 --deck 时检查）
- 出现"动作、点击、停顿、手势"这类舞台动作栏目
- 出现第三人称写法（提供 --speaker 时检查）

警告：
- 某页缺"讲稿参考"或内容很短
- 残留资料来源、文件路径
- 常见 AI 腔和自造词

用法：
  python3 scripts/validate_speaker_notes.py speaker_notes.md --deck deck.html --speaker 林志远
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_checks import find_ai_phrases, find_sources_and_paths, find_third_person  # noqa: E402

PAGE_RE = re.compile(r"^\s{0,3}#{2,3}\s*P(\d+)\b.*$", re.M | re.I)
STAGE_RE = re.compile(
    r"^\s{0,3}(?:[-*]\s*)?(?:#{1,6}\s*)?(?:\*\*)?"
    r"(动作|讲者动作|页面动作|演讲动作|操作|点击|指向|停顿|手势|切换效果|舞台提示)(?:\*\*)?\s*[:：]",
    re.M,
)
SLIDE_RE = re.compile(r"<section\b[^>]*class=[\"'](?:[^\"']*\s)?slide(?:\s[^\"']*)?[\"']", re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def split_pages(text):
    marks = list(PAGE_RE.finditer(text))
    pages = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        pages.append((int(m.group(1)), text[m.end():end]))
    return pages


def validate(path, deck, speakers):
    p = Path(path)
    if not p.is_file():
        print(f"错误：文件不存在 — {path}")
        return False
    text = p.read_text(encoding="utf-8", errors="ignore")
    issues, warnings = [], []
    pages = split_pages(text)

    if not pages:
        issues.append("没有找到逐页标题。请按「## P1 · 页面标题」逐页写。")
    nums = [n for n, _ in pages]
    if nums and nums != list(range(1, len(nums) + 1)):
        warnings.append(f"页码不连续或有重复：{nums}")
    if deck:
        d = Path(deck)
        if d.is_file():
            n_slides = len(SLIDE_RE.findall(COMMENT_RE.sub("", d.read_text(encoding="utf-8", errors="ignore"))))
            if n_slides != len(pages):
                issues.append(f"讲稿有 {len(pages)} 页，演示稿有 {n_slides} 页，需要逐页对应。")
        else:
            warnings.append(f"找不到演示稿 {deck}，跳过页数比对。")

    stage = sorted(set(STAGE_RE.findall(text)))
    if stage:
        issues.append(f"出现舞台动作类栏目：{stage}。讲稿只写讲述方向、讲稿和过渡。")

    for n, body in pages:
        m = re.search(r"讲稿参考\**\s*[:：]?\s*(.*?)(?=\n\s*\**(?:过渡到下一页|English)|\Z)", body, re.S)
        if not m:
            warnings.append(f"P{n} 没有「讲稿参考」。")
        elif len(re.sub(r"\s", "", m.group(1))) < 30:
            warnings.append(f"P{n} 的讲稿参考少于 30 字，分享人可能不知道怎么讲。")

    tp = find_third_person(text, speakers)
    if tp:
        issues.append("出现第三人称写法（讲稿是分享人自己讲）：" + "；".join(tp[:5]))
    src = find_sources_and_paths(text)
    if src:
        warnings.append("残留资料来源或文件路径，交付版讲稿和备注里通常不需要：" + "；".join(src[:5]))
    ai = find_ai_phrases(text)
    if ai:
        warnings.append("可能是 AI 腔或自造词：" + "、".join(f"{w}×{c}" for w, c in ai))

    print("=" * 72)
    print(f"讲稿校验：{p.name}　共 {len(pages)} 页")
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
    return not issues


def main():
    ap = argparse.ArgumentParser(description="校验逐页讲稿")
    ap.add_argument("notes")
    ap.add_argument("--deck", help="对应的 HTML 演示稿，用来比对页数")
    ap.add_argument("--speaker", action="append", default=[], help="分享人的称呼，可写多次")
    a = ap.parse_args()
    return 0 if validate(a.notes, a.deck, a.speaker) else 1


if __name__ == "__main__":
    sys.exit(main())
