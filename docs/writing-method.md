# The writing method · [中文](writing-method.zh-CN.md)

This page collects the method for consistent, coherent writing that the rules of paper_workbench support. It names the rule for
each step, so a new paper project can switch the method on in one block. The method came from revision rounds on real
manuscripts. It holds no text or result of those manuscripts.

The author decides. Each rule below flags a sentence or a float; the author rewrites it, accepts it with a reason, or changes the
rule (`AGENTS.md` §1).

## Switch it on

Put this in the paper's `rules.local.json`. Every rule of the method that is off by default is listed, so remove the lines your
venue or author does not want. Read the numbers from the venue's guide for authors.

```jsonc
{
  "enable": ["W20", "E6", "E7", "J1",          // abstract: structure, number count, number roles, length
             "W21", "O3",                      // paragraphs: old before new, the body stands alone
             "W22", "W23",                     // sentences: affirmative wording, length
             "T11", "T12", "T13"],             // floats: caption length, page placement, selection clause
  "document": {
    "J1":  {"min": 150, "max": 250},
    "E6":  {"max_numbers": 2},
    "T11": {"min": 15, "max": 35},
    "T12": {"pages_after": 1}
  },
  "tone": {"W23": {"max_words": 25}}
}
```

`T12` reads the compiled PDF: set `"pdf": "main.pdf"` in `paper_workbench.json` (default: the workbench PDF, else `main.pdf`
beside `main.tex`). It needs PyMuPDF.

## 1. One thread from the abstract to the conclusion

| Step | What to do | Rule |
|---|---|---|
| Order | The abstract goes from old to new: the field, the gap, the motivation, the proposal, the mechanisms, what they provide, the results. | `W1` (manual) |
| Structure | One sentence states the proposal (“We propose …”). The mechanisms follow as First, Second, Third. One sentence after them states what the method provides. | `W20` |
| Numbers | The abstract holds few numbers, and each has a role: one shows the overall ability and one a specific ability, each as a lead over the runner-up. | `E6`, `E7` (manual) |
| Echo | The introduction expands each abstract sentence, and the conclusion answers it without a new claim. | `W4` (manual), the **Flow** view of the review page |

Check the abstract with `check --only W20,J1,E6` before you show it to the author. A proposal that fails its own structure rule
costs a round.

## 2. Sentences that hand over to each other

| Step | What to do | Rule |
|---|---|---|
| Old before new | A sentence opens with what the reader knows from the previous sentence and ends on the new information. | `W21`, the **old→new** mark |
| Topic chain | The subject picks up the previous predicate or object (linear) or repeats the previous subject (constant). A run of new subjects reads as a list. | the **topic** mark |
| Relation | A connective marks a real relation. A consequence connective appears once, and never before “we propose”. | `W13`, `M2` (manual), the **relation** mark |
| Rhythm | Three sentences with the same opening and nearly the same length read flat. | the **rhythm** mark |

`W21` flags only the clear case: no shared word, no pointing word, no connective and a new subject. The review page shows all
four marks under every sentence and a summary per paragraph ([review.md](review.md)). Read the first three words of each
sentence of a paragraph alone: they should tell its story.

## 3. Plain sentences

The sentence rules adapt ASD-STE100 at about 80% strictness (see `CREDITS.md`).

| Step | What to do | Rule |
|---|---|---|
| One idea | One main action per sentence, complete clauses, no qualifier appended after the last comma. | `W14`, `W15`, `W16` |
| Length | A sentence has at most 25 words (your limit in `W23.max_words`). | `W23` |
| Active voice | The actor is the subject. “We” appears only where the authors act. | `W10`, `W12` |
| Conditions first | A condition comes before the action. | `W11` |
| One term | One concept keeps one term and one head noun. Change the glossary first, then the text, figures and captions. | `A3`, `A6`, `A7` |
| Plain words | Direct verbs, no filler, exact values in place of vague words. | `M1` (manual), `W7` |

## 4. Affirmative wording

Write what the paper does and shows. Do not answer an imagined objection in advance.

| Step | What to do | Rule |
|---|---|---|
| No pre-emptive concession | Delete “we do not claim”, “admittedly”, “merely”, “serves only as”. State the fact. | `W22` |
| Conventions | A community convention (a metric set, a test protocol) is stated plainly with its source. It is not a weakness of this paper. | `W22` (by hand) |
| Strengths first | Self-criticism belongs in the limitation section, where the paper weighs it. | `W8`, `W9` |
| Real costs stay | A measured trade-off is a result. Report it with its value. | — |

The affirmative form never claims more than the evidence. If it would, use a neutral factual sentence or delete the sentence.
A measured negative result stays in the paper.

## 5. Floats that the text carries

| Step | What to do | Rule |
|---|---|---|
| Caption length | A caption has 15 to 35 words (your limits): what the float shows and how to read it. The mechanism stays in the text. | `T9` (manual), `T11` |
| Citation first | The text cites a float before it appears, in the source and on the page: the same page or the next. | `T1`, `T2`, `T12` |
| Selection | A figure of chosen cases says in a few words how they were chosen. It shows a phenomenon and does not present a named method as worse. | `T13` (manual) |
| Body stands alone | No body sentence points to the supplement. A claim is supported where it is made. | `O3` |
| Figures | One visual language, readable sizes, print-ready files. | `G1`–`G9` |

## 6. The revision loop

1. Write each revision into a new version folder. Never edit a delivered version.
2. Run `check`. Work from the highest failing stage of the rule tree down.
3. Build the workbench and the review page. Read the Flow view and the flow marks of every changed paragraph.
4. Record each change with the author's words and the evidence behind every number.
5. Before a proposal goes to the author, run the rules on the proposal itself.

## 7. Review rounds that can be compared

A mock review is useful only if its rounds can be compared.

- **Same setup every round.** One model, one effort setting, one prompt. Between rounds change only the version name in the prompt. If the setup changes, mark it in the score log and do not average across the change.
- **Isolated packet.** The reviewer gets the PDF and its page images in an empty folder. It reads no source, notes or earlier review.
- **Fresh context.** Each round starts with no memory of earlier rounds. `tools/review_fresh.sh` does this for the Codex CLI.
- **Audit.** Check the raw log: the commands the reviewer ran, the files it read, and that the packet did not change.
- **Do not chase the score.** A finding is a question. Fix what is true, state conventions plainly, and keep every claim inside its evidence.
