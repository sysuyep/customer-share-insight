#!/usr/bin/env python3
"""
校验客户洞察报告 HTML。

严重问题：
- 抬头没有"客户洞察报告"
- 六章（id 为 s1–s6）缺失、顺序不对，或多出其他章节
- 引用网络资源、残留脚本代码、残留模板示例文字"【示例】"
- 使用 2px 以上的左侧彩色边条

警告：
- 章节标题只写了章节名，没有写结论
- 诊断少于 2 条或多于 4 条
- 表格没有放进可横向滑动的区域（手机上会撑破页面）
- 缺少深色模式、viewport 设置；使用阴影
- 常见 AI 腔和自造词

用法：
  python3 scripts/validate_insight_report.py insight_report.html
"""

import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_checks import find_ai_phrases  # noqa: E402

CHAPTERS = ["客户画像", "企业发展时间线", "核心业务与经营模式", "管理理念与价值观", "诊断与机会", "博商学习与已发生的改变"]
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"<[^>]+>")
SECTION_RE = re.compile(r"<section\b[^>]*class=[\"'](?:[^\"']*\s)?chapter(?:\s[^\"']*)?[\"'][^>]*>", re.I)


def text_of(s):
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", s))).strip()


def validate(path):
    p = Path(path)
    if not p.is_file():
        print(f"错误：文件不存在 — {path}")
        return False
    raw = p.read_text(encoding="utf-8", errors="ignore")
    html = COMMENT_RE.sub("", raw)
    issues, warnings = [], []

    if "客户洞察报告" not in html:
        issues.append("抬头缺少「客户洞察报告」字样，格式应为：客户洞察报告 · 公司名 · 客户姓名。")
    if "【示例】" in raw:
        issues.append("还有模板示例文字「【示例】」没有替换。")
    if re.search(r"(html\s*\+=|\"\"\"|#\s*SECTION\b)", html, re.I):
        issues.append("文件里残留脚本代码（如 html += 、三引号、# SECTION）。")
    if re.search(r"<link\b[^>]*href\s*=\s*[\"']https?://|<script\b[^>]*src\s*=\s*[\"']https?://|url\(\s*[\"']?https?://|<img\b[^>]*src\s*=\s*[\"']https?://", html, re.I):
        issues.append("引用了网络资源，报告要单文件可打开。")
    if any(float(w) >= 2 for w in re.findall(r"border-(?:left|inline-start)\s*:\s*([0-9.]+)px", html, re.I)):
        issues.append("使用了 2px 以上的左侧边条。区分层次请用底色交替、细线和留白。")
    if re.search(r"box-shadow\s*:\s*(?!none)", html, re.I):
        warnings.append("使用了阴影（box-shadow）。")

    sections = []
    for m in SECTION_RE.finditer(html):
        sid = re.search(r"\bid=[\"']([^\"']+)[\"']", m.group(0))
        end = html.find("</section>", m.end())
        sections.append((sid.group(1) if sid else "", html[m.end():end]))
    ids = [s for s, _ in sections]
    if ids != ["s1", "s2", "s3", "s4", "s5", "s6"]:
        issues.append(f"章节应为 s1–s6 六章、按顺序排列，现在是：{ids or '没有找到 class=chapter 的章节'}。")

    for (sid, body), name in zip(sections, CHAPTERS):
        label = re.search(r"class=[\"'][^\"']*\bch-label\b[^\"']*[\"'][^>]*>(.*?)</", body, re.S)
        title = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.S)
        if label and name not in text_of(label.group(1)):
            warnings.append(f"{sid} 的章节标签应包含「{name}」，现在是「{text_of(label.group(1))}」。")
        if not title:
            warnings.append(f"{sid} 缺少章节标题（h2）。")
        else:
            t = text_of(title.group(1))
            if len(t) <= len(name) + 4 or t.replace(" ", "") in CHAPTERS:
                warnings.append(f"{sid} 的标题「{t}」像章节名，分析报告的标题要直接写结论。")

    if len(sections) >= 5:
        n_diag = len(re.findall(r"class=[\"'](?:[^\"']*\s)?diag(?:\s[^\"']*)?[\"']", sections[4][1]))
        if not 2 <= n_diag <= 4:
            warnings.append(f"诊断与机会有 {n_diag} 条诊断，建议 3–4 条，每条讲一个独立问题。")

    tables = len(re.findall(r"<table\b", html, re.I))
    wrapped = len(re.findall(r"table-wrap", html))
    if tables and wrapped < tables:
        warnings.append("有表格没有放进 .table-wrap，手机宽度下可能撑破页面。")
    if "prefers-color-scheme" not in html:
        warnings.append("缺少深色模式配色。")
    if 'name="viewport"' not in html:
        warnings.append("缺少 viewport 设置，手机上显示会缩得很小。")

    ai = find_ai_phrases(text_of(html))
    if ai:
        warnings.append("可能是 AI 腔或自造词：" + "、".join(f"{w}×{c}" for w, c in ai))

    print("=" * 72)
    print(f"洞察报告校验：{p.name}")
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python3 scripts/validate_insight_report.py <insight_report.html>")
        sys.exit(1)
    sys.exit(0 if validate(sys.argv[1]) else 1)
