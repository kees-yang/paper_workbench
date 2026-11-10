# Credits and design references

**English** · 中文见下文

paper_workbench borrows ideas from the work below. It copies no code or text from the design references. Libraries are used as
dependencies under their own licenses. None of the people or organizations listed endorse this project.

## Writing rules

**ASD-STE100 Simplified Technical English.** ASD (AeroSpace, Security and Defence Industries Association of Europe),
Specification ASD-STE100. https://www.asd-ste100.org/

The sentence rules of the default pack adapt these STE principles to scientific prose:

| STE principle | paper_workbench rules |
|---|---|
| active voice | `W10` |
| one topic per sentence | `W14`: one main action per sentence |
| no ambiguous `-ing` constructions | `W15`: complete clauses, no comma participle phrases |
| one word, one meaning | `A3`, `A6`, `A7`: glossary terms and head nouns |
| plain, approved words | `M1`: plain words and direct verbs |

paper_workbench does not claim STE compliance. It uses no STE dictionary. Sentence length is limited only by the opt-in rule
`W23`, with a limit the project sets. It keeps the technical terms a paper needs. Obtain the specification from ASD.

**"80% of the way to ASD-STE100."** A. Karpathy, post on X, 2 October 2026.
https://x.com/karpathy/status/2105819303471976479

The post suggested asking models to write about 80% of the way to ASD-STE100, so that their output is easier to read. The
default pack follows that idea: it applies the STE principles above and leaves the rest of the standard out.

**Old before new and topic chains.** The flow marks of the review page and the opt-in rule `W21` follow two descriptions of
coherent prose: G. D. Gopen and J. A. Swan, “The Science of Scientific Writing”, American Scientist 78(6), 1990 (old
information at the start of a sentence, new information at its end), and F. Daneš, “Functional sentence perspective and the
organization of the text”, in Papers on Functional Sentence Perspective, 1974 (linear and constant thematic progression). The
marks are a word-overlap heuristic, not an implementation of either work.

The other rules come from the authors' own revision rounds on manuscripts, and their reasons are given in the register:

- the rule tree, which says to revise at the highest failing stage;
- strengths first;
- no filler;
- consequence connectives;
- the abstract structure;
- table order;
- the figure rules;
- caption length, float pages, the selection clause and the body that stands alone;
- affirmative wording and the roles of the abstract numbers.

## Interface

**Obsidian.** https://obsidian.md

The interface design of paper_workbench draws inspiration from Obsidian:

- the workbench (`paper_workbench workbench`) is a calm, note-like reading surface;
- it has panes side by side, with tabs and a collapsible outline;
- items link to each other, so a sentence, its rule, its number and its source are one click apart.

The offline HTML report keeps the outline style: findings sit under their rule along the rule tree, and each rule folds open.

**Blender node editor.** https://www.blender.org

The argument canvas of the workbench, where claims and evidence are boxes joined by links, follows the node-editor
style. No code or text of Blender is used.

## Libraries and tools

| Used for | Project | License | Citation |
|---|---|---|---|
| sentence parsing (`W14`–`W16`, `A6`) | spaCy, https://spacy.io, and the `en_core_web_sm` model | MIT | M. Honnibal, I. Montani, S. Van Landeghem, A. Boyd, spaCy: Industrial-strength Natural Language Processing in Python, 2020, doi:10.5281/zenodo.1212303 |
| figure-file rules `G1`–`G4` and the PDF pane of the workbench (optional extras `figures`, `workbench`) | PyMuPDF, https://github.com/pymupdf/PyMuPDF | GNU AGPL-3.0 or Artifex commercial license | — |
| research workflow of the workspace this project grew out of | ARIS (Auto-claude-code-research-in-sleep), https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep | see its repository | — |
| development and testing | Claude Code (Anthropic) and Codex (OpenAI) coding agents | — | — |

paper_workbench itself is MIT-licensed and does not bundle PyMuPDF. PyMuPDF is installed only with `pip install -e ".[figures]"` or `".[workbench]"`,
and that install is under PyMuPDF's own license terms.

