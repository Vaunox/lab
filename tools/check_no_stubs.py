#!/usr/bin/env python
"""No stubs, mechanically. Deep dive P0 section 7.

Blunt by design, and it will occasionally be annoying. That is the intent: every
pattern below is the textual signature of a deferral, and *a deferral that cannot
be written down cannot be made silently*.

Scope is `src/lab/` and `tools/` (section 7.1). The checkers are src-equivalent
and check themselves -- failure case 14 -- so this file is inside its own
jurisdiction, which is why its banned words are assembled at import rather than
written as literals. See `_assemble`.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

SCAN_ROOTS = ("src/lab", "tools")


def _assemble(*parts: str) -> str:
    """Build a banned token at runtime so this file does not contain it.

    This checker scans `tools/`, and it lives in `tools/`. Spelling the markers
    as literals would make the tool a violation of its own rule, and the obvious
    escape -- excluding the checker from its own scan -- is a hole in the one
    place a hole must not be. DE-000l records the same self-reference defeating
    an earlier attempt to grep contents for vendor names; the lesson taken there
    was to narrow the scope rather than to bolt on exclusions, and the same
    lesson applies here.
    """
    return "".join(parts)


# Section 7.1, row 1: in comments and in string literals.
MARKER_WORDS: tuple[str, ...] = (
    _assemble("TO", "DO"),
    _assemble("FIX", "ME"),
    _assemble("XX", "X"),
    _assemble("HA", "CK"),
)

# Section 7.1, final row: deferral language in a docstring.
DEFERRAL_PHRASES: tuple[str, ...] = (
    _assemble("for ", "now"),
    _assemble("la", "ter"),
    _assemble("tempo", "rary"),
    _assemble("place", "holder"),
    _assemble("simpli", "fied"),
    _assemble("not ", "implemented"),
)

# Section 7.3. The one escape hatch, and it is loud.
STUB_MARKER_RE = re.compile(r"#\s*STUB:\s*(DEF-\d+)")

PROTOCOL_BASES = frozenset({"Protocol", "typing.Protocol"})
RUNTIME_CHECKABLE = frozenset({"runtime_checkable", "typing.runtime_checkable"})

SKIP_DECORATORS = frozenset(
    {
        "pytest.mark.skip",
        "pytest.mark.xfail",
        "mark.skip",
        "mark.xfail",
    }
)


@dataclass
class Report:
    """Accumulated findings. Empty is the only passing state."""

    findings: list[str] = field(default_factory=list)
    files_scanned: int = 0

    def fail(self, path: Path, line: int, message: str) -> None:
        self.findings.append(f"{path}:{line}: {message}")

    @property
    def ok(self) -> bool:
        return not self.findings


class StubCheckError(RuntimeError):
    """The checker cannot run. Distinct from the checker finding a violation."""


def dotted_name(node: ast.expr) -> str:
    """Render a dotted attribute or name node back to source form."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{dotted_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return dotted_name(node.value)
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return ""


def is_protocol_member(enclosing: ast.ClassDef | None) -> bool:
    """Whether an `...` body is legal here. Section 7.2, and it is a real case.

    A Protocol member's body *is* `...` by language convention. Flagging it would
    make this checker useless, and a useless checker gets turned off inside a
    day -- at which point every other rule it enforces goes with it.

    Legal iff the enclosing class inherits `Protocol` or is decorated
    `@runtime_checkable`. A bare function is never a Protocol member, so an
    absent enclosing class is False rather than lenient: the fixture tree carries
    both shapes precisely because a checker that cannot tell them apart is not
    shipped.
    """
    if enclosing is None:
        return False
    for base in enclosing.bases:
        if dotted_name(base) in PROTOCOL_BASES:
            return True
    for decorator in enclosing.decorator_list:
        if dotted_name(decorator) in RUNTIME_CHECKABLE:
            return True
    return False


