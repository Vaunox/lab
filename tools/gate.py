#!/usr/bin/env python
"""The gate. Deep dive P0 section 5.1.

Python, not make. There is no make on Windows, and a gate the operator cannot
run is a gate the operator does not run.

Fails closed on zero registered checkers. "Nothing to check" is not "all checks
passed", and during P0 -- while the checkers are still being written -- that
distinction is the whole difference between a bootstrap and a bypass.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_attribution
import check_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Stage:
    """One gate stage: a name and something that returns True on success."""

    name: str
    run: Callable[[Path], bool]


class EmptyRegistryError(RuntimeError):
    """Raised when the gate is asked to run with no registered checkers."""


def _shell(root: Path, command: list[str]) -> bool:
    result = subprocess.run(command, cwd=root, check=False)
    return result.returncode == 0


def stage_lint(root: Path) -> bool:
    return _shell(root, [sys.executable, "-m", "ruff", "check", "."])


def stage_types(root: Path) -> bool:
    return _shell(root, [sys.executable, "-m", "mypy"])


def stage_tests(root: Path) -> bool:
    return _shell(root, [sys.executable, "-m", "pytest", "-q"])


def stage_manifest(root: Path) -> bool:
    """Run the completeness gate as four reported sub-checks.

    The sub-assertions are called here, on the gate's real path, rather than
    being referenced from a test written to supply a call site. DoD-(a) asks
    whether a primitive is genuinely invoked; the honest invoker of a manifest
    sub-check is the gate that runs it. Reserve tests for proving behaviour.

    Running them as named stages also means a failure says which of the four
    broke, instead of reporting an opaque "manifest failed".
    """
    report = check_manifest.Report()
    try:
        deep_dive = check_manifest.locate_deep_dive(root)
        manifest = check_manifest.assert_deep_dive_frozen(deep_dive)
        rows = check_manifest.parse_rows(manifest)
    except check_manifest.ManifestError as exc:
        print(f"    REFUSED TO RUN: {exc}", file=sys.stderr)
        return False

    report.rows_total = len(rows)
    for row in rows:
        if check_manifest.check_existence(root, row, report):
            report.rows_built += 1
        check_manifest.check_certifying_test(root, row, report)
        if row.call_site == "required":
            check_manifest.assert_called_outside_own_module(root, row, report)

    check_manifest.assert_closed_loop(rows, deep_dive, report)
    check_manifest.assert_deferrals_empty(root, report)

    print(check_manifest.format_tally(report, deep_dive.name.split("_", 1)[0]))
    for failure in report.failures:
        print(f"    {failure}", file=sys.stderr)
    return report.ok


def stage_attribution(root: Path) -> bool:
    """Scan the full history for AI authorship, in process. Section 4.3.

    Run here rather than by subprocess so that `scan_authorship_metadata` is
    invoked from the gate's real path. Operator ruling R-006: certifying tests
    prove behaviour, they do not supply call sites, and the honest invoker of a
    metadata scan is the gate that runs it.
    """
    try:
        commits = check_attribution.read_history(root)
    except check_attribution.HistoryUnavailableError as exc:
        print(f"    REFUSED TO RUN: {exc}", file=sys.stderr)
        return False

    findings = check_attribution.scan_authorship_metadata(commits)
    findings.extend(check_attribution.scan_tracked_paths(root))
    for finding in findings:
        print(f"    {finding}", file=sys.stderr)
    if not findings:
        print(f"    clean over {len(commits)} record(s)")
    return not findings


def _script_stage(script: str) -> Callable[[Path], bool]:
    def run(root: Path) -> bool:
        target = root / script
        if not target.exists():
            print(f"    missing checker: {script}", file=sys.stderr)
            return False
        return _shell(root, [sys.executable, script])

    return run


# Section 5.1 order: lint, types, tests, manifest, stubs, spec-isolation,
# imports, attribution, fixtures, substrate-purity.
#
# Mutation testing is deliberately absent: it is slow, and it runs on gate PRs
# and nightly instead (blueprint section 9.8).
STAGES: list[Stage] = [
    Stage("lint", stage_lint),
    Stage("types", stage_types),
    Stage("tests", stage_tests),
    Stage("manifest", stage_manifest),
    Stage("stubs", _script_stage("tools/check_no_stubs.py")),
    Stage("spec-isolation", _script_stage("tools/check_spec_isolation.py")),
    Stage("imports", _script_stage("tools/check_import_graph.py")),
    Stage("attribution", stage_attribution),
    Stage("fixtures", _script_stage("tools/check_fixture_provenance.py")),
    Stage("substrate-purity", _script_stage("tools/check_substrate_purity.py")),
]


def run_gate(root: Path, stages: list[Stage]) -> int:
    """Run every stage in order. Refuse to pass an empty registry.

    An empty registry is not a clean run. A gate that reports success because it
    was given nothing to do is the exact shape of the bypass this project exists
    to refuse.
    """
    if not stages:
        raise EmptyRegistryError(
            "no checkers registered -- 'nothing to check' is not 'all checks passed'"
        )

    failed: list[str] = []
    for stage in stages:
        print(f"\n=== {stage.name} ===")
        if stage.run(root):
            print(f"--- {stage.name}: ok")
        else:
            print(f"--- {stage.name}: FAILED")
            failed.append(stage.name)

    print("\n" + "=" * 60)
    if failed:
        print(f"GATE RED -- failed stages: {', '.join(failed)}")
        return 1
    print(f"GATE GREEN -- {len(stages)} stages passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The gate (deep dive P0 section 5.1).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        return run_gate(args.root, STAGES)
    except EmptyRegistryError as exc:
        print(f"gate: FAILS CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
