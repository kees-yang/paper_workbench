import json
import re
import tempfile
import unittest
from pathlib import Path

from paperrules import texread
from paperrules.config import load_project
from paperrules.workbench import annot, model, page
from helpers import BIB, DOC, EXAMPLE, make_project

try:
    import fitz
except ImportError:      # the PDF pane is optional
    fitz = None


def data_of(path):
    html = Path(path).read_text(encoding='utf-8')
    assert '@@' not in html
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace('\\u003c', '<'))


TABLE = r"""\begin{table}\caption{T.}\label{tab:t}
\begin{tabular}{c|cc}\hline
 & \multicolumn{2}{c}{Score}\\ & A & B \\ \hline
 M1 & 1.0 & \textbf{2.0}\\ \hline
 Ours & \br{3.0} & 4.0 \\ \hline
\end{tabular}\end{table}"""


class Annotations(unittest.TestCase):
    def setUp(self):
        self.paper = texread.read(make_project({'main.tex': DOC, 'refs.bib': BIB}) / 'main.tex')

    def test_ids_and_listing(self):
        ids = annot.row_ids(self.paper)
        self.assertEqual(ids['S001'], 'P001-R001')
        self.assertIn('P001-R001', annot.listing(self.paper))

    def test_check_finds_bad_quotes_and_ids(self):
        a = {'rows': {'P002-R001': {'zh': '红外图像很好。', 'previous': {}},
                      'P002-R002': {'zh': '可见光图像也很好。', 'previous': dict(anchor_id='P002-R001', anchor_quote='不在句中', target_quote='可见光图像', anchor_head='', target_head='')},
                      'P999-R001': {'zh': 'x'}}, 'paragraphs': {'P888': {}}}
        problems = annot.check(a, self.paper)
        self.assertTrue(any('P999-R001' in p for p in problems))
        self.assertTrue(any('不在句中' in p for p in problems))
        self.assertTrue(any('P888' in p for p in problems))

    def test_skeleton_covers_every_row(self):
        sk = annot.skeleton(self.paper)
        self.assertEqual(len(sk['rows']), len(self.paper.rows))


class Tables(unittest.TestCase):
    def test_header_rows_bold_and_rules(self):
        doc = '\\newcommand{\\br}[1]{\\textbf{#1}}\n\\begin{document}\n' + TABLE + '\n\\end{document}'
        p = texread.read(make_project({'main.tex': doc}) / 'main.tex')
        t = model.parse_table(p.floats[0], {}, p.labels, p.bold_macros)
        self.assertEqual(t['head'], ['Score · A', 'Score · B'])
        rows = t['sections'][0]['rows']
        self.assertEqual([r['label'] for r in rows], ['M1', 'Ours'])
        self.assertEqual([(c['text'], c['mark']) for c in rows[0]['cells']], [('1.0', ''), ('2.0', 'best')])
        self.assertEqual(rows[1]['cells'][0]['mark'], 'best')            # a macro that wraps \textbf
        self.assertTrue(rows[1]['ours'])


class Build(unittest.TestCase):
    def test_build_without_annotations_or_pdf(self):
        d = make_project({'main.tex': DOC, 'refs.bib': BIB})
        out = d / 'wb.html'
        res = page.build(load_project(d), out)
        D = data_of(out)
        self.assertEqual(res['rows'], len(D['rows']))
        self.assertTrue(D['paragraphs'] and D['canvas']['nodes'] and D['ws']['paragraphs'])
        self.assertEqual(D['page_dimensions'], [])                      # no PDF: the pane is hidden by the page
        self.assertEqual(D['ids']['abstract'], 'P001')
        self.assertEqual(D['compliance']['summary']['fail'], 1)         # the rule report is embedded (B1: missing key b)

    def test_refresh_queue_follows_the_accepted_baseline(self):
        d = make_project({'main.tex': DOC, 'refs.bib': BIB})
        proj = load_project(d)
        page.build(proj, d / 'wb.html', accept='first')
        self.assertEqual(data_of(d / 'wb.html')['ws']['queue'], [])
        (d / 'main.tex').write_text(DOC.replace('Fusion', 'Image fusion'))
        page.build(load_project(d), d / 'wb.html')
        D = data_of(d / 'wb.html')
        self.assertTrue(any(i['unit'].startswith('sentence:') for i in D['ws']['queue']))
        self.assertTrue(D['canvas']['changed_rows'])

    def test_template_has_no_paper_specific_ids(self):
        t = Path(page.TEMPLATE)
        text = ''.join((t / f).read_text(encoding='utf-8') for f in ('main.js', 'ws_views.js', 'main_template.html'))
        self.assertEqual(re.findall(r'''['"]P\d{3}(?:-R\d{3})?['"]''', text), [])      # no paragraph or sentence id of any paper
        self.assertNotIn('writing_system', text)                                   # no path of the workspace the page came from


