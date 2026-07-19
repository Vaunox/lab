#!/usr/bin/env python
"""The completeness gate. Deep dive P0 section 6.

Asserts that everything the phase specified was built, that every built symbol is
actually called, and that the spec and the manifest agree in both directions.

The correctness gate asks whether what exists behaves correctly. This asks
whether everything that should exist, exists -- which is the question every
previous project on this codebase failed to ask.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Section 6.2. The registry is closed: an unrecognised kind is a hard error,
# never a skip. A skip is the vacuous pass this tool exists to prevent, and an
# open-ended kind field is where a stub hides.
SYMBOL_KINDS = frozenset(
    {
        "function",
        "method",
        "class",
        "protocol",
        "enum",
        "constant",
        "exception",
        "contextmanager",
        "type",
    }
)
KNOWN_KINDS = SYMBOL_KINDS | {"file", "script", "infra"}

# Section 6.3, closed for the same reason the kind registry is closed. The
# call-site assertion used to run only when this field read exactly "required",
# and every other value -- including a typo like "Required", "call-site" or "na"
# -- silently disabled it. That is the vacuous pass section 6.2 closes for
# `kind`, left open one field over. `n/a` is a classification, not a bypass: the
# row still has to exist and still has to pass its certifying test.
KNOWN_CALL_SITES = frozenset({"required", "n/a"})

# Section 6.4: hardcoded and short. A configurable exempt list is a loophole with
# a config file.
#
# Matching is by PREFIX of the title, not equality. The list entry "Why" is what
# forces this: the real heading is "Why the machinery goes first". Under equality
# matching that heading, plus "MANIFEST -- frozen" and "GATE 0 -- exit", all fall
# out of the exempt set -- and sections 11 and 12 have no manifest rows, so P0
# would fail its own completeness gate.
EXEMPT_HEADING_PREFIXES = (
    "Scope",
    "Why",
    "Failure modes and edge cases",
    "Test plan",
    "MANIFEST",
    "GATE",
    "Amendment log",
)

# Depth-2 and depth-3 headings numbered "N.", "N.M" or "N.Mx" (section 9.2b).
HEADING_RE = re.compile(r"^(#{2,6})\s+(\d+(?:\.\d+[a-z]?)?)\.?\s*(.*)$")

# Only the `spec:` field is resolved, never prose. Section 3.3's body cites
# "section 12.1", which lives in MASTER_BLUEPRINT.md -- a checker that scanned
# prose for section tokens would fail on P0's own file.
SPEC_REF_RE = re.compile(r"§\s*(\d+(?:\.\d+[a-z]?)?)")

INFRA_PROBES = ("\\.git", "git.remote.origin", "github.branch_protection.main")


@dataclass(frozen=True)
class Row:
    """One manifest row."""

    id: str
    artifact: str
    kind: str
    spec: str
    call_site: str
    certifying_test: str


@dataclass
class Report:
    """Accumulated failures and the tally HANDOFF.md pastes verbatim."""

    failures: list[str] = field(default_factory=list)
    rows_total: int = 0
    rows_built: int = 0
    sections_uncovered: list[str] = field(default_factory=list)
    rows_unspecified: list[str] = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.failures.append(message)

    @property
    def ok(self) -> bool:
        return not self.failures


class ManifestError(RuntimeError):
    """The checker cannot run. Distinct from the checker finding a violation."""


# --------------------------------------------------------------------------
# Locating and parsing the deep dive
# --------------------------------------------------------------------------


def locate_deep_dive(repo: Path, phase: str | None = None) -> Path:
    """Find the active phase's deep dive.

    Section 6.1 step 2: a phase cannot open against an outline, so an absent deep
    dive is a refusal to run rather than a failure to report.
    """
    deep_dives = sorted((repo / "docs" / "deep_dives").glob("P*_*.md"))
    if not deep_dives:
        raise ManifestError("no deep dive found under docs/deep_dives/")
    if phase is not None:
        for candidate in deep_dives:
            if candidate.name.startswith(f"{phase}_"):
                return candidate
        raise ManifestError(f"no deep dive for phase {phase}")
    return deep_dives[0]


def extract_manifest_block(text: str) -> dict[str, Any]:
    """Pull the manifest YAML out of the deep dive.

    Located structurally, not by key. Section 6.1 step 3 says "extract the YAML
    `manifest:` block", but no such key exists in any frozen manifest -- P0 and
    P1 both use top-level manifest_version/phase/frozen/rows. A key lookup would
    raise on the very document it was written to read.
    """
    required = {"manifest_version", "phase", "frozen", "rows"}
    for block in re.findall(r"```yaml\n(.*?)```", text, re.DOTALL):
        try:
            parsed = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, dict) and required <= set(parsed):
            return parsed
    raise ManifestError(
        "no manifest block found: expected a fenced yaml block carrying "
        "manifest_version, phase, frozen and rows"
    )


def assert_deep_dive_frozen(deep_dive: Path) -> dict[str, Any]:
    """Refuse to run unless the deep dive declares `frozen: true`.

    Section 6.1 step 2. This is the mechanical form of "a phase cannot begin
    until its manifest is frozen"; without it the rule is prose.

    The check reads the PARSED key, never a grep for the string. P0's line 3
    contains the words "Manifest frozen" in prose, so a textual search would
    pass on a document that had never declared anything.
    """
    if not deep_dive.exists():
        raise ManifestError(f"deep dive absent: {deep_dive}")
    manifest = extract_manifest_block(deep_dive.read_text(encoding="utf-8"))
    if manifest.get("frozen") is not True:
        raise ManifestError(
            f"{deep_dive.name} does not declare `frozen: true` -- an outline is "
            "not a specification, and this phase may not open"
        )
    return manifest


def parse_rows(manifest: dict[str, Any]) -> list[Row]:
    """Convert raw manifest rows into typed rows, rejecting unknown kinds."""
    rows: list[Row] = []
    for raw in manifest.get("rows") or []:
        missing = {"id", "artifact", "kind", "spec"} - set(raw)
        if missing:
            raise ManifestError(f"manifest row missing {sorted(missing)}: {raw!r}")
        kind = str(raw["kind"])
        if kind not in KNOWN_KINDS:
            raise ManifestError(
                f"row {raw['id']}: unrecognised kind {kind!r}. The registry is "
                f"closed; known kinds are {sorted(KNOWN_KINDS)}"
            )
        call_site = str(raw.get("call_site", "n/a"))
        if call_site not in KNOWN_CALL_SITES:
            raise ManifestError(
                f"row {raw['id']}: unrecognised call_site {call_site!r}. The "
                f"registry is closed; known values are {sorted(KNOWN_CALL_SITES)}. "
                "An unrecognised value would silently disable the call-site "
                "assertion for this row"
            )
        rows.append(
            Row(
                id=str(raw["id"]),
                artifact=str(raw["artifact"]),
                kind=kind,
                spec=str(raw["spec"]),
                call_site=call_site,
                certifying_test=str(raw.get("certifying_test", "")),
            )
        )
    return rows


def parse_headings(text: str) -> list[tuple[str, str]]:
    """Return (section number, title) for every numbered heading."""
    headings: list[tuple[str, str]] = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if match:
            title = match.group(3).lstrip("-— ").strip()
            headings.append((match.group(2), title))
    return headings


def is_exempt(title: str) -> bool:
    """Front matter, not deliverables. Section 6.4."""
    return title.startswith(EXEMPT_HEADING_PREFIXES)


def integer_section(ref: str) -> str:
    """Roll a subsection reference up to its integer parent.

    Blueprint section 10.3 pins coverage granularity at integer sections. P0
    leaves 4.1, 4.5, 5.4, 6.2, 7.1 and 9.3 rowless by design, and a rule no
    frozen manifest can satisfy is a rule that gets turned off.
    """
    return ref.split(".")[0]


# --------------------------------------------------------------------------
# Existence, by kind
# --------------------------------------------------------------------------


def _tracked_files(repo: Path) -> set[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _index_mode(repo: Path, relative: str) -> str | None:
    """Read a path's mode from the git index.

    Section 6.2 requires a script to be executable. That bit is read from the
    index, not the filesystem: os.access(p, os.X_OK) returns true for every
    readable file on Windows, which would make the check vacuous on one leg of
    the section 5.2 matrix. The index mode is platform-independent and is what a
    fresh Linux clone actually receives.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-s", "--", relative],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout.split()[0]


