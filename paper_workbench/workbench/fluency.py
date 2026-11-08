"""Sentence flow: how each sentence hands over to the one before it. Four methods, each made visible per sentence.

  old before new   The words a sentence shares with the previous sentence (or a word that points back: this, these, such, it, ...) are
                   the old information. Fluent prose puts them early, in the first two fifths of the sentence, and ends on new
                   information. Status: old first, old late, or no old words.
  topic chain      The subject of a sentence against the previous sentence. linear: the subject picks up the previous sentence's
                   second half (its predicate and object). constant: the subject repeats the previous subject. new: the subject
                   shares nothing with the previous sentence. A run of new subjects reads as a list, not as an argument.
  relation         The logical relation to the previous text and the word that signals it (table RELATIONS). implicit: no signal
                   word. Not every sentence needs a signal; a relation the reader must guess is worth one.
  rhythm           How the sentence opens (subject, connective, clause, phrase, ordinal) and its length. A run of three or more
                   sentences with the same opening and nearly the same length reads flat.
The analysis reads the English sentence and the subject spans of the workbench. It is a heuristic: read each mark, do not obey it.
"""
import re

STOP = set("""a an the of to in on at by for with from into onto over under than then that this these those it its they them their
there here which who whom whose what when where while as and or but nor so if not no is are was were be been being has have had do does
did can could may might must shall should will would each every all any both either neither one per via about after before across
between through during without within more most less least only also such same other another we our us you your he she his her""".split())
POINT = {"this", "these", "that", "those", "such", "it", "its", "they", "their", "them", "both", "here", "thus", "hence"}
# relation types, the words that signal them at or near the start of a sentence, and a plain definition
RELATIONS = [
    ("cause", "gives the reason for the previous statement", ["because", "since", "as a result of", "due to", "owing to"]),
    ("result", "follows from the previous statement", ["therefore", "thus", "hence", "so", "consequently", "as a result", "accordingly", "which makes", "this makes"]),
    ("contrast", "opposes or differs from the previous statement", ["however", "but", "in contrast", "by contrast", "whereas", "unlike", "instead", "yet", "on the other hand", "conversely"]),
    ("concession", "admits a point and limits it", ["although", "though", "even though", "despite", "nevertheless", "nonetheless", "still"]),
    ("addition", "adds a point of the same kind", ["also", "moreover", "in addition", "furthermore", "besides", "likewise", "similarly", "alongside"]),
    ("example", "gives a case of the previous statement", ["for example", "for instance", "such as", "e.g."]),
    ("elaboration", "restates or narrows the previous statement", ["that is", "in other words", "namely", "specifically", "in particular", "indeed"]),
    ("sequence", "orders steps or parts", ["first", "second", "third", "fourth", "then", "next", "finally", "lastly"]),
    ("purpose", "states what an action is for", ["to ", "in order to", "so that"]),
    ("condition", "states when the statement holds", ["if", "when", "unless", "once", "where"]),
    ("summary", "closes or generalises a span", ["in summary", "overall", "in short", "together", "in sum"]),
]
SUBORD = {"because", "although", "though", "since", "when", "if", "while", "whereas", "once", "unless", "as", "to"}
PREP = {"in", "on", "under", "without", "with", "for", "during", "after", "before", "across", "at", "by", "from", "over", "on", "among", "beyond", "unlike", "despite", "through"}
CONN = {"however", "therefore", "thus", "hence", "so", "also", "moreover", "furthermore", "besides", "consequently", "instead", "yet", "still", "indeed", "nevertheless", "nonetheless", "accordingly", "similarly", "likewise", "overall", "together", "alongside"}
ORD = {"first", "second", "third", "fourth", "fifth", "finally", "lastly", "then", "next"}
WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-]*")


