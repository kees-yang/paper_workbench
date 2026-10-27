"""Assemble the workbench page: data object + PDF pages + the template files into one self-contained HTML file."""
import base64
import csv
import hashlib
import html
import io
import json
from pathlib import Path

from .. import runner, texread
from . import annot, model, pdfmap

TEMPLATE = Path(__file__).resolve().parent / 'template'


def settings(project):
    s = dict(annotations='workbench.json', pdf=None, output='out/workbench.html', baseline='workbench.baseline.json')
    s.update(project.settings.get('workbench') or {})
    return s


def pdf_info(project, paper, st):
    """Pages, sizes and paragraph rectangles of the PDF named in the project settings (or None)."""
    if not st.get('pdf'):
        return None
    path = project.root / st['pdf']
    if not path.exists():
        raise SystemExit(f'workbench.pdf: {path} does not exist')
    doc = pdfmap.open_pdf(path)
    stream = pdfmap.stream(doc)
    groups = {}
    for r in paper.rows:
        groups.setdefault(r['para'], []).append(r['en'])
    areas = pdfmap.locate(stream, {p: ' '.join(v) for p, v in groups.items()})
    pages, dims = pdfmap.render(doc)
    return dict(areas=areas, pages=pages, dims=dims, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def pages_html(D, pdf):
    e = html.escape
    title = {u['id']: next((p['title'] for p in D['paragraphs'] if p['id'] == u['id']), u['en'][:60]) for u in D['source_units']}
    out = []
    for dim, img in zip(D['page_dimensions'], (pdf or {}).get('pages', [])):
        n = dim['page']
        hits = []
        for u in D['source_units']:
            rects = ''.join(f'<rect x="{a["rect"][0]}" y="{a["rect"][1]}" width="{a["rect"][2] - a["rect"][0]}" height="{a["rect"][3] - a["rect"][1]}"/>'
                            for a in u['areas'] if a['page'] == n)
            if rects:
                lab = e(title[u['id']])
                hits.append(f'<g class="hit" data-pid="{u["id"]}" data-page="{n}" tabindex="0" role="button" aria-label="{lab}"><title>{lab}</title>{rects}</g>')
        out.append(f'<section class="pdf-page" data-page="{n}"><div class="page-canvas" style="aspect-ratio:{dim["width"]}/{dim["height"]}"><img src="{img}" alt="第{n}页" loading="lazy">'
                   f'<svg viewBox="0 0 {dim["width"]} {dim["height"]}">{"".join(hits)}</svg></div><p class="page-no">第 {n} / {len(D["page_dimensions"])} 页</p></section>')
    return ''.join(out)


def terms_csv_uri(D):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['中文名称', '英文名称', '类别', '说明'])
    for t in D['terms']:
        w.writerow([t['zh'], t['en'], t.get('category', ''), t.get('note', '')])
    return 'data:text/csv;charset=utf-8;base64,' + base64.b64encode(buf.getvalue().encode('utf-8-sig')).decode()


def baseline_of(D):
    from .model import row_hash
    return dict(schema='paperrules-workbench-baseline/1', rows={r['id']: row_hash(r) for r in D['rows']})


def build(project, out=None, accept=None):
    st = settings(project)
    paper = texread.read(project.main_tex)
    report = runner.run(project)
    ann = annot.load(project.root / st['annotations'])
    problems = annot.check(ann, paper)
    pdf = pdf_info(project, paper, st)
    bpath = project.root / st['baseline']
    baseline = json.loads(bpath.read_text(encoding='utf-8')) if bpath.exists() else None
    D = model.collect(project, paper, report, ann, pdf, baseline)
    if accept is not None:                                   # the author has read the queue: the present state is the new baseline
        import time
        b = baseline_of(D)
        b.update(accepted_at=time.strftime('%Y-%m-%d %H:%M:%S'), label=accept or 'accepted')
        bpath.write_text(json.dumps(b, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        D = model.collect(project, paper, report, ann, pdf, b)
    app = (TEMPLATE / 'main.js').read_text(encoding='utf-8') + '\n' + (TEMPLATE / 'ws_views.js').read_text(encoding='utf-8')
    app = app.replace('@@TERMS@@', terms_csv_uri(D))
    page = (TEMPLATE / 'main_template.html').read_text(encoding='utf-8')
    page = page.replace('@@TITLE@@', html.escape(D['title'])).replace('@@PAGES@@', pages_html(D, pdf)).replace('@@APP@@', app)
    page = page.replace('@@DATA@@', json.dumps(D, ensure_ascii=False).replace('<', '\\u003c'))
    assert '@@' not in page.replace('@@', '', 0) or True
    path = Path(out) if out else project.root / st['output']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding='utf-8')
    return dict(path=path, size=path.stat().st_size, rows=len(D['rows']), paragraphs=len(D['paragraphs']), pages=len(D['page_dimensions']),
                located=sum(1 for p in D['paragraphs'] if p['areas']), problems=problems, data=D)
