"""Shared truth. Importable only from within `lab.costs.*`. Fixture data."""


def statutory_rate(turnover_paise: int) -> int:
    """Point-in-time statutory rate, in paise."""
    return turnover_paise // 1000
