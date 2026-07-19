"""The ledger minting a result, which is legitimate. Fixture data.

Present so the planted tree also proves the rule is not a blanket ban. A checker
that flagged this construction too would be rejecting the tree for the wrong
reason, and `test_import_graph_rejects_violation` asserts the ledger is absent
from the violation list.
"""

from lab.ledger.schema import TrialResult


def append(net_paise: int) -> TrialResult:
    """Inside `lab.ledger.*`, so the construction is permitted."""
    return TrialResult(net_paise=net_paise)