@unittest.skipIf(fitz is None, 'PyMuPDF not installed')
class Pdf(unittest.TestCase):
    def test_paragraphs_are_found_on_the_page(self):
        from paperrules.workbench import pdfmap
        d = Path(tempfile.mkdtemp(prefix='paperrules-pdf-'))
        doc = fitz.open()
        pg = doc.new_page()
        y = 80
        for line in ['The first paragraph talks about infrared images and their', 'many uses in surveillance and driving assistance today.',
                     'A second paragraph explains why visible images carry texture', 'details that infrared images usually lack in practice.']:
            pg.insert_text((72, y), line, fontsize=11)
            y += 14 if 'second' not in line and 'many' not in line else 30
        doc.save(d / 'a.pdf')
        st = pdfmap.stream(pdfmap.open_pdf(d / 'a.pdf'))
        res = pdfmap.locate(st, {'P1': 'The first paragraph talks about infrared images and their many uses in surveillance and driving assistance today.',
                                 'P2': 'A second paragraph explains why visible images carry texture details that infrared images usually lack in practice.'})
        self.assertEqual(set(res), {'P1', 'P2'})
        self.assertLess(res['P1'][0]['rect'][3], res['P2'][0]['rect'][1] + 1)     # the first paragraph is above the second


@unittest.skipIf(fitz is None, 'PyMuPDF not installed')
class ExampleWorkbench(unittest.TestCase):
    def test_example_page_has_every_panel_filled(self):
        out = Path(tempfile.mkdtemp(prefix='paperrules-wb-')) / 'wb.html'
        res = page.build(load_project(EXAMPLE), out)
        self.assertEqual(res['problems'], [])
        D = data_of(out)
        self.assertEqual((len(D['paragraphs']), len(D['rows'])), (53, 196))
        self.assertGreaterEqual(res['located'], 45)
        self.assertEqual(len(D['page_dimensions']), 10)
        self.assertEqual([L['id'] for L in D['flow']['lines']], ['GAP', 'MOTIVATION', 'METHOD', 'RESULTS'])
        self.assertEqual(len(D['ws']['records']), 13)
        self.assertEqual(len(D['ws']['floats']['tables']), 4)
        self.assertTrue(all(t.get('sections') for t in D['ws']['floats']['tables'].values()))
        self.assertEqual(D['ws']['queue'], [])                                   # the baseline of the example is accepted
        self.assertTrue(any(r['cn_analysis']['previous']['anchor_id'] for r in D['rows']))
        self.assertTrue(D['spo'])


if __name__ == '__main__':
    unittest.main()


class Review(unittest.TestCase):
    """The review page reads built workbench pages and adds sentence links, an abbreviation check and a score log."""
    PAGE = EXAMPLE / 'expected' / 'workbench.html'

    def test_review_page(self):
        from paperrules.workbench import review
        d = Path(tempfile.mkdtemp())
        scores = d / 'scores.json'
        scores.write_text(json.dumps({'target': 8, 'rounds': [{'line': 'main', 'round': 'R1', 'version': 'v1', 'score': 5},
                                                             {'line': 'main', 'round': 'R2', 'version': 'v2', 'score': 6}]}), encoding='utf-8')
        out = d / 'review.html'
        papers = review.build([('one', str(self.PAGE)), ('two', str(self.PAGE))], out, names={'APTP'}, scores=str(scores))
        html = out.read_text(encoding='utf-8')
        self.assertEqual(len(papers), 2)
        self.assertNotIn('__DATA__', html)
        self.assertNotIn('__SCORES__', html)
        p = papers[0]
        self.assertGreater(p['stats']['rows'], 100)
        self.assertGreater(p['stats']['prev'], 0)
        st = {x['abbr']: x['status'] for x in p['abbr'] if x['scope'] == 'Body'}
        self.assertEqual(st.get('APTP'), 'name')
        self.assertEqual(st.get('GPU'), 'name')
        self.assertNotIn('Quantitative', st)

    def test_definition_forms(self):
        from paperrules.workbench import review
        rows = [dict(id='P001-R001', kind='paragraph', en_source='We use the structural similarity (SSIM) and EN (entropy of the image).'),
                dict(id='P001-R002', kind='paragraph', en_source='VIF is the visual information fidelity. AG rises.')]
        st = {x['abbr']: x['status'] for x in review.abbreviations(rows, set())}
        self.assertEqual(st, {'SSIM': 'defined', 'EN': 'defined', 'VIF': 'defined', 'AG': 'undefined'})

    def test_cli(self):
        from paperrules import cli
        out = Path(tempfile.mkdtemp()) / 'r.html'
        cli.main(['review', f'example={self.PAGE}', '--out', str(out), '--names', 'APTP,MSRS'])
        self.assertTrue(out.is_file())
