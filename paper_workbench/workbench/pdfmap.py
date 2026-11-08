"""PDF pages as images, and the place of each paragraph on them (PyMuPDF, optional dependency: pip install pymupdf).

The paragraph text of the LaTeX reader is aligned with the text lines of the PDF: the first and last word 4-grams of a
paragraph are looked up in the word stream of the PDF (two-column order, hyphenated words rejoined), and the lines
between them, per page and column, give the rectangles. A paragraph the alignment cannot find has no rectangle: it is
still analysed, only a click on the page does not select it.
"""
import base64
import re

WORD = re.compile(r'[a-z]{2,}')


def _fitz():
    try:
        import fitz
    except ImportError as e:
        raise SystemExit('the PDF pane needs PyMuPDF: pip install pymupdf') from e
    return fitz


def words(text):
    return WORD.findall(text.lower())


def page_lines(page):
    """Text lines of a page in reading order: (rect, text, column). Full-width blocks split the page into bands;
    inside a band the left column comes before the right one."""
    W = page.rect.width
    blocks = [b for b in page.get_text('dict')['blocks'] if b['type'] == 0 and b['lines']]
    full = sorted([b for b in blocks if b['bbox'][2] - b['bbox'][0] > 0.62 * W], key=lambda b: b['bbox'][1])
    cols = [b for b in blocks if b not in full]
    out = []

    def emit(bs, col):
        for b in sorted(bs, key=lambda b: b['bbox'][1]):
            for ln in b['lines']:
                if abs(ln['dir'][0]) < 0.99:                      # rotated text, such as the arXiv stamp
                    continue
                t = ''.join(s['text'] for s in ln['spans']).strip()
                if t:
                    out.append((tuple(ln['bbox']), t, col))

    edges = [-1.0] + [b['bbox'][1] for b in full] + [1e9]
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        band = [b for b in cols if lo <= b['bbox'][1] < hi] if i else [b for b in cols if b['bbox'][1] < hi]
        emit([b for b in band if (b['bbox'][0] + b['bbox'][2]) / 2 < W / 2], 0)
        emit([b for b in band if (b['bbox'][0] + b['bbox'][2]) / 2 >= W / 2], 1)
        if i < len(full):
            emit([full[i]], 2)
    return out


def stream(doc):
    """(tokens, owner) where owner[i] = index of the line that holds token i; lines = list of (page, rect, col)."""
    toks, owner, lines = [], [], []
    for pno, page in enumerate(doc, 1):
        carry = ''
        for rect, text, col in page_lines(page):
            lines.append((pno, rect, col))
            ws = words(text)
            if carry and ws and text[:1].islower():       # "princi-" + "ple"
                ws[0] = carry + ws[0]
            carry = ''
            if text.endswith('-') and WORD.search(text) and ws:
                carry = ws.pop()
            for w in ws:
                toks.append(w)
                owner.append(len(lines) - 1)
    return toks, owner, lines


def locate(doc_stream, texts):
    """Rectangles per paragraph text: {key: [{page, rect}]}. texts: ordered {key: english text}."""
    toks, owner, lines = doc_stream
    idx = {n: {} for n in (6, 4)}
    for n in idx:
        for i in range(len(toks) - n + 1):
            idx[n].setdefault(tuple(toks[i:i + n]), []).append(i)
    res, last = {}, 0

    def find(pw, rng, lo, hi=None):
        """First position (in word index of the paragraph, offset) of an n-gram of pw inside the PDF stream."""
        for n in (6, 4):
            for a in rng:
                if a < 0 or a + n > len(pw):
                    continue
                c = [i for i in idx[n].get(tuple(pw[a:a + n]), []) if i >= lo and (hi is None or i <= hi)]
                if c:
                    return a, n, min(c, key=lambda i: abs(i - lo))
        return None

    for key, text in texts.items():
        pw = words(text)
        if len(pw) < 5:
            continue
        f = find(pw, range(0, 4), 0)
        if f is None:
            continue
        a, n, i = f
        near = [j for j in idx[n][tuple(pw[a:a + n])]]
        i = min(near, key=lambda j: (j < last - 5, abs(j - last)))     # several hits: the one right after the previous paragraph
        start = max(i - a, 0)
        g = find(pw, range(len(pw) - 6, max(len(pw) - 12, -1), -1), start, start + 3 * len(pw) + 60)
        end = g[2] + (len(pw) - g[0]) - 1 if g else start + len(pw)
        end = min(end, len(toks) - 1)
        ls = sorted({owner[k] for k in range(start, end + 1)})
        groups = {}
        for li in ls:
            pno, rect, col = lines[li]
            gr = groups.setdefault((pno, col), list(rect))
            gr[0], gr[1], gr[2], gr[3] = min(gr[0], rect[0]), min(gr[1], rect[1]), max(gr[2], rect[2]), max(gr[3], rect[3])
        res[key] = [dict(page=p, rect=[round(v, 2) for v in r]) for (p, _), r in sorted(groups.items())]
        last = end
    return res


def render(doc, dpi=96, quality=68):
    """JPEG data URIs and the size in points of every page."""
    pages, dims = [], []
    for pno, page in enumerate(doc, 1):
        pix = page.get_pixmap(dpi=dpi)
        pages.append('data:image/jpeg;base64,' + base64.b64encode(pix.tobytes('jpeg', jpg_quality=quality)).decode())
        dims.append(dict(page=pno, width=page.rect.width, height=page.rect.height))
    return pages, dims


def open_pdf(path):
    return _fitz().open(str(path))
