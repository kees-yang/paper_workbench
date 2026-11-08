"""The argument canvas and the paragraph outline matching.

``build(A)`` turns the argument structure (abstract slots, introduction paragraphs, body sections, conclusion claims) into the
node-editor data the page draws: five columns, nodes with a role colour, and wires. Wires follow the claims: an abstract slot
expands into the introduction paragraphs that serve it, an introduction paragraph into the body paragraphs that serve the same
claim, and body paragraphs feed the conclusion claim they support. ``step_maps`` matches each paragraph's outline steps
(``flow`` split at →) to its sentences by shared wording; a reading aid, not a stored analysis.
"""
import re

MOVE = {  # move → (role colour, Chinese role name)
    'background': ('context', '背景'), 'state_of_the_art': ('context', '现状'), 'problem': ('gap', '问题'),
    'motivation': ('motivation', '动机'), 'approach': ('method', '方法思路'), 'overview': ('method', '总览'),
    'notation_inputs': ('method', '输入与记号'), 'module': ('method', '模块'), 'objective': ('method', '训练目标'),
    'analysis': ('method', '分析'), 'contributions': ('method', '贡献'), 'setup': ('setup', '实验设置'),
    'prior_work': ('prior', '已有工作'), 'contrast': ('prior', '区别'), 'main_results': ('result', '主要结果'),
    'qualitative': ('result', '视觉分析'), 'ablation': ('result', '消融'), 'efficiency': ('result', '效率'),
    'task_validation': ('result', '下游验证'), 'results': ('result', '结果'), 'scope': ('discuss', '范围'),
    'future_work': ('discuss', '后续工作'), 'caption': ('section', '图表'),
}
SLOT_ROLE = ['context', 'gap', 'motivation', 'method', 'result']


def role_of(move):
    m = move[0] if isinstance(move, list) and move else move
    return MOVE.get(m, ('method', m or '段落'))


def build(A):
    """A: dict(slots, intro, groups, paras, claims, columns). Returns the canvas dict used by the page."""
    info, nodes, edges = {}, [], []
    cols = [dict(title=t, sub=s) for t, s in A['columns']]
    for i, s in enumerate(A['slots']):
        info[s['id']] = dict(kind='slot', unit=A['abstract_id'], label='摘要 · ' + s['name_zh'], role=SLOT_ROLE[i % 5], role_zh=s['name_zh'],
                             title=s['name_zh'], claim=s['claim_zh'], scope=s.get('scope'), rows=s['sentences'], nums=[], floats=[],
                             changed=False, sim=False)
        nodes.append(dict(k=s['id'], col=0, kind='slot'))

    def para_info(pid, label):
        p = A['paras'][pid]
        role, role_zh = role_of(p['move'])
        return dict(kind='para', unit=pid, label=label, role=role, role_zh=role_zh, title=p['title'], claim=p['claim'], nums=[],
                    floats=p['floats'], changed=False, new=False, sim=False)

    for i, pid in enumerate(A['intro'], 1):
        info[pid] = para_info(pid, f"{A['intro_label']} · 第{i}段")
        nodes.append(dict(k=pid, col=1, kind='para'))
    for g in A['groups']:
        for j, pid in enumerate(g['paragraphs'], 1):
            info[pid] = para_info(pid, f"{g['label']} 第{j}段")
        info[g['id']] = dict(kind='group', unit=g['paragraphs'][0], label=g['label'], role='section', role_zh='小节', title=g['title'],
                             claim=g.get('claim', ''), nums=[], floats=[], changed=False, sim=False)
        nodes.append(dict(k=g['id'], col=g['col'], kind='group', rows=g['paragraphs']))
    for c in A['claims']:
        info[c['id']] = dict(kind='claim', unit=A['conclusion_id'], label='结论 · ' + c['short'], role='concl', role_zh=c['short'], title=c['zh'],
                             claim='', rows=c['sentences'], nums=[], floats=[], changed=False, sim=False,
                             support=[p for p in c.get('supported_by', []) if p in info])
        nodes.append(dict(k=c['id'], col=4, kind='claim'))

    mirror = {c['id']: c['mirrors'] for c in A['claims']}
    expand = lambda keys: set(keys).union(*[mirror.get(k, []) for k in keys]) if keys else set()
    body = [r for g in A['groups'] for r in g['paragraphs']]
    for s in A['slots']:
        for pid in A['intro']:
            if any(x == s['id'] or x.startswith(s['id'] + '.') for x in A['paras'][pid]['serves']):
                edges.append(dict(a=s['id'], b=pid, t='claim'))
    for pid in A['intro']:
        K = set(A['paras'][pid]['serves'])
        edges += [dict(a=pid, b=r, t='claim') for r in body if K & expand(A['paras'][r]['serves'])]
    for c in A['claims']:
        keys = {c['id']} | set(c['mirrors'])
        edges += [dict(a=r, b=c['id'], t='claim') for r in body if keys & set(A['paras'][r]['serves'])]
        edges += [dict(a=m, b=c['id'], t='mirror') for m in c['mirrors'] if m in info]
    for g in A['groups']:                                    # a chapter hanging off an introduction paragraph
        if g.get('parent') in info and g['parent'] in A['intro']:
            edges.append(dict(a=g['parent'], b=g['id'], t='struct'))
    return dict(cols=cols, nodes=nodes, info=info, edges=edges, sim_rows={}, changed_rows=[], sim=dict(label='', note=''))


