"""A file whose CONTENTS mention the vendor, which is topic and not attribution.

This module exists to be scanned and passed. Failure case 7: `.gitignore`
contains the literal CLAUDE.md and a docstring may say "Claude API" -- both are
legitimate, and a checker that greps contents can never pass. See DE-000l.
"""

VENDOR_DOCS = "https://docs.anthropic.com"
NOTE = "Generated with care by a human. Run this under Claude Code if you like."