The example paper in `examples/aptp-cvpr2026/` is credited in [NOTICE](NOTICE) (CC BY 4.0).

---

## 中文

paper_workbench 借鉴了以下工作的思路。它没有复制这些设计参考中的代码或文字。依赖库按各自的许可使用。以下个人和机构均未为本项目背书。

**写作规则**

- **ASD-STE100 简化技术英语。** ASD（欧洲航空航天、安全与防务工业协会）发布的规范 ASD-STE100，https://www.asd-ste100.org/ 。默认规则包把 STE 的以下原则改写为适用于科研论文的规则：
  - 主动语态（`W10`）；
  - 一句一个主题（`W14`：一句一个主要动作）；
  - 不用有歧义的 -ing 结构（`W15`：从句完整，不用逗号分词短语）；
  - 一词一义（`A3`、`A6`、`A7`：术语表与中心名词）；
  - 用简单、规定的词（`M1`）。

  本项目不声称符合 STE，不使用 STE 词典；句长只由可选规则 `W23` 限制，上限由项目设定；并保留论文必需的术语。规范本身请向 ASD 获取。
- **“80% of the way to ASD-STE100”。** A. Karpathy 于 2026 年 10 月 2 日在 X 上发帖，https://x.com/karpathy/status/2105819303471976479 。帖子建议让模型的写法接近 ASD-STE100 的八成，使输出更易读。默认规则包按这一思路，只采用上述 STE 原则，不采用标准的其余部分。
- **旧信息在前与主题链。** 审阅页的衔接标记和可选规则 `W21` 依据两种对连贯文字的描述：G. D. Gopen 与 J. A. Swan，“The Science of Scientific Writing”，American Scientist 78(6)，1990（句首放旧信息，句末放新信息）；F. Daneš，“Functional sentence perspective and the organization of the text”，载 Papers on Functional Sentence Perspective，1974（线性与恒定的主位推进）。这些标记是基于词重叠的启发式方法，并非对两者的实现。
- 其余规则来自作者自己对稿件的多轮修改，理由写在规则登记中：
  - 规则树（先改最上层未通过的层）；
  - 先写优势；
  - 不写空话；
  - 结果连接词；
  - 摘要结构；
  - 表格行顺序；
  - 图件规则；
  - 图注长度、图表所在页、选例说明、正文自成一体；
  - 肯定式表述与摘要数字的角色。

**界面**

- **Obsidian**，https://obsidian.md 。本项目的界面设计借鉴了 Obsidian：
  - 工作台（`paper_workbench workbench`）采用安静、类似笔记的阅读界面；
  - 多栏并排，有标签页与可折叠的大纲；
  - 条目之间互相链接，从句子到规则、到数字、到来源只需点一下。

  离线 HTML 报告保留了大纲式布局：各条结果按规则树排在对应规则之下，每条规则都可以折叠展开。
- **Blender 节点编辑器**，https://www.blender.org 。工作台的论证画布采用节点编辑器风格，论点与证据是用连线相连的方框。没有使用 Blender 的任何代码或文字。

**库与工具**

- **spaCy**（MIT）及 `en_core_web_sm` 模型：用于句法分析（`W14`–`W16`、`A6`）。引用：M. Honnibal, I. Montani, S. Van Landeghem, A. Boyd, spaCy: Industrial-strength Natural Language Processing in Python, 2020, doi:10.5281/zenodo.1212303。
- **PyMuPDF**（GNU AGPL-3.0 或 Artifex 商业许可）：可选依赖，用于图件规则 `G1`–`G4` 与工作台的 PDF 面板。本项目采用 MIT 许可，不附带 PyMuPDF。只有用 `pip install -e ".[figures]"` 或 `".[workbench]"` 安装时才会装上它，安装后按 PyMuPDF 自己的许可使用。
- **ARIS**（Auto-claude-code-research-in-sleep），https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep ：本项目所源自的研究工作区使用它的研究工作流。
- **Claude Code**（Anthropic）与 **Codex**（OpenAI）编码智能体：用于开发与测试。
- 示例论文的署名见 [NOTICE](NOTICE)（CC BY 4.0）。
