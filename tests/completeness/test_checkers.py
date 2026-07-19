"""The planted-violation harness. Deep dive P0 section 2.2, and failure case 15.

> A checker that always passes is worse than no checker, because it manufactures
> confidence.

`test_every_checker_rejects_its_fixture` is the phase's load-bearing test: each
of the seven checkers is pointed at a deliberately broken tree and must exit
non-zero. Section 12 raises it to a correctness-gate condition in its own right,
and section 10 calls its absence *"the one that matters."*

Two properties are proven here, not one. That a checker rejects a broken tree
shows it can fail. That it accepts a clean one shows it is not merely always
failing -- which is the same vacuity as always passing, wearing the opposite
sign. Both fixtures ship.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import check_manifest
import check_no_stubs
import check_spec_isolation
import pytest

from tests.completeness.registry import CHECKERS, FIXTURE_ROOT, REPO_ROOT, Checker

# --------------------------------------------------------------------------
# The harness
# --------------------------------------------------------------------------


@pytest.mark.parametrize("checker", CHECKERS, ids=lambda c: c.stage)
def test_every_checker_rejects_its_fixture(checker: Checker) -> None:
    """Each of the seven exits non-zero on its planted violation.

    Section 2.2. An unbuilt checker fails here rather than being skipped: a skip
    would report green for machinery that does not exist, which is the vacuous
    pass this whole phase is arranged against.
    """
    assert checker.script_path.exists(), (
        f"{checker.script} is not built. Section 2.2 requires every checker to "
        "ship with a planted violation and a test proving it rejects it; an "
        "unbuilt checker is an honest red, never a skip"
    )
    assert checker.fixture_path.is_dir(), (
        f"{checker.script} has no planted violation at "
        f"tests/completeness/fixtures/{checker.fixture}/. A checker with no "
        "proof it can fail is a checker that will one day silently stop working"
    )

    result = subprocess.run(
        [sys.executable, str(checker.script_path), "--root", str(checker.fixture_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, (
        f"{checker.script} ACCEPTED its planted violation at "
        f"fixtures/{checker.fixture}/. It cannot fail, so it certifies nothing.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_checker_registry_matches_manifest() -> None:
    """The registry is closed against the frozen manifest, not against itself.

    Section 11 enumerates the checker scripts. If the registry were merely a
    hand-kept list, a checker could be added to the manifest and never acquire a
    fixture -- and the harness above would go on reporting green over six
    checkers while the seventh went unproven. Deriving the expected set from the
    spec is what makes the loop close.
    """
    deep_dive = check_manifest.locate_deep_dive(REPO_ROOT, "P0")
    manifest = check_manifest.assert_deep_dive_frozen(deep_dive)
    rows = check_manifest.parse_rows(manifest)

    specified = {
        row.artifact
        for row in rows
        if row.artifact.startswith("tools/check_") and row.artifact.endswith(".py")
    }
    registered = {checker.script for checker in CHECKERS}

    assert registered == specified, (
        "the planted-violation registry and the frozen manifest disagree.\n"
        f"  in the manifest, no fixture: {sorted(specified - registered)}\n"
        f"  fixture registered, not in the manifest: {sorted(registered - specified)}"
    )


# --------------------------------------------------------------------------
# check_manifest -- the retrofit
# --------------------------------------------------------------------------

_DEEP_DIVE = """# Deep Dive P9 — Generated fixture

## 1. Scope

Exempt front matter.

## 2. The subject under test

The section every generated row cites.

## 3. MANIFEST — frozen

```yaml
manifest_version: 1
phase: P9
frozen: {frozen}

rows:
{rows}
```
"""

_DEFERRALS = """# DEFERRALS

## Open deferrals

| ID | Phase | Manifest row | What is missing | Why | Opened | Closes by |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

