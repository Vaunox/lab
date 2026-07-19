#!/usr/bin/env python
"""The engine may not be its own oracle. Deep dive P0 section 9.2.

> **A fixture the engine produced is not a gate. It is a mirror.**

It will pass, it will look like rigour, and it will certify whatever the engine
happens to do -- including whatever it does wrong. With no external baseline this
is the only remaining way to cheat, and it is the obvious one, which is why it
gets a checker rather than a review note.

For every gate fixture declared in `ACCEPTANCE.md`, three assertions:

1. the blob hash matches the declaration
2. a derivation document exists alongside the fixture
3. the fixture commit **predates** the engine commit

No fixtures exist in P0. The tool ships anyway and is proven against a
fixture-of-fixtures, because building it in P4 -- the phase it polices -- would
mean building the judge and the defendant in the same session.

**Declaration format.** `ACCEPTANCE.md` carries a `<!-- gate_fixtures -->` marker
followed by a fenced yaml list. That format is a builder decision recorded for
operator review (D-004 in HANDOFF.md): section 9.2 fixes the three assertions but
does not fix the syntax that carries them, and P4 is where the first real
declaration lands. Zero declarations is the correct and expected P0 state, and it
is reported explicitly rather than passing in silence.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DECLARATION_MARKER = "<!-- gate_fixtures -->"


@dataclass(frozen=True)
class Declaration:
    """One declared gate fixture, as `ACCEPTANCE.md` states it."""

    id: str
    path: str
    blob_sha: str
    derivation: str
    engine_path: str = ""


@dataclass
class Report:
    findings: list[str] = field(default_factory=list)
    declarations: int = 0

    @property
    def ok(self) -> bool:
        return not self.findings


class ProvenanceError(RuntimeError):
    """The checker cannot run. Distinct from the checker finding a violation."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def parse_declarations(text: str) -> list[Declaration]:
    """Read the declared fixtures out of `ACCEPTANCE.md`.

    A malformed declaration raises rather than being skipped. A skipped
    declaration is a fixture that claims provenance and is never asked for it,
    which is worse than an undeclared fixture: it appears on the list.
    """
    if DECLARATION_MARKER not in text:
        return []

    after = text.split(DECLARATION_MARKER, 1)[1]
    blocks = re.findall(r"```yaml\n(.*?)```", after, re.DOTALL)
    if not blocks:
        raise ProvenanceError(f"{DECLARATION_MARKER} is present but no yaml block follows it")

    document = yaml.safe_load(blocks[0])
    if document is None:
        return []
    if not isinstance(document, list):
        raise ProvenanceError("gate_fixtures block must be a list of declarations")

    declarations: list[Declaration] = []
    for index, entry in enumerate(document):
        if not isinstance(entry, dict):
            raise ProvenanceError(f"declaration {index} is not a mapping")
        missing = {"id", "path", "blob_sha", "derivation"} - set(entry)
        if missing:
            raise ProvenanceError(f"declaration {index} is missing {sorted(missing)}")
        declarations.append(
            Declaration(
                id=str(entry["id"]),
                path=str(entry["path"]),
                blob_sha=str(entry["blob_sha"]),
                derivation=str(entry["derivation"]),
                engine_path=str(entry.get("engine_path", "")),
            )
        )
    return declarations


def blob_sha(path: Path) -> str:
    """Git's blob hash for a file, computed the way git itself computes it."""
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    import hashlib

    return hashlib.sha1(header + data).hexdigest()


def first_commit_touching(root: Path, path: str) -> str | None:
    """The earliest commit that introduced a path."""
    result = _git(root, "log", "--diff-filter=A", "--format=%H", "--", path)
    if result.returncode != 0:
        return None
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return commits[-1] if commits else None


def fixture_predates_engine(root: Path, declaration: Declaration) -> bool | None:
    """Whether the fixture commit is an ancestor of the engine commit.

    Returns None when the question cannot be asked -- no engine path declared,
    or one of the two paths has no introducing commit. The caller reports that
    as a finding rather than as a pass: an unanswerable provenance question is
    not an answered one.
    """
    if not declaration.engine_path:
        return None
    fixture_commit = first_commit_touching(root, declaration.path)
    engine_commit = first_commit_touching(root, declaration.engine_path)
    if fixture_commit is None or engine_commit is None:
        return None
    if fixture_commit == engine_commit:
        return False
    result = _git(root, "merge-base", "--is-ancestor", fixture_commit, engine_commit)
    return result.returncode == 0


def check_declaration(root: Path, declaration: Declaration, report: Report) -> None:
    """Apply the three section 9.2 assertions to one declared fixture."""
    fixture = root / declaration.path

    if not fixture.exists():
        report.findings.append(f"{declaration.id}: declared fixture {declaration.path} is absent")
        return

    actual = blob_sha(fixture)
    if actual != declaration.blob_sha:
        report.findings.append(
            f"{declaration.id}: blob hash mismatch for {declaration.path}. "
            f"ACCEPTANCE.md declares {declaration.blob_sha}, the file hashes to "
            f"{actual}. The fixture changed after it was declared, and a gate "
            "fixture that can be edited is not a gate"
        )

    derivation = root / declaration.derivation
    if not derivation.exists():
        report.findings.append(
            f"{declaration.id}: no derivation document at {declaration.derivation}. "
            "A fixture with no shown arithmetic cannot be distinguished from one "
            "the engine produced, and a fixture the engine produced is a mirror"
        )
    elif derivation.stat().st_size == 0:
        report.findings.append(f"{declaration.id}: derivation document is empty")

    if (root / ".git").exists():
        ancestry = fixture_predates_engine(root, declaration)
        if ancestry is False:
            report.findings.append(
                f"{declaration.id}: the fixture does not predate the engine. "
                "Fixtures land in a separate, EARLIER PR than the engine that "
                "must match them (section 11.2)"
            )
        elif ancestry is None and declaration.engine_path:
            report.findings.append(
                f"{declaration.id}: cannot establish that the fixture predates "
                f"{declaration.engine_path}. An unanswerable provenance question "
                "is not an answered one"
            )


def check(root: Path) -> Report:
    """Validate every fixture `ACCEPTANCE.md` declares."""
    acceptance = root / "ACCEPTANCE.md"
    if not acceptance.exists():
        raise ProvenanceError(f"ACCEPTANCE.md not found under {root}")

    declarations = parse_declarations(acceptance.read_text(encoding="utf-8"))
    report = Report(declarations=len(declarations))
    for declaration in declarations:
        check_declaration(root, declaration, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixture provenance (deep dive P0 section 9.2).")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)

    try:
        report = check(args.root)
    except ProvenanceError as exc:
        print(f"check_fixture_provenance: REFUSED TO RUN: {exc}", file=sys.stderr)
        return 2

    if report.findings:
        for finding in report.findings:
            print(f"  FAIL  {finding}", file=sys.stderr)
        print(f"check_fixture_provenance: {len(report.findings)} finding(s)", file=sys.stderr)
        return 1

    if report.declarations == 0:
        print(
            "check_fixture_provenance: no gate fixtures declared in ACCEPTANCE.md. "
            "That is the expected P0 state -- the tool ships before the phase it "
            "polices, so the judge is never built in the same session as the "
            "defendant."
        )
    else:
        print(f"check_fixture_provenance: {report.declarations} declaration(s) verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