def module_path(repo: Path, dotted: str) -> Path | None:
    """Map a dotted prefix onto the file that should define it."""
    parts = dotted.split(".")
    for depth in range(len(parts) - 1, 0, -1):
        stem = Path(*parts[:depth])
        for candidate in (repo / "src" / stem, repo / stem):
            module = candidate.with_suffix(".py")
            if module.exists():
                return module
            if (candidate / "__init__.py").exists():
                return candidate / "__init__.py"
    return None


def defines_symbol(module: Path, symbol: str) -> bool:
    """Resolve a symbol by AST walk, never by import.

    Section 6.2: importing runs module-level code, which means a checker that can
    be made to pass by writing a clever __getattr__. AST inspection sees what is
    written, which is what the manifest is a claim about.
    """
    try:
        tree = ast.parse(module.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
            and node.name == symbol
        ):
            return True
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == symbol
        ):
            return True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    return True
    return False


def check_existence(repo: Path, row: Row, report: Report) -> bool:
    """Assert the row's artifact exists, dispatching on kind."""
    tracked = _tracked_files(repo)
    if row.kind in SYMBOL_KINDS:
        module = module_path(repo, row.artifact)
        if module is None:
            report.fail(f"{row.id}: no module found for {row.artifact}")
            return False
        symbol = row.artifact.rsplit(".", 1)[-1]
        if not defines_symbol(module, symbol):
            report.fail(f"{row.id}: {module}: does not define {symbol}")
            return False
        return True

    if row.kind == "script":
        target = repo / row.artifact
        if not target.exists():
            report.fail(f"{row.id}: missing script {row.artifact}")
            return False
        mode = _index_mode(repo, row.artifact)
        if mode is None:
            report.fail(f"{row.id}: {row.artifact} is not tracked by git")
            return False
        if mode != "100755":
            report.fail(
                f"{row.id}: {row.artifact} has index mode {mode}, expected 100755 "
                "(section 6.2 requires a script to be executable)"
            )
            return False
        return True

    if row.kind == "file":
        artifact = row.artifact.rstrip("/")
        target = repo / artifact
        if row.artifact.endswith("/"):
            beneath = [p for p in tracked if p.startswith(f"{artifact}/")]
            if not beneath:
                report.fail(
                    f"{row.id}: {row.artifact} contains no tracked file. An empty "
                    "fixtures directory is the vacuous pass section 2.2 forbids"
                )
                return False
            return True
        if not target.exists():
            report.fail(f"{row.id}: missing file {row.artifact}")
            return False
        if artifact not in tracked:
            report.fail(
                f"{row.id}: {row.artifact} exists but is not tracked by git -- it "
                "would be absent from a fresh clone"
            )
            return False
        if target.stat().st_size == 0:
            report.fail(f"{row.id}: {row.artifact} is empty")
            return False
        return True

    return check_infra(repo, row, report)


