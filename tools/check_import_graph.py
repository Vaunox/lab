#!/usr/bin/env python
"""Substrate boundaries, as data. Deep dive P0 section 9.1.

The architectural rules -- *nothing outside `costs/` computes a cost*, *only the
ledger may mint a result* -- are checked by AST rather than by review, because a
boundary maintained by review is a boundary maintained by whoever is least tired.

**Every rule carries its `reason`, and the checker prints it on failure.** A
violation message reading only "import rule violated" teaches the next agent
nothing, and an agent taught nothing routes around the obstacle. A message
reading *"the engine cannot mint a result"* teaches it the invariant, and an
agent that has learned the invariant stops trying to break it.

The rules file is empty of `lab.*` rules in P0 -- there is no `lab` code yet --
but the tool ships and is tested against a fixture tree. That is the pattern for
the whole phase: the machinery is complete, and the rules arrive with the code
they police.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULES = "tools/import_rules.yaml"


@dataclass(frozen=True)
class Violation:
    """One breach, carrying the rule's reason so the message can teach."""

    path: Path
    line: int
    message: str
    reason: str

    def render(self) -> str:
        return f"  FAIL  {self.path}:{self.line}: {self.message}\n        reason: {self.reason}"


@dataclass
class Report:
    violations: list[Violation] = field(default_factory=list)
    rules_applied: int = 0
    modules_scanned: int = 0

    @property
    def ok(self) -> bool:
        return not self.violations


class ImportRuleError(RuntimeError):
    """The checker cannot run, or a rule is malformed. Never a silent skip."""


def module_name(path: Path, source_root: Path) -> str:
    """Dotted module name for a file beneath `src/`."""
    relative = path.relative_to(source_root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def matches(module: str, patterns: list[str]) -> bool:
    """Whether a module falls inside any of the allowed patterns.

    `lab.ledger.*` admits `lab.ledger.chain` and also `lab.ledger` itself. A
    package is inside its own boundary, and reading the pattern strictly would
    forbid `lab/ledger/__init__.py` from touching the very symbol the ledger
    exists to own -- a rule whose first violation is the rule's own author.
    """
    for pattern in patterns:
        if fnmatch.fnmatch(module, pattern):
            return True
        if pattern.endswith(".*") and module == pattern[:-2]:
            return True
    return False


def load_rules(path: Path) -> list[dict[str, Any]]:
    """Read the rules file, rejecting any rule that does not carry a reason.

    A rule with no reason is a hard error rather than a rule enforced quietly.
    The reason is not documentation attached to the rule; it is half of what the
    rule does, because the message is the only part of this tool the next agent
    will ever read.
    """
    if not path.exists():
        raise ImportRuleError(f"rules file not found: {path}")

    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if document is None:
        document = []
    if not isinstance(document, list):
        raise ImportRuleError(f"{path}: expected a top-level list of rules, got {type(document)}")

    for index, rule in enumerate(document):
        if not isinstance(rule, dict):
            raise ImportRuleError(f"{path}: rule {index} is not a mapping")
        if not str(rule.get("reason", "")).strip():
            raise ImportRuleError(
                f"{path}: rule {index} ({rule!r}) carries no `reason`. Section 9.1 "
                "requires one, and the checker prints it on failure -- a rule "
                "that cannot explain itself will be routed around"
            )
        has_symbol = "symbol" in rule and "constructed_only_in" in rule
        has_module = "module" in rule and "imported_only_by" in rule
        if not (has_symbol or has_module):
            raise ImportRuleError(
                f"{path}: rule {index} ({rule!r}) is neither a "
                "symbol/constructed_only_in nor a module/imported_only_by rule. "
                "The rule registry is closed; an unrecognised shape is a hard "
                "error, never a skip"
            )
    return document


def _called_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _imported_modules(tree: ast.AST) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.module, node.lineno))
            found.extend((f"{node.module}.{alias.name}", node.lineno) for alias in node.names)
    return found


def check_module(
    path: Path,
    source_root: Path,
    rules: list[dict[str, Any]],
    report: Report,
) -> None:
    """Apply every rule to one module."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return

    dotted = module_name(path, source_root)
    report.modules_scanned += 1

    for rule in rules:
        reason = str(rule["reason"])

        if "symbol" in rule and "constructed_only_in" in rule:
            symbol = str(rule["symbol"])
            allowed = [str(p) for p in rule["constructed_only_in"]]
            if matches(dotted, allowed):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _called_name(node) == symbol:
                    report.violations.append(
                        Violation(
                            path=path,
                            line=node.lineno,
                            message=(
                                f"{dotted} constructs {symbol}, which may only be "
                                f"constructed in {', '.join(allowed)}"
                            ),
                            reason=reason,
                        )
                    )

        if "module" in rule and "imported_only_by" in rule:
            target = str(rule["module"])
            allowed = [str(p) for p in rule["imported_only_by"]]
            if matches(dotted, allowed):
                continue
            # Deduplicated by line: `from lab.costs.schedule import rate` yields
            # both the module and the qualified name, and reporting one import
            # statement twice makes the count a measure of syntax rather than of
            # breaches.
            breached = {
                line
                for imported, line in _imported_modules(tree)
                if imported == target or imported.startswith(f"{target}.")
            }
            for line in sorted(breached):
                report.violations.append(
                    Violation(
                        path=path,
                        line=line,
                        message=(
                            f"{dotted} imports {target}, which may only be "
                            f"imported by {', '.join(allowed)}"
                        ),
                        reason=reason,
                    )
                )


def check(root: Path, rules_path: Path | None = None) -> Report:
    """Apply the rules file across every module beneath `src/`."""
    rules = load_rules(rules_path or root / DEFAULT_RULES)
    report = Report(rules_applied=len(rules))

    source_root = root / "src"
    if not source_root.is_dir():
        return report

    for path in sorted(source_root.rglob("*.py")):
        check_module(path, source_root, rules, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import graph (deep dive P0 section 9.1).")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--rules", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = check(args.root, args.rules)
    except ImportRuleError as exc:
        print(f"check_import_graph: REFUSED TO RUN: {exc}", file=sys.stderr)
        return 2

    if report.violations:
        for violation in report.violations:
            print(violation.render(), file=sys.stderr)
        print(f"check_import_graph: {len(report.violations)} violation(s)", file=sys.stderr)
        return 1

    print(
        f"check_import_graph: clean -- {report.rules_applied} rule(s) over "
        f"{report.modules_scanned} module(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
