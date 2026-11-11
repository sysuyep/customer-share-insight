#!/usr/bin/env python3
"""
各校验脚本共用的文字检查：第三人称写法、常见 AI 腔和自造词、资料来源和文件路径。

清单里的词只做提示（警告），因为有些词在特定语境下是合理的。
审稿时发现新的问题表达，补进 AI_PHRASES 即可。
"""

import re

# 审稿中被指出过的表达，以及常见的自造词和网络腔
AI_PHRASES = [
    # 案例审稿中被指出过的
    "暴露", "据点", "跑得更快", "一张排程", "题目看清", "管优点", "从一个账",
    "案底", "反共识", "必读的纸", "最便宜的阶段", "会暂停的",
    # 自造的内部行话
    "门禁", "底账", "硬体检", "状态锚", "剥洋葱", "销账", "定摆法", "全家桶",
    "五件套", "四件套", "三件套", "暴雷", "收口", "挂起", "回填", "兜底",
    # 空泛的流行说法
    "赋能", "抓手", "颗粒度", "打通链路", "底层逻辑", "降维打击", "破局之道",
    # 拟人化、身体感强的动词用法
    "吃掉", "喂给", "吐出", "啃下",
]

THIRD_PERSON_VERBS = "意识到|认为|决定|觉得|发现|表示|坦言|带领|带着|的公司|的团队|开始|选择"

SOURCE_LINE_RE = re.compile(r"^\s*[-*]?\s*(\*\*)?\s*(来源|资料来源|依据|出处|Sources?|References?)\s*(\*\*)?\s*[:：]", re.I | re.M)
PATH_RE = re.compile(r"(/Users/[^\s)）]+|[A-Za-z]:\\[^\s]+|\S+\.(?:md|docx?|txt|pdf)\b)")


def find_ai_phrases(text):
    """返回 [(词, 次数)]，只列出现过的。"""
    hits = []
    for w in AI_PHRASES:
        n = text.count(w)
        if n:
            hits.append((w, n))
    return hits


def find_third_person(text, speakers):
    """检查"某某意识到""他决定"这类第三人称写法。speakers 为分享人的各种称呼。"""
    hits = []
    names = [re.escape(s) for s in speakers if s and s.strip()]
    patterns = []
    if names:
        patterns.append(re.compile(r"(?:%s)(?:先生|女士|总)?\s*(?:%s)" % ("|".join(names), THIRD_PERSON_VERBS)))
    patterns.append(re.compile(r"(?<![其吉])他(?:%s)" % THIRD_PERSON_VERBS))
    for pat in patterns:
        for m in pat.finditer(text):
            start = max(0, m.start() - 8)
            hits.append(text[start:m.end() + 8].replace("\n", " "))
    return hits


def find_sources_and_paths(text):
    hits = [m.group(0).strip() for m in SOURCE_LINE_RE.finditer(text)]
    hits += [m.group(0) for m in PATH_RE.finditer(text)]
    return hits