def check_infra(repo: Path, row: Row, report: Report) -> bool:
    """Probe the three bootstrap invariants. Closed registry; unknown is fatal.

    The branch-protection row is deliberately NOT probed against the GitHub API.
    Section 3.3 is explicit that verifying it needs an admin-scoped token, and
    putting an admin-scoped token in CI to check that admins are restricted is a
    circle not worth closing. Its evidence is the piped response in HANDOFF.md,
    validated through the certifying_test field instead.
    """
    if row.artifact == ".git":
        inside = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        if inside.returncode != 0:
            report.fail(f"{row.id}: not a git repository")
            return False
        hooks = subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "core.hooksPath"],
            capture_output=True,
            text=True,
            check=False,
        )
        if hooks.stdout.strip() != ".githooks":
            report.fail(
                f"{row.id}: core.hooksPath is {hooks.stdout.strip()!r}, expected "
                "'.githooks' (section 3.1)"
            )
            return False
        return True

    if row.artifact == "git.remote.origin":
        remote = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        url = remote.stdout.strip()
        if remote.returncode != 0 or "github.com" not in url:
            report.fail(f"{row.id}: origin is not a github.com remote: {url!r}")
            return False
        if not url.rstrip("/").removesuffix(".git").endswith("/lab"):
            report.fail(f"{row.id}: origin does not point at a repo named 'lab': {url!r}")
            return False
        return True

    if row.artifact == "github.branch_protection.main":
        return True

    report.fail(f"{row.id}: unrecognised infra artifact {row.artifact!r}")
    return False


