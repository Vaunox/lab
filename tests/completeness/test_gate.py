"""The gate's own certifying tests. Deep dive P0 section 5.1.

The property that matters here is negative and easy to lose: the gate must
refuse to report success when it has been given nothing to do. During P0, while
the checkers are still being written, that refusal is the entire difference
between a bootstrap and a bypass -- an empty registry is the one input on which
a green result is indistinguishable from a working gate.
"""

from __future__ import annotations

from pathlib import Path

import gate
import pytest

# Section 5.1 enumerates the stage order exhaustively. Pinned here so that
# dropping a stage is a test failure rather than a quiet reduction in scope.
EXPECTED_STAGE_ORDER = (
    "lint",
    "types",
    "tests",
    "manifest",
    "stubs",
    "spec-isolation",
    "imports",
    "attribution",
    "fixtures",
    "substrate-purity",
)


def test_gate_fails_closed_on_zero_checkers(tmp_path: Path) -> None:
    """ "Nothing to check" is not "all checks passed". Section 5.1.

    Raising rather than returning non-zero is deliberate: a return code is a
    verdict on the tree, and the gate has no verdict to give here. It is
    reporting that it was not able to grade at all, which is DoD rule 4 -- fail
    closed on absent input, never grade a placeholder as real.
    """
    with pytest.raises(gate.EmptyRegistryError):
        gate.run_gate(tmp_path, [])


def test_gate_cli_exits_non_zero_on_an_empty_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The refusal survives the trip through main() and reaches the shell.

    An exception caught and swallowed into `return 0` would satisfy the test
    above and still ship a gate that passes on nothing.
    """
    monkeypatch.setattr(gate, "STAGES", [])

    assert gate.main(["--root", str(tmp_path)]) != 0


def test_gate_reports_red_when_a_stage_fails(tmp_path: Path) -> None:
    """A failing stage is reported, named, and returns non-zero."""
    stages = [
        gate.Stage("passes", lambda _root: True),
        gate.Stage("fails", lambda _root: False),
    ]

    assert gate.run_gate(tmp_path, stages) == 1


def test_gate_reports_green_only_when_every_stage_passes(tmp_path: Path) -> None:
    """The positive control: the gate is not merely always red."""
    stages = [
        gate.Stage("passes", lambda _root: True),
        gate.Stage("also-passes", lambda _root: True),
    ]

    assert gate.run_gate(tmp_path, stages) == 0


def test_gate_registers_every_stage_section_5_1_names() -> None:
    """The registered stages are section 5.1's list, in section 5.1's order.

    Mutation testing does not reach `STAGES` -- it is data, not logic -- so the
    only thing standing between a quietly deleted stage and a green gate is an
    assertion that names them all.
    """
    assert tuple(stage.name for stage in gate.STAGES) == EXPECTED_STAGE_ORDER


def test_gate_treats_a_missing_checker_as_a_failure(tmp_path: Path) -> None:
    """An absent checker script fails its stage. It is never skipped.

    A skip would report green for machinery that does not exist, which is the
    same vacuous pass as an empty registry, arriving one level down.
    """
    stage = gate._script_stage("tools/check_does_not_exist.py")

    assert stage(tmp_path) is False
