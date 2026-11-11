# customer-share-insight · 客户洞察分享

把企业家或学员的访谈录音转写、教练入企对谈，做成由分享人本人上台讲的经营分享：HTML 演示稿、逐页讲稿、内部客户洞察报告；需要时再转成带演讲备注的可编辑 PPT 和中英双语讲稿。也可以在访谈前帮你做背景调研、写访谈大纲。

适用于 Claude（Claude Code、Claude 桌面应用）和 Codex。当前版本：**v1111001**（2026-11-11）。

## 适合什么场景

- 请总裁班同学、企业家客户在线下课程现场做经营分享，需要准备演示稿和讲稿。
- 手上有一份访谈或教练对谈的录音转写，想整理成客户故事、案例分享。
- 要去访谈某位同学，需要先查背景、写访谈大纲。

只需要一份独立的客户洞察报告、不做分享演示稿时，用 customer-insight Skill。

## 工作流程

本流程分六个阶段，每个阶段结束都会停下来等你确认，再进入下一阶段。阶段 0 和阶段 5 按需使用。

| 阶段 | 做什么 | 你需要确认什么 |
|---|---|---|
| 0 访谈准备 | 背景调研、访谈大纲（不超过 18 题，带预设追问）、素材清单 | 大纲能不能用 |
| 1 分析初稿 | 整理事实、公开范围、关键决定、待核实问题、素材缺口 | 事实是否准确、哪些能公开、分享时长和最终要哪些文件 |
| 2 三个方向 | 三个组织方式不同的分享方向，各带模块架构 | 选哪个，或怎么融合 |
| 3 逐页框架 | 每页的上屏文字和讲稿要点分开写，附标题连读和自查结果 | 每页内容和顺序 |
| 4 样稿与成品 | 先做视觉样稿比较，再生成演示稿、讲稿、洞察报告 | 样稿选哪版；成品要不要改 |
| 5 交付转换 | 可编辑 PPT、演讲备注、中英双语讲稿 PDF | 是否可以交付 |

第 3 步最关键。过去的案例里，一半以上的时间花在成品做完之后的返工上，而页面跳跃、讲述句被放上页面、数字重复这些问题，大多能在逐页框架里提前发现。

## 产出文件

| 文件 | 说明 |
|---|---|
| `{客户}_{主题}_deck.html` | 演示稿，1920×1080，滚动浏览，可打印成 PDF，跟随系统切换深色模式 |
| `{客户}_{主题}_speaker_notes.md` | 逐页讲稿：讲述方向、讲稿参考、过渡到下一页 |
| `{客户}_{主题}_insight_report.html` | 内部客户洞察报告，六章固定结构，手机上也能看 |
| `{客户}_{主题}_editable.pptx` | 可编辑 PPT，演讲备注写在每页（阶段 5） |
| `{客户}_{主题}_speaker_notes_bilingual.pdf` | 中英双语讲稿（阶段 5） |

## 安装

### Claude Code 和 Codex

建议把仓库放在一个位置，再用链接给两边使用：

```bash
git clone https://github.com/sysuyep/customer-share-insight.git ~/.agents/skills/customer-share-insight
```

```bash
ln -s ../../.agents/skills/customer-share-insight ~/.claude/skills/customer-share-insight
```

```bash
ln -s ../../.agents/skills/customer-share-insight ~/.codex/skills/customer-share-insight
```

以后更新只需要在 `~/.agents/skills/customer-share-insight` 里运行 `git pull`。

### Claude 桌面应用或网页版

把本仓库打包成 `.skill` 文件（可用 skill-creator 自带的打包脚本），在技能设置里上传。

## 使用示例

访谈前：

```text
使用 customer-share-insight。下周要访谈我们班的陈总，他在佛山做商用空调安装和维保，背景资料在 background.md，帮我准备访谈大纲。
```

拿到转写稿后：

```text
参考 customer-share-insight，把这份访谈做成同学分享：[转写稿路径]。
分享人是王总本人，在总裁班课上讲给其他企业老板，约 20 分钟，中文。
最后需要可编辑 PPT，备注写进 PPT。从阶段 1 开始，每个阶段等我确认。
```

## 目录结构

```text
customer-share-insight/
├── SKILL.md                 Skill 主文件：流程、内容原则、页面要求
├── agents/openai.yaml       Codex 的显示名称和默认提示
├── references/              各阶段的详细说明，按需读取
│   ├── interview-prep.md    阶段 0：背景调研、访谈大纲
│   ├── narrative.md         阶段 1、2：提炼素材、切分模块
│   ├── page-plan.md         阶段 3：逐页框架、标题连读
│   ├── visual-style.md      阶段 4：配色、字体、照片、样稿
│   ├── deck-guide.md        阶段 4：版式、字数上限、交付前检查
│   ├── insight-report.md    阶段 4：洞察报告结构
│   ├── pptx-export.md       阶段 5：可编辑 PPT、备注、双语讲稿
│   └── common-mistakes.md   执行中的常见错误
├── assets/
│   ├── deck-template.html            演示稿模板（19 种版式）
│   └── insight-report-template.html  洞察报告模板
├── scripts/                 校验和转换脚本
└── evals/                   测试用例（打包安装时不包含）
```

## 校验脚本和依赖

| 脚本 | 作用 | 依赖 |
|---|---|---|
| `validate_html_deck.py` | 演示稿结构、外链、禁用的视觉写法、重复数字、第三人称、AI 腔，打印标题连读 | Python 3.9+ |
| `check_deck_render.py` | 逐页渲染检查：溢出、底部区域、字号、标题单字掉行，并逐页截图 | Python 版 Playwright（可选） |
| `validate_speaker_notes.py` | 讲稿与演示稿页数对应、舞台动作栏目、来源和路径残留 | Python 3.9+ |
| `validate_insight_report.py` | 洞察报告六章结构、章节标题是否写结论、手机适配 | Python 3.9+ |
| `notes_to_pptx.py` | 把逐页讲稿写进 PPT 演讲备注 | python-pptx |
| `check_pptx.py` | PPT 页数、备注、是否有整页截图 | python-pptx |

渲染检查需要先安装 Playwright：

```bash
pip install playwright && playwright install chromium
```

## 测试用例

`evals/` 下有 6 个测试用例，每个用例一个文件夹，覆盖访谈大纲、阶段 1 停下确认、教练对谈不编造历史、修复旧框架、写逐页框架、生成三个文件。测试材料都是虚构的。

用 Claude Code（v2.1.269 及以上）在本目录运行：

```bash
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

这会真实调用模型并产生费用。`evals/evals.json` 是旧格式的测试，已被同名的用例文件夹替代，保留作参考。

## 注意

- 真实客户的访谈转写、照片和生成的成品不要提交到本仓库，放在各自的项目文件夹里。
- 修改 Skill 后，同时更新 SKILL.md 开头的 `version` 和 `updated`，以及本文件开头的版本号。