def stem(w):
    w = w.lower()
    for a, b in (("ies", "y"), ("sses", "ss"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if w.endswith(a) and len(w) - len(a) >= 4:
            return w[:len(w) - len(a)] + b
    return w


def tokens(t):
    return [(m.start(), m.end(), m.group(0)) for m in WORD.finditer(t or "")]


def content(toks):
    return {stem(w) for _, _, w in toks if w.lower() not in STOP and len(w) > 2}


INSIDE = [("result", ", so "), ("result", ", which makes "), ("result", " therefore "), ("result", " thus "), ("contrast", ", whereas "),
          ("contrast", ", but "), ("contrast", ", yet "), ("contrast", ", while "), ("cause", " because "), ("purpose", " so that "),
          ("example", " such as "), ("example", " for example"), ("condition", " where ")]


FIRST_ONLY = {"but", "yet", "whereas", "so", "although", "though", "even though", "despite", "unlike", "instead", "as a result of", "due to",
              "owing to", "such as", "so that", "in order to", "still"}   # these join clauses; at the sentence start they link back


def relation(t):
    """The relation to the previous text: the first signal word among the first six words ('start'), else 'implicit'. Also the
    first relation marked inside the sentence, between its own clauses ('inside'), which is not a link to the previous sentence."""
    low = " " + re.sub(r"\s+", " ", (t or "").lower()) + " "
    head = " " + " ".join(low.split()[:6]) + " "
    best = None
    for typ, _, words in RELATIONS:
        for w in words:
            ww = w.strip()
            m = re.search(r"[\s,(]" + re.escape(ww) + r"(?=[\s,:;])", head)
            if not m or (best and m.start() >= best[2]):
                continue
            if typ == "purpose" and not re.match(r" to [a-z]+", head):   # "to" counts only as an opening infinitive
                continue
            if (typ in ("condition", "sequence", "cause", "example") or ww in FIRST_ONLY) and m.start() > 0:
                continue                                                     # conjunctions link back only as the first word
            best = (typ, ww, m.start())
    # inside: a clause connector after the start, other than the start signal itself
    after = low[low.find(best[1]) + len(best[1]):] if best else low
    inside = next(((typ, w.strip(" ,")) for typ, w in INSIDE if w in after and after.index(w) > 0), ("", ""))
    return dict(type=best[0] if best else "implicit", word=best[1] if best else "", inside=inside[0], inside_word=inside[1])


def opening(toks):
    if not toks:
        return "subject"
    w = toks[0][2].lower()
    if w in ORD:
        return "ordinal"
    if w in CONN:
        return "connective"
    if w in SUBORD:
        return "clause"
    if w in PREP:
        return "phrase"
    return "subject"


def analyse(sents):
    """sents: [(id, english, subject-predicate-object spans)] of one paragraph, in order. Returns {id: marks} and a paragraph summary."""
    out, prev = {}, None
    for sid, en, spo in sents:
        toks = tokens(en)
        n = max(1, len(toks))
        subj = [s for s in (spo or []) if s[2] == "S"]
        s_end = subj[0][1] if subj else (toks[min(3, len(toks) - 1)][1] if toks else 0)
        s_beg = subj[0][0] if subj else 0
        subj_toks = [x for x in toks if x[0] >= s_beg and x[1] <= s_end]
        m = dict(words=len(toks), open=opening(toks), rel=relation(en), old=[], new="", pos="opens", chain="opens", old_at=None)
        if prev is not None:
            ptoks, pspo = prev
            given = content(ptoks)
            p_pred = [s for s in (pspo or []) if s[2] in "PO"]
            p_rheme_start = p_pred[0][0] if p_pred else (ptoks[len(ptoks) // 2][0] if ptoks else 0)
            rheme = content([x for x in ptoks if x[0] >= p_rheme_start])
            theme_prev = content([x for x in ptoks if x[0] < p_rheme_start])
            old_idx = [i for i, (_, _, w) in enumerate(toks) if (w.lower() not in STOP and len(w) > 2 and stem(w) in given) or (w.lower() in POINT and i < n * 0.4)]
            m["old"] = sorted({toks[i][2] for i in old_idx}, key=lambda w: en.find(w))[:6]
            if old_idx:
                m["old_at"] = round(old_idx[0] / n, 2)
                m["pos"] = "old first" if old_idx[0] <= n * 0.4 else "old late"
            else:
                m["pos"] = "no old words"
            tail = [w for _, _, w in toks[int(n * 0.6):] if w.lower() not in STOP and len(w) > 2 and stem(w) not in given]
            m["new"] = " ".join(tail[-4:])
            sc = content(subj_toks) if subj_toks else content(toks[:4])
            sw = {w.lower() for _, _, w in (subj_toks or toks[:3])}
            if sc & rheme or sw & {"this", "these", "such", "that", "those"}:
                m["chain"] = "linear"
            elif sc & theme_prev or sc & given or sw & {"it", "they", "its", "their"}:
                m["chain"] = "constant"
            else:
                m["chain"] = "new"
        out[sid] = m
        prev = (toks, spo)
    seq = [out[s[0]] for s in sents]
    runs = []
    for i in range(len(seq) - 2):   # flat rhythm: same opening and lengths within 3 words, three in a row
        a, b, c = seq[i:i + 3]
        if a["open"] == b["open"] == c["open"] and max(x["words"] for x in (a, b, c)) - min(x["words"] for x in (a, b, c)) <= 3:
            runs.append(sents[i][0])
    jumps = sum(1 for x in seq[1:] if x["chain"] == "new")
    summary = dict(first=[" ".join(w for _, _, w in tokens(s[1])[:3]) for s in sents], lengths=[x["words"] for x in seq],
                   old_first=sum(1 for x in seq[1:] if x["pos"] == "old first"), linked=max(0, len(seq) - 1), jumps=jumps,
                   implicit=sum(1 for x in seq[1:] if x["rel"]["type"] == "implicit"), flat=runs)
    return out, summary
