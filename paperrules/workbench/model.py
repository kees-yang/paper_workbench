"""Collect the data object of the workbench page (the contract is documented in docs/workbench.md).

Sources: the reader (sentences, sections, floats, citations), the rule report (compliance), the glossary (terms), the
annotation file (Chinese rendering, links, claims, storyline), and optionally the PDF (pages and paragraph rectangles).
Whatever a source does not give is left empty, and the panel that needs it says so.
"""
import hashlib
import json
import re

from . import annot, canvas, flow

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
SKIP_CHAPTER = re.compile(r'acknowledg|reference|appendix|supplement|bibliograph', re.I)
CONCL_CHAPTER = re.compile(r'conclusion|summary|discussion and', re.I)
STATUS = {'pass': 'pass', 'warn': 'warn', 'fail': 'fail', 'manual': 'manual', 'skip': 'manual'}
HOW = {'auto': '自动检查', 'partial': '半自动：检查器标出，作者判断', 'manual': '人工核查'}


def sha(o):
    return hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def short(t, n=60):
    t = re.sub(r'\s+', ' ', t).strip()
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + '…'


def plain_title(t):
    return re.sub(r'\\[a-zA-Z]+|[{}$~]', '', t).strip()


def spo_en(sentences):
    """Subject, predicate and object spans of every finite clause of an English sentence: [[start, end, 'S'|'P'|'O'], …]."""
    from ..rules_sentence import doc
    out = {}
    for rid, en in sentences.items():
        d, spans, taken = doc(en), [], []

        def add(a, b, role):
            if b > a and not any(a < y and x < b for x, y, _ in taken):
                spans.append([a, b, role])
                taken.append((a, b, role))

        for t in d:
            if t.pos_ not in ('VERB', 'AUX') or not any(c.dep_ in ('nsubj', 'nsubjpass', 'expl') for c in t.children):
                continue
            subj = next(c for c in t.children if c.dep_ in ('nsubj', 'nsubjpass', 'expl'))
            lo, hi = subj.left_edge.i, subj.right_edge.i
            inner = [x.i for x in d[lo:hi + 1] if x.dep_ in ('relcl', 'acl', 'advcl', 'ccomp')]
            if inner:
                hi = min(inner) - 1
                while hi > lo and d[hi].pos_ in ('PUNCT', 'CCONJ', 'ADP', 'PRON') and d[hi].dep_ != 'nsubj':
                    hi -= 1
            if hi >= lo:
                add(d[lo].idx, d[hi].idx + len(d[hi]), 'S')
            pred = [x for x in [*t.lefts, t, *t.rights] if x is t or (x.dep_ in ('aux', 'auxpass', 'neg', 'prt') and x.head is t)]
            for x in pred:
                add(x.idx, x.idx + len(x), 'P')
            obj = next((c for c in t.children if c.dep_ in ('dobj', 'attr', 'oprd', 'acomp', 'dative')), None)
            if obj is not None:
                lo, hi = obj.left_edge.i, obj.right_edge.i
                inner = [x.i for x in d[lo:hi + 1] if x.dep_ in ('relcl', 'acl', 'advcl', 'ccomp', 'prep') and x.i > obj.i]
                if inner:
                    hi = min(inner) - 1
                add(d[lo].idx, d[hi].idx + len(d[hi]), 'O')
        out[rid] = sorted(spans)
    return out


def row_hash(r):
    return sha([r['en_source'], r['zh'], r['cn_analysis']['previous'], r['cn_analysis']['earlier']])[:16]


