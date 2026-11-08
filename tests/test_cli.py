import io
import json
import unittest
from contextlib import redirect_stdout

import tempfile
from pathlib import Path

from paper_workbench import cli
from paper_workbench.config import load_project
from helpers import BIB, DOC, make_project


def run(*argv):
    out = io.StringIO()
    code = 0
    with redirect_stdout(out):
        try:
            cli.main(list(argv))
        except SystemExit as e:
            code = e.code or 0
    return code, out.getvalue()


class CliTest(unittest.TestCase):
    def test_init_check_and_exit_codes(self):
        import tempfile
        from pathlib import Path
        d = Path(tempfile.mkdtemp(prefix='paperrules-cli-'))
        (d / 'main.tex').write_text(DOC)
        (d / 'refs.bib').write_text(BIB)
        code, out = run('init', str(d), '--main', 'main.tex')
        self.assertEqual(code, 0)
        self.assertTrue((d / 'paper_workbench.json').exists() and (d / 'rules.local.json').exists())
        code, out = run('check', str(d))
        self.assertEqual(code, 1)                      # B1 fails (cited key b is missing)
        self.assertTrue((d / 'out' / 'report.html').exists())
        res = json.loads((d / 'out' / 'report.json').read_text())
        self.assertEqual(res['summary']['fail'], 1)
        code, out = run('check', str(d), '--only', 'W10', '--no-files')
        self.assertEqual(code, 0)

    def test_rules_and_test_commands(self):
        d = make_project({'main.tex': '\\begin{document}\nHello there.\n\\end{document}'})
        code, out = run('rules', 'tree', '--project', str(d))
        self.assertEqual(code, 0)
        self.assertIn('W14', out)
        code, out = run('rules', 'markdown', '--project', str(d))
        self.assertIn('一句一个主要动作', out)
        code, out = run('test', str(d))
        self.assertEqual(code, 0)

    def test_accept_writes_exception(self):
        d = make_project({'main.tex': '\\begin{document}\nWe evaluate it.\n\\end{document}'})
        code, out = run('accept', 'W12', 'We evaluate it.', '--reason', 'authors are the actor', '--project', str(d))
        self.assertEqual(code, 0)
        ex = json.loads((d / 'exceptions.json').read_text())['exceptions']
        self.assertEqual(ex[0]['rule'], 'W12')
        code, out = run('check', str(d), '--only', 'W12', '--json')
        res = json.loads(out)
        self.assertEqual([f['status'] for f in res['findings']], ['accepted'])


if __name__ == '__main__':
    unittest.main()


class FormerName(unittest.TestCase):
    """paper_workbench was paperrules before 0.5.0: old imports, the old command and old project files keep working."""

    def test_old_imports_reach_the_same_modules(self):
        import paperrules
        import paper_workbench
        from paperrules.workbench import review as old
        from paper_workbench.workbench import review as new
        from paperrules.config import load_project as old_load
        self.assertIs(old, new)
        self.assertIs(old_load, load_project)
        self.assertEqual(paperrules.__version__, paper_workbench.__version__)
        self.assertEqual(new.__spec__.name, 'paper_workbench.workbench.review')

    def test_old_command(self):
        import subprocess
        import sys
        root = Path(__file__).resolve().parents[1]
        r = subprocess.run([sys.executable, '-m', 'paperrules', '--version'], capture_output=True, text=True, cwd=root)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('paper_workbench', r.stdout)

    def test_old_project_file(self):
        d = Path(tempfile.mkdtemp(prefix='paperrules-old-'))
        (d / 'main.tex').write_text(DOC, encoding='utf-8')
        (d / 'paperrules.json').write_text(json.dumps({'main_tex': 'main.tex'}), encoding='utf-8')
        self.assertEqual(load_project(d).main_tex.name, 'main.tex')