# --------------------------------------------------------------------------
# Call sites
# --------------------------------------------------------------------------


def _python_files(repo: Path, exclude: Iterable[Path] = ()) -> Iterator[Path]:
    excluded = {p.resolve() for p in exclude}
    for root in ("src", "tools", "tests"):
        base = repo / root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "fixtures" in path.parts:
                continue
            if path.resolve() not in excluded:
                yield path


def assert_called_outside_own_module(repo: Path, row: Row, report: Report) -> bool:
    """Assert the row's symbol is referenced outside its own module and test.

    Section 6.3. This is DoD-(a) mechanised: a primitive that exists but nothing
    calls is not done. It was a PR-checklist item on the previous program, and a
    checklist item is a thing an agent ticks.

    For a `script` row the analogue of an AST reference is an invocation edge --
    a subprocess call, a workflow `run:` step, or a pre-commit `entry:`. Prose,
    comments and markdown are never edges: the cheap reading, "the path appears
    somewhere in another file", is satisfied by a sentence in a README.
    """
    own_test = repo / row.certifying_test.split("::")[0] if row.certifying_test else None
    exclude = [p for p in (own_test,) if p is not None]

    if row.kind == "script":
        exclude.append(repo / row.artifact)
        if _find_script_invocation(repo, row.artifact, exclude) is None:
            report.fail(
                f"{row.id}: nothing invokes {row.artifact}. Definition is not use " "(section 6.3)"
            )
            return False
        return True

    module = module_path(repo, row.artifact)
    if module is not None:
        exclude.append(module)
    symbol = row.artifact.rsplit(".", 1)[-1]
    for path in _python_files(repo, exclude):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == symbol:
                return True
            if isinstance(node, ast.Attribute) and node.attr == symbol:
                return True
    report.fail(
        f"{row.id}: {row.artifact} is never referenced outside its own module and "
        "certifying test. Definition is not use (section 6.3)"
    )
    return False


def _find_script_invocation(repo: Path, artifact: str, exclude: Iterable[Path]) -> str | None:
    """Locate an executable invocation edge for a script path."""
    excluded = {p.resolve() for p in exclude}
    dotted = artifact.removesuffix(".py").replace("/", ".")
    # tools/ is a scripts directory, not a package, so a sibling importing it
    # writes `import check_manifest` rather than `import tools.check_manifest`.
    # Both name the same file and both are real invocation edges.
    bare = dotted.rsplit(".", 1)[-1]
    module_names = {dotted, bare}

    for path in _python_files(repo, excluded):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == artifact:
                return str(path)
            if isinstance(node, ast.ImportFrom) and node.module in module_names:
                return str(path)
            if isinstance(node, ast.Import) and any(
                alias.name in module_names for alias in node.names
            ):
                return str(path)

    workflows = repo / ".github" / "workflows"
    for path in sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml")):
        if path.resolve() in excluded:
            continue
        if _yaml_mentions_in_run(path, artifact):
            return str(path)

    precommit = repo / ".pre-commit-config.yaml"
    if (
        precommit.exists()
        and precommit.resolve() not in excluded
        and _precommit_entry_mentions(precommit, artifact)
    ):
        return str(precommit)

    hooks = repo / ".githooks"
    if hooks.exists():
        for path in hooks.iterdir():
            if path.is_file() and artifact in path.read_text(encoding="utf-8"):
                return str(path)
    return None


