"""Certifying test named by the planted fixture's single manifest row.

Fixture data, never collected: this file is not named test_*.py, so pytest does
not pick it up, and `check_manifest.py` resolves the name by AST walk rather
than by collection.
"""


def test_planted_row_is_absent() -> None:
    """Named by P9.PLANTED.MISSING so the row's evidence citation resolves."""
    return None
