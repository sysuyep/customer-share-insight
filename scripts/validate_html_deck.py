#!/usr/bin/env python3
"""
校验客户分享 HTML 演示稿的结构、视觉写法和文字。

严重问题（必须修）：
- 缺 .deck 容器、slide 缺 data-page / data-role、slide 没有套 .slide-wrapper
- 没有封面；模块导览页不是正好一页
- 引用网络资源（字体、脚本、图片、样式）
- 文件里残留脚本代码（html += 、三引号、# SECTION）或模板示例文字"【示例】"
- 使用左侧彩色边条（border-left 2px 以上）
- 样式里有小于 18px 的字号（浏览外框的提示文字除外）
- 缺少缩放脚本（resize 监听）
- 出现第三人称写法（需要用 --speaker 提供分享人称呼）

警告（逐条确认）：
- 页数和预期不符、版式种类少于 5 种
- 使用阴影、缺少打印样式或深色模式
- 模块导览页和模块过渡页的编号、标题对不上；过渡页没有编号
- 封面出现数字或序号
- 同一个带单位的数字出现在多页、相邻两页标题过于相似
- 常见 AI 腔和自造词

最后打印"标题连读"，方便从头读一遍检查思路是否连贯。

用法：
  python3 scripts/validate_html_deck.py deck.html --speaker 林志远 --speaker 林总 [--expected-pages 22]
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_checks import find_ai_phrases, find_third_person  # noqa: E402

def cls_re(name):
    """匹配 class 属性里完整的类名（不会把 slide-wrapper 当成 slide）。"""
    return r"class=[\"'](?:[^\"']*\s)?%s(?:\s[^\"']*)?[\"']" % re.escape(name)


SLIDE_OPEN_RE = re.compile(r"<section\b[^>]*" + cls_re("slide") + r"[^>]*>", re.I)
ATTR_RE = lambda name: re.compile(name + r"\s*=\s*[\"']([^\"']*)[\"']", re.I)  # noqa: E731
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
EXTERNAL_RES = [
    (re.compile(r"<link\b[^>]*href\s*=\s*[\"']https?://", re.I), "外链样式或字体 <link>"),
    (re.compile(r"<script\b[^>]*src\s*=\s*[\"']https?://", re.I), "外链脚本 <script src>"),
    (re.compile(r"<img\b[^>]*src\s*=\s*[\"']https?://", re.I), "外链图片 <img>"),
    (re.compile(r"url\(\s*[\"']?https?://", re.I), "样式里的外链 url()"),
    (re.compile(r"@import\s+[\"']?(?:url\()?\s*[\"']?https?://", re.I), "外链 @import"),
]
CODE_RESIDUE_RE = re.compile(r"(html\s*\+=|\"\"\"|'''|#\s*SECTION\b|for\s+slide\s+in\s+slides)", re.I)
BORDER_LEFT_RE = re.compile(r"border-(?:left|inline-start)\s*:\s*([0-9.]+)px", re.I)
BORDER_LEFT_WIDTH_RE = re.compile(r"border-(?:left|inline-start)-width\s*:\s*([0-9.]+)px", re.I)
SHADOW_RE = re.compile(r"box-shadow\s*:\s*(?!none)[^;]+;", re.I)
CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
FONT_PX_RE = re.compile(r"font-size\s*:\s*([0-9.]+)px", re.I)
NUM_UNIT_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(分钟|小时|天|个月|年|人|家|个|间|座|台|辆|条|万元|亿元|万|亿|元|%|倍|立方米|方)"
)
TITLE_CLASSES = ["opener-title", "cover-title", "company-name", "claim", "quote-text", "closing-main", "title"]


def text_of(fragment):
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", fragment))).strip()


def parse_slides(html):
    slides = []
    for m in SLIDE_OPEN_RE.finditer(html):
        start, depth, j = m.end(), 1, m.end()
        while depth > 0:
            o = re.search(r"<section\b", html[j:], re.I)
            c = re.search(r"</section\s*>", html[j:], re.I)
            if not c:
                break
            if o and o.start() < c.start():
                depth += 1
                j += o.end()
            else:
                depth -= 1
                if depth == 0:
                    slides.append((m.group(0), html[start:j + c.start()]))
                j += c.end()
    return slides


def first_by_class(inner, cls):
    m = re.search(r"<(\w+)[^>]*" + cls_re(cls) + r"[^>]*>(.*?)</\1>", inner, re.S | re.I)
    return text_of(m.group(2)) if m else ""


def all_by_class(inner, cls):
    return [text_of(g) for _, g in re.findall(
        r"<(\w+)[^>]*" + cls_re(cls) + r"[^>]*>(.*?)</\1>", inner, re.S | re.I)]


def slide_title(inner):
    for cls in TITLE_CLASSES:
        t = first_by_class(inner, cls)
        if t:
            return t
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", inner, re.S | re.I)
    return text_of(m.group(1)) if m else ""


def bigrams(s):
    s = re.sub(r"[\s，。、：；！？,.:;!?\"'“”‘’（）()]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def validate(path, speakers, expected_pages):
    p = Path(path)
    if not p.is_file():
        print(f"错误：文件不存在 — {path}")
        return False
    raw = p.read_text(encoding="utf-8", errors="ignore")
    html = COMMENT_RE.sub("", raw)
    css = "\n".join(STYLE_RE.findall(html))
    body_html = SCRIPT_RE.sub("", STYLE_RE.sub("", html))
    issues, warnings = [], []

    if not re.search(cls_re("deck"), html):
        issues.append('没有找到 class="deck" 的外层容器。请以 assets/deck-template.html 为起点。')
    slides = parse_slides(body_html)
    n = len(slides)
    if n == 0:
        issues.append('没有找到 <section class="slide ..."> 页面。')
    wrappers = len(re.findall(cls_re("slide-wrapper"), body_html))
    if n and wrappers != n:
        issues.append(f"有 {n} 页，但 .slide-wrapper 只有 {wrappers} 个；每页都要套一层 .slide-wrapper。")

    roles, titles, slide_texts = [], [], []
    for idx, (head, inner) in enumerate(slides, 1):
        page = ATTR_RE("data-page").search(head)
        role = ATTR_RE("data-role").search(head)
        if not page:
            issues.append(f"第 {idx} 页缺 data-page。")
        if not role:
            issues.append(f"第 {idx} 页缺 data-role。")
        roles.append(role.group(1) if role else "")
        titles.append(slide_title(inner))
        slide_texts.append(text_of(re.sub(r"<div[^>]*class=[\"']page-num[\"'][^>]*>.*?</div>", "", inner, flags=re.S)))

    rc = Counter(roles)
    if n and rc.get("cover", 0) == 0:
        issues.append('没有封面页（data-role="cover"）。')
    if n and rc.get("agenda", 0) != 1:
        issues.append(f'模块导览页（data-role="agenda"）应正好一页，现在有 {rc.get("agenda", 0)} 页。')
    if expected_pages and n != expected_pages:
        warnings.append(f"页数 {n} 与逐页框架的 {expected_pages} 页不一致。")
    elif n and not 8 <= n <= 30:
        warnings.append(f"共 {n} 页，请确认和分享时长匹配（15 分钟约 10–14 页，20–30 分钟约 15–24 页）。")
    if n and len(set(roles)) < 5:
        warnings.append(f"只用了 {len(set(roles))} 种版式：{sorted(set(roles))}。建议至少 5 种，按内容关系选择。")

    for pat, label in EXTERNAL_RES:
        if pat.search(html):
            issues.append(f"引用了网络资源：{label}。演示稿要单文件可打开，资源请内嵌。")
    if CODE_RESIDUE_RE.search(body_html + css):
        issues.append("文件里残留脚本代码（如 html += 、三引号、# SECTION）。请直接写 HTML，或运行脚本后把输出写进文件。")
    if "【示例】" in raw:
        issues.append("还有模板示例文字「【示例】」没有替换。")

    widths = [float(w) for w in BORDER_LEFT_RE.findall(html)] + [float(w) for w in BORDER_LEFT_WIDTH_RE.findall(html)]
    if any(w >= 2 for w in widths):
        issues.append("使用了 2px 以上的左侧边条（border-left）。区分和强调请用浅色底色、细线、字重，不用左侧彩色边条。")
    if SHADOW_RE.search(html):
        warnings.append("使用了阴影（box-shadow）。层次请用底色交替、细线和留白来区分。")

    for sel, decl in CSS_RULE_RE.findall(css):
        if "deck-hint" in sel or "@" in sel:
            continue
        for px in FONT_PX_RE.findall(decl):
            if float(px) < 18:
                issues.append(f"字号 {px}px 小于 18px：{sel.strip()[:60]}。会场后排看不清。")
    for px in FONT_PX_RE.findall(" ".join(re.findall(r"style=[\"']([^\"']*)[\"']", body_html))):
        if float(px) < 18:
            issues.append(f"行内样式里有 {px}px 的字号，小于 18px。")

    if not re.search(r"addEventListener\(\s*['\"]resize['\"]", html):
        issues.append("缺少缩放脚本（resize 监听），窄屏下页面会被裁切。请保留模板里的 <script>。")
    if not re.search(r"addEventListener\(\s*['\"]keydown['\"]", html):
        warnings.append("缺少键盘跳页脚本。")
    if not re.search(r"@media\s+print", html):
        warnings.append("缺少打印样式，导出 PDF 可能分页错乱。")
    if "prefers-color-scheme" not in html:
        warnings.append("缺少深色模式配色。")

    # 导览页与过渡页
    agenda_items = []
    for (head, inner), role in zip(slides, roles):
        if role == "agenda":
            agenda_items = list(zip(all_by_class(inner, "agenda-num"), all_by_class(inner, "agenda-title")))
    openers = [(first_by_class(inner, "opener-num"), first_by_class(inner, "opener-title") or slide_title(inner))
               for (head, inner), role in zip(slides, roles) if role == "module-opener"]
    if agenda_items and openers:
        if len(agenda_items) != len(openers):
            warnings.append(f"导览页列了 {len(agenda_items)} 个模块，但有 {len(openers)} 个模块过渡页。")
        for i, ((an, at), (on, ot)) in enumerate(zip(agenda_items, openers), 1):
            if at != ot:
                warnings.append(f"第 {i} 个模块标题不一致：导览页「{at}」，过渡页「{ot}」。两处要逐字一致。")
            if not on:
                warnings.append(f"第 {i} 个模块过渡页没有编号，建议用大号编号让听众知道进入了第几部分。")
            elif an and an != on:
                warnings.append(f"第 {i} 个模块编号不一致：导览页 {an}，过渡页 {on}。")

    # 封面
    for (head, inner), role, t in zip(slides, roles, slide_texts):
        if role == "cover":
            if NUM_UNIT_RE.search(t.replace("【示例】", "")) or re.search(r"(?<!\d)0[1-9](?!\d)", t):
                warnings.append("封面出现了数字或序号。封面只放主标题、副标题、分享人和公司。")

    # 重复数字
    seen = defaultdict(set)
    for idx, t in enumerate(slide_texts, 1):
        for num, unit in NUM_UNIT_RE.findall(t):
            if unit == "年" and len(num) == 4:
                continue
            seen[f"{num}{unit}"].add(idx)
    dups = {k: sorted(v) for k, v in seen.items() if len(v) > 1}
    for k, pages in sorted(dups.items(), key=lambda kv: kv[1]):
        warnings.append(f"数字「{k}」出现在第 {pages} 页。同一个数字尽量只在一页出现。")

    # 相邻标题过于相似
    for i in range(1, len(titles)):
        a, b = bigrams(titles[i - 1]), bigrams(titles[i])
        if a and b and len(a & b) / len(a | b) >= 0.5:
            warnings.append(f"第 {i} 页和第 {i + 1} 页标题意思接近：「{titles[i - 1]}」/「{titles[i]}」。")

    # 文字
    all_text = " ".join(slide_texts)
    tp = find_third_person(all_text, speakers)
    if tp:
        issues.append("出现第三人称写法（演示稿应是分享人自己讲）：" + "；".join(tp[:5]))
    if not speakers:
        warnings.append("没有提供 --speaker，跳过了「某某意识到」这类写法的检查。")
    ai = find_ai_phrases(all_text)
    if ai:
        warnings.append("可能是 AI 腔或自造词，请确认是否换成平实说法：" + "、".join(f"{w}×{c}" for w, c in ai))

    print("=" * 72)
    print(f"演示稿校验：{p.name}　共 {n} 页")
    print(f"版式分布：{dict(rc)}")
    print("=" * 72)
    print("\n标题连读：")
    for i, (r, t) in enumerate(zip(roles, titles), 1):
        print(f"  P{i:02d} [{r}] {t}")
    if issues:
        print("\n严重问题")
        for x in issues:
            print(f"- {x}")
    if warnings:
        print("\n警告")
        for x in warnings:
            print(f"- {x}")
    if not issues and not warnings:
        print("\n通过：没有发现问题。")
    elif not issues:
        print("\n通过，但有警告，请逐条确认。")
    else:
        print("\n有严重问题，修复后再交付。")
    return not issues


def main():
    ap = argparse.ArgumentParser(description="校验客户分享 HTML 演示稿")
    ap.add_argument("deck")
    ap.add_argument("--speaker", action="append", default=[], help="分享人的称呼，可写多次")
    ap.add_argument("--expected-pages", type=int, default=0, help="逐页框架确定的页数")
    a = ap.parse_args()
    return 0 if validate(a.deck, a.speaker, a.expected_pages) else 1


if __name__ == "__main__":
    sys.exit(main())
