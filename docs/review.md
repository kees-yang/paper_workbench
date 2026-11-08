# The review page

**English** · [简体中文](review.zh-CN.md)

`paper_workbench review` puts one or more built workbench pages into one compact page for reading and review. Use it to read a paper
sentence by sentence, to compare two versions or two candidate papers side by side, and to keep a log of review scores.
It reads the data that `paper_workbench workbench` already wrote, so build the workbench of each paper first.

```bash
python -m paper_workbench workbench my-paper                           # writes my-paper/out/workbench.html
python -m paper_workbench review main=my-paper alt=other-paper --out review.html \
       --names "MyNet,MSRS,TNO" --scores review/score_log.json
```

Each argument is `NAME=PAGE`: `PAGE` is a built `workbench.html` or a project folder (its `out/workbench.html` is used), and
`NAME` labels the tab. The page is one offline file.

> **Treat the page like the manuscript.** It embeds the whole text and the PDF pages of every paper. Do not publish the page
> of an unpublished paper.

## Views

| View | What it shows |
|---|---|
| **Sentences** | One paragraph at a time: its question, claim and the claim it follows, then a table with one row per sentence. Each row holds the original sentence with its subject, predicate and object underlined (blue, red, green), the rendering (hide it with the 中文 switch), and the link to the previous sentence: the relation, the anchor phrase and the phrase it leads to. A red **no link** chip marks a sentence that does not pick up the one before; the paragraph list marks such paragraphs with an amber dot. Earlier links (to text further back) show as a second chip. The linked phrases are tinted at both ends, in the sentence and in the sentence it picks up, with the head noun in bold. The PDF page with the paragraph box sits on the right. |
| **Abbreviations** | The first use of each abbreviation in the abstract, the body and the supplement, with its status. **defined**: a definition stands at the first use. **undefined**: it needs one. **name**: a method, dataset or tool name that needs none. |
| **Flow** | The paper as one shortcut. (1) Each abstract slot, then the introduction and body paragraphs that expand it and the conclusion items that answer it; an empty cell is a part of the abstract the paper does not carry through. (2) The structure of each part: the abstract as background or necessity → question → motivation → novel points (three expected) → result; the introduction as background, related work, question, motivation, method and contribution, with the words of each part; the conclusion as the answer to the research question (a conclusion item that mirrors the question slot). (3) The storylines: each claim from the abstract to the conclusion with the checks of each step (expands, not a copy, key concepts kept, echoes) and the open issues. Parts are found from the slot names and paragraph moves of the annotation file (`workbench.json`). |
| **Notes** | A note per sentence (click a sentence to write one). Notes stay in the browser; **Export notes** saves them as Markdown. |
| **Scores** | The review score log, if you pass `--scores`: a chart of the score per round and per line, a table of rounds with the change and the top finding, versions not yet reviewed, and open issues. |

Search covers the original and the rendering of every sentence.

## Options

| Option | Meaning |
|---|---|
| `--out FILE` | Output file (default `review.html`). |
| `--names LIST` or `--names @FILE` | Names that need no definition, separated by commas, spaces or new lines; repeat the option to add more. Venue, framework and hardware names (CVPR, PyTorch, GPU, …) are built in. |
| `--supp-from TEXT` | The supplement starts at the first chapter or section that starts with `TEXT`. By default it starts at the first chapter whose title contains *appendix*, *supplement*, 附录 or 补充. |
| `--supp-page N` | Rows on PDF page `N` or later also belong to the supplement (for a paper and supplement compiled as one PDF). |
| `--scores FILE` | The score log (below). |
| `--title TEXT` | Page title. |

## What counts as a definition

The check reads the sentence of the first use. These forms count: `long form (ABBR)`, `ABBR (long form)` with a lowercase long
form, `ABBR is the …` (also *are*, *denotes*, *measures*, *gives*), and a caption label `ABBR: lowercase …`. The check is a
pattern match: read every flagged sentence before you change it.

## Score log format

```json
{
  "target": 8,
  "note": "Scores from the same reviewer setup.",
  "rounds": [
    {"line": "main", "round": "R1", "version": "v3", "model": "reviewer-a", "score": 5, "verdict": "not ready",
     "changes": "what changed before this round", "top": "the top finding"},
    {"line": "main", "round": "R2", "version": "v4", "model": "reviewer-a", "score": 6, "verdict": "almost"}
  ],
  "unreviewed": [{"line": "main", "versions": "v5", "changes": "fixes since R2"}],
  "bottlenecks": [{"issue": "…", "rounds": "R1, R2", "status": "Open", "evidence": "…"}]
}
```

Only `rounds[].score` is required. `line` groups rounds into one curve per paper (default `paper`). A change of `model` between
two rounds draws a marker, because scores from different reviewers are not comparable. `status` values that start with *Open*
or *Addressed* get a colour.
