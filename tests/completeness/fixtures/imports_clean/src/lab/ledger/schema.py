"""The symbol the planted rule protects. Fixture data."""


class TrialResult:
    """Constructed only inside `lab.ledger.*`."""

    def __init__(self, net_paise: int) -> None:
        self.net_paise = net_paise
