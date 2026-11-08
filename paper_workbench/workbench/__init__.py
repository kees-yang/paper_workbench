"""The workbench: a self-contained HTML page with the paper's PDF pages, an argument canvas and analysis panels.

``build(project)`` collects the paper (reader), the rule report, the glossary and an optional annotation file
(``workbench.json``: Chinese rendering, sentence links, claims, storyline) into one data object and fills the template
in ``template/``. See docs/workbench.md for the data contract.
"""
