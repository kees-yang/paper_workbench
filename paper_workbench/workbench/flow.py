"""The storyline view (语义流): one claim followed through the levels of the paper, with four checks per node.

The annotation file lists, for each storyline (background, gap, method, results …), its points; each point lists the nodes it
passes (abstract, introduction, body, conclusion) with the sentences that carry it. This module adds the checks:

    expand         a node that expands (role expand) adds at least three words the previous node does not have
    nonredundant   the carrying sentence is not a copy of the previous node's (similarity below copy_minor)
    consistent     the core concepts of the point come back in every expanding node
    echo           an echo node (the conclusion) repeats at least one core concept and adds no new claim

They are heuristics on word overlap, a reading aid for the author: a flag is a question about a node, not a verdict.
"""
import difflib
import re

THRESHOLDS = dict(copy_major=0.9, copy_minor=0.75, echo_copy=0.95, new_words=3)
RULE = dict(expand='F1', nonredundant='F2', consistent='F4', echo='F6')


def _words(t):
    return set(w for w in re.findall(r'[a-z]{4,}', t.lower()))


def build(story, rows, para_of):
    """story: annotation ``storyline`` list; rows: {id: row dict with zh, en_source}; para_of: {row id: paragraph id}."""
    T = THRESHOLDS
    lines, issues = [], []
    for L in story:
        units = []
        for pt in L.get('points', []):
            core = [c['zh'] for c in pt.get('concepts', []) if c.get('core')]
            chain, prev = [], None
            for n in pt.get('nodes', []):
                ids = [r for r in n.get('rows', []) if r in rows]
                carrier = ids[0] if ids else None
                node = dict(level=n['level'], role=n['role'], carrier=carrier, first=carrier, text_rows=ids,
                            paragraphs=list(dict.fromkeys(para_of[r] for r in ids)), checks={}, excluded=False)
                if carrier:
                    en = ' '.join(rows[r]['en_source'] for r in ids)
                    zh = ''.join(rows[r]['zh'] for r in ids)
                    ck = node['checks']
                    if prev is not None:
                        ratio = difflib.SequenceMatcher(None, en.lower(), prev[0].lower()).ratio()
                        lim = T['echo_copy'] if n['role'] == 'echo' else T['copy_minor']
                        sev = 'major' if ratio >= T['copy_major'] and n['role'] != 'echo' else 'minor' if ratio >= lim else 'pass'
                        ck['nonredundant'] = [sev, f'与上一节点承载句相似度{ratio:.2f}']
                        if n['role'] == 'expand':
                            new = len(_words(en) - _words(prev[0]))
                            ck['expand'] = ['pass' if new >= T['new_words'] else 'minor', f'新增{new}项细节' if new >= T['new_words'] else f'新增细节只有{new}项']
                    if core and n['role'] in ('expand', 'echo'):
                        miss = [c for c in core if c not in zh]
                        key = 'echo' if n['role'] == 'echo' else 'consistent'
                        if n['role'] == 'echo':
                            ck[key] = ['pass', '呼应核心概念'] if len(miss) < len(core) else ['minor', '呼应缺少：' + '、'.join(miss)]
                        else:
                            ck[key] = ['pass', '核心概念全部延续'] if not miss else ['minor', '缺少核心概念：' + '、'.join(miss)]
                    prev = (en, zh)
                    for k, v in ck.items():
                        if v[0] != 'pass':
                            issues.append(dict(severity=v[0], rule=RULE[k], line=L['id'], point=pt.get('key'), level=n['level'], rows=ids, msg=v[1]))
                chain.append(node)
            units.append(dict(key=pt.get('key'), zh=pt['zh'], concepts=pt.get('concepts', []), subject=[], chain=chain))
        lines.append(dict(id=L['id'], name=L['name'], story=L.get('story', ''), nodes=[dict(level=n['level'], role=n['role']) for n in (units[0]['chain'] if units else [])],
                          units=units))
    summary = {}
    for i in issues:
        summary.setdefault(i['rule'], {}).setdefault(i['severity'], 0)
        summary[i['rule']][i['severity']] += 1
    return dict(schema='paperrules-flow/1', anchor='storyline', order=[L['id'] for L in lines], thresholds=T, lines=lines, issues=issues,
                summary=summary, links_checked=sum(len(u['chain']) for L in lines for u in L['units']),
                counts=dict(major=sum(i['severity'] == 'major' for i in issues), minor=sum(i['severity'] == 'minor' for i in issues)),
                uncovered_paragraphs=[])
