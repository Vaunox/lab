"""Planted violation: an engine reaching into shared truth and minting a result.

Fixture data. Both breaches are deliberate and both are the real failure this
checker exists to catch -- an engine that computes a cost, and an engine that
mints its own TrialResult.
"""

from lab.costs.schedule import statutory_rate
from lab.ledger.schema import TrialResult


def run(bars: list[int]) -> TrialResult:
    """Duplicates truth, then mints a result it has no authority to mint."""
    charged = sum(bar * statutory_rate(bar) for bar in bars)
    return TrialResult(net_paise=charged)
