"""paperrules: the name of paper_workbench before 0.5.0.

Old code keeps working: ``import paperrules``, ``from paperrules.workbench import page`` and ``python -m paperrules`` all reach
the paper_workbench modules (the same module objects, not copies). New code imports paper_workbench.
"""
import importlib
import importlib.abc
import importlib.util
import sys

import paper_workbench as _new
from paper_workbench import *  # noqa: F401,F403

__version__ = _new.__version__


class _Alias(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """paperrules.<x> -> paper_workbench.<x>."""

    def __init__(self):
        self._spec = {}

    def find_spec(self, name, path=None, target=None):
        if name.startswith('paperrules.') and name != 'paperrules.__main__':
            return importlib.util.spec_from_loader(name, self)
        return None

    def create_module(self, spec):
        mod = importlib.import_module('paper_workbench' + spec.name[len('paperrules'):])
        self._spec[spec.name] = mod.__spec__
        return mod

    def exec_module(self, module):
        module.__spec__ = self._spec.pop(module.__spec__.name, module.__spec__)   # keep the real module's own spec


if not any(isinstance(f, _Alias) for f in sys.meta_path):
    sys.meta_path.insert(0, _Alias())