def baseline_diff(baseline, rows, paragraphs):
    """Units whose text or analysis changed since the accepted baseline: (changed row ids, queue items)."""
    if not baseline:
        return set(), []
    old = baseline.get('rows', {})
    changed = {r['id'] for r in rows if r['id'] in old and old[r['id']] != row_hash(r)}
    added = {r['id'] for r in rows if r['id'] not in old}
    removed = sorted(set(old) - {r['id'] for r in rows})
    items = [dict(unit='sentence:' + i, kind='sentence', reason='句子或其分析在上次确认之后已变' if i in changed else '上次确认之后新增的句子',
                  action='复核本句：中文、与前句的关系、数字来源', status='pending') for i in sorted(changed | added)]
    for p in paragraphs:
        n = [r for r in p['rows'] if r in changed | added]
        if n:
            items.append(dict(unit='paragraph:' + p['id'], kind='paragraph', reason=f'本段有{len(n)}句已变或新增', action='复核本段的判断、步骤与服务的主张', status='pending'))
    items += [dict(unit='node:' + i, kind='node', reason='上次确认的句子已不在正文中', action='确认删除是有意的', status='pending') for i in removed]
    return changed | added, items


def collect(project, paper, report, ann, pdf=None, baseline=None):
    ids = annot.row_ids(paper)
    rev = {v: k for k, v in ids.items()}
    wb = {ids[r['id']]: r for r in paper.rows}
    zhc = lambda c: (ann.get('chapters') or {}).get(c) or c
    zhs = lambda c: (ann.get('sections') or {}).get(c) or c
    A = ann.get('rows') or {}
    AP = ann.get('paragraphs') or {}

    # ---- paragraphs in reading order (abstract, then by position; captions sit where their float is)
    groups = {}
    for r in paper.rows:
        groups.setdefault(r['para'], []).append(r)
    order = sorted(groups, key=lambda p: (groups[p][0]['kind'] != 'abstract', groups[p][0]['offset'], p))
    floats_at = {(f['file'], f['line']): f for f in paper.floats}
    flabel = lambda f: ('图' if f['env'] == 'figure' else '表') + str(f['number'])
    body_order = [p for p in order if groups[p][0]['kind'] not in ('figure', 'table', 'abstract')]
    starts = [groups[p][0]['offset'] for p in body_order]
    refs_by_para = {p: [] for p in body_order}
    for rf in paper.refs:
        j = max((i for i, s in enumerate(starts) if s <= rf['offset']), default=None)
        if j is not None and rf['label'] in {f['label'] for f in paper.floats}:
            refs_by_para[body_order[j]].append(rf['label'])
    first_cite = {}
    for p in body_order:
        for lab in refs_by_para[p]:
            first_cite.setdefault(lab, p)
    fl_by_label = {f['label']: f for f in paper.floats if f['label']}

    paragraphs, rows = [], []
    prev_in_chapter = {}
    abstract_id = next((p for p in order if groups[p][0]['kind'] == 'abstract'), order[0])
    for p in order:
        rs = groups[p]
        kind = rs[0]['kind']
        ap = AP.get(p, {})
        fl = floats_at.get((rs[0]['file'], rs[0]['line'])) if kind in ('figure', 'table') else None
        chapter = zhc(rs[0]['chapter']) if kind != 'abstract' else '摘要'
        if kind in ('figure', 'table'):                      # a caption belongs to the chapter its float sits in
            hs = [h for h in paper.headings if h['offset'] <= rs[0]['offset'] and h['level'] == 0]
            chapter = zhc(plain_title(hs[-1]['title'])) if hs else chapter
        title = ap.get('title') or (f"{'图' if kind == 'figure' else '表'}{fl['number']}：{short(rs[0]['en'], 28)}" if fl else '摘要' if kind == 'abstract' else short(rs[0]['en'], 34))
        claim = ap.get('claim') or short(rs[0]['en'], 140)
        prev = prev_in_chapter.get(chapter) if kind not in ('figure', 'table', 'abstract') else None
        paragraphs.append(dict(
            id=p, chapter=chapter, section=zhs(rs[0]['section']), kind='abstract' if kind == 'abstract' else kind if kind in ('figure', 'table') else 'paragraph',
            title=title, question=ap.get('question', ''), claim=claim, flow=ap.get('flow', ''), scope=ap.get('scope', ''),
            rows=[ids[r['id']] for r in rs], areas=(pdf or {}).get('areas', {}).get(p, []),
            previous_paragraph=prev['id'] if prev else None,
            previous_claim=prev['claim'] if prev else '独立引入，或图表说明。'))
        if kind not in ('figure', 'table', 'abstract'):
            prev_in_chapter[chapter] = paragraphs[-1]
        for r in rs:
            wid = ids[r['id']]
            a = A.get(wid, {})
            cn = dict(previous=dict(a.get('previous') or {}), earlier=dict(a.get('earlier') or {}), parse='', closure='')
            for k in ('previous', 'earlier'):
                cn[k].setdefault('anchor_id', None)
                for f in ('anchor_quote', 'anchor_head', 'target_quote', 'target_head', 'relation', 'phrase_type'):
                    cn[k].setdefault(f, '')
                if not cn[k]['anchor_id']:
                    cn[k]['anchor_id'] = None
            rows.append(dict(id=wid, paragraph_id=p, chapter=chapter, section=zhs(r['section']), kind=paragraphs[-1]['kind'],
                             zh=a.get('zh') or r['en'], en_source=r['en'], en_shared_with=[], cn_analysis=cn, terms=[]))
    pm = {p['id']: p for p in paragraphs}
    rm = {r['id']: r for r in rows}

    # ---- glossary → terms with the rows that use them
    terms = []
    for t in project.glossary:
        forms = [t['en']] + t.get('aliases_en', []) + t.get('allowed', [])
        pats = [re.compile(r'(?<![A-Za-z])' + re.escape(f) + r's?(?![A-Za-z])', re.I) for f in forms if len(f) > 1]
        terms.append(dict(id=t.get('id', t['en']), zh=t.get('zh') or t['en'], en=t['en'], category=t.get('category', ''), aliases_zh=[t.get('zh') or t['en']],
                          aliases_en=[t['en']] + t.get('aliases_en', []), allowed=t.get('allowed', []), symbol=t.get('symbol', ''), note=t.get('note', ''),
                          row_ids=[r['id'] for r in rows if any(p.search(r['en_source']) for p in pats)]))
    for r in rows:
        r['terms'] = [dict(id=t['id'], zh=t['zh'], en=t['en'], allowed=t['allowed'], note=t['note'], symbol=t['symbol']) for t in terms if r['id'] in t['row_ids']]

    # ---- argument structure: abstract slots, introduction, body sections, conclusion claims
    chapters = [h for h in paper.headings if h['level'] == 0]
    for h in chapters:
        h['title'] = plain_title(h['title'])
    real = [h for h in chapters if not SKIP_CHAPTER.search(h['title'])]
    concl = next((h for h in reversed(real) if CONCL_CHAPTER.search(h['title'])), real[-1] if real else None)
    intro = real[0] if real else None
    mid = [h for h in real if h is not intro and h is not concl]
    sec_h = [h for h in paper.headings if h['level'] == 1]
    for h in sec_h:
        h['title'] = plain_title(h['title'])

    def chapter_of(off):
        c = [h for h in chapters if h['offset'] <= off]
        return c[-1] if c else None

    def para_off(p):
        return groups[p][0]['offset']

    A_ = dict(abstract_id=abstract_id, intro=[], groups=[], paras={}, claims=[], slots=[], columns=[])
    slots = (ann.get('abstract') or {}).get('slots') or [dict(id='S1', name='Abstract', name_zh='摘要', claim_zh='', scope='', sentences=pm[abstract_id]['rows'])]
    A_['slots'] = [dict(s, claim_zh=s.get('claim_zh', ''), sentences=[x for x in s.get('sentences', []) if x in rm]) for s in slots]
    roman = {h['title']: ROMAN[i] for i, h in enumerate(real)}
    nodes_ws = [dict(id='ABS', kind='root', title='Abstract (argument core)', parent=None, children=[roman[intro['title']]] if intro else [],
                     claim=' '.join(s['claim_zh'] for s in A_['slots'] if s['claim_zh']), serves=[], template='abstract', stale=False)]
    wsp = {}
    for p in order:
        kind = groups[p][0]['kind']
        ap = AP.get(p, {})
        serves = list(ap.get('serves', []))
        A_['paras'][p] = dict(chapter=pm[p]['chapter'], title=pm[p]['title'], claim=pm[p]['claim'], move=ap.get('move', 'caption' if kind in ('figure', 'table') else ''),
                              serves=serves, floats=[], sentences=pm[p]['rows'])
    # introduction paragraphs and body groups
    for p in order:
        r0 = groups[p][0]
        if r0['kind'] == 'abstract':
            continue
        off = r0['offset']
        ch = chapter_of(off)
        if ch is None:
            continue
        if intro and ch is intro and r0['kind'] not in ('figure', 'table'):
            A_['intro'].append(p)
    for i, ch in enumerate(mid):
        nxt = [h for h in chapters if h['offset'] > ch['offset']]
        end = nxt[0]['offset'] if nxt else 10 ** 9
        subs = [h for h in sec_h if ch['offset'] < h['offset'] < end]
        bounds = [(ch['offset'], subs[0]['offset'] if subs else end, None)] + \
                 [(h['offset'], subs[k + 1]['offset'] if k + 1 < len(subs) else end, h) for k, h in enumerate(subs)]
        n_sub = 0
        for lo, hi, h in bounds:
            n_sub += 1 if h else 0
            ps = [p for p in order if groups[p][0]['kind'] != 'abstract' and lo <= para_off(p) < hi]
            if not ps:
                continue
            chnum = ch.get('number') or str(i + 2)
            gid = roman[ch['title']] + (f'-{chr(64 + n_sub)}' if h else '')
            numtxt = chnum + (f'.{n_sub}' if h else '')
            A_['groups'].append(dict(id=gid, title=zhs(h['title']) if h else zhc(ch['title']), label=f"{zhc(ch['title'])} · {numtxt}",
                                     paragraphs=ps, col=2 if i < (len(mid) + 1) // 2 else 3, chapter=ch['title']))
    for lab, p in first_cite.items():
        f = fl_by_label[lab]
        A_['paras'][p]['floats'].append(flabel(f))
    A_['intro_label'] = zhc(intro['title']) if intro else '引言'
    A_['columns'] = [('摘要', '论证槽'), (A_['intro_label'], '逐段'), ('、'.join(zhc(h['title']) for h in mid[:(len(mid) + 1) // 2]) or '正文', '按小节'),
                     ('、'.join(zhc(h['title']) for h in mid[(len(mid) + 1) // 2:]) or '正文', '按小节'), ('结论', '回扣摘要')]
    conc_ps = [p for p in order if concl and chapter_of(groups[p][0]['offset']) is concl and groups[p][0]['kind'] not in ('figure', 'table', 'abstract')]
    conclusion_id = conc_ps[0] if conc_ps else order[-1]
    A_['conclusion_id'] = conclusion_id
    claims = ann.get('claims') or []
    A_['claims'] = [dict(id=c['id'], zh=c['zh'], short=c.get('short') or c['id'], sentences=[x for x in c.get('sentences', []) if x in rm],
                         mirrors=c.get('mirrors', []), supported_by=c.get('supported_by', [])) for c in claims]
    cv = canvas.build(A_)

    # ---- the writing-system views (argument tree, evidence, floats, queue)
    nodes_ws += [dict(id=roman[h['title']], kind='chapter', title=zhc(h['title']), parent='ABS' if h is intro else (roman[intro['title']] if intro else 'ABS'),
                      children=[], claim='', serves=[], template='', stale=False) for h in real]
    nid = {n['id']: n for n in nodes_ws}
    for g in A_['groups']:
        chap = roman[g['chapter']]
        if g['id'] != chap:
            nodes_ws.append(dict(id=g['id'], kind='section', title=g['title'], parent=chap, children=[], claim='', serves=[], template='', stale=False))
            nid[g['id']] = nodes_ws[-1]
    for n in nodes_ws:
        if n['parent'] and n['parent'] in nid:
            nid[n['parent']]['children'].append(n['id'])
    parent_of, titles = {}, {n['id']: n['title'] for n in nodes_ws}
    for g in A_['groups']:
        for p in g['paragraphs']:
            parent_of[p] = g['id']
    for p in A_['intro']:
        parent_of[p] = roman[intro['title']]
    for p in order:
        par = 'ABS' if p == abstract_id else parent_of.get(p) or (roman.get(chapter_of(groups[p][0]['offset'])['title'], 'ABS') if chapter_of(groups[p][0]['offset']) else 'ABS')
        chain, x = [], par
        while x:
            chain.append(dict(id=x, title=titles.get(x, '')))
            x = nid[x]['parent'] if x in nid else None
        wsp[p] = dict(parent=par, chain=chain, move=A_['paras'][p]['move'] or 'paragraph', serves=A_['paras'][p]['serves'], evidence=[],
                      floats=[f['label'] for f in paper.floats if f['label'] and first_cite.get(f['label']) == p],
                      citations=[], budget=dict(sentences=len(groups[p]), words=sum(len(r['en'].split()) for r in groups[p])), stale=False)
    claim_text = {s['id']: s['claim_zh'] for s in A_['slots']}
    for s_ in A_['slots']:
        for pt in s_.get('points', []):
            claim_text[pt['id']] = pt['zh']
    claim_text.update({c['id']: c['zh'] for c in A_['claims']})
    trace = []
    body_key = {h['title']: ROMAN[i + 1] for i, h in enumerate(mid)}
    for s in A_['slots']:
        intro_ps = [p for p in A_['intro'] if any(x == s['id'] or x.startswith(s['id'] + '.') for x in A_['paras'][p]['serves'])]
        body = {k: [] for k in ('II', 'III', 'IV', 'V')}
        for g in A_['groups']:
            for p in g['paragraphs']:
                if any(x == s['id'] or x.startswith(s['id'] + '.') for x in A_['paras'][p]['serves']):
                    body.setdefault(roman[g['chapter']], []).append(p)
        trace.append(dict(slot=s['id'], name=s['name_zh'], claim=s['claim_zh'], sentences=s['sentences'], intro=intro_ps, body=body,
                          conclusion=[c['id'] for c in A_['claims'] if s['id'] in c['mirrors']]))
    cites = {}
    for k in paper.cites:
        cites[k] = dict(number=paper.cites.index(k) + 1, title=k)
    tables, figures = {}, {}
    for f in paper.floats:
        lab = f['label'] or f"{f['env']}{f['number']}"
        rec = dict(kind='论文表格' if f['env'] == 'table' else '论文图', number=('Table ' if f['env'] == 'table' else 'Fig. ') + str(f['number']), width='columnwidth', env=f['env'],
                   caption=f.get('caption_plain') or '', records=[], first_cited_in=first_cite.get(f['label']) or '', preview='')
        if f['env'] == 'table':
            t = parse_table(f, {k: i + 1 for i, k in enumerate(paper.cites)}, paper.labels, paper.bold_macros)
            if t:
                rec.update(t)
        else:
            g = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', f['tex'])
            rec['asset'] = g.group(1) if g else ''
        (tables if f['env'] == 'table' else figures)[lab] = rec
    changed_rows, queue = baseline_diff(baseline, rows, paragraphs)
    for p_ in paragraphs:
        if any(r in changed_rows for r in p_['rows']) and p_['id'] in cv['info']:
            cv['info'][p_['id']]['changed'] = True
    cv['changed_rows'] = sorted(changed_rows)
    ev = ann.get('evidence') or {}
    records, ev_sent = {}, {}
    for rid, x in (ev.get('records') or {}).items():
        records[rid] = dict(type=x.get('type', 'table'), printed=str(x['printed']), value=x.get('value'), unit=x.get('unit', ''), file=x.get('file'), row=x.get('row') or {},
                            column=x.get('column'), formula=x.get('formula'), inputs=x.get('inputs', []), note=x.get('note'), protocol=x.get('protocol'),
                            sentences=[], floats=x.get('floats', []), label=x.get('label', rid))
    for sid, x in (ev.get('sentences') or {}).items():
        if sid not in rm:
            continue
        ev_sent[sid] = dict(sid=sid, evidence=[dict(literal=e['literal'], record=e['record']) for e in x.get('evidence', []) if e['record'] in records],
                            unresolved=x.get('unresolved', []), citations=[], connector=dict(lead=None, inner=[]), stale=False)
        for e in ev_sent[sid]['evidence']:
            if sid not in records[e['record']]['sentences']:
                records[e['record']]['sentences'].append(sid)
    for sid, x in ev_sent.items():
        pid = rm[sid]['paragraph_id']
        for e in x['evidence']:
            if e['record'] not in wsp[pid]['evidence']:
                wsp[pid]['evidence'].append(e['record'])
    n_unres = sum(len(x['unresolved']) for x in ev_sent.values())
    for pid, w in wsp.items():
        info = cv['info'].get(pid)
        if info is not None:
            info['nums'] = [dict(k=r, label=records[r]['label'], value=records[r]['printed'], unit=records[r]['unit'] if records[r]['unit'] not in ('', None) else '',
                                 formula=records[r]['formula'], file=(records[r]['file'] or '').split('/')[-1], protocol=records[r]['protocol'], floats=[])
                            for r in w['evidence']]
    ws = dict(schema='paperrules-workbench-ws/1', built=report['checked_at'], paper_version=ann.get('version', ''), status='demo',
              slots=[dict(id=s['id'], name=s.get('name', s['name_zh']), name_zh=s['name_zh'], rows=s['sentences'], scope=s.get('scope', ''), budget_sentences=len(s['sentences']),
                          needs='', claim_en=s.get('claim_en', ''), claim_zh=s['claim_zh'], evidence=[], terms=[], sentences=s['sentences'], status='imported', points=s.get('points', []))
                    for s in A_['slots']],
              conclusion=[dict(id=c['id'], zh=c['zh'], rows=c['sentences'], mirrors=c['mirrors'], supported_by=c['supported_by'], claim_en='', evidence=[], sentences=c['sentences'])
                          for c in A_['claims']],
              claims=claim_text, departures=[], nodes=nodes_ws, paragraphs=wsp, sentences=ev_sent,
              records=records, citations=cites, floats=dict(tables=tables, figures=figures),
              checks=[dict(id='evidence.unsourced_numbers', title='未登记的数字', status='warn' if n_unres else 'pass' if records else 'manual',
                           summary=(f'{n_unres}个数字没有记录' if n_unres else '无') if records else '项目没有证据登记', items=[])],
              queue=queue, proposals=[], simulation=None, trace=trace,
              last_refresh=dict(accepted=(baseline or {}).get('accepted_at', ''), label=(baseline or {}).get('label', ''), from_baseline=(baseline or {}).get('label', ''), items=queue),
              trace_labels={ROMAN[i + 1]: zhc(h['title']) for i, h in enumerate(mid)})

    # ---- storyline
    para_of = {r['id']: r['paragraph_id'] for r in rows}
    fl = flow.build(ann.get('storyline') or [], rm, para_of) if ann.get('storyline') else None

    # ---- rule compliance (from the rule report)
    comp = compliance(report, ann, pdf)
    D = dict(schema='paperrules-workbench/1', title=ann.get('title') or project.settings.get('title') or project.main_tex.stem, subtitle=ann.get('version', ''),
             journal=ann.get('journal', ''), pdf_version=ann.get('version', ''), pdf_sha256=(pdf or {}).get('sha256', ''), pdf_sha=(pdf or {}).get('sha256', '')[:12],
             ids=dict(abstract=abstract_id, conclusion=conclusion_id, slots=[s['id'] for s in A_['slots']], slot2line={}, trace_labels=ws['trace_labels']),
             chapters=list(dict.fromkeys(p['chapter'] for p in paragraphs)), paragraphs=paragraphs, rows=rows, removed_rows=[], removed_paragraphs=[],
             removed_units=[], prior_versions=[], terms=terms, chapter_for={p['id']: p['chapter'] for p in paragraphs},
             source_units=[dict(id=p['id'], kind=p['kind'], en=' '.join(rm[r]['en_source'] for r in p['rows']), areas=p['areas']) for p in paragraphs],
             page_dimensions=(pdf or {}).get('dims', []), ws=ws, canvas=cv, step_map=canvas.step_maps(dict(rows=rows, paragraphs=paragraphs)),
             compliance=comp, compliance_history=[], spo={rid: dict(en=sp, zh=[]) for rid, sp in spo_en({r['id']: r['en_source'] for r in rows}).items()})
    if fl:
        D['flow'] = fl
        D['ids']['slot2line'] = {s['id']: L['id'] for L in fl['lines'] for s in A_['slots'] if any(s['id'] == str(u.get('key', '')).split('.')[0] for u in L['units'])}
        for c in A_['claims']:
            first = next((D['ids']['slot2line'][m] for m in c['mirrors'] if m in D['ids']['slot2line']), None)
            if first:
                D['ids']['slot2line'][c['id']] = first
    D['source_hash'] = sha([r['zh'] for r in rows] + [r['en_source'] for r in rows])[:16]
    return D


def compliance(report, ann, pdf):
    """The rule report in the shape of the page's 规则核查 view."""
    by_id = {r['id']: r for r in report['rules']}
    groups, manual = [], []
    for st in report['stages']:
        nodes, flat = [], []
        for n in st['nodes']:
            rules = []
            for rid in n['rules']:
                r = by_id[rid]
                if r['status'] == 'off':
                    continue
                fs = [f for f in report['findings'] if f['rule'] == rid]
                open_ = [f for f in fs if f['status'] != 'accepted']
                summ = r['note'] or ('通过' if r['status'] == 'pass' else f'{len(open_)}项待处理' + (f'，{r["accepted"]}项已写明理由接受' if r['accepted'] else ''))
                if r['status'] == 'manual':
                    manual.append(dict(title=r['statement']['zh'], source=r['why']['zh'], last='见检查清单', stage=st['id']))
                    summ = '人工核查'
                row = dict(id=rid, title=r['statement']['zh'], source=r['why']['zh'], how=HOW[r['method']], status=STATUS[r['status']], summary=summ,
                           items=[dict(sentence=f['id'], file=f"{f['file']}:{f['line']}" if f['file'] else '', matched=f['matched'],
                                       status='已接受：' + f['reason'] if f['status'] == 'accepted' else '') for f in fs[:40]])
                rules.append(row)
                flat.append(row)
            nodes.append(dict(name=n['name']['zh'], rules=rules))
        groups.append(dict(stage=st['id'], number=st['number'], name=f"{st['number']}. {st['name']['zh']}", role=st['role']['zh'], when=st['when']['zh'],
                           status=STATUS.get(st['status'], 'pass'), gate=st['gate'], blocked_by=st['blocked_by'], rechecked_for=[], nodes=nodes, rules=flat))
    s = report['summary']
    return dict(schema='paperrules-compliance/1', checked_at=report['checked_at'], paper_version=ann.get('version', ''), journal=ann.get('journal', ''),
                inputs=dict(pdf=report['project']['main_tex'], pdf_sha256=(pdf or {}).get('sha256', ''), tex_sha256='', workbench_sha256='', checks_built=report['checked_at']),
                summary=dict(**{'pass': s['pass'], 'warn': s['warn'], 'fail': s['fail'], 'manual': s['manual']}), groups=groups,
                tree=dict(principles=[x['zh'] for x in report.get('principles', [])] or ['自上而下检查：源头 → 主线 → 段落 → 句子 → 格式 → 规则系统。', '在最高的未通过层修改。'],
                          first_failing=report['first_failing']['zh'] if report['first_failing'] else None, changes=[]), manual=manual)


# ---------------------------------------------------------------------------------------------------- tables
RULE_CMD = re.compile(r'\\(?:hline|midrule|toprule|bottomrule|hdashline|cline\{[^}]*\}|cmidrule(?:\([^)]*\))?\{[^}]*\}|specialrule\{[^}]*\}\{[^}]*\}\{[^}]*\})')
LEAD_RULE = re.compile(r'^\s*(?:' + RULE_CMD.pattern + r'\s*)+')


def _cell(raw, cite_no, labels, bold):
    """(text, colspan, mark) of one tabular cell."""
    span, t = 1, raw
    m = re.search(r'\\multicolumn\{(\d+)\}\{[^}]*\}\{', t)
    if m:
        from ..texread import braced
        span = int(m.group(1))
        t = braced(t, m.end() - 1)[0]
    m = re.search(r'\\multirow\{\d+\}\{[^}]*\}\{', t)
    if m:
        from ..texread import braced
        t = braced(t, m.end() - 1)[0]
    t = re.sub(r'\\(?:cellcolor|rowcolor|columncolor)(?:\[[^\]]*\])?\{[^}]*\}', '', t)
    t = re.sub(r'\$\\times\$', '×', t)
    t = re.sub(r'\$\\sim\$', '～', t)
    is_bold = '\\textbf' in t or any(re.search(r'\\' + m + r'\b', t) for m in bold)
    mark = 'best' if is_bold else 'second' if '\\underline' in t else ''
    from ..texread import plain
    return plain(t, cite_no, labels), span, mark


def parse_table(f, cite_no, labels, bold):
    """The first tabular of a float as header, rows and rules; None when it cannot be read."""
    m = re.search(r'\\begin\{tabular\*?\}(?:\{[^}]*\})?\{[^}]*\}(.*?)\\end\{tabular\*?\}', f['tex'], re.S)
    if not m:
        return None
    raw = [r for r in re.split(r'\\\\(?:\[[^\]]*\])?', m.group(1))]
    rows, rule_before = [], []
    for r in raw:
        lead = LEAD_RULE.match(r)
        rule_before.append(bool(lead))
        r = RULE_CMD.sub('', r).strip()
        if not r:
            rows.append(None)
            continue
        cells = [_cell(c, cite_no, labels, bold) for c in re.split(r'(?<!\\)&', r)]
        rows.append(cells)
    keep = [i for i, r in enumerate(rows) if r]
    if len(keep) < 2:
        return None
    grid = [rows[i] for i in keep]
    rule_after = []
    for k, i in enumerate(keep):
        nxt = keep[k + 1] if k + 1 < len(keep) else len(rows)
        rule_after.append(any(rule_before[j] for j in range(i + 1, min(nxt + 1, len(rule_before)))))
    h = next((k for k, x in enumerate(rule_after) if x), 0)
    while h + 1 < len(grid) - 1 and not any(re.search(r'\d', c[0]) for c in grid[h + 1]):
        h += 1                                  # a second header row (units, variants) has no number in it
    ncols = max(sum(c[1] for c in r) for r in grid)

    def expand(r):
        out = []
        for text, span, mark in r:
            out += [(text, mark)] * span
        return out + [('', '')] * (ncols - len(out))

    heads = [expand(r) for r in grid[:h + 1]]
    head = []
    for c in range(ncols):
        parts = []
        for r in heads:
            if r[c][0] and r[c][0] not in parts:
                parts.append(r[c][0])
        head.append(' · '.join(parts))
    body, ra = [], []
    for k, r in enumerate(grid[h + 1:], h + 1):
        cells = expand(r)
        body.append(dict(label=cells[0][0], ours=any(x[0].lower() == 'ours' for x in cells), cells=[dict(text=t, mark=mk) for t, mk in cells[1:]]))
        ra.append(rule_after[k])
    return dict(row_head=head[0] or '', head=head[1:], sections=[dict(title='', rows=body, rule_after=ra)])