def _grams(t):
    t = re.sub(r'[（(][^）)]*[）)]|[\s，。、：；“”‘’《》,.;:!?·—–-]', '', t)
    return {t[i:i + 2] for i in range(len(t) - 1)} | set(t)


def step_maps(d):
    """Each paragraph's outline steps matched to its sentences, keeping both orders (see the module docstring)."""
    rows = {r['id']: r for r in d['rows']}
    out = {}
    for p in d['paragraphs']:
        steps = [s.strip() for s in (p.get('flow') or '').split('→') if s.strip()]
        ids = [r for r in p['rows'] if r in rows]
        if not steps or not ids:
            continue
        txt = [rows[r]['zh'] + ' ' + ((rows[r].get('cn_analysis') or {}).get('previous') or {}).get('relation', '') for r in ids]
        G = [_grams(t) for t in txt]
        S = [[len(_grams(s) & g) / max(1, len(_grams(s))) for g in G] for s in steps]
        n, m = len(steps), len(ids)
        NEG = -1e9
        if m >= n:
            best = [[NEG] * (m + 1) for _ in range(n + 1)]
            back = [[0] * (m + 1) for _ in range(n + 1)]
            best[0][0] = 0
            for i in range(1, n + 1):
                for j in range(i, m - (n - i) + 1):
                    for k in range(i - 1, j):
                        if best[i - 1][k] == NEG:
                            continue
                        v = best[i - 1][k] + sum(S[i - 1][k:j]) / (j - k) ** 0.5
                        if v > best[i][j]:
                            best[i][j], back[i][j] = v, k
            cuts, j = [], m
            for i in range(n, 0, -1):
                k = back[i][j]
                cuts.append((k, j))
                j = k
            assign = [ids[a:b] for a, b in reversed(cuts)]
        else:                                                  # fewer sentences than steps: one sentence per step, order kept
            best = [[NEG] * m for _ in range(n)]
            back = [[0] * m for _ in range(n)]
            best[0][0] = S[0][0]
            for i in range(1, n):
                for j in range(m):
                    for k in (j - 1, j):
                        if 0 <= k and best[i - 1][k] > NEG and (n - 1 - i) >= (m - 1 - j):
                            v = best[i - 1][k] + S[i][j]
                            if v > best[i][j]:
                                best[i][j], back[i][j] = v, k
            j, seq = m - 1, []
            for i in range(n - 1, -1, -1):
                seq.append(j)
                j = back[i][j]
            assign = [[ids[j]] for j in reversed(seq)]
        weak = [i for i, a in enumerate(assign) if max(S[i][ids.index(r)] for r in a) < 0.2]
        out[p['id']] = dict(steps=steps, assign=assign, weak=weak)
    return out
