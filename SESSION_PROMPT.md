# Session prompt

Open Claude Code in this directory and say:

```
Read CLAUDE.md and begin.
```

That is the whole thing. `CLAUDE.md` works out which session this is, reads
`HANDOFF.md` for the current state, and follows the deep dive for the active
phase.

---

## The one thing the builder cannot do for you

If `gh auth status` fails, it will stop and ask you to run:

```
gh auth login
```

Then say `continue`. Credential handling is yours, not the builder's — that is
the only manual step in the entire program, and it exists on purpose.

---

## If you want to be explicit

The prompt above is sufficient. This longer form says the same thing out loud,
and is useful if a session has drifted:

```
Read HANDOFF.md first — it is the current state of the phase and is authoritative
over your assumptions. Then DEAD_ENDS.md.

Then MASTER_BLUEPRINT.md Part I in full:
  §9  Completion   — done means proven at the call site
  §10 Completeness — the gate is a SAMPLE of the spec, not a summary
  §11 Gate integrity — you may not edit the thing that judges you
  §12 Session protocol — a phase may span sessions; a PR may not merge partially
  Project-Specific Inviolable Rules

Read docs/deep_dives/ for the active phase, IN FULL. It is the specification.

Build EVERY ROW of its MANIFEST — not merely the artifacts the gate tests touch.
If you catch yourself deciding something is "not needed for the gate," stop.
That is the exact failure this project exists to prevent.

If the deep dive is ambiguous anywhere, STOP and surface it. Do not choose the
simpler reading.

Work on the phase branch. Never commit to main. Never put spec and code in the
same commit.

Update HANDOFF.md continuously — after each decision, each rejected approach,
each surprise. Not at the end.

End by running `python tools/gate.py` and piping its output verbatim into HANDOFF.md. If
work is unfinished, END RED AND HONEST. Never write a stub to make a check pass.
```