def resolve_deferral_marker(marker_id: str, deferrals: Path) -> bool:
    """Whether a `# STUB: DEF-nnn` marker resolves to an open deferral row.

    Section 7.3. The marker is what makes a mid-session stub legal and *visible*;
    this function is what stops it becoming a way to ship one. An ID that names
    no open row is worse than no marker at all, because it carries the appearance
    of having been registered.

    Merge-time stubs remain impossible regardless of what this returns:
    `DEFERRALS.md` must be empty to merge (section 6.1 step 7), so an ID that
    resolves here blocks the merge one gate over. The escape hatch checkpoints;
    it cannot ship.
    """
    if not deferrals.exists():
        return False
    text = deferrals.read_text(encoding="utf-8")
    section = text.split("## Open deferrals", 1)
    if len(section) < 2:
        return False
    body = section[1].split("\n---", 1)[0]
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0] == marker_id:
            return True
    return False


def _comment_lines(source: str) -> dict[int, str]:
    """Map line number to comment text. Tokenised, never regexed off raw source.

    A regex over raw text cannot tell a `#` inside a string literal from a real
    comment, and the difference decides whether this file's own STUB_MARKER_RE
    counts as a finding.
    """
    comments: dict[int, str] = {}
    try:
        tokens = tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                comments[token.start[0]] = token.string
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return comments
    return comments


def _body_is_only(body: list[ast.stmt], statement: type[ast.stmt]) -> bool:
    """Whether a body consists of a docstring and nothing but the given statement.

    A docstring does not stop a body being empty. `def f(): "explains itself"; pass`
    is the same absence of code as a bare `pass`, dressed better, and reading the
    spec's *"body is only pass"* to exclude it would exempt the more polished half
    of the failure mode.
    """
    meaningful = list(body)
    if (
        meaningful
        and isinstance(meaningful[0], ast.Expr)
        and isinstance(meaningful[0].value, ast.Constant)
        and isinstance(meaningful[0].value.value, str)
    ):
        meaningful = meaningful[1:]
    if not meaningful:
        return statement is ast.Pass
    return all(isinstance(node, statement) for node in meaningful)


def _is_ellipsis_body(body: list[ast.stmt]) -> bool:
    meaningful = list(body)
    if (
        len(meaningful) > 1
        and isinstance(meaningful[0], ast.Expr)
        and isinstance(meaningful[0].value, ast.Constant)
        and isinstance(meaningful[0].value.value, str)
    ):
        meaningful = meaningful[1:]
    return len(meaningful) == 1 and (
        isinstance(meaningful[0], ast.Expr)
        and isinstance(meaningful[0].value, ast.Constant)
        and meaningful[0].value.value is Ellipsis
    )


