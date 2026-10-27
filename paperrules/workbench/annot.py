"""The annotation file of the workbench (``workbench.json``) and its checks.

Everything the reader and the rule checker cannot know is written here, by the authors or by an assistant that works from
the paper: the Chinese rendering of each sentence, the link of a sentence to the text before it, what each paragraph claims,
how the abstract and the conclusion relate to the body, and the storyline. Every field is optional; a panel without its
annotation shows what it can (the English text, the rule findings) and says what is missing.

Ids: paragraphs are ``P001``…, rows (sentences) are ``<paragraph>-R001``…, as printed by ``paperrules workbench ids``.
"""
import json
import re
from pathlib import Path

SCHEMA = 'paperrules-workbench-annotations/1'
ROLES = ('context', 'gap', 'motivation', 'method', 'result', 'prior', 'setup', 'discuss', 'concl')
LINK_KEYS = ('anchor_id', 'anchor_quote', 'anchor_head', 'target_quote', 'target_head', 'relation', 'phrase_type')


def load(path):
    p = Path(path)
    if not p.exists():
        return dict(schema=SCHEMA)
    return json.loads(p.read_text(encoding='utf-8'))


def row_ids(paper):
    """Reader rows → workbench ids: (para id, index in its paragraph) → ``P013-R002``."""
    count, out = {}, {}
    for r in paper.rows:
        k = count[r['para']] = count.get(r['para'], 0) + 1
        out[r['id']] = f"{r['para']}-R{k:03d}"
    return out


def check(ann, paper):
    """Problems of an annotation file against the paper: unknown ids, quotes that are not in the sentence, empty slots."""
    ids = row_ids(paper)
    rows = {ids[r['id']]: r for r in paper.rows}
    paras = {r['para'] for r in paper.rows}
    out = []
    for rid, a in (ann.get('rows') or {}).items():
        if rid not in rows:
            out.append(f'rows: unknown sentence {rid}')
            continue
        zh = a.get('zh') or ''
        for kind in ('previous', 'earlier'):
            L = a.get(kind)
            if not L or not L.get('anchor_id'):
                continue
            if L['anchor_id'] not in rows:
                out.append(f'{rid}.{kind}: unknown anchor {L["anchor_id"]}')
                continue
            az = ((ann['rows'].get(L['anchor_id']) or {}).get('zh')) or ''
            if L.get('anchor_quote') and L['anchor_quote'] not in az:
                out.append(f'{rid}.{kind}: anchor_quote “{L["anchor_quote"]}” is not in the Chinese of {L["anchor_id"]}')
            if L.get('target_quote') and L['target_quote'] not in zh:
                out.append(f'{rid}.{kind}: target_quote “{L["target_quote"]}” is not in the Chinese of {rid}')
            for h, q in (('anchor_head', 'anchor_quote'), ('target_head', 'target_quote')):
                if L.get(h) and L.get(q) and L[h] not in L[q]:
                    out.append(f'{rid}.{kind}: {h} “{L[h]}” is not inside {q}')
    for pid in (ann.get('paragraphs') or {}):
        if pid not in paras:
            out.append(f'paragraphs: unknown paragraph {pid}')
    slots = (ann.get('abstract') or {}).get('slots', [])
    for s in slots:
        for r in s.get('sentences', []):
            if r not in rows:
                out.append(f'abstract slot {s["id"]}: unknown sentence {r}')
    for c in ann.get('claims', []):
        for r in c.get('sentences', []):
            if r not in rows:
                out.append(f'claim {c["id"]}: unknown sentence {r}')
        for p in c.get('supported_by', []):
            if p not in paras:
                out.append(f'claim {c["id"]}: unknown paragraph {p}')
    ev = ann.get('evidence') or {}
    for sid, x in (ev.get('sentences') or {}).items():
        if sid not in rows:
            out.append(f'evidence: unknown sentence {sid}')
            continue
        for e in x.get('evidence', []):
            if e['literal'] not in rows[sid]['en']:
                out.append(f'evidence {sid}: “{e["literal"]}” is not in the sentence')
            if e['record'] not in (ev.get('records') or {}):
                out.append(f'evidence {sid}: unknown record {e["record"]}')
    for L in ann.get('storyline', []):
        for u in L.get('points', []):
            for n in u.get('nodes', []):
                for r in n.get('rows', []):
                    if r not in rows:
                        out.append(f'storyline {L["id"]}/{u.get("key")}: unknown sentence {r}')
    return out


def listing(paper):
    """Text listing of the ids with the English sentence, for writing the annotations."""
    ids = row_ids(paper)
    lines, last = [], None
    for r in sorted(paper.rows, key=lambda r: (r['kind'] in ('figure', 'table'), r['id'])):
        if r['para'] != last:
            lines.append(f"\n{r['para']}  [{r['kind']}] {r['chapter']} · {r['section']}")
            last = r['para']
        lines.append(f"  {ids[r['id']]}  {r['en']}")
    return '\n'.join(lines).lstrip('\n')


def skeleton(paper):
    """An annotation file with every id and an empty field to fill in."""
    ids = row_ids(paper)
    paras = {}
    for r in paper.rows:
        paras.setdefault(r['para'], dict(title='', question='', claim='', flow='', scope='', move='', serves=[]))
    return dict(
        schema=SCHEMA, title='', version='', journal='', language='zh',
        chapters={c: '' for c in dict.fromkeys(r['chapter'] for r in paper.rows)},
        abstract=dict(slots=[dict(id=f'S{i}', name=n, name_zh='', claim_zh='', claim_en='', scope='', sentences=[])
                             for i, n in enumerate(['State of the art', 'Gap', 'Motivation', 'Method', 'Results'], 1)]),
        paragraphs=paras,
        rows={ids[r['id']]: dict(zh='', previous=dict.fromkeys(LINK_KEYS, ''), earlier=dict.fromkeys(LINK_KEYS, '')) for r in paper.rows},
        claims=[dict(id='C1', zh='', sentences=[], mirrors=[], supported_by=[])],
        storyline=[dict(id='MAIN', name='', story='', points=[dict(key='MAIN.a', zh='', concepts=[], nodes=[])])])
