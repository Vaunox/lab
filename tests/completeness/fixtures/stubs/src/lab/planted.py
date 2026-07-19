"""Planted violations for check_no_stubs. Deep dive P0 sections 7.1 to 7.3.

Fixture data. Every defect below is deliberate, and each one is a distinct row of
the section 7.1 table so that a single tree exercises the whole registry.

The legitimate Protocol at the top is the load-bearing half: a checker that
rejects this file by flagging *everything* has not distinguished the language
convention from the deferral, and section 7.2 is explicit that such a checker is
not shipped.
"""

from typing import Protocol, runtime_checkable


class MarketView(Protocol):
    """Legitimate. A Protocol member's body is `...` by language convention."""

    def price(self, isin: str) -> int: ...

    def is_tradable(self, isin: str) -> bool: ...


@runtime_checkable
class CostProfile(Protocol):
    """Legitimate by decorator rather than by base class."""

    def brokerage(self, turnover: int) -> int: ...


def bare_ellipsis_is_not_a_protocol_member() -> None: ...


def bare_pass_body() -> None:
    pass


def documented_pass_body() -> None:
    """A docstring does not stop a body being empty."""
    pass


def raises_not_implemented() -> int:
    raise NotImplementedError


def marker_naming_no_open_row() -> int:  # STUB: DEF-404
    pass


def deferral_language_in_the_docstring() -> int:
    """Returns zero as a placeholder until the real schedule lands."""
    return 0


class Nested:
    """The Protocol exemption must not leak into an unrelated class."""

    def method_with_ellipsis(self) -> None: ...
