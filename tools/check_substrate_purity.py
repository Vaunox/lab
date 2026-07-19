#!/usr/bin/env python
"""The kill gate. Deep dive P0 section 9.2b, and Constitution S1.

Does nothing until Gate 4 cuts the `substrate-frozen` tag, and everything at
Gate 5. It tests the thing that was actually at stake, directly rather than by
proxy:

> **Can one contract hold two dissimilar simulation semantics without
> contaminating the truth beneath them?**

Against `git diff substrate-frozen..HEAD -- src/lab/{core,ledger,costs,fills,
validation}`: automatic failure on engine-specific vocabulary anywhere in the
substrate. If the second engine cannot be built without changing shared truth in
an engine-specific way, the abstraction is wrong and **the project stops.** It
does not get a flag.

Ships in P0, inert until P4 -- built before the code it polices, like every other
checker here. Inertness is reported explicitly and never as a pass: while the tag
does not exist there is nothing to compare against, and silence would be
indistinguishable from a clean substrate.

The judge reads *added lines of a unified diff*. Both the git path and the
fixture path produce that same text and are parsed by the same function, so the
planted violation and the real diff are graded by identical code.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

SUBSTRATE_PATHS = (
    "src/lab/core",
    "src/lab/ledger",
    "src/lab/costs",
    "src/lab/fills",
    "src/lab/validation",
)

FROZEN_TAG = "substrate-frozen"

FIXTURE_DIFF = "FIXTURE_SUBSTRATE_DIFF"

# Section 9.2b. Engine vocabulary has no business in shared truth: the substrate
# is what both engines stand on, and a substrate that knows which engine is
# calling has already forked.
ENGINE_VOCABULARY: tuple[str, ...] = (
    "intraday",
    "daily",
    "square_off",
    "squareoff",
    "MIS",
    "engine_id ==",
    "isinstance(engine",
)

# Matched case-sensitively and as a whole word. `MIS` is the broker product code;
# as a case-insensitive substring it fires on "mismatch", "permission" and
# "dismiss", and a kill gate that cries wolf on ordinary English is a kill gate
# somebody disables before Gate 5.
CASE_SENSITIVE_WORD_TERMS = frozenset({"MIS"})


@dataclass(frozen=True)
class AddedLine:
    """One added line of the substrate diff."""

    path: str
    text: str


@dataclass
class Report:
    findings: list[str] = field(default_factory=list)
    added_lines: int = 0
    inert: bool = False

    @property
    def ok(self) -> bool:
        return not self.findings


class SubstratePurityError(RuntimeError):
    """The checker cannot run. Distinct from the checker finding a violation."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def parse_added_lines(diff: str) -> list[AddedLine]:
    """Extract added lines from a unified diff, tracking the file they belong to.

    `+++ b/path` headers are consumed as headers, never as content -- otherwise
    the file header itself is scanned, and a diff touching
    `src/lab/costs/daily_schedule.py` reports a vocabulary violation on the
    strength of its own filename.
    """
    added: list[AddedLine] = []
    current = ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = target[2:] if target.startswith(("a/", "b/")) else target
            continue
        if line.startswith(("--- ", "diff ", "index ", "@@", "new file", "deleted file")):
            continue
        if line.startswith("+"):
            added.append(AddedLine(path=current, text=line[1:]))
    return added


def _pattern_for(term: str) -> re.Pattern[str]:
    """Build the match rule for one banned term.

    Substring and case-insensitive by default, because section 9.2b says
    *anywhere in the substrate* and because the realistic leak is a suffixed
    identifier rather than a bare word. `square_off_at` is exactly how this
    vocabulary actually arrives, and word-boundary matching misses it -- a false
    negative in the one checker whose job is to stop the project.

    Erring toward refusal is correct here in a way it rarely is. A false positive
    on the kill gate is loud, reviewable, and costs an argument. A false negative
    ships a contaminated substrate under two engines and is discovered, if ever,
    by whoever is auditing the ledger.
    """
    if term in CASE_SENSITIVE_WORD_TERMS:
        return re.compile(rf"\b{re.escape(term)}\b")
    return re.compile(re.escape(term), re.IGNORECASE)


def scan_vocabulary(lines: list[AddedLine]) -> list[str]:
    """Automatic failure on engine-specific vocabulary. Section 9.2b."""
    findings: list[str] = []
    for line in lines:
        for term in ENGINE_VOCABULARY:
            if _pattern_for(term).search(line.text):
                findings.append(
                    f"{line.path}: engine vocabulary {term!r} added to the "
                    f"substrate: {line.text.strip()!r}"
                )
    return findings


def substrate_diff(root: Path) -> tuple[str, bool]:
    """The diff under judgement, and whether the checker is inert.

    Inert means the `substrate-frozen` tag does not exist yet, which is the
    normal state from P0 until Gate 4. As elsewhere, the fixture seam is
    unreachable in any tree carrying a `.git`.
    """
    if (root / ".git").exists():
        tag = _git(root, "rev-parse", "--verify", f"refs/tags/{FROZEN_TAG}")
        if tag.returncode != 0:
            return "", True
        result = _git(root, "diff", f"{FROZEN_TAG}..HEAD", "--", *SUBSTRATE_PATHS)
        if result.returncode != 0:
            raise SubstratePurityError(f"cannot diff {FROZEN_TAG}..HEAD: {result.stderr.strip()}")
        return result.stdout, False

    fixture = root / FIXTURE_DIFF
    if not fixture.exists():
        raise SubstratePurityError(
            f"{root} is not a git repository and carries no {FIXTURE_DIFF}; "
            "there is no substrate diff to judge"
        )
    return fixture.read_text(encoding="utf-8"), False


def check(root: Path) -> Report:
    """Judge the substrate diff for engine contamination."""
    diff, inert = substrate_diff(root)
    if inert:
        return Report(inert=True)

    lines = parse_added_lines(diff)
    report = Report(added_lines=len(lines))
    report.findings.extend(scan_vocabulary(lines))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Substrate purity (deep dive P0 section 9.2b).")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)

    try:
        report = check(args.root)
    except SubstratePurityError as exc:
        print(f"check_substrate_purity: REFUSED TO RUN: {exc}", file=sys.stderr)
        return 2

    if report.inert:
        print(
            f"check_substrate_purity: inert -- no {FROZEN_TAG} tag exists yet. "
            "The kill gate arms at Gate 4 and fires at Gate 5. Reported rather "
            "than passed silently: nothing to compare is not a clean substrate."
        )
        return 0

    if report.findings:
        for finding in report.findings:
            print(f"  FAIL  {finding}", file=sys.stderr)
        print(
            "check_substrate_purity: the substrate has been changed in an "
            "engine-specific way. Constitution S1: if the second engine cannot "
            "be built without contaminating shared truth, the abstraction is "
            "wrong and the project STOPS. Do not patch this.",
            file=sys.stderr,
        )
        return 1

    print(f"check_substrate_purity: clean over {report.added_lines} added line(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
