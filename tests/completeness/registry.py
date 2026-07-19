"""The seven checkers, their planted violations, and how to drive them.

Deep dive P0 section 2.2. Every checker ships with a deliberately broken tree and
a test proving the checker rejects it, because *a checker that always passes is
worse than no checker* -- it manufactures confidence.

The registry is closed and its membership is not this file's opinion. Section 11
of the frozen deep dive enumerates the checker scripts, and
`test_checker_registry_matches_manifest` asserts this tuple equals that
enumeration. Adding a checker to the manifest therefore forces a fixture to exist
for it; the registry cannot quietly shrink to the set of checkers that happen to
have been written.

**Uniform invocation contract.** Every checker accepts `--root DIR` and treats
that directory as the tree under judgement, exiting non-zero on a violation. That
uniformity is what lets one test drive all seven. The checkers whose real input
comes from git (spec isolation, attribution, fixture provenance, substrate
purity) read it from the fixture tree instead when `--root` points somewhere
other than the repository, which is what makes them testable at all -- a
git-derived checker with no injection seam can only be tested by building throw-
away repositories, and a fixture that cannot be committed cannot be reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parent.parent
FIXTURE_ROOT = TESTS_ROOT / "fixtures"


@dataclass(frozen=True)
class Checker:
    """One checker, its planted violation, and the gate stage it backs."""

    stage: str
    script: str
    fixture: str

    @property
    def script_path(self) -> Path:
        return REPO_ROOT / self.script

    @property
    def fixture_path(self) -> Path:
        return FIXTURE_ROOT / self.fixture


# Ordered as tools/gate.py runs them (section 5.1), so a reader comparing the two
# lists is comparing like with like.
CHECKERS: tuple[Checker, ...] = (
    Checker("manifest", "tools/check_manifest.py", "manifest"),
    Checker("stubs", "tools/check_no_stubs.py", "stubs"),
    Checker("spec-isolation", "tools/check_spec_isolation.py", "spec_isolation"),
    Checker("imports", "tools/check_import_graph.py", "imports"),
    Checker("attribution", "tools/check_attribution.py", "attribution"),
    Checker("fixtures", "tools/check_fixture_provenance.py", "fixture_provenance"),
    Checker("substrate-purity", "tools/check_substrate_purity.py", "substrate_purity"),
)
