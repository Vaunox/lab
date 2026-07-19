"""The negative control for check_no_stubs.

Nothing here is planted. Every `...` body belongs to a Protocol member, which
section 7.2 permits, so a correct checker accepts this tree whole.

This fixture is what stops the Protocol exemption being certified by a checker
that simply flags nothing.
"""

from typing import Protocol, runtime_checkable


class MarketView(Protocol):
    """Point-in-time view. Contains nothing after `asof`."""

    def price(self, isin: str) -> int: ...

    def is_tradable(self, isin: str) -> bool: ...


@runtime_checkable
class CostProfile(Protocol):
    """Broker profile, curated and versioned, never a blank form."""

    def brokerage(self, turnover: int) -> int: ...


def a_real_function(value: int) -> int:
    """Has a body, so there is nothing to flag."""
    return value * 2
