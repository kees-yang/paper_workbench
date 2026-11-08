"""The review page: one or more built workbench pages side by side in a compact reading view.

It reads the data that ``paper_workbench workbench`` already wrote into each ``workbench.html`` and builds one offline page with
  Sentences      one paragraph at a time: its question and claim, then a table of the sentences (original and rendering) with
                 the link of each sentence to the previous one and to earlier text, and the PDF page with the paragraph box
  Abbreviations  the first use of each abbreviation in the abstract, the body and the supplement, and whether a definition
                 stands there ("long form (ABBR)", "ABBR (long form)", "ABBR is the ...", or a caption label "ABBR: ...")
  Notes          a note per sentence (kept in the browser), exported as Markdown
  Scores         an optional review score log: rounds per line, change per round, open issues
Nothing in the source pages changes.
"""
import json
import re
from collections import OrderedDict
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / 'template' / 'review_template.html'

# Tokens that name a venue, tool or common unit: no definition expected. A project adds its own names with --names.
BUILTIN_NAMES = set("""CVPR ICCV ECCV NeurIPS ICLR ICML AAAI IJCAI WACV BMVC TPAMI TIP IJCV TMM TCSVT ACM IEEE arXiv GitHub LaTeX
PyTorch TensorFlow JAX CUDA NVIDIA GPU CPU RGB ReLU GELU SiLU Adam AdamW SGD BatchNorm LayerNorm GroupNorm ImageNet COCO
OpenAI Anthropic Claude ChatGPT Linux GeForce RTX II III IV VI VII VIII IX XI XII""".split())
ABBR = re.compile(r"(?<![\w-])([A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*|[A-Z]{2,}\d*|m[A-Z][A-Za-z]+\d*|Q[a-z]{1,4})(?![\w-])")
SKIP = {'Fig', 'Figs', 'Table', 'Tables', 'Eq', 'Eqs', 'Sec', 'Top', 'Left', 'Right', 'Bottom', 'Bold', 'Mean'}
SUPP = re.compile(r'appendix|supplement|附录|补充', re.I)


def load(path):
    """The data object and the PDF page images of a built workbench page."""
    s = Path(path).read_text(encoding='utf-8')
    a = s.index('id="data">') + len('id="data">')
    data = json.loads(s[a:s.index('</script>', a)])
    imgs = re.findall(r'<img[^>]*src="(data:image/[a-z]+;base64,[^"]+)"', s)
    return data, imgs


def read_names(spec):
    """--names: a comma-separated list, or @file with names separated by spaces, commas or new lines."""
    out = set()
    for part in spec or []:
        text = Path(part[1:]).read_text(encoding='utf-8') if part.startswith('@') else part
        out |= {w for w in re.split(r'[\s,]+', text) if w and not w.startswith('#')}
    return out


def scope_of(row):
    if row.get('kind') == 'abstract':
        return 'Abstract'
    return 'Supplement' if row.get('_supp') else 'Body'


def abbreviations(rows, names):
    """First use of each abbreviation per scope, with its status: defined, undefined, or a name (no definition expected)."""
    out = OrderedDict()
    for r in rows:
        t = r.get('en_source') or ''
        sc = scope_of(r)
        for m in ABBR.finditer(t):
            a = m.group(1)
            if a in SKIP or len(a) < 2 or a.lower() == a:
                continue
            key = (sc, a)
            if key in out:
                out[key]['n'] += 1
                continue
            before, rest = t[max(0, m.start() - 2):m.start()], t[m.end():]
            inpar = before.endswith('(') and rest.startswith(')')                             # long form (ABBR)
            longafter = re.match(r' \((?!see\b)[a-z][a-z-]+ [a-z]', rest[:30]) is not None      # ABBR (long form)
            isdef = re.match(r'\s+(is|are|denotes|measures|gives)\s+(the|a|an)\s+[a-z]', rest[:30]) is not None
            label = re.match(r'(\s+[A-Z][A-Za-z]*)?:\s+[a-z]', rest[:16]) is not None           # caption label "ABBR: lowercase ..."
            if a in names or a.rstrip('s') in names:
                status = 'name'
            else:
                status = 'defined' if (inpar or longafter or isdef or label) else 'undefined'
            out[key] = dict(scope=sc, abbr=a, row=r['id'], status=status, n=1, text=t)
    return list(out.values())


def paper(name, path, names, supp_from=None, supp_page=None):
    data, imgs = load(path)
    rows = data['rows']
    start = re.compile(re.escape(supp_from), re.I) if supp_from else SUPP
    seen = False
    for r in rows:                      # the supplement starts at the first row of an appendix or supplement chapter
        if r.get('kind') != 'abstract' and (start.search(str(r.get('chapter', ''))) or (supp_from and start.match(str(r.get('section', ''))))):
            seen = True
        r['_supp'] = seen and r.get('kind') != 'abstract'
    where = {}
    for p in data['paragraphs']:
        ar = p.get('areas') or []
        if ar:
            pg = min(x['page'] for x in ar)
            where[p['id']] = (pg, min(x['rect'][1] for x in ar if x['page'] == pg))
    last = (0, 0)
    for r in rows:                      # rows of an unlocated paragraph keep the place of the row before them
        last = where.get(r.get('paragraph_id'), last)
        r['_at'] = last
        if supp_page and r.get('kind') != 'abstract' and last[0] >= supp_page:
            r['_supp'] = True
    ab = abbreviations(sorted(rows, key=lambda r: (0 if r.get('kind') == 'abstract' else 1, r['_at'], r['id'])), names)
    P = [dict(id=p['id'], ch=p.get('chapter', ''), sec=p.get('section', ''), kind=p.get('kind', ''), title=p.get('title', ''),
              q=p.get('question', ''), claim=p.get('claim', ''), prev=p.get('previous_claim', ''), areas=p.get('areas', []),
              rows=[x if isinstance(x, str) else x.get('id') for x in p.get('rows', [])]) for p in data['paragraphs']]
    R = {}
    for r in rows:
        a = r.get('cn_analysis') or {}

        def link(f):
            x = a.get(f) or {}
            return {k: x.get(k, '') for k in ('anchor_id', 'anchor_quote', 'target_quote', 'relation')} if x.get('anchor_id') else None
        R[r['id']] = dict(en=r.get('en_source', ''), zh=r.get('zh', ''), p=r.get('paragraph_id', ''), prev=link('previous'), earl=link('earlier'))
    stats = dict(rows=len(R), paras=len(P), prev=sum(1 for v in R.values() if v['prev']), earl=sum(1 for v in R.values() if v['earl']),
                 located=sum(1 for p in P if p['areas']), undefined=sum(1 for x in ab if x['status'] == 'undefined'))
    return dict(name=name, title=data.get('title', ''), version=data.get('pdf_version', ''), P=P, R=R, imgs=imgs,
                dims=data.get('page_dimensions', []), abbr=ab, stats=stats)


def build(pages, out, names=(), scores=None, title='Review Workbench', supp_from=None, supp_page=None):
    """pages: list of (name, path to workbench.html). Writes one self-contained HTML file and returns the paper summaries."""
    nm = BUILTIN_NAMES | set(names)
    papers = [paper(n, p, nm, supp_from, supp_page) for n, p in pages]
    safe = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
    sc = safe(json.loads(Path(scores).read_text(encoding='utf-8'))) if scores else '{}'
    html = TEMPLATE.read_text(encoding='utf-8')
    esc = title.replace('&', '&amp;').replace('<', '&lt;')
    html = html.replace('__TITLE__', esc).replace('__SCORES__', sc).replace('__DATA__', safe(papers))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    return papers
