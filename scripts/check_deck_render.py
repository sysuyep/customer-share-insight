#!/usr/bin/env python3
"""
在无界面浏览器里打开 HTML 演示稿，逐页检查实际渲染结果。

检查项（按 1920×1080 画布坐标）：
- 元素超出画布边界（文字被裁掉）
- 正文落进底部 140px（会场后排看不到；页码除外）
- 字号：小于 18px 报严重问题；18–23px 且文字较长时提示"正文偏小"
- 标题最后一行只剩一两个字

可选：--screenshots 目录   每页截一张图，文件名 P01.png、P02.png……
可选：--dark               用深色模式渲染再检查一遍配色

依赖：Python 版 Playwright（pip install playwright，再运行 playwright install chromium）。
没有安装时脚本会提示，并以退出码 2 结束，不影响其他校验脚本。

用法：
  python3 scripts/check_deck_render.py deck.html
  python3 scripts/check_deck_render.py deck.html --screenshots shots/
"""

import argparse
import json
import sys
from pathlib import Path

JS_CHECK = r"""
() => {
  const SAFE_BOTTOM = 1080 - 140;
  const skipBottom = ['page-num', 'photo', 'shade', 'photo-note', 'deck-hint'];
  const titleSel = '.title, .cover-title, .opener-title, .claim, .quote-text, .closing-main, h1, h2';
  const out = [];
  document.querySelectorAll('section.slide').forEach((slide, idx) => {
    const sr = slide.getBoundingClientRect();
    const scale = sr.width / 1920;
    const page = slide.getAttribute('data-page') || String(idx + 1);
    const role = slide.getAttribute('data-role') || '';
    const issues = [], warnings = [];
    const hasClass = (el, names) => {
      for (let e = el; e && e !== slide; e = e.parentElement) {
        if (names.some(n => e.classList && e.classList.contains(n))) return true;
      }
      return false;
    };
    const textOf = el => Array.from(el.childNodes)
      .filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();

    slide.querySelectorAll('*').forEach(el => {
      const own = textOf(el);
      if (!own) return;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return;
      const top = (r.top - sr.top) / scale, bottom = (r.bottom - sr.top) / scale;
      const left = (r.left - sr.left) / scale, right = (r.right - sr.left) / scale;
      const snippet = own.slice(0, 18);
      if (right > 1921 || bottom > 1081 || left < -1 || top < -1) {
        issues.push(`文字超出画布：「${snippet}」`);
      } else if (bottom > SAFE_BOTTOM + 4 && !hasClass(el, skipBottom)) {
        warnings.push(`文字落进底部 140px：「${snippet}」（底边 y=${Math.round(bottom)}）`);
      }
      const fs = parseFloat(cs.fontSize);
      if (!hasClass(el, ['deck-hint'])) {
        if (fs < 18) issues.push(`字号 ${fs}px 小于 18px：「${snippet}」`);
        else if (fs < 24 && own.length > 20) warnings.push(`正文字号 ${fs}px 偏小（建议不小于 24px）：「${snippet}」`);
      }
    });

    slide.querySelectorAll(titleSel).forEach(el => {
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const rects = [];
      while (walker.nextNode()) {
        const range = document.createRange();
        range.selectNodeContents(walker.currentNode);
        Array.from(range.getClientRects()).forEach(rc => { if (rc.width > 0) rects.push(rc); });
      }
      if (rects.length < 2) return;
      const lines = {};
      rects.forEach(rc => {
        const key = Math.round(rc.top / 4);
        lines[key] = (lines[key] || 0) + rc.width;
      });
      const keys = Object.keys(lines).map(Number).sort((a, b) => a - b);
      if (keys.length < 2) return;
      const lastWidth = lines[keys[keys.length - 1]];
      const em = parseFloat(getComputedStyle(el).fontSize) * scale;
      if (lastWidth < em * 2.2) {
        warnings.push(`标题最后一行只剩一两个字：「${el.textContent.trim().slice(0, 20)}」`);
      }
    });

    const title = (slide.querySelector(titleSel) || {}).textContent || '';
    out.push({ page, role, title: title.trim().replace(/\s+/g, ' '), issues, warnings });
  });
  return out;
}
"""


def main():
    ap = argparse.ArgumentParser(description="逐页检查 HTML 演示稿的实际渲染结果")
    ap.add_argument("deck")
    ap.add_argument("--screenshots", help="每页截图保存到这个目录")
    ap.add_argument("--dark", action="store_true", help="用深色模式渲染")
    args = ap.parse_args()

    deck = Path(args.deck).resolve()
    if not deck.is_file():
        print(f"错误：文件不存在 — {deck}")
        return 1
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("未安装 Python 版 Playwright，跳过渲染检查。")
        print("安装：pip install playwright && playwright install chromium")
        print("没有条件安装时，请在浏览器里打开演示稿逐页看一遍。")
        return 2

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # 浏览器内核没装
            print(f"无法启动浏览器：{e}")
            print("请运行：playwright install chromium")
            return 2
        try:
            page = browser.new_page(
                viewport={"width": 1984, "height": 1200},
                color_scheme="dark" if args.dark else "light",
            )
            page.goto(deck.as_uri())
            page.wait_for_timeout(400)
            results = page.evaluate(JS_CHECK)
            if args.screenshots:
                outdir = Path(args.screenshots)
                outdir.mkdir(parents=True, exist_ok=True)
                for i, el in enumerate(page.query_selector_all(".slide-wrapper"), 1):
                    el.screenshot(path=str(outdir / f"P{i:02d}.png"))
        finally:
            browser.close()

    n_issue = sum(len(r["issues"]) for r in results)
    n_warn = sum(len(r["warnings"]) for r in results)
    print("=" * 72)
    print(f"渲染检查：{deck.name}（{'深色' if args.dark else '浅色'}模式），共 {len(results)} 页")
    print("=" * 72)
    for r in results:
        if not r["issues"] and not r["warnings"]:
            continue
        print(f"\nP{r['page']}（{r['role']}）{r['title'][:30]}")
        for it in r["issues"]:
            print(f"  严重：{it}")
        for it in r["warnings"]:
            print(f"  警告：{it}")
    if args.screenshots:
        print(f"\n截图已保存到：{Path(args.screenshots).resolve()}")
    print(f"\n合计：严重问题 {n_issue} 条，警告 {n_warn} 条。")
    return 1 if n_issue else 0


if __name__ == "__main__":
    sys.exit(main())