def _yaml_mentions_in_run(path: Path, artifact: str) -> bool:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return False
    for job in (document or {}).get("jobs", {}).values():
        for step in job.get("steps", []) or []:
            if artifact in str(step.get("run", "")):
                return True
    return False


def _precommit_entry_mentions(path: Path, artifact: str) -> bool:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return False
    for repo_block in (document or {}).get("repos", []) or []:
        for hook in repo_block.get("hooks", []) or []:
            if artifact in str(hook.get("entry", "")):
                return True
    return False


# --------------------------------------------------------------------------
# The closed loop
# --------------------------------------------------------------------------


def assert_closed_loop(rows: list[Row], deep_dive: Path, report: Report) -> bool:
    """Verify spec and manifest agree in both directions. Section 6.4.

    A heading with no row is unbuilt spec: something was specified and nothing
    was built. A row with no heading is unspecified work -- and unspecified work
    is where the agent guesses, which is where it minimises.

    Exemption applies to the heading direction only. A row may legally cite INTO
    an exempt section: P0.FIXTURES.VIOLATIONS cites section 2.2, which lives
    under the exempt "Why the machinery goes first".
    """
    headings = parse_headings(deep_dive.read_text(encoding="utf-8"))
    known = {number for number, _ in headings}
    covered: set[str] = set()
    ok = True

    for row in rows:
        match = SPEC_REF_RE.search(row.spec)
        if match is None:
            report.fail(f"{row.id}: spec field {row.spec!r} names no section")
            report.rows_unspecified.append(row.id)
            ok = False
            continue
        ref = match.group(1)
        if ref not in known:
            report.fail(f"{row.id}: cites section {ref}, which does not exist in {deep_dive.name}")
            report.rows_unspecified.append(row.id)
            ok = False
            continue
        covered.add(integer_section(ref))

    for number, title in headings:
        if "." in number or is_exempt(title):
            continue
        if number not in covered:
            report.fail(f"section {number} ({title}) has no manifest row -- unbuilt spec")
            report.sections_uncovered.append(f"{number} {title}")
            ok = False
    return ok


# --------------------------------------------------------------------------
# Certifying tests and deferrals
# --------------------------------------------------------------------------


def check_certifying_test(repo: Path, row: Row, report: Report) -> bool:
    """Validate the row's evidence citation. Two dialects; a third is fatal.

    A `.py::name` reference is a pytest node id and is resolved by AST -- not by
    pytest collection, which executes conftest.py, the same objection section 6.2
    raises against importlib.

    A `.md::name` reference is a documentary citation, and it exists because the
    branch-protection row cannot be machine-verified without an admin token
    (section 3.3). Validating the pasted evidence is how that row escapes being
    vacuous: section 12.1 mechanised, typed status is a claim and piped status is
    evidence.
    """
    if not row.certifying_test:
        report.fail(f"{row.id}: no certifying_test")
        return False
    path_part, _, name = row.certifying_test.partition("::")
    target = repo / path_part
    if not target.exists():
        report.fail(f"{row.id}: certifying_test file {path_part} does not exist")
        return False

    if path_part.endswith(".py"):
        if not defines_symbol(target, name):
            report.fail(f"{row.id}: {path_part} does not define {name}")
            return False
        return True

    if path_part.endswith(".md"):
        return _check_evidence_block(target, name, row, report)

    report.fail(
        f"{row.id}: certifying_test {row.certifying_test!r} is neither a .py node "
        "id nor a .md evidence citation"
    )
    return False


