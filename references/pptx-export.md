# 阶段 5：可编辑 PPT、演讲备注和双语讲稿

用户在阶段 1 选了这些格式，或者在 HTML 演示稿定稿后提出要可编辑 PPT 时，进入本阶段。

## 1. 可编辑 PPT

**要求：** 标题、正文、数字、线条、色块都是 PowerPoint 里能直接编辑的对象；只有照片是图片。不能把 HTML 每页截图后整页贴进 PPT，那样用户改一个字都改不了。

**做法：** 按已经定稿的 HTML 演示稿（以及逐页框架）用 python-pptx 重新搭建每一页，而不是让另一个模型"把 HTML 转成 PPT"。后者在过去的测试里视觉完全变样，还会丢字。

- 页面尺寸 16:9（13.333 × 7.5 英寸）。HTML 画布 1920×1080 对应 PPT 的换算：1px ≈ 0.00694 英寸；字号按 0.75 换算成磅（如 60px ≈ 45pt，28px ≈ 21pt）。
- 颜色、字体、版式沿用 HTML 版的视觉规则；中文字体用"微软雅黑"或"苹方"，并在文本框上同时设置东亚字体，避免在别的电脑上变成宋体。
- 折线图、柱状图用 PowerPoint 原生图表；数据标签显示不全时，在图上叠加可编辑文本框。
- 照片按 HTML 版的裁切位置放置；渐变遮罩用半透明形状实现。
- 本机如果装了 ppt-master Skill，也可以用它生成，但完成后同样要用下面的脚本检查。

运行 python-pptx 需要对应的 Python 环境。全局 Python 缺少依赖时，换用已经装好 python-pptx 的虚拟环境，或先安装：`pip install python-pptx`。

## 2. 写入演讲备注

用脚本把逐页讲稿写进对应页的备注区，不要手工粘贴或用简单的正则切分（过去出现过只写进标题、正文被截掉的问题）：

```bash
python3 <SKILL_DIR>/scripts/notes_to_pptx.py deck.pptx speaker_notes.md -o deck_with_notes.pptx
```

- 脚本按 `## P# · 标题` 切分讲稿，第 N 段写入第 N 页；页数对不上会报错。
- 默认去掉"来源""依据""Sources"等行和文件路径，备注里只留讲述内容。需要保留时加 `--keep-sources`。
- 讲稿里如果每页有 `**English**` 段，会一并写入（中文在前、英文在后）。

## 3. 检查 PPT

```bash
python3 <SKILL_DIR>/scripts/check_pptx.py deck_with_notes.pptx --expected-slides 22
```

检查页数、每页备注是否为空、是否有整页图片的页面、备注里是否残留来源和路径。严重问题修完再交付。条件允许时，再用 PowerPoint 或 Keynote 打开看一遍换行和字体。

## 4. 中英双语讲稿

- 中文原稿保持原意，英文按现场演讲的口吻翻译，不逐字直译；金额和数量转换成英文习惯写法（如"300 多万马币"写成 over RM3 million）。
- 全篇第一人称，人名、公司名、产品名的译法全篇统一。
- 讲稿 Markdown 每页结构：

```markdown
## P5 · 页面标题

**讲稿参考**：
中文讲稿……

**English**:
English script...
```

- 输出 PDF：把讲稿排成 A4 的 HTML（每页对应一张幻灯片，先中文后英文，页眉写页码和页面标题），再用浏览器打印成 PDF，命名 `{customer}_{topic}_speaker_notes_bilingual.pdf`。打印前确认页数和幻灯片一致。

## 5. 交付

回复里分别给出每个文件的完整路径，说明做过哪些检查（页数、备注、可编辑对象数量、是否在 PowerPoint 里打开过），哪些没有验证。