class _Scanner(ast.NodeVisitor):
    """Walks one module, tracking the enclosing class for the Protocol rule."""

    def __init__(self, path: Path, comments: dict[int, str], deferrals: Path, report: Report):
        self.path = path
        self.comments = comments
        self.deferrals = deferrals
        self.report = report
        # `None` marks a function scope. A nested function is not a member of the
        # class that encloses its parent, so the Protocol exemption must not leak
        # down into it -- otherwise `...` becomes legal anywhere inside a
        # Protocol, which is most of the exemption's blast radius.
        self.class_stack: list[ast.ClassDef | None] = []

    # -- helpers ---------------------------------------------------------

    def _marker_for(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
        end = node.end_lineno or node.lineno
        for line in range(node.lineno, end + 1):
            match = STUB_MARKER_RE.search(self.comments.get(line, ""))
            if match:
                return match.group(1)
        return None

    def _check_stub_body(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        enclosing = self.class_stack[-1] if self.class_stack else None
        is_pass = _body_is_only(node.body, ast.Pass)
        is_ellipsis = _is_ellipsis_body(node.body)

        if is_ellipsis and is_protocol_member(enclosing):
            return
        if not (is_pass or is_ellipsis):
            return

        shape = "pass" if is_pass else "..."
        marker = self._marker_for(node)
        if marker is None:
            self.report.fail(
                self.path,
                node.lineno,
                f"{node.name}: body is only `{shape}`. Unfinished work is absent "
                "code, not stubbed code (section 7.3). If this is a mid-session "
                "checkpoint, mark it `# STUB: DEF-nnn` against an open deferral",
            )
            return
        if not resolve_deferral_marker(marker, self.deferrals):
            self.report.fail(
                self.path,
                node.lineno,
                f"{node.name}: marker {marker} names no open row in "
                "DEFERRALS.md. An ID that resolves to nothing is worse than no "
                "marker, because it looks registered",
            )

    def _check_skip_decorators(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            name = dotted_name(decorator)
            if name not in SKIP_DECORATORS:
                continue
            self.report.fail(
                self.path,
                decorator.lineno,
                f"{node.name}: @{name} must cite a DIVERGENCES.md entry, and "
                "DIVERGENCES.md defines no citable ID, so no skip can currently "
                "be justified. Fail-closed pending an operator ruling -- see "
                "Q-002 in PROJECT_STATE.md, 'Blocked / needs a decision'. Note "
                "that this rule is INERT where it matters: SCAN_ROOTS excludes "
                "tests/, so a skip in a test is never seen. Q-002 owns that too",
            )

    def _check_docstring(self, node: ast.AST) -> None:
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            return
        docstring = ast.get_docstring(node)
        if not docstring:
            return
        lowered = docstring.lower()
        for phrase in DEFERRAL_PHRASES:
            if phrase in lowered:
                line = getattr(node, "lineno", 1)
                self.report.fail(
                    self.path,
                    line,
                    f"docstring contains deferral language {phrase!r} (section 7.1)",
                )

    # -- visitors --------------------------------------------------------

    def visit_Module(self, node: ast.Module) -> None:
        self._check_docstring(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_docstring(node)
        self.class_stack.append(node)
        self.generic_visit(node)
        self.class_stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._check_docstring(node)
        self._check_stub_body(node)
        self._check_skip_decorators(node)
        self.class_stack.append(None)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is not None and dotted_name(node.exc) == "NotImplementedError":
            self.report.fail(
                self.path,
                node.lineno,
                "raises NotImplementedError (section 7.1)",
            )
        self.generic_visit(node)


def scan_file(path: Path, deferrals: Path, report: Report) -> None:
    """Scan one module for every section 7.1 pattern."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.fail(path, exc.lineno or 1, f"cannot parse: {exc.msg}")
        return

    comments = _comment_lines(source)
    scanner = _Scanner(path, comments, deferrals, report)
    scanner.visit(tree)

    for line, text in comments.items():
        for word in MARKER_WORDS:
            if word in text:
                report.fail(path, line, f"comment contains {word} (section 7.1)")

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for word in MARKER_WORDS:
                if word in node.value:
                    report.fail(path, node.lineno, f"string literal contains {word}")

    report.files_scanned += 1


def scan(root: Path) -> Report:
    """Scan `src/lab/` and `tools/`, refusing a vacuous pass on an empty tree."""
    report = Report()
    deferrals = root / "DEFERRALS.md"

    present = [root / part for part in SCAN_ROOTS if (root / part).is_dir()]
    if not present:
        raise StubCheckError(
            f"neither {' nor '.join(SCAN_ROOTS)} exists under {root} -- nothing "
            "to scan is not a clean scan"
        )

    for base in present:
        for path in sorted(base.rglob("*.py")):
            scan_file(path, deferrals, report)

    if report.files_scanned == 0:
        raise StubCheckError(f"no python files found under {root} -- refusing a vacuous pass")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="No stubs (deep dive P0 section 7).")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)

    try:
        report = scan(args.root)
    except StubCheckError as exc:
        print(f"check_no_stubs: REFUSED TO RUN: {exc}", file=sys.stderr)
        return 2

    if report.findings:
        for finding in report.findings:
            print(f"  FAIL  {finding}", file=sys.stderr)
        print(f"check_no_stubs: {len(report.findings)} finding(s)", file=sys.stderr)
        return 1
    print(f"check_no_stubs: clean over {report.files_scanned} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