def _check_evidence_block(document: Path, anchor: str, row: Row, report: Report) -> bool:
    text = document.read_text(encoding="utf-8")
    marker = f"<!-- {anchor} -->"
    if marker not in text:
        report.fail(f"{row.id}: {document.name} has no evidence block anchored {marker}")
        return False
    after = text.split(marker, 1)[1]
    blocks = re.findall(r"```json\n(.*?)```", after, re.DOTALL)
    if not blocks:
        report.fail(f"{row.id}: no json block follows {marker} in {document.name}")
        return False
    try:
        protection = json.loads(blocks[0])
    except json.JSONDecodeError as exc:
        report.fail(f"{row.id}: evidence block is not valid JSON: {exc}")
        return False

    checks = {
        "required_status_checks.strict": protection.get("required_status_checks", {}).get("strict")
        is True,
        "required_status_checks contains 'gate'": "gate"
        in (protection.get("required_status_checks", {}).get("contexts") or []),
        "enforce_admins": protection.get("enforce_admins", {}).get("enabled") is True,
        "required_linear_history": protection.get("required_linear_history", {}).get("enabled")
        is True,
        "allow_force_pushes disabled": protection.get("allow_force_pushes", {}).get("enabled")
        is False,
        "allow_deletions disabled": protection.get("allow_deletions", {}).get("enabled") is False,
    }
    unmet = [name for name, held in checks.items() if not held]
    if unmet:
        report.fail(f"{row.id}: pasted protection evidence fails: {', '.join(unmet)}")
        return False
    return True


def assert_deferrals_empty(repo: Path, report: Report) -> bool:
    """Section 6.1 step 7: a phase does not merge with an open deferral."""
    deferrals = repo / "DEFERRALS.md"
    if not deferrals.exists():
        report.fail("DEFERRALS.md is missing")
        return False
    text = deferrals.read_text(encoding="utf-8")
    section = text.split("## Open deferrals", 1)
    if len(section) < 2:
        report.fail("DEFERRALS.md has no 'Open deferrals' section")
        return False
    body = section[1].split("\n---", 1)[0]
    open_rows = [
        line
        for line in body.splitlines()
        if line.strip().startswith("|")
        and not re.match(r"^\|[\s|:-]+\|$", line.strip())
        and "ID" not in line
        and not re.match(r"^\|\s*[-—]\s*\|", line.strip())
    ]
    if open_rows:
        report.fail(f"DEFERRALS.md has {len(open_rows)} open deferral(s); must be empty to merge")
        return False
    return True


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def check(repo: Path, phase: str | None = None) -> Report:
    """Run every manifest assertion and return the accumulated report."""
    report = Report()
    deep_dive = locate_deep_dive(repo, phase)
    manifest = assert_deep_dive_frozen(deep_dive)
    rows = parse_rows(manifest)
    report.rows_total = len(rows)

    for row in rows:
        built = check_existence(repo, row, report)
        if built:
            report.rows_built += 1
        check_certifying_test(repo, row, report)
        if row.call_site == "required":
            assert_called_outside_own_module(repo, row, report)

    assert_closed_loop(rows, deep_dive, report)
    assert_deferrals_empty(repo, report)
    return report


def format_tally(report: Report, phase: str) -> str:
    """The tally HANDOFF.md pastes verbatim. Never hand-counted."""
    lines = [
        f"phase:                        {phase}",
        f"rows total:                   {report.rows_total}",
        f"rows built:                   {report.rows_built}",
        f"rows open:                    {report.rows_total - report.rows_built}",
        f"spec sections without a row:  {len(report.sections_uncovered)}",
        f"rows without a spec section:  {len(report.rows_unspecified)}",
        f"failures:                     {len(report.failures)}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Completeness gate (deep dive P0 section 6).")
    # --root is the uniform contract every checker honours, so that one test can
    # drive all seven against their planted violations (section 2.2).
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--phase", default=None)
    args = parser.parse_args(argv)

    try:
        report = check(args.root, args.phase)
    except ManifestError as exc:
        print(f"check_manifest: REFUSED TO RUN: {exc}", file=sys.stderr)
        return 2

    deep_dive = locate_deep_dive(args.root, args.phase)
    phase = deep_dive.name.split("_", 1)[0]
    print(format_tally(report, phase))
    if report.failures:
        print()
        for failure in report.failures:
            print(f"  FAIL  {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