---
"""

_CERTIFIER = '''"""Fixture certifier."""


def test_generated_row() -> None:
    """Named by every generated row so evidence citations resolve."""
    return None
'''


def _mini_repo(
    root: Path,
    rows: str,
    *,
    frozen: bool = True,
    sources: dict[str, str] | None = None,
) -> Path:
    """Write a minimal repo-shaped tree carrying exactly one planted defect."""
    deep_dives = root / "docs" / "deep_dives"
    deep_dives.mkdir(parents=True, exist_ok=True)
    (deep_dives / "P9_generated.md").write_text(
        _DEEP_DIVE.format(frozen="true" if frozen else "false", rows=rows),
        encoding="utf-8",
    )
    (root / "DEFERRALS.md").write_text(_DEFERRALS, encoding="utf-8")
    tests = root / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "planted_certifier.py").write_text(_CERTIFIER, encoding="utf-8")

    for relative, text in (sources or {}).items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return root


def test_manifest_rejects_missing_row() -> None:
    """The tracked planted violation: a row naming an artifact that is not there.

    This is the fixture `test_every_checker_rejects_its_fixture` drives, asserted
    here at the level of the specific failure so that the rejection is known to
    be attributable to the planted defect rather than to fixture sloppiness.
    """
    report = check_manifest.check(FIXTURE_ROOT / "manifest")

    assert not report.ok
    assert any(
        "P9.PLANTED.MISSING" in failure for failure in report.failures
    ), f"rejected, but not for the planted reason: {report.failures}"


def test_manifest_accepts_clean_tree() -> None:
    """The negative control. A checker that cannot pass certifies nothing either.

    Also the first exercise of `check_existence` against a tree where the
    artifact is present and tracked; every prior run had only ever seen absent
    artifacts, so the passing leg was unproven.
    """
    report = check_manifest.check(FIXTURE_ROOT / "manifest_clean")

    assert report.ok, f"the negative control was rejected: {report.failures}"
    assert report.rows_total == 1
    assert report.rows_built == 1


def test_manifest_rejects_uncalled_symbol(tmp_path: Path) -> None:
    """Section 6.3, DoD-(a): a primitive that exists but nothing calls is not done.

    The orphan is defined, and the manifest claims it. Nothing references it
    anywhere outside its own module, which is the orphaned-primitive failure the
    prior program's audit found by hand and this checker finds mechanically.
    """
    repo = _mini_repo(
        tmp_path,
        rows=(
            "  - id: P9.ORPHAN\n"
            "    artifact: lab.thing.orphan\n"
            "    kind: function\n"
            '    spec: "§2"\n'
            "    call_site: required\n"
            "    certifying_test: tests/planted_certifier.py::test_generated_row\n"
        ),
        sources={"src/lab/thing.py": "def orphan() -> None:\n    return None\n"},
    )

    report = check_manifest.check(repo)

    assert not report.ok
    assert any(
        "never referenced outside its own module" in f for f in report.failures
    ), f"rejected, but not for the orphaned-symbol reason: {report.failures}"


def test_manifest_rejects_unspecified_row(tmp_path: Path) -> None:
    """Section 6.4, the second direction: a row citing a section that is not there.

    Unspecified work is where the agent guesses, and an agent guessing resolves
    toward whatever is cheapest to build.
    """
    repo = _mini_repo(
        tmp_path,
        rows=(
            "  - id: P9.UNSPECIFIED\n"
            "    artifact: DEFERRALS.md\n"
            "    kind: file\n"
            '    spec: "§99"\n'
            "    call_site: n/a\n"
            "    certifying_test: tests/planted_certifier.py::test_generated_row\n"
        ),
    )

    report = check_manifest.check(repo)

    assert not report.ok
    assert any(
        "does not exist in" in f for f in report.failures
    ), f"rejected, but not for the unspecified-row reason: {report.failures}"
    assert "P9.UNSPECIFIED" in report.rows_unspecified


def test_manifest_refuses_unfrozen_deep_dive(tmp_path: Path) -> None:
    """Section 6.1 step 2: a phase cannot open against an outline.

    A refusal, not a failure. The distinction is deliberate -- the checker is
    saying it cannot grade this input, which is DoD rule 4 (fail closed on
    un-provenanced input) applied to the checker itself.
    """
    repo = _mini_repo(
        tmp_path,
        rows=(
            "  - id: P9.UNFROZEN\n"
            "    artifact: DEFERRALS.md\n"
            "    kind: file\n"
            '    spec: "§2"\n'
            "    call_site: n/a\n"
            "    certifying_test: tests/planted_certifier.py::test_generated_row\n"
        ),
        frozen=False,
    )

    with pytest.raises(check_manifest.ManifestError, match="frozen"):
        check_manifest.check(repo)


def test_manifest_frozen_check_reads_the_parsed_key_not_the_prose(tmp_path: Path) -> None:
    """A grep for the word "frozen" would pass a document that declared nothing.

    P0's own line 3 reads "Manifest frozen." in prose. The fixture below carries
    the same prose and `frozen: false`, so a textual check passes it and the
    parsed check refuses it. Recorded as a test because the two implementations
    are indistinguishable on every other input.
    """
    repo = _mini_repo(
        tmp_path,
        rows=(
            "  - id: P9.PROSE\n"
            "    artifact: DEFERRALS.md\n"
            "    kind: file\n"
            '    spec: "§2"\n'
            "    call_site: n/a\n"
            "    certifying_test: tests/planted_certifier.py::test_generated_row\n"
        ),
        frozen=False,
    )
    deep_dive = repo / "docs" / "deep_dives" / "P9_generated.md"
    deep_dive.write_text(
        "> **Status: COMPLETE. Manifest frozen.**\n\n" + deep_dive.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    assert "frozen" in deep_dive.read_text(encoding="utf-8").lower()
    with pytest.raises(check_manifest.ManifestError):
        check_manifest.assert_deep_dive_frozen(deep_dive)


# --------------------------------------------------------------------------
# check_no_stubs
# --------------------------------------------------------------------------


def _stub_findings(fixture: str) -> list[str]:
    return check_no_stubs.scan(FIXTURE_ROOT / fixture).findings


def test_stubs_rejects_bare_pass() -> None:
    """Section 7.1: a function body that is only `pass`.

    The documented variant is asserted alongside the bare one because a docstring
    does not stop a body being empty, and the polished half of a failure mode is
    the half that survives review.
    """
    findings = _stub_findings("stubs")

    assert any("bare_pass_body" in f and "`pass`" in f for f in findings), findings
    assert any("documented_pass_body" in f for f in findings), findings


def test_stubs_allows_protocol_ellipsis() -> None:
    """Section 7.2: the exemption is real, and it is narrow.

    Two assertions, because either alone is satisfiable by a broken checker. The
    clean tree proves the exemption applies; the planted tree proves it does not
    leak to a bare function or to an unrelated class that merely contains one.
    """
    assert _stub_findings("stubs_clean") == []

    findings = _stub_findings("stubs")
    assert any("bare_ellipsis_is_not_a_protocol_member" in f for f in findings), findings
    assert any("method_with_ellipsis" in f for f in findings), findings
    assert not any("def price" in f or "is_tradable" in f for f in findings), findings


def test_stubs_protocol_predicate_reads_bases_and_decorators() -> None:
    """`is_protocol_member` at the unit level, on both routes into the exemption."""
    module = ast.parse(
        "class ByBase(Protocol):\n    pass\n"
        "@runtime_checkable\n"
        "class ByDecorator:\n    pass\n"
        "class Unrelated:\n    pass\n"
    )
    classes = {node.name: node for node in module.body if isinstance(node, ast.ClassDef)}

    assert check_no_stubs.is_protocol_member(classes["ByBase"])
    assert check_no_stubs.is_protocol_member(classes["ByDecorator"])
    assert not check_no_stubs.is_protocol_member(classes["Unrelated"])
    assert not check_no_stubs.is_protocol_member(None)


def test_stubs_rejects_unregistered_marker() -> None:
    """Section 7.3: a marker naming no open row is worse than no marker.

    It carries the appearance of having been registered, which is the property
    that gets a reviewer to move on.
    """
    findings = _stub_findings("stubs")

    assert any("DEF-404" in f and "no open row" in f for f in findings), findings


def test_stubs_marker_resolves_against_an_open_deferral(tmp_path: Path) -> None:
    """The escape hatch opens when the ID is genuinely registered.

    Without this the previous test is satisfied by a resolver that always returns
    False -- which would ban mid-session checkpoints outright and, per section
    7.3, is how you *get* silent stubs.
    """
    deferrals = tmp_path / "DEFERRALS.md"
    deferrals.write_text(
        "# DEFERRALS\n\n## Open deferrals\n\n"
        "| ID | Phase | Manifest row | What is missing | Why | Opened | Closes by |\n"
        "|---|---|---|---|---|---|---|\n"
        "| DEF-001 | P9 | P9.ROW | the body | checkpoint | today | tomorrow |\n\n---\n",
        encoding="utf-8",
    )

    assert check_no_stubs.resolve_deferral_marker("DEF-001", deferrals)
    assert not check_no_stubs.resolve_deferral_marker("DEF-404", deferrals)
    assert not check_no_stubs.resolve_deferral_marker("DEF-001", tmp_path / "absent.md")


def test_stubs_rejects_not_implemented_and_deferral_language() -> None:
    """The remaining two rows of the section 7.1 table."""
    findings = _stub_findings("stubs")

    assert any("NotImplementedError" in f for f in findings), findings
    assert any("deferral language" in f for f in findings), findings


def test_stubs_refuses_to_run_on_a_tree_with_nothing_to_scan(tmp_path: Path) -> None:
    """Nothing to scan is not a clean scan.

    The same fail-closed discipline as the gate's empty registry, one level down.
    A checker pointed at the wrong directory must say so rather than report the
    silence as cleanliness.
    """
    with pytest.raises(check_no_stubs.StubCheckError):
        check_no_stubs.scan(tmp_path)


# --------------------------------------------------------------------------
# check_spec_isolation
# --------------------------------------------------------------------------


def test_spec_isolation_rejects_mixed_pr() -> None:
    """Failure case 11: a PR touching CONSTITUTION.md and src/ together."""
    report = check_spec_isolation.check(FIXTURE_ROOT / "spec_isolation")

    assert report.mixed
    assert not report.ok
    assert "CONSTITUTION.md" in report.spec
    assert "docs/deep_dives/P0_scaffold.md" in report.spec
    assert "src/lab/core/config.py" in report.code


def test_spec_isolation_allows_handoff_with_code() -> None:
    """Failure case 12, and the carve-out section 8 insists on.

    The logs are not a courtesy exemption. `HANDOFF.md` is *required* to travel
    with the code it describes, so a checker that blocks it makes the
    session-end ritual unmergeable -- and a ritual that cannot be merged stops
    being performed.
    """
    report = check_spec_isolation.check(FIXTURE_ROOT / "spec_isolation_logs")

    assert report.ok
    assert not report.mixed
    assert set(report.logs) == set(check_spec_isolation.LOG_PATHS)
    assert report.code, "the control is vacuous if it carries no code"


def test_spec_isolation_classifies_by_prefix_not_substring() -> None:
    """A fixture is not a governance document because of where it sits.

    The planted trees live at
    `tests/completeness/fixtures/*/docs/deep_dives/*.md`. Under substring
    matching every one of them classifies as SPEC, and every commit touching a
    fixture reports as a spec-and-code violation. The rule would be switched off
    within a day. Pinned as a test because the two implementations differ on
    nothing else.
    """
    report = check_spec_isolation.classify(
        [
            "tests/completeness/fixtures/manifest/docs/deep_dives/P9_planted.md",
            "docs/deep_dives/P0_scaffold.md",
        ]
    )

    assert report.code == ["tests/completeness/fixtures/manifest/docs/deep_dives/P9_planted.md"]
    assert report.spec == ["docs/deep_dives/P0_scaffold.md"]


def test_spec_isolation_bootstrap_exception_is_open_on_this_repo() -> None:
    """Section 5.4, on the real tree, where the exception is currently load-bearing.

    Session 1 predicted this exception would never have to deploy, reasoning
    that the phase branch would carry no SPEC at all. Amendments A-001 to A-003
    edited a frozen deep dive on this branch, so the diff carries SPEC and CODE
    together and the exception is doing real work. The prediction is recorded as
    falsified in DEAD_ENDS.md.
    """
    report = check_spec_isolation.check(REPO_ROOT)

    assert report.mixed, "expected the P0 branch to carry both tiers"
    assert report.exception_applies
    assert report.ok


def test_spec_isolation_bootstrap_exception_self_closes() -> None:
    """The same diff, once origin/main produces the `gate` check, is denied.

    This is the test that proves the exception is narrow rather than permanent.
    An exception somebody has to remember to switch off is a hole with a
    reminder attached; this one closes on a condition the repository reaches on
    its own, and the closing is asserted rather than asserted-about.
    """
    permitted = check_spec_isolation.check(REPO_ROOT)
    denied = check_spec_isolation.check(REPO_ROOT, assume_gate_on_main=True)

    assert permitted.ok
    assert denied.mixed
    assert not denied.ok, "the exception did not close; it is permanent, not narrow"


def test_spec_isolation_refuses_a_tree_with_no_diff_to_judge(tmp_path: Path) -> None:
    """No diff is not a clean diff."""
    with pytest.raises(check_spec_isolation.SpecIsolationError):
        check_spec_isolation.check(tmp_path)
