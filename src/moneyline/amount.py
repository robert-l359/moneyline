"""The core value type: an exact amount paired with an optional currency."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    """An amount of money.

    Stored as a Decimal rather than a float so that combining amounts
    never drifts (0.10 + 0.20 is exactly 0.30 here, unlike with binary
    floats). Currency is optional: a bare number with no symbol or code
    parses fine, and such an amount can be combined with anything.
    """

    amount: Decimal
    currency: str | None = None

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount, self._merged_currency(other))

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount, self._merged_currency(other))

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def _merged_currency(self, other: "Money") -> str | None:
        if self.currency and other.currency and self.currency != other.currency:
            raise ValueError(
                f"cannot combine {self.currency} and {other.currency} amounts"
            )
        return self.currency or other.currency

    def __str__(self) -> str:
        text = f"{self.amount:,.2f}"
        return f"{text} {self.currency}" if self.currency else text
