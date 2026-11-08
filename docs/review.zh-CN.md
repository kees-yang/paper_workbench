# 审阅页

[English](review.md) · **简体中文**

`paperrules review` 把一个或多个已生成的工作台页面合成一个紧凑的审阅页。用它逐句阅读论文，并排比较两个版本或两篇候选论文，并记录审稿分数。
它读取 `paperrules workbench` 已写入的数据，所以先为每篇论文生成工作台。

```bash
python -m paperrules workbench my-paper                           # 生成 my-paper/out/workbench.html
python -m paperrules review main=my-paper alt=other-paper --out review.html \
       --names "MyNet,MSRS,TNO" --scores review/score_log.json
```

每个参数写作 `名称=页面`：页面是已生成的 `workbench.html`，或项目文件夹（使用其中的 `out/workbench.html`）；名称是标签页上的文字。输出是一个离线文件。

> **像对待稿件一样对待这个页面。** 它包含每篇论文的全文和 PDF 页面。不要公开未发表论文的页面。

## 视图

| 视图 | 内容 |
|---|---|
| **Sentences（句子）** | 每次一段：段落的问题、主张和承接的主张，然后是每句一行的表格。每行有原句、译文（用“中文”开关隐藏），以及与上一句的衔接：关系、锚点短语和它引出的短语。红色 **no link** 标记没有承接上一句的句子，段落列表用琥珀色圆点标出这样的段落。与更早文字的衔接显示为第二个标签。右侧是带段落框的 PDF 页面。 |
| **Abbreviations（缩写）** | 每个缩写在摘要、正文和补充材料中的首次出现及其状态。**defined**：首次出现处有定义。**undefined**：需要定义。**name**：方法、数据集或工具名，不需要定义。 |
| **Notes（笔记）** | 每句一条笔记（点击句子即可书写）。笔记保存在浏览器中，**Export notes** 将其导出为 Markdown。 |
| **Scores（分数）** | 传入 `--scores` 时显示审稿分数记录：各轮、各条线的分数图，每轮的变化和首要问题，尚未审阅的版本，以及未解决的问题。 |

搜索覆盖每句的原文和译文。

## 选项

| 选项 | 含义 |
|---|---|
| `--out FILE` | 输出文件（默认 `review.html`）。 |
| `--names 列表` 或 `--names @文件` | 不需要定义的名称，用逗号、空格或换行分隔，可重复使用。会议、框架和硬件名称（CVPR、PyTorch、GPU 等）已内置。 |
| `--supp-from 文字` | 补充材料从第一个以该文字开头的章或节开始。默认从标题含 *appendix*、*supplement*、附录或补充的第一章开始。 |
| `--supp-page N` | 第 N 页及之后的句子也属于补充材料（正文和补充材料编译为一个 PDF 时使用）。 |
| `--scores FILE` | 分数记录（见下）。 |
| `--title 文字` | 页面标题。 |

## 什么算定义

检查读取首次出现的句子。以下形式算作定义：`全称 (ABBR)`、`ABBR (小写全称)`、`ABBR is the …`（以及 *are*、*denotes*、*measures*、*gives*），以及图表标题中的标签 `ABBR: 小写 …`。这是模式匹配：修改之前请阅读每个被标出的句子。

## 分数记录格式

格式见英文文档中的 JSON 示例。只有 `rounds[].score` 是必填项。`line` 把各轮归入每篇论文的一条曲线（默认 `paper`）。相邻两轮的 `model` 不同时会画出标记，因为不同审稿人的分数不可比较。以 *Open* 或 *Addressed* 开头的 `status` 会着色。
