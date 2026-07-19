"""The scaffold. Deep dive P0 sections 4.4, 5 and 5.3."""

from __future__ import annotations

import tomllib
from typing import Any

import yaml

from tests.completeness.registry import REPO_ROOT


def _pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_mypy_is_strict() -> None:
    """Section 5: strict, and not "strict where convenient".

    The substrate's correctness argument leans on types, and a partially-typed
    substrate has the appearance of that argument without the substance. The
    covered paths are asserted too -- `strict = true` over an empty `files` list
    is strictness applied to nothing.
    """
    mypy = _pyproject()["tool"]["mypy"]

    assert mypy["strict"] is True
    assert set(mypy["files"]) >= {"src", "tools", "tests"}


def test_precommit_runs_stub_check() -> None:
    """Section 5: pre-commit catches it before the commit exists.

    The gate catches the same things before the merge does. Two layers, because
    a check that only runs at merge time is a check that runs after the mistake
    has already been made comfortable.
    """
    document = yaml.safe_load((REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    entries = [
        str(hook.get("entry", ""))
        for repo in document["repos"]
        for hook in (repo.get("hooks") or [])
    ]

    assert any("check_no_stubs.py" in entry for entry in entries), entries
    assert any("check_attribution.py" in entry for entry in entries), entries


def test_license_is_apache_2() -> None:
    """Section 5.3. A repository with no licence is "all rights reserved" by default.

    That is the wrong default to hold for even one day, least of all on a public
    repo where a contributor could open a PR into an IP vacuum. The structural
    assertions guard against a truncated or reflowed copy: Session 1 wrote one
    that was textually complete and structurally destroyed, 202 lines collapsed
    onto one.
    """
    text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")

    assert "Apache License" in text
    assert "Version 2.0, January 2004" in text
    assert "http://www.apache.org/licenses/" in text
    assert len(text.splitlines()) > 190, "the licence looks reflowed or truncated"


def test_notice_present() -> None:
    """Section 5.3: Apache-2.0 plus NOTICE, and the NOTICE names a holder."""
    notice = REPO_ROOT / "NOTICE"

    assert notice.exists()
    text = notice.read_text(encoding="utf-8").strip()
    assert text, "NOTICE is empty"
    assert "Copyright" in text


def test_claude_md_is_ignored() -> None:
    """Section 4.4: a committed tool config is the loudest signature there is.

    Both halves are asserted -- that the ignore rules exist, and that nothing
    matching them is actually tracked. The rule without the tracked-file check is
    a claim about intent; a file already committed stays committed no matter what
    `.gitignore` says afterwards.
    """
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "CLAUDE.md" in gitignore
    assert ".claude/" in gitignore or ".claude" in gitignore

    import check_attribution

    assert check_attribution.scan_tracked_paths(REPO_ROOT) == []


def test_pyproject_excludes_fixtures_from_type_checking() -> None:
    """The planted violations are data, not source.

    They are deliberately broken trees fed to the checkers, and two of them share
    a filename on purpose. Type-checking them would fail on the collision rather
    than on anything meaningful.
    """
    mypy = _pyproject()["tool"]["mypy"]

    assert any("fixtures" in pattern for pattern in mypy.get("exclude", []))
